import axios from 'axios'
import { API_BASE_URL } from '../config/api.js'

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
  baseURL: `${API_BASE_URL}/api`,
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
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('current_user')
      if (window.location.pathname !== '/login' && window.location.pathname !== '/Login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export default {
  /**
   * Login with username/password, loginType, and captchaToken
   * @param {string} username - Username or user ID
   * @param {string} password - User password
   * @param {string} loginType - 'username' or 'userid'
   * @param {string} captchaToken - reCAPTCHA token
   */
  async login(username, password, loginType = 'username', captchaToken) {
    try {
      const response = await authApi.post('/jwt/login/', {
        username,
        password,
        login_type: loginType,
        captcha_token: captchaToken
      })

      const token = response.data.access_token
      const refreshToken = response.data.refresh_token

      if (token) {
        localStorage.setItem('session_token', token)
        localStorage.setItem('access_token', token)
      }
      if (refreshToken) {
        localStorage.setItem('refresh_token', refreshToken)
      }
      if (response.data.user) {
        localStorage.setItem('current_user', JSON.stringify(response.data.user))
        localStorage.setItem('user_id', response.data.user.UserId)
        // Set user name and email for navbar and other components
        if (response.data.user.UserName) {
          localStorage.setItem('user_name', response.data.user.UserName)
        }
        if (response.data.user.Email) {
          localStorage.setItem('user_email', response.data.user.Email)
        }
        // MULTI-TENANCY: Store tenant info if available
        if (response.data.user.tenant_id) {
          localStorage.setItem('tenant_id', response.data.user.tenant_id)
        }
        if (response.data.user.tenant_name) {
          localStorage.setItem('tenant_name', response.data.user.tenant_name)
        }
      }
      // MULTI-TENANCY: Also check for tenant info in token response
      if (response.data.tenant_id) {
        localStorage.setItem('tenant_id', response.data.tenant_id)
      }
      if (response.data.tenant_name) {
        localStorage.setItem('tenant_name', response.data.tenant_name)
      }
      if (response.data.access_token_expires) {
        localStorage.setItem('access_token_expires', response.data.access_token_expires)
      }
      if (response.data.refresh_token_expires) {
        localStorage.setItem('refresh_token_expires', response.data.refresh_token_expires)
      }
      
      // CRITICAL: Set is_logged_in flag - this is required for App.vue to show sidebar/navbar
      localStorage.setItem('is_logged_in', 'true')
      localStorage.setItem('isAuthenticated', 'true')

      return {
        success: true,
        data: response.data,
        user: response.data.user,
        token,
        accessToken: token,
        refreshToken: refreshToken,
        message: response.data.message,
        requiresMfa: response.data.requires_mfa || false,
        emailMasked: response.data.email_masked,
        consent_required: response.data.consent_required
      }
    } catch (error) {
      console.error('JWT Login error:', error)
      return {
        success: false,
        error: error.response?.data?.message || 'Login failed. Please try again.',
        details: error.response?.data
      }
    }
  },

  /**
   * Initiate Google OAuth flow
   */
  async initiateGoogleOAuth() {
    try {
      const response = await authApi.get('/google-oauth/initiate/')
      
      if (response.data.status === 'success' && response.data.authorization_url) {
        // Redirect to Google OAuth
        window.location.href = response.data.authorization_url
      } else {
        throw new Error(response.data.message || 'Failed to initiate Google OAuth')
      }
    } catch (error) {
      console.error('Google OAuth initiate error:', error)
      throw error
    }
  },

  /**
   * Handle Google OAuth callback
   * @param {string} accessToken - Access token from OAuth
   * @param {string} refreshToken - Refresh token from OAuth
   * @param {string} userId - User ID
   * @param {string} consentRequired - Whether consent is required
   * @param {string} accessTokenExpires - Access token expiration
   * @param {string} refreshTokenExpires - Refresh token expiration
   */
  async handleGoogleOAuthCallback(accessToken, refreshToken, userId, consentRequired, accessTokenExpires, refreshTokenExpires) {
    try {
      if (accessToken) {
        localStorage.setItem('session_token', accessToken)
        localStorage.setItem('access_token', accessToken)
      }
      if (refreshToken) {
        localStorage.setItem('refresh_token', refreshToken)
      }
      if (userId) {
        localStorage.setItem('user_id', userId)
      }
      if (accessTokenExpires) {
        localStorage.setItem('access_token_expires', accessTokenExpires)
      }
      if (refreshTokenExpires) {
        localStorage.setItem('refresh_token_expires', refreshTokenExpires)
      }

      // Fetch user data if needed
      if (userId) {
        try {
          const userResponse = await authApi.get(`/user-profile/${userId}/`)
          if (userResponse.data) {
            localStorage.setItem('current_user', JSON.stringify(userResponse.data))
            // Set user name and email for navbar and other components
            if (userResponse.data.UserName) {
              localStorage.setItem('user_name', userResponse.data.UserName)
            }
            if (userResponse.data.Email) {
              localStorage.setItem('user_email', userResponse.data.Email)
            }
          }
        } catch (err) {
          console.warn('Could not fetch user profile:', err)
        }
      }
      
      // CRITICAL: Set is_logged_in flag - this is required for App.vue to show sidebar/navbar
      localStorage.setItem('is_logged_in', 'true')
      localStorage.setItem('isAuthenticated', 'true')

      return {
        success: true,
        consent_required: consentRequired === 'true' || consentRequired === true
      }
    } catch (error) {
      console.error('Google OAuth callback error:', error)
      return {
        success: false,
        error: error.message || 'Failed to complete Google sign-in'
      }
    }
  },

  /**
   * Clear all authentication data
   */
  clearAuthData() {
    localStorage.removeItem('session_token')
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('current_user')
    localStorage.removeItem('user_id')
    localStorage.removeItem('access_token_expires')
    localStorage.removeItem('refresh_token_expires')
    localStorage.removeItem('isAuthenticated')
    localStorage.removeItem('is_logged_in')
    // MULTI-TENANCY: Clear tenant data
    localStorage.removeItem('tenant_id')
    localStorage.removeItem('tenant_name')
  },

  /**
   * Validate current session
   */
  async validateSession() {
    try {
      const response = await authApi.get('/jwt/verify/')
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

      const response = await authApi.post('/jwt/refresh/', {
        refresh_token: refreshToken
      })

      if (response.data.access_token) {
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
      const response = await authApi.post('/jwt/logout/')
      console.log('AuthService: Logout API response:', response.data)
      
      // Clear local storage
      this.clearAuthData()
      console.log('AuthService: Local storage cleared')
      
      return {
        success: true,
        message: response.data?.message || 'Logged out successfully'
      }
    } catch (error) {
      console.error('AuthService: Logout API error:', error)
      console.error('AuthService: Error details:', error.response?.data)
      
      // Still clear local storage even if API call fails
      this.clearAuthData()
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
  },

  /**
   * MULTI-TENANCY: Get current tenant ID
   */
  getTenantId() {
    return localStorage.getItem('tenant_id')
  },

  /**
   * MULTI-TENANCY: Get current tenant name
   */
  getTenantName() {
    return localStorage.getItem('tenant_name')
  },

  /**
   * MULTI-TENANCY: Get tenant info from token
   * Decodes JWT token and extracts tenant information
   */
  getTenantInfoFromToken() {
    try {
      const token = this.getSessionToken()
      if (!token) return null

      // Decode JWT token (without verification - client-side only)
      const base64Url = token.split('.')[1]
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      )
      
      const payload = JSON.parse(jsonPayload)
      
      return {
        tenant_id: payload.tenant_id,
        tenant_name: payload.tenant_name
      }
    } catch (error) {
      console.error('Error decoding token for tenant info:', error)
      return null
    }
  },

  /**
   * MULTI-TENANCY: Check if user belongs to a tenant
   */
  hasTenant() {
    const tenantId = this.getTenantId()
    return !!tenantId
  }
}

