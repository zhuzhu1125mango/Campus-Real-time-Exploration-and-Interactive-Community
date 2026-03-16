<template>
  <div class="school-card" @click="goToDetail">
    <div class="school-header">
      <div class="school-logo">
        <img v-if="school.logo" :src="school.logo" :alt="school.name" />
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
        <i :class="isFavorite ? 'el-icon-star-on' : 'el-icon-star-off'"></i>
        {{ isFavorite ? '已收藏' : '收藏' }}
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
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
  event.stopPropagation() // 阻止事件冒泡，避免触发goToDetail
  
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录后再收藏院校')
    router.push('/login')
    return
  }
  
  try {
    if (isFavorite.value) {
      // 取消收藏
      const result = await userStore.unfavoriteSchool(props.school.id)
      if (result) {
        ElMessage.success('已取消收藏')
      }
    } else {
      // 添加收藏
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
  background-color: white;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
  overflow: hidden;
  transition: all 0.3s ease;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.school-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
}

.school-header {
  padding: 20px;
  display: flex;
  align-items: center;
  border-bottom: 1px solid #f0f0f0;
}

.school-logo {
  width: 60px;
  height: 60px;
  min-width: 60px;
  border-radius: 8px;
  overflow: hidden;
  margin-right: 15px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f0f3ff;
}

.school-logo img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.logo-placeholder {
  width: 100%;
  height: 100%;
  background-color: #4361ee;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: bold;
}

.school-basic-info {
  flex: 1;
}

.school-name {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 8px 0;
  color: #333;
}

.school-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.badge {
  padding: 3px 6px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.badge-985 {
  background-color: #e6f7ff;
  color: #1890ff;
}

.badge-211 {
  background-color: #f6ffed;
  color: #52c41a;
}

.badge-double {
  background-color: #fff7e6;
  color: #fa8c16;
}

.school-type {
  padding: 3px 6px;
  background-color: #f5f5f5;
  color: #666;
  border-radius: 4px;
  font-size: 12px;
}

.school-info {
  padding: 15px 20px;
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 10px;
  border-bottom: 1px solid #f0f0f0;
}

.info-item {
  font-size: 14px;
}

.info-label {
  color: #999;
  margin-right: 5px;
}

.info-value {
  color: #333;
  font-weight: 500;
}

.school-description {
  padding: 15px 20px;
  color: #666;
  line-height: 1.5;
  font-size: 14px;
  flex: 1;
}

.school-footer {
  padding: 15px 20px;
  border-top: 1px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
}
</style> 