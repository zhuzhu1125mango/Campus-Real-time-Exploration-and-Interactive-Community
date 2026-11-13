import re

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.auth import get_user_model

from notifications.notification_sender import notify_forum_event
from users.tasks import queue_update_user_points
from .models import Post, Topic

User = get_user_model()


@receiver(post_save, sender=Post)
def handle_post_created(sender, instance, created, **kwargs):
    """帖子创建后的通知与积分处理。"""
    if not created:
        return

    # 异步发放积分：首贴=发帖，非首贴=回复
    action = 'post' if instance.is_first_post else 'reply'
    queue_update_user_points(instance.author.id, action)

    # 仅非首贴需要发送回复/提及通知
    if instance.is_first_post:
        return

    topic_author = instance.topic.author

    # 回复主题通知
    if topic_author != instance.author:
        notify_forum_event(
            recipient=topic_author,
            sender=instance.author,
            forum_type='topic_reply',
            message=f"{instance.author.username} 回复了你的主题 '{instance.topic.title}'",
            topic=instance.topic,
            post=instance,
        )

    # 处理@提及的用户通知
    mention_usernames = set(re.findall(r'@([\w.-]+)', instance.content or ''))
    if mention_usernames:
        mentioned_users = User.objects.filter(username__in=mention_usernames)
        for user in mentioned_users:
            # 不给自己发提及通知；主题作者已收到回复通知，也跳过避免重复
            if user == instance.author or user == topic_author:
                continue
            notify_forum_event(
                recipient=user,
                sender=instance.author,
                forum_type='mention',
                message=f"{instance.author.username} 在主题 '{instance.topic.title}' 中提到了你",
                topic=instance.topic,
                post=instance,
            )


@receiver(post_delete, sender=Post)
def update_topic_on_post_delete(sender, instance, **kwargs):
    """删除帖子时更新主题信息"""
    # 如果不是首贴，并且主题仍然存在，更新主题的更新时间
    if not instance.is_first_post and hasattr(instance, 'topic') and instance.topic:
        try:
            topic = instance.topic
            topic.updated_at = timezone.now()
            topic.save(update_fields=['updated_at'])
        except Topic.DoesNotExist:
            pass
