import apiService from './apiService.js'

export default {
    async getDashboardSummary(params = {}) {
        try {
            // apiService handles query params automatically
            const response = await apiService.get('/policy-dashboard/', params);
            return {
                data: {
                    ...response,
                    policies: Array.isArray(response.policies) ? response.policies : []
                }
            };
        } catch (error) {
            console.error('Error fetching dashboard data:', error);
            return {
                data: {
                    total_policies: 0,
                    active_policies: 0,
                    inactive_policies: 0,
                    total_subpolicies: 0,
                    active_subpolicies: 0,
                    approval_rate: 0,
                    policies: []
                }
            };
        }
    },
    getPolicyAnalytics(params) {
        return apiService.get('/policy-analytics/', params);
    },
    getPolicyStatusDistribution(params = {}) {
      return apiService.get('/policy-status-distribution/', params);
    },
    getReviewerWorkload(params = {}) {
      return apiService.get('/reviewer-workload/', params);
    },
    getRecentPolicyActivity(params = {}) {
      return apiService.get('/recent-policy-activity/', params);
    },
    getAvgApprovalTime(params = {}) {
      return apiService.get('/avg-policy-approval-time/', params);
    },
    getAllPolicies() {
        return apiService.get('/policies/');
    },
    // Get all frameworks
    getAllFrameworks() {
        return apiService.get('/frameworks/', { include_all_status: true });
    },
    // New: Get policies by framework
    getPoliciesByFramework(frameworkId) {
        return apiService.get(`/frameworks/${frameworkId}/policies/list/`);
    },
    // New: Get framework status distribution
    getFrameworkStatusDistribution(params = {}) {
        return apiService.get('/framework-status-distribution/', params);
    },
    // Get recent policies (last 5 created)
    getRecentPolicies() {
        return apiService.get('/policies/', { limit: 5, ordering: '-CreatedByDate' });
    }
};