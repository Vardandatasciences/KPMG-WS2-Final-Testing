/**
 * Composable for handling API errors consistently across all pages
 * Automatically redirects to AccessDenied on 403 errors
 */
import { ref } from 'vue'
import { useRouter } from 'vue-router'

export function useApiErrorHandler() {
  const router = useRouter()
  const error = ref(null)
  const isLoading = ref(false)

  /**
   * Handle 403 Forbidden errors - redirect to AccessDenied page
   */
  const handle403Error = (errorResponse) => {
    const errorData = errorResponse?.data || errorResponse
    const errorMessage = errorData?.error || errorData?.message || 'You do not have permission to access this resource.'
    const errorCode = errorData?.code || '403'
    
    // Store error info in sessionStorage
    sessionStorage.setItem('access_denied_error', JSON.stringify({
      message: errorMessage,
      code: errorCode,
      timestamp: new Date().toISOString(),
      path: window.location.pathname
    }))
    
    // Redirect to access denied page
    router.push('/access-denied')
  }

  /**
   * Handle 401 Unauthorized errors - redirect to login
   */
  const handle401Error = () => {
    // Clear authentication data
    localStorage.removeItem('session_token')
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('current_user')
    
    // Redirect to login
    router.push('/login')
  }

  /**
   * Wrap an API call with error handling
   */
  const withErrorHandling = async (apiCall, options = {}) => {
    const { showLoading = true, onError = null } = options
    
    try {
      if (showLoading) isLoading.value = true
      error.value = null
      
      const result = await apiCall()
      return result
      
    } catch (err) {
      error.value = err
      
      // Handle 403 Forbidden
      if (err.response?.status === 403 || err.status === 403) {
        handle403Error(err.response || err)
        return null
      }
      
      // Handle 401 Unauthorized
      if (err.response?.status === 401 || err.status === 401) {
        handle401Error()
        return null
      }
      
      // Call custom error handler if provided
      if (onError) {
        onError(err)
      }
      
      throw err
      
    } finally {
      if (showLoading) isLoading.value = false
    }
  }

  /**
   * Check if error is a permission error
   */
  const isPermissionError = (err) => {
    return err?.response?.status === 403 || err?.status === 403
  }

  /**
   * Check if error is an authentication error
   */
  const isAuthError = (err) => {
    return err?.response?.status === 401 || err?.status === 401
  }

  return {
    error,
    isLoading,
    withErrorHandling,
    handle403Error,
    handle401Error,
    isPermissionError,
    isAuthError
  }
}

