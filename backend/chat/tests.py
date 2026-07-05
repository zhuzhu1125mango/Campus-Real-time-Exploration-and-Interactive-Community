import json
import time

from channels.db import database_sync_to_async
from channels.testing.websocket import WebsocketCommunicator
from django.test import TestCase, TransactionTestCase, override_settings
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from config.asgi import application
from chat.models import ChatMessage
from chat.views import RecentActivePresence, presence

User = get_user_model()


# 测试期间关闭 DRF 限流，避免并发或重复请求因限流出现非预期失败
DISABLE_THROTTLE_SETTINGS = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_THROTTLE_CLASSES': [],
    'DEFAULT_THROTTLE_RATES': {},
}


class RecentActivePresenceTests(TestCase):
    """最近活跃用户统计测试"""

    def setUp(self):
        # 每次测试前清理内存回退集合
        with presence._lock:
            presence._fallback_users.clear()
        # 如果 Redis 可用也清空
        try:
            r = presence._get_redis()
            if r:
                r.delete(presence.KEY)
        except Exception:
            pass

    def test_mark_active_and_count(self):
        """标记用户活跃后，计数应增加"""
        self.assertEqual(presence.count(), 0)
        presence.mark_active(1)
        self.assertEqual(presence.count(), 1)
        presence.mark_active(2)
        self.assertEqual(presence.count(), 2)

    def test_duplicate_user_does_not_inflate_count(self):
        """同一用户多次活跃不应重复计数"""
        presence.mark_active(1)
        presence.mark_active(1)
        presence.mark_active(1)
        self.assertEqual(presence.count(), 1)

    def test_expired_users_are_removed(self):
        """窗口期外的用户应被清理"""
        # 直接构造一个过期的记录，避免依赖真实睡眠时间
        expired_time = time.time() - presence.WINDOW_SECONDS - 1
        with presence._lock:
            presence._fallback_users['1'] = expired_time
            presence._fallback_users['2'] = time.time()

        self.assertEqual(presence.count(), 1)

        # 再插入一个过期记录后，也应只剩活跃用户
        with presence._lock:
            presence._fallback_users['3'] = expired_time
        self.assertEqual(presence.count(), 1)

    def test_none_user_id_is_ignored(self):
        """None 用户 ID 不应导致异常"""
        presence.mark_active(None)
        self.assertEqual(presence.count(), 0)

    def test_count_cleans_expired_users(self):
        """count 调用时应清理过期用户并返回正确数量"""
        now = time.time()
        with presence._lock:
            presence._fallback_users['1'] = now
            presence._fallback_users['2'] = now - presence.WINDOW_SECONDS - 1
            presence._fallback_users['3'] = now

        self.assertEqual(presence.count(), 2)

        with presence._lock:
            self.assertNotIn('2', presence._fallback_users)


class ChatMessageModelTests(TestCase):
    """聊天消息模型基础测试"""

    def test_create_chat_message(self):
        user = User.objects.create_user(
            username='chat_user',
            password='password123'
        )
        from chat.models import ChatMessage
        message = ChatMessage.objects.create(
            user=user,
            content='hello world'
        )
        self.assertEqual(str(message.content), 'hello world')
        self.assertEqual(message.user, user)


class ChatWebSocketTestBase(TransactionTestCase):
    """WebSocket 测试基类，使用 Django 原生异步测试避免 async_to_sync 死锁。"""

    async def asyncSetUp(self):
        await super().asyncSetUp()
        self._clear_presence()

    async def asyncTearDown(self):
        self._clear_presence()
        await super().asyncTearDown()

    def _clear_presence(self):
        """清理在线统计的内存回退状态，并强制使用内存回退避免 Redis 阻塞事件循环。"""
        with presence._lock:
            presence._fallback_users.clear()
        RecentActivePresence._redis = None
        RecentActivePresence._redis_available = False

    @database_sync_to_async
    def create_user(self, username='user', password='TestPass123!', **kwargs):
        # email 在 User 模型中设置了 unique=True，为空字符串时多个用户会冲突，
        # 因此未提供时根据用户名生成唯一邮箱。
        if 'email' not in kwargs:
            kwargs['email'] = f'{username}@example.com'
        return User.objects.create_user(
            username=username, password=password, **kwargs
        )

    @database_sync_to_async
    def get_access_token(self, user):
        return str(RefreshToken.for_user(user).access_token)

    def get_communicator(self, token=None):
        """构造 WebSocket 连接客户端；token 使用 jwt 子协议格式传递。"""
        subprotocols = ['jwt', token] if token else []
        return WebsocketCommunicator(
            application, '/ws/chat/public/', subprotocols=subprotocols
        )

    async def drain_messages(self, communicator, timeout=0.5):
        """排空连接建立或广播产生的待收消息。

        使用 receive_nothing 检测队列是否为空，避免 receive_json_from 的超时
        逻辑取消应用 future。
        """
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if await communicator.receive_nothing(timeout=0.05):
                break
            try:
                await communicator.receive_json_from(timeout=0.5)
            except Exception:
                break

    async def connect(self, token=None):
        """连接 WebSocket 并排空初始消息，返回 (connected, communicator)。"""
        communicator = self.get_communicator(token)
        connected, _ = await communicator.connect(timeout=10)
        if connected:
            await self.drain_messages(communicator)
        return connected, communicator

    async def connect_communicator(self, communicator):
        """对已有的 communicator 进行连接并排空初始消息。"""
        connected, _ = await communicator.connect(timeout=10)
        if connected:
            await self.drain_messages(communicator)
        return connected, communicator

    async def send_json(self, communicator, payload):
        await communicator.send_json_to(payload)

    async def receive_json(self, communicator, timeout=10):
        return await communicator.receive_json_from(timeout=timeout)

    async def disconnect(self, communicator):
        try:
            await communicator.disconnect()
        except Exception:
            pass


class WebSocketAuthTests(ChatWebSocketTestBase):
    """WebSocket 连接认证测试"""

    async def test_valid_token_connects(self):
        """携带有效 jwt 子协议应成功连接公共聊天室。"""
        user = await self.create_user('ws_auth_user')
        access = await self.get_access_token(user)
        connected, communicator = await self.connect(access)
        self.assertTrue(connected)
        await self.disconnect(communicator)

    async def test_no_token_rejected(self):
        """不携带 token 应被拒绝连接。"""
        connected, _ = await self.connect()
        self.assertFalse(connected)

    async def test_invalid_token_rejected(self):
        """携带无效 token 应被拒绝连接。"""
        connected, _ = await self.connect('invalid-token')
        self.assertFalse(connected)

    async def test_disabled_user_rejected(self):
        """被禁用的用户携带有效 token 也应被拒绝连接。"""
        user = await self.create_user('ws_disabled_user')
        user.is_active = False
        await database_sync_to_async(user.save)()
        access = await self.get_access_token(user)
        connected, _ = await self.connect(access)
        self.assertFalse(connected)


class WebSocketMessageTests(ChatWebSocketTestBase):
    """WebSocket 消息收发测试"""

    async def test_chat_message_persisted(self):
        """用户发送公共聊天消息后，消息应被持久化到 ChatMessage 模型。"""
        user = await self.create_user('ws_sender')
        access = await self.get_access_token(user)
        connected, communicator = await self.connect(access)
        self.assertTrue(connected)

        self.assertEqual(await database_sync_to_async(ChatMessage.objects.count)(), 0)
        await self.send_json(communicator, {
            'type': 'chat_message',
            'message': 'hello persistence'
        })

        response = await self.receive_json(communicator)
        self.assertEqual(response['type'], 'message_received')

        self.assertEqual(await database_sync_to_async(ChatMessage.objects.count)(), 1)
        message = await database_sync_to_async(ChatMessage.objects.first)()
        self.assertEqual(message.content, 'hello persistence')
        # 避免在异步上下文触发关联查询，直接比较 user_id
        self.assertEqual(message.user_id, user.id)

        await self.disconnect(communicator)

    async def test_chat_message_broadcast_to_room(self):
        """同一房间内的其他用户应收到发送的聊天消息。"""
        user1 = await self.create_user('ws_sender1')
        user2 = await self.create_user('ws_sender2')
        access1 = await self.get_access_token(user1)
        access2 = await self.get_access_token(user2)

        comm1 = self.get_communicator(access1)
        connected1, _ = await self.connect_communicator(comm1)
        self.assertTrue(connected1)

        comm2 = self.get_communicator(access2)
        connected2, _ = await self.connect_communicator(comm2)
        self.assertTrue(connected2)

        # user2 连接时会广播在线人数更新给房间内的 user1
        await self.drain_messages(comm1)

        await self.send_json(comm1, {
            'type': 'chat_message',
            'message': 'broadcast message'
        })

        # 发送者会同时收到广播消息与服务端确认，顺序不固定，取到 chat_message 为止
        sender_msg = await self.receive_json(comm1)
        while sender_msg['type'] != 'chat_message':
            sender_msg = await self.receive_json(comm1)
        self.assertEqual(sender_msg['type'], 'chat_message')
        self.assertEqual(sender_msg['message'], 'broadcast message')

        # 同一房间内其他用户收到广播消息
        other_msg = await self.receive_json(comm2)
        while other_msg['type'] != 'chat_message':
            other_msg = await self.receive_json(comm2)
        self.assertEqual(other_msg['type'], 'chat_message')
        self.assertEqual(other_msg['message'], 'broadcast message')
        self.assertEqual(other_msg['username'], user1.username)

        await self.disconnect(comm1)
        await self.disconnect(comm2)


@override_settings(REST_FRAMEWORK=DISABLE_THROTTLE_SETTINGS)
class ChatAPITestBase(APITestCase):
    """聊天 API 测试基类"""

    def create_user(self, username='api_user', password='TestPass123!', **kwargs):
        if 'email' not in kwargs:
            kwargs['email'] = f'{username}@example.com'
        return User.objects.create_user(
            username=username, password=password, **kwargs
        )

    def authenticate(self, user):
        access = str(RefreshToken.for_user(user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        return access


@override_settings(REST_FRAMEWORK=DISABLE_THROTTLE_SETTINGS)
class RecentMessagesAPITests(ChatAPITestBase):
    """recent_messages 接口测试"""

    def test_recent_messages_returns_recent_messages(self):
        """GET /api/chat/messages/recent_messages/ 应返回最近消息，按时间倒序。"""
        user = self.create_user('recent_user')
        ChatMessage.objects.create(user=user, content='older')
        ChatMessage.objects.create(user=user, content='newer')

        response = self.client.get('/api/chat/messages/recent_messages/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        contents = [m['content'] for m in response.data]
        self.assertEqual(len(contents), 2)
        self.assertIn('older', contents)
        self.assertIn('newer', contents)


@override_settings(REST_FRAMEWORK=DISABLE_THROTTLE_SETTINGS)
class ChatMessageViewSetTests(ChatAPITestBase):
    """ChatMessageViewSet 接口测试"""

    def test_list_messages_authenticated(self):
        """已认证用户访问 list 应返回分页的消息列表。"""
        user = self.create_user('list_user')
        self.authenticate(user)
        ChatMessage.objects.create(user=user, content='msg_one')
        ChatMessage.objects.create(user=user, content='msg_two')

        response = self.client.get('/api/chat/messages/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        contents = [m['content'] for m in response.data['results']]
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(contents), 2)
        self.assertIn('msg_one', contents)
        self.assertIn('msg_two', contents)

    def test_list_messages_unauthenticated(self):
        """未认证用户访问 list 应返回 401。"""
        response = self.client.get('/api/chat/messages/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


@override_settings(REST_FRAMEWORK=DISABLE_THROTTLE_SETTINGS)
class OnlineUsersAPITests(ChatAPITestBase):
    """online_users 接口测试"""

    def test_get_online_users(self):
        """GET /api/chat/messages/online_users/ 应返回在线人数与统计指标。"""
        response = self.client.get('/api/chat/messages/online_users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)
        self.assertIn('metric', response.data)
        self.assertEqual(response.data['metric'], 'recently_active')
        self.assertIn('window_seconds', response.data)
        self.assertEqual(response.data['window_seconds'], presence.WINDOW_SECONDS)
