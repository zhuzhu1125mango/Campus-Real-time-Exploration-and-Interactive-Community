<template>
  <div class="my-learning-page container-wide page-padding">
    <SectionHeader
      title="我的学习"
      subtitle="管理你正在学习的课程"
      icon="i-ep-notebook"
    />

    <div class="learning-toolbar">
      <router-link to="/certificates" class="btn btn-secondary">
        <span class="i-ep-medal" />
        我的证书
      </router-link>
    </div>

    <GlassCard :hover="false" class="my-learning-card">
      <div v-if="loading" class="loading-state">
        <div class="loading-spinner" />
        <p>加载中...</p>
      </div>

      <div v-else-if="enrollments.length === 0" class="empty-state">
        <div class="empty-icon">
          <span class="i-ep-notebook" />
        </div>
        <p>你还没有报名任何课程</p>
        <button class="btn btn-primary" @click="goLearning">
          <span class="i-ep-right" />
          去发现课程
        </button>
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
              <div class="progress-fill" :style="{ width: `${enrollment.progress}%` }" />
            </div>
            <div class="progress-meta">
              <span class="progress-text">
                <span class="i-ep-timer meta-icon" />
                学习进度 {{ enrollment.progress.toFixed(0) }}%
              </span>
              <span v-if="enrollment.is_completed" class="completed-badge">
                <span class="i-ep-check meta-icon" />
                已完成
              </span>
              <span v-else class="status-text">学习中</span>
            </div>
          </div>
          <div class="enrollment-action">
            <button class="btn btn-primary" @click.stop="goCourse(enrollment.course.id)">
              <span v-if="enrollment.is_completed" class="i-ep-refresh" />
              <span v-else class="i-ep-right" />
              {{ enrollment.is_completed ? '复习' : '继续学习' }}
            </button>
            <button
              v-if="certificateMap[enrollment.course.id]"
              class="btn btn-secondary"
              @click.stop="goCertificate(enrollment.course.id)"
            >
              <span class="i-ep-medal" />
              查看证书
            </button>
            <button
              v-if="!enrollment.is_completed"
              class="btn btn-secondary"
              @click.stop="openReminder(enrollment)"
            >
              <span :class="isReminderOn(enrollment.course.id) ? 'i-ep-bell-filled' : 'i-ep-bell'" />
              {{ isReminderOn(enrollment.course.id) ? '提醒已开启' : '学习提醒' }}
            </button>
          </div>
        </div>
      </div>
    </GlassCard>

    <el-dialog v-model="reminderDialogVisible" title="学习提醒" width="420px">
      <div class="reminder-form">
        <p class="reminder-course">{{ editingReminder.courseTitle }}</p>
        <div class="reminder-row">
          <span class="reminder-label">开启每日提醒</span>
          <el-switch v-model="editingReminder.is_active" />
        </div>
        <div class="reminder-row">
          <span class="reminder-label">提醒时间</span>
          <el-time-picker
            v-model="editingReminder.remind_time"
            format="HH:mm"
            value-format="HH:mm"
            placeholder="选择时间"
            :disabled="!editingReminder.is_active"
          />
        </div>
        <p class="reminder-tip">提醒通过站内通知发送，课程完成后自动停止。</p>
      </div>
      <template #footer>
        <button class="btn btn-secondary" @click="reminderDialogVisible = false">取消</button>
        <button class="btn btn-primary" :disabled="savingReminder" @click="saveReminder">
          {{ savingReminder ? '保存中...' : '保存' }}
        </button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { learningApi } from '../api/learning'
import { getApiErrorMessage } from '../utils/error'
import type { Enrollment, Certificate, StudyReminder } from '../types/learning'
import GlassCard from '@/components/GlassCard.vue'
import SectionHeader from '@/components/SectionHeader.vue'

const router = useRouter()

const enrollments = ref<Enrollment[]>([])
const certificates = ref<Certificate[]>([])
const certificateMap = ref<Record<number, Certificate>>({})
const reminderMap = ref<Record<number, StudyReminder>>({})
const reminderDialogVisible = ref(false)
const savingReminder = ref(false)
const editingReminder = ref({
  courseId: 0,
  courseTitle: '',
  is_active: true,
  remind_time: '20:00'
})
const loading = ref(false)
const defaultCover = '/trae-api/api/ide/v1/text_to_image?prompt=campus%20online%20course%20cover%20image&image_size=landscape_16_9'

const loadEnrollments = async () => {
  loading.value = true
  try {
    const [enrollmentRes, certificateRes, reminderRes] = await Promise.all([
      learningApi.getEnrollments(),
      learningApi.getCertificates(),
      learningApi.getReminders()
    ])
    enrollments.value = enrollmentRes.results
    certificates.value = certificateRes.results || []
    certificateMap.value = certificates.value.reduce<Record<number, Certificate>>((acc, item) => {
      acc[item.course_id] = item
      return acc
    }, {})
    reminderMap.value = (reminderRes.results || []).reduce<Record<number, StudyReminder>>((acc, item) => {
      acc[item.course_id] = item
      return acc
    }, {})
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '加载学习记录失败'))
  } finally {
    loading.value = false
  }
}

const isReminderOn = (courseId: number) => {
  const reminder = reminderMap.value[courseId]
  return Boolean(reminder && reminder.is_active)
}

const openReminder = (enrollment: Enrollment) => {
  const reminder = reminderMap.value[enrollment.course.id]
  editingReminder.value = {
    courseId: enrollment.course.id,
    courseTitle: enrollment.course.title,
    is_active: reminder ? reminder.is_active : true,
    remind_time: reminder?.remind_time || '20:00'
  }
  reminderDialogVisible.value = true
}

const saveReminder = async () => {
  if (!editingReminder.value.courseId) return
  savingReminder.value = true
  try {
    const saved = await learningApi.createReminder({
      course: editingReminder.value.courseId,
      remind_time: editingReminder.value.remind_time,
      is_active: editingReminder.value.is_active
    })
    reminderMap.value = { ...reminderMap.value, [saved.course_id]: saved }
    reminderDialogVisible.value = false
    ElMessage.success(saved.is_active ? `已设置每天 ${saved.remind_time} 提醒` : '学习提醒已关闭')
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '保存提醒失败'))
  } finally {
    savingReminder.value = false
  }
}

const goCourse = (courseId: number) => {
  router.push(`/learning/course/${courseId}`)
}

const goCertificate = (courseId: number) => {
  const certificate = certificateMap.value[courseId]
  if (certificate) {
    router.push(`/certificate/${certificate.id}`)
  }
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
  min-height: calc(100vh - 200px);
}

.my-learning-card {
  min-height: 400px;
}

.learning-toolbar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: var(--space-4);
}

.reminder-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.reminder-course {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
}

.reminder-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}

.reminder-label {
  font-size: 0.9rem;
  color: var(--text-secondary);
}

.reminder-tip {
  margin: 0;
  font-size: 0.8rem;
  color: var(--text-tertiary);
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-10) 0;
  color: var(--text-secondary);
  text-align: center;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--primary-200);
  border-top-color: var(--primary-600);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: var(--space-3);
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-icon {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: var(--primary-50);
  color: var(--primary-500);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: var(--space-4);
  font-size: 2rem;
}

.enrollment-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.enrollment-card {
  display: flex;
  align-items: center;
  gap: var(--space-5);
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  border: 1px solid var(--border-color);
  cursor: pointer;
  transition: all 0.25s ease;
}

.enrollment-card:hover {
  border-color: var(--primary-600);
  box-shadow: var(--shadow-md);
}

.enrollment-cover {
  width: 160px;
  aspect-ratio: 16 / 9;
  object-fit: cover;
  border-radius: var(--radius-md);
  flex-shrink: 0;
}

.enrollment-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  min-width: 0;
}

.course-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.course-desc {
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin: 0;
  line-height: 1.5;
}

.progress-bar {
  height: 8px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--primary-500), var(--primary-600));
  border-radius: var(--radius-full);
  transition: width 0.3s ease;
}

.progress-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.progress-text,
.status-text {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
}

.completed-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  color: var(--success-color);
  font-weight: 600;
}

.meta-icon {
  font-size: 1rem;
}

.enrollment-action {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
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
  text-decoration: none;
}

.btn-primary {
  background-color: var(--primary-600);
  color: white;
}

.btn-primary:hover {
  background-color: var(--primary-700);
}

.btn-secondary {
  background-color: var(--bg-tertiary);
  color: var(--text-primary);
}

.btn-secondary:hover {
  background-color: var(--border-color);
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
