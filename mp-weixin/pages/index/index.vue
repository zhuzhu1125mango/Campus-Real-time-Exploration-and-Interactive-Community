<template>
  <view class="container">
    <!-- 顶部搜索区域 -->
    <view class="search-section">
      <view class="search-bar" @click="goToSearch">
        <text class="search-placeholder">搜索院校、帖子、内容...</text>
        <view class="search-btn">搜索</view>
      </view>
    </view>

    <scroll-view scroll-y class="main-scroll" @scrolltolower="loadMore" refresher-enabled :refresher-triggered="refreshing" @refresherrefresh="onRefresh">
      <!-- 功能入口 -->
      <view class="function-grid">
        <view class="function-item" @click="navigateTo('/pages/schools/schools')">
          <view class="function-icon">🏫</view>
          <text class="function-text">院校查询</text>
        </view>
        <view class="function-item" @click="navigateTo('/pages/explore/explore')">
          <view class="function-icon">🗺️</view>
          <text class="function-text">校园探索</text>
        </view>
        <view class="function-item" @click="navigateTo('/pages/forum/forum')">
          <view class="function-icon">📋</view>
          <text class="function-text">论坛</text>
        </view>
        <view class="function-item" @click="navigateTo('/pages/content/content')">
          <view class="function-icon">📄</view>
          <text class="function-text">内容中心</text>
        </view>
        <view class="function-item" @click="navigateTo('/pages/learning/learning')">
          <view class="function-icon">📚</view>
          <text class="function-text">在线学习</text>
        </view>
        <view class="function-item" @click="navigateTo('/pages/activity/activity')">
          <view class="function-icon">📣</view>
          <text class="function-text">动态</text>
        </view>
        <view class="function-item" @click="navigateTo('/pages/messages/messages')">
          <view class="function-icon">💬</view>
          <text class="function-text">消息</text>
        </view>
        <view class="function-item" @click="navigateTo('/pages/profile/profile')">
          <view class="function-icon">👤</view>
          <text class="function-text">我的</text>
        </view>
      </view>

      <!-- 热门话题 -->
      <view class="section topics-section">
        <view class="section-header">
          <text class="section-title">热门话题</text>
        </view>
        <scroll-view v-if="trendingTopics.length > 0" scroll-x class="topic-scroll">
          <view
            v-for="topic in trendingTopics"
            :key="topic.id"
            class="topic-tag"
            @click="goToTrending(topic)"
          >
            # {{ topic.name }}
          </view>
        </scroll-view>
        <view v-else-if="loadingTrending" class="section-loading">
          <view class="spinner small"></view>
        </view>
        <view v-else class="empty-tip">
          <text>暂无热门话题</text>
        </view>
      </view>

      <!-- Feed 流 -->
      <view class="feed-section">
        <view class="feed-tabs">
          <view
            v-for="opt in typeOptions"
            :key="opt.value"
            class="feed-tab"
            :class="{ active: feedType === opt.value }"
            @click="onTypeChange(opt.value)"
          >
            {{ opt.label }}
          </view>
          <view v-if="feedType === 'nearby'" class="locate-btn" @click="locateUser">
            <text>{{ locating ? '定位中' : '定位' }}</text>
          </view>
        </view>

        <view v-if="feedType === 'following' && !isLoggedIn" class="login-prompt">
          <text>登录后查看关注好友的动态</text>
          <button class="login-btn" @click="goToLogin">去登录</button>
        </view>

        <view v-else>
          <view v-if="loading && items.length === 0" class="feed-loading">
            <view class="spinner"></view>
            <text>加载中...</text>
          </view>
          <view v-else-if="items.length === 0" class="empty-tip">
            <text>暂无{{ getTypeLabel(feedType) }}内容</text>
          </view>
          <view v-else class="feed-list">
            <view
              v-for="item in items"
              :key="item.id"
              class="feed-card"
              @click="goToItem(item)"
            >
              <view class="feed-header">
                <image
                  class="author-avatar"
                  :src="item.author?.avatar || '/static/logo.png'"
                  mode="aspectFill"
                />
                <view class="author-info">
                  <text class="author-name">{{ item.author?.username || '匿名用户' }}</text>
                  <text class="feed-time">{{ formatTime(item.created_at) }}</text>
                </view>
                <text class="type-badge" :style="{ color: getTypeBadge(item.object_type).color, backgroundColor: getTypeBadge(item.object_type).color + '20' }">
                  {{ getTypeBadge(item.object_type).label }}
                </text>
              </view>

              <view class="feed-body">
                <text class="feed-title">{{ item.title }}</text>
                <text class="feed-summary">{{ stripHtml(item.content || '').slice(0, 120) }}</text>
                <view v-if="item.images && item.images.length > 0" class="feed-images">
                  <image
                    v-for="(img, idx) in item.images.slice(0, 3)"
                    :key="idx"
                    class="feed-image"
                    :src="img"
                    mode="aspectFill"
                  />
                </view>
              </view>

              <view class="feed-footer">
                <template v-if="item.object_type === 'topic'">
                  <text v-if="item.meta?.board_name" class="meta-item">{{ item.meta.board_name }}</text>
                  <text class="meta-item">💬 {{ item.meta?.reply_count || 0 }}</text>
                  <text class="meta-item">👁️ {{ item.meta?.view_count || 0 }}</text>
                </template>
                <template v-else-if="item.object_type === 'content'">
                  <text v-if="item.meta?.content_type" class="meta-item">{{ item.meta.content_type }}</text>
                  <text class="meta-item">👁️ {{ item.meta?.view_count || 0 }}</text>
                  <text class="meta-item">💬 {{ item.meta?.comment_count || 0 }}</text>
                  <text class="meta-item">⭐ {{ item.meta?.like_count || 0 }}</text>
                </template>
                <template v-else-if="item.object_type === 'activity'">
                  <text class="meta-item">⭐ {{ item.meta?.likes_count || 0 }}</text>
                  <text class="meta-item">💬 {{ item.meta?.comments_count || 0 }}</text>
                </template>
                <template v-else-if="item.object_type === 'event'">
                  <text v-if="item.meta?.location" class="meta-item">📍 {{ item.meta.location }}</text>
                  <text v-if="item.meta?.start_time" class="meta-item">📅 {{ formatTime(item.meta.start_time) }}</text>
                </template>
              </view>
            </view>
          </view>

          <view class="feed-loadmore">
            <text v-if="loading" class="load-text">加载中...</text>
            <text v-else-if="hasMore" class="load-text" @click="loadMore">加载更多</text>
            <text v-else-if="items.length > 0" class="load-text no-more">没有更多了</text>
          </view>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import feedApi from '../../api/feed'

const DEFAULT_LOCATION = { lat: 39.9042, lng: 116.4074 }
const typeOptions = [
  { label: '推荐', value: 'recommend' },
  { label: '关注', value: 'following' },
  { label: '附近', value: 'nearby' }
]

const feedType = ref('recommend')
const items = ref([])
const loading = ref(false)
const hasMore = ref(true)
const page = ref(1)
const pageSize = 10
const userLocation = ref(null)
const locating = ref(false)
const refreshing = ref(false)
const trendingTopics = ref([])
const loadingTrending = ref(false)

const isLoggedIn = computed(() => !!uni.getStorageSync('accessToken'))

onMounted(() => {
  fetchFeed(true)
  fetchTrendingTopics()
})

const getTypeLabel = (type) => {
  return typeOptions.find(o => o.value === type)?.label || type
}

const getTypeBadge = (objectType) => {
  const map = {
    topic: { label: '话题', color: '#4361ee' },
    content: { label: '文章', color: '#10b981' },
    activity: { label: '动态', color: '#f59e0b' },
    event: { label: '活动', color: '#ef4444' }
  }
  return map[objectType] || { label: '其他', color: '#6b7280' }
}

const stripHtml = (html) => {
  if (!html) return ''
  return html.replace(/<[^>]+>/g, '').replace(/&nbsp;/g, ' ').trim()
}

const fetchFeed = async (reset = false) => {
  if (loading.value) return
  if (reset) {
    page.value = 1
    items.value = []
    hasMore.value = true
  }
  if (!hasMore.value && !reset) return

  loading.value = true
  try {
    const params = {
      type: feedType.value,
      page: page.value,
      page_size: pageSize
    }
    if (feedType.value === 'nearby') {
      const loc = userLocation.value || DEFAULT_LOCATION
      params.lat = loc.lat
      params.lng = loc.lng
      params.radius = 10
    }
    const response = await feedApi.getFeed(params)
    const results = response.results || []
    items.value = reset ? results : [...items.value, ...results]
    hasMore.value = results.length === pageSize
    page.value++
  } catch (error) {
    console.error('加载 Feed 失败:', error)
    uni.showToast({ title: '加载 Feed 失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

const onTypeChange = (type) => {
  feedType.value = type
  if (type === 'nearby' && !userLocation.value) {
    locateUser(() => fetchFeed(true))
  } else {
    fetchFeed(true)
  }
}

const loadMore = () => {
  if (!loading.value && hasMore.value) {
    fetchFeed()
  }
}

const onRefresh = () => {
  refreshing.value = true
  Promise.all([
    fetchTrendingTopics(),
    fetchFeed(true)
  ]).finally(() => {
    refreshing.value = false
  })
}

const locateUser = (callback) => {
  locating.value = true
  uni.getLocation({
    type: 'gcj02',
    isHighAccuracy: true,
    highAccuracyExpireTime: 10000,
    success: (res) => {
      userLocation.value = { lat: res.latitude, lng: res.longitude }
      locating.value = false
      callback?.()
    },
    fail: () => {
      uni.showToast({ title: '无法获取当前位置，使用默认位置', icon: 'none' })
      userLocation.value = DEFAULT_LOCATION
      locating.value = false
      callback?.()
    }
  })
}

const fetchTrendingTopics = async () => {
  loadingTrending.value = true
  try {
    const data = await feedApi.getTrendingTopics()
    trendingTopics.value = Array.isArray(data) ? data : []
  } catch (error) {
    console.error('加载热门话题失败:', error)
    trendingTopics.value = []
  } finally {
    loadingTrending.value = false
  }
}

const goToItem = (item) => {
  switch (item.object_type) {
    case 'topic':
      uni.navigateTo({ url: `/pages/post-detail/post-detail?id=${item.object_id}` })
      break
    case 'content':
      uni.navigateTo({ url: `/pages/content-detail/content-detail?id=${item.object_id}` })
      break
    case 'activity':
      uni.navigateTo({ url: '/pages/activity/activity' })
      break
    case 'event':
      uni.switchTab({ url: '/pages/explore/explore' })
      break
  }
}

const goToTrending = (topic) => {
  if (topic.type === 'forum_tag') {
    uni.navigateTo({ url: `/pages/forum/forum?tag=${encodeURIComponent(topic.name)}` })
  } else {
    uni.navigateTo({ url: `/pages/content/content?tag=${encodeURIComponent(topic.name)}` })
  }
}

const goToSearch = () => {
  uni.navigateTo({ url: '/pages/search/search' })
}

const goToLogin = () => {
  uni.navigateTo({ url: '/pages/login/login' })
}

const navigateTo = (url) => {
  const tabbarPages = [
    '/pages/index/index',
    '/pages/explore/explore',
    '/pages/forum/forum',
    '/pages/messages/messages',
    '/pages/profile/profile'
  ]

  if (tabbarPages.includes(url)) {
    uni.switchTab({ url })
  } else {
    uni.navigateTo({ url })
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
  if (diff < 604800000) return Math.floor(diff / 86400000) + '天前'
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

.search-section {
  background-color: #4361ee;
  padding: 30rpx;
}

.search-bar {
  display: flex;
  align-items: center;
  background-color: #fff;
  border-radius: 50rpx;
  padding: 16rpx 30rpx;
}

.search-placeholder {
  flex: 1;
  font-size: 28rpx;
  color: #999;
}

.search-btn {
  font-size: 26rpx;
  color: #4361ee;
  font-weight: 500;
}

.main-scroll {
  flex: 1;
}

.function-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20rpx;
  padding: 30rpx;
  background-color: #fff;
  margin-bottom: 20rpx;
}

.function-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.function-icon {
  width: 90rpx;
  height: 90rpx;
  background-color: #f0f9f0;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 48rpx;
  margin-bottom: 10rpx;
}

.function-text {
  font-size: 24rpx;
  color: #666;
}

.section {
  background-color: #fff;
  margin-bottom: 20rpx;
  padding: 30rpx;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20rpx;
}

.section-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
}

.topic-scroll {
  white-space: nowrap;
}

.topic-tag {
  display: inline-block;
  padding: 12rpx 24rpx;
  margin-right: 16rpx;
  background-color: #eef1ff;
  color: #4361ee;
  font-size: 26rpx;
  border-radius: 9999rpx;
}

.feed-section {
  background-color: #fff;
  padding: 30rpx;
}

.feed-tabs {
  display: flex;
  align-items: center;
  gap: 20rpx;
  margin-bottom: 24rpx;
}

.feed-tab {
  padding: 12rpx 28rpx;
  font-size: 28rpx;
  color: #666;
  background-color: #f3f4f6;
  border-radius: 9999rpx;
}

.feed-tab.active {
  background-color: #4361ee;
  color: #fff;
  font-weight: 500;
}

.locate-btn {
  margin-left: auto;
  padding: 10rpx 20rpx;
  font-size: 24rpx;
  color: #4361ee;
  background-color: #eef1ff;
  border-radius: 8rpx;
}

.login-prompt {
  text-align: center;
  padding: 80rpx 40rpx;
  background-color: #f9fafc;
  border-radius: 16rpx;
}

.login-prompt text {
  display: block;
  font-size: 28rpx;
  color: #666;
  margin-bottom: 24rpx;
}

.login-btn {
  display: inline-block;
  padding: 16rpx 48rpx;
  background-color: #4361ee;
  color: #fff;
  font-size: 28rpx;
  border-radius: 12rpx;
}

.feed-loading,
.section-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60rpx 0;
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

.spinner.small {
  width: 32rpx;
  height: 32rpx;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-tip {
  text-align: center;
  padding: 60rpx 0;
  color: #999;
  font-size: 28rpx;
}

.feed-list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.feed-card {
  background-color: #f9fafc;
  border-radius: 16rpx;
  padding: 24rpx;
}

.feed-header {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-bottom: 16rpx;
}

.author-avatar {
  width: 72rpx;
  height: 72rpx;
  border-radius: 50%;
  background-color: #eee;
}

.author-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.author-name {
  font-size: 28rpx;
  font-weight: 500;
  color: #333;
}

.feed-time {
  font-size: 22rpx;
  color: #999;
}

.type-badge {
  font-size: 22rpx;
  padding: 4rpx 14rpx;
  border-radius: 9999rpx;
}

.feed-body {
  margin-bottom: 16rpx;
}

.feed-title {
  display: block;
  font-size: 30rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 10rpx;
  line-height: 1.4;
}

.feed-summary {
  display: block;
  font-size: 26rpx;
  color: #666;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.feed-images {
  display: flex;
  gap: 12rpx;
  margin-top: 16rpx;
}

.feed-image {
  width: 200rpx;
  height: 200rpx;
  border-radius: 12rpx;
  background-color: #eee;
}

.feed-footer {
  display: flex;
  flex-wrap: wrap;
  gap: 20rpx;
  padding-top: 16rpx;
  border-top: 1rpx solid #f0f0f0;
}

.meta-item {
  font-size: 24rpx;
  color: #999;
}

.feed-loadmore {
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
