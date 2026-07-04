<template>
  <div class="points-leaderboard">
    <h3 class="leaderboard-title">🏆 积分排行榜</h3>
    
    <div v-if="loading" class="loading">
      <el-skeleton :rows="5" animated />
    </div>
    
    <div v-else class="leaderboard-list">
      <div 
        v-for="(item, index) in leaderboard" 
        :key="item.user_id"
        class="leaderboard-item"
        :class="{ 
          'rank-1': index === 0,
          'rank-2': index === 1,
          'rank-3': index === 2
        }"
        @click="$emit('selectUser', item.user_id)"
      >
        <div class="rank-badge">{{ index + 1 }}</div>
        <div class="user-avatar">
          <img 
            :src="item.avatar || 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=user%20avatar%20placeholder&image_size=square'" 
            :alt="item.username"
          />
        </div>
        <div class="user-info">
          <div class="user-name">{{ item.username }}</div>
          <div class="user-level">{{ item.level_name }}</div>
        </div>
        <div class="user-points">
          <span class="points-value">{{ item.points }}</span>
          <span class="points-label">积分</span>
        </div>
      </div>
      
      <div v-if="leaderboard.length === 0" class="no-data">
        暂无排行数据
      </div>
    </div>
    
    <button v-if="leaderboard.length > 0" class="view-all-btn" @click="$emit('viewAll')">
      查看完整榜单
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { userApi } from '@/api/user'

interface LeaderboardItem {
  rank: number
  user_id: number
  username: string
  avatar: string | null
  points: number
  level: number
  level_name: string
}

defineEmits<{
  (e: 'selectUser', userId: number): void
  (e: 'viewAll'): void
}>()

const leaderboard = ref<LeaderboardItem[]>([])
const loading = ref(true)

const fetchLeaderboard = async () => {
  loading.value = true
  try {
    const response = await userApi.getPointsLeaderboard()
    leaderboard.value = response
  } catch (error) {
    console.error('获取积分排行榜失败:', error)
    // 使用模拟数据
    leaderboard.value = [
      { rank: 1, user_id: 1, username: '学霸小王', avatar: null, points: 2580, level: 6, level_name: '学神' },
      { rank: 2, user_id: 2, username: '研究生小李', avatar: null, points: 1890, level: 5, level_name: '学霸' },
      { rank: 3, user_id: 3, username: '考研达人', avatar: null, points: 1560, level: 5, level_name: '学霸' },
      { rank: 4, user_id: 4, username: '校园之星', avatar: null, points: 1240, level: 4, level_name: '高级学员' },
      { rank: 5, user_id: 5, username: '努力学习中', avatar: null, points: 980, level: 4, level_name: '高级学员' },
    ]
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchLeaderboard()
})

defineExpose({
  refresh: fetchLeaderboard
})
</script>

<style scoped>
.points-leaderboard {
  background: white;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.leaderboard-title {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.loading {
  padding: 10px;
}

.leaderboard-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.leaderboard-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.leaderboard-item:hover {
  background: #f8f9fa;
}

.leaderboard-item.rank-1 {
  background: linear-gradient(135deg, #fff9e6 0%, #fff3cd 100%);
  border: 1px solid #ffeeba;
}

.leaderboard-item.rank-2 {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border: 1px solid #dee2e6;
}

.leaderboard-item.rank-3 {
  background: linear-gradient(135deg, #fff5f5 0%, #ffe4e4 100%);
  border: 1px solid #fecaca;
}

.rank-badge {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #f3f4f6;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: bold;
  color: #666;
  flex-shrink: 0;
}

.rank-1 .rank-badge {
  background: linear-gradient(135deg, #ffd700 0%, #ffb700 100%);
  color: #8b6914;
}

.rank-2 .rank-badge {
  background: linear-gradient(135deg, #c0c0c0 0%, #a8a8a8 100%);
  color: #555;
}

.rank-3 .rank-badge {
  background: linear-gradient(135deg, #cd7f32 0%, #b87333 100%);
  color: #fff;
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
}

.user-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.user-info {
  flex: 1;
  min-width: 0;
}

.user-name {
  font-weight: 600;
  font-size: 14px;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-level {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}

.user-points {
  text-align: right;
  flex-shrink: 0;
}

.points-value {
  display: block;
  font-size: 16px;
  font-weight: bold;
  color: #4361ee;
}

.points-label {
  font-size: 11px;
  color: #999;
}

.no-data {
  text-align: center;
  padding: 20px;
  color: #999;
}

.view-all-btn {
  width: 100%;
  margin-top: 12px;
  padding: 10px;
  background: #f3f4f6;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  color: #4361ee;
  cursor: pointer;
  transition: background 0.2s;
}

.view-all-btn:hover {
  background: #e5e7eb;
}
</style>