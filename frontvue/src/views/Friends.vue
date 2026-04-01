<template>
  <div class="friends-page">
    <div class="friends-container">
      <div class="friends-sidebar">
        <h1>好友</h1>
        <ul class="sidebar-menu">
          <li :class="{ active: activeTab === 'list' }" @click="activeTab = 'list'">
            <span class="menu-icon friends-icon"></span>
            <span class="menu-text">好友列表</span>
          </li>
          <li :class="{ active: activeTab === 'requests' }" @click="activeTab = 'requests'">
            <span class="menu-icon requests-icon"></span>
            <span class="menu-text">好友请求</span>
            <span v-if="unreadRequests > 0" class="badge">{{ unreadRequests }}</span>
          </li>
          <li :class="{ active: activeTab === 'add' }" @click="activeTab = 'add'">
            <span class="menu-icon add-icon"></span>
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
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import FriendsList from '../components/FriendsList.vue'
import FriendRequests from '../components/FriendRequests.vue'
import AddFriend from '../components/AddFriend.vue'

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
  min-height: 100vh;
  background-color: #f5f7fa;
  padding: 20px;
}

.friends-container {
  max-width: 1000px;
  margin: 0 auto;
  display: flex;
  background-color: white;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.friends-sidebar {
  width: 250px;
  background-color: #f9f9f9;
  border-right: 1px solid #f0f0f0;
  padding: 20px 0;
}

.friends-sidebar h1 {
  margin: 0 20px 30px 20px;
  font-size: 1.5rem;
  color: #333;
}

.sidebar-menu {
  list-style: none;
  padding: 0;
  margin: 0;
}

.sidebar-menu li {
  display: flex;
  align-items: center;
  padding: 12px 20px;
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
}

.sidebar-menu li:hover {
  background-color: rgba(67, 97, 238, 0.1);
}

.sidebar-menu li.active {
  background-color: rgba(67, 97, 238, 0.1);
  border-left: 3px solid #4361ee;
}

.menu-icon {
  width: 20px;
  height: 20px;
  background-size: contain;
  background-repeat: no-repeat;
  background-position: center;
  margin-right: 12px;
}

.friends-icon {
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%23666"><path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/></svg>');
}

.requests-icon {
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%23666"><path d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.5-9H8.5V6c0-1.38 1.12-2.5 2.5-2.5s2.5 1.12 2.5 2.5v2z"/></svg>');
}

.add-icon {
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%23666"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/></svg>');
}

.sidebar-menu li.active .friends-icon {
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%234361ee"><path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/></svg>');
}

.sidebar-menu li.active .requests-icon {
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%234361ee"><path d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.5-9H8.5V6c0-1.38 1.12-2.5 2.5-2.5s2.5 1.12 2.5 2.5v2z"/></svg>');
}

.sidebar-menu li.active .add-icon {
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%234361ee"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/></svg>');
}

.menu-text {
  flex: 1;
  font-size: 0.95rem;
  color: #333;
}

.sidebar-menu li.active .menu-text {
  color: #4361ee;
  font-weight: 500;
}

.badge {
  background-color: #f44336;
  color: white;
  border-radius: 10px;
  padding: 2px 8px;
  font-size: 0.75rem;
  font-weight: 600;
  min-width: 20px;
  text-align: center;
}

.friends-content {
  flex: 1;
  min-height: 600px;
}

@media (max-width: 768px) {
  .friends-page {
    padding: 10px;
  }
  
  .friends-container {
    flex-direction: column;
  }
  
  .friends-sidebar {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid #f0f0f0;
    padding: 10px 0;
  }
  
  .friends-sidebar h1 {
    margin: 0 10px 15px 10px;
    font-size: 1.2rem;
  }
  
  .sidebar-menu {
    display: flex;
    overflow-x: auto;
  }
  
  .sidebar-menu li {
    flex: 1;
    min-width: 120px;
    border-left: none;
    border-bottom: 3px solid transparent;
  }
  
  .sidebar-menu li.active {
    border-left: none;
    border-bottom: 3px solid #4361ee;
  }
  
  .friends-content {
    min-height: 400px;
  }
}
</style>