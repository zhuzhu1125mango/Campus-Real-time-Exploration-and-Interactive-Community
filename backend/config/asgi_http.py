"""
HTTP 专用 ASGI 入口。

只暴露 Django HTTP 应用，不加载 Channels WebSocket 路由。
用于生产环境独立部署 HTTP API 服务，避免 WebSocket 长连接与 HTTP
短请求竞争同进程内的协程/线程资源。

启动方式：
    gunicorn config.asgi_http:application \
        --bind 0.0.0.0:8000 \
        --worker-class uvicorn.workers.UvicornWorker
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_asgi_application()
