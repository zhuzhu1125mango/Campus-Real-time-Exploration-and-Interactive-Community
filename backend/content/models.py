from django.db import models
from django.conf import settings
from django.utils import timezone
from django.urls import reverse


class ContentType(models.Model):
    """内容类型模型"""
    name = models.CharField(max_length=50, unique=True, verbose_name='类型名称')
    description = models.TextField(blank=True, verbose_name='类型描述')
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '内容类型'
        verbose_name_plural = '内容类型'
        ordering = ['name']

    def __str__(self):
        return self.name


class Category(models.Model):
    """分类模型"""
    name = models.CharField(max_length=100, unique=True, verbose_name='分类名称')
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children', verbose_name='父分类')
    description = models.TextField(blank=True, verbose_name='分类描述')
    order = models.IntegerField(default=0, verbose_name='排序')
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '分类'
        verbose_name_plural = '分类'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Tag(models.Model):
    """标签模型"""
    name = models.CharField(max_length=50, unique=True, verbose_name='标签名称')
    description = models.TextField(blank=True, verbose_name='标签描述')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '标签'
        verbose_name_plural = '标签'
        ordering = ['name']

    def __str__(self):
        return self.name


class Content(models.Model):
    """内容模型"""
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('pending', '待审核'),
        ('published', '已发布'),
        ('rejected', '已拒绝'),
    ]

    title = models.CharField(max_length=200, verbose_name='标题')
    slug = models.SlugField(max_length=200, unique=True, verbose_name='别名')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, verbose_name='内容类型')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='分类')
    tags = models.ManyToManyField(Tag, blank=True, verbose_name='标签')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='作者')
    content = models.TextField(verbose_name='内容')
    summary = models.TextField(blank=True, verbose_name='摘要')
    featured_image = models.ImageField(upload_to='content/images/', blank=True, null=True, verbose_name='特色图片')
    is_published = models.BooleanField(default=False, verbose_name='是否发布')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='状态')
    publish_date = models.DateTimeField(null=True, blank=True, verbose_name='发布时间')
    view_count = models.IntegerField(default=0, verbose_name='浏览次数')
    comment_count = models.IntegerField(default=0, verbose_name='评论次数')
    like_count = models.IntegerField(default=0, verbose_name='点赞次数')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '内容'
        verbose_name_plural = '内容'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at'], name='content_status_created_idx'),
            models.Index(fields=['author', 'status'], name='content_author_status_idx'),
            models.Index(fields=['content_type', 'status'], name='content_type_status_idx'),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('content-detail', args=[self.slug])

    def save(self, *args, **kwargs):
        # 保持 is_published 与 status 同步，便于旧代码兼容
        if self.status == 'published':
            self.is_published = True
        elif self.status in ('draft', 'rejected'):
            self.is_published = False

        if self.is_published and not self.publish_date:
            self.publish_date = timezone.now()
        super().save(*args, **kwargs)


class Comment(models.Model):
    """评论模型"""
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='comments', verbose_name='内容')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='用户')
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies', verbose_name='父评论')
    content_text = models.TextField(verbose_name='评论内容')
    is_approved = models.BooleanField(default=True, verbose_name='是否批准')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '评论'
        verbose_name_plural = '评论'
        ordering = ['-created_at']

    def __str__(self):
        return f'评论 by {self.user.username} on {self.content.title}'


class ContentRevision(models.Model):
    """内容修订历史模型"""
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='revisions', verbose_name='内容')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='作者')
    title = models.CharField(max_length=200, verbose_name='标题')
    content_text = models.TextField(verbose_name='内容')
    summary = models.TextField(blank=True, verbose_name='摘要')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '内容修订'
        verbose_name_plural = '内容修订'
        ordering = ['-created_at']

    def __str__(self):
        return f'Revision for {self.content.title} at {self.created_at}'