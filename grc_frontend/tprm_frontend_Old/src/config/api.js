// API Configuration
const API_CONFIG = {
  BASE_URL: import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_TPRM_API_BASE_URL || 'https://grc-tprm.vardaands.com/api/tprm',
  RFP_APPROVAL_BASE: import.meta.env.VITE_RFP_APPROVAL_BASE || `${import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_TPRM_API_BASE_URL || 'https://grc-tprm.vardaands.com/api/tprm'}/rfp-approval`,
  TIMEOUT: 10000, // 10 seconds
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
  
  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
    },
    ...options,
  }

  try {
    const response = await fetch(url, defaultOptions)

    // Handle 401 Unauthorized
    if (response.status === 401) {
      console.error('🔒 Authentication failed - redirecting to login')
      localStorage.removeItem('session_token')
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('current_user')
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
        // Return a pending promise that never resolves to prevent further execution
        return new Promise(() => {})
      }
      throw new Error('Authentication required')
    }

    // Handle 403 Forbidden
    if (response.status === 403) {
      console.error('🚫 Access denied - insufficient permissions')
      const errorData = await response.json().catch(() => ({}))
      const errorMessage = errorData?.error || errorData?.message || 'You do not have permission to access this resource.'
      const errorCode = errorData?.code || '403'
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