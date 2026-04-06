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
    const value = sessionStorage.getItem(key) || localStorage.getItem(key)
    if (value) {
      return { key, value }
    }
  }
  return { key: null, value: null }
}

const SENSITIVE_KEYS = ['session_token', 'token', 'access_token', 'jwt_token', 'refresh_token', 'current_user']

const setSensitive = (key, value) => {
  sessionStorage.setItem(key, value)
  localStorage.removeItem(key)
}

const removeSensitive = (key) => {
  sessionStorage.removeItem(key)
  localStorage.removeItem(key)
}

// One-time migration: move legacy sensitive auth data out of localStorage.
SENSITIVE_KEYS.forEach((k) => {
  const v = localStorage.getItem(k)
  if (v) {
    sessionStorage.setItem(k, v)
    localStorage.removeItem(k)
  }
})
 
// Cookie-first auth: tokens are stored in HttpOnly cookies.
// We keep this for backward compatibility, but new flows should not depend on it.
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
      const data = error.response?.data || {}
      // ONLY clear tokens and redirect on true session expiry.
      // Do NOT clear tokens on every 401 - a transient 401 should not wipe
      // valid sessionStorage tokens and kill all subsequent requests.
      if (data.session_expired === true) {
        removeSensitive('session_token')
        removeSensitive('access_token')
        removeSensitive('refresh_token')
        removeSensitive('current_user')
        localStorage.setItem('auth_logout_reason', 'session_expired')
        if (window.location.pathname !== '/login' && window.location.pathname !== '/Login') {
          window.location.href = '/login'
        }
      }
      // Note: session_invalidated is no longer used since we disabled the session
      // token cache check. Don't treat it as a reason to wipe tokens.
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

      // Cookie-first: backend sets HttpOnly cookies for access/refresh tokens.
      // BUT: We must also store in sessionStorage so TprmWrapper can pass token to TPRM iframe.
      // GRC API calls use cookies; TPRM iframe receives token via postMessage.
      if (token) {
        sessionStorage.setItem('access_token', token)
        localStorage.removeItem('access_token')
      } else {
        sessionStorage.removeItem('access_token')
      }
      if (refreshToken) {
        sessionStorage.setItem('refresh_token', refreshToken)
        localStorage.removeItem('refresh_token')
      } else {
        sessionStorage.removeItem('refresh_token')
      }
      sessionStorage.removeItem('session_token')
      localStorage.removeItem('session_token')
      if (response.data.user) {
        setSensitive('current_user', JSON.stringify(response.data.user))
        const uid =
          response.data.user.UserId ??
          response.data.user.user_id ??
          response.data.user.userid ??
          response.data.user.id
        if (uid != null && uid !== '') {
          localStorage.setItem('user_id', String(uid))
        }
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

      // If user_id still missing, derive from JWT payload (router + shell need this)
      if (!localStorage.getItem('user_id') && token) {
        try {
          const payload = JSON.parse(atob(token.split('.')[1]))
          const fromJwt =
            payload.user_id ?? payload.userid ?? payload.UserId ?? payload.sub
          if (fromJwt != null && fromJwt !== '') {
            localStorage.setItem('user_id', String(fromJwt))
          }
        } catch (e) {
          /* ignore */
        }
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
   * Fetch one-time Google OAuth callback payload from backend session
   */
  async getGoogleOAuthCallbackPayload(handoffKey = null) {
    try {
      const response = await authApi.get('/google-oauth/callback-payload/', {
        params: handoffKey ? { handoff: handoffKey } : undefined
      })
      if (response.data?.status === 'success' && response.data?.data) {
        return { success: true, data: response.data.data }
      }
      return {
        success: false,
        error: response.data?.message || 'OAuth callback payload not available'
      }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.message || 'Failed to fetch OAuth callback payload'
      }
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
      // Cookie-first: backend sets HttpOnly cookies. Do not store tokens in browser storage.
      removeSensitive('session_token')
      removeSensitive('access_token')
      removeSensitive('refresh_token')
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
          if (userResponse.data && userResponse.data.status === 'success') {
            const userData = userResponse.data.data
            const originalData = userData.original || {}
            
            setSensitive('current_user', JSON.stringify(userResponse.data))
            
            // Build full name from firstName and lastName
            const firstName = originalData.firstName || userData.firstName || ''
            const lastName = originalData.lastName || userData.lastName || ''
            const username = originalData.username || userData.username || ''
            const email = originalData.email || userData.email || ''
            
            // Set full name for sidebar and navbar (consistent with regular login)
            if (firstName && lastName) {
              const fullName = `${firstName} ${lastName}`.trim()
              localStorage.setItem('user_name', fullName)
              localStorage.setItem('fullName', fullName)
              localStorage.setItem('username', fullName)
            } else if (username) {
              localStorage.setItem('user_name', username)
              localStorage.setItem('username', username)
            }
            
            // Set email
            if (email) {
              localStorage.setItem('user_email', email)
            }
            
            console.log('✅ User profile data stored for Google OAuth login:', {
              fullName: firstName && lastName ? `${firstName} ${lastName}` : username,
              email: email
            })
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
    removeSensitive('session_token')
    removeSensitive('access_token')
    removeSensitive('refresh_token')
    removeSensitive('current_user')
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
      // Cookie-first: refresh token is read from HttpOnly cookie by backend.
      const response = await authApi.post('/jwt/refresh/', {})
      // Ensure we don't keep any legacy token values around.
      removeSensitive('session_token')
      removeSensitive('access_token')
      removeSensitive('refresh_token')
 
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
   * Verify MFA OTP and complete login
   * @param {string} username - Username or user ID
   * @param {string} password - User password
   * @param {string} otp - 6-digit OTP code
   * @param {string} loginType - 'username' or 'userid'
   */
  async verifyMfaOtp(username, password, otp, loginType = 'username') {
    try {
      const response = await authApi.post('/jwt/mfa/verify-otp/', {
        username,
        password,
        otp,
        login_type: loginType
      })
 
      if (response.data.status === 'success') {
        const token = response.data.access_token
        const refreshToken = response.data.refresh_token
 
        // Cookie-first: backend sets HttpOnly cookies. But also store in sessionStorage for TPRM iframe.
        if (token) {
          sessionStorage.setItem('access_token', token)
          localStorage.removeItem('access_token')
        } else {
          sessionStorage.removeItem('access_token')
        }
        if (refreshToken) {
          sessionStorage.setItem('refresh_token', refreshToken)
          localStorage.removeItem('refresh_token')
        } else {
          sessionStorage.removeItem('refresh_token')
        }
        sessionStorage.removeItem('session_token')
        localStorage.removeItem('session_token')
        if (response.data.user) {
          setSensitive('current_user', JSON.stringify(response.data.user))
          const uid =
            response.data.user.UserId ??
            response.data.user.user_id ??
            response.data.user.userid ??
            response.data.user.id
          if (uid != null && uid !== '') {
            localStorage.setItem('user_id', String(uid))
          }
          // Set user name and email for navbar and other components
          if (response.data.user.UserName) {
            localStorage.setItem('user_name', response.data.user.UserName)
          }
          if (response.data.user.Email) {
            localStorage.setItem('user_email', response.data.user.Email)
          }
        }
        if (response.data.access_token_expires) {
          localStorage.setItem('access_token_expires', response.data.access_token_expires)
        }
        if (response.data.refresh_token_expires) {
          localStorage.setItem('refresh_token_expires', response.data.refresh_token_expires)
        }

        // If we don't have a user_id, try to derive from response.user only (no token decoding).
       
        // CRITICAL: Set is_logged_in flag - this is required for App.vue to show sidebar/navbar
        localStorage.setItem('is_logged_in', 'true')
        localStorage.setItem('isAuthenticated', 'true')
 
        return {
          success: true,
          user: response.data.user,
          token,
          accessToken: token,
          refreshToken: refreshToken,
          consent_required: response.data.consent_required || false
        }
      } else {
        return {
          success: false,
          error: response.data.message || 'MFA verification failed'
        }
      }
    } catch (error) {
      console.error('MFA OTP verification error:', error)
      return {
        success: false,
        error: error.response?.data?.message || 'MFA verification failed. Please try again.',
        details: error.response?.data
      }
    }
  },
 
  /**
   * Resend MFA OTP to user's email
   * @param {string} username - Username or user ID
   * @param {string} password - User password
   * @param {string} loginType - 'username' or 'userid'
   */
  async resendMfaOtp(username, password, loginType = 'username') {
    try {
      const response = await authApi.post('/jwt/mfa/resend-otp/', {
        username,
        password,
        login_type: loginType
      })
 
      if (response.data.status === 'success') {
        return {
          success: true,
          message: response.data.message || 'New verification code sent',
          emailMasked: response.data.email_masked
        }
      } else {
        return {
          success: false,
          message: response.data.message || 'Failed to resend verification code'
        }
      }
    } catch (error) {
      console.error('Resend MFA OTP error:', error)
      return {
        success: false,
        message: error.response?.data?.message || 'Failed to resend verification code. Please try again.',
        details: error.response?.data
      }
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
 
 
 