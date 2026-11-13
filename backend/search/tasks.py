"""
搜索索引异步任务。

通过 Celery 异步更新 Elasticsearch 索引，避免写请求阻塞。
"""

import logging

from celery import shared_task
from django.apps import apps

from .client import get_es_client, es_is_available
from .documents import (
    SchoolDocument, TopicDocument, PostDocument,
    ContentDocument, CourseDocument, UserDocument,
)

logger = logging.getLogger(__name__)


def _format_dt(value):
    """将日期格式化为 ISO 字符串，兼容 None。"""
    if value is None:
        return None
    return value.isoformat()


def _school_to_doc(school):
    return SchoolDocument(
        meta={'id': school.id},
        name=school.name,
        english_name=school.english_name or '',
        abbreviation=school.abbreviation or '',
        code=school.code or '',
        province=school.province or '',
        city=school.city or '',
        school_type=school.school_type or '',
        school_level=school.school_level or '',
        description=school.description or '',
        national_rank=school.national_rank,
        student_count=school.student_count,
        founded_year=school.founded_year,
        is_active=True,
        created_at=_format_dt(school.created_at),
        updated_at=_format_dt(school.updated_at),
    )


def _topic_to_doc(topic):
    first_post = topic.posts.filter(is_first_post=True).first()
    return TopicDocument(
        meta={'id': topic.id},
        title=topic.title or '',
        content=first_post.content if first_post else '',
        author_username=topic.author.username if topic.author else '',
        author_id=topic.author_id,
        board_id=topic.board_id,
        board_name=topic.board.name if topic.board else '',
        tags=[tag.name for tag in topic.tags.all()] if hasattr(topic, 'tags') else [],
        status=topic.status or 'normal',
        views=topic.views or 0,
        post_count=topic.posts.count(),
        created_at=_format_dt(topic.created_at),
        updated_at=_format_dt(topic.updated_at),
    )


def _post_to_doc(post):
    return PostDocument(
        meta={'id': post.id},
        content=post.content or '',
        topic_id=post.topic_id,
        topic_title=post.topic.title if post.topic else '',
        author_username=post.author.username if post.author else '',
        author_id=post.author_id,
        content_status=post.content_status or 'approved',
        is_first_post=post.is_first_post,
        created_at=_format_dt(post.created_at),
        updated_at=_format_dt(post.updated_at),
    )


def _content_to_doc(content):
    return ContentDocument(
        meta={'id': content.id},
        title=content.title or '',
        summary=content.summary or '',
        content=content.content or '',
        author_username=content.author.username if content.author else '',
        author_id=content.author_id,
        category_name=content.category.name if content.category else '',
        tags=[tag.name for tag in content.tags.all()] if hasattr(content, 'tags') else [],
        status=content.status or 'draft',
        slug=content.slug or '',
        view_count=content.view_count or 0,
        created_at=_format_dt(content.created_at),
        updated_at=_format_dt(content.updated_at),
    )


def _course_to_doc(course):
    return CourseDocument(
        meta={'id': course.id},
        title=course.title or '',
        description=course.description or '',
        instructor_username=course.instructor.username if course.instructor else '',
        instructor_id=course.instructor_id,
        categories=[cat.name for cat in course.categories.all()] if hasattr(course, 'categories') else [],
        is_published=course.is_published,
        is_free=course.is_free,
        price=float(course.price) if course.price else 0.0,
        slug=course.slug or '',
        enroll_count=course.enroll_count or 0,
        average_rating=course.average_rating or 0.0,
        created_at=_format_dt(course.created_at),
        updated_at=_format_dt(course.updated_at),
    )


def _user_to_doc(user):
    return UserDocument(
        meta={'id': user.id},
        username=user.username or '',
        email=user.email or '',
        phone=user.phone or '',
        school=user.school or '',
        major=user.major or '',
        bio=user.bio or '',
        is_verified=user.is_verified,
        is_staff=user.is_staff,
        created_at=_format_dt(user.date_joined),
    )


MODEL_TO_DOC = {
    'schools.School': (_school_to_doc, SchoolDocument),
    'forum.Topic': (_topic_to_doc, TopicDocument),
    'forum.Post': (_post_to_doc, PostDocument),
    'content.Content': (_content_to_doc, ContentDocument),
    'learning.Course': (_course_to_doc, CourseDocument),
    'users.User': (_user_to_doc, UserDocument),
}


@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def index_object(self, app_label_model, object_id):
    """
    将指定对象索引到 Elasticsearch。

    参数:
        app_label_model: 'app_label.ModelName'，例如 'schools.School'
        object_id: 对象主键
    """
    if not es_is_available():
        logger.warning("Elasticsearch 不可用，跳过索引任务")
        return

    converter, doc_class = MODEL_TO_DOC.get(app_label_model, (None, None))
    if converter is None:
        logger.warning(f"未注册的模型: {app_label_model}")
        return

    try:
        app_label, model_name = app_label_model.split('.')
        Model = apps.get_model(app_label, model_name)
        instance = Model.objects.get(pk=object_id)
    except Exception as exc:
        logger.warning(f"获取对象失败: {app_label_model}#{object_id} - {exc}")
        return

    try:
        doc = converter(instance)
        doc.save(using=get_es_client())
        logger.info(f"已索引 {app_label_model}#{object_id}")
    except Exception as exc:
        logger.exception(f"索引失败: {app_label_model}#{object_id}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def remove_object_from_index(self, app_label_model, object_id):
    """从 Elasticsearch 中删除指定对象。"""
    if not es_is_available():
        logger.warning("Elasticsearch 不可用，跳过删除索引任务")
        return

    _, doc_class = MODEL_TO_DOC.get(app_label_model, (None, None))
    if doc_class is None:
        return

    try:
        doc_class.get(using=get_es_client(), id=object_id).delete()
        logger.info(f"已删除索引 {app_label_model}#{object_id}")
    except Exception as exc:
        logger.warning(f"删除索引失败（可能不存在）: {app_label_model}#{object_id} - {exc}")
