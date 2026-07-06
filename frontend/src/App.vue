<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import request from './utils/request'
import Toast from './components/Toast.vue'
import NotificationDropdown from './components/NotificationDropdown.vue'
import ThemeToggle from './components/ThemeToggle.vue'
import NavDropdown from './components/NavDropdown.vue'
import { userApi } from './api/user'
import { useUserStore } from './stores/userStore'
import config from './utils/config'
import type { NavDropdownItem } from './components/NavDropdown.vue'

// 使用User Store
const userStore = useUserStore()
const router = useRouter()

// 后端服务器状态
const backendStatus = ref<'checking' | 'online' | 'offline'>('checking')
// 应用初始化状态
const appInitialized = ref(false)
// 未读私信数
const unreadMessageCount = ref(0)
let unreadMessageInterval: number
// 移动端菜单状态
const mobileMenuOpen = ref(false)

// 检查后端服务器状态（带超时、取消和重试）
const checkBackendStatus = async (retries = 2) => {
  console.log('开始检查后端服务器状态')
  for (let attempt = 0; attempt <= retries; attempt++) {
    const controller = new AbortController()
    const timeoutId = window.setTimeout(() => controller.abort(), 5000)
    try {
      // 使用统一 request 封装（响应拦截器已返回 response.data）
      const data = await request.get('/health/', {
        signal: controller.signal,
        timeout: 5000
      })
      if (data?.status === 'ok') {
        console.log('后端服务器可用')
        backendStatus.value = 'online'
        appInitialized.value = true
        return
      }
      throw new Error('健康检查失败')
    } catch (error: any) {
      const isAbort = error.name === 'AbortError'
      if (isAbort) {
        console.warn(`健康检查超时（尝试 ${attempt + 1}/${retries + 1}）`)
      } else if (attempt >= retries) {
        console.error('后端服务器不可用:', error.message || error)
      }
      if (attempt >= retries) {
        backendStatus.value = 'offline'
        appInitialized.value = false
        return
      }
      // 重试前等待
      await new Promise(resolve => window.setTimeout(resolve, 800 * (attempt + 1)))
    } finally {
      window.clearTimeout(timeoutId)
    }
  }
}

// 检查登录状态
onMounted(async () => {
  // 首先检查后端服务器状态
  await checkBackendStatus()

  // 如果后端服务器可用，再检查登录状态
  if (backendStatus.value === 'online' && localStorage.getItem(config.jwt.accessTokenKey)) {
    try {
      await userStore.fetchUserProfile()
      await fetchUnreadMessageCount()
      unreadMessageInterval = window.setInterval(fetchUnreadMessageCount, 60000)
    } catch (error) {
      console.error('验证登录状态失败', error)
      // 如果获取用户信息失败，清除token
      userStore.logout()
    }
  }
})

onUnmounted(() => {
  if (unreadMessageInterval) {
    clearInterval(unreadMessageInterval)
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

// 获取未读私信数
const fetchUnreadMessageCount = async () => {
  if (!userStore.isLoggedIn) {
    unreadMessageCount.value = 0
    return
  }
  try {
    const response = await userApi.getUnreadMessagesCount()
    unreadMessageCount.value = response?.unread_count || 0
  } catch (error) {
    console.error('获取未读私信数失败:', error)
  }
}

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

// 导航链接配置
const navLinks = computed(() => [
  { to: '/explore', label: '校园探索' },
  { to: '/schools', label: '院校查询' },
  { to: '/forum', label: '论坛' },
  { to: '/learning', label: '在线学习' },
  { to: '/content', label: '内容中心' },
  { to: '/search', label: '搜索' },
])

// 用户下拉菜单项
const userMenuItems = computed<NavDropdownItem[]>(() => [
  { label: '个人中心', icon: 'i-ep-user', to: '/profile' },
  { label: '收藏院校', icon: 'i-ep-star', to: '/my-favorite-schools' },
  { label: '聊天室', icon: 'i-ep-chat-dot-round', to: '/chat-room' },
  { label: '私信', icon: 'i-ep-message', to: '/messages' },
  { divider: true },
  { label: '退出登录', icon: 'i-ep-switch-button', danger: true, action: handleLogout },
])

// 未登录菜单项
const guestMenuItems = computed<NavDropdownItem[]>(() => [
  { label: '登录', icon: 'i-ep-user', to: '/login' },
  { label: '注册', icon: 'i-ep-plus', to: '/register' },
])
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
        <div class="nav-inner">
          <div class="nav-brand">
            <router-link to="/">
              <span class="brand-dot"></span>
              校园实时互动社区
            </router-link>
          </div>

          <!-- 桌面端导航 -->
          <div class="nav-links">
            <router-link
              v-for="link in navLinks"
              :key="link.to"
              :to="link.to"
              class="nav-link"
            >
              {{ link.label }}
            </router-link>
          </div>

          <!-- 右侧工具区 -->
          <div class="nav-tools">
            <ThemeToggle />

            <template v-if="userStore.isLoggedIn">
              <router-link to="/messages" class="messages-link" title="私信">
                <span class="i-ep-message nav-icon" />
                <span v-if="unreadMessageCount > 0" class="nav-badge">
                  {{ unreadMessageCount > 99 ? '99+' : unreadMessageCount }}
                </span>
              </router-link>

              <NotificationDropdown class="notification-container" />

              <NavDropdown :items="userMenuItems">
                <span class="i-ep-user-filled nav-icon" />
                <span class="user-name">{{ userStore.user?.username || '用户' }}</span>
                <span class="i-ep-arrow-down nav-chevron" />
              </NavDropdown>
            </template>

            <template v-else>
              <NavDropdown :items="guestMenuItems">
                <span class="i-ep-user nav-icon" />
                <span class="user-name">访客</span>
                <span class="i-ep-arrow-down nav-chevron" />
              </NavDropdown>
            </template>

            <!-- 移动端菜单按钮 -->
            <button
              type="button"
              class="mobile-menu-btn"
              :aria-expanded="mobileMenuOpen"
              aria-label="切换菜单"
              @click="mobileMenuOpen = !mobileMenuOpen"
            >
              <span
                class="nav-icon"
                :class="mobileMenuOpen ? 'i-ep-close' : 'i-ep-menu'"
              />
            </button>
          </div>
        </div>

        <!-- 移动端导航菜单 -->
        <transition name="slide-down">
          <div v-show="mobileMenuOpen" class="mobile-menu">
            <router-link
              v-for="link in navLinks"
              :key="link.to"
              :to="link.to"
              class="mobile-nav-link"
              @click="mobileMenuOpen = false"
            >
              {{ link.label }}
            </router-link>
            <template v-if="userStore.isLoggedIn">
              <router-link to="/profile" class="mobile-nav-link" @click="mobileMenuOpen = false">
                个人中心
              </router-link>
              <router-link to="/messages" class="mobile-nav-link" @click="mobileMenuOpen = false">
                私信
                <span v-if="unreadMessageCount > 0" class="mobile-badge">
                  {{ unreadMessageCount > 99 ? '99+' : unreadMessageCount }}
                </span>
              </router-link>
              <button type="button" class="mobile-nav-link text-error" @click="handleLogout">
                退出登录
              </button>
            </template>
            <template v-else>
              <router-link to="/login" class="mobile-nav-link" @click="mobileMenuOpen = false">
                登录
              </router-link>
              <router-link to="/register" class="mobile-nav-link" @click="mobileMenuOpen = false">
                注册
              </router-link>
            </template>
          </div>
        </transition>
      </nav>

      <main class="main-content">
        <router-view></router-view>
      </main>

      <footer class="footer">
        <p>&copy; 2025 校园实时互动社区. All rights reserved.</p>
      </footer>
    </template>

    <!-- 全局Toast通知组件 -->
    <Toast />
  </div>
</template>

<style scoped>
.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* 后端服务器检查样式 */
.backend-checking,
.backend-offline {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  background-color: var(--bg-secondary);
  text-align: center;
  padding: 2rem;
}

.checking-spinner {
  width: 50px;
  height: 50px;
  border: 4px solid rgba(37, 99, 235, 0.3);
  border-radius: 50%;
  border-top-color: var(--primary-600);
  animation: spin 1s ease-in-out infinite;
  margin-bottom: var(--space-6);
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.backend-checking p {
  font-size: 1.2rem;
  color: var(--text-secondary);
}

.backend-offline .offline-icon {
  font-size: 4rem;
  margin-bottom: var(--space-6);
}

.backend-offline h2 {
  font-size: 2rem;
  color: var(--error-color);
  margin-bottom: var(--space-4);
}

.backend-offline p {
  font-size: 1.1rem;
  color: var(--text-secondary);
  margin-bottom: var(--space-8);
  max-width: 500px;
}

.retry-button {
  padding: 0.8rem 1.5rem;
  background-color: var(--primary-600);
  color: var(--text-inverse);
  border: none;
  border-radius: var(--radius-md);
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.3s;
}

.retry-button:hover {
  background-color: var(--primary-700);
}

/* 导航栏 */
.navbar {
  position: sticky;
  top: 0;
  z-index: 100;
  background: var(--glass-bg);
  backdrop-filter: blur(12px) saturate(180%);
  -webkit-backdrop-filter: blur(12px) saturate(180%);
  border-bottom: 1px solid var(--glass-border);
  box-shadow: var(--glass-shadow);
  transition: all 0.3s ease;
}

.nav-inner {
  max-width: 1280px;
  margin: 0 auto;
  padding: var(--space-3) var(--space-6);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
}

.nav-brand a {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  font-size: 1.35rem;
  font-weight: 700;
  color: var(--text-primary);
  text-decoration: none;
  white-space: nowrap;
  transition: color 0.3s;
}

.nav-brand a:hover {
  color: var(--primary-600);
}

.brand-dot {
  width: 10px;
  height: 10px;
  border-radius: var(--radius-full);
  background: var(--primary-600);
  box-shadow: 0 0 0 4px var(--primary-100);
}

.dark .brand-dot {
  box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.25);
}

.nav-links {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
  margin-left: auto;
  margin-right: var(--space-4);
}

.nav-links::-webkit-scrollbar {
  display: none;
}

.nav-link {
  color: var(--text-secondary);
  text-decoration: none;
  font-weight: 500;
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-md);
  transition: all 0.2s ease;
  white-space: nowrap;
}

.nav-link:hover {
  color: var(--primary-600);
  background: var(--primary-50);
  text-decoration: none;
}

.nav-link.router-link-active {
  color: var(--primary-600);
  font-weight: 600;
  background: var(--primary-50);
}

.dark .nav-link:hover,
.dark .nav-link.router-link-active {
  color: var(--primary-400);
  background: var(--bg-tertiary);
}

.nav-tools {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.nav-icon {
  width: 20px;
  height: 20px;
}

.nav-chevron {
  width: 14px;
  height: 14px;
  opacity: 0.6;
}

.messages-link {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: var(--radius-full);
  color: var(--text-secondary);
  transition: all 0.2s ease;
}

.messages-link:hover {
  color: var(--primary-600);
  background: var(--primary-50);
}

.dark .messages-link:hover {
  color: var(--primary-400);
  background: var(--bg-tertiary);
}

.nav-badge {
  position: absolute;
  top: 2px;
  right: 2px;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  background-color: var(--error-color);
  color: var(--text-inverse);
  font-size: 10px;
  font-weight: 600;
  border-radius: var(--radius-full);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

.notification-container {
  display: inline-flex;
  align-items: center;
}

.user-name {
  max-width: 80px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 0.95rem;
  font-weight: 500;
}

.mobile-menu-btn {
  display: none;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  transition: all 0.2s ease;
}

.mobile-menu-btn:hover {
  color: var(--primary-600);
  background: var(--primary-50);
}

/* 移动端菜单 */
.mobile-menu {
  display: none;
  flex-direction: column;
  padding: var(--space-2) var(--space-6) var(--space-4);
  border-top: 1px solid var(--border-color-light);
  background: var(--glass-bg);
  backdrop-filter: blur(12px) saturate(180%);
}

.mobile-nav-link {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-weight: 500;
  transition: all 0.2s ease;
}

.mobile-nav-link:hover,
.mobile-nav-link.router-link-active {
  color: var(--primary-600);
  background: var(--primary-50);
}

.text-error {
  color: var(--error-color);
}

.mobile-badge {
  padding: 2px 8px;
  background: var(--error-color);
  color: var(--text-inverse);
  font-size: 0.75rem;
  font-weight: 600;
  border-radius: var(--radius-full);
}

.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.25s ease;
}

.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

.main-content {
  flex: 1;
  background-color: var(--bg-secondary);
}

.footer {
  background-color: var(--bg-primary);
  padding: var(--space-6);
  text-align: center;
  color: var(--text-secondary);
  font-size: 0.9rem;
  border-top: 1px solid var(--border-color-light);
}

@media (max-width: 1024px) {
  .nav-links {
    display: none;
  }

  .mobile-menu-btn {
    display: inline-flex;
  }

  .mobile-menu {
    display: flex;
  }
}

@media (max-width: 640px) {
  .nav-inner {
    padding: var(--space-3) var(--space-4);
  }

  .nav-brand a {
    font-size: 1.1rem;
  }

  .user-name {
    display: none;
  }

  .nav-chevron {
    display: none;
  }
}
</style>
