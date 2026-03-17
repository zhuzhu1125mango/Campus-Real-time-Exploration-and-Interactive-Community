from django.db import models
from django.utils import timezone

class School(models.Model):
    """学校模型"""
    # 学校基本信息
    name = models.CharField(max_length=100, verbose_name='学校名称')
    english_name = models.CharField(max_length=200, blank=True, verbose_name='英文名称')
    code = models.CharField(max_length=20, blank=True, verbose_name='学校代码')
    abbreviation = models.CharField(max_length=20, blank=True, verbose_name='简称')
    
    # 学校类型和层次
    SCHOOL_TYPES = [
        ('comprehensive', '综合'),
        ('science', '理工'),
        ('liberal_arts', '文科'),
        ('medical', '医药'),
        ('agriculture', '农林'),
        ('normal', '师范'),
        ('finance', '财经'),
        ('engineering', '工科'),
        ('other', '其他')
    ]
    school_type = models.CharField(max_length=20, choices=SCHOOL_TYPES, default='comprehensive', verbose_name='学校类型')
    
    SCHOOL_LEVELS = [
        ('985', '985工程'),
        ('211', '211工程'),
        ('double_first_class', '双一流'),
        ('key', '重点'),
        ('ordinary', '普通')
    ]
    school_level = models.CharField(max_length=20, choices=SCHOOL_LEVELS, default='ordinary', verbose_name='办学层次')
    
    # 学校基本信息
    founded_year = models.IntegerField(null=True, blank=True, verbose_name='建校时间')
    province = models.CharField(max_length=50, verbose_name='所在省份')
    city = models.CharField(max_length=50, verbose_name='所在城市')
    address = models.CharField(max_length=200, blank=True, verbose_name='详细地址')
    website = models.URLField(blank=True, verbose_name='学校官网')
    description = models.TextField(blank=True, verbose_name='学校描述')
    
    # 学校规模
    student_count = models.IntegerField(null=True, blank=True, verbose_name='学生人数')
    faculty_count = models.IntegerField(null=True, blank=True, verbose_name='教职工人数')
    campus_area = models.FloatField(null=True, blank=True, verbose_name='校园面积(万平方米)')
    
    # 学校排名
    national_rank = models.IntegerField(null=True, blank=True, verbose_name='全国排名')
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = '学校'
        verbose_name_plural = '学校'
        ordering = ['-national_rank', 'name']

class Major(models.Model):
    """专业模型"""
    # 专业基本信息
    name = models.CharField(max_length=100, verbose_name='专业名称')
    code = models.CharField(max_length=20, verbose_name='专业代码')
    description = models.TextField(blank=True, verbose_name='专业描述')
    
    # 学位类型
    DEGREE_TYPES = [
        ('bachelor', '本科'),
        ('master', '硕士'),
        ('doctor', '博士')
    ]
    degree_type = models.CharField(max_length=20, choices=DEGREE_TYPES, default='bachelor', verbose_name='学位类型')
    
    # 学科门类
    SUBJECT_CATEGORIES = [
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
        ('art', '艺术学')
    ]
    subject_category = models.CharField(max_length=20, choices=SUBJECT_CATEGORIES, default='science', verbose_name='学科门类')
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = '专业'
        verbose_name_plural = '专业'
        ordering = ['name']

class SchoolMajor(models.Model):
    """学校专业关联模型"""
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='majors', verbose_name='学校')
    major = models.ForeignKey(Major, on_delete=models.CASCADE, related_name='schools', verbose_name='专业')
    is_active = models.BooleanField(default=True, verbose_name='是否开设')
    
    # 专业特色
    is_key_major = models.BooleanField(default=False, verbose_name='是否重点专业')
    is_characteristic_major = models.BooleanField(default=False, verbose_name='是否特色专业')
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    def __str__(self):
        return f"{self.school.name} - {self.major.name}"
    
    class Meta:
        verbose_name = '学校专业'
        verbose_name_plural = '学校专业'
        unique_together = ('school', 'major')

class SchoolRating(models.Model):
    """学校评分模型"""
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='ratings', verbose_name='学校')
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='school_ratings', verbose_name='用户')
    rating = models.IntegerField(choices=[(1, '1星'), (2, '2星'), (3, '3星'), (4, '4星'), (5, '5星')], verbose_name='评分')
    comment = models.TextField(blank=True, verbose_name='评价内容')
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    def __str__(self):
        return f"{self.user.username} 对 {self.school.name} 的评价"
    
    class Meta:
        verbose_name = '学校评分'
        verbose_name_plural = '学校评分'
        unique_together = ('school', 'user')

class MajorRating(models.Model):
    """专业评分模型"""
    major = models.ForeignKey(Major, on_delete=models.CASCADE, related_name='ratings', verbose_name='专业')
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='major_ratings', verbose_name='用户')
    rating = models.IntegerField(choices=[(1, '1星'), (2, '2星'), (3, '3星'), (4, '4星'), (5, '5星')], verbose_name='评分')
    comment = models.TextField(blank=True, verbose_name='评价内容')
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    def __str__(self):
        return f"{self.user.username} 对 {self.major.name} 的评价"
    
    class Meta:
        verbose_name = '专业评分'
        verbose_name_plural = '专业评分'
        unique_together = ('major', 'user')

class AdmissionScore(models.Model):
    """录取分数线模型"""
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='admission_scores', verbose_name='学校')
    major = models.ForeignKey(Major, on_delete=models.SET_NULL, null=True, blank=True, related_name='admission_scores', verbose_name='专业')
    
    # 分数线信息
    year = models.IntegerField(verbose_name='年份')
    province = models.CharField(max_length=50, verbose_name='省份')
    score_type = models.CharField(max_length=20, choices=[('science', '理科'), ('liberal_arts', '文科'), ('comprehensive', '综合')], verbose_name='科类')
    min_score = models.IntegerField(verbose_name='最低分')
    avg_score = models.IntegerField(verbose_name='平均分')
    ranking = models.IntegerField(null=True, blank=True, verbose_name='排名')
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    def __str__(self):
        return f"{self.school.name} {self.year}年录取分数线"
    
    class Meta:
        verbose_name = '录取分数线'
        verbose_name_plural = '录取分数线'
        ordering = ['-year']

class Forum(models.Model):
    """论坛模型"""
    school = models.OneToOneField(School, on_delete=models.CASCADE, related_name='forum', verbose_name='学校')
    name = models.CharField(max_length=100, verbose_name='论坛名称')
    description = models.TextField(blank=True, verbose_name='论坛描述')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = '论坛'
        verbose_name_plural = '论坛'

class Tag(models.Model):
    """标签模型"""
    name = models.CharField(max_length=50, unique=True, verbose_name='标签名称')
    description = models.TextField(blank=True, verbose_name='标签描述')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = '标签'
        verbose_name_plural = '标签'

class Post(models.Model):
    """帖子模型"""
    forum = models.ForeignKey(Forum, on_delete=models.CASCADE, related_name='posts', verbose_name='论坛')
    author = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='posts', verbose_name='作者')
    title = models.CharField(max_length=200, verbose_name='标题')
    content = models.TextField(verbose_name='内容')
    tags = models.ManyToManyField(Tag, blank=True, related_name='posts', verbose_name='标签')
    
    # 统计信息
    view_count = models.IntegerField(default=0, verbose_name='浏览数')
    comment_count = models.IntegerField(default=0, verbose_name='评论数')
    like_count = models.IntegerField(default=0, verbose_name='点赞数')
    
    # 状态
    is_published = models.BooleanField(default=True, verbose_name='是否发布')
    is_sticky = models.BooleanField(default=False, verbose_name='是否置顶')
    is_精华 = models.BooleanField(default=False, verbose_name='是否精华')
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = '帖子'
        verbose_name_plural = '帖子'
        ordering = ['-is_sticky', '-created_at']

class Comment(models.Model):
    """评论模型"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments', verbose_name='帖子')
    author = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='comments', verbose_name='作者')
    content = models.TextField(verbose_name='内容')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies', verbose_name='父评论')
    
    # 统计信息
    like_count = models.IntegerField(default=0, verbose_name='点赞数')
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    def __str__(self):
        return f"{self.author.username} 的评论"
    
    class Meta:
        verbose_name = '评论'
        verbose_name_plural = '评论'
        ordering = ['created_at']

class Event(models.Model):
    """校园活动模型"""
    title = models.CharField(max_length=200, verbose_name='活动标题')
    description = models.TextField(verbose_name='活动描述')
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='events', verbose_name='学校')
    start_time = models.DateTimeField(verbose_name='开始时间')
    end_time = models.DateTimeField(verbose_name='结束时间')
    location = models.CharField(max_length=200, verbose_name='活动地点')
    organizer = models.CharField(max_length=100, verbose_name='组织者')
    capacity = models.IntegerField(null=True, blank=True, verbose_name='活动容量')
    registration_deadline = models.DateTimeField(null=True, blank=True, verbose_name='报名截止时间')
    is_public = models.BooleanField(default=True, verbose_name='是否公开')
    
    # 活动状态
    STATUS_CHOICES = [
        ('upcoming', '即将开始'),
        ('ongoing', '进行中'),
        ('completed', '已完成'),
        ('cancelled', '已取消')
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming', verbose_name='活动状态')
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = '校园活动'
        verbose_name_plural = '校园活动'
        ordering = ['start_time']

class EventRegistration(models.Model):
    """活动报名模型"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations', verbose_name='活动')
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='event_registrations', verbose_name='用户')
    
    # 报名状态
    STATUS_CHOICES = [
        ('pending', '待确认'),
        ('confirmed', '已确认'),
        ('cancelled', '已取消')
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='报名状态')
    
    # 报名信息
    metadata = models.JSONField(default=dict, verbose_name='报名信息')
    
    # 时间戳
    registered_at = models.DateTimeField(auto_now_add=True, verbose_name='报名时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    def __str__(self):
        return f"{self.user.username} 报名 {self.event.title}"
    
    class Meta:
        verbose_name = '活动报名'
        verbose_name_plural = '活动报名'
        unique_together = ('event', 'user')
