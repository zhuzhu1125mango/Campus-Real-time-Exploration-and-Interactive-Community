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
  const user = computed(() => userProfileStore.user)
  const loading = computed(() => authStore.loading || tokenStore.loading || userProfileStore.loading)
  const error = computed(() => authStore.error || tokenStore.error || userProfileStore.error)
  const isLoggedIn = computed(() => userProfileStore.isLoggedIn)

  const fetchUserInfo = async () => {
    return userProfileStore.fetchUserInfo()
  }

  const login = async (username: string, password: string) => {
    return authStore.login(username, password)
  }

  const register = async (userData: any) => {
    return authStore.register(userData)
  }

  const logout = () => {
    return authStore.logout()
  }

  const refreshAuthToken = async () => {
    return tokenStore.refreshAuthToken()
  }

  const ensureValidToken = async () => {
    return tokenStore.ensureValidToken()
  }

  const favoriteSchool = async (schoolId: number) => {
    return userProfileStore.favoriteSchool(schoolId)
  }

  const unfavoriteSchool = async (schoolId: number) => {
    return userProfileStore.unfavoriteSchool(schoolId)
  }

  const initialize = () => {
    authStore.initializeAuth()
  }

  return {
    token,
    refreshToken,
    user,
    loading,
    error,
    isLoggedIn,
    fetchUserInfo,
    fetchUserProfile: fetchUserInfo,
    login,
    register,
    logout,
    refreshAuthToken,
    ensureValidToken,
    favoriteSchool,
    unfavoriteSchool,
    initialize
  }
})

