from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Q, Sum, F, OuterRef, Subquery, Exists
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from rest_framework import viewsets, permissions, filters, status, serializers
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from .models import (
    Category, Board, Topic, Post, Attachment,
    Like, Tag, Report, Bookmark,
    Comment, CommentLike
)
from .serializers import (
    CategorySerializer, BoardListSerializer, BoardDetailSerializer,
    BoardCreateUpdateSerializer, TopicListSerializer, TopicDetailSerializer,
    TopicCreateSerializer, PostSerializer, PostCreateSerializer,
    PostUpdateSerializer, AttachmentSerializer, LikeSerializer,
    TagSerializer, ReportCreateSerializer, BookmarkSerializer,
    CommentSerializer, CommentCreateSerializer
)
from notifications.notification_sender import notify_forum_event
from users.permissions import IsOwnerOrAdmin
from users.throttles import SearchThrottle, WriteThrottle
from users.tasks import queue_update_user_points
from search.services import SearchService
from core.base_viewsets import (
    StandardResultsSetPagination,
    PublicReadOnlyModelViewSet,
    AuthenticatedModelViewSet,
)


def annotate_topic_list(queryset):
    """为主题列表查询集添加帖子数与最后回复信息的 annotate，减少 N+1。
    注意：字段名避免与模型 property 重名（Topic.post_count 等）。"""
    last_post = Post.objects.filter(topic=OuterRef('pk')).order_by('-created_at')
    return queryset.annotate(
        topic_post_count=Count('posts', distinct=True),
        last_post_id=Subquery(last_post.values('id')[:1]),
        last_post_created_at=Subquery(last_post.values('created_at')[:1]),
        last_post_author_id=Subquery(last_post.values('author__id')[:1]),
        last_post_author_username=Subquery(last_post.values('author__username')[:1]),
        last_post_is_first_post=Subquery(last_post.values('is_first_post')[:1]),
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
    """获取热门话题（支持分页）"""
    days = int(request.query_params.get('days', 7))
    
    # 计算时间范围
    now = timezone.now()
    date_from = now - timedelta(days=days)
    
    # 获取时间范围内的热门话题，使用 distinct 避免多对多关联导致重复计数
    topics = annotate_topic_list(
        Topic.objects.filter(created_at__gte=date_from)
    ).annotate(
        like_count=Count('posts__likes', distinct=True)
    ).order_by('-views', '-topic_post_count', '-like_count')
    
    paginator = StandardResultsSetPagination()
    page = paginator.paginate_queryset(topics, request)
    serializer = TopicListSerializer(page, many=True, context={'request': request})
    return paginator.get_paginated_response(serializer.data)


# 添加获取用户收藏主题功能
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def my_bookmarks(request):
    """获取用户收藏的主题"""
    user = request.user
    # 直接以 Topic 为查询目标并预取关联，避免 N+1
    topics = annotate_topic_list(
        Topic.objects.filter(bookmarks__user=user).select_related('author', 'board').prefetch_related('tags').order_by('-created_at')
    )
    
    paginator = StandardResultsSetPagination()
    page = paginator.paginate_queryset(topics, request)
    serializer = TopicListSerializer(page, many=True, context={'request': request})
    return paginator.get_paginated_response(serializer.data)


class CategoryViewSet(PublicReadOnlyModelViewSet):
    """论坛分类视图集"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_config = {
        'list': [permissions.AllowAny],
        'retrieve': [permissions.AllowAny],
        'create': [permissions.IsAdminUser],
        'update': [permissions.IsAdminUser],
        'partial_update': [permissions.IsAdminUser],
        'destroy': [permissions.IsAdminUser],
    }


class BoardViewSet(PublicReadOnlyModelViewSet):
    """论坛板块视图集"""
    queryset = Board.objects.all()
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['order', 'name', 'created_at']
    ordering = ['category', 'order', 'name']
    select_related_fields = ['category']
    permission_config = {
        'list': [permissions.AllowAny],
        'retrieve': [permissions.AllowAny],
        'topics': [permissions.AllowAny],
        'active_topics': [permissions.AllowAny],
        'create': [permissions.IsAdminUser],
        'update': [permissions.IsAdminUser],
        'partial_update': [permissions.IsAdminUser],
        'destroy': [permissions.IsAdminUser],
    }

    def get_serializer_class(self):
        if self.action == 'list':
            return BoardListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return BoardCreateUpdateSerializer
        return BoardDetailSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == 'list':
            # 预取分类，并通过 annotate 聚合主题数、帖子数、最后发帖信息，减少 N+1
            # 字段名避免与模型 property 重名
            last_post = Post.objects.filter(topic__board=OuterRef('pk')).order_by('-created_at')
            return queryset.annotate(
                board_topic_count=Count('topics', distinct=True),
                board_post_count=Count('topics__posts', distinct=True),
                last_post_id=Subquery(last_post.values('id')[:1]),
                last_post_created_at=Subquery(last_post.values('created_at')[:1]),
                last_post_topic_id=Subquery(last_post.values('topic__id')[:1]),
                last_post_topic_title=Subquery(last_post.values('topic__title')[:1]),
                last_post_author_id=Subquery(last_post.values('author__id')[:1]),
                last_post_author_username=Subquery(last_post.values('author__username')[:1]),
            )

        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )

        return queryset

    @action(detail=True, methods=['get'])
    def topics(self, request, pk=None):
        """获取板块内的主题列表"""
        board = self.get_object()
        # 预取作者、板块、标签，并 annotate 帖子数/最后回复，减少 N+1
        queryset = annotate_topic_list(
            Topic.objects.filter(board=board).select_related('author', 'board').prefetch_related('tags')
        )
        
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
        
        # 获取最近活跃的主题，预取关联并使用 distinct 去重
        queryset = annotate_topic_list(
            Topic.objects.filter(
                board=board,
                posts__created_at__gte=date_from
            ).select_related('author', 'board').prefetch_related('tags')
        ).annotate(
            recent_posts=Count('posts', filter=Q(posts__created_at__gte=date_from), distinct=True)
        ).order_by('-recent_posts', '-views').distinct()
        
        # 分页
        page = self.paginate_queryset(queryset)
        serializer = TopicListSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)


class TopicViewSet(PublicReadOnlyModelViewSet):
    """主题视图集"""
    queryset = Topic.objects.all()
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'views']
    ordering = ['-created_at']
    select_related_fields = ['author', 'board']
    prefetch_related_fields = ['tags']
    permission_config = {
        'list': [permissions.AllowAny],
        'retrieve': [permissions.AllowAny],
        'posts': [permissions.AllowAny],
        'create': [permissions.IsAuthenticated],
        'bookmark': [permissions.IsAuthenticated],
        'unbookmark': [permissions.IsAuthenticated],
        'close': [permissions.IsAuthenticated],
        'update': [permissions.IsAuthenticated, IsOwnerOrAdmin],
        'partial_update': [permissions.IsAuthenticated, IsOwnerOrAdmin],
        'destroy': [permissions.IsAuthenticated, IsOwnerOrAdmin],
    }
    throttle_config = {
        'list': [SearchThrottle],
        'retrieve': [SearchThrottle],
        'create': [WriteThrottle],
        'bookmark': [WriteThrottle],
        'unbookmark': [WriteThrottle],
        'close': [WriteThrottle],
        'update': [WriteThrottle],
        'partial_update': [WriteThrottle],
        'destroy': [WriteThrottle],
    }

    def get_serializer_class(self):
        if self.action == 'create':
            return TopicCreateSerializer
        elif self.action == 'list':
            return TopicListSerializer
        return TopicDetailSerializer

    def get_queryset(self):
        # 预取作者、板块和标签，并 annotate 帖子数/最后回复信息，减少 N+1 查询
        queryset = annotate_topic_list(super().get_queryset())

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

        search = self.request.query_params.get('search')
        if search:
            service = SearchService()
            es_ids = list(service.search_topics(search, limit=200).values_list('pk', flat=True))
            if es_ids:
                queryset = queryset.filter(pk__in=es_ids)
            else:
                queryset = queryset.filter(title__icontains=search)

        return queryset

    def perform_create(self, serializer):
        # TopicCreateSerializer 已负责创建主题及首贴
        serializer.save()
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # 使用 F() 表达式原子更新浏览量，避免并发覆盖
        Topic.objects.filter(pk=instance.pk).update(views=F('views') + 1)
        instance.refresh_from_db(fields=['views'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def posts(self, request, pk=None):
        """获取主题内的帖子列表"""
        topic = self.get_object()
        # 预取作者、主题、板块、点赞，减少 N+1
        queryset = Post.objects.filter(topic=topic).select_related('author', 'topic', 'topic__board', 'edited_by', 'reviewed_by').prefetch_related('likes')
        
        # 分页
        page = self.paginate_queryset(queryset)
        serializer = PostSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def bookmark(self, request, pk=None):
        """收藏主题"""
        topic = self.get_object()
        user = request.user

        bookmark, created = Bookmark.objects.get_or_create(user=user, topic=topic)

        if not created:
            return Response({"detail": "已经收藏过此主题"}, status=status.HTTP_200_OK)

        # 异步发放收藏积分
        queue_update_user_points(user.id, 'favorite', description='收藏主题')

        return Response({"status": "收藏成功"}, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['delete'])
    def unbookmark(self, request, pk=None):
        """取消收藏主题"""
        topic = self.get_object()
        user = request.user
        
        try:
            bookmark = Bookmark.objects.get(user=user, topic=topic)
            bookmark.delete()
            return Response({"status": "取消收藏成功"}, status=status.HTTP_200_OK)
        except Bookmark.DoesNotExist:
            return Response({"detail": "未找到收藏记录"}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """关闭或重新打开主题"""
        topic = self.get_object()
        
        # 检查是否有权限（作者、版主或管理员）
        if (topic.author != request.user and 
            not topic.board.moderators.filter(id=request.user.id).exists() and 
            not request.user.is_staff):
            return Response({"detail": "没有权限执行此操作"}, status=status.HTTP_403_FORBIDDEN)
        
        topic.is_closed = not topic.is_closed
        topic.save(update_fields=['is_closed'])
        
        status_message = "关闭" if topic.is_closed else "打开"
        return Response({"status": f"主题已{status_message}"}, status=status.HTTP_200_OK)


class PostViewSet(PublicReadOnlyModelViewSet):
    """帖子视图集"""
    queryset = Post.objects.all()
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    select_related_fields = ['author', 'topic', 'topic__board', 'edited_by', 'reviewed_by']
    annotation_fields = {'like_count': Count('likes', distinct=True)}
    permission_config = {
        'list': [permissions.AllowAny],
        'retrieve': [permissions.AllowAny],
        'create': [permissions.IsAuthenticated],
        'like': [permissions.IsAuthenticated],
        'unlike': [permissions.IsAuthenticated],
        'report': [permissions.IsAuthenticated],
        'pending_review': [permissions.IsAuthenticated],
        'update': [permissions.IsAuthenticated],
        'partial_update': [permissions.IsAuthenticated],
        'destroy': [permissions.IsAuthenticated],
    }
    throttle_config = {
        'list': [SearchThrottle],
        'retrieve': [SearchThrottle],
        'create': [WriteThrottle],
        'like': [WriteThrottle],
        'unlike': [WriteThrottle],
        'report': [WriteThrottle],
        'update': [WriteThrottle],
        'partial_update': [WriteThrottle],
        'destroy': [WriteThrottle],
    }

    def get_serializer_class(self):
        if self.action == 'create':
            return PostCreateSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return PostUpdateSerializer
        return PostSerializer

    def get_queryset(self):
        # 预取与 annotate 由基类统一处理；子类追加业务过滤
        queryset = super().get_queryset()

        # 当前用户是否点赞使用 Exists 子查询，避免拉取全部点赞记录
        user = self.request.user
        if user.is_authenticated:
            queryset = queryset.annotate(
                is_liked=Exists(Like.objects.filter(post=OuterRef('pk'), user=user))
            )

        # 非管理员和版主只能看到已审核通过的帖子
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

        search = self.request.query_params.get('search')
        if search:
            service = SearchService()
            es_ids = list(service.search_posts(search, limit=200).values_list('pk', flat=True))
            if es_ids:
                queryset = queryset.filter(pk__in=es_ids)
            else:
                queryset = queryset.filter(
                    Q(content__icontains=search) | Q(topic__title__icontains=search)
                )

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
        # 使用事务和行锁，防止并发下多个帖子同时被标记为首贴
        with transaction.atomic():
            # 锁定该主题下的所有帖子
            Post.objects.filter(topic=post.topic).select_for_update()
            is_first_post = not Post.objects.filter(topic=post.topic).exclude(id=post.id).exists()
            if is_first_post:
                post.is_first_post = True
                post.save(update_fields=['is_first_post'])
    
    def perform_update(self, serializer):
        post = serializer.instance
        # 只有帖子作者、管理员和版主可以编辑
        if post.author != self.request.user and not self.request.user.is_staff and not self.is_moderator(self.request.user):
            raise serializers.ValidationError({"detail": "您没有权限编辑此帖子"})
        serializer.save()
    
    def perform_destroy(self, instance):
        # 仅帖子作者、管理员或版主可删除
        user = self.request.user
        is_moderator = instance.topic.board.moderators.filter(id=user.id).exists()
        if instance.author != user and not user.is_staff and not is_moderator:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("您没有权限删除此帖子")

        # 如果是首贴，删除整个主题
        if instance.is_first_post:
            instance.topic.delete()
        else:
            instance.delete()
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """点赞或取消点赞帖子"""
        post = self.get_object()

        # 只能点赞已审核通过的帖子
        if post.content_status != 'approved' and not request.user.is_staff and not self.is_moderator(request.user):
            return Response({"detail": "此帖子未通过审核或已被隐藏"}, status=status.HTTP_403_FORBIDDEN)

        with transaction.atomic():
            like, created = Like.objects.get_or_create(user=request.user, post=post)

            if not created:
                # 如果已存在，则取消点赞
                like.delete()
                return Response({"status": "取消点赞成功"}, status=status.HTTP_200_OK)

            # 创建点赞通知（如果点赞的不是自己的帖子）
            if post.author != request.user:
                notify_forum_event(
                    recipient=post.author,
                    sender=request.user,
                    forum_type='like',
                    message=f"{request.user.username} 点赞了你的帖子",
                    post=post,
                )

        # 异步更新积分：点赞者 +2，被点赞者 +3
        queue_update_user_points(request.user.id, 'like')
        if post.author != request.user:
            queue_update_user_points(post.author.id, 'liked')

        return Response({"status": "点赞成功"}, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def report(self, request, pk=None):
        """举报帖子"""
        post = self.get_object()
        
        serializer = ReportCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(reporter=request.user, post=post)
            
            # 标记帖子为需要审查
            post.content_status = 'flagged'
            post.save(update_fields=['content_status'])
            
            # 通知版主和管理员
            moderators = post.topic.board.moderators.all()
            for moderator in moderators:
                notify_forum_event(
                    recipient=moderator,
                    sender=request.user,
                    forum_type='system',
                    message=f"帖子被举报，需要审核：{post.topic.title}",
                    topic=post.topic,
                    post=post,
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
        
        # 查找点赞记录
        try:
            like = Like.objects.get(user=request.user, post=post)
            like.delete()
            return Response({"status": "取消点赞成功"}, status=status.HTTP_200_OK)
        except Like.DoesNotExist:
            return Response({"detail": "未找到点赞记录"}, status=status.HTTP_404_NOT_FOUND)


class AttachmentViewSet(AuthenticatedModelViewSet):
    """附件视图集"""
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        
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
        post = get_object_or_404(Post, id=post_id)

        # 只能给自己的帖子添加附件
        if post.author != self.request.user and not self.request.user.is_staff:
            raise PermissionDenied("没有权限给此帖子添加附件")

        serializer.save(post=post)
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """下载附件并增加下载次数"""
        attachment = self.get_object()
        # 使用 F() 表达式原子更新下载次数，避免并发覆盖
        Attachment.objects.filter(pk=attachment.pk).update(download_count=F('download_count') + 1)
        return Response({"file_url": attachment.file.url}, status=status.HTTP_200_OK)


class TagViewSet(PublicReadOnlyModelViewSet):
    """标签视图集"""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_config = {
        'list': [permissions.AllowAny],
        'retrieve': [permissions.AllowAny],
        'hot': [permissions.AllowAny],
        'topics': [permissions.AllowAny],
        'create': [permissions.IsAdminUser],
        'update': [permissions.IsAdminUser],
        'partial_update': [permissions.IsAdminUser],
        'destroy': [permissions.IsAdminUser],
    }

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)
        return queryset

    @action(detail=False, methods=['get'])
    def hot(self, request):
        """获取热门标签（按关联主题数排序）"""
        limit = int(request.query_params.get('limit', 10))
        tags = Tag.objects.annotate(
            topic_count=Count('topics')
        ).order_by('-topic_count', '-id')[:limit]
        serializer = self.get_serializer(tags, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def topics(self, request, pk=None):
        """获取标签下的主题列表"""
        tag = self.get_object()
        # 预取关联并 annotate 列表字段，减少 N+1
        queryset = annotate_topic_list(
            tag.topics.select_related('author', 'board').prefetch_related('tags').order_by('-created_at')
        )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = TopicListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = TopicListSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)


class BookmarkViewSet(AuthenticatedModelViewSet):
    """书签视图集"""
    serializer_class = BookmarkSerializer
    queryset = Bookmark.objects.all()
    throttle_config = {
        'list': [SearchThrottle],
        'retrieve': [SearchThrottle],
        'create': [WriteThrottle],
        'destroy': [WriteThrottle],
        'unbookmark': [WriteThrottle],
    }

    def get_queryset(self):
        # 只能查看自己的书签
        return Bookmark.objects.filter(user=self.request.user)

    @action(detail=False, methods=['delete'], url_path='unbookmark')
    def unbookmark(self, request):
        """取消收藏主题"""
        topic_id = request.query_params.get('topic') or request.data.get('topic')
        if not topic_id:
            return Response({"detail": "请提供要取消收藏的主题ID"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            bookmark = Bookmark.objects.get(user=request.user, topic_id=topic_id)
            bookmark.delete()
            return Response({"status": "取消收藏成功"}, status=status.HTTP_200_OK)
        except Bookmark.DoesNotExist:
            return Response({"detail": "未找到收藏记录"}, status=status.HTTP_404_NOT_FOUND)


class CommentViewSet(PublicReadOnlyModelViewSet):
    """评论视图集"""
    queryset = Comment.objects.all()
    select_related_fields = ['author', 'post']
    prefetch_related_fields = ['likes', 'replies__author']
    annotation_fields = {'like_count': Count('likes', distinct=True)}
    permission_config = {
        'list': [permissions.AllowAny],
        'retrieve': [permissions.AllowAny],
        'create': [permissions.IsAuthenticated],
        'like': [permissions.IsAuthenticated],
        'report': [permissions.IsAuthenticated],
        'update': [permissions.IsAuthenticated, IsOwnerOrAdmin],
        'partial_update': [permissions.IsAuthenticated, IsOwnerOrAdmin],
        'destroy': [permissions.IsAuthenticated, IsOwnerOrAdmin],
        'approve': [permissions.IsAuthenticated, permissions.IsAdminUser],
        'disapprove': [permissions.IsAuthenticated, permissions.IsAdminUser],
    }
    throttle_config = {
        'list': [SearchThrottle],
        'retrieve': [SearchThrottle],
        'create': [WriteThrottle],
        'like': [WriteThrottle],
        'report': [WriteThrottle],
        'update': [WriteThrottle],
        'partial_update': [WriteThrottle],
        'destroy': [WriteThrottle],
        'approve': [WriteThrottle],
        'disapprove': [WriteThrottle],
    }

    def get_serializer_class(self):
        if self.action == 'create':
            return CommentCreateSerializer
        return CommentSerializer

    def get_queryset(self):
        # 预取与 annotate 由基类统一处理；子类追加业务过滤
        queryset = super().get_queryset()

        # 当前用户是否点赞
        user = self.request.user
        if user.is_authenticated:
            queryset = queryset.annotate(
                is_liked=Exists(CommentLike.objects.filter(comment=OuterRef('pk'), user=user))
            )

        # 根据帖子筛选
        post_id = self.request.query_params.get('post')
        if post_id:
            queryset = queryset.filter(post_id=post_id, parent=None)

        # 根据作者筛选
        author_id = self.request.query_params.get('author')
        if author_id:
            queryset = queryset.filter(author_id=author_id)

        return queryset
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """点赞或取消点赞评论"""
        comment = self.get_object()

        with transaction.atomic():
            like, created = CommentLike.objects.get_or_create(user=request.user, comment=comment)

            if not created:
                like.delete()
                return Response({"status": "取消点赞成功"}, status=status.HTTP_200_OK)

            # 创建点赞通知（如果点赞的不是自己的评论）
            if comment.author != request.user:
                notify_forum_event(
                    recipient=comment.author,
                    sender=request.user,
                    forum_type='like',
                    message=f"{request.user.username} 点赞了你的评论",
                    post=comment.post,
                )

        # 异步更新积分：点赞者 +2，被点赞者 +3
        queue_update_user_points(request.user.id, 'like')
        if comment.author != request.user:
            queue_update_user_points(comment.author.id, 'liked')

        return Response({"status": "点赞成功"}, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def report(self, request, pk=None):
        """举报评论"""
        comment = self.get_object()
        
        report_type = request.data.get('report_type', 'other')
        description = request.data.get('description', '')
        
        if report_type not in [choice[0] for choice in Report.REPORT_TYPES]:
            return Response({"detail": "无效的举报类型"}, status=status.HTTP_400_BAD_REQUEST)
        
        # 创建举报记录
        Report.objects.create(
            reporter=request.user,
            post=comment.post,
            report_type=report_type,
            description=description
        )
        
        return Response({"status": "举报成功"}, status=status.HTTP_201_CREATED)
