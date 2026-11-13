<template>
  <div class="course-list">
    <GlassCard :hover="false" class="filter-card" padding="md">
      <div class="filter-header">
        <h2 class="section-title">{{ title }}</h2>
        <span class="i-ep-filter filter-icon" />
      </div>

      <div class="course-filters">
        <div class="search-box">
          <span class="i-ep-search search-icon" />
          <input
            v-model="searchQuery"
            type="text"
            placeholder="搜索课程"
            class="search-input"
            @input="handleSearch"
          />
        </div>

        <div class="filter-selects">
          <select v-model="selectedCategory" @change="loadCourses">
            <option value="">所有分类</option>
            <option v-for="category in categories" :key="category.id" :value="category.id">
              {{ category.name }}
            </option>
          </select>

          <select v-model="selectedPrice" @change="loadCourses">
            <option value="">所有价格</option>
            <option value="true">免费</option>
            <option value="false">付费</option>
          </select>

          <select v-model="ordering" @change="loadCourses">
            <option value="-created_at">最新发布</option>
            <option value="-enroll_count">最多报名</option>
            <option value="-average_rating">评分最高</option>
            <option value="price">价格最低</option>
            <option value="-price">价格最高</option>
          </select>
        </div>
      </div>
    </GlassCard>

    <div v-if="loading" class="loading-state">
      <el-skeleton :rows="5" animated />
      <span>加载课程中...</span>
    </div>

    <div v-else-if="error" class="error-state">
      <el-alert :title="error" type="error" show-icon @close="error = null" />
      <button class="btn btn-secondary retry-button" @click="loadCourses">
        <span class="i-ep-refresh-right" />
        重新加载
      </button>
    </div>

    <div v-else-if="courses.length === 0" class="empty-state">
      <span class="i-ep-reading empty-icon" />
      <p class="empty-title">暂无课程</p>
      <p class="empty-desc">当前筛选条件下没有找到课程，试试其他条件吧</p>
      <button class="btn btn-secondary" @click="resetFilters">
        重置筛选条件
      </button>
    </div>

    <div v-else class="course-grid">
      <GlassCard
        v-for="course in courses"
        :key="course.id"
        :hover="true"
        padding="none"
        class="course-card"
        @click="goDetail(course.id)"
      >
        <div class="course-image">
          <img :src="course.cover_image || defaultCover" :alt="course.title">
        </div>
        <div class="course-content">
          <h3 class="course-title">{{ course.title }}</h3>
          <p class="course-description">{{ course.description.substring(0, 100) }}...</p>
          <div class="course-meta">
            <span class="course-instructor">
              <span class="i-ep-user meta-icon" />
              {{ course.instructor.username }}
            </span>
            <span class="course-rating">
              <span class="rating-stars">
                <span
                  v-for="i in 5"
                  :key="i"
                  class="i-ep-star star"
                  :class="{ 'filled': i <= Math.round(course.average_rating) }"
                />
              </span>
              <span class="rating-value">{{ course.average_rating.toFixed(1) }}</span>
            </span>
          </div>
          <div class="course-footer">
            <span class="course-price" :class="{ 'free': course.is_free }">
              {{ course.is_free ? '免费' : `¥${course.price}` }}
            </span>
            <button
              class="btn btn-primary course-enroll"
              :class="{ 'btn-secondary': course.is_enrolled }"
              @click.stop="enrollCourse(course)"
            >
              {{ course.is_enrolled ? '已报名' : '立即报名' }}
            </button>
          </div>
        </div>
      </GlassCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { learningApi } from '../api/learning'
import { getApiErrorMessage } from '../utils/error'
import { useUserStore } from '../stores/userStore'
import GlassCard from '../components/GlassCard.vue'
import type { Course, Category } from '../types/learning'

const props = defineProps<{
  title?: string
}>()

const router = useRouter()
const userStore = useUserStore()
const title = props.title || '课程列表'
const courses = ref<Course[]>([])
const categories = ref<Category[]>([])
const searchQuery = ref('')
const selectedCategory = ref('')
const selectedPrice = ref('')
const ordering = ref('-created_at')
const defaultCover = '/trae-api/api/ide/v1/text_to_image?prompt=campus%20online%20course%20cover%20image&image_size=square'
const loading = ref(false)
const error = ref<string | null>(null)

let searchTimer: ReturnType<typeof setTimeout> | null = null

const handleSearch = () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    loadCourses()
  }, 300)
}

const resetFilters = () => {
  searchQuery.value = ''
  selectedCategory.value = ''
  selectedPrice.value = ''
  ordering.value = '-created_at'
  loadCourses()
}

const goDetail = (courseId: number) => {
  router.push(`/learning/course/${courseId}`)
}

const enrollCourse = async (course: Course) => {
  if (course.is_enrolled) {
    goDetail(course.id)
    return
  }
  if (!userStore.isLoggedIn) {
    router.push(`/login?redirect=${encodeURIComponent(`/learning/course/${course.id}`)}`)
    return
  }
  try {
    await learningApi.enrollCourse(course.id)
    course.is_enrolled = true
    course.enroll_count += 1
    ElMessage.success('报名成功！')
    goDetail(course.id)
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '报名失败'))
  }
}

const loadCourses = async () => {
  loading.value = true
  error.value = null
  try {
    const params: any = { ordering: ordering.value }
    if (selectedCategory.value) {
      params.category = selectedCategory.value
    }
    if (selectedPrice.value !== '') {
      params.is_free = selectedPrice.value
    }
    if (searchQuery.value.trim()) {
      params.search = searchQuery.value.trim()
    }
    const response = await learningApi.getCourses(params)
    courses.value = response.results
  } catch (err) {
    console.error('加载课程失败:', err)
    error.value = '加载课程失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

const loadCategories = async () => {
  try {
    const response = await learningApi.getCategories()
    categories.value = response.results
  } catch (error) {
    console.error('加载分类失败:', error)
  }
}

onMounted(() => {
  loadCourses()
  loadCategories()
})
</script>

<style scoped>
.course-list {
  width: 100%;
}

.filter-card {
  margin-bottom: var(--space-6);
}

.filter-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-5);
}

.section-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text-primary);
}

.filter-icon {
  width: 20px;
  height: 20px;
  color: var(--primary-600);
}

.course-filters {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-4);
}

.search-box {
  position: relative;
  flex: 1;
  min-width: 220px;
  max-width: 360px;
}

.search-icon {
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
  width: 18px;
  height: 18px;
  color: var(--text-tertiary);
  pointer-events: none;
}

.search-input {
  width: 100%;
  padding: 10px 14px 10px 42px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  font-size: 0.95rem;
  color: var(--text-primary);
  background: var(--bg-primary);
  transition: all 0.2s ease;
}

.search-input:focus {
  outline: none;
  border-color: var(--primary-400);
  box-shadow: 0 0 0 3px var(--primary-100);
}

.filter-selects {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-3);
}

.filter-selects select {
  min-width: 140px;
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  font-size: 0.95rem;
  color: var(--text-primary);
  background: var(--bg-primary);
  transition: all 0.2s ease;
  cursor: pointer;
}

.filter-selects select:focus {
  outline: none;
  border-color: var(--primary-400);
  box-shadow: 0 0 0 3px var(--primary-100);
}

.loading-state {
  text-align: center;
  padding: var(--space-10);
  color: var(--text-secondary);
}

.loading-state span {
  display: block;
  margin-top: var(--space-4);
}

.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-8);
  text-align: center;
}

.retry-button {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-12);
  text-align: center;
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-card);
  backdrop-filter: blur(12px) saturate(180%);
  -webkit-backdrop-filter: blur(12px) saturate(180%);
}

.empty-icon {
  width: 64px;
  height: 64px;
  color: var(--primary-400);
  margin-bottom: var(--space-4);
}

.empty-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--space-2);
}

.empty-desc {
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin-bottom: var(--space-5);
}

.course-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: var(--space-5);
}

.course-card {
  overflow: hidden;
  cursor: pointer;
}

.course-image {
  height: 180px;
  overflow: hidden;
}

.course-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.course-card:hover .course-image img {
  transform: scale(1.05);
}

.course-content {
  padding: var(--space-5);
}

.course-title {
  font-size: 1.125rem;
  font-weight: 700;
  margin-bottom: var(--space-2);
  color: var(--text-primary);
  line-height: 1.4;
}

.course-description {
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin-bottom: var(--space-4);
  line-height: 1.5;
}

.course-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-4);
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.course-instructor {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  font-weight: 500;
}

.meta-icon {
  width: 16px;
  height: 16px;
  color: var(--text-tertiary);
}

.course-rating {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.rating-stars {
  display: flex;
  gap: 2px;
}

.star {
  width: 16px;
  height: 16px;
  color: var(--border-color);
}

.star.filled {
  color: var(--warning-color);
}

.rating-value {
  font-weight: 600;
  color: var(--text-primary);
}

.course-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: var(--space-4);
  padding-top: var(--space-4);
  border-top: 1px solid var(--border-color-light);
}

.course-price {
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--error-color);
}

.course-price.free {
  color: var(--success-color);
}

.course-enroll {
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: 0.625rem 1.25rem;
  border-radius: var(--radius-md);
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: all 0.2s ease;
}

.btn-primary {
  background-color: var(--primary-600);
  color: white;
}

.btn-primary:hover:not(:disabled) {
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
  opacity: 0.6;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .course-filters {
    flex-direction: column;
    align-items: stretch;
  }

  .search-box {
    max-width: none;
  }

  .filter-selects {
    width: 100%;
  }

  .filter-selects select {
    flex: 1;
    min-width: 0;
  }

  .course-grid {
    grid-template-columns: 1fr;
  }

  .course-meta {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-2);
  }
}
</style>
