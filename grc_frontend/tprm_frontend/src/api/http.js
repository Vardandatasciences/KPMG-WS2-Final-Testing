import axios from 'axios'
import { getTprmApiBaseUrl } from '@/utils/backendEnv'

// Create axios instance with base configuration
const http = axios.create({
  baseURL: getTprmApiBaseUrl(),
  timeout: 0, // No timeout - let requests complete naturally
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add JWT token
http.interceptors.request.use(
  (config) => {
    // Add JWT token - read from sessionStorage (received from GRC parent via postMessage)
    const token = sessionStorage.getItem('access_token') ||
                  sessionStorage.getItem('session_token') ||
                  localStorage.getItem('session_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    // For FormData requests, let the browser set the Content-Type header
    // This is crucial for file uploads to work properly
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type']
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor to unwrap the unified envelope
http.interceptors.response.use(
  (response) => {
    // If the response has the unified envelope format, unwrap it
    if (response.data && typeof response.data === 'object' && 'success' in response.data) {
      if (response.data.success) {
        // Success response - use .data if present, otherwise keep full body (e.g. risk_generation at top level)
        const body = response.data.data !== undefined ? response.data.data : response.data
        return {
          ...response,
          data: body,
          meta: response.data.meta
        }
      } else {
        // Error response - throw an error
        const error = new Error(response.data.error?.message || 'Unknown error')
        error.code = response.data.error?.code
        error.details = response.data.error?.details
        throw error
      }
    }
    return response
  },
  (error) => {
    // Handle 401 Unauthorized - token expired or invalid
    if (error.response?.status === 401) {
      // Only clear tokens and redirect if we're not in an iframe (TPRM context)
      // In TPRM iframe, the parent GRC app manages authentication
      const isInIframe = window.self !== window.top
      
      // Check if token exists - check both storage mechanisms as GRC shell syncs to sessionStorage
      const hasToken = sessionStorage.getItem('access_token') || 
                       sessionStorage.getItem('session_token') ||
                       localStorage.getItem('session_token') || 
                       localStorage.getItem('access_token')
      
      // Only clear and redirect if:
      // 1. Not in iframe AND no token exists, OR
      // 2. Error message indicates token is actually expired/invalid (not a server error)
      const errorRaw = error.response?.data?.error || error.response?.data?.detail || ''
      // Safely convert to string before calling .includes (value may be bool/object)
      const errorMessage = typeof errorRaw === 'string' ? errorRaw : JSON.stringify(errorRaw)
      const isTokenExpired = errorMessage.includes('expired') || errorMessage.includes('invalid') || errorMessage.includes('Token')
      
      if (!isInIframe && (!hasToken || isTokenExpired)) {
        // Clear authentication data
        localStorage.removeItem('session_token')
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('current_user')
        
        // Redirect to login if not already there
        if (window.location.pathname !== '/login') {
          window.location.href = '/login'
        }
      } else if (isInIframe && !hasToken) {
        // In iframe but no token - request auth from parent
        if (window.parent && window.parent !== window) {
          window.parent.postMessage({ type: 'TPRM_REDIRECT_TO_LOGIN' }, '*')
        }
      }
      // If we have a token and it's a server error, don't clear tokens - just throw the error
    }
    
    // Handle 403 Forbidden - permission denied
    // NOTE: Do NOT auto-redirect here - components handle 403 individually.
    // Auto-redirect was causing loops.
    if (error.response?.status === 403) {
      const errorData = error.response.data
      const errorMessage = errorData?.error || errorData?.message || 'You do not have permission to access this resource.'
      console.warn('[TPRM http] 403 Forbidden:', errorMessage, error.config?.url)
      sessionStorage.setItem('access_denied_error', JSON.stringify({
        message: typeof errorMessage === 'string' ? errorMessage : JSON.stringify(errorMessage),
        code: errorData?.code || '403',
        timestamp: new Date().toISOString(),
        path: window.location.pathname
      }))
      // Fall through - let component handle the error
    }
    
    // Handle network errors or other axios errors
    if (error.response) {
      // Server responded with error status
      const errorData = error.response.data
      if (errorData && errorData.error) {
        const newError = new Error(errorData.error.message || 'Server error')
        newError.code = errorData.error.code
        newError.details = errorData.error.details
        newError.response = error.response
        throw newError
      }
    }
    throw error
  }
)

export default http
