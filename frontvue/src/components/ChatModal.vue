<template>
  <div class="chat-modal" v-if="visible">
    <div class="chat-modal-overlay" @click="close"></div>
    <div class="chat-modal-content">
      <div class="chat-modal-header">
        <div class="chat-modal-title">
          <div class="chat-user-avatar" :style="{ backgroundImage: `url(${friend.avatar || 'http://localhost:8000/media/avatars1/默认头像.png'})` }"></div>
          <h3>{{ friend.username }}</h3>
        </div>
        <button class="chat-modal-close" @click="close">×</button>
      </div>
      <div class="chat-modal-body">
        <div class="chat-messages" ref="messagesContainer">
          <!-- 消息堆叠显示 -->
          <template v-for="(group, index) in groupedMessages" :key="index">
            <div 
              :class="['chat-message-group', { 'own': group.isOwn }]"
            >
              <div class="message-avatar" v-if="!group.isContinuation">
                <img :src="group.messages[0].sender.avatar || 'http://localhost:8000/media/avatars1/默认头像.png'" :alt="group.messages[0].sender.username">
              </div>
              <div class="message-avatar-placeholder" v-else></div>
              <div class="message-group-content">
                <div class="message-sender" v-if="!group.isContinuation">{{ group.messages[0].sender.username }}</div>
                <div 
                  v-for="message in group.messages" 
                  :key="message.id" 
                  class="message-item"
                >
                  <div class="message-text">{{ message.content }}</div>
                  <div class="message-time">{{ formatTime(message.created_at) }}</div>
                </div>
              </div>
            </div>
          </template>
          <div v-if="loading" class="loading-messages">加载中...</div>
          <div v-if="messages.length === 0 && !loading" class="empty-messages">暂无消息，开始聊天吧！</div>
        </div>
        <div class="chat-input-area">
          <input 
            type="text" 
            v-model="messageInput" 
            placeholder="输入消息..." 
            @keyup.enter="sendMessage"
            class="chat-input"
          >
          <button @click="sendMessage" class="chat-send-btn">发送</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick, computed } from 'vue'
import { userApi } from '../api/user'
import { useToast } from '../composables/useToast'
import { useUserStore } from '../stores/userStore'
import { messageStorage, useMessageStorageCleanup } from '../utils/messageStorage'

// Props
const props = defineProps<{
  visible: boolean
  friend: {
    id: number
    username: string
    email: string
    avatar?: string
  }
}>()

// Emits
const emit = defineEmits<{
  (e: 'close'): void
}>()

// State
const userStore = useUserStore()
const { showToast } = useToast()
const messages = ref<any[]>([])
const messageInput = ref('')
const loading = ref(false)
const messagesContainer = ref<HTMLElement | null>(null)
const ws = ref<WebSocket | null>(null)

// 分组消息，实现堆叠效果
const groupedMessages = computed(() => {
  if (messages.value.length === 0) return []
  
  const groups: any[] = []
  let currentGroup: any = null
  
  messages.value.forEach((message, index) => {
    const isOwn = message.sender.id === userStore.user?.id
    const prevMessage = index > 0 ? messages.value[index - 1] : null
    const isContinuation = prevMessage && 
                          prevMessage.sender.id === message.sender.id &&
                          (new Date(message.created_at).getTime() - new Date(prevMessage.created_at).getTime()) < 60000 // 1分钟内的消息视为连续
    
    if (!currentGroup || !isContinuation) {
      // 开始新组
      currentGroup = {
        messages: [message],
        isOwn,
        isContinuation: false
      }
      groups.push(currentGroup)
    } else {
      // 继续当前组
      currentGroup.messages.push(message)
      currentGroup.isContinuation = true
    }
  })
  
  return groups
})

// Format time
const formatTime = (timeString: string) => {
  const date = new Date(timeString)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

// Scroll to bottom
const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

// Load messages
const loadMessages = async () => {
  if (!props.friend) return
  
  loading.value = true
  try {
    // 先从本地存储加载消息
    const storedMessages = messageStorage.getPrivateMessages(props.friend.id)
    if (storedMessages.length > 0) {
      messages.value = storedMessages
      console.log('从本地存储加载了', storedMessages.length, '条私信');
    }
    
    // 从服务器获取最新消息
    const response = await userApi.getConversation(props.friend.id)
    if (response && response.messages && Array.isArray(response.messages)) {
      messages.value = response.messages
      // 保存到本地存储
      messageStorage.savePrivateMessages(props.friend.id, response.messages)
      scrollToBottom()
    }
  } catch (error) {
    console.error('加载消息失败:', error)
    showToast('加载消息失败', 'error')
  } finally {
    loading.value = false
  }
}

// Send message
const sendMessage = async () => {
  if (!messageInput.value.trim() || !props.friend) return
  
  const content = messageInput.value.trim()
  messageInput.value = ''
  
  try {
    // 立即添加到本地消息列表
    if (userStore.user) {
      const newMessage = {
        id: Date.now(),
        content,
        sender: {
          id: userStore.user.id,
          username: userStore.user.username,
          avatar: userStore.user.avatar
        },
        receiver: {
          id: props.friend.id,
          username: props.friend.username,
          avatar: props.friend.avatar
        },
        created_at: new Date().toISOString(),
        is_read: true
      }
      messages.value.push(newMessage)
      // 保存到本地存储
      messageStorage.savePrivateMessages(props.friend.id, messages.value)
      scrollToBottom()
    }
    
    // 发送消息到服务器
    await userApi.sendMessage({ receiver: props.friend.id, content })
  } catch (error) {
    console.error('发送消息失败:', error)
    showToast('发送消息失败', 'error')
  }
}

// Close modal
const close = () => {
  // 保存消息到本地存储
  if (props.friend) {
    messageStorage.savePrivateMessages(props.friend.id, messages.value)
  }
  emit('close')
}

// Init WebSocket
const initWebSocket = () => {
  // 关闭现有连接
  if (ws.value) {
    ws.value.close()
  }
  
  // 创建新连接
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/';
  const baseUrl = new URL(API_BASE_URL);
  let wsUrl = (window.location.protocol === 'https:' ? 'wss:' : 'ws:') + 
             '//' + baseUrl.host + '/ws/chat';
  
  // 添加认证token
  if (userStore.isLoggedIn && userStore.token) {
    wsUrl += `?token=${encodeURIComponent(userStore.token)}`;
  }
  
  ws.value = new WebSocket(wsUrl)
  
  ws.value.onopen = () => {
    console.log('聊天WebSocket连接已建立')
  }
  
  ws.value.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      
      // 处理私信消息
      if (data.type === 'private_message' && data.recipient_id === userStore.user?.id) {
        const newMessage = {
          id: data.id,
          content: data.message,
          sender: {
            id: data.sender_id,
            username: data.sender_username,
            avatar: data.sender_avatar
          },
          receiver: {
            id: data.recipient_id,
            username: userStore.user?.username || '',
            avatar: userStore.user?.avatar
          },
          created_at: data.time,
          is_read: false
        }
        messages.value.push(newMessage)
        // 保存到本地存储
        if (props.friend) {
          messageStorage.savePrivateMessages(props.friend.id, messages.value)
        }
        scrollToBottom()
      }
    } catch (error) {
      console.error('处理WebSocket消息失败:', error)
    }
  }
  
  ws.value.onclose = () => {
    console.log('聊天WebSocket连接已关闭')
  }
  
  ws.value.onerror = (error) => {
    console.error('聊天WebSocket错误:', error)
  }
}

// 监听消息变化，保存到本地存储
watch(messages, (newMessages) => {
  if (props.friend) {
    messageStorage.savePrivateMessages(props.friend.id, newMessages)
  }
}, { deep: true })

// Watch for visible changes
watch(() => props.visible, (newValue) => {
  if (newValue) {
    loadMessages()
    initWebSocket()
  } else {
    if (ws.value) {
      ws.value.close()
    }
    // 保存消息到本地存储
    if (props.friend) {
      messageStorage.savePrivateMessages(props.friend.id, messages.value)
    }
  }
})

onMounted(() => {
  // 启动消息存储清理
  useMessageStorageCleanup()
  
  if (props.visible) {
    loadMessages()
    initWebSocket()
  }
})

onUnmounted(() => {
  if (ws.value) {
    ws.value.close()
  }
  // 保存消息到本地存储
  if (props.friend) {
    messageStorage.savePrivateMessages(props.friend.id, messages.value)
  }
})
</script>

<style scoped>
.chat-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chat-modal-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(2px);
}

.chat-modal-content {
  position: relative;
  width: 500px;
  height: 600px;
  background-color: white;
  border-radius: 12px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
  z-index: 1001;
}

.chat-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  border-bottom: 1px solid #f0f0f0;
  background-color: #f9f9f9;
  border-radius: 12px 12px 0 0;
}

.chat-modal-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.chat-user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-size: cover;
  background-position: center;
  background-color: #f0f0f0;
}

.chat-modal-title h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: #333;
}

.chat-modal-close {
  width: 30px;
  height: 30px;
  border: none;
  background: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #666;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.3s;
}

.chat-modal-close:hover {
  background-color: #f0f0f0;
  color: #333;
}

.chat-modal-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chat-messages {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.chat-message-group {
  display: flex;
  gap: 10px;
  max-width: 80%;
  margin-bottom: 15px;
}

.chat-message-group.own {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message-avatar {
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  margin-top: 2px;
}

.message-avatar-placeholder {
  width: 36px;
  height: 36px;
  flex-shrink: 0;
}

.message-avatar img {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
}

.message-group-content {
  flex: 1;
  min-width: 0;
}

.message-sender {
  font-size: 0.75rem;
  color: #666;
  margin-bottom: 4px;
  margin-left: 4px;
}

.chat-message-group.own .message-sender {
  text-align: right;
  margin-right: 4px;
  margin-left: 0;
}

.message-item {
  margin-bottom: 6px;
}

.message-text {
  background-color: #f0f0f0;
  padding: 10px 14px;
  border-radius: 18px;
  font-size: 0.9rem;
  line-height: 1.4;
  word-wrap: break-word;
  display: inline-block;
  max-width: 100%;
}

.chat-message-group.own .message-text {
  background-color: #4361ee;
  color: white;
}

.message-time {
  font-size: 0.7rem;
  color: #999;
  margin-top: 2px;
  margin-left: 4px;
  text-align: left;
}

.chat-message-group.own .message-time {
  text-align: right;
  margin-right: 4px;
  margin-left: 0;
}

.loading-messages {
  text-align: center;
  color: #666;
  padding: 20px;
}

.empty-messages {
  text-align: center;
  color: #999;
  padding: 40px 20px;
  font-style: italic;
}

.chat-input-area {
  display: flex;
  padding: 15px;
  border-top: 1px solid #f0f0f0;
  background-color: #f9f9f9;
  border-radius: 0 0 12px 12px;
  gap: 10px;
}

.chat-input {
  flex: 1;
  padding: 10px 15px;
  border: 1px solid #e0e0e0;
  border-radius: 20px;
  font-size: 0.9rem;
  outline: none;
  transition: all 0.3s;
}

.chat-input:focus {
  border-color: #4361ee;
  box-shadow: 0 0 0 2px rgba(67, 97, 238, 0.1);
}

.chat-send-btn {
  padding: 10px 20px;
  background-color: #4361ee;
  color: white;
  border: none;
  border-radius: 20px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
  white-space: nowrap;
}

.chat-send-btn:hover {
  background-color: #3a0ca3;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(67, 97, 238, 0.3);
}

.chat-send-btn:active {
  transform: translateY(0);
}

/* Scrollbar styles */
.chat-messages::-webkit-scrollbar {
  width: 6px;
}

.chat-messages::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* Responsive */
@media (max-width: 576px) {
  .chat-modal-content {
    width: 90%;
    height: 80vh;
  }
}
</style>