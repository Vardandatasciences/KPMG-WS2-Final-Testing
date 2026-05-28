import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'
import { createPinia } from 'pinia'
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
import './assets/css/grc-skeleton.css'
import './assets/css/policy-module-skeleton.css'
import './assets/css/dropdown.css'
import './assets/css/darktheme.css'
import './assets/css/Colourblindness.css'
import { API_BASE_URL } from './config/api.js'
import { clearLegacyClientJwtKeys } from './utils/legacyAuthStorage.js'

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

// Global dedupe/cache for frequently repeated framework GETs across modules.
const SHARED_GET_CACHE_TTL_MS = 5000
const SHARED_GET_ENDPOINT_HINTS = [
  '/api/frameworks/get-selected/',
  '/api/frameworks/approved-active/',
]
const sharedGetCache = new Map()

const isSharedGetCandidate = (config) => {
  const method = String(config?.method || 'get').toLowerCase()
  if (method !== 'get') return false
  const url = String(config?.url || '')
  return SHARED_GET_ENDPOINT_HINTS.some((hint) => url.includes(hint))
}

const buildSharedGetCacheKey = (config) => {
  const url = String(config?.url || '')
  const params = config?.params ? JSON.stringify(config.params) : ''
  return `${url}::${params}`
}

const resolveAxiosAdapter = (adapterCandidate) => {
  if (typeof adapterCandidate === 'function') return adapterCandidate
  if (typeof axios.getAdapter === 'function') {
    try {
      return axios.getAdapter(adapterCandidate || axios.defaults.adapter)
    } catch (error) {
      console.warn('Unable to resolve axios adapter:', error?.message || error)
      return null
    }
  }
  return null
}

// CRITICAL: Enable credentials (cookies) for session management
axios.defaults.withCredentials = true
console.log('🍪 Axios configured to send cookies with requests (withCredentials: true)')

// Cookie-first: strip any per-call Authorization and legacy storage (raw `axios.get` usage).
axios.interceptors.request.use(
  (config) => {
    if (isSharedGetCandidate(config)) {
      const key = buildSharedGetCacheKey(config)
      const now = Date.now()
      const existing = sharedGetCache.get(key)

      if (existing?.response && (now - existing.timestamp) < SHARED_GET_CACHE_TTL_MS) {
        config.adapter = () => Promise.resolve({
          data: existing.response.data,
          status: existing.response.status,
          statusText: existing.response.statusText,
          headers: existing.response.headers,
          config,
          request: null,
        })
        return config
      }

      if (existing?.promise) {
        config.adapter = () =>
          existing.promise.then((response) => ({
            data: response.data,
            status: response.status,
            statusText: response.statusText,
            headers: response.headers,
            config,
            request: null,
          }))
        return config
      }

      const defaultAdapter = resolveAxiosAdapter(config.adapter || axios.defaults.adapter)
      if (!defaultAdapter) {
        // Fallback: do not dedupe this request if adapter resolution failed.
        return config
      }
      const networkPromise = Promise.resolve().then(() => defaultAdapter(config))
      sharedGetCache.set(key, {
        timestamp: now,
        promise: networkPromise,
        response: null,
      })
      config.__sharedGetCacheKey = key
      config.adapter = () => networkPromise
    }

    clearLegacyClientJwtKeys()
    try {
      if (config.headers) {
        delete config.headers.Authorization
        if (config.headers.common) delete config.headers.common.Authorization
      }
    } catch {
      /* ignore */
    }
    return config
  },
  (error) => Promise.reject(error)
)
console.log('✅ Global axios: HttpOnly cookies only; no Bearer from storage')

axios.interceptors.response.use(
  (response) => {
    const config = response?.config || {}
    if (isSharedGetCandidate(config)) {
      const key = config.__sharedGetCacheKey || buildSharedGetCacheKey(config)
      sharedGetCache.set(key, {
        timestamp: Date.now(),
        promise: null,
        response: {
          data: response.data,
          status: response.status,
          statusText: response.statusText,
          headers: response.headers,
        },
      })
    }
    return response
  },
  (error) => {
    const config = error?.config || {}
    if (isSharedGetCandidate(config)) {
      const key = config.__sharedGetCacheKey || buildSharedGetCacheKey(config)
      sharedGetCache.delete(key)
    }
    return Promise.reject(error)
  }
)

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
const pinia = createPinia()
app.config.performance = true
app.config.warnHandler = () => null

// Compatibility shim for legacy typo calls observed in some Options API components.
// If a component accidentally calls `this.initializedFramework()`, delegate to
// `this.initializeFramework()` when present instead of throwing.
app.mixin({
  methods: {
    async initializedFramework(...args) {
      if (typeof this.initializeFramework === 'function') {
        return this.initializeFramework(...args)
      }
      return true
    },
  },
})

app.use(router)
app.use(store)
app.use(pinia)
app.use(ElementPlus)
app.use(vuetify)
app.use(Popup)

// Make router and store available globally for AccessUtils
window.router = router
window.store = store
window.pinia = pinia

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

// Wait for initial navigation; always mount so a stuck guard does not leave a blank document
router.isReady().then(() => {
  app.mount('#app')
}).catch((e) => {
  console.error('Router isReady failed, mounting anyway:', e)
  app.mount('#app')
})

// -----------------------------------------------------------------------------
// Global form draft persistence (route-scoped)
// Keeps form field values when user navigates away and comes back.
// -----------------------------------------------------------------------------
const FORM_DRAFTS_STORAGE_KEY = 'grc_form_drafts_v1'
let formDraftsSaveTimer = null

const loadFormDrafts = () => {
  try {
    const raw = sessionStorage.getItem(FORM_DRAFTS_STORAGE_KEY)
    if (!raw) return {}
    const parsed = JSON.parse(raw)
    return parsed && typeof parsed === 'object' ? parsed : {}
  } catch {
    return {}
  }
}

const persistFormDrafts = (drafts) => {
  try {
    sessionStorage.setItem(FORM_DRAFTS_STORAGE_KEY, JSON.stringify(drafts || {}))
  } catch {
    // ignore storage failures
  }
}

const getCurrentRouteDraftKey = () => {
  const routePath = router.currentRoute?.value?.path || window.location.pathname
  return String(routePath || '/')
}

const isPersistableField = (el) => {
  if (!el || !el.tagName) return false
  const tag = String(el.tagName).toLowerCase()
  if (!['input', 'textarea', 'select'].includes(tag)) return false
  if (el.disabled || el.readOnly) return false

  if (tag === 'input') {
    const type = String(el.type || '').toLowerCase()
    if (['password', 'file', 'hidden', 'submit', 'button', 'image', 'reset'].includes(type)) {
      return false
    }
  }
  return true
}

const getElementPersistKey = (el) => {
  if (!el) return null
  const name = el.getAttribute('name')
  const id = el.getAttribute('id')
  const persistKey = el.getAttribute('data-persist-key')
  const placeholder = el.getAttribute('placeholder')
  const ariaLabel = el.getAttribute('aria-label')
  const tag = String(el.tagName || '').toLowerCase()
  const type = String(el.type || '').toLowerCase()
  return persistKey || name || id || `${tag}:${type}:${placeholder || ariaLabel || ''}`
}

const readElementValue = (el) => {
  const tag = String(el.tagName || '').toLowerCase()
  const type = String(el.type || '').toLowerCase()
  if (tag === 'input' && ['checkbox', 'radio'].includes(type)) {
    return !!el.checked
  }
  return el.value
}

const writeElementValue = (el, value) => {
  const tag = String(el.tagName || '').toLowerCase()
  const type = String(el.type || '').toLowerCase()
  if (tag === 'input' && ['checkbox', 'radio'].includes(type)) {
    el.checked = !!value
  } else {
    el.value = value ?? ''
  }
  el.dispatchEvent(new Event('input', { bubbles: true }))
  el.dispatchEvent(new Event('change', { bubbles: true }))
}

const collectRouteDraft = () => {
  const fields = Array.from(document.querySelectorAll('input, textarea, select'))
  const draft = {}

  fields.forEach((el) => {
    if (!isPersistableField(el)) return
    const key = getElementPersistKey(el)
    if (!key) return
    draft[key] = readElementValue(el)
  })

  return draft
}

const saveCurrentRouteDraft = () => {
  const drafts = loadFormDrafts()
  drafts[getCurrentRouteDraftKey()] = collectRouteDraft()
  persistFormDrafts(drafts)
}

const saveCurrentRouteDraftDebounced = () => {
  if (formDraftsSaveTimer) clearTimeout(formDraftsSaveTimer)
  formDraftsSaveTimer = setTimeout(saveCurrentRouteDraft, 250)
}

const restoreCurrentRouteDraft = () => {
  const drafts = loadFormDrafts()
  const routeDraft = drafts[getCurrentRouteDraftKey()]
  if (!routeDraft || typeof routeDraft !== 'object') return

  const fields = Array.from(document.querySelectorAll('input, textarea, select'))
  fields.forEach((el) => {
    if (!isPersistableField(el)) return
    const key = getElementPersistKey(el)
    if (!key || !(key in routeDraft)) return
    writeElementValue(el, routeDraft[key])
  })
}

// Save while user types/selects across all forms
document.addEventListener('input', saveCurrentRouteDraftDebounced, true)
document.addEventListener('change', saveCurrentRouteDraftDebounced, true)

// Save before route switch, then restore after navigation renders
router.beforeEach(() => {
  saveCurrentRouteDraft()
  return true
})

router.afterEach(() => {
  setTimeout(() => {
    restoreCurrentRouteDraft()
  }, 0)
})

