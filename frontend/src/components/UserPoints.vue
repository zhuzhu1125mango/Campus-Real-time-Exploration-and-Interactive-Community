<template>
  <div class="user-points">
    <div class="points-header">
      <div class="points-info">
        <div class="points-value">{{ points }}</div>
        <div class="points-label">积分</div>
      </div>
      <div class="level-badge">
        <span class="level-icon">🏆</span>
        <span class="level-name">{{ levelName }}</span>
      </div>
    </div>
    
    <div class="level-progress">
      <div class="progress-bar">
        <div 
          class="progress-fill" 
          :style="{ width: levelProgress + '%' }"
        ></div>
      </div>
      <div class="progress-info">
        <span>等级 {{ level }}</span>
        <span>{{ levelProgress }}%</span>
      </div>
    </div>
    
    <div class="points-actions">
      <button class="action-btn primary" @click="$emit('checkin')">
        <span class="btn-icon">📅</span>
        <span>每日签到</span>
      </button>
      <button class="action-btn" @click="$emit('viewHistory')">
        <span class="btn-icon">📊</span>
        <span>积分记录</span>
      </button>
    </div>
    
    <div class="points-rules">
      <h4 class="rules-title">积分规则</h4>
      <ul class="rules-list">
        <li><span class="rule-icon">📝</span> 发帖 +5分</li>
        <li><span class="rule-icon">💬</span> 回复 +2分</li>
        <li><span class="rule-icon">❤️</span> 获赞 +1分</li>
        <li><span class="rule-icon">📅</span> 每日签到 +5分</li>
        <li><span class="rule-icon">🔥</span> 连续3天签到额外+5分</li>
        <li><span class="rule-icon">👑</span> 连续7天签到额外+10分</li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { userApi } from '@/api/user'

const props = withDefaults(defineProps<{
  userId?: number
}>(), {
  userId: 0
})

const emit = defineEmits<{
  (e: 'checkin'): void
  (e: 'viewHistory'): void
}>()

const points = ref(0)
const level = ref(1)
const levelName = ref('新手')
const levelProgress = ref(0)
const loading = ref(true)

const fetchPointsInfo = async () => {
  loading.value = true
  try {
    const id = props.userId || 'me'
    const response = await userApi.getUserPoints(id)
    points.value = response.points
    level.value = response.level
    levelName.value = response.level_name
    levelProgress.value = response.level_progress
  } catch (error) {
    console.error('获取积分信息失败:', error)
    // 使用默认模拟数据
    points.value = 128
    level.value = 3
    levelName.value = '中级学员'
    levelProgress.value = 65
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchPointsInfo()
})

defineExpose({
  refresh: fetchPointsInfo
})
</script>

<style scoped>
.user-points {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  padding: 20px;
  color: white;
}

.points-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.points-info {
  text-align: left;
}

.points-value {
  font-size: 36px;
  font-weight: bold;
  line-height: 1;
}

.points-label {
  font-size: 14px;
  opacity: 0.8;
  margin-top: 4px;
}

.level-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(255, 255, 255, 0.2);
  padding: 8px 16px;
  border-radius: 20px;
}

.level-icon {
  font-size: 20px;
}

.level-name {
  font-weight: 600;
  font-size: 14px;
}

.level-progress {
  margin-bottom: 20px;
}

.progress-bar {
  height: 8px;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: white;
  border-radius: 4px;
  transition: width 0.3s ease;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 12px;
  opacity: 0.9;
}

.points-actions {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.action-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

.action-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

.action-btn.primary {
  background: white;
  color: #667eea;
}

.action-btn.primary:hover {
  background: rgba(255, 255, 255, 0.9);
}

.btn-icon {
  font-size: 16px;
}

.points-rules {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  padding: 15px;
}

.rules-title {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
}

.rules-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.rules-list li {
  font-size: 12px;
  opacity: 0.9;
}

.rule-icon {
  margin-right: 6px;
}

@media (max-width: 480px) {
  .rules-list {
    grid-template-columns: 1fr;
  }
}
</style>