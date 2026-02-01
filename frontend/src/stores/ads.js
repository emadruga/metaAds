/**
 * Ads Store
 *
 * Manages ad search, saved ads, and ad details.
 */
import { defineStore } from 'pinia'
import { adApi, savedApi } from '@/services/api'

export const useAdsStore = defineStore('ads', {
  state: () => ({
    // Search results
    ads: [],
    pagination: null,
    filters: {
      q: '',
      is_active: '',
      platform: '',
      sort: 'days_active',
      order: 'desc'
    },

    // Selected ad
    selectedAd: null,
    selectedAdDetail: null,
    relatedAds: null,
    relatedAdsData: null,

    // Saved ads
    savedAds: [],
    savedPagination: null,
    savedTags: [],

    // Loading states
    loading: false,
    detailLoading: false,
    savedLoading: false,
    error: null
  }),

  getters: {
    hasAds: (state) => state.ads.length > 0,
    hasSavedAds: (state) => state.savedAds.length > 0,
    isAdSaved: (state) => (adId) => {
      const ad = state.ads.find((a) => a.id === adId)
      return ad?.is_saved || false
    }
  },

  actions: {
    async searchAds(nicheSlug, filters = {}) {
      this.loading = true
      this.error = null

      try {
        const params = { ...this.filters, ...filters }
        const response = await adApi.search(nicheSlug, params)

        this.ads = response.data.data
        this.pagination = response.data.pagination
        this.filters = params
      } catch (error) {
        console.error('Failed to search ads:', error)
        this.error = error.response?.data?.error || error.message
        this.ads = []
      } finally {
        this.loading = false
      }
    },

    async fetchAdDetail(nicheSlug, adId) {
      this.detailLoading = true
      this.error = null

      try {
        const response = await adApi.get(nicheSlug, adId)
        this.selectedAdDetail = response.data.data
        this.selectedAd = response.data.data

        // Also fetch related ads to show count
        this.fetchRelatedAds(nicheSlug, adId)
      } catch (error) {
        console.error('Failed to fetch ad detail:', error)
        this.error = error.response?.data?.error || error.message
        this.selectedAdDetail = null
      } finally {
        this.detailLoading = false
      }
    },

    async fetchRelatedAds(nicheSlug, adId) {
      try {
        const response = await adApi.related(nicheSlug, adId)
        this.relatedAds = response.data.data.related
        this.relatedAdsData = response.data.data
      } catch (error) {
        console.error('Failed to fetch related ads:', error)
        this.relatedAds = null
        this.relatedAdsData = null
      }
    },

    async fetchSavedAds(nicheSlug, params = {}) {
      this.savedLoading = true
      this.error = null

      try {
        const response = await savedApi.list(nicheSlug, params)
        this.savedAds = response.data.data
        this.savedPagination = response.data.pagination
        this.savedTags = response.data.tags || []
      } catch (error) {
        console.error('Failed to fetch saved ads:', error)
        this.error = error.response?.data?.error || error.message
        this.savedAds = []
      } finally {
        this.savedLoading = false
      }
    },

    async saveAd(nicheSlug, adId, data = {}) {
      try {
        const response = await savedApi.save(nicheSlug, adId, data)
        const updatedAd = response.data.data

        // Update in ads list
        this.updateAdInList(adId, { is_saved: true, saved: updatedAd.saved })

        // Update selected ad if it's the same
        if (this.selectedAd?.id === adId) {
          this.selectedAd = updatedAd
          this.selectedAdDetail = updatedAd
        }

        return updatedAd
      } catch (error) {
        console.error('Failed to save ad:', error)
        throw error
      }
    },

    async unsaveAd(nicheSlug, adId) {
      try {
        await savedApi.unsave(nicheSlug, adId)

        // Update in ads list
        this.updateAdInList(adId, { is_saved: false, saved: null })

        // Remove from saved ads list
        this.savedAds = this.savedAds.filter((a) => a.id !== adId)

        // Update selected ad if it's the same
        if (this.selectedAd?.id === adId) {
          this.selectedAd.is_saved = false
          this.selectedAd.saved = null
          if (this.selectedAdDetail) {
            this.selectedAdDetail.is_saved = false
            this.selectedAdDetail.saved = null
          }
        }
      } catch (error) {
        console.error('Failed to unsave ad:', error)
        throw error
      }
    },

    async updateSavedAd(nicheSlug, adId, data) {
      try {
        const response = await savedApi.update(nicheSlug, adId, data)
        const updatedAd = response.data.data

        // Update in saved ads list
        const index = this.savedAds.findIndex((a) => a.id === adId)
        if (index !== -1) {
          this.savedAds[index] = updatedAd
        }

        // Update selected ad if it's the same
        if (this.selectedAd?.id === adId) {
          this.selectedAd = updatedAd
          this.selectedAdDetail = updatedAd
        }

        return updatedAd
      } catch (error) {
        console.error('Failed to update saved ad:', error)
        throw error
      }
    },

    async toggleSave(nicheSlug, ad) {
      if (ad.is_saved) {
        await this.unsaveAd(nicheSlug, ad.id)
      } else {
        await this.saveAd(nicheSlug, ad.id)
      }
    },

    updateAdInList(adId, updates) {
      const index = this.ads.findIndex((a) => a.id === adId)
      if (index !== -1) {
        this.ads[index] = { ...this.ads[index], ...updates }
      }
    },

    selectAd(ad) {
      this.selectedAd = ad
    },

    clearSelectedAd() {
      this.selectedAd = null
      this.selectedAdDetail = null
      this.relatedAds = null
      this.relatedAdsData = null
    },

    setFilters(filters) {
      this.filters = { ...this.filters, ...filters }
    },

    clearFilters() {
      this.filters = {
        q: '',
        is_active: '',
        platform: '',
        sort: 'days_active',
        order: 'desc'
      }
    }
  }
})
