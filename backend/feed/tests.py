from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from forum.models import Category, Board, Topic, Post, Tag as ForumTag
from content.models import ContentType, Content, Tag as ContentTag
from users.activities import Activity
from users.friendship import Friend
from schools.models import School, Event, Place

User = get_user_model()


class FeedBaseAPITest(APITestCase):
    """Feed API 测试基类。"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='feeduser', password='TestPass123!', email='feed@example.com'
        )
        self.friend = User.objects.create_user(
            username='feedfriend', password='TestPass123!', email='friend@example.com'
        )
        self.other_user = User.objects.create_user(
            username='feedother', password='TestPass123!', email='other@example.com'
        )

        # 论坛数据
        self.category = Category.objects.create(name='Feed分类', description='测试分类')
        self.board = Board.objects.create(
            category=self.category, name='Feed板块', description='测试板块'
        )
        self.topic = Topic.objects.create(
            board=self.board, title='Feed主题', author=self.user
        )
        Post.objects.create(
            topic=self.topic,
            author=self.user,
            content='首贴内容',
            is_first_post=True,
            content_status='approved'
        )

        # 内容数据
        self.content_type, _ = ContentType.objects.get_or_create(
            name='feed-article-type', defaults={'description': '测试类型'}
        )
        self.content = Content.objects.create(
            title='Feed文章',
            slug='feed-article',
            content_type=self.content_type,
            author=self.user,
            content='文章内容',
            summary='文章摘要',
            status='published',
            publish_date=timezone.now()
        )

        # 动态数据
        self.activity = Activity.objects.create(
            user=self.user,
            activity_type='custom',
            content='用户动态内容',
            is_public=True
        )

        # 好友关系
        Friend.objects.create(user1=self.user, user2=self.friend)

    def authenticate(self, user):
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')


class FeedRecommendTests(FeedBaseAPITest):
    """推荐 Feed 测试。"""

    def test_feed_recommend_authenticated(self):
        """已认证用户可以获取推荐 Feed。"""
        self.authenticate(self.user)
        response = self.client.get('/api/feed/feed/', {'type': 'recommend'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['type'], 'recommend')
        object_types = {item['object_type'] for item in response.data['results']}
        self.assertIn('topic', object_types)
        self.assertIn('content', object_types)
        self.assertIn('activity', object_types)

    def test_feed_recommend_anonymous(self):
        """未认证用户可以获取推荐 Feed。"""
        response = self.client.get('/api/feed/feed/', {'type': 'recommend'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)

    def test_feed_pagination(self):
        """Feed 分页参数生效。"""
        response = self.client.get(
            '/api/feed/feed/',
            {'type': 'recommend', 'page': 1, 'page_size': 2},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['page'], 1)
        self.assertEqual(response.data['page_size'], 2)
        self.assertLessEqual(len(response.data['results']), 2)

    def test_feed_invalid_type(self):
        """无效的 feed 类型返回 400。"""
        response = self.client.get('/api/feed/feed/', {'type': 'unknown'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class FeedFollowingTests(FeedBaseAPITest):
    """关注 Feed 测试。"""

    def test_feed_following_with_friends(self):
        """有好友时返回好友发布的内容。"""
        friend_topic = Topic.objects.create(
            board=self.board, title='好友主题', author=self.friend
        )
        Post.objects.create(
            topic=friend_topic,
            author=self.friend,
            content='好友首贴',
            is_first_post=True,
            content_status='approved'
        )

        self.authenticate(self.user)
        response = self.client.get('/api/feed/feed/', {'type': 'following'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        object_ids = [item['object_id'] for item in response.data['results']]
        self.assertIn(friend_topic.id, object_ids)

    def test_feed_following_no_friends(self):
        """没有好友时返回空列表。"""
        Friend.objects.all().delete()
        self.authenticate(self.user)
        response = self.client.get('/api/feed/feed/', {'type': 'following'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_feed_following_anonymous(self):
        """未认证用户获取关注 Feed 返回空列表。"""
        response = self.client.get('/api/feed/feed/', {'type': 'following'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)


class FeedNearbyTests(FeedBaseAPITest):
    """附近 Feed 测试。"""

    def setUp(self):
        super().setUp()
        self.school = School.objects.create(
            name='附近测试学校',
            abbreviation='附近测试',
            province='北京市',
            city='北京市',
            school_type='comprehensive',
            school_level='985'
        )
        self.place = Place.objects.create(
            name='附近地点',
            school=self.school,
            category='landmark',
            latitude=39.9,
            longitude=116.4,
            is_active=True
        )
        self.event = Event.objects.create(
            title='附近活动',
            description='活动描述',
            school=self.school,
            start_time=timezone.now() + timedelta(days=1),
            end_time=timezone.now() + timedelta(days=1, hours=2),
            location='活动地点',
            organizer='组织者',
            status='upcoming',
            is_public=True
        )

    def test_feed_nearby_with_location(self):
        """提供经纬度时返回附近活动。"""
        response = self.client.get(
            '/api/feed/feed/',
            {'type': 'nearby', 'lat': '39.9', 'lng': '116.4', 'radius': '10'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        object_types = {item['object_type'] for item in response.data['results']}
        self.assertIn('event', object_types)

    def test_feed_nearby_without_location(self):
        """未提供经纬度时返回空列表。"""
        response = self.client.get('/api/feed/feed/', {'type': 'nearby'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_feed_nearby_invalid_location(self):
        """非法经纬度返回空列表。"""
        response = self.client.get(
            '/api/feed/feed/',
            {'type': 'nearby', 'lat': 'invalid', 'lng': 'invalid'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)


class FeedTrendingTopicsTests(FeedBaseAPITest):
    """热门话题测试。"""

    def setUp(self):
        super().setUp()
        self.forum_tag, _ = ForumTag.objects.get_or_create(
            name='feed-forum-tag', defaults={'description': '测试'}
        )
        self.topic.tags.add(self.forum_tag)

        self.content_tag, _ = ContentTag.objects.get_or_create(
            name='feed-content-tag', defaults={'description': '测试'}
        )
        self.content.tags.add(self.content_tag)

    def test_trending_topics(self):
        """返回热门话题/标签列表。"""
        response = self.client.get('/api/feed/trending_topics/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        names = {item['name'] for item in response.data}
        self.assertIn(self.forum_tag.name, names)
        self.assertIn(self.content_tag.name, names)

    def test_trending_topics_order(self):
        """按关联数量倒序排列。"""
        popular_tag, _ = ForumTag.objects.get_or_create(name='feed-popular-tag')
        for i in range(3):
            topic = Topic.objects.create(
                board=self.board, title=f'热门主题{i}', author=self.user
            )
            topic.tags.add(popular_tag)

        response = self.client.get('/api/feed/trending_topics/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        if len(response.data) >= 2:
            self.assertGreaterEqual(response.data[0]['count'], response.data[1]['count'])
