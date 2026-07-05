/**
 * 从任意错误对象中提取用户友好的提示文案。
 * 避免直接把后端原始堆栈、HTML 或未知异常详情暴露给用户。
 */
export function getErrorMessage(error: unknown, fallback = '操作失败，请稍后重试'): string {
  if (!error) return fallback

  // axios 风格的响应错误
  if (typeof error === 'object' && error !== null) {
    const err = error as Record<string, any>

    if (typeof err.response?.data?.detail === 'string') {
      return err.response.data.detail
    }
    if (typeof err.response?.data?.error === 'string') {
      return err.response.data.error
    }
    if (typeof err.response?.data?.message === 'string') {
      return err.response.data.message
    }
    // DRF 字段级错误，例如 { username: ["该用户名已存在"] }
    if (err.response?.data && typeof err.response.data === 'object') {
      const data = err.response.data
      for (const key in data) {
        if (Array.isArray(data[key]) && data[key].length > 0 && typeof data[key][0] === 'string') {
          return data[key][0]
        }
      }
    }
    if (typeof err.detail === 'string') {
      return err.detail
    }
    if (typeof err.message === 'string' && err.message !== '[object Object]') {
      // 仅当看起来是用户可读信息时才返回
      return err.message
    }
  }

  return fallback
}
