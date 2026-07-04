from django.db import models
from django.contrib.auth import get_user_model
import json

User = get_user_model()

class ChatMessage(models.Model):
    """聊天消息模型"""
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='chat_messages', 
        verbose_name='用户',
        null=True,  # 允许为空
        blank=True  # 允许为空白
    )
    content = models.TextField(verbose_name='消息内容')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='发送时间')
    
    class Meta:
        verbose_name = '聊天消息'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
    
    def __str__(self):
        username = self.user.username if self.user else "游客"
        if not self.content:
            return f"{username}: <空消息>"
        return f"{username}: {self.content[:50]}"
    
    def clean(self):
        """验证模型字段"""
        if not self.content or self.content.strip() == '':
            raise ValueError("消息内容不能为空")
    
    def to_dict(self):
        """将消息转换为字典格式"""
        try:
            if self.user:
                username = self.user.username if hasattr(self.user, 'username') else "未知用户"
                user_id = self.user.id
                avatar = None
                if hasattr(self.user, 'avatar') and self.user.avatar:
                    try:
                        avatar = self.user.avatar.url
                    except Exception:
                        avatar = None
            else:
                username = "游客"
                user_id = 0
                avatar = None
                
            return {
                'id': self.id,
                'content': self.content,
                'time': self.created_at.isoformat(),
                'user': {
                    'id': user_id,
                    'username': username,
                    'avatar': avatar
                }
            }
        except Exception as e:
            print(f"消息序列化失败: {str(e)}")
            # 返回简化版本的字典，避免完全失败
            return {
                'id': self.id,
                'content': self.content,
                'time': self.created_at.isoformat(),
                'user': {
                    'id': 0,
                    'username': "用户名获取失败",
                    'avatar': None
                }
            }
