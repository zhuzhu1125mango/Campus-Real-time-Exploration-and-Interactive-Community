<template>
  <view class="container">
    <!-- 顶部标题区 -->
    <view class="header">
      <view class="header-title">内容中心</view>
      <view class="header-desc">发现优质校园内容，分享你的知识与见解</view>
      <button class="create-btn" v-if="isLoggedIn" @click="goCreate">发布内容</button>
    </view>

    <!-- 投稿状态 Tab -->
    <view class="content-tabs" v-if="isLoggedIn">
      <view
        v-for="tab in tabs"
        :key="tab.key"
        class="tab-item"
        :class="{ active: activeTab === tab.key }"
        @click="setTab(tab.key)"
      >
        {{ tab.label }}
      </view>
    </view>

    <!-- 搜索与筛选 -->
    <view class="filter-section">
      <view class="search-bar">
        <input
          type="text"
          v-model="searchQuery"
          placeholder="搜索内容"
          class="search-input"
          @confirm="handleSearch"
        />
        <button class="search-btn" @click="handleSearch">搜索</button>
      </view>
      <view class="filter-row">
        <picker mode="selector" :range="categoryNames" :value="categoryIndex" @change="onCategoryChange">
          <view class="filter-picker">{{ categoryNames[categoryIndex] || '全部分类' }}</view>
        </picker>
        <picker mode="selector" :range="orderOptions" :value="orderIndex" range-key="label" @change="onOrderChange">
          <view class="filter-picker">{{ orderOptions[orderIndex].label }}</view>
        </picker>
      </view>
    </view>

    <!-- 内容列表 -->
    <view class="content-list" v-if="contents.length > 0">
      <view
        class="content-card"
        v-for="item in contents"
        :key="item.id"
        @click="goDetail(item.id)"
      >
        <image
          v-if="item.featured_image"
          class="content-image"
          :src="item.featured_image"
          mode="aspectFill"
        />
        <view class="content-body">
          <view class="content-meta-top">
            <text v-if="item.category" class="category-tag">{{ item.category.name }}</text>
            <text class="content-type">{{ item.content_type?.name }}</text>
            <text
              v-if="activeTab !== 'all' && item.status"
              class="status-tag"
              :class="statusClass[item.status]"
            >
              {{ statusLabels[item.status] }}
            </text>
          </view>
          <view class="content-title">{{ item.title }}</view>
          <view class="content-summary">{{ stripHtml(item.summary || item.content).substring(0, 80) }}...</view>
          <view class="content-meta-bottom">
            <text class="author">{{ item.author?.username }}</text>
            <text class="divider">·</text>
            <text>{{ formatDate(item.created_at) }}</text>
            <text class="divider">·</text>
            <text>{{ item.view_count }} 浏览</text>
          </view>
        </view>
      </view>

      <view class="load-more" v-if="loadingMore">加载中...</view>
      <view class="no-more" v-else-if="!hasMore">没有更多了</view>
    </view>

    <view class="empty-state" v-else-if="!loading">
      <text>暂无内容</text>
      <button class="empty-btn" v-if="isLoggedIn" @click="goCreate">去发布第一篇内容</button>
    </view>

    <view class="loading-state" v-if="loading && contents.length === 0">
      <text>加载中...</text>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import contentApi from '../../api/content'

const contents = ref([])
const categories = ref([])
const categoryIndex = ref(0)
const loading = ref(false)
const loadingMore = ref(false)
const searchQuery = ref('')
const ordering = ref('-created_at')
const page = ref(1)
const total = ref(0)
const hasMore = ref(true)
const isLoggedIn = ref(false)
const activeTab = ref('all')

const tabs = [
  { key: 'all', label: '全部' },
  { key: 'mine', label: '我的投稿' },
  { key: 'draft', label: '草稿' },
  { key: 'pending', label: '待审核' },
  { key: 'rejected', label: '已拒绝' }
]

const statusLabels = {
  draft: '草稿',
  pending: '待审核',
  published: '已发布',
  rejected: '已拒绝'
}

const statusClass = {
  draft: 'status-draft',
  pending: 'status-pending',
  published: 'status-published',
  rejected: 'status-rejected'
}

const orderOptions = [
  { value: '-created_at', label: '最新发布' },
  { value: '-view_count', label: '最多浏览' },
  { value: '-like_count', label: '最多点赞' },
  { value: '-comment_count', label: '最多评论' }
]
const orderIndex = ref(0)

const categoryNames = computed(() => {
  return ['全部分类', ...categories.value.map(c => c.name)]
})

onMounted(() => {
  isLoggedIn.value = !!uni.getStorageSync('accessToken')
  loadCategories()
  loadContents()
})

const loadCategories = async () => {
  try {
    const res = await contentApi.getCategories()
    categories.value = res.results || []
  } catch (error) {
    console.error('加载分类失败', error)
  }
}

const loadContents = async (isRefresh = false) => {
  if (isRefresh) {
    page.value = 1
    contents.value = []
  }
  if (page.value === 1) {
    loading.value = true
  } else {
    loadingMore.value = true
  }

  try {
    let res
    if (activeTab.value === 'all') {
      const params = {
        page: page.value,
        ordering: ordering.value,
        is_published: true
      }
      if (searchQuery.value.trim()) {
        params.search = searchQuery.value.trim()
      }
      if (categoryIndex.value > 0) {
        params.category = categories.value[categoryIndex.value - 1].id
      }
      res = await contentApi.getContents(params)
    } else {
      const params = { page: page.value }
      if (activeTab.value !== 'mine') {
        params.status = activeTab.value
      }
      res = await contentApi.getMyContents(params)
    }

    const results = Array.isArray(res) ? res : (res.results || [])
    if (page.value === 1) {
      contents.value = results
    } else {
      contents.value.push(...results)
    }
    total.value = res.count || results.length
    hasMore.value = !!res.next
  } catch (error) {
    console.error('加载内容失败', error)
    uni.showToast({ title: '加载内容失败', icon: 'none' })
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

const handleSearch = () => {
  loadContents(true)
}

const setTab = (tab) => {
  if (activeTab.value === tab) return
  activeTab.value = tab
  loadContents(true)
}

const onCategoryChange = (e) => {
  categoryIndex.value = Number(e.detail.value)
  loadContents(true)
}

const onOrderChange = (e) => {
  orderIndex.value = Number(e.detail.value)
  ordering.value = orderOptions[orderIndex.value].value
  loadContents(true)
}

const loadMore = () => {
  if (!hasMore.value || loadingMore.value) return
  page.value += 1
  loadContents()
}

const goDetail = (id) => {
  uni.navigateTo({ url: `/pages/content-detail/content-detail?id=${id}` })
}

const goCreate = () => {
  uni.navigateTo({ url: '/pages/content-create/content-create' })
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

// 下拉刷新
const onPullDownRefresh = async () => {
  await loadContents(true)
  uni.stopPullDownRefresh()
}

// 触底加载
const onReachBottom = () => {
  loadMore()
}
</script>

<style scoped>
.container {
  min-height: 100vh;
  background-color: #f5f5f5;
  padding-bottom: 20rpx;
}

.header {
  background: linear-gradient(135deg, #4361ee 0%, #3a0ca3 100%);
  color: #fff;
  padding: 40rpx 30rpx;
}

.header-title {
  font-size: 40rpx;
  font-weight: 600;
  margin-bottom: 10rpx;
}

.header-desc {
  font-size: 26rpx;
  opacity: 0.9;
  margin-bottom: 20rpx;
}

.create-btn {
  display: inline-block;
  background-color: #fff;
  color: #4361ee;
  font-size: 26rpx;
  padding: 10rpx 30rpx;
  border-radius: 30rpx;
  border: none;
}

.filter-section {
  background-color: #fff;
  padding: 20rpx 30rpx;
  margin-bottom: 20rpx;
}

.search-bar {
  display: flex;
  align-items: center;
  background-color: #f5f5f5;
  border-radius: 50rpx;
  padding: 10rpx 20rpx;
  margin-bottom: 20rpx;
}

.search-input {
  flex: 1;
  height: 60rpx;
  font-size: 28rpx;
}

.search-btn {
  background-color: #4361ee;
  color: #fff;
  font-size: 26rpx;
  padding: 10rpx 30rpx;
  border-radius: 30rpx;
  border: none;
}

.filter-row {
  display: flex;
  gap: 20rpx;
}

.filter-picker {
  background-color: #f5f5f5;
  color: #666;
  font-size: 26rpx;
  padding: 14rpx 24rpx;
  border-radius: 30rpx;
}

.content-list {
  padding: 0 30rpx;
}

.content-card {
  background-color: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
  margin-bottom: 20rpx;
}

.content-image {
  width: 100%;
  height: 300rpx;
  border-radius: 12rpx;
  margin-bottom: 20rpx;
}

.content-meta-top {
  display: flex;
  gap: 12rpx;
  margin-bottom: 14rpx;
}

.category-tag {
  background-color: rgba(67, 97, 238, 0.1);
  color: #4361ee;
  font-size: 22rpx;
  padding: 4rpx 14rpx;
  border-radius: 6rpx;
}

.content-type {
  background-color: #f0f0f0;
  color: #666;
  font-size: 22rpx;
  padding: 4rpx 14rpx;
  border-radius: 6rpx;
}

.status-tag {
  font-size: 20rpx;
  padding: 2rpx 10rpx;
  border-radius: 6rpx;
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

.content-tabs {
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

.content-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 12rpx;
}

.content-summary {
  font-size: 26rpx;
  color: #666;
  line-height: 1.6;
  margin-bottom: 16rpx;
}

.content-meta-bottom {
  font-size: 24rpx;
  color: #999;
}

.author {
  color: #4361ee;
}

.divider {
  margin: 0 8rpx;
}

.load-more,
.no-more {
  text-align: center;
  padding: 24rpx;
  font-size: 24rpx;
  color: #999;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 120rpx 40rpx;
  color: #999;
  font-size: 28rpx;
}

.empty-btn {
  margin-top: 30rpx;
  background-color: #4361ee;
  color: #fff;
  font-size: 26rpx;
  padding: 12rpx 40rpx;
  border-radius: 30rpx;
  border: none;
}

.loading-state {
  text-align: center;
  padding: 120rpx;
  color: #999;
}
</style>
