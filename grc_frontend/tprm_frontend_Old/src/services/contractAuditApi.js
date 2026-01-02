import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://grc-tprm.vardaands.com/api/tprm'

// Helper to get token from any of the storage keys (compatible with GRC auth)
function getStoredToken() {
  const keys = ['access_token', 'session_token', 'token', 'jwt_token']
  for (const key of keys) {
    const val = localStorage.getItem(key)
    if (val) return val
  }
  return null
}

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Helper to refresh token using JWT refresh endpoint
async function refreshTokenIfNeeded() {
  try {
    const refreshToken = localStorage.getItem('refresh_token')
    if (!refreshToken) {
      console.warn('⚠️ [contractAuditApi] No refresh token available')
      return false
    }
    
    // Construct JWT refresh URL - remove /api/tprm suffix if present, then add /api/jwt/refresh/
    let jwtRefreshUrl = API_BASE_URL
    if (jwtRefreshUrl.endsWith('/api/tprm')) {
      jwtRefreshUrl = jwtRefreshUrl.replace('/api/tprm', '')
    }
    jwtRefreshUrl = `${jwtRefreshUrl}/api/jwt/refresh/`
    
    const refreshResponse = await axios.post(jwtRefreshUrl, {
      refresh_token: refreshToken
    })
    
    if (refreshResponse.data.status === 'success') {
      const { access_token, refresh_token: newRefreshToken } = refreshResponse.data
      localStorage.setItem('access_token', access_token)
      if (newRefreshToken) {
        localStorage.setItem('refresh_token', newRefreshToken)
      }
      console.log('✅ [contractAuditApi] Token refreshed successfully')
      return true
    }
    
    return false
  } catch (error) {
    // Don't log errors for refresh failures - they're expected if token is expired
    if (error.response?.status !== 401) {
      console.warn('⚠️ [contractAuditApi] Token refresh failed:', error.message)
    }
    return false
  }
}

// Add request interceptor to inject JWT token
api.interceptors.request.use(
  (config) => {
    // Get token from localStorage (check multiple keys for compatibility)
    const token = getStoredToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    } else {
      console.warn('⚠️ [contractAuditApi] No token found for request:', config.url)
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    
    // CRITICAL: Don't try to refresh if the refresh endpoint itself failed
    if (originalRequest.url && originalRequest.url.includes('/api/jwt/refresh/')) {
      console.error('❌ [contractAuditApi] Refresh endpoint returned 401 - refresh token is invalid/expired')
      return Promise.reject(error)
    }
    
    // Handle 401 errors (token expired) - attempt token refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      console.log('🔄 [contractAuditApi] 401 error detected - attempting token refresh...')
      originalRequest._retry = true
      
      try {
        // Try to refresh token using the helper function
        // This will try local authService first, then fall back to direct JWT refresh
        const refreshSuccess = await refreshTokenIfNeeded()
        
        if (refreshSuccess) {
          console.log('✅ [contractAuditApi] Token refreshed successfully, retrying request')
          const newToken = getStoredToken()
          if (newToken) {
            originalRequest.headers.Authorization = `Bearer ${newToken}`
          }
          return api(originalRequest)
        }
      } catch (refreshError) {
        console.error('❌ [contractAuditApi] Error during token refresh:', refreshError)
      }
      
      // If refresh failed, don't force logout - let the component handle the error gracefully
      console.warn('⚠️ [contractAuditApi] Token refresh failed - request will fail')
    } else if (error.response?.status === 401) {
      // Already retried, don't try again
      console.error('❌ [contractAuditApi] Token refresh already attempted, request failed')
    } else if (error.response?.status === 403) {
      // Permission denied - RBAC check failed
      const errorMessage = error.response?.data?.error || error.response?.data?.message || 'You do not have permission to access this resource.'
      const errorCode = error.response?.data?.code || '403'
      
      // Store error info in sessionStorage so the AccessDenied page can display it
      sessionStorage.setItem('access_denied_error', JSON.stringify({
        message: errorMessage,
        code: errorCode,
        timestamp: new Date().toISOString(),
        path: window.location.pathname
      }))
      
      // Redirect to access denied page
      if (window.location.pathname !== '/access-denied') {
        window.location.href = '/access-denied'
      }
    }
    return Promise.reject(error)
  }
)

const contractAuditApi = {
  // Contract Audit CRUD operations
  async getContractAudits(params = {}) {
    try {
      const response = await api.get('/audits-contract/', { params })
      return {
        success: true,
        data: response.data.data || response.data,
        pagination: response.data.pagination
      }
    } catch (error) {
      console.error('Error fetching contract audits:', error)
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to fetch contract audits',
        message: error.response?.data?.message || error.message
      }
    }
  },

  async getContractAudit(auditId) {
    try {
      const response = await api.get(`/audits-contract/${auditId}/`)
      return {
        success: true,
        data: response.data.data || response.data
      }
    } catch (error) {
      console.error('Error fetching contract audit:', error)
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to fetch contract audit',
        message: error.response?.data?.message || error.message
      }
    }
  },

  async createContractAudit(auditData) {
    try {
      const response = await api.post('/audits-contract/', auditData)
      return {
        success: true,
        data: response.data.data || response.data,
        message: response.data.message || 'Contract audit created successfully'
      }
    } catch (error) {
      console.error('Error creating contract audit:', error)
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to create contract audit',
        message: error.response?.data?.message || error.message
      }
    }
  },

  async updateContractAudit(auditId, auditData) {
    try {
      const response = await api.patch(`/audits-contract/${auditId}/`, auditData)
      return {
        success: true,
        data: response.data.data || response.data,
        message: response.data.message || 'Contract audit updated successfully'
      }
    } catch (error) {
      console.error('Error updating contract audit:', error)
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to update contract audit',
        message: error.response?.data?.message || error.message
      }
    }
  },

  async deleteContractAudit(auditId) {
    try {
      const response = await api.delete(`/audits-contract/${auditId}/`)
      return {
        success: true,
        message: response.data.message || 'Contract audit deleted successfully'
      }
    } catch (error) {
      console.error('Error deleting contract audit:', error)
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to delete contract audit',
        message: error.response?.data?.message || error.message
      }
    }
  },

  // Contract Audit actions
  async startContractAudit(auditId) {
    try {
      const response = await api.post(`/audits-contract/${auditId}/contractstart/`)
      return {
        success: true,
        data: response.data.data || response.data,
        message: response.data.message || 'Contract audit started successfully'
      }
    } catch (error) {
      console.error('Error starting contract audit:', error)
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to start contract audit',
        message: error.response?.data?.message || error.message
      }
    }
  },

  async submitContractAuditResponse(auditId, responseData) {
    try {
      const response = await api.post(`/audits-contract/${auditId}/contractsubmit-response/`, responseData)
      return {
        success: true,
        data: response.data.data || response.data,
        message: response.data.message || 'Contract audit response submitted successfully'
      }
    } catch (error) {
      console.error('Error submitting contract audit response:', error)
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to submit contract audit response',
        message: error.response?.data?.message || error.message
      }
    }
  },

  async reviewContractAudit(auditId, reviewData) {
    try {
      const response = await api.post(`/audits-contract/${auditId}/contractreview/`, reviewData)
      return {
        success: true,
        data: response.data.data || response.data,
        message: response.data.message || 'Contract audit reviewed successfully'
      }
    } catch (error) {
      console.error('Error reviewing contract audit:', error)
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to review contract audit',
        message: error.response?.data?.message || error.message
      }
    }
  },

  // Contract Audit Questionnaires
  async getContractAuditQuestionnaires(params = {}) {
    try {
      const response = await api.get('/audits-contract/contractquestionnaires/', { params })
      return {
        success: true,
        data: response.data.data || response.data
      }
    } catch (error) {
      console.error('Error fetching contract audit questionnaires:', error)
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to fetch contract audit questionnaires',
        message: error.response?.data?.message || error.message
      }
    }
  },

  async getContractAuditQuestionnairesByTerm(params = {}) {
    try {
      const response = await api.get('/audits-contract/contractquestionnaires-by-term/', { params })
      return {
        success: true,
        data: response.data.data || response.data
      }
    } catch (error) {
      console.error('Error fetching contract audit questionnaires by term:', error)
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to fetch contract audit questionnaires by term',
        message: error.response?.data?.message || error.message
      }
    }
  },

  async getContractAuditQuestionnairesForTermIds(params = {}) {
    try {
      const response = await api.get('/audits-contract/contractquestionnaires-by-term-ids/', { params })
      return {
        success: true,
        data: response.data.data || response.data
      }
    } catch (error) {
      console.error('Error fetching contract audit questionnaires for term IDs:', error)
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to fetch contract audit questionnaires for term IDs',
        message: error.response?.data?.message || error.message
      }
    }
  },

  async getContractAuditQuestionnaire(questionnaireId) {
    try {
      const response = await api.get(`/audits-contract/contractquestionnaires/${questionnaireId}/`)
      return {
        success: true,
        data: response.data.data || response.data
      }
    } catch (error) {
      console.error('Error fetching contract audit questionnaire:', error)
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to fetch contract audit questionnaire',
        message: error.response?.data?.message || error.message
      }
    }
  },

  // Contract Audit Versions
  async getContractAuditVersions(params = {}) {
    try {
      const response = await api.get('/audits-contract/contractversions/', { params })
      return {
        success: true,
        data: response.data.data || response.data
      }
    } catch (error) {
      console.error('Error fetching contract audit versions:', error)
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to fetch contract audit versions',
        message: error.response?.data?.message || error.message
      }
    }
  },

  async getContractAuditVersion(versionId) {
    try {
      const response = await api.get(`/audits-contract/contractversions/${versionId}/`)
      return {
        success: true,
        data: response.data.data || response.data
      }
    } catch (error) {
      console.error('Error fetching contract audit version:', error)
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to fetch contract audit version',
        message: error.response?.data?.message || error.message
      }
    }
  },

  async createContractAuditVersion(versionData) {
    try {
      const response = await api.post('/audits-contract/contractversions/', versionData)
      return {
        success: true,
        data: response.data.data || response.data,
        message: response.data.message || 'Contract audit version created successfully'
      }
    } catch (error) {
      console.error('Error creating contract audit version:', error)
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to create contract audit version',
        message: error.response?.data?.message || error.message
      }
    }
  },

  async updateContractAuditVersion(versionId, versionData) {
    try {
      const response = await api.patch(`/audits-contract/contractversions/${versionId}/`, versionData)
      return {
        success: true,
        data: response.data.data || response.data,
        message: response.data.message || 'Contract audit version updated successfully'
      }
    } catch (error) {
      console.error('Error updating contract audit version:', error)
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to update contract audit version',
        message: error.response?.data?.message || error.message
      }
    }
  },

  // Contract Audit Findings
  async getContractAuditFindings(params = {}) {
    try {
      const response = await api.get('/audits-contract/contractfindings/', { params })
      return {
        success: true,
        data: response.data.data || response.data
      }
    } catch (error) {
      console.error('Error fetching contract audit findings:', error)
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to fetch contract audit findings',
        message: error.response?.data?.message || error.message
      }
    }
  },

  async getContractAuditFinding(findingId) {
    try {
      const response = await api.get(`/audits-contract/contractfindings/${findingId}/`)
      return {
        success: true,
        data: response.data.data || response.data
      }
    } catch (error) {
      console.error('Error fetching contract audit finding:', error)
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to fetch contract audit finding',
        message: error.response?.data?.message || error.message
      }
    }
  },

  async createContractAuditFinding(findingData) {
    try {
      const response = await api.post('/audits-contract/contractfindings/', findingData)
      return {
        success: true,
        data: response.data.data || response.data,
        message: response.data.message || 'Contract audit finding created successfully'
      }
    } catch (error) {
      console.error('Error creating contract audit finding:', error)
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to create contract audit finding',
        message: error.response?.data?.message || error.message
      }
    }
  },

  // Contract Audit Reports
  async getContractAuditReports(params = {}) {
    try {
      const response = await api.get('/audits-contract/contractreports/', { params })
      return {
        success: true,
        data: response.data.data || response.data
      }
    } catch (error) {
      console.error('Error fetching contract audit reports:', error)
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to fetch contract audit reports',
        message: error.response?.data?.message || error.message
      }
    }
  },

  async getContractAuditReport(reportId) {
    try {
      const response = await api.get(`/audits-contract/contractreports/${reportId}/`)
      return {
        success: true,
        data: response.data.data || response.data
      }
    } catch (error) {
      console.error('Error fetching contract audit report:', error)
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to fetch contract audit report',
        message: error.response?.data?.message || error.message
      }
    }
  },

  // Dashboard and utilities
  async getContractAuditDashboardStats() {
    try {
      const response = await api.get('/audits-contract/contractdashboard/stats/')
      return {
        success: true,
        data: response.data.data || response.data
      }
    } catch (error) {
      console.error('Error fetching contract audit dashboard stats:', error)
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to fetch contract audit dashboard stats',
        message: error.response?.data?.message || error.message
      }
    }
  },

  async getAvailableContracts() {
    try {
      const response = await api.get('/audits-contract/contractavailable-contracts/')
      return {
        success: true,
        data: response.data.data || response.data
      }
    } catch (error) {
      console.error('Error fetching available contracts:', error)
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to fetch available contracts',
        message: error.response?.data?.message || error.message
      }
    }
  },

  async getContractTermsForAudit(contractId) {
    try {
      const response = await api.get(`/audits-contract/contract-terms/${contractId}/`)
      return {
        success: true,
        data: response.data.data || response.data
      }
    } catch (error) {
      console.error('Error fetching contract terms for audit:', error)
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to fetch contract terms',
        message: error.response?.data?.message || error.message
      }
    }
  },

  async getAvailableUsers() {
    try {
      const response = await api.get('/audits-contract/contractavailable-users/')
      return {
        success: true,
        data: response.data.data || response.data
      }
    } catch (error) {
      console.error('Error fetching available users:', error)
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to fetch available users',
        message: error.response?.data?.message || error.message
      }
    }
  }
}

export default contractAuditApi
