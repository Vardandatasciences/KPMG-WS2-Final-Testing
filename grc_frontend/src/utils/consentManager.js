/**
 * Consent Manager Utility
 * Provides functions to check and handle consent requirements across the application
 */

import { apiService } from '../services/apiService.js';
import { getFrameworkIdForClient, getSessionFrameworkId } from './frameworkContextStorage.js';

/**
 * Framework id for consent APIs: session-scoped only + env default (no localStorage).
 */
function getFrameworkId() {
  const id = getFrameworkIdForClient();
  if (!getSessionFrameworkId()) {
    console.warn(
      '⚠️ [Consent] No session framework_id; using default for this request'
    );
  }
  return id;
}

/**
 * SECURITY: Standardizes user ID retrieval from centralized session handling.
 * Avoids direct sessionStorage access where possible.
 */
function getUserId() {
  // apiService has a helper to resolve this correctly from various session sources
  // But since it's not exported as a standalone helper yet, we use a safe fallback.
  try {
    const currentUserStr = sessionStorage.getItem('current_user');
    if (currentUserStr) {
      const parsed = JSON.parse(currentUserStr);
      return parsed?.UserId || parsed?.user_id || parsed?.id || sessionStorage.getItem('user_id');
    }
  } catch (e) {
    return sessionStorage.getItem('user_id');
  }
  return sessionStorage.getItem('user_id');
}

export async function checkConsentRequired(actionType) {
  try {
    const frameworkId = getFrameworkId();
    const userId = getUserId();

    const payload = {
      action_type: actionType,
      framework_id: frameworkId
    };

    if (userId) {
      payload.user_id = userId;
    }

    // Use apiService for secure, cookie-first authentication and logging
    const response = await apiService.post('/api/consent/check/', payload);

    if (response && response.status === 'success') {
      return {
        required: response.required,
        config: response.config
      };
    }

    return { required: false, config: null };
  } catch (error) {
    // In case of error, we fail-open for UX but log the issue securely
    console.error('❌ [Consent] Error checking consent requirement:', error.message);
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
    const frameworkId = getFrameworkId();

    // The backend will extract IP and User Agent securely if passed as null
    const response = await apiService.post('/api/consent/accept/', {
      user_id: userId,
      config_id: configId,
      action_type: actionType,
      framework_id: frameworkId,
      ip_address: ipAddress,
      user_agent: navigator.userAgent
    });

    return response && response.status === 'success';
  } catch (error) {
    console.error('Error recording consent acceptance:', error.message);
    return false;
  }
}

/**
 * Get consent action type mappings
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
 */
export class ConsentManager {
  constructor() {
    this.showModal = false;
    this.currentAction = null;
    this.currentConfig = null;
    this.pendingCallback = null;
  }

  async executeWithConsent(actionType, callback) {
    const { required, config } = await checkConsentRequired(actionType);

    if (required && config) {
      this.currentAction = actionType;
      this.currentConfig = config;
      this.pendingCallback = callback;
      return false; 
    } else {
      if (callback) {
        await callback();
      }
      return true;
    }
  }

  async onConsentAccepted() {
    if (this.pendingCallback) {
      await this.pendingCallback();
      this.clear();
    }
  }

  clear() {
    this.currentAction = null;
    this.currentConfig = null;
    this.pendingCallback = null;
  }
}

/**
 * Vue Composable for Consent Management
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
 */
export async function withdrawConsent(userId, actionType, reason = null, frameworkId = null) {
  try {
    const fwId = frameworkId || getFrameworkId();

    return await apiService.post('/api/consent/withdraw/', {
      user_id: userId,
      action_type: actionType,
      framework_id: fwId,
      ip_address: null,
      user_agent: navigator.userAgent,
      reason: reason
    });
  } catch (error) {
    console.error('Error withdrawing consent:', error.message);
    throw error;
  }
}

/**
 * Withdraw all consents for a user
 */
export async function withdrawAllConsents(userId, frameworkId = null, reason = null) {
  try {
    const fwId = frameworkId || getFrameworkId();

    const payload = {
      user_id: userId,
      ip_address: null,
      user_agent: navigator.userAgent,
      reason: reason
    };

    if (fwId) {
      payload.framework_id = fwId;
    }

    return await apiService.post('/api/consent/withdraw-all/', payload);
  } catch (error) {
    console.error('Error withdrawing all consents:', error.message);
    throw error;
  }
}

/**
 * Get user's consent withdrawal history
 */
export async function getUserConsentWithdrawals(userId, frameworkId = null, actionType = null) {
  try {
    const params = {};
    if (frameworkId) params.framework_id = frameworkId;
    if (actionType) params.action_type = actionType;

    return await apiService.get(`/api/consent/withdrawals/${userId}/`, params);
  } catch (error) {
    console.error('Error fetching consent withdrawals:', error.message);
    throw error;
  }
}

/**
 * Get user's consent acceptance history
 */
export async function getUserConsentHistory(userId, frameworkId = null, actionType = null) {
  try {
    const params = {};
    if (frameworkId) params.framework_id = frameworkId;
    if (actionType) params.action_type = actionType;

    return await apiService.get(`/api/consent/user-history/${userId}/`, params);
  } catch (error) {
    console.error('Error fetching consent history:', error.message);
    throw error;
  }
}

/**
 * Check consent status for a user (including withdrawals)
 */
export async function checkConsentStatus(userId, frameworkId, actionType = null) {
  try {
    const params = {};
    if (frameworkId !== null && frameworkId !== undefined && frameworkId !== '') {
      params.framework_id = frameworkId;
    }
    if (actionType) {
      params.action_type = actionType;
    }

    return await apiService.get(`/api/consent/status/${userId}/`, params);
  } catch (error) {
    console.error('Error checking consent status:', error.message);
    throw error;
  }
}

export default {
  checkConsentRequired,
  recordConsentAcceptance,
  withdrawConsent,
  withdrawAllConsents,
  getUserConsentHistory,
  getUserConsentWithdrawals,
  checkConsentStatus,
  CONSENT_ACTIONS,
  getActionLabel,
  ConsentManager,
  useConsent
};
