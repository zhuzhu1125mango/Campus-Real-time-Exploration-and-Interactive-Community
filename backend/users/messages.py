from django.db import models
from django.db.models import functions, Count
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

User = get_user_model()


class Message(models.Model):
    """
    私信模型
    用于存储用户之间的私信消息
    """
    # 消息发送者
    sender = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='sent_messages', 
        verbose_name=_('发送者')
    )
    
    # 消息接收者
    receiver = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='received_messages', 
        verbose_name=_('接收者')
    )
    
    # 消息内容
    content = models.TextField(_('内容'))
    
    # 消息状态
    is_read = models.BooleanField(_('是否已读'), default=False)
    
    # 时间戳
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('私信')
        verbose_name_plural = _('私信')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sender', 'receiver', 'created_at']),
            models.Index(fields=['receiver', 'is_read', 'sender']),
        ]
    
    def __str__(self):
        return f"{self.sender.username} -> {self.receiver.username}: {self.content[:20]}..."
    
    def mark_as_read(self):
        """
        将消息标记为已读
        """
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read', 'updated_at'])
            return True
        return False
    
    @classmethod
    def mark_all_as_read(cls, receiver, sender):
        """
        将来自特定发送者的所有消息标记为已读
        """
        cls.objects.filter(
            receiver=receiver,
            sender=sender,
            is_read=False
        ).update(
            is_read=True,
            updated_at=functions.Now()
        )
    
    @classmethod
    def get_conversation(cls, user1, user2):
        """
        获取两个用户之间的对话
        """
        return cls.objects.filter(
            models.Q(sender=user1, receiver=user2) |
            models.Q(sender=user2, receiver=user1)
        ).order_by('created_at')
    
    @classmethod
    def get_unread_count(cls, user):
        """
        获取用户的未读消息数量
        """
        return cls.objects.filter(receiver=user, is_read=False).count()
    
    @classmethod
    def get_unread_count_from(cls, user, sender):
        """
        获取来自特定发送者的未读消息数量
        """
        return cls.objects.filter(
            receiver=user,
            sender=sender,
            is_read=False
        ).count()
    
    @classmethod
    def get_conversations(cls, user):
        """
        获取用户的所有对话
        返回一个列表，每个元素包含对话对象和最后一条消息
        """
        # 获取每个对话伙伴的最新一条消息，使用 select_related 避免 N+1
        latest_messages = cls.objects.select_related('sender', 'receiver').filter(
            models.Q(sender=user) | models.Q(receiver=user)
        ).order_by('-created_at')

        # 一次性获取所有发送者的未读消息数量，避免循环中的 N+1 查询
        unread_counts = {
            item['sender']: item['count']
            for item in cls.objects.filter(receiver=user, is_read=False)
            .values('sender')
            .annotate(count=Count('id'))
        }

        # 收集每个对话伙伴的最新消息
        seen_partners = set()
        conversations = []
        for message in latest_messages:
            partner = message.receiver if message.sender == user else message.sender
            partner_id = partner.id
            if partner_id in seen_partners:
                continue
            seen_partners.add(partner_id)

            conversations.append({
                'user': partner,
                'last_message': message,
                'unread_count': unread_counts.get(partner_id, 0)
            })

        # 按最后一条消息的时间排序
        conversations.sort(key=lambda x: x['last_message'].created_at, reverse=True)

        return conversations