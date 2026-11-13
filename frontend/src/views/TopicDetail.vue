<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { forumApi } from '../api/forum'
import { sanitizeHtml } from '../utils/xss'
import type { Topic, Post } from '../types/forum'
import GlassCard from '../components/GlassCard.vue'

// 路由
const route = useRoute()
const router = useRouter()

// 帖子和主题数据
const topic = ref<Topic | null>(null)
const posts = ref<Post[]>([])
const firstPost = ref<Post | null>(null)

// 举报相关
const showReportModal = ref(false)
const reportedPostId = ref<number | null>(null)
const reportReason = ref('')

// 计算属性：回复帖子（非首帖）
const replyPosts = computed(() => {
  return posts.value.filter(p => p && !p.is_first_post)
})

// 加载状态
const loading = ref(true)
const error = ref<string | null>(null)

// 点赞帖子
const toggleLikePost = async (postId: number) => {
  try {
    const post = posts.value.find(p => p.id === postId)
    if (!post) return

    if (post.is_liked) {
      await forumApi.unlikePost(postId)
      post.is_liked = false
      post.like_count = (post.like_count || 1) - 1
    } else {
      await forumApi.likePost(postId)
      post.is_liked = true
      post.like_count = (post.like_count || 0) + 1
    }
  } catch (err) {
    console.error('点赞失败:', err)
    alert('操作失败，请稍后重试')
  }
}

// 打开举报弹窗
const openReportModal = (postId: number) => {
  reportedPostId.value = postId
  reportReason.value = ''
  showReportModal.value = true
}

// 关闭举报弹窗
const closeReportModal = () => {
  showReportModal.value = false
  reportedPostId.value = null
  reportReason.value = ''
}

// 提交举报
const submitReport = async () => {
  if (!reportedPostId.value || !reportReason.value.trim()) {
    alert('请填写举报原因')
    return
  }

  try {
    await forumApi.reportPost(reportedPostId.value, reportReason.value)
    alert('举报成功，管理员将尽快处理')
    closeReportModal()
  } catch (err) {
    console.error('举报失败:', err)
    alert('举报失败，请稍后重试')
  }
}

// 格式化时间
const formatTime = (dateStr: string | undefined) => {
  if (!dateStr) return '未知'
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  if (diff < 24 * 60 * 60 * 1000) {
    const hours = Math.floor(diff / (60 * 60 * 1000))
    if (hours === 0) {
      const minutes = Math.floor(diff / (60 * 1000))
      return minutes <= 0 ? '刚刚' : `${minutes}分钟前`
    }
    return `${hours}小时前`
  }
  if (diff < 7 * 24 * 60 * 60 * 1000) {
    const days = ['日', '一', '二', '三', '四', '五', '六']
    return `星期${days[date.getDay()]} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
  }
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

// 返回版块
const goBack = () => {
  if (topic.value?.board) {
    router.push(`/forum/board/${topic.value.board}`)
  } else {
    router.push('/forum')
  }
}

// 加载主题和帖子
const loadTopicAndPosts = async () => {
  const topicId = Number(route.params.id)
  if (!topicId) {
    error.value = '主题ID不存在'
    loading.value = false
    return
  }

  loading.value = true
  error.value = null
  try {
    // 获取主题信息
    topic.value = await forumApi.getTopic(topicId)

    // 获取主题的所有帖子
    const response = await forumApi.getTopicPosts(topicId, 1)
    posts.value = response.results

    // 设置首帖
    firstPost.value = posts.value.find(p => p.is_first_post) || null
  } catch (err) {
    console.error('加载主题失败:', err)
    error.value = '加载失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

// 初始加载
onMounted(() => {
  loadTopicAndPosts()
})
</script>

<template>
  <div class="topic-detail-page container-medium page-padding">
    <div v-if="loading" class="loading-state">
      <div class="loading-spinner"></div>
      <p>加载中...</p>
    </div>

    <div v-else-if="error" class="error-state">
      <span class="i-ep-warning error-icon" />
      <p>{{ error }}</p>
      <button class="btn btn-primary" @click="loadTopicAndPosts">重新加载</button>
    </div>

    <template v-else-if="topic && firstPost">
      <!-- 面包屑与标题 -->
      <div class="topic-header">
        <button class="back-link" @click="goBack">
          <span class="i-ep-arrow-left" />
          返回版块
        </button>
        <h1 class="topic-title">{{ topic.title }}</h1>
        <div class="topic-meta">
          <div class="author-info">
            <img
              v-if="firstPost.author.avatar"
              :src="firstPost.author.avatar"
              alt="avatar"
              class="author-avatar"
            />
            <div v-else class="author-avatar-placeholder">
              {{ firstPost.author.username.substring(0, 1) }}
            </div>
            <span class="author-name">{{ firstPost.author.username }}</span>
            <span class="post-time">{{ formatTime(firstPost.created_at) }}</span>
          </div>
          <div class="topic-stats">
            <span class="stat-item">
              <span class="i-ep-view stat-icon" />
              {{ topic.views || 0 }} 浏览
            </span>
            <span class="stat-item">
              <span class="i-ep-chat-dot-round stat-icon" />
              {{ replyPosts.length }} 回复
            </span>
          </div>
        </div>
      </div>

      <!-- 首帖 -->
      <GlassCard :hover="false" class="post first-post">
        <div class="post-content">
          <div class="post-body rich-content" v-html="sanitizeHtml(firstPost.content)"></div>
          <div v-if="firstPost.is_edited" class="post-edited-info">
            已编辑于 {{ formatTime(firstPost.edited_at) }}
          </div>
          <div class="post-actions">
            <button
              class="btn-like"
              :class="{ liked: firstPost.is_liked }"
              @click="toggleLikePost(firstPost.id)"
            >
              <span class="i-ep-thumb stat-icon" />
              <span>{{ firstPost.like_count || 0 }}</span>
            </button>
            <button class="btn-report" @click="openReportModal(firstPost.id)">
              <span class="i-ep-warning stat-icon" />
              <span>举报</span>
            </button>
          </div>
        </div>
      </GlassCard>

      <!-- 回复列表 -->
      <div v-if="replyPosts.length > 0" class="replies-section">
        <h2 class="replies-title">
          <span class="i-ep-chat-dot-round" />
          全部回复 ({{ replyPosts.length }})
        </h2>
        <GlassCard
          v-for="post in replyPosts"
          :key="post.id"
          :hover="false"
          class="post reply-post"
        >
          <div class="reply-header">
            <div class="author-info">
              <img
                v-if="post.author.avatar"
                :src="post.author.avatar"
                alt="avatar"
                class="author-avatar small"
              />
              <div v-else class="author-avatar-placeholder small">
                {{ post.author.username.substring(0, 1) }}
              </div>
              <span class="author-name">{{ post.author.username }}</span>
              <span class="post-time">{{ formatTime(post.created_at) }}</span>
            </div>
          </div>
          <div class="post-content">
            <div class="post-body rich-content" v-html="sanitizeHtml(post.content)"></div>

            <div v-if="post.content_status !== 'approved'" class="post-status-info">
              <span class="status-badge" :class="post.content_status">
                {{ post.content_status }}
              </span>
              <span v-if="post.review_note" class="review-note">
                审核备注: {{ post.review_note }}
              </span>
            </div>

            <div v-if="post.is_edited" class="post-edited-info">
              已编辑于 {{ formatTime(post.edited_at) }}
            </div>
            <div class="post-actions">
              <button
                class="btn-like"
                :class="{ liked: post.is_liked }"
                @click="toggleLikePost(post.id)"
              >
                <span class="i-ep-thumb stat-icon" />
                <span>{{ post.like_count || 0 }}</span>
              </button>
              <button class="btn-report" @click="openReportModal(post.id)">
                <span class="i-ep-warning stat-icon" />
                <span>举报</span>
              </button>
            </div>
          </div>
        </GlassCard>
      </div>
    </template>

    <div v-else class="error-state">
      <span class="i-ep-warning error-icon" />
      <p>主题不存在或已被删除</p>
      <button class="btn btn-primary" @click="router.push('/forum')">返回论坛</button>
    </div>

    <!-- 举报弹窗 -->
    <div v-if="showReportModal" class="modal-overlay" @click.self="closeReportModal">
      <GlassCard :hover="false" class="modal-content">
        <h3>举报帖子</h3>
        <div class="report-form">
          <label>举报原因</label>
          <textarea
            v-model="reportReason"
            placeholder="请描述举报原因..."
            rows="4"
          ></textarea>
          <div class="modal-actions">
            <button class="btn btn-secondary" @click="closeReportModal">取消</button>
            <button class="btn btn-danger" @click="submitReport">提交举报</button>
          </div>
        </div>
      </GlassCard>
    </div>
  </div>
</template>

<style scoped>
.topic-detail-page {
  color: var(--text-primary);
}

.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 5rem 0;
  color: var(--text-secondary);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--primary-200);
  border-top-color: var(--primary-600);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  color: var(--warning-color);
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.625rem 1.25rem;
  border-radius: var(--radius-md);
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: all 0.2s;
}

.btn-primary {
  background-color: var(--primary-600);
  color: white;
}

.btn-primary:hover {
  background-color: var(--primary-700);
}

.btn-secondary {
  background-color: var(--bg-tertiary);
  color: var(--text-primary);
}

.btn-secondary:hover {
  background-color: var(--border-color);
}

.btn-danger {
  background-color: var(--error-color);
  color: white;
}

.btn-danger:hover {
  background-color: #dc2626;
}

.topic-header {
  margin-bottom: 1.5rem;
}

.back-link {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 0.875rem;
  margin-bottom: 0.75rem;
  padding: 0;
  transition: color 0.2s;
}

.back-link:hover {
  color: var(--primary-600);
}

.topic-title {
  font-size: 1.75rem;
  font-weight: 700;
  margin-bottom: 1rem;
  line-height: 1.3;
}

.topic-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
}

.author-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.author-avatar,
.author-avatar-placeholder {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
}

.author-avatar.small,
.author-avatar-placeholder.small {
  width: 36px;
  height: 36px;
}

.author-avatar-placeholder {
  background: linear-gradient(135deg, var(--primary-500), var(--primary-700));
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
}

.author-name {
  font-weight: 600;
  color: var(--text-primary);
}

.post-time {
  color: var(--text-tertiary);
  font-size: 0.875rem;
}

.topic-stats {
  display: flex;
  gap: 1rem;
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 0.375rem;
}

.stat-icon {
  color: var(--text-tertiary);
}

.post {
  margin-bottom: 1rem;
}

.post-content {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.post-body {
  line-height: 1.8;
  font-size: 1rem;
  color: var(--text-primary);
}

.rich-content :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: var(--radius-md);
  margin: 1rem 0;
}

.rich-content :deep(p) {
  margin-bottom: 1rem;
}

.rich-content :deep(h1),
.rich-content :deep(h2),
.rich-content :deep(h3),
.rich-content :deep(h4),
.rich-content :deep(h5),
.rich-content :deep(h6) {
  margin-top: 1.5rem;
  margin-bottom: 1rem;
  line-height: 1.25;
  font-weight: 600;
}

.rich-content :deep(blockquote) {
  padding: 0 1em;
  color: var(--text-secondary);
  border-left: 0.25em solid var(--border-color);
  margin: 1rem 0;
}

.rich-content :deep(pre) {
  background-color: var(--bg-tertiary);
  border-radius: var(--radius-md);
  padding: 1rem;
  overflow: auto;
  margin: 1rem 0;
}

.rich-content :deep(code) {
  background-color: var(--bg-tertiary);
  border-radius: var(--radius-sm);
  padding: 0.2em 0.4em;
  font-family: SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace;
}

.rich-content :deep(a) {
  color: var(--primary-600);
}

.post-edited-info {
  font-size: 0.75rem;
  color: var(--text-tertiary);
  font-style: italic;
}

.post-actions {
  display: flex;
  gap: 0.75rem;
}

.btn-like,
.btn-report {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.5rem 1rem;
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-full);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.875rem;
}

.btn-like:hover {
  border-color: var(--primary-500);
  color: var(--primary-600);
}

.btn-like.liked {
  background-color: var(--primary-50);
  border-color: var(--primary-500);
  color: var(--primary-600);
}

.btn-report:hover {
  border-color: var(--error-color);
  color: var(--error-color);
}

.post-status-info {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
}

.status-badge {
  display: inline-flex;
  align-self: flex-start;
  padding: 0.25rem 0.5rem;
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-weight: 500;
  color: white;
  text-transform: uppercase;
}

.status-badge.pending {
  background-color: var(--warning-color);
}

.status-badge.rejected {
  background-color: var(--error-color);
}

.status-badge.flagged {
  background-color: var(--accent-orange);
}

.status-badge.approved {
  background-color: var(--success-color);
}

.review-note {
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.replies-section {
  margin-top: 2rem;
}

.replies-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.25rem;
  font-weight: 700;
  margin-bottom: 1rem;
  color: var(--text-primary);
}

.reply-post {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.reply-header {
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--border-color-light);
}

/* 弹窗样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal-content {
  width: 100%;
  max-width: 450px;
}

.modal-content h3 {
  margin: 0 0 1.25rem;
  font-size: 1.25rem;
  color: var(--text-primary);
}

.report-form {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.report-form label {
  font-weight: 500;
  color: var(--text-primary);
}

.report-form textarea {
  padding: 0.75rem 1rem;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  font-size: 0.875rem;
  resize: vertical;
  background: var(--bg-primary);
  color: var(--text-primary);
}

.report-form textarea:focus {
  outline: none;
  border-color: var(--primary-500);
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 1rem;
}

@media (max-width: 768px) {
  .topic-title {
    font-size: 1.4rem;
  }

  .topic-meta {
    flex-direction: column;
    align-items: flex-start;
  }

  .topic-stats {
    width: 100%;
    justify-content: flex-start;
  }
}
</style>
