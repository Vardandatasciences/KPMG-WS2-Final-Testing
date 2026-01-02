import { defineStore } from 'pinia'
import apiClient from '@/config/axios'

/**
 * Auth store that reuses GRC session - NO hardcoded users
 * Reads user and token from localStorage (set by GRC login)
 * Also listens for auth sync from GRC parent window (when running in iframe)
 */

const TOKEN_KEYS = ['session_token', 'token', 'access_token', 'jwt_token']
const USER_KEYS = ['current_user', 'user']

function getStoredToken() {
  for (const key of TOKEN_KEYS) {
    const val = localStorage.getItem(key)
    if (val) return val
  }
  return null
}

function getStoredUser() {
  for (const key of USER_KEYS) {
    const val = localStorage.getItem(key)
    if (val) {
      try {
        return JSON.parse(val)
      } catch (e) {
        console.error('Error parsing stored user:', e)
      }
    }
  }
  return null
}

// Check if running inside an iframe
function isInIframe() {
  try {
    return window.self !== window.top
  } catch (e) {
    return true
  }
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    isAuthenticated: false,
    loading: false,
    token: null,
    refreshToken: null,
    _messageHandler: null
  }),

  getters: {
    isLoggedIn: (state) => state.isAuthenticated && state.user !== null,
    userInfo: (state) => state.user,
    isLoading: (state) => state.loading
  },

  actions: {
    // Initialize auth state from localStorage (GRC session)
    initializeAuth() {
      console.log('[TPRM AuthStore] Initializing auth from GRC session...')
      
      const user = getStoredUser()
      const token = getStoredToken()
      const isAuthFlag = localStorage.getItem('isAuthenticated') === 'true' || 
                         localStorage.getItem('is_logged_in') === 'true'
      
      console.log('[TPRM AuthStore] Found:', { 
        hasUser: !!user, 
        hasToken: !!token, 
        isAuthFlag,
        userId: user?.userid || user?.UserId || user?.id || user?.user_id
      })
      
      if (user && (token || isAuthFlag)) {
        this.user = user
        this.isAuthenticated = true
        this.token = token
        this.refreshToken = localStorage.getItem('refresh_token') || localStorage.getItem('refreshToken')
        console.log('[TPRM AuthStore] Authenticated as:', user.username || user.UserName || user.email)
      } else {
        console.warn('[TPRM AuthStore] No valid GRC session found - checking if in iframe...')
        
        // If running in iframe, request auth from parent
        if (isInIframe()) {
          console.log('[TPRM AuthStore] Running in iframe, requesting auth from GRC parent...')
          this.requestAuthFromParent()
        } else {
          this.user = null
          this.isAuthenticated = false
          this.token = null
          this.refreshToken = null
        }
      }
      
      // Set up message listener for auth sync from parent
      this.setupMessageListener()
    },

    // Request auth data from GRC parent window
    requestAuthFromParent() {
      if (window.parent && window.parent !== window) {
        console.log('[TPRM AuthStore] Sending auth request to parent window')
        window.parent.postMessage({ type: 'TPRM_AUTH_REQUEST' }, '*')
      }
    },

    // Set up listener for auth messages from GRC parent
    setupMessageListener() {
      if (this._messageHandler) {
        return // Already set up
      }

      this._messageHandler = (event) => {
        // Handle auth sync from GRC parent
        if (event.data && event.data.type === 'GRC_AUTH_SYNC') {
          console.log('[TPRM AuthStore] Received auth sync from GRC:', {
            hasToken: !!event.data.token,
            hasUser: !!event.data.user,
            isAuthenticated: event.data.isAuthenticated
          })
          
          // Store auth data in localStorage for future use
          if (event.data.token) {
            localStorage.setItem('access_token', event.data.token)
            localStorage.setItem('session_token', event.data.token)
            localStorage.setItem('token', event.data.token)
            this.token = event.data.token
          }
          
          if (event.data.refreshToken) {
            localStorage.setItem('refresh_token', event.data.refreshToken)
            this.refreshToken = event.data.refreshToken
          }
          
          if (event.data.user) {
            localStorage.setItem('user', JSON.stringify(event.data.user))
            localStorage.setItem('current_user', JSON.stringify(event.data.user))
            this.user = event.data.user
          }
          
          if (event.data.isAuthenticated) {
            localStorage.setItem('isAuthenticated', 'true')
            localStorage.setItem('is_logged_in', 'true')
            this.isAuthenticated = true
          }
          
          console.log('[TPRM AuthStore] Auth synced successfully:', {
            user: this.user?.username || this.user?.UserName || this.user?.email,
            hasToken: !!this.token
          })
        }
      }

      window.addEventListener('message', this._messageHandler)
      console.log('[TPRM AuthStore] Message listener set up for GRC auth sync')
    },

    // Clean up message listener
    cleanupMessageListener() {
      if (this._messageHandler) {
        window.removeEventListener('message', this._messageHandler)
        this._messageHandler = null
      }
    },

    // Set user data
    setUser(userData, tokens = {}) {
      this.user = userData
      this.isAuthenticated = true
      this.token = tokens.access || null
      this.refreshToken = tokens.refresh || null
      
      localStorage.setItem('current_user', JSON.stringify(userData))
      localStorage.setItem('user', JSON.stringify(userData))
      localStorage.setItem('isAuthenticated', 'true')
      if (tokens.access) {
        localStorage.setItem('token', tokens.access)
        localStorage.setItem('session_token', tokens.access)
        localStorage.setItem('access_token', tokens.access)
      }
      if (tokens.refresh) localStorage.setItem('refresh_token', tokens.refresh)
    },

    // Clear user data
    clearUser() {
      this.user = null
      this.isAuthenticated = false
      this.token = null
      this.refreshToken = null
      
      // Don't clear GRC session keys - only clear TPRM-specific if any
      console.log('[TPRM AuthStore] Cleared local auth state (GRC session preserved)')
    },

    // Check authentication status - just re-read from localStorage
    async checkAuth() {
      this.loading = true
      try {
        this.initializeAuth()
        return this.isAuthenticated
      } finally {
        this.loading = false
      }
    },

    // Login - for TPRM this just re-reads GRC session
    async login(credentials) {
      this.loading = true
      try {
        // Re-initialize from GRC session
        this.initializeAuth()
        
        if (this.isAuthenticated) {
          return { success: true, message: 'Using GRC session' }
        }
        
        return { success: false, message: 'No GRC session found - please login to GRC first' }
      } finally {
        this.loading = false
      }
    },

    // Logout - just clear local state, don't touch GRC session
    async logout() {
      this.loading = true
      try {
        this.clearUser()
      } finally {
        this.loading = false
      }
    },

    // Refresh token
    async refreshAccessToken() {
      const refreshToken = localStorage.getItem('refresh_token') || localStorage.getItem('refreshToken')
      if (!refreshToken) {
        throw new Error('No refresh token available')
      }

      try {
        const response = await apiClient.post('/api/auth/token/refresh/', {
          refresh: refreshToken
        })

        if (response.data && response.data.access) {
          this.token = response.data.access
          localStorage.setItem('token', response.data.access)
          localStorage.setItem('session_token', response.data.access)
          localStorage.setItem('access_token', response.data.access)
          return response.data.access
        }

        throw new Error('Failed to refresh token')
      } catch (error) {
        console.error('Token refresh failed:', error)
        throw error
      }
    }
  }
})
