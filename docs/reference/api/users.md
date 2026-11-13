# 用户与认证 API

前缀：`/api/users/`，JWT 端点位于 `/api/token/`。

## 1. 认证与验证码

| 方法 | 路径 | 认证 | 说明 |
|---|---|---|---|
| POST | `/api/token/` | 公开 | 获取 access/refresh |
| POST | `/api/token/refresh/` | 公开 | 刷新 access |
| POST | `/api/token/verify/` | 公开 | 校验 token |
| POST | `/api/users/users/login/` | 公开 | 密码登录，返回 token + user |
| POST | `/api/users/users/email_code_login/` | 公开 | 邮箱验证码登录 |
| POST | `/api/users/users/phone_code_login/` | 公开 | 手机验证码登录 |
| POST | `/api/users/users/logout/` | 登录 | 登出，refresh 加入黑名单 |
| POST | `/api/users/users/send_email_code/` | 公开 | 发送邮箱验证码 |
| POST | `/api/users/users/send_phone_code/` | 公开 | 发送手机验证码 |
| POST | `/api/users/users/verify_code/` | 公开 | 校验验证码 |
| POST | `/api/users/users/reset_password/` | 公开 | 重置密码 |
| POST | `/api/users/email-code/` | 公开 | `send_email_code` 的别名 |
| POST | `/api/users/phone-code/` | 公开 | `send_phone_code` 的别名 |
| POST | `/api/users/verify-code/` | 公开 | `verify_code` 的别名 |
| POST | `/api/users/email-code-login/` | 公开 | 邮箱验证码登录别名 |
| POST | `/api/users/phone-code-login/` | 公开 | 手机验证码登录别名 |
| POST | `/api/users/reset-password/` | 公开 | 重置密码别名 |

### 1.1 密码登录

```http
POST /api/users/users/login/
Content-Type: application/json

{"username": "alice", "password": "secret"}
```

响应：

```json
{
  "refresh": "<jwt>",
  "access": "<jwt>",
  "user": {
    "id": 1,
    "username": "alice",
    "email": "a@example.com",
    "avatar": null,
    "points": 12,
    "level": 1
  }
}
```

### 1.2 验证码

- 发送邮箱验证码：body 至少包含 `email`，可带 `purpose`
- 发送手机验证码：body 至少包含 `phone`，可带 `purpose`
- 校验验证码：body 包含目标（`email` 或 `phone`）、`code`、`code_type`

验证码限制：

- 有效期由 `VerificationCode.expires_at` 控制
- 发送频率受 `code` 限流（3/min）
- `SMS_ENABLED=False` 时不会真正调用阿里云短信

### 1.3 注册

```http
POST /api/users/users/
Content-Type: application/json

{
  "username": "alice",
  "email": "a@example.com",
  "password": "secret",
  "password_confirm": "secret",
  "code": "123456"
}
```

> 注册只有在验证码校验通过后才设置 `is_verified=True`。

## 2. 用户资料

| 方法 | 路径 | 认证 | 说明 |
|---|---|---|---|
| GET | `/api/users/users/` | 登录 | 用户列表（分页） |
| GET | `/api/users/users/{id}/` | 公开 | 用户详情（公开字段） |
| PATCH/PUT | `/api/users/users/{id}/` | 所有者/管理员 | 更新用户 |
| DELETE | `/api/users/users/{id}/` | 所有者/管理员 | 删除用户 |
| GET | `/api/users/users/me/` | 登录 | 当前用户完整信息 |
| PATCH | `/api/users/users/update_me/` | 登录 | 更新当前用户 |
| GET | `/api/users/users/{id}/topics/` | 登录 | 用户创建的主题 |
| GET | `/api/users/users/{id}/posts/` | 登录 | 用户帖子；`include_first=true` 包含首贴 |
| GET | `/api/users/users/{id}/profile_stats/` | 登录 | 主题/帖子/回复等统计 |
| GET | `/api/users/users/search/` | 登录 | `?q=` 搜索用户 |

当前用户信息包含积分字段：

```json
{
  "id": 1,
  "username": "alice",
  "points": 120,
  "level": 2,
  "level_name": "初级学员"
}
```

资料更新支持 `avatar`、`banner` 文件上传（multipart/form-data）。

## 3. 积分与等级

| 方法 | 路径 | 认证 | 说明 |
|---|---|---|---|
| GET | `/api/users/users/{id}/points/` | 登录，本人/管理员 | 积分、等级、进度 |
| GET | `/api/users/users/{id}/points_records/` | 登录，本人/管理员 | 积分流水（分页） |
| POST | `/api/users/users/daily_checkin/` | 登录 | 每日签到 |
| GET | `/api/users/points-leaderboard/` | 公开 | 积分排行榜 |

积分详情响应：

```json
{
  "points": 120,
  "level": 2,
  "level_name": "初级学员",
  "level_progress": 46,
  "next_level_points": 150
}
```

签到规则：

- 每日一次，重复签到返回 400 `{"error": "今天已经签到过了"}`
- 基础 +5
- 连续 3 天额外 +5，连续 7 天额外 +10
- 积分异步发放，响应中的 `total_points` 可能稍后才更新

积分规则与等级阈值见 [后台任务参考](../background-jobs.md)。

## 4. 关注

| 方法 | 路径 | 认证 | 说明 |
|---|---|---|---|
| POST | `/api/users/users/{id}/follow/` | 登录 | 关注用户 |
| POST | `/api/users/users/{id}/unfollow/` | 登录 | 取消关注 |

关注关系存储在 `User.following`（自关联多对多），
与好友关系（`friendships.Friend`）是两套独立关系。

## 5. 用户资料扩展

| 方法 | 路径 | 认证 | 说明 |
|---|---|---|---|
| GET/POST | `/api/users/profiles/` | 登录 | 资料列表/创建 |
| GET/PATCH/PUT/DELETE | `/api/users/profiles/{id}/` | 所有者/管理员 | 资料详情/更新/删除 |

`UserProfile` 字段：`interests`、`target_schools`、`target_majors`、`gpa`、
`study_status`、`website`、`social_links`。

## 6. 通知（挂载在 users 下）

推荐使用以下路径，详见 [聊天与通知](chat-and-notifications.md)：

| 方法 | 路径 |
|---|---|
| GET | `/api/users/notifications/` |
| GET | `/api/users/notifications/{id}/` |
| POST | `/api/users/notifications/{id}/mark_read/` |
| POST | `/api/users/notifications/mark_all_read/` |
| GET | `/api/users/notifications/unread/` |
| GET | `/api/users/notifications/count/` |
| GET | `/api/users/notifications/by_type/?type=message` |
| GET | `/api/users/notifications/type_counts/` |
| DELETE | `/api/users/notifications/delete_all_read/` |
| POST | `/api/users/notifications/send_notification/`（管理员） |

## 7. 调试接口

以下接口仅用于本地排查，生产应通过 Nginx/防火墙限制访问：

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/users/debug-avatar/` | 头像路径调试 |
| GET | `/api/users/test-static/` | 静态文件检查 |
| GET | `/api/users/list-avatars/` | 列出头像文件 |
| GET | `/api/users/test-html-media/` | HTML/媒体检查 |
