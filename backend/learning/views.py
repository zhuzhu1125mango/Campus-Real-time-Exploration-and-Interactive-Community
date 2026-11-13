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
from users.permissions import IsOwnerOrAdmin, IsInstructorOrAdmin, IsCourseInstructorOrAdmin
from users.throttles import SearchThrottle, WriteThrottle
from users.tasks import queue_update_user_points
from search.services import SearchService
from rest_framework.exceptions import PermissionDenied
from django.db import transaction
from django.db.utils import IntegrityError
from django.db.models import Q, F, Avg
from core.base_viewsets import (
    BaseModelViewSet,
    PublicReadOnlyModelViewSet,
    AuthenticatedModelViewSet,
)


class CategoryViewSet(PublicReadOnlyModelViewSet):
    """课程分类视图集"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_config = {
        'list': [AllowAny],
        'retrieve': [AllowAny],
        'create': [IsAdminUser],
        'update': [IsAdminUser],
        'partial_update': [IsAdminUser],
        'destroy': [IsAdminUser],
    }


class CourseViewSet(BaseModelViewSet):
    """课程视图集"""
    queryset = Course.objects.filter(is_published=True)
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'enroll_count', 'average_rating', 'price', 'view_count']
    ordering = ['-created_at']
    permission_config = {
        'list': [AllowAny],
        'retrieve': [AllowAny],
        'chapters': [AllowAny],
        'lessons': [AllowAny],
        'resources': [AllowAny],
        'reviews': [AllowAny],
        'create': [IsAuthenticated],
        'update': [IsAuthenticated, IsInstructorOrAdmin],
        'partial_update': [IsAuthenticated, IsInstructorOrAdmin],
        'destroy': [IsAuthenticated, IsInstructorOrAdmin],
        'publish': [IsAuthenticated, IsInstructorOrAdmin],
        'unpublish': [IsAuthenticated, IsInstructorOrAdmin],
    }
    throttle_config = {
        'list': [SearchThrottle],
        'retrieve': [SearchThrottle],
        'chapters': [SearchThrottle],
        'lessons': [SearchThrottle],
        'resources': [SearchThrottle],
        'reviews': [SearchThrottle],
        'create': [WriteThrottle],
        'update': [WriteThrottle],
        'partial_update': [WriteThrottle],
        'destroy': [WriteThrottle],
        'publish': [WriteThrottle],
        'unpublish': [WriteThrottle],
    }

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 过滤参数
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(categories__id=category)
        
        is_free = self.request.query_params.get('is_free')
        if is_free is not None:
            queryset = queryset.filter(is_free=(is_free.lower() == 'true'))

        search = self.request.query_params.get('search')
        if search:
            service = SearchService()
            es_ids = list(service.search_courses(search, limit=200).values_list('pk', flat=True))
            if es_ids:
                queryset = queryset.filter(pk__in=es_ids)
            else:
                queryset = queryset.filter(
                    Q(title__icontains=search) |
                    Q(description__icontains=search) |
                    Q(instructor__username__icontains=search)
                )

        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return CourseCreateSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return CourseUpdateSerializer
        return CourseSerializer
    
    def perform_create(self, serializer):
        # 保存课程并设置讲师为当前用户
        course = serializer.save(instructor=self.request.user)

        # 异步发放创建课程积分
        queue_update_user_points(
            self.request.user.id,
            'create_course',
            description=f'创建课程 {course.title}'
        )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsInstructorOrAdmin])
    def publish(self, request, pk=None):
        """讲师或管理员发布课程"""
        course = self.get_object()
        course.is_published = True
        course.save()
        return Response({'status': 'published'})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsInstructorOrAdmin])
    def unpublish(self, request, pk=None):
        """讲师或管理员下架课程"""
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


class ChapterViewSet(BaseModelViewSet):
    """课程章节视图集"""
    queryset = Chapter.objects.all()
    permission_config = {
        'list': [AllowAny],
        'retrieve': [AllowAny],
        'lessons': [AllowAny],
        'create': [IsAuthenticated, IsCourseInstructorOrAdmin],
        'update': [IsAuthenticated, IsCourseInstructorOrAdmin],
        'partial_update': [IsAuthenticated, IsCourseInstructorOrAdmin],
        'destroy': [IsAuthenticated, IsCourseInstructorOrAdmin],
    }

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        if user.is_authenticated and (user.is_staff or Course.objects.filter(instructor=user).exists()):
            return queryset
        return queryset.filter(course__is_published=True)

    def get_serializer_class(self):
        if self.action == 'create':
            return ChapterCreateSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return ChapterUpdateSerializer
        return ChapterSerializer

    def perform_create(self, serializer):
        course = serializer.validated_data.get('course')
        if course and course.instructor != self.request.user and not self.request.user.is_staff:
            raise PermissionDenied("您没有权限为此课程添加章节")
        serializer.save()

    @action(detail=True, methods=['get'])
    def lessons(self, request, pk=None):
        chapter = self.get_object()
        lessons = chapter.lessons.all()
        serializer = LessonSerializer(lessons, many=True)
        return Response(serializer.data)


class LessonViewSet(BaseModelViewSet):
    """课程课时视图集"""
    queryset = Lesson.objects.all()
    permission_config = {
        'list': [AllowAny],
        'retrieve': [AllowAny],
        'increment_view': [AllowAny],
        'create': [IsAuthenticated, IsCourseInstructorOrAdmin],
        'update': [IsAuthenticated, IsCourseInstructorOrAdmin],
        'partial_update': [IsAuthenticated, IsCourseInstructorOrAdmin],
        'destroy': [IsAuthenticated, IsCourseInstructorOrAdmin],
    }

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        if user.is_authenticated and (user.is_staff or Course.objects.filter(instructor=user).exists()):
            return queryset
        return queryset.filter(chapter__course__is_published=True)

    def get_serializer_class(self):
        if self.action == 'create':
            return LessonCreateSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return LessonUpdateSerializer
        return LessonSerializer

    def perform_create(self, serializer):
        chapter = serializer.validated_data.get('chapter')
        course = chapter.course if chapter else None
        if course and course.instructor != self.request.user and not self.request.user.is_staff:
            raise PermissionDenied("您没有权限为此课程添加课时")
        serializer.save()

    @action(detail=True, methods=['post'])
    def increment_view(self, request, pk=None):
        lesson = self.get_object()
        # 使用 F() 表达式原子更新浏览次数，避免并发覆盖
        Lesson.objects.filter(pk=lesson.pk).update(view_count=F('view_count') + 1)
        return Response({'status': 'view_count_incremented'})


class EnrollmentViewSet(AuthenticatedModelViewSet):
    """课程报名视图集"""
    queryset = Enrollment.objects.all()
    throttle_config = {
        'list': [SearchThrottle],
        'retrieve': [SearchThrottle],
        'create': [WriteThrottle],
        'complete': [WriteThrottle],
    }

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

        with transaction.atomic():
            # 锁定课程行，并检查是否已报名，防止并发重复报名
            course = Course.objects.select_for_update().get(pk=course.pk)
            existing = Enrollment.objects.filter(user=user, course=course).first()
            if existing:
                serializer = EnrollmentSerializer(existing, context={'request': request})
                return Response(serializer.data, status=status.HTTP_200_OK)

            try:
                self.perform_create(serializer, course=course)
            except IntegrityError:
                # 唯一约束冲突时返回已存在的报名记录
                existing = Enrollment.objects.get(user=user, course=course)
                serializer = EnrollmentSerializer(existing, context={'request': request})
                return Response(serializer.data, status=status.HTTP_200_OK)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer, course=None):
        # 保存报名并更新课程的报名人数
        enrollment = serializer.save(user=self.request.user)
        if course is None:
            course = enrollment.course
        # 使用 F() 表达式原子更新报名人数，避免并发覆盖
        Course.objects.filter(pk=course.pk).update(enroll_count=F('enroll_count') + 1)

        # 为课程的所有课时创建进度记录
        lessons = Lesson.objects.filter(chapter__course=course)
        for lesson in lessons:
            Progress.objects.get_or_create(
                enrollment=enrollment,
                lesson=lesson,
                defaults={'is_completed': False}
            )

        # 异步发放报名课程积分
        queue_update_user_points(
            self.request.user.id,
            'favorite',
            description=f'报名课程 {course.title}'
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
        was_completed = enrollment.is_completed
        enrollment.is_completed = True
        enrollment.progress = 100.0
        enrollment.completed_at = timezone.now()
        enrollment.save()

        # 仅在首次完成时发放完成课程积分
        if not was_completed:
            queue_update_user_points(
                request.user.id,
                'complete_course',
                description=f'完成课程 {enrollment.course.title}'
            )

        return Response({'status': 'course_completed'})


class ProgressViewSet(AuthenticatedModelViewSet):
    """学习进度视图集"""
    queryset = Progress.objects.all()
    throttle_config = {
        'list': [SearchThrottle],
        'retrieve': [SearchThrottle],
        'create': [WriteThrottle],
        'update': [WriteThrottle],
        'partial_update': [WriteThrottle],
        'record': [WriteThrottle],
    }

    def get_queryset(self):
        return Progress.objects.filter(enrollment__user=self.request.user)

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update', 'record']:
            return ProgressUpdateSerializer
        return ProgressSerializer

    def perform_update(self, serializer):
        # 保存进度并更新报名的总体进度
        progress = serializer.save()
        enrollment = progress.enrollment
        with transaction.atomic():
            # 锁定报名行，防止并发进度更新覆盖
            enrollment = Enrollment.objects.select_for_update().get(pk=enrollment.pk)
            total_lessons = Lesson.objects.filter(chapter__course=enrollment.course).count()
            completed_lessons = Progress.objects.filter(enrollment=enrollment, is_completed=True).count()
            enrollment.progress = (completed_lessons / total_lessons) * 100 if total_lessons > 0 else 0
            enrollment.save(update_fields=['progress'])

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


class ReviewViewSet(BaseModelViewSet):
    """课程评价视图集"""
    queryset = Review.objects.all()
    permission_config = {
        'list': [AllowAny],
        'retrieve': [AllowAny],
        'create': [IsAuthenticated],
        'update': [IsAuthenticated, IsOwnerOrAdmin],
        'partial_update': [IsAuthenticated, IsOwnerOrAdmin],
        'destroy': [IsAuthenticated, IsOwnerOrAdmin],
        'approve': [IsAuthenticated, IsAdminUser],
        'disapprove': [IsAuthenticated, IsAdminUser],
    }
    throttle_config = {
        'list': [SearchThrottle],
        'retrieve': [SearchThrottle],
        'create': [WriteThrottle],
        'update': [WriteThrottle],
        'partial_update': [WriteThrottle],
        'destroy': [WriteThrottle],
    }

    def get_serializer_class(self):
        if self.action == 'create':
            return ReviewCreateSerializer
        return ReviewSerializer

    def _update_course_rating(self, course):
        """使用聚合计算课程平均评分，避免并发下的统计错误"""
        result = course.reviews.filter(is_approved=True).aggregate(avg_rating=Avg('rating'))
        course.average_rating = result['avg_rating'] or 0.0
        course.save(update_fields=['average_rating'])

    def perform_create(self, serializer):
        # 保存评价并更新课程的平均评分
        review = serializer.save(user=self.request.user)
        self._update_course_rating(review.course)

        # 异步发放课程评价积分
        queue_update_user_points(
            self.request.user.id,
            'comment',
            description=f'评价课程 {review.course.title}'
        )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdminUser])
    def approve(self, request, pk=None):
        """管理员审核通过课程评价"""
        review = self.get_object()
        review.is_approved = True
        review.save()
        self._update_course_rating(review.course)
        return Response({'status': 'review_approved'})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdminUser])
    def disapprove(self, request, pk=None):
        """管理员审核拒绝课程评价"""
        review = self.get_object()
        review.is_approved = False
        review.save()
        self._update_course_rating(review.course)
        return Response({'status': 'review_disapproved'})


class LearningResourceViewSet(BaseModelViewSet):
    """学习资源视图集"""
    queryset = LearningResource.objects.all()
    permission_config = {
        'list': [AllowAny],
        'retrieve': [AllowAny],
        'increment_download': [AllowAny],
        'create': [IsAuthenticated, IsCourseInstructorOrAdmin],
        'update': [IsAuthenticated, IsCourseInstructorOrAdmin],
        'partial_update': [IsAuthenticated, IsCourseInstructorOrAdmin],
        'destroy': [IsAuthenticated, IsCourseInstructorOrAdmin],
    }
    throttle_config = {
        'list': [SearchThrottle],
        'retrieve': [SearchThrottle],
        'create': [WriteThrottle],
        'update': [WriteThrottle],
        'partial_update': [WriteThrottle],
        'destroy': [WriteThrottle],
    }

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        if user.is_authenticated and (user.is_staff or Course.objects.filter(instructor=user).exists()):
            return queryset
        return queryset.filter(course__is_published=True)

    def get_serializer_class(self):
        if self.action == 'create':
            return LearningResourceCreateSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return LearningResourceUpdateSerializer
        return LearningResourceSerializer

    def perform_create(self, serializer):
        course = serializer.validated_data.get('course')
        if course and course.instructor != self.request.user and not self.request.user.is_staff:
            raise PermissionDenied("您没有权限为此课程添加学习资源")
        serializer.save()

    @action(detail=True, methods=['post'])
    def increment_download(self, request, pk=None):
        resource = self.get_object()
        # 使用 F() 表达式原子更新下载次数，避免并发覆盖
        LearningResource.objects.filter(pk=resource.pk).update(download_count=F('download_count') + 1)
        return Response({'status': 'download_count_incremented'})
