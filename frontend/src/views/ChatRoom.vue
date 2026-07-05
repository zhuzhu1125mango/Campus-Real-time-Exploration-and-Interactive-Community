<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { useUserStore } from '../stores/userStore'
import config from '../utils/config'
import { messageStorage } from '../utils/messageStorage'
import { ElMessage } from 'element-plus'

interface ChatUser {
  id: number
  username: string
  avatar?: string | null
}

interface ChatMessageItem {
  id: number | string
  content: string
  type: 'chat' | 'system'
  user: ChatUser
  time: string
  isTemp?: boolean
  sendFailed?: boolean
}

const router = useRouter()
const userStore = useUserStore()

// 状态
const messages = ref<ChatMessageItem[]>([])
const messageInput = ref('')
const onlineCount = ref(0)
const loading = ref(false)
const connected = ref(false)
const connectionStatus = ref<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected')
const messagesContainer = ref<HTMLElement | null>(null)

// WebSocket
const ws = ref<WebSocket | null>(null)
const heartbeatInterval = ref<number | null>(null)
const reconnectTimeout = ref<number | null>(null)
const reconnectAttempts = ref(0)
const maxReconnectAttempts = 3
const reconnectDelay = 1000

const currentUserId = computed(() => userStore.user?.id || 0)
const currentUsername = computed(() => userStore.user?.username || '')

const connectionStatusText = computed(() => {
  switch (connectionStatus.value) {
    case 'connecting': return '连接中...'
    case 'connected': return '在线'
    case 'disconnected': return '已断开'
    case 'error': return '连接错误'
    default: return ''
  }
})

const getAvatarUrl = (avatar?: string | null) => {
  if (!avatar) return `${config.media.baseUrl}${config.media.defaultAvatar}`
  if (avatar.startsWith('http')) return avatar
  return `${config.media.baseUrl}${avatar}`
}

const getInitials = (name?: string) => {
  if (!name) return '?'
  return name.slice(0, 2).toUpperCase()
}

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

// 从历史记录加载消息
const loadHistoryMessages = async () => {
  loading.value = true
  try {
    const response = await axios.get('/api/chat/messages/recent_messages/')
    const history = (response.data || []).map((msg: any) => ({
      id: msg.id,
      content: msg.content,
      type: 'chat' as const,
      user: {
        id: msg.user?.id || 0,
        username: msg.user?.username || '未知用户',
        avatar: msg.user?.avatar
      },
      time: msg.created_at
    }))
    messages.value = history.reverse()
    scrollToBottom()
  } catch (error) {
    console.error('加载历史消息失败:', error)
    ElMessage.warning('加载历史消息失败')
  } finally {
    loading.value = false
  }
}

// 加载在线人数
const loadOnlineCount = async () => {
  try {
    const response = await axios.get('/api/chat/messages/online_users/')
    onlineCount.value = response.data?.count || 0
  } catch (error) {
    console.error('加载在线人数失败:', error)
  }
}

// 统一消息格式
const normalizeMessage = (data: any): ChatMessageItem | null => {
  if (data.type === 'chat_message') {
    return {
      id: `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
      content: data.message,
      type: 'chat',
      user: {
        id: data.user_id || 0,
        username: data.username || '未知用户',
        avatar: data.avatar
      },
      time: data.time || new Date().toISOString()
    }
  }
  if (data.type === 'system') {
    return {
      id: `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
      content: data.message,
      type: 'system',
      user: { id: 0, username: '系统', avatar: null },
      time: data.time || new Date().toISOString()
    }
  }
  return null
}

// WebSocket 连接
const connectWebSocket = async () => {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录后进入聊天室')
    router.push('/login')
    return
  }

  const token = localStorage.getItem(config.jwt.accessTokenKey)
  if (!token) {
    ElMessage.warning('登录会话已过期，请重新登录')
    router.push('/login')
    return
  }

  if (ws.value && ws.value.readyState < 2) {
    ws.value.close()
  }

  connectionStatus.value = 'connecting'
  const wsUrl = `${config.wsBaseUrl}/ws/chat/public/`

  try {
    ws.value = new WebSocket(wsUrl, ['jwt', token])

    ws.value.onopen = () => {
      connectionStatus.value = 'connected'
      connected.value = true
      reconnectAttempts.value = 0

      if (heartbeatInterval.value) {
        clearInterval(heartbeatInterval.value)
      }
      heartbeatInterval.value = window.setInterval(() => {
        if (ws.value && ws.value.readyState === 1) {
          ws.value.send(JSON.stringify({ type: 'heartbeat', timestamp: Date.now() }))
        }
      }, 30000)
    }

    ws.value.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)

        if (data.type === 'chat_message') {
          const msg = normalizeMessage(data)
          if (msg) {
            messages.value.push(msg)
            scrollToBottom()
            saveMessagesToStorage()
          }
        } else if (data.type === 'online_users') {
          onlineCount.value = data.count || 0
        } else if (data.type === 'welcome') {
          onlineCount.value = data.online_users?.count || 0
        } else if (data.type === 'heartbeat_response') {
          // 忽略心跳响应
        } else if (data.type === 'error') {
          ElMessage.error(data.message || '服务器错误')
        }
      } catch (e) {
        console.error('解析WebSocket消息出错:', e)
      }
    }

    ws.value.onclose = (event) => {
      connectionStatus.value = 'disconnected'
      connected.value = false
      if (heartbeatInterval.value) {
        clearInterval(heartbeatInterval.value)
        heartbeatInterval.value = null
      }

      // 认证失败不自动重连
      if (event.code === 4001) {
        ElMessage.error('登录会话已过期，请重新登录')
        router.push('/login')
        return
      }

      if (reconnectAttempts.value < maxReconnectAttempts && userStore.isLoggedIn) {
        reconnectAttempts.value++
        const delay = reconnectDelay * Math.pow(1.5, reconnectAttempts.value - 1)
        reconnectTimeout.value = window.setTimeout(() => {
          connectWebSocket()
        }, delay)
      }
    }

    ws.value.onerror = () => {
      connectionStatus.value = 'error'
    }
  } catch (e) {
    console.error('WebSocket连接初始化错误:', e)
    connectionStatus.value = 'error'
  }
}

// 发送消息
const sendMessage = () => {
  if (!messageInput.value.trim()) return
  if (!connected.value || !ws.value || ws.value.readyState !== 1) {
    ElMessage.warning('聊天室未连接，请稍后再试')
    return
  }

  const content = messageInput.value.trim()
  const clientId = Date.now()

  // 乐观显示
  const tempMessage: ChatMessageItem = {
    id: `temp_${clientId}`,
    content,
    type: 'chat',
    user: {
      id: currentUserId.value,
      username: currentUsername.value,
      avatar: userStore.user?.avatar
    },
    time: new Date().toISOString(),
    isTemp: true
  }
  messages.value.push(tempMessage)
  scrollToBottom()

  ws.value.send(JSON.stringify({
    type: 'chat_message',
    message: content,
    client_id: clientId
  }))

  messageInput.value = ''
  saveMessagesToStorage()
}

// 本地存储
const saveMessagesToStorage = () => {
  messageStorage.saveChatMessages(messages.value.slice(-100))
}

const loadMessagesFromStorage = () => {
  const cached = messageStorage.getChatMessages()
  if (cached && cached.length > 0) {
    messages.value = cached
  }
}

// 关闭连接
const closeWebSocket = () => {
  if (ws.value) {
    ws.value.close()
    ws.value = null
  }
  if (heartbeatInterval.value) {
    clearInterval(heartbeatInterval.value)
    heartbeatInterval.value = null
  }
  if (reconnectTimeout.value) {
    clearTimeout(reconnectTimeout.value)
    reconnectTimeout.value = null
  }
}

onMounted(async () => {
  if (!userStore.isLoggedIn) {
    router.push('/login')
    return
  }
  loadMessagesFromStorage()
  await loadHistoryMessages()
  await loadOnlineCount()
  connectWebSocket()
})

onUnmounted(() => {
  closeWebSocket()
  saveMessagesToStorage()
})
</script>

<template>
  <div class="chat-room">
    <div class="chat-header">
      <h2 class="chat-title">公共聊天室</h2>
      <div class="header-meta">
        <span class="online-count">在线: {{ onlineCount }} 人</span>
        <span class="connection-status" :class="connectionStatus">{{ connectionStatusText }}</span>
      </div>
    </div>

    <div class="chat-messages" ref="messagesContainer">
      <div v-if="loading" class="loading-container">
        <div class="loading-spinner"></div>
        <p>加载历史消息中...</p>
      </div>

      <div v-else-if="messages.length === 0" class="empty-state">
        <p>还没有消息，来说点什么吧！</p>
      </div>

      <div v-else class="messages-list">
        <div
          v-for="message in messages"
          :key="message.id"
          :class="[
            'message-item',
            message.type === 'system' ? 'system-message' : '',
            message.user.id === currentUserId ? 'self-message' : 'other-message'
          ]"
        >
          <template v-if="message.type === 'system'">
            <span class="system-text">{{ message.content }}</span>
          </template>
          <template v-else>
            <div
              class="message-avatar"
              :style="{ backgroundImage: message.user.avatar ? `url(${getAvatarUrl(message.user.avatar)})` : 'none' }"
            >
              <span v-if="!message.user.avatar">{{ getInitials(message.user.username) }}</span>
            </div>
            <div class="message-body">
              <div class="message-info">
                <span class="message-username">{{ message.user.username }}</span>
                <span class="message-time">{{ new Date(message.time).toLocaleTimeString() }}</span>
              </div>
              <div class="message-content" :class="{ 'send-failed': message.sendFailed }">
                <p>{{ message.content }}</p>
                <span v-if="message.isTemp && !message.sendFailed" class="sending-hint">发送中...</span>
                <span v-if="message.sendFailed" class="failed-hint">发送失败</span>
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>

    <div class="chat-input-area">
      <input
        type="text"
        v-model="messageInput"
        placeholder="输入消息，按回车发送..."
        class="message-input"
        @keyup.enter="sendMessage"
        :disabled="!connected"
      />
      <button class="send-btn" @click="sendMessage" :disabled="!messageInput.trim() || !connected">
        发送
      </button>
    </div>
  </div>
</template>

<style scoped>
.chat-room {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 120px);
  max-width: 900px;
  margin: 0 auto;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e8e8e8;
  background: #fafafa;
}

.chat-title {
  margin: 0;
  font-size: 18px;
  color: #333;
}

.header-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 14px;
}

.online-count {
  color: #666;
}

.connection-status {
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
}

.connection-status.connecting {
  background: #fff7e6;
  color: #fa8c16;
}

.connection-status.connected {
  background: #f6ffed;
  color: #52c41a;
}

.connection-status.disconnected,
.connection-status.error {
  background: #fff1f0;
  color: #f5222d;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
  background: #f5f5f5;
}

.loading-container,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #999;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e8e8e8;
  border-top-color: #1890ff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 12px;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.messages-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.message-item {
  display: flex;
  gap: 12px;
  max-width: 80%;
}

.message-item.self-message {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message-item.other-message {
  align-self: flex-start;
}

.message-item.system-message {
  align-self: center;
  max-width: 100%;
}

.system-text {
  padding: 4px 12px;
  background: #e8e8e8;
  color: #666;
  border-radius: 12px;
  font-size: 12px;
}

.message-avatar {
  width: 40px;
  height: 40px;
  min-width: 40px;
  border-radius: 50%;
  background: #1890ff;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  background-size: cover;
  background-position: center;
}

.message-body {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.self-message .message-body {
  align-items: flex-end;
}

.message-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.message-username {
  color: #666;
}

.message-time {
  color: #999;
}

.message-content {
  padding: 10px 14px;
  border-radius: 12px;
  background: #fff;
  color: #333;
  word-break: break-word;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.self-message .message-content {
  background: #1890ff;
  color: #fff;
}

.self-message .message-content .message-time,
.self-message .message-username {
  color: rgba(255, 255, 255, 0.85);
}

.message-content p {
  margin: 0;
  line-height: 1.5;
}

.sending-hint,
.failed-hint {
  display: block;
  font-size: 11px;
  margin-top: 4px;
  opacity: 0.8;
}

.failed-hint {
  color: #ff4d4f;
}

.chat-input-area {
  display: flex;
  gap: 12px;
  padding: 12px 20px;
  border-top: 1px solid #e8e8e8;
  background: #fff;
}

.message-input {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid #d9d9d9;
  border-radius: 20px;
  outline: none;
  font-size: 14px;
}

.message-input:focus {
  border-color: #1890ff;
}

.message-input:disabled {
  background: #f5f5f5;
  color: #999;
}

.send-btn {
  padding: 0 24px;
  border: none;
  border-radius: 20px;
  background: #1890ff;
  color: #fff;
  font-size: 14px;
  cursor: pointer;
}

.send-btn:hover:not(:disabled) {
  background: #40a9ff;
}

.send-btn:disabled {
  background: #bfbfbf;
  cursor: not-allowed;
}
</style>
