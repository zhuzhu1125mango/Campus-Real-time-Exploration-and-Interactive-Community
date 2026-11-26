<template>
  <view class="container">
    <!-- 状态筛选 -->
    <scroll-view class="status-scroll" scroll-x>
      <view class="status-list">
        <view
          class="status-chip"
          :class="{ active: activeStatus === item.value }"
          v-for="item in statusOptions"
          :key="item.value"
          @click="changeStatus(item.value)"
        >
          {{ item.label }}
        </view>
      </view>
    </scroll-view>

    <!-- 活动列表 -->
    <view class="event-list">
      <view
        class="event-card"
        v-for="event in events"
        :key="event.id"
        @click="openDetail(event)"
      >
        <view class="event-head">
          <text class="event-title">{{ event.title }}</text>
          <text class="status-tag" :class="event.status">{{ statusText(event.status) }}</text>
        </view>
        <view class="event-meta">🕒 {{ formatDateTime(event.start_time) }}</view>
        <view class="event-meta" v-if="event.location">📍 {{ event.location }}</view>
        <view class="event-meta" v-if="getSchoolName(event)">🏫 {{ getSchoolName(event) }}</view>
        <view class="event-foot">
          <text class="count">
            报名 {{ event.registration_count || 0 }}<text v-if="event.capacity">/{{ event.capacity }}</text>
          </text>
          <view
            v-if="event.is_registered"
            class="action-btn registered"
            @click.stop="cancelRegistration(event)"
          >
            取消报名
          </view>
          <view
            v-else-if="event.status === 'upcoming'"
            class="action-btn"
            @click.stop="registerEvent(event)"
          >
            立即报名
          </view>
          <text v-else class="action-disabled">不可报名</text>
        </view>
      </view>
    </view>

    <view class="tip" v-if="loading">加载中...</view>
    <view class="tip" v-else-if="noMore && events.length > 0">没有更多了</view>
    <view class="tip empty" v-else-if="events.length === 0">暂无活动</view>

    <!-- 活动详情 -->
    <view class="detail-mask" v-if="showDetail" @click="closeDetail">
      <view class="detail-panel" @click.stop>
        <view class="detail-head">
          <text class="detail-title">{{ detail.title }}</text>
          <text class="status-tag" :class="detail.status">{{ statusText(detail.status) }}</text>
        </view>
        <view class="detail-info">🕒 开始：{{ formatDateTime(detail.start_time) }}</view>
        <view class="detail-info">🕒 结束：{{ formatDateTime(detail.end_time) }}</view>
        <view class="detail-info" v-if="detail.location">📍 地点：{{ detail.location }}</view>
        <view class="detail-info" v-if="detail.organizer">👥 组织者：{{ detail.organizer }}</view>
        <view class="detail-info" v-if="getSchoolName(detail)">🏫 学校：{{ getSchoolName(detail) }}</view>
        <view class="detail-info">
          👥 报名人数：{{ detail.registration_count || 0 }}<text v-if="detail.capacity">/{{ detail.capacity }}</text>
        </view>
        <view class="detail-info" v-if="detail.registration_deadline">
          ⏰ 报名截止：{{ formatDateTime(detail.registration_deadline) }}
        </view>
        <view class="detail-desc-title">活动描述</view>
        <text class="detail-desc">{{ detail.description || '暂无描述' }}</text>
        <view class="detail-actions">
          <button class="btn-secondary" @click="closeDetail">关闭</button>
          <button
            v-if="detail.is_registered"
            class="btn-primary warn"
            :disabled="submitting"
            @click="cancelRegistration(detail)"
          >
            取消报名
          </button>
          <button
            v-else-if="detail.status === 'upcoming'"
            class="btn-primary"
            :disabled="submitting"
            @click="registerEvent(detail)"
          >
            立即报名
          </button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad, onPullDownRefresh, onReachBottom } from '@dcloudio/uni-app'
import schoolApi from '../../api/school'

const statusOptions = [
  { label: '全部', value: '' },
  { label: '即将开始', value: 'upcoming' },
  { label: '进行中', value: 'ongoing' },
  { label: '已完成', value: 'completed' }
]

const schoolId = ref(null)
const activeStatus = ref('')
const events = ref([])
const loading = ref(false)
const noMore = ref(false)
const submitting = ref(false)
const page = ref(1)
const pageSize = 10

const showDetail = ref(false)
const detail = ref({})

onLoad((options) => {
  if (options?.school_id) {
    schoolId.value = Number(options.school_id) || null
  }
  loadEvents()
})

onPullDownRefresh(() => {
  page.value = 1
  noMore.value = false
  events.value = []
  loadEvents()
})

onReachBottom(() => {
  if (!noMore.value && !loading.value) {
    page.value++
    loadEvents()
  }
})

const loadEvents = async () => {
  if (loading.value) return
  loading.value = true
  try {
    const params = { page: page.value, pageSize }
    if (activeStatus.value) params.status = activeStatus.value
    if (schoolId.value) params.school_id = schoolId.value

    const result = await schoolApi.getEvents(params)
    const list = result?.results || (Array.isArray(result) ? result : [])
    if (page.value === 1) {
      events.value = list
    } else {
      events.value = [...events.value, ...list]
    }
    const total = result?.count
    noMore.value = total !== undefined
      ? events.value.length >= total
      : list.length < pageSize
  } catch (error) {
    console.error('加载活动失败:', error)
    if (page.value > 1) page.value--
    uni.showToast({ title: '加载活动失败', icon: 'none' })
  } finally {
    loading.value = false
    uni.stopPullDownRefresh()
  }
}

const changeStatus = (status) => {
  if (activeStatus.value === status) return
  activeStatus.value = status
  page.value = 1
  noMore.value = false
  events.value = []
  loadEvents()
}

const openDetail = async (event) => {
  detail.value = { ...event }
  showDetail.value = true
  try {
    const result = await schoolApi.getEventDetail(event.id)
    if (result && result.id) {
      detail.value = result
    }
  } catch (error) {
    console.error('加载活动详情失败:', error)
  }
}

const closeDetail = () => {
  showDetail.value = false
  detail.value = {}
}

const ensureLogin = () => {
  const token = uni.getStorageSync('accessToken')
  if (!token) {
    uni.showToast({ title: '请先登录', icon: 'none' })
    setTimeout(() => {
      uni.navigateTo({ url: '/pages/login/login' })
    }, 800)
    return false
  }
  return true
}

const registerEvent = async (event) => {
  if (!ensureLogin() || submitting.value) return
  submitting.value = true
  try {
    await schoolApi.registerEvent(event.id)
    uni.showToast({ title: '报名成功', icon: 'success' })
    await refreshEvent(event.id)
  } catch (error) {
    console.error('报名失败:', error)
    uni.showToast({ title: error?.detail || '报名失败', icon: 'none' })
  } finally {
    submitting.value = false
  }
}

const cancelRegistration = async (event) => {
  if (!ensureLogin() || submitting.value) return
  submitting.value = true
  try {
    await schoolApi.cancelEventRegistration(event.id)
    uni.showToast({ title: '已取消报名', icon: 'success' })
    await refreshEvent(event.id)
  } catch (error) {
    console.error('取消报名失败:', error)
    uni.showToast({ title: error?.detail || '操作失败', icon: 'none' })
  } finally {
    submitting.value = false
  }
}

// 重新拉取单个活动，确保列表与详情状态一致
const refreshEvent = async (eventId) => {
  try {
    const result = await schoolApi.getEventDetail(eventId)
    if (!result || !result.id) return
    const index = events.value.findIndex((item) => item.id === eventId)
    if (index !== -1) {
      events.value.splice(index, 1, { ...events.value[index], ...result })
    }
    if (showDetail.value && detail.value.id === eventId) {
      detail.value = result
    }
  } catch (error) {
    console.error('刷新活动失败:', error)
  }
}

const getSchoolName = (event) => {
  if (!event) return ''
  if (typeof event.school === 'string') return event.school
  return event.school_name || event.school?.name || ''
}

const statusText = (status) => {
  switch (status) {
    case 'upcoming':
      return '即将开始'
    case 'ongoing':
      return '进行中'
    case 'completed':
      return '已完成'
    case 'cancelled':
      return '已取消'
    default:
      return status || ''
  }
}

const formatDateTime = (value) => {
  if (!value) return '-'
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
  padding-bottom: 40rpx;
}

.status-scroll {
  background-color: #fff;
  white-space: nowrap;
  padding: 20rpx 0;
}

.status-list {
  display: inline-flex;
  padding: 0 20rpx;
}

.status-chip {
  padding: 10rpx 30rpx;
  margin: 0 10rpx;
  border-radius: 30rpx;
  background-color: #f5f5f5;
  color: #666;
  font-size: 28rpx;
}

.status-chip.active {
  background-color: #4361ee;
  color: #fff;
}

.event-list {
  padding: 20rpx 30rpx;
}

.event-card {
  background-color: #fff;
  border-radius: 16rpx;
  padding: 30rpx;
  margin-bottom: 20rpx;
}

.event-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16rpx;
  margin-bottom: 16rpx;
}

.event-title {
  flex: 1;
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
}

.status-tag {
  flex-shrink: 0;
  font-size: 22rpx;
  padding: 6rpx 16rpx;
  border-radius: 8rpx;
  background-color: #eef1ff;
  color: #4361ee;
}

.status-tag.ongoing {
  background-color: #e8f5e9;
  color: #2e7d32;
}

.status-tag.completed {
  background-color: #f5f5f5;
  color: #999;
}

.status-tag.cancelled {
  background-color: #ffeaea;
  color: #e53935;
}

.event-meta {
  font-size: 26rpx;
  color: #666;
  margin-bottom: 10rpx;
}

.event-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 20rpx;
  padding-top: 20rpx;
  border-top: 1rpx solid #f0f0f0;
}

.count {
  font-size: 26rpx;
  color: #999;
}

.action-btn {
  padding: 10rpx 28rpx;
  border-radius: 30rpx;
  background-color: #4361ee;
  color: #fff;
  font-size: 26rpx;
}

.action-btn.registered {
  background-color: #fff;
  color: #ff9800;
  border: 1rpx solid #ff9800;
}

.action-disabled {
  font-size: 26rpx;
  color: #bbb;
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

.detail-mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  padding: 40rpx;
}

.detail-panel {
  width: 100%;
  max-height: 80vh;
  overflow-y: auto;
  background-color: #fff;
  border-radius: 20rpx;
  padding: 40rpx;
}

.detail-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16rpx;
  margin-bottom: 24rpx;
}

.detail-title {
  flex: 1;
  font-size: 34rpx;
  font-weight: 600;
  color: #333;
}

.detail-info {
  font-size: 26rpx;
  color: #666;
  margin-bottom: 12rpx;
}

.detail-desc-title {
  margin: 24rpx 0 12rpx;
  font-size: 28rpx;
  font-weight: 600;
  color: #333;
}

.detail-desc {
  display: block;
  font-size: 26rpx;
  color: #666;
  line-height: 1.7;
}

.detail-actions {
  display: flex;
  gap: 20rpx;
  margin-top: 30rpx;
}

.detail-actions button {
  flex: 1;
  height: 76rpx;
  line-height: 76rpx;
  border-radius: 38rpx;
  font-size: 28rpx;
}

.btn-primary {
  background-color: #4361ee;
  color: #fff;
  border: none;
}

.btn-primary.warn {
  background-color: #ff9800;
}

.btn-secondary {
  background-color: #f5f5f5;
  color: #333;
  border: none;
}
</style>
