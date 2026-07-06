import request from '@/utils/request'
import type { FeedResponse, FeedParams, TrendingTopic } from '@/types/feed'

export const feedApi = {
  getFeed(params: FeedParams) {
    return request.get<FeedResponse>('/feed/feed/', { params })
  },

  getTrendingTopics() {
    return request.get<TrendingTopic[]>('/feed/trending_topics/')
  }
}
