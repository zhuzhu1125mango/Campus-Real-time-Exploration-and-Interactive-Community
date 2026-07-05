import request from './request'

// 论坛相关API
const forumApi = {
  /**
   * 获取帖子列表
   * @param {Object} params - 查询参数
   * @param {number} params.board - 板块ID
   * @param {string} params.ordering - 排序方式
   * @param {number} params.page - 页码
   * @param {number} params.page_size - 每页数量
   * @returns {Promise} 帖子列表
   */
  getPosts: (params) => {
    return request.get('/posts/', params)
  },

  /**
   * 获取帖子详情
   * @param {number} id - 帖子ID
   * @returns {Promise} 帖子详情
   */
  getPostDetail: (id) => {
    return request.get(`/posts/${id}/`)
  },

  /**
   * 创建帖子
   * @param {Object} data - 帖子数据
   * @param {number} data.topic - 主题ID
   * @param {string} data.content - 内容
   * @returns {Promise} 创建结果
   */
  createPost: (data) => {
    return request.post('/posts/', data)
  },

  /**
   * 更新帖子
   * @param {number} id - 帖子ID
   * @param {Object} data - 帖子数据
   * @returns {Promise} 更新结果
   */
  updatePost: (id, data) => {
    return request.put(`/posts/${id}/`, data)
  },

  /**
   * 删除帖子
   * @param {number} id - 帖子ID
   * @returns {Promise} 删除结果
   */
  deletePost: (id) => {
    return request.delete(`/posts/${id}/`)
  },

  /**
   * 点赞帖子
   * @param {number} postId - 帖子ID
   * @returns {Promise} 点赞结果
   */
  likePost: (postId) => {
    return request.post(`/posts/${postId}/like/`)
  },

  /**
   * 取消点赞
   * @param {number} postId - 帖子ID
   * @returns {Promise} 取消点赞结果
   */
  unlikePost: (postId) => {
    return request.delete(`/posts/${postId}/unlike/`)
  },

  /**
   * 获取评论列表
   * @param {number} postId - 帖子ID
   * @returns {Promise} 评论列表
   */
  getComments: (postId) => {
    return request.get('/comments/', { post: postId })
  },

  /**
   * 发表评论
   * @param {number} postId - 帖子ID
   * @param {Object} data - 评论数据
   * @param {string} data.content - 评论内容
   * @param {number} data.parent - 父评论ID（可选）
   * @returns {Promise} 发表结果
   */
  createComment: (postId, data) => {
    return request.post('/comments/', {
      post: postId,
      content: data.content,
      parent: data.parent || null
    })
  },

  /**
   * 获取分类列表
   * @returns {Promise} 分类列表
   */
  getCategories: () => {
    return request.get('/categories/')
  },

  /**
   * 获取板块列表
   * @returns {Promise} 板块列表
   */
  getBoards: (params) => {
    return request.get('/boards/', params)
  },

  /**
   * 获取主题列表
   * @param {Object} params - 查询参数
   * @returns {Promise} 主题列表
   */
  getTopics: (params) => {
    return request.get('/topics/', params)
  },

  /**
   * 获取主题详情
   * @param {number} id - 主题ID
   * @returns {Promise} 主题详情
   */
  getTopicDetail: (id) => {
    return request.get(`/topics/${id}/`)
  },

  /**
   * 创建主题
   * @param {Object} data - 主题数据
   * @param {string} data.title - 标题
   * @param {number} data.board - 板块ID
   * @param {string} data.content - 内容
   * @param {Array} data.tags - 标签数组
   * @returns {Promise} 创建结果
   */
  createTopic: (data) => {
    return request.post('/topics/', data)
  },

  /**
   * 获取主题内的帖子列表
   * @param {number} topicId - 主题ID
   * @param {Object} params - 查询参数
   * @returns {Promise} 帖子列表
   */
  getTopicPosts: (topicId, params = {}) => {
    return request.get(`/topics/${topicId}/posts/`, params)
  },

  /**
   * 回复主题
   * @param {Object} data - 回复数据
   * @param {number} data.topic - 主题ID
   * @param {string} data.content - 回复内容
   * @returns {Promise} 创建结果
   */
  replyTopic: (data) => {
    return request.post('/posts/', data)
  },

  /**
   * 获取热门话题
   * @param {Object} params - 查询参数
   * @param {number} params.days - 时间范围（天）
   * @param {number} params.limit - 数量限制
   * @returns {Promise} 热门话题列表
   */
  getHotTopics: (params) => {
    return request.get('/hot-topics/', params)
  },

  /**
   * 收藏主题
   * @param {number} topicId - 主题ID
   * @returns {Promise} 收藏结果
   */
  bookmarkTopic: (topicId) => {
    return request.post(`/topics/${topicId}/bookmark/`)
  },

  /**
   * 取消收藏主题
   * @param {number} topicId - 主题ID
   * @returns {Promise} 取消收藏结果
   */
  unbookmarkTopic: (topicId) => {
    return request.delete(`/topics/${topicId}/unbookmark/`)
  },

  /**
   * 获取论坛统计数据
   * @returns {Promise} 论坛统计
   */
  getStats: () => {
    return request.get('/stats/')
  },

  /**
   * 获取我的收藏主题
   * @returns {Promise} 收藏主题列表
   */
  getMyBookmarks: () => {
    return request.get('/my-bookmarks/')
  }
}

export default forumApi
