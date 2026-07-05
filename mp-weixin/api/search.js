// 搜索 API 模块
import request from './request'

const searchApi = {
  // 全局聚合搜索
  search(q, type = 'all', limit = 20) {
    return request.get('/search/', { q, type, limit })
  },

  // 搜索建议
  getSuggestions(q) {
    return request.get('/search/suggestions/', { q })
  }
}

export default searchApi
