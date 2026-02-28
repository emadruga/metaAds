<template>
  <div class="history-view">
    <div class="history-header">
      <h2 class="section-title">Collection History</h2>
      <button class="btn btn-secondary" :disabled="loading" @click="fetchRuns">
        {{ loading ? 'Loading…' : 'Refresh' }}
      </button>
    </div>

    <div v-if="error" class="error-state">
      <span class="error-icon">⚠</span>
      <span>{{ error }}</span>
      <button class="btn btn-primary" @click="fetchRuns">Retry</button>
    </div>

    <div v-else-if="loading && !runs.length" class="loading-state">
      <div class="spinner"></div>
      <span>Loading history…</span>
    </div>

    <div v-else-if="!runs.length" class="empty-state">
      <p>No collection runs yet for this niche.</p>
      <p class="hint">Click <strong>📥 Collect Ads</strong> to start your first run.</p>
    </div>

    <div v-else class="table-wrapper">
      <table class="history-table">
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>Countries</th>
            <th>Keyword</th>
            <th>Solicited</th>
            <th>Returned</th>
            <th>New</th>
            <th>Updated</th>
            <th>#Ads</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="run in runs" :key="run.run_id" :class="rowClass(run.status)">
            <td class="ts-cell">{{ formatTs(run.started_at) }}</td>
            <td class="countries-cell">{{ formatCountries(run.countries) }}</td>
            <td class="keyword-cell">{{ run.keyword ?? '—' }}</td>
            <td class="num-cell">{{ run.limit_requested || '—' }}</td>
            <td class="num-cell">{{ run.ads_found ?? '—' }}</td>
            <td class="num-cell new-cell">{{ run.ads_new ?? '—' }}</td>
            <td class="num-cell upd-cell">{{ run.ads_updated ?? '—' }}</td>
            <td class="num-cell total-cell">{{ run.total_ads_after > 0 ? run.total_ads_after : '—' }}</td>
            <td>
              <span class="badge" :class="statusClass(run.status)">
                {{ run.status ?? 'unknown' }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { collectApi } from '@/services/api'

const route = useRoute()
const loading = ref(false)
const error = ref(null)
const runs = ref([])

async function fetchRuns() {
  const slug = route.params.nicheSlug
  loading.value = true
  error.value = null
  try {
    const res = await collectApi.getRuns(slug, { limit: 50 })
    runs.value = res.data.data ?? []
  } catch (err) {
    error.value = err.response?.data?.error ?? err.message ?? 'Unknown error'
  } finally {
    loading.value = false
  }
}

onMounted(fetchRuns)

function flagEmoji(code) {
  // Convert ISO 3166-1 alpha-2 code to regional indicator emoji pair
  return [...code.toUpperCase()].map(c =>
    String.fromCodePoint(c.charCodeAt(0) + 0x1F1A5)
  ).join('')
}

function formatCountries(list) {
  if (!list || !list.length) return '—'
  return list.slice(0, 3).map(flagEmoji).join(' ')
}

function formatTs(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

function statusClass(status) {
  if (status === 'completed') return 'badge-green'
  if (status === 'failed') return 'badge-red'
  if (status === 'running' || status === 'pending') return 'badge-blue'
  return 'badge-gray'
}

function rowClass(status) {
  if (status === 'failed') return 'row-bad'
  return ''
}
</script>

<style lang="scss" scoped>
.history-view {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
}

.history-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.section-title {
  font-size: var(--font-size-lg);
  font-weight: 600;
  margin: 0;
  color: var(--color-gray-900);
}

/* States */
.loading-state,
.error-state,
.empty-state {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 3rem;
  justify-content: center;
  color: var(--color-text-secondary);
}

.error-state { color: var(--color-error, #dc2626); }

.error-icon { font-size: 1.25rem; }

.spinner {
  width: 1.5rem;
  height: 1.5rem;
  border: 2px solid var(--color-gray-200);
  border-top-color: var(--color-primary-500);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  flex-shrink: 0;
}

@keyframes spin { to { transform: rotate(360deg); } }

.hint { font-size: var(--font-size-sm); }

/* Table */
.table-wrapper {
  overflow-x: auto;
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.history-table {
  width: 100%;
  border-collapse: collapse;
  background-color: var(--color-bg-primary);
  font-size: 0.875rem;
}

.history-table th {
  padding: 0.6rem 1rem;
  text-align: left;
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-secondary);
  background-color: var(--color-bg-secondary);
  border-bottom: 1px solid var(--color-border);
  white-space: nowrap;
}

.history-table td {
  padding: 0.6rem 1rem;
  border-bottom: 1px solid var(--color-border);
  color: var(--color-gray-900);
  vertical-align: middle;
}

.history-table tr:last-child td { border-bottom: none; }
.history-table tbody tr:hover { background-color: var(--color-gray-50, #f9fafb); }

.row-bad { background-color: rgba(229, 62, 62, 0.05); }

.ts-cell       { white-space: nowrap; color: var(--color-text-secondary); font-size: 0.8rem; }
.countries-cell { white-space: nowrap; font-size: 1rem; letter-spacing: 0.1em; }
.keyword-cell { font-weight: 500; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.num-cell  { text-align: right; font-variant-numeric: tabular-nums; }
.new-cell   { color: #276749; }
.upd-cell   { color: #3730a3; }
.total-cell { color: var(--color-gray-700); font-weight: 600; }

/* Badges */
.badge {
  display: inline-block;
  padding: 0.2rem 0.5rem;
  border-radius: 9999px;
  font-size: 0.72rem;
  font-weight: 500;
  white-space: nowrap;
}

.badge-green { background: rgba(56, 161, 105, 0.12); color: #276749; }
.badge-gray  { background: rgba(113, 128, 150, 0.12); color: #4a5568; }
.badge-red   { background: rgba(229, 62, 62, 0.12); color: #9b2c2c; }
.badge-blue  { background: rgba(102, 126, 234, 0.12); color: #3730a3; }

/* Buttons */
.btn {
  padding: 0.4rem 0.9rem;
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  font-weight: 500;
  cursor: pointer;
  border: none;
}
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-primary  { background-color: var(--color-primary-500); color: white; }
.btn-secondary {
  background-color: var(--color-gray-100);
  color: var(--color-gray-700);
  border: 1px solid var(--color-border);
}
.btn-primary:not(:disabled):hover  { opacity: 0.85; }
.btn-secondary:not(:disabled):hover { background-color: var(--color-gray-200, #e2e8f0); }
</style>
