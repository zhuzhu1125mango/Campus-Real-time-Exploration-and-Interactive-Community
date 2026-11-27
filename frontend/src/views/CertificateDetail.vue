<template>
  <div class="certificate-detail-page container-medium page-padding">
    <div class="page-toolbar no-print">
      <button class="btn btn-secondary" @click="goBack">返回</button>
      <button class="btn btn-primary" :disabled="!certificate" @click="printCertificate">
        打印证书
      </button>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="loading-spinner" />
      <p>加载证书中...</p>
    </div>

    <div v-else-if="error" class="error-state">
      <span class="i-ep-warning error-icon" />
      <p>{{ error }}</p>
      <button class="btn btn-secondary" @click="loadCertificate">重新加载</button>
    </div>

    <div v-else-if="certificate" class="certificate-paper" :class="{ revoked: certificate.status !== 'valid' }">
      <div class="certificate-border">
        <div class="certificate-brand">
          <span class="i-ep-medal brand-icon" />
          <span class="brand-name">校园实时互动社区</span>
        </div>

        <h1 class="certificate-title">结业证书</h1>
        <p class="certificate-subtitle">CERTIFICATE OF COMPLETION</p>

        <p class="certificate-user">{{ certificate.username }}</p>
        <p class="certificate-text">同学已完成课程</p>
        <p class="certificate-course">《{{ certificate.course_title }}》</p>
        <p class="certificate-text">的全部课时学习，经考核准予结业，特发此证。</p>

        <div class="certificate-footer">
          <div class="footer-item">
            <span class="footer-label">讲师</span>
            <span class="footer-value">{{ certificate.instructor_name }}</span>
          </div>
          <div class="footer-item">
            <span class="footer-label">颁发时间</span>
            <span class="footer-value">{{ formatDate(certificate.issued_at) }}</span>
          </div>
          <div class="footer-item">
            <span class="footer-label">证书编号</span>
            <span class="footer-value">{{ certificate.number }}</span>
          </div>
        </div>

        <div v-if="certificate.status !== 'valid'" class="revoked-mark">已撤销</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { learningApi } from '../api/learning'
import { getApiErrorMessage } from '../utils/error'
import { formatDate } from '../utils/date'
import type { Certificate } from '../types/learning'

const route = useRoute()
const router = useRouter()

const certificate = ref<Certificate | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

const certificateId = Number(route.params.id)

const loadCertificate = async () => {
  if (Number.isNaN(certificateId) || certificateId <= 0) {
    error.value = '无效的证书ID'
    return
  }
  loading.value = true
  error.value = null
  try {
    certificate.value = await learningApi.getCertificate(certificateId)
  } catch (err) {
    error.value = getApiErrorMessage(err, '加载证书失败')
  } finally {
    loading.value = false
  }
}

const printCertificate = () => {
  window.print()
}

const goBack = () => {
  router.back()
}

onMounted(() => {
  loadCertificate()
})
</script>

<style scoped>
.certificate-detail-page {
  min-height: calc(100vh - 200px);
}

.page-toolbar {
  display: flex;
  justify-content: space-between;
  margin-bottom: var(--space-5);
}

.loading-state,
.error-state {
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

.error-icon {
  font-size: 2.5rem;
  color: var(--warning-color);
}

.certificate-paper {
  background: #fffdf7;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  padding: var(--space-6);
}

.certificate-border {
  position: relative;
  border: 3px double #c9a227;
  border-radius: var(--radius-md);
  padding: var(--space-10) var(--space-8);
  text-align: center;
  color: #3a3226;
}

.certificate-brand {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  color: #a8842a;
  font-weight: 600;
  letter-spacing: 0.08em;
}

.brand-icon {
  font-size: 1.5rem;
}

.certificate-title {
  margin: var(--space-6) 0 var(--space-1);
  font-size: 2.2rem;
  font-weight: 700;
  letter-spacing: 0.3em;
  color: #7a5f14;
}

.certificate-subtitle {
  margin: 0 0 var(--space-8);
  font-size: 0.75rem;
  letter-spacing: 0.35em;
  color: #b09a5a;
}

.certificate-user {
  margin: 0 0 var(--space-2);
  font-size: 1.8rem;
  font-weight: 600;
  color: #3a3226;
  border-bottom: 1px solid #d9c78e;
  display: inline-block;
  padding: 0 var(--space-6) var(--space-1);
}

.certificate-text {
  margin: var(--space-3) 0;
  font-size: 1rem;
  color: #5b5140;
}

.certificate-course {
  margin: var(--space-2) 0;
  font-size: 1.4rem;
  font-weight: 600;
  color: #7a5f14;
}

.certificate-footer {
  display: flex;
  justify-content: space-around;
  flex-wrap: wrap;
  gap: var(--space-4);
  margin-top: var(--space-10);
  padding-top: var(--space-5);
  border-top: 1px dashed #d9c78e;
}

.footer-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  font-size: 0.85rem;
}

.footer-label {
  color: #a08c56;
}

.footer-value {
  color: #3a3226;
  font-weight: 600;
}

.revoked-mark {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%) rotate(-18deg);
  font-size: 4rem;
  font-weight: 800;
  color: rgba(220, 38, 38, 0.18);
  border: 6px solid rgba(220, 38, 38, 0.18);
  border-radius: var(--radius-lg);
  padding: var(--space-2) var(--space-8);
  pointer-events: none;
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

@media print {
  :global(nav),
  :global(footer),
  .no-print {
    display: none !important;
  }

  .certificate-detail-page {
    padding: 0;
    min-height: auto;
  }

  .certificate-paper {
    box-shadow: none;
    padding: 0;
    background: #fff;
  }
}
</style>
