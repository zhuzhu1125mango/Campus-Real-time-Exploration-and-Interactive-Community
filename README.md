# Campus-Real-time-Exploration-and-Interactive-Community

一个面向高校场景的实时互动社区平台，支持院校查询、校园论坛、在线学习、内容分享、私信沟通等功能。项目采用前后端分离架构，并同步开发微信小程序端。

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.12, Django, Django REST Framework, Django Channels, Celery |
| H5 前端 | Vue 3, TypeScript, Pinia, VueUse, Axios, Element Plus, UnoCSS, ECharts, Leaflet |
| 小程序 | Uni-app, uni-ui |
| 数据库 | MySQL 8.0（支持主从读写分离） |
| 搜索引擎 | Elasticsearch 8.x + analysis-ik 中文分词 |
| 消息队列 | RabbitMQ（Celery Broker） |
| 缓存/实时通信 | Redis（WebSocket Channel Layer / 业务缓存拆分） |
| 实时通信 | WebSocket（Django Channels + Uvicorn） |
| 容器化 | Docker, Docker Compose |
| 依赖管理 | 后端：uv；前端：pnpm |

## 项目结构

```
.
├── backend/                        # Django 后端
│   ├── config/                     # ASGI/WSGI/Celery/Settings 配置
│   │   ├── asgi.py                 # 统一 ASGI 入口
│   │   ├── asgi_http.py            # HTTP 专用 ASGI 入口（生产）
│   │   ├── asgi_ws.py              # WebSocket 专用 ASGI 入口（生产）
│   │   ├── celery.py               # Celery 配置
│   │   ├── db_router.py            # 主从读写分离路由
│   │   └── settings.py             # Django 配置
│   ├── core/cache_utils.py         # 统一缓存工具层
│   ├── search/                     # Elasticsearch 搜索模块
│   │   ├── documents.py            # ES 文档映射（ik 分词）
│   │   ├── services.py             # 搜索服务（ES + MySQL 降级）
│   │   ├── signals.py              # 模型变更异步同步索引
│   │   ├── tasks.py                # 索引更新 Celery 任务
│   │   └── management/commands/rebuild_search_index.py
│   ├── notifications/              # 统一通知模型与发送入口
│   ├── users/                      # 用户、积分、等级
│   ├── scripts/                    # 生产启动脚本
│   │   ├── start_http.sh           # HTTP 服务
│   │   ├── start_ws.sh             # WebSocket 服务
│   │   ├── start_worker.sh         # Celery Worker
│   │   └── start_beat.sh           # Celery Beat
│   ├── pyproject.toml              # uv 依赖配置
│   ├── uv.lock
│   └── manage.py
├── frontend/                       # Vue 3 H5 前端
│   ├── src/
│   │   ├── utils/echarts.ts        # ECharts 按需引入
│   │   └── ...
│   ├── vite.config.ts              # Vite 配置（manualChunks 拆包）
│   ├── package.json
│   └── pnpm-lock.yaml
├── mp-weixin/                       # 微信小程序源码（Uni-app）
│   ├── pages.json
│   ├── api/
│   └── ...
├── elasticsearch/                   # ES 自定义镜像（内置 ik 分词）
│   └── Dockerfile
├── nginx/                           # Nginx 配置
│   ├── nginx.conf                   # 开发/基础配置
│   ├── nginx.prod.conf.template     # 生产 HTTPS 配置模板（通过 envsubst 渲染）
│   ├── Dockerfile                   # Nginx 生产镜像
│   └── entrypoint.sh                # 容器启动时渲染模板为最终配置
├── docker-compose.yml               # 基础容器编排
├── docker-compose.prod.yml          # 生产环境覆盖配置
├── .env.example                     # 生产/部署环境变量示例
├── docs/                            # 项目文档中心
│   ├── README.md                    # 文档导航
│   ├── getting-started/             # 安装、快速开始、配置
│   ├── guides/                      # 开发、测试、部署、运维、排障
│   ├── architecture/                # 系统架构与设计说明
│   ├── reference/                   # API、数据模型、WebSocket、后台任务
│   ├── project/                     # 贡献、安全、变更记录、路线图
│   └── archive/                     # 历史文档
└── README.md                        # 本文件
```

## 核心功能

1. **院校查询与评价** - 学校列表、详情、专业查询、分数线查询、收藏
2. **校园论坛** - 话题/板块、发帖（含审核）、评论回复、点赞/收藏
3. **在线学习** - 课程列表、课程详情、报名学习、课时视频播放器、学习进度
4. **内容中心** - 用户内容提交、状态管理、全局搜索
5. **用户系统** - 注册登录、个人资料、密码重置、我的收藏、积分等级
6. **实时沟通** - 公共聊天室（WebSocket，消息持久化）、H5 私信（消息持久化、已读/未读、会话列表）
7. **全局搜索** - 基于 Elasticsearch + ik 中文分词，支持课程/内容/学校/论坛主题/帖子/用户；ES 故障时自动降级为 MySQL LIKE
8. **通知系统** - 统一通知模型，创建后异步推送到 WebSocket
9. **积分系统** - 注册/登录/发帖/回复/点赞/被点赞/签到/完善资料/身份认证/创建课程/完成课程等行为统一积分规则，异步更新
10. **数据可视化** - 管理后台统计仪表盘

> 说明：公共聊天室与 H5 私信共存；公共聊天室 WebSocket 路由为 `/ws/chat/public/`，私信 WebSocket 路由为 `/ws/chat/private/<user_id>/`。

## 快速开始

### 环境要求

- Python 3.12.*
- Node.js 18+
- pnpm
- uv
- MySQL 8.0+（生产环境）
- Redis 7+（推荐拆分为 WebSocket 与缓存两个实例）
- RabbitMQ 3+（Celery Broker）
- Elasticsearch 8.x + analysis-ik（可选，未启动时搜索降级为 MySQL LIKE）

### 后端启动

#### 1. 首次环境准备

进入后端目录，安装依赖并准备环境变量：

```bash
cd backend

# 复制环境变量模板，按实际环境修改（至少填写 DJANGO_SECRET_KEY、数据库、Redis、RabbitMQ 等）
cp .env.example .env

# 使用 uv 安装依赖（已锁定版本，与 uv.lock 保持一致）
uv sync --frozen
```

`.env` 中必填项说明请参考 `backend/.env.example` 中的注释。

#### 2. 启动外部依赖服务

后端运行前需要启动以下服务：

- **MySQL 8.0+**：创建 `university_exchange` 数据库（字符集 `utf8mb4`）。
- **Redis 7+**：用于 Channel Layer、业务缓存。
- **RabbitMQ 3+**：作为 Celery Broker。
- **Elasticsearch 8.x + analysis-ik**（可选）：未启动时搜索自动降级为 MySQL LIKE。

推荐在 Docker 中运行这些基础设施，宿主机只跑前后端：

```bash
# 一键启动 MySQL / Redis / RabbitMQ / Elasticsearch
docker compose up -d mysql redis-ws redis-cache rabbitmq elasticsearch
```

服务端口将映射到宿主机：

| 服务 | 宿主机地址 |
|------|-----------|
| MySQL | `127.0.0.1:3306` |
| Redis WebSocket | `redis://127.0.0.1:6379/0` |
| Redis 缓存 | `redis://127.0.0.1:6380/1` |
| RabbitMQ | `amqp://127.0.0.1:5672` |
| Elasticsearch | `http://127.0.0.1:9200` |

若本地 6379 已被占用，修改 `docker-compose.yml` 中 `redis-ws` 的端口映射，并同步修改 `backend/.env` 中的 `REDIS_WS_URL`。

#### 3. 启动 HTTP / WebSocket 服务

`start_server.py` 会自动完成数据库迁移、静态文件收集、端口检查等初始化，然后启动 ASGI 服务器：

```bash
cd backend
python start_server.py
```

启动成功后：

- HTTP API：`http://localhost:8000`
- WebSocket：`ws://localhost:8000/ws/`

> 注意：`start_server.py` 内部使用 uvicorn 启动 ASGI 应用，请勿使用 Django 原生的 `python manage.py runserver`，否则 WebSocket 无法连接。

常用参数：

```bash
# 不执行自动测试（加快启动速度）
python start_server.py --no-tests

# 禁用热加载（适用于稳定调试）
python start_server.py --no-reload

# 创建默认超级用户 admin/admin123
python start_server.py --create-admin
```

#### 4. 启动 Celery Worker（异步任务必需）

积分更新、通知推送、ES 索引更新等均为异步任务，需要在另一个终端单独启动 Celery Worker：

```bash
cd backend
uv run celery -A config worker --loglevel info --concurrency 2
```

生产环境请参考 [部署指南](docs/guides/deployment.md) 使用 `scripts/start_worker.sh`。

#### 5. 启动 Celery Beat（定时任务可选）

如需运行定时任务（如每日签到重置、过期消息清理），再启动一个 Beat 进程：

```bash
cd backend
uv run celery -A config beat --loglevel info
```

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

详细部署步骤请参考 [部署指南](docs/guides/deployment.md)。

## 架构优化说明

本阶段已完成的主要架构优化：

- **Elasticsearch 替换 LIKE 搜索**：基于 analysis-ik 中文分词，支持全局搜索；ES 故障时自动降级为 MySQL LIKE。
- **缓存策略细化**：统一缓存工具层 `core/cache_utils.py`，包含分层 TTL、空值缓存、互斥锁、随机抖动、版本号失效、gzip 压缩、异常降级。
- **通知/积分业务异步化**：积分更新与通知推送改为 Celery 异步任务；积分任务统一通过 `transaction.on_commit` 派发，避免事务未提交时读取不到数据；通过 `PointsRecord` 实现幂等发放。
- **通知模型统一**：彻底移除 `forum.Notification`，统一使用 `notifications.Notification`；评论/回复类事件使用独立的 `content_comment` 通知类型。
- **安全基线加固**：
  - 富文本/HTML 统一使用 `bleach` 清洗后再入库（`core/html_sanitizer.py`），覆盖用户资料、论坛帖子/评论、内容文章等字段。
  - WebSocket 消息增加后端频率限制与内容清洗，防止 XSS 与恶意刷屏。
  - `.gitignore` 与 `backend/.dockerignore` 排除敏感文件与本地环境。
- **生产环境加固**：HTTP 与 WebSocket 服务分离、Docker Compose 收紧端口暴露、Nginx HTTPS 配置通过 `envsubst` 从环境变量渲染、强随机 `SECRET_KEY` 校验、独立 `django-init` 初始化任务。

详细说明请参考 [架构总览](docs/architecture/overview.md)。

## 开发规范

- 后端统一使用 `uv` 管理依赖，通过 `pyproject.toml` 和 `uv.lock` 保持一致性。
- 前端统一使用 `pnpm` 管理依赖，不要提交 `package-lock.json` 或 `yarn.lock`。
- 启动开发服务器前，`start_server.py` 会自动执行 `uv sync --frozen` 检查依赖。
- 提交代码前请确认 `.gitignore` 已正确排除环境文件、构建产物和临时文件。
- 生产环境 `DJANGO_SECRET_KEY` 必须使用强随机密钥（建议 64 位以上），不可使用示例值。

## 文档导航

- [项目文档中心](docs/README.md)
- [安装](docs/getting-started/installation.md) / [快速开始](docs/getting-started/quickstart.md) / [配置](docs/getting-started/configuration.md)
- [开发指南](docs/guides/development.md) / [测试指南](docs/guides/testing.md)
- [部署指南](docs/guides/deployment.md) / [运维手册](docs/guides/operations.md) / [故障排查](docs/guides/troubleshooting.md)
- [架构总览](docs/architecture/overview.md) / [后端](docs/architecture/backend.md) / [前端](docs/architecture/frontend.md) / [实时通信](docs/architecture/realtime.md)
- [API 参考](docs/reference/api/README.md) / [数据模型](docs/reference/data-model.md) / [WebSocket 协议](docs/reference/websocket-protocol.md) / [后台任务](docs/reference/background-jobs.md)
- [贡献指南](docs/project/contributing.md) / [安全说明](docs/project/security.md) / [变更记录](docs/project/changelog.md) / [路线图](docs/project/roadmap.md)

## 许可证

本项目采用 MIT 许可证。
