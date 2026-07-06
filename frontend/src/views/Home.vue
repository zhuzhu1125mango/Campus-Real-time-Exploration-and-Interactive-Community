<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ChatDotSquare, View, Star, Calendar, Location } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/userStore'
import { feedApi } from '@/api/feed'
import type { FeedItem, FeedType, TrendingTopic } from '@/types/feed'
import { formatDate } from '@/utils/date'
import { stripHtml, sanitizeHtml } from '@/utils/xss'

const router = useRouter()
const userStore = useUserStore()

const DEFAULT_LOCATION = { lat: 39.9042, lng: 116.4074 }

const feedType = ref<FeedType>('recommend')
const items = ref<FeedItem[]>([])
const loading = ref(false)
const hasMore = ref(true)
const page = ref(1)
const pageSize = 10
const userLocation = ref<{ lat: number; lng: number } | null>(null)
const locating = ref(false)
const trendingTopics = ref<TrendingTopic[]>([])
const loadingTrending = ref(false)

const isLoggedIn = computed(() => userStore.isLoggedIn)

const typeOptions: { label: string; value: FeedType }[] = [
  { label: '推荐', value: 'recommend' },
  { label: '关注', value: 'following' },
  { label: '附近', value: 'nearby' }
]

const formatTime = (timeString: string) => {
  return formatDate(timeString)
}

const getTypeLabel = (type: FeedType) => {
  return typeOptions.find(o => o.value === type)?.label || type
}

const getTypeBadge = (objectType: string) => {
  const map: Record<string, { label: string; color: string }> = {
    topic: { label: '话题', color: '#4361ee' },
    content: { label: '文章', color: '#10b981' },
    activity: { label: '动态', color: '#f59e0b' },
    event: { label: '活动', color: '#ef4444' }
  }
  return map[objectType] || { label: '其他', color: '#6b7280' }
}

const fetchFeed = async (reset = false) => {
  if (loading.value) return
  if (reset) {
    page.value = 1
    items.value = []
    hasMore.value = true
  }
  if (!hasMore.value && !reset) return

  loading.value = true
  try {
    const params: Record<string, any> = {
      type: feedType.value,
      page: page.value,
      page_size: pageSize
    }
    if (feedType.value === 'nearby') {
      const loc = userLocation.value || DEFAULT_LOCATION
      params.lat = loc.lat
      params.lng = loc.lng
      params.radius = 10
    }
    const response = await feedApi.getFeed(params)
    const results = response.results || []
    items.value = reset ? results : [...items.value, ...results]
    hasMore.value = results.length === pageSize
    page.value++
  } catch (error: any) {
    console.error('加载 Feed 失败:', error)
    ElMessage.error('加载 Feed 失败')
  } finally {
    loading.value = false
  }
}

const onTypeChange = (type: FeedType) => {
  feedType.value = type
  if (type === 'nearby' && !userLocation.value) {
    locateUser(() => fetchFeed(true))
  } else {
    fetchFeed(true)
  }
}

const loadMore = () => {
  if (!loading.value && hasMore.value) {
    fetchFeed()
  }
}

const locateUser = (callback?: () => void) => {
  locating.value = true
  if (!navigator.geolocation) {
    ElMessage.warning('浏览器不支持定位，使用默认位置')
    userLocation.value = DEFAULT_LOCATION
    locating.value = false
    callback?.()
    return
  }
  navigator.geolocation.getCurrentPosition(
    position => {
      userLocation.value = {
        lat: position.coords.latitude,
        lng: position.coords.longitude
      }
      locating.value = false
      callback?.()
    },
    error => {
      console.error('定位失败:', error)
      ElMessage.warning('无法获取当前位置，使用默认位置')
      userLocation.value = DEFAULT_LOCATION
      locating.value = false
      callback?.()
    },
    { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 }
  )
}

const fetchTrendingTopics = async () => {
  loadingTrending.value = true
  try {
    const data = await feedApi.getTrendingTopics()
    trendingTopics.value = data || []
  } catch (error) {
    console.error('加载热门话题失败:', error)
    trendingTopics.value = []
  } finally {
    loadingTrending.value = false
  }
}

const goToItem = (item: FeedItem) => {
  switch (item.object_type) {
    case 'topic':
      router.push(`/forum/topic/${item.object_id}`)
      break
    case 'content':
      router.push(`/content/${item.object_id}`)
      break
    case 'activity':
      if (item.meta.target_url) {
        router.push(item.meta.target_url)
      } else {
        router.push('/activity')
      }
      break
    case 'event':
      router.push('/events')
      break
  }
}

const goToTrending = (topic: TrendingTopic) => {
  if (topic.type === 'forum_tag') {
    router.push(`/forum/tag/${topic.id.replace('forum_tag_', '')}?name=${encodeURIComponent(topic.name)}`)
  } else {
    router.push(`/content?tag=${encodeURIComponent(topic.name)}`)
  }
}

const promptLogin = () => {
  ElMessageBox.confirm('关注功能需要登录，是否前往登录？', '提示', { type: 'info' })
    .then(() => router.push('/login'))
    .catch(() => {})
}

const handleScroll = () => {
  const scrollTop = window.scrollY || document.documentElement.scrollTop
  const windowHeight = window.innerHeight
  const docHeight = document.documentElement.scrollHeight
  if (docHeight - scrollTop - windowHeight < 200) {
    loadMore()
  }
}

onMounted(() => {
  fetchFeed(true)
  fetchTrendingTopics()
  window.addEventListener('scroll', handleScroll)
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})
</script>

<template>
  <div class="home-container">
    <div class="home-header">
      <div class="hero-section">
        <div class="hero-content">
          <h1 class="hero-title">欢迎来到<span class="highlight">校园实时互动社区</span></h1>
          <p class="hero-subtitle">连接校园，分享知识，共同成长</p>
        </div>
        <div class="hero-actions">
          <router-link v-if="isLoggedIn" to="/profile" class="btn btn-primary">进入个人中心</router-link>
          <router-link v-else to="/login" class="btn btn-primary">立即加入</router-link>
          <router-link to="/explore" class="btn btn-secondary">校园探索</router-link>
        </div>
      </div>
    </div>

    <div class="home-layout">
      <main class="feed-main">
        <div class="feed-tabs">
          <button
            v-for="opt in typeOptions"
            :key="opt.value"
            class="tab-btn"
            :class="{ active: feedType === opt.value }"
            @click="onTypeChange(opt.value)"
          >
            {{ opt.label }}
          </button>
          <button v-if="feedType === 'nearby'" class="locate-btn" @click="locateUser(() => fetchFeed(true))" :disabled="locating">
            {{ locating ? '定位中...' : '重新定位' }}
          </button>
        </div>

        <div v-if="feedType === 'following' && !isLoggedIn" class="login-prompt">
          <p>登录后查看关注好友的动态</p>
          <button class="btn btn-primary" @click="promptLogin">去登录</button>
        </div>

        <div v-else>
          <div v-if="loading && items.length === 0" class="feed-loading">
            <el-skeleton :rows="5" animated />
          </div>

          <div v-else-if="items.length === 0" class="feed-empty">
            <el-empty :description="`暂无${getTypeLabel(feedType)}内容`" />
          </div>

          <div v-else class="feed-list">
            <article
              v-for="item in items"
              :key="item.id"
              class="feed-card"
              @click="goToItem(item)"
            >
              <div class="feed-card-header">
                <img
                  class="author-avatar"
                  :src="item.author.avatar || 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=user%20avatar%20placeholder&image_size=square'"
                  :alt="item.author.username"
                />
                <div class="author-info">
                  <span class="author-name">{{ item.author.username }}</span>
                  <span class="feed-time">{{ formatTime(item.created_at) }}</span>
                </div>
                <span class="type-badge" :style="{ backgroundColor: getTypeBadge(item.object_type).color + '20', color: getTypeBadge(item.object_type).color }">
                  {{ getTypeBadge(item.object_type).label }}
                </span>
              </div>

              <div class="feed-card-body">
                <h3 class="feed-title">{{ item.title }}</h3>
                <div class="feed-summary" v-html="sanitizeHtml(stripHtml(item.content).slice(0, 200))"></div>
                <div v-if="item.images && item.images.length > 0" class="feed-images">
                  <img v-for="(img, index) in item.images.slice(0, 3)" :key="index" :src="img" alt="" />
                </div>
              </div>

              <div class="feed-card-footer">
                <template v-if="item.object_type === 'topic'">
                  <span v-if="item.meta.board_name" class="meta-item">{{ item.meta.board_name }}</span>
                  <span class="meta-item"><el-icon><ChatDotSquare /></el-icon> {{ item.meta.reply_count || 0 }}</span>
                  <span class="meta-item"><el-icon><View /></el-icon> {{ item.meta.view_count || 0 }}</span>
                </template>
                <template v-else-if="item.object_type === 'content'">
                  <span v-if="item.meta.content_type" class="meta-item">{{ item.meta.content_type }}</span>
                  <span class="meta-item"><el-icon><View /></el-icon> {{ item.meta.view_count || 0 }}</span>
                  <span class="meta-item"><el-icon><ChatDotSquare /></el-icon> {{ item.meta.comment_count || 0 }}</span>
                  <span class="meta-item"><el-icon><Star /></el-icon> {{ item.meta.like_count || 0 }}</span>
                </template>
                <template v-else-if="item.object_type === 'activity'">
                  <span class="meta-item"><el-icon><Star /></el-icon> {{ item.meta.likes_count || 0 }}</span>
                  <span class="meta-item"><el-icon><ChatDotSquare /></el-icon> {{ item.meta.comments_count || 0 }}</span>
                </template>
                <template v-else-if="item.object_type === 'event'">
                  <span v-if="item.meta.location" class="meta-item"><el-icon><Location /></el-icon> {{ item.meta.location }}</span>
                  <span v-if="item.meta.start_time" class="meta-item"><el-icon><Calendar /></el-icon> {{ formatTime(item.meta.start_time) }}</span>
                </template>
              </div>
            </article>
          </div>

          <div v-if="items.length > 0" class="feed-loadmore">
            <button v-if="loading" class="load-btn" disabled>加载中...</button>
            <button v-else-if="hasMore" class="load-btn" @click="loadMore">加载更多</button>
            <span v-else class="no-more">没有更多了</span>
          </div>
        </div>
      </main>

      <aside class="home-sidebar">
        <div class="sidebar-card">
          <h3>热门话题</h3>
          <div v-if="loadingTrending" class="sidebar-loading">
            <el-skeleton :rows="4" animated />
          </div>
          <div v-else-if="trendingTopics.length === 0" class="sidebar-empty">
            暂无热门话题
          </div>
          <ul v-else class="topic-list">
            <li v-for="topic in trendingTopics" :key="topic.id" @click="goToTrending(topic)">
              <span class="topic-name"># {{ topic.name }}</span>
              <span class="topic-count">{{ topic.count }}</span>
            </li>
          </ul>
        </div>

        <div class="sidebar-card">
          <h3>快速入口</h3>
          <div class="quick-links">
            <router-link to="/forum">校园论坛</router-link>
            <router-link to="/learning">在线学习</router-link>
            <router-link to="/content">内容中心</router-link>
            <router-link to="/events">校园活动</router-link>
            <router-link to="/schools">院校查询</router-link>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.home-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--space-6);
}

.home-header {
  margin-bottom: var(--space-6);
}

.hero-section {
  background: linear-gradient(135deg, var(--primary-500), var(--primary-700));
  border-radius: var(--radius-xl);
  padding: var(--space-8);
  color: var(--text-inverse);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-6);
  flex-wrap: wrap;
}

.hero-title {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: var(--space-2);
}

.highlight {
  color: #fde047;
}

.hero-subtitle {
  font-size: 1.1rem;
  opacity: 0.9;
}

.hero-actions {
  display: flex;
  gap: var(--space-3);
}

.btn {
  padding: var(--space-3) var(--space-5);
  border-radius: var(--radius-md);
  font-weight: 600;
  text-decoration: none;
  transition: all 0.2s;
}

.btn-primary {
  background: var(--text-inverse);
  color: var(--primary-600);
}

.btn-primary:hover {
  background: #f3f4f6;
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.2);
  color: var(--text-inverse);
  border: 1px solid rgba(255, 255, 255, 0.4);
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.3);
}

.home-layout {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: var(--space-6);
}

.feed-main {
  min-width: 0;
}

.feed-tabs {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-4);
  flex-wrap: wrap;
}

.tab-btn {
  padding: var(--space-2) var(--space-5);
  border-radius: var(--radius-full);
  font-weight: 600;
  color: var(--text-secondary);
  background: var(--bg-primary);
  transition: all 0.2s;
}

.tab-btn.active {
  background: var(--primary-500);
  color: var(--text-inverse);
}

.locate-btn {
  margin-left: auto;
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-md);
  background: var(--bg-primary);
  color: var(--primary-600);
  font-weight: 500;
  border: 1px solid var(--primary-200);
}

.locate-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.login-prompt {
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  padding: var(--space-8);
  text-align: center;
  box-shadow: var(--shadow-sm);
}

.login-prompt p {
  color: var(--text-secondary);
  margin-bottom: var(--space-4);
}

.feed-loading,
.feed-empty {
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  padding: var(--space-8);
  box-shadow: var(--shadow-sm);
}

.feed-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.feed-card {
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  box-shadow: var(--shadow-sm);
  cursor: pointer;
  transition: box-shadow 0.2s, transform 0.2s;
}

.feed-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.feed-card-header {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-3);
}

.author-avatar {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-full);
  object-fit: cover;
}

.author-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.author-name {
  font-weight: 600;
  color: var(--text-primary);
}

.feed-time {
  font-size: 0.8rem;
  color: var(--text-tertiary);
}

.type-badge {
  font-size: 0.75rem;
  padding: 2px 10px;
  border-radius: var(--radius-full);
  font-weight: 500;
}

.feed-card-body {
  margin-bottom: var(--space-3);
}

.feed-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: var(--space-2);
  line-height: 1.4;
}

.feed-summary {
  color: var(--text-secondary);
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.feed-summary :deep(p) {
  margin: 0;
}

.feed-images {
  display: flex;
  gap: var(--space-2);
  margin-top: var(--space-3);
}

.feed-images img {
  width: 120px;
  height: 120px;
  object-fit: cover;
  border-radius: var(--radius-md);
}

.feed-card-footer {
  display: flex;
  gap: var(--space-4);
  padding-top: var(--space-3);
  border-top: 1px solid var(--border-color-light);
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.meta-item {
  display: flex;
  align-items: center;
  gap: var(--space-1);
}

.feed-loadmore {
  text-align: center;
  padding: var(--space-6);
}

.load-btn,
.no-more {
  padding: var(--space-2) var(--space-6);
  border-radius: var(--radius-full);
  font-weight: 500;
  color: var(--text-secondary);
  background: var(--bg-primary);
}

.load-btn:hover:not(:disabled) {
  color: var(--primary-500);
}

.home-sidebar {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.sidebar-card {
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  box-shadow: var(--shadow-sm);
}

.sidebar-card h3 {
  font-size: 1.1rem;
  font-weight: 700;
  margin-bottom: var(--space-4);
  color: var(--text-primary);
}

.sidebar-loading,
.sidebar-empty {
  color: var(--text-tertiary);
  text-align: center;
}

.topic-list {
  list-style: none;
}

.topic-list li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-2) 0;
  cursor: pointer;
  border-bottom: 1px solid var(--border-color-light);
}

.topic-list li:last-child {
  border-bottom: none;
}

.topic-list li:hover .topic-name {
  color: var(--primary-500);
}

.topic-name {
  color: var(--text-primary);
  font-weight: 500;
  transition: color 0.2s;
}

.topic-count {
  font-size: 0.8rem;
  color: var(--text-tertiary);
  background: var(--bg-tertiary);
  padding: 2px 8px;
  border-radius: var(--radius-full);
}

.quick-links {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.quick-links a {
  color: var(--text-secondary);
  padding: var(--space-2) 0;
  transition: color 0.2s;
}

.quick-links a:hover {
  color: var(--primary-500);
}

@media (max-width: 1024px) {
  .home-layout {
    grid-template-columns: 1fr;
  }

  .home-sidebar {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  }
}

@media (max-width: 640px) {
  .home-container {
    padding: var(--space-4);
  }

  .hero-section {
    flex-direction: column;
    align-items: flex-start;
  }

  .hero-title {
    font-size: 1.5rem;
  }

  .feed-tabs {
    justify-content: space-between;
  }

  .locate-btn {
    margin-left: 0;
  }
}
</style>
