import axios, { type AxiosInstance, type InternalAxiosRequestConfig, type AxiosResponse } from 'axios'
import config from './config'

// 页面跳转函数
const redirectToLogin = () => {
  // 检查是否在浏览器环境中
  if (typeof window !== 'undefined') {
    // 使用window.location.href进行跳转，因为在工具文件中直接导入router可能会导致循环依赖
    window.location.href = '/login'
  }
}

// 是否正在刷新token
let isRefreshing = false
// 共享的 token 刷新 Promise，用于让并发 401 请求等待同一次刷新
let refreshPromise: Promise<string | null> | null = null

// 创建 axios 实例
const service: AxiosInstance = axios.create({
  baseURL: config.apiBaseUrl,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 从cookie中获取CSRF token
const getCSRFToken = () => {
  if (typeof document === 'undefined') return ''
  const cookieValue = document.cookie
    .split('; ') 
    .find(row => row.startsWith('csrftoken=')) 
    ?.split('=')[1]
  return cookieValue || ''
}

// 请求拦截器
service.interceptors.request.use(
  (requestConfig: InternalAxiosRequestConfig) => {
    // 从 localStorage 获取 token
    const token = localStorage.getItem(config.jwt.accessTokenKey)
    
    // 登录请求和刷新token请求不设置Authorization头
    const loginPaths = ['/users/users/login/', '/users/users/email_code_login/', '/users/users/phone_code_login/']
    const refreshPath = '/token/refresh/'
    
    const url = requestConfig.url || ''
    const shouldSetAuth = !loginPaths.some(path => url.includes(path)) && url !== refreshPath
    
    if (token && shouldSetAuth) {
      // 根据后端要求设置认证头
      const authHeader = `${config.jwt.tokenType} ${token}`
      requestConfig.headers.set('Authorization', authHeader)
    }
    
    // 添加CSRF token
    const csrfToken = getCSRFToken()
    if (csrfToken) {
      requestConfig.headers.set('X-CSRFToken', csrfToken)
    }
    
    return requestConfig
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  (response: AxiosResponse) => {
    return response.data
  },
  async (error) => {
    // 获取原始请求配置
    const originalRequest = error.config
    
    // 处理错误响应
    if (error.response) {
      const { status, data } = error.response
      
      // 处理token过期 (401错误)
        if (status === 401 && !originalRequest._retry) {
          // 检查是否是登录请求或刷新token请求
          const url = originalRequest.url || ''
          const isLoginRequest = ['/users/users/login/', '/users/users/email_code_login/', '/users/users/phone_code_login/'].some(path => url.includes(path))
          const isRefreshRequest = url === '/token/refresh/'

          // 登录请求和刷新token请求的401错误直接返回，不尝试刷新token
          if (isLoginRequest || isRefreshRequest) {
            return Promise.reject(error)
          }

          originalRequest._retry = true

          // 如果已经在刷新token，复用共享的刷新 Promise
          if (isRefreshing && refreshPromise) {
            try {
              const newToken = await refreshPromise
              if (!newToken) {
                return Promise.reject(new Error('Token刷新失败'))
              }
              originalRequest.headers.Authorization = `${config.jwt.tokenType} ${newToken}`
              return service.request(originalRequest)
            } catch (refreshError) {
              return Promise.reject(refreshError)
            }
          }

          isRefreshing = true

          refreshPromise = (async () => {
            try {
              // 获取刷新token
              const refreshToken = localStorage.getItem(config.jwt.refreshTokenKey)
              if (!refreshToken) {
                throw new Error('没有刷新token')
              }

              // 使用 service 实例刷新 token，与项目其他请求保持一致
              const refreshResponse = await service.post('/token/refresh/', { refresh: refreshToken }) as { access?: string }
              const newToken = refreshResponse.access

              if (!newToken) {
                throw new Error('Token刷新失败')
              }

              // 保存新token到localStorage
              localStorage.setItem(config.jwt.accessTokenKey, newToken)
              return newToken
            } catch (refreshError) {
              // 刷新失败，清除token并跳转到登录页
              localStorage.removeItem(config.jwt.accessTokenKey)
              localStorage.removeItem(config.jwt.refreshTokenKey)
              redirectToLogin()
              throw refreshError
            } finally {
              isRefreshing = false
              refreshPromise = null
            }
          })()

          try {
            const newToken = await refreshPromise
            if (!newToken) {
              return Promise.reject(new Error('Token刷新失败'))
            }
            // 更新当前请求的Authorization头并重试
            originalRequest.headers.Authorization = `${config.jwt.tokenType} ${newToken}`
            return service.request(originalRequest)
          } catch (refreshError) {
            return Promise.reject(refreshError)
          }
        }
      
      switch (status) {
        case 400:
          console.error(data.message || '请求参数错误')
          break
        case 401:
          // 只有非登录和非刷新token请求的401错误才清除token并跳转到登录页
          const url = originalRequest.url || ''
          const isLoginOrRefresh = ['/users/users/login/', '/users/users/email_code_login/', '/users/users/phone_code_login/', '/token/refresh/'].some(path => url.includes(path))
          if (!isLoginOrRefresh) {
            console.error('请先登录')
            localStorage.removeItem(config.jwt.accessTokenKey)
            localStorage.removeItem(config.jwt.refreshTokenKey)
            redirectToLogin()
          }
          break
        case 403:
          console.error('没有权限访问')
          break
        case 404:
          console.error('请求的资源不存在')
          break
        case 500:
          console.error('服务器错误，请稍后重试')
          break
        default:
          console.error(data.message || '请求失败')
      }
    } else if (error.request) {
      console.error('网络错误，请检查网络连接')
    } else {
      console.error('请求配置错误')
    }
    
    return Promise.reject(error)
  }
)

// 类型断言，确保TypeScript知道响应拦截器会返回响应数据
export default service as unknown as Omit<AxiosInstance, 'get' | 'post' | 'put' | 'delete' | 'patch'> & {
  get<T = any>(url: string, config?: any): Promise<T>
  post<T = any>(url: string, data?: any, config?: any): Promise<T>
  put<T = any>(url: string, data?: any, config?: any): Promise<T>
  delete<T = any>(url: string, config?: any): Promise<T>
  patch<T = any>(url: string, data?: any, config?: any): Promise<T>
}