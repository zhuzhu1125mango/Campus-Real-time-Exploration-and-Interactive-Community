<template>
  <div class="course-list">
    <div class="course-list-header">
      <h2>{{ title }}</h2>
      <div class="course-list-filters">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="搜索课程"
          class="search-input"
          @input="handleSearch"
        />
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
    <div class="course-grid">
      <div
        v-for="course in courses"
        :key="course.id"
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
            <span class="course-instructor">{{ course.instructor.username }}</span>
            <span class="course-rating">
              <span class="rating-stars">
                <span v-for="i in 5" :key="i" class="star" :class="{ 'filled': i <= Math.round(course.average_rating) }">
                  ★
                </span>
              </span>
              <span class="rating-value">{{ course.average_rating.toFixed(1) }}</span>
            </span>
          </div>
          <div class="course-footer">
            <span class="course-price">
              {{ course.is_free ? '免费' : `¥${course.price}` }}
            </span>
            <button class="course-enroll" @click.stop="enrollCourse(course)">
              {{ course.is_enrolled ? '已报名' : '立即报名' }}
            </button>
          </div>
        </div>
      </div>
    </div>
    <div v-if="courses.length === 0" class="no-courses">
      暂无课程
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { learningApi } from '../api/learning'
import { useUserStore } from '../stores/userStore'
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
const defaultCover = 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=campus%20online%20course%20cover%20image&image_size=square'

let searchTimer: ReturnType<typeof setTimeout> | null = null

const handleSearch = () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    loadCourses()
  }, 300)
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
  } catch (error: any) {
    const msg = error?.response?.data?.detail || error?.response?.data?.non_field_errors?.[0] || '报名失败'
    ElMessage.error(msg)
  }
}

const loadCourses = async () => {
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
  } catch (error) {
    console.error('加载课程失败:', error)
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
  padding: 20px;
}

.course-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.course-list-header h2 {
  font-size: 24px;
  font-weight: bold;
  color: #333;
}

.course-list-filters {
  display: flex;
  gap: 10px;
}

.course-list-filters select,
.course-list-filters .search-input {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.course-list-filters .search-input {
  width: 180px;
}

.course-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.course-card {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  transition: transform 0.3s ease;
  cursor: pointer;
}

.course-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.course-image {
  height: 180px;
  overflow: hidden;
}

.course-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.course-content {
  padding: 16px;
}

.course-title {
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 8px;
  color: #333;
}

.course-description {
  font-size: 14px;
  color: #666;
  margin-bottom: 12px;
  line-height: 1.4;
}

.course-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-size: 14px;
  color: #888;
}

.course-instructor {
  font-weight: 500;
}

.course-rating {
  display: flex;
  align-items: center;
  gap: 5px;
}

.rating-stars {
  display: flex;
  gap: 2px;
}

.star {
  color: #ddd;
  font-size: 14px;
}

.star.filled {
  color: #ffc107;
}

.rating-value {
  font-weight: 500;
  color: #333;
}

.course-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
}

.course-price {
  font-size: 18px;
  font-weight: bold;
  color: #e74c3c;
}

.course-enroll {
  padding: 8px 16px;
  background: #3498db;
  color: #fff;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.3s ease;
}

.course-enroll:hover {
  background: #2980b9;
}

.course-enroll:disabled {
  background: #95a5a6;
  cursor: not-allowed;
}

.no-courses {
  text-align: center;
  padding: 40px;
  color: #999;
  font-size: 16px;
}

@media (max-width: 768px) {
  .course-list-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .course-list-filters {
    width: 100%;
  }
  
  .course-list-filters select {
    flex: 1;
  }
  
  .course-grid {
    grid-template-columns: 1fr;
  }
}
</style>