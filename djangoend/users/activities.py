from django.db import models
from django.conf import settings
from django.utils import timezone


class Activity(models.Model):
    """用户动态模型"""
    ACTIVITY_TYPES = [
        ('post', '发布帖子'),
        ('comment', '发表评论'),
        ('like', '点赞'),
        ('follow', '关注用户'),
        ('enroll', '报名课程'),
        ('share', '分享内容'),
        ('custom', '自定义动态'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='social_activities', verbose_name='用户')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES, verbose_name='动态类型')
    content = models.TextField(blank=True, verbose_name='动态内容')
    target_content_type = models.CharField(max_length=100, blank=True, verbose_name='目标内容类型')
    target_object_id = models.PositiveIntegerField(blank=True, null=True, verbose_name='目标对象ID')
    target_title = models.CharField(max_length=200, blank=True, verbose_name='目标标题')
    target_url = models.URLField(blank=True, verbose_name='目标链接')
    is_public = models.BooleanField(default=True, verbose_name='是否公开')
    likes_count = models.IntegerField(default=0, verbose_name='点赞数')
    comments_count = models.IntegerField(default=0, verbose_name='评论数')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '用户动态'
        verbose_name_plural = '用户动态'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} - {self.get_activity_type_display()} - {self.created_at}'


class ActivityLike(models.Model):
    """动态点赞模型"""
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='likes', verbose_name='动态')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='activity_likes', verbose_name='用户')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '动态点赞'
        verbose_name_plural = '动态点赞'
        unique_together = ('activity', 'user')

    def __str__(self):
        return f'{self.user.username} 点赞了 {self.activity.id} 号动态'


class ActivityComment(models.Model):
    """动态评论模型"""
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='comments', verbose_name='动态')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='activity_comments', verbose_name='用户')
    content = models.TextField(verbose_name='评论内容')
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies', verbose_name='父评论')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '动态评论'
        verbose_name_plural = '动态评论'
        ordering = ['created_at']

    def __str__(self):
        return f'{self.user.username} 评论了 {self.activity.id} 号动态'