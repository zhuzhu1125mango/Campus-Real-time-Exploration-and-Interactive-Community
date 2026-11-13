<template>
  <div class="auth-page container-narrow page-padding">
    <SectionHeader
      title="重置密码"
      subtitle="请选择验证方式重置您的密码"
      icon="i-ep-key"
    />

    <GlassCard :hover="false" class="auth-card" padding="lg">
      <div class="auth-tabs">
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

      <!-- 手机验证码重置 -->
      <form v-if="activeTab === 'phone'" @submit.prevent="handlePhoneReset" class="auth-form">
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
          <label for="phonePassword">新密码</label>
          <div class="input-wrapper">
            <span class="input-icon i-ep-lock" />
            <input
              :type="showPhonePassword ? 'text' : 'password'"
              id="phonePassword"
              v-model="phoneForm.password"
              required
              placeholder="请输入新密码"
              minlength="8"
              class="form-input"
            />
            <button
              type="button"
              class="btn-toggle-password"
              @click="showPhonePassword = !showPhonePassword"
            >
              <span :class="['toggle-password-icon', showPhonePassword ? 'i-ep-view' : 'i-ep-hide']" />
            </button>
          </div>
        </div>

        <div class="form-group">
          <label for="phonePasswordConfirm">确认密码</label>
          <div class="input-wrapper">
            <span class="input-icon i-ep-lock" />
            <input
              :type="showPhonePasswordConfirm ? 'text' : 'password'"
              id="phonePasswordConfirm"
              v-model="phoneForm.password_confirm"
              required
              placeholder="请再次输入密码"
              minlength="8"
              class="form-input"
            />
            <button
              type="button"
              class="btn-toggle-password"
              @click="showPhonePasswordConfirm = !showPhonePasswordConfirm"
            >
              <span :class="['toggle-password-icon', showPhonePasswordConfirm ? 'i-ep-view' : 'i-ep-hide']" />
            </button>
          </div>
        </div>

        <div class="form-actions">
          <button type="submit" class="btn btn-primary" :disabled="loading">
            <span v-if="loading" class="loading-spinner" />
            <span>{{ loading ? '提交中...' : '重置密码' }}</span>
          </button>
        </div>
      </form>

      <!-- 邮箱验证码重置 -->
      <form v-if="activeTab === 'email'" @submit.prevent="handleEmailReset" class="auth-form">
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
          <label for="emailPassword">新密码</label>
          <div class="input-wrapper">
            <span class="input-icon i-ep-lock" />
            <input
              :type="showEmailPassword ? 'text' : 'password'"
              id="emailPassword"
              v-model="emailForm.password"
              required
              placeholder="请输入新密码"
              minlength="8"
              class="form-input"
            />
            <button
              type="button"
              class="btn-toggle-password"
              @click="showEmailPassword = !showEmailPassword"
            >
              <span :class="['toggle-password-icon', showEmailPassword ? 'i-ep-view' : 'i-ep-hide']" />
            </button>
          </div>
        </div>

        <div class="form-group">
          <label for="emailPasswordConfirm">确认密码</label>
          <div class="input-wrapper">
            <span class="input-icon i-ep-lock" />
            <input
              :type="showEmailPasswordConfirm ? 'text' : 'password'"
              id="emailPasswordConfirm"
              v-model="emailForm.password_confirm"
              required
              placeholder="请再次输入密码"
              minlength="8"
              class="form-input"
            />
            <button
              type="button"
              class="btn-toggle-password"
              @click="showEmailPasswordConfirm = !showEmailPasswordConfirm"
            >
              <span :class="['toggle-password-icon', showEmailPasswordConfirm ? 'i-ep-view' : 'i-ep-hide']" />
            </button>
          </div>
        </div>

        <div class="form-actions">
          <button type="submit" class="btn btn-primary" :disabled="loading">
            <span v-if="loading" class="loading-spinner" />
            <span>{{ loading ? '提交中...' : '重置密码' }}</span>
          </button>
        </div>
      </form>

      <div class="auth-footer">
        <p>记起密码了？ <router-link to="/login" class="auth-link">返回登录</router-link></p>
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
const activeTab = ref('phone')

// 手机验证码表单
const phoneForm = ref({
  phone: '',
  code: '',
  password: '',
  password_confirm: ''
})

// 邮箱验证码表单
const emailForm = ref({
  email: '',
  code: '',
  password: '',
  password_confirm: ''
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

// 密码验证
const isValidPhoneForm = computed(() => {
  return phoneForm.value.password.length >= 8 &&
         phoneForm.value.password === phoneForm.value.password_confirm
})

const isValidEmailForm = computed(() => {
  return emailForm.value.password.length >= 8 &&
         emailForm.value.password === emailForm.value.password_confirm
})

// 控制密码显示/隐藏状态
const showPhonePassword = ref(false)
const showPhonePasswordConfirm = ref(false)
const showEmailPassword = ref(false)
const showEmailPasswordConfirm = ref(false)

// 手机验证码重置密码
const handlePhoneReset = async () => {
  if (!isValidPhone.value) {
    showToast('请输入正确的手机号', 'error')
    return
  }

  if (!isValidPhoneForm.value) {
    if (phoneForm.value.password.length < 8) {
      showToast('密码长度不能少于8位', 'error')
    } else {
      showToast('两次输入的密码不一致', 'error')
    }
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

    showToast('密码重置成功，请重新登录', 'success')

    // 重定向到登录页
    router.push('/login')
  } catch (error) {
    console.error('密码重置失败:', error)
    showToast(getApiErrorMessage(error, '密码重置失败，请检查信息是否正确'), 'error')
  } finally {
    loading.value = false
  }
}

// 邮箱验证码重置密码
const handleEmailReset = async () => {
  if (!isValidEmail.value) {
    showToast('请输入正确的邮箱', 'error')
    return
  }

  if (!isValidEmailForm.value) {
    if (emailForm.value.password.length < 8) {
      showToast('密码长度不能少于8位', 'error')
    } else {
      showToast('两次输入的密码不一致', 'error')
    }
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

    showToast('密码重置成功，请重新登录', 'success')

    // 重定向到登录页
    router.push('/login')
  } catch (error) {
    console.error('密码重置失败:', error)
    showToast(getApiErrorMessage(error, '密码重置失败，请检查信息是否正确'), 'error')
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
      purpose: 'reset_password'
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
  } catch (error) {
    console.error('发送验证码失败:', error)
    showToast(getApiErrorMessage(error, '发送验证码失败'), 'error')
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
      purpose: 'reset_password'
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
  } catch (error) {
    console.error('发送验证码失败:', error)
    showToast(getApiErrorMessage(error, '发送验证码失败'), 'error')
  }
}
</script>

<style scoped>
.auth-page {
  min-height: calc(100vh - 200px);
}

.auth-card {
  max-width: 480px;
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
