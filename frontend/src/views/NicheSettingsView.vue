<template>
  <div class="settings-view">
    <header class="page-header">
      <router-link :to="`/n/${currentSlug}`" class="back-link">
        ← Back to Workspace
      </router-link>
      <h1>Niche Settings</h1>
    </header>

    <main class="page-main">
      <!-- Loading State -->
      <div v-if="loading && !form.name" class="loading-state">
        <div class="spinner"></div>
        <p>Loading niche settings...</p>
      </div>

      <!-- Form -->
      <form v-else @submit.prevent="handleSave" class="settings-form card">
        <!-- Basic Information Section -->
        <section class="form-section">
          <h2 class="section-title">Basic Information</h2>

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
                maxlength="2"
              />
              <small>Use an emoji to represent this niche</small>
            </div>

            <div class="form-group">
              <label for="color">Color</label>
              <input
                id="color"
                v-model="form.color"
                type="color"
                class="input input-color"
              />
              <small>Theme color for this niche</small>
            </div>
          </div>
        </section>

        <!-- Collection Settings Section -->
        <section class="form-section">
          <h2 class="section-title">Collection Settings</h2>

          <div class="form-group">
            <label for="keywords">
              Keywords
              <span class="keyword-count" :class="{ 'keyword-count--over': keywordCount > 5 }">
                {{ keywordCount }}/5
              </span>
            </label>
            <input
              id="keywords"
              v-model="keywordsInput"
              type="text"
              class="input"
              :class="{ 'input--error': keywordCount > 5 }"
              placeholder="video editing ai, opus clip, descript"
            />
            <small v-if="keywordCount <= 5">Comma-separated keywords for ad collection. Max 5 keywords per niche.</small>
            <small v-else class="hint--error">Only 5 keywords can be used per niche at the moment. Please remove {{ keywordCount - 5 }} keyword{{ keywordCount - 5 > 1 ? 's' : '' }}.</small>
          </div>

          <div class="form-group">
            <label for="countries">Default Countries</label>
            <input
              id="countries"
              v-model="countriesInput"
              type="text"
              class="input"
              placeholder="US, BR, UK"
            />
            <small>Comma-separated country codes (ISO 2-letter)</small>
          </div>

          <div class="form-group form-group--inline">
            <div class="inline-label-group">
              <label for="auto-collect" class="inline-label">Auto-Collect</label>
              <small>Automatically collect ads on a daily schedule</small>
            </div>
            <label class="toggle-switch" :class="{ updating: saving }">
              <input
                id="auto-collect"
                type="checkbox"
                v-model="form.auto_collect_enabled"
                :disabled="saving"
              />
              <span class="slider">
                <span class="slider-off">Off</span>
                <span class="slider-on">On</span>
              </span>
            </label>
          </div>

          <div class="form-group">
            <label>Default Platforms</label>
            <div class="checkbox-group">
              <label class="checkbox-label">
                <input
                  v-model="form.platforms"
                  type="checkbox"
                  value="instagram"
                />
                <span>Instagram</span>
              </label>
              <label class="checkbox-label">
                <input
                  v-model="form.platforms"
                  type="checkbox"
                  value="facebook"
                />
                <span>Facebook</span>
              </label>
              <label class="checkbox-label">
                <input
                  v-model="form.platforms"
                  type="checkbox"
                  value="messenger"
                />
                <span>Messenger</span>
              </label>
              <label class="checkbox-label">
                <input
                  v-model="form.platforms"
                  type="checkbox"
                  value="audience_network"
                />
                <span>Audience Network</span>
              </label>
            </div>
            <small>Select which platforms to collect ads from</small>
          </div>
        </section>

        <!-- Error Message -->
        <div v-if="error" class="error-message">
          {{ error }}
        </div>

        <!-- Success Message -->
        <div v-if="successMessage" class="success-message">
          {{ successMessage }}
        </div>

        <!-- Form Actions -->
        <div class="form-actions">
          <router-link :to="`/n/${currentSlug}`" class="btn btn-secondary">
            Cancel
          </router-link>
          <button type="submit" class="btn btn-primary" :disabled="saving || keywordCount > 5">
            {{ saving ? 'Saving...' : 'Save Changes' }}
          </button>
        </div>

        <!-- Danger Zone -->
        <section class="danger-zone">
          <h2 class="section-title danger-title">Danger Zone</h2>
          <p class="danger-description">
            Once you delete a niche, there is no going back. All collected ads and saved data will be permanently removed.
          </p>
          <button
            type="button"
            class="btn btn-danger"
            @click="showDeleteModal = true"
          >
            🗑️ Delete This Niche
          </button>
        </section>
      </form>
    </main>

    <!-- Delete Confirmation Modal -->
    <teleport to="body">
      <div v-if="showDeleteModal" class="modal-overlay" @click="showDeleteModal = false">
        <div class="modal-content delete-modal" @click.stop>
          <h2 class="modal-title">⚠️ Delete Niche</h2>
          <p class="modal-description">
            Are you sure you want to delete <strong>{{ form.name }}</strong>?
          </p>
          <p class="modal-warning">
            This will permanently delete:
          </p>
          <ul class="modal-list">
            <li>All collected ads in this niche</li>
            <li>All saved ads and notes</li>
            <li>All niche settings and metadata</li>
          </ul>
          <p class="modal-warning-final">
            <strong>This action cannot be undone.</strong>
          </p>

          <div v-if="deleteError" class="error-message">
            {{ deleteError }}
          </div>

          <div class="modal-actions">
            <button
              type="button"
              class="btn btn-secondary"
              @click="showDeleteModal = false"
              :disabled="deleting"
            >
              Cancel
            </button>
            <button
              type="button"
              class="btn btn-danger"
              @click="handleDelete"
              :disabled="deleting"
            >
              {{ deleting ? 'Deleting...' : 'Delete Niche' }}
            </button>
          </div>
        </div>
      </div>
    </teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useNichesStore } from '@/stores/niches'

const route = useRoute()
const router = useRouter()
const nichesStore = useNichesStore()

// Use nicheSlug param from parent route
const currentSlug = ref(route.params.nicheSlug)
const loading = ref(true)

const form = ref({
  name: '',
  description: '',
  icon: '📊',
  color: '#8B5CF6',
  platforms: ['instagram'],
  auto_collect_enabled: false,
})

const keywordsInput = ref('')
const countriesInput = ref('US')

const keywordCount = computed(() =>
  keywordsInput.value.split(',').map(k => k.trim()).filter(k => k).length
)

const saving = ref(false)
const error = ref(null)
const successMessage = ref(null)

const showDeleteModal = ref(false)
const deleting = ref(false)
const deleteError = ref(null)

// Load niche data on mount
onMounted(async () => {
  currentSlug.value = route.params.nicheSlug
  console.log('NicheSettingsView mounted, slug:', currentSlug.value)
  if (currentSlug.value) {
    await loadNicheData()
  } else {
    error.value = 'No niche selected'
    loading.value = false
  }
})

// Watch for route changes
watch(() => route.params.nicheSlug, async (newSlug) => {
  if (newSlug) {
    currentSlug.value = newSlug
    console.log('Route changed, new slug:', newSlug)
    await loadNicheData()
  }
})

async function loadNicheData() {
  loading.value = true
  error.value = null

  try {
    console.log('Fetching niche data for:', currentSlug.value)
    await nichesStore.fetchNiche(currentSlug.value)
    const niche = nichesStore.currentNiche

    console.log('Niche data received:', niche)

    if (niche) {
      form.value = {
        name: niche.name || '',
        description: niche.description || '',
        icon: niche.icon || '📊',
        color: niche.color || '#8B5CF6',
        platforms: Array.isArray(niche.platforms) ? niche.platforms : ['instagram'],
        auto_collect_enabled: niche.auto_collect_enabled || false,
      }

      // Convert arrays to comma-separated strings
      keywordsInput.value = Array.isArray(niche.keywords)
        ? niche.keywords.join(', ')
        : ''
      countriesInput.value = Array.isArray(niche.countries)
        ? niche.countries.join(', ')
        : 'US'

      console.log('Form populated:', form.value)
    } else {
      error.value = 'Niche not found'
    }
  } catch (err) {
    console.error('Error loading niche:', err)
    error.value = 'Failed to load niche settings'
  } finally {
    loading.value = false
  }
}

async function handleSave() {
  if (!form.value.name.trim()) {
    error.value = 'Niche name is required'
    return
  }

  saving.value = true
  error.value = null
  successMessage.value = null

  try {
    // Parse keywords and countries
    const keywords = keywordsInput.value
      .split(',')
      .map(k => k.trim())
      .filter(k => k)

    const countries = countriesInput.value
      .split(',')
      .map(c => c.trim().toUpperCase())
      .filter(c => c)

    // Prepare update data
    const updateData = {
      name: form.value.name.trim(),
      description: form.value.description?.trim() || '',
      icon: form.value.icon || '📊',
      color: form.value.color || '#8B5CF6',
      keywords,
      countries,
      platforms: form.value.platforms,
      auto_collect_enabled: form.value.auto_collect_enabled,
    }

    const updatedNiche = await nichesStore.updateNiche(currentSlug.value, updateData)

    successMessage.value = 'Settings saved successfully!'

    // If slug changed due to name change, redirect
    if (updatedNiche.slug !== currentSlug.value) {
      setTimeout(() => {
        router.push(`/n/${updatedNiche.slug}/settings`)
      }, 1500)
    } else {
      // Clear success message after 3 seconds
      setTimeout(() => {
        successMessage.value = null
      }, 3000)
    }
  } catch (err) {
    error.value = err.response?.data?.error || 'Failed to save settings'
  } finally {
    saving.value = false
  }
}

async function handleDelete() {
  deleting.value = true
  deleteError.value = null

  try {
    await nichesStore.deleteNiche(currentSlug.value)

    // Redirect to niche selector
    router.push('/')
  } catch (err) {
    deleteError.value = err.response?.data?.error || 'Failed to delete niche'
  } finally {
    deleting.value = false
  }
}
</script>

<style lang="scss" scoped>
.settings-view {
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
    text-decoration: none;

    &:hover {
      color: var(--color-primary);
    }
  }

  h1 {
    font-size: var(--font-size-xl);
    font-weight: 600;
  }
}

.page-main {
  padding: var(--spacing-6);
  max-width: 800px;
  margin: 0 auto;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-12);
  text-align: center;

  .spinner {
    width: 48px;
    height: 48px;
    border: 4px solid var(--color-border);
    border-top-color: var(--color-primary);
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-bottom: var(--spacing-4);
  }

  p {
    color: var(--color-text-secondary);
  }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.settings-form {
  padding: var(--spacing-6);
}

.form-section {
  margin-bottom: var(--spacing-8);
  padding-bottom: var(--spacing-6);
  border-bottom: 1px solid var(--color-border);

  &:last-of-type {
    border-bottom: none;
  }
}

.section-title {
  font-size: var(--font-size-lg);
  font-weight: 600;
  margin-bottom: var(--spacing-4);
}

.form-group {
  margin-bottom: var(--spacing-4);

  label {
    display: block;
    font-weight: 500;
    margin-bottom: var(--spacing-2);
    font-size: var(--font-size-sm);
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

  @media (max-width: 640px) {
    grid-template-columns: 1fr;
  }
}

.input-color {
  height: 48px;
  padding: var(--spacing-1);
  cursor: pointer;
}

textarea.input {
  resize: vertical;
  min-height: 80px;
}

.checkbox-group {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-3);
  padding: var(--spacing-3) 0;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  cursor: pointer;
  font-size: var(--font-size-sm);

  input[type="checkbox"] {
    width: 18px;
    height: 18px;
    cursor: pointer;
  }

  span {
    user-select: none;
  }

  &:hover span {
    color: var(--color-primary);
  }
}

// ---- Auto-collect toggle (inline form group) ----

.form-group--inline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-4);
}

.inline-label-group {
  label { margin-bottom: 0; }
  small { display: block; margin-top: var(--spacing-1); }
}

.inline-label {
  font-weight: 500;
  font-size: var(--font-size-sm);
}

.toggle-switch {
  position: relative;
  display: inline-block;
  cursor: pointer;
  flex-shrink: 0;

  input {
    position: absolute;
    opacity: 0;
    width: 0;
    height: 0;
  }

  &.updating {
    opacity: 0.6;
    cursor: not-allowed;
  }
}

.slider {
  display: flex;
  align-items: center;
  width: 72px;
  height: 26px;
  background-color: var(--color-gray-200);
  border-radius: var(--radius-full);
  position: relative;
  transition: background-color var(--transition-fast);
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    left: 3px;
    width: 20px;
    height: 20px;
    background-color: white;
    border-radius: 50%;
    transition: transform var(--transition-fast);
    z-index: 1;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  }
}

.slider-off,
.slider-on {
  position: absolute;
  font-size: 10px;
  font-weight: 600;
  line-height: 1;
  transition: opacity var(--transition-fast);
  user-select: none;
}

.slider-off {
  right: 7px;
  color: var(--color-text-secondary);
  opacity: 1;
}

.slider-on {
  left: 7px;
  color: white;
  opacity: 0;
}

input:checked + .slider {
  background-color: var(--color-primary-600);

  &::before {
    transform: translateX(46px);
  }

  .slider-off { opacity: 0; }
  .slider-on  { opacity: 1; }
}

// ---- Keyword counter ----

.keyword-count {
  font-weight: 400;
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  margin-left: var(--spacing-2);

  &--over {
    color: #dc2626;
    font-weight: 600;
  }
}

.input--error {
  border-color: #dc2626 !important;

  &:focus {
    box-shadow: 0 0 0 3px rgba(220, 38, 38, 0.15);
  }
}

.hint--error {
  color: #dc2626 !important;
}

.error-message {
  padding: var(--spacing-3);
  background-color: #fee2e2;
  color: #991b1b;
  border-radius: var(--radius-md);
  margin-bottom: var(--spacing-4);
  font-size: var(--font-size-sm);
}

.success-message {
  padding: var(--spacing-3);
  background-color: #d1fae5;
  color: #065f46;
  border-radius: var(--radius-md);
  margin-bottom: var(--spacing-4);
  font-size: var(--font-size-sm);
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-3);
  margin-top: var(--spacing-6);
  padding-top: var(--spacing-4);
  border-top: 1px solid var(--color-border);
}

// Danger Zone
.danger-zone {
  margin-top: var(--spacing-8);
  padding: var(--spacing-6);
  background-color: #fef2f2;
  border: 2px solid #fecaca;
  border-radius: var(--radius-lg);

  .danger-title {
    color: #991b1b;
    margin-bottom: var(--spacing-3);
  }

  .danger-description {
    color: #7f1d1d;
    font-size: var(--font-size-sm);
    margin-bottom: var(--spacing-4);
    line-height: 1.5;
  }
}

.btn-danger {
  background-color: #dc2626;
  color: white;
  border: none;
  padding: var(--spacing-2) var(--spacing-4);
  border-radius: var(--radius-md);
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;

  &:hover:not(:disabled) {
    background-color: #b91c1c;
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

// Delete Modal
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
  z-index: 9999;
  padding: var(--spacing-4);
}

.modal-content {
  background-color: var(--color-bg-primary);
  border-radius: var(--radius-lg);
  padding: var(--spacing-6);
  max-width: 500px;
  width: 100%;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
}

.delete-modal {
  .modal-title {
    font-size: var(--font-size-lg);
    font-weight: 600;
    margin-bottom: var(--spacing-3);
  }

  .modal-description {
    color: var(--color-text-secondary);
    margin-bottom: var(--spacing-3);
    line-height: 1.5;

    strong {
      color: var(--color-text-primary);
    }
  }

  .modal-warning {
    color: #991b1b;
    font-size: var(--font-size-sm);
    margin-bottom: var(--spacing-2);
    font-weight: 500;
  }

  .modal-list {
    margin: var(--spacing-3) 0;
    padding-left: var(--spacing-5);
    color: var(--color-text-secondary);
    font-size: var(--font-size-sm);

    li {
      margin-bottom: var(--spacing-1);
    }
  }

  .modal-warning-final {
    color: #991b1b;
    font-size: var(--font-size-sm);
    font-weight: 600;
    margin-top: var(--spacing-4);
    margin-bottom: var(--spacing-4);
  }

  .modal-actions {
    display: flex;
    justify-content: flex-end;
    gap: var(--spacing-3);
    margin-top: var(--spacing-6);
  }
}
</style>
