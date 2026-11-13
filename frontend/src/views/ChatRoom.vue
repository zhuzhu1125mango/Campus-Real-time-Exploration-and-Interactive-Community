<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/userStore'
import { useTokenStore } from '../stores/tokenStore'
import GlassCard from '@/components/GlassCard.vue'
import SectionHeader from '@/components/SectionHeader.vue'
import config from '../utils/config'
import { formatAvatar } from '../utils/image'
import { messageStorage } from '../utils/messageStorage'
import { chatApi } from '../api/chat'
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
const tokenStore = useTokenStore()

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

const getInitials = (name?: string) => {
  if (!name) return '?'
  return name.slice(0, 2).toUpperCase()
}

const formatTime = (time: string) => {
  return new Date(time).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

const formatDate = (time: string) => {
  const date = new Date(time)
  const today = new Date()
  const yesterday = new Date(today)
  yesterday.setDate(yesterday.getDate() - 1)

  const isSameDay = (a: Date, b: Date) =>
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()

  if (isSameDay(date, today)) return '今天'
  if (isSameDay(date, yesterday)) return '昨天'
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

const groupedMessages = computed(() => {
  const groups: { date: string; messages: ChatMessageItem[] }[] = []
  let currentDate = ''

  messages.value.forEach(msg => {
    if (msg.type === 'system') {
      groups.push({ date: '', messages: [msg] })
      return
    }
    const date = formatDate(msg.time)
    if (date !== currentDate) {
      currentDate = date
      groups.push({ date, messages: [msg] })
    } else {
      groups[groups.length - 1].messages.push(msg)
    }
  })

  return groups
})

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
    const data = await chatApi.getRecentMessages()
    const history = (data || []).map((msg: any) => ({
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
    const data = await chatApi.getOnlineUsers()
    onlineCount.value = data?.count || 0
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

  const token = tokenStore.accessToken
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

const handleInputKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Enter' && !e.shiftKey && !e.ctrlKey) {
    e.preventDefault()
    sendMessage()
  }
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
  <div class="chat-room-page container-wide page-padding">
    <SectionHeader
      title="公共聊天室"
      :subtitle="`${onlineCount} 人在线`"
      icon="i-ep-chat-dot-round"
    />

    <div class="connection-status-bar">
      <span class="connection-status-dot" :class="connectionStatus" />
      <span class="connection-status-text" :class="connectionStatus">{{ connectionStatusText }}</span>
    </div>

    <GlassCard :hover="false" class="messages-card" padding="none">
      <div class="chat-messages" ref="messagesContainer">
        <div v-if="loading" class="loading-container">
          <div class="loading-spinner"></div>
          <p>加载历史消息中...</p>
        </div>

        <div v-else-if="messages.length === 0" class="empty-state">
          <div class="empty-icon">
            <span class="i-ep-chat-line-round" />
          </div>
          <p>还没有消息，来说点什么吧！</p>
        </div>

        <div v-else class="messages-list">
          <template v-for="(group, groupIndex) in groupedMessages" :key="groupIndex">
            <div v-if="group.date" class="date-divider">
              <span>{{ group.date }}</span>
            </div>
            <div
              v-for="message in group.messages"
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
                  :style="{ backgroundImage: message.user.avatar ? `url(${formatAvatar(message.user.avatar)})` : 'none' }"
                >
                  <span v-if="!message.user.avatar">{{ getInitials(message.user.username) }}</span>
                </div>
                <div class="message-body">
                  <div class="message-info">
                    <span class="message-username">{{ message.user.username }}</span>
                    <span class="message-time">{{ formatTime(message.time) }}</span>
                  </div>
                  <div class="message-content" :class="{ 'send-failed': message.sendFailed }">
                    <p>{{ message.content }}</p>
                    <span v-if="message.isTemp && !message.sendFailed" class="sending-hint">发送中...</span>
                    <span v-if="message.sendFailed" class="failed-hint">发送失败</span>
                  </div>
                </div>
              </template>
            </div>
          </template>
        </div>
      </div>
    </GlassCard>

    <div v-if="!connected && !loading" class="reconnect-bar">
      <span class="i-ep-warning reconnect-icon" />
      <span>连接已断开，消息可能无法实时同步</span>
      <button class="btn btn-secondary reconnect-btn" @click="connectWebSocket">重新连接</button>
    </div>

    <GlassCard :hover="false" class="input-card" padding="md">
      <div class="chat-input-area">
        <textarea
          v-model="messageInput"
          placeholder="输入消息，Enter 发送，Shift+Enter 换行..."
          class="message-input"
          rows="1"
          :disabled="!connected"
          @keydown="handleInputKeydown"
        ></textarea>
        <button
          class="btn btn-primary send-btn"
          @click="sendMessage"
          :disabled="!messageInput.trim() || !connected"
        >
          发送
        </button>
      </div>
    </GlassCard>
  </div>
</template>

<style scoped>
.chat-room-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 120px);
  min-height: 480px;
}

.messages-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  margin-bottom: var(--space-4);
}

.input-card {
  flex-shrink: 0;
}

.connection-status-bar {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--space-2);
  margin-bottom: var(--space-3);
  font-size: 0.875rem;
}

.connection-status-dot {
  width: 8px;
  height: 8px;
  border-radius: var(--radius-full);
  background: var(--text-tertiary);
}

.connection-status-text {
  color: var(--text-secondary);
}

.connection-status-dot.connecting,
.connection-status-text.connecting {
  background: var(--warning-color);
  color: var(--warning-color);
}

.connection-status-dot.connected,
.connection-status-text.connected {
  background: var(--success-color);
  color: var(--success-color);
}

.connection-status-dot.disconnected,
.connection-status-text.disconnected,
.connection-status-dot.error,
.connection-status-text.error {
  background: var(--error-color);
  color: var(--error-color);
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-4) var(--space-5);
}

.loading-container,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-tertiary);
}

.empty-icon {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: var(--primary-50);
  color: var(--primary-500);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: var(--space-4);
}

.empty-icon span {
  width: 32px;
  height: 32px;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--border-color);
  border-top-color: var(--primary-500);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: var(--space-3);
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.messages-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.date-divider {
  display: flex;
  align-items: center;
  justify-content: center;
  margin: var(--space-2) 0;
}

.date-divider span {
  padding: 4px 12px;
  background: var(--bg-tertiary);
  color: var(--text-tertiary);
  border-radius: var(--radius-full);
  font-size: 12px;
}

.dark .date-divider span {
  background: var(--bg-secondary);
}

.message-item {
  display: flex;
  gap: var(--space-3);
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
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  border-radius: var(--radius-full);
  font-size: 12px;
}

.dark .system-text {
  background: var(--bg-secondary);
}

.message-avatar {
  width: 40px;
  height: 40px;
  min-width: 40px;
  border-radius: 50%;
  background: var(--primary-500);
  color: var(--text-inverse);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  background-size: cover;
  background-position: center;
  box-shadow: var(--shadow-sm);
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
  gap: var(--space-2);
  font-size: 12px;
}

.message-username {
  color: var(--text-secondary);
  font-weight: 500;
}

.message-time {
  color: var(--text-tertiary);
}

.message-content {
  padding: 10px 14px;
  border-radius: var(--radius-xl);
  background: var(--bg-primary);
  color: var(--text-primary);
  word-break: break-word;
  box-shadow: var(--shadow-sm);
  max-width: 100%;
  border: 1px solid var(--border-color-light);
}

.self-message .message-content {
  background: var(--primary-500);
  color: var(--text-inverse);
  border-color: transparent;
  border-bottom-right-radius: var(--radius-sm);
  box-shadow: var(--shadow-md);
}

.other-message .message-content {
  border-bottom-left-radius: var(--radius-sm);
}

.message-content p {
  margin: 0;
  line-height: 1.5;
  white-space: pre-wrap;
}

.sending-hint,
.failed-hint {
  display: block;
  font-size: 11px;
  margin-top: 4px;
  opacity: 0.8;
}

.failed-hint {
  color: var(--error-color);
}

.self-message .failed-hint {
  color: #ffccc7;
}

.message-content.send-failed {
  background: var(--error-bg);
  color: var(--error-color);
  border-color: var(--error-color);
}

.reconnect-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  padding: var(--space-3);
  margin-bottom: var(--space-4);
  background: var(--warning-bg);
  color: var(--warning-color);
  font-size: 13px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--warning-color);
  opacity: 0.9;
}

.reconnect-icon {
  width: 18px;
  height: 18px;
}

.reconnect-btn {
  font-size: 12px;
  padding: var(--space-1) var(--space-3);
}

.chat-input-area {
  display: flex;
  gap: var(--space-3);
  align-items: flex-end;
}

.message-input {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-xl);
  background: var(--bg-primary);
  color: var(--text-primary);
  outline: none;
  font-size: 14px;
  resize: none;
  min-height: 42px;
  max-height: 120px;
  line-height: 1.5;
  font-family: inherit;
}

.message-input:focus {
  border-color: var(--primary-500);
  box-shadow: 0 0 0 3px var(--primary-50);
}

.message-input:disabled {
  background: var(--bg-tertiary);
  color: var(--text-tertiary);
}

/* 按钮样式 */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-5);
  border-radius: var(--radius-lg);
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: all 0.2s ease;
}

.btn-primary {
  background-color: var(--primary-600);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: var(--primary-700);
}

.btn-secondary {
  background-color: var(--bg-tertiary);
  color: var(--text-primary);
}

.btn-secondary:hover:not(:disabled) {
  background-color: var(--border-color-light);
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.send-btn {
  padding: var(--space-3) var(--space-6);
}

@media (max-width: 640px) {
  .chat-room-page {
    height: calc(100vh - 100px);
    min-height: auto;
  }

  .messages-card {
    margin-bottom: var(--space-3);
  }

  .chat-messages {
    padding: var(--space-3);
  }

  .message-item {
    max-width: 90%;
  }

  .message-avatar {
    width: 36px;
    height: 36px;
    min-width: 36px;
    font-size: 12px;
  }

  .chat-input-area {
    gap: var(--space-2);
  }

  .send-btn {
    padding: var(--space-2) var(--space-4);
  }

  .reconnect-bar {
    flex-wrap: wrap;
    text-align: center;
    font-size: 12px;
  }
}
</style>
