#!/bin/bash
"""
生产环境启动脚本
使用Gunicorn和Uvicorn启动应用
"""

# 进入项目目录
cd "$(dirname "$0")"

# 设置环境变量
export DJANGO_SETTINGS_MODULE="djangoProject.settings"

# 启动服务器
gunicorn djangoProject.asgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --timeout 300 \
    --access-logfile /var/log/campus-app/access.log \
    --error-logfile /var/log/campus-app/error.log
