<template>
  <view class="container">
    <!-- 搜索区域 -->
    <view class="search-wrapper">
      <view class="search-box">
        <input
          type="text"
          v-model="keyword"
          placeholder="搜索院校名称"
          class="search-input"
          @confirm="handleSearch"
        />
        <button class="search-btn" @click="handleSearch">搜索</button>
      </view>
    </view>

    <!-- 筛选区域 -->
    <view class="filter-wrapper">
      <view class="filter-item" @click="showProvincePicker">
        <text>{{ selectedProvince || '省份' }}</text>
        <text class="arrow">▼</text>
      </view>
      <view class="filter-item" @click="showTypePicker">
        <text>{{ selectedType || '类型' }}</text>
        <text class="arrow">▼</text>
      </view>
    </view>

    <!-- 院校列表 -->
    <scroll-view class="school-list" scroll-y @scrolltolower="loadMore">
      <view class="loading-more" v-if="loading && schools.length === 0">
        <text>加载中...</text>
      </view>
      <view
        class="school-card"
        v-for="school in schools"
        :key="school.id"
        @click="viewSchoolDetail(school.id)"
      >
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
      <view class="empty" v-if="!loading && schools.length === 0">
        <text>暂无数据</text>
      </view>
    </scroll-view>
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import schoolApi from '../../api/school'

const keyword = ref('')
const selectedProvince = ref('')
const selectedType = ref('')
const schools = ref([])
const loading = ref(false)
const noMore = ref(false)
const page = ref(1)
const provinces = ref([])
const types = ref([])

onMounted(() => {
  loadProvinces()
  loadTypes()
  loadSchools()
})

const loadProvinces = async () => {
  try {
    const result = await schoolApi.getProvinces()
    if (Array.isArray(result)) {
      provinces.value = result
    }
  } catch (error) {
    console.error('加载省份失败:', error)
    provinces.value = ['北京', '上海', '天津', '重庆', '广东', '江苏', '浙江', '四川', '湖北', '陕西']
  }
}

const loadTypes = async () => {
  try {
    const result = await schoolApi.getSchoolTypes()
    if (result && typeof result === 'object') {
      types.value = Object.values(result)
    }
  } catch (error) {
    console.error('加载类型失败:', error)
    types.value = ['综合', '理工', '师范', '农林', '医药', '语言', '财经', '体育', '艺术']
  }
}

const loadSchools = async () => {
  if (loading.value) return
  loading.value = true

  try {
    const params = {
      page: page.value,
      page_size: 10
    }
    if (keyword.value) {
      params.search = keyword.value
    }
    if (selectedProvince.value) {
      params.province = selectedProvince.value
    }
    if (selectedType.value) {
      params.school_type = selectedType.value
    }

    const result = await schoolApi.getSchools(params)

    if (result && result.results) {
      if (page.value === 1) {
        schools.value = result.results
      } else {
        schools.value = [...schools.value, ...result.results]
      }
      noMore.value = page.value >= (result.total_pages || 1)
    } else if (Array.isArray(result)) {
      schools.value = result
      noMore.value = true
    }
  } catch (error) {
    console.error('加载院校失败:', error)
    uni.showToast({
      title: '加载失败',
      icon: 'none'
    })
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  page.value = 1
  noMore.value = false
  loadSchools()
}

const showProvincePicker = () => {
  if (provinces.value.length === 0) {
    uni.showToast({ title: '省份数据加载中', icon: 'none' })
    return
  }
  uni.showActionSheet({
    itemList: ['不限', ...provinces.value],
    success: (res) => {
      if (res.tapIndex === 0) {
        selectedProvince.value = ''
      } else {
        selectedProvince.value = provinces.value[res.tapIndex - 1]
      }
      handleSearch()
    }
  })
}

const showTypePicker = () => {
  if (types.value.length === 0) {
    uni.showToast({ title: '类型数据加载中', icon: 'none' })
    return
  }
  uni.showActionSheet({
    itemList: ['不限', ...types.value],
    success: (res) => {
      if (res.tapIndex === 0) {
        selectedType.value = ''
      } else {
        selectedType.value = types.value[res.tapIndex - 1]
      }
      handleSearch()
    }
  })
}

const loadMore = () => {
  if (!noMore.value && !loading.value) {
    page.value++
    loadSchools()
  }
}

const viewSchoolDetail = (id) => {
  uni.navigateTo({
    url: `/pages/school-detail/school-detail?id=${id}`
  })
}
</script>

<style scoped>
.container {
  min-height: 100vh;
  background-color: #f5f5f5;
}

.search-wrapper {
  background-color: #4361ee;
  padding: 30rpx;
}

.search-box {
  display: flex;
  align-items: center;
  background-color: #fff;
  border-radius: 50rpx;
  padding: 10rpx 20rpx;
}

.search-input {
  flex: 1;
  height: 60rpx;
  font-size: 28rpx;
}

.search-btn {
  background-color: #4361ee;
  color: #fff;
  font-size: 26rpx;
  padding: 10rpx 30rpx;
  border-radius: 30rpx;
  border: none;
}

.filter-wrapper {
  display: flex;
  background-color: #fff;
  padding: 20rpx 0;
  margin-bottom: 20rpx;
}

.filter-item {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 28rpx;
  color: #666;
}

.arrow {
  margin-left: 10rpx;
  font-size: 20rpx;
  color: #999;
}

.school-list {
  height: calc(100vh - 300rpx);
  padding: 0 30rpx;
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

.tag-985 {
  background-color: #ff4757;
  color: #fff;
}

.tag-211 {
  background-color: #ffa502;
  color: #fff;
}

.tag-level {
  background-color: #4361ee;
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

.school-score {
  display: flex;
  align-items: center;
  padding-top: 20rpx;
  border-top: 1rpx solid #f0f0f0;
}

.score-label {
  font-size: 26rpx;
  color: #999;
  margin-right: 10rpx;
}

.score-value {
  font-size: 32rpx;
  font-weight: 600;
  color: #4361ee;
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
  color: #4361ee;
}

.loading-more,
.no-more,
.empty {
  text-align: center;
  padding: 30rpx;
  color: #999;
  font-size: 26rpx;
}
</style>
