'''
# 大学交流网站后端 - Django项目

## 项目设置

### 1. 环境准备

确保您已安装Python (3.8+)和MySQL数据库。

### 2. 安装依赖

```bash
# 在djangoend目录下执行
pip install -r requirements.txt
```

### 3. 数据库配置

1. 创建MySQL数据库
```sql
CREATE DATABASE university_exchange CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

2. 在`djangoend/settings.py`中配置数据库连接信息
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'university_exchange',  # 数据库名称
        'USER': '您的数据库用户名',      # 替换为您的MySQL用户名
        'PASSWORD': '您的数据库密码',    # 替换为您的MySQL密码
        'HOST': '127.0.0.1',
        'PORT': '3306',
    }
}
```

### 4. 运行迁移

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. 创建超级用户

```bash
python manage.py createsuperuser
```

### 6. 启动开发服务器

```bash
python manage.py runserver 0.0.0.0:8000
```

现在您可以访问:
- 管理后台: http://localhost:8000/admin/
- API文档: http://localhost:8000/swagger/

## 项目结构

```
djangoend/
├── djangoend/             # 项目配置目录
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py        # 项目设置
│   ├── urls.py            # 主URL配置
│   └── wsgi.py
├── apps/                  # 应用目录(将在开发中创建)
│   ├── users/             # 用户应用
│   ├── posts/             # 帖子应用
│   └── ...
├── media/                 # 上传的媒体文件
├── static/                # 静态文件
├── manage.py              # Django管理脚本
└── requirements.txt       # 项目依赖
```

## API开发指南

### 创建新应用

```bash
python manage.py startapp 应用名称
```

### 添加到已安装应用

在`settings.py`中添加新应用:

```python
INSTALLED_APPS = [
    # ...
    '应用名称',
]
```

### 创建REST API

1. 在应用目录中创建`serializers.py`定义序列化器
2. 在`views.py`中使用ModelViewSet创建API视图
3. 创建`urls.py`并配置路由
4. 在主`urls.py`中包含应用URLs

## 部署到阿里云

### 准备工作

1. 修改`settings.py`中的部署设置:
   - `DEBUG = False`
   - 更新`ALLOWED_HOSTS`
   - 配置数据库连接

2. 收集静态文件:
```bash
python manage.py collectstatic
```

### 使用Gunicorn和Nginx

1. 安装Gunicorn:
```bash
pip install gunicorn
```

2. 启动Gunicorn:
```bash
gunicorn djangoend.wsgi:application --bind 0.0.0.0:8000
```

3. 配置Nginx作为反向代理

详细的部署文档稍后提供。 
'''