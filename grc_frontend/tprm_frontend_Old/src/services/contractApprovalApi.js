import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'https://grc-tprm.vardaands.com/api/tprm',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Helper function to get stored token (check multiple keys)
const getStoredToken = () => {
  return localStorage.getItem('access_token') || 
         localStorage.getItem('session_token') || 
         localStorage.getItem('jwt_token')
}

// Add request interceptor to inject JWT token
api.interceptors.request.use(
  (config) => {
    const token = getStoredToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Helper function to refresh token
const refreshTokenIfNeeded = async () => {
  const refreshToken = localStorage.getItem('refresh_token')
  if (!refreshToken) {
    return null
  }

  try {
    const response = await axios.post(
      `${import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || 'https://grc-tprm.vardaands.com/api/tprm'}/jwt/refresh/`,
      { refresh: refreshToken }
    )
    
    if (response.data && response.data.access) {
      localStorage.setItem('access_token', response.data.access)
      if (response.data.refresh) {
        localStorage.setItem('refresh_token', response.data.refresh)
      }
      return response.data.access
    }
    return null
  } catch (error) {
    console.error('Token refresh failed:', error)
    return null
  }
}

// Add response interceptor to handle authentication and permission errors
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      // Token expired or invalid - try to refresh
      originalRequest._retry = true
      
      const newToken = await refreshTokenIfNeeded()
      if (newToken) {
        // Retry the original request with new token
        originalRequest.headers.Authorization = `Bearer ${newToken}`
        return api(originalRequest)
      } else {
        // Refresh failed - clear tokens and redirect to login
        localStorage.removeItem('access_token')
        localStorage.removeItem('session_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('current_user')
        if (window.location.pathname !== '/login') {
          window.location.href = '/login'
        }
      }
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
