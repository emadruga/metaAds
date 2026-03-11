<template>
  <div class="global-history">
    <!-- Header -->
    <header class="page-header">
      <div class="header-left">
        <router-link to="/" class="back-link">← Your Niches</router-link>
        <h1 class="page-title">🌐 Global History</h1>
      </div>
      <button class="btn btn-secondary btn-sm" @click="refresh" :disabled="loading">
        {{ loading ? 'Loading…' : '↻ Refresh' }}
      </button>
    </header>

    <!-- Rate-limit alert banner -->
    <div v-if="currentTotal >= alertThreshold" class="alert-banner" :class="currentTotal >= hardLimit ? 'alert-danger' : 'alert-warning'">
      ⚠️ Rate limit at risk: <strong>{{ currentTotal }}/{{ hardLimit }}</strong> Meta API requests used this hour
      (threshold: {{ alertThreshold }})
    </div>

    <!-- Rate-limit chart -->
    <section class="card chart-card">
      <div class="card-header">
        <h2>API Requests / Hour (last {{ chartHours }}h)</h2>
        <div class="chart-controls">
          <select v-model="chartHours" @change="loadRateLimitHistory" class="select-sm">
            <option :value="24">Last 24h</option>
            <option :value="48">Last 48h</option>
            <option :value="168">Last 7 days</option>
          </select>
        </div>
      </div>
      <div class="chart-wrapper">
        <canvas ref="chartCanvas"></canvas>
      </div>
    </section>

    <!-- Table controls -->
    <section class="card table-card">
      <div class="card-header">
        <h2>All Collection Runs</h2>
        <div class="table-controls">
          <select v-model="tableHours" @change="resetAndLoad" class="select-sm">
            <option :value="24">Last 24h</option>
            <option :value="48">Last 48h</option>
            <option :value="168">Last 7 days</option>
          </select>
        </div>
      </div>

      <div v-if="loadError" class="error-banner">{{ loadError }}</div>

      <div class="table-scroll">
        <table class="history-table">
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>User</th>
              <th>Niche</th>
              <th>Keyword</th>
              <th>Countries</th>
              <th>Solicited</th>
              <th>Returned</th>
              <th>New</th>
              <th>Updated</th>
              <th>API Reqs</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="runs.length === 0 && !loading">
              <td colspan="11" class="empty-row">No runs found for this period</td>
            </tr>
            <tr v-for="run in runs" :key="run.run_id">
              <td class="col-timestamp">{{ formatDate(run.started_at) }}</td>
              <td class="col-user">{{ run.user_email || '—' }}</td>
              <td class="col-niche">{{ run.niche_name || run.niche_id?.substring(0, 8) }}</td>
              <td class="col-keyword">{{ run.keyword || '—' }}</td>
              <td class="col-countries">{{ formatCountries(run.countries) }}</td>
              <td class="col-num">{{ run.limit_requested || '—' }}</td>
              <td class="col-num">{{ run.ads_found }}</td>
              <td class="col-num col-new">{{ run.ads_new }}</td>
              <td class="col-num">{{ run.ads_updated }}</td>
              <td class="col-num col-api" :class="apiReqClass(run.api_requests_made)">
                {{ run.api_requests_made || 0 }}
              </td>
              <td>
                <span class="status-badge" :class="`status-${run.status}`">
                  {{ run.status }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div class="pagination">
        <span class="pagination-info">Showing {{ runs.length }} run{{ runs.length !== 1 ? 's' : '' }}</span>
        <button
          v-if="nextCursor"
          class="btn btn-secondary btn-sm"
          @click="loadMore"
          :disabled="loadingMore"
        >
          {{ loadingMore ? 'Loading…' : 'Load more' }}
        </button>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { collectApi } from '@/services/api'

// ── State ──────────────────────────────────────────────────────────────────
const loading      = ref(false)
const loadingMore  = ref(false)
const loadError    = ref('')
const runs         = ref([])
const nextCursor   = ref(null)
const tableHours   = ref(24)
const chartHours   = ref(48)

// Rate-limit chart data
const currentTotal     = ref(0)
const alertThreshold   = ref(160)
const hardLimit        = ref(200)
const chartCanvas      = ref(null)
let   chartInstance    = null

// ── Lifecycle ───────────────────────────────────────────────────────────────
onMounted(async () => {
  await Promise.all([loadRateLimitHistory(), loadGlobalHistory()])
})

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.destroy()
    chartInstance = null
  }
})

// ── Data loading ────────────────────────────────────────────────────────────
async function loadRateLimitHistory() {
  try {
    const resp = await collectApi.getRateLimitHistory(chartHours.value)
    const d = resp.data
    currentTotal.value   = d.current_total || 0
    alertThreshold.value = d.alert_threshold || 160
    hardLimit.value      = d.hard_limit || 200
    await nextTick()
    renderChart(d.data || [], d.current_hour)
  } catch (err) {
    console.error('Rate limit history error:', err)
  }
}

async function loadGlobalHistory(cursor = null) {
  if (!cursor) {
    loading.value  = true
    loadError.value = ''
  } else {
    loadingMore.value = true
  }

  try {
    const params = { hours: tableHours.value, limit: 50 }
    if (cursor) params.cursor = cursor

    const resp = await collectApi.getGlobalHistory(params)
    const d = resp.data

    if (cursor) {
      runs.value = [...runs.value, ...d.data]
    } else {
      runs.value = d.data
    }

    // Always sort newest-first after any load/append, since DynamoDB scan
    // pages arrive in internal storage order — not chronological order.
    runs.value.sort((a, b) => {
      if (!a.started_at) return 1
      if (!b.started_at) return -1
      return new Date(b.started_at) - new Date(a.started_at)
    })

    nextCursor.value = d.next_cursor || null
  } catch (err) {
    loadError.value = err.response?.data?.error || 'Failed to load global history'
  } finally {
    loading.value     = false
    loadingMore.value = false
  }
}

function resetAndLoad() {
  runs.value    = []
  nextCursor.value = null
  loadGlobalHistory()
}

function loadMore() {
  if (nextCursor.value) loadGlobalHistory(nextCursor.value)
}

async function refresh() {
  runs.value = []
  nextCursor.value = null
  await Promise.all([loadRateLimitHistory(), loadGlobalHistory()])
}

// ── Chart ───────────────────────────────────────────────────────────────────
async function renderChart(buckets, currentHour) {
  const { Chart, registerables } = await import('chart.js')
  Chart.register(...registerables)

  if (chartInstance) {
    chartInstance.destroy()
    chartInstance = null
  }

  if (!chartCanvas.value) return

  // Build a complete hourly grid (newest → oldest)
  const now = new Date()
  const labels   = []
  const values   = []
  const bgColors = []

  const bucketMap = {}
  for (const b of buckets) {
    bucketMap[b.hour] = b.total_requests
  }

  for (let i = chartHours.value - 1; i >= 0; i--) {
    const d = new Date(now)
    d.setUTCHours(d.getUTCHours() - i, 0, 0, 0)
    const key = d.toISOString().substring(0, 13)  // "2026-03-05T06"
    labels.push(key.substring(11) + ':00')         // "06:00"
    const v = bucketMap[key] || 0
    values.push(v)
    bgColors.push(
      key === currentHour
        ? 'rgba(139, 92, 246, 0.7)'
        : v >= hardLimit.value
        ? 'rgba(239, 68, 68, 0.7)'
        : v >= alertThreshold.value
        ? 'rgba(251, 191, 36, 0.7)'
        : 'rgba(59, 130, 246, 0.5)'
    )
  }

  chartInstance = new Chart(chartCanvas.value, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {
          label: 'API Requests',
          data: values,
          backgroundColor: bgColors,
          borderColor: bgColors.map(c => c.replace('0.5', '1').replace('0.7', '1')),
          borderWidth: 1,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: ctx => `${ctx.parsed.y} requests`,
          },
        },
        annotation: undefined,
      },
      scales: {
        y: {
          beginAtZero: true,
          max: Math.max(hardLimit.value + 20, Math.max(...values) + 10),
          ticks: { stepSize: 40 },
        },
        x: {
          ticks: {
            maxRotation: 45,
            autoSkip: true,
            maxTicksLimit: 24,
          },
        },
      },
    },
    plugins: [
      {
        id: 'thresholdLines',
        afterDraw(chart) {
          const { ctx, chartArea, scales } = chart
          const drawLine = (value, color, label) => {
            const y = scales.y.getPixelForValue(value)
            ctx.save()
            ctx.strokeStyle = color
            ctx.lineWidth = 1.5
            ctx.setLineDash([6, 4])
            ctx.beginPath()
            ctx.moveTo(chartArea.left, y)
            ctx.lineTo(chartArea.right, y)
            ctx.stroke()
            ctx.fillStyle = color
            ctx.font = '11px sans-serif'
            ctx.fillText(label, chartArea.right - 60, y - 4)
            ctx.restore()
          }
          drawLine(alertThreshold.value, '#f59e0b', `Alert ${alertThreshold.value}`)
          drawLine(hardLimit.value, '#ef4444', `Limit ${hardLimit.value}`)
        },
      },
    ],
  })
}

// ── Formatters ───────────────────────────────────────────────────────────────
function formatDate(iso) {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString('en-US', {
      month: 'short', day: 'numeric',
      hour: '2-digit', minute: '2-digit',
    })
  } catch { return iso }
}

function formatCountries(arr) {
  if (!Array.isArray(arr)) return '—'
  return arr.slice(0, 3).join(', ') + (arr.length > 3 ? `…+${arr.length - 3}` : '')
}

function apiReqClass(n) {
  if (!n) return ''
  if (n >= 10) return 'high-reqs'
  if (n >= 5)  return 'med-reqs'
  return ''
}
</script>

<style lang="scss" scoped>
.global-history {
  min-height: 100vh;
  background-color: var(--color-bg-secondary);
  padding: var(--spacing-6);
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-4);
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--spacing-4);
}

.back-link {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  text-decoration: none;
  &:hover { color: var(--color-gray-900); }
}

.page-title {
  font-size: var(--font-size-2xl);
  font-weight: 600;
  margin: 0;
}

// Alert banner
.alert-banner {
  padding: var(--spacing-3) var(--spacing-4);
  border-radius: var(--radius-md);
  margin-bottom: var(--spacing-4);
  font-size: var(--font-size-sm);
  font-weight: 500;

  &.alert-warning {
    background-color: #fef3c7;
    border: 1px solid #f59e0b;
    color: #92400e;
  }
  &.alert-danger {
    background-color: #fee2e2;
    border: 1px solid #ef4444;
    color: #991b1b;
  }
}

// Cards
.card {
  background: var(--color-bg-primary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  margin-bottom: var(--spacing-6);
  overflow: hidden;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-4) var(--spacing-5);
  border-bottom: 1px solid var(--color-border);

  h2 {
    font-size: var(--font-size-lg);
    font-weight: 600;
    margin: 0;
  }
}

.chart-controls,
.table-controls {
  display: flex;
  gap: var(--spacing-2);
}

// Chart
.chart-wrapper {
  padding: var(--spacing-4);
  height: 280px;
}

// Table
.table-scroll {
  overflow-x: auto;
}

.history-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--font-size-sm);

  th, td {
    padding: var(--spacing-2) var(--spacing-3);
    text-align: left;
    white-space: nowrap;
    border-bottom: 1px solid var(--color-border);
  }

  th {
    background-color: var(--color-gray-50);
    font-weight: 600;
    color: var(--color-text-secondary);
    font-size: var(--font-size-xs);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  tr:last-child td { border-bottom: none; }
  tr:hover td { background-color: var(--color-gray-50); }
}

.col-num { text-align: right; }
.col-new { color: var(--color-primary-600); font-weight: 600; }
.col-api { font-weight: 600; }

.high-reqs { color: #ef4444; }
.med-reqs  { color: #f59e0b; }

.empty-row {
  text-align: center;
  padding: var(--spacing-8);
  color: var(--color-text-secondary);
}

// Status badges
.status-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
  font-weight: 600;

  &.status-completed  { background: #d1fae5; color: #065f46; }
  &.status-running    { background: #dbeafe; color: #1e40af; }
  &.status-pending    { background: #fef3c7; color: #92400e; }
  &.status-error      { background: #fee2e2; color: #991b1b; }
}

// Pagination
.pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-3) var(--spacing-5);
  border-top: 1px solid var(--color-border);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

// Controls
.select-sm {
  padding: var(--spacing-1) var(--spacing-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  background: var(--color-bg-primary);
  cursor: pointer;
}

.btn {
  padding: var(--spacing-2) var(--spacing-4);
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: all var(--transition-fast);

  &.btn-secondary {
    background: var(--color-gray-100);
    color: var(--color-gray-900);
    border: 1px solid var(--color-border);
    &:hover:not(:disabled) { background: var(--color-gray-200); }
    &:disabled { opacity: 0.6; cursor: not-allowed; }
  }

  &.btn-sm {
    padding: var(--spacing-1) var(--spacing-3);
    font-size: var(--font-size-xs);
  }
}

.error-banner {
  padding: var(--spacing-3) var(--spacing-4);
  background: #fee2e2;
  color: #991b1b;
  border-bottom: 1px solid #fecaca;
  font-size: var(--font-size-sm);
}
</style>
