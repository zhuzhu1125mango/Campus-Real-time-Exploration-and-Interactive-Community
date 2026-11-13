# 聊天与通知 API

## 1. 公共聊天 REST

前缀：`/api/chat/`。

| 方法 | 路径 | 认证 | 说明 |
|---|---|---|---|
| GET | `/api/chat/health/` | 公开 | 健康检查 |
| GET | `/api/chat/messages/recent_messages/` | 登录 | 最近消息，`?limit=` |
| GET | `/api/chat/messages/online_users/` | 公开 | 最近活跃人数 |
| POST | `/api/chat/send_message/` | 登录 | HTTP 发送消息 |
| GET/POST | `/api/chat/messages/` | 登录 | 消息列表/创建 |
| GET/PATCH/PUT/DELETE | `/api/chat/messages/{id}/` | 登录，本人/管理员 | 消息管理 |

在线人数响应：

```json
{
  "count": 12,
  "window_seconds": 300
}
```

> 在线人数是“最近 5 分钟活跃用户数”，不是精确连接数。

实时收发请使用 WebSocket，见 [WebSocket 协议](../websocket-protocol.md)。

## 2. 私信 REST

前缀：`/api/users/messages/`，详见 [社交 API](social.md)。

## 3. 通知

统一使用 `notifications.Notification`。推荐前缀：`/api/users/notifications/`。

| 方法 | 路径 | 认证 | 说明 |
|---|---|---|---|
| GET | `/api/users/notifications/` | 登录 | 我的通知（分页） |
| GET | `/api/users/notifications/{id}/` | 登录 | 通知详情 |
| POST | `/api/users/notifications/{id}/mark_read/` | 登录 | 单条已读 |
| POST | `/api/users/notifications/mark_all_read/` | 登录 | 全部已读 |
| GET | `/api/users/notifications/unread/` | 登录 | 未读列表 |
| GET | `/api/users/notifications/count/` | 登录 | 未读数量 |
| GET | `/api/users/notifications/by_type/?type=message` | 登录 | 按类型筛选 |
| GET | `/api/users/notifications/type_counts/` | 登录 | 各类型数量 |
| DELETE | `/api/users/notifications/delete_all_read/` | 登录 | 删除全部已读 |
| POST | `/api/users/notifications/send_notification/` | 管理员 | 发送系统通知 |

### 3.1 通知类型

| 类型 | 用途 |
|---|---|
| `system` | 系统通知 |
| `interaction` | 点赞、关注、好友请求等 |
| `content_comment` | 评论/回复 |
| `message` | 私信 |
| `activity` | 活动通知 |

### 3.2 响应结构

```json
{
  "id": 1,
  "recipient": 1,
  "sender": {"id": 2, "username": "bob"},
  "notification_type": "message",
  "title": "新私信",
  "content": "bob 给您发送了一条私信",
  "url": "/chat/2",
  "is_read": false,
  "created_at": "2026-11-13T10:00:00+08:00"
}
```

### 3.3 实时推送

创建通知后：

```text
Notification.post_save
  → transaction.on_commit
  → Celery send_notification_async
  → WebSocket group user_<recipient_id>
  → 客户端收到 notification + unread_notifications
```

### 3.4 旧接口已移除

`/api/notifications/` 兼容层已删除，请求返回 404。
请统一使用 `/api/users/notifications/...`。

## 4. 通知触发场景

| 场景 | 类型 | 接收者 |
|---|---|---|
| 好友请求 | `interaction` | 被请求方 |
| 好友请求接受 | `interaction` | 请求方 |
| 好友被移除 | `interaction` | 被移除方 |
| 帖子回复 | `interaction` / `content_comment` | 主题作者/被回复者 |
| 评论/回复内容 | `content_comment` | 内容作者/父评论作者 |
| 点赞 | `interaction` | 内容作者 |
| 私信 | `message` | 接收者 |
| 系统公告 | `system` | 指定用户/全体 |

## 5. WebSocket

| 场景 | 地址 |
|---|---|
| 公共聊天 | `ws://host/ws/chat/public/` |
| 私信 | `ws://host/ws/chat/private/<user_id>/` |

认证、消息格式、关闭码见 [WebSocket 协议](../websocket-protocol.md)。
