import { createStore } from 'vuex'
import contractsApi from '@/services/contractsApi'
import contractAuditApi from '@/services/contractAuditApi'

const contractStore = createStore({
  state: {
    // Authentication state
    currentUser: null,
    isAuthenticated: false,
    sessionToken: null,
    
    // Contract management state
    contracts: [],
    currentContract: null,
    contractStats: {},
    contractFilters: {
      status: '',
      vendor: '',
      category: '',
      search: ''
    },
    
    // Vendor management state
    vendors: [],
    currentVendor: null,
    vendorStats: {},
    
    // Contract audits state
    contractAudits: [],
    currentContractAudit: null,
    auditStats: {},
    auditQuestionnaires: [],
    
    // UI state
    loading: false,
    loadingMessage: '',
    error: null,
    
    // Pagination
    pagination: {
      current: 1,
      total: 0,
      pageSize: 10
    }
  },
  
  getters: {
    // Authentication getters
    isAuthenticated: state => state.isAuthenticated,
    currentUser: state => state.currentUser,
    
    // Contract getters
    allContracts: state => state.contracts,
    activeContracts: state => state.contracts.filter(contract => contract.status === 'ACTIVE'),
    expiredContracts: state => state.contracts.filter(contract => contract.status === 'EXPIRED'),
    pendingContracts: state => state.contracts.filter(contract => contract.status === 'PENDING_APPROVAL'),
    
    // Vendor getters
    allVendors: state => state.vendors,
    
    // Audit getters
    allContractAudits: state => state.contractAudits,
    pendingAudits: state => state.contractAudits.filter(audit => audit.status === 'PENDING'),
    completedAudits: state => state.contractAudits.filter(audit => audit.status === 'COMPLETED'),
    
    // UI getters
    isLoading: state => state.loading,
    loadingMessage: state => state.loadingMessage,
    hasError: state => !!state.error,
    error: state => state.error
  },
  
  mutations: {
    // Authentication mutations
    SET_AUTH(state, { user, token }) {
      state.currentUser = user
      state.sessionToken = token
      state.isAuthenticated = true
      if (token) {
        localStorage.setItem('session_token', token)
      }
    },
    
    CLEAR_AUTH(state) {
      state.currentUser = null
      state.sessionToken = null
      state.isAuthenticated = false
      localStorage.removeItem('session_token')
    },
    
    // Contract mutations
    SET_CONTRACTS(state, contracts) {
      state.contracts = contracts
    },
    
    SET_CURRENT_CONTRACT(state, contract) {
      state.currentContract = contract
    },
    
    ADD_CONTRACT(state, contract) {
      state.contracts.unshift(contract)
    },
    
    UPDATE_CONTRACT(state, updatedContract) {
      const index = state.contracts.findIndex(contract => contract.id === updatedContract.id)
      if (index !== -1) {
        state.contracts.splice(index, 1, updatedContract)
      }
    },
    
    REMOVE_CONTRACT(state, contractId) {
      state.contracts = state.contracts.filter(contract => contract.id !== contractId)
    },
    
    SET_CONTRACT_STATS(state, stats) {
      state.contractStats = stats
    },
    
    SET_CONTRACT_FILTERS(state, filters) {
      state.contractFilters = { ...state.contractFilters, ...filters }
    },
    
    // Vendor mutations
    SET_VENDORS(state, vendors) {
      state.vendors = vendors
    },
    
    SET_CURRENT_VENDOR(state, vendor) {
      state.currentVendor = vendor
    },
    
    SET_VENDOR_STATS(state, stats) {
      state.vendorStats = stats
    },
    
    // Contract audit mutations
    SET_CONTRACT_AUDITS(state, audits) {
      state.contractAudits = audits
    },
    
    SET_CURRENT_CONTRACT_AUDIT(state, audit) {
      state.currentContractAudit = audit
    },
    
    ADD_CONTRACT_AUDIT(state, audit) {
      state.contractAudits.unshift(audit)
    },
    
    UPDATE_CONTRACT_AUDIT(state, updatedAudit) {
      const index = state.contractAudits.findIndex(audit => audit.id === updatedAudit.id)
      if (index !== -1) {
        state.contractAudits.splice(index, 1, updatedAudit)
      }
    },
    
    SET_AUDIT_STATS(state, stats) {
      state.auditStats = stats
    },
    
    SET_AUDIT_QUESTIONNAIRES(state, questionnaires) {
      state.auditQuestionnaires = questionnaires
    },
    
    // UI mutations
    SET_LOADING(state, { loading, message = '' }) {
      state.loading = loading
      state.loadingMessage = message
    },
    
    SET_ERROR(state, error) {
      state.error = error
    },
    
    CLEAR_ERROR(state) {
      state.error = null
    },
    
    SET_PAGINATION(state, pagination) {
      state.pagination = { ...state.pagination, ...pagination }
    }
  },
  
  actions: {
    // Authentication actions
    async login({ commit }, credentials) {
      try {
        commit('SET_LOADING', { loading: true, message: 'Logging in...' })
        commit('CLEAR_ERROR')
        
        const response = await contractsApi.login(credentials)
        
        if (response.success) {
          const { user, session_token } = response.data
          commit('SET_AUTH', { user, token: session_token })
          return { success: true }
        } else {
          const error = response.error || 'Login failed'
          commit('SET_ERROR', error)
          return { success: false, error }
        }
      } catch (error) {
        console.error('Login error:', error)
        const errorMessage = 'An unexpected error occurred during login'
        commit('SET_ERROR', errorMessage)
        return { success: false, error: errorMessage }
      } finally {
        commit('SET_LOADING', { loading: false })
      }
    },
    
    async validateSession({ commit }) {
      try {
        const response = await contractsApi.validateSession()
        
        if (response.success) {
          const { user } = response.data
          const token = localStorage.getItem('session_token')
          commit('SET_AUTH', { user, token })
          return { success: true }
        } else {
          commit('CLEAR_AUTH')
          return { success: false }
        }
      } catch (error) {
        console.error('Session validation error:', error)
        commit('CLEAR_AUTH')
        return { success: false }
      }
    },
    
    logout({ commit }) {
      commit('CLEAR_AUTH')
    },
    
    // Contract actions
    async fetchContracts({ commit }, params = {}) {
      try {
        commit('SET_LOADING', { loading: true, message: 'Fetching contracts...' })
        commit('CLEAR_ERROR')
        
        const response = await contractsApi.getContracts(params)
        
        if (response.success) {
          commit('SET_CONTRACTS', response.data || [])
          if (response.pagination) {
            commit('SET_PAGINATION', response.pagination)
          }
          return { success: true, data: response.data }
        } else {
          const error = response.error || 'Failed to fetch contracts'
          commit('SET_ERROR', error)
          return { success: false, error }
        }
      } catch (error) {
        console.error('Error fetching contracts:', error)
        const errorMessage = 'An unexpected error occurred while fetching contracts'
        commit('SET_ERROR', errorMessage)
        return { success: false, error: errorMessage }
      } finally {
        commit('SET_LOADING', { loading: false })
      }
    },
    
    async fetchContract({ commit }, contractId) {
      try {
        commit('SET_LOADING', { loading: true, message: 'Fetching contract details...' })
        commit('CLEAR_ERROR')
        
        const response = await contractsApi.getContract(contractId)
        
        if (response.success) {
          commit('SET_CURRENT_CONTRACT', response.data)
          return { success: true, data: response.data }
        } else {
          const error = response.error || 'Failed to fetch contract'
          commit('SET_ERROR', error)
          return { success: false, error }
        }
      } catch (error) {
        console.error('Error fetching contract:', error)
        const errorMessage = 'An unexpected error occurred while fetching contract'
        commit('SET_ERROR', errorMessage)
        return { success: false, error: errorMessage }
      } finally {
        commit('SET_LOADING', { loading: false })
      }
    },
    
    async createContract({ commit, dispatch }, contractData) {
      try {
        commit('SET_LOADING', { loading: true, message: 'Creating contract...' })
        commit('CLEAR_ERROR')
        
        const response = await contractsApi.createContract(contractData)
        
        if (response.success) {
          commit('ADD_CONTRACT', response.data)
          // Refresh contract stats
          dispatch('fetchContractStats')
          return { success: true, data: response.data }
        } else {
          const error = response.error || 'Failed to create contract'
          commit('SET_ERROR', error)
          return { success: false, error }
        }
      } catch (error) {
        console.error('Error creating contract:', error)
        const errorMessage = 'An unexpected error occurred while creating contract'
        commit('SET_ERROR', errorMessage)
        return { success: false, error: errorMessage }
      } finally {
        commit('SET_LOADING', { loading: false })
      }
    },
    
    async updateContract({ commit, dispatch }, { contractId, contractData }) {
      try {
        commit('SET_LOADING', { loading: true, message: 'Updating contract...' })
        commit('CLEAR_ERROR')
        
        const response = await contractsApi.updateContract(contractId, contractData)
        
        if (response.success) {
          commit('UPDATE_CONTRACT', response.data)
          commit('SET_CURRENT_CONTRACT', response.data)
          // Refresh contract stats
          dispatch('fetchContractStats')
          return { success: true, data: response.data }
        } else {
          const error = response.error || 'Failed to update contract'
          commit('SET_ERROR', error)
          return { success: false, error }
        }
      } catch (error) {
        console.error('Error updating contract:', error)
        const errorMessage = 'An unexpected error occurred while updating contract'
        commit('SET_ERROR', errorMessage)
        return { success: false, error: errorMessage }
      } finally {
        commit('SET_LOADING', { loading: false })
      }
    },
    
    async deleteContract({ commit, dispatch }, contractId) {
      try {
        commit('SET_LOADING', { loading: true, message: 'Deleting contract...' })
        commit('CLEAR_ERROR')
        
        const response = await contractsApi.deleteContract(contractId)
        
        if (response.success) {
          commit('REMOVE_CONTRACT', contractId)
          // Refresh contract stats
          dispatch('fetchContractStats')
          return { success: true }
        } else {
          const error = response.error || 'Failed to delete contract'
          commit('SET_ERROR', error)
          return { success: false, error }
        }
      } catch (error) {
        console.error('Error deleting contract:', error)
        const errorMessage = 'An unexpected error occurred while deleting contract'
        commit('SET_ERROR', errorMessage)
        return { success: false, error: errorMessage }
      } finally {
        commit('SET_LOADING', { loading: false })
      }
    },
    
    async fetchContractStats({ commit }) {
      try {
        const response = await contractsApi.getContractStats()
        
        if (response.success) {
          commit('SET_CONTRACT_STATS', response.data)
          return { success: true, data: response.data }
        }
      } catch (error) {
        console.error('Error fetching contract stats:', error)
      }
    },
    
    // Vendor actions
    async fetchVendors({ commit }, params = {}) {
      try {
        commit('SET_LOADING', { loading: true, message: 'Fetching vendors...' })
        commit('CLEAR_ERROR')
        
        const response = await contractsApi.getVendors(params)
        
        if (response.success) {
          commit('SET_VENDORS', response.data || [])
          return { success: true, data: response.data }
        } else {
          const error = response.error || 'Failed to fetch vendors'
          commit('SET_ERROR', error)
          return { success: false, error }
        }
      } catch (error) {
        console.error('Error fetching vendors:', error)
        const errorMessage = 'An unexpected error occurred while fetching vendors'
        commit('SET_ERROR', errorMessage)
        return { success: false, error: errorMessage }
      } finally {
        commit('SET_LOADING', { loading: false })
      }
    },
    
    // Contract Audit actions
    async fetchContractAudits({ commit }, params = {}) {
      try {
        commit('SET_LOADING', { loading: true, message: 'Fetching contract audits...' })
        commit('CLEAR_ERROR')
        
        const response = await contractAuditApi.getContractAudits(params)
        
        if (response.success) {
          commit('SET_CONTRACT_AUDITS', response.data || [])
          return { success: true, data: response.data }
        } else {
          const error = response.error || 'Failed to fetch contract audits'
          commit('SET_ERROR', error)
          return { success: false, error }
        }
      } catch (error) {
        console.error('Error fetching contract audits:', error)
        const errorMessage = 'An unexpected error occurred while fetching contract audits'
        commit('SET_ERROR', errorMessage)
        return { success: false, error: errorMessage }
      } finally {
        commit('SET_LOADING', { loading: false })
      }
    },
    
    async createContractAudit({ commit, dispatch }, auditData) {
      try {
        commit('SET_LOADING', { loading: true, message: 'Creating contract audit...' })
        commit('CLEAR_ERROR')
        
        const response = await contractAuditApi.createContractAudit(auditData)
        
        if (response.success) {
          commit('ADD_CONTRACT_AUDIT', response.data)
          // Refresh audit stats
          dispatch('fetchContractAuditStats')
          return { success: true, data: response.data }
        } else {
          const error = response.error || 'Failed to create contract audit'
          commit('SET_ERROR', error)
          return { success: false, error }
        }
      } catch (error) {
        console.error('Error creating contract audit:', error)
        const errorMessage = 'An unexpected error occurred while creating contract audit'
        commit('SET_ERROR', errorMessage)
        return { success: false, error: errorMessage }
      } finally {
        commit('SET_LOADING', { loading: false })
      }
    },
    
    async fetchContractAuditStats({ commit }) {
      try {
        const response = await contractAuditApi.getContractAuditDashboardStats()
        
        if (response.success) {
          commit('SET_AUDIT_STATS', response.data)
          return { success: true, data: response.data }
        }
      } catch (error) {
        console.error('Error fetching contract audit stats:', error)
      }
    },
    
    // UI actions
    setLoading({ commit }, payload) {
      commit('SET_LOADING', payload)
    },
    
    setError({ commit }, error) {
      commit('SET_ERROR', error)
    },
    
    clearError({ commit }) {
      commit('CLEAR_ERROR')
    },
    
    setContractFilters({ commit }, filters) {
      commit('SET_CONTRACT_FILTERS', filters)
    }
  }
})

export default contractStore
