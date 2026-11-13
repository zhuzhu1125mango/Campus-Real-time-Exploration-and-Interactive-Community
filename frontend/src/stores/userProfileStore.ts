import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { userApi } from '../api/user'
import { buildMediaUrl } from '../utils/urlUtils'
import config from '../utils/config'
import { getApiErrorMessage } from '../utils/error'
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

const USER_CACHE_PREFIX = 'user_profile:'
const LEGACY_AVATAR_KEY = 'user_avatar'
const LEGACY_BANNER_KEY = 'user_banner'

function getUserCacheKey(userId: number) {
  return `${USER_CACHE_PREFIX}${userId}`
}

function readCachedUser(userId: number): User | null {
  try {
    const raw = localStorage.getItem(getUserCacheKey(userId))
    if (!raw) return null
    return JSON.parse(raw)
  } catch {
    return null
  }
}

function writeCachedUser(userId: number, user: User) {
  localStorage.setItem(getUserCacheKey(userId), JSON.stringify(user))
}

function removeCachedUser(userId: number) {
  localStorage.removeItem(getUserCacheKey(userId))
}

export const useUserProfileStore = defineStore('userProfile', () => {
  const tokenStore = useTokenStore()
  const user = ref<User | null>(null)
  const loading = ref<boolean>(false)
  const error = ref<string | null>(null)
  const failedToLoad = ref(false)

  const activeUserId = computed(() => tokenStore.activeUserId)

  const isLoggedIn = computed(() => {
    return !!user.value && !!user.value.id
  })

  const loadUserFromCache = (userId: number) => {
    const cached = readCachedUser(userId)
    if (cached) {
      user.value = cached
      return true
    }
    return false
  }

  const fetchUserInfo = async (options: { force?: boolean } = {}) => {
    const currentUserId = activeUserId.value
    if (!currentUserId) {
      user.value = null
      return null
    }

    if (loading.value) return user.value

    if (!options.force && loadUserFromCache(currentUserId)) {
      return user.value
    }

    if (!tokenStore.accessToken) {
      user.value = null
      return null
    }

    loading.value = true
    failedToLoad.value = false
    error.value = null

    try {
      const userData = await userApi.getProfile()

      const avatarUrl = buildMediaUrl(userData.avatar, config.media.defaultAvatar)
      const bannerUrl = buildMediaUrl(userData.banner, config.media.defaultBanner)

      const normalized: User = {
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

      user.value = normalized
      writeCachedUser(normalized.id, normalized)

      // 同步更新账号元数据
      tokenStore.updateAccountMeta({
        userId: normalized.id,
        username: normalized.username,
        avatar: normalized.avatar
      })

      return normalized
    } catch (err) {
      failedToLoad.value = true
      error.value = getApiErrorMessage(err, '获取用户信息失败')
      const status = (err as { response?: { status?: number } }).response?.status
      if (status === 401) {
        tokenStore.removeAccount(currentUserId)
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
          writeCachedUser(user.value.id, user.value)
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
        writeCachedUser(user.value.id, user.value)
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
  }

  const clearAllUsers = () => {
    tokenStore.accounts.forEach(a => removeCachedUser(a.userId))
    clearUser()
    localStorage.removeItem(LEGACY_AVATAR_KEY)
    localStorage.removeItem(LEGACY_BANNER_KEY)
    localStorage.removeItem('tempAvatarPreview')
    localStorage.removeItem('tempBannerPreview')
  }

  const initializeUser = () => {
    const currentUserId = activeUserId.value
    if (!currentUserId) {
      user.value = null
      return
    }

    if (loadUserFromCache(currentUserId)) {
      fetchUserInfo()
    } else {
      // 兼容旧版缓存：如果新缓存没有但旧版头像 key 存在，尝试用 token 拉取
      fetchUserInfo()
    }
  }

  // 监听 activeUserId 变化，自动加载对应用户信息
  watch(
    () => tokenStore.activeUserId,
    (newId, oldId) => {
      if (newId && newId !== oldId) {
        if (!loadUserFromCache(newId)) {
          fetchUserInfo()
        }
      } else if (!newId) {
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
    clearAllUsers,
    initializeUser
  }
})
