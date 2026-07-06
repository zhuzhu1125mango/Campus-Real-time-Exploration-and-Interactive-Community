<template>
  <view class="container">
    <!-- 搜索栏 -->
    <view class="search-header">
      <view class="search-box">
        <view class="search-input-wrapper">
          <text class="search-icon">🔍</text>
          <input
            type="text"
            v-model="query"
            placeholder="搜索课程、内容、学校、论坛..."
            class="search-input"
            confirm-type="search"
            maxlength="100"
            @confirm="doSearch"
            @input="handleInput"
            @focus="handleFocus"
          />
          <view v-if="query" class="clear-btn" @click="query = ''; results = {}; hasSearched = false">
            <text class="clear-icon">✕</text>
          </view>
        </view>
        <button class="search-btn" :disabled="loading" @click="doSearch">{{ loading ? '搜索中' : '搜索' }}</button>
      </view>
      <view v-if="suggestions.length > 0 && showSuggestions" class="suggestions">
        <view
          v-for="item in suggestions"
          :key="`${item.type}-${item.id}`"
          class="suggestion-item"
          @click="selectSuggestion(item)"
        >
          <text class="suggestion-type">{{ typeLabels[item.type] }}</text>
          <rich-text class="suggestion-title" :nodes="highlightNodes(item.title, query)"></rich-text>
        </view>
      </view>
    </view>

    <!-- 类型 Tab -->
    <view class="search-tabs">
      <view
        v-for="t in searchTypes"
        :key="t.key"
        class="tab-item"
        :class="{ active: activeType === t.key }"
        @click="changeType(t.key)"
      >
        {{ t.label }}
      </view>
    </view>

    <!-- 搜索结果 -->
    <view class="search-body">
      <view v-if="loading" class="skeleton-wrapper">
        <view v-for="i in 2" :key="i" class="skeleton-section">
          <view class="skeleton-title"></view>
          <view v-for="j in 3" :key="j" class="skeleton-card">
            <view class="skeleton-line short"></view>
            <view class="skeleton-line"></view>
          </view>
        </view>
      </view>

      <template v-else-if="hasSearched">
        <view v-if="totalCount === 0" class="empty-state">
          <view class="empty-icon">🔍</view>
          <text class="empty-title">未找到与 "{{ query }}" 相关的结果</text>
          <text class="empty-desc">换个关键词试试看</text>
        </view>

        <scroll-view v-else scroll-y class="result-scroll">
          <!-- 课程 -->
          <view v-if="results.courses?.length > 0" class="result-section">
            <view class="section-title">课程</view>
            <view
              v-for="course in results.courses"
              :key="`course-${course.id}`"
              class="result-card"
              @click="goDetail('course', course)"
            >
              <rich-text class="result-title" :nodes="highlightNodes(course.title, query)"></rich-text>
              <rich-text class="result-desc" :nodes="highlightNodes(course.description, query)"></rich-text>
              <view class="result-meta">
                <text>{{ course.instructor?.username }}</text>
                <text>{{ course.enroll_count }} 人报名</text>
              </view>
            </view>
          </view>

          <!-- 内容 -->
          <view v-if="results.contents?.length > 0" class="result-section">
            <view class="section-title">内容</view>
            <view
              v-for="item in results.contents"
              :key="`content-${item.id}`"
              class="result-card"
              @click="goDetail('content', item)"
            >
              <rich-text class="result-title" :nodes="highlightNodes(item.title, query)"></rich-text>
              <rich-text class="result-desc" :nodes="highlightNodes(stripHtml(item.summary || item.content).substring(0, 80), query) + '...'"></rich-text>
              <view class="result-meta">
                <text>{{ item.author?.username }}</text>
                <text>{{ formatDate(item.created_at) }}</text>
              </view>
            </view>
          </view>

          <!-- 学校 -->
          <view v-if="results.schools?.length > 0" class="result-section">
            <view class="section-title">学校</view>
            <view
              v-for="school in results.schools"
              :key="`school-${school.id}`"
              class="result-card"
              @click="goDetail('school', school)"
            >
              <rich-text class="result-title" :nodes="highlightNodes(school.name, query)"></rich-text>
              <rich-text class="result-desc" :nodes="highlightNodes(`${school.province} ${school.city}`, query)"></rich-text>
              <view class="result-meta">
                <text>{{ school.school_level }}</text>
                <text v-if="school.national_rank">全国排名 {{ school.national_rank }}</text>
              </view>
            </view>
          </view>

          <!-- 论坛主题 -->
          <view v-if="results.topics?.length > 0" class="result-section">
            <view class="section-title">论坛主题</view>
            <view
              v-for="topic in results.topics"
              :key="`topic-${topic.id}`"
              class="result-card"
              @click="goDetail('topic', topic)"
            >
              <rich-text class="result-title" :nodes="highlightNodes(topic.title, query)"></rich-text>
              <view class="result-meta">
                <text>{{ topic.author?.username }}</text>
                <text>{{ topic.views }} 浏览</text>
              </view>
            </view>
          </view>

          <!-- 帖子 -->
          <view v-if="results.posts?.length > 0" class="result-section">
            <view class="section-title">帖子</view>
            <view
              v-for="post in results.posts"
              :key="`post-${post.id}`"
              class="result-card"
              @click="goDetail('post', post)"
            >
              <rich-text class="result-desc" :nodes="highlightNodes(stripHtml(post.content).substring(0, 100), query) + '...'"></rich-text>
              <view class="result-meta">
                <text>{{ post.author?.username }}</text>
                <text>{{ formatDate(post.created_at) }}</text>
              </view>
            </view>
          </view>
        </scroll-view>
      </template>

      <view v-else class="search-placeholder">
        <view v-if="searchHistory.length > 0" class="history-section">
          <view class="section-header">
            <text class="section-title">搜索历史</text>
            <text class="clear-link" @click="clearHistory">清空</text>
          </view>
          <view class="tag-list">
            <text
              v-for="item in searchHistory"
              :key="item"
              class="history-tag"
              @click="useHistory(item)"
            >
              {{ item }}
              <text class="remove-btn" @click.stop="removeHistory(item)">✕</text>
            </text>
          </view>
        </view>

        <view class="hot-section">
          <view class="section-header">
            <text class="section-title">热门搜索</text>
          </view>
          <view class="tag-list">
            <text
              v-for="item in hotSearches"
              :key="item"
              class="hot-tag"
              @click="useHistory(item)"
            >
              {{ item }}
            </text>
          </view>
        </view>

        <view class="empty-state soft">
          <view class="empty-icon">🔍</view>
          <text class="empty-title">输入关键词开始搜索</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { onUnload } from '@dcloudio/uni-app'
import searchApi from '../../api/search'

onUnload(() => {
  if (suggestionTimer.value) {
    clearTimeout(suggestionTimer.value)
    suggestionTimer.value = null
  }
})

const props = defineProps({
  type: {
    type: String,
    default: 'all'
  },
  keyword: {
    type: String,
    default: ''
  }
})

const query = ref('')
const activeType = ref('all')
const loading = ref(false)
const hasSearched = ref(false)
const results = ref({})
const suggestions = ref([])
const showSuggestions = ref(false)
const suggestionTimer = ref(null)
const searchHistory = ref([])

const HISTORY_KEY = 'campus_search_history'
const MAX_HISTORY = 10

const searchTypes = [
  { key: 'all', label: '全部' },
  { key: 'course', label: '课程' },
  { key: 'content', label: '内容' },
  { key: 'school', label: '学校' },
  { key: 'topic', label: '主题' },
  { key: 'post', label: '帖子' }
]

const typeLabels = {
  course: '课程',
  content: '内容',
  school: '学校',
  topic: '主题',
  post: '帖子'
}

const hotSearches = ['计算机', '清华大学', '考研', 'Python', '校园活动']

const totalCount = computed(() => {
  let count = 0
  const keys = ['courses', 'contents', 'schools', 'topics', 'posts']
  keys.forEach((key) => {
    const list = results.value[key]
    if (Array.isArray(list)) count += list.length
  })
  return count
})

const loadHistory = () => {
  try {
    const raw = uni.getStorageSync(HISTORY_KEY)
    if (raw) {
      const parsed = JSON.parse(raw)
      if (Array.isArray(parsed)) {
        searchHistory.value = parsed.slice(0, MAX_HISTORY)
      }
    }
  } catch {
    searchHistory.value = []
  }
}

const saveHistory = () => {
  try {
    uni.setStorageSync(HISTORY_KEY, JSON.stringify(searchHistory.value))
  } catch {
    // ignore
  }
}

const addHistory = (keyword) => {
  if (!keyword) return
  const list = searchHistory.value.filter(item => item !== keyword)
  list.unshift(keyword)
  searchHistory.value = list.slice(0, MAX_HISTORY)
  saveHistory()
}

const removeHistory = (keyword) => {
  searchHistory.value = searchHistory.value.filter(item => item !== keyword)
  saveHistory()
}

const clearHistory = () => {
  searchHistory.value = []
  saveHistory()
}

const useHistory = (keyword) => {
  query.value = keyword
  showSuggestions.value = false
  doSearch()
}

onMounted(() => {
  loadHistory()
  const pages = getCurrentPages()
  const page = pages[pages.length - 1]
  const options = page?.options || page?.$route?.query || {}
  activeType.value = options.type || props.type || 'all'
  query.value = options.keyword || props.keyword || ''
  if (query.value) {
    doSearch()
  }
})

const doSearch = async () => {
  const q = query.value.trim()
  if (!q) {
    results.value = {}
    hasSearched.value = false
    showSuggestions.value = false
    return
  }
  loading.value = true
  hasSearched.value = true
  showSuggestions.value = false
  try {
    const res = await searchApi.search(q, activeType.value, 20)
    results.value = res.results || {}
    addHistory(q)
  } catch (err) {
    console.error('搜索失败', err)
    uni.showToast({ title: '搜索失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

const loadSuggestions = async () => {
  const q = query.value.trim()
  if (!q) {
    suggestions.value = []
    showSuggestions.value = false
    return
  }
  try {
    const res = await searchApi.getSuggestions(q)
    suggestions.value = res.suggestions || []
    showSuggestions.value = suggestions.value.length > 0
  } catch (err) {
    console.error('获取搜索建议失败', err)
  }
}

const handleInput = () => {
  if (suggestionTimer.value) clearTimeout(suggestionTimer.value)
  suggestionTimer.value = setTimeout(() => {
    loadSuggestions()
  }, 300)
}

const handleFocus = () => {
  if (query.value.trim() && suggestions.value.length > 0) {
    showSuggestions.value = true
  }
}

const selectSuggestion = (item) => {
  query.value = item.title
  showSuggestions.value = false
  doSearch()
}

const changeType = (type) => {
  activeType.value = type
  if (query.value.trim()) {
    doSearch()
  }
}

const goDetail = (type, item) => {
  let url = ''
  if (type === 'course') url = `/pages/course-detail/course-detail?id=${item.id}`
  else if (type === 'content') url = `/pages/content-detail/content-detail?id=${item.id}`
  else if (type === 'school') url = `/pages/school-detail/school-detail?id=${item.id}`
  else if (type === 'topic') url = `/pages/post-detail/post-detail?id=${item.id}`
  else if (type === 'post') url = `/pages/post-detail/post-detail?id=${item.topic}`
  if (url) {
    uni.navigateTo({ url })
  }
}

const stripHtml = (html) => {
  if (!html) return ''
  return html.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim()
}

const formatDate = (date) => {
  if (!date) return ''
  const d = new Date(date)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

const escapeHtml = (text) => {
  if (!text) return ''
  return text.replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

const highlightNodes = (text, keyword) => {
  if (!keyword || !text) return escapeHtml(String(text))
  const safeKeyword = keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const regex = new RegExp(`(${safeKeyword})`, 'gi')
  const html = escapeHtml(String(text)).replace(regex, '<span style="color:#4361ee;font-weight:600;">$1</span>')
  return html
}
</script>

<style scoped>
.container {
  min-height: 100vh;
  background-color: #f5f5f5;
  display: flex;
  flex-direction: column;
}

.search-header {
  background-color: #fff;
  padding: 20rpx 30rpx;
  position: relative;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.search-input-wrapper {
  flex: 1;
  display: flex;
  align-items: center;
  background-color: #f5f5f5;
  border-radius: 36rpx;
  padding: 0 20rpx;
}

.search-icon {
  font-size: 26rpx;
  color: #999;
  margin-right: 12rpx;
}

.search-input {
  flex: 1;
  height: 72rpx;
  font-size: 28rpx;
  background: transparent;
}

.clear-btn {
  width: 40rpx;
  height: 40rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.clear-icon {
  font-size: 24rpx;
  color: #999;
}

.search-btn {
  background-color: #4361ee;
  color: #fff;
  font-size: 26rpx;
  padding: 0 30rpx;
  height: 64rpx;
  line-height: 64rpx;
  border-radius: 32rpx;
  border: none;
}

.search-btn[disabled] {
  opacity: 0.7;
}

.suggestions {
  position: absolute;
  top: 100%;
  left: 30rpx;
  right: 30rpx;
  background-color: #fff;
  border-radius: 12rpx;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.1);
  z-index: 100;
  padding: 10rpx 0;
}

.suggestion-item {
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 20rpx 24rpx;
}

.suggestion-type {
  font-size: 20rpx;
  color: #4361ee;
  background-color: rgba(67, 97, 238, 0.1);
  padding: 4rpx 12rpx;
  border-radius: 6rpx;
}

.suggestion-title {
  flex: 1;
  font-size: 28rpx;
  color: #333;
}

.search-tabs {
  display: flex;
  gap: 16rpx;
  padding: 20rpx 30rpx;
  background-color: #fff;
  border-bottom: 1rpx solid #f0f0f0;
  overflow-x: auto;
}

.tab-item {
  flex-shrink: 0;
  padding: 10rpx 24rpx;
  border-radius: 30rpx;
  font-size: 26rpx;
  color: #666;
  background-color: #f5f5f5;
}

.tab-item.active {
  color: #fff;
  background-color: #4361ee;
}

.search-body {
  flex: 1;
  padding: 20rpx 30rpx;
  overflow: hidden;
}

.skeleton-wrapper {
  display: flex;
  flex-direction: column;
  gap: 40rpx;
}

.skeleton-section {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.skeleton-title {
  width: 120rpx;
  height: 40rpx;
  background: linear-gradient(90deg, #eee 25%, #f5f5f5 50%, #eee 75%);
  background-size: 200% 100%;
  border-radius: 8rpx;
  animation: shimmer 1.5s infinite;
}

.skeleton-card {
  background: #fff;
  border-radius: 12rpx;
  padding: 24rpx;
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.skeleton-line {
  height: 28rpx;
  background: linear-gradient(90deg, #eee 25%, #f5f5f5 50%, #eee 75%);
  background-size: 200% 100%;
  border-radius: 8rpx;
  animation: shimmer 1.5s infinite;
}

.skeleton-line.short {
  width: 50%;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 120rpx 40rpx;
  text-align: center;
}

.empty-state.soft {
  padding: 80rpx 40rpx;
}

.empty-icon {
  width: 120rpx;
  height: 120rpx;
  border-radius: 50%;
  background: rgba(67, 97, 238, 0.08);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 56rpx;
  margin-bottom: 24rpx;
}

.empty-title {
  font-size: 30rpx;
  color: #333;
  margin-bottom: 12rpx;
}

.empty-desc {
  font-size: 26rpx;
  color: #999;
}

.result-scroll {
  height: 100%;
}

.result-section {
  margin-bottom: 30rpx;
}

.section-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 20rpx;
  padding-bottom: 16rpx;
  border-bottom: 1rpx solid #eee;
}

.result-card {
  background-color: #fff;
  border-radius: 12rpx;
  padding: 24rpx;
  margin-bottom: 16rpx;
  border: 1rpx solid transparent;
  transition: all 0.2s;
}

.result-card:active {
  transform: scale(0.98);
  border-color: rgba(67, 97, 238, 0.2);
}

.result-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 12rpx;
}

.result-desc {
  font-size: 26rpx;
  color: #666;
  line-height: 1.5;
  margin-bottom: 16rpx;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.result-meta {
  display: flex;
  gap: 16rpx;
  font-size: 22rpx;
  color: #999;
}

.search-placeholder {
  display: flex;
  flex-direction: column;
  gap: 30rpx;
}

.history-section,
.hot-section {
  background: #fff;
  border-radius: 12rpx;
  padding: 24rpx;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20rpx;
}

.section-title {
  font-size: 28rpx;
  font-weight: 600;
  color: #333;
}

.clear-link {
  font-size: 24rpx;
  color: #999;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
}

.history-tag,
.hot-tag {
  display: inline-flex;
  align-items: center;
  gap: 8rpx;
  padding: 10rpx 20rpx;
  border-radius: 30rpx;
  font-size: 26rpx;
  color: #666;
  background: #f5f5f5;
}

.hot-tag {
  color: #4361ee;
  background: rgba(67, 97, 238, 0.08);
}

.remove-btn {
  font-size: 20rpx;
  color: #999;
  padding: 4rpx;
}
</style>
