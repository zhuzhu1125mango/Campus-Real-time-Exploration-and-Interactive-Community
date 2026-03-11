from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User, UserProfile, VerificationCode
from .favorites import Favorite
from .notifications import Notification


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = '用户资料'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('个人信息'), {'fields': ('first_name', 'last_name', 'email', 'phone', 'avatar', 'bio')}),
        (_('学生信息'), {'fields': ('is_student', 'grade', 'major', 'school')}),
        (_('状态'), {'fields': ('is_verified',)}),
        (_('权限'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('重要日期'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'phone', 'password1', 'password2'),
        }),
    )
    list_display = ('username', 'email', 'phone', 'is_student', 'is_verified', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'is_student', 'is_verified')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'phone')
    ordering = ('username',)
    inlines = (UserProfileInline,)


@admin.register(VerificationCode)
class VerificationCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'email', 'phone', 'code_type', 'is_used', 'created_at', 'expires_at')
    list_filter = ('code_type', 'is_used')
    search_fields = ('code', 'email', 'phone')
    ordering = ('-created_at',)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'content_type', 'object_id', 'category', 'created_at')
    list_filter = ('content_type', 'category')
    search_fields = ('user__username', 'category', 'note')
    ordering = ('-created_at',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'sender', 'notification_type', 'title', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read')
    search_fields = ('recipient__username', 'sender__username', 'title', 'content')
    ordering = ('-created_at',)