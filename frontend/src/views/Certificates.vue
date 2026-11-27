<template>
  <div class="certificates-page container-wide page-padding">
    <SectionHeader
      title="我的证书"
      subtitle="完成课程后自动发放，可用于学习成果展示"
      icon="i-ep-medal"
    />

    <GlassCard :hover="false" class="verify-card">
      <div class="verify-row">
        <input
          v-model="verifyNumber"
          type="text"
          class="verify-input"
          placeholder="输入证书编号校验真伪，如 CERT-20261126-XXXXXXXX"
          @keyup.enter="verify"
        />
        <button class="btn btn-primary" :disabled="verifying" @click="verify">
          {{ verifying ? '校验中...' : '校验' }}
        </button>
      </div>
      <p v-if="verifyResult" class="verify-result" :class="{ invalid: !verifyResult.valid }">
        {{ verifyResult.message }}
      </p>
    </GlassCard>

    <div v-if="loading" class="loading-state">
      <div class="loading-spinner" />
      <p>加载中...</p>
    </div>

    <GlassCard v-else-if="certificates.length === 0" :hover="false">
      <div class="empty-state">
        <span class="i-ep-medal empty-icon" />
        <p>还没有证书，完成课程学习后即可获得</p>
        <button class="btn btn-primary" @click="goLearning">去学习</button>
      </div>
    </GlassCard>

    <div v-else class="certificate-list">
      <GlassCard
        v-for="certificate in certificates"
        :key="certificate.id"
        :hover="false"
        class="certificate-card"
      >
        <div class="certificate-main">
          <div class="certificate-badge">
            <span class="i-ep-medal" />
          </div>
          <div class="certificate-info">
            <h3 class="course-title">{{ certificate.course_title }}</h3>
            <p class="certificate-meta">讲师：{{ certificate.instructor_name }}</p>
            <p class="certificate-meta">编号：{{ certificate.number }}</p>
            <p class="certificate-meta">颁发时间：{{ formatDate(certificate.issued_at) }}</p>
          </div>
          <div class="certificate-side">
            <span class="status-tag" :class="certificate.status">
              {{ certificate.status === 'valid' ? '有效' : '已撤销' }}
            </span>
            <button class="btn btn-secondary" @click="goDetail(certificate.id)">查看证书</button>
          </div>
        </div>
      </GlassCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { learningApi } from '../api/learning'
import { getApiErrorMessage } from '../utils/error'
import { formatDate } from '../utils/date'
import type { Certificate } from '../types/learning'
import GlassCard from '@/components/GlassCard.vue'
import SectionHeader from '@/components/SectionHeader.vue'

const router = useRouter()

const certificates = ref<Certificate[]>([])
const loading = ref(false)
const verifyNumber = ref('')
const verifying = ref(false)
const verifyResult = ref<{ valid: boolean; message: string } | null>(null)

const loadCertificates = async () => {
  loading.value = true
  try {
    const response = await learningApi.getCertificates()
    certificates.value = response.results || []
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '加载证书失败'))
  } finally {
    loading.value = false
  }
}

const verify = async () => {
  const number = verifyNumber.value.trim()
  if (!number) {
    ElMessage.warning('请输入证书编号')
    return
  }
  verifying.value = true
  verifyResult.value = null
  try {
    const certificate = await learningApi.verifyCertificate(number)
    verifyResult.value = {
      valid: certificate.status === 'valid',
      message: certificate.status === 'valid'
        ? `校验通过：${certificate.username} 已完成《${certificate.course_title}》`
        : '该证书已被撤销'
    }
  } catch {
    verifyResult.value = { valid: false, message: '未找到该证书，请检查编号是否正确' }
  } finally {
    verifying.value = false
  }
}

const goDetail = (id: number) => {
  router.push(`/certificate/${id}`)
}

const goLearning = () => {
  router.push('/learning')
}

onMounted(() => {
  loadCertificates()
})
</script>

<style scoped>
.certificates-page {
  min-height: calc(100vh - 200px);
}

.verify-card {
  margin-bottom: var(--space-5);
}

.verify-row {
  display: flex;
  gap: var(--space-3);
}

.verify-input {
  flex: 1;
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  font-size: 0.95rem;
  background: var(--bg-primary);
  color: var(--text-primary);
}

.verify-input:focus {
  outline: none;
  border-color: var(--primary-400);
  box-shadow: 0 0 0 3px var(--primary-100);
}

.verify-result {
  margin: var(--space-3) 0 0;
  font-size: 0.9rem;
  color: var(--success-color);
}

.verify-result.invalid {
  color: var(--error-color);
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-10) 0;
  color: var(--text-secondary);
  gap: var(--space-3);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--primary-200);
  border-top-color: var(--primary-600);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-icon {
  font-size: 2.5rem;
  color: var(--text-tertiary);
}

.certificate-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.certificate-main {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.certificate-badge {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--primary-50);
  color: var(--primary-600);
  font-size: 1.6rem;
  flex-shrink: 0;
}

.certificate-info {
  flex: 1;
  min-width: 0;
}

.course-title {
  margin: 0 0 var(--space-1);
  font-size: 1.05rem;
  font-weight: 600;
  color: var(--text-primary);
}

.certificate-meta {
  margin: 0;
  font-size: 0.85rem;
  color: var(--text-secondary);
  line-height: 1.6;
}

.certificate-side {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: var(--space-2);
  flex-shrink: 0;
}

.status-tag {
  padding: 2px var(--space-3);
  border-radius: var(--radius-full);
  font-size: 0.75rem;
  font-weight: 600;
  background: var(--success-bg);
  color: var(--success-color);
}

.status-tag.revoked {
  background: var(--error-bg);
  color: var(--error-color);
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: 0.625rem 1.25rem;
  border-radius: var(--radius-md);
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: all 0.2s ease;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background-color: var(--primary-600);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: var(--primary-700);
}

.btn-secondary {
  background-color: var(--bg-tertiary);
  color: var(--text-primary);
}

.btn-secondary:hover {
  background-color: var(--border-color);
}

@media (max-width: 768px) {
  .verify-row {
    flex-direction: column;
  }

  .certificate-main {
    flex-direction: column;
    align-items: flex-start;
  }

  .certificate-side {
    align-items: flex-start;
  }
}
</style>
