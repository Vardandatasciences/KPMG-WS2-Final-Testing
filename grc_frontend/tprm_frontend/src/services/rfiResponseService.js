/**
 * Service for RFI responses list and filters
 */
import api from '@/utils/api_rfp.js'
import { getTprmApiV1BaseUrl } from '@/utils/backendEnv'

const API_BASE = getTprmApiV1BaseUrl()

const rfiResponseService = {
  /**
   * List RFI responses with optional filters
   * @param {Object} params - { rfi_id, evaluation_status, submission_status, vendor_search }
   * @returns {Promise<{ results: Array }>}
   */
  async getResponses(params = {}) {
    try {
      const query = new URLSearchParams()
      if (params.rfi_id != null && params.rfi_id !== '') query.set('rfi_id', params.rfi_id)
      if (params.evaluation_status) query.set('evaluation_status', params.evaluation_status)
      if (params.submission_status) query.set('submission_status', params.submission_status)
      if (params.vendor_search) query.set('vendor_search', params.vendor_search)

      const qs = query.toString()
      const url = qs ? `${API_BASE}/rfi-responses/list/?${qs}` : `${API_BASE}/rfi-responses/list/`
      console.log('[RFIResponseService] Fetching responses from:', url)
      
      const response = await api.get(url)
      console.log('[RFIResponseService] Response received:', {
        status: response.status,
        hasData: !!response.data,
        hasResults: !!(response.data && response.data.results),
        resultsCount: response.data?.results?.length || 0
      })
      
      // Handle both JsonResponse format ({results: [...]}) and direct array
      if (response.data && response.data.results) {
        return response.data
      } else if (Array.isArray(response.data)) {
        return { results: response.data }
      } else {
        console.warn('[RFIResponseService] Unexpected response format:', response.data)
        return { results: [] }
      }
    } catch (error) {
      console.error('[RFIResponseService] Error fetching responses:', error)
      console.error('[RFIResponseService] Error details:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status,
        url: error.config?.url
      })
      throw error
    }
  }
}

export default rfiResponseService
