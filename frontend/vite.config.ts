import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import UnoCSS from 'unocss/vite'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue(), UnoCSS()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@shared': path.resolve(__dirname, '../shared'),
    },
  },
  build: {
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules')) {
            if (id.includes('echarts')) return 'echarts'
            if (id.includes('element-plus') && !id.includes('@element-plus/icons-vue')) return 'element-plus'
            if (id.includes('@element-plus/icons-vue')) return 'element-plus-icons'
            if (id.includes('leaflet')) return 'leaflet'
            if (id.includes('@vueuse/core') || id.includes('@vueuse/shared')) return 'vueuse'
            if (id.includes('axios')) return 'axios'
            if (id.includes('pinia')) return 'pinia'
            if (id.includes('vue-router')) return 'vue-router'
            if (id.includes('tinymce')) return 'tinymce'
          }
        },
      },
    },
  },
  server: {
    port: 5173,
    strictPort: false,
    open: false,
    host: 'localhost',
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
        changeOrigin: true,
      },
      '/health': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/health/': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/media': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      '/trae-api': {
        target: 'https://trae-api-cn.mchost.guru',
        changeOrigin: true,
        rewrite: path => path.replace(/^\/trae-api/, '')
      }
    }
  }
})
