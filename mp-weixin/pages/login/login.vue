<template>
  <view class="container">
    <view class="login-header">
      <text class="title">欢迎回来</text>
      <text class="subtitle">登录到校园实时互动社区</text>
    </view>

    <view class="login-form">
      <view class="form-item">
        <input type="text" v-model="loginForm.username" placeholder="用户名/邮箱/手机号" class="form-input" />
      </view>
      <view class="form-item">
        <input type="password" v-model="loginForm.password" placeholder="密码" class="form-input" />
      </view>

      <view class="form-options">
        <checkbox-group @change="rememberChange">
          <label>
            <checkbox value="1" :checked="loginForm.remember" />
            <text class="remember-text">记住我</text>
          </label>
        </checkbox-group>
        <text class="forgot-text" @click="forgotPassword">忘记密码？</text>
      </view>

      <button class="login-btn" @click="handleLogin" :loading="loading">登录</button>

      <view class="divider">
        <view class="divider-line"></view>
        <text class="divider-text">或</text>
        <view class="divider-line"></view>
      </view>

      <button class="wechat-btn" @click="wechatLogin">
        <text class="icon">💬</text>
        <text>微信登录</text>
      </button>
    </view>

    <view class="register-link">
      <text>还没有账号？</text>
      <text class="link" @click="goToRegister">立即注册</text>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import userApi from '../../api/user'

const loading = ref(false)
const loginForm = ref({
  username: '',
  password: '',
  remember: false
})

const rememberChange = (e) => {
  loginForm.value.remember = e.detail.value.length > 0
}

const handleLogin = async () => {
  if (!loginForm.value.username || !loginForm.value.password) {
    uni.showToast({ title: '请填写完整信息', icon: 'none' })
    return
  }

  loading.value = true

  try {
    const result = await userApi.login({
      username: loginForm.value.username,
      password: loginForm.value.password
    })

    if (result.access && result.refresh) {
      uni.setStorageSync('accessToken', result.access)
      uni.setStorageSync('refreshToken', result.refresh)
      uni.setStorageSync('userInfo', result.user)
      uni.setStorageSync('username', result.user.username)
      uni.showToast({ title: '登录成功', icon: 'success' })

      setTimeout(() => {
        uni.switchTab({ url: '/pages/index/index' })
      }, 1500)
    } else {
      uni.showToast({ title: '登录失败，请重试', icon: 'none' })
    }
  } catch (error) {
    console.error('登录失败:', error)
    uni.showToast({ title: error?.message || '登录失败，请重试', icon: 'none' })
  } finally {
    loading.value = false
  }
}

const wechatLogin = () => {
  uni.showToast({ title: '微信登录开发中', icon: 'none' })
}

const forgotPassword = () => {
  uni.navigateTo({ url: '/pages/reset-password/reset-password' })
}

const goToRegister = () => {
  uni.navigateTo({ url: '/pages/register/register' })
}
</script>

<style scoped>
.container {
  min-height: 100vh;
  background-color: #f5f5f5;
  padding: 60rpx 50rpx;
}

.login-header {
  margin-bottom: 80rpx;
}

.title {
  display: block;
  font-size: 48rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 20rpx;
}

.subtitle {
  font-size: 28rpx;
  color: #999;
}

.login-form {
  background-color: #fff;
  border-radius: 24rpx;
  padding: 60rpx 40rpx;
  margin-bottom: 40rpx;
}

.form-item {
  margin-bottom: 40rpx;
}

.form-input {
  height: 90rpx;
  background-color: #f5f5f5;
  border-radius: 45rpx;
  padding: 0 40rpx;
  font-size: 28rpx;
}

.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 40rpx;
}

.remember-text {
  font-size: 26rpx;
  color: #666;
  margin-left: 10rpx;
}

.forgot-text {
  font-size: 26rpx;
  color: #4CAF50;
}

.login-btn {
  width: 100%;
  height: 90rpx;
  background-color: #4CAF50;
  color: #fff;
  border-radius: 45rpx;
  font-size: 32rpx;
  font-weight: 500;
  border: none;
}

.divider {
  display: flex;
  align-items: center;
  margin: 50rpx 0;
}

.divider-line {
  flex: 1;
  height: 1rpx;
  background-color: #eee;
}

.divider-text {
  padding: 0 30rpx;
  font-size: 26rpx;
  color: #999;
}

.wechat-btn {
  width: 100%;
  height: 90rpx;
  background-color: #fff;
  color: #333;
  border-radius: 45rpx;
  font-size: 32rpx;
  border: 1rpx solid #eee;
  display: flex;
  align-items: center;
  justify-content: center;
}

.wechat-btn .icon {
  margin-right: 10rpx;
  font-size: 40rpx;
}

.register-link {
  text-align: center;
  font-size: 28rpx;
  color: #666;
}

.link {
  color: #4CAF50;
  margin-left: 10rpx;
}
</style>
