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
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add JWT token from localStorage (try multiple possible keys)
    const token = localStorage.getItem('session_token') || 
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
      
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    
    // Handle 403 Forbidden - permission denied
    if (error.response?.status === 403) {
      const errorData = error.response.data
      const errorMessage = errorData?.error || errorData?.message || 'You do not have permission to access this resource.'
      const errorCode = errorData?.code || '403'
      
      // Store error info in sessionStorage for AccessDenied page
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
    
    return Promise.reject(error)
  }
)

export default api
