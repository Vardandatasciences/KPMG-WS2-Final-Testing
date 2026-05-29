/**
 * Similarity Detection Service (Step 7 Frontend)
 * API calls for similarity check and results
 */

import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || '/api';

/**
 * Run similarity check (Steps 1-6)
 * Called when user clicks "Suggest" button
 * 
 * @param {Object} data - Form data
 * @param {string} data.item_type - 'Framework'|'Policy'|'SubPolicy'|'Compliance'
 * @param {Object} data.item_data - Form field values
 * @param {number} data.tenant_id - Tenant ID
 * @param {number} [data.parent_framework_id] - For Policy/SubPolicy/Compliance
 * @param {number} [data.parent_policy_id] - For SubPolicy/Compliance
 * @param {number} [data.parent_subpolicy_id] - For Compliance
 * @returns {Promise<Object>} Similarity check results
 */
export const checkSimilarity = async (data, options = {}) => {
  try {
    const response = await axios.post(`${API_URL}/similarity/check/`, data, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'Content-Type': 'application/json'
      },
      signal: options.signal
    });
    return response.data;
  } catch (error) {
    if (axios.isCancel?.(error) || error.code === 'ERR_CANCELED' || error.name === 'CanceledError') {
      const cancelled = new Error('Similarity check cancelled');
      cancelled.code = 'ERR_CANCELED';
      cancelled.name = 'CanceledError';
      throw cancelled;
    }
    console.error('Similarity check failed:', error);
    throw error;
  }
};

/**
 * Fetch similarity results for display
 * @param {number} checkId - Check ID from checkSimilarity response
 * @returns {Promise<Object>} Detailed results
 */
export const getSimilarityResult = async (checkId) => {
  try {
    const response = await axios.get(`${API_URL}/similarity/check/${checkId}/`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });
    return response.data;
  } catch (error) {
    console.error('Failed to fetch similarity results:', error);
    throw error;
  }
};

/**
 * Record user decision (Step 8 & 9)
 * @param {number} checkId - Check ID
 * @param {string} decision - 'CREATE_ANYWAY'|'USE_EXISTING'|'CANCEL'
 * @param {number} [selectedCandidateId] - If USE_EXISTING
 * @param {string} [reason] - User's reason
 * @returns {Promise<Object>} Response with step8_decision and step9_result
 */
export const recordUserDecision = async (checkId, decision, selectedCandidateId = null, reason = '') => {
  try {
    const response = await axios.post(
      `${API_URL}/similarity/check/${checkId}/decision/`,
      {
        decision,
        selected_candidate_id: selectedCandidateId,
        reason
      },
      {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        }
      }
    );
    return response.data; // Returns {success, step8_decision, step9_result}
  } catch (error) {
    console.error('Failed to record decision:', error);
    throw error;
  }
};

/**
 * Helper to format similarity score as percentage
 * @param {number} score - 0-1 score
 * @returns {string} Formatted percentage
 */
export const formatScore = (score) => {
  if (!score && score !== 0) return 'N/A';
  return `${(score * 100).toFixed(1)}%`;
};

/**
 * Get risk level color
 * @param {string} riskLevel - 'LOW'|'MEDIUM'|'HIGH'|'UNKNOWN'
 * @returns {string} Color code
 */
export const getRiskColor = (riskLevel) => {
  const colors = {
    'LOW': '#4CAF50',      // Green
    'MEDIUM': '#FF9800',   // Orange
    'HIGH': '#F44336',     // Red
    'UNKNOWN': '#9E9E9E'   // Gray
  };
  return colors[riskLevel] || colors['UNKNOWN'];
};

/**
 * Get status icon
 * @param {string} status - duplicate|highly_similar|related_but_different|different
 * @returns {string} Emoji/icon
 */
export const getStatusIcon = (status) => {
  const icons = {
    'duplicate': '⚠️',
    'highly_similar': '🔶',
    'related_but_different': 'ℹ️',
    'different': '✅'
  };
  return icons[status] || '❓';
};
