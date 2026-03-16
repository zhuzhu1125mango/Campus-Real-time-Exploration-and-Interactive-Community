<template>
  <div class="notifications-container">
    <div class="notifications-header">
      <h1 class="page-title">论坛通知</h1>
      <button v-if="notifications.length > 0" class="btn-mark-all-read" @click="markAllAsRead">
        全部标为已读
      </button>
    </div>

    <div v-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>加载中...</p>
    </div>

    <div v-else-if="notifications.length === 0" class="empty-notifications">
      <div class="empty-icon"></div>
      <p>暂无通知</p>
      <router-link to="/forum" class="btn-to-forum">浏览论坛</router-link>
    </div>

    <div v-else class="notifications-list">
      <div 
        v-for="notification in notifications" 
        :key="notification.id" 
        class="notification-item"
        :class="{ 'unread': !notification.is_read }"
        @click="viewNotification(notification)"
      >
        <div class="notification-dot" v-if="!notification.is_read"></div>
        <div class="notification-content">
          <div class="notification-text" v-html="notification.content"></div>
          <div class="notification-time">{{ formatDate(notification.created_at) }}</div>
        </div>
        <button class="btn-mark-read" @click.stop="markAsRead(notification.id)" v-if="!notification.is_read">
          标为已读
        </button>
      </div>

      <!-- 分页 -->
      <div v-if="totalPages > 1" class="pagination">
        <button 
          class="btn-page" 
          :disabled="currentPage === 1" 
          @click="changePage(currentPage - 1)"
        >
          上一页
        </button>
        <span class="page-info">{{ currentPage }} / {{ totalPages }}</span>
        <button 
          class="btn-page" 
          :disabled="currentPage === totalPages" 
          @click="changePage(currentPage + 1)"
        >
          下一页
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { forumApi } from '../api/forum'
import type { Notification } from '../types/forum'

const router = useRouter()

// 状态
const notifications = ref<Notification[]>([])
const loading = ref(true)
const currentPage = ref(1)
const totalNotifications = ref(0)

// 计算属性
const totalPages = computed(() => {
  return Math.ceil(totalNotifications.value / 10)
})

// 获取通知列表
const fetchNotifications = async () => {
  loading.value = true
  try {
    const response = await forumApi.getNotifications()
    notifications.value = response
    totalNotifications.value = response.length
  } catch (error) {
    console.error('获取通知失败:', error)
  } finally {
    loading.value = false
  }
}

// 查看通知
const viewNotification = (notification: Notification) => {
  if (!notification.is_read) {
    markAsRead(notification.id)
  }
  // 通知类型处理逻辑
  if (notification.notification_type === 'reply' && notification.post) {
    router.push(`/forum/post/${notification.post}`)
  }
}

// 标记单条通知为已读
const markAsRead = async (notificationId: number) => {
  try {
    await forumApi.markNotificationAsRead(notificationId)
    
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
    await forumApi.markAllNotificationsAsRead()
    
    // 更新本地状态
    notifications.value.forEach(notification => {
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
.notifications-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.notifications-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.page-title {
  font-size: 24px;
  color: #333;
  margin: 0;
}

.btn-mark-all-read {
  padding: 8px 15px;
  background-color: #f1f1f1;
  border: none;
  border-radius: 4px;
  color: #333;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-mark-all-read:hover {
  background-color: #e0e0e0;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 50px 0;
}

.loading-spinner {
  border: 4px solid rgba(0, 0, 0, 0.1);
  border-radius: 50%;
  border-top: 4px solid #3498db;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin-bottom: 15px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.empty-notifications {
  text-align: center;
  padding: 50px 0;
  color: #666;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 20px;
  opacity: 0.3;
}

.empty-icon::before {
  content: "🔔";
}

.btn-to-forum {
  display: inline-block;
  margin-top: 20px;
  padding: 10px 20px;
  background-color: #3498db;
  color: white;
  text-decoration: none;
  border-radius: 4px;
  font-weight: 500;
}

.notifications-list {
  margin-bottom: 30px;
}

.notification-item {
  position: relative;
  display: flex;
  align-items: center;
  padding: 15px 20px;
  background-color: white;
  border-radius: 8px;
  margin-bottom: 15px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  cursor: pointer;
  transition: background-color 0.2s;
}

.notification-item:hover {
  background-color: #f5f5f5;
}

.notification-item.unread {
  background-color: #ebf7ff;
}

.notification-dot {
  width: 10px;
  height: 10px;
  background-color: #3498db;
  border-radius: 50%;
  margin-right: 15px;
}

.notification-content {
  flex: 1;
}

.notification-text {
  margin-bottom: 5px;
  color: #333;
  line-height: 1.4;
}

.notification-time {
  font-size: 14px;
  color: #888;
}

.btn-mark-read {
  padding: 6px 12px;
  background-color: transparent;
  border: 1px solid #ddd;
  border-radius: 4px;
  color: #666;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
  margin-left: 15px;
}

.btn-mark-read:hover {
  background-color: #f1f1f1;
  border-color: #3498db;
  color: #3498db;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: 30px;
  gap: 20px;
}

.btn-page {
  padding: 8px 15px;
  background-color: #f1f1f1;
  border: none;
  border-radius: 4px;
  color: #333;
  cursor: pointer;
}

.btn-page:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  color: #666;
}

@media (max-width: 768px) {
  .notification-item {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .notification-dot {
    position: absolute;
    top: 15px;
    left: 5px;
  }
  
  .notification-content {
    padding-left: 20px;
    width: 100%;
  }
  
  .btn-mark-read {
    margin-left: 20px;
    margin-top: 10px;
  }
}
</style> 