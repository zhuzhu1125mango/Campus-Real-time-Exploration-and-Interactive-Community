<template>
  <div class="friends-list">
    <div class="friends-header">
      <h2>我的好友</h2>
      <div class="search-box">
        <input 
          type="text" 
          v-model="searchQuery" 
          placeholder="搜索好友..."
          class="search-input"
        >
      </div>
    </div>
    
    <div class="friends-content">
      <div v-if="loading" class="loading-container">
        <div class="loading-spinner"></div>
        <p>加载中...</p>
      </div>
      
      <div v-else-if="friends.length === 0" class="empty-friends">
        <div class="empty-icon"></div>
        <p>暂无好友</p>
        <p class="empty-hint">去发现并添加好友吧！</p>
      </div>
      
      <div v-else class="friends-list-container">
        <div 
          v-for="friend in filteredFriends" 
          :key="friend.id" 
          class="friend-item"
        >
          <div class="friend-avatar" :style="{ backgroundImage: friend.avatar ? `url(${friend.avatar})` : 'none' }">
            <span v-if="!friend.avatar">{{ getInitials(friend.username) }}</span>
          </div>
          <div class="friend-info">
            <h3 class="friend-name">{{ friend.username }}</h3>
            <p class="friend-email">{{ friend.email }}</p>
          </div>
          <div class="friend-actions">
            <button class="message-btn" @click="navigateToChat(friend.id)">
              <span class="message-icon"></span>
              私信
            </button>
            <button class="remove-btn" @click="confirmRemoveFriend(friend.id, friend.username)">
              <span class="remove-icon"></span>
              移除
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 移除好友确认对话框 -->
    <div v-if="showRemoveConfirm" class="confirm-dialog">
      <div class="confirm-content">
        <h3>确认移除好友</h3>
        <p>确定要将 {{ friendToRemoveName }} 从好友列表中移除吗？</p>
        <div class="confirm-buttons">
          <button class="cancel-btn" @click="showRemoveConfirm = false">取消</button>
          <button class="confirm-btn" @click="removeFriend">确认移除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from '../composables/useToast'
import { userApi } from '../api/user'

const router = useRouter()
const { showToast } = useToast()

// 状态数据
const loading = ref(false)
const friends = ref<any[]>([])
const searchQuery = ref('')
const showRemoveConfirm = ref(false)
const friendToRemoveId = ref<number | null>(null)
const friendToRemoveName = ref('')

// 过滤后的好友列表
const filteredFriends = computed(() => {
  if (!searchQuery.value) {
    return friends.value
  }
  const query = searchQuery.value.toLowerCase()
  return friends.value.filter(friend => 
    friend.username.toLowerCase().includes(query) ||
    friend.email.toLowerCase().includes(query)
  )
})

// 获取好友列表
const fetchFriends = async () => {
  loading.value = true
  try {
    const response = await userApi.getFriends()
    friends.value = response.friends
  } catch (error) {
    console.error('获取好友列表失败:', error)
    showToast('获取好友列表失败', 'error')
  } finally {
    loading.value = false
  }
}

// 确认移除好友
const confirmRemoveFriend = (friendId: number, friendName: string) => {
  friendToRemoveId.value = friendId
  friendToRemoveName.value = friendName
  showRemoveConfirm.value = true
}

// 移除好友
const removeFriend = async () => {
  if (!friendToRemoveId.value) return
  
  try {
    await userApi.removeFriend(friendToRemoveId.value)
    // 从列表中移除
    friends.value = friends.value.filter(friend => friend.id !== friendToRemoveId.value)
    showRemoveConfirm.value = false
    showToast('好友已移除', 'success')
  } catch (error) {
    console.error('移除好友失败:', error)
    showToast('移除好友失败', 'error')
  }
}

// 导航到聊天页面
const navigateToChat = (friendId: number) => {
  router.push(`/chat/${friendId}`)
}

// 获取用户名首字母
const getInitials = (username: string) => {
  return username.charAt(0).toUpperCase()
}

// 生命周期钩子
onMounted(() => {
  fetchFriends()
})
</script>

<style scoped>
.friends-list {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.friends-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.friends-header h2 {
  margin: 0;
  font-size: 1.5rem;
  color: #333;
}

.search-box {
  flex: 1;
  max-width: 300px;
  margin-left: 20px;
}

.search-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 20px;
  font-size: 0.9rem;
  transition: all 0.3s;
}

.search-input:focus {
  outline: none;
  border-color: #4361ee;
  box-shadow: 0 0 0 2px rgba(67, 97, 238, 0.1);
}

.friends-content {
  background-color: white;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  overflow: hidden;
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

.empty-friends {
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
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%23ccc"><path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/></svg>');
  background-size: 50%;
  background-repeat: no-repeat;
  background-position: center;
}

.empty-friends p {
  margin: 5px 0;
}

.empty-hint {
  font-size: 0.9rem;
  color: #aaa;
}

.friends-list-container {
  padding: 10px 0;
}

.friend-item {
  display: flex;
  align-items: center;
  padding: 15px 20px;
  border-bottom: 1px solid #f0f0f0;
  transition: all 0.3s;
}

.friend-item:hover {
  background-color: #f9f9f9;
}

.friend-item:last-child {
  border-bottom: none;
}

.friend-avatar {
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

.friend-info {
  flex: 1;
  min-width: 0;
}

.friend-name {
  margin: 0 0 5px 0;
  font-size: 1rem;
  font-weight: 600;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.friend-email {
  margin: 0;
  font-size: 0.85rem;
  color: #666;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.friend-actions {
  display: flex;
  gap: 10px;
}

.message-btn, .remove-btn {
  padding: 6px 12px;
  border: 1px solid #ddd;
  border-radius: 20px;
  background-color: white;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 5px;
}

.message-btn {
  color: #4361ee;
  border-color: #4361ee;
}

.message-btn:hover {
  background-color: #4361ee;
  color: white;
}

.remove-btn {
  color: #f44336;
  border-color: #f44336;
}

.remove-btn:hover {
  background-color: #f44336;
  color: white;
}

.message-icon, .remove-icon {
  width: 14px;
  height: 14px;
  background-size: contain;
  background-repeat: no-repeat;
  background-position: center;
}

.message-icon {
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M20 2H4c-1.1 0-1.99.9-1.99 2L2 22l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-2 12H6v-2h12v2zm0-3H6V9h12v2zm0-3H6V6h12v2z"/></svg>');
}

.remove-icon {
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/></svg>');
}

.confirm-dialog {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.confirm-content {
  background-color: white;
  border-radius: 12px;
  padding: 20px;
  max-width: 400px;
  width: 90%;
  box-shadow: 0 5px 20px rgba(0, 0, 0, 0.15);
}

.confirm-content h3 {
  margin: 0 0 15px 0;
  color: #333;
}

.confirm-content p {
  margin: 0 0 20px 0;
  color: #666;
}

.confirm-buttons {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.cancel-btn, .confirm-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s;
}

.cancel-btn {
  background-color: #f0f0f0;
  color: #333;
}

.cancel-btn:hover {
  background-color: #e0e0e0;
}

.confirm-btn {
  background-color: #f44336;
  color: white;
}

.confirm-btn:hover {
  background-color: #d32f2f;
}

@media (max-width: 768px) {
  .friends-list {
    padding: 10px;
  }
  
  .friends-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .search-box {
    width: 100%;
    max-width: none;
    margin-left: 0;
  }
  
  .friend-item {
    padding: 12px;
  }
  
  .friend-actions {
    flex-direction: column;
    gap: 5px;
  }
  
  .message-btn, .remove-btn {
    padding: 4px 8px;
    font-size: 0.8rem;
  }
}
</style>