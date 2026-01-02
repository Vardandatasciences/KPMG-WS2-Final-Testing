import { ref, reactive, readonly } from 'vue'

const toasts = ref([])

const useToast = () => {
  const addToast = (toast) => {
    const id = Math.random().toString(36).substr(2, 9)
    const newToast = {
      id,
      duration: 5000,
      ...toast
    }
    
    toasts.value.push(newToast)
    
    // Auto-remove toast after duration
    if (newToast.duration && newToast.duration > 0) {
      setTimeout(() => {
        removeToast(id)
      }, newToast.duration)
    }
    
    return id
  }

  const removeToast = (id) => {
    const index = toasts.value.findIndex(toast => toast.id === id)
    if (index > -1) {
      toasts.value.splice(index, 1)
    }
  }

  const clearAllToasts = () => {
    toasts.value = []
  }

  // Convenience methods
  const success = (title, message, duration) => {
    return addToast({ type: 'success', title, message, duration })
  }

  const error = (title, message, duration) => {
    return addToast({ type: 'error', title, message, duration })
  }

  const warning = (title, message, duration) => {
    return addToast({ type: 'warning', title, message, duration })
  }

  const info = (title, message, duration) => {
    return addToast({ type: 'info', title, message, duration })
  }

  return {
    toasts: readonly(toasts),
    addToast,
    removeToast,
    clearAllToasts,
    success,
    error,
    warning,
    info
  }
}

// Global toast state
const toastState = reactive({
  toasts: toasts.value
})

export {
  useToast,
  toastState
}
