"""动态模块测试。

覆盖公开可见性、发布、点赞幂等、评论计数与通知、关注流与个人动态。
"""

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient

from notifications.models import Notification

from .models import Activity, ActivityComment, ActivityLike

User = get_user_model()


class ActivityAPITests(TestCase):
    """动态接口测试。"""

    def setUp(self):
        cache.clear()
        self.alice = User.objects.create_user(username='alice', password='testpass', email='alice@example.com')
        self.bob = User.objects.create_user(username='bob', password='testpass', email='bob@example.com')
        self.carol = User.objects.create_user(username='carol', password='testpass', email='carol@example.com')

        self.public_activity = Activity.objects.create(
            user=self.alice,
            activity_type='post',
            content='公开动态',
            is_public=True,
        )
        self.private_activity = Activity.objects.create(
            user=self.alice,
            activity_type='post',
            content='私密动态',
            is_public=False,
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.bob)

        self.activities_url = '/api/users/activities/'

        self.points_patcher = patch('activities.views.queue_update_user_points')
        self.mock_points = self.points_patcher.start()
        self.addCleanup(self.points_patcher.stop)

    def test_public_list_excludes_private_activities(self):
        """列表只返回公开动态。"""
        response = self.client.get(self.activities_url)

        self.assertEqual(response.status_code, 200)
        contents = [item['content'] for item in response.data['results']]
        self.assertEqual(contents, ['公开动态'])

    def test_retrieve_private_activity_returns_404(self):
        """私密动态无法通过详情接口访问。"""
        response = self.client.get(f'{self.activities_url}{self.private_activity.id}/')

        self.assertEqual(response.status_code, 404)

    def test_create_activity_assigns_user_and_awards_points(self):
        """发布动态应记录作者并发放积分。"""
        response = self.client.post(
            self.activities_url,
            {'activity_type': 'post', 'content': '今天去图书馆'},
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        activity = Activity.objects.get(content='今天去图书馆')
        self.assertEqual(activity.user, self.bob)

        self.mock_points.assert_called_once()
        self.assertEqual(self.mock_points.call_args.args[0], self.bob.id)
        self.assertEqual(self.mock_points.call_args.args[1], 'post')

    def test_create_activity_requires_authentication(self):
        """未登录用户不能发布动态。"""
        self.client.force_authenticate(user=None)

        response = self.client.post(
            self.activities_url,
            {'activity_type': 'post', 'content': '匿名动态'},
            format='json',
        )

        self.assertEqual(response.status_code, 401)
        self.assertFalse(Activity.objects.filter(content='匿名动态').exists())

    def test_like_increments_count_and_awards_points(self):
        """点赞应创建记录、更新点赞数并发放双方积分。"""
        response = self.client.post(f'{self.activities_url}{self.public_activity.id}/like/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'liked')

        self.public_activity.refresh_from_db()
        self.assertEqual(self.public_activity.likes_count, 1)
        self.assertTrue(
            ActivityLike.objects.filter(activity=self.public_activity, user=self.bob).exists()
        )

        self.mock_points.assert_any_call(self.bob.id, 'like', description='点赞动态')
        self.mock_points.assert_any_call(self.alice.id, 'liked', description='动态被点赞')

    def test_like_twice_returns_400(self):
        """重复点赞返回 400 且点赞数只增加一次。"""
        first = self.client.post(f'{self.activities_url}{self.public_activity.id}/like/')
        second = self.client.post(f'{self.activities_url}{self.public_activity.id}/like/')

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 400)
        self.assertEqual(second.data['status'], 'already_liked')

        self.public_activity.refresh_from_db()
        self.assertEqual(self.public_activity.likes_count, 1)

    def test_like_own_activity_skips_author_reward_and_notification(self):
        """点赞自己的动态不发放被赞积分，也不产生通知。"""
        self.client.force_authenticate(user=self.alice)

        response = self.client.post(f'{self.activities_url}{self.public_activity.id}/like/')

        self.assertEqual(response.status_code, 200)
        self.mock_points.assert_called_once_with(self.alice.id, 'like', description='点赞动态')
        self.assertEqual(Notification.objects.count(), 0)

    def test_like_notifies_author(self):
        """点赞他人动态应通知作者。"""
        self.client.post(f'{self.activities_url}{self.public_activity.id}/like/')

        notification = Notification.objects.get(recipient=self.alice)
        self.assertEqual(notification.sender, self.bob)
        self.assertEqual(notification.title, '新点赞')
        self.assertEqual(notification.notification_type, 'interaction')

    def test_unlike_without_like_returns_400(self):
        """未点赞时取消点赞返回 400。"""
        response = self.client.post(f'{self.activities_url}{self.public_activity.id}/unlike/')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['status'], 'not_liked')

    def test_unlike_removes_like_and_decrements_count(self):
        """取消点赞应删除记录并把点赞数减一。"""
        self.client.post(f'{self.activities_url}{self.public_activity.id}/like/')

        response = self.client.post(f'{self.activities_url}{self.public_activity.id}/unlike/')

        self.assertEqual(response.status_code, 200)
        self.public_activity.refresh_from_db()
        self.assertEqual(self.public_activity.likes_count, 0)
        self.assertFalse(
            ActivityLike.objects.filter(activity=self.public_activity, user=self.bob).exists()
        )

    def test_comments_endpoint_returns_top_level_with_replies(self):
        """评论接口返回顶层评论并嵌套回复。"""
        root = ActivityComment.objects.create(
            activity=self.public_activity,
            user=self.bob,
            content='顶层评论',
        )
        ActivityComment.objects.create(
            activity=self.public_activity,
            user=self.alice,
            content='回复',
            parent=root,
        )

        response = self.client.get(f'{self.activities_url}{self.public_activity.id}/comments/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['content'], '顶层评论')
        self.assertEqual(len(response.data[0]['replies']), 1)

    def test_create_comment_updates_count_and_notifies_author(self):
        """评论动态应更新评论数并通知作者。"""
        response = self.client.post(
            '/api/users/activity-comments/',
            {'activity': self.public_activity.id, 'content': '写得不错'},
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        self.public_activity.refresh_from_db()
        self.assertEqual(self.public_activity.comments_count, 1)

        notification = Notification.objects.get(recipient=self.alice)
        self.assertEqual(notification.notification_type, 'content_comment')
        self.assertEqual(notification.title, '新评论')

    def test_comment_on_own_activity_creates_no_notification(self):
        """评论自己的动态不产生通知。"""
        self.client.force_authenticate(user=self.alice)

        response = self.client.post(
            '/api/users/activity-comments/',
            {'activity': self.public_activity.id, 'content': '自我评论'},
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Notification.objects.count(), 0)

    def test_feed_returns_following_and_self(self):
        """关注流包含关注用户与自己的公开动态。"""
        self.alice.following.add(self.bob)
        Activity.objects.create(user=self.bob, activity_type='post', content='bob 动态')
        Activity.objects.create(user=self.carol, activity_type='post', content='carol 动态')

        self.client.force_authenticate(user=self.alice)
        response = self.client.get(f'{self.activities_url}feed/')

        self.assertEqual(response.status_code, 200)
        contents = {item['content'] for item in response.data['results']}
        self.assertEqual(contents, {'公开动态', 'bob 动态'})

    def test_my_activities_returns_only_own(self):
        """个人动态只返回当前用户发布的内容。"""
        Activity.objects.create(user=self.bob, activity_type='post', content='bob 动态')

        response = self.client.get(f'{self.activities_url}my_activities/')

        self.assertEqual(response.status_code, 200)
        contents = {item['content'] for item in response.data['results']}
        self.assertEqual(contents, {'bob 动态'})
