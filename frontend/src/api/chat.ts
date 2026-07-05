import request from '../utils/request'

export interface ChatMessage {
  id: number
  content: string
  created_at: string
  user: {
    id: number
    username: string
    avatar: string | null
  }
}

export interface OnlineUsers {
  count: number
  metric: string
  window_seconds?: number
}

export const chatApi = {
  // 获取最近的公共聊天室消息
  getRecentMessages(): Promise<ChatMessage[]> {
    return request.get('/chat/messages/recent_messages/')
  },

  // 获取在线用户数量
  getOnlineUsers(): Promise<OnlineUsers> {
    return request.get('/chat/messages/online_users/')
  },

  // 通过 HTTP 发送公共聊天室消息
  sendMessage(content: string): Promise<ChatMessage> {
    return request.post('/chat/send_message/', { content })
  }
}
