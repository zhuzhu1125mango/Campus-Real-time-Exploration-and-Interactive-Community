<template>
  <view class="container">
    <!-- 顶部工具栏 -->
    <view class="toolbar">
      <view class="radius-control">
        <text class="radius-label">范围: {{ radius }}km</text>
        <slider
          class="radius-slider"
          :min="1"
          :max="20"
          :value="radius"
          :block-size="18"
          activeColor="#4361ee"
          backgroundColor="#e5e7eb"
          @change="onRadiusChange"
        />
      </view>
      <view class="toolbar-actions">
        <view class="tab-group">
          <view
            class="tab-item"
            :class="{ active: activeTab === 'places' }"
            @click="switchTab('places')"
          >附近地点</view>
          <view
            class="tab-item"
            :class="{ active: activeTab === 'events' }"
            @click="switchTab('events')"
          >附近活动</view>
        </view>
        <button class="locate-btn" :disabled="loadingLocation" @click="locateUser">
          {{ loadingLocation ? '定位中' : '重新定位' }}
        </button>
      </view>
    </view>

    <!-- 地图区域 -->
    <view class="map-section">
      <map
        v-if="mapCenter"
        class="map"
        :latitude="mapCenter.lat"
        :longitude="mapCenter.lng"
        :scale="14"
        :markers="markers"
        :circles="circles"
        :show-location="true"
        @markertap="onMarkerTap"
        @tap="onMapTap"
      />
      <view v-else class="map-loading">
        <view class="spinner"></view>
        <text>正在定位...</text>
      </view>
    </view>

    <!-- 分类筛选（地点） -->
    <scroll-view v-if="activeTab === 'places'" class="category-bar" scroll-x>
      <view
        v-for="item in categoryOptions"
        :key="item.value"
        class="category-item"
        :class="{ active: selectedCategory === item.value }"
        @click="onCategoryChange(item.value)"
      >
        {{ item.label }}
      </view>
    </scroll-view>

    <!-- 列表区域 -->
    <view class="list-section">
      <!-- 地点列表 -->
      <view v-if="activeTab === 'places'">
        <view class="section-title">附近地点</view>
        <scroll-view scroll-y class="place-list" @scrolltolower="onLoadMore">
          <view v-if="loadingPlaces" class="loading">
            <view class="spinner small"></view>
            <text>加载中...</text>
          </view>
          <view v-else-if="filteredPlaces.length === 0" class="empty">
            <text>附近暂无地点</text>
          </view>
          <view
            v-else
            v-for="place in filteredPlaces"
            :key="place.id"
            class="place-item"
            :class="{ active: selectedPlace && selectedPlace.id === place.id }"
            @click="selectPlace(place)"
          >
            <view class="place-main">
              <view class="place-header">
                <text class="place-name">{{ place.name }}</text>
                <text class="place-category">{{ place.category_display }}</text>
              </view>
              <text v-if="place.distance !== undefined" class="place-distance">{{ place.distance }}km</text>
              <text v-if="place.description" class="place-desc">{{ place.description }}</text>
            </view>
            <view class="place-badge">
              <text class="checkin-count">{{ place.checkin_count }} 打卡</text>
            </view>
          </view>
        </scroll-view>
      </view>

      <!-- 活动列表 -->
      <view v-else>
        <view class="section-title">附近活动</view>
        <scroll-view scroll-y class="event-list" @scrolltolower="onLoadMore">
          <view v-if="loadingEvents" class="loading">
            <view class="spinner small"></view>
            <text>加载中...</text>
          </view>
          <view v-else-if="events.length === 0" class="empty">
            <text>附近暂无活动</text>
          </view>
          <view
            v-else
            v-for="event in events"
            :key="event.id"
            class="event-item"
            @click="viewEvent(event)"
          >
            <view class="event-title">{{ event.title }}</view>
            <text class="event-meta">{{ event.school }} · {{ event.location }}</text>
            <text class="event-time">{{ formatTime(event.start_time) }} 开始</text>
          </view>
        </scroll-view>
      </view>
    </view>

    <!-- 地点详情与打卡弹窗 -->
    <view v-if="selectedPlace && activeTab === 'places'" class="detail-card">
      <view class="detail-header">
        <view>
          <text class="detail-name">{{ selectedPlace.name }}</text>
          <text class="detail-meta">{{ selectedPlace.category_display }} · {{ selectedPlace.distance !== undefined ? `${selectedPlace.distance}km` : '' }}</text>
        </view>
        <text class="close-btn" @click="selectedPlace = null">×</text>
      </view>
      <text v-if="selectedPlace.description" class="detail-desc">{{ selectedPlace.description }}</text>
      <text v-if="selectedPlace.address" class="detail-address">地址：{{ selectedPlace.address }}</text>
      <view v-if="!selectedPlace.is_checked_in_today" class="checkin-form">
        <input
          v-model="checkInNote"
          class="checkin-input"
          placeholder="写点打卡感想（可选）"
          maxlength="100"
        />
      </view>
      <button
        class="checkin-btn"
        :disabled="selectedPlace.is_checked_in_today || checkingIn"
        @click="handleCheckIn"
      >
        {{ selectedPlace.is_checked_in_today ? '今日已打卡' : (checkingIn ? '打卡中...' : '立即打卡') }}
      </button>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import schoolApi from '../../api/school'

const DEFAULT_LOCATION = { lat: 39.9042, lng: 116.4074 }
const categoryOptions = [
  { label: '全部', value: '' },
  { label: '地标', value: 'landmark' },
  { label: '教学楼', value: 'building' },
  { label: '宿舍', value: 'dormitory' },
  { label: '食堂', value: 'canteen' },
  { label: '图书馆', value: 'library' },
  { label: '体育场馆', value: 'sport' },
  { label: '活动场所', value: 'activity' },
  { label: '景点', value: 'scenic' },
  { label: '其他', value: 'other' }
]

const loadingLocation = ref(false)
const loadingPlaces = ref(false)
const loadingEvents = ref(false)
const checkingIn = ref(false)

const userLocation = ref(null)
const radius = ref(5)
const selectedCategory = ref('')
const activeTab = ref('places')
const selectedPlace = ref(null)

const places = ref([])
const events = ref([])
const checkInNote = ref('')

const mapCenter = computed(() => {
  return userLocation.value || DEFAULT_LOCATION
})

const filteredPlaces = computed(() => {
  if (!selectedCategory.value) return places.value
  return places.value.filter(p => p.category === selectedCategory.value)
})

const markers = computed(() => {
  const list = []
  if (userLocation.value) {
    list.push({
      id: 0,
      latitude: userLocation.value.lat,
      longitude: userLocation.value.lng,
      title: '我的位置',
      iconPath: '',
      width: 20,
      height: 20,
      callout: {
        content: '我的位置',
        color: '#000',
        fontSize: 12,
        borderRadius: 4,
        padding: 8,
        display: 'BYCLICK'
      }
    })
  }
  filteredPlaces.value.forEach((place, index) => {
    list.push({
      id: place.id,
      latitude: place.latitude,
      longitude: place.longitude,
      title: place.name,
      width: 28,
      height: 28,
      callout: {
        content: `${place.name}\n${place.category_display}${place.distance !== undefined ? ` · ${place.distance}km` : ''}`,
        color: '#000',
        fontSize: 12,
        borderRadius: 6,
        padding: 8,
        display: 'BYCLICK'
      }
    })
  })
  return list
})

const circles = computed(() => {
  if (!userLocation.value) return []
  return [{
    latitude: userLocation.value.lat,
    longitude: userLocation.value.lng,
    radius: radius.value * 1000,
    strokeWidth: 1,
    color: '#4361ee88',
    fillColor: '#4361ee22'
  }]
})

onMounted(() => {
  locateUser()
})

const locateUser = () => {
  loadingLocation.value = true
  uni.getLocation({
    type: 'gcj02',
    isHighAccuracy: true,
    highAccuracyExpireTime: 10000,
    success: (res) => {
      userLocation.value = { lat: res.latitude, lng: res.longitude }
      loadExploreData()
      loadingLocation.value = false
    },
    fail: () => {
      uni.showToast({ title: '无法获取当前位置，使用默认位置', icon: 'none' })
      userLocation.value = DEFAULT_LOCATION
      loadExploreData()
      loadingLocation.value = false
    }
  })
}

const loadExploreData = () => {
  fetchNearbyPlaces()
  fetchNearbyEvents()
}

const fetchNearbyPlaces = async () => {
  if (!userLocation.value) return
  loadingPlaces.value = true
  try {
    const params = {
      lat: userLocation.value.lat,
      lng: userLocation.value.lng,
      radius: radius.value
    }
    const data = await schoolApi.getNearbyPlaces(params)
    places.value = Array.isArray(data) ? data : []
  } catch (error) {
    console.error('获取附近地点失败:', error)
    uni.showToast({ title: '获取附近地点失败', icon: 'none' })
  } finally {
    loadingPlaces.value = false
  }
}

const fetchNearbyEvents = async () => {
  if (!userLocation.value) return
  loadingEvents.value = true
  try {
    const params = {
      lat: userLocation.value.lat,
      lng: userLocation.value.lng,
      radius: radius.value * 2
    }
    const data = await schoolApi.getNearbyEvents(params)
    events.value = Array.isArray(data) ? data : []
  } catch (error) {
    console.error('获取附近活动失败:', error)
    uni.showToast({ title: '获取附近活动失败', icon: 'none' })
  } finally {
    loadingEvents.value = false
  }
}

const onRadiusChange = (e) => {
  radius.value = e.detail.value
  loadExploreData()
}

const onCategoryChange = (value) => {
  selectedCategory.value = value
}

const switchTab = (tab) => {
  activeTab.value = tab
  selectedPlace.value = null
}

const selectPlace = (place) => {
  selectedPlace.value = place
}

const onMarkerTap = (e) => {
  const place = places.value.find(p => p.id === e.detail.markerId)
  if (place) {
    selectedPlace.value = place
  }
}

const onMapTap = () => {
  selectedPlace.value = null
}

const viewEvent = (event) => {
  // 小程序暂无活动详情页，跳转到院校详情
  if (event.school && event.school.id) {
    uni.navigateTo({ url: `/pages/school-detail/school-detail?id=${event.school.id}` })
  }
}

const handleCheckIn = async () => {
  const token = uni.getStorageSync('accessToken')
  if (!token) {
    uni.showModal({
      title: '提示',
      content: '登录后即可打卡，是否前往登录？',
      success: (res) => {
        if (res.confirm) {
          uni.navigateTo({ url: '/pages/login/login' })
        }
      }
    })
    return
  }
  if (!selectedPlace.value) return
  checkingIn.value = true
  try {
    await schoolApi.checkIn(selectedPlace.value.id, {
      latitude: userLocation.value?.lat,
      longitude: userLocation.value?.lng,
      note: checkInNote.value
    })
    uni.showToast({ title: `在 ${selectedPlace.value.name} 打卡成功，积分 +5`, icon: 'success' })
    selectedPlace.value.is_checked_in_today = true
    selectedPlace.value.checkin_count += 1
    checkInNote.value = ''
    fetchNearbyPlaces()
  } catch (error) {
    const msg = (error?.data?.detail) || '打卡失败'
    uni.showToast({ title: msg, icon: 'none' })
  } finally {
    checkingIn.value = false
  }
}

const onLoadMore = () => {
  // 当前后端为一次性返回，无需分页加载
}

const formatTime = (time) => {
  if (!time) return ''
  const date = new Date(time)
  const now = new Date()
  const diff = now - date
  if (diff < 86400000) return '今天'
  if (diff < 172800000) return '明天'
  return `${date.getMonth() + 1}月${date.getDate()}日 ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}
</script>

<style scoped>
.container {
  min-height: 100vh;
  background-color: #f5f5f5;
  display: flex;
  flex-direction: column;
}

.toolbar {
  background-color: #fff;
  padding: 20rpx 30rpx;
}

.radius-control {
  display: flex;
  align-items: center;
  gap: 20rpx;
  margin-bottom: 20rpx;
}

.radius-label {
  font-size: 26rpx;
  color: #333;
  white-space: nowrap;
}

.radius-slider {
  flex: 1;
  margin: 0;
}

.toolbar-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20rpx;
}

.tab-group {
  display: flex;
  background-color: #f3f4f6;
  border-radius: 8rpx;
  padding: 4rpx;
}

.tab-item {
  padding: 12rpx 24rpx;
  font-size: 26rpx;
  color: #666;
  border-radius: 6rpx;
}

.tab-item.active {
  background-color: #4361ee;
  color: #fff;
}

.locate-btn {
  margin: 0;
  padding: 12rpx 24rpx;
  font-size: 24rpx;
  background-color: #4361ee;
  color: #fff;
  border-radius: 8rpx;
  line-height: 1.4;
}

.locate-btn:disabled {
  opacity: 0.7;
}

.map-section {
  height: 400rpx;
  background-color: #e5e7eb;
  position: relative;
}

.map {
  width: 100%;
  height: 100%;
}

.map-loading,
.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #999;
  font-size: 26rpx;
  gap: 16rpx;
}

.spinner {
  width: 40rpx;
  height: 40rpx;
  border: 4rpx solid rgba(67, 97, 238, 0.3);
  border-radius: 50%;
  border-top-color: #4361ee;
  animation: spin 1s linear infinite;
}

.spinner.small {
  width: 32rpx;
  height: 32rpx;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.category-bar {
  white-space: nowrap;
  background-color: #fff;
  padding: 20rpx 30rpx;
  border-bottom: 1rpx solid #f3f4f6;
}

.category-item {
  display: inline-block;
  padding: 10rpx 24rpx;
  margin-right: 16rpx;
  font-size: 24rpx;
  color: #666;
  background-color: #f3f4f6;
  border-radius: 9999rpx;
}

.category-item.active {
  background-color: #4361ee;
  color: #fff;
}

.list-section {
  flex: 1;
  background-color: #fff;
  padding: 20rpx 30rpx;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.section-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 16rpx;
}

.place-list,
.event-list {
  flex: 1;
  height: 100%;
}

.place-item,
.event-item {
  padding: 24rpx;
  background-color: #f9fafc;
  border-radius: 12rpx;
  margin-bottom: 16rpx;
}

.place-item.active {
  background-color: #eef1ff;
}

.place-header {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-bottom: 8rpx;
}

.place-name,
.event-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #333;
}

.place-category {
  font-size: 22rpx;
  color: #4361ee;
  background-color: #eef1ff;
  padding: 4rpx 12rpx;
  border-radius: 6rpx;
}

.place-distance,
.event-meta,
.event-time {
  font-size: 24rpx;
  color: #999;
  margin-bottom: 8rpx;
}

.place-desc {
  font-size: 24rpx;
  color: #666;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.place-badge {
  margin-top: 12rpx;
}

.checkin-count {
  font-size: 22rpx;
  color: #4361ee;
  background-color: #eef1ff;
  padding: 4rpx 12rpx;
  border-radius: 9999rpx;
}

.empty {
  text-align: center;
  padding: 80rpx 0;
  color: #999;
  font-size: 28rpx;
}

.detail-card {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #fff;
  border-radius: 24rpx 24rpx 0 0;
  padding: 30rpx;
  box-shadow: 0 -4rpx 20rpx rgba(0, 0, 0, 0.1);
  z-index: 100;
  padding-bottom: calc(30rpx + env(safe-area-inset-bottom));
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16rpx;
}

.detail-name {
  display: block;
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 8rpx;
}

.detail-meta {
  font-size: 24rpx;
  color: #999;
}

.close-btn {
  font-size: 40rpx;
  color: #999;
  line-height: 1;
  padding: 0 10rpx;
}

.detail-desc,
.detail-address {
  font-size: 26rpx;
  color: #666;
  line-height: 1.6;
  margin-bottom: 16rpx;
}

.checkin-form {
  margin-bottom: 16rpx;
}

.checkin-input {
  width: 100%;
  height: 80rpx;
  background-color: #f3f4f6;
  border-radius: 8rpx;
  padding: 0 20rpx;
  font-size: 26rpx;
}

.checkin-btn {
  width: 100%;
  height: 80rpx;
  line-height: 80rpx;
  background-color: #10b981;
  color: #fff;
  font-size: 28rpx;
  border-radius: 12rpx;
}

.checkin-btn:disabled {
  background-color: #9ca3af;
}
</style>
