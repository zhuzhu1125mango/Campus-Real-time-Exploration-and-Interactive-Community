# 部署说明

## 1. 环境准备

### 1.1 系统要求
- Windows 10/11 或 Linux/macOS
- Python 3.10+
- Node.js 16+
- MySQL 8.0+

### 1.2 依赖安装

#### 后端依赖
```bash
# 进入后端目录
cd djangoend

# 安装依赖
pip install -r requirements.txt
```

#### 前端依赖
```bash
# 进入前端目录
cd frontvue

# 安装依赖
npm install
```

## 2. 数据库配置

### 2.1 创建数据库
```sql
CREATE DATABASE university_exchange CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2.2 配置数据库连接
编辑 `djangoend/djangoProject/settings.py` 文件，修改数据库配置：

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'university_exchange',
        'USER': 'root',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    }
}
```

## 3. 后端部署

### 3.1 数据库迁移
```bash
# 进入后端目录
cd djangoend

# 生成迁移文件
python manage.py makemigrations

# 应用迁移
python manage.py migrate
```

### 3.2 启动后端服务
```bash
# 使用 Uvicorn 启动后端服务
python start_server.py
```

默认启动在 `http://0.0.0.0:8000`

## 4. 前端部署

### 4.1 配置 API 基础 URL
编辑 `frontvue/.env.development` 文件，修改 API 基础 URL：

```env
# API基础URL
VITE_API_BASE_URL=http://localhost:8000

# WebSocket基础URL
VITE_WS_BASE_URL=ws://localhost:8000

# 上传文件URL
VITE_UPLOAD_URL=http://localhost:8000/media

# 静态资源URL
VITE_STATIC_URL=http://localhost:8000/static
```

### 4.2 启动前端开发服务器
```bash
# 进入前端目录
cd frontvue

# 启动开发服务器
npm run dev
```

默认启动在 `http://localhost:5174`

### 4.3 构建生产版本
```bash
# 构建生产版本
npm run build
```

构建结果将生成在 `frontvue/dist` 目录

## 5. 生产环境部署

### 5.1 后端部署
- 使用 Gunicorn + Uvicorn 作为生产服务器
- 配置 Nginx 作为反向代理
- 设置环境变量 `DJANGO_SETTINGS_MODULE` 为 `djangoProject.settings`

### 5.2 前端部署
- 将 `frontvue/dist` 目录部署到 Nginx 或其他静态文件服务器
- 配置 Nginx 反向代理到后端 API

## 6. 常见问题

### 6.1 端口冲突
如果端口 8000 或 5174 已被占用，可以修改 `start_server.py` 和 `.env.development` 文件中的端口配置。

### 6.2 数据库连接失败
检查数据库服务是否启动，用户名和密码是否正确，数据库是否存在。

### 6.3 CORS 错误
后端已配置 CORS，允许前端访问。如果仍有问题，检查 `djangoProject/settings.py` 中的 CORS 配置。

## 7. 服务状态检查

- 后端 API 健康检查：`GET http://localhost:8000/api/schools/test-connection/`
- 前端服务：`http://localhost:5174`
- 后端服务：`http://localhost:8000`
