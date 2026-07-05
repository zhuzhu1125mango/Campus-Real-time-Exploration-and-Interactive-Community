<template>
  <view class="container">
    <view class="loading" v-if="loading && schools.length === 0">
      <text>加载中...</text>
    </view>

    <view class="empty-tip" v-else-if="!loading && schools.length === 0">
      <text>暂无收藏院校</text>
      <button class="browse-btn" @click="goToSchools">去浏览院校</button>
    </view>

    <scroll-view v-else class="school-list" scroll-y @scrolltolower="loadMore">
      <view class="school-card" v-for="school in schools" :key="school.id" @click="viewSchoolDetail(school.id)">
        <view class="school-header">
          <view class="school-name">{{ school.name }}</view>
          <view class="school-tags">
            <text class="tag tag-level" v-if="school.school_level">{{ school.school_level }}</text>
          </view>
        </view>
        <view class="school-info">
          <text class="info-item">📍 {{ school.province }}</text>
          <text class="info-item">🎓 {{ school.school_type || school.type }}</text>
        </view>
        <view class="school-rank" v-if="school.national_rank">
          <text class="rank-label">全国排名:</text>
          <text class="rank-value">{{ school.national_rank }}</text>
        </view>
      </view>

      <view class="loading-more" v-if="loading && schools.length > 0">
        <text>加载中...</text>
      </view>
      <view class="no-more" v-if="noMore && schools.length > 0">
        <text>没有更多了</text>
      </view>
    </scroll-view>
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import schoolApi from '../../api/school'

const schools = ref([])
const loading = ref(false)
const noMore = ref(false)
const page = ref(1)

onMounted(() => {
  checkAuthAndLoad()
})

const checkAuthAndLoad = () => {
  const token = uni.getStorageSync('accessToken')
  if (!token) {
    uni.showToast({ title: '请先登录', icon: 'none' })
    setTimeout(() => {
      uni.navigateTo({ url: '/pages/login/login' })
    }, 1000)
    return
  }
  loadFavorites()
}

const loadFavorites = async () => {
  if (loading.value) return
  loading.value = true

  try {
    const result = await schoolApi.getMyFavorites()
    if (Array.isArray(result)) {
      schools.value = result
      noMore.value = true
    } else if (result && result.results) {
      if (page.value === 1) {
        schools.value = result.results
      } else {
        schools.value = [...schools.value, ...result.results]
      }
      noMore.value = page.value >= (result.total_pages || 1)
    } else {
      schools.value = []
      noMore.value = true
    }
  } catch (error) {
    console.error('获取收藏院校失败:', error)
    uni.showToast({ title: '加载失败', icon: 'none' })
    schools.value = []
  } finally {
    loading.value = false
  }
}

const loadMore = () => {
  if (!noMore.value && !loading.value) {
    page.value++
    loadFavorites()
  }
}

const viewSchoolDetail = (id) => {
  uni.navigateTo({ url: `/pages/school-detail/school-detail?id=${id}` })
}

const goToSchools = () => {
  uni.switchTab({ url: '/pages/schools/schools' })
}
</script>

<style scoped>
.container {
  min-height: 100vh;
  background-color: #f5f5f5;
}

.loading,
.empty-tip {
  text-align: center;
  padding: 100rpx 30rpx;
  color: #999;
  font-size: 28rpx;
}

.empty-tip {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.browse-btn {
  margin-top: 40rpx;
  background-color: #4CAF50;
  color: #fff;
  font-size: 28rpx;
  padding: 15rpx 50rpx;
  border-radius: 40rpx;
  border: none;
}

.school-list {
  height: 100vh;
  padding: 20rpx 30rpx;
}

.school-card {
  background-color: #fff;
  border-radius: 16rpx;
  padding: 30rpx;
  margin-bottom: 20rpx;
}

.school-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20rpx;
}

.school-name {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
}

.school-tags {
  display: flex;
  gap: 10rpx;
}

.tag {
  font-size: 20rpx;
  padding: 4rpx 12rpx;
  border-radius: 4rpx;
}

.tag-level {
  background-color: #4CAF50;
  color: #fff;
}

.school-info {
  display: flex;
  gap: 30rpx;
  margin-bottom: 20rpx;
}

.info-item {
  font-size: 26rpx;
  color: #666;
}

.school-rank {
  display: flex;
  align-items: center;
  padding-top: 20rpx;
  border-top: 1rpx solid #f0f0f0;
}

.rank-label {
  font-size: 26rpx;
  color: #999;
  margin-right: 10rpx;
}

.rank-value {
  font-size: 32rpx;
  font-weight: 600;
  color: #4CAF50;
}

.loading-more,
.no-more {
  text-align: center;
  padding: 30rpx;
  color: #999;
  font-size: 26rpx;
}
</style>
