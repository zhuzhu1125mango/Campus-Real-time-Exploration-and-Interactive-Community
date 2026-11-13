<template>
  <div class="forum-page container-wide page-padding">
    <div class="forum-hero">
      <div class="forum-hero-main">
        <h1 class="forum-title">校园论坛</h1>
        <p class="forum-description">分享知识，交流经验，连接每一个校园观点</p>
      </div>
      <div v-if="isLoggedIn" class="forum-actions">
        <router-link to="/forum/notifications" class="action-link">
          <span class="i-ep-bell action-icon" />
          通知
          <span v-if="unreadNotificationsCount > 0" class="notification-badge">
            {{ unreadNotificationsCount }}
          </span>
        </router-link>
        <router-link to="/forum/bookmarks" class="action-link">
          <span class="i-ep-star action-icon" />
          收藏
        </router-link>
      </div>
    </div>

    <!-- 全局搜索框 -->
    <GlassCard :hover="false" class="search-card" padding="md">
      <div class="forum-search">
        <div class="search-container">
          <span class="i-ep-search search-icon" />
          <input
            v-model="searchQuery"
            type="text"
            placeholder="搜索话题、帖子或用户..."
            class="search-input"
            maxlength="100"
            @input="performSearch"
            @keyup.enter="performSearch"
          />
          <button class="search-button" @click="performSearch">
            <span class="i-ep-search" />
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
                <img
                  v-if="result.type === 'user'"
                  :src="result.avatar || defaultAvatar"
                  class="result-avatar"
                  :alt="result.username"
                />
                <span v-else-if="result.type === 'topic'" class="i-ep-chat-dot-round" />
                <span v-else-if="result.type === 'post'" class="i-ep-document" />
                <span v-else class="i-ep-user" />
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
    </GlassCard>

    <!-- 论坛统计信息 -->
    <div class="forum-stats">
      <GlassCard v-for="stat in statsList" :key="stat.label" :hover="true" class="stat-card" padding="sm">
        <div class="stat-value">{{ stat.value }}</div>
        <div class="stat-label">{{ stat.label }}</div>
      </GlassCard>
    </div>

    <div class="forum-layout">
      <!-- 左侧：分类、板块和最新主题 -->
      <div class="forum-main">
        <!-- 论坛分类和版块 -->
        <GlassCard :hover="false" class="forum-content-card">
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
                    <GlassCard
                      v-for="board in getBoardsByCategory(category.id)"
                      :key="board.id"
                      :hover="true"
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
                        <span class="board-stat">
                          <el-icon><ChatDotSquare /></el-icon>
                          {{ board.topic_count || 0 }} 主题
                        </span>
                        <span class="board-stat">
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
                    </GlassCard>
                  </div>
                </template>
                <div v-else class="no-boards-message">暂无板块</div>
              </div>
            </template>
          </div>
        </GlassCard>

        <!-- 最新主题列表 -->
        <GlassCard :hover="false" class="latest-topics-card">
          <SectionHeader title="最新主题" subtitle="看看大家都在聊什么" icon="i-ep-chat-dot-square" />
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
        </GlassCard>
      </div>

      <!-- 右侧：热门话题和最新活动 -->
      <aside class="forum-sidebar">
        <!-- 热门话题 -->
        <GlassCard :hover="false" class="sidebar-card" title="热门话题" subtitle="本周最受关注">
          <div v-if="loadingHotTopics" class="loading">
            <el-skeleton :rows="3" animated />
          </div>
          <div v-else-if="errorHotTopics" class="error-message">
            {{ errorHotTopics }}
          </div>
          <div v-else-if="hotTopics.length === 0" class="no-data">暂无热门话题</div>
          <div v-else class="hot-topics-list">
            <div v-for="topic in hotTopics" :key="topic.id" class="hot-topic-item">
              <router-link :to="`/forum/topic/${topic.id}`" class="topic-link">
                <div class="hot-topic-title">{{ truncateText(topic.title, 30) }}</div>
                <div class="hot-topic-meta">
                  <span class="topic-views">{{ topic.views }} 浏览</span>
                  <span class="topic-posts">{{ topic.post_count }} 回复</span>
                </div>
              </router-link>
            </div>
          </div>
        </GlassCard>

        <!-- 热门标签 -->
        <GlassCard :hover="false" class="sidebar-card" title="热门标签" subtitle="发现感兴趣的话题">
          <div v-if="loadingHotTags" class="loading">
            <el-skeleton :rows="3" animated />
          </div>
          <div v-else>
            <TagCloud :tags="hotTags" title="" @select="handleTagSelect" />
          </div>
        </GlassCard>

        <!-- 最新动态 -->
        <GlassCard :hover="false" class="sidebar-card" title="最新动态" subtitle="校园新鲜事">
          <div v-if="activitiesLoading" class="loading">
            <el-skeleton :rows="3" animated />
          </div>
          <div v-else-if="activitiesError" class="error-message">
            {{ activitiesError }}
          </div>
          <div v-else-if="activities.length === 0" class="no-data">暂无动态</div>
          <div v-else class="activities-list">
            <div v-for="activity in activities" :key="activity.id" class="activity-item">
              <div class="activity-avatar">
                <img
                  :src="activity.user?.avatar || defaultAvatar"
                  :alt="activity.user?.username"
                />
              </div>
              <div class="activity-content">
                <div class="activity-header">
                  <span class="activity-author">{{ activity.user?.username }}</span>
                  <span class="activity-time">{{ formatActivityTime(activity.created_at) }}</span>
                </div>
                <p class="activity-text">{{ truncateText(activity.content || '', 40) }}</p>
                <div class="activity-actions">
                  <button class="action-btn" @click="toggleLike(activity.id)">
                    <span class="like-icon" :class="{ liked: activity.is_liked }">
                      {{ activity.is_liked ? '♥' : '♡' }}
                    </span>
                    <span>{{ activity.likes_count }}</span>
                  </button>
                  <span class="comment-count">
                    <span class="i-ep-chat-dot-round comment-icon" />
                    <span>{{ activity.comments_count }}</span>
                  </span>
                </div>
              </div>
            </div>
          </div>
          <button v-if="hasMore && !activitiesLoading" class="load-more-btn" @click="loadActivities">
            加载更多
          </button>
        </GlassCard>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { logger } from '@/utils/logger'
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Folder, Menu, ChatDotSquare, Document, View } from '@element-plus/icons-vue'
import type { Component as VueComponent } from 'vue'
import { forumApi } from '@/api/forum'
import { userApi } from '@/api/user'
import { useUserStore } from '@/stores/userStore'
import { stripHtml } from '@/utils/xss'
import { debounce } from '@/utils/debounce'
import TagCloud from '@/components/TagCloud.vue'
import GlassCard from '@/components/GlassCard.vue'
import SectionHeader from '@/components/SectionHeader.vue'
import type { Category, Board, Topic, Post, ForumStats } from '@/types/forum'
import type { User, Activity } from '@/types/user'

type SearchResultTopic = Topic & { type: 'topic' }
type SearchResultPost = Post & { type: 'post'; summary?: string; topic_title?: string }
type SearchResultUser = User & { type: 'user' }
type SearchResult = SearchResultTopic | SearchResultPost | SearchResultUser

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
const activities = ref<Activity[]>([])
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
const latestTopicsTotalPages = computed(() =>
  Math.ceil(latestTopicsTotal.value / latestTopicsPageSize.value)
)

// 搜索相关状态
const searchQuery = ref('')
const searchType = ref('all')
const searchResults = ref<SearchResult[]>([])
const searchLoading = ref(false)
const showSearchResults = ref(false)
const defaultAvatar = '/trae-api/api/ide/v1/text_to_image?prompt=user%20avatar%20placeholder&image_size=square'

// 登录状态
const isLoggedIn = computed(() => userStore.isLoggedIn)

const statsList = computed(() => [
  { value: statsData.value.user_count, label: '注册用户' },
  { value: statsData.value.topic_count, label: '话题数' },
  { value: statsData.value.post_count, label: '帖子数' },
  { value: statsData.value.today_post_count, label: '今日帖子' }
])

// 获取分类列表
const fetchCategories = async () => {
  loading.value = true
  error.value = null

  try {
    const response = await forumApi.getCategories()
    if (Array.isArray(response)) {
      categories.value = response.filter(
        (category) => category && typeof category === 'object' && 'id' in category
      )
    } else {
      categories.value = []
    }
    logger.log('获取分类成功:', categories.value)
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
    if (Array.isArray(response)) {
      boards.value = response
    } else if (response && typeof response === 'object' && 'results' in response) {
      boards.value = (response as { results: Board[] }).results
    } else {
      console.error('API返回的板块数据格式不正确:', response)
      boards.value = []
    }
    logger.log('获取板块成功:', boards.value)
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
    const days = 7
    const limit = 10
    const response = await forumApi.getHotTopics(days, limit)
    hotTopics.value = response
    logger.log('获取热门话题成功:', hotTopics.value)
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
    logger.log('获取用户动态成功:', activities.value)
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
    hotTags.value = response.map((tag) => ({
      id: tag.id,
      name: tag.name,
      count: tag.topic_count || 0
    }))
    logger.log('获取热门标签成功:', hotTags.value)
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
      { id: 8, name: '校园活动', count: 38 }
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
    const activity = activities.value.find((a) => a.id === activityId)
    if (!activity) return

    if (activity.is_liked) {
      await userApi.unlikeActivity(activityId)
    } else {
      await userApi.likeActivity(activityId)
    }

    activity.is_liked = !activity.is_liked
    activity.likes_count = (activity.likes_count || 0) + (activity.is_liked ? 1 : -1)
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
    const results: SearchResult[] = []

    if (type === 'all' || type === 'topic') {
      try {
        const topicRes = await forumApi.searchTopics(query, 1, 10)
        results.push(...topicRes.results.map((t) => ({ type: 'topic' as const, ...t })))
      } catch (err) {
        console.error('搜索话题失败:', err)
      }
    }

    if (type === 'all' || type === 'post') {
      try {
        const postRes = await forumApi.searchPosts(query, 1, 10)
        results.push(
          ...postRes.results.map((p) => ({
            type: 'post' as const,
            summary: truncateText(stripHtml(p.content), 80),
            ...p
          }))
        )
      } catch (err) {
        console.error('搜索帖子失败:', err)
      }
    }

    if (type === 'all' || type === 'user') {
      try {
        const users = await userApi.searchUsers(query)
        results.push(...users.map((u) => ({ type: 'user' as const, ...u })))
      } catch (err) {
        console.error('搜索用户失败:', err)
      }
    }

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
const getSearchResultTitle = (result: SearchResult) => {
  if (result.type === 'topic') return result.title || '无标题'
  if (result.type === 'post') return result.topic_title || '帖子回复'
  if (result.type === 'user') return result.username || '未知用户'
  return ''
}

// 获取搜索结果元信息
const getSearchResultMeta = (result: SearchResult) => {
  if (result.type === 'topic') return result.author?.username || '匿名用户'
  if (result.type === 'post')
    return `${result.author?.username || '匿名用户'} · 回复于 ${result.topic_title || '未知主题'}`
  if (result.type === 'user') return result.email || ''
  return ''
}

// 跳转到搜索结果详情
const goToSearchResult = (result: SearchResult) => {
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
    logger.log('用户未登录，跳过获取通知')
    return
  }

  try {
    const response = await userApi.getUnreadNotificationsCount()
    unreadNotificationsCount.value = response?.unread_count || 0
    logger.log('获取到未读通知数量:', unreadNotificationsCount.value)
  } catch (error) {
    console.error('获取未读通知失败:', getErrorMessage(error, '未知错误'))
    unreadNotificationsCount.value = 0
  }
}

// 获取论坛统计数据
const fetchForumStats = async () => {
  try {
    const response = await forumApi.getForumStats()
    statsData.value = response
    logger.log('获取论坛统计成功:', statsData.value)
  } catch (error) {
    console.error('获取论坛统计失败:', error)
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
  return boards.value.filter(
    (board) => board && typeof board === 'object' && 'id' in board && board.category === categoryId
  )
}

// 导航到板块详情页
const navigateToBoard = (boardId: number) => {
  router.push(`/forum/board/${boardId}`)
}

// 从 unknown 错误中提取可读消息
const getErrorMessage = (err: unknown, defaultMsg: string): string => {
  if (err instanceof Error) return err.message
  if (
    err &&
    typeof err === 'object' &&
    'message' in err &&
    typeof (err as { message?: unknown }).message === 'string'
  ) {
    return (err as { message: string }).message
  }
  return defaultMsg
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
.forum-page {
  min-height: 100vh;
}

.forum-hero {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-6);
  gap: var(--space-4);
}

.forum-title {
  font-size: 1.875rem;
  font-weight: 800;
  margin: 0 0 var(--space-2) 0;
  color: var(--text-primary);
}

.forum-description {
  margin: 0;
  color: var(--text-secondary);
  font-size: 1rem;
}

.forum-actions {
  display: flex;
  gap: var(--space-3);
  flex-shrink: 0;
}

.action-link {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  background: var(--bg-tertiary);
  border-radius: var(--radius-full);
  text-decoration: none;
  color: var(--text-primary);
  font-weight: 500;
  font-size: 0.9rem;
  transition: all 0.2s ease;
}

.action-link:hover {
  background: var(--primary-100);
  color: var(--primary-600);
}

.action-icon {
  width: 18px;
  height: 18px;
}

.notification-badge {
  background-color: var(--error-color);
  color: var(--text-inverse);
  border-radius: var(--radius-full);
  min-width: 18px;
  height: 18px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  padding: 0 5px;
}

.search-card {
  margin-bottom: var(--space-6);
  position: relative;
}

.search-container {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: var(--space-2) var(--space-3);
}

.search-icon {
  width: 20px;
  height: 20px;
  color: var(--text-tertiary);
  margin-left: var(--space-2);
}

.search-input {
  flex: 1;
  padding: var(--space-2);
  border: none;
  outline: none;
  font-size: 0.95rem;
  color: var(--text-primary);
  background: transparent;
}

.search-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: var(--primary-600);
  border: none;
  border-radius: var(--radius-md);
  color: var(--text-inverse);
  cursor: pointer;
  transition: background-color 0.2s;
  flex-shrink: 0;
}

.search-button:hover {
  background: var(--primary-700);
}

.search-filters {
  flex-shrink: 0;
}

.search-filter {
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-primary);
  font-size: 0.9rem;
  color: var(--text-primary);
  cursor: pointer;
}

.search-results {
  position: absolute;
  top: calc(100% + var(--space-3));
  left: var(--space-5);
  right: var(--space-5);
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
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
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  cursor: pointer;
  border-bottom: 1px solid var(--border-color-light);
  transition: background-color 0.2s;
}

.search-result-item:last-child {
  border-bottom: none;
}

.search-result-item:hover {
  background-color: var(--bg-secondary);
}

.result-icon {
  width: 42px;
  height: 42px;
  border-radius: var(--radius-md);
  background: var(--primary-50);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--primary-600);
  font-size: 1.25rem;
  flex-shrink: 0;
}

.result-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  object-fit: cover;
}

.result-content {
  flex: 1;
  min-width: 0;
}

.result-title {
  margin: 0 0 4px 0;
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.result-meta {
  margin: 0;
  font-size: 0.8rem;
  color: var(--text-tertiary);
  display: flex;
  gap: var(--space-3);
}

.result-summary {
  margin: 4px 0 0 0;
  font-size: 0.8rem;
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.result-stats {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
  font-size: 0.75rem;
  color: var(--text-tertiary);
  flex-shrink: 0;
}

.no-search-results {
  padding: var(--space-8);
  text-align: center;
  color: var(--text-tertiary);
}

.forum-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-4);
  margin-bottom: var(--space-6);
}

.stat-card {
  text-align: center;
}

.stat-value {
  font-size: 1.75rem;
  font-weight: 800;
  color: var(--primary-600);
  margin-bottom: var(--space-1);
}

.stat-label {
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.forum-layout {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: var(--space-6);
  align-items: start;
}

.forum-main {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.forum-content-card {
  min-height: 200px;
}

.category-section {
  margin-bottom: var(--space-8);
}

.category-section:last-child {
  margin-bottom: 0;
}

.category-header {
  margin-bottom: var(--space-4);
}

.category-title {
  display: flex;
  align-items: center;
  font-size: 1.25rem;
  font-weight: 700;
  margin: 0;
  color: var(--text-primary);
}

.category-icon {
  margin-right: var(--space-2);
  font-size: 1.25rem;
  color: var(--primary-600);
}

.category-description {
  margin: var(--space-1) 0 0 32px;
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.board-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--space-4);
}

.board-card {
  cursor: pointer;
}

.board-header {
  display: flex;
  align-items: center;
  margin-bottom: var(--space-2);
}

.board-icon {
  margin-right: var(--space-2);
  font-size: 1.1rem;
  color: var(--primary-600);
}

.board-title {
  margin: 0;
  font-size: 1rem;
  font-weight: 700;
  color: var(--text-primary);
}

.board-description {
  margin: 0 0 var(--space-3) 0;
  font-size: 0.85rem;
  color: var(--text-secondary);
  line-height: 1.5;
}

.board-stats {
  display: flex;
  gap: var(--space-4);
  margin-bottom: var(--space-3);
  font-size: 0.8rem;
  color: var(--text-tertiary);
}

.board-stat {
  display: flex;
  align-items: center;
  gap: var(--space-1);
}

.board-last-post {
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

.last-post-label {
  font-weight: 600;
  margin-right: var(--space-1);
}

.no-boards-message {
  background: var(--bg-secondary);
  padding: var(--space-6);
  border-radius: var(--radius-lg);
  text-align: center;
  color: var(--text-secondary);
}

.latest-topics-card {
  min-height: 200px;
}

.latest-topics-list {
  display: flex;
  flex-direction: column;
}

.latest-topic-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-4) 0;
  border-bottom: 1px solid var(--border-color-light);
  cursor: pointer;
  transition: background-color 0.2s;
}

.latest-topic-item:last-child {
  border-bottom: none;
}

.latest-topic-item:hover {
  background-color: var(--bg-secondary);
  margin: 0 calc(-1 * var(--space-5));
  padding-left: var(--space-5);
  padding-right: var(--space-5);
  border-radius: var(--radius-md);
}

.topic-main {
  flex: 1;
  min-width: 0;
}

.topic-title {
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--space-1);
  font-size: 1rem;
}

.topic-meta {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  font-size: 0.8rem;
  color: var(--text-tertiary);
}

.topic-board {
  color: var(--primary-600);
  font-weight: 500;
}

.latest-topic-item .topic-stats {
  display: flex;
  gap: var(--space-3);
  font-size: 0.85rem;
  color: var(--text-tertiary);
  flex-shrink: 0;
}

.latest-topic-item .topic-stats span {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
}

.forum-sidebar {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.sidebar-card {
  min-height: 150px;
}

.hot-topics-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.hot-topic-item {
  padding: var(--space-2);
  border-radius: var(--radius-md);
  transition: all 0.2s;
}

.hot-topic-item:hover {
  background-color: var(--bg-secondary);
}

.topic-link {
  text-decoration: none;
  color: inherit;
  display: block;
}

.hot-topic-title {
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 4px;
  font-size: 0.9rem;
}

.hot-topic-meta {
  display: flex;
  gap: var(--space-3);
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

.activities-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.activity-item {
  display: flex;
  gap: var(--space-3);
  padding: var(--space-2);
  border-radius: var(--radius-md);
  transition: background-color 0.2s;
}

.activity-item:hover {
  background-color: var(--bg-secondary);
}

.activity-avatar {
  width: 38px;
  height: 38px;
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
  font-size: 0.85rem;
  color: var(--text-primary);
}

.activity-time {
  font-size: 0.7rem;
  color: var(--text-tertiary);
}

.activity-text {
  margin: 0 0 var(--space-2) 0;
  font-size: 0.85rem;
  color: var(--text-secondary);
  line-height: 1.4;
  word-break: break-all;
}

.activity-actions {
  display: flex;
  gap: var(--space-3);
  font-size: 0.8rem;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  background: none;
  border: none;
  color: var(--text-tertiary);
  cursor: pointer;
  padding: 2px 4px;
  border-radius: var(--radius-sm);
  transition: all 0.2s;
}

.action-btn:hover {
  color: var(--error-color);
}

.like-icon {
  font-size: 14px;
}

.like-icon.liked {
  color: var(--error-color);
}

.comment-count {
  display: flex;
  align-items: center;
  gap: 4px;
  color: var(--text-tertiary);
}

.comment-icon {
  font-size: 14px;
}

.load-more-btn {
  width: 100%;
  padding: var(--space-2);
  margin-top: var(--space-3);
  background: var(--bg-tertiary);
  border: none;
  border-radius: var(--radius-md);
  color: var(--primary-600);
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.load-more-btn:hover {
  background: var(--primary-100);
}

.loading-container {
  padding: var(--space-6);
  text-align: center;
  color: var(--text-secondary);
}

.loading-spinner {
  border: 3px solid var(--primary-100);
  border-radius: 50%;
  border-top: 3px solid var(--primary-600);
  width: 32px;
  height: 32px;
  animation: spin 1s linear infinite;
  margin: 0 auto var(--space-3);
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.error-message {
  background-color: var(--error-bg);
  color: var(--error-color);
  padding: var(--space-4);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-4);
  font-size: 0.9rem;
}

.no-data {
  text-align: center;
  padding: var(--space-8);
  color: var(--text-tertiary);
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: var(--space-4);
}

@media (max-width: 1024px) {
  .forum-layout {
    grid-template-columns: 1fr;
  }

  .forum-sidebar {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  }
}

@media (max-width: 768px) {
  .forum-hero {
    flex-direction: column;
    align-items: flex-start;
  }

  .forum-actions {
    width: 100%;
  }

  .action-link {
    flex: 1;
    justify-content: center;
  }

  .forum-stats {
    grid-template-columns: repeat(2, 1fr);
  }

  .search-results {
    left: var(--space-4);
    right: var(--space-4);
  }

  .board-grid {
    grid-template-columns: 1fr;
  }

  .latest-topic-item {
    flex-direction: column;
    align-items: flex-start;
  }

  .latest-topic-item .topic-stats {
    width: 100%;
    justify-content: flex-start;
  }
}
</style>
