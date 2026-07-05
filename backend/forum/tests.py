from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Category, Board, Topic, Post, Bookmark, Like, Tag

User = get_user_model()


class ForumBaseAPITest(APITestCase):
    """论坛 API 测试基类，提供通用辅助方法。"""

    def setUp(self):
        cache.clear()

        self.user = self.create_user('topicauthor')
        self.other_user = self.create_user('otheruser')
        self.admin = self.create_user('adminuser', is_staff=True)

        self.category = Category.objects.create(name='测试分类', description='测试用分类')
        self.board = Board.objects.create(
            category=self.category,
            name='测试板块',
            description='测试用板块'
        )

        self.topic = self.create_topic(
            author=self.user,
            board=self.board,
            title='测试主题',
            content='主题首贴内容'
        )
        self.first_post = Post.objects.get(topic=self.topic, is_first_post=True)

    def create_user(self, username, password='TestPass123!', **kwargs):
        kwargs.setdefault('email', f'{username}@example.com')
        return User.objects.create_user(username=username, password=password, **kwargs)

    def get_tokens(self, user):
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token), str(refresh)

    def authenticate(self, user):
        access, _ = self.get_tokens(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')

    def create_board(self, name='测试板块', category=None, **kwargs):
        if category is None:
            category = Category.objects.create(name=f'{name}分类')
        return Board.objects.create(category=category, name=name, **kwargs)

    def create_topic(self, author, board, title='测试主题', content='测试内容', tags=None):
        topic = Topic.objects.create(board=board, title=title, author=author)
        Post.objects.create(
            topic=topic,
            author=author,
            content=content,
            is_first_post=True,
            content_status='approved'
        )
        if tags:
            for tag_name in tags:
                tag, _ = Tag.objects.get_or_create(name=tag_name)
                topic.tags.add(tag)
        return topic

    def create_post(self, author, topic, content='回复内容'):
        return Post.objects.create(
            topic=topic,
            author=author,
            content=content,
            content_status='approved'
        )


class TopicTests(ForumBaseAPITest):
    """主题相关测试。"""

    def test_create_topic_authenticated(self):
        """已认证用户可以创建主题并自动生成首贴。"""
        self.authenticate(self.user)
        response = self.client.post('/api/topics/', {
            'title': '新主题',
            'board': self.board.id,
            'content': '新主题内容'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], '新主题')
        self.assertTrue(
            Post.objects.filter(topic_id=response.data['id'], is_first_post=True).exists()
        )

    def test_create_topic_unauthenticated(self):
        """未认证用户不能创建主题。"""
        response = self.client.post('/api/topics/', {
            'title': '匿名主题',
            'board': self.board.id,
            'content': '匿名内容'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_topic_list_anonymous(self):
        """未认证用户可以查看主题列表。"""
        response = self.client.get('/api/topics/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertGreaterEqual(response.data['count'], 1)

    def test_topic_detail_anonymous(self):
        """未认证用户可以查看主题详情。"""
        response = self.client.get(f'/api/topics/{self.topic.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.topic.id)
        self.assertEqual(response.data['title'], self.topic.title)

    def test_topic_posts_action(self):
        """可以通过主题详情下的 posts 动作获取帖子列表。"""
        response = self.client.get(f'/api/topics/{self.topic.id}/posts/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        returned_ids = {post['id'] for post in response.data['results']}
        self.assertIn(self.first_post.id, returned_ids)

    def test_close_topic_by_author(self):
        """作者可以关闭自己的主题。"""
        self.authenticate(self.user)
        response = self.client.post(f'/api/topics/{self.topic.id}/close/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.topic.refresh_from_db()
        self.assertTrue(self.topic.is_closed)

    def test_close_topic_by_admin(self):
        """管理员可以关闭他人主题。"""
        self.authenticate(self.admin)
        response = self.client.post(f'/api/topics/{self.topic.id}/close/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.topic.refresh_from_db()
        self.assertTrue(self.topic.is_closed)

    def test_close_topic_by_non_author(self):
        """非作者/非管理员不能关闭他人主题。"""
        self.authenticate(self.other_user)
        response = self.client.post(f'/api/topics/{self.topic.id}/close/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class PostTests(ForumBaseAPITest):
    """帖子相关测试。"""

    def test_create_post_authenticated(self):
        """已认证用户可以在主题下创建帖子。"""
        self.authenticate(self.user)
        response = self.client.post('/api/posts/', {
            'topic': self.topic.id,
            'content': '这是我的回复'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['content'], '这是我的回复')
        self.assertEqual(response.data['topic'], self.topic.id)

    def test_create_post_unauthenticated(self):
        """未认证用户不能创建帖子。"""
        response = self.client.post('/api/posts/', {
            'topic': self.topic.id,
            'content': '匿名回复'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_list(self):
        """帖子列表应返回主题下的帖子。"""
        reply = self.create_post(self.other_user, self.topic, '列表中的回复')

        response = self.client.get('/api/posts/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        returned_ids = {post['id'] for post in response.data['results']}
        self.assertIn(self.first_post.id, returned_ids)
        self.assertIn(reply.id, returned_ids)

    def test_post_detail(self):
        """可以查看帖子详情。"""
        response = self.client.get(f'/api/posts/{self.first_post.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.first_post.id)
        self.assertEqual(response.data['content'], self.first_post.content)


class LikeTests(ForumBaseAPITest):
    """点赞相关测试。"""

    def test_like_post(self):
        """已认证用户可以点赞帖子。"""
        self.authenticate(self.other_user)
        response = self.client.post(f'/api/posts/{self.first_post.id}/like/')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Like.objects.filter(user=self.other_user, post=self.first_post).exists())

    def test_unlike_post(self):
        """可以通过 DELETE 请求取消点赞。"""
        self.authenticate(self.other_user)
        self.client.post(f'/api/posts/{self.first_post.id}/like/')

        response = self.client.delete(f'/api/posts/{self.first_post.id}/unlike/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Like.objects.filter(user=self.other_user, post=self.first_post).exists())

    def test_duplicate_like_toggles(self):
        """当前实现中重复点赞会取消点赞（toggle 行为）。"""
        self.authenticate(self.other_user)
        first = self.client.post(f'/api/posts/{self.first_post.id}/like/')
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)

        second = self.client.post(f'/api/posts/{self.first_post.id}/like/')
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertFalse(Like.objects.filter(user=self.other_user, post=self.first_post).exists())

    def test_unlike_not_liked_post(self):
        """取消未点赞的帖子应返回 404。"""
        self.authenticate(self.other_user)
        response = self.client.delete(f'/api/posts/{self.first_post.id}/unlike/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class BookmarkTests(ForumBaseAPITest):
    """收藏相关测试。"""

    def test_bookmark_topic(self):
        """已认证用户可以收藏主题。"""
        self.authenticate(self.user)
        response = self.client.post(f'/api/topics/{self.topic.id}/bookmark/')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Bookmark.objects.filter(user=self.user, topic=self.topic).exists())

    def test_unbookmark_topic(self):
        """可以通过 DELETE 请求取消收藏主题。"""
        self.authenticate(self.user)
        self.client.post(f'/api/topics/{self.topic.id}/bookmark/')

        response = self.client.delete(f'/api/topics/{self.topic.id}/unbookmark/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Bookmark.objects.filter(user=self.user, topic=self.topic).exists())

    def test_my_bookmarks(self):
        """可以获取我的收藏主题列表。"""
        self.authenticate(self.user)
        self.client.post(f'/api/topics/{self.topic.id}/bookmark/')

        response = self.client.get('/api/my-bookmarks/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.topic.id)

    def test_duplicate_bookmark_is_idempotent(self):
        """重复收藏不会创建多条记录，返回已收藏提示。"""
        self.authenticate(self.user)
        first = self.client.post(f'/api/topics/{self.topic.id}/bookmark/')
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)

        second = self.client.post(f'/api/topics/{self.topic.id}/bookmark/')
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertEqual(Bookmark.objects.filter(user=self.user, topic=self.topic).count(), 1)


class ForumPermissionTests(ForumBaseAPITest):
    """论坛权限相关测试。"""

    def test_unauthenticated_cannot_create_topic(self):
        """未认证用户不能创建主题。"""
        response = self.client.post('/api/topics/', {
            'title': '权限测试主题',
            'board': self.board.id,
            'content': '内容'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_cannot_create_post(self):
        """未认证用户不能创建帖子。"""
        response = self.client.post('/api/posts/', {
            'topic': self.topic.id,
            'content': '权限测试回复'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_author_cannot_close_topic(self):
        """非作者、非管理员、非版主不能关闭他人主题。"""
        self.authenticate(self.other_user)
        response = self.client.post(f'/api/topics/{self.topic.id}/close/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
