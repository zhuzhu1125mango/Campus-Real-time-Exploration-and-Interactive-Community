<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { contentApi } from '../api/content'
import RichTextEditor from '../components/RichTextEditor.vue'
import type { ContentType, Category, Tag } from '../types/content'

const router = useRouter()

const title = ref('')
const content = ref('')
const summary = ref('')
const contentTypeId = ref('')
const categoryId = ref('')
const selectedTags = ref<number[]>([])
const featuredImage = ref<File | null>(null)
const isPublished = ref(true)
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
  if (target.files && target.files.length > 0) {
    featuredImage.value = target.files[0]
  }
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
    formData.append('is_published', String(isPublished.value))
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
  } catch (err: any) {
    console.error('发布内容失败', err)
    error.value = err?.response?.data?.detail || '发布内容失败，请稍后重试'
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
  <div class="content-create-page">
    <div class="create-header">
      <div class="header-inner">
        <button class="back-link" @click="goBack">← 返回内容中心</button>
        <h1>发布内容</h1>
        <p>分享你的校园故事、经验与知识</p>
      </div>
    </div>

    <div class="create-body">
      <div class="create-form">
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
          <label class="checkbox-label">
            <input v-model="isPublished" type="checkbox" />
            立即发布
          </label>
        </div>

        <div class="form-actions">
          <button class="btn btn-secondary" @click="goBack">取消</button>
          <button
            class="btn btn-primary"
            :disabled="submitting"
            @click="submitContent"
          >
            {{ submitting ? '发布中...' : '发布内容' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.content-create-page {
  min-height: calc(100vh - 200px);
}

.create-header {
  background: linear-gradient(135deg, #4361ee 0%, #3a0ca3 100%);
  color: white;
  padding: 3rem 2rem;
}

.header-inner {
  max-width: 900px;
  margin: 0 auto;
}

.back-link {
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.85);
  cursor: pointer;
  font-size: 0.95rem;
  margin-bottom: 1rem;
  padding: 0;
}

.back-link:hover {
  color: white;
}

.create-header h1 {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.create-header p {
  opacity: 0.9;
}

.create-body {
  max-width: 900px;
  margin: 0 auto;
  padding: 2rem;
}

.create-form {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #333;
}

.required {
  color: #e74c3c;
}

.form-input,
.form-select,
.form-textarea {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-size: 1rem;
  transition: border-color 0.3s;
}

.form-input:focus,
.form-select:focus,
.form-textarea:focus {
  outline: none;
  border-color: #4361ee;
}

.form-file {
  padding: 0.5rem 0;
}

.form-tip {
  color: #999;
  font-size: 0.85rem;
  margin-top: 0.25rem;
}

.tags-select {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.tag-checkbox {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.4rem 0.75rem;
  border: 1px solid #e0e0e0;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.3s;
  font-size: 0.9rem;
}

.tag-checkbox input {
  display: none;
}

.tag-checkbox.selected {
  background-color: rgba(67, 97, 238, 0.1);
  border-color: #4361ee;
  color: #4361ee;
}

.form-inline {
  display: flex;
  align-items: center;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  margin-bottom: 0;
}

.checkbox-label input {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.error-message {
  background-color: #fdeaea;
  color: #e74c3c;
  padding: 1rem;
  border-radius: 6px;
  margin-bottom: 1.5rem;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 2rem;
}

.btn {
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: all 0.3s;
}

.btn-primary {
  background-color: #4361ee;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: #3a56d4;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background-color: #f0f0f0;
  color: #333;
}

.btn-secondary:hover {
  background-color: #e0e0e0;
}

@media (max-width: 768px) {
  .form-row {
    grid-template-columns: 1fr;
  }

  .create-form {
    padding: 1.25rem;
  }
}
</style>
