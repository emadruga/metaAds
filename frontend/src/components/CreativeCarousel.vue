<template>
  <div class="creative-carousel" @click.stop>
    <!-- Single creative or empty state -->
    <template v-if="allCreatives.length <= 1">
      <div class="single-creative">
        <img
          v-if="allCreatives[0]?.url"
          :src="allCreatives[0].url"
          :alt="alt"
          @error="handleImageError"
        />
        <div v-else class="placeholder">
          <span>📷</span>
        </div>
      </div>
    </template>

    <!-- Multiple creatives carousel -->
    <template v-else>
      <div
        class="carousel-container"
        ref="carouselRef"
        @touchstart="handleTouchStart"
        @touchmove="handleTouchMove"
        @touchend="handleTouchEnd"
      >
        <div
          class="carousel-track"
          :style="{ transform: `translateX(${translateX}px)` }"
        >
          <div
            v-for="(creative, index) in allCreatives"
            :key="index"
            class="carousel-slide"
            :style="{ width: `${slideWidth}px` }"
          >
            <img
              v-if="creative.type !== 'video'"
              :src="creative.url"
              :alt="`${alt} - ${index + 1}`"
              @error="handleImageError"
            />
            <div v-else class="video-placeholder">
              <span class="video-icon">▶️</span>
              <span class="video-label">Video</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Navigation arrows -->
      <button
        v-if="currentIndex > 0"
        class="nav-arrow nav-prev"
        @click.stop="goToPrev"
      >
        ‹
      </button>
      <button
        v-if="currentIndex < allCreatives.length - 1"
        class="nav-arrow nav-next"
        @click.stop="goToNext"
      >
        ›
      </button>

      <!-- Dot indicators -->
      <div class="carousel-dots">
        <span
          v-for="(_, index) in allCreatives"
          :key="index"
          class="dot"
          :class="{ active: index === currentIndex }"
          @click.stop="goToIndex(index)"
        ></span>
      </div>

      <!-- Counter badge -->
      <div class="counter-badge">
        {{ currentIndex + 1 }}/{{ allCreatives.length }}
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  // Array of creative objects: [{url: string, type: 'image'|'video'}]
  creatives: {
    type: Array,
    default: () => []
  },
  // Fallback thumbnail URL
  thumbnailUrl: {
    type: String,
    default: null
  },
  // Alt text for images
  alt: {
    type: String,
    default: 'Ad creative'
  }
})

const carouselRef = ref(null)
const currentIndex = ref(0)
const slideWidth = ref(280)
const translateX = ref(0)

// Touch handling
let touchStartX = 0
let touchCurrentX = 0
let isDragging = false

// Combine creatives with fallback thumbnail
const allCreatives = computed(() => {
  if (props.creatives && props.creatives.length > 0) {
    return props.creatives
  }
  // Fallback to thumbnail if no creatives
  if (props.thumbnailUrl) {
    return [{ url: props.thumbnailUrl, type: 'image' }]
  }
  return []
})

// Update slide width based on container
function updateSlideWidth() {
  if (carouselRef.value) {
    slideWidth.value = carouselRef.value.offsetWidth
    updateTranslateX()
  }
}

function updateTranslateX() {
  translateX.value = -currentIndex.value * slideWidth.value
}

function goToIndex(index) {
  if (index >= 0 && index < allCreatives.value.length) {
    currentIndex.value = index
    updateTranslateX()
  }
}

function goToNext() {
  if (currentIndex.value < allCreatives.value.length - 1) {
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
}

function handleTouchMove(e) {
  if (!isDragging) return
  touchCurrentX = e.touches[0].clientX
  const diff = touchCurrentX - touchStartX
  // Live dragging effect (limited)
  const baseTranslate = -currentIndex.value * slideWidth.value
  translateX.value = baseTranslate + Math.max(-50, Math.min(50, diff * 0.5))
}

function handleTouchEnd() {
  if (!isDragging) return
  isDragging = false

  const diff = touchCurrentX - touchStartX
  const threshold = 30

  if (diff > threshold) {
    goToPrev()
  } else if (diff < -threshold) {
    goToNext()
  } else {
    updateTranslateX()
  }
}

function handleImageError(e) {
  e.target.src = ''
  e.target.style.display = 'none'
}

// Reset index when creatives change
watch(() => props.creatives, () => {
  currentIndex.value = 0
  updateTranslateX()
})

onMounted(() => {
  updateSlideWidth()
  window.addEventListener('resize', updateSlideWidth)
})

onUnmounted(() => {
  window.removeEventListener('resize', updateSlideWidth)
})
</script>

<style lang="scss" scoped>
.creative-carousel {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
  background-color: var(--color-gray-100);
}

.single-creative {
  width: 100%;
  height: 100%;

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .placeholder {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2rem;
    color: var(--color-gray-400);
  }
}

.carousel-container {
  width: 100%;
  height: 100%;
  overflow: hidden;
  touch-action: pan-y;
}

.carousel-track {
  display: flex;
  height: 100%;
  transition: transform 0.25s ease-out;
}

.carousel-slide {
  flex-shrink: 0;
  height: 100%;

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
}

.video-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--color-gray-200), var(--color-gray-300));

  .video-icon {
    font-size: 2rem;
    margin-bottom: var(--spacing-1);
  }

  .video-label {
    font-size: var(--font-size-xs);
    color: var(--color-text-secondary);
  }
}

/* Navigation arrows */
.nav-arrow {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 24px;
  height: 24px;
  border: none;
  border-radius: 50%;
  background-color: rgba(255, 255, 255, 0.9);
  color: var(--color-text-primary);
  font-size: 1rem;
  font-weight: bold;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  transition: all var(--transition-fast);
  z-index: 2;

  &:hover {
    background-color: white;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
  }

  &.nav-prev {
    left: 4px;
  }

  &.nav-next {
    right: 4px;
  }
}

/* Dot indicators */
.carousel-dots {
  position: absolute;
  bottom: 6px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 4px;
  z-index: 2;
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: rgba(255, 255, 255, 0.5);
  cursor: pointer;
  transition: all var(--transition-fast);

  &.active {
    background-color: white;
    transform: scale(1.2);
  }

  &:hover:not(.active) {
    background-color: rgba(255, 255, 255, 0.8);
  }
}

/* Counter badge */
.counter-badge {
  position: absolute;
  top: 6px;
  right: 6px;
  padding: 2px 6px;
  font-size: 10px;
  font-weight: 600;
  color: white;
  background-color: rgba(0, 0, 0, 0.6);
  border-radius: var(--radius-sm);
  z-index: 2;
}
</style>
