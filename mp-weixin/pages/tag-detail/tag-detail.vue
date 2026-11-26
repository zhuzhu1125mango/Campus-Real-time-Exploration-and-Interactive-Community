<template>
  <view class="container">
    <view class="tag-header">
      <view class="tag-name"># {{ tag.name || '标签详情' }}</view>
      <view class="tag-meta">共 {{ tag.topic_count || total || 0 }} 个主题</view>
    </view>

    <view class="topic-list">
      <view
        class="topic-item"
        v-for="topic in topics"
        :key="topic.id"
        @click="goToTopic(topic.id)"
      >
        <text class="topic-title">{{ topic.title }}</text>
        <view class="topic-meta">
          <text class="author">{{ topic.author?.username || '匿名用户' }}</text>
          <text class="dot">·</text>
          <text>{{ formatDate(topic.created_at) }}</text>
          <text class="dot">·</text>
          <text>👁 {{ topic.views || 0 }}</text>
          <text class="dot">·</text>
          <text>💬 {{ topic.reply_count || 0 }}</text>
        </view>
      </view>
    </view>

    <view class="tip" v-if="loading">加载中...</view>
    <view class="tip" v-else-if="noMore && topics.length > 0">没有更多了</view>
    <view class="tip empty" v-else-if="topics.length === 0">该标签下还没有主题</view>

    <view class="back-bar">
      <button class="back-btn" @click="goBack">返回论坛</button>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad, onPullDownRefresh, onReachBottom } from '@dcloudio/uni-app'
import forumApi from '../../api/forum'

const tagId = ref(null)
const tag = ref({})
const topics = ref([])
const total = ref(0)
const loading = ref(false)
const noMore = ref(false)
const page = ref(1)
const pageSize = 10

onLoad((options) => {
  tagId.value = Number(options?.id || 0)
  if (!tagId.value) {
    uni.showToast({ title: '参数错误', icon: 'none' })
    return
  }
  loadTag()
  loadTopics()
})

onPullDownRefresh(() => {
  page.value = 1
  noMore.value = false
  topics.value = []
  Promise.all([loadTag(), loadTopics()]).finally(() => {
    uni.stopPullDownRefresh()
  })
})

onReachBottom(() => {
  if (!noMore.value && !loading.value) {
    page.value++
    loadTopics()
  }
})

const loadTag = async () => {
  try {
    const result = await forumApi.getTagDetail(tagId.value)
    tag.value = result || {}
  } catch (error) {
    console.error('加载标签详情失败:', error)
    uni.showToast({ title: '加载标签失败', icon: 'none' })
  }
}

const loadTopics = async () => {
  if (loading.value) return
  loading.value = true
  try {
    const result = await forumApi.getTagTopics(tagId.value, {
      page: page.value,
      page_size: pageSize
    })
    const list = result?.results || (Array.isArray(result) ? result : [])
    if (page.value === 1) {
      topics.value = list
    } else {
      topics.value = [...topics.value, ...list]
    }
    total.value = result?.count || topics.value.length
    noMore.value = result?.count !== undefined
      ? topics.value.length >= result.count
      : list.length < pageSize
  } catch (error) {
    console.error('加载标签主题失败:', error)
    if (page.value > 1) page.value--
    topics.value = page.value === 1 ? [] : topics.value
    uni.showToast({ title: '加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

const goToTopic = (topicId) => {
  uni.navigateTo({ url: `/pages/post-detail/post-detail?id=${topicId}` })
}

const goBack = () => {
  const pages = getCurrentPages()
  if (pages.length > 1) {
    uni.navigateBack()
  } else {
    uni.switchTab({ url: '/pages/forum/forum' })
  }
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
  padding-bottom: 140rpx;
}

.tag-header {
  background-color: #fff;
  padding: 40rpx 30rpx;
}

.tag-name {
  font-size: 38rpx;
  font-weight: 600;
  color: #4361ee;
  margin-bottom: 12rpx;
}

.tag-meta {
  font-size: 26rpx;
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

.topic-title {
  display: block;
  font-size: 30rpx;
  font-weight: 500;
  color: #333;
  margin-bottom: 14rpx;
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

.tip {
  text-align: center;
  padding: 30rpx;
  color: #999;
  font-size: 26rpx;
}

.tip.empty {
  padding: 120rpx 30rpx;
}

.back-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  padding: 20rpx 30rpx;
  background-color: #fff;
  box-shadow: 0 -2rpx 10rpx rgba(0, 0, 0, 0.05);
}

.back-btn {
  width: 100%;
  height: 76rpx;
  line-height: 76rpx;
  border-radius: 38rpx;
  font-size: 28rpx;
  color: #4361ee;
  background-color: #eef1ff;
  border: none;
}
</style>
