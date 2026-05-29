/**
 * Composable for Similarity Check (Step 7 Integration)
 * Use in any creation form (Framework, Policy, SubPolicy, Compliance)
 * 
 * Usage:
 * const { showModal, loading, results, checkSimilarity, handleCreateAnyway, handleUseExisting } = useSimilarityCheck();
 */

import { ref } from 'vue';
import { checkSimilarity as apiCheckSimilarity, recordUserDecision } from '@/services/similarityService';

export function useSimilarityCheck() {
  // State
  const showModal = ref(false);
  const loading = ref(false);
  const results = ref({
    checkId: null,
    canCreate: true,
    riskLevel: 'LOW',
    overallAdvice: '',
    suggestedAction: 'ALLOW',
    candidates: []
  });
  const error = ref(null);

  /**
   * Check similarity before creating
   * Call this when user clicks "Suggest" button
   * 
   * @param {Object} params
   * @param {string} params.item_type - 'Framework'|'Policy'|'SubPolicy'|'Compliance'
   * @param {Object} params.item_data - Form data
   * @param {number} params.tenant_id - Tenant ID
   * @param {number} [params.parent_framework_id] - For Policy/SubPolicy/Compliance
   * @param {number} [params.parent_policy_id] - For SubPolicy/Compliance
   * @param {number} [params.parent_subpolicy_id] - For Compliance
   */
  const checkSimilarity = async (params) => {
    loading.value = true;
    error.value = null;
    
    try {
      const response = await apiCheckSimilarity(params);
      
      results.value = {
        checkId: response.check_id,
        canCreate: response.can_create,
        riskLevel: response.risk_level,
        overallAdvice: response.overall_advice,
        suggestedAction: response.suggested_action,
        candidates: response.candidates || [],
        domain: response.domain,
        industry: response.industry
      };
      
      // Show modal if similar records found or risk is medium/high
      if (response.candidates?.length > 0 || response.risk_level === 'MEDIUM' || response.risk_level === 'HIGH') {
        showModal.value = true;
      }
      
      return response;
      
    } catch (err) {
      console.error('Similarity check failed:', err);
      error.value = err.message || 'Failed to check similarity';
      throw err;
    } finally {
      loading.value = false;
    }
  };

  /**
   * Handle "Create Anyway" decision
   * Records user decision (Step 8) and finalizes (Step 9)
   * Returns created record info
   */
  const handleCreateAnyway = async () => {
    if (!results.value.checkId) return null;
    
    loading.value = true;
    
    try {
      const response = await recordUserDecision(results.value.checkId, 'CREATE_ANYWAY');
      showModal.value = false;
      
      // Return Step 9 result with created record info
      return {
        success: response.success,
        action: response.step9_result?.action_taken,
        recordId: response.step9_result?.created_record_id,
        recordType: response.step9_result?.created_record_type,
        message: response.step9_result?.message
      };
    } catch (err) {
      console.error('Failed to finalize:', err);
      error.value = err.message;
      return null;
    } finally {
      loading.value = false;
    }
  };

  /**
   * Handle "Use Existing" decision (Step 8 & 9)
   * @param {Object} candidate - Selected existing record
   */
  const handleUseExisting = async (candidate) => {
    if (!results.value.checkId || !candidate) return null;
    
    loading.value = true;
    
    try {
      const response = await recordUserDecision(
        results.value.checkId, 
        'USE_EXISTING', 
        candidate.id,
        `User selected existing ${candidate.record_type}: ${candidate.name}`
      );
      showModal.value = false;
      
      // Return Step 9 result
      return {
        success: response.success,
        action: response.step9_result?.action_taken,
        recordId: response.step9_result?.created_record_id || candidate.id,
        recordType: response.step9_result?.created_record_type || candidate.record_type,
        message: response.step9_result?.message,
        candidate: candidate
      };
    } catch (err) {
      console.error('Failed to finalize:', err);
      error.value = err.message;
      return null;
    } finally {
      loading.value = false;
    }
  };

  /**
   * Handle "Cancel" - Close modal without action
   */
  const handleCancel = () => {
    showModal.value = false;
    
    // Optionally record cancel decision
    if (results.value.checkId) {
      recordUserDecision(results.value.checkId, 'CANCEL').catch(console.error);
    }
  };

  /**
   * Reset state
   */
  const reset = () => {
    showModal.value = false;
    loading.value = false;
    results.value = {
      checkId: null,
      canCreate: true,
      riskLevel: 'LOW',
      overallAdvice: '',
      suggestedAction: 'ALLOW',
      candidates: []
    };
    error.value = null;
  };

  return {
    // State (reactive)
    showModal,
    loading,
    results,
    error,
    
    // Methods
    checkSimilarity,
    handleCreateAnyway,
    handleUseExisting,
    handleCancel,
    reset
  };
}
