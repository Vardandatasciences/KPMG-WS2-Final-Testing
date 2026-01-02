import { createApp } from 'vue'
import App from './App_rfp.vue'
import router from './router/index_rfp'
import { sharedPinia } from './store/shared.js'
import { useRFPStore, useVendorStore, useUserStore } from './store/index_rfp.js'
import './assets/styles/styles.css'

// Import RFP components globally
import rfpBadge from './components_rfp/rfpBadge.vue'
import rfpButton from './components_rfp/rfpButton.vue'
import rfpCard from './components_rfp/rfpCard.vue'
import rfpCardContent from './components_rfp/rfpCardContent.vue'
import rfpCardDescription from './components_rfp/rfpCardDescription.vue'
import rfpCardFooter from './components_rfp/rfpCardFooter.vue'
import rfpCardHeader from './components_rfp/rfpCardHeader.vue'
import rfpCardTitle from './components_rfp/rfpCardTitle.vue'
import rfpProgress from './components_rfp/rfpProgress.vue'
import rfpToast from './components_rfp/rfpToast.vue'
import rfpToaster from './components_rfp/rfpToaster.vue'

// Import UI components
import Button from './components_rfp/Button.vue'
import Card from './components_rfp/Card.vue'

const app = createApp(App)

app.use(router)

// Use the shared Pinia instance
app.use(sharedPinia)

// Register components globally
app.component('rfp-badge', rfpBadge)
app.component('rfp-button', rfpButton)
app.component('rfp-card', rfpCard)
app.component('rfp-card-content', rfpCardContent)
app.component('rfp-card-description', rfpCardDescription)
app.component('rfp-card-footer', rfpCardFooter)
app.component('rfp-card-header', rfpCardHeader)
app.component('rfp-card-title', rfpCardTitle)
app.component('rfp-progress', rfpProgress)
app.component('rfp-toast', rfpToast)
app.component('rfp-toaster', rfpToaster)

// Register UI components
app.component('Button', Button)
app.component('Card', Card)

// Initialize individual stores
const rfpStore = useRFPStore()
const vendorStore = useVendorStore()
const userStore = useUserStore()

// Fetch initial data
rfpStore.fetchRFPs()
vendorStore.fetchVendors()

app.mount('#app')
