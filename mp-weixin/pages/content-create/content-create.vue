<template>
  <view class="container">
    <!-- 顶部 -->
    <view class="header">
      <view class="back-link" @click="goBack">← 返回内容中心</view>
      <view class="header-title">发布内容</view>
      <view class="header-desc">分享你的校园故事、经验与知识</view>
    </view>

    <view class="form-body">
      <view v-if="error" class="error-message">{{ error }}</view>

      <view class="form-group">
        <view class="form-label">标题 <text class="required">*</text></view>
        <input
          type="text"
          v-model="title"
          placeholder="请输入内容标题"
          class="form-input"
        />
      </view>

      <view class="form-group">
        <view class="form-label">内容类型 <text class="required">*</text></view>
        <picker mode="selector" :range="contentTypeNames" :value="contentTypeIndex" @change="onContentTypeChange">
          <view class="form-picker">{{ contentTypeNames[contentTypeIndex] || '请选择内容类型' }}</view>
        </picker>
      </view>

      <view class="form-group">
        <view class="form-label">分类</view>
        <picker mode="selector" :range="categoryNames" :value="categoryIndex" @change="onCategoryChange">
          <view class="form-picker">{{ categoryNames[categoryIndex] || '请选择分类' }}</view>
        </picker>
      </view>

      <view class="form-group">
        <view class="form-label">标签</view>
        <view class="tags-select">
          <view
            v-for="tag in tags"
            :key="tag.id"
            class="tag-item"
            :class="{ selected: selectedTags.includes(tag.id) }"
            @click="toggleTag(tag.id)"
          >
            {{ tag.name }}
          </view>
        </view>
      </view>

      <view class="form-group">
        <view class="form-label">摘要</view>
        <textarea
          v-model="summary"
          placeholder="简要描述内容要点（可选）"
          class="form-textarea"
        />
      </view>

      <view class="form-group">
        <view class="form-label">内容 <text class="required">*</text></view>
        <textarea
          v-model="content"
          placeholder="请输入内容，支持简单的 HTML 标签..."
          class="form-textarea content-textarea"
        />
      </view>

      <view class="form-group">
        <view class="form-label">特色图片</view>
        <view v-if="featuredImagePath" class="image-preview">
          <image class="preview-img" :src="featuredImagePath" mode="aspectFill" />
          <text class="remove-image" @click="removeImage">删除</text>
        </view>
        <button v-else class="upload-btn" @click="chooseImage">选择图片</button>
        <view class="form-tip">支持 JPG、PNG 格式图片</view>
      </view>

      <view class="form-group">
        <view class="form-label">发布方式</view>
        <picker mode="selector" :range="statusNames" :value="statusIndex" @change="onStatusChange">
          <view class="form-picker">{{ statusNames[statusIndex] }}</view>
        </picker>
      </view>

      <view class="form-actions">
        <button class="btn btn-secondary" @click="goBack">取消</button>
        <button class="btn btn-primary" :disabled="submitting" @click="submitContent">
          {{ submitting ? '发布中...' : '发布内容' }}
        </button>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { onUnload } from '@dcloudio/uni-app'
import contentApi from '../../api/content'
import { API_BASE_URL } from '../../api/request'

const title = ref('')
const content = ref('')
const summary = ref('')
const contentTypeIndex = ref(0)
const categoryIndex = ref(0)
const selectedTags = ref([])
const featuredImagePath = ref('')
const featuredImageFile = ref(null)
const statusIndex = ref(0)
const submitting = ref(false)
const error = ref('')
let publishRedirectTimer = null

const statusOptions = [
  { value: 'draft', label: '保存为草稿' },
  { value: 'pending', label: '提交审核' }
]
const statusNames = computed(() => statusOptions.map(s => s.label))

const contentTypes = ref([])
const categories = ref([])
const tags = ref([])

const contentTypeNames = computed(() => contentTypes.value.map(t => t.name))
const categoryNames = computed(() => ['请选择分类', ...categories.value.map(c => c.name)])

onMounted(() => {
  loadOptions()
})

onUnload(() => {
  if (publishRedirectTimer) {
    clearTimeout(publishRedirectTimer)
    publishRedirectTimer = null
  }
})

const loadOptions = async () => {
  try {
    const [typesRes, catsRes, tagsRes] = await Promise.all([
      contentApi.getContentTypes(),
      contentApi.getCategories(),
      contentApi.getTags()
    ])
    contentTypes.value = (typesRes.results || []).filter(t => t.is_active !== false)
    categories.value = catsRes.results || []
    tags.value = tagsRes.results || []
    if (contentTypes.value.length > 0) {
      contentTypeIndex.value = 0
    }
  } catch (err) {
    console.error('加载选项失败', err)
    error.value = '加载分类选项失败，请刷新重试'
  }
}

const onContentTypeChange = (e) => {
  contentTypeIndex.value = Number(e.detail.value)
}

const onCategoryChange = (e) => {
  categoryIndex.value = Number(e.detail.value)
}

const onStatusChange = (e) => {
  statusIndex.value = Number(e.detail.value)
}

const toggleTag = (tagId) => {
  const index = selectedTags.value.indexOf(tagId)
  if (index === -1) {
    selectedTags.value.push(tagId)
  } else {
    selectedTags.value.splice(index, 1)
  }
}

const chooseImage = () => {
  uni.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success: (res) => {
      featuredImagePath.value = res.tempFilePaths[0]
      featuredImageFile.value = res.tempFiles[0]
    }
  })
}

const removeImage = () => {
  featuredImagePath.value = ''
  featuredImageFile.value = null
}

const submitContent = async () => {
  if (!title.value.trim()) {
    error.value = '请输入标题'
    return
  }
  if (contentTypeIndex.value < 0 || !contentTypes.value[contentTypeIndex.value]) {
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
    const token = uni.getStorageSync('accessToken')
    const formData = {
      title: title.value.trim(),
      content_type: contentTypes.value[contentTypeIndex.value].id,
      content: content.value,
      status: statusOptions[statusIndex.value].value
    }

    if (summary.value.trim()) {
      formData.summary = summary.value.trim()
    }
    if (categoryIndex.value > 0) {
      formData.category = categories.value[categoryIndex.value - 1].id
    }
    if (selectedTags.value.length > 0) {
      formData.tags = selectedTags.value
    }

    let response
    if (featuredImagePath.value) {
      // 使用 uploadFile 上传文件
      response = await uploadWithImage(formData, token)
    } else {
      response = await contentApi.createContent(formData)
    }

    uni.showToast({ title: '发布成功', icon: 'success' })
    publishRedirectTimer = setTimeout(() => {
      uni.redirectTo({ url: `/pages/content-detail/content-detail?id=${response.id}` })
    }, 800)
  } catch (err) {
    console.error('发布内容失败', err)
    error.value = err?.message || '发布内容失败，请稍后重试'
  } finally {
    submitting.value = false
  }
}

const uploadWithImage = (formData, token) => {
  return new Promise((resolve, reject) => {
    const uploadTask = uni.uploadFile({
      url: `${API_BASE_URL}/content/contents/`,
      filePath: featuredImagePath.value,
      name: 'featured_image',
      header: {
        Authorization: `Bearer ${token}`
      },
      formData: buildStringFormData(formData),
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(JSON.parse(res.data))
        } else {
          const data = JSON.parse(res.data)
          reject(new Error(data?.detail || data?.message || '上传失败'))
        }
      },
      fail: (err) => reject(err)
    })
  })
}

const buildStringFormData = (data) => {
  const result = {}
  for (const key in data) {
    if (Array.isArray(data[key])) {
      result[key] = data[key].join(',')
    } else {
      result[key] = String(data[key])
    }
  }
  return result
}

const goBack = () => {
  uni.navigateBack({ delta: 1 })
}
</script>

<style scoped>
.container {
  min-height: 100vh;
  background-color: #f5f5f5;
  padding-bottom: 40rpx;
}

.header {
  background: linear-gradient(135deg, #4361ee 0%, #3a0ca3 100%);
  color: #fff;
  padding: 40rpx 30rpx;
}

.back-link {
  color: rgba(255, 255, 255, 0.85);
  font-size: 26rpx;
  margin-bottom: 20rpx;
}

.header-title {
  font-size: 40rpx;
  font-weight: 600;
  margin-bottom: 10rpx;
}

.header-desc {
  font-size: 26rpx;
  opacity: 0.9;
}

.form-body {
  background-color: #fff;
  margin: 20rpx;
  border-radius: 16rpx;
  padding: 30rpx;
}

.error-message {
  background-color: #fdeaea;
  color: #e74c3c;
  padding: 20rpx;
  border-radius: 12rpx;
  margin-bottom: 24rpx;
  font-size: 26rpx;
}

.form-group {
  margin-bottom: 30rpx;
}

.form-label {
  font-size: 28rpx;
  font-weight: 500;
  color: #333;
  margin-bottom: 12rpx;
}

.required {
  color: #e74c3c;
}

.form-input,
.form-picker,
.form-textarea {
  width: 100%;
  padding: 20rpx;
  border: 1rpx solid #e0e0e0;
  border-radius: 12rpx;
  font-size: 28rpx;
  background-color: #fff;
  box-sizing: border-box;
}

.form-textarea {
  height: 160rpx;
}

.content-textarea {
  height: 300rpx;
}

.tags-select {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
}

.tag-item {
  padding: 10rpx 24rpx;
  border: 1rpx solid #e0e0e0;
  border-radius: 30rpx;
  font-size: 26rpx;
  color: #666;
}

.tag-item.selected {
  background-color: rgba(67, 97, 238, 0.1);
  border-color: #4361ee;
  color: #4361ee;
}

.image-preview {
  position: relative;
  width: 200rpx;
  height: 200rpx;
}

.preview-img {
  width: 100%;
  height: 100%;
  border-radius: 12rpx;
}

.remove-image {
  position: absolute;
  top: -10rpx;
  right: -10rpx;
  background-color: #e74c3c;
  color: #fff;
  font-size: 22rpx;
  padding: 6rpx 14rpx;
  border-radius: 20rpx;
}

.upload-btn {
  background-color: #f5f5f5;
  color: #666;
  font-size: 28rpx;
  padding: 20rpx 40rpx;
  border-radius: 12rpx;
  border: 1rpx dashed #ccc;
}

.form-tip {
  font-size: 24rpx;
  color: #999;
  margin-top: 10rpx;
}

.form-actions {
  display: flex;
  gap: 24rpx;
  margin-top: 40rpx;
}

.btn {
  flex: 1;
  height: 80rpx;
  line-height: 80rpx;
  border-radius: 40rpx;
  font-size: 28rpx;
  font-weight: 500;
  border: none;
}

.btn-primary {
  background-color: #4361ee;
  color: #fff;
}

.btn-primary:disabled {
  opacity: 0.5;
}

.btn-secondary {
  background-color: #f0f0f0;
  color: #333;
}
</style>
