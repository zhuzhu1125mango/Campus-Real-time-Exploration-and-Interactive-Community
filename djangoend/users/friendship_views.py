from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q

from .friendship import FriendRequest, Friend
from .friendship_serializers import (
    FriendRequestSerializer, 
    FriendRequestCreateSerializer, 
    FriendListSerializer,
    UserSerializer
)
from .notification_sender import send_notification_to_user


class FriendRequestViewSet(viewsets.ModelViewSet):
    """
    好友请求视图集
    """
    serializer_class = FriendRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # 获取当前用户发送和接收的好友请求
        return FriendRequest.objects.filter(
            Q(sender=self.request.user) | Q(receiver=self.request.user)
        )
    
    def get_serializer_class(self):
        if self.action == 'create':
            return FriendRequestCreateSerializer
        return self.serializer_class
    
    def perform_create(self, serializer):
        friend_request = serializer.save()
        # 发送好友请求通知
        send_notification_to_user(
            friend_request.receiver,
            '好友请求',
            f'{friend_request.sender.username} 向您发送了好友请求',
            'interaction',
            f'/user/{friend_request.sender.id}'
        )
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """
        接受好友请求
        """
        friend_request = self.get_object()
        
        # 只有请求接收者可以接受
        if friend_request.receiver != request.user:
            return Response(
                {'error': '您不是该请求的接收者'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if friend_request.accept():
            # 发送好友请求被接受的通知
            send_notification_to_user(
                friend_request.sender,
                '好友请求已接受',
                f'{friend_request.receiver.username} 接受了您的好友请求',
                'interaction',
                f'/user/{friend_request.receiver.id}'
            )
            return Response(
                {'message': '好友请求已接受'},
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {'error': '好友请求状态错误'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """
        拒绝好友请求
        """
        friend_request = self.get_object()
        
        # 只有请求接收者可以拒绝
        if friend_request.receiver != request.user:
            return Response(
                {'error': '您不是该请求的接收者'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if friend_request.reject():
            return Response(
                {'message': '好友请求已拒绝'},
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {'error': '好友请求状态错误'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def received(self, request):
        """
        获取收到的好友请求
        """
        queryset = self.get_queryset().filter(receiver=request.user, status='pending')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def sent(self, request):
        """
        获取发送的好友请求
        """
        queryset = self.get_queryset().filter(sender=request.user)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class FriendViewSet(viewsets.ViewSet):
    """
    好友关系视图集
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def friend_list(self, request):
        """
        获取好友列表
        """
        friends = Friend.get_friends(request.user)
        serializer = UserSerializer(friends, many=True)
        return Response({
            'friends': serializer.data,
            'count': len(friends)
        })
    
    @action(detail=False, methods=['post'])
    def remove(self, request):
        """
        移除好友
        """
        friend_id = request.data.get('friend_id')
        if not friend_id:
            return Response(
                {'error': '缺少好友ID'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            friend = User.objects.get(id=friend_id)
            
            if Friend.remove_friend(request.user, friend):
                # 发送好友被移除的通知
                send_notification_to_user(
                    friend,
                    '好友关系已解除',
                    f'{request.user.username} 已将您从好友列表中移除',
                    'interaction'
                )
                return Response(
                    {'message': '好友已移除'},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {'error': '移除好友失败'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except User.DoesNotExist:
            return Response(
                {'error': '用户不存在'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def check(self, request):
        """
        检查两个用户是否是好友
        """
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response(
                {'error': '缺少用户ID'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(id=user_id)
            is_friend = Friend.is_friend(request.user, user)
            return Response({'is_friend': is_friend})
        except User.DoesNotExist:
            return Response(
                {'error': '用户不存在'},
                status=status.HTTP_404_NOT_FOUND
            )
