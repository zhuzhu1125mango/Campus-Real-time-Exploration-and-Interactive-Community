<template>
  <div class="notification-dropdown">
    <button 
      class="notification-icon" 
      @click="toggleDropdown" 
      :class="{ 'has-unread': unreadCount > 0 }"
    >
      <span class="bell-icon"></span>
      <span v-if="unreadCount > 0" class="badge">{{ unreadCount > 99 ? '99+' : unreadCount }}</span>
    </button>
    
    <div class="dropdown-content" v-show="isOpen" ref="dropdownContent">
      <div class="dropdown-header">
        <h3>通知消息</h3>
        <button class="mark-all-read" @click="markAllAsRead" :disabled="loading || unreadCount === 0">
          全部已读
        </button>
      </div>
      
      <div class="notification-tabs">
        <button 
          v-for="tab in tabs" 
          :key="tab.type"
          @click="activeTab = tab.type" 
          :class="['tab-button', { active: activeTab === tab.type }]"
        >
          {{ tab.name }}
        </button>
      </div>
      
      <div class="notifications-container">
        <div v-if="loading" class="loading-container">
          <div class="loading-spinner"></div>
          <p>加载中...</p>
        </div>
        
        <div v-else-if="filteredNotifications.length === 0" class="empty-notification">
          <div class="empty-icon"></div>
          <p>暂无{{ getActiveTabName() }}通知</p>
        </div>
        
        <div v-else class="notification-list">
          <div 
            v-for="notification in filteredNotifications" 
            :key="notification.id" 
            :class="['notification-item', { 'unread': !notification.is_read }]"
            @click="handleNotificationClick(notification)"
          >
            <div class="notification-avatar">
              <div v-if="notification.sender" 
                class="avatar-img" 
                :style="getSenderAvatarStyle(notification.sender)">
              </div>
              <div v-else class="system-icon"></div>
            </div>
            <div class="notification-content">
              <div class="notification-title">{{ notification.title }}</div>
              <div class="notification-text">{{ notification.content }}</div>
              <div class="notification-time">{{ formatTime(notification.created_at) }}</div>
            </div>
            <div class="notification-status" v-if="!notification.is_read"></div>
          </div>
        </div>
      </div>
      
      <div class="dropdown-footer">
        <router-link to="/notifications" class="view-all" @click="isOpen = false">
          查看全部
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from '../composables/useToast'
import { userApi } from '../api/user'

const { showToast } = useToast()
const router = useRouter()

// 状态数据
const isOpen = ref(false)
const loading = ref(false)
const unreadCount = ref(0)
const notifications = ref<any[]>([])
const activeTab = ref('all')
const dropdownContent = ref<HTMLElement | null>(null)

// 通知类型选项卡
const tabs = [
  { type: 'all', name: '全部' },
  { type: 'system', name: '系统' },
  { type: 'interaction', name: '互动' },
  { type: 'message', name: '私信' }
]

// 获取当前选项卡名称
const getActiveTabName = () => {
  const tab = tabs.find(t => t.type === activeTab.value)
  return tab ? tab.name : '全部'
}

// 过滤后的通知列表
const filteredNotifications = computed(() => {
  if (activeTab.value === 'all') {
    return notifications.value
  }
  return notifications.value.filter(item => item.notification_type === activeTab.value)
})

// 切换下拉菜单
const toggleDropdown = () => {
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    fetchNotifications()
  }
}

// 点击外部关闭下拉菜单
const handleClickOutside = (event: MouseEvent) => {
  if (
    isOpen.value && 
    dropdownContent.value && 
    !dropdownContent.value.contains(event.target as Node) &&
    !(event.target as Element).closest('.notification-icon')
  ) {
    isOpen.value = false
  }
}

// 获取通知列表
const fetchNotifications = async () => {
  loading.value = true
  try {
    // 使用userApi获取通知
    const response = await userApi.getNotifications()
    notifications.value = response.data
  } catch (error) {
    console.error('获取通知失败:', error)
    showToast('获取通知失败', 'error')
  } finally {
    loading.value = false
  }
}

// 获取未读通知数
const fetchUnreadCount = async () => {
  try {
    // 使用userApi获取未读通知数
    const response = await userApi.getUnreadNotificationsCount()
    unreadCount.value = response.data.unread_count
  } catch (error) {
    console.error('获取未读数失败:', error)
  }
}

// 标记所有通知为已读
const markAllAsRead = async () => {
  try {
    loading.value = true
    // 使用userApi标记所有为已读
    await userApi.markAllNotificationsAsRead()
    
    // 更新列表中通知状态
    notifications.value = notifications.value.map(n => ({
      ...n,
      is_read: true
    }))
    
    unreadCount.value = 0
    showToast('已将所有通知标记为已读', 'success')
  } catch (error) {
    console.error('标记已读失败:', error)
    showToast('操作失败，请稍后再试', 'error')
  } finally {
    loading.value = false
  }
}

// 点击通知项
const handleNotificationClick = async (notification: any) => {
  // 如果未读，标记为已读
  if (!notification.is_read) {
    try {
      // 使用userApi标记单个为已读
      await userApi.markNotificationAsRead(notification.id)
      
      // 更新当前通知状态
      notifications.value = notifications.value.map(n => 
        n.id === notification.id ? { ...n, is_read: true } : n
      )
      
      // 减少未读数
      if (unreadCount.value > 0) {
        unreadCount.value--
      }
    } catch (error) {
      console.error('标记已读失败:', error)
    }
  }
  
  // 处理跳转
  if (notification.url) {
    isOpen.value = false
    router.push(notification.url)
  }
}

// 获取发送者头像样式
const getSenderAvatarStyle = (sender: any) => {
  if (sender?.avatar) {
    return { backgroundImage: `url(${sender.avatar})` }
  }
  return { backgroundColor: '#4361ee' }
}

// 格式化时间
const formatTime = (dateString: string) => {
  const now = new Date()
  const date = new Date(dateString)
  const diffMs = now.getTime() - date.getTime()
  const diffSec = Math.floor(diffMs / 1000)
  const diffMin = Math.floor(diffSec / 60)
  const diffHour = Math.floor(diffMin / 60)
  const diffDay = Math.floor(diffHour / 24)
  
  if (diffSec < 60) {
    return '刚刚'
  } else if (diffMin < 60) {
    return `${diffMin}分钟前`
  } else if (diffHour < 24) {
    return `${diffHour}小时前`
  } else if (diffDay < 7) {
    return `${diffDay}天前`
  } else {
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
  }
}

// 定期刷新未读通知数
let intervalId: number

// 生命周期钩子
onMounted(() => {
  document.addEventListener('mousedown', handleClickOutside)
  fetchUnreadCount()
  
  // 定期检查未读通知数（每分钟）
  intervalId = window.setInterval(fetchUnreadCount, 60000)
})

onUnmounted(() => {
  document.removeEventListener('mousedown', handleClickOutside)
  clearInterval(intervalId)
})

// 监听activeTab变化，切换时重新获取通知
watch(activeTab, () => {
  if (isOpen.value) {
    fetchNotifications()
  }
})
</script>

<style scoped>
.notification-dropdown {
  position: relative;
  display: inline-block;
}

.notification-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: none;
  background-color: transparent;
  position: relative;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
}

.notification-icon:hover {
  background-color: rgba(67, 97, 238, 0.1);
}

.bell-icon {
  width: 24px;
  height: 24px;
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%23666"><path d="M12 22c1.1 0 2-.9 2-2h-4c0 1.1.9 2 2 2zm6-6v-5c0-3.07-1.63-5.64-4.5-6.32V4c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5 1.5v.68C7.64 5.36 6 7.92 6 11v5l-2 2v1h16v-1l-2-2zm-2 1H8v-6c0-2.48 1.51-4.5 4-4.5s4 2.02 4 4.5v6z"/></svg>');
  background-size: contain;
  background-position: center;
  background-repeat: no-repeat;
}

.has-unread .bell-icon {
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%234361ee"><path d="M12 22c1.1 0 2-.9 2-2h-4c0 1.1.9 2 2 2zm6-6v-5c0-3.07-1.63-5.64-4.5-6.32V4c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5 1.5v.68C7.64 5.36 6 7.92 6 11v5l-2 2v1h16v-1l-2-2zm-2 1H8v-6c0-2.48 1.51-4.5 4-4.5s4 2.02 4 4.5v6z"/></svg>');
}

.badge {
  position: absolute;
  top: -2px;
  right: -2px;
  min-width: 18px;
  height: 18px;
  border-radius: 9px;
  background-color: #f44336;
  color: white;
  font-size: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 4px;
}

.dropdown-content {
  position: absolute;
  right: 0;
  top: 50px;
  width: 350px;
  background-color: white;
  border-radius: 12px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.dropdown-content::before {
  content: '';
  position: absolute;
  top: -6px;
  right: 15px;
  width: 12px;
  height: 12px;
  background-color: white;
  transform: rotate(45deg);
  border-top-left-radius: 2px;
  box-shadow: -1px -1px 5px rgba(0, 0, 0, 0.05);
}

.dropdown-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  border-bottom: 1px solid #f0f0f0;
}

.dropdown-header h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: #333;
}

.mark-all-read {
  font-size: 0.8rem;
  color: #4361ee;
  background: none;
  border: none;
  cursor: pointer;
  padding: 5px 10px;
  border-radius: 4px;
  transition: all 0.3s;
}

.mark-all-read:hover:not(:disabled) {
  background-color: rgba(67, 97, 238, 0.1);
}

.mark-all-read:disabled {
  color: #ccc;
  cursor: default;
}

.notification-tabs {
  display: flex;
  border-bottom: 1px solid #f0f0f0;
}

.tab-button {
  flex: 1;
  padding: 10px;
  background: none;
  border: none;
  font-size: 0.9rem;
  color: #666;
  cursor: pointer;
  transition: all 0.3s;
}

.tab-button:hover {
  background-color: #f9f9f9;
}

.tab-button.active {
  color: #4361ee;
  font-weight: 500;
  box-shadow: inset 0 -2px 0 #4361ee;
}

.notifications-container {
  max-height: 400px;
  overflow-y: auto;
  padding: 0;
  flex: 1;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 30px;
  color: #888;
}

.loading-spinner {
  width: 30px;
  height: 30px;
  border: 3px solid rgba(67, 97, 238, 0.2);
  border-radius: 50%;
  border-top-color: #4361ee;
  animation: spin 1s linear infinite;
  margin-bottom: 10px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-notification {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 30px;
  color: #888;
}

.empty-icon {
  width: 50px;
  height: 50px;
  margin-bottom: 10px;
  opacity: 0.3;
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%23666"><path d="M12 22c1.1 0 2-.9 2-2h-4c0 1.1.9 2 2 2zm6-6v-5c0-3.07-1.63-5.64-4.5-6.32V4c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5 1.5v.68C7.64 5.36 6 7.92 6 11v5l-2 2v1h16v-1l-2-2z"/></svg>');
  background-size: contain;
  background-position: center;
  background-repeat: no-repeat;
}

.notification-list {
  padding: 10px 0;
}

.notification-item {
  display: flex;
  padding: 12px 15px;
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
}

.notification-item:hover {
  background-color: #f9fafc;
}

.notification-item.unread {
  background-color: rgba(67, 97, 238, 0.05);
}

.notification-item.unread:hover {
  background-color: rgba(67, 97, 238, 0.1);
}

.notification-avatar {
  margin-right: 12px;
  flex-shrink: 0;
}

.avatar-img, .system-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: #f0f0f0;
  background-size: cover;
  background-position: center;
}

.system-icon {
  background-color: #4361ee;
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white"><path d="M2.5 19h19v2h-19v-2zm19.57-9.36c-.21-.8-1.04-1.28-1.84-1.06L14.92 10 8.46 3.92l-1.21.84 5.13 7.49-5.88 1.56c-.8.21-1.28 1.04-1.06 1.84.22.8 1.04 1.28 1.85 1.07L19.23 13c.8-.23 1.28-1.05 1.07-1.85z"/></svg>');
  background-size: 50%;
  background-repeat: no-repeat;
  background-position: center;
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-title {
  font-weight: 500;
  margin-bottom: 2px;
  color: #333;
  font-size: 0.9rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.notification-text {
  color: #666;
  font-size: 0.85rem;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  line-clamp: 2;
  overflow: hidden;
}

.notification-time {
  font-size: 0.75rem;
  color: #999;
  margin-top: 3px;
}

.notification-status {
  position: absolute;
  top: 18px;
  right: 15px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #4361ee;
}

.dropdown-footer {
  padding: 12px;
  text-align: center;
  border-top: 1px solid #f0f0f0;
}

.view-all {
  display: block;
  padding: 8px;
  color: #4361ee;
  text-decoration: none;
  border-radius: 4px;
  transition: all 0.3s;
  font-size: 0.9rem;
}

.view-all:hover {
  background-color: rgba(67, 97, 238, 0.1);
  text-decoration: none;
}

@media (max-width: 480px) {
  .dropdown-content {
    width: 300px;
    right: -20px;
  }
}
</style> 