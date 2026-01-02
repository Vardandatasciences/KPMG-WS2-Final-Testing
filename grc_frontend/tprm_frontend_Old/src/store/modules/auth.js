import authService from '@/services/authService'
import permissionsService from '@/services/permissionsService'
 
const authModule = {
  namespaced: true,
 
  state: {
    currentUser: null,
    isAuthenticated: false,
    sessionToken: null,
    loading: false,
    error: null
  },
 
  getters: {
    currentUser: state => state.currentUser,
    isAuthenticated: state => state.isAuthenticated,
    sessionToken: state => state.sessionToken,
    isLoading: state => state.loading,
    hasError: state => !!state.error,
    error: state => state.error
  },
 
  mutations: {
    SET_AUTH(state, { user, token, accessToken, refreshToken }) {
      state.currentUser = user
      state.sessionToken = token
      state.isAuthenticated = true
      if (token) {
        localStorage.setItem('session_token', token)
        localStorage.setItem('current_user', JSON.stringify(user))
      }
      if (typeof accessToken !== 'undefined') {
        if (accessToken) {
          localStorage.setItem('access_token', accessToken)
        } else {
          localStorage.removeItem('access_token')
        }
      }
      if (typeof refreshToken !== 'undefined') {
        if (refreshToken) {
          localStorage.setItem('refresh_token', refreshToken)
        } else {
          localStorage.removeItem('refresh_token')
        }
      }
      // Clear permission cache on login to force fresh permission checks
      console.log('[Auth] Clearing permission cache on login')
      permissionsService.clearCache()
    },
   
    CLEAR_AUTH(state) {
      state.currentUser = null
      state.sessionToken = null
      state.isAuthenticated = false
      localStorage.removeItem('session_token')
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('current_user')
      // Clear permission cache on logout
      console.log('[Auth] Clearing permission cache on logout')
      permissionsService.clearCache()
    },
   
    SET_LOADING(state, loading) {
      state.loading = loading
    },
   
    SET_ERROR(state, error) {
      state.error = error
    },
   
    CLEAR_ERROR(state) {
      state.error = null
    },
   
    SET_USER(state, user) {
      state.currentUser = user
      if (user) {
        localStorage.setItem('current_user', JSON.stringify(user))
      }
    }
  },
 
  actions: {
    async login({ commit }, { username, password }) {
      try {
        commit('SET_LOADING', true)
        commit('CLEAR_ERROR')
       
        console.log('Auth module: Attempting login for user:', username)
       
        const result = await authService.login(username, password)
       
        if (result.success) {
          commit('SET_AUTH', {
            user: result.user,
            token: result.token,
            accessToken: result.accessToken,
            refreshToken: result.refreshToken
          })
          return {
            success: true,
            user: result.user,
            message: result.message
          }
        } else {
          commit('SET_ERROR', result.error)
          return {
            success: false,
            error: result.error
          }
        }
      } catch (error) {
        console.error('Auth module: Login error:', error)
        const errorMessage = error.message || 'An unexpected error occurred during login'
        commit('SET_ERROR', errorMessage)
        return {
          success: false,
          error: errorMessage
        }
      } finally {
        commit('SET_LOADING', false)
      }
    },
   
   
    /**
     * Validate current session
     */
    async validateSession({ commit }) {
      try {
        commit('SET_LOADING', true)
        commit('CLEAR_ERROR')
       
        // Check if we have a token
        if (!authService.isAuthenticated()) {
          commit('CLEAR_AUTH')
          return { success: false, error: 'No authentication found' }
        }
       
        console.log('Auth module: Validating session')
       
        const result = await authService.validateSession()
       
        if (result.success) {
          const token = authService.getSessionToken()
          commit('SET_AUTH', {
            user: result.user,
            token: token
          })
          console.log('Auth module: Session validation successful')
          return {
            success: true,
            user: result.user
          }
        } else {
          commit('CLEAR_AUTH')
          return {
            success: false,
            error: result.error
          }
        }
      } catch (error) {
        console.error('Auth module: Session validation error:', error)
        commit('CLEAR_AUTH')
        return {
          success: false,
          error: error.message || 'Session validation failed'
        }
      } finally {
        commit('SET_LOADING', false)
      }
    },
   
    /**
     * Logout user
     */
    async logoutUser({ commit }) {
      try {
        commit('SET_LOADING', true)
       
        console.log('Auth module: Logging out user')
       
        const result = await authService.logout()
       
        console.log('Auth module: Logout service result:', result)
       
        // Always clear auth state from Vuex
        commit('CLEAR_AUTH')
       
        if (result.success) {
          console.log('Auth module: ✅ Logout successful - session token cleared from database')
          return { success: true, message: result.message }
        } else {
          console.log('Auth module: ⚠️ Logout API failed but local state cleared')
          return { success: false, error: result.error }
        }
      } catch (error) {
        console.error('Auth module: ❌ Logout error:', error)
        // Still clear auth even if API call fails
        commit('CLEAR_AUTH')
        return { success: false, error: error.message }
      } finally {
        commit('SET_LOADING', false)
      }
    },
   
    /**
     * Initialize auth state from localStorage and set up iframe auth sync
     */
    initializeAuth({ commit }) {
      try {
        const user = authService.getCurrentUser()
        const token = authService.getSessionToken()
        
        if (user && token) {
          commit('SET_AUTH', { user, token })
          console.log('[Auth Module] Initialized with stored user:', user.username || user.UserName || user.email)
        } else {
          // Check if running in iframe - if so, request auth from parent
          const isInIframe = window.self !== window.top
          if (isInIframe) {
            console.log('[Auth Module] Running in iframe, requesting auth from parent...')
            if (window.parent && window.parent !== window) {
              window.parent.postMessage({ type: 'TPRM_AUTH_REQUEST' }, '*')
            }
          }
          
          commit('CLEAR_AUTH')
          console.log('[Auth Module] No stored authentication found')
        }
        
        // Set up message listener for auth sync from parent (only once)
        if (!window._authSyncListenerSet) {
          window._authSyncListenerSet = true
          window.addEventListener('message', (event) => {
            if (event.data && event.data.type === 'GRC_AUTH_SYNC') {
              console.log('[Auth Module] Received auth sync from GRC parent:', {
                hasToken: !!event.data.token,
                hasUser: !!event.data.user,
                isAuthenticated: event.data.isAuthenticated
              })
              
              if (event.data.token && event.data.user) {
                commit('SET_AUTH', {
                  user: event.data.user,
                  token: event.data.token,
                  accessToken: event.data.token,
                  refreshToken: event.data.refreshToken
                })
                console.log('[Auth Module] Auth synced successfully from GRC parent')
              }
            }
          })
          console.log('[Auth Module] Message listener set up for GRC auth sync')
        }
      } catch (error) {
        console.error('[Auth Module] Initialize error:', error)
        commit('CLEAR_AUTH')
      }
    },
   
    /**
     * Clear error message
     */
    clearError({ commit }) {
      commit('CLEAR_ERROR')
    }
  }
}
 
export default authModule