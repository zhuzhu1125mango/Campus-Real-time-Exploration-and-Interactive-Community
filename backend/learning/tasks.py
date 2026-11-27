"""学习模块的 Celery 定时任务。"""

import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)

# 定时扫描窗口（分钟），与 Beat 调度间隔保持一致
REMINDER_WINDOW_MINUTES = 10


@shared_task
def send_study_reminders(now=None):
    """发送到期未完成课程的学习提醒。

    ``now`` 仅供测试注入固定时间；Beat 调用时不传参，使用当前时间。
    每个提醒每天最多发送一次。
    """
    from notifications.models import Notification

    from .models import Enrollment, StudyReminder

    local_now = timezone.localtime(now or timezone.now())
    window_start = local_now - timedelta(minutes=REMINDER_WINDOW_MINUTES)
    sent = 0

    reminders = StudyReminder.objects.filter(is_active=True).select_related('user', 'course')
    for reminder in reminders:
        target = local_now.replace(
            hour=reminder.remind_time.hour,
            minute=reminder.remind_time.minute,
            second=0,
            microsecond=0,
        )
        candidates = (target, target - timedelta(days=1))
        if not any(window_start <= candidate <= local_now for candidate in candidates):
            continue

        if (
            reminder.last_reminded_at
            and timezone.localtime(reminder.last_reminded_at).date() == local_now.date()
        ):
            continue

        enrollment = Enrollment.objects.filter(
            user_id=reminder.user_id, course_id=reminder.course_id
        ).only('id', 'progress', 'is_completed').first()
        if not enrollment or enrollment.is_completed:
            continue

        Notification.objects.create(
            recipient=reminder.user,
            notification_type='course_reminder',
            title='学习提醒',
            content=(
                f'别忘了继续学习《{reminder.course.title}》，'
                f'当前进度 {int(enrollment.progress)}%'
            ),
            url=f'/learning/course/{reminder.course_id}',
        )
        reminder.last_reminded_at = local_now
        reminder.save(update_fields=['last_reminded_at', 'updated_at'])
        sent += 1

    if sent:
        logger.info('学习提醒已发送: %s 条', sent)
    return sent
