import { defineStore } from 'pinia'
import { ref } from 'vue'
import { userApi } from '../api/user'
import { useTokenStore } from './tokenStore'
import { useUserProfileStore } from './userProfileStore'

export const useAuthStore = defineStore('auth', () => {
  const tokenStore = useTokenStore()
  const userProfileStore = useUserProfileStore()

  const loading = ref<boolean>(false)
  const error = ref<string | null>(null)

  const login = async (username: string, password: string) => {
    loading.value = true
    error.value = null

    try {
      const response = await userApi.login({ username, password })
      tokenStore.setTokens(response.access, response.refresh)
      await userProfileStore.fetchUserInfo()
      return true
    } catch (err: any) {
      error.value = err.response?.data?.detail || '登录失败，请检查用户名和密码'
      return false
    } finally {
      loading.value = false
    }
  }

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

  const logout = () => {
    tokenStore.clearTokens()
    userProfileStore.clearUser()
    return { success: true }
  }

  const initializeAuth = () => {
    tokenStore.initializeTokenCheck()
    userProfileStore.initializeUser()
  }

  const refreshToken = async () => {
    return tokenStore.refreshAuthToken()
  }

  return {
    loading,
    error,
    login,
    register,
    logout,
    refreshToken,
    initializeAuth
  }
})