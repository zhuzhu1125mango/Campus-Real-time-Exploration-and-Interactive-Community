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
    
    <!-- 全局搜索框 -->
    <div class="forum-search">
      <div class="search-container">
        <input
          type="text"
          v-model="searchQuery"
          placeholder="搜索话题、帖子或用户..."
          class="search-input"
          maxlength="100"
          @input="performSearch"
          @keyup.enter="performSearch"
        />
        <button class="search-button" @click="performSearch">
          <span class="icon-search"></span>
        </button>
        <div v-if="searchQuery" class="search-filters">
          <select v-model="searchType" class="search-filter">
            <option value="all">全部</option>
            <option value="topic">话题</option>
            <option value="post">帖子</option>
            <option value="user">用户</option>
          </select>
        </div>
      </div>
      
      <!-- 搜索结果 -->
      <div v-if="showSearchResults" class="search-results">
        <div v-if="searchLoading" class="loading-container">
          <div class="loading-spinner"></div>
        </div>
        <div v-else-if="searchResults.length === 0" class="no-search-results">
          <p>未找到相关结果</p>
        </div>
        <div v-else class="search-results-list">
          <div 
            v-for="result in searchResults" 
            :key="`${result.type}-${result.id}`" 
            class="search-result-item"
            @click="goToSearchResult(result)"
          >
            <div class="result-icon">
              <img v-if="result.type === 'user'" :src="result.avatar || defaultAvatar" class="result-avatar" :alt="result.username">
              <span v-else-if="result.type === 'topic'" class="icon-topic"></span>
              <span v-else-if="result.type === 'post'" class="icon-post"></span>
              <span v-else class="icon-user"></span>
            </div>
            <div class="result-content">
              <h4 class="result-title">{{ getSearchResultTitle(result) }}</h4>
              <p class="result-meta">
                <span>{{ getSearchResultMeta(result) }}</span>
                <span>{{ formatActivityTime(result.created_at) }}</span>
              </p>
              <p v-if="result.type === 'post' && result.summary" class="result-summary">
                {{ result.summary }}
              </p>
            </div>
            <div class="result-stats">
              <template v-if="result.type === 'topic'">
                <span>{{ result.views || 0 }} 浏览</span>
                <span>{{ result.post_count || 0 }} 回复</span>
              </template>
              <template v-else-if="result.type === 'post'">
                <span>{{ result.like_count || 0 }} 点赞</span>
              </template>
              <template v-else-if="result.type === 'user'">
                <span>用户</span>
              </template>
            </div>
          </div>
        </div>
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
      <!-- 左侧：分类、板块和最新主题 -->
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
            <template v-for="category in categories" :key="category?.id">
              <div v-if="category && category.id" class="category-section">
                <div class="category-header">
                  <h2 class="category-title">
                    <el-icon class="category-icon">
                      <component :is="resolveIcon(category.icon) || Folder" />
                    </el-icon>
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
                        <el-icon class="board-icon">
                          <component :is="resolveIcon(board.icon) || Menu" />
                        </el-icon>
                        <h3 class="board-title">{{ board.name }}</h3>
                      </div>
                      <p v-if="board.description" class="board-description">{{ board.description }}</p>
                      <div class="board-stats">
                        <span class="stat-item">
                          <el-icon><ChatDotSquare /></el-icon>
                          {{ board.topic_count || 0 }} 主题
                        </span>
                        <span class="stat-item">
                          <el-icon><Document /></el-icon>
                          {{ board.post_count || 0 }} 帖子
                        </span>
                      </div>
                      <div v-if="board.last_post" class="board-last-post">
                        <span class="last-post-label">最新:</span>
                        <span class="last-post-info">
                          {{ truncateText(board.last_post.title || '', 20) }}
                          <template v-if="board.last_post.author">
                            by {{ board.last_post.author.username || '未知用户' }}
                          </template>
                          {{ formatDate(board.last_post.created_at || new Date().toISOString()) }}
                        </span>
                      </div>
                    </div>
                  </div>
                </template>
                <div v-else class="no-boards-message">
                  暂无板块
                </div>
              </div>
            </template>
          </div>
        </div>

        <!-- 最新主题列表 -->
        <div class="latest-topics-section">
          <div class="section-header">
            <h2 class="section-title">最新主题</h2>
          </div>
          <div v-if="latestTopicsLoading" class="loading-container">
            <el-skeleton :rows="5" animated />
          </div>
          <div v-else-if="latestTopics.length === 0" class="no-data">
            暂无主题，点击板块进入发布第一个主题
          </div>
          <div v-else class="latest-topics-list">
            <div
              v-for="topic in latestTopics"
              :key="topic.id"
              class="latest-topic-item"
              @click="goToTopic(topic.id)"
            >
              <div class="topic-main">
                <h3 class="topic-title">{{ truncateText(topic.title, 40) }}</h3>
                <div class="topic-meta">
                  <span class="topic-board">{{ topic.board_name || '未知板块' }}</span>
                  <span class="topic-author">{{ topic.author?.username || '匿名用户' }}</span>
                  <span class="topic-time">{{ formatActivityTime(topic.created_at) }}</span>
                </div>
              </div>
              <div class="topic-stats">
                <span><el-icon><View /></el-icon> {{ topic.views || 0 }}</span>
                <span><el-icon><ChatDotSquare /></el-icon> {{ topic.reply_count || 0 }}</span>
              </div>
            </div>
          </div>
          <div v-if="latestTopicsTotalPages > 1" class="pagination">
            <el-pagination
              v-model:current-page="latestTopicsPage"
              :page-size="latestTopicsPageSize"
              :total="latestTopicsTotal"
              layout="prev, pager, next"
              @current-change="handleLatestTopicsPageChange"
            />
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
        
        <!-- 热门标签 -->
        <div class="hot-tags-section">
          <h3 class="section-title">热门标签</h3>
          <div v-if="loadingHotTags" class="loading">
            <el-skeleton :rows="3" animated />
          </div>
          <div v-else>
            <TagCloud 
              :tags="hotTags" 
              title="" 
              @select="handleTagSelect" 
            />
          </div>
        </div>
        
        <!-- 最新动态 -->
        <div class="latest-activities-section">
          <h3 class="section-title">最新动态</h3>
          <div v-if="activitiesLoading" class="loading">
            <el-skeleton :rows="3" animated />
          </div>
          <div v-else-if="activitiesError" class="error-message">
            {{ activitiesError }}
          </div>
          <div v-else-if="activities.length === 0" class="no-data">
            暂无动态
          </div>
          <div v-else class="activities-list">
            <div v-for="activity in activities" :key="activity.id" class="activity-item">
              <div class="activity-avatar">
                <img :src="activity.user?.avatar || 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=user%20avatar%20placeholder&image_size=square'" :alt="activity.user?.username">
              </div>
              <div class="activity-content">
                <div class="activity-header">
                  <span class="activity-author">{{ activity.user?.username }}</span>
                  <span class="activity-time">{{ formatActivityTime(activity.created_at) }}</span>
                </div>
                <p class="activity-text">{{ truncateText(activity.content, 40) }}</p>
                <div class="activity-actions">
                  <button class="action-btn" @click="toggleLike(activity.id)">
                    <span :class="['like-icon', { 'liked': activity.is_liked }]">{{ activity.is_liked ? '♥' : '♡' }}</span>
                    <span>{{ activity.likes_count }}</span>
                  </button>
                  <span class="comment-count">
                    <span class="comment-icon">💬</span>
                    <span>{{ activity.comments_count }}</span>
                  </span>
                </div>
              </div>
            </div>
          </div>
          <button v-if="hasMore && !activitiesLoading" class="load-more-btn" @click="loadActivities">
            加载更多
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  Folder, Menu, ChatDotSquare, Document, View
} from '@element-plus/icons-vue'
import type { Component as VueComponent } from 'vue'
import { forumApi } from '@/api/forum'
import { userApi } from '@/api/user'
import { useUserStore } from '@/stores/userStore'
import { stripHtml } from '@/utils/xss'
import { debounce } from '@/utils/debounce'
import TagCloud from '@/components/TagCloud.vue'
import type { Category, Board, Topic, ForumStats } from '@/types/forum'
import type { User } from '@/types/user'

interface Tag {
  id: number
  name: string
  count: number
}

// 旧 Element UI 图标类名映射到 Element Plus 图标组件
const iconMap: Record<string, VueComponent> = {
  'el-icon-folder': Folder,
  'el-icon-menu': Menu,
  'el-icon-chat-dot-square': ChatDotSquare,
  'el-icon-document': Document,
  'el-icon-view': View
}

const resolveIcon = (iconName?: string) => {
  if (!iconName) return undefined
  return iconMap[iconName]
}

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

// 用户动态
const activities = ref<any[]>([])
const activitiesLoading = ref(true)
const activitiesError = ref<string | null>(null)
const hasMore = ref(true)
const page = ref(1)

// 热门标签
const hotTags = ref<Tag[]>([])
const loadingHotTags = ref(true)
const errorHotTags = ref<string | null>(null)
const selectedTag = ref<Tag | null>(null)

// 最新主题
const latestTopics = ref<Topic[]>([])
const latestTopicsLoading = ref(true)
const latestTopicsPage = ref(1)
const latestTopicsPageSize = ref(10)
const latestTopicsTotal = ref(0)
const latestTopicsTotalPages = computed(() => Math.ceil(latestTopicsTotal.value / latestTopicsPageSize.value))

// 搜索相关状态
const searchQuery = ref('')
const searchType = ref('all')
const searchResults = ref<any[]>([])
const searchLoading = ref(false)
const showSearchResults = ref(false)
const defaultAvatar = 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=user%20avatar%20placeholder&image_size=square'

// 声明需要的变量

// 登录状态
const isLoggedIn = computed(() => userStore.isLoggedIn)

// 获取分类列表
const fetchCategories = async () => {
  loading.value = true
  error.value = null
  
  try {
    const response = await forumApi.getCategories()
    // 确保response是数组并过滤掉无效元素
    if (Array.isArray(response)) {
      categories.value = response.filter(category => 
        category && typeof category === 'object' && 'id' in category
      )
    } else {
      categories.value = []
    }
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

// 加载用户动态
const loadActivities = async () => {
  if (activitiesLoading.value) return
  
  activitiesLoading.value = true
  activitiesError.value = null
  
  try {
    const response = await userApi.getActivities({
      page: page.value,
      page_size: 5
    })
    
    if (page.value === 1) {
      activities.value = response.results
    } else {
      activities.value = [...activities.value, ...response.results]
    }
    
    hasMore.value = response.results.length === 5
    page.value++
    console.log('获取用户动态成功:', activities.value)
  } catch (error) {
    console.error('加载用户动态失败:', error)
    activitiesError.value = '加载动态失败'
  } finally {
    activitiesLoading.value = false
  }
}

// 获取热门标签
const fetchHotTags = async () => {
  loadingHotTags.value = true
  errorHotTags.value = null
  
  try {
    const response = await forumApi.getHotTags()
    hotTags.value = response.map(tag => ({
      id: tag.id,
      name: tag.name,
      count: tag.topic_count || 0
    }))
    console.log('获取热门标签成功:', hotTags.value)
  } catch (err) {
    console.error('获取热门标签失败:', err)
    hotTags.value = [
      { id: 1, name: '考研', count: 128 },
      { id: 2, name: '校园生活', count: 96 },
      { id: 3, name: '就业', count: 85 },
      { id: 4, name: '专业选择', count: 72 },
      { id: 5, name: '学习方法', count: 64 },
      { id: 6, name: '留学', count: 58 },
      { id: 7, name: '保研', count: 45 },
      { id: 8, name: '校园活动', count: 38 },
    ]
    errorHotTags.value = '获取热门标签失败，使用默认标签'
  } finally {
    loadingHotTags.value = false
  }
}

// 获取最新主题
const fetchLatestTopics = async () => {
  latestTopicsLoading.value = true
  try {
    const response = await forumApi.getLatestTopics(latestTopicsPage.value, latestTopicsPageSize.value)
    latestTopics.value = response.results
    latestTopicsTotal.value = response.count
  } catch (err) {
    console.error('获取最新主题失败:', err)
    latestTopics.value = []
    latestTopicsTotal.value = 0
  } finally {
    latestTopicsLoading.value = false
  }
}

// 最新主题分页变化
const handleLatestTopicsPageChange = (page: number) => {
  latestTopicsPage.value = page
  fetchLatestTopics()
}

// 选择标签
const handleTagSelect = (tag: Tag) => {
  selectedTag.value = tag
  router.push(`/forum/tag/${tag.id}?name=${encodeURIComponent(tag.name)}`)
}

// 切换点赞
const toggleLike = async (activityId: number) => {
  try {
    const activity = activities.value.find(a => a.id === activityId)
    if (!activity) return
    
    if (activity.is_liked) {
      await userApi.unlikeActivity(activityId)
    } else {
      await userApi.likeActivity(activityId)
    }
    
    activity.is_liked = !activity.is_liked
    activity.likes_count += activity.is_liked ? 1 : -1
  } catch (error) {
    console.error('切换点赞失败:', error)
  }
}

// 执行搜索（防抖）
const performSearch = debounce(async () => {
  const query = searchQuery.value.trim()
  if (!query) {
    showSearchResults.value = false
    searchResults.value = []
    return
  }

  searchLoading.value = true
  searchResults.value = []

  try {
    const type = searchType.value
    const results: any[] = []

    if (type === 'all' || type === 'topic') {
      try {
        const topicRes = await forumApi.searchTopics(query, 1, 10)
        results.push(...topicRes.results.map(t => ({ type: 'topic' as const, ...t })))
      } catch (err) {
        console.error('搜索话题失败:', err)
      }
    }

    if (type === 'all' || type === 'post') {
      try {
        const postRes = await forumApi.searchPosts(query, 1, 10)
        results.push(...postRes.results.map(p => ({
          type: 'post' as const,
          summary: truncateText(stripHtml(p.content), 80),
          ...p
        })))
      } catch (err) {
        console.error('搜索帖子失败:', err)
      }
    }

    if (type === 'all' || type === 'user') {
      try {
        const users = await userApi.searchUsers(query)
        results.push(...users.map((u: User) => ({ type: 'user' as const, ...u })))
      } catch (err) {
        console.error('搜索用户失败:', err)
      }
    }

    // 按时间排序，越新的越靠前
    results.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    searchResults.value = results
    showSearchResults.value = true
  } catch (error) {
    console.error('搜索失败:', error)
    searchResults.value = []
  } finally {
    searchLoading.value = false
  }
}, 400)

// 获取搜索结果标题
const getSearchResultTitle = (result: any) => {
  if (result.type === 'topic') return result.title || '无标题'
  if (result.type === 'post') return result.topic_title || '帖子回复'
  if (result.type === 'user') return result.username || '未知用户'
  return ''
}

// 获取搜索结果元信息
const getSearchResultMeta = (result: any) => {
  if (result.type === 'topic') return result.author?.username || '匿名用户'
  if (result.type === 'post') return `${result.author?.username || '匿名用户'} · 回复于 ${result.topic_title || '未知主题'}`
  if (result.type === 'user') return result.email || ''
  return ''
}

// 跳转到搜索结果详情
const goToSearchResult = (result: any) => {
  if (result.type === 'topic') {
    router.push(`/forum/topic/${result.id}`)
  } else if (result.type === 'post') {
    router.push(`/forum/topic/${result.topic}#post-${result.id}`)
  } else if (result.type === 'user') {
    router.push(`/profile/${result.id}`)
  }
  clearSearch()
}

// 清空搜索
const clearSearch = () => {
  searchQuery.value = ''
  showSearchResults.value = false
  searchResults.value = []
}

// 跳转到话题详情
const goToTopic = (topicId: number) => {
  router.push(`/forum/topic/${topicId}`)
  clearSearch()
}

// 格式化动态时间
const formatActivityTime = (timeString: string) => {
  if (!timeString) return ''
  const date = new Date(timeString)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)
  
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  
  return date.toLocaleDateString('zh-CN')
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
  return boards.value.filter(board => board && typeof board === 'object' && 'id' in board && board.category === categoryId)
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
      fetchHotTopics(),
      fetchHotTags(),
      loadActivities(),
      fetchLatestTopics()
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

/* 搜索样式 */
.forum-search {
  margin-bottom: 20px;
  position: relative;
}

.search-container {
  display: flex;
  align-items: center;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  padding: 8px;
}

.search-input {
  flex: 1;
  padding: 10px 15px;
  border: none;
  outline: none;
  font-size: 14px;
}

.search-button {
  padding: 10px 15px;
  background-color: #4361ee;
  border: none;
  border-radius: 6px;
  color: white;
  cursor: pointer;
  transition: background-color 0.2s;
}

.search-button:hover {
  background-color: #3a56d4;
}

.icon-search {
  display: inline-block;
  width: 18px;
  height: 18px;
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white"><path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.77l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/></svg>');
  background-size: contain;
  background-repeat: no-repeat;
}

.search-filters {
  margin-left: 10px;
}

.search-filter {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  background-color: white;
  font-size: 14px;
  cursor: pointer;
}

/* 搜索结果样式 */
.search-results {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  margin-top: 10px;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  z-index: 100;
  overflow: hidden;
}

.search-results-list {
  max-height: 400px;
  overflow-y: auto;
}

.search-result-item {
  display: flex;
  align-items: center;
  padding: 12px 15px;
  cursor: pointer;
  border-bottom: 1px solid #f0f0f0;
  transition: background-color 0.2s;
}

.search-result-item:last-child {
  border-bottom: none;
}

.search-result-item:hover {
  background-color: #f8f9fa;
}

.result-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background-color: #f0f4ff;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 15px;
}

.icon-topic,
.icon-post,
.icon-user {
  display: inline-block;
  width: 20px;
  height: 20px;
  background-size: contain;
  background-repeat: no-repeat;
}

.icon-topic {
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%234361ee"><path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z"/></svg>');
}

.icon-post {
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%234361ee"><path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm1 16H7v-2h8v2zm0-4H7v-2h8v2zm-3-5V3.5L18.5 9H13z"/></svg>');
}

.icon-user {
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%234361ee"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>');
}

.result-content {
  flex: 1;
  min-width: 0;
}

.result-title {
  margin: 0 0 5px 0;
  font-size: 15px;
  font-weight: 600;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.result-meta {
  margin: 0;
  font-size: 13px;
  color: #999;
  display: flex;
  gap: 10px;
}

.result-stats {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  font-size: 12px;
  color: #666;
}

.result-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  object-fit: cover;
}

.result-summary {
  margin: 4px 0 0 0;
  font-size: 13px;
  color: #666;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.no-search-results {
  padding: 30px;
  text-align: center;
  color: #999;
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

/* 用户动态样式 */
.latest-activities-section {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e5e7eb;
}

.activities-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.activity-item {
  display: flex;
  gap: 10px;
  padding: 10px;
  border-radius: 8px;
  transition: background-color 0.2s;
}

.activity-item:hover {
  background-color: #f9fafb;
}

.activity-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
}

.activity-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.activity-content {
  flex: 1;
  min-width: 0;
}

.activity-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.activity-author {
  font-weight: 600;
  font-size: 13px;
  color: #1f2937;
}

.activity-time {
  font-size: 11px;
  color: #9ca3af;
}

.activity-text {
  margin: 0 0 6px 0;
  font-size: 13px;
  color: #4b5563;
  line-height: 1.4;
  word-break: break-all;
}

.activity-actions {
  display: flex;
  gap: 12px;
  font-size: 12px;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  background: none;
  border: none;
  color: #6b7280;
  cursor: pointer;
  padding: 2px 4px;
  border-radius: 4px;
  transition: all 0.2s;
}

.action-btn:hover {
  background-color: #f3f4f6;
}

.like-icon {
  font-size: 14px;
}

.like-icon.liked {
  color: #ef4444;
}

.comment-count {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #6b7280;
}

.comment-icon {
  font-size: 12px;
}

.load-more-btn {
  width: 100%;
  padding: 8px;
  margin-top: 10px;
  background-color: #f3f4f6;
  border: none;
  border-radius: 6px;
  color: #4361ee;
  font-size: 13px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.load-more-btn:hover {
  background-color: #e5e7eb;
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