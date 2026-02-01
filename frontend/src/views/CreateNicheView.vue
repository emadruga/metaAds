<template>
  <div class="create-niche">
    <header class="page-header">
      <router-link to="/" class="back-link">
        ← Back to Niches
      </router-link>
      <h1>Create New Niche</h1>
    </header>

    <main class="page-main">
      <form @submit.prevent="handleSubmit" class="niche-form card">
        <div class="form-group">
          <label for="name">Niche Name *</label>
          <input
            id="name"
            v-model="form.name"
            type="text"
            class="input"
            placeholder="e.g., Video Editing Apps"
            required
          />
        </div>

        <div class="form-group">
          <label for="description">Description</label>
          <textarea
            id="description"
            v-model="form.description"
            class="input"
            placeholder="Optional description for this niche"
            rows="3"
          ></textarea>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label for="icon">Icon</label>
            <input
              id="icon"
              v-model="form.icon"
              type="text"
              class="input"
              placeholder="📊"
            />
          </div>

          <div class="form-group">
            <label for="color">Color</label>
            <input
              id="color"
              v-model="form.color"
              type="color"
              class="input input-color"
            />
          </div>
        </div>

        <div class="form-group">
          <label for="keywords">Keywords (comma-separated)</label>
          <input
            id="keywords"
            v-model="keywordsInput"
            type="text"
            class="input"
            placeholder="video editing ai, opus clip, descript"
          />
          <small>These keywords will be used when collecting ads</small>
        </div>

        <div class="form-group">
          <label for="countries">Countries (comma-separated)</label>
          <input
            id="countries"
            v-model="countriesInput"
            type="text"
            class="input"
            placeholder="US, BR, UK"
          />
        </div>

        <div v-if="error" class="error-message">
          {{ error }}
        </div>

        <div class="form-actions">
          <router-link to="/" class="btn btn-secondary">Cancel</router-link>
          <button type="submit" class="btn btn-primary" :disabled="loading">
            {{ loading ? 'Creating...' : 'Create Niche' }}
          </button>
        </div>
      </form>
    </main>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useNichesStore } from '@/stores/niches'

const router = useRouter()
const nichesStore = useNichesStore()

const form = ref({
  name: '',
  description: '',
  icon: '📊',
  color: '#8B5CF6'
})

const keywordsInput = ref('')
const countriesInput = ref('US')

const loading = computed(() => nichesStore.loading)
const error = computed(() => nichesStore.error)

async function handleSubmit() {
  const keywords = keywordsInput.value
    .split(',')
    .map(k => k.trim())
    .filter(k => k)

  const countries = countriesInput.value
    .split(',')
    .map(c => c.trim().toUpperCase())
    .filter(c => c)

  try {
    const niche = await nichesStore.createNiche({
      ...form.value,
      keywords,
      countries
    })

    router.push(`/n/${niche.slug}`)
  } catch (err) {
    // Error is handled in store
  }
}
</script>

<style lang="scss" scoped>
.create-niche {
  min-height: 100vh;
  background-color: var(--color-bg-secondary);
}

.page-header {
  padding: var(--spacing-4) var(--spacing-6);
  background-color: var(--color-bg-primary);
  border-bottom: 1px solid var(--color-border);

  .back-link {
    display: inline-block;
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
    margin-bottom: var(--spacing-2);
  }

  h1 {
    font-size: var(--font-size-xl);
    font-weight: 600;
  }
}

.page-main {
  padding: var(--spacing-6);
  max-width: 600px;
  margin: 0 auto;
}

.niche-form {
  padding: var(--spacing-6);
}

.form-group {
  margin-bottom: var(--spacing-4);

  label {
    display: block;
    font-weight: 500;
    margin-bottom: var(--spacing-2);
  }

  small {
    display: block;
    font-size: var(--font-size-xs);
    color: var(--color-text-muted);
    margin-top: var(--spacing-1);
  }
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-4);
}

.input-color {
  height: 40px;
  padding: var(--spacing-1);
  cursor: pointer;
}

textarea.input {
  resize: vertical;
}

.error-message {
  padding: var(--spacing-3);
  background-color: #fee2e2;
  color: #991b1b;
  border-radius: var(--radius-md);
  margin-bottom: var(--spacing-4);
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-3);
  margin-top: var(--spacing-6);
}
</style>
