import request from './request'

// 聊天相关API
const chatApi = {
  /**
   * 获取最近的聊天消息
   * @param {Object} params - 查询参数
   * @returns {Promise} 聊天记录
   */
  getRecentMessages: (params) => {
    return request.get('/chat/messages/recent_messages/', params)
  },

  /**
   * 获取在线用户数量
   * @returns {Promise} 在线用户数量
   */
  getOnlineUsers: () => {
    return request.get('/chat/messages/online_users/')
  },

  /**
   * 发送消息
   * @param {Object} data - 消息数据
   * @param {string} data.content - 消息内容
   * @returns {Promise} 发送结果
   */
  sendMessage: (data) => {
    return request.post('/chat/send_message/', data)
  }
}

export default chatApi
