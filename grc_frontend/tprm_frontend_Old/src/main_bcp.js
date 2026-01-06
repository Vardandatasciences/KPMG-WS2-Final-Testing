// import { createApp } from 'vue'
// import App from './App.vue'
// import router from './router'
// import store from './store'
// import './styles/variables.css'
// import './styles/base.css'

// createApp(App).use(store).use(router).mount('#app')



import { createApp } from 'vue'
import App from './App.vue'
import router from './router/index_bcp.js'
import store from './store'
import './styles/variables.css'
import './styles/base.css'
import './styles/bcp-styles.css'

// Import PopupModal component for global registration
import PopupModal from './popup/PopupModal.vue'

const app = createApp(App)

// Register PopupModal globally for BCP module
app.component('PopupModal', PopupModal)

app.use(store).use(router).mount('#app')
