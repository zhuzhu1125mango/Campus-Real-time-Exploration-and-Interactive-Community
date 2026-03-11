import axios, { type AxiosInstance, type InternalAxiosRequestConfig, type AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'
import config from './config'
import { useUserStore } from '@/stores/userStore'

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
    console.log('请求详情:', {
      url: requestConfig.url,
      method: requestConfig.method,
      token: token ? '存在' : '不存在',
      tokenKey: config.jwt.accessTokenKey,
      headers: requestConfig.headers
    })
    
    if (token) {
      // 根据后端要求设置认证头
      const authHeader = `${config.jwt.tokenType} ${token}`
      requestConfig.headers.set('Authorization', authHeader)
      console.log('认证头设置:', {
        authHeader,
        fullHeaders: requestConfig.headers
      })
    } else {
      console.log('未找到token，跳过认证')
    }
    return requestConfig
  },
  (error) => {
    console.error('请求拦截器错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  (response: AxiosResponse) => {
    console.log('响应成功:', {
      url: response.config.url,
      status: response.status,
      data: response.data
    })
    return response.data
  },
  async (error) => {
    console.error('响应错误:', {
      url: error.config?.url,
      status: error.response?.status,
      data: error.response?.data,
      message: error.message
    })
    
    // 获取原始请求配置
    const originalRequest = error.config
    
    // 处理错误响应
    if (error.response) {
      const { status, data } = error.response
      
      // 处理token过期 (401错误)
      if (status === 401 && !originalRequest._retry) {
        console.log('Token过期，尝试刷新Token')
        
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
            console.log('刷新Token失败，跳转到登录页')
            localStorage.removeItem(config.jwt.accessTokenKey)
            localStorage.removeItem(config.jwt.refreshTokenKey)
            window.location.href = '/login'
            return Promise.reject(error)
          }
        } catch (refreshError) {
          console.error('刷新Token失败:', refreshError)
          localStorage.removeItem(config.jwt.accessTokenKey)
          localStorage.removeItem(config.jwt.refreshTokenKey)
          window.location.href = '/login'
          return Promise.reject(error)
        } finally {
          isRefreshing = false
        }
      }
      
      switch (status) {
        case 400:
          ElMessage.error(data.message || '请求参数错误')
          break
        case 401:
          console.log('认证失败，清除token并跳转登录页')
          ElMessage.error('请先登录')
          localStorage.removeItem(config.jwt.accessTokenKey)
          localStorage.removeItem(config.jwt.refreshTokenKey)
          window.location.href = '/login'
          break
        case 403:
          console.log('权限不足:', data.message)
          ElMessage.error('没有权限访问')
          break
        case 404:
          ElMessage.error('请求的资源不存在')
          break
        case 500:
          ElMessage.error('服务器错误，请稍后重试')
          break
        default:
          ElMessage.error(data.message || '请求失败')
      }
    } else if (error.request) {
      console.log('网络请求失败:', error.request)
      ElMessage.error('网络错误，请检查网络连接')
    } else {
      console.log('请求配置错误:', error.message)
      ElMessage.error('请求配置错误')
    }
    
    return Promise.reject(error)
  }
)

export default service 