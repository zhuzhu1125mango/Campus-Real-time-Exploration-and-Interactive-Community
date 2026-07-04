# 部署说明

## 1. 环境准备

### 1.1 系统要求
- Windows 10/11 或 Linux/macOS
- Python 3.10+
- Node.js 16+
- MySQL 8.0+（生产环境）
- Redis（可选，用于缓存）

### 1.2 依赖安装

#### 后端依赖
```bash
cd djangoend
python -m venv venv
venv\Scripts\activate.bat  # Windows
source venv/bin/activate   # Linux/Mac
pip install -r requirements.txt
```

#### 前端依赖
```bash
cd frontvue
npm install
```

## 2. 数据库配置

### 2.1 创建数据库
```sql
CREATE DATABASE university_exchange CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2.2 配置数据库连接
编辑 `djangoend/.env` 文件（复制 `.env.example`）：

```env
# Django设置
DJANGO_SETTINGS_MODULE=djangoProject.settings
SECRET_KEY=your-secret-key-here

# 数据库配置
DATABASE_URL=mysql://username:password@localhost:3306/university_exchange

# 允许的主机
ALLOWED_HOSTS=localhost,127.0.0.1,example.com

# Redis配置（可选）
REDIS_URL=redis://localhost:6379/0
```

### 2.3 数据库迁移
```bash
cd djangoend
python manage.py makemigrations
python manage.py migrate
```

### 2.4 创建超级用户
```bash
python manage.py createsuperuser
```

## 3. 后端部署

### 3.1 开发环境
```bash
cd djangoend
python start_server.py
```

默认启动在 `http://0.0.0.0:8000`

### 3.2 生产环境

#### 使用 Gunicorn + Uvicorn
```bash
pip install gunicorn
gunicorn djangoProject.asgi:application --bind 0.0.0.0:8000 --worker-class uvicorn.workers.UvicornWorker
```

#### 使用 systemd 服务
创建 `/etc/systemd/system/campus-app.service`：

```ini
[Unit]
Description=Campus App Django Application
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/path/to/Campus-Real-time-Exploration-and-Interactive-Community/djangoend
ExecStart=/path/to/venv/bin/gunicorn djangoProject.asgi:application \
    --bind 127.0.0.1:8000 \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --timeout 300 \
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

## 4. 前端部署

### 4.1 配置 API 基础 URL
编辑 `frontvue/.env.development` 或 `frontvue/.env.production`：

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000
VITE_UPLOAD_URL=http://localhost:8000/media
VITE_STATIC_URL=http://localhost:8000/static
```

### 4.2 启动前端开发服务器
```bash
cd frontvue
npm run dev
```

默认启动在 `http://localhost:5173`

### 4.3 构建生产版本
```bash
cd frontvue
npm run build
```

构建结果将生成在 `frontvue/dist` 目录

## 5. Nginx 配置

### 5.1 安装 Nginx
```bash
sudo apt install nginx  # Ubuntu/Debian
```

### 5.2 配置文件
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
        root /path/to/Campus-Real-time-Exploration-and-Interactive-Community/frontvue/dist;
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
        alias /path/to/Campus-Real-time-Exploration-and-Interactive-Community/djangoend/media/;
        expires 30d;
    }
    
    location /static/ {
        alias /path/to/Campus-Real-time-Exploration-and-Interactive-Community/djangoend/static/;
        expires 30d;
    }
}
```

### 5.3 启用配置
```bash
sudo ln -s /etc/nginx/sites-available/campus-app /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 6. CDN 集成

### 6.1 Cloudflare 配置
1. 登录 Cloudflare，添加域名
2. 配置 DNS 记录指向服务器 IP
3. 启用 CDN 加速
4. 在 Nginx 中添加 Cloudflare IP 白名单

```nginx
set_real_ip_from 103.21.244.0/22;
set_real_ip_from 103.22.200.0/22;
set_real_ip_from 103.31.4.0/22;
real_ip_header CF-Connecting-IP;
```

## 7. 缓存配置

### 7.1 Redis 缓存
在 `settings.py` 中配置：

```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://localhost:6379/0',
    }
}
```

### 7.2 前端缓存策略
配置 HTTP 缓存头，启用静态资源缓存。

## 8. 日志配置

### 8.1 应用日志
配置 `settings.py`：

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/campus-app/django.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

### 8.2 Nginx 日志
- 访问日志：`/var/log/nginx/access.log`
- 错误日志：`/var/log/nginx/error.log`

## 9. 安全配置

### 9.1 生产环境设置
- 设置 `DEBUG = False`
- 配置 `ALLOWED_HOSTS`
- 使用 HTTPS
- 配置 CSRF 保护

### 9.2 安全头
在 Nginx 中添加安全响应头：

```nginx
add_header X-Content-Type-Options nosniff;
add_header X-Frame-Options DENY;
add_header X-XSS-Protection "1; mode=block";
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';";
```

## 10. 监控与维护

### 10.1 服务状态检查
```bash
systemctl status campus-app
systemctl status nginx
```

### 10.2 日志监控
```bash
tail -f /var/log/campus-app/error.log
tail -f /var/log/nginx/error.log
```

### 10.3 定期维护
- 备份数据库
- 更新依赖
- 安全扫描

## 11. 常见问题

### 11.1 端口冲突
修改 `start_server.py` 中的端口配置。

### 11.2 数据库连接失败
检查数据库服务是否启动，用户名和密码是否正确。

### 11.3 CORS 错误
检查 `settings.py` 中的 CORS 配置。

### 11.4 WebSocket 连接失败
检查 Nginx 的 WebSocket 代理配置。

## 12. 服务状态检查

- 后端 API 健康检查：`GET http://localhost:8000/api/schools/test-connection/`
- 前端服务：`http://localhost:5173`
- 后端服务：`http://localhost:8000`