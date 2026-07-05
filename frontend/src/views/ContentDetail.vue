<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { contentApi } from '../api/content'
import { useUserStore } from '../stores/userStore'
import { sanitizeHtml } from '../utils/xss'
import type { ContentItem, Comment } from '../types/content'

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
  <div class="content-detail-page">
    <div v-if="loading" class="loading-state">
      <div class="loading-spinner"></div>
      <p>加载中...</p>
    </div>

    <template v-else-if="content">
      <div class="content-header">
        <div class="header-inner">
          <button class="back-link" @click="goBack">← 返回内容中心</button>
          <div class="content-meta-top">
            <span v-if="content.category" class="category-tag">{{ content.category.name }}</span>
            <span class="content-type">{{ content.content_type.name }}</span>
          </div>
          <h1 class="content-title">{{ content.title }}</h1>
          <div class="content-author-bar">
            <div class="author-info">
              <span class="author-name">{{ content.author.username }}</span>
              <span class="publish-time">{{ formatDate(content.created_at) }}</span>
            </div>
            <div class="content-stats">
              <span>{{ content.view_count }} 浏览</span>
              <span>{{ content.like_count }} 点赞</span>
              <span>{{ content.comment_count }} 评论</span>
            </div>
          </div>
          <div v-if="content.tags && content.tags.length > 0" class="content-tags">
            <span v-for="tag in content.tags" :key="tag.id" class="tag-item"># {{ tag.name }}</span>
          </div>
        </div>
      </div>

      <div class="content-body">
        <div class="content-main">
          <div v-if="content.featured_image" class="featured-image-wrap">
            <img :src="content.featured_image" :alt="content.title" class="featured-image" />
          </div>

          <div class="content-text" v-html="safeContent"></div>

          <div class="comments-section">
            <h2 class="section-title">评论 ({{ comments.length }})</h2>

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
              暂无评论，来说两句吧
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
          </div>
        </div>
      </div>
    </template>

    <div v-else-if="error" class="error-state">
      <p>{{ error }}</p>
      <button class="btn btn-primary" @click="loadContent">重新加载</button>
    </div>
  </div>
</template>

<style scoped>
.content-detail-page {
  min-height: calc(100vh - 200px);
}

.content-header {
  background: linear-gradient(135deg, #4361ee 0%, #3a0ca3 100%);
  color: white;
  padding: 3rem 2rem;
}

.header-inner {
  max-width: 900px;
  margin: 0 auto;
}

.back-link {
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.85);
  cursor: pointer;
  font-size: 0.95rem;
  margin-bottom: 1rem;
  padding: 0;
}

.back-link:hover {
  color: white;
}

.content-meta-top {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.category-tag,
.content-type {
  padding: 0.25rem 0.75rem;
  border-radius: 4px;
  font-size: 0.85rem;
  font-weight: 500;
}

.category-tag {
  background-color: rgba(255, 255, 255, 0.2);
  color: white;
}

.content-type {
  background-color: rgba(255, 255, 255, 0.15);
  color: rgba(255, 255, 255, 0.9);
}

.content-title {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 1.5rem;
  line-height: 1.3;
}

.content-author-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 1rem;
}

.author-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.author-name {
  font-weight: 600;
}

.publish-time {
  opacity: 0.8;
  font-size: 0.9rem;
}

.content-stats {
  display: flex;
  gap: 1rem;
  opacity: 0.85;
  font-size: 0.9rem;
}

.content-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 1rem;
}

.tag-item {
  padding: 0.25rem 0.6rem;
  background-color: rgba(255, 255, 255, 0.15);
  border-radius: 4px;
  font-size: 0.85rem;
}

.content-body {
  max-width: 900px;
  margin: 0 auto;
  padding: 2rem;
}

.content-main {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.featured-image-wrap {
  margin-bottom: 2rem;
}

.featured-image {
  width: 100%;
  max-height: 400px;
  object-fit: cover;
  border-radius: 8px;
}

.content-text {
  line-height: 1.8;
  color: #333;
  font-size: 1.05rem;
}

.content-text :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 8px;
}

.content-text :deep(p) {
  margin-bottom: 1rem;
}

.content-text :deep(h2),
.content-text :deep(h3) {
  margin-top: 1.5rem;
  margin-bottom: 1rem;
}

.comments-section {
  margin-top: 3rem;
  padding-top: 2rem;
  border-top: 1px solid #eee;
}

.section-title {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 1.5rem;
}

.comment-form {
  margin-bottom: 2rem;
}

.comment-input {
  width: 100%;
  padding: 1rem;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  font-size: 1rem;
  resize: vertical;
  margin-bottom: 1rem;
}

.login-tip {
  background-color: #f9fafc;
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 2rem;
  color: #666;
}

.login-tip a {
  color: #4361ee;
  font-weight: 500;
}

.empty-comments {
  text-align: center;
  padding: 2rem;
  color: #999;
}

.comment-list {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.comment-item {
  padding: 1rem;
  background-color: #f9fafc;
  border-radius: 8px;
}

.comment-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}

.comment-user {
  font-weight: 600;
  color: #4361ee;
}

.comment-time {
  color: #999;
  font-size: 0.85rem;
}

.comment-text {
  color: #333;
  line-height: 1.6;
}

.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem;
  color: #666;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(67, 97, 238, 0.3);
  border-radius: 50%;
  border-top-color: #4361ee;
  animation: spin 1s ease-in-out infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.btn {
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: all 0.3s;
}

.btn-primary {
  background-color: #4361ee;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: #3a56d4;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .content-title {
    font-size: 1.5rem;
  }

  .content-author-bar {
    flex-direction: column;
    align-items: flex-start;
  }

  .content-main {
    padding: 1.25rem;
  }
}
</style>
