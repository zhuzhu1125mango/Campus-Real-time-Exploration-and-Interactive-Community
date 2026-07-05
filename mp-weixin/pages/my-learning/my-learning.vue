<template>
  <view class="container">
    <!-- 顶部 -->
    <view class="header">
      <view class="header-title">我的学习</view>
      <view class="header-desc">管理你的课程学习进度</view>
    </view>

    <view class="learning-body">
      <view class="loading-state" v-if="loading">
        <text>加载中...</text>
      </view>

      <template v-else>
        <view v-if="enrollments.length === 0" class="empty-state">
          <text>你还没有报名任何课程</text>
          <button class="empty-btn" @click="goLearning">去发现课程</button>
        </view>

        <view v-else class="enrollment-list">
          <view
            class="enrollment-card"
            v-for="enrollment in enrollments"
            :key="enrollment.id"
            @click="goCourse(enrollment.course.id)"
          >
            <image
              class="enrollment-cover"
              :src="enrollment.course.cover_image || defaultCover"
              mode="aspectFill"
            />
            <view class="enrollment-info">
              <view class="course-title">{{ enrollment.course.title }}</view>
              <view class="course-desc">{{ enrollment.course.description?.substring(0, 60) }}...</view>
              <view class="progress-bar">
                <view class="progress-fill" :style="{ width: `${enrollment.progress || 0}%` }"></view>
              </view>
              <view class="progress-meta">
                <text>学习进度 {{ (enrollment.progress || 0).toFixed(0) }}%</text>
                <text v-if="enrollment.is_completed" class="completed-badge">已完成</text>
                <text v-else>学习中</text>
              </view>
            </view>
            <view class="enrollment-action">
              <button class="action-btn" @click.stop="goCourse(enrollment.course.id)">
                {{ enrollment.is_completed ? '复习' : '继续学习' }}
              </button>
            </view>
          </view>
        </view>
      </template>
    </view>
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import learningApi from '../../api/learning'

const defaultCover = 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=campus%20online%20course%20cover%20image&image_size=landscape_16_9'

const enrollments = ref([])
const loading = ref(false)

onMounted(() => {
  loadEnrollments()
})

const loadEnrollments = async () => {
  loading.value = true
  try {
    const res = await learningApi.getEnrollments()
    enrollments.value = res.results || []
  } catch (error) {
    console.error('加载学习记录失败', error)
    uni.showToast({ title: '加载学习记录失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

const goCourse = (courseId) => {
  uni.navigateTo({ url: `/pages/course-detail/course-detail?id=${courseId}` })
}

const goLearning = () => {
  uni.switchTab({ url: '/pages/learning/learning' })
}

// 下拉刷新
const onPullDownRefresh = async () => {
  await loadEnrollments()
  uni.stopPullDownRefresh()
}
</script>

<style scoped>
.container {
  min-height: 100vh;
  background-color: #f5f5f5;
}

.header {
  background: linear-gradient(135deg, #4361ee 0%, #3a56d4 100%);
  color: #fff;
  padding: 60rpx 30rpx;
  text-align: center;
}

.header-title {
  font-size: 44rpx;
  font-weight: 700;
  margin-bottom: 12rpx;
}

.header-desc {
  font-size: 26rpx;
  opacity: 0.9;
}

.learning-body {
  padding: 30rpx;
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 120rpx 40rpx;
  color: #999;
  font-size: 28rpx;
}

.empty-btn {
  margin-top: 30rpx;
  background-color: #4361ee;
  color: #fff;
  font-size: 26rpx;
  padding: 12rpx 40rpx;
  border-radius: 30rpx;
  border: none;
}

.enrollment-list {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.enrollment-card {
  display: flex;
  align-items: center;
  gap: 24rpx;
  background-color: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
}

.enrollment-cover {
  width: 160rpx;
  height: 110rpx;
  border-radius: 10rpx;
  flex-shrink: 0;
}

.enrollment-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.course-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #333;
}

.course-desc {
  font-size: 24rpx;
  color: #666;
  line-height: 1.4;
}

.progress-bar {
  height: 12rpx;
  background-color: #e8e8e8;
  border-radius: 6rpx;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background-color: #4361ee;
  border-radius: 6rpx;
}

.progress-meta {
  display: flex;
  justify-content: space-between;
  font-size: 24rpx;
  color: #666;
}

.completed-badge {
  color: #27ae60;
  font-weight: 600;
}

.enrollment-action {
  flex-shrink: 0;
}

.action-btn {
  background-color: #4361ee;
  color: #fff;
  font-size: 24rpx;
  padding: 10rpx 24rpx;
  border-radius: 30rpx;
  border: none;
}
</style>
