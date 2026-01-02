import { createApp } from 'vue'
import GenericWrapper from '@/components_rfp/GenericWrapper.vue'
import AssigneeDecision from '@/views/rfp-approval/AssigneeDecision.vue'
import { sharedPinia } from '@/store/shared.js'
import { useRFPStore, useVendorStore, useUserStore } from '@/store/index.js'

// Create Vue app
const app = createApp(GenericWrapper, { component: AssigneeDecision })

// Use the shared Pinia instance
app.use(sharedPinia)

// Initialize individual stores
const rfpStore = useRFPStore()
const vendorStore = useVendorStore()
const userStore = useUserStore()

// Fetch initial data
rfpStore.fetchRFPs()
vendorStore.fetchVendors()

// Mount the app
app.mount('#app')
