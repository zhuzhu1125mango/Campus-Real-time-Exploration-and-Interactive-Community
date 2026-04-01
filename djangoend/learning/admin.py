from django.contrib import admin
from .models import Course, Category, CourseCategory, Chapter, Lesson, Enrollment, Progress, Review, LearningResource


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'instructor', 'is_free', 'price', 'is_published', 'publish_date', 'enroll_count', 'view_count', 'average_rating', 'created_at')
    list_filter = ('is_free', 'is_published', 'publish_date', 'created_at')
    search_fields = ('title', 'description', 'instructor__username')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'order', 'is_active', 'created_at')
    list_filter = ('parent', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('order', 'name')


@admin.register(CourseCategory)
class CourseCategoryAdmin(admin.ModelAdmin):
    list_display = ('course', 'category', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('course__title', 'category__name')
    ordering = ('-created_at',)


@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order', 'created_at')
    list_filter = ('course', 'created_at')
    search_fields = ('title', 'description', 'course__title')
    ordering = ('course', 'order')


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'chapter', 'order', 'is_free', 'view_count', 'created_at')
    list_filter = ('chapter__course', 'is_free', 'created_at')
    search_fields = ('title', 'description', 'chapter__title', 'chapter__course__title')
    ordering = ('chapter', 'order')


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'is_completed', 'progress', 'enrolled_at', 'completed_at')
    list_filter = ('is_completed', 'enrolled_at', 'completed_at')
    search_fields = ('user__username', 'course__title')
    date_hierarchy = 'enrolled_at'
    ordering = ('-enrolled_at',)


@admin.register(Progress)
class ProgressAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'lesson', 'is_completed', 'last_watched_at')
    list_filter = ('is_completed', 'last_watched_at')
    search_fields = ('enrollment__user__username', 'lesson__title')
    ordering = ('-last_watched_at',)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'rating', 'is_approved', 'created_at')
    list_filter = ('rating', 'is_approved', 'created_at')
    search_fields = ('user__username', 'course__title', 'comment')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)


@admin.register(LearningResource)
class LearningResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'file_type', 'file_size', 'download_count', 'is_free', 'created_at')
    list_filter = ('course', 'file_type', 'is_free', 'created_at')
    search_fields = ('title', 'description', 'course__title')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)