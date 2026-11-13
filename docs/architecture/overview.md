# 架构总览

本文解释系统由哪些部分组成、请求如何流动、以及关键设计取舍。
具体实现细节见后端、前端、实时通信、异步与搜索等分册。

## 1. 系统上下文

```text
┌─────────────┐   HTTPS/JSON   ┌──────────────────────────────┐
│ H5 前端      │───────────────→│                              │
│ (Vue 3)     │   WSS          │        Nginx / 网关           │
└─────────────┘───────────────→│                              │
┌─────────────┐   HTTPS/JSON   │                              │
│ 微信小程序   │───────────────→│                              │
└─────────────┘                └───────┬──────────────┬───────┘
                                       │ /api /media  │ /ws
                                       ↓              ↓
                              ┌──────────────┐ ┌──────────────┐
                              │ django-http  │ │  django-ws   │
                              │  DRF + ORM   │ │  Channels    │
                              └──────┬───────┘ └──────┬───────┘
                                     │                │
              ┌──────────────────────┼────────────────┘
              ↓                      ↓
       ┌─────────────┐        ┌─────────────┐
       │   MySQL     │        │    Redis    │
       │ 主库/从库    │        │ WS + Cache  │
       └─────────────┘        └──────┬──────┘
                                     ↑
       ┌─────────────┐        ┌──────┴──────┐
       │Elasticsearch│←───────│Celery Worker│←── RabbitMQ
       └─────────────┘        └─────────────┘
```

## 2. 组件职责

| 组件 | 职责 |
|---|---|
| H5（`frontend/`） | 面向浏览器的完整功能端：院校、论坛、学习、内容、私信、聊天、个人中心 |
| 小程序（`mp-weixin/`） | 微信生态端：核心浏览、论坛、课程、聊天、私信 |
| `django-http` | REST API、Admin、认证、业务读写 |
| `django-ws` | WebSocket 长连接、公共聊天、私信、通知推送 |
| `celery-worker` | 积分、通知推送、ES 索引更新 |
| MySQL | 业务主数据，可选主从读写分离 |
| Redis WS | Channels Channel Layer |
| Redis Cache | 业务缓存、限流、Celery 结果 |
| RabbitMQ | Celery Broker |
| Elasticsearch | 全局搜索，失败时降级 MySQL |
| Nginx | TLS、静态/媒体、反向代理、WebSocket 升级 |

## 3. 关键请求流程

### 3.1 普通 HTTP 请求

```text
客户端 → Nginx → django-http
        → DRF 认证（JWT/Session）
        → ViewSet（权限、限流、查询优化）
        → Serializer
        → ORM（读：可走从库）
        → Response
```

### 3.2 写操作与异步副作用

以发帖为例：

```text
POST /api/topics/
  → 校验权限与限流
  → 事务内写入 Topic/Post
  → 清洗 HTML
  → transaction.on_commit 派发积分任务
  → transaction.on_commit 派发通知任务
  → post_save 信号派发 ES 索引任务
  → 立即返回
        ↓
Celery Worker：更新积分、写通知、推送 WS、更新索引
```

设计目的：主请求不被旁路逻辑拖慢；事务回滚时不会产生“幽灵任务”。

### 3.3 WebSocket 消息

```text
客户端 → Nginx /ws/ → django-ws
  → TokenAuthMiddleware（JWT）
  → ChatConsumer / PrivateChatConsumer
  → 频率限制 + HTML 清洗
  → 持久化（ChatMessage / Message）
  → channel_layer.group_send
  → 同组客户端收到消息
```

### 3.4 搜索

```text
GET /api/search/?q=...
  → SearchService
  → ES 可用：ik 分词查询，取 id 后回表
  → ES 不可用：MySQL icontains 降级
  → 统一结构返回
```

## 4. 核心设计决策

| 决策 | 原因 | 代价/注意 |
|---|---|---|
| HTTP 与 WebSocket 进程分离 | 长连接会占用大量协程/连接，分离后各自扩容 | 需要两个启动入口与 Nginx 路由 |
| Redis 拆分为 WS 与 Cache | 避免 Channel Layer 与业务缓存互相影响 | 多一个实例与配置项 |
| 统一 `notifications.Notification` | 避免多套通知模型与重复推送 | 旧 `/api/notifications` 兼容层需清理 |
| ES + MySQL 降级 | 中文搜索体验与可用性兼顾 | 降级时性能与召回下降 |
| Celery + `transaction.on_commit` | 异步化且避免读到未提交数据 | 任务延迟、需监控 Worker |
| 按领域拆分 Django app | 降低耦合，便于独立演进 | app 数量多，跨 app 依赖需克制 |
| 管理端使用 Django Admin | 降低后台开发成本 | 复杂运营需求需自定义页面 |
| H5 多账号 token 槽位 | 支持切换账号 | 请求层复杂度上升 |

## 5. 非功能设计

### 5.1 性能

- 列表接口统一分页；论坛/学校使用 `annotate` 与 `select_related` 降低 N+1。
- 学校列表等热点数据走统一缓存层。
- Vite `manualChunks` 拆分大依赖，ECharts 按需引入。
- 生产 HTTP 使用 gunicorn + uvicorn worker，WebSocket 使用独立 uvicorn。

### 5.2 可用性

- ES 故障自动降级。
- 缓存异常时直接执行 loader，不阻塞业务。
- Celery 任务失败自动重试（最多 3 次）。
- WebSocket 断开后前端/小程序有重连与心跳。

### 5.3 安全

- 生产强制 `DJANGO_SECRET_KEY`，关闭 `DEBUG`。
- CORS 白名单、CSRF、Cookie Secure/HttpOnly。
- 富文本 `bleach` 清洗；H5 `v-html` 二次过滤。
- WebSocket JWT 认证、频率限制、消息长度限制。
- Nginx 安全响应头与 HTTPS。

详见 [安全说明](../project/security.md)。

## 6. 与代码的对应关系

| 概念 | 代码位置 |
|---|---|
| 路由总入口 | `backend/config/urls.py` |
| 设置 | `backend/config/settings.py` |
| ASGI 入口 | `backend/config/asgi.py`、`asgi_http.py`、`asgi_ws.py` |
| Celery | `backend/config/celery.py` |
| 读写分离 | `backend/config/db_router.py` |
| 通用 ViewSet | `backend/core/base_viewsets.py` |
| 缓存 | `backend/core/cache_utils.py` |
| HTML 清洗 | `backend/core/html_sanitizer.py` |
| WebSocket 消费者 | `backend/chat/consumers.py` |
| 搜索 | `backend/search/` |
| 通知 | `backend/notifications/` |
| 前端请求层 | `frontend/src/utils/request.ts` |
| 前端路由 | `frontend/src/router/index.ts` |

## 7. 延伸阅读

- [后端架构](backend.md)
- [前端架构](frontend.md)
- [实时通信](realtime.md)
- [异步、搜索与缓存](async-search-cache.md)
- [数据模型](../reference/data-model.md)
