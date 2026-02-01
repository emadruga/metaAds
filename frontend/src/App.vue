<template>
  <div class="app">
    <!-- In dev mode, show dev banner -->
    <div v-if="isDevMode" class="dev-banner">
      🔧 Dev Mode - Auth Bypassed
    </div>

    <!-- In production, use Clerk control components -->
    <template v-if="!isDevMode">
      <ClerkLoading>
        <div class="loading-container">
          <div class="loading-spinner"></div>
          <p>Loading...</p>
        </div>
      </ClerkLoading>
      <ClerkLoaded>
        <RouterView />
      </ClerkLoaded>
    </template>

    <!-- In dev mode, just render the router -->
    <template v-else>
      <RouterView />
    </template>
  </div>
</template>

<script setup>
  import { watch } from 'vue'
  import { ClerkLoaded, ClerkLoading, useAuth } from '@clerk/vue'
  import { devMode } from '@/services/api'
  import { setAuthInstance } from '@/services/clerkClient'

  const isDevMode = devMode

  // In production mode, set the auth instance for API interceptor
  if (!isDevMode) {
    const auth = useAuth()

    // Watch for Clerk to be loaded and set the auth instance
    watch(
      () => auth.isLoaded.value,
      (isLoaded) => {
        if (isLoaded) {
          console.log('[App] Clerk loaded, setting auth instance for API')
          setAuthInstance(auth)
        }
      },
      { immediate: true }
    )
  }
</script>

<style lang="scss">
  .app {
    min-height: 100vh;
    background-color: var(--color-bg-primary);
    color: var(--color-text-primary);
  }

  .dev-banner {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    background: linear-gradient(90deg, #f59e0b, #d97706);
    color: white;
    text-align: center;
    padding: 4px 0;
    font-size: 12px;
    font-weight: 600;
    z-index: 9999;
  }

  /* Offset body content when dev banner is shown */
  .dev-banner + * {
    margin-top: 28px;
  }

  .loading-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    gap: var(--spacing-4);
  }

  .loading-spinner {
    width: 40px;
    height: 40px;
    border: 3px solid var(--color-border);
    border-top-color: var(--color-primary);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  .loading-container p {
    color: var(--color-text-secondary);
    font-size: var(--font-size-sm);
  }
</style>
