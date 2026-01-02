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
    async fetchRFPs() {
      this.loading = true
      try {
        const { fetchRFPs } = useRfpApi()
        
        // Fetch RFPs from the Django backend API with authentication
        const data = await fetchRFPs()
        
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
        } else {
          throw new Error('Invalid response format from API')
        }
      } catch (error) {
        console.error('Error fetching RFPs:', error)
        this.error = error
        // Fallback to mock data if API fails
        this.rfps = [
          {
            id: 1,
            title: 'Software Development RFP',
            status: 'active',
            createdDate: '2024-01-15',
            deadline: '2024-02-15'
          },
          {
            id: 2,
            title: 'Cloud Infrastructure RFP',
            status: 'draft',
            createdDate: '2024-01-14',
            deadline: '2024-02-14'
          }
        ]
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
