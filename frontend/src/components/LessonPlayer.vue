<template>
  <ElDialog
    v-model="visible"
    :title="lesson?.title || '课时学习'"
    width="900px"
    destroy-on-close
    class="lesson-player-dialog"
    @closed="handleClose"
  >
    <div v-if="lesson" class="lesson-player">
      <!-- 视频区 -->
      <div v-if="lesson.video_url" class="video-wrapper">
        <video
          ref="videoRef"
          :src="lesson.video_url"
          controls
          class="lesson-video"
          @ended="handleVideoEnded"
        ></video>
      </div>

      <!-- 课时内容 -->
      <div class="lesson-content">
        <h3 class="lesson-section-title">课时内容</h3>
        <div v-if="lesson.content" class="content-text" v-html="lesson.content"></div>
        <div v-else class="empty-tip">该课时暂无文字内容</div>
      </div>

      <!-- 课时信息 -->
      <div class="lesson-meta-bar">
        <span v-if="lesson.duration">时长：{{ formatDuration(lesson.duration) }}</span>
        <span>浏览量：{{ lesson.view_count }}</span>
        <span v-if="progress?.is_completed" class="completed-tag">已完成</span>
      </div>

      <!-- 操作 -->
      <div class="lesson-actions">
        <button
          v-if="!progress?.is_completed"
          class="btn btn-primary"
          :disabled="completing"
          @click="markComplete"
        >
          {{ completing ? '提交中...' : '标记为已完成' }}
        </button>
        <button v-else class="btn btn-success" disabled>已完成</button>
      </div>
    </div>
  </ElDialog>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { ElDialog, ElMessage } from 'element-plus'
import { learningApi } from '../api/learning'
import type { Lesson, Course, Progress, Enrollment } from '../types/learning'

const props = defineProps<{
  visible: boolean
  lesson: Lesson | null
  course: Course | null
  enrollment?: Enrollment | null
}>()

const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void
  (e: 'complete'): void
}>()

const visible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val)
})

const progress = ref<Progress | null>(null)
const loadingProgress = ref(false)
const completing = ref(false)

const handleClose = () => {
  progress.value = null
}

const loadProgress = async () => {
  if (!props.lesson || !props.enrollment) return
  loadingProgress.value = true
  try {
    const res = await learningApi.getProgresses({
      enrollment: props.enrollment.id,
      lesson: props.lesson.id
    })
    progress.value = res.results[0] || null
  } catch (error) {
    console.error('加载进度失败:', error)
  } finally {
    loadingProgress.value = false
  }
}

const incrementView = async () => {
  if (!props.lesson) return
  try {
    await learningApi.incrementLessonView(props.lesson.id)
  } catch (error) {
    console.error('增加观看次数失败:', error)
  }
}

const markComplete = async () => {
  if (!props.lesson || !props.enrollment) {
    ElMessage.warning('请先报名课程')
    return
  }
  if (!progress.value) {
    ElMessage.warning('未找到学习进度记录')
    return
  }
  completing.value = true
  try {
    await learningApi.updateProgress(progress.value.id, {
      is_completed: true,
      last_watched_at: new Date().toISOString()
    })
    progress.value.is_completed = true
    ElMessage.success('已标记为完成')
    emit('complete')
  } catch (error: any) {
    const msg = error?.response?.data?.detail || '标记完成失败'
    ElMessage.error(msg)
  } finally {
    completing.value = false
  }
}

const handleVideoEnded = () => {
  if (props.enrollment && progress.value && !progress.value.is_completed) {
    markComplete()
  }
}

const formatDuration = (duration: string | null): string => {
  if (!duration) return ''
  const parts = duration.split(':')
  if (parts.length === 3) {
    const [h, m, s] = parts
    return `${Number(h)}:${m}:${s}`
  }
  return duration
}

watch(() => props.visible, (val) => {
  if (val && props.lesson) {
    loadProgress()
    incrementView()
  }
})
</script>

<style scoped>
.lesson-player {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.video-wrapper {
  width: 100%;
  border-radius: 8px;
  overflow: hidden;
  background: #000;
}

.lesson-video {
  width: 100%;
  max-height: 480px;
  display: block;
}

.lesson-content {
  background: #f9fafc;
  border-radius: 8px;
  padding: 20px;
}

.lesson-section-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin: 0 0 12px;
}

.content-text {
  font-size: 14px;
  line-height: 1.8;
  color: #444;
}

.empty-tip {
  color: #999;
  font-size: 14px;
}

.lesson-meta-bar {
  display: flex;
  gap: 20px;
  font-size: 13px;
  color: #666;
}

.completed-tag {
  color: #27ae60;
  font-weight: 600;
}

.lesson-actions {
  display: flex;
  justify-content: flex-end;
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

.btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.btn-primary {
  background: #4361ee;
  color: #fff;
}

.btn-primary:hover:not(:disabled) {
  background: #3a56d4;
}

.btn-success {
  background: #27ae60;
  color: #fff;
}
</style>
