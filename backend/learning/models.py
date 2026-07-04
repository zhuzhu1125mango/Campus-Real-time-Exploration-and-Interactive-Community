from django.db import models
from django.conf import settings
from django.utils import timezone
from django.urls import reverse


class Course(models.Model):
    """课程模型"""
    title = models.CharField(max_length=200, verbose_name='课程标题')
    slug = models.SlugField(max_length=200, unique=True, verbose_name='课程别名')
    description = models.TextField(verbose_name='课程描述')
    instructor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='courses', verbose_name='讲师')
    cover_image = models.ImageField(upload_to='learning/courses/', blank=True, null=True, verbose_name='课程封面')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name='课程价格')
    is_free = models.BooleanField(default=False, verbose_name='是否免费')
    is_published = models.BooleanField(default=False, verbose_name='是否发布')
    publish_date = models.DateTimeField(null=True, blank=True, verbose_name='发布时间')
    enroll_count = models.IntegerField(default=0, verbose_name='报名人数')
    view_count = models.IntegerField(default=0, verbose_name='浏览次数')
    average_rating = models.FloatField(default=0.0, verbose_name='平均评分')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '课程'
        verbose_name_plural = '课程'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('course-detail', args=[self.slug])

    def save(self, *args, **kwargs):
        if self.is_published and not self.publish_date:
            self.publish_date = timezone.now()
        super().save(*args, **kwargs)


class Category(models.Model):
    """课程分类模型"""
    name = models.CharField(max_length=100, unique=True, verbose_name='分类名称')
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children', verbose_name='父分类')
    description = models.TextField(blank=True, verbose_name='分类描述')
    order = models.IntegerField(default=0, verbose_name='排序')
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '课程分类'
        verbose_name_plural = '课程分类'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class CourseCategory(models.Model):
    """课程与分类的多对多关系"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='categories', verbose_name='课程')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='courses', verbose_name='分类')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '课程分类关联'
        verbose_name_plural = '课程分类关联'
        unique_together = ('course', 'category')

    def __str__(self):
        return f'{self.course.title} - {self.category.name}'


class Chapter(models.Model):
    """章节模型"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='chapters', verbose_name='课程')
    title = models.CharField(max_length=200, verbose_name='章节标题')
    description = models.TextField(blank=True, verbose_name='章节描述')
    order = models.IntegerField(default=0, verbose_name='排序')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '章节'
        verbose_name_plural = '章节'
        ordering = ['course', 'order']

    def __str__(self):
        return f'{self.course.title} - {self.title}'


class Lesson(models.Model):
    """课时模型"""
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='lessons', verbose_name='章节')
    title = models.CharField(max_length=200, verbose_name='课时标题')
    description = models.TextField(blank=True, verbose_name='课时描述')
    content = models.TextField(blank=True, verbose_name='课时内容')
    video_url = models.URLField(blank=True, verbose_name='视频链接')
    duration = models.DurationField(blank=True, null=True, verbose_name='时长')
    is_free = models.BooleanField(default=False, verbose_name='是否免费')
    order = models.IntegerField(default=0, verbose_name='排序')
    view_count = models.IntegerField(default=0, verbose_name='观看次数')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '课时'
        verbose_name_plural = '课时'
        ordering = ['chapter', 'order']

    def __str__(self):
        return f'{self.chapter.course.title} - {self.chapter.title} - {self.title}'


class Enrollment(models.Model):
    """课程报名模型"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='enrollments', verbose_name='用户')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments', verbose_name='课程')
    is_completed = models.BooleanField(default=False, verbose_name='是否完成')
    progress = models.FloatField(default=0.0, verbose_name='学习进度')
    enrolled_at = models.DateTimeField(auto_now_add=True, verbose_name='报名时间')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')

    class Meta:
        verbose_name = '课程报名'
        verbose_name_plural = '课程报名'
        unique_together = ('user', 'course')

    def __str__(self):
        return f'{self.user.username} - {self.course.title}'


class Progress(models.Model):
    """学习进度模型"""
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='progresses', verbose_name='报名')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='progresses', verbose_name='课时')
    is_completed = models.BooleanField(default=False, verbose_name='是否完成')
    last_watched_at = models.DateTimeField(null=True, blank=True, verbose_name='最后观看时间')
    watched_duration = models.DurationField(default=timezone.timedelta(seconds=0), verbose_name='观看时长')

    class Meta:
        verbose_name = '学习进度'
        verbose_name_plural = '学习进度'
        unique_together = ('enrollment', 'lesson')

    def __str__(self):
        return f'{self.enrollment.user.username} - {self.lesson.title}'


class Review(models.Model):
    """课程评价模型"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews', verbose_name='用户')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='reviews', verbose_name='课程')
    rating = models.IntegerField(choices=[(1, '1星'), (2, '2星'), (3, '3星'), (4, '4星'), (5, '5星')], verbose_name='评分')
    comment = models.TextField(blank=True, verbose_name='评价内容')
    is_approved = models.BooleanField(default=True, verbose_name='是否批准')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '课程评价'
        verbose_name_plural = '课程评价'
        unique_together = ('user', 'course')

    def __str__(self):
        return f'{self.user.username} - {self.course.title} - {self.rating}星'


class LearningResource(models.Model):
    """学习资源模型"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='resources', verbose_name='课程')
    title = models.CharField(max_length=200, verbose_name='资源标题')
    description = models.TextField(blank=True, verbose_name='资源描述')
    file = models.FileField(upload_to='learning/resources/', verbose_name='资源文件')
    file_type = models.CharField(max_length=50, verbose_name='文件类型')
    file_size = models.IntegerField(verbose_name='文件大小')
    download_count = models.IntegerField(default=0, verbose_name='下载次数')
    is_free = models.BooleanField(default=False, verbose_name='是否免费')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '学习资源'
        verbose_name_plural = '学习资源'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.course.title} - {self.title}'