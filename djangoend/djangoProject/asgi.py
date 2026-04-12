"""
ASGI config for djangoProject project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject.settings')
django.setup()

# 导入聊天路由和中间件（必须在django.setup()之后）
import chat.routing
from chat.middleware import TokenAuthMiddleware

# 初始化Django ASGI应用
django_asgi_app = get_asgi_application()

# 配置协议路由 - 使用自定义的TokenAuthMiddleware
application = ProtocolTypeRouter({
    # HTTP请求由Django处理
    "http": django_asgi_app,
    # WebSocket请求由Channels处理，使用自定义的TokenAuthMiddleware
    "websocket": TokenAuthMiddleware(
        URLRouter(
            chat.routing.websocket_urlpatterns
        )
    ),
}) 