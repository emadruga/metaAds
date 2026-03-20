<template>
  <div class="modal-overlay" @click.self="$emit('cancel')">
    <div class="modal-dialog confirm-competitor-modal">

      <div class="modal-header">
        <h3>Confirm Competitor</h3>
        <button class="close-btn" @click="$emit('cancel')">&times;</button>
      </div>

      <div class="modal-body">
        <p class="modal-hint">
          We found the following page in Meta Ad Library. Is this the competitor you want to track?
        </p>

        <!-- Candidate card -->
        <div class="candidate-card">
          <div class="candidate-name">{{ current.page_name }}</div>
          <div class="candidate-meta">
            <span class="meta-item" v-if="current.category">{{ current.category }}</span>
            <span class="meta-item" v-if="current.fan_count">
              {{ formatFollowers(current.fan_count) }} FB followers
            </span>
            <span class="meta-item page-id">ID: {{ current.page_id }}</span>
          </div>
          <div v-if="current.about" class="candidate-about">{{ current.about }}</div>
        </div>

        <!-- Pagination hint when multiple candidates -->
        <p v-if="candidates.length > 1" class="candidate-nav-hint">
          Result {{ currentIndex + 1 }} of {{ candidates.length }}
        </p>
      </div>

      <div class="modal-actions">
        <button class="btn btn-ghost" @click="$emit('cancel')">Cancel</button>
        <button
          v-if="candidates.length > 1 && currentIndex < candidates.length - 1"
          class="btn btn-ghost"
          @click="currentIndex++"
        >
          Not this one →
        </button>
        <button
          class="btn btn-primary"
          :disabled="adding"
          @click="confirmAdd"
        >
          {{ adding ? 'Adding...' : 'Yes, add this competitor' }}
        </button>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  candidates: { type: Array, required: true },
  adding:     { type: Boolean, default: false },
})

const emit = defineEmits(['confirm', 'cancel'])

const currentIndex = ref(0)
const current = computed(() => props.candidates[currentIndex.value])

function formatFollowers(n) {
  if (!n) return ''
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M'
  if (n >= 1_000)     return (n / 1_000).toFixed(1) + 'K'
  return String(n)
}

function confirmAdd() {
  emit('confirm', current.value)
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.confirm-competitor-modal {
  background: var(--color-surface, #1e1e2e);
  border: 1px solid var(--color-border, #333);
  border-radius: 12px;
  width: 480px;
  max-width: 95vw;
  padding: 0;
  overflow: hidden;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px 16px;
  border-bottom: 1px solid var(--color-border, #333);
}

.modal-header h3 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--color-text, #fff);
}

.close-btn {
  background: none;
  border: none;
  color: var(--color-text-muted, #aaa);
  font-size: 1.4rem;
  cursor: pointer;
  line-height: 1;
  padding: 0 4px;
}

.close-btn:hover { color: var(--color-text, #fff); }

.modal-body {
  padding: 20px 24px;
}

.modal-hint {
  margin: 0 0 16px;
  color: var(--color-text-muted, #aaa);
  font-size: 0.9rem;
}

.candidate-card {
  background: var(--color-surface-alt, #2a2a3e);
  border: 1px solid var(--color-border, #333);
  border-radius: 8px;
  padding: 16px;
}

.candidate-name {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--color-text, #fff);
  margin-bottom: 8px;
}

.candidate-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 8px;
}

.meta-item {
  font-size: 0.8rem;
  color: var(--color-text-muted, #aaa);
  background: var(--color-surface, #1e1e2e);
  border-radius: 4px;
  padding: 2px 8px;
}

.page-id {
  font-family: monospace;
  font-size: 0.75rem;
}

.candidate-about {
  font-size: 0.85rem;
  color: var(--color-text-muted, #aaa);
  line-height: 1.4;
  margin-top: 8px;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.candidate-nav-hint {
  margin: 12px 0 0;
  font-size: 0.8rem;
  color: var(--color-text-muted, #aaa);
  text-align: right;
}

.modal-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  padding: 16px 24px 20px;
  border-top: 1px solid var(--color-border, #333);
}
</style>
