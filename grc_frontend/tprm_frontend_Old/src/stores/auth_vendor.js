import { defineStore } from 'pinia'

/**
 * Vendor Auth Store - reads from GRC session
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

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    isAuthenticated: false,
    loading: false
  }),

  getters: {
    isLoggedIn: (state) => state.isAuthenticated && state.user !== null,
    userInfo: (state) => state.user
  },

  actions: {
    // Set user data
    setUser(userData) {
      this.user = userData
      this.isAuthenticated = true
      localStorage.setItem('current_user', JSON.stringify(userData))
      localStorage.setItem('user', JSON.stringify(userData))
      localStorage.setItem('isAuthenticated', 'true')
    },

    // Clear user data (local only, don't clear GRC session)
    clearUser() {
      this.user = null
      this.isAuthenticated = false
      console.log('[VendorAuthStore] Local state cleared')
    },

    // Initialize auth state from localStorage (GRC session)
    async initializeAuth() {
      console.log('[VendorAuthStore] Initializing from GRC session...')
      
      const user = getStoredUser()
      const token = getStoredToken()
      const isAuthFlag = localStorage.getItem('isAuthenticated') === 'true' || 
                         localStorage.getItem('is_logged_in') === 'true'
      
      console.log('[VendorAuthStore] Found:', { 
        hasUser: !!user, 
        hasToken: !!token, 
        isAuthFlag,
        userId: user?.userid || user?.UserId || user?.id || user?.user_id
      })
      
      if (user && (token || isAuthFlag)) {
        this.user = user
        this.isAuthenticated = true
        console.log('[VendorAuthStore] Authenticated as:', user.username || user.UserName || user.email)
      } else {
        console.warn('[VendorAuthStore] No valid GRC session found')
        this.user = null
        this.isAuthenticated = false
      }
    },

    // Check authentication status - just re-read from localStorage
    async checkAuth() {
      this.loading = true
      try {
        await this.initializeAuth()
        return this.isAuthenticated
      } finally {
        this.loading = false
      }
    },

    // Login - for vendor module this just re-reads GRC session
    async login(credentials) {
      this.loading = true
      try {
        await this.initializeAuth()
        
        if (this.isAuthenticated) {
          return { success: true, message: 'Using GRC session' }
        }
        
        return { success: false, message: 'No GRC session found - please login to GRC first' }
      } finally {
        this.loading = false
      }
    },

    // Logout - just clear local state
    async logout() {
      this.loading = true
      try {
        this.clearUser()
      } finally {
        this.loading = false
      }
    }
  }
})
