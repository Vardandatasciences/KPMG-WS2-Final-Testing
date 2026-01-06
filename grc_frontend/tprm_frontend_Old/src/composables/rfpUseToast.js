/**
 * RFP Secure Toast Composable
 * Enhanced toast system with security validation and Vue 3 Composition API
 */

import { ref, reactive, readonly, computed } from 'vue'
import { rfpSanitizeString, rfpGenerateId } from '@/utils/rfpUtils.js'
import { RfpValidator } from '@/utils/rfpValidation.js'

// Toast state management
const toasts = ref([])
const maxToasts = 5 // Limit to prevent memory issues

// Toast configuration
const defaultConfig = {
  duration: 5000, // 5 seconds
  maxDuration: 30000, // 30 seconds max
  minDuration: 1000, // 1 second min
  maxTitleLength: 100,
  maxMessageLength: 500
}

// Global toast state for reactive updates
const rfpToastState = reactive({
  toasts: computed(() => readonly(toasts.value))
})

// Toast management functions
const rfpUseToast = () => {
  // Validate toast data
  const validateToast = (toast) => {
    // Validate title
    if (!toast.title || typeof toast.title !== 'string') {
      console.error('Toast title is required and must be a string')
      return null
    }

    const sanitizedTitle = rfpSanitizeString(toast.title)
    if (sanitizedTitle.length === 0 || sanitizedTitle.length > defaultConfig.maxTitleLength) {
      console.error('Toast title must be between 1 and 100 characters')
      return null
    }

    // Validate message
    let sanitizedMessage
    if (toast.message) {
      if (typeof toast.message !== 'string') {
        console.error('Toast message must be a string')
        return null
      }
      
      sanitizedMessage = rfpSanitizeString(toast.message)
      if (sanitizedMessage.length > defaultConfig.maxMessageLength) {
        console.error('Toast message cannot exceed 500 characters')
        return null
      }
    }

    // Validate type
    const validTypes = ['success', 'error', 'warning', 'info']
    if (!toast.type || !validTypes.includes(toast.type)) {
      console.error('Invalid toast type')
      return null
    }

    // Validate duration
    let duration = defaultConfig.duration
    if (toast.duration !== undefined) {
      if (typeof toast.duration !== 'number' || toast.duration < 0) {
        console.error('Toast duration must be a positive number')
        return null
      }
      
      duration = Math.min(
        Math.max(toast.duration, defaultConfig.minDuration),
        defaultConfig.maxDuration
      )
    }

    // Validate action
    let action
    if (toast.action) {
      if (!toast.action.label || typeof toast.action.label !== 'string') {
        console.error('Toast action label must be a string')
        return null
      }
      
      if (typeof toast.action.handler !== 'function') {
        console.error('Toast action handler must be a function')
        return null
      }

      const sanitizedLabel = rfpSanitizeString(toast.action.label)
      if (sanitizedLabel.length === 0 || sanitizedLabel.length > 50) {
        console.error('Toast action label must be between 1 and 50 characters')
        return null
      }

      action = {
        label: sanitizedLabel,
        handler: toast.action.handler
      }
    }

    return {
      id: toast.id || rfpGenerateId(),
      type: toast.type,
      title: sanitizedTitle,
      message: sanitizedMessage,
      duration,
      action,
      dismissible: toast.dismissible !== false, // Default to true
      persistent: toast.persistent === true // Default to false
    }
  }

  // Add toast with validation
  const addToast = (toast) => {
    const validatedToast = validateToast(toast)
    
    if (!validatedToast) {
      return null
    }

    // Limit number of toasts
    if (toasts.value.length >= maxToasts) {
      // Remove oldest toast
      toasts.value.shift()
    }

    toasts.value.push(validatedToast)

    // Auto-remove toast after duration (unless persistent)
    if (!validatedToast.persistent && validatedToast.duration > 0) {
      setTimeout(() => {
        removeToast(validatedToast.id)
      }, validatedToast.duration)
    }

    return validatedToast.id
  }

  // Remove toast by ID
  const removeToast = (id) => {
    const index = toasts.value.findIndex(toast => toast.id === id)
    if (index > -1) {
      toasts.value.splice(index, 1)
      return true
    }
    return false
  }

  // Clear all toasts
  const clearAllToasts = () => {
    toasts.value = []
  }

  // Update existing toast
  const updateToast = (id, updates) => {
    const index = toasts.value.findIndex(toast => toast.id === id)
    if (index === -1) {
      return false
    }

    const currentToast = toasts.value[index]
    const updatedToast = validateToast({ ...currentToast, ...updates })
    
    if (!updatedToast) {
      return false
    }

    toasts.value[index] = updatedToast
    return true
  }

  // Convenience methods for different toast types
  const success = (title, message, options) => {
    return addToast({
      type: 'success',
      title,
      message,
      ...options
    })
  }

  const error = (title, message, options) => {
    return addToast({
      type: 'error',
      title,
      message,
      duration: 8000, // Longer duration for errors
      ...options
    })
  }

  const warning = (title, message, options) => {
    return addToast({
      type: 'warning',
      title,
      message,
      duration: 6000, // Medium duration for warnings
      ...options
    })
  }

  const info = (title, message, options) => {
    return addToast({
      type: 'info',
      title,
      message,
      ...options
    })
  }

  // Promise-based toast for async operations
  const promise = (promise, messages) => {
    const loadingId = addToast({
      type: 'info',
      title: messages.loading,
      persistent: true,
      dismissible: false
    })

    return promise
      .then((data) => {
        if (loadingId) {
          removeToast(loadingId)
        }
        
        const successMessage = typeof messages.success === 'function' 
          ? messages.success(data) 
          : messages.success
        
        success(successMessage)
        return data
      })
      .catch((error) => {
        if (loadingId) {
          removeToast(loadingId)
        }
        
        const errorMessage = typeof messages.error === 'function' 
          ? messages.error(error) 
          : messages.error
        
        error(errorMessage)
        throw error
      })
  }

  // Toast with action confirmation
  const confirm = (title, message, onConfirm, onCancel) => {
    return addToast({
      type: 'warning',
      title,
      message,
      persistent: true,
      action: {
        label: 'Confirm',
        handler: () => {
          onConfirm()
          removeToast(toasts.value.find(t => t.title === title)?.id || '')
        }
      },
      dismissible: true
    })
  }

  // Get toast by ID
  const getToast = (id) => {
    return toasts.value.find(toast => toast.id === id)
  }

  // Get toasts by type
  const getToastsByType = (type) => {
    return toasts.value.filter(toast => toast.type === type)
  }

  // Check if toast exists
  const hasToast = (id) => {
    return toasts.value.some(toast => toast.id === id)
  }

  // Get toast count
  const getToastCount = () => {
    return toasts.value.length
  }

  // Get toast count by type
  const getToastCountByType = (type) => {
    return toasts.value.filter(toast => toast.type === type).length
  }

  return {
    // State
    toasts: readonly(toasts),
    
    // Core methods
    addToast,
    removeToast,
    updateToast,
    clearAllToasts,
    
    // Convenience methods
    success,
    error,
    warning,
    info,
    promise,
    confirm,
    
    // Utility methods
    getToast,
    getToastsByType,
    hasToast,
    getToastCount,
    getToastCountByType
  }
}

// Global toast instance for app-wide usage
const rfpToast = rfpUseToast()

export {
  rfpUseToast,
  rfpToast,
  rfpToastState,
  defaultConfig
}
