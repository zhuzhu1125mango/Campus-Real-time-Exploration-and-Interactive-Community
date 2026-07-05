<template>
  <view class="container">
    <!-- 顶部搜索区域 -->
    <view class="search-section">
      <view class="search-bar">
        <input
          type="text"
          v-model="searchKeyword"
          placeholder="搜索院校、帖子..."
          class="search-input"
          @confirm="handleSearch"
        />
        <button class="search-btn" @click="handleSearch">搜索</button>
      </view>
    </view>

    <!-- 功能入口 -->
    <view class="function-grid">
      <view class="function-item" @click="navigateTo('/pages/schools/schools')">
        <view class="function-icon">🏫</view>
        <text class="function-text">院校查询</text>
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
      <view class="function-item" @click="navigateTo('/pages/messages/messages')">
        <view class="function-icon">💬</view>
        <text class="function-text">消息</text>
      </view>
      <view class="function-item" @click="navigateTo('/pages/chat-room/chat-room')">
        <view class="function-icon">🗨️</view>
        <text class="function-text">聊天室</text>
      </view>
      <view class="function-item" @click="navigateTo('/pages/notifications/notifications')">
        <view class="function-icon">🔔</view>
        <text class="function-text">通知</text>
      </view>
    </view>

    <!-- 最新帖子 -->
    <view class="section">
      <view class="section-header">
        <text class="section-title">最新帖子</text>
        <text class="section-more" @click="navigateTo('/pages/forum/forum')">更多 ></text>
      </view>
      <view class="post-list" v-if="latestPosts.length > 0">
        <view class="post-item" v-for="post in latestPosts" :key="post.id" @click="viewPost(post.id)">
          <view class="post-title">{{ post.title }}</view>
          <view class="post-info">
            <text class="post-author">{{ post.author?.username || '匿名用户' }}</text>
            <text class="post-time">{{ formatTime(post.created_at) }}</text>
          </view>
        </view>
      </view>
      <view class="empty-tip" v-else>
        <text>暂无帖子</text>
      </view>
    </view>

    <!-- 推荐院校 -->
    <view class="section">
      <view class="section-header">
        <text class="section-title">推荐院校</text>
        <text class="section-more" @click="navigateTo('/pages/schools/schools')">更多 ></text>
      </view>
      <view class="school-list" v-if="recommendedSchools.length > 0">
        <view class="school-item" v-for="school in recommendedSchools" :key="school.id" @click="viewSchool(school.id)">
          <view class="school-name">{{ school.name }}</view>
          <view class="school-info">{{ school.province }} | {{ school.school_level }}</view>
        </view>
      </view>
      <view class="empty-tip" v-else>
        <text>暂无推荐院校</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import forumApi from '../../api/forum'
import schoolApi from '../../api/school'

const searchKeyword = ref('')
const latestPosts = ref([])
const recommendedSchools = ref([])

onMounted(() => {
  loadData()
})

const loadData = async () => {
  await Promise.all([
    loadLatestPosts(),
    loadRecommendedSchools()
  ])
}

const loadLatestPosts = async () => {
  try {
    const result = await forumApi.getTopics({ page: 1, page_size: 5 })
    if (result && result.results) {
      latestPosts.value = result.results
    } else if (Array.isArray(result)) {
      latestPosts.value = result.slice(0, 5)
    }
  } catch (error) {
    console.error('加载最新帖子失败:', error)
  }
}

const loadRecommendedSchools = async () => {
  try {
    const result = await schoolApi.getSchools({ page: 1, page_size: 5 })
    if (result && result.results) {
      recommendedSchools.value = result.results
    } else if (Array.isArray(result)) {
      recommendedSchools.value = result.slice(0, 5)
    }
  } catch (error) {
    console.error('加载推荐院校失败:', error)
  }
}

const handleSearch = () => {
  const keyword = searchKeyword.value.trim()
  uni.navigateTo({
    url: `/pages/search/search?keyword=${encodeURIComponent(keyword)}`
  })
}

const navigateTo = (url) => {
  const tabbarPages = [
    '/pages/index/index',
    '/pages/schools/schools',
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

const viewPost = (id) => {
  uni.navigateTo({
    url: `/pages/post-detail/post-detail?id=${id}`
  })
}

const viewSchool = (id) => {
  uni.navigateTo({
    url: `/pages/school-detail/school-detail?id=${id}`
  })
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
  padding-bottom: 20rpx;
}

.search-section {
  background-color: #4CAF50;
  padding: 30rpx;
}

.search-bar {
  display: flex;
  align-items: center;
  background-color: #fff;
  border-radius: 50rpx;
  padding: 10rpx 20rpx;
}

.search-input {
  flex: 1;
  height: 60rpx;
  font-size: 28rpx;
}

.search-btn {
  background-color: #4CAF50;
  color: #fff;
  font-size: 26rpx;
  padding: 10rpx 30rpx;
  border-radius: 30rpx;
  border: none;
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
  width: 100rpx;
  height: 100rpx;
  background-color: #f0f9f0;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 50rpx;
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

.section-more {
  font-size: 26rpx;
  color: #999;
}

.post-list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.post-item {
  padding: 20rpx;
  background-color: #f9f9f9;
  border-radius: 10rpx;
}

.post-title {
  font-size: 28rpx;
  color: #333;
  margin-bottom: 10rpx;
}

.post-info {
  display: flex;
  justify-content: space-between;
  font-size: 24rpx;
  color: #999;
}

.empty-tip {
  text-align: center;
  padding: 40rpx;
  color: #999;
  font-size: 26rpx;
}

.school-list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.school-item {
  padding: 20rpx;
  background-color: #f9f9f9;
  border-radius: 10rpx;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.school-name {
  font-size: 28rpx;
  color: #333;
  font-weight: 500;
}

.school-info {
  font-size: 24rpx;
  color: #999;
}
</style>
