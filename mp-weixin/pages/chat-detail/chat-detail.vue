<template>
  <view class="container">
    <view class="header" :style="headerStyle">
      <text class="back-icon" @click="goBack">&#60;</text>
      <image class="header-avatar" :src="formatAvatar(userInfo.avatar)" mode="aspectFill" />
      <text class="header-title">{{ userInfo.username || username }}</text>
      <view class="header-status" :class="connectionStatus">
        <text class="status-dot"></text>
        <text class="status-text">{{ connectionStatusText }}</text>
      </view>
    </view>

    <scroll-view class="message-list" scroll-y :scroll-top="scrollTop" :scroll-with-animation="true">
      <view class="load-more" v-if="hasMore && !loadingMore" @click="loadMore">
        <text>加载更多消息</text>
      </view>
      <view class="loading-more" v-if="loadingMore">
        <text>加载中...</text>
      </view>

      <view class="empty-tip" v-if="!loading && messages.length === 0">
        <view class="empty-icon">✉️</view>
        <text>开始与 {{ userInfo.username || username }} 聊天吧！</text>
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
            :class="{ 'message-mine': isMine(msg) }"
          >
            <image v-if="!isMine(msg)" class="msg-avatar" :src="formatAvatar(msg.sender?.avatar)" mode="aspectFill" />
            <view class="message-body">
              <view class="message-content" :class="{ 'send-failed': msg.sendFailed }">
                <text class="message-text">{{ msg.content }}</text>
              </view>
              <view class="message-meta">
                <text v-if="msg.isTemp && !msg.sendFailed" class="status-hint sending">发送中...</text>
                <text v-else-if="msg.sendFailed" class="status-hint failed" @click="resendMessage(msg)">发送失败，点击重试</text>
                <text v-else-if="isMine(msg)" class="status-hint sent">已发送</text>
                <text class="message-time">{{ formatDateTime(msg.created_at) }}</text>
              </view>
            </view>
            <image v-if="isMine(msg)" class="msg-avatar" :src="formatAvatar(currentUserAvatar)" mode="aspectFill" />
          </view>
        </template>
      </view>
    </scroll-view>

    <view v-if="!isConnected && !loading" class="reconnect-bar">
      <text class="reconnect-text">⚠ 连接已断开，可能无法实时收到新消息</text>
      <text class="reconnect-btn" @click="initWebSocket">重新连接</text>
    </view>

    <view class="input-area safe-area-bottom">
      <input
        class="message-input"
        v-model="inputMessage"
        type="text"
        placeholder="输入消息..."
        confirm-type="send"
        :disabled="sending"
        @confirm="sendMessage"
      />
      <button class="send-btn" :disabled="!inputMessage.trim() || sending" @click="sendMessage">
        {{ sending ? '发送中' : '发送' }}
      </button>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import { onLoad, onUnload } from '@dcloudio/uni-app'
import userApi from '../../api/user'
import { getWebSocketUrl, getWebSocketProtocols } from '../../api/request'
import { formatAvatar } from '../../utils/image'
import { formatDateTime } from '../../utils/date'

const userId = ref(0)
const username = ref('')
const userInfo = ref({})
const messages = ref([])
const inputMessage = ref('')
const currentUserId = ref(0)
const currentUserAvatar = ref('')
const loading = ref(false)
const loadingMore = ref(false)
const sending = ref(false)
const scrollTop = ref(0)
const hasMore = ref(true)
const page = ref(1)
const pageSize = 20
const socketTask = ref(null)
const reconnectTimer = ref(null)
const heartbeatTimer = ref(null)
const reconnectAttempts = ref(0)
const maxReconnectAttempts = 5
const reconnectDelay = 1000
const connectionStatus = ref('disconnected')
const isConnected = ref(false)

const isMine = (msg) => {
  return msg.sender?.id === currentUserId.value
}

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
    const date = formatDate(msg.created_at)
    if (date !== currentDate) {
      currentDate = date
      groups.push({ date, messages: [msg] })
    } else {
      groups[groups.length - 1].messages.push(msg)
    }
  })

  return groups
})

onLoad((options) => {
  const info = uni.getSystemInfoSync()
  statusBarHeight.value = info.statusBarHeight
  userId.value = Number(options.userId) || 0
  username.value = options.username || ''
  checkAuthAndLoad()
})

onUnload(() => {
  closeSocket()
})

const checkAuthAndLoad = async () => {
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
      currentUserId.value = info.id
      currentUserAvatar.value = info.avatar
    } catch (e) {
      console.error('解析用户信息失败', e)
    }
  }

  // 进入私聊前先检查好友关系
  const canChat = await checkFriendship()
  if (!canChat) return

  loadMessages()
}

const checkFriendship = async () => {
  if (!userId.value) return false
  try {
    const result = await userApi.checkFriendship(userId.value)
    if (!result.is_friend) {
      uni.showToast({ title: '你们还不是好友，无法发起私聊', icon: 'none' })
      setTimeout(() => {
        uni.navigateBack()
      }, 1500)
      return false
    }
    return true
  } catch (error) {
    console.error('检查好友关系失败:', error)
    uni.showToast({ title: '无法验证好友关系', icon: 'none' })
    setTimeout(() => {
      uni.navigateBack()
    }, 1500)
    return false
  }
}

const loadMessages = async (isLoadMore = false) => {
  if (!userId.value) return

  if (isLoadMore) {
    if (loadingMore.value || !hasMore.value) return
    loadingMore.value = true
    page.value++
  } else {
    loading.value = true
    page.value = 1
  }

  try {
    const result = await userApi.getConversation(userId.value, page.value, pageSize)
    userInfo.value = result.user || {}
    const list = result.messages || []

    if (isLoadMore) {
      messages.value = [...list, ...messages.value]
      if (!result.next) {
        hasMore.value = false
      }
    } else {
      messages.value = list
      hasMore.value = !!result.next
      scrollToBottom()
    }

    // 标记对方消息为已读，并建立 WebSocket 连接
    if (!isLoadMore) {
      userApi.markMessagesAsRead(userId.value).catch(() => { })
      initWebSocket()
    }
  } catch (error) {
    console.error('获取对话失败:', error)
    uni.showToast({ title: '加载失败', icon: 'none' })
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

const loadMore = () => {
  loadMessages(true)
}

const scrollToBottom = () => {
  nextTick(() => {
    scrollTop.value = 999999 + Date.now()
  })
}

const initWebSocket = () => {
  if (!userId.value || socketTask.value) return

  connectionStatus.value = 'connecting'
  const url = getWebSocketUrl(`private/${userId.value}`)
  const protocols = getWebSocketProtocols()

  socketTask.value = uni.connectSocket({
    url,
    protocols,
    success: () => {
      console.log('私信 WebSocket 连接请求已发送')
    }
  })

  socketTask.value.onOpen(() => {
    console.log('私信 WebSocket 连接已打开')
    connectionStatus.value = 'connected'
    isConnected.value = true
    reconnectAttempts.value = 0
    startHeartbeat()
    loadMessages()
  })

  socketTask.value.onMessage((res) => {
    try {
      const data = JSON.parse(res.data)
      if (data.type === 'private_message') {
        handlePrivateMessage(data)
      } else if (data.type === 'private_chat_ready') {
        console.log('私聊频道就绪:', data.message)
      } else if (data.type === 'heartbeat_response') {
        // 忽略
      } else if (data.type === 'message_received') {
        const index = messages.value.findIndex(
          msg => msg.isTemp && msg.content === data.content && msg.sender?.id === currentUserId.value
        )
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
    } catch (error) {
      console.error('解析私信消息失败:', error)
    }
  })

  socketTask.value.onClose((res) => {
    console.log('私信 WebSocket 连接已关闭', res)
    socketTask.value = null
    isConnected.value = false
    connectionStatus.value = 'disconnected'
    stopHeartbeat()

    // 4001 未认证、4002 缺少参数、4003 非好友、4004 用户不存在时不重连
    if ([4001, 4002, 4003, 4004].includes(res?.code)) {
      let message = '连接失败'
      if (res?.code === 4001) message = '请先登录'
      if (res?.code === 4003) message = '你们还不是好友，无法私聊'
      if (res?.code === 4004) message = '对方用户不存在'
      uni.showToast({ title: message, icon: 'none' })
      if (res?.code === 4003) {
        setTimeout(() => {
          uni.navigateBack()
        }, 1500)
      }
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
    console.error('私信 WebSocket 错误:', error)
    connectionStatus.value = 'error'
    isConnected.value = false
  })
}

const handlePrivateMessage = (data) => {
  const senderId = Number(data.sender_id)
  const receiverId = Number(data.receiver_id)
  const currentId = Number(userId.value)

  // 只处理属于当前对话的消息
  const participants = [senderId, receiverId]
  if (!participants.includes(currentUserId.value) || !participants.includes(currentId)) {
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

  // 检查是否是当前用户的临时消息，如果是则替换
  const existingIndex = messages.value.findIndex(msg =>
    msg.isTemp && msg.sender?.id === senderId && msg.content === newMessage.content
  )

  if (existingIndex !== -1) {
    messages.value[existingIndex] = newMessage
  } else {
    messages.value.push(newMessage)
    scrollToBottom()
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
  if (socketTask.value) {
    socketTask.value.close()
    socketTask.value = null
  }
}

const sendMessage = async () => {
  const content = inputMessage.value.trim()
  if (!content || sending.value || !userId.value) return

  sending.value = true
  const tempId = `temp-${Date.now()}`
  const tempMessage = {
    id: tempId,
    content,
    created_at: new Date().toISOString(),
    sender: {
      id: currentUserId.value,
      username: '我',
      avatar: currentUserAvatar.value
    },
    receiver: userInfo.value,
    isTemp: true,
    sendFailed: false
  }

  messages.value.push(tempMessage)
  inputMessage.value = ''
  scrollToBottom()

  try {
    const response = await userApi.sendMessage(userId.value, { content })
    const index = messages.value.findIndex(msg => msg.id === tempId)
    if (index !== -1 && response) {
      messages.value[index] = {
        ...response,
        sender: response.sender || tempMessage.sender,
        receiver: response.receiver || userInfo.value,
        isTemp: false,
        sendFailed: false
      }
    }
  } catch (error) {
    console.error('发送私信失败:', error)
    const index = messages.value.findIndex(msg => msg.id === tempId)
    if (index !== -1) {
      messages.value[index] = {
        ...messages.value[index],
        isTemp: false,
        sendFailed: true
      }
    }
    uni.showToast({ title: '发送失败', icon: 'none' })
  } finally {
    sending.value = false
  }
}

const resendMessage = async (message) => {
  if (!message.content || !userId.value) return
  message.sendFailed = false
  message.isTemp = true
  sending.value = true

  try {
    const response = await userApi.sendMessage(userId.value, { content: message.content })
    const index = messages.value.findIndex(msg => msg.id === message.id)
    if (index !== -1 && response) {
      messages.value[index] = {
        ...response,
        sender: response.sender || message.sender,
        receiver: response.receiver || userInfo.value,
        isTemp: false,
        sendFailed: false
      }
    }
  } catch (error) {
    console.error('重发私信失败:', error)
    message.sendFailed = true
    message.isTemp = false
    uni.showToast({ title: '重发失败', icon: 'none' })
  } finally {
    sending.value = false
  }
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

.header-avatar {
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
  margin-right: 20rpx;
  background-color: #eee;
}

.header-title {
  flex: 1;
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
}

.header-status {
  display: flex;
  align-items: center;
  padding: 4rpx 12rpx;
  border-radius: 12rpx;
  font-size: 22rpx;
}

.header-status .status-dot {
  width: 12rpx;
  height: 12rpx;
  border-radius: 50%;
  margin-right: 8rpx;
}

.header-status.connecting {
  background: #fff7e6;
  color: #fa8c16;
}

.header-status.connecting .status-dot {
  background: #fa8c16;
}

.header-status.connected {
  background: #f6ffed;
  color: #52c41a;
}

.header-status.connected .status-dot {
  background: #52c41a;
}

.header-status.disconnected,
.header-status.error {
  background: #fff1f0;
  color: #f5222d;
}

.header-status.disconnected .status-dot,
.header-status.error .status-dot {
  background: #f5222d;
}

.message-list {
  flex: 1;
  padding: 20rpx;
  overflow-y: auto;
}

.load-more,
.loading-more {
  text-align: center;
  padding: 20rpx;
  color: #999;
  font-size: 24rpx;
}

.load-more {
  color: #4361ee;
}

.empty-tip {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 100rpx 30rpx;
  color: #999;
  font-size: 28rpx;
  text-align: center;
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

.msg-avatar {
  width: 72rpx;
  height: 72rpx;
  border-radius: 50%;
  background-color: #eee;
  flex-shrink: 0;
}

.message-body {
  max-width: 70%;
  margin: 0 20rpx;
  display: flex;
  flex-direction: column;
}

.message-content {
  padding: 18rpx 24rpx;
  border-radius: 16rpx;
  background-color: #fff;
  display: flex;
  flex-direction: column;
}

.message-mine .message-content {
  background-color: #4361ee;
}

.message-content.send-failed {
  background-color: #fff1f0 !important;
  border: 1rpx solid #f5222d;
}

.message-text {
  font-size: 28rpx;
  color: #333;
  line-height: 1.5;
  word-break: break-all;
}

.message-mine .message-text {
  color: #fff;
}

.message-mine .send-failed .message-text {
  color: #f5222d;
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

.status-hint.sent {
  color: #999;
}

.message-time {
  font-size: 20rpx;
  color: #999;
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
  padding: 20rpx 30rpx;
  background-color: #fff;
  border-top: 1rpx solid #f0f0f0;
}

.message-input {
  flex: 1;
  height: 72rpx;
  background-color: #f5f5f5;
  border-radius: 36rpx;
  padding: 0 30rpx;
  font-size: 28rpx;
  color: #333;
}

.send-btn {
  width: 120rpx;
  height: 72rpx;
  line-height: 72rpx;
  margin-left: 20rpx;
  padding: 0;
  background-color: #4361ee;
  color: #fff;
  font-size: 28rpx;
  border-radius: 36rpx;
  border: none;
}

.send-btn[disabled] {
  background-color: #ccc;
}
</style>
