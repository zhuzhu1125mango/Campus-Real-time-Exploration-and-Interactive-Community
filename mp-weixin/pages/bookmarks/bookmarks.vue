<template>
  <view class="container">
    <view class="header">
      <text class="title">我的收藏</text>
    </view>

    <!-- 收藏类型切换 -->
    <view class="tab-wrapper">
      <view class="tab-list">
        <view
          class="tab-item"
          :class="{ active: currentTab === 'schools' }"
          @click="currentTab = 'schools'"
        >
          收藏院校
        </view>
        <view
          class="tab-item"
          :class="{ active: currentTab === 'posts' }"
          @click="currentTab = 'posts'"
        >
          收藏帖子
        </view>
      </view>
    </view>

    <!-- 收藏列表 -->
    <scroll-view class="list-content" scroll-y>
      <!-- 院校收藏 -->
      <view v-if="currentTab === 'schools'">
        <view
          class="school-item"
          v-for="school in schoolBookmarks"
          :key="school.id"
          @click="viewSchool(school.id)"
        >
          <view class="school-info">
            <view class="school-name">{{ school.name }}</view>
            <view class="school-tags">
              <text class="tag tag-985" v-if="school.is_985">985</text>
              <text class="tag tag-211" v-if="school.is_211">211</text>
            </view>
          </view>
          <view class="school-meta">
            <text>{{ school.province }}</text>
            <text>{{ school.type }}</text>
          </view>
          <view class="remove-btn" @click.stop="removeSchoolBookmark(school.id)">删除</view>
        </view>
      </view>

      <!-- 帖子收藏 -->
      <view v-else>
        <view
          class="post-item"
          v-for="post in postBookmarks"
          :key="post.id"
          @click="viewPost(post.id)"
        >
          <view class="post-title">{{ post.title }}</view>
          <view class="post-info">
            <text>{{ post.author }}</text>
            <text>{{ formatTime(post.created_at) }}</text>
          </view>
          <view class="remove-btn" @click.stop="removePostBookmark(post.id)">删除</view>
        </view>
      </view>

      <view class="empty" v-if="(currentTab === 'schools' && schoolBookmarks.length === 0) || (currentTab === 'posts' && postBookmarks.length === 0)">
        <text>暂无收藏</text>
      </view>
    </scroll-view>
  </view>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import schoolApi from '../../api/school'
import forumApi from '../../api/forum'

const currentTab = ref('schools')
const schoolBookmarks = ref([])
const postBookmarks = ref([])
const loading = ref(false)

watch(currentTab, () => {
  loadBookmarks()
})

onMounted(() => {
  checkLoginAndLoad()
})

const checkLoginAndLoad = () => {
  const token = uni.getStorageSync('accessToken')
  if (!token) {
    uni.showToast({ title: '请先登录', icon: 'none' })
    setTimeout(() => {
      uni.navigateBack()
    }, 1500)
    return
  }
  loadBookmarks()
}

const loadBookmarks = async () => {
  loading.value = true
  try {
    if (currentTab.value === 'schools') {
      await loadSchoolBookmarks()
    } else {
      await loadPostBookmarks()
    }
  } finally {
    loading.value = false
  }
}

const loadSchoolBookmarks = async () => {
  try {
    const result = await schoolApi.getMyFavorites()
    schoolBookmarks.value = (result && Array.isArray(result)) ? result : []
  } catch (error) {
    console.error('加载收藏院校失败:', error)
    schoolBookmarks.value = []
  }
}

const loadPostBookmarks = async () => {
  try {
    const result = await forumApi.getMyBookmarks()
    postBookmarks.value = (result && Array.isArray(result)) ? result : []
  } catch (error) {
    console.error('加载收藏帖子失败:', error)
    postBookmarks.value = []
  }
}

const viewSchool = (id) => {
  uni.navigateTo({ url: `/pages/school-detail/school-detail?id=${id}` })
}

const viewPost = (id) => {
  uni.navigateTo({ url: `/pages/post-detail/post-detail?id=${id}` })
}

const removeSchoolBookmark = async (id) => {
  uni.showModal({
    title: '提示',
    content: '确定要删除此收藏吗？',
    success: async (res) => {
      if (res.confirm) {
        try {
          await schoolApi.unfavoriteSchool(id)
          schoolBookmarks.value = schoolBookmarks.value.filter(s => s.id !== id)
          uni.showToast({ title: '已删除', icon: 'success' })
        } catch (error) {
          console.error('删除收藏失败:', error)
          uni.showToast({ title: '删除失败', icon: 'none' })
        }
      }
    }
  })
}

const removePostBookmark = async (id) => {
  uni.showModal({
    title: '提示',
    content: '确定要删除此收藏吗？',
    success: async (res) => {
      if (res.confirm) {
        try {
          await forumApi.unbookmarkTopic(id)
          postBookmarks.value = postBookmarks.value.filter(p => p.id !== id)
          uni.showToast({ title: '已删除', icon: 'success' })
        } catch (error) {
          console.error('删除收藏失败:', error)
          uni.showToast({ title: '删除失败', icon: 'none' })
        }
      }
    }
  })
}

const formatTime = (time) => {
  if (!time) return ''
  const date = new Date(time)
  const now = new Date()
  const diff = now - date
  if (diff < 86400000) return Math.floor(diff / 3600000) + '小时前'
  return Math.floor(diff / 86400000) + '天前'
}
</script>

<style scoped>
.container {
  min-height: 100vh;
  background-color: #f5f5f5;
}

.header {
  background-color: #fff;
  padding: 30rpx;
  text-align: center;
}

.title {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
}

.tab-wrapper {
  background-color: #fff;
  padding: 0 30rpx 20rpx;
}

.tab-list {
  display: flex;
  border-bottom: 1rpx solid #eee;
}

.tab-item {
  flex: 1;
  text-align: center;
  padding: 20rpx 0;
  font-size: 28rpx;
  color: #666;
  position: relative;
}

.tab-item.active {
  color: #4361ee;
  font-weight: 500;
}

.tab-item.active::after {
  content: '';
  position: absolute;
  bottom: -1rpx;
  left: 50%;
  transform: translateX(-50%);
  width: 60rpx;
  height: 4rpx;
  background-color: #4361ee;
  border-radius: 2rpx;
}

.list-content {
  height: calc(100vh - 200rpx);
  padding: 20rpx 30rpx;
}

.school-item {
  background-color: #fff;
  border-radius: 16rpx;
  padding: 30rpx;
  margin-bottom: 20rpx;
  display: flex;
  flex-direction: column;
  gap: 15rpx;
}

.school-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.school-name {
  font-size: 30rpx;
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

.school-meta {
  display: flex;
  gap: 20rpx;
  font-size: 24rpx;
  color: #999;
}

.post-item {
  background-color: #fff;
  border-radius: 16rpx;
  padding: 30rpx;
  margin-bottom: 20rpx;
  display: flex;
  flex-direction: column;
  gap: 15rpx;
}

.post-title {
  font-size: 28rpx;
  color: #333;
  font-weight: 500;
}

.post-info {
  display: flex;
  justify-content: space-between;
  font-size: 24rpx;
  color: #999;
}

.remove-btn {
  position: absolute;
  right: 30rpx;
  top: 50%;
  transform: translateY(-50%);
  font-size: 26rpx;
  color: #999;
}

.school-item,
.post-item {
  position: relative;
}

.empty {
  text-align: center;
  padding: 100rpx 0;
  color: #999;
  font-size: 28rpx;
}
</style>
