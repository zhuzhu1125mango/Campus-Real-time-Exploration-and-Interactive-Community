# 部署配置文档

## 1. 生产环境配置

### 1.1 服务器要求
- **操作系统**：Ubuntu 20.04 LTS 或更高版本
- **CPU**：2核或更高
- **内存**：4GB或更高
- **存储**：50GB或更高

### 1.2 依赖安装
```bash
# 安装系统依赖
sudo apt update
sudo apt install python3-pip python3-venv nginx

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装Python依赖
pip install -r requirements.txt
```

### 1.3 环境变量配置
创建 `.env` 文件：
```
# Django设置
DJANGO_SETTINGS_MODULE=djangoProject.settings

# 数据库配置
DATABASE_URL=mysql://username:password@localhost:3306/university_exchange

# 密钥
SECRET_KEY=your-secret-key-here

# 允许的主机
ALLOWED_HOSTS=example.com,www.example.com

# 邮件配置
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-email-password
```

### 1.4 启动脚本
使用 `start_production.sh` 脚本启动应用：
```bash
# 赋予执行权限
chmod +x start_production.sh

# 启动应用
./start_production.sh
```

## 2. Nginx配置

### 2.1 安装Nginx
```bash
sudo apt install nginx
```

### 2.2 配置文件
创建 `/etc/nginx/sites-available/campus-app`：

```nginx
upstream campus_app {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name example.com;
    
    # 重定向到HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name example.com;
    
    # SSL配置
    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    
    # 静态资源处理
    location / {
        root /path/to/Campus-Real-time-Exploration-and-Interactive-Community/frontvue/dist;
        try_files $uri $uri/ /index.html;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000";
    }
    
    # API和WebSocket代理
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
    
    # WebSocket代理
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
}
```

### 2.3 启用配置
```bash
# 启用配置
sudo ln -s /etc/nginx/sites-available/campus-app /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启Nginx
sudo systemctl restart nginx
```

## 3. CDN集成

### 3.1 选择CDN服务
推荐使用以下CDN服务：
- **Cloudflare**：免费计划，全球覆盖
- **阿里云CDN**：国内访问速度快
- **腾讯云CDN**：国内访问速度快

### 3.2 Cloudflare配置
1. 登录Cloudflare账户，添加域名
2. 配置DNS记录指向你的服务器IP
3. 启用CDN加速
4. 在Nginx配置中添加CDN IP白名单

### 3.3 Nginx中添加CDN白名单
```nginx
# 在server块中添加
set_real_ip_from 103.21.244.0/22;
set_real_ip_from 103.22.200.0/22;
set_real_ip_from 103.31.4.0/22;
# 添加更多Cloudflare IP段
real_ip_header CF-Connecting-IP;
```

### 3.4 前端配置
在前端项目中配置CDN域名：

```javascript
// frontvue/.env
VITE_API_BASE_URL=https://api.example.com
VITE_CDN_BASE_URL=https://cdn.example.com
```

## 4. 系统服务配置

### 4.1 创建systemd服务
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

### 4.2 启用服务
```bash
# 创建日志目录
sudo mkdir -p /var/log/campus-app
sudo chown -R ubuntu:www-data /var/log/campus-app

# 启用服务
sudo systemctl daemon-reload
sudo systemctl enable campus-app
sudo systemctl start campus-app
```

## 5. 部署流程

1. **准备服务器**：安装必要依赖
2. **配置数据库**：设置MySQL并导入数据
3. **部署后端**：
   - 安装Python依赖
   - 运行数据库迁移
   - 启动Gunicorn/UVicorn服务
4. **部署前端**：
   - 构建前端项目
   - 部署静态文件
5. **配置Nginx**：设置反向代理和SSL
6. **配置CDN**：启用CDN加速
7. **启动服务**：按顺序启动各服务

## 6. 监控与维护

### 6.1 日志监控
- Nginx日志：`/var/log/nginx/`
- 应用日志：`/var/log/campus-app/`
- 使用ELK Stack或Graylog集中管理日志

### 6.2 性能监控
- 服务器监控：Prometheus + Grafana
- 应用监控：Django Silk或New Relic
- 告警：配置邮件或Slack告警

### 6.3 定期维护
- 备份数据库：定期备份MySQL数据库
- 更新依赖：定期更新系统和依赖
- 安全检查：定期进行安全扫描

## 7. 故障排查

### 7.1 常见问题
| 问题 | 可能原因 | 解决方案 |
|------|---------|---------|
| 502 Bad Gateway | Gunicorn未运行 | 检查服务状态并重启 |
| 404 Not Found | 静态文件路径错误 | 检查Nginx配置中的root路径 |
| WebSocket连接失败 | WebSocket配置错误 | 检查Nginx的WebSocket代理配置 |
| 504 Gateway Timeout | 超时设置不足 | 增加proxy_read_timeout和Gunicorn timeout |
| SSL错误 | 证书配置错误 | 检查SSL证书路径和权限 |

### 7.2 日志分析
```bash
# 查看Nginx错误日志
tail -f /var/log/nginx/error.log

# 查看应用错误日志
tail -f /var/log/campus-app/error.log

# 查看服务状态
systemctl status campus-app
```

## 8. 性能优化

### 8.1 Nginx优化
- 启用gzip压缩
- 配置适当的缓存策略
- 调整worker_processes为CPU核心数

### 8.2 Gunicorn/UVicorn优化
- 工作进程数：2 * CPU核心数 + 1
- 调整timeout为300秒（适应WebSocket连接）
- 启用worker_connections为1000

### 8.3 前端优化
- 启用代码分割
- 优化静态资源大小
- 使用CDN加速静态资源

## 9. 安全加固

### 9.1 服务器安全
- 禁用root登录
- 配置防火墙
- 定期更新系统和依赖

### 9.2 应用安全
- 使用HTTPS
- 实现CSRF保护
- 防止SQL注入
- 保护敏感数据

## 10. 自动化部署

### 10.1 CI/CD配置
使用GitHub Actions或Jenkins实现自动化部署：

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r djangoend/requirements.txt
      - name: Build frontend
        run: |
          cd frontvue
          npm install
          npm run build
      - name: Deploy to server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SERVER_KEY }}
          script: |
            cd /path/to/project
            git pull
            source venv/bin/activate
            pip install -r requirements.txt
            python djangoend/manage.py migrate
            sudo systemctl restart campus-app
            sudo systemctl restart nginx
```

## 11. 版本控制

### 11.1 依赖版本
- 记录所有依赖的版本号
- 使用固定版本号避免依赖冲突
- 定期更新依赖以修复安全漏洞

### 11.2 配置版本
- 版本控制所有配置文件
- 使用环境变量管理敏感配置
- 保持配置文件的一致性

## 12. 扩展与升级

### 12.1 水平扩展
- 使用负载均衡器
- 部署多个应用实例
- 配置数据库主从复制

### 12.2 垂直扩展
- 增加服务器资源
- 优化数据库性能
- 使用缓存服务

### 12.3 应用升级
- 测试环境验证
- 滚动部署
- 回滚机制

## 13. 结论

本部署文档提供了完整的生产环境部署配置，包括服务器配置、Nginx配置、CDN集成、系统服务配置等。按照文档中的步骤进行部署，可以确保应用在生产环境中稳定运行，并具备良好的性能和安全性。

随着应用的发展，可以根据实际需求对配置进行调整和优化，以适应不断变化的业务需求。