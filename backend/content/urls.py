from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ContentTypeViewSet, CategoryViewSet, TagViewSet, ContentViewSet,
    CommentViewSet, ContentReportViewSet, ContentImageUploadView,
)

router = DefaultRouter()
router.register(r'content-types', ContentTypeViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'tags', TagViewSet)
router.register(r'contents', ContentViewSet)
router.register(r'comments', CommentViewSet)
router.register(r'reports', ContentReportViewSet, basename='content-report')

urlpatterns = [
    path('images/', ContentImageUploadView.as_view(), name='content-image-upload'),
    path('', include(router.urls)),
]
