import { defineStore } from 'pinia'
import apiClient from '@/config/axios'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    isAuthenticated: false,
    loading: false,
    token: null,
    refreshToken: null,
    authBootstrapped: false
  }),

  getters: {
    isLoggedIn: (state) => state.isAuthenticated && state.user !== null,
    userInfo: (state) => state.user,
    isLoading: (state) => state.loading
  },

  actions: {
    initializeAuth() {
      this.user = null
      this.isAuthenticated = false
      this.token = null
      this.refreshToken = null
      this.authBootstrapped = false
    },

    async bootstrapAuth() {
      if (this.authBootstrapped) return
      this.authBootstrapped = true
      await this.checkAuth()
    },

    setUser(userData, tokens = {}) {
      this.user = userData
      this.isAuthenticated = true
      this.token = tokens.accessToken ?? null
      this.refreshToken = tokens.refreshToken ?? null
    },

    clearUser() {
      this.user = null
      this.isAuthenticated = false
      this.token = null
      this.refreshToken = null
    },

    async checkAuth() {
      this.loading = true
      try {
        const response = await apiClient.get('/api/jwt/verify/')
        if (response.data && response.data.user) {
          this.setUser(response.data.user)
          return true
        }
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

    async login(credentials) {
      this.loading = true
      try {
        const response = await apiClient.post('/api/jwt/login/', {
          username: credentials.username,
          password: credentials.password,
          login_type: credentials.login_type || 'username'
        })

        if (response.data?.user) {
          this.setUser(response.data.user)
          return { success: true, message: response.data.message || 'Login successful' }
        }
        return { success: false, message: response.data?.message || 'Login failed' }
      } catch (error) {
        console.error('Login failed:', error)
        return {
          success: false,
          message: error.response?.data?.message || 'Login failed'
        }
      } finally {
        this.loading = false
      }
    },

    async logout() {
      this.loading = true
      try {
        await apiClient.post('/api/jwt/logout/', {})
      } catch (error) {
        console.error('Logout error:', error)
      } finally {
        this.clearUser()
        this.loading = false
      }
    },

    async refreshAccessToken() {
      throw new Error('Token refresh is not supported in cookie-first mode')
    }
  }
})
