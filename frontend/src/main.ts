import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import './style.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import { useUserStore } from './stores/userStore'

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)  // 使用 Pinia 状态管理
app.use(ElementPlus)    // 使用 Element Plus UI 组件库

// 注册所有 Element Plus 图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(router)        // 使用路由
app.mount('#app')      // 挂载应用

// 在 Pinia 和应用挂载后初始化用户状态
const userStore = useUserStore()
userStore.initialize()