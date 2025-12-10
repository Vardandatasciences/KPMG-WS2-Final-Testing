/**
 * Consent Manager Utility
 * Provides functions to check and handle consent requirements across the application
 */

import axios from 'axios';
import { API_BASE_URL } from '../config/api.js';

/**
 * Check if consent is required for a specific action
 * @param {string} actionType - The type of action (e.g., 'create_policy', 'upload_policy')
 * @returns {Promise<{required: boolean, config: object|null}>}
 */
/**
 * Get framework ID from various sources
 * @returns {string|null} Framework ID or null
 */
function getFrameworkId() {
  // Try multiple sources
  let frameworkId = localStorage.getItem('framework_id') || 
                    localStorage.getItem('selectedFrameworkId') ||
                    localStorage.getItem('frameworkId') ||
                    sessionStorage.getItem('framework_id') ||
                    sessionStorage.getItem('selectedFrameworkId');
  
  // If still not found, default to 1 (most common case)
  if (!frameworkId) {
    console.warn('⚠️ [Consent] Framework ID not found in storage, defaulting to 1');
    frameworkId = '1';
    localStorage.setItem('framework_id', '1');
  }
  
  return frameworkId;
}

export async function checkConsentRequired(actionType) {
  try {
    const frameworkId = getFrameworkId();
    const token = localStorage.getItem('access_token');
    const userId = localStorage.getItem('user_id');

    if (!token) {
      // Don't log as error - this is expected when user is logged out
      // Just return without requiring consent (fail-open behavior)
      console.warn('⚠️ [Consent] No access token found - skipping consent check');
      return { required: false, config: null };
    }
    
    console.log(`🔍 [Consent] Checking consent for action: ${actionType}, framework: ${frameworkId}`);
    console.log(`🔍 [Consent] API URL: ${API_BASE_URL}/api/consent/check/`);
    
    const payload = {
      action_type: actionType,
      framework_id: frameworkId
    };
    
    // Include user_id if available to check for active consent
    if (userId) {
      payload.user_id = userId;
    }
    
    console.log(`🔍 [Consent] Request payload:`, payload);

    const response = await axios.post(
      `${API_BASE_URL}/api/consent/check/`,
      payload,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      }
    );

    console.log('📡 [Consent] API Response Status:', response.status);
    console.log('📡 [Consent] API Response Data:', JSON.stringify(response.data, null, 2));

    if (response.data.status === 'success') {
      const isRequired = response.data.required;
      console.log(`${isRequired ? '✅' : '❌'} [Consent] Consent ${isRequired ? 'REQUIRED' : 'not required'} for ${actionType}`);
      if (isRequired) {
        console.log('📋 [Consent] Config:', response.data.config);
      } else {
        console.log('ℹ️ [Consent] Consent not required - config.is_enabled is false or config not found');
      }
      return {
        required: response.data.required,
        config: response.data.config
      };
    }

    console.warn('⚠️ [Consent] Unexpected response from consent API:', response.data);
    return { required: false, config: null };
  } catch (error) {
    console.error('❌ [Consent] Error checking consent requirement:', error);
    console.error('❌ [Consent] Error details:', error.response?.data || error.message);
    console.error('❌ [Consent] Full error:', error);
    
    // Log the full error response for debugging
    if (error.response) {
      console.error('❌ [Consent] Error response status:', error.response.status);
      console.error('❌ [Consent] Error response data:', error.response.data);
    }
    
    // In case of error, don't block the action but log it clearly
    console.warn('⚠️ [Consent] Allowing action to proceed due to error (fail-open behavior)');
    return { required: false, config: null };
  }
}

/**
 * Record consent acceptance
 * @param {number} userId - User ID
 * @param {number} configId - Consent configuration ID
 * @param {string} actionType - Action type
 * @param {string} ipAddress - IP address (optional)
 * @returns {Promise<boolean>} - Success status
 */

export async function recordConsentAcceptance(userId, configId, actionType, ipAddress = null) {
  try {
    const frameworkId = localStorage.getItem('framework_id');
    const token = localStorage.getItem('access_token');

    // If IP address not provided, let backend extract it from request
    // The backend will get it from request.META
    const response = await axios.post(
      `${API_BASE_URL}/api/consent/accept/`,
      {
        user_id: userId,
        config_id: configId,
        action_type: actionType,
        framework_id: frameworkId,
        ip_address: ipAddress, // Can be null, backend will extract from request
        user_agent: navigator.userAgent
      },
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      }
    );

    return response.data.status === 'success';
  } catch (error) {
    console.error('Error recording consent acceptance:', error);
    return false;
  }
}

/**
 * Get consent action type mappings
 * Provides a map of action names to consent action types
 */
export const CONSENT_ACTIONS = {
  CREATE_POLICY: 'create_policy',
  CREATE_COMPLIANCE: 'create_compliance',
  CREATE_AUDIT: 'create_audit',
  CREATE_INCIDENT: 'create_incident',
  CREATE_RISK: 'create_risk',
  CREATE_EVENT: 'create_event',
  UPLOAD_POLICY: 'upload_policy',
  UPLOAD_AUDIT: 'upload_audit',
  UPLOAD_INCIDENT: 'upload_incident',
  UPLOAD_RISK: 'upload_risk',
  UPLOAD_EVENT: 'upload_event'
};

/**
 * Get human-readable action label
 * @param {string} actionType - Action type constant
 * @returns {string} - Human-readable label
 */
export function getActionLabel(actionType) {
  const labels = {
    'create_policy': 'Create Policy',
    'create_compliance': 'Create Compliance',
    'create_audit': 'Create Audit',
    'create_incident': 'Create Incident',
    'create_risk': 'Create Risk',
    'create_event': 'Create Event',
    'upload_policy': 'Upload in Policy',
    'upload_audit': 'Upload in Audit',
    'upload_incident': 'Upload in Incident',
    'upload_risk': 'Upload in Risk',
    'upload_event': 'Upload in Event'
  };
  return labels[actionType] || actionType;
}

/**
 * Consent Manager Class for Vue components
 * Can be used as a mixin or imported directly
 */
export class ConsentManager {
  constructor() {
    this.showModal = false;
    this.currentAction = null;
    this.currentConfig = null;
    this.pendingCallback = null;
  }

  /**
   * Execute an action with consent check
   * @param {string} actionType - Action type
   * @param {Function} callback - Function to execute after consent (if required)
   * @returns {Promise<boolean>} - Success status
   */
  async executeWithConsent(actionType, callback) {
    const { required, config } = await checkConsentRequired(actionType);

    if (required && config) {
      // Store the callback to execute after consent
      this.currentAction = actionType;
      this.currentConfig = config;
      this.pendingCallback = callback;
      return false; // Indicates consent is required
    } else {
      // No consent required, execute immediately
      if (callback) {
        await callback();
      }
      return true; // Indicates action completed
    }
  }

  /**
   * Handle consent acceptance
   */
  async onConsentAccepted() {
    if (this.pendingCallback) {
      await this.pendingCallback();
      this.clear();
    }
  }

  /**
   * Clear current action state
   */
  clear() {
    this.currentAction = null;
    this.currentConfig = null;
    this.pendingCallback = null;
  }
}

/**
 * Vue Composable for Consent Management
 * Use this in Vue 3 Composition API
 */
export function useConsent() {
  const consentData = {
    showModal: false,
    actionType: null,
    config: null,
    pendingCallback: null
  };

  const checkAndExecute = async (actionType, callback) => {
    const { required, config } = await checkConsentRequired(actionType);

    if (required && config) {
      consentData.showModal = true;
      consentData.actionType = actionType;
      consentData.config = config;
      consentData.pendingCallback = callback;
      return false;
    } else {
      if (callback) {
        await callback();
      }
      return true;
    }
  };

  const onConsentAccepted = async () => {
    if (consentData.pendingCallback) {
      await consentData.pendingCallback();
      closeModal();
    }
  };

  const closeModal = () => {
    consentData.showModal = false;
    consentData.actionType = null;
    consentData.config = null;
    consentData.pendingCallback = null;
  };

  return {
    consentData,
    checkAndExecute,
    onConsentAccepted,
    closeModal
  };
}

/**
 * Withdraw consent for a specific action
 * @param {number} userId - User ID
 * @param {string} actionType - Action type
 * @param {string} reason - Optional reason for withdrawal
 * @returns {Promise<Object>} - Withdrawal response
 */
export async function withdrawConsent(userId, actionType, reason = null) {
  try {
    const frameworkId = getFrameworkId();
    const token = localStorage.getItem('access_token');

    const response = await axios.post(
      `${API_BASE_URL}/api/consent/withdraw/`,
      {
        user_id: userId,
        action_type: actionType,
        framework_id: frameworkId,
        ip_address: null, // Can be set server-side if needed
        user_agent: navigator.userAgent,
        reason: reason
      },
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      }
    );

    return response.data;
  } catch (error) {
    console.error('Error withdrawing consent:', error);
    throw error;
  }
}

/**
 * Withdraw all consents for a user
 * @param {number} userId - User ID
 * @param {number|null} frameworkId - Optional framework ID (if null, withdraws from all frameworks)
 * @param {string} reason - Optional reason for withdrawal
 * @returns {Promise<Object>} - Withdrawal response
 */
export async function withdrawAllConsents(userId, frameworkId = null, reason = null) {
  try {
    const fwId = frameworkId || getFrameworkId();
    const token = localStorage.getItem('access_token');

    const payload = {
      user_id: userId,
      ip_address: null,
      user_agent: navigator.userAgent,
      reason: reason
    };

    if (fwId) {
      payload.framework_id = fwId;
    }

    const response = await axios.post(
      `${API_BASE_URL}/api/consent/withdraw-all/`,
      payload,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      }
    );

    return response.data;
  } catch (error) {
    console.error('Error withdrawing all consents:', error);
    throw error;
  }
}

/**
 * Get user's consent withdrawal history
 * @param {number} userId - User ID
 * @param {number|null} frameworkId - Optional framework ID filter
 * @param {string|null} actionType - Optional action type filter
 * @returns {Promise<Object>} - Withdrawal history
 */
export async function getUserConsentWithdrawals(userId, frameworkId = null, actionType = null) {
  try {
    const token = localStorage.getItem('access_token');
    const params = {};

    if (frameworkId) {
      params.framework_id = frameworkId;
    }
    if (actionType) {
      params.action_type = actionType;
    }

    const response = await axios.get(
      `${API_BASE_URL}/api/consent/withdrawals/${userId}/`,
      {
        params,
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      }
    );

    return response.data;
  } catch (error) {
    console.error('Error fetching consent withdrawals:', error);
    throw error;
  }
}

/**
 * Check consent status for a user (including withdrawals)
 * @param {number} userId - User ID
 * @param {number} frameworkId - Framework ID
 * @param {string|null} actionType - Optional action type
 * @returns {Promise<Object>} - Consent status
 */
export async function checkConsentStatus(userId, frameworkId, actionType = null) {
  try {
    const token = localStorage.getItem('access_token');
    const params = {
      framework_id: frameworkId
    };

    if (actionType) {
      params.action_type = actionType;
    }

    const response = await axios.get(
      `${API_BASE_URL}/api/consent/status/${userId}/`,
      {
        params,
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      }
    );

    return response.data;
  } catch (error) {
    console.error('Error checking consent status:', error);
    throw error;
  }
}

export default {
  checkConsentRequired,
  recordConsentAcceptance,
  withdrawConsent,
  withdrawAllConsents,
  getUserConsentWithdrawals,
  checkConsentStatus,
  CONSENT_ACTIONS,
  getActionLabel,
  ConsentManager,
  useConsent
};

