import { defineStore } from 'pinia'
import { sharedPinia } from './shared'
import { useRfpApi } from '@/composables/useRfpApi'

// RFP Store
const useRFPStore = defineStore('rfp', {
  state: () => ({
    rfps: [],
    currentRFP: null,
    loading: false,
    error: null
  }),

  getters: {
    activeRFPs: (state) => state.rfps.filter((rfp) => rfp.status === 'active'),
    draftRFPs: (state) => state.rfps.filter((rfp) => rfp.status === 'draft'),
    completedRFPs: (state) => state.rfps.filter((rfp) => rfp.status === 'completed')
  },

  actions: {
    // MULTI-TENANCY: Clear store when tenant changes
    clearStore() {
      console.log('[RFP Store] Clearing RFP store (tenant/user change detected)')
      this.rfps = []
      this.currentRFP = null
      this.error = null
      this.loading = false
    },

    async fetchRFPs() {
      // MULTI-TENANCY: Check if tenant_id has changed, clear store if so
      const currentTenantId = localStorage.getItem('tenant_id')
      const storedTenantId = sessionStorage.getItem('rfp_store_tenant_id')
      
      if (storedTenantId && storedTenantId !== currentTenantId) {
        console.log(`[RFP Store] Tenant changed from ${storedTenantId} to ${currentTenantId}, clearing store`)
        this.clearStore()
      }
      
      // Store current tenant_id for next check
      if (currentTenantId) {
        sessionStorage.setItem('rfp_store_tenant_id', currentTenantId)
      }
      
      this.loading = true
      try {
        const { fetchRFPs } = useRfpApi()
        
        // Fetch RFPs from the Django backend API with authentication
        const data = await fetchRFPs()
        
        console.log('[RFP Store] Fetched RFPs - Full response:', data)
        console.log('[RFP Store] Fetched RFPs:', {
          count: data?.results?.length || 0,
          tenant_id: currentTenantId,
          hasResults: !!data?.results,
          isArray: Array.isArray(data),
          dataType: typeof data,
          dataKeys: data && typeof data === 'object' ? Object.keys(data) : null
        })
        
        // Check if response is router URLs (error case)
        if (data && typeof data === 'object' && data.rfps && typeof data.rfps === 'string' && data.rfps.includes('http')) {
          console.error('[RFP Store] ❌ Received router URLs instead of RFP data. This means the API endpoint is wrong.')
          console.error('[RFP Store] Response:', data)
          throw new Error('Invalid API endpoint - received router URLs instead of RFP data. Please check the API URL configuration.')
        }
        
        if (data && data.results) {
          // Transform the data to match the expected format
          this.rfps = data.results.map((rfp) => ({
            id: rfp.rfp_id,
            rfp_number: rfp.rfp_number,
            title: rfp.rfp_title,
            description: rfp.description,
            status: rfp.status.toLowerCase(),
            createdDate: rfp.created_at,
            deadline: rfp.submission_deadline,
            budgetMin: rfp.budget_range_min,
            budgetMax: rfp.budget_range_max,
            criteriaCount: rfp.evaluation_criteria?.length || 0,
            createdByName: rfp.created_by_name || 'Unknown'
          }))
          console.log(`[RFP Store] ✅ Loaded ${this.rfps.length} RFPs for tenant ${currentTenantId}`)
        } else if (data && Array.isArray(data)) {
          // Handle case where API returns array directly
          this.rfps = data.map((rfp) => ({
            id: rfp.rfp_id,
            rfp_number: rfp.rfp_number,
            title: rfp.rfp_title,
            description: rfp.description,
            status: rfp.status?.toLowerCase() || 'draft',
            createdDate: rfp.created_at,
            deadline: rfp.submission_deadline,
            budgetMin: rfp.budget_range_min,
            budgetMax: rfp.budget_range_max,
            criteriaCount: rfp.evaluation_criteria?.length || 0,
            createdByName: rfp.created_by_name || 'Unknown'
          }))
          console.log(`[RFP Store] ✅ Loaded ${this.rfps.length} RFPs (array format) for tenant ${currentTenantId}`)
        } else {
          console.warn('[RFP Store] ⚠️ Invalid response format from API:', data)
          this.rfps = []
        }
      } catch (error) {
        console.error('[RFP Store] ❌ Error fetching RFPs:', error)
        this.error = error
        this.rfps = [] // Clear on error instead of showing mock data
      } finally {
        this.loading = false
      }
    },

    async createRFP(rfpData) {
      this.loading = true
      try {
        const { createRFP } = useRfpApi()
        
        // Call the API with authentication
        const data = await createRFP(rfpData)
        
        // Transform the response to match our format
        const newRFP = {
          id: data.rfp_id,
          rfp_number: data.rfp_number,
          title: data.rfp_title,
          description: data.description,
          status: data.status.toLowerCase(),
          createdDate: data.created_at,
          deadline: data.submission_deadline,
          budgetMin: data.budget_range_min,
          budgetMax: data.budget_range_max,
          criteriaCount: data.evaluation_criteria ? data.evaluation_criteria.length : 0,
          createdByName: data.created_by_details ? 
            `${data.created_by_details.first_name} ${data.created_by_details.last_name}`.trim() || data.created_by_details.username :
            'Unknown'
        }
        this.rfps.unshift(newRFP) // Add to beginning of list
        return newRFP
      } catch (error) {
        console.error('Error creating RFP:', error)
        this.error = error
        throw error
      } finally {
        this.loading = false
      }
    },

    setCurrentRFP(rfp) {
      this.currentRFP = rfp
    }
  }
})

// Vendor Store
const useVendorStore = defineStore('vendor', {
  state: () => ({
    vendors: [],
    currentVendor: null,
    loading: false,
    error: null
  }),

  getters: {
    activeVendors: (state) => state.vendors.filter((vendor) => vendor.status === 'active'),
    pendingVendors: (state) => state.vendors.filter((vendor) => vendor.status === 'pending')
  },

  actions: {
    async fetchVendors() {
      this.loading = true
      try {
        // TODO: Replace with actual API call
        // Mock data for now
        this.vendors = [
          {
            id: 1,
            name: 'TechCorp Inc.',
            email: 'contact@techcorp.com',
            status: 'active',
            category: 'Software Development'
          },
          {
            id: 2,
            name: 'CloudSolutions Ltd.',
            email: 'info@cloudsolutions.com',
            status: 'active',
            category: 'Cloud Services'
          }
        ]
      } catch (error) {
        this.error = error
      } finally {
        this.loading = false
      }
    }
  }
})

// User Store
const useUserStore = defineStore('user', {
  state: () => ({
    user: null,
    isAuthenticated: false,
    loading: false,
    error: null
  }),

  actions: {
    async login(credentials) {
      this.loading = true
      try {
        // TODO: Replace with actual API call
        // Mock login
        this.user = {
          id: 1,
          email: credentials.email,
          name: 'John Doe',
          role: 'admin'
        }
        this.isAuthenticated = true
      } catch (error) {
        this.error = error
        throw error
      } finally {
        this.loading = false
      }
    },

    async logout() {
      this.user = null
      this.isAuthenticated = false
    }
  }
})

export {
  useRFPStore,
  useVendorStore,
  useUserStore
}
