<template>
  <view class="container">
    <view class="loading" v-if="loading">加载证书中...</view>
    <view class="empty" v-else-if="error">{{ error }}</view>

    <template v-else-if="certificate">
      <view class="certificate-paper" :class="{ revoked: certificate.status !== 'valid' }">
        <view class="brand">🎖️ 校园实时互动社区</view>
        <view class="title">结业证书</view>
        <view class="subtitle">CERTIFICATE OF COMPLETION</view>

        <view class="user">{{ certificate.username }}</view>
        <view class="text">同学已完成课程</view>
        <view class="course">《{{ certificate.course_title }}》</view>
        <view class="text">的全部课时学习，经考核准予结业，特发此证。</view>

        <view class="footer">
          <view class="footer-item">
            <text class="footer-label">讲师</text>
            <text class="footer-value">{{ certificate.instructor_name }}</text>
          </view>
          <view class="footer-item">
            <text class="footer-label">颁发时间</text>
            <text class="footer-value">{{ formatDate(certificate.issued_at) }}</text>
          </view>
          <view class="footer-item">
            <text class="footer-label">证书编号</text>
            <text class="footer-value">{{ certificate.number }}</text>
          </view>
        </view>

        <view v-if="certificate.status !== 'valid'" class="revoked-mark">已撤销</view>
      </view>

      <view class="actions">
        <button class="action-btn" @click="copyNumber">复制证书编号</button>
      </view>
    </template>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import learningApi from '../../api/learning'

const certificate = ref(null)
const loading = ref(false)
const error = ref('')

onLoad((options) => {
  const id = Number(options?.id || 0)
  if (!id) {
    error.value = '参数错误'
    return
  }
  loadCertificate(id)
})

const loadCertificate = async (id) => {
  loading.value = true
  error.value = ''
  try {
    certificate.value = await learningApi.getCertificate(id)
  } catch (err) {
    console.error('加载证书失败', err)
    error.value = '证书不存在或无权查看'
  } finally {
    loading.value = false
  }
}

const copyNumber = () => {
  if (!certificate.value?.number) return
  uni.setClipboardData({
    data: certificate.value.number,
    success: () => uni.showToast({ title: '编号已复制', icon: 'success' })
  })
}

const formatDate = (value) => {
  if (!value) return ''
  const date = new Date(value)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}
</script>

<style scoped>
.container {
  min-height: 100vh;
  background-color: #f5f5f5;
  padding: 30rpx;
}

.loading,
.empty {
  text-align: center;
  padding: 120rpx 40rpx;
  color: #999;
  font-size: 28rpx;
}

.certificate-paper {
  position: relative;
  background-color: #fffdf7;
  border: 3rpx double #c9a227;
  border-radius: 20rpx;
  padding: 60rpx 40rpx;
  text-align: center;
  color: #3a3226;
}

.brand {
  font-size: 26rpx;
  color: #a8842a;
  letter-spacing: 2rpx;
}

.title {
  margin: 40rpx 0 10rpx;
  font-size: 56rpx;
  font-weight: 700;
  letter-spacing: 12rpx;
  color: #7a5f14;
}

.subtitle {
  font-size: 20rpx;
  letter-spacing: 6rpx;
  color: #b09a5a;
  margin-bottom: 50rpx;
}

.user {
  display: inline-block;
  font-size: 40rpx;
  font-weight: 600;
  padding: 0 40rpx 8rpx;
  border-bottom: 1rpx solid #d9c78e;
}

.text {
  font-size: 26rpx;
  color: #5b5140;
  margin: 20rpx 0;
}

.course {
  font-size: 34rpx;
  font-weight: 600;
  color: #7a5f14;
  margin: 12rpx 0;
}

.footer {
  margin-top: 60rpx;
  padding-top: 30rpx;
  border-top: 1rpx dashed #d9c78e;
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.footer-item {
  display: flex;
  justify-content: space-between;
  font-size: 24rpx;
}

.footer-label {
  color: #a08c56;
}

.footer-value {
  color: #3a3226;
  font-weight: 600;
}

.revoked-mark {
  position: absolute;
  top: 45%;
  left: 50%;
  transform: translate(-50%, -50%) rotate(-18deg);
  font-size: 72rpx;
  font-weight: 800;
  color: rgba(220, 38, 38, 0.18);
  border: 8rpx solid rgba(220, 38, 38, 0.18);
  border-radius: 20rpx;
  padding: 10rpx 40rpx;
}

.actions {
  margin-top: 30rpx;
}

.action-btn {
  width: 100%;
  height: 80rpx;
  line-height: 80rpx;
  border-radius: 40rpx;
  background-color: #fff;
  color: #4361ee;
  border: 1rpx solid #4361ee;
  font-size: 28rpx;
}
</style>
