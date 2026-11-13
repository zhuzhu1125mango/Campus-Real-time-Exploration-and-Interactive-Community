/**
 * 双端共享的日期格式化工具
 * H5 与小程序均可导入使用。
 */

const pad = (n) => String(n).padStart(2, '0')

/**
 * 格式化时间：今天显示 HH:mm，今年显示 MM-DD，其他显示 YYYY-MM-DD
 * @param {string|Date|number} time
 * @returns {string}
 */
export function formatTime(time) {
  if (!time) return ''
  const date = new Date(time)
  if (isNaN(date.getTime())) return ''

  const now = new Date()

  if (
    date.getFullYear() === now.getFullYear() &&
    date.getMonth() === now.getMonth() &&
    date.getDate() === now.getDate()
  ) {
    return `${pad(date.getHours())}:${pad(date.getMinutes())}`
  }

  if (date.getFullYear() === now.getFullYear()) {
    return `${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
  }

  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

/**
 * 格式化日期时间：YYYY-MM-DD HH:mm
 * @param {string|Date|number} time
 * @returns {string}
 */
export function formatDateTime(time) {
  if (!time) return ''
  const date = new Date(time)
  if (isNaN(date.getTime())) return ''
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

/**
 * 根据日期新旧程度格式化日期
 * 今天的日期显示为"今天 HH:MM"
 * 昨天的日期显示为"昨天 HH:MM"
 * 一周内的日期显示为"星期X HH:MM"
 * 更早的日期显示为"YYYY-MM-DD HH:MM"
 * @param {string|Date|number} dateString
 * @returns {string}
 */
export function formatDate(dateString) {
  if (!dateString) return ''

  const date = new Date(dateString)
  if (isNaN(date.getTime())) return ''

  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const yesterday = new Date(today)
  yesterday.setDate(yesterday.getDate() - 1)

  const diffDays = Math.floor((today.getTime() - date.getTime()) / (1000 * 60 * 60 * 24))
  const timeStr = `${pad(date.getHours())}:${pad(date.getMinutes())}`

  if (date >= today) {
    return `今天 ${timeStr}`
  }

  if (date >= yesterday) {
    return `昨天 ${timeStr}`
  }

  if (diffDays < 7) {
    const weekdays = ['日', '一', '二', '三', '四', '五', '六']
    return `星期${weekdays[date.getDay()]} ${timeStr}`
  }

  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${timeStr}`
}
