<template>
  <view class="container">
    <view class="reset-card">
      <view class="reset-header">
        <text class="title">重置密码</text>
        <text class="subtitle">请选择验证方式重置您的密码</text>
      </view>

      <view class="reset-tabs">
        <view class="tab-item" :class="{ active: activeTab === 'phone' }" @click="activeTab = 'phone'">手机验证码</view>
        <view class="tab-item" :class="{ active: activeTab === 'email' }" @click="activeTab = 'email'">邮箱验证码</view>
      </view>

      <!-- 手机重置 -->
      <view v-if="activeTab === 'phone'" class="reset-form">
        <view class="form-group">
          <text class="label">手机号</text>
          <input
            type="digit"
            v-model="phoneForm.phone"
            placeholder="请输入手机号"
            class="input"
            maxlength="11"
          />
        </view>

        <view class="form-group">
          <text class="label">验证码</text>
          <view class="code-wrapper">
            <input
              type="text"
              v-model="phoneForm.code"
              placeholder="请输入验证码"
              class="input code-input"
            />
            <button
              class="btn-code"
              :disabled="phoneCounting || !isValidPhone"
              @click="sendPhoneCode"
            >
              {{ phoneCountDown ? `${phoneCountDown}秒后重发` : '获取验证码' }}
            </button>
          </view>
        </view>

        <view class="form-group">
          <text class="label">新密码</text>
          <input
            :type="showPhonePassword ? 'text' : 'password'"
            v-model="phoneForm.password"
            placeholder="请输入新密码（至少8位）"
            class="input"
            minlength="8"
          />
        </view>

        <view class="form-group">
          <text class="label">确认密码</text>
          <input
            :type="showPhonePassword ? 'text' : 'password'"
            v-model="phoneForm.password_confirm"
            placeholder="请再次输入新密码"
            class="input"
            minlength="8"
          />
        </view>

        <view class="form-actions">
          <button class="btn-reset" :disabled="loading || !isValidPhoneForm" @click="handlePhoneReset">
            {{ loading ? '提交中...' : '重置密码' }}
          </button>
        </view>
      </view>

      <!-- 邮箱重置 -->
      <view v-if="activeTab === 'email'" class="reset-form">
        <view class="form-group">
          <text class="label">邮箱</text>
          <input
            type="text"
            v-model="emailForm.email"
            placeholder="请输入邮箱"
            class="input"
          />
        </view>

        <view class="form-group">
          <text class="label">验证码</text>
          <view class="code-wrapper">
            <input
              type="text"
              v-model="emailForm.code"
              placeholder="请输入验证码"
              class="input code-input"
            />
            <button
              class="btn-code"
              :disabled="emailCounting || !isValidEmail"
              @click="sendEmailCode"
            >
              {{ emailCountDown ? `${emailCountDown}秒后重发` : '获取验证码' }}
            </button>
          </view>
        </view>

        <view class="form-group">
          <text class="label">新密码</text>
          <input
            :type="showEmailPassword ? 'text' : 'password'"
            v-model="emailForm.password"
            placeholder="请输入新密码（至少8位）"
            class="input"
            minlength="8"
          />
        </view>

        <view class="form-group">
          <text class="label">确认密码</text>
          <input
            :type="showEmailPassword ? 'text' : 'password'"
            v-model="emailForm.password_confirm"
            placeholder="请再次输入新密码"
            class="input"
            minlength="8"
          />
        </view>

        <view class="form-actions">
          <button class="btn-reset" :disabled="loading || !isValidEmailForm" @click="handleEmailReset">
            {{ loading ? '提交中...' : '重置密码' }}
          </button>
        </view>
      </view>

      <view class="reset-footer">
        <text>记起密码了？</text>
        <text class="login-link" @click="goToLogin">返回登录</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import userApi from '../../api/user'

const loading = ref(false)
const activeTab = ref('phone')

const phoneForm = ref({
  phone: '',
  code: '',
  password: '',
  password_confirm: ''
})

const emailForm = ref({
  email: '',
  code: '',
  password: '',
  password_confirm: ''
})

const phoneCountDown = ref(0)
const emailCountDown = ref(0)
const showPhonePassword = ref(false)
const showEmailPassword = ref(false)

const phoneCounting = computed(() => phoneCountDown.value > 0)
const emailCounting = computed(() => emailCountDown.value > 0)

const isValidPhone = computed(() => {
  const phoneRegex = /^1[3-9]\d{9}$/
  return phoneRegex.test(phoneForm.value.phone)
})

const isValidEmail = computed(() => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(emailForm.value.email)
})

const isValidPhoneForm = computed(() => {
  return phoneForm.value.code &&
         phoneForm.value.password.length >= 8 &&
         phoneForm.value.password === phoneForm.value.password_confirm
})

const isValidEmailForm = computed(() => {
  return emailForm.value.code &&
         emailForm.value.password.length >= 8 &&
         emailForm.value.password === emailForm.value.password_confirm
})

const startCountDown = (type) => {
  const target = type === 'phone' ? phoneCountDown : emailCountDown
  target.value = 60
  const timer = setInterval(() => {
    target.value--
    if (target.value <= 0) {
      clearInterval(timer)
    }
  }, 1000)
}

const sendPhoneCode = async () => {
  if (!isValidPhone.value) {
    uni.showToast({ title: '请输入正确的手机号', icon: 'none' })
    return
  }

  try {
    await userApi.sendPhoneCode({
      phone: phoneForm.value.phone,
      purpose: 'reset_password'
    })
    startCountDown('phone')
    uni.showToast({ title: '验证码已发送', icon: 'success' })
  } catch (error) {
    console.error('发送验证码失败:', error)
    uni.showToast({ title: '发送失败，请稍后重试', icon: 'none' })
  }
}

const sendEmailCode = async () => {
  if (!isValidEmail.value) {
    uni.showToast({ title: '请输入正确的邮箱', icon: 'none' })
    return
  }

  try {
    await userApi.sendEmailCode({
      email: emailForm.value.email,
      purpose: 'reset_password'
    })
    startCountDown('email')
    uni.showToast({ title: '验证码已发送', icon: 'success' })
  } catch (error) {
    console.error('发送验证码失败:', error)
    uni.showToast({ title: '发送失败，请稍后重试', icon: 'none' })
  }
}

const handlePhoneReset = async () => {
  if (!isValidPhone.value) {
    uni.showToast({ title: '请输入正确的手机号', icon: 'none' })
    return
  }

  if (phoneForm.value.password.length < 8) {
    uni.showToast({ title: '密码长度不能少于8位', icon: 'none' })
    return
  }

  if (phoneForm.value.password !== phoneForm.value.password_confirm) {
    uni.showToast({ title: '两次输入的密码不一致', icon: 'none' })
    return
  }

  try {
    loading.value = true
    await userApi.resetPassword({
      phone: phoneForm.value.phone,
      code: phoneForm.value.code,
      password: phoneForm.value.password,
      password_confirm: phoneForm.value.password_confirm
    })
    uni.showToast({ title: '密码重置成功', icon: 'success' })
    setTimeout(() => {
      uni.navigateTo({ url: '/pages/login/login' })
    }, 1500)
  } catch (error) {
    console.error('密码重置失败:', error)
    uni.showToast({ title: '重置失败，请检查信息', icon: 'none' })
  } finally {
    loading.value = false
  }
}

const handleEmailReset = async () => {
  if (!isValidEmail.value) {
    uni.showToast({ title: '请输入正确的邮箱', icon: 'none' })
    return
  }

  if (emailForm.value.password.length < 8) {
    uni.showToast({ title: '密码长度不能少于8位', icon: 'none' })
    return
  }

  if (emailForm.value.password !== emailForm.value.password_confirm) {
    uni.showToast({ title: '两次输入的密码不一致', icon: 'none' })
    return
  }

  try {
    loading.value = true
    await userApi.resetPassword({
      email: emailForm.value.email,
      code: emailForm.value.code,
      password: emailForm.value.password,
      password_confirm: emailForm.value.password_confirm
    })
    uni.showToast({ title: '密码重置成功', icon: 'success' })
    setTimeout(() => {
      uni.navigateTo({ url: '/pages/login/login' })
    }, 1500)
  } catch (error) {
    console.error('密码重置失败:', error)
    uni.showToast({ title: '重置失败，请检查信息', icon: 'none' })
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
  padding: 40rpx 30rpx;
}

.reset-card {
  background-color: #fff;
  border-radius: 20rpx;
  padding: 50rpx 30rpx;
}

.reset-header {
  text-align: center;
  margin-bottom: 40rpx;
}

.title {
  display: block;
  font-size: 40rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 15rpx;
}

.subtitle {
  display: block;
  font-size: 26rpx;
  color: #999;
}

.reset-tabs {
  display: flex;
  border-bottom: 1rpx solid #eee;
  margin-bottom: 40rpx;
}

.tab-item {
  flex: 1;
  text-align: center;
  padding: 25rpx 0;
  font-size: 28rpx;
  color: #666;
  border-bottom: 4rpx solid transparent;
}

.tab-item.active {
  color: #4361ee;
  border-bottom-color: #4361ee;
  font-weight: 500;
}

.form-group {
  margin-bottom: 30rpx;
}

.label {
  display: block;
  font-size: 28rpx;
  color: #555;
  margin-bottom: 15rpx;
}

.input {
  width: 100%;
  height: 80rpx;
  background-color: #f9f9f9;
  border-radius: 12rpx;
  padding: 0 25rpx;
  font-size: 28rpx;
  color: #333;
  box-sizing: border-box;
}

.code-wrapper {
  display: flex;
  gap: 20rpx;
}

.code-input {
  flex: 1;
}

.btn-code {
  width: 220rpx;
  height: 80rpx;
  background-color: #4361ee;
  color: #fff;
  font-size: 24rpx;
  border-radius: 12rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
}

.btn-code[disabled] {
  background-color: #ccc;
}

.form-actions {
  margin-top: 50rpx;
}

.btn-reset {
  width: 100%;
  height: 90rpx;
  background-color: #4361ee;
  color: #fff;
  font-size: 32rpx;
  font-weight: 500;
  border-radius: 45rpx;
  border: none;
}

.btn-reset[disabled] {
  background-color: #ccc;
}

.reset-footer {
  text-align: center;
  margin-top: 40rpx;
  font-size: 26rpx;
  color: #666;
}

.login-link {
  color: #4361ee;
  margin-left: 10rpx;
}
</style>
