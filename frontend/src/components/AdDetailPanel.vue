<template>
  <div class="ad-detail-panel">
    <!-- Empty state -->
    <div v-if="!ad" class="empty-state">
      <div class="empty-icon">👆</div>
      <h3>Select an Ad</h3>
      <p>Click on an ad to view its details</p>
    </div>

    <!-- Loading state -->
    <div v-else-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Loading details...</p>
    </div>

    <!-- Ad details -->
    <template v-else>
      <!-- Header -->
      <div class="detail-header">
        <div class="page-info">
          <h2 class="page-name">{{ ad.page?.name || ad.page_name }}</h2>
          <span v-if="ad.page?.verified" class="verified-badge">✓ Verified</span>
        </div>
        <button
          class="save-btn"
          :class="{ active: isSaved }"
          @click="$emit('toggle-save', ad)"
        >
          {{ isSaved ? '★ Saved' : '☆ Save' }}
        </button>
      </div>

      <!-- Media with Creative Carousel -->
      <div class="detail-media" v-if="hasMedia">
        <CreativeCarousel
          :creatives="ad.media?.creatives || ad.creatives || []"
          :thumbnail-url="ad.media?.thumbnail_url || ad.thumbnail_url"
          :alt="ad.page?.name || ad.page_name"
        />
      </div>

      <!-- Content -->
      <div class="detail-content">
        <h3 v-if="ad.content?.headline || ad.headline" class="headline">
          {{ ad.content?.headline || ad.headline }}
        </h3>
        <p class="body-text">{{ ad.content?.body || ad.body || 'No body text' }}</p>

        <div class="cta-section" v-if="formattedCTA">
          <span class="cta-label">CTA:</span>
          <span class="cta-badge">{{ formattedCTA }}</span>
        </div>

        <a
          v-if="ad.content?.landing_url || ad.landing_url"
          :href="ad.content?.landing_url || ad.landing_url"
          target="_blank"
          class="landing-link"
        >
          🔗 View Landing Page
        </a>
      </div>

      <!-- Stats -->
      <div class="detail-stats">
        <div class="stat-item">
          <span class="stat-label">Days Active</span>
          <span class="stat-value">{{ ad.timing?.days_active || ad.days_active || 0 }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">Status</span>
          <span class="stat-value" :class="ad.timing?.is_active || ad.is_active ? 'active' : 'inactive'">
            {{ (ad.timing?.is_active || ad.is_active) ? 'Active' : 'Inactive' }}
          </span>
        </div>
        <div class="stat-item">
          <span class="stat-label">Start Date</span>
          <span class="stat-value">{{ formatDate(ad.timing?.start_date || ad.start_date) }}</span>
        </div>
        <div class="stat-item" v-if="ad.timing?.end_date || ad.end_date">
          <span class="stat-label">End Date</span>
          <span class="stat-value">{{ formatDate(ad.timing?.end_date || ad.end_date) }}</span>
        </div>
      </div>

      <!-- Platforms -->
      <div class="detail-platforms">
        <span class="section-label">Platforms</span>
        <div class="platform-list">
          <span
            v-for="platform in (ad.platforms || [])"
            :key="platform"
            class="platform-tag"
          >
            {{ platformLabel(platform) }}
          </span>
        </div>
      </div>

      <!-- Notes (if saved) -->
      <div class="detail-notes" v-if="isSaved">
        <span class="section-label">Notes</span>
        <textarea
          class="notes-input"
          v-model="notes"
          placeholder="Add notes about this ad..."
          @blur="saveNotes"
        ></textarea>

        <div class="tags-section">
          <span class="section-label">Tags</span>
          <div class="tags-list">
            <span
              v-for="tag in tags"
              :key="tag"
              class="tag"
              @click="removeTag(tag)"
            >
              {{ tag }} ×
            </span>
            <input
              type="text"
              class="tag-input"
              v-model="newTag"
              placeholder="Add tag..."
              @keyup.enter="addTag"
            />
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div class="detail-actions">
        <button
          v-if="relatedCount > 0"
          class="btn btn-ghost related-btn"
          @click="$emit('view-related', ad)"
        >
          🎯 View {{ relatedCount }} Other Campaign{{ relatedCount !== 1 ? 's' : '' }}
        </button>
        <a
          v-if="ad.media?.snapshot_url || ad.snapshot_url"
          :href="ad.media?.snapshot_url || ad.snapshot_url"
          target="_blank"
          class="btn btn-primary"
        >
          🔍 View Full Ad on Meta
        </a>
      </div>

      <!-- Note about images (only show if button is visible) -->
      <div v-if="ad.media?.snapshot_url || ad.snapshot_url" class="meta-note">
        <small>💡 Tip: Click "View Full Ad on Meta" to see the actual ad creative with images and videos.</small>
      </div>

      <!-- Variant Analysis (show if 5+ variants exist) -->
      <VariantAnalysis
        v-if="ad.variant_count >= 5"
        :niche-slug="nicheSlug"
        :ad-id="ad.id"
      />
    </template>
  </div>
</template>

<script setup>
  import { ref, computed, watch } from 'vue'
  import VariantAnalysis from './VariantAnalysis.vue'
  import CreativeCarousel from './CreativeCarousel.vue'

  const props = defineProps({
    ad: {
      type: Object,
      default: null
    },
    loading: {
      type: Boolean,
      default: false
    },
    relatedCount: {
      type: Number,
      default: 0
    },
    nicheSlug: {
      type: String,
      required: true
    }
  })

  const emit = defineEmits(['toggle-save', 'update-notes', 'view-related'])

  const notes = ref('')
  const tags = ref([])
  const newTag = ref('')

  const isSaved = computed(() => {
    return props.ad?.saved?.is_saved || props.ad?.is_saved || false
  })

  const hasMedia = computed(() => {
    const creatives = props.ad?.media?.creatives || props.ad?.creatives || []
    const thumbnail = props.ad?.media?.thumbnail_url || props.ad?.thumbnail_url
    return creatives.length > 0 || thumbnail
  })

  const formattedCTA = computed(() => {
    // Force reactivity by accessing ad.id
    const adId = props.ad?.id
    if (!adId) return null

    const cta = props.ad?.content?.cta || props.ad?.cta
    if (!cta) return null

    // Convert to Title Case (handles both "learn more" and "learn_more")
    return cta
      .split(/[_\s]+/)
      .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(' ')
  })

  watch(
    () => props.ad?.id,
    (newId) => {
      if (newId && props.ad) {
        notes.value = props.ad.saved?.notes || ''
        tags.value = props.ad.saved?.tags || []
      }
    },
    { immediate: true }
  )

  function formatDate(dateStr) {
    if (!dateStr) return 'N/A'
    try {
      return new Date(dateStr).toLocaleDateString()
    } catch {
      return dateStr
    }
  }

  function platformLabel(platform) {
    const labels = {
      facebook: '📘 Facebook',
      instagram: '📷 Instagram',
      messenger: '💬 Messenger',
      audience_network: '🌐 Audience Network'
    }
    return labels[platform] || platform
  }

  function saveNotes() {
    if (props.ad && isSaved.value) {
      emit('update-notes', { notes: notes.value, tags: tags.value })
    }
  }

  function addTag() {
    const tag = newTag.value.trim().toLowerCase()
    if (tag && !tags.value.includes(tag)) {
      tags.value.push(tag)
      newTag.value = ''
      saveNotes()
    }
  }

  function removeTag(tag) {
    tags.value = tags.value.filter((t) => t !== tag)
    saveNotes()
  }
</script>

<style lang="scss" scoped>
  .ad-detail-panel {
    height: 100%;
    overflow-y: auto;
  }

  .empty-state,
  .loading-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    text-align: center;
    color: var(--color-text-secondary);
  }

  .empty-icon {
    font-size: 3rem;
    margin-bottom: var(--spacing-3);
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

  .detail-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    margin-bottom: var(--spacing-4);
  }

  .page-name {
    font-size: var(--font-size-xl);
    font-weight: 600;
    margin: 0;
  }

  .verified-badge {
    display: inline-block;
    font-size: var(--font-size-xs);
    color: var(--color-primary-600);
    margin-top: var(--spacing-1);
  }

  .save-btn {
    padding: var(--spacing-2) var(--spacing-3);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    background-color: var(--color-bg-primary);
    cursor: pointer;
    transition: all var(--transition-fast);

    &:hover,
    &.active {
      background-color: var(--color-warning-50);
      border-color: var(--color-warning-500);
      color: var(--color-warning-700);
    }
  }

  .detail-media {
    margin-bottom: var(--spacing-4);
    border-radius: var(--radius-md);
    overflow: hidden;

    img {
      width: 100%;
      display: block;
    }
  }

  .detail-content {
    margin-bottom: var(--spacing-4);
    padding-bottom: var(--spacing-4);
    border-bottom: 1px solid var(--color-border);
  }

  .headline {
    font-size: var(--font-size-lg);
    font-weight: 600;
    margin: 0 0 var(--spacing-2) 0;
  }

  .body-text {
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
    line-height: 1.6;
    margin: 0 0 var(--spacing-3) 0;
    white-space: pre-wrap;
  }

  .cta-section {
    display: flex;
    align-items: center;
    gap: var(--spacing-2);
    margin-bottom: var(--spacing-3);

    .cta-label {
      font-size: var(--font-size-sm);
      color: var(--color-text-secondary);
      font-weight: 500;
    }

    .cta-badge {
      font-size: var(--font-size-sm);
      font-weight: 600;
      color: var(--color-success-700);
      background-color: var(--color-success-50);
      padding: var(--spacing-1) var(--spacing-2);
      border-radius: var(--radius-md);
      border: 1px solid var(--color-success-200);
    }
  }

  .landing-link {
    display: inline-block;
    font-size: var(--font-size-sm);
    color: var(--color-primary-600);
    text-decoration: none;

    &:hover {
      text-decoration: underline;
    }
  }

  .detail-stats {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: var(--spacing-3);
    margin-bottom: var(--spacing-4);
  }

  .stat-item {
    .stat-label {
      display: block;
      font-size: var(--font-size-xs);
      color: var(--color-text-secondary);
      margin-bottom: var(--spacing-1);
    }

    .stat-value {
      font-weight: 600;

      &.active {
        color: var(--color-success-600);
      }

      &.inactive {
        color: var(--color-gray-500);
      }
    }
  }

  .section-label {
    display: block;
    font-size: var(--font-size-sm);
    font-weight: 500;
    color: var(--color-text-secondary);
    margin-bottom: var(--spacing-2);
  }

  .detail-platforms {
    margin-bottom: var(--spacing-4);
  }

  .platform-list {
    display: flex;
    flex-wrap: wrap;
    gap: var(--spacing-2);
  }

  .platform-tag {
    font-size: var(--font-size-sm);
    padding: var(--spacing-1) var(--spacing-2);
    background-color: var(--color-gray-100);
    border-radius: var(--radius-sm);
  }

  .detail-notes {
    margin-bottom: var(--spacing-4);
    padding: var(--spacing-3);
    background-color: var(--color-warning-50);
    border-radius: var(--radius-md);
  }

  .notes-input {
    width: 100%;
    min-height: 80px;
    padding: var(--spacing-2);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    font-size: var(--font-size-sm);
    resize: vertical;
    margin-bottom: var(--spacing-3);
  }

  .tags-section {
    margin-top: var(--spacing-2);
  }

  .tags-list {
    display: flex;
    flex-wrap: wrap;
    gap: var(--spacing-1);
  }

  .tag {
    font-size: var(--font-size-xs);
    padding: var(--spacing-1) var(--spacing-2);
    background-color: var(--color-primary-100);
    color: var(--color-primary-700);
    border-radius: var(--radius-full);
    cursor: pointer;

    &:hover {
      background-color: var(--color-primary-200);
    }
  }

  .tag-input {
    flex: 1;
    min-width: 80px;
    padding: var(--spacing-1) var(--spacing-2);
    border: 1px dashed var(--color-border);
    border-radius: var(--radius-full);
    font-size: var(--font-size-xs);

    &:focus {
      outline: none;
      border-color: var(--color-primary-500);
    }
  }

  .detail-actions {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-2);
  }

  .related-btn {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: var(--spacing-2);
  }

  .related-count {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 20px;
    height: 20px;
    padding: 0 var(--spacing-1);
    font-size: var(--font-size-xs);
    font-weight: 600;
    color: white;
    background-color: var(--color-primary-500);
    border-radius: var(--radius-full);
  }

  .meta-note {
    padding: var(--spacing-3);
    border-radius: var(--radius-md);
    font-size: var(--font-size-sm);
    line-height: 1.5;
    margin-top: var(--spacing-3);
    background-color: var(--color-primary-50);
    border-left: 3px solid var(--color-primary-500);
    color: var(--color-text-secondary);
  }
</style>
