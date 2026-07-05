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
    queryset = Content.objects.filter(status='published')
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'summary', 'content', 'author__username']
    ordering_fields = ['created_at', 'updated_at', 'view_count', 'like_count', 'comment_count', 'publish_date']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        if self.action in ['submit', 'create', 'update', 'partial_update', 'destroy', 'my_contents']:
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdminUser()]

    def get_queryset(self):
        user = self.request.user
        queryset = Content.objects.all()

        if not user or not user.is_authenticated:
            # 游客：仅可见已发布内容
            return queryset.filter(status='published')

        # 登录用户默认可见已发布内容 + 自己的全部内容
        queryset = queryset.filter(
            Q(status='published') | Q(author=user)
        ).distinct()

        # 支持按状态筛选（仅筛选自己的内容，避免看到他人未发布内容）
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(
                Q(author=user, status=status_param) | Q(status='published')
            ).distinct()

        return queryset

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

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def submit(self, request, pk=None):
        """用户提交投稿，进入待审核状态"""
        content = self.get_object()
        if content.author != request.user and not request.user.is_staff:
            return Response({'detail': '无权操作'}, status=status.HTTP_403_FORBIDDEN)
        content.status = 'pending'
        content.save()
        return Response({'status': 'pending', 'id': content.id})

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def approve(self, request, pk=None):
        """管理员审核通过"""
        content = self.get_object()
        content.status = 'published'
        content.save()
        return Response({'status': 'published', 'id': content.id})

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def reject(self, request, pk=None):
        """管理员拒绝投稿"""
        content = self.get_object()
        content.status = 'rejected'
        content.save()
        return Response({'status': 'rejected', 'id': content.id})

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        content = self.get_object()
        content.status = 'published'
        content.save()
        return Response({'status': 'published'})

    @action(detail=True, methods=['post'])
    def unpublish(self, request, pk=None):
        content = self.get_object()
        content.status = 'draft'
        content.save()
        return Response({'status': 'draft'})

    @action(detail=True, methods=['get'])
    def revisions(self, request, pk=None):
        content = self.get_object()
        revisions = content.revisions.all()
        serializer = ContentRevisionSerializer(revisions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_contents(self, request):
        queryset = Content.objects.filter(author=request.user)
        status_param = request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
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