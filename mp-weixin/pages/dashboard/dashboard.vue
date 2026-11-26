<template>
  <view class="container">
    <view class="toolbar">
      <text class="updated" v-if="lastUpdated">更新于 {{ formatDate(lastUpdated) }}</text>
      <view class="refresh-btn" @click="loadStats">刷新</view>
    </view>

    <view class="tip" v-if="loading">加载中...</view>
    <view class="tip empty" v-else-if="error">统计数据加载失败，请稍后重试</view>

    <template v-else>
      <!-- 概览 -->
      <view class="overview-grid">
        <view class="overview-card">
          <text class="card-icon">🏫</text>
          <text class="card-value">{{ stats.school_stats?.total_schools || 0 }}</text>
          <text class="card-label">学校总数</text>
        </view>
        <view class="overview-card">
          <text class="card-icon">💬</text>
          <text class="card-value">{{ stats.forum_stats?.total_posts || 0 }}</text>
          <text class="card-label">帖子总数</text>
        </view>
        <view class="overview-card">
          <text class="card-icon">📅</text>
          <text class="card-value">{{ stats.event_stats?.total_events || 0 }}</text>
          <text class="card-label">活动总数</text>
        </view>
        <view class="overview-card">
          <text class="card-icon">👥</text>
          <text class="card-value">{{ stats.user_stats?.total_users || 0 }}</text>
          <text class="card-label">用户总数</text>
        </view>
      </view>

      <!-- 近 7 天论坛活跃 -->
      <view class="section">
        <view class="section-title">近 7 天论坛活跃</view>
        <view class="inline-stats">
          <view class="inline-item">
            <text class="inline-value">{{ stats.forum_stats?.recent_posts || 0 }}</text>
            <text class="inline-label">新帖子</text>
          </view>
          <view class="inline-item">
            <text class="inline-value">{{ stats.forum_stats?.recent_comments || 0 }}</text>
            <text class="inline-label">新评论</text>
          </view>
        </view>
      </view>

      <!-- 分布数据 -->
      <template v-for="block in distributionBlocks" :key="block.key">
        <view class="section" v-if="block.items.length">
          <view class="section-title">{{ block.title }}</view>
          <view class="bar-item" v-for="item in block.items" :key="item.label">
            <view class="bar-head">
              <text class="bar-label">{{ item.label }}</text>
              <text class="bar-value">{{ item.value }}</text>
            </view>
            <view class="bar-track">
              <view class="bar-fill" :style="{ width: item.percent + '%' }"></view>
            </view>
          </view>
        </view>
      </template>
    </template>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onLoad, onPullDownRefresh } from '@dcloudio/uni-app'
import schoolApi from '../../api/school'

const stats = ref({})
const loading = ref(true)
const error = ref(false)
const lastUpdated = ref('')

onLoad(() => {
  loadStats()
})

onPullDownRefresh(() => {
  loadStats().finally(() => uni.stopPullDownRefresh())
})

const loadStats = async () => {
  loading.value = true
  error.value = false
  try {
    const result = await schoolApi.getDashboardStats()
    stats.value = result || {}
    lastUpdated.value = result?.last_updated || new Date().toISOString()
  } catch (err) {
    console.error('加载统计数据失败:', err)
    error.value = true
  } finally {
    loading.value = false
  }
}

// 把后端的分布数据归一化为 { label, value, percent }
const normalize = (list) => {
  const items = (Array.isArray(list) ? list : []).map((item) => ({
    label: item.name || item.province || item.activity_type || item.status || '其他',
    value: Number(item.value ?? item.count ?? 0)
  }))
  const max = Math.max(...items.map((item) => item.value), 1)
  return items
    .sort((a, b) => b.value - a.value)
    .map((item) => ({ ...item, percent: Math.round((item.value / max) * 100) }))
}

const distributionBlocks = computed(() => [
  {
    key: 'school_type',
    title: '学校类型分布',
    items: normalize(stats.value.school_stats?.type_distribution)
  },
  {
    key: 'school_level',
    title: '学校层次分布',
    items: normalize(stats.value.school_stats?.level_distribution)
  },
  {
    key: 'province',
    title: '省份分布',
    items: normalize(stats.value.school_stats?.province_distribution)
  },
  {
    key: 'event_status',
    title: '活动状态分布',
    items: normalize(stats.value.event_stats?.status_distribution)
  },
  {
    key: 'user_activity',
    title: '用户行为分布',
    items: normalize(stats.value.user_stats?.activity_stats)
  }
])

const formatDate = (value) => {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  const pad = (n) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}
</script>

<style scoped>
.container {
  min-height: 100vh;
  background-color: #f5f5f5;
  padding: 20rpx 30rpx 40rpx;
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20rpx;
}

.updated {
  font-size: 24rpx;
  color: #999;
}

.refresh-btn {
  padding: 10rpx 28rpx;
  border-radius: 30rpx;
  font-size: 24rpx;
  color: #4361ee;
  background-color: #eef1ff;
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20rpx;
}

.overview-card {
  background-color: #fff;
  border-radius: 16rpx;
  padding: 30rpx;
  display: flex;
  flex-direction: column;
}

.card-icon {
  font-size: 40rpx;
  margin-bottom: 16rpx;
}

.card-value {
  font-size: 40rpx;
  font-weight: 700;
  color: #333;
}

.card-label {
  font-size: 24rpx;
  color: #999;
  margin-top: 8rpx;
}

.section {
  background-color: #fff;
  border-radius: 16rpx;
  padding: 30rpx;
  margin-top: 20rpx;
}

.section-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 20rpx;
}

.inline-stats {
  display: flex;
}

.inline-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.inline-value {
  font-size: 36rpx;
  font-weight: 600;
  color: #4361ee;
  margin-bottom: 8rpx;
}

.inline-label {
  font-size: 24rpx;
  color: #999;
}

.bar-item {
  margin-bottom: 20rpx;
}

.bar-item:last-child {
  margin-bottom: 0;
}

.bar-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10rpx;
}

.bar-label {
  flex: 1;
  font-size: 26rpx;
  color: #666;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.bar-value {
  font-size: 26rpx;
  color: #333;
  margin-left: 16rpx;
}

.bar-track {
  height: 16rpx;
  border-radius: 8rpx;
  background-color: #f0f0f0;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 8rpx;
  background-color: #4361ee;
}

.tip {
  text-align: center;
  padding: 30rpx;
  color: #999;
  font-size: 26rpx;
}

.tip.empty {
  padding: 120rpx 30rpx;
}
</style>
