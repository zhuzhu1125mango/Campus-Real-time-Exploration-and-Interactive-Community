from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator

from .messages import Message
from .messages_serializers import (
    MessageSerializer,
    MessageCreateSerializer,
    ConversationSerializer,
    ConversationDetailSerializer,
    UserSerializer
)
from .notification_sender import send_notification_to_user
from .websocket_service import websocket_service

User = get_user_model()


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
        data = serializer.validated_data
        receiver = data.get('receiver')
        sender = self.request.user
        content = data.get('content', '')
        
        # 保存消息到数据库
        message = Message.objects.create(
            sender=sender,
            receiver=receiver,
            content=content
        )
        
        # 发送私信通知
        send_notification_to_user(
            receiver,
            '新私信',
            f'{sender.username} 给您发送了一条私信',
            'message',
            f'/chat/{sender.id}'
        )
        
        # 通过WebSocket推送消息给接收者
        websocket_service.send_private_message(sender, receiver, message)
        
        return message
    
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

        支持分页查询：?user_id=<id>&page=<page>&page_size=<size>
        未提供 page 时返回全部消息（兼容旧逻辑）。
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
            user_id_int = int(user_id)
            if user_id_int <= 0:
                raise ValueError('用户ID必须为正整数')
            other_user = User.objects.get(id=user_id_int)

            # 获取对话消息（按创建时间倒序，便于分页加载最新消息）
            # 使用 select_related 避免 N+1 查询
            messages_qs = Message.objects.select_related('sender', 'receiver').filter(
                Q(sender=request.user, receiver=other_user) |
                Q(sender=other_user, receiver=request.user)
            ).order_by('-created_at')

            # 标记来自对方的未读消息为已读
            Message.mark_all_as_read(request.user, other_user)

            page = request.query_params.get('page')
            page_size = request.query_params.get('page_size', 20)

            if page is not None:
                try:
                    page = int(page)
                    page_size = int(page_size)
                except ValueError:
                    return Response(
                        {'error': 'page 和 page_size 必须是整数'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                paginator = Paginator(messages_qs, page_size)
                page_obj = paginator.get_page(page)
                # 返回给前端时恢复升序，便于正序渲染
                messages = list(page_obj.object_list)[::-1]
                return Response({
                    'user': UserSerializer(other_user).data,
                    'messages': MessageSerializer(messages, many=True).data,
                    'unread_count': 0,
                    'count': paginator.count,
                    'next': page_obj.next_page_number() if page_obj.has_next() else None,
                    'previous': page_obj.previous_page_number() if page_obj.has_previous() else None,
                })

            # 未分页：返回全部消息（升序，兼容旧逻辑）
            messages = messages_qs.order_by('created_at')

            # 构建响应数据
            conversation_data = {
                'user': other_user,
                'messages': messages,
                'unread_count': 0  # 因为已经标记为已读
            }

            serializer = ConversationDetailSerializer(conversation_data)
            return Response(serializer.data)
        except (User.DoesNotExist, ValueError):
            return Response(
                {'error': '用户不存在或用户ID无效'},
                status=status.HTTP_400_BAD_REQUEST
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
    
    @action(detail=False, methods=['get', 'post'], url_path='(?P<user_id>[^/.]+)')
    def user_messages(self, request, user_id=None):
        """
        获取与特定用户的消息列表（GET）或发送消息（POST）
        """
        try:
            other_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': '用户不存在'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if request.method == 'GET':
            # 获取消息列表，使用 select_related 避免 N+1 查询
            messages = Message.objects.select_related('sender', 'receiver').filter(
                Q(sender=request.user, receiver=other_user) |
                Q(sender=other_user, receiver=request.user)
            ).order_by('created_at')
            serializer = MessageSerializer(messages, many=True)
            return Response(serializer.data)
        elif request.method == 'POST':
            # 发送消息
            content = request.data.get('content', '')
            if not content.strip():
                return Response(
                    {'error': '消息内容不能为空'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            message = Message.objects.create(
                sender=request.user,
                receiver=other_user,
                content=content.strip()
            )
            
            # 发送私信通知
            send_notification_to_user(
                other_user,
                '新私信',
                f'{request.user.username} 给您发送了一条私信',
                'message',
                f'/chat/{request.user.id}'
            )
            
            # 通过WebSocket推送消息
            websocket_service.send_private_message(request.user, other_user, message)
            
            serializer = MessageSerializer(message)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'], url_path='(?P<user_id>[^/.]+)/mark_read')
    def mark_user_messages_read(self, request, user_id=None):
        """
        标记与特定用户的所有消息为已读
        """
        try:
            other_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': '用户不存在'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        Message.mark_all_as_read(request.user, other_user)
        return Response(
            {'message': '所有消息已标记为已读'},
            status=status.HTTP_200_OK
        )
