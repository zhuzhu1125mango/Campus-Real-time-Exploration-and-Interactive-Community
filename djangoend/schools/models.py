from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

User = get_user_model()


class School(models.Model):
    """
    院校模型
    存储大学/学院的基本信息
    """
    SCHOOL_TYPES = (
        ('comprehensive', '综合类'),
        ('science', '理工类'),
        ('agriculture', '农林类'),
        ('medicine', '医药类'),
        ('normal', '师范类'),
        ('language', '语言类'),
        ('finance', '财经类'),
        ('political', '政法类'),
        ('art', '艺术类'),
        ('sport', '体育类'),
        ('military', '军事类'),
        ('other', '其他'),
    )
    
    SCHOOL_LEVELS = (
        ('985', '985工程'),
        ('211', '211工程'),
        ('double_first_class', '双一流'),
        ('ordinary', '普通本科'),
        ('vocational', '高职高专'),
        ('independent', '独立学院'),
        ('sino_foreign', '中外合作'),
        ('other', '其他'),
    )
    
    # 基本信息
    name = models.CharField(_('院校名称'), max_length=100)
    english_name = models.CharField(_('英文名称'), max_length=200, blank=True)
    code = models.CharField(_('院校代码'), max_length=20, unique=True)
    abbreviation = models.CharField(_('简称'), max_length=50, blank=True)
    school_type = models.CharField(_('院校类型'), max_length=20, choices=SCHOOL_TYPES, default='comprehensive')
    school_level = models.CharField(_('院校层次'), max_length=20, choices=SCHOOL_LEVELS, default='ordinary')
    founded_year = models.IntegerField(_('创建年份'), null=True, blank=True)
    
    # 地理位置
    province = models.CharField(_('所在省份'), max_length=20)
    city = models.CharField(_('所在城市'), max_length=20)
    address = models.CharField(_('详细地址'), max_length=200, blank=True)
    location = models.CharField(_('地理坐标'), max_length=100, blank=True, help_text='经纬度，格式：纬度,经度')
    
    # 联系方式
    website = models.URLField(_('官方网站'), blank=True)
    email = models.EmailField(_('联系邮箱'), blank=True)
    phone = models.CharField(_('联系电话'), max_length=20, blank=True)
    
    # 招生信息
    admission_office_phone = models.CharField(_('招生办电话'), max_length=50, blank=True)
    admission_office_email = models.EmailField(_('招生办邮箱'), blank=True)
    has_graduate_program = models.BooleanField(_('是否有研究生院'), default=False)
    
    # 描述信息
    introduction = models.TextField(_('学校简介'), blank=True)
    features = models.TextField(_('特色优势'), blank=True)
    facilities = models.TextField(_('校园设施'), blank=True)
    
    # 媒体信息
    logo = models.ImageField(_('校徽'), upload_to='schools/logos/', blank=True, null=True)
    banner = models.ImageField(_('校园图片'), upload_to='schools/banners/', blank=True, null=True)
    
    # 统计信息
    student_count = models.IntegerField(_('学生人数'), null=True, blank=True)
    faculty_count = models.IntegerField(_('教师人数'), null=True, blank=True)
    
    # 排名信息
    national_rank = models.IntegerField(_('全国排名'), null=True, blank=True)
    world_rank = models.IntegerField(_('世界排名'), null=True, blank=True)
    
    # 元数据
    is_verified = models.BooleanField(_('信息是否已验证'), default=False)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('院校')
        verbose_name_plural = _('院校')
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Major(models.Model):
    """
    专业模型
    存储专业信息
    """
    DEGREE_TYPES = (
        ('bachelor', '本科'),
        ('master', '硕士'),
        ('doctor', '博士'),
        ('vocational', '专科'),
    )
    
    SUBJECT_CATEGORIES = (
        ('philosophy', '哲学'),
        ('economics', '经济学'),
        ('law', '法学'),
        ('education', '教育学'),
        ('literature', '文学'),
        ('history', '历史学'),
        ('science', '理学'),
        ('engineering', '工学'),
        ('agriculture', '农学'),
        ('medicine', '医学'),
        ('management', '管理学'),
        ('art', '艺术学'),
    )
    
    # 基本信息
    name = models.CharField(_('专业名称'), max_length=100)
    code = models.CharField(_('专业代码'), max_length=20)
    degree_type = models.CharField(_('学位类型'), max_length=20, choices=DEGREE_TYPES)
    subject_category = models.CharField(_('学科门类'), max_length=20, choices=SUBJECT_CATEGORIES)
    
    # 描述信息
    description = models.TextField(_('专业描述'), blank=True)
    career_prospects = models.TextField(_('就业前景'), blank=True)
    
    # 元数据
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('专业')
        verbose_name_plural = _('专业')
        ordering = ['name']
    
    def __str__(self):
        return self.name


class SchoolMajor(models.Model):
    """
    院校专业关联模型
    存储院校开设的专业信息
    """
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='majors')
    major = models.ForeignKey(Major, on_delete=models.CASCADE, related_name='schools')
    is_active = models.BooleanField(_('是否在招'), default=True)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('院校专业')
        verbose_name_plural = _('院校专业')
        unique_together = ['school', 'major']
    
    def __str__(self):
        return f"{self.school.name} - {self.major.name}"


class SchoolRating(models.Model):
    """
    院校评分模型
    存储用户对院校的评价
    """
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='school_ratings')
    rating = models.IntegerField(_('评分'), choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(_('评价内容'), blank=True)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('院校评分')
        verbose_name_plural = _('院校评分')
        unique_together = ['school', 'user']
    
    def __str__(self):
        return f"{self.school.name} - {self.user.username}"


class MajorRating(models.Model):
    """
    专业评分模型
    存储用户对专业的评价
    """
    major = models.ForeignKey(Major, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='major_ratings')
    rating = models.IntegerField(_('评分'), choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(_('评价内容'), blank=True)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('专业评分')
        verbose_name_plural = _('专业评分')
        unique_together = ['major', 'user']
    
    def __str__(self):
        return f"{self.major.name} - {self.user.username}"


class AdmissionScore(models.Model):
    """
    录取分数线模型
    存储院校专业的录取分数线
    """
    SCORE_TYPES = (
        ('art', '文科'),
        ('science', '理科'),
        ('comprehensive', '综合'),
    )
    
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='admission_scores')
    major = models.ForeignKey(Major, on_delete=models.CASCADE, related_name='admission_scores')
    year = models.IntegerField(_('年份'))
    province = models.CharField(_('省份'), max_length=20)
    score_type = models.CharField(_('科类'), max_length=20, choices=SCORE_TYPES)
    min_score = models.IntegerField(_('最低分'))
    max_score = models.IntegerField(_('最高分'))
    avg_score = models.IntegerField(_('平均分'))
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('录取分数线')
        verbose_name_plural = _('录取分数线')
        unique_together = ['school', 'major', 'year', 'province', 'score_type']
    
    def __str__(self):
        return f"{self.school.name} - {self.major.name} - {self.year}年"


class Forum(models.Model):
    """
    讨论区模型
    每个学校对应一个讨论区
    """
    school = models.OneToOneField(School, on_delete=models.CASCADE, related_name='forum')
    name = models.CharField(_('讨论区名称'), max_length=100)
    description = models.TextField(_('讨论区描述'), blank=True)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('讨论区')
        verbose_name_plural = _('讨论区')
    
    def __str__(self):
        return f"{self.school.name}的讨论区"


class Post(models.Model):
    """
    帖子模型
    存储用户发布的帖子
    """
    POST_STATUS = (
        ('draft', '草稿'),
        ('published', '已发布'),
        ('archived', '已归档'),
        ('deleted', '已删除'),
    )
    
    forum = models.ForeignKey(Forum, on_delete=models.CASCADE, related_name='posts')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    title = models.CharField(_('标题'), max_length=200)
    content = models.TextField(_('内容'))
    status = models.CharField(_('状态'), max_length=20, choices=POST_STATUS, default='published')
    views = models.IntegerField(_('浏览量'), default=0)
    likes = models.ManyToManyField(User, related_name='liked_posts', blank=True)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('帖子')
        verbose_name_plural = _('帖子')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title


class Comment(models.Model):
    """
    评论模型
    存储用户对帖子的评论
    """
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField(_('内容'))
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    likes = models.ManyToManyField(User, related_name='liked_comments', blank=True)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('评论')
        verbose_name_plural = _('评论')
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.author.username}的评论"


class Tag(models.Model):
    """
    标签模型
    用于对帖子进行分类
    """
    name = models.CharField(_('标签名称'), max_length=50, unique=True)
    description = models.TextField(_('标签描述'), blank=True)
    posts = models.ManyToManyField(Post, related_name='tags', blank=True)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('标签')
        verbose_name_plural = _('标签')
        ordering = ['name']
    
    def __str__(self):
        return self.name