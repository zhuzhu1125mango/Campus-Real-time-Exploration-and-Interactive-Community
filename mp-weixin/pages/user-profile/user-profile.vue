<template>
  <view class="container">
    <view class="loading" v-if="loading">
      <text>加载中...</text>
    </view>

    <template v-else>
      <!-- 用户头部信息 -->
      <view class="user-header">
        <image v-if="user.avatar" class="user-avatar" :src="user.avatar" mode="aspectFill"></image>
        <view v-else class="avatar-placeholder">{{ user.username ? user.username.substring(0, 1).toUpperCase() : '?' }}</view>
        <view class="user-info">
        <text class="username">{{ user.username || '未知用户' }}</text>
        <view class="user-meta">
          <text class="join-date">注册于 {{ formatDate(stats.join_date) }}</text>
          <text v-if="user.location" class="location">📍 {{ user.location }}</text>
        </view>
        <text class="user-bio" v-if="user.bio">{{ user.bio }}</text>
      </view>
      <button v-if="canSendMessage" class="msg-btn" @click="goToChat">发私信</button>
    </view>

      <!-- 用户统计 -->
      <view class="user-stats">
        <view class="stat-item">
          <text class="stat-value">{{ stats.topic_count || 0 }}</text>
          <text class="stat-label">主题</text>
        </view>
        <view class="stat-item">
          <text class="stat-value">{{ stats.post_count || 0 }}</text>
          <text class="stat-label">帖子</text>
        </view>
        <view class="stat-item">
          <text class="stat-value">{{ stats.reply_count || 0 }}</text>
          <text class="stat-label">回复</text>
        </view>
      </view>

      <!-- 活跃板块 -->
      <view class="active-boards" v-if="stats.active_boards && stats.active_boards.length > 0">
        <text class="section-title">活跃板块</text>
        <view class="boards-list">
          <view class="board-item" v-for="board in stats.active_boards" :key="board.id" @click="goToBoard(board.id)">
            <text class="board-name">{{ board.name }}</text>
            <text class="board-post-count">{{ board.post_count }} 篇帖子</text>
          </view>
        </view>
      </view>

      <!-- 内容标签页 -->
      <view class="content-tabs">
        <view class="tab-item" :class="{ active: activeTab === 'topics' }" @click="setActiveTab('topics')">主题</view>
        <view class="tab-item" :class="{ active: activeTab === 'posts' }" @click="setActiveTab('posts')">回复</view>
      </view>

      <!-- 主题列表 -->
      <view v-if="activeTab === 'topics'" class="content-list">
        <view class="loading" v-if="loadingTopics">
          <text>加载中...</text>
        </view>
        <view class="empty-tip" v-else-if="topics.length === 0">
          <text>暂无主题</text>
        </view>
        <view v-else>
          <view class="topic-item" v-for="topic in topics" :key="topic.id" @click="goToTopic(topic.id)">
            <view class="topic-header">
              <text class="topic-title">{{ topic.title }}</text>
              <text class="topic-date">{{ formatDate(topic.created_at) }}</text>
            </view>
            <view class="topic-footer">
              <text class="topic-board">{{ topic.board_name || '未知板块' }}</text>
              <view class="topic-stats">
                <text>{{ topic.views || 0 }} 浏览</text>
                <text>{{ topic.reply_count || 0 }} 回复</text>
              </view>
            </view>
          </view>
          <view class="pagination" v-if="topicTotalPages > 1">
            <button class="btn-page" :disabled="topicPage === 1" @click="changePage('topics', topicPage - 1)">上一页</button>
            <text class="page-info">{{ topicPage }} / {{ topicTotalPages }}</text>
            <button class="btn-page" :disabled="topicPage === topicTotalPages" @click="changePage('topics', topicPage + 1)">下一页</button>
          </view>
        </view>
      </view>

      <!-- 帖子列表 -->
      <view v-if="activeTab === 'posts'" class="content-list">
        <view class="loading" v-if="loadingPosts">
          <text>加载中...</text>
        </view>
        <view class="empty-tip" v-else-if="posts.length === 0">
          <text>暂无回复</text>
        </view>
        <view v-else>
          <view class="post-item" v-for="post in posts" :key="post.id" @click="goToPost(post.topic, post.id)">
            <view class="post-header">
              <text class="post-topic">回复：{{ post.topic_title || '未知主题' }}</text>
              <text class="post-date">{{ formatDate(post.created_at) }}</text>
            </view>
            <view class="post-preview">{{ getPostPreview(post.content) }}</view>
            <view class="post-footer" v-if="post.is_edited || post.content_status !== 'approved'">
              <text v-if="post.is_edited" class="post-edited">已编辑于 {{ formatDate(post.edited_at) }}</text>
              <text v-if="post.content_status !== 'approved'" class="status-badge" :class="post.content_status">{{ getStatusText(post.content_status) }}</text>
            </view>
          </view>
          <view class="pagination" v-if="postTotalPages > 1">
            <button class="btn-page" :disabled="postPage === 1" @click="changePage('posts', postPage - 1)">上一页</button>
            <text class="page-info">{{ postPage }} / {{ postTotalPages }}</text>
            <button class="btn-page" :disabled="postPage === postTotalPages" @click="changePage('posts', postPage + 1)">下一页</button>
          </view>
        </view>
      </view>
    </template>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import userApi from '../../api/user'

const userId = ref('me')
const currentUserId = ref(null)
const loading = ref(true)
const isFriend = ref(false)
const user = ref({})
const stats = ref({
  topic_count: 0,
  post_count: 0,
  reply_count: 0,
  active_boards: [],
  join_date: ''
})
const activeTab = ref('topics')

const topics = ref([])
const loadingTopics = ref(false)
const topicPage = ref(1)
const topicTotalCount = ref(0)
const topicTotalPages = ref(1)

const posts = ref([])
const loadingPosts = ref(false)
const postPage = ref(1)
const postTotalCount = ref(0)
const postTotalPages = ref(1)

const canSendMessage = computed(() => {
  return userId.value !== 'me' &&
    Number(userId.value) !== Number(currentUserId.value) &&
    isFriend.value
})

onMounted(() => {
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1]
  const options = currentPage.options || currentPage.$page?.options || {}
  userId.value = options.id || 'me'

  const storedUserInfo = uni.getStorageSync('userInfo')
  if (storedUserInfo) {
    try {
      const info = typeof storedUserInfo === 'string' ? JSON.parse(storedUserInfo) : storedUserInfo
      currentUserId.value = info.id
    } catch (e) {
      console.error('解析用户信息失败', e)
    }
  }

  fetchUserProfile()
})

const fetchUserProfile = async () => {
  loading.value = true
  try {
    const [userResponse, statsResponse] = await Promise.all([
      userApi.getUserProfile(userId.value),
      userApi.getUserProfileStats(userId.value)
    ])
    user.value = userResponse || {}
    stats.value = statsResponse || {}

    if (userId.value !== 'me') {
      checkFriendship()
    }

    await fetchUserTopics()
  } catch (error) {
    console.error('获取用户资料失败:', error)
    uni.showToast({ title: '加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

const fetchUserTopics = async () => {
  loadingTopics.value = true
  try {
    const response = await userApi.getUserTopics(userId.value, topicPage.value)
    topics.value = response.results || []
    topicTotalCount.value = response.count || 0
    topicTotalPages.value = Math.ceil(topicTotalCount.value / 10) || 1
  } catch (error) {
    console.error('获取用户主题失败:', error)
  } finally {
    loadingTopics.value = false
  }
}

const fetchUserPosts = async () => {
  loadingPosts.value = true
  try {
    const response = await userApi.getUserPosts(userId.value, postPage.value)
    posts.value = response.results || []
    postTotalCount.value = response.count || 0
    postTotalPages.value = Math.ceil(postTotalCount.value / 10) || 1
  } catch (error) {
    console.error('获取用户帖子失败:', error)
  } finally {
    loadingPosts.value = false
  }
}

const setActiveTab = (tab) => {
  activeTab.value = tab
  if (tab === 'posts' && posts.value.length === 0) {
    fetchUserPosts()
  }
}

const changePage = async (type, page) => {
  if (type === 'topics') {
    topicPage.value = page
    await fetchUserTopics()
  } else {
    postPage.value = page
    await fetchUserPosts()
  }
}

const goToTopic = (topicId) => {
  uni.navigateTo({ url: `/pages/post-detail/post-detail?id=${topicId}` })
}

const goToPost = (topicId, postId) => {
  uni.navigateTo({ url: `/pages/post-detail/post-detail?id=${topicId}` })
}

const goToBoard = (boardId) => {
  uni.showToast({ title: '板块详情开发中', icon: 'none' })
}

const checkFriendship = async () => {
  try {
    const result = await userApi.checkFriendship(userId.value)
    isFriend.value = result.is_friend || false
  } catch (error) {
    console.error('检查好友关系失败:', error)
    isFriend.value = false
  }
}

const goToChat = () => {
  uni.navigateTo({
    url: `/pages/chat-detail/chat-detail?userId=${userId.value}&username=${encodeURIComponent(user.value.username || '')}`
  })
}

const getPostPreview = (content) => {
  if (!content) return ''
  const plainText = content.replace(/<[^>]+>/g, '')
  return plainText.length > 100 ? plainText.substring(0, 100) + '...' : plainText
}

const getStatusText = (status) => {
  const statusMap = {
    pending: '待审核',
    approved: '已通过',
    rejected: '已拒绝',
    flagged: '已标记'
  }
  return statusMap[status] || status
}

const formatDate = (dateStr) => {
  if (!dateStr) return '未知'
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now - date

  if (diff < 86400000) {
    const hours = Math.floor(diff / (60 * 60 * 1000))
    if (hours === 0) {
      const minutes = Math.floor(diff / (60 * 1000))
      return minutes <= 0 ? '刚刚' : `${minutes}分钟前`
    }
    return `${hours}小时前`
  }

  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}
</script>

<style scoped>
.container {
  min-height: 100vh;
  background-color: #f5f5f5;
  padding-bottom: 30rpx;
}

.loading {
  text-align: center;
  padding: 100rpx;
  color: #999;
}

.user-header {
  background-color: #fff;
  padding: 40rpx 30rpx;
  display: flex;
  align-items: center;
}

.user-avatar,
.avatar-placeholder {
  width: 140rpx;
  height: 140rpx;
  border-radius: 50%;
  margin-right: 30rpx;
}

.avatar-placeholder {
  background-color: #4361ee;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 56rpx;
  font-weight: bold;
}

.user-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.msg-btn {
  margin-left: 20rpx;
  padding: 12rpx 30rpx;
  background-color: #4361ee;
  color: #fff;
  font-size: 26rpx;
  border-radius: 30rpx;
  border: none;
  white-space: nowrap;
}

.username {
  font-size: 36rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 10rpx;
}

.user-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 15rpx;
  margin-bottom: 10rpx;
}

.join-date,
.location {
  font-size: 24rpx;
  color: #999;
}

.user-bio {
  font-size: 26rpx;
  color: #666;
  line-height: 1.4;
}

.user-stats {
  display: flex;
  background-color: #fff;
  margin-top: 20rpx;
  padding: 30rpx 0;
}

.stat-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  border-right: 1rpx solid #eee;
}

.stat-item:last-child {
  border-right: none;
}

.stat-value {
  font-size: 36rpx;
  font-weight: bold;
  color: #4361ee;
  margin-bottom: 8rpx;
}

.stat-label {
  font-size: 26rpx;
  color: #666;
}

.active-boards {
  background-color: #fff;
  margin-top: 20rpx;
  padding: 30rpx;
}

.section-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 20rpx;
  display: block;
}

.boards-list {
  display: flex;
  flex-wrap: wrap;
  gap: 15rpx;
}

.board-item {
  background-color: #f0f9f0;
  padding: 15rpx 25rpx;
  border-radius: 8rpx;
  display: flex;
  flex-direction: column;
}

.board-name {
  font-size: 26rpx;
  color: #333;
  margin-bottom: 5rpx;
}

.board-post-count {
  font-size: 22rpx;
  color: #999;
}

.content-tabs {
  display: flex;
  background-color: #fff;
  margin-top: 20rpx;
  border-bottom: 1rpx solid #eee;
}

.tab-item {
  flex: 1;
  text-align: center;
  padding: 25rpx 0;
  font-size: 30rpx;
  color: #666;
  border-bottom: 4rpx solid transparent;
}

.tab-item.active {
  color: #4361ee;
  border-bottom-color: #4361ee;
  font-weight: 500;
}

.content-list {
  background-color: #fff;
  min-height: 400rpx;
}

.empty-tip {
  text-align: center;
  padding: 80rpx;
  color: #999;
  font-size: 28rpx;
}

.topic-item,
.post-item {
  padding: 25rpx 30rpx;
  border-bottom: 1rpx solid #f0f0f0;
}

.topic-header,
.post-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 15rpx;
}

.topic-title,
.post-topic {
  font-size: 30rpx;
  color: #333;
  font-weight: 500;
  flex: 1;
  margin-right: 20rpx;
}

.topic-date,
.post-date {
  font-size: 24rpx;
  color: #999;
}

.topic-footer,
.post-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 15rpx;
}

.topic-board {
  background-color: #f0f9f0;
  color: #4361ee;
  font-size: 22rpx;
  padding: 5rpx 15rpx;
  border-radius: 4rpx;
}

.topic-stats {
  display: flex;
  gap: 20rpx;
  font-size: 24rpx;
  color: #999;
}

.post-preview {
  font-size: 28rpx;
  color: #666;
  line-height: 1.5;
}

.post-edited {
  font-size: 22rpx;
  color: #999;
  font-style: italic;
}

.status-badge {
  font-size: 22rpx;
  padding: 4rpx 12rpx;
  border-radius: 4rpx;
  color: #fff;
}

.status-badge.pending {
  background-color: #f39c12;
}

.status-badge.rejected {
  background-color: #e74c3c;
}

.status-badge.flagged {
  background-color: #e67e22;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 30rpx;
  gap: 20rpx;
}

.btn-page {
  background-color: #f0f0f0;
  color: #333;
  font-size: 26rpx;
  padding: 10rpx 25rpx;
  border-radius: 8rpx;
  border: none;
}

.btn-page[disabled] {
  color: #ccc;
}

.page-info {
  font-size: 28rpx;
  color: #666;
}
</style>
