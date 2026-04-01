<template>
  <div class="chat-detail">
    <div class="chat-header">
      <button class="back-btn" @click="goBack">
        <span class="back-icon"></span>
      </button>
      <div class="chat-user-info">
        <div class="chat-user-avatar" :style="{ backgroundImage: user?.avatar ? `url(${user.avatar})` : 'none' }">
          <span v-if="!user?.avatar">{{ getInitials(user?.username || '') }}</span>
        </div>
        <h3 class="chat-user-name">{{ user?.username }}</h3>
      </div>
      <div class="chat-actions">
        <button class="more-btn">
          <span class="more-icon"></span>
        </button>
      </div>
    </div>
    
    <div class="chat-messages" ref="messagesContainer">
      <div v-if="loading" class="loading-container">
        <div class="loading-spinner"></div>
        <p>加载中...</p>
      </div>
      
      <div v-else-if="messages.length === 0" class="empty-messages">
        <p>开始与 {{ user?.username }} 聊天吧！</p>
      </div>
      
      <div v-else class="messages-list">
        <div 
          v-for="message in messages" 
          :key="message.id" 
          :class="['message-item', message.sender.id === currentUserId ? 'sent' : 'received']"
        >
          <div class="message-content">
            <p class="message-text">{{ message.content }}</p>
            <span class="message-time">{{ formatTime(message.created_at) }}</span>
          </div>
        </div>
      </div>
    </div>
    
    <div class="chat-input-area">
      <input 
        type="text" 
        v-model="messageInput" 
        placeholder="输入消息..."
        class="message-input"
        @keyup.enter="sendMessage"
      >
      <button class="send-btn" @click="sendMessage" :disabled="!messageInput.trim()">
        <span class="send-icon"></span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useToast } from '../composables/useToast'
import { userApi } from '../api/user'
import { useUserStore } from '../stores/userStore'

const router = useRouter()
const route = useRoute()
const { showToast } = useToast()
const userStore = useUserStore()

// 状态数据
const loading = ref(false)
const messages = ref<any[]>([])
const user = ref<any>(null)
const messageInput = ref('')
const messagesContainer = ref<HTMLElement | null>(null)

// 获取当前用户ID
const currentUserId = computed(() => userStore.user?.id || 0)

// 获取用户ID参数
const userId = computed(() => route.params.id as string)

// 加载对话
const loadConversation = async () => {
  if (!userId.value) return
  
  loading.value = true
  try {
    const response = await userApi.getConversation(Number(userId.value))
    user.value = response.user
    messages.value = response.messages
    
    // 滚动到底部
    await nextTick()
    scrollToBottom()
  } catch (error) {
    console.error('加载对话失败:', error)
    showToast('加载对话失败', 'error')
  } finally {
    loading.value = false
  }
}

// 发送消息
const sendMessage = async () => {
  if (!messageInput.value.trim() || !userId.value) return
  
  const content = messageInput.value.trim()
  messageInput.value = ''
  
  try {
    // 先添加到消息列表（乐观更新）
    const tempMessage = {
      id: Date.now(),
      sender: userStore.user,
      receiver: user.value,
      content,
      is_read: false,
      created_at: new Date().toISOString()
    }
    messages.value.push(tempMessage)
    
    // 滚动到底部
    await nextTick()
    scrollToBottom()
    
    // 发送消息
    await userApi.sendMessage({
      receiver: Number(userId.value),
      content
    })
    
    // 重新加载对话，获取最新消息
    await loadConversation()
  } catch (error) {
    console.error('发送消息失败:', error)
    showToast('发送消息失败', 'error')
    // 移除临时消息
    messages.value = messages.value.filter(msg => msg.id !== Date.now())
  }
}

// 滚动到底部
const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// 获取用户名首字母
const getInitials = (username: string) => {
  return username.charAt(0).toUpperCase()
}

// 格式化时间
const formatTime = (dateString: string) => {
  const date = new Date(dateString)
  return `${date.getHours()}:${String(date.getMinutes()).padStart(2, '0')}`
}

// 返回上一页
const goBack = () => {
  router.push('/chat')
}

// 监听路由参数变化
watch(() => route.params.id, () => {
  loadConversation()
})

// 生命周期钩子
onMounted(() => {
  loadConversation()
  
  // 定期刷新对话（每10秒）
  const intervalId = setInterval(loadConversation, 10000)
  
  // 清理函数
  return () => clearInterval(intervalId)
})
</script>

<style scoped>
.chat-detail {
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: #f9f9f9;
}

.chat-header {
  display: flex;
  align-items: center;
  padding: 15px 20px;
  background-color: white;
  border-bottom: 1px solid #f0f0f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.back-btn {
  width: 36px;
  height: 36px;
  border: none;
  background-color: transparent;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s;
  margin-right: 15px;
}

.back-btn:hover {
  background-color: #f0f0f0;
}

.back-icon {
  width: 20px;
  height: 20px;
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%23333"><path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/></svg>');
  background-size: contain;
  background-repeat: no-repeat;
  background-position: center;
}

.chat-user-info {
  flex: 1;
  display: flex;
  align-items: center;
}

.chat-user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: #4361ee;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
  font-weight: 600;
  margin-right: 12px;
}

.chat-user-name {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: #333;
}

.chat-actions {
  display: flex;
  gap: 10px;
}

.more-btn {
  width: 36px;
  height: 36px;
  border: none;
  background-color: transparent;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s;
}

.more-btn:hover {
  background-color: #f0f0f0;
}

.more-icon {
  width: 20px;
  height: 20px;
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%23333"><path d="M12 8c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z"/></svg>');
  background-size: contain;
  background-repeat: no-repeat;
  background-position: center;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
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

.empty-messages {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
  color: #888;
  font-size: 1.1rem;
}

.messages-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.message-item {
  max-width: 70%;
  display: flex;
  margin-bottom: 10px;
}

.message-item.sent {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message-item.received {
  align-self: flex-start;
}

.message-content {
  padding: 10px 15px;
  border-radius: 18px;
  position: relative;
}

.message-item.sent .message-content {
  background-color: #4361ee;
  color: white;
  border-bottom-right-radius: 4px;
}

.message-item.received .message-content {
  background-color: white;
  color: #333;
  border-bottom-left-radius: 4px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.message-text {
  margin: 0 0 5px 0;
  line-height: 1.4;
}

.message-time {
  font-size: 0.75rem;
  opacity: 0.7;
  display: block;
  text-align: right;
}

.chat-input-area {
  display: flex;
  align-items: center;
  padding: 15px 20px;
  background-color: white;
  border-top: 1px solid #f0f0f0;
  gap: 10px;
}

.message-input {
  flex: 1;
  padding: 12px 15px;
  border: 1px solid #ddd;
  border-radius: 25px;
  font-size: 0.9rem;
  transition: all 0.3s;
  resize: none;
}

.message-input:focus {
  outline: none;
  border-color: #4361ee;
  box-shadow: 0 0 0 2px rgba(67, 97, 238, 0.1);
}

.send-btn {
  width: 40px;
  height: 40px;
  border: none;
  background-color: #4361ee;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s;
}

.send-btn:hover:not(:disabled) {
  background-color: #3a0ca3;
  transform: scale(1.05);
}

.send-btn:disabled {
  background-color: #ccc;
  cursor: default;
}

.send-icon {
  width: 20px;
  height: 20px;
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>');
  background-size: contain;
  background-repeat: no-repeat;
  background-position: center;
}

@media (max-width: 768px) {
  .chat-header {
    padding: 12px 15px;
  }
  
  .chat-messages {
    padding: 15px;
  }
  
  .message-item {
    max-width: 85%;
  }
  
  .chat-input-area {
    padding: 12px 15px;
  }
  
  .message-input {
    padding: 10px 12px;
  }
}
</style>