import time

from django.test import TestCase
from django.contrib.auth import get_user_model

from chat.views import RecentActivePresence, presence

User = get_user_model()


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
