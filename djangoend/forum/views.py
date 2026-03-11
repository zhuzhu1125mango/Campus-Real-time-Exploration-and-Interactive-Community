from django.shortcuts import render
from django.db.models import Count, Q, Sum
from django.utils import timezone
from datetime import timedelta
from rest_framework import viewsets, permissions, filters, status, serializers
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from .models import (
    Category, Board, Topic, Post, Attachment,
    Like, Tag, Report, Notification, Bookmark
)
from .serializers import (
    CategorySerializer, BoardListSerializer, BoardDetailSerializer,
    BoardCreateUpdateSerializer, TopicListSerializer, TopicDetailSerializer,
    TopicCreateSerializer, PostSerializer, PostCreateSerializer, 
    PostUpdateSerializer, AttachmentSerializer, LikeSerializer,
    TagSerializer, ReportCreateSerializer, BookmarkSerializer,
    NotificationSerializer
)


# 添加论坛统计功能
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def forum_stats(request):
    """获取论坛统计数据"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    # 计算时间范围
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 计算各种统计数据
    stats = {
        'user_count': User.objects.count(),
        'topic_count': Topic.objects.count(),
        'post_count': Post.objects.count(),
        'today_post_count': Post.objects.filter(created_at__gte=today_start).count(),
        'category_count': Category.objects.count(),
        'board_count': Board.objects.count()
    }
    
    return Response(stats)


# 添加热门话题功能
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def hot_topics(request):
    """获取热门话题"""
    days = int(request.query_params.get('days', 7))
    limit = int(request.query_params.get('limit', 10))
    
    # 计算时间范围
    now = timezone.now()
    date_from = now - timedelta(days=days)
    
    # 获取时间范围内的热门话题
    topics = Topic.objects.filter(
        created_at__gte=date_from
    ).annotate(
        post_count=Count('posts'),
        like_count=Count('posts__likes')
    ).order_by('-views', '-post_count', '-like_count')[:limit]
    
    serializer = TopicListSerializer(topics, many=True, context={'request': request})
    return Response(serializer.data)


class StandardResultsSetPagination(PageNumberPagination):
    """标准分页类"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class CategoryViewSet(viewsets.ModelViewSet):
    """论坛分类视图集"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return super().get_permissions()


class BoardViewSet(viewsets.ModelViewSet):
    """论坛板块视图集"""
    queryset = Board.objects.all()
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['order', 'name', 'created_at']
    ordering = ['category', 'order', 'name']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return BoardListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return BoardCreateUpdateSerializer
        return BoardDetailSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'topics', 'active_topics']:
            return [permissions.AllowAny()]
        return super().get_permissions()
    
    def get_queryset(self):
        queryset = Board.objects.all()
        if self.action == 'list':
            # 为列表添加额外的统计数据
            return queryset.annotate(
                topic_count=Count('topics', distinct=True),
                post_count=Count('topics__posts', distinct=True)
            )
        return queryset
    
    @action(detail=True, methods=['get'])
    def topics(self, request, pk=None):
        """获取板块内的主题列表"""
        board = self.get_object()
        queryset = Topic.objects.filter(board=board)
        
        # 过滤和排序
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        ordering = request.query_params.get('ordering', '-created_at')
        if ordering not in ['-created_at', 'created_at', '-views', 'views']:
            ordering = '-created_at'
        queryset = queryset.order_by(ordering)
        
        # 分页
        page = self.paginate_queryset(queryset)
        serializer = TopicListSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def active_topics(self, request, pk=None):
        """获取板块内的活跃主题列表"""
        board = self.get_object()
        days = int(request.query_params.get('days', 7))
        
        # 计算时间范围
        now = timezone.now()
        date_from = now - timedelta(days=days)
        
        # 获取最近活跃的主题
        queryset = Topic.objects.filter(
            board=board,
            posts__created_at__gte=date_from
        ).annotate(
            recent_posts=Count('posts', filter=Q(posts__created_at__gte=date_from))
        ).order_by('-recent_posts', '-views')
        
        # 分页
        page = self.paginate_queryset(queryset)
        serializer = TopicListSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)


class TopicViewSet(viewsets.ModelViewSet):
    """主题视图集"""
    queryset = Topic.objects.all()
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title']
    ordering_fields = ['created_at', 'views']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return TopicCreateSerializer
        elif self.action == 'list':
            return TopicListSerializer
        return TopicDetailSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'posts']:
            # 允许所有用户查看主题和帖子列表
            return [permissions.AllowAny()]
        elif self.action in ['create', 'update', 'partial_update', 'destroy', 'bookmark', 'close']:
            # 需要登录才能创建、编辑、删除主题，以及收藏、关闭主题
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated()]
    
    def get_queryset(self):
        queryset = Topic.objects.all()
        
        # 过滤
        board_id = self.request.query_params.get('board')
        if board_id:
            queryset = queryset.filter(board_id=board_id)
        
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        tag = self.request.query_params.get('tag')
        if tag:
            queryset = queryset.filter(tags__name=tag)
        
        author = self.request.query_params.get('author')
        if author:
            queryset = queryset.filter(author__username=author)
        
        return queryset
    
    def perform_create(self, serializer):
        topic = serializer.validated_data.get('topic')
        
        # 检查主题是否已关闭
        if topic.is_closed:
            raise serializers.ValidationError({"detail": "主题已关闭，无法发表新帖子"})
        
        # 检查是否是首贴
        is_first_post = not Post.objects.filter(topic=topic).exists()
        
        # 保存帖子，关联作者
        post = serializer.save(author=self.request.user, is_first_post=is_first_post)
        
        # 更新主题的更新时间
        topic.updated_at = timezone.now()
        topic.save(update_fields=['updated_at'])
        
        # 如果不是自己的主题，创建回复通知
        if topic.author != self.request.user:
            Notification.objects.create(
                user=topic.author,
                sender=self.request.user,
                notification_type='topic_reply',
                topic=topic,
                post=post,
                message=f"{self.request.user.username} 回复了您的主题 \"{topic.title}\""
            )
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # 增加浏览量
        instance.views += 1
        instance.save(update_fields=['views'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def posts(self, request, pk=None):
        """获取主题内的帖子列表"""
        topic = self.get_object()
        queryset = Post.objects.filter(topic=topic)
        
        # 分页
        page = self.paginate_queryset(queryset)
        serializer = PostSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def bookmark(self, request, pk=None):
        """收藏或取消收藏主题"""
        topic = self.get_object()
        user = request.user
        
        if not user.is_authenticated:
            return Response({"detail": "认证凭据未提供"}, status=status.HTTP_401_UNAUTHORIZED)
        
        bookmark, created = Bookmark.objects.get_or_create(user=user, topic=topic)
        
        if not created:
            # 如果已存在，则删除书签
            bookmark.delete()
            return Response({"status": "取消收藏成功"}, status=status.HTTP_200_OK)
        
        return Response({"status": "收藏成功"}, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """关闭或重新打开主题"""
        topic = self.get_object()
        
        if not request.user.is_authenticated:
            return Response({"detail": "认证凭据未提供"}, status=status.HTTP_401_UNAUTHORIZED)
        
        # 检查是否有权限（作者、版主或管理员）
        if (topic.author != request.user and 
            not topic.board.moderators.filter(id=request.user.id).exists() and 
            not request.user.is_staff):
            return Response({"detail": "没有权限执行此操作"}, status=status.HTTP_403_FORBIDDEN)
        
        topic.is_closed = not topic.is_closed
        topic.save(update_fields=['is_closed'])
        
        status_message = "关闭" if topic.is_closed else "打开"
        return Response({"status": f"主题已{status_message}"}, status=status.HTTP_200_OK)


class PostViewSet(viewsets.ModelViewSet):
    """帖子视图集"""
    queryset = Post.objects.all()
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PostCreateSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return PostUpdateSerializer
        elif self.action == 'audit':
            return PostAuditSerializer
        return PostSerializer
    
    def get_queryset(self):
        queryset = Post.objects.all()
        
        # 非管理员和版主只能看到已审核通过的帖子
        user = self.request.user
        if not user.is_authenticated or (not user.is_staff and not self.is_moderator(user)):
            queryset = queryset.filter(content_status='approved')
        
        # 根据版块筛选
        board_id = self.request.query_params.get('board')
        if board_id:
            queryset = queryset.filter(topic__board_id=board_id)
        
        # 根据作者筛选
        author_id = self.request.query_params.get('author')
        if author_id:
            queryset = queryset.filter(author_id=author_id)
        
        # 根据主题筛选
        topic_id = self.request.query_params.get('topic')
        if topic_id:
            queryset = queryset.filter(topic_id=topic_id)
        
        # 根据内容状态筛选（仅管理员和版主可见）
        if user.is_authenticated and (user.is_staff or self.is_moderator(user)):
            status_filter = self.request.query_params.get('status')
            if status_filter:
                queryset = queryset.filter(content_status=status_filter)
        
        return queryset
    
    def is_moderator(self, user):
        """检查用户是否是版主"""
        # 获取帖子所在的版块
        if self.kwargs.get('pk'):
            try:
                post = Post.objects.get(pk=self.kwargs['pk'])
                return post.topic.board.moderators.filter(id=user.id).exists()
            except Post.DoesNotExist:
                pass
        return False
    
    def perform_create(self, serializer):
        post = serializer.save()
        # 如果是主题的第一个帖子，设置为首贴
        is_first_post = not Post.objects.filter(topic=post.topic).exclude(id=post.id).exists()
        if is_first_post:
            post.is_first_post = True
            post.save(update_fields=['is_first_post'])
    
    def perform_update(self, serializer):
        post = serializer.instance
        # 只有帖子作者、管理员和版主可以编辑
        if post.author != self.request.user and not self.request.user.is_staff and not self.is_moderator(self.request.user):
            raise PermissionDenied("您没有权限编辑此帖子")
        serializer.save()
    
    def perform_destroy(self, instance):
        # 如果是首贴，删除整个主题
        if instance.is_first_post:
            instance.topic.delete()
        else:
            instance.delete()
    
    @action(detail=True, methods=['post'])
    def audit(self, request, pk=None):
        """审核帖子"""
        post = self.get_object()
        
        # 只有管理员和版主可以审核
        if not request.user.is_staff and not self.is_moderator(request.user):
            return Response({"detail": "您没有权限审核帖子"}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = self.get_serializer(post, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """点赞或取消点赞帖子"""
        post = self.get_object()
        
        # 用户必须登录才能点赞
        if not request.user.is_authenticated:
            return Response({"detail": "认证凭据未提供"}, status=status.HTTP_401_UNAUTHORIZED)
        
        # 只能点赞已审核通过的帖子
        if post.content_status != 'approved' and not request.user.is_staff and not self.is_moderator(request.user):
            return Response({"detail": "此帖子未通过审核或已被隐藏"}, status=status.HTTP_403_FORBIDDEN)
        
        like, created = Like.objects.get_or_create(user=request.user, post=post)
        
        if not created:
            # 如果已存在，则取消点赞
            like.delete()
            return Response({"status": "取消点赞成功"}, status=status.HTTP_200_OK)
        
        # 创建点赞通知（如果点赞的不是自己的帖子）
        if post.author != request.user:
            Notification.objects.create(
                user=post.author,
                sender=request.user,
                notification_type='like',
                post=post,
                message=f"{request.user.username} 点赞了你的帖子"
            )
        
        return Response({"status": "点赞成功"}, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def report(self, request, pk=None):
        """举报帖子"""
        post = self.get_object()
        
        if not request.user.is_authenticated:
            return Response({"detail": "认证凭据未提供"}, status=status.HTTP_401_UNAUTHORIZED)
        
        serializer = ReportCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(reporter=request.user, post=post)
            
            # 标记帖子为需要审查
            post.content_status = 'flagged'
            post.save(update_fields=['content_status'])
            
            # 通知版主和管理员
            moderators = post.topic.board.moderators.all()
            for moderator in moderators:
                Notification.objects.create(
                    user=moderator,
                    sender=request.user,
                    notification_type='system',
                    topic=post.topic,
                    post=post,
                    message=f"帖子被举报，需要审核：{post.topic.title}"
                )
            
            return Response({"status": "举报成功"}, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    @action(detail=False, methods=['get'])
    def pending_review(self, request):
        """获取待审核的帖子列表"""
        # 只有管理员和版主可以查看
        if not request.user.is_staff and not any(board.moderators.filter(id=request.user.id).exists() for board in Board.objects.all()):
            return Response({"detail": "您没有权限查看待审核的帖子"}, status=status.HTTP_403_FORBIDDEN)
        
        # 如果是版主，只能看自己负责版块的帖子
        if not request.user.is_staff:
            moderated_boards = Board.objects.filter(moderators=request.user)
            queryset = Post.objects.filter(
                Q(content_status='pending') | Q(content_status='flagged'),
                topic__board__in=moderated_boards
            )
        else:
            queryset = Post.objects.filter(
                Q(content_status='pending') | Q(content_status='flagged')
            )
        
        page = self.paginate_queryset(queryset)
        serializer = PostSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['delete'])
    def unlike(self, request, pk=None):
        """取消点赞帖子"""
        post = self.get_object()
        
        # 用户必须登录才能取消点赞
        if not request.user.is_authenticated:
            return Response({"detail": "认证凭据未提供"}, status=status.HTTP_401_UNAUTHORIZED)
        
        # 查找点赞记录
        try:
            like = Like.objects.get(user=request.user, post=post)
            like.delete()
            return Response({"status": "取消点赞成功"}, status=status.HTTP_200_OK)
        except Like.DoesNotExist:
            return Response({"detail": "未找到点赞记录"}, status=status.HTTP_404_NOT_FOUND)


class AttachmentViewSet(viewsets.ModelViewSet):
    """附件视图集"""
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Attachment.objects.all()
        
        # 只允许查看自己的附件
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(post__author=self.request.user) | 
                Q(post__topic__board__moderators=self.request.user)
            )
        
        post_id = self.request.query_params.get('post')
        if post_id:
            queryset = queryset.filter(post_id=post_id)
        
        return queryset
    
    def perform_create(self, serializer):
        post_id = self.request.data.get('post')
        try:
            post = Post.objects.get(id=post_id)
            
            # 只能给自己的帖子添加附件
            if post.author != self.request.user and not self.request.user.is_staff:
                return Response(
                    {"detail": "没有权限给此帖子添加附件"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            serializer.save(post=post)
        except Post.DoesNotExist:
            return Response(
                {"detail": "帖子不存在"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """下载附件并增加下载次数"""
        attachment = self.get_object()
        attachment.download_count += 1
        attachment.save(update_fields=['download_count'])
        return Response({"file_url": attachment.file.url}, status=status.HTTP_200_OK)


class TagViewSet(viewsets.ModelViewSet):
    """标签视图集"""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return super().get_permissions()


class BookmarkViewSet(viewsets.ModelViewSet):
    """书签视图集"""
    serializer_class = BookmarkSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # 只能查看自己的书签
        return Bookmark.objects.filter(user=self.request.user)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """通知视图集"""
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        # 只能查看自己的通知
        return Notification.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """标记通知为已读"""
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        return Response({"status": "标记成功"}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """标记所有通知为已读"""
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({"status": "所有通知已标记为已读"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['delete'])
    def unbookmark(self, request, pk=None):
        """取消收藏主题"""
        topic = self.get_object()
        user = request.user
        
        if not user.is_authenticated:
            return Response({"detail": "认证凭据未提供"}, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            bookmark = Bookmark.objects.get(user=user, topic=topic)
            bookmark.delete()
            return Response({"status": "取消收藏成功"}, status=status.HTTP_200_OK)
        except Bookmark.DoesNotExist:
            return Response({"detail": "未找到收藏记录"}, status=status.HTTP_404_NOT_FOUND)
