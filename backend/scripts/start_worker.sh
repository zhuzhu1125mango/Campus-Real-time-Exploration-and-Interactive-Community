#!/bin/bash
# 启动 Celery Worker

set -euo pipefail

cd "$(dirname "$0")/.."

# 加载环境变量
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

export DJANGO_SETTINGS_MODULE="config.settings"

exec uv run celery -A config worker \
    --loglevel info \
    --concurrency "${CELERY_CONCURRENCY:-2}" \
    --pool prefork
