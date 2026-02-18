<template>
  <div class="saved-view">
    <div class="saved-header">
      <div class="header-content">
        <h2>Saved Ads</h2>
        <p class="subtitle">Your saved ads and notes for this niche</p>
      </div>

      <!-- Tags filter -->
      <div class="tags-filter" v-if="adsStore.savedTags.length > 0">
        <span class="filter-label">Filter by tag:</span>
        <button
          class="tag-btn"
          :class="{ active: !selectedTag }"
          @click="selectedTag = null"
        >
          All
        </button>
        <button
          v-for="tag in adsStore.savedTags"
          :key="tag"
          class="tag-btn"
          :class="{ active: selectedTag === tag }"
          @click="selectedTag = tag"
        >
          {{ tag }}
        </button>
      </div>
    </div>

    <div class="saved-content">
      <AdGrid
        :ads="filteredAds"
        :loading="adsStore.savedLoading"
        :selected-ad-id="adsStore.selectedAd?.id"
        :pagination="adsStore.savedPagination"
        empty-message="No saved ads yet. Save ads from the Search tab to build your collection."
        @select="handleSelectAd"
        @toggle-save="handleToggleSave"
        @page-change="handlePageChange"
      />
    </div>

    <!-- Detail sidebar (optional) -->
    <div class="saved-detail" v-if="adsStore.selectedAd">
      <AdDetailPanel
        :ad="adsStore.selectedAdDetail || adsStore.selectedAd"
        :loading="adsStore.detailLoading"
        @toggle-save="handleToggleSave"
        @update-notes="handleUpdateNotes"
        @view-related="handleViewRelated"
      />
    </div>
  </div>
</template>

<script setup>
  import { ref, computed, onMounted, watch } from 'vue'
  import { useRoute } from 'vue-router'
  import { useAdsStore } from '@/stores/ads'
  import AdGrid from '@/components/AdGrid.vue'
  import AdDetailPanel from '@/components/AdDetailPanel.vue'

  const route = useRoute()
  const adsStore = useAdsStore()

  const selectedTag = ref(null)

  const nicheSlug = () => route.params.nicheSlug

  const filteredAds = computed(() => {
    if (!selectedTag.value) {
      return adsStore.savedAds
    }
    return adsStore.savedAds.filter((ad) => ad.saved?.tags?.includes(selectedTag.value))
  })

  async function handleSelectAd(ad) {
    adsStore.selectAd(ad)
    await adsStore.fetchAdDetail(nicheSlug(), ad.id)
  }

  async function handleToggleSave(ad) {
    await adsStore.toggleSave(nicheSlug(), ad)
    // Refresh saved ads list
    await adsStore.fetchSavedAds(nicheSlug())
  }

  async function handleUpdateNotes({ notes, tags }) {
    if (adsStore.selectedAd) {
      await adsStore.updateSavedAd(nicheSlug(), adsStore.selectedAd.id, { notes, tags })
      // Refresh saved ads list to update tags
      await adsStore.fetchSavedAds(nicheSlug())
    }
  }

  function handleViewRelated(ad) {
    adsStore.fetchRelatedAds(nicheSlug(), ad.id)
  }

  async function handlePageChange(page) {
    await adsStore.fetchSavedAds(nicheSlug(), { page, tag: selectedTag.value })
  }

  onMounted(() => {
    // Clear selected ad when mounting (prevents leaking from other niches/tabs)
    adsStore.clearSelectedAd()
    adsStore.fetchSavedAds(nicheSlug())
  })

  // Re-fetch when niche changes
  watch(
    () => route.params.nicheSlug,
    (newSlug) => {
      if (newSlug) {
        adsStore.clearSelectedAd()
        adsStore.fetchSavedAds(newSlug)
      }
    }
  )

  // Re-fetch when tag filter changes
  watch(selectedTag, (tag) => {
    adsStore.fetchSavedAds(nicheSlug(), { tag })
  })
</script>

<style lang="scss" scoped>
  .saved-view {
    display: grid;
    grid-template-columns: 1fr 400px;
    gap: var(--spacing-4);
    min-height: calc(100vh - 160px);

    @media (max-width: 1024px) {
      grid-template-columns: 1fr;

      .saved-detail {
        display: none;
      }
    }
  }

  .saved-header {
    grid-column: 1 / -1;
    background-color: var(--color-bg-primary);
    border-radius: var(--radius-lg);
    padding: var(--spacing-4);
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: var(--spacing-4);

    h2 {
      font-size: var(--font-size-xl);
      font-weight: 600;
      margin: 0;
    }

    .subtitle {
      color: var(--color-text-secondary);
      margin: var(--spacing-1) 0 0 0;
    }
  }

  .tags-filter {
    display: flex;
    align-items: center;
    gap: var(--spacing-2);
    flex-wrap: wrap;

    .filter-label {
      font-size: var(--font-size-sm);
      color: var(--color-text-secondary);
    }
  }

  .tag-btn {
    padding: var(--spacing-1) var(--spacing-3);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-full);
    background-color: var(--color-bg-primary);
    font-size: var(--font-size-sm);
    cursor: pointer;
    transition: all var(--transition-fast);

    &:hover {
      background-color: var(--color-gray-100);
    }

    &.active {
      background-color: var(--color-primary-500);
      border-color: var(--color-primary-500);
      color: white;
    }
  }

  .saved-content {
    background-color: var(--color-bg-primary);
    border-radius: var(--radius-lg);
    padding: var(--spacing-4);
    overflow-y: auto;
  }

  .saved-detail {
    background-color: var(--color-bg-primary);
    border-radius: var(--radius-lg);
    padding: var(--spacing-4);
    overflow-y: auto;
    position: sticky;
    top: var(--spacing-4);
    max-height: calc(100vh - 200px);
  }
</style>
