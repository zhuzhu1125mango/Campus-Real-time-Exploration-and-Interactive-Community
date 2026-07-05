#!/bin/bash
# 生产环境启动脚本
# 使用 Gunicorn + Uvicorn Worker 启动 ASGI 应用

set -euo pipefail

# 进入项目目录
cd "$(dirname "$0")"

# 加载环境变量（如果存在 .env 文件）
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# 确保日志目录存在
mkdir -p /var/log/campus-app

# 设置环境变量
export DJANGO_SETTINGS_MODULE="config.settings"

# 启动服务器
exec .venv/bin/gunicorn config.asgi:application \
    --bind "${BIND:-0.0.0.0:8000}" \
    --workers "${WORKERS:-4}" \
    --worker-class uvicorn.workers.UvicornWorker \
    --timeout 300 \
    --access-logfile /var/log/campus-app/access.log \
    --error-logfile /var/log/campus-app/error.log
