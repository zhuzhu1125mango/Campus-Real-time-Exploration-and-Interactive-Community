<template>
  <div class="auth-page container-narrow page-padding">
    <SectionHeader
      title="欢迎回来"
      subtitle="请登录您的账号以继续使用"
      icon="i-ep-user"
    />

    <GlassCard :hover="false" class="auth-card" padding="lg">
      <div class="auth-tabs">
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
      <form v-if="activeTab === 'password'" @submit.prevent="handlePasswordLogin" class="auth-form">
        <div class="form-group">
          <label for="username">用户名</label>
          <div class="input-wrapper">
            <span class="input-icon i-ep-user" />
            <input
              type="text"
              id="username"
              v-model="passwordForm.username"
              required
              placeholder="请输入用户名"
              class="form-input"
            />
          </div>
        </div>

        <div class="form-group">
          <label for="password">密码</label>
          <div class="input-wrapper">
            <span class="input-icon i-ep-lock" />
            <input
              :type="showPassword ? 'text' : 'password'"
              id="password"
              v-model="passwordForm.password"
              required
              placeholder="请输入密码"
              class="form-input"
            />
            <button
              type="button"
              class="btn-toggle-password"
              @click="showPassword = !showPassword"
            >
              <span :class="['toggle-password-icon', showPassword ? 'i-ep-view' : 'i-ep-hide']" />
            </button>
          </div>
        </div>

        <div class="form-actions">
          <button type="submit" class="btn btn-primary" :disabled="loading">
            <span v-if="loading" class="loading-spinner" />
            <span>{{ loading ? '登录中...' : '登录' }}</span>
          </button>
        </div>
      </form>

      <!-- 手机验证码登录 -->
      <form v-if="activeTab === 'phone'" @submit.prevent="handlePhoneLogin" class="auth-form">
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

        <div class="form-actions">
          <button type="submit" class="btn btn-primary" :disabled="loading">
            <span v-if="loading" class="loading-spinner" />
            <span>{{ loading ? '登录中...' : '登录' }}</span>
          </button>
        </div>
      </form>

      <!-- 邮箱验证码登录 -->
      <form v-if="activeTab === 'email'" @submit.prevent="handleEmailLogin" class="auth-form">
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

        <div class="form-actions">
          <button type="submit" class="btn btn-primary" :disabled="loading">
            <span v-if="loading" class="loading-spinner" />
            <span>{{ loading ? '登录中...' : '登录' }}</span>
          </button>
        </div>
      </form>

      <div class="auth-footer">
        <p>还没有账号？ <router-link to="/register" class="auth-link">立即注册</router-link></p>
        <p class="forgot-password">
          <router-link to="/reset-password" class="auth-link">忘记密码？</router-link>
        </p>
      </div>
    </GlassCard>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import GlassCard from '@/components/GlassCard.vue'
import SectionHeader from '@/components/SectionHeader.vue'
import { userApi } from '../api/user'
import { getErrorMessage } from '../utils/error'
import config from '../utils/config'
import { useToast } from '../composables/useToast'
import { useUserStore } from '../stores/userStore'
import { useTokenStore } from '../stores/tokenStore'

const router = useRouter()
const route = useRoute()
const { showToast } = useToast()
const userStore = useUserStore()
const tokenStore = useTokenStore()
const loading = ref(false)
const activeTab = ref('password')
const showPassword = ref(false)

// 是否处于“添加账号”模式：登录后不切换当前账号
const isAddAccountMode = computed(() => route.query.addAccount === '1')

// 登录成功后的统一跳转
const onLoginSuccess = (switched: boolean) => {
  showToast(isAddAccountMode.value ? '账号已添加' : '登录成功', 'success')
  if (isAddAccountMode.value && !switched) {
    // 添加账号但不切换，返回上一页或首页
    router.back()
  } else {
    router.push('/')
  }
}

// 验证码登录通用处理：先写到旧 key 拉取用户信息，再归入多账号体系
const handleCodeLogin = async (
  loginFn: () => Promise<{ access: string; refresh: string }>
) => {
  const tokenData = await loginFn()

  // 临时写入旧 key，让 getProfile 能带上 Authorization
  localStorage.setItem(config.jwt.accessTokenKey, tokenData.access)
  localStorage.setItem(config.jwt.refreshTokenKey, tokenData.refresh)

  try {
    const userInfo = await userApi.getProfile()
    tokenStore.addAccount(userInfo.id, tokenData.access, tokenData.refresh, {
      switch: !isAddAccountMode.value
    })
    tokenStore.updateAccountMeta({
      userId: userInfo.id,
      username: userInfo.username,
      avatar: userInfo.avatar || undefined
    })
    onLoginSuccess(!isAddAccountMode.value)
  } finally {
    // 清理旧 key，避免与多账号存储冲突
    localStorage.removeItem(config.jwt.accessTokenKey)
    localStorage.removeItem(config.jwt.refreshTokenKey)
  }
}

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
    const result = await userStore.login(
      passwordForm.value.username,
      passwordForm.value.password,
      { switch: !isAddAccountMode.value }
    )

    if (result) {
      onLoginSuccess(result.switched)
    } else {
      showToast(userStore.error || '登录失败，请检查用户名和密码', 'error')
    }
  } catch (error) {
    showToast(getErrorMessage(error, '登录失败，请检查用户名和密码'), 'error')
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
    await handleCodeLogin(() => userApi.phoneCodeLogin(phoneForm.value))
  } catch (error) {
    showToast(getErrorMessage(error, '登录失败，请检查手机号和验证码'), 'error')
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
    await handleCodeLogin(() => userApi.emailCodeLogin(emailForm.value))
  } catch (error) {
    showToast(getErrorMessage(error, '登录失败，请检查邮箱和验证码'), 'error')
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
  } catch (error) {
    showToast(getErrorMessage(error, '发送验证码失败'), 'error')
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
  } catch (error) {
    showToast(getErrorMessage(error, '发送验证码失败'), 'error')
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

.forgot-password {
  margin-top: var(--space-2);
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
