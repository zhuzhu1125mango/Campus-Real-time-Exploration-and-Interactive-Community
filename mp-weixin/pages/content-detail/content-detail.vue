<template>
  <view class="container">
    <view class="loading-state" v-if="loading">
      <text>加载中...</text>
    </view>

    <template v-else-if="content">
      <!-- 内容头部 -->
      <view class="content-header">
        <view class="back-link" @click="goBack">← 返回内容中心</view>
        <view class="content-meta-top">
          <text v-if="content.category" class="category-tag">{{ content.category.name }}</text>
          <text class="content-type">{{ content.content_type?.name }}</text>
          <text v-if="content.status" class="status-tag" :class="statusClass[content.status]">
            {{ statusLabels[content.status] }}
          </text>
        </view>
        <view class="content-title">{{ content.title }}</view>
        <view v-if="isAuthor" class="author-actions">
          <text class="action-btn danger" @click="deleteContent">删除</text>
          <text
            v-if="content.status === 'draft' || content.status === 'rejected'"
            class="action-btn primary"
            @click="submitForReview"
          >
            提交审核
          </text>
          <text
            v-if="content.status === 'pending'"
            class="action-btn"
            @click="withdrawToDraft"
          >
            撤回为草稿
          </text>
        </view>
        <view class="content-author-bar">
          <view class="author-info">
            <text class="author-name">{{ content.author?.username }}</text>
            <text class="publish-time">{{ formatDate(content.created_at) }}</text>
          </view>
          <view class="content-stats">
            <text>{{ content.view_count }} 浏览</text>
            <text>{{ content.like_count }} 点赞</text>
            <text>{{ content.comment_count }} 评论</text>
          </view>
        </view>
        <view class="content-tags" v-if="content.tags && content.tags.length > 0">
          <text v-for="tag in content.tags" :key="tag.id" class="tag-item"># {{ tag.name }}</text>
        </view>
      </view>

      <!-- 内容主体 -->
      <view class="content-body">
        <image
          v-if="content.featured_image"
          class="featured-image"
          :src="content.featured_image"
          mode="widthFix"
        />
        <rich-text class="content-text" :nodes="safeContent"></rich-text>
      </view>

      <!-- 评论区 -->
      <view class="comments-section">
        <view class="section-title">评论 ({{ comments.length }})</view>

        <view v-if="isLoggedIn" class="comment-form">
          <textarea
            v-model="commentText"
            placeholder="写下你的评论..."
            class="comment-input"
          />
          <button
            class="submit-btn"
            :disabled="commentLoading || !commentText.trim()"
            @click="submitComment"
          >
            {{ commentLoading ? '发布中...' : '发布评论' }}
          </button>
        </view>

        <view v-else class="login-tip">
          <text @click="goLogin" class="login-link">登录</text>
          <text>后参与评论</text>
        </view>

        <view v-if="comments.length === 0" class="empty-comments">暂无评论，来说两句吧</view>

        <view v-else class="comment-list">
          <view v-for="comment in comments" :key="comment.id" class="comment-item">
            <view class="comment-header">
              <text class="comment-user">{{ comment.user?.username }}</text>
              <text class="comment-time">{{ formatDate(comment.created_at) }}</text>
            </view>
            <view class="comment-text">{{ comment.content_text }}</view>
          </view>
        </view>
      </view>
    </template>

    <view class="error-state" v-else-if="error">
      <text>{{ error }}</text>
      <button class="retry-btn" @click="loadContent">重新加载</button>
    </view>
  </view>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { onUnload } from '@dcloudio/uni-app'
import contentApi from '../../api/content'
import userApi from '../../api/user'
import { sanitizeHtml } from '../../utils/xss'

const props = defineProps({
  id: {
    type: String,
    default: ''
  }
})

const content = ref(null)
const comments = ref([])
const loading = ref(false)
const commentLoading = ref(false)
const commentText = ref('')
const error = ref('')
const isLoggedIn = ref(false)
const currentUserId = ref(null)
let deleteRedirectTimer = null

const safeContent = computed(() => sanitizeHtml(content.value?.content || ''))

const statusLabels = {
  draft: '草稿',
  pending: '待审核',
  published: '已发布',
  rejected: '已拒绝'
}

const statusClass = {
  draft: 'status-draft',
  pending: 'status-pending',
  published: 'status-published',
  rejected: 'status-rejected'
}

const isAuthor = computed(() => {
  return content.value && currentUserId.value && content.value.author?.id === currentUserId.value
})

onMounted(() => {
  isLoggedIn.value = !!uni.getStorageSync('accessToken')
  if (isLoggedIn.value) {
    loadCurrentUser()
  }
  loadContent()
})

onUnload(() => {
  if (deleteRedirectTimer) {
    clearTimeout(deleteRedirectTimer)
    deleteRedirectTimer = null
  }
})

const loadCurrentUser = async () => {
  try {
    const user = await userApi.getUserInfo()
    currentUserId.value = user.id
  } catch (err) {
    console.error('获取当前用户失败', err)
  }
}

const loadContent = async () => {
  const id = props.id || getQueryId()
  if (!id) {
    error.value = '无效的内容ID'
    return
  }

  loading.value = true
  error.value = ''
  try {
    content.value = await contentApi.getContentDetail(id)
    await loadComments()
  } catch (err) {
    console.error('加载内容详情失败', err)
    error.value = '内容加载失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

const loadComments = async () => {
  if (!content.value) return
  try {
    const res = await contentApi.getComments({ content: content.value.id })
    comments.value = res.results || []
  } catch (err) {
    console.error('加载评论失败', err)
  }
}

const submitComment = async () => {
  if (!content.value || !commentText.value.trim()) return
  commentLoading.value = true
  try {
    await contentApi.createComment({
      content: content.value.id,
      content_text: commentText.value.trim()
    })
    commentText.value = ''
    await loadComments()
    if (content.value) {
      content.value.comment_count += 1
    }
    uni.showToast({ title: '评论成功', icon: 'success' })
  } catch (err) {
    console.error('发表评论失败', err)
    uni.showToast({ title: '发表评论失败', icon: 'none' })
  } finally {
    commentLoading.value = false
  }
}

const getQueryId = () => {
  const pages = getCurrentPages()
  const page = pages[pages.length - 1]
  return page?.options?.id || page?.$route?.query?.id
}

const goBack = () => {
  uni.navigateBack({ delta: 1 })
}

const goLogin = () => {
  uni.navigateTo({ url: '/pages/login/login' })
}

const deleteContent = () => {
  if (!content.value) return
  uni.showModal({
    title: '确认删除',
    content: '删除后无法恢复，是否继续？',
    success: async (res) => {
      if (res.confirm) {
        try {
          await contentApi.deleteContent(content.value.id)
          uni.showToast({ title: '删除成功', icon: 'success' })
          deleteRedirectTimer = setTimeout(() => {
            uni.navigateBack({ delta: 1 })
          }, 800)
        } catch (err) {
          console.error('删除内容失败', err)
          uni.showToast({ title: '删除失败', icon: 'none' })
        }
      }
    }
  })
}

const submitForReview = async () => {
  if (!content.value) return
  try {
    await contentApi.submitContent(content.value.id)
    content.value.status = 'pending'
    uni.showToast({ title: '已提交审核', icon: 'success' })
  } catch (err) {
    console.error('提交审核失败', err)
    uni.showToast({ title: '提交审核失败', icon: 'none' })
  }
}

const withdrawToDraft = async () => {
  if (!content.value) return
  try {
    await contentApi.unpublishContent(content.value.id)
    content.value.status = 'draft'
    uni.showToast({ title: '已撤回为草稿', icon: 'success' })
  } catch (err) {
    console.error('撤回失败', err)
    uni.showToast({ title: '撤回失败', icon: 'none' })
  }
}

const formatDate = (date) => {
  if (!date) return ''
  const d = new Date(date)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}
</script>

<style scoped>
.container {
  min-height: 100vh;
  background-color: #f5f5f5;
  padding-bottom: 40rpx;
}

.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 120rpx;
  color: #999;
}

.retry-btn {
  margin-top: 30rpx;
  background-color: #4361ee;
  color: #fff;
  font-size: 26rpx;
  padding: 12rpx 40rpx;
  border-radius: 30rpx;
  border: none;
}

.content-header {
  background: linear-gradient(135deg, #4361ee 0%, #3a0ca3 100%);
  color: #fff;
  padding: 40rpx 30rpx;
}

.back-link {
  color: rgba(255, 255, 255, 0.85);
  font-size: 26rpx;
  margin-bottom: 20rpx;
}

.content-meta-top {
  display: flex;
  gap: 12rpx;
  margin-bottom: 20rpx;
}

.category-tag,
.content-type {
  background-color: rgba(255, 255, 255, 0.2);
  color: #fff;
  font-size: 22rpx;
  padding: 6rpx 16rpx;
  border-radius: 6rpx;
}

.status-tag {
  font-size: 20rpx;
  padding: 4rpx 12rpx;
  border-radius: 6rpx;
}

.status-draft {
  background-color: rgba(255, 255, 255, 0.25);
  color: #fff;
}

.status-pending {
  background-color: #fff3cd;
  color: #856404;
}

.status-published {
  background-color: #d4edda;
  color: #155724;
}

.status-rejected {
  background-color: #f8d7da;
  color: #721c24;
}

.author-actions {
  display: flex;
  gap: 16rpx;
  margin-bottom: 20rpx;
}

.action-btn {
  font-size: 24rpx;
  padding: 8rpx 20rpx;
  border-radius: 30rpx;
  background-color: rgba(255, 255, 255, 0.2);
  color: #fff;
}

.action-btn.primary {
  background-color: #fff;
  color: #4361ee;
}

.action-btn.danger {
  background-color: rgba(231, 76, 60, 0.2);
  color: #fff;
}

.content-title {
  font-size: 40rpx;
  font-weight: 700;
  line-height: 1.4;
  margin-bottom: 24rpx;
}

.content-author-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16rpx;
  margin-bottom: 16rpx;
}

.author-info {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.author-name {
  font-weight: 600;
}

.publish-time {
  opacity: 0.8;
  font-size: 24rpx;
}

.content-stats {
  display: flex;
  gap: 16rpx;
  opacity: 0.85;
  font-size: 24rpx;
}

.content-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
  margin-top: 16rpx;
}

.tag-item {
  background-color: rgba(255, 255, 255, 0.15);
  font-size: 24rpx;
  padding: 6rpx 14rpx;
  border-radius: 6rpx;
}

.content-body {
  background-color: #fff;
  margin: 20rpx 0;
  padding: 30rpx;
}

.featured-image {
  width: 100%;
  border-radius: 12rpx;
  margin-bottom: 24rpx;
}

.content-text {
  line-height: 1.8;
  color: #333;
  font-size: 30rpx;
}

.comments-section {
  background-color: #fff;
  padding: 30rpx;
}

.section-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 24rpx;
}

.comment-form {
  margin-bottom: 30rpx;
}

.comment-input {
  width: 100%;
  height: 160rpx;
  padding: 20rpx;
  border: 1rpx solid #e0e0e0;
  border-radius: 12rpx;
  font-size: 28rpx;
  margin-bottom: 16rpx;
  box-sizing: border-box;
}

.submit-btn {
  background-color: #4361ee;
  color: #fff;
  font-size: 28rpx;
  padding: 14rpx 40rpx;
  border-radius: 30rpx;
  border: none;
}

.submit-btn:disabled {
  opacity: 0.5;
}

.login-tip {
  background-color: #f9fafc;
  padding: 20rpx;
  border-radius: 12rpx;
  margin-bottom: 30rpx;
  color: #666;
  font-size: 28rpx;
}

.login-link {
  color: #4361ee;
  font-weight: 500;
  margin-right: 8rpx;
}

.empty-comments {
  text-align: center;
  padding: 60rpx;
  color: #999;
  font-size: 28rpx;
}

.comment-list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.comment-item {
  padding: 20rpx;
  background-color: #f9fafc;
  border-radius: 12rpx;
}

.comment-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10rpx;
}

.comment-user {
  font-weight: 600;
  color: #4361ee;
  font-size: 28rpx;
}

.comment-time {
  color: #999;
  font-size: 24rpx;
}

.comment-text {
  color: #333;
  font-size: 28rpx;
  line-height: 1.6;
}
</style>
