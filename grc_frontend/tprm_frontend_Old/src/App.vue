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
import { RouterView, useRoute } from 'vue-router'
import AppLayout from './components/layout/AppLayout.vue'
import PopupModal from './popup/PopupModal.vue'
import { computed, onMounted } from 'vue'
import { useStore } from 'vuex'
import { getTprmApiBaseUrl } from '@/utils/backendEnv'

const route = useRoute()
const store = useStore()

// Define standalone routes that should not have layout
const standaloneRoutes = [
  'VendorPortal',
  'VendorPortalSubmit', 
  'VendorPortalOpen',
  'TestVendorPortal',
  'VendorPortalDirect',
  'AwardResponse',
  'Login'
]

const isStandaloneRoute = computed(() => {
  return standaloneRoutes.includes(route.name)
})

onMounted(() => {
  console.log('=== TPRM App Mounted ===')
  console.log('Environment:', import.meta.env.MODE)
  console.log('API Base URL:', getTprmApiBaseUrl())
  
  // Initialize authentication state from localStorage
  store.dispatch('auth/initializeAuth')
  console.log('Auth initialized')
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
