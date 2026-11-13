# 社交 API（好友、收藏、动态、私信）

前缀均在 `/api/users/` 下。

## 1. 收藏

`Favorite` 是通用收藏，使用 `ContentType` 多态关联任意模型。
`content_type` 参数格式为 `app_label.model`，例如 `schools.school`。

| 方法 | 路径 | 认证 | 说明 |
|---|---|---|---|
| GET | `/api/users/favorites/` | 登录 | 我的收藏（分页） |
| POST | `/api/users/favorites/` | 登录 | 创建收藏 |
| GET/PATCH/PUT/DELETE | `/api/users/favorites/{id}/` | 所有者 | 收藏详情/更新/删除 |
| POST | `/api/users/favorites/add_favorite/` | 登录 | 添加收藏（推荐） |
| DELETE | `/api/users/favorites/remove_favorite/` | 登录 | 按内容移除收藏 |
| GET | `/api/users/favorites/check_favorite/` | 登录 | 检查是否已收藏 |
| GET | `/api/users/favorites/by_category/` | 登录 | 按分类筛选 |

### 1.1 添加收藏

```http
POST /api/users/favorites/add_favorite/
Authorization: Bearer <access>
Content-Type: application/json

{
  "content_type": "schools.school",
  "object_id": 1,
  "category": "school",
  "note": "目标院校"
}
```

响应：

```json
{"id": 10, "message": "收藏成功"}
```

规则：

- 同一用户对同一对象只能收藏一次
- 收藏对象必须存在
- 收藏学校时会同步 `User.favorite_schools`
- 收藏积分异步发放

### 1.2 检查与移除

```http
GET /api/users/favorites/check_favorite/?content_type=schools.school&object_id=1
→ {"is_favorited": true}
```

```http
DELETE /api/users/favorites/remove_favorite/
Content-Type: application/json

{"content_type": "schools.school", "object_id": 1}
```

## 2. 好友

好友关系与“关注”是两套独立关系：

- 关注：`User.following`，单向，用于内容流
- 好友：`friendships.Friend`，双向，用于私信权限

### 2.1 好友请求

| 方法 | 路径 | 认证 | 说明 |
|---|---|---|---|
| GET/POST | `/api/users/friend-requests/` | 登录 | 请求列表/发起请求 |
| GET | `/api/users/friend-requests/received/` | 登录 | 收到的待处理请求 |
| GET | `/api/users/friend-requests/sent/` | 登录 | 我发出的请求 |
| GET | `/api/users/friend-requests/{id}/` | 登录 | 请求详情 |
| POST | `/api/users/friend-requests/{id}/accept/` | 接收者 | 接受 |
| POST | `/api/users/friend-requests/{id}/reject/` | 接收者 | 拒绝 |

创建请求 body 通常包含 `receiver`（用户 ID）。接受/拒绝只有接收者可以操作，
否则返回 403。接受后会创建双向好友关系并发送通知。

### 2.2 好友列表

| 方法 | 路径 | 认证 | 说明 |
|---|---|---|---|
| GET | `/api/users/friends/friend_list/` | 登录 | 好友列表 |
| GET | `/api/users/friends/check/?user_id=2` | 登录 | 是否好友 |
| POST | `/api/users/friends/remove/` | 登录 | 移除好友，body `{"friend_id": 2}` |

好友列表响应：

```json
{
  "friends": [{"id": 2, "username": "bob"}],
  "count": 1
}
```

> 私信 WebSocket 要求双方是好友，否则连接关闭码为 4003。

## 3. 用户动态

| 方法 | 路径 | 认证 | 说明 |
|---|---|---|---|
| GET/POST | `/api/users/activities/` | 读公开/写登录 | 动态列表/发布 |
| GET/PATCH/PUT/DELETE | `/api/users/activities/{id}/` | 读公开/所有者写 | 动态详情/更新/删除 |
| GET | `/api/users/activities/feed/` | 登录 | 关注流（好友/关注 + 自己） |
| GET | `/api/users/activities/my_activities/` | 登录 | 我的动态 |
| POST | `/api/users/activities/{id}/like/` | 登录 | 点赞 |
| POST | `/api/users/activities/{id}/unlike/` | 登录 | 取消点赞 |
| GET | `/api/users/activities/{id}/comments/` | 登录 | 动态评论 |
| GET/POST | `/api/users/activity-comments/` | 登录 | 评论 |
| GET/PATCH/PUT/DELETE | `/api/users/activity-comments/{id}/` | 登录，本人/管理员 | 评论管理 |
| GET/POST | `/api/users/activity-likes/` | 登录 | 点赞记录 |

动态字段：

| 字段 | 说明 |
|---|---|
| `activity_type` | `post`/`comment`/`like`/`follow`/`enroll`/`share`/`custom` |
| `content` | 动态正文 |
| `target_content_type` / `target_object_id` | 关联对象 |
| `target_title` / `target_url` | 展示用 |
| `is_public` | 是否公开 |
| `likes_count` / `comments_count` | 计数 |

## 4. 私信

| 方法 | 路径 | 认证 | 说明 |
|---|---|---|---|
| GET/POST | `/api/users/messages/` | 登录 | 消息列表/发送 |
| GET/PATCH/PUT/DELETE | `/api/users/messages/{id}/` | 参与者 | 消息详情/更新/删除 |
| GET | `/api/users/messages/conversations/` | 登录 | 会话列表 |
| GET | `/api/users/messages/conversation/?user_id=2` | 登录 | 与某人的对话 |
| GET | `/api/users/messages/unread_count/` | 登录 | 未读总数 |
| POST | `/api/users/messages/mark_all_read/` | 登录 | 标记来自某人的全部消息已读 |
| POST | `/api/users/messages/{user_id}/mark_read/` | 登录 | 同上（按用户） |
| GET/POST | `/api/users/messages/{user_id}/` | 登录 | 用户维度消息 |
| POST | `/api/users/messages/{id}/mark_read/` | 接收者 | 单条已读 |

### 4.1 会话列表

```http
GET /api/users/messages/conversations/
```

响应为数组，每项包含：

```json
{
  "user": {"id": 2, "username": "bob", "avatar": null},
  "last_message": {"content": "你好", "created_at": "..."},
  "unread_count": 3
}
```

### 4.2 对话

```http
GET /api/users/messages/conversation/?user_id=2&page=1&page_size=20
```

- 不带 `page`：返回全部消息（升序，兼容旧逻辑）
- 带 `page`：倒序取最新一页，返回前恢复升序
- 打开对话会把来自对方的未读消息标记为已读

### 4.3 发送

```http
POST /api/users/messages/
Authorization: Bearer <access>
Content-Type: application/json

{"receiver": 2, "content": "你好"}
```

发送前建议确认好友关系。WebSocket 直发路径见
[WebSocket 协议](../websocket-protocol.md)。

> 路由中同时存在 `messages/{user_id}/` 与 `messages/{pk}/`，两者正则都能匹配数字。
> 客户端应优先使用 `conversations/`、`conversation/?user_id=`、`mark_read/` 等明确路径，
> 避免依赖有歧义的详情路由。
