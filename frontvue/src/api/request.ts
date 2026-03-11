import axios, { InternalAxiosRequestConfig, AxiosResponse } from 'axios'
import type { AxiosInstance } from 'axios'
import config from '../utils/config'

// 创建axios实例
const service: AxiosInstance = axios.create({
  baseURL: config.apiBaseUrl,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // 允许跨域携带cookie
})

// 请求拦截器
service.interceptors.request.use(
  (reqConfig: InternalAxiosRequestConfig) => {
    // 从localStorage获取token
    const token = localStorage.getItem(config.jwt.accessTokenKey)
    if (token) {
      reqConfig.headers.set('Authorization', `Bearer ${token}`)
    }
    return reqConfig
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
    const originalRequest = error.config

    // 如果是401错误且未重试过
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        // 尝试刷新token
        const refreshToken = localStorage.getItem(config.jwt.refreshTokenKey)
        const response = await axios.post(`${config.apiBaseUrl}/api/token/refresh/`, {
          refresh: refreshToken,
        })

        // 更新token
        const { access } = response.data
        localStorage.setItem(config.jwt.accessTokenKey, access)

        // 重试原始请求
        originalRequest.headers.set('Authorization', `Bearer ${access}`)
        return service(originalRequest)
      } catch (refreshError) {
        // 刷新token失败，清除token并跳转到登录页
        localStorage.removeItem(config.jwt.accessTokenKey)
        localStorage.removeItem(config.jwt.refreshTokenKey)
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)

// 扩展请求方法的类型
interface RequestMethods {
  get<T = any>(url: string, params?: any): Promise<T>;
  post<T = any>(url: string, data?: any): Promise<T>;
  put<T = any>(url: string, data?: any): Promise<T>;
  patch<T = any>(url: string, data?: any): Promise<T>;
  delete<T = any>(url: string, params?: any): Promise<T>;
}

// 创建带有类型的请求实例
const request: RequestMethods = {
  get<T = any>(url: string, params?: any): Promise<T> {
    return service.get(url, { params }) as Promise<T>;
  },
  post<T = any>(url: string, data?: any): Promise<T> {
    return service.post(url, data) as Promise<T>;
  },
  put<T = any>(url: string, data?: any): Promise<T> {
    return service.put(url, data) as Promise<T>;
  },
  patch<T = any>(url: string, data?: any): Promise<T> {
    return service.patch(url, data) as Promise<T>;
  },
  delete<T = any>(url: string, params?: any): Promise<T> {
    return service.delete(url, { params }) as Promise<T>;
  }
};

export default request 