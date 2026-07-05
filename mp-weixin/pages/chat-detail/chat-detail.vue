<template>
  <view class="container">
    <view class="header">
      <text class="back-icon" @click="goBack">&#60;</text>
      <image class="header-avatar" :src="formatAvatar(userInfo.avatar)" mode="aspectFill" />
      <text class="header-title">{{ userInfo.username || username }}</text>
    </view>

    <scroll-view class="message-list" scroll-y :scroll-top="scrollTop" :scroll-with-animation="true">
      <view class="load-more" v-if="hasMore && !loadingMore" @click="loadMore">
        <text>加载更多消息</text>
      </view>
      <view class="loading-more" v-if="loadingMore">
        <text>加载中...</text>
      </view>

      <view class="message-item" v-for="(msg, index) in messages" :key="msg.id || index"
        :class="{ 'message-mine': isMine(msg) }">
        <image v-if="!isMine(msg)" class="msg-avatar" :src="formatAvatar(msg.sender?.avatar)" mode="aspectFill" />
        <view class="message-content">
          <text class="message-text">{{ msg.content }}</text>
          <text class="message-time">{{ formatDateTime(msg.created_at) }}</text>
        </view>
        <image v-if="isMine(msg)" class="msg-avatar" :src="formatAvatar(currentUserAvatar)" mode="aspectFill" />
      </view>
    </scroll-view>

    <view class="input-area">
      <input class="message-input" v-model="inputMessage" type="text" placeholder="输入消息..." confirm-type="send"
        @confirm="sendMessage" />
      <button class="send-btn" :disabled="!inputMessage.trim() || sending" @click="sendMessage">
        {{ sending ? '发送中' : '发送' }}
      </button>
    </view>
  </view>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import userApi from '../../api/user'
import { getWebSocketUrl } from '../../api/request'
import { formatAvatar } from '../../utils/image'
import { formatDateTime } from '../../utils/date'

const userId = ref(0)
const username = ref('')
const userInfo = ref({})
const messages = ref([])
const inputMessage = ref('')
const currentUserId = ref(0)
const currentUserAvatar = ref('')
const loadingMore = ref(false)
const sending = ref(false)
const scrollTop = ref(0)
const hasMore = ref(true)
const page = ref(1)
const pageSize = 20
const socketTask = ref(null)
const reconnectTimer = ref(null)

const isMine = (msg) => {
  return msg.sender?.id === currentUserId.value
}

onLoad((options) => {
  userId.value = Number(options.userId) || 0
  username.value = options.username || ''
})

onMounted(() => {
  checkAuthAndLoad()
})

onUnmounted(() => {
  closeSocket()
  if (reconnectTimer.value) {
    clearTimeout(reconnectTimer.value)
  }
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

    // 标记对方消息为已读
    if (!isLoadMore) {
      userApi.markMessagesAsRead(userId.value).catch(() => { })
      initWebSocket()
    }
  } catch (error) {
    console.error('获取对话失败:', error)
    uni.showToast({ title: '加载失败', icon: 'none' })
  } finally {
    loadingMore.value = false
  }
}

const loadMore = () => {
  loadMessages(true)
}

const scrollToBottom = () => {
  nextTick(() => {
    scrollTop.value = 999999
  })
}

const initWebSocket = () => {
  if (!userId.value || socketTask.value) return

  const url = getWebSocketUrl(`private/${userId.value}`)
  socketTask.value = uni.connectSocket({
    url,
    success: () => {
      console.log('私信 WebSocket 连接请求已发送')
    }
  })

  socketTask.value.onOpen(() => {
    console.log('私信 WebSocket 连接已打开')
  })

  socketTask.value.onMessage((res) => {
    try {
      const data = JSON.parse(res.data)
      if (data.type === 'private_message') {
        const msg = {
          id: data.id,
          content: data.content,
          created_at: data.created_at,
          sender: {
            id: data.sender_id,
            username: data.sender_username,
            avatar: data.sender_avatar
          },
          receiver: {
            id: data.receiver_id,
            username: data.receiver_username
          }
        }
        messages.value.push(msg)
        scrollToBottom()
      }
    } catch (error) {
      console.error('解析私信消息失败:', error)
    }
  })

  socketTask.value.onClose((res) => {
    console.log('私信 WebSocket 连接已关闭', res)
    socketTask.value = null

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

    reconnectTimer.value = setTimeout(() => {
      initWebSocket()
    }, 5000)
  })

  socketTask.value.onError((error) => {
    console.error('私信 WebSocket 错误:', error)
  })
}

const closeSocket = () => {
  if (socketTask.value) {
    socketTask.value.close()
    socketTask.value = null
  }
}

const sendMessage = async () => {
  const content = inputMessage.value.trim()
  if (!content || sending.value) return

  sending.value = true
  const tempMsg = {
    id: `temp-${Date.now()}`,
    content,
    created_at: new Date().toISOString(),
    sender: {
      id: currentUserId.value,
      username: '我',
      avatar: currentUserAvatar.value
    }
  }
  messages.value.push(tempMsg)
  inputMessage.value = ''
  scrollToBottom()

  try {
    await userApi.sendMessage(userId.value, { content })
  } catch (error) {
    console.error('发送私信失败:', error)
    uni.showToast({ title: '发送失败', icon: 'none' })
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
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
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
  color: #4CAF50;
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

.message-content {
  max-width: 70%;
  margin: 0 20rpx;
  display: flex;
  flex-direction: column;
}

.message-text {
  background-color: #fff;
  padding: 18rpx 24rpx;
  border-radius: 16rpx;
  font-size: 28rpx;
  color: #333;
  line-height: 1.5;
  word-break: break-all;
}

.message-mine .message-text {
  background-color: #4CAF50;
  color: #fff;
}

.message-time {
  font-size: 20rpx;
  color: #999;
  margin-top: 8rpx;
}

.message-mine .message-time {
  text-align: right;
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
  background-color: #4CAF50;
  color: #fff;
  font-size: 28rpx;
  border-radius: 36rpx;
  border: none;
}

.send-btn[disabled] {
  background-color: #ccc;
}
</style>
