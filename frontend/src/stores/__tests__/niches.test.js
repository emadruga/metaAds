/**
 * Unit tests for niches.js store — toggleAutoCollect action.
 *
 * Run from the frontend directory:
 *   npm test
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

// ---------------------------------------------------------------------------
// Mock the API module — no real HTTP calls
// ---------------------------------------------------------------------------

vi.mock('@/services/api', () => ({
  nicheApi: {
    list: vi.fn(),
    get: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
  },
  devMode: false,
}))

import { nicheApi } from '@/services/api'
import { useNichesStore } from '../niches'

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const makeNiche = (overrides = {}) => ({
  slug: 'test-niche',
  name: 'Test Niche',
  auto_collect_enabled: false,
  auto_collect_interval_hours: 3,
  ...overrides,
})

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('useNichesStore — toggleAutoCollect', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('applies optimistic update immediately (before API resolves)', async () => {
    const store = useNichesStore()
    store.niches = [makeNiche()]

    // API is pending — never resolves during this check
    let resolveApi
    nicheApi.update.mockReturnValue(new Promise(r => { resolveApi = r }))

    const promise = store.toggleAutoCollect('test-niche', true)

    // Optimistic update must be visible synchronously (before await)
    expect(store.niches[0].auto_collect_enabled).toBe(true)

    // Clean up — resolve so the promise finishes
    resolveApi({ data: { data: makeNiche({ auto_collect_enabled: true }) } })
    await promise
  })

  it('replaces niche data with API response on success', async () => {
    const store = useNichesStore()
    store.niches = [makeNiche()]

    const serverNiche = makeNiche({ auto_collect_enabled: true, updated_at: '2026-02-27T00:00:00Z' })
    nicheApi.update.mockResolvedValue({ data: { data: serverNiche } })

    await store.toggleAutoCollect('test-niche', true)

    expect(store.niches[0]).toEqual(serverNiche)
  })

  it('calls nicheApi.update with the correct payload', async () => {
    const store = useNichesStore()
    store.niches = [makeNiche()]
    nicheApi.update.mockResolvedValue({ data: { data: makeNiche({ auto_collect_enabled: true }) } })

    await store.toggleAutoCollect('test-niche', true)

    expect(nicheApi.update).toHaveBeenCalledWith('test-niche', { auto_collect_enabled: true })
  })

  it('reverts optimistic update when API fails', async () => {
    const store = useNichesStore()
    store.niches = [makeNiche({ auto_collect_enabled: false })]
    nicheApi.update.mockRejectedValue(new Error('Network error'))

    await expect(store.toggleAutoCollect('test-niche', true)).rejects.toThrow()

    expect(store.niches[0].auto_collect_enabled).toBe(false)
  })

  it('re-throws the API error so callers can handle it', async () => {
    const store = useNichesStore()
    store.niches = [makeNiche()]
    nicheApi.update.mockRejectedValue(new Error('Server error'))

    await expect(store.toggleAutoCollect('test-niche', true)).rejects.toThrow('Server error')
  })

  it('does NOT set loading=true at any point', async () => {
    const store = useNichesStore()
    store.niches = [makeNiche()]

    let resolveApi
    nicheApi.update.mockReturnValue(new Promise(r => { resolveApi = r }))

    const promise = store.toggleAutoCollect('test-niche', true)

    // During in-flight request, loading must stay false
    expect(store.loading).toBe(false)

    resolveApi({ data: { data: makeNiche({ auto_collect_enabled: true }) } })
    await promise

    expect(store.loading).toBe(false)
  })

  it('also applies optimistic update to currentNiche when slug matches', async () => {
    const store = useNichesStore()
    store.niches = [makeNiche()]
    store.currentNiche = makeNiche()
    nicheApi.update.mockResolvedValue({ data: { data: makeNiche({ auto_collect_enabled: true }) } })

    await store.toggleAutoCollect('test-niche', true)

    expect(store.currentNiche.auto_collect_enabled).toBe(true)
  })

  it('reverts currentNiche on API failure', async () => {
    const store = useNichesStore()
    store.niches = [makeNiche()]
    store.currentNiche = makeNiche({ auto_collect_enabled: false })
    nicheApi.update.mockRejectedValue(new Error('Fail'))

    await expect(store.toggleAutoCollect('test-niche', true)).rejects.toThrow()

    expect(store.currentNiche.auto_collect_enabled).toBe(false)
  })

  it('does not touch niches/currentNiche for a slug that is not in the list', async () => {
    const store = useNichesStore()
    store.niches = [makeNiche({ slug: 'other-niche' })]
    nicheApi.update.mockResolvedValue({ data: { data: makeNiche({ slug: 'test-niche' }) } })

    await store.toggleAutoCollect('test-niche', true)

    // The other niche is untouched
    expect(store.niches[0].slug).toBe('other-niche')
    expect(store.niches[0].auto_collect_enabled).toBe(false)
  })
})
