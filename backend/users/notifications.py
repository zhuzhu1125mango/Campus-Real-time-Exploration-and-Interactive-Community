from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

User = get_user_model()


class Notification(models.Model):
    """
    通知模型
    用于存储用户的各种通知消息
    """
    NOTIFICATION_TYPES = (
        ('system', '系统通知'),
        ('interaction', '互动通知'),  # 如点赞、评论、关注等
        ('message', '私信'),
        ('activity', '活动通知'),
    )
    
    # 通知接收者
    recipient = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='notifications', 
        verbose_name=_('接收者')
    )
    
    # 通知发送者（可为空，如系统通知）
    sender = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='sent_notifications', 
        verbose_name=_('发送者')
    )
    
    # 通知类型
    notification_type = models.CharField(
        _('通知类型'), 
        max_length=20, 
        choices=NOTIFICATION_TYPES
    )
    
    # 通知标题
    title = models.CharField(_('标题'), max_length=100)
    
    # 通知内容
    content = models.TextField(_('内容'))
    
    # 相关对象（可选）- 使用ContentType实现通用关系
    content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        verbose_name=_('内容类型')
    )
    object_id = models.PositiveIntegerField(null=True, blank=True, verbose_name=_('对象ID'))
    related_object = GenericForeignKey('content_type', 'object_id')
    
    # 链接（可选）- 点击通知跳转的URL
    url = models.CharField(_('链接'), max_length=255, blank=True)
    
    # 通知状态
    is_read = models.BooleanField(_('是否已读'), default=False)
    
    # 时间戳
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('通知')
        verbose_name_plural = _('通知')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.recipient.username}的通知: {self.title}"
    
    def mark_as_read(self):
        """
        将通知标记为已读
        """
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read', 'updated_at'])
    
    @classmethod
    def mark_all_as_read(cls, user):
        """
        将用户的所有通知标记为已读
        """
        cls.objects.filter(recipient=user, is_read=False).update(
            is_read=True,
            updated_at=models.functions.Now()
        )
    
    @classmethod
    def get_unread_count(cls, user):
        """
        获取用户未读通知数量
        """
        return cls.objects.filter(recipient=user, is_read=False).count()