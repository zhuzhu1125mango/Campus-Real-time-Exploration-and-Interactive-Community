import { ref } from 'vue'

interface Toast {
  id: number
  message: string
  type: 'success' | 'error' | 'info' | 'warning'
  duration: number
}

// 创建一个全局的toast数组
const toasts = ref<Toast[]>([])
let toastId = 0

export function useToast() {
  // 显示toast
  const showToast = (
    message: string, 
    type: 'success' | 'error' | 'info' | 'warning' = 'info', 
    duration = 3000
  ) => {
    const id = ++toastId
    
    // 添加新的toast
    toasts.value.push({
      id,
      message,
      type,
      duration
    })
    
    // 设置定时器自动移除
    setTimeout(() => {
      removeToast(id)
    }, duration)
    
    return id
  }
  
  // 移除指定toast
  const removeToast = (id: number) => {
    const index = toasts.value.findIndex(toast => toast.id === id)
    if (index !== -1) {
      toasts.value.splice(index, 1)
    }
  }
  
  // 清除所有toast
  const clearToasts = () => {
    toasts.value = []
  }
  
  return {
    toasts,
    showToast,
    removeToast,
    clearToasts
  }
} 