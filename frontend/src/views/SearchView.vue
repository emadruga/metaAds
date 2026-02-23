<template>
  <div class="search-view" :class="{ 'mobile-detail-open': showMobileDetail }">
    <!-- Filters Panel -->
    <div class="search-panel" :class="{ collapsed: filtersCollapsed }">
      <div class="panel-header">
        <h2>Filters</h2>
        <button
          class="collapse-btn"
          @click="filtersCollapsed = !filtersCollapsed"
          :title="filtersCollapsed ? 'Expand filters' : 'Collapse filters'"
        >
          {{ filtersCollapsed ? '▶' : '◀' }}
        </button>
      </div>
      <div v-show="!filtersCollapsed" class="panel-content">
        <SearchFilters
          :filters="adsStore.filters"
          @update:filters="adsStore.setFilters"
          @apply="handleSearch"
        />
      </div>
    </div>

    <!-- Results Panel - Desktop: Grid, Mobile: Carousel -->
    <div class="results-panel">
      <div class="results-header">
        <h2>Results</h2>
        <!-- View mode toggle (desktop only) -->
        <div class="view-toggle desktop-only">
          <button
            class="toggle-btn"
            :class="{ active: viewMode === 'cards' }"
            @click="viewMode = 'cards'"
            title="Card view"
          >
            ⊞
          </button>
          <button
            class="toggle-btn"
            :class="{ active: viewMode === 'table' }"
            @click="viewMode = 'table'"
            title="Table view"
          >
            ☰
          </button>
        </div>
        <span class="results-count" v-if="adsStore.pagination">
          {{ adsStore.pagination.total_ads }} ads found
        </span>
        <!-- Mobile filter toggle -->
        <button class="mobile-filter-btn" @click="showMobileFilters = true">
          🔍 Filters
        </button>
      </div>

      <!-- Desktop: Grid or Table view -->
      <div class="desktop-only">
        <AdGrid
          v-if="viewMode === 'cards'"
          :ads="adsStore.ads"
          :loading="adsStore.loading"
          :selected-ad-id="adsStore.selectedAd?.meta_ad_id"
          :pagination="adsStore.pagination"
          :show-collect-button="true"
          empty-message="No ads found. Try adjusting your search filters or run a collection."
          @select="handleSelectAd"
          @toggle-save="handleToggleSave"
          @page-change="handlePageChange"
          @collect="nichesStore.openCollectModal()"
        />
        <AdTable
          v-else
          :ads="adsStore.ads"
          :loading="adsStore.loading"
          :selected-ad-id="adsStore.selectedAd?.meta_ad_id"
          :pagination="adsStore.pagination"
          :show-collect-button="true"
          :sort-by="adsStore.filters.sort"
          :sort-order="adsStore.filters.order"
          empty-message="No ads found. Try adjusting your search filters or run a collection."
          @select="handleSelectAd"
          @toggle-save="handleToggleSave"
          @page-change="handlePageChange"
          @collect="nichesStore.openCollectModal()"
        />
      </div>

      <!-- Mobile: Carousel view -->
      <div class="mobile-only">
        <AdCarousel
          :ads="adsStore.ads"
          :loading="adsStore.loading"
          :selected-ad-id="adsStore.selectedAd?.meta_ad_id"
          :show-collect-button="true"
          empty-message="No ads found. Tap 'Filters' to adjust or collect new ads."
          @select="handleMobileSelectAd"
          @toggle-save="handleToggleSave"
          @collect="nichesStore.openCollectModal()"
        />
      </div>
    </div>

    <!-- Detail Panel - Desktop -->
    <div class="detail-panel desktop-only" :class="{ collapsed: detailCollapsed }">
      <div class="panel-header">
        <h2>Ad Detail</h2>
        <button
          class="collapse-btn"
          @click="detailCollapsed = !detailCollapsed"
          :title="detailCollapsed ? 'Expand detail' : 'Collapse detail'"
        >
          {{ detailCollapsed ? '◀' : '▶' }}
        </button>
      </div>
      <div v-show="!detailCollapsed" class="panel-content">
        <AdDetailPanel
          :ad="adsStore.selectedAdDetail || adsStore.selectedAd"
          :loading="adsStore.detailLoading"
          :related-count="adsStore.relatedAds?.length || 0"
          :niche-slug="nicheSlug()"
          @toggle-save="handleToggleSave"
          @update-notes="handleUpdateNotes"
          @view-related="handleViewRelated"
        />
      </div>
    </div>

    <!-- Mobile Detail Overlay -->
    <div class="mobile-detail-overlay mobile-only" v-if="showMobileDetail">
      <div class="mobile-detail-header">
        <button class="back-btn" @click="closeMobileDetail">← Back</button>
        <h2>Ad Detail</h2>
      </div>
      <div class="mobile-detail-content">
        <AdDetailPanel
          :ad="adsStore.selectedAdDetail || adsStore.selectedAd"
          :loading="adsStore.detailLoading"
          :related-count="adsStore.relatedAds?.length || 0"
          :niche-slug="nicheSlug()"
          @toggle-save="handleToggleSave"
          @update-notes="handleUpdateNotes"
          @view-related="handleViewRelated"
        />
      </div>
    </div>

    <!-- Mobile Filters Overlay -->
    <div class="mobile-filters-overlay mobile-only" v-if="showMobileFilters">
      <div class="mobile-filters-header">
        <h2>Filters</h2>
        <button class="close-btn" @click="showMobileFilters = false">✕</button>
      </div>
      <div class="mobile-filters-content">
        <SearchFilters
          :filters="adsStore.filters"
          @update:filters="adsStore.setFilters"
          @apply="handleMobileApplyFilters"
        />
      </div>
    </div>

    <!-- Related Ads Modal -->
    <RelatedAdsModal
      v-if="showRelatedModal"
      :related="relatedAdsData.related || []"
      :loading="false"
      :insights="relatedAdsData.insights"
      :page-name="adsStore.selectedAd?.page_name"
      @close="showRelatedModal = false"
      @select-ad="handleSelectRelatedAd"
    />
  </div>
</template>

<script setup>
  import { ref, onMounted, watch, computed } from 'vue'
  import { useRoute } from 'vue-router'
  import { useAdsStore } from '@/stores/ads'
  import { useNichesStore } from '@/stores/niches'
  import SearchFilters from '@/components/SearchFilters.vue'
  import AdGrid from '@/components/AdGrid.vue'
  import AdTable from '@/components/AdTable.vue'
  import AdCarousel from '@/components/AdCarousel.vue'
  import AdDetailPanel from '@/components/AdDetailPanel.vue'
  import RelatedAdsModal from '@/components/RelatedAdsModal.vue'

  const route = useRoute()
  const adsStore = useAdsStore()
  const nichesStore = useNichesStore()

  const showMobileDetail = ref(false)
  const showMobileFilters = ref(false)
  const showRelatedModal = ref(false)
  const viewMode = ref('table') // 'cards' or 'table'
  const filtersCollapsed = ref(false)
  const detailCollapsed = ref(false)

  const relatedAdsData = computed(() => adsStore.relatedAdsData || {})

  const nicheSlug = () => route.params.nicheSlug

  async function handleSearch(filters) {
    // Clear selected ad when starting a new search
    adsStore.clearSelectedAd()
    await adsStore.searchAds(nicheSlug(), filters)
  }

  async function handleSelectAd(ad) {
    adsStore.selectAd(ad)
    await adsStore.fetchAdDetail(nicheSlug(), ad.meta_ad_id)
    // Auto-expand detail panel when ad is selected
    detailCollapsed.value = false
  }

  // Mobile: select ad and open detail overlay
  async function handleMobileSelectAd(ad) {
    await handleSelectAd(ad)
    showMobileDetail.value = true
  }

  function closeMobileDetail() {
    showMobileDetail.value = false
  }

  // Mobile: apply filters and close overlay
  async function handleMobileApplyFilters(filters) {
    await handleSearch(filters)
    showMobileFilters.value = false
  }

  async function handleToggleSave(ad) {
    await adsStore.toggleSave(nicheSlug(), ad)
  }

  async function handleUpdateNotes({ notes, tags }) {
    if (adsStore.selectedAd) {
      await adsStore.updateSavedAd(nicheSlug(), adsStore.selectedAd.meta_ad_id, { notes, tags })
    }
  }

  async function handleViewRelated(ad) {
    await adsStore.fetchRelatedAds(nicheSlug(), ad.meta_ad_id)
    showRelatedModal.value = true
  }

  function handleSelectRelatedAd(ad) {
    adsStore.selectAd(ad)
    adsStore.fetchAdDetail(nicheSlug(), ad.id)
    showRelatedModal.value = false
  }

  async function handlePageChange(page) {
    await adsStore.searchAds(nicheSlug(), { ...adsStore.filters, page })
  }

  onMounted(() => {
    // Clear selected ad when mounting (prevents leaking from other niches/tabs)
    adsStore.clearSelectedAd()
    // Initial search
    adsStore.searchAds(nicheSlug())
  })

  // Re-search when niche changes
  watch(
    () => route.params.nicheSlug,
    (newSlug) => {
      if (newSlug) {
        adsStore.clearSelectedAd()
        adsStore.searchAds(newSlug)
        showMobileDetail.value = false
      }
    }
  )
</script>

<style lang="scss" scoped>
  .search-view {
    display: grid;
    grid-template-columns: 280px 1fr 400px;
    gap: var(--spacing-4);
    height: calc(100vh - 160px);
    position: relative;
    transition: grid-template-columns var(--transition-base);

    // Both filters and detail expanded (default)
    // 280px 1fr 400px

    // Only filters collapsed
    &:has(.search-panel.collapsed):not(:has(.detail-panel.collapsed)) {
      grid-template-columns: 60px 1fr 400px;

      @media (max-width: 1200px) {
        grid-template-columns: 60px 1fr;
      }
    }

    // Only detail collapsed
    &:has(.detail-panel.collapsed):not(:has(.search-panel.collapsed)) {
      grid-template-columns: 280px 1fr 60px;

      @media (max-width: 1200px) {
        grid-template-columns: 250px 1fr;
      }
    }

    // Both filters and detail collapsed
    &:has(.search-panel.collapsed):has(.detail-panel.collapsed) {
      grid-template-columns: 60px 1fr 60px;

      @media (max-width: 1200px) {
        grid-template-columns: 60px 1fr;
      }
    }

    @media (max-width: 1200px) {
      grid-template-columns: 250px 1fr;
    }

    @media (max-width: 768px) {
      grid-template-columns: 1fr;
      height: calc(100vh - 120px);
    }
  }

  /* Desktop/Mobile visibility */
  .desktop-only {
    display: block;

    @media (max-width: 768px) {
      display: none;
    }
  }

  .mobile-only {
    display: none;

    @media (max-width: 768px) {
      display: block;
    }
  }

  .search-panel,
  .results-panel,
  .detail-panel {
    background-color: var(--color-bg-primary);
    border-radius: var(--radius-lg);
    padding: var(--spacing-4);
    overflow-y: auto;

    h2 {
      font-size: var(--font-size-lg);
      font-weight: 600;
      margin: 0 0 var(--spacing-4) 0;
      padding-bottom: var(--spacing-3);
      border-bottom: 1px solid var(--color-border);
    }
  }

  .search-panel {
    transition: all var(--transition-base);
    position: relative;

    &.collapsed {
      padding: var(--spacing-3);
      overflow: visible;

      .panel-header {
        flex-direction: column;
        align-items: center;
        gap: var(--spacing-2);

        h2 {
          writing-mode: vertical-rl;
          transform: rotate(180deg);
          margin: 0;
          padding: 0;
          border: 0;
          white-space: nowrap;
        }
      }

      .collapse-btn {
        margin: 0;
      }
    }

    @media (max-width: 768px) {
      display: none;
    }
  }

  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-4);
    padding-bottom: var(--spacing-3);
    border-bottom: 1px solid var(--color-border);
    transition: all var(--transition-base);

    h2 {
      margin: 0;
      padding: 0;
      border: 0;
      font-size: var(--font-size-lg);
      font-weight: 600;
      transition: all var(--transition-base);
    }
  }

  .collapse-btn {
    padding: var(--spacing-1) var(--spacing-2);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    background-color: var(--color-bg-primary);
    color: var(--color-text-secondary);
    font-size: var(--font-size-sm);
    cursor: pointer;
    transition: all var(--transition-fast);

    &:hover {
      background-color: var(--color-gray-100);
      border-color: var(--color-primary-500);
      color: var(--color-primary-600);
    }
  }

  .panel-content {
    animation: fadeIn 0.2s ease-in;
  }

  @keyframes fadeIn {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }

  .detail-panel {
    transition: all var(--transition-base);
    position: relative;

    &.collapsed {
      padding: var(--spacing-3);
      overflow: visible;

      .panel-header {
        flex-direction: column;
        align-items: center;
        gap: var(--spacing-2);

        h2 {
          writing-mode: vertical-rl;
          transform: rotate(180deg);
          margin: 0;
          padding: 0;
          border: 0;
          white-space: nowrap;
        }
      }

      .collapse-btn {
        margin: 0;
      }
    }

    @media (max-width: 1200px) {
      display: none;
    }
  }

  .results-panel {
    @media (max-width: 768px) {
      padding: 0;
      border-radius: 0;

      .mobile-only {
        height: 100%;
      }
    }
  }

  .results-header {
    display: flex;
    align-items: center;
    gap: var(--spacing-3);
    margin-bottom: var(--spacing-4);
    padding-bottom: var(--spacing-3);
    border-bottom: 1px solid var(--color-border);

    h2 {
      margin: 0;
      padding: 0;
      border: 0;
    }

    @media (max-width: 768px) {
      padding: var(--spacing-3) var(--spacing-4);
      margin-bottom: 0;
      background-color: var(--color-bg-primary);
    }
  }

  .view-toggle {
    display: flex;
    gap: 0;
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    overflow: hidden;

    .toggle-btn {
      padding: var(--spacing-1) var(--spacing-3);
      border: none;
      background-color: var(--color-bg-primary);
      color: var(--color-text-secondary);
      font-size: var(--font-size-lg);
      cursor: pointer;
      transition: all var(--transition-fast);
      border-right: 1px solid var(--color-border);

      &:last-child {
        border-right: none;
      }

      &:hover {
        background-color: var(--color-gray-100);
      }

      &.active {
        background-color: var(--color-primary-500);
        color: white;
      }
    }
  }

  .results-count {
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
  }

  .mobile-filter-btn {
    display: none;
    padding: var(--spacing-2) var(--spacing-3);
    font-size: var(--font-size-sm);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    background-color: var(--color-bg-primary);
    cursor: pointer;

    @media (max-width: 768px) {
      display: block;
    }
  }

  /* Mobile Detail Overlay */
  .mobile-detail-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: var(--color-bg-primary);
    z-index: 100;
    display: flex;
    flex-direction: column;
  }

  .mobile-detail-header {
    display: flex;
    align-items: center;
    gap: var(--spacing-3);
    padding: var(--spacing-3) var(--spacing-4);
    border-bottom: 1px solid var(--color-border);
    background-color: var(--color-bg-secondary);

    h2 {
      margin: 0;
      font-size: var(--font-size-lg);
    }
  }

  .back-btn {
    padding: var(--spacing-2) var(--spacing-3);
    font-size: var(--font-size-sm);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    background-color: var(--color-bg-primary);
    cursor: pointer;
  }

  .mobile-detail-content {
    flex: 1;
    overflow-y: auto;
    padding: var(--spacing-4);
  }

  /* Mobile Filters Overlay */
  .mobile-filters-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: var(--color-bg-primary);
    z-index: 100;
    display: flex;
    flex-direction: column;
  }

  .mobile-filters-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: var(--spacing-3) var(--spacing-4);
    border-bottom: 1px solid var(--color-border);
    background-color: var(--color-bg-secondary);

    h2 {
      margin: 0;
      font-size: var(--font-size-lg);
    }
  }

  .close-btn {
    padding: var(--spacing-2) var(--spacing-3);
    font-size: var(--font-size-lg);
    border: none;
    background: none;
    cursor: pointer;
    color: var(--color-text-secondary);
  }

  .mobile-filters-content {
    flex: 1;
    overflow-y: auto;
    padding: var(--spacing-4);
  }
</style>
