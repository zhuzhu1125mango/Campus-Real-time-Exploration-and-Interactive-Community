# 重构变更摘要（2026-11-13）

## 1. 概要

| 项 | 内容 |
|---|---|
| 对比基线 | `21ec72a`（origin/main 原位置） |
| 目标提交 | `7273dbb`（当前 HEAD / origin/main） |
| 包含提交 | `57ec28e` 关注功能、`7273dbb` 架构与文档重构 |
| 变更规模 | 291 个文件，+26223 / -11754 |
| 核心目标 | 领域模块拆分、通知/搜索/异步统一、生产化部署、文档体系重建 |
| 当前状态 | 已推送至 `origin/main`，工作区除 `.trae/` 外干净 |

## 2. 变更分布

| 区域 | 文件数 | 新增行 | 删除行 | 主要变化 |
|---|---:|---:|---:|---|
| `frontend/` | 82 | 11815 | 8751 | 请求层、多账号、页面重构、安全工具、构建拆包 |
| `backend/` | 146 | 6596 | 2118 | 领域拆分、搜索、缓存、Celery、ASGI、部署脚本 |
| `docs/` | 38 | 6334 | 694 | 文档目录重构与 30 篇新文档 |
| 根目录 | 4 | 548 | 21 | README、Docker Compose、环境变量模板 |
| `mp-weixin/` | 9 | 343 | 170 | 请求层、通知页、WebSocket、工具 |
| `shared/` | 7 | 408 | 0 | 三端共享常量与工具 |
| `nginx/` | 4 | 173 | 0 | 开发/生产配置、证书模板渲染 |
| `elasticsearch/` | 1 | 6 | 0 | 内置 ik 分词镜像 |

## 3. 后端架构

### 3.1 领域模块拆分

从 `users` 中拆出 5 个独立 app：

| 新 app | 职责 |
|---|---|
| `activities` | 用户动态、动态点赞/评论 |
| `favorites` | 通用收藏（ContentType 多态） |
| `friendships` | 好友请求与好友关系 |
| `private_messages` | 私信 REST |
| `notifications` | 统一通知模型、发送入口、信号与视图 |

### 3.2 新增通用层

- `backend/core/base_viewsets.py`：配置化权限、限流、查询优化基类
- `backend/core/cache_utils.py`：分层 TTL、空值缓存、互斥锁、抖动、版本失效、gzip、降级
- `backend/core/html_sanitizer.py`：基于 bleach 的富文本清洗

### 3.3 搜索与异步

- 新增 `search/` 的 Elasticsearch 实现：
  - `documents.py`：学校/主题/帖子/内容/课程/用户 6 类文档
  - `services.py`：ES 查询 + MySQL LIKE 降级
  - `signals.py` / `tasks.py`：模型变更异步更新索引
  - `rebuild_search_index` 管理命令
- 新增 `users/tasks.py`：
  - `update_user_points_async`：积分与等级异步更新
  - `send_notification_async`：通知 WebSocket 异步推送
  - `queue_update_user_points`：统一通过 `transaction.on_commit` 派发
- 新增 `config/celery.py`：显式发现各 app 的 `tasks.py`

### 3.4 通知统一

- 统一使用 `notifications.Notification`（表 `users_notification`）
- 移除 `forum.Notification`，新增数据迁移
- 新增 `content_comment` 通知类型
- **移除旧 `/api/notifications/` 兼容 ViewSet**，统一使用 `/api/users/notifications/`

### 3.5 配置与数据库

- 新增 `config/asgi_http.py`、`config/asgi_ws.py`：HTTP 与 WebSocket 分离
- 新增 `config/db_router.py`：主从读写分离
- `settings.py`：
  - Redis 拆分 `REDIS_WS_URL` / `REDIS_CACHE_URL`
  - JWT、CORS、CSRF、Cookie 安全配置
  - DRF 限流、分页、Celery、ES 配置
  - 生产强制 `DJANGO_SECRET_KEY`

### 3.6 实时通信

- WebSocket 认证支持 `Sec-WebSocket-Protocol: jwt,<token>`，兼容 `?token=`
- 公共聊天室与私信增加：
  - 频率限制（60 秒 60 条）
  - 内容清洗
  - 1000 字符上限
  - 在线人数改为 Redis 最近 5 分钟活跃统计
- 私聊要求好友关系，分组 `private_{minId}_{maxId}`

## 4. API 变更

### 4.1 新增/调整

| 模块 | 变化 |
|---|---|
| 通知 | 统一为 `/api/users/notifications/`，支持列表、未读数、按类型、全部已读、删除已读 |
| 关注 | 新增 `/api/users/users/{id}/follow/`、`/unfollow/` |
| Feed | 新增 `/api/feed/feed/`、`/api/feed/trending_topics/` |
| 搜索 | `/api/search/` 优先 ES，失败降级 MySQL |
| 探索 | 新增地点、附近地点/活动、打卡接口 |
| 学习 | 课程发布、章节/课时、进度记录、资源下载等 action 完善 |

### 4.2 破坏性变更

| 变更 | 影响 | 迁移方式 |
|---|---|---|
| 移除 `/api/notifications/` | 旧客户端会收到 404 | 改用 `/api/users/notifications/...` |
| WebSocket token 传递 | 推荐 `jwt` 子协议 | 旧 `?token=` 仍兼容 |
| 通知类型 | 评论类改为 `content_comment` | 历史数据保持原类型 |

## 5. 前端与小程序

### 5.1 H5

- 请求层统一：
  - 多账号 token 槽位（`auth_tokens:<userId>`）
  - 401 并发刷新复用同一 Promise
  - CSRF 头注入
- 安全：`v-html` 统一走 `utils/xss.ts`
- 构建：`manualChunks` 拆分 echarts、element-plus、leaflet、vueuse 等
- 页面：论坛、内容、学习、院校、聊天、通知、个人中心等整体重构
- 通知页改用 `/api/users/notifications/` 并支持分页

### 5.2 微信小程序

- 请求层：统一 Bearer token、401 刷新、重试
- WebSocket：`jwt` 子协议、心跳、重连
- 通知页改用 `notificationApi` 并支持分页
- 内容投稿状态、课时播放器续播/倍速、全局搜索页补齐

### 5.3 关注功能

`57ec28e` 打通 H5、小程序与后端关注能力。

## 6. 部署与运维

### 6.1 新增部署资产

- `backend/Dockerfile`、`backend/.dockerignore`
- `docker-compose.yml`、`docker-compose.prod.yml`
- `nginx/`：开发配置、生产 HTTPS 模板、`envsubst` 渲染、Dockerfile
- `elasticsearch/Dockerfile`：内置 analysis-ik
- 启动脚本：
  - `start_http.sh`、`start_ws.sh`、`start_worker.sh`、`start_beat.sh`
  - `init_django.sh`：迁移、collectstatic、重建 ES 索引

### 6.2 生产配置

- 仅 Nginx 暴露 80/443
- HTTP / WebSocket 独立进程
- `django-init` 独立初始化，避免多实例重复迁移
- 已为 `django-init` 补齐数据库、Redis、Celery、ES、密钥等环境变量

### 6.3 新增关键环境变量

```env
REDIS_WS_URL=redis://redis-ws:6379/0
REDIS_CACHE_URL=redis://redis-cache:6379/0
CELERY_BROKER_URL=amqp://...
CELERY_RESULT_BACKEND=redis://...
ELASTICSEARCH_HOSTS=http://elasticsearch:9200
ELASTICSEARCH_FALLBACK_TO_DB=True
DB_REPLICA_HOST=
PROD_DOMAIN=
SSL_CERT_PATH=
SSL_KEY_PATH=
```

完整说明见 [配置说明](../getting-started/configuration.md)。

## 7. 数据与迁移

新增迁移：

| App | 迁移 | 说明 |
|---|---|---|
| `activities` | `0001_initial` | 动态、点赞、评论 |
| `favorites` | `0001_initial` | 通用收藏 |
| `friendships` | `0001_initial` | 好友请求、好友 |
| `notifications` | `0001_initial`、`0002_alter...` | 统一通知与类型调整 |
| `private_messages` | `0001_initial` | 私信 |
| `forum` | `0008_migrate_and_remove_notification` | 迁移历史通知并移除旧模型 |
| `users` | `0011_alter_pointsrecord_action` | 积分行为类型 |

### 升级步骤

```bash
cd backend
uv sync --frozen
uv run python manage.py migrate
uv run python manage.py collectstatic --noinput
uv run python manage.py rebuild_search_index --delete
```

> `forum.0008` 涉及历史通知数据迁移，升级前请备份数据库。
> 回滚代码不会自动回滚该数据迁移。

## 8. 安全加固

- 富文本统一 `bleach` 清洗（用户资料、论坛、内容、聊天消息）
- H5 `v-html` 统一 DOMPurify 过滤
- WebSocket 频率限制 + 内容清洗 + 长度限制
- JWT 刷新轮换与黑名单
- CORS 白名单、CSRF、Cookie Secure/HttpOnly
- `.dockerignore` 排除 `.env`、`.venv`、日志等
- 生产强制强随机 `DJANGO_SECRET_KEY`

## 9. 文档

- `docs/` 按入门、指南、架构、参考、项目治理重建
- 新增/重写 30 篇文档
- 旧文档 5 份移入 `docs/archive/`
- 覆盖：安装、快速开始、配置、开发、测试、部署、运维、排障、API、数据模型、WebSocket、后台任务、贡献、安全、变更记录、路线图

入口：[项目文档中心](../README.md)

## 10. 验证结果

| 检查 | 结果 |
|---|---|
| `manage.py check` | 无问题 |
| `makemigrations --check --dry-run` | `No changes detected` |
| 旧 `/api/notifications/` | 404 |
| `/api/users/notifications/...` | 正常解析 |
| `pnpm type-check` | 通过 |
| 定向测试 | notifications 7 个 + BookmarkTests 4 个全部通过 |

> 全量 `forum` 测试在未开启 Celery eager 时会因本机 Redis 认证阻塞；
> 设置 `CELERY_TASK_ALWAYS_EAGER=True` 后可正常执行。

## 11. 已知问题与后续

| 优先级 | 问题 |
|---|---|
| P2 | `VITE_API_BASE_URL` 未被前端实际读取 |
| P2 | 小程序 `api/index.js` 未导出 `searchApi` |
| P2 | 通知消费者事件名与下发 `type` 不一致 |
| P2 | `activities/content/favorites/friendships/private_messages` 测试仍为空 |
| P2 | 前端缺少单元/E2E 测试 |

详见 [路线图](roadmap.md)。

## 12. 提交与回滚

### 提交

```text
7273dbb refactor: 拆分领域模块并统一通知、搜索与文档体系
57ec28e feat: integrate follow feature across H5, mini-program and backend
```

### 回滚

```bash
# 回滚本次重构（保留工作区）
git revert 7273dbb

# 如需同时回滚关注功能
git revert 57ec28e
```

回滚前请确认：

1. 数据库已备份
2. `forum.0008` 通知数据迁移可接受保留
3. 旧客户端不再依赖 `/api/users/notifications/` 之外的新接口
4. 生产环境变量与镜像版本同步回退
