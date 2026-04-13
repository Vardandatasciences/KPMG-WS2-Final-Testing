import apiService from './apiService.js'

export default {
    async getDashboardSummary(params = {}) {
        const response = await apiService.get('/api/policy-dashboard/', params);
        return {
            ...response,
            policies: Array.isArray(response?.policies) ? response.policies : []
        };
    },
    getPolicyAnalytics(params) {
        return apiService.get('/api/policy-analytics/', params);
    },
    getPolicyStatusDistribution(params = {}) {
      return apiService.get('/api/policy-status-distribution/', params);
    },
    getReviewerWorkload(params = {}) {
      return apiService.get('/api/reviewer-workload/', params);
    },
    getRecentPolicyActivity(params = {}) {
      return apiService.get('/api/recent-policy-activity/', params);
    },
    getAvgApprovalTime(params = {}) {
      return apiService.get('/api/avg-policy-approval-time/', params);
    },
    getAllPolicies() {
        return apiService.get('/api/policies/');
    },
    // Get all frameworks
    getAllFrameworks() {
        return apiService.get('/api/frameworks/', { include_all_status: true });
    },
    // New: Get policies by framework
    getPoliciesByFramework(frameworkId) {
        return apiService.get(`/api/frameworks/${frameworkId}/policies/list/`);
    },
    // New: Get framework status distribution
    getFrameworkStatusDistribution(params = {}) {
        return apiService.get('/api/framework-status-distribution/', params);
    },
    // Get recent policies (last 5 created)
    getRecentPolicies() {
        return apiService.get('/api/policies/', { limit: 5, ordering: '-CreatedByDate' });
    }
};