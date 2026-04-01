<template>
  <div class="learning-resources">
    <div class="resources-header">
      <h2>{{ title }}</h2>
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
    </div>
    <div class="resources-list">
      <div v-for="resource in filteredResources" :key="resource.id" class="resource-item">
        <div class="resource-icon">
          <span v-if="resource.file_type.includes('pdf')" class="icon">📄</span>
          <span v-else-if="resource.file_type.includes('doc') || resource.file_type.includes('docx')" class="icon">📝</span>
          <span v-else-if="resource.file_type.includes('video')" class="icon">🎥</span>
          <span v-else-if="resource.file_type.includes('audio')" class="icon">🎵</span>
          <span v-else class="icon">📦</span>
        </div>
        <div class="resource-content">
          <h3 class="resource-title">{{ resource.title }}</h3>
          <p class="resource-description">{{ resource.description }}</p>
          <div class="resource-meta">
            <span class="resource-course">{{ resource.course }}</span>
            <span class="resource-type">{{ resource.file_type.toUpperCase() }}</span>
            <span class="resource-size">{{ formatFileSize(resource.file_size) }}</span>
            <span class="resource-downloads">{{ resource.download_count }} 次下载</span>
          </div>
        </div>
        <div class="resource-actions">
          <button class="download-button" @click="downloadResource(resource.id, resource.file_url, resource.title)">
            下载
          </button>
        </div>
      </div>
    </div>
    <div v-if="filteredResources.length === 0" class="no-resources">
      暂无学习资源
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { learningApi } from '../api/learning'
import type { LearningResource, Course } from '../types/learning'

const props = defineProps<{
  title?: string
}>()

const title = props.title || '学习资源'
const resources = ref<LearningResource[]>([])
const courses = ref<Course[]>([])
const selectedCourse = ref('')
const selectedType = ref('')

const filteredResources = computed(() => {
  let filtered = resources.value
  
  if (selectedCourse.value) {
    filtered = filtered.filter(resource => resource.course === selectedCourse.value)
  }
  
  if (selectedType.value) {
    filtered = filtered.filter(resource => {
      if (selectedType.value === 'pdf') return resource.file_type.includes('pdf')
      if (selectedType.value === 'doc') return resource.file_type.includes('doc')
      if (selectedType.value === 'video') return resource.file_type.includes('video')
      if (selectedType.value === 'audio') return resource.file_type.includes('audio')
      return true
    })
  }
  
  return filtered
})

const filterResources = () => {
  // 过滤逻辑已在computed中处理
}

const formatFileSize = (size: number): string => {
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(2)} KB`
  if (size < 1024 * 1024 * 1024) return `${(size / (1024 * 1024)).toFixed(2)} MB`
  return `${(size / (1024 * 1024 * 1024)).toFixed(2)} GB`
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
  try {
    const response = await learningApi.getResources()
    resources.value = response.results
  } catch (error) {
    console.error('加载资源失败:', error)
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
  padding: 20px;
}

.resources-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.resources-header h2 {
  font-size: 24px;
  font-weight: bold;
  color: #333;
}

.resources-filters {
  display: flex;
  gap: 10px;
}

.resources-filters select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.resources-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.resource-item {
  display: flex;
  align-items: center;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 16px;
  transition: transform 0.3s ease;
}

.resource-item:hover {
  transform: translateX(5px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.resource-icon {
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f5;
  border-radius: 8px;
  margin-right: 16px;
  flex-shrink: 0;
}

.resource-icon .icon {
  font-size: 24px;
}

.resource-content {
  flex: 1;
}

.resource-title {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 4px;
  color: #333;
}

.resource-description {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
  line-height: 1.4;
}

.resource-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #888;
  flex-wrap: wrap;
}

.resource-actions {
  margin-left: 16px;
  flex-shrink: 0;
}

.download-button {
  padding: 8px 16px;
  background: #27ae60;
  color: #fff;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.3s ease;
}

.download-button:hover {
  background: #219a52;
}

.no-resources {
  text-align: center;
  padding: 40px;
  color: #999;
  font-size: 16px;
}

@media (max-width: 768px) {
  .resources-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .resources-filters {
    width: 100%;
  }
  
  .resources-filters select {
    flex: 1;
  }
  
  .resource-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
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