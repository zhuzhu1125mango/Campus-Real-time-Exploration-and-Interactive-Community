from django.db.models import Q
from rest_framework import viewsets, permissions, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import ContentType, Category, Tag, Content, Comment, ContentRevision
from .serializers import (
    ContentTypeSerializer, CategorySerializer, TagSerializer,
    ContentSerializer, ContentCreateSerializer, ContentUpdateSerializer,
    CommentSerializer, CommentCreateSerializer, ContentRevisionSerializer
)
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny


class ContentTypeViewSet(viewsets.ModelViewSet):
    queryset = ContentType.objects.all()
    serializer_class = ContentTypeSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated(), IsAdminUser()]


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]


class ContentViewSet(viewsets.ModelViewSet):
    queryset = Content.objects.all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'summary', 'content', 'author__username']
    ordering_fields = ['created_at', 'updated_at', 'view_count', 'like_count', 'comment_count', 'publish_date']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if user and user.is_authenticated:
            # 登录用户：可见所有已发布内容 + 自己的所有内容
            return Content.objects.filter(
                Q(is_published=True) | Q(author=user)
            ).distinct()
        # 游客：仅可见已发布内容
        return Content.objects.filter(is_published=True)

    def get_serializer_class(self):
        if self.action == 'create':
            return ContentCreateSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return ContentUpdateSerializer
        return ContentSerializer
    
    def perform_create(self, serializer):
        # 保存内容并创建修订历史
        content = serializer.save(author=self.request.user)
        ContentRevision.objects.create(
            content=content,
            author=self.request.user,
            title=content.title,
            content_text=content.content,
            summary=content.summary
        )
    
    def perform_update(self, serializer):
        # 保存内容并创建修订历史
        content = serializer.save()
        ContentRevision.objects.create(
            content=content,
            author=self.request.user,
            title=content.title,
            content_text=content.content,
            summary=content.summary
        )
    
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        content = self.get_object()
        content.is_published = True
        content.save()
        return Response({'status': 'published'})
    
    @action(detail=True, methods=['post'])
    def unpublish(self, request, pk=None):
        content = self.get_object()
        content.is_published = False
        content.save()
        return Response({'status': 'unpublished'})
    
    @action(detail=True, methods=['get'])
    def revisions(self, request, pk=None):
        content = self.get_object()
        revisions = content.revisions.all()
        serializer = ContentRevisionSerializer(revisions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_contents(self, request):
        queryset = Content.objects.filter(author=request.user)
        serializer = ContentSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.filter(is_approved=True)

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'create':
            return CommentCreateSerializer
        return CommentSerializer
    
    def perform_create(self, serializer):
        # 保存评论并更新内容的评论计数
        comment = serializer.save(user=self.request.user)
        content = comment.content
        content.comment_count = content.comments.count()
        content.save()
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        comment = self.get_object()
        comment.is_approved = True
        comment.save()
        return Response({'status': 'approved'})
    
    @action(detail=True, methods=['post'])
    def disapprove(self, request, pk=None):
        comment = self.get_object()
        comment.is_approved = False
        comment.save()
        return Response({'status': 'disapproved'})