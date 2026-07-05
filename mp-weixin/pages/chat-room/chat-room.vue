<template>
  <view class="container">
    <view class="header">
      <text class="back-icon" @click="goBack">&#60;</text>
      <text class="header-title">公共聊天室</text>
      <view class="header-meta">
        <text class="online-count">在线 {{ onlineCount }} 人</text>
        <text class="status-text" :class="connectionStatus">{{ connectionStatusText }}</text>
      </view>
    </view>

    <scroll-view class="message-list" scroll-y :scroll-top="scrollTop" :scroll-with-animation="true">
      <view class="loading-more" v-if="loading">
        <text>加载历史消息...</text>
      </view>

      <view class="empty-tip" v-else-if="messages.length === 0">
        <text>还没有消息，来说点什么吧！</text>
      </view>

      <view v-else>
        <view
          class="message-item"
          v-for="(msg, index) in messages"
          :key="msg.id || index"
          :class="[
            msg.type === 'system' ? 'system-message' : '',
            msg.user?.id === currentUserId ? 'message-mine' : ''
          ]"
        >
          <template v-if="msg.type === 'system'">
            <text class="system-text">{{ msg.content }}</text>
          </template>
          <template v-else>
            <image
              v-if="msg.user?.id !== currentUserId"
              class="msg-avatar"
              :src="formatAvatar(msg.user?.avatar)"
              mode="aspectFill"
            />
            <view class="message-content">
              <text class="msg-username" v-if="msg.user?.id !== currentUserId">{{ msg.user?.username }}</text>
              <text class="message-text">{{ msg.content }}</text>
              <text class="message-time">{{ formatDateTime(msg.time) }}</text>
            </view>
            <image
              v-if="msg.user?.id === currentUserId"
              class="msg-avatar"
              :src="formatAvatar(currentUserAvatar)"
              mode="aspectFill"
            />
          </template>
        </view>
      </view>
    </scroll-view>

    <view class="input-area">
      <input
        class="message-input"
        v-model="inputMessage"
        type="text"
        placeholder="输入消息..."
        confirm-type="send"
        :disabled="!connected"
        @confirm="sendMessage"
      />
      <button class="send-btn" :disabled="!inputMessage.trim() || !connected" @click="sendMessage">
        {{ sending ? '发送中' : '发送' }}
      </button>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import chatApi from '../../api/chat'
import { getWebSocketUrl } from '../../api/request'
import { formatAvatar } from '../../utils/image'
import { formatDateTime } from '../../utils/date'

const messages = ref([])
const inputMessage = ref('')
const onlineCount = ref(0)
const loading = ref(false)
const sending = ref(false)
const scrollTop = ref(0)
const connected = ref(false)
const connectionStatus = ref('disconnected')

const socketTask = ref(null)
const reconnectTimer = ref(null)
const heartbeatTimer = ref(null)

const currentUserId = ref(0)
const currentUserAvatar = ref('')

const connectionStatusText = computed(() => {
  const map = {
    connecting: '连接中',
    connected: '在线',
    disconnected: '已断开',
    error: '连接错误'
  }
  return map[connectionStatus.value] || ''
})

onMounted(() => {
  checkAuthAndLoad()
})

onUnmounted(() => {
  closeSocket()
  stopHeartbeat()
})

const checkAuthAndLoad = () => {
  const token = uni.getStorageSync('accessToken')
  if (!token) {
    uni.showToast({ title: '请先登录', icon: 'none' })
    setTimeout(() => {
      uni.navigateTo({ url: '/pages/login/login' })
    }, 1000)
    return
  }

  const storedUserInfo = uni.getStorageSync('userInfo')
  if (storedUserInfo) {
    try {
      const info = typeof storedUserInfo === 'string' ? JSON.parse(storedUserInfo) : storedUserInfo
      currentUserId.value = info.id || 0
      currentUserAvatar.value = info.avatar || ''
    } catch (e) {
      console.error('解析用户信息失败', e)
    }
  }

  loadHistory()
  loadOnlineCount()
  initWebSocket()
}

const loadHistory = async () => {
  loading.value = true
  try {
    const result = await chatApi.getRecentMessages()
    const list = (result || []).map((msg) => ({
      id: msg.id,
      content: msg.content,
      type: 'chat',
      user: {
        id: msg.user?.id || 0,
        username: msg.user?.username || '未知用户',
        avatar: msg.user?.avatar
      },
      time: msg.created_at
    }))
    messages.value = list.reverse()
    scrollToBottom()
  } catch (error) {
    console.error('加载历史消息失败:', error)
    uni.showToast({ title: '加载历史消息失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

const loadOnlineCount = async () => {
  try {
    const result = await chatApi.getOnlineUsers()
    onlineCount.value = result?.count || 0
  } catch (error) {
    console.error('加载在线人数失败:', error)
  }
}

const initWebSocket = () => {
  if (socketTask.value) return

  connectionStatus.value = 'connecting'
  const url = getWebSocketUrl('public')
  socketTask.value = uni.connectSocket({
    url,
    success: () => {
      console.log('公共聊天室 WebSocket 连接请求已发送')
    }
  })

  socketTask.value.onOpen(() => {
    console.log('公共聊天室 WebSocket 连接已打开')
    connectionStatus.value = 'connected'
    connected.value = true
    startHeartbeat()
  })

  socketTask.value.onMessage((res) => {
    try {
      const data = JSON.parse(res.data)
      handleSocketMessage(data)
    } catch (error) {
      console.error('解析公共聊天室消息失败:', error)
    }
  })

  socketTask.value.onClose((event) => {
    console.log('公共聊天室 WebSocket 连接已关闭', event)
    socketTask.value = null
    connected.value = false
    connectionStatus.value = 'disconnected'
    stopHeartbeat()

    if (event?.code === 4001) {
      uni.showToast({ title: '登录已过期，请重新登录', icon: 'none' })
      setTimeout(() => {
        uni.navigateTo({ url: '/pages/login/login' })
      }, 1000)
      return
    }

    reconnectTimer.value = setTimeout(() => {
      initWebSocket()
    }, 5000)
  })

  socketTask.value.onError((error) => {
    console.error('公共聊天室 WebSocket 错误:', error)
    connectionStatus.value = 'error'
  })
}

const handleSocketMessage = (data) => {
  if (data.type === 'chat_message') {
    messages.value.push({
      id: `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
      content: data.message,
      type: 'chat',
      user: {
        id: data.user_id || 0,
        username: data.username || '未知用户',
        avatar: data.avatar
      },
      time: data.time || new Date().toISOString()
    })
    scrollToBottom()
  } else if (data.type === 'online_users') {
    onlineCount.value = data.count || 0
  } else if (data.type === 'welcome') {
    onlineCount.value = data.online_users?.count || 0
  } else if (data.type === 'heartbeat_response') {
    // 忽略
  } else if (data.type === 'error') {
    uni.showToast({ title: data.message || '服务器错误', icon: 'none' })
  }
}

const startHeartbeat = () => {
  stopHeartbeat()
  heartbeatTimer.value = setInterval(() => {
    if (socketTask.value) {
      socketTask.value.send({
        data: JSON.stringify({ type: 'heartbeat', timestamp: Date.now() })
      })
    }
  }, 30000)
}

const stopHeartbeat = () => {
  if (heartbeatTimer.value) {
    clearInterval(heartbeatTimer.value)
    heartbeatTimer.value = null
  }
}

const closeSocket = () => {
  if (reconnectTimer.value) {
    clearTimeout(reconnectTimer.value)
    reconnectTimer.value = null
  }
  if (socketTask.value) {
    socketTask.value.close()
    socketTask.value = null
  }
}

const sendMessage = () => {
  const content = inputMessage.value.trim()
  if (!content || sending.value || !connected.value) return

  sending.value = true
  const clientId = Date.now()
  const tempMsg = {
    id: `temp-${clientId}`,
    content,
    type: 'chat',
    user: {
      id: currentUserId.value,
      username: '我',
      avatar: currentUserAvatar.value
    },
    time: new Date().toISOString()
  }
  messages.value.push(tempMsg)
  inputMessage.value = ''
  scrollToBottom()

  if (socketTask.value) {
    socketTask.value.send({
      data: JSON.stringify({
        type: 'chat_message',
        message: content,
        client_id: clientId
      })
    })
  }

  sending.value = false
}

const scrollToBottom = () => {
  nextTick(() => {
    scrollTop.value = 999999 + Date.now()
  })
}

const goBack = () => {
  uni.navigateBack()
}
</script>

<style scoped>
.container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #f5f5f5;
}

.header {
  display: flex;
  align-items: center;
  padding: 20rpx 30rpx;
  background-color: #fff;
  border-bottom: 1rpx solid #f0f0f0;
}

.back-icon {
  font-size: 36rpx;
  color: #666;
  margin-right: 20rpx;
  padding: 10rpx;
}

.header-title {
  flex: 1;
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
}

.header-meta {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.online-count {
  font-size: 24rpx;
  color: #666;
}

.status-text {
  font-size: 22rpx;
  padding: 4rpx 12rpx;
  border-radius: 12rpx;
}

.status-text.connecting {
  background: #fff7e6;
  color: #fa8c16;
}

.status-text.connected {
  background: #f6ffed;
  color: #52c41a;
}

.status-text.disconnected,
.status-text.error {
  background: #fff1f0;
  color: #f5222d;
}

.message-list {
  flex: 1;
  padding: 20rpx;
  overflow-y: auto;
}

.loading-more,
.empty-tip {
  text-align: center;
  padding: 40rpx;
  color: #999;
  font-size: 28rpx;
}

.message-item {
  display: flex;
  align-items: flex-start;
  margin-bottom: 30rpx;
}

.message-mine {
  flex-direction: row-reverse;
}

.system-message {
  justify-content: center;
}

.system-text {
  padding: 8rpx 20rpx;
  background: #e0e0e0;
  color: #666;
  border-radius: 20rpx;
  font-size: 24rpx;
}

.msg-avatar {
  width: 72rpx;
  height: 72rpx;
  border-radius: 50%;
  background-color: #eee;
  flex-shrink: 0;
}

.message-content {
  max-width: 70%;
  margin: 0 20rpx;
  padding: 16rpx 20rpx;
  border-radius: 16rpx;
  background-color: #fff;
  display: flex;
  flex-direction: column;
}

.message-mine .message-content {
  background-color: #4CAF50;
}

.msg-username {
  font-size: 24rpx;
  color: #999;
  margin-bottom: 8rpx;
}

.message-text {
  font-size: 30rpx;
  color: #333;
  line-height: 1.5;
  word-break: break-word;
}

.message-mine .message-text {
  color: #fff;
}

.message-time {
  font-size: 22rpx;
  color: #999;
  margin-top: 8rpx;
  align-self: flex-end;
}

.message-mine .message-time {
  color: rgba(255, 255, 255, 0.7);
}

.input-area {
  display: flex;
  align-items: center;
  padding: 20rpx;
  background-color: #fff;
  border-top: 1rpx solid #f0f0f0;
}

.message-input {
  flex: 1;
  height: 72rpx;
  padding: 0 24rpx;
  background-color: #f5f5f5;
  border-radius: 36rpx;
  font-size: 28rpx;
  margin-right: 16rpx;
}

.send-btn {
  width: 120rpx;
  height: 72rpx;
  line-height: 72rpx;
  background-color: #4CAF50;
  color: #fff;
  border-radius: 36rpx;
  font-size: 28rpx;
  padding: 0;
}

.send-btn[disabled] {
  background-color: #bfbfbf;
}
</style>
