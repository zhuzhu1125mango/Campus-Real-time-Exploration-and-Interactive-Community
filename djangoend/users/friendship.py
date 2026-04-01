from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

User = get_user_model()


class FriendRequest(models.Model):
    """
    好友请求模型
    """
    STATUS_CHOICES = (
        ('pending', '待处理'),
        ('accepted', '已接受'),
        ('rejected', '已拒绝'),
    )
    
    # 请求发送者
    sender = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='sent_friend_requests', 
        verbose_name=_('发送者')
    )
    
    # 请求接收者
    receiver = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='received_friend_requests', 
        verbose_name=_('接收者')
    )
    
    # 请求状态
    status = models.CharField(
        _('状态'), 
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='pending'
    )
    
    # 时间戳
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('好友请求')
        verbose_name_plural = _('好友请求')
        unique_together = ('sender', 'receiver')
    
    def __str__(self):
        return f"{self.sender.username} -> {self.receiver.username} ({self.status})"
    
    def accept(self):
        """
        接受好友请求
        """
        if self.status == 'pending':
            self.status = 'accepted'
            self.save()
            # 创建双向好友关系
            Friend.objects.get_or_create(user1=self.sender, user2=self.receiver)
            Friend.objects.get_or_create(user1=self.receiver, user2=self.sender)
            return True
        return False
    
    def reject(self):
        """
        拒绝好友请求
        """
        if self.status == 'pending':
            self.status = 'rejected'
            self.save()
            return True
        return False


class Friend(models.Model):
    """
    好友关系模型
    存储用户之间的好友关系
    """
    # 用户1
    user1 = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='friendships_as_user1', 
        verbose_name=_('用户1')
    )
    
    # 用户2
    user2 = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='friendships_as_user2', 
        verbose_name=_('用户2')
    )
    
    # 成为好友的时间
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('好友关系')
        verbose_name_plural = _('好友关系')
        unique_together = ('user1', 'user2')
    
    def __str__(self):
        return f"{self.user1.username} & {self.user2.username}"
    
    @classmethod
    def get_friends(cls, user):
        """
        获取用户的所有好友
        """
        friendships = cls.objects.filter(
            models.Q(user1=user) | models.Q(user2=user)
        )
        friends = []
        for friendship in friendships:
            if friendship.user1 == user:
                friends.append(friendship.user2)
            else:
                friends.append(friendship.user1)
        return friends
    
    @classmethod
    def is_friend(cls, user1, user2):
        """
        检查两个用户是否是好友
        """
        return cls.objects.filter(
            (models.Q(user1=user1) & models.Q(user2=user2)) |
            (models.Q(user1=user2) & models.Q(user2=user1))
        ).exists()
    
    @classmethod
    def remove_friend(cls, user1, user2):
        """
        解除好友关系
        """
        # 删除两个方向的好友关系
        cls.objects.filter(
            (models.Q(user1=user1) & models.Q(user2=user2)) |
            (models.Q(user1=user2) & models.Q(user2=user1))
        ).delete()
        return True