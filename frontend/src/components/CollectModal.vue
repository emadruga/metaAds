<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal">
      <div class="modal-header">
        <h2>Collect Ads</h2>
        <button class="close-btn" @click="$emit('close')">&times;</button>
      </div>

      <div class="modal-body">
        <p class="modal-description">
          Fetch ads from Meta Ad Library for this niche.
        </p>

        <!-- Keyword selection -->
        <div class="form-group">
          <label class="form-label">Keyword</label>
          <select v-model="selectedKeyword" class="form-select">
            <option v-for="kw in keywords" :key="kw" :value="kw">{{ kw }}</option>
            <option value="_custom">Custom keyword...</option>
          </select>
        </div>

        <!-- Custom keyword input -->
        <div v-if="selectedKeyword === '_custom'" class="form-group">
          <label class="form-label">Custom Keyword</label>
          <input
            v-model="customKeyword"
            type="text"
            class="form-input"
            placeholder="Enter search keyword"
          />
        </div>

        <!-- Limit -->
        <div class="form-group">
          <label class="form-label">Max Ads to Collect</label>
          <select v-model="limit" class="form-select">
            <option :value="25">25 ads</option>
            <option :value="50">50 ads</option>
            <option :value="100">100 ads</option>
            <option :value="200">200 ads</option>
          </select>
        </div>

        <!-- Error message -->
        <div v-if="error" class="error-message">
          <strong>❌ Collection Failed</strong><br />
          {{ error }}
        </div>

        <!-- Progress indicator -->
        <div v-if="collecting" class="progress-message">
          <div class="progress-spinner-large"></div>
          <div class="progress-text">
            <strong>Collecting ads from Meta Ad Library...</strong>
            <p>Fetching up to {{ limit }} ads for "{{ effectiveKeyword }}"</p>
            <p class="progress-note">This may take 10-30 seconds.</p>
          </div>
        </div>

        <!-- Success message -->
        <div v-if="result" class="success-message">
          <div class="success-icon">✅</div>
          <strong>Collection Complete!</strong><br />
          Collected <strong>{{ result.ads_collected }}</strong> ads
          (<strong>{{ result.ads_new }}</strong> new, <strong>{{ result.ads_updated }}</strong> updated)
          <p v-if="result.message" class="result-detail">{{ result.message }}</p>
        </div>
      </div>

      <div class="modal-footer">
        <button class="btn btn-ghost" @click="$emit('close')" :disabled="collecting">
          {{ result ? 'Close' : 'Cancel' }}
        </button>
        <button
          v-if="!result"
          class="btn btn-primary"
          @click="startCollection"
          :disabled="collecting || !effectiveKeyword"
        >
          <span v-if="collecting" class="spinner"></span>
          {{ collecting ? 'Collecting...' : 'Start Collection' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { nicheApi } from '@/services/api'

const props = defineProps({
  nicheSlug: {
    type: String,
    required: true
  },
  keywords: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['close', 'collected'])

const selectedKeyword = ref(props.keywords[0] || '_custom')
const customKeyword = ref('')
const limit = ref(50)
const collecting = ref(false)
const error = ref(null)
const result = ref(null)

const effectiveKeyword = computed(() => {
  if (selectedKeyword.value === '_custom') {
    return customKeyword.value.trim()
  }
  return selectedKeyword.value
})

async function startCollection() {
  if (!effectiveKeyword.value) {
    error.value = 'Please enter a keyword'
    return
  }

  collecting.value = true
  error.value = null
  result.value = null

  try {
    const response = await nicheApi.collect(props.nicheSlug, {
      keyword: effectiveKeyword.value,
      limit: limit.value
    })

    result.value = response.data.data
    emit('collected', result.value)
  } catch (err) {
    console.error('Collection failed:', err)
    error.value = err.response?.data?.error || err.message || 'Collection failed'
  } finally {
    collecting.value = false
  }
}
</script>

<style lang="scss" scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background-color: var(--color-bg-primary);
  border-radius: var(--radius-xl);
  width: 100%;
  max-width: 480px;
  max-height: 90vh;
  overflow: hidden;
  box-shadow: var(--shadow-xl);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-4) var(--spacing-6);
  border-bottom: 1px solid var(--color-border);

  h2 {
    margin: 0;
    font-size: var(--font-size-lg);
    font-weight: 600;
  }
}

.close-btn {
  background: none;
  border: none;
  font-size: var(--font-size-2xl);
  color: var(--color-text-secondary);
  cursor: pointer;
  padding: 0;
  line-height: 1;

  &:hover {
    color: var(--color-text-primary);
  }
}

.modal-body {
  padding: var(--spacing-6);
}

.modal-description {
  color: var(--color-text-secondary);
  margin: 0 0 var(--spacing-4) 0;
}

.form-group {
  margin-bottom: var(--spacing-4);
}

.form-label {
  display: block;
  font-size: var(--font-size-sm);
  font-weight: 500;
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-1);
}

.form-input,
.form-select {
  width: 100%;
  padding: var(--spacing-2) var(--spacing-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: var(--font-size-base);
  background-color: var(--color-bg-primary);
  color: var(--color-text-primary);

  &:focus {
    outline: none;
    border-color: var(--color-primary-500);
  }
}

.error-message {
  padding: var(--spacing-3);
  background-color: var(--color-error-50);
  border: 1px solid var(--color-error-200);
  border-radius: var(--radius-md);
  color: var(--color-error-700);
  font-size: var(--font-size-sm);
}

.success-message {
  padding: var(--spacing-4);
  background-color: var(--color-success-50);
  border: 1px solid var(--color-success-200);
  border-radius: var(--radius-md);
  color: var(--color-success-700);
  font-size: var(--font-size-sm);
  text-align: center;

  .success-icon {
    font-size: var(--font-size-3xl);
    margin-bottom: var(--spacing-2);
  }

  strong {
    font-size: var(--font-size-base);
  }

  .result-detail {
    margin-top: var(--spacing-2);
    font-size: var(--font-size-xs);
    opacity: 0.8;
  }
}

.progress-message {
  padding: var(--spacing-4);
  background-color: var(--color-primary-50);
  border: 1px solid var(--color-primary-200);
  border-radius: var(--radius-md);
  text-align: center;

  .progress-spinner-large {
    display: inline-block;
    width: 40px;
    height: 40px;
    border: 4px solid var(--color-primary-200);
    border-top-color: var(--color-primary-600);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
    margin-bottom: var(--spacing-3);
  }

  .progress-text {
    color: var(--color-primary-700);

    strong {
      display: block;
      font-size: var(--font-size-base);
      margin-bottom: var(--spacing-2);
    }

    p {
      margin: var(--spacing-1) 0;
      font-size: var(--font-size-sm);
    }

    .progress-note {
      font-size: var(--font-size-xs);
      opacity: 0.7;
    }
  }
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-2);
  padding: var(--spacing-4) var(--spacing-6);
  border-top: 1px solid var(--color-border);
  background-color: var(--color-bg-secondary);
}

.spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid currentColor;
  border-right-color: transparent;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
  margin-right: var(--spacing-2);
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
