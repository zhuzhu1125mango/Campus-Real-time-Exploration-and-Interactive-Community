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
  favorite_schools?: number[]
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