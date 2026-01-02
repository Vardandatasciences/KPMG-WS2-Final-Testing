/**
 * RFP API Composable
 * Provides authenticated API calls for RFP operations
 */

import { getApiV1BaseUrl, getApiV1Url } from '@/utils/backendEnv.js'

const API_BASE_URL = getApiV1BaseUrl()

const buildApiUrl = (path = '') => getApiV1Url(path)

export function useRfpApi() {
  /**
   * Get authentication headers with JWT token
   */
  const getAuthHeaders = () => {
    const token = localStorage.getItem('session_token') || 
                  localStorage.getItem('auth_token') || 
                  localStorage.getItem('access_token')
    
    return {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
    }
  }

  /**
   * Handle API response and errors
   */
  const handleResponse = async (response) => {
    // Handle 401 Unauthorized
    if (response.status === 401) {
      localStorage.removeItem('session_token')
      localStorage.removeItem('auth_token')
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('current_user')
      
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
      throw new Error('Authentication required')
    }
    
    // Handle 403 Forbidden
    if (response.status === 403) {
      const errorData = await response.json().catch(() => ({}))
      const errorMessage = errorData?.error || errorData?.message || 'You do not have permission to access this resource.'
      const errorCode = errorData?.code || '403'
      
      sessionStorage.setItem('access_denied_error', JSON.stringify({
        message: errorMessage,
        code: errorCode,
        timestamp: new Date().toISOString(),
        path: window.location.pathname
      }))
      
      console.log('🔄 Redirecting to /access-denied page...')
      window.location.href = '/access-denied'
      // Return a never-resolving promise to stop execution
      return new Promise(() => {})
    }
    
    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`HTTP error! status: ${response.status} - ${errorText}`)
    }
    
    return response.json()
  }

  /**
   * Fetch all RFPs
   */
  const fetchRFPs = async (filters = {}) => {
    // Remove empty/null filters
    const cleanFilters = Object.fromEntries(
      Object.entries(filters).filter(([_, v]) => v !== null && v !== undefined && v !== '')
    )
    const queryParams = new URLSearchParams(cleanFilters).toString()
    
    // The router registers 'rfps' under /api/v1/rfps/, so the full path is /api/v1/rfps/rfps/
    // But we want /api/v1/rfps/ directly, so we use the router's base path
    const url = buildApiUrl(`/rfps/${queryParams ? `?${queryParams}` : ''}`)
    
    console.log('[useRfpApi] Fetching RFPs from URL:', url)
    console.log('[useRfpApi] Filters:', cleanFilters)
    
    const response = await fetch(url, {
      method: 'GET',
      headers: getAuthHeaders(),
    })
    
    const data = await handleResponse(response)
    console.log('[useRfpApi] Response received:', {
      type: typeof data,
      isArray: Array.isArray(data),
      keys: data && typeof data === 'object' ? Object.keys(data) : null,
      count: data?.count,
      resultsLength: data?.results?.length,
      hasResults: !!data?.results,
      fullResponse: data
    })
    
    return data
  }

  /**
   * Fetch single RFP by ID
   */
  const fetchRFP = async (rfpId) => {
    const response = await fetch(buildApiUrl(`/rfps/${rfpId}/`), {
      method: 'GET',
      headers: getAuthHeaders(),
    })
    
    return handleResponse(response)
  }

  /**
   * Create new RFP
   */
  const createRFP = async (rfpData) => {
    const response = await fetch(buildApiUrl('/rfps/'), {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(rfpData),
    })
    
    return handleResponse(response)
  }

  /**
   * Update existing RFP
   */
  const updateRFP = async (rfpId, rfpData) => {
    const response = await fetch(buildApiUrl(`/rfps/${rfpId}/`), {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify(rfpData),
    })
    
    return handleResponse(response)
  }

  /**
   * Delete RFP
   */
  const deleteRFP = async (rfpId) => {
    const response = await fetch(buildApiUrl(`/rfps/${rfpId}/`), {
      method: 'DELETE',
      headers: getAuthHeaders(),
    })
    
    if (!response.ok) {
      return handleResponse(response)
    }
    
    return true
  }

  /**
   * Get RFP full details
   */
  const getRFPFullDetails = async (rfpId) => {
    const response = await fetch(buildApiUrl(`/rfps/${rfpId}/get_full_details/`), {
      method: 'GET',
      headers: getAuthHeaders(),
    })
    
    return handleResponse(response)
  }

  /**
   * Download RFP document
   */
  const downloadRFPDocument = async (rfpId, format = 'pdf') => {
    const endpoint = format === 'pdf' 
      ? buildApiUrl(`/rfps/${rfpId}/download/pdf/`)
      : buildApiUrl(`/rfps/${rfpId}/download/word/`)
    
    const response = await fetch(endpoint, {
      method: 'GET',
      headers: getAuthHeaders(),
    })
    
    if (!response.ok) {
      throw new Error(`Failed to download ${format.toUpperCase()} document`)
    }
    
    return response.blob()
  }

  /**
   * Fetch vendors
   */
  const fetchVendors = async () => {
    const response = await fetch(buildApiUrl('/vendors/active/'), {
      method: 'GET',
      headers: getAuthHeaders(),
    })
    
    return handleResponse(response)
  }

  return {
    fetchRFPs,
    fetchRFP,
    createRFP,
    updateRFP,
    deleteRFP,
    getRFPFullDetails,
    downloadRFPDocument,
    fetchVendors,
    getAuthHeaders,
    buildApiUrl,
    API_BASE_URL,
  }
}

