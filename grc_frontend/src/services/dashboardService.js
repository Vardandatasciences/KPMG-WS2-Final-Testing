import apiService from './apiService.js'

// In-memory cache for dashboard data (stale-while-revalidate pattern)
const _cache = {};
const CACHE_TTL_MS = 5 * 60 * 1000; // 5 minutes

function _cacheKey(endpoint, params) {
  return endpoint + '|' + JSON.stringify(params || {});
}

function _getCached(key) {
  const entry = _cache[key];
  if (!entry) return null;
  if (Date.now() - entry.ts > CACHE_TTL_MS) return null;
  return entry.data;
}

function _setCached(key, data) {
  _cache[key] = { data, ts: Date.now() };
}

async function _cachedGet(endpoint, params) {
  const key = _cacheKey(endpoint, params);
  const hit = _getCached(key);
  if (hit !== null) return hit;
  const data = await apiService.get(endpoint, params);
  _setCached(key, data);
  return data;
}

export default {
    // Expose cache helpers for stale-while-revalidate in components
    hasSummaryCache(params = {}) {
      return _getCached(_cacheKey('/api/policy-dashboard/', params)) !== null;
    },
    getSummaryCached(params = {}) {
      const data = _getCached(_cacheKey('/api/policy-dashboard/', params));
      if (!data) return null;
      return { ...data, policies: Array.isArray(data?.policies) ? data.policies : [] };
    },
    hasFrameworksCache() {
      return _getCached(_cacheKey('/api/frameworks/', { include_all_status: true })) !== null;
    },
    getFrameworksCached() {
      return _getCached(_cacheKey('/api/frameworks/', { include_all_status: true }));
    },

    async getDashboardSummary(params = {}) {
        const response = await _cachedGet('/api/policy-dashboard/', params);
        return {
            ...response,
            policies: Array.isArray(response?.policies) ? response.policies : []
        };
    },
    getPolicyAnalytics(params) {
        return _cachedGet('/api/policy-analytics/', params);
    },
    getPolicyStatusDistribution(params = {}) {
      return _cachedGet('/api/policy-status-distribution/', params);
    },
    getReviewerWorkload(params = {}) {
      return _cachedGet('/api/reviewer-workload/', params);
    },
    getRecentPolicyActivity(params = {}) {
      return _cachedGet('/api/recent-policy-activity/', params);
    },
    getAvgApprovalTime(params = {}) {
      return _cachedGet('/api/avg-policy-approval-time/', params);
    },
    getAllPolicies() {
        return _cachedGet('/api/policies/', undefined);
    },
    // Get all frameworks
    getAllFrameworks({ force = false } = {}) {
        if (force) {
            return apiService.get('/api/frameworks/', { include_all_status: true }, { skipCache: true });
        }
        return _cachedGet('/api/frameworks/', { include_all_status: true });
    },
    // New: Get policies by framework
    getPoliciesByFramework(frameworkId) {
        return _cachedGet(`/api/frameworks/${frameworkId}/policies/list/`, undefined);
    },
    // New: Get framework status distribution
    getFrameworkStatusDistribution(params = {}) {
        return _cachedGet('/api/framework-status-distribution/', params);
    },
    // Get recent policies (last 5 created)
    getRecentPolicies() {
        return _cachedGet('/api/policies/', { limit: 5, ordering: '-CreatedByDate' });
    }
};