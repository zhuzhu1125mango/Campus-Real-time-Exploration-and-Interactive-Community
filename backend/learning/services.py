"""学习模块的报名、结业与证书服务。

集中封装跨 ViewSet 复用的流程，避免支付、报名、进度三处重复实现。
"""

import uuid

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from users.tasks import queue_update_user_points

from .models import Certificate, Course, Enrollment, Lesson, Progress


def generate_certificate_number():
    """生成证书编号，形如 CERT-20261126-1A2B3C4D。"""
    return f'CERT-{timezone.now():%Y%m%d}-{uuid.uuid4().hex[:8].upper()}'


def ensure_enrollment(user, course):
    """创建报名（幂等），并初始化课程进度。

    返回 ``(enrollment, created)``。并发场景下通过锁定课程行串行化，
    保证报名人数只增加一次。
    """
    with transaction.atomic():
        course = Course.objects.select_for_update().get(pk=course.pk)
        enrollment, created = Enrollment.objects.get_or_create(user=user, course=course)
        if not created:
            return enrollment, False

        Course.objects.filter(pk=course.pk).update(enroll_count=F('enroll_count') + 1)

        lessons = Lesson.objects.filter(chapter__course=course)
        Progress.objects.bulk_create(
            [Progress(enrollment=enrollment, lesson=lesson) for lesson in lessons],
            ignore_conflicts=True,
        )

        queue_update_user_points(
            user.id,
            'favorite',
            description=f'报名课程 {course.title}',
        )
        return enrollment, True


def issue_certificate(enrollment):
    """为已完成课程发放证书；未完成或已存在时返回 None/已有证书。"""
    if not enrollment.is_completed:
        return None
    certificate, _ = Certificate.objects.get_or_create(
        enrollment=enrollment,
        defaults={'number': generate_certificate_number()},
    )
    return certificate


def complete_enrollment(enrollment):
    """将报名标记为完成，发放积分与结业证书（幂等）。"""
    if not enrollment.is_completed:
        enrollment.is_completed = True
        enrollment.progress = 100.0
        enrollment.completed_at = timezone.now()
        enrollment.save(update_fields=['is_completed', 'progress', 'completed_at'])
        queue_update_user_points(
            enrollment.user_id,
            'complete_course',
            description=f'完成课程 {enrollment.course.title}',
        )
    return issue_certificate(enrollment)
