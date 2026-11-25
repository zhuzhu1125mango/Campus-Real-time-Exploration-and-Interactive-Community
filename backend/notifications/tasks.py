"""通知相关的 Celery 任务。"""

import logging

from celery import shared_task

from users.wechat import (
    build_notification_data,
    get_template_id,
    send_subscribe_message,
    template_key_for,
)

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2, default_retry_delay=10)
def send_wechat_subscribe_async(self, notification_id):
    """向已授权订阅消息的用户发送微信订阅消息。

    订阅消息为一次性授权：发送成功后从用户授权列表中移除对应模板。
    """
    from .models import Notification

    try:
        notification = Notification.objects.select_related('recipient').get(id=notification_id)
    except Notification.DoesNotExist:
        return

    user = notification.recipient
    openid = getattr(user, 'wechat_openid', None)
    template_key = template_key_for(notification.notification_type)
    subscriptions = list(user.wechat_subscriptions or [])

    if not openid or not template_key or template_key not in subscriptions:
        return

    template_id = get_template_id(template_key)
    if not template_id:
        return

    sent = send_subscribe_message(
        openid,
        template_id,
        build_notification_data(notification),
    )
    if not sent:
        return

    subscriptions.remove(template_key)
    user.wechat_subscriptions = subscriptions
    user.save(update_fields=['wechat_subscriptions'])
    logger.info(
        '微信订阅消息已发送: user_id=%s, template=%s, notification_id=%s',
        user.id, template_key, notification_id,
    )
