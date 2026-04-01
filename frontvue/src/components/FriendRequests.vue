<template>
  <div class="friend-requests">
    <div class="requests-header">
      <h2>好友请求</h2>
    </div>
    
    <div class="requests-content">
      <div v-if="loading" class="loading-container">
        <div class="loading-spinner"></div>
        <p>加载中...</p>
      </div>
      
      <div v-else-if="requests.length === 0" class="empty-requests">
        <div class="empty-icon"></div>
        <p>暂无好友请求</p>
      </div>
      
      <div v-else class="requests-list">
        <div 
          v-for="request in requests" 
          :key="request.id" 
          class="request-item"
        >
          <div class="request-avatar" :style="{ backgroundImage: request.sender.avatar ? `url(${request.sender.avatar})` : 'none' }">
            <span v-if="!request.sender.avatar">{{ getInitials(request.sender.username) }}</span>
          </div>
          <div class="request-info">
            <h3 class="request-sender">{{ request.sender.username }}</h3>
            <p class="request-time">{{ formatTime(request.created_at) }}</p>
          </div>
          <div class="request-actions">
            <button class="accept-btn" @click="acceptRequest(request.id)">
              接受
            </button>
            <button class="reject-btn" @click="rejectRequest(request.id)">
              拒绝
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
const loading = ref(false)
const requests = ref<any[]>([])

// 获取好友请求列表
const fetchFriendRequests = async () => {
  loading.value = true
  try {
    const response = await userApi.getReceivedFriendRequests()
    requests.value = response
  } catch (error) {
    console.error('获取好友请求失败:', error)
    showToast('获取好友请求失败', 'error')
  } finally {
    loading.value = false
  }
}

// 接受好友请求
const acceptRequest = async (requestId: number) => {
  try {
    await userApi.acceptFriendRequest(requestId)
    // 从列表中移除
    requests.value = requests.value.filter(request => request.id !== requestId)
    showToast('已接受好友请求', 'success')
  } catch (error) {
    console.error('接受好友请求失败:', error)
    showToast('接受好友请求失败', 'error')
  }
}

// 拒绝好友请求
const rejectRequest = async (requestId: number) => {
  try {
    await userApi.rejectFriendRequest(requestId)
    // 从列表中移除
    requests.value = requests.value.filter(request => request.id !== requestId)
    showToast('已拒绝好友请求', 'success')
  } catch (error) {
    console.error('拒绝好友请求失败:', error)
    showToast('拒绝好友请求失败', 'error')
  }
}

// 获取用户名首字母
const getInitials = (username: string) => {
  return username.charAt(0).toUpperCase()
}

// 格式化时间
const formatTime = (dateString: string) => {
  const now = new Date()
  const date = new Date(dateString)
  const diffMs = now.getTime() - date.getTime()
  const diffSec = Math.floor(diffMs / 1000)
  const diffMin = Math.floor(diffSec / 60)
  const diffHour = Math.floor(diffMin / 60)
  const diffDay = Math.floor(diffHour / 24)
  
  if (diffSec < 60) {
    return '刚刚'
  } else if (diffMin < 60) {
    return `${diffMin}分钟前`
  } else if (diffHour < 24) {
    return `${diffHour}小时前`
  } else if (diffDay < 7) {
    return `${diffDay}天前`
  } else {
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
  }
}

// 生命周期钩子
onMounted(() => {
  fetchFriendRequests()
})
</script>

<style scoped>
.friend-requests {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
}

.requests-header {
  margin-bottom: 20px;
}

.requests-header h2 {
  margin: 0;
  font-size: 1.5rem;
  color: #333;
}

.requests-content {
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

.empty-requests {
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

.requests-list {
  padding: 10px 0;
}

.request-item {
  display: flex;
  align-items: center;
  padding: 15px 20px;
  border-bottom: 1px solid #f0f0f0;
  transition: all 0.3s;
}

.request-item:hover {
  background-color: #f9f9f9;
}

.request-item:last-child {
  border-bottom: none;
}

.request-avatar {
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

.request-info {
  flex: 1;
  min-width: 0;
}

.request-sender {
  margin: 0 0 5px 0;
  font-size: 1rem;
  font-weight: 600;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.request-time {
  margin: 0;
  font-size: 0.85rem;
  color: #666;
}

.request-actions {
  display: flex;
  gap: 10px;
}

.accept-btn, .reject-btn {
  padding: 6px 16px;
  border: none;
  border-radius: 20px;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.3s;
}

.accept-btn {
  background-color: #4361ee;
  color: white;
}

.accept-btn:hover {
  background-color: #3a0ca3;
}

.reject-btn {
  background-color: #f0f0f0;
  color: #333;
  border: 1px solid #ddd;
}

.reject-btn:hover {
  background-color: #e0e0e0;
}

@media (max-width: 768px) {
  .friend-requests {
    padding: 10px;
  }
  
  .request-item {
    padding: 12px;
  }
  
  .request-actions {
    flex-direction: column;
    gap: 5px;
  }
  
  .accept-btn, .reject-btn {
    padding: 4px 12px;
    font-size: 0.8rem;
  }
}
</style>