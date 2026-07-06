<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, ElSkeleton } from 'element-plus'
import { ChatDotSquare, View, Star, Calendar, Location } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/userStore'
import { feedApi } from '@/api/feed'
import { schoolApi } from '@/api/school'
import { learningApi } from '@/api/learning'
import { userApi } from '@/api/user'
import type { FeedItem, FeedType, TrendingTopic } from '@/types/feed'
import type { Place, Event as SchoolEvent, School } from '@/types/school'
import { formatDate } from '@/utils/date'
import { stripHtml, sanitizeHtml } from '@/utils/xss'
import GlassCard from '@/components/GlassCard.vue'
import QuickAction from '@/components/QuickAction.vue'
import FollowButton from '@/components/FollowButton.vue'

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
const places = ref<Place[]>([])
const loadingPlaces = ref(false)
const events = ref<SchoolEvent[]>([])
const loadingEvents = ref(false)
const schools = ref<School[]>([])
const loadingSchools = ref(false)
const enrollments = ref<any[]>([])
const loadingEnrollments = ref(false)
const notifications = ref<any[]>([])
const loadingNotifications = ref(false)
const searchKeyword = ref('')
const followingMap = ref<Record<number, boolean>>({})

const isLoggedIn = computed(() => userStore.isLoggedIn)

const typeOptions: { label: string; value: FeedType }[] = [
  { label: '推荐', value: 'recommend' },
  { label: '关注', value: 'following' },
  { label: '附近', value: 'nearby' }
]

const quickActions = computed(() => [
  { icon: 'i-ep-chat-line-round', label: '发帖', description: '参与校园讨论', to: '/forum', color: 'primary' as const },
  { icon: 'i-ep-document', label: '写文章', description: '分享知识与经验', to: '/content/create', color: 'green' as const },
  { icon: 'i-ep-calendar', label: '发布活动', description: '发起校园活动', to: '/events', color: 'orange' as const },
  { icon: 'i-ep-map-location', label: '去地图', description: '探索附近地点', to: '/explore', color: 'purple' as const },
])

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

const fetchNearbyPlaces = async () => {
  loadingPlaces.value = true
  try {
    const loc = userLocation.value || DEFAULT_LOCATION
    const data = await schoolApi.getNearbyPlaces({
      lat: loc.lat,
      lng: loc.lng,
      radius: 5
    })
    places.value = (data || []).slice(0, 5)
  } catch (error) {
    console.error('加载附近地点失败:', error)
    places.value = []
  } finally {
    loadingPlaces.value = false
  }
}

const fetchNearbyEvents = async () => {
  loadingEvents.value = true
  try {
    const loc = userLocation.value || DEFAULT_LOCATION
    const data = await schoolApi.getNearbyEvents({
      lat: loc.lat,
      lng: loc.lng,
      radius: 10
    })
    events.value = (data || []).slice(0, 5)
  } catch (error) {
    console.error('加载活动失败:', error)
    events.value = []
  } finally {
    loadingEvents.value = false
  }
}

const fetchRecommendedSchools = async () => {
  loadingSchools.value = true
  try {
    const response = await schoolApi.getRecommendations({ type: 'popular', limit: 5 })
    schools.value = response.recommendations || []
  } catch (error) {
    console.error('加载推荐院校失败:', error)
    schools.value = []
  } finally {
    loadingSchools.value = false
  }
}

const fetchMyLearning = async () => {
  if (!isLoggedIn.value) return
  loadingEnrollments.value = true
  try {
    const response = await learningApi.getEnrollments({ page: 1 })
    enrollments.value = (response.results || []).slice(0, 3)
  } catch (error) {
    console.error('加载学习进度失败:', error)
    enrollments.value = []
  } finally {
    loadingEnrollments.value = false
  }
}

const fetchNotifications = async () => {
  if (!isLoggedIn.value) return
  loadingNotifications.value = true
  try {
    const response = await userApi.getNotifications({ unread: true, page_size: 5 })
    notifications.value = (response.results || response || []).slice(0, 5)
  } catch (error) {
    console.error('加载通知失败:', error)
    notifications.value = []
  } finally {
    loadingNotifications.value = false
  }
}

const handleFollowUpdate = (userId: number, following: boolean) => {
  followingMap.value[userId] = following
}

const isFollowing = (item: FeedItem) => {
  if (followingMap.value[item.author.id] !== undefined) {
    return followingMap.value[item.author.id]
  }
  return false
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

const goToPlace = (_place: Place) => {
  router.push('/explore')
}

const goToSchool = (school: School) => {
  router.push(`/schools/${school.id}`)
}

const goToEvent = (_event: SchoolEvent) => {
  router.push('/events')
}

const goToEnrollment = (enrollment: any) => {
  const courseId = enrollment.course?.id || enrollment.course
  if (courseId) {
    router.push(`/learning/course/${courseId}`)
  } else {
    router.push('/my-learning')
  }
}

const goToNotification = (_notification: any) => {
  router.push('/notifications')
}

const handleSearch = () => {
  const keyword = searchKeyword.value.trim()
  if (!keyword) return
  router.push(`/search?q=${encodeURIComponent(keyword)}`)
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
  locateUser(() => {
    fetchNearbyPlaces()
    fetchNearbyEvents()
  })
  fetchRecommendedSchools()
  fetchMyLearning()
  fetchNotifications()
  window.addEventListener('scroll', handleScroll)
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})
</script>

<template>
  <div class="home-page container-wide page-padding">
    <!-- Hero 区 -->
    <GlassCard class="hero-card" :hover="false" padding="lg">
      <div class="hero-grid">
        <div class="hero-main">
          <h1 class="hero-title">
            欢迎来到
            <span class="hero-highlight">校园实时互动社区</span>
          </h1>
          <p class="hero-subtitle">连接校园每一个角落，发现身边的精彩</p>
          <div class="hero-search">
            <span class="hero-search-icon i-ep-search" />
            <input
              v-model="searchKeyword"
              type="text"
              placeholder="搜索院校、话题、内容..."
              @keyup.enter="handleSearch"
            />
            <button type="button" class="hero-search-btn" @click="handleSearch">
              搜索
            </button>
          </div>
        </div>
        <div class="hero-actions">
          <QuickAction
            v-for="action in quickActions"
            :key="action.label"
            :icon="action.icon"
            :label="action.label"
            :description="action.description"
            :to="action.to"
            :color="action.color"
          />
        </div>
      </div>
    </GlassCard>

    <!-- 主体 12 列网格 -->
    <div class="home-grid">
      <!-- 主列：Feed 流 -->
      <main class="home-main">
        <GlassCard :hover="false" padding="md">
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
            <button
              v-if="feedType === 'nearby'"
              class="locate-btn"
              :disabled="locating"
              @click="locateUser(() => fetchFeed(true))"
            >
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
                  <FollowButton
                    :user-id="item.author.id"
                    :following="isFollowing(item)"
                    size="sm"
                    @update="(following) => handleFollowUpdate(item.author.id, following)"
                  />
                  <span
                    class="type-badge"
                    :style="{ backgroundColor: getTypeBadge(item.object_type).color + '20', color: getTypeBadge(item.object_type).color }"
                  >
                    {{ getTypeBadge(item.object_type).label }}
                  </span>
                </div>

                <div class="feed-card-body">
                  <h3 class="feed-title">{{ item.title }}</h3>
                  <div class="feed-summary" v-html="sanitizeHtml(stripHtml(item.content).slice(0, 200))" />
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
        </GlassCard>
      </main>

      <!-- 右侧栏 -->
      <aside class="home-sidebar">
        <!-- 地图探索 -->
        <GlassCard title="附近地点" subtitle="发现身边的校园地标" :action="{ label: '去探索', to: '/explore' }">
          <div v-if="loadingPlaces" class="widget-loading">
            <el-skeleton :rows="3" animated />
          </div>
          <div v-else-if="places.length === 0" class="widget-empty">暂无附近地点</div>
          <ul v-else class="widget-list">
            <li v-for="place in places" :key="place.id" class="widget-item" @click="goToPlace(place)">
              <span class="widget-dot" :style="{ background: place.icon || 'var(--primary-500)' }" />
              <div class="widget-item-main">
                <span class="widget-item-title">{{ place.name }}</span>
                <span class="widget-item-meta">{{ place.category_display }}{{ place.distance !== undefined ? ` · ${place.distance}km` : '' }}</span>
              </div>
            </li>
          </ul>
        </GlassCard>

        <!-- 热门话题 -->
        <GlassCard title="热门话题" subtitle="大家都在讨论什么" :action="{ label: '全部', to: '/forum' }">
          <div v-if="loadingTrending" class="widget-loading">
            <el-skeleton :rows="4" animated />
          </div>
          <div v-else-if="trendingTopics.length === 0" class="widget-empty">暂无热门话题</div>
          <ul v-else class="topic-list">
            <li v-for="(topic, index) in trendingTopics" :key="topic.id" @click="goToTrending(topic)">
              <span class="topic-rank" :class="{ hot: index < 3 }">{{ index + 1 }}</span>
              <span class="topic-name"># {{ topic.name }}</span>
              <span class="topic-count">{{ topic.count }}</span>
            </li>
          </ul>
        </GlassCard>

        <!-- 推荐院校 -->
        <GlassCard title="推荐院校" subtitle="值得关注的高校" :action="{ label: '更多', to: '/schools' }">
          <div v-if="loadingSchools" class="widget-loading">
            <el-skeleton :rows="3" animated />
          </div>
          <div v-else-if="schools.length === 0" class="widget-empty">暂无推荐院校</div>
          <ul v-else class="widget-list">
            <li v-for="school in schools" :key="school.id" class="widget-item" @click="goToSchool(school)">
              <img
                v-if="school.logo"
                class="widget-thumb"
                :src="school.logo"
                :alt="school.name"
              />
              <span v-else class="widget-thumb fallback">{{ school.name.charAt(0) }}</span>
              <div class="widget-item-main">
                <span class="widget-item-title">{{ school.name }}</span>
                <span class="widget-item-meta">{{ school.province }}{{ school.school_type ? ` · ${school.school_type}` : '' }}</span>
              </div>
            </li>
          </ul>
        </GlassCard>

        <!-- 我的学习 -->
        <GlassCard v-if="isLoggedIn" title="我的学习" subtitle="继续你的课程" :action="{ label: '全部', to: '/my-learning' }">
          <div v-if="loadingEnrollments" class="widget-loading">
            <el-skeleton :rows="2" animated />
          </div>
          <div v-else-if="enrollments.length === 0" class="widget-empty">
            还没有报名课程，<router-link to="/learning">去发现</router-link>
          </div>
          <ul v-else class="widget-list">
            <li v-for="enrollment in enrollments" :key="enrollment.id" class="widget-item" @click="goToEnrollment(enrollment)">
              <span class="widget-thumb fallback">
                {{ (enrollment.course?.title || enrollment.course || '课').charAt(0) }}
              </span>
              <div class="widget-item-main">
                <span class="widget-item-title">{{ enrollment.course?.title || '课程' }}</span>
                <span class="widget-item-meta">进度 {{ enrollment.progress || enrollment.progress_rate || 0 }}%</span>
              </div>
            </li>
          </ul>
        </GlassCard>

        <!-- 通知 -->
        <GlassCard v-if="isLoggedIn" title="未读通知" subtitle="你的最新消息" :action="{ label: '查看', to: '/notifications' }">
          <div v-if="loadingNotifications" class="widget-loading">
            <el-skeleton :rows="2" animated />
          </div>
          <div v-else-if="notifications.length === 0" class="widget-empty">暂无未读通知</div>
          <ul v-else class="widget-list">
            <li
              v-for="notification in notifications"
              :key="notification.id"
              class="widget-item"
              @click="goToNotification(notification)"
            >
              <span class="widget-dot unread" />
              <div class="widget-item-main">
                <span class="widget-item-title">{{ notification.title || '新通知' }}</span>
                <span class="widget-item-meta">{{ formatTime(notification.created_at) }}</span>
              </div>
            </li>
          </ul>
        </GlassCard>

        <!-- 即将开始活动 -->
        <GlassCard title="即将开始" subtitle="不要错过校园活动" :action="{ label: '全部', to: '/events' }">
          <div v-if="loadingEvents" class="widget-loading">
            <el-skeleton :rows="3" animated />
          </div>
          <div v-else-if="events.length === 0" class="widget-empty">暂无即将开始的活动</div>
          <ul v-else class="widget-list">
            <li v-for="event in events" :key="event.id" class="widget-item" @click="goToEvent(event)">
              <span class="widget-dot event" />
              <div class="widget-item-main">
                <span class="widget-item-title">{{ event.title }}</span>
                <span class="widget-item-meta">
                  <template v-if="event.start_time">{{ formatTime(event.start_time) }}</template>
                  <template v-if="event.location"> · {{ event.location }}</template>
                </span>
              </div>
            </li>
          </ul>
        </GlassCard>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.home-page {
  display: flex;
  flex-direction: column;
  gap: var(--space-8);
}

.hero-card {
  overflow: hidden;
}

.hero-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-8);
  align-items: center;
}

.hero-main {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.hero-title {
  font-size: 2rem;
  font-weight: 800;
  color: var(--text-primary);
  line-height: 1.25;
}

.hero-highlight {
  color: var(--primary-600);
}

.dark .hero-highlight {
  color: var(--primary-400);
}

.hero-subtitle {
  font-size: 1.1rem;
  color: var(--text-secondary);
}

.hero-search {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2);
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-full);
  box-shadow: var(--shadow-sm);
  max-width: 480px;
}

.hero-search-icon {
  width: 20px;
  height: 20px;
  margin-left: var(--space-3);
  color: var(--text-tertiary);
}

.hero-search input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  color: var(--text-primary);
  font-size: 1rem;
  min-width: 0;
}

.hero-search input::placeholder {
  color: var(--text-tertiary);
}

.hero-search-btn {
  padding: var(--space-2) var(--space-5);
  background: var(--primary-600);
  color: var(--text-inverse);
  font-weight: 600;
  border-radius: var(--radius-full);
  transition: background 0.2s;
}

.hero-search-btn:hover {
  background: var(--primary-700);
}

.hero-actions {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-4);
}

.home-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 360px;
  gap: var(--space-6);
  align-items: start;
}

.home-main {
  min-width: 0;
}

.home-sidebar {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
  min-width: 0;
}

.feed-tabs {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-5);
  flex-wrap: wrap;
}

.tab-btn {
  padding: var(--space-2) var(--space-5);
  border-radius: var(--radius-full);
  font-weight: 600;
  color: var(--text-secondary);
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  transition: all 0.2s;
}

.tab-btn.active {
  background: var(--primary-500);
  color: var(--text-inverse);
  border-color: var(--primary-500);
}

.tab-btn:hover:not(.active) {
  color: var(--primary-600);
  border-color: var(--primary-300);
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
}

.login-prompt p {
  color: var(--text-secondary);
  margin-bottom: var(--space-4);
}

.btn {
  padding: var(--space-3) var(--space-5);
  border-radius: var(--radius-md);
  font-weight: 600;
  text-decoration: none;
  transition: all 0.2s;
  display: inline-block;
}

.btn-primary {
  background: var(--primary-600);
  color: var(--text-inverse);
}

.btn-primary:hover {
  background: var(--primary-700);
}

.feed-loading,
.feed-empty {
  padding: var(--space-8) 0;
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
  padding: var(--space-6) 0 0;
}

.load-btn,
.no-more {
  padding: var(--space-2) var(--space-6);
  border-radius: var(--radius-full);
  font-size: 0.9rem;
  color: var(--text-secondary);
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
}

.load-btn:hover:not(:disabled) {
  color: var(--primary-600);
  border-color: var(--primary-300);
}

.widget-loading {
  padding: var(--space-2) 0;
}

.widget-empty {
  padding: var(--space-4) 0;
  text-align: center;
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.widget-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.widget-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background 0.2s;
}

.widget-item:hover {
  background: var(--bg-tertiary);
}

.widget-dot {
  width: 10px;
  height: 10px;
  border-radius: var(--radius-full);
  flex-shrink: 0;
  background: var(--primary-500);
}

.widget-dot.unread {
  background: var(--error-color);
}

.widget-dot.event {
  background: var(--accent-orange);
}

.widget-thumb {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-md);
  object-fit: cover;
  flex-shrink: 0;
  background: var(--bg-tertiary);
}

.widget-thumb.fallback {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.875rem;
  font-weight: 700;
  color: var(--primary-600);
  background: var(--primary-50);
}

.widget-item-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.widget-item-title {
  font-size: 0.95rem;
  font-weight: 500;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.widget-item-meta {
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.topic-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.topic-list li {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background 0.2s;
}

.topic-list li:hover {
  background: var(--bg-tertiary);
}

.topic-rank {
  width: 22px;
  height: 22px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--text-secondary);
  background: var(--bg-tertiary);
  flex-shrink: 0;
}

.topic-rank.hot {
  color: var(--text-inverse);
  background: var(--error-color);
}

.topic-name {
  flex: 1;
  min-width: 0;
  font-size: 0.95rem;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.topic-count {
  font-size: 0.8rem;
  color: var(--text-tertiary);
  flex-shrink: 0;
}

@media (max-width: 1024px) {
  .hero-grid {
    grid-template-columns: 1fr;
  }

  .hero-actions {
    grid-template-columns: repeat(4, 1fr);
  }

  .home-grid {
    grid-template-columns: 1fr;
  }

  .home-sidebar {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: var(--space-5);
  }
}

@media (max-width: 768px) {
  .hero-actions {
    grid-template-columns: repeat(2, 1fr);
  }

  .hero-title {
    font-size: 1.5rem;
  }

  .home-sidebar {
    grid-template-columns: 1fr;
  }

  .feed-images img {
    width: 90px;
    height: 90px;
  }
}
</style>
