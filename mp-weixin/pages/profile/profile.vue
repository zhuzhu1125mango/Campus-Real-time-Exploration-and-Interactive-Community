<template>
  <view class="container">
    <!-- 用户信息卡片 -->
    <view class="user-card">
      <image class="avatar" :src="userInfo.avatar || '/static/logo.png'" mode="aspectFill"></image>
      <view class="user-info">
        <text class="username">{{ userInfo.username || '未登录' }}</text>
        <text class="user-desc">{{ userInfo.bio || '这个人很懒，什么都没写' }}</text>
      </view>
      <button class="edit-btn" v-if="isLoggedIn" @click="viewProfile">编辑</button>
    </view>

    <!-- 功能列表 -->
    <view class="menu-list">
      <view class="menu-item" @click="navigateTo('/pages/user-profile/user-profile?id=me')">
        <text class="icon">👤</text>
        <text class="menu-text">用户资料</text>
        <text class="arrow">></text>
      </view>
      <view class="menu-item" @click="navigateTo('/pages/my-learning/my-learning')">
        <text class="icon">📚</text>
        <text class="menu-text">我的学习</text>
        <text class="arrow">></text>
      </view>
      <view class="menu-item" @click="navigateTo('/pages/content/content')">
        <text class="icon">📄</text>
        <text class="menu-text">内容中心</text>
        <text class="arrow">></text>
      </view>
      <view class="menu-item" @click="navigateTo('/pages/my-favorite-schools/my-favorite-schools')">
        <text class="icon">🏫</text>
        <text class="menu-text">我的收藏院校</text>
        <text class="arrow">></text>
      </view>
      <view class="menu-item" @click="navigateTo('/pages/messages/messages')">
        <text class="icon">💬</text>
        <text class="menu-text">我的消息</text>
        <text class="arrow">></text>
      </view>
      <view class="menu-item" @click="navigateTo('/pages/bookmarks/bookmarks')">
        <text class="icon">❤️</text>
        <text class="menu-text">我的收藏</text>
        <text class="arrow">></text>
      </view>
      <view class="menu-item" @click="navigateTo('/pages/notifications/notifications')">
        <text class="icon">🔔</text>
        <text class="menu-text">通知</text>
        <text class="arrow">></text>
      </view>
      <view class="menu-item" @click="navigateTo('/pages/settings/settings')">
        <text class="icon">⚙️</text>
        <text class="menu-text">设置</text>
        <text class="arrow">></text>
      </view>
      <view class="menu-item" @click="navigateTo('/pages/about/about')">
        <text class="icon">ℹ️</text>
        <text class="menu-text">关于我们</text>
        <text class="arrow">></text>
      </view>
    </view>

    <!-- 登录/注册按钮 -->
    <view class="auth-buttons" v-if="!isLoggedIn">
      <button class="login-btn" @click="navigateTo('/pages/login/login')">登录</button>
      <button class="register-btn" @click="navigateTo('/pages/register/register')">注册</button>
    </view>

    <!-- 退出登录按钮 -->
    <button class="logout-btn" v-if="isLoggedIn" @click="handleLogout">退出登录</button>
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import userApi from '../../api/user'

const isLoggedIn = ref(false)
const userInfo = ref({})

onMounted(() => {
  checkLoginStatus()
})

const checkLoginStatus = () => {
  const token = uni.getStorageSync('accessToken')
  const storedUserInfo = uni.getStorageSync('userInfo')
  if (token) {
    isLoggedIn.value = true
    if (storedUserInfo) {
      userInfo.value = storedUserInfo
    } else {
      loadUserInfo()
    }
  }
}

const loadUserInfo = async () => {
  try {
    const result = await userApi.getUserInfo()
    userInfo.value = result || {}
    uni.setStorageSync('userInfo', result)
  } catch (error) {
    console.error('加载用户信息失败:', error)
    userInfo.value = {
      username: uni.getStorageSync('username') || '用户',
      avatar: '',
      bio: '这个人很懒，什么都没写'
    }
  }
}

const navigateTo = (url) => {
  const tabbarPages = [
    '/pages/index/index',
    '/pages/schools/schools',
    '/pages/forum/forum',
    '/pages/messages/messages',
    '/pages/profile/profile'
  ]

  if (tabbarPages.includes(url)) {
    uni.switchTab({ url })
  } else {
    uni.navigateTo({ url })
  }
}

const viewProfile = () => {
  uni.navigateTo({ url: '/pages/user-profile/user-profile?id=me' })
}

const handleLogout = () => {
  uni.showModal({
    title: '提示',
    content: '确定要退出登录吗？',
    success: (res) => {
      if (res.confirm) {
        uni.removeStorageSync('accessToken')
        uni.removeStorageSync('refreshToken')
        uni.removeStorageSync('userInfo')
        isLoggedIn.value = false
        userInfo.value = {}
        uni.showToast({ title: '已退出登录', icon: 'success' })
      }
    }
  })
}
</script>

<style scoped>
.container {
  min-height: 100vh;
  background-color: #f5f5f5;
  padding: 30rpx;
}

.user-card {
  background-color: #fff;
  border-radius: 16rpx;
  padding: 40rpx;
  display: flex;
  align-items: center;
  margin-bottom: 30rpx;
}

.avatar {
  width: 120rpx;
  height: 120rpx;
  border-radius: 50%;
  margin-right: 30rpx;
}

.user-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.username {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 10rpx;
}

.user-desc {
  font-size: 26rpx;
  color: #999;
}

.edit-btn {
  font-size: 26rpx;
  color: #4CAF50;
  padding: 10rpx 30rpx;
  border: 1rpx solid #4CAF50;
  border-radius: 30rpx;
  background-color: #fff;
}

.menu-list {
  background-color: #fff;
  border-radius: 16rpx;
  overflow: hidden;
  margin-bottom: 30rpx;
}

.menu-item {
  display: flex;
  align-items: center;
  padding: 30rpx;
  border-bottom: 1rpx solid #f0f0f0;
}

.menu-item:last-child {
  border-bottom: none;
}

.menu-item .icon {
  font-size: 40rpx;
  margin-right: 20rpx;
}

.menu-text {
  flex: 1;
  font-size: 28rpx;
  color: #333;
}

.menu-item .arrow {
  color: #ccc;
  font-size: 28rpx;
}

.auth-buttons {
  display: flex;
  gap: 30rpx;
}

.login-btn,
.register-btn {
  flex: 1;
  height: 80rpx;
  line-height: 80rpx;
  border-radius: 40rpx;
  font-size: 28rpx;
  font-weight: 500;
}

.login-btn {
  background-color: #4CAF50;
  color: #fff;
  border: none;
}

.register-btn {
  background-color: #fff;
  color: #4CAF50;
  border: 1rpx solid #4CAF50;
}

.logout-btn {
  width: 100%;
  height: 80rpx;
  line-height: 80rpx;
  background-color: #fff;
  color: #999;
  border-radius: 40rpx;
  font-size: 28rpx;
  border: none;
}
</style>
