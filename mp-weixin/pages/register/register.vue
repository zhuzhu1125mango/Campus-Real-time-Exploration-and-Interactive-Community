<template>
  <view class="container">
    <view class="register-header">
      <text class="title">创建账号</text>
      <text class="subtitle">加入校园实时互动社区</text>
    </view>

    <!-- 注册方式切换 -->
    <view class="tab-switch">
      <view
        class="tab-item"
        :class="{ active: registerType === 'email' }"
        @click="registerType = 'email'"
      >
        邮箱注册
      </view>
      <view
        class="tab-item"
        :class="{ active: registerType === 'phone' }"
        @click="registerType = 'phone'"
      >
        手机注册
      </view>
    </view>

    <view class="register-form">
      <!-- 邮箱注册表单 -->
      <view v-if="registerType === 'email'">
        <view class="form-item">
          <input type="text" v-model="emailForm.username" placeholder="用户名" class="form-input" />
        </view>
        <view class="form-item">
          <input type="text" v-model="emailForm.email" placeholder="邮箱" class="form-input" />
        </view>
        <view class="form-item">
          <input type="password" v-model="emailForm.password" placeholder="密码（至少8位）" class="form-input" />
        </view>
        <view class="form-item">
          <input type="password" v-model="emailForm.confirmPassword" placeholder="确认密码" class="form-input" />
        </view>
        <view class="form-item verification">
          <input type="text" v-model="emailForm.code" placeholder="验证码" class="form-input code-input" />
          <button class="send-code-btn" @click="sendEmailCode" :disabled="countdown > 0">
            {{ countdown > 0 ? `${countdown}s` : '获取验证码' }}
          </button>
        </view>
        <button class="register-btn" @click="handleEmailRegister" :loading="loading">注册</button>
      </view>

      <!-- 手机注册表单 -->
      <view v-else>
        <view class="form-item">
          <input type="text" v-model="phoneForm.username" placeholder="用户名" class="form-input" />
        </view>
        <view class="form-item">
          <input type="text" v-model="phoneForm.phone" placeholder="手机号" class="form-input" />
        </view>
        <view class="form-item">
          <input type="password" v-model="phoneForm.password" placeholder="密码（至少8位）" class="form-input" />
        </view>
        <view class="form-item">
          <input type="password" v-model="phoneForm.confirmPassword" placeholder="确认密码" class="form-input" />
        </view>
        <view class="form-item verification">
          <input type="text" v-model="phoneForm.code" placeholder="验证码" class="form-input code-input" />
          <button class="send-code-btn" @click="sendPhoneCode" :disabled="countdown > 0">
            {{ countdown > 0 ? `${countdown}s` : '获取验证码' }}
          </button>
        </view>
        <button class="register-btn" @click="handlePhoneRegister" :loading="loading">注册</button>
      </view>
    </view>

    <view class="login-link">
      <text>已有账号？</text>
      <text class="link" @click="goToLogin">立即登录</text>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import userApi from '../../api/user'

const registerType = ref('email')
const countdown = ref(0)
let countdownTimer = null
const loading = ref(false)

const emailForm = ref({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  code: ''
})

const phoneForm = ref({
  username: '',
  phone: '',
  password: '',
  confirmPassword: '',
  code: ''
})

const sendEmailCode = async () => {
  if (!emailForm.value.email) {
    uni.showToast({ title: '请输入邮箱', icon: 'none' })
    return
  }

  try {
    await userApi.sendEmailCode({
      email: emailForm.value.email,
      purpose: 'register'
    })
    uni.showToast({ title: '验证码已发送', icon: 'success' })
    startCountdown()
  } catch (error) {
    uni.showToast({ title: '发送失败，请重试', icon: 'none' })
  }
}

const sendPhoneCode = async () => {
  if (!phoneForm.value.phone) {
    uni.showToast({ title: '请输入手机号', icon: 'none' })
    return
  }

  try {
    await userApi.sendPhoneCode({
      phone: phoneForm.value.phone,
      purpose: 'register'
    })
    uni.showToast({ title: '验证码已发送', icon: 'success' })
    startCountdown()
  } catch (error) {
    uni.showToast({ title: '发送失败，请重试', icon: 'none' })
  }
}

const startCountdown = () => {
  countdown.value = 60
  countdownTimer = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) {
      clearInterval(countdownTimer)
    }
  }, 1000)
}

const handleEmailRegister = async () => {
  const { username, email, password, confirmPassword, code } = emailForm.value

  if (!username || !email || !password || !confirmPassword || !code) {
    uni.showToast({ title: '请填写完整信息', icon: 'none' })
    return
  }

  if (password !== confirmPassword) {
    uni.showToast({ title: '两次密码输入不一致', icon: 'none' })
    return
  }

  if (password.length < 8) {
    uni.showToast({ title: '密码长度不能少于8位', icon: 'none' })
    return
  }

  loading.value = true
  try {
    await userApi.register({
      username,
      email,
      password,
      password_confirm: confirmPassword,
      code
    })
    uni.showToast({ title: '注册成功', icon: 'success' })
    setTimeout(() => {
      uni.navigateTo({ url: '/pages/login/login' })
    }, 1500)
  } catch (error) {
    console.error('注册失败:', error)
    uni.showToast({ title: error?.message || '注册失败，请重试', icon: 'none' })
  } finally {
    loading.value = false
  }
}

const handlePhoneRegister = async () => {
  const { username, phone, password, confirmPassword, code } = phoneForm.value

  if (!username || !phone || !password || !confirmPassword || !code) {
    uni.showToast({ title: '请填写完整信息', icon: 'none' })
    return
  }

  if (password !== confirmPassword) {
    uni.showToast({ title: '两次密码输入不一致', icon: 'none' })
    return
  }

  if (password.length < 8) {
    uni.showToast({ title: '密码长度不能少于8位', icon: 'none' })
    return
  }

  loading.value = true
  try {
    await userApi.register({
      username,
      phone,
      password,
      password_confirm: confirmPassword,
      code
    })
    uni.showToast({ title: '注册成功', icon: 'success' })
    setTimeout(() => {
      uni.navigateTo({ url: '/pages/login/login' })
    }, 1500)
  } catch (error) {
    console.error('注册失败:', error)
    uni.showToast({ title: error?.message || '注册失败，请重试', icon: 'none' })
  } finally {
    loading.value = false
  }
}

const goToLogin = () => {
  uni.navigateTo({ url: '/pages/login/login' })
}
</script>

<style scoped>
.container {
  min-height: 100vh;
  background-color: #f5f5f5;
  padding: 60rpx 50rpx;
}

.register-header {
  margin-bottom: 60rpx;
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

.tab-switch {
  display: flex;
  background-color: #fff;
  border-radius: 50rpx;
  padding: 8rpx;
  margin-bottom: 40rpx;
}

.tab-item {
  flex: 1;
  text-align: center;
  padding: 20rpx 0;
  font-size: 28rpx;
  color: #666;
  border-radius: 40rpx;
}

.tab-item.active {
  background-color: #4361ee;
  color: #fff;
}

.register-form {
  background-color: #fff;
  border-radius: 24rpx;
  padding: 60rpx 40rpx;
  margin-bottom: 40rpx;
}

.form-item {
  margin-bottom: 30rpx;
}

.form-input {
  height: 90rpx;
  background-color: #f5f5f5;
  border-radius: 45rpx;
  padding: 0 40rpx;
  font-size: 28rpx;
}

.verification {
  display: flex;
  gap: 20rpx;
}

.code-input {
  flex: 1;
}

.send-code-btn {
  width: 240rpx;
  height: 90rpx;
  background-color: #4361ee;
  color: #fff;
  border-radius: 45rpx;
  font-size: 26rpx;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
}

.send-code-btn[disabled] {
  background-color: #ccc;
}

.register-btn {
  width: 100%;
  height: 90rpx;
  background-color: #4361ee;
  color: #fff;
  border-radius: 45rpx;
  font-size: 32rpx;
  font-weight: 500;
  border: none;
  margin-top: 20rpx;
}

.login-link {
  text-align: center;
  font-size: 28rpx;
  color: #666;
}

.link {
  color: #4361ee;
  margin-left: 10rpx;
}
</style>
