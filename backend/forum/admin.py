from django.contrib import admin
from .models import (
    Category, Board, Topic, Post, Attachment,
    Like, Tag, Report, Notification, Bookmark
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'order', 'created_at')
    search_fields = ('name', 'description')
    list_filter = ('created_at',)
    ordering = ('order', 'name')


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'order', 'is_active', 'created_at')
    list_filter = ('category', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    filter_horizontal = ('moderators',)
    ordering = ('category', 'order', 'name')


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'board', 'author', 'status', 'views', 'is_closed', 'created_at')
    list_filter = ('board', 'status', 'is_closed', 'created_at')
    search_fields = ('title', 'author__username')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('get_topic_title', 'author', 'is_first_post', 'is_edited', 'created_at')
    list_filter = ('is_first_post', 'is_edited', 'created_at')
    search_fields = ('topic__title', 'author__username', 'content')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    
    def get_topic_title(self, obj):
        return obj.topic.title
    get_topic_title.short_description = '主题'
    get_topic_title.admin_order_field = 'topic__title'


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ('filename', 'file_type', 'file_size', 'download_count', 'created_at')
    list_filter = ('file_type', 'created_at')
    search_fields = ('filename', 'post__topic__title')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'post__topic__title')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name', 'description')
    filter_horizontal = ('topics',)
    ordering = ('name',)


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('reporter', 'post', 'report_type', 'status', 'created_at')
    list_filter = ('report_type', 'status', 'created_at')
    search_fields = ('reporter__username', 'description')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('user__username', 'message')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ('user', 'topic', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'topic__title')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
