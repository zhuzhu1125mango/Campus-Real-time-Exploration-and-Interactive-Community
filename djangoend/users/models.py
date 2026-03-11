from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    """
    自定义用户模型
    扩展Django默认的User模型，添加额外的字段
    """
    GENDER_CHOICES = (
        ('M', '男'),
        ('F', '女'),
        ('O', '其他'),
    )

    # 基本信息
    email = models.EmailField(_('邮箱'), unique=True, blank=True, null=True)
    phone = models.CharField(_('手机号'), max_length=11, blank=True, null=True, unique=True)
    avatar = models.ImageField(_('头像'), upload_to='avatars/', blank=True, null=True)
    banner = models.ImageField(_('背景图'), upload_to='banners/', blank=True, null=True)
    gender = models.CharField(_('性别'), max_length=1, choices=GENDER_CHOICES, default='O')
    
    # 教育信息
    education_level = models.CharField(_('学历'), max_length=20, blank=True)
    school = models.CharField(_('学校'), max_length=100, blank=True, null=True)
    major = models.CharField(_('专业'), max_length=100, blank=True, null=True)
    graduation_year = models.IntegerField(_('毕业年份'), null=True, blank=True)
    
    # 报考信息
    target_degree = models.CharField(_('目标学历'), max_length=20, blank=True)
    target_major = models.CharField(_('目标专业'), max_length=100, blank=True)
    target_schools = models.TextField(_('目标院校'), blank=True)
    
    # 其他信息
    bio = models.TextField(_('个人简介'), max_length=500, blank=True)
    
    # 用户类型
    is_student = models.BooleanField(_('是否为学生'), default=False)
    
    # 学生特有字段
    grade = models.CharField(_('年级'), max_length=20, blank=True, null=True)
    
    # 用户状态
    is_verified = models.BooleanField(_('是否验证'), default=False)
    
    # 收藏
    favorite_schools = models.ManyToManyField('schools.School', related_name='favorited_by', blank=True, verbose_name=_('收藏的学校'))
    
    # 创建和更新时间
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)

    class Meta:
        verbose_name = _('用户')
        verbose_name_plural = _('用户')
        ordering = ['-date_joined']

    def __str__(self):
        return self.username

    def get_full_name(self):
        """
        返回用户全名
        """
        if self.first_name and self.last_name:
            return f"{self.last_name}{self.first_name}"
        return self.username

    @property
    def is_complete_profile(self):
        """
        检查用户是否完成了个人资料
        """
        if self.is_student:
            return bool(self.email and self.phone and self.school and self.major)
        return bool(self.email and self.phone)

class UserProfile(models.Model):
    """
    用户扩展资料模型
    存储用户的额外信息
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # 个人兴趣和偏好
    interests = models.TextField(_('兴趣爱好'), blank=True)
    target_schools = models.TextField(_('目标院校'), blank=True)
    target_majors = models.TextField(_('目标专业'), blank=True)
    
    # 学习情况
    gpa = models.FloatField(_('GPA'), blank=True, null=True)
    study_status = models.CharField(_('学习状态'), max_length=50, blank=True)
    
    # 社交链接
    website = models.URLField(_('个人网站'), blank=True)
    social_links = models.JSONField(_('社交链接'), default=dict, blank=True)
    
    class Meta:
        verbose_name = _('用户资料')
        verbose_name_plural = _('用户资料')
        
    def __str__(self):
        return f"{self.user.username}的资料"

class VerificationCode(models.Model):
    """
    验证码模型
    用于邮箱和手机验证
    """
    CODE_TYPE_CHOICES = (
        ('email', '邮箱验证'),
        ('phone', '手机验证'),
        ('password', '密码重置'),
    )
    
    code = models.CharField(_('验证码'), max_length=10)
    email = models.EmailField(_('邮箱'), blank=True, null=True)
    phone = models.CharField(_('手机号'), max_length=11, blank=True, null=True)
    code_type = models.CharField(_('验证码类型'), max_length=20, choices=CODE_TYPE_CHOICES)
    is_used = models.BooleanField(_('是否已使用'), default=False)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    expires_at = models.DateTimeField(_('过期时间'))
    
    class Meta:
        verbose_name = _('验证码')
        verbose_name_plural = _('验证码')
        
    def __str__(self):
        if self.email:
            return f"{self.email}的{self.get_code_type_display()}"
        return f"{self.phone}的{self.get_code_type_display()}"
        
    @property
    def is_expired(self):
        """
        检查验证码是否已过期
        """
        from django.utils import timezone
        return timezone.now() > self.expires_at 