import apiService from '@/services/apiService';
import { API_ENDPOINTS } from '@/config/api.js';

class AIRecommendationService {
  async getRecommendations(taskData) {
    try {
      console.log('AI Service: Getting recommendations for:', taskData);
      
      // First update the audit status to 'Under review' using centralized apiService
      const data = await apiService.post(API_ENDPOINTS.AI_RECOMMENDATIONS, {
        review_id: taskData.reviewId || `audit_${Date.now()}`,
        review_type: 'audit',
        title: taskData.title || taskData.auditTitle,
        description: taskData.description || taskData.auditDescription,
        domain: taskData.domain || 'General',
        severity: taskData.severity || 'Medium',
        department_id: taskData.departmentId || 1,
        max_recommendations: 5
      });

      console.log('AI Service: Response received:', data);
      
      return {
        success: true,
        data: data
      };
    } catch (error) {
      console.error('AI Recommendation Error:', error);
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to get AI recommendations'
      };
    }
  }

  async getRiskRecommendations(taskData) {
    try {
      const data = await apiService.post(API_ENDPOINTS.AI_RECOMMENDATIONS, {
        review_id: taskData.reviewId || `risk_${Date.now()}`,
        review_type: 'risk',
        title: taskData.title || taskData.riskTitle,
        description: taskData.description || taskData.riskDescription,
        domain: taskData.domain || 'Risk Management',
        severity: taskData.severity || 'Medium',
        department_id: taskData.departmentId || 1,
        max_recommendations: 5
      });

      return {
        success: true,
        data: data
      };
    } catch (error) {
      console.error('AI Risk Recommendation Error:', error);
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to get AI risk recommendations'
      };
    }
  }

  async getPolicyRecommendations(taskData) {
    try {
      const data = await apiService.post(API_ENDPOINTS.AI_RECOMMENDATIONS, {
        review_id: taskData.reviewId || `policy_${Date.now()}`,
        review_type: 'policy',
        title: taskData.title || taskData.policyTitle,
        description: taskData.description || taskData.policyDescription,
        domain: taskData.domain || 'Policy Management',
        severity: taskData.severity || 'Medium',
        department_id: taskData.departmentId || 1,
        max_recommendations: 5
      });

      return {
        success: true,
        data: data
      };
    } catch (error) {
      console.error('AI Policy Recommendation Error:', error);
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to get AI policy recommendations'
      };
    }
  }
}

export default new AIRecommendationService();
