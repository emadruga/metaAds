/**
 * Unit tests for CreateNicheView.vue — keyword counter and submit guard.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import CreateNicheView from '../CreateNicheView.vue'

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: vi.fn() }),
  RouterLink: { template: '<a><slot /></a>' },
}))

const mockCreateNiche = vi.fn()

vi.mock('@/stores/niches', () => ({
  useNichesStore: () => ({
    loading: false,
    error: null,
    createNiche: mockCreateNiche,
  }),
}))

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function mountView() {
  return mount(CreateNicheView, {
    global: {
      stubs: { RouterLink: { template: '<a><slot /></a>' } },
    },
  })
}

async function setKeywords(wrapper, value) {
  const input = wrapper.find('#keywords')
  await input.setValue(value)
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('CreateNicheView — keyword counter', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    mockCreateNiche.mockClear()
  })

  it('shows 0/5 when keyword input is empty', async () => {
    const wrapper = mountView()
    await setKeywords(wrapper, '')
    expect(wrapper.find('.keyword-count').text()).toBe('0/5')
  })

  it('counts correctly for 3 comma-separated keywords', async () => {
    const wrapper = mountView()
    await setKeywords(wrapper, 'ai video, opus clip, descript')
    expect(wrapper.find('.keyword-count').text()).toBe('3/5')
  })

  it('shows 5/5 (no error) when exactly 5 keywords', async () => {
    const wrapper = mountView()
    await setKeywords(wrapper, 'kw1, kw2, kw3, kw4, kw5')
    const counter = wrapper.find('.keyword-count')
    expect(counter.text()).toBe('5/5')
    expect(counter.classes()).not.toContain('keyword-count--over')
  })

  it('shows 6/5 with --over class when 6 keywords are entered', async () => {
    const wrapper = mountView()
    await setKeywords(wrapper, 'kw1, kw2, kw3, kw4, kw5, kw6')
    const counter = wrapper.find('.keyword-count')
    expect(counter.text()).toBe('6/5')
    expect(counter.classes()).toContain('keyword-count--over')
  })

  it('input gets input--error class when count > 5', async () => {
    const wrapper = mountView()
    await setKeywords(wrapper, 'kw1, kw2, kw3, kw4, kw5, kw6')
    expect(wrapper.find('#keywords').classes()).toContain('input--error')
  })

  it('input does NOT have input--error class when count <= 5', async () => {
    const wrapper = mountView()
    await setKeywords(wrapper, 'kw1, kw2, kw3')
    expect(wrapper.find('#keywords').classes()).not.toContain('input--error')
  })

  it('submit button is disabled when count > 5', async () => {
    const wrapper = mountView()
    await setKeywords(wrapper, 'kw1, kw2, kw3, kw4, kw5, kw6')
    const btn = wrapper.find('button[type="submit"]')
    expect(btn.element.disabled).toBe(true)
  })

  it('submit button is enabled when count is exactly 5', async () => {
    const wrapper = mountView()
    await setKeywords(wrapper, 'kw1, kw2, kw3, kw4, kw5')
    const btn = wrapper.find('button[type="submit"]')
    expect(btn.element.disabled).toBe(false)
  })

  it('submit button is enabled when count is 0 (no keywords)', async () => {
    const wrapper = mountView()
    await setKeywords(wrapper, '')
    const btn = wrapper.find('button[type="submit"]')
    expect(btn.element.disabled).toBe(false)
  })

  it('shows warning text when count exceeds 5', async () => {
    const wrapper = mountView()
    await setKeywords(wrapper, 'kw1, kw2, kw3, kw4, kw5, kw6')
    expect(wrapper.text()).toContain('Only 5 keywords can be used')
  })

  it('shows normal hint when count is within limit', async () => {
    const wrapper = mountView()
    await setKeywords(wrapper, 'kw1, kw2')
    expect(wrapper.text()).toContain('Max 5 keywords per niche')
  })

  it('ignores blank entries when counting (trailing comma)', async () => {
    const wrapper = mountView()
    // "kw1," → split gives ["kw1", ""] → filter removes "" → count 1
    await setKeywords(wrapper, 'kw1,')
    expect(wrapper.find('.keyword-count').text()).toBe('1/5')
  })

  it('trims whitespace when counting keywords', async () => {
    const wrapper = mountView()
    await setKeywords(wrapper, '  kw1  ,  kw2  ')
    expect(wrapper.find('.keyword-count').text()).toBe('2/5')
  })
})
