import apiService from './api'
import { getTprmApiUrl } from '@/utils/backendEnv'

class SLAApprovalApiService {
  constructor() {
    this.baseURL = getTprmApiUrl('slas/approvals')
  }

  async slaApprovalRequest(endpoint, options = {}) {
    try {
      // Get JWT token from localStorage (try multiple possible keys)
      const token = localStorage.getItem('session_token') || 
                    localStorage.getItem('access_token') ||
                    localStorage.getItem('jwt_token')
      
      const headers = {
        'Content-Type': 'application/json',
        ...options.headers
      }
      
      // Add Authorization header if token exists
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }
      
      // Construct full URL
      const fullUrl = `${this.baseURL}${endpoint}`
      console.log('[SLA Approval API] Request:', {
        method: options.method || 'GET',
        url: fullUrl,
        hasToken: !!token,
        endpoint,
        baseURL: this.baseURL
      })
      
      const response = await fetch(fullUrl, {
        headers: headers,
        ...options
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        console.error('[SLA Approval API] Error response:', {
          status: response.status,
          statusText: response.statusText,
          errorData
        })
        throw new Error(`HTTP error! status: ${response.status} - ${JSON.stringify(errorData)}`)
      }

      const data = await response.json()
      console.log('[SLA Approval API] Success:', { url: fullUrl, dataKeys: Object.keys(data) })
      return data
    } catch (error) {
      // Handle network errors (connection refused, etc.)
      if (error.message.includes('Failed to fetch') || error.message.includes('ERR_CONNECTION_REFUSED')) {
        console.error('[SLA Approval API] Connection error - Backend server may not be running:', {
          url: `${this.baseURL}${endpoint}`,
          error: error.message
        })
        throw new Error(`Cannot connect to backend server. Please ensure the backend is running at ${this.baseURL}`)
      }
      console.error('[SLA Approval API] Request failed:', error)
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
    // baseURL already includes 'slas/approvals', so endpoint should be just the ID
    // Backend expects: /api/tprm/slas/approvals/approvals/<int:pk>/
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
    // Use the main API service which has the correct base URL
    const apiService = (await import('./api')).default
    const response = await apiService.getSLAs()
    
    // Apply filters client-side if needed (backend should handle this, but fallback)
    let filtered = response.results || response || []
    
    if (Object.keys(filters).length > 0) {
      filtered = filtered.filter(sla => {
        return Object.keys(filters).every(key => {
          const filterValue = filters[key]
          if (filterValue === null || filterValue === undefined || filterValue === '') {
            return true
          }
          const slaValue = sla[key]
          return slaValue != null && String(slaValue).toLowerCase().includes(String(filterValue).toLowerCase())
        })
      })
    }
    
    return {
      results: filtered,
      count: filtered.length
    }
  }
  
  // Get a single SLA by ID
  async getSLAById(slaId) {
    const apiService = (await import('./api')).default
    return apiService.getSLA(slaId)
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
    // Use the main API service which has the correct base URL
    const apiService = (await import('./api')).default
    const response = await apiService.getSLAs()
    
    // Apply filters client-side if needed (backend should handle this, but fallback)
    let filtered = response.results || response || []
    
    if (Object.keys(filters).length > 0) {
      filtered = filtered.filter(sla => {
        return Object.keys(filters).every(key => {
          const filterValue = filters[key]
          if (filterValue === null || filterValue === undefined || filterValue === '') {
            return true
          }
          const slaValue = sla[key]
          return slaValue != null && String(slaValue).toLowerCase().includes(String(filterValue).toLowerCase())
        })
      })
    }
    
    return {
      results: filtered,
      count: filtered.length
    }
  }

  // Get vendors
  async getVendors(filters = {}) {
    // Use the main API service which has the correct base URL
    const apiService = (await import('./api')).default
    const response = await apiService.getVendors()
    
    // Apply filters client-side if needed
    let filtered = response.results || response || []
    
    if (Object.keys(filters).length > 0) {
      filtered = filtered.filter(vendor => {
        return Object.keys(filters).every(key => {
          const filterValue = filters[key]
          if (filterValue === null || filterValue === undefined || filterValue === '') {
            return true
          }
          const vendorValue = vendor[key]
          return vendorValue != null && String(vendorValue).toLowerCase().includes(String(filterValue).toLowerCase())
        })
      })
    }
    
    return {
      results: filtered,
      count: filtered.length
    }
  }

  // Get users for assignment (users with ApproveContract permission)
  async getUsers(filters = {}) {
    try {
      const response = await this.slaApprovalRequest('/available-users/')
      // Ensure consistent response format
      if (response && response.success !== undefined) {
        return response
      } else if (Array.isArray(response)) {
        return {
          success: true,
          data: response,
          count: response.length
        }
      } else {
        return {
          success: true,
          data: response.data || response.results || [],
          count: (response.data || response.results || []).length
        }
      }
    } catch (error) {
      console.error('Error fetching users:', error)
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to fetch users',
        message: error.response?.data?.message || error.message,
        data: []
      }
    }
  }

  // Health check
  async healthCheck() {
    return this.slaApprovalRequest('/health/')
  }
}

export default new SLAApprovalApiService()
