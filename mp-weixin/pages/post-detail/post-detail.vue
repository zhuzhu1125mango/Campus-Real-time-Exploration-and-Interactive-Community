<template>
  <view class="container">
    <view class="loading" v-if="loading && !topic.id">
      <text>加载中...</text>
    </view>
    <template v-else>
      <!-- 主题头部 -->
      <view class="topic-header-card">
        <view class="topic-title">{{ topic.title }}</view>
        <view class="topic-meta">
          <image class="avatar" :src="topic.author?.avatar || '/static/logo.png'" mode="aspectFill"></image>
          <view class="meta-info">
            <text class="author-name">{{ topic.author?.username || '匿名用户' }}</text>
            <text class="topic-time">{{ formatTime(topic.created_at) }}</text>
          </view>
          <view class="board-tag" v-if="topic.board_name">
            <text>{{ topic.board_name }}</text>
          </view>
        </view>
      </view>

      <!-- 首贴内容 -->
      <view class="first-post-card" v-if="firstPost">
        <rich-text class="post-content" :nodes="safeFirstPostContent"></rich-text>
        <view class="post-actions">
          <view class="action-item" @click="togglePostLike(firstPost)">
            <text class="icon">{{ firstPost.is_liked ? '❤️' : '🤍' }}</text>
            <text>{{ firstPost.like_count || 0 }}</text>
          </view>
          <view class="action-item" @click="toggleBookmark">
            <text class="icon">{{ isBookmarked ? '🔖' : '📑' }}</text>
            <text>{{ isBookmarked ? '已收藏' : '收藏' }}</text>
          </view>
          <view class="action-item">
            <text class="icon">👁</text>
            <text>{{ topic.views || 0 }}</text>
          </view>
        </view>
      </view>

      <!-- 回复列表 -->
      <view class="reply-section">
        <view class="section-title">回复 ({{ replies.length }})</view>
        <view class="reply-list" v-if="replies.length > 0">
          <view class="reply-item" v-for="reply in replies" :key="reply.id">
            <image class="reply-avatar" :src="reply.author?.avatar || '/static/logo.png'" mode="aspectFill"></image>
            <view class="reply-content">
              <view class="reply-header">
                <text class="reply-author">{{ reply.author?.username || '匿名用户' }}</text>
                <text class="reply-floor">{{ reply.floor }}楼</text>
                <text class="reply-time">{{ formatTime(reply.created_at) }}</text>
              </view>
              <rich-text class="reply-text" :nodes="safeReplyContent(reply.content)"></rich-text>
              <view class="reply-actions">
                <view class="reply-action" @click="togglePostLike(reply)">
                  <text class="icon">{{ reply.is_liked ? '❤️' : '🤍' }}</text>
                  <text>{{ reply.like_count || 0 }}</text>
                </view>
              </view>
            </view>
          </view>
        </view>
        <view class="empty-tip" v-else>
          <text>暂无回复，快来抢沙发吧</text>
        </view>
        <view class="no-more" v-if="replies.length > 0 && noMore">
          <text>没有更多了</text>
        </view>
      </view>

      <!-- 回复输入 -->
      <view class="reply-input-area">
        <input
          type="text"
          v-model="replyContent"
          placeholder="写下你的回复..."
          class="reply-input"
          @confirm="submitReply"
          :disabled="submitting"
        />
        <button class="submit-btn" @click="submitReply" :disabled="!replyContent.trim() || submitting">
          {{ submitting ? '发送中' : '发送' }}
        </button>
      </view>
    </template>
  </view>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { onUnload } from '@dcloudio/uni-app'
import forumApi from '../../api/forum'
import { sanitizeHtml } from '../../utils/xss'

const topicId = ref(null)
const loading = ref(false)
const submitting = ref(false)
const topic = ref({})
const posts = ref([])
const replies = ref([])
const replyContent = ref('')
const isBookmarked = ref(false)
const page = ref(1)
const noMore = ref(false)
let loginRedirectTimer = null

const firstPost = computed(() => {
  return posts.value.find(p => p.is_first_post) || posts.value[0] || null
})

const safeFirstPostContent = computed(() => sanitizeHtml(firstPost.value?.content || ''))
const safeReplyContent = (content) => sanitizeHtml(content || '')

onMounted(() => {
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1]
  const options = currentPage.options || currentPage.$page?.options || {}
  topicId.value = options.id

  if (topicId.value) {
    loadTopicDetail()
    loadTopicPosts()
  } else {
    uni.showToast({ title: '参数错误', icon: 'none' })
  }
})

onUnload(() => {
  if (loginRedirectTimer) {
    clearTimeout(loginRedirectTimer)
    loginRedirectTimer = null
  }
})

const loadTopicDetail = async () => {
  loading.value = true
  try {
    const result = await forumApi.getTopicDetail(topicId.value)
    topic.value = result || {}
    if (result && result.is_bookmarked !== undefined) {
      isBookmarked.value = result.is_bookmarked
    }
  } catch (error) {
    console.error('加载主题详情失败:', error)
    uni.showToast({ title: '加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

const loadTopicPosts = async () => {
  try {
    const result = await forumApi.getTopicPosts(topicId.value, { page: page.value, page_size: 20 })
    let list = []
    if (result && result.results) {
      list = result.results
      noMore.value = !result.next
    } else if (Array.isArray(result)) {
      list = result
      noMore.value = true
    }

    posts.value = list
    replies.value = list.filter(p => !p.is_first_post).map((p, index) => ({
      ...p,
      floor: index + 2
    }))
  } catch (error) {
    console.error('加载帖子列表失败:', error)
  }
}

const togglePostLike = async (post) => {
  if (!post || !post.id) return

  const token = uni.getStorageSync('accessToken')
  if (!token) {
    uni.showToast({ title: '请先登录', icon: 'none' })
    loginRedirectTimer = setTimeout(() => uni.navigateTo({ url: '/pages/login/login' }), 1000)
    return
  }

  try {
    if (post.is_liked) {
      await forumApi.unlikePost(post.id)
      post.is_liked = false
      post.like_count = Math.max(0, (post.like_count || 1) - 1)
    } else {
      await forumApi.likePost(post.id)
      post.is_liked = true
      post.like_count = (post.like_count || 0) + 1
    }
  } catch (error) {
    console.error('点赞操作失败:', error)
    uni.showToast({ title: '操作失败', icon: 'none' })
  }
}

const toggleBookmark = async () => {
  const token = uni.getStorageSync('accessToken')
  if (!token) {
    uni.showToast({ title: '请先登录', icon: 'none' })
    loginRedirectTimer = setTimeout(() => uni.navigateTo({ url: '/pages/login/login' }), 1000)
    return
  }

  try {
    if (isBookmarked.value) {
      await forumApi.unbookmarkTopic(topicId.value)
      isBookmarked.value = false
      uni.showToast({ title: '已取消收藏', icon: 'success' })
    } else {
      await forumApi.bookmarkTopic(topicId.value)
      isBookmarked.value = true
      uni.showToast({ title: '收藏成功', icon: 'success' })
    }
  } catch (error) {
    console.error('收藏操作失败:', error)
    uni.showToast({ title: '操作失败', icon: 'none' })
  }
}

const submitReply = async () => {
  if (!replyContent.value.trim()) return

  const token = uni.getStorageSync('accessToken')
  if (!token) {
    uni.showToast({ title: '请先登录', icon: 'none' })
    loginRedirectTimer = setTimeout(() => uni.navigateTo({ url: '/pages/login/login' }), 1000)
    return
  }

  if (topic.value.is_closed) {
    uni.showToast({ title: '该主题已关闭', icon: 'none' })
    return
  }

  submitting.value = true
  try {
    await forumApi.replyTopic({ topic: topicId.value, content: replyContent.value })
    uni.showToast({ title: '回复成功', icon: 'success' })
    replyContent.value = ''
    page.value = 1
    await loadTopicPosts()
  } catch (error) {
    console.error('回复失败:', error)
    uni.showToast({ title: '回复失败', icon: 'none' })
  } finally {
    submitting.value = false
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

onPullDownRefresh(() => {
  page.value = 1
  loadTopicDetail()
  loadTopicPosts().finally(() => {
    uni.stopPullDownRefresh()
  })
})
</script>

<style scoped>
.container {
  min-height: 100vh;
  background-color: #f5f5f5;
  padding-bottom: 120rpx;
}

.loading {
  text-align: center;
  padding: 100rpx;
  color: #999;
}

.topic-header-card {
  background-color: #fff;
  padding: 30rpx;
}

.topic-title {
  font-size: 36rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 20rpx;
  line-height: 1.5;
}

.topic-meta {
  display: flex;
  align-items: center;
}

.avatar {
  width: 70rpx;
  height: 70rpx;
  border-radius: 50%;
  margin-right: 20rpx;
}

.meta-info {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.author-name {
  font-size: 28rpx;
  color: #333;
  font-weight: 500;
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

.first-post-card {
  background-color: #fff;
  padding: 30rpx;
  margin-top: 20rpx;
}

.post-content {
  font-size: 28rpx;
  color: #333;
  line-height: 1.8;
}

.post-actions {
  display: flex;
  padding-top: 30rpx;
  margin-top: 30rpx;
  border-top: 1rpx solid #f0f0f0;
}

.action-item {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10rpx;
  font-size: 26rpx;
  color: #666;
}

.reply-section {
  background-color: #fff;
  padding: 30rpx;
  margin-top: 20rpx;
  min-height: 300rpx;
}

.section-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 20rpx;
}

.reply-list {
  display: flex;
  flex-direction: column;
  gap: 30rpx;
}

.reply-item {
  display: flex;
}

.reply-avatar {
  width: 60rpx;
  height: 60rpx;
  border-radius: 50%;
  margin-right: 20rpx;
}

.reply-content {
  flex: 1;
}

.reply-header {
  display: flex;
  align-items: center;
  margin-bottom: 10rpx;
}

.reply-author {
  font-size: 28rpx;
  color: #333;
  font-weight: 500;
  margin-right: 15rpx;
}

.reply-floor {
  font-size: 22rpx;
  color: #4361ee;
  background-color: #e8f5e9;
  padding: 2rpx 10rpx;
  border-radius: 6rpx;
  margin-right: 15rpx;
}

.reply-time {
  font-size: 24rpx;
  color: #999;
}

.reply-text {
  font-size: 28rpx;
  color: #333;
  line-height: 1.6;
}

.reply-actions {
  display: flex;
  margin-top: 15rpx;
}

.reply-action {
  display: flex;
  align-items: center;
  gap: 8rpx;
  font-size: 24rpx;
  color: #999;
}

.empty-tip {
  text-align: center;
  padding: 60rpx 30rpx;
  color: #999;
  font-size: 28rpx;
}

.no-more {
  text-align: center;
  padding: 30rpx;
  color: #999;
  font-size: 26rpx;
}

.reply-input-area {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  align-items: center;
  padding: 20rpx 30rpx;
  background-color: #fff;
  box-shadow: 0 -2rpx 10rpx rgba(0, 0, 0, 0.05);
}

.reply-input {
  flex: 1;
  height: 70rpx;
  background-color: #f5f5f5;
  border-radius: 35rpx;
  padding: 0 30rpx;
  font-size: 28rpx;
}

.submit-btn {
  width: 120rpx;
  height: 70rpx;
  background-color: #4361ee;
  color: #fff;
  border-radius: 35rpx;
  font-size: 28rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-left: 20rpx;
  border: none;
}

.submit-btn[disabled] {
  background-color: #ccc;
}
</style>
