<template>
  <view class="container">
    <view class="header">
      <text class="title">论坛通知</text>
      <view v-if="notifications.length > 0" class="mark-all-btn" @click="markAllAsRead">
        <text>全部标为已读</text>
      </view>
    </view>

    <scroll-view class="notification-list" scroll-y @scrolltolower="loadMore">
      <view v-if="loading" class="loading">
        <view class="spinner"></view>
        <text>加载中...</text>
      </view>

      <view v-else-if="notifications.length === 0" class="empty">
        <text class="empty-icon">🔔</text>
        <text>暂无通知</text>
        <view class="to-forum" @click="goToForum">浏览论坛</view>
      </view>

      <view
        v-else
        v-for="notification in notifications"
        :key="notification.id"
        class="notification-item"
        :class="{ unread: !notification.is_read }"
        @click="viewNotification(notification)"
      >
        <view v-if="!notification.is_read" class="unread-dot"></view>
        <view class="notification-content">
          <rich-text class="notification-text" :nodes="sanitizeHtml(notification.content)"></rich-text>
          <text class="notification-time">{{ formatTime(notification.created_at) }}</text>
        </view>
        <view
          v-if="!notification.is_read"
          class="mark-read-btn"
          @click.stop="markAsRead(notification.id)"
        >
          <text>标为已读</text>
        </view>
      </view>

      <view v-if="notifications.length > 0" class="load-more">
        <text v-if="loadingMore" class="load-text">加载中...</text>
        <text v-else-if="hasMore" class="load-text" @click="loadMore">加载更多</text>
        <text v-else class="load-text no-more">没有更多了</text>
      </view>
    </scroll-view>
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import forumApi from '../../api/forum'
import { sanitizeHtml } from '../../utils/xss'

const notifications = ref([])
const loading = ref(false)
const loadingMore = ref(false)
const page = ref(1)
const pageSize = 10
const hasMore = ref(true)

onMounted(() => {
  loadNotifications(true)
})

const loadNotifications = async (reset = false) => {
  if (reset) {
    page.value = 1
    notifications.value = []
    hasMore.value = true
  }
  if (loading.value || loadingMore.value) return
  if (!hasMore.value && !reset) return

  if (reset) {
    loading.value = true
  } else {
    loadingMore.value = true
  }

  try {
    const result = await forumApi.getNotifications()
    const list = Array.isArray(result) ? result : (result.results || [])
    notifications.value = reset ? list : [...notifications.value, ...list]
    hasMore.value = list.length === pageSize
    page.value++
  } catch (error) {
    console.error('加载通知失败:', error)
    uni.showToast({ title: '加载通知失败', icon: 'none' })
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

const loadMore = () => {
  loadNotifications(false)
}

const viewNotification = (notification) => {
  if (!notification.is_read) {
    markAsRead(notification.id)
  }
  if (notification.notification_type === 'reply' && notification.post) {
    uni.navigateTo({ url: `/pages/post-detail/post-detail?id=${notification.post}` })
  }
}

const markAsRead = async (notificationId) => {
  try {
    await forumApi.markNotificationAsRead(notificationId)
    const notification = notifications.value.find(n => n.id === notificationId)
    if (notification) {
      notification.is_read = true
    }
  } catch (error) {
    console.error('标记通知已读失败:', error)
    uni.showToast({ title: '标记失败', icon: 'none' })
  }
}

const markAllAsRead = async () => {
  try {
    await forumApi.markAllNotificationsAsRead()
    notifications.value.forEach(notification => {
      notification.is_read = true
    })
    uni.showToast({ title: '已全部标为已读', icon: 'success' })
  } catch (error) {
    console.error('标记所有通知已读失败:', error)
    uni.showToast({ title: '操作失败', icon: 'none' })
  }
}

const goToForum = () => {
  uni.switchTab({ url: '/pages/forum/forum' })
}

const formatTime = (time) => {
  if (!time) return ''
  const date = new Date(time)
  const now = new Date()
  const diff = now - date
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return Math.floor(diff / 60000) + '分钟前'
  if (diff < 86400000) return Math.floor(diff / 3600000) + '小时前'
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}
</script>

<style scoped>
.container {
  min-height: 100vh;
  background-color: #f5f5f5;
  display: flex;
  flex-direction: column;
}

.header {
  background-color: #fff;
  padding: 30rpx;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
}

.mark-all-btn {
  padding: 10rpx 20rpx;
  font-size: 24rpx;
  color: #4361ee;
  background-color: #eef1ff;
  border-radius: 8rpx;
}

.notification-list {
  flex: 1;
  padding: 20rpx 30rpx;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 100rpx 0;
  gap: 16rpx;
  color: #999;
  font-size: 26rpx;
}

.spinner {
  width: 40rpx;
  height: 40rpx;
  border: 4rpx solid rgba(67, 97, 238, 0.3);
  border-radius: 50%;
  border-top-color: #4361ee;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty {
  text-align: center;
  padding: 100rpx 0;
  color: #999;
  font-size: 28rpx;
}

.empty-icon {
  display: block;
  font-size: 80rpx;
  margin-bottom: 20rpx;
  opacity: 0.5;
}

.to-forum {
  display: inline-block;
  margin-top: 30rpx;
  padding: 16rpx 40rpx;
  background-color: #4361ee;
  color: #fff;
  font-size: 28rpx;
  border-radius: 12rpx;
}

.notification-item {
  position: relative;
  display: flex;
  align-items: flex-start;
  background-color: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
  margin-bottom: 20rpx;
}

.notification-item.unread {
  background-color: #ebf7ff;
}

.unread-dot {
  width: 16rpx;
  height: 16rpx;
  background-color: #4361ee;
  border-radius: 50%;
  margin-right: 16rpx;
  margin-top: 8rpx;
  flex-shrink: 0;
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-text {
  font-size: 28rpx;
  color: #333;
  line-height: 1.5;
  margin-bottom: 10rpx;
}

.notification-time {
  font-size: 24rpx;
  color: #999;
}

.mark-read-btn {
  margin-left: 16rpx;
  padding: 10rpx 18rpx;
  font-size: 22rpx;
  color: #666;
  border: 1rpx solid #ddd;
  border-radius: 8rpx;
  flex-shrink: 0;
}

.load-more {
  text-align: center;
  padding: 30rpx 0;
}

.load-text {
  font-size: 26rpx;
  color: #999;
}

.load-text.no-more {
  color: #bbb;
}
</style>
