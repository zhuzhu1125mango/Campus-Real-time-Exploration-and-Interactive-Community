import { defineStore } from 'pinia'
import { ref } from 'vue'
import config from '../utils/config'
import { userApi } from '../api/user'
import { createDefaultExpiryService, calculateExpiryTime } from '../services/tokenExpiryService'

export const useTokenStore = defineStore('token', () => {
  const accessToken = ref<string>(localStorage.getItem(config.jwt.accessTokenKey) || '')
  const refreshToken = ref<string>(localStorage.getItem(config.jwt.refreshTokenKey) || '')
  const loading = ref<boolean>(false)
  const error = ref<string | null>(null)

  const expiryService = createDefaultExpiryService(() => {
    clearTokens()
  })

  const setTokens = (access: string, refresh: string) => {
    accessToken.value = access
    refreshToken.value = refresh
    localStorage.setItem(config.jwt.accessTokenKey, access)
    localStorage.setItem(config.jwt.refreshTokenKey, refresh)

    const expiryTime = calculateExpiryTime()
    expiryService.setTokenExpiry(expiryTime)
    expiryService.startExpiryCheck()
  }

  const clearTokens = () => {
    accessToken.value = ''
    refreshToken.value = ''
    localStorage.removeItem(config.jwt.accessTokenKey)
    localStorage.removeItem(config.jwt.refreshTokenKey)
    expiryService.clearExpiry()
  }

  const refreshAuthToken = async () => {
    if (!refreshToken.value) {
      return null
    }

    loading.value = true
    error.value = null

    try {
      const response = await userApi.refreshToken(refreshToken.value)
      setTokens(response.access, response.refresh)
      return response.access
    } catch (err: any) {
      error.value = err.response?.data?.detail || '刷新token失败'
      clearTokens()
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * 在调用需要有效 token 的场景（如 WebSocket）前使用。
   * 仅当本地判断 token 可能过期时才尝试刷新，避免每次请求都刷新。
   */
  const ensureValidToken = async () => {
    if (!accessToken.value) {
      return null
    }
    const remaining = expiryService.getRemainingTime()
    // token 不存在过期时间或已经/即将过期时尝试刷新
    if (remaining === null || remaining <= 60 * 1000) {
      return refreshAuthToken()
    }
    return accessToken.value
  }

  const hasToken = () => {
    return !!accessToken.value
  }

  const initializeTokenCheck = () => {
    if (accessToken.value) {
      const isExpired = expiryService.checkExpiry()
      if (!isExpired) {
        expiryService.startExpiryCheck()
      }
    }
  }

  return {
    accessToken,
    refreshToken,
    loading,
    error,
    setTokens,
    clearTokens,
    refreshAuthToken,
    ensureValidToken,
    hasToken,
    initializeTokenCheck
  }
})