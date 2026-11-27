from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet, CourseViewSet, ChapterViewSet, LessonViewSet, EnrollmentViewSet,
    ProgressViewSet, ReviewViewSet, LearningResourceViewSet, PaymentOrderViewSet,
    CertificateViewSet, StudyReminderViewSet,
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'courses', CourseViewSet)
router.register(r'chapters', ChapterViewSet)
router.register(r'lessons', LessonViewSet)
router.register(r'enrollments', EnrollmentViewSet)
router.register(r'progresses', ProgressViewSet)
router.register(r'reviews', ReviewViewSet)
router.register(r'resources', LearningResourceViewSet)
router.register(r'orders', PaymentOrderViewSet)
router.register(r'certificates', CertificateViewSet)
router.register(r'reminders', StudyReminderViewSet)

urlpatterns = [
    path('', include(router.urls)),
]