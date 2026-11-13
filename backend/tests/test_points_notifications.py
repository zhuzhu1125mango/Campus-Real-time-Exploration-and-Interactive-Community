"""积分与通知相关功能的单元测试。"""

from datetime import datetime, time as dt_time, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
)
class EagerCeleryTestCase(TestCase):
    """基类：让 Celery 任务在测试中以 eager 模式同步执行。"""
    pass

from notifications.models import Notification
from notifications.notification_sender import notify_forum_event
from users.models import PointsRecord
from users.points import (
    POINTS_RULES,
    ACTION_DESCRIPTIONS,
    LEVEL_THRESHOLDS,
    calculate_level,
    get_points_for_action,
    get_action_description,
)
from users.tasks import update_user_points_async

User = get_user_model()


class PointsRulesTests(EagerCeleryTestCase):
    """积分规则配置测试。"""

    def test_all_actions_have_description(self):
        for action in POINTS_RULES:
            self.assertIn(action, ACTION_DESCRIPTIONS, f"行为 {action} 缺少描述")

    def test_required_actions_present(self):
        required = [
            'register', 'login', 'complete_profile', 'verified',
            'daily_checkin', 'consecutive_checkin_3', 'consecutive_checkin_7',
            'post', 'reply', 'comment', 'like', 'liked', 'favorite',
            'create_course', 'complete_course',
        ]
        for action in required:
            self.assertIn(action, POINTS_RULES, f"缺少积分规则: {action}")
            self.assertGreaterEqual(POINTS_RULES[action], 0, f"积分不应为负: {action}")

    def test_level_thresholds(self):
        self.assertEqual(calculate_level(0), 1)
        self.assertEqual(calculate_level(49), 1)
        self.assertEqual(calculate_level(50), 2)
        self.assertEqual(calculate_level(10000), 8)
        self.assertEqual(len(LEVEL_THRESHOLDS), 8)

    def test_helper_functions(self):
        self.assertEqual(get_points_for_action('post'), POINTS_RULES['post'])
        self.assertEqual(get_points_for_action('unknown_action'), 0)
        self.assertEqual(get_action_description('post'), ACTION_DESCRIPTIONS['post'])
        self.assertEqual(get_action_description('unknown_action'), 'unknown_action')


class PointsTaskTests(EagerCeleryTestCase):
    """积分异步任务测试。"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='testpass', email='test@example.com'
        )
        # 用户创建信号会异步发放注册积分，刷新后获取真实积分
        self.user.refresh_from_db()

    def test_update_user_points_increases_total(self):
        initial_points = self.user.points
        update_user_points_async(self.user.id, 'post')
        self.user.refresh_from_db()
        self.assertEqual(self.user.points, initial_points + POINTS_RULES['post'])
        self.assertEqual(PointsRecord.objects.filter(user=self.user, action='post').count(), 1)

    def test_update_user_points_level_up(self):
        # 直接赋予接近升级所需的积分
        User.objects.filter(pk=self.user.pk).update(points=45)
        update_user_points_async(self.user.id, 'complete_profile')
        self.user.refresh_from_db()
        self.assertEqual(self.user.level, 2)

    def test_update_user_points_zero_action_skipped(self):
        initial_points = self.user.points
        update_user_points_async(self.user.id, 'system')
        self.user.refresh_from_db()
        self.assertEqual(self.user.points, initial_points)
        self.assertFalse(PointsRecord.objects.filter(user=self.user, action='system').exists())

    def test_update_user_points_missing_user(self):
        # 不存在的用户不应抛异常
        result = update_user_points_async(99999, 'post')
        self.assertIsNone(result)


class CheckinPointsTests(EagerCeleryTestCase):
    """每日签到与连续签到积分测试。"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='checkinuser', password='testpass'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def _make_checkin_record(self, action, days_ago):
        date = timezone.now().date() - timedelta(days=days_ago)
        created_at = timezone.make_aware(datetime.combine(date, dt_time.min))
        record = PointsRecord.objects.create(
            user=self.user,
            action=action,
            points=POINTS_RULES[action],
            description='test',
        )
        PointsRecord.objects.filter(pk=record.pk).update(created_at=created_at)

    def test_daily_checkin_first_time(self):
        response = self.client.post(reverse('user-daily-checkin'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            PointsRecord.objects.filter(user=self.user, action='daily_checkin').count(),
            1,
        )

    def test_daily_checkin_idempotent(self):
        self.client.post(reverse('user-daily-checkin'))
        response = self.client.post(reverse('user-daily-checkin'))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            PointsRecord.objects.filter(user=self.user, action='daily_checkin').count(),
            1,
        )

    def test_consecutive_checkin_reward_once(self):
        # 构造连续 7 天签到记录
        for days_ago in range(1, 8):
            self._make_checkin_record('daily_checkin', days_ago)

        response = self.client.post(reverse('user-daily-checkin'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            PointsRecord.objects.filter(user=self.user, action='consecutive_checkin_7').count(),
            1,
        )

        # 再次签到不应重复发放 7 天奖励
        # 先删除今天的 daily_checkin 以模拟明天（仅用于测试幂等）
        PointsRecord.objects.filter(
            user=self.user, action='daily_checkin',
            created_at__date=timezone.now().date()
        ).delete()
        PointsRecord.objects.filter(
            user=self.user, action='daily_checkin',
            created_at__gte=timezone.now().date()
        ).delete()

        response = self.client.post(reverse('user-daily-checkin'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            PointsRecord.objects.filter(user=self.user, action='consecutive_checkin_7').count(),
            1,
        )


class LoginPointsTests(EagerCeleryTestCase):
    """登录积分测试。"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='loginuser', password='testpass'
        )
        self.client = APIClient()

    def test_login_awards_points_first_time(self):
        response = self.client.post(reverse('user-login'), {
            'username': 'loginuser',
            'password': 'testpass',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            PointsRecord.objects.filter(user=self.user, action='login').count(),
            1,
        )

    def test_login_idempotent_same_day(self):
        self.client.post(reverse('user-login'), {
            'username': 'loginuser',
            'password': 'testpass',
        })
        response = self.client.post(reverse('user-login'), {
            'username': 'loginuser',
            'password': 'testpass',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            PointsRecord.objects.filter(user=self.user, action='login').count(),
            1,
        )


class FavoritePointsTests(EagerCeleryTestCase):
    """收藏积分测试。"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='favuser', password='testpass'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_forum_bookmark_awards_points(self):
        from forum.models import Category, Board, Topic
        category = Category.objects.create(name='测试分类')
        board = Board.objects.create(name='测试板块', category=category)
        topic = Topic.objects.create(
            title='测试主题',
            author=self.user,
            board=board,
        )
        response = self.client.post(reverse('topic-bookmark', kwargs={'pk': topic.pk}))
        self.assertIn(response.status_code, [201, 200])
        self.assertTrue(
            PointsRecord.objects.filter(user=self.user, action='favorite').exists()
        )


class ContentPointsTests(EagerCeleryTestCase):
    """内容模块积分测试。"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='contentuser', password='testpass'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_create_content_awards_points(self):
        from content.models import ContentType as CT
        ct, _ = CT.objects.get_or_create(name='文章')
        response = self.client.post(reverse('content-list'), {
            'title': '测试内容',
            'content': '测试正文',
            'summary': '摘要',
            'content_type': ct.id,
            'status': 'published',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            PointsRecord.objects.filter(user=self.user, action='post').exists()
        )


class NotificationTests(EagerCeleryTestCase):
    """通知发送测试。"""

    def setUp(self):
        self.sender = User.objects.create_user(
            username='sender', password='testpass', email='sender@example.com'
        )
        self.recipient = User.objects.create_user(
            username='recipient', password='testpass', email='recipient@example.com'
        )

    def test_notify_forum_event_creates_notification(self):
        notify_forum_event(
            recipient=self.recipient,
            sender=self.sender,
            forum_type='topic_reply',
            message='有人回复了你的主题',
        )
        self.assertEqual(Notification.objects.filter(recipient=self.recipient).count(), 1)
        notification = Notification.objects.first()
        self.assertEqual(notification.notification_type, 'interaction')
        self.assertEqual(notification.title, '新回复')

    def test_content_comment_notification_type(self):
        notify_forum_event(
            recipient=self.recipient,
            sender=self.sender,
            forum_type='content_comment',
            message='有人评论了你的内容',
        )
        notification = Notification.objects.first()
        self.assertEqual(notification.notification_type, 'interaction')
        self.assertEqual(notification.title, '新评论')
