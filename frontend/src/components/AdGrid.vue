<template>
  <div class="ad-grid-container">
    <!-- Loading state -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Loading ads...</p>
    </div>

    <!-- Empty state -->
    <div v-else-if="ads.length === 0" class="empty-state">
      <div class="empty-icon">📭</div>
      <h3>No ads found</h3>
      <p>{{ emptyMessage }}</p>
      <button v-if="showCollectButton" class="btn btn-primary collect-cta" @click="$emit('collect')">
        📥 Collect Ads Now
      </button>
    </div>

    <!-- Ad grid: one card per item.
         Items may be variant groups { variant_key, ads: [...] }
         or flat ad objects (e.g. from Saved view). -->
    <div v-else class="ad-grid">
      <AdCard
        v-for="item in ads"
        :key="item.variant_key || item.ads?.[0]?.meta_ad_id || item.meta_ad_id"
        :ad="item.ads ? item.ads[0] : item"
        :is-selected="selectedAdId === (item.ads ? item.ads[0]?.meta_ad_id : item.meta_ad_id)"
        @select="$emit('select', $event)"
        @toggle-save="$emit('toggle-save', $event)"
      />
    </div>

    <!-- Pagination -->
    <div v-if="pagination && pagination.pages > 1" class="pagination">
      <button
        class="btn btn-ghost btn-icon"
        :disabled="pagination.page === 1"
        @click="$emit('page-change', 1)"
        title="First page"
      >
        ⇤
      </button>
      <button
        class="btn btn-ghost"
        :disabled="!pagination.has_prev"
        @click="$emit('page-change', pagination.page - 1)"
      >
        ← Previous
      </button>
      <span class="page-info">
        Page {{ pagination.page }} of {{ pagination.pages }}
      </span>
      <button
        class="btn btn-ghost"
        :disabled="!pagination.has_next"
        @click="$emit('page-change', pagination.page + 1)"
      >
        Next →
      </button>
      <button
        class="btn btn-ghost btn-icon"
        :disabled="pagination.page === pagination.pages"
        @click="$emit('page-change', pagination.pages)"
        title="Last page"
      >
        ⇥
      </button>
    </div>
  </div>
</template>

<script setup>
  import AdCard from './AdCard.vue'

  defineProps({
    ads: {
      type: Array,
      default: () => []
    },
    loading: {
      type: Boolean,
      default: false
    },
    selectedAdId: {
      type: String,
      default: null
    },
    pagination: {
      type: Object,
      default: null
    },
    emptyMessage: {
      type: String,
      default: 'Try adjusting your search filters.'
    },
    showCollectButton: {
      type: Boolean,
      default: false
    }
  })

  defineEmits(['select', 'toggle-save', 'page-change', 'collect'])
</script>

<style lang="scss" scoped>
  .ad-grid-container {
    height: 100%;
    display: flex;
    flex-direction: column;
  }

  .ad-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: var(--spacing-4);
    flex: 1;
    overflow-y: auto;
    padding-bottom: var(--spacing-4);
  }

  .loading-state,
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: var(--spacing-8);
    text-align: center;
    color: var(--color-text-secondary);
  }

  .spinner {
    width: 40px;
    height: 40px;
    border: 3px solid var(--color-gray-200);
    border-top-color: var(--color-primary-500);
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-bottom: var(--spacing-3);
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  .empty-icon {
    font-size: 3rem;
    margin-bottom: var(--spacing-3);
  }

  .empty-state h3 {
    margin: 0 0 var(--spacing-2) 0;
    color: var(--color-text-primary);
  }

  .empty-state p {
    margin: 0;
    font-size: var(--font-size-sm);
  }

  .collect-cta {
    margin-top: var(--spacing-4);
  }

  .pagination {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: var(--spacing-4);
    padding-top: var(--spacing-4);
    border-top: 1px solid var(--color-border);
    margin-top: auto;
  }

  .page-info {
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
  }
</style>
