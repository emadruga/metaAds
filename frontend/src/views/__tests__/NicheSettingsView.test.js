/**
 * Unit tests for NicheSettingsView.vue — keyword counter and save guard.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'

// ---------------------------------------------------------------------------
// vi.hoisted — define shared mock state BEFORE vi.mock() is hoisted
// ---------------------------------------------------------------------------

const mockStore = vi.hoisted(() => ({
  loading: false,
  error: null,
  currentNiche: null,
  fetchNiche: vi.fn(),
  updateNiche: vi.fn(),
  deleteNiche: vi.fn(),
}))

const mockRouteParams = vi.hoisted(() => ({ nicheSlug: 'test-niche' }))

// ---------------------------------------------------------------------------
// Module mocks
// ---------------------------------------------------------------------------

vi.mock('@/stores/niches', () => ({
  useNichesStore: () => mockStore,
}))

vi.mock('vue-router', () => ({
  useRoute: () => ({ params: mockRouteParams }),
  useRouter: () => ({ push: vi.fn() }),
  RouterLink: { template: '<a><slot /></a>' },
}))

import NicheSettingsView from '../NicheSettingsView.vue'

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const baseNiche = {
  slug: 'test-niche',
  name: 'Test Niche',
  description: '',
  icon: '📊',
  color: '#8B5CF6',
  platforms: ['instagram'],
  keywords: ['kw1', 'kw2', 'kw3'],
  countries: ['US'],
  auto_collect_enabled: false,
}

function mountView() {
  return mount(NicheSettingsView, {
    attachTo: document.body,
    global: {
      stubs: {
        RouterLink: { template: '<a><slot /></a>' },
        Teleport: true,
      },
    },
  })
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('NicheSettingsView — keyword counter', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockStore.currentNiche = { ...baseNiche }
    mockStore.fetchNiche.mockImplementation(async () => {
      // The component reads mockStore.currentNiche right after this resolves
    })
  })

  it('pre-populates keywords from the fetched niche (3 keywords → shows 3/5)', async () => {
    const wrapper = mountView()
    // Wait for onMounted + loadNicheData to complete
    await wrapper.vm.$nextTick()
    await wrapper.vm.$nextTick()

    const counter = wrapper.find('.keyword-count')
    expect(counter.text()).toBe('3/5')
  })

  it('counter updates reactively as user types', async () => {
    const wrapper = mountView()
    await wrapper.vm.$nextTick()
    await wrapper.vm.$nextTick()

    const input = wrapper.find('#keywords')
    await input.setValue('kw1, kw2, kw3, kw4, kw5')
    expect(wrapper.find('.keyword-count').text()).toBe('5/5')
  })

  it('shows --over class when count exceeds 5', async () => {
    const wrapper = mountView()
    await wrapper.vm.$nextTick()
    await wrapper.vm.$nextTick()

    await wrapper.find('#keywords').setValue('kw1, kw2, kw3, kw4, kw5, kw6')
    const counter = wrapper.find('.keyword-count')
    expect(counter.text()).toBe('6/5')
    expect(counter.classes()).toContain('keyword-count--over')
  })

  it('save button is disabled when keyword count exceeds 5', async () => {
    const wrapper = mountView()
    await wrapper.vm.$nextTick()
    await wrapper.vm.$nextTick()

    await wrapper.find('#keywords').setValue('kw1, kw2, kw3, kw4, kw5, kw6')
    const btn = wrapper.find('button[type="submit"]')
    expect(btn.element.disabled).toBe(true)
  })

  it('save button is enabled when count is exactly 5', async () => {
    const wrapper = mountView()
    await wrapper.vm.$nextTick()
    await wrapper.vm.$nextTick()

    await wrapper.find('#keywords').setValue('kw1, kw2, kw3, kw4, kw5')
    const btn = wrapper.find('button[type="submit"]')
    expect(btn.element.disabled).toBe(false)
  })

  it('shows warning text when count > 5', async () => {
    const wrapper = mountView()
    await wrapper.vm.$nextTick()
    await wrapper.vm.$nextTick()

    await wrapper.find('#keywords').setValue('kw1, kw2, kw3, kw4, kw5, kw6')
    expect(wrapper.text()).toContain('Only 5 keywords can be used')
  })

  it('niche with 0 existing keywords starts at 0/5', async () => {
    mockStore.currentNiche = { ...baseNiche, keywords: [] }
    const wrapper = mountView()
    await wrapper.vm.$nextTick()
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.keyword-count').text()).toBe('0/5')
  })

  it('counter has --over class for niche pre-loaded with 6 keywords', async () => {
    mockStore.currentNiche = {
      ...baseNiche,
      keywords: ['kw1', 'kw2', 'kw3', 'kw4', 'kw5', 'kw6'],
    }
    const wrapper = mountView()
    await wrapper.vm.$nextTick()
    await wrapper.vm.$nextTick()

    const counter = wrapper.find('.keyword-count')
    expect(counter.text()).toBe('6/5')
    expect(counter.classes()).toContain('keyword-count--over')
  })
})
