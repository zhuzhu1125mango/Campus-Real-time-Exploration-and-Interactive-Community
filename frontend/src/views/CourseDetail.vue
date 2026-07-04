<template>
  <div class="course-detail-page">
    <div v-if="loading" class="loading-state">
      <div class="loading-spinner"></div>
      <p>加载课程中...</p>
    </div>

    <template v-else-if="course">
      <!-- 课程头部 -->
      <div class="course-hero">
        <div class="course-hero-inner">
          <img
            :src="course.cover_image || defaultCover"
            :alt="course.title"
            class="course-cover"
          />
          <div class="course-info">
            <div class="course-badges">
              <span v-for="cat in course.categories" :key="cat.id" class="badge">{{ cat.name }}</span>
              <span v-if="course.is_free" class="badge badge-free">免费</span>
              <span v-else class="badge badge-paid">付费</span>
            </div>
            <h1 class="course-title">{{ course.title }}</h1>
            <p class="course-description">{{ course.description }}</p>
            <div class="course-meta">
              <span class="meta-item">
                <span class="meta-label">讲师</span>
                <span class="meta-value">{{ course.instructor.username }}</span>
              </span>
              <span class="meta-item">
                <span class="meta-label">评分</span>
                <span class="meta-value">
                  <span class="stars">
                    <span v-for="i in 5" :key="i" class="star" :class="{ filled: i <= Math.round(course.average_rating) }">★</span>
                  </span>
                  {{ course.average_rating.toFixed(1) }}
                </span>
              </span>
              <span class="meta-item">
                <span class="meta-label">报名</span>
                <span class="meta-value">{{ course.enroll_count }} 人</span>
              </span>
              <span class="meta-item">
                <span class="meta-label">课时</span>
                <span class="meta-value">{{ course.lesson_count }} 节</span>
              </span>
            </div>
            <div class="course-actions">
              <template v-if="!userStore.isLoggedIn">
                <button class="btn btn-primary" @click="goLogin">登录后报名</button>
              </template>
              <template v-else-if="course.is_enrolled">
                <button class="btn btn-primary" @click="startLearning">继续学习</button>
              </template>
              <template v-else>
                <button class="btn btn-primary" :disabled="enrolling" @click="enroll">
                  {{ enrolling ? '报名中...' : '立即报名' }}
                </button>
              </template>
              <span v-if="!course.is_free" class="course-price">¥{{ course.price }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 内容区 -->
      <div class="course-body">
        <div class="course-main">
          <!-- 章节 -->
          <section class="section chapters-section">
            <h2 class="section-title">课程章节</h2>
            <div v-if="chapters.length === 0" class="empty-state">暂无章节</div>
            <div v-else class="chapter-list">
              <div
                v-for="chapter in chapters"
                :key="chapter.id"
                class="chapter-card"
              >
                <div class="chapter-header" @click="toggleChapter(chapter.id)">
                  <div class="chapter-title-wrap">
                    <span class="chapter-toggle">{{ isExpanded(chapter.id) ? '▼' : '▶' }}</span>
                    <h3 class="chapter-title">{{ chapter.title }}</h3>
                  </div>
                  <span class="chapter-count">{{ chapter.lesson_count }} 课时</span>
                </div>
                <div v-show="isExpanded(chapter.id)" class="lesson-list">
                  <div
                    v-for="lesson in chapter.lessons"
                    :key="lesson.id"
                    class="lesson-item"
                    :class="{ locked: !canWatchLesson(lesson) }"
                    @click="openLesson(lesson)"
                  >
                    <span class="lesson-icon">▶</span>
                    <span class="lesson-title">{{ lesson.title }}</span>
                    <span v-if="lesson.is_free" class="tag tag-free">免费</span>
                    <span v-else-if="!course.is_enrolled" class="tag tag-lock">锁定</span>
                    <span v-if="lesson.duration" class="lesson-duration">{{ formatDuration(lesson.duration) }}</span>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <!-- 资源 -->
          <section class="section resources-section">
            <h2 class="section-title">课程资源</h2>
            <div v-if="resources.length === 0" class="empty-state">暂无资源</div>
            <div v-else class="resource-list">
              <div v-for="resource in resources" :key="resource.id" class="resource-item">
                <div class="resource-info">
                  <span class="resource-icon">{{ getResourceIcon(resource.file_type) }}</span>
                  <div class="resource-text">
                    <h4>{{ resource.title }}</h4>
                    <p>{{ resource.description || '无描述' }}</p>
                    <span class="resource-meta">{{ resource.file_type.toUpperCase() }} · {{ formatFileSize(resource.file_size) }} · {{ resource.download_count }} 次下载</span>
                  </div>
                </div>
                <button class="btn btn-secondary" @click="downloadResource(resource)">下载</button>
              </div>
            </div>
          </section>

          <!-- 评价 -->
          <section class="section reviews-section">
            <h2 class="section-title">学员评价</h2>
            <div v-if="reviews.length === 0" class="empty-state">暂无评价</div>
            <div v-else class="review-list">
              <div v-for="review in reviews" :key="review.id" class="review-item">
                <div class="review-header">
                  <span class="review-user">{{ review.user.username }}</span>
                  <span class="review-rating">
                    <span v-for="i in 5" :key="i" class="star" :class="{ filled: i <= review.rating }">★</span>
                  </span>
                  <span class="review-time">{{ formatDate(review.created_at) }}</span>
                </div>
                <p class="review-comment">{{ review.comment }}</p>
              </div>
            </div>
          </section>
        </div>
      </div>
    </template>

    <div v-else class="error-state">
      <p>课程加载失败，请稍后重试</p>
      <button class="btn btn-primary" @click="loadCourse">重新加载</button>
    </div>

    <LessonPlayer
      v-model:visible="playerVisible"
      :lesson="currentLesson"
      :course="course"
      :enrollment="enrollment"
      @complete="handleLessonComplete"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../stores/userStore'
import { learningApi } from '../api/learning'
import { formatDate } from '../utils/date'
import LessonPlayer from '../components/LessonPlayer.vue'
import type { Course, Chapter, Lesson, LearningResource, Review, Enrollment } from '../types/learning'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const defaultCover = 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=campus%20online%20course%20cover%20image&image_size=landscape_16_9'

const course = ref<Course | null>(null)
const chapters = ref<Chapter[]>([])
const resources = ref<LearningResource[]>([])
const reviews = ref<Review[]>([])
const enrollment = ref<Enrollment | null>(null)
const loading = ref(false)
const enrolling = ref(false)
const expandedChapters = ref<number[]>([])
const playerVisible = ref(false)
const currentLesson = ref<Lesson | null>(null)

const courseId = Number(route.params.courseId)

const loadCourse = async () => {
  if (isNaN(courseId) || courseId <= 0) {
    ElMessage.error('无效的课程ID')
    router.replace('/learning')
    return
  }

  loading.value = true
  try {
    const requests: any[] = [
      learningApi.getCourseDetail(courseId),
      learningApi.getCourseChapters(courseId),
      learningApi.getCourseResources(courseId),
      learningApi.getCourseReviews(courseId)
    ]
    if (userStore.isLoggedIn) {
      requests.push(learningApi.getEnrollments({ course: courseId }))
    }

    const [courseRes, chaptersRes, resourcesRes, reviewsRes, enrollmentRes] = await Promise.all(requests)

    course.value = courseRes
    chapters.value = chaptersRes.results.sort((a: Chapter, b: Chapter) => a.order - b.order)
    resources.value = resourcesRes.results
    reviews.value = reviewsRes.results
    if (enrollmentRes && enrollmentRes.results.length > 0) {
      enrollment.value = enrollmentRes.results[0]
    }

    // 默认展开第一个章节
    if (chapters.value.length > 0) {
      expandedChapters.value = [chapters.value[0].id]
    }
  } catch (error: any) {
    const msg = error?.response?.data?.detail || '课程加载失败'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}

const toggleChapter = (chapterId: number) => {
  const index = expandedChapters.value.indexOf(chapterId)
  if (index === -1) {
    expandedChapters.value.push(chapterId)
  } else {
    expandedChapters.value.splice(index, 1)
  }
}

const isExpanded = (chapterId: number) => expandedChapters.value.includes(chapterId)

const canWatchLesson = (lesson: Lesson) => {
  return lesson.is_free || course.value?.is_enrolled
}

const openLesson = (lesson: Lesson) => {
  if (!canWatchLesson(lesson)) {
    ElMessage.warning('报名课程后即可学习该课时')
    return
  }
  currentLesson.value = lesson
  playerVisible.value = true
}

const startLearning = () => {
  // 自动定位到第一个未锁定课时
  for (const chapter of chapters.value) {
    for (const lesson of chapter.lessons) {
      if (canWatchLesson(lesson)) {
        openLesson(lesson)
        return
      }
    }
  }
  ElMessage.info('暂无可学习课时')
}

const goLogin = () => {
  router.push(`/login?redirect=${encodeURIComponent(route.fullPath)}`)
}

const enroll = async () => {
  if (!userStore.isLoggedIn) {
    goLogin()
    return
  }
  enrolling.value = true
  try {
    await learningApi.enrollCourse(courseId)
    if (course.value) {
      course.value.is_enrolled = true
      course.value.enroll_count += 1
    }
    ElMessage.success('报名成功，开始学习吧！')
  } catch (error: any) {
    const msg = error?.response?.data?.detail || error?.response?.data?.non_field_errors?.[0] || '报名失败'
    ElMessage.error(msg)
  } finally {
    enrolling.value = false
  }
}

const handleLessonComplete = () => {
  // 课时学习完成后的回调，可刷新学习进度
}

const downloadResource = (resource: LearningResource) => {
  learningApi.incrementResourceDownload(resource.id).catch(() => {})
  const url = typeof resource.file_url === 'string' ? resource.file_url : ''
  if (!url) {
    ElMessage.warning('资源链接无效')
    return
  }
  const link = document.createElement('a')
  link.href = url
  link.download = resource.title
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

const formatDuration = (duration: string | null): string => {
  if (!duration) return ''
  // duration 可能为 HH:MM:SS 或 ISO 8601 格式
  const parts = duration.split(':')
  if (parts.length === 3) {
    const [h, m, s] = parts
    return `${Number(h)}:${m}:${s}`
  }
  return duration
}

const formatFileSize = (size: number): string => {
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(2)} KB`
  if (size < 1024 * 1024 * 1024) return `${(size / (1024 * 1024)).toFixed(2)} MB`
  return `${(size / (1024 * 1024 * 1024)).toFixed(2)} GB`
}

const getResourceIcon = (fileType: string): string => {
  const type = fileType.toLowerCase()
  if (type.includes('pdf')) return '📄'
  if (type.includes('doc') || type.includes('word')) return '📝'
  if (type.includes('video')) return '🎥'
  if (type.includes('audio')) return '🎵'
  if (type.includes('zip') || type.includes('rar')) return '📦'
  return '📎'
}

onMounted(() => {
  loadCourse()
})
</script>

<style scoped>
.course-detail-page {
  min-height: 100vh;
  background: #f5f7fa;
}

.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
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

.course-hero {
  background: linear-gradient(135deg, #4361ee 0%, #3a56d4 100%);
  color: #fff;
  padding: 48px 24px;
}

.course-hero-inner {
  max-width: 1200px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 360px 1fr;
  gap: 40px;
  align-items: start;
}

.course-cover {
  width: 100%;
  aspect-ratio: 16 / 9;
  object-fit: cover;
  border-radius: 12px;
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.2);
}

.course-info {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.course-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.badge {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
  background: rgba(255, 255, 255, 0.2);
}

.badge-free {
  background: #27ae60;
}

.badge-paid {
  background: #e74c3c;
}

.course-title {
  font-size: 32px;
  font-weight: 700;
  line-height: 1.2;
  margin: 0;
}

.course-description {
  font-size: 16px;
  line-height: 1.6;
  opacity: 0.9;
  margin: 0;
}

.course-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 24px;
}

.meta-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.meta-label {
  font-size: 12px;
  opacity: 0.7;
}

.meta-value {
  font-size: 15px;
  font-weight: 500;
}

.stars {
  display: inline-flex;
  gap: 2px;
}

.star {
  color: rgba(255, 255, 255, 0.4);
  font-size: 14px;
}

.star.filled {
  color: #ffc107;
}

.course-actions {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-top: 8px;
}

.btn {
  padding: 12px 28px;
  border-radius: 8px;
  border: none;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.btn-primary {
  background: #fff;
  color: #4361ee;
}

.btn-primary:hover:not(:disabled) {
  background: #f0f3ff;
  transform: translateY(-1px);
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.15);
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.25);
}

.course-price {
  font-size: 24px;
  font-weight: 700;
}

.course-body {
  max-width: 1200px;
  margin: 0 auto;
  padding: 32px 24px 60px;
}

.course-main {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.section {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.section-title {
  font-size: 20px;
  font-weight: 700;
  color: #333;
  margin: 0 0 20px;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #999;
}

.chapter-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.chapter-card {
  border: 1px solid #e8e8e8;
  border-radius: 10px;
  overflow: hidden;
}

.chapter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: #f9fafc;
  cursor: pointer;
  transition: background 0.2s;
}

.chapter-header:hover {
  background: #f0f3ff;
}

.chapter-title-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
}

.chapter-toggle {
  font-size: 12px;
  color: #666;
}

.chapter-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin: 0;
}

.chapter-count {
  font-size: 13px;
  color: #888;
}

.lesson-list {
  padding: 8px 20px;
}

.lesson-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  transition: color 0.2s;
}

.lesson-item:last-child {
  border-bottom: none;
}

.lesson-item:hover:not(.locked) {
  color: #4361ee;
}

.lesson-item.locked {
  color: #999;
  cursor: not-allowed;
}

.lesson-icon {
  font-size: 12px;
  color: #4361ee;
}

.lesson-item.locked .lesson-icon {
  color: #bbb;
}

.lesson-title {
  flex: 1;
  font-size: 14px;
}

.tag {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.tag-free {
  background: #e8f8ef;
  color: #27ae60;
}

.tag-lock {
  background: #f2f2f2;
  color: #888;
}

.lesson-duration {
  font-size: 12px;
  color: #888;
}

.resource-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.resource-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
}

.resource-info {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.resource-icon {
  font-size: 24px;
}

.resource-text h4 {
  font-size: 15px;
  font-weight: 600;
  color: #333;
  margin: 0 0 4px;
}

.resource-text p {
  font-size: 13px;
  color: #666;
  margin: 0 0 6px;
}

.resource-meta {
  font-size: 12px;
  color: #999;
}

.review-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.review-item {
  padding: 16px;
  background: #f9fafc;
  border-radius: 8px;
}

.review-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.review-user {
  font-weight: 600;
  color: #333;
}

.review-rating .star {
  color: #ddd;
}

.review-rating .star.filled {
  color: #ffc107;
}

.review-time {
  font-size: 12px;
  color: #999;
  margin-left: auto;
}

.review-comment {
  font-size: 14px;
  color: #555;
  margin: 0;
  line-height: 1.5;
}

@media (max-width: 768px) {
  .course-hero-inner {
    grid-template-columns: 1fr;
  }

  .course-title {
    font-size: 24px;
  }

  .course-meta {
    gap: 16px;
  }

  .resource-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
}
</style>
