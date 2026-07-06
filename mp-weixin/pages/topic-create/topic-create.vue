<template>
  <view class="container">
    <view class="header">
      <view class="back-link" @click="goBack">← 返回论坛</view>
      <view class="header-title">发布主题</view>
      <view class="header-desc">分享你的问题、经验与话题</view>
    </view>

    <view class="form-body">
      <view v-if="error" class="error-message">{{ error }}</view>

      <view class="form-group">
        <view class="form-label">标题 <text class="required">*</text></view>
        <input
          type="text"
          v-model="title"
          placeholder="请输入主题标题"
          class="form-input"
        />
      </view>

      <view class="form-group">
        <view class="form-label">板块 <text class="required">*</text></view>
        <picker mode="selector" :range="boardNames" :value="boardIndex" @change="onBoardChange">
          <view class="form-picker">{{ boardNames[boardIndex] || '请选择板块' }}</view>
        </picker>
      </view>

      <view class="form-group">
        <view class="form-label">内容 <text class="required">*</text></view>
        <textarea
          v-model="content"
          placeholder="请输入主题内容，支持简单的 HTML 标签..."
          class="form-textarea content-textarea"
        />
      </view>

      <view class="form-actions">
        <button class="btn btn-secondary" @click="goBack">取消</button>
        <button class="btn btn-primary" :disabled="submitting" @click="submitTopic">
          {{ submitting ? '发布中...' : '发布主题' }}
        </button>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { onUnload } from '@dcloudio/uni-app'
import forumApi from '../../api/forum'

const title = ref('')
const content = ref('')
const boardIndex = ref(0)
const boards = ref([])
const submitting = ref(false)
const error = ref('')
const preselectedBoardId = ref(null)
let publishRedirectTimer = null

const boardNames = computed(() => ['请选择板块', ...boards.value.map(b => b.name)])

onMounted(() => {
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1]
  const options = currentPage.options || currentPage.$page?.options || {}
  if (options.boardId) {
    preselectedBoardId.value = Number(options.boardId)
  }
  loadBoards()
})

onUnload(() => {
  if (publishRedirectTimer) {
    clearTimeout(publishRedirectTimer)
    publishRedirectTimer = null
  }
})

const loadBoards = async () => {
  try {
    const result = await forumApi.getBoards()
    const list = result.results || result || []
    boards.value = list.filter(b => b.is_active !== false)

    if (preselectedBoardId.value) {
      const index = boards.value.findIndex(b => b.id === preselectedBoardId.value)
      if (index !== -1) {
        boardIndex.value = index + 1
      }
    }
  } catch (err) {
    console.error('加载板块失败', err)
    error.value = '加载板块失败，请刷新重试'
  }
}

const onBoardChange = (e) => {
  boardIndex.value = Number(e.detail.value)
}

const submitTopic = async () => {
  if (!title.value.trim()) {
    error.value = '请输入标题'
    return
  }
  if (boardIndex.value <= 0 || !boards.value[boardIndex.value - 1]) {
    error.value = '请选择板块'
    return
  }
  if (!content.value.trim()) {
    error.value = '请输入内容'
    return
  }

  submitting.value = true
  error.value = ''

  try {
    const boardId = boards.value[boardIndex.value - 1].id
    const response = await forumApi.createTopic({
      title: title.value.trim(),
      board: boardId,
      content: content.value
    })

    uni.showToast({ title: '发布成功', icon: 'success' })
    publishRedirectTimer = setTimeout(() => {
      uni.redirectTo({ url: `/pages/post-detail/post-detail?id=${response.id}` })
    }, 800)
  } catch (err) {
    console.error('发布主题失败', err)
    error.value = err?.message || '发布主题失败，请稍后重试'
  } finally {
    submitting.value = false
  }
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
  background: linear-gradient(135deg, #4361ee 0%, #2E7D32 100%);
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
