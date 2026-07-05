import request from '../utils/request'
import type { Course } from '../types/learning'
import type { ContentItem } from '../types/content'
import type { Topic, Post } from '../types/forum'
import type { School } from '../types/school'

export type SearchType = 'all' | 'course' | 'content' | 'school' | 'topic' | 'post'

export interface SearchSuggestion {
  type: SearchType
  id: number
  title: string
  slug?: string
}

export interface SearchResults {
  courses?: Course[]
  contents?: ContentItem[]
  schools?: School[]
  topics?: Topic[]
  posts?: Post[]
}

export interface SearchResponse {
  query: string
  type: SearchType
  results: SearchResults
}

export const searchApi = {
  search(q: string, type: SearchType = 'all', limit = 20): Promise<SearchResponse> {
    return request.get('/search/', { params: { q, type, limit } })
  },

  getSuggestions(q: string): Promise<{ query: string; suggestions: SearchSuggestion[] }> {
    return request.get('/search/suggestions/', { params: { q } })
  }
}
