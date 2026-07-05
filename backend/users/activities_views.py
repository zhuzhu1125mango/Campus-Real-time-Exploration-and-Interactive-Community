from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .activities import Activity, ActivityLike, ActivityComment
from .activities_serializers import (
    ActivitySerializer, ActivityCreateSerializer,
    ActivityLikeSerializer, ActivityLikeCreateSerializer,
    ActivityCommentSerializer, ActivityCommentCreateSerializer
)
from rest_framework.permissions import IsAuthenticated, AllowAny


class ActivityViewSet(viewsets.ModelViewSet):
    queryset = Activity.objects.filter(is_public=True)
    permission_classes = [AllowAny]
    
    def get_permissions(self):
        # 对于创建、点赞、取消点赞等操作，需要用户登录
        if self.action in ['create', 'like', 'unlike', 'comments', 'feed', 'my_activities']:
            return [IsAuthenticated()]
        # 对于列表和详情视图，允许未登录用户访问
        return [AllowAny()]
    
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
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        activity = self.get_object()
        # 检查是否已经点赞
        if activity.likes.filter(user=request.user).exists():
            return Response({'status': 'already_liked'}, status=status.HTTP_400_BAD_REQUEST)
        # 创建点赞记录
        ActivityLike.objects.create(activity=activity, user=request.user)
        # 更新动态的点赞数
        activity.likes_count = activity.likes.count()
        activity.save()
        return Response({'status': 'liked'})
    
    @action(detail=True, methods=['post'])
    def unlike(self, request, pk=None):
        activity = self.get_object()
        # 检查是否已经点赞
        like = activity.likes.filter(user=request.user).first()
        if not like:
            return Response({'status': 'not_liked'}, status=status.HTTP_400_BAD_REQUEST)
        # 删除点赞记录
        like.delete()
        # 更新动态的点赞数
        activity.likes_count = activity.likes.count()
        activity.save()
        return Response({'status': 'unliked'})
    
    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        activity = self.get_object()
        comments = activity.comments.filter(parent=None)
        serializer = ActivityCommentSerializer(comments, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def feed(self, request):
        # 获取关注用户的动态
        # 当前 User 模型未实现 following 关系，先返回当前用户自己的动态，避免 AttributeError
        following_ids = [request.user.id]
        # TODO: 实现用户关注关系后，替换为 request.user.following.values_list('id', flat=True)
        # 获取动态
        activities = Activity.objects.filter(user__id__in=following_ids, is_public=True).order_by('-created_at')
        serializer = ActivitySerializer(activities, many=True, context={'request': request})
        return Response({'results': serializer.data})
    
    @action(detail=False, methods=['get'])
    def my_activities(self, request):
        # 获取当前用户的动态
        activities = Activity.objects.filter(user=request.user).order_by('-created_at')
        serializer = ActivitySerializer(activities, many=True, context={'request': request})
        return Response({'results': serializer.data})


class ActivityLikeViewSet(viewsets.ModelViewSet):
    queryset = ActivityLike.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ActivityLikeCreateSerializer
        return ActivityLikeSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ActivityCommentViewSet(viewsets.ModelViewSet):
    queryset = ActivityComment.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ActivityCommentCreateSerializer
        return ActivityCommentSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)