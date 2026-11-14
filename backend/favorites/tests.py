"""收藏模块测试。

覆盖多态收藏、重复收藏、学校收藏同步、取消收藏与越权访问。
"""

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient

from schools.models import School

from .models import Favorite

User = get_user_model()


class FavoriteAPITests(TestCase):
    """收藏接口测试。"""

    def setUp(self):
        cache.clear()
        self.alice = User.objects.create_user(username='alice', password='testpass', email='alice@example.com')
        self.bob = User.objects.create_user(username='bob', password='testpass', email='bob@example.com')

        self.school = School.objects.create(
            name='测试大学',
            abbreviation='测试',
            province='北京市',
            city='北京市',
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.alice)

        self.favorites_url = '/api/users/favorites/'
        self.content_type = 'schools.school'

        self.points_patcher = patch('favorites.views.queue_update_user_points')
        self.mock_points = self.points_patcher.start()
        self.addCleanup(self.points_patcher.stop)

    def _add_school_favorite(self, client=None, school=None):
        client = client or self.client
        school = school or self.school
        return client.post(
            f'{self.favorites_url}add_favorite/',
            {
                'content_type': self.content_type,
                'object_id': school.id,
                'category': '目标院校',
                'note': '重点关注',
            },
            format='json',
        )

    def test_add_favorite_creates_record_and_syncs_school(self):
        """添加学校收藏应落库、同步用户收藏学校并发放积分。"""
        response = self._add_school_favorite()

        self.assertEqual(response.status_code, 201)
        favorite = Favorite.objects.get()
        self.assertEqual(favorite.user, self.alice)
        self.assertEqual(favorite.object_id, self.school.id)
        self.assertEqual(favorite.category, '目标院校')

        self.assertTrue(self.alice.favorite_schools.filter(id=self.school.id).exists())
        self.mock_points.assert_called_once()
        self.assertEqual(self.mock_points.call_args.args[0], self.alice.id)
        self.assertEqual(self.mock_points.call_args.args[1], 'favorite')

    def test_duplicate_favorite_rejected(self):
        """重复收藏同一对象应返回 400。"""
        self._add_school_favorite()

        response = self._add_school_favorite()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Favorite.objects.count(), 1)

    def test_invalid_content_type_rejected(self):
        """非法内容类型应返回 400。"""
        response = self.client.post(
            f'{self.favorites_url}add_favorite/',
            {'content_type': 'invalid', 'object_id': self.school.id},
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Favorite.objects.count(), 0)

    def test_nonexistent_target_rejected(self):
        """收藏不存在的对象应返回 400。"""
        response = self.client.post(
            f'{self.favorites_url}add_favorite/',
            {'content_type': self.content_type, 'object_id': 999999},
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Favorite.objects.count(), 0)

    def test_check_favorite(self):
        """check_favorite 正确返回收藏状态。"""
        self._add_school_favorite()

        response = self.client.get(
            f'{self.favorites_url}check_favorite/',
            {'content_type': self.content_type, 'object_id': self.school.id},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['is_favorited'])

    def test_check_favorite_requires_params(self):
        """check_favorite 缺少参数时返回 400。"""
        response = self.client.get(f'{self.favorites_url}check_favorite/')

        self.assertEqual(response.status_code, 400)

    def test_remove_favorite(self):
        """取消收藏应删除记录并解除学校同步关系。"""
        self._add_school_favorite()

        response = self.client.delete(
            f'{self.favorites_url}remove_favorite/',
            {'content_type': self.content_type, 'object_id': self.school.id},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Favorite.objects.count(), 0)
        self.assertFalse(self.alice.favorite_schools.filter(id=self.school.id).exists())

    def test_remove_missing_favorite_returns_404(self):
        """取消不存在的收藏返回 404。"""
        response = self.client.delete(
            f'{self.favorites_url}remove_favorite/',
            {'content_type': self.content_type, 'object_id': self.school.id},
            format='json',
        )

        self.assertEqual(response.status_code, 404)

    def test_remove_favorite_requires_params(self):
        """取消收藏缺少参数时返回 400。"""
        response = self.client.delete(
            f'{self.favorites_url}remove_favorite/',
            {},
            format='json',
        )

        self.assertEqual(response.status_code, 400)

    def test_list_returns_only_own_favorites(self):
        """收藏列表只返回当前用户的记录。"""
        self._add_school_favorite()

        other_client = APIClient()
        other_client.force_authenticate(user=self.bob)
        other_response = self._add_school_favorite(client=other_client)

        self.assertEqual(other_response.status_code, 201)

        response = self.client.get(self.favorites_url)

        self.assertEqual(response.status_code, 200)
        results = response.data['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['object_id'], self.school.id)
        self.assertEqual(results[0]['content_object_name'], self.school.name)

    def test_add_favorite_requires_authentication(self):
        """未登录用户不能添加收藏。"""
        self.client.force_authenticate(user=None)

        response = self._add_school_favorite()

        self.assertEqual(response.status_code, 401)
        self.assertEqual(Favorite.objects.count(), 0)
