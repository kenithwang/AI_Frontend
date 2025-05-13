/**
 * File: AI_Frontend/frontend_vue/src/main.js
 * Purpose: Entry point for the Vue.js application.
 *          Initializes the Vue app, imports global styles, plugins (like Vue Router, Pinia, Element Plus), and mounts the root App.vue component.
 * Interactions:
 *  - Imports App.vue as the root component.
 *  - Imports and registers Vue Router (if used).
 *  - Imports and registers Pinia (if used for state management).
 *  - Imports and registers Element Plus UI library.
 *  - Mounts the Vue application to the #app element in public/index.html.
 */

import { createApp } from 'vue'
import App from './App.vue'
// import router from './router' // If using Vue Router
// import store from './store'  // If using Vuex/Pinia
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
// import axios from 'axios'

const app = createApp(App)

// app.use(router) // If using Vue Router
// app.use(store)  // If using Vuex/Pinia
app.use(ElementPlus)

// // Configure Axios globally (optional)
// app.config.globalProperties.$axios = axios.create({
//   baseURL: process.env.VUE_APP_API_BASE_URL || 'http://localhost:8000/api'
// });

app.mount('#app') 