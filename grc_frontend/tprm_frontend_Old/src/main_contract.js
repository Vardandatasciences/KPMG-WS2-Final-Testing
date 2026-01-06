import { createApp } from 'vue';
import { VueQueryPlugin } from '@tanstack/vue-query';
import App from './App_contract.vue';
import router from './router/index.js';
import store from './store/index_contract.js';
import './index.css';

const app = createApp(App);
app.use(store);
app.use(router);
app.use(VueQueryPlugin);
app.mount('#app');
