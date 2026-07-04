import request from '../utils/request'
import type { ContentItem, ContentType, Category, Tag, Comment } from '../types/content'

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export const contentApi = {
  // 内容相关API
  getContents(params?: {
    page?: number
    search?: string
    ordering?: string
    category?: number | string
    content_type?: number | string
    is_published?: boolean | string
  }): Promise<PaginatedResponse<ContentItem>> {
    return request.get('/content/contents/', { params })
  },

  getContentDetail(id: number | string): Promise<ContentItem> {
    return request.get(`/content/contents/${id}/`)
  },

  createContent(data: FormData | Record<string, any>): Promise<ContentItem> {
    const headers = data instanceof FormData ? { 'Content-Type': 'multipart/form-data' } : undefined
    return request.post('/content/contents/', data, { headers })
  },

  updateContent(id: number | string, data: FormData | Record<string, any>): Promise<ContentItem> {
    const headers = data instanceof FormData ? { 'Content-Type': 'multipart/form-data' } : undefined
    return request.put(`/content/contents/${id}/`, data, { headers })
  },

  deleteContent(id: number | string): Promise<void> {
    return request.delete(`/content/contents/${id}/`)
  },

  publishContent(id: number | string): Promise<{ status: string }> {
    return request.post(`/content/contents/${id}/publish/`)
  },

  unpublishContent(id: number | string): Promise<{ status: string }> {
    return request.post(`/content/contents/${id}/unpublish/`)
  },

  getMyContents(): Promise<ContentItem[]> {
    return request.get('/content/contents/my_contents/')
  },

  // 内容类型API
  getContentTypes(): Promise<PaginatedResponse<ContentType>> {
    return request.get('/content/content-types/')
  },

  // 分类API
  getCategories(): Promise<PaginatedResponse<Category>> {
    return request.get('/content/categories/')
  },

  // 标签API
  getTags(): Promise<PaginatedResponse<Tag>> {
    return request.get('/content/tags/')
  },

  // 评论API
  getComments(params?: { content?: number | string; page?: number }): Promise<PaginatedResponse<Comment>> {
    return request.get('/content/comments/', { params })
  },

  createComment(data: { content: number | string; parent?: number | null; content_text: string }): Promise<Comment> {
    return request.post('/content/comments/', data)
  }
}
