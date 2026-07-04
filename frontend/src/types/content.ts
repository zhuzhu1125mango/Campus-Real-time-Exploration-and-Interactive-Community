import type { User } from './user'

export interface ContentType {
  id: number
  name: string
  description?: string
  is_active?: boolean
  created_at?: string
  updated_at?: string
}

export interface Category {
  id: number
  name: string
  parent?: string | null
  description?: string
  order?: number
  is_active?: boolean
  created_at?: string
  updated_at?: string
}

export interface Tag {
  id: number
  name: string
  description?: string
  created_at?: string
  updated_at?: string
}

export interface ContentItem {
  id: number
  title: string
  slug: string
  content_type: ContentType
  category: Category | null
  tags: Tag[]
  author: User
  content: string
  summary: string
  featured_image: string | null
  is_published: boolean
  publish_date: string | null
  view_count: number
  comment_count: number
  like_count: number
  created_at: string
  updated_at: string
}

export interface Comment {
  id: number
  content: string
  user: User
  parent: number | null
  content_text: string
  is_approved: boolean
  created_at: string
  updated_at: string
}

export interface ContentCreateData {
  title: string
  slug?: string
  content_type: number
  category?: number | null
  tags?: number[]
  content: string
  summary?: string
  featured_image?: File | null
  is_published?: boolean
}
