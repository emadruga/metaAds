<template>
  <div class="competitor-detail">
    <!-- Header -->
    <header class="detail-header">
      <div class="header-left">
        <router-link to="/competitors" class="back-btn">← Competition</router-link>
        <h1 class="page-title">{{ competitor?.page_name || 'Loading...' }}</h1>
      </div>
      <div class="header-right">
        <div v-if="isDevMode" class="dev-user-badge">👤 Dev User</div>
        <UserButton v-else :afterSignOutUrl="'/sign-in'" />
      </div>
    </header>

    <!-- Loading competitor info -->
    <div v-if="!competitor && !storeError" class="page-loading">
      <div class="spinner"></div>
      <p>Loading competitor...</p>
    </div>

    <div v-else-if="storeError" class="page-error">
      <p>{{ storeError }}</p>
      <router-link to="/competitors" class="btn btn-primary">Back to Competition</router-link>
    </div>

    <div v-else class="detail-body">
      <!-- Left panel: competitor metadata -->
      <aside class="meta-panel">
        <div class="meta-card">
          <h2 class="meta-page-name">{{ competitor.page_name }}</h2>

          <div class="meta-field">
            <span class="meta-label">Page ID</span>
            <span class="meta-value mono">{{ competitor.page_id }}</span>
          </div>

          <div class="meta-field">
            <span class="meta-label">Added</span>
            <span class="meta-value">{{ formatDate(competitor.added_at) }}</span>
          </div>

          <div class="meta-field" v-if="adsData">
            <span class="meta-label">Active Ads</span>
            <span class="meta-value highlight">{{ adsData.count }}</span>
          </div>

          <div class="meta-field" v-if="longestRunningAd">
            <span class="meta-label">Longest Running</span>
            <span class="meta-value highlight">{{ longestRunningAd.days_active }} days</span>
          </div>

          <div class="meta-field" v-if="avgDaysActive !== null">
            <span class="meta-label">Avg. Days Active</span>
            <span class="meta-value">{{ avgDaysActive }} days</span>
          </div>

          <div class="meta-field" v-if="platformSummary.length > 0">
            <span class="meta-label">Platforms</span>
            <div class="platform-tags">
              <span v-for="p in platformSummary" :key="p" class="platform-tag">{{ p }}</span>
            </div>
          </div>

          <!-- Notes -->
          <div class="meta-notes-section">
            <span class="meta-label">Notes</span>
            <textarea
              class="notes-input"
              v-model="notesValue"
              placeholder="Add notes about this competitor..."
              @blur="saveNotes"
            ></textarea>
          </div>

          <!-- Actions -->
          <div class="meta-actions">
            <a
              :href="`https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=US&q=${encodeURIComponent(competitor.page_name)}&search_type=page`"
              target="_blank"
              rel="noopener noreferrer"
              class="btn btn-ghost btn-sm"
            >
              🔗 Open in Meta Library
            </a>
          </div>
        </div>
      </aside>

      <!-- Main panel: ads table -->
      <section class="ads-panel">
        <!-- Filter / status selector -->
        <div class="ads-toolbar">
          <div class="toolbar-left">
            <h3 class="ads-title">
              {{ statusLabel }} Ads
              <span v-if="adsData" class="ads-count">{{ adsData.count }}</span>
            </h3>
          </div>
          <div class="toolbar-right">
            <select v-model="statusFilter" class="status-select" @change="loadAds">
              <option value="ACTIVE">Active only</option>
              <option value="ALL">All ads</option>
              <option value="INACTIVE">Inactive only</option>
            </select>
            <button
              class="btn btn-ghost btn-sm refresh-btn"
              @click="loadAds"
              :disabled="store.adsLoading"
              title="Refresh"
            >
              {{ store.adsLoading ? '⏳' : '↻' }} Refresh
            </button>
          </div>
        </div>

        <!-- Loading ads -->
        <div v-if="store.adsLoading && !adsData" class="ads-loading">
          <div class="spinner"></div>
          <p>Fetching ads from Meta Ad Library...</p>
        </div>

        <!-- Error -->
        <div v-else-if="store.adsError" class="ads-error">
          <p>⚠️ {{ store.adsError }}</p>
          <button class="btn btn-primary btn-sm" @click="loadAds">Try Again</button>
        </div>

        <!-- Empty -->
        <div v-else-if="adsData && adsData.ads.length === 0" class="ads-empty">
          <p>No {{ statusFilter.toLowerCase() }} ads found for this page.</p>
        </div>

        <!-- Ads table -->
        <div v-else-if="adsData" class="ads-table-wrapper">
          <table class="ads-table">
            <thead>
              <tr>
                <th class="col-id">Library ID</th>
                <th class="col-body">Ad Copy</th>
                <th class="col-start">Started</th>
                <th class="col-days">Days Active</th>
                <th class="col-platforms">Platforms</th>
                <th class="col-status">Status</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="ad in filteredAds"
                :key="ad.meta_ad_id"
                class="ad-row"
                @click="selectedAd = ad"
              >
                <td class="col-id">
                  <span class="ad-id-text">{{ ad.meta_ad_id }}</span>
                </td>
                <td class="col-body">
                  <span class="ad-body-preview">{{ truncate(ad.body || ad.headline, 120) }}</span>
                </td>
                <td class="col-start">{{ formatDate(ad.start_date) }}</td>
                <td class="col-days">
                  <span :class="['days-badge', daysClass(ad.days_active)]">
                    {{ ad.days_active ?? '—' }}
                  </span>
                </td>
                <td class="col-platforms">
                  <span class="platforms-text">{{ formatPlatforms(ad.platforms) }}</span>
                </td>
                <td class="col-status">
                  <span :class="['status-dot', ad.is_active ? 'active' : 'inactive']">
                    {{ ad.is_active ? 'Active' : 'Inactive' }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Initial state (before first load) -->
        <div v-else class="ads-initial">
          <button class="btn btn-primary" @click="loadAds">
            📥 Fetch Ads from Meta
          </button>
          <p class="hint">We'll pull active ads for this competitor directly from Meta Ad Library.</p>
        </div>
      </section>
    </div>

    <!-- Ad detail modal -->
    <CompetitorAdModal
      v-if="selectedAd"
      :ad="selectedAd"
      @close="selectedAd = null"
    />
  </div>
</template>

<script setup>
  import { ref, computed, onMounted, watch } from 'vue'
  import { useRoute } from 'vue-router'
  import { UserButton } from '@clerk/vue'
  import { useCompetitorsStore } from '@/stores/competitors'
  import { competitorApi } from '@/services/api'
  import { devMode } from '@/services/api'
  import CompetitorAdModal from '@/components/CompetitorAdModal.vue'

  const route = useRoute()
  const store = useCompetitorsStore()
  const isDevMode = devMode

  const pageId = computed(() => route.params.pageId)

  const selectedAd = ref(null)
  const statusFilter = ref('ACTIVE')
  const storeError = ref('')
  const notesValue = ref('')

  const competitor = computed(() => store.competitorByPageId(pageId.value))

  const adsData = computed(() => store.getAdsForPage(pageId.value))

  const filteredAds = computed(() => adsData.value?.ads || [])

  const longestRunningAd = computed(() => {
    const ads = filteredAds.value
    if (!ads.length) return null
    return ads.reduce((best, a) =>
      (a.days_active || 0) > (best.days_active || 0) ? a : best
    )
  })

  const avgDaysActive = computed(() => {
    const ads = filteredAds.value.filter((a) => a.days_active != null)
    if (!ads.length) return null
    const sum = ads.reduce((s, a) => s + a.days_active, 0)
    return Math.round(sum / ads.length)
  })

  const platformSummary = computed(() => {
    const set = new Set()
    filteredAds.value.forEach((a) => (a.platforms || []).forEach((p) => set.add(p)))
    return [...set]
  })

  const statusLabel = computed(() => {
    const map = { ACTIVE: 'Active', INACTIVE: 'Inactive', ALL: 'All' }
    return map[statusFilter.value] || statusFilter.value
  })

  async function loadAds() {
    if (!pageId.value) return
    try {
      await store.fetchCompetitorAds(pageId.value, {
        status: statusFilter.value,
        limit: 200,
      })
    } catch (_) {
      // error already stored in store.adsError
    }
  }

  async function saveNotes() {
    if (!competitor.value) return
    try {
      await competitorApi.update(pageId.value, { notes: notesValue.value })
    } catch (_) {
      // silently ignore - non-critical
    }
  }

  watch(competitor, (c) => {
    if (c) notesValue.value = c.notes || ''
  }, { immediate: true })

  function formatDate(dateStr) {
    if (!dateStr) return '—'
    try {
      return new Date(dateStr).toLocaleDateString('en-US', {
        year: 'numeric', month: 'short', day: 'numeric',
      })
    } catch {
      return dateStr
    }
  }

  function formatPlatforms(platforms) {
    if (!platforms || !platforms.length) return '—'
    const labels = { facebook: 'FB', instagram: 'IG', messenger: 'MSG', audience_network: 'AN' }
    return platforms.map((p) => labels[p] || p).join(', ')
  }

  function truncate(text, max) {
    if (!text) return '—'
    return text.length > max ? text.slice(0, max) + '…' : text
  }

  function daysClass(days) {
    if (days == null) return ''
    if (days >= 180) return 'days-high'
    if (days >= 60) return 'days-mid'
    return 'days-low'
  }

  onMounted(async () => {
    // Make sure competitors list is loaded so we can look up metadata
    if (store.competitors.length === 0) {
      await store.fetchCompetitors()
    }
    // Auto-load ads on mount
    loadAds()
  })
</script>

<style lang="scss" scoped>
  .competitor-detail {
    min-height: 100vh;
    background-color: var(--color-bg-secondary);
    display: flex;
    flex-direction: column;
  }

  // Header
  .detail-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: var(--spacing-3) var(--spacing-6);
    background-color: var(--color-bg-primary);
    border-bottom: 1px solid var(--color-border);
    gap: var(--spacing-4);
  }

  .header-left {
    display: flex;
    align-items: center;
    gap: var(--spacing-4);
    min-width: 0;
  }

  .back-btn {
    font-size: var(--font-size-sm);
    font-weight: 500;
    color: var(--color-text-secondary);
    text-decoration: none;
    white-space: nowrap;
    flex-shrink: 0;

    &:hover {
      color: var(--color-primary-600);
    }
  }

  .page-title {
    font-size: var(--font-size-lg);
    font-weight: 600;
    margin: 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .dev-user-badge {
    padding: var(--spacing-2) var(--spacing-3);
    background-color: var(--color-warning-100);
    border-radius: var(--radius-full);
    font-size: var(--font-size-sm);
  }

  // Loading / error
  .page-loading,
  .page-error {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    flex: 1;
    padding: var(--spacing-12);
    text-align: center;
    gap: var(--spacing-4);
    color: var(--color-text-secondary);
  }

  .spinner {
    width: 36px;
    height: 36px;
    border: 3px solid var(--color-gray-200);
    border-top-color: var(--color-primary-500);
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-bottom: var(--spacing-3);
  }

  @keyframes spin { to { transform: rotate(360deg); } }

  // Two-panel layout
  .detail-body {
    display: flex;
    flex: 1;
    gap: 0;
    overflow: hidden;
  }

  // Left panel
  .meta-panel {
    width: 280px;
    flex-shrink: 0;
    border-right: 1px solid var(--color-border);
    overflow-y: auto;
    background-color: var(--color-bg-primary);
  }

  .meta-card {
    padding: var(--spacing-5);
    display: flex;
    flex-direction: column;
    gap: var(--spacing-4);
  }

  .meta-page-name {
    font-size: var(--font-size-lg);
    font-weight: 700;
    color: var(--color-gray-900);
    margin: 0;
    line-height: 1.3;
    word-break: break-word;
  }

  .meta-field {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-1);
  }

  .meta-label {
    font-size: var(--font-size-xs);
    font-weight: 600;
    color: var(--color-text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .meta-value {
    font-size: var(--font-size-sm);
    color: var(--color-gray-800);
    word-break: break-all;

    &.mono {
      font-family: monospace;
      font-size: var(--font-size-xs);
      color: var(--color-text-secondary);
    }

    &.highlight {
      font-size: var(--font-size-xl);
      font-weight: 700;
      color: var(--color-primary-600);
    }
  }

  .platform-tags {
    display: flex;
    flex-wrap: wrap;
    gap: var(--spacing-1);
  }

  .platform-tag {
    font-size: var(--font-size-xs);
    padding: 2px var(--spacing-2);
    background-color: var(--color-gray-100);
    border-radius: var(--radius-full);
    color: var(--color-text-secondary);
  }

  .meta-notes-section {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-2);
  }

  .notes-input {
    width: 100%;
    min-height: 80px;
    padding: var(--spacing-2);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    font-size: var(--font-size-sm);
    resize: vertical;
    box-sizing: border-box;

    &:focus {
      outline: none;
      border-color: var(--color-primary-500);
    }
  }

  .meta-actions {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-2);
  }

  .btn-sm {
    padding: var(--spacing-1) var(--spacing-3);
    font-size: var(--font-size-xs);
  }

  // Right panel
  .ads-panel {
    flex: 1;
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }

  .ads-toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: var(--spacing-3) var(--spacing-5);
    border-bottom: 1px solid var(--color-border);
    background-color: var(--color-bg-primary);
    gap: var(--spacing-3);
  }

  .toolbar-left,
  .toolbar-right {
    display: flex;
    align-items: center;
    gap: var(--spacing-2);
  }

  .ads-title {
    font-size: var(--font-size-base);
    font-weight: 600;
    margin: 0;
    display: flex;
    align-items: center;
    gap: var(--spacing-2);
  }

  .ads-count {
    font-size: var(--font-size-sm);
    font-weight: 400;
    color: var(--color-text-secondary);
    background-color: var(--color-gray-100);
    padding: 2px var(--spacing-2);
    border-radius: var(--radius-full);
  }

  .status-select {
    padding: var(--spacing-1) var(--spacing-2);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    font-size: var(--font-size-sm);
    background-color: var(--color-bg-primary);

    &:focus {
      outline: none;
      border-color: var(--color-primary-500);
    }
  }

  .refresh-btn {
    font-size: var(--font-size-sm);
  }

  // States inside ads panel
  .ads-loading,
  .ads-error,
  .ads-empty,
  .ads-initial {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: var(--spacing-12);
    text-align: center;
    gap: var(--spacing-3);
    color: var(--color-text-secondary);
  }

  .hint {
    font-size: var(--font-size-sm);
    color: var(--color-text-muted);
    max-width: 360px;
    line-height: 1.5;
  }

  // Table
  .ads-table-wrapper {
    flex: 1;
    overflow-y: auto;
    padding: var(--spacing-4) var(--spacing-5);
  }

  .ads-table {
    width: 100%;
    border-collapse: collapse;
    font-size: var(--font-size-sm);
  }

  .ads-table thead th {
    text-align: left;
    font-size: var(--font-size-xs);
    font-weight: 600;
    color: var(--color-text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: var(--spacing-2) var(--spacing-3);
    border-bottom: 1px solid var(--color-border);
    background-color: var(--color-bg-primary);
    position: sticky;
    top: 0;
  }

  .ad-row {
    cursor: pointer;
    transition: background-color var(--transition-fast);

    &:hover {
      background-color: var(--color-primary-50);
    }

    td {
      padding: var(--spacing-2) var(--spacing-3);
      border-bottom: 1px solid var(--color-border);
      vertical-align: middle;
    }
  }

  .col-id { width: 130px; }
  .col-body { }
  .col-start { width: 120px; white-space: nowrap; }
  .col-days { width: 100px; text-align: center; }
  .col-platforms { width: 120px; }
  .col-status { width: 90px; }

  .ad-id-text {
    font-family: monospace;
    font-size: var(--font-size-xs);
    color: var(--color-text-muted);
  }

  .ad-body-preview {
    color: var(--color-text-secondary);
    line-height: 1.4;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .days-badge {
    display: inline-block;
    padding: 2px var(--spacing-2);
    border-radius: var(--radius-full);
    font-weight: 600;
    font-size: var(--font-size-xs);

    &.days-high {
      background-color: var(--color-success-50);
      color: var(--color-success-700);
    }

    &.days-mid {
      background-color: var(--color-warning-50);
      color: #92400e;
    }

    &.days-low {
      background-color: var(--color-gray-100);
      color: var(--color-gray-600);
    }
  }

  .platforms-text {
    color: var(--color-text-secondary);
    font-size: var(--font-size-xs);
  }

  .status-dot {
    font-size: var(--font-size-xs);
    font-weight: 600;
    padding: 2px var(--spacing-2);
    border-radius: var(--radius-full);

    &.active {
      background-color: var(--color-success-50);
      color: var(--color-success-700);
    }

    &.inactive {
      background-color: var(--color-gray-100);
      color: var(--color-gray-600);
    }
  }
</style>
