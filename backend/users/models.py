from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from .validators import validate_image_extension, validate_avatar_size, validate_banner_size

class User(AbstractUser):
    """自定义用户模型"""
    email = models.EmailField(blank=True, null=True, unique=True, verbose_name='邮箱')
    phone = models.CharField(max_length=11, blank=True, null=True, unique=True, verbose_name='手机号')
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
        validators=[validate_image_extension, validate_avatar_size],
        verbose_name='头像'
    )
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
    banner = models.ImageField(
        upload_to='banners/',
        null=True,
        blank=True,
        validators=[validate_image_extension, validate_banner_size],
        verbose_name='横幅'
    )
    
    # 积分系统
    points = models.IntegerField(default=0, verbose_name='积分')
    level = models.IntegerField(default=1, verbose_name='等级')
    
    # 收藏的学校
    favorite_schools = models.ManyToManyField('schools.School', blank=True, related_name='favorited_by')
    
    @property
    def level_name(self):
        """根据等级返回等级名称"""
        levels = [
            (0, '新手'),
            (50, '初级学员'),
            (200, '中级学员'),
            (500, '高级学员'),
            (1000, '学霸'),
            (2000, '学神'),
            (5000, '导师'),
            (10000, '大师')
        ]
        for points, name in reversed(levels):
            if self.points >= points:
                return name
        return '新手'
    
    @property
    def next_level_points(self):
        """计算升级到下一级需要的积分"""
        level_thresholds = [0, 50, 200, 500, 1000, 2000, 5000, 10000]
        current_threshold = level_thresholds[min(self.level - 1, len(level_thresholds) - 1)]
        next_threshold = level_thresholds[min(self.level, len(level_thresholds) - 1)]
        return next_threshold - current_threshold
    
    @property
    def level_progress(self):
        """计算当前等级的进度百分比"""
        level_thresholds = [0, 50, 200, 500, 1000, 2000, 5000, 10000]
        if self.level >= len(level_thresholds):
            return 100
        current_threshold = level_thresholds[self.level - 1]
        next_threshold = level_thresholds[self.level]
        if next_threshold == current_threshold:
            return 100
        return min(100, int((self.points - current_threshold) / (next_threshold - current_threshold) * 100))
    
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
        indexes = [
            models.Index(fields=['email', 'is_used', 'code_type'], name='users_code_email_used_idx'),
            models.Index(fields=['phone', 'is_used', 'code_type'], name='users_code_phone_used_idx'),
            models.Index(fields=['created_at'], name='users_code_created_idx'),
        ]

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
        indexes = [
            models.Index(fields=['user', 'activity_type', '-timestamp'], name='users_act_user_type_time_idx'),
            models.Index(fields=['target_type', 'target_id'], name='users_act_target_idx'),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.activity_type} - {self.target_type} - {self.target_id}"


class PointsRecord(models.Model):
    """积分记录模型"""
    POINTS_ACTION = [
        ('register', '注册'),
        ('login', '登录'),
        ('post', '发帖'),
        ('reply', '回复'),
        ('like', '点赞'),
        ('comment', '评论'),
        ('share', '分享'),
        ('invite', '邀请'),
        ('daily_checkin', '每日签到'),
        ('complete_profile', '完善资料'),
        ('verified', '身份认证'),
        ('system', '系统奖励'),
        ('admin', '管理员操作')
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='points_records', verbose_name='用户')
    action = models.CharField(max_length=50, choices=POINTS_ACTION, verbose_name='行为类型')
    points = models.IntegerField(verbose_name='积分变化')
    description = models.CharField(max_length=200, blank=True, verbose_name='描述')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        verbose_name = '积分记录'
        verbose_name_plural = '积分记录'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'action', '-created_at'], name='users_pts_user_act_crt_idx'),
            models.Index(fields=['user', '-created_at'], name='users_pts_user_crt_idx'),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.points}"
