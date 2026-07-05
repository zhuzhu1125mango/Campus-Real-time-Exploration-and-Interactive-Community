/**
 * 简易 HTML 清理工具（小程序端无 DOMPurify，使用白名单过滤）
 * 仅保留常见富文本标签与属性，移除 script/style 及事件处理器。
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
 * 清理 HTML 字符串，返回可在 rich-text 中安全使用的字符串。
 */
export function sanitizeHtml(html) {
  if (!html) return ''
  if (typeof html !== 'string') return String(html)

  // 1. 移除注释
  let cleaned = html.replace(/<!--[\s\S]*?-->/g, '')

  // 2. 移除 script / style / iframe / object / embed 标签及其内容
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

    // 解析并过滤属性
    const attrRegex = /\s([a-zA-Z\-_:]+)(?:=["']([^"']*)["'])?/g
    let attrs = ''
    let attrMatch
    while ((attrMatch = attrRegex.exec(match)) !== null) {
      const attrName = attrMatch[1].toLowerCase()
      const attrValue = attrMatch[2] || ''

      if (EVENT_ATTR_REGEX.test(attrName)) continue
      if (!ALLOWED_ATTRS.has(attrName)) continue

      // 对 href/src 做协议校验，防止 javascript: 伪协议
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
 */
export function stripHtml(html) {
  if (!html) return ''
  return sanitizeHtml(html)
    .replace(/<[^>]+>/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
}
