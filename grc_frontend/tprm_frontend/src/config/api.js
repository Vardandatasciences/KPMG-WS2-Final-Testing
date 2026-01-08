// Helper to detect if we should use localhost
const getDefaultBaseUrl = () => {
  // Priority 1: Explicitly set API base URL from environment
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL
  }
  
  // Priority 2: Explicitly set TPRM API base URL from environment
  if (import.meta.env.VITE_TPRM_API_BASE_URL) {
    return import.meta.env.VITE_TPRM_API_BASE_URL
  }
  
  // Priority 3: Build URL from backend host/port environment variables
  const backendHost = import.meta.env.VITE_BACKEND_HOST || import.meta.env.VITE_API_HOST
  const backendPort = import.meta.env.VITE_BACKEND_PORT || import.meta.env.VITE_API_PORT || '8000'
  const backendProtocol = import.meta.env.VITE_BACKEND_PROTOCOL || import.meta.env.VITE_API_PROTOCOL || 'http'
  
  if (backendHost) {
    const portSegment = backendPort ? `:${backendPort}` : ''
    return `${backendProtocol}://${backendHost}${portSegment}/api/tprm`
  }
  
  // Priority 4: Check if we're in development mode and on localhost
  const isDevelopment = import.meta.env.MODE === 'development' || import.meta.env.DEV
  const isLocalhost = typeof window !== 'undefined' && window.location && 
                      (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
  
  // Use localhost in development if on localhost (fallback)
  if (isDevelopment && isLocalhost) {
    const protocol = window.location.protocol
    const hostname = window.location.hostname
    const defaultBackendPort = backendPort || '8000'
    return `${protocol}//${hostname}:${defaultBackendPort}/api/tprm`
  }
  
  // Priority 5: Use production URL from environment or default
  return import.meta.env.VITE_PRODUCTION_API_URL || 'https://grc-tprm.vardaands.com/api/tprm'
}

// API Configuration
const BASE_URL = getDefaultBaseUrl()
const API_CONFIG = {
  BASE_URL: BASE_URL,
  RFP_APPROVAL_BASE: import.meta.env.VITE_RFP_APPROVAL_BASE || `${BASE_URL}/rfp-approval`,
  TIMEOUT: parseInt(import.meta.env.VITE_API_TIMEOUT || '10000', 10), // Default 10 seconds, from env
}

// Log the API configuration in development
if (import.meta.env.MODE === 'development' || import.meta.env.DEV) {
  console.log('[API Config] Environment Variables:')
  console.log('  - VITE_API_BASE_URL:', import.meta.env.VITE_API_BASE_URL || 'not set')
  console.log('  - VITE_TPRM_API_BASE_URL:', import.meta.env.VITE_TPRM_API_BASE_URL || 'not set')
  console.log('  - VITE_BACKEND_HOST:', import.meta.env.VITE_BACKEND_HOST || 'not set')
  console.log('  - VITE_BACKEND_PORT:', import.meta.env.VITE_BACKEND_PORT || 'not set')
  console.log('  - VITE_PRODUCTION_API_URL:', import.meta.env.VITE_PRODUCTION_API_URL || 'not set')
  console.log('[API Config] Resolved Configuration:')
  console.log('  - BASE_URL:', API_CONFIG.BASE_URL)
  console.log('  - RFP_APPROVAL_BASE:', API_CONFIG.RFP_APPROVAL_BASE)
  console.log('  - TIMEOUT:', API_CONFIG.TIMEOUT)
}

// API Endpoints
const API_ENDPOINTS = {
  // RFP Approval endpoints
  RFP_APPROVAL: {
    WORKFLOWS: '/workflows/',
    USERS: '/users/',
    REQUESTS: '/requests/',
    STAGES: '/stages/',
    COMMENTS: '/comments/',
    USER_APPROVALS: '/user-approvals/',
    UPDATE_STAGE_STATUS: '/update-stage-status/',
  },
  // Access Request endpoints
  CREATE_ACCESS_REQUEST: `${API_CONFIG.BASE_URL}/rbac/access-requests/`,
  GET_ACCESS_REQUESTS: (userId) => `${API_CONFIG.BASE_URL}/rbac/access-requests/${userId}/`,
  UPDATE_ACCESS_REQUEST_STATUS: (requestId) => `${API_CONFIG.BASE_URL}/rbac/access-requests/${requestId}/status/`,
  // Add other API endpoints as needed
}

// Helper function to build full API URLs
const buildApiUrl = (endpoint, baseUrl = API_CONFIG.RFP_APPROVAL_BASE) => {
  return `${baseUrl}${endpoint}`
}

// Helper function to get JWT token
const getAuthToken = () => {
  return localStorage.getItem('session_token') || 
         localStorage.getItem('auth_token') || 
         localStorage.getItem('access_token')
}

// Helper function for API calls with error handling and JWT authentication
const apiCall = async (url, options = {}) => {
  const token = getAuthToken()
  const { skipRedirect = false, ...fetchOptions } = options
  
  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
    },
    ...fetchOptions,
  }

  try {
    const response = await fetch(url, defaultOptions)

    // Handle 401 Unauthorized
    if (response.status === 401) {
      console.error('🔒 Authentication failed')
      if (!skipRedirect) {
        localStorage.removeItem('session_token')
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('current_user')
        if (window.location.pathname !== '/login') {
          window.location.href = '/login'
          // Return a pending promise that never resolves to prevent further execution
          return new Promise(() => {})
        }
      }
      throw new Error('Authentication required')
    }

    // Handle 403 Forbidden
    if (response.status === 403) {
      console.error('🚫 Access denied - insufficient permissions')
      const errorData = await response.json().catch(() => ({}))
      const errorMessage = errorData?.error || errorData?.message || 'You do not have permission to access this resource.'
      const errorCode = errorData?.code || '403'
      
      if (!skipRedirect) {
        sessionStorage.setItem('access_denied_error', JSON.stringify({
          message: errorMessage,
          code: errorCode,
          timestamp: new Date().toISOString(),
          path: window.location.pathname
        }))
        if (window.location.pathname !== '/access-denied') {
          console.log('🔄 Redirecting to /access-denied page...')
          window.location.href = '/access-denied'
          // Return a pending promise that never resolves to prevent further execution
          return new Promise(() => {})
        }
      }
      throw new Error(errorMessage)
    }

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    // Check if response is JSON
    const contentType = response.headers.get('content-type')
    if (contentType && contentType.includes('application/json')) {
      return await response.json()
    } else {
      // If not JSON, it might be an HTML error page
      const text = await response.text()
      console.error('Non-JSON response received:', text.substring(0, 200))
      throw new Error(`Server returned non-JSON response. Status: ${response.status}`)
    }
  } catch (error) {
    console.error('API call failed:', error)
    throw error
  }
}

export {
  API_CONFIG,
  API_ENDPOINTS,
  buildApiUrl,
  apiCall,
  getAuthToken
}