"""通知模块测试。

覆盖通知创建、WebSocket 推送、content_comment 类型映射、序列化器兼容等场景。
"""

from unittest.mock import patch, MagicMock, AsyncMock

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from notifications.models import Notification
from notifications.notification_sender import (
    create_notification,
    send_notification_to_user,
    notify_forum_event,
)
from notifications.serializers import NotificationSerializer
from users.tasks import send_notification_async

User = get_user_model()


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
)
class NotificationCreationTests(TestCase):
    """通知创建相关测试。"""

    def setUp(self):
        self.recipient = User.objects.create_user(
            username='recipient',
            password='testpass',
            email='recipient@example.com',
        )
        self.sender = User.objects.create_user(
            username='sender',
            password='testpass',
            email='sender@example.com',
        )

    def test_create_notification(self):
        """create_notification 应正确创建通知记录。"""
        notification = create_notification(
            recipient=self.recipient,
            title='测试通知',
            content='这是一条测试通知',
            notification_type='system',
            sender=self.sender,
            url='/test/',
        )

        self.assertEqual(notification.recipient, self.recipient)
        self.assertEqual(notification.sender, self.sender)
        self.assertEqual(notification.notification_type, 'system')
        self.assertEqual(notification.title, '测试通知')
        self.assertFalse(notification.is_read)

    def test_send_notification_to_user(self):
        """send_notification_to_user 应创建并返回通知。"""
        notification = send_notification_to_user(
            user=self.recipient,
            title='新私信',
            content='有人给你发了私信',
            notification_type='message',
        )

        self.assertIsNotNone(notification)
        self.assertEqual(notification.notification_type, 'message')

    def test_content_comment_type_mapping(self):
        """content_comment 论坛事件应映射为独立的 content_comment 通知类型。"""
        notification = notify_forum_event(
            recipient=self.recipient,
            sender=self.sender,
            forum_type='content_comment',
            message='有人评论了你的内容',
        )

        self.assertEqual(notification.notification_type, 'content_comment')
        self.assertEqual(notification.title, '新评论')

    def test_like_type_mapping(self):
        """like 论坛事件仍映射为 interaction 类型。"""
        notification = notify_forum_event(
            recipient=self.recipient,
            sender=self.sender,
            forum_type='like',
            message='有人点赞了你',
        )

        self.assertEqual(notification.notification_type, 'interaction')


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
)
class NotificationSerializerTests(TestCase):
    """通知序列化器测试。"""

    def setUp(self):
        self.recipient = User.objects.create_user(
            username='serialuser',
            password='testpass',
            email='serial@example.com',
        )

    def test_content_comment_serialization(self):
        """content_comment 类型通知应正确序列化。"""
        notification = Notification.objects.create(
            recipient=self.recipient,
            title='新评论',
            content='有人评论了你',
            notification_type='content_comment',
        )

        serializer = NotificationSerializer(notification)
        data = serializer.data

        self.assertEqual(data['notification_type'], 'content_comment')
        self.assertEqual(data['title'], '新评论')
        self.assertEqual(data['sender_username'], None)


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
)
class NotificationWebSocketTests(TestCase):
    """通知 WebSocket 推送测试。"""

    def setUp(self):
        self.recipient = User.objects.create_user(
            username='wsuser',
            password='testpass',
            email='ws@example.com',
        )
        self.notification = Notification.objects.create(
            recipient=self.recipient,
            title='推送测试',
            content='测试 WebSocket 推送',
            notification_type='system',
        )

    @patch('users.tasks.get_channel_layer')
    def test_send_notification_async_triggers_group_send(self, mock_get_channel_layer):
        """send_notification_async 应向用户通知组发送消息。"""
        mock_channel_layer = MagicMock()
        mock_channel_layer.group_send = AsyncMock()
        mock_get_channel_layer.return_value = mock_channel_layer

        send_notification_async(self.notification.id)

        # 应发送通知消息与未读数更新消息
        calls = mock_channel_layer.group_send.call_args_list
        self.assertEqual(len(calls), 2)

        # 第一次调用：通知消息
        group_name, payload = calls[0][0]
        self.assertEqual(group_name, f"user_{self.recipient.id}")
        self.assertEqual(payload['type'], 'notification')
        self.assertEqual(payload['notification']['title'], '推送测试')

        # 第二次调用：未读数更新
        group_name, payload = calls[1][0]
        self.assertEqual(group_name, f"user_{self.recipient.id}")
        self.assertEqual(payload['type'], 'unread_notifications_update')
        self.assertEqual(payload['count'], 1)

    def test_send_notification_async_missing_notification(self):
        """通知不存在时不应抛异常。"""
        result = send_notification_async(99999)
        self.assertIsNone(result)
