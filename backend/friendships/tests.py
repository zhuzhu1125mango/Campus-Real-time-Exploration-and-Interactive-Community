"""好友模块测试。

覆盖好友请求创建、接受/拒绝状态流转、重复请求、好友列表与解除关系。
"""

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient

from .models import Friend, FriendRequest

User = get_user_model()


class FriendRequestAPITests(TestCase):
    """好友请求接口测试。"""

    def setUp(self):
        cache.clear()
        self.alice = User.objects.create_user(username='alice', password='testpass', email='alice@example.com')
        self.bob = User.objects.create_user(username='bob', password='testpass', email='bob@example.com')
        self.carol = User.objects.create_user(username='carol', password='testpass', email='carol@example.com')

        self.client = APIClient()
        self.client.force_authenticate(user=self.alice)

        self.requests_url = '/api/users/friend-requests/'

    def _create_request(self, sender, receiver, status='pending'):
        return FriendRequest.objects.create(sender=sender, receiver=receiver, status=status)

    def test_send_request_creates_pending_and_notifies(self):
        """发送好友请求应创建 pending 记录并通知接收者。"""
        with patch('friendships.views.send_notification_to_user') as mock_notify:
            response = self.client.post(
                self.requests_url,
                {'receiver': self.bob.id},
                format='json',
            )

        self.assertEqual(response.status_code, 201)
        friend_request = FriendRequest.objects.get()
        self.assertEqual(friend_request.sender, self.alice)
        self.assertEqual(friend_request.receiver, self.bob)
        self.assertEqual(friend_request.status, 'pending')

        mock_notify.assert_called_once()
        self.assertEqual(mock_notify.call_args.kwargs['user'], self.bob)

    def test_cannot_send_request_to_self(self):
        """不能向自己发送好友请求。"""
        response = self.client.post(
            self.requests_url,
            {'receiver': self.alice.id},
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(FriendRequest.objects.count(), 0)

    def test_duplicate_pending_request_rejected(self):
        """重复发送待处理请求应返回 400。"""
        self._create_request(self.alice, self.bob)

        response = self.client.post(
            self.requests_url,
            {'receiver': self.bob.id},
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(FriendRequest.objects.count(), 1)

    def test_cannot_request_existing_friend(self):
        """已经是好友时不能再次发送请求。"""
        Friend.objects.create(user1=self.alice, user2=self.bob)

        response = self.client.post(
            self.requests_url,
            {'receiver': self.bob.id},
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(FriendRequest.objects.count(), 0)

    def test_list_only_involves_current_user(self):
        """请求列表只包含与当前用户相关的记录。"""
        self._create_request(self.alice, self.bob)
        self._create_request(self.bob, self.carol)

        response = self.client.get(self.requests_url)

        self.assertEqual(response.status_code, 200)
        results = response.data['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['sender']['id'], self.alice.id)

    def test_received_returns_pending_requests(self):
        """received 只返回待处理且发给当前用户的请求。"""
        pending = self._create_request(self.bob, self.alice)
        self._create_request(self.carol, self.alice, status='accepted')

        response = self.client.get(f'{self.requests_url}received/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['id'] for item in response.data], [pending.id])

    def test_sent_returns_requests_by_sender(self):
        """sent 返回当前用户发出的请求。"""
        sent = self._create_request(self.alice, self.bob)
        self._create_request(self.bob, self.carol)

        response = self.client.get(f'{self.requests_url}sent/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['id'] for item in response.data], [sent.id])

    def test_receiver_accepts_creates_friend_and_notifies(self):
        """接收者接受请求后应建立好友关系并通知发起者。"""
        friend_request = self._create_request(self.bob, self.alice)
        self.client.force_authenticate(user=self.alice)

        with patch('friendships.views.send_notification_to_user') as mock_notify:
            response = self.client.post(f'{self.requests_url}{friend_request.id}/accept/')

        self.assertEqual(response.status_code, 200)
        friend_request.refresh_from_db()
        self.assertEqual(friend_request.status, 'accepted')
        self.assertTrue(Friend.is_friend(self.alice, self.bob))

        mock_notify.assert_called_once()
        self.assertEqual(mock_notify.call_args.kwargs['user'], self.bob)

    def test_non_receiver_cannot_accept(self):
        """非接收者看不到该请求，接受时返回 404。"""
        friend_request = self._create_request(self.bob, self.alice)
        self.client.force_authenticate(user=self.carol)

        response = self.client.post(f'{self.requests_url}{friend_request.id}/accept/')

        self.assertEqual(response.status_code, 404)
        friend_request.refresh_from_db()
        self.assertEqual(friend_request.status, 'pending')
        self.assertFalse(Friend.is_friend(self.alice, self.bob))

    def test_accept_twice_returns_400(self):
        """已处理的请求不能重复接受。"""
        friend_request = self._create_request(self.bob, self.alice)
        self.client.force_authenticate(user=self.alice)

        first = self.client.post(f'{self.requests_url}{friend_request.id}/accept/')
        second = self.client.post(f'{self.requests_url}{friend_request.id}/accept/')

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 400)

    def test_reject_sets_status_and_creates_no_friend(self):
        """拒绝请求后状态变为 rejected，且不会建立好友关系。"""
        friend_request = self._create_request(self.bob, self.alice)
        self.client.force_authenticate(user=self.alice)

        response = self.client.post(f'{self.requests_url}{friend_request.id}/reject/')

        self.assertEqual(response.status_code, 200)
        friend_request.refresh_from_db()
        self.assertEqual(friend_request.status, 'rejected')
        self.assertFalse(Friend.is_friend(self.alice, self.bob))

    def test_non_receiver_cannot_reject(self):
        """非接收者看不到该请求，拒绝时返回 404。"""
        friend_request = self._create_request(self.bob, self.alice)
        self.client.force_authenticate(user=self.carol)

        response = self.client.post(f'{self.requests_url}{friend_request.id}/reject/')

        self.assertEqual(response.status_code, 404)
        friend_request.refresh_from_db()
        self.assertEqual(friend_request.status, 'pending')

    def test_requests_require_authentication(self):
        """未登录用户不能访问好友请求。"""
        self.client.force_authenticate(user=None)

        response = self.client.get(self.requests_url)

        self.assertEqual(response.status_code, 401)


class FriendAPITests(TestCase):
    """好友关系接口测试。"""

    def setUp(self):
        cache.clear()
        self.alice = User.objects.create_user(username='alice', password='testpass', email='alice@example.com')
        self.bob = User.objects.create_user(username='bob', password='testpass', email='bob@example.com')
        self.carol = User.objects.create_user(username='carol', password='testpass', email='carol@example.com')

        self.client = APIClient()
        self.client.force_authenticate(user=self.alice)

        self.friends_url = '/api/users/friends/'

    def test_friend_list_returns_both_directions(self):
        """好友列表应包含两个方向建立的关系。"""
        Friend.objects.create(user1=self.alice, user2=self.bob)
        Friend.objects.create(user1=self.carol, user2=self.alice)

        response = self.client.get(f'{self.friends_url}friend_list/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)
        usernames = {item['username'] for item in response.data['friends']}
        self.assertEqual(usernames, {'bob', 'carol'})

    def test_check_returns_friendship_state(self):
        """check 接口正确返回是否好友。"""
        Friend.objects.create(user1=self.alice, user2=self.bob)

        friend_response = self.client.get(
            f'{self.friends_url}check/', {'user_id': self.bob.id}
        )
        stranger_response = self.client.get(
            f'{self.friends_url}check/', {'user_id': self.carol.id}
        )

        self.assertTrue(friend_response.data['is_friend'])
        self.assertFalse(stranger_response.data['is_friend'])

    def test_check_requires_user_id(self):
        """check 缺少 user_id 时返回 400。"""
        response = self.client.get(f'{self.friends_url}check/')

        self.assertEqual(response.status_code, 400)

    def test_check_unknown_user_returns_404(self):
        """check 查询不存在的用户返回 404。"""
        response = self.client.get(f'{self.friends_url}check/', {'user_id': 999999})

        self.assertEqual(response.status_code, 404)

    def test_remove_friend(self):
        """解除好友关系应删除记录并通知对方。"""
        Friend.objects.create(user1=self.alice, user2=self.bob)

        with patch('friendships.views.send_notification_to_user') as mock_notify:
            response = self.client.post(
                f'{self.friends_url}remove/',
                {'friend_id': self.bob.id},
                format='json',
            )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Friend.is_friend(self.alice, self.bob))
        mock_notify.assert_called_once()
        self.assertEqual(mock_notify.call_args.kwargs['user'], self.bob)

    def test_remove_requires_friend_id(self):
        """缺少 friend_id 时返回 400。"""
        response = self.client.post(f'{self.friends_url}remove/', {}, format='json')

        self.assertEqual(response.status_code, 400)

    def test_remove_unknown_user_returns_404(self):
        """移除不存在的用户返回 404。"""
        response = self.client.post(
            f'{self.friends_url}remove/',
            {'friend_id': 999999},
            format='json',
        )

        self.assertEqual(response.status_code, 404)

    def test_friend_endpoints_require_authentication(self):
        """未登录用户不能访问好友接口。"""
        self.client.force_authenticate(user=None)

        response = self.client.get(f'{self.friends_url}friend_list/')

        self.assertEqual(response.status_code, 401)
