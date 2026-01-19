import { ref } from 'vue'
import apiService from '@/services/api'

// Shared state for unread notification count
const unreadCount = ref(0)
const isInitialized = ref(false)

export function useNotificationCount() {
  const setUnreadCount = (count) => {
    unreadCount.value = count
  }

  const incrementUnreadCount = () => {
    unreadCount.value++
  }

  const decrementUnreadCount = () => {
    if (unreadCount.value > 0) {
      unreadCount.value--
    }
  }

  const initializeNotificationCount = async () => {
    if (isInitialized.value) return
    
    // Check if user is authenticated before fetching notification count
    const token = localStorage.getItem('session_token')
    if (!token) {
      console.log('No authentication token found, skipping notification count initialization')
      unreadCount.value = 0
      isInitialized.value = true
      return
    }
    
    try {
      console.log('Initializing notification count...')
      const stats = await apiService.getNotificationStats()
      unreadCount.value = stats.total_unread || 0
      isInitialized.value = true
      console.log('Notification count initialized:', unreadCount.value)
    } catch (error) {
      // Silently handle 403 (Forbidden) errors for public/unauthenticated pages
      if (error.status === 403 || error.message?.includes('403') || error.message?.includes('Forbidden') || error.message?.includes('Permission denied')) {
        // Don't log - this is expected on public pages
        unreadCount.value = 0
        isInitialized.value = true
        return
      }
      console.error('Failed to initialize notification count:', error)
      // Set to 0 on error to avoid showing incorrect counts
      unreadCount.value = 0
      isInitialized.value = true
    }
  }

  const refreshNotificationCount = async () => {
    // Check if user is authenticated before fetching notification count
    const token = localStorage.getItem('session_token')
    if (!token) {
      console.log('No authentication token found, skipping notification count refresh')
      unreadCount.value = 0
      return
    }
    
    try {
      const stats = await apiService.getNotificationStats()
      unreadCount.value = stats.total_unread || 0
      console.log('Notification count refreshed:', unreadCount.value)
    } catch (error) {
      // Silently handle 403 (Forbidden) errors for public/unauthenticated pages
      if (error.status === 403 || error.message?.includes('403') || error.message?.includes('Forbidden') || error.message?.includes('Permission denied')) {
        // Don't log - this is expected on public pages
        return
      }
      console.error('Failed to refresh notification count:', error)
      // Don't reset count on error to avoid flickering
    }
  }

  return {
    unreadCount,
    isInitialized,
    setUnreadCount,
    incrementUnreadCount,
    decrementUnreadCount,
    initializeNotificationCount,
    refreshNotificationCount
  }
}
