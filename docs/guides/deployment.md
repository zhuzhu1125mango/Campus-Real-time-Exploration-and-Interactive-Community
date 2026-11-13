# 部署指南

本文覆盖三种部署方式：

1. 本地开发（宿主机跑前后端，Docker 跑基础设施）
2. Docker Compose 全容器部署（开发/联调）
3. Docker Compose 生产部署（Nginx + HTTPS + ASGI 分离）

## 1. 部署拓扑

```text
                    ┌──────────────┐
   Browser / 小程序 →│    Nginx     │ :80 / :443
                    └───┬──────┬───┘
                        │      │
              /api /media│      │/ws
                        ↓      ↓
                ┌──────────┐  ┌──────────┐
                │django-http│  │ django-ws│
                │  :8000    │  │  :8001   │
                └────┬─────┘  └────┬─────┘
                     └──────┬──────┘
                            ↓
        MySQL / Redis(WS) / Redis(Cache) / RabbitMQ / Elasticsearch
                            ↑
                     ┌──────────────┐
                     │celery-worker │
                     └──────────────┘
```

生产环境的关键原则：

- HTTP 与 WebSocket 使用独立 ASGI 入口，避免长连接与短请求竞争资源。
- 只有 Nginx 暴露 80/443，其余服务只在 `campus_network` 内互通。
- 数据库迁移、静态文件收集、ES 索引重建只由 `django-init` 执行一次。

## 2. 本地开发部署

### 2.1 基础设施

```bash
docker compose up -d mysql redis-ws redis-cache rabbitmq elasticsearch
```

### 2.2 后端

```bash
cd backend
cp .env.example .env
# 填写 DJANGO_SECRET_KEY、DB_*、REDIS_*、RABBITMQ_URL、ELASTICSEARCH_HOSTS
python start_server.py
```

宿主机直连地址：

- HTTP：`http://localhost:8000`
- WebSocket：`ws://localhost:8000/ws/chat/public/`

### 2.3 Celery

```bash
cd backend
uv run celery -A config worker --loglevel info --concurrency 2
```

### 2.4 前端

```bash
cd frontend
pnpm dev
```

访问 `http://localhost:5173`。

## 3. Docker Compose 全容器部署

```bash
# 根目录 .env
cp .env.example .env
# 必填：DJANGO_SECRET_KEY、DB_PASSWORD、RABBITMQ_PASSWORD、ALLOWED_HOSTS

docker compose up -d
```

服务与访问方式：

| 服务 | 容器端口 | 宿主机访问 |
|---|---|---|
| nginx | 80 | `http://localhost` |
| mysql | 3306 | 仅容器网络（prod） |
| redis-ws | 6379 | 仅容器网络（prod） |
| redis-cache | 6379 | 仅容器网络（prod） |
| rabbitmq | 5672 / 15672 | 仅容器网络（prod） |
| elasticsearch | 9200 | 仅容器网络（prod） |
| django-http | 8000 | 经 Nginx `/` |
| django-ws | 8001 | 经 Nginx `/ws/` |
| celery-worker | — | 无端口 |

> 全容器模式下请通过 `http://localhost/api/health/` 访问，不要直接访问 `:8000`，
> 因为 `docker-compose.yml` 未将 Django 端口映射到宿主机。

常用命令：

```bash
docker compose ps
docker compose logs -f django-http
docker compose logs -f django-ws
docker compose logs -f celery-worker
docker compose exec django-http uv run python manage.py createsuperuser
```

## 4. 生产部署

### 4.1 准备变量

根目录 `.env` 至少包含：

```env
DJANGO_SECRET_KEY=<64位以上强随机值>
DJANGO_DEBUG=False
ALLOWED_HOSTS=api.example.com,example.com

DB_NAME=university_exchange
DB_USER=campus
DB_PASSWORD=<强密码>

RABBITMQ_USER=campus
RABBITMQ_PASSWORD=<强密码>

PROD_DOMAIN=api.example.com
SSL_CERT_PATH=/etc/nginx/ssl/fullchain.pem
SSL_KEY_PATH=/etc/nginx/ssl/privkey.pem
SSL_CERT_HOST_PATH=/etc/letsencrypt/live/api.example.com/fullchain.pem
SSL_KEY_HOST_PATH=/etc/letsencrypt/live/api.example.com/privkey.pem
```

### 4.2 启动

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
```

启动顺序由 `depends_on` 控制：

1. MySQL、Redis、RabbitMQ、Elasticsearch 健康检查通过
2. `django-init` 执行迁移、collectstatic、`rebuild_search_index --delete`
3. `django-http`、`django-ws`、`celery-worker` 启动
4. Nginx 启动并渲染 HTTPS 配置

### 4.3 初始化服务环境变量

`docker-compose.prod.yml` 中的 `django-init` 不属于基础编排，因此需要显式声明环境变量。
当前已配置：

- `DJANGO_SECRET_KEY`、`DJANGO_DEBUG=False`、`ALLOWED_HOSTS`
- `DB_HOST=mysql`、`DB_NAME`、`DB_USER`、`DB_PASSWORD`
- `REDIS_CACHE_URL`、`REDIS_WS_URL`
- `CELERY_BROKER_URL`、`CELERY_RESULT_BACKEND`
- `ELASTICSEARCH_HOSTS`、`ELASTICSEARCH_FALLBACK_TO_DB`

修改 `django-http` 的环境变量时，应同步更新 `django-init`，避免初始化与运行环境不一致。

### 4.4 Nginx HTTPS

生产使用 `nginx/nginx.prod.conf.template`，容器启动时由 `nginx/entrypoint.sh`
通过 `envsubst` 渲染为 `/etc/nginx/conf.d/default.conf`。

模板中的变量：

| 变量 | 说明 |
|---|---|
| `PROD_DOMAIN` | `server_name` |
| `SSL_CERT_PATH` | 容器内证书路径 |
| `SSL_KEY_PATH` | 容器内私钥路径 |

渲染效果：

- 80 端口强制跳转 HTTPS
- 443 端口启用 HTTP/2
- `/ws/` 转发到 `django-ws:8001`
- `/static/`、`/media/` 由 Nginx 直接提供
- 其余请求转发到 `django-http:8000`
- 附加安全响应头

校验配置：

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml config
docker compose exec nginx nginx -t
```

## 5. 非容器化部署（systemd）

生产也可直接在宿主机运行三个进程：

```bash
cd backend
./scripts/start_http.sh    # gunicorn + uvicorn worker，:8000
./scripts/start_ws.sh      # uvicorn，:8001
./scripts/start_worker.sh  # celery worker
./scripts/start_beat.sh    # 可选，celery beat
```

systemd 单元示例：

```ini
[Unit]
Description=Campus HTTP Service
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/opt/campus/backend
ExecStart=/opt/campus/backend/scripts/start_http.sh
Restart=always

[Install]
WantedBy=multi-user.target
```

对 `campus-ws`、`campus-worker` 复制同样结构，分别替换 `ExecStart`。

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now campus-http campus-ws campus-worker
```

## 6. 数据库与静态资源

```bash
cd backend
uv run python manage.py migrate --noinput
uv run python manage.py collectstatic --noinput
uv run python manage.py createsuperuser
```

生产环境不要在每个 HTTP 实例启动时执行迁移，统一交给初始化任务。

## 7. Elasticsearch 初始化

```bash
# 宿主机
cd backend
uv run python manage.py rebuild_search_index --delete

# 容器
docker compose exec django-http uv run python manage.py rebuild_search_index --delete
```

只重建某个模型：

```bash
uv run python manage.py rebuild_search_index --model schools.School --delete
```

日常增量由 `search/signals.py` + Celery 异步完成。

## 8. H5 前端部署

```bash
cd frontend
pnpm install --frozen-lockfile
pnpm build
```

产物在 `frontend/dist/`。推荐由 Nginx 托管，并将 `/api`、`/ws`、`/media` 反向代理到后端。

生产必须确认：

- 使用 HTTPS/WSS
- `ALLOWED_HOSTS` 包含前端与 API 域名
- `CORS_ALLOWED_ORIGINS` 只包含可信域名
- 静态资源使用长期缓存（Vite 文件名带 hash）

## 9. 微信小程序发布

1. 配置 `mp-weixin/.env`：
   ```env
   VUE_APP_API_BASE_URL=https://api.example.com/api
   VUE_APP_WS_BASE_URL=wss://api.example.com/ws/chat
   ```
2. 在 `manifest.json` 填写 AppID。
3. HBuilderX：发行 → 小程序-微信。
4. 微信公众平台配置 request/socket 合法域名。
5. 微信开发者工具上传并提交审核。

## 10. 上线检查清单

- [ ] `DJANGO_SECRET_KEY` 为强随机值，未使用示例值
- [ ] `DJANGO_DEBUG=False`
- [ ] `ALLOWED_HOSTS`、`CORS_ALLOWED_ORIGINS` 正确
- [ ] 数据库、Redis、RabbitMQ 使用强密码
- [ ] 数据库迁移已执行
- [ ] `collectstatic` 已执行
- [ ] ES 索引已全量重建
- [ ] Celery Worker 正常运行
- [ ] WebSocket 公网可连接
- [ ] HTTPS 证书有效，80 自动跳转 443
- [ ] 前端 `/api`、`/ws`、`/media` 代理正确
- [ ] 小程序使用 HTTPS/WSS 且域名已备案
- [ ] 监控与日志可访问
