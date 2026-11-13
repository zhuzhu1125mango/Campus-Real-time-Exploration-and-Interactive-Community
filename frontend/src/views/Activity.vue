<script setup lang="ts">
import { ref } from 'vue'
import ActivityFeed from '../components/ActivityFeed.vue'
import GlassCard from '../components/GlassCard.vue'
import SectionHeader from '../components/SectionHeader.vue'

const activeTab = ref<'feed' | 'my' | 'all'>('feed')

const tabs: { key: 'feed' | 'my' | 'all'; label: string; icon: string }[] = [
  { key: 'feed', label: '关注动态', icon: 'i-ep-user-filled' },
  { key: 'my', label: '我的动态', icon: 'i-ep-user' },
  { key: 'all', label: '全部动态', icon: 'i-ep-view' }
]

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

<template>
  <div class="activity-page container-wide page-padding">
    <SectionHeader
      title="个人动态"
      subtitle="查看你和关注用户的最新动态"
      icon="i-ep-magic-stick"
    />

    <GlassCard :hover="false" class="activity-card">
      <div class="activity-tabs">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          class="tab-btn"
          :class="{ active: activeTab === tab.key }"
          @click="activeTab = tab.key"
        >
          <span :class="tab.icon" />
          {{ tab.label }}
        </button>
      </div>

      <div class="activity-feed-container">
        <ActivityFeed
          :title="getTabTitle()"
          :feed-type="activeTab"
        />
      </div>
    </GlassCard>
  </div>
</template>

<style scoped>
.activity-page {
  min-height: calc(100vh - 200px);
}

.activity-card {
  overflow: visible;
}

.activity-tabs {
  display: flex;
  gap: var(--space-2);
  margin-bottom: var(--space-5);
  padding: var(--space-1);
  background: var(--bg-tertiary);
  border-radius: var(--radius-lg);
  width: fit-content;
}

.tab-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  font-size: 0.95rem;
  font-weight: 500;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
}

.tab-btn:hover {
  color: var(--text-primary);
  background: var(--bg-primary);
}

.tab-btn.active {
  background: var(--bg-primary);
  color: var(--primary-600);
  box-shadow: var(--shadow-sm);
}

.dark .tab-btn.active {
  background: var(--bg-primary);
  color: var(--primary-400);
}

.activity-feed-container {
  border-radius: var(--radius-lg);
  overflow: hidden;
}

@media (max-width: 640px) {
  .activity-tabs {
    width: 100%;
  }

  .tab-btn {
    flex: 1;
    justify-content: center;
    padding: var(--space-2) var(--space-3);
    font-size: 0.875rem;
  }
}
</style>
