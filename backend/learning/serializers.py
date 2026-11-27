from rest_framework import serializers
from datetime import time

from .models import (
    Course, Category, CourseCategory, Chapter, Lesson, Enrollment, Progress,
    Review, LearningResource, PaymentOrder, Certificate, StudyReminder,
)
from users.serializers import UserSerializer


class CategorySerializer(serializers.ModelSerializer):
    parent = serializers.CharField(source='parent.name', allow_null=True, required=False)
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'parent', 'description', 'order', 'is_active', 'created_at', 'updated_at']


class CourseSerializer(serializers.ModelSerializer):
    instructor = UserSerializer()
    categories = CategorySerializer(many=True, source='categories.all')
    cover_image = serializers.SerializerMethodField()
    chapter_count = serializers.SerializerMethodField()
    lesson_count = serializers.SerializerMethodField()
    is_enrolled = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'description', 'instructor', 'categories',
            'cover_image', 'price', 'is_free', 'is_published', 'publish_date',
            'enroll_count', 'view_count', 'average_rating', 'chapter_count',
            'lesson_count', 'is_enrolled', 'created_at', 'updated_at'
        ]

    def get_cover_image(self, obj):
        if obj.cover_image:
            return obj.cover_image.url
        return None

    def get_chapter_count(self, obj):
        return obj.chapters.count()

    def get_lesson_count(self, obj):
        return Lesson.objects.filter(chapter__course=obj).count()

    def get_is_enrolled(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.enrollments.filter(user=request.user).exists()


class CourseCreateSerializer(serializers.ModelSerializer):
    categories = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), many=True, required=False)
    
    class Meta:
        model = Course
        fields = [
            'title', 'slug', 'description', 'instructor', 'categories',
            'cover_image', 'price', 'is_free', 'is_published'
        ]
    
    def create(self, validated_data):
        categories = validated_data.pop('categories', [])
        course = super().create(validated_data)
        for category in categories:
            CourseCategory.objects.create(course=course, category=category)
        return course


class CourseUpdateSerializer(serializers.ModelSerializer):
    categories = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), many=True, required=False)
    
    class Meta:
        model = Course
        fields = [
            'title', 'slug', 'description', 'instructor', 'categories',
            'cover_image', 'price', 'is_free', 'is_published'
        ]
    
    def update(self, instance, validated_data):
        categories = validated_data.pop('categories', None)
        instance = super().update(instance, validated_data)
        if categories is not None:
            # 清除现有的分类关联
            instance.categories.clear()
            # 添加新的分类关联
            for category in categories:
                CourseCategory.objects.create(course=instance, category=category)
        return instance


class LessonSerializer(serializers.ModelSerializer):
    chapter = serializers.CharField(source='chapter.title')
    chapter_id = serializers.IntegerField(source='chapter.id', read_only=True)
    course = serializers.CharField(source='chapter.course.title')

    class Meta:
        model = Lesson
        fields = [
            'id', 'course', 'chapter', 'chapter_id', 'title', 'description', 'content',
            'video_url', 'duration', 'is_free', 'order', 'view_count',
            'created_at', 'updated_at'
        ]


class LessonCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ['chapter', 'title', 'description', 'content', 'video_url', 'duration', 'is_free', 'order']


class LessonUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ['title', 'description', 'content', 'video_url', 'duration', 'is_free', 'order']


class ChapterSerializer(serializers.ModelSerializer):
    course = serializers.CharField(source='course.title')
    lesson_count = serializers.SerializerMethodField()
    lessons = LessonSerializer(many=True, source='lessons.all', read_only=True)

    class Meta:
        model = Chapter
        fields = ['id', 'course', 'title', 'description', 'order', 'lesson_count', 'lessons', 'created_at', 'updated_at']

    def get_lesson_count(self, obj):
        return obj.lessons.count()


class ChapterCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chapter
        fields = ['course', 'title', 'description', 'order']


class ChapterUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chapter
        fields = ['title', 'description', 'order']


class EnrollmentSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    course = CourseSerializer()
    
    class Meta:
        model = Enrollment
        fields = ['id', 'user', 'course', 'is_completed', 'progress', 'enrolled_at', 'completed_at']


class EnrollmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = ['course']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class ProgressSerializer(serializers.ModelSerializer):
    enrollment = serializers.CharField(source='enrollment.id')
    lesson = LessonSerializer()

    class Meta:
        model = Progress
        fields = ['id', 'enrollment', 'lesson', 'is_completed', 'last_watched_at', 'watched_duration', 'last_position']


class ProgressUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Progress
        fields = ['is_completed', 'last_watched_at', 'watched_duration', 'last_position']


class ReviewSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    course = serializers.CharField(source='course.title')
    
    class Meta:
        model = Review
        fields = ['id', 'user', 'course', 'rating', 'comment', 'is_approved', 'created_at', 'updated_at']


class ReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['course', 'rating', 'comment']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class LearningResourceSerializer(serializers.ModelSerializer):
    course = serializers.CharField(source='course.title')
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = LearningResource
        fields = [
            'id', 'course', 'title', 'description', 'file_url', 'file_type',
            'file_size', 'download_count', 'is_free', 'created_at', 'updated_at'
        ]
    
    def get_file_url(self, obj):
        if obj.file:
            return obj.file.url
        return None


class LearningResourceCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningResource
        fields = ['course', 'title', 'description', 'file', 'file_type', 'file_size', 'is_free']


class LearningResourceUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningResource
        fields = ['title', 'description', 'file', 'file_type', 'file_size', 'is_free']


class PaymentOrderSerializer(serializers.ModelSerializer):
    course_id = serializers.IntegerField(source='course.id', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)
    course_cover = serializers.SerializerMethodField()

    class Meta:
        model = PaymentOrder
        fields = [
            'id', 'order_no', 'amount', 'status', 'payment_method',
            'course_id', 'course_title', 'course_cover',
            'created_at', 'paid_at',
        ]

    def get_course_cover(self, obj):
        if obj.course.cover_image:
            return obj.course.cover_image.url
        return None


class PaymentOrderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentOrder
        fields = ['course', 'payment_method']


class CertificateSerializer(serializers.ModelSerializer):
    course_id = serializers.IntegerField(source='enrollment.course.id', read_only=True)
    course_title = serializers.CharField(source='enrollment.course.title', read_only=True)
    course_cover = serializers.SerializerMethodField()
    instructor_name = serializers.CharField(source='enrollment.course.instructor.username', read_only=True)
    username = serializers.CharField(source='enrollment.user.username', read_only=True)
    enrollment_id = serializers.IntegerField(source='enrollment.id', read_only=True)

    class Meta:
        model = Certificate
        fields = [
            'id', 'number', 'status', 'issued_at', 'revoked_at', 'remark',
            'enrollment_id', 'username', 'course_id', 'course_title',
            'course_cover', 'instructor_name',
        ]

    def get_course_cover(self, obj):
        if obj.enrollment.course.cover_image:
            return obj.enrollment.course.cover_image.url
        return None


class StudyReminderSerializer(serializers.ModelSerializer):
    course = serializers.PrimaryKeyRelatedField(queryset=Course.objects.filter(is_published=True))
    course_id = serializers.IntegerField(source='course.id', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)
    course_cover = serializers.SerializerMethodField()
    remind_time = serializers.TimeField(format='%H:%M', default=time(20, 0))
    is_active = serializers.BooleanField(default=True)
    progress = serializers.SerializerMethodField()
    is_completed = serializers.SerializerMethodField()

    class Meta:
        model = StudyReminder
        fields = [
            'id', 'course', 'course_id', 'course_title', 'course_cover',
            'is_active', 'remind_time', 'progress', 'is_completed',
            'last_reminded_at', 'created_at', 'updated_at',
        ]
        read_only_fields = ['last_reminded_at', 'created_at', 'updated_at']

    def get_course_cover(self, obj):
        if obj.course.cover_image:
            return obj.course.cover_image.url
        return None

    def _enrollment(self, obj):
        if not hasattr(obj, '_enrollment_cache'):
            obj._enrollment_cache = Enrollment.objects.filter(
                user_id=obj.user_id, course_id=obj.course_id
            ).only('progress', 'is_completed').first()
        return obj._enrollment_cache

    def get_progress(self, obj):
        enrollment = self._enrollment(obj)
        return round(enrollment.progress, 1) if enrollment else 0

    def get_is_completed(self, obj):
        enrollment = self._enrollment(obj)
        return bool(enrollment and enrollment.is_completed)