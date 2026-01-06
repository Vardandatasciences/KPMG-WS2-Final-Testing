/**
 * API service for connecting frontend to backend
 */
import { getTprmApiBaseUrl, getApiOrigin } from '@/utils/backendEnv'

// Use environment-aware URL resolution - defaults to production
const TPRM_BASE = getTprmApiBaseUrl();
const API_BASE_URL = TPRM_BASE;
const RFP_API_URL = `${TPRM_BASE}/rfp`;
const SLA_API_URL = `${TPRM_BASE}/slas`;
const AUDITS_API_URL = `${TPRM_BASE}/audits`;
const NOTIFICATIONS_API_URL = `${TPRM_BASE}/notifications`;
const BCPDRP_API_URL = `${TPRM_BASE}/bcpdrp`;
const RISK_ANALYSIS_API_URL = `${TPRM_BASE}/risk-analysis`;

class APIService {
  constructor() {
    this.baseURL = API_BASE_URL;
    this.rfpURL = RFP_API_URL;
    this.slaURL = SLA_API_URL;
    this.auditsURL = AUDITS_API_URL;
    this.notificationsURL = NOTIFICATIONS_API_URL;
    this.bcpdrpURL = BCPDRP_API_URL;
    this.riskAnalysisURL = RISK_ANALYSIS_API_URL;
  }

  // Helper to get token from any of the storage keys (compatible with GRC auth)
  getStoredToken() {
    const keys = ['access_token', 'session_token', 'token', 'jwt_token'];
    for (const key of keys) {
      const val = localStorage.getItem(key);
      if (val) return val;
    }
    return null;
  }

  // Helper to refresh token if needed
  async refreshTokenIfNeeded() {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) {
        return false;
      }
      
      const apiOrigin = getApiOrigin() || 'https://grc-tprm.vardaands.com'
      const refreshResponse = await fetch(`${apiOrigin}/api/jwt/refresh/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ refresh_token: refreshToken })
      });
      
      if (refreshResponse.ok) {
        const refreshData = await refreshResponse.json();
        if (refreshData.status === 'success') {
          localStorage.setItem('access_token', refreshData.access_token);
          if (refreshData.refresh_token) {
            localStorage.setItem('refresh_token', refreshData.refresh_token);
          }
          return true;
        }
      }
      return false;
    } catch (error) {
      return false;
    }
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    let token = this.getStoredToken();
    
    // If no token, try to refresh
    if (!token) {
      await this.refreshTokenIfNeeded();
      token = this.getStoredToken();
    }
    
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` }),
        ...options.headers,
      },
      ...options,
    };

    try {
      let response = await fetch(url, config);
      
      // Handle 401 errors - try to refresh token and retry
      if (response.status === 401 && !options._retry) {
        console.log('🔄 [APIService] 401 error detected, attempting token refresh...');
        const refreshSuccess = await this.refreshTokenIfNeeded();
        
        if (refreshSuccess) {
          // Retry with new token
          const newToken = this.getStoredToken();
          if (newToken) {
            config.headers['Authorization'] = `Bearer ${newToken}`;
            config._retry = true;
            response = await fetch(url, config);
          }
        }
      }
      
      if (!response.ok) {
        // 401 = Unauthorized (invalid/missing token) → don't redirect, just throw error
        if (response.status === 401) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        // 403 = Forbidden (valid token but no permission) → throw error with response for usePermissions to handle
        if (response.status === 403) {
          const errorData = await response.json().catch(() => ({}));
          const error = new Error(errorData.error || errorData.message || 'Permission denied');
          error.response = {
            status: 403,
            data: errorData
          };
          throw error;
        }
        
        // For 500 errors, try to get more details
        if (response.status === 500) {
          const errorData = await response.json().catch(() => ({}));
          const errorMessage = errorData.error || errorData.message || errorData.detail || 'Internal server error';
          throw new Error(`HTTP error! status: ${response.status} - ${errorMessage}`);
        }
        
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  async slaRequest(endpoint, options = {}) {
    const url = `${this.slaURL}${endpoint}`;
    const token = this.getStoredToken();
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` }),
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        // 401 = Unauthorized (invalid/missing token) → redirect to login
        if (response.status === 401) {
          localStorage.removeItem('session_token');
          localStorage.removeItem('current_user');
          if (window.location.pathname !== '/login') {
            window.location.href = '/login';
          }
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        // 403 = Forbidden (valid token but no permission) → throw error with response for usePermissions to handle
        if (response.status === 403) {
          const errorData = await response.json().catch(() => ({}));
          const error = new Error(errorData.error || errorData.message || 'Permission denied');
          error.response = {
            status: 403,
            data: errorData
          };
          throw error;
        }
        
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('SLA API request failed:', error);
      throw error;
    }
  }

  async auditsRequest(endpoint, options = {}) {
    const { allow404 = false, ...fetchOptions } = options;
    const url = `${this.auditsURL}${endpoint}`;
    const token = this.getStoredToken();
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` }),
        ...fetchOptions.headers,
      },
      ...fetchOptions,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        if (allow404 && response.status === 404) {
          // Gracefully handle expected missing resources (e.g., inactive SLAs)
          return null;
        }
        // 401 = Unauthorized (invalid/missing token) → redirect to login
        if (response.status === 401) {
          localStorage.removeItem('session_token');
          localStorage.removeItem('current_user');
          if (window.location.pathname !== '/login') {
            window.location.href = '/login';
          }
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        // 403 = Forbidden (valid token but no permission) → throw error with response for usePermissions to handle
        if (response.status === 403) {
          const errorData = await response.json().catch(() => ({}));
          const error = new Error(errorData.error || errorData.message || 'Permission denied');
          error.response = {
            status: 403,
            data: errorData
          };
          throw error;
        }
        
        const errorText = await response.text();
        console.error(`HTTP error! status: ${response.status}`, errorText);
        throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Audits API request failed:', error);
      throw error;
    }
  }

  async notificationsRequest(endpoint, options = {}) {
    const url = `${this.notificationsURL}${endpoint}`;
    const token = this.getStoredToken();
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` }),
        ...options.headers,
      },
      credentials: 'include', // Include cookies for CORS
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        // 401 = Unauthorized (invalid/missing token) → redirect to login
        if (response.status === 401) {
          localStorage.removeItem('session_token');
          localStorage.removeItem('current_user');
          if (window.location.pathname !== '/login') {
            window.location.href = '/login';
          }
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        // 403 = Forbidden (valid token but no permission) → throw error with response for usePermissions to handle
        if (response.status === 403) {
          const errorData = await response.json().catch(() => ({}));
          const error = new Error(errorData.error || errorData.message || 'Permission denied');
          error.response = {
            status: 403,
            data: errorData
          };
          throw error;
        }
        
        // 404 = Not Found - endpoint doesn't exist, return empty/default response
        if (response.status === 404) {
          console.warn(`Notifications endpoint not found: ${url}, returning empty response`);
          return { total_unread: 0, notifications: [] };
        }
        
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      // Handle network errors gracefully (CORS, connection refused, etc.)
      if (error.message && (error.message.includes('Failed to fetch') || 
                            error.message.includes('NetworkError') ||
                            error.message.includes('ERR_CONNECTION_REFUSED') ||
                            error.name === 'TypeError')) {
        console.warn('Notifications API request failed (network error):', error.message);
        // Return empty response instead of throwing to prevent app breakage
        return { total_unread: 0, notifications: [] };
      }
      
      console.error('Notifications API request failed:', error);
      throw error;
    }
  }

  // Vendor endpoints
  async getVendors() {
    const response = await this.slaRequest('/vendors/');
    return response.results || response;
  }

  async getVendor(id) {
    return this.slaRequest(`/vendors/${id}/`);
  }

  async createVendor(data) {
    return this.slaRequest('/vendors/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateVendor(id, data) {
    return this.slaRequest(`/vendors/${id}/`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteVendor(id) {
    return this.slaRequest(`/vendors/${id}/`, {
      method: 'DELETE',
    });
  }

  // Contract endpoints
  async getContracts() {
    const response = await this.slaRequest('/contracts/');
    return response.results || response;
  }

  async getContract(id) {
    return this.slaRequest(`/contracts/${id}/`);
  }

  async createContract(data) {
    return this.slaRequest('/contracts/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateContract(id, data) {
    return this.slaRequest(`/contracts/${id}/`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteContract(id) {
    return this.slaRequest(`/contracts/${id}/`, {
      method: 'DELETE',
    });
  }

  // SLA endpoints
  async getSLAs() {
    const response = await this.slaRequest('/');
    return response.results || response;
  }

  async getSLA(id) {
    return this.slaRequest(`/${id}/`);
  }

  async getSLADetail(id) {
    return this.slaRequest(`/${id}/`);
  }

  async createSLA(data) {
    return this.slaRequest('/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateSLA(id, data) {
    return this.slaRequest(`/${id}/`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteSLA(id) {
    return this.slaRequest(`/${id}/`, {
      method: 'DELETE',
    });
  }

  // Helper function to build SLA update data with proper vendor_id and contract_id
  _buildSLAUpdateData(currentSLA, updates = {}) {
    return {
      sla_name: currentSLA.sla_name,
      sla_type: currentSLA.sla_type,
      effective_date: currentSLA.effective_date,
      expiry_date: currentSLA.expiry_date,
      status: currentSLA.status,
      business_service_impacted: currentSLA.business_service_impacted,
      reporting_frequency: currentSLA.reporting_frequency,
      baseline_period: currentSLA.baseline_period,
      improvement_targets: currentSLA.improvement_targets,
      penalty_threshold: currentSLA.penalty_threshold,
      credit_threshold: currentSLA.credit_threshold,
      measurement_methodology: currentSLA.measurement_methodology,
      exclusions: currentSLA.exclusions,
      force_majeure_clauses: currentSLA.force_majeure_clauses,
      compliance_framework: currentSLA.compliance_framework,
      audit_requirements: currentSLA.audit_requirements,
      document_versioning: currentSLA.document_versioning,
      priority: currentSLA.priority,
      approval_status: currentSLA.approval_status,
      compliance_score: currentSLA.compliance_score,
      vendor_id: currentSLA.vendor?.vendor_id || currentSLA.vendor_id,
      contract_id: currentSLA.contract?.contract_id || currentSLA.contract_id,
      ...updates // Override with any specific updates
    };
  }

  async extendSLA(id, data) {
    // Get current SLA data first
    const currentSLA = await this.getSLA(id);
    
    // Update the SLA with new expiry date and status
    const updateData = this._buildSLAUpdateData(currentSLA, {
      expiry_date: data.newExpiryDate,
      status: 'ACTIVE' // Keep it active when extending
    });
    
    console.log('Extending SLA with data:', updateData);
    
    return this.slaRequest(`/${id}/`, {
      method: 'PUT',
      body: JSON.stringify(updateData),
    });
  }

  async stopSLA(id, data) {
    // Get current SLA data first
    const currentSLA = await this.getSLA(id);
    
    // Update the SLA status to inactive
    const updateData = this._buildSLAUpdateData(currentSLA, {
      status: 'INACTIVE'
    });
    
    console.log('Stopping SLA with data:', updateData);
    
    return this.slaRequest(`/${id}/`, {
      method: 'PUT',
      body: JSON.stringify(updateData),
    });
  }

  async submitSLA(id) {
    return this.slaRequest(`/${id}/submit/`, {
      method: 'POST',
    });
  }

  async approveSLA(id, action = 'approve', comments = '') {
    return this.slaRequest(`/${id}/approve/`, {
      method: 'POST',
      body: JSON.stringify({ action, comments }),
    });
  }

  // Analytics endpoints
  async getDashboardStats() {
    return this.slaRequest('/dashboard-stats/');
  }

  async getComplianceSummary() {
    return this.slaRequest('/compliance-summary/');
  }

  async getVendorSummary() {
    return this.slaRequest('/vendor-summary/');
  }

  async getTrends() {
    return this.slaRequest('/trends/');
  }

  async getPerformanceDashboard(params = {}) {
    const queryParams = new URLSearchParams(params).toString();
    const endpoint = queryParams ? `/performance-dashboard/?${queryParams}` : '/performance-dashboard/';
    return this.slaRequest(endpoint);
  }
  
  // Get comprehensive KPI data
  async getSLAKPIData() {
    return this.slaRequest('/kpi-data/');
  }
  
  // SLA Metrics endpoints
  async getMetrics() {
    return this.slaRequest('/metrics/');
  }

  async getMetric(id) {
    return this.slaRequest(`/metrics/${id}/`);
  }

  async createMetric(data) {
    return this.slaRequest('/metrics/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateMetric(id, data) {
    return this.slaRequest(`/metrics/${id}/`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteMetric(id) {
    return this.slaRequest(`/metrics/${id}/`, {
      method: 'DELETE',
    });
  }

  // SLA Documents endpoints
  async getDocuments() {
    const response = await this.slaRequest('/documents/');
    return response.results || response;
  }

  async getDocument(id) {
    return this.slaRequest(`/documents/${id}/`);
  }

  async createDocument(data) {
    return this.slaRequest('/documents/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateDocument(id, data) {
    return this.slaRequest(`/documents/${id}/`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteDocument(id) {
    return this.slaRequest(`/documents/${id}/`, {
      method: 'DELETE',
    });
  }

  // Compliance endpoints
  async getComplianceRecords() {
    const response = await this.slaRequest('/compliance/');
    return response.results || response;
  }

  async getComplianceRecord(id) {
    return this.slaRequest(`/compliance/${id}/`);
  }

  async createComplianceRecord(data) {
    return this.slaRequest('/compliance/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateComplianceRecord(id, data) {
    return this.slaRequest(`/compliance/${id}/`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteComplianceRecord(id) {
    return this.slaRequest(`/compliance/${id}/`, {
      method: 'DELETE',
    });
  }

  // Violations endpoints
  async getViolations() {
    const response = await this.slaRequest('/violations/');
    return response.results || response;
  }

  async getViolation(id) {
    return this.slaRequest(`/violations/${id}/`);
  }

  async createViolation(data) {
    return this.slaRequest('/violations/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateViolation(id, data) {
    return this.slaRequest(`/violations/${id}/`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteViolation(id) {
    return this.slaRequest(`/violations/${id}/`, {
      method: 'DELETE',
    });
  }

  // Reviews endpoints
  async getReviews() {
    const response = await this.slaRequest('/reviews/');
    return response.results || response;
  }

  async getReview(id) {
    return this.slaRequest(`/reviews/${id}/`);
  }

  async createReview(data) {
    return this.slaRequest('/reviews/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateReview(id, data) {
    return this.slaRequest(`/reviews/${id}/`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteReview(id) {
    return this.slaRequest(`/reviews/${id}/`, {
      method: 'DELETE',
    });
  }

  // Notifications endpoints
  async getNotifications(filters = {}) {
    const queryParams = new URLSearchParams();
    
    // Add filters to query params
    Object.keys(filters).forEach(key => {
      if (filters[key] !== undefined && filters[key] !== null) {
        if (Array.isArray(filters[key])) {
          filters[key].forEach(item => queryParams.append(key, item));
        } else {
          queryParams.append(key, filters[key]);
        }
      }
    });
    
    const endpoint = queryParams.toString() ? `/?${queryParams.toString()}` : '/';
    const response = await this.notificationsRequest(endpoint);
    
    // Return the full response object (which may contain pagination metadata)
    // The caller can check for response.results or treat it as an array
    return response;
  }
  
  // Helper method to get all notifications across all pages
  async getAllNotifications(filters = {}) {
    let allNotifications = [];
    let page = 1;
    let hasMore = true;
    const pageSize = 100; // Fetch 100 per page
    
    while (hasMore) {
      const pageFilters = {
        ...filters,
        page: page,
        page_size: pageSize
      };
      
      const queryParams = new URLSearchParams();
      Object.keys(pageFilters).forEach(key => {
        if (pageFilters[key] !== undefined && pageFilters[key] !== null) {
          if (Array.isArray(pageFilters[key])) {
            pageFilters[key].forEach(item => queryParams.append(key, item));
          } else {
            queryParams.append(key, pageFilters[key]);
          }
        }
      });
      
      const endpoint = queryParams.toString() ? `/?${queryParams.toString()}` : '/';
      const response = await this.notificationsRequest(endpoint);
      
      if (Array.isArray(response)) {
        // Direct array response (no pagination)
        allNotifications = [...allNotifications, ...response];
        hasMore = false;
      } else if (response.results && Array.isArray(response.results)) {
        // Paginated response
        allNotifications = [...allNotifications, ...response.results];
        
        // Check if there's a next page
        hasMore = response.next !== null && response.next !== undefined && response.results.length === pageSize;
        
        // If we have a count and haven't reached it yet
        if (response.count !== undefined && allNotifications.length < response.count && response.results.length > 0) {
          hasMore = true;
        } else if (response.results.length < pageSize) {
          // If we got fewer results than page size, we're done
          hasMore = false;
        }
        
        page++;
      } else {
        hasMore = false;
      }
      
      // Safety limit
      if (page > 100) {
        console.warn('Reached safety limit of 100 pages');
        hasMore = false;
      }
    }
    
    return allNotifications;
  }

  async getNotification(id) {
    return this.notificationsRequest(`/${id}/`);
  }

  async createNotification(data) {
    return this.notificationsRequest('/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateNotification(id, data) {
    return this.notificationsRequest(`/${id}/`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteNotification(id) {
    return this.notificationsRequest(`/${id}/`, {
      method: 'DELETE',
    });
  }

  async markNotificationAsRead(id) {
    return this.notificationsRequest(`/${id}/mark_as_read/`, {
      method: 'POST',
    });
  }

  async dismissNotification(id) {
    return this.notificationsRequest(`/${id}/dismiss/`, {
      method: 'DELETE',
    });
  }

  async getNotificationStats() {
    return this.notificationsRequest('/stats/');
  }

  // Frameworks endpoints
  async getFrameworks() {
    const response = await this.request('/compliance/frameworks/');
    return response.results || response;
  }

  async getFramework(id) {
    return this.request(`/compliance/frameworks/${id}/`);
  }

  async createFramework(data) {
    return this.request('/compliance/frameworks/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateFramework(id, data) {
    return this.request(`/compliance/frameworks/${id}/`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteFramework(id) {
    return this.request(`/compliance/frameworks/${id}/`, {
      method: 'DELETE',
    });
  }

  // Compliance Mappings endpoints
  async getComplianceMappings() {
    const response = await this.request('/compliance/compliance-mappings/');
    return response.results || response;
  }

  async getComplianceMapping(id) {
    return this.request(`/compliance/compliance-mappings/${id}/`);
  }

  async createComplianceMapping(data) {
    return this.request('/compliance/compliance-mappings/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateComplianceMapping(id, data) {
    return this.request(`/compliance/compliance-mappings/${id}/`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteComplianceMapping(id) {
    return this.request(`/compliance/compliance-mappings/${id}/`, {
      method: 'DELETE',
    });
  }

  async getComplianceMappingsBySLA(slaId) {
    return this.request(`/compliance/compliance-mappings/by_sla/?sla_id=${slaId}`);
  }

  async getComplianceMappingsByFramework(frameworkId) {
    return this.request(`/compliance/compliance-mappings/by_framework/?framework_id=${frameworkId}`);
  }

  async getComplianceMappingSummary() {
    return this.request('/compliance/compliance-mappings/summary/');
  }

  // Audit endpoints
  async getAudits(filters = {}) {
    const queryParams = new URLSearchParams();
    
    // Add filters to query params
    Object.keys(filters).forEach(key => {
      if (filters[key] !== undefined && filters[key] !== null) {
        if (Array.isArray(filters[key])) {
          filters[key].forEach(item => queryParams.append(key, item));
        } else {
          queryParams.append(key, filters[key]);
        }
      }
    });
    
    const endpoint = queryParams.toString() ? `/?${queryParams.toString()}` : '/';
    const response = await this.auditsRequest(endpoint);
    return response.results || response;
  }

  async getAudit(id) {
    return this.auditsRequest(`/${id}/`);
  }

  async createAudit(data) {
    return this.auditsRequest('/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateAudit(id, data) {
    return this.auditsRequest(`/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  async deleteAudit(id) {
    return this.auditsRequest(`/${id}/`, {
      method: 'DELETE',
    });
  }

  // Audit Questions endpoints
  async getAuditQuestions(filters = {}) {
    const queryParams = new URLSearchParams();
    
    Object.keys(filters).forEach(key => {
      if (filters[key] !== undefined && filters[key] !== null) {
        queryParams.append(key, filters[key]);
      }
    });
    
    const endpoint = queryParams.toString() ? `/questions/?${queryParams.toString()}` : '/questions/';
    const response = await this.auditsRequest(endpoint);
    return response.results || response;
  }

  async getAuditQuestion(id) {
    return this.auditsRequest(`/questions/${id}/`);
  }

  async createAuditQuestion(data) {
    return this.auditsRequest('/questions/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateAuditQuestion(id, data) {
    return this.auditsRequest(`/questions/${id}/`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteAuditQuestion(id) {
    return this.auditsRequest(`/questions/${id}/`, {
      method: 'DELETE',
    });
  }

  // Audit Responses endpoints
  async getAuditResponses(filters = {}) {
    const queryParams = new URLSearchParams();
    
    Object.keys(filters).forEach(key => {
      if (filters[key] !== undefined && filters[key] !== null) {
        queryParams.append(key, filters[key]);
      }
    });
    
    const endpoint = queryParams.toString() ? `/responses/?${queryParams.toString()}` : '/responses/';
    const response = await this.auditsRequest(endpoint);
    return response.results || response;
  }

  async getAuditResponse(id) {
    return this.auditsRequest(`/responses/${id}/`);
  }

  async createAuditResponse(data) {
    return this.auditsRequest('/responses/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateAuditResponse(id, data) {
    return this.auditsRequest(`/responses/${id}/`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteAuditResponse(id) {
    return this.auditsRequest(`/responses/${id}/`, {
      method: 'DELETE',
    });
  }

  // Audit utility endpoints
  async getAuditDashboardStats() {
    return this.auditsRequest('/dashboard/stats/');
  }

  async getAvailableSLAs() {
    return this.auditsRequest('/available-slas/?user_id=1');
  }

  async getSLAMetrics(slaId) {
    const metricsData = await this.auditsRequest(`/sla-metrics/${slaId}/?user_id=1`, {
      allow404: true
    });
    // Return a consistent payload shape even when the SLA is missing/inactive
    return metricsData || { sla: { sla_id: slaId }, metrics: [] };
  }

  async uploadAuditEvidenceDocument(file, metadata = {}) {
    if (!file) {
      throw new Error('No file provided for upload');
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('user_id', metadata.userId ?? '1');

    if (metadata.customFileName) {
      formData.append('custom_file_name', metadata.customFileName);
    }
    if (metadata.auditId) {
      formData.append('audit_id', metadata.auditId);
    }
    if (metadata.metricId) {
      formData.append('metric_id', metadata.metricId);
    }
    if (metadata.metricName) {
      formData.append('metric_name', metadata.metricName);
    }
    // Tag uploads so they can be filtered on the backend
    formData.append('platform', 'audit-execution');

    const token = this.getStoredToken();
    const response = await fetch(`${this.rfpURL}/s3/upload/`, {
      method: 'POST',
      headers: {
        ...(token && { 'Authorization': `Bearer ${token}` })
      },
      body: formData
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Evidence upload failed (${response.status}): ${errorText}`);
    }

    return await response.json();
  }

  async getS3File(documentId) {
    if (!documentId) {
      throw new Error('Missing document identifier');
    }

    const token = this.getStoredToken();
    const response = await fetch(`${this.rfpURL}/s3-files/${documentId}/`, {
      headers: {
        ...(token && { 'Authorization': `Bearer ${token}` })
      }
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Failed to fetch S3 file (${response.status}): ${errorText}`);
    }

    return await response.json();
  }

  async getAvailableUsers() {
    return this.auditsRequest('/available-users/');
  }

  // Static questionnaires
  async getStaticQuestionnaires(params = {}) {
    const queryParams = new URLSearchParams(params);
    const endpoint = queryParams.toString() ? `/questionnaires/?${queryParams.toString()}` : '/questionnaires/';
    return this.auditsRequest(endpoint);
  }

  async getQuestionnairesByMetric(metricName) {
    return this.auditsRequest(`/questionnaires/?metric_name=${metricName}`);
  }
  
  // Get all questionnaires without pagination
  async getAllStaticQuestionnaires() {
    return this.auditsRequest('/questionnaires/?page_size=1000');
  }

  // Get questionnaires by term_category (preferred) or term_title (for contracts)
  async getQuestionnairesByTermTitle(termTitle = null, termId = null, termCategory = null) {
    const params = new URLSearchParams();
    // Prioritize term_category - only use term_title if term_category is not provided
    if (termCategory) {
      params.append('term_category', termCategory);
    } else if (termTitle) {
      params.append('term_title', termTitle);
    }
    // term_id can be passed alongside term_category or term_title for additional matching
    if (termId) params.append('term_id', termId);
    // Use the audits-contract endpoint (not audits endpoint)
    return this.request(`/audits-contract/contractquestionnaires-by-term/?${params.toString()}`);
  }

  // Get templates for a term
  async getTemplatesByTerm(termTitle = null, termId = null, termCategory = null) {
    const params = new URLSearchParams();
    if (termCategory) {
      params.append('term_category', termCategory);
    }
    if (termTitle) {
      params.append('term_title', termTitle);
    }
    if (termId) {
      params.append('term_id', termId);
    }
    return this.request(`/audits-contract/contracttemplates-by-term/?${params.toString()}`);
  }

  // Get questions from a specific template
  async getTemplateQuestions(templateId, termId = null, termCategory = null) {
    const params = new URLSearchParams();
    if (termId) {
      params.append('term_id', termId);
    }
    if (termCategory) {
      params.append('term_category', termCategory);
    }
    return this.request(`/audits-contract/contracttemplate/${templateId}/questions/?${params.toString()}`);
  }

  // Audit versions
  async getAuditVersions(auditId) {
    return this.auditsRequest(`/versions/?audit_id=${auditId}`);
  }

  async createAuditVersion(data) {
    return this.auditsRequest('/versions/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateAuditVersion(versionId, data) {
    return this.auditsRequest(`/versions/${versionId}/`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  // Audit findings
  async getAuditFindings(auditId) {
    return this.auditsRequest(`/findings/?audit_id=${auditId}`);
  }

  async createAuditFinding(data) {
    return this.auditsRequest('/findings/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateAuditFinding(findingId, data) {
    return this.auditsRequest(`/findings/${findingId}/`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  // Audit actions
  async submitAuditResponse(auditId, data) {
    return this.auditsRequest(`/${auditId}/submit-response/`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async reviewAudit(auditId, action = 'approve', comments = '') {
    return this.auditsRequest(`/${auditId}/review/`, {
      method: 'POST',
      body: JSON.stringify({ action, comments }),
    });
  }

  // BCP/DRP API methods
  async bcpdrpRequest(endpoint, options = {}) {
    const url = `${this.bcpdrpURL}${endpoint}`;
    const token = this.getStoredToken();
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` }),
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        // 401 = Unauthorized (invalid/missing token) → redirect to login
        if (response.status === 401) {
          console.log('BCP/DRP API: 401 Unauthorized - redirecting to login');
          localStorage.removeItem('session_token');
          localStorage.removeItem('current_user');
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          if (window.location.pathname !== '/login') {
            window.location.href = '/login';
          }
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        // 403 = Forbidden - check if it's an authentication issue
        if (response.status === 403) {
          const errorData = await response.json().catch(() => ({}));
          const errorMessage = errorData.detail || errorData.error || errorData.message || '';
          
          // If 403 is due to missing authentication, redirect to login
          if (errorMessage.toLowerCase().includes('authentication') || 
              errorMessage.toLowerCase().includes('credentials') ||
              errorMessage.toLowerCase().includes('not authenticated')) {
            console.log('BCP/DRP API: 403 Authentication error - redirecting to login');
            localStorage.removeItem('session_token');
            localStorage.removeItem('current_user');
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            if (window.location.pathname !== '/login') {
              window.location.href = '/login';
            }
            throw new Error('Authentication required');
          }
          
          // Otherwise, it's a permission issue - throw error with response
          const error = new Error(errorMessage || 'Permission denied');
          error.response = {
            status: 403,
            data: errorData
          };
          throw error;
        }
        
        const errorText = await response.text();
        console.error(`HTTP error! status: ${response.status}`, errorText);
        throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('BCP/DRP API request failed:', error);
      throw error;
    }
  }

  async riskAnalysisRequest(endpoint, options = {}) {
    const url = `${this.riskAnalysisURL}${endpoint}`;
    const token = this.getStoredToken();
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` }),
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        // 401 = Unauthorized (invalid/missing token) → redirect to login
        if (response.status === 401) {
          localStorage.removeItem('session_token');
          localStorage.removeItem('current_user');
          if (window.location.pathname !== '/login') {
            window.location.href = '/login';
          }
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        // 403 = Forbidden (valid token but no permission) → throw error with response for usePermissions to handle
        if (response.status === 403) {
          const errorData = await response.json().catch(() => ({}));
          const error = new Error(errorData.error || errorData.message || 'Permission denied');
          error.response = {
            status: 403,
            data: errorData
          };
          throw error;
        }
        
        const errorText = await response.text();
        console.error(`HTTP error! status: ${response.status}`, errorText);
        throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Risk Analysis API request failed:', error);
      throw error;
    }
  }

  // Plans endpoints
  async getPlans(filters = {}) {
    const queryParams = new URLSearchParams();
    
    Object.keys(filters).forEach(key => {
      if (filters[key] !== undefined && filters[key] !== null) {
        queryParams.append(key, filters[key]);
      }
    });
    
    const endpoint = queryParams.toString() ? `/?${queryParams.toString()}` : '/';
    const response = await this.bcpdrpRequest(`/plans${endpoint}`);
    return response.results || response;
  }

  async getPlan(id) {
    return this.bcpdrpRequest(`/plans/${id}/`);
  }

  async createPlan(data) {
    return this.bcpdrpRequest('/plans/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updatePlan(id, data) {
    return this.bcpdrpRequest(`/plans/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  async deletePlan(id) {
    return this.bcpdrpRequest(`/plans/${id}/`, {
      method: 'DELETE',
    });
  }

  // OCR endpoints
  async getOcrPlans(filters = {}) {
    const queryParams = new URLSearchParams();
    
    Object.keys(filters).forEach(key => {
      if (filters[key] !== undefined && filters[key] !== null) {
        queryParams.append(key, filters[key]);
      }
    });
    
    const endpoint = queryParams.toString() ? `/?${queryParams.toString()}` : '/';
    return this.bcpdrpRequest(`/ocr/plans${endpoint}`);
  }

  async getOcrPlanDetail(id) {
    return this.bcpdrpRequest(`/ocr/plans/${id}/`);
  }

  async extractOcr(id, data) {
    return this.bcpdrpRequest(`/ocr/plans/${id}/extract/`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateOcrStatus(id, data) {
    return this.bcpdrpRequest(`/ocr/plans/${id}/status/`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  // Evaluations endpoints
  async getEvaluations(planId) {
    return this.bcpdrpRequest(`/evaluations/${planId}/`);
  }

  async saveEvaluation(planId, data) {
    return this.bcpdrpRequest(`/evaluations/${planId}/save/`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getEvaluation(planId, evaluationId) {
    return this.bcpdrpRequest(`/evaluations/${planId}/${evaluationId}/`);
  }

  async saveOcrExtraction(planId, data) {
    return this.bcpdrpRequest(`/ocr/plans/${planId}/extract/`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getApprovalAssignments(filters = {}) {
    const queryParams = new URLSearchParams();
    
    Object.keys(filters).forEach(key => {
      if (filters[key] !== undefined && filters[key] !== null) {
        queryParams.append(key, filters[key]);
      }
    });
    
    const endpoint = queryParams.toString() ? `/?${queryParams.toString()}` : '/';
    return this.bcpdrpRequest(`/approvals${endpoint}`);
  }

  async getUser(id) {
    return this.bcpdrpRequest(`/users/${id}/`);
  }

  async createUser(data) {
    return this.bcpdrpRequest('/users/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateUser(id, data) {
    return this.bcpdrpRequest(`/users/${id}/`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteUser(id) {
    return this.bcpdrpRequest(`/users/${id}/`, {
      method: 'DELETE',
    });
  }

  // Vendor upload endpoint
  async uploadVendor(data) {
    return this.bcpdrpRequest('/vendor-upload/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Dropdowns endpoint
  async getDropdowns(params = {}) {
    const queryParams = new URLSearchParams();
    
    Object.keys(params).forEach(key => {
      if (params[key] !== undefined && params[key] !== null) {
        queryParams.append(key, params[key]);
      }
    });
    
    const endpoint = queryParams.toString() ? `/?${queryParams.toString()}` : '/';
    return this.bcpdrpRequest(`/dropdowns${endpoint}`);
  }

  // Questionnaires endpoints
  async getQuestionnaires(filters = {}) {
    const queryParams = new URLSearchParams();
    
    Object.keys(filters).forEach(key => {
      if (filters[key] !== undefined && filters[key] !== null) {
        queryParams.append(key, filters[key]);
      }
    });
    
    const endpoint = queryParams.toString() ? `/?${queryParams.toString()}` : '/';
    const response = await this.bcpdrpRequest(`/questionnaires${endpoint}`);
    return response.results || response;
  }

  async getQuestionnaire(id) {
    return this.bcpdrpRequest(`/questionnaires/${id}/`);
  }

  async saveQuestionnaire(data) {
    return this.bcpdrpRequest('/questionnaires/save/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Plan decisions endpoint
  async updatePlanDecision(id, data) {
    return this.bcpdrpRequest(`/plans/${id}/decision/`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  // Users endpoints
  async getUsers(filters = {}) {
    const queryParams = new URLSearchParams();
    
    Object.keys(filters).forEach(key => {
      if (filters[key] !== undefined && filters[key] !== null) {
        queryParams.append(key, filters[key]);
      }
    });
    
    const endpoint = queryParams.toString() ? `/?${queryParams.toString()}` : '/';
    const response = await this.bcpdrpRequest(`/users${endpoint}`);
    return response.results || response;
  }

  // Approvals endpoints
  async getApprovals(filters = {}) {
    const queryParams = new URLSearchParams();
    
    Object.keys(filters).forEach(key => {
      if (filters[key] !== undefined && filters[key] !== null) {
        queryParams.append(key, filters[key]);
      }
    });
    
    const endpoint = queryParams.toString() ? `/?${queryParams.toString()}` : '/';
    const response = await this.bcpdrpRequest(`/approvals${endpoint}`);
    return response.results || response;
  }

  async createApprovalAssignment(data) {
    return this.bcpdrpRequest('/approvals/assignments/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getMyApprovals(filters = {}) {
    const queryParams = new URLSearchParams();
    
    Object.keys(filters).forEach(key => {
      if (filters[key] !== undefined && filters[key] !== null) {
        queryParams.append(key, filters[key]);
      }
    });
    
    const endpoint = queryParams.toString() ? `/?${queryParams.toString()}` : '/';
    const response = await this.bcpdrpRequest(`/my-approvals${endpoint}`);
    return response.results || response;
  }

  async dropdowns(params = {}) {
    const queryParams = new URLSearchParams();
    
    Object.keys(params).forEach(key => {
      if (params[key] !== undefined && params[key] !== null) {
        queryParams.append(key, params[key]);
      }
    });
    
    const endpoint = queryParams.toString() ? `/?${queryParams.toString()}` : '/';
    return this.bcpdrpRequest(`/dropdowns${endpoint}`);
  }

  // Risk Analysis endpoints
  async getRiskDashboard() {
    return this.riskAnalysisRequest('/dashboard/');
  }

  async generateEntityRisk(data) {
    return this.riskAnalysisRequest('/entity-risk-generation/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getEntityDropdowns() {
    return this.riskAnalysisRequest('/entity-dropdown/');
  }

  async getRiskAnalysis(filters = {}) {
    const queryParams = new URLSearchParams();
    
    Object.keys(filters).forEach(key => {
      if (filters[key] !== undefined && filters[key] !== null) {
        queryParams.append(key, filters[key]);
      }
    });
    
    const endpoint = queryParams.toString() ? `/?${queryParams.toString()}` : '/';
    const response = await this.riskAnalysisRequest(endpoint);
    return response.results || response;
  }

  // Plans object for BCP/DRP
  get plans() {
    return {
      list: (filters = {}) => this.getPlans(filters),
      create: (data) => this.createPlan(data),
      update: (id, data) => this.updatePlan(id, data),
      delete: (id) => this.deletePlan(id),
      get: (id) => this.getPlan(id)
    };
  }

  // Evaluations object for BCP/DRP
  get evaluations() {
    return {
      list: (planId) => this.getEvaluations(planId),
      save: (planId, data) => this.saveEvaluation(planId, data),
      get: (planId, evaluationId) => this.getEvaluation(planId, evaluationId)
    };
  }

  // OCR object for BCP/DRP
  get ocr() {
    return {
      planDetail: (planId) => this.getOcrPlanDetail(planId),
      plans: () => this.getOcrPlans(),
      extract: (planId, data) => this.saveOcrExtraction(planId, data),
      status: (planId, data) => this.updateOcrStatus(planId, data)
    };
  }

  // Approvals object for BCP/DRP
  get approvals() {
    return {
      list: (filters = {}) => this.getApprovalAssignments(filters),
      createAssignment: (data) => this.createApprovalAssignment(data),
      myApprovals: (filters = {}) => this.getMyApprovals(filters)
    };
  }

  // Users object for BCP/DRP
  get users() {
    return {
      list: (filters = {}) => this.getUsers(filters),
      get: (id) => this.getUser(id),
      create: (data) => this.createUser(data),
      update: (id, data) => this.updateUser(id, data),
      delete: (id) => this.deleteUser(id)
    };
  }
}

// Create and export a singleton instance
const apiService = new APIService();

// Export axios instance for contract modules
import axios from 'axios'
export const api = axios.create({
  baseURL: getTprmApiBaseUrl(),
  headers: {
    'Content-Type': 'application/json',
  },
})

// Helper function for axios interceptor (outside class)
function getStoredTokenForAxios() {
  const keys = ['access_token', 'session_token', 'token', 'jwt_token'];
  for (const key of keys) {
    const val = localStorage.getItem(key);
    if (val) return val;
  }
  return null;
}

// Add request interceptor to inject JWT token
api.interceptors.request.use(
  (config) => {
    const token = getStoredTokenForAxios();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor to handle authentication and permission errors
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // Handle 401 errors - try to refresh token and retry
    if (error.response?.status === 401 && !originalRequest._retry) {
      console.log('🔄 [Axios Interceptor] 401 error detected, attempting token refresh...');
      originalRequest._retry = true;
      
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const apiOrigin = getApiOrigin() || 'https://grc-tprm.vardaands.com'
          const refreshResponse = await fetch(`${apiOrigin}/api/jwt/refresh/`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({ refresh_token: refreshToken })
          });
          
          if (refreshResponse.ok) {
            const refreshData = await refreshResponse.json();
            if (refreshData.status === 'success') {
              localStorage.setItem('access_token', refreshData.access_token);
              if (refreshData.refresh_token) {
                localStorage.setItem('refresh_token', refreshData.refresh_token);
              }
              
              // Retry the original request with new token
              const newToken = getStoredTokenForAxios();
              if (newToken) {
                originalRequest.headers.Authorization = `Bearer ${newToken}`;
                return api(originalRequest);
              }
            }
          }
        }
      } catch (refreshError) {
        console.error('❌ Token refresh failed in axios interceptor:', refreshError);
      }
      
      // If refresh failed, remove tokens and redirect to login
      console.warn('⚠️ API 401 Unauthorized - refresh failed');
      localStorage.removeItem('access_token');
      localStorage.removeItem('session_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('current_user');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    } else if (error.response?.status === 403) {
      // Permission denied - RBAC check failed
      const errorMessage = error.response?.data?.error || error.response?.data?.message || 'You do not have permission to access this resource.';
      const errorCode = error.response?.data?.code || '403';
      
      console.warn('⚠️ API 403 Forbidden:', errorMessage);
      
      // Store error info but don't redirect automatically - let components handle it
      sessionStorage.setItem('access_denied_error', JSON.stringify({
        message: errorMessage,
        code: errorCode,
        timestamp: new Date().toISOString(),
        path: window.location.pathname,
        url: error.config?.url
      }));
      
      // Attach more detailed error info to the error object
      error.permissionDenied = true;
      error.permissionError = errorMessage;
      
      // Only redirect if this is a critical permission error (not just a missing resource)
      // Let individual components decide how to handle 403 errors
    }
    return Promise.reject(error);
  }
);

export default apiService;
