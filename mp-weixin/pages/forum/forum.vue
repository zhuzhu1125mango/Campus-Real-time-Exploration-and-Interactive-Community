<template>
  <view class="container">
    <!-- 排序标签 -->
    <view class="sort-bar">
      <view
        class="sort-item"
        :class="{ active: currentSort === '-created_at' }"
        @click="selectSort('-created_at')"
      >
        最新
      </view>
      <view
        class="sort-item"
        :class="{ active: currentSort === '-views' }"
        @click="selectSort('-views')"
      >
        最热
      </view>
    </view>

    <!-- 分类标签 -->
    <scroll-view class="category-scroll" scroll-x>
      <view class="category-list">
        <view
          class="category-item"
          :class="{ active: currentBoard === 0 }"
          @click="selectBoard(0)"
        >
          全部
        </view>
        <view
          class="category-item"
          :class="{ active: currentBoard === item.id }"
          v-for="item in boards"
          :key="item.id"
          @click="selectBoard(item.id)"
        >
          {{ item.name }}
        </view>
      </view>
    </scroll-view>

    <!-- 主题列表 -->
    <scroll-view class="topic-list" scroll-y @scrolltolower="loadMore">
      <view class="loading-more" v-if="loading && topics.length === 0">
        <text>加载中...</text>
      </view>
      <view class="topic-item" v-for="topic in topics" :key="topic.id" @click="viewTopic(topic.id)">
        <view class="topic-header">
          <image class="avatar" :src="topic.author?.avatar || '/static/logo.png'" mode="aspectFill"></image>
          <view class="author-info">
            <text class="author-name">{{ topic.author?.username || '匿名用户' }}</text>
            <text class="topic-time">{{ formatTime(topic.created_at) }}</text>
          </view>
          <view class="board-tag" v-if="topic.board_name">
            <text>{{ topic.board_name }}</text>
          </view>
        </view>
        <view class="topic-content">
          <text class="topic-title">{{ topic.title }}</text>
          <text class="topic-excerpt">{{ getTopicExcerpt(topic) }}</text>
        </view>
        <view class="topic-footer">
          <view class="footer-item">
            <text class="icon">👁</text>
            <text>{{ topic.views || 0 }}</text>
          </view>
          <view class="footer-item">
            <text class="icon">💬</text>
            <text>{{ topic.reply_count || 0 }}</text>
          </view>
          <view class="footer-item" v-if="topic.tags && topic.tags.length > 0">
            <text class="icon">🏷️</text>
            <text>{{ topic.tags.map(t => t.name).join(' ') }}</text>
          </view>
        </view>
      </view>

      <view class="loading-more" v-if="loading && topics.length > 0">
        <text>加载中...</text>
      </view>
      <view class="no-more" v-if="noMore && topics.length > 0">
        <text>没有更多了</text>
      </view>
      <view class="no-data" v-if="!loading && topics.length === 0">
        <text>暂无主题</text>
      </view>
    </scroll-view>

    <!-- 发布按钮 -->
    <view class="publish-btn" @click="goToPublish">
      <text class="icon">✏️</text>
    </view>
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { onUnload } from '@dcloudio/uni-app'
import forumApi from '../../api/forum'

const currentBoard = ref(0)
const currentSort = ref('-created_at')
const boards = ref([])
const topics = ref([])
const loading = ref(false)
const noMore = ref(false)
const page = ref(1)
let loginRedirectTimer = null

onMounted(() => {
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1]
  const options = currentPage.options || currentPage.$page?.options || {}
  if (options.boardId) {
    currentBoard.value = Number(options.boardId)
  }
  loadBoards().then(() => {
    loadTopics()
  })
})

const loadBoards = async () => {
  try {
    const result = await forumApi.getBoards()
    if (result && result.results) {
      boards.value = result.results
    } else if (Array.isArray(result)) {
      boards.value = result
    }
  } catch (error) {
    console.error('加载板块失败:', error)
  }
}

const loadTopics = async () => {
  if (loading.value) return
  loading.value = true

  try {
    const params = {
      page: page.value,
      page_size: 10,
      ordering: currentSort.value
    }
    if (currentBoard.value !== 0) {
      params.board = currentBoard.value
    }

    const result = await forumApi.getTopics(params)

    if (result && result.results) {
      if (page.value === 1) {
        topics.value = result.results
      } else {
        topics.value = [...topics.value, ...result.results]
      }
      noMore.value = page.value >= (result.total_pages || Math.ceil(result.count / 10) || 1)
    } else if (Array.isArray(result)) {
      if (page.value === 1) {
        topics.value = result
      } else {
        topics.value = [...topics.value, ...result]
      }
      noMore.value = true
    }
  } catch (error) {
    console.error('加载主题失败:', error)
    uni.showToast({ title: '加载失败', icon: 'none' })
  } finally {
    loading.value = false
    uni.stopPullDownRefresh()
  }
}

const selectBoard = (id) => {
  currentBoard.value = id
  page.value = 1
  noMore.value = false
  topics.value = []
  loadTopics()
}

const selectSort = (sort) => {
  if (currentSort.value === sort) return
  currentSort.value = sort
  page.value = 1
  noMore.value = false
  topics.value = []
  loadTopics()
}

const loadMore = () => {
  if (!noMore.value && !loading.value) {
    page.value++
    loadTopics()
  }
}

const viewTopic = (id) => {
  uni.navigateTo({ url: `/pages/post-detail/post-detail?id=${id}` })
}

const goToPublish = () => {
  const token = uni.getStorageSync('accessToken')
  if (!token) {
    uni.showToast({ title: '请先登录', icon: 'none' })
    loginRedirectTimer = setTimeout(() => {
      uni.navigateTo({ url: '/pages/login/login' })
    }, 1000)
    return
  }
  const boardParam = currentBoard.value !== 0 ? `?boardId=${currentBoard.value}` : ''
  uni.navigateTo({ url: `/pages/topic-create/topic-create${boardParam}` })
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

const getTopicExcerpt = (topic) => {
  if (topic.last_reply_user) {
    return `最新回复：${topic.last_reply_user.username || '匿名用户'}`
  }
  return ''
}

onPullDownRefresh(() => {
  page.value = 1
  noMore.value = false
  loadBoards()
  loadTopics()
})

onUnload(() => {
  if (loginRedirectTimer) {
    clearTimeout(loginRedirectTimer)
    loginRedirectTimer = null
  }
})
</script>

<style scoped>
.container {
  min-height: 100vh;
  background-color: #f5f5f5;
}

.sort-bar {
  display: flex;
  background-color: #fff;
  padding: 0 20rpx;
  border-bottom: 1rpx solid #f0f0f0;
}

.sort-item {
  padding: 20rpx 30rpx;
  font-size: 28rpx;
  color: #666;
  position: relative;
}

.sort-item.active {
  color: #4361ee;
  font-weight: 500;
}

.sort-item.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 30rpx;
  right: 30rpx;
  height: 4rpx;
  background-color: #4361ee;
  border-radius: 2rpx;
}

.category-scroll {
  background-color: #fff;
  white-space: nowrap;
  padding: 20rpx 0;
}

.category-list {
  display: inline-flex;
  padding: 0 20rpx;
}

.category-item {
  padding: 10rpx 30rpx;
  font-size: 28rpx;
  color: #666;
  margin: 0 10rpx;
  border-radius: 30rpx;
  background-color: #f5f5f5;
}

.category-item.active {
  background-color: #4361ee;
  color: #fff;
}

.topic-list {
  height: calc(100vh - 220rpx);
  padding: 20rpx 30rpx;
}

.topic-item {
  background-color: #fff;
  border-radius: 16rpx;
  padding: 30rpx;
  margin-bottom: 20rpx;
}

.topic-header {
  display: flex;
  align-items: center;
  margin-bottom: 20rpx;
}

.avatar {
  width: 80rpx;
  height: 80rpx;
  border-radius: 50%;
  margin-right: 20rpx;
}

.author-info {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.author-name {
  font-size: 28rpx;
  font-weight: 500;
  color: #333;
}

.topic-time {
  font-size: 24rpx;
  color: #999;
  margin-top: 5rpx;
}

.board-tag {
  padding: 6rpx 16rpx;
  background-color: #e8f5e9;
  color: #4361ee;
  font-size: 22rpx;
  border-radius: 8rpx;
}

.topic-content {
  margin-bottom: 20rpx;
}

.topic-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #333;
  display: block;
  margin-bottom: 10rpx;
}

.topic-excerpt {
  font-size: 26rpx;
  color: #999;
  line-height: 1.6;
  display: block;
}

.topic-footer {
  display: flex;
  gap: 40rpx;
  padding-top: 20rpx;
  border-top: 1rpx solid #f0f0f0;
}

.footer-item {
  display: flex;
  align-items: center;
  gap: 10rpx;
  font-size: 26rpx;
  color: #999;
}

.publish-btn {
  position: fixed;
  right: 40rpx;
  bottom: 100rpx;
  width: 100rpx;
  height: 100rpx;
  background-color: #4361ee;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4rpx 20rpx rgba(76, 175, 80, 0.4);
}

.publish-btn .icon {
  font-size: 50rpx;
}

.loading-more,
.no-more,
.no-data {
  text-align: center;
  padding: 30rpx;
  color: #999;
  font-size: 26rpx;
}

.no-data {
  padding: 100rpx 30rpx;
}
</style>
