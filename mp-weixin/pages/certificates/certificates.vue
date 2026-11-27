<template>
  <view class="container">
    <view class="verify-card">
      <input
        class="verify-input"
        v-model="verifyNumber"
        placeholder="输入证书编号校验证书真伪"
        confirm-type="search"
        @confirm="verify"
      />
      <view class="verify-btn" @click="verify">{{ verifying ? '校验中' : '校验' }}</view>
    </view>
    <view v-if="verifyMessage" class="verify-result" :class="{ invalid: !verifyValid }">
      {{ verifyMessage }}
    </view>

    <view class="loading" v-if="loading">加载中...</view>
    <view class="empty" v-else-if="certificates.length === 0">
      <text>还没有证书，完成课程学习后即可获得</text>
      <view class="empty-btn" @click="goLearning">去学习</view>
    </view>

    <view v-else class="certificate-list">
      <view
        class="certificate-card"
        v-for="certificate in certificates"
        :key="certificate.id"
        @click="goDetail(certificate.id)"
      >
        <view class="certificate-icon">🎖️</view>
        <view class="certificate-info">
          <view class="course-title">{{ certificate.course_title }}</view>
          <view class="meta">讲师：{{ certificate.instructor_name }}</view>
          <view class="meta">编号：{{ certificate.number }}</view>
          <view class="meta">颁发时间：{{ formatDate(certificate.issued_at) }}</view>
        </view>
        <view class="certificate-side">
          <text class="status-tag" :class="certificate.status">
            {{ certificate.status === 'valid' ? '有效' : '已撤销' }}
          </text>
          <text class="arrow">></text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad, onPullDownRefresh } from '@dcloudio/uni-app'
import learningApi from '../../api/learning'

const certificates = ref([])
const loading = ref(false)
const verifyNumber = ref('')
const verifying = ref(false)
const verifyMessage = ref('')
const verifyValid = ref(false)

onLoad(() => {
  if (!uni.getStorageSync('accessToken')) {
    uni.showToast({ title: '请先登录', icon: 'none' })
    setTimeout(() => uni.navigateTo({ url: '/pages/login/login' }), 800)
    return
  }
  loadCertificates()
})

onPullDownRefresh(async () => {
  await loadCertificates()
  uni.stopPullDownRefresh()
})

const loadCertificates = async () => {
  loading.value = true
  try {
    const res = await learningApi.getCertificates()
    certificates.value = res?.results || []
  } catch (error) {
    console.error('加载证书失败', error)
    uni.showToast({ title: '加载证书失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

const verify = async () => {
  const number = verifyNumber.value.trim()
  if (!number) {
    uni.showToast({ title: '请输入证书编号', icon: 'none' })
    return
  }
  verifying.value = true
  verifyMessage.value = ''
  try {
    const certificate = await learningApi.verifyCertificate(number)
    verifyValid.value = certificate.status === 'valid'
    verifyMessage.value = verifyValid.value
      ? `校验通过：${certificate.username} 已完成《${certificate.course_title}》`
      : '该证书已被撤销'
  } catch (error) {
    console.error('校验证书失败', error)
    verifyValid.value = false
    verifyMessage.value = '未找到该证书，请检查编号是否正确'
  } finally {
    verifying.value = false
  }
}

const goDetail = (id) => {
  uni.navigateTo({ url: `/pages/certificate-detail/certificate-detail?id=${id}` })
}

const goLearning = () => {
  uni.switchTab({ url: '/pages/learning/learning' })
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
  padding: 20rpx 30rpx 40rpx;
}

.verify-card {
  display: flex;
  align-items: center;
  gap: 16rpx;
  background-color: #fff;
  border-radius: 16rpx;
  padding: 20rpx;
}

.verify-input {
  flex: 1;
  height: 68rpx;
  font-size: 26rpx;
  background-color: #f7f7f7;
  border-radius: 34rpx;
  padding: 0 24rpx;
}

.verify-btn {
  flex-shrink: 0;
  height: 68rpx;
  line-height: 68rpx;
  padding: 0 32rpx;
  border-radius: 34rpx;
  background-color: #4361ee;
  color: #fff;
  font-size: 26rpx;
}

.verify-result {
  margin-top: 16rpx;
  font-size: 24rpx;
  color: #27ae60;
}

.verify-result.invalid {
  color: #e53935;
}

.loading,
.empty {
  text-align: center;
  padding: 120rpx 40rpx;
  color: #999;
  font-size: 28rpx;
}

.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24rpx;
}

.empty-btn {
  background-color: #4361ee;
  color: #fff;
  font-size: 26rpx;
  padding: 12rpx 40rpx;
  border-radius: 30rpx;
}

.certificate-list {
  margin-top: 20rpx;
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.certificate-card {
  display: flex;
  align-items: center;
  gap: 20rpx;
  background-color: #fff;
  border-radius: 16rpx;
  padding: 28rpx;
}

.certificate-icon {
  font-size: 48rpx;
  flex-shrink: 0;
}

.certificate-info {
  flex: 1;
  min-width: 0;
}

.course-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 8rpx;
}

.meta {
  font-size: 24rpx;
  color: #999;
  line-height: 1.6;
}

.certificate-side {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 12rpx;
  flex-shrink: 0;
}

.status-tag {
  font-size: 22rpx;
  padding: 4rpx 16rpx;
  border-radius: 20rpx;
  background-color: #e8f5e9;
  color: #2e7d32;
}

.status-tag.revoked {
  background-color: #ffeaea;
  color: #e53935;
}

.arrow {
  color: #ccc;
  font-size: 26rpx;
}
</style>
