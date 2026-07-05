<template>
  <view class="container">
    <!-- 搜索栏 -->
    <view class="search-header">
      <view class="search-box">
        <input
          type="text"
          v-model="query"
          placeholder="搜索课程、内容、学校、论坛..."
          class="search-input"
          confirm-type="search"
          @confirm="doSearch"
          @input="handleInput"
          @focus="handleFocus"
        />
        <button class="search-btn" @click="doSearch">搜索</button>
      </view>
      <view v-if="suggestions.length > 0 && showSuggestions" class="suggestions">
        <view
          v-for="item in suggestions"
          :key="`${item.type}-${item.id}`"
          class="suggestion-item"
          @click="selectSuggestion(item)"
        >
          <text class="suggestion-type">{{ typeLabels[item.type] }}</text>
          <text class="suggestion-title">{{ item.title }}</text>
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
      <view v-if="loading" class="loading-state">
        <text>搜索中...</text>
      </view>

      <template v-else-if="hasSearched">
        <view v-if="totalCount === 0" class="empty-state">
          <text>未找到与 "{{ query }}" 相关的结果</text>
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
              <view class="result-title">{{ course.title }}</view>
              <view class="result-desc">{{ course.description }}</view>
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
              <view class="result-title">{{ item.title }}</view>
              <view class="result-desc">{{ stripHtml(item.summary || item.content).substring(0, 80) }}...</view>
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
              <view class="result-title">{{ school.name }}</view>
              <view class="result-desc">{{ school.province }} {{ school.city }}</view>
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
              <view class="result-title">{{ topic.title }}</view>
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
              <view class="result-desc">{{ stripHtml(post.content).substring(0, 100) }}...</view>
              <view class="result-meta">
                <text>{{ post.author?.username }}</text>
                <text>{{ formatDate(post.created_at) }}</text>
              </view>
            </view>
          </view>
        </scroll-view>
      </template>

      <view v-else class="empty-state">
        <text>输入关键词开始搜索</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import searchApi from '../../api/search'

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

const totalCount = computed(() => {
  let count = 0
  const keys = ['courses', 'contents', 'schools', 'topics', 'posts']
  keys.forEach((key) => {
    const list = results.value[key]
    if (Array.isArray(list)) count += list.length
  })
  return count
})

onMounted(() => {
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
</script>

<style scoped>
.container {
  min-height: 100vh;
  background-color: #f5f5f5;
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

.search-input {
  flex: 1;
  height: 72rpx;
  padding: 0 24rpx;
  background-color: #f5f5f5;
  border-radius: 36rpx;
  font-size: 28rpx;
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
  padding: 20rpx 30rpx;
}

.loading-state,
.empty-state {
  text-align: center;
  padding: 120rpx 40rpx;
  color: #999;
  font-size: 28rpx;
}

.result-scroll {
  max-height: calc(100vh - 260rpx);
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
</style>
