<template>
  <view class="container">
    <view class="header" :style="headerStyle">
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
        <view class="empty-icon">💬</view>
        <text>还没有消息，来说点什么吧！</text>
      </view>

      <view v-else class="messages-list">
        <template v-for="(group, groupIndex) in groupedMessages" :key="groupIndex">
          <view v-if="group.date" class="date-divider">
            <text>{{ group.date }}</text>
          </view>
          <view
            class="message-item"
            v-for="(msg, index) in group.messages"
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
                <view class="message-meta">
                  <text v-if="msg.isTemp && !msg.sendFailed" class="status-hint sending">发送中...</text>
                  <text v-if="msg.sendFailed" class="status-hint failed" @click="resendMessage(msg)">发送失败，点击重试</text>
                  <text class="message-time">{{ formatDateTime(msg.time) }}</text>
                </view>
              </view>
              <image
                v-if="msg.user?.id === currentUserId"
                class="msg-avatar"
                :src="formatAvatar(currentUserAvatar)"
                mode="aspectFill"
              />
            </template>
          </view>
        </template>
      </view>
    </scroll-view>

    <view v-if="!connected && !loading" class="reconnect-bar">
      <text class="reconnect-text">⚠ 连接已断开，消息可能无法实时同步</text>
      <text class="reconnect-btn" @click="initWebSocket">重新连接</text>
    </view>

    <view class="input-area safe-area-bottom">
      <input
        class="message-input"
        v-model="inputMessage"
        type="text"
        placeholder="输入消息..."
        confirm-type="send"
        :disabled="!connected"
        @confirm="sendMessage"
      />
      <button class="send-btn" :disabled="!inputMessage.trim() || !connected || sending" @click="sendMessage">
        {{ sending ? '发送中' : '发送' }}
      </button>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import { onLoad, onUnload } from '@dcloudio/uni-app'
import chatApi from '../../api/chat'
import { getWebSocketUrl, getWebSocketProtocols } from '../../api/request'
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
const ackTimers = ref(new Set())
const reconnectAttempts = ref(0)
const maxReconnectAttempts = 5
const reconnectDelay = 1000

const currentUserId = ref(0)
const currentUserAvatar = ref('')
const statusBarHeight = ref(0)

const headerStyle = computed(() => {
  return {
    paddingTop: `${statusBarHeight.value + 20}rpx`
  }
})

const connectionStatusText = computed(() => {
  const map = {
    connecting: '连接中',
    connected: '在线',
    disconnected: '已断开',
    error: '连接错误'
  }
  return map[connectionStatus.value] || ''
})

const formatDate = (time) => {
  if (!time) return ''
  const date = new Date(time)
  if (isNaN(date.getTime())) return ''
  const today = new Date()
  const yesterday = new Date(today)
  yesterday.setDate(yesterday.getDate() - 1)

  const isSameDay = (a, b) =>
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()

  if (isSameDay(date, today)) return '今天'
  if (isSameDay(date, yesterday)) return '昨天'
  return `${date.getMonth() + 1}月${date.getDate()}日`
}

const groupedMessages = computed(() => {
  const groups = []
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

onLoad(() => {
  const info = uni.getSystemInfoSync()
  statusBarHeight.value = info.statusBarHeight
  checkAuthAndLoad()
})

onUnload(() => {
  closeSocket()
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
  const protocols = getWebSocketProtocols()

  socketTask.value = uni.connectSocket({
    url,
    protocols,
    success: () => {
      console.log('公共聊天室 WebSocket 连接请求已发送')
    }
  })

  socketTask.value.onOpen(() => {
    console.log('公共聊天室 WebSocket 连接已打开')
    connectionStatus.value = 'connected'
    connected.value = true
    reconnectAttempts.value = 0
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

    // 认证失败不重连
    if (event?.code === 4001) {
      uni.showToast({ title: '登录已过期，请重新登录', icon: 'none' })
      setTimeout(() => {
        uni.navigateTo({ url: '/pages/login/login' })
      }, 1000)
      return
    }

    // 带退避的有限重连
    if (reconnectAttempts.value < maxReconnectAttempts) {
      reconnectAttempts.value++
      const delay = reconnectDelay * Math.pow(1.5, reconnectAttempts.value - 1)
      reconnectTimer.value = setTimeout(() => {
        initWebSocket()
      }, delay)
    }
  })

  socketTask.value.onError((error) => {
    console.error('公共聊天室 WebSocket 错误:', error)
    connectionStatus.value = 'error'
  })
}

const handleSocketMessage = (data) => {
  if (data.type === 'chat_message') {
    const existingTemp = messages.value.findIndex(
      msg => msg.isTemp && msg.clientId === data.client_id
    )
    if (existingTemp !== -1) {
      messages.value[existingTemp] = {
        ...messages.value[existingTemp],
        id: `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
        time: data.time || new Date().toISOString(),
        isTemp: false,
        sendFailed: false
      }
    } else {
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
    }
    scrollToBottom()
  } else if (data.type === 'online_users') {
    onlineCount.value = data.count || 0
  } else if (data.type === 'welcome') {
    onlineCount.value = data.online_users?.count || 0
  } else if (data.type === 'heartbeat_response') {
    // 忽略
  } else if (data.type === 'message_received') {
    const index = messages.value.findIndex(msg => msg.isTemp && msg.clientId === data.client_id)
    if (index !== -1) {
      messages.value[index] = {
        ...messages.value[index],
        isTemp: false,
        sendFailed: false
      }
    }
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
  stopHeartbeat()
  ackTimers.value.forEach((timer) => clearTimeout(timer))
  ackTimers.value.clear()
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
    clientId,
    content,
    type: 'chat',
    user: {
      id: currentUserId.value,
      username: '我',
      avatar: currentUserAvatar.value
    },
    time: new Date().toISOString(),
    isTemp: true,
    sendFailed: false
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

  // 2 秒内未收到确认则标记失败
  const ackTimer = setTimeout(() => {
    ackTimers.value.delete(ackTimer)
    const index = messages.value.findIndex(msg => msg.id === tempMsg.id)
    if (index !== -1 && messages.value[index].isTemp) {
      messages.value[index].sendFailed = true
      messages.value[index].isTemp = false
    }
    sending.value = false
  }, 2000)
  ackTimers.value.add(ackTimer)
}

const resendMessage = (msg) => {
  if (!msg.content || !connected.value) return
  msg.sendFailed = false
  msg.isTemp = true
  msg.clientId = Date.now()
  scrollToBottom()

  if (socketTask.value) {
    socketTask.value.send({
      data: JSON.stringify({
        type: 'chat_message',
        message: msg.content,
        client_id: msg.clientId
      })
    })
  }

  const ackTimer = setTimeout(() => {
    ackTimers.value.delete(ackTimer)
    const index = messages.value.findIndex(item => item.id === msg.id)
    if (index !== -1 && messages.value[index].isTemp) {
      messages.value[index].sendFailed = true
      messages.value[index].isTemp = false
    }
  }, 2000)
  ackTimers.value.add(ackTimer)
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

.empty-tip {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.empty-icon {
  font-size: 80rpx;
  margin-bottom: 20rpx;
}

.messages-list {
  display: flex;
  flex-direction: column;
}

.date-divider {
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 20rpx 0;
}

.date-divider text {
  padding: 8rpx 20rpx;
  background: #e0e0e0;
  color: #666;
  border-radius: 20rpx;
  font-size: 24rpx;
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
  background-color: #4361ee;
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

.message-meta {
  display: flex;
  align-items: center;
  margin-top: 8rpx;
  flex-wrap: wrap;
}

.message-mine .message-meta {
  justify-content: flex-end;
}

.status-hint {
  font-size: 22rpx;
  margin-right: 12rpx;
}

.status-hint.sending {
  color: #fa8c16;
}

.status-hint.failed {
  color: #f5222d;
  text-decoration: underline;
}

.message-time {
  font-size: 22rpx;
  color: #999;
  align-self: flex-end;
}

.message-mine .message-time {
  color: rgba(255, 255, 255, 0.7);
}

.reconnect-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16rpx 24rpx;
  background: #fff7e6;
  border-top: 1rpx solid #ffe7ba;
}

.reconnect-text {
  font-size: 24rpx;
  color: #fa8c16;
  flex: 1;
}

.reconnect-btn {
  font-size: 24rpx;
  color: #fff;
  background: #fa8c16;
  padding: 8rpx 20rpx;
  border-radius: 24rpx;
  margin-left: 16rpx;
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
  background-color: #4361ee;
  color: #fff;
  border-radius: 36rpx;
  font-size: 28rpx;
  padding: 0;
}

.send-btn[disabled] {
  background-color: #bfbfbf;
}
</style>
