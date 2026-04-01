import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { userApi } from '../api/user'

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
    
    // 如果没有token，直接返回false
    if (!hasToken) {
      // 确保用户状态被重置
      if (user.value) {
        resetState()
      }
      return false
    }
    
    // 如果token存在但加载失败，清除无效token
    if (hasToken && !hasUser && failedToLoad.value) {
      resetState()
      return false
    }
    
    // 如果有token但没有用户信息且不在加载中，尝试获取用户信息
    if (hasToken && !hasUser && !isInitialLoad) {
      // 异步获取用户信息，不阻塞计算属性返回
      fetchUserInfo().catch(err => {
        console.error('获取用户信息失败:', err)
        failedToLoad.value = true
      })
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
      // 使用userApi.getProfile()来获取用户信息，这样会使用我们的request工具，自动添加认证头
      const userData = await userApi.getProfile()
      console.log('获取到的用户信息:', userData)
      
      // 处理头像URL
      let avatarUrl = userData.avatar || ''
      
      // 如果头像URL不是绝对URL且不为空，添加基础URL
      if (avatarUrl && !avatarUrl.startsWith('http') && !avatarUrl.startsWith('data:')) {
        // 媒体文件直接使用后端根路径，不需要/api前缀
        if (avatarUrl.startsWith('/')) {
          avatarUrl = `http://localhost:8000${avatarUrl}`
        } else {
          avatarUrl = `http://localhost:8000/${avatarUrl}`
        }
      }
      
      // 处理背景图URL
      let bannerUrl = userData.banner || ''
      
      // 如果背景图URL不是绝对URL且不为空，添加基础URL
      if (bannerUrl && !bannerUrl.startsWith('http') && !bannerUrl.startsWith('data:')) {
        // 媒体文件直接使用后端根路径，不需要/api前缀
        if (bannerUrl.startsWith('/')) {
          bannerUrl = `http://localhost:8000${bannerUrl}`
        } else {
          bannerUrl = `http://localhost:8000/${bannerUrl}`
        }
      }
      
      // 更新用户对象，确保所有字段都被正确设置
      user.value = {
        id: userData.id,
        username: userData.username,
        email: userData.email,
        avatar: avatarUrl || undefined,
        banner: bannerUrl || undefined,
        phone: userData.phone || undefined,
        bio: userData.bio || undefined,
        favorite_schools: userData.favorite_schools || [],
        is_staff: userData.is_staff || false,
        is_superuser: userData.is_superuser || false,
        created_at: userData.created_at || undefined,
        updated_at: userData.updated_at || undefined
      }
      
      // 更新localStorage中的头像和背景图
      localStorage.setItem('user_avatar', avatarUrl || '')
      localStorage.setItem('user_banner', bannerUrl || '')
      
      loading.value = false
      console.log('更新后的用户信息:', user.value)
      return user.value
    } catch (err: any) {
      loading.value = false
      failedToLoad.value = true
      error.value = err.response?.data?.detail || '获取用户信息失败'
      console.error('获取用户信息失败:', err)
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
      
      // 无论是否返回user数据，都强制获取最新用户信息
      await fetchUserInfo()
      
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
      token.value = response.access
      refreshToken.value = response.refresh
      
      // 存储到本地存储
      localStorage.setItem(accessTokenKey, response.access)
      localStorage.setItem(refreshTokenKey, response.refresh)
      
      return response.access
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
    
    // 只有在有token的情况下才创建临时用户对象
    if (token.value && (validAvatar || validBanner)) {
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