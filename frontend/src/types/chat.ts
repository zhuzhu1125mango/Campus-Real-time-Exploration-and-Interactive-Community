import type { User } from './user'

/** 公共聊天室消息 */
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

/** 在线用户统计 */
export interface OnlineUsers {
  count: number
  metric: string
  window_seconds?: number
}

/** 私信消息 */
export interface PrivateMessage {
  id: number
  sender: User
  receiver: User
  content: string
  is_read: boolean
  is_recalled: boolean
  recalled_at?: string | null
  created_at: string
  updated_at: string
}

/** 私信会话 */
export interface Conversation {
  user: User
  last_message: PrivateMessage | null
  unread_count: number
}

/** 与特定用户的对话详情 */
export interface ConversationDetail {
  user: User
  messages: PrivateMessage[]
  unread_count: number
  count: number
  next: number | null
  previous: number | null
}

/** 发送私信请求体 */
export interface SendPrivateMessageData {
  content: string
}
