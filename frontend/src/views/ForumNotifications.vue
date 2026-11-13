<template>
  <div class="forum-notifications-page container-medium page-padding">
    <SectionHeader
      title="论坛通知"
      subtitle="查看论坛相关通知消息"
      icon="i-ep-bell"
    />

    <GlassCard :hover="false" class="notifications-card">
      <div class="notifications-toolbar">
        <h2 class="card-title">通知列表</h2>
        <button
          v-if="validNotifications.length > 0"
          class="btn btn-primary"
          @click="markAllAsRead"
        >
          <span class="i-ep-check" />
          全部标为已读
        </button>
      </div>

      <div v-if="loading" class="loading-state">
        <div class="loading-spinner" />
        <p>加载中...</p>
      </div>

      <div v-else-if="notifications.length === 0" class="empty-state">
        <div class="empty-icon">
          <span class="i-ep-bell" />
        </div>
        <p>暂无通知</p>
        <router-link to="/forum">
          <button class="btn btn-primary">
            <span class="i-ep-view" />
            浏览论坛
          </button>
        </router-link>
      </div>

      <div v-else class="notifications-list">
        <div
          v-for="notification in validNotifications"
          :key="notification?.id"
          class="notification-item"
          :class="{ 'unread': !notification?.is_read }"
          @click="viewNotification(notification)"
        >
          <div class="notification-dot" v-if="!notification?.is_read" />
          <div class="notification-content">
            <div class="notification-text" v-html="sanitizeHtml(notification?.content || '')" />
            <div class="notification-time">{{ formatDate(notification?.created_at || '') }}</div>
          </div>
          <button
            class="btn btn-secondary"
            @click.stop="markAsRead(notification?.id)"
            v-if="!notification?.is_read"
          >
            <span class="i-ep-check" />
            标为已读
          </button>
        </div>

        <!-- 分页 -->
        <div v-if="totalPages > 1" class="pagination">
          <button
            class="btn btn-secondary"
            :disabled="currentPage === 1"
            @click="changePage(currentPage - 1)"
          >
            <span class="i-ep-arrow-left" />
            上一页
          </button>
          <span class="page-info">{{ currentPage }} / {{ totalPages }}</span>
          <button
            class="btn btn-secondary"
            :disabled="currentPage === totalPages"
            @click="changePage(currentPage + 1)"
          >
            下一页
            <span class="i-ep-arrow-right" />
          </button>
        </div>
      </div>
    </GlassCard>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { userApi } from '../api/user'
import { sanitizeHtml } from '../utils/xss'
import type { Notification } from '../types/user'
import GlassCard from '../components/GlassCard.vue'
import SectionHeader from '../components/SectionHeader.vue'

const router = useRouter()

// 状态
const notifications = ref<Notification[]>([])
const loading = ref(true)
const currentPage = ref(1)
const totalNotifications = ref(0)

// 过滤掉后端可能返回的 null/undefined 项，避免渲染时读取 .id 报错
const validNotifications = computed(() => notifications.value.filter(Boolean))

// 计算属性
const totalPages = computed(() => {
  return Math.ceil(totalNotifications.value / 10)
})

// 获取通知列表
const fetchNotifications = async () => {
  loading.value = true
  try {
    const response = await userApi.getNotifications({
      page: currentPage.value,
      page_size: 10
    })
    notifications.value = response.results
    totalNotifications.value = response.count
  } catch (error) {
    console.error('获取通知失败:', error)
  } finally {
    loading.value = false
  }
}

// 查看通知
const viewNotification = (notification: Notification | null | undefined) => {
  if (!notification) return
  if (!notification.is_read) {
    markAsRead(notification.id)
  }
  if (notification.url && notification.url.startsWith('/')) {
    router.push(notification.url)
  }
}

// 标记单条通知为已读
const markAsRead = async (notificationId: number) => {
  try {
    await userApi.markNotificationAsRead(notificationId)

    // 更新本地状态
    const notification = notifications.value.find(n => n.id === notificationId)
    if (notification) {
      notification.is_read = true
    }
  } catch (error) {
    console.error('标记通知已读失败:', error)
  }
}

// 标记所有通知为已读
const markAllAsRead = async () => {
  try {
    await userApi.markAllNotificationsAsRead()

    // 标记所有通知为已读（仅更新有效项，避免 null 项报错）
    validNotifications.value.forEach(notification => {
      notification.is_read = true
    })
  } catch (error) {
    console.error('标记所有通知已读失败:', error)
  }
}

// 分页
const changePage = (page: number) => {
  currentPage.value = page
  fetchNotifications()
}

// 格式化日期
const formatDate = (dateStr: string) => {
  if (!dateStr) return '未知'

  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  // 小于一天，显示相对时间
  if (diff < 24 * 60 * 60 * 1000) {
    const hours = Math.floor(diff / (60 * 60 * 1000))
    if (hours === 0) {
      const minutes = Math.floor(diff / (60 * 1000))
      return minutes <= 0 ? '刚刚' : `${minutes}分钟前`
    }
    return `${hours}小时前`
  }

  // 显示年月日
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

// 生命周期钩子
onMounted(async () => {
  await fetchNotifications()
})
</script>

<style scoped>
.notifications-card {
  overflow: hidden;
}

.notifications-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-5);
}

.card-title {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text-primary);
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-10) 0;
  color: var(--text-secondary);
  text-align: center;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(67, 97, 238, 0.2);
  border-radius: 50%;
  border-top-color: var(--primary-500);
  animation: spin 1s linear infinite;
  margin-bottom: var(--space-3);
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-icon {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: var(--primary-50);
  color: var(--primary-500);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: var(--space-4);
  font-size: 2rem;
}

.empty-state p {
  margin-bottom: var(--space-4);
}

.notifications-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.notification-item {
  position: relative;
  display: flex;
  align-items: center;
  padding: var(--space-4);
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
  cursor: pointer;
  transition: all 0.2s ease;
}

.notification-item:hover {
  border-color: var(--primary-600);
  box-shadow: var(--shadow-sm);
}

.notification-item.unread {
  background: var(--primary-50);
  border-color: var(--primary-200);
}

.notification-dot {
  width: 10px;
  height: 10px;
  background-color: var(--primary-600);
  border-radius: 50%;
  margin-right: var(--space-3);
  flex-shrink: 0;
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-text {
  margin-bottom: var(--space-1);
  color: var(--text-primary);
  line-height: 1.5;
}

.notification-time {
  font-size: 0.875rem;
  color: var(--text-tertiary);
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: var(--space-5);
  gap: var(--space-4);
}

.page-info {
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: 0.625rem 1.25rem;
  border-radius: var(--radius-md);
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: all 0.2s ease;
}

.btn-primary {
  background-color: var(--primary-600);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: var(--primary-700);
}

.btn-secondary {
  background-color: var(--bg-tertiary);
  color: var(--text-primary);
}

.btn-secondary:hover:not(:disabled) {
  background-color: var(--border-color);
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .notifications-toolbar {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-3);
  }

  .notification-item {
    flex-direction: column;
    align-items: flex-start;
  }

  .notification-dot {
    position: absolute;
    top: var(--space-4);
    left: var(--space-2);
  }

  .notification-content {
    padding-left: var(--space-4);
    width: 100%;
  }

  .notification-item .btn {
    margin-left: var(--space-4);
    margin-top: var(--space-3);
  }
}
</style>
