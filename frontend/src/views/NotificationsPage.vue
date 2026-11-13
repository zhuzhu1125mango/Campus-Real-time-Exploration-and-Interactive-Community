<template>
  <div class="notifications-page container-medium page-padding">
    <SectionHeader
      title="通知中心"
      subtitle="管理系统通知与互动消息"
      icon="i-ep-message"
    />

    <GlassCard :hover="false" class="filters-card" padding="md">
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
            class="btn btn-secondary"
            :class="{ active: filterUnread }"
            @click="filterUnread = !filterUnread"
          >
            <span class="i-ep-bell" />
            只看未读
          </button>
        </div>
      </div>
    </GlassCard>

    <GlassCard :hover="false" class="notifications-card">
      <div class="notifications-toolbar">
        <h2 class="card-title">通知列表</h2>
        <div class="toolbar-actions">
          <button
            class="btn btn-primary"
            @click="markAllAsRead"
            :disabled="loading || unreadCount === 0"
          >
            <span class="i-ep-check" />
            全部标为已读
          </button>
          <button
            class="btn btn-secondary"
            @click="deleteAllRead"
            :disabled="loading"
          >
            <span class="i-ep-delete" />
            删除已读通知
          </button>
        </div>
      </div>

      <div v-if="loading" class="loading-state">
        <div class="loading-spinner" />
        <p>加载中...</p>
      </div>

      <div v-else-if="filteredNotifications.length === 0" class="empty-state">
        <div class="empty-icon">
          <span class="i-ep-message" />
        </div>
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
              <div
                v-if="notification.sender"
                class="avatar-img"
                :style="getSenderAvatarStyle(notification.sender)"
              />
              <div v-else class="system-icon">
                <span class="i-ep-set-up" />
              </div>
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
                class="action-btn"
                title="标记为已读"
                @click.stop="markAsRead(notification.id)"
              >
                <span class="i-ep-check action-icon" />
              </button>
              <button
                class="action-btn"
                title="删除通知"
                @click.stop="deleteNotification(notification.id)"
              >
                <span class="i-ep-delete action-icon" />
              </button>
            </div>
          </div>

          <div class="notification-content">
            {{ notification.content }}
          </div>

          <div class="notification-footer" v-if="notification.url">
            <a :href="notification.url" class="detail-link" target="_blank" rel="noopener noreferrer">
              <span class="i-ep-right" />
              查看详情
            </a>
          </div>
        </div>

        <div v-if="hasMoreNotifications && !loading" class="load-more">
          <button @click="loadMoreNotifications" class="btn btn-secondary">
            <span class="i-ep-bottom" />
            加载更多
          </button>
        </div>
      </div>
    </GlassCard>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { userApi } from '../api/user'
import { useToast } from '../composables/useToast'
import type { Notification, User } from '../types/user'
import GlassCard from '../components/GlassCard.vue'
import SectionHeader from '../components/SectionHeader.vue'

interface Tab {
  type: string
  name: string
  count: number
}

// 状态数据
const loading = ref(false)
const notifications = ref<Notification[]>([])
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
      notifications.value = response.results
    } else {
      notifications.value = [...notifications.value, ...response.results]
    }

    // 更新分页信息
    totalCount.value = response.count
    hasMoreNotifications.value = notifications.value.length < response.count

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
    unreadCount.value = response.unread_count ?? 0
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
const getSenderAvatarStyle = (sender: User) => {
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
.filters-card {
  margin-bottom: var(--space-5);
}

.notification-filters {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-4);
}

.filter-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.tab-button {
  background: transparent;
  border: none;
  padding: var(--space-2) var(--space-4);
  color: var(--text-secondary);
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  border-radius: var(--radius-md);
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
}

.tab-button:hover {
  color: var(--text-primary);
  background: var(--bg-tertiary);
}

.tab-button.active {
  color: var(--primary-600);
  background: var(--primary-50);
  font-weight: 600;
}

.dark .tab-button.active {
  color: var(--primary-400);
  background: var(--bg-tertiary);
}

.count {
  margin-left: var(--space-1);
  font-size: 0.8rem;
  opacity: 0.7;
}

.filter-buttons {
  display: flex;
  gap: var(--space-3);
  flex-shrink: 0;
}

.notifications-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-5);
  gap: var(--space-4);
}

.card-title {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text-primary);
}

.toolbar-actions {
  display: flex;
  gap: var(--space-3);
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

.notifications-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.notification-card {
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
  overflow: hidden;
  transition: all 0.25s ease;
}

.notification-card:hover {
  border-color: var(--primary-600);
  box-shadow: var(--shadow-md);
}

.notification-card.unread {
  border-left: 4px solid var(--primary-600);
}

.notification-header {
  display: flex;
  padding: var(--space-4);
  border-bottom: 1px solid var(--border-color-light);
  position: relative;
  gap: var(--space-3);
}

.notification-avatar {
  flex-shrink: 0;
}

.avatar-img,
.system-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background-color: var(--bg-tertiary);
  background-size: cover;
  background-position: center;
}

.system-icon {
  background-color: var(--primary-600);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
}

.notification-info {
  flex: 1;
  min-width: 0;
}

.notification-title {
  font-size: 1.05rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 var(--space-2);
}

.notification-meta {
  display: flex;
  gap: var(--space-3);
  font-size: 0.85rem;
  color: var(--text-tertiary);
}

.notification-type {
  color: var(--primary-600);
}

.notification-actions {
  display: flex;
  gap: var(--space-2);
  flex-shrink: 0;
}

.action-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background-color: var(--bg-tertiary);
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.action-btn:hover {
  background-color: var(--border-color);
  color: var(--text-primary);
}

.action-icon {
  font-size: 1.1rem;
}

.notification-content {
  padding: var(--space-4);
  line-height: 1.6;
  color: var(--text-secondary);
}

.notification-footer {
  padding: var(--space-3) var(--space-4);
  border-top: 1px solid var(--border-color-light);
}

.detail-link {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  color: var(--primary-600);
  text-decoration: none;
  font-weight: 500;
  font-size: 0.9rem;
  transition: all 0.2s;
}

.detail-link:hover {
  color: var(--primary-500);
}

.load-more {
  text-align: center;
  margin-top: var(--space-4);
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

.btn-secondary.active {
  color: var(--primary-600);
  background: var(--primary-50);
}

.dark .btn-secondary.active {
  color: var(--primary-400);
  background: var(--bg-tertiary);
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .notification-filters {
    flex-direction: column;
    gap: var(--space-3);
    align-items: flex-start;
  }

  .filter-tabs {
    width: 100%;
    overflow-x: auto;
    padding-bottom: var(--space-2);
  }

  .tab-button {
    white-space: nowrap;
  }

  .notifications-toolbar {
    flex-direction: column;
    align-items: flex-start;
  }

  .toolbar-actions {
    width: 100%;
    flex-wrap: wrap;
  }

  .notification-header {
    flex-wrap: wrap;
  }

  .notification-actions {
    width: 100%;
    justify-content: flex-end;
    margin-top: var(--space-2);
  }
}
</style>
