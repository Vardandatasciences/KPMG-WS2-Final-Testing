// API Configuration - Centralized URL Management
// Change this variable to switch between different environments

// Environment Configuration
const ENVIRONMENT = 'development'; 
// Options: 'aws', 'local', 'development'

// API Base URLs for different environments
const API_URLS = {
  // AWS: Use domain without port - nginx proxies /api/ to localhost:8000/api/
  aws: 'https://riskavaire.vardaands.com/api/tprm',
  local: 'http://127.0.0.1:8000/api/tprm',
  development: 'http://127.0.0.1:8000/api/tprm'
};

// CRITICAL: Prevent webpack constant folding by using runtime evaluation
// This ensures the correct URL is used even after minification
const getApiBaseUrl = () => {
  // Force runtime evaluation - prevent webpack from inlining
  const currentEnv = ENVIRONMENT;
  if (currentEnv === 'aws') {
    return API_URLS.aws;
  } else if (currentEnv === 'local') {
    return API_URLS.local;
  } else if (currentEnv === 'development') {
    return API_URLS.development;
  }
  // Default fallback
  return API_URLS.aws;
};

// Get the current API base URL based on environment
// Using function call prevents webpack from inlining the wrong value
const BASE_URL = getApiBaseUrl();

// API Configuration
const API_CONFIG = {
  BASE_URL: BASE_URL,
  RFP_APPROVAL_BASE: `${BASE_URL}/rfp-approval`,
  TIMEOUT: parseInt(import.meta.env.VITE_API_TIMEOUT || '10000', 10), // Default 10 seconds, from env
}

// Log the API configuration
console.log(`🔧 TPRM API Configuration: Using ${ENVIRONMENT} environment`);
console.log(`🌐 Base URL: ${API_CONFIG.BASE_URL}`);
console.log(`  - RFP_APPROVAL_BASE: ${API_CONFIG.RFP_APPROVAL_BASE}`);
console.log(`  - TIMEOUT: ${API_CONFIG.TIMEOUT}`);

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

// Export API base URL for use in other modules
export const API_BASE_URL = BASE_URL;

export {
  API_CONFIG,
  API_ENDPOINTS,
  buildApiUrl,
  apiCall,
  getAuthToken,
  ENVIRONMENT,
  API_URLS,
  getApiBaseUrl
}