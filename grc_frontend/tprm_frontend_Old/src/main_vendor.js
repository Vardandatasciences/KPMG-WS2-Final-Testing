import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App_vendor.vue'
import router from './router/index_vendor.js'
import './assets/styles/vendor_variables.css'
import './assets/styles/vendor_global.css'
import './assets/styles/vendor_components.css'
// Element Plus (UI library used by the dashboard)
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

const vendor_app = createApp(App)

vendor_app.use(createPinia())
vendor_app.use(router)
vendor_app.use(ElementPlus)

vendor_app.mount('#vendor_app')
