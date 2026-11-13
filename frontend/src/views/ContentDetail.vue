<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { contentApi } from '../api/content'
import { useUserStore } from '../stores/userStore'
import { sanitizeHtml } from '../utils/xss'
import type { ContentItem, Comment } from '../types/content'
import GlassCard from '../components/GlassCard.vue'
import SectionHeader from '../components/SectionHeader.vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const content = ref<ContentItem | null>(null)
const comments = ref<Comment[]>([])
const loading = ref(false)
const commentLoading = ref(false)
const commentText = ref('')
const error = ref('')

const isLoggedIn = computed(() => userStore.isLoggedIn)
const safeContent = computed(() => content.value ? sanitizeHtml(content.value.content) : '')

const loadContent = async () => {
  const id = route.params.id as string
  if (!id) return

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
    const response = await contentApi.getComments({ content: content.value.id })
    comments.value = response.results
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
  } catch (err) {
    console.error('发表评论失败', err)
    alert('发表评论失败，请稍后重试')
  } finally {
    commentLoading.value = false
  }
}

const goBack = () => {
  router.push('/content')
}

const formatDate = (date: string) => {
  return new Date(date).toLocaleString('zh-CN')
}

onMounted(() => {
  loadContent()
})
</script>

<template>
  <div class="content-detail-page container-medium page-padding">
    <div v-if="loading" class="loading-state">
      <div class="loading-spinner"></div>
      <p>加载中...</p>
    </div>

    <template v-else-if="content">
      <SectionHeader
        :title="content.title"
        :subtitle="`${content.content_type.name}${content.category ? ' · ' + content.category.name : ''}`"
        icon="i-ep-reading"
        :action="{ label: '返回内容中心', onClick: goBack }"
      />

      <GlassCard :hover="false" class="content-main-card">
        <div class="content-meta-bar">
          <div class="author-info">
            <span class="author-name">{{ content.author.username }}</span>
            <span class="publish-time">{{ formatDate(content.created_at) }}</span>
          </div>
          <div class="content-stats">
            <span class="stat-item">
              <span class="i-ep-view stat-icon" />
              {{ content.view_count }} 浏览
            </span>
            <span class="stat-item">
              <span class="i-ep-thumb stat-icon" />
              {{ content.like_count }} 点赞
            </span>
            <span class="stat-item">
              <span class="i-ep-chat-dot-round stat-icon" />
              {{ content.comment_count }} 评论
            </span>
          </div>
        </div>

        <div v-if="content.tags && content.tags.length > 0" class="content-tags">
          <span v-for="tag in content.tags" :key="tag.id" class="tag-item">
            # {{ tag.name }}
          </span>
        </div>

        <div v-if="content.featured_image" class="featured-image-wrap">
          <img :src="content.featured_image" :alt="content.title" class="featured-image" />
        </div>

        <div class="content-text rich-content" v-html="safeContent"></div>
      </GlassCard>

      <GlassCard :hover="false" class="comments-card">
        <h2 class="comments-title">
          <span class="i-ep-chat-dot-round" />
          评论 ({{ comments.length }})
        </h2>

        <div v-if="isLoggedIn" class="comment-form">
          <textarea
            v-model="commentText"
            placeholder="写下你的评论..."
            class="comment-input"
            rows="3"
          ></textarea>
          <button
            class="btn btn-primary"
            :disabled="commentLoading || !commentText.trim()"
            @click="submitComment"
          >
            {{ commentLoading ? '发布中...' : '发布评论' }}
          </button>
        </div>

        <div v-else class="login-tip">
          <p>
            <router-link to="/login">登录</router-link>
            后参与评论
          </p>
        </div>

        <div v-if="comments.length === 0" class="empty-comments">
          <span class="i-ep-chat-dot-round empty-icon" />
          <p>暂无评论，来说两句吧</p>
        </div>

        <div v-else class="comment-list">
          <div v-for="comment in comments" :key="comment.id" class="comment-item">
            <div class="comment-header">
              <span class="comment-user">{{ comment.user.username }}</span>
              <span class="comment-time">{{ formatDate(comment.created_at) }}</span>
            </div>
            <p class="comment-text">{{ comment.content_text }}</p>
          </div>
        </div>
      </GlassCard>
    </template>

    <div v-else-if="error" class="error-state">
      <span class="i-ep-warning error-icon" />
      <p>{{ error }}</p>
      <button class="btn btn-primary" @click="loadContent">重新加载</button>
    </div>
  </div>
</template>

<style scoped>
.content-detail-page {
  min-height: calc(100vh - 200px);
}

.content-meta-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-3);
  margin-bottom: var(--space-4);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--border-color-light);
}

.author-info {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.author-name {
  font-weight: 600;
  color: var(--text-primary);
}

.publish-time {
  color: var(--text-tertiary);
  font-size: 0.9rem;
}

.content-stats {
  display: flex;
  gap: var(--space-4);
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.stat-item {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
}

.stat-icon {
  color: var(--text-tertiary);
}

.content-tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  margin-bottom: var(--space-4);
}

.tag-item {
  padding: var(--space-1) var(--space-2);
  background-color: var(--primary-50);
  color: var(--primary-600);
  border-radius: var(--radius-md);
  font-size: 0.85rem;
}

.dark .tag-item {
  background-color: var(--bg-tertiary);
  color: var(--primary-400);
}

.featured-image-wrap {
  margin-bottom: var(--space-6);
}

.featured-image {
  width: 100%;
  max-height: 400px;
  object-fit: cover;
  border-radius: var(--radius-lg);
}

.content-text {
  line-height: 1.8;
  color: var(--text-primary);
  font-size: 1.05rem;
}

.content-text :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: var(--radius-lg);
}

.content-text :deep(p) {
  margin-bottom: var(--space-4);
}

.content-text :deep(h2),
.content-text :deep(h3) {
  margin-top: var(--space-6);
  margin-bottom: var(--space-4);
}

.comments-card {
  margin-top: var(--space-6);
}

.comments-title {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: 1.15rem;
  font-weight: 600;
  margin-bottom: var(--space-4);
  color: var(--text-primary);
}

.comment-form {
  margin-bottom: var(--space-6);
}

.comment-input {
  width: 100%;
  padding: var(--space-3);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  font-size: 1rem;
  resize: vertical;
  margin-bottom: var(--space-3);
  background: var(--bg-primary);
  color: var(--text-primary);
  transition: border-color 0.2s;
}

.comment-input:focus {
  outline: none;
  border-color: var(--primary-400);
}

.login-tip {
  background-color: var(--bg-tertiary);
  padding: var(--space-4);
  border-radius: var(--radius-lg);
  margin-bottom: var(--space-6);
  color: var(--text-secondary);
}

.empty-comments {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-8);
  color: var(--text-tertiary);
  gap: var(--space-3);
}

.empty-icon {
  font-size: 2rem;
}

.comment-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.comment-item {
  padding: var(--space-4);
  background-color: var(--bg-tertiary);
  border-radius: var(--radius-lg);
}

.comment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-2);
}

.comment-user {
  font-weight: 600;
  color: var(--primary-600);
}

.dark .comment-user {
  color: var(--primary-400);
}

.comment-time {
  color: var(--text-tertiary);
  font-size: 0.85rem;
}

.comment-text {
  color: var(--text-primary);
  line-height: 1.6;
}

.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-12);
  color: var(--text-secondary);
  gap: var(--space-3);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--primary-200);
  border-radius: 50%;
  border-top-color: var(--primary-600);
  animation: spin 1s ease-in-out infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-icon {
  font-size: 2.5rem;
  color: var(--warning-color);
}

.btn {
  padding: var(--space-2) var(--space-5);
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

.btn-primary:hover:not(:disabled) {
  background-color: var(--primary-700);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .content-meta-bar {
    flex-direction: column;
    align-items: flex-start;
  }

  .content-main-card,
  .comments-card {
    padding: var(--space-4);
  }
}
</style>
