#!/bin/bash
# 启动 Django HTTP API 服务（独立 ASGI 入口）

set -euo pipefail

cd "$(dirname "$0")/.."

# 加载环境变量
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

export DJANGO_SETTINGS_MODULE="config.settings"

# 注意：迁移、collectstatic、重建索引已由独立的 django-init 服务执行，
# 本脚本仅负责启动 HTTP 服务，避免多实例启动时重复执行迁移。

# 启动 HTTP 服务
exec uv run gunicorn config.asgi_http:application \
    --bind "${HTTP_BIND:-0.0.0.0:8000}" \
    --workers "${HTTP_WORKERS:-4}" \
    --worker-class uvicorn.workers.UvicornWorker \
    --timeout 300 \
    --access-logfile - \
    --error-logfile -
