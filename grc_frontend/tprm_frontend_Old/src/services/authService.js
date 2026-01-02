import axios from 'axios'
import { getTprmApiBaseUrl } from '@/utils/backendEnv'

const API_BASE_URL = getTprmApiBaseUrl()

const TOKEN_STORAGE_KEYS = [
  'session_token',
  'token',
  'access_token',
  'jwt_token'
]

const USER_STORAGE_KEYS = [
  'current_user',
  'user'
]

const getFromStorage = (keys) => {
  for (const key of keys) {
    const value = localStorage.getItem(key)
    if (value) {
      return { key, value }
    }
  }
  return { key: null, value: null }
}

const getStoredToken = () => {
  const { value } = getFromStorage(TOKEN_STORAGE_KEYS)
  return value
}

// Create axios instance with default config
const authApi = axios.create({
  baseURL: `${API_BASE_URL}/auth`,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true
})

// Request interceptor to add token
authApi.interceptors.request.use(
  (config) => {
    const token = getStoredToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor to handle errors
authApi.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('session_token')
      localStorage.removeItem('current_user')
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export default {
  /**
   * Login with username and password (single-step, MFA disabled)
   */
  async login(username, password) {
    try {
      const response = await authApi.post('/login/', {
        username,
        password
      })

      const token = response.data.session_token || response.data.access_token

      if (token) {
        localStorage.setItem('session_token', token)
      }
      if (response.data.access_token) {
        localStorage.setItem('access_token', response.data.access_token)
      }
      if (response.data.refresh_token) {
        localStorage.setItem('refresh_token', response.data.refresh_token)
      }
      localStorage.setItem('current_user', JSON.stringify(response.data.user))

      return {
        success: true,
        data: response.data,
        user: response.data.user,
        token,
        accessToken: response.data.access_token,
        refreshToken: response.data.refresh_token,
        message: response.data.message
      }
    } catch (error) {
      console.error('Login error:', error)
      return {
        success: false,
        error: error.response?.data?.message || 'Login failed. Please try again.',
        details: error.response?.data
      }
    }
  },

  /**
   * Validate current session
   */
  async validateSession() {
    try {
      const response = await authApi.get('/validate-session/')
      return {
        success: true,
        user: response.data.user
      }
    } catch (error) {
      console.error('Session validation error:', error)
      return {
        success: false,
        error: error.response?.data?.message || 'Session validation failed'
      }
    }
  },

  /**
   * Refresh access token
   */
  async refreshToken() {
    try {
      const refreshToken = localStorage.getItem('refresh_token')
      if (!refreshToken) {
        throw new Error('No refresh token available')
      }

      const response = await authApi.post('/refresh-token/', {
        refresh_token: refreshToken
      })

      if (response.data.success) {
        const newToken = response.data.access_token
        localStorage.setItem('session_token', newToken)
        localStorage.setItem('access_token', newToken)
      }

      return {
        success: true,
        token: response.data.access_token
      }
    } catch (error) {
      console.error('Token refresh error:', error)
      return {
        success: false,
        error: error.response?.data?.message || 'Token refresh failed'
      }
    }
  },

  /**
   * Logout user
   */
  async logout() {
    try {
      console.log('AuthService: Calling logout API...')
      const response = await authApi.post('/logout/')
      console.log('AuthService: Logout API response:', response.data)
      
      // Clear local storage
      localStorage.removeItem('session_token')
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('current_user')
      console.log('AuthService: Local storage cleared')
      
      return {
        success: true,
        message: response.data?.message || 'Logged out successfully'
      }
    } catch (error) {
      console.error('AuthService: Logout API error:', error)
      console.error('AuthService: Error details:', error.response?.data)
      
      // Still clear local storage even if API call fails
      localStorage.removeItem('session_token')
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('current_user')
      console.log('AuthService: Local storage cleared despite error')
      
      return {
        success: false,
        error: error.response?.data?.message || 'Logout API call failed, but local storage cleared'
      }
    }
  },

  /**
   * Get current user from localStorage
   */
  getCurrentUser() {
    try {
      const { value } = getFromStorage(USER_STORAGE_KEYS)
      return value ? JSON.parse(value) : null
    } catch (error) {
      console.error('Error getting current user:', error)
      return null
    }
  },

  /**
   * Get current session token
   */
  getSessionToken() {
    return getStoredToken()
  },

  /**
   * Check if user is authenticated
   */
  isAuthenticated() {
    const token = this.getSessionToken()
    const user = this.getCurrentUser()
    const grcAuthFlag = localStorage.getItem('isAuthenticated') === 'true' || localStorage.getItem('is_logged_in') === 'true'
    return !!user && (!!token || grcAuthFlag)
  }
}

