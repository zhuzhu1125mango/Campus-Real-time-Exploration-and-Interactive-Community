<template>
  <view class="container">
    <view class="loading-state" v-if="loading">
      <text>加载课程中...</text>
    </view>

    <template v-else-if="course">
      <!-- 课程头部 -->
      <view class="course-hero">
        <image
          class="course-cover"
          :src="course.cover_image || defaultCover"
          mode="aspectFill"
        />
        <view class="course-info">
          <view class="course-badges">
            <text v-for="cat in course.categories" :key="cat.id" class="badge">{{ cat.name }}</text>
            <text v-if="course.is_free" class="badge badge-free">免费</text>
            <text v-else class="badge badge-paid">付费</text>
          </view>
          <view class="course-title">{{ course.title }}</view>
          <view class="course-description">{{ course.description }}</view>
          <view class="course-meta">
            <view class="meta-item">
              <text class="meta-label">讲师</text>
              <text class="meta-value">{{ course.instructor?.username }}</text>
            </view>
            <view class="meta-item">
              <text class="meta-label">评分</text>
              <text class="meta-value">{{ renderStars(course.average_rating) }} {{ course.average_rating?.toFixed(1) }}</text>
            </view>
            <view class="meta-item">
              <text class="meta-label">报名</text>
              <text class="meta-value">{{ course.enroll_count }} 人</text>
            </view>
            <view class="meta-item">
              <text class="meta-label">课时</text>
              <text class="meta-value">{{ course.lesson_count }} 节</text>
            </view>
          </view>
          <view class="course-actions">
            <button v-if="!isLoggedIn" class="btn btn-primary" @click="goLogin">登录后报名</button>
            <button v-else-if="course.is_enrolled" class="btn btn-primary" @click="startLearning">继续学习</button>
            <button v-else class="btn btn-primary" :disabled="enrolling" @click="enroll">
              {{ enrolling ? '报名中...' : '立即报名' }}
            </button>
            <text v-if="!course.is_free" class="course-price">¥{{ course.price }}</text>
          </view>
        </view>
      </view>

      <!-- 内容区 -->
      <view class="course-body">
        <!-- 章节 -->
        <view class="section">
          <view class="section-title">课程章节</view>
          <view v-if="chapters.length === 0" class="empty-state">暂无章节</view>
          <view v-else class="chapter-list">
            <view
              v-for="chapter in chapters"
              :key="chapter.id"
              class="chapter-card"
            >
              <view class="chapter-header" @click="toggleChapter(chapter.id)">
                <view class="chapter-title-wrap">
                  <text class="chapter-toggle">{{ isExpanded(chapter.id) ? '▼' : '▶' }}</text>
                  <text class="chapter-title">{{ chapter.title }}</text>
                </view>
                <text class="chapter-count">{{ chapter.lesson_count }} 课时</text>
              </view>
              <view v-show="isExpanded(chapter.id)" class="lesson-list">
                <view
                  v-for="lesson in chapter.lessons"
                  :key="lesson.id"
                  class="lesson-item"
                  :class="{ locked: !canWatchLesson(lesson) }"
                  @click="openLesson(lesson)"
                >
                  <text class="lesson-icon">
                    {{ getLessonProgress(lesson.id)?.is_completed ? '✓' : '▶' }}
                  </text>
                  <text class="lesson-title">{{ lesson.title }}</text>
                  <text v-if="lesson.is_free" class="tag tag-free">免费</text>
                  <text v-else-if="!course.is_enrolled" class="tag tag-lock">锁定</text>
                  <text v-if="getLessonProgress(lesson.id)?.is_completed" class="tag tag-completed">已完成</text>
                  <text v-if="lesson.duration" class="lesson-duration">{{ formatDuration(lesson.duration) }}</text>
                </view>
              </view>
            </view>
          </view>
        </view>

        <!-- 资源 -->
        <view class="section">
          <view class="section-title">课程资源</view>
          <view v-if="resources.length === 0" class="empty-state">暂无资源</view>
          <view v-else class="resource-list">
            <view v-for="resource in resources" :key="resource.id" class="resource-item" @click="downloadResource(resource)">
              <text class="resource-icon">{{ getResourceIcon(resource.file_type) }}</text>
              <view class="resource-text">
                <view class="resource-title">{{ resource.title }}</view>
                <view class="resource-desc">{{ resource.description || '无描述' }}</view>
                <view class="resource-meta">{{ resource.file_type?.toUpperCase() }} · {{ formatFileSize(resource.file_size) }}</view>
              </view>
              <text class="download-icon">↓</text>
            </view>
          </view>
        </view>

        <!-- 评价 -->
        <view class="section">
          <view class="section-title">学员评价</view>
          <view v-if="reviews.length === 0" class="empty-state">暂无评价</view>
          <view v-else class="review-list">
            <view v-for="review in reviews" :key="review.id" class="review-item">
              <view class="review-header">
                <text class="review-user">{{ review.user?.username }}</text>
                <text class="review-rating">{{ renderStars(review.rating) }}</text>
                <text class="review-time">{{ formatDate(review.created_at) }}</text>
              </view>
              <view class="review-comment">{{ review.comment }}</view>
            </view>
          </view>
        </view>
      </view>

      <!-- 课时播放器弹窗 -->
      <view class="player-mask" v-if="playerVisible" @click="closePlayer">
        <view class="player-wrap" @click.stop>
          <view class="player-header">
            <text class="player-title">{{ currentLesson?.title }}</text>
            <text class="player-close" @click="closePlayer">×</text>
          </view>
          <video
            v-if="currentLesson?.video_url"
            id="lessonVideo"
            class="player-video"
            :src="currentLesson.video_url"
            :initial-time="currentProgress?.last_position || 0"
            controls
            autoplay
            @timeupdate="handleTimeUpdate"
            @ended="handleLessonComplete"
          />
          <view v-else class="player-content">
            <rich-text :nodes="safeLessonContent"></rich-text>
          </view>
          <view v-if="currentLesson?.video_url" class="player-controls">
            <view class="speed-control">
              <text class="control-label">倍速</text>
              <view class="speed-list">
                <text
                  v-for="speed in speedOptions"
                  :key="speed"
                  class="speed-item"
                  :class="{ active: playbackRate === speed }"
                  @click="changeSpeed(speed)"
                >
                  {{ speed }}x
                </text>
              </view>
            </view>
            <text v-if="currentProgress?.last_position" class="resume-tip">
              已恢复至 {{ formatSeconds(currentProgress.last_position) }}
            </text>
            <text v-if="currentProgress?.is_completed" class="completed-tip">已完成</text>
          </view>
        </view>
      </view>
    </template>

    <view class="error-state" v-else>
      <text>{{ error }}</text>
      <button class="retry-btn" @click="loadCourse">重新加载</button>
    </view>
  </view>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { onUnload } from '@dcloudio/uni-app'
import learningApi from '../../api/learning'
import { sanitizeHtml } from '../../utils/xss'

const defaultCover = 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=campus%20online%20course%20cover%20image&image_size=landscape_16_9'

const course = ref(null)
const chapters = ref([])
const resources = ref([])
const reviews = ref([])
const enrollment = ref(null)
const loading = ref(false)
const enrolling = ref(false)
const error = ref('')
const isLoggedIn = ref(false)
const expandedChapters = ref([])
const playerVisible = ref(false)
const currentLesson = ref(null)
const playbackRate = ref(1)
const progressMap = ref({})
const currentProgress = ref(null)
const lastSavedPosition = ref(0)
const speedOptions = [0.5, 0.75, 1, 1.25, 1.5, 2]
let playbackRateTimer = null
let nextLessonTimer = null

const safeLessonContent = computed(() => sanitizeHtml(currentLesson.value?.content || ''))

const courseId = ref('')

onMounted(() => {
  isLoggedIn.value = !!uni.getStorageSync('accessToken')
  courseId.value = getQueryId()
  loadCourse()
})

onUnload(() => {
  if (playbackRateTimer) {
    clearTimeout(playbackRateTimer)
    playbackRateTimer = null
  }
  if (nextLessonTimer) {
    clearTimeout(nextLessonTimer)
    nextLessonTimer = null
  }
})

const getQueryId = () => {
  const pages = getCurrentPages()
  const page = pages[pages.length - 1]
  return page?.options?.id || page?.$route?.query?.id
}

const loadCourse = async () => {
  if (!courseId.value) {
    error.value = '无效的课程ID'
    return
  }

  loading.value = true
  error.value = ''
  try {
    const requests = [
      learningApi.getCourseDetail(courseId.value),
      learningApi.getCourseChapters(courseId.value),
      learningApi.getCourseResources(courseId.value),
      learningApi.getCourseReviews(courseId.value)
    ]
    if (isLoggedIn.value) {
      requests.push(learningApi.getEnrollments({ course: courseId.value }))
    }

    const [courseRes, chaptersRes, resourcesRes, reviewsRes, enrollmentRes] = await Promise.all(requests)

    course.value = courseRes
    chapters.value = (chaptersRes.results || []).sort((a, b) => a.order - b.order)
    resources.value = resourcesRes.results || []
    reviews.value = reviewsRes.results || []

    if (enrollmentRes && enrollmentRes.results.length > 0) {
      enrollment.value = enrollmentRes.results[0]
      course.value.is_enrolled = true
      await loadProgresses()
    }

    if (chapters.value.length > 0) {
      expandedChapters.value = [chapters.value[0].id]
    }
  } catch (err) {
    console.error('加载课程失败', err)
    error.value = '课程加载失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

const toggleChapter = (chapterId) => {
  const index = expandedChapters.value.indexOf(chapterId)
  if (index === -1) {
    expandedChapters.value.push(chapterId)
  } else {
    expandedChapters.value.splice(index, 1)
  }
}

const isExpanded = (chapterId) => expandedChapters.value.includes(chapterId)

const canWatchLesson = (lesson) => {
  return lesson.is_free || course.value?.is_enrolled
}

const openLesson = async (lesson) => {
  if (!canWatchLesson(lesson)) {
    uni.showToast({ title: '报名课程后即可学习该课时', icon: 'none' })
    return
  }
  currentLesson.value = lesson
  playbackRate.value = 1
  await loadLessonProgress(lesson)
  playerVisible.value = true
  learningApi.incrementLessonView(lesson.id).catch(() => {})
  playbackRateTimer = setTimeout(() => {
    applyPlaybackRate()
  }, 300)
}

const startLearning = () => {
  for (const chapter of chapters.value) {
    for (const lesson of chapter.lessons) {
      if (canWatchLesson(lesson)) {
        openLesson(lesson)
        return
      }
    }
  }
  uni.showToast({ title: '暂无可学习课时', icon: 'none' })
}

const closePlayer = () => {
  if (currentLesson.value && enrollment.value) {
    saveProgress(true)
  }
  playerVisible.value = false
  currentLesson.value = null
  currentProgress.value = null
  lastSavedPosition.value = 0
}

const loadProgresses = async () => {
  if (!enrollment.value) return
  try {
    const res = await learningApi.getProgresses({ enrollment: enrollment.value.id })
    const list = res.results || []
    const map = {}
    list.forEach((p) => {
      map[p.lesson] = p
    })
    progressMap.value = map
  } catch (err) {
    console.error('加载学习进度失败', err)
  }
}

const getLessonProgress = (lessonId) => {
  return progressMap.value[lessonId] || null
}

const loadLessonProgress = async (lesson) => {
  if (!enrollment.value || !lesson) return
  let progress = progressMap.value[lesson.id]
  if (!progress) {
    try {
      const created = await learningApi.recordProgress({
        enrollment: enrollment.value.id,
        lesson: lesson.id,
        last_position: 0
      })
      progress = created
      progressMap.value[lesson.id] = progress
    } catch (err) {
      console.error('创建进度失败', err)
    }
  }
  currentProgress.value = progress || null
  lastSavedPosition.value = progress?.last_position || 0
}

const saveProgress = async (force = false) => {
  if (!enrollment.value || !currentLesson.value) return
  // 小程序 video 组件不直接暴露 currentTime，需在 timeupdate 事件中通过 detail 获取
  const videoCtx = uni.createVideoContext('lessonVideo')
  // 通过组件事件中的 currentTime 保存，这里仅作兜底，不强制时跳过
  if (!force) return

  const position = lastSavedPosition.value
  try {
    const updated = await learningApi.recordProgress({
      enrollment: enrollment.value.id,
      lesson: currentLesson.value.id,
      last_position: position,
      last_watched_at: new Date().toISOString()
    })
    progressMap.value[currentLesson.value.id] = updated
    currentProgress.value = updated
  } catch (err) {
    console.error('保存进度失败', err)
  }
}

const handleTimeUpdate = (e) => {
  const currentTime = Math.floor(e.detail.currentTime || 0)
  if (Math.abs(currentTime - lastSavedPosition.value) >= 10) {
    lastSavedPosition.value = currentTime
    learningApi.recordProgress({
      enrollment: enrollment.value.id,
      lesson: currentLesson.value.id,
      last_position: currentTime,
      last_watched_at: new Date().toISOString()
    }).then((updated) => {
      progressMap.value[currentLesson.value.id] = updated
      currentProgress.value = updated
    }).catch((err) => console.error('保存进度失败', err))
  }
}

const applyPlaybackRate = () => {
  const videoCtx = uni.createVideoContext('lessonVideo')
  if (videoCtx.playbackRate) {
    videoCtx.playbackRate(playbackRate.value)
  }
}

const changeSpeed = (speed) => {
  playbackRate.value = speed
  applyPlaybackRate()
}

const handleLessonComplete = async () => {
  if (!enrollment.value || !currentLesson.value) return
  try {
    const updated = await learningApi.recordProgress({
      enrollment: enrollment.value.id,
      lesson: currentLesson.value.id,
      is_completed: true,
      last_position: lastSavedPosition.value,
      last_watched_at: new Date().toISOString()
    })
    progressMap.value[currentLesson.value.id] = updated
    currentProgress.value = updated
    uni.showToast({ title: '课时完成', icon: 'success' })
    nextLessonTimer = setTimeout(() => {
      playNextLesson()
    }, 1000)
  } catch (err) {
    console.error('更新进度失败', err)
  }
}

const playNextLesson = () => {
  const allLessons = []
  chapters.value.forEach((chapter) => {
    chapter.lessons.forEach((lesson) => {
      allLessons.push(lesson)
    })
  })
  const currentIndex = allLessons.findIndex((l) => l.id === currentLesson.value?.id)
  if (currentIndex === -1 || currentIndex === allLessons.length - 1) {
    closePlayer()
    return
  }
  const nextLesson = allLessons[currentIndex + 1]
  if (!canWatchLesson(nextLesson)) {
    closePlayer()
    uni.showToast({ title: '已到达最后一个可学习课时', icon: 'none' })
    return
  }
  currentLesson.value = nextLesson
  loadLessonProgress(nextLesson)
}

const goLogin = () => {
  uni.navigateTo({ url: '/pages/login/login' })
}

const enroll = async () => {
  if (!isLoggedIn.value) {
    goLogin()
    return
  }
  enrolling.value = true
  try {
    await learningApi.enrollCourse(courseId.value)
    if (course.value) {
      course.value.is_enrolled = true
      course.value.enroll_count += 1
    }
    uni.showToast({ title: '报名成功', icon: 'success' })
  } catch (err) {
    console.error('报名失败', err)
    uni.showToast({ title: err?.message || '报名失败', icon: 'none' })
  } finally {
    enrolling.value = false
  }
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

const renderStars = (rating) => {
  const r = Math.round(rating || 0)
  return '★'.repeat(r) + '☆'.repeat(5 - r)
}

const formatDuration = (duration) => {
  if (!duration) return ''
  const parts = duration.split(':')
  if (parts.length === 3) {
    const [h, m, s] = parts
    return `${Number(h)}:${m}:${s}`
  }
  return duration
}

const formatSeconds = (seconds) => {
  if (!seconds) return '0:00'
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${String(s).padStart(2, '0')}`
}

const formatFileSize = (size) => {
  if (!size) return '未知大小'
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(2)} KB`
  if (size < 1024 * 1024 * 1024) return `${(size / (1024 * 1024)).toFixed(2)} MB`
  return `${(size / (1024 * 1024 * 1024)).toFixed(2)} GB`
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

const formatDate = (date) => {
  if (!date) return ''
  const d = new Date(date)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}
</script>

<style scoped>
.container {
  min-height: 100vh;
  background-color: #f5f5f5;
  padding-bottom: 40rpx;
}

.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 120rpx;
  color: #999;
}

.retry-btn {
  margin-top: 30rpx;
  background-color: #4361ee;
  color: #fff;
  font-size: 26rpx;
  padding: 12rpx 40rpx;
  border-radius: 30rpx;
  border: none;
}

.course-hero {
  background: linear-gradient(135deg, #4361ee 0%, #3a56d4 100%);
  color: #fff;
  padding: 40rpx 30rpx;
}

.course-cover {
  width: 100%;
  height: 320rpx;
  border-radius: 16rpx;
  margin-bottom: 24rpx;
}

.course-info {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.course-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
}

.badge {
  background-color: rgba(255, 255, 255, 0.2);
  font-size: 22rpx;
  padding: 6rpx 16rpx;
  border-radius: 20rpx;
}

.badge-free {
  background-color: #27ae60;
}

.badge-paid {
  background-color: #e74c3c;
}

.course-title {
  font-size: 40rpx;
  font-weight: 700;
  line-height: 1.3;
}

.course-description {
  font-size: 28rpx;
  opacity: 0.9;
  line-height: 1.5;
}

.course-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 30rpx;
}

.meta-item {
  display: flex;
  flex-direction: column;
  gap: 6rpx;
}

.meta-label {
  font-size: 22rpx;
  opacity: 0.7;
}

.meta-value {
  font-size: 26rpx;
  font-weight: 500;
}

.course-actions {
  display: flex;
  align-items: center;
  gap: 20rpx;
  margin-top: 10rpx;
}

.btn {
  height: 72rpx;
  line-height: 72rpx;
  border-radius: 36rpx;
  font-size: 28rpx;
  font-weight: 600;
  border: none;
  padding: 0 40rpx;
}

.btn-primary {
  background-color: #fff;
  color: #4361ee;
}

.btn-primary:disabled {
  opacity: 0.7;
}

.course-price {
  font-size: 36rpx;
  font-weight: 700;
}

.course-body {
  padding: 20rpx 30rpx;
}

.section {
  background-color: #fff;
  border-radius: 16rpx;
  padding: 30rpx;
  margin-bottom: 20rpx;
}

.section-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 24rpx;
}

.empty-state {
  text-align: center;
  padding: 40rpx;
  color: #999;
  font-size: 26rpx;
}

.chapter-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.chapter-card {
  border: 1rpx solid #e8e8e8;
  border-radius: 12rpx;
  overflow: hidden;
}

.chapter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24rpx 28rpx;
  background-color: #f9fafc;
}

.chapter-title-wrap {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.chapter-toggle {
  font-size: 22rpx;
  color: #666;
}

.chapter-title {
  font-size: 28rpx;
  font-weight: 600;
  color: #333;
}

.chapter-count {
  font-size: 24rpx;
  color: #888;
}

.lesson-list {
  padding: 12rpx 28rpx;
}

.lesson-item {
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 20rpx 0;
  border-bottom: 1rpx solid #f0f0f0;
}

.lesson-item:last-child {
  border-bottom: none;
}

.lesson-item.locked {
  color: #999;
}

.lesson-icon {
  font-size: 22rpx;
  color: #4361ee;
}

.lesson-item.locked .lesson-icon {
  color: #bbb;
}

.lesson-title {
  flex: 1;
  font-size: 28rpx;
}

.tag {
  font-size: 20rpx;
  padding: 4rpx 10rpx;
  border-radius: 4rpx;
}

.tag-free {
  background-color: #e8f8ef;
  color: #27ae60;
}

.tag-lock {
  background-color: #f2f2f2;
  color: #888;
}

.tag-completed {
  background-color: #d4edda;
  color: #155724;
}

.lesson-duration {
  font-size: 22rpx;
  color: #888;
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

.resource-text {
  flex: 1;
}

.resource-title {
  font-size: 28rpx;
  color: #333;
  margin-bottom: 6rpx;
}

.resource-desc {
  font-size: 24rpx;
  color: #666;
  margin-bottom: 6rpx;
}

.resource-meta {
  font-size: 22rpx;
  color: #999;
}

.download-icon {
  font-size: 32rpx;
  color: #4361ee;
}

.review-list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.review-item {
  padding: 20rpx;
  background-color: #f9fafc;
  border-radius: 12rpx;
}

.review-header {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-bottom: 10rpx;
}

.review-user {
  font-weight: 600;
  color: #333;
  font-size: 28rpx;
}

.review-rating {
  color: #ffc107;
  font-size: 24rpx;
}

.review-time {
  font-size: 22rpx;
  color: #999;
  margin-left: auto;
}

.review-comment {
  font-size: 26rpx;
  color: #555;
  line-height: 1.5;
}

.player-mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 999;
}

.player-wrap {
  width: 90%;
  background-color: #fff;
  border-radius: 16rpx;
  overflow: hidden;
}

.player-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20rpx 30rpx;
  border-bottom: 1rpx solid #f0f0f0;
}

.player-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #333;
}

.player-close {
  font-size: 48rpx;
  color: #999;
  padding: 0 10rpx;
}

.player-video {
  width: 100%;
  height: 400rpx;
}

.player-content {
  max-height: 600rpx;
  overflow-y: auto;
  padding: 30rpx;
}

.player-controls {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
  padding: 20rpx 30rpx;
  background-color: #1a1a1a;
  color: #fff;
}

.speed-control {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.control-label {
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.8);
}

.speed-list {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
}

.speed-item {
  padding: 8rpx 16rpx;
  border-radius: 6rpx;
  font-size: 22rpx;
  background-color: rgba(255, 255, 255, 0.15);
  color: #fff;
}

.speed-item.active {
  background-color: #4361ee;
}

.resume-tip,
.completed-tip {
  font-size: 22rpx;
}

.resume-tip {
  color: rgba(255, 255, 255, 0.7);
}

.completed-tip {
  color: #27ae60;
}
</style>
