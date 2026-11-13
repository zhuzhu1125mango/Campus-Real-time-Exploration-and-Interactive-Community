from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from .models import UserActivity, UserProfile, PointsRecord
from .tasks import queue_update_user_points

User = get_user_model()


def _has_points_record(user, action):
    """检查用户是否已有指定类型的积分记录，用于幂等发放。"""
    return PointsRecord.objects.filter(user=user, action=action).exists()


def _is_profile_complete(user):
    """判断用户资料是否达到完善标准。"""
    if not user.school or not user.education_level:
        return False

    has_major = bool(user.major) or bool(user.target_major)
    has_bio = bool(user.bio)

    profile = getattr(user, 'profile', None)
    has_profile_extra = (
        profile is not None
        and (bool(profile.interests) or bool(profile.target_schools))
    )

    return has_major and (has_bio or has_profile_extra)


@receiver(post_save, sender=User)
def handle_user_saved(sender, instance, created, **kwargs):
    """用户创建或更新时的积分处理。"""
    if created:
        queue_update_user_points(instance.id, 'register')
        return

    # 身份认证积分（仅首次）
    if instance.is_verified and not _has_points_record(instance, 'verified'):
        queue_update_user_points(instance.id, 'verified')

    # 资料完善积分（仅首次，且需存在 profile）
    if _is_profile_complete(instance) and not _has_points_record(instance, 'complete_profile'):
        queue_update_user_points(instance.id, 'complete_profile')


@receiver(post_save, sender=UserProfile)
def handle_profile_saved(sender, instance, created, **kwargs):
    """资料更新时检查是否达到完善标准。"""
    user = instance.user
    if _is_profile_complete(user) and not _has_points_record(user, 'complete_profile'):
        queue_update_user_points(user.id, 'complete_profile')


@receiver(post_save, sender=UserActivity)
def record_activity(sender, instance, created, **kwargs):
    """记录用户行为后的 hook（预留扩展点）。"""
    pass
