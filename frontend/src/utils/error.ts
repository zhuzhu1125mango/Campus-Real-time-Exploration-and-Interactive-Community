/**
 * 从 unknown 错误对象中提取可读消息
 */
export const getErrorMessage = (err: unknown, defaultMsg = '未知错误'): string => {
  if (err instanceof Error) return err.message
  if (
    err &&
    typeof err === 'object' &&
    'message' in err &&
    typeof (err as { message?: unknown }).message === 'string'
  ) {
    return (err as { message: string }).message
  }
  return defaultMsg
}

interface ApiErrorData {
  detail?: string
  error?: string
  message?: string
  non_field_errors?: string[]
}

interface ApiErrorResponse {
  response?: {
    data?: ApiErrorData
  }
}

/**
 * 从 API 错误响应中提取后端返回的详细错误信息
 */
export const getApiErrorMessage = (err: unknown, defaultMsg = '请求失败'): string => {
  const apiErr = err as ApiErrorResponse
  const data = apiErr.response?.data
  if (data) {
    return (
      data.detail ||
      data.error ||
      data.message ||
      data.non_field_errors?.[0] ||
      defaultMsg
    )
  }
  return getErrorMessage(err, defaultMsg)
}
