import request from './request'

// 用户相关API
const userApi = {
  /**
   * 用户登录
   * @param {Object} data - 登录参数
   * @param {string} data.username - 用户名/邮箱/手机号
   * @param {string} data.password - 密码
   * @returns {Promise} 登录结果
   */
  login: (data) => {
    return request.post('/users/users/login/', data)
  },

  /**
   * 用户注册
   * @param {Object} data - 注册参数
   * @param {string} data.username - 用户名
   * @param {string} data.email - 邮箱
   * @param {string} data.phone - 手机号
   * @param {string} data.password - 密码
   * @param {string} data.password_confirm - 确认密码
   * @param {string} data.code - 验证码
   * @returns {Promise} 注册结果
   */
  register: (data) => {
    return request.post('/users/users/', data)
  },

  /**
   * 发送邮箱验证码
   * @param {Object} data - 请求参数
   * @param {string} data.email - 邮箱
   * @param {string} data.purpose - 用途（register/login）
   * @returns {Promise} 发送结果
   */
  sendEmailCode: (data) => {
    return request.post('/users/email-code/', data)
  },

  /**
   * 发送手机验证码
   * @param {Object} data - 请求参数
   * @param {string} data.phone - 手机号
   * @param {string} data.purpose - 用途（register/login）
   * @returns {Promise} 发送结果
   */
  sendPhoneCode: (data) => {
    return request.post('/users/phone-code/', data)
  },

  /**
   * 获取用户信息
   * @returns {Promise} 用户信息
   */
  getUserInfo: () => {
    return request.get('/users/users/me/')
  },

  /**
   * 退出登录
   * @returns {Promise} 退出结果
   */
  logout: () => {
    return request.post('/users/users/logout/')
  },

  /**
   * 微信登录
   * @param {Object} data - 登录参数
   * @param {string} data.code - 微信code
   * @returns {Promise} 登录结果
   */
  wechatLogin: (data) => {
    return request.post('/users/users/wechat_login/', data)
  },

  /**
   * 刷新token
   * @param {Object} data - 刷新参数
   * @param {string} data.refresh - 刷新token
   * @returns {Promise} 刷新结果
   */
  refreshToken: (data) => {
    return request.post('/token/refresh/', data)
  },

  /**
   * 重置密码
   * @param {Object} data - 重置参数
   * @param {string} [data.phone] - 手机号
   * @param {string} [data.email] - 邮箱
   * @param {string} data.code - 验证码
   * @param {string} data.password - 新密码
   * @param {string} data.password_confirm - 确认密码
   * @returns {Promise} 重置结果
   */
  resetPassword: (data) => {
    return request.post('/users/reset-password/', data)
  },

  /**
   * 获取用户资料
   * @param {number|string} userId - 用户ID，传 'me' 获取当前用户
   * @returns {Promise} 用户资料
   */
  getUserProfile: (userId) => {
    return request.get(`/users/users/${userId}/`)
  },

  /**
   * 获取用户资料统计
   * @param {number|string} userId - 用户ID，传 'me' 获取当前用户
   * @returns {Promise} 统计信息
   */
  getUserProfileStats: (userId) => {
    return request.get(`/users/users/${userId}/profile_stats/`)
  },

  /**
   * 获取用户创建的主题
   * @param {number|string} userId - 用户ID
   * @param {number} page - 页码
   * @returns {Promise} 主题列表
   */
  getUserTopics: (userId, page = 1) => {
    return request.get(`/users/users/${userId}/topics/`, { page })
  },

  /**
   * 获取用户的帖子和回复
   * @param {number|string} userId - 用户ID
   * @param {number} page - 页码
   * @param {boolean} includeFirst - 是否包含首贴
   * @returns {Promise} 帖子列表
   */
  getUserPosts: (userId, page = 1, includeFirst = false) => {
    return request.get(`/users/users/${userId}/posts/`, { page, include_first: includeFirst })
  },

  /**
   * 检查是否好友
   * @param {number|string} userId - 用户ID
   * @returns {Promise} 好友关系
   */
  checkFriendship: (userId) => {
    return request.get('/users/friends/check/', { user_id: userId })
  },

  /**
   * 获取好友列表
   * @returns {Promise} 好友列表
   */
  getFriends: () => {
    return request.get('/users/friends/friend_list/')
  },

  /**
   * 移除好友
   * @param {number} friendId - 好友用户ID
   * @returns {Promise} 移除结果
   */
  removeFriend: (friendId) => {
    return request.post('/users/friends/remove/', { friend_id: friendId })
  },

  /**
   * 发送好友请求
   * @param {number} receiverId - 接收者用户ID
   * @returns {Promise} 请求结果
   */
  sendFriendRequest: (receiverId) => {
    return request.post('/users/friend-requests/', { receiver: receiverId })
  },

  /**
   * 获取收到的好友请求
   * @returns {Promise} 好友请求列表
   */
  getReceivedFriendRequests: () => {
    return request.get('/users/friend-requests/received/')
  },

  /**
   * 获取已发送的好友请求
   * @returns {Promise} 好友请求列表
   */
  getSentFriendRequests: () => {
    return request.get('/users/friend-requests/sent/')
  },

  /**
   * 接受好友请求
   * @param {number} requestId - 请求ID
   * @returns {Promise} 处理结果
   */
  acceptFriendRequest: (requestId) => {
    return request.post(`/users/friend-requests/${requestId}/accept/`)
  },

  /**
   * 拒绝好友请求
   * @param {number} requestId - 请求ID
   * @returns {Promise} 处理结果
   */
  rejectFriendRequest: (requestId) => {
    return request.post(`/users/friend-requests/${requestId}/reject/`)
  },

  /**
   * 搜索用户
   * @param {string} query - 用户名或邮箱关键词
   * @returns {Promise} 用户列表
   */
  searchUsers: (query) => {
    return request.get('/users/users/search/', { q: query })
  },

  /**
   * 获取私信会话列表
   * @returns {Promise} 会话列表
   */
  getConversations: () => {
    return request.get('/users/messages/conversations/')
  },

  /**
   * 获取与特定用户的对话消息
   * @param {number|string} userId - 用户ID
   * @param {number} page - 页码
   * @param {number} pageSize - 每页条数
   * @returns {Promise} 对话消息
   */
  getConversation: (userId, page = 1, pageSize = 20) => {
    return request.get('/users/messages/conversation/', { user_id: userId, page, page_size: pageSize })
  },

  /**
   * 发送私信
   * @param {number|string} userId - 接收者用户ID
   * @param {Object} data - 消息数据
   * @param {string} data.content - 消息内容
   * @returns {Promise} 发送结果
   */
  sendMessage: (userId, data) => {
    return request.post(`/users/messages/${userId}/`, data)
  },

  /**
   * 标记与特定用户的所有消息为已读
   * @param {number|string} userId - 用户ID
   * @returns {Promise} 标记结果
   */
  markMessagesAsRead: (userId) => {
    return request.post(`/users/messages/${userId}/mark_read/`)
  },

  /**
   * 撤回私信（发送后 120 秒内，仅发送者）
   * @param {number|string} messageId - 消息ID
   * @returns {Promise} 撤回结果
   */
  recallMessage: (messageId) => {
    return request.post(`/users/messages/${messageId}/recall/`)
  },

  /**
   * 获取未读私信数量
   * @returns {Promise} 未读数量
   */
  getUnreadMessagesCount: () => {
    return request.get('/users/messages/unread_count/')
  },

  /**
   * 获取全部公开动态
   * @param {Object} params - 查询参数
   * @param {number} params.page - 页码
   * @param {number} params.page_size - 每页数量
   * @returns {Promise} 动态列表
   */
  getActivities: (params) => {
    return request.get('/activities/', params)
  },

  /**
   * 获取关注动态
   * @returns {Promise} 动态列表
   */
  getActivityFeed: () => {
    return request.get('/activities/feed/')
  },

  /**
   * 关注用户
   * @param {number|string} userId - 用户ID
   * @returns {Promise} 关注结果
   */
  followUser: (userId) => {
    return request.post(`/users/users/${userId}/follow/`)
  },

  /**
   * 取消关注用户
   * @param {number|string} userId - 用户ID
   * @returns {Promise} 取消关注结果
   */
  unfollowUser: (userId) => {
    return request.post(`/users/users/${userId}/unfollow/`)
  },

  /**
   * 获取我的动态
   * @returns {Promise} 动态列表
   */
  getMyActivities: () => {
    return request.get('/activities/my_activities/')
  },

  /**
   * 创建动态
   * @param {Object} data - 动态数据
   * @param {string} data.activity_type - 动态类型
   * @param {string} data.content - 内容
   * @param {boolean} data.is_public - 是否公开
   * @returns {Promise} 创建结果
   */
  createActivity: (data) => {
    return request.post('/activities/', data)
  },

  /**
   * 点赞动态
   * @param {number} activityId - 动态ID
   * @returns {Promise} 点赞结果
   */
  likeActivity: (activityId) => {
    return request.post(`/activities/${activityId}/like/`)
  },

  /**
   * 取消点赞动态
   * @param {number} activityId - 动态ID
   * @returns {Promise} 取消点赞结果
   */
  unlikeActivity: (activityId) => {
    return request.post(`/activities/${activityId}/unlike/`)
  },

  /**
   * 获取动态评论
   * @param {number} activityId - 动态ID
   * @returns {Promise} 评论列表
   */
  getActivityComments: (activityId) => {
    return request.get(`/activities/${activityId}/comments/`)
  },

  /**
   * 创建动态评论
   * @param {Object} data - 评论数据
   * @param {number} data.activity - 动态ID
   * @param {string} data.content - 内容
   * @param {number} [data.parent] - 父评论ID
   * @returns {Promise} 创建结果
   */
  createActivityComment: (data) => {
    return request.post('/activity-comments/', data)
  }
}

export default userApi
