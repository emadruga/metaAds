<template>
  <div class="ad-table-container">
    <!-- Loading state -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Loading ads...</p>
    </div>

    <!-- Empty state -->
    <div v-else-if="ads.length === 0" class="empty-state">
      <div class="empty-icon">📭</div>
      <h3>No ads found</h3>
      <p>{{ emptyMessage }}</p>
      <button v-if="showCollectButton" class="btn btn-primary collect-cta" @click="$emit('collect')">
        📥 Collect Ads Now
      </button>
    </div>

    <!-- Ad table -->
    <div v-else class="table-wrapper">
      <table class="ad-table">
        <thead>
          <tr>
            <th class="col-expand"></th>
            <th class="col-title">Ad Title</th>
            <th class="col-body">Body Text</th>
            <th class="col-days">Days Active</th>
            <th class="col-status">Status</th>
            <th class="col-actions"></th>
          </tr>
        </thead>
        <tbody>
          <template v-for="group in groupedAds" :key="group.key">
            <!-- Group header row (first ad in group) -->
            <tr
              class="group-row"
              :class="{
                selected: selectedAdId === group.ads[0].id,
                'has-children': group.ads.length > 1
              }"
              @click="handleRowClick(group.ads[0], $event)"
            >
              <td class="col-expand">
                <button
                  v-if="group.ads.length > 1"
                  class="expand-btn"
                  @click.stop="toggleGroup(group.key)"
                  :title="isGroupExpanded(group.key) ? 'Collapse group' : 'Expand group'"
                >
                  {{ isGroupExpanded(group.key) ? '−' : '+' }}
                  <span class="count">{{ group.ads.length }}</span>
                </button>
              </td>
              <td class="col-title">
                <div class="title-cell">
                  <span class="page-name">{{ group.pageName }}</span>
                  <span v-if="group.headline" class="headline">{{ group.headline }}</span>
                </div>
              </td>
              <td class="col-body">
                <div class="body-preview">
                  {{ truncateText(group.ads[0].body, 100) }}
                </div>
              </td>
              <td class="col-days">
                <span class="days-badge">{{ group.ads[0].days_active || 0 }}</span>
              </td>
              <td class="col-status">
                <span class="status-badge" :class="group.ads[0].is_active ? 'active' : 'inactive'">
                  {{ group.ads[0].is_active ? 'Active' : 'Inactive' }}
                </span>
              </td>
              <td class="col-actions">
                <button
                  class="save-btn"
                  :class="{ saved: group.ads[0].is_saved }"
                  @click.stop="$emit('toggle-save', group.ads[0])"
                  :title="group.ads[0].is_saved ? 'Unsave' : 'Save'"
                >
                  {{ group.ads[0].is_saved ? '★' : '☆' }}
                </button>
              </td>
            </tr>

            <!-- Expanded child rows (other ads in group) -->
            <template v-if="isGroupExpanded(group.key) && group.ads.length > 1">
              <tr
                v-for="(ad, index) in group.ads.slice(1)"
                :key="ad.id"
                class="child-row"
                :class="{ selected: selectedAdId === ad.id }"
                @click="handleRowClick(ad, $event)"
              >
                <td class="col-expand">
                  <span class="child-indicator">└</span>
                </td>
                <td class="col-title">
                  <div class="title-cell child">
                    <span class="variant-label">Variant {{ index + 2 }}</span>
                  </div>
                </td>
                <td class="col-body">
                  <div class="body-preview">
                    {{ truncateText(ad.body, 100) }}
                  </div>
                </td>
                <td class="col-days">
                  <span class="days-badge">{{ ad.days_active || 0 }}</span>
                </td>
                <td class="col-status">
                  <span class="status-badge" :class="ad.is_active ? 'active' : 'inactive'">
                    {{ ad.is_active ? 'Active' : 'Inactive' }}
                  </span>
                </td>
                <td class="col-actions">
                  <button
                    class="save-btn"
                    :class="{ saved: ad.is_saved }"
                    @click.stop="$emit('toggle-save', ad)"
                    :title="ad.is_saved ? 'Unsave' : 'Save'"
                  >
                    {{ ad.is_saved ? '★' : '☆' }}
                  </button>
                </td>
              </tr>
            </template>
          </template>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div v-if="pagination && pagination.pages > 1" class="pagination">
      <button
        class="btn btn-ghost btn-icon"
        :disabled="pagination.page === 1"
        @click="$emit('page-change', 1)"
        title="First page"
      >
        ⇤
      </button>
      <button
        class="btn btn-ghost"
        :disabled="!pagination.has_prev"
        @click="$emit('page-change', pagination.page - 1)"
      >
        ← Previous
      </button>
      <span class="page-info">
        Page {{ pagination.page }} of {{ pagination.pages }}
      </span>
      <button
        class="btn btn-ghost"
        :disabled="!pagination.has_next"
        @click="$emit('page-change', pagination.page + 1)"
      >
        Next →
      </button>
      <button
        class="btn btn-ghost btn-icon"
        :disabled="pagination.page === pagination.pages"
        @click="$emit('page-change', pagination.pages)"
        title="Last page"
      >
        ⇥
      </button>
    </div>
  </div>
</template>

<script setup>
  import { ref, computed } from 'vue'

  const props = defineProps({
    ads: {
      type: Array,
      default: () => []
    },
    loading: {
      type: Boolean,
      default: false
    },
    selectedAdId: {
      type: String,
      default: null
    },
    pagination: {
      type: Object,
      default: null
    },
    emptyMessage: {
      type: String,
      default: 'Try adjusting your search filters.'
    },
    showCollectButton: {
      type: Boolean,
      default: false
    },
    sortBy: {
      type: String,
      default: 'variants' // 'variants', 'days_active', 'start_date'
    },
    sortOrder: {
      type: String,
      default: 'desc' // 'asc' or 'desc'
    }
  })

  const emit = defineEmits(['select', 'toggle-save', 'page-change', 'collect'])

  const expandedGroups = ref(new Set())

  // Group ads by title (page_name + headline)
  const groupedAds = computed(() => {
    const groups = {}

    props.ads.forEach(ad => {
      const groupKey = `${ad.page_name}|${ad.headline || ''}`

      if (!groups[groupKey]) {
        groups[groupKey] = {
          key: groupKey,
          pageName: ad.page_name,
          headline: ad.headline,
          ads: []
        }
      }

      groups[groupKey].ads.push(ad)
    })

    // Convert to array
    const groupsArray = Object.values(groups)

    // Sort based on sortBy and sortOrder
    return groupsArray.sort((a, b) => {
      let compareValue = 0

      switch (props.sortBy) {
        case 'variants':
          compareValue = b.ads.length - a.ads.length
          break
        case 'days_active':
          compareValue = (b.ads[0].days_active || 0) - (a.ads[0].days_active || 0)
          break
        case 'start_date':
          const dateA = new Date(a.ads[0].start_date || 0)
          const dateB = new Date(b.ads[0].start_date || 0)
          compareValue = dateB - dateA
          break
        case 'collected_at':
          const collectedA = new Date(a.ads[0].collected_at || 0)
          const collectedB = new Date(b.ads[0].collected_at || 0)
          compareValue = collectedB - collectedA
          break
        default:
          compareValue = b.ads.length - a.ads.length
      }

      // Reverse if ascending order
      return props.sortOrder === 'asc' ? -compareValue : compareValue
    })
  })

  function toggleGroup(groupKey) {
    if (expandedGroups.value.has(groupKey)) {
      expandedGroups.value.delete(groupKey)
    } else {
      expandedGroups.value.add(groupKey)
    }
  }

  function isGroupExpanded(groupKey) {
    return expandedGroups.value.has(groupKey)
  }

  function truncateText(text, maxLength) {
    if (!text) return 'No body text'
    if (text.length <= maxLength) return text
    return text.slice(0, maxLength) + '...'
  }

  function handleRowClick(ad, event) {
    // Don't select if clicking on action buttons
    if (event.target.closest('.save-btn')) return
    emit('select', ad)
  }
</script>

<style lang="scss" scoped>
  .ad-table-container {
    height: 100%;
    display: flex;
    flex-direction: column;
  }

  .loading-state,
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: var(--spacing-8);
    text-align: center;
    color: var(--color-text-secondary);
  }

  .spinner {
    width: 40px;
    height: 40px;
    border: 3px solid var(--color-gray-200);
    border-top-color: var(--color-primary-500);
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-bottom: var(--spacing-3);
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  .empty-icon {
    font-size: 3rem;
    margin-bottom: var(--spacing-3);
  }

  .empty-state h3 {
    margin: 0 0 var(--spacing-2) 0;
    color: var(--color-text-primary);
  }

  .empty-state p {
    margin: 0;
    font-size: var(--font-size-sm);
  }

  .collect-cta {
    margin-top: var(--spacing-4);
  }

  .table-wrapper {
    flex: 1;
    overflow-y: auto;
    overflow-x: auto;
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
  }

  .ad-table {
    width: 100%;
    border-collapse: collapse;
    font-size: var(--font-size-sm);

    thead {
      position: sticky;
      top: 0;
      background-color: var(--color-bg-secondary);
      z-index: 1;
      border-bottom: 2px solid var(--color-border);

      th {
        padding: var(--spacing-3) var(--spacing-4);
        text-align: left;
        font-weight: 600;
        color: var(--color-text-secondary);
        font-size: var(--font-size-xs);
        text-transform: uppercase;
        letter-spacing: 0.5px;
      }
    }

    tbody {
      tr {
        border-bottom: 1px solid var(--color-border);
        cursor: pointer;
        transition: background-color var(--transition-fast);

        &:hover {
          background-color: var(--color-gray-50);
        }

        &.selected {
          background-color: var(--color-primary-50);
        }

        td {
          padding: var(--spacing-3) var(--spacing-4);
          vertical-align: top;
        }
      }
    }
  }

  .col-expand {
    width: 60px;
    min-width: 60px;
    text-align: center;
  }

  .col-title {
    width: 25%;
    min-width: 200px;
  }

  .col-body {
    width: 35%;
    min-width: 300px;
  }

  .col-days {
    width: 10%;
    min-width: 100px;
    text-align: center;
  }

  .col-status {
    width: 10%;
    min-width: 100px;
    text-align: center;
  }

  .col-actions {
    width: 5%;
    min-width: 60px;
    text-align: center;
  }

  .expand-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: var(--spacing-1);
    padding: var(--spacing-1) var(--spacing-2);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    background-color: var(--color-bg-primary);
    color: var(--color-text-secondary);
    font-size: var(--font-size-sm);
    font-weight: 600;
    cursor: pointer;
    transition: all var(--transition-fast);
    margin: 0 auto;

    &:hover {
      background-color: var(--color-primary-50);
      border-color: var(--color-primary-500);
      color: var(--color-primary-600);
    }

    .count {
      font-size: var(--font-size-xs);
      padding: 1px 4px;
      background-color: var(--color-primary-100);
      border-radius: var(--radius-full);
      min-width: 16px;
      text-align: center;
    }
  }

  .child-indicator {
    color: var(--color-text-secondary);
    font-size: var(--font-size-sm);
  }

  .group-row {
    &.has-children {
      font-weight: 500;
    }
  }

  .child-row {
    background-color: var(--color-gray-50);

    &:hover {
      background-color: var(--color-gray-100);
    }

    &.selected {
      background-color: var(--color-primary-50);
    }
  }

  .title-cell {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-1);

    .page-name {
      font-weight: 600;
      color: var(--color-text-primary);
    }

    .headline {
      font-size: var(--font-size-xs);
      color: var(--color-text-secondary);
    }

    &.child {
      padding-left: var(--spacing-2);
    }

    .variant-label {
      font-size: var(--font-size-xs);
      color: var(--color-text-secondary);
      font-style: italic;
    }
  }

  .body-preview {
    color: var(--color-text-secondary);
    line-height: 1.5;
  }

  .days-badge {
    display: inline-block;
    padding: var(--spacing-1) var(--spacing-2);
    background-color: var(--color-gray-100);
    border-radius: var(--radius-full);
    font-weight: 500;
    font-size: var(--font-size-xs);
  }

  .status-badge {
    display: inline-block;
    padding: var(--spacing-1) var(--spacing-2);
    border-radius: var(--radius-full);
    font-weight: 500;
    font-size: var(--font-size-xs);

    &.active {
      background-color: var(--color-success-100);
      color: var(--color-success-700);
    }

    &.inactive {
      background-color: var(--color-gray-100);
      color: var(--color-gray-700);
    }
  }

  .save-btn {
    padding: var(--spacing-1) var(--spacing-2);
    border: none;
    background: none;
    font-size: var(--font-size-lg);
    cursor: pointer;
    color: var(--color-gray-400);
    transition: all var(--transition-fast);

    &:hover {
      color: var(--color-warning-500);
      transform: scale(1.2);
    }

    &.saved {
      color: var(--color-warning-500);
    }
  }

  .pagination {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: var(--spacing-4);
    padding-top: var(--spacing-4);
    border-top: 1px solid var(--color-border);
    margin-top: var(--spacing-4);
  }

  .page-info {
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
  }
</style>
