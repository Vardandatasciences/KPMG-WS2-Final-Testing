import axios from 'axios'
import { getTprmApiBaseUrl } from '@/utils/backendEnv'

const api = axios.create({
  baseURL: getTprmApiBaseUrl(),
  withCredentials: true, // Support session cookies
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add request interceptor to inject JWT token
api.interceptors.request.use(
  (config) => {
    // Standard token retrieval: check sessionStorage first (populated by GRC parent)
    const token = sessionStorage.getItem('access_token') || 
                  sessionStorage.getItem('session_token') ||
                  localStorage.getItem('session_token') ||
                  localStorage.getItem('auth_token') || 
                  localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Add response interceptor to handle authentication and permission errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('session_token')
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('current_user')
      
      // If in iframe, request auth from GRC parent
      const isInIframe = window.self !== window.top
      if (isInIframe && window.parent) {
        window.parent.postMessage({ type: 'TPRM_REDIRECT_TO_LOGIN' }, '*')
      } else if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    } else if (error.response?.status === 403) {
      // Permission denied - RBAC check failed
      // Removed auto-redirect to prevent loops; individual components handle 403.
      const errorData = error.response.data
      const errorMessage = errorData?.error || errorData?.message || 'You do not have permission to access this resource.'
      console.warn('[contractApprovalApi] 403 Forbidden:', errorMessage, error.config?.url)
      
      // Store error info in sessionStorage for optional display by components
      sessionStorage.setItem('access_denied_error', JSON.stringify({
        message: errorMessage,
        code: errorData?.code || '403',
        timestamp: new Date().toISOString(),
        path: window.location.pathname
      }))
    }
    return Promise.reject(error)
  }
)

const CONTRACT_APPROVAL_API_BASE = '/contracts/approvals'

class ContractApprovalApi {
  // Get all contract approvals with filtering
  async getApprovals(params = {}) {
    try {
      const response = await api.get(`${CONTRACT_APPROVAL_API_BASE}/approvals/`, { params })
      return response.data
    } catch (error) {
      console.error('Error fetching contract approvals:', error)
      throw this.handleError(error)
    }
  }

  // Get specific contract approval
  async getApproval(approvalId) {
    try {
      const response = await api.get(`${CONTRACT_APPROVAL_API_BASE}/approvals/${approvalId}/`)
      return response.data
    } catch (error) {
      console.error('Error fetching contract approval:', error)
      throw this.handleError(error)
    }
  }

  // Create new contract approval
  async createApproval(approvalData) {
    try {
      const response = await api.post(`${CONTRACT_APPROVAL_API_BASE}/approvals/create/`, approvalData)
      return response.data
    } catch (error) {
      console.error('Error creating contract approval:', error)
      throw this.handleError(error)
    }
  }

  // Create multiple contract approvals
  async createBulkApprovals(bulkData) {
    try {
      const response = await api.post(`${CONTRACT_APPROVAL_API_BASE}/approvals/bulk-create/`, bulkData)
      return response.data
    } catch (error) {
      console.error('Error creating bulk contract approvals:', error)
      throw this.handleError(error)
    }
  }

  // Update contract approval
  async updateApproval(approvalId, updateData) {
    try {
      const response = await api.put(`${CONTRACT_APPROVAL_API_BASE}/approvals/${approvalId}/update/`, updateData)
      return response.data
    } catch (error) {
      console.error('Error updating contract approval:', error)
      throw this.handleError(error)
    }
  }

  // Delete contract approval
  async deleteApproval(approvalId) {
    try {
      const response = await api.delete(`${CONTRACT_APPROVAL_API_BASE}/approvals/${approvalId}/delete/`)
      return response.data
    } catch (error) {
      console.error('Error deleting contract approval:', error)
      throw this.handleError(error)
    }
  }

  // Get contract approval statistics
  async getApprovalStats(params = {}) {
    try {
      const response = await api.get(`${CONTRACT_APPROVAL_API_BASE}/approvals/stats/`, { params })
      return response.data
    } catch (error) {
      console.error('Error fetching contract approval stats:', error)
      throw this.handleError(error)
    }
  }

  // Get approvals for specific contract
  async getContractApprovals(contractId, params = {}) {
    try {
      const response = await api.get(`${CONTRACT_APPROVAL_API_BASE}/contracts/${contractId}/approvals/`, { params })
      return response.data
    } catch (error) {
      console.error('Error fetching contract approvals:', error)
      throw this.handleError(error)
    }
  }

  // Create approval for specific contract
  async createContractApproval(contractId, approvalData) {
    try {
      const response = await api.post(`${CONTRACT_APPROVAL_API_BASE}/contracts/${contractId}/approvals/create/`, approvalData)
      return response.data
    } catch (error) {
      console.error('Error creating contract approval:', error)
      throw this.handleError(error)
    }
  }

  // Get approvals where user is the assigner (for review)
  async getAssignerApprovals(params = {}) {
    try {
      const response = await api.get(`${CONTRACT_APPROVAL_API_BASE}/assigner-approvals/`, { params })
      return response.data
    } catch (error) {
      console.error('Error fetching assigner approvals:', error)
      throw this.handleError(error)
    }
  }

  // Approve a contract
  async approveContract(approvalId) {
    try {
      const response = await api.post(`${CONTRACT_APPROVAL_API_BASE}/approvals/${approvalId}/approve/`)
      return response.data
    } catch (error) {
      console.error('Error approving contract:', error)
      throw this.handleError(error)
    }
  }

  // Reject a contract
  async rejectContract(approvalId, rejectionReason = '') {
    try {
      const response = await api.post(`${CONTRACT_APPROVAL_API_BASE}/approvals/${approvalId}/reject/`, {
        rejection_reason: rejectionReason
      })
      return response.data
    } catch (error) {
      console.error('Error rejecting contract:', error)
      throw this.handleError(error)
    }
  }

  // Error handling
  handleError(error) {
    if (error.response) {
      // Server responded with error status
      const { status, data } = error.response
      return {
        status,
        message: data.message || data.error || 'An error occurred',
        errors: data.errors || null
      }
    } else if (error.request) {
      // Request was made but no response received
      return {
        status: 0,
        message: 'Network error - please check your connection',
        errors: null
      }
    } else {
      // Something else happened
      return {
        status: -1,
        message: error.message || 'An unexpected error occurred',
        errors: null
      }
    }
  }
}

export default new ContractApprovalApi()
