<template>
  <div class="competitors-dashboard">
    <header class="dashboard-header">
      <div class="header-left">
        <h1 class="logo">MetAds</h1>
      </div>
      <nav class="header-nav">
        <router-link to="/" class="nav-link">📊 Your Niches</router-link>
        <router-link to="/competitors" class="nav-link">🏆 Competition</router-link>
        <router-link to="/admin/collection-health" class="nav-link">
          📡 Collection Health
        </router-link>
        <router-link v-if="isAdmin" to="/admin/global-history" class="nav-link">
          🌐 Global History
        </router-link>
      </nav>
      <div class="header-right">
        <div v-if="isDevMode" class="dev-user-badge">👤 Dev User</div>
        <UserButton v-else :afterSignOutUrl="'/sign-in'" />
      </div>
    </header>

    <main class="dashboard-main">
      <div class="dashboard-content">
        <div class="page-title-row">
          <div>
            <h2 class="page-title">Competition</h2>
            <p class="page-subtitle">Track competitor advertisers and their active ads</p>
          </div>
          <button class="btn btn-primary" @click="showAddForm = true">
            + Add Competitor
          </button>
        </div>

        <!-- Add competitor form -->
        <div v-if="showAddForm" class="add-form-card">
          <h3 class="form-title">Add Competitor</h3>
          <p class="form-hint">
            Enter the exact advertiser name as shown in Meta Ad Library. We'll look up their
            page ID automatically.
          </p>
          <div class="form-row">
            <input
              ref="pageNameInput"
              v-model="newPageName"
              class="form-input"
              type="text"
              placeholder="e.g. Lost Dutchman Leather Goods"
              @keyup.enter="handleAdd"
              :disabled="adding"
            />
            <select v-model="newCountries" class="form-input form-input-country" :disabled="adding">
              <option value="BR">🇧🇷 Brazil</option>
              <option value="US">🇺🇸 United States</option>
              <option value="CA">🇨🇦 Canada</option>
              <option value="FR">🇫🇷 France</option>
              <option value="DE">🇩🇪 Germany</option>
              <option value="IT">🇮🇹 Italy</option>
              <option value="PT">🇵🇹 Portugal</option>
              <option value="ES">🇪🇸 Spain</option>
              <option value="JP">🇯🇵 Japan</option>
              <option value="CN">🇨🇳 China</option>
            </select>
            <input
              v-model="newPageId"
              class="form-input form-input-sm"
              type="text"
              placeholder="Page ID (optional)"
              :disabled="adding"
            />
          </div>
          <div v-if="addError" class="form-error">{{ addError }}</div>
          <div class="form-actions">
            <button class="btn btn-ghost" @click="cancelAdd" :disabled="resolving || adding">Cancel</button>
            <button class="btn btn-primary" @click="handleAdd" :disabled="resolving || adding || !newPageName.trim()">
              {{ resolving ? 'Searching...' : adding ? 'Adding...' : 'Search' }}
            </button>
          </div>
        </div>

        <!-- Search filter -->
        <div v-if="store.competitors.length > 0" class="search-row">
          <input
            v-model="searchQuery"
            class="search-input"
            type="text"
            placeholder="Filter competitors..."
          />
        </div>

        <!-- Loading -->
        <div v-if="store.loading" class="loading-state">
          <div class="spinner"></div>
          <p>Loading competitors...</p>
        </div>

        <!-- Error -->
        <div v-else-if="store.error" class="error-state">
          <div class="error-icon">⚠️</div>
          <h3>Error Loading Competitors</h3>
          <p>{{ store.error }}</p>
          <button class="btn btn-primary" @click="store.fetchCompetitors()">Try Again</button>
        </div>

        <!-- Empty state -->
        <div v-else-if="store.competitors.length === 0" class="empty-state">
          <div class="empty-icon">🏆</div>
          <h3>No competitors yet</h3>
          <p>Add advertiser pages you want to monitor. We'll show you all their active ads.</p>
          <button class="btn btn-primary" @click="showAddForm = true">Add First Competitor</button>
        </div>

        <!-- Competitors grid -->
        <div v-else class="competitors-grid">
          <CompetitorCard
            v-for="c in filteredCompetitors"
            :key="c.page_id"
            :competitor="c"
            @click="goToDetail"
            @remove="handleRemove"
          />
          <div v-if="filteredCompetitors.length === 0" class="no-results">
            No competitors match "{{ searchQuery }}"
          </div>
        </div>
      </div>
    </main>

    <!-- Confirm competitor modal -->
    <ConfirmCompetitorModal
      v-if="showConfirmModal && confirmCandidates.length"
      :candidates="confirmCandidates"
      :adding="adding"
      @confirm="handleConfirm"
      @cancel="showConfirmModal = false"
    />

    <!-- Remove confirm modal -->
    <div v-if="confirmRemove" class="modal-overlay" @click.self="confirmRemove = null">
      <div class="modal-dialog">
        <h3>Remove Competitor</h3>
        <p>
          Remove <strong>{{ confirmRemove.page_name }}</strong> from your competitors list?
        </p>
        <div class="modal-actions">
          <button class="btn btn-ghost" @click="confirmRemove = null">Cancel</button>
          <button class="btn btn-danger" @click="executeRemove">Remove</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
  import { ref, computed, onMounted, nextTick, watch } from 'vue'
  import { useRouter } from 'vue-router'
  import { UserButton, useUser } from '@clerk/vue'
  import { useCompetitorsStore } from '@/stores/competitors'
  import { devMode } from '@/services/api'
  import CompetitorCard from '@/components/CompetitorCard.vue'
  import ConfirmCompetitorModal from '@/components/ConfirmCompetitorModal.vue'

  const router = useRouter()
  const store = useCompetitorsStore()
  const isDevMode = devMode
  const isAdmin = ref(isDevMode)

  if (!isDevMode) {
    const { user } = useUser()
    watch(user, (u) => { isAdmin.value = u?.publicMetadata?.role === 'admin' }, { immediate: true })
  }

  const showAddForm = ref(false)
  const newPageName = ref('')
  const newPageId = ref('')
  const newCountries = ref('BR')
  const resolving = ref(false)   // searching Meta API for candidates
  const adding = ref(false)      // saving the confirmed competitor
  const addError = ref('')
  const searchQuery = ref('')
  const confirmRemove = ref(null)
  const pageNameInput = ref(null)

  // Confirmation modal state
  const confirmCandidates = ref([])      // list returned by /resolve
  const confirmResolvedCountries = ref('') // country string that found the candidates
  const showConfirmModal = ref(false)

  const filteredCompetitors = computed(() => {
    if (!searchQuery.value.trim()) return store.competitors
    const q = searchQuery.value.toLowerCase()
    return store.competitors.filter((c) =>
      c.page_name.toLowerCase().includes(q) ||
      c.page_id.toLowerCase().includes(q)
    )
  })

  async function handleAdd() {
    const name = newPageName.value.trim()
    if (!name) return

    addError.value = ''

    // If the user typed a page_id directly, skip resolution and go straight to save
    if (newPageId.value.trim()) {
      await _saveCompetitor({ page_name: name, page_id: newPageId.value.trim(), countries: newCountries.value })
      return
    }

    // Step 1: resolve — find candidates without saving
    resolving.value = true
    try {
      const { candidates, resolved_countries } = await store.resolveCompetitor({
        page_name: name,
        countries: newCountries.value,
      })
      confirmCandidates.value = candidates
      confirmResolvedCountries.value = resolved_countries || newCountries.value
      showConfirmModal.value = true
    } catch (e) {
      addError.value = e.response?.data?.error || e.message || 'Could not find this advertiser'
    } finally {
      resolving.value = false
    }
  }

  async function handleConfirm(candidate) {
    // Step 2: user confirmed a candidate — save with the countries that
    // actually found the page (not the dropdown hint) so ad fetches
    // target the right market from the start.
    await _saveCompetitor({
      page_name: candidate.page_name,
      page_id:   candidate.page_id,
      countries: confirmResolvedCountries.value || newCountries.value,
    })
  }

  async function _saveCompetitor(pageData) {
    adding.value = true
    addError.value = ''
    try {
      await store.addCompetitor(pageData)
      showConfirmModal.value = false
      cancelAdd()
    } catch (e) {
      addError.value = e.response?.data?.error || e.message || 'Failed to add competitor'
      showConfirmModal.value = false
    } finally {
      adding.value = false
    }
  }

  function cancelAdd() {
    showAddForm.value = false
    showConfirmModal.value = false
    confirmCandidates.value = []
    confirmResolvedCountries.value = ''
    newPageName.value = ''
    newPageId.value = ''
    newCountries.value = 'BR'
    addError.value = ''
  }

  watch(showAddForm, async (val) => {
    if (val) {
      await nextTick()
      pageNameInput.value?.focus()
    }
  })

  function goToDetail(competitor) {
    router.push(`/competitors/${competitor.page_id}`)
  }

  function handleRemove(competitor) {
    confirmRemove.value = competitor
  }

  async function executeRemove() {
    if (!confirmRemove.value) return
    try {
      await store.removeCompetitor(confirmRemove.value.page_id)
    } finally {
      confirmRemove.value = null
    }
  }

  onMounted(() => {
    store.fetchCompetitors()
  })
</script>

<style lang="scss" scoped>
  .competitors-dashboard {
    min-height: 100vh;
    background-color: var(--color-bg-secondary);
  }

  .dashboard-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: var(--spacing-4) var(--spacing-6);
    background-color: var(--color-bg-primary);
    border-bottom: 1px solid var(--color-border);
  }

  .logo {
    font-size: var(--font-size-xl);
    font-weight: 700;
    color: var(--color-gray-900);
  }

  .header-nav {
    display: flex;
    align-items: center;
    gap: var(--spacing-2);
  }

  .nav-link {
    font-size: var(--font-size-sm);
    font-weight: 500;
    color: var(--color-text-secondary);
    text-decoration: none;
    padding: var(--spacing-2) var(--spacing-3);
    border-radius: var(--radius-md);
    transition: all var(--transition-fast);

    &:hover {
      color: var(--color-gray-900);
      background-color: var(--color-gray-100);
    }

    &.router-link-active {
      color: var(--color-primary-600);
      background-color: var(--color-primary-50);
    }
  }

  .dev-user-badge {
    padding: var(--spacing-2) var(--spacing-3);
    background-color: var(--color-warning-100);
    border-radius: var(--radius-full);
    font-size: var(--font-size-sm);
  }

  .dashboard-main {
    padding: var(--spacing-8);
    max-width: 1200px;
    margin: 0 auto;
  }

  .dashboard-content {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-6);
  }

  .page-title-row {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: var(--spacing-4);
  }

  .page-title {
    font-size: var(--font-size-2xl);
    font-weight: 600;
    margin: 0 0 var(--spacing-1) 0;
  }

  .page-subtitle {
    color: var(--color-text-secondary);
    margin: 0;
  }

  // Add form
  .add-form-card {
    background-color: var(--color-bg-primary);
    border: 1px solid var(--color-primary-200);
    border-radius: var(--radius-xl);
    padding: var(--spacing-5);
    display: flex;
    flex-direction: column;
    gap: var(--spacing-3);
  }

  .form-title {
    font-size: var(--font-size-lg);
    font-weight: 600;
    margin: 0;
  }

  .form-hint {
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
    margin: 0;
  }

  .form-row {
    display: flex;
    gap: var(--spacing-2);
    flex-wrap: wrap;
  }

  .form-input {
    flex: 1;
    min-width: 220px;
    padding: var(--spacing-2) var(--spacing-3);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    font-size: var(--font-size-sm);
    background-color: var(--color-bg-primary);

    &:focus {
      outline: none;
      border-color: var(--color-primary-500);
    }

    &.form-input-sm {
      flex: 0 0 180px;
      min-width: 0;
    }

    &.form-input-country {
      flex: 0 0 160px;
      min-width: 0;
      cursor: pointer;
    }

    &:disabled {
      opacity: 0.5;
    }
  }

  .form-error {
    font-size: var(--font-size-sm);
    color: var(--color-error, #dc2626);
    background-color: #fef2f2;
    border: 1px solid #fecaca;
    border-radius: var(--radius-md);
    padding: var(--spacing-2) var(--spacing-3);
  }

  .form-actions {
    display: flex;
    gap: var(--spacing-2);
    justify-content: flex-end;
  }

  // Search
  .search-row {
    display: flex;
  }

  .search-input {
    width: 100%;
    max-width: 400px;
    padding: var(--spacing-2) var(--spacing-3);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    font-size: var(--font-size-sm);
    background-color: var(--color-bg-primary);

    &:focus {
      outline: none;
      border-color: var(--color-primary-500);
    }
  }

  // States
  .loading-state,
  .empty-state,
  .error-state {
    text-align: center;
    padding: var(--spacing-12);
  }

  .spinner {
    width: 40px;
    height: 40px;
    border: 3px solid var(--color-gray-200);
    border-top-color: var(--color-primary-500);
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto var(--spacing-4);
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .empty-icon,
  .error-icon {
    font-size: 4rem;
    margin-bottom: var(--spacing-4);
  }

  .empty-state h3,
  .error-state h3 {
    font-size: var(--font-size-xl);
    margin-bottom: var(--spacing-2);
  }

  .empty-state p,
  .error-state p {
    color: var(--color-text-secondary);
    margin-bottom: var(--spacing-6);
  }

  // Grid
  .competitors-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: var(--spacing-4);
  }

  .no-results {
    grid-column: 1 / -1;
    text-align: center;
    padding: var(--spacing-8);
    color: var(--color-text-secondary);
  }

  // Remove modal
  .modal-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }

  .modal-dialog {
    background: var(--color-bg-primary);
    border-radius: var(--radius-lg);
    padding: var(--spacing-6);
    max-width: 400px;
    width: 90%;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);

    h3 {
      margin: 0 0 var(--spacing-3);
      font-size: var(--font-size-lg);
    }

    p {
      margin: 0 0 var(--spacing-4);
      color: var(--color-text-secondary);
    }
  }

  .modal-actions {
    display: flex;
    gap: var(--spacing-2);
    justify-content: flex-end;
  }

  .btn-danger {
    background-color: var(--color-error, #dc2626);
    color: white;
    border: none;

    &:hover {
      background-color: #b91c1c;
    }
  }
</style>
