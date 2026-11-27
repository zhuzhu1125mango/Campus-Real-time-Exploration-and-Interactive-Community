from django.db import models
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from datetime import time
import uuid


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
        indexes = [
            models.Index(fields=['instructor', 'is_published'], name='learn_course_inst_pub_idx'),
            models.Index(fields=['is_published', '-created_at'], name='learn_course_pub_crt_idx'),
        ]

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
    last_position = models.IntegerField(default=0, verbose_name='上次观看位置(秒)')

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


def generate_order_no():
    """生成唯一的支付订单号。"""
    return f'ORD{timezone.now():%Y%m%d%H%M%S}{uuid.uuid4().hex[:6].upper()}'


class PaymentOrder(models.Model):
    """课程支付订单。

    当前接入的是模拟支付：创建订单后调用 pay 接口即视为支付成功，
    后续可替换为微信/支付宝等真实网关，只需在 pay 流程中补充回调校验。
    """
    STATUS_PENDING = 'pending'
    STATUS_PAID = 'paid'
    STATUS_CANCELLED = 'cancelled'
    STATUS_REFUNDED = 'refunded'
    STATUS_CHOICES = [
        (STATUS_PENDING, '待支付'),
        (STATUS_PAID, '已支付'),
        (STATUS_CANCELLED, '已取消'),
        (STATUS_REFUNDED, '已退款'),
    ]
    METHOD_MOCK = 'mock'
    METHOD_CHOICES = [
        (METHOD_MOCK, '模拟支付'),
        ('wechat', '微信支付'),
        ('alipay', '支付宝'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='payment_orders', verbose_name='用户'
    )
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE,
        related_name='payment_orders', verbose_name='课程'
    )
    order_no = models.CharField(max_length=64, unique=True, verbose_name='订单号')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='订单金额')
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING, verbose_name='订单状态'
    )
    payment_method = models.CharField(
        max_length=20, choices=METHOD_CHOICES, default=METHOD_MOCK, verbose_name='支付方式'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name='支付时间')

    class Meta:
        verbose_name = '支付订单'
        verbose_name_plural = '支付订单'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status'], name='learn_order_user_status_idx'),
            models.Index(fields=['course', 'status'], name='learn_order_course_status_idx'),
        ]

    def __str__(self):
        return f'{self.order_no} - {self.user.username} - {self.course.title}'

    def save(self, *args, **kwargs):
        if not self.order_no:
            self.order_no = generate_order_no()
        super().save(*args, **kwargs)


class Certificate(models.Model):
    """课程结业证书。

    用户完成课程后自动发放，一条报名记录最多对应一张证书，
    可通过证书编号公开校验真伪。
    """
    STATUS_VALID = 'valid'
    STATUS_REVOKED = 'revoked'
    STATUS_CHOICES = [
        (STATUS_VALID, '有效'),
        (STATUS_REVOKED, '已撤销'),
    ]

    enrollment = models.OneToOneField(
        Enrollment, on_delete=models.CASCADE,
        related_name='certificate', verbose_name='报名记录'
    )
    number = models.CharField(max_length=64, unique=True, verbose_name='证书编号')
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_VALID, verbose_name='证书状态'
    )
    issued_at = models.DateTimeField(auto_now_add=True, verbose_name='发放时间')
    revoked_at = models.DateTimeField(null=True, blank=True, verbose_name='撤销时间')
    remark = models.CharField(max_length=200, blank=True, verbose_name='备注')

    class Meta:
        verbose_name = '课程证书'
        verbose_name_plural = '课程证书'
        ordering = ['-issued_at']
        indexes = [
            models.Index(fields=['status', '-issued_at'], name='learn_cert_status_idx'),
        ]

    def __str__(self):
        return f'{self.number} - {self.enrollment.user.username} - {self.enrollment.course.title}'


class StudyReminder(models.Model):
    """学习提醒设置。

    每个用户对每门课程最多一条提醒，由 Celery Beat 定时扫描并发送站内通知。
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='study_reminders', verbose_name='用户'
    )
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE,
        related_name='study_reminders', verbose_name='课程'
    )
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    remind_time = models.TimeField(default=time(20, 0), verbose_name='提醒时间')
    last_reminded_at = models.DateTimeField(null=True, blank=True, verbose_name='最近提醒时间')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '学习提醒'
        verbose_name_plural = '学习提醒'
        ordering = ['-updated_at']
        unique_together = ('user', 'course')
        indexes = [
            models.Index(fields=['is_active', 'remind_time'], name='learn_reminder_active_idx'),
        ]

    def __str__(self):
        return f'{self.user.username} - {self.course.title} - {self.remind_time:%H:%M}'