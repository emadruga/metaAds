<template>
  <div class="variant-analysis">
    <div class="analysis-header">
      <h3>🔍 Variant Analysis</h3>
      <span class="variant-count">{{ totalVariants }} variants</span>
    </div>

    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>Analyzing variants...</p>
    </div>

    <div v-else-if="error" class="error">
      <p>{{ error }}</p>
    </div>

    <div v-else-if="analysis" class="analysis-content">
      <div v-if="analysis.differences.length === 0" class="no-differences">
        <p>All variants appear identical in text content.</p>
        <small>Differences may be in creative media (images/videos) which requires manual review.</small>
      </div>

      <div v-else class="differences-list">
        <div
          v-for="diff in analysis.differences"
          :key="diff.field"
          class="difference-item"
        >
          <div class="diff-header">
            <span class="diff-label">{{ diff.label }}</span>
            <span class="diff-count">{{ diff.variations_count }} variations</span>
          </div>
          <p class="diff-description">{{ diff.description }}</p>

          <div v-if="diff.values && diff.values.length > 0" class="diff-values">
            <details>
              <summary>Show examples ({{ diff.values.length }})</summary>
              <ul class="value-list">
                <li v-for="(value, index) in diff.values" :key="index" class="value-item">
                  <span class="value-number">{{ index + 1 }}.</span>
                  <span class="value-text">{{ truncate(value, 150) }}</span>
                </li>
              </ul>
            </details>
          </div>
        </div>
      </div>

      <div class="analysis-insights">
        <ul>
          <li v-if="hasTextVariations">
            Testing <strong>{{ textVariationsCount }} different text versions</strong> - analyze which performs best
          </li>
          <li v-if="hasCTAVariations">
            Experimenting with <strong>{{ ctaVariationsCount }} CTAs</strong> - track conversion rates
          </li>
          <li v-if="hasLengthVariations">
            Varying text length from <strong>{{ minLength }} to {{ maxLength }} characters</strong>
          </li>
          <li v-if="hasMediaVariations">
            <strong>{{ totalVariants }} creative variations</strong> - likely testing different images/videos
          </li>
        </ul>
      </div>

      <div class="variant-tip">
        💡 <strong>Tip:</strong> Expand the row in the table view (click the + button) to see all {{ totalVariants }} variants side-by-side.
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { adApi } from '@/services/api'

const props = defineProps({
  nicheSlug: {
    type: String,
    required: true
  },
  adId: {
    type: String,
    required: true
  }
})

const loading = ref(false)
const error = ref(null)
const analysis = ref(null)

const totalVariants = computed(() => analysis.value?.total_variants || 0)

const hasTextVariations = computed(() => {
  return analysis.value?.differences.some(d => d.field === 'body_text')
})

const textVariationsCount = computed(() => {
  const diff = analysis.value?.differences.find(d => d.field === 'body_text')
  return diff?.variations_count || 0
})

const hasCTAVariations = computed(() => {
  return analysis.value?.differences.some(d => d.field === 'cta')
})

const ctaVariationsCount = computed(() => {
  const diff = analysis.value?.differences.find(d => d.field === 'cta')
  return diff?.variations_count || 0
})

const hasLengthVariations = computed(() => {
  return analysis.value?.differences.some(d => d.field === 'body_length')
})

const minLength = computed(() => {
  const diff = analysis.value?.differences.find(d => d.field === 'body_length')
  if (!diff) return 0
  const match = diff.description.match(/from (\d+) to/)
  return match ? parseInt(match[1]) : 0
})

const maxLength = computed(() => {
  const diff = analysis.value?.differences.find(d => d.field === 'body_length')
  if (!diff) return 0
  const match = diff.description.match(/to (\d+) characters/)
  return match ? parseInt(match[1]) : 0
})

const hasMediaVariations = computed(() => {
  return analysis.value?.differences.some(d => d.field === 'media')
})

async function loadAnalysis() {
  loading.value = true
  error.value = null

  try {
    const response = await adApi.variantAnalysis(props.nicheSlug, props.adId)
    analysis.value = response.data.data
  } catch (err) {
    error.value = 'Failed to load variant analysis'
    console.error('Variant analysis error:', err)
  } finally {
    loading.value = false
  }
}

function truncate(text, maxLength) {
  if (!text || text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

watch(() => props.adId, () => {
  if (props.adId) {
    loadAnalysis()
  }
}, { immediate: true })
</script>

<style lang="scss" scoped>
.variant-analysis {
  background-color: var(--color-bg-secondary);
  border-radius: var(--radius-lg);
  padding: var(--spacing-4);
  margin-top: var(--spacing-4);
}

.analysis-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-3);

  h3 {
    margin: 0;
    font-size: var(--font-size-lg);
    font-weight: 600;
  }

  .variant-count {
    background-color: var(--color-primary-100);
    color: var(--color-primary-700);
    padding: var(--spacing-1) var(--spacing-2);
    border-radius: var(--radius-full);
    font-size: var(--font-size-sm);
    font-weight: 600;
  }
}

.loading, .error, .no-differences {
  text-align: center;
  padding: var(--spacing-4);
  color: var(--color-text-secondary);
}

.spinner {
  width: 30px;
  height: 30px;
  border: 3px solid var(--color-gray-200);
  border-top-color: var(--color-primary-500);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto var(--spacing-2);
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error {
  color: var(--color-error-600);
}

.differences-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
}

.difference-item {
  background-color: var(--color-bg-primary);
  border-radius: var(--radius-md);
  padding: var(--spacing-3);
  border-left: 3px solid var(--color-primary-500);
}

.diff-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-1);

  .diff-label {
    font-weight: 600;
    color: var(--color-text-primary);
  }

  .diff-count {
    background-color: var(--color-gray-100);
    padding: 2px var(--spacing-2);
    border-radius: var(--radius-full);
    font-size: var(--font-size-xs);
    color: var(--color-text-secondary);
  }
}

.diff-description {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  margin: 0 0 var(--spacing-2) 0;
}

.diff-values {
  margin-top: var(--spacing-2);

  details {
    summary {
      cursor: pointer;
      font-size: var(--font-size-sm);
      color: var(--color-primary-600);
      user-select: none;

      &:hover {
        text-decoration: underline;
      }
    }
  }

  .value-list {
    list-style: none;
    padding: 0;
    margin: var(--spacing-2) 0 0 0;
    max-height: 300px;
    overflow-y: auto;
  }

  .value-item {
    display: flex;
    gap: var(--spacing-2);
    padding: var(--spacing-2);
    font-size: var(--font-size-sm);
    border-bottom: 1px solid var(--color-border);

    &:last-child {
      border-bottom: none;
    }

    .value-number {
      color: var(--color-text-secondary);
      font-weight: 600;
      min-width: 24px;
    }

    .value-text {
      color: var(--color-text-primary);
      line-height: 1.5;
    }
  }
}

.analysis-insights {
  margin-top: var(--spacing-4);
  padding: var(--spacing-3);
  background-color: var(--color-primary-50);
  border-radius: var(--radius-md);

  ul {
    list-style: none;
    padding: 0;
    margin: 0;

    li {
      padding: var(--spacing-1) 0;
      color: var(--color-text-primary);
      font-size: var(--font-size-sm);

      &:before {
        content: '•';
        color: var(--color-primary-600);
        font-weight: bold;
        margin-right: var(--spacing-2);
      }
    }
  }
}

.variant-tip {
  margin-top: var(--spacing-3);
  padding: var(--spacing-3);
  background-color: var(--color-primary-50);
  border-left: 3px solid var(--color-primary-500);
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: 1.5;
}

.no-differences {
  padding: var(--spacing-3);

  p {
    margin: 0 0 var(--spacing-1) 0;
    color: var(--color-text-primary);
  }

  small {
    color: var(--color-text-secondary);
    font-size: var(--font-size-xs);
  }
}
</style>
