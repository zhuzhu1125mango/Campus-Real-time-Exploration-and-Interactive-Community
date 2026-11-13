<template>
  <div class="messages-container">
    <div class="messages-sidebar">
      <SectionHeader title="私信" icon="i-ep-chat-round" class="sidebar-header" />

      <!-- 搜索框 -->
      <GlassCard :hover="false" class="search-card" padding="sm">
        <div class="search-box">
          <span class="i-ep-search search-icon" />
          <input
            v-model="searchQuery"
            type="text"
            placeholder="搜索联系人..."
            class="search-input"
          />
          <button v-if="searchQuery" class="clear-btn" @click="searchQuery = ''">
            <span class="i-ep-close" />
          </button>
        </div>
      </GlassCard>

      <!-- 对话列表 -->
      <GlassCard :hover="false" class="conversation-card" padding="none">
        <div class="conversation-list">
          <div v-if="loading && conversations.length === 0" class="loading-container">
            <div class="loading-spinner"></div>
            <p>加载中...</p>
          </div>

          <div v-else-if="filteredConversations.length === 0" class="empty-conversations">
            <div class="empty-icon">
              <span class="i-ep-chat-round" />
            </div>
            <p v-if="searchQuery">未找到匹配的联系人</p>
            <template v-else>
              <p>暂无私信</p>
              <button class="btn btn-primary" @click="goToFriends">去添加好友</button>
            </template>
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
                :src="formatAvatar(conv.user.avatar)"
                alt="avatar"
                class="avatar"
                @error="($event.target as HTMLImageElement).src = formatAvatar()"
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
      </GlassCard>
    </div>

    <div class="messages-content">
      <GlassCard :hover="false" class="empty-card" padding="lg">
        <div class="empty-content">
          <div class="empty-icon">
            <span class="i-ep-chat-round" />
          </div>
          <p>选择一个对话开始聊天</p>
        </div>
      </GlassCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { userApi } from '@/api/user'
import { useToast } from '@/composables/useToast'
import { formatAvatar } from '@/utils/image'
import GlassCard from '@/components/GlassCard.vue'
import SectionHeader from '@/components/SectionHeader.vue'
import type { Conversation } from '@/types/chat'

const router = useRouter()
const { showToast } = useToast()

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

const goToChat = async (userId: number) => {
  try {
    const { is_friend } = await userApi.checkFriendship(userId)
    if (!is_friend) {
      showToast('你们还不是好友，请先添加好友', 'warning')
      router.push(`/friends?add=${userId}`)
      return
    }
    router.push(`/chat/${userId}`)
  } catch (error) {
    console.error('检查好友关系失败:', error)
    showToast('无法建立私聊，请稍后再试', 'error')
  }
}

const goToFriends = () => {
  router.push('/friends')
}

const getMessagePreview = (content?: string) => {
  if (!content) return ''
  if (content.length > 30) {
    return content.substring(0, 30) + '...'
  }
  return content
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
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-xl);
  box-shadow: var(--glass-shadow);
  backdrop-filter: blur(12px) saturate(180%);
  -webkit-backdrop-filter: blur(12px) saturate(180%);
  overflow: hidden;
}

.messages-sidebar {
  width: 320px;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  padding: var(--space-4);
  border-right: 1px solid var(--glass-border);
}

.sidebar-header {
  margin-bottom: 0;
  flex-shrink: 0;
}

.search-card {
  flex-shrink: 0;
}

.search-box {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.search-icon {
  width: 18px;
  height: 18px;
  color: var(--text-tertiary);
  flex-shrink: 0;
}

.search-input {
  flex: 1;
  padding: var(--space-2) 0;
  border: none;
  font-size: 0.9rem;
  outline: none;
  color: var(--text-primary);
  background: transparent;
}

.search-input::placeholder {
  color: var(--text-tertiary);
}

.clear-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  color: var(--text-tertiary);
  cursor: pointer;
  background: transparent;
  transition: color 0.2s, background-color 0.2s;
}

.clear-btn:hover {
  color: var(--text-secondary);
  background: var(--bg-tertiary);
}

.clear-btn span {
  width: 12px;
  height: 12px;
}

.conversation-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.conversation-card :deep(.glass-card-body) {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
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
  padding: var(--space-10);
  color: var(--text-tertiary);
}

.loading-spinner {
  width: 24px;
  height: 24px;
  border: 2px solid var(--primary-200);
  border-radius: 50%;
  border-top-color: var(--primary-500);
  animation: spin 1s linear infinite;
  margin-bottom: var(--space-2);
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-conversations {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--space-10) var(--space-4);
  color: var(--text-tertiary);
  text-align: center;
}

.empty-conversations p {
  margin-bottom: var(--space-3);
}

.empty-icon {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: var(--primary-50);
  color: var(--primary-500);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: var(--space-3);
}

.empty-icon span {
  width: 28px;
  height: 28px;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.625rem 1.25rem;
  border-radius: var(--radius-md);
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: all 0.2s;
}

.btn-primary {
  background-color: var(--primary-600);
  color: white;
}

.btn-primary:hover {
  background-color: var(--primary-700);
}

.btn-secondary {
  background-color: var(--bg-tertiary);
  color: var(--text-primary);
}

.btn-secondary:hover:not(:disabled) {
  background-color: var(--border-color);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.conversation-item {
  display: flex;
  align-items: center;
  padding: var(--space-3) var(--space-4);
  cursor: pointer;
  transition: background-color 0.2s;
  border-bottom: 1px solid var(--border-color-light);
}

.conversation-item:hover {
  background-color: var(--bg-secondary);
}

.avatar-wrapper {
  position: relative;
  margin-right: var(--space-3);
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
  background-color: var(--primary-500);
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
  background-color: var(--error-color);
  color: white;
  font-size: 0.7rem;
  padding: 0.15rem 0.4rem;
  border-radius: var(--radius-full);
  min-width: 18px;
  text-align: center;
  box-shadow: var(--shadow-sm);
  font-weight: 600;
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
  color: var(--text-primary);
}

.conversation-preview {
  font-size: 0.85rem;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.conversation-meta {
  flex-shrink: 0;
  margin-left: var(--space-2);
}

.conversation-time {
  font-size: 0.8rem;
  color: var(--text-tertiary);
  white-space: nowrap;
}

.messages-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: var(--space-4);
}

.empty-card {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.empty-card :deep(.glass-card-body) {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.empty-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-tertiary);
}

.empty-content .empty-icon {
  width: 72px;
  height: 72px;
  margin-bottom: var(--space-4);
}

.empty-content .empty-icon span {
  width: 36px;
  height: 36px;
}

@media (max-width: 768px) {
  .messages-sidebar {
    width: 100%;
    border-right: none;
  }

  .messages-content {
    display: none;
  }
}
</style>
