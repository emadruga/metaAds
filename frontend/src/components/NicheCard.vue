<template>
  <div class="niche-card" :style="cardStyle" @click="navigateToNiche">
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
      <div class="auto-collect-toggle" @click.stop>
        <span class="toggle-label">Auto-Collect</span>
        <label class="toggle-switch" :class="{ updating: isUpdating }">
          <input
            type="checkbox"
            :checked="niche.auto_collect_enabled || false"
            :disabled="isUpdating"
            @change="handleToggle"
          />
          <span class="slider">
            <span class="slider-off">Off</span>
            <span class="slider-on">On</span>
          </span>
        </label>
      </div>
    </div>
    <div class="niche-arrow">→</div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useNichesStore } from '@/stores/niches'

const props = defineProps({
  niche: {
    type: Object,
    required: true
  }
})

const router = useRouter()
const nichesStore = useNichesStore()
const isUpdating = ref(false)

const cardStyle = computed(() => ({
  '--accent-color': props.niche.color || '#8B5CF6'
}))

function navigateToNiche() {
  router.push(`/n/${props.niche.slug}`)
}

async function handleToggle(event) {
  const enabled = event.target.checked
  isUpdating.value = true
  try {
    await nichesStore.toggleAutoCollect(props.niche.slug, enabled)
  } catch {
    // Store already reverted the optimistic update; checkbox reflects reverted state
    // via niche.auto_collect_enabled binding
    event.target.checked = !enabled
  } finally {
    isUpdating.value = false
  }
}
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
    color: inherit;
    cursor: pointer;
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
    flex-shrink: 0;
  }

  .niche-info {
    flex: 1;
    min-width: 0;
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
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .niche-stats {
    display: flex;
    gap: var(--spacing-4);
    margin-bottom: var(--spacing-2);
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

  // ---- Auto-collect toggle ----

  .auto-collect-toggle {
    display: flex;
    align-items: center;
    gap: var(--spacing-2);
    padding-top: var(--spacing-2);
    border-top: 1px solid var(--color-border);
  }

  .toggle-label {
    font-size: var(--font-size-xs);
    color: var(--color-text-secondary);
    white-space: nowrap;
    user-select: none;
  }

  .toggle-switch {
    position: relative;
    display: inline-block;
    cursor: pointer;

    input {
      position: absolute;
      opacity: 0;
      width: 0;
      height: 0;
    }

    &.updating {
      opacity: 0.6;
      cursor: not-allowed;
    }
  }

  .slider {
    display: flex;
    align-items: center;
    width: 72px;
    height: 26px;
    background-color: var(--color-gray-200);
    border-radius: var(--radius-full);
    position: relative;
    transition: background-color var(--transition-fast);
    overflow: hidden;

    &::before {
      content: '';
      position: absolute;
      left: 3px;
      width: 20px;
      height: 20px;
      background-color: white;
      border-radius: 50%;
      transition: transform var(--transition-fast);
      z-index: 1;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
    }
  }

  .slider-off,
  .slider-on {
    position: absolute;
    font-size: 10px;
    font-weight: 600;
    line-height: 1;
    transition: opacity var(--transition-fast);
    user-select: none;
  }

  .slider-off {
    right: 7px;
    color: var(--color-text-secondary);
    opacity: 1;
  }

  .slider-on {
    left: 7px;
    color: white;
    opacity: 0;
  }

  input:checked + .slider {
    background-color: var(--accent-color);

    &::before {
      transform: translateX(46px);
    }

    .slider-off {
      opacity: 0;
    }

    .slider-on {
      opacity: 1;
    }
  }

  .niche-arrow {
    color: var(--color-text-secondary);
    font-size: var(--font-size-xl);
    flex-shrink: 0;
  }
</style>
