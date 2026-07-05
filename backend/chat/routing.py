from django.urls import re_path
from . import consumers

# WebSocket路由配置
# 注意：Channels 的 URLRouter 接收的 path 不含前导斜杠，正则不匹配 '/ws/...'
websocket_urlpatterns = [
    # 公共聊天室
    re_path(r'^ws/chat/public/?$', consumers.ChatConsumer.as_asgi()),
    # 私聊 - 支持用户ID作为参数
    re_path(r'^ws/chat/private/(?P<user_id>\d+)/?$', consumers.PrivateChatConsumer.as_asgi()),
] 