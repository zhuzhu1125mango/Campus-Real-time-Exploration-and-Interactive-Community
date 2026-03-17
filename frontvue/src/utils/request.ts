import axios, { type AxiosInstance, type InternalAxiosRequestConfig, type AxiosResponse } from 'axios'
import config from './config'
import { useUserStore } from '@/stores/userStore'

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
// 等待刷新token的请求队列
let requests: Array<(token: string) => void> = []

// 创建 axios 实例
const service: AxiosInstance = axios.create({
  baseURL: config.apiBaseUrl,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
service.interceptors.request.use(
  (requestConfig: InternalAxiosRequestConfig) => {
    // 从 localStorage 获取 token
    const token = localStorage.getItem(config.jwt.accessTokenKey)
    
    if (token) {
      // 根据后端要求设置认证头
      const authHeader = `${config.jwt.tokenType} ${token}`
      requestConfig.headers.set('Authorization', authHeader)
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
        if (isRefreshing) {
          // 如果已经在刷新token，将请求加入队列
          return new Promise(resolve => {
            requests.push((token: string) => {
              originalRequest.headers.Authorization = `${config.jwt.tokenType} ${token}`
              resolve(service(originalRequest))
            })
          })
        }
        
        originalRequest._retry = true
        isRefreshing = true
        
        try {
          // 获取刷新token
          const refreshToken = localStorage.getItem(config.jwt.refreshTokenKey)
          if (!refreshToken) {
            throw new Error('没有刷新token')
          }
          
          // 使用userStore中的方法刷新token
          const userStore = useUserStore()
          const newToken = await userStore.refreshAuthToken()
          
          if (newToken) {
            // 执行队列中的请求
            requests.forEach(callback => callback(newToken))
            requests = []
            
            // 更新当前请求的Authorization头
            originalRequest.headers.Authorization = `${config.jwt.tokenType} ${newToken}`
            return service(originalRequest)
          } else {
            // 刷新失败，清除token并跳转到登录页
            localStorage.removeItem(config.jwt.accessTokenKey)
            localStorage.removeItem(config.jwt.refreshTokenKey)
            redirectToLogin()
            return Promise.reject(error)
          }
        } catch (refreshError) {
          localStorage.removeItem(config.jwt.accessTokenKey)
          localStorage.removeItem(config.jwt.refreshTokenKey)
          redirectToLogin()
          return Promise.reject(error)
        } finally {
          isRefreshing = false
        }
      }
      
      switch (status) {
        case 400:
          console.error(data.message || '请求参数错误')
          break
        case 401:
          console.error('请先登录')
          localStorage.removeItem(config.jwt.accessTokenKey)
          localStorage.removeItem(config.jwt.refreshTokenKey)
          redirectToLogin()
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

export default service 