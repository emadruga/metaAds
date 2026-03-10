<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-content creative-quality-modal">
      <!-- Header -->
      <div class="modal-header">
        <div class="header-title">
          <h3>🎨 Creative Quality Assessment</h3>
          <span v-if="adPageName" class="page-name">{{ adPageName }}</span>
        </div>
        <button class="close-btn" @click="$emit('close')">✕</button>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <p>Checking creative assets...</p>
        <small>Probing thumbnail and video availability</small>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="error-state">
        <div class="error-icon">⚠️</div>
        <p>{{ error }}</p>
        <button class="btn btn-ghost" @click="$emit('close')">Close</button>
      </div>

      <!-- Results -->
      <template v-else-if="assets">
        <div class="assets-section">
          <div class="section-title">ASSET AVAILABILITY</div>
          <div class="assets-grid">

            <!-- Thumbnail -->
            <div class="asset-card" :class="assets.thumbnail.accessible ? 'accessible' : 'unavailable'">
              <div class="asset-icon">🖼️</div>
              <div class="asset-info">
                <div class="asset-label">Thumbnail</div>
                <div class="asset-status">
                  <span class="status-badge" :class="assets.thumbnail.accessible ? 'badge-ok' : 'badge-fail'">
                    {{ assets.thumbnail.accessible ? '✓ Available' : '✗ Not Available' }}
                  </span>
                </div>
                <div v-if="assets.thumbnail.url" class="asset-url">
                  <span class="url-preview">{{ truncateUrl(assets.thumbnail.url) }}</span>
                </div>
                <div v-else class="asset-url-missing">No thumbnail URL found in snapshot</div>
              </div>
            </div>

            <!-- Video -->
            <div class="asset-card" :class="assets.video.accessible ? 'accessible' : (isImageAd ? 'not-applicable' : 'unavailable')">
              <div class="asset-icon">🎬</div>
              <div class="asset-info">
                <div class="asset-label">Video (MP4)</div>
                <div class="asset-status">
                  <span v-if="isImageAd" class="status-badge badge-neutral">
                    — Image ad
                  </span>
                  <span v-else class="status-badge" :class="assets.video.accessible ? 'badge-ok' : 'badge-fail'">
                    {{ assets.video.accessible ? '✓ Available' : '✗ Not Available' }}
                  </span>
                </div>
                <div v-if="assets.video.url" class="asset-url">
                  <span class="url-preview">{{ truncateUrl(assets.video.url) }}</span>
                </div>
                <div v-else-if="!isImageAd" class="asset-url-missing">No video URL found in snapshot</div>
              </div>
            </div>

          </div>
        </div>

        <!-- Fetch error note if any -->
        <div v-if="assets.fetch_error" class="fetch-error-note">
          <small>⚠️ Snapshot fetch issue: {{ assets.fetch_error }}</small>
        </div>

        <!-- Info note -->
        <div class="info-note">
          <small>
            💡 Asset URLs are CDN-signed and expire after a few hours. Run this check again
            if you need fresh URLs. Download buttons will be available in the next version.
          </small>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { adApi } from '../services/api.js'

const props = defineProps({
  nicheSlug: {
    type: String,
    required: true
  },
  adId: {
    type: String,
    required: true
  },
  adPageName: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['close'])

const loading = ref(true)
const error = ref(null)
const assets = ref(null)

const isImageAd = computed(() => {
  if (!assets.value) return false
  return assets.value.creative_type === 'image' && !assets.value.video.url
})

function truncateUrl(url) {
  if (!url) return ''
  try {
    const u = new URL(url)
    return u.hostname + u.pathname.substring(0, 40) + (u.pathname.length > 40 ? '...' : '')
  } catch {
    return url.substring(0, 60) + (url.length > 60 ? '...' : '')
  }
}

onMounted(async () => {
  try {
    const resp = await adApi.creativeAssets(props.nicheSlug, props.adId)
    assets.value = resp.data?.data || resp.data
  } catch (err) {
    error.value = err.response?.data?.error || err.message || 'Failed to check creative assets'
  } finally {
    loading.value = false
  }
})
</script>

<style lang="scss" scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: var(--spacing-4);
}

.modal-content {
  background-color: var(--color-bg-primary);
  border-radius: var(--radius-lg);
  max-width: 560px;
  width: 100%;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.15);
  overflow: hidden;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-4);
  border-bottom: 1px solid var(--color-border);

  .header-title {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-1);
  }

  h3 {
    margin: 0;
    font-size: var(--font-size-xl);
    font-weight: 600;
  }

  .page-name {
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
  }
}

.close-btn {
  background: none;
  border: none;
  font-size: var(--font-size-xl);
  cursor: pointer;
  color: var(--color-text-secondary);
  padding: var(--spacing-2);
  line-height: 1;

  &:hover {
    color: var(--color-text-primary);
  }
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-8) var(--spacing-4);
  gap: var(--spacing-2);
  color: var(--color-text-secondary);

  p {
    margin: 0;
    font-weight: 500;
    color: var(--color-text-primary);
  }

  small {
    font-size: var(--font-size-sm);
  }
}

.spinner {
  width: 36px;
  height: 36px;
  border: 3px solid var(--color-border);
  border-top-color: var(--color-primary-600);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--spacing-8) var(--spacing-4);
  gap: var(--spacing-3);
  text-align: center;

  .error-icon {
    font-size: 2.5rem;
  }

  p {
    color: var(--color-text-primary);
    margin: 0;
  }
}

.assets-section {
  padding: var(--spacing-4);

  .section-title {
    font-size: var(--font-size-xs);
    font-weight: 600;
    letter-spacing: 0.05em;
    color: var(--color-text-secondary);
    margin-bottom: var(--spacing-3);
  }
}

.assets-grid {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
}

.asset-card {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-3);
  padding: var(--spacing-3) var(--spacing-4);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);

  &.accessible {
    background-color: var(--color-success-50, #f0fdf4);
    border-color: var(--color-success-200, #bbf7d0);
  }

  &.unavailable {
    background-color: var(--color-error-50, #fef2f2);
    border-color: var(--color-error-200, #fecaca);
  }

  &.not-applicable {
    background-color: var(--color-bg-secondary);
    opacity: 0.6;
  }
}

.asset-icon {
  font-size: 1.75rem;
  line-height: 1;
  flex-shrink: 0;
}

.asset-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-1);
}

.asset-label {
  font-weight: 600;
  font-size: var(--font-size-base);
  color: var(--color-text-primary);
}

.asset-status {
  display: flex;
  align-items: center;
}

.status-badge {
  font-size: var(--font-size-sm);
  font-weight: 600;
  padding: 2px var(--spacing-2);
  border-radius: var(--radius-sm);

  &.badge-ok {
    background-color: var(--color-success-100, #dcfce7);
    color: var(--color-success-700, #15803d);
  }

  &.badge-fail {
    background-color: var(--color-error-100, #fee2e2);
    color: var(--color-error-700, #b91c1c);
  }

  &.badge-neutral {
    background-color: var(--color-bg-secondary);
    color: var(--color-text-secondary);
  }
}

.asset-url {
  margin-top: var(--spacing-1);
}

.url-preview {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  font-family: monospace;
  word-break: break-all;
}

.asset-url-missing {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  font-style: italic;
}

.fetch-error-note {
  padding: var(--spacing-2) var(--spacing-4);
  background-color: var(--color-warning-50, #fffbeb);
  border-top: 1px solid var(--color-border);

  small {
    color: var(--color-warning-700, #b45309);
  }
}

.info-note {
  padding: var(--spacing-3) var(--spacing-4);
  border-top: 1px solid var(--color-border);

  small {
    font-size: var(--font-size-xs);
    color: var(--color-text-secondary);
    line-height: 1.5;
  }
}
</style>
