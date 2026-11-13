from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db import transaction
from django.db.models import F

from users.permissions import IsOwnerOrAdmin
from users.tasks import queue_update_user_points
from notifications.notification_sender import notify_forum_event
from core.base_viewsets import BaseModelViewSet, AuthenticatedModelViewSet
from .models import Activity, ActivityLike, ActivityComment
from .serializers import (
    ActivitySerializer,
    ActivityCreateSerializer,
    ActivityLikeSerializer,
    ActivityLikeCreateSerializer,
    ActivityCommentSerializer,
    ActivityCommentCreateSerializer,
)


class ActivityViewSet(BaseModelViewSet):
    """动态视图集"""
    queryset = Activity.objects.filter(is_public=True)
    permission_config = {
        'list': [AllowAny],
        'retrieve': [AllowAny],
        'create': [IsAuthenticated],
        'like': [IsAuthenticated],
        'unlike': [IsAuthenticated],
        'comments': [IsAuthenticated],
        'feed': [IsAuthenticated],
        'my_activities': [IsAuthenticated],
        'update': [IsAuthenticated, IsOwnerOrAdmin],
        'partial_update': [IsAuthenticated, IsOwnerOrAdmin],
        'destroy': [IsAuthenticated, IsOwnerOrAdmin],
    }

    def get_serializer_class(self):
        if self.action == 'create':
            return ActivityCreateSerializer
        return ActivitySerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def perform_create(self, serializer):
        # 保存动态
        activity = serializer.save(user=self.request.user)

        # 异步发放发布动态积分
        queue_update_user_points(
            self.request.user.id,
            'post',
            description='发布动态'
        )

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        activity = self.get_object()
        with transaction.atomic():
            # 使用 get_or_create + 唯一约束，防止并发重复点赞
            like, created = ActivityLike.objects.get_or_create(activity=activity, user=request.user)
            if not created:
                return Response({'status': 'already_liked'}, status=status.HTTP_400_BAD_REQUEST)
            # 使用 F 表达式原子更新点赞数
            Activity.objects.filter(pk=activity.pk).update(likes_count=F('likes_count') + 1)

        # 异步发放点赞积分
        queue_update_user_points(request.user.id, 'like', description='点赞动态')

        # 被点赞者积分与通知（自己点赞自己不通知）
        if activity.user != request.user:
            queue_update_user_points(
                activity.user.id,
                'liked',
                description='动态被点赞'
            )
            notify_forum_event(
                recipient=activity.user,
                sender=request.user,
                forum_type='like',
                message=f"{request.user.username} 点赞了你的动态",
                topic=None,
                post=None,
            )

        return Response({'status': 'liked'})

    @action(detail=True, methods=['post'])
    def unlike(self, request, pk=None):
        activity = self.get_object()
        with transaction.atomic():
            like = ActivityLike.objects.filter(activity=activity, user=request.user).first()
            if not like:
                return Response({'status': 'not_liked'}, status=status.HTTP_400_BAD_REQUEST)
            like.delete()
            Activity.objects.filter(pk=activity.pk).update(likes_count=F('likes_count') - 1)
        return Response({'status': 'unliked'})

    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        activity = self.get_object()
        comments = activity.comments.filter(parent=None)
        serializer = ActivityCommentSerializer(comments, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def feed(self, request):
        # 获取关注用户及自己的公开动态
        following_ids = list(request.user.following.values_list('id', flat=True))
        following_ids.append(request.user.id)
        activities = Activity.objects.filter(user__id__in=following_ids, is_public=True).order_by('-created_at')
        serializer = ActivitySerializer(activities, many=True, context={'request': request})
        return Response({'results': serializer.data})

    @action(detail=False, methods=['get'])
    def my_activities(self, request):
        # 获取当前用户的动态
        activities = Activity.objects.filter(user=request.user).order_by('-created_at')
        serializer = ActivitySerializer(activities, many=True, context={'request': request})
        return Response({'results': serializer.data})


class ActivityLikeViewSet(AuthenticatedModelViewSet):
    """动态点赞视图集"""
    queryset = ActivityLike.objects.all()
    permission_config = {
        'list': [IsAuthenticated],
        'retrieve': [IsAuthenticated, IsOwnerOrAdmin],
        'create': [IsAuthenticated],
        'update': [IsAuthenticated, IsOwnerOrAdmin],
        'partial_update': [IsAuthenticated, IsOwnerOrAdmin],
        'destroy': [IsAuthenticated, IsOwnerOrAdmin],
    }

    def get_serializer_class(self):
        if self.action == 'create':
            return ActivityLikeCreateSerializer
        return ActivityLikeSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ActivityCommentViewSet(AuthenticatedModelViewSet):
    """动态评论视图集"""
    queryset = ActivityComment.objects.all()
    permission_config = {
        'list': [IsAuthenticated],
        'retrieve': [IsAuthenticated, IsOwnerOrAdmin],
        'create': [IsAuthenticated],
        'update': [IsAuthenticated, IsOwnerOrAdmin],
        'partial_update': [IsAuthenticated, IsOwnerOrAdmin],
        'destroy': [IsAuthenticated, IsOwnerOrAdmin],
    }

    def get_serializer_class(self):
        if self.action == 'create':
            return ActivityCommentCreateSerializer
        return ActivityCommentSerializer

    def perform_create(self, serializer):
        comment = serializer.save(user=self.request.user)

        # 异步发放评论动态积分
        queue_update_user_points(
            self.request.user.id,
            'comment',
            description='评论动态'
        )

        # 通知动态作者（自己评论自己不通知）
        activity = comment.activity
        if activity.user != self.request.user:
            notify_forum_event(
                recipient=activity.user,
                sender=self.request.user,
                forum_type='content_comment',
                message=f"{self.request.user.username} 评论了你的动态",
                topic=None,
                post=None,
            )
