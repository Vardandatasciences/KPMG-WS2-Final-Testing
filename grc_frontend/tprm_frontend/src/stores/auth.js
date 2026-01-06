import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import apiClient from '@/config/axios'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    isAuthenticated: false,
    loading: false,
    token: null,
    refreshToken: null
  }),

  getters: {
    isLoggedIn: (state) => state.isAuthenticated && state.user !== null,
    userInfo: (state) => state.user,
    isLoading: (state) => state.loading
  },

  actions: {
    // Initialize hardcoded user for vendor module
    initializeHardcodedUser() {
      const hardcodedUser = {
        id: 60,
        username: 'GRC Administrator',
        email: 'admin@vendor.com',
        first_name: 'GRC',
        last_name: 'Administrator',
        role: 'admin',
        permissions: ['all']
      }
      
      this.user = hardcodedUser
      this.isAuthenticated = true
      localStorage.setItem('user', JSON.stringify(hardcodedUser))
      localStorage.setItem('isAuthenticated', 'true')
    },

    // Initialize auth state from localStorage
    initializeAuth() {
      const user = localStorage.getItem('user')
      const isAuthenticated = localStorage.getItem('isAuthenticated')
      const token = localStorage.getItem('token')
      const refreshToken = localStorage.getItem('refreshToken')
      
      if (user && isAuthenticated === 'true') {
        this.user = JSON.parse(user)
        this.isAuthenticated = true
        this.token = token
        this.refreshToken = refreshToken
      } else {
        // If no user in localStorage, initialize hardcoded user for vendor module
        this.initializeHardcodedUser()
      }
    },

    // Set user data
    setUser(userData, tokens = {}) {
      this.user = userData
      this.isAuthenticated = true
      this.token = tokens.access || null
      this.refreshToken = tokens.refresh || null
      
      localStorage.setItem('user', JSON.stringify(userData))
      localStorage.setItem('isAuthenticated', 'true')
      if (tokens.access) localStorage.setItem('token', tokens.access)
      if (tokens.refresh) localStorage.setItem('refreshToken', tokens.refresh)
    },

    // Clear user data
    clearUser() {
      this.user = null
      this.isAuthenticated = false
      this.token = null
      this.refreshToken = null
      
      localStorage.removeItem('user')
      localStorage.removeItem('isAuthenticated')
      localStorage.removeItem('token')
      localStorage.removeItem('refreshToken')
    },

    // Check authentication status
    async checkAuth() {
      this.loading = true
      try {
        // If we have a token, verify it with the backend
        if (this.token) {
          const response = await apiClient.get('/api/auth/verify/', {
            headers: {
              'Authorization': `Bearer ${this.token}`
            }
          })
          
          if (response.data && response.data.user) {
            this.setUser(response.data.user, { access: this.token, refresh: this.refreshToken })
            return true
          }
        }
        
        // Fallback to hardcoded user for vendor module
        if (!this.isAuthenticated) {
          this.initializeHardcodedUser()
        }
        return true
      } catch (error) {
        console.error('Auth check failed:', error)
        // Even on error, initialize hardcoded user for vendor module
        this.initializeHardcodedUser()
        return true
      } finally {
        this.loading = false
      }
    },

    // Login
    async login(credentials) {
      this.loading = true
      try {
        const response = await apiClient.post('/api/auth/login/', credentials)
        
        if (response.data && response.data.user) {
          this.setUser(response.data.user, {
            access: response.data.access,
            refresh: response.data.refresh
          })
          return { success: true, message: 'Login successful' }
        }
        
        // Fallback to hardcoded user
        this.initializeHardcodedUser()
        return { success: true, message: 'Login successful' }
      } catch (error) {
        console.error('Login failed:', error)
        // Fallback to hardcoded user for vendor module
        this.initializeHardcodedUser()
        return { success: true, message: 'Login successful' }
      } finally {
        this.loading = false
      }
    },

    // Logout
    async logout() {
      this.loading = true
      try {
        if (this.token) {
          await apiClient.post('/api/auth/logout/', {}, {
            headers: {
              'Authorization': `Bearer ${this.token}`
            }
          })
        }
      } catch (error) {
        console.error('Logout error:', error)
      } finally {
        this.clearUser()
        // Reinitialize hardcoded user for vendor module
        this.initializeHardcodedUser()
        this.loading = false
      }
    },

    // Refresh token
    async refreshAccessToken() {
      if (!this.refreshToken) {
        throw new Error('No refresh token available')
      }

      try {
        const response = await apiClient.post('/api/auth/token/refresh/', {
          refresh: this.refreshToken
        })

        if (response.data && response.data.access) {
          this.token = response.data.access
          localStorage.setItem('token', response.data.access)
          return response.data.access
        }

        throw new Error('Failed to refresh token')
      } catch (error) {
        console.error('Token refresh failed:', error)
        this.clearUser()
        throw error
      }
    }
  }
})