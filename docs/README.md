# Campus-Real-time-Exploration-and-Interactive-Community - 文档中心

欢迎来到项目文档中心，这里集中存放了项目的所有文档资料。

## 文档目录

### 快速导航

| 文档 | 说明 |
|------|------|
| [README.md](../README.md) | 项目主说明 |
| [部署指南](deployment.md) | 项目部署说明 |
| [API 文档](api/) | API 接口文档 |
| [测试报告](tests/) | 测试报告 |

### 1. API 文档

- [前端 API 调用文档](api/frontend_api.md) - 前端 API 调用示例

### 2. 测试报告

- [测试报告](tests/test_report.md) - 完整测试报告

## 项目概述

本项目是一个面向高校场景的实时互动社区平台，旨在为用户提供校园信息查询、论坛互动、在线学习、内容分享、私信沟通等功能。项目采用前后端分离架构，并同步开发微信小程序端：

- **后端**: Python 3.12 + Django + Django REST Framework + Django Channels
- **H5 前端**: Vue 3 + TypeScript + Pinia + Element Plus + Tailwind CSS
- **微信小程序**: Uni-app + uni-ui
- **实时通信**: WebSocket（Django Channels + Uvicorn）
- **数据库**: MySQL 8.0
- **依赖管理**: 后端 uv；前端 pnpm

## 核心功能

1. **院校查询与评价** - 学校列表、详情、专业查询、分数线查询、收藏
2. **校园论坛** - 话题/板块、发帖（含审核）、评论回复、点赞/收藏
3. **在线学习** - 课程列表、课程详情、报名学习、课时视频播放器、学习进度
4. **内容中心** - 用户内容提交、状态管理、全局搜索
5. **用户系统** - 注册登录、个人资料、密码重置、我的收藏
6. **实时沟通** - 公共聊天室（WebSocket，消息持久化）、H5 私信（消息持久化、已读/未读、会话列表）；小程序端已同步支持公共聊天室入口
7. **数据可视化** - 管理后台统计仪表盘

> 说明：公共聊天室与 H5 私信共存；公共聊天室 WebSocket 路由为 `/ws/chat/public/`，私信 WebSocket 路由为 `/ws/chat/private/<user_id>/`。

## 快速开始

### 环境要求

- Python 3.12.*
- Node.js 18+
- pnpm
- uv
- MySQL 8.0+（生产环境）

### 后端启动

```bash
cd backend
uv sync --frozen
python start_server.py
```

后端默认运行在 `http://localhost:8000`。

> 注意：WebSocket 需要 ASGI 服务器，项目已通过 `start_server.py` 使用 uvicorn 启动，请勿使用 Django 原生的 `runserver`。

### H5 前端启动

```bash
cd frontend
pnpm install
pnpm dev
```

前端默认运行在 `http://localhost:5173`。

### 小程序启动

使用 HBuilderX 或微信开发者工具打开 `mp-weixin/` 目录，按照 Uni-app 流程运行到微信小程序模拟器。

### 部署说明

详细部署步骤请参考 [部署指南](deployment.md)。

## 联系方式

如有问题或建议，请通过 Issue 联系我们。