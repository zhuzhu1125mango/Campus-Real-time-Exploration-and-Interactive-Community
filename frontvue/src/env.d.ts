/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_APP_TITLE: string
  readonly VITE_APP_DESCRIPTION: string
  readonly VITE_UPLOAD_URL: string
  readonly VITE_STATIC_URL: string
  readonly VITE_CORS_ORIGIN: string
  readonly VITE_JWT_ACCESS_TOKEN_KEY: string
  readonly VITE_JWT_REFRESH_TOKEN_KEY: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
} 