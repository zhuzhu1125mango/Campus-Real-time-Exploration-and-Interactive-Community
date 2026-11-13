<template>
  <div class="school-card" @click="goToDetail">
    <div class="school-header">
      <div class="school-logo">
        <img v-if="school.image" :src="school.image" :alt="school.name" />
        <div v-else class="logo-placeholder">{{ getInitials(school.name) }}</div>
      </div>
      <div class="school-basic-info">
        <h3 class="school-name">{{ school.name }}</h3>
        <div class="school-badges">
          <span v-if="school.school_level?.includes('985')" class="badge badge-985">985</span>
          <span v-if="school.school_level?.includes('211')" class="badge badge-211">211</span>
          <span v-if="school.school_level?.includes('双一流')" class="badge badge-double">双一流</span>
          <span class="school-type">{{ school.school_type || '未知类型' }}</span>
        </div>
      </div>
    </div>

    <div class="school-info">
      <div class="info-item">
        <span class="info-label">地区:</span>
        <span class="info-value">{{ school.province || '未知' }} {{ school.city || '' }}</span>
      </div>
      <div class="info-item">
        <span class="info-label">排名:</span>
        <span class="info-value">{{ school.national_rank || '暂无' }}</span>
      </div>
      <div class="info-item">
        <span class="info-label">创建于:</span>
        <span class="info-value">{{ school.founded_year || '暂无' }}</span>
      </div>
    </div>

    <div class="school-description">
      {{ truncateText(school.introduction || '暂无简介', 100) }}
    </div>

    <div class="school-footer">
      <el-button type="primary" size="small" @click.stop="goToDetail">查看详情</el-button>
      <el-button v-if="showActions" type="info" size="small" plain @click="toggleFavorite">
        <el-icon>
          <component :is="isFavorite ? StarFilled : Star" />
        </el-icon>
        {{ isFavorite ? '已收藏' : '收藏' }}
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { Star, StarFilled } from '@element-plus/icons-vue'
import { useUserStore } from '../stores/userStore'
import type { School } from '../types/school'
import { ElMessage } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()

const props = defineProps({
  school: {
    type: Object as () => School,
    required: true
  },
  showDetails: {
    type: Boolean,
    default: true
  },
  showActions: {
    type: Boolean,
    default: true
  }
})

// 是否已收藏
const isFavorite = computed(() => {
  if (!userStore.user || !userStore.user.favorite_schools) {
    return false
  }
  return userStore.user.favorite_schools.includes(props.school.id)
})

// 获取学校名称首字母
const getInitials = (name: string) => {
  if (!name) return '?'
  return name.substring(0, 2)
}

// 截断文本
const truncateText = (text: string, maxLength: number) => {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

// 跳转到详情页
const goToDetail = () => {
  router.push(`/schools/${props.school.id}`)
}

// 切换收藏状态
const toggleFavorite = async (event: Event) => {
  event.stopPropagation()

  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录后再收藏院校')
    router.push('/login')
    return
  }

  try {
    if (isFavorite.value) {
      const result = await userStore.unfavoriteSchool(props.school.id)
      if (result) {
        ElMessage.success('已取消收藏')
      }
    } else {
      const result = await userStore.favoriteSchool(props.school.id)
      if (result) {
        ElMessage.success('收藏成功')
      }
    }
  } catch (error) {
    console.error('操作收藏失败:', error)
    ElMessage.error('操作失败，请稍后重试')
  }
}
</script>

<style scoped>
.school-card {
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-card);
  backdrop-filter: blur(12px) saturate(180%);
  -webkit-backdrop-filter: blur(12px) saturate(180%);
  overflow: hidden;
  transition: all 0.3s ease;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.school-card:hover {
  transform: translateY(-6px);
  box-shadow: var(--shadow-lg);
}

.school-header {
  padding: var(--space-5);
  display: flex;
  align-items: center;
  border-bottom: 1px solid var(--border-color-light);
}

.school-logo {
  width: 64px;
  height: 64px;
  min-width: 64px;
  border-radius: var(--radius-md);
  overflow: hidden;
  margin-right: var(--space-4);
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-tertiary);
}

.school-logo img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.logo-placeholder {
  width: 100%;
  height: 100%;
  background: var(--primary-600);
  color: var(--text-inverse);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
  font-weight: 700;
}

.school-basic-info {
  flex: 1;
}

.school-name {
  font-size: 1.1rem;
  font-weight: 700;
  margin: 0 0 var(--space-2) 0;
  color: var(--text-primary);
}

.school-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.badge {
  padding: 3px 7px;
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-weight: 700;
}

.badge-985 {
  background-color: var(--primary-100);
  color: var(--primary-700);
}

.badge-211 {
  background-color: var(--accent-green-light);
  color: var(--accent-green);
}

.badge-double {
  background-color: var(--warning-bg);
  color: var(--warning-color);
}

.school-type {
  padding: 3px 7px;
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
}

.school-info {
  padding: var(--space-4) var(--space-5);
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--space-2);
  border-bottom: 1px solid var(--border-color-light);
}

.info-item {
  font-size: 0.875rem;
}

.info-label {
  color: var(--text-tertiary);
  margin-right: var(--space-1);
}

.info-value {
  color: var(--text-primary);
  font-weight: 500;
}

.school-description {
  padding: var(--space-4) var(--space-5);
  color: var(--text-secondary);
  line-height: 1.6;
  font-size: 0.9rem;
  flex: 1;
}

.school-footer {
  padding: var(--space-4) var(--space-5);
  border-top: 1px solid var(--border-color-light);
  display: flex;
  justify-content: space-between;
}
</style>
