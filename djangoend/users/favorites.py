from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

User = get_user_model()


class Favorite(models.Model):
    """
    收藏夹模型
    用于存储用户收藏的各种内容（院校、专业、帖子等）
    使用Django的ContentType框架实现通用关系
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites', verbose_name=_('用户'))
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, verbose_name=_('内容类型'))
    object_id = models.PositiveIntegerField(verbose_name=_('对象ID'))
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # 收藏夹分类（可选）
    category = models.CharField(_('分类'), max_length=50, blank=True)
    
    # 备注（可选）
    note = models.TextField(_('备注'), blank=True)
    
    # 创建时间
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('收藏')
        verbose_name_plural = _('收藏')
        # 确保用户不会重复收藏同一个对象
        unique_together = ('user', 'content_type', 'object_id')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username}收藏的{self.content_type}"
    
    @property
    def content_type_name(self):
        """
        返回内容类型的可读名称
        """
        return self.content_type.name
    
    @property
    def content_object_name(self):
        """
        返回被收藏对象的名称
        """
        if hasattr(self.content_object, 'name'):
            return self.content_object.name
        elif hasattr(self.content_object, 'title'):
            return self.content_object.title
        else:
            return str(self.content_object)