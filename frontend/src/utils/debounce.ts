/**
 * 创建一个防抖函数。
 * 在 wait 毫秒内多次调用时，只有最后一次会实际执行。
 */
export function debounce<T extends (...args: any[]) => void>(
  fn: T,
  wait: number = 300
): (...args: Parameters<T>) => void {
  let timer: ReturnType<typeof setTimeout> | null = null

  return (...args: Parameters<T>) => {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => {
      fn(...args)
    }, wait)
  }
}
