# 故障排查

按「症状 → 可能原因 → 处理」组织。先看日志，再对照本文。

## 1. 启动与配置

### 1.1 `DJANGO_SECRET_KEY 环境变量未设置`

原因：`backend/.env` 未创建，或变量名为空。

处理：

```bash
cd backend
cp .env.example .env
# 填入强随机值
```

### 1.2 `System check identified some issues`

先执行：

```bash
cd backend
uv run python manage.py check
```

按输出修复模型/字段/Admin 注册问题。常见于新增模型后忘记注册或字段引用错误。

### 1.3 迁移漂移

```bash
uv run python manage.py makemigrations --check --dry-run
```

若提示有未生成迁移：

```bash
uv run python manage.py makemigrations
uv run python manage.py migrate
```

### 1.4 端口被占用

```powershell
netstat -ano | findstr :8000
```

释放端口或通过 `HTTP_BIND` / `WS_PORT` 修改启动地址。

## 2. 数据库

### 2.1 `Access denied for user`

检查 `backend/.env` 中的 `DB_USER` / `DB_PASSWORD` / `DB_HOST`。
Docker 场景下 `DB_HOST` 必须是 `mysql`，不是 `127.0.0.1`。

### 2.2 `Unknown database`

```sql
CREATE DATABASE university_exchange CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

或确认 Compose 的 `MYSQL_DATABASE` 已生效。

### 2.3 读写分离后读不到刚写入的数据

主从延迟导致。对一致性敏感的查询显式走主库，或暂时清空 `DB_REPLICA_HOST`。

## 3. Redis / Celery

### 3.1 Celery 任务不执行

按顺序排查：

1. Worker 是否启动：`docker compose ps celery-worker`
2. Broker 是否可达：RabbitMQ 管理台 15672，或 `redis-cli ping`
3. `CELERY_BROKER_URL` 是否正确
4. `CELERY_TASK_ALWAYS_EAGER` 是否被误设为 `True`（会绕过 Worker）
5. 查看 Worker 日志中的反序列化/导入错误

### 3.2 通知/积分更新延迟

这是异步设计的正常现象。若长时间不更新：

- 检查 `send_notification_async` / `update_user_points_async` 是否失败重试
- 检查 `transaction.on_commit` 是否因事务回滚而未派发
- 确认通知记录已写入再检查 Worker

### 3.3 积分重复发放

一次性行为通过 `PointsRecord` 幂等检查。若发现重复：

- 检查是否绕过了 `queue_update_user_points`
- 检查自定义代码是否直接调用 `update_user_points_async.delay`
- 检查并发场景是否缺少 `select_for_update`

## 4. WebSocket

### 4.1 连接立即关闭 4001

未认证。确认：

- 使用 `['jwt', '<access-token>']` 子协议，或 URL 带 `?token=`
- token 未过期
- 公共聊天室要求登录

### 4.2 私聊 4003

双方不是好友。私聊连接前会调用 `Friend.is_friend` 校验。

### 4.3 私聊 4004

目标用户不存在，检查 `user_id`。

### 4.4 本地 WebSocket 连不上

- 必须使用 `python start_server.py`（uvicorn/daphne），不能用 `runserver`
- 前端 Vite 代理 `/ws` 是否指向 `ws://localhost:8000`
- 生产确认 Nginx `/ws/` 转发到 `django-ws:8001`，并带有 `Upgrade` / `Connection` 头

### 4.5 多标签页在线人数不准

在线人数是“最近 5 分钟活跃用户数”，不是连接数；断开不会立即减一，属设计行为。

### 4.6 生产多实例消息不同步

`DEBUG=True` 时使用 InMemoryChannelLayer，只支持单进程。
生产必须 `DEBUG=False` 并使用 Redis Channel Layer。

## 5. 搜索

### 5.1 ES 连接失败

```bash
curl http://localhost:9200/_cluster/health
```

若 ES 未启动，搜索会自动降级为 MySQL LIKE，业务不中断，但结果与性能下降。

### 5.2 搜索结果为空/不全

- 确认已执行 `rebuild_search_index --delete`
- 确认模型保存信号已触发索引任务
- 检查 Celery Worker 是否执行 `search.tasks`
- 检查索引前缀与 `ELASTICSEARCH_INDEX_PREFIX` 是否一致

### 5.3 中文分词效果差

确认 ES 镜像内置 `analysis-ik`，索引使用 `ik_max_word`，搜索使用 `ik_smart`。

## 6. 登录与前端

### 6.1 401 后反复跳登录

- 检查 refresh token 是否有效
- 检查 `/api/token/refresh/` 是否返回新 token
- 确认没有多个请求同时清空 token（前端已用共享 `refreshPromise` 处理）
- 检查系统时间是否偏差过大导致 JWT 校验失败

### 6.2 CORS 错误

- `CORS_ALLOWED_ORIGINS` 是否包含前端实际 origin（协议+域名+端口）
- 生产不要开启 `CORS_ALLOW_ALL_ORIGINS`
- 预检请求是否被 Nginx 拦截

### 6.3 图片/媒体 404

- 开发：确认 `DEBUG=True` 且 `MEDIA_ROOT` 存在
- Docker：确认 `./backend/media` 已挂载到 Nginx
- 生产：确认 Nginx `/media/` 指向 `/app/media/`

### 6.4 前端请求地址不对

`frontend/src/utils/config.ts` 中 `apiBaseUrl` 读取 `VITE_API_BASE_URL`，缺省为 `/api`。
开发环境保持 `/api` 走 Vite 代理；生产环境可配置为完整前缀（必须包含 `/api`），
或继续依赖 Nginx 反向代理。媒体地址由 `VITE_MEDIA_BASE_URL` 控制。

## 7. 小程序

### 7.1 请求失败/域名不合法

- `VUE_APP_API_BASE_URL` 必须包含 `/api`
- 生产必须是 HTTPS，并在微信公众平台配置合法域名
- 本地开发可在开发者工具中临时关闭域名校验

### 7.2 WebSocket 连不上

- `VUE_APP_WS_BASE_URL` 必须包含 `/ws/chat`
- 代码会追加 `/public` 或 `/private/<id>`，不要重复拼接
- token 通过 `jwt` 子协议传递，不要放在 URL

## 8. 已修复问题（保留记录）

以下问题已在 2026-11-13 修复，仅用于排查历史版本。

### 8.1 旧版 `/api/notifications/` 接口不可用（已修复）

旧 `forum.NotificationViewSet` 使用了统一通知模型不存在的 `user` 字段，
并注册在 `/api/notifications/`。该 ViewSet 与相关路由、兼容序列化器已删除。

当前行为：

- `/api/notifications/` 返回 404
- 统一使用 `/api/users/notifications/...`
- H5 与小程序通知页均已切换到新路径

### 8.2 `notifications/mark-all-read/`（连字符）不可达（已修复）

该路径已随遗留 ViewSet 一并删除。标记全部已读请使用：

```text
POST /api/users/notifications/mark_all_read/
```

### 8.3 `django-init` 缺少环境变量（已修复）

`docker-compose.prod.yml` 已为 `django-init` 补齐数据库、Redis、Celery、
Elasticsearch 与 `DJANGO_SECRET_KEY` 等环境变量，见
[部署指南 4.3](deployment.md#43-初始化服务环境变量)。

### 8.4 小程序 API 索引未导出 `searchApi`（已修复）

`mp-weixin/api/index.js` 已导出 `searchApi`，并同步挂在默认导出对象的
`search` 字段上。新页面既可从索引导入，也可继续直接 `import` `api/search.js`。

## 9. 仍然无法解决

收集以下信息后提交 Issue：

- 复现步骤
- 期望结果与实际结果
- 后端/前端/Worker 日志片段
- 相关配置（**隐去密钥**）
- 浏览器/小程序基础库版本
