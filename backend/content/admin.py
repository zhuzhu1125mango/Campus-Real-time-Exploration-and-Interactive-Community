from django.contrib import admin
from .models import ContentType, Category, Tag, Content, Comment, ContentRevision


@admin.register(ContentType)
class ContentTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'order', 'is_active', 'created_at')
    list_filter = ('parent', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('order', 'name')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)


@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    list_display = ('title', 'content_type', 'category', 'author', 'status', 'is_published', 'publish_date', 'view_count', 'created_at')
    list_filter = ('content_type', 'category', 'status', 'is_published', 'created_at', 'publish_date')
    search_fields = ('title', 'content', 'summary', 'author__username')
    filter_horizontal = ('tags',)
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('content', 'user', 'parent', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('content_text', 'user__username', 'content__title')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)


@admin.register(ContentRevision)
class ContentRevisionAdmin(admin.ModelAdmin):
    list_display = ('content', 'author', 'created_at')
    list_filter = ('created_at', 'author')
    search_fields = ('content__title', 'author__username')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)