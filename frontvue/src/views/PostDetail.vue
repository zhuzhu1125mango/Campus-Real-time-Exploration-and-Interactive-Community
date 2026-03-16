<template>
  <div class="post-detail-container">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <div class="loading-spinner large"></div>
      <p>正在加载帖子...</p>
    </div>
    
    <!-- 帖子内容 -->
    <div v-else-if="post" class="post-content-container">
      <div class="post-header">
        <h1 class="post-title">{{ post.title }}</h1>
        <div class="post-meta">
          <div class="post-author">
            <img v-if="post.author.avatar" :src="post.author.avatar" alt="avatar" class="author-avatar" />
            <div v-else class="author-avatar-placeholder">{{ post.author.username.substring(0, 1) }}</div>
            <span class="author-name">{{ post.author.username }}</span>
            <span class="post-time">{{ formatTime(post.created_at) }}</span>
          </div>
          <div class="post-stats">
            <div class="stat-item">
              <span class="icon-view"></span>
              <span>{{ (post as any).views || 0 }}</span>
            </div>
            <div class="stat-item">
              <span class="icon-comment"></span>
              <span>{{ (post as any).comments_count || 0 }}</span>
            </div>
            <div 
              class="stat-item like-button" 
              :class="{ liked: post.is_liked }"
              @click.stop="handleLikePost"
            >
              <span class="icon-like"></span>
              <span>{{ post.like_count || 0 }}</span>
            </div>
          </div>
        </div>
        <div class="post-tags" v-if="(post as any).tags && (post as any).tags.length">
          <span v-for="tag in (post as any).tags" :key="tag.id" class="post-tag">{{ tag.name }}</span>
        </div>
      </div>
      
      <div class="post-content">
        {{ post.content }}
      </div>
      
      <!-- 评论区 -->
      <div class="comments-section">
        <h2 class="comments-title">评论 ({{ (post as any).comments_count || 0 }})</h2>
        
        <!-- 评论表单 -->
        <div v-if="isLoggedIn" class="comment-form">
          <textarea 
            v-model="newComment" 
            placeholder="发表你的评论..." 
            rows="3"
            class="comment-input"
          ></textarea>
          <button 
            class="btn-submit" 
            @click="submitComment(null)" 
            :disabled="!newComment.trim() || submittingComment"
          >
            <span v-if="submittingComment" class="loading-spinner"></span>
            <span>{{ submittingComment ? '提交中...' : '发表评论' }}</span>
          </button>
        </div>
        <div v-else class="login-tip">
          请<router-link to="/login">登录</router-link>后发表评论
        </div>
        
        <!-- 评论列表 -->
        <div v-if="commentsLoading" class="loading-comments">
          <div class="loading-spinner"></div>
          <p>加载评论中...</p>
        </div>
        
        <div v-else-if="comments.length === 0" class="empty-comments">
          暂无评论，来发表第一条评论吧！
        </div>
        
        <div v-else class="comments-list">
          <div v-for="comment in comments" :key="comment.id" class="comment-item">
            <div class="comment-header">
              <div class="comment-author">
                <img v-if="comment.author.avatar" :src="comment.author.avatar" alt="avatar" class="author-avatar" />
                <div v-else class="author-avatar-placeholder">{{ comment.author.username.substring(0, 1) }}</div>
                <span class="author-name">{{ comment.author.username }}</span>
                <span class="comment-time">{{ formatTime(comment.created_at) }}</span>
              </div>
              <div 
                class="like-button" 
                :class="{ liked: (comment as any).is_liked }"
                @click.stop="handleLikeComment(comment)"
              >
                <span class="icon-like"></span>
                <span>{{ comment.like_count || 0 }}</span>
              </div>
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
                <button class="btn-cancel" @click="cancelReply">取消</button>
                <button 
                  class="btn-submit" 
                  @click="submitComment(comment.id)" 
                  :disabled="!replyContent.trim() || submittingComment"
                >
                  <span v-if="submittingComment" class="loading-spinner"></span>
                  <span>{{ submittingComment ? '提交中...' : '回复' }}</span>
                </button>
              </div>
            </div>
            
            <!-- 回复列表 -->
            <div v-if="(comment as any).replies && (comment as any).replies.length > 0" class="replies-list">
              <div v-for="reply in (comment as any).replies" :key="reply.id" class="reply-item">
                <div class="comment-header">
                  <div class="comment-author">
                    <img v-if="reply.author.avatar" :src="reply.author.avatar" alt="avatar" class="author-avatar" />
                    <div v-else class="author-avatar-placeholder">{{ reply.author.username.substring(0, 1) }}</div>
                    <span class="author-name">{{ reply.author.username }}</span>
                    <span class="comment-time">{{ formatTime(reply.created_at) }}</span>
                  </div>
                  <div 
                    class="like-button" 
                    :class="{ liked: (reply as any).is_liked }"
                    @click.stop="handleLikeComment(reply)"
                  >
                    <span class="icon-like"></span>
                    <span>{{ reply.like_count || 0 }}</span>
                  </div>
                </div>
                <div class="comment-content">{{ reply.content }}</div>
                <div class="comment-actions">
                  <button v-if="isLoggedIn" class="btn-reply" @click="startReply(comment)">回复</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 错误状态 -->
    <div v-else class="error-container">
      <div class="error-icon"></div>
      <p>哎呀，加载帖子时出错了</p>
      <button class="btn-retry" @click="fetchPost">重试</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { forumApi } from '@/api/forum'
import type { Post, Comment } from '@/types/forum'
import config from '@/utils/config'

const route = useRoute()
const router = useRouter()

// 状态
const post = ref<Post | null>(null)
const comments = ref<Comment[]>([])
const loading = ref(true)
const commentsLoading = ref(true)
const submittingComment = ref(false)
const newComment = ref('')
const replyingTo = ref<number | null>(null)
const replyContent = ref('')

// 登录状态
const isLoggedIn = computed(() => {
  return !!localStorage.getItem(config.jwt.accessTokenKey)
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
    const response = await forumApi.getPostComments(post.value.id)
    
    // 处理评论和回复的结构
    const parentComments: (Comment & { replies?: Comment[] })[] = []
    const replyMap = new Map<number, Comment[]>()
    
    response.results.forEach((comment: Comment) => {
      if (comment.parent === null) {
        parentComments.push({...comment, replies: []})
      } else if (comment.parent) {
        if (!replyMap.has(comment.parent)) {
          replyMap.set(comment.parent, [])
        }
        replyMap.get(comment.parent)?.push(comment)
      }
    })
    
    // 将回复添加到父评论中
    parentComments.forEach(comment => {
      const replies = replyMap.get(comment.id)
      if (replies) {
        comment.replies = replies
      }
    })
    
    comments.value = parentComments
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
.post-detail-container {
  max-width: 900px;
  margin: 0 auto;
  padding: 2rem 1rem;
}

.loading-container,
.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 5rem 0;
  color: #666;
}

.loading-spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(67, 97, 238, 0.3);
  border-radius: 50%;
  border-top-color: #4361ee;
  animation: spin 1s linear infinite;
}

.loading-spinner.large {
  width: 30px;
  height: 30px;
  border-width: 3px;
  margin-bottom: 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-icon {
  width: 60px;
  height: 60px;
  margin-bottom: 1.5rem;
  opacity: 0.5;
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%23ff3b30"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/></svg>');
  background-repeat: no-repeat;
  background-position: center;
}

.btn-retry {
  margin-top: 1rem;
  padding: 0.7rem 1.5rem;
  background-color: #4361ee;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
}

.post-content-container {
  background-color: white;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

.post-header {
  padding: 1.5rem;
  border-bottom: 1px solid #f0f0f0;
}

.post-title {
  font-size: 1.8rem;
  font-weight: 700;
  margin-bottom: 1rem;
  color: #333;
}

.post-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.post-author {
  display: flex;
  align-items: center;
}

.author-avatar,
.author-avatar-placeholder {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  margin-right: 0.8rem;
  overflow: hidden;
}

.author-avatar-placeholder {
  background-color: #4361ee;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 1.2rem;
}

.author-name {
  font-weight: 600;
  font-size: 1rem;
  margin-right: 1rem;
}

.post-time {
  color: #999;
  font-size: 0.9rem;
}

.post-stats {
  display: flex;
  gap: 1.5rem;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  color: #999;
  font-size: 0.9rem;
}

.icon-view,
.icon-comment,
.icon-like {
  display: inline-block;
  width: 18px;
  height: 18px;
  background-size: contain;
  background-repeat: no-repeat;
}

.icon-view {
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%23999"><path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/></svg>');
}

.icon-comment {
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%23999"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/></svg>');
}

.like-button {
  cursor: pointer;
  transition: all 0.2s;
}

.like-button:hover {
  color: #4361ee;
}

.like-button:hover .icon-like {
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%234361ee"><path d="M16.5 3c-1.74 0-3.41.81-4.5 2.09C10.91 3.81 9.24 3 7.5 3 4.42 3 2 5.42 2 8.5c0 3.78 3.4 6.86 8.55 11.54L12 21.35l1.45-1.32C18.6 15.36 22 12.28 22 8.5 22 5.42 19.58 3 16.5 3zm-4.4 15.55l-.1.1-.1-.1C7.14 14.24 4 11.39 4 8.5 4 6.5 5.5 5 7.5 5c1.54 0 3.04.99 3.57 2.36h1.87C13.46 5.99 14.96 5 16.5 5c2 0 3.5 1.5 3.5 3.5 0 2.89-3.14 5.74-7.9 10.05z"/></svg>');
}

.like-button.liked {
  color: #4361ee;
}

.like-button.liked .icon-like {
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%234361ee"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>');
}

.icon-like {
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%23999"><path d="M16.5 3c-1.74 0-3.41.81-4.5 2.09C10.91 3.81 9.24 3 7.5 3 4.42 3 2 5.42 2 8.5c0 3.78 3.4 6.86 8.55 11.54L12 21.35l1.45-1.32C18.6 15.36 22 12.28 22 8.5 22 5.42 19.58 3 16.5 3zm-4.4 15.55l-.1.1-.1-.1C7.14 14.24 4 11.39 4 8.5 4 6.5 5.5 5 7.5 5c1.54 0 3.04.99 3.57 2.36h1.87C13.46 5.99 14.96 5 16.5 5c2 0 3.5 1.5 3.5 3.5 0 2.89-3.14 5.74-7.9 10.05z"/></svg>');
}

.post-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.post-tag {
  padding: 0.3rem 0.8rem;
  background-color: #f0f4ff;
  color: #4361ee;
  border-radius: 20px;
  font-size: 0.9rem;
}

.post-content {
  padding: 2rem 1.5rem;
  font-size: 1.1rem;
  line-height: 1.7;
  color: #333;
  white-space: pre-line;
}

/* 评论区 */
.comments-section {
  padding: 1.5rem;
  border-top: 1px solid #f0f0f0;
}

.comments-title {
  font-size: 1.3rem;
  margin-bottom: 1.5rem;
  color: #333;
}

.comment-form {
  margin-bottom: 2rem;
}

.comment-input {
  width: 100%;
  padding: 0.8rem;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  font-size: 1rem;
  margin-bottom: 1rem;
  resize: vertical;
}

.comment-input:focus {
  outline: none;
  border-color: #4361ee;
  box-shadow: 0 0 0 3px rgba(67, 97, 238, 0.1);
}

.login-tip {
  text-align: center;
  margin-bottom: 2rem;
  padding: 1rem;
  background-color: #f8f9fa;
  border-radius: 8px;
  color: #666;
}

.login-tip a {
  color: #4361ee;
  text-decoration: none;
  font-weight: 600;
}

.loading-comments {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem 0;
  color: #666;
}

.empty-comments {
  text-align: center;
  padding: 2rem 0;
  color: #999;
}

.comments-list {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.comment-item {
  position: relative;
}

.comment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.8rem;
}

.comment-author {
  display: flex;
  align-items: center;
}

.comment-time {
  color: #999;
  font-size: 0.9rem;
}

.comment-content {
  margin-bottom: 0.8rem;
  line-height: 1.5;
  white-space: pre-line;
}

.comment-actions {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
}

.btn-reply {
  background: none;
  border: none;
  color: #4361ee;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  padding: 0;
}

.reply-form {
  margin-top: 1rem;
  margin-bottom: 1.5rem;
  padding-left: 2rem;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
}

.btn-cancel {
  padding: 0.6rem 1.2rem;
  background-color: #f5f5f5;
  color: #555;
  border: none;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
}

.btn-submit {
  padding: 0.6rem 1.2rem;
  background-color: #4361ee;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.btn-submit:disabled {
  background-color: #b0b0b0;
  cursor: not-allowed;
}

.replies-list {
  margin-top: 1.5rem;
  padding-left: 2rem;
  border-left: 2px solid #f0f0f0;
}

.reply-item {
  margin-bottom: 1.5rem;
}

.reply-item:last-child {
  margin-bottom: 0;
}

@media (max-width: 768px) {
  .post-meta {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  
  .post-stats {
    width: 100%;
    justify-content: space-between;
  }
  
  .replies-list {
    padding-left: 1rem;
  }
}
</style> 