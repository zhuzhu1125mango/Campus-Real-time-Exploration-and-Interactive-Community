#!/bin/bash
# 启动 Django WebSocket 服务（独立 ASGI 入口）

set -euo pipefail

cd "$(dirname "$0")/.."

# 加载环境变量
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

export DJANGO_SETTINGS_MODULE="config.settings"

# 启动 WebSocket 服务
exec uv run uvicorn config.asgi_ws:application \
    --host "${WS_HOST:-0.0.0.0}" \
    --port "${WS_PORT:-8001}" \
    --ws websockets \
    --loop uvloop \
    --log-level info
