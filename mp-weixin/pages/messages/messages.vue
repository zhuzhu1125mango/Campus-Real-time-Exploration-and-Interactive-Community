<template>
  <view class="container">
    <view class="loading" v-if="loading && conversations.length === 0">
      <text>加载中...</text>
    </view>

    <view class="empty-tip" v-else-if="!loading && conversations.length === 0">
      <text>暂无消息</text>
      <text class="sub-tip">添加好友后开始聊天</text>
    </view>

    <scroll-view v-else class="conversation-list" scroll-y refresher-enabled :refresher-triggered="refreshing"
      @refresherrefresh="onRefresh" @scrolltolower="loadMore">
      <view class="conversation-item" v-for="item in conversations" :key="item.user.id"
        @click="goToChat(item.user.id, item.user.username)">
        <image class="avatar" :src="formatAvatar(item.user.avatar)" mode="aspectFill" />
        <view class="content">
          <view class="header">
            <text class="username">{{ item.user.username }}</text>
            <text class="time">{{ formatTime(item.last_message?.created_at) }}</text>
          </view>
          <view class="footer">
            <text class="last-message">{{ item.last_message?.content || '暂无消息' }}</text>
            <text v-if="item.unread_count > 0" class="badge">{{ item.unread_count > 99 ? '99+' : item.unread_count
            }}</text>
          </view>
        </view>
      </view>

      <view class="loading-more" v-if="loading && conversations.length > 0">
        <text>加载中...</text>
      </view>
      <view class="no-more" v-if="noMore && conversations.length > 0">
        <text>没有更多了</text>
      </view>
    </scroll-view>
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { onPullDownRefresh } from '@dcloudio/uni-app'
import userApi from '../../api/user'
import { formatAvatar } from '../../utils/image'
import { formatTime } from '../../utils/date'

const conversations = ref([])
const loading = ref(false)
const refreshing = ref(false)
const noMore = ref(false)
const page = ref(1)
const pageSize = 20

onMounted(() => {
  checkAuthAndLoad()
})

onPullDownRefresh(() => {
  onRefresh()
})

const checkAuthAndLoad = () => {
  const token = uni.getStorageSync('accessToken')
  if (!token) {
    uni.showToast({ title: '请先登录', icon: 'none' })
    setTimeout(() => {
      uni.navigateTo({ url: '/pages/login/login' })
    }, 1000)
    return
  }
  loadConversations()
}

const loadConversations = async (isRefresh = false) => {
  if (loading.value) return
  loading.value = true

  try {
    const result = await userApi.getConversations()
    const list = Array.isArray(result) ? result : result.conversations || []
    if (isRefresh) {
      conversations.value = list
    } else {
      conversations.value = list
    }
    noMore.value = true
  } catch (error) {
    console.error('获取会话列表失败:', error)
    uni.showToast({ title: '加载失败', icon: 'none' })
  } finally {
    loading.value = false
    refreshing.value = false
    uni.stopPullDownRefresh()
  }
}

const onRefresh = () => {
  refreshing.value = true
  loadConversations(true)
}

const loadMore = () => {
  // 会话列表通常一次性返回，暂不做分页
}

const goToChat = (userId, username) => {
  uni.navigateTo({ url: `/pages/chat-detail/chat-detail?userId=${userId}&username=${encodeURIComponent(username)}` })
}
</script>

<style scoped>
.container {
  min-height: 100vh;
  background-color: #f5f5f5;
}

.loading,
.empty-tip {
  text-align: center;
  padding: 100rpx 30rpx;
  color: #999;
  font-size: 28rpx;
}

.empty-tip {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.sub-tip {
  margin-top: 20rpx;
  font-size: 24rpx;
  color: #bbb;
}

.conversation-list {
  height: 100vh;
}

.conversation-item {
  display: flex;
  align-items: center;
  background-color: #fff;
  padding: 24rpx 30rpx;
  border-bottom: 1rpx solid #f0f0f0;
}

.avatar {
  width: 88rpx;
  height: 88rpx;
  border-radius: 50%;
  margin-right: 24rpx;
  background-color: #eee;
}

.content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10rpx;
}

.username {
  font-size: 30rpx;
  font-weight: 600;
  color: #333;
}

.time {
  font-size: 22rpx;
  color: #999;
}

.footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.last-message {
  flex: 1;
  font-size: 26rpx;
  color: #666;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-right: 20rpx;
}

.badge {
  min-width: 32rpx;
  height: 32rpx;
  padding: 0 8rpx;
  background-color: #ef4444;
  color: #fff;
  font-size: 20rpx;
  border-radius: 16rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.loading-more,
.no-more {
  text-align: center;
  padding: 30rpx;
  color: #999;
  font-size: 26rpx;
}
</style>
