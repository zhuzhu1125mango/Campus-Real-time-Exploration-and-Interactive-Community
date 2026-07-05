# Campus-Real-time-Exploration-and-Interactive-Community

一个面向高校场景的实时互动社区平台，支持院校查询、校园论坛、在线学习、内容分享、私信沟通等功能。项目采用前后端分离架构，并同步开发微信小程序端。

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.12, Django, Django REST Framework, Django Channels |
| H5 前端 | Vue 3, TypeScript, Pinia, VueUse, Vue Query, Axios, Element Plus, Tailwind CSS |
| 小程序 | Uni-app, uni-ui |
| 数据库 | MySQL 8.0 |
| 实时通信 | WebSocket（Django Channels + Uvicorn） |
| 依赖管理 | 后端：uv；前端：pnpm |

## 项目结构

```
.
├── backend/                        # Django 后端
│   ├── start_server.py             # 开发服务器启动脚本（自动 uv sync + uvicorn 热重载）
│   ├── pyproject.toml              # uv 依赖配置
│   ├── manage.py
│   └── ...
├── frontend/                       # Vue 3 H5 前端
│   ├── package.json
│   ├── pnpm-lock.yaml
│   └── ...
├── mp-weixin/                       # 微信小程序源码（Uni-app）
│   ├── pages.json
│   └── ...
├── docs/                           # 项目文档
│   ├── README.md
│   ├── deployment.md
│   └── ...
└── README.md                       # 本文件
```

## 核心功能

1. **院校查询与评价** - 学校列表、详情、专业查询、分数线查询、收藏
2. **校园论坛** - 话题/板块、发帖（含审核）、评论回复、点赞/收藏
3. **在线学习** - 课程列表、课程详情、报名学习、课时视频播放器、学习进度
4. **内容中心** - 用户内容提交、状态管理、全局搜索
5. **用户系统** - 注册登录、个人资料、密码重置、我的收藏
6. **实时沟通** - 公共聊天室（WebSocket，消息持久化）、H5 私信（消息持久化、已读/未读、会话列表）
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

## 部署说明

详细部署步骤请参考 [docs/deployment.md](docs/deployment.md)。

## 开发规范

- 后端统一使用 `uv` 管理依赖，通过 `pyproject.toml` 和 `uv.lock` 保持一致性。
- 前端统一使用 `pnpm` 管理依赖，不要提交 `package-lock.json` 或 `yarn.lock`。
- 启动开发服务器前，`start_server.py` 会自动执行 `uv sync --frozen` 检查依赖。
- 提交代码前请确认 `.gitignore` 已正确排除环境文件、构建产物和临时文件。

## 文档导航

- [项目文档中心](docs/README.md)
- [部署指南](docs/deployment.md)
- [API 文档](docs/api/)
- [测试报告](docs/tests/)

## 许可证

本项目采用 MIT 许可证。
