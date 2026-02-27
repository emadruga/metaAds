/**
 * Unit tests for AdminCollectionView.vue — collection health dashboard.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { nextTick } from 'vue'

// ---------------------------------------------------------------------------
// Shared mock state (vi.hoisted so it's available before vi.mock() runs)
// ---------------------------------------------------------------------------

const mockGetHealth = vi.hoisted(() => vi.fn())

// ---------------------------------------------------------------------------
// Module mocks
// ---------------------------------------------------------------------------

vi.mock('@/services/api', () => ({
  collectApi: { getHealth: mockGetHealth },
}))

vi.mock('vue-router', () => ({
  useRoute: () => ({ params: {} }),
  useRouter: () => ({ push: vi.fn() }),
  RouterLink: { template: '<a :href="to"><slot /></a>', props: ['to'] },
}))

import AdminCollectionView from '../AdminCollectionView.vue'

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeSummary(overrides = {}) {
  return {
    total_niches: 2,
    niches_with_auto_collect: 1,
    total_runs_24h: 4,
    total_successful_24h: 3,
    ...overrides,
  }
}

function makeNiche(overrides = {}) {
  return {
    niche_id: 'niche-1',
    slug: 'test-niche',
    name: 'Test Niche',
    auto_collect_enabled: true,
    auto_collect_interval_hours: 6,
    hours_since_last_run: 2.0,
    runs_24h: 3,
    successful_24h: 3,
    success_rate: 100.0,
    stale_ads_count: 0,
    last_run_status: 'completed',
    ...overrides,
  }
}

function makeHealthResponse(summaryOverrides = {}, niches = [makeNiche()]) {
  return {
    data: {
      success: true,
      data: {
        summary: makeSummary(summaryOverrides),
        niches,
      },
    },
  }
}

function mountView() {
  return mount(AdminCollectionView, {
    attachTo: document.body,
    global: {
      stubs: {
        RouterLink: { template: '<a :href="to"><slot /></a>', props: ['to'] },
      },
    },
  })
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('AdminCollectionView — initial load', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('calls collectApi.getHealth on mount', async () => {
    mockGetHealth.mockResolvedValueOnce(makeHealthResponse())
    mountView()
    expect(mockGetHealth).toHaveBeenCalledTimes(1)
  })

  it('shows loading spinner before data arrives', async () => {
    // Never resolves during this test
    mockGetHealth.mockReturnValue(new Promise(() => {}))
    const wrapper = mountView()
    // Wait one tick for onMounted → fetchHealth() to set loading=true and Vue to re-render
    await nextTick()
    expect(wrapper.find('.spinner').exists()).toBe(true)
  })

  it('renders summary cards after successful fetch', async () => {
    mockGetHealth.mockResolvedValueOnce(
      makeHealthResponse({ total_niches: 3, total_runs_24h: 10 })
    )
    const wrapper = mountView()
    await flushPromises()

    const cards = wrapper.findAll('.summary-card')
    expect(cards.length).toBe(4)

    // First card shows total niches
    expect(cards[0].find('.card-value').text()).toBe('3')
    // Third card shows total runs
    expect(cards[2].find('.card-value').text()).toBe('10')
  })

  it('renders one row per niche in the table', async () => {
    mockGetHealth.mockResolvedValueOnce(
      makeHealthResponse({}, [makeNiche({ niche_id: 'a' }), makeNiche({ niche_id: 'b' })])
    )
    const wrapper = mountView()
    await flushPromises()

    const rows = wrapper.findAll('.health-table tbody tr')
    expect(rows.length).toBe(2)
  })
})

describe('AdminCollectionView — summary calculations', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('displays overall success rate as percentage', async () => {
    mockGetHealth.mockResolvedValueOnce(
      makeHealthResponse({ total_runs_24h: 4, total_successful_24h: 3 })
    )
    const wrapper = mountView()
    await flushPromises()

    const cards = wrapper.findAll('.summary-card')
    // 4th card = success rate
    expect(cards[3].find('.card-value').text()).toBe('75.0%')
  })

  it('shows em-dash for success rate when no runs', async () => {
    mockGetHealth.mockResolvedValueOnce(
      makeHealthResponse({ total_runs_24h: 0, total_successful_24h: 0 })
    )
    const wrapper = mountView()
    await flushPromises()

    const cards = wrapper.findAll('.summary-card')
    expect(cards[3].find('.card-value').text()).toBe('—')
  })

  it('formats hours_since_last_run in hours', async () => {
    mockGetHealth.mockResolvedValueOnce(
      makeHealthResponse({}, [makeNiche({ hours_since_last_run: 3.5 })])
    )
    const wrapper = mountView()
    await flushPromises()

    const row = wrapper.find('.health-table tbody tr')
    expect(row.text()).toContain('3.5 h ago')
  })

  it('formats hours_since_last_run in minutes when less than 1 h', async () => {
    mockGetHealth.mockResolvedValueOnce(
      makeHealthResponse({}, [makeNiche({ hours_since_last_run: 0.5 })])
    )
    const wrapper = mountView()
    await flushPromises()

    const row = wrapper.find('.health-table tbody tr')
    expect(row.text()).toContain('30 min ago')
  })

  it('shows "Never" when hours_since_last_run is null', async () => {
    mockGetHealth.mockResolvedValueOnce(
      makeHealthResponse({}, [makeNiche({ hours_since_last_run: null, last_run_status: null })])
    )
    const wrapper = mountView()
    await flushPromises()

    const row = wrapper.find('.health-table tbody tr')
    expect(row.text()).toContain('Never')
  })
})

describe('AdminCollectionView — stale ads section', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('shows stale-ads section only when stale ads exist', async () => {
    mockGetHealth.mockResolvedValueOnce(
      makeHealthResponse({}, [makeNiche({ stale_ads_count: 5 })])
    )
    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.find('.stale-section').exists()).toBe(true)
    expect(wrapper.find('.stale-section').text()).toContain('5 ad(s) not seen in the last 24 h')
  })

  it('hides stale-ads section when all ads are fresh', async () => {
    mockGetHealth.mockResolvedValueOnce(
      makeHealthResponse({}, [makeNiche({ stale_ads_count: 0 })])
    )
    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.find('.stale-section').exists()).toBe(false)
  })
})

describe('AdminCollectionView — error handling', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('shows error message when fetch fails', async () => {
    mockGetHealth.mockRejectedValueOnce({
      message: 'Network Error',
      response: null,
    })
    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.find('.error-state').exists()).toBe(true)
    expect(wrapper.find('.error-state').text()).toContain('Network Error')
  })

  it('uses error.response.data.error when available', async () => {
    mockGetHealth.mockRejectedValueOnce({
      response: { data: { error: 'Unauthorized' } },
    })
    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.find('.error-state').text()).toContain('Unauthorized')
  })

  it('retry button calls fetchHealth again', async () => {
    mockGetHealth.mockRejectedValueOnce({ message: 'Oops' })
    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.find('.error-state').exists()).toBe(true)

    // Resolve on retry
    mockGetHealth.mockResolvedValueOnce(makeHealthResponse())
    await wrapper.find('.btn-primary').trigger('click')
    await flushPromises()

    expect(wrapper.find('.error-state').exists()).toBe(false)
    expect(wrapper.find('.summary-section').exists()).toBe(true)
    expect(mockGetHealth).toHaveBeenCalledTimes(2)
  })
})

describe('AdminCollectionView — empty state', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('shows empty-state message when niches list is empty', async () => {
    mockGetHealth.mockResolvedValueOnce(
      makeHealthResponse({ total_niches: 0 }, [])
    )
    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.find('.health-table').exists()).toBe(false)
    expect(wrapper.find('.empty-state').exists()).toBe(true)
  })
})

describe('AdminCollectionView — refresh button', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('Refresh button triggers another getHealth call', async () => {
    mockGetHealth.mockResolvedValue(makeHealthResponse())
    const wrapper = mountView()
    await flushPromises()

    await wrapper.find('button.btn-secondary').trigger('click')
    await flushPromises()

    expect(mockGetHealth).toHaveBeenCalledTimes(2)
  })
})
