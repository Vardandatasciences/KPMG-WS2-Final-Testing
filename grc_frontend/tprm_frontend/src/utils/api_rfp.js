/**
 * Simple API client for ApprovalWorkflowCreator
 * This file provides the missing api import that ApprovalWorkflowCreator.vue expects
 */

import axios from 'axios'
import { getTprmApiV1BaseUrl } from '@/utils/backendEnv'

const API_BASE_URL = getTprmApiV1BaseUrl()

// Create axios instance with default configuration
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  withCredentials: true, // Support session cookies
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Standard token retrieval: check sessionStorage first (populated by GRC parent)
    const token = sessionStorage.getItem('access_token') || 
                  sessionStorage.getItem('session_token') ||
                  localStorage.getItem('session_token') || 
                  localStorage.getItem('auth_token') || 
                  localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    // Handle 401 Unauthorized - token expired or invalid
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token')
      localStorage.removeItem('session_token')
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('current_user')
      
      // If in iframe, request auth from GRC parent
      const isInIframe = window.self !== window.top
      if (isInIframe && window.parent) {
        window.parent.postMessage({ type: 'TPRM_REDIRECT_TO_LOGIN' }, '*')
      } else if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    
    // Handle 403 Forbidden - permission denied
    // Removed auto-redirect to prevent loops; individual components handle 403.
    if (error.response?.status === 403) {
      const errorData = error.response.data
      const errorMessage = errorData?.error || errorData?.message || 'You do not have permission to access this resource.'
      console.warn('[api_rfp] 403 Forbidden:', errorMessage, error.config?.url)
      
      // Store error info in sessionStorage for optional display by components
      sessionStorage.setItem('access_denied_error', JSON.stringify({
        message: errorMessage,
        code: errorData?.code || '403',
        timestamp: new Date().toISOString(),
        path: window.location.pathname
      }))
    }
    
    return Promise.reject(error)
  }
)

export default api
