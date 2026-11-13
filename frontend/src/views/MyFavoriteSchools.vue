<template>
  <div class="my-favorite-schools-page container-wide page-padding">
    <SectionHeader
      title="我的关注院校"
      icon="i-ep-star"
    />

    <GlassCard :hover="false" class="favorite-schools-card">
      <div v-if="loading" class="loading-state">
        <div class="loading-spinner" />
        <p>加载中...</p>
      </div>

      <div v-else-if="error" class="error-state">
        <div class="error-icon">
          <span class="i-ep-warning" />
        </div>
        <p class="error-message">{{ error }}</p>
        <div class="error-actions">
          <button class="btn btn-primary" @click="fetchFavoriteSchools">
            <span class="i-ep-refresh" />
            重新加载
          </button>
        </div>
      </div>

      <div v-else-if="schools.length === 0" class="empty-state">
        <div class="empty-icon">
          <span class="i-ep-star" />
        </div>
        <p>暂无关注院校</p>
        <router-link to="/schools">
          <button class="btn btn-primary">
            <span class="i-ep-school" />
            去浏览院校
          </button>
        </router-link>
      </div>

      <div v-else class="schools-grid">
        <SchoolCard
          v-for="school in schools"
          :key="school.id"
          :school="school"
        />
      </div>
    </GlassCard>
  </div>
</template>

<script setup lang="ts">
import { logger } from '@/utils/logger'
import { ref, onMounted } from 'vue'
import { schoolApi } from '../api/school'
import { useUserStore } from '../stores/userStore'
import type { School } from '../types/school'
import SchoolCard from '../components/SchoolCard.vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { userApi } from '../api/user'
import GlassCard from '@/components/GlassCard.vue'
import SectionHeader from '@/components/SectionHeader.vue'

// 数据
const schools = ref<School[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const userStore = useUserStore()
const router = useRouter()

// 获取收藏的学校
const fetchFavoriteSchools = async () => {
  if (!userStore.isLoggedIn) {
    router.push('/login')
    return
  }

  loading.value = true
  error.value = null

  try {
    // 获取用户收藏列表
    const favoritesResponse = await userApi.getFavoriteSchools()

    if (!favoritesResponse || !Array.isArray(favoritesResponse)) {
      console.error('获取收藏学校失败: 格式错误', favoritesResponse)
      schools.value = []
      loading.value = false
      return
    }

    logger.log('收藏记录:', favoritesResponse)

    if (favoritesResponse.length === 0) {
      schools.value = []
      loading.value = false
      return
    }

    // 提取学校详情（后端已直接返回被收藏对象信息）
    const schoolsData: School[] = []
    for (const favorite of favoritesResponse) {
      // 检查是否为学校类型的收藏
      if (favorite.content_type === 'schools.school' && favorite.content_object) {
        const school = favorite.content_object as School
        schoolsData.push(school)
      } else if (favorite.content_type && favorite.content_type.includes('school') && favorite.object_id) {
        // 兼容旧数据：对象信息不存在时回退到单独请求
        try {
          const response = await schoolApi.getSchool(favorite.object_id)
          schoolsData.push(response as unknown as School)
        } catch (err) {
          console.error(`获取学校 ID ${favorite.object_id} 详情失败:`, err)
        }
      }
    }

    schools.value = schoolsData
  } catch (err) {
    error.value = err instanceof Error ? err.message : '获取收藏院校失败'
    ElMessage.error(error.value)
    schools.value = []
  } finally {
    loading.value = false
  }
}

// 生命周期钩子
onMounted(() => {
  fetchFavoriteSchools()
})
</script>

<style scoped>
.my-favorite-schools-page {
  min-height: calc(100vh - 200px);
}

.favorite-schools-card {
  min-height: 400px;
}

.loading-state,
.empty-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-10) 0;
  color: var(--text-secondary);
  text-align: center;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--primary-200);
  border-top-color: var(--primary-600);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: var(--space-3);
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-icon,
.error-icon {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: var(--space-4);
  font-size: 2rem;
}

.empty-icon {
  background: var(--primary-50);
  color: var(--primary-500);
}

.error-icon {
  background: var(--error-bg);
  color: var(--error-color);
}

.error-message {
  margin-bottom: var(--space-4);
  color: var(--text-primary);
  font-weight: 500;
}

.error-actions {
  display: flex;
  gap: var(--space-3);
}

.schools-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--space-6);
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-md);
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: all 0.2s;
  text-decoration: none;
}

.btn-primary {
  background-color: var(--primary-600);
  color: white;
}

.btn-primary:hover {
  background-color: var(--primary-700);
}

.btn-secondary {
  background-color: var(--bg-tertiary);
  color: var(--text-primary);
}

.btn-secondary:hover {
  background-color: var(--border-color);
}

.btn-danger {
  background-color: var(--error-bg);
  color: var(--error-color);
}

.btn-danger:hover {
  background-color: var(--error-color);
  color: white;
}

@media (max-width: 640px) {
  .schools-grid {
    grid-template-columns: 1fr;
  }
}
</style>
