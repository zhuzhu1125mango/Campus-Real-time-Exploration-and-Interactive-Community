from django.db import models
from django.db.models import functions
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
        # 获取所有与该用户有过消息往来的用户
        sent_to = cls.objects.filter(sender=user).values_list('receiver', flat=True)
        received_from = cls.objects.filter(receiver=user).values_list('sender', flat=True)
        conversation_users = set(sent_to).union(set(received_from))
        
        conversations = []
        for conversation_user in conversation_users:
            # 获取最后一条消息
            last_message = cls.objects.filter(
                models.Q(sender=user, receiver=conversation_user) |
                models.Q(sender=conversation_user, receiver=user)
            ).order_by('-created_at').first()
            
            if last_message:
                # 获取未读消息数量
                unread_count = cls.get_unread_count_from(user, conversation_user)
                
                # 获取对话用户信息
                conversation_user_obj = User.objects.get(id=conversation_user)
                
                conversations.append({
                    'user': conversation_user_obj,
                    'last_message': last_message,
                    'unread_count': unread_count
                })
        
        # 按最后一条消息的时间排序
        conversations.sort(key=lambda x: x['last_message'].created_at, reverse=True)
        
        return conversations