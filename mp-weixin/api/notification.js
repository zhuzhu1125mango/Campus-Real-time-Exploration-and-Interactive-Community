import request from './request'

const notificationApi = {
  /**
   * 获取通知列表
   * @param {Object} params - 查询参数
   * @param {number} params.page - 页码
   * @param {number} params.page_size - 每页数量
   * @returns {Promise} 通知列表
   */
  getNotifications: (params) => {
    return request.get('/users/notifications/', params)
  },

  /**
   * 获取未读通知
   * @returns {Promise} 未读通知列表
   */
  getUnread: () => {
    return request.get('/users/notifications/unread/')
  },

  /**
   * 获取未读通知数量
   * @returns {Promise} 未读数量
   */
  getUnreadCount: () => {
    return request.get('/users/notifications/count/')
  },

  /**
   * 将所有通知标记为已读
   * @returns {Promise} 操作结果
   */
  markAllRead: () => {
    return request.post('/users/notifications/mark_all_read/')
  },

  /**
   * 将单个通知标记为已读
   * @param {number} id - 通知ID
   * @returns {Promise} 操作结果
   */
  markAsRead: (id) => {
    return request.post(`/users/notifications/${id}/mark_read/`)
  },

  /**
   * 删除所有已读通知
   * @returns {Promise} 操作结果
   */
  deleteAllRead: () => {
    return request.delete('/users/notifications/delete_all_read/')
  }
}

export default notificationApi