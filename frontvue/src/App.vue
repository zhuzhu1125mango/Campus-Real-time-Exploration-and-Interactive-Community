<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { userApi } from './api/user'
import config from './utils/config'
import Toast from './components/Toast.vue'
import NotificationDropdown from './components/NotificationDropdown.vue'
import { useUserStore } from './stores/userStore'

// 使用User Store
const userStore = useUserStore()
const router = useRouter()

// 检查登录状态
onMounted(async () => {
  // 如果本地存储中有token，尝试获取用户信息验证登录状态
  if (localStorage.getItem(config.jwt.accessTokenKey)) {
    try {
      await userStore.fetchUserProfile()
    } catch (error) {
      console.error('验证登录状态失败', error)
      // 如果获取用户信息失败，清除token
      userStore.logout()
    }
  }
})

// 退出登录
const handleLogout = async () => {
  try {
    await userApi.logout()
  } catch (error) {
    console.error('登出请求发送失败', error)
  } finally {
    // 无论API调用成功与否，都清除本地状态
    userStore.logout()
    router.push('/login')
  }
}
</script>

<template>
  <div class="app">
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
    
    <!-- 全局Toast通知组件 -->
    <Toast />
  </div>
</template>

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
