<template>
  <div class="chat-room" :class="{ embedded, fullscreen: isFullscreen }">
    <div class="chat-header">
      <h3>实时聊天室 <span v-if="connectionStatus !== 'connected'" class="connection-status">{{ connectionStatusText }}</span></h3>
      <div class="online-users">
        <span class="online-count">{{ onlineUsers }}人在线</span>
        <button @click="fetchOnlineUsers" class="refresh-btn" title="刷新在线人数" :disabled="connectionStatus !== 'connected'">
          <i class="refresh-icon">⟳</i>
        </button>
        <button @click="toggleFullscreen" class="maximize-btn" title="{{ isFullscreen ? '退出全屏' : '全屏模式' }}">
          <i class="maximize-icon">{{ isFullscreen ? '⛶' : '⛶' }}</i>
        </button>
      </div>
    </div>
    
    <div class="chat-messages" ref="messagesContainer">
      <div v-for="(message, index) in messages" :key="index" 
           :class="['message', message.user && message.user.id === userStore.user?.id ? 'message-mine' : '', message.type === 'system' ? 'message-system' : '']">
        <template v-if="message.type === 'system'">
          <div class="system-message">
            {{ message.content }}
            <span class="message-time">{{ formatTime(message.time) }}</span>
          </div>
        </template>
        <template v-else>
          <div class="message-avatar" @click="showUserMenu(message.user)">
              <img 
                :src="message.user?.avatar || 'http://localhost:8000/media/avatars1/默认头像.png'" 
                :alt="message.user?.username"
                @error="handleImageError"
                loading="lazy"
                style="cursor: pointer;"
              >
            </div>
          <div class="message-content">
            <div class="message-header">
              <span class="message-author" @click="showUserMenu(message.user)" style="cursor: pointer;">{{ message.user?.username }}</span>
              <span class="message-time">{{ formatTime(message.time) }}</span>
            </div>
            <div class="message-body" v-html="formatMessageContent(message.content)"></div>
          </div>
        </template>
      </div>
      <div v-if="messages.length === 0" class="no-messages">
        暂无消息，发送第一条消息开始聊天吧！
      </div>
    </div>
    
    <div class="connection-status-bar" v-if="connectionStatus !== 'connected'">
      <template v-if="connectionStatus === 'connecting'">
        <span class="connecting-spinner"></span> 正在连接到聊天服务器...
      </template>
      <template v-else-if="connectionStatus === 'disconnected'">
        连接已断开 <button @click="connectWebSocket" class="reconnect-btn">重新连接</button>
      </template>
      <template v-else-if="connectionStatus === 'error'">
        连接出错 <button @click="connectWebSocket" class="reconnect-btn">重试连接</button>
      </template>
    </div>
    
    <div class="chat-input">
      <input 
        v-model="messageInput" 
        @keyup.enter="sendMessage"
        placeholder="输入消息..." 
        :disabled="!userStore.isLoggedIn || connectionStatus !== 'connected'"
      />
      <button 
        @click="sendMessage" 
        :disabled="!userStore.isLoggedIn || connectionStatus !== 'connected' || !messageInput.trim()"
        :class="{ 'loading': sending }"
      >
        {{ sending ? '发送中...' : '发送' }}
      </button>
    </div>
    <div v-if="!userStore.isLoggedIn" class="login-tip">
      请<router-link to="/login">登录</router-link>后参与聊天
    </div>
    <div v-else-if="connectionStatus !== 'connected'" class="login-tip">
      正在连接服务器，请稍候...
    </div>
    <div v-if="lastError" class="error-message">
      {{ lastError }}
      <button @click="lastError = ''" class="close-btn">×</button>
    </div>
    
    <!-- 用户菜单 -->
    <div 
      v-if="userMenuVisible" 
      class="user-menu"
      :style="{
        left: userMenuPosition.x + 'px',
        top: userMenuPosition.y + 'px'
      }"
    >
      <div class="user-menu-header">
        <div class="user-menu-avatar">
          <img :src="currentUser?.avatar || 'http://localhost:8000/media/avatars1/默认头像.png'" :alt="currentUser?.username">
        </div>
        <div class="user-menu-name">{{ currentUser?.username }}</div>
      </div>
      <div class="user-menu-actions">
        <button class="user-menu-action" @click="addFriend">
          <i class="action-icon">+</i> 添加好友
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, nextTick, watch } from 'vue'
import { useUserStore } from '@/stores/userStore'
import { formatDate } from '../utils/date'
import config from '../utils/config'
import { userApi } from '../api/user'
import { useToast } from '../composables/useToast'
import { messageStorage, useMessageStorageCleanup } from '../utils/messageStorage'

// 接收属性
const props = defineProps({
  embedded: {
    type: Boolean,
    default: false
  }
})

const userStore = useUserStore()
const { showToast } = useToast()

// 定义组件事件
const emit = defineEmits<{
  (e: 'online-users-update', count: number): void
}>()

// 用户菜单状态
const userMenuVisible = ref(false)
const userMenuPosition = ref({ x: 0, y: 0 })
const currentUser = ref<any>(null)

// 从config获取API和WebSocket URL
const API_BASE_URL = config.apiBaseUrl;


// 模拟服务器数据
interface User {
  id: number
  username: string
  avatar?: string
}

interface ChatMessage {
  id: number
  content: string
  type: 'chat' | 'system'
  user?: User
  time: string
  clientId?: number // 客户端消息ID，用于去重
}

// 响应式数据
const messages = ref<ChatMessage[]>([])
const onlineUsers = ref<number>(0)
const messageInput = ref('')
const ws = ref<WebSocket | null>(null)
const connectionStatus = ref<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected')
const reconnectAttempts = ref(0)
const maxReconnectAttempts = 3
const reconnectTimeout = ref<number | null>(null)
const sending = ref(false)
const heartbeatInterval = ref<number | null>(null)
const lastError = ref('')
const reconnectDelay = 1000; // 缩短重连延迟时间（毫秒）
const isFullscreen = ref(false)

// 连接状态文本
const connectionStatusText = computed(() => {
  switch (connectionStatus.value) {
    case 'connecting':
      return '(连接中...)'
    case 'disconnected':
      return '(未连接)'
    case 'error':
      return '(连接错误)'
    default:
      return ''
  }
})

// 获取历史消息 - 已禁用历史记录保存功能
const fetchHistoryMessages = async () => {
  try {
    // 仅显示欢迎消息，不再加载历史记录
    messages.value = [{
      id: 1,
      content: '欢迎来到校园实时聊天室！',
      type: 'system',
      time: new Date().toISOString()
    }]
    console.log('历史记录保存功能已禁用，仅显示欢迎消息');
  } catch (error) {
    console.error('获取历史消息失败:', error);
    // 显示错误消息
    messages.value = [{
      id: 1,
      content: '无法加载历史消息，请检查网络连接',
      type: 'system',
      time: new Date().toISOString()
    }];
    
    lastError.value = '加载历史消息失败，请刷新页面重试';
  }
}

// 更新在线用户数量
const updateOnlineUsers = (count: number) => {
  onlineUsers.value = count;
  emit('online-users-update', count);
};

// 获取在线用户数量
const fetchOnlineUsers = async () => {
  try {
    const apiUrl = `${API_BASE_URL}/chat/messages/online_users/`;
    const response = await fetch(apiUrl);
    if (response.ok) {
      const data = await response.json();
      updateOnlineUsers(data.count);
    } else {
      console.error('获取在线用户数量失败，状态码:', response.status);
    }
  } catch (error) {
    console.error('获取在线用户数量失败:', error);
  }
};

// WebSocket连接逻辑
const connectWebSocket = () => {
  // 重置连接状态
  connectionStatus.value = 'connecting'
  
  try {
    // 3. 如果存在之前的连接，关闭它
    if (ws.value && ws.value.readyState < 2) {  // 0=CONNECTING, 1=OPEN
      ws.value.close()
    }
    
    // 4. 创建新的WebSocket连接
    // 使用后端服务器的WebSocket URL
    let wsUrl;
    
    // 使用相对路径，利用Vite的代理配置
    wsUrl = (window.location.protocol === 'https:' ? 'wss:' : 'ws:') + 
             '//' + window.location.host + '/ws/chat';
    console.log('使用后端服务器WebSocket URL:', wsUrl);
    
    // 确保WebSocket连接正确建立
    console.log('准备连接WebSocket，当前用户状态:', { isLoggedIn: userStore.isLoggedIn, token: userStore.token ? '有token' : '无token' });
    
    // 添加认证token到WebSocket URL（如果用户已登录且有token）
    if (userStore.isLoggedIn && userStore.token) {
      wsUrl += `?token=${encodeURIComponent(userStore.token)}`;
      console.log('添加token后的WebSocket URL:', wsUrl);
    }
    
    // 添加错误处理，捕获WebSocket连接错误
    console.log('准备连接WebSocket:', wsUrl);
    
    ws.value = new WebSocket(wsUrl);
    
    // WebSocket事件处理
    ws.value.onopen = () => {
      console.log('WebSocket连接已打开')
      connectionStatus.value = 'connected'
      reconnectAttempts.value = 0
      
      // 设置心跳检测
      if (heartbeatInterval.value) {
        clearInterval(heartbeatInterval.value)
      }
      
      heartbeatInterval.value = window.setInterval(() => {
        if (ws.value && ws.value.readyState === 1) {
          ws.value.send(JSON.stringify({
            type: 'heartbeat',
            timestamp: Date.now()
          }))
          console.log('发送心跳消息')
        }
      }, 30000) // 每30秒发送一次心跳
      
      // 连接成功后发送一条测试消息
      console.log('WebSocket连接成功，准备发送测试消息')
    }
    
    ws.value.onmessage = (event) => {
      console.log('收到WebSocket消息:', event.data)
      try {
        const data = JSON.parse(event.data)
        
        // 处理不同类型的消息
        if (data.type === 'chat_message') {
          // 收到聊天消息
          console.log('处理聊天消息:', data);
          
          // 检查消息是否已存在，避免重复添加
          const messageExists = messages.value.some(msg => 
            (msg.clientId && msg.clientId === data.client_id) || // 检查客户端消息ID
            (msg.id && msg.id === data.id) || // 检查服务器消息ID
            // 额外检查：如果是当前用户发送的消息，且内容和时间相近，也视为重复
            (msg.user && msg.user.id === userStore.user?.id && 
             msg.content === data.message && 
             Math.abs(new Date(msg.time).getTime() - new Date(data.time || new Date().toISOString()).getTime()) < 1000)
          );
          
          // 如果消息不存在，才添加到消息列表
          if (!messageExists) {
            messages.value.push({
              id: data.id || Date.now(),
              content: data.message,
              type: 'chat',
              user: {
                id: data.user_id,
                username: data.username,
                avatar: data.avatar
              },
              time: data.time || new Date().toISOString(),
              clientId: data.client_id // 保存客户端消息ID用于去重
            });
            // 滚动到底部
            scrollToBottom();
          } else {
            console.log('消息已存在，跳过重复添加:', data);
          }
        } else if (data.type === 'online_users') {
          // 更新在线用户数
          console.log('更新在线用户数:', data.count)
          onlineUsers.value = data.count
          // 向父组件发送更新事件
          updateOnlineUsers(data.count)
          
        } else if (data.type === 'welcome') {
          // 欢迎消息处理
          console.log('收到欢迎消息:', data)
          if (data.online_users && data.online_users.count) {
            onlineUsers.value = data.online_users.count
            updateOnlineUsers(data.online_users.count)
          }
          
          // 加载历史消息
          fetchHistoryMessages()
        } else if (data.type === 'auth_success') {
          // 认证成功消息
          console.log('认证成功:', data);
          // 可以在这里添加认证成功的UI反馈
          messages.value.push({
            id: Date.now(),
            content: data.message || '身份验证成功',
            type: 'system',
            time: data.time || new Date().toISOString()
          });
        } else if (data.type === 'auth_warning') {
          // 未认证警告
          console.warn('未认证警告:', data);
          messages.value.push({
            id: Date.now(),
            content: data.message || '您尚未登录，部分功能可能受限',
            type: 'system',
            time: data.time || new Date().toISOString()
          });
        } else if (data.type === 'error') {
          // 错误消息
          console.error('服务器错误:', data);
          lastError.value = data.message || '服务器发生错误';
        } else if (data.type === 'heartbeat_response') {
          // 心跳响应，静默处理
          console.log('心跳响应:', data.timestamp);
        } else if (data.type === 'message_received') {
          // 消息已收到确认
          console.log('消息已收到:', data);
        } else {
          // 未知消息类型
          console.log('未知消息类型:', data.type, data);
        }
      } catch (e) {
        console.error('解析WebSocket消息出错:', e)
        lastError.value = '解析消息出错'
      }
    }
    
    ws.value.onclose = (event) => {
      console.log('WebSocket连接已关闭，代码:', event.code, '原因:', event.reason)
      connectionStatus.value = 'disconnected'
      
      // 清除心跳检测
      if (heartbeatInterval.value) {
        clearInterval(heartbeatInterval.value)
        heartbeatInterval.value = null
      }
      
      // 尝试重新连接
      if (reconnectAttempts.value < maxReconnectAttempts && userStore.isLoggedIn) {
        reconnectAttempts.value++
        const delay = reconnectDelay * Math.pow(1.5, reconnectAttempts.value - 1)
        console.log(`将在 ${delay}ms 后尝试重新连接，第 ${reconnectAttempts.value} 次`)
        
        reconnectTimeout.value = window.setTimeout(() => {
          if (userStore.isLoggedIn) {
            connectWebSocket()
          }
        }, delay)
      }
    }
    
    ws.value.onerror = (error: Event) => {
      console.error('聊天WebSocket错误:', error)
      connectionStatus.value = 'error'
      lastError.value = '连接发生错误，请稍后重试'
    }
  } catch (e: Error | unknown) {
    console.error('WebSocket连接初始化错误:', e)
    connectionStatus.value = 'error'
    lastError.value = `连接初始化错误: ${e instanceof Error ? e.message : '未知错误'}`
    
    // 自动重试
    if (reconnectAttempts.value < maxReconnectAttempts) {
      reconnectAttempts.value++;
      const delay = reconnectDelay * Math.pow(1.5, reconnectAttempts.value - 1);
      console.log(`将在 ${delay}ms 后尝试重新连接，第 ${reconnectAttempts.value} 次`);
      
      reconnectTimeout.value = window.setTimeout(() => {
        if (userStore.isLoggedIn) {
          connectWebSocket();
        }
      }, delay);
    }
  }
}

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    const container = document.querySelector('.chat-messages')
    if (container) {
      container.scrollTop = container.scrollHeight
    }
  })
}

// 发送消息
const sendMessage = async () => {
  if (!userStore.isLoggedIn || !messageInput.value.trim() || connectionStatus.value !== 'connected') {
    console.error('无法发送消息: 用户未登录或消息为空或连接未建立');
    return;
  }
  
  const messageContent = messageInput.value.trim();
  sending.value = true;
  console.log('准备发送消息:', messageContent);
  
  try {
    // 检查WebSocket连接状态
    if (!ws.value || ws.value.readyState !== WebSocket.OPEN) {
      console.error('WebSocket未连接，readyState:', ws.value?.readyState);
      lastError.value = 'WebSocket连接不可用，请刷新页面重试';
      sending.value = false;
      return;
    }
    
    // 清空输入框
    messageInput.value = '';
    
    // 生成客户端消息ID
    const clientMessageId = Date.now();
    
    // 立即将消息添加到本地数组，确保发送者能看到自己的消息
    if (userStore.user) {
      const newMessage: ChatMessage = {
        id: clientMessageId,
        content: messageContent,
        type: 'chat',
        user: {
          id: userStore.user.id,
          username: userStore.user.username,
          avatar: userStore.user.avatar
        },
        time: new Date().toISOString(),
        clientId: clientMessageId // 添加客户端消息ID用于去重
      };
      messages.value.push(newMessage);
      scrollToBottom();
    }
    
    // 发送到服务器 - 确保格式与后端期望的匹配
    const messageData = {
      type: 'chat_message',
      message: messageContent,
      content: messageContent,  // 兼容两种可能的字段名
      client_id: clientMessageId // 发送客户端消息ID用于去重
    };
    
    console.log('发送WebSocket消息:', JSON.stringify(messageData));
    ws.value.send(JSON.stringify(messageData));
    
  } catch (error) {
    console.error('发送消息失败:', error);
    lastError.value = '发送消息失败，请重试';
  } finally {
    sending.value = false;
  }
}

// 格式化时间
const formatTime = (timeString: string) => {
  return formatDate(timeString)
}

// 格式化消息内容，支持链接识别
const formatMessageContent = (content: string) => {
  if (!content) return '';
  
  // 简单的URL识别和转换
  const urlRegex = /(https?:\/\/[^\s]+)/g;
  const formattedContent = content.replace(urlRegex, '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>');
  
  return formattedContent;
};

// 处理图片加载错误
const handleImageError = (event: Event) => {
  const target = event.target as HTMLImageElement;
  target.src = 'http://localhost:8000/media/avatars1/默认头像.png';
  target.alt = '默认头像';
};

// 显示用户菜单
const showUserMenu = (user: any, event?: MouseEvent) => {
  if (!user || !user.id || !user.username || user.id === userStore.user?.id) return;
  
  currentUser.value = user;
  
  // 计算菜单位置
  if (event) {
    userMenuPosition.value = {
      x: event.clientX,
      y: event.clientY
    };
  }
  
  userMenuVisible.value = true;
  
  // 点击其他地方关闭菜单
  setTimeout(() => {
    document.addEventListener('click', hideUserMenu);
  }, 0);
};

// 隐藏用户菜单
const hideUserMenu = () => {
  userMenuVisible.value = false;
  currentUser.value = null;
  document.removeEventListener('click', hideUserMenu);
};

// 添加好友
const addFriend = async () => {
  if (!currentUser.value || !currentUser.value.id || !currentUser.value.username) {
    console.error('用户信息不完整，无法发送好友请求');
    showToast('用户信息不完整，无法发送好友请求', 'error');
    return;
  }
  
  try {
    await userApi.sendFriendRequest(currentUser.value.id);
    showToast(`已向 ${currentUser.value.username} 发送好友请求`, 'success');
    hideUserMenu();
  } catch (error) {
    console.error('发送好友请求失败:', error);
    showToast('发送好友请求失败', 'error');
  }
};

// 监听消息变化，自动滚动到底部并保存到本地存储
watch(messages, (newMessages) => {
  scrollToBottom()
  // 保存消息到本地存储
  messageStorage.saveChatMessages(newMessages)
}, { deep: true })

// 监听登录状态变化
watch(() => userStore.isLoggedIn, (newValue) => {
  if (newValue) {
    console.log('用户已登录，尝试建立WebSocket连接');
    connectWebSocket();
    fetchOnlineUsers();
  } else {
    console.log('用户已登出，关闭WebSocket连接');
    if (ws.value) {
      ws.value.close();
      ws.value = null;
    }
    connectionStatus.value = 'disconnected';
    onlineUsers.value = 0;
  }
})

// 组件挂载时检查登录状态并连接
onMounted(() => {
  console.log('组件挂载，检查登录状态');
  console.log('用户信息:', userStore.user);
  console.log('登录状态:', userStore.isLoggedIn);
  console.log('令牌:', userStore.token);
  
  // 启动消息存储清理
  useMessageStorageCleanup()
  
  // 先从本地存储加载消息
  const storedMessages = messageStorage.getChatMessages()
  if (storedMessages.length > 0) {
    messages.value = storedMessages
    console.log('从本地存储加载了', storedMessages.length, '条消息');
  }
  
  // 获取历史消息，无论是否登录
  fetchHistoryMessages();
  
  if (userStore.isLoggedIn) {
    console.log('用户已登录，尝试连接WebSocket');
    connectWebSocket();
  } else {
    console.log('用户未登录，不连接WebSocket');
  }
})

// 切换全屏模式
const toggleFullscreen = () => {
  isFullscreen.value = !isFullscreen.value;
  // 触发滚动到底部，确保消息显示正常
  scrollToBottom();
}

// 组件卸载时关闭WebSocket连接
onUnmounted(() => {
  if (ws.value) {
    ws.value.close();
    ws.value = null;
  }
  // 保存消息到本地存储
  messageStorage.saveChatMessages(messages.value)
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
  height: 300px;
  width: 100%;
  position: relative;
  transition: all 0.3s ease;
}

/* 当组件被集成到其他容器中时，移除边框和阴影 */
.chat-room.embedded {
  border-radius: 0;
  box-shadow: none;
  height: 100%;
}

/* 全屏模式 */
.chat-room.fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  height: 100vh;
  width: 100vw;
  border-radius: 0;
  z-index: 1000;
  box-shadow: none;
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
  display: flex;
  align-items: center;
}

.connection-status {
  font-size: 12px;
  margin-left: 8px;
  opacity: 0.8;
}

.online-count {
  font-size: 12px;
  background-color: rgba(255, 255, 255, 0.2);
  padding: 2px 8px;
  border-radius: 10px;
}

.refresh-btn {
  background: none;
  border: none;
  color: white;
  cursor: pointer;
  margin-left: 5px;
  font-size: 14px;
  padding: 0;
  opacity: 0.8;
  transition: opacity 0.2s;
}

.refresh-btn:hover {
  opacity: 1;
}

.maximize-btn {
  background: none;
  border: none;
  color: white;
  cursor: pointer;
  margin-left: 10px;
  font-size: 14px;
  padding: 0;
  opacity: 0.8;
  transition: opacity 0.2s;
}

.maximize-btn:hover {
  opacity: 1;
}

.refresh-icon {
  font-style: normal;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  background-color: #f9f9f9;
  max-height: 350px; /* 固定消息区域高度 */
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

.message-system {
  align-self: center;
  max-width: 100%;
}

.system-message {
  background-color: rgba(0, 0, 0, 0.05);
  color: #666;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
  border: 2px solid #e0e0e0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.message-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.2s ease;
}

.message-avatar img:hover {
  transform: scale(1.05);
}

.message-content {
  background-color: #ffffff;
  border-radius: 16px;
  padding: 12px 16px;
  position: relative;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border: 1px solid #e0e0e0;
}

.message-mine .message-content {
  background-color: #f0f4ff;
  border-color: #e0e7ff;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
  padding-bottom: 4px;
  border-bottom: 1px solid #f0f0f0;
}

.message-mine .message-header {
  border-bottom-color: #e0e7ff;
}

.message-author {
  font-weight: 600;
  font-size: 13px;
  color: #333333;
  text-transform: capitalize;
}

.message-mine .message-author {
  color: #4361ee;
}

.message-time {
  font-size: 11px;
  color: #999999;
  opacity: 0.8;
}

.message-body {
  font-size: 14px;
  line-height: 1.5;
  word-break: break-word;
  color: #333333;
}

.message-mine .message-body {
  color: #2d3748;
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
  background-color: #4361ee;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  min-width: 80px;
  transition: all 0.2s;
}

.chat-input button:hover:not(:disabled) {
  background-color: #3a56d4;
  transform: translateY(-2px);
}

.chat-input button.loading {
  opacity: 0.8;
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

.login-tip a, .reconnect-btn {
  color: #4361ee;
  text-decoration: none;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 12px;
  padding: 0;
  transition: all 0.2s;
}

.reconnect-btn:hover {
  color: #3a56d4;
  text-decoration: underline;
}

.error-message {
  position: absolute;
  bottom: 60px;
  left: 50%;
  transform: translateX(-50%);
  background-color: rgba(255, 0, 0, 0.1);
  color: #d32f2f;
  padding: 5px 10px;
  border-radius: 4px;
  font-size: 12px;
  display: flex;
  align-items: center;
  z-index: 1;
}

.close-btn {
  background: none;
  border: none;
  color: #d32f2f;
  cursor: pointer;
  margin-left: 8px;
  font-size: 14px;
  padding: 0;
}

.connection-status-bar {
  background-color: #f8f9fa;
  padding: 8px;
  text-align: center;
  font-size: 13px;
  color: #495057;
  border-bottom: 1px solid #e9ecef;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.connecting-spinner {
  display: inline-block;
  width: 12px;
  height: 12px;
  border: 2px solid rgba(67, 97, 238, 0.3);
  border-radius: 50%;
  border-top-color: #4361ee;
  animation: spin 1s ease-in-out infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 用户菜单样式 */
.user-menu {
  position: fixed;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  min-width: 200px;
  max-width: 250px;
  overflow: hidden;
}

.user-menu-header {
  padding: 12px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-menu-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
}

.user-menu-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.user-menu-name {
  font-weight: 600;
  font-size: 14px;
  color: #333;
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-menu-actions {
  padding: 4px 0;
}

.user-menu-action {
  width: 100%;
  padding: 10px 16px;
  border: none;
  background: none;
  text-align: left;
  font-size: 14px;
  color: #333;
  cursor: pointer;
  transition: background-color 0.2s;
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-menu-action:hover {
  background-color: #f5f5f5;
}

.action-icon {
  font-style: normal;
  font-size: 16px;
  font-weight: bold;
  color: #4361ee;
}
</style> 