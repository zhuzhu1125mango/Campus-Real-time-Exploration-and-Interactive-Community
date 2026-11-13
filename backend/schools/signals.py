from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from core.cache_utils import invalidate_namespace
from schools.services.board_service import get_or_create_school_board

from .models import (
    School, Major, SchoolMajor,
    AdmissionScore, SchoolRating, MajorRating,
    Event, EventRegistration,
)


@receiver(post_save, sender=School)
def create_school_board(sender, instance, created, **kwargs):
    """创建学校时自动创建对应的论坛板块"""
    if not created:
        return

    get_or_create_school_board(instance)


def _invalidate_school_caches():
    """学校相关数据变更时，使相关缓存命名空间失效。"""
    invalidate_namespace('schools')
    invalidate_namespace('stats')
    invalidate_namespace('recommendation')


@receiver(post_save, sender=School)
@receiver(post_delete, sender=School)
def on_school_changed(sender, instance, **kwargs):
    """学校数据变更时失效相关缓存。"""
    _invalidate_school_caches()


@receiver(post_save, sender=Major)
@receiver(post_delete, sender=Major)
def on_major_changed(sender, instance, **kwargs):
    """专业数据变更时失效统计与推荐缓存。"""
    invalidate_namespace('stats')
    invalidate_namespace('recommendation')


@receiver(post_save, sender=SchoolMajor)
@receiver(post_delete, sender=SchoolMajor)
def on_school_major_changed(sender, instance, **kwargs):
    """学校-专业关联变更时失效学校与统计缓存。"""
    _invalidate_school_caches()


@receiver(post_save, sender=AdmissionScore)
@receiver(post_delete, sender=AdmissionScore)
def on_admission_score_changed(sender, instance, **kwargs):
    """录取分数变更时失效学校与统计缓存。"""
    _invalidate_school_caches()


@receiver(post_save, sender=SchoolRating)
@receiver(post_delete, sender=SchoolRating)
def on_school_rating_changed(sender, instance, **kwargs):
    """学校评分变更时失效学校与统计缓存。"""
    _invalidate_school_caches()


@receiver(post_save, sender=MajorRating)
@receiver(post_delete, sender=MajorRating)
def on_major_rating_changed(sender, instance, **kwargs):
    """专业评分变更时失效统计与推荐缓存。"""
    invalidate_namespace('stats')
    invalidate_namespace('recommendation')


@receiver(post_save, sender=Event)
@receiver(post_delete, sender=Event)
@receiver(post_save, sender=EventRegistration)
@receiver(post_delete, sender=EventRegistration)
def on_event_changed(sender, instance, **kwargs):
    """活动数据变更时失效统计缓存。"""
    invalidate_namespace('stats')
