/**
 * Option A: background similarity on update — save only after review + confirm.
 */

import axios from 'axios';
import { getSimilarityResult, recordUserDecision } from '@/services/similarityService';

const API_URL = import.meta.env.VITE_API_URL || '/api';

function authHeaders() {
  const token = localStorage.getItem('access_token');
  return {
    Authorization: token ? `Bearer ${token}` : '',
    'Content-Type': 'application/json',
  };
}

export async function startAsyncUpdateSimilarity({ checks, pendingSave }) {
  const tenantId =
    parseInt(localStorage.getItem('tenant_id'), 10) ||
    parseInt(localStorage.getItem('tenantId'), 10) ||
    null;
  const response = await axios.post(
    `${API_URL}/similarity/async-update/`,
    { checks, pending_save: pendingSave, tenant_id: tenantId },
    { headers: authHeaders() }
  );
  return response.data;
}

export async function getAsyncUpdateStatus(masterCheckId) {
  const response = await axios.get(
    `${API_URL}/similarity/async-update/${masterCheckId}/status/`,
    { headers: authHeaders() }
  );
  return response.data;
}

export async function getPendingSavePayload(masterCheckId) {
  const response = await axios.get(
    `${API_URL}/similarity/async-update/${masterCheckId}/pending-save/`,
    { headers: authHeaders() }
  );
  return response.data;
}

export async function markPendingSaveExecuted(masterCheckId) {
  const response = await axios.post(
    `${API_URL}/similarity/async-update/${masterCheckId}/executed/`,
    {},
    { headers: authHeaders() }
  );
  return response.data;
}

export async function pollUntilReady(masterCheckId, { intervalMs = 2500, maxAttempts = 120 } = {}) {
  for (let i = 0; i < maxAttempts; i += 1) {
    const status = await getAsyncUpdateStatus(masterCheckId);
    if (status.background_status === 'READY') {
      return status;
    }
    if (status.background_status === 'FAILED') {
      throw new Error(status.error || 'Background similarity check failed');
    }
    await new Promise((r) => setTimeout(r, intervalMs));
  }
  throw new Error('Similarity check timed out. Check notifications later.');
}

export { getSimilarityResult, recordUserDecision };

export async function executePendingSave({ operation, entityPk, payload }, apiService) {
  if (operation === 'framework_version') {
    return apiService.post(`/api/frameworks/${entityPk}/create-version/`, payload);
  }
  if (operation === 'policy_version') {
    return apiService.post(`/api/policies/${entityPk}/create-version/`, payload);
  }
  if (operation === 'compliance_update') {
    const { originalComplianceId, editData, complianceStore: store } = payload;
    const cs = store || (await import('@/stores/compliance')).useComplianceStore();
    return cs.updateComplianceCompat(originalComplianceId, editData);
  }
  if (operation === 'tt_create_policy') {
    return apiService.post('/api/tailoring/create-policy/', payload);
  }
  if (operation === 'tt_create_framework') {
    return apiService.post('/api/tailoring/create-framework/', payload);
  }
  throw new Error(`Unknown pending save operation: ${operation}`);
}
