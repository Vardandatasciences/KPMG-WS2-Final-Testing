import axios from 'axios'
import { getApiOrigin } from '@/utils/backendEnv.js'

const API_ORIGIN = getApiOrigin()
// Create axios instance with base configuration
const apiClient = axios.create({
  baseURL: API_ORIGIN,
  timeout: 10000,
  withCredentials: true, // Important for session cookies
  headers: {
    'Content-Type': 'application/json',
  }
})

// Helper to get token from any of the storage keys
function getStoredToken() {
  const keys = ['session_token', 'token', 'access_token', 'jwt_token']
  for (const key of keys) {
    const val = localStorage.getItem(key)
    if (val) return val
  }
  return null
}

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    console.log(`Making ${config.method?.toUpperCase()} request to: ${config.url}`)
    
    // Add JWT token from localStorage (check multiple keys for GRC compatibility)
    const token = getStoredToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    // For FormData requests, let the browser set the Content-Type header
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type']
    }
    
    return config
  },
  (error) => {
    console.error('Request error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor
apiClient.interceptors.response.use(
  (response) => {
    console.log(`Response received from: ${response.config.url}`, response.status)
    return response
  },
  (error) => {
    console.error('Response error:', error)
    
    // Handle 401 Unauthorized - token expired or invalid
    if (error.response?.status === 401) {
      console.warn('⚠️ 401 Unauthorized - Token expired or invalid')
      
      // Try to refresh token if available
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken && !error.config._retry) {
        console.log('Attempting to refresh token...')
        error.config._retry = true
        
        // Import auth service and attempt token refresh
        import('../services/authService.js').then(({ default: authService }) => {
          return authService.refreshToken().then(result => {
            if (result.success) {
              console.log('Token refreshed successfully, retrying request')
              // Retry the original request with new token
              error.config.headers.Authorization = `Bearer ${result.token}`
              return apiClient.request(error.config)
            } else {
              // Refresh failed, redirect to login
              console.error('Token refresh failed')
              localStorage.removeItem('session_token')
              localStorage.removeItem('access_token')
              localStorage.removeItem('refresh_token')
              localStorage.removeItem('current_user')
              
              if (window.location.pathname !== '/login' && !window.location.pathname.includes('/vendor-login')) {
                window.location.href = '/login'
              }
            }
          })
        }).catch(err => {
          console.error('Error refreshing token:', err)
          // Clear authentication data and redirect
          localStorage.removeItem('session_token')
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          localStorage.removeItem('current_user')
          
          if (window.location.pathname !== '/login' && !window.location.pathname.includes('/vendor-login')) {
            window.location.href = '/login'
          }
        })
      } else {
        // No refresh token or retry already failed
        localStorage.removeItem('session_token')
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('current_user')
        
        if (window.location.pathname !== '/login' && !window.location.pathname.includes('/vendor-login')) {
          window.location.href = '/login'
        }
      }
    }
    
    // Handle 403 Forbidden - permission denied
    // Don't redirect automatically - let components handle the error
    if (error.response?.status === 403) {
      const errorData = error.response.data
      const errorMessage = errorData?.error || errorData?.message || 'You do not have permission to access this resource.'
      const errorCode = errorData?.code || '403'
      
      console.warn('⚠️ 403 Forbidden:', errorMessage)
      
      // Store error info but don't redirect - let the component handle it
      sessionStorage.setItem('access_denied_error', JSON.stringify({
        message: errorMessage,
        code: errorCode,
        timestamp: new Date().toISOString(),
        path: window.location.pathname,
        url: error.config?.url
      }))
      
      // Attach more detailed error info to the error object
      error.permissionDenied = true
      error.permissionError = errorMessage
    }
    
    return Promise.reject(error)
  }
)

export default apiClient
