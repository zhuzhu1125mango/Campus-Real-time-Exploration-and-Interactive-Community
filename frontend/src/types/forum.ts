import type { User } from './user'

export interface Tag {
  id: number
  name: string
  slug: string
  description?: string
  created_at: string
}

export interface Category {
  id: number
  name: string
  description: string
  icon?: string
  created_at: string
  updated_at: string
}

export interface Board {
  id: number
  category: number
  name: string
  description: string
  icon?: string
  topic_count: number
  post_count: number
  last_post?: Post
  created_at: string
  updated_at: string
}

export interface Topic {
  id: number
  board: number
  board_name?: string
  title: string
  author: User
  status: string
  views: number
  is_closed: boolean
  post_count: number
  reply_count?: number
  last_post?: Post
  created_at: string
  updated_at: string
  tags?: Tag[]
}

export interface Post {
  id: number
  topic: number
  title?: string
  author: User
  content: string
  is_first_post: boolean
  is_edited: boolean
  edited_at?: string
  content_status?: string
  review_note?: string
  like_count: number
  is_liked?: boolean
  created_at: string
  updated_at: string
}

export interface Notification {
  id: number
  user: number
  sender?: User
  notification_type: string
  content: string
  post?: number
  is_read: boolean
  created_at: string
}

export interface ForumStats {
  user_count: number
  topic_count: number
  post_count: number
  today_post_count: number
  category_count: number
  board_count: number
}

export interface CategoryListResponse {
  count: number
  next: string | null
  previous: string | null
  results: Category[]
}

export interface BoardListResponse {
  count: number
  next: string | null
  previous: string | null
  results: Board[]
}

export interface TopicListResponse {
  count: number
  next: string | null
  previous: string | null
  results: Topic[]
}

export interface PostListResponse {
  count: number
  next: string | null
  previous: string | null
  results: Post[]
}

export interface NotificationListResponse {
  count: number
  next: string | null
  previous: string | null
  results: Notification[]
}

export interface BookmarkListResponse {
  count: number
  next: string | null
  previous: string | null
  results: Topic[]
}

export interface Bookmark {
  id: number
  user: number
  topic: number
  created_at: string
}

export interface Comment {
  id: number
  post: number
  author: User
  content: string
  parent?: number
  like_count: number
  created_at: string
  updated_at: string
} 