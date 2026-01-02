/**
 * Unified Vendor API Service
 * Connects to all vendor management endpoints
 */
import axios from 'axios'

const VENDOR_BASE_URL = 'https://grc-tprm.vardaands.com/api/tprm'

// Create axios instance for vendor APIs with JWT authentication
const vendorApi = axios.create({
  baseURL: VENDOR_BASE_URL,
  timeout: 20000,
  headers: {
    'Content-Type': 'application/json',
  }
})

// Request interceptor to add JWT token
vendorApi.interceptors.request.use(
  (config) => {
    // Add JWT token from localStorage
    const token = localStorage.getItem('session_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    // For FormData requests, let the browser set the Content-Type header
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type']
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor to handle errors
vendorApi.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('Vendor API Error:', error)
    
    // Handle 401 Unauthorized - token expired or invalid
    if (error.response?.status === 401) {
      // Clear authentication data
      localStorage.removeItem('session_token')
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('current_user')
      
      // Redirect to login if not already there
      if (window.location.pathname !== '/login' && !window.location.pathname.includes('/vendor-login')) {
        window.location.href = '/login'
      }
    }
    
    // Handle 403 Forbidden - permission denied
    if (error.response?.status === 403) {
      const errorData = error.response.data
      const errorMessage = errorData?.error || errorData?.message || 'You do not have permission to access this resource.'
      const errorCode = errorData?.code || '403'
      const permissionType = errorData?.permission_type || 'unknown'
      
      console.error(`[VendorAPI] Permission denied: ${permissionType}`, error.response.data)
      
      // Store error info in sessionStorage so AccessDenied page can display it
      sessionStorage.setItem('access_denied_error', JSON.stringify({
        message: errorMessage,
        code: errorCode,
        timestamp: new Date().toISOString(),
        path: window.location.pathname,
        permission: permissionType,
        permissionRequired: permissionType
      }))
      
      // Redirect to access denied page
      if (window.location.pathname !== '/access-denied') {
        console.log('🔄 Redirecting to /access-denied page...')
        window.location.href = '/access-denied'
      }
    }
    
    return Promise.reject(error)
  }
)

class VendorAPIService {
  constructor() {
    this.baseURL = VENDOR_BASE_URL
    this.api = vendorApi
  }

  // Vendor Core APIs
  async getVendors(params = {}) {
    try {
      const response = await this.api.get('/vendor-core/vendors/', { params })
      return response.data
    } catch (error) {
      console.error('Failed to fetch vendors:', error)
      throw error
    }
  }

  async createVendor(vendorData) {
    try {
      const response = await this.api.post('/vendor-core/vendors/', vendorData)
      return response.data
    } catch (error) {
      console.error('Failed to create vendor:', error)
      throw error
    }
  }

  async updateVendor(vendorId, vendorData) {
    try {
      const response = await this.api.put(`/vendor-core/vendors/${vendorId}/`, vendorData)
      return response.data
    } catch (error) {
      console.error('Failed to update vendor:', error)
      throw error
    }
  }

  async deleteVendor(vendorId) {
    try {
      const response = await this.api.delete(`/vendor-core/vendors/${vendorId}/`)
      return response.data
    } catch (error) {
      console.error('Failed to delete vendor:', error)
      throw error
    }
  }

  // Vendor Authentication APIs - reads GRC session
  async checkAuth() {
    try {
      const response = await this.api.get('/vendor-auth/check-auth/')
      return response.data
    } catch (error) {
      console.error('Auth check failed:', error)
      // Return GRC session user if available
      const user = this.getGrcSessionUser()
      return { authenticated: !!user, user }
    }
  }

  async login(credentials) {
    try {
      const response = await this.api.post('/vendor-auth/login/', credentials)
      return response.data
    } catch (error) {
      console.error('Login failed:', error)
      // Return GRC session user if available
      const user = this.getGrcSessionUser()
      return { success: !!user, user }
    }
  }

  getGrcSessionUser() {
    try {
      const userStr = localStorage.getItem('current_user') || localStorage.getItem('user')
      if (userStr) {
        return JSON.parse(userStr)
      }
    } catch (e) {
      console.error('Error getting GRC session user:', e)
    }
    return null
  }

  async logout() {
    try {
      const response = await this.api.post('/vendor-auth/logout/')
      return response.data
    } catch (error) {
      console.error('Logout error:', error)
      return { success: true }
    }
  }

  // Vendor Risk APIs
  async getRiskAssessments(params = {}) {
    try {
      const response = await this.api.get('/vendor-risk/assessments/', { params })
      return response.data
    } catch (error) {
      console.error('Failed to fetch risk assessments:', error)
      throw error
    }
  }

  async createRiskAssessment(assessmentData) {
    try {
      const response = await this.api.post('/vendor-risk/assessments/', assessmentData)
      return response.data
    } catch (error) {
      console.error('Failed to create risk assessment:', error)
      throw error
    }
  }

  async updateRiskAssessment(assessmentId, assessmentData) {
    try {
      const response = await this.api.put(`/vendor-risk/assessments/${assessmentId}/`, assessmentData)
      return response.data
    } catch (error) {
      console.error('Failed to update risk assessment:', error)
      throw error
    }
  }

  // Vendor Questionnaire APIs
  async getQuestionnaires(params = {}) {
    try {
      const response = await this.api.get('/vendor-questionnaire/questionnaires/', { params })
      return response.data
    } catch (error) {
      console.error('Failed to fetch questionnaires:', error)
      throw error
    }
  }

  async createQuestionnaire(questionnaireData) {
    try {
      const response = await this.api.post('/vendor-questionnaire/questionnaires/', questionnaireData)
      return response.data
    } catch (error) {
      console.error('Failed to create questionnaire:', error)
      throw error
    }
  }

  async updateQuestionnaire(questionnaireId, questionnaireData) {
    try {
      const response = await this.api.put(`/vendor-questionnaire/questionnaires/${questionnaireId}/`, questionnaireData)
      return response.data
    } catch (error) {
      console.error('Failed to update questionnaire:', error)
      throw error
    }
  }

  async deleteQuestionnaire(questionnaireId) {
    try {
      const response = await this.api.delete(`/vendor-questionnaire/questionnaires/${questionnaireId}/`)
      return response.data
    } catch (error) {
      console.error('Failed to delete questionnaire:', error)
      throw error
    }
  }

  async getQuestionnaireTypes() {
    try {
      const response = await this.api.get('/vendor-questionnaire/questionnaires/get_questionnaire_types/')
      return response.data
    } catch (error) {
      console.error('Failed to fetch questionnaire types:', error)
      return []
    }
  }

  async getQuestionTypes() {
    try {
      const response = await this.api.get('/vendor-questionnaire/questionnaires/get_question_types/')
      return response.data
    } catch (error) {
      console.error('Failed to fetch question types:', error)
      return []
    }
  }

  async getVendorCategories() {
    try {
      const response = await this.api.get('/vendor-questionnaire/questionnaires/get_vendor_categories/')
      return response.data
    } catch (error) {
      console.error('Failed to fetch vendor categories:', error)
      return []
    }
  }

  // Vendor Dashboard APIs
  async getDashboardData() {
    try {
      const response = await this.api.get('/vendor-dashboard/dashboard-data/')
      return response.data
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
      // Return mock data for development
      return {
        kpis: [
          { title: "Total Vendors", value: "247", variant: "default", trend: { value: "12%", isPositive: true } },
          { title: "High-Risk Vendors", value: "8", variant: "destructive", trend: { value: "2%", isPositive: false } },
          { title: "SLA Compliance", value: "94.2%", variant: "success", trend: { value: "3.1%", isPositive: true } },
          { title: "Avg Risk Score", value: "2.4", variant: "default", trend: { value: "0.3", isPositive: false } }
        ],
        recentVendors: [
          { name: "TechCorp Solutions", status: "pending", riskLevel: "medium", daysActive: 5 },
          { name: "Global Industries", status: "approved", riskLevel: "low", daysActive: 12 },
          { name: "DataStream Inc", status: "review", riskLevel: "high", daysActive: 3 },
          { name: "SecureNet Systems", status: "approved", riskLevel: "low", daysActive: 8 }
        ]
      }
    }
  }

  async getKPIData() {
    try {
      const response = await this.api.get('/vendor-dashboard/kpi-data/')
      return response.data
    } catch (error) {
      console.error('Failed to fetch KPI data:', error)
      throw error
    }
  }

  // Vendor Lifecycle APIs
  async getLifecycleData(vendorId) {
    try {
      const response = await this.api.get(`/vendor-lifecycle/vendors/${vendorId}/lifecycle/`)
      return response.data
    } catch (error) {
      console.error('Failed to fetch lifecycle data:', error)
      throw error
    }
  }

  async updateLifecycleStage(vendorId, stageData) {
    try {
      const response = await this.api.put(`/vendor-lifecycle/vendors/${vendorId}/lifecycle/`, stageData)
      return response.data
    } catch (error) {
      console.error('Failed to update lifecycle stage:', error)
      throw error
    }
  }

  // Vendor Approval APIs
  async getApprovalWorkflows(params = {}) {
    try {
      const response = await this.api.get('/vendor-approval/workflows/', { params })
      return response.data
    } catch (error) {
      console.error('Failed to fetch approval workflows:', error)
      throw error
    }
  }

  async createApprovalWorkflow(workflowData) {
    try {
      const response = await this.api.post('/vendor-approval/workflows/', workflowData)
      return response.data
    } catch (error) {
      console.error('Failed to create approval workflow:', error)
      throw error
    }
  }

  async updateApprovalWorkflow(workflowId, workflowData) {
    try {
      const response = await this.api.put(`/vendor-approval/workflows/${workflowId}/`, workflowData)
      return response.data
    } catch (error) {
      console.error('Failed to update approval workflow:', error)
      throw error
    }
  }

  async getMyApprovals(params = {}) {
    try {
      const response = await this.api.get('/vendor-approval/my-approvals/', { params })
      return response.data
    } catch (error) {
      console.error('Failed to fetch my approvals:', error)
      throw error
    }
  }

  async getAllApprovals(params = {}) {
    try {
      const response = await this.api.get('/vendor-approval/all-approvals/', { params })
      return response.data
    } catch (error) {
      console.error('Failed to fetch all approvals:', error)
      throw error
    }
  }

  // Risk Analysis Vendor APIs
  async analyzeVendorRisk(vendorId, analysisData) {
    try {
      const response = await this.api.post(`/risk-analysis-vendor/analyze/${vendorId}/`, analysisData)
      return response.data
    } catch (error) {
      console.error('Failed to analyze vendor risk:', error)
      throw error
    }
  }

  async getRiskAnalysisHistory(vendorId, params = {}) {
    try {
      const response = await this.api.get(`/risk-analysis-vendor/history/${vendorId}/`, { params })
      return response.data
    } catch (error) {
      console.error('Failed to fetch risk analysis history:', error)
      throw error
    }
  }
}

// Create and export a singleton instance
const vendorAPI = new VendorAPIService()
export default vendorAPI

// Also export the class for direct instantiation if needed
export { VendorAPIService }
