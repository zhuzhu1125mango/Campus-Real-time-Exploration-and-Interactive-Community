import logging
import os
import threading
import time

from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated, AllowAny

from .models import ChatMessage
from .serializers import ChatMessageSerializer

User = get_user_model()
logger = logging.getLogger(__name__)

REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')


class RecentActivePresence:
    """
    基于 Redis 的"最近活跃"用户统计。

    使用 Redis Sorted Set 记录用户最近一次活跃时间，窗口期内的用户即为"在线"。
    当 Redis 不可用时，回退到线程安全的内存字典（开发环境单进程）。

    相比内存集合的优势：
    - 支持多 worker / 多实例部署
    - 同一用户多连接不会误删，以最近活跃时间为准
    - 连接异常断开时，用户会在窗口过期后自动下线
    """

    KEY = "chat:recent_active_users"
    WINDOW_SECONDS = 300  # 5 分钟活跃窗口

    _redis = None
    _redis_available = None
    _lock = threading.Lock()
    _fallback_users = {}

    @classmethod
    def _get_redis(cls):
        if cls._redis_available is False:
            return None
        if cls._redis is not None:
            return cls._redis
        try:
            import redis
            cls._redis = redis.from_url(REDIS_URL, decode_responses=True)
            cls._redis.ping()
            cls._redis_available = True
            logger.info("Redis 最近活跃用户统计已启用")
            return cls._redis
        except Exception as e:
            logger.warning("Redis 不可用，回退到内存最近活跃用户统计: %s", e)
            cls._redis_available = False
            return None

    @classmethod
    def mark_active(cls, user_id):
        """标记用户为活跃（连接、心跳、发消息时调用）。"""
        if user_id is None:
            return
        r = cls._get_redis()
        user_id = str(user_id)
        timestamp = time.time()
        if r:
            r.zadd(cls.KEY, {user_id: timestamp})
        else:
            with cls._lock:
                cls._fallback_users[user_id] = timestamp

    @classmethod
    def count(cls):
        """返回窗口期内的活跃用户数量，并清理过期记录。"""
        r = cls._get_redis()
        cutoff = time.time() - cls.WINDOW_SECONDS
        if r:
            r.zremrangebyscore(cls.KEY, 0, cutoff)
            return r.zcard(cls.KEY) or 0
        with cls._lock:
            inactive = [
                uid for uid, ts in cls._fallback_users.items()
                if ts < cutoff
            ]
            for uid in inactive:
                cls._fallback_users.pop(uid, None)
            return len(cls._fallback_users) or 0


presence = RecentActivePresence()

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
    """获取最近活跃用户数量"""
    return Response({
        "count": presence.count() or 1,
        "metric": "recently_active",
        "window_seconds": presence.WINDOW_SECONDS,
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_message(request):
    """发送聊天消息（HTTP接口），与 WebSocket 一致要求登录"""
    content = request.data.get('content', '').strip()
    if not content:
        return Response({"error": "消息内容不能为空"}, status=400)

    # 限制消息长度
    if len(content) > 1000:
        return Response({"error": "消息内容过长，请限制在1000字符以内"}, status=400)

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
        content=content,
        user=user
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
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
        else:
            serializer.save()
