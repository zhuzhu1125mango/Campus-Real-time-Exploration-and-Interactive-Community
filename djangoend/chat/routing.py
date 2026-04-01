from django.urls import re_path
from . import consumers
from .middleware import TokenAuthMiddleware

# WebSocket路由配置
# 注意：使用单一路径以简化维护
websocket_urlpatterns = [
    # 使用可选尾部斜杠的单一路径
    re_path(r'ws/chat/?$', TokenAuthMiddleware(consumers.ChatConsumer.as_asgi())),
] 