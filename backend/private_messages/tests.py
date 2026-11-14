"""私信模块测试。

覆盖消息创建、会话查询、已读状态、未读数与越权访问。
"""

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient

from .models import Message

User = get_user_model()


class MessageAPITests(TestCase):
    """私信接口测试。"""

    def setUp(self):
        cache.clear()
        self.alice = User.objects.create_user(username='alice', password='testpass', email='alice@example.com')
        self.bob = User.objects.create_user(username='bob', password='testpass', email='bob@example.com')
        self.carol = User.objects.create_user(username='carol', password='testpass', email='carol@example.com')

        self.client = APIClient()
        self.client.force_authenticate(user=self.alice)

        self.messages_url = '/api/users/messages/'

    def _create_message(self, sender, receiver, content='你好', is_read=False):
        return Message.objects.create(
            sender=sender,
            receiver=receiver,
            content=content,
            is_read=is_read,
        )

    def test_create_message_saves_and_pushes(self):
        """创建私信应落库并触发通知与 WebSocket 推送。"""
        with patch('private_messages.views.send_notification_to_user') as mock_notify, \
                patch('private_messages.views.websocket_service.send_private_message') as mock_push:
            response = self.client.post(
                self.messages_url,
                {'receiver': self.bob.id, 'content': '晚上一起自习吗'},
                format='json',
            )

        self.assertEqual(response.status_code, 201)
        message = Message.objects.get()
        self.assertEqual(message.sender, self.alice)
        self.assertEqual(message.receiver, self.bob)
        self.assertFalse(message.is_read)

        mock_notify.assert_called_once()
        self.assertEqual(mock_notify.call_args.kwargs['user'], self.bob)
        mock_push.assert_called_once()
        self.assertEqual(mock_push.call_args.args[1], self.bob)

    def test_create_message_rejects_self(self):
        """不能给自己发送私信。"""
        response = self.client.post(
            self.messages_url,
            {'receiver': self.alice.id, 'content': '自言自语'},
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Message.objects.count(), 0)

    def test_create_message_rejects_blank_content(self):
        """空白内容应被拒绝。"""
        response = self.client.post(
            self.messages_url,
            {'receiver': self.bob.id, 'content': '   '},
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Message.objects.count(), 0)

    def test_create_message_requires_authentication(self):
        """未登录用户不能发送私信。"""
        self.client.force_authenticate(user=None)

        response = self.client.post(
            self.messages_url,
            {'receiver': self.bob.id, 'content': 'hi'},
            format='json',
        )

        self.assertEqual(response.status_code, 401)

    def test_user_messages_get_returns_two_way_conversation(self):
        """按用户查询应返回双向消息，且不包含第三方消息。"""
        self._create_message(self.alice, self.bob, 'a->b')
        self._create_message(self.bob, self.alice, 'b->a')
        self._create_message(self.bob, self.carol, 'b->c')

        response = self.client.get(f'{self.messages_url}{self.bob.id}/')

        self.assertEqual(response.status_code, 200)
        contents = [item['content'] for item in response.data]
        self.assertEqual(sorted(contents), ['a->b', 'b->a'])

    def test_user_messages_post_sends_message(self):
        """通过按用户路径发送私信应创建消息。"""
        with patch('private_messages.views.send_notification_to_user'), \
                patch('private_messages.views.websocket_service.send_private_message'):
            response = self.client.post(
                f'{self.messages_url}{self.bob.id}/',
                {'content': '周末打球吗'},
                format='json',
            )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            Message.objects.filter(sender=self.alice, receiver=self.bob, content='周末打球吗').exists()
        )

    def test_user_messages_post_rejects_blank_content(self):
        """按用户路径发送空消息应返回 400。"""
        response = self.client.post(
            f'{self.messages_url}{self.bob.id}/',
            {'content': '  '},
            format='json',
        )

        self.assertEqual(response.status_code, 400)

    def test_conversation_marks_incoming_messages_read(self):
        """打开会话应将对方发来的未读消息标记为已读。"""
        message = self._create_message(self.bob, self.alice, '未读消息')
        self._create_message(self.alice, self.bob, '我发出的消息')

        response = self.client.get(
            f'{self.messages_url}conversation/',
            {'user_id': self.bob.id},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['user']['id'], self.bob.id)
        self.assertEqual(len(response.data['messages']), 2)

        message.refresh_from_db()
        self.assertTrue(message.is_read)

    def test_conversation_requires_user_id(self):
        """缺少 user_id 时返回 400。"""
        response = self.client.get(f'{self.messages_url}conversation/')

        self.assertEqual(response.status_code, 400)

    def test_conversation_with_unknown_user_returns_400(self):
        """用户不存在时返回 400。"""
        response = self.client.get(
            f'{self.messages_url}conversation/',
            {'user_id': 999999},
        )

        self.assertEqual(response.status_code, 400)

    def test_conversation_pagination(self):
        """提供 page 参数时按页返回并给出总数。"""
        for index in range(3):
            self._create_message(self.alice, self.bob, f'消息{index}')

        response = self.client.get(
            f'{self.messages_url}conversation/',
            {'user_id': self.bob.id, 'page': 1, 'page_size': 2},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 3)
        self.assertEqual(len(response.data['messages']), 2)
        self.assertIsNotNone(response.data['next'])

    def test_conversation_does_not_leak_other_pairs(self):
        """查询与某人的会话不应泄露其他用户之间的消息。"""
        self._create_message(self.bob, self.carol, '私密内容')

        response = self.client.get(
            f'{self.messages_url}conversation/',
            {'user_id': self.bob.id},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['messages'], [])

    def test_unread_count(self):
        """未读数只统计收到的未读消息。"""
        self._create_message(self.bob, self.alice, '未读1')
        self._create_message(self.bob, self.alice, '未读2')
        self._create_message(self.carol, self.alice, '已读', is_read=True)
        self._create_message(self.alice, self.bob, '我发出的未读')

        response = self.client.get(f'{self.messages_url}unread_count/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['unread_count'], 2)

    def test_mark_all_read_only_affects_target_sender(self):
        """标记某人的消息已读不应影响其他发送者。"""
        self._create_message(self.bob, self.alice, '来自 bob')
        self._create_message(self.carol, self.alice, '来自 carol')

        response = self.client.post(
            f'{self.messages_url}mark_all_read/',
            {'user_id': self.bob.id},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            Message.objects.filter(sender=self.bob, receiver=self.alice, is_read=False).count(), 0
        )
        self.assertEqual(
            Message.objects.filter(sender=self.carol, receiver=self.alice, is_read=False).count(), 1
        )

    def test_mark_user_messages_read(self):
        """按用户批量标记已读只影响该用户发来的消息。"""
        self._create_message(self.bob, self.alice, 'bob 消息')
        self._create_message(self.carol, self.alice, 'carol 消息')

        response = self.client.post(f'{self.messages_url}{self.bob.id}/mark_read/')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            Message.objects.get(sender=self.bob, receiver=self.alice).is_read
        )
        self.assertFalse(
            Message.objects.get(sender=self.carol, receiver=self.alice).is_read
        )

    def test_list_excludes_unrelated_messages(self):
        """列表接口只返回与当前用户相关的消息。"""
        self._create_message(self.alice, self.bob, '相关')
        self._create_message(self.bob, self.carol, '无关')

        response = self.client.get(self.messages_url)

        self.assertEqual(response.status_code, 200)
        results = response.data['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['content'], '相关')
