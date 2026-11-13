<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { contentApi } from '../api/content'
import RichTextEditor from '../components/RichTextEditor.vue'
import config from '../utils/config'
import { getApiErrorMessage } from '../utils/error'
import type { ContentType, Category, Tag } from '../types/content'
import GlassCard from '../components/GlassCard.vue'
import SectionHeader from '../components/SectionHeader.vue'

const router = useRouter()

const title = ref('')
const content = ref('')
const summary = ref('')
const contentTypeId = ref('')
const categoryId = ref('')
const selectedTags = ref<number[]>([])
const featuredImage = ref<File | null>(null)
const status = ref<'draft' | 'pending'>('draft')
const submitting = ref(false)
const error = ref('')

const contentTypes = ref<ContentType[]>([])
const categories = ref<Category[]>([])
const tags = ref<Tag[]>([])

const loadOptions = async () => {
  try {
    const [typesRes, catsRes, tagsRes] = await Promise.all([
      contentApi.getContentTypes(),
      contentApi.getCategories(),
      contentApi.getTags()
    ])
    contentTypes.value = typesRes.results
    categories.value = catsRes.results
    tags.value = tagsRes.results
    if (contentTypes.value.length > 0) {
      contentTypeId.value = String(contentTypes.value[0].id)
    }
  } catch (err) {
    console.error('加载选项失败', err)
    error.value = '加载分类选项失败，请刷新页面重试'
  }
}

const handleImageChange = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (!target.files || target.files.length === 0) return

  const file = target.files[0]
  if (!config.upload.allowedTypes.includes(file.type)) {
    error.value = '请选择 JPG、PNG、GIF 或 WebP 格式的图片'
    target.value = ''
    return
  }
  if (file.size > config.upload.maxSize) {
    error.value = `图片大小不能超过 ${config.upload.maxSize / 1024 / 1024}MB`
    target.value = ''
    return
  }

  featuredImage.value = file
}

const submitContent = async () => {
  if (!title.value.trim()) {
    error.value = '请输入标题'
    return
  }
  if (!contentTypeId.value) {
    error.value = '请选择内容类型'
    return
  }
  if (!content.value.trim()) {
    error.value = '请输入内容'
    return
  }

  submitting.value = true
  error.value = ''

  try {
    const formData = new FormData()
    formData.append('title', title.value.trim())
    formData.append('content_type', contentTypeId.value)
    formData.append('content', content.value)
    formData.append('status', status.value)
    if (summary.value.trim()) {
      formData.append('summary', summary.value.trim())
    }
    if (categoryId.value) {
      formData.append('category', categoryId.value)
    }
    selectedTags.value.forEach((tagId) => {
      formData.append('tags', String(tagId))
    })
    if (featuredImage.value) {
      formData.append('featured_image', featuredImage.value)
    }

    const response = await contentApi.createContent(formData)
    router.push(`/content/${response.id}`)
  } catch (err) {
    console.error('发布内容失败', err)
    error.value = getApiErrorMessage(err, '发布内容失败，请稍后重试')
  } finally {
    submitting.value = false
  }
}

const goBack = () => {
  router.push('/content')
}

onMounted(() => {
  loadOptions()
})
</script>

<template>
  <div class="content-create-page container-medium page-padding">
    <SectionHeader
      title="发布内容"
      subtitle="分享你的校园故事、经验与知识"
      icon="i-ep-edit-pen"
      :action="{ label: '返回内容中心', onClick: goBack }"
    />

    <GlassCard :hover="false" class="create-form-card">
      <div v-if="error" class="error-message">{{ error }}</div>

      <div class="form-group">
        <label for="title">标题 <span class="required">*</span></label>
        <input
          id="title"
          v-model="title"
          type="text"
          placeholder="请输入内容标题"
          class="form-input"
        />
      </div>

      <div class="form-row">
        <div class="form-group">
          <label for="contentType">内容类型 <span class="required">*</span></label>
          <select id="contentType" v-model="contentTypeId" class="form-select">
            <option v-for="type in contentTypes" :key="type.id" :value="String(type.id)">
              {{ type.name }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label for="category">分类</label>
          <select id="category" v-model="categoryId" class="form-select">
            <option value="">请选择分类</option>
            <option v-for="category in categories" :key="category.id" :value="String(category.id)">
              {{ category.name }}
            </option>
          </select>
        </div>
      </div>

      <div class="form-group">
        <label>标签</label>
        <div class="tags-select">
          <label
            v-for="tag in tags"
            :key="tag.id"
            class="tag-checkbox"
            :class="{ selected: selectedTags.includes(tag.id) }"
          >
            <input
              v-model="selectedTags"
              type="checkbox"
              :value="tag.id"
            />
            {{ tag.name }}
          </label>
        </div>
      </div>

      <div class="form-group">
        <label for="summary">摘要</label>
        <textarea
          id="summary"
          v-model="summary"
          placeholder="简要描述内容要点（可选）"
          class="form-textarea"
          rows="3"
        ></textarea>
      </div>

      <div class="form-group">
        <label>内容 <span class="required">*</span></label>
        <RichTextEditor v-model="content" placeholder="请输入内容..." />
      </div>

      <div class="form-group">
        <label for="featuredImage">特色图片</label>
        <input
          id="featuredImage"
          type="file"
          accept="image/*"
          class="form-file"
          @change="handleImageChange"
        />
        <p class="form-tip">支持 JPG、PNG 格式图片</p>
      </div>

      <div class="form-group form-inline">
        <label for="status">发布方式</label>
        <select id="status" v-model="status" class="form-select">
          <option value="draft">保存为草稿</option>
          <option value="pending">提交审核</option>
        </select>
      </div>

      <div class="form-actions">
        <button class="btn btn-secondary" @click="goBack">取消</button>
        <button
          class="btn btn-primary"
          :disabled="submitting"
          @click="submitContent"
        >
          <span v-if="submitting" class="loading-spinner small"></span>
          <span>{{ submitting ? '发布中...' : '发布内容' }}</span>
        </button>
      </div>
    </GlassCard>
  </div>
</template>

<style scoped>
.content-create-page {
  min-height: calc(100vh - 200px);
}

.create-form-card {
  max-width: 900px;
  margin: 0 auto;
}

.form-group {
  margin-bottom: var(--space-5);
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-4);
}

label {
  display: block;
  margin-bottom: var(--space-2);
  font-weight: 500;
  color: var(--text-primary);
}

.required {
  color: var(--error-color);
}

.form-input,
.form-select,
.form-textarea {
  width: 100%;
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  font-size: 1rem;
  transition: border-color 0.2s, box-shadow 0.2s;
  background: var(--bg-primary);
  color: var(--text-primary);
}

.form-input:focus,
.form-select:focus,
.form-textarea:focus {
  outline: none;
  border-color: var(--primary-400);
  box-shadow: 0 0 0 3px var(--primary-100);
}

.dark .form-input:focus,
.dark .form-select:focus,
.dark .form-textarea:focus {
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
}

.form-file {
  padding: var(--space-2) 0;
  color: var(--text-secondary);
}

.form-tip {
  color: var(--text-tertiary);
  font-size: 0.85rem;
  margin-top: var(--space-1);
}

.tags-select {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.tag-checkbox {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-full);
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.9rem;
  color: var(--text-secondary);
  background: var(--bg-primary);
}

.tag-checkbox input {
  display: none;
}

.tag-checkbox:hover {
  border-color: var(--primary-300);
  color: var(--primary-600);
}

.tag-checkbox.selected {
  background-color: var(--primary-50);
  border-color: var(--primary-500);
  color: var(--primary-600);
}

.dark .tag-checkbox.selected {
  background-color: var(--bg-tertiary);
  border-color: var(--primary-400);
  color: var(--primary-400);
}

.form-inline {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.form-inline label {
  margin-bottom: 0;
  white-space: nowrap;
}

.error-message {
  background-color: var(--error-bg);
  color: var(--error-color);
  padding: var(--space-4);
  border-radius: var(--radius-lg);
  margin-bottom: var(--space-5);
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-4);
  margin-top: var(--space-6);
  padding-top: var(--space-6);
  border-top: 1px solid var(--border-color-light);
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-6);
  border-radius: var(--radius-lg);
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: all 0.2s;
}

.btn-primary {
  background-color: var(--primary-600);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: var(--primary-700);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background-color: var(--bg-tertiary);
  color: var(--text-primary);
}

.btn-secondary:hover {
  background-color: var(--border-color-light);
}

.loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: spin 1s ease-in-out infinite;
}

.loading-spinner.small {
  width: 14px;
  height: 14px;
  border-width: 2px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .form-row {
    grid-template-columns: 1fr;
  }

  .form-inline {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-2);
  }

  .form-actions {
    flex-direction: column-reverse;
  }

  .btn {
    width: 100%;
  }
}
</style>
