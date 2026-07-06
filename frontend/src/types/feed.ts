export type FeedObjectType = 'topic' | 'content' | 'activity' | 'event'

export interface FeedAuthor {
  id: number
  username: string
  avatar?: string | null
}

export interface FeedMeta {
  // topic
  board_name?: string | null
  reply_count?: number
  view_count?: number
  // content
  content_type?: string | null
  comment_count?: number
  like_count?: number
  // activity
  activity_type?: string
  likes_count?: number
  comments_count?: number
  target_url?: string
  // event
  location?: string
  start_time?: string
  status?: string
}

export interface FeedItem {
  id: string
  object_type: FeedObjectType
  object_id: number
  title: string
  content: string
  author: FeedAuthor
  images: string[]
  meta: FeedMeta
  created_at: string
}

export interface FeedResponse {
  results: FeedItem[]
  count: number
  page: number
  page_size: number
  type: string
}

export type FeedType = 'recommend' | 'following' | 'nearby'

export interface FeedParams {
  type?: FeedType
  page?: number
  page_size?: number
  lat?: number
  lng?: number
  radius?: number
}

export interface TrendingTopic {
  id: string
  type: 'forum_tag' | 'content_tag'
  name: string
  description?: string
  count: number
}
