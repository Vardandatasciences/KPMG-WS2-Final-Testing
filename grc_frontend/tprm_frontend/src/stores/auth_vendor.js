import { defineStore } from 'pinia'
import { getTprmApiV1Url } from '@/utils/backendEnv'

const API_BASE_URL = getTprmApiV1Url('vendor-auth')

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    isAuthenticated: false,
    loading: false,
    initialized: false
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
      sessionStorage.setItem('current_user', JSON.stringify(userData))
      localStorage.removeItem('current_user')
    },

    clearUser() {
      this.user = null
      this.isAuthenticated = false
      this.initialized = false
      sessionStorage.removeItem('current_user')
      localStorage.removeItem('current_user')
      localStorage.removeItem('session_token')
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    },

    // Initialize auth state from localStorage or check with backend
    async initializeAuth() {
      // Prevent multiple initializations
      if (this.initialized) {
        console.log('[AuthStore] Already initialized, skipping')
        return
      }
      
      this.loading = true
      try {
        console.log('[AuthStore] Verifying session with backend')
        await this.checkAuth()
      } finally {
        this.initialized = true
        this.loading = false
      }
    },

    // Check authentication status with backend
    async checkAuth() {
      this.loading = true
      try {
        const response = await fetch(`${API_BASE_URL}/check-auth/`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include', // Include cookies for session
        })

        if (response.ok) {
          const data = await response.json()
          if (data.authenticated && data.user) {
            this.setUser(data.user)
            return true
          }
        }
        
        // If not authenticated, clear user data
        this.clearUser()
        return false
      } catch (error) {
        console.error('Auth check failed:', error)
        this.clearUser()
        return false
      } finally {
        this.loading = false
      }
    },

    // Login with credentials
    async login(credentials) {
      this.loading = true
      try {
        const response = await fetch(`${API_BASE_URL}/login/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include', // Include cookies for session
          body: JSON.stringify(credentials),
        })

        const data = await response.json()

        if (response.ok && data.success && data.user) {
          this.setUser(data.user)
          return { success: true, message: data.message || 'Login successful' }
        } else {
          return { success: false, message: data.message || 'Login failed' }
        }
      } catch (error) {
        console.error('Login failed:', error)
        return { success: false, message: 'An error occurred during login' }
      } finally {
        this.loading = false
      }
    },

    // Logout
    async logout() {
      this.loading = true
      try {
        await fetch(`${API_BASE_URL}/logout/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include', // Include cookies for session
        })
      } catch (error) {
        console.error('Logout error:', error)
      } finally {
        // Always clear user data locally
        this.clearUser()
        this.loading = false
      }
    }
  }
})
 
 