<template>
  <div class="ad-carousel-container">
    <!-- Loading state -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Loading ads...</p>
    </div>

    <!-- Empty state -->
    <div v-else-if="ads.length === 0" class="empty-state">
      <div class="empty-icon">📭</div>
      <h3>No ads found</h3>
      <p>{{ emptyMessage }}</p>
      <button v-if="showCollectButton" class="btn btn-primary collect-cta" @click="$emit('collect')">
        📥 Collect Ads Now
      </button>
    </div>

    <!-- Carousel -->
    <template v-else>
      <!-- Navigation header -->
      <div class="carousel-header">
        <span class="carousel-counter">{{ currentIndex + 1 }} / {{ ads.length }}</span>
        <div class="carousel-nav-buttons">
          <button
            class="nav-btn"
            :disabled="currentIndex === 0"
            @click="goToPrev"
          >
            ← Prev
          </button>
          <button
            class="nav-btn"
            :disabled="currentIndex === ads.length - 1"
            @click="goToNext"
          >
            Next →
          </button>
        </div>
      </div>

      <!-- Swipeable card container -->
      <div
        class="carousel-track"
        ref="trackRef"
        @touchstart="handleTouchStart"
        @touchmove="handleTouchMove"
        @touchend="handleTouchEnd"
      >
        <div
          class="carousel-card"
          :style="{ transform: `translateX(${translateX}px)` }"
        >
          <!-- Current Ad Card (larger display) -->
          <div class="featured-card" :class="{ saved: currentAd?.is_saved }">
            <!-- Thumbnail with Creative Carousel - larger for mobile -->
            <div class="card-thumbnail">
              <CreativeCarousel
                :creatives="currentAd?.creatives || []"
                :thumbnail-url="currentAd?.thumbnail_url"
                :alt="currentAd?.page_name"
              />
              <div class="ad-platforms">
                <span v-for="platform in currentAd?.platforms" :key="platform" class="platform-badge">
                  {{ platformIcon(platform) }}
                </span>
              </div>
              <span class="status-badge" :class="currentAd?.is_active ? 'active' : 'inactive'">
                {{ currentAd?.is_active ? 'Active' : 'Inactive' }}
              </span>
            </div>

            <!-- Content -->
            <div class="card-content">
              <div class="card-header">
                <span class="page-name">{{ currentAd?.page_name }}</span>
                <button
                  class="save-btn"
                  :class="{ active: currentAd?.is_saved }"
                  @click="$emit('toggle-save', currentAd)"
                  :title="currentAd?.is_saved ? 'Unsave' : 'Save'"
                >
                  {{ currentAd?.is_saved ? '★' : '☆' }}
                </button>
              </div>

              <p class="card-body" v-if="currentAd?.body">{{ truncatedBody }}</p>

              <div class="card-meta">
                <span class="meta-item" v-if="currentAd?.days_active">
                  <span class="meta-icon">📅</span>
                  {{ currentAd.days_active }} days active
                </span>
                <span class="meta-item" v-if="currentAd?.cta">
                  <span class="meta-icon">🔗</span>
                  {{ currentAd.cta }}
                </span>
              </div>

              <!-- Action buttons -->
              <div class="card-actions">
                <button class="btn btn-primary" @click="$emit('select', currentAd)">
                  View Details
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Swipe hint -->
      <div class="swipe-hint" v-if="showSwipeHint">
        <span>👆 Swipe left or right to navigate</span>
      </div>

      <!-- Dot indicators -->
      <div class="carousel-dots" v-if="ads.length <= 10">
        <span
          v-for="(ad, index) in ads"
          :key="ad.id"
          class="dot"
          :class="{ active: index === currentIndex, saved: ad.is_saved }"
          @click="goToIndex(index)"
        ></span>
      </div>

      <!-- Progress bar for many ads -->
      <div class="carousel-progress" v-else>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: `${((currentIndex + 1) / ads.length) * 100}%` }"></div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import CreativeCarousel from './CreativeCarousel.vue'

const props = defineProps({
  ads: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  selectedAdId: {
    type: String,
    default: null
  },
  emptyMessage: {
    type: String,
    default: 'Try adjusting your search filters.'
  },
  showCollectButton: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['select', 'toggle-save', 'collect'])

const currentIndex = ref(0)
const translateX = ref(0)
const trackRef = ref(null)
const showSwipeHint = ref(true)

// Touch handling
let touchStartX = 0
let touchCurrentX = 0
let isDragging = false

const currentAd = computed(() => props.ads[currentIndex.value])

const truncatedBody = computed(() => {
  if (!currentAd.value?.body) return ''
  return currentAd.value.body.length > 150
    ? currentAd.value.body.substring(0, 150) + '...'
    : currentAd.value.body
})

// Reset index when ads change
watch(() => props.ads, () => {
  currentIndex.value = 0
  translateX.value = 0
})

// Sync with selected ad
watch(() => props.selectedAdId, (newId) => {
  if (newId) {
    const index = props.ads.findIndex(ad => ad.id === newId)
    if (index !== -1) {
      currentIndex.value = index
    }
  }
})

function goToIndex(index) {
  if (index >= 0 && index < props.ads.length) {
    currentIndex.value = index
    translateX.value = 0
    showSwipeHint.value = false
  }
}

function goToNext() {
  if (currentIndex.value < props.ads.length - 1) {
    goToIndex(currentIndex.value + 1)
  }
}

function goToPrev() {
  if (currentIndex.value > 0) {
    goToIndex(currentIndex.value - 1)
  }
}

function handleTouchStart(e) {
  touchStartX = e.touches[0].clientX
  touchCurrentX = touchStartX
  isDragging = true
  showSwipeHint.value = false
}

function handleTouchMove(e) {
  if (!isDragging) return
  touchCurrentX = e.touches[0].clientX
  const diff = touchCurrentX - touchStartX
  // Limit the drag distance
  translateX.value = Math.max(-100, Math.min(100, diff))
}

function handleTouchEnd() {
  if (!isDragging) return
  isDragging = false

  const diff = touchCurrentX - touchStartX
  const threshold = 50

  if (diff > threshold && currentIndex.value > 0) {
    // Swipe right - go to previous
    goToPrev()
  } else if (diff < -threshold && currentIndex.value < props.ads.length - 1) {
    // Swipe left - go to next
    goToNext()
  } else {
    // Snap back
    translateX.value = 0
  }
}

function platformIcon(platform) {
  const icons = {
    facebook: '📘',
    instagram: '📷',
    messenger: '💬',
    audience_network: '🌐'
  }
  return icons[platform] || '📱'
}

// Hide swipe hint after a few seconds
onMounted(() => {
  setTimeout(() => {
    showSwipeHint.value = false
  }, 3000)
})
</script>

<style lang="scss" scoped>
.ad-carousel-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-8);
  text-align: center;
  color: var(--color-text-secondary);
  flex: 1;
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

.empty-icon {
  font-size: 3rem;
  margin-bottom: var(--spacing-3);
}

.empty-state h3 {
  margin: 0 0 var(--spacing-2) 0;
  color: var(--color-text-primary);
}

.empty-state p {
  margin: 0;
  font-size: var(--font-size-sm);
}

.collect-cta {
  margin-top: var(--spacing-4);
}

/* Carousel header */
.carousel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-3);
  background-color: var(--color-bg-secondary);
  border-bottom: 1px solid var(--color-border);
}

.carousel-counter {
  font-weight: 600;
  color: var(--color-text-primary);
}

.carousel-nav-buttons {
  display: flex;
  gap: var(--spacing-2);
}

.nav-btn {
  padding: var(--spacing-2) var(--spacing-3);
  font-size: var(--font-size-sm);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background-color: var(--color-bg-primary);
  cursor: pointer;
  transition: all var(--transition-fast);

  &:hover:not(:disabled) {
    background-color: var(--color-primary-50);
    border-color: var(--color-primary-300);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

/* Carousel track */
.carousel-track {
  flex: 1;
  overflow: hidden;
  touch-action: pan-y;
  padding: var(--spacing-4);
}

.carousel-card {
  transition: transform 0.2s ease-out;
  height: 100%;
}

/* Featured card (single ad display) */
.featured-card {
  background-color: var(--color-bg-primary);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  height: 100%;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-md);

  &.saved {
    border-color: var(--color-warning-500);
  }
}

.card-thumbnail {
  position: relative;
  height: 200px;
  background-color: var(--color-gray-100);
  flex-shrink: 0;

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
    font-size: 4rem;
    color: var(--color-gray-400);
  }

  .ad-platforms {
    position: absolute;
    top: var(--spacing-2);
    left: var(--spacing-2);
    display: flex;
    gap: var(--spacing-1);
  }

  .platform-badge {
    background-color: rgba(255, 255, 255, 0.9);
    padding: 4px 8px;
    border-radius: var(--radius-sm);
    font-size: var(--font-size-sm);
  }

  .status-badge {
    position: absolute;
    top: var(--spacing-2);
    right: var(--spacing-2);
    font-size: var(--font-size-xs);
    padding: 4px 10px;
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
}

.card-content {
  padding: var(--spacing-4);
  flex: 1;
  display: flex;
  flex-direction: column;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-3);
}

.page-name {
  font-weight: 600;
  font-size: var(--font-size-lg);
  color: var(--color-text-primary);
}

.save-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: var(--color-gray-400);
  transition: all var(--transition-fast);
  padding: var(--spacing-1);

  &:hover,
  &.active {
    color: var(--color-warning-500);
  }
}

.card-body {
  font-size: var(--font-size-base);
  color: var(--color-text-secondary);
  line-height: 1.5;
  margin: 0 0 var(--spacing-4) 0;
  flex: 1;
}

.card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-3);
  margin-bottom: var(--spacing-4);
}

.meta-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);

  .meta-icon {
    font-size: 1em;
  }
}

.card-actions {
  margin-top: auto;

  .btn {
    width: 100%;
    padding: var(--spacing-3);
    font-size: var(--font-size-base);
  }
}

/* Swipe hint */
.swipe-hint {
  text-align: center;
  padding: var(--spacing-2);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  animation: fadeInOut 3s ease-in-out;
}

@keyframes fadeInOut {
  0%, 100% { opacity: 0; }
  20%, 80% { opacity: 1; }
}

/* Dot indicators */
.carousel-dots {
  display: flex;
  justify-content: center;
  gap: var(--spacing-2);
  padding: var(--spacing-3);
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background-color: var(--color-gray-300);
  cursor: pointer;
  transition: all var(--transition-fast);

  &.active {
    background-color: var(--color-primary-500);
    transform: scale(1.2);
  }

  &.saved {
    border: 2px solid var(--color-warning-500);
  }
}

/* Progress bar for many ads */
.carousel-progress {
  padding: var(--spacing-3);
}

.progress-bar {
  height: 4px;
  background-color: var(--color-gray-200);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background-color: var(--color-primary-500);
  transition: width var(--transition-fast);
}
</style>
