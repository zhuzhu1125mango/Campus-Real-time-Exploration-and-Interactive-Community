import re

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import Post, Topic, Notification

User = get_user_model()


@receiver(post_save, sender=Post)
def create_notification_for_post(sender, instance, created, **kwargs):
    """创建帖子回复通知与@提及通知"""
    if created and not instance.is_first_post:
        # 获取主题作者
        topic_author = instance.topic.author

        # 避免给自己发通知
        if topic_author != instance.author:
            # 创建回复通知
            Notification.objects.create(
                user=topic_author,
                sender=instance.author,
                notification_type='topic_reply',
                topic=instance.topic,
                post=instance,
                message=f"{instance.author.username} 回复了你的主题 '{instance.topic.title}'"
            )

        # 处理@提及的用户通知
        mention_usernames = set(re.findall(r'@([\w.-]+)', instance.content or ''))
        if mention_usernames:
            mentioned_users = User.objects.filter(username__in=mention_usernames)
            for user in mentioned_users:
                # 不给自己发提及通知；主题作者已收到回复通知，也跳过避免重复
                if user == instance.author or user == topic_author:
                    continue
                Notification.objects.create(
                    user=user,
                    sender=instance.author,
                    notification_type='mention',
                    topic=instance.topic,
                    post=instance,
                    message=f"{instance.author.username} 在主题 '{instance.topic.title}' 中提到了你"
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