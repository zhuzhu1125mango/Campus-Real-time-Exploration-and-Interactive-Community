<template>
  <div class="favorite-schools-container">
    <h1 class="page-title">我的收藏院校</h1>
    
    <div v-if="loading" class="loading-indicator">
      <el-skeleton :rows="6" animated />
      <span>加载中...</span>
    </div>

    <div v-else-if="error" class="error-state">
      <el-alert
        :title="error"
        type="error"
        show-icon
        @close="error = null"
      />
    </div>

    <div v-else-if="schools.length === 0" class="empty-state">
      <el-empty
        description="暂无收藏院校"
        :image-size="200"
      >
        <template #extra>
          <router-link to="/schools">
            <el-button type="primary">去浏览院校</el-button>
          </router-link>
        </template>
      </el-empty>
    </div>

    <div v-else class="schools-grid">
      <SchoolCard 
        v-for="school in schools" 
        :key="school.id" 
        :school="school"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { schoolApi } from '../api/school'
import { useUserStore } from '../stores/userStore'
import type { School } from '../types/school'
import SchoolCard from '../components/SchoolCard.vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { userApi } from '../api/user'

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
    
    console.log('收藏记录:', favoritesResponse)
    
    if (favoritesResponse.length === 0) {
      schools.value = []
      loading.value = false
      return
    }
    
    // 获取学校详情
    const schoolsData: School[] = []
    for (const favorite of favoritesResponse) {
      // 检查是否为学校类型的收藏
      if (favorite.content_type && favorite.content_type.includes('school') && favorite.object_id) {
        try {
          const response = await schoolApi.getSchool(favorite.object_id)
          schoolsData.push(response as unknown as School)
        } catch (err) {
          console.error(`获取学校 ID ${favorite.object_id} 详情失败:`, err)
          // 继续获取其他学校
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
.favorite-schools-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem 1rem;
}

.page-title {
  font-size: 1.8rem;
  margin-bottom: 2rem;
  color: #333;
  position: relative;
}

.page-title::after {
  content: '';
  position: absolute;
  width: 60px;
  height: 4px;
  background-color: #4361ee;
  bottom: -10px;
  left: 0;
  border-radius: 2px;
}

.loading-indicator, .error-state, .empty-state {
  padding: 3rem 0;
  text-align: center;
}

.schools-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 2rem;
  margin-top: 2rem;
}

@media (max-width: 768px) {
  .schools-grid {
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 1.5rem;
  }
}
</style> 