<template>
  <div class="user-profile-container">
    <div v-if="loading" class="loading-container">
      <div class="loading-spinner large"></div>
      <p>加载中...</p>
    </div>
    
    <template v-else>
      <!-- 用户基本信息 -->
      <div class="user-header">
        <div class="avatar-container">
          <img v-if="user.avatar" :src="user.avatar" alt="用户头像" class="user-avatar" />
          <div v-else class="avatar-placeholder">{{ user.username ? user.username.substring(0, 1).toUpperCase() : '?' }}</div>
        </div>
        <div class="user-info">
          <h1 class="username">{{ user.username }}</h1>
          <div class="user-meta">
            <span class="join-date">注册于 {{ formatDate(stats.join_date) }}</span>
            <span v-if="user.location" class="location">
              <i class="location-icon"></i>
              {{ user.location }}
            </span>
          </div>
          <div class="user-bio" v-if="user.bio">{{ user.bio }}</div>
        </div>
      </div>
      
      <!-- 用户统计信息 -->
      <div class="user-stats">
        <div class="stat-item">
          <div class="stat-value">{{ stats.topic_count }}</div>
          <div class="stat-label">主题</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ stats.post_count }}</div>
          <div class="stat-label">帖子</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ stats.reply_count }}</div>
          <div class="stat-label">回复</div>
        </div>
      </div>
      
      <!-- 活跃板块 -->
      <div class="active-boards" v-if="stats.active_boards && stats.active_boards.length > 0">
        <h3 class="section-title">活跃板块</h3>
        <div class="boards-list">
          <router-link
            v-for="board in stats.active_boards"
            :key="board.id"
            :to="`/forum/board/${board.id}`"
            class="board-item"
          >
            <span class="board-name">{{ board.name }}</span>
            <span class="board-post-count">{{ board.post_count }}篇帖子</span>
          </router-link>
        </div>
      </div>
      
      <!-- 内容标签页 -->
      <div class="content-tabs">
        <div 
          class="tab-item" 
          :class="{ active: activeTab === 'topics' }"
          @click="setActiveTab('topics')"
        >
          主题
        </div>
        <div 
          class="tab-item" 
          :class="{ active: activeTab === 'posts' }"
          @click="setActiveTab('posts')"
        >
          回复
        </div>
      </div>
      
      <!-- 主题列表 -->
      <div v-if="activeTab === 'topics'" class="topics-list">
        <div v-if="loadingTopics" class="loading-container small">
          <div class="loading-spinner"></div>
          <p>加载中...</p>
        </div>
        
        <div v-else-if="topics.length === 0" class="empty-list">
          <p>暂无主题</p>
        </div>
        
        <div v-else class="topic-items">
          <div 
            v-for="topic in topics" 
            :key="topic.id"
            class="topic-item"
            @click="goToTopic(topic.id)"
          >
            <div class="topic-header">
              <h3 class="topic-title">{{ topic.title }}</h3>
              <span class="topic-date">{{ formatDate(topic.created_at) }}</span>
            </div>
            <div class="topic-footer">
              <span class="topic-board">{{ (topic as any).board_name || '未知板块' }}</span>
              <div class="topic-stats">
                <span class="stat-views">{{ topic.views || 0 }} 浏览</span>
                <span class="stat-replies">{{ (topic.post_count || 0) - 1 }} 回复</span>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 主题分页 -->
        <div v-if="topicTotalPages > 1" class="pagination">
          <button 
            class="btn-page" 
            :disabled="topicPage === 1" 
            @click="changePage('topics', topicPage - 1)"
          >
            上一页
          </button>
          <span class="page-info">{{ topicPage }} / {{ topicTotalPages }}</span>
          <button 
            class="btn-page" 
            :disabled="topicPage === topicTotalPages" 
            @click="changePage('topics', topicPage + 1)"
          >
            下一页
          </button>
        </div>
      </div>
      
      <!-- 帖子列表 -->
      <div v-if="activeTab === 'posts'" class="posts-list">
        <div v-if="loadingPosts" class="loading-container small">
          <div class="loading-spinner"></div>
          <p>加载中...</p>
        </div>
        
        <div v-else-if="posts.length === 0" class="empty-list">
          <p>暂无回复</p>
        </div>
        
        <div v-else class="post-items">
          <div 
            v-for="post in posts" 
            :key="post.id"
            class="post-item"
            @click="goToPost(post.topic, post.id)"
          >
            <div class="post-header">
              <div class="post-topic">回复：{{ (post as any).topic_title || '未知主题' }}</div>
              <span class="post-date">{{ formatDate(post.created_at) }}</span>
            </div>
            <div class="post-content">
              <div class="post-preview" v-html="getPostPreview(post.content)"></div>
            </div>
            <div class="post-footer">
              <div v-if="(post as any).is_edited" class="post-edited">
                (已编辑于 {{ formatDate((post as any).edited_at || '') }})
              </div>
              <div class="post-status" v-if="(post as any).content_status !== 'approved'">
                <span class="status-badge" :class="(post as any).content_status">
                  {{ getStatusText((post as any).content_status || 'approved') }}
                </span>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 帖子分页 -->
        <div v-if="postTotalPages > 1" class="pagination">
          <button 
            class="btn-page" 
            :disabled="postPage === 1" 
            @click="changePage('posts', postPage - 1)"
          >
            上一页
          </button>
          <span class="page-info">{{ postPage }} / {{ postTotalPages }}</span>
          <button 
            class="btn-page" 
            :disabled="postPage === postTotalPages" 
            @click="changePage('posts', postPage + 1)"
          >
            下一页
          </button>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { userApi } from '@/api/user'
import type { User } from '@/types/user'
import type { Topic, Post } from '@/types/forum'

const route = useRoute()
const router = useRouter()

// 状态
const loading = ref(true)
const user = ref<User>({} as User)

interface Board {
  id: number
  name: string
  post_count: number
}

const stats = ref({
  topic_count: 0,
  post_count: 0,
  reply_count: 0,
  active_boards: [] as Board[],
  join_date: ''
})
const activeTab = ref('topics')

// 主题列表
const topics = ref<Topic[]>([])
const loadingTopics = ref(false)
const topicPage = ref(1)
const topicTotalCount = ref(0)
const topicTotalPages = ref(1)

// 帖子列表
const posts = ref<Post[]>([])
const loadingPosts = ref(false)
const postPage = ref(1)
const postTotalCount = ref(0)
const postTotalPages = ref(1)

// 获取用户资料
const fetchUserProfile = async () => {
  loading.value = true
  try {
    const userId = Array.isArray(route.params.id) ? route.params.id[0] : route.params.id || 'me'
    const [userResponse, statsResponse] = await Promise.all([
      userApi.getUserProfile(userId),
      userApi.getUserProfileStats(userId)
    ])
    
    user.value = userResponse
    stats.value = statsResponse
    
    // 加载主题列表
    await fetchUserTopics()
    
  } catch (error) {
    console.error('获取用户资料失败:', error)
  } finally {
    loading.value = false
  }
}

// 获取用户主题
const fetchUserTopics = async () => {
  loadingTopics.value = true
  try {
    const userId = Array.isArray(route.params.id) ? route.params.id[0] : route.params.id || 'me'
    const response = await userApi.getUserTopics(userId, topicPage.value)
    
    topics.value = response.results
    topicTotalCount.value = response.count
    topicTotalPages.value = Math.ceil(topicTotalCount.value / 10)
    
  } catch (error) {
    console.error('获取用户主题失败:', error)
  } finally {
    loadingTopics.value = false
  }
}

// 获取用户帖子
const fetchUserPosts = async () => {
  loadingPosts.value = true
  try {
    const userId = Array.isArray(route.params.id) ? route.params.id[0] : route.params.id || 'me'
    const response = await userApi.getUserPosts(userId, postPage.value)
    
    posts.value = response.results
    postTotalCount.value = response.count
    postTotalPages.value = Math.ceil(postTotalCount.value / 10)
    
  } catch (error) {
    console.error('获取用户帖子失败:', error)
  } finally {
    loadingPosts.value = false
  }
}

// 切换标签页
const setActiveTab = (tab: string) => {
  activeTab.value = tab
  
  if (tab === 'posts' && posts.value.length === 0) {
    fetchUserPosts()
  }
}

// 切换页码
const changePage = async (type: string, page: number) => {
  if (type === 'topics') {
    topicPage.value = page
    await fetchUserTopics()
  } else {
    postPage.value = page
    await fetchUserPosts()
  }
}

// 跳转到主题详情
const goToTopic = (topicId: number) => {
  router.push(`/forum/topic/${topicId}`)
}

// 跳转到帖子所在的主题
const goToPost = (topicId: number, postId: number) => {
  router.push(`/forum/topic/${topicId}#post-${postId}`)
}

// 获取帖子预览内容
const getPostPreview = (content: string) => {
  const stripTags = (html: string) => {
    // 创建临时元素
    const tempDiv = document.createElement('div')
    tempDiv.innerHTML = html
    return tempDiv.textContent || tempDiv.innerText || ''
  }
  
  const plainText = stripTags(content)
  return plainText.length > 100 ? plainText.substring(0, 100) + '...' : plainText
}

// 获取状态文本
const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    'pending': '待审核',
    'approved': '已通过',
    'rejected': '已拒绝',
    'flagged': '已标记'
  }
  return statusMap[status] || status
}

// 格式化日期
const formatDate = (dateStr: string) => {
  if (!dateStr) return '未知'
  
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  // 小于一天，显示相对时间
  if (diff < 24 * 60 * 60 * 1000) {
    const hours = Math.floor(diff / (60 * 60 * 1000))
    if (hours === 0) {
      const minutes = Math.floor(diff / (60 * 1000))
      return minutes <= 0 ? '刚刚' : `${minutes}分钟前`
    }
    return `${hours}小时前`
  }
  
  // 显示年月日
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

// 生命周期钩子
onMounted(() => {
  fetchUserProfile()
})
</script>

<style scoped>
.user-profile-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 50px 0;
}

.loading-container.small {
  padding: 20px 0;
}

.loading-spinner {
  border: 4px solid rgba(0, 0, 0, 0.1);
  border-radius: 50%;
  border-top: 4px solid #3498db;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin-bottom: 15px;
}

.loading-spinner.small {
  width: 20px;
  height: 20px;
  border-width: 2px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 用户头部信息 */
.user-header {
  display: flex;
  align-items: center;
  margin-bottom: 30px;
}

.avatar-container {
  margin-right: 20px;
}

.user-avatar,
.avatar-placeholder {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  overflow: hidden;
}

.avatar-placeholder {
  background-color: #3498db;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36px;
  font-weight: bold;
}

.user-info {
  flex: 1;
}

.username {
  font-size: 24px;
  margin: 0 0 10px 0;
  color: #333;
}

.user-meta {
  display: flex;
  gap: 15px;
  color: #666;
  margin-bottom: 10px;
  font-size: 14px;
}

.user-bio {
  color: #666;
  line-height: 1.4;
}

/* 用户统计信息 */
.user-stats {
  display: flex;
  background-color: #f8f9fa;
  border-radius: 8px;
  margin-bottom: 30px;
  overflow: hidden;
}

.stat-item {
  flex: 1;
  padding: 20px;
  text-align: center;
  border-right: 1px solid #eee;
}

.stat-item:last-child {
  border-right: none;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #3498db;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 14px;
  color: #666;
}

/* 活跃板块 */
.active-boards {
  margin-bottom: 30px;
}

.section-title {
  font-size: 18px;
  margin: 0 0 15px 0;
  color: #333;
}

.boards-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.board-item {
  display: flex;
  flex-direction: column;
  padding: 15px;
  background-color: #f8f9fa;
  border-radius: 8px;
  text-decoration: none;
  color: #333;
  transition: all 0.2s;
}

.board-item:hover {
  background-color: #e9ecef;
}

.board-name {
  font-weight: 500;
  margin-bottom: 5px;
}

.board-post-count {
  font-size: 12px;
  color: #666;
}

/* 内容标签页 */
.content-tabs {
  display: flex;
  margin-bottom: 20px;
  border-bottom: 1px solid #eee;
}

.tab-item {
  padding: 10px 20px;
  cursor: pointer;
  font-weight: 500;
  color: #666;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
}

.tab-item:hover {
  color: #3498db;
}

.tab-item.active {
  color: #3498db;
  border-bottom-color: #3498db;
}

/* 空列表 */
.empty-list {
  padding: 50px;
  text-align: center;
  color: #666;
  background-color: #f8f9fa;
  border-radius: 8px;
}

/* 主题列表 */
.topic-items {
  margin-bottom: 20px;
}

.topic-item {
  margin-bottom: 15px;
  padding: 15px;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: all 0.2s;
}

.topic-item:hover {
  box-shadow: 0 3px 6px rgba(0, 0, 0, 0.15);
}

.topic-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
}

.topic-title {
  margin: 0;
  font-size: 16px;
  color: #333;
}

.topic-date {
  font-size: 12px;
  color: #999;
  white-space: nowrap;
}

.topic-footer {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #666;
}

.topic-board {
  background-color: #e9ecef;
  padding: 2px 8px;
  border-radius: 4px;
}

.topic-stats {
  display: flex;
  gap: 10px;
}

/* 帖子列表 */
.post-items {
  margin-bottom: 20px;
}

.post-item {
  margin-bottom: 15px;
  padding: 15px;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: all 0.2s;
}

.post-item:hover {
  box-shadow: 0 3px 6px rgba(0, 0, 0, 0.15);
}

.post-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
}

.post-topic {
  font-weight: 500;
  color: #333;
}

.post-date {
  font-size: 12px;
  color: #999;
  white-space: nowrap;
}

.post-content {
  margin-bottom: 10px;
}

.post-preview {
  font-size: 14px;
  color: #666;
  line-height: 1.5;
}

.post-footer {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #999;
}

.post-edited {
  font-style: italic;
}

.status-badge {
  padding: 2px 8px;
  border-radius: 4px;
  color: white;
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

/* 分页 */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: 20px;
  margin-bottom: 30px;
  gap: 15px;
}

.btn-page {
  padding: 8px 15px;
  background-color: #f1f1f1;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-page:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-page:not(:disabled):hover {
  background-color: #e9ecef;
}

@media (max-width: 768px) {
  .user-header {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }
  
  .avatar-container {
    margin-right: 0;
    margin-bottom: 20px;
  }
  
  .user-stats {
    flex-direction: column;
  }
  
  .stat-item {
    border-right: none;
    border-bottom: 1px solid #eee;
  }
  
  .stat-item:last-child {
    border-bottom: none;
  }
  
  .topic-header,
  .post-header,
  .topic-footer {
    flex-direction: column;
    gap: 5px;
  }
}
</style> 