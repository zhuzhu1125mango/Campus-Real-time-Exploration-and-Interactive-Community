"""统一通知发送入口。

所有通知创建与实时推送都应通过此处封装的方法完成，
推送本身由 Celery 异步任务执行，避免阻塞主业务线程。
"""

from django.contrib.contenttypes.models import ContentType

from .models import Notification


def create_notification(
    recipient,
    title,
    content,
    notification_type='system',
    sender=None,
    related_object=None,
    url=''
):
    """
    创建通知记录。

    创建后会由 notifications/signals.py 自动触发异步 WebSocket 推送，
    调用方无需关心发送细节。
    """
    kwargs = {
        'recipient': recipient,
        'title': title,
        'content': content,
        'notification_type': notification_type,
        'sender': sender,
        'url': url,
    }

    if related_object is not None:
        kwargs['content_type'] = ContentType.objects.get_for_model(related_object)
        kwargs['object_id'] = related_object.pk

    return Notification.objects.create(**kwargs)


def send_notification_to_user(
    user,
    title,
    content,
    notification_type='system',
    sender=None,
    related_object=None,
    url=''
):
    """
    创建并发送通知给用户。

    返回值: 创建的 Notification 实例
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()

    if not isinstance(user, User):
        return None

    return create_notification(
        recipient=user,
        title=title,
        content=content,
        notification_type=notification_type,
        sender=sender,
        related_object=related_object,
        url=url,
    )


def notify_users(
    recipients,
    title,
    content,
    notification_type='system',
    sender=None,
    related_object=None,
    url=''
):
    """
    批量创建通知（例如通知多个版主）。

    返回值: 创建的 Notification 实例列表
    """
    notifications = []
    for recipient in recipients:
        notification = create_notification(
            recipient=recipient,
            title=title,
            content=content,
            notification_type=notification_type,
            sender=sender,
            related_object=related_object,
            url=url,
        )
        notifications.append(notification)
    return notifications


# forum.Notification 类型到 notifications.Notification 类型的映射。
# 注意：content_comment 自本版本起使用独立通知类型；历史已创建的 interaction 类型记录
# 无法与安全区分，因此保持不变，仅后续新增的通知按新规则写入。
_FORUM_TYPE_MAP = {
    'topic_reply': 'interaction',
    'mention': 'interaction',
    'like': 'interaction',
    'content_comment': 'content_comment',
    'topic_moved': 'system',
    'topic_closed': 'system',
    'topic_pinned': 'system',
    'system': 'system',
}

_FORUM_TYPE_TITLES = {
    'topic_reply': '新回复',
    'mention': '有人提及你',
    'like': '新点赞',
    'content_comment': '新评论',
    'topic_moved': '主题被移动',
    'topic_closed': '主题被关闭',
    'topic_pinned': '主题被置顶',
    'system': '系统通知',
}


def notify_forum_event(
    recipient,
    sender,
    forum_type,
    message,
    topic=None,
    post=None,
):
    """
    将原 forum.Notification 事件迁移到通用 notifications.Notification。

    用于逐步替换 forum 应用内的通知模型，保持最小侵入。
    """
    notification_type = _FORUM_TYPE_MAP.get(forum_type, 'system')
    title = _FORUM_TYPE_TITLES.get(forum_type, '系统通知')
    related_object = post if post is not None else topic

    return create_notification(
        recipient=recipient,
        sender=sender,
        title=title,
        content=message,
        notification_type=notification_type,
        related_object=related_object,
    )
