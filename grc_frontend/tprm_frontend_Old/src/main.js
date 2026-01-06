import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './style.css'
import './styles/vendor.css'
import './assets/styles/styles.css'  // RFP styles
// Vue Query for global search
import { VueQueryPlugin } from '@tanstack/vue-query'
// Element Plus
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
// Auth debugging utility
import authDebug from './utils/authDebug.js'

// Vuetify
import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import '@mdi/font/css/materialdesignicons.css'

// Vuex for contract pages
import { createStore } from 'vuex'
import authModule from './store/modules/auth'

const contractStore = createStore({
  modules: {
    auth: authModule
  },
  
  state: {
    loading: false,
    loadingMessage: ''
  },
  
  getters: {
    isLoading: state => state.loading,
    loadingMessage: state => state.loadingMessage
  },
  
  mutations: {
    SET_LOADING(state, { loading, message = '' }) {
      state.loading = loading
      state.loadingMessage = message
    },
    
    CLEAR_AUTH(state) {
      // Global auth clearing for emergency purposes
      localStorage.removeItem('session_token')
    }
  },
  
  actions: {
    setLoading({ commit }, payload) {
      commit('SET_LOADING', payload)
    }
  }
})

const vuetify = createVuetify({
  components,
  directives,
})

const pinia = createPinia()

const app = createApp(App)

// Use Pinia first
app.use(pinia)

// Use other plugins
app.use(contractStore)
app.use(router)
app.use(vuetify)
app.use(ElementPlus)

// Register all Element Plus icons
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// Global error handler
app.config.errorHandler = (err, vm, info) => {
  console.error('Global error:', err, info)
}

// Global warning handler
app.config.warnHandler = (msg, vm, trace) => {
  console.warn('Global warning:', msg, trace)
}

app.config.globalProperties.$initializeStores = async () => {
  try {
    const { useAuthStore } = await import('./stores/auth')
    const authStore = useAuthStore()
    authStore.initializeAuth()
  } catch (error) {
    console.error('Failed to initialize stores:', error)
  }
}

// Add router guard to initialize stores
router.beforeEach(async (to, from, next) => {
  try {
    const { useAuthStore } = await import('./stores/auth')
    const authStore = useAuthStore()
    
    // Initialize auth if not already done
    if (!authStore.isAuthenticated) {
      authStore.initializeAuth()
    }
    
    // Initialize RFP stores for RFP routes
    if (to.path.startsWith('/rfp') || to.path.startsWith('/vendor-portal') || to.path.startsWith('/submit')) {
      try {
        const { useRFPStore, useVendorStore, useUserStore } = await import('./store/index_rfp')
        // RFP stores will be available globally
      } catch (error) {
        console.warn('RFP stores not available:', error)
      }
    }
  } catch (error) {
    console.error('Router guard error:', error)
  }
  next()
})

app.mount('#app')
