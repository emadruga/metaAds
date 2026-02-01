/**
 * Auth Store
 *
 * Manages user authentication state.
 */
import { defineStore } from 'pinia'
import { useAuth, useUser } from '@clerk/vue'
import { authApi } from '@/services/api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    loading: true,
    error: null
  }),

  getters: {
    isAuthenticated: (state) => !!state.user,
    userName: (state) => {
      if (!state.user) return ''
      return state.user.first_name || state.user.email?.split('@')[0] || 'User'
    },
    userInitials: (state) => {
      if (!state.user) return ''
      const first = state.user.first_name?.[0] || state.user.email?.[0] || 'U'
      const last = state.user.last_name?.[0] || ''
      return (first + last).toUpperCase()
    }
  },

  actions: {
    async fetchUser() {
      this.loading = true
      this.error = null

      try {
        const { isSignedIn } = useAuth()

        if (!isSignedIn.value) {
          this.user = null
          return
        }

        const response = await authApi.me()
        this.user = response.data.data
      } catch (error) {
        console.error('Failed to fetch user:', error)
        this.error = error.message
        this.user = null
      } finally {
        this.loading = false
      }
    },

    clearUser() {
      this.user = null
      this.error = null
    }
  }
})
