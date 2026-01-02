/**
 * Contracts API Service
 * 
 * This service handles all API calls related to contract management
 * including CRUD operations, search, statistics, and file uploads.
 */

import { api } from './api'

// Base path for contracts API - matches Django URL structure: /api/tprm/contracts/
const CONTRACTS_API_BASE = '/contracts'

class ContractsApiService {
  /**
   * Get all contracts with filtering and pagination
   * @param {Object} params - Query parameters
   * @returns {Promise} API response
   */
  async getContracts(params = {}) {
    try {
      const url = `${CONTRACTS_API_BASE}/contracts/`
      console.log(`[ContractsAPI] GET ${url}`, { params })
      const response = await api.get(url, { params })
      console.log(`[ContractsAPI] Response:`, response.status, response.data)
      return response.data
    } catch (error) {
      console.error('[ContractsAPI] Error fetching contracts:', {
        message: error.message,
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
        url: error.config?.url
      })
      throw this.handleError(error)
    }
  }

  /**
   * Get contract by ID
   * @param {number} contractId - Contract ID
   * @returns {Promise} API response
   */
  async getContract(contractId) {
    try {
      const response = await api.get(`${CONTRACTS_API_BASE}/contracts/${contractId}/`)
      return response.data
    } catch (error) {
      console.error('Error fetching contract:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Get comprehensive contract details including terms, clauses, and sub-contracts
   * @param {number} contractId - Contract ID
   * @returns {Promise} API response
   */
  async getContractComprehensive(contractId) {
    try {
      // Use the contractapproval endpoint for comprehensive details
      const url = `/contracts/approvals/contracts/${contractId}/comprehensive/`
      console.log(`[API] Making request to: ${url}`)
      console.log(`[API] Full URL: ${api.defaults.baseURL}${url}`)
      
      const response = await api.get(url)
      console.log(`[API] Response received:`, response.status, response.data)
      return response.data
    } catch (error) {
      console.error('[API] Error fetching comprehensive contract details:', error)
      console.error('[API] Error details:', {
        message: error.message,
        code: error.code,
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data
      })
      throw this.handleError(error)
    }
  }

  /**
   * Get subcontracts for a parent contract
   * @param {number} parentContractId - Parent Contract ID
   * @returns {Promise} API response
   */
  async getSubcontracts(parentContractId) {
    try {
      const response = await api.get(`${CONTRACTS_API_BASE}/contracts/${parentContractId}/subcontracts/`)
      return response.data
    } catch (error) {
      console.error('Error fetching subcontracts:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Get contract amendments as contracts for a parent contract
   * @param {number} parentContractId - Parent Contract ID
   * @returns {Promise} API response
   */
  async getContractAmendmentsAsContracts(parentContractId) {
    try {
      const url = `${CONTRACTS_API_BASE}/contracts/${parentContractId}/amendments-as-contracts/`
      console.log(`[API] *** AMENDMENTS API CALL *** Fetching contract amendments from: ${url}`)
      console.log(`[API] Parent Contract ID: ${parentContractId} (type: ${typeof parentContractId})`)
      const response = await api.get(url)
      console.log(`[API] Contract amendments response status:`, response.status)
      console.log(`[API] Contract amendments response data:`, response.data)
      return response.data
    } catch (error) {
      console.error('[API] *** AMENDMENTS API ERROR ***', error)
      console.error('Error details:', {
        message: error.message,
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
        url: `${CONTRACTS_API_BASE}/contracts/${parentContractId}/amendments-as-contracts/`
      })
      throw this.handleError(error)
    }
  }

  /**
   * Get contract terms by contract ID
   * @param {number} contractId - Contract ID
   * @returns {Promise} API response
   */
  async getContractTerms(contractId) {
    try {
      const response = await api.get(`${CONTRACTS_API_BASE}/contracts/${contractId}/terms/`)
      return response.data
    } catch (error) {
      console.error('Error fetching contract terms:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Get contract clauses by contract ID
   * @param {number} contractId - Contract ID
   * @returns {Promise} API response
   */
  async getContractClauses(contractId) {
    try {
      const response = await api.get(`${CONTRACTS_API_BASE}/contracts/${contractId}/clauses/`)
      return response.data
    } catch (error) {
      console.error('Error fetching contract clauses:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Create a new contract
   * @param {Object} contractData - Contract data
   * @returns {Promise} API response
   */
  async createContract(contractData) {
    try {
      const response = await api.post(`${CONTRACTS_API_BASE}/contracts/create/`, contractData)
      return response.data
    } catch (error) {
      console.error('Error creating contract:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Update an existing contract
   * @param {number} contractId - Contract ID
   * @param {Object} contractData - Updated contract data
   * @returns {Promise} API response
   */
  async updateContract(contractId, contractData) {
    try {
      const response = await api.put(`${CONTRACTS_API_BASE}/contracts/${contractId}/update/`, contractData)
      return response.data
    } catch (error) {
      console.error('Error updating contract:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Partially update a contract (PATCH)
   * @param {number} contractId - Contract ID
   * @param {Object} contractData - Partial contract data to update
   * @returns {Promise} API response
   */
  async patchContract(contractId, contractData) {
    try {
      const response = await api.patch(`${CONTRACTS_API_BASE}/contracts/${contractId}/update/`, contractData)
      return response.data
    } catch (error) {
      console.error('Error patching contract:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Delete a contract (archive)
   * @param {number} contractId - Contract ID
   * @returns {Promise} API response
   */
  async deleteContract(contractId) {
    try {
      const response = await api.delete(`${CONTRACTS_API_BASE}/contracts/${contractId}/delete/`)
      return response.data
    } catch (error) {
      console.error('Error deleting contract:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Archive a contract with reason
   * @param {number} contractId - Contract ID
   * @param {Object} archiveData - Archive data
   * @returns {Promise} API response
   */
  async archiveContract(contractId, archiveData) {
    try {
      const response = await api.post(`${CONTRACTS_API_BASE}/contracts/${contractId}/archive/`, archiveData)
      return response.data
    } catch (error) {
      console.error('Error archiving contract:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Restore an archived contract
   * @param {number} contractId - Contract ID
   * @param {Object} restoreData - Restore data
   * @returns {Promise} API response
   */
  async restoreContract(contractId, restoreData) {
    try {
      const response = await api.post(`${CONTRACTS_API_BASE}/contracts/${contractId}/restore/`, restoreData)
      return response.data
    } catch (error) {
      console.error('Error restoring contract:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Search contracts with advanced filters
   * @param {Object} searchParams - Search parameters
   * @returns {Promise} API response
   */
  async searchContracts(searchParams) {
    try {
      const response = await api.get(`${CONTRACTS_API_BASE}/contracts/search/`, { params: searchParams })
      return response.data
    } catch (error) {
      console.error('Error searching contracts:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Get contract statistics
   * @returns {Promise} API response
   */
  async getContractStats() {
    try {
      const response = await api.get(`${CONTRACTS_API_BASE}/contracts/stats/`)
      return response.data
    } catch (error) {
      console.error('Error fetching contract stats:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Get comprehensive contract analytics data
   * @returns {Promise} API response
   */
  async getContractAnalytics() {
    try {
      const response = await api.get(`${CONTRACTS_API_BASE}/contracts/analytics/`)
      return response.data
    } catch (error) {
      console.error('Error fetching contract analytics:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Get contract amendments KPI data
   * @param {number} limit - Number of top contracts to retrieve (default 10)
   * @returns {Promise} API response
   */
  async getContractAmendmentsKPI(limit = 10) {
    try {
      const response = await api.get(`${CONTRACTS_API_BASE}/contracts/kpi/amendments/`, {
        params: { limit }
      })
      return response.data
    } catch (error) {
      console.error('Error fetching contract amendments KPI:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Get contracts expiring soon KPI data
   * Returns count of contracts expiring in different time periods (0-30, 31-60, 61-90, 90+ days)
   * @returns {Promise} API response
   */
  async getContractsExpiringSoonKPI() {
    try {
      const response = await api.get(`${CONTRACTS_API_BASE}/contracts/kpi/expiring-soon/`)
      return response.data
    } catch (error) {
      console.error('Error fetching contracts expiring soon KPI:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Get average contract value by contract type KPI data
   * Returns average contract value for each contract type (MASTER_AGREEMENT, SOW, LICENSE, etc.)
   * @returns {Promise} API response
   */
  async getAverageContractValueByTypeKPI() {
    try {
      const response = await api.get(`${CONTRACTS_API_BASE}/contracts/kpi/avg-value-by-type/`)
      return response.data
    } catch (error) {
      console.error('Error fetching average contract value by type KPI:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Get business criticality KPI data
   * Returns count of contracts by business criticality level (critical, high, medium, low)
   * @returns {Promise} API response
   */
  async getBusinessCriticalityKPI() {
    try {
      const response = await api.get(`${CONTRACTS_API_BASE}/contracts/kpi/business-criticality/`)
      return response.data
    } catch (error) {
      console.error('Error fetching business criticality KPI:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Get total liability exposure KPI data
   * Returns sum of all liability caps with risk assessment and color coding
   * @returns {Promise} API response
   */
  async getTotalLiabilityExposureKPI() {
    try {
      const response = await api.get(`${CONTRACTS_API_BASE}/contracts/kpi/total-liability/`)
      return response.data
    } catch (error) {
      console.error('Error fetching total liability exposure KPI:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Get contract risk exposure KPI data
   * Returns count of contracts by risk level from risk_tprm table
   * @returns {Promise} API response
   */
  async getContractRiskExposureKPI() {
    try {
      const response = await api.get(`${CONTRACTS_API_BASE}/contracts/kpi/risk-exposure/`)
      return response.data
    } catch (error) {
      console.error('Error fetching contract risk exposure KPI:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Get early termination rate KPI data
   * Returns termination percentage by contract type
   * @returns {Promise} API response
   */
  async getEarlyTerminationRateKPI() {
    try {
      const response = await api.get(`${CONTRACTS_API_BASE}/contracts/kpi/early-termination-rate/`)
      return response.data
    } catch (error) {
      console.error('Error fetching early termination rate KPI:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Get time to approve contract KPI data
   * Returns average days to approve contracts per month
   * @param {number} year - Year to fetch data for (optional, defaults to current year)
   * @returns {Promise} API response
   */
  async getTimeToApproveContractKPI(year = null) {
    try {
      const params = year ? { year } : {}
      const response = await api.get(`${CONTRACTS_API_BASE}/contracts/kpi/time-to-approve/`, { params })
      return response.data
    } catch (error) {
      console.error('Error fetching time to approve contract KPI:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Get all vendors with pagination
   * @param {Object} params - Query parameters (page, page_size, search, etc.)
   * @returns {Promise} API response
   */
  async getVendors(params = {}) {
    try {
      const response = await api.get(`${CONTRACTS_API_BASE}/vendorcontracts/`, { params })
      return response.data
    } catch (error) {
      console.error('Error fetching vendors:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Check if user has permission to create contracts
   * @returns {Promise} API response
   */
  async checkContractCreatePermission() {
    try {
      // Use the dedicated permission check endpoint
      const response = await api.get(`${CONTRACTS_API_BASE}/permissions/check-contract-create/`)
      return { hasPermission: true, data: response.data }
    } catch (error) {
      console.error('Permission check error:', error)
      
      if (error.response?.status === 403) {
      return {
          hasPermission: false, 
          error: error.response.data,
          message: error.response.data?.message || 'You do not have permission to create contracts.'
        }
      } else if (error.response?.status === 401) {
      return {
          hasPermission: false, 
          error: { error: 'AUTHENTICATION_REQUIRED' },
          message: 'Authentication required. Please log in to access this page.'
        }
      }
      
      // For other errors, allow access but return the error
      return { hasPermission: true, error: error }
    }
  }

  /**
   * Check if user has permission to list contracts
   * @returns {Promise} API response
   */
  async checkContractListPermission() {
    try {
      // Use the contracts list endpoint to check permissions
      const response = await api.get(`${CONTRACTS_API_BASE}/contracts/`, { 
        params: { page: 1, page_size: 1 } 
      })
      return { success: true, data: response.data }
    } catch (error) {
      console.error('Permission check error:', error)
      
      if (error.response?.status === 403) {
      return {
          success: false, 
          error: error.response.data,
          message: error.response.data?.message || 'You do not have permission to view contracts.'
      }
      } else if (error.response?.status === 401) {
      return {
        success: false,
          error: { error: 'AUTHENTICATION_REQUIRED' },
          message: 'Authentication required. Please log in to access this page.'
        }
      }
      
      // For other errors, allow access but return the error
      return { success: true, error: error }
    }
  }

  /**
   * Check if user has permission to view dashboard
   * @returns {Promise} API response
   */
  async checkDashboardPermission() {
    try {
      // Use the contract stats endpoint to check permissions
      const response = await api.get(`${CONTRACTS_API_BASE}/contracts/stats/`)
      return { success: true, data: response.data }
    } catch (error) {
      console.error('Permission check error:', error)
      
      if (error.response?.status === 403) {
      return {
          success: false, 
          error: error.response.data,
          message: error.response.data?.message || 'You do not have permission to view the dashboard.'
        }
      } else if (error.response?.status === 401) {
      return {
        success: false,
          error: { error: 'AUTHENTICATION_REQUIRED' },
          message: 'Authentication required. Please log in to access this page.'
        }
      }
      
      // For other errors, allow access but return the error
      return { success: true, error: error }
    }
  }

  /**
   * Check if user has permission to view contract details
   * @param {number} contractId - Contract ID
   * @returns {Promise} API response
   */
  async checkContractDetailPermission(contractId) {
    try {
      // Use the contract detail endpoint to check permissions
      const response = await api.get(`${CONTRACTS_API_BASE}/contracts/${contractId}/`)
      return { success: true, data: response.data }
    } catch (error) {
      console.error('Permission check error:', error)
      
      if (error.response?.status === 403) {
      return {
          success: false, 
          error: error.response.data,
          message: error.response.data?.message || 'You do not have permission to view this contract.'
        }
      } else if (error.response?.status === 401) {
      return {
        success: false,
          error: { error: 'AUTHENTICATION_REQUIRED' },
          message: 'Authentication required. Please log in to access this page.'
        }
      } else if (error.response?.status === 404) {
        return { 
          success: false, 
          error: { error: 'CONTRACT_NOT_FOUND' },
          message: 'Contract not found or has been archived.'
        }
      }
      
      // For other errors, allow access but return the error
      return { success: true, error: error }
    }
  }

  /**
   * Get contract statistics for dashboard
   * @returns {Promise} API response
   */
  async getContractStats() {
    try {
      const response = await api.get(`${CONTRACTS_API_BASE}/contracts/stats/`)
      return response.data
    } catch (error) {
      console.error('Error fetching contract stats:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Get recent contracts for dashboard
   * @param {number} limit - Number of recent contracts to fetch
   * @returns {Promise} API response
   */
  async getRecentContracts(limit = 5) {
    try {
      const response = await api.get(`${CONTRACTS_API_BASE}/contracts/`, {
        params: { 
          page: 1, 
          page_size: limit,
          ordering: '-created_at'
        }
      })
      return response.data
    } catch (error) {
      console.error('Error fetching recent contracts:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Get contracts list with filtering and pagination
   * @param {Object} params - Query parameters
   * @returns {Promise} API response
   */
  async getContracts(params = {}) {
    try {
      const response = await api.get(`${CONTRACTS_API_BASE}/contracts/`, { params })
      return response.data
    } catch (error) {
      console.error('Error fetching contracts:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Search contracts with advanced filters
   * @param {Object} searchParams - Search parameters
   * @returns {Promise} API response
   */
  async searchContracts(searchParams = {}) {
    try {
      const response = await api.get(`${CONTRACTS_API_BASE}/contracts/search/`, { params: searchParams })
      return response.data
    } catch (error) {
      console.error('Error searching contracts:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Get contract statistics
   * @returns {Promise} API response
   */
  async getContractStats() {
    try {
      const response = await api.get(`${CONTRACTS_API_BASE}/contracts/stats/`)
      return response.data
    } catch (error) {
      console.error('Error fetching contract stats:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Get contract details by ID
   * @param {number} contractId - Contract ID
   * @returns {Promise} API response
   */
  async getContractById(contractId) {
    try {
      const response = await api.get(`${CONTRACTS_API_BASE}/contracts/${contractId}/`)
      return response.data
    } catch (error) {
      console.error('Error fetching contract details:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Update contract
   * @param {number} contractId - Contract ID
   * @param {Object} contractData - Contract data
   * @returns {Promise} API response
   */
  async updateContract(contractId, contractData) {
    try {
      const response = await api.put(`${CONTRACTS_API_BASE}/contracts/${contractId}/update/`, contractData)
      return response.data
    } catch (error) {
      console.error('Error updating contract:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Delete contract (archive)
   * @param {number} contractId - Contract ID
   * @returns {Promise} API response
   */
  async deleteContract(contractId) {
    try {
      const response = await api.delete(`${CONTRACTS_API_BASE}/contracts/${contractId}/delete/`)
      return response.data
    } catch (error) {
      console.error('Error deleting contract:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Archive contract
   * @param {number} contractId - Contract ID
   * @param {Object} archiveData - Archive data
   * @returns {Promise} API response
   */
  async archiveContract(contractId, archiveData) {
    try {
      const response = await api.post(`${CONTRACTS_API_BASE}/contracts/${contractId}/archive/`, archiveData)
      return response.data
    } catch (error) {
      console.error('Error archiving contract:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Restore archived contract
   * @param {number} contractId - Contract ID
   * @param {Object} restoreData - Restore data
   * @returns {Promise} API response
   */
  async restoreContract(contractId, restoreData) {
    try {
      const response = await api.post(`${CONTRACTS_API_BASE}/contracts/${contractId}/restore/`, restoreData)
      return response.data
    } catch (error) {
      console.error('Error restoring contract:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Get contract renewals list
   * @returns {Promise} API response
   */
  async getContractRenewals() {
    try {
      const response = await api.get(`${CONTRACTS_API_BASE}/contracts/renewals/`)
      return response.data
    } catch (error) {
      console.error('Error fetching contract renewals:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Create contract renewal
   * @param {Object} renewalData - Renewal data
   * @returns {Promise} API response
   */
  async createContractRenewal(renewalData) {
    try {
      const response = await api.post(`${CONTRACTS_API_BASE}/contracts/renewals/create/`, renewalData)
      return response.data
    } catch (error) {
      console.error('Error creating contract renewal:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Get contract renewal by ID
   * @param {number} renewalId - Renewal ID
   * @returns {Promise} API response
   */
  async getContractRenewal(renewalId) {
    try {
      const response = await api.get(`${CONTRACTS_API_BASE}/contracts/renewals/${renewalId}/`)
      return response.data
    } catch (error) {
      console.error('Error fetching contract renewal:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Update contract renewal
   * @param {number} renewalId - Renewal ID
   * @param {Object} renewalData - Renewal data
   * @returns {Promise} API response
   */
  async updateContractRenewal(renewalId, renewalData) {
    try {
      const response = await api.put(`${CONTRACTS_API_BASE}/contracts/renewals/${renewalId}/update/`, renewalData)
      return response.data
    } catch (error) {
      console.error('Error updating contract renewal:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Delete contract renewal
   * @param {number} renewalId - Renewal ID
   * @returns {Promise} API response
   */
  async deleteContractRenewal(renewalId) {
    try {
      const response = await api.delete(`${CONTRACTS_API_BASE}/contracts/renewals/${renewalId}/delete/`)
      return response.data
    } catch (error) {
      console.error('Error deleting contract renewal:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Create contract terms
   * @param {number} contractId - Contract ID
   * @param {Object} termData - Term data
   * @returns {Promise} API response
   */
  async createContractTerms(contractId, termData) {
    try {
      const response = await api.post(`${CONTRACTS_API_BASE}/contracts/${contractId}/terms/create/`, termData)
      return response.data
    } catch (error) {
      console.error('Error creating contract terms:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Create contract clauses
   * @param {number} contractId - Contract ID
   * @param {Object} clauseData - Clause data
   * @returns {Promise} API response
   */
  async createContractClauses(contractId, clauseData) {
    try {
      const response = await api.post(`${CONTRACTS_API_BASE}/contracts/${contractId}/clauses/create/`, clauseData)
      return response.data
    } catch (error) {
      console.error('Error creating contract clauses:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Update contract terms (individual updates)
   * @param {number} contractId - Contract ID
   * @param {Array} termsData - Array of term data
   * @returns {Promise} API response
   */
  async updateContractTerms(contractId, termsData) {
    try {
      if (!termsData || termsData.length === 0) {
        return { success: true, message: 'No terms to update' }
      }

      const results = []
      for (const term of termsData) {
        if (term.id) {
          // Update existing term
          const response = await api.put(`${CONTRACTS_API_BASE}/contracts/${contractId}/terms/${term.id}/update/`, term)
          results.push(response.data)
        } else {
          // Create new term
          const response = await api.post(`${CONTRACTS_API_BASE}/contracts/${contractId}/terms/create/`, [term])
          results.push(response.data)
        }
      }
      
      return { success: true, data: results, message: 'Terms updated successfully' }
    } catch (error) {
      console.error('Error updating contract terms:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Update contract clauses (individual updates)
   * @param {number} contractId - Contract ID
   * @param {Array} clausesData - Array of clause data
   * @returns {Promise} API response
   */
  async updateContractClauses(contractId, clausesData) {
    try {
      if (!clausesData || clausesData.length === 0) {
        return { success: true, message: 'No clauses to update' }
      }

      const results = []
      for (const clause of clausesData) {
        if (clause.id) {
          // Update existing clause - remove status field if it's causing issues
          const clauseToUpdate = { ...clause }
          // Temporarily remove status field to avoid 400 errors until migration is applied
          if (clauseToUpdate.status) {
            delete clauseToUpdate.status
          }
          const response = await api.put(`${CONTRACTS_API_BASE}/contracts/${contractId}/clauses/${clause.id}/update/`, clauseToUpdate)
          results.push(response.data)
        } else {
          // Create new clause
          const clauseToCreate = { ...clause }
          // Temporarily remove status field for new clauses too
          if (clauseToCreate.status) {
            delete clauseToCreate.status
          }
          const response = await api.post(`${CONTRACTS_API_BASE}/contracts/${contractId}/clauses/create/`, [clauseToCreate])
          results.push(response.data)
        }
      }
      
      return { success: true, data: results, message: 'Clauses updated successfully' }
    } catch (error) {
      console.error('Error updating contract clauses:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Get contract term by ID
   * @param {number} contractId - Contract ID
   * @param {number} termId - Term ID
   * @returns {Promise} API response
   */
  async getContractTerm(contractId, termId) {
    try {
      const response = await api.get(`${CONTRACTS_API_BASE}/contracts/${contractId}/terms/${termId}/`)
      return response.data
    } catch (error) {
      console.error('Error fetching contract term:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Update contract term
   * @param {number} contractId - Contract ID
   * @param {number} termId - Term ID
   * @param {Object} termData - Term data
   * @returns {Promise} API response
   */
  async updateContractTerm(contractId, termId, termData) {
    try {
      const response = await api.put(`${CONTRACTS_API_BASE}/contracts/${contractId}/terms/${termId}/update/`, termData)
      return response.data
    } catch (error) {
      console.error('Error updating contract term:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Delete contract term
   * @param {number} contractId - Contract ID
   * @param {number} termId - Term ID
   * @returns {Promise} API response
   */
  async deleteContractTerm(contractId, termId) {
    try {
      const response = await api.delete(`${CONTRACTS_API_BASE}/contracts/${contractId}/terms/${termId}/delete/`)
      return response.data
    } catch (error) {
      console.error('Error deleting contract term:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Get contract clause by ID
   * @param {number} contractId - Contract ID
   * @param {number} clauseId - Clause ID
   * @returns {Promise} API response
   */
  async getContractClause(contractId, clauseId) {
    try {
      const response = await api.get(`${CONTRACTS_API_BASE}/contracts/${contractId}/clauses/${clauseId}/`)
      return response.data
    } catch (error) {
      console.error('Error fetching contract clause:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Update contract clause
   * @param {number} contractId - Contract ID
   * @param {number} clauseId - Clause ID
   * @param {Object} clauseData - Clause data
   * @returns {Promise} API response
   */
  async updateContractClause(contractId, clauseId, clauseData) {
    try {
      const response = await api.put(`${CONTRACTS_API_BASE}/contracts/${contractId}/clauses/${clauseId}/update/`, clauseData)
      return response.data
    } catch (error) {
      console.error('Error updating contract clause:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Delete all contract terms
   * @param {number} contractId - Contract ID
   * @returns {Promise} API response
   */
  async deleteContractTerms(contractId) {
    try {
      const response = await api.delete(`${CONTRACTS_API_BASE}/contracts/${contractId}/terms/delete-all/`)
      return response.data
    } catch (error) {
      console.error('Error deleting contract terms:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Delete all contract clauses
   * @param {number} contractId - Contract ID
   * @returns {Promise} API response
   */
  async deleteContractClauses(contractId) {
    try {
      const response = await api.delete(`${CONTRACTS_API_BASE}/contracts/${contractId}/clauses/delete-all/`)
      return response.data
    } catch (error) {
      console.error('Error deleting contract clauses:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Delete contract clause
   * @param {number} contractId - Contract ID
   * @param {number} clauseId - Clause ID
   * @returns {Promise} API response
   */
  async deleteContractClause(contractId, clauseId) {
    try {
      const response = await api.delete(`${CONTRACTS_API_BASE}/contracts/${contractId}/clauses/${clauseId}/delete/`)
      return response.data
    } catch (error) {
      console.error('Error deleting contract clause:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Upload contract file
   * @param {number} contractId - Contract ID
   * @param {File} file - File to upload
   * @param {Function} onProgress - Progress callback
   * @returns {Promise} API response
   */
  async uploadContractFile(contractId, file, onProgress) {
    try {
      const formData = new FormData()
      formData.append('file', file)
      
      const response = await api.post(
        `${CONTRACTS_API_BASE}/contracts/${contractId}/upload/`,
        formData,
        {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
          onUploadProgress: onProgress
        }
      )
      return response.data
    } catch (error) {
      console.error('Error uploading contract file:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Download contract file
   * @param {number} contractId - Contract ID
   * @returns {Promise} Blob data
   */
  async downloadContractFile(contractId) {
    try {
      const response = await api.get(`${CONTRACTS_API_BASE}/contracts/${contractId}/download/`, {
        responseType: 'blob'
      })
      return response.data
    } catch (error) {
      console.error('Error downloading contract file:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Get contract preview data
   * @param {Object} contractData - Contract data for preview
   * @returns {Promise} API response
   */
  async getContractPreview(contractData) {
    try {
      const response = await api.post(`${CONTRACTS_API_BASE}/contracts/preview/`, contractData)
      return response.data
    } catch (error) {
      console.error('Error getting contract preview:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Validate contract data
   * @param {Object} contractData - Contract data to validate
   * @returns {Promise} API response
   */
  async validateContract(contractData) {
    try {
      const response = await api.post(`${CONTRACTS_API_BASE}/contracts/validate/`, contractData)
      return response.data
    } catch (error) {
      console.error('Error validating contract:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Get contract audit trail
   * @param {number} contractId - Contract ID
   * @returns {Promise} API response
   */
  async getContractAuditTrail(contractId) {
    try {
      const response = await api.get(`${CONTRACTS_API_BASE}/contracts/${contractId}/audit/`)
      return response.data
    } catch (error) {
      console.error('Error fetching contract audit trail:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Get contract notifications
   * @param {Object} params - Query parameters
   * @returns {Promise} API response
   */
  async getContractNotifications(params = {}) {
    try {
      const response = await api.get(`${CONTRACTS_API_BASE}/contracts/notifications/`, { params })
      return response.data
    } catch (error) {
      console.error('Error fetching contract notifications:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Mark notification as read
   * @param {number} notificationId - Notification ID
   * @returns {Promise} API response
   */
  async markNotificationAsRead(notificationId) {
    try {
      const response = await api.post(`${CONTRACTS_API_BASE}/contracts/notifications/${notificationId}/read/`)
      return response.data
    } catch (error) {
      console.error('Error marking notification as read:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Get contract templates
   * @returns {Promise} API response
   */
  async getContractTemplates() {
    try {
      const response = await api.get(`${CONTRACTS_API_BASE}/contracts/templates/`)
      return response.data
    } catch (error) {
      console.error('Error fetching contract templates:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Create contract from template
   * @param {number} templateId - Template ID
   * @param {Object} contractData - Contract data
   * @returns {Promise} API response
   */
  async createContractFromTemplate(templateId, contractData) {
    try {
      const response = await api.post(`${CONTRACTS_API_BASE}/contracts/templates/${templateId}/create/`, contractData)
      return response.data
    } catch (error) {
      console.error('Error creating contract from template:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Get all users for contract assignment
   * @returns {Promise} API response
   */
  async getUsers() {
    try {
      const response = await api.get(`${CONTRACTS_API_BASE}/users/`)
      return response.data
    } catch (error) {
      console.error('Error fetching users:', error)
      throw this.handleError(error)
      }
    }

  /**
   * Get legal reviewers for contract assignment
   * @returns {Promise} API response
   */
  async getLegalReviewers() {
    try {
      const response = await api.get(`${CONTRACTS_API_BASE}/users/legal-reviewers/`)
      return response.data
    } catch (error) {
      console.error('Error fetching legal reviewers:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Create a new subcontract under a parent contract
   * @param {number} parentContractId - Parent contract ID
   * @param {Object} subcontractData - Subcontract data
   * @returns {Promise} API response
   */
  async createSubcontract(parentContractId, subcontractData) {
    try {
      const response = await api.post(`${CONTRACTS_API_BASE}/contracts/${parentContractId}/subcontracts/create/`, subcontractData)
      return response.data
    } catch (error) {
      console.error('Error creating subcontract:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Create both main contract and subcontract together
   * @param {Object} mainContractData - Main contract data
   * @param {Object} subcontractData - Subcontract data
   * @returns {Promise} API response
   */
  async createContractWithSubcontract(mainContractData, subcontractData) {
    try {
      const requestData = {
        main_contract: mainContractData,
        subcontract: subcontractData
      }
      
      // Debug the data being sent
      console.log('🔍 API call - requestData structure:', {
        main_contract_keys: Object.keys(requestData.main_contract || {}),
        subcontract_keys: Object.keys(requestData.subcontract || {})
      })
      console.log('🔍 API call - subcontract JSON fields:', {
        insurance_requirements: requestData.subcontract?.insurance_requirements,
        data_protection_clauses: requestData.subcontract?.data_protection_clauses,
        custom_fields: requestData.subcontract?.custom_fields
      })
      
      const response = await api.post(`${CONTRACTS_API_BASE}/contracts/with-subcontract/create/`, requestData)
      return response.data
    } catch (error) {
      console.error('Error creating contract with subcontract:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Create a subcontract with parent contract versioning
   * @param {number} parentContractId - Parent contract ID
   * @param {Object} subcontractData - Subcontract data with version_type
   * @returns {Promise} API response
   */
  async createSubcontractWithVersioning(parentContractId, subcontractData) {
    try {
      console.log('🔍 API call - createSubcontractWithVersioning:', {
        parentContractId,
        subcontractData_keys: Object.keys(subcontractData || {}),
        version_type: subcontractData?.version_type
      })
      
      const response = await api.post(`${CONTRACTS_API_BASE}/contracts/${parentContractId}/subcontract-with-versioning/create/`, subcontractData)
      return response.data
    } catch (error) {
      console.error('Error creating subcontract with versioning:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Get contract amendments
   * @param {number} contractId - Contract ID
   * @param {Object} params - Query parameters
   * @returns {Promise} API response
   */
  async getContractAmendments(contractId, params = {}) {
    try {
      const response = await api.get(`${CONTRACTS_API_BASE}/contracts/${contractId}/amendments/`, { params })
      return response.data
    } catch (error) {
      console.error('Error fetching contract amendments:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Create contract amendment
   * @param {number} contractId - Contract ID
   * @param {Object} amendmentData - Amendment data
   * @returns {Promise} API response
   */
  async createContractAmendment(contractId, amendmentData) {
    try {
      console.log('🔍 API Debug - createContractAmendment called with:')
      console.log('  - contractId:', contractId, '(type:', typeof contractId, ')')
      console.log('  - amendmentData keys:', Object.keys(amendmentData))
      console.log('  - API URL will be:', `${CONTRACTS_API_BASE}/contracts/${contractId}/create-amendment/`)
      
      if (!contractId || contractId === 'undefined' || contractId === 'null') {
        throw new Error('Contract ID is required and must be a valid number')
      }
      
      const response = await api.post(`${CONTRACTS_API_BASE}/contracts/${contractId}/create-amendment/`, amendmentData)
      console.log('✅ API call successful, response:', response.data)
      return response.data
    } catch (error) {
      console.error('❌ Error creating contract amendment:', error)
      console.error('❌ Error details:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status,
        statusText: error.response?.statusText,
        url: error.config?.url
      })
      throw this.handleError(error)
    }
  }

  /**
   * Get contract amendment by ID
   * @param {number} contractId - Contract ID
   * @param {number} amendmentId - Amendment ID
   * @returns {Promise} API response
   */
  async getContractAmendment(contractId, amendmentId) {
    try {
      const response = await api.get(`${CONTRACTS_API_BASE}/contracts/${contractId}/amendments/${amendmentId}/`)
      return response.data
    } catch (error) {
      console.error('Error fetching contract amendment:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Update contract amendment
   * @param {number} contractId - Contract ID
   * @param {number} amendmentId - Amendment ID
   * @param {Object} amendmentData - Amendment data
   * @returns {Promise} API response
   */
  async updateContractAmendment(contractId, amendmentId, amendmentData) {
    try {
      const response = await api.put(`${CONTRACTS_API_BASE}/contracts/${contractId}/amendments/${amendmentId}/update/`, amendmentData)
      return response.data
    } catch (error) {
      console.error('Error updating contract amendment:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Delete contract amendment
   * @param {number} contractId - Contract ID
   * @param {number} amendmentId - Amendment ID
   * @returns {Promise} API response
   */
  async deleteContractAmendment(contractId, amendmentId) {
    try {
      const response = await api.delete(`${CONTRACTS_API_BASE}/contracts/${contractId}/amendments/${amendmentId}/delete/`)
      return response.data
    } catch (error) {
      console.error('Error deleting contract amendment:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Archive a contract
   * @param {number} contractId - Contract ID
   * @param {Object} archiveData - Archive data (reason, comments, can_be_restored)
   * @returns {Promise} API response
   */
  async archiveContract(contractId, archiveData) {
    try {
      const response = await api.post(`${CONTRACTS_API_BASE}/contracts/${contractId}/archive/`, archiveData)
      return response.data
    } catch (error) {
      console.error('Error archiving contract:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Restore an archived contract
   * @param {number} contractId - Contract ID
   * @param {Object} restoreData - Restore data (restore_reason)
   * @returns {Promise} API response
   */
  async restoreContract(contractId, restoreData) {
    try {
      const response = await api.post(`${CONTRACTS_API_BASE}/contracts/${contractId}/restore/`, restoreData)
      return response.data
    } catch (error) {
      console.error('Error restoring contract:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Get archived contracts
   * @param {Object} params - Query parameters
   * @returns {Promise} API response
   */
  async getArchivedContracts(params = {}) {
    try {
      const response = await api.get(`${CONTRACTS_API_BASE}/contracts/`, { 
        params: { ...params, is_archived: true }
      })
      return response.data
    } catch (error) {
      console.error('Error fetching archived contracts:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Create a new version of an existing contract
   * @param {number} contractId - Contract ID
   * @param {Object} versionData - Version data
   * @returns {Promise} API response
   */
  async createContractVersion(contractId, versionData) {
    try {
      const response = await api.post(`${CONTRACTS_API_BASE}/contracts/${contractId}/create-version/`, versionData)
      return response.data
    } catch (error) {
      console.error('Error creating contract version:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Get all versions of a contract
   * @param {number} contractId - Contract ID
   * @returns {Promise} API response
   */
  async getContractVersions(contractId) {
    try {
      const response = await api.get(`${CONTRACTS_API_BASE}/contracts/${contractId}/versions/`)
      return response.data
    } catch (error) {
      console.error('Error fetching contract versions:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Compare two contracts (original and amendment)
   * @param {number} contractId - Original contract ID
   * @param {number} amendmentId - Amendment contract ID
   * @returns {Promise} API response
   */
  async compareContracts(contractId, amendmentId) {
    try {
      const response = await api.get(`${CONTRACTS_API_BASE}/contracts/${contractId}/compare/${amendmentId}/`)
      return response.data
    } catch (error) {
      console.error('Error comparing contracts:', error)
      throw this.handleError(error)
    }
  }


  /**
   * Create a subcontract
   * @param {number} contractId - Main contract ID
   * @param {Object} subcontractData - Subcontract data
   * @returns {Promise} API response
   */
  async createSubcontract(contractId, subcontractData) {
    try {
      const response = await api.post(`${CONTRACTS_API_BASE}/contracts/${contractId}/subcontracts/`, subcontractData)
      return response.data
    } catch (error) {
      console.error('Error creating subcontract:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Upload contract file for OCR extraction
   * @param {number} contractId - Contract ID
   * @param {File} file - File to upload
   * @returns {Promise} API response
   */
  async uploadContractOCR(contractId, file) {
    try {
      const formData = new FormData()
      formData.append('file', file)
      
      const response = await api.post(`${CONTRACTS_API_BASE}/contracts/${contractId}/upload-ocr/`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      return response.data
    } catch (error) {
      console.error('Error uploading contract OCR:', error)
      throw this.handleError(error)
    }
  }

  /**
   * Trigger contract risk analysis in background
   * @param {number} contractId - Contract ID
   * @returns {Promise} API response
   */
  async triggerContractRiskAnalysis(contractId) {
    try {
      console.log(`🔄 Triggering risk analysis for contract ${contractId}`)
      const response = await api.post(`${CONTRACTS_API_BASE}/contracts/${contractId}/trigger-contract-risk-analysis/`)
      console.log(`✅ Risk analysis triggered successfully for contract ${contractId}:`, response.data)
      return response.data
    } catch (error) {
      console.error(`❌ Error triggering risk analysis for contract ${contractId}:`, error)
      throw this.handleError(error)
    }
  }

  /**
   * Handle API errors
   * @param {Error} error - Error object
   * @returns {Error} Formatted error
   */
  handleError(error) {
    if (error.response) {
      // Server responded with error status
      const { status, data } = error.response
      const url = error.config?.url || 'unknown'
      
      console.error(`[ContractsAPI] HTTP Error ${status} for ${url}:`, {
        status,
        statusText: error.response.statusText,
        data,
        headers: error.response.headers
      })
      
      if (status === 401) {
        return new Error('Authentication required. Please log in.')
      } else if (status === 403) {
        return new Error('You do not have permission to perform this action.')
      } else if (status === 404) {
        return new Error('The requested resource was not found.')
      } else if (status === 429) {
        return new Error('Too many requests. Please try again later.')
      } else if (status >= 500) {
        // Log detailed error for 500 errors to help debug backend issues
        const errorDetails = data?.detail || data?.error || data?.message || 'Unknown server error'
        console.error(`[ContractsAPI] Server Error Details:`, {
          url,
          status,
          error: errorDetails,
          fullResponse: data
        })
        return new Error(`Server error (${status}): ${errorDetails}. Please check the backend logs.`)
      } else {
        return new Error(data.message || data.error || data.detail || 'An error occurred.')
      }
    } else if (error.request) {
      // Network error
      console.error('[ContractsAPI] Network Error:', {
        url: error.config?.url,
        message: error.message
      })
      return new Error('Network error. Please check your connection.')
    } else {
      // Other error
      console.error('[ContractsAPI] Unexpected Error:', error)
      return new Error(error.message || 'An unexpected error occurred.')
    }
  }
}

// Create and export singleton instance
const contractsApi = new ContractsApiService()
export default contractsApi
