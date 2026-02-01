<template>
  <div class="settings-view">
    <div class="settings-header">
      <h2>Niche Settings</h2>
      <p class="subtitle">Configure your niche preferences</p>
    </div>

    <div class="settings-content">
      <p class="placeholder-text">
        Niche settings functionality will be implemented in Phase 4.
        <br /><br />
        Use the API endpoints to test:
        <br />
        <code>PATCH /api/niches/:slug</code>
        <br />
        <code>POST /api/niches/:slug/collect</code>
      </p>
    </div>
  </div>
</template>

<script setup>
// Niche settings component - to be implemented in Phase 4
</script>

<style lang="scss" scoped>
.settings-view {
  background-color: var(--color-bg-primary);
  border-radius: var(--radius-lg);
  padding: var(--spacing-6);
  max-width: 800px;
  margin: 0 auto;
}

.settings-header {
  margin-bottom: var(--spacing-6);

  h2 {
    font-size: var(--font-size-xl);
    font-weight: 600;
    margin-bottom: var(--spacing-2);
  }

  .subtitle {
    color: var(--color-text-secondary);
  }
}

.placeholder-text {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);

  code {
    display: inline-block;
    margin-top: var(--spacing-2);
    padding: var(--spacing-1) var(--spacing-2);
    background-color: var(--color-gray-100);
    border-radius: var(--radius-sm);
    font-family: monospace;
    font-size: var(--font-size-xs);
  }
}
</style>
