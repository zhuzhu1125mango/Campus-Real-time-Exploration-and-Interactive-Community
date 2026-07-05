import DOMPurify from 'dompurify'

/**
 * 对 HTML 特殊字符进行转义，防止 XSS 注入。
 * 适用于用户输入的纯文本内容。
 */
export function escapeHtml(text: string): string {
  if (!text) return ''
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}

/**
 * 格式化聊天消息内容：先转义 HTML，再将 URL 转换为安全链接。
 */
export function formatMessageContent(content: string): string {
  if (!content) return ''

  const escaped = escapeHtml(content)
  const urlRegex = /(https?:\/\/[^\s<]+)/g
  return escaped.replace(urlRegex, (url) => {
    // 对 href 值再做一次转义，防止引号注入
    const safeUrl = escapeHtml(url)
    return `<a href="${safeUrl}" target="_blank" rel="noopener noreferrer nofollow">${safeUrl}</a>`
  })
}

/**
 * 使用 DOMPurify 清理富文本内容，仅保留安全的 HTML 标签和属性。
 * 适用于帖子、通知等可能包含富文本的场景。
 */
export function sanitizeHtml(html: string): string {
  if (!html) return ''
  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: [
      'p', 'br', 'strong', 'b', 'em', 'i', 'u', 's', 'strike',
      'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
      'ul', 'ol', 'li', 'blockquote', 'pre', 'code',
      'a', 'img', 'span', 'div', 'table', 'thead', 'tbody', 'tr', 'td', 'th'
    ],
    ALLOWED_ATTR: [
      'href', 'title', 'target', 'rel',
      'src', 'alt', 'width', 'height',
      'class', 'style'
    ],
    ALLOW_DATA_ATTR: false
  }) as string
}

/**
 * 从 HTML 内容中提取纯文本。
 * 先使用 DOMPurify 清理危险标签与事件属性，再读取 textContent，
 * 避免在转换过程中触发 XSS 攻击载荷。
 */
export function stripHtml(html: string): string {
  if (!html) return ''
  const tmp = document.createElement('div')
  tmp.innerHTML = sanitizeHtml(html)
  return tmp.textContent || tmp.innerText || ''
}
