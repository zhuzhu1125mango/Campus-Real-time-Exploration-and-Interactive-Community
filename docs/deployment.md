# 部署说明

## 1. 环境准备

### 1.1 系统要求

- Windows 10/11 或 Linux/macOS
- Python 3.12.*
- Node.js 18+
- pnpm
- uv
- MySQL 8.0+（生产环境）
- Redis（可选，用于缓存和 Channels 层）

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

#### H5 前端依赖

项目使用 [pnpm](https://pnpm.io/) 管理前端依赖：

```bash
cd frontend
pnpm install
```

## 2. 数据库配置

### 2.1 创建数据库

```sql
CREATE DATABASE campus_community CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2.2 配置数据库连接

在 `backend/` 目录下创建 `.env` 文件（可参考 `.env.example`）：

```env
# Django 设置
DJANGO_SETTINGS_MODULE=config.settings
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=False

# 数据库配置（仅支持 MySQL 8.0+）
DB_ENGINE=django.db.backends.mysql
DB_NAME=campus_community
DB_USER=username
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=3306

# 允许的主机
ALLOWED_HOSTS=localhost,127.0.0.1,example.com

# Redis 配置（推荐用于 Channels 和缓存）
REDIS_URL=redis://localhost:6379/0
```

### 2.3 数据库迁移

```bash
cd backend
uv run python manage.py makemigrations
uv run python manage.py migrate
```

### 2.4 创建超级用户

```bash
uv run python manage.py createsuperuser
```

### 2.5 收集静态文件

```bash
uv run python manage.py collectstatic --noinput
```

## 3. 后端部署

### 3.1 开发环境

```bash
cd backend
python start_server.py
```

默认启动在 `http://0.0.0.0:8000`，使用 uvicorn 支持 WebSocket 热重载。

### 3.2 生产环境

#### 使用 Uvicorn 直接启动

```bash
cd backend
uv run uvicorn config.asgi:application --host 0.0.0.0 --port 8000 --workers 4
```

> 注意：WebSocket 连接需要 ASGI 服务器，必须使用 uvicorn 或 daphne，不能使用 Django 原生 `runserver`。

#### 使用 systemd 服务（Linux）

创建 `/etc/systemd/system/campus-app.service`：

```ini
[Unit]
Description=Campus Community Django Application
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/path/to/Campus-Real-time-Exploration-and-Interactive-Community/backend
ExecStart=/path/to/backend/.venv/bin/uvicorn config.asgi:application \
    --host 127.0.0.1 \
    --port 8000 \
    --workers 4 \
    --access-logfile /var/log/campus-app/access.log \
    --error-logfile /var/log/campus-app/error.log

[Install]
WantedBy=multi-user.target
```

启用服务：

```bash
sudo mkdir -p /var/log/campus-app
sudo chown -R ubuntu:www-data /var/log/campus-app
sudo systemctl daemon-reload
sudo systemctl enable campus-app
sudo systemctl start campus-app
```

## 4. H5 前端部署

### 4.1 配置 API 基础 URL

编辑 `frontend/.env.production`：

```env
VITE_API_BASE_URL=https://api.example.com
VITE_WS_BASE_URL=wss://api.example.com
VITE_UPLOAD_URL=https://api.example.com/media
VITE_STATIC_URL=https://api.example.com/static
```

### 4.2 启动前端开发服务器

```bash
cd frontend
pnpm dev
```

默认启动在 `http://localhost:5173`。

### 4.3 构建生产版本

```bash
cd frontend
pnpm build
```

构建结果将生成在 `frontend/dist` 目录。

## 5. 微信小程序部署

1. 使用 HBuilderX 打开 `mp-weixin/`。
2. 配置 `manifest.json` 中的微信小程序 AppID。
3. 点击「发行」→「小程序-微信」，生成到 `unpackage/dist/build/mp-weixin`。
4. 使用微信开发者工具上传并提交审核。

## 6. Nginx 配置

### 6.1 安装 Nginx

```bash
sudo apt install nginx  # Ubuntu/Debian
```

### 6.2 配置文件

创建 `/etc/nginx/sites-available/campus-app`：

```nginx
upstream campus_app {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name example.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name example.com;

    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';

    location / {
        root /path/to/Campus-Real-time-Exploration-and-Interactive-Community/frontend/dist;
        try_files $uri $uri/ /index.html;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000";
    }

    location /api/ {
        proxy_pass http://campus_app;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 3600s;
    }

    location /ws/ {
        proxy_pass http://campus_app;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 3600s;
    }

    location /media/ {
        alias /path/to/Campus-Real-time-Exploration-and-Interactive-Community/backend/media/;
        expires 30d;
    }

    location /static/ {
        alias /path/to/Campus-Real-time-Exploration-and-Interactive-Community/backend/static/;
        expires 30d;
    }
}
```

### 6.3 启用配置

```bash
sudo ln -s /etc/nginx/sites-available/campus-app /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 7. CDN 集成

### 7.1 Cloudflare 配置

1. 登录 Cloudflare，添加域名。
2. 配置 DNS 记录指向服务器 IP。
3. 启用 CDN 加速。
4. 在 Nginx 中添加 Cloudflare IP 白名单：

```nginx
set_real_ip_from 103.21.244.0/22;
set_real_ip_from 103.22.200.0/22;
set_real_ip_from 103.31.4.0/22;
real_ip_header CF-Connecting-IP;
```

## 8. 缓存配置

### 8.1 Redis 缓存

在 `settings.py` 中配置：

```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://localhost:6379/0',
    }
}
```

### 8.2 前端缓存策略

配置 HTTP 缓存头，启用静态资源缓存。Vite 构建产物已包含 hash，可长期缓存。

## 9. 日志配置

### 9.1 应用日志

项目通过 `start_server.py` 在 `backend/logs/uvicorn.log` 中记录日志。生产环境建议配置 systemd 日志路径。

### 9.2 Nginx 日志

- 访问日志：`/var/log/nginx/access.log`
- 错误日志：`/var/log/nginx/error.log`

## 10. 安全配置

### 10.1 生产环境设置

- 设置 `DEBUG = False`
- 配置 `ALLOWED_HOSTS`
- 使用 HTTPS
- 配置 CSRF 和 CORS 白名单

### 10.2 安全头

在 Nginx 中添加安全响应头：

```nginx
add_header X-Content-Type-Options nosniff;
add_header X-Frame-Options DENY;
add_header X-XSS-Protection "1; mode=block";
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';";
```

## 11. 监控与维护

### 11.1 服务状态检查

```bash
systemctl status campus-app
systemctl status nginx
```

### 11.2 日志监控

```bash
tail -f /var/log/campus-app/error.log
tail -f /var/log/nginx/error.log
```

### 11.3 定期维护

- 备份数据库
- 更新依赖（`uv sync` 和 `pnpm update`）
- 安全扫描

## 12. 常见问题

### 12.1 端口冲突

修改 `backend/start_server.py` 中的端口配置，或使用 `--port` 参数启动 uvicorn。

### 12.2 数据库连接失败

检查数据库服务是否启动，用户名和密码是否正确，以及 `.env` 中的 `DB_HOST`、`DB_NAME`、`DB_USER`、`DB_PASSWORD` 配置。

### 12.3 CORS 错误

检查 `backend/config/settings.py` 中的 `CORS_ALLOWED_ORIGINS` 配置。

### 12.4 WebSocket 连接失败

- 确认使用 uvicorn/daphne 启动 ASGI 应用，而非 Django `runserver`。
- 检查 Nginx 的 WebSocket 代理配置（`Upgrade` 和 `Connection` 头）。
- 确认 `ALLOWED_HOSTS` 和 CORS 配置包含前端域名。

## 13. 服务状态检查

- 后端 API 健康检查：`GET https://api.example.com/api/schools/test-connection/`
- H5 前端：`https://example.com`
- 后端服务：`https://api.example.com`
