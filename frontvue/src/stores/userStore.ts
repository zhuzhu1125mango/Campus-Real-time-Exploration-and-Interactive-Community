import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { userApi } from '../api/user'
import axios from 'axios'

export interface User {
  id: number
  username: string
  email: string
  avatar?: string
  banner?: string
  phone?: string
  bio?: string
  favorite_schools?: number[]
  is_staff?: boolean
  is_superuser?: boolean
  created_at?: string
  updated_at?: string
}

export const useUserStore = defineStore('user', () => {
  // 存储访问令牌的键名
  const accessTokenKey = import.meta.env.VITE_JWT_ACCESS_TOKEN_KEY || 'access_token'
  const refreshTokenKey = import.meta.env.VITE_JWT_REFRESH_TOKEN_KEY || 'refresh_token'
  
  // 状态
  const token = ref<string>(localStorage.getItem(accessTokenKey) || '')
  const refreshToken = ref<string>(localStorage.getItem(refreshTokenKey) || '')
  const user = ref<User | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const failedToLoad = ref(false)
  
  // 重置状态函数
  const resetState = () => {
    token.value = ''
    refreshToken.value = ''
    user.value = null
    error.value = null
    failedToLoad.value = false
  }
  
  // 计算属性：用户是否已登录
  const isLoggedIn = computed(() => {
    const hasToken = !!token.value
    const hasUser = !!user.value && !!user.value.id
    const isInitialLoad = loading.value
    
    // 如果有token但没有用户信息且不在加载中，尝试获取用户信息
    if (hasToken && !hasUser && !isInitialLoad) {
      // 异步获取用户信息，不阻塞计算属性返回
      fetchUserInfo().catch(err => {
        console.error('获取用户信息失败:', err)
        failedToLoad.value = true
      })
    }
    
    // 如果token存在但加载失败，清除无效token
    if (hasToken && !hasUser && failedToLoad.value) {
      resetState()
      return false
    }
    
    return hasToken && hasUser
  })
  
  // 获取用户信息
  async function fetchUserInfo() {
    if (loading.value) return
    
    loading.value = true
    failedToLoad.value = false
    error.value = null
    
    try {
      const response = await axios.get('/api/users/users/me/', {
        headers: {
          'Authorization': `Bearer ${token.value}`
        }
      })
      
      if (response.status === 200) {
        // 更新用户信息
        const userData = response.data
        
        // 处理头像URL
        let avatarUrl = userData.avatar || ''
        
        // 如果头像URL不是绝对URL且不为空，添加基础URL
        if (avatarUrl && !avatarUrl.startsWith('http') && !avatarUrl.startsWith('data:')) {
          // 确保URL格式正确
          if (avatarUrl.startsWith('/')) {
            avatarUrl = `${import.meta.env.VITE_API_BASE_URL}${avatarUrl}`
          } else {
            avatarUrl = `${import.meta.env.VITE_API_BASE_URL}/${avatarUrl}`
          }
        }
        
        // 处理背景图URL
        let bannerUrl = userData.banner || ''
        
        // 如果背景图URL不是绝对URL且不为空，添加基础URL
        if (bannerUrl && !bannerUrl.startsWith('http') && !bannerUrl.startsWith('data:')) {
          // 确保URL格式正确
          if (bannerUrl.startsWith('/')) {
            bannerUrl = `${import.meta.env.VITE_API_BASE_URL}${bannerUrl}`
          } else {
            bannerUrl = `${import.meta.env.VITE_API_BASE_URL}/${bannerUrl}`
          }
        }
        
        // 更新用户对象
        user.value = {
          ...userData,
          avatar: avatarUrl || undefined,
          banner: bannerUrl || undefined
        }
        
        loading.value = false
        return user.value
      }
    } catch (err: any) {
      loading.value = false
      failedToLoad.value = true
      error.value = err.response?.data?.detail || '获取用户信息失败'
      return null
    }
  }
  
  // 登录
  const login = async (username: string, password: string) => {
    loading.value = true
    error.value = null
    
    try {
      const response = await userApi.login({ username, password })
      token.value = response.access
      refreshToken.value = response.refresh
      
      // 保存到本地存储
      localStorage.setItem(accessTokenKey, response.access)
      localStorage.setItem(refreshTokenKey, response.refresh)
      
      // 获取用户信息
      if (response.user) {
        // 处理avatar和banner字段可能为null的情况
        const userData = {
          ...response.user,
          avatar: response.user.avatar || undefined,
          banner: response.user.banner || undefined
        }
        user.value = userData
      } else {
        await fetchUserInfo()
      }
      
      return true
    } catch (err: any) {
      error.value = err.response?.data?.detail || '登录失败，请检查用户名和密码'
      return false
    } finally {
      loading.value = false
    }
  }
  
  // 注册
  const register = async (userData: any) => {
    loading.value = true
    error.value = null
    
    try {
      await userApi.register(userData)
      return true
    } catch (err: any) {
      error.value = err.response?.data || '注册失败，请稍后重试'
      return false
    } finally {
      loading.value = false
    }
  }
  
  // 登出
  const logout = () => {
    token.value = ''
    refreshToken.value = ''
    user.value = null
    
    // 清除本地存储
    localStorage.removeItem(accessTokenKey)
    localStorage.removeItem(refreshTokenKey)
    localStorage.removeItem('user_avatar')
    localStorage.removeItem('user_banner')
    
    resetState()
    
    return { success: true }
  }
  
  // 刷新token
  const refreshAuthToken = async () => {
    if (!refreshToken.value) {
      logout()
      return null
    }
    
    try {
      const response = await userApi.refreshToken(refreshToken.value)
      token.value = response.data.access
      refreshToken.value = response.data.refresh
      
      // 更新本地存储
      localStorage.setItem(accessTokenKey, response.data.access)
      localStorage.setItem(refreshTokenKey, response.data.refresh)
      
      return response.data.access
    } catch (error) {
      logout()
      return null
    }
  }
  
  // 收藏学校
  const favoriteSchool = async (schoolId: number) => {
    try {
      await userApi.favoriteSchool(schoolId)
      if (user.value && user.value.favorite_schools) {
        if (!user.value.favorite_schools.includes(schoolId)) {
          user.value.favorite_schools.push(schoolId)
        }
      }
      return true
    } catch (error) {
      return false
    }
  }
  
  // 取消收藏学校
  const unfavoriteSchool = async (schoolId: number) => {
    try {
      await userApi.unfavoriteSchool(schoolId)
      if (user.value && user.value.favorite_schools) {
        user.value.favorite_schools = user.value.favorite_schools.filter((id: number) => id !== schoolId)
      }
      return true
    } catch (error) {
      return false
    }
  }
  
  // 初始化获取用户信息
  if (token.value && !user.value) {
    // 尝试从localStorage中恢复头像和背景图
    const savedAvatar = localStorage.getItem('user_avatar')
    const savedBanner = localStorage.getItem('user_banner')
    
    // 过滤掉无效的blob URLs
    const validAvatar = (savedAvatar && !savedAvatar.startsWith('blob:')) ? savedAvatar : ''
    const validBanner = (savedBanner && !savedBanner.startsWith('blob:')) ? savedBanner : ''
    
    // 如果localStorage中有头像或背景图，先创建一个临时用户对象
    if (validAvatar || validBanner) {
      user.value = {
        id: 0,
        username: '',
        email: '',
        avatar: validAvatar,
        banner: validBanner
      }
    }
    
    fetchUserInfo()
  }
  
  // 导出所有状态和方法
  return {
    token,
    refreshToken,
    user,
    loading,
    error,
    isLoggedIn,
    fetchUserInfo,
    // 为了向后兼容，添加fetchUserProfile别名
    fetchUserProfile: fetchUserInfo,
    login,
    register,
    logout,
    refreshAuthToken,
    favoriteSchool,
    unfavoriteSchool
  }
}) 