<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { ElMessage, ElMessageBox } from 'element-plus'
import { schoolApi } from '@/api/school'
import { useUserStore } from '@/stores/userStore'
import { getApiErrorMessage } from '@/utils/error'
import type { Place, Event as SchoolEvent, PlaceCategory } from '@/types/school'
import GlassCard from '@/components/GlassCard.vue'
import SectionHeader from '@/components/SectionHeader.vue'

const router = useRouter()
const userStore = useUserStore()

const DEFAULT_LOCATION = { lat: 39.9042, lng: 116.4074 }
const categoryOptions: { label: string; value: PlaceCategory | '' }[] = [
  { label: '全部', value: '' },
  { label: '地标', value: 'landmark' },
  { label: '教学楼', value: 'building' },
  { label: '宿舍', value: 'dormitory' },
  { label: '食堂', value: 'canteen' },
  { label: '图书馆', value: 'library' },
  { label: '体育场馆', value: 'sport' },
  { label: '活动场所', value: 'activity' },
  { label: '景点', value: 'scenic' },
  { label: '其他', value: 'other' },
]

const mapContainer = ref<HTMLElement | null>(null)
let map: L.Map | null = null
let markers: L.Marker[] = []
let userMarker: L.Marker | null = null

const loadingLocation = ref(false)
const loadingPlaces = ref(false)
const loadingEvents = ref(false)
const checkingIn = ref(false)

const userLocation = ref<{ lat: number; lng: number } | null>(null)
const radius = ref(5)
const selectedCategory = ref<PlaceCategory | ''>('')
const activeTab = ref<'places' | 'events'>('places')
const selectedPlace = ref<Place | null>(null)

const places = ref<Place[]>([])
const events = ref<SchoolEvent[]>([])
const checkInNote = ref('')

const isLoggedIn = computed(() => userStore.isLoggedIn)

const filteredPlaces = computed(() => {
  if (!selectedCategory.value) return places.value
  return places.value.filter(p => p.category === selectedCategory.value)
})

const initMap = () => {
  if (!mapContainer.value || map) return
  const center = userLocation.value || DEFAULT_LOCATION
  map = L.map(mapContainer.value).setView([center.lat, center.lng], 14)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(map)
  map.on('click', () => {
    selectedPlace.value = null
  })
}

const updateUserMarker = () => {
  if (!map || !userLocation.value) return
  const icon = L.divIcon({
    className: 'user-location-marker',
    html: '<div class="user-dot"></div><div class="user-pulse"></div>',
    iconSize: [20, 20],
    iconAnchor: [10, 10]
  })
  if (userMarker) {
    userMarker.setLatLng([userLocation.value.lat, userLocation.value.lng])
  } else {
    userMarker = L.marker([userLocation.value.lat, userLocation.value.lng], { icon }).addTo(map)
  }
}

const getCategoryIcon = (category: PlaceCategory) => {
  const mapColors: Record<PlaceCategory, string> = {
    landmark: '#f59e0b',
    building: '#3b82f6',
    dormitory: '#8b5cf6',
    canteen: '#ef4444',
    library: '#10b981',
    sport: '#06b6d4',
    activity: '#f97316',
    scenic: '#84cc16',
    other: '#6b7280'
  }
  return L.divIcon({
    className: 'place-marker',
    html: `<div class="marker-pin" style="background-color: ${mapColors[category] || mapColors.other}"></div>`,
    iconSize: [28, 28],
    iconAnchor: [14, 28]
  })
}

const renderMarkers = () => {
  if (!map) return
  markers.forEach(m => map!.removeLayer(m))
  markers = []

  filteredPlaces.value.forEach(place => {
    const marker = L.marker([place.latitude, place.longitude], { icon: getCategoryIcon(place.category) })
      .addTo(map!)
      .bindPopup(`<b>${place.name}</b><br/>${place.category_display}${place.distance !== undefined ? ` · ${place.distance}km` : ''}`)
    marker.on('click', () => {
      selectedPlace.value = place
      map!.panTo([place.latitude, place.longitude])
    })
    markers.push(marker)
  })
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
    places.value = data || []
    renderMarkers()
  } catch (error) {
    console.error('获取附近地点失败:', error)
    ElMessage.error('获取附近地点失败')
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
    events.value = data || []
  } catch (error) {
    console.error('获取附近活动失败:', error)
    ElMessage.error('获取附近活动失败')
  } finally {
    loadingEvents.value = false
  }
}

const loadExploreData = () => {
  fetchNearbyPlaces()
  fetchNearbyEvents()
}

const locateUser = () => {
  loadingLocation.value = true
  if (!navigator.geolocation) {
    ElMessage.warning('浏览器不支持定位，使用默认位置')
    userLocation.value = DEFAULT_LOCATION
    initMap()
    updateUserMarker()
    loadExploreData()
    loadingLocation.value = false
    return
  }
  navigator.geolocation.getCurrentPosition(
    position => {
      userLocation.value = {
        lat: position.coords.latitude,
        lng: position.coords.longitude
      }
      nextTick(() => {
        initMap()
        updateUserMarker()
        loadExploreData()
      })
      loadingLocation.value = false
    },
    error => {
      console.error('定位失败:', error)
      ElMessage.warning('无法获取当前位置，使用默认位置')
      userLocation.value = DEFAULT_LOCATION
      nextTick(() => {
        initMap()
        updateUserMarker()
        loadExploreData()
      })
      loadingLocation.value = false
    },
    { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 }
  )
}

const onRadiusChange = () => {
  loadExploreData()
}

const onCategoryChange = () => {
  renderMarkers()
}

const selectPlace = (place: Place) => {
  selectedPlace.value = place
  if (map) {
    map.panTo([place.latitude, place.longitude])
    const marker = markers.find(m => {
      const latLng = m.getLatLng()
      return latLng.lat === place.latitude && latLng.lng === place.longitude
    })
    if (marker) marker.openPopup()
  }
}

const viewEvent = (_event: SchoolEvent) => {
  router.push({ name: 'Events' })
}

const handleCheckIn = async () => {
  if (!isLoggedIn.value) {
    ElMessageBox.confirm('登录后即可打卡，是否前往登录？', '提示', { type: 'info' })
      .then(() => router.push('/login'))
      .catch(() => {})
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
    ElMessage.success(`在 ${selectedPlace.value.name} 打卡成功，积分 +5`)
    selectedPlace.value.is_checked_in_today = true
    selectedPlace.value.checkin_count += 1
    checkInNote.value = ''
    fetchNearbyPlaces()
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '打卡失败'))
  } finally {
    checkingIn.value = false
  }
}

onMounted(() => {
  locateUser()
})

onUnmounted(() => {
  if (map) {
    map.remove()
    map = null
  }
})
</script>

<template>
  <div class="explore-page container-wide page-padding">
    <SectionHeader
      title="校园探索"
      subtitle="发现附近地点、活动，打卡解锁积分"
      icon="i-mdi-map-marker-radius"
    />

    <GlassCard class="toolbar-card" :hover="false">
      <div class="explore-toolbar">
        <div class="toolbar-left">
          <label class="toolbar-label">范围: {{ radius }}km</label>
          <input
            type="range"
            min="1"
            max="20"
            v-model.number="radius"
            @change="onRadiusChange"
            class="radius-slider"
          />
        </div>
        <div class="toolbar-center">
          <button
            class="tab-btn"
            :class="{ active: activeTab === 'places' }"
            @click="activeTab = 'places'"
          >
            附近地点
          </button>
          <button
            class="tab-btn"
            :class="{ active: activeTab === 'events' }"
            @click="activeTab = 'events'"
          >
            附近活动
          </button>
        </div>
        <div class="toolbar-right">
          <button class="locate-btn" @click="locateUser" :disabled="loadingLocation">
            <span class="btn-icon i-mdi-crosshairs-gps" />
            {{ loadingLocation ? '定位中...' : '重新定位' }}
          </button>
        </div>
      </div>
    </GlassCard>

    <div class="explore-body">
      <div class="map-section">
        <div ref="mapContainer" class="map-container"></div>
        <div v-if="loadingLocation" class="map-overlay">
          <div class="spinner"></div>
          <p>正在定位...</p>
        </div>
      </div>

      <aside class="sidebar">
        <GlassCard v-if="activeTab === 'places'" class="panel-card" :hover="false">
          <div class="filter-row">
            <select v-model="selectedCategory" @change="onCategoryChange" class="category-select">
              <option v-for="opt in categoryOptions" :key="opt.value" :value="opt.value">
                {{ opt.label }}
              </option>
            </select>
          </div>

          <div v-if="loadingPlaces" class="panel-loading">
            <el-skeleton :rows="5" animated />
          </div>
          <div v-else-if="filteredPlaces.length === 0" class="panel-empty">
            <span class="empty-icon i-mdi-map-marker-off-outline" />
            <p>附近暂无地点</p>
          </div>
          <ul v-else class="place-list">
            <li
              v-for="place in filteredPlaces"
              :key="place.id"
              class="place-item"
              :class="{ active: selectedPlace?.id === place.id }"
              @click="selectPlace(place)"
            >
              <div class="place-info">
                <h4>{{ place.name }}</h4>
                <span class="place-meta">{{ place.category_display }} {{ place.distance !== undefined ? `· ${place.distance}km` : '' }}</span>
                <p v-if="place.description" class="place-desc">{{ place.description }}</p>
              </div>
              <div class="place-badge">
                <span class="checkin-count">{{ place.checkin_count }} 打卡</span>
              </div>
            </li>
          </ul>
        </GlassCard>

        <GlassCard v-else class="panel-card" :hover="false">
          <div v-if="loadingEvents" class="panel-loading">
            <el-skeleton :rows="5" animated />
          </div>
          <div v-else-if="events.length === 0" class="panel-empty">
            <span class="empty-icon i-mdi-calendar-blank-outline" />
            <p>附近暂无活动</p>
          </div>
          <ul v-else class="event-list">
            <li v-for="event in events" :key="event.id" class="event-item" @click="viewEvent(event)">
              <h4>{{ event.title }}</h4>
              <p class="event-meta">{{ event.school }} · {{ event.location }}</p>
              <p class="event-time">{{ event.start_time }} 开始</p>
            </li>
          </ul>
        </GlassCard>

        <GlassCard v-if="selectedPlace && activeTab === 'places'" class="detail-card" :hover="false">
          <h3 class="detail-title">{{ selectedPlace.name }}</h3>
          <p class="detail-meta">{{ selectedPlace.category_display }} · {{ selectedPlace.distance !== undefined ? `${selectedPlace.distance}km` : '' }}</p>
          <p v-if="selectedPlace.description" class="detail-desc">{{ selectedPlace.description }}</p>
          <p v-if="selectedPlace.address" class="detail-address">
            <span class="label">地址:</span> {{ selectedPlace.address }}
          </p>
          <div class="detail-actions">
            <button
              class="checkin-btn"
              :disabled="selectedPlace.is_checked_in_today || checkingIn"
              @click="handleCheckIn"
            >
              <span v-if="!selectedPlace.is_checked_in_today" class="btn-icon i-mdi-check-circle-outline" />
              {{ selectedPlace.is_checked_in_today ? '今日已打卡' : (checkingIn ? '打卡中...' : '立即打卡') }}
            </button>
          </div>
          <div v-if="!selectedPlace.is_checked_in_today" class="checkin-note">
            <input v-model="checkInNote" placeholder="写点打卡感想（可选）" maxlength="100" />
          </div>
        </GlassCard>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.explore-page {
  max-width: 1400px;
}

.toolbar-card {
  margin-bottom: var(--space-6);
}

.explore-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  flex-wrap: wrap;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.toolbar-label {
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--text-primary);
  white-space: nowrap;
}

.radius-slider {
  width: 150px;
  accent-color: var(--primary-500);
}

.toolbar-center {
  display: flex;
  gap: var(--space-2);
}

.tab-btn {
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-md);
  font-weight: 500;
  color: var(--text-secondary);
  background: var(--bg-tertiary);
  transition: all 0.2s;
}

.tab-btn.active {
  background: var(--primary-500);
  color: var(--text-inverse);
}

.locate-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-md);
  background: var(--primary-500);
  color: var(--text-inverse);
  font-weight: 500;
  transition: opacity 0.2s;
}

.locate-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.btn-icon {
  width: 18px;
  height: 18px;
}

.explore-body {
  display: grid;
  grid-template-columns: 1fr 360px;
  gap: var(--space-6);
  min-height: 600px;
}

.map-section {
  position: relative;
  border-radius: var(--radius-xl);
  overflow: hidden;
  background: var(--bg-primary);
  border: 1px solid var(--glass-border);
  box-shadow: var(--shadow-card);
}

.map-container {
  width: 100%;
  height: 100%;
  min-height: 600px;
}

.map-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: var(--glass-bg);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  gap: var(--space-4);
  color: var(--text-primary);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(67, 97, 238, 0.3);
  border-radius: 50%;
  border-top-color: var(--primary-500);
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.sidebar {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.panel-card {
  flex: 1;
  min-height: 300px;
  display: flex;
  flex-direction: column;
}

.filter-row {
  margin-bottom: var(--space-4);
}

.category-select {
  width: 100%;
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  font-size: 0.9rem;
  color: var(--text-primary);
  background: var(--bg-primary);
  outline: none;
  transition: border-color 0.2s;
}

.category-select:focus {
  border-color: var(--primary-500);
}

.panel-loading {
  flex: 1;
}

.panel-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  color: var(--text-tertiary);
}

.empty-icon {
  width: 48px;
  height: 48px;
}

.place-list,
.event-list {
  list-style: none;
  overflow-y: auto;
  flex: 1;
  padding-right: var(--space-2);
}

.place-item,
.event-item {
  padding: var(--space-3);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background 0.2s;
  margin-bottom: var(--space-2);
}

.place-item:hover,
.event-item:hover,
.place-item.active {
  background: var(--primary-50);
}

.dark .place-item:hover,
.dark .event-item:hover,
.dark .place-item.active {
  background: rgba(37, 99, 235, 0.12);
}

.place-info h4,
.event-item h4 {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--space-1);
}

.place-meta,
.event-meta {
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.place-desc,
.event-time {
  font-size: 0.85rem;
  color: var(--text-tertiary);
  margin-top: var(--space-1);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.place-badge {
  margin-top: var(--space-2);
}

.checkin-count {
  font-size: 0.75rem;
  color: var(--primary-600);
  background: var(--primary-50);
  padding: 2px 8px;
  border-radius: var(--radius-full);
}

.dark .checkin-count {
  color: var(--primary-400);
  background: rgba(37, 99, 235, 0.12);
}

.detail-card {
  padding: var(--space-5);
}

.detail-title {
  font-size: 1.2rem;
  font-weight: 700;
  margin-bottom: var(--space-2);
  color: var(--text-primary);
}

.detail-meta {
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin-bottom: var(--space-3);
}

.detail-desc,
.detail-address {
  font-size: 0.9rem;
  color: var(--text-primary);
  margin-bottom: var(--space-3);
  line-height: 1.5;
}

.detail-address .label {
  color: var(--text-secondary);
}

.detail-actions {
  margin-bottom: var(--space-3);
}

.checkin-btn {
  width: 100%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-3);
  border-radius: var(--radius-md);
  background: var(--success-color);
  color: var(--text-inverse);
  font-weight: 600;
  transition: opacity 0.2s;
}

.checkin-btn:disabled {
  background: var(--text-tertiary);
  cursor: not-allowed;
}

.checkin-note input {
  width: 100%;
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  font-size: 0.9rem;
  color: var(--text-primary);
  background: var(--bg-primary);
  outline: none;
  transition: border-color 0.2s;
}

.checkin-note input:focus {
  border-color: var(--primary-500);
}

@media (max-width: 1024px) {
  .explore-body {
    grid-template-columns: 1fr;
  }

  .map-container {
    min-height: 400px;
  }
}

@media (max-width: 640px) {
  .explore-toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .toolbar-left,
  .toolbar-center,
  .toolbar-right {
    justify-content: center;
  }
}
</style>

<style>
.place-marker .marker-pin {
  width: 28px;
  height: 28px;
  border-radius: 50% 50% 50% 0;
  transform: rotate(-45deg);
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3);
}

.user-location-marker {
  position: relative;
}

.user-dot {
  width: 12px;
  height: 12px;
  background: #3b82f6;
  border-radius: 50%;
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 2;
}

.user-pulse {
  width: 24px;
  height: 24px;
  background: rgba(59, 130, 246, 0.3);
  border-radius: 50%;
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0% { transform: translate(-50%, -50%) scale(1); opacity: 0.6; }
  100% { transform: translate(-50%, -50%) scale(2); opacity: 0; }
}
</style>
