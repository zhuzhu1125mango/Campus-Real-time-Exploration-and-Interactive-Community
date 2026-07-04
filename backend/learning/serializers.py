from rest_framework import serializers
from .models import Course, Category, CourseCategory, Chapter, Lesson, Enrollment, Progress, Review, LearningResource
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


class LessonUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ['title', 'description', 'content', 'video_url', 'duration', 'is_free', 'order']


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
        fields = ['id', 'enrollment', 'lesson', 'is_completed', 'last_watched_at', 'watched_duration']


class ProgressUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Progress
        fields = ['is_completed', 'last_watched_at', 'watched_duration']


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