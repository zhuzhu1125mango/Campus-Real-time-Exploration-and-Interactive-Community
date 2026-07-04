<template>
  <div class="my-learning-page">
    <div class="my-learning-header">
      <h1>我的学习</h1>
      <p>管理你的课程学习进度</p>
    </div>

    <div class="my-learning-body">
      <div v-if="loading" class="loading-state">
        <div class="loading-spinner"></div>
        <p>加载中...</p>
      </div>

      <template v-else>
        <div v-if="enrollments.length === 0" class="empty-state">
          <p>你还没有报名任何课程</p>
          <button class="btn btn-primary" @click="goLearning">去发现课程</button>
        </div>

        <div v-else class="enrollment-list">
          <div
            v-for="enrollment in enrollments"
            :key="enrollment.id"
            class="enrollment-card"
            @click="goCourse(enrollment.course.id)"
          >
            <img
              :src="enrollment.course.cover_image || defaultCover"
              :alt="enrollment.course.title"
              class="enrollment-cover"
            />
            <div class="enrollment-info">
              <h3 class="course-title">{{ enrollment.course.title }}</h3>
              <p class="course-desc">{{ enrollment.course.description.substring(0, 80) }}...</p>
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: `${enrollment.progress}%` }"></div>
              </div>
              <div class="progress-meta">
                <span>学习进度 {{ enrollment.progress.toFixed(0) }}%</span>
                <span v-if="enrollment.is_completed" class="completed-badge">已完成</span>
                <span v-else>学习中</span>
              </div>
            </div>
            <div class="enrollment-action">
              <button class="btn btn-primary" @click.stop="goCourse(enrollment.course.id)">
                {{ enrollment.is_completed ? '复习' : '继续学习' }}
              </button>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { learningApi } from '../api/learning'
import type { Enrollment } from '../types/learning'

const router = useRouter()

const enrollments = ref<Enrollment[]>([])
const loading = ref(false)
const defaultCover = 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=campus%20online%20course%20cover%20image&image_size=landscape_16_9'

const loadEnrollments = async () => {
  loading.value = true
  try {
    const response = await learningApi.getEnrollments()
    enrollments.value = response.results
  } catch (error: any) {
    const msg = error?.response?.data?.detail || '加载学习记录失败'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}

const goCourse = (courseId: number) => {
  router.push(`/learning/course/${courseId}`)
}

const goLearning = () => {
  router.push('/learning')
}

onMounted(() => {
  loadEnrollments()
})
</script>

<style scoped>
.my-learning-page {
  min-height: 100vh;
  background: #f5f7fa;
}

.my-learning-header {
  background: linear-gradient(135deg, #4361ee 0%, #3a56d4 100%);
  color: #fff;
  padding: 48px 24px;
  text-align: center;
}

.my-learning-header h1 {
  font-size: 32px;
  font-weight: 700;
  margin: 0 0 8px;
}

.my-learning-header p {
  font-size: 16px;
  opacity: 0.9;
  margin: 0;
}

.my-learning-body {
  max-width: 1000px;
  margin: 0 auto;
  padding: 32px 24px 60px;
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  color: #666;
}

.loading-spinner {
  width: 48px;
  height: 48px;
  border: 4px solid rgba(67, 97, 238, 0.2);
  border-top-color: #4361ee;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-state p {
  font-size: 16px;
  margin-bottom: 20px;
}

.btn {
  padding: 10px 24px;
  border-radius: 6px;
  border: none;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: #4361ee;
  color: #fff;
}

.btn-primary:hover {
  background: #3a56d4;
}

.enrollment-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.enrollment-card {
  display: flex;
  align-items: center;
  gap: 20px;
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  cursor: pointer;
  transition: all 0.2s;
}

.enrollment-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.enrollment-cover {
  width: 160px;
  aspect-ratio: 16 / 9;
  object-fit: cover;
  border-radius: 8px;
  flex-shrink: 0;
}

.enrollment-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.course-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin: 0;
}

.course-desc {
  font-size: 14px;
  color: #666;
  margin: 0;
  line-height: 1.4;
}

.progress-bar {
  height: 8px;
  background: #e8e8e8;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #4361ee;
  border-radius: 4px;
  transition: width 0.3s ease;
}

.progress-meta {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: #666;
}

.completed-badge {
  color: #27ae60;
  font-weight: 600;
}

.enrollment-action {
  flex-shrink: 0;
}

@media (max-width: 768px) {
  .enrollment-card {
    flex-direction: column;
    align-items: flex-start;
  }

  .enrollment-cover {
    width: 100%;
  }
}
</style>
