<template>
  <div class="chat-room">
    <div class="chat-header">
      <h3>实时聊天室</h3>
      <div class="online-users">
        <span class="online-count">{{ onlineUsers.length }}人在线</span>
      </div>
    </div>
    
    <div class="chat-messages" ref="messagesContainer">
      <div v-for="(message, index) in messages" :key="index" 
           :class="['message', message.user.id === userStore.user?.id ? 'message-mine' : '']">
        <div class="message-avatar">
          <img :src="message.user.avatar || '/default-avatar.png'" :alt="message.user.username">
        </div>
        <div class="message-content">
          <div class="message-header">
            <span class="message-author">{{ message.user.username }}</span>
            <span class="message-time">{{ formatTime(message.time) }}</span>
          </div>
          <div class="message-body">{{ message.content }}</div>
        </div>
      </div>
      <div v-if="messages.length === 0" class="no-messages">
        暂无消息，发送第一条消息开始聊天吧！
      </div>
    </div>
    
    <div class="chat-input">
      <input 
        v-model="messageInput" 
        @keyup.enter="sendMessage"
        placeholder="输入消息..." 
        :disabled="!isLoggedIn"
      />
      <button @click="sendMessage" :disabled="!isLoggedIn || !messageInput.trim()">
        发送
      </button>
    </div>
    <div v-if="!isLoggedIn" class="login-tip">
      请<router-link to="/login">登录</router-link>后参与聊天
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, nextTick, watch } from 'vue'
import { useUserStore } from '@/stores/userStore'
import { formatDate } from '@/utils/date'

const userStore = useUserStore()
const isLoggedIn = computed(() => userStore.isLoggedIn)

// 模拟服务器数据
interface ChatMessage {
  id: number
  content: string
  user: {
    id: number
    username: string
    avatar?: string
  }
  time: string
}

interface OnlineUser {
  id: number
  username: string
  avatar?: string
}

// 响应式数据
const messages = ref<ChatMessage[]>([])
const onlineUsers = ref<OnlineUser[]>([])
const messageInput = ref('')
const messagesContainer = ref<HTMLElement | null>(null)
const ws = ref<WebSocket | null>(null)

// 模拟获取历史消息
const fetchHistoryMessages = async () => {
  try {
    // 这里应该调用API获取历史消息
    // 目前使用模拟数据
    messages.value = [
      {
        id: 1,
        content: '欢迎来到校园实时聊天室！',
        user: { id: 0, username: '系统', avatar: '/system-avatar.png' },
        time: new Date(Date.now() - 3600000).toISOString()
      },
      {
        id: 2,
        content: '有人知道今天食堂有什么好吃的吗？',
        user: { id: 101, username: '美食达人', avatar: '/avatar1.png' },
        time: new Date(Date.now() - 1800000).toISOString()
      },
      {
        id: 3,
        content: '今天的红烧肉很不错，推荐尝试！',
        user: { id: 102, username: '校园达人', avatar: '/avatar2.png' },
        time: new Date(Date.now() - 1200000).toISOString()
      }
    ]
  } catch (error) {
    console.error('获取历史消息失败:', error)
  }
}

// 模拟获取在线用户
const fetchOnlineUsers = async () => {
  try {
    // 这里应该调用API获取在线用户
    // 目前使用模拟数据
    onlineUsers.value = [
      { id: 101, username: '美食达人', avatar: '/avatar1.png' },
      { id: 102, username: '校园达人', avatar: '/avatar2.png' }
    ]
    
    // 如果当前用户已登录，添加到在线用户列表
    if (isLoggedIn.value && userStore.user) {
      const currentUser = {
        id: userStore.user.id,
        username: userStore.user.username,
        avatar: userStore.user.avatar
      }
      if (!onlineUsers.value.some(user => user.id === currentUser.id)) {
        onlineUsers.value.push(currentUser)
      }
    }
  } catch (error) {
    console.error('获取在线用户失败:', error)
  }
}

// 初始化WebSocket连接
const initWebSocket = () => {
  // 检查浏览器是否支持WebSocket
  if (!('WebSocket' in window)) {
    console.error('浏览器不支持WebSocket')
    return
  }
  
  try {
    // 创建WebSocket连接
    const wsUrl = 'ws://localhost:8000/ws/chat/'
    ws.value = new WebSocket(wsUrl)
    
    // 连接建立时的回调
    ws.value.onopen = () => {
      console.log('WebSocket连接已建立')
      // 发送用户加入消息
      if (isLoggedIn.value && userStore.user) {
        sendSystemMessage(`${userStore.user.username} 加入了聊天室`)
      }
    }
    
    // 接收消息的回调
    ws.value.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'chat_message') {
          messages.value.push({
            id: Date.now(),
            content: data.message,
            user: data.user,
            time: new Date().toISOString()
          })
          scrollToBottom()
        } else if (data.type === 'user_list') {
          onlineUsers.value = data.users
        }
      } catch (error) {
        console.error('处理WebSocket消息失败:', error)
      }
    }
    
    // 连接关闭的回调
    ws.value.onclose = () => {
      console.log('WebSocket连接已关闭')
    }
    
    // 发生错误的回调
    ws.value.onerror = (error) => {
      console.error('WebSocket错误:', error)
    }
  } catch (error) {
    console.error('初始化WebSocket失败:', error)
  }
}

// 发送系统消息
const sendSystemMessage = (content: string) => {
  if (ws.value && ws.value.readyState === WebSocket.OPEN) {
    ws.value.send(JSON.stringify({
      type: 'system_message',
      message: content
    }))
  }
}

// 发送消息
const sendMessage = () => {
  if (!isLoggedIn.value || !messageInput.value.trim()) return
  
  const message = messageInput.value.trim()
  
  // 如果WebSocket连接可用，发送消息
  if (ws.value && ws.value.readyState === WebSocket.OPEN) {
    ws.value.send(JSON.stringify({
      type: 'chat_message',
      message: message,
      user: {
        id: userStore.user?.id,
        username: userStore.user?.username,
        avatar: userStore.user?.avatar
      }
    }))
  } else {
    // 模拟消息发送（实际项目中应该重新连接WebSocket）
    messages.value.push({
      id: Date.now(),
      content: message,
      user: {
        id: userStore.user?.id || 0,
        username: userStore.user?.username || '未知用户',
        avatar: userStore.user?.avatar
      },
      time: new Date().toISOString()
    })
  }
  
  // 清空输入框
  messageInput.value = ''
  
  // 滚动到底部
  scrollToBottom()
}

// 滚动到底部
const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// 格式化时间
const formatTime = (timeString: string) => {
  return formatDate(timeString)
}

// 监听消息变化，自动滚动到底部
watch(messages, () => {
  scrollToBottom()
})

// 组件挂载时
onMounted(async () => {
  await fetchHistoryMessages()
  await fetchOnlineUsers()
  initWebSocket()
  scrollToBottom()
})

// 组件卸载时关闭WebSocket连接
onUnmounted(() => {
  if (ws.value) {
    // 发送用户离开消息
    if (isLoggedIn.value && userStore.user) {
      sendSystemMessage(`${userStore.user.username} 离开了聊天室`)
    }
    ws.value.close()
  }
})
</script>

<style scoped>
.chat-room {
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  background-color: #fff;
  display: flex;
  flex-direction: column;
  height: 400px;
  width: 100%;
}

.chat-header {
  padding: 12px 16px;
  background-color: #409eff;
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chat-header h3 {
  margin: 0;
  font-size: 16px;
}

.online-count {
  font-size: 12px;
  background-color: rgba(255, 255, 255, 0.2);
  padding: 2px 8px;
  border-radius: 10px;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.no-messages {
  text-align: center;
  color: #999;
  margin: auto;
}

.message {
  display: flex;
  gap: 8px;
  max-width: 80%;
}

.message-mine {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
}

.message-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.message-content {
  background-color: #f1f1f1;
  border-radius: 12px;
  padding: 8px 12px;
  position: relative;
}

.message-mine .message-content {
  background-color: #e1f3ff;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.message-author {
  font-weight: 500;
  font-size: 13px;
  color: #333;
}

.message-time {
  font-size: 11px;
  color: #999;
}

.message-body {
  font-size: 14px;
  line-height: 1.4;
  word-break: break-word;
}

.chat-input {
  display: flex;
  padding: 12px;
  background-color: #f9f9f9;
  border-top: 1px solid #eee;
}

.chat-input input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  outline: none;
}

.chat-input input:focus {
  border-color: #409eff;
}

.chat-input button {
  margin-left: 8px;
  padding: 0 16px;
  background-color: #409eff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.chat-input button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.login-tip {
  text-align: center;
  padding: 8px;
  font-size: 12px;
  color: #666;
  background-color: #f9f9f9;
}

.login-tip a {
  color: #409eff;
  text-decoration: none;
}
</style> 