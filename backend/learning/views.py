from rest_framework import viewsets, permissions, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from .models import Course, Category, Chapter, Lesson, Enrollment, Progress, Review, LearningResource
from .serializers import (
    CategorySerializer, CourseSerializer, CourseCreateSerializer, CourseUpdateSerializer,
    ChapterSerializer, ChapterCreateSerializer, ChapterUpdateSerializer,
    LessonSerializer, LessonCreateSerializer, LessonUpdateSerializer,
    EnrollmentSerializer, EnrollmentCreateSerializer,
    ProgressSerializer, ProgressUpdateSerializer,
    ReviewSerializer, ReviewCreateSerializer,
    LearningResourceSerializer, LearningResourceCreateSerializer, LearningResourceUpdateSerializer
)
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAdminUser()]


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.filter(is_published=True)
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'instructor__username']
    ordering_fields = ['created_at', 'enroll_count', 'average_rating', 'price', 'view_count']
    ordering = ['-created_at']

    def get_permissions(self):
        # 课程列表对游客开放；详情及关联内容、报名等操作需登录
        if self.action == 'list':
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 过滤参数
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(categories__id=category)
        
        is_free = self.request.query_params.get('is_free')
        if is_free is not None:
            queryset = queryset.filter(is_free=(is_free.lower() == 'true'))
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CourseCreateSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return CourseUpdateSerializer
        return CourseSerializer
    
    def perform_create(self, serializer):
        # 保存课程并设置讲师为当前用户
        serializer.save(instructor=self.request.user)
    
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        course = self.get_object()
        course.is_published = True
        course.save()
        return Response({'status': 'published'})
    
    @action(detail=True, methods=['post'])
    def unpublish(self, request, pk=None):
        course = self.get_object()
        course.is_published = False
        course.save()
        return Response({'status': 'unpublished'})
    
    @action(detail=True, methods=['get'])
    def chapters(self, request, pk=None):
        course = self.get_object()
        chapters = course.chapters.all()
        serializer = ChapterSerializer(chapters, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def lessons(self, request, pk=None):
        course = self.get_object()
        lessons = Lesson.objects.filter(chapter__course=course)
        serializer = LessonSerializer(lessons, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def resources(self, request, pk=None):
        course = self.get_object()
        resources = course.resources.all()
        serializer = LearningResourceSerializer(resources, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        course = self.get_object()
        reviews = course.reviews.filter(is_approved=True)
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)


class ChapterViewSet(viewsets.ModelViewSet):
    queryset = Chapter.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ChapterCreateSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return ChapterUpdateSerializer
        return ChapterSerializer
    
    @action(detail=True, methods=['get'])
    def lessons(self, request, pk=None):
        chapter = self.get_object()
        lessons = chapter.lessons.all()
        serializer = LessonSerializer(lessons, many=True)
        return Response(serializer.data)


class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return LessonCreateSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return LessonUpdateSerializer
        return LessonSerializer
    
    @action(detail=True, methods=['post'])
    def increment_view(self, request, pk=None):
        lesson = self.get_object()
        lesson.view_count += 1
        lesson.save()
        return Response({'status': 'view_count_incremented'})


class EnrollmentViewSet(viewsets.ModelViewSet):
    queryset = Enrollment.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Enrollment.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create':
            return EnrollmentCreateSerializer
        return EnrollmentSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        course = serializer.validated_data['course']
        user = request.user

        existing = Enrollment.objects.filter(user=user, course=course).first()
        if existing:
            serializer = EnrollmentSerializer(existing, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        # 保存报名并更新课程的报名人数
        enrollment = serializer.save(user=self.request.user)
        course = enrollment.course
        course.enroll_count = course.enrollments.count()
        course.save()

        # 为课程的所有课时创建进度记录
        lessons = Lesson.objects.filter(chapter__course=course)
        for lesson in lessons:
            Progress.objects.get_or_create(
                enrollment=enrollment,
                lesson=lesson,
                defaults={'is_completed': False}
            )
    
    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        enrollment = self.get_object()
        progresses = enrollment.progresses.all()
        serializer = ProgressSerializer(progresses, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        enrollment = self.get_object()
        enrollment.is_completed = True
        enrollment.progress = 100.0
        enrollment.completed_at = timezone.now()
        enrollment.save()
        return Response({'status': 'course_completed'})


class ProgressViewSet(viewsets.ModelViewSet):
    queryset = Progress.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Progress.objects.filter(enrollment__user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'update' or self.action == 'partial_update' or self.action == 'record':
            return ProgressUpdateSerializer
        return ProgressSerializer

    def perform_update(self, serializer):
        # 保存进度并更新报名的总体进度
        progress = serializer.save()
        enrollment = progress.enrollment
        total_lessons = Lesson.objects.filter(chapter__course=enrollment.course).count()
        completed_lessons = enrollment.progresses.filter(is_completed=True).count()
        enrollment.progress = (completed_lessons / total_lessons) * 100 if total_lessons > 0 else 0
        enrollment.save()

    @action(detail=False, methods=['post'])
    def record(self, request):
        """创建或更新课时学习进度"""
        enrollment_id = request.data.get('enrollment')
        lesson_id = request.data.get('lesson')
        if not enrollment_id or not lesson_id:
            return Response({'detail': '缺少 enrollment 或 lesson 参数'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            enrollment = Enrollment.objects.get(id=enrollment_id, user=request.user)
            lesson = Lesson.objects.get(id=lesson_id)
        except Enrollment.DoesNotExist:
            return Response({'detail': '报名记录不存在'}, status=status.HTTP_404_NOT_FOUND)
        except Lesson.DoesNotExist:
            return Response({'detail': '课时不存在'}, status=status.HTTP_404_NOT_FOUND)

        progress, _ = Progress.objects.get_or_create(
            enrollment=enrollment,
            lesson=lesson,
            defaults={'is_completed': False, 'last_position': 0}
        )

        serializer = ProgressUpdateSerializer(progress, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(ProgressSerializer(progress).data)


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ReviewCreateSerializer
        return ReviewSerializer
    
    def perform_create(self, serializer):
        # 保存评价并更新课程的平均评分
        review = serializer.save(user=self.request.user)
        course = review.course
        reviews = course.reviews.filter(is_approved=True)
        total_rating = sum(review.rating for review in reviews)
        course.average_rating = total_rating / reviews.count() if reviews.count() > 0 else 0
        course.save()
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        review = self.get_object()
        review.is_approved = True
        review.save()
        return Response({'status': 'review_approved'})
    
    @action(detail=True, methods=['post'])
    def disapprove(self, request, pk=None):
        review = self.get_object()
        review.is_approved = False
        review.save()
        return Response({'status': 'review_disapproved'})


class LearningResourceViewSet(viewsets.ModelViewSet):
    queryset = LearningResource.objects.all()

    def get_permissions(self):
        # 学习资源列表/详情对游客开放；创建/更新/删除/下载统计需登录
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'create':
            return LearningResourceCreateSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return LearningResourceUpdateSerializer
        return LearningResourceSerializer
    
    @action(detail=True, methods=['post'])
    def increment_download(self, request, pk=None):
        resource = self.get_object()
        resource.download_count += 1
        resource.save()
        return Response({'status': 'download_count_incremented'})