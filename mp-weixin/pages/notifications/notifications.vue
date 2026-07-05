<template>
  <view class="container">
    <view class="header">
      <text class="title">通知</text>
    </view>

    <!-- 通知列表 -->
    <scroll-view class="notification-list" scroll-y>
      <view class="loading" v-if="loading">
        <text>加载中...</text>
      </view>
      <template v-else>
      <view
        class="notification-item"
        :class="{ unread: !notification.is_read }"
        v-for="notification in notifications"
        :key="notification.id"
        @click="handleNotification(notification)"
      >
        <view class="notification-icon">
          <text>{{ getNotificationIcon(notification.notification_type || notification.type) }}</text>
        </view>
        <view class="notification-content">
          <view class="notification-header">
            <text class="notification-title">{{ notification.title }}</text>
            <text class="notification-time">{{ formatTime(notification.created_at) }}</text>
          </view>
          <text class="notification-text">{{ notification.content || notification.message }}</text>
        </view>
        <view class="unread-dot" v-if="!notification.is_read"></view>
      </view>

      <view class="empty" v-if="!loading && notifications.length === 0">
        <text>暂无通知</text>
      </view>
      </template>
    </scroll-view>
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import notificationApi from '../../api/notification'

const notifications = ref([])
const loading = ref(false)

onMounted(() => {
  loadNotifications()
})

const loadNotifications = async () => {
  loading.value = true
  try {
    const result = await notificationApi.getNotifications()
    if (result && result.results) {
      notifications.value = result.results
    } else if (Array.isArray(result)) {
      notifications.value = result
    } else {
      notifications.value = []
    }
  } catch (error) {
    console.error('加载通知失败:', error)
    notifications.value = []
  } finally {
    loading.value = false
  }
}

const getNotificationIcon = (type) => {
  const icons = {
    system: '🔔',
    forum: '💬',
    chat: '✉️',
    friend: '👥',
    activity: '📅'
  }
  return icons[type] || '🔔'
}

const handleNotification = async (notification) => {
  if (!notification.is_read) {
    try {
      await notificationApi.markAsRead(notification.id)
      notification.is_read = true
    } catch (error) {
      console.error('标记已读失败:', error)
    }
  }

  if (notification.target_id) {
    switch (notification.notification_type || notification.type) {
      case 'forum':
      case 'comment':
        uni.navigateTo({ url: `/pages/post-detail/post-detail?id=${notification.target_id}` })
        break
      case 'chat':
      case 'message':
        uni.navigateTo({ url: `/pages/chat-detail/chat-detail?userId=${notification.target_id}` })
        break
      default:
        break
    }
  }
}

const formatTime = (time) => {
  if (!time) return ''
  const date = new Date(time)
  const now = new Date()
  const diff = now - date
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return Math.floor(diff / 60000) + '分钟前'
  if (diff < 86400000) return Math.floor(diff / 3600000) + '小时前'
  return Math.floor(diff / 86400000) + '天前'
}
</script>

<style scoped>
.container {
  min-height: 100vh;
  background-color: #f5f5f5;
}

.header {
  background-color: #fff;
  padding: 30rpx;
  text-align: center;
}

.title {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
}

.notification-list {
  height: calc(100vh - 100rpx);
  padding: 20rpx 30rpx;
}

.loading {
  text-align: center;
  padding: 100rpx;
  color: #999;
}

.notification-item {
  background-color: #fff;
  border-radius: 16rpx;
  padding: 30rpx;
  margin-bottom: 20rpx;
  display: flex;
  align-items: flex-start;
  position: relative;
}

.notification-item.unread {
  background-color: #f0f9f0;
}

.notification-icon {
  width: 80rpx;
  height: 80rpx;
  background-color: #f5f5f5;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 20rpx;
  font-size: 40rpx;
}

.notification-content {
  flex: 1;
}

.notification-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10rpx;
}

.notification-title {
  font-size: 28rpx;
  font-weight: 500;
  color: #333;
}

.notification-time {
  font-size: 22rpx;
  color: #999;
}

.notification-text {
  font-size: 26rpx;
  color: #666;
  line-height: 1.5;
}

.unread-dot {
  position: absolute;
  top: 30rpx;
  right: 30rpx;
  width: 16rpx;
  height: 16rpx;
  background-color: #4CAF50;
  border-radius: 50%;
}

.empty {
  text-align: center;
  padding: 100rpx 0;
  color: #999;
  font-size: 28rpx;
}
</style>
