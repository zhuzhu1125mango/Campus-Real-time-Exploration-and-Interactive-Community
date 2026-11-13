# 实时通信（WebSocket）

实时能力基于 Django Channels + Redis Channel Layer，生产环境由独立进程提供。

## 1. 入口与配置

| 场景 | 入口 | 说明 |
|---|---|---|
| 开发（一体） | `config.asgi:application` | `start_server.py` 使用 uvicorn 启动 |
| 生产 HTTP | `config.asgi_http:application` | 仅 Django HTTP |
| 生产 WebSocket | `config.asgi_ws:application` | 仅 Channels 路由 |

Channel Layer：

| 环境 | 后端 |
|---|---|
| `DEBUG=True` | `InMemoryChannelLayer`（仅单进程） |
| `DEBUG=False` | `channels_redis.core.RedisChannelLayer`，容量 1500，过期 10s |

生产必须使用 Redis 层，否则多实例之间无法广播。

## 2. 路由

`chat/routing.py`：

| 路径 | 消费者 |
|---|---|
| `ws/chat/public/` | `ChatConsumer` |
| `ws/chat/private/<user_id>/` | `PrivateChatConsumer` |

## 3. 认证

`chat/middleware.py` 的 `TokenAuthMiddleware` 按优先级提取 token：

1. `Sec-WebSocket-Protocol` 子协议：`['jwt', '<access_token>']`
2. URL 查询参数：`?token=<access_token>`（兼容旧客户端）

校验流程：

```text
AccessToken(token) → user_id → User.objects.get
  → 用户存在且 is_active：scope['user'] = user
  → 否则：scope['user'] = AnonymousUser()
```

推荐客户端使用子协议，避免 token 出现在日志/历史中。

## 4. 公共聊天室

### 4.1 连接

- 必须登录；未认证直接 `close(4001)`
- 加入组 `chat`
- 已登录用户额外加入 `user_<id>`，用于接收通知
- 连接时标记最近活跃

### 4.2 服务端主动消息

| `type` | 触发 | 关键字段 |
|---|---|---|
| `auth_success` | 认证通过 | `user.id`、`user.username` |
| `unread_notifications` | 连接时 | `count` |
| `welcome` | 连接时 | `online_users.count`、`metric=recently_active` |
| `online_users` | 人数变化 | `count`、`time` |
| `chat_message` | 广播 | `message`、`username`、`user_id`、`avatar`、`time` |
| `message_received` | 发送成功 | `message`、`time` |
| `notification` | 新通知 | `notification` 对象 |
| `unread_notifications` | 未读数变化 | `count` |
| `notification_marked_read` | 单条已读 | `notification_id` |
| `all_notifications_marked_read` | 全部已读 | — |
| `heartbeat_response` | 心跳 | `timestamp` |
| `error` | 校验失败 | `message` |

### 4.3 客户端消息

| `type` | 说明 |
|---|---|
| `chat_message` | 发送聊天消息，字段 `message`、可选 `client_id` |
| `heartbeat` | 心跳，字段 `timestamp` |
| `mark_notification_read` | 标记单条通知，字段 `notification_id` |
| `mark_all_notifications_read` | 标记全部通知 |

### 4.4 校验与持久化

- 频率限制：60 秒窗口最多 60 条（按用户 + 消息类型计数）
- 内容清洗：`sanitize_html`
- 空内容拒绝
- 长度上限 1000 字符
- 入库：`chat.ChatMessage`
- 入库失败只记录日志，不影响广播

## 5. 私信

### 5.1 连接前置校验

| 条件 | 失败关闭码 |
|---|---|
| 未认证 | 4001 |
| 缺少 `user_id` | 4002 |
| 目标用户不存在 | 4004 |
| 双方不是好友 | 4003 |

### 5.2 分组

```python
user_ids = sorted([str(self.user.id), str(self.target_user_id)])
room_group_name = f"private_{user_ids[0]}_{user_ids[1]}"
```

按 ID 排序保证双方进入同一个组，且不同会话互不干扰。

### 5.3 消息

客户端发送：

```json
{
  "type": "private_message",
  "content": "你好"
}
```

服务端广播：

```json
{
  "type": "private_message",
  "id": 123,
  "content": "你好",
  "sender_id": 1,
  "sender_username": "alice",
  "sender_avatar": "/media/avatars/a.png",
  "receiver_id": 2,
  "receiver_username": "bob",
  "is_read": false,
  "created_at": "2026-11-13T10:00:00+08:00"
}
```

同时：

- 持久化到 `private_messages.Message`
- 给接收者创建 `message` 类型通知
- 返回 `message_received` 确认

### 5.4 连接成功

```json
{
  "type": "private_chat_ready",
  "message": "私聊连接已建立",
  "target_user_id": 2,
  "time": "..."
}
```

## 6. 在线人数

`chat/views.py` 的 `RecentActivePresence`：

- Redis Sorted Set key：`chat:recent_active_users`
- 活跃窗口：300 秒
- 连接、心跳、发消息都会刷新活跃时间
- 统计时清理窗口外成员
- Redis 不可用时回退到进程内字典（仅单进程准确）

因此“在线人数”准确含义是**最近 5 分钟活跃用户数**。

## 7. 通知推送

通知由 Celery 任务 `send_notification_async` 推送到 `user_<id>` 组：

```text
Notification.post_save
  → transaction.on_commit
  → send_notification_async.delay(id)
  → group_send('user_<id>', {'type': 'notification', ...})
  → group_send('user_<id>', {'type': 'unread_notifications_update', ...})
  → Consumer.notification / unread_notifications_update 转发给客户端
```

注意：消费者方法名是 `unread_notifications_update`，但下发给客户端的 `type` 是
`unread_notifications`。

## 8. 关闭码

| 关闭码 | 含义 | 处理 |
|---|---|---|
| 4001 | 未认证 | 检查 token/子协议 |
| 4002 | 缺少目标用户 | 检查路由参数 |
| 4003 | 非好友 | 先建立好友关系 |
| 4004 | 目标用户不存在 | 检查 userId |

## 9. 扩展与限制

- 生产多副本共享 Redis Channel Layer，可水平扩容。
- 私聊要求好友关系，避免陌生人骚扰。
- 单条消息 1000 字符上限；如需富文本/图片，应扩展消息模型与清洗规则。
- 当前未实现消息撤回、输入中状态、离线消息补推。
