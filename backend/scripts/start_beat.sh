#!/bin/bash
# 启动 Celery Beat（定时任务调度器）

set -euo pipefail

cd "$(dirname "$0")/.."

# 加载环境变量
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

export DJANGO_SETTINGS_MODULE="config.settings"

exec uv run celery -A config beat \
    --loglevel info
