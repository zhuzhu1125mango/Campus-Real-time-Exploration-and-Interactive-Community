from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import School, Major, SchoolMajor, SchoolRating, MajorRating, AdmissionScore, Forum, Post, Comment, Tag


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'province', 'city', 'school_type', 'school_level', 'is_verified')
    list_filter = ('school_type', 'school_level', 'province', 'is_verified')
    search_fields = ('name', 'code', 'abbreviation', 'province', 'city')
    fieldsets = (
        (_('基本信息'), {'fields': ('name', 'english_name', 'code', 'abbreviation', 'school_type', 'school_level', 'founded_year')}),
        (_('地理位置'), {'fields': ('province', 'city', 'address', 'location')}),
        (_('联系方式'), {'fields': ('website', 'email', 'phone')}),
        (_('招生信息'), {'fields': ('admission_office_phone', 'admission_office_email', 'has_graduate_program')}),
        (_('描述信息'), {'fields': ('introduction', 'features', 'facilities')}),
        (_('媒体信息'), {'fields': ('logo', 'banner')}),
        (_('统计信息'), {'fields': ('student_count', 'faculty_count')}),
        (_('排名信息'), {'fields': ('national_rank', 'world_rank')}),
        (_('元数据'), {'fields': ('is_verified',)}),
    )


@admin.register(Major)
class MajorAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'degree_type', 'subject_category')
    list_filter = ('degree_type', 'subject_category')
    search_fields = ('name', 'code')
    fieldsets = (
        (_('基本信息'), {'fields': ('name', 'code', 'degree_type', 'subject_category')}),
        (_('描述信息'), {'fields': ('description', 'career_prospects')}),
    )


@admin.register(SchoolMajor)
class SchoolMajorAdmin(admin.ModelAdmin):
    list_display = ('school', 'major', 'is_active')
    list_filter = ('is_active', 'school')
    search_fields = ('school__name', 'major__name')
    fieldsets = (
        (_('关联信息'), {'fields': ('school', 'major')}),
        (_('状态'), {'fields': ('is_active',)}),
    )


@admin.register(SchoolRating)
class SchoolRatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'school', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('user__username', 'school__name', 'comment')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(MajorRating)
class MajorRatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'major', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('user__username', 'major__name', 'comment')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(AdmissionScore)
class AdmissionScoreAdmin(admin.ModelAdmin):
    list_display = ('school', 'major', 'province', 'year', 'score_type', 'min_score')
    list_filter = ('year', 'province', 'score_type', 'school')
    search_fields = ('school__name', 'major__name', 'province')


@admin.register(Forum)
class ForumAdmin(admin.ModelAdmin):
    list_display = ['name', 'school', 'created_at']
    search_fields = ['name', 'school__name']
    list_filter = ['created_at']


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'forum', 'status', 'created_at']
    search_fields = ['title', 'content', 'author__username']
    list_filter = ['status', 'created_at']
    filter_horizontal = ['likes']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['author', 'post', 'created_at']
    search_fields = ['content', 'author__username']
    list_filter = ['created_at']
    filter_horizontal = ['likes']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name', 'description']
    list_filter = ['created_at']
    filter_horizontal = ['posts']