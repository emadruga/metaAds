<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-container">
      <!-- Header -->
      <div class="modal-header">
        <div class="modal-title">
          <span class="page-badge">{{ ad.page_name }}</span>
          <span v-if="ad.is_active" class="status-badge active">Active</span>
          <span v-else class="status-badge inactive">Inactive</span>
        </div>
        <button class="close-btn" @click="$emit('close')">✕</button>
      </div>

      <!-- Body -->
      <div class="modal-body">
        <!-- Ad ID -->
        <div class="ad-id">
          <span class="field-label">Library ID</span>
          <span class="field-value mono">{{ ad.meta_ad_id }}</span>
        </div>

        <!-- Stats row -->
        <div class="stats-row">
          <div class="stat">
            <span class="stat-label">Days Active</span>
            <span class="stat-value highlight">{{ ad.days_active ?? '—' }}</span>
          </div>
          <div class="stat">
            <span class="stat-label">Started</span>
            <span class="stat-value">{{ formatDate(ad.start_date) }}</span>
          </div>
          <div class="stat" v-if="ad.end_date">
            <span class="stat-label">Ended</span>
            <span class="stat-value">{{ formatDate(ad.end_date) }}</span>
          </div>
          <div class="stat">
            <span class="stat-label">Platforms</span>
            <span class="stat-value">{{ formatPlatforms(ad.platforms) }}</span>
          </div>
        </div>

        <!-- Content -->
        <div v-if="ad.headline" class="ad-section">
          <span class="field-label">Headline</span>
          <p class="ad-headline">{{ ad.headline }}</p>
        </div>

        <div v-if="ad.body" class="ad-section">
          <span class="field-label">Ad Copy</span>
          <p class="ad-body">{{ ad.body }}</p>
        </div>

        <div v-if="ad.description" class="ad-section">
          <span class="field-label">Description</span>
          <p class="ad-description">{{ ad.description }}</p>
        </div>

        <div v-if="ad.link_caption" class="ad-section">
          <span class="field-label">Link Caption</span>
          <p class="ad-caption">{{ ad.link_caption }}</p>
        </div>
      </div>

      <!-- Footer actions -->
      <div class="modal-footer">
        <button class="btn btn-ghost" @click="$emit('close')">Close</button>
        <a
          v-if="metaAdLibraryUrl"
          :href="metaAdLibraryUrl"
          target="_blank"
          rel="noopener noreferrer"
          class="btn btn-primary"
        >
          View on Meta Ad Library
        </a>
      </div>
    </div>
  </div>
</template>

<script setup>
  import { computed } from 'vue'

  const props = defineProps({
    ad: {
      type: Object,
      required: true,
    },
  })

  defineEmits(['close'])

  // Works for both Graph API ads (snapshot_url set) and Playwright ads (meta_ad_id only)
  const metaAdLibraryUrl = computed(() => {
    if (props.ad.snapshot_url) return props.ad.snapshot_url
    if (props.ad.meta_ad_id) return `https://www.facebook.com/ads/library/?id=${props.ad.meta_ad_id}`
    return null
  })

  function formatDate(dateStr) {
    if (!dateStr) return '—'
    try {
      return new Date(dateStr).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      })
    } catch {
      return dateStr
    }
  }

  function formatPlatforms(platforms) {
    if (!platforms || platforms.length === 0) return '—'
    const labels = {
      facebook: 'Facebook',
      instagram: 'Instagram',
      messenger: 'Messenger',
      audience_network: 'Audience Network',
    }
    return platforms.map((p) => labels[p] || p).join(', ')
  }
</script>

<style lang="scss" scoped>
  .modal-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.55);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 2000;
    padding: var(--spacing-4);
  }

  .modal-container {
    background: var(--color-bg-primary);
    border-radius: var(--radius-xl);
    width: 100%;
    max-width: 600px;
    max-height: 90vh;
    display: flex;
    flex-direction: column;
    box-shadow: 0 24px 80px rgba(0, 0, 0, 0.3);
    overflow: hidden;
  }

  .modal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: var(--spacing-4) var(--spacing-5);
    border-bottom: 1px solid var(--color-border);
    gap: var(--spacing-3);
  }

  .modal-title {
    display: flex;
    align-items: center;
    gap: var(--spacing-2);
    flex: 1;
    min-width: 0;
  }

  .page-badge {
    font-size: var(--font-size-base);
    font-weight: 600;
    color: var(--color-gray-900);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .status-badge {
    flex-shrink: 0;
    font-size: var(--font-size-xs);
    font-weight: 600;
    padding: 2px var(--spacing-2);
    border-radius: var(--radius-full);

    &.active {
      background-color: var(--color-success-50);
      color: var(--color-success-700);
      border: 1px solid var(--color-success-200);
    }

    &.inactive {
      background-color: var(--color-gray-100);
      color: var(--color-gray-600);
      border: 1px solid var(--color-gray-300);
    }
  }

  .close-btn {
    flex-shrink: 0;
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    background: transparent;
    cursor: pointer;
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
    transition: all var(--transition-fast);

    &:hover {
      background-color: var(--color-gray-100);
    }
  }

  .modal-body {
    flex: 1;
    overflow-y: auto;
    padding: var(--spacing-5);
    display: flex;
    flex-direction: column;
    gap: var(--spacing-4);
  }

  .ad-id {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-1);
  }

  .field-label {
    font-size: var(--font-size-xs);
    font-weight: 600;
    color: var(--color-text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .field-value {
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);

    &.mono {
      font-family: monospace;
      font-size: var(--font-size-xs);
    }
  }

  .stats-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: var(--spacing-3);
    padding: var(--spacing-3);
    background-color: var(--color-bg-secondary);
    border-radius: var(--radius-lg);
  }

  .stat {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-1);
  }

  .stat-label {
    font-size: var(--font-size-xs);
    font-weight: 600;
    color: var(--color-text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .stat-value {
    font-size: var(--font-size-sm);
    font-weight: 500;
    color: var(--color-gray-900);

    &.highlight {
      font-size: var(--font-size-xl);
      font-weight: 700;
      color: var(--color-primary-600);
    }
  }

  .ad-section {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-2);
  }

  .ad-headline {
    font-size: var(--font-size-base);
    font-weight: 600;
    color: var(--color-gray-900);
    margin: 0;
    line-height: 1.4;
  }

  .ad-body {
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
    margin: 0;
    line-height: 1.6;
    white-space: pre-wrap;
  }

  .ad-description,
  .ad-caption {
    font-size: var(--font-size-sm);
    color: var(--color-text-muted);
    margin: 0;
    line-height: 1.5;
  }

  .modal-footer {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: var(--spacing-2);
    padding: var(--spacing-4) var(--spacing-5);
    border-top: 1px solid var(--color-border);
  }
</style>
