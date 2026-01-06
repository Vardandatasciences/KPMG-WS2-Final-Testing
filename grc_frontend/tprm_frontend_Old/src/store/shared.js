import { createPinia } from 'pinia'
import { createPersistedState, createSessionPersistedState } from './persistence'

// Create shared pinia instance with persistence
export const sharedPinia = createPinia()

// Add persistence plugins
sharedPinia.use(createPersistedState({
  key: 'rfp-app',
  include: ['user', 'rfp.currentRFP'], // Persist user auth and current RFP
  exclude: ['rfp.loading', 'rfp.error', 'vendor.loading', 'vendor.error', 'user.loading', 'user.error'] // Don't persist loading/error states
}))

sharedPinia.use(createSessionPersistedState({
  key: 'rfp-session',
  include: ['rfp.rfps', 'vendor.vendors'] // Persist data temporarily in session storage
}))

// Export the stores for direct import
export { useRFPStore, useVendorStore, useUserStore } from './index_rfp'
