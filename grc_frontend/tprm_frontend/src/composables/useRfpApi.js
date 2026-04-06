/**
 * RFP API Composable
 * Provides authenticated API calls for RFP operations
 */

import { getApiV1BaseUrl, getApiV1Url, getTprmApiUrl } from '@/utils/backendEnv.js'
import { getParentPostMessageTargetOrigin } from '@/utils/parentPostMessageOrigin.js'

const API_BASE_URL = getApiV1BaseUrl()

// MULTI-TENANCY: Use TPRM API URL for RFP endpoints
// Backend router is at /api/tprm/rfp/, and router.register('rfps') creates /api/tprm/rfp/rfps/
const buildApiUrl = (path = '') => {
  // Remove leading slash if present
  let cleanPath = path.startsWith('/') ? path.slice(1) : path
  // Ensure path doesn't already start with 'rfp/'
  if (cleanPath.startsWith('rfp/')) {
    cleanPath = cleanPath.slice(4) // Remove 'rfp/' prefix if present
  }
  // Build TPRM URL: /api/tprm/rfp/{path}
  const fullUrl = getTprmApiUrl(`rfp/${cleanPath}`)
  console.log('[buildApiUrl] Built URL:', { input: path, cleanPath, fullUrl })
  return fullUrl
}

export function useRfpApi() {
  /**
   * Get authentication headers with JWT token
   */
  const getAuthHeaders = () => {
    // Standard token retrieval: check sessionStorage first (populated by GRC parent)
    const token = sessionStorage.getItem('access_token') || 
                  sessionStorage.getItem('session_token') ||
                  localStorage.getItem('session_token') ||
                  localStorage.getItem('auth_token') || 
                  localStorage.getItem('access_token')
    
    const headers = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    }
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
    
    return headers
  }

  /**
   * Handle API response and errors
   */
  const handleResponse = async (response) => {
    // Handle 401 Unauthorized
    if (response.status === 401) {
      // Clear local auth data
      localStorage.removeItem('session_token')
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('current_user')
      
      const isInIframe = window.self !== window.top
      if (isInIframe && window.parent) {
        window.parent.postMessage({ type: 'TPRM_REDIRECT_TO_LOGIN' }, getParentPostMessageTargetOrigin())
      } else if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
      throw new Error('Authentication required')
    }
    
    // Handle 403 Forbidden
    if (response.status === 403) {
      const errorData = await response.json().catch(() => ({}))
      const errorMessage = errorData?.error || errorData?.message || 'You do not have permission to access this resource.'
      const errorCode = errorData?.code || '403'
      
      console.warn('[useRfpApi] 403 Forbidden:', errorMessage, response.url)
      
      // Store error info in sessionStorage for optional display by components
      sessionStorage.setItem('access_denied_error', JSON.stringify({
        message: errorMessage,
        code: errorCode,
        timestamp: new Date().toISOString(),
        path: window.location.pathname
      }))
      
      // Removed auto-redirect to prevent loops; individual components handle 403.
      throw new Error(errorMessage)
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
    const queryParams = new URLSearchParams(filters).toString()
    // Backend router is at /api/tprm/rfp/, and router.register('rfps') creates /api/tprm/rfp/rfps/
    const url = buildApiUrl(`rfps/${queryParams ? `?${queryParams}` : ''}`)
    
    console.log('[useRfpApi] Fetching RFPs from URL:', url)
    
    const response = await fetch(url, {
      method: 'GET',
      headers: getAuthHeaders(),
      credentials: 'include',
    })
    
    const data = await handleResponse(response)
    console.log('[useRfpApi] Response received:', {
      type: typeof data,
      isArray: Array.isArray(data),
      hasResults: !!data?.results,
      keys: data && typeof data === 'object' ? Object.keys(data) : null,
      count: data?.count,
      resultsLength: data?.results?.length
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
      credentials: 'include',
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
      credentials: 'include',
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
      credentials: 'include',
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
      credentials: 'include',
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
      credentials: 'include',
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
      credentials: 'include',
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
      credentials: 'include',
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

