"""微信绑定与订阅消息测试。"""

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from notifications.models import Notification
from notifications.tasks import send_wechat_subscribe_async

User = get_user_model()

WECHAT_SETTINGS = {
    'WECHAT_APPID': 'wx-test-appid',
    'WECHAT_SECRET': 'wx-test-secret',
    'WECHAT_SUBSCRIBE_TEMPLATES': {
        'comment': 'tpl-comment',
        'message': 'tpl-message',
        'interaction': 'tpl-interaction',
    },
}


@override_settings(**WECHAT_SETTINGS)
class WechatAccountAPITests(TestCase):
    """微信绑定、登录与订阅授权接口。"""

    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            username='alice', password='testpass', email='alice@example.com'
        )
        self.other = User.objects.create_user(
            username='bob', password='testpass', email='bob@example.com'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.bind_url = '/api/users/users/wechat_bind/'
        self.subscribe_url = '/api/users/users/wechat_subscribe/'
        self.login_url = '/api/users/users/wechat_login/'

    def test_bind_success(self):
        with patch('users.views.code_to_openid', return_value='openid-alice'):
            response = self.client.post(self.bind_url, {'code': 'wx-code'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['bound'])
        self.user.refresh_from_db()
        self.assertEqual(self.user.wechat_openid, 'openid-alice')

    def test_bind_rejects_openid_used_by_other_user(self):
        self.other.wechat_openid = 'openid-taken'
        self.other.save(update_fields=['wechat_openid'])

        with patch('users.views.code_to_openid', return_value='openid-taken'):
            response = self.client.post(self.bind_url, {'code': 'wx-code'}, format='json')

        self.assertEqual(response.status_code, 400)
        self.user.refresh_from_db()
        self.assertIsNone(self.user.wechat_openid)

    def test_bind_fails_when_code_invalid(self):
        with patch('users.views.code_to_openid', return_value=None):
            response = self.client.post(self.bind_url, {'code': 'bad'}, format='json')

        self.assertEqual(response.status_code, 400)

    def test_bind_requires_authentication(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(self.bind_url, {'code': 'wx-code'}, format='json')

        self.assertEqual(response.status_code, 401)

    def test_subscribe_records_templates(self):
        response = self.client.post(
            self.subscribe_url,
            {'templates': ['comment', 'message']},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(sorted(response.data['templates']), ['comment', 'message'])
        self.user.refresh_from_db()
        self.assertEqual(sorted(self.user.wechat_subscriptions), ['comment', 'message'])

    def test_subscribe_deduplicates_templates(self):
        self.client.post(self.subscribe_url, {'templates': ['comment']}, format='json')
        response = self.client.post(self.subscribe_url, {'templates': ['comment']}, format='json')

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.wechat_subscriptions, ['comment'])

    def test_subscribe_rejects_unknown_template(self):
        response = self.client.post(
            self.subscribe_url,
            {'templates': ['unknown']},
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.user.refresh_from_db()
        self.assertEqual(self.user.wechat_subscriptions, [])

    def test_wechat_login_returns_tokens(self):
        self.user.wechat_openid = 'openid-alice'
        self.user.save(update_fields=['wechat_openid'])

        with patch('users.views.code_to_openid', return_value='openid-alice'):
            response = self.client.post(self.login_url, {'code': 'wx-code'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['id'], self.user.id)

    def test_wechat_login_requires_bound_account(self):
        with patch('users.views.code_to_openid', return_value='openid-unknown'):
            response = self.client.post(self.login_url, {'code': 'wx-code'}, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertTrue(response.data.get('need_bind'))


@override_settings(**WECHAT_SETTINGS)
class WechatSubscribeTaskTests(TestCase):
    """订阅消息任务测试。"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='alice',
            password='testpass',
            email='alice@example.com',
            wechat_openid='openid-alice',
            wechat_subscriptions=['comment'],
        )
        self.notification = Notification.objects.create(
            recipient=self.user,
            title='新评论',
            content='有人评论了你的内容',
            notification_type='content_comment',
        )

    def test_task_sends_and_consumes_subscription(self):
        with patch('notifications.tasks.send_subscribe_message', return_value=True) as mock_send:
            send_wechat_subscribe_async(self.notification.id)

        self.user.refresh_from_db()
        mock_send.assert_called_once()
        args = mock_send.call_args.args
        self.assertEqual(args[0], 'openid-alice')
        self.assertEqual(args[1], 'tpl-comment')
        self.assertEqual(args[2]['thing1'], '新评论')
        self.assertEqual(self.user.wechat_subscriptions, [])

    def test_task_skips_without_subscription(self):
        self.user.wechat_subscriptions = []
        self.user.save(update_fields=['wechat_subscriptions'])

        with patch('notifications.tasks.send_subscribe_message') as mock_send:
            send_wechat_subscribe_async(self.notification.id)

        mock_send.assert_not_called()

    def test_task_skips_without_openid(self):
        self.user.wechat_openid = None
        self.user.save(update_fields=['wechat_openid'])

        with patch('notifications.tasks.send_subscribe_message') as mock_send:
            send_wechat_subscribe_async(self.notification.id)

        mock_send.assert_not_called()

    def test_task_keeps_subscription_when_send_fails(self):
        with patch('notifications.tasks.send_subscribe_message', return_value=False):
            send_wechat_subscribe_async(self.notification.id)

        self.user.refresh_from_db()
        self.assertEqual(self.user.wechat_subscriptions, ['comment'])
