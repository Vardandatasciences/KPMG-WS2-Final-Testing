/**
 * Permission handling composable
 * Provides utilities for handling RBAC permission errors
 */
import { ref } from 'vue'
import { useRouter } from 'vue-router'

export function usePermissions() {
  const router = useRouter()
  const permissionError = ref(null)
  const hasPermission = ref(true)

  /**
   * Handle API call with permission error handling
   * Wraps an API call and catches permission errors
   * 
   * @param {Function} apiCall - The API call function to execute
   * @param {Object} options - Options for error handling
   * @param {boolean} options.redirectOnError - Whether to redirect to access denied page (default: true)
   * @param {Function} options.onError - Custom error handler callback
   * @returns {Promise} - The result of the API call
   */
  const withPermissionCheck = async (apiCall, options = {}) => {
    const {
      redirectOnError = true,
      onError = null
    } = options

    try {
      permissionError.value = null
      hasPermission.value = true
      
      const result = await apiCall()
      return result
    } catch (error) {
      if (error.response?.status === 403) {
        // Permission denied
        permissionError.value = {
          message: error.response?.data?.error || error.response?.data?.message || 'Permission denied',
          code: error.response?.data?.code || '403',
          permission: error.response?.data?.permission || 'Unknown'
        }
        hasPermission.value = false

        // Call custom error handler if provided
        if (onError) {
          onError(permissionError.value)
        }

        // Redirect to access denied page if enabled
        if (redirectOnError) {
          sessionStorage.setItem('access_denied_error', JSON.stringify({
            message: permissionError.value.message,
            code: permissionError.value.code,
            timestamp: new Date().toISOString(),
            path: window.location.pathname,
            permission: permissionError.value.permission
          }))
          
          router.push('/access-denied')
        }
      }
      
      // Re-throw error for further handling if needed
      throw error
    }
  }

  /**
   * Check if user has permission for a specific action
   * This is a helper function that can be used before making API calls
   * 
   * @param {Function} apiCall - The API call to check permission
   * @returns {Promise<boolean>} - Whether the user has permission
   */
  const checkPermission = async (apiCall) => {
    try {
      await apiCall()
      hasPermission.value = true
      return true
    } catch (error) {
      if (error.response?.status === 403) {
        hasPermission.value = false
        permissionError.value = {
          message: error.response?.data?.error || 'Permission denied',
          code: error.response?.data?.code || '403',
          permission: error.response?.data?.permission || 'Unknown'
        }
        return false
      }
      // For other errors, we assume it's not a permission issue
      throw error
    }
  }

  /**
   * Clear permission error state
   */
  const clearPermissionError = () => {
    permissionError.value = null
    hasPermission.value = true
  }

  return {
    // State
    permissionError,
    hasPermission,
    
    // Methods
    withPermissionCheck,
    checkPermission,
    clearPermissionError
  }
}

