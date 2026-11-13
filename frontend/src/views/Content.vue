<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { contentApi } from '../api/content'
import { useUserStore } from '../stores/userStore'
import { stripHtml } from '../utils/xss'
import { debounce } from '../utils/debounce'
import type { ContentItem, Category } from '../types/content'
import GlassCard from '../components/GlassCard.vue'
import SectionHeader from '../components/SectionHeader.vue'

const router = useRouter()
const userStore = useUserStore()

const contents = ref<ContentItem[]>([])
const categories = ref<Category[]>([])
const loading = ref(false)
const searchQuery = ref('')
const selectedCategory = ref('')
const ordering = ref('-created_at')
const page = ref(1)
const total = ref(0)
const nextUrl = ref<string | null>(null)
const prevUrl = ref<string | null>(null)
const activeTab = ref<'all' | 'mine' | 'draft' | 'pending' | 'rejected'>('all')

const isLoggedIn = computed(() => userStore.isLoggedIn)

const statusLabels: Record<string, string> = {
  draft: '草稿',
  pending: '待审核',
  published: '已发布',
  rejected: '已拒绝'
}

const statusClass: Record<string, string> = {
  draft: 'status-draft',
  pending: 'status-pending',
  published: 'status-published',
  rejected: 'status-rejected'
}

const loadContents = async () => {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: page.value,
      ordering: ordering.value
    }
    if (searchQuery.value.trim()) {
      params.search = searchQuery.value.trim()
    }
    if (selectedCategory.value) {
      params.category = selectedCategory.value
    }

    if (activeTab.value === 'all') {
      params.is_published = true
      const paginatedResponse = await contentApi.getContents(params)
      contents.value = paginatedResponse.results
      total.value = paginatedResponse.count
      nextUrl.value = paginatedResponse.next
      prevUrl.value = paginatedResponse.previous
    } else {
      const status = activeTab.value === 'mine' ? undefined : activeTab.value
      const listResponse = await contentApi.getMyContents({ status })
      contents.value = listResponse
      total.value = listResponse.length
      nextUrl.value = null
      prevUrl.value = null
    }
  } catch (error) {
    console.error('加载内容失败', error)
  } finally {
    loading.value = false
  }
}

const loadCategories = async () => {
  try {
    const response = await contentApi.getCategories()
    categories.value = response.results
  } catch (error) {
    console.error('加载分类失败', error)
  }
}

const handleSearch = debounce(() => {
  page.value = 1
  loadContents()
}, 400)

const setTab = (tab: 'all' | 'mine' | 'draft' | 'pending' | 'rejected') => {
  activeTab.value = tab
  page.value = 1
  loadContents()
}

const changePage = (newPage: number) => {
  page.value = newPage
  loadContents()
}

const goDetail = (id: number | string) => {
  router.push(`/content/${id}`)
}

const goCreate = () => {
  router.push('/content/create')
}

const formatDate = (date: string) => {
  return new Date(date).toLocaleDateString('zh-CN')
}

watch([selectedCategory, ordering, activeTab], () => {
  page.value = 1
  loadContents()
})

onMounted(() => {
  loadCategories()
  loadContents()
})
</script>

<template>
  <div class="content-page container-wide page-padding">
    <SectionHeader
      title="内容中心"
      subtitle="发现优质校园内容，分享你的知识与见解"
      icon="i-ep-reading"
      :action="isLoggedIn ? { label: '发布内容', onClick: goCreate } : undefined"
    />

    <GlassCard :hover="false" class="filter-card">
      <div v-if="isLoggedIn" class="content-tabs">
        <button
          v-for="tab in [
            { key: 'all', label: '全部' },
            { key: 'mine', label: '我的投稿' },
            { key: 'draft', label: '草稿' },
            { key: 'pending', label: '待审核' },
            { key: 'rejected', label: '已拒绝' }
          ]"
          :key="tab.key"
          class="tab-btn"
          :class="{ active: activeTab === tab.key }"
          @click="setTab(tab.key as any)"
        >
          {{ tab.label }}
        </button>
      </div>

      <div class="content-filters">
        <div class="search-box">
          <span class="i-ep-search search-icon" />
          <input
            v-model="searchQuery"
            type="text"
            placeholder="搜索内容"
            class="search-input"
            maxlength="100"
            @input="handleSearch"
            @keyup.enter="handleSearch"
          />
        </div>
        <select v-model="selectedCategory" class="filter-select">
          <option value="">全部分类</option>
          <option v-for="category in categories" :key="category.id" :value="category.id">
            {{ category.name }}
          </option>
        </select>
        <select v-model="ordering" class="filter-select">
          <option value="-created_at">最新发布</option>
          <option value="-view_count">最多浏览</option>
          <option value="-like_count">最多点赞</option>
          <option value="-comment_count">最多评论</option>
        </select>
      </div>
    </GlassCard>

    <div v-if="loading" class="loading-state">
      <div class="loading-spinner"></div>
      <p>加载中...</p>
    </div>

    <template v-else>
      <div v-if="contents.length === 0" class="empty-state">
        <span class="i-ep-document empty-icon" />
        <p>暂无内容</p>
        <button v-if="isLoggedIn" class="btn btn-primary" @click="goCreate">去发布第一篇内容</button>
      </div>

      <div v-else class="content-list">
        <GlassCard
          v-for="item in contents"
          :key="item.id"
          :hover="true"
          class="content-card"
          @click="goDetail(item.id)"
        >
          <img
            v-if="item.featured_image"
            :src="item.featured_image"
            :alt="item.title"
            class="content-image"
          />
          <div class="content-card-body">
            <div class="content-meta-top">
              <span v-if="item.category" class="category-tag">{{ item.category.name }}</span>
              <span class="content-type">{{ item.content_type.name }}</span>
              <span v-if="activeTab !== 'all' && item.status" class="status-tag" :class="statusClass[item.status]">
                {{ statusLabels[item.status] }}
              </span>
            </div>
            <h3 class="content-title">{{ item.title }}</h3>
            <p class="content-summary">{{ stripHtml(item.summary || item.content).substring(0, 120) }}...</p>
            <div class="content-meta-bottom">
              <span class="author">{{ item.author.username }}</span>
              <span class="divider">·</span>
              <span>{{ formatDate(item.created_at) }}</span>
              <span class="divider">·</span>
              <span>{{ item.view_count }} 浏览</span>
              <span class="divider">·</span>
              <span>{{ item.like_count }} 点赞</span>
              <span class="divider">·</span>
              <span>{{ item.comment_count }} 评论</span>
            </div>
          </div>
        </GlassCard>
      </div>

      <div v-if="contents.length > 0" class="pagination">
        <button
          class="btn btn-secondary"
          :disabled="!prevUrl"
          @click="changePage(page - 1)"
        >
          上一页
        </button>
        <span class="page-info">第 {{ page }} 页</span>
        <button
          class="btn btn-secondary"
          :disabled="!nextUrl"
          @click="changePage(page + 1)"
        >
          下一页
        </button>
      </div>
    </template>
  </div>
</template>

<style scoped>
.content-page {
  color: var(--text-primary);
}

.filter-card {
  margin-bottom: 1.5rem;
}

.content-tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.25rem;
  flex-wrap: wrap;
  padding-bottom: 1.25rem;
  border-bottom: 1px solid var(--border-color-light);
}

.tab-btn {
  padding: 0.5rem 1rem;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.tab-btn:hover {
  border-color: var(--primary-400);
  color: var(--primary-600);
}

.tab-btn.active {
  background: var(--primary-600);
  border-color: var(--primary-600);
  color: white;
}

.content-filters {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.search-box {
  flex: 1;
  min-width: 240px;
  display: flex;
  align-items: center;
  position: relative;
}

.search-icon {
  position: absolute;
  left: 1rem;
  color: var(--text-tertiary);
}

.search-input {
  width: 100%;
  padding: 0.625rem 1rem 0.625rem 2.5rem;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  font-size: 0.95rem;
  background: var(--bg-primary);
  color: var(--text-primary);
  transition: border-color 0.2s;
}

.search-input:focus {
  outline: none;
  border-color: var(--primary-500);
}

.filter-select {
  padding: 0.625rem 1rem;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  font-size: 0.95rem;
  background: var(--bg-primary);
  color: var(--text-primary);
  min-width: 140px;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.625rem 1.25rem;
  border-radius: var(--radius-md);
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: all 0.2s;
}

.btn-primary {
  background-color: var(--primary-600);
  color: white;
}

.btn-primary:hover {
  background-color: var(--primary-700);
}

.btn-secondary {
  background-color: var(--bg-tertiary);
  color: var(--text-primary);
}

.btn-secondary:hover:not(:disabled) {
  background-color: var(--border-color);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 0;
  color: var(--text-secondary);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--primary-200);
  border-top-color: var(--primary-600);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 4rem 0;
  color: var(--text-secondary);
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  opacity: 0.4;
}

.empty-state p {
  font-size: 1.1rem;
  margin-bottom: 1rem;
}

.content-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.content-card {
  display: flex;
  gap: 1.25rem;
  cursor: pointer;
}

.content-image {
  width: 200px;
  height: 140px;
  object-fit: cover;
  border-radius: var(--radius-lg);
  flex-shrink: 0;
}

.content-card-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.content-meta-top {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
  flex-wrap: wrap;
}

.category-tag,
.content-type,
.status-tag {
  padding: 0.25rem 0.6rem;
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-weight: 500;
}

.category-tag {
  background-color: var(--primary-50);
  color: var(--primary-700);
}

.content-type {
  background-color: var(--bg-tertiary);
  color: var(--text-secondary);
}

.status-draft {
  background-color: var(--bg-tertiary);
  color: var(--text-secondary);
}

.status-pending {
  background-color: var(--warning-bg);
  color: var(--warning-color);
}

.status-published {
  background-color: var(--success-bg);
  color: var(--success-color);
}

.status-rejected {
  background-color: var(--error-bg);
  color: var(--error-color);
}

.content-title {
  font-size: 1.15rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 0.5rem;
}

.content-summary {
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: 1rem;
  flex: 1;
}

.content-meta-bottom {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  color: var(--text-tertiary);
  font-size: 0.875rem;
  flex-wrap: wrap;
}

.author {
  color: var(--primary-600);
  font-weight: 500;
}

.divider {
  margin: 0 0.25rem;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  margin-top: 2rem;
}

.page-info {
  color: var(--text-secondary);
  font-size: 0.875rem;
}

@media (max-width: 768px) {
  .content-card {
    flex-direction: column;
  }

  .content-image {
    width: 100%;
    height: 180px;
  }

  .content-filters {
    flex-direction: column;
  }

  .search-box {
    min-width: auto;
  }

  .filter-select {
    width: 100%;
  }
}
</style>
