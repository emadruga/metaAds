<template>
  <div class="workspace">
    <header class="workspace-header">
      <div class="header-left">
        <router-link to="/" class="back-btn">←</router-link>
        <span class="niche-icon" v-if="currentNiche">{{ currentNiche.icon }}</span>
        <h1 class="niche-name">{{ currentNiche?.name || 'Loading...' }}</h1>
      </div>
      <div class="header-right">
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
  import { computed, onMounted, watch } from 'vue'
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

  const nicheSlug = computed(() => route.params.nicheSlug)
  const currentNiche = computed(() => nichesStore.currentNiche)

  async function loadNiche() {
    if (nicheSlug.value) {
      await nichesStore.fetchNiche(nicheSlug.value)
    }
  }

  function handleCollected(result) {
    // Refresh the ads list after collection
    if (result.ads_collected > 0) {
      adsStore.searchAds(nicheSlug.value)
    }
  }

  onMounted(() => {
    loadNiche()
  })

  watch(nicheSlug, () => {
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
</style>
