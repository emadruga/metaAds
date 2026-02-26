<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-content related-ads-modal">
      <!-- Header -->
      <div class="modal-header">
        <div class="header-title">
          <h3>Related Ads ({{ related.length }})</h3>
          <span v-if="pageName" class="page-name">{{ pageName }}</span>
        </div>
        <button class="close-btn" @click="$emit('close')">✕</button>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <p>Loading related ads...</p>
      </div>

      <!-- Empty State -->
      <div v-else-if="!related || related.length === 0" class="empty-state">
        <p>No related ads found</p>
        <small>No other ads from this advertiser in this niche</small>
      </div>

      <template v-else>
        <!-- Campaign Insights -->
        <div v-if="insights" class="insights-section">
          <div class="insights-title">CAMPAIGN INSIGHTS</div>
          <div class="insights-grid">
            <div class="insight-item">
              <span class="insight-label">Longest running:</span>
              <span class="insight-value">{{ insights.longest_running?.days_active || 0 }} days</span>
            </div>
            <div class="insight-item">
              <span class="insight-label">Total campaigns:</span>
              <span class="insight-value">{{ insights.total_variants }}</span>
            </div>
            <div class="insight-item" v-if="insights.newest?.start_date">
              <span class="insight-label">Newest:</span>
              <span class="insight-value">{{ formatRelativeDate(insights.newest.start_date) }}</span>
            </div>
          </div>
        </div>

        <!-- Related Ads List -->
        <div class="related-ads-list">
          <div
            v-for="ad in related"
            :key="ad.id"
            class="related-ad-item"
            @click="handleSelectAd(ad)"
          >
            <!-- Badge for longest/newest -->
            <div v-if="getBadge(ad)" class="ad-badge" :class="getBadge(ad).class">
              {{ getBadge(ad).text }}
            </div>

            <!-- Thumbnail -->
            <div class="ad-thumbnail">
              <CreativeCarousel
                :creatives="ad.creatives || []"
                :thumbnail-url="ad.thumbnail_url"
                :alt="ad.page_name"
              />
            </div>

            <!-- Content -->
            <div class="ad-content">
              <h4 v-if="ad.headline" class="ad-headline">
                {{ truncateText(ad.headline, 80) }}
              </h4>
              <p v-if="ad.body" class="ad-body">
                {{ truncateText(ad.body, 120) }}
              </p>

              <div class="ad-meta">
                <span class="meta-item">
                  <span class="meta-icon">📅</span>
                  {{ ad.days_active || 0 }} days
                </span>
                <span class="meta-item" v-if="ad.platforms && ad.platforms.length > 0">
                  <span class="meta-icon">{{ getPlatformIcons(ad.platforms) }}</span>
                </span>
                <span class="meta-item" v-if="ad.cta">
                  {{ ad.cta }}
                </span>
                <span class="status-badge" :class="ad.is_active ? 'active' : 'inactive'">
                  {{ ad.is_active ? 'Active' : 'Inactive' }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import CreativeCarousel from './CreativeCarousel.vue'

const props = defineProps({
  related: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  insights: {
    type: Object,
    default: null
  },
  pageName: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['close', 'select-ad'])

function handleSelectAd(ad) {
  emit('select-ad', ad)
  emit('close')
}

function getBadge(ad) {
  if (!props.insights) return null

  // Check if this is the longest running ad
  if (props.insights.longest_running?.id === ad.id) {
    return {
      text: '★ LONGEST',
      class: 'longest'
    }
  }

  // Check if this is the newest ad
  if (props.insights.newest?.id === ad.id) {
    return {
      text: '✦ NEWEST',
      class: 'newest'
    }
  }

  return null
}

function truncateText(text, maxLength) {
  if (!text) return ''
  return text.length > maxLength ? text.substring(0, maxLength) + '...' : text
}

function formatDate(dateStr) {
  if (!dateStr) return 'N/A'
  try {
    return new Date(dateStr).toLocaleDateString()
  } catch {
    return dateStr
  }
}

function formatRelativeDate(dateStr) {
  if (!dateStr) return 'N/A'
  try {
    const date = new Date(dateStr)
    const now = new Date()
    const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24))

    if (diffDays === 0) return 'Today'
    if (diffDays === 1) return 'Yesterday'
    if (diffDays < 7) return `${diffDays} days ago`
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`
    return formatDate(dateStr)
  } catch {
    return dateStr
  }
}

function getPlatformIcons(platforms) {
  if (!platforms || platforms.length === 0) return ''

  const icons = {
    facebook: '📘',
    instagram: '📷',
    messenger: '💬',
    audience_network: '🌐'
  }

  return platforms.map(p => icons[p] || '📱').join(' ')
}
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
  max-width: 800px;
  width: 100%;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.15);
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

.insights-section {
  padding: var(--spacing-4);
  background-color: var(--color-primary-50);
  border-bottom: 1px solid var(--color-border);

  .insights-title {
    font-size: var(--font-size-xs);
    font-weight: 600;
    letter-spacing: 0.05em;
    color: var(--color-text-secondary);
    margin-bottom: var(--spacing-2);
  }

  .insights-grid {
    display: flex;
    gap: var(--spacing-4);

    @media (max-width: 600px) {
      flex-direction: column;
      gap: var(--spacing-2);
    }
  }
}

.insight-item {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-1);
}

.insight-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  font-weight: 500;
}

.insight-value {
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--color-primary-700);
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-8);
  color: var(--color-text-secondary);
  text-align: center;

  p {
    margin: 0;
    font-size: var(--font-size-base);
  }

  small {
    margin-top: var(--spacing-1);
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
  }
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--color-gray-200);
  border-top-color: var(--color-primary-500);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: var(--spacing-3);
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.related-ads-list {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-4);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
}

.related-ad-item {
  position: relative;
  display: flex;
  gap: var(--spacing-3);
  padding: var(--spacing-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);

  &:hover {
    border-color: var(--color-primary-300);
    box-shadow: var(--shadow-sm);
    background-color: var(--color-gray-50);
  }

  @media (max-width: 600px) {
    flex-direction: column;
  }
}

.ad-badge {
  position: absolute;
  top: var(--spacing-2);
  right: var(--spacing-2);
  font-size: var(--font-size-xs);
  font-weight: 600;
  padding: 2px 8px;
  border-radius: var(--radius-full);
  z-index: 1;

  &.longest {
    background-color: var(--color-warning-100);
    color: var(--color-warning-700);
  }

  &.newest {
    background-color: var(--color-success-100);
    color: var(--color-success-700);
  }
}

.ad-thumbnail {
  flex-shrink: 0;
  width: 150px;
  height: 100px;
  border-radius: var(--radius-md);
  overflow: hidden;
  background-color: var(--color-gray-100);

  @media (max-width: 600px) {
    width: 100%;
    height: 150px;
  }
}

.ad-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
}

.ad-headline {
  margin: 0;
  font-size: var(--font-size-md);
  font-weight: 600;
  color: var(--color-text-primary);
  line-height: 1.4;
}

.ad-body {
  margin: 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: 1.5;
}

.ad-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--spacing-2);
  margin-top: auto;
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
