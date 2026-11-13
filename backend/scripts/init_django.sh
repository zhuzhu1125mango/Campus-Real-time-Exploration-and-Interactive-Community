#!/bin/bash
# Django 初始化任务：数据库迁移、静态文件收集、重建搜索索引。
# 作为独立的 docker-compose init 服务运行一次，避免多 HTTP 实例同时执行迁移。

set -euo pipefail

cd "$(dirname "$0")/.."

# 加载环境变量
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

export DJANGO_SETTINGS_MODULE="config.settings"

echo "[init] 执行数据库迁移..."
uv run python manage.py migrate --noinput

echo "[init] 收集静态文件..."
uv run python manage.py collectstatic --noinput

echo "[init] 重建搜索索引..."
uv run python manage.py rebuild_search_index --delete

echo "[init] Django 初始化完成。"
