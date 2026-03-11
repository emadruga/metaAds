<template>
  <div class="niche-selector">
    <header class="selector-header">
      <div class="header-left">
        <h1 class="logo">MetAds</h1>
      </div>
      <nav class="header-nav">
        <router-link to="/competitors" class="nav-link">
          🏆 Competition
        </router-link>
        <router-link to="/admin/collection-health" class="nav-link">
          📡 Collection Health
        </router-link>
        <router-link v-if="isAdmin" to="/admin/global-history" class="nav-link">
          🌐 Global History
        </router-link>
      </nav>
      <div class="header-right">
        <!-- In dev mode, show simple user badge instead of Clerk -->
        <div v-if="isDevMode" class="dev-user-badge">
          👤 Dev User
        </div>
        <UserButton v-else :afterSignOutUrl="'/sign-in'" />
      </div>
    </header>

    <main class="selector-main">
      <div class="selector-content">
        <h2 class="selector-title">Your Niches</h2>
        <p class="selector-subtitle">Select a niche to start analyzing ads</p>

        <div v-if="loading" class="loading-state">
          <div class="spinner"></div>
          <p>Loading niches...</p>
        </div>

        <div v-else-if="error" class="error-state">
          <div class="error-icon">⚠️</div>
          <h3>Error Loading Niches</h3>
          <p>{{ error }}</p>
          <button class="btn btn-primary" @click="nichesStore.fetchNiches()">
            Try Again
          </button>
        </div>

        <div v-else-if="niches.length === 0" class="empty-state">
          <div class="empty-icon">📊</div>
          <h3>No niches yet</h3>
          <p>Create your first niche to start collecting and analyzing ads</p>
          <router-link to="/niches/new" class="btn btn-primary">
            Create First Niche
          </router-link>
        </div>

        <div v-else class="niche-grid">
          <NicheCard v-for="niche in niches" :key="niche.id" :niche="niche" />

          <router-link to="/niches/new" class="niche-card niche-card-new">
            <div class="niche-icon">+</div>
            <h3 class="niche-name">Create New</h3>
            <p class="niche-description">Add a new research niche</p>
          </router-link>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
  import { onMounted, computed, ref, watch } from 'vue'
  import { UserButton, useUser } from '@clerk/vue'
  import { useNichesStore } from '@/stores/niches'
  import { devMode } from '@/services/api'
  import NicheCard from '@/components/NicheCard.vue'

  const nichesStore = useNichesStore()
  const isDevMode = devMode

  // In dev mode there is no Clerk — always show admin links
  const isAdmin = ref(isDevMode)

  // Must be called at setup time (not inside onMounted), same pattern as App.vue.
  // useUser().user is a reactive ref; watch keeps isAdmin in sync as Clerk loads.
  if (!isDevMode) {
    const { user } = useUser()
    watch(user, (u) => {
      isAdmin.value = u?.publicMetadata?.role === 'admin'
    }, { immediate: true })
  }

  const niches = computed(() => nichesStore.niches)
  const loading = computed(() => nichesStore.loading)
  const error = computed(() => nichesStore.error)

  onMounted(() => {
    nichesStore.fetchNiches()
  })
</script>

<style lang="scss" scoped>
  .niche-selector {
    min-height: 100vh;
    background-color: var(--color-bg-secondary);
  }

  .selector-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: var(--spacing-4) var(--spacing-6);
    background-color: var(--color-bg-primary);
    border-bottom: 1px solid var(--color-border);
  }

  .logo {
    font-size: var(--font-size-xl);
    font-weight: 700;
    color: var(--color-gray-900);
  }

  .header-nav {
    display: flex;
    align-items: center;
    gap: var(--spacing-2);
  }

  .nav-link {
    font-size: var(--font-size-sm);
    font-weight: 500;
    color: var(--color-text-secondary);
    text-decoration: none;
    padding: var(--spacing-2) var(--spacing-3);
    border-radius: var(--radius-md);
    transition: all var(--transition-fast);

    &:hover {
      color: var(--color-gray-900);
      background-color: var(--color-gray-100);
    }

    &.router-link-active {
      color: var(--color-primary-600);
      background-color: var(--color-primary-50);
    }
  }

  .dev-user-badge {
    padding: var(--spacing-2) var(--spacing-3);
    background-color: var(--color-warning-100);
    border-radius: var(--radius-full);
    font-size: var(--font-size-sm);
  }

  .selector-main {
    padding: var(--spacing-8);
    max-width: 1200px;
    margin: 0 auto;
  }

  .selector-title {
    font-size: var(--font-size-2xl);
    font-weight: 600;
    margin-bottom: var(--spacing-2);
  }

  .selector-subtitle {
    color: var(--color-text-secondary);
    margin-bottom: var(--spacing-6);
  }

  .loading-state,
  .empty-state,
  .error-state {
    text-align: center;
    padding: var(--spacing-12);
  }

  .spinner {
    width: 40px;
    height: 40px;
    border: 3px solid var(--color-gray-200);
    border-top-color: var(--color-primary-500);
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto var(--spacing-4);
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  .empty-icon,
  .error-icon {
    font-size: 4rem;
    margin-bottom: var(--spacing-4);
  }

  .empty-state h3,
  .error-state h3 {
    font-size: var(--font-size-xl);
    margin-bottom: var(--spacing-2);
  }

  .empty-state p,
  .error-state p {
    color: var(--color-text-secondary);
    margin-bottom: var(--spacing-6);
  }

  .niche-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: var(--spacing-4);
  }

  .niche-card-new {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 150px;
    padding: var(--spacing-6);
    background-color: var(--color-bg-secondary);
    border: 2px dashed var(--color-gray-300);
    border-radius: var(--radius-xl);
    text-decoration: none;
    transition: all var(--transition-base);

    &:hover {
      border-color: var(--color-primary-400);
      background-color: var(--color-primary-50);
    }

    .niche-icon {
      font-size: 2rem;
      color: var(--color-gray-400);
      margin-bottom: var(--spacing-2);
    }

    .niche-name {
      font-size: var(--font-size-lg);
      font-weight: 600;
      color: var(--color-text-secondary);
      margin: 0 0 var(--spacing-1) 0;
    }

    .niche-description {
      font-size: var(--font-size-sm);
      color: var(--color-text-muted);
      margin: 0;
    }
  }
</style>
