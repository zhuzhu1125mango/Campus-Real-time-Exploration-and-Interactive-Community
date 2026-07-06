from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import (
    School, Major, SchoolMajor, SchoolRating, MajorRating, AdmissionScore,
    Event, EventRegistration, Place, CheckIn
)


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'province', 'city', 'school_type', 'school_level')
    list_filter = ('school_type', 'school_level', 'province')
    search_fields = ('name', 'code', 'abbreviation', 'province', 'city')
    fieldsets = (
        (_('基本信息'), {'fields': ('name', 'english_name', 'code', 'abbreviation', 'school_type', 'school_level', 'founded_year')}),
        (_('地理位置'), {'fields': ('province', 'city', 'address')}),
        (_('联系方式'), {'fields': ('website',)}),
        (_('描述信息'), {'fields': ('description',)}),
        (_('统计信息'), {'fields': ('student_count', 'faculty_count', 'campus_area')}),
        (_('排名信息'), {'fields': ('national_rank',)}),
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


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'school', 'start_time', 'end_time', 'status', 'is_public')
    list_filter = ('status', 'is_public', 'school')
    search_fields = ('title', 'school__name', 'location')


@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ('event', 'user', 'status', 'registered_at')
    list_filter = ('status',)
    search_fields = ('event__title', 'user__username')


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = ('name', 'school', 'category', 'latitude', 'longitude', 'checkin_count', 'is_active')
    list_filter = ('category', 'is_active', 'school')
    search_fields = ('name', 'school__name', 'address')


@admin.register(CheckIn)
class CheckInAdmin(admin.ModelAdmin):
    list_display = ('user', 'place', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'place__name')
    readonly_fields = ('created_at',)


