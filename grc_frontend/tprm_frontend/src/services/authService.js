import axios from 'axios'
import { getTprmApiBaseUrl } from '@/utils/backendEnv'

const API_BASE_URL = getTprmApiBaseUrl()

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
   * Step 1: Login with username and password, receive OTP via email
   */
  async login(username, password) {
    try {
      const response = await authApi.post('/login/', {
        username,
        password
      })
      return {
        success: true,
        data: response.data,
        requiresOtp: response.data.requires_otp,
        user: response.data.user,
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
   * Step 2: Verify OTP code
   */
  async verifyOtp(username, otp) {
    try {
      const response = await authApi.post('/verify-otp/', {
        username,
        otp
      })
      
      if (response.data.success) {
        // Store authentication data
        const token = response.data.session_token || response.data.access_token
        localStorage.setItem('session_token', token)
        localStorage.setItem('access_token', response.data.access_token)
        localStorage.setItem('refresh_token', response.data.refresh_token)
        localStorage.setItem('current_user', JSON.stringify(response.data.user))
      }
      
      return {
        success: true,
        data: response.data,
        user: response.data.user,
        token: response.data.session_token || response.data.access_token
      }
    } catch (error) {
      console.error('OTP verification error:', error)
      return {
        success: false,
        error: error.response?.data?.message || 'OTP verification failed. Please try again.',
        details: error.response?.data
      }
    }
  },

  /**
   * Resend OTP code
   */
  async resendOtp(username) {
    try {
      const response = await authApi.post('/resend-otp/', {
        username
      })
      return {
        success: true,
        message: response.data.message
      }
    } catch (error) {
      console.error('Resend OTP error:', error)
      return {
        success: false,
        error: error.response?.data?.message || 'Failed to resend OTP. Please try again.',
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
   * Get MFA status for a user
   */
  async getMfaStatus(username) {
    try {
      const response = await authApi.get('/status/', {
        params: { username }
      })
      return {
        success: true,
        data: response.data
      }
    } catch (error) {
      console.error('MFA status error:', error)
      return {
        success: false,
        error: error.response?.data?.message || 'Failed to get MFA status'
      }
    }
  },

  /**
   * Get current user from localStorage
   */
  getCurrentUser() {
    try {
      const userStr = localStorage.getItem('current_user')
      return userStr ? JSON.parse(userStr) : null
    } catch (error) {
      console.error('Error getting current user:', error)
      return null
    }
  },

  /**
   * Get current session token
   */
  getSessionToken() {
    return localStorage.getItem('session_token')
  },

  /**
   * Check if user is authenticated
   */
  isAuthenticated() {
    const token = this.getSessionToken()
    const user = this.getCurrentUser()
    return !!(token && user)
  }
}

