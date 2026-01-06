import axios from 'axios'
import { getTprmApiBaseUrl } from '@/utils/backendEnv'

// Create axios instance with default configuration
const api = axios.create({
  baseURL: getTprmApiBaseUrl(),
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add request interceptor to prevent infinite retries
api.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Add response interceptor to handle errors gracefully
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    // If it's a connection error, don't retry
    if (error.code === 'ECONNREFUSED' || error.code === 'ERR_NETWORK') {
      console.warn('Backend server is not available:', error.message)
      // Return a mock response to prevent infinite loops
      return Promise.resolve({
        data: {
          total: 0,
          page: 1,
          page_size: 20,
          grouped_results: {},
          entity_type_counts: {},
          facets: { modules: {} },
          query_time: 0,
          query: '',
          error: 'Backend server is not available. Please start the Django server.'
        }
      })
    }
    return Promise.reject(error)
  }
)

// Global Search API
export const searchAPI = {
  search: async (query) => {
    const response = await api.post('/global-search/query/', query)
    return response.data
  },
  
  getStats: async () => {
    const response = await api.get('/global-search/stats/')
    return response.data
  },
  
  // New Dashboard Analytics endpoints
  getDashboardAnalytics: async () => {
    const response = await api.get('/global-search/dashboard-analytics/')
    return response.data
  },
  
  getLiveUpdates: async () => {
    const response = await api.get('/global-search/live-updates/')
    return response.data
  },
  
  updateIndex: async (data) => {
    const response = await api.post('/global-search/index/update/', data)
    return response.data
  },
  
  bulkUpdateIndex: async (data) => {
    const response = await api.post('/global-search/index/bulk-update/', data)
    return response.data
  },
  
  deleteIndexEntry: async (entityType, entityId) => {
    const response = await api.delete('/global-search/index/delete/', {
      data: { entity_type: entityType, entity_id: entityId }
    })
    return response.data
  },
  
  getSearchHistory: async (page = 1, pageSize = 1000) => {
    const response = await api.get('/global-search/history/', {
      params: { page, page_size: pageSize }
    })
    return response.data
  },
  
  clearSearchHistory: async () => {
    await api.delete('/global-search/history/')
  },
  
  getFilterOptions: async () => {
    const response = await api.get('/global-search/filter-options/')
    return response.data
  },
}

// Vendor API
export const vendorAPI = {
  getVendors: async (params) => {
    const response = await api.get('/vendor/vendors/', { params })
    return response.data
  },
  
  getVendor: async (id) => {
    const response = await api.get(`/vendor/vendors/${id}/`)
    return response.data
  },
  
  createVendor: async (data) => {
    const response = await api.post('/vendor/vendors/', data)
    return response.data
  },
  
  updateVendor: async (id, data) => {
    const response = await api.put(`/vendor/vendors/${id}/`, data)
    return response.data
  },
  
  deleteVendor: async (id) => {
    await api.delete(`/vendor/vendors/${id}/`)
  },
}

// RFP API
export const rfpAPI = {
  getRFPs: async (params) => {
    const response = await api.get('/rfp/rfps/', { params })
    return response.data
  },
  
  getRFP: async (id) => {
    const response = await api.get(`/rfp/rfps/${id}/`)
    return response.data
  },
  
  createRFP: async (data) => {
    const response = await api.post('/rfp/rfps/', data)
    return response.data
  },
  
  updateRFP: async (id, data) => {
    const response = await api.put(`/rfp/rfps/${id}/`, data)
    return response.data
  },
  
  deleteRFP: async (id) => {
    await api.delete(`/rfp/rfps/${id}/`)
  },
}

// Contract API
export const contractAPI = {
  getContracts: async (params) => {
    const response = await api.get('/contract/contracts/', { params })
    return response.data
  },
  
  getContract: async (id) => {
    const response = await api.get(`/contract/contracts/${id}/`)
    return response.data
  },
  
  createContract: async (data) => {
    const response = await api.post('/contract/contracts/', data)
    return response.data
  },
  
  updateContract: async (id, data) => {
    const response = await api.put(`/contract/contracts/${id}/`, data)
    return response.data
  },
  
  deleteContract: async (id) => {
    await api.delete(`/contract/contracts/${id}/`)
  },
}

// SLA API
export const slaAPI = {
  getSLAs: async (params) => {
    const response = await api.get('/sla/slas/', { params })
    return response.data
  },
  
  getSLA: async (id) => {
    const response = await api.get(`/sla/slas/${id}/`)
    return response.data
  },
  
  createSLA: async (data) => {
    const response = await api.post('/sla/slas/', data)
    return response.data
  },
  
  updateSLA: async (id, data) => {
    const response = await api.put(`/sla/slas/${id}/`, data)
    return response.data
  },
  
  deleteSLA: async (id) => {
    await api.delete(`/sla/slas/${id}/`)
  },
}

// BCP/DRP API
export const bcpDrpAPI = {
  getPlans: async (params) => {
    const response = await api.get('/bcp-drp/plans/', { params })
    return response.data
  },
  
  getPlan: async (id) => {
    const response = await api.get(`/bcp-drp/plans/${id}/`)
    return response.data
  },
  
  createPlan: async (data) => {
    const response = await api.post('/bcp-drp/plans/', data)
    return response.data
  },
  
  updatePlan: async (id, data) => {
    const response = await api.put(`/bcp-drp/plans/${id}/`, data)
    return response.data
  },
  
  deletePlan: async (id) => {
    await api.delete(`/bcp-drp/plans/${id}/`)
  },
}

export default api
