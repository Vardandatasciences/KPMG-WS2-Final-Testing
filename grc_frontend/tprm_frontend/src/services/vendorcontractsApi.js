import axios from 'axios'
import { getTprmApiBaseUrl } from '@/utils/backendEnv'

const API_BASE_URL = getTprmApiBaseUrl()

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
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

// Add response interceptor for error handling
api.interceptors.response.use(
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

const vendorcontractsApi = {
  // Get all vendors with filtering and pagination
  async getVendors(params = {}) {
    try {
      const response = await api.get('/contracts/vendorcontracts/', { params })
      console.log('Vendors API response:', response.data)
      return {
        success: true,
        data: response.data.data,
        pagination: response.data.pagination
      }
    } catch (error) {
      console.error('Error fetching vendors:', error)
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to fetch vendors',
        message: error.response?.data?.message || error.message
      }
    }
  },

  // Get vendor details with contracts
  async getVendor(vendorId) {
    try {
      const response = await api.get(`/contracts/vendorcontracts/${vendorId}/`)
      return {
        success: true,
        data: response.data.data
      }
    } catch (error) {
      console.error('Error fetching vendor:', error)
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to fetch vendor',
        message: error.response?.data?.message || error.message
      }
    }
  },

  // Get vendor statistics
  async getVendorStats() {
    try {
      const response = await api.get('/contracts/vendorcontracts/stats/')
      console.log('Vendor stats API response:', response.data)
      return {
        success: true,
        data: response.data.data
      }
    } catch (error) {
      console.error('Error fetching vendor stats:', error)
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to fetch vendor statistics',
        message: error.response?.data?.message || error.message
      }
    }
  },

  // Get vendor contacts
  async getVendorContacts(vendorId, params = {}) {
    try {
      const response = await api.get(`/contracts/vendorcontracts/${vendorId}/contacts/`, { params })
      return {
        success: true,
        data: response.data.data
      }
    } catch (error) {
      console.error('Error fetching vendor contacts:', error)
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to fetch vendor contacts',
        message: error.response?.data?.message || error.message
      }
    }
  },

  // Create vendor contact
  async createVendorContact(vendorId, contactData) {
    try {
      const response = await api.post(`/contracts/vendorcontracts/${vendorId}/contacts/create/`, contactData)
      return {
        success: true,
        data: response.data.data,
        message: response.data.message
      }
    } catch (error) {
      console.error('Error creating vendor contact:', error)
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to create vendor contact',
        message: error.response?.data?.message || error.message
      }
    }
  },

  // Search vendors
  async searchVendors(searchParams) {
    try {
      const response = await api.get('/contracts/vendorcontracts/', { params: searchParams })
      return {
        success: true,
        data: response.data.data,
        pagination: response.data.pagination
      }
    } catch (error) {
      console.error('Error searching vendors:', error)
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to search vendors',
        message: error.response?.data?.message || error.message
      }
    }
  },

  // Get comprehensive contract details including terms, clauses, and sub-contracts
  async getContractComprehensiveDetail(contractId) {
    try {
      const response = await api.get(`/contracts/contracts/${contractId}/comprehensive/`)
      return {
        success: true,
        data: response.data.data
      }
    } catch (error) {
      console.error('Error fetching comprehensive contract details:', error)
      return {
        success: false,
        error: error.response?.data?.error || 'Failed to fetch contract details',
        message: error.response?.data?.message || error.message
      }
    }
  },

  // Get contract approvals for a specific contract
  async getContractApprovals(contractId) {
    try {
      const response = await api.get(`/contracts/approvals/get-contract-approvals/`, {
        params: { object_id: contractId, object_type: 'CONTRACT_CREATION' }
      })
      return {
        success: true,
        data: response.data.data
      }
    } catch (error) {
      console.error('Error fetching contract approvals:', error)
      return {
        success: false,
        message: error.response?.data?.message || 'Failed to fetch contract approvals'
      }
    }
  },

  // Update contract approval
  async updateContractApproval(approvalId, data) {
    try {
      const response = await api.put(`/contracts/approvals/approvals/${approvalId}/update/`, data)
      return {
        success: true,
        data: response.data.data
      }
    } catch (error) {
      console.error('Error updating contract approval:', error)
      return {
        success: false,
        message: error.response?.data?.message || 'Failed to update contract approval'
      }
    }
  },

  // Create contract approval
  async createContractApproval(data) {
    try {
      const response = await api.post(`/contracts/approvals/approvals/create/`, data)
      return {
        success: true,
        data: response.data.data
      }
    } catch (error) {
      console.error('Error creating contract approval:', error)
      return {
        success: false,
        message: error.response?.data?.message || 'Failed to create contract approval'
      }
    }
  }
}

export default vendorcontractsApi