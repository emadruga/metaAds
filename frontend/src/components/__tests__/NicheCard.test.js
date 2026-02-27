/**
 * Unit tests for NicheCard.vue — Phase 0 auto-collect toggle.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import NicheCard from '../NicheCard.vue'

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const mockPush = vi.fn()

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: mockPush }),
}))

// toggleAutoCollect mock — default resolves immediately
const mockToggle = vi.fn().mockResolvedValue(undefined)

vi.mock('@/stores/niches', () => ({
  useNichesStore: () => ({ toggleAutoCollect: mockToggle }),
}))

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const makeNiche = (overrides = {}) => ({
  slug: 'test-niche',
  name: 'Test Niche',
  icon: '📊',
  color: '#8B5CF6',
  auto_collect_enabled: false,
  stats: { total_ads: 10, saved_ads: 3 },
  ...overrides,
})

function mountCard(nicheOverrides = {}) {
  return mount(NicheCard, {
    props: { niche: makeNiche(nicheOverrides) },
    global: { plugins: [] },
  })
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('NicheCard', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    mockPush.mockClear()
    mockToggle.mockClear()
  })

  // --- Navigation ---

  it('clicking the card body navigates to /n/<slug>', async () => {
    const wrapper = mountCard()
    await wrapper.find('.niche-card').trigger('click')
    expect(mockPush).toHaveBeenCalledWith('/n/test-niche')
  })

  it('clicking the auto-collect toggle does NOT navigate', async () => {
    const wrapper = mountCard()
    // Click the toggle container (which has @click.stop)
    await wrapper.find('.auto-collect-toggle').trigger('click')
    expect(mockPush).not.toHaveBeenCalled()
  })

  // --- Checkbox state ---

  it('checkbox is unchecked when auto_collect_enabled=false', () => {
    const wrapper = mountCard({ auto_collect_enabled: false })
    const checkbox = wrapper.find('input[type="checkbox"]')
    expect(checkbox.element.checked).toBe(false)
  })

  it('checkbox is checked when auto_collect_enabled=true', () => {
    const wrapper = mountCard({ auto_collect_enabled: true })
    const checkbox = wrapper.find('input[type="checkbox"]')
    expect(checkbox.element.checked).toBe(true)
  })

  it('missing auto_collect_enabled defaults to unchecked', () => {
    const niche = makeNiche()
    delete niche.auto_collect_enabled
    const wrapper = mount(NicheCard, { props: { niche } })
    const checkbox = wrapper.find('input[type="checkbox"]')
    expect(checkbox.element.checked).toBe(false)
  })

  // --- Toggle action ---

  it('checking the checkbox calls toggleAutoCollect with (slug, true)', async () => {
    const wrapper = mountCard({ auto_collect_enabled: false })
    const checkbox = wrapper.find('input[type="checkbox"]')

    // setValue sets checked=true and dispatches the change event properly
    await checkbox.setValue(true)

    expect(mockToggle).toHaveBeenCalledWith('test-niche', true)
  })

  it('checkbox is disabled while toggle API call is in-flight', async () => {
    // Make the toggle return a pending promise so isUpdating stays true
    let resolveToggle
    mockToggle.mockReturnValue(new Promise(r => { resolveToggle = r }))

    const wrapper = mountCard()
    const checkbox = wrapper.find('input[type="checkbox"]')

    // setValue dispatches change event → handleToggle sets isUpdating=true,
    // then suspends on the pending promise. setValue also awaits nextTick
    // so the DOM is updated (disabled=true) before we assert.
    await checkbox.setValue(true)

    expect(checkbox.element.disabled).toBe(true)

    // Resolve and clean up
    resolveToggle()
  })

  // --- Stats display ---

  it('displays total_ads from niche stats', () => {
    const wrapper = mountCard({ stats: { total_ads: 42, saved_ads: 7 } })
    expect(wrapper.text()).toContain('42')
    expect(wrapper.text()).toContain('7')
  })

  it('displays 0 when stats are missing', () => {
    const niche = makeNiche()
    delete niche.stats
    const wrapper = mount(NicheCard, { props: { niche } })
    // Should not throw and should show 0s
    expect(wrapper.find('.stat-value').text()).toBe('0')
  })

  // --- Toggle label ---

  it('renders the "Auto-Collect" label text', () => {
    const wrapper = mountCard()
    expect(wrapper.find('.toggle-label').text()).toBe('Auto-Collect')
  })
})
