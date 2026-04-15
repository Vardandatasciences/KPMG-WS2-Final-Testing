import axios from 'axios'
import { getApiOrigin } from '@/utils/backendEnv.js'
import { getParentPostMessageTargetOrigin } from '@/utils/parentPostMessageOrigin.js'
import { clearLegacyClientJwtKeys } from '@/utils/legacyAuthStorage.js'

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

// Request interceptor — cookie-first; never attach stale Bearer from storage
apiClient.interceptors.request.use(
  (config) => {
    console.log(`Making ${config.method?.toUpperCase()} request to: ${config.url}`)
    clearLegacyClientJwtKeys()
    try {
      delete config.headers.Authorization
    } catch {
      /* ignore */
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
      const data = error.response?.data || {}
      if (data.session_invalidated === true) {
        localStorage.setItem('auth_logout_reason', 'session_invalidated')
      }
      // Clear authentication data from both sessionStorage and localStorage
      sessionStorage.removeItem('session_token')
      sessionStorage.removeItem('access_token')
      sessionStorage.removeItem('refresh_token')
      sessionStorage.removeItem('current_user')
      localStorage.removeItem('session_token')
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('current_user')
      
      // If in iframe, request auth from GRC parent instead of redirecting to login
      const isInIframe = window.self !== window.top
      if (isInIframe && window.parent) {
        console.warn('[TPRM] 401 received - requesting auth from GRC parent')
        window.parent.postMessage({ type: 'TPRM_REDIRECT_TO_LOGIN' }, getParentPostMessageTargetOrigin())
      } else if (window.location.pathname !== '/login' && !window.location.pathname.includes('/vendor-login')) {
        window.location.href = '/login'
      }
    }
    
    // Handle 403 Forbidden - permission denied
    // NOTE: Do NOT auto-redirect here - components handle 403 individually.
    // Auto-redirect was causing loops (e.g., vendor-core, notifications, contract endpoints).
    if (error.response?.status === 403) {
      const errorData = error.response.data
      const errorMessage = errorData?.error || errorData?.message || 'You do not have permission to access this resource.'
      console.warn('[TPRM] 403 Forbidden:', errorMessage, error.config?.url)
      // Store error info in sessionStorage for optional display by components
      sessionStorage.setItem('access_denied_error', JSON.stringify({
        message: errorMessage,
        code: errorData?.code || '403',
        timestamp: new Date().toISOString(),
        path: window.location.pathname
      }))
      // Let component handle the error - no redirect
    }
    
    return Promise.reject(error)
  }
)

export default apiClient
