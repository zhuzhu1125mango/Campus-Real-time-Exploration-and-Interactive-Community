<template>
  <div class="chat-detail">
    <div class="chat-header">
      <button class="back-btn" @click="goBack">
        <span class="back-icon"></span>
      </button>
      <div class="chat-user-info">
        <div class="chat-user-avatar" :style="{ backgroundImage: user?.avatar ? `url(${getAvatarUrl(user.avatar)})` : 'none' }">
          <span v-if="!user?.avatar">{{ getInitials(user?.username || '') }}</span>
        </div>
        <h3 class="chat-user-name">{{ user?.username }}</h3>
      </div>
      <div class="chat-actions">
        <div class="connection-status-indicator" :class="connectionStatus">
          <span class="status-dot"></span>
          <span class="status-text">{{ connectionStatusText }}</span>
        </div>
        <button class="more-btn">
          <span class="more-icon"></span>
        </button>
      </div>
    </div>
    
    <div class="chat-messages" ref="messagesContainer" @scroll="handleMessagesScroll">
      <div v-if="loading" class="loading-container">
        <div class="loading-spinner"></div>
        <p>加载中...</p>
      </div>

      <div v-else>
        <div v-if="isLoadingMore" class="loading-more">
          <div class="loading-spinner small"></div>
          <span>加载历史消息...</span>
        </div>

        <div v-if="messages.length === 0" class="empty-messages">
          <p>开始与 {{ user?.username }} 聊天吧！</p>
        </div>

        <div v-else class="messages-list">
        <div 
          v-for="message in messages" 
          :key="message.id" 
          :class="['message-item', message.sender.id === currentUserId ? 'sent' : 'received']"
        >
          <div
            class="message-avatar"
            @click="goToUserProfile(message.sender.id)"
            :style="{ backgroundImage: message.sender.avatar ? `url(${getAvatarUrl(message.sender.avatar)})` : 'none' }"
          >
            <span v-if="!message.sender.avatar">{{ getInitials(message.sender.username || '') }}</span>
          </div>
          <div class="message-content" :class="{ 'send-failed': message.sendFailed }">
            <p class="message-text">{{ message.content }}</p>
            <span v-if="message.sendFailed" class="send-failed-text">发送失败</span>
            <span class="message-time">{{ formatTime(message.created_at) }}</span>
          </div>
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
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useToast } from '../composables/useToast'
import { userApi } from '../api/user'
import { useUserStore } from '../stores/userStore'
import config from '../utils/config'
import { ElMessage } from 'element-plus'

const getAvatarUrl = (avatar?: string | null) => {
  if (!avatar) return `${config.media.baseUrl}${config.media.defaultAvatar}`
  if (avatar.startsWith('http')) return avatar
  return `${config.media.baseUrl}${avatar}`
}

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

// 分页状态
const currentPage = ref(1)
const hasMoreMessages = ref(false)
const isLoadingMore = ref(false)
const pageSize = 20

// WebSocket相关状态
const ws = ref<WebSocket | null>(null)
const connectionStatus = ref<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected')
const reconnectAttempts = ref(0)
const maxReconnectAttempts = 3
const reconnectTimeout = ref<number | null>(null)
const heartbeatInterval = ref<number | null>(null)
const lastError = ref('')
const reconnectDelay = 1000

// 获取WebSocket基础URL
const WS_BASE_URL = config.wsBaseUrl

// 获取当前用户ID
const currentUserId = computed(() => userStore.user?.id || 0)

// 获取用户ID参数（仅保留有效数字ID）
const userId = computed(() => {
  const id = route.params.id
  if (typeof id !== 'string' || !/^\d+$/.test(id)) return ''
  return id
})

// 连接状态文本
const connectionStatusText = computed(() => {
  switch (connectionStatus.value) {
    case 'connecting':
      return '连接中...'
    case 'connected':
      return '在线'
    case 'disconnected':
      return '已断开'
    case 'error':
      return '连接错误'
    default:
      return ''
  }
})

// 加载对话
const loadConversation = async (page = 1, isLoadMore = false) => {
  if (!userId.value) return

  if (isLoadMore) {
    isLoadingMore.value = true
  } else {
    loading.value = true
    currentPage.value = page
  }

  try {
    const response = await userApi.getConversation(Number(userId.value), page, pageSize)

    // 首次加载或重新加载时设置用户信息
    if (!isLoadMore) {
      user.value = response.user
    }

    const loadedMessages = response.messages || []

    if (isLoadMore) {
      // 记录加载前的滚动高度，便于加载后保持滚动位置
      const oldScrollHeight = messagesContainer.value?.scrollHeight || 0
      messages.value = [...loadedMessages, ...messages.value]
      hasMoreMessages.value = !!response.next

      await nextTick()
      const newScrollHeight = messagesContainer.value?.scrollHeight || 0
      if (messagesContainer.value) {
        messagesContainer.value.scrollTop = newScrollHeight - oldScrollHeight
      }
    } else {
      messages.value = loadedMessages
      hasMoreMessages.value = !!response.next

      // 滚动到底部
      await nextTick()
      scrollToBottom()
    }
  } catch (error) {
    console.error('加载对话失败:', error)
    showToast('加载对话失败', 'error')
  } finally {
    loading.value = false
    isLoadingMore.value = false
  }
}

// 加载更多历史消息
const loadMoreMessages = async () => {
  if (isLoadingMore.value || !hasMoreMessages.value || !userId.value) return
  await loadConversation(currentPage.value + 1, true)
  currentPage.value += 1
}

// 处理消息区域滚动事件
const handleMessagesScroll = () => {
  const container = messagesContainer.value
  if (!container) return

  // 滚动到顶部时加载更多历史消息
  if (container.scrollTop <= 10 && hasMoreMessages.value && !isLoadingMore.value) {
    loadMoreMessages()
  }
}

// 发送消息
const sendMessage = async () => {
  if (!messageInput.value.trim() || !userId.value) return

  const content = messageInput.value.trim()
  messageInput.value = ''

  // 生成临时消息ID，避免与服务器真实ID冲突
  const tempId = `temp_${Date.now()}`

  try {
    console.log(`[ChatDetail] 发送消息给用户 ${userId.value}: ${content}`)

    // 先添加到消息列表（乐观更新）
    const tempMessage = {
      id: tempId,
      sender: userStore.user,
      receiver: user.value,
      content,
      is_read: false,
      created_at: new Date().toISOString(),
      isTemp: true,
      sendFailed: false
    }
    messages.value.push(tempMessage)

    // 滚动到底部
    await nextTick()
    scrollToBottom()

    // 发送消息到后端
    const response = await userApi.sendMessage(Number(userId.value), { content })

    console.log('[ChatDetail] 消息发送成功:', response)

    // 用服务器返回的真实消息替换临时消息
    const index = messages.value.findIndex(msg => msg.id === tempId)
    if (index !== -1 && response) {
      messages.value[index] = {
        ...response,
        sender: response.sender || userStore.user,
        receiver: response.receiver || user.value,
        isTemp: false,
        sendFailed: false
      }
    }
  } catch (error) {
    console.error('[ChatDetail] 发送消息失败:', error)
    showToast('发送消息失败', 'error')

    // 标记临时消息为失败，保留内容以便重发
    const index = messages.value.findIndex(msg => msg.id === tempId)
    if (index !== -1) {
      messages.value[index] = { ...messages.value[index], sendFailed: true }
    }
  }
}

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

// WebSocket连接逻辑
const connectWebSocket = async () => {
  if (!userId.value || !userStore.isLoggedIn) {
    console.log('[ChatDetail] 无法建立WebSocket连接：用户未登录或缺少必要参数')
    return
  }

  // 在连接前确保 token 有效
  const validToken = await userStore.ensureValidToken()
  if (!validToken) {
    console.log('[ChatDetail] 无法获取有效 token，跳过 WebSocket 连接')
    connectionStatus.value = 'disconnected'
    lastError.value = '登录会话已过期，请重新登录'
    return
  }

  connectionStatus.value = 'connecting'
  console.log(`[ChatDetail] 开始连接私聊WebSocket，对方用户ID: ${userId.value}`)

  try {
    // 关闭现有连接
    if (ws.value && ws.value.readyState < 2) {
      console.log('[ChatDetail] 关闭现有WebSocket连接')
      ws.value.close()
    }

    // 构建WebSocket URL
    const wsUrl = `${WS_BASE_URL}/ws/chat/private/${userId.value}/`
    console.log('[ChatDetail] WebSocket连接URL:', wsUrl)

    // 通过 Sec-WebSocket-Protocol 子协议传递 token，避免 token 暴露在 URL 中
    const protocols = ['jwt', validToken]

    // 创建新连接
    ws.value = new WebSocket(wsUrl, protocols)

    ws.value.onopen = () => {
      console.log('[ChatDetail] 私聊WebSocket连接已成功打开')
      connectionStatus.value = 'connected'
      reconnectAttempts.value = 0
      lastError.value = ''

      // 启动心跳
      if (heartbeatInterval.value) {
        clearInterval(heartbeatInterval.value)
      }

      heartbeatInterval.value = window.setInterval(() => {
        if (ws.value && ws.value.readyState === 1) {
          ws.value.send(JSON.stringify({
            type: 'heartbeat',
            timestamp: Date.now()
          }))
        }
      }, 30000)
      
      // 连接成功后，重新加载对话确保消息同步
      loadConversation()
      
      // 显示连接成功提示
      ElMessage.success('WebSocket连接已建立')
    }

    ws.value.onmessage = (event) => {
      console.log('[ChatDetail] 收到私聊WebSocket消息:', event.data)
      try {
        const data = JSON.parse(event.data)

        if (data.type === 'private_message') {
          handlePrivateMessage(data)
        } else if (data.type === 'private_chat_ready') {
          console.log('[ChatDetail] 私聊频道就绪:', data.message)
        } else if (data.type === 'heartbeat_response') {
          console.log('[ChatDetail] 私聊心跳响应:', data.timestamp)
        } else if (data.type === 'message_received') {
          console.log('[ChatDetail] 消息发送确认:', data.message)
        } else if (data.type === 'error') {
          console.error('[ChatDetail] 私聊WebSocket错误:', data)
          lastError.value = data.message || '服务器发生错误'
        } else {
          console.log('[ChatDetail] 未知私聊消息类型:', data.type, data)
        }
      } catch (e) {
        console.error('[ChatDetail] 解析私聊WebSocket消息出错:', e)
        lastError.value = '解析消息出错'
      }
    }

    ws.value.onclose = (event) => {
      console.log(`[ChatDetail] 私聊WebSocket连接已关闭，代码: ${event.code}, 原因: ${event.reason}`)
      connectionStatus.value = 'disconnected'

      // 清理定时器
      if (heartbeatInterval.value) {
        clearInterval(heartbeatInterval.value)
        heartbeatInterval.value = null
      }

      // 认证失败(4001)、缺少参数(4002)或目标用户不存在(4004)时不盲目重连
      if ([4001, 4002, 4003, 4004].includes(event.code)) {
        if (event.code === 4001) {
          lastError.value = '登录会话已过期，请重新登录'
        } else if (event.code === 4003) {
          lastError.value = '双方不是好友，无法建立私聊'
        } else if (event.code === 4004) {
          lastError.value = '对方用户不存在'
        }
        return
      }

      // 尝试重连
      if (reconnectAttempts.value < maxReconnectAttempts && userStore.isLoggedIn) {
        reconnectAttempts.value++
        const delay = reconnectDelay * Math.pow(1.5, reconnectAttempts.value - 1)
        console.log(`[ChatDetail] 将在 ${delay}ms 后尝试重新连接，第 ${reconnectAttempts.value} 次`)

        // 显示重连提示
        if (reconnectAttempts.value === 1) {
          ElMessage.warning(`WebSocket连接断开，正在尝试重新连接... (第 ${reconnectAttempts.value} 次)`)
        }

        reconnectTimeout.value = window.setTimeout(() => {
          if (userStore.isLoggedIn && userId.value) {
            console.log('[ChatDetail] 执行重连...')
            connectWebSocket()
          }
        }, delay)
      } else {
        console.log('[ChatDetail] 达到最大重连次数或用户已登出，停止重连')
        if (userStore.isLoggedIn) {
          ElMessage.error('WebSocket连接断开，已达到最大重连次数')
        }
      }
    }

    ws.value.onerror = () => {
      // 连接细节已在 onclose 中记录，避免重复报错
      connectionStatus.value = 'error'
      lastError.value = '私聊连接发生错误，请稍后重试'

      // 尝试重连
      if (reconnectAttempts.value < maxReconnectAttempts) {
        reconnectAttempts.value++
        const delay = reconnectDelay * Math.pow(1.5, reconnectAttempts.value - 1)
        console.log(`[ChatDetail] 将在 ${delay}ms 后尝试重新连接，第 ${reconnectAttempts.value} 次`)

        reconnectTimeout.value = window.setTimeout(() => {
          if (userStore.isLoggedIn && userId.value) {
            connectWebSocket()
          }
        }, delay)
      }
    }
  } catch (e: Error | unknown) {
    console.error('[ChatDetail] 私聊WebSocket连接初始化错误:', e)
    connectionStatus.value = 'error'
    lastError.value = `连接初始化错误: ${e instanceof Error ? e.message : '未知错误'}`

    if (reconnectAttempts.value < maxReconnectAttempts) {
      reconnectAttempts.value++
      const delay = reconnectDelay * Math.pow(1.5, reconnectAttempts.value - 1)
      console.log(`[ChatDetail] 将在 ${delay}ms 后尝试重新连接，第 ${reconnectAttempts.value} 次`)

      reconnectTimeout.value = window.setTimeout(() => {
        if (userStore.isLoggedIn && userId.value) {
          connectWebSocket()
        }
      }, delay)
    }
  }
}

// 处理私聊消息
const handlePrivateMessage = (data: any) => {
  console.log('[ChatDetail] 处理私聊消息:', data)

  const senderId = Number(data.sender_id)
  const receiverId = Number(data.receiver_id)
  const currentId = Number(userId.value)

  // 只处理属于当前对话的消息（参与方必须包含当前用户和目标用户）
  const participants = [senderId, receiverId]
  if (!participants.includes(currentUserId.value) || !participants.includes(currentId)) {
    console.log('[ChatDetail] 消息不属于当前对话，忽略')
    return
  }

  const newMessage = {
    id: data.id || Date.now(),
    sender: {
      id: senderId,
      username: data.sender_username,
      avatar: data.sender_avatar
    },
    receiver: {
      id: receiverId,
      username: data.receiver_username
    },
    content: data.content,
    is_read: data.is_read || false,
    created_at: data.created_at || new Date().toISOString()
  }

  // 检查消息是否已存在（按ID）或是自己的临时消息
  const existingIndex = messages.value.findIndex(msg =>
    msg.id === newMessage.id ||
    (msg.isTemp && msg.sender?.id === newMessage.sender.id && msg.content === newMessage.content)
  )

  if (existingIndex !== -1) {
    const existing = messages.value[existingIndex]
    // 如果是临时消息，用真实消息替换
    if (existing.isTemp) {
      console.log('[ChatDetail] 用真实消息替换临时消息:', newMessage)
      messages.value[existingIndex] = newMessage
    } else {
      console.log('[ChatDetail] 消息已存在，跳过重复添加:', data)
    }
  } else {
    console.log('[ChatDetail] 添加新消息:', newMessage)
    messages.value.push(newMessage)
    scrollToBottom()
  }
}

// 关闭WebSocket连接
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

// 获取用户名首字母
const getInitials = (username: string) => {
  return username.charAt(0).toUpperCase()
}

// 格式化时间
const formatTime = (dateString: string) => {
  const date = new Date(dateString)
  return `${date.getHours()}:${String(date.getMinutes()).padStart(2, '0')}`
}

// 返回消息中心
const goBack = () => {
  router.push('/messages')
}

// 跳转到用户个人主页
const goToUserProfile = (userId: number) => {
  router.push(`/profile/${userId}`)
}

// 监听路由参数变化
watch(() => route.params.id, () => {
  loadConversation()
})

// 生命周期钩子
onMounted(() => {
  loadConversation()
  
  // 建立WebSocket连接
  if (userStore.isLoggedIn) {
    connectWebSocket()
  }
  
  // 监听登录状态变化
  const loginWatcher = watch(() => userStore.isLoggedIn, (newValue) => {
    if (newValue && userId.value) {
      connectWebSocket()
    } else {
      closeWebSocket()
    }
  })
  
  // 监听用户ID变化，重新连接WebSocket
  const userIdWatcher = watch(userId, () => {
    closeWebSocket()
    if (userStore.isLoggedIn && userId.value) {
      connectWebSocket()
    }
  })
  
  // 清理函数
  return () => {
    loginWatcher()
    userIdWatcher()
    closeWebSocket()
  }
})

// 组件卸载时清理WebSocket连接
onUnmounted(() => {
  closeWebSocket()
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

.loading-spinner.small {
  width: 16px;
  height: 16px;
  border-width: 2px;
  margin-bottom: 0;
  margin-right: 8px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-more {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 10px;
  color: #888;
  font-size: 0.85rem;
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

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: #4361ee;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  font-weight: 600;
  flex-shrink: 0;
  cursor: pointer;
  transition: all 0.3s;
  margin: 0 10px;
  background-size: cover;
  background-position: center;
}

.message-avatar:hover {
  transform: scale(1.1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
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

/* 连接状态指示器 */
.connection-status-indicator {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 11px;
}

.connection-status-indicator.connecting {
  background-color: #fff3cd;
}

.connection-status-indicator.connecting .status-dot {
  background-color: #ffc107;
}

.connection-status-indicator.connecting .status-text {
  color: #856404;
}

.connection-status-indicator.connected {
  background-color: #d4edda;
}

.connection-status-indicator.connected .status-dot {
  background-color: #28a745;
}

.connection-status-indicator.connected .status-text {
  color: #155724;
}

.connection-status-indicator.disconnected {
  background-color: #f8d7da;
}

.connection-status-indicator.disconnected .status-dot {
  background-color: #dc3545;
}

.connection-status-indicator.disconnected .status-text {
  color: #721c24;
}

.connection-status-indicator.error {
  background-color: #f8d7da;
}

.connection-status-indicator.error .status-dot {
  background-color: #dc3545;
}

.connection-status-indicator.error .status-text {
  color: #721c24;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-text {
  font-weight: 500;
}

.message-content.send-failed {
  background-color: #f8d7da !important;
  color: #721c24 !important;
  border: 1px solid #f5c6cb;
}

.send-failed-text {
  font-size: 0.75rem;
  color: #dc3545;
  display: block;
  margin-bottom: 4px;
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