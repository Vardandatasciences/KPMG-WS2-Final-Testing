import axios from 'axios'
import { getTprmApiBaseUrl, getApiOrigin } from '@/utils/backendEnv'
import { getParentPostMessageTargetOrigin } from '@/utils/parentPostMessageOrigin.js'

const API_BASE_URL = getTprmApiBaseUrl()

// Create axios instance with default config
const authApi = axios.create({
  baseURL: `${API_BASE_URL}/auth`,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true
})

const setSensitive = (key, value) => {
  sessionStorage.setItem(key, value)
  localStorage.removeItem(key)
}

// Cookie-first auth: tokens are stored in HttpOnly cookies, not storage.
// Keep current_user in sessionStorage for UI purposes only.
const getSensitive = (key) => sessionStorage.getItem(key) || localStorage.getItem(key)

const clearSensitive = () => {
  ;['session_token', 'access_token', 'refresh_token', 'current_user'].forEach((k) => {
    sessionStorage.removeItem(k)
    localStorage.removeItem(k)
  })
  sessionStorage.removeItem('tprm_cookie_session_validated')
}

// Coalesce concurrent jwt/verify calls (router + guards + App.vue often run together).
let validateSessionInFlight = null

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
      // Token expired or invalid
      console.warn('[TPRM Auth] 401 Unauthorized - redirecting via parent shell')
      clearSensitive()
      
      // Notify parent GRC context to handle the login redirect
      const isInIframe = window.self !== window.top
      if (isInIframe && window.parent) {
        window.parent.postMessage({ type: 'TPRM_REDIRECT_TO_LOGIN' }, getParentPostMessageTargetOrigin())
      } else if (window.location.pathname !== '/login') {
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
        // Maintain tokens in storage for backward compatibility ("not disturb the flow").
        // The HttpOnly cookies sent by the backend are now the primary security mechanism.
        const token = response.data.session_token || response.data.access_token
        localStorage.setItem('session_token', token)
        localStorage.setItem('access_token', response.data.access_token)
        if (response.data.refresh_token) {
          localStorage.setItem('refresh_token', response.data.refresh_token)
        }
        localStorage.setItem('current_user', JSON.stringify(response.data.user))
        
        // Also store in sessionStorage which is prioritized by http.js
        sessionStorage.setItem('session_token', token)
        sessionStorage.setItem('access_token', response.data.access_token)
        sessionStorage.setItem('current_user', JSON.stringify(response.data.user))
        
        // Mark as validated via backend cookie
        sessionStorage.setItem('tprm_cookie_session_validated', 'true')
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
   * Validate current session (deduped; cookie-first against shared GRC JWT).
   * On 401, attempts one cookie-based refresh so short-lived access cookies recover without a full reload.
   */
  async validateSession() {
    if (validateSessionInFlight) {
      return validateSessionInFlight
    }
    const origin = getApiOrigin()
    const verify = () =>
      axios.get(`${origin}/api/jwt/verify/`, {
        withCredentials: true,
      })

    validateSessionInFlight = (async () => {
      try {
        const response = await verify()
        return {
          success: true,
          user: response.data.user,
        }
      } catch (error) {
        const status = error.response?.status
        if (status === 401) {
          try {
            await axios.post(`${origin}/api/jwt/refresh/`, {}, { withCredentials: true })
            const response = await verify()
            return {
              success: true,
              user: response.data.user,
            }
          } catch {
            // Refresh could not establish a session (e.g. logged in elsewhere).
          }
          console.debug(
            '[TPRM Auth] jwt/verify returned 401 after refresh attempt — session missing, expired, or rotated'
          )
        } else {
          console.error('Session validation error:', error)
        }
        return {
          success: false,
          error: error.response?.data?.message || 'Session validation failed',
        }
      } finally {
        validateSessionInFlight = null
      }
    })()

    return validateSessionInFlight
  },

  /**
   * Awaitable auth check for router/guards (avoids treating a Promise as a boolean).
   */
  async resolveAuthenticationStatus() {
    if (sessionStorage.getItem('tprm_cookie_session_validated') === 'true') {
      return true
    }
    const res = await this.validateSession()
    if (res && res.success) {
      sessionStorage.setItem('tprm_cookie_session_validated', 'true')
      return true
    }
    clearSensitive()
    return false
  },

  /**
   * Refresh access token
   */
  async refreshToken() {
    try {
      // Refresh shared cookie session through GRC JWT endpoint.
      const response = await axios.post(`${getApiOrigin()}/api/jwt/refresh/`, {}, {
        withCredentials: true,
      })

      if (response.data.success) {
        clearSensitive()
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
      clearSensitive()
      console.log('AuthService: Local storage cleared')
      
      return {
        success: true,
        message: response.data?.message || 'Logged out successfully'
      }
    } catch (error) {
      console.error('AuthService: Logout API error:', error)
      console.error('AuthService: Error details:', error.response?.data)
      
      // Still clear local storage even if API call fails
      clearSensitive()
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
      const userStr = getSensitive('current_user')
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
    return getSensitive('session_token')
  },

  /**
   * Check if user is authenticated
   */
  isAuthenticated() {
    // Cookie-first: validate via backend once per tab.
    if (sessionStorage.getItem('tprm_cookie_session_validated') === 'true') {
      return true
    }

    // Return a promise — prefer resolveAuthenticationStatus() in async guards
    return this.validateSession()
      .then((res) => {
        if (res && res.success) {
          sessionStorage.setItem('tprm_cookie_session_validated', 'true')
          return true
        }
        clearSensitive()
        return false
      })
      .catch(() => {
        clearSensitive()
        return false
      })
  }
}

