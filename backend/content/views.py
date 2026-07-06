from django.db.models import Q, F, Count, Exists, OuterRef
from rest_framework import viewsets, permissions, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from .models import ContentType, Category, Tag, Content, Comment, ContentRevision
from .serializers import (
    ContentTypeSerializer, CategorySerializer, TagSerializer,
    ContentSerializer, ContentCreateSerializer, ContentUpdateSerializer,
    CommentSerializer, CommentCreateSerializer, ContentRevisionSerializer
)
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from users.permissions import IsOwnerOrAdmin
from users.throttles import SearchThrottle, WriteThrottle


class StandardResultsSetPagination(PageNumberPagination):
    """标准分页类"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


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
        return [IsAuthenticated(), IsAdminUser()]


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated(), IsAdminUser()]


class ContentViewSet(viewsets.ModelViewSet):
    queryset = Content.objects.filter(status='published')
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'summary', 'content', 'author__username']
    ordering_fields = ['created_at', 'updated_at', 'view_count', 'like_count', 'comment_count', 'publish_date']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        if self.action in ['submit', 'create', 'update', 'partial_update', 'destroy', 'my_contents']:
            return [IsAuthenticated(), IsOwnerOrAdmin()]
        return [IsAuthenticated(), IsAdminUser()]

    def get_throttles(self):
        if self.action in ['list', 'retrieve']:
            return [SearchThrottle()]
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'submit']:
            return [WriteThrottle()]
        return super().get_throttles()

    def get_queryset(self):
        user = self.request.user
        # 预取内容类型、分类、作者、标签，减少 N+1 查询
        queryset = Content.objects.select_related(
            'content_type', 'category', 'author'
        ).prefetch_related('tags')

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

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdminUser])
    def publish(self, request, pk=None):
        """管理员发布内容"""
        content = self.get_object()
        content.status = 'published'
        content.save()
        return Response({'status': 'published'})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdminUser])
    def unpublish(self, request, pk=None):
        """管理员下架内容"""
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
        queryset = Content.objects.filter(author=request.user).select_related(
            'content_type', 'category', 'author'
        ).prefetch_related('tags')
        status_param = request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        page = self.paginate_queryset(queryset)
        serializer = ContentSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.filter(is_approved=True)
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsOwnerOrAdmin()]
        if self.action in ['approve', 'disapprove']:
            return [IsAuthenticated(), IsAdminUser()]
        return [IsAuthenticated()]

    def get_throttles(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [WriteThrottle()]
        return super().get_throttles()

    def get_serializer_class(self):
        if self.action == 'create':
            return CommentCreateSerializer
        return CommentSerializer

    def get_queryset(self):
        # 预取内容、用户、父评论，减少 N+1 查询
        queryset = Comment.objects.filter(is_approved=True).select_related(
            'content', 'user', 'parent'
        )
        content_id = self.request.query_params.get('content')
        if content_id:
            queryset = queryset.filter(content_id=content_id)
        return queryset
    
    def perform_create(self, serializer):
        # 保存评论并使用 F() 表达式原子更新内容的评论计数
        comment = serializer.save(user=self.request.user)
        Content.objects.filter(pk=comment.content_id).update(comment_count=F('comment_count') + 1)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdminUser])
    def approve(self, request, pk=None):
        """管理员审核通过评论"""
        comment = self.get_object()
        if not comment.is_approved:
            comment.is_approved = True
            comment.save()
            Content.objects.filter(pk=comment.content_id).update(comment_count=F('comment_count') + 1)
        return Response({'status': 'approved'})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdminUser])
    def disapprove(self, request, pk=None):
        """管理员审核拒绝评论"""
        comment = self.get_object()
        if comment.is_approved:
            comment.is_approved = False
            comment.save()
            Content.objects.filter(pk=comment.content_id).update(comment_count=F('comment_count') - 1)
        return Response({'status': 'disapproved'})