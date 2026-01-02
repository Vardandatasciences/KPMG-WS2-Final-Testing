import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'https://grc-tprm.vardaands.com/api/tprm',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add request interceptor to inject JWT token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('session_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor to handle common errors
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    if (error.response?.status === 401) {
      // Session expired or invalid
      localStorage.removeItem('session_token')
      localStorage.removeItem('current_user')
      window.location.href = '/login'
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

// Audit API methods
const auditApi = {
  // Contract Audit CRUD operations
  async getAudits(params = {}) {
    try {
      const response = await api.get('/audits-contract/', { params })
      return response.data
    } catch (error) {
      console.error('Error fetching contract audits:', error)
      throw error
    }
  },

  async getAudit(auditId) {
    try {
      const response = await api.get(`/audits-contract/${auditId}/`)
      return response.data
    } catch (error) {
      console.error('Error fetching contract audit:', error)
      throw error
    }
  },

  async createContractAudit(auditData) {
    try {
      const response = await api.post('/audits-contract/', auditData)
      return response.data
    } catch (error) {
      console.error('Error creating contract audit:', error)
      throw error
    }
  },

  async updateAudit(auditId, auditData) {
    try {
      const response = await api.patch(`/audits-contract/${auditId}/`, auditData)
      return response.data
    } catch (error) {
      console.error('Error updating contract audit:', error)
      throw error
    }
  },

  async startAudit(auditId) {
    try {
      const response = await api.post(`/audits-contract/${auditId}/start/`)
      return response.data
    } catch (error) {
      console.error('Error starting contract audit:', error)
      throw error
    }
  },

  // Contract and Terms
  async getAvailableContracts() {
    try {
      const response = await api.get('/audits-contract/contractavailable-contracts/')
      return response.data
    } catch (error) {
      console.error('Error fetching available contracts:', error)
      throw error
    }
  },

  async getContractTerms(contractId) {
    try {
      const response = await api.get(`/audits-contract/contract-terms/${contractId}/`)
      return response.data
    } catch (error) {
      console.error('Error fetching contract terms:', error)
      throw error
    }
  },

  // Users
  async getAvailableUsers() {
    try {
      const response = await api.get('/audits-contract/contractavailable-users/')
      return response.data
    } catch (error) {
      console.error('Error fetching available users:', error)
      throw error
    }
  },

  // Dashboard and Statistics
  async getAuditDashboardStats() {
    try {
      const response = await api.get('/audits-contract/contractdashboard/stats/')
      return response.data
    } catch (error) {
      console.error('Error fetching contract audit dashboard stats:', error)
      throw error
    }
  },

  // Audit Versions
  async getAuditVersions(auditId) {
    try {
      const response = await api.get('/audits-contract/contractversions/', {
        params: { audit_id: auditId }
      })
      return response.data
    } catch (error) {
      console.error('Error fetching contract audit versions:', error)
      throw error
    }
  },

  async createAuditVersion(versionData) {
    try {
      const response = await api.post('/audits-contract/contractversions/', versionData)
      return response.data
    } catch (error) {
      console.error('Error creating contract audit version:', error)
      throw error
    }
  },

  async updateAuditVersion(versionId, versionData) {
    try {
      const response = await api.patch(`/audits-contract/contractversions/${versionId}/`, versionData)
      return response.data
    } catch (error) {
      console.error('Error updating contract audit version:', error)
      throw error
    }
  },

  // Audit Findings
  async getAuditFindings(auditId) {
    try {
      const response = await api.get('/audits-contract/contractfindings/', {
        params: { audit_id: auditId }
      })
      return response.data
    } catch (error) {
      console.error('Error fetching contract audit findings:', error)
      throw error
    }
  },

  async createAuditFinding(findingData) {
    try {
      const response = await api.post('/audits-contract/contractfindings/', findingData)
      return response.data
    } catch (error) {
      console.error('Error creating contract audit finding:', error)
      throw error
    }
  },

  // Static Questionnaires
  async getStaticQuestionnaires(params = {}) {
    try {
      const response = await api.get('/audits-contract/contractquestionnaires/', { params })
      return response.data
    } catch (error) {
      console.error('Error fetching contract static questionnaires:', error)
      throw error
    }
  },

  // Audit Actions
  async submitAuditResponse(auditId, responseData) {
    try {
      const response = await api.post(`/audits-contract/${auditId}/contractsubmit-response/`, responseData)
      return response.data
    } catch (error) {
      console.error('Error submitting contract audit response:', error)
      throw error
    }
  },

  async reviewAudit(auditId, reviewData) {
    try {
      const response = await api.post(`/audits-contract/${auditId}/contractreview/`, reviewData)
      return response.data
    } catch (error) {
      console.error('Error reviewing contract audit:', error)
      throw error
    }
  }
}

// Create a unified API service that includes audit methods
const apiService = {
  ...auditApi,
  // Add any other API methods here as needed
}

// Export both the raw api instance and the enhanced apiService
export { api }
export default apiService
