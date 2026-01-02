import axios from 'axios'
import { getTprmApiBaseUrl } from '@/utils/backendEnv'

// Create axios instance with base configuration
const http = axios.create({
  baseURL: getTprmApiBaseUrl(),
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add JWT token
http.interceptors.request.use(
  (config) => {
    // Add JWT token from localStorage
    const token = localStorage.getItem('session_token')
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
        // Success response - return the data directly
        return {
          ...response,
          data: response.data.data,
          meta: response.data.meta
        }
      } else {
        // Error response - throw an error
        // Handle both string and object error formats
        const errorMessage = typeof response.data.error === 'string' 
          ? response.data.error 
          : (response.data.error?.message || 'Unknown error')
        const error = new Error(errorMessage)
        error.code = typeof response.data.error === 'object' ? response.data.error?.code : undefined
        error.details = typeof response.data.error === 'object' ? response.data.error?.details : undefined
        error.response = response  // Preserve original response for error handling
        throw error
      }
    }
    return response
  },
  (error) => {
    // Handle 401 Unauthorized - token expired or invalid
    if (error.response?.status === 401) {
      // Clear authentication data
      localStorage.removeItem('session_token')
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('current_user')
      
      // Redirect to login if not already there
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    
    // Handle 403 Forbidden - permission denied
    if (error.response?.status === 403) {
      const errorData = error.response.data
      const errorMessage = errorData?.error || errorData?.message || 'You do not have permission to access this resource.'
      const errorCode = errorData?.code || '403'
      
      // Store error info in sessionStorage so AccessDenied page can display it
      sessionStorage.setItem('access_denied_error', JSON.stringify({
        message: errorMessage,
        code: errorCode,
        timestamp: new Date().toISOString(),
        path: window.location.pathname
      }))
      
      // Redirect to access denied page
      if (window.location.pathname !== '/access-denied') {
        console.log('🔄 Redirecting to /access-denied page...')
        window.location.href = '/access-denied'
        // Return a promise that never resolves to stop execution
        return new Promise(() => {})
      }
    }
    
    // Handle network errors or other axios errors
    if (error.response) {
      // Server responded with error status
      const errorData = error.response.data
      if (errorData) {
        // Handle both string and object error formats
        let errorMessage = 'Server error'
        let errorCode = undefined
        let errorDetails = undefined
        
        if (errorData.error) {
          if (typeof errorData.error === 'string') {
            errorMessage = errorData.error
          } else if (typeof errorData.error === 'object') {
            errorMessage = errorData.error.message || errorData.error.error || 'Server error'
            errorCode = errorData.error.code
            errorDetails = errorData.error.details
          }
        } else if (errorData.message) {
          errorMessage = errorData.message
        }
        
        const newError = new Error(errorMessage)
        newError.code = errorCode || errorData.code
        newError.details = errorDetails || errorData.details
        newError.response = error.response
        throw newError
      }
    }
    throw error
  }
)

export default http
