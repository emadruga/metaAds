<template>
  <div class="ad-card" :class="{ selected: isSelected, saved: ad.is_saved }" @click="$emit('select', ad)">
    <!-- Thumbnail with Creative Carousel -->
    <div class="ad-thumbnail">
      <CreativeCarousel
        :creatives="ad.creatives || []"
        :thumbnail-url="ad.thumbnail_url"
        :alt="ad.page_name"
      />
      <div class="ad-platforms">
        <span v-for="platform in ad.platforms" :key="platform" class="platform-badge">
          {{ platformIcon(platform) }}
        </span>
      </div>
    </div>

    <!-- Content -->
    <div class="ad-content">
      <div class="ad-header">
        <span class="page-name">{{ ad.page_name }}</span>
        <button
          class="save-btn"
          :class="{ active: ad.is_saved }"
          @click.stop="$emit('toggle-save', ad)"
          :title="ad.is_saved ? 'Unsave' : 'Save'"
        >
          {{ ad.is_saved ? '★' : '☆' }}
        </button>
      </div>

      <p class="ad-body" v-if="ad.body">{{ truncatedBody }}</p>

      <div class="ad-meta">
        <span class="meta-item" v-if="ad.days_active">
          <span class="meta-icon">📅</span>
          {{ ad.days_active }} days
        </span>
        <span class="meta-item" v-if="ad.cta">
          <span class="meta-icon">🔗</span>
          {{ ad.cta }}
        </span>
        <span class="status-badge" :class="ad.is_active ? 'active' : 'inactive'">
          {{ ad.is_active ? 'Active' : 'Inactive' }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
  import { computed } from 'vue'
  import CreativeCarousel from './CreativeCarousel.vue'

  const props = defineProps({
    ad: {
      type: Object,
      required: true
    },
    isSelected: {
      type: Boolean,
      default: false
    }
  })

  defineEmits(['select', 'toggle-save'])

  const truncatedBody = computed(() => {
    if (!props.ad.body) return ''
    return props.ad.body.length > 100 ? props.ad.body.substring(0, 100) + '...' : props.ad.body
  })

  function platformIcon(platform) {
    const icons = {
      facebook: '📘',
      instagram: '📷',
      messenger: '💬',
      audience_network: '🌐'
    }
    return icons[platform] || '📱'
  }
</script>

<style lang="scss" scoped>
  .ad-card {
    background-color: var(--color-bg-primary);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
    overflow: hidden;
    cursor: pointer;
    transition: all var(--transition-fast);

    &:hover {
      border-color: var(--color-primary-300);
      box-shadow: var(--shadow-sm);
    }

    &.selected {
      border-color: var(--color-primary-500);
      box-shadow: 0 0 0 2px var(--color-primary-100);
    }

    &.saved {
      border-left: 3px solid var(--color-warning-500);
    }
  }

  .ad-thumbnail {
    position: relative;
    height: 120px;
    background-color: var(--color-gray-100);

    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }

    .thumbnail-placeholder {
      width: 100%;
      height: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 2rem;
      color: var(--color-gray-400);
    }

    .ad-platforms {
      position: absolute;
      top: var(--spacing-2);
      right: var(--spacing-2);
      display: flex;
      gap: var(--spacing-1);
    }

    .platform-badge {
      background-color: rgba(255, 255, 255, 0.9);
      padding: 2px 6px;
      border-radius: var(--radius-sm);
      font-size: var(--font-size-xs);
    }
  }

  .ad-content {
    padding: var(--spacing-3);
  }

  .ad-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: var(--spacing-2);
  }

  .page-name {
    font-weight: 600;
    font-size: var(--font-size-sm);
    color: var(--color-text-primary);
  }

  .save-btn {
    background: none;
    border: none;
    font-size: var(--font-size-lg);
    cursor: pointer;
    color: var(--color-gray-400);
    transition: all var(--transition-fast);

    &:hover,
    &.active {
      color: var(--color-warning-500);
    }
  }

  .ad-body {
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
    line-height: 1.4;
    margin: 0 0 var(--spacing-3) 0;
  }

  .ad-meta {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--spacing-2);
  }

  .meta-item {
    display: flex;
    align-items: center;
    gap: var(--spacing-1);
    font-size: var(--font-size-xs);
    color: var(--color-text-secondary);

    .meta-icon {
      font-size: 0.9em;
    }
  }

  .status-badge {
    font-size: var(--font-size-xs);
    padding: 2px 8px;
    border-radius: var(--radius-full);
    font-weight: 500;

    &.active {
      background-color: var(--color-success-100);
      color: var(--color-success-700);
    }

    &.inactive {
      background-color: var(--color-gray-100);
      color: var(--color-gray-600);
    }
  }
</style>
