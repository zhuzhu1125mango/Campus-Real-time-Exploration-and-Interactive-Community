<template>
  <div class="auth-page container-narrow page-padding">
    <SectionHeader
      title="创建新账号"
      subtitle="加入校园互动社区，开启精彩校园生活"
      icon="i-ep-user-filled"
    />

    <GlassCard :hover="false" class="auth-card" padding="lg">
      <div class="auth-tabs">
        <button
          @click="activeTab = 'email'"
          :class="['tab-btn', { active: activeTab === 'email' }]"
        >
          邮箱注册
        </button>
        <button
          @click="activeTab = 'phone'"
          :class="['tab-btn', { active: activeTab === 'phone' }]"
        >
          手机号注册
        </button>
      </div>

      <!-- 邮箱注册 -->
      <form v-if="activeTab === 'email'" @submit.prevent="handleEmailRegister" class="auth-form">
        <div class="form-group">
          <label for="username-email">用户名</label>
          <div class="input-wrapper">
            <span class="input-icon i-ep-user" />
            <input
              type="text"
              id="username-email"
              v-model="emailForm.username"
              required
              placeholder="请输入用户名"
              minlength="3"
              maxlength="30"
              class="form-input"
            />
          </div>
        </div>

        <div class="form-group">
          <label for="email">邮箱</label>
          <div class="input-wrapper">
            <span class="input-icon i-ep-message" />
            <input
              type="email"
              id="email"
              v-model="emailForm.email"
              required
              placeholder="请输入邮箱"
              class="form-input"
            />
          </div>
        </div>

        <div class="form-group">
          <label for="emailCode">验证码</label>
          <div class="input-wrapper code-wrapper">
            <span class="input-icon i-ep-key" />
            <input
              type="text"
              id="emailCode"
              v-model="emailForm.code"
              required
              placeholder="请输入验证码"
              class="form-input"
            />
            <button
              type="button"
              class="btn btn-secondary code-btn"
              :disabled="emailCounting || !isValidEmail"
              @click="sendEmailCode"
            >
              {{ emailCountDown ? `${emailCountDown}秒后重发` : '获取验证码' }}
            </button>
          </div>
        </div>

        <div class="form-group">
          <label for="password-email">密码</label>
          <div class="input-wrapper">
            <span class="input-icon i-ep-lock" />
            <input
              :type="showPasswordEmail ? 'text' : 'password'"
              id="password-email"
              v-model="emailForm.password"
              required
              placeholder="请输入密码"
              minlength="8"
              class="form-input"
            />
            <button
              type="button"
              class="btn-toggle-password"
              @click="showPasswordEmail = !showPasswordEmail"
            >
              <span :class="['toggle-password-icon', showPasswordEmail ? 'i-ep-view' : 'i-ep-hide']" />
            </button>
          </div>
        </div>

        <div class="form-group">
          <label for="confirmPassword-email">确认密码</label>
          <div class="input-wrapper">
            <span class="input-icon i-ep-lock" />
            <input
              :type="showConfirmPasswordEmail ? 'text' : 'password'"
              id="confirmPassword-email"
              v-model="emailForm.password_confirm"
              required
              placeholder="请再次输入密码"
              minlength="8"
              class="form-input"
            />
            <button
              type="button"
              class="btn-toggle-password"
              @click="showConfirmPasswordEmail = !showConfirmPasswordEmail"
            >
              <span :class="['toggle-password-icon', showConfirmPasswordEmail ? 'i-ep-view' : 'i-ep-hide']" />
            </button>
          </div>
        </div>

        <div class="form-actions">
          <button type="submit" class="btn btn-primary" :disabled="loading">
            <span v-if="loading" class="loading-spinner" />
            <span>{{ loading ? '注册中...' : '注册' }}</span>
          </button>
        </div>
      </form>

      <!-- 手机号注册 -->
      <form v-if="activeTab === 'phone'" @submit.prevent="handlePhoneRegister" class="auth-form">
        <div class="form-group">
          <label for="username-phone">用户名</label>
          <div class="input-wrapper">
            <span class="input-icon i-ep-user" />
            <input
              type="text"
              id="username-phone"
              v-model="phoneForm.username"
              required
              placeholder="请输入用户名"
              minlength="3"
              maxlength="30"
              class="form-input"
            />
          </div>
        </div>

        <div class="form-group">
          <label for="phone">手机号</label>
          <div class="input-wrapper">
            <span class="input-icon i-ep-iphone" />
            <input
              type="tel"
              id="phone"
              v-model="phoneForm.phone"
              required
              placeholder="请输入手机号"
              pattern="^1[3-9]\d{9}$"
              class="form-input"
            />
          </div>
        </div>

        <div class="form-group">
          <label for="phoneCode">验证码</label>
          <div class="input-wrapper code-wrapper">
            <span class="input-icon i-ep-key" />
            <input
              type="text"
              id="phoneCode"
              v-model="phoneForm.code"
              required
              placeholder="请输入验证码"
              class="form-input"
            />
            <button
              type="button"
              class="btn btn-secondary code-btn"
              :disabled="phoneCounting || !isValidPhone"
              @click="sendPhoneCode"
            >
              {{ phoneCountDown ? `${phoneCountDown}秒后重发` : '获取验证码' }}
            </button>
          </div>
        </div>

        <div class="form-group">
          <label for="password-phone">密码</label>
          <div class="input-wrapper">
            <span class="input-icon i-ep-lock" />
            <input
              :type="showPasswordPhone ? 'text' : 'password'"
              id="password-phone"
              v-model="phoneForm.password"
              required
              placeholder="请输入密码"
              minlength="8"
              class="form-input"
            />
            <button
              type="button"
              class="btn-toggle-password"
              @click="showPasswordPhone = !showPasswordPhone"
            >
              <span :class="['toggle-password-icon', showPasswordPhone ? 'i-ep-view' : 'i-ep-hide']" />
            </button>
          </div>
        </div>

        <div class="form-group">
          <label for="confirmPassword-phone">确认密码</label>
          <div class="input-wrapper">
            <span class="input-icon i-ep-lock" />
            <input
              :type="showConfirmPasswordPhone ? 'text' : 'password'"
              id="confirmPassword-phone"
              v-model="phoneForm.password_confirm"
              required
              placeholder="请再次输入密码"
              minlength="8"
              class="form-input"
            />
            <button
              type="button"
              class="btn-toggle-password"
              @click="showConfirmPasswordPhone = !showConfirmPasswordPhone"
            >
              <span :class="['toggle-password-icon', showConfirmPasswordPhone ? 'i-ep-view' : 'i-ep-hide']" />
            </button>
          </div>
        </div>

        <div class="form-actions">
          <button type="submit" class="btn btn-primary" :disabled="loading">
            <span v-if="loading" class="loading-spinner" />
            <span>{{ loading ? '注册中...' : '注册' }}</span>
          </button>
        </div>
      </form>

      <div class="auth-footer">
        <p>已有账号？ <router-link to="/login" class="auth-link">立即登录</router-link></p>
      </div>
    </GlassCard>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import GlassCard from '@/components/GlassCard.vue'
import SectionHeader from '@/components/SectionHeader.vue'
import { userApi } from '../api/user'
import { useToast } from '../composables/useToast'
import { getApiErrorMessage } from '../utils/error'

const router = useRouter()
const { showToast } = useToast()
const loading = ref(false)
const activeTab = ref('email')

// 控制密码显示/隐藏状态
const showPasswordEmail = ref(false)
const showConfirmPasswordEmail = ref(false)
const showPasswordPhone = ref(false)
const showConfirmPasswordPhone = ref(false)

// 邮箱注册表单
const emailForm = ref({
  username: '',
  email: '',
  code: '',
  password: '',
  password_confirm: ''
})

// 手机号注册表单
const phoneForm = ref({
  username: '',
  phone: '',
  code: '',
  password: '',
  password_confirm: ''
})

// 验证码倒计时
const emailCountDown = ref(0)
const phoneCountDown = ref(0)
const emailCounting = computed(() => emailCountDown.value > 0)
const phoneCounting = computed(() => phoneCountDown.value > 0)

// 表单验证
const isValidEmail = computed(() => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(emailForm.value.email)
})

const isValidPhone = computed(() => {
  const phoneRegex = /^1[3-9]\d{9}$/
  return phoneRegex.test(phoneForm.value.phone)
})

// 邮箱注册
const handleEmailRegister = async () => {
  // 验证用户名
  if (!emailForm.value.username.trim()) {
    showToast('请输入用户名', 'error')
    return
  }

  // 验证邮箱
  if (!isValidEmail.value) {
    showToast('请输入正确的邮箱地址', 'error')
    return
  }

  // 验证密码
  if (emailForm.value.password !== emailForm.value.password_confirm) {
    showToast('两次输入的密码不一致', 'error')
    return
  }

  if (emailForm.value.password.length < 8) {
    showToast('密码长度不能少于8位', 'error')
    return
  }

  loading.value = true

  try {
    const registerData: any = {
      username: emailForm.value.username,
      email: emailForm.value.email,
      password: emailForm.value.password,
      password_confirm: emailForm.value.password_confirm
    }

    // 只有当用户输入了验证码时，才发送code字段
    if (emailForm.value.code) {
      registerData.code = emailForm.value.code
    }

    await userApi.register(registerData)

    showToast('注册成功，请登录', 'success')

    // 注册成功，跳转到登录页
    router.push('/login')
  } catch (error) {
    const data = (error as { response?: { data?: Record<string, unknown> } }).response?.data
    let errorMsg = '注册失败，请稍后重试'
    if (data?.detail) {
      errorMsg = data.detail as string
    } else if (data) {
      for (const key in data) {
        const val = data[key]
        if (Array.isArray(val) && val.length > 0) {
          errorMsg = String(val[0])
          break
        }
      }
    } else if (error instanceof Error) {
      errorMsg = error.message
    }
    showToast(errorMsg, 'error')
  } finally {
    loading.value = false
  }
}

// 手机号注册
const handlePhoneRegister = async () => {
  // 验证用户名
  if (!phoneForm.value.username.trim()) {
    showToast('请输入用户名', 'error')
    return
  }

  // 验证手机号
  if (!isValidPhone.value) {
    showToast('请输入正确的手机号', 'error')
    return
  }

  // 验证密码
  if (phoneForm.value.password !== phoneForm.value.password_confirm) {
    showToast('两次输入的密码不一致', 'error')
    return
  }

  if (phoneForm.value.password.length < 8) {
    showToast('密码长度不能少于8位', 'error')
    return
  }

  loading.value = true

  try {
    const registerData: any = {
      username: phoneForm.value.username,
      phone: phoneForm.value.phone,
      password: phoneForm.value.password,
      password_confirm: phoneForm.value.password_confirm
    }

    // 只有当用户输入了验证码时，才发送code字段
    if (phoneForm.value.code) {
      registerData.code = phoneForm.value.code
    }

    await userApi.register(registerData)

    showToast('注册成功，请登录', 'success')

    // 注册成功，跳转到登录页
    router.push('/login')
  } catch (error) {
    const data = (error as { response?: { data?: Record<string, unknown> } }).response?.data
    let errorMsg = '注册失败，请稍后重试'
    if (data?.detail) {
      errorMsg = data.detail as string
    } else if (data) {
      for (const key in data) {
        const val = data[key]
        if (Array.isArray(val) && val.length > 0) {
          errorMsg = String(val[0])
          break
        }
      }
    } else if (error instanceof Error) {
      errorMsg = error.message
    }
    showToast(errorMsg, 'error')
  } finally {
    loading.value = false
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
      purpose: 'register'
    })

    // 开始倒计时
    emailCountDown.value = 60
    const timer = setInterval(() => {
      emailCountDown.value--
      if (emailCountDown.value <= 0) {
        clearInterval(timer)
      }
    }, 1000)

    showToast('验证码已发送，请查看邮箱', 'success')
  } catch (error) {
    showToast(getApiErrorMessage(error, '发送验证码失败'), 'error')
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
      purpose: 'register'
    })

    // 开始倒计时
    phoneCountDown.value = 60
    const timer = setInterval(() => {
      phoneCountDown.value--
      if (phoneCountDown.value <= 0) {
        clearInterval(timer)
      }
    }, 1000)

    showToast('验证码已发送，请注意查收', 'success')
  } catch (error) {
    showToast(getApiErrorMessage(error, '发送验证码失败'), 'error')
  }
}
</script>

<style scoped>
.auth-page {
  min-height: calc(100vh - 200px);
}

.auth-card {
  max-width: 520px;
  margin: 0 auto;
}

.auth-tabs {
  display: flex;
  border-bottom: 1px solid var(--border-color);
  margin-bottom: var(--space-6);
}

.tab-btn {
  flex: 1;
  padding: var(--space-3) 0;
  background: none;
  border: none;
  color: var(--text-secondary);
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.tab-btn.active {
  color: var(--primary-600);
  font-weight: 600;
}

.tab-btn.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 20%;
  width: 60%;
  height: 3px;
  background-color: var(--primary-600);
  border-radius: var(--radius-sm) var(--radius-sm) 0 0;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.form-group label {
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--text-primary);
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.code-wrapper {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: var(--space-2);
}

.input-icon {
  position: absolute;
  left: var(--space-3);
  color: var(--text-tertiary);
  font-size: 1.1rem;
  pointer-events: none;
}

.form-input {
  width: 100%;
  padding: var(--space-3) var(--space-4);
  padding-left: 2.5rem;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  font-size: 1rem;
  background: var(--bg-primary);
  color: var(--text-primary);
  transition: border-color 0.2s, box-shadow 0.2s;
}

.form-input:focus {
  outline: none;
  border-color: var(--primary-400);
  box-shadow: 0 0 0 3px var(--primary-100);
}

.form-input::placeholder {
  color: var(--text-tertiary);
}

.dark .form-input:focus {
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
}

.btn-toggle-password {
  position: absolute;
  right: var(--space-3);
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-1);
  color: var(--text-tertiary);
  background: none;
  border: none;
  cursor: pointer;
  transition: color 0.2s;
}

.btn-toggle-password:hover {
  color: var(--text-secondary);
}

.toggle-password-icon {
  font-size: 1.1rem;
}

.code-btn {
  padding: var(--space-2) var(--space-3);
  font-size: 0.85rem;
  white-space: nowrap;
}

.form-actions {
  margin-top: var(--space-2);
}

.form-actions .btn {
  width: 100%;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-6);
  border-radius: var(--radius-lg);
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: all 0.2s;
}

.btn-primary {
  background-color: var(--primary-600);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: var(--primary-700);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background-color: var(--bg-tertiary);
  color: var(--text-primary);
}

.btn-secondary:hover:not(:disabled) {
  background-color: var(--border-color-light);
}

.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: spin 1s ease-in-out infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.auth-footer {
  margin-top: var(--space-6);
  padding-top: var(--space-6);
  border-top: 1px solid var(--border-color-light);
  text-align: center;
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.auth-link {
  color: var(--text-link);
  font-weight: 600;
}

.auth-link:hover {
  color: var(--primary-500);
}

@media (max-width: 640px) {
  .auth-card {
    max-width: 100%;
  }

  .tab-btn {
    font-size: 0.85rem;
  }
}
</style>
