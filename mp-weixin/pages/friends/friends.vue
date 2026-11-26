<template>
  <view class="container">
    <!-- 切换标签 -->
    <view class="tab-bar">
      <view
        class="tab-item"
        :class="{ active: activeTab === 'list' }"
        @click="switchTab('list')"
      >
        好友列表
      </view>
      <view
        class="tab-item"
        :class="{ active: activeTab === 'requests' }"
        @click="switchTab('requests')"
      >
        好友请求
        <text class="badge" v-if="receivedRequests.length > 0">{{ receivedRequests.length }}</text>
      </view>
      <view
        class="tab-item"
        :class="{ active: activeTab === 'add' }"
        @click="switchTab('add')"
      >
        添加好友
      </view>
    </view>

    <!-- 好友列表 -->
    <view v-if="activeTab === 'list'" class="panel">
      <input
        class="search-input"
        type="text"
        v-model="friendKeyword"
        placeholder="搜索好友..."
      />
      <view class="tip" v-if="loadingFriends">加载中...</view>
      <view class="user-item" v-for="friend in filteredFriends" :key="friend.id">
        <image class="avatar" :src="friend.avatar || '/static/logo.png'" mode="aspectFill"></image>
        <view class="user-info">
          <text class="user-name">{{ friend.username }}</text>
          <text class="user-sub">{{ friend.email || friend.bio || '暂无简介' }}</text>
        </view>
        <view class="user-actions">
          <view class="mini-btn primary" @click="goToChat(friend.id)">私信</view>
          <view class="mini-btn danger" @click="confirmRemove(friend)">移除</view>
        </view>
      </view>
      <view class="tip empty" v-if="!loadingFriends && filteredFriends.length === 0">
        暂无好友，去添加好友吧
      </view>
    </view>

    <!-- 好友请求 -->
    <view v-else-if="activeTab === 'requests'" class="panel">
      <view class="tip" v-if="loadingRequests">加载中...</view>
      <view class="user-item" v-for="request in receivedRequests" :key="request.id">
        <image
          class="avatar"
          :src="request.sender?.avatar || '/static/logo.png'"
          mode="aspectFill"
        ></image>
        <view class="user-info">
          <text class="user-name">{{ request.sender?.username || '匿名用户' }}</text>
          <text class="user-sub">{{ formatTime(request.created_at) }} 请求添加好友</text>
        </view>
        <view class="user-actions">
          <view class="mini-btn primary" @click="acceptRequest(request)">接受</view>
          <view class="mini-btn" @click="rejectRequest(request)">拒绝</view>
        </view>
      </view>
      <view class="tip empty" v-if="!loadingRequests && receivedRequests.length === 0">
        暂无好友请求
      </view>
    </view>

    <!-- 添加好友 -->
    <view v-else class="panel">
      <view class="search-row">
        <input
          class="search-input"
          type="text"
          v-model="userKeyword"
          placeholder="搜索用户名或邮箱"
          confirm-type="search"
          @confirm="searchUsers"
        />
        <view class="search-btn" @click="searchUsers">搜索</view>
      </view>
      <view class="tip" v-if="searching">搜索中...</view>
      <view class="user-item" v-for="user in searchResults" :key="user.id">
        <image class="avatar" :src="user.avatar || '/static/logo.png'" mode="aspectFill"></image>
        <view class="user-info">
          <text class="user-name">{{ user.username }}</text>
          <text class="user-sub">{{ user.email || user.bio || '暂无简介' }}</text>
        </view>
        <view class="user-actions">
          <text class="state-text" v-if="friendIds.includes(user.id)">已是好友</text>
          <text class="state-text" v-else-if="sentReceiverIds.includes(user.id)">已发送</text>
          <view class="mini-btn primary" v-else @click="sendRequest(user)">添加</view>
        </view>
      </view>
      <view class="tip empty" v-if="!searching && searched && searchResults.length === 0">
        未找到匹配的用户
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onLoad, onPullDownRefresh } from '@dcloudio/uni-app'
import userApi from '../../api/user'

const activeTab = ref('list')

const friends = ref([])
const friendKeyword = ref('')
const loadingFriends = ref(false)
const friendIds = computed(() => friends.value.map((item) => item.id))

const receivedRequests = ref([])
const loadingRequests = ref(false)

const userKeyword = ref('')
const searchResults = ref([])
const sentReceiverIds = ref([])
const searching = ref(false)
const searched = ref(false)

const filteredFriends = computed(() => {
  const keyword = friendKeyword.value.trim().toLowerCase()
  if (!keyword) return friends.value
  return friends.value.filter((friend) => {
    const name = (friend.username || '').toLowerCase()
    const email = (friend.email || '').toLowerCase()
    return name.includes(keyword) || email.includes(keyword)
  })
})

onLoad(() => {
  if (!ensureLogin()) return
  loadFriends()
  loadRequests()
})

onPullDownRefresh(() => {
  Promise.all([loadFriends(), loadRequests()]).finally(() => {
    uni.stopPullDownRefresh()
  })
})

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

const switchTab = (tab) => {
  activeTab.value = tab
  if (tab === 'requests') {
    loadRequests()
  }
}

const loadFriends = async () => {
  loadingFriends.value = true
  try {
    const result = await userApi.getFriends()
    friends.value = result?.friends || (Array.isArray(result) ? result : [])
  } catch (error) {
    console.error('加载好友列表失败:', error)
    friends.value = []
  } finally {
    loadingFriends.value = false
  }
}

const loadRequests = async () => {
  loadingRequests.value = true
  try {
    const result = await userApi.getReceivedFriendRequests()
    receivedRequests.value = Array.isArray(result) ? result : (result?.results || [])
  } catch (error) {
    console.error('加载好友请求失败:', error)
    receivedRequests.value = []
  } finally {
    loadingRequests.value = false
  }
}

const acceptRequest = async (request) => {
  try {
    await userApi.acceptFriendRequest(request.id)
    receivedRequests.value = receivedRequests.value.filter((item) => item.id !== request.id)
    uni.showToast({ title: '已接受', icon: 'success' })
    loadFriends()
  } catch (error) {
    console.error('接受好友请求失败:', error)
    uni.showToast({ title: '操作失败', icon: 'none' })
  }
}

const rejectRequest = async (request) => {
  try {
    await userApi.rejectFriendRequest(request.id)
    receivedRequests.value = receivedRequests.value.filter((item) => item.id !== request.id)
    uni.showToast({ title: '已拒绝', icon: 'success' })
  } catch (error) {
    console.error('拒绝好友请求失败:', error)
    uni.showToast({ title: '操作失败', icon: 'none' })
  }
}

const searchUsers = async () => {
  const keyword = userKeyword.value.trim()
  if (!keyword) {
    uni.showToast({ title: '请输入关键词', icon: 'none' })
    return
  }
  searching.value = true
  searched.value = false
  try {
    const result = await userApi.searchUsers(keyword)
    searchResults.value = result?.results || (Array.isArray(result) ? result : [])
    searched.value = true
    await loadSentRequests()
  } catch (error) {
    console.error('搜索用户失败:', error)
    searchResults.value = []
    searched.value = true
  } finally {
    searching.value = false
  }
}

const loadSentRequests = async () => {
  try {
    const result = await userApi.getSentFriendRequests()
    const list = Array.isArray(result) ? result : (result?.results || [])
    sentReceiverIds.value = list.map((item) => item.receiver?.id).filter(Boolean)
  } catch (error) {
    console.error('加载已发送请求失败:', error)
  }
}

const sendRequest = async (user) => {
  try {
    await userApi.sendFriendRequest(user.id)
    sentReceiverIds.value.push(user.id)
    uni.showToast({ title: '请求已发送', icon: 'success' })
  } catch (error) {
    console.error('发送好友请求失败:', error)
    uni.showToast({ title: error?.detail || '发送失败', icon: 'none' })
  }
}

const goToChat = (userId) => {
  uni.navigateTo({ url: `/pages/chat-detail/chat-detail?id=${userId}` })
}

const confirmRemove = (friend) => {
  uni.showModal({
    title: '移除好友',
    content: `确定将 ${friend.username} 从好友列表中移除吗？`,
    success: async (res) => {
      if (!res.confirm) return
      try {
        await userApi.removeFriend(friend.id)
        friends.value = friends.value.filter((item) => item.id !== friend.id)
        uni.showToast({ title: '已移除', icon: 'success' })
      } catch (error) {
        console.error('移除好友失败:', error)
        uni.showToast({ title: '移除失败', icon: 'none' })
      }
    }
  })
}

const formatTime = (value) => {
  if (!value) return ''
  const date = new Date(value)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  if (diff < 7 * 86400000) return `${Math.floor(diff / 86400000)}天前`
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}
</script>

<style scoped>
.container {
  min-height: 100vh;
  background-color: #f5f5f5;
}

.tab-bar {
  display: flex;
  background-color: #fff;
  border-bottom: 1rpx solid #f0f0f0;
}

.tab-item {
  flex: 1;
  text-align: center;
  padding: 26rpx 0;
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
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 60rpx;
  height: 4rpx;
  border-radius: 2rpx;
  background-color: #4361ee;
}

.badge {
  margin-left: 8rpx;
  font-size: 20rpx;
  color: #fff;
  background-color: #e53935;
  border-radius: 20rpx;
  padding: 2rpx 10rpx;
}

.panel {
  padding: 20rpx 30rpx;
}

.search-row {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-bottom: 20rpx;
}

.search-input {
  flex: 1;
  height: 72rpx;
  background-color: #fff;
  border-radius: 36rpx;
  padding: 0 30rpx;
  font-size: 28rpx;
  margin-bottom: 20rpx;
}

.search-row .search-input {
  margin-bottom: 0;
}

.search-btn {
  height: 72rpx;
  line-height: 72rpx;
  padding: 0 32rpx;
  border-radius: 36rpx;
  background-color: #4361ee;
  color: #fff;
  font-size: 28rpx;
}

.user-item {
  display: flex;
  align-items: center;
  background-color: #fff;
  border-radius: 16rpx;
  padding: 24rpx 30rpx;
  margin-bottom: 16rpx;
}

.avatar {
  width: 88rpx;
  height: 88rpx;
  border-radius: 50%;
  margin-right: 20rpx;
}

.user-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.user-name {
  font-size: 30rpx;
  font-weight: 500;
  color: #333;
  margin-bottom: 6rpx;
}

.user-sub {
  font-size: 24rpx;
  color: #999;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-actions {
  display: flex;
  align-items: center;
  gap: 12rpx;
  flex-shrink: 0;
}

.mini-btn {
  padding: 10rpx 24rpx;
  border-radius: 30rpx;
  font-size: 24rpx;
  color: #666;
  border: 1rpx solid #ddd;
  background-color: #fff;
}

.mini-btn.primary {
  color: #fff;
  background-color: #4361ee;
  border-color: #4361ee;
}

.mini-btn.danger {
  color: #e53935;
  border-color: #e53935;
}

.state-text {
  font-size: 24rpx;
  color: #999;
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
