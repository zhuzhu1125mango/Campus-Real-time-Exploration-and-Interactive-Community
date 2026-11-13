"""
Django 信号与 Elasticsearch 索引同步。

模型保存/删除时异步触发索引更新任务。
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from forum.models import Topic, Post
from schools.models import School
from content.models import Content
from learning.models import Course
from users.models import User

from .tasks import index_object, remove_object_from_index


# 需要同步到 ES 的模型与对应的 app_label.ModelName
_INDEXED_MODELS = {
    School: 'schools.School',
    Topic: 'forum.Topic',
    Post: 'forum.Post',
    Content: 'content.Content',
    Course: 'learning.Course',
    User: 'users.User',
}


def _queue_index(instance):
    app_label_model = _INDEXED_MODELS.get(type(instance))
    if app_label_model:
        index_object.delay(app_label_model, instance.pk)


def _queue_remove(instance):
    app_label_model = _INDEXED_MODELS.get(type(instance))
    if app_label_model:
        remove_object_from_index.delay(app_label_model, instance.pk)


@receiver(post_save, sender=School)
def index_school(sender, instance, **kwargs):
    _queue_index(instance)


@receiver(post_delete, sender=School)
def remove_school(sender, instance, **kwargs):
    _queue_remove(instance)


@receiver(post_save, sender=Topic)
def index_topic(sender, instance, **kwargs):
    _queue_index(instance)


@receiver(post_delete, sender=Topic)
def remove_topic(sender, instance, **kwargs):
    _queue_remove(instance)


@receiver(post_save, sender=Post)
def index_post(sender, instance, **kwargs):
    _queue_index(instance)
    # 回复更新后，主题内容（首贴）可能未变，但帖子数/更新时间变化，需要重索引主题
    if not instance.is_first_post and instance.topic:
        _queue_index(instance.topic)


@receiver(post_delete, sender=Post)
def remove_post(sender, instance, **kwargs):
    _queue_remove(instance)
    if instance.topic:
        _queue_index(instance.topic)


@receiver(post_save, sender=Content)
def index_content(sender, instance, **kwargs):
    _queue_index(instance)


@receiver(post_delete, sender=Content)
def remove_content(sender, instance, **kwargs):
    _queue_remove(instance)


@receiver(post_save, sender=Course)
def index_course(sender, instance, **kwargs):
    _queue_index(instance)


@receiver(post_delete, sender=Course)
def remove_course(sender, instance, **kwargs):
    _queue_remove(instance)


@receiver(post_save, sender=User)
def index_user(sender, instance, **kwargs):
    _queue_index(instance)


@receiver(post_delete, sender=User)
def remove_user(sender, instance, **kwargs):
    _queue_remove(instance)
