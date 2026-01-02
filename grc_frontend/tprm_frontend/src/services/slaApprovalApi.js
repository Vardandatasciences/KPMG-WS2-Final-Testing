import apiService from './api'
import { getTprmApiUrl } from '@/utils/backendEnv'

class SLAApprovalApiService {
  constructor() {
    this.baseURL = getTprmApiUrl('slas/approvals')
  }

  async slaApprovalRequest(endpoint, options = {}) {
    try {
      // Get JWT token from localStorage
      const token = localStorage.getItem('session_token')
      const headers = {
        'Content-Type': 'application/json',
        ...options.headers
      }
      
      // Add Authorization header if token exists
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }
      
      const response = await fetch(`${this.baseURL}${endpoint}`, {
        headers: headers,
        ...options
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(`HTTP error! status: ${response.status} - ${JSON.stringify(errorData)}`)
      }

      return await response.json()
    } catch (error) {
      console.error('SLA Approval API request failed:', error)
      throw error
    }
  }

  // Get all SLA approvals with optional filters
  async getApprovals(filters = {}) {
    const queryParams = new URLSearchParams()
    
    Object.keys(filters).forEach(key => {
      if (filters[key] !== null && filters[key] !== undefined && filters[key] !== '') {
        queryParams.append(key, filters[key])
      }
    })
    
    const queryString = queryParams.toString()
    const endpoint = queryString ? `/approvals/?${queryString}` : '/approvals/'
    
    return this.slaApprovalRequest(endpoint)
  }

  // Get SLA approval by ID
  async getApproval(approvalId) {
    return this.slaApprovalRequest(`/approvals/${approvalId}/`)
  }

  // Create new SLA approval
  async createApproval(approvalData) {
    return this.slaApprovalRequest('/approvals/create/', {
      method: 'POST',
      body: JSON.stringify(approvalData)
    })
  }

  // Create multiple SLA approvals
  async bulkCreateApprovals(approvalsData) {
    return this.slaApprovalRequest('/approvals/bulk-create/', {
      method: 'POST',
      body: JSON.stringify(approvalsData)
    })
  }

  // Update SLA approval
  async updateApproval(approvalId, updateData) {
    return this.slaApprovalRequest(`/approvals/${approvalId}/update/`, {
      method: 'PUT',
      body: JSON.stringify(updateData)
    })
  }

  // Delete SLA approval
  async deleteApproval(approvalId) {
    return this.slaApprovalRequest(`/approvals/${approvalId}/delete/`, {
      method: 'DELETE'
    })
  }

  // Get SLA approval statistics
  async getApprovalStats(filters = {}) {
    const queryParams = new URLSearchParams()
    
    Object.keys(filters).forEach(key => {
      if (filters[key] !== null && filters[key] !== undefined && filters[key] !== '') {
        queryParams.append(key, filters[key])
      }
    })
    
    const queryString = queryParams.toString()
    const endpoint = queryString ? `/approvals/stats/?${queryString}` : '/approvals/stats/'
    
    return this.slaApprovalRequest(endpoint)
  }

  // Get approvals for a specific SLA
  async getSLAApprovals(slaId, filters = {}) {
    const queryParams = new URLSearchParams()
    
    Object.keys(filters).forEach(key => {
      if (filters[key] !== null && filters[key] !== undefined && filters[key] !== '') {
        queryParams.append(key, filters[key])
      }
    })
    
    const queryString = queryParams.toString()
    const endpoint = queryString ? `/slas/${slaId}/approvals/?${queryString}` : `/slas/${slaId}/approvals/`
    
    return this.slaApprovalRequest(endpoint)
  }

  // Get approvals where user is the assigner (for review)
  async getAssignerApprovals(filters = {}) {
    const queryParams = new URLSearchParams()
    
    Object.keys(filters).forEach(key => {
      if (filters[key] !== null && filters[key] !== undefined && filters[key] !== '') {
        queryParams.append(key, filters[key])
      }
    })
    
    const queryString = queryParams.toString()
    const endpoint = queryString ? `/assigner-approvals/?${queryString}` : '/assigner-approvals/'
    
    return this.slaApprovalRequest(endpoint)
  }

  // Get all approvals (admin view) - same as getApprovals but with admin context
  async getAllApprovals(filters = {}) {
    return this.getApprovals(filters)
  }

  // Get all reviews (admin view) - same as getAssignerApprovals but with admin context
  async getAllReviews(filters = {}) {
    return this.getAssignerApprovals(filters)
  }

  // Approve SLA
  async approveSLA(approvalId) {
    return this.slaApprovalRequest(`/approvals/${approvalId}/approve/`, {
      method: 'POST'
    })
  }

  // Reject SLA
  async rejectSLA(approvalId, rejectionReason = '') {
    return this.slaApprovalRequest(`/approvals/${approvalId}/reject/`, {
      method: 'POST',
      body: JSON.stringify({ rejection_reason: rejectionReason })
    })
  }

  // Get all SLAs with optional filters
  async getSLAs(filters = {}) {
    const queryParams = new URLSearchParams()
    
    Object.keys(filters).forEach(key => {
      if (filters[key] !== null && filters[key] !== undefined && filters[key] !== '') {
        queryParams.append(key, filters[key])
      }
    })
    
    const queryString = queryParams.toString()
    const endpoint = queryString ? `/api/slas/?${queryString}` : '/api/slas/'
    
    const token = localStorage.getItem('session_token')
    const headers = {
      'Content-Type': 'application/json'
    }
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
    
    return fetch(endpoint, {
      headers: headers
    }).then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      return response.json()
    })
  }

  // Get SLAs with PENDING approval status
  async getPendingSLAs(filters = {}) {
    const queryParams = new URLSearchParams()
    
    // Always filter for PENDING approval status
    queryParams.append('approval_status', 'PENDING')
    
    Object.keys(filters).forEach(key => {
      if (filters[key] !== null && filters[key] !== undefined && filters[key] !== '') {
        queryParams.append(key, filters[key])
      }
    })
    
    const queryString = queryParams.toString()
    const endpoint = queryString ? `/api/slas/?${queryString}` : '/api/slas/?approval_status=PENDING'
    
    const token = localStorage.getItem('session_token')
    const headers = {
      'Content-Type': 'application/json'
    }
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
    
    return fetch(endpoint, {
      headers: headers
    }).then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      return response.json()
    })
  }

  // Get all SLAs (both pending and approved) for display
  async getAllSLAs(filters = {}) {
    const queryParams = new URLSearchParams()
    
    Object.keys(filters).forEach(key => {
      if (filters[key] !== null && filters[key] !== undefined && filters[key] !== '') {
        queryParams.append(key, filters[key])
      }
    })
    
    const queryString = queryParams.toString()
    const endpoint = queryString ? `/api/slas/?${queryString}` : '/api/slas/'
    
    const token = localStorage.getItem('session_token')
    const headers = {
      'Content-Type': 'application/json'
    }
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
    
    return fetch(endpoint, {
      headers: headers
    }).then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      return response.json()
    })
  }

  // Get vendors
  async getVendors(filters = {}) {
    const queryParams = new URLSearchParams()
    
    Object.keys(filters).forEach(key => {
      if (filters[key] !== null && filters[key] !== undefined && filters[key] !== '') {
        queryParams.append(key, filters[key])
      }
    })
    
    const queryString = queryParams.toString()
    const endpoint = queryString ? `/api/slas/vendors/?${queryString}` : '/api/slas/vendors/'
    
    const token = localStorage.getItem('session_token')
    const headers = {
      'Content-Type': 'application/json'
    }
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
    
    return fetch(endpoint, {
      headers: headers
    }).then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      return response.json()
    })
  }

  // Get users for assignment (users with ApproveContract permission)
  async getUsers(filters = {}) {
    return this.slaApprovalRequest('/available-users/')
  }

  // Health check
  async healthCheck() {
    return this.slaApprovalRequest('/health/')
  }
}

export default new SLAApprovalApiService()
