/**
 * Niches Store
 *
 * Manages niche list and current niche state.
 */
import { defineStore } from 'pinia'
import { nicheApi } from '@/services/api'

export const useNichesStore = defineStore('niches', {
  state: () => ({
    niches: [],
    currentNiche: null,
    loading: false,
    error: null,
    showCollectModal: false
  }),

  getters: {
    nicheCount: (state) => state.niches.length,
    getNicheBySlug: (state) => (slug) => {
      return state.niches.find(n => n.slug === slug)
    }
  },

  actions: {
    async fetchNiches() {
      this.loading = true
      this.error = null

      try {
        const response = await nicheApi.list()
        this.niches = response.data.data
      } catch (error) {
        console.error('Failed to fetch niches:', error)
        this.error = error.message
      } finally {
        this.loading = false
      }
    },

    async fetchNiche(slug) {
      this.loading = true
      this.error = null

      try {
        const response = await nicheApi.get(slug)
        this.currentNiche = response.data.data

        // Update in niches array too
        const index = this.niches.findIndex(n => n.slug === slug)
        if (index !== -1) {
          this.niches[index] = this.currentNiche
        }
      } catch (error) {
        console.error('Failed to fetch niche:', error)
        this.error = error.message
        this.currentNiche = null
      } finally {
        this.loading = false
      }
    },

    async createNiche(data) {
      this.loading = true
      this.error = null

      try {
        const response = await nicheApi.create(data)
        const newNiche = response.data.data
        this.niches.unshift(newNiche)
        return newNiche
      } catch (error) {
        console.error('Failed to create niche:', error)
        this.error = error.response?.data?.error || error.message
        throw error
      } finally {
        this.loading = false
      }
    },

    async updateNiche(slug, data) {
      this.loading = true
      this.error = null

      try {
        const response = await nicheApi.update(slug, data)
        const updatedNiche = response.data.data

        // Update in niches array
        const index = this.niches.findIndex(n => n.slug === slug)
        if (index !== -1) {
          this.niches[index] = updatedNiche
        }

        // Update current niche if it's the same
        if (this.currentNiche?.slug === slug) {
          this.currentNiche = updatedNiche
        }

        return updatedNiche
      } catch (error) {
        console.error('Failed to update niche:', error)
        this.error = error.response?.data?.error || error.message
        throw error
      } finally {
        this.loading = false
      }
    },

    async deleteNiche(slug) {
      this.loading = true
      this.error = null

      try {
        await nicheApi.delete(slug)

        // Remove from niches array
        this.niches = this.niches.filter(n => n.slug !== slug)

        // Clear current niche if it's the deleted one
        if (this.currentNiche?.slug === slug) {
          this.currentNiche = null
        }
      } catch (error) {
        console.error('Failed to delete niche:', error)
        this.error = error.response?.data?.error || error.message
        throw error
      } finally {
        this.loading = false
      }
    },

    async toggleAutoCollect(slug, enabled) {
      // Optimistic update — flip the flag in the store immediately
      const index = this.niches.findIndex(n => n.slug === slug)
      if (index !== -1) {
        this.niches[index] = { ...this.niches[index], auto_collect_enabled: enabled }
      }
      if (this.currentNiche?.slug === slug) {
        this.currentNiche = { ...this.currentNiche, auto_collect_enabled: enabled }
      }

      // Silent PATCH — no loading spinner
      try {
        const response = await nicheApi.update(slug, { auto_collect_enabled: enabled })
        const updated = response.data.data
        if (index !== -1) {
          this.niches[index] = updated
        }
        if (this.currentNiche?.slug === slug) {
          this.currentNiche = updated
        }
      } catch (error) {
        // Revert optimistic update on failure
        if (index !== -1) {
          this.niches[index] = { ...this.niches[index], auto_collect_enabled: !enabled }
        }
        if (this.currentNiche?.slug === slug) {
          this.currentNiche = { ...this.currentNiche, auto_collect_enabled: !enabled }
        }
        console.error('Failed to toggle auto-collect:', error)
        throw error
      }
    },

    setCurrentNiche(niche) {
      this.currentNiche = niche
    },

    clearCurrentNiche() {
      this.currentNiche = null
    },

    openCollectModal() {
      this.showCollectModal = true
    },

    closeCollectModal() {
      this.showCollectModal = false
    }
  }
})
