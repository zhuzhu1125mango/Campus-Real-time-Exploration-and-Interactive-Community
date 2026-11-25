import request from './request'

const wechatApi = {
  /** 绑定当前账号与微信 openid */
  bind: (code) => request.post('/users/users/wechat_bind/', { code }),

  /** 记录已授权的订阅消息模板 */
  subscribe: (templates) => request.post('/users/users/wechat_subscribe/', { templates }),

  /** 微信 code 登录（需先绑定） */
  login: (code) => request.post('/users/users/wechat_login/', { code })
}

export default wechatApi
