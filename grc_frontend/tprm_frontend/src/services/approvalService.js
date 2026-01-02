import axios from 'axios'

const API_BASE_URL = process.env.VUE_APP_API_URL || 'http://localhost:3000/api'

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add request interceptor to handle authentication
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token if available
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

// Add response interceptor to handle errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
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

const approvalService = {
  // Get all users
  async getUsers() {
    try {
      const response = await apiClient.get('/approval/users/')
      return response.data
    } catch (error) {
      throw new Error(`Failed to fetch users: ${error.response?.data?.detail || error.message}`)
    }
  },

  // Get all approval requests
  async getApprovalRequests() {
    try {
      const response = await apiClient.get('/approval/requests/')
      return response.data
    } catch (error) {
      throw new Error(`Failed to fetch approval requests: ${error.response?.data?.detail || error.message}`)
    }
  },

  // Get approval requests by user ID
  async getApprovalRequestsByUser(userId) {
    try {
      const response = await apiClient.get(`/approval/requests/user/${userId}/`)
      return response.data
    } catch (error) {
      throw new Error(`Failed to fetch approval requests for user: ${error.response?.data?.detail || error.message}`)
    }
  },

  // Get approval stages by user ID (this is the key method for your requirement)
  async getApprovalStagesByUser(userId) {
    try {
      const response = await apiClient.get(`/approval/stages/user/${userId}/`)
      return response.data
    } catch (error) {
      throw new Error(`Failed to fetch approval stages for user: ${error.response?.data?.detail || error.message}`)
    }
  },

  // Get approval stages for a specific approval
  async getApprovalStages(approvalId) {
    try {
      const response = await apiClient.get(`/approval/stages/${approvalId}/`)
      return response.data
    } catch (error) {
      throw new Error(`Failed to fetch approval stages: ${error.response?.data?.detail || error.message}`)
    }
  },

  // Approve a stage
  async approveStage(stageId, data) {
    try {
      await apiClient.post(`/approval/stages/${stageId}/approve/`, data)
    } catch (error) {
      throw new Error(`Failed to approve stage: ${error.response?.data?.detail || error.message}`)
    }
  },

  // Reject a stage
  async rejectStage(stageId, rejectionReason) {
    try {
      await apiClient.post(`/approval/stages/${stageId}/reject/`, {
        rejection_reason: rejectionReason,
        rejected_at: new Date().toISOString()
      })
    } catch (error) {
      throw new Error(`Failed to reject stage: ${error.response?.data?.detail || error.message}`)
    }
  },

  // Get approval request by ID
  async getApprovalRequestById(approvalId) {
    try {
      const response = await apiClient.get(`/approval/requests/${approvalId}/`)
      return response.data
    } catch (error) {
      throw new Error(`Failed to fetch approval request: ${error.response?.data?.detail || error.message}`)
    }
  },

  // Create new approval request
  async createApprovalRequest(data) {
    try {
      const response = await apiClient.post('/approval/requests/', data)
      return response.data
    } catch (error) {
      throw new Error(`Failed to create approval request: ${error.response?.data?.detail || error.message}`)
    }
  },

  // Update approval request
  async updateApprovalRequest(approvalId, data) {
    try {
      const response = await apiClient.put(`/approval/requests/${approvalId}/`, data)
      return response.data
    } catch (error) {
      throw new Error(`Failed to update approval request: ${error.response?.data?.detail || error.message}`)
    }
  },

  // Delete approval request
  async deleteApprovalRequest(approvalId) {
    try {
      await apiClient.delete(`/approval/requests/${approvalId}/`)
    } catch (error) {
      throw new Error(`Failed to delete approval request: ${error.response?.data?.detail || error.message}`)
    }
  },

  // Get all approval workflows
  async getApprovalWorkflows() {
    try {
      const response = await apiClient.get('/approval/workflows/')
      return response.data
    } catch (error) {
      throw new Error(`Failed to fetch approval workflows: ${error.response?.data?.detail || error.message}`)
    }
  },

  // Get approval workflows by creator
  async getApprovalWorkflowsByCreator(createdBy) {
    try {
      const response = await apiClient.get(`/approval/workflows/?created_by=${createdBy}`)
      return response.data
    } catch (error) {
      throw new Error(`Failed to fetch approval workflows by creator: ${error.response?.data?.detail || error.message}`)
    }
  },

  // Get approval workflow by ID
  async getApprovalWorkflowById(workflowId) {
    try {
      const response = await apiClient.get(`/approval/workflows/${workflowId}/`)
      return response.data
    } catch (error) {
      throw new Error(`Failed to fetch approval workflow: ${error.response?.data?.detail || error.message}`)
    }
  },

  // Update approval workflow
  async updateApprovalWorkflow(workflowId, data) {
    try {
      const response = await apiClient.patch(`/approval/workflows/${workflowId}/`, data)
      return response.data
    } catch (error) {
      throw new Error(`Failed to update approval workflow: ${error.response?.data?.detail || error.message}`)
    }
  },

  // Get workflow changes/history
  async getWorkflowChanges(workflowId) {
    try {
      const response = await apiClient.get(`/approval/workflows/${workflowId}/changes/`)
      return response.data
    } catch (error) {
      throw new Error(`Failed to fetch workflow changes: ${error.response?.data?.detail || error.message}`)
    }
  },

  // Create new approval workflow
  async createApprovalWorkflow(data) {
    try {
      const response = await apiClient.post('/approval/workflows/', data)
      return response.data
    } catch (error) {
      throw new Error(`Failed to create approval workflow: ${error.response?.data?.detail || error.message}`)
    }
  },

  // Delete approval workflow
  async deleteApprovalWorkflow(workflowId) {
    try {
      await apiClient.delete(`/approval/workflows/${workflowId}/`)
    } catch (error) {
      throw new Error(`Failed to delete approval workflow: ${error.response?.data?.detail || error.message}`)
    }
  }
}

module.exports = {
  approvalService,
  default: approvalService
}
