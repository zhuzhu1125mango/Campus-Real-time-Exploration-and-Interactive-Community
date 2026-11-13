import { defineStore } from 'pinia'
import { ref } from 'vue'
import { userApi } from '../api/user'
import { getApiErrorMessage } from '../utils/error'
import { useTokenStore } from './tokenStore'
import { useUserProfileStore } from './userProfileStore'

export interface LoginResult {
  switched: boolean
  userId: number
  username: string
}

export const useAuthStore = defineStore('auth', () => {
  const tokenStore = useTokenStore()
  const userProfileStore = useUserProfileStore()

  const loading = ref<boolean>(false)
  const error = ref<string | null>(null)

  /**
   * 登录账号。
   * @param options.switch 登录成功后是否切换为当前账号；默认 true。
   */
  const login = async (
    username: string,
    password: string,
    options: { switch?: boolean } = {}
  ): Promise<LoginResult | null> => {
    loading.value = true
    error.value = null

    try {
      const response = await userApi.login({ username, password })
      const user = response.user
      const userId = Number(user?.id)

      if (!userId || !user) {
        error.value = '登录响应缺少用户ID'
        return null
      }

      tokenStore.addAccount(userId, response.access, response.refresh, {
        switch: options.switch !== false
      })

      // 同步更新账号元数据
      tokenStore.updateAccountMeta({
        userId,
        username: user.username,
        avatar: user.avatar || undefined
      })

      // 拉取并缓存完整用户信息
      await userProfileStore.fetchUserInfo({ force: true })

      return {
        switched: options.switch !== false,
        userId,
        username: user.username
      }
    } catch (err) {
      error.value = getApiErrorMessage(err, '登录失败，请检查用户名和密码')
      return null
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
    } catch (err) {
      error.value = getApiErrorMessage(err, '注册失败，请稍后重试')
      return false
    } finally {
      loading.value = false
    }
  }

  /**
   * 退出当前账号。
   * @param all 是否清除所有已保存账号；默认 false。
   */
  const logout = async (all = false) => {
    try {
      await userApi.logout()
    } catch (error) {
      // 登出请求发送失败，继续执行登出操作
    } finally {
      if (all) {
        tokenStore.clearAll()
        userProfileStore.clearAllUsers()
      } else {
        const currentId = tokenStore.activeUserId
        if (currentId) {
          tokenStore.removeAccount(currentId)
          userProfileStore.clearUser()
        }
      }
    }
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
    initializeAuth,
    refreshToken
  }
})
