<template>
  <div class="course-list">
    <div class="course-list-header">
      <h2>{{ title }}</h2>
      <div class="course-list-filters">
        <select v-model="selectedCategory" @change="filterCourses">
          <option value="">所有分类</option>
          <option v-for="category in categories" :key="category.id" :value="category.id">
            {{ category.name }}
          </option>
        </select>
        <select v-model="selectedPrice" @change="filterCourses">
          <option value="">所有价格</option>
          <option value="free">免费</option>
          <option value="paid">付费</option>
        </select>
      </div>
    </div>
    <div class="course-grid">
      <div v-for="course in filteredCourses" :key="course.id" class="course-card">
        <div class="course-image">
          <img :src="course.cover_image || 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=campus%20online%20course%20cover%20image&image_size=square'" :alt="course.title">
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
            <button class="course-enroll" @click="enrollCourse(course.id)">
              {{ isEnrolled(course.id) ? '已报名' : '立即报名' }}
            </button>
          </div>
        </div>
      </div>
    </div>
    <div v-if="filteredCourses.length === 0" class="no-courses">
      暂无课程
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { learningApi } from '../api/learning'
import type { Course, Category } from '../types/learning'

const props = defineProps<{
  title?: string
}>()

const title = props.title || '课程列表'
const courses = ref<Course[]>([])
const categories = ref<Category[]>([])
const selectedCategory = ref('')
const selectedPrice = ref('')
const enrollments = ref<number[]>([])

const filteredCourses = computed(() => {
  let filtered = courses.value
  
  if (selectedCategory.value) {
    filtered = filtered.filter(course => 
      course.categories.some(category => category.id === Number(selectedCategory.value))
    )
  }
  
  if (selectedPrice.value === 'free') {
    filtered = filtered.filter(course => course.is_free)
  } else if (selectedPrice.value === 'paid') {
    filtered = filtered.filter(course => !course.is_free)
  }
  
  return filtered
})

const isEnrolled = (courseId: number) => {
  return enrollments.value.includes(courseId)
}

const filterCourses = () => {
  // 过滤逻辑已在computed中处理
}

const enrollCourse = async (courseId: number) => {
  try {
    await learningApi.enrollCourse(courseId)
    enrollments.value.push(courseId)
    alert('报名成功！')
  } catch (error) {
    console.error('报名失败:', error)
    alert('报名失败，请重试')
  }
}

const loadCourses = async () => {
  try {
    const response = await learningApi.getCourses()
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

const loadEnrollments = async () => {
  try {
    const response = await learningApi.getEnrollments()
    enrollments.value = response.results.map((enrollment: any) => enrollment.course.id)
  } catch (error) {
    console.error('加载报名信息失败:', error)
  }
}

onMounted(() => {
  loadCourses()
  loadCategories()
  loadEnrollments()
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

.course-list-filters select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
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