from django.db.models import Q, F
from rest_framework import status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import ContentType, Category, Tag, Content, Comment, ContentRevision
from .serializers import (
    ContentTypeSerializer, CategorySerializer, TagSerializer,
    ContentSerializer, ContentCreateSerializer, ContentUpdateSerializer,
    CommentSerializer, CommentCreateSerializer, ContentRevisionSerializer
)
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from users.permissions import IsOwnerOrAdmin
from users.throttles import SearchThrottle, WriteThrottle
from users.tasks import queue_update_user_points
from notifications.notification_sender import notify_forum_event
from search.services import SearchService
from core.base_viewsets import (
    PublicReadOnlyModelViewSet,
    BaseModelViewSet,
)


class ContentTypeViewSet(PublicReadOnlyModelViewSet):
    """内容类型视图集"""
    queryset = ContentType.objects.all()
    serializer_class = ContentTypeSerializer
    permission_config = {
        'list': [AllowAny],
        'retrieve': [AllowAny],
        'create': [IsAuthenticated, IsAdminUser],
        'update': [IsAuthenticated, IsAdminUser],
        'partial_update': [IsAuthenticated, IsAdminUser],
        'destroy': [IsAuthenticated, IsAdminUser],
    }


class CategoryViewSet(PublicReadOnlyModelViewSet):
    """内容分类视图集"""
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_config = {
        'list': [AllowAny],
        'retrieve': [AllowAny],
        'create': [IsAuthenticated, IsAdminUser],
        'update': [IsAuthenticated, IsAdminUser],
        'partial_update': [IsAuthenticated, IsAdminUser],
        'destroy': [IsAuthenticated, IsAdminUser],
    }


class TagViewSet(PublicReadOnlyModelViewSet):
    """内容标签视图集"""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_config = {
        'list': [AllowAny],
        'retrieve': [AllowAny],
        'create': [IsAuthenticated, IsAdminUser],
        'update': [IsAuthenticated, IsAdminUser],
        'partial_update': [IsAuthenticated, IsAdminUser],
        'destroy': [IsAuthenticated, IsAdminUser],
    }


class ContentViewSet(BaseModelViewSet):
    """内容视图集"""
    queryset = Content.objects.filter(status='published')
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'updated_at', 'view_count', 'like_count', 'comment_count', 'publish_date']
    ordering = ['-created_at']
    select_related_fields = ['content_type', 'category', 'author']
    prefetch_related_fields = ['tags']
    permission_config = {
        'list': [AllowAny],
        'retrieve': [AllowAny],
        'submit': [IsAuthenticated, IsOwnerOrAdmin],
        'create': [IsAuthenticated, IsOwnerOrAdmin],
        'update': [IsAuthenticated, IsOwnerOrAdmin],
        'partial_update': [IsAuthenticated, IsOwnerOrAdmin],
        'destroy': [IsAuthenticated, IsOwnerOrAdmin],
        'my_contents': [IsAuthenticated, IsOwnerOrAdmin],
        'approve': [IsAuthenticated, IsAdminUser],
        'reject': [IsAuthenticated, IsAdminUser],
        'publish': [IsAuthenticated, IsAdminUser],
        'unpublish': [IsAuthenticated, IsAdminUser],
    }
    throttle_config = {
        'list': [SearchThrottle],
        'retrieve': [SearchThrottle],
        'create': [WriteThrottle],
        'update': [WriteThrottle],
        'partial_update': [WriteThrottle],
        'destroy': [WriteThrottle],
        'submit': [WriteThrottle],
    }

    def get_queryset(self):
        user = self.request.user
        # 预取与 select_related 由基类统一处理；子类追加业务过滤
        queryset = super().get_queryset()

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

        search = self.request.query_params.get('search')
        if search:
            service = SearchService()
            es_ids = list(service.search_contents(search, limit=200).values_list('pk', flat=True))
            if es_ids:
                queryset = queryset.filter(pk__in=es_ids)
            else:
                queryset = queryset.filter(
                    Q(title__icontains=search) |
                    Q(summary__icontains=search) |
                    Q(content__icontains=search) |
                    Q(author__username__icontains=search)
                )

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

        # 异步发放内容发布积分
        queue_update_user_points(
            self.request.user.id,
            'post',
            description='发布内容'
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


def _notify_content_comment(comment):
    """内容被评论时通知内容作者。"""
    content_author = comment.content.author
    if content_author and content_author != comment.user:
        notify_forum_event(
            recipient=content_author,
            sender=comment.user,
            forum_type='content_comment',
            message=f"{comment.user.username} 评论了你的内容 '{comment.content.title}'",
            topic=None,
            post=None,
        )


class CommentViewSet(BaseModelViewSet):
    """内容评论视图集"""
    queryset = Comment.objects.filter(is_approved=True)
    select_related_fields = ['content', 'user', 'parent']
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
            return CommentCreateSerializer
        return CommentSerializer

    def get_queryset(self):
        # 预取由基类统一处理；子类追加业务过滤
        queryset = super().get_queryset()
        content_id = self.request.query_params.get('content')
        if content_id:
            queryset = queryset.filter(content_id=content_id)
        return queryset
    
    def perform_create(self, serializer):
        # 保存评论并使用 F() 表达式原子更新内容的评论计数
        comment = serializer.save(user=self.request.user)
        Content.objects.filter(pk=comment.content_id).update(comment_count=F('comment_count') + 1)

        # 默认已通过审核，直接发放积分并通知
        if comment.is_approved:
            queue_update_user_points(comment.user.id, 'comment', description='评论内容')
            _notify_content_comment(comment)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdminUser])
    def approve(self, request, pk=None):
        """管理员审核通过评论"""
        comment = self.get_object()
        if not comment.is_approved:
            comment.is_approved = True
            comment.save()
            Content.objects.filter(pk=comment.content_id).update(comment_count=F('comment_count') + 1)

            # 异步发放评论积分并通知作者
            queue_update_user_points(comment.user.id, 'comment', description='评论内容')
            _notify_content_comment(comment)
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
