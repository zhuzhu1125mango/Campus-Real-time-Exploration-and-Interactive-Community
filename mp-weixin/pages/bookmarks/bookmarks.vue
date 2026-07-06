<template>
  <view class="container">
    <view class="header">
      <text class="title">我的收藏</text>
    </view>

    <scroll-view class="bookmark-list" scroll-y @scrolltolower="loadMore">
      <view v-if="loading" class="loading">
        <view class="spinner"></view>
        <text>加载中...</text>
      </view>

      <view v-else-if="bookmarks.length === 0" class="empty">
        <text class="empty-icon">🔖</text>
        <text>您还没有收藏任何主题</text>
        <view class="to-forum" @click="goToForum">浏览论坛</view>
      </view>

      <view
        v-else
        v-for="bookmark in bookmarks"
        :key="bookmark.id"
        class="bookmark-item"
        @click="goToTopicDetail(bookmark.topic)"
      >
        <view class="bookmark-main">
          <text class="bookmark-title">{{ bookmark.topic_title || `收藏主题 ${bookmark.topic}` }}</text>
          <text class="bookmark-date">{{ formatDate(bookmark.created_at) }}</text>
        </view>
        <view class="remove-btn" @click.stop="removeBookmark(bookmark.topic)">
          <text>删除</text>
        </view>
      </view>

      <view v-if="bookmarks.length > 0" class="load-more">
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

const bookmarks = ref([])
const loading = ref(false)
const loadingMore = ref(false)
const page = ref(1)
const pageSize = 10
const hasMore = ref(true)

onMounted(() => {
  checkLoginAndLoad()
})

const checkLoginAndLoad = () => {
  const token = uni.getStorageSync('accessToken')
  if (!token) {
    uni.showToast({ title: '请先登录', icon: 'none' })
    setTimeout(() => {
      uni.navigateBack()
    }, 1500)
    return
  }
  loadBookmarks(true)
}

const loadBookmarks = async (reset = false) => {
  if (reset) {
    page.value = 1
    bookmarks.value = []
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
    const result = await forumApi.getMyBookmarks()
    const list = Array.isArray(result) ? result : (result.results || [])
    bookmarks.value = reset ? list : [...bookmarks.value, ...list]
    hasMore.value = list.length === pageSize
    page.value++
  } catch (error) {
    console.error('获取收藏失败:', error)
    uni.showToast({ title: '获取收藏失败', icon: 'none' })
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

const loadMore = () => {
  loadBookmarks(false)
}

const removeBookmark = async (topicId) => {
  uni.showModal({
    title: '提示',
    content: '确定要移除该收藏吗？',
    success: async (res) => {
      if (res.confirm) {
        try {
          await forumApi.unbookmarkTopic(topicId)
          bookmarks.value = bookmarks.value.filter(b => b.topic !== topicId)
          uni.showToast({ title: '已移除', icon: 'success' })
        } catch (error) {
          console.error('移除收藏失败:', error)
          uni.showToast({ title: '移除失败', icon: 'none' })
        }
      }
    }
  })
}

const goToTopicDetail = (topicId) => {
  uni.navigateTo({ url: `/pages/post-detail/post-detail?id=${topicId}` })
}

const goToForum = () => {
  uni.switchTab({ url: '/pages/forum/forum' })
}

const formatDate = (dateStr) => {
  if (!dateStr) return '未知'
  const date = new Date(dateStr)
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
  text-align: center;
}

.title {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
}

.bookmark-list {
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

.bookmark-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background-color: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
  margin-bottom: 20rpx;
}

.bookmark-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.bookmark-title {
  font-size: 28rpx;
  color: #333;
  font-weight: 500;
}

.bookmark-date {
  font-size: 24rpx;
  color: #999;
}

.remove-btn {
  padding: 10rpx 20rpx;
  font-size: 24rpx;
  color: #ef4444;
  border: 1rpx solid #ef4444;
  border-radius: 8rpx;
  margin-left: 16rpx;
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
