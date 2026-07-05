<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { searchApi, type SearchType, type SearchResults, type SearchSuggestion } from '../api/search'

const route = useRoute()
const router = useRouter()

const query = ref('')
const activeType = ref<SearchType>('all')
const loading = ref(false)
const results = ref<SearchResults>({})
const suggestions = ref<SearchSuggestion[]>([])
const showSuggestions = ref(false)

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

const totalCount = computed(() => {
  let count = 0
  for (const key of Object.keys(results.value)) {
    const list = results.value[key as keyof SearchResults]
    if (Array.isArray(list)) count += list.length
  }
  return count
})

const stripHtml = (html: string) => {
  if (!html) return ''
  const tmp = document.createElement('div')
  tmp.innerHTML = html
  return tmp.textContent || tmp.innerText || ''
}

const doSearch = async () => {
  const q = query.value.trim()
  if (!q) {
    results.value = {}
    return
  }
  loading.value = true
  try {
    const res = await searchApi.search(q, activeType.value, 20)
    results.value = res.results
    // 更新 URL
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

const selectSuggestion = (item: SearchSuggestion) => {
  query.value = item.title
  showSuggestions.value = false
  doSearch()
}

const changeType = (type: SearchType) => {
  activeType.value = type
  doSearch()
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

watch(() => route.query, () => {
  query.value = String(route.query.q || '')
  activeType.value = (route.query.type as SearchType) || 'all'
  if (query.value) doSearch()
}, { immediate: true })
</script>

<template>
  <div class="search-page">
    <div class="search-header">
      <div class="search-header-inner">
        <h1>全局搜索</h1>
        <div class="search-box">
          <input
            v-model="query"
            type="text"
            placeholder="搜索课程、内容、学校、论坛..."
            class="search-input"
            @input="handleInput"
            @keyup.enter="doSearch"
            @blur="showSuggestions = false"
            @focus="query && loadSuggestions()"
          />
          <button class="btn btn-primary" :disabled="loading" @click="doSearch">
            {{ loading ? '搜索中...' : '搜索' }}
          </button>
          <ul v-if="showSuggestions" class="suggestions-list">
            <li
              v-for="item in suggestions"
              :key="`${item.type}-${item.id}`"
              class="suggestion-item"
              @mousedown="selectSuggestion(item)"
            >
              <span class="suggestion-type">{{ typeLabels[item.type] || item.type }}</span>
              <span class="suggestion-title">{{ item.title }}</span>
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

      <div v-if="loading" class="loading-state">
        <div class="loading-spinner"></div>
        <p>搜索中...</p>
      </div>

      <template v-else-if="query">
        <div v-if="totalCount === 0" class="empty-state">
          <p>未找到与 "{{ query }}" 相关的结果</p>
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
                <h3>{{ course.title }}</h3>
                <p>{{ course.description }}</p>
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
                <h3>{{ item.title }}</h3>
                <p>{{ stripHtml(item.summary || item.content).substring(0, 120) }}...</p>
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
                <h3>{{ school.name }}</h3>
                <p>{{ school.province }} {{ school.city }}</p>
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
                <h3>{{ topic.title }}</h3>
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
                <p>{{ stripHtml(post.content).substring(0, 150) }}...</p>
                <div class="result-meta">
                  <span>{{ post.author.username }}</span>
                  <span>{{ formatDate(post.created_at) }}</span>
                </div>
              </div>
            </div>
          </section>
        </div>
      </template>

      <div v-else class="empty-state">
        <p>输入关键词开始搜索</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.search-page {
  min-height: calc(100vh - 200px);
}

.search-header {
  background: linear-gradient(135deg, #4361ee 0%, #3a0ca3 100%);
  color: white;
  padding: 3rem 2rem;
}

.search-header-inner {
  max-width: 800px;
  margin: 0 auto;
}

.search-header h1 {
  font-size: 2rem;
  margin-bottom: 1.5rem;
}

.search-box {
  position: relative;
  display: flex;
  gap: 0.75rem;
}

.search-box .search-input {
  flex: 1;
  padding: 0.9rem 1rem;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
}

.search-box .btn {
  padding: 0 1.5rem;
  border-radius: 8px;
  border: none;
  font-weight: 500;
  cursor: pointer;
}

.suggestions-list {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  right: 0;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  list-style: none;
  padding: 0.5rem 0;
  z-index: 10;
}

.suggestion-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.7rem 1rem;
  cursor: pointer;
  color: #333;
}

.suggestion-item:hover {
  background: #f5f5f5;
}

.suggestion-type {
  font-size: 0.75rem;
  color: #4361ee;
  background: rgba(67, 97, 238, 0.1);
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
  white-space: nowrap;
}

.suggestion-title {
  font-size: 0.95rem;
}

.search-body {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.search-tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
}

.tab-btn {
  padding: 0.5rem 1rem;
  border-radius: 6px;
  border: 1px solid #e0e0e0;
  background: white;
  color: #666;
  cursor: pointer;
  transition: all 0.3s;
}

.tab-btn.active {
  background: #4361ee;
  color: white;
  border-color: #4361ee;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem;
  color: #666;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(67, 97, 238, 0.3);
  border-radius: 50%;
  border-top-color: #4361ee;
  animation: spin 1s ease-in-out infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-state {
  text-align: center;
  padding: 4rem;
  color: #666;
}

.search-results {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.result-section h2 {
  font-size: 1.1rem;
  color: #333;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #eee;
}

.result-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1rem;
}

.result-card {
  background: white;
  border-radius: 10px;
  padding: 1.25rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  cursor: pointer;
  transition: all 0.3s;
}

.result-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.result-card h3 {
  font-size: 1rem;
  font-weight: 600;
  color: #333;
  margin-bottom: 0.5rem;
}

.result-card p {
  font-size: 0.9rem;
  color: #666;
  line-height: 1.5;
  margin-bottom: 0.75rem;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.result-meta {
  display: flex;
  gap: 0.75rem;
  font-size: 0.8rem;
  color: #999;
}

.btn-primary {
  background-color: #4361ee;
  color: white;
}

.btn-primary:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .search-box {
    flex-direction: column;
  }

  .search-box .btn {
    padding: 0.75rem;
  }
}
</style>
