<template>
  <div class="similarity-review-page">
    <div v-if="loading" class="similarity-review-loading">
      <span class="spinner" />
      <p>{{ loadingMessage }}</p>
    </div>

    <div v-else-if="error" class="similarity-review-error">
      <p>{{ error }}</p>
      <button type="button" class="btn btn-secondary" @click="$router.back()">Go back</button>
    </div>

    <SimilarityModal
      v-else-if="showModal && currentResult"
      :visible="true"
      :loading="modalBusy"
      :check-id="currentCheckId"
      :new-record="currentResult.new_record || {}"
      :analysis="currentResult.analysis || {}"
      :candidates="currentResult.candidates || []"
      :suggested-action="currentResult.analysis?.suggested_action || 'ALLOW'"
      :checking-item-type="currentItemType"
      @create-anyway="onCreateAnyway"
      @use-existing="onUseExisting"
      @cancel="onCancelCheck"
    />

    <div v-else-if="allChecksDone && !saving" class="similarity-review-confirm">
      <h2>Confirm save</h2>
      <p>
        You reviewed {{ batchCheckIds.length }} similarity check(s) for
        <strong>{{ pendingLabel }}</strong>.
      </p>
      <button type="button" class="btn btn-primary" :disabled="saving" @click="confirmAndSave">
        Confirm and save update
      </button>
      <button type="button" class="btn btn-secondary" @click="$router.push('/notifications')">
        Cancel
      </button>
    </div>

    <div v-else-if="saving" class="similarity-review-loading">
      <span class="spinner" />
      <p>Saving your update…</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import SimilarityModal from '@/components/SimilarityModal.vue';
import { PopupService } from '@/modules/popup';
import apiService from '@/services/apiService';
import {
  getAsyncUpdateStatus,
  getSimilarityResult,
  getPendingSavePayload,
  markPendingSaveExecuted,
  executePendingSave,
  recordUserDecision,
} from '@/services/similarityAsyncUpdateService';

const route = useRoute();
const router = useRouter();

const masterCheckId = computed(() => parseInt(route.query.checkId, 10) || null);

const loading = ref(true);
const loadingMessage = ref('Loading similarity review…');
const error = ref('');
const batchCheckIds = ref([]);
const pendingLabel = ref('your update');
const checkIndex = ref(0);
const showModal = ref(false);
const modalBusy = ref(false);
const currentResult = ref(null);
const currentCheckId = ref(null);
const currentItemType = ref('');
const allChecksDone = ref(false);
const saving = ref(false);

async function loadBatch() {
  if (!masterCheckId.value) {
    error.value = 'Missing check id';
    loading.value = false;
    return;
  }
  const status = await getAsyncUpdateStatus(masterCheckId.value);
  if (status.background_status === 'PROCESSING') {
    loadingMessage.value = 'Background check still running…';
    setTimeout(loadBatch, 2000);
    return;
  }
  if (status.background_status === 'FAILED') {
    error.value = status.error || 'Background similarity check failed';
    loading.value = false;
    return;
  }
  pendingLabel.value = status.pending_save_label || 'your update';
  batchCheckIds.value = status.batch_check_ids?.length
    ? status.batch_check_ids
    : [masterCheckId.value];
  loading.value = false;
  await showNextCheck();
}

async function showNextCheck() {
  if (checkIndex.value >= batchCheckIds.value.length) {
    allChecksDone.value = true;
    showModal.value = false;
    return;
  }
  const cid = batchCheckIds.value[checkIndex.value];
  currentCheckId.value = cid;
  loadingMessage.value = `Loading check ${checkIndex.value + 1} of ${batchCheckIds.value.length}…`;
  const result = await getSimilarityResult(cid);
  currentResult.value = result;
  currentItemType.value = result.new_record?.type || '';
  const needsModal =
    (result.candidates && result.candidates.length > 0) ||
    ['MEDIUM', 'HIGH'].includes((result.analysis?.risk_level || '').toUpperCase());
  if (needsModal) {
    showModal.value = true;
  } else {
    try {
      await recordUserDecision(cid, 'CANCEL');
    } catch (e) {
      console.warn(e);
    }
    checkIndex.value += 1;
    await showNextCheck();
  }
}

async function advanceAfterDecision() {
  checkIndex.value += 1;
  showModal.value = false;
  modalBusy.value = false;
  await showNextCheck();
}

async function submitDecision(decision, selectedCandidateId = null) {
  modalBusy.value = true;
  try {
    const result = await recordUserDecision(
      currentCheckId.value,
      decision,
      selectedCandidateId
    );
    if (result?.success === false) {
      const err = result?.step9_result?.error || result?.error || 'Failed to record decision';
      PopupService.error(err, 'Error');
      modalBusy.value = false;
      return;
    }
    await advanceAfterDecision();
  } catch (e) {
    modalBusy.value = false;
    PopupService.error(e.message || 'Failed to record decision', 'Error');
  }
}

function onCreateAnyway() {
  return submitDecision('CREATE_ANYWAY');
}

function onUseExisting(candidate) {
  const selectedId =
    candidate?.entity_id ?? candidate?.id ?? candidate?.entityId ?? null;
  if (!selectedId) {
    PopupService.warning('Select a record to use.', 'Selection required');
    return;
  }
  return submitDecision('USE_EXISTING', selectedId);
}

function onCancelCheck() {
  PopupService.warning(
    'Save was not performed. You can return when ready to review again.',
    'Cancelled'
  );
  router.push('/notifications');
}

async function confirmAndSave() {
  saving.value = true;
  try {
    const pending = await getPendingSavePayload(masterCheckId.value);
    const response = await executePendingSave(
      {
        operation: pending.operation,
        entityPk: pending.entity_pk,
        payload: pending.payload,
      },
      apiService
    );
    if (pending.operation === 'policy_version' && response?.PolicyId && response?.FrameworkId) {
      const { usePolicyStore } = await import('@/stores/policy');
      usePolicyStore().prependPolicyTailoringCache(response.FrameworkId, {
        PolicyId: response.PolicyId,
        PolicyName: response.PolicyName || pending.payload?.PolicyName,
        Status: 'Under Review',
        FrameworkId: response.FrameworkId,
        ActiveInactive: 'Inactive',
        CurrentVersion: response.NewVersion,
      });
    }
    if (pending.operation === 'tt_create_policy' && response?.PolicyId && response?.FrameworkId) {
      const { usePolicyStore } = await import('@/stores/policy');
      const meta = pending.meta || {};
      usePolicyStore().prependPolicyTailoringCache(response.FrameworkId, {
        PolicyId: response.PolicyId,
        PolicyName: response.PolicyName || meta.policyNameSnapshot,
        PolicyDescription: meta.policyDescSnapshot,
        Status: response.Status || 'Under Review',
        FrameworkId: response.FrameworkId,
        ActiveInactive: 'Inactive',
      });
    }
    if (pending.operation === 'tt_create_framework' && response?.FrameworkId) {
      const { usePolicyStore } = await import('@/stores/policy');
      const policyDataService = (await import('@/services/policyService')).default;
      const meta = pending.meta || {};
      usePolicyStore().mergeFrameworkRowFromCreate({
        FrameworkId: response.FrameworkId,
        FrameworkName: response.FrameworkName || meta.frameworkNameSnapshot,
        Category: meta.frameworkCategorySnapshot,
        InternalExternal: meta.frameworkInternalExternalSnapshot || 'Internal',
        ActiveInactive: 'Inactive',
        Status: response.Status || 'Under Review',
        CurrentVersion: 1,
        FrameworkDescription: meta.frameworkDescSnapshot,
      });
      policyDataService.mergeExplorerFrameworkRow({
        id: response.FrameworkId,
        name: response.FrameworkName || meta.frameworkNameSnapshot,
        category: meta.frameworkCategorySnapshot || '',
        description: meta.frameworkDescSnapshot || '',
        status: 'Inactive',
        internalExternal: meta.frameworkInternalExternalSnapshot || 'Internal',
        versions: [{ version: 1 }],
      });
    }
    if (pending.operation === 'compliance_update' && response?.data?.success) {
      const { CompliancePopups } = await import('@/components/Compliance/utils/popupUtils');
      CompliancePopups.complianceUpdated({
        ComplianceId: response.data.compliance_id || pending.payload?.originalComplianceId,
        ComplianceVersion: pending.payload?.editData?.ComplianceVersion,
        ComplianceItemDescription: pending.payload?.editData?.ComplianceItemDescription,
      });
      await markPendingSaveExecuted(masterCheckId.value);
      PopupService.success('Update saved successfully.', 'Saved');
      router.push('/compliance/tailoring');
      return;
    }
    await markPendingSaveExecuted(masterCheckId.value);
    PopupService.success('Update saved successfully.', 'Saved');
    if (pending.operation === 'tt_create_policy' || pending.operation === 'policy_version') {
      router.push('/create-policy/tailoring');
      return;
    }
    if (pending.operation === 'tt_create_framework') {
      router.push('/framework-explorer');
      return;
    }
    router.push('/framework-explorer');
  } catch (e) {
    console.error(e);
    const msg = e.response?.data?.error || e.message || 'Save failed';
    PopupService.error(msg, 'Save failed');
    saving.value = false;
  }
}

onMounted(() => {
  loadBatch().catch((e) => {
    error.value = e.message || 'Failed to load review';
    loading.value = false;
  });
});
</script>

<style scoped>
.similarity-review-page {
  min-height: 320px;
  padding: 2rem;
  max-width: 960px;
  margin: 0 auto;
}
.similarity-review-loading,
.similarity-review-error,
.similarity-review-confirm {
  text-align: center;
  padding: 2rem;
}
.spinner {
  display: inline-block;
  width: 40px;
  height: 40px;
  border: 3px solid #e5e7eb;
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
.btn {
  margin: 0.5rem;
  padding: 0.5rem 1.25rem;
  border-radius: 6px;
  cursor: pointer;
}
.btn-primary {
  background: #3b6cf6;
  color: #fff;
  border: none;
}
.btn-secondary {
  background: #f3f4f6;
  border: 1px solid #d1d5db;
}
</style>
