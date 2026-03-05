import axios from 'axios'
import { getApiOrigin } from '@/utils/backendEnv'

// Get API base URL - use origin so we can pass full paths like /api/v1/...
const API_BASE_URL = getApiOrigin()

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 20000,
})

// Add JWT authentication to all requests (except public endpoints)
api.interceptors.request.use(
  (config) => {
    // Check if this is a public endpoint that shouldn't require auth
    const isPublicEndpoint = config.url?.includes('/public/') || 
                             config.url?.includes('questionnaire-response-public') ||
                             (config.url?.includes('get_assignment_responses') && 
                              window.location.pathname === '/questionnaire-response-public') ||
                             (config.url?.includes('save_responses') && 
                              window.location.pathname === '/questionnaire-response-public') ||
                             (config.url?.includes('submit_final_responses') && 
                              window.location.pathname === '/questionnaire-response-public') ||
                             (config.url?.includes('upload_files') && 
                              window.location.pathname === '/questionnaire-response-public') ||
                             (config.url?.includes('remove_file') && 
                              window.location.pathname === '/questionnaire-response-public')
    
    if (!isPublicEndpoint) {
      const token = localStorage.getItem('session_token')
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
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
      // Check if this is a public endpoint (like questionnaire-response-public)
      const isPublicEndpoint = error.config?.url?.includes('/public/') || 
                               error.config?.url?.includes('questionnaire-response-public')
      
      // Handle 401 Unauthorized (but NOT for public endpoints)
      if (error.response.status === 401 && !isPublicEndpoint) {
        console.error('[API] Authentication failed - redirecting to login')
        localStorage.removeItem('session_token')
        localStorage.removeItem('user')
        window.location.href = '/login'
      }
      // Handle 403 Forbidden
      else if (error.response.status === 403) {
        console.error('[API] Access denied - insufficient permissions')
        // Skip redirect for public endpoints
        const isPublicEndpoint = error.config?.url?.includes('/public/') || 
                                 error.config?.url?.includes('questionnaire-response-public') ||
                                 error.config?.url?.includes('get_assignment_responses') ||
                                 error.config?.url?.includes('save_responses') ||
                                 error.config?.url?.includes('submit_final_responses') ||
                                 error.config?.url?.includes('upload_files') ||
                                 error.config?.url?.includes('remove_file')
        
        if (!isPublicEndpoint) {
          // Optionally redirect to access denied page for authenticated routes
          // window.location.href = '/access-denied'
        }
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

