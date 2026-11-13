"""
WebSocket 专用 ASGI 入口。

只暴露 Channels WebSocket 路由，由 TokenAuthMiddleware 完成 JWT 认证。
用于生产环境独立部署 WebSocket 长连接服务，可横向扩展。

启动方式：
    uvicorn config.asgi_ws:application \
        --host 0.0.0.0 --port 8001 \
        --ws websockets \
        --loop uvloop
"""

import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import chat.routing
from chat.middleware import TokenAuthMiddleware

application = ProtocolTypeRouter({
    # WebSocket 请求由 Channels 处理，使用自定义的 TokenAuthMiddleware
    "websocket": TokenAuthMiddleware(
        URLRouter(
            chat.routing.websocket_urlpatterns
        )
    ),
})
