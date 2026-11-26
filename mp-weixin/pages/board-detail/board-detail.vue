<template>
  <view class="container">
    <!-- 板块信息 -->
    <view class="board-header">
      <view class="board-title">{{ board.name || '板块详情' }}</view>
      <view class="board-desc" v-if="board.description">{{ board.description }}</view>
      <view class="board-meta" v-if="board.school_name">🏫 {{ board.school_name }}</view>
    </view>

    <!-- 主题列表 -->
    <view class="topic-list">
      <view
        class="topic-item"
        v-for="topic in topics"
        :key="topic.id"
        @click="goToTopic(topic.id)"
      >
        <view class="topic-head">
          <text class="topic-status" :class="topic.status"></text>
          <text class="topic-title">{{ topic.title }}</text>
        </view>
        <view class="topic-meta">
          <text class="author">{{ topic.author?.username || '匿名用户' }}</text>
          <text class="dot">·</text>
          <text>{{ formatDate(topic.created_at) }}</text>
          <text class="dot">·</text>
          <text>👁 {{ topic.views || 0 }}</text>
          <text class="dot">·</text>
          <text>💬 {{ (topic.post_count || 1) - 1 }}</text>
        </view>
        <view class="topic-tags" v-if="topic.tags && topic.tags.length">
          <text
            class="tag"
            v-for="tag in topic.tags"
            :key="tag.id"
            @click.stop="goToTag(tag.id)"
          ># {{ tag.name }}</text>
        </view>
      </view>
    </view>

    <view class="tip" v-if="loading">加载中...</view>
    <view class="tip" v-else-if="noMore && topics.length > 0">没有更多了</view>
    <view class="tip empty" v-else-if="topics.length === 0">暂无主题，来发布第一个主题吧</view>

    <!-- 发布主题 -->
    <view class="publish-btn" v-if="board.id" @click="goToPublish">
      <text class="icon">✏️</text>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad, onPullDownRefresh, onReachBottom } from '@dcloudio/uni-app'
import forumApi from '../../api/forum'

const boardId = ref(null)
const board = ref({})
const topics = ref([])
const loading = ref(false)
const noMore = ref(false)
const page = ref(1)
const pageSize = 10

onLoad((options) => {
  boardId.value = Number(options?.id || options?.boardId || 0)
  if (!boardId.value) {
    uni.showToast({ title: '参数错误', icon: 'none' })
    return
  }
  loadBoard()
  loadTopics()
})

onPullDownRefresh(() => {
  page.value = 1
  noMore.value = false
  topics.value = []
  Promise.all([loadBoard(), loadTopics()]).finally(() => {
    uni.stopPullDownRefresh()
  })
})

onReachBottom(() => {
  if (!noMore.value && !loading.value) {
    page.value++
    loadTopics()
  }
})

const loadBoard = async () => {
  try {
    const result = await forumApi.getBoardDetail(boardId.value)
    board.value = result || {}
  } catch (error) {
    console.error('加载板块详情失败:', error)
  }
}

const loadTopics = async () => {
  if (loading.value) return
  loading.value = true
  try {
    const result = await forumApi.getBoardTopics(boardId.value, {
      page: page.value,
      page_size: pageSize
    })
    const list = result?.results || (Array.isArray(result) ? result : [])
    if (page.value === 1) {
      topics.value = list
    } else {
      topics.value = [...topics.value, ...list]
    }
    const total = result?.count
    noMore.value = total !== undefined ? topics.value.length >= total : list.length < pageSize
  } catch (error) {
    console.error('加载主题列表失败:', error)
    if (page.value > 1) page.value--
    uni.showToast({ title: '加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

const goToTopic = (topicId) => {
  uni.navigateTo({ url: `/pages/post-detail/post-detail?id=${topicId}` })
}

const goToTag = (tagId) => {
  if (!tagId) return
  uni.navigateTo({ url: `/pages/tag-detail/tag-detail?id=${tagId}` })
}

const goToPublish = () => {
  const token = uni.getStorageSync('accessToken')
  if (!token) {
    uni.showToast({ title: '请先登录', icon: 'none' })
    setTimeout(() => {
      uni.navigateTo({ url: '/pages/login/login' })
    }, 800)
    return
  }
  uni.navigateTo({ url: `/pages/topic-create/topic-create?boardId=${boardId.value}` })
}

const formatDate = (value) => {
  if (!value) return ''
  const date = new Date(value)
  const diff = Date.now() - date.getTime()
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  if (diff < 7 * 86400000) return `${Math.floor(diff / 86400000)}天前`
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}
</script>

<style scoped>
.container {
  min-height: 100vh;
  background-color: #f5f5f5;
  padding-bottom: 160rpx;
}

.board-header {
  background-color: #fff;
  padding: 40rpx 30rpx;
}

.board-title {
  font-size: 38rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 12rpx;
}

.board-desc {
  font-size: 26rpx;
  color: #666;
  line-height: 1.6;
  margin-bottom: 10rpx;
}

.board-meta {
  font-size: 24rpx;
  color: #999;
}

.topic-list {
  padding: 20rpx 30rpx;
}

.topic-item {
  background-color: #fff;
  border-radius: 16rpx;
  padding: 28rpx;
  margin-bottom: 16rpx;
}

.topic-head {
  display: flex;
  align-items: center;
  margin-bottom: 14rpx;
}

.topic-status {
  width: 14rpx;
  height: 14rpx;
  border-radius: 50%;
  background-color: #2e7d32;
  margin-right: 14rpx;
  flex-shrink: 0;
}

.topic-status.pinned {
  background-color: #e53935;
}

.topic-status.closed {
  background-color: #bbb;
}

.topic-title {
  flex: 1;
  font-size: 30rpx;
  font-weight: 500;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.topic-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10rpx;
  font-size: 24rpx;
  color: #999;
}

.author {
  color: #4361ee;
}

.dot {
  color: #ddd;
}

.topic-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
  margin-top: 16rpx;
}

.tag {
  font-size: 22rpx;
  color: #4361ee;
  background-color: #eef1ff;
  border-radius: 18rpx;
  padding: 4rpx 16rpx;
}

.tip {
  text-align: center;
  padding: 30rpx;
  color: #999;
  font-size: 26rpx;
}

.tip.empty {
  padding: 120rpx 30rpx;
}

.publish-btn {
  position: fixed;
  right: 40rpx;
  bottom: 60rpx;
  width: 100rpx;
  height: 100rpx;
  background-color: #4361ee;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4rpx 20rpx rgba(67, 97, 238, 0.4);
}

.publish-btn .icon {
  font-size: 46rpx;
}
</style>
