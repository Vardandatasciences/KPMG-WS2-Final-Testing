<template>
  <div class="similarity-submit-gate">
    <Teleport to="body">
      <div v-if="checking" class="similarity-checking-overlay">
        <div class="similarity-checking-box">
          <span class="similarity-checking-spinner" />
          <p class="similarity-checking-title">{{ progressLabel || 'Checking for similar records…' }}</p>
          <p class="similarity-checking-sub">
            This step can take 1–2 minutes while similar records are ranked and reviewed.
            Use <strong>Back to form</strong> to stop and return without saving.
          </p>
          <div class="similarity-checking-actions">
            <button type="button" class="btn btn-outline btn-sm" @click="onCancelWhileChecking">
              Back to form
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <SimilarityModal
      v-if="showModal"
      :visible="true"
      :loading="modalLoading"
      :check-id="results.checkId"
      :new-record="displayRecord"
      :analysis="{
        risk_level: results.riskLevel,
        overall_advice: results.overallAdvice,
        confidence: results.confidence
      }"
      :candidates="results.candidates"
      :suggested-action="results.suggestedAction"
      :checking-item-type="activeCheckingItemType"
      @create-anyway="onProceed"
      @use-existing="onUseExisting"
      @cancel="onCancel"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { checkSimilarity, recordUserDecision } from '@/services/similarityService';
import { buildSimilarityCheckPayload } from '@/utils/similaritySubmitHelper';
import SimilarityModal from './SimilarityModal.vue';

const props = defineProps({
  itemType: {
    type: String,
    required: true,
    validator: (v) => ['Framework', 'Policy', 'SubPolicy', 'Compliance'].includes(v)
  },
  itemData: { type: Object, required: true },
  tenantId: { type: Number, default: null },
  parentFrameworkId: { type: [Number, String], default: null },
  parentPolicyId: { type: [Number, String], default: null },
  parentSubpolicyId: { type: [Number, String], default: null },
  /** When editing, exclude this DB entity id from matches */
  excludeEntityId: { type: [Number, String], default: null }
});

const checking = ref(false);
const progressLabel = ref('');
const modalLoading = ref(false);
const showModal = ref(false);
const displayRecord = ref({});
const activeCheckingItemType = ref('');
const results = ref({
  checkId: null,
  riskLevel: 'LOW',
  overallAdvice: '',
  suggestedAction: 'ALLOW',
  candidates: [],
  confidence: null
});

let pendingResolve = null;
let cancelledWhileChecking = false;
let activeAbortController = null;
let runGeneration = 0;

function isCheckCancelledError(err) {
  return (
    cancelledWhileChecking
    || err?.code === 'ERR_CANCELED'
    || err?.name === 'CanceledError'
    || err?.message === 'Similarity check cancelled'
  );
}

function buildParams(overrides = null) {
  if (overrides) {
    return buildSimilarityCheckPayload(overrides);
  }
  return buildSimilarityCheckPayload({
    itemType: props.itemType,
    itemData: props.itemData,
    tenantId: props.tenantId,
    parentFrameworkId: props.parentFrameworkId,
    parentPolicyId: props.parentPolicyId,
    parentSubpolicyId: props.parentSubpolicyId,
    excludeEntityId: props.excludeEntityId
  });
}

function needsUserReview(response, forceReview = false) {
  if (forceReview) return true;
  const risk = (response.risk_level || '').toUpperCase();
  return (
    (response.candidates && response.candidates.length > 0)
    || risk === 'MEDIUM'
    || risk === 'HIGH'
  );
}

async function cleanupPendingAudit(checkId) {
  if (!checkId) return;
  try {
    await recordUserDecision(checkId, 'CANCEL');
  } catch (e) {
    console.warn('Similarity audit cleanup failed:', e);
  }
}

function finish(result) {
  showModal.value = false;
  checking.value = false;
  modalLoading.value = false;
  const resolve = pendingResolve;
  pendingResolve = null;
  if (resolve) resolve(result);
}

function onCancelWhileChecking() {
  cancelledWhileChecking = true;
  runGeneration += 1;
  progressLabel.value = '';
  if (activeAbortController) {
    activeAbortController.abort();
    activeAbortController = null;
  }
  // Only resolve an open modal promise; the in-flight HTTP call returns cancel via catch/generation check
  if (pendingResolve) {
    finish({ action: 'cancel' });
  } else {
    checking.value = false;
    showModal.value = false;
    modalLoading.value = false;
  }
}

function onProceed() {
  modalLoading.value = true;
  cleanupPendingAudit(results.value.checkId).finally(() => {
    finish({ action: 'proceed' });
  });
}

function onUseExisting(candidate) {
  modalLoading.value = true;
  const checkId = results.value.checkId;
  recordUserDecision(
    checkId,
    'USE_EXISTING',
    candidate?.id,
    `User selected existing ${candidate?.record_type || props.itemType}: ${candidate?.name}`
  )
    .finally(() => {
      finish({ action: 'use_existing', candidate });
    });
}

function onCancel() {
  cleanupPendingAudit(results.value.checkId).finally(() => {
    finish({ action: 'cancel' });
  });
}

/**
 * Run similarity check before form submit/save.
 * @param {Object} [overrides] - optional item_type, item_data, parent_* ids (overrides props)
 * @returns {Promise<{action: 'proceed'|'cancel'|'use_existing', candidate?}>}
 */
async function runCheck(overrides = null) {
  if (checking.value) {
    return { action: 'cancel' };
  }

  const generation = ++runGeneration;
  cancelledWhileChecking = false;

  activeAbortController = new AbortController();
  const { signal } = activeAbortController;

  checking.value = true;
  showModal.value = false;
  activeCheckingItemType.value = overrides?.item_type || overrides?.itemType || props.itemType || '';
  displayRecord.value = overrides?.item_data || overrides?.itemData || props.itemData || {};

  try {
    const response = await checkSimilarity(buildParams(overrides), { signal });

    if (generation !== runGeneration || cancelledWhileChecking) {
      if (response?.check_id) {
        await cleanupPendingAudit(response.check_id);
      }
      return { action: 'cancel' };
    }

    results.value = {
      checkId: response.check_id,
      riskLevel: response.risk_level || 'LOW',
      overallAdvice: response.overall_advice || '',
      suggestedAction: response.suggested_action || 'ALLOW',
      candidates: response.candidates || [],
      confidence: response.confidence ?? null
    };

    const forceReview = !!(overrides && overrides.alwaysShowReview);
    if (!needsUserReview(response, forceReview)) {
      await cleanupPendingAudit(response.check_id);
      return { action: 'proceed' };
    }

    return new Promise((resolve) => {
      pendingResolve = resolve;
      checking.value = false;
      showModal.value = true;
    });
  } catch (err) {
    if (isCheckCancelledError(err)) {
      return { action: 'cancel' };
    }
    console.error('Similarity submit gate failed:', err);
    // Option A: warn only — allow submit if check API fails
    return { action: 'proceed' };
  } finally {
    activeAbortController = null;
    if (!showModal.value && !pendingResolve) {
      checking.value = false;
    }
  }
}

function setProgressLabel(label) {
  progressLabel.value = label || '';
}

function clearProgressLabel() {
  progressLabel.value = '';
}

defineExpose({ runCheck, setProgressLabel, clearProgressLabel });
</script>

<style scoped>
.similarity-checking-overlay {
  position: fixed;
  inset: 0;
  z-index: 10000;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
}

.similarity-checking-box {
  background: #fff;
  border-radius: 12px;
  padding: 28px 32px;
  max-width: 420px;
  text-align: center;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.similarity-checking-spinner {
  display: inline-block;
  width: 36px;
  height: 36px;
  border: 3px solid #e5e7eb;
  border-top-color: #667eea;
  border-radius: 50%;
  animation: similarity-spin 0.8s linear infinite;
  margin-bottom: 16px;
}

.similarity-checking-title {
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0 0 8px;
  color: #111827;
}

.similarity-checking-sub {
  font-size: 0.875rem;
  color: #6b7280;
  margin: 0 0 16px;
  line-height: 1.45;
}

.similarity-checking-actions {
  display: flex;
  justify-content: center;
  gap: 0.75rem;
}

@keyframes similarity-spin {
  to { transform: rotate(360deg); }
}
</style>
