# WebSocket 协议

## 1. 连接地址

| 场景 | 地址 |
|---|---|
| 公共聊天室 | `ws://<host>/ws/chat/public/` |
| 私信 | `ws://<host>/ws/chat/private/<user_id>/` |
| 生产 | `wss://<host>/ws/chat/...` |

`<user_id>` 是聊天对方的用户 ID，不是当前用户。

## 2. 认证

### 2.1 推荐：子协议

```javascript
const ws = new WebSocket(url, ['jwt', accessToken])
```

服务端读取 `Sec-WebSocket-Protocol` 的第二个值作为 JWT。

### 2.2 兼容：查询参数

```text
ws://host/ws/chat/public/?token=<access_token>
```

> 查询参数可能被日志记录，生产优先使用子协议。

### 2.3 认证结果

| 情况 | 结果 |
|---|---|
| 有效 token + 活跃用户 | `scope.user` = 用户 |
| 无 token / 无效 / 过期 | 匿名用户 |
| 公共聊天匿名 | 关闭码 4001 |
| 私信匿名 | 关闭码 4001 |

## 3. 通用约定

- 所有消息为 JSON 文本帧
- 客户端消息必须包含 `type`
- 时间字段为 ISO 8601 字符串
- 服务端错误统一为：

```json
{"type": "error", "message": "错误描述", "time": "..."}
```

- 心跳建议 30–60 秒一次

## 4. 公共聊天室

### 4.1 客户端 → 服务端

| `type` | 字段 | 说明 |
|---|---|---|
| `heartbeat` | `timestamp` | 心跳 |
| `chat_message` | `message`、可选 `client_id` | 发送消息 |
| `mark_notification_read` | `notification_id` | 标记单条通知已读 |
| `mark_all_notifications_read` | 无 | 标记全部通知已读 |

发送消息示例：

```json
{
  "type": "chat_message",
  "message": "大家好",
  "client_id": "local-123"
}
```

### 4.2 服务端 → 客户端

| `type` | 字段 | 触发 |
|---|---|---|
| `auth_success` | `message`、`user{id,username}` | 认证通过 |
| `unread_notifications` | `count` | 连接时/未读数变化 |
| `welcome` | `message`、`time`、`online_users{count,metric}` | 连接成功 |
| `online_users` | `count`、`time` | 人数变化 |
| `chat_message` | `message`、`username`、`user_id`、`avatar`、`time` | 收到广播 |
| `message_received` | `message`、`time` | 发送确认 |
| `notification` | `notification{}`、`time` | 新通知 |
| `notification_marked_read` | `notification_id` | 单条已读 |
| `all_notifications_marked_read` | 无 | 全部已读 |
| `heartbeat_response` | `timestamp` | 心跳响应 |
| `error` | `message`、`time` | 校验失败 |

`online_users.metric` 固定为 `recently_active`，表示最近 5 分钟活跃用户。

### 4.3 校验规则

| 规则 | 限制 |
|---|---|
| 频率 | 60 秒最多 60 条 |
| 长度 | ≤ 1000 字符 |
| 空内容 | 拒绝 |
| HTML | `sanitize_html` 清洗 |
| 持久化 | 写入 `chat_chatmessage` |

## 5. 私信

### 5.1 连接前置条件

| 条件 | 失败关闭码 |
|---|---|
| 已登录 | 4001 |
| 提供 `user_id` | 4002 |
| 目标用户存在 | 4004 |
| 双方是好友 | 4003 |

### 5.2 客户端 → 服务端

| `type` | 字段 | 说明 |
|---|---|---|
| `heartbeat` | `timestamp` | 心跳 |
| `private_message` | `content` | 发送私信 |

```json
{"type": "private_message", "content": "你好"}
```

### 5.3 服务端 → 客户端

| `type` | 字段 | 触发 |
|---|---|---|
| `private_chat_ready` | `message`、`target_user_id`、`time` | 连接成功 |
| `private_message` | `id`、`content`、`sender_id`、`sender_username`、`sender_avatar`、`receiver_id`、`receiver_username`、`is_read`、`created_at` | 收到消息 |
| `message_received` | `message`、`time` | 发送确认 |
| `heartbeat_response` | `timestamp` | 心跳 |
| `error` | `message`、`time` | 校验失败 |

### 5.4 副作用

- 持久化到 `users_message`
- 给接收者创建 `message` 类型通知
- 通知通过 Celery 异步推送

## 6. 分组

| 组名 | 用途 |
|---|---|
| `chat` | 公共聊天室广播 |
| `user_<id>` | 某个用户的实时通知 |
| `private_<minId>_<maxId>` | 两人私信会话 |

私信组名按用户 ID 排序，保证双方进入同一组。

## 7. 在线状态

- Redis Sorted Set：`chat:recent_active_users`
- 活跃窗口：300 秒
- 连接、心跳、发消息都会刷新
- 统计时自动清理过期成员
- Redis 不可用时回退进程内字典（仅单进程准确）

## 8. 关闭码

| 关闭码 | 含义 |
|---|---|
| 4001 | 未认证 |
| 4002 | 缺少目标用户 ID |
| 4003 | 双方不是好友 |
| 4004 | 目标用户不存在 |

客户端收到关闭后应停止自动重连，先修正 token、参数或好友关系。

## 9. 客户端实现建议

1. 连接时携带 `['jwt', token]`。
2. 打开后启动心跳定时器（30–60 秒）。
3. 监听 `error` 并提示用户。
4. 非 4xxx 关闭码才自动重连，采用指数退避。
5. 页面卸载时清除心跳与重连定时器，并关闭连接。
6. 收到 `notification` 后刷新未读数或通知列表。

## 10. 前端与小程序实现

| 端 | 文件 |
|---|---|
| H5 公共聊天 | `frontend/src/views/ChatRoom.vue` |
| H5 私信 | `frontend/src/components/ChatDetail.vue` |
| 小程序公共聊天 | `mp-weixin/pages/chat-room/chat-room.vue` |
| 小程序私信 | `mp-weixin/pages/chat-detail/chat-detail.vue` |
| 小程序 URL 工具 | `mp-weixin/api/request.js` |

小程序环境变量：

```env
VUE_APP_WS_BASE_URL=wss://api.example.com/ws/chat
```

代码会自动追加 `/public` 或 `/private/<id>`。
