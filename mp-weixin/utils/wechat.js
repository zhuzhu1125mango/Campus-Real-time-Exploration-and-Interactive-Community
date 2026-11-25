/**
 * 微信订阅消息工具。
 *
 * 使用前需在微信公众平台创建订阅消息模板，并将模板 ID 填入下方，
 * 同时在后端配置同名环境变量（WECHAT_TEMPLATE_*）。
 */
import wechatApi from '../api/wechat'

export const SUBSCRIBE_TEMPLATE_IDS = {
  comment: '',
  message: '',
  interaction: ''
}

export const SUBSCRIBE_TEMPLATE_KEYS = Object.keys(SUBSCRIBE_TEMPLATE_IDS)

const getWxLoginCode = () => new Promise((resolve, reject) => {
  uni.login({
    provider: 'weixin',
    success: (res) => resolve(res.code),
    fail: reject
  })
})

/** 将当前登录账号绑定微信 openid（失败静默，不阻塞主流程） */
export async function bindWechatAccount() {
  if (!uni.getStorageSync('accessToken')) return false
  try {
    const code = await getWxLoginCode()
    if (!code) return false
    await wechatApi.bind(code)
    return true
  } catch (error) {
    console.warn('[wechat] 绑定微信失败', error)
    return false
  }
}

/** 请求订阅消息授权，返回用户同意的模板 key 列表 */
export function requestSubscribe(templates = SUBSCRIBE_TEMPLATE_KEYS) {
  const tmplIds = templates
    .map((key) => SUBSCRIBE_TEMPLATE_IDS[key])
    .filter(Boolean)

  if (!tmplIds.length) {
    uni.showToast({ title: '尚未配置订阅消息模板', icon: 'none' })
    return Promise.resolve([])
  }

  return new Promise((resolve) => {
    uni.requestSubscribeMessage({
      tmplIds,
      success: (res) => {
        const accepted = templates.filter((key) => res[SUBSCRIBE_TEMPLATE_IDS[key]] === 'accept')
        resolve(accepted)
      },
      fail: () => resolve([])
    })
  })
}

/** 请求授权并把结果同步到后端 */
export async function requestAndSaveSubscribe(templates) {
  const accepted = await requestSubscribe(templates)
  if (!accepted.length) return []
  try {
    const res = await wechatApi.subscribe(accepted)
    return res.templates || accepted
  } catch (error) {
    console.warn('[wechat] 保存订阅授权失败', error)
    return []
  }
}

export default {
  SUBSCRIBE_TEMPLATE_IDS,
  SUBSCRIBE_TEMPLATE_KEYS,
  bindWechatAccount,
  requestSubscribe,
  requestAndSaveSubscribe
}
