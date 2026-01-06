import { ref } from 'vue'
import notificationService from '@/services/notificationService'

// Global notification state
const notifications = ref([])
const isLoading = ref(false)

const hasAuthToken = () => {
  if (typeof window === 'undefined') {
    return false
  }
  try {
    return Boolean(
      localStorage.getItem('session_token') ||
      localStorage.getItem('auth_token') ||
      localStorage.getItem('access_token')
    )
  } catch (error) {
    console.warn('Notifications: unable to read auth tokens', error)
    return false
  }
}

const createLocalNotification = (type, title, message, data = {}) => {
  const now = new Date().toISOString()
  const notification = {
    id: `local-${now}-${Math.random().toString(36).slice(2, 8)}`,
    title,
    message,
    metadata: {
      type,
      ...data,
      source: 'local'
    },
    status: 'unread',
    created_at: now,
    read_at: null
  }
  notifications.value.unshift(notification)
  return notification
}

export function useNotifications() {
  // Show success notification
  const showSuccess = async (title, message, data = {}) => {
    if (!hasAuthToken()) {
      return createLocalNotification('success', title, message, data)
    }
    try {
      isLoading.value = true
      const notification = await notificationService.createSuccessNotification(title, message, data)
      notifications.value.unshift(notification)
      return notification
    } catch (error) {
      console.error('Failed to create success notification:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  // Show error notification
  const showError = async (title, message, data = {}) => {
    if (!hasAuthToken()) {
      return createLocalNotification('error', title, message, data)
    }
    try {
      isLoading.value = true
      const notification = await notificationService.createErrorNotification(title, message, data)
      notifications.value.unshift(notification)
      return notification
    } catch (error) {
      console.error('Failed to create error notification:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  // Show warning notification
  const showWarning = async (title, message, data = {}) => {
    if (!hasAuthToken()) {
      return createLocalNotification('warning', title, message, data)
    }
    try {
      isLoading.value = true
      const notification = await notificationService.createWarningNotification(title, message, data)
      notifications.value.unshift(notification)
      return notification
    } catch (error) {
      console.error('Failed to create warning notification:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  // Show info notification
  const showInfo = async (title, message, data = {}) => {
    if (!hasAuthToken()) {
      return createLocalNotification('info', title, message, data)
    }
    try {
      isLoading.value = true
      const notification = await notificationService.createInfoNotification(title, message, data)
      notifications.value.unshift(notification)
      return notification
    } catch (error) {
      console.error('Failed to create info notification:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  // SLA-specific notification helpers
  const showSLASuccess = async (action, slaData) => {
    if (!hasAuthToken()) {
      return createLocalNotification('sla-success', action, '', slaData)
    }
    try {
      isLoading.value = true
      const notification = await notificationService.createSLASuccessNotification(action, slaData)
      notifications.value.unshift(notification)
      return notification
    } catch (error) {
      console.error('Failed to create SLA success notification:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  const showSLAError = async (action, error, slaData = {}) => {
    if (!hasAuthToken()) {
      return createLocalNotification('sla-error', action, error?.message || '', { ...slaData, error })
    }
    try {
      isLoading.value = true
      const notification = await notificationService.createSLAErrorNotification(action, error, slaData)
      notifications.value.unshift(notification)
      return notification
    } catch (error) {
      console.error('Failed to create SLA error notification:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  const showSLAWarning = async (action, slaData) => {
    if (!hasAuthToken()) {
      return createLocalNotification('sla-warning', action, '', slaData)
    }
    try {
      isLoading.value = true
      const notification = await notificationService.createSLAWarningNotification(action, slaData)
      notifications.value.unshift(notification)
      return notification
    } catch (error) {
      console.error('Failed to create SLA warning notification:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  // Clear all notifications
  const clearAll = () => {
    notifications.value = []
  }

  // Clear specific notification
  const clearNotification = (notificationId) => {
    notifications.value = notifications.value.filter(n => n.id !== notificationId)
  }

  // Get notifications by type
  const getNotificationsByType = (type) => {
    return notifications.value.filter(n => n.metadata?.type === type)
  }

  // Get unread notifications
  const getUnreadNotifications = () => {
    return notifications.value.filter(n => n.status !== 'read')
  }

  // Mark notification as read
  const markAsRead = async (notificationId) => {
    try {
      // Update local state
      const notification = notifications.value.find(n => n.id === notificationId)
      if (notification) {
        notification.status = 'read'
        notification.read_at = new Date().toISOString()
      }
      
      // Update in backend
      await notificationService.markAsRead(notificationId)
    } catch (error) {
      console.error('Failed to mark notification as read:', error)
      throw error
    }
  }

  // Subscribe to new notifications
  const subscribe = (callback) => {
    return notificationService.subscribe(callback)
  }

  return {
    // State
    notifications,
    isLoading,
    
    // Methods
    showSuccess,
    showError,
    showWarning,
    showInfo,
    showSLASuccess,
    showSLAError,
    showSLAWarning,
    clearAll,
    clearNotification,
    getNotificationsByType,
    getUnreadNotifications,
    markAsRead,
    subscribe
  }
}

// Export default for easy importing
export default useNotifications
