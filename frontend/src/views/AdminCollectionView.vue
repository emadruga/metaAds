<template>
  <div class="admin-collection">
    <header class="admin-header">
      <div class="header-left">
        <router-link to="/" class="back-link">← Home</router-link>
        <h1 class="page-title">Collection Health</h1>
      </div>
      <button class="btn btn-secondary" :disabled="loading" @click="fetchAll">
        {{ loading ? 'Loading…' : 'Refresh' }}
      </button>
    </header>

    <main class="admin-main">
      <!-- Error state -->
      <div v-if="error" class="error-state">
        <div class="error-icon">⚠</div>
        <h3>Failed to load health data</h3>
        <p>{{ error }}</p>
        <button class="btn btn-primary" @click="fetchAll">Retry</button>
      </div>

      <!-- Loading state -->
      <div v-else-if="loading && !healthData" class="loading-state">
        <div class="spinner"></div>
        <p>Loading collection health…</p>
      </div>

      <template v-else-if="healthData">

        <!-- RATE-LIMIT ALERT BANNER -->
        <div v-if="currentHourUsage >= 160" class="alert-banner">
          ⚠ Rate limit at risk: {{ currentHourUsage }}/200 requests used this hour
          ({{ Math.round(currentHourUsage / 200 * 100) }}%)
        </div>

        <!-- Summary cards -->
        <section class="summary-section">
          <div class="summary-card">
            <div class="card-value">{{ healthData.summary.total_niches }}</div>
            <div class="card-label">Total niches</div>
          </div>
          <div class="summary-card">
            <div class="card-value">{{ healthData.summary.niches_with_auto_collect }}</div>
            <div class="card-label">Auto-collect enabled</div>
          </div>
          <div class="summary-card">
            <div class="card-value">{{ healthData.summary.total_runs_24h }}</div>
            <div class="card-label">Runs (last 24 h)</div>
          </div>
          <div class="summary-card" :class="successRateClass(healthData.summary)">
            <div class="card-value">{{ overallSuccessRate(healthData.summary) }}</div>
            <div class="card-label">Success rate (24 h)</div>
          </div>
        </section>

        <!-- Per-niche table -->
        <section class="table-section">
          <h2 class="section-title">Niche Details</h2>

          <div v-if="healthData.niches.length === 0" class="empty-state">
            <p>No niches found.</p>
          </div>

          <table v-else class="health-table">
            <thead>
              <tr>
                <th>Niche</th>
                <th>Auto-collect</th>
                <th>Last run</th>
                <th>Runs (24 h)</th>
                <th>Success rate</th>
                <th>Stale ads</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="niche in healthData.niches" :key="niche.niche_id"
                  :class="rowClass(niche)">
                <td class="niche-name-cell">
                  <router-link :to="`/n/${niche.slug}`">{{ niche.name }}</router-link>
                </td>
                <td>
                  <span class="badge" :class="niche.auto_collect_enabled ? 'badge-green' : 'badge-gray'">
                    {{ niche.auto_collect_enabled
                        ? `Every ${niche.auto_collect_interval_hours}h`
                        : 'Off' }}
                  </span>
                </td>
                <td>{{ formatHours(niche.hours_since_last_run) }}</td>
                <td>{{ niche.runs_24h }}</td>
                <td>{{ niche.success_rate != null ? `${niche.success_rate}%` : '—' }}</td>
                <td>
                  <span v-if="niche.stale_ads_count > 0" class="badge badge-warn">
                    {{ niche.stale_ads_count }}
                  </span>
                  <span v-else class="badge badge-green">0</span>
                </td>
                <td>
                  <span class="badge" :class="statusBadgeClass(niche.last_run_status)">
                    {{ niche.last_run_status ?? 'never run' }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </section>

        <!-- Stale-ads callout -->
        <section v-if="stalestNiches.length > 0" class="stale-section">
          <h2 class="section-title">Niches with stale ads</h2>
          <ul class="stale-list">
            <li v-for="niche in stalestNiches" :key="niche.niche_id" class="stale-item">
              <router-link :to="`/n/${niche.slug}`">{{ niche.name }}</router-link>
              — {{ niche.stale_ads_count }} ad(s) not seen in the last 24 h
            </li>
          </ul>
        </section>

        <!-- API REQUESTS/HOUR CHART -->
        <section class="chart-section">
          <div class="section-header">
            <h2 class="section-title">Meta API Requests / Hour (last 48 h)</h2>
            <div class="chart-legend">
              <span class="legend-item"><span class="dot dot-blue"></span> Requests</span>
              <span class="legend-item"><span class="dot dot-orange"></span> Alert (160)</span>
              <span class="legend-item"><span class="dot dot-red"></span> Limit (200)</span>
            </div>
          </div>
          <div v-if="rateLimitLoading" class="loading-inline">Loading chart…</div>
          <div v-else-if="rateLimitWindows.length === 0" class="empty-state">No rate-limit data yet.</div>
          <div v-else class="chart-container">
            <canvas ref="chartCanvas"></canvas>
          </div>
        </section>

        <!-- GLOBAL COLLECTION HISTORY -->
        <section class="table-section">
          <div class="section-header">
            <h2 class="section-title">Global Collection History</h2>
            <div class="filter-row">
              <select v-model="globalRunsHours" class="select-sm" @change="fetchGlobalRuns">
                <option :value="24">Last 24 h</option>
                <option :value="48">Last 48 h</option>
                <option :value="168">Last 7 d</option>
              </select>
            </div>
          </div>

          <div v-if="globalRunsLoading" class="loading-inline">Loading…</div>
          <div v-else-if="globalRuns.length === 0" class="empty-state">No runs in this period.</div>

          <div v-else class="table-scroll">
            <table class="health-table runs-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Niche ID</th>
                  <th>Keyword</th>
                  <th>Countries</th>
                  <th>Limit</th>
                  <th>API Reqs</th>
                  <th>Returned</th>
                  <th>New</th>
                  <th>Updated</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="run in globalRuns" :key="run.run_id">
                  <td class="mono">{{ formatTimestamp(run.started_at) }}</td>
                  <td class="mono truncate">{{ run.niche_id?.slice(-8) ?? '—' }}</td>
                  <td>{{ run.keyword ?? '—' }}</td>
                  <td>{{ (run.countries ?? []).join(', ') || '—' }}</td>
                  <td>{{ run.limit_requested ?? '—' }}</td>
                  <td>{{ run.api_requests_made ?? '—' }}</td>
                  <td>{{ run.ads_found ?? '—' }}</td>
                  <td>{{ run.ads_new ?? '—' }}</td>
                  <td>{{ run.ads_updated ?? '—' }}</td>
                  <td>
                    <span class="badge" :class="statusBadgeClass(run.status)">{{ run.status }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

      </template>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { collectApi } from '@/services/api'

// ---- state ----

const loading = ref(false)
const error = ref(null)
const healthData = ref(null)

const rateLimitLoading = ref(false)
const rateLimitWindows = ref([])
const currentHourUsage = ref(0)

const globalRunsLoading = ref(false)
const globalRuns = ref([])
const globalRunsHours = ref(24)

const chartCanvas = ref(null)
let chartInstance = null

// ---- fetch functions ----

async function fetchHealth() {
  loading.value = true
  error.value = null
  try {
    const res = await collectApi.getHealth()
    healthData.value = res.data.data
  } catch (err) {
    error.value = err.response?.data?.error ?? err.message ?? 'Unknown error'
  } finally {
    loading.value = false
  }
}

async function fetchRateLimitHistory() {
  rateLimitLoading.value = true
  try {
    const res = await collectApi.getRateLimitHistory(48)
    const windows = res.data.data ?? []
    windows.sort((a, b) => a.hour.localeCompare(b.hour))
    rateLimitWindows.value = windows

    const nowHour = new Date().toISOString().slice(0, 13)
    const cur = windows.find(w => w.hour === nowHour)
    currentHourUsage.value = cur?.total_requests ?? 0
  } catch (e) {
    console.warn('Rate-limit history fetch failed:', e.message)
  } finally {
    rateLimitLoading.value = false
  }
}

async function fetchGlobalRuns() {
  globalRunsLoading.value = true
  try {
    const res = await collectApi.getGlobalRuns({ hours: globalRunsHours.value, limit: 100 })
    globalRuns.value = res.data.data ?? []
  } catch (e) {
    console.warn('Global runs fetch failed:', e.message)
  } finally {
    globalRunsLoading.value = false
  }
}

async function fetchAll() {
  await Promise.all([fetchHealth(), fetchRateLimitHistory(), fetchGlobalRuns()])
}

// ---- chart ----

async function renderChart() {
  await nextTick()
  if (!chartCanvas.value || rateLimitWindows.value.length === 0) return

  const { Chart, registerables } = await import('chart.js')
  Chart.register(...registerables)

  if (chartInstance) {
    chartInstance.destroy()
    chartInstance = null
  }

  const labels = rateLimitWindows.value.map(w => {
    const [date, hour] = w.hour.split('T')
    const [, mm, dd] = date.split('-')
    return `${mm}-${dd} ${hour}h`
  })
  const data = rateLimitWindows.value.map(w => w.total_requests)

  chartInstance = new Chart(chartCanvas.value, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: 'API Requests',
          data,
          borderColor: '#4f46e5',
          backgroundColor: 'rgba(79,70,229,0.08)',
          pointRadius: 4,
          pointBackgroundColor: '#4f46e5',
          tension: 0.3,
          fill: true,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          min: 0,
          max: 220,
          ticks: { stepSize: 50 },
          grid: { color: 'rgba(0,0,0,0.06)' },
        },
        x: {
          ticks: { maxTicksLimit: 12, maxRotation: 45, font: { size: 11 } },
          grid: { color: 'rgba(0,0,0,0.04)' },
        },
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: { label: (ctx) => ` ${ctx.parsed.y} / 200 requests` },
        },
      },
    },
    plugins: [
      {
        id: 'thresholdLines',
        afterDraw(chart) {
          const { ctx, chartArea: { left, right }, scales: { y } } = chart
          const drawLine = (value, color) => {
            const yPx = y.getPixelForValue(value)
            ctx.save()
            ctx.beginPath()
            ctx.moveTo(left, yPx)
            ctx.lineTo(right, yPx)
            ctx.strokeStyle = color
            ctx.lineWidth = 1.5
            ctx.setLineDash([6, 3])
            ctx.stroke()
            ctx.restore()
          }
          drawLine(160, '#d69e2e')
          drawLine(200, '#e53e3e')
        },
      },
    ],
  })
}

watch(rateLimitWindows, () => {
  if (rateLimitWindows.value.length > 0) renderChart()
})

// ---- lifecycle ----

onMounted(fetchAll)

onUnmounted(() => {
  if (chartInstance) chartInstance.destroy()
})

// ---- computed ----

const stalestNiches = computed(() =>
  (healthData.value?.niches ?? []).filter((n) => n.stale_ads_count > 0)
)

// ---- helpers ----

function overallSuccessRate(summary) {
  if (!summary.total_runs_24h) return '—'
  const rate = (summary.total_successful_24h / summary.total_runs_24h) * 100
  return `${rate.toFixed(1)}%`
}

function successRateClass(summary) {
  if (!summary.total_runs_24h) return ''
  const rate = summary.total_successful_24h / summary.total_runs_24h
  if (rate >= 0.9) return 'card-good'
  if (rate >= 0.7) return 'card-warn'
  return 'card-bad'
}

function formatHours(hours) {
  if (hours == null) return 'Never'
  if (hours < 1) return `${Math.round(hours * 60)} min ago`
  return `${hours.toFixed(1)} h ago`
}

function formatTimestamp(iso) {
  if (!iso) return '—'
  try {
    return new Date(iso).toISOString().replace('T', ' ').slice(0, 16) + ' UTC'
  } catch {
    return iso
  }
}

function rowClass(niche) {
  if (niche.stale_ads_count > 0) return 'row-warn'
  if (niche.last_run_status === 'failed') return 'row-bad'
  return ''
}

function statusBadgeClass(status) {
  if (status === 'completed') return 'badge-green'
  if (status === 'failed' || status === 'error') return 'badge-red'
  if (status === 'pending' || status === 'running') return 'badge-blue'
  return 'badge-gray'
}
</script>

<style scoped>
.admin-collection {
  min-height: 100vh;
  background-color: var(--color-bg-secondary);
  color: var(--color-gray-900);
}

/* Header */
.admin-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-4) var(--spacing-6);
  background-color: var(--color-bg-primary);
  border-bottom: 1px solid var(--color-border);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.back-link {
  color: var(--color-text-secondary);
  text-decoration: none;
  font-size: var(--font-size-sm);
}

.back-link:hover { color: var(--color-gray-900); }

.page-title {
  font-size: var(--font-size-2xl);
  font-weight: 700;
  margin: 0;
}

/* Main */
.admin-main {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--spacing-8);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-6);
}

/* States */
.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 4rem;
  text-align: center;
}

.error-icon { font-size: 2.5rem; }

.loading-inline {
  color: var(--color-text-secondary);
  font-size: 0.875rem;
  padding: 1rem 0;
}

.spinner {
  width: 2rem;
  height: 2rem;
  border: 3px solid var(--color-gray-200);
  border-top-color: var(--color-primary-500);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

/* Alert Banner */
.alert-banner {
  background: rgba(214, 158, 46, 0.15);
  border: 1px solid rgba(214, 158, 46, 0.5);
  border-radius: var(--radius-md);
  padding: 0.85rem 1.25rem;
  font-size: 0.9rem;
  font-weight: 600;
  color: #744210;
}

/* Summary cards */
.summary-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: var(--spacing-4);
}

.summary-card {
  background-color: var(--color-bg-primary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 1.25rem 1.5rem;
  text-align: center;
  box-shadow: var(--shadow-sm, 0 1px 3px rgba(0,0,0,0.08));
}

.card-value {
  font-size: 2rem;
  font-weight: 700;
  color: var(--color-gray-900);
}

.card-label {
  font-size: 0.8rem;
  color: var(--color-text-secondary);
  margin-top: 0.25rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.card-good  { border-color: #38a169; }
.card-warn  { border-color: #d69e2e; }
.card-bad   { border-color: #e53e3e; }

/* Chart section */
.chart-section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
  background-color: var(--color-bg-primary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 1.25rem 1.5rem;
  box-shadow: var(--shadow-sm, 0 1px 3px rgba(0,0,0,0.08));
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.chart-legend {
  display: flex;
  gap: 1rem;
  font-size: 0.8rem;
  color: var(--color-text-secondary);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.35rem;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
}

.dot-blue   { background: #4f46e5; }
.dot-orange { background: #d69e2e; }
.dot-red    { background: #e53e3e; }

.chart-container {
  position: relative;
  height: 260px;
}

/* Table */
.table-section { display: flex; flex-direction: column; gap: var(--spacing-3); }

.section-title {
  font-size: var(--font-size-lg);
  font-weight: 600;
  margin: 0;
  color: var(--color-gray-900);
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.select-sm {
  padding: 0.3rem 0.6rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: 0.8rem;
  background: var(--color-bg-primary);
  color: var(--color-gray-900);
  cursor: pointer;
}

.table-scroll {
  overflow-x: auto;
}

.health-table {
  width: 100%;
  border-collapse: collapse;
  background-color: var(--color-bg-primary);
  border-radius: var(--radius-lg);
  overflow: hidden;
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-sm, 0 1px 3px rgba(0,0,0,0.08));
}

.health-table th {
  padding: 0.75rem 1rem;
  text-align: left;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-secondary);
  background-color: var(--color-bg-secondary);
  border-bottom: 1px solid var(--color-border);
  white-space: nowrap;
}

.health-table td {
  padding: 0.65rem 1rem;
  border-bottom: 1px solid var(--color-border);
  font-size: 0.875rem;
  color: var(--color-gray-900);
}

.health-table tr:last-child td { border-bottom: none; }
.health-table tbody tr:hover { background-color: var(--color-gray-50, #f9fafb); }

.row-warn { background-color: rgba(214, 158, 46, 0.06); }
.row-bad  { background-color: rgba(229, 62, 62, 0.06); }

.niche-name-cell a {
  color: var(--color-primary-600, #4f46e5);
  text-decoration: none;
  font-weight: 500;
}
.niche-name-cell a:hover { text-decoration: underline; }

.mono { font-family: monospace; font-size: 0.82rem; }
.truncate { max-width: 80px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* Badges */
.badge {
  display: inline-block;
  padding: 0.2rem 0.55rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 500;
}

.badge-green  { background: rgba(56, 161, 105, 0.12); color: #276749; }
.badge-gray   { background: rgba(113, 128, 150, 0.12); color: #4a5568; }
.badge-warn,
.badge-yellow { background: rgba(214, 158, 46, 0.15); color: #744210; }
.badge-red    { background: rgba(229, 62, 62, 0.12); color: #9b2c2c; }
.badge-blue   { background: rgba(102, 126, 234, 0.12); color: #3730a3; }

/* Stale section */
.stale-section { display: flex; flex-direction: column; gap: 0.75rem; }

.stale-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.stale-item {
  background: rgba(214, 158, 46, 0.08);
  border: 1px solid rgba(214, 158, 46, 0.35);
  border-radius: var(--radius-md);
  padding: 0.75rem 1rem;
  font-size: 0.875rem;
  color: var(--color-gray-900);
}

.stale-item a { color: var(--color-primary-600, #4f46e5); text-decoration: none; }
.stale-item a:hover { text-decoration: underline; }

/* Buttons */
.btn {
  padding: 0.5rem 1rem;
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: opacity 0.15s;
}
.btn:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-primary   { background-color: var(--color-primary-500); color: white; }
.btn-secondary {
  background-color: var(--color-gray-100);
  color: var(--color-gray-700);
  border: 1px solid var(--color-border);
}
.btn-primary:not(:disabled):hover  { opacity: 0.85; }
.btn-secondary:not(:disabled):hover { background-color: var(--color-gray-200, #e2e8f0); }

.empty-state { color: var(--color-text-secondary); padding: 2rem; text-align: center; }
</style>
