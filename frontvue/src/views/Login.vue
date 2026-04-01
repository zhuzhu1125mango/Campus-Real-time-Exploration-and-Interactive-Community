<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <h2>欢迎回来</h2>
        <p>请登录您的账号以继续使用</p>
      </div>
      
      <div class="login-tabs">
        <button 
          @click="activeTab = 'password'" 
          :class="['tab-btn', { active: activeTab === 'password' }]"
        >
          密码登录
        </button>
        <button 
          @click="activeTab = 'phone'" 
          :class="['tab-btn', { active: activeTab === 'phone' }]"
        >
          手机验证码
        </button>
        <button 
          @click="activeTab = 'email'" 
          :class="['tab-btn', { active: activeTab === 'email' }]"
        >
          邮箱验证码
        </button>
      </div>
      
      <!-- 密码登录 -->
      <form v-if="activeTab === 'password'" @submit.prevent="handlePasswordLogin" class="login-form">
        <div class="form-group">
          <label for="username">用户名</label>
          <div class="input-wrapper">
            <span class="input-icon user-icon"></span>
            <input
              type="text"
              id="username"
              v-model="passwordForm.username"
              required
              placeholder="请输入用户名"
            />
          </div>
        </div>
        
        <div class="form-group">
          <label for="password">密码</label>
          <div class="input-wrapper">
            <span class="input-icon password-icon"></span>
            <input
              :type="showPassword ? 'text' : 'password'"
              id="password"
              v-model="passwordForm.password"
              required
              placeholder="请输入密码"
            />
            <button 
              type="button" 
              class="btn-toggle-password" 
              @click="showPassword = !showPassword"
            >
              <span :class="['toggle-password-icon', showPassword ? 'show' : 'hide']"></span>
            </button>
          </div>
        </div>
        
        <div class="form-actions">
          <button type="submit" class="btn-login" :disabled="loading">
            <span v-if="loading" class="loading-spinner"></span>
            <span>{{ loading ? '登录中...' : '登录' }}</span>
          </button>
        </div>
      </form>
      
      <!-- 手机验证码登录 -->
      <form v-if="activeTab === 'phone'" @submit.prevent="handlePhoneLogin" class="login-form">
        <div class="form-group">
          <label for="phone">手机号</label>
          <div class="input-wrapper">
            <span class="input-icon phone-icon"></span>
            <input
              type="tel"
              id="phone"
              v-model="phoneForm.phone"
              required
              placeholder="请输入手机号"
              pattern="^1[3-9]\d{9}$"
            />
          </div>
        </div>
        
        <div class="form-group">
          <label for="phoneCode">验证码</label>
          <div class="input-wrapper code-wrapper">
            <span class="input-icon code-icon"></span>
            <input
              type="text"
              id="phoneCode"
              v-model="phoneForm.code"
              required
              placeholder="请输入验证码"
            />
            <button 
              type="button" 
              class="btn-code" 
              :disabled="phoneCounting || !isValidPhone" 
              @click="sendPhoneCode"
            >
              {{ phoneCountDown ? `${phoneCountDown}秒后重发` : '获取验证码' }}
            </button>
          </div>
        </div>
        
        <div class="form-actions">
          <button type="submit" class="btn-login" :disabled="loading">
            <span v-if="loading" class="loading-spinner"></span>
            <span>{{ loading ? '登录中...' : '登录' }}</span>
          </button>
        </div>
      </form>
      
      <!-- 邮箱验证码登录 -->
      <form v-if="activeTab === 'email'" @submit.prevent="handleEmailLogin" class="login-form">
        <div class="form-group">
          <label for="email">邮箱</label>
          <div class="input-wrapper">
            <span class="input-icon email-icon"></span>
            <input
              type="email"
              id="email"
              v-model="emailForm.email"
              required
              placeholder="请输入邮箱"
            />
          </div>
        </div>
        
        <div class="form-group">
          <label for="emailCode">验证码</label>
          <div class="input-wrapper code-wrapper">
            <span class="input-icon code-icon"></span>
            <input
              type="text"
              id="emailCode"
              v-model="emailForm.code"
              required
              placeholder="请输入验证码"
            />
            <button 
              type="button" 
              class="btn-code" 
              :disabled="emailCounting || !isValidEmail" 
              @click="sendEmailCode"
            >
              {{ emailCountDown ? `${emailCountDown}秒后重发` : '获取验证码' }}
            </button>
          </div>
        </div>
        
        <div class="form-actions">
          <button type="submit" class="btn-login" :disabled="loading">
            <span v-if="loading" class="loading-spinner"></span>
            <span>{{ loading ? '登录中...' : '登录' }}</span>
          </button>
        </div>
      </form>
      
      <div class="login-footer">
        <p>还没有账号？ <router-link to="/register" class="register-link">立即注册</router-link></p>
        <p class="forgot-password">
          <router-link to="/reset-password" class="register-link">忘记密码？</router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { userApi } from '../api/user'
import config from '../utils/config'
import { useToast } from '../composables/useToast'
import { useUserStore } from '../stores/userStore'

const router = useRouter()
const { showToast } = useToast()
const userStore = useUserStore()
const loading = ref(false)
const activeTab = ref('password')
const showPassword = ref(false)

// 密码登录表单
const passwordForm = ref({
  username: '',
  password: ''
})

// 手机验证码登录表单
const phoneForm = ref({
  phone: '',
  code: ''
})

// 邮箱验证码登录表单
const emailForm = ref({
  email: '',
  code: ''
})

// 验证码倒计时
const phoneCountDown = ref(0)
const emailCountDown = ref(0)
const phoneCounting = computed(() => phoneCountDown.value > 0)
const emailCounting = computed(() => emailCountDown.value > 0)

// 表单验证
const isValidPhone = computed(() => {
  const phoneRegex = /^1[3-9]\d{9}$/
  return phoneRegex.test(phoneForm.value.phone)
})

const isValidEmail = computed(() => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(emailForm.value.email)
})

// 密码登录
const handlePasswordLogin = async () => {
  try {
    loading.value = true
    // 直接使用userStore的login方法
    const success = await userStore.login(passwordForm.value.username, passwordForm.value.password)
    
    if (success) {
      // 显示成功提示
      showToast('登录成功', 'success')
      
      // 重定向到首页
      router.push('/')
    } else {
      showToast(userStore.error || '登录失败，请检查用户名和密码', 'error')
    }
  } catch (error: any) {
    const errorMessage = error.response?.data?.detail || error.message || '登录过程中发生错误'
    showToast(errorMessage, 'error')
  } finally {
    loading.value = false
  }
}

// 手机验证码登录
const handlePhoneLogin = async () => {
  if (!isValidPhone.value) {
    showToast('请输入正确的手机号', 'error')
    return
  }
  
  try {
    loading.value = true
    const tokenData = await userApi.phoneCodeLogin(phoneForm.value)
    
    // 保存token到localStorage
    localStorage.setItem(config.jwt.accessTokenKey, tokenData.access)
    localStorage.setItem(config.jwt.refreshTokenKey, tokenData.refresh)
    
    // 更新userStore中的状态
    const userInfo = await userStore.fetchUserProfile()
    
    if (userInfo) {
      // 显示成功提示
      showToast('登录成功', 'success')
      
      // 重定向到首页
      router.push('/')
    } else {
      // 获取用户信息失败
      showToast('登录成功但获取用户信息失败', 'error')
      // 清除token
      userStore.logout()
    }
  } catch (error: any) {
    const errorMsg = error.response?.data?.detail || error.message || '登录失败，请检查手机号和验证码'
    showToast(errorMsg, 'error')
    // 清除token
    userStore.logout()
  } finally {
    loading.value = false
  }
}

// 邮箱验证码登录
const handleEmailLogin = async () => {
  if (!isValidEmail.value) {
    showToast('请输入正确的邮箱', 'error')
    return
  }
  
  try {
    loading.value = true
    const tokenData = await userApi.emailCodeLogin(emailForm.value)
    
    // 保存token到localStorage
    localStorage.setItem(config.jwt.accessTokenKey, tokenData.access)
    localStorage.setItem(config.jwt.refreshTokenKey, tokenData.refresh)
    
    // 更新userStore中的状态
    const userInfo = await userStore.fetchUserProfile()
    
    if (userInfo) {
      // 显示成功提示
      showToast('登录成功', 'success')
      
      // 重定向到首页
      router.push('/')
    } else {
      // 获取用户信息失败
      showToast('登录成功但获取用户信息失败', 'error')
      // 清除token
      userStore.logout()
    }
  } catch (error: any) {
    const errorMsg = error.response?.data?.detail || error.message || '登录失败，请检查邮箱和验证码'
    showToast(errorMsg, 'error')
    // 清除token
    userStore.logout()
  } finally {
    loading.value = false
  }
}

// 发送手机验证码
const sendPhoneCode = async () => {
  if (!isValidPhone.value) {
    showToast('请输入正确的手机号', 'error')
    return
  }
  
  try {
    await userApi.sendPhoneCode({
      phone: phoneForm.value.phone,
      purpose: 'login'
    })
    
    // 开始倒计时
    phoneCountDown.value = 60
    const timer = setInterval(() => {
      phoneCountDown.value--
      if (phoneCountDown.value <= 0) {
        clearInterval(timer)
      }
    }, 1000)
    
    showToast('验证码已发送', 'success')
  } catch (error: any) {
    const errorMsg = error.response?.data?.detail || error.message || '发送验证码失败'
    showToast(errorMsg, 'error')
  }
}

// 发送邮箱验证码
const sendEmailCode = async () => {
  if (!isValidEmail.value) {
    showToast('请输入正确的邮箱', 'error')
    return
  }
  
  try {
    await userApi.sendEmailCode({
      email: emailForm.value.email,
      purpose: 'login'
    })
    
    // 开始倒计时
    emailCountDown.value = 60
    const timer = setInterval(() => {
      emailCountDown.value--
      if (emailCountDown.value <= 0) {
        clearInterval(timer)
      }
    }, 1000)
    
    showToast('验证码已发送', 'success')
  } catch (error: any) {
    const errorMsg = error.response?.data?.detail || error.message || '发送验证码失败'
    showToast(errorMsg, 'error')
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: calc(100vh - 130px);
  padding: 2rem 1rem;
  background-color: #f9fafc;
}

.login-card {
  width: 100%;
  max-width: 450px;
  background-color: white;
  border-radius: 16px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.login-header {
  padding: 2.5rem 2.5rem 1.5rem;
  text-align: center;
}

.login-header h2 {
  font-size: 1.8rem;
  color: #333;
  margin-bottom: 0.5rem;
  font-weight: 700;
}

.login-header p {
  color: #666;
  font-size: 1rem;
}

.login-tabs {
  display: flex;
  border-bottom: 1px solid #eee;
  margin-bottom: 1.5rem;
}

.tab-btn {
  flex: 1;
  padding: 1rem 0;
  background: none;
  border: none;
  color: #666;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
}

.tab-btn.active {
  color: #4361ee;
  font-weight: 600;
}

.tab-btn.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 20%;
  width: 60%;
  height: 3px;
  background-color: #4361ee;
  border-radius: 3px 3px 0 0;
}

.login-form {
  padding: 0 2.5rem 2rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

label {
  display: block;
  margin-bottom: 0.5rem;
  color: #555;
  font-weight: 500;
  font-size: 0.9rem;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.code-wrapper {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 8px;
}

.input-icon {
  position: absolute;
  left: 12px;
  width: 20px;
  height: 20px;
  background-position: center;
  background-repeat: no-repeat;
  background-size: contain;
  opacity: 0.5;
}

.user-icon {
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%234361ee"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>');
}

.password-icon {
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%234361ee"><path d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1 1.71 0 3.1 1.39 3.1 3.1v2z"/></svg>');
}

.phone-icon {
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%234361ee"><path d="M16 1H8C6.34 1 5 2.34 5 4v16c0 1.66 1.34 3 3 3h8c1.66 0 3-1.34 3-3V4c0-1.66-1.34-3-3-3zm-2 20h-4v-1h4v1zm3.25-3H6.75V4h10.5v14z"/></svg>');
}

.email-icon {
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%234361ee"><path d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/></svg>');
}

.code-icon {
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%234361ee"><path d="M22 3H2C.9 3 0 3.9 0 5v14c0 1.1.9 2 2 2h20c1.1 0 1.99-.9 1.99-2L24 5c0-1.1-.9-2-2-2zm0 16H2V5h20v14zM10 8h4c1.1 0 2 .9 2 2s-.9 2-2 2h-4v-2h4v-2h-4v2z"/></svg>');
}

input {
  width: 100%;
  padding: 0.8rem 0.8rem 0.8rem 2.5rem;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  font-size: 1rem;
  transition: all 0.3s;
}

input:focus {
  outline: none;
  border-color: #4361ee;
  box-shadow: 0 0 0 3px rgba(67, 97, 238, 0.1);
}

.btn-code {
  min-width: 110px;
  padding: 0.8rem;
  background-color: #4361ee;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  white-space: nowrap;
}

.btn-code:hover:not(:disabled) {
  background-color: #3a56d4;
}

.btn-code:disabled {
  background-color: #b0b0b0;
  cursor: not-allowed;
}

.form-actions {
  margin-top: 2rem;
}

.btn-login {
  width: 100%;
  padding: 0.9rem;
  background-color: #4361ee;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 0.5rem;
}

.btn-login:hover {
  background-color: #3a56d4;
  transform: translateY(-2px);
  box-shadow: 0 4px 6px rgba(67, 97, 238, 0.2);
}

.btn-login:disabled {
  background-color: #b0b0b0;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.loading-spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255,255,255,0.3);
  border-radius: 50%;
  border-top-color: #fff;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.login-footer {
  padding: 1.5rem;
  background-color: #f8f9ff;
  text-align: center;
  border-top: 1px solid #f0f0f0;
}

.register-link {
  color: #4361ee;
  font-weight: 600;
  text-decoration: none;
}

.register-link:hover {
  text-decoration: underline;
}

.forgot-password {
  margin-top: 0.5rem;
  font-size: 0.9rem;
}

@media (max-width: 480px) {
  .login-card {
    max-width: 100%;
  }
  
  .login-header {
    padding: 2rem 1.5rem 1rem;
  }
  
  .login-form {
    padding: 0 1.5rem 1.5rem;
  }
  
  .tab-btn {
    font-size: 0.8rem;
    padding: 0.8rem 0;
  }
}

/* 密码显示/隐藏按钮样式 */
.btn-toggle-password {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  padding: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
  outline: none;
}

.toggle-password-icon {
  width: 20px;
  height: 20px;
  display: inline-block;
  background-size: contain;
  background-repeat: no-repeat;
  background-position: center;
}

.toggle-password-icon.show {
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%23666"><path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/></svg>');
}

.toggle-password-icon.hide {
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%23666"><path d="M12 7c2.76 0 5 2.24 5 5 0 .65-.13 1.26-.36 1.83l2.92 2.92c1.51-1.26 2.7-2.89 3.43-4.75-1.73-4.39-6-7.5-11-7.5-1.4 0-2.74.25-3.98.7l2.16 2.16C10.74 7.13 11.35 7 12 7zM2 4.27l2.28 2.28.46.46C3.08 8.3 1.78 10.02 1 12c1.73 4.39 6 7.5 11 7.5 1.55 0 3.03-.3 4.38-.84l.42.42L19.73 22 21 20.73 3.27 3 2 4.27zM7.53 9.8l1.55 1.55c-.05.21-.08.43-.08.65 0 1.66 1.34 3 3 3 .22 0 .44-.03.65-.08l1.55 1.55c-.67.33-1.41.53-2.2.53-2.76 0-5-2.24-5-5 0-.79.2-1.53.53-2.2zm4.31-.78l3.15 3.15.02-.16c0-1.66-1.34-3-3-3l-.17.01z"/></svg>');
}
</style> 