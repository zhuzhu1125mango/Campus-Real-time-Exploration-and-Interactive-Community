import { defineStore } from 'pinia'
import { computed } from 'vue'
import { useAuthStore } from './authStore'
import { useTokenStore } from './tokenStore'
import { useUserProfileStore } from './userProfileStore'
export type { User } from './userProfileStore'

export const useUserStore = defineStore('user', () => {
  const authStore = useAuthStore()
  const tokenStore = useTokenStore()
  const userProfileStore = useUserProfileStore()

  const token = computed(() => tokenStore.accessToken)
  const refreshToken = computed(() => tokenStore.refreshToken)
  const activeUserId = computed(() => tokenStore.activeUserId)
  const accounts = computed(() => tokenStore.accounts)
  const user = computed(() => userProfileStore.user)
  const loading = computed(() => authStore.loading || tokenStore.loading || userProfileStore.loading)
  const error = computed(() => authStore.error || tokenStore.error || userProfileStore.error)
  const isLoggedIn = computed(() => userProfileStore.isLoggedIn)

  const fetchUserInfo = async (options?: { force?: boolean }) => {
    return userProfileStore.fetchUserInfo(options)
  }

  const login = async (username: string, password: string, options?: { switch?: boolean }) => {
    return authStore.login(username, password, options)
  }

  const register = async (userData: any) => {
    return authStore.register(userData)
  }

  const logout = async (all = false) => {
    return authStore.logout(all)
  }

  /**
   * 切换到指定账号。
   * @returns 是否切换成功
   */
  const switchAccount = (userId: number) => {
    const ok = tokenStore.switchAccount(userId)
    if (ok) {
      userProfileStore.fetchUserInfo()
    }
    return ok
  }

  /**
   * 移除指定账号（登出该账号）。
   */
  const removeAccount = (userId: number) => {
    tokenStore.removeAccount(userId)
  }

  const refreshAuthToken = async () => {
    return tokenStore.refreshAuthToken()
  }

  const ensureValidToken = async () => {
    return tokenStore.ensureValidToken()
  }

  const initialize = () => {
    authStore.initializeAuth()
  }

  const favoriteSchool = async (schoolId: number) => {
    return userProfileStore.favoriteSchool(schoolId)
  }

  const unfavoriteSchool = async (schoolId: number) => {
    return userProfileStore.unfavoriteSchool(schoolId)
  }

  return {
    token,
    refreshToken,
    activeUserId,
    accounts,
    user,
    loading,
    error,
    isLoggedIn,
    fetchUserInfo,
    fetchUserProfile: fetchUserInfo,
    login,
    register,
    logout,
    switchAccount,
    removeAccount,
    refreshAuthToken,
    ensureValidToken,
    initialize,
    favoriteSchool,
    unfavoriteSchool
  }
})
