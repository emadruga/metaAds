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
          <!-- Page identity -->
          <div class="meta-identity">
            <h2 class="meta-page-name">{{ competitor.page_name }}</h2>
            <span v-if="competitor.category" class="category-badge">{{ competitor.category }}</span>
          </div>

          <div class="meta-field">
            <span class="meta-label">Page ID</span>
            <span class="meta-value mono">{{ competitor.page_id }}</span>
          </div>

          <div class="meta-field" v-if="competitor.fan_count != null">
            <span class="meta-label">Page Followers</span>
            <span class="meta-value">{{ formatNumber(competitor.fan_count) }}</span>
          </div>

          <div class="meta-field">
            <span class="meta-label">Tracked Since</span>
            <span class="meta-value">{{ formatDate(competitor.added_at) }}</span>
          </div>

          <!-- AD PORTFOLIO section -->
          <div class="meta-section" v-if="agg">
            <span class="meta-section-title">Ad Portfolio</span>
            <div class="meta-stat-grid">
              <div class="meta-stat">
                <span class="meta-stat-value highlight">{{ agg.total_ads_found ?? adsData?.count ?? '—' }}</span>
                <span class="meta-stat-label">Total Ads</span>
              </div>
              <div class="meta-stat">
                <span class="meta-stat-value">{{ adsData?.count ?? '—' }}</span>
                <span class="meta-stat-label">{{ statusFilter }} Ads</span>
              </div>
              <div class="meta-stat">
                <span class="meta-stat-value">{{ agg.new_ads_last_30d ?? '—' }}</span>
                <span class="meta-stat-label">New (30d)</span>
              </div>
              <div class="meta-stat">
                <span class="meta-stat-value">{{ longestRunningAd?.days_active ?? '—' }}</span>
                <span class="meta-stat-label">Max Days</span>
              </div>
              <div class="meta-stat" v-if="avgDaysActive !== null">
                <span class="meta-stat-value">{{ avgDaysActive }}</span>
                <span class="meta-stat-label">Avg Days</span>
              </div>
              <div class="meta-stat" v-if="agg.kill_threshold_days != null">
                <span class="meta-stat-value">{{ agg.kill_threshold_days }}</span>
                <span class="meta-stat-label">Kill Threshold</span>
              </div>
            </div>
          </div>

          <!-- SPEND ESTIMATES section -->
          <div class="meta-section" v-if="agg && (agg.spend_all_time?.max > 0)">
            <span class="meta-section-title">Spend Estimate</span>
            <div class="spend-row">
              <span class="spend-label">All-time</span>
              <span class="spend-range">
                {{ formatMoney(agg.spend_all_time.min) }} – {{ formatMoney(agg.spend_all_time.max) }}
              </span>
            </div>
            <div class="spend-row" v-if="agg.spend_30d?.max > 0">
              <span class="spend-label">Last 30 days</span>
              <span class="spend-range">
                {{ formatMoney(agg.spend_30d.min) }} – {{ formatMoney(agg.spend_30d.max) }}
              </span>
            </div>
            <p class="spend-note">Mid-point of Meta's disclosed ranges</p>
          </div>

          <!-- CREATIVE MIX section -->
          <div class="meta-section" v-if="agg && Object.keys(agg.media_type_pct || {}).length > 0">
            <span class="meta-section-title">Creative Mix</span>
            <div class="mix-bars">
              <div
                v-for="(pct, type) in agg.media_type_pct"
                :key="type"
                class="mix-bar-row"
              >
                <span class="mix-type">{{ formatMediaType(type) }}</span>
                <div class="mix-bar-track">
                  <div class="mix-bar-fill" :style="{ width: pct + '%' }"></div>
                </div>
                <span class="mix-pct">{{ pct }}%</span>
              </div>
            </div>
          </div>

          <!-- PLATFORM DISTRIBUTION section -->
          <div class="meta-section" v-if="agg && Object.keys(agg.platform_pct || {}).length > 0">
            <span class="meta-section-title">Platforms</span>
            <div class="mix-bars">
              <div
                v-for="(pct, platform) in agg.platform_pct"
                :key="platform"
                class="mix-bar-row"
              >
                <span class="mix-type">{{ formatPlatformName(platform) }}</span>
                <div class="mix-bar-track">
                  <div class="mix-bar-fill platform" :style="{ width: pct + '%' }"></div>
                </div>
                <span class="mix-pct">{{ pct }}%</span>
              </div>
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
              <option value="ALL">All ads</option>
              <option value="ACTIVE">Active only</option>
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
                <th class="col-expand"></th>
                <th class="col-type">Type</th>
                <th class="col-body">Ad Copy</th>
                <th class="col-start">Started</th>
                <th class="col-days">Days Active</th>
                <th class="col-status">Status</th>
              </tr>
            </thead>
            <tbody>
              <template v-for="group in filteredAds" :key="group.variant_key">
                <!-- Group row -->
                <tr class="ad-row" @click="selectedAd = group.ads[0]">
                  <td class="col-expand">
                    <button
                      v-if="group.count > 1"
                      class="expand-btn"
                      @click.stop="toggleGroup(group.variant_key)"
                      :title="expandedGroups.has(group.variant_key) ? 'Collapse' : 'Expand variants'"
                    >
                      {{ expandedGroups.has(group.variant_key) ? '−' : '+' }}
                      <span class="variant-count">{{ group.count }}</span>
                    </button>
                  </td>
                  <td class="col-type">
                    <span :class="['media-badge', mediaClass(group.media_type)]">
                      {{ formatMediaType(group.media_type) }}
                    </span>
                  </td>
                  <td class="col-body">
                    <span class="ad-body-preview">{{ truncate(group.body || group.headline, 120) }}</span>
                  </td>
                  <td class="col-start">{{ formatDate(group.start_date) }}</td>
                  <td class="col-days">
                    <span :class="['days-badge', daysClass(group.days_active)]">
                      {{ group.days_active ?? '—' }}
                    </span>
                  </td>
                  <td class="col-status">
                    <span :class="['status-dot', group.is_active ? 'active' : 'inactive']">
                      {{ group.is_active ? 'Active' : 'Ended' }}
                    </span>
                  </td>
                </tr>
                <!-- Variant child rows -->
                <template v-if="expandedGroups.has(group.variant_key)">
                  <tr
                    v-for="(ad, i) in group.ads"
                    :key="ad.meta_ad_id"
                    class="ad-row variant-row"
                    @click="selectedAd = ad"
                  >
                    <td class="col-expand">
                      <span class="variant-indent">└</span>
                    </td>
                    <td class="col-type">
                      <span :class="['media-badge', mediaClass(ad.media_type)]">
                        {{ formatMediaType(ad.media_type) }}
                      </span>
                    </td>
                    <td class="col-body">
                      <span class="variant-label">Variant {{ i + 1 }}</span>
                      <span class="ad-body-preview">{{ truncate(ad.body || ad.headline, 100) }}</span>
                    </td>
                    <td class="col-start">{{ formatDate(ad.start_date) }}</td>
                    <td class="col-days">
                      <span :class="['days-badge', daysClass(ad.days_active)]">
                        {{ ad.days_active ?? '—' }}
                      </span>
                    </td>
                    <td class="col-status">
                      <span :class="['status-dot', ad.is_active ? 'active' : 'inactive']">
                        {{ ad.is_active ? 'Active' : 'Ended' }}
                      </span>
                    </td>
                  </tr>
                </template>
              </template>
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
  const statusFilter = ref('ALL')
  const storeError = ref('')
  const notesValue = ref('')
  const expandedGroups = ref(new Set())

  const competitor = computed(() => store.competitorByPageId(pageId.value))

  const adsData = computed(() => store.getAdsForPage(pageId.value))
  const agg = computed(() => adsData.value?.aggregates || null)

  const filteredAds = computed(() => adsData.value?.ads || [])

  // Flatten all individual ads across groups for stats
  const allIndividualAds = computed(() =>
    filteredAds.value.flatMap((g) => g.ads || [])
  )

  const longestRunningAd = computed(() => {
    const ads = allIndividualAds.value
    if (!ads.length) return null
    return ads.reduce((best, a) =>
      (a.days_active || 0) > (best.days_active || 0) ? a : best
    )
  })

  const avgDaysActive = computed(() => {
    const ads = allIndividualAds.value.filter((a) => a.days_active != null)
    if (!ads.length) return null
    const sum = ads.reduce((s, a) => s + a.days_active, 0)
    return Math.round(sum / ads.length)
  })

  function toggleGroup(variantKey) {
    const s = new Set(expandedGroups.value)
    s.has(variantKey) ? s.delete(variantKey) : s.add(variantKey)
    expandedGroups.value = s
  }

  const statusLabel = computed(() => {
    const map = { ACTIVE: 'Active', INACTIVE: 'Inactive', ALL: 'All' }
    return map[statusFilter.value] || statusFilter.value
  })

  async function loadAds() {
    if (!pageId.value) return
    try {
      const params = { status: statusFilter.value, limit: 200 }
      const c = competitor.value?.countries
      if (c) params.countries = c
      await store.fetchCompetitorAds(pageId.value, params)
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

  function formatPlatformName(p) {
    const labels = { facebook: 'Facebook', instagram: 'Instagram', messenger: 'Messenger', audience_network: 'Audience Network' }
    return labels[p] || p
  }

  function formatNumber(n) {
    if (n == null) return '—'
    if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M'
    if (n >= 1_000) return (n / 1_000).toFixed(1) + 'K'
    return String(n)
  }

  function formatMoney(raw) {
    const n = parseInt(raw || 0, 10)
    if (!n) return '$0'
    if (n >= 1_000_000) return '$' + (n / 1_000_000).toFixed(1) + 'M'
    if (n >= 1_000) return '$' + Math.round(n / 1_000) + 'K'
    return '$' + n
  }

  function formatMediaType(type) {
    if (!type) return '?'
    const map = { VIDEO: 'Video', IMAGE: 'Image', PHOTO: 'Image', CAROUSEL: 'Carousel', OTHER: 'Other' }
    return map[type.toUpperCase()] || type
  }

  function mediaClass(type) {
    if (!type) return 'media-other'
    const t = type.toUpperCase()
    if (t === 'VIDEO') return 'media-video'
    if (t === 'IMAGE') return 'media-image'
    if (t === 'CAROUSEL') return 'media-carousel'
    return 'media-other'
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

  .meta-identity {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-1);
  }

  .meta-page-name {
    font-size: var(--font-size-lg);
    font-weight: 700;
    color: var(--color-gray-900);
    margin: 0;
    line-height: 1.3;
    word-break: break-word;
  }

  .category-badge {
    font-size: var(--font-size-xs);
    color: var(--color-text-muted);
    background-color: var(--color-gray-100);
    border-radius: var(--radius-full);
    padding: 2px var(--spacing-2);
    align-self: flex-start;
  }

  // Section groupings within left panel
  .meta-section {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-2);
    padding-top: var(--spacing-3);
    border-top: 1px solid var(--color-border);
  }

  .meta-section-title {
    font-size: var(--font-size-xs);
    font-weight: 700;
    color: var(--color-text-muted);
    text-transform: uppercase;
    letter-spacing: 0.07em;
  }

  // Stat grid inside Ad Portfolio section
  .meta-stat-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--spacing-2) var(--spacing-3);
  }

  .meta-stat {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .meta-stat-value {
    font-size: var(--font-size-base);
    font-weight: 700;
    color: var(--color-gray-900);

    &.highlight {
      color: var(--color-primary-600);
      font-size: var(--font-size-xl);
    }
  }

  .meta-stat-label {
    font-size: var(--font-size-xs);
    color: var(--color-text-muted);
  }

  // Spend estimate
  .spend-row {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: var(--spacing-2);
  }

  .spend-label {
    font-size: var(--font-size-xs);
    color: var(--color-text-muted);
    white-space: nowrap;
  }

  .spend-range {
    font-size: var(--font-size-sm);
    font-weight: 600;
    color: var(--color-gray-900);
    text-align: right;
  }

  .spend-note {
    font-size: 10px;
    color: var(--color-text-muted);
    margin: 0;
    font-style: italic;
  }

  // Creative mix / platform bar charts
  .mix-bars {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-2);
  }

  .mix-bar-row {
    display: grid;
    grid-template-columns: 70px 1fr 32px;
    align-items: center;
    gap: var(--spacing-2);
  }

  .mix-type {
    font-size: var(--font-size-xs);
    color: var(--color-text-secondary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .mix-bar-track {
    height: 6px;
    background-color: var(--color-gray-100);
    border-radius: var(--radius-full);
    overflow: hidden;
  }

  .mix-bar-fill {
    height: 100%;
    background-color: var(--color-primary-400);
    border-radius: var(--radius-full);
    transition: width 0.4s ease;

    &.platform {
      background-color: var(--color-success-400, #34d399);
    }
  }

  .mix-pct {
    font-size: var(--font-size-xs);
    font-weight: 600;
    color: var(--color-text-secondary);
    text-align: right;
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

  .col-expand { width: 44px; text-align: center; }
  .col-type { width: 80px; }
  .col-body { }
  .col-start { width: 110px; white-space: nowrap; }
  .col-days { width: 90px; text-align: center; }
  .col-status { width: 80px; }

  .media-badge {
    display: inline-block;
    font-size: 10px;
    font-weight: 700;
    padding: 2px 5px;
    border-radius: var(--radius-sm);
    text-transform: uppercase;
    letter-spacing: 0.03em;

    &.media-video    { background-color: #ede9fe; color: #6d28d9; }
    &.media-image    { background-color: #dbeafe; color: #1d4ed8; }
    &.media-carousel { background-color: #fef3c7; color: #92400e; }
    &.media-other    { background-color: var(--color-gray-100); color: var(--color-gray-600); }
  }

  .spend-text {
    font-size: var(--font-size-xs);
    color: var(--color-text-secondary);

    &.muted { color: var(--color-text-muted); }
  }

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

  .expand-btn {
    display: inline-flex;
    align-items: center;
    gap: 2px;
    padding: 2px 5px;
    border: 1px solid var(--color-border);
    border-radius: var(--radius-sm);
    background-color: var(--color-bg-primary);
    font-size: 11px;
    font-weight: 700;
    color: var(--color-primary-600);
    cursor: pointer;
    line-height: 1;

    &:hover {
      background-color: var(--color-primary-50);
    }
  }

  .variant-count {
    font-size: 10px;
    font-weight: 600;
    color: var(--color-text-muted);
  }

  .variant-row {
    background-color: var(--color-gray-50);

    &:hover {
      background-color: var(--color-primary-50);
    }
  }

  .variant-indent {
    color: var(--color-text-muted);
    font-size: var(--font-size-sm);
  }

  .variant-label {
    display: block;
    font-size: 10px;
    font-weight: 600;
    color: var(--color-text-muted);
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 2px;
  }
</style>
