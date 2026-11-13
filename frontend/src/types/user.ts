export interface User {
  id: number
  username: string
  email: string
  first_name?: string
  last_name?: string
  phone?: string
  avatar?: string | null
  banner?: string | null
  bio?: string
  location?: string
  website?: string
  created_at: string
  updated_at?: string
  last_login?: string
  is_active?: boolean
  is_staff?: boolean
  is_superuser?: boolean
  favorite_schools?: number[]
  follower_count?: number
  following_count?: number
  is_following?: boolean
}

// 用户名密码登录表单
export interface LoginForm {
  username: string
  password: string
}

// 手机验证码登录表单
export interface PhoneLoginForm {
  phone: string
  code: string
}

// 邮箱验证码登录表单
export interface EmailLoginForm {
  email: string
  code: string
}

// 重置密码表单
export interface ResetPasswordForm {
  email?: string
  phone?: string
  code: string
  password: string
  password_confirm: string
}

// 发送验证码表单
export interface SendCodeForm {
  email?: string
  phone?: string
  purpose: 'register' | 'login' | 'reset_password'
}

// 修改后的注册表单
export interface RegisterForm {
  username: string
  email?: string
  phone?: string
  code?: string
  password: string
  password_confirm: string
}

export interface TokenResponse {
  access: string
  refresh: string
  user?: User
}

export interface UserProfile extends User {
  posts_count: number
  comments_count: number
  followers_count: number
  following_count: number
  is_following: boolean
}

export interface LoginCredentials {
  username: string
  password: string
}

export interface RegisterData extends LoginCredentials {
  email: string
  first_name?: string
  last_name?: string
}

export interface PasswordResetData {
  email: string
}

export interface PasswordChangeData {
  old_password: string
  new_password: string
  confirm_password: string
}

export interface Message {
  id: number
  sender: User
  receiver: User
  content: string
  created_at: string
  is_read: boolean
}

/** 收藏项 */
export interface Favorite {
  id: number
  content_type: string
  object_id: number
  category: string
  note?: string
  content_type_name?: string
  content_object_name?: string
  content_object: unknown
}

/** 通知 */
export interface Notification {
  id: number
  recipient: number
  sender?: User
  sender_username?: string
  notification_type: string
  title: string
  content: string
  content_type?: number | null
  content_type_name?: string
  object_id?: number
  url?: string
  is_read: boolean
  created_at: string
  updated_at: string
}

/** 通知类型统计 */
export interface NotificationTypeCounts {
  [key: string]: number
}

/** 好友请求 */
export interface FriendRequest {
  id: number
  sender: User
  receiver: User
  status: 'pending' | 'accepted' | 'rejected'
  created_at: string
  updated_at: string
}

/** 动态 */
export interface Activity {
  id: number
  user: User
  activity_type: string
  content?: string
  target_content_type?: string
  target_object_id?: number
  target_title?: string
  target_url?: string
  is_public?: boolean
  is_liked?: boolean
  likes_count?: number
  comments_count?: number
  comments?: ActivityComment[]
  created_at: string
  updated_at: string
}

/** 动态评论 */
export interface ActivityComment {
  id: number
  activity: number
  user: User
  content: string
  parent?: number | null
  replies?: ActivityComment[]
  created_at: string
  updated_at: string
}

/** 用户积分信息 */
export interface UserPoints {
  points: number
  level: number
  level_name: string
  level_progress: number
  next_level_points: number
}

/** 积分记录 */
export interface PointsRecord {
  id: number
  action: string
  points: number
  description: string
  created_at: string
}

/** 用户积分记录分页响应 */
export interface PointsRecordsResponse {
  count: number
  next: string | null
  previous: string | null
  results: PointsRecord[]
}

/** 积分排行榜项 */
export interface PointsLeaderboardItem {
  rank: number
  user_id: number
  username: string
  avatar: string | null
  points: number
  level: number
  level_name: string
}

/** 每日签到结果 */
export interface DailyCheckinResult {
  message: string
  points: number
  total_points: number
}

/** 用户资料统计 */
export interface UserProfileStats {
  topic_count: number
  post_count: number
  reply_count: number
  active_boards: Array<{ id: number; name: string; post_count: number }>
  join_date: string
}

/** 分页响应通用结构 */
export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}