// 环境变量配置
interface Config {
  apiBaseUrl: string
  cors: {
    allowedOrigins: string[]
    allowedMethods: string[]
    allowedHeaders: string[]
  }
  jwt: {
    accessTokenKey: string
    refreshTokenKey: string
    tokenType: string
    expiresIn: number
  }
  app: {
    title: string
    description: string
  }
  upload: {
    maxSize: number
    allowedTypes: string[]
    maxCount: number
  }
  pagination: {
    defaultPageSize: number
    maxPageSize: number
  }
}

const config: Config = {
  apiBaseUrl: '/api',
  cors: {
    allowedOrigins: ['http://localhost:5173'],
    allowedMethods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization']
  },
  jwt: {
    accessTokenKey: 'access_token',
    refreshTokenKey: 'refresh_token',
    tokenType: 'Bearer',
    expiresIn: 3600 // 1小时
  },
  app: {
    title: import.meta.env.VITE_APP_TITLE || '校园实时互动社区',
    description: import.meta.env.VITE_APP_DESCRIPTION || '连接校园, 分享知识, 共同成长'
  },
  upload: {
    maxSize: 5 * 1024 * 1024, // 5MB
    allowedTypes: ['image/jpeg', 'image/png', 'image/gif'],
    maxCount: 9
  },
  pagination: {
    defaultPageSize: 10,
    maxPageSize: 100
  }
}

export default config 