<script setup lang="ts">
import { ref, watch, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Search, Clock, Top, Close, ArrowRight } from '@element-plus/icons-vue'
import { searchApi, type SearchType, type SearchResults, type SearchSuggestion } from '../api/search'
import { stripHtml, escapeHtml } from '../utils/xss'

const route = useRoute()
const router = useRouter()

const query = ref('')
const activeType = ref<SearchType>('all')
const loading = ref(false)
const results = ref<SearchResults>({})
const suggestions = ref<SearchSuggestion[]>([])
const showSuggestions = ref(false)
const searchHistory = ref<string[]>([])

const HISTORY_KEY = 'campus_search_history'
const MAX_HISTORY = 10

const searchTypes: { key: SearchType; label: string }[] = [
  { key: 'all', label: '全部' },
  { key: 'course', label: '课程' },
  { key: 'content', label: '内容' },
  { key: 'school', label: '学校' },
  { key: 'topic', label: '论坛主题' },
  { key: 'post', label: '帖子' }
]

const typeLabels: Record<string, string> = {
  course: '课程',
  content: '内容',
  school: '学校',
  topic: '论坛主题',
  post: '帖子'
}

const hotSearches = ['计算机', '清华大学', '考研', 'Python', '校园活动']

const totalCount = computed(() => {
  let count = 0
  for (const key of Object.keys(results.value)) {
    const list = results.value[key as keyof SearchResults]
    if (Array.isArray(list)) count += list.length
  }
  return count
})

const hasSearched = computed(() => query.value.trim() !== '' && !loading.value)

const loadHistory = () => {
  try {
    const raw = localStorage.getItem(HISTORY_KEY)
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
    localStorage.setItem(HISTORY_KEY, JSON.stringify(searchHistory.value))
  } catch {
    // ignore
  }
}

const addHistory = (keyword: string) => {
  if (!keyword) return
  const list = searchHistory.value.filter(item => item !== keyword)
  list.unshift(keyword)
  searchHistory.value = list.slice(0, MAX_HISTORY)
  saveHistory()
}

const removeHistory = (keyword: string) => {
  searchHistory.value = searchHistory.value.filter(item => item !== keyword)
  saveHistory()
}

const clearHistory = () => {
  searchHistory.value = []
  saveHistory()
}

const useHistory = (keyword: string) => {
  query.value = keyword
  showSuggestions.value = false
  doSearch()
}

const doSearch = async () => {
  const q = query.value.trim()
  if (!q) {
    results.value = {}
    return
  }
  loading.value = true
  showSuggestions.value = false
  try {
    const res = await searchApi.search(q, activeType.value, 20)
    results.value = res.results
    addHistory(q)
    router.replace({ path: '/search', query: { q, type: activeType.value } })
  } catch (error) {
    console.error('搜索失败', error)
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
    suggestions.value = res.suggestions
    showSuggestions.value = suggestions.value.length > 0
  } catch (error) {
    console.error('获取搜索建议失败', error)
  }
}

let suggestionTimer: number | null = null
const handleInput = () => {
  if (suggestionTimer) clearTimeout(suggestionTimer)
  suggestionTimer = window.setTimeout(loadSuggestions, 300)
}

const handleFocus = () => {
  if (query.value.trim()) {
    loadSuggestions()
  }
}

const selectSuggestion = (item: SearchSuggestion) => {
  query.value = item.title
  showSuggestions.value = false
  doSearch()
}

const changeType = (type: SearchType) => {
  activeType.value = type
  if (query.value.trim()) {
    doSearch()
  }
}

const goDetail = (type: string, item: any) => {
  if (type === 'course') router.push(`/learning/course/${item.id}`)
  else if (type === 'content') router.push(`/content/${item.id}`)
  else if (type === 'school') router.push(`/schools/${item.id}`)
  else if (type === 'topic') router.push(`/forum/topic/${item.id}`)
  else if (type === 'post') router.push(`/forum/topic/${item.topic}`)
}

const formatDate = (date: string) => {
  return new Date(date).toLocaleDateString('zh-CN')
}

const highlightText = (text: string, keyword: string) => {
  if (!keyword || !text) return text
  const safeText = escapeHtml(text)
  const safeKeyword = keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const regex = new RegExp(`(${safeKeyword})`, 'gi')
  return safeText.replace(regex, '<mark>$1</mark>')
}

watch(() => route.query, () => {
  query.value = String(route.query.q || '')
  activeType.value = (route.query.type as SearchType) || 'all'
  if (query.value) doSearch()
}, { immediate: true })

onMounted(() => {
  loadHistory()
})
</script>

<template>
  <div class="search-page">
    <div class="search-header">
      <div class="search-header-inner">
        <h1>全局搜索</h1>
        <div class="search-box">
          <div class="search-input-wrapper">
            <Search class="search-icon" />
            <input
              v-model="query"
              type="text"
              placeholder="搜索课程、内容、学校、论坛..."
              class="search-input"
              maxlength="100"
              @input="handleInput"
              @keyup.enter="doSearch"
              @focus="handleFocus"
            />
            <button v-if="query" class="clear-btn" @click="query = ''; results = {}">
              <Close />
            </button>
          </div>
          <button class="btn btn-primary" :disabled="loading" @click="doSearch">
            {{ loading ? '搜索中' : '搜索' }}
          </button>
          <ul v-if="showSuggestions" class="suggestions-list">
            <li
              v-for="item in suggestions"
              :key="`${item.type}-${item.id}`"
              class="suggestion-item"
              @mousedown="selectSuggestion(item)"
            >
              <span class="suggestion-type">{{ typeLabels[item.type] || item.type }}</span>
              <span class="suggestion-title" v-html="highlightText(item.title, query)"></span>
              <ArrowRight class="suggestion-arrow" />
            </li>
          </ul>
        </div>
      </div>
    </div>

    <div class="search-body">
      <div class="search-tabs">
        <button
          v-for="t in searchTypes"
          :key="t.key"
          class="tab-btn"
          :class="{ active: activeType === t.key }"
          @click="changeType(t.key)"
        >
          {{ t.label }}
        </button>
      </div>

      <div v-if="loading" class="skeleton-wrapper">
        <div v-for="i in 3" :key="i" class="skeleton-section">
          <div class="skeleton-title"></div>
          <div class="skeleton-list">
            <div v-for="j in 3" :key="j" class="skeleton-card">
              <div class="skeleton-line short"></div>
              <div class="skeleton-line"></div>
              <div class="skeleton-line shorter"></div>
            </div>
          </div>
        </div>
      </div>

      <template v-else-if="hasSearched">
        <div v-if="totalCount === 0" class="empty-state">
          <div class="empty-icon">
            <Search />
          </div>
          <p class="empty-title">未找到与 "{{ query }}" 相关的结果</p>
          <p class="empty-desc">换个关键词试试看</p>
        </div>

        <div v-else class="search-results">
          <section v-if="results.courses && results.courses.length > 0" class="result-section">
            <h2>课程</h2>
            <div class="result-list">
              <div
                v-for="course in results.courses"
                :key="`course-${course.id}`"
                class="result-card"
                @click="goDetail('course', course)"
              >
                <h3 v-html="highlightText(course.title, query)"></h3>
                <p v-html="highlightText(course.description, query)"></p>
                <div class="result-meta">
                  <span>{{ course.instructor.username }}</span>
                  <span>{{ course.enroll_count }} 人报名</span>
                </div>
              </div>
            </div>
          </section>

          <section v-if="results.contents && results.contents.length > 0" class="result-section">
            <h2>内容</h2>
            <div class="result-list">
              <div
                v-for="item in results.contents"
                :key="`content-${item.id}`"
                class="result-card"
                @click="goDetail('content', item)"
              >
                <h3 v-html="highlightText(item.title, query)"></h3>
                <p v-html="highlightText(stripHtml(item.summary || item.content).substring(0, 120), query) + '...'"></p>
                <div class="result-meta">
                  <span>{{ item.author.username }}</span>
                  <span>{{ formatDate(item.created_at) }}</span>
                </div>
              </div>
            </div>
          </section>

          <section v-if="results.schools && results.schools.length > 0" class="result-section">
            <h2>学校</h2>
            <div class="result-list">
              <div
                v-for="school in results.schools"
                :key="`school-${school.id}`"
                class="result-card"
                @click="goDetail('school', school)"
              >
                <h3 v-html="highlightText(school.name, query)"></h3>
                <p v-html="highlightText(`${school.province} ${school.city}`, query)"></p>
                <div class="result-meta">
                  <span>{{ school.school_level }}</span>
                  <span v-if="school.national_rank">全国排名 {{ school.national_rank }}</span>
                </div>
              </div>
            </div>
          </section>

          <section v-if="results.topics && results.topics.length > 0" class="result-section">
            <h2>论坛主题</h2>
            <div class="result-list">
              <div
                v-for="topic in results.topics"
                :key="`topic-${topic.id}`"
                class="result-card"
                @click="goDetail('topic', topic)"
              >
                <h3 v-html="highlightText(topic.title, query)"></h3>
                <div class="result-meta">
                  <span>{{ topic.author.username }}</span>
                  <span>{{ topic.views }} 浏览</span>
                  <span>{{ formatDate(topic.created_at) }}</span>
                </div>
              </div>
            </div>
          </section>

          <section v-if="results.posts && results.posts.length > 0" class="result-section">
            <h2>帖子</h2>
            <div class="result-list">
              <div
                v-for="post in results.posts"
                :key="`post-${post.id}`"
                class="result-card"
                @click="goDetail('post', post)"
              >
                <p v-html="highlightText(stripHtml(post.content).substring(0, 150), query) + '...'"></p>
                <div class="result-meta">
                  <span>{{ post.author.username }}</span>
                  <span>{{ formatDate(post.created_at) }}</span>
                </div>
              </div>
            </div>
          </section>
        </div>
      </template>

      <div v-else class="search-placeholder">
        <div v-if="searchHistory.length > 0" class="history-section">
          <div class="section-header">
            <Clock class="section-icon" />
            <span class="section-title">搜索历史</span>
            <button class="clear-link" @click="clearHistory">清空</button>
          </div>
          <div class="tag-list">
            <span
              v-for="item in searchHistory"
              :key="item"
              class="history-tag"
              @click="useHistory(item)"
            >
              {{ item }}
              <span class="remove-btn" @click.stop="removeHistory(item)">
                <Close />
              </span>
            </span>
          </div>
        </div>

        <div class="hot-section">
          <div class="section-header">
            <Top class="section-icon" />
            <span class="section-title">热门搜索</span>
          </div>
          <div class="tag-list">
            <span
              v-for="item in hotSearches"
              :key="item"
              class="hot-tag"
              @click="useHistory(item)"
            >
              {{ item }}
            </span>
          </div>
        </div>

        <div class="empty-state soft">
          <div class="empty-icon">
            <Search />
          </div>
          <p class="empty-title">输入关键词开始搜索</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.search-page {
  min-height: calc(100vh - 200px);
}

.search-header {
  background: linear-gradient(135deg, var(--primary-500) 0%, var(--primary-700) 100%);
  color: white;
  padding: var(--space-10) var(--space-6);
}

.search-header-inner {
  max-width: 800px;
  margin: 0 auto;
}

.search-header h1 {
  font-size: 2rem;
  margin-bottom: var(--space-6);
}

.search-box {
  position: relative;
  display: flex;
  gap: var(--space-3);
}

.search-input-wrapper {
  flex: 1;
  position: relative;
  display: flex;
  align-items: center;
  background: white;
  border-radius: var(--radius-lg);
  padding: 0 var(--space-4);
}

.search-icon {
  width: 20px;
  height: 20px;
  color: var(--text-tertiary);
  flex-shrink: 0;
}

.search-box .search-input {
  flex: 1;
  padding: var(--space-3) var(--space-3);
  border: none;
  background: transparent;
  font-size: 1rem;
  color: var(--text-primary);
  outline: none;
}

.search-box .search-input::placeholder {
  color: var(--text-tertiary);
}

.clear-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all 0.2s;
}

.clear-btn:hover {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
}

.search-box .btn {
  padding: 0 var(--space-6);
  border-radius: var(--radius-lg);
  border: none;
  font-weight: 500;
  cursor: pointer;
}

.suggestions-list {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  right: calc(72px + var(--space-3));
  background: white;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  list-style: none;
  padding: var(--space-2) 0;
  z-index: 10;
}

.suggestion-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  cursor: pointer;
  color: var(--text-primary);
  transition: background-color 0.2s;
}

.suggestion-item:hover {
  background: var(--primary-50);
}

.suggestion-type {
  font-size: 0.75rem;
  color: var(--primary-500);
  background: var(--primary-50);
  padding: 0.15rem var(--space-2);
  border-radius: var(--radius-sm);
  white-space: nowrap;
}

.suggestion-title {
  flex: 1;
  font-size: 0.95rem;
}

.suggestion-title :deep(mark) {
  background: transparent;
  color: var(--primary-500);
  font-weight: 600;
}

.suggestion-arrow {
  width: 16px;
  height: 16px;
  color: var(--text-tertiary);
}

.search-body {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--space-6);
}

.search-tabs {
  display: flex;
  gap: var(--space-2);
  margin-bottom: var(--space-6);
  flex-wrap: wrap;
}

.tab-btn {
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-full);
  border: 1px solid var(--border-color);
  background: white;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.tab-btn:hover {
  border-color: var(--primary-300);
  color: var(--primary-500);
}

.tab-btn.active {
  background: var(--primary-500);
  color: white;
  border-color: var(--primary-500);
}

.skeleton-wrapper {
  display: flex;
  flex-direction: column;
  gap: var(--space-8);
}

.skeleton-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.skeleton-title {
  width: 80px;
  height: 24px;
  background: linear-gradient(90deg, var(--bg-tertiary) 25%, var(--bg-secondary) 50%, var(--bg-tertiary) 75%);
  background-size: 200% 100%;
  border-radius: var(--radius-sm);
  animation: shimmer 1.5s infinite;
}

.skeleton-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--space-4);
}

.skeleton-card {
  background: white;
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  box-shadow: var(--shadow-sm);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.skeleton-line {
  height: 16px;
  background: linear-gradient(90deg, var(--bg-tertiary) 25%, var(--bg-secondary) 50%, var(--bg-tertiary) 75%);
  background-size: 200% 100%;
  border-radius: var(--radius-sm);
  animation: shimmer 1.5s infinite;
}

.skeleton-line.short {
  width: 60%;
}

.skeleton-line.shorter {
  width: 40%;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.empty-state {
  text-align: center;
  padding: var(--space-12);
  color: var(--text-secondary);
}

.empty-state.soft {
  padding: var(--space-10) 0;
}

.empty-icon {
  width: 72px;
  height: 72px;
  margin: 0 auto var(--space-4);
  border-radius: 50%;
  background: var(--primary-50);
  color: var(--primary-500);
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-icon svg {
  width: 36px;
  height: 36px;
}

.empty-title {
  font-size: 1.1rem;
  color: var(--text-primary);
  margin-bottom: var(--space-2);
}

.empty-desc {
  font-size: 0.9rem;
  color: var(--text-tertiary);
}

.search-results {
  display: flex;
  flex-direction: column;
  gap: var(--space-8);
}

.result-section h2 {
  font-size: 1.1rem;
  color: var(--text-primary);
  margin-bottom: var(--space-4);
  padding-bottom: var(--space-2);
  border-bottom: 1px solid var(--border-color-light);
}

.result-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--space-4);
}

.result-card {
  background: white;
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  box-shadow: var(--shadow-sm);
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.result-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
  border-color: var(--primary-100);
}

.result-card h3 {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--space-2);
}

.result-card h3 :deep(mark) {
  background: transparent;
  color: var(--primary-500);
  font-weight: 700;
}

.result-card p {
  font-size: 0.9rem;
  color: var(--text-secondary);
  line-height: 1.5;
  margin-bottom: var(--space-3);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.result-card p :deep(mark) {
  background: transparent;
  color: var(--primary-500);
  font-weight: 600;
}

.result-meta {
  display: flex;
  gap: var(--space-3);
  font-size: 0.8rem;
  color: var(--text-tertiary);
}

.btn-primary {
  background-color: var(--primary-500);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: var(--primary-600);
}

.btn-primary:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.search-placeholder {
  display: flex;
  flex-direction: column;
  gap: var(--space-8);
}

.history-section,
.hot-section {
  background: white;
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  box-shadow: var(--shadow-sm);
}

.section-header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-4);
}

.section-icon {
  width: 18px;
  height: 18px;
  color: var(--primary-500);
}

.section-title {
  flex: 1;
  font-weight: 600;
  color: var(--text-primary);
}

.clear-link {
  font-size: 0.85rem;
  color: var(--text-tertiary);
  cursor: pointer;
  transition: color 0.2s;
}

.clear-link:hover {
  color: var(--error-color);
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
}

.history-tag,
.hot-tag {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-full);
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s;
}

.history-tag:hover,
.hot-tag:hover {
  background: var(--primary-50);
  color: var(--primary-500);
}

.remove-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  color: var(--text-tertiary);
}

.remove-btn:hover {
  background: var(--border-color);
  color: var(--text-primary);
}

.hot-tag {
  background: var(--primary-50);
  color: var(--primary-600);
}

.hot-tag:hover {
  background: var(--primary-100);
}

@media (max-width: 768px) {
  .search-box {
    flex-direction: column;
  }

  .search-box .btn {
    padding: var(--space-3);
  }

  .suggestions-list {
    right: 0;
  }

  .search-header h1 {
    font-size: 1.5rem;
  }
}
</style>
