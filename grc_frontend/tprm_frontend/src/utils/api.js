import axios from 'axios'
import { getApiOrigin } from '@/utils/backendEnv'

// Get API base URL - use origin so we can pass full paths like /api/v1/...
const API_BASE_URL = getApiOrigin()

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 20000,
})

// Add JWT authentication to all requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('session_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Handle authentication errors and connection issues
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle connection errors
    if (!error.response) {
      const isConnectionError = error.code === 'ERR_NETWORK' || 
                                error.code === 'ERR_CONNECTION_REFUSED' ||
                                error.message?.includes('ERR_CONNECTION_REFUSED') ||
                                error.message?.includes('Network Error')
      
      if (isConnectionError) {
        console.error('[API] Connection error - Backend server may not be running')
        console.error(`[API] Attempted to connect to: ${API_BASE_URL}`)
        console.error('[API] Error details:', {
          code: error.code,
          message: error.message,
          config: error.config
        })
      }
    }
    
    if (error.response) {
      // Handle 401 Unauthorized
      if (error.response.status === 401) {
        console.error('[API] Authentication failed - redirecting to login')
        localStorage.removeItem('session_token')
        localStorage.removeItem('user')
        window.location.href = '/login'
      }
      // Handle 403 Forbidden
      else if (error.response.status === 403) {
        console.error('[API] Access denied - insufficient permissions')
        // Optionally redirect to access denied page
        // window.location.href = '/access-denied'
      }
    }
    return Promise.reject(error)
  }
)

// Helper function for API calls
export const apiCall = async (url, options = {}) => {
  const config = {
    url,
    method: options.method || 'GET',
    ...options
  }
  
  if (options.data) {
    config.data = options.data
  }
  
  return api(config)
}

export default api

