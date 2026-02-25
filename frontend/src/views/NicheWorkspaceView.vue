<template>
  <div class="workspace">
    <header class="workspace-header">
      <div class="header-left">
        <router-link to="/" class="back-btn">←</router-link>
        <span class="niche-icon" v-if="currentNiche">{{ currentNiche.icon }}</span>
        <h1 class="niche-name">{{ currentNiche?.name || 'Loading...' }}</h1>
      </div>
      <div class="header-right">
        <button
          v-if="adsStore.ads.length > 0"
          class="btn btn-ghost"
          @click="handleClearAds"
          :disabled="clearing"
          title="Clear all ads from this niche"
        >
          {{ clearing ? '🗑️ Clearing...' : '🗑️ Clear All' }}
        </button>
        <button class="btn btn-primary collect-btn" @click="nichesStore.openCollectModal()">
          📥 Collect Ads
        </button>
        <router-link :to="`/n/${nicheSlug}/settings`" class="btn btn-ghost">
          ⚙️
        </router-link>
        <!-- In dev mode, show simple user badge instead of Clerk -->
        <div v-if="isDevMode" class="dev-user-badge">
          👤 Dev User
        </div>
        <UserButton v-else :afterSignOutUrl="'/sign-in'" />
      </div>
    </header>

    <!-- Collect Modal -->
    <CollectModal
      v-if="nichesStore.showCollectModal"
      :niche-slug="nicheSlug"
      :keywords="currentNiche?.keywords || []"
      @close="nichesStore.closeCollectModal()"
      @collected="handleCollected"
    />

    <!-- Clear Ads Modal (shown when there are saved ads) -->
    <div v-if="showClearModal" class="modal-overlay" @click.self="showClearModal = false">
      <div class="modal-dialog">
        <h3>Clear Ads</h3>
        <p>
          You have <strong>{{ currentNiche?.stats?.saved_ads || 0 }} saved ad(s)</strong> in this niche.
          What would you like to clear?
        </p>
        <div class="modal-actions">
          <button class="btn btn-ghost" @click="showClearModal = false">Cancel</button>
          <button class="btn btn-secondary" :disabled="clearing" @click="executeClear(false)">
            Clear Unsaved Only
          </button>
          <button class="btn btn-danger" :disabled="clearing" @click="executeClear(true)">
            Clear All (incl. saved)
          </button>
        </div>
      </div>
    </div>

    <nav class="workspace-nav">
      <router-link :to="`/n/${nicheSlug}`" class="nav-item" exact-active-class="active">
        🔍 Search
      </router-link>
      <router-link :to="`/n/${nicheSlug}/saved`" class="nav-item" active-class="active">
        ⭐ Saved
      </router-link>
    </nav>

    <main class="workspace-main">
      <RouterView />
    </main>
  </div>
</template>

<script setup>
  import { ref, computed, onMounted, watch } from 'vue'
  import { useRoute } from 'vue-router'
  import { UserButton } from '@clerk/vue'
  import { useNichesStore } from '@/stores/niches'
  import { useAdsStore } from '@/stores/ads'
  import { devMode } from '@/services/api'
  import CollectModal from '@/components/CollectModal.vue'

  const route = useRoute()
  const nichesStore = useNichesStore()
  const adsStore = useAdsStore()
  const isDevMode = devMode
  const clearing = ref(false)
  const showClearModal = ref(false)

  const nicheSlug = computed(() => route.params.nicheSlug)
  const currentNiche = computed(() => nichesStore.currentNiche)

  async function loadNiche() {
    if (nicheSlug.value) {
      await nichesStore.fetchNiche(nicheSlug.value)
    }
  }

  function handleCollected() {
    // Always refresh after a completed collection so new ads appear
    adsStore.searchAds(nicheSlug.value)
    nichesStore.fetchNiche(nicheSlug.value)
  }

  function handleClearAds() {
    const savedCount = currentNiche.value?.stats?.saved_ads || 0
    if (savedCount > 0) {
      showClearModal.value = true
    } else {
      executeClear(false)
    }
  }

  async function executeClear(includeSaved) {
    showClearModal.value = false
    clearing.value = true

    try {
      const result = await adsStore.clearAllAds(nicheSlug.value, includeSaved)
      // Refresh niche stats so "Your Niches" totals are correct
      await nichesStore.fetchNiche(nicheSlug.value)
      alert(`✓ Cleared ${result.ads_deleted} ads from this niche`)
    } catch (error) {
      alert(`Failed to clear ads: ${error.message}`)
    } finally {
      clearing.value = false
    }
  }

  onMounted(() => {
    loadNiche()
  })

  watch(nicheSlug, () => {
    // Clear selected ad when switching niches
    adsStore.clearSelectedAd()
    loadNiche()
  })
</script>

<style lang="scss" scoped>
  .workspace {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    background-color: var(--color-bg-secondary);
  }

  .workspace-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: var(--spacing-3) var(--spacing-4);
    background-color: var(--color-bg-primary);
    border-bottom: 1px solid var(--color-border);
  }

  .header-left {
    display: flex;
    align-items: center;
    gap: var(--spacing-3);
  }

  .back-btn {
    padding: var(--spacing-2);
    color: var(--color-text-secondary);
    text-decoration: none;
    font-size: var(--font-size-lg);

    &:hover {
      color: var(--color-text-primary);
    }
  }

  .niche-icon {
    font-size: var(--font-size-xl);
  }

  .niche-name {
    font-size: var(--font-size-lg);
    font-weight: 600;
    margin: 0;
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: var(--spacing-2);
  }

  .dev-user-badge {
    padding: var(--spacing-2) var(--spacing-3);
    background-color: var(--color-warning-100);
    border-radius: var(--radius-full);
    font-size: var(--font-size-sm);
  }

  .collect-btn {
    display: flex;
    align-items: center;
    gap: var(--spacing-1);
  }

  .workspace-nav {
    display: flex;
    gap: var(--spacing-1);
    padding: var(--spacing-2) var(--spacing-4);
    background-color: var(--color-bg-primary);
    border-bottom: 1px solid var(--color-border);
  }

  .nav-item {
    padding: var(--spacing-2) var(--spacing-4);
    color: var(--color-text-secondary);
    text-decoration: none;
    border-radius: var(--radius-md);
    font-weight: 500;
    transition: all var(--transition-fast);

    &:hover {
      background-color: var(--color-gray-100);
      color: var(--color-text-primary);
    }

    &.active {
      background-color: var(--color-primary-50);
      color: var(--color-primary-700);
    }
  }

  .workspace-main {
    flex: 1;
    padding: var(--spacing-4);
  }

  .modal-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }

  .modal-dialog {
    background: var(--color-bg-primary);
    border-radius: var(--radius-lg);
    padding: var(--spacing-6);
    max-width: 420px;
    width: 90%;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);

    h3 {
      margin: 0 0 var(--spacing-3);
      font-size: var(--font-size-lg);
    }

    p {
      margin: 0 0 var(--spacing-4);
      color: var(--color-text-secondary);
      line-height: 1.5;
    }
  }

  .modal-actions {
    display: flex;
    gap: var(--spacing-2);
    justify-content: flex-end;
    flex-wrap: wrap;
  }

  .btn-danger {
    background-color: var(--color-error, #dc2626);
    color: white;
    border: none;

    &:hover:not(:disabled) {
      background-color: #b91c1c;
    }
  }

  .btn-secondary {
    background-color: var(--color-gray-200, #e5e7eb);
    color: var(--color-text-primary);
    border: none;

    &:hover:not(:disabled) {
      background-color: var(--color-gray-300, #d1d5db);
    }
  }
</style>
