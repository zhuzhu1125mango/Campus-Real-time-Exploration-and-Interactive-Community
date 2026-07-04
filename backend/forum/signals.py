from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone

from .models import Post, Topic, Notification


@receiver(post_save, sender=Post)
def create_notification_for_post(sender, instance, created, **kwargs):
    """创建帖子回复通知"""
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
        
        # TODO: 处理@提及的用户通知


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