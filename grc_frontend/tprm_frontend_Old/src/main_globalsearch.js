import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import { VueQueryPlugin } from '@tanstack/vue-query'

// Vuetify
import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import '@mdi/font/css/materialdesignicons.css'

// App
import App from './App_globalsearch.vue'

// Routes
import GlobalSearch from './pages/GlobalSearch_TPRM.vue'

// Create router
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/search' },
    { path: '/search', name: 'search', component: GlobalSearch },
    { path: '/dashboard', redirect: '/search' } // Redirect old dashboard route to search
  ]
})

// Create Vuetify
const vuetify = createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: 'light'
  }
})

// Create app
const app = createApp(App)

// Use plugins
app.use(createPinia())
app.use(router)
app.use(vuetify)
app.use(VueQueryPlugin)

// Mount app
app.mount('#app')
