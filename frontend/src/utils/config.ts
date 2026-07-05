// 环境变量配置
interface Config {
  apiBaseUrl: string
  wsBaseUrl: string
  media: {
    baseUrl: string
    defaultAvatar: string
    defaultBanner: string
  }
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
  wsBaseUrl: import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000',
  media: {
    baseUrl: import.meta.env.VITE_MEDIA_BASE_URL || 'http://localhost:8000',
    defaultAvatar: '/media/avatars/default-avatar.svg',
    defaultBanner: '/media/banners/default-banner.svg'
  },
  cors: {
    allowedOrigins: [
      'http://localhost:5173',
      'http://localhost:5174',
      'http://localhost:5175',
      'http://localhost:3000',
      'http://localhost:8080',
      'http://localhost:8081'
    ],
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
    maxSize: 5 * 1024 * 1024, // 5MB，与后端头像限制一致
    allowedTypes: ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
    maxCount: 9
  },
  pagination: {
    defaultPageSize: 10,
    maxPageSize: 100
  }
}

export default config 