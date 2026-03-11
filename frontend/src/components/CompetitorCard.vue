<template>
  <div class="competitor-card" @click="$emit('click', competitor)">
    <div class="card-header">
      <div class="page-info">
        <h3 class="page-name">{{ competitor.page_name }}</h3>
        <span class="page-id">ID: {{ competitor.page_id }}</span>
      </div>
      <button
        class="remove-btn"
        title="Remove competitor"
        @click.stop="$emit('remove', competitor)"
      >
        ✕
      </button>
    </div>

    <div class="card-meta">
      <span class="meta-item">
        📅 Added {{ formatDate(competitor.added_at) }}
      </span>
    </div>

    <div v-if="competitor.notes" class="card-notes">
      {{ competitor.notes }}
    </div>

    <div class="card-footer">
      <span class="view-link">View ads →</span>
    </div>
  </div>
</template>

<script setup>
  defineProps({
    competitor: {
      type: Object,
      required: true,
    },
  })

  defineEmits(['click', 'remove'])

  function formatDate(dateStr) {
    if (!dateStr) return 'Unknown'
    try {
      return new Date(dateStr).toLocaleDateString()
    } catch {
      return dateStr
    }
  }
</script>

<style lang="scss" scoped>
  .competitor-card {
    background-color: var(--color-bg-primary);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-xl);
    padding: var(--spacing-5);
    cursor: pointer;
    transition: all var(--transition-base);
    display: flex;
    flex-direction: column;
    gap: var(--spacing-3);

    &:hover {
      border-color: var(--color-primary-300);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
      transform: translateY(-1px);
    }
  }

  .card-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: var(--spacing-2);
  }

  .page-info {
    flex: 1;
    min-width: 0;
  }

  .page-name {
    font-size: var(--font-size-lg);
    font-weight: 600;
    color: var(--color-gray-900);
    margin: 0 0 var(--spacing-1) 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .page-id {
    font-size: var(--font-size-xs);
    color: var(--color-text-muted);
    font-family: monospace;
  }

  .remove-btn {
    flex-shrink: 0;
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    background: transparent;
    color: var(--color-text-muted);
    cursor: pointer;
    font-size: var(--font-size-xs);
    transition: all var(--transition-fast);

    &:hover {
      background-color: var(--color-error, #dc2626);
      border-color: var(--color-error, #dc2626);
      color: white;
    }
  }

  .card-meta {
    display: flex;
    flex-wrap: wrap;
    gap: var(--spacing-2);
  }

  .meta-item {
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
  }

  .card-notes {
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
    line-height: 1.4;
    background-color: var(--color-gray-50);
    border-radius: var(--radius-md);
    padding: var(--spacing-2) var(--spacing-3);
  }

  .card-footer {
    display: flex;
    align-items: center;
    justify-content: flex-end;
  }

  .view-link {
    font-size: var(--font-size-sm);
    font-weight: 500;
    color: var(--color-primary-600);
  }
</style>
