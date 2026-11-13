"""搜索模块测试。

覆盖 Elasticsearch 降级、索引任务、搜索视图等核心场景。
"""

from unittest.mock import patch, MagicMock

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from content.models import ContentType as ArticleContentType, Content
from forum.models import Board, Category as ForumCategory, Topic, Post
from learning.models import Course
from schools.models import School
from search.services import SearchService
from search.tasks import index_object, remove_object_from_index

User = get_user_model()


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
)
class SearchServiceTests(TestCase):
    """搜索服务单元测试。"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='searchuser',
            password='testpass',
            email='search@example.com',
            school='测试大学',
        )
        self.school = School.objects.create(
            name='清华大学',
            province='北京',
            city='北京',
        )
        self.course = Course.objects.create(
            title='Python 入门',
            slug='python-intro',
            description='Python 基础课程',
            instructor=self.user,
            is_published=True,
        )
        self.content_type, _ = ArticleContentType.objects.get_or_create(name='文章')
        self.content = Content.objects.create(
            title='Python 学习指南',
            slug='python-guide',
            content_type=self.content_type,
            author=self.user,
            content='这是一篇关于 Python 的学习指南。',
            summary='Python 指南',
            status='published',
        )
        self.forum_category = ForumCategory.objects.create(name='技术')
        self.board = Board.objects.create(
            category=self.forum_category,
            name='Python 讨论',
            description='Python 技术讨论',
        )
        self.topic = Topic.objects.create(
            board=self.board,
            title='Python 问题求助',
            author=self.user,
            status='normal',
        )
        self.post = Post.objects.create(
            topic=self.topic,
            author=self.user,
            content='请问 Python 如何入门？',
            is_first_post=True,
        )

    @patch('search.services.es_is_available', return_value=False)
    def test_search_fallback_when_es_unavailable(self, _mock_es):
        """ES 不可用时，搜索应降级为数据库 LIKE 查询。"""
        service = SearchService()

        schools = service.search_schools('清华')
        self.assertIn(self.school, schools)

        courses = service.search_courses('Python')
        self.assertIn(self.course, courses)

        contents = service.search_contents('Python')
        self.assertIn(self.content, contents)

        topics = service.search_topics('Python')
        self.assertIn(self.topic, topics)

        posts = service.search_posts('入门')
        self.assertIn(self.post, posts)

        users = service.search_users('searchuser')
        self.assertIn(self.user, users)

    @patch('search.services.es_is_available', return_value=False)
    def test_search_suggestions_fallback(self, _mock_es):
        """搜索建议在 ES 不可用时返回数据库结果。"""
        service = SearchService()
        suggestions = service.get_suggestions('Python')

        types = {s['type'] for s in suggestions}
        self.assertIn('course', types)
        self.assertIn('content', types)
        self.assertIn('topic', types)

    @patch('search.services.es_is_available', return_value=False)
    def test_search_empty_query_returns_empty(self, _mock_es):
        """空查询应返回空结果集。"""
        service = SearchService()
        self.assertEqual(list(service.search_courses('', limit=10)), [])


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
)
class SearchIndexTaskTests(TestCase):
    """搜索索引异步任务测试。"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='indexuser',
            password='testpass',
            email='index@example.com',
        )

    @patch('search.tasks.es_is_available', return_value=False)
    def test_index_object_skips_when_es_unavailable(self, _mock_es):
        """ES 不可用时，索引任务应直接返回。"""
        result = index_object('users.User', self.user.id)
        self.assertIsNone(result)

    @patch('search.tasks.es_is_available', return_value=False)
    def test_remove_object_skips_when_es_unavailable(self, _mock_es):
        """ES 不可用时，删除索引任务应直接返回。"""
        result = remove_object_from_index('users.User', self.user.id)
        self.assertIsNone(result)

    @patch('search.tasks.es_is_available', return_value=True)
    @patch('search.tasks.get_es_client')
    @patch('search.tasks.UserDocument')
    def test_index_object_calls_save(self, mock_doc_class, _mock_client, _mock_es):
        """ES 可用时，索引任务应将文档保存到 ES。"""
        mock_doc = MagicMock()
        mock_doc_class.return_value = mock_doc

        index_object('users.User', self.user.id)

        mock_doc.save.assert_called_once()


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
)
class SearchViewTests(TestCase):
    """搜索视图测试。"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='viewuser',
            password='testpass',
            email='view@example.com',
        )
        self.school = School.objects.create(
            name='北京大学',
            province='北京',
            city='北京',
        )

    def test_global_search_empty_query(self):
        """空查询返回空结果结构。"""
        url = reverse('global_search')
        response = self.client.get(url, {'q': '', 'type': 'all'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['query'], '')
        self.assertEqual(response.data['results'], {})

    @patch('search.services.es_is_available', return_value=False)
    def test_global_search_with_query(self, _mock_es):
        """有查询时返回对应类型结果。"""
        url = reverse('global_search')
        response = self.client.get(url, {'q': '北京', 'type': 'school'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['query'], '北京')
        self.assertIn('schools', response.data['results'])
        self.assertEqual(len(response.data['results']['schools']), 1)

    @patch('search.services.es_is_available', return_value=False)
    def test_search_suggestions_view(self, _mock_es):
        """搜索建议视图返回建议列表。"""
        url = reverse('search_suggestions')
        response = self.client.get(url, {'q': '北京'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['query'], '北京')
        self.assertIsInstance(response.data['suggestions'], list)
