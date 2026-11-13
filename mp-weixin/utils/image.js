import { formatAvatar as sharedFormatAvatar, formatImage as sharedFormatImage, getMediaBaseUrl } from '../../shared/utils/image.js'
import { API_BASE_URL } from '../api/request'

const DEFAULT_AVATAR = '/static/logo.png'
const BASE_URL = getMediaBaseUrl(API_BASE_URL)

/**
 * 格式化头像 URL，处理相对路径与绝对路径
 * @param {string|null} avatar
 * @returns {string}
 */
export const formatAvatar = (avatar) => {
  return sharedFormatAvatar(avatar, BASE_URL, `${BASE_URL}${DEFAULT_AVATAR}`)
}

/**
 * 格式化图片 URL
 * @param {string|null} url
 * @returns {string}
 */
export const formatImage = (url) => {
  return sharedFormatImage(url, BASE_URL)
}
