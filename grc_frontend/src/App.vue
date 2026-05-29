<template>
  <div id="app">
    <div v-if="showSessionReconnectBanner" class="session-reconnect-banner">
      Reconnecting session...
    </div>
    <div v-if="isAuthenticated" class="app-container">
      <!-- Show Sidebar on all pages including home -->
      <Sidebar />
      <!-- Global Navbar for all authenticated pages -->
      <GlobalNavbar />
      <div class="main-content with-sidebar">
        <!-- keep-alive preserves component state between navigations so cached data
             is shown instantly on re-visit without re-fetching from the API.
             Form/create/edit pages are excluded so they always start fresh. -->
        <router-view v-slot="{ Component }">
          <keep-alive :exclude="[
            'CreatePolicy',
            'CreateCompliance',
            'EditCompliance',
            'CreateRisk',
            'CreateRiskInstance',
            'UploadFramework',
            'CreateFramework',
            'AssignAudit',
            'IncidentManagement',
            'EventCreation',
            'EventEditModal',
          ]">
            <component :is="Component" :key="routeComponentKey" />
          </keep-alive>
        </router-view>
      </div>
    </div>
    <div v-else class="login-container">
      <router-view></router-view>
    </div>
    <PopupModal />
    <!-- Global Consent Modal -->
    <ConsentModal ref="consentModal" />
    <!-- Cookie Banner -->
    <CookieBanner />
    <!-- Session Timeout Popup -->
    <SessionTimeoutPopup />
    <!-- Debug component - remove in production -->
    <!-- <AuthDebug /> -->
  </div>
</template>
 
<script>
import Sidebar from './components/Policy/Sidebar.vue'
import GlobalNavbar from './components/GlobalNavbar.vue'
import PopupModal from './modules/popup/PopupModal.vue'
import ConsentModal from './components/Consent/ConsentModal.vue'
import CookieBanner from './components/Cookie/CookieBanner.vue'
import SessionTimeoutPopup from './components/SessionTimeoutPopup.vue'
import consentService from './services/consentService.js'
import { useFrameworkStore } from './stores/framework'
// import AuthDebug from './components/AuthDebug.vue'
 
export default {
  name: 'App',
  components: {
    Sidebar,
    GlobalNavbar,
    PopupModal,
    ConsentModal,
    CookieBanner,
    SessionTimeoutPopup
    // AuthDebug
  },
  data() {
    return {
      isAuthenticated: false,
      hasExplicitlyLoggedIn: false,
      showSessionReconnectBanner: false
    }
  },
  created() {
    // Clear any stale authentication data on app load
    this.clearStaleAuthData()
   
    // Check authentication status on app load
    this.checkAuthStatus()
    
    // Load framework selection from backend session into Pinia store
    this.$nextTick(() => {
      if (this.isAuthenticated) {
        this.loadFrameworkFromSession()
      }
    })
   
    // Listen for auth changes
    window.addEventListener('authChanged', this.checkAuthStatus)
   
    // Make login/logout methods available globally
    window.onSuccessfulLogin = this.onSuccessfulLogin
    window.onLogout = this.onLogout
    window.forceAuthCheck = this.forceAuthCheck
    window.appComponent = this
   
    // Additional check after a short delay to ensure sidebar is rendered
    this.$nextTick(() => {
      setTimeout(() => {
        this.checkAuthStatus()
      }, 100)
    })
  },
  mounted() {
    // Register consent modal with consent service
    // Use $nextTick to ensure the ref is available
    this.$nextTick(() => {
      if (this.$refs.consentModal) {
        console.log('🔍 [App] Consent modal ref:', this.$refs.consentModal);
        console.log('🔍 [App] Consent modal show method:', typeof this.$refs.consentModal?.show);
        consentService.registerModal(this.$refs.consentModal)
        console.log('✅ Consent modal registered globally')
      } else {
        console.error('❌ [App] Consent modal ref not found!');
      }
    });
  },
  beforeUnmount() {
    window.removeEventListener('authChanged', this.checkAuthStatus)
  },
  watch: {
    '$route.name'(newRouteName) {
      if (this.isAuthenticated) {
        this.warmupPerfRoutesPinia(newRouteName)
      }
    }
  },
  computed: {
    frameworkRenderKey() {
      const frameworkStore = useFrameworkStore()
      return frameworkStore.selectedFrameworkId || 'all'
    },
    // Form routes load framework from session in created() — remounting on frameworkRenderKey
    // change mid-init causes "Cannot read properties of null (reading 'component')".
    routeComponentKey() {
      const formRouteNames = new Set([
        'CreatePolicy',
        'CreateCompliance',
        'EditCompliance',
        'CreateRisk',
        'CreateRiskInstance',
        'UploadFramework',
        'CreateFramework',
        'AssignAudit',
        'IncidentManagement',
        'EventCreation',
        'EventEditModal',
      ])
      if (formRouteNames.has(this.$route.name)) {
        return this.$route.fullPath
      }
      return `${this.$route.fullPath}::${this.frameworkRenderKey}`
    },
  },
  methods: {
    isLoginRoute(path) {
      if (!path || typeof path !== 'string') return false
      const normalized = path.replace(/\/+$/, '').toLowerCase()
      return normalized === '/login'
    },
    clearStaleAuthData() {
      // Cookie-first auth: do not require JS-readable tokens.
      // Only clear truly inconsistent shell flags.
      const hasValidUserId = !!(sessionStorage.getItem('user_id') || localStorage.getItem('user_id'))
      const isLoggedIn = (sessionStorage.getItem('is_logged_in') || localStorage.getItem('is_logged_in')) === 'true'

      // Remove legacy token artifacts always (safe cleanup).
      sessionStorage.removeItem('access_token')
      sessionStorage.removeItem('refresh_token')
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')

      if ((hasValidUserId && !isLoggedIn) || (!hasValidUserId && isLoggedIn)) {
        console.log('🧹 Clearing stale authentication data')
        sessionStorage.removeItem('user_id')
        sessionStorage.removeItem('user')
        sessionStorage.removeItem('current_user')
        sessionStorage.removeItem('is_logged_in')
        sessionStorage.removeItem('user_email')
        sessionStorage.removeItem('user_name')
        localStorage.removeItem('user_id')
        localStorage.removeItem('is_logged_in')
        localStorage.removeItem('user_email')
        localStorage.removeItem('user_name')
      }
    },
   
    async checkAuthStatus() {
      // Cookie-first auth: use shell flags + backend session verification.
      const userId = sessionStorage.getItem('user_id') || localStorage.getItem('user_id')
      const isLoggedIn = (sessionStorage.getItem('is_logged_in') || localStorage.getItem('is_logged_in')) === 'true'
      const hasAuthFlag = (sessionStorage.getItem('isAuthenticated') || localStorage.getItem('isAuthenticated')) === 'true'
      
      const hasAuthData = !!(userId && (isLoggedIn || hasAuthFlag))
      let cookieSessionValid = false

      if (hasAuthData) {
        if (sessionStorage.getItem('cookie_session_validated') === 'true') {
          cookieSessionValid = true
        } else {
          try {
            const { default: authService } = await import('./services/authService.js')
            const result = await authService.validateSession()
            cookieSessionValid = !!(result && result.success)
            if (cookieSessionValid) {
              sessionStorage.setItem('cookie_session_validated', 'true')
              this.showSessionReconnectBanner = false
            } else {
              // Keep shell authenticated on transient backend/network errors.
              // Only force logout path on explicit auth failure (401/403).
              if (result && result.isAuthError === true) {
                sessionStorage.removeItem('cookie_session_validated')
                this.showSessionReconnectBanner = false
              } else {
                cookieSessionValid = true
                this.showSessionReconnectBanner = true
              }
            }
          } catch (error) {
            // Transient verify failures should not flash login UI while user is active.
            cookieSessionValid = true
            this.showSessionReconnectBanner = true
          }
        }
      }

      this.isAuthenticated = hasAuthData && cookieSessionValid
      
      // If user is authenticated on page refresh, set hasExplicitlyLoggedIn to true
      if (this.isAuthenticated && !this.hasExplicitlyLoggedIn) {
        this.hasExplicitlyLoggedIn = true
      }
      if (this.isAuthenticated) {
        this.warmupPerfRoutesPinia(this.$route?.name)
      }
     
      console.log('🔐 Authentication check:', {
        hasToken: undefined, // HttpOnly cookie (not JS-readable)
        hasUserId: !!userId,
        isLoggedIn: isLoggedIn,
        cookieSessionValid: cookieSessionValid,
        hasExplicitlyLoggedIn: this.hasExplicitlyLoggedIn,
        isAuthenticated: this.isAuthenticated,
        sidebarWillRender: this.isAuthenticated,
        currentRoute: this.$route?.path
      })

      // Hard safety: never render login page inside authenticated shell.
      if (this.isAuthenticated && this.isLoginRoute(this.$route?.path)) {
        this.$router.replace('/home').catch(() => {})
      }

      // Hide banner once authenticated path is healthy again.
      if (this.isAuthenticated && cookieSessionValid && sessionStorage.getItem('cookie_session_validated') === 'true') {
        this.showSessionReconnectBanner = false
      }
    },
   
    // Load framework from backend session
    async loadFrameworkFromSession() {
      try {
        console.log('🔄 App.vue: Loading framework from backend session...')
        const frameworkStore = useFrameworkStore()
        await frameworkStore.loadFrameworkFromSession()
      } catch (error) {
        console.error('❌ App.vue: Error loading framework from session:', error)
      }
    },
    warmupPerfRoutesPinia(routeName) {
      // Do not trigger cross-module prefetch from App shell.
      // Home/login must stay light and only call APIs needed for current screen.
      // Module-specific pages fetch their own data and now use Pinia-first rendering.
      if (!routeName) return
    },
    
    // Method to be called when user successfully logs in
    onSuccessfulLogin() {
      this.hasExplicitlyLoggedIn = true
      // Force immediate authentication state update
      this.isAuthenticated = true
      this.checkAuthStatus()
      // Load framework after successful login
      this.loadFrameworkFromSession()
      this.startPeriodicTokenRefresh()
      // Trigger auth changed event for session timeout service
      window.dispatchEvent(new Event('authChanged'))
      
      // Additional safety check after a short delay
      this.$nextTick(() => {
        setTimeout(() => {
          this.checkAuthStatus()
        }, 50)
      })
    },
   
    // Method to be called when user logs out
    async onLogout() {
      window.__grcLoggingOut = true
      this.hasExplicitlyLoggedIn = false
      this.isAuthenticated = false
      try {
        const { default: policyDataService } = await import('./services/policyService.js')
        policyDataService.resetOnLogout()
      } catch (error) {
        console.warn('Unable to reset policy prefetch on logout:', error?.message || error)
      }
      sessionStorage.removeItem('cookie_session_validated')
      sessionStorage.removeItem('access_token')
      sessionStorage.removeItem('refresh_token')
      sessionStorage.removeItem('user_id')
      sessionStorage.removeItem('user')
      sessionStorage.removeItem('current_user')
      sessionStorage.removeItem('is_logged_in')
      sessionStorage.removeItem('user_email')
      sessionStorage.removeItem('user_name')
      localStorage.removeItem('access_token')
      localStorage.removeItem('user_id')
      localStorage.removeItem('is_logged_in')
      localStorage.removeItem('user_email')
      localStorage.removeItem('user_name')
     
      // Stop periodic token refresh
      try {
        const { default: authService } = await import('./services/authService.js')
        authService.stopPeriodicTokenRefresh()
        console.log('🛑 Periodic token refresh stopped on logout')
      } catch (error) {
        console.error('❌ Error stopping periodic token refresh:', error)
      } finally {
        window.__grcLoggingOut = false
      }
    },
   
    // Method to force authentication check (useful for debugging)
    forceAuthCheck() {
      console.log('🔄 Force authentication check triggered')
      this.checkAuthStatus()
    },
   
    // Method to start periodic token refresh (optional if implemented in service)
    async startPeriodicTokenRefresh() {
      try {
        const { default: authService } = await import('./services/authService.js')
        // Check if the method exists before calling it
        if (authService && typeof authService.startPeriodicTokenRefresh === 'function') {
          authService.startPeriodicTokenRefresh()
          console.log('🔄 Periodic token refresh started from App.vue')
        } else {
          console.log('ℹ️ Periodic token refresh not available in authService (optional feature)')
        }
      } catch (error) {
        // Don't log as error - this is an optional feature
        console.log('ℹ️ Periodic token refresh not available:', error.message)
      }
    }
  }
}
</script>
 
<style>
body {
  margin: 0;
  font-family: Arial, Helvetica, sans-serif;
}
 
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
  min-height: 100vh;
}
 
.app-container {
  display: flex;
  min-height: 100vh;
}
 
.main-content {
  flex: 1;
  background-color: #ffffff;
  min-width: 0;
  overflow-x: hidden;
}

.main-content.with-sidebar {
  padding: 4rem 20px 20px;
  margin-left: 20px; /* Account for sidebar width */
}
 
.login-container {
  min-height: 100vh;
  width: 100%;
  position: relative;
  z-index: 0;
  flex: 1;
  display: block;
}

/* :deep() is for scoped SFC styles only; here it can produce invalid CSS */
.login-container .login-page {
  min-height: 100vh;
}

.session-reconnect-banner {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 9999;
  background: #fff4e5;
  color: #8a5300;
  border-bottom: 1px solid #ffd8a8;
  padding: 8px 16px;
  font-size: 13px;
  font-weight: 600;
  text-align: center;
}
</style>
 