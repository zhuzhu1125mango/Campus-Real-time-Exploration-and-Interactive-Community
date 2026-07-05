<template>
  <view class="container">
    <!-- 顶部 -->
    <view class="header">
      <view class="header-title">在线学习</view>
      <view class="header-desc">探索优质课程和学习资源，提升你的知识技能</view>
    </view>

    <!-- 搜索与筛选 -->
    <view class="filter-section">
      <view class="search-bar">
        <input
          type="text"
          v-model="searchQuery"
          placeholder="搜索课程"
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

    <!-- 课程列表 -->
    <view class="section">
      <view class="section-header">
        <text class="section-title">推荐课程</text>
        <text class="my-learning" @click="goMyLearning">我的学习 ></text>
      </view>

      <view class="course-list" v-if="courses.length > 0">
        <view
          class="course-card"
          v-for="course in courses"
          :key="course.id"
          @click="goCourseDetail(course.id)"
        >
          <image
            class="course-cover"
            :src="course.cover_image || defaultCover"
            mode="aspectFill"
          />
          <view class="course-info">
            <view class="course-title">{{ course.title }}</view>
            <view class="course-desc">{{ course.description?.substring(0, 50) }}...</view>
            <view class="course-meta">
              <text class="instructor">{{ course.instructor?.username }}</text>
              <text class="rating">★ {{ course.average_rating?.toFixed(1) || '0.0' }}</text>
            </view>
            <view class="course-footer">
              <text class="enroll-count">{{ course.enroll_count }} 人已报名</text>
              <text class="price" :class="{ free: course.is_free }">{{ course.is_free ? '免费' : '¥' + course.price }}</text>
            </view>
          </view>
        </view>

        <view class="load-more" v-if="loadingMore">加载中...</view>
        <view class="no-more" v-else-if="!hasMore">没有更多了</view>
      </view>

      <view class="empty-state" v-else-if="!loading">
        <text>暂无课程</text>
      </view>

      <view class="loading-state" v-if="loading && courses.length === 0">
        <text>加载中...</text>
      </view>
    </view>

    <!-- 学习资源 -->
    <view class="section resources-section">
      <view class="section-header">
        <text class="section-title">学习资源</text>
      </view>
      <view class="resource-list" v-if="resources.length > 0">
        <view
          class="resource-item"
          v-for="resource in resources"
          :key="resource.id"
          @click="downloadResource(resource)"
        >
          <text class="resource-icon">{{ getResourceIcon(resource.file_type) }}</text>
          <view class="resource-info">
            <view class="resource-title">{{ resource.title }}</view>
            <view class="resource-meta">{{ resource.file_type?.toUpperCase() }} · {{ formatFileSize(resource.file_size) }}</view>
          </view>
          <text class="download-icon">↓</text>
        </view>
      </view>
      <view class="empty-state" v-else-if="!resourceLoading">
        <text>暂无资源</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import learningApi from '../../api/learning'

const defaultCover = 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=campus%20online%20course%20cover%20image&image_size=landscape_16_9'

const courses = ref([])
const categories = ref([])
const categoryIndex = ref(0)
const resources = ref([])
const loading = ref(false)
const loadingMore = ref(false)
const resourceLoading = ref(false)
const searchQuery = ref('')
const ordering = ref('-created_at')
const page = ref(1)
const hasMore = ref(true)

const orderOptions = [
  { value: '-created_at', label: '最新发布' },
  { value: '-enroll_count', label: '最多报名' },
  { value: '-average_rating', label: '评分最高' }
]
const orderIndex = ref(0)

const categoryNames = computed(() => ['全部分类', ...categories.value.map(c => c.name)])

onMounted(() => {
  loadCategories()
  loadCourses()
  loadResources()
})

const loadCategories = async () => {
  try {
    const res = await learningApi.getCategories()
    categories.value = res.results || []
  } catch (error) {
    console.error('加载分类失败', error)
  }
}

const loadCourses = async (isRefresh = false) => {
  if (isRefresh) {
    page.value = 1
    courses.value = []
  }
  if (page.value === 1) {
    loading.value = true
  } else {
    loadingMore.value = true
  }

  try {
    const params = {
      page: page.value,
      ordering: ordering.value,
      is_published: true
    }
    if (searchQuery.value.trim()) {
      params.search = searchQuery.value.trim()
    }
    if (categoryIndex.value > 0) {
      params.categories = categories.value[categoryIndex.value - 1].id
    }

    const res = await learningApi.getCourses(params)
    const results = res.results || []
    if (page.value === 1) {
      courses.value = results
    } else {
      courses.value.push(...results)
    }
    hasMore.value = !!res.next
  } catch (error) {
    console.error('加载课程失败', error)
    uni.showToast({ title: '加载课程失败', icon: 'none' })
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

const loadResources = async () => {
  resourceLoading.value = true
  try {
    const res = await learningApi.getResources({ page: 1, page_size: 10 })
    resources.value = res.results || []
  } catch (error) {
    console.error('加载资源失败', error)
  } finally {
    resourceLoading.value = false
  }
}

const handleSearch = () => {
  loadCourses(true)
}

const onCategoryChange = (e) => {
  categoryIndex.value = Number(e.detail.value)
  loadCourses(true)
}

const onOrderChange = (e) => {
  orderIndex.value = Number(e.detail.value)
  ordering.value = orderOptions[orderIndex.value].value
  loadCourses(true)
}

const loadMore = () => {
  if (!hasMore.value || loadingMore.value) return
  page.value += 1
  loadCourses()
}

const goCourseDetail = (id) => {
  uni.navigateTo({ url: `/pages/course-detail/course-detail?id=${id}` })
}

const goMyLearning = () => {
  uni.navigateTo({ url: '/pages/my-learning/my-learning' })
}

const getResourceIcon = (fileType) => {
  const type = (fileType || '').toLowerCase()
  if (type.includes('pdf')) return '📄'
  if (type.includes('doc') || type.includes('word')) return '📝'
  if (type.includes('video')) return '🎥'
  if (type.includes('audio')) return '🎵'
  if (type.includes('zip') || type.includes('rar')) return '📦'
  return '📎'
}

const formatFileSize = (size) => {
  if (!size) return '未知大小'
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(2)} KB`
  if (size < 1024 * 1024 * 1024) return `${(size / (1024 * 1024)).toFixed(2)} MB`
  return `${(size / (1024 * 1024 * 1024)).toFixed(2)} GB`
}

const downloadResource = (resource) => {
  if (!resource.file_url) {
    uni.showToast({ title: '资源链接无效', icon: 'none' })
    return
  }
  learningApi.incrementResourceDownload(resource.id).catch(() => {})
  uni.downloadFile({
    url: resource.file_url,
    success: (res) => {
      if (res.statusCode === 200) {
        uni.openDocument({ filePath: res.tempFilePath })
      }
    },
    fail: () => {
      uni.showToast({ title: '下载失败', icon: 'none' })
    }
  })
}

// 下拉刷新
const onPullDownRefresh = async () => {
  await Promise.all([loadCourses(true), loadResources()])
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
  background: linear-gradient(135deg, #4361ee, #2980b9);
  color: #fff;
  padding: 60rpx 30rpx;
  text-align: center;
}

.header-title {
  font-size: 44rpx;
  font-weight: bold;
  margin-bottom: 12rpx;
}

.header-desc {
  font-size: 26rpx;
  opacity: 0.9;
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

.section {
  background-color: #fff;
  margin-bottom: 20rpx;
  padding: 30rpx;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24rpx;
}

.section-title {
  font-size: 34rpx;
  font-weight: 600;
  color: #333;
}

.my-learning {
  font-size: 26rpx;
  color: #4361ee;
}

.course-list {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.course-card {
  display: flex;
  gap: 20rpx;
  background-color: #f9f9f9;
  border-radius: 16rpx;
  padding: 20rpx;
}

.course-cover {
  width: 200rpx;
  height: 140rpx;
  border-radius: 12rpx;
  flex-shrink: 0;
}

.course-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.course-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 8rpx;
}

.course-desc {
  font-size: 24rpx;
  color: #666;
  line-height: 1.4;
  margin-bottom: 12rpx;
}

.course-meta {
  display: flex;
  justify-content: space-between;
  font-size: 24rpx;
  color: #999;
  margin-bottom: 12rpx;
}

.course-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.enroll-count {
  font-size: 24rpx;
  color: #999;
}

.price {
  font-size: 28rpx;
  font-weight: 600;
  color: #e74c3c;
}

.price.free {
  color: #27ae60;
}

.load-more,
.no-more {
  text-align: center;
  padding: 24rpx;
  font-size: 24rpx;
  color: #999;
}

.empty-state {
  text-align: center;
  padding: 80rpx 40rpx;
  color: #999;
  font-size: 28rpx;
}

.loading-state {
  text-align: center;
  padding: 80rpx;
  color: #999;
}

.resources-section {
  margin-bottom: 0;
}

.resource-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.resource-item {
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 20rpx;
  background-color: #f9f9f9;
  border-radius: 12rpx;
}

.resource-icon {
  font-size: 40rpx;
}

.resource-info {
  flex: 1;
}

.resource-title {
  font-size: 28rpx;
  color: #333;
  margin-bottom: 8rpx;
}

.resource-meta {
  font-size: 24rpx;
  color: #999;
}

.download-icon {
  font-size: 32rpx;
  color: #4361ee;
}
</style>
