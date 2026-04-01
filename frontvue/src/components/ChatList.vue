<template>
  <div class="chat-list">
    <div class="chat-list-header">
      <h2>私信</h2>
      <div class="search-box">
        <input 
          type="text" 
          v-model="searchQuery" 
          placeholder="搜索对话..."
          class="search-input"
        >
      </div>
    </div>
    
    <div class="chat-list-content">
      <div v-if="loading" class="loading-container">
        <div class="loading-spinner"></div>
        <p>加载中...</p>
      </div>
      
      <div v-else-if="conversations.length === 0" class="empty-chats">
        <div class="empty-icon"></div>
        <p>暂无对话</p>
        <p class="empty-hint">与好友开始私信吧！</p>
      </div>
      
      <div v-else class="conversations-list">
        <div 
          v-for="conversation in filteredConversations" 
          :key="conversation.user.id" 
          class="conversation-item"
          :class="{ 'has-unread': conversation.unread_count > 0 }"
          @click="navigateToChat(conversation.user.id)"
        >
          <div class="conversation-avatar" :style="{ backgroundImage: conversation.user.avatar ? `url(${conversation.user.avatar})` : 'none' }">
            <span v-if="!conversation.user.avatar">{{ getInitials(conversation.user.username) }}</span>
          </div>
          <div class="conversation-info">
            <div class="conversation-header">
              <h3 class="conversation-name">{{ conversation.user.username }}</h3>
              <span class="conversation-time">{{ formatTime(conversation.last_message.created_at) }}</span>
            </div>
            <p class="conversation-preview">{{ getMessagePreview(conversation.last_message.content) }}</p>
          </div>
          <div v-if="conversation.unread_count > 0" class="unread-badge">{{ conversation.unread_count }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from '../composables/useToast'
import { userApi } from '../api/user'

const router = useRouter()
const { showToast } = useToast()

// 状态数据
const loading = ref(false)
const conversations = ref<any[]>([])
const searchQuery = ref('')
let intervalId: number

// 过滤后的对话列表
const filteredConversations = computed(() => {
  if (!searchQuery.value) {
    return conversations.value
  }
  const query = searchQuery.value.toLowerCase()
  return conversations.value.filter(conversation => 
    conversation.user.username.toLowerCase().includes(query) ||
    conversation.last_message.content.toLowerCase().includes(query)
  )
})

// 获取对话列表
const fetchConversations = async () => {
  loading.value = true
  try {
    const response = await userApi.getConversations()
    conversations.value = response
  } catch (error) {
    console.error('获取对话列表失败:', error)
    showToast('获取对话列表失败', 'error')
  } finally {
    loading.value = false
  }
}

// 导航到聊天页面
const navigateToChat = (userId: number) => {
  router.push(`/chat/${userId}`)
}

// 获取消息预览
const getMessagePreview = (content: string) => {
  if (content.length > 30) {
    return content.substring(0, 30) + '...'
  }
  return content
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
    return `${date.getMonth() + 1}/${date.getDate()}`
  }
}

// 生命周期钩子
onMounted(() => {
  fetchConversations()
  // 定期刷新对话列表（每30秒）
  intervalId = window.setInterval(fetchConversations, 30000)
})

onUnmounted(() => {
  clearInterval(intervalId)
})
</script>

<style scoped>
.chat-list {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chat-list-header {
  padding: 20px;
  border-bottom: 1px solid #f0f0f0;
  background-color: white;
}

.chat-list-header h2 {
  margin: 0 0 15px 0;
  font-size: 1.5rem;
  color: #333;
}

.search-box {
  position: relative;
}

.search-input {
  width: 100%;
  padding: 10px 15px;
  border: 1px solid #ddd;
  border-radius: 25px;
  font-size: 0.9rem;
  transition: all 0.3s;
}

.search-input:focus {
  outline: none;
  border-color: #4361ee;
  box-shadow: 0 0 0 2px rgba(67, 97, 238, 0.1);
}

.chat-list-content {
  flex: 1;
  overflow-y: auto;
  background-color: #f9f9f9;
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

.empty-chats {
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
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%23ccc"><path d="M20 2H4c-1.1 0-1.99.9-1.99 2L2 22l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-2 12H6v-2h12v2zm0-3H6V9h12v2zm0-3H6V6h12v2z"/></svg>');
  background-size: 50%;
  background-repeat: no-repeat;
  background-position: center;
}

.empty-chats p {
  margin: 5px 0;
}

.empty-hint {
  font-size: 0.9rem;
  color: #aaa;
}

.conversations-list {
  padding: 10px 0;
}

.conversation-item {
  display: flex;
  align-items: center;
  padding: 15px 20px;
  background-color: white;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
}

.conversation-item:hover {
  background-color: #f5f5f5;
}

.conversation-item.has-unread {
  background-color: rgba(67, 97, 238, 0.05);
}

.conversation-avatar {
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

.conversation-info {
  flex: 1;
  min-width: 0;
}

.conversation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 5px;
}

.conversation-name {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.conversation-time {
  font-size: 0.8rem;
  color: #999;
}

.conversation-preview {
  margin: 0;
  font-size: 0.9rem;
  color: #666;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.unread-badge {
  background-color: #f44336;
  color: white;
  border-radius: 10px;
  padding: 2px 8px;
  font-size: 0.75rem;
  font-weight: 600;
  min-width: 20px;
  text-align: center;
  margin-left: 10px;
}

@media (max-width: 768px) {
  .chat-list-header {
    padding: 15px;
  }
  
  .chat-list-header h2 {
    font-size: 1.2rem;
    margin-bottom: 10px;
  }
  
  .conversation-item {
    padding: 12px 15px;
  }
  
  .conversation-avatar {
    width: 40px;
    height: 40px;
    font-size: 1rem;
  }
  
  .conversation-name {
    font-size: 0.9rem;
  }
  
  .conversation-time {
    font-size: 0.7rem;
  }
  
  .conversation-preview {
    font-size: 0.8rem;
  }
}
</style>