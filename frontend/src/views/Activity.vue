<template>
  <div class="activity-page">
    <div class="activity-header">
      <h1>个人动态</h1>
      <p>查看你和关注用户的最新动态</p>
    </div>
    
    <div class="activity-content">
      <div class="activity-tabs">
        <button 
          class="tab-btn" 
          :class="{ 'active': activeTab === 'feed' }"
          @click="activeTab = 'feed'"
        >
          关注动态
        </button>
        <button 
          class="tab-btn" 
          :class="{ 'active': activeTab === 'my' }"
          @click="activeTab = 'my'"
        >
          我的动态
        </button>
        <button 
          class="tab-btn" 
          :class="{ 'active': activeTab === 'all' }"
          @click="activeTab = 'all'"
        >
          全部动态
        </button>
      </div>
      
      <div class="activity-feed-container">
        <ActivityFeed 
          :title="getTabTitle()" 
          :feed-type="activeTab"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import ActivityFeed from '../components/ActivityFeed.vue'

const activeTab = ref<'feed' | 'my' | 'all'>('feed')

const getTabTitle = () => {
  switch (activeTab.value) {
    case 'feed':
      return '关注动态'
    case 'my':
      return '我的动态'
    case 'all':
      return '全部动态'
    default:
      return '动态'
  }
}
</script>

<style scoped>
.activity-page {
  min-height: 100vh;
  background: #f5f7fa;
}

.activity-header {
  background: linear-gradient(135deg, #9b59b6, #8e44ad);
  color: #fff;
  padding: 60px 20px;
  text-align: center;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.activity-header h1 {
  font-size: 36px;
  font-weight: bold;
  margin-bottom: 10px;
}

.activity-header p {
  font-size: 18px;
  opacity: 0.9;
}

.activity-content {
  padding: 40px 20px;
  max-width: 800px;
  margin: 0 auto;
}

.activity-tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  background: #fff;
  border-radius: 8px;
  padding: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.tab-btn {
  flex: 1;
  padding: 12px;
  background: none;
  border: none;
  border-radius: 6px;
  font-size: 16px;
  font-weight: 500;
  color: #666;
  cursor: pointer;
  transition: all 0.3s ease;
}

.tab-btn:hover {
  background: #f5f7fa;
  color: #333;
}

.tab-btn.active {
  background: #9b59b6;
  color: #fff;
}

.activity-feed-container {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

@media (max-width: 768px) {
  .activity-header {
    padding: 40px 20px;
  }
  
  .activity-header h1 {
    font-size: 28px;
  }
  
  .activity-content {
    padding: 20px 10px;
  }
  
  .activity-tabs {
    flex-direction: column;
  }
  
  .tab-btn {
    padding: 10px;
    font-size: 14px;
  }
}
</style>