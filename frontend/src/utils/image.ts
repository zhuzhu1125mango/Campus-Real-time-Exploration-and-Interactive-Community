import config from './config'

export const DEFAULT_AVATAR = config.media.defaultAvatar
export const DEFAULT_BANNER = config.media.defaultBanner
export const BASE_URL = config.media.baseUrl

/**
 * 格式化头像 URL，处理相对路径与绝对路径，空值返回默认头像
 * @param avatar 头像路径或 URL
 * @returns 完整头像 URL
 */
export function formatAvatar(avatar?: string | null): string {
  if (!avatar) return `${BASE_URL}${DEFAULT_AVATAR}`
  if (avatar.startsWith('http') || avatar.startsWith('data:')) return avatar
  return `${BASE_URL}${avatar}`
}

/**
 * 格式化图片 URL，处理相对路径与绝对路径
 * @param url 图片路径或 URL
 * @returns 完整图片 URL
 */
export function formatImage(url?: string | null): string {
  if (!url) return ''
  if (url.startsWith('http') || url.startsWith('data:')) return url
  return `${BASE_URL}${url}`
}
