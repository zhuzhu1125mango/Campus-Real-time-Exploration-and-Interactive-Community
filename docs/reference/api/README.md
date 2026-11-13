# REST API 参考

## 1. 基础约定

| 项 | 值 |
|---|---|
| Base URL | `/api`（开发 `http://localhost:8000/api`） |
| 数据格式 | JSON（上传接口使用 multipart/form-data） |
| 认证 | `Authorization: Bearer <access_token>` |
| 字符集 | UTF-8 |
| 时间 | ISO 8601，时区 `Asia/Shanghai` |

路径可能带或不带尾部斜杠（Django `APPEND_SLASH` 默认会重定向）。
DRF 还支持 `?format=json` 或 `.json` 后缀，但业务代码统一使用默认 JSON。

## 2. 认证

### 2.1 获取 Token

```http
POST /api/token/
Content-Type: application/json

{"username": "alice", "password": "secret"}
```

响应：

```json
{
  "access": "<jwt>",
  "refresh": "<jwt>"
}
```

也可以使用业务登录接口 `POST /api/users/users/login/`，额外返回 `user` 信息。

### 2.2 刷新与校验

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/token/refresh/` | body `{ "refresh": "..." }` |
| POST | `/api/token/verify/` | 校验 token 是否有效 |

JWT 参数：

| 项 | 值 |
|---|---|
| access 有效期 | 30 分钟 |
| refresh 有效期 | 1 天 |
| 刷新轮换 | 开启 |
| 旧 refresh 拉黑 | 开启 |

### 2.3 登出

```http
POST /api/users/users/logout/
Authorization: Bearer <access>
Content-Type: application/json

{"refresh": "<refresh_token>"}
```

服务端会将 refresh token 加入黑名单。

## 3. 分页

存在两种分页类：

| 场景 | 默认 `page_size` | 查询参数 |
|---|---|---|
| DRF 全局默认 | 12 | `page`、`page_size`（视视图而定） |
| `BaseModelViewSet` | 10 | `page`、`page_size`（上限 100） |

分页响应：

```json
{
  "count": 100,
  "next": "http://host/api/xxx/?page=2",
  "previous": null,
  "results": []
}
```

## 4. 限流

| 范围 | 速率 | 触发场景 |
|---|---|---|
| 匿名 | 60/min | 未登录请求 |
| 登录用户 | 120/min | 普通请求 |
| 登录接口 | 10/min | `/users/login/` 等 |
| 验证码 | 3/min | 发送邮箱/短信验证码 |
| 搜索 | 30/min | 搜索相关接口 |
| 写操作 | 60/min | 发帖、评论、点赞等 |

超限返回 `429 Too Many Requests`。

## 5. 错误格式

| 状态码 | 含义 |
|---|---|
| 400 | 参数错误 / 业务校验失败 |
| 401 | 未认证或 token 失效 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 429 | 触发限流 |
| 500 | 服务端错误 |

常见 body：

```json
{"detail": "未找到。"}
```

```json
{"field": ["该字段是必填项。"]}
```

```json
{"error": "今天已经签到过了"}
```

## 6. 权限标记

本文档使用以下简写：

| 标记 | 含义 |
|---|---|
| 公开 | 无需登录 |
| 登录 | 需要有效 access token |
| 管理员 | `is_staff=True` |
| 所有者 | 资源作者或管理员 |
| 好友 | 双方存在好友关系 |

## 7. 模块索引

| 模块 | 文档 | 路径前缀 |
|---|---|---|
| 用户、认证、积分、关注 | [users.md](users.md) | `/api/users/`、`/api/token/` |
| 好友、收藏、动态、私信 | [social.md](social.md) | `/api/users/` |
| 论坛 | [forum.md](forum.md) | `/api/` |
| 院校、专业、活动、探索 | [schools.md](schools.md) | `/api/schools/` |
| 学习 | [learning.md](learning.md) | `/api/learning/` |
| 内容中心 | [content.md](content.md) | `/api/content/` |
| 聊天与通知 | [chat-and-notifications.md](chat-and-notifications.md) | `/api/chat/`、`/api/users/notifications/` |
| Feed 与搜索 | [feed-and-search.md](feed-and-search.md) | `/api/feed/`、`/api/search/` |

## 8. 重要路径说明

### 8.1 论坛挂在根路径

论坛路由不是 `/api/forum/`，而是直接挂在 `/api/`：

- `/api/categories/`
- `/api/boards/`
- `/api/topics/`
- `/api/posts/`
- `/api/comments/`
- `/api/tags/`
- `/api/bookmarks/`

旧文档中的 `/api/forum/...` 已过时。

### 8.2 通知挂载点

通知统一使用：

```text
/api/users/notifications/
```

旧 `/api/notifications/` 兼容层已移除，请求会返回 404。
H5 与小程序的通知页均已切换到新路径。

## 9. 健康检查

| 方法 | 路径 | 认证 |
|---|---|---|
| GET | `/api/health/` | 公开 |
| GET | `/health/` | 公开 |
| GET | `/api/chat/health/` | 公开 |
| GET | `/api/schools/test-connection/` | 公开 |
