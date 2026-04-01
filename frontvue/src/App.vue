<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { userApi } from './api/user'
import Toast from './components/Toast.vue'
import NotificationDropdown from './components/NotificationDropdown.vue'
import { useUserStore } from './stores/userStore'
import config from './utils/config'
import request from './utils/request'

// 使用User Store
const userStore = useUserStore()
const router = useRouter()

// 后端服务器状态
const backendStatus = ref<'checking' | 'online' | 'offline'>('checking')
// 应用初始化状态
const appInitialized = ref(false)

// 检查后端服务器状态
const checkBackendStatus = async () => {
  console.log('开始检查后端服务器状态')
  try {
    // 发送一个简单的GET请求到后端健康检查端点
    // 健康检查端点在根路径下，没有/api前缀
    const healthUrl = 'http://localhost:8000/health/'
    console.log('发送健康检查请求到:', healthUrl)
    const response = await fetch(healthUrl)
    if (response.ok) {
      console.log('后端服务器可用')
      backendStatus.value = 'online'
      appInitialized.value = true
    } else {
      throw new Error('健康检查失败')
    }
  } catch (error) {
    console.error('后端服务器不可用:', error)
    backendStatus.value = 'offline'
    appInitialized.value = false
  }
  console.log('后端服务器状态:', backendStatus.value)
  console.log('应用初始化状态:', appInitialized.value)
}

// 检查登录状态
onMounted(async () => {
  // 首先检查后端服务器状态
  await checkBackendStatus()
  
  // 如果后端服务器可用，再检查登录状态
  if (backendStatus.value === 'online' && localStorage.getItem(config.jwt.accessTokenKey)) {
    try {
      await userStore.fetchUserProfile()
    } catch (error) {
      console.error('验证登录状态失败', error)
      // 如果获取用户信息失败，清除token
      userStore.logout()
    }
  }
})

// 监听后端状态变化
watch(backendStatus, (newStatus) => {
  if (newStatus === 'online' && !appInitialized.value) {
    appInitialized.value = true
  } else if (newStatus === 'offline') {
    appInitialized.value = false
  }
})

// 退出登录
const handleLogout = async () => {
  try {
    await userApi.logout()
  } catch (error) {
    // 登出请求发送失败，继续执行登出操作
  } finally {
    // 无论API调用成功与否，都清除本地状态
    userStore.logout()
    router.push('/login')
  }
}

// 重新检查后端状态
const retryBackendCheck = async () => {
  backendStatus.value = 'checking'
  await checkBackendStatus()
}
</script>

<template>
  <div class="app">
    <!-- 后端服务器状态检查 -->
    <div v-if="backendStatus === 'checking'" class="backend-checking">
      <div class="checking-spinner"></div>
      <p>正在连接后端服务器...</p>
    </div>
    
    <!-- 后端服务器不可用 -->
    <div v-else-if="backendStatus === 'offline'" class="backend-offline">
      <div class="offline-icon">🔌</div>
      <h2>后端服务器不可用</h2>
      <p>无法连接到后端服务器，请确保后端服务已启动并运行。</p>
      <button class="retry-button" @click="retryBackendCheck">重试连接</button>
    </div>
    
    <!-- 后端服务器可用，显示主应用 -->
    <template v-else>
      <nav class="navbar">
        <div class="nav-brand">
          <router-link to="/">校园实时互动社区</router-link>
        </div>
        <div class="nav-links">
          <router-link to="/schools">院校查询</router-link>
          <router-link to="/forum">论坛</router-link>
          <template v-if="userStore.isLoggedIn">
            <router-link to="/my-favorite-schools">收藏院校</router-link>
            <NotificationDropdown class="notification-container" />
            <router-link to="/profile">个人中心</router-link>
            <a href="#" @click.prevent="handleLogout">退出登录</a>
          </template>
          <template v-else>
            <router-link to="/login">登录</router-link>
            <router-link to="/register">注册</router-link>
          </template>
        </div>
      </nav>

      <main class="main-content">
        <router-view></router-view>
      </main>

      <footer class="footer">
        <p>&copy; 2024 校园实时互动社区. All rights reserved.</p>
      </footer>
    </template>
    
    <!-- 全局Toast通知组件 -->
    <Toast />
  </div>
</template>

<style>
/* 后端服务器检查样式 */
.backend-checking,
.backend-offline {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  background-color: #f9fafc;
  text-align: center;
  padding: 2rem;
}

.checking-spinner {
  width: 50px;
  height: 50px;
  border: 4px solid rgba(67, 97, 238, 0.3);
  border-radius: 50%;
  border-top-color: #4361ee;
  animation: spin 1s ease-in-out infinite;
  margin-bottom: 1.5rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.backend-checking p {
  font-size: 1.2rem;
  color: #666;
}

.backend-offline .offline-icon {
  font-size: 4rem;
  margin-bottom: 1.5rem;
}

.backend-offline h2 {
  font-size: 2rem;
  color: #e74c3c;
  margin-bottom: 1rem;
}

.backend-offline p {
  font-size: 1.1rem;
  color: #666;
  margin-bottom: 2rem;
  max-width: 500px;
}

.retry-button {
  padding: 0.8rem 1.5rem;
  background-color: #4361ee;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.3s;
}

.retry-button:hover {
  background-color: #3a56d4;
}
</style>

<style>
.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.navbar {
  background-color: #fff;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav-brand a {
  font-size: 1.5rem;
  font-weight: 700;
  color: #333;
  text-decoration: none;
  transition: color 0.3s;
  display: flex;
  align-items: center;
}

.nav-brand a:hover {
  color: #4361ee;
}

.nav-brand a::before {
  content: '';
  display: inline-block;
  width: 12px;
  height: 12px;
  background-color: #4361ee;
  border-radius: 50%;
  margin-right: 0.6rem;
}

.nav-links {
  display: flex;
  gap: 1.5rem;
  align-items: center;
}

.nav-links a {
  color: #666;
  text-decoration: none;
  font-weight: 500;
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  transition: all 0.3s;
}

.nav-links a:hover {
  color: #4361ee;
  background-color: rgba(67, 97, 238, 0.08);
  text-decoration: none;
}

.nav-links a.router-link-active {
  color: #4361ee;
  font-weight: 600;
  background-color: rgba(67, 97, 238, 0.08);
}

.notification-container {
  margin: 0 0.5rem;
}

.main-content {
  flex: 1;
  background-color: #f9fafc;
}

.footer {
  background-color: #fff;
  padding: 1.5rem;
  text-align: center;
  color: #666;
  font-size: 0.9rem;
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.05);
}

/* 全局样式 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  line-height: 1.6;
  color: #333;
  background-color: #f9fafc;
}

a {
  color: #4361ee;
  text-decoration: none;
}

a:hover {
  text-decoration: underline;
}

button {
  cursor: pointer;
  font-family: inherit;
}

input, select, textarea {
  font-family: inherit;
}
</style>
