<template>
  <div class="forum-container">
    <div class="forum-header">
      <div class="forum-info">
        <h1 class="forum-title">校园论坛</h1>
        <p class="forum-description">分享知识，交流经验</p>
      </div>
      <div class="forum-actions" v-if="isLoggedIn">
        <router-link to="/forum/notifications" class="btn-notifications">
          <span class="icon-notification"></span>
          通知
          <span v-if="unreadNotificationsCount > 0" class="notification-badge">{{ unreadNotificationsCount }}</span>
        </router-link>
        <router-link to="/forum/bookmarks" class="btn-bookmarks">
          <span class="icon-bookmark"></span>
          收藏
        </router-link>
      </div>
    </div>
    
    <!-- 论坛统计信息 -->
    <div class="forum-stats">
      <div class="stat-item">
        <div class="stat-value">{{ statsData.user_count }}</div>
        <div class="stat-label">注册用户</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{{ statsData.topic_count }}</div>
        <div class="stat-label">话题数</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{{ statsData.post_count }}</div>
        <div class="stat-label">帖子数</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{{ statsData.today_post_count }}</div>
        <div class="stat-label">今日帖子</div>
      </div>
    </div>

    <div class="forum-layout">
      <!-- 左侧：分类和板块 -->
      <div class="forum-main">
        <!-- 论坛分类和版块 -->
        <div class="forum-content">
          <div v-if="loading" class="loading-container">
            <el-skeleton :rows="5" animated />
          </div>
          <div v-else-if="error" class="error-message">
            {{ error }}
          </div>
          <div v-else class="forum-categories">
            <div v-for="category in categories" :key="category.id" class="category-section">
              <div class="category-header">
                <h2 class="category-title">
                  <i :class="category.icon || 'el-icon-folder'" class="category-icon"></i>
                  {{ category.name }}
                </h2>
                <p v-if="category.description" class="category-description">{{ category.description }}</p>
              </div>
              
              <template v-if="getBoardsByCategory(category.id).length > 0">
                <div class="board-grid">
                  <div 
                    v-for="board in getBoardsByCategory(category.id)" 
                    :key="board.id"
                    class="board-card"
                    @click="navigateToBoard(board.id)"
                  >
                    <div class="board-header">
                      <i :class="board.icon || 'el-icon-menu'" class="board-icon"></i>
                      <h3 class="board-title">{{ board.name }}</h3>
                    </div>
                    <p v-if="board.description" class="board-description">{{ board.description }}</p>
                    <div class="board-stats">
                      <span class="stat-item">
                        <i class="el-icon-chat-dot-square"></i>
                        {{ board.topic_count || 0 }} 主题
                      </span>
                      <span class="stat-item">
                        <i class="el-icon-document"></i>
                        {{ board.post_count || 0 }} 帖子
                      </span>
                    </div>
                    <div v-if="board.last_post" class="board-last-post">
                      <span class="last-post-label">最新:</span>
                      <span class="last-post-info">
                        {{ truncateText(board.last_post.title || '', 20) }}
                        <template v-if="board.last_post.author">
                          by {{ board.last_post.author.username }}
                        </template>
                        {{ formatDate(board.last_post.created_at) }}
                      </span>
                    </div>
                  </div>
                </div>
              </template>
              <div v-else class="no-boards-message">
                暂无板块
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 右侧：热门话题和最新活动 -->
      <div class="forum-sidebar">
        <!-- 热门话题 -->
        <div class="hot-topics-section">
          <h3 class="section-title">热门话题</h3>
          <div v-if="loadingHotTopics" class="loading">
            <el-skeleton :rows="3" animated />
          </div>
          <div v-else-if="errorHotTopics" class="error-message">
            {{ errorHotTopics }}
          </div>
          <div v-else-if="hotTopics.length === 0" class="no-data">
            暂无热门话题
          </div>
          <div v-else class="hot-topics-list">
            <div v-for="topic in hotTopics" :key="topic.id" class="hot-topic-item">
              <router-link :to="`/forum/topic/${topic.id}`" class="topic-link">
                <div class="topic-title">{{ truncateText(topic.title, 30) }}</div>
                <div class="topic-meta">
                  <span class="topic-views">{{ topic.views }} 浏览</span>
                  <span class="topic-posts">{{ topic.post_count }} 回复</span>
                </div>
              </router-link>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { forumApi } from '@/api/forum'
import { useUserStore } from '@/stores/userStore'
import type { Category, Board, Topic, ForumStats } from '@/types/forum'

const router = useRouter()
const userStore = useUserStore()

// 状态
const categories = ref<Category[]>([])
const boards = ref<Board[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const unreadNotificationsCount = ref(0)
const statsData = ref<ForumStats>({
  user_count: 0,
  topic_count: 0,
  post_count: 0,
  today_post_count: 0,
  category_count: 0,
  board_count: 0
})

// 热门话题
const hotTopics = ref<Topic[]>([])
const loadingHotTopics = ref(true)
const errorHotTopics = ref<string | null>(null)

// 声明需要的变量

// 登录状态
const isLoggedIn = computed(() => userStore.isLoggedIn)

// 获取分类列表
const fetchCategories = async () => {
  loading.value = true
  error.value = null
  
  try {
    const response = await forumApi.getCategories()
    categories.value = response
    console.log('获取分类成功:', categories.value)
  } catch (err) {
    console.error('获取分类列表失败:', err)
    categories.value = []
    error.value = '获取分类列表失败，请刷新页面重试'
  }
}

// 获取版块列表
const fetchBoards = async () => {
  loading.value = true
  error.value = null
  try {
    const response = await forumApi.getBoards()
    // 确保boards.value是数组
    if (Array.isArray(response)) {
      boards.value = response
    } else if (response && typeof response === 'object' && 'results' in response) {
      boards.value = response.results
    } else {
      console.error('API返回的板块数据格式不正确:', response)
      boards.value = []
    }
    console.log('获取板块成功:', boards.value)
  } catch (err) {
    console.error('获取版块列表失败:', err)
    boards.value = []
    error.value = '获取版块列表失败，请刷新页面重试'
  } finally {
    loading.value = false
  }
}

// 获取热门话题
const fetchHotTopics = async () => {
  loadingHotTopics.value = true
  errorHotTopics.value = null
  
  try {
    const days = 7; // 默认获取7天内的热门话题
    const limit = 10; // 默认获取10条
    const response = await forumApi.getHotTopics(days, limit)
    hotTopics.value = response
    console.log('获取热门话题成功:', hotTopics.value)
  } catch (err) {
    console.error('获取热门话题失败:', err)
    hotTopics.value = []
    errorHotTopics.value = '获取热门话题失败'
  } finally {
    loadingHotTopics.value = false
  }
}

// 获取未读通知数量
const fetchUnreadNotifications = async () => {
  if (!isLoggedIn.value) {
    console.log('用户未登录，跳过获取通知')
    return
  }
  
  try {
    const response = await forumApi.getNotifications()
    // 确保 response 是数组
    const notifications = Array.isArray(response) ? response : []
    unreadNotificationsCount.value = notifications.filter(notification => !notification.is_read).length
    console.log('获取到未读通知数量:', unreadNotificationsCount.value)
  } catch (error: any) {
    console.error('获取未读通知失败:', error?.message || '未知错误')
    unreadNotificationsCount.value = 0
    // 不显示通知错误，因为这是非关键功能
  }
}

// 获取论坛统计数据
const fetchForumStats = async () => {
  try {
    const response = await forumApi.getForumStats()
    statsData.value = response
    console.log('获取论坛统计成功:', statsData.value)
  } catch (error) {
    console.error('获取论坛统计失败:', error)
    // 失败时使用默认值
    statsData.value = {
      user_count: 0,
      topic_count: 0,
      post_count: 0,
      today_post_count: 0,
      category_count: 0,
      board_count: 0
    }
  }
}

// 获取分类下的版块
const getBoardsByCategory = (categoryId: number) => {
  return boards.value.filter(board => board.category === categoryId)
}

// 导航到板块详情页
const navigateToBoard = (boardId: number) => {
  router.push(`/forum/board/${boardId}`)
}

// 文本截断辅助函数
const truncateText = (text: string, maxLength: number) => {
  if (!text) return ''
  return text.length > maxLength ? text.slice(0, maxLength) + '...' : text
}

// 格式化日期
const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const day = 24 * 60 * 60 * 1000
  
  if (diff < day) {
    return '今天 ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  } else if (diff < 2 * day) {
    return '昨天 ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  } else {
    return date.toLocaleDateString([], { month: 'short', day: 'numeric' })
  }
}

// 页面加载时获取数据
onMounted(async () => {
  try {
    await Promise.all([
      fetchCategories(),
      fetchBoards(),
      fetchUnreadNotifications(),
      fetchForumStats(),
      fetchHotTopics()
    ])
  } catch (err) {
    console.error('初始化论坛数据失败:', err)
  }
})
</script>

<style scoped>
.forum-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.forum-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.forum-title {
  font-size: 28px;
  margin: 0;
  color: #333;
}

.forum-description {
  margin: 5px 0 0;
  color: #666;
}

.forum-actions {
  display: flex;
  gap: 15px;
}

.btn-notifications, .btn-bookmarks {
  display: flex;
  align-items: center;
  padding: 8px 15px;
  background-color: #f3f4f6;
  border-radius: 20px;
  text-decoration: none;
  color: #333;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-notifications:hover, .btn-bookmarks:hover {
  background-color: #e5e7eb;
}

.notification-badge {
  background-color: #ef4444;
  color: white;
  border-radius: 50%;
  min-width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  margin-left: 5px;
}

/* 论坛统计样式 */
.forum-stats {
  display: flex;
  gap: 20px;
  background-color: #f9fafb;
  border-radius: 10px;
  padding: 15px;
  margin-bottom: 20px;
  justify-content: space-around;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #3b82f6;
}

.stat-label {
  font-size: 14px;
  color: #6b7280;
  margin-top: 5px;
}

/* 论坛布局 */
.forum-layout {
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: 20px;
}

/* 热门话题部分 */
.forum-sidebar {
  background-color: #f9fafb;
  border-radius: 10px;
  padding: 15px;
}

.section-title {
  font-size: 18px;
  margin-top: 0;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid #e5e7eb;
}

.hot-topics-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.hot-topic-item {
  padding: 10px;
  border-radius: 5px;
  transition: all 0.2s;
}

.hot-topic-item:hover {
  background-color: #f3f4f6;
}

.topic-link {
  text-decoration: none;
  color: inherit;
  display: block;
}

.topic-title {
  font-weight: 500;
  color: #1f2937;
  margin-bottom: 5px;
}

.topic-meta {
  display: flex;
  gap: 15px;
  font-size: 12px;
  color: #6b7280;
}

.topic-views, .topic-posts {
  display: flex;
  align-items: center;
}

.category-section {
  margin-bottom: 30px;
}

.category-header {
  margin-bottom: 15px;
}

.category-title {
  display: flex;
  align-items: center;
  font-size: 20px;
  margin: 0;
  color: #333;
}

.category-icon {
  margin-right: 10px;
  font-size: 18px;
  color: #3b82f6;
}

.category-description {
  margin: 5px 0 0 28px;
  color: #666;
  font-size: 14px;
}

.board-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 15px;
}

.board-card {
  background-color: #fff;
  border-radius: 8px;
  padding: 15px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: all 0.2s;
  cursor: pointer;
}

.board-card:hover {
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.board-header {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.board-icon {
  margin-right: 10px;
  font-size: 16px;
  color: #3b82f6;
}

.board-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.board-description {
  margin: 0 0 15px;
  font-size: 14px;
  color: #4b5563;
}

.board-stats {
  display: flex;
  gap: 15px;
  margin-bottom: 10px;
  font-size: 12px;
  color: #6b7280;
}

.board-stats .stat-item {
  display: flex;
  align-items: center;
}

.board-stats .stat-item i {
  margin-right: 5px;
}

.board-last-post {
  font-size: 12px;
  color: #6b7280;
}

.last-post-label {
  font-weight: 500;
  margin-right: 5px;
}

.no-boards-message {
  background-color: #f9fafb;
  padding: 20px;
  border-radius: 8px;
  text-align: center;
  color: #6b7280;
}

.loading-container {
  padding: 20px;
}

.error-message {
  background-color: #fee2e2;
  color: #b91c1c;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 20px;
}

@media (max-width: 768px) {
  .forum-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .forum-actions {
    margin-top: 15px;
  }
  
  .forum-layout {
    grid-template-columns: 1fr;
  }
  
  .board-grid {
    grid-template-columns: 1fr;
  }
  
  .forum-stats {
    flex-wrap: wrap;
  }
  
  .stat-item {
    flex: 1 0 40%;
  }
}
</style> 