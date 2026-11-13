"""
搜索服务：封装 Elasticsearch 查询，并在 ES 不可用时降级为 MySQL LIKE 搜索。
"""

import logging

from django.conf import settings
from django.db.models import Q
from elasticsearch_dsl import Search
from elasticsearch_dsl.connections import connections

from .client import es_is_available
from .documents import (
    SchoolDocument, TopicDocument, PostDocument,
    ContentDocument, CourseDocument, UserDocument,
)

from schools.models import School
from forum.models import Topic, Post
from content.models import Content
from learning.models import Course
from users.models import User

logger = logging.getLogger(__name__)


class SearchService:
    """统一搜索服务。"""

    def __init__(self):
        self.fallback_enabled = getattr(settings, 'ELASTICSEARCH_FALLBACK_TO_DB', True)

    def _get_client(self):
        return connections.get_connection()

    def _build_multimatch(self, search, query, fields):
        """构建多字段 match 查询，优先使用 ik 分词。"""
        return search.query(
            'multi_match',
            query=query,
            fields=fields,
            type='best_fields',
            operator='or',
        )

    def _execute_es(self, search, limit):
        search = search[:limit]
        response = search.execute()
        return [hit.meta.id for hit in response.hits]

    # ----------------------------
    # 各类型搜索
    # ----------------------------

    def search_schools(self, query, limit=10):
        if not query:
            return School.objects.none()

        if es_is_available():
            try:
                s = self._build_multimatch(
                    Search(using=self._get_client(), index=SchoolDocument.Index.name),
                    query,
                    ['name^3', 'abbreviation^2', 'english_name', 'code', 'description', 'province', 'city']
                )
                ids = self._execute_es(s, limit)
                return School.objects.filter(pk__in=ids)
            except Exception as exc:
                logger.warning(f"ES 学校搜索失败，降级到数据库: {exc}")

        if not self.fallback_enabled:
            return School.objects.none()

        return School.objects.filter(
            Q(name__icontains=query) |
            Q(english_name__icontains=query) |
            Q(abbreviation__icontains=query) |
            Q(code__icontains=query)
        ).distinct()[:limit]

    def search_topics(self, query, limit=10):
        if not query:
            return Topic.objects.none()

        if es_is_available():
            try:
                s = self._build_multimatch(
                    Search(using=self._get_client(), index=TopicDocument.Index.name),
                    query,
                    ['title^3', 'content', 'author_username', 'board_name', 'tags']
                ).filter('term', status='normal')
                ids = self._execute_es(s, limit)
                return Topic.objects.filter(pk__in=ids).exclude(status='hidden')
            except Exception as exc:
                logger.warning(f"ES 主题搜索失败，降级到数据库: {exc}")

        if not self.fallback_enabled:
            return Topic.objects.none()

        return Topic.objects.filter(
            Q(title__icontains=query),
            ~Q(status='hidden')
        ).distinct()[:limit]

    def search_posts(self, query, limit=10):
        if not query:
            return Post.objects.none()

        if es_is_available():
            try:
                s = self._build_multimatch(
                    Search(using=self._get_client(), index=PostDocument.Index.name),
                    query,
                    ['content^2', 'topic_title^2', 'author_username']
                ).filter('term', content_status='approved')
                ids = self._execute_es(s, limit)
                return Post.objects.filter(pk__in=ids).select_related('topic', 'author')
            except Exception as exc:
                logger.warning(f"ES 帖子搜索失败，降级到数据库: {exc}")

        if not self.fallback_enabled:
            return Post.objects.none()

        return Post.objects.filter(
            Q(content__icontains=query) | Q(topic__title__icontains=query),
            content_status='approved'
        ).select_related('topic', 'author').distinct()[:limit]

    def search_contents(self, query, limit=10):
        if not query:
            return Content.objects.none()

        if es_is_available():
            try:
                s = self._build_multimatch(
                    Search(using=self._get_client(), index=ContentDocument.Index.name),
                    query,
                    ['title^3', 'summary^2', 'content', 'author_username', 'category_name', 'tags']
                ).filter('term', status='published')
                ids = self._execute_es(s, limit)
                return Content.objects.filter(pk__in=ids)
            except Exception as exc:
                logger.warning(f"ES 内容搜索失败，降级到数据库: {exc}")

        if not self.fallback_enabled:
            return Content.objects.none()

        return Content.objects.filter(
            Q(title__icontains=query) |
            Q(summary__icontains=query) |
            Q(content__icontains=query) |
            Q(author__username__icontains=query),
            status='published'
        ).distinct()[:limit]

    def search_courses(self, query, limit=10):
        if not query:
            return Course.objects.none()

        if es_is_available():
            try:
                s = self._build_multimatch(
                    Search(using=self._get_client(), index=CourseDocument.Index.name),
                    query,
                    ['title^3', 'description^2', 'instructor_username', 'categories']
                ).filter('term', is_published=True)
                ids = self._execute_es(s, limit)
                return Course.objects.filter(pk__in=ids)
            except Exception as exc:
                logger.warning(f"ES 课程搜索失败，降级到数据库: {exc}")

        if not self.fallback_enabled:
            return Course.objects.none()

        return Course.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(instructor__username__icontains=query),
            is_published=True
        ).distinct()[:limit]

    def search_users(self, query, limit=10, include_private=False, current_user=None):
        if not query:
            return User.objects.none()

        if es_is_available():
            try:
                fields = ['username^3', 'school', 'major', 'bio']
                if include_private:
                    fields.extend(['email', 'phone'])
                s = self._build_multimatch(
                    Search(using=self._get_client(), index=UserDocument.Index.name),
                    query,
                    fields
                )
                ids = self._execute_es(s, limit)
                queryset = User.objects.filter(pk__in=ids)
                if not include_private:
                    queryset = queryset.filter(is_active=True)
                return queryset
            except Exception as exc:
                logger.warning(f"ES 用户搜索失败，降级到数据库: {exc}")

        if not self.fallback_enabled:
            return User.objects.none()

        filters = Q(username__icontains=query)
        if include_private:
            filters |= Q(email__icontains=query) | Q(phone__icontains=query)
        return User.objects.filter(filters).distinct()[:limit]

    # ----------------------------
    # 搜索建议
    # ----------------------------

    def get_suggestions(self, query, limit=5):
        """返回各类型搜索建议，用于搜索框下拉提示。"""
        if not query:
            return []

        suggestions = []

        # 课程建议
        for course in self.search_courses(query, limit):
            suggestions.append({'type': 'course', 'id': course.id, 'title': course.title, 'slug': course.slug})

        # 内容建议
        for content in self.search_contents(query, limit):
            suggestions.append({'type': 'content', 'id': content.id, 'title': content.title, 'slug': content.slug})

        # 学校建议
        for school in self.search_schools(query, limit):
            suggestions.append({'type': 'school', 'id': school.id, 'title': school.name})

        # 主题建议
        for topic in self.search_topics(query, limit):
            suggestions.append({'type': 'topic', 'id': topic.id, 'title': topic.title})

        return suggestions
