/**
 * 双端共享的 XSS 过滤工具
 * 不依赖浏览器 DOM API，可在 H5 与小程序中同时使用。
 */

const ALLOWED_TAGS = new Set([
  'p', 'br', 'strong', 'b', 'em', 'i', 'u', 's', 'strike',
  'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
  'ul', 'ol', 'li', 'blockquote', 'pre', 'code',
  'a', 'img', 'span', 'div', 'table', 'thead', 'tbody', 'tr', 'td', 'th'
])

const ALLOWED_ATTRS = new Set([
  'href', 'title', 'target', 'rel',
  'src', 'alt', 'width', 'height',
  'class', 'style'
])

const EVENT_ATTR_REGEX = /^on/i

/**
 * 对 HTML 特殊字符进行转义，防止 XSS 注入。
 * @param {string} text
 * @returns {string}
 */
export function escapeHtml(text) {
  if (!text) return ''
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}

/**
 * 使用白名单清理 HTML 字符串，仅保留安全的标签与属性。
 * @param {string} html
 * @returns {string}
 */
export function sanitizeHtml(html) {
  if (!html) return ''
  if (typeof html !== 'string') return String(html)

  // 1. 移除注释
  let cleaned = html.replace(/<!--[\s\S]*?-->/g, '')

  // 2. 移除 script / style / iframe / object / embed / form / input 标签及其内容
  cleaned = cleaned.replace(/<(script|style|iframe|object|embed|form|input)[\s\S]*?<\/\1>/gi, '')

  // 3. 过滤标签与属性
  cleaned = cleaned.replace(/<\/?([a-zA-Z][a-zA-Z0-9]*)\b[^>]*>/g, (match, tagName) => {
    const lowerTag = tagName.toLowerCase()
    if (!ALLOWED_TAGS.has(lowerTag)) {
      return ''
    }

    const isClosing = match.startsWith('</')
    if (isClosing) {
      return `</${lowerTag}>`
    }

    const attrRegex = /\s([a-zA-Z\-_:]+)(?:=["']([^"']*)["'])?/g
    let attrs = ''
    let attrMatch
    while ((attrMatch = attrRegex.exec(match)) !== null) {
      const attrName = attrMatch[1].toLowerCase()
      const attrValue = attrMatch[2] || ''

      if (EVENT_ATTR_REGEX.test(attrName)) continue
      if (!ALLOWED_ATTRS.has(attrName)) continue

      if ((attrName === 'href' || attrName === 'src') && /^(javascript|data):/i.test(attrValue)) {
        continue
      }

      attrs += ` ${attrName}="${attrValue.replace(/"/g, '&quot;')}"`
    }

    return `<${lowerTag}${attrs}>`
  })

  return cleaned
}

/**
 * 从 HTML 中提取纯文本。
 * @param {string} html
 * @returns {string}
 */
export function stripHtml(html) {
  if (!html) return ''
  return sanitizeHtml(html)
    .replace(/<[^>]+>/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
}

/**
 * 格式化聊天消息内容：先转义 HTML，再将 URL 转换为安全链接。
 * 仅适用于 H5（小程序中富文本链接需使用 rich-text 组件）。
 * @param {string} content
 * @returns {string}
 */
export function formatMessageContent(content) {
  if (!content) return ''

  const escaped = escapeHtml(content)
  const urlRegex = /(https?:\/\/[^\s<]+)/g
  return escaped.replace(urlRegex, (url) => {
    const safeUrl = escapeHtml(url)
    return `<a href="${safeUrl}" target="_blank" rel="noopener noreferrer nofollow">${safeUrl}</a>`
  })
}
