<template>
  <div class="messages-container">
    <div class="messages-sidebar">
      <h2 class="sidebar-title">私信</h2>
      
      <!-- 搜索框 -->
      <div class="search-box">
        <input 
          v-model="searchQuery" 
          type="text" 
          placeholder="搜索联系人..."
          class="search-input"
        />
      </div>
      
      <!-- 对话列表 -->
      <div class="conversation-list">
        <div v-if="loading" class="loading-container">
          <div class="loading-spinner"></div>
          <p>加载中...</p>
        </div>
        
        <div v-else-if="filteredConversations.length === 0" class="empty-conversations">
          暂无私信
        </div>
        
        <div 
          v-for="conv in filteredConversations" 
          :key="conv.user.id"
          class="conversation-item"
          @click="goToChat(conv.user.id)"
        >
          <div class="avatar-wrapper">
            <img
              v-if="conv.user.avatar"
              :src="getAvatarUrl(conv.user.avatar)"
              alt="avatar"
              class="avatar"
              @error="($event.target as HTMLImageElement).src = `${config.media.baseUrl}${config.media.defaultAvatar}`"
            />
            <div v-else class="avatar-placeholder">{{ conv.user.username.substring(0, 1) }}</div>
            <span v-if="conv.unread_count > 0" class="unread-badge">{{ conv.unread_count }}</span>
          </div>
          <div class="conversation-info">
            <div class="conversation-name">{{ conv.user.username }}</div>
            <div class="conversation-preview">
              {{ getMessagePreview(conv.last_message?.content) }}
            </div>
          </div>
          <div class="conversation-meta">
            <div class="conversation-time">{{ formatTime(conv.last_message?.created_at) }}</div>
          </div>
        </div>
      </div>
    </div>
    
    <div class="messages-content">
      <div class="empty-content">
        <div class="empty-icon"></div>
        <p>选择一个对话开始聊天</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { userApi } from '@/api/user'
import config from '@/utils/config'
import type { User } from '@/types/user'

interface LastMessage {
  content: string
  created_at: string
}

interface Conversation {
  user: User
  last_message: LastMessage | null
  unread_count: number
}

const router = useRouter()

const conversations = ref<Conversation[]>([])
const searchQuery = ref('')
const loading = ref(false)
let intervalId: number

const filteredConversations = computed(() => {
  if (!searchQuery.value) return conversations.value
  const query = searchQuery.value.toLowerCase()
  return conversations.value.filter(conv => 
    conv.user.username.toLowerCase().includes(query)
  )
})

const fetchConversations = async () => {
  loading.value = true
  try {
    const response = await userApi.getConversations()
    conversations.value = response || []
  } catch (error) {
    console.error('获取对话列表失败:', error)
  } finally {
    loading.value = false
  }
}

const goToChat = (userId: number) => {
  router.push(`/chat/${userId}`)
}

const getMessagePreview = (content?: string) => {
  if (!content) return ''
  if (content.length > 30) {
    return content.substring(0, 30) + '...'
  }
  return content
}

const getAvatarUrl = (avatar?: string | null) => {
  if (!avatar) return `${config.media.baseUrl}${config.media.defaultAvatar}`
  if (avatar.startsWith('http')) return avatar
  return `${config.media.baseUrl}${avatar}`
}

const formatTime = (dateStr?: string) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  if (diff < 24 * 60 * 60 * 1000) {
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }
  
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

onMounted(() => {
  fetchConversations()
  intervalId = window.setInterval(fetchConversations, 30000)
})

onUnmounted(() => {
  clearInterval(intervalId)
})
</script>

<style scoped>
.messages-container {
  display: flex;
  height: calc(100vh - 60px);
  max-width: 1200px;
  margin: 0 auto;
  background-color: #f5f5f5;
}

.messages-sidebar {
  width: 320px;
  background-color: white;
  border-right: 1px solid #e0e0e0;
  display: flex;
  flex-direction: column;
}

.sidebar-title {
  padding: 1.2rem 1rem;
  font-size: 1.2rem;
  font-weight: 600;
  border-bottom: 1px solid #e0e0e0;
  margin: 0;
}

.search-box {
  padding: 0.8rem 1rem;
  border-bottom: 1px solid #e0e0e0;
}

.search-input {
  width: 100%;
  padding: 0.6rem 0.8rem;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  font-size: 0.9rem;
  box-sizing: border-box;
}

.search-input:focus {
  outline: none;
  border-color: #4361ee;
  box-shadow: 0 0 0 3px rgba(67, 97, 238, 0.1);
}

.conversation-list {
  flex: 1;
  overflow-y: auto;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  color: #888;
}

.loading-spinner {
  width: 24px;
  height: 24px;
  border: 2px solid rgba(67, 97, 238, 0.3);
  border-radius: 50%;
  border-top-color: #4361ee;
  animation: spin 1s linear infinite;
  margin-bottom: 0.5rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-conversations {
  text-align: center;
  padding: 3rem;
  color: #999;
}

.conversation-item {
  display: flex;
  align-items: center;
  padding: 1rem;
  cursor: pointer;
  transition: background-color 0.2s;
  border-bottom: 1px solid #f0f0f0;
}

.conversation-item:hover {
  background-color: #f8f9fa;
}

.avatar-wrapper {
  position: relative;
  margin-right: 1rem;
  flex-shrink: 0;
}

.avatar,
.avatar-placeholder {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  overflow: hidden;
}

.avatar-placeholder {
  background-color: #4361ee;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 1.2rem;
}

.unread-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  background-color: #ef4444;
  color: white;
  font-size: 0.7rem;
  padding: 0.15rem 0.4rem;
  border-radius: 10px;
  min-width: 18px;
  text-align: center;
}

.conversation-info {
  flex: 1;
  overflow: hidden;
}

.conversation-name {
  font-weight: 600;
  font-size: 0.95rem;
  margin-bottom: 0.2rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.conversation-preview {
  font-size: 0.85rem;
  color: #666;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.conversation-meta {
  flex-shrink: 0;
  margin-left: 0.5rem;
}

.conversation-time {
  font-size: 0.8rem;
  color: #999;
  white-space: nowrap;
}

.messages-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: #f5f5f5;
}

.empty-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #999;
}

.empty-icon {
  width: 60px;
  height: 60px;
  margin-bottom: 1rem;
  opacity: 0.3;
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%234361ee"><path d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/></svg>');
  background-repeat: no-repeat;
  background-position: center;
}

@media (max-width: 768px) {
  .messages-sidebar {
    width: 100%;
  }
  
  .messages-content {
    display: none;
  }
}
</style>
