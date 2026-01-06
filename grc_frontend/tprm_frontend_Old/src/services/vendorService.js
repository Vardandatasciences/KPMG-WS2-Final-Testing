import axios from 'axios'
import { getTprmApiBaseUrl } from '@/utils/backendEnv'

// Use environment-aware URL resolution - defaults to production
const API_BASE_URL = getTprmApiBaseUrl()

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
    // Add JWT token from localStorage (using session_token key)
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
    console.error('API Error:', error.response?.data || error.message)
    
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
      
      console.error(`[VendorService] Permission denied: ${permissionType}`, error.response.data)
      
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

const vendorService = {
  // Get all vendors with optional search and filtering
  async getVendors(params = {}) {
    try {
      const response = await apiClient.get('/vendors/', { params })
      return response.data
    } catch (error) {
      throw new Error(`Failed to fetch vendors: ${error.response?.data?.detail || error.message}`)
    }
  },

  // Get active vendors (approved vendors with primary contacts)
  async getActiveVendors() {
    try {
      const response = await apiClient.get('/vendors/active')
      return response.data
    } catch (error) {
      throw new Error(`Failed to fetch active vendors: ${error.response?.data?.detail || error.message}`)
    }
  },

  // Get vendor by ID
  async getVendorById(vendorId) {
    try {
      const response = await apiClient.get(`/vendors/${vendorId}/`)
      return response.data
    } catch (error) {
      throw new Error(`Failed to fetch vendor: ${error.response?.data?.detail || error.message}`)
    }
  },

  // Create new vendor
  async createVendor(vendorData) {
    try {
      const response = await apiClient.post('/vendors/', vendorData)
      return response.data
    } catch (error) {
      throw new Error(`Failed to create vendor: ${error.response?.data?.detail || error.message}`)
    }
  },

  // Update vendor
  async updateVendor(vendorId, vendorData) {
    try {
      const response = await apiClient.put(`/vendors/${vendorId}/`, vendorData)
      return response.data
    } catch (error) {
      throw new Error(`Failed to update vendor: ${error.response?.data?.detail || error.message}`)
    }
  },

  // Delete vendor
  async deleteVendor(vendorId) {
    try {
      const response = await apiClient.delete(`/vendors/${vendorId}/`)
      return response.data
    } catch (error) {
      throw new Error(`Failed to delete vendor: ${error.response?.data?.detail || error.message}`)
    }
  },

  // Bulk upload vendors from CSV
  async bulkUploadVendors(csvFile) {
    try {
      const formData = new FormData()
      formData.append('csv_file', csvFile)
      
      const response = await apiClient.post('/vendors/bulk_upload/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      return response.data
    } catch (error) {
      throw new Error(`Failed to bulk upload vendors: ${error.response?.data?.detail || error.message}`)
    }
  },

  // Get vendor categories
  async getVendorCategories() {
    try {
      const response = await apiClient.get('/vendor-categories/')
      return response.data
    } catch (error) {
      throw new Error(`Failed to fetch vendor categories: ${error.response?.data?.detail || error.message}`)
    }
  },

  // Get RFP vendor selections
  async getRFPVendorSelections(rfpId) {
    try {
      const response = await apiClient.get('/vendor-selections/', {
        params: { rfp_id: rfpId }
      })
      return response.data
    } catch (error) {
      throw new Error(`Failed to fetch vendor selections: ${error.response?.data?.detail || error.message}`)
    }
  },

  // Select existing vendors for RFP
  async selectExistingVendors(rfpId, vendorIds, matchScores = {}) {
    try {
      const response = await apiClient.post('/vendor-selections/select_existing_vendors/', {
        rfp_id: rfpId,
        vendor_ids: vendorIds,
        match_scores: matchScores
      })
      return response.data
    } catch (error) {
      throw new Error(`Failed to select vendors: ${error.response?.data?.detail || error.message}`)
    }
  },

  // Create manual vendor and select for RFP
  async createManualVendor(rfpId, vendorData, matchScore) {
    try {
      const response = await apiClient.post('/vendor-selections/create_manual_vendor/', {
        rfp_id: rfpId,
        vendor_data: vendorData,
        match_score: matchScore
      })
      return response.data
    } catch (error) {
      throw new Error(`Failed to create manual vendor: ${error.response?.data?.detail || error.message}`)
    }
  },

  // Get unmatched vendors
  async getUnmatchedVendors() {
    try {
      const response = await apiClient.get('/unmatched-vendors/')
      return response.data
    } catch (error) {
      throw new Error(`Failed to fetch unmatched vendors: ${error.response?.data?.detail || error.message}`)
    }
  },

  // Search vendors with advanced filters
  async searchVendors(searchParams) {
    try {
      const response = await apiClient.get('/vendors/', { params: searchParams })
      return response.data
    } catch (error) {
      throw new Error(`Failed to search vendors: ${error.response?.data?.detail || error.message}`)
    }
  }
}

module.exports = {
  vendorService,
  default: vendorService
}
