// API 基础配置
const API_BASE_URL = 'http://192.168.202.1:8000/api'
const WS_BASE_URL = 'ws://192.168.202.1:8000/ws/chat'

// 超时设置（毫秒）
const REQUEST_TIMEOUT = 30000

// 重试次数
const MAX_RETRY_COUNT = 3

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
      // 未授权，清除token并跳转到登录页
      uni.removeStorageSync('accessToken')
      uni.removeStorageSync('refreshToken')
      uni.navigateTo({ url: '/pages/login/login' })
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

// 带重试的请求方法
const requestWithRetry = async (config, retryCount = 0) => {
  try {
    const response = await uni.request({
      ...config,
      url: API_BASE_URL + config.url,
      timeout: REQUEST_TIMEOUT,
      header: {
        'Content-Type': 'application/json',
        ...config.header
      }
    })

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

// 获取WebSocket连接URL
// path: 可选路径后缀，如 'private/123'
const getWebSocketUrl = (path = '') => {
  const token = uni.getStorageSync('accessToken')
  const baseUrl = path ? `${WS_BASE_URL}/${path}` : WS_BASE_URL
  if (token) {
    return `${baseUrl}?token=${token}`
  }
  return baseUrl
}

export default request
export { API_BASE_URL, WS_BASE_URL, getWebSocketUrl }
