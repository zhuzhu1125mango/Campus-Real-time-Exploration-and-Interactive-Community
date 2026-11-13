import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import config from '../utils/config'
import { userApi } from '../api/user'
import { getApiErrorMessage } from '../utils/error'
import { createDefaultExpiryService, calculateExpiryTime } from '../services/tokenExpiryService'

const ACCOUNTS_KEY = 'auth_accounts'
const ACTIVE_USER_ID_KEY = 'active_user_id'
const TOKEN_KEY_PREFIX = 'auth_tokens:'

export interface AccountMeta {
  userId: number
  username: string
  avatar?: string
}

function getTokenKey(userId: number) {
  return `${TOKEN_KEY_PREFIX}${userId}`
}

function readAccounts(): AccountMeta[] {
  try {
    const raw = localStorage.getItem(ACCOUNTS_KEY)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

function writeAccounts(accounts: AccountMeta[]) {
  localStorage.setItem(ACCOUNTS_KEY, JSON.stringify(accounts))
}

function readActiveUserId(): number | null {
  const raw = localStorage.getItem(ACTIVE_USER_ID_KEY)
  return raw ? Number(raw) : null
}

function writeActiveUserId(userId: number | null) {
  if (userId) {
    localStorage.setItem(ACTIVE_USER_ID_KEY, String(userId))
  } else {
    localStorage.removeItem(ACTIVE_USER_ID_KEY)
  }
}

function readTokens(userId: number): { access: string; refresh: string } | null {
  try {
    const raw = localStorage.getItem(getTokenKey(userId))
    if (!raw) return null
    const parsed = JSON.parse(raw)
    if (parsed?.access && parsed?.refresh) {
      return parsed
    }
  } catch {
    // ignore
  }
  return null
}

function writeTokens(userId: number, access: string, refresh: string) {
  localStorage.setItem(getTokenKey(userId), JSON.stringify({ access, refresh }))
}

function removeTokens(userId: number) {
  localStorage.removeItem(getTokenKey(userId))
}

/**
 * 将旧版单槽位 token 迁移到新的按用户 ID 存储格式。
 * 迁移后删除旧 key，避免重复迁移。
 */
function migrateLegacyTokens(): { userId: number; access: string; refresh: string } | null {
  const access = localStorage.getItem(config.jwt.accessTokenKey)
  const refresh = localStorage.getItem(config.jwt.refreshTokenKey)
  if (!access || !refresh) return null

  try {
    const payload = JSON.parse(atob(access.split('.')[1]))
    const userId = Number(payload?.user_id || payload?.sub)
    if (!userId) return null

    writeTokens(userId, access, refresh)
    writeActiveUserId(userId)
    localStorage.removeItem(config.jwt.accessTokenKey)
    localStorage.removeItem(config.jwt.refreshTokenKey)
    return { userId, access, refresh }
  } catch {
    return null
  }
}

export const useTokenStore = defineStore('token', () => {
  // 初始化时执行一次迁移
  const migrated = migrateLegacyTokens()

  const accounts = ref<AccountMeta[]>(readAccounts())
  const activeUserId = ref<number | null>(readActiveUserId())
  const loading = ref<boolean>(false)
  const error = ref<string | null>(null)

  const accessToken = computed(() => {
    if (!activeUserId.value) return ''
    return readTokens(activeUserId.value)?.access || ''
  })

  const refreshToken = computed(() => {
    if (!activeUserId.value) return ''
    return readTokens(activeUserId.value)?.refresh || ''
  })

  const expiryService = createDefaultExpiryService(() => {
    clearCurrentTokens()
  })

  const setTokens = (access: string, refresh: string, userId: number) => {
    writeTokens(userId, access, refresh)
    if (!activeUserId.value) {
      activeUserId.value = userId
      writeActiveUserId(userId)
    }

    const expiryTime = calculateExpiryTime()
    expiryService.setTokenExpiry(expiryTime)
    expiryService.startExpiryCheck()
  }

  /**
   * 添加/更新一个账号的 token，并可选择是否切换为当前激活账号。
   */
  const addAccount = (
    userId: number,
    access: string,
    refresh: string,
    options: { switch?: boolean } = {}
  ) => {
    writeTokens(userId, access, refresh)
    if (options.switch !== false) {
      activeUserId.value = userId
      writeActiveUserId(userId)
    }

    const expiryTime = calculateExpiryTime()
    expiryService.setTokenExpiry(expiryTime)
    expiryService.startExpiryCheck()
  }

  const switchAccount = (userId: number) => {
    if (!readTokens(userId)) return false
    activeUserId.value = userId
    writeActiveUserId(userId)
    expiryService.startExpiryCheck()
    return true
  }

  const removeAccount = (userId: number) => {
    removeTokens(userId)
    const list = readAccounts().filter(a => a.userId !== userId)
    writeAccounts(list)
    accounts.value = list

    if (activeUserId.value === userId) {
      const next = list[list.length - 1]
      if (next) {
        activeUserId.value = next.userId
        writeActiveUserId(next.userId)
      } else {
        activeUserId.value = null
        writeActiveUserId(null)
        expiryService.clearExpiry()
      }
    }
  }

  const clearCurrentTokens = () => {
    if (activeUserId.value) {
      removeAccount(activeUserId.value)
    }
  }

  const clearAll = () => {
    readAccounts().forEach(a => removeTokens(a.userId))
    localStorage.removeItem(ACCOUNTS_KEY)
    localStorage.removeItem(ACTIVE_USER_ID_KEY)
    accounts.value = []
    activeUserId.value = null
    expiryService.clearExpiry()
  }

  const updateAccountMeta = (meta: AccountMeta) => {
    const list = readAccounts()
    const idx = list.findIndex(a => a.userId === meta.userId)
    if (idx >= 0) {
      list[idx] = meta
    } else {
      list.push(meta)
    }
    writeAccounts(list)
    accounts.value = list
  }

  const refreshAuthToken = async () => {
    const currentRefresh = refreshToken.value
    const userId = activeUserId.value
    if (!currentRefresh || !userId) {
      return null
    }

    loading.value = true
    error.value = null

    try {
      const response = await userApi.refreshToken(currentRefresh)
      writeTokens(userId, response.access, response.refresh || currentRefresh)
      return response.access
    } catch (err) {
      error.value = getApiErrorMessage(err, '刷新token失败')
      removeAccount(userId)
      return null
    } finally {
      loading.value = false
    }
  }

  const ensureValidToken = async () => {
    if (!accessToken.value) {
      return null
    }
    const remaining = expiryService.getRemainingTime()
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

  // 迁移后如果本地没有账号元数据但有 token，补充一个占位账号
  if (migrated) {
    activeUserId.value = migrated.userId
    writeActiveUserId(migrated.userId)
  }

  return {
    accessToken,
    refreshToken,
    activeUserId,
    accounts,
    loading,
    error,
    setTokens,
    addAccount,
    switchAccount,
    removeAccount,
    clearCurrentTokens,
    clearAll,
    updateAccountMeta,
    refreshAuthToken,
    ensureValidToken,
    hasToken,
    initializeTokenCheck
  }
})
