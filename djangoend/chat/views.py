from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from .models import ChatMessage
from .serializers import ChatMessageSerializer
from django.contrib.auth import get_user_model
import asyncio
from rest_framework.permissions import IsAuthenticated, AllowAny
import logging
from django.http import JsonResponse

User = get_user_model()
logger = logging.getLogger(__name__)

# 在线用户集合（简化实现）
online_users = set()

# API视图函数

@api_view(['GET'])
@permission_classes([AllowAny])
def health(request):
    """健康检查API端点"""
    return Response({"status": "ok"})

@api_view(['GET'])
@permission_classes([AllowAny])
def recent_messages(request):
    """获取最近的聊天消息"""
    try:
        messages = ChatMessage.objects.all().order_by('-created_at')[:50]
        serializer = ChatMessageSerializer(messages, many=True)
        return Response(serializer.data)
    except Exception as e:
        logger.error(f"获取历史消息出错: {str(e)}")
        return Response({"error": "获取消息失败"}, status=500)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_online_users(request):
    """获取在线用户数量"""
    return Response({"count": len(online_users) or 1})

@api_view(['POST'])
@permission_classes([AllowAny])  # 临时允许匿名访问
def send_message(request):
    """发送聊天消息（HTTP接口）"""
    content = request.data.get('content', '').strip()
    if not content:
        return Response({"error": "消息内容不能为空"}, status=400)
    
    # 限制消息长度
    if len(content) > 1000:
        return Response({"error": "消息内容过长，请限制在1000字符以内"}, status=400)
    
    # 根据用户是否已认证，设置消息属性
    if request.user.is_authenticated:
        user = request.user
        user_id = user.id
        username = user.username
        
        # 获取用户头像
        avatar = None
        if hasattr(user, 'avatar') and user.avatar:
            try:
                avatar = user.avatar.url
            except Exception:
                avatar = None
                
        # 创建消息记录
        message = ChatMessage.objects.create(
            user=user,
            content=content
        )
    else:
        # 匿名用户消息
        user_id = 0
        username = "游客"
        avatar = None
        
        # 创建消息记录
        message = ChatMessage.objects.create(
            content=content
        )
    
    # 广播给所有WebSocket客户端
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "chat",
        {
            "type": "chat_message",
            "message": content,
            "username": username,
            "user_id": user_id,
            "avatar": avatar,
            "time": message.created_at.isoformat()
        }
    )
    
    # 返回消息数据
    serializer = ChatMessageSerializer(message)
    return Response(serializer.data)

class ChatMessageViewSet(viewsets.ModelViewSet):
    """聊天消息API视图集"""
    queryset = ChatMessage.objects.all().order_by('-created_at')
    serializer_class = ChatMessageSerializer
    permission_classes = [AllowAny]  # 临时允许匿名访问
    
    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
        else:
            serializer.save()
