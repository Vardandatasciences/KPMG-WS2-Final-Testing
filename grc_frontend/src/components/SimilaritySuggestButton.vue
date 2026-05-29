<template>
  <!-- 
    Similarity Suggest Button (Step 7)
    Add this next to "Create" button in any form
    
    Usage:
    <SimilaritySuggestButton
      :item-type="'Framework'"
      :item-data="formData"
      :tenant-id="tenantId"
      @similarity-checked="onSimilarityChecked"
      @create-anyway="onCreateAnyway"
      @use-existing="onUseExisting"
    />
  -->
  <div class="suggest-button-wrapper">
    <button
      type="button"
      class="suggest-btn"
      :disabled="disabled || loading"
      @click="onSuggestClick"
    >
      <span v-if="loading" class="spinner"></span>
      <span v-else>💡 Suggest</span>
    </button>
    
    <span v-if="hint" class="hint-text">{{ hint }}</span>

    <!-- Mount modal only when open — avoids vnode errors during parent $forceUpdate -->
    <SimilarityModal
      v-if="showModal"
      :visible="true"
      :loading="loading"
      :check-id="results.checkId"
      :new-record="itemData"
      :analysis="{
        risk_level: results.riskLevel,
        overall_advice: results.overallAdvice,
        confidence: results.confidence
      }"
      :candidates="results.candidates"
      :suggested-action="results.suggestedAction"
      @create-anyway="onCreateAnyway"
      @use-existing="onUseExisting"
      @cancel="onCancel"
    />
  </div>
</template>

<script setup>
import { useSimilarityCheck } from '@/composables/useSimilarityCheck';
import SimilarityModal from './SimilarityModal.vue';

const props = defineProps({
  // Required props
  itemType: { 
    type: String, 
    required: true,
    validator: (value) => ['Framework', 'Policy', 'SubPolicy', 'Compliance'].includes(value)
  },
  itemData: { type: Object, required: true },
  tenantId: { type: Number, default: null },
  
  // Optional parent IDs for hierarchical records
  parentFrameworkId: { type: Number, default: null },
  parentPolicyId: { type: Number, default: null },
  parentSubpolicyId: { type: Number, default: null },
  
  // Button state
  disabled: { type: Boolean, default: false },
  hint: { type: String, default: 'Check for similar records' }
});

const emit = defineEmits([
  'similarity-checked',  // Emits when check completes with results
  'create-anyway',       // Emits Step 9 result: {success, action, recordId, recordType, message}
  'use-existing'         // Emits Step 9 result with candidate info
]);

// Use the similarity check composable
const {
  showModal,
  loading,
  results,
  checkSimilarity,
  handleCreateAnyway,
  handleUseExisting,
  handleCancel
} = useSimilarityCheck();

const onSuggestClick = async () => {
  // Resolve tenant_id from prop or localStorage
  const tenantId = props.tenantId
    || parseInt(localStorage.getItem('tenant_id'))
    || parseInt(localStorage.getItem('tenantId'))
    || null;

  // DEBUG: log what we are about to send
  console.log('[SimilaritySuggestButton] itemType:', props.itemType);
  console.log('[SimilaritySuggestButton] itemData:', JSON.stringify(props.itemData));
  console.log('[SimilaritySuggestButton] tenantId:', tenantId);

  // Build params based on item type
  const params = {
    item_type: props.itemType,
    item_data: props.itemData,
    tenant_id: tenantId
  };
  
  // Add parent IDs for hierarchical records (Chroma expects numeric IDs)
  const fwId = props.parentFrameworkId != null && props.parentFrameworkId !== ''
    ? parseInt(props.parentFrameworkId, 10) : null;
  const polId = props.parentPolicyId != null && props.parentPolicyId !== ''
    ? parseInt(props.parentPolicyId, 10) : null;
  const subPolId = props.parentSubpolicyId != null && props.parentSubpolicyId !== ''
    ? parseInt(props.parentSubpolicyId, 10) : null;
  if (fwId && !Number.isNaN(fwId)) params.parent_framework_id = fwId;
  if (polId && !Number.isNaN(polId)) params.parent_policy_id = polId;
  if (subPolId && !Number.isNaN(subPolId)) params.parent_subpolicy_id = subPolId;
  
  try {
    const response = await checkSimilarity(params);
    emit('similarity-checked', response);
    
    // If no similar records found (LOW risk), auto-proceed with creation
    if (!response.candidates?.length && response.risk_level === 'LOW') {
      emit('create-anyway', { success: true, action: 'CREATE_NEW', message: 'No similar records found. Safe to create.' });
    }
  } catch (err) {
    console.error('Similarity check failed:', err);
  }
};

const onCreateAnyway = async () => {
  const step9Result = await handleCreateAnyway();
  if (step9Result) {
    emit('create-anyway', step9Result);
  }
};

const onUseExisting = async (candidate) => {
  const step9Result = await handleUseExisting(candidate);
  if (step9Result) {
    emit('use-existing', step9Result);
  }
};

const onCancel = () => {
  handleCancel();
};
</script>

<style scoped>
.suggest-button-wrapper {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.suggest-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.suggest-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.suggest-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.hint-text {
  font-size: 12px;
  color: #666;
  font-style: italic;
}
</style>
