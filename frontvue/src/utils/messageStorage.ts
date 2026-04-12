import { onMounted, onUnmounted } from 'vue'

// 消息存储键名
const CHAT_MESSAGES_KEY = 'chat_messages'
const PRIVATE_MESSAGES_KEY = 'private_messages'
const MESSAGE_EXPIRY_DAYS = 7 // 消息保留天数

// 消息类型定义
export interface ChatMessage {
  id: number
  content: string
  type: 'chat' | 'system'
  user?: {
    id: number
    username: string
    avatar?: string
  }
  time: string
  clientId?: number
}

export interface PrivateMessage {
  id: number
  content: string
  sender: {
    id: number
    username: string
    avatar?: string
  }
  receiver: {
    id: number
    username: string
    avatar?: string
  }
  created_at: string
  is_read?: boolean
}

// 本地存储工具类
class MessageStorage {
  // 保存实时聊天室消息
  saveChatMessages(messages: ChatMessage[]): void {
    try {
      const data = {
        messages,
        timestamp: Date.now()
      }
      localStorage.setItem(CHAT_MESSAGES_KEY, JSON.stringify(data))
    } catch (error) {
      console.error('保存聊天室消息失败:', error)
    }
  }

  // 获取实时聊天室消息
  getChatMessages(): ChatMessage[] {
    try {
      const dataStr = localStorage.getItem(CHAT_MESSAGES_KEY)
      if (!dataStr) return []

      const data = JSON.parse(dataStr)
      const timestamp = data.timestamp
      const messages = data.messages

      // 检查消息是否过期
      if (this.isExpired(timestamp)) {
        this.clearChatMessages()
        return []
      }

      return messages
    } catch (error) {
      console.error('获取聊天室消息失败:', error)
      return []
    }
  }

  // 清除实时聊天室消息
  clearChatMessages(): void {
    try {
      localStorage.removeItem(CHAT_MESSAGES_KEY)
    } catch (error) {
      console.error('清除聊天室消息失败:', error)
    }
  }

  // 保存私信消息
  savePrivateMessages(userId: number, messages: PrivateMessage[]): void {
    try {
      const key = `${PRIVATE_MESSAGES_KEY}_${userId}`
      const data = {
        messages,
        timestamp: Date.now()
      }
      localStorage.setItem(key, JSON.stringify(data))
    } catch (error) {
      console.error('保存私信消息失败:', error)
    }
  }

  // 获取私信消息
  getPrivateMessages(userId: number): PrivateMessage[] {
    try {
      const key = `${PRIVATE_MESSAGES_KEY}_${userId}`
      const dataStr = localStorage.getItem(key)
      if (!dataStr) return []

      const data = JSON.parse(dataStr)
      const timestamp = data.timestamp
      const messages = data.messages

      // 检查消息是否过期
      if (this.isExpired(timestamp)) {
        this.clearPrivateMessages(userId)
        return []
      }

      return messages
    } catch (error) {
      console.error('获取私信消息失败:', error)
      return []
    }
  }

  // 清除私信消息
  clearPrivateMessages(userId: number): void {
    try {
      const key = `${PRIVATE_MESSAGES_KEY}_${userId}`
      localStorage.removeItem(key)
    } catch (error) {
      console.error('清除私信消息失败:', error)
    }
  }

  // 检查是否过期
  private isExpired(timestamp: number): boolean {
    const now = Date.now()
    const expiryTime = MESSAGE_EXPIRY_DAYS * 24 * 60 * 60 * 1000
    return now - timestamp > expiryTime
  }

  // 清理所有过期消息
  cleanupExpiredMessages(): void {
    try {
      // 清理聊天室消息
      const chatDataStr = localStorage.getItem(CHAT_MESSAGES_KEY)
      if (chatDataStr) {
        const chatData = JSON.parse(chatDataStr)
        if (this.isExpired(chatData.timestamp)) {
          this.clearChatMessages()
        }
      }

      // 清理私信消息
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i)
        if (key && key.startsWith(PRIVATE_MESSAGES_KEY)) {
          const dataStr = localStorage.getItem(key)
          if (dataStr) {
            const data = JSON.parse(dataStr)
            if (this.isExpired(data.timestamp)) {
              localStorage.removeItem(key)
            }
          }
        }
      }
    } catch (error) {
      console.error('清理过期消息失败:', error)
    }
  }

  // 获取存储使用情况
  getStorageUsage(): {
    total: number
    used: number
    percentage: number
  } {
    try {
      let totalSize = 0
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i)
        const value = localStorage.getItem(key!)
        if (key && value) {
          totalSize += key.length + value.length
        }
      }

      // 估算localStorage总容量（通常为5MB）
      const totalCapacity = 5 * 1024 * 1024
      const used = totalSize
      const percentage = (used / totalCapacity) * 100

      return {
        total: totalCapacity,
        used,
        percentage
      }
    } catch (error) {
      console.error('获取存储使用情况失败:', error)
      return {
        total: 5 * 1024 * 1024,
        used: 0,
        percentage: 0
      }
    }
  }
}

// 导出单例实例
export const messageStorage = new MessageStorage()

// 定期清理过期消息
export function useMessageStorageCleanup() {
  onMounted(() => {
    // 初始化时清理
    messageStorage.cleanupExpiredMessages()

    // 每小时清理一次
    const cleanupInterval = setInterval(() => {
      messageStorage.cleanupExpiredMessages()
    }, 60 * 60 * 1000)

    onUnmounted(() => {
      clearInterval(cleanupInterval)
    })
  })
}
