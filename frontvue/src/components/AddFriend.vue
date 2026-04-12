<template>
  <div class="add-friend">
    <div class="add-friend-header">
      <h2>添加好友</h2>
    </div>
    
    <div class="add-friend-content">
      <div class="search-section">
        <input 
          type="text" 
          v-model="searchQuery" 
          placeholder="搜索用户名或邮箱..."
          class="search-input"
          @input="handleSearch"
        >
      </div>
      
      <div v-if="loading" class="loading-container">
        <div class="loading-spinner"></div>
        <p>搜索中...</p>
      </div>
      
      <div v-else-if="searchResults.length === 0 && searchQuery" class="empty-results">
        <div class="empty-icon"></div>
        <p>未找到匹配的用户</p>
      </div>
      
      <div v-else-if="searchResults.length > 0" class="search-results">
        <div 
          v-for="user in searchResults" 
          :key="user.id" 
          class="user-item"
        >
          <div class="user-avatar" :style="{ backgroundImage: user.avatar ? `url(${user.avatar})` : 'none' }">
            <span v-if="!user.avatar">{{ getInitials(user.username) }}</span>
          </div>
          <div class="user-info">
            <h3 class="user-name">{{ user.username }}</h3>
            <p class="user-email">{{ user.email }}</p>
          </div>
          <div class="user-actions">
            <button 
              v-if="!isFriend(user.id) && !hasSentRequest(user.id)"
              class="add-btn"
              @click="sendFriendRequest(user.id, user.username)"
            >
              添加好友
            </button>
            <button 
              v-else-if="hasSentRequest(user.id)"
              class="pending-btn"
              disabled
            >
              请求已发送
            </button>
            <button 
              v-else
              class="friend-btn"
              disabled
            >
              已是好友
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useToast } from '../composables/useToast'
import { userApi } from '../api/user'

const { showToast } = useToast()

// 状态数据
const searchQuery = ref('')
const loading = ref(false)
const searchResults = ref<any[]>([])
const friends = ref<number[]>([])
const sentRequests = ref<number[]>([])

// 搜索用户
const handleSearch = async () => {
  if (!searchQuery.value.trim()) {
    searchResults.value = []
    return
  }
  
  loading.value = true
  try {
    // 使用真实的搜索API
    const response = await userApi.searchUsers(searchQuery.value)
    searchResults.value = response
  } catch (error) {
    console.error('搜索用户失败:', error)
    showToast('搜索用户失败', 'error')
  } finally {
    loading.value = false
  }
}

// 发送好友请求
const sendFriendRequest = async (userId: number, username: string) => {
  try {
    await userApi.sendFriendRequest(userId)
    sentRequests.value.push(userId)
    showToast(`已向 ${username} 发送好友请求`, 'success')
  } catch (error) {
    console.error('发送好友请求失败:', error)
    showToast('发送好友请求失败', 'error')
  }
}

// 检查是否是好友
const isFriend = (userId: number) => {
  return friends.value.includes(userId)
}

// 检查是否已发送请求
const hasSentRequest = (userId: number) => {
  return sentRequests.value.includes(userId)
}

// 获取用户名首字母
const getInitials = (username: string) => {
  return username.charAt(0).toUpperCase()
}

// 获取好友列表和已发送的请求
const fetchFriendsAndRequests = async () => {
  try {
    // 获取好友列表
    const friendsResponse = await userApi.getFriends()
    friends.value = friendsResponse.friends.map((friend: any) => friend.id)
    
    // 获取已发送的好友请求
    const sentRequestsResponse = await userApi.getSentFriendRequests()
    sentRequests.value = sentRequestsResponse.map((request: any) => request.receiver.id)
  } catch (error) {
    console.error('获取好友信息失败:', error)
  }
}

// 生命周期钩子
onMounted(() => {
  fetchFriendsAndRequests()
})
</script>

<style scoped>
.add-friend {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
}

.add-friend-header {
  margin-bottom: 20px;
}

.add-friend-header h2 {
  margin: 0;
  font-size: 1.5rem;
  color: #333;
}

.add-friend-content {
  background-color: white;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.search-section {
  padding: 20px;
  border-bottom: 1px solid #f0f0f0;
}

.search-input {
  width: 100%;
  padding: 10px 15px;
  border: 1px solid #ddd;
  border-radius: 25px;
  font-size: 1rem;
  transition: all 0.3s;
}

.search-input:focus {
  outline: none;
  border-color: #4361ee;
  box-shadow: 0 0 0 2px rgba(67, 97, 238, 0.1);
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: #888;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(67, 97, 238, 0.2);
  border-radius: 50%;
  border-top-color: #4361ee;
  animation: spin 1s linear infinite;
  margin-bottom: 10px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-results {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #888;
  text-align: center;
}

.empty-icon {
  width: 80px;
  height: 80px;
  background-color: #f0f0f0;
  border-radius: 50%;
  margin-bottom: 20px;
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%23ccc"><path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/></svg>');
  background-size: 50%;
  background-repeat: no-repeat;
  background-position: center;
}

.search-results {
  padding: 10px 0;
}

.user-item {
  display: flex;
  align-items: center;
  padding: 15px 20px;
  border-bottom: 1px solid #f0f0f0;
  transition: all 0.3s;
}

.user-item:hover {
  background-color: #f9f9f9;
}

.user-item:last-child {
  border-bottom: none;
}

.user-avatar {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background-color: #4361ee;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  font-weight: 600;
  margin-right: 15px;
  flex-shrink: 0;
}

.user-info {
  flex: 1;
  min-width: 0;
}

.user-name {
  margin: 0 0 5px 0;
  font-size: 1rem;
  font-weight: 600;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-email {
  margin: 0;
  font-size: 0.85rem;
  color: #666;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-actions {
  display: flex;
  gap: 10px;
}

.add-btn, .pending-btn, .friend-btn {
  padding: 6px 16px;
  border: none;
  border-radius: 20px;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.3s;
}

.add-btn {
  background-color: #4361ee;
  color: white;
}

.add-btn:hover {
  background-color: #3a0ca3;
}

.pending-btn {
  background-color: #f0f0f0;
  color: #666;
  cursor: default;
}

.friend-btn {
  background-color: #e8f5e8;
  color: #2e7d32;
  cursor: default;
}

@media (max-width: 768px) {
  .add-friend {
    padding: 10px;
  }
  
  .user-item {
    padding: 12px;
  }
  
  .user-actions {
    flex-direction: column;
    gap: 5px;
  }
  
  .add-btn, .pending-btn, .friend-btn {
    padding: 4px 12px;
    font-size: 0.8rem;
  }
}
</style>