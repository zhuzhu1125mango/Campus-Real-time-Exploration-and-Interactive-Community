"""
Elasticsearch Document 定义。

为全站搜索建立统一的索引结构，使用 ik 中文分词器。
"""

from django.conf import settings
from elasticsearch_dsl import Document, Text, Keyword, Integer, Boolean, Date, Float
from elasticsearch_dsl.connections import connections
from elasticsearch_dsl import Index


def _index_name(name):
    """生成带前缀的索引名。"""
    prefix = getattr(settings, 'ELASTICSEARCH_INDEX_PREFIX', 'campus')
    return f"{prefix}_{name}"


# 统一索引设置，包含 ik 中文分词器
IK_INDEX_SETTINGS = {
    'number_of_shards': 1,
    'number_of_replicas': 0,
    'analysis': {
        'analyzer': {
            'ik_smart': {
                'type': 'custom',
                'tokenizer': 'ik_smart',
            },
            'ik_max_word': {
                'type': 'custom',
                'tokenizer': 'ik_max_word',
            },
        },
    },
}


def setup_elasticsearch_connections():
    """初始化 ES 连接（在 settings 配置后调用）。"""
    connections.create_connection(
        alias='default',
        hosts=settings.ELASTICSEARCH_HOSTS,
        timeout=settings.ELASTICSEARCH_TIMEOUT,
        retry_on_timeout=settings.ELASTICSEARCH_RETRY_ON_TIMEOUT,
    )


class SchoolDocument(Document):
    """学校搜索文档。"""

    name = Text(analyzer='ik_max_word', search_analyzer='ik_smart')
    english_name = Text()
    abbreviation = Text()
    code = Keyword()
    province = Keyword()
    city = Keyword()
    school_type = Keyword()
    school_level = Keyword()
    description = Text(analyzer='ik_max_word', search_analyzer='ik_smart')
    national_rank = Integer()
    student_count = Integer()
    founded_year = Integer()
    is_active = Boolean()
    created_at = Date()
    updated_at = Date()

    class Index:
        name = _index_name('schools')
        settings = IK_INDEX_SETTINGS


class TopicDocument(Document):
    """论坛主题搜索文档。"""

    title = Text(analyzer='ik_max_word', search_analyzer='ik_smart')
    content = Text(analyzer='ik_max_word', search_analyzer='ik_smart')
    author_username = Keyword()
    author_id = Integer()
    board_id = Integer()
    board_name = Text(analyzer='ik_smart')
    tags = Keyword(multi=True)
    status = Keyword()
    views = Integer()
    post_count = Integer()
    created_at = Date()
    updated_at = Date()

    class Index:
        name = _index_name('topics')
        settings = IK_INDEX_SETTINGS


class PostDocument(Document):
    """论坛帖子/回复搜索文档。"""

    content = Text(analyzer='ik_max_word', search_analyzer='ik_smart')
    topic_id = Integer()
    topic_title = Text(analyzer='ik_max_word', search_analyzer='ik_smart')
    author_username = Keyword()
    author_id = Integer()
    content_status = Keyword()
    is_first_post = Boolean()
    created_at = Date()
    updated_at = Date()

    class Index:
        name = _index_name('posts')
        settings = IK_INDEX_SETTINGS


class ContentDocument(Document):
    """内容文章搜索文档。"""

    title = Text(analyzer='ik_max_word', search_analyzer='ik_smart')
    summary = Text(analyzer='ik_max_word', search_analyzer='ik_smart')
    content = Text(analyzer='ik_max_word', search_analyzer='ik_smart')
    author_username = Keyword()
    author_id = Integer()
    category_name = Text(analyzer='ik_smart')
    tags = Keyword(multi=True)
    status = Keyword()
    slug = Keyword()
    view_count = Integer()
    created_at = Date()
    updated_at = Date()

    class Index:
        name = _index_name('contents')
        settings = IK_INDEX_SETTINGS


class CourseDocument(Document):
    """课程搜索文档。"""

    title = Text(analyzer='ik_max_word', search_analyzer='ik_smart')
    description = Text(analyzer='ik_max_word', search_analyzer='ik_smart')
    instructor_username = Keyword()
    instructor_id = Integer()
    categories = Keyword(multi=True)
    is_published = Boolean()
    is_free = Boolean()
    price = Float()
    slug = Keyword()
    enroll_count = Integer()
    average_rating = Float()
    created_at = Date()
    updated_at = Date()

    class Index:
        name = _index_name('courses')
        settings = IK_INDEX_SETTINGS


class UserDocument(Document):
    """用户搜索文档。"""

    username = Text(analyzer='ik_smart', fields={'keyword': Keyword()})
    email = Keyword()
    phone = Keyword()
    school = Text(analyzer='ik_smart')
    major = Text(analyzer='ik_smart')
    bio = Text(analyzer='ik_max_word', search_analyzer='ik_smart')
    is_verified = Boolean()
    is_staff = Boolean()
    created_at = Date()

    class Index:
        name = _index_name('users')
        settings = IK_INDEX_SETTINGS


DOCUMENT_REGISTRY = {
    'schools': SchoolDocument,
    'topics': TopicDocument,
    'posts': PostDocument,
    'contents': ContentDocument,
    'courses': CourseDocument,
    'users': UserDocument,
}


def create_all_indices():
    """创建所有索引（幂等）。"""
    for doc in DOCUMENT_REGISTRY.values():
        doc.init()


def delete_all_indices():
    """删除所有索引（慎用）。"""
    for doc in DOCUMENT_REGISTRY.values():
        idx = Index(doc.Index.name)
        if idx.exists():
            idx.delete()
