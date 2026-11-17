"""实时功能测试：敏感词过滤、私信撤回与输入中状态。"""

import json
from datetime import timedelta
from unittest.mock import patch

from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase, TransactionTestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from chat.consumers import ChatConsumer
from chat.views import RecentActivePresence, presence
from config.asgi import application
from core.sensitive_filter import mask_sensitive
from private_messages.models import Message

User = get_user_model()

IN_MEMORY_CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}


class SensitiveFilterTests(TestCase):
    """敏感词过滤测试。"""

    def test_default_words_are_masked(self):
        self.assertEqual(mask_sensitive('你这个傻逼'), '你这个***')
        self.assertEqual(mask_sensitive('fuck this'), '*** this')

    def test_case_insensitive(self):
        self.assertEqual(mask_sensitive('FUCK'), '***')
        self.assertEqual(mask_sensitive('ShIt'), '***')

    def test_plain_text_unchanged(self):
        self.assertEqual(mask_sensitive('今天天气不错'), '今天天气不错')
        self.assertEqual(mask_sensitive('hello world'), 'hello world')

    def test_empty_value_returns_as_is(self):
        self.assertEqual(mask_sensitive(''), '')
        self.assertIsNone(mask_sensitive(None))

    @override_settings(SENSITIVE_WORDS=['自定义词'])
    def test_settings_words_are_applied(self):
        self.assertEqual(mask_sensitive('这是自定义词'), '这是***')
        # 配置词表与默认词表合并，默认词依然生效
        self.assertEqual(mask_sensitive('傻逼'), '***')


class MessageRecallAPITests(TestCase):
    """私信撤回接口测试。"""

    def setUp(self):
        self.alice = User.objects.create_user(username='alice', password='pass123', email='alice@example.com')
        self.bob = User.objects.create_user(username='bob', password='pass123', email='bob@example.com')
        self.carol = User.objects.create_user(username='carol', password='pass123', email='carol@example.com')

        self.client = APIClient()
        self.client.force_authenticate(user=self.alice)
        self.messages_url = '/api/users/messages/'

        self.message = Message.objects.create(
            sender=self.alice,
            receiver=self.bob,
            content='撤回测试',
        )

    def _recall_url(self, message_id):
        return f'{self.messages_url}{message_id}/recall/'

    def test_sender_can_recall_within_window(self):
        with patch('private_messages.views.websocket_service.send_message_recalled') as mock_push:
            response = self.client.post(self._recall_url(self.message.id))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['message'], '消息已撤回')
        self.assertEqual(response.data['message_id'], self.message.id)
        self.assertIsNotNone(response.data['recalled_at'])

        self.message.refresh_from_db()
        self.assertTrue(self.message.is_recalled)
        self.assertIsNotNone(self.message.recalled_at)

        mock_push.assert_called_once()
        self.assertEqual(mock_push.call_args.args[0], self.alice)
        self.assertEqual(mock_push.call_args.args[1], self.bob)
        self.assertEqual(mock_push.call_args.args[2].id, self.message.id)

    def test_receiver_cannot_recall(self):
        self.client.force_authenticate(user=self.bob)

        response = self.client.post(self._recall_url(self.message.id))

        self.assertEqual(response.status_code, 403)
        self.message.refresh_from_db()
        self.assertFalse(self.message.is_recalled)

    def test_unrelated_user_gets_404(self):
        self.client.force_authenticate(user=self.carol)

        response = self.client.post(self._recall_url(self.message.id))

        self.assertEqual(response.status_code, 404)

    def test_recall_after_timeout_returns_400(self):
        Message.objects.filter(pk=self.message.pk).update(
            created_at=timezone.now() - timedelta(seconds=200)
        )

        response = self.client.post(self._recall_url(self.message.id))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error'], '消息已超过可撤回时间')
        self.message.refresh_from_db()
        self.assertFalse(self.message.is_recalled)

    def test_repeat_recall_returns_400(self):
        with patch('private_messages.views.websocket_service.send_message_recalled'):
            first = self.client.post(self._recall_url(self.message.id))
            second = self.client.post(self._recall_url(self.message.id))

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 400)
        self.assertEqual(second.data['error'], '消息已撤回')

    def test_recall_requires_authentication(self):
        self.client.force_authenticate(user=None)

        response = self.client.post(self._recall_url(self.message.id))

        self.assertEqual(response.status_code, 401)

    def test_serializer_exposes_recall_fields(self):
        response = self.client.get(self.messages_url)

        self.assertEqual(response.status_code, 200)
        item = response.data['results'][0]
        self.assertIn('is_recalled', item)
        self.assertIn('recalled_at', item)
        self.assertFalse(item['is_recalled'])
        self.assertIsNone(item['recalled_at'])


@override_settings(CHANNEL_LAYERS=IN_MEMORY_CHANNEL_LAYERS)
class ChatTypingWebSocketTests(TransactionTestCase):
    """公共聊天室输入中状态测试。"""

    def setUp(self):
        # 避免测试环境尝试连接真实 Redis，强制使用内存回退实现
        RecentActivePresence._redis = None
        RecentActivePresence._redis_available = False
        with presence._lock:
            presence._fallback_users.clear()

        self.user = User.objects.create_user(
            username='typing_user',
            password='pass123',
            email='typing@example.com',
        )
        self.token = str(RefreshToken.for_user(self.user).access_token)

    async def test_authenticated_typing_is_broadcast(self):
        communicator = WebsocketCommunicator(
            application,
            '/ws/chat/public/',
            subprotocols=['jwt', self.token],
        )
        connected, _ = await communicator.connect(timeout=10)
        self.assertTrue(connected)

        try:
            # 排空连接建立时下发的初始消息
            while not await communicator.receive_nothing(timeout=0.1):
                await communicator.receive_json_from(timeout=1)

            await communicator.send_json_to({'type': 'typing'})
            event = await communicator.receive_json_from(timeout=5)
        finally:
            await communicator.disconnect()

        self.assertEqual(event['type'], 'typing')
        self.assertEqual(event['user_id'], self.user.id)
        self.assertEqual(event['username'], 'typing_user')
        self.assertEqual(event['room'], 'public')
        self.assertIn('time', event)


class ChatTypingUnauthenticatedTests(TransactionTestCase):
    """未认证用户发送 typing 应收到登录提示。"""

    async def test_unauthenticated_typing_returns_error(self):
        consumer = ChatConsumer()
        consumer.scope = {
            'user': AnonymousUser(),
            'subprotocols': [],
            'url_route': {'kwargs': {}},
        }
        consumer.user = AnonymousUser()
        consumer.channel_layer = get_channel_layer()
        consumer.channel_name = 'test_typing_anon'
        consumer.room_group_name = 'chat'

        sent = []

        async def fake_send(text_data=None, **kwargs):
            sent.append(text_data)

        consumer.send = fake_send

        await consumer.receive(text_data=json.dumps({'type': 'typing'}))

        self.assertTrue(sent)
        payload = json.loads(sent[-1])
        self.assertEqual(payload['type'], 'error')
        self.assertEqual(payload['message'], '请先登录')
