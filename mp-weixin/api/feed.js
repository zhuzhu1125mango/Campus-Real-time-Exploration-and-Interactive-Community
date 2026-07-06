import request from './request'

// Feed 流相关 API
const feedApi = {
  /**
   * 获取统一 Feed 流
   * @param {Object} params - 查询参数
   * @param {string} params.type - 类型：recommend/following/nearby
   * @param {number} params.page - 页码
   * @param {number} params.page_size - 每页数量
   * @param {number} [params.lat] - 附近类型必填：纬度
   * @param {number} [params.lng] - 附近类型必填：经度
   * @param {number} [params.radius] - 附近类型可选：半径（km）
   * @returns {Promise} Feed 列表
   */
  getFeed: (params) => {
    return request.get('/feed/feed/', params)
  },

  /**
   * 获取热门话题/标签
   * @returns {Promise} 热门话题列表
   */
  getTrendingTopics: () => {
    return request.get('/feed/trending_topics/')
  }
}

export default feedApi
