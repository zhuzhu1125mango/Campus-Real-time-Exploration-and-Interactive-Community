<template>
  <div class="learning-resources">
    <GlassCard :hover="false" class="filter-card" padding="md">
      <div class="filter-header">
        <h2 class="section-title">{{ title }}</h2>
        <span class="i-ep-filter filter-icon" />
      </div>

      <div class="resources-filters">
        <select v-model="selectedCourse" @change="filterResources">
          <option value="">所有课程</option>
          <option v-for="course in courses" :key="course.id" :value="course.id">
            {{ course.title }}
          </option>
        </select>

        <select v-model="selectedType" @change="filterResources">
          <option value="">所有类型</option>
          <option value="pdf">PDF</option>
          <option value="doc">文档</option>
          <option value="video">视频</option>
          <option value="audio">音频</option>
          <option value="other">其他</option>
        </select>
      </div>
    </GlassCard>

    <div v-if="loading" class="loading-state">
      <el-skeleton :rows="5" animated />
      <span>加载资源中...</span>
    </div>

    <div v-else-if="error" class="error-state">
      <el-alert :title="error" type="error" show-icon @close="error = null" />
      <button class="btn btn-secondary retry-button" @click="loadResources">
        <span class="i-ep-refresh-right" />
        重新加载
      </button>
    </div>

    <div v-else-if="filteredResources.length === 0" class="empty-state">
      <span class="i-ep-folder-opened empty-icon" />
      <p class="empty-title">暂无学习资源</p>
      <p class="empty-desc">当前筛选条件下没有找到资源，试试其他条件吧</p>
      <button class="btn btn-secondary" @click="resetFilters">
        重置筛选条件
      </button>
    </div>

    <div v-else class="resources-list">
      <GlassCard
        v-for="resource in filteredResources"
        :key="resource.id"
        :hover="true"
        padding="md"
        class="resource-item"
      >
        <div class="resource-icon">
          <span
            class="file-icon"
            :class="getFileIconClass(resource.file_type)"
          />
        </div>
        <div class="resource-content">
          <h3 class="resource-title">{{ resource.title }}</h3>
          <p class="resource-description">{{ resource.description }}</p>
          <div class="resource-meta">
            <span class="resource-course">
              <span class="i-ep-reading meta-icon" />
              {{ typeof resource.course === 'object' ? resource.course.title : resource.course }}
            </span>
            <span class="resource-type">{{ resource.file_type.toUpperCase() }}</span>
            <span class="resource-size">{{ formatFileSize(resource.file_size) }}</span>
            <span class="resource-downloads">
              <span class="i-ep-download meta-icon" />
              {{ resource.download_count }} 次下载
            </span>
          </div>
        </div>
        <div class="resource-actions">
          <button class="btn btn-primary download-button" @click="downloadResource(resource.id, resource.file_url, resource.title)">
            <span class="i-ep-download" />
            下载
          </button>
        </div>
      </GlassCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { learningApi } from '../api/learning'
import GlassCard from '../components/GlassCard.vue'
import type { LearningResource, Course } from '../types/learning'

const props = defineProps<{
  title?: string
}>()

const title = props.title || '学习资源'
const resources = ref<LearningResource[]>([])
const courses = ref<Course[]>([])
const selectedCourse = ref('')
const selectedType = ref('')
const loading = ref(false)
const error = ref<string | null>(null)

const filteredResources = computed(() => {
  let filtered = resources.value

  if (selectedCourse.value) {
    filtered = filtered.filter(resource => {
      if (typeof resource.course === 'object' && resource.course.id) {
        return resource.course.id === Number(selectedCourse.value)
      }
      return resource.course === selectedCourse.value
    })
  }

  if (selectedType.value) {
    filtered = filtered.filter(resource => {
      const fileType = resource.file_type || ''
      if (selectedType.value === 'pdf') return fileType.toLowerCase().includes('pdf')
      if (selectedType.value === 'doc') return fileType.toLowerCase().includes('doc')
      if (selectedType.value === 'video') return fileType.toLowerCase().includes('video')
      if (selectedType.value === 'audio') return fileType.toLowerCase().includes('audio')
      return true
    })
  }

  return filtered
})

const filterResources = () => {
  // 过滤逻辑已在computed中处理
}

const resetFilters = () => {
  selectedCourse.value = ''
  selectedType.value = ''
}

const formatFileSize = (size: number): string => {
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(2)} KB`
  if (size < 1024 * 1024 * 1024) return `${(size / (1024 * 1024)).toFixed(2)} MB`
  return `${(size / (1024 * 1024 * 1024)).toFixed(2)} GB`
}

const getFileIconClass = (fileType: string): string => {
  const type = fileType.toLowerCase()
  if (type.includes('pdf')) return 'i-ep-document'
  if (type.includes('doc') || type.includes('docx')) return 'i-ep-document-copy'
  if (type.includes('video')) return 'i-ep-video-camera'
  if (type.includes('audio')) return 'i-ep-headset'
  return 'i-ep-box'
}

const downloadResource = async (resourceId: number, fileUrl: string, fileName: string) => {
  try {
    // 增加下载次数
    await learningApi.incrementResourceDownload(resourceId)

    // 触发下载
    const link = document.createElement('a')
    link.href = fileUrl
    link.download = fileName
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  } catch (error) {
    console.error('下载资源失败:', error)
    alert('下载失败，请重试')
  }
}

const loadResources = async () => {
  loading.value = true
  error.value = null
  try {
    const response = await learningApi.getResources()
    resources.value = response.results
  } catch (err) {
    console.error('加载资源失败:', err)
    error.value = '加载资源失败，请稍后重试'
  } finally {
    loading.value = false
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

onMounted(() => {
  loadResources()
  loadCourses()
})
</script>

<style scoped>
.learning-resources {
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

.resources-filters {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-3);
}

.resources-filters select {
  min-width: 160px;
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  font-size: 0.95rem;
  color: var(--text-primary);
  background: var(--bg-primary);
  transition: all 0.2s ease;
  cursor: pointer;
}

.resources-filters select:focus {
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

.resources-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.resource-item {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.resource-icon {
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-tertiary);
  border-radius: var(--radius-lg);
  flex-shrink: 0;
}

.file-icon {
  width: 28px;
  height: 28px;
  color: var(--primary-600);
}

.resource-content {
  flex: 1;
  min-width: 0;
}

.resource-title {
  font-size: 1rem;
  font-weight: 700;
  margin-bottom: var(--space-1);
  color: var(--text-primary);
  line-height: 1.4;
}

.resource-description {
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin-bottom: var(--space-2);
  line-height: 1.5;
}

.resource-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-3);
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

.resource-meta span {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
}

.resource-course,
.resource-downloads {
  color: var(--text-secondary);
}

.resource-type {
  padding: 2px 8px;
  background: var(--primary-50);
  color: var(--primary-600);
  border-radius: var(--radius-sm);
  font-weight: 500;
}

.meta-icon {
  width: 14px;
  height: 14px;
}

.resource-actions {
  flex-shrink: 0;
}

.download-button {
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
  .resources-filters {
    width: 100%;
  }

  .resources-filters select {
    flex: 1;
    min-width: 0;
  }

  .resource-item {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-3);
  }

  .resource-icon {
    align-self: flex-start;
  }

  .resource-actions {
    align-self: flex-end;
    margin-left: 0;
  }
}
</style>
