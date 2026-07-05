<template>
  <div class="notifications-page">
    <div class="page-header">
      <h1>通知中心</h1>
      <div class="header-actions">
        <button 
          class="btn-mark-all" 
          @click="markAllAsRead" 
          :disabled="loading || unreadCount === 0"
        >
          全部标为已读
        </button>
        <button 
          class="btn-delete-read" 
          @click="deleteAllRead" 
          :disabled="loading"
        >
          删除已读通知
        </button>
      </div>
    </div>
    
    <div class="notification-filters">
      <div class="filter-tabs">
        <button 
          v-for="tab in tabs" 
          :key="tab.type"
          @click="activeTab = tab.type" 
          :class="['tab-button', { active: activeTab === tab.type }]"
        >
          {{ tab.name }}
          <span v-if="tab.type === 'all' && totalCount > 0" class="count">({{ totalCount }})</span>
          <span v-else-if="tab.count > 0" class="count">({{ tab.count }})</span>
        </button>
      </div>
      
      <div class="filter-buttons">
        <button 
          class="btn-filter" 
          :class="{ active: filterUnread }"
          @click="filterUnread = !filterUnread"
        >
          <span class="unread-dot"></span> 只看未读
        </button>
      </div>
    </div>
    
    <div class="notifications-container">
      <div v-if="loading" class="loading-state">
        <div class="loading-spinner"></div>
        <p>加载中...</p>
      </div>
      
      <div v-else-if="filteredNotifications.length === 0" class="empty-state">
        <div class="empty-icon"></div>
        <p>暂无{{ getActiveTabName() }}通知</p>
      </div>
      
      <div v-else class="notifications-list">
        <div 
          v-for="notification in filteredNotifications" 
          :key="notification.id" 
          :class="['notification-card', { 'unread': !notification.is_read }]"
        >
          <div class="notification-header">
            <div class="notification-avatar">
              <div v-if="notification.sender" 
                   class="avatar-img" 
                   :style="getSenderAvatarStyle(notification.sender)">
              </div>
              <div v-else class="system-icon"></div>
            </div>
            <div class="notification-info">
              <h3 class="notification-title">{{ notification.title }}</h3>
              <div class="notification-meta">
                <span class="notification-type">{{ getNotificationType(notification.notification_type) }}</span>
                <span class="notification-time">{{ formatTime(notification.created_at) }}</span>
              </div>
            </div>
            <div class="notification-actions">
              <button 
                v-if="!notification.is_read" 
                class="btn-mark-read" 
                title="标记为已读"
                @click.stop="markAsRead(notification.id)"
              >
                <span class="read-icon"></span>
              </button>
              <button 
                class="btn-delete" 
                title="删除通知"
                @click.stop="deleteNotification(notification.id)"
              >
                <span class="delete-icon"></span>
              </button>
            </div>
          </div>
          
          <div class="notification-content">
            {{ notification.content }}
          </div>
          
          <div class="notification-footer" v-if="notification.url">
            <a :href="notification.url" class="btn-link" target="_blank" rel="noopener noreferrer">
              <span class="link-icon"></span> 查看详情
            </a>
          </div>
        </div>
        
        <div v-if="hasMoreNotifications && !loading" class="load-more">
          <button @click="loadMoreNotifications" class="btn-load-more">
            加载更多
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { userApi } from '../api/user'
import { useToast } from '../composables/useToast'

interface Tab {
  type: string
  name: string
  count: number
}

// 状态数据
const loading = ref(false)
const notifications = ref<any[]>([])
const page = ref(1)
const perPage = ref(10)
const activeTab = ref('all')
const filterUnread = ref(false)
const hasMoreNotifications = ref(false)
const totalCount = ref(0)
const unreadCount = ref(0)
const { showToast } = useToast()

// 通知类型选项卡
const tabs = ref<Tab[]>([
  { type: 'all', name: '全部', count: 0 },
  { type: 'system', name: '系统通知', count: 0 },
  { type: 'interaction', name: '互动通知', count: 0 },
  { type: 'message', name: '私信', count: 0 },
  { type: 'activity', name: '活动通知', count: 0 }
])

// 获取当前选项卡名称
const getActiveTabName = () => {
  const tab = tabs.value.find(t => t.type === activeTab.value)
  return tab ? tab.name : '全部'
}

// 获取通知类型名称
const getNotificationType = (type: string) => {
  const map: Record<string, string> = {
    'system': '系统通知',
    'interaction': '互动通知',
    'message': '私信',
    'activity': '活动通知'
  }
  return map[type] || '通知'
}

// 过滤后的通知列表
const filteredNotifications = computed(() => {
  let filtered = notifications.value

  // 按类型过滤
  if (activeTab.value !== 'all') {
    filtered = filtered.filter(item => item.notification_type === activeTab.value)
  }
  
  // 过滤未读通知
  if (filterUnread.value) {
    filtered = filtered.filter(item => !item.is_read)
  }
  
  return filtered
})

// 获取通知列表
const fetchNotifications = async (reset = true) => {
  loading.value = true
  try {
    // 如果是重置，则重置页码
    if (reset) {
      page.value = 1
      notifications.value = []
    }

    // 构建请求参数
    const params: Record<string, any> = {
      page: page.value,
      page_size: perPage.value
    }

    // 如果选择了只看未读
    if (filterUnread.value) {
      params.unread = true
    }

    // 如果选择了特定类型
    if (activeTab.value !== 'all') {
      params.type = activeTab.value
    }

    const response = await userApi.getNotifications(params)

    // 更新数据
    if (reset) {
      notifications.value = response.results || response
    } else {
      notifications.value = [...notifications.value, ...(response.results || response)]
    }

    // 更新分页信息
    if (response.count !== undefined) {
      totalCount.value = response.count
      hasMoreNotifications.value = notifications.value.length < response.count
    } else {
      hasMoreNotifications.value = false
    }

    // 获取各类型的数量
    fetchTypeCounts()

    // 获取未读数量
    fetchUnreadCount()

  } catch (error) {
    console.error('获取通知失败:', error)
    showToast('获取通知失败', 'error')
  } finally {
    loading.value = false
  }
}

// 加载更多通知
const loadMoreNotifications = () => {
  if (hasMoreNotifications.value && !loading.value) {
    page.value++
    fetchNotifications(false)
  }
}

// 获取各类型通知数量
const fetchTypeCounts = async () => {
  try {
    const response = await userApi.getNotificationTypeCounts()

    // 更新各类型计数
    tabs.value = tabs.value.map(tab => {
      if (tab.type === 'all') {
        return { ...tab, count: totalCount.value }
      } else {
        return { ...tab, count: response[tab.type] || 0 }
      }
    })
  } catch (error) {
    console.error('获取通知类型计数失败:', error)
  }
}

// 获取未读通知数
const fetchUnreadCount = async () => {
  try {
    const response = await userApi.getUnreadNotificationsCount()
    unreadCount.value = response.unread_count
  } catch (error) {
    console.error('获取未读数失败:', error)
  }
}

// 标记单个通知为已读
const markAsRead = async (id: number) => {
  try {
    await userApi.markNotificationAsRead(id)

    // 更新通知状态
    notifications.value = notifications.value.map(n =>
      n.id === id ? { ...n, is_read: true } : n
    )

    // 减少未读数
    if (unreadCount.value > 0) {
      unreadCount.value--
    }

    showToast('通知已标记为已读', 'success')
  } catch (error) {
    console.error('标记已读失败:', error)
    showToast('操作失败，请稍后再试', 'error')
  }
}

// 标记所有通知为已读
const markAllAsRead = async () => {
  try {
    loading.value = true

    await userApi.markAllNotificationsAsRead()

    // 更新所有通知状态
    notifications.value = notifications.value.map(n => ({
      ...n,
      is_read: true
    }))

    unreadCount.value = 0
    showToast('所有通知已标记为已读', 'success')
  } catch (error) {
    console.error('标记已读失败:', error)
    showToast('操作失败，请稍后再试', 'error')
  } finally {
    loading.value = false
  }
}

// 删除单个通知
const deleteNotification = async (id: number) => {
  if (!confirm('确定要删除这条通知吗？')) {
    return
  }

  try {
    await userApi.deleteNotification(id)

    // 先判断是否是未读通知，再从列表中移除
    const notification = notifications.value.find(n => n.id === id)
    if (notification && !notification.is_read && unreadCount.value > 0) {
      unreadCount.value--
    }

    // 从列表中移除
    notifications.value = notifications.value.filter(n => n.id !== id)
    totalCount.value--

    showToast('通知已删除', 'success')
  } catch (error) {
    console.error('删除通知失败:', error)
    showToast('操作失败，请稍后再试', 'error')
  }
}

// 删除所有已读通知
const deleteAllRead = async () => {
  if (!confirm('确定要删除所有已读通知吗？')) {
    return
  }

  try {
    loading.value = true

    const response = await userApi.deleteAllReadNotifications()

    // 刷新列表
    fetchNotifications()
    const match = response.message.match(/\d+/)
    showToast(`已删除${match ? match[0] : 0}条已读通知`, 'success')
  } catch (error) {
    console.error('删除已读通知失败:', error)
    showToast('操作失败，请稍后再试', 'error')
  } finally {
    loading.value = false
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

// 监听过滤条件变化，刷新数据
watch([activeTab, filterUnread], () => {
  fetchNotifications()
})

// 组件挂载时加载数据
onMounted(() => {
  fetchNotifications()
})
</script>

<style scoped>
.notifications-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 2rem 1rem;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.page-header h1 {
  font-size: 1.8rem;
  font-weight: 700;
  color: #333;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 1rem;
}

.btn-mark-all, .btn-delete-read {
  padding: 0.6rem 1rem;
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
  border: none;
}

.btn-mark-all {
  background-color: #4361ee;
  color: white;
}

.btn-mark-all:hover:not(:disabled) {
  background-color: #3a56d4;
}

.btn-delete-read {
  background-color: #f44336;
  color: white;
}

.btn-delete-read:hover:not(:disabled) {
  background-color: #d32f2f;
}

.btn-mark-all:disabled, .btn-delete-read:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.notification-filters {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  background-color: white;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  padding: 0.5rem 1rem;
}

.filter-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
}

.tab-button {
  background: none;
  border: none;
  padding: 0.7rem 1rem;
  color: #666;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.3s;
  display: flex;
  align-items: center;
}

.tab-button:hover {
  background-color: rgba(67, 97, 238, 0.05);
}

.tab-button.active {
  color: #4361ee;
  background-color: rgba(67, 97, 238, 0.1);
  font-weight: 600;
}

.count {
  margin-left: 5px;
  font-size: 0.8rem;
  opacity: 0.7;
}

.filter-buttons {
  display: flex;
  gap: 1rem;
}

.btn-filter {
  display: flex;
  align-items: center;
  background: none;
  border: 1px solid #eee;
  padding: 0.5rem 0.8rem;
  border-radius: 6px;
  font-size: 0.85rem;
  color: #666;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-filter:hover {
  border-color: #4361ee;
  color: #4361ee;
}

.btn-filter.active {
  background-color: rgba(67, 97, 238, 0.1);
  color: #4361ee;
  border-color: #4361ee;
}

.unread-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #4361ee;
  margin-right: 6px;
}

.loading-state, .empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 0;
  color: #888;
  background-color: white;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(67, 97, 238, 0.2);
  border-radius: 50%;
  border-top-color: #4361ee;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-icon {
  width: 80px;
  height: 80px;
  margin-bottom: 1rem;
  opacity: 0.3;
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%23666"><path d="M18 17v-7c0-2.5-1.62-4.64-4-5.47V4c0-.83-.67-1.5-1.5-1.5S11 3.17 11 4v.48C8.62 5.36 7 7.5 7 10v7l-2 2v1h16v-1l-3-2zm-4 5c1.1 0 2-.9 2-2h-4c0 1.1.9 2 2 2z"/></svg>');
  background-size: contain;
  background-position: center;
  background-repeat: no-repeat;
}

.notifications-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.notification-card {
  background-color: white;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  overflow: hidden;
  transition: all 0.3s;
}

.notification-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.1);
}

.notification-card.unread {
  border-left: 4px solid #4361ee;
}

.notification-header {
  display: flex;
  padding: 1rem;
  border-bottom: 1px solid #f0f0f0;
  position: relative;
}

.notification-avatar {
  margin-right: 1rem;
}

.avatar-img, .system-icon {
  width: 50px;
  height: 50px;
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

.notification-info {
  flex: 1;
  min-width: 0;
}

.notification-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #333;
  margin-top: 0;
  margin-bottom: 0.5rem;
}

.notification-meta {
  display: flex;
  gap: 1rem;
  font-size: 0.85rem;
  color: #888;
}

.notification-type {
  color: #4361ee;
}

.notification-actions {
  display: flex;
  gap: 0.5rem;
}

.btn-mark-read, .btn-delete {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background-color: #f5f5f5;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
}

.btn-mark-read:hover {
  background-color: #e3f2fd;
}

.btn-delete:hover {
  background-color: #ffebee;
}

.read-icon, .delete-icon {
  width: 20px;
  height: 20px;
  background-position: center;
  background-repeat: no-repeat;
  background-size: contain;
}

.read-icon {
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%232196f3"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>');
}

.delete-icon {
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%23f44336"><path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/></svg>');
}

.notification-content {
  padding: 1.2rem;
  line-height: 1.6;
  color: #444;
}

.notification-footer {
  padding: 0.8rem 1.2rem;
  border-top: 1px solid #f0f0f0;
}

.btn-link {
  display: inline-flex;
  align-items: center;
  color: #4361ee;
  text-decoration: none;
  font-weight: 500;
  font-size: 0.9rem;
  transition: all 0.3s;
}

.btn-link:hover {
  text-decoration: underline;
}

.link-icon {
  width: 18px;
  height: 18px;
  margin-right: 6px;
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%234361ee"><path d="M19 19H5V5h7V3H5c-1.11 0-2 .9-2 2v14c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2v-7h-2v7zM14 3v2h3.59l-9.83 9.83 1.41 1.41L19 6.41V10h2V3h-7z"/></svg>');
  background-size: contain;
  background-position: center;
  background-repeat: no-repeat;
}

.load-more {
  text-align: center;
  margin-top: 1.5rem;
}

.btn-load-more {
  padding: 0.7rem 2rem;
  background-color: white;
  color: #4361ee;
  border: 1px solid #4361ee;
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-load-more:hover {
  background-color: rgba(67, 97, 238, 0.05);
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  
  .notification-filters {
    flex-direction: column;
    gap: 1rem;
    align-items: flex-start;
  }
  
  .filter-tabs {
    width: 100%;
    overflow-x: auto;
    padding-bottom: 0.5rem;
  }
  
  .tab-button {
    white-space: nowrap;
  }
}
</style> 