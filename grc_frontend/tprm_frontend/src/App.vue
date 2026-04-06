<template>
  <div class="min-h-screen bg-background">
    <!-- Standalone routes (no layout) -->
    <RouterView v-if="isStandaloneRoute" />
    
    <!-- Routes with layout -->
    <AppLayout v-else>
      <RouterView />
    </AppLayout>
    
    <!-- Global Popup Modal -->
    <PopupModal />
  </div>
</template>

<script setup>
import { RouterView, useRoute, useRouter } from 'vue-router'
import AppLayout from './components/layout/AppLayout.vue'
import PopupModal from './popup/PopupModal.vue'
import { computed, onMounted } from 'vue'
import { useStore } from 'vuex'
import { useRFPStore } from '@/store/index_rfp'
import { getParentPostMessageTargetOrigin } from '@/utils/parentPostMessageOrigin.js'

const route = useRoute()
const router = useRouter()
const store = useStore()

// Define standalone routes that should not have layout
const standaloneRoutes = [
  'VendorPortal',
  'VendorPortalSubmit', 
  'VendorPortalOpen',
  'TestVendorPortal',
  'VendorPortalDirect',
  'AwardResponse',
  'Questionnaire Response (Public)'
  // Login removed - using GRC login instead
]

const isStandaloneRoute = computed(() => {
  return standaloneRoutes.includes(route.name)
})

onMounted(() => {
  console.log('=== TPRM App Mounted ===')
  console.log('Environment:', import.meta.env.MODE)
  console.log('API Base URL:', import.meta.env.VITE_API_BASE_URL)
  
  // Initialize authentication state from localStorage
  store.dispatch('auth/initializeAuth')
  console.log('Auth initialized')
  
  // Listen for auth sync messages from GRC parent (if in iframe)
  const isInIframe = window.self !== window.top
  if (isInIframe) {
    console.log('[TPRM App] In iframe - setting up auth sync listener')
    
    // Request auth from parent immediately
    if (window.parent && window.parent !== window) {
      console.log('[TPRM App] Requesting auth from parent...')
      window.parent.postMessage({ type: 'TPRM_AUTH_REQUEST' }, getParentPostMessageTargetOrigin())
    }
    
    // Listen for messages from parent (auth sync and navigation)
    const handleMessage = (event) => {
      if (window.parent !== window) {
        const allowed = getParentPostMessageTargetOrigin()
        if (allowed && event.origin !== allowed) {
          return
        }
        if (event.source !== window.parent) {
          return
        }
      }

      // Debug: log all messages (can be removed later)
      if (event.data && event.data.type) {
        console.log('[TPRM App] 📨 Received message from parent:', event.data.type, event.data)
      }
      
      // Handle auth sync from parent
      if (event.data && event.data.type === 'GRC_AUTH_SYNC') {
        console.log('[TPRM App] ✅ Received auth sync from GRC parent:', {
          authMode: event.data.authMode,
          hasUser: !!event.data.user,
          isAuthenticated: event.data.isAuthenticated
        })

        sessionStorage.removeItem('access_token')
        sessionStorage.removeItem('refresh_token')
        sessionStorage.removeItem('session_token')
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('session_token')

        let userPayload = event.data.user
        if (userPayload) {
          sessionStorage.setItem('current_user', JSON.stringify(userPayload))
          localStorage.removeItem('current_user')
          const uid = userPayload.UserId ?? userPayload.user_id ?? userPayload.id
          if (uid != null && uid !== '') {
            localStorage.setItem('user_id', String(uid))
          }
          if (userPayload.tenant_id) {
            localStorage.setItem('tenant_id', userPayload.tenant_id)
          }
          if (userPayload.tenant_name) {
            localStorage.setItem('tenant_name', userPayload.tenant_name)
          }
        } else if (event.data.isAuthenticated && event.data.userId) {
          localStorage.setItem('user_id', String(event.data.userId))
          userPayload = {
            UserId: event.data.userId,
            user_id: event.data.userId,
            id: event.data.userId
          }
        } else {
          console.warn('[TPRM App] ⚠️ No user payload in auth sync (cookie mode)')
        }

        if (event.data.tenantId) {
          localStorage.setItem('tenant_id', event.data.tenantId)
        }
        if (event.data.tenantName) {
          localStorage.setItem('tenant_name', event.data.tenantName)
        }
        if (event.data.tenant_id) {
          localStorage.setItem('tenant_id', event.data.tenant_id)
        }
        if (event.data.tenant_name) {
          localStorage.setItem('tenant_name', event.data.tenant_name)
        }

        const previousTenantId = sessionStorage.getItem('rfp_store_tenant_id')
        const newTenantId =
          userPayload?.tenant_id ||
          event.data.tenantId ||
          event.data.tenant_id ||
          localStorage.getItem('tenant_id')

        if (previousTenantId && newTenantId && previousTenantId !== newTenantId) {
          console.log(`[TPRM App] 🔄 Tenant changed from ${previousTenantId} to ${newTenantId}, clearing RFP store`)
          try {
            const rfpStore = useRFPStore()
            rfpStore.clearStore()
          } catch (e) {
            console.warn('[TPRM App] ⚠️ Could not clear RFP store:', e)
          }
        }

        if (userPayload && event.data.isAuthenticated) {
          store.commit('auth/SET_AUTH', {
            user: userPayload,
            token: null
          })
          console.log('[TPRM App] ✅ Auth synced to Vuex store (cookie-first)')
        }
      }
      
      // Handle navigation request from parent
      if (event.data && event.data.type === 'NAVIGATE_TO_ROUTE') {
        const targetPath = event.data.path
        if (targetPath) {
          console.log('[TPRM App] 🧭 Received navigation request from parent:', targetPath)
          // Normalize path (remove leading /tprm if present, ensure leading slash)
          let normalizedPath = targetPath.startsWith('/tprm/') 
            ? targetPath.replace('/tprm', '') 
            : targetPath.startsWith('/tprm') 
            ? targetPath.replace('/tprm', '') 
            : targetPath
          if (!normalizedPath.startsWith('/')) {
            normalizedPath = '/' + normalizedPath
          }
          
          // Only navigate if path is different from current route
          if (normalizedPath !== route.path) {
            console.log('[TPRM App] 🧭 Navigating to:', normalizedPath, '(current:', route.path, ')')
            router.push(normalizedPath).catch(err => {
              // Ignore navigation errors (e.g., if already navigating to the same route)
              if (err.name !== 'NavigationDuplicated') {
                console.error('[TPRM App] Navigation error:', err)
                // Check for syntax errors in component
                if (err.message && (err.message.includes('Unexpected token') || err.message.includes('SyntaxError'))) {
                  console.error('[TPRM App] ⚠️ Syntax error detected in component:', {
                    path: normalizedPath,
                    error: err.message,
                    stack: err.stack
                  })
                  // Show error via PopupService if available
                  try {
                    const { PopupService } = require('@/popup/popupService')
                    PopupService.error(
                      `Error loading page: ${normalizedPath}\n\nThis may be due to a syntax error in the component file. Please check the browser console for details.`,
                      'Navigation Error'
                    )
                  } catch (e) {
                    // PopupService not available, just log
                    console.error('Could not show error popup:', e)
                  }
                }
              }
            })
          } else {
            console.log('[TPRM App] Already at target path, skipping navigation')
          }
        }
      }
    }
    
    // Set up listener immediately
    window.addEventListener('message', handleMessage)
    console.log('[TPRM App] ✅ Message listener set up (auth sync + navigation)')
    
    // Also check if auth data is already in parent's localStorage (for immediate sync)
    // This is a fallback in case the message was sent before listener was set up
    setTimeout(async () => {
      try {
        const authService = (await import('@/services/authService')).default
        const ok = await authService.isAuthenticated()
        if (!ok) {
          console.log('[TPRM App] No valid cookie session, requesting auth again...')
          if (window.parent && window.parent !== window) {
            window.parent.postMessage({ type: 'TPRM_AUTH_REQUEST' }, getParentPostMessageTargetOrigin())
          }
        }
      } catch (e) {
        // If anything goes wrong, fall back to requesting auth again.
        if (window.parent && window.parent !== window) {
          window.parent.postMessage({ type: 'TPRM_AUTH_REQUEST' }, getParentPostMessageTargetOrigin())
        }
      }
    }, 500)
  }
})
</script>

<style>
/* Global styles for standalone vendor portal */
.vendor-portal-standalone {
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  right: 0 !important;
  bottom: 0 !important;
  width: 100vw !important;
  height: 100vh !important;
  z-index: 99999 !important;
  overflow-y: auto !important;
  overflow-x: hidden !important;
  background-color: #f9fafb !important;
  margin: 0 !important;
  padding: 0 !important;
}

/* Hide any external layout elements when on standalone routes */
body.standalone-route aside,
body.standalone-route .sidebar,
body.standalone-route .app-sidebar,
body.standalone-route header,
body.standalone-route .header,
body.standalone-route .app-header,
body.standalone-route nav:not(.vendor-portal nav),
body.standalone-route .navigation:not(.vendor-portal .navigation),
body.standalone-route .app-navigation:not(.vendor-portal .app-navigation),
body.standalone-route .app-layout:not(.vendor-portal .app-layout),
body.standalone-route .main-content:not(.vendor-portal .main-content) {
  display: none !important;
  visibility: hidden !important;
}

/* Ensure body and html are clean for standalone routes */
body.standalone-route {
  margin: 0 !important;
  padding: 0 !important;
  overflow-y: auto !important;
  overflow-x: hidden !important;
}

html.standalone-route {
  margin: 0 !important;
  padding: 0 !important;
}
</style>
