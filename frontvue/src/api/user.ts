import request from './request'
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
import type { Topic, Post } from '@/types/forum'

interface UserProfile {
  username: string
  email: string
  phone?: string
  bio?: string
  avatar?: string | null
}

interface LoginData {
  username: string
  password: string
}

interface RegisterData {
  username: string
  email: string
  password: string
  password2: string
}

export const userApi = {
  // 用户名密码登录
  login(data: LoginForm): Promise<TokenResponse> {
    return request.post<TokenResponse>('/api/users/users/login/', data)
  },

  // 邮箱验证码登录
  emailCodeLogin(data: EmailLoginForm): Promise<TokenResponse> {
    return request.post<TokenResponse>('/api/users/users/email_code_login/', data)
  },

  // 手机验证码登录
  phoneCodeLogin(data: PhoneLoginForm): Promise<TokenResponse> {
    return request.post<TokenResponse>('/api/users/users/phone_code_login/', data)
  },

  // 发送邮箱验证码
  sendEmailCode(data: SendCodeForm) {
    return request.post('/api/users/users/send_email_code/', {
      email: data.email,
      purpose: data.purpose
    })
  },

  // 发送手机验证码
  sendPhoneCode(data: SendCodeForm) {
    return request.post('/api/users/users/send_phone_code/', {
      phone: data.phone,
      purpose: data.purpose
    })
  },

  // 注册
  register(data: RegisterForm) {
    return request.post<User>('/api/users/users/', data)
  },

  // 重置密码
  resetPassword(data: ResetPasswordForm) {
    return request.post('/api/users/reset-password/', data)
  },

  // 刷新 token
  refreshToken(refresh: string) {
    return request.post<TokenResponse>('/api/users/token/refresh/', { refresh })
  },

  // 获取用户信息
  getProfile() {
    return request.get<User>('/api/users/users/me/')
  },

  // 更新用户信息
  updateProfile(data: FormData | Record<string, any>) {
    console.log('调用 updateProfile API:', data)
    
    // 如果是FormData类型（包含文件上传）
    if (data instanceof FormData) {
      console.log('检测到FormData，使用multipart/form-data格式上传')
      
      // 检查FormData中的文件
      if (data.has('avatar')) {
        const avatarFile = data.get('avatar')
        if (avatarFile instanceof File) {
          console.log('上传头像文件详情:', {
            name: avatarFile.name,
            type: avatarFile.type,
            size: avatarFile.size,
            lastModified: new Date(avatarFile.lastModified).toISOString()
          })
        } else {
          console.log('上传头像非文件类型:', avatarFile)
        }
      } else {
        console.log('FormData中没有avatar字段')
      }
      
      if (data.has('banner')) {
        const bannerFile = data.get('banner')
        if (bannerFile instanceof File) {
          console.log('上传背景图文件详情:', {
            name: bannerFile.name,
            type: bannerFile.type,
            size: bannerFile.size,
            lastModified: new Date(bannerFile.lastModified).toISOString()
          })
        } else {
          console.log('上传背景图非文件类型:', bannerFile)
        }
      } else {
        console.log('FormData中没有banner字段')
      }
      
      // 获取本地存储的token
      const token = localStorage.getItem(config.jwt.accessTokenKey)
      
      // 打印服务器地址和完整URL
      const fullUrl = `${config.apiBaseUrl}/api/users/users/update_me/`
      console.log('发送请求到URL:', fullUrl)
      
      // 添加超时设置
      return axios.patch(
        fullUrl,
        data,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
            ...(token ? { Authorization: `Bearer ${token}` } : {})
          },
          timeout: 30000, // 30秒超时
          onUploadProgress: (progressEvent) => {
            if (progressEvent.total) {
              const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
              console.log(`上传进度: ${percentCompleted}%`)
            }
          }
        }
      )
      .then(response => {
        console.log('上传成功，服务器响应:', response)
        console.log('服务器返回的数据:', response.data)
        
        // 检查响应中是否包含头像和背景图URL
        if (response.data.avatar) {
          console.log('返回的头像URL:', response.data.avatar)
        } else {
          console.log('返回数据中没有头像URL')
        }
        
        if (response.data.banner) {
          console.log('返回的背景图URL:', response.data.banner)
        } else {
          console.log('返回数据中没有背景图URL')
        }
        
        return response.data
      })
      .catch(error => {
        console.error('上传失败:', error)
        if (error.response) {
          console.error('服务器响应状态:', error.response.status)
          console.error('服务器响应数据:', error.response.data)
        } else if (error.request) {
          console.error('没有收到响应，请求信息:', error.request)
        } else {
          console.error('请求配置错误:', error.message)
        }
        throw error
      })
    }
    
    // 如果是普通对象（不包含文件上传）
    console.log('使用JSON格式更新用户资料')
    return request.patch<User>('/api/users/users/update_me/', data)
  },

  // 更改密码
  changePassword(data: { old_password: string; new_password: string }) {
    return request.post('/api/users/change-password/', data)
  },

  // 找回密码
  forgotPassword(email: string) {
    return request.post('/api/users/forgot-password/', { email })
  },

  // 获取收藏的学校
  getFavoriteSchools() {
    return request.get<{ schools: number[] }>('/api/users/favorites/by_category/', { 
      params: { category: 'school' } 
    })
  },

  // 收藏学校
  favoriteSchool(schoolId: number) {
    return request.post<{ success: boolean }>('/api/users/favorites/add_favorite/', { 
      content_type: 'schools.school',
      object_id: schoolId 
    })
  },

  // 取消收藏学校
  unfavoriteSchool(schoolId: number) {
    return request.delete<{ success: boolean }>('/api/users/favorites/remove_favorite/', {
      data: {
        content_type: 'schools.school',
        object_id: schoolId
      }
    })
  },

  // 移除收藏学校 (别名，与unfavoriteSchool功能相同)
  removeFavoriteSchool(schoolId: number) {
    return request.delete<{ success: boolean }>('/api/users/favorites/remove_favorite/', {
      data: {
        content_type: 'schools.school',
        object_id: schoolId
      }
    })
  },

  // 获取通知列表
  getNotifications() {
    return request.get('/api/users/notifications/')
  },

  // 获取未读通知数
  getUnreadNotificationsCount() {
    return request.get('/api/users/notifications/count/')
  },
  
  // 标记所有通知为已读
  markAllNotificationsAsRead() {
    return request.post('/api/users/notifications/mark_all_read/')
  },
  
  // 标记单个通知为已读
  markNotificationAsRead(notificationId: number) {
    return request.post(`/api/users/notifications/${notificationId}/mark_read/`)
  },

  // 检查登录状态
  checkLogin() {
    return request.get<{ is_logged_in: boolean, user?: UserProfile }>('/api/users/check-login/')
  },

  // 退出登录
  logout() {
    return request.post('/api/users/users/logout/')
  },

  // 获取当前用户信息
  getCurrentUser(): Promise<User> {
    return request.get('/api/users/me/')
  },

  // 获取用户资料
  getUserProfile(userId: number | string): Promise<User> {
    return request.get(`/api/users/${userId}/`)
  },

  // 更新用户资料
  updateUserProfile(data: Partial<User>): Promise<User> {
    return request.patch('/api/users/me/', data)
  },
  
  // 获取用户创建的主题
  getUserTopics(userId: number | string, page = 1): Promise<{ count: number; next: string | null; previous: string | null; results: Topic[] }> {
    return request.get(`/api/users/${userId}/topics/`, { params: { page } })
  },
  
  // 获取用户的帖子和回复
  getUserPosts(userId: number | string, page = 1, includeFirst = false): Promise<{ count: number; next: string | null; previous: string | null; results: Post[] }> {
    return request.get(`/api/users/${userId}/posts/`, { 
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
    return request.get(`/api/users/${userId}/profile_stats/`)
  }
} 