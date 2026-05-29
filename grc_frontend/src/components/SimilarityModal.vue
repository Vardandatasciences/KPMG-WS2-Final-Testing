<template>
  <Teleport to="body">
    <div v-if="visible" class="sim-overlay" @click.self="onCancel">
      <div class="sim-dialog" role="dialog" aria-labelledby="sim-dialog-title">
        <!-- Header -->
        <header class="sim-header">
          <div class="sim-header-main">
            <div class="sim-header-icon" aria-hidden="true">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="11" cy="11" r="7" />
                <path d="M20 20l-3.5-3.5" />
              </svg>
            </div>
            <div>
              <h2 id="sim-dialog-title" class="sim-title">{{ headerTitle }}</h2>
              <p v-if="candidates.length" class="sim-subtitle">
                {{ candidates.length }} similar {{ candidates.length === 1 ? 'record' : 'records' }} in your library
              </p>
            </div>
          </div>
          <span class="sim-risk" :class="riskClass">{{ riskLevel }}</span>
          <button type="button" class="sim-close" aria-label="Close" @click="onCancel">&times;</button>
        </header>

        <!-- Advice -->
        <section v-if="analysis.overall_advice" class="sim-advice">
          <p>{{ analysis.overall_advice }}</p>
          <span v-if="analysis.confidence != null" class="sim-confidence">
            Confidence {{ (analysis.confidence * 100).toFixed(0) }}%
          </span>
        </section>

        <!-- Candidates -->
        <section class="sim-body">
          <p v-if="!candidates.length" class="sim-empty">No similar records were found. You can continue safely.</p>

          <article
            v-for="candidate in candidates"
            :key="candidate.id"
            class="sim-card"
            :class="{ 'sim-card--selected': selectedCandidate?.id === candidate.id }"
            tabindex="0"
            @click="selectCandidate(candidate)"
            @keydown.enter.prevent="selectCandidate(candidate)"
          >
            <div class="sim-card-top">
              <div class="sim-card-title-row">
                <span v-if="entityTypeLabel(candidate)" class="sim-entity">{{ entityTypeLabel(candidate) }}</span>
                <h3 class="sim-card-name">{{ candidate.name }}</h3>
              </div>
              <span
                class="sim-select-dot"
                :class="{ 'sim-select-dot--on': selectedCandidate?.id === candidate.id }"
                aria-hidden="true"
              />
            </div>

            <div class="sim-meta">
              <span class="sim-chip">Match {{ formatScore(candidate.chroma_score) }}</span>
              <span class="sim-chip sim-chip--muted">Rank {{ formatScore(candidate.reranker_score) }}</span>
              <span class="sim-status" :class="statusClass(candidate.final_status)">
                {{ formatStatus(candidate.final_status) }}
              </span>
            </div>

            <p v-if="candidate.reason" class="sim-reason">{{ candidate.reason }}</p>

            <div
              v-if="candidate.same_points?.length || candidate.different_points?.length"
              class="sim-compare"
            >
              <div v-if="candidate.same_points?.length" class="sim-compare-col">
                <span class="sim-compare-label sim-compare-label--same">Similar</span>
                <ul>
                  <li v-for="point in candidate.same_points" :key="'s-' + point">{{ point }}</li>
                </ul>
              </div>
              <div v-if="candidate.different_points?.length" class="sim-compare-col">
                <span class="sim-compare-label sim-compare-label--diff">Different</span>
                <ul>
                  <li v-for="point in candidate.different_points" :key="'d-' + point">{{ point }}</li>
                </ul>
              </div>
            </div>

            <a
              v-if="candidate.view_url && candidate.view_url !== '#'"
              :href="candidate.view_url"
              target="_blank"
              rel="noopener noreferrer"
              class="sim-link"
              @click.stop
            >
              Open record
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6M15 3h6v6M10 14L21 3" />
              </svg>
            </a>
          </article>
        </section>

        <!-- Footer -->
        <footer class="sim-footer">
          <p v-if="selectedCandidate" class="sim-footer-hint">
            Selected: <strong>{{ selectedCandidate.name }}</strong>
          </p>
          <div class="sim-actions">
            <button type="button" class="sim-btn sim-btn--ghost" :disabled="loading" @click="onCancel">
              Cancel
            </button>
            <button
              v-if="canUseExisting"
              type="button"
              class="sim-btn sim-btn--primary"
              :disabled="loading || !selectedCandidate"
              @click="onUseExisting"
            >
              {{ loading ? 'Processing…' : 'Use existing' }}
            </button>
            <button
              v-if="canCreate"
              type="button"
              class="sim-btn sim-btn--secondary"
              :disabled="loading"
              @click="onCreateAnyway"
            >
              {{ loading ? 'Processing…' : 'Create anyway' }}
            </button>
          </div>
        </footer>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import { formatScore } from '@/services/similarityService';

const props = defineProps({
  visible: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
  checkId: { type: Number, default: null },
  newRecord: { type: Object, default: () => ({}) },
  analysis: { type: Object, default: () => ({}) },
  candidates: { type: Array, default: () => [] },
  suggestedAction: { type: String, default: 'ALLOW' },
  /** Item type being created (Framework, Policy, etc.) — used when candidate has no type */
  checkingItemType: { type: String, default: '' }
});

const emit = defineEmits(['create-anyway', 'use-existing', 'cancel', 'merge']);

const selectedCandidate = ref(null);

watch(
  () => props.candidates,
  (list) => {
    selectedCandidate.value = list?.length ? list[0] : null;
  },
  { immediate: true }
);

watch(
  () => props.visible,
  (v) => {
    if (v && props.candidates?.length) {
      selectedCandidate.value = props.candidates[0];
    }
  }
);

const riskLevel = computed(() => (props.analysis.risk_level || 'UNKNOWN').toUpperCase());

const riskClass = computed(() => {
  const map = { LOW: 'sim-risk--low', MEDIUM: 'sim-risk--medium', HIGH: 'sim-risk--high' };
  return map[riskLevel.value] || 'sim-risk--unknown';
});

const checkingTypeLabel = computed(() => {
  const raw = (props.checkingItemType || '').trim();
  if (!raw) return '';
  return raw.replace(/_/g, ' ');
});

const headerTitle = computed(() => {
  const typePrefix = checkingTypeLabel.value ? `${checkingTypeLabel.value}: ` : '';
  if (!props.candidates.length) {
    return typePrefix ? `${typePrefix}no similar records` : 'No similar records';
  }
  if (riskLevel.value === 'HIGH') return `${typePrefix}possible duplicate`.trim();
  if (riskLevel.value === 'MEDIUM') return `${typePrefix}similar records found`.trim();
  return typePrefix ? `${typePrefix}review before continuing` : 'Review before continuing';
});

const canCreate = computed(() => props.suggestedAction !== 'BLOCK');
const canUseExisting = computed(() => props.candidates.length > 0);

function entityTypeLabel(candidate) {
  const raw =
    candidate.record_type
    || candidate.entity_type
    || props.checkingItemType
    || '';
  const normalized = String(raw).trim().toLowerCase();
  if (!normalized || normalized === 'unknown' || normalized === 'record') {
    return null;
  }
  const s = String(raw).replace(/_/g, ' ');
  return s.charAt(0).toUpperCase() + s.slice(1).toLowerCase();
}

function formatStatus(status) {
  if (!status) return 'Unknown';
  return String(status).replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

function statusClass(status) {
  const key = (status || 'unknown').toLowerCase().replace(/_/g, '-');
  return `sim-status--${key}`;
}

function selectCandidate(candidate) {
  selectedCandidate.value = candidate;
}

function onCreateAnyway() {
  emit('create-anyway');
}

function onUseExisting() {
  if (selectedCandidate.value) {
    emit('use-existing', selectedCandidate.value);
  }
}

function onCancel() {
  selectedCandidate.value = null;
  emit('cancel');
}
</script>

<style scoped>
.sim-overlay {
  position: fixed;
  inset: 0;
  z-index: 10001;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: rgba(15, 23, 42, 0.45);
  backdrop-filter: blur(4px);
}

.sim-dialog {
  display: flex;
  flex-direction: column;
  width: 100%;
  max-width: 520px;
  max-height: min(88vh, 720px);
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 24px 48px rgba(15, 23, 42, 0.18);
  overflow: hidden;
}

/* Header */
.sim-header {
  display: grid;
  grid-template-columns: 1fr auto auto;
  align-items: start;
  gap: 12px;
  padding: 20px 20px 16px;
  border-bottom: 1px solid #f1f5f9;
}

.sim-header-main {
  display: flex;
  gap: 12px;
  min-width: 0;
}

.sim-header-icon {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  background: #eff6ff;
  color: #2563eb;
}

.sim-title {
  margin: 0;
  font-size: 1.125rem;
  font-weight: 600;
  color: #0f172a;
  line-height: 1.3;
}

.sim-subtitle {
  margin: 4px 0 0;
  font-size: 0.8125rem;
  color: #64748b;
}

.sim-risk {
  align-self: center;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.sim-risk--low {
  background: #ecfdf5;
  color: #047857;
}

.sim-risk--medium {
  background: #fff7ed;
  color: #c2410c;
}

.sim-risk--high {
  background: #fef2f2;
  color: #b91c1c;
}

.sim-risk--unknown {
  background: #f1f5f9;
  color: #475569;
}

.sim-close {
  background: none;
  border: none;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  font-size: 1.5rem;
  line-height: 1;
  color: #94a3b8;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.sim-close:hover {
  background: #f1f5f9;
  color: #334155;
}

/* Advice */
.sim-advice {
  padding: 12px 20px;
  background: #f8fafc;
  border-bottom: 1px solid #f1f5f9;
}

.sim-advice p {
  margin: 0;
  font-size: 0.875rem;
  line-height: 1.5;
  color: #475569;
}

.sim-confidence {
  display: inline-block;
  margin-top: 6px;
  font-size: 0.75rem;
  color: #94a3b8;
}

/* Body */
.sim-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
}

.sim-empty {
  margin: 0;
  font-size: 0.875rem;
  color: #64748b;
  text-align: center;
  padding: 24px 0;
}

/* Card */
.sim-card {
  padding: 14px 16px;
  margin-bottom: 10px;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  cursor: pointer;
  transition: border-color 0.15s, box-shadow 0.15s, background 0.15s;
}

.sim-card:last-child {
  margin-bottom: 0;
}

.sim-card:hover {
  border-color: #93c5fd;
  background: #fafbff;
}

.sim-card--selected {
  border-color: #2563eb;
  background: #f8fafc;
  box-shadow: 0 0 0 1px #2563eb;
}

.sim-card-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.sim-card-title-row {
  min-width: 0;
}

.sim-entity {
  display: inline-block;
  margin-bottom: 4px;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: 0.03em;
  text-transform: uppercase;
  background: #f1f5f9;
  color: #475569;
}

.sim-card-name {
  margin: 0;
  font-size: 0.9375rem;
  font-weight: 600;
  color: #0f172a;
  line-height: 1.35;
  word-break: break-word;
}

.sim-select-dot {
  flex-shrink: 0;
  width: 18px;
  height: 18px;
  margin-top: 2px;
  border: 2px solid #cbd5e1;
  border-radius: 50%;
  transition: border-color 0.15s, background 0.15s;
}

.sim-select-dot--on {
  border-color: #2563eb;
  background: #2563eb;
  box-shadow: inset 0 0 0 3px #fff;
}

.sim-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin-top: 10px;
}

.sim-chip {
  font-size: 0.75rem;
  font-weight: 500;
  padding: 3px 8px;
  border-radius: 6px;
  background: #f1f5f9;
  color: #334155;
}

.sim-chip--muted {
  background: transparent;
  color: #64748b;
  border: 1px solid #e2e8f0;
}

.sim-status {
  font-size: 0.6875rem;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 6px;
  margin-left: auto;
}

.sim-status--duplicate {
  background: #fef2f2;
  color: #b91c1c;
}

.sim-status--highly-similar {
  background: #fff7ed;
  color: #c2410c;
}

.sim-status--related-but-different {
  background: #eff6ff;
  color: #1d4ed8;
}

.sim-status--different {
  background: #ecfdf5;
  color: #047857;
}

.sim-status--unknown {
  background: #f1f5f9;
  color: #64748b;
}

.sim-reason {
  margin: 10px 0 0;
  font-size: 0.8125rem;
  line-height: 1.5;
  color: #64748b;
}

.sim-compare {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #f1f5f9;
}

.sim-compare-label {
  display: block;
  font-size: 0.6875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-bottom: 6px;
}

.sim-compare-label--same {
  color: #047857;
}

.sim-compare-label--diff {
  color: #b45309;
}

.sim-compare ul {
  margin: 0;
  padding: 0;
  list-style: none;
}

.sim-compare li {
  position: relative;
  padding-left: 12px;
  font-size: 0.75rem;
  line-height: 1.45;
  color: #475569;
  margin-bottom: 4px;
}

.sim-compare li::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0.45em;
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: currentColor;
  opacity: 0.5;
}

.sim-compare-label--same + ul li::before {
  background: #10b981;
}

.sim-compare-label--diff + ul li::before {
  background: #f59e0b;
}

.sim-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-top: 10px;
  font-size: 0.8125rem;
  font-weight: 500;
  color: #2563eb;
  text-decoration: none;
}

.sim-link:hover {
  text-decoration: underline;
}

/* Footer */
.sim-footer {
  padding: 14px 20px 18px;
  border-top: 1px solid #f1f5f9;
  background: #fafbfc;
}

.sim-footer-hint {
  margin: 0 0 12px;
  font-size: 0.8125rem;
  color: #64748b;
}

.sim-footer-hint strong {
  color: #0f172a;
}

.sim-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}

.sim-btn {
  padding: 9px 16px;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
}

.sim-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.sim-btn--ghost {
  background: transparent;
  color: #64748b;
  border: 1px solid #e2e8f0;
}

.sim-btn--ghost:hover:not(:disabled) {
  background: #fff;
  color: #334155;
}

.sim-btn--primary {
  background: #2563eb;
  color: #fff;
}

.sim-btn--primary:hover:not(:disabled) {
  background: #1d4ed8;
}

.sim-btn--secondary {
  background: #fff;
  color: #334155;
  border: 1px solid #cbd5e1;
}

.sim-btn--secondary:hover:not(:disabled) {
  background: #f8fafc;
  border-color: #94a3b8;
}

@media (max-width: 520px) {
  .sim-overlay {
    padding: 0;
    align-items: flex-end;
  }

  .sim-dialog {
    max-width: 100%;
    max-height: 92vh;
    border-radius: 16px 16px 0 0;
  }

  .sim-compare {
    grid-template-columns: 1fr;
  }

  .sim-actions {
    flex-direction: column-reverse;
  }

  .sim-btn {
    width: 100%;
    justify-content: center;
  }
}
</style>
