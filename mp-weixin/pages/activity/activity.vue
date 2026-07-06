<template>
  <view class="container">
    <view class="header">
      <text class="title">个人动态</text>
    </view>

    <view class="tabs">
      <view
        v-for="tab in tabs"
        :key="tab.value"
        class="tab-item"
        :class="{ active: activeTab === tab.value }"
        @click="switchTab(tab.value)"
      >
        {{ tab.label }}
      </view>
    </view>

    <view class="create-bar" @click="openCreateForm">
      <text class="create-text">分享新鲜事...</text>
      <text class="create-btn">发布</text>
    </view>

    <scroll-view class="activity-list" scroll-y @scrolltolower="loadMore" refresher-enabled :refresher-triggered="refreshing" @refresherrefresh="onRefresh">
      <view v-if="loading && activities.length === 0" class="loading">
        <view class="spinner"></view>
        <text>加载中...</text>
      </view>

      <view v-else-if="activities.length === 0" class="empty">
        <text>暂无动态，快来发布第一条动态吧！</text>
      </view>

      <view
        v-else
        v-for="activity in activities"
        :key="activity.id"
        class="activity-item"
      >
        <view class="activity-header">
          <image
            class="author-avatar"
            :src="activity.user?.avatar || '/static/logo.png'"
            mode="aspectFill"
          />
          <view class="author-info">
            <text class="author-name">{{ activity.user?.username || '匿名用户' }}</text>
            <text class="activity-type">{{ getActivityTypeText(activity.activity_type) }}</text>
            <text class="activity-time">{{ formatTime(activity.created_at) }}</text>
          </view>
        </view>

        <view class="activity-body">
          <text class="activity-content">{{ activity.content }}</text>
          <view v-if="activity.target_title" class="activity-target" @click="goToTarget(activity)">
            <text>{{ activity.target_title }}</text>
          </view>
        </view>

        <view class="activity-actions">
          <view
            class="action-btn"
            :class="{ liked: activity.is_liked }"
            @click="toggleLike(activity)"
          >
            <text>❤️ {{ activity.likes_count || 0 }}</text>
          </view>
          <view class="action-btn" @click="toggleComments(activity)">
            <text>💬 {{ activity.comments_count || 0 }}</text>
          </view>
        </view>

        <!-- 评论区域 -->
        <view v-if="expandedActivity === activity.id" class="activity-comments">
          <view v-if="activity.comments && activity.comments.length > 0" class="comments-list">
            <view
              v-for="comment in activity.comments"
              :key="comment.id"
              class="comment-item"
            >
              <image
                class="comment-avatar"
                :src="comment.user?.avatar || '/static/logo.png'"
                mode="aspectFill"
              />
              <view class="comment-main">
                <view class="comment-header">
                  <text class="comment-user">{{ comment.user?.username || '匿名用户' }}</text>
                  <text class="comment-time">{{ formatTime(comment.created_at) }}</text>
                </view>
                <text class="comment-content">{{ comment.content }}</text>
              </view>
            </view>
          </view>
          <view v-else class="no-comments">
            <text>暂无评论</text>
          </view>

          <view class="comment-form">
            <input
              v-model="commentForm.content"
              class="comment-input"
              placeholder="写下你的评论..."
            />
            <view class="submit-btn" @click="submitComment(activity.id)">发送</view>
          </view>
        </view>
      </view>

      <view v-if="activities.length > 0" class="load-more">
        <text v-if="loadingMore" class="load-text">加载中...</text>
        <text v-else-if="hasMore" class="load-text" @click="loadMore">加载更多</text>
        <text v-else class="load-text no-more">没有更多了</text>
      </view>
    </scroll-view>

    <!-- 发布动态弹窗 -->
    <view v-if="showCreateForm" class="create-modal" @click="closeCreateForm">
      <view class="create-panel" @click.stop>
        <view class="create-panel-header">
          <text class="panel-title">发布动态</text>
          <text class="close-btn" @click="closeCreateForm">×</text>
        </view>
        <textarea
          v-model="activityForm.content"
          class="create-textarea"
          placeholder="分享你的想法..."
          maxlength="500"
        />
        <view class="create-options">
          <text class="option-label">是否公开</text>
          <switch :checked="activityForm.is_public" @change="onPublicChange" color="#4361ee" />
        </view>
        <button class="submit-create-btn" :disabled="!activityForm.content.trim() || creating" @click="createActivity">
          {{ creating ? '发布中...' : '发布' }}
        </button>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import userApi from '../../api/user'

const tabs = [
  { label: '关注动态', value: 'feed' },
  { label: '我的动态', value: 'my' },
  { label: '全部动态', value: 'all' }
]

const activeTab = ref('feed')
const activities = ref([])
const loading = ref(false)
const loadingMore = ref(false)
const refreshing = ref(false)
const page = ref(1)
const pageSize = 10
const hasMore = ref(true)
const showCreateForm = ref(false)
const creating = ref(false)
const expandedActivity = ref(null)

const activityForm = ref({
  activity_type: 'custom',
  content: '',
  is_public: true
})

const commentForm = ref({
  content: '',
  parent: undefined
})

onMounted(() => {
  loadActivities(true)
})

const switchTab = (tab) => {
  activeTab.value = tab
  loadActivities(true)
}

const loadActivities = async (reset = false) => {
  if (reset) {
    page.value = 1
    activities.value = []
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
    let response
    if (activeTab.value === 'feed') {
      response = await userApi.getActivityFeed()
    } else if (activeTab.value === 'my') {
      response = await userApi.getMyActivities()
    } else {
      response = await userApi.getActivities({ page: page.value, page_size: pageSize })
    }
    const list = response.results || []
    activities.value = reset ? list : [...activities.value, ...list]
    hasMore.value = list.length === pageSize
    page.value++
  } catch (error) {
    console.error('加载动态失败:', error)
    uni.showToast({ title: '加载动态失败', icon: 'none' })
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

const loadMore = () => {
  loadActivities(false)
}

const onRefresh = () => {
  refreshing.value = true
  loadActivities(true).finally(() => {
    refreshing.value = false
  })
}

const getActivityTypeText = (type) => {
  const typeMap = {
    post: '发布了帖子',
    comment: '发表了评论',
    like: '点赞了内容',
    follow: '关注了用户',
    enroll: '报名了课程',
    share: '分享了内容',
    custom: '发布了动态'
  }
  return typeMap[type] || type
}

const openCreateForm = () => {
  const token = uni.getStorageSync('accessToken')
  if (!token) {
    uni.showToast({ title: '请先登录', icon: 'none' })
    return
  }
  showCreateForm.value = true
}

const closeCreateForm = () => {
  showCreateForm.value = false
  activityForm.value = {
    activity_type: 'custom',
    content: '',
    is_public: true
  }
}

const onPublicChange = (e) => {
  activityForm.value.is_public = e.detail.value
}

const createActivity = async () => {
  if (!activityForm.value.content.trim()) return
  creating.value = true
  try {
    await userApi.createActivity(activityForm.value)
    uni.showToast({ title: '发布成功', icon: 'success' })
    closeCreateForm()
    if (activeTab.value !== 'all') {
      activeTab.value = 'my'
    }
    loadActivities(true)
  } catch (error) {
    console.error('发布动态失败:', error)
    uni.showToast({ title: '发布失败', icon: 'none' })
  } finally {
    creating.value = false
  }
}

const toggleLike = async (activity) => {
  const token = uni.getStorageSync('accessToken')
  if (!token) {
    uni.showToast({ title: '请先登录', icon: 'none' })
    return
  }
  try {
    if (activity.is_liked) {
      await userApi.unlikeActivity(activity.id)
      activity.is_liked = false
      activity.likes_count = Math.max(0, (activity.likes_count || 1) - 1)
    } else {
      await userApi.likeActivity(activity.id)
      activity.is_liked = true
      activity.likes_count = (activity.likes_count || 0) + 1
    }
  } catch (error) {
    console.error('点赞操作失败:', error)
    uni.showToast({ title: '操作失败', icon: 'none' })
  }
}

const toggleComments = async (activity) => {
  if (expandedActivity.value === activity.id) {
    expandedActivity.value = null
  } else {
    expandedActivity.value = activity.id
    if (!activity.comments) {
      try {
        const comments = await userApi.getActivityComments(activity.id)
        activity.comments = comments.results || []
      } catch (error) {
        console.error('加载评论失败:', error)
        activity.comments = []
      }
    }
  }
}

const submitComment = async (activityId) => {
  const token = uni.getStorageSync('accessToken')
  if (!token) {
    uni.showToast({ title: '请先登录', icon: 'none' })
    return
  }
  if (!commentForm.value.content.trim()) return
  try {
    await userApi.createActivityComment({
      activity: activityId,
      content: commentForm.value.content,
      parent: commentForm.value.parent
    })
    commentForm.value.content = ''
    const activity = activities.value.find(a => a.id === activityId)
    if (activity) {
      activity.comments_count = (activity.comments_count || 0) + 1
      activity.comments = undefined
      toggleComments(activity)
      toggleComments(activity)
    }
    uni.showToast({ title: '评论成功', icon: 'success' })
  } catch (error) {
    console.error('发表评论失败:', error)
    uni.showToast({ title: '评论失败', icon: 'none' })
  }
}

const goToTarget = (activity) => {
  if (activity.target_url) {
    // 小程序内不处理外部链接
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

.header {
  background: linear-gradient(135deg, #9b59b6, #8e44ad);
  padding: 40rpx 30rpx;
  text-align: center;
}

.title {
  font-size: 36rpx;
  font-weight: 600;
  color: #fff;
}

.tabs {
  display: flex;
  background-color: #fff;
  padding: 20rpx 30rpx;
  gap: 16rpx;
}

.tab-item {
  flex: 1;
  text-align: center;
  padding: 16rpx 0;
  font-size: 28rpx;
  color: #666;
  background-color: #f3f4f6;
  border-radius: 12rpx;
}

.tab-item.active {
  background-color: #9b59b6;
  color: #fff;
  font-weight: 500;
}

.create-bar {
  display: flex;
  align-items: center;
  margin: 20rpx 30rpx;
  padding: 20rpx 24rpx;
  background-color: #fff;
  border-radius: 16rpx;
}

.create-text {
  flex: 1;
  font-size: 28rpx;
  color: #999;
}

.create-btn {
  padding: 10rpx 24rpx;
  font-size: 26rpx;
  color: #fff;
  background-color: #4361ee;
  border-radius: 12rpx;
}

.activity-list {
  flex: 1;
  padding: 0 30rpx 20rpx;
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

.activity-item {
  background-color: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
  margin-bottom: 20rpx;
}

.activity-header {
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

.activity-type,
.activity-time {
  font-size: 22rpx;
  color: #999;
}

.activity-body {
  margin-bottom: 16rpx;
}

.activity-content {
  display: block;
  font-size: 28rpx;
  color: #333;
  line-height: 1.6;
  margin-bottom: 12rpx;
}

.activity-target {
  padding: 16rpx;
  background-color: #f5f7fa;
  border-left: 6rpx solid #4361ee;
  border-radius: 8rpx;
}

.activity-target text {
  font-size: 26rpx;
  color: #4361ee;
}

.activity-actions {
  display: flex;
  gap: 30rpx;
  padding-top: 16rpx;
  border-top: 1rpx solid #f0f0f0;
}

.action-btn {
  font-size: 26rpx;
  color: #666;
}

.action-btn.liked {
  color: #ef4444;
}

.activity-comments {
  margin-top: 20rpx;
  padding-top: 20rpx;
  border-top: 1rpx solid #f0f0f0;
}

.comments-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
  margin-bottom: 16rpx;
}

.comment-item {
  display: flex;
  gap: 16rpx;
}

.comment-avatar {
  width: 56rpx;
  height: 56rpx;
  border-radius: 50%;
  background-color: #eee;
}

.comment-main {
  flex: 1;
  background-color: #f5f7fa;
  border-radius: 12rpx;
  padding: 16rpx;
}

.comment-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8rpx;
}

.comment-user {
  font-size: 24rpx;
  font-weight: 500;
  color: #333;
}

.comment-time {
  font-size: 20rpx;
  color: #999;
}

.comment-content {
  font-size: 26rpx;
  color: #666;
  line-height: 1.5;
}

.no-comments {
  text-align: center;
  padding: 30rpx 0;
  color: #999;
  font-size: 26rpx;
}

.comment-form {
  display: flex;
  gap: 16rpx;
  align-items: center;
}

.comment-input {
  flex: 1;
  height: 72rpx;
  background-color: #f3f4f6;
  border-radius: 12rpx;
  padding: 0 20rpx;
  font-size: 26rpx;
}

.submit-btn {
  padding: 16rpx 28rpx;
  font-size: 26rpx;
  color: #fff;
  background-color: #4361ee;
  border-radius: 12rpx;
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

.create-modal {
  position: fixed;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
  padding: 30rpx;
}

.create-panel {
  width: 100%;
  background-color: #fff;
  border-radius: 24rpx;
  padding: 30rpx;
}

.create-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20rpx;
}

.panel-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
}

.close-btn {
  font-size: 48rpx;
  color: #999;
  line-height: 1;
}

.create-textarea {
  width: 100%;
  height: 240rpx;
  background-color: #f3f4f6;
  border-radius: 12rpx;
  padding: 20rpx;
  font-size: 28rpx;
}

.create-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 20rpx 0;
}

.option-label {
  font-size: 28rpx;
  color: #666;
}

.submit-create-btn {
  width: 100%;
  height: 80rpx;
  line-height: 80rpx;
  background-color: #10b981;
  color: #fff;
  font-size: 28rpx;
  border-radius: 12rpx;
}

.submit-create-btn:disabled {
  background-color: #9ca3af;
}
</style>
