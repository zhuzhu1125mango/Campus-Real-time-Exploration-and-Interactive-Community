import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { userApi } from '../api/user'
import { buildMediaUrl } from '../utils/urlUtils'
import config from '../utils/config'
import { useTokenStore } from './tokenStore'

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

export const useUserProfileStore = defineStore('userProfile', () => {
  const tokenStore = useTokenStore()
  const user = ref<User | null>(null)
  const loading = ref<boolean>(false)
  const error = ref<string | null>(null)
  const failedToLoad = ref(false)

  const isLoggedIn = computed(() => {
    return !!user.value && !!user.value.id
  })

  const fetchUserInfo = async () => {
    if (loading.value || !tokenStore.accessToken) return

    loading.value = true
    failedToLoad.value = false
    error.value = null

    try {
      const userData = await userApi.getProfile()

      const avatarUrl = buildMediaUrl(userData.avatar, config.media.defaultAvatar)
      const bannerUrl = buildMediaUrl(userData.banner, config.media.defaultBanner)

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

      localStorage.setItem('user_avatar', avatarUrl || '')
      localStorage.setItem('user_banner', bannerUrl || '')

      return user.value
    } catch (err: any) {
      failedToLoad.value = true
      error.value = err.response?.data?.detail || '获取用户信息失败'
      if (err.response?.status === 401) {
        tokenStore.clearTokens()
      }
      return null
    } finally {
      loading.value = false
    }
  }

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

  const clearUser = () => {
    user.value = null
    error.value = null
    failedToLoad.value = false
    localStorage.removeItem('user_avatar')
    localStorage.removeItem('user_banner')
  }

  const initializeUser = () => {
    if (tokenStore.accessToken && !user.value) {
      const savedAvatar = localStorage.getItem('user_avatar')
      const savedBanner = localStorage.getItem('user_banner')

      const validAvatar = (savedAvatar && !savedAvatar.startsWith('blob:')) ? savedAvatar : ''
      const validBanner = (savedBanner && !savedBanner.startsWith('blob:')) ? savedBanner : ''

      if (tokenStore.accessToken && (validAvatar || validBanner)) {
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
  }

  watch(
    () => tokenStore.accessToken,
    (newToken) => {
      if (newToken && !user.value) {
        fetchUserInfo()
      } else if (!newToken) {
        clearUser()
      }
    },
    { immediate: false }
  )

  return {
    user,
    loading,
    error,
    failedToLoad,
    isLoggedIn,
    fetchUserInfo,
    favoriteSchool,
    unfavoriteSchool,
    clearUser,
    initializeUser
  }
})