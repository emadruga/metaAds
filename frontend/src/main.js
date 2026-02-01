/**
 * MetAds Frontend - Entry Point
 *
 * Initializes Vue app with:
 * - Pinia (state management)
 * - Vue Router
 * - Clerk (authentication)
 */
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { clerkPlugin } from '@clerk/vue'
import App from './App.vue'
import router from './router'

// Import global styles
import './assets/styles/base.scss'

const app = createApp(App)

// State management
app.use(createPinia())

// Routing
app.use(router)

// Clerk authentication
app.use(clerkPlugin, {
  publishableKey: import.meta.env.VITE_CLERK_PUBLISHABLE_KEY
})

app.mount('#app')
