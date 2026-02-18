<template>
  <div class="search-filters">
    <!-- Search input -->
    <div class="filter-group">
      <label class="filter-label">Search</label>
      <input
        type="text"
        class="filter-input"
        v-model="localFilters.q"
        placeholder="Search ads..."
        @keyup.enter="applyFilters"
      />
    </div>

    <!-- Status filter -->
    <div class="filter-group">
      <label class="filter-label">Status</label>
      <select v-model="localFilters.is_active" class="filter-select">
        <option value="">All</option>
        <option value="true">Active</option>
        <option value="false">Inactive</option>
      </select>
    </div>

    <!-- Platform filter -->
    <div class="filter-group">
      <label class="filter-label">Platform</label>
      <select v-model="localFilters.platform" class="filter-select">
        <option value="">All platforms</option>
        <option value="facebook">Facebook</option>
        <option value="instagram">Instagram</option>
        <option value="messenger">Messenger</option>
      </select>
    </div>

    <!-- Sort -->
    <div class="filter-group">
      <label class="filter-label">Sort by</label>
      <select v-model="localFilters.sort" class="filter-select">
        <option value="days_active">Days Active</option>
        <option value="start_date">Start Date</option>
        <option value="collected_at">Recently Added</option>
      </select>
    </div>

    <!-- Order -->
    <div class="filter-group">
      <label class="filter-label">Order</label>
      <div class="order-buttons">
        <button
          class="order-btn"
          :class="{ active: localFilters.order === 'desc' }"
          @click="localFilters.order = 'desc'"
        >
          ↓ Desc
        </button>
        <button
          class="order-btn"
          :class="{ active: localFilters.order === 'asc' }"
          @click="localFilters.order = 'asc'"
        >
          ↑ Asc
        </button>
      </div>
    </div>

    <!-- Apply button -->
    <button class="btn btn-primary apply-btn" @click="applyFilters">
      Apply Filters
    </button>

    <!-- Clear filters -->
    <button class="btn btn-ghost clear-btn" @click="clearFilters">
      Clear All
    </button>
  </div>
</template>

<script setup>
  import { reactive, watch } from 'vue'

  const props = defineProps({
    filters: {
      type: Object,
      default: () => ({})
    }
  })

  const emit = defineEmits(['update:filters', 'apply'])

  const localFilters = reactive({
    q: props.filters.q || '',
    is_active: props.filters.is_active || '',
    platform: props.filters.platform || '',
    sort: props.filters.sort || 'days_active',
    order: props.filters.order || 'desc'
  })

  watch(
    () => props.filters,
    (newFilters) => {
      Object.assign(localFilters, newFilters)
    },
    { deep: true }
  )

  function applyFilters() {
    // Keep all filter keys, including empty strings (which means "All")
    // This ensures that changing a filter to "All" actually clears it
    emit('update:filters', { ...localFilters })
    emit('apply', { ...localFilters })
  }

  function clearFilters() {
    localFilters.q = ''
    localFilters.is_active = ''
    localFilters.platform = ''
    localFilters.sort = 'days_active'
    localFilters.order = 'desc'
    applyFilters()
  }
</script>

<style lang="scss" scoped>
  .search-filters {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-4);
  }

  .filter-group {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-1);
  }

  .filter-label {
    font-size: var(--font-size-sm);
    font-weight: 500;
    color: var(--color-text-secondary);
  }

  .filter-input,
  .filter-select {
    padding: var(--spacing-2) var(--spacing-3);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    font-size: var(--font-size-sm);
    background-color: var(--color-bg-primary);
    color: var(--color-text-primary);
    transition: border-color var(--transition-fast);

    &:focus {
      outline: none;
      border-color: var(--color-primary-500);
    }
  }

  .order-buttons {
    display: flex;
    gap: var(--spacing-1);
  }

  .order-btn {
    flex: 1;
    padding: var(--spacing-2);
    border: 1px solid var(--color-border);
    background-color: var(--color-bg-primary);
    border-radius: var(--radius-md);
    font-size: var(--font-size-xs);
    cursor: pointer;
    transition: all var(--transition-fast);

    &:hover {
      background-color: var(--color-gray-100);
    }

    &.active {
      background-color: var(--color-primary-50);
      border-color: var(--color-primary-500);
      color: var(--color-primary-700);
    }
  }

  .apply-btn {
    margin-top: var(--spacing-2);
  }

  .clear-btn {
    font-size: var(--font-size-sm);
  }
</style>
