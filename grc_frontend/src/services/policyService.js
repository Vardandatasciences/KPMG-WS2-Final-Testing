/**
 * Policy Service - Centralized Data Management
 *
 * This service handles:
 * 1. Prefetching and caching common policy datasets (frameworks, summaries, etc.)
 * 2. Providing cached data to policy-related components for instant loading
 * 3. Offering helpers to update or clear cached data when mutations occur
 */

import { axiosInstance, API_ENDPOINTS } from '@/config/api.js';
import { summarizeExplorerFromFrameworkRows } from '@/composables/usePolicyExplorerPinia.js';

/** Cookie-first auth: skip protected prefetch when shell flags are cleared (e.g. logout). */
export function isPolicyPrefetchAllowed() {
  if (typeof window !== 'undefined' && window.__grcLoggingOut) {
    return false;
  }
  const userId = sessionStorage.getItem('user_id') || localStorage.getItem('user_id');
  const loggedIn =
    (sessionStorage.getItem('is_logged_in') || localStorage.getItem('is_logged_in')) === 'true' ||
    (sessionStorage.getItem('isAuthenticated') || localStorage.getItem('isAuthenticated')) === 'true';
  return !!(userId && loggedIn);
}

function isAuthRelatedPrefetchError(error) {
  const status = error?.response?.status;
  return status === 401 || status === 403 || status === 400;
}

class PolicyService {
  constructor() {
    this.dataStore = {
      frameworksList: [],      // From FRAMEWORKS endpoint (lightweight list)
      policyFrameworks: [],    // From all-policies frameworks endpoint (detailed)
      explorerFrameworks: [],  // From framework explorer endpoint
      explorerSummary: null,
      lastFetchTime: null,
      isFetching: false,
      fetchError: null
    };
  }

  /**
   * Prefetch all major policy data sets
   */
  async fetchAllPolicyData() {
    if (!isPolicyPrefetchAllowed()) {
      console.log('[Policy Service] Skipping prefetch — user not authenticated');
      return this.dataStore;
    }

    if (this.dataStore.isFetching) {
      console.log('[Policy Service] Already fetching, skipping duplicate request');
      return this.dataStore;
    }

    this.dataStore.isFetching = true;
    console.log('[Policy Service] 🚀 Starting policy data prefetch...');

    try {
      await Promise.all([
        this.fetchFrameworksList(),
        this.fetchAllPoliciesFrameworks(),
        this.fetchFrameworkExplorerData()
      ]);

      this.dataStore.lastFetchTime = new Date();
      this.dataStore.fetchError = null;

      console.log('[Policy Service] ✅ Prefetch complete', {
        frameworksList: this.dataStore.frameworksList.length,
        policyFrameworks: this.dataStore.policyFrameworks.length,
        explorerFrameworks: this.dataStore.explorerFrameworks.length
      });

      return this.dataStore;
    } catch (error) {
      if (!isPolicyPrefetchAllowed() || isAuthRelatedPrefetchError(error)) {
        console.warn('[Policy Service] Prefetch skipped after auth loss:', error?.message || error);
        this.dataStore.fetchError = null;
        return this.dataStore;
      }
      console.error('[Policy Service] ❌ Prefetch failed:', error);
      this.dataStore.fetchError = error.message;
      throw error;
    } finally {
      this.dataStore.isFetching = false;
    }
  }

  /**
   * Fetch frameworks list (lightweight) from FRAMEWORKS endpoint
   */
  async fetchFrameworksList() {
    if (!isPolicyPrefetchAllowed()) {
      this.dataStore.frameworksList = [];
      return;
    }
    try {
      const response = await axiosInstance.get(API_ENDPOINTS.FRAMEWORKS, {
        timeout: 60000
      });

      if (Array.isArray(response.data)) {
        this.dataStore.frameworksList = response.data;
      } else if (Array.isArray(response.data?.frameworks)) {
        this.dataStore.frameworksList = response.data.frameworks;
      } else {
        this.dataStore.frameworksList = [];
      }

      console.log(`[Policy Service] Fetched ${this.dataStore.frameworksList.length} frameworks (list)`);
    } catch (error) {
      console.error('[Policy Service] Error fetching frameworks list:', error);
      this.dataStore.frameworksList = [];
      if (!isPolicyPrefetchAllowed() || isAuthRelatedPrefetchError(error)) return;
      throw error;
    }
  }

  /**
   * Fetch detailed frameworks used in All Policies view
   */
  async fetchAllPoliciesFrameworks() {
    if (!isPolicyPrefetchAllowed()) {
      this.dataStore.policyFrameworks = [];
      return;
    }
    try {
      const response = await axiosInstance.get(API_ENDPOINTS.POLICY_ALL_POLICIES_FRAMEWORKS, {
        timeout: 60000
      });

      if (Array.isArray(response.data)) {
        this.dataStore.policyFrameworks = response.data;
      } else if (Array.isArray(response.data?.frameworks)) {
        this.dataStore.policyFrameworks = response.data.frameworks;
      } else {
        this.dataStore.policyFrameworks = [];
      }

      console.log(`[Policy Service] Fetched ${this.dataStore.policyFrameworks.length} policy frameworks`);
    } catch (error) {
      console.error('[Policy Service] Error fetching policy frameworks:', error);
      this.dataStore.policyFrameworks = [];
      if (!isPolicyPrefetchAllowed() || isAuthRelatedPrefetchError(error)) return;
      throw error;
    }
  }

  /**
   * Fetch framework explorer data (frameworks + summary)
   * @param {object} params Optional query parameters (for filters)
   */
  async fetchFrameworkExplorerData(params = {}) {
    if (!isPolicyPrefetchAllowed()) {
      this.dataStore.explorerFrameworks = [];
      this.dataStore.explorerSummary = null;
      return;
    }
    try {
      const response = await axiosInstance.get(API_ENDPOINTS.FRAMEWORK_EXPLORER, {
        params,
        timeout: 60000
      });

      if (response.data) {
        this.dataStore.explorerFrameworks = response.data.frameworks || [];
        this.dataStore.explorerSummary = response.data.summary || null;
      } else {
        this.dataStore.explorerFrameworks = [];
        this.dataStore.explorerSummary = null;
      }

      console.log(`[Policy Service] Fetched ${this.dataStore.explorerFrameworks.length} explorer frameworks`);
    } catch (error) {
      console.error('[Policy Service] Error fetching framework explorer data:', error);
      this.dataStore.explorerFrameworks = [];
      this.dataStore.explorerSummary = null;
      if (!isPolicyPrefetchAllowed() || isAuthRelatedPrefetchError(error)) return;
      throw error;
    }
  }

  // ===== Getters =====

  getFrameworksList() {
    return this.dataStore.frameworksList;
  }

  getAllPoliciesFrameworks() {
    return this.dataStore.policyFrameworks;
  }

  getFrameworkExplorerFrameworks() {
    return this.dataStore.explorerFrameworks;
  }

  getFrameworkExplorerSummary() {
    return this.dataStore.explorerSummary;
  }

  // ===== Setters =====

  setFrameworksList(frameworks = []) {
    this.dataStore.frameworksList = frameworks;
    this.dataStore.lastFetchTime = new Date();
  }

  setAllPoliciesFrameworks(frameworks = []) {
    this.dataStore.policyFrameworks = frameworks;
    this.dataStore.lastFetchTime = new Date();
  }

  setFrameworkExplorerData(frameworks = [], summary = null) {
    this.dataStore.explorerFrameworks = frameworks;
    this.dataStore.explorerSummary = summary;
    this.dataStore.lastFetchTime = new Date();
  }

  /**
   * Insert or replace one explorer row after create/version mutations (instant Framework Explorer paint).
   */
  mergeExplorerFrameworkRow(explorerRow) {
    const id = explorerRow?.id ?? explorerRow?.FrameworkId;
    if (id == null) return;
    const prev = Array.isArray(this.dataStore.explorerFrameworks)
      ? this.dataStore.explorerFrameworks
      : [];
    const filtered = prev.filter((f) => String(f.id ?? f.FrameworkId) !== String(id));
    const row = { ...explorerRow, id: Number(id) || id };
    const merged = [row, ...filtered];
    this.dataStore.explorerFrameworks = merged;
    this.dataStore.explorerSummary = summarizeExplorerFromFrameworkRows(merged);
    this.dataStore.lastFetchTime = new Date();

    const fl = Array.isArray(this.dataStore.frameworksList) ? this.dataStore.frameworksList : [];
    const flFiltered = fl.filter((f) => String(f.FrameworkId ?? f.id) !== String(id));
    flFiltered.push({
      FrameworkId: id,
      FrameworkName: row.name ?? row.FrameworkName ?? '',
      Category: row.category ?? '',
      Identifier: row.identifier ?? row.Identifier,
    });
    this.dataStore.frameworksList = flFiltered;
  }

  // ===== Cache Checks =====

  hasFrameworksListCache() {
    return Array.isArray(this.dataStore.frameworksList) && this.dataStore.frameworksList.length > 0;
  }

  hasAllPoliciesFrameworksCache() {
    return Array.isArray(this.dataStore.policyFrameworks) && this.dataStore.policyFrameworks.length > 0;
  }

  hasFrameworkExplorerCache() {
    return Array.isArray(this.dataStore.explorerFrameworks) && this.dataStore.explorerFrameworks.length > 0;
  }

  // ===== Maintenance Helpers =====

  clearCache() {
    this.dataStore.frameworksList = [];
    this.dataStore.policyFrameworks = [];
    this.dataStore.explorerFrameworks = [];
    this.dataStore.explorerSummary = null;
    this.dataStore.lastFetchTime = null;
    this.dataStore.fetchError = null;
    this.dataStore.isFetching = false;
    console.log('[Policy Service] Cache cleared');
  }

  /** Cancel in-flight prefetch dedupe (call on logout). */
  resetOnLogout() {
    this.clearCache();
    if (typeof window !== 'undefined') {
      delete window.policyDataFetchPromise;
      try {
        sessionStorage.removeItem('api_cache_frameworks_list_v1');
      } catch (_) { /* ignore */ }
    }
  }

  getCacheStats() {
    return {
      frameworksListCount: this.dataStore.frameworksList.length,
      policyFrameworksCount: this.dataStore.policyFrameworks.length,
      explorerFrameworksCount: this.dataStore.explorerFrameworks.length,
      hasSummary: !!this.dataStore.explorerSummary,
      lastFetchTime: this.dataStore.lastFetchTime,
      isFetching: this.dataStore.isFetching,
      hasError: !!this.dataStore.fetchError
    };
  }
}

const policyDataService = new PolicyService();
export default policyDataService;


