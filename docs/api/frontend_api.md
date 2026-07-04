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

### 1.6 发送验证码

**发送邮箱验证码**
- 接口: `POST /api/users/email-code/`
- 参数: `{ email: string, purpose: string }`
- 响应: `{ message: string }`

**发送手机验证码**
- 接口: `POST /api/users/phone-code/`
- 参数: `{ phone: string, purpose: string }`
- 响应: `{ message: string }`

### 1.7 更新用户信息

- 接口: `PATCH /api/users/users/me/`
- 参数: `{ username?: string, email?: string, phone?: string, avatar?: File, banner?: File }`
- 响应: `User`

## 2. 论坛相关API

### 2.1 帖子相关

**获取帖子详情**
- 接口: `GET /api/forum/posts/{postId}/`
- 响应: `Post`

**获取帖子列表**
- 接口: `GET /api/forum/posts/`
- 参数: `{ page?: number, page_size?: number, category?: number, order_by?: string }`
- 响应: `{ count: number, next: string, previous: string, results: Post[] }`

**获取帖子评论**
- 接口: `GET /api/forum/posts/{postId}/comments/`
- 参数: `{ page?: number, page_size?: number }`
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

**创建帖子**
- 接口: `POST /api/forum/posts/`
- 参数: `{ title: string, content: string, category?: number, tags?: string[] }`
- 响应: `Post`

### 2.2 评论相关

**点赞评论**
- 接口: `POST /api/forum/comments/{commentId}/like/`
- 响应: `void`

**取消点赞评论**
- 接口: `DELETE /api/forum/comments/{commentId}/like/`
- 响应: `void`

### 2.3 分类相关

**获取分类列表**
- 接口: `GET /api/forum/categories/`
- 响应: `Category[]`

### 2.4 板块相关

**获取板块列表**
- 接口: `GET /api/forum/boards/`
- 参数: `{ page?: number, page_size?: number }`
- 响应: `{ count: number, next: string, previous: string, results: Board[] }`

**获取板块详情**
- 接口: `GET /api/forum/boards/{boardId}/`
- 响应: `Board`

## 3. 学校相关API

### 3.1 学校列表

- 接口: `GET /api/schools/`
- 参数: `{ province?: string, city?: string, type?: string, level?: string, page?: number, page_size?: number, keyword?: string }`
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

### 3.4 学校对比

- 接口: `POST /api/schools/compare/`
- 参数: `{ school_ids: number[] }`
- 响应: `SchoolComparisonResult`

### 3.5 推荐系统

- 接口: `GET /api/schools/recommendations/`
- 参数: `{ type?: string, limit?: number }`
- 响应: `{ results: Recommendation[] }`

### 3.6 统计数据

**获取仪表盘数据**
- 接口: `GET /api/schools/stats/dashboard/`
- 响应: `DashboardStats`

## 4. 活动相关API

### 4.1 活动列表

- 接口: `GET /api/schools/events/`
- 参数: `{ page?: number, page_size?: number, status?: string, start_date?: string, end_date?: string }`
- 响应: `{ count: number, next: string, previous: string, results: Event[] }`

### 4.2 活动详情

- 接口: `GET /api/schools/events/{id}/`
- 响应: `Event`

### 4.3 活动报名

- 接口: `POST /api/schools/events/{id}/register/`
- 响应: `{ success: boolean, message: string }`

### 4.4 取消报名

- 接口: `POST /api/schools/events/{id}/cancel_registration/`
- 响应: `{ success: boolean, message: string }`

## 5. 好友相关API

### 5.1 获取好友列表

- 接口: `GET /api/users/friends/`
- 参数: `{ page?: number, page_size?: number }`
- 响应: `{ count: number, next: string, previous: string, results: Friend[] }`

### 5.2 添加好友

- 接口: `POST /api/users/friends/`
- 参数: `{ user_id: number }`
- 响应: `Friend`

### 5.3 接受好友请求

- 接口: `POST /api/users/friends/{id}/accept/`
- 响应: `{ success: boolean, message: string }`

### 5.4 删除好友

- 接口: `DELETE /api/users/friends/{id}/`
- 响应: `{ success: boolean, message: string }`

## 6. 收藏相关API

### 6.1 获取收藏列表

- 接口: `GET /api/users/favorites/`
- 参数: `{ page?: number, page_size?: number }`
- 响应: `{ count: number, next: string, previous: string, results: Favorite[] }`

### 6.2 添加收藏

- 接口: `POST /api/users/favorites/`
- 参数: `{ school_id: number }`
- 响应: `Favorite`

### 6.3 删除收藏

- 接口: `DELETE /api/users/favorites/{id}/`
- 响应: `{ success: boolean, message: string }`

## 7. 聊天相关API

### 7.1 获取历史消息

- 接口: `GET /api/chat/messages/recent_messages/`
- 参数: `{ limit?: number }`
- 响应: `ChatMessage[]`

### 7.2 获取在线用户数

- 接口: `GET /api/chat/messages/online_users/`
- 响应: `{ count: number }`

## 8. WebSocket接口

### 8.1 连接WebSocket

- 地址: `ws://localhost:8000/ws/chat/?token={token}`
- 连接参数: 需要在URL中传递JWT token

### 8.2 WebSocket消息类型

**发送消息**
- 格式: `{ type: 'chat_message', message: string, content: string }`

**接收消息**
- 聊天消息: `{ type: 'chat_message', message: string, username: string, user_id: number, avatar: string, time: string }`
- 在线用户更新: `{ type: 'online_users', count: number }`
- 欢迎消息: `{ type: 'welcome', message: string, online_users: { count: number } }`

## 9. 错误处理

所有API调用都应该处理以下错误情况：

1. **401 Unauthorized**: 未授权，token过期或无效
2. **400 Bad Request**: 请求参数错误
3. **403 Forbidden**: 权限不足
4. **404 Not Found**: 资源不存在
5. **500 Internal Server Error**: 服务器内部错误

## 10. 示例代码

### 10.1 使用axios调用API

```typescript
import request from '@/utils/request';

const login = async (username: string, password: string) => {
  try {
    const response = await request.post('/api/users/users/login/', { username, password });
    return response;
  } catch (error) {
    console.error('登录失败:', error);
    throw error;
  }
};

const getUserInfo = async () => {
  try {
    const response = await request.get('/api/users/users/me/');
    return response;
  } catch (error) {
    console.error('获取用户信息失败:', error);
    throw error;
  }
};

const getSchools = async (params?: { keyword?: string; province?: string }) => {
  try {
    const response = await request.get('/api/schools/', { params });
    return response;
  } catch (error) {
    console.error('获取学校列表失败:', error);
    throw error;
  }
};
```

### 10.2 使用WebSocket

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