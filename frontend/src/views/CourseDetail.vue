<template>
  <div class="course-detail-page container-wide page-padding">
    <div v-if="loading" class="loading-state">
      <div class="loading-spinner"></div>
      <p>加载课程中...</p>
    </div>

    <template v-else-if="course">
      <SectionHeader
        :title="course.title"
        :subtitle="(course.categories.map(c => c.name).join(' / ') || '课程') + ' · 讲师 ' + course.instructor.username"
        icon="i-ep-reading"
      />

      <div class="course-layout">
        <aside class="course-sidebar">
          <GlassCard :hover="false" padding="none" class="course-info-card">
            <img
              :src="course.cover_image || defaultCover"
              :alt="course.title"
              class="course-cover"
            />
            <div class="course-info-body">
              <div class="course-badges">
                <span v-for="cat in course.categories" :key="cat.id" class="badge badge-category">{{ cat.name }}</span>
                <span v-if="course.is_free" class="badge badge-free">免费</span>
                <span v-else class="badge badge-paid">付费</span>
              </div>
              <p class="course-description">{{ course.description }}</p>
              <div class="course-meta">
                <div class="meta-item">
                  <span class="i-ep-user meta-icon" />
                  <span class="meta-label">讲师</span>
                  <span class="meta-value">{{ course.instructor.username }}</span>
                </div>
                <div class="meta-item">
                  <span class="i-ep-star meta-icon" />
                  <span class="meta-label">评分</span>
                  <span class="meta-value">
                    <span class="stars">
                      <span v-for="i in 5" :key="i" class="i-ep-star star" :class="{ filled: i <= Math.round(course.average_rating) }" />
                    </span>
                    {{ course.average_rating.toFixed(1) }}
                  </span>
                </div>
                <div class="meta-item">
                  <span class="i-ep-check meta-icon" />
                  <span class="meta-label">报名</span>
                  <span class="meta-value">{{ course.enroll_count }} 人</span>
                </div>
                <div class="meta-item">
                  <span class="i-ep-video-play meta-icon" />
                  <span class="meta-label">课时</span>
                  <span class="meta-value">{{ course.lesson_count }} 节</span>
                </div>
              </div>
              <div class="course-actions">
                <template v-if="!userStore.isLoggedIn">
                  <button class="btn btn-primary" @click="goLogin">登录后报名</button>
                </template>
                <template v-else-if="course.is_enrolled">
                  <button class="btn btn-primary" @click="startLearning">继续学习</button>
                  <button v-if="certificate" class="btn btn-secondary" @click="goCertificate">
                    <span class="i-ep-medal" />
                    查看证书
                  </button>
                </template>
                <template v-else>
                  <button
                    v-if="course.is_free"
                    class="btn btn-primary"
                    :disabled="enrolling"
                    @click="enroll"
                  >
                    {{ enrolling ? '报名中...' : '立即报名' }}
                  </button>
                  <button
                    v-else
                    class="btn btn-primary"
                    :disabled="purchasing"
                    @click="purchase"
                  >
                    {{ purchasing ? '支付中...' : '购买课程' }}
                  </button>
                </template>
                <span v-if="!course.is_free" class="course-price">¥{{ course.price }}</span>
              </div>
            </div>
          </GlassCard>
        </aside>

        <main class="course-main">
          <GlassCard :hover="false" title="课程章节" class="chapters-card">
            <div v-if="chapters.length === 0" class="empty-state">暂无章节</div>
            <div v-else class="chapter-list">
              <div
                v-for="chapter in chapters"
                :key="chapter.id"
                class="chapter-card"
              >
                <div class="chapter-header" @click="toggleChapter(chapter.id)">
                  <div class="chapter-title-wrap">
                    <span class="chapter-toggle" :class="isExpanded(chapter.id) ? 'i-ep-arrow-down' : 'i-ep-arrow-right'" />
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
                    <span class="lesson-icon" :class="canWatchLesson(lesson) ? 'i-ep-video-play' : 'i-ep-lock'" />
                    <span class="lesson-title">{{ lesson.title }}</span>
                    <span v-if="lesson.is_free" class="tag tag-free">免费</span>
                    <span v-else-if="!course.is_enrolled" class="tag tag-lock">锁定</span>
                    <span v-if="lesson.duration" class="lesson-duration">{{ formatDuration(lesson.duration) }}</span>
                  </div>
                </div>
              </div>
            </div>
          </GlassCard>

          <GlassCard :hover="false" title="课程资源" class="resources-card">
            <div v-if="resources.length === 0" class="empty-state">暂无资源</div>
            <div v-else class="resource-list">
              <div v-for="resource in resources" :key="resource.id" class="resource-item">
                <div class="resource-info">
                  <span class="resource-icon i-ep-document" />
                  <div class="resource-text">
                    <h4>{{ resource.title }}</h4>
                    <p>{{ resource.description || '无描述' }}</p>
                    <span class="resource-meta">{{ resource.file_type.toUpperCase() }} · {{ formatFileSize(resource.file_size) }} · {{ resource.download_count }} 次下载</span>
                  </div>
                </div>
                <button class="btn btn-secondary" @click="downloadResource(resource)">
                  <span class="i-ep-download" />
                  下载
                </button>
              </div>
            </div>
          </GlassCard>

          <GlassCard :hover="false" title="学员评价" class="reviews-card">
            <div v-if="reviews.length === 0" class="empty-state">暂无评价</div>
            <div v-else class="review-list">
              <div v-for="review in reviews" :key="review.id" class="review-item">
                <div class="review-header">
                  <span class="i-ep-user review-user-icon" />
                  <span class="review-user">{{ review.user.username }}</span>
                  <span class="review-rating">
                    <span v-for="i in 5" :key="i" class="i-ep-star star" :class="{ filled: i <= review.rating }" />
                  </span>
                  <span class="review-time">{{ formatDate(review.created_at) }}</span>
                </div>
                <p class="review-comment">{{ review.comment }}</p>
              </div>
            </div>
          </GlassCard>
        </main>
      </div>
    </template>

    <div v-else class="error-state">
      <span class="i-ep-warning error-icon" />
      <p>课程加载失败，请稍后重试</p>
      <button class="btn btn-primary" @click="loadCourse">重新加载</button>
    </div>

    <LessonPlayer
      v-model:visible="playerVisible"
      :lesson="currentLesson"
      :course="course"
      :enrollment="enrollment"
      @complete="handleLessonComplete"
      @next="openNextLesson"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '../stores/userStore'
import { learningApi } from '../api/learning'
import { formatDate } from '../utils/date'
import { getApiErrorMessage } from '../utils/error'
import LessonPlayer from '../components/LessonPlayer.vue'
import GlassCard from '@/components/GlassCard.vue'
import SectionHeader from '@/components/SectionHeader.vue'
import type { Course, Chapter, Lesson, LearningResource, Review, Enrollment, Certificate } from '../types/learning'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const defaultCover = '/trae-api/api/ide/v1/text_to_image?prompt=campus%20online%20course%20cover%20image&image_size=landscape_16_9'

const course = ref<Course | null>(null)
const chapters = ref<Chapter[]>([])
const resources = ref<LearningResource[]>([])
const reviews = ref<Review[]>([])
const enrollment = ref<Enrollment | null>(null)
const certificate = ref<Certificate | null>(null)
const loading = ref(false)
const enrolling = ref(false)
const purchasing = ref(false)
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
    const chapterList = Array.isArray(chaptersRes) ? chaptersRes : chaptersRes.results
    chapters.value = chapterList.sort((a: Chapter, b: Chapter) => a.order - b.order)
    resources.value = Array.isArray(resourcesRes) ? resourcesRes : resourcesRes.results
    reviews.value = Array.isArray(reviewsRes) ? reviewsRes : reviewsRes.results
    if (enrollmentRes && enrollmentRes.results.length > 0) {
      enrollment.value = enrollmentRes.results[0]
    }
    if (enrollment.value?.is_completed) {
      loadCertificate()
    }

    // 默认展开第一个章节
    if (chapters.value.length > 0) {
      expandedChapters.value = [chapters.value[0].id]
    }
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '课程加载失败'))
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
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '报名失败'))
  } finally {
    enrolling.value = false
  }
}

const handleLessonComplete = () => {
  // 课时学习完成后的回调，可刷新学习进度
}

const purchase = async () => {
  if (!userStore.isLoggedIn) {
    goLogin()
    return
  }
  if (!course.value) return

  try {
    await ElMessageBox.confirm(
      `确认支付 ¥${course.value.price} 购买《${course.value.title}》？当前为模拟支付，不会产生真实扣款。`,
      '确认支付',
      { confirmButtonText: '确认支付', cancelButtonText: '取消', type: 'warning' }
    )
  } catch {
    return
  }

  purchasing.value = true
  try {
    const order = await learningApi.createPaymentOrder(courseId)
    await learningApi.payOrder(order.id)
    ElMessage.success('支付成功，已加入学习')
    await loadCourse()
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '支付失败，请稍后重试'))
  } finally {
    purchasing.value = false
  }
}

const loadCertificate = async () => {
  try {
    const response = await learningApi.getCertificates({ course: courseId })
    certificate.value = response.results?.[0] || null
  } catch {
    certificate.value = null
  }
}

const goCertificate = () => {
  if (certificate.value) {
    router.push(`/certificate/${certificate.value.id}`)
  }
}

const openNextLesson = () => {
  if (!currentLesson.value) return
  const allLessons: Lesson[] = []
  for (const chapter of chapters.value) {
    for (const lesson of chapter.lessons) {
      allLessons.push(lesson)
    }
  }
  const currentIndex = allLessons.findIndex(l => l.id === currentLesson.value?.id)
  const nextLesson = allLessons[currentIndex + 1]
  if (nextLesson && canWatchLesson(nextLesson)) {
    currentLesson.value = nextLesson
  } else if (nextLesson) {
    ElMessage.info('已学完当前课时，后续课时需要报名后继续学习')
  } else {
    ElMessage.success('恭喜，已完成本课程所有课时')
  }
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

onMounted(() => {
  loadCourse()
})
</script>

<style scoped>
.course-detail-page {
  min-height: calc(100vh - 200px);
}

.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-12) 0;
  text-align: center;
  color: var(--text-secondary);
  gap: var(--space-3);
}

.loading-spinner {
  width: 48px;
  height: 48px;
  border: 4px solid var(--primary-200);
  border-top-color: var(--primary-600);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-icon {
  font-size: 2.5rem;
  color: var(--warning-color);
}

.course-layout {
  display: grid;
  grid-template-columns: 340px 1fr;
  gap: var(--space-6);
  align-items: start;
}

.course-info-card {
  overflow: hidden;
}

.course-cover {
  width: 100%;
  aspect-ratio: 16 / 9;
  object-fit: cover;
  display: block;
}

.course-info-body {
  padding: var(--space-5);
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.course-badges {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.badge {
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-full);
  font-size: 0.75rem;
  font-weight: 600;
}

.badge-category {
  background-color: var(--primary-100);
  color: var(--primary-700);
}

.badge-free {
  background-color: var(--success-bg);
  color: var(--success-color);
}

.badge-paid {
  background-color: var(--error-bg);
  color: var(--error-color);
}

.course-description {
  font-size: 0.95rem;
  line-height: 1.7;
  color: var(--text-secondary);
  margin: 0;
}

.course-meta {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-3);
}

.meta-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.meta-icon {
  font-size: 1.1rem;
  color: var(--primary-500);
}

.meta-label {
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

.meta-value {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-primary);
}

.stars {
  display: inline-flex;
  gap: 2px;
  margin-right: var(--space-1);
}

.star {
  color: var(--text-tertiary);
  font-size: 0.85rem;
}

.star.filled {
  color: var(--warning-color);
}

.course-actions {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-wrap: wrap;
}

.course-price {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--primary-600);
}

.course-main {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-5);
  border-radius: var(--radius-md);
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: all 0.2s;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background-color: var(--primary-600);
  color: var(--text-inverse);
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

.btn-danger {
  background-color: var(--error-color);
  color: var(--text-inverse);
}

.btn-danger:hover:not(:disabled) {
  filter: brightness(0.92);
}

.empty-state {
  text-align: center;
  padding: var(--space-8) 0;
  color: var(--text-tertiary);
}

.chapter-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.chapter-card {
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.chapter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-4) var(--space-5);
  background-color: var(--bg-tertiary);
  cursor: pointer;
  transition: background-color 0.2s;
}

.chapter-header:hover {
  background-color: var(--border-color-light);
}

.chapter-title-wrap {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.chapter-toggle {
  font-size: 0.85rem;
  color: var(--text-tertiary);
}

.chapter-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.chapter-count {
  font-size: 0.8rem;
  color: var(--text-tertiary);
}

.lesson-list {
  padding: var(--space-2) var(--space-5);
}

.lesson-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) 0;
  border-bottom: 1px solid var(--border-color-light);
  cursor: pointer;
  transition: color 0.2s;
}

.lesson-item:last-child {
  border-bottom: none;
}

.lesson-item:hover:not(.locked) {
  color: var(--primary-600);
}

.lesson-item.locked {
  color: var(--text-tertiary);
  cursor: not-allowed;
}

.lesson-icon {
  font-size: 0.85rem;
  color: var(--primary-600);
}

.lesson-item.locked .lesson-icon {
  color: var(--text-tertiary);
}

.lesson-title {
  flex: 1;
  font-size: 0.9rem;
}

.tag {
  padding: 2px var(--space-2);
  border-radius: var(--radius-sm);
  font-size: 0.7rem;
  font-weight: 600;
}

.tag-free {
  background-color: var(--success-bg);
  color: var(--success-color);
}

.tag-lock {
  background-color: var(--bg-tertiary);
  color: var(--text-tertiary);
}

.lesson-duration {
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

.resource-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.resource-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-4);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
}

.resource-info {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
}

.resource-icon {
  font-size: 1.5rem;
  color: var(--text-tertiary);
}

.resource-text h4 {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 var(--space-1) 0;
}

.resource-text p {
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin: 0 0 var(--space-1) 0;
}

.resource-meta {
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

.review-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.review-item {
  padding: var(--space-4);
  background-color: var(--bg-tertiary);
  border-radius: var(--radius-lg);
}

.review-header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-2);
}

.review-user-icon {
  font-size: 0.9rem;
  color: var(--text-tertiary);
}

.review-user {
  font-weight: 600;
  color: var(--text-primary);
}

.review-rating {
  display: inline-flex;
  gap: 2px;
}

.review-rating .star {
  font-size: 0.8rem;
}

.review-time {
  font-size: 0.75rem;
  color: var(--text-tertiary);
  margin-left: auto;
}

.review-comment {
  font-size: 0.9rem;
  color: var(--text-secondary);
  margin: 0;
  line-height: 1.6;
}

@media (max-width: 768px) {
  .course-layout {
    grid-template-columns: 1fr;
  }

  .course-info-body {
    padding: var(--space-4);
  }

  .course-meta {
    grid-template-columns: repeat(2, 1fr);
  }

  .resource-item {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-3);
  }

  .chapter-header {
    padding: var(--space-3) var(--space-4);
  }

  .lesson-list {
    padding: var(--space-2) var(--space-4);
  }
}
</style>
