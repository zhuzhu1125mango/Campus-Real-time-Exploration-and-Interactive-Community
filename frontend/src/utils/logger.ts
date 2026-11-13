/**
 * 统一日志工具
 * - 开发环境（import.meta.env.DEV === true）正常输出
 * - 生产环境静默 log/warn，保留 error
 */
const isDev = import.meta.env.DEV

export const logger = {
  log: (...args: unknown[]) => {
    if (isDev) {
      // eslint-disable-next-line no-console
      console.log(...args)
    }
  },
  warn: (...args: unknown[]) => {
    if (isDev) {
      // eslint-disable-next-line no-console
      console.warn(...args)
    }
  },
  error: (...args: unknown[]) => {
    // 错误日志在生产和开发环境都保留，便于排查线上问题
    // eslint-disable-next-line no-console
    console.error(...args)
  },
  info: (...args: unknown[]) => {
    if (isDev) {
      // eslint-disable-next-line no-console
      console.info(...args)
    }
  },
}
