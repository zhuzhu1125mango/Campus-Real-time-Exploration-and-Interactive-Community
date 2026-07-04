from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from schools.models import School  # 添加School模型的导入

User = get_user_model()


class Category(models.Model):
    """
    论坛分类模型
    用于对论坛板块进行分类
    """
    name = models.CharField(_('分类名称'), max_length=50)
    description = models.TextField(_('分类描述'), blank=True)
    icon = models.CharField(_('图标'), max_length=50, blank=True, help_text='可以使用Font Awesome图标名称')
    order = models.IntegerField(_('排序'), default=0)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('论坛分类')
        verbose_name_plural = _('论坛分类')
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name


class Board(models.Model):
    """
    论坛板块模型
    属于某个分类，包含多个主题
    一个学校只能有一个讨论区
    """
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='boards')
    name = models.CharField(_('板块名称'), max_length=100)
    description = models.TextField(_('板块描述'), blank=True)
    icon = models.CharField(_('图标'), max_length=50, blank=True, help_text='可以使用Font Awesome图标名称')
    order = models.IntegerField(_('排序'), default=0)
    moderators = models.ManyToManyField(User, related_name='moderated_boards', blank=True)
    is_active = models.BooleanField(_('是否激活'), default=True)
    school = models.OneToOneField(School, on_delete=models.CASCADE, related_name='board', null=True, blank=True)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('论坛板块')
        verbose_name_plural = _('论坛板块')
        ordering = ['category', 'order', 'name']
    
    def __str__(self):
        if self.school:
            return f"{self.name} ({self.school.name})"
        return self.name
    
    @property
    def topic_count(self):
        """获取板块的主题数量"""
        return self.topics.count()
    
    @property
    def post_count(self):
        """获取板块的帖子数量"""
        return Post.objects.filter(topic__board=self).count()
    
    @property
    def last_post(self):
        """获取板块的最后一个帖子"""
        return Post.objects.filter(topic__board=self).order_by('-created_at').first()


class Topic(models.Model):
    """
    主题模型
    属于某个板块，包含多个帖子
    """
    TOPIC_STATUS = (
        ('normal', '正常'),
        ('pinned', '置顶'),
        ('announcement', '公告'),
        ('closed', '已关闭'),
        ('hidden', '已隐藏'),
    )
    
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='topics')
    title = models.CharField(_('主题标题'), max_length=200)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='topics')
    status = models.CharField(_('状态'), max_length=20, choices=TOPIC_STATUS, default='normal')
    views = models.IntegerField(_('浏览量'), default=0)
    is_closed = models.BooleanField(_('是否关闭'), default=False)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('主题')
        verbose_name_plural = _('主题')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    @property
    def post_count(self):
        """获取主题的帖子数量"""
        return self.posts.count()
    
    @property
    def last_post(self):
        """获取主题的最后一个帖子"""
        return self.posts.order_by('-created_at').first()


class Post(models.Model):
    """
    帖子模型
    属于某个主题，用户可以回复
    """
    CONTENT_STATUS = (
        ('pending', '待审核'),
        ('approved', '已通过'),
        ('rejected', '已拒绝'),
        ('flagged', '标记审查')
    )
    
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='posts')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='forum_posts')
    content = models.TextField(_('内容'))  # 存储HTML格式的内容
    is_first_post = models.BooleanField(_('是否为首贴'), default=False)
    is_edited = models.BooleanField(_('是否已编辑'), default=False)
    edited_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='edited_posts', null=True, blank=True)
    edited_at = models.DateTimeField(_('编辑时间'), null=True, blank=True)
    
    # 审核相关字段
    content_status = models.CharField(_('内容状态'), max_length=20, choices=CONTENT_STATUS, default='approved')
    review_note = models.TextField(_('审核备注'), blank=True, null=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='reviewed_posts', null=True, blank=True)
    reviewed_at = models.DateTimeField(_('审核时间'), null=True, blank=True)
    
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('帖子')
        verbose_name_plural = _('帖子')
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.topic.title} - {self.author.username}"


class Attachment(models.Model):
    """
    附件模型
    用于存储帖子中的附件
    """
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(_('文件'), upload_to='forum/attachments/')
    filename = models.CharField(_('文件名'), max_length=200)
    file_size = models.IntegerField(_('文件大小'), help_text='以字节为单位')
    file_type = models.CharField(_('文件类型'), max_length=50)
    download_count = models.IntegerField(_('下载次数'), default=0)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('附件')
        verbose_name_plural = _('附件')
    
    def __str__(self):
        return self.filename


class Like(models.Model):
    """
    点赞模型
    用户对帖子的点赞
    """
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='forum_likes')
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('点赞')
        verbose_name_plural = _('点赞')
        unique_together = ['post', 'user']
    
    def __str__(self):
        return f"{self.user.username} -> {self.post.id}"


class Tag(models.Model):
    """
    标签模型
    用于对主题进行分类
    """
    name = models.CharField(_('标签名称'), max_length=50, unique=True)
    description = models.TextField(_('标签描述'), blank=True)
    topics = models.ManyToManyField(Topic, related_name='tags', blank=True)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('标签')
        verbose_name_plural = _('标签')
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Report(models.Model):
    """
    举报模型
    用户举报不当内容
    """
    REPORT_TYPES = (
        ('spam', '垃圾内容'),
        ('offensive', '冒犯性内容'),
        ('inappropriate', '不适当内容'),
        ('illegal', '违法内容'),
        ('other', '其他'),
    )
    
    REPORT_STATUS = (
        ('pending', '待处理'),
        ('investigating', '调查中'),
        ('resolved', '已解决'),
        ('rejected', '已驳回'),
    )
    
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reports')
    report_type = models.CharField(_('举报类型'), max_length=20, choices=REPORT_TYPES)
    description = models.TextField(_('详细说明'))
    status = models.CharField(_('状态'), max_length=20, choices=REPORT_STATUS, default='pending')
    handled_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='handled_reports', null=True, blank=True)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('举报')
        verbose_name_plural = _('举报')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.reporter.username} 举报 {self.post.id}"


class Notification(models.Model):
    """
    通知模型
    用于通知用户论坛活动
    """
    NOTIFICATION_TYPES = (
        ('topic_reply', '主题回复'),
        ('mention', '提及'),
        ('like', '点赞'),
        ('topic_moved', '主题移动'),
        ('topic_closed', '主题关闭'),
        ('topic_pinned', '主题置顶'),
        ('system', '系统通知'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='forum_notifications')
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='sent_forum_notifications', null=True, blank=True)
    notification_type = models.CharField(_('通知类型'), max_length=20, choices=NOTIFICATION_TYPES)
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, related_name='notifications', null=True, blank=True)
    post = models.ForeignKey(Post, on_delete=models.SET_NULL, related_name='notifications', null=True, blank=True)
    message = models.TextField(_('通知内容'))
    is_read = models.BooleanField(_('是否已读'), default=False)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('通知')
        verbose_name_plural = _('通知')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username}的通知: {self.message[:30]}"


class Bookmark(models.Model):
    """
    书签模型
    用户收藏主题
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='forum_bookmarks')
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='bookmarks')
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('书签')
        verbose_name_plural = _('书签')
        unique_together = ['user', 'topic']
    
    def __str__(self):
        return f"{self.user.username} -> {self.topic.title[:30]}"


class Comment(models.Model):
    """
    评论模型
    用于对帖子进行评论，支持多级回复
    """
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='forum_comments')
    content = models.TextField(_('内容'))
    parent = models.ForeignKey('self', on_delete=models.CASCADE, related_name='replies', null=True, blank=True)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('评论')
        verbose_name_plural = _('评论')
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.author.username} -> {self.post.id}"
    
    @property
    def like_count(self):
        """获取评论的点赞数"""
        return CommentLike.objects.filter(comment=self).count()


class CommentLike(models.Model):
    """
    评论点赞模型
    用户对评论的点赞
    """
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comment_likes')
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('评论点赞')
        verbose_name_plural = _('评论点赞')
        unique_together = ['comment', 'user']
    
    def __str__(self):
        return f"{self.user.username} -> {self.comment.id}"
