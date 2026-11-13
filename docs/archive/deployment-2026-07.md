# 部署说明

本文档覆盖开发环境、Docker Compose 一键部署以及生产环境加固部署。

## 1. 环境准备

### 1.1 系统要求

- Windows 10/11 或 Linux/macOS
- Python 3.12.*
- Node.js 18+
- pnpm
- uv
- MySQL 8.0+（生产环境）
- Redis 7+（推荐拆分为 WebSocket 与业务缓存两个实例）
- RabbitMQ 3.8+（Celery Broker）
- Elasticsearch 8.x + analysis-ik 中文分词插件（可选，未启动时搜索降级为 MySQL LIKE）
- Docker & Docker Compose（容器化部署）

### 1.2 依赖安装

#### 后端依赖

项目使用 [uv](https://github.com/astral-sh/uv) 管理 Python 依赖：

```bash
cd backend
uv sync --frozen
```

如需开发依赖：

```bash
uv sync --frozen --with-dev
```

> 生产环境镜像通过 `uv sync --frozen --no-dev --extra prod` 安装。

#### H5 前端依赖

项目使用 [pnpm](https://pnpm.io/) 管理前端依赖：

```bash
cd frontend
pnpm install
```

## 2. 环境变量配置

### 2.1 本地开发

在 `backend/` 目录下创建 `.env` 文件，参考 [`backend/.env.example`](../../backend/.env.example)。`start_server.py` 与各启动脚本会自动加载该文件。

### 2.2 Docker Compose 生产部署

在项目根目录创建 `.env` 文件，参考根目录 [`.env.example`](../../.env.example)。该文件除包含 Django、数据库、Redis、RabbitMQ、Elasticsearch 等配置外，还包含 Nginx 生产域名与证书路径变量。

核心环境变量示例：

```env
# Django 设置
# 生产环境必须替换为强随机密钥，建议 64 位以上
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com

# 数据库配置（仅支持 MySQL 8.0+）
DB_ENGINE=django.db.backends.mysql
DB_NAME=university_exchange
DB_USER=root
DB_PASSWORD=123456
DB_HOST=127.0.0.1
DB_PORT=3306

# 从库配置（生产环境启用读写分离时填写）
# 不填写 DB_REPLICA_HOST 时，读请求会自动回退到主库
DB_REPLICA_NAME=university_exchange
DB_REPLICA_USER=root
DB_REPLICA_PASSWORD=123456
DB_REPLICA_HOST=
DB_REPLICA_PORT=3306

# CORS 设置
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:8080,https://your-frontend-domain.com

# Redis 配置（兼容旧版 REDIS_URL）
# Docker 基础设施：redis-ws 映射到宿主机 6379，redis-cache 映射到宿主机 6380
REDIS_URL=redis://127.0.0.1:6379/1
REDIS_WS_URL=redis://127.0.0.1:6379/0
REDIS_CACHE_URL=redis://127.0.0.1:6380/1

# RabbitMQ 配置（Celery Broker）
RABBITMQ_URL=amqp://campus:campus@127.0.0.1:5672//

# Celery 配置
CELERY_BROKER_URL=amqp://campus:campus@127.0.0.1:5672//
CELERY_RESULT_BACKEND=redis://127.0.0.1:6380/3

# 媒体和静态文件
MEDIA_URL=/media/
STATIC_URL=/static/

# Elasticsearch 配置
ELASTICSEARCH_HOSTS=http://127.0.0.1:9200
ELASTICSEARCH_TIMEOUT=10
# ES 不可用时是否降级为 MySQL LIKE 搜索
ELASTICSEARCH_FALLBACK_TO_DB=True
# 索引名称前缀
ELASTICSEARCH_INDEX_PREFIX=campus
```

> **安全警告**：`DJANGO_SECRET_KEY` 生产环境不可使用示例值，建议使用 `openssl rand -base64 64` 或 Python `secrets.token_urlsafe(64)` 生成。

## 3. 数据库配置

### 3.1 创建数据库

```sql
CREATE DATABASE university_exchange CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3.2 数据库迁移

```bash
cd backend
uv run python manage.py migrate
```

### 3.3 创建超级用户

```bash
uv run python manage.py createsuperuser
```

### 3.4 收集静态文件

```bash
uv run python manage.py collectstatic --noinput
```

### 3.5 读写分离（可选）

生产环境可配置 MySQL 从库：

1. 在 `.env` 中设置 `DB_REPLICA_HOST` 等从库连接信息。
2. `config/db_router.py` 会自动将读请求路由到从库，写请求路由到主库。
3. 未配置从库时，所有请求自动回退到主库。

## 4. Elasticsearch 初始化

### 4.1 启动 Elasticsearch

Docker Compose 已包含 ES 服务，使用自定义镜像内置 analysis-ik 分词插件：

```bash
docker compose up -d elasticsearch
```

### 4.2 全量重建索引

上线前必须执行全量灌数：

```bash
# 本地
cd backend
uv run python manage.py rebuild_search_index --delete

# Docker Compose
docker compose exec django-http uv run python manage.py rebuild_search_index --delete
```

> `--delete` 会先删除已有索引再重建；日常增量更新由 `search/signals.py` 通过 Celery 异步完成。

### 4.3 指定模型重建

```bash
uv run python manage.py rebuild_search_index --model schools.School --delete
```

## 5. 后端部署

### 5.1 开发环境

```bash
cd backend
python start_server.py
```

默认启动在 `http://0.0.0.0:8000`，使用 uvicorn 支持 WebSocket 热重载。

同时需要启动 Celery Worker：

```bash
cd backend
uv run celery -A config worker --loglevel info --concurrency 2
```

> 注意：WebSocket 连接需要 ASGI 服务器，必须使用 uvicorn 或 daphne，不能使用 Django 原生 `runserver`。

### 5.2 生产环境：ASGI HTTP / WebSocket 分离

为避免 WebSocket 长连接与 HTTP 短请求竞争资源，生产环境使用独立的 ASGI 入口：

#### HTTP 服务

```bash
cd backend
./scripts/start_http.sh
```

底层命令：

```bash
uv run gunicorn config.asgi_http:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --timeout 300
```

#### WebSocket 服务

```bash
cd backend
./scripts/start_ws.sh
```

底层命令：

```bash
uv run uvicorn config.asgi_ws:application \
    --host 0.0.0.0 --port 8001 \
    --ws websockets \
    --loop uvloop
```

#### Celery Worker

```bash
cd backend
./scripts/start_worker.sh
```

底层命令：

```bash
uv run celery -A config worker --loglevel info --concurrency 2 --pool prefork
```

#### Celery Beat（定时任务，可选）

```bash
cd backend
./scripts/start_beat.sh
```

### 5.3 使用 systemd 服务（Linux）

创建 `/etc/systemd/system/campus-http.service`：

```ini
[Unit]
Description=Campus Community Django HTTP Service
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/path/to/Campus-Real-time-Exploration-and-Interactive-Community/backend
ExecStart=/path/to/Campus-Real-time-Exploration-and-Interactive-Community/backend/scripts/start_http.sh
Restart=always

[Install]
WantedBy=multi-user.target
```

创建 `/etc/systemd/system/campus-ws.service`：

```ini
[Unit]
Description=Campus Community Django WebSocket Service
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/path/to/Campus-Real-time-Exploration-and-Interactive-Community/backend
ExecStart=/path/to/Campus-Real-time-Exploration-and-Interactive-Community/backend/scripts/start_ws.sh
Restart=always

[Install]
WantedBy=multi-user.target
```

创建 `/etc/systemd/system/campus-worker.service`：

```ini
[Unit]
Description=Campus Community Celery Worker
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/path/to/Campus-Real-time-Exploration-and-Interactive-Community/backend
ExecStart=/path/to/Campus-Real-time-Exploration-and-Interactive-Community/backend/scripts/start_worker.sh
Restart=always

[Install]
WantedBy=multi-user.target
```

启用并启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable campus-http campus-ws campus-worker
sudo systemctl start campus-http campus-ws campus-worker
```

## 6. H5 前端部署

### 6.1 配置 API 基础 URL

编辑 `frontend/.env.production`：

```env
VITE_API_BASE_URL=https://api.example.com
VITE_WS_BASE_URL=wss://api.example.com
VITE_UPLOAD_URL=https://api.example.com/media
VITE_STATIC_URL=https://api.example.com/static
```

### 6.2 构建生产版本

```bash
cd frontend
pnpm build
```

构建结果将生成在 `frontend/dist` 目录。Vite 已配置 `manualChunks` 拆分大依赖（echarts、element-plus、leaflet 等），并采用 ECharts 按需引入。

### 6.3 开发服务器

```bash
cd frontend
pnpm dev
```

默认启动在 `http://localhost:5173`。

## 7. 微信小程序部署

1. 使用 HBuilderX 打开 `mp-weixin/`。
2. 配置 `manifest.json` 中的微信小程序 AppID。
3. 配置 `mp-weixin/.env` 中的 `API_BASE_URL`（使用环境变量，不可硬编码内网 IP 和 HTTP）。
4. 点击「发行」→「小程序-微信」，生成到 `unpackage/dist/build/mp-weixin`。
5. 使用微信开发者工具上传并提交审核。

## 8. Docker Compose 部署

### 8.1 开发/测试环境

```bash
docker compose up -d
```

将启动以下服务：

- MySQL 8.0（端口 3306）
- Redis WebSocket（端口 6379）
- Redis 缓存（端口 6380）
- RabbitMQ（端口 5672 / 管理界面 15672）
- Elasticsearch（端口 9200）
- Django HTTP（端口 8000）
- Django WebSocket（端口 8001）
- Celery Worker
- Nginx（端口 80）

### 8.2 生产环境

使用 `docker-compose.prod.yml` 覆盖生产配置：

```bash
# 1. 在项目根目录创建 .env，填写域名、证书路径、数据库密码、密钥等
#    可直接复制 .env.example 并修改
cp .env.example .env

# 2. 启动服务（Nginx 会在容器启动时通过 envsubst 渲染 HTTPS 配置）
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 3. 初始化 Elasticsearch 索引（已由 django-init 服务自动执行，如失败可手动执行）
docker compose exec django-http uv run python manage.py rebuild_search_index --delete
```

生产覆盖配置主要变更：

- 关闭 MySQL / Redis / RabbitMQ / Elasticsearch 对外端口暴露，仅保留 Nginx 80/443。
- 新增独立的 `django-init` 服务，负责数据库迁移、静态文件收集、重建搜索索引，避免多 HTTP 实例重复执行迁移。
- Nginx 使用 `nginx.prod.conf.template` 模板，启动时通过环境变量渲染为最终配置。
- HTTP / WebSocket / Worker 服务不暴露端口，仅通过内部网络通信。

### 8.3 Docker Compose 配置校验

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml config
```

## 9. Nginx 配置

### 9.1 生产 HTTPS 配置

使用 `nginx/nginx.prod.conf.template` 模板，容器启动时通过 `envsubst` 渲染为 `/etc/nginx/conf.d/default.conf`。关键配置包括：

- HTTP 80 端口强制跳转 HTTPS。
- HTTPS 443 端口提供 API、WebSocket、静态/媒体文件服务。
- WebSocket `/ws/` 转发到独立的 `django-ws:8001`。
- 其余请求转发到 `django-http:8000`。
- 安全响应头：X-Content-Type-Options、X-Frame-Options、X-XSS-Protection、Referrer-Policy。

模板中使用以下环境变量，需在 `.env` 中配置：

| 变量 | 说明 | 示例 |
|---|---|---|
| `PROD_DOMAIN` | 实际域名 | `campus.example.com` |
| `SSL_CERT_PATH` | 容器内证书路径 | `/etc/nginx/ssl/fullchain.pem` |
| `SSL_KEY_PATH` | 容器内私钥路径 | `/etc/nginx/ssl/privkey.pem` |
| `SSL_CERT_HOST_PATH` | 宿主机证书挂载路径 | `/etc/letsencrypt/live/campus.example.com/fullchain.pem` |
| `SSL_KEY_HOST_PATH` | 宿主机私钥挂载路径 | `/etc/letsencrypt/live/campus.example.com/privkey.pem` |

> 使用 Let's Encrypt 时，证书路径通常为 `/etc/letsencrypt/live/<domain>/fullchain.pem` 与 `/etc/letsencrypt/live/<domain>/privkey.pem`。

### 9.2 启用配置（非容器化部署）

非容器化部署时，需要手动使用 `envsubst` 渲染模板：

```bash
export PROD_DOMAIN=campus.example.com
export SSL_CERT_PATH=/etc/letsencrypt/live/campus.example.com/fullchain.pem
export SSL_KEY_PATH=/etc/letsencrypt/live/campus.example.com/privkey.pem

envsubst '$PROD_DOMAIN $SSL_CERT_PATH $SSL_KEY_PATH' \
    < /path/to/Campus-Real-time-Exploration-and-Interactive-Community/nginx/nginx.prod.conf.template \
    > /etc/nginx/sites-available/campus-app

sudo ln -s /etc/nginx/sites-available/campus-app /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 10. 缓存配置

### 10.1 Redis 缓存

`config/settings.py` 中已配置：

- 开发环境：LocMemCache
- 生产环境：django-redis，使用 `REDIS_CACHE_URL`

统一缓存工具层 `core/cache_utils.py` 提供：

- 分层 TTL：hot（600s）/ medium（300s）/ cold（3600s）
- 空值缓存：防止缓存穿透
- 互斥锁：防止缓存击穿
- 随机抖动：防止缓存雪崩
- 版本号失效：一键失效命名空间
- gzip 压缩：大 value 自动压缩
- 异常降级：Redis 异常时不阻塞业务

### 10.2 前端缓存策略

Vite 构建产物已包含 hash，Nginx 配置长期缓存静态资源。

## 11. 安全配置

### 11.1 生产环境设置

- 设置 `DEBUG = False`
- 配置 `ALLOWED_HOSTS`
- 使用 HTTPS
- 配置 CSRF 和 CORS 白名单
- `DJANGO_SECRET_KEY` 使用强随机密钥
- 数据库密码、Redis 密码、RabbitMQ 密码使用强密码

### 11.2 安全头

Nginx 已配置：

```nginx
add_header X-Content-Type-Options nosniff always;
add_header X-Frame-Options DENY always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy strict-origin-when-cross-origin always;
```

Django 设置中已启用：

- `SECURE_CONTENT_TYPE_NOSNIFF = True`
- `SECURE_BROWSER_XSS_FILTER = True`
- `X_FRAME_OPTIONS = 'DENY'`
- `CSRF_COOKIE_SECURE = True`（生产环境）
- `SESSION_COOKIE_SECURE = True`（生产环境）

### 11.3 H5 v-html XSS 防护

前端 `frontend/src/utils/xss.ts` 提供 XSS 过滤工具，所有 `v-html` 渲染必须使用过滤后的内容。

## 12. 监控与维护

### 12.1 服务状态检查

```bash
# systemd 部署
systemctl status campus-http
systemctl status campus-ws
systemctl status campus-worker
systemctl status nginx

# Docker Compose 部署
docker compose ps
docker compose logs -f django-http
docker compose logs -f django-ws
docker compose logs -f celery-worker
```

### 12.2 日志监控

```bash
# systemd
tail -f /var/log/campus-app/error.log
tail -f /var/log/nginx/error.log

# Docker Compose
docker compose logs -f django-http
docker compose logs -f celery-worker
```

### 12.3 定期维护

- 备份数据库
- 更新依赖（`uv sync` 和 `pnpm update`）
- 安全扫描
- 检查 Celery 任务队列积压
- 监控 Elasticsearch 集群健康状态

## 13. 常见问题

### 13.1 端口冲突

修改 `.env` 或 Docker Compose 中的端口映射。

### 13.2 数据库连接失败

检查数据库服务是否启动，用户名和密码是否正确，以及 `.env` 中的 `DB_HOST`、`DB_NAME`、`DB_USER`、`DB_PASSWORD` 配置。

### 13.3 CORS 错误

检查 `backend/config/settings.py` 中的 `CORS_ALLOWED_ORIGINS` 配置。

### 13.4 WebSocket 连接失败

- 确认使用 uvicorn/daphne 启动 ASGI 应用，而非 Django `runserver`。
- 检查 Nginx 的 WebSocket 代理配置（`Upgrade` 和 `Connection` 头）。
- 确认 `ALLOWED_HOSTS` 和 CORS 配置包含前端域名。
- 生产环境确认 `/ws/` 路由转发到独立的 WebSocket 服务端口。

### 13.5 Elasticsearch 不可用

搜索会自动降级为 MySQL LIKE，但建议尽快恢复 ES 服务并执行 `rebuild_search_index`。

### 13.6 Celery 任务未执行

- 确认 RabbitMQ/Redis Broker 正常启动
- 确认 Celery Worker 已启动
- 检查 `CELERY_BROKER_URL` 配置是否正确

## 14. 服务状态检查

- 后端 API 健康检查：`GET https://api.example.com/api/schools/test-connection/`
- H5 前端：`https://example.com`
- 后端服务：`https://api.example.com`
- WebSocket：`wss://api.example.com/ws/chat/public/`
