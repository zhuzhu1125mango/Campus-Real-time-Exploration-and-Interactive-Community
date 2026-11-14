"""users app 的 Celery 异步任务。"""

import logging

from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
from django.conf import settings
from django.db import transaction

from .points import get_points_for_action, get_action_description, calculate_level

logger = logging.getLogger(__name__)


def queue_update_user_points(user_id, action, description=None, extra_points=None):
    """在事务提交后再派发积分任务；不在事务中时立即派发。

    所有业务代码应通过本函数派发积分任务，避免 Celery Worker 在事务回滚前
    读取不到数据或读到旧数据。
    """
    kwargs = {
        'description': description,
        'extra_points': extra_points,
    }

    def _dispatch():
        update_user_points_async.delay(user_id, action, **kwargs)

    connection = transaction.get_connection()
    if getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False) or not connection.in_atomic_block:
        _dispatch()
    else:
        transaction.on_commit(_dispatch)


async def _group_send(channel_layer, group, message):
    """异步发送群组消息，供 Celery 同步任务通过 async_to_sync 调用。"""
    await channel_layer.group_send(group, message)


@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def send_notification_async(self, notification_id):
    """
    异步通过 WebSocket 发送实时通知。

    参数:
        notification_id: Notification 记录的主键
    """
    from notifications.models import Notification

    try:
        notification = Notification.objects.select_related('recipient', 'sender').get(id=notification_id)
    except Notification.DoesNotExist:
        logger.warning(f"通知 {notification_id} 不存在，跳过发送")
        return

    try:
        channel_layer = get_channel_layer()
        notification_data = {
            'id': notification.id,
            'title': notification.title,
            'content': notification.content,
            'notification_type': notification.notification_type,
            'created_at': notification.created_at.isoformat(),
            'is_read': notification.is_read,
            'url': notification.url,
        }

        if notification.sender:
            notification_data['sender'] = {
                'id': notification.sender.id,
                'username': notification.sender.username,
            }

        user_group_name = f"user_{notification.recipient.id}"
        async_to_sync(_group_send)(
            channel_layer,
            user_group_name,
            {
                'type': 'notification',
                'notification': notification_data,
            }
        )

        unread_count = Notification.get_unread_count(notification.recipient)
        async_to_sync(_group_send)(
            channel_layer,
            user_group_name,
            {
                'type': 'unread_notifications_update',
                'count': unread_count,
            }
        )

        logger.info(f"异步通知已发送: notification_id={notification_id}")
    except Exception as exc:
        logger.exception(f"异步发送通知失败: notification_id={notification_id}")
        raise self.retry(exc=exc)


def apply_points(user_id, action, description=None, extra_points=None):
    """同步发放积分并更新等级。

    调用方应处于事务中（每日签到会先锁定用户行）。返回 None 表示
    用户不存在或该行为积分为 0。
    """
    from django.contrib.auth import get_user_model
    from .models import PointsRecord

    User = get_user_model()

    points = extra_points if extra_points is not None else get_points_for_action(action)
    if points == 0:
        return None

    if description is None:
        description = get_action_description(action)

    with transaction.atomic():
        try:
            user = User.objects.select_for_update().get(pk=user_id)
        except User.DoesNotExist:
            return None

        PointsRecord.objects.create(
            user=user,
            action=action,
            points=points,
            description=description,
        )

        new_points = user.points + points
        new_level = calculate_level(new_points)
        update_fields = {'points': new_points}
        if new_level != user.level:
            update_fields['level'] = new_level

        User.objects.filter(pk=user_id).update(**update_fields)

    return {
        'points': points,
        'total_points': new_points,
        'level': new_level,
    }


@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def update_user_points_async(self, user_id, action, description=None, extra_points=None):
    """
    异步更新用户积分、等级并创建积分记录。

    参数:
        user_id: 用户主键
        action: 积分行为类型，对应 users/points.py 中的 POINTS_RULES
        description: 可选自定义描述，默认使用 ACTION_DESCRIPTIONS
        extra_points: 可选强制指定积分值，不传则按规则计算
    """
    try:
        result = apply_points(user_id, action, description, extra_points)
    except Exception as exc:
        logger.exception(f"异步更新用户积分失败: user_id={user_id}, action={action}")
        raise self.retry(exc=exc)

    if result is None:
        logger.info(f"积分更新跳过（用户不存在或积分为 0）: user_id={user_id}, action={action}")
        return

    logger.info(
        f"异步更新用户积分成功: user_id={user_id}, action={action}, "
        f"points={result['points']}, total_points={result['total_points']}, "
        f"level={result['level']}"
    )
