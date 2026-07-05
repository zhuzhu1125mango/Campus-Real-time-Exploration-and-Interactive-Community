import { API_BASE_URL } from '../api/request'

const DEFAULT_AVATAR = '/static/logo.png'
const BASE_URL = API_BASE_URL.replace(/\/api$/, '')

/**
 * 格式化头像 URL，处理相对路径与绝对路径
 * @param {string|null} avatar
 * @returns {string}
 */
export const formatAvatar = (avatar) => {
  if (!avatar) return DEFAULT_AVATAR
  if (avatar.startsWith('http://') || avatar.startsWith('https://')) {
    return avatar
  }
  return `${BASE_URL}${avatar}`
}

/**
 * 格式化图片 URL
 * @param {string|null} url
 * @returns {string}
 */
export const formatImage = (url) => {
  if (!url) return ''
  if (url.startsWith('http://') || url.startsWith('https://')) {
    return url
  }
  return `${BASE_URL}${url}`
}
