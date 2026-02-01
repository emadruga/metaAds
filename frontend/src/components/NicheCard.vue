<template>
  <router-link :to="`/n/${niche.slug}`" class="niche-card" :style="cardStyle">
    <div class="niche-icon">{{ niche.icon || '📊' }}</div>
    <div class="niche-info">
      <h3 class="niche-name">{{ niche.name }}</h3>
      <p class="niche-description" v-if="niche.description">{{ niche.description }}</p>
      <div class="niche-stats">
        <span class="stat">
          <span class="stat-value">{{ niche.stats?.total_ads || 0 }}</span>
          <span class="stat-label">ads</span>
        </span>
        <span class="stat">
          <span class="stat-value">{{ niche.stats?.saved_ads || 0 }}</span>
          <span class="stat-label">saved</span>
        </span>
      </div>
    </div>
    <div class="niche-arrow">→</div>
  </router-link>
</template>

<script setup>
  import { computed } from 'vue'

  const props = defineProps({
    niche: {
      type: Object,
      required: true
    }
  })

  const cardStyle = computed(() => ({
    '--accent-color': props.niche.color || '#8B5CF6'
  }))
</script>

<style lang="scss" scoped>
  .niche-card {
    display: flex;
    align-items: center;
    gap: var(--spacing-4);
    padding: var(--spacing-4);
    background-color: var(--color-bg-primary);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
    text-decoration: none;
    color: inherit;
    transition: all var(--transition-fast);
    border-left: 4px solid var(--accent-color);

    &:hover {
      border-color: var(--accent-color);
      box-shadow: var(--shadow-md);
      transform: translateY(-2px);
    }
  }

  .niche-icon {
    font-size: 2rem;
    width: 48px;
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: var(--color-gray-100);
    border-radius: var(--radius-md);
  }

  .niche-info {
    flex: 1;
  }

  .niche-name {
    font-size: var(--font-size-lg);
    font-weight: 600;
    margin: 0 0 var(--spacing-1) 0;
  }

  .niche-description {
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
    margin: 0 0 var(--spacing-2) 0;
  }

  .niche-stats {
    display: flex;
    gap: var(--spacing-4);
  }

  .stat {
    display: flex;
    align-items: baseline;
    gap: var(--spacing-1);

    .stat-value {
      font-weight: 600;
      color: var(--accent-color);
    }

    .stat-label {
      font-size: var(--font-size-xs);
      color: var(--color-text-secondary);
    }
  }

  .niche-arrow {
    color: var(--color-text-secondary);
    font-size: var(--font-size-xl);
  }
</style>
