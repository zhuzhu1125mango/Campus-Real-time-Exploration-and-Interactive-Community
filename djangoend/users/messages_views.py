from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q

from .messages import Message
from .messages_serializers import (
    MessageSerializer, 
    MessageCreateSerializer, 
    ConversationSerializer,
    ConversationDetailSerializer
)
from .notification_sender import send_notification_to_user


class MessageViewSet(viewsets.ModelViewSet):
    """
    私信视图集
    """
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # 获取当前用户发送和接收的消息
        return Message.objects.filter(
            Q(sender=self.request.user) | Q(receiver=self.request.user)
        )
    
    def get_serializer_class(self):
        if self.action == 'create':
            return MessageCreateSerializer
        return self.serializer_class
    
    def perform_create(self, serializer):
        message = serializer.save()
        # 发送私信通知
        send_notification_to_user(
            message.receiver,
            '新私信',
            f'{message.sender.username} 给您发送了一条私信',
            'message',
            f'/chat/{message.sender.id}'
        )
    
    @action(detail=False, methods=['get'])
    def conversations(self, request):
        """
        获取用户的所有对话
        """
        conversations = Message.get_conversations(request.user)
        serializer = ConversationSerializer(conversations, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def conversation(self, request):
        """
        获取与特定用户的对话
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
            other_user = User.objects.get(id=user_id)
            
            # 获取对话消息
            messages = Message.get_conversation(request.user, other_user)
            
            # 标记来自对方的未读消息为已读
            Message.mark_all_as_read(request.user, other_user)
            
            # 构建响应数据
            conversation_data = {
                'user': other_user,
                'messages': messages,
                'unread_count': 0  # 因为已经标记为已读
            }
            
            serializer = ConversationDetailSerializer(conversation_data)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response(
                {'error': '用户不存在'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """
        获取未读消息数量
        """
        count = Message.get_unread_count(request.user)
        return Response({'unread_count': count})
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """
        将消息标记为已读
        """
        message = self.get_object()
        
        # 只有消息接收者可以标记为已读
        if message.receiver != request.user:
            return Response(
                {'error': '您不是该消息的接收者'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if message.mark_as_read():
            return Response(
                {'message': '消息已标记为已读'},
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {'error': '消息已经是已读状态'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """
        将来自特定用户的所有消息标记为已读
        """
        user_id = request.data.get('user_id')
        if not user_id:
            return Response(
                {'error': '缺少用户ID'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            other_user = User.objects.get(id=user_id)
            
            Message.mark_all_as_read(request.user, other_user)
            return Response(
                {'message': '所有消息已标记为已读'},
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response(
                {'error': '用户不存在'},
                status=status.HTTP_404_NOT_FOUND
            )
