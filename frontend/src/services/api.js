/**
 * API Service
 *
 * Axios instance configured with authentication support.
 * Supports both Clerk auth and dev mode bypass.
 */
import axios from 'axios'
import { getSessionToken, isSignedIn, getAuthInstance } from './clerkClient'

// Check if we're in dev mode (no Clerk key provided)
const isDevMode = !import.meta.env.VITE_CLERK_PUBLISHABLE_KEY

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:5001/api',
  headers: {
    'Content-Type': 'application/json'
  }
})

// Add auth token to requests
api.interceptors.request.use(async (config) => {
  if (isDevMode) {
    // In dev mode, no auth needed (backend has DEV_AUTH_BYPASS=true)
    return config
  }

  try {
    // Wait for auth to be available (set by App.vue)
    const auth = getAuthInstance()

    if (!auth) {
      // Auth not initialized yet, wait a bit
      await new Promise((resolve) => {
        const timeout = setTimeout(() => {
          console.warn('[API] Timeout waiting for auth instance')
          resolve()
        }, 5000)

        const checkInterval = setInterval(() => {
          if (getAuthInstance()) {
            clearInterval(checkInterval)
            clearTimeout(timeout)
            resolve()
          }
        }, 50)
      })
    }

    // Get the session token
    const token = await getSessionToken()

    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    } else {
      console.warn('[API] No auth token available - user may not be signed in')
    }
  } catch (error) {
    console.warn('[API] Auth not available, proceeding without token', error)
  }

  return config
})

// Handle errors
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401 && !isDevMode) {
      // Check if we're already on an auth page
      const currentPath = window.location.pathname
      if (currentPath === '/sign-in' || currentPath === '/sign-up') {
        // Already on auth page, don't redirect
        return Promise.reject(error)
      }

      // Check if user is actually signed out or if it's just a timing issue
      if (isSignedIn()) {
        console.warn('[API] Got 401 but user is signed in - may be a timing issue or token expired')
        // Don't redirect - the component can handle the error
        return Promise.reject(error)
      }

      // User is actually not signed in - redirect to sign-in
      console.log('[API] User not signed in, redirecting to sign-in')
      window.location.href = '/sign-in'
    }
    return Promise.reject(error)
  }
)

export default api

// Export dev mode flag for components
export const devMode = isDevMode

// API helper functions
export const nicheApi = {
  list: () => api.get('/niches'),
  get: (slug) => api.get(`/niches/${slug}`),
  create: (data) => api.post('/niches', data),
  update: (slug, data) => api.patch(`/niches/${slug}`, data),
  delete: (slug) => api.delete(`/niches/${slug}`),
  stats: (slug) => api.get(`/niches/${slug}/stats`),
  collect: (slug, data) => api.post(`/niches/${slug}/collect`, data)
}

export const adApi = {
  search: (slug, params) => api.get(`/niches/${slug}/ads/search`, { params }),
  get: (slug, adId) => api.get(`/niches/${slug}/ads/${adId}`),
  related: (slug, adId) => api.get(`/niches/${slug}/ads/${adId}/related`)
}

export const savedApi = {
  list: (slug, params) => api.get(`/niches/${slug}/saved`, { params }),
  save: (slug, adId, data) => api.post(`/niches/${slug}/ads/${adId}/save`, data),
  unsave: (slug, adId) => api.delete(`/niches/${slug}/ads/${adId}/save`),
  update: (slug, adId, data) => api.patch(`/niches/${slug}/ads/${adId}/save`, data)
}

export const authApi = {
  me: () => api.get('/auth/me'),
  health: () => api.get('/health')
}
