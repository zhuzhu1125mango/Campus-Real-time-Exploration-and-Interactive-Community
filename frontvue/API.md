# 前端API调用文档

## 1. 用户相关API

### 1.1 登录

**密码登录**
- 接口: `POST /api/users/users/login/`
- 参数: `{ username: string, password: string }`
- 响应: `{ access: string, refresh: string, user: User }`

**邮箱验证码登录**
- 接口: `POST /api/users/users/email_code_login/`
- 参数: `{ email: string, code: string }`
- 响应: `{ access: string, refresh: string, user: User }`

**手机验证码登录**
- 接口: `POST /api/users/users/phone_code_login/`
- 参数: `{ phone: string, code: string }`
- 响应: `{ access: string, refresh: string, user: User }`

### 1.2 注册

- 接口: `POST /api/users/users/`
- 参数: `{ username: string, email?: string, phone?: string, password: string, password_confirm: string, code?: string }`
- 响应: `User`

### 1.3 获取用户信息

- 接口: `GET /api/users/users/me/`
- 响应: `User`

### 1.4 刷新token

- 接口: `POST /api/token/refresh/`
- 参数: `{ refresh: string }`
- 响应: `{ access: string, refresh: string }`

### 1.5 退出登录

- 接口: `POST /api/users/users/logout/`
- 响应: `{ detail: string }`

## 2. 论坛相关API

### 2.1 帖子相关

**获取帖子详情**
- 接口: `GET /api/forum/posts/{postId}/`
- 响应: `Post`

**获取帖子评论**
- 接口: `GET /api/forum/posts/{postId}/comments/`
- 响应: `{ results: Comment[] }`

**添加评论**
- 接口: `POST /api/forum/comments/`
- 参数: `{ post: number, content: string, parent?: number }`
- 响应: `Comment`

**点赞帖子**
- 接口: `POST /api/forum/posts/{postId}/like/`
- 响应: `void`

**取消点赞帖子**
- 接口: `DELETE /api/forum/posts/{postId}/like/`
- 响应: `void`

**举报帖子**
- 接口: `POST /api/forum/posts/{postId}/report/`
- 参数: `{ reason: string }`
- 响应: `void`

**更新帖子**
- 接口: `PATCH /api/forum/posts/{postId}/`
- 参数: `{ content: string }`
- 响应: `Post`

**删除帖子**
- 接口: `DELETE /api/forum/posts/{postId}/`
- 响应: `void`

### 2.2 评论相关

**点赞评论**
- 接口: `POST /api/forum/comments/{commentId}/like/`
- 响应: `void`

### 2.3 分类相关

**获取分类列表**
- 接口: `GET /api/forum/categories/`
- 响应: `Category[]`

### 2.4 板块相关

**获取板块列表**
- 接口: `GET /api/forum/boards/`
- 响应: `Board[]` 或 `{ count: number, next: string, previous: string, results: Board[] }`

**获取板块详情**
- 接口: `GET /api/forum/boards/{boardId}/`
- 响应: `Board`

**获取板块主题**
- 接口: `GET /api/forum/boards/{boardId}/topics/`
- 参数: `{ page?: number }`
- 响应: `{ count: number, next: string, previous: string, results: Topic[] }`

**获取板块内活跃主题**
- 接口: `GET /api/forum/boards/{boardId}/active_topics/`
- 参数: `{ days?: number }`
- 响应: `{ count: number, next: string, previous: string, results: Topic[] }`

### 2.5 主题相关

**获取主题详情**
- 接口: `GET /api/forum/topics/{topicId}/`
- 响应: `Topic`

**创建主题**
- 接口: `POST /api/forum/boards/{boardId}/topics/`
- 参数: `{ title: string, content: string, tags?: string[] }`
- 响应: `Topic`

**获取主题帖子**
- 接口: `GET /api/forum/topics/{topicId}/posts/`
- 参数: `{ page: number }`
- 响应: `{ results: Post[], count: number }`

**回复主题**
- 接口: `POST /api/forum/posts/`
- 参数: `{ topic: number, content: string }`
- 响应: `Post`

**收藏主题**
- 接口: `POST /api/forum/topics/{topicId}/bookmark/`
- 响应: `void`

**取消收藏主题**
- 接口: `DELETE /api/forum/topics/{topicId}/bookmark/`
- 响应: `void`

### 2.6 通知相关

**获取通知列表**
- 接口: `GET /api/forum/notifications/`
- 响应: `Notification[]`

**标记通知为已读**
- 接口: `POST /api/forum/notifications/{notificationId}/read/`
- 响应: `void`

**标记所有通知为已读**
- 接口: `POST /api/forum/notifications/mark-all-read/`
- 响应: `void`

### 2.7 论坛统计相关

**获取论坛统计信息**
- 接口: `GET /api/forum/stats/`
- 响应: `{ total_users: number, total_topics: number, total_posts: number, total_comments: number }`

### 2.8 热门话题相关

**获取热门话题**
- 接口: `GET /api/forum/hot-topics/`
- 参数: `{ days?: number, limit?: number }`
- 响应: `Topic[]`

### 2.9 书签相关

**获取书签列表**
- 接口: `GET /api/forum/bookmarks/`
- 响应: `Bookmark[]`

**添加书签**
- 接口: `POST /api/forum/bookmarks/`
- 参数: `{ topic: number }`
- 响应: `Bookmark`

**删除书签**
- 接口: `DELETE /api/forum/bookmarks/{bookmarkId}/`
- 响应: `void`

## 3. 学校相关API

### 3.1 学校列表

- 接口: `GET /api/schools/`
- 参数: `{ province?: string, city?: string, type?: string, level?: string, page?: number, page_size?: number }`
- 响应: `{ count: number, next: string, previous: string, results: School[] }`

### 3.2 学校详情

- 接口: `GET /api/schools/{id}/`
- 响应: `School`

### 3.3 学校评分

**获取学校评分**
- 接口: `GET /api/schools/{schoolId}/ratings/`
- 参数: `{ page?: number, pageSize?: number }`
- 响应: `{ results: SchoolRating[], count: number }`

**评分学校**
- 接口: `POST /api/schools/{schoolId}/rate/`
- 参数: `{ score: number, comment: string }`
- 响应: `SchoolRating`

### 3.4 学校筛选数据

**获取省份列表**
- 接口: `GET /api/schools/provinces/`
- 响应: `string[]`

**获取城市列表**
- 接口: `GET /api/schools/cities/`
- 参数: `{ province: string }`
- 响应: `string[]`

**获取学校类型列表**
- 接口: `GET /api/schools/types/`
- 响应: `{ [key: string]: string }`

**获取学校层次列表**
- 接口: `GET /api/schools/levels/`
- 响应: `{ [key: string]: string }`

### 3.5 学校数据导入

**导入学校CSV数据**
- 接口: `POST /api/schools/import_csv/`
- 参数: `FormData` (包含file字段)
- 响应: `{ success: boolean, message: string, total: number, success_count: number, error_count: number }`

## 4. 聊天相关API

### 4.1 获取历史消息

- 接口: `GET /api/chat/messages/recent_messages/`
- 响应: `ChatMessage[]`

### 4.2 获取在线用户数

- 接口: `GET /api/chat/messages/online_users/`
- 响应: `{ count: number }`

## 5. WebSocket接口

### 5.1 连接WebSocket

- 地址: `ws://localhost:8000/ws/chat/?token={token}`
- 连接参数: 需要在URL中传递JWT token

### 5.2 WebSocket消息类型

**发送消息**
- 格式: `{ type: 'chat_message', message: string, content: string }`

**接收消息**
- 聊天消息: `{ type: 'chat_message', message: string, username: string, user_id: number, avatar: string, time: string }`
- 在线用户更新: `{ type: 'online_users', count: number }`
- 欢迎消息: `{ type: 'welcome', message: string, online_users: { count: number } }`
- 认证成功: `{ type: 'auth_success', message: string }`
- 认证警告: `{ type: 'auth_warning', message: string }`
- 错误消息: `{ type: 'error', message: string }`
- 心跳响应: `{ type: 'heartbeat_response', timestamp: number }`

## 6. 错误处理

所有API调用都应该处理以下错误情况：

1. **401 Unauthorized**: 未授权，token过期或无效
2. **400 Bad Request**: 请求参数错误
3. **403 Forbidden**: 权限不足
4. **404 Not Found**: 资源不存在
5. **500 Internal Server Error**: 服务器内部错误

## 7. 示例代码

### 7.1 使用axios调用API

```typescript
import request from '@/utils/request';

// 登录
const login = async (username: string, password: string) => {
  try {
    const response = await request.post('/api/users/users/login/', { username, password });
    return response;
  } catch (error) {
    console.error('登录失败:', error);
    throw error;
  }
};

// 获取用户信息
const getUserInfo = async () => {
  try {
    const response = await request.get('/api/users/users/me/');
    return response;
  } catch (error) {
    console.error('获取用户信息失败:', error);
    throw error;
  }
};
```

### 7.2 使用WebSocket

```typescript
const connectWebSocket = (token: string) => {
  const ws = new WebSocket(`ws://localhost:8000/ws/chat/?token=${token}`);
  
  ws.onopen = () => {
    console.log('WebSocket连接已打开');
  };
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'chat_message') {
      // 处理聊天消息
    } else if (data.type === 'online_users') {
      // 处理在线用户更新
    }
  };
  
  ws.onclose = () => {
    console.log('WebSocket连接已关闭');
  };
  
  ws.onerror = (error) => {
    console.error('WebSocket错误:', error);
  };
  
  return ws;
};
```
