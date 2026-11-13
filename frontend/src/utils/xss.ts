/**
 * XSS 过滤工具
 * 由 @shared/utils/xss 提供双端共享实现，不依赖浏览器 DOM API。
 */
export { escapeHtml, sanitizeHtml, stripHtml, formatMessageContent } from '@shared/utils/xss.js'
