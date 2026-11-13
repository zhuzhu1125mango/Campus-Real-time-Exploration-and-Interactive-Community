<template>
  <div class="friends-page container-wide page-padding">
    <SectionHeader
      title="好友管理"
      subtitle="管理好友列表、处理好友请求、添加新朋友"
      icon="i-ep-user-filled"
    />

    <GlassCard :hover="false" class="friends-card">
      <div class="friends-layout">
        <div class="friends-sidebar">
          <ul class="sidebar-menu">
            <li :class="{ active: activeTab === 'list' }" @click="activeTab = 'list'">
              <span class="menu-icon i-ep-user-filled" />
              <span class="menu-text">好友列表</span>
            </li>
            <li :class="{ active: activeTab === 'requests' }" @click="activeTab = 'requests'">
              <span class="menu-icon i-ep-bell" />
              <span class="menu-text">好友请求</span>
              <span v-if="unreadRequests > 0" class="badge">{{ unreadRequests }}</span>
            </li>
            <li :class="{ active: activeTab === 'add' }" @click="activeTab = 'add'">
              <span class="menu-icon i-ep-plus" />
              <span class="menu-text">添加好友</span>
            </li>
          </ul>
        </div>

        <div class="friends-content">
          <div v-if="activeTab === 'list'">
            <FriendsList />
          </div>
          <div v-else-if="activeTab === 'requests'">
            <FriendRequests @update:unread-count="updateUnreadRequests" />
          </div>
          <div v-else-if="activeTab === 'add'">
            <AddFriend />
          </div>
        </div>
      </div>
    </GlassCard>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import FriendsList from '../components/FriendsList.vue'
import FriendRequests from '../components/FriendRequests.vue'
import AddFriend from '../components/AddFriend.vue'
import GlassCard from '../components/GlassCard.vue'
import SectionHeader from '../components/SectionHeader.vue'

// 状态数据
const activeTab = ref('list')
const unreadRequests = ref(0)

// 更新未读请求数
const updateUnreadRequests = (count: number) => {
  unreadRequests.value = count
}
</script>

<style scoped>
.friends-page {
  min-height: calc(100vh - 200px);
}

.friends-card {
  overflow: hidden;
}

.friends-layout {
  display: flex;
  min-height: 600px;
}

.friends-sidebar {
  width: 250px;
  flex-shrink: 0;
  border-right: 1px solid var(--border-color-light);
  padding: var(--space-2);
}

.sidebar-menu {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.sidebar-menu li {
  display: flex;
  align-items: center;
  padding: var(--space-3) var(--space-4);
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  border-radius: var(--radius-lg);
  color: var(--text-secondary);
}

.sidebar-menu li:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.sidebar-menu li.active {
  background: var(--primary-50);
  color: var(--primary-600);
}

.dark .sidebar-menu li.active {
  background: var(--bg-tertiary);
  color: var(--primary-400);
}

.menu-icon {
  width: 20px;
  height: 20px;
  margin-right: var(--space-3);
  flex-shrink: 0;
}

.menu-text {
  flex: 1;
  font-size: 0.95rem;
  font-weight: 500;
}

.badge {
  background-color: var(--danger-500);
  color: white;
  border-radius: var(--radius-full);
  padding: 2px 8px;
  font-size: 0.75rem;
  font-weight: 600;
  min-width: 20px;
  text-align: center;
}

.friends-content {
  flex: 1;
  padding: var(--space-2) var(--space-4);
  min-width: 0;
}

@media (max-width: 768px) {
  .friends-layout {
    flex-direction: column;
    min-height: auto;
  }

  .friends-sidebar {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid var(--border-color-light);
    padding: var(--space-2) 0;
  }

  .sidebar-menu {
    flex-direction: row;
    overflow-x: auto;
    padding-bottom: var(--space-2);
  }

  .sidebar-menu li {
    flex: 1;
    min-width: 120px;
    justify-content: center;
    border-radius: var(--radius-md);
  }

  .menu-icon {
    margin-right: var(--space-2);
  }

  .friends-content {
    padding: var(--space-4) 0;
  }
}
</style>
