import request from '../utils/request'
import axios from 'axios'
import config from '../utils/config'
import type { 
  LoginForm, 
  RegisterForm, 
  TokenResponse, 
  User, 
  EmailLoginForm, 
  PhoneLoginForm,
  SendCodeForm,
  ResetPasswordForm
} from '../types/user'
import type { Topic, Post } from '../types/forum'



export const userApi = {
  // 用户名密码登录
  login(data: LoginForm): Promise<any> {
    return request.post('/users/users/login/', data)
  },

  // 邮箱验证码登录
  emailCodeLogin(data: EmailLoginForm): Promise<any> {
    return request.post('/users/users/email_code_login/', data)
  },

  // 手机验证码登录
  phoneCodeLogin(data: PhoneLoginForm): Promise<any> {
    return request.post('/users/users/phone_code_login/', data)
  },

  // 发送邮箱验证码
  sendEmailCode(data: SendCodeForm) {
    return request.post('/users/users/send_email_code/', {
      email: data.email,
      purpose: data.purpose
    })
  },

  // 发送手机验证码
  sendPhoneCode(data: SendCodeForm) {
    return request.post('/users/users/send_phone_code/', {
      phone: data.phone,
      purpose: data.purpose
    })
  },

  // 注册
  register(data: RegisterForm) {
    return request.post<User>('/users/users/', data)
  },

  // 重置密码
  resetPassword(data: ResetPasswordForm) {
    return request.post('/users/reset-password/', data)
  },

  // 刷新 token
  refreshToken(refresh: string) {
    return request.post<TokenResponse>('/token/refresh/', { refresh })
  },

  // 获取用户信息
  getProfile() {
    return request.get<User>('/users/users/me/')
  },

  // 更新用户信息
  updateProfile(data: FormData | Record<string, any>) {
    // 如果是FormData类型（包含文件上传）
    if (data instanceof FormData) {
      // 获取本地存储的token
      const token = localStorage.getItem(config.jwt.accessTokenKey)
      
      const fullUrl = `http://localhost:8000/api/users/users/update_me/`
      
      // 添加超时设置
      return axios.patch(
        fullUrl,
        data,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
            ...(token ? { Authorization: `Bearer ${token}` } : {})
          },
          timeout: 30000 // 30秒超时
        }
      )
      .then(response => {
        return response.data
      })
      .catch(error => {
        throw error
      })
    }
    
    // 如果是普通对象（不包含文件上传）
    return request.patch<User>('/users/users/update_me/', data)
  },

  // 更改密码
  changePassword(data: { old_password: string; new_password: string }) {
    return request.post('/users/users/change_password/', data)
  },

  // 找回密码
  forgotPassword(email: string) {
    return request.post('/users/users/forgot_password/', { email })
  },

  // 获取收藏的学校
  getFavoriteSchools() {
    return request.get<{ schools: number[] }>('/users/favorites/by_category/', { 
      params: { category: 'school' } 
    })
  },

  // 收藏学校
  favoriteSchool(schoolId: number) {
    return request.post<{ success: boolean }>('/users/favorites/add_favorite/', { 
      content_type: 'schools.school',
      object_id: schoolId 
    })
  },

  // 取消收藏学校
  unfavoriteSchool(schoolId: number) {
    return request.delete<{ success: boolean }>('/users/favorites/remove_favorite/', {
      data: {
        content_type: 'schools.school',
        object_id: schoolId
      }
    })
  },

  // 移除收藏学校 (别名，与unfavoriteSchool功能相同)
  removeFavoriteSchool(schoolId: number) {
    return request.delete<{ success: boolean }>('/users/favorites/remove_favorite/', {
      data: {
        content_type: 'schools.school',
        object_id: schoolId
      }
    })
  },

  // 获取通知列表
  getNotifications() {
    return request.get('/users/notifications/')
  },

  // 获取未读通知数
  getUnreadNotificationsCount() {
    return request.get('/users/notifications/count/')
  },
  
  // 标记所有通知为已读
  markAllNotificationsAsRead() {
    return request.post('/users/notifications/mark_all_read/')
  },
  
  // 标记单个通知为已读
  markNotificationAsRead(notificationId: number) {
    return request.post(`/users/notifications/${notificationId}/mark_read/`)
  },

  // 退出登录
  logout() {
    return request.post('/users/users/logout/')
  },

  // 获取当前用户信息
  getCurrentUser(): Promise<any> {
    return request.get('/users/users/me/')
  },

  // 获取用户资料
  getUserProfile(userId: number | string): Promise<any> {
    return request.get(`/users/users/${userId}/`)
  },

  // 更新用户资料
  updateUserProfile(data: Partial<any>): Promise<any> {
    return request.patch('/users/users/me/', data)
  },
  
  // 获取用户创建的主题
  getUserTopics(userId: number | string, page = 1): Promise<{ count: number; next: string | null; previous: string | null; results: Topic[] }> {
    return request.get(`/users/users/${userId}/topics/`, { params: { page } })
  },
  
  // 获取用户的帖子和回复
  getUserPosts(userId: number | string, page = 1, includeFirst = false): Promise<{ count: number; next: string | null; previous: string | null; results: Post[] }> {
    return request.get(`/users/users/${userId}/posts/`, { 
      params: { 
        page,
        include_first: includeFirst 
      } 
    })
  },
  
  // 获取用户个人资料统计信息
  getUserProfileStats(userId: number | string): Promise<{
    topic_count: number;
    post_count: number;
    reply_count: number;
    active_boards: Array<{ id: number; name: string; post_count: number }>;
    join_date: string;
  }> {
    return request.get(`/users/users/${userId}/profile_stats/`)
  },
  
  // 好友系统相关API
  
  // 获取好友列表
  getFriends(): Promise<{ friends: any[]; count: number }> {
    return request.get('/users/friends/friend_list/')
  },
  
  // 发送好友请求
  sendFriendRequest(receiverId: number): Promise<any> {
    return request.post('/users/friend-requests/', { receiver: receiverId })
  },
  
  // 获取收到的好友请求
  getReceivedFriendRequests(): Promise<any[]> {
    return request.get('/users/friend-requests/received/')
  },
  
  // 获取发送的好友请求
  getSentFriendRequests(): Promise<any[]> {
    return request.get('/users/friend-requests/sent/')
  },
  
  // 接受好友请求
  acceptFriendRequest(requestId: number): Promise<any> {
    return request.post(`/users/friend-requests/${requestId}/accept/`)
  },
  
  // 拒绝好友请求
  rejectFriendRequest(requestId: number): Promise<any> {
    return request.post(`/users/friend-requests/${requestId}/reject/`)
  },
  
  // 移除好友
  removeFriend(friendId: number): Promise<any> {
    return request.post('/users/friends/remove/', { friend_id: friendId })
  },
  
  // 检查是否是好友
  checkFriendship(userId: number): Promise<{ is_friend: boolean }> {
    return request.get(`/users/friends/check/?user_id=${userId}`)
  },
  
  // 搜索用户
  searchUsers(query: string): Promise<any[]> {
    return request.get(`/users/users/search/?q=${encodeURIComponent(query)}`)
  },
  
  // 私信系统相关API
  
  // 获取所有对话
  getConversations(): Promise<any[]> {
    return request.get('/users/messages/conversations/')
  },
  
  // 获取与特定用户的对话
  getConversation(userId: number): Promise<any> {
    return request.get(`/users/messages/conversation/?user_id=${userId}`)
  },
  
  // 发送私信
  sendMessage(data: { receiver: number; content: string }): Promise<any> {
    return request.post('/users/messages/', data)
  },
  
  // 获取未读消息数量
  getUnreadMessagesCount(): Promise<{ unread_count: number }> {
    return request.get('/users/messages/unread_count/')
  },
  
  // 标记消息为已读
  markMessageAsRead(messageId: number): Promise<any> {
    return request.post(`/users/messages/${messageId}/mark_read/`)
  },
  
  // 标记所有消息为已读
  markAllMessagesAsRead(userId: number): Promise<any> {
    return request.post('/users/messages/mark_all_read/', { user_id: userId })
  },
  
  // 个人动态相关API
  
  // 获取动态列表
  getActivities(params?: { page?: number; page_size?: number; type?: string }): Promise<{ count: number; next: string | null; previous: string | null; results: any[] }> {
    return request.get('/users/activities/', { params })
  },
  
  // 获取动态详情
  getActivityDetail(activityId: number | string): Promise<any> {
    return request.get(`/users/activities/${activityId}/`)
  },
  
  // 创建动态
  createActivity(data: { activity_type: string; content?: string; target_content_type?: string; target_object_id?: number; target_title?: string; target_url?: string; is_public?: boolean }): Promise<any> {
    return request.post('/users/activities/', data)
  },
  
  // 获取动态评论
  getActivityComments(activityId: number | string): Promise<any[]> {
    return request.get(`/users/activities/${activityId}/comments/`)
  },
  
  // 点赞动态
  likeActivity(activityId: number | string): Promise<{ status: string }> {
    return request.post(`/users/activities/${activityId}/like/`)
  },
  
  // 取消点赞动态
  unlikeActivity(activityId: number | string): Promise<{ status: string }> {
    return request.post(`/users/activities/${activityId}/unlike/`)
  },
  
  // 获取关注动态
  getActivityFeed(params?: { page?: number }): Promise<{ count: number; next: string | null; previous: string | null; results: any[] }> {
    return request.get('/users/activities/feed/', { params })
  },
  
  // 获取我的动态
  getMyActivities(params?: { page?: number }): Promise<{ count: number; next: string | null; previous: string | null; results: any[] }> {
    return request.get('/users/activities/my_activities/', { params })
  },
  
  // 创建评论
  createActivityComment(data: { activity: number; content: string; parent?: number }): Promise<any> {
    return request.post('/users/activity-comments/', data)
  }
} 