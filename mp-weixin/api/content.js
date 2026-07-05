// 内容中心 API 模块
import request from './request'

const contentApi = {
  // 内容列表
  getContents(params = {}) {
    return request.get('/content/contents/', params)
  },

  // 内容详情
  getContentDetail(id) {
    return request.get(`/content/contents/${id}/`)
  },

  // 创建内容
  createContent(data) {
    return request.post('/content/contents/', data)
  },

  // 更新内容
  updateContent(id, data) {
    return request.put(`/content/contents/${id}/`, data)
  },

  // 删除内容
  deleteContent(id) {
    return request.delete(`/content/contents/${id}/`)
  },

  // 发布内容
  publishContent(id) {
    return request.post(`/content/contents/${id}/publish/`)
  },

  // 取消发布
  unpublishContent(id) {
    return request.post(`/content/contents/${id}/unpublish/`)
  },

  // 提交审核
  submitContent(id) {
    return request.post(`/content/contents/${id}/submit/`)
  },

  // 我的内容
  getMyContents(params = {}) {
    return request.get('/content/contents/my_contents/', params)
  },

  // 内容类型
  getContentTypes() {
    return request.get('/content/content-types/')
  },

  // 分类列表
  getCategories() {
    return request.get('/content/categories/')
  },

  // 标签列表
  getTags() {
    return request.get('/content/tags/')
  },

  // 评论列表
  getComments(params = {}) {
    return request.get('/content/comments/', params)
  },

  // 创建评论
  createComment(data) {
    return request.post('/content/comments/', data)
  }
}

export default contentApi
