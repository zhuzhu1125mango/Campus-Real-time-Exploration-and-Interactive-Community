from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from users.tasks import send_notification_async
from .models import Notification
from .tasks import send_wechat_subscribe_async


@receiver(post_save, sender=Notification)
def trigger_notification_send(sender, instance, created, **kwargs):
    """Notification 记录创建后，异步触发 WebSocket 推送与微信订阅消息。

    推送任务延迟到事务提交后再派发，避免 Celery Worker 在事务尚未提交时
    读取不到通知记录。
    """
    if created:
        transaction.on_commit(
            lambda: send_notification_async.delay(instance.id)
        )
        transaction.on_commit(
            lambda: send_wechat_subscribe_async.delay(instance.id)
        )
