/**
 * 双端共享的图片 URL 处理工具
 */

const DEFAULT_AVATAR = '/media/avatars/default-avatar.svg'

/**
 * 判断是否为绝对 URL 或 data URI
 * @param {string} url
 * @returns {boolean}
 */
function isAbsoluteUrl(url) {
  return typeof url === 'string' && (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('data:'))
}

/**
 * 格式化头像 URL
 * @param {string|null} avatar
 * @param {string} baseUrl
 * @param {string} defaultAvatar
 * @returns {string}
 */
export function formatAvatar(avatar, baseUrl = '', defaultAvatar = DEFAULT_AVATAR) {
  if (!avatar) return `${baseUrl}${defaultAvatar}`
  if (isAbsoluteUrl(avatar)) return avatar
  return `${baseUrl}${avatar}`
}

/**
 * 格式化图片 URL
 * @param {string|null} url
 * @param {string} baseUrl
 * @returns {string}
 */
export function formatImage(url, baseUrl = '') {
  if (!url) return ''
  if (isAbsoluteUrl(url)) return url
  return `${baseUrl}${url}`
}

/**
 * 获取媒体基础 URL
 * 小程序端传入 API 基础地址；H5 端可通过配置注入。
 * @param {string} apiBaseUrl
 * @returns {string}
 */
export function getMediaBaseUrl(apiBaseUrl) {
  if (!apiBaseUrl) return ''
  return apiBaseUrl.replace(/\/api$/, '')
}
