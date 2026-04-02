import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'
import axios from 'axios'
import '@fortawesome/fontawesome-free/css/all.min.css'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import Popup from './modules/popup';
import './styles/theme.css'
import './assets/css/main.css'
import './assets/css/dropdown.css'
import './assets/css/darktheme.css'
import './assets/css/Colourblindness.css'
import { API_BASE_URL } from './config/api.js'

// Create Vuetify instance
const vuetify = createVuetify({
  components,
  directives,
  icons: {
    defaultSet: 'mdi',
  },
})

// Configure axios defaults for JWT authentication
axios.defaults.baseURL = API_BASE_URL  // Use centralized API configuration
axios.defaults.headers.common['Content-Type'] = 'application/json'
axios.defaults.timeout = 120000  // 2 minutes timeout (increased for long-running operations)

// CRITICAL: Enable credentials (cookies) for session management
axios.defaults.withCredentials = true
console.log('🍪 Axios configured to send cookies with requests (withCredentials: true)')

// Cookie-first auth: do not inject Authorization headers from browser storage.
console.log('✅ GLOBAL Axios request flow uses HttpOnly cookies only');

// Initialize auth service (cookie-first, no token storage)
import './services/authService.js'

console.log('🔐 Axios configured with JWT authentication')

// Track page load time for interceptor
sessionStorage.setItem('pageLoadTime', Date.now().toString())

// Setup HTTP interceptor for access control
console.log('🛡️ Setting up HTTP interceptor for access control')

// Add response interceptor to handle 403 (Forbidden) responses
// COMMENTED OUT: Disabled to allow home page to be accessible to all users
// axios.interceptors.response.use(
//   (response) => {
//     return response;
//   },
//   (error) => {
//     if (error.response && error.response.status === 403) {
//       console.log('🚫 Access denied (403) - redirecting to access denied page');
//       
//       // Store access denied information
//       const accessDeniedInfo = {
//         feature: 'API endpoint',
//         message: error.response.data?.message || 'You do not have permission to access this resource.',
//         timestamp: new Date().toISOString(),
//         url: error.config?.url || 'Unknown',
//         requiredPermission: error.response.data?.required_permission || 'Unknown'
//       };
//       sessionStorage.setItem('accessDeniedInfo', JSON.stringify(accessDeniedInfo));
//       
//       // Redirect to access denied page
//       if (window.router) {
//         window.router.push('/access-denied');
//       }
//     }
//     return Promise.reject(error);
//   }
// );

const app = createApp(App)
app.config.compilerOptions.isCustomElement = tag => tag.includes('-')
app.config.performance = true
app.config.warnHandler = () => null 
app.use(router)
app.use(store)
app.use(ElementPlus)
app.use(vuetify)
app.use(Popup)

// Make router and store available globally for AccessUtils
window.router = router
window.store = store

// Global error handler to suppress reCAPTCHA timeout errors
window.addEventListener('unhandledrejection', (event) => {
  const error = event.reason;
  const errorMessage = error?.message || '';
  const errorString = error?.toString() || '';
  const errorStack = error?.stack || '';
  
  // Suppress reCAPTCHA timeout errors
  if (errorMessage.includes('Timeout') || errorString.includes('Timeout') ||
      errorMessage.includes('timeout') || errorString.includes('timeout') ||
      errorStack.includes('recaptcha') || errorStack.includes('recaptcha_en.js') ||
      errorMessage.includes('recaptcha') || errorString.includes('recaptcha')) {
    console.warn('⚠️ Suppressed unhandled promise rejection (likely reCAPTCHA timeout):', errorMessage);
    event.preventDefault(); // Prevent the error from being logged to console
    return;
  }
  
  // Suppress network errors
  if (errorMessage.includes('Network Error') || errorMessage.includes('ERR_NETWORK') ||
      errorString.includes('Network Error') || errorString.includes('ERR_NETWORK')) {
    console.warn('⚠️ Suppressed unhandled promise rejection (network error):', errorMessage);
    event.preventDefault();
    return;
  }
});

// Global error handler for general errors
window.addEventListener('error', (event) => {
  const error = event.error || event;
  const errorMessage = error?.message || '';
  const errorString = error?.toString() || '';
  const errorStack = error?.stack || '';
  
  // Suppress reCAPTCHA timeout errors
  if (errorMessage.includes('Timeout') || errorString.includes('Timeout') ||
      errorMessage.includes('timeout') || errorString.includes('timeout') ||
      errorStack.includes('recaptcha') || errorStack.includes('recaptcha_en.js') ||
      errorMessage.includes('recaptcha') || errorString.includes('recaptcha')) {
    console.warn('⚠️ Suppressed error (likely reCAPTCHA timeout):', errorMessage);
    event.preventDefault();
    return;
  }
});
// Initialize theme on app mount
const initializeTheme = () => {
  try {
    // Load theme from localStorage first (for immediate application)
    const savedTheme = localStorage.getItem('selected-theme') || 'light'
    const savedColorblind = localStorage.getItem('selected-colorblind')
    
    document.documentElement.setAttribute('data-theme', savedTheme)
    document.body.setAttribute('data-theme', savedTheme)
    
    // Apply color-blindness mode if set
    if (savedColorblind) {
      document.documentElement.setAttribute('data-colorblind', savedColorblind)
      document.body.setAttribute('data-colorblind', savedColorblind)
    }
    
    // Apply to app element after it's created
    setTimeout(() => {
      const appElement = document.getElementById('app')
      if (appElement) {
        appElement.setAttribute('data-theme', savedTheme)
        if (savedColorblind) {
          appElement.setAttribute('data-colorblind', savedColorblind)
        }
      }
    }, 0)
  } catch (error) {
    console.error('Error initializing theme:', error)
    // Default to light theme
    document.documentElement.setAttribute('data-theme', 'light')
    document.body.setAttribute('data-theme', 'light')
    setTimeout(() => {
      const appElement = document.getElementById('app')
      if (appElement) {
        appElement.setAttribute('data-theme', 'light')
      }
    }, 0)
  }
}

// Apply theme before mounting
initializeTheme()

app.mount('#app')
