/**
 * TPRM Consent Management Utility
 * Provides functions to check and record consent for TPRM actions
 */

import axios from 'axios';
import { getApiOrigin } from '@/utils/backendEnv';

// Get API base URL - use the same method as other TPRM files
// TPRM consent endpoints are at /api/tprm/consent/
const getApiBaseUrl = () => {
  const origin = getApiOrigin();
  // API_BASE_URL should be the origin (e.g., http://127.0.0.1:8000)
  // The endpoints will be constructed as ${API_BASE_URL}/api/tprm/consent/...
  return origin;
};

const API_BASE_URL = getApiBaseUrl();
console.log('[TPRM Consent] API Base URL initialized:', API_BASE_URL);

// TPRM Action Types
export const TPRM_CONSENT_ACTIONS = {
  CREATE_SLA: 'tprm_create_sla',
  UPDATE_SLA: 'tprm_update_sla',
  DELETE_SLA: 'tprm_delete_sla',
  CREATE_VENDOR: 'tprm_create_vendor',
  UPDATE_VENDOR: 'tprm_update_vendor',
  CREATE_CONTRACT: 'tprm_create_contract',
  UPDATE_CONTRACT: 'tprm_update_contract',
  CREATE_RFP: 'tprm_create_rfp',
  SUBMIT_RFP: 'tprm_submit_rfp',
  CREATE_RISK: 'tprm_create_risk',
  CREATE_COMPLIANCE: 'tprm_create_compliance',
  CREATE_PLANS: 'tprm_create_plans',
};

// Action Labels for display
export const TPRM_ACTION_LABELS = {
  [TPRM_CONSENT_ACTIONS.CREATE_SLA]: 'Create SLA',
  [TPRM_CONSENT_ACTIONS.UPDATE_SLA]: 'Update SLA',
  [TPRM_CONSENT_ACTIONS.DELETE_SLA]: 'Delete SLA',
  [TPRM_CONSENT_ACTIONS.CREATE_VENDOR]: 'Create Vendor',
  [TPRM_CONSENT_ACTIONS.UPDATE_VENDOR]: 'Update Vendor',
  [TPRM_CONSENT_ACTIONS.CREATE_CONTRACT]: 'Create Contract',
  [TPRM_CONSENT_ACTIONS.UPDATE_CONTRACT]: 'Update Contract',
  [TPRM_CONSENT_ACTIONS.CREATE_RFP]: 'Create RFP',
  [TPRM_CONSENT_ACTIONS.SUBMIT_RFP]: 'Submit RFP',
  [TPRM_CONSENT_ACTIONS.CREATE_RISK]: 'Create Risk Assessment',
  [TPRM_CONSENT_ACTIONS.CREATE_COMPLIANCE]: 'Create Compliance Record',
};

/**
 * Get action label for display
 */
export function getTPRMActionLabel(actionType) {
  return TPRM_ACTION_LABELS[actionType] || actionType;
}

/**
 * Check if consent is required for a TPRM action
 * @param {string} actionType - The action type (e.g., 'tprm_create_sla')
 * @param {number} userId - Optional user ID to check for active consent
 * @param {number} frameworkId - Optional framework ID (defaults to 1 for TPRM)
 * @returns {Promise<{required: boolean, config: object|null, has_active_consent: boolean|null}>}
 */
export async function checkTPRMConsentRequired(actionType, userId = null, frameworkId = 1) {
  try {
    const token = localStorage.getItem('access_token');
    const checkUserId = userId || localStorage.getItem('user_id');
    
    console.log('[TPRM Consent] Checking consent requirement:', {
      actionType,
      userId: checkUserId,
      frameworkId,
      apiUrl: `${API_BASE_URL}/api/tprm/consent/check-required/`
    });
    
    const response = await axios.post(
      `${API_BASE_URL}/api/tprm/consent/check-required/`,
      {
        action_type: actionType,
        framework_id: frameworkId,
        user_id: checkUserId
      },
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      }
    );

    console.log('[TPRM Consent] Consent check API response:', response.data);

    if (response.data.status === 'success') {
      const result = {
        required: response.data.required,
        config: response.data.config,
        has_active_consent: response.data.has_active_consent
      };
      console.log('[TPRM Consent] Consent check result:', result);
      return result;
    } else {
      console.warn('[TPRM Consent] Consent check returned non-success status:', response.data);
      throw new Error(response.data.message || 'Failed to check consent requirement');
    }
  } catch (error) {
    console.error('[TPRM Consent] Error checking consent requirement:', error);
    console.error('[TPRM Consent] Error response:', error.response?.data);
    console.error('[TPRM Consent] Error status:', error.response?.status);
    
    // If backend returns CONSENT_REQUIRED error, extract config
    if (error.response?.data?.error === 'CONSENT_REQUIRED') {
      console.log('[TPRM Consent] Backend indicated consent required via error response');
      return {
        required: true,
        config: error.response.data.consent_config,
        has_active_consent: false
      };
    }
    
    // On error, log but don't fail open - let the user know something went wrong
    console.warn('[TPRM Consent] Consent check failed, but continuing (may need to check manually)');
    return {
      required: false,
      config: null,
      has_active_consent: null
    };
  }
}

/**
 * Record consent acceptance
 * @param {number} userId - User ID
 * @param {number} configId - Consent configuration ID
 * @param {string} actionType - The action type
 * @param {number} frameworkId - Framework ID (defaults to 1 for TPRM)
 * @returns {Promise<boolean>} - Success status
 */
export async function recordTPRMConsentAcceptance(userId, configId, actionType, frameworkId = 1) {
  try {
    const token = localStorage.getItem('access_token');
    const response = await axios.post(
      `${API_BASE_URL}/api/tprm/consent/accept/`,
      {
        user_id: userId,
        config_id: configId,
        action_type: actionType,
        framework_id: frameworkId
      },
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      }
    );

    if (response.data.status === 'success') {
      console.log('[TPRM Consent] Consent acceptance recorded successfully');
      return true;
    } else {
      console.error('[TPRM Consent] Failed to record consent:', response.data.message);
      return false;
    }
  } catch (error) {
    console.error('[TPRM Consent] Error recording consent acceptance:', error);
    return false;
  }
}

/**
 * Execute an action with consent check
 * This is a helper function that checks consent, shows modal if needed, and executes the action
 * @param {string} actionType - The action type
 * @param {Function} actionFunction - The function to execute after consent is accepted
 * @param {Function} showConsentModal - Function to show consent modal (should return a Promise that resolves to true/false)
 * @returns {Promise<any>} - Result of the action function
 */
export async function executeWithTPRMConsent(actionType, actionFunction, showConsentModal) {
  console.log(`[TPRM Consent] ========== Starting consent flow for: ${actionType} ==========`);
  
  try {
    // Step 1: Check if consent is required
    const userId = localStorage.getItem('user_id');
    console.log(`[TPRM Consent] Checking consent requirement for user: ${userId}`);
    
    const { required, config, has_active_consent } = await checkTPRMConsentRequired(actionType, userId);
    
    console.log(`[TPRM Consent] Consent check completed:`, {
      required,
      hasConfig: !!config,
      has_active_consent,
      configId: config?.config_id,
      actionType: config?.action_type
    });
    
    if (required && config) {
      // Check if user already has active consent
      if (has_active_consent) {
        console.log(`[TPRM Consent] ✅ User already has active consent for ${actionType} - proceeding without modal`);
        // User has active consent, proceed directly
        return await actionFunction(config);
      }
      
      console.log(`[TPRM Consent] ⚠️ Consent required for ${actionType} - showing modal`);
      console.log(`[TPRM Consent] Modal config:`, config);
      
      // Step 2: Show consent modal
      const accepted = await showConsentModal(actionType, config);
      
      console.log(`[TPRM Consent] Modal response:`, accepted, typeof accepted);
      
      if (accepted === true || accepted === 'true') {
        console.log(`[TPRM Consent] ✅ User accepted consent for ${actionType} - proceeding with action`);
        // Step 3: Execute action with consent data
        return await actionFunction(config);
      } else {
        console.log(`[TPRM Consent] ❌ User rejected/cancelled consent for ${actionType}`);
        throw new Error('Action cancelled - consent not accepted');
      }
    } else {
      if (!required) {
        console.log(`[TPRM Consent] ℹ️ No consent required for ${actionType} (consent not enabled) - proceeding directly`);
      } else if (!config) {
        console.warn(`[TPRM Consent] ⚠️ Consent required but no config found for ${actionType}`);
      }
      // No consent required, execute directly
      return await actionFunction(null);
    }
  } catch (error) {
    console.error(`[TPRM Consent] ❌ Error in consent flow:`, error);
    console.error(`[TPRM Consent] Error message:`, error.message);
    console.error(`[TPRM Consent] Error stack:`, error.stack);
    
    // Check if the backend returned a CONSENT_REQUIRED error
    if (error.response?.data?.error === 'CONSENT_REQUIRED') {
      console.log(`[TPRM Consent] 🔄 Backend requested consent via error response`);
      const config = error.response.data.consent_config;
      const accepted = await showConsentModal(config.action_type, config);
      
      if (accepted) {
        return await actionFunction(config);
      } else {
        throw new Error('Action cancelled - consent rejected');
      }
    } else {
      throw error;
    }
  }
}

