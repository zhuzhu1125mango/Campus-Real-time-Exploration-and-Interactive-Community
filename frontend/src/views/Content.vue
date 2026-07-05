<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { contentApi } from '../api/content'
import { useUserStore } from '../stores/userStore'
import type { ContentItem, Category } from '../types/content'

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

const handleSearch = () => {
  page.value = 1
  loadContents()
}

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

const stripHtml = (html: string) => {
  if (!html) return ''
  const tmp = document.createElement('div')
  tmp.innerHTML = html
  return tmp.textContent || tmp.innerText || ''
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
  <div class="content-page">
    <div class="content-header">
      <div class="header-inner">
        <div class="header-text">
          <h1>内容中心</h1>
          <p>发现优质校园内容，分享你的知识与见解</p>
        </div>
        <button v-if="isLoggedIn" class="btn btn-primary create-btn" @click="goCreate">
          发布内容
        </button>
      </div>
    </div>

    <div class="content-body">
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
        <input
          v-model="searchQuery"
          type="text"
          placeholder="搜索内容"
          class="search-input"
          @keyup.enter="handleSearch"
        />
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
        <button class="btn btn-secondary" @click="handleSearch">搜索</button>
      </div>

      <div v-if="loading" class="loading-state">
        <div class="loading-spinner"></div>
        <p>加载中...</p>
      </div>

      <template v-else>
        <div v-if="contents.length === 0" class="empty-state">
          <p>暂无内容</p>
          <button v-if="isLoggedIn" class="btn btn-primary" @click="goCreate">去发布第一篇内容</button>
        </div>

        <div v-else class="content-list">
          <div
            v-for="item in contents"
            :key="item.id"
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
          </div>
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
  </div>
</template>

<style scoped>
.content-page {
  min-height: calc(100vh - 200px);
}

.content-header {
  background: linear-gradient(135deg, #4361ee 0%, #3a0ca3 100%);
  color: white;
  padding: 3rem 2rem;
}

.header-inner {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.header-text h1 {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.header-text p {
  opacity: 0.9;
}

.create-btn {
  background-color: white;
  color: #4361ee;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.create-btn:hover {
  background-color: #f0f0f0;
}

.content-body {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.content-tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
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

.content-filters {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
  flex-wrap: wrap;
}

.search-input {
  flex: 1;
  min-width: 200px;
  padding: 0.75rem 1rem;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-size: 1rem;
}

.filter-select {
  padding: 0.75rem 1rem;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-size: 1rem;
  background-color: white;
  min-width: 140px;
}

.btn {
  padding: 0.75rem 1.25rem;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: all 0.3s;
}

.btn-primary {
  background-color: #4361ee;
  color: white;
}

.btn-primary:hover {
  background-color: #3a56d4;
}

.btn-secondary {
  background-color: #f0f0f0;
  color: #333;
}

.btn-secondary:hover:not(:disabled) {
  background-color: #e0e0e0;
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

.empty-state p {
  font-size: 1.1rem;
  margin-bottom: 1rem;
}

.content-list {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.content-card {
  display: flex;
  gap: 1.5rem;
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  cursor: pointer;
  transition: all 0.3s;
}

.content-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.content-image {
  width: 200px;
  height: 140px;
  object-fit: cover;
  border-radius: 8px;
  flex-shrink: 0;
}

.content-card-body {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.content-meta-top {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.category-tag,
.content-type {
  padding: 0.25rem 0.6rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 500;
}

.category-tag {
  background-color: rgba(67, 97, 238, 0.1);
  color: #4361ee;
}

.content-type {
  background-color: #f0f0f0;
  color: #666;
}

.status-tag {
  padding: 0.25rem 0.6rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
}

.status-draft {
  background-color: #f0f0f0;
  color: #666;
}

.status-pending {
  background-color: #fff3cd;
  color: #856404;
}

.status-published {
  background-color: #d4edda;
  color: #155724;
}

.status-rejected {
  background-color: #f8d7da;
  color: #721c24;
}

.content-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #333;
  margin-bottom: 0.5rem;
}

.content-summary {
  color: #666;
  line-height: 1.6;
  margin-bottom: 1rem;
  flex: 1;
}

.content-meta-bottom {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #999;
  font-size: 0.9rem;
}

.author {
  color: #4361ee;
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
  color: #666;
}

@media (max-width: 768px) {
  .header-inner {
    flex-direction: column;
    text-align: center;
  }

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
}
</style>
