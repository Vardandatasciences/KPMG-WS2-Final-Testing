<template>
  <header class="main-header" :class="{ 'scrolled': isScrolled }">
    <div class="header-content">
      <div class="logo">
      </div>
      
      <nav class="main-nav">
        <router-link :to="{ name: 'home' }" class="nav-link" :class="{ active: isRouteActive('home') }">Dashboard</router-link>
        <router-link :to="{ name: 'PolicyDashboard' }" class="nav-link" :class="{ active: isRouteActive('PolicyDashboard') }">Policies</router-link>
        <router-link :to="{ name: 'ComplianceDashboard' }" class="nav-link" :class="{ active: isRouteActive('ComplianceDashboard') }">Compliance</router-link>
        <router-link :to="{ name: 'RiskDashboard' }" class="nav-link" :class="{ active: isRouteActive('RiskDashboard') }">Risk</router-link>
        <router-link :to="{ name: 'AuditorUserDashboard' }" class="nav-link" :class="{ active: isRouteActive('AuditorUserDashboard') }">Audits</router-link>
        <router-link :to="{ name: 'IncidentPerformanceDashboard' }" class="nav-link" :class="{ active: isRouteActive('IncidentPerformanceDashboard') }">Incidents</router-link>
      </nav>
      
      <div class="header-actions">
        <label
          class="framework-mode-toggle"
          title="Specific framework changes are done on Home"
        >
          <span class="framework-mode-main">
            <span class="framework-mode-label">All Frameworks</span>
            <input
              type="checkbox"
              class="framework-mode-checkbox"
              :checked="isAllFrameworksMode"
              :disabled="isSwitchingFrameworkMode"
              @change="handleFrameworkModeToggle"
            >
            <span class="framework-mode-slider"></span>
          </span>
          <span class="framework-mode-badge" aria-label="framework mode info">
            Framework Mode
          </span>
          <span class="framework-mode-tooltip" role="tooltip">
            Specific framework changes are done on Home
          </span>
        </label>

        <!-- Notification Bell -->
        <div class="notification-bell" @click="navigateToNotifications">
          <i class="fas fa-bell"></i>
          <span v-if="unreadCount > 0" class="notification-badge">{{ unreadCount }}</span>
        </div>
        
        <button @click="logout" class="btn btn-reject logout-btn">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9"/>
          </svg>
          Logout
        </button>
      </div>
    </div>
  </header>
</template>

<script>
import logo from '../assets/RiskaVaire.png'
import { API_ENDPOINTS, axiosInstance } from '../config/api.js'
import authService from '../services/authService.js'
import { useFrameworkStore } from '@/stores/framework'

export default {
  name: 'GlobalNavbar',
  data() {
    return {
      isScrolled: false,
      userName: '',
      userInitials: '',
      logo,
      unreadCount: 0,
      pollInterval: null,
      frameworkStore: null,
      isAllFrameworksMode: true,
      isSwitchingFrameworkMode: false
    }
  },
  async mounted() {
    this.frameworkStore = useFrameworkStore()
    this.setupScrollListener()
    this.loadUserData()
    this.startNotificationPolling()
    await this.syncFrameworkModeState()
    window.addEventListener('framework-changed', this.syncFrameworkModeState)
  },
  beforeUnmount() {
    window.removeEventListener('scroll', this.handleScroll)
    window.removeEventListener('framework-changed', this.syncFrameworkModeState)
    if (this.pollInterval) {
      clearInterval(this.pollInterval)
    }
  },
  methods: {
    setupScrollListener() {
      window.addEventListener('scroll', this.handleScroll)
    },
    handleScroll() {
      this.isScrolled = window.scrollY > 10
    },
    loadUserData() {
      const userName = sessionStorage.getItem('user_name') || localStorage.getItem('user_name') || 'User'
      this.userName = userName
      this.userInitials = userName.split(' ').map(name => name.charAt(0)).join('').toUpperCase()
    },
    isRouteActive(routeName) {
      return this.$route.name === routeName
    },
    navigateToNotifications() {
      this.$router.push('/notifications')
    },
    async syncFrameworkModeState() {
      try {
        if (!this.frameworkStore) {
          this.frameworkStore = useFrameworkStore()
        }
        await this.frameworkStore.loadFrameworkFromSession()
        this.isAllFrameworksMode = !this.frameworkStore.selectedFrameworkId || this.frameworkStore.selectedFrameworkId === 'all'
      } catch (error) {
        console.warn('[GlobalNavbar] Unable to sync framework mode state:', error?.message || error)
      }
    },
    async handleFrameworkModeToggle(event) {
      const checked = !!event?.target?.checked
      if (!checked) {
        // Keep toggle ON unless a specific framework is selected from Home.
        // Users should not turn this OFF directly from navbar.
        this.isAllFrameworksMode = true
        return
      }

      this.isSwitchingFrameworkMode = true
      try {
        if (!this.frameworkStore) {
          this.frameworkStore = useFrameworkStore()
        }
        await this.frameworkStore.resetFramework()
        this.isAllFrameworksMode = true
      } catch (error) {
        console.error('[GlobalNavbar] Failed to enable all frameworks mode:', error)
        await this.syncFrameworkModeState()
      } finally {
        this.isSwitchingFrameworkMode = false
      }
    },
    async fetchUnreadCount() {
      try {
        const userId = sessionStorage.getItem('user_id') || localStorage.getItem('user_id')
        const isLoggedIn = (sessionStorage.getItem('is_logged_in') || localStorage.getItem('is_logged_in')) === 'true'
        const hasAuthFlag = (sessionStorage.getItem('isAuthenticated') || localStorage.getItem('isAuthenticated')) === 'true'
        
        if (!userId || (!isLoggedIn && !hasAuthFlag)) {
          return
        }
        
        // Use axiosInstance (configured with withCredentials: true) instead of raw axios
        const response = await axiosInstance.get(API_ENDPOINTS.GET_NOTIFICATIONS(userId), {
          timeout: 5000
        })
        
        if (response.data && response.data.status === 'success') {
          const count = (response.data.notifications || []).filter(n => n.status && !n.status.isRead).length
          this.unreadCount = count
        }
      } catch (error) {
        console.log('Error fetching notifications:', error.message)
      }
    },
    startNotificationPolling() {
      this.fetchUnreadCount()
      // OPTIMIZED: Reduced polling frequency from 30s to 2 minutes to reduce server load
      this.pollInterval = setInterval(this.fetchUnreadCount, 120000) // Poll every 2 minutes
    },
    async logout() {
      try {
        console.log('🔄 [GlobalNavbar] Logout button clicked - starting logout process...')
        
        // Stop notification polling
        if (this.pollInterval) {
          clearInterval(this.pollInterval)
          this.pollInterval = null
          console.log('🛑 [GlobalNavbar] Notification polling stopped')
        }
        
        // Call authService.logout() which will:
        // 1. Call the backend /api/jwt/logout/ endpoint
        // 2. Clear all auth data properly
        // 3. Emit logout events
        console.log('📞 [GlobalNavbar] Calling authService.logout()...')
        await authService.logout()
        
        console.log('✅ [GlobalNavbar] Logout successful')
        
        // Dispatch auth change event
        window.dispatchEvent(new CustomEvent('authChanged'))
        
        // Navigate to login
        console.log('🔄 [GlobalNavbar] Redirecting to login page...')
        this.$router.push('/login')
      } catch (error) {
        console.error('❌ [GlobalNavbar] Logout error:', error)
        // Force redirect to login even if logout fails
        this.$router.push('/login')
      }
    }
  }
}
</script>

<style scoped>
/* Header Styles */
.main-header {
  position: fixed;
  top: 0px;
  left: 256px; /* Updated to match sidebar width (reduced from 280px to 256px) */
  right: 0;
  z-index: 3000;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-bottom: 0.5px solid rgb(234, 223, 223); /* Remove bottom border */
  transition: all 0.3s ease;
  padding: 0.70rem 1rem;
  overflow: hidden; /* Prevent content from extending beyond header boundaries */
}

.main-header.scrolled {
  background: rgba(255, 255, 255, 0.98);
  box-shadow: 0 4px 32px rgba(0, 0, 0, 0.1);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.4rem 2rem;
  max-width: 1400px;
  margin-top: 0 auto;
  margin-left: 0; /* Removed negative margin to prevent overlap with sidebar */
  position: relative;
  z-index: 1; /* Lower z-index so sidebar-header appears above */
  min-width: 0; /* Prevent extending beyond parent */
}

.logo {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.logo-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 0;
  overflow: visible;
  background: transparent;
  border: none;
  box-shadow: none;
}

.logo-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
  border-radius: 0;
  background: transparent;
  border: none;
  box-shadow: none;
}

.logo-text {
  font-size: 1.25rem;
  font-weight: 700;
  color: #1f2937;
}

.main-nav {
  display: flex;
  align-items: center;
  padding-top: -20px;
  gap: 2rem;
  margin-left: -7rem; /* Shift nav links a bit to the right */
}

.nav-link {
  text-decoration: none;
  color: #6b7280;
  font-weight: 500;
  font-size: 0.95rem;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  transition: all 0.2s ease;
  position: relative;
}

.nav-link:hover {
  color: #1e40af;
  background: rgba(30, 64, 175, 0.05);
}

.nav-link.active {
  color: #1e40af;
  background: rgba(30, 64, 175, 0.1);
}

.header-actions {
  display: flex;
  align-items: center;
  margin-right: 15px;
  gap: 2.5rem;
}

.user-menu {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 1rem;
  border-radius: 12px;
  background: rgba(0, 0, 0, 0.02);
}

.user-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #1e40af, #3b82f6);
  border-radius: 50%;
  color: white;
  font-weight: 600;
  font-size: 0.875rem;
}

.user-name {
  font-weight: 500;
  color: #374151;
  font-size: 0.875rem;
}

/* Notification Bell Styles */
.notification-bell {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  color: #6b7280;
}

.notification-bell:hover {
  background: rgba(30, 64, 175, 0.05);
  color: #1e40af;
  transform: translateY(-1px);
}

.notification-bell i {
  font-size: 1.1rem;
}

.notification-badge {
  position: absolute;
  top: -2px;
  right: -2px;
  background: #dc2626;
  color: white;
  border-radius: 100%;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.7rem;
  font-weight: 600;
  border: 2px solid white;
}

.logout-btn svg {
  position: relative;
  top: -1px; /* nudge icon upward */
  margin-right: 0;
}

.framework-mode-toggle {
  display: inline-flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
  user-select: none;
  position: relative;
}

.framework-mode-main {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.framework-mode-label {
  font-size: 12px;
  font-weight: 600;
  color: #4b5563;
}

.framework-mode-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(37, 99, 235, 0.12);
  border: 1px solid rgba(37, 99, 235, 0.25);
  color: #1d4ed8;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.3px;
  text-transform: uppercase;
}

.framework-mode-checkbox {
  opacity: 0;
  width: 0;
  height: 0;
  position: absolute;
}

.framework-mode-slider {
  position: relative;
  width: 40px;
  height: 22px;
  background: #d1d5db;
  border-radius: 999px;
  transition: background 0.2s ease;
}

.framework-mode-slider::before {
  content: '';
  position: absolute;
  left: 2px;
  top: 2px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #fff;
  transition: transform 0.2s ease;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

.framework-mode-checkbox:checked + .framework-mode-slider {
  background: #2563eb;
}

.framework-mode-checkbox:checked + .framework-mode-slider::before {
  transform: translateX(18px);
}

.framework-mode-tooltip {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  min-width: 230px;
  max-width: 280px;
  padding: 8px 10px;
  border-radius: 8px;
  background: #111827;
  color: #f9fafb;
  font-size: 11px;
  line-height: 1.35;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
  opacity: 0;
  visibility: hidden;
  transform: translateY(-4px);
  transition: opacity 0.15s ease, transform 0.15s ease, visibility 0.15s ease;
  z-index: 3500;
  pointer-events: none;
}

.framework-mode-tooltip::before {
  content: '';
  position: absolute;
  top: -5px;
  left: 14px;
  width: 10px;
  height: 10px;
  background: #111827;
  transform: rotate(45deg);
}

.framework-mode-toggle:hover .framework-mode-tooltip {
  opacity: 1;
  visibility: visible;
  transform: translateY(0);
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .main-header {
    left: 0;
  }
  
  .header-content {
    padding: 1rem;
  }
  
  .main-nav {
    gap: 1rem;
  }
  
  .nav-link {
    padding: 0.5rem;
    font-size: 0.875rem;
  }
  
  .logo-text {
    display: none;
  }
  
  .notification-bell {
    width: 36px;
    height: 36px;
  }
  
  .notification-badge {
    width: 16px;
    height: 16px;
    font-size: 0.65rem;
  }
}
</style>
