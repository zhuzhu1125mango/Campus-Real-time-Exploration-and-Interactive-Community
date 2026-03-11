# 校园实时互动社区

## 项目功能

本项目是一个校园实时互动社区平台，提供以下功能：

### 1. 院校查询和评价
- 浏览学校列表
- 查看学校详情
- 专业查询
- 历年分数线查询
- 用户评价系统

### 2. 校园论坛
- 每个学校拥有自己的论坛板块
- 用户可以发表主题帖
- 支持评论和回复功能
- 点赞功能
- 标签管理

### 3. 用户系统
- 用户注册和登录
- 个人资料管理
- 收藏的学校
- 发表的评论和帖子管理

## 技术栈

### 前端
- Vue 3 + TypeScript
- Pinia 状态管理
- Vue Router
- Axios

### 后端
- Django
- Django Rest Framework
- JWT 认证
- PostgreSQL / SQLite

## 开发指南

### 安装依赖

前端：
```bash
cd frontvue
npm install
```

后端：
```bash
cd djangoend
pip install -r requirements.txt
```

### 运行开发服务器

前端：
```bash
cd frontvue
npm run dev
```

后端：
```bash
cd djangoend
python manage.py runserver
```

## 功能说明

### 论坛功能
- 每个学校都有自己的论坛页面
- 用户可以在论坛中发布帖子、评论和回复
- 支持帖子搜索、筛选和分页
- 评论支持嵌套回复和点赞

### 帖子详情页
- 显示帖子完整内容和作者信息
- 评论和回复系统
- 点赞功能
- 按时间顺序展示评论

## 数据模型

### 论坛相关
- Forum(id, school, name, description, posts_count, created_at, updated_at)
- Post(id, forum, author, title, content, status, views, likes_count, comments_count, tags, created_at, updated_at)
- Comment(id, post, author, content, parent, likes_count, created_at, updated_at)
- Tag(id, name, description)

### API说明
- `/api/schools/forums/` - 获取学校论坛
- `/api/schools/forums/<id>/posts/` - 获取论坛帖子
- `/api/schools/posts/<id>/` - 获取帖子详情
- `/api/schools/posts/<id>/comments/` - 获取帖子评论
- `/api/schools/comments/` - 创建评论
- `/api/schools/posts/<id>/like/` - 点赞帖子
- `/api/schools/comments/<id>/like/` - 点赞评论
- `/api/schools/tags/` - 获取标签 