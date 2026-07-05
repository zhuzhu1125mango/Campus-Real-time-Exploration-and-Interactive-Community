<template>
  <view class="container">
    <view class="loading" v-if="loading">
      <text>加载中...</text>
    </view>
    <template v-else>
    <view class="school-header">
      <view class="school-name">{{ schoolInfo.name }}</view>
      <view class="school-tags">
        <text class="tag tag-level" v-if="schoolInfo.school_level">{{ schoolInfo.school_level }}</text>
        <text class="tag tag-type">{{ schoolInfo.school_type || schoolInfo.type }}</text>
      </view>
    </view>

    <view class="section">
      <view class="section-title">基本信息</view>
      <view class="info-grid">
        <view class="info-item">
          <text class="label">所在地</text>
          <text class="value">{{ schoolInfo.province }}</text>
        </view>
        <view class="info-item">
          <text class="label">院校类型</text>
          <text class="value">{{ schoolInfo.school_type || schoolInfo.type }}</text>
        </view>
        <view class="info-item">
          <text class="label">创办时间</text>
          <text class="value">{{ schoolInfo.founded_year || schoolInfo.founded }}</text>
        </view>
        <view class="info-item">
          <text class="label">院校性质</text>
          <text class="value">{{ schoolInfo.nature || '公立' }}</text>
        </view>
      </view>
    </view>

    <view class="section">
      <view class="section-title">历年分数线</view>
      <view class="score-list" v-if="scores.length > 0">
        <view class="score-item" v-for="score in scores" :key="score.id">
          <text class="year">{{ score.year }}年</text>
          <text class="score">最低分: {{ score.min_score }}</text>
          <text class="rank">位次: {{ score.rank || '-' }}</text>
        </view>
      </view>
      <view class="empty-tip" v-else>
        <text>暂无分数线数据</text>
      </view>
    </view>

    <view class="section">
      <view class="section-title">院校简介</view>
      <view class="description">
        <text>{{ schoolInfo.description || schoolInfo.intro || '暂无简介' }}</text>
      </view>
    </view>

    <view class="section" v-if="forumBoard || schoolInfo.board_id">
      <view class="section-title">学校论坛</view>
      <view class="forum-entry" @click="goToSchoolForum">
        <text class="forum-icon">💬</text>
        <view class="forum-info">
          <text class="forum-title">{{ schoolInfo.name }}论坛</text>
          <text class="forum-desc">校友交流、招生咨询、校园生活</text>
        </view>
        <text class="forum-arrow">→</text>
      </view>
    </view>

    <view class="action-bar">
      <button class="action-btn collect-btn" @click="toggleCollect">
        <text class="icon">{{ isCollected ? '❤️' : '🤍' }}</text>
        <text>{{ isCollected ? '已收藏' : '收藏' }}</text>
      </button>
      <button class="action-btn compare-btn" @click="addToCompare">
        <text class="icon">⚖️</text>
        <text>加入对比</text>
      </button>
    </view>
    </template>
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import schoolApi from '../../api/school'

const schoolId = ref(null)
const loading = ref(false)
const schoolInfo = ref({})
const scores = ref([])
const isCollected = ref(false)
const forumBoard = ref(null)

onMounted(() => {
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1]
  const options = currentPage.options || currentPage.$page?.options || {}
  schoolId.value = options.id

  if (schoolId.value) {
    loadSchoolDetail()
    loadAdmissionScores()
    loadSchoolForum()
  } else {
    uni.showToast({ title: '参数错误', icon: 'none' })
  }
})

const loadSchoolDetail = async () => {
  loading.value = true
  try {
    const result = await schoolApi.getSchoolDetail(schoolId.value)
    schoolInfo.value = result || {}
  } catch (error) {
    console.error('加载院校详情失败:', error)
    uni.showToast({ title: '加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

const loadAdmissionScores = async () => {
  try {
    const result = await schoolApi.getSchoolScores(schoolId.value)
    scores.value = (result && Array.isArray(result)) ? result : []
  } catch (error) {
    console.error('加载分数线失败:', error)
  }
}

const toggleCollect = async () => {
  const token = uni.getStorageSync('accessToken')
  if (!token) {
    uni.showToast({ title: '请先登录', icon: 'none' })
    setTimeout(() => {
      uni.navigateTo({ url: '/pages/login/login' })
    }, 1000)
    return
  }

  try {
    if (isCollected.value) {
      await schoolApi.unfavoriteSchool(schoolId.value)
      isCollected.value = false
      uni.showToast({ title: '已取消收藏', icon: 'success' })
    } else {
      await schoolApi.favoriteSchool(schoolId.value)
      isCollected.value = true
      uni.showToast({ title: '收藏成功', icon: 'success' })
    }
  } catch (error) {
    console.error('收藏操作失败:', error)
    uni.showToast({ title: '操作失败', icon: 'none' })
  }
}

const addToCompare = () => {
  uni.showToast({ title: '已加入对比栏', icon: 'success' })
}

const loadSchoolForum = async () => {
  try {
    const result = await schoolApi.getSchoolForum(schoolId.value)
    if (result && result.id) {
      forumBoard.value = result.id
    }
  } catch (error) {
    console.error('加载学校论坛失败:', error)
  }
}

const goToSchoolForum = () => {
  const boardId = forumBoard.value || schoolInfo.value.board_id
  if (!boardId) {
    uni.showToast({ title: '该学校暂无论坛', icon: 'none' })
    return
  }
  uni.navigateTo({ url: `/pages/forum/forum?boardId=${boardId}` })
}
</script>

<style scoped>
.container {
  min-height: 100vh;
  background-color: #f5f5f5;
  padding-bottom: 120rpx;
}

.school-header {
  background-color: #fff;
  padding: 40rpx 30rpx;
}

.school-name {
  font-size: 40rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 20rpx;
}

.school-tags {
  display: flex;
  gap: 15rpx;
}

.tag {
  font-size: 22rpx;
  padding: 6rpx 16rpx;
  border-radius: 6rpx;
}

.tag-985 {
  background-color: #ff4757;
  color: #fff;
}

.tag-211 {
  background-color: #ffa502;
  color: #fff;
}

.tag-type {
  background-color: #4CAF50;
  color: #fff;
}

.tag-level {
  background-color: #ff9800;
  color: #fff;
}

.loading {
  text-align: center;
  padding: 100rpx;
  color: #999;
}

.empty-tip {
  text-align: center;
  padding: 40rpx;
  color: #999;
}

.section {
  background-color: #fff;
  margin-top: 20rpx;
  padding: 30rpx;
}

.section-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 20rpx;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 30rpx;
}

.info-item {
  display: flex;
  flex-direction: column;
}

.label {
  font-size: 24rpx;
  color: #999;
  margin-bottom: 10rpx;
}

.value {
  font-size: 28rpx;
  color: #333;
}

.score-list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.score-item {
  display: flex;
  justify-content: space-between;
  padding: 20rpx;
  background-color: #f9f9f9;
  border-radius: 10rpx;
}

.year {
  font-size: 28rpx;
  color: #333;
}

.score {
  font-size: 28rpx;
  color: #4CAF50;
  font-weight: 500;
}

.rank {
  font-size: 28rpx;
  color: #999;
}

.description {
  font-size: 28rpx;
  color: #666;
  line-height: 1.8;
}

.forum-entry {
  display: flex;
  align-items: center;
  padding: 24rpx;
  background-color: #f9f9f9;
  border-radius: 12rpx;
}

.forum-icon {
  font-size: 48rpx;
  margin-right: 20rpx;
}

.forum-info {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.forum-title {
  font-size: 30rpx;
  color: #333;
  font-weight: 500;
  margin-bottom: 8rpx;
}

.forum-desc {
  font-size: 24rpx;
  color: #999;
}

.forum-arrow {
  font-size: 32rpx;
  color: #999;
}

.action-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  gap: 20rpx;
  padding: 20rpx 30rpx;
  background-color: #fff;
  box-shadow: 0 -2rpx 10rpx rgba(0, 0, 0, 0.05);
}

.action-btn {
  flex: 1;
  height: 80rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 40rpx;
  font-size: 28rpx;
  border: none;
}

.collect-btn {
  background-color: #fff;
  color: #333;
  border: 1rpx solid #ddd;
}

.compare-btn {
  background-color: #4CAF50;
  color: #fff;
}

.icon {
  margin-right: 10rpx;
}
</style>
