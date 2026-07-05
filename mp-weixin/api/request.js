// API 基础配置：优先读取环境变量，无环境变量时使用本地开发默认值
const API_BASE_URL = process.env.VUE_APP_API_BASE_URL || 'http://192.168.202.1:8000/api'
const WS_BASE_URL = process.env.VUE_APP_WS_BASE_URL || 'ws://192.168.202.1:8000/ws/chat'

// 超时设置（毫秒）
const REQUEST_TIMEOUT = 30000

// 重试次数
const MAX_RETRY_COUNT = 3

// token 刷新状态
let isRefreshing = false
let refreshPromise = null

// 登录态失效后统一跳转
const redirectToLogin = () => {
  uni.removeStorageSync('accessToken')
  uni.removeStorageSync('refreshToken')
  uni.navigateTo({ url: '/pages/login/login' })
}

// 刷新 access token
const refreshAccessToken = async () => {
  const refreshToken = uni.getStorageSync('refreshToken')
  if (!refreshToken) {
    redirectToLogin()
    throw new Error('没有刷新token')
  }

  const res = await uni.request({
    url: `${API_BASE_URL}/token/refresh/`,
    method: 'POST',
    data: { refresh: refreshToken },
    header: { 'Content-Type': 'application/json' },
    timeout: REQUEST_TIMEOUT
  })

  if (res.statusCode !== 200 || !res.data || !res.data.access) {
    redirectToLogin()
    throw new Error('Token刷新失败')
  }

  uni.setStorageSync('accessToken', res.data.access)
  if (res.data.refresh) {
    uni.setStorageSync('refreshToken', res.data.refresh)
  }
  return res.data.access
}

// 请求拦截器
const requestInterceptor = (config) => {
  // 添加认证token
  const token = uni.getStorageSync('accessToken')
  if (token) {
    config.header['Authorization'] = `Bearer ${token}`
  }

  // 添加请求时间戳
  config.header['X-Request-Time'] = Date.now()

  return config
}

// 响应拦截器
const responseInterceptor = (response) => {
  const { statusCode, data } = response

  // 统一错误处理
  if (statusCode !== 200) {
    handleError(response)
  }

  return data
}

// 错误处理
const handleError = (response) => {
  const { statusCode, data } = response

  switch (statusCode) {
    case 401:
      // 未授权统一在 requestWithRetry 中处理刷新，这里不再重复跳转
      uni.showToast({ title: data?.detail || '登录已过期', icon: 'none' })
      break
    case 403:
      uni.showToast({ title: '无权限访问', icon: 'none' })
      break
    case 404:
      uni.showToast({ title: '接口不存在', icon: 'none' })
      break
    case 500:
      uni.showToast({ title: '服务器错误', icon: 'none' })
      break
    default:
      uni.showToast({
        title: data?.message || '请求失败',
        icon: 'none'
      })
  }
}

// 带重试和 token 刷新的请求方法
const requestWithRetry = async (config, retryCount = 0) => {
  try {
    const intercepted = requestInterceptor({
      ...config,
      header: {
        'Content-Type': 'application/json',
        ...(config.header || {})
      }
    })

    const response = await uni.request({
      ...intercepted,
      url: API_BASE_URL + intercepted.url,
      timeout: REQUEST_TIMEOUT
    })

    // 401 时尝试刷新 token（排除登录和刷新接口自身）
    if (response.statusCode === 401 && !config._retry) {
      const url = config.url || ''
      const isLoginOrRefresh = [
        '/users/users/login/',
        '/token/refresh/'
      ].some(path => url.includes(path))

      if (!isLoginOrRefresh) {
        config._retry = true

        // 复用正在进行的刷新
        if (isRefreshing && refreshPromise) {
          try {
            const newToken = await refreshPromise
            const retryResponse = await uni.request({
              ...intercepted,
              url: API_BASE_URL + intercepted.url,
              timeout: REQUEST_TIMEOUT,
              header: {
                ...intercepted.header,
                Authorization: `Bearer ${newToken}`
              }
            })
            return responseInterceptor(retryResponse)
          } catch (error) {
            throw error
          }
        }

        isRefreshing = true
        refreshPromise = refreshAccessToken().finally(() => {
          isRefreshing = false
          refreshPromise = null
        })

        try {
          const newToken = await refreshPromise
          const retryResponse = await uni.request({
            ...intercepted,
            url: API_BASE_URL + intercepted.url,
            timeout: REQUEST_TIMEOUT,
            header: {
              ...intercepted.header,
              Authorization: `Bearer ${newToken}`
            }
          })
          return responseInterceptor(retryResponse)
        } catch (error) {
          throw error
        }
      }
    }

    return responseInterceptor(response)
  } catch (error) {
    if (retryCount < MAX_RETRY_COUNT) {
      // 网络错误时重试
      if (error.errno === -1) {
        return requestWithRetry(config, retryCount + 1)
      }
    }

    uni.showToast({ title: '网络错误，请检查网络连接', icon: 'none' })
    throw error
  }
}

// 基础请求方法
const request = {
  get: (url, params = {}) => {
    return requestWithRetry({
      method: 'GET',
      url,
      data: params
    })
  },

  post: (url, data = {}) => {
    return requestWithRetry({
      method: 'POST',
      url,
      data
    })
  },

  put: (url, data = {}) => {
    return requestWithRetry({
      method: 'PUT',
      url,
      data
    })
  },

  delete: (url, params = {}) => {
    return requestWithRetry({
      method: 'DELETE',
      url,
      data: params
    })
  }
}

// 获取WebSocket连接URL（不再将 token 暴露在 URL 查询参数中）
const getWebSocketUrl = (path = '') => {
  return path ? `${WS_BASE_URL}/${path}` : WS_BASE_URL
}

// 获取WebSocket子协议（用于安全传递 token）
const getWebSocketProtocols = () => {
  const token = uni.getStorageSync('accessToken')
  return token ? ['jwt', token] : []
}

export default request
export { API_BASE_URL, WS_BASE_URL, getWebSocketUrl, getWebSocketProtocols }
