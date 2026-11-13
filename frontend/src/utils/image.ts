import { formatAvatar as sharedFormatAvatar, formatImage as sharedFormatImage } from '@shared/utils/image.js'
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
  return sharedFormatAvatar(avatar, BASE_URL, `${BASE_URL}${DEFAULT_AVATAR}`)
}

/**
 * 格式化图片 URL，处理相对路径与绝对路径
 * @param url 图片路径或 URL
 * @returns 完整图片 URL
 */
export function formatImage(url?: string | null): string {
  return sharedFormatImage(url, BASE_URL)
}
