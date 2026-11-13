<template>
  <div class="post-detail-page container-medium page-padding">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-state">
      <div class="loading-spinner"></div>
      <p>正在加载帖子...</p>
    </div>

    <!-- 帖子内容 -->
    <template v-else-if="post">
      <SectionHeader
        :title="post.title || ''"
        :subtitle="post.author.username + ' · ' + formatTime(post.created_at)"
        icon="i-ep-document"
      />

      <GlassCard :hover="false" class="post-card">
        <div class="post-meta-bar">
          <div class="author-info">
            <img v-if="post.author.avatar" :src="post.author.avatar" alt="avatar" class="author-avatar" />
            <div v-else class="author-avatar-placeholder">{{ post.author.username.substring(0, 1) }}</div>
            <span class="author-name">{{ post.author.username }}</span>
            <span class="post-time">{{ formatTime(post.created_at) }}</span>
          </div>
          <div class="post-actions-bar">
            <div class="post-stats">
              <span class="stat-item">
                <span class="i-ep-view stat-icon" />
                <span>{{ (post as any).views || 0 }}</span>
              </span>
              <span class="stat-item">
                <span class="i-ep-chat-dot-round stat-icon" />
                <span>{{ (post as any).comments_count || 0 }}</span>
              </span>
              <button
                type="button"
                class="stat-item like-button"
                :class="{ liked: post.is_liked }"
                @click.stop="handleLikePost"
              >
                <span class="i-ep-thumb stat-icon" />
                <span>{{ post.like_count || 0 }}</span>
              </button>
            </div>
            <!-- 编辑和删除按钮（仅作者可见） -->
            <div v-if="isAuthor" class="post-management">
              <button class="btn btn-secondary" @click="startEdit">
                <span class="i-ep-edit" />
                <span>编辑</span>
              </button>
              <button class="btn btn-danger" @click="confirmDelete">
                <span class="i-ep-delete" />
                <span>删除</span>
              </button>
            </div>
          </div>
        </div>

        <div class="post-tags" v-if="(post as any).tags && (post as any).tags.length">
          <span v-for="tag in (post as any).tags" :key="tag.id" class="post-tag">{{ tag.name }}</span>
        </div>

        <div v-if="!editingPost" class="post-content">
          {{ post.content }}
        </div>

        <!-- 编辑表单 -->
        <div v-else class="edit-form">
          <textarea
            v-model="editContent"
            class="edit-input"
            rows="8"
          ></textarea>
          <div class="edit-actions">
            <button class="btn btn-secondary" @click="cancelEdit">取消</button>
            <button
              class="btn btn-primary"
              @click="saveEdit"
              :disabled="!editContent.trim() || submittingEdit"
            >
              <span v-if="submittingEdit" class="loading-spinner small"></span>
              <span>{{ submittingEdit ? '保存中...' : '保存修改' }}</span>
            </button>
          </div>
        </div>
      </GlassCard>

      <!-- 评论区 -->
      <GlassCard :hover="false" class="comments-card">
        <h2 class="comments-title">
          <span class="i-ep-chat-dot-round" />
          评论 ({{ (post as any).comments_count || 0 }})
        </h2>

        <!-- 评论表单 -->
        <div v-if="isLoggedIn" class="comment-form">
          <textarea
            v-model="newComment"
            placeholder="发表你的评论..."
            rows="3"
            class="comment-input"
          ></textarea>
          <button
            class="btn btn-primary"
            @click="submitComment(null)"
            :disabled="!newComment.trim() || submittingComment"
          >
            <span v-if="submittingComment" class="loading-spinner small"></span>
            <span>{{ submittingComment ? '提交中...' : '发表评论' }}</span>
          </button>
        </div>
        <div v-else class="login-tip">
          请<router-link to="/login">登录</router-link>后发表评论
        </div>

        <!-- 评论列表 -->
        <div v-if="commentsLoading" class="loading-state loading-inline">
          <div class="loading-spinner"></div>
          <p>加载评论中...</p>
        </div>

        <div v-else-if="comments.length === 0" class="empty-state empty-inline">
          <span class="i-ep-chat-dot-round empty-icon" />
          <p>暂无评论，来发表第一条评论吧！</p>
        </div>

        <div v-else class="comments-list">
          <div v-for="comment in comments" :key="comment.id" class="comment-item">
            <div class="comment-header">
              <div class="comment-author">
                <img v-if="comment.author.avatar" :src="comment.author.avatar" alt="avatar" class="author-avatar small" />
                <div v-else class="author-avatar-placeholder small">{{ comment.author.username.substring(0, 1) }}</div>
                <span class="author-name">{{ comment.author.username }}</span>
                <span class="comment-time">{{ formatTime(comment.created_at) }}</span>
              </div>
              <button
                type="button"
                class="like-button"
                :class="{ liked: (comment as any).is_liked }"
                @click.stop="handleLikeComment(comment)"
              >
                <span class="i-ep-thumb stat-icon" />
                <span>{{ comment.like_count || 0 }}</span>
              </button>
            </div>

            <div class="comment-content">{{ comment.content }}</div>

            <div class="comment-actions">
              <button v-if="isLoggedIn" class="btn-reply" @click="startReply(comment)">回复</button>
            </div>

            <!-- 回复表单 -->
            <div v-if="replyingTo === comment.id" class="reply-form">
              <textarea
                v-model="replyContent"
                placeholder="回复评论..."
                rows="2"
                class="comment-input"
              ></textarea>
              <div class="form-actions">
                <button class="btn btn-secondary" @click="cancelReply">取消</button>
                <button
                  class="btn btn-primary"
                  @click="submitComment(comment.id)"
                  :disabled="!replyContent.trim() || submittingComment"
                >
                  <span v-if="submittingComment" class="loading-spinner small"></span>
                  <span>{{ submittingComment ? '提交中...' : '回复' }}</span>
                </button>
              </div>
            </div>

            <!-- 回复列表 -->
            <div v-if="(comment as any).replies && (comment as any).replies.length > 0" class="replies-list">
              <div v-for="reply in (comment as any).replies" :key="reply.id" class="reply-item">
                <div class="comment-header">
                  <div class="comment-author">
                    <img v-if="reply.author.avatar" :src="reply.author.avatar" alt="avatar" class="author-avatar small" />
                    <div v-else class="author-avatar-placeholder small">{{ reply.author.username.substring(0, 1) }}</div>
                    <span class="author-name">{{ reply.author.username }}</span>
                    <span class="comment-time">{{ formatTime(reply.created_at) }}</span>
                  </div>
                  <button
                    type="button"
                    class="like-button"
                    :class="{ liked: (reply as any).is_liked }"
                    @click.stop="handleLikeComment(reply)"
                  >
                    <span class="i-ep-thumb stat-icon" />
                    <span>{{ reply.like_count || 0 }}</span>
                  </button>
                </div>
                <div class="comment-content">{{ reply.content }}</div>
                <div class="comment-actions">
                  <button v-if="isLoggedIn" class="btn-reply" @click="startReply(comment)">回复</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </GlassCard>
    </template>

    <!-- 错误状态 -->
    <div v-else class="error-state">
      <span class="i-ep-warning error-icon" />
      <p>哎呀，加载帖子时出错了</p>
      <button class="btn btn-primary" @click="fetchPost">重试</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { forumApi } from '@/api/forum'
import type { Post, Comment } from '@/types/forum'
import { useUserStore } from '@/stores/userStore'
import GlassCard from '@/components/GlassCard.vue'
import SectionHeader from '@/components/SectionHeader.vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

// 状态
const post = ref<Post | null>(null)
const comments = ref<Comment[]>([])
const loading = ref(true)
const commentsLoading = ref(true)
const submittingComment = ref(false)
const newComment = ref('')
const replyingTo = ref<number | null>(null)
const replyContent = ref('')

// 编辑相关状态
const editingPost = ref(false)
const editContent = ref('')
const submittingEdit = ref(false)

// 登录状态
const isLoggedIn = computed(() => {
  return userStore.isLoggedIn
})

// 是否为作者
const isAuthor = computed(() => {
  if (!isLoggedIn.value || !post.value) return false
  return String(userStore.user?.id) === String((post.value as any).author.id)
})

// 获取帖子详情
const fetchPost = async () => {
  loading.value = true
  try {
    const postId = Number(route.params.postId)
    if (!postId) {
      router.push('/404')
      return
    }

    const response = await forumApi.getPost(postId)
    post.value = response
  } catch (error) {
    console.error('获取帖子详情失败:', error)
    post.value = null
  } finally {
    loading.value = false
  }
}

// 获取评论列表
const fetchComments = async () => {
  if (!post.value) return

  commentsLoading.value = true
  try {
    const response = await forumApi.getComments(post.value.id)
    comments.value = response.results
  } catch (error) {
    console.error('获取评论列表失败:', error)
  } finally {
    commentsLoading.value = false
  }
}

// 点赞帖子
const handleLikePost = async () => {
  if (!isLoggedIn.value || !post.value) return

  try {
    await forumApi.likePost(post.value.id)

    // 更新点赞状态
    if (post.value.is_liked) {
      post.value.like_count = (post.value.like_count || 0) - 1
    } else {
      post.value.like_count = (post.value.like_count || 0) + 1
    }
    post.value.is_liked = !post.value.is_liked
  } catch (error) {
    console.error('点赞失败:', error)
  }
}

// 点赞评论
const handleLikeComment = async (comment: Comment) => {
  if (!isLoggedIn.value) return

  try {
    await forumApi.likeComment(comment.id)

    // 更新点赞状态
    const currentLiked = (comment as any).is_liked || false
    if (currentLiked) {
      comment.like_count = (comment.like_count || 0) - 1
    } else {
      comment.like_count = (comment.like_count || 0) + 1
    }
    (comment as any).is_liked = !currentLiked
  } catch (error) {
    console.error('点赞评论失败:', error)
  }
}

// 开始回复
const startReply = (comment: Comment) => {
  replyingTo.value = comment.id
  replyContent.value = ''
}

// 取消回复
const cancelReply = () => {
  replyingTo.value = null
  replyContent.value = ''
}

// 提交评论或回复
const submitComment = async (parentId: number | null) => {
  if (!isLoggedIn.value || !post.value) return

  const content = parentId === null ? newComment.value : replyContent.value
  if (!content.trim()) return

  submittingComment.value = true
  try {
    const commentData = {
      post: post.value.id,
      content: content.trim()
    }

    if (parentId !== null) {
      Object.assign(commentData, { parent: parentId })
    }

    await forumApi.addComment(commentData)

    // 重置表单
    if (parentId === null) {
      newComment.value = ''
    } else {
      replyContent.value = ''
      replyingTo.value = null
    }

    // 重新获取评论
    await fetchComments()

    // 更新帖子的评论计数
    if (post.value) {
      (post.value as any).comments_count = ((post.value as any).comments_count || 0) + 1
    }
  } catch (error) {
    console.error('提交评论失败:', error)
    alert('提交评论失败，请稍后重试')
  } finally {
    submittingComment.value = false
  }
}

// 开始编辑帖子
const startEdit = () => {
  if (!post.value) return
  editContent.value = post.value.content
  editingPost.value = true
}

// 取消编辑
const cancelEdit = () => {
  editingPost.value = false
  editContent.value = ''
}

// 保存编辑
const saveEdit = async () => {
  if (!post.value || !editContent.value.trim()) return

  submittingEdit.value = true
  try {
    await forumApi.updatePost(post.value.id, { content: editContent.value.trim() })

    // 更新本地数据
    post.value.content = editContent.value.trim()
    editingPost.value = false
    editContent.value = ''

    alert('编辑成功')
  } catch (error) {
    console.error('编辑帖子失败:', error)
    alert('编辑失败，请稍后重试')
  } finally {
    submittingEdit.value = false
  }
}

// 确认删除
const confirmDelete = () => {
  if (!post.value) return

  if (confirm('确定要删除这篇帖子吗？此操作不可撤销。')) {
    deletePost()
  }
}

// 删除帖子
const deletePost = async () => {
  if (!post.value) return

  try {
    await forumApi.deletePost(post.value.id)

    // 删除成功后返回上一页
    router.back()
  } catch (error) {
    console.error('删除帖子失败:', error)
    alert('删除失败，请稍后重试')
  }
}

// 格式化时间
const formatTime = (dateStr: string) => {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  // 小于一天，显示相对时间
  if (diff < 24 * 60 * 60 * 1000) {
    const hours = Math.floor(diff / (60 * 60 * 1000))
    if (hours === 0) {
      const minutes = Math.floor(diff / (60 * 1000))
      return minutes === 0 ? '刚刚' : `${minutes}分钟前`
    }
    return `${hours}小时前`
  }

  // 小于一周，显示星期几
  if (diff < 7 * 24 * 60 * 60 * 1000) {
    const days = ['日', '一', '二', '三', '四', '五', '六']
    return `星期${days[date.getDay()]}`
  }

  // 大于一周，显示具体日期
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

onMounted(async () => {
  await fetchPost()
  if (post.value) {
    await fetchComments()
  }
})
</script>

<style scoped>
.post-detail-page {
  color: var(--text-primary);
}

.loading-state,
.error-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 5rem 0;
  color: var(--text-secondary);
  gap: var(--space-3);
}

.loading-state.loading-inline,
.empty-state.empty-inline {
  padding: 2rem 0;
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

.loading-spinner.small {
  width: 16px;
  height: 16px;
  border-width: 2px;
  margin: 0;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-icon {
  font-size: 3rem;
  color: var(--warning-color);
  margin-bottom: 1rem;
}

.empty-icon {
  font-size: 2rem;
  color: var(--text-tertiary);
  margin-bottom: 1rem;
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

.btn-primary:hover:not(:disabled) {
  background-color: var(--primary-700);
}

.btn-secondary {
  background-color: var(--bg-tertiary);
  color: var(--text-primary);
}

.btn-secondary:hover:not(:disabled) {
  background-color: var(--border-color);
}

.btn-danger {
  background-color: var(--error-color);
  color: white;
}

.btn-danger:hover:not(:disabled) {
  background-color: #dc2626;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.post-card,
.comments-card {
  margin-bottom: var(--space-6);
}

.post-meta-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-4);
  margin-bottom: var(--space-4);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--border-color-light);
}

.author-info,
.comment-author {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.author-avatar,
.author-avatar-placeholder {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
}

.author-avatar-placeholder {
  background: linear-gradient(135deg, var(--primary-500), var(--primary-700));
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
}

.author-avatar.small,
.author-avatar-placeholder.small {
  width: 36px;
  height: 36px;
}

.author-name {
  font-weight: 600;
  color: var(--text-primary);
}

.post-time,
.comment-time {
  color: var(--text-tertiary);
  font-size: 0.875rem;
}

.post-actions-bar {
  display: flex;
  align-items: center;
  gap: var(--space-6);
}

.post-management {
  display: flex;
  gap: var(--space-3);
}

.post-stats {
  display: flex;
  gap: var(--space-4);
}

.stat-item {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.stat-icon {
  color: var(--text-tertiary);
  font-size: 0.875rem;
}

.like-button {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
  transition: color 0.2s;
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.like-button:hover {
  color: var(--primary-600);
}

.like-button.liked {
  color: var(--primary-600);
}

.post-tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  margin-bottom: var(--space-4);
}

.post-tag {
  padding: var(--space-1) var(--space-3);
  background-color: var(--primary-50);
  color: var(--primary-600);
  border-radius: var(--radius-full);
  font-size: 0.85rem;
}

.dark .post-tag {
  background-color: var(--bg-tertiary);
  color: var(--primary-400);
}

.post-content {
  line-height: 1.8;
  color: var(--text-primary);
  font-size: 1.05rem;
  white-space: pre-line;
}

.edit-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.edit-input,
.comment-input {
  width: 100%;
  padding: var(--space-3);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  font-size: 1rem;
  resize: vertical;
  background: var(--bg-primary);
  color: var(--text-primary);
  transition: border-color 0.2s;
}

.edit-input:focus,
.comment-input:focus {
  outline: none;
  border-color: var(--primary-400);
}

.edit-actions,
.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
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

.login-tip {
  text-align: center;
  margin-bottom: var(--space-6);
  padding: var(--space-4);
  background-color: var(--bg-tertiary);
  border-radius: var(--radius-lg);
  color: var(--text-secondary);
}

.login-tip a {
  color: var(--primary-600);
  text-decoration: none;
  font-weight: 600;
}

.comments-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.comment-item {
  position: relative;
}

.comment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-3);
}

.comment-content {
  margin-bottom: var(--space-3);
  line-height: 1.6;
  color: var(--text-primary);
  white-space: pre-line;
}

.comment-actions {
  display: flex;
  gap: var(--space-4);
  margin-bottom: var(--space-3);
}

.btn-reply {
  background: none;
  border: none;
  color: var(--primary-600);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  padding: 0;
  transition: color 0.2s;
}

.btn-reply:hover {
  color: var(--primary-500);
}

.reply-form {
  margin-top: var(--space-3);
  margin-bottom: var(--space-4);
  padding-left: var(--space-8);
}

.replies-list {
  margin-top: var(--space-4);
  padding-left: var(--space-8);
  border-left: 2px solid var(--border-color-light);
}

.reply-item {
  margin-bottom: var(--space-4);
}

.reply-item:last-child {
  margin-bottom: 0;
}

@media (max-width: 768px) {
  .post-meta-bar {
    flex-direction: column;
    align-items: flex-start;
  }

  .post-actions-bar {
    width: 100%;
    justify-content: space-between;
  }

  .post-stats {
    width: 100%;
    justify-content: space-between;
  }

  .replies-list,
  .reply-form {
    padding-left: var(--space-4);
  }
}
</style>
