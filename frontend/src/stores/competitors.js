import { defineStore } from 'pinia'
import { competitorApi } from '@/services/api'

export const useCompetitorsStore = defineStore('competitors', {
  state: () => ({
    competitors: [],
    loading: false,
    error: null,
    // Per-competitor ad data (keyed by page_id)
    adsCache: {},
    adsLoading: false,
    adsError: null,
  }),

  getters: {
    competitorByPageId: (state) => (pageId) =>
      state.competitors.find((c) => c.page_id === pageId) || null,
  },

  actions: {
    async fetchCompetitors() {
      this.loading = true
      this.error = null
      try {
        const response = await competitorApi.list()
        this.competitors = response.data.data || []
      } catch (e) {
        this.error = e.response?.data?.error || e.message
      } finally {
        this.loading = false
      }
    },

    async addCompetitor(pageData) {
      const response = await competitorApi.add(pageData)
      const competitor = response.data.data
      this.competitors.unshift(competitor)
      return competitor
    },

    async removeCompetitor(pageId) {
      await competitorApi.remove(pageId)
      this.competitors = this.competitors.filter((c) => c.page_id !== pageId)
      delete this.adsCache[pageId]
    },

    async fetchCompetitorAds(pageId, params = {}) {
      this.adsLoading = true
      this.adsError = null
      try {
        const response = await competitorApi.getAds(pageId, params)
        this.adsCache[pageId] = {
          ads: response.data.data || [],
          page_name: response.data.page_name,
          count: response.data.count,
          aggregates: response.data.aggregates || {},
          fetchedAt: new Date().toISOString(),
        }
        return this.adsCache[pageId]
      } catch (e) {
        this.adsError = e.response?.data?.error || e.message
        throw e
      } finally {
        this.adsLoading = false
      }
    },

    getAdsForPage(pageId) {
      return this.adsCache[pageId] || null
    },
  },
})
