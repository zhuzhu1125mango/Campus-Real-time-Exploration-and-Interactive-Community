from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class User(AbstractUser):
    """自定义用户模型"""
    email = models.EmailField(blank=True, null=True, unique=True, verbose_name='邮箱')
    phone = models.CharField(max_length=11, blank=True, null=True, unique=True, verbose_name='手机号')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, verbose_name='头像')
    gender = models.CharField(max_length=1, choices=[('M', '男'), ('F', '女'), ('O', '其他')], default='O', verbose_name='性别')
    education_level = models.CharField(max_length=20, blank=True, verbose_name='学历')
    school = models.CharField(max_length=100, blank=True, null=True, verbose_name='学校')
    major = models.CharField(max_length=100, blank=True, null=True, verbose_name='专业')
    graduation_year = models.IntegerField(null=True, blank=True, verbose_name='毕业年份')
    target_degree = models.CharField(max_length=20, blank=True, verbose_name='目标学历')
    target_major = models.CharField(max_length=100, blank=True, verbose_name='目标专业')
    target_schools = models.TextField(blank=True, verbose_name='目标院校')
    bio = models.TextField(max_length=500, blank=True, verbose_name='个人简介')
    is_student = models.BooleanField(default=False, verbose_name='是否为学生')
    grade = models.CharField(max_length=20, blank=True, null=True, verbose_name='年级')
    is_verified = models.BooleanField(default=False, verbose_name='是否验证')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    banner = models.ImageField(upload_to='banners/', null=True, blank=True, verbose_name='横幅')
    
    # 收藏的学校
    favorite_schools = models.ManyToManyField('schools.School', blank=True, related_name='favorited_by')
    
    class Meta:
        verbose_name = '用户'
        verbose_name_plural = '用户'
        ordering = ['-date_joined']
    
    def __str__(self):
        return self.username

class UserProfile(models.Model):
    """用户详细资料模型"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name='用户')
    interests = models.TextField(blank=True, verbose_name='兴趣爱好')
    target_schools = models.TextField(blank=True, verbose_name='目标院校')
    target_majors = models.TextField(blank=True, verbose_name='目标专业')
    gpa = models.FloatField(null=True, blank=True, verbose_name='GPA')
    study_status = models.CharField(max_length=50, blank=True, verbose_name='学习状态')
    website = models.URLField(blank=True, verbose_name='个人网站')
    social_links = models.JSONField(default=dict, blank=True, verbose_name='社交链接')
    
    class Meta:
        verbose_name = '用户资料'
        verbose_name_plural = '用户资料'
    
    def __str__(self):
        return f"{self.user.username} 的资料"

class VerificationCode(models.Model):
    """验证码模型"""
    code = models.CharField(max_length=10, verbose_name='验证码')
    email = models.EmailField(blank=True, null=True, verbose_name='邮箱')
    phone = models.CharField(max_length=11, blank=True, null=True, verbose_name='手机号')
    code_type = models.CharField(max_length=20, choices=[
        ('email', '邮箱验证'),
        ('phone', '手机验证'),
        ('password', '密码重置')
    ], verbose_name='验证码类型')
    is_used = models.BooleanField(default=False, verbose_name='是否已使用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    expires_at = models.DateTimeField(verbose_name='过期时间')
    
    class Meta:
        verbose_name = '验证码'
        verbose_name_plural = '验证码'
    
    @property
    def is_expired(self):
        """检查验证码是否过期"""
        return timezone.now() > self.expires_at
    
    def __str__(self):
        return f"{self.code} - {self.code_type}"

class UserActivity(models.Model):
    """用户行为记录模型"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities', verbose_name='用户')
    activity_type = models.CharField(max_length=50, choices=[
        ('browse', '浏览'),
        ('search', '搜索'),
        ('favorite', '收藏'),
        ('compare', '对比'),
        ('rate', '评分')
    ], verbose_name='行为类型')
    target_type = models.CharField(max_length=50, choices=[
        ('school', '院校'),
        ('major', '专业'),
        ('post', '帖子'),
        ('topic', '主题')
    ], verbose_name='目标类型')
    target_id = models.IntegerField(verbose_name='目标ID')
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='时间戳')
    metadata = models.JSONField(default=dict, verbose_name='元数据')
    
    class Meta:
        verbose_name = '用户行为'
        verbose_name_plural = '用户行为'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user.username} - {self.activity_type} - {self.target_type} - {self.target_id}"
