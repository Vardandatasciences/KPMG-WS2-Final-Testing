<template>
  <!-- Vendor Detail View (Full Page) -->
  <VendorDetailView 
    v-if="showDetailModal"
    :vendor-code="selectedVendorCode"
    :initial-tab="initialTabFromRoute"
    @back="closeDetailModal"
  />
  
  <!-- Vendor List View -->
  <div v-else class="all-vendors-container">
    <!-- Header -->
    <div class="vendors-header">
      <div>
        <h1 class="vendors-title">All Vendors</h1>
        <p class="vendors-subtitle">View and manage all vendors in the system</p>
      </div>
      <div class="header-actions">
        <div class="view-toggle">
          <button 
            class="view-btn" 
            :class="{ active: viewMode === 'card' }"
            @click="viewMode = 'card'"
            title="Card View"
          >
            <i class="fas fa-th-large"></i>
            Card
          </button>
          <button 
            class="view-btn" 
            :class="{ active: viewMode === 'table' }"
            @click="viewMode = 'table'"
            title="Table View"
          >
            <i class="fas fa-table"></i>
            Table
          </button>
        </div>
      </div>
    </div>

    <!-- Stats Cards -->
    <div class="stats-grid">
      <div class="stat-card stat-onboarded-rfp">
        <div class="stat-icon">
          <i class="fas fa-file-contract"></i>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.onboarded_with_rfp }}</div>
          <div class="stat-label">Onboarded with RFP</div>
        </div>
      </div>
      <div class="stat-card stat-onboarded-no-rfp">
        <div class="stat-icon">
          <i class="fas fa-user-plus"></i>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.onboarded_without_rfp }}</div>
          <div class="stat-label">Onboarded without RFP</div>
        </div>
      </div>
      <div class="stat-card stat-temp-rfp">
        <div class="stat-icon">
          <i class="fas fa-clock"></i>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.temporary_with_rfp }}</div>
          <div class="stat-label">Temporary with RFP</div>
        </div>
      </div>
      <div class="stat-card stat-temp-no-rfp">
        <div class="stat-icon">
          <i class="fas fa-hourglass-half"></i>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.temporary_without_rfp }}</div>
          <div class="stat-label">Temporary without RFP</div>
        </div>
      </div>
    </div>

    <!-- Filters -->
    <div class="filters-section">
      <div class="filter-group">
        <label class="filter-label">Vendor Type</label>
        <select v-model="filters.vendorType" class="filter-select">
          <option value="">All Types</option>
          <option value="ONBOARDED_WITH_RFP">Onboarded with RFP</option>
          <option value="ONBOARDED_WITHOUT_RFP">Onboarded without RFP</option>
          <option value="TEMPORARY_WITH_RFP">Temporary with RFP</option>
          <option value="TEMPORARY_WITHOUT_RFP">Temporary without RFP</option>
        </select>
      </div>
      <div class="filter-group">
        <label class="filter-label">Risk Level</label>
        <select v-model="filters.riskLevel" class="filter-select">
          <option value="">All Risk Levels</option>
          <option value="LOW">Low</option>
          <option value="MEDIUM">Medium</option>
          <option value="HIGH">High</option>
          <option value="CRITICAL">Critical</option>
        </select>
      </div>
      <div class="filter-group">
        <label class="filter-label">Status</label>
        <select v-model="filters.status" class="filter-select">
          <option value="">All Status</option>
          <option value="DRAFT">Draft</option>
          <option value="SUBMITTED">Submitted</option>
          <option value="IN_REVIEW">In Review</option>
          <option value="APPROVED">Approved</option>
          <option value="REJECTED">Rejected</option>
          <option value="SUSPENDED">Suspended</option>
          <option value="TERMINATED">Terminated</option>
        </select>
      </div>
      <div class="filter-group search-group">
        <label class="filter-label">Search</label>
        <div class="search-input-wrapper">
          <i class="fas fa-search search-icon"></i>
          <input 
            v-model="filters.search" 
            type="text" 
            class="search-input" 
            placeholder="Search by name, code..."
          />
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-container">
      <div class="spinner"></div>
      <p>Loading vendors...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-container">
      <i class="fas fa-exclamation-triangle"></i>
      <p>{{ error }}</p>
      <button @click="fetchVendors" class="btn btn-primary">Retry</button>
    </div>

    <!-- Empty State -->
    <div v-else-if="filteredVendors.length === 0" class="empty-container">
      <i class="fas fa-inbox"></i>
      <p>No vendors found</p>
    </div>

    <!-- Card View -->
    <div v-else-if="viewMode === 'card'" class="vendors-grid">
      <div 
        v-for="vendor in filteredVendors" 
        :key="vendor.vendor_code"
        class="vendor-card"
        :class="getVendorCardClass(vendor.vendor_type)"
      >
        <div class="vendor-card-header">
          <div class="vendor-type-badge" :class="getVendorTypeBadgeClass(vendor.vendor_type)">
            {{ vendor.vendor_type_label }}
          </div>
          <div class="vendor-actions">
            <button 
              @click="viewVendorDetails(vendor.vendor_code)" 
              class="action-btn view-btn-card"
              title="View Details"
            >
              <i class="fas fa-eye"></i>
              <span>View</span>
            </button>
          </div>
        </div>
        
        <div class="vendor-card-body">
          <h3 class="vendor-name">{{ vendor.company_name || 'N/A' }}</h3>
          <p class="vendor-code">{{ vendor.vendor_code }}</p>
          
          <div class="vendor-details">
            <div class="detail-row">
              <span class="detail-label">Legal Name:</span>
              <span class="detail-value">{{ vendor.legal_name || 'N/A' }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">Industry:</span>
              <span class="detail-value">{{ vendor.industry_sector || 'N/A' }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">Business Type:</span>
              <span class="detail-value">{{ vendor.business_type || 'N/A' }}</span>
            </div>
          </div>

          <div class="vendor-badges">
            <span 
              v-if="vendor.risk_level" 
              class="badge"
              :class="getRiskLevelClass(vendor.risk_level)"
            >
              {{ vendor.risk_level }}
            </span>
            <span 
              v-if="vendor.status" 
              class="badge"
              :class="getStatusClass(vendor.status)"
            >
              {{ vendor.status }}
            </span>
            <span v-if="vendor.is_critical_vendor" class="badge badge-critical">
              Critical
            </span>
            <span v-if="vendor.has_data_access" class="badge badge-info">
              Data Access
            </span>
            <span v-if="vendor.has_system_access" class="badge badge-info">
              System Access
            </span>
          </div>
        </div>

        <div class="vendor-card-footer">
          <div class="footer-info">
            <i class="fas fa-calendar"></i>
            <span>{{ formatDate(vendor.created_at) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Table View -->
    <div v-else class="table-container">
      <table class="vendors-table">
        <thead>
          <tr>
            <th>Vendor Code</th>
            <th>Company Name</th>
            <th>Legal Name</th>
            <th>Type</th>
            <th>Risk Level</th>
            <th>Status</th>
            <th>Industry</th>
            <th>Created</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="vendor in filteredVendors" :key="vendor.vendor_code">
            <td class="vendor-code-cell">{{ vendor.vendor_code }}</td>
            <td class="vendor-name-cell">{{ vendor.company_name || 'N/A' }}</td>
            <td>{{ vendor.legal_name || 'N/A' }}</td>
            <td>{{ vendor.vendor_type_label || '-' }}</td>
            <td>
              <span 
                v-if="vendor.risk_level"
                class="badge"
                :class="getRiskLevelClass(vendor.risk_level)"
              >
                {{ vendor.risk_level }}
              </span>
              <span v-else>-</span>
            </td>
            <td>
              <span 
                v-if="vendor.status"
                class="badge"
                :class="getStatusClass(vendor.status)"
              >
                {{ vendor.status }}
              </span>
              <span v-else>-</span>
            </td>
            <td>{{ vendor.industry_sector || '-' }}</td>
            <td>{{ formatDate(vendor.created_at) }}</td>
            <td>
              <div class="table-actions">
                <button 
                  @click="viewVendorDetails(vendor.vendor_code)" 
                  class="action-btn btn-sm view-btn-table"
                  title="View Details"
                >
                  <i class="fas fa-eye"></i>
                  <span>View</span>
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from '@/config/axios'
import VendorDetailView from './VendorDetailView.vue'
import { PopupService } from '@/popup/popupService'

export default {
  name: 'AllVendors',
  components: {
    VendorDetailView
  },
  setup() {
    const route = useRoute()
    const router = useRouter()
    const vendors = ref([])
    const loading = ref(false)
    const error = ref(null)
    const viewMode = ref('table')
    const showDetailModal = ref(false)
    const selectedVendorCode = ref(null)

    const initialTabFromRoute = computed(() => route.query.tab || null)
    
    const filters = ref({
      vendorType: '',
      riskLevel: '',
      status: '',
      search: ''
    })

    const stats = ref({
      onboarded_with_rfp: 0,
      onboarded_without_rfp: 0,
      temporary_with_rfp: 0,
      temporary_without_rfp: 0
    })

    const fetchVendors = async () => {
      loading.value = true
      error.value = null
      
      console.log('[AllVendors] 🔍 Starting fetchVendors...')
      console.log('[AllVendors] 📍 Current URL:', window.location.href)
      console.log('[AllVendors] 🔑 Auth token exists:', !!localStorage.getItem('session_token'))
      console.log('[AllVendors] 🌐 API Base URL:', axios.defaults.baseURL || 'Not set (using relative)')
      
      const apiUrl = '/api/v1/management/vendors/all/'
      console.log('[AllVendors] 📡 Making request to:', apiUrl)
      console.log('[AllVendors] 📡 Full URL will be:', `${window.location.origin}${apiUrl}`)
      
      try {
        const response = await axios.get(apiUrl)
        
        console.log('[AllVendors] ✅ Response received:', {
          status: response.status,
          statusText: response.statusText,
          data: response.data,
          headers: response.headers
        })
        
        if (response.data.success) {
          console.log('[AllVendors] ✅ Success! Vendors count:', response.data.data?.length || 0)
          console.log('[AllVendors] 📊 Stats:', response.data.counts)
          vendors.value = response.data.data
          stats.value = response.data.counts
        } else {
          console.error('[AllVendors] ❌ Response indicates failure:', response.data)
          error.value = response.data.error || 'Failed to load vendors'
        }
      } catch (err) {
        console.error('[AllVendors] ❌ Error fetching vendors:', err)
        console.error('[AllVendors] ❌ Error details:', {
          message: err.message,
          code: err.code,
          response: err.response ? {
            status: err.response.status,
            statusText: err.response.statusText,
            data: err.response.data,
            headers: err.response.headers
          } : 'No response',
          config: err.config ? {
            url: err.config.url,
            method: err.config.method,
            baseURL: err.config.baseURL,
            headers: err.config.headers
          } : 'No config'
        })
        
        if (err.response?.status === 404) {
          error.value = `Endpoint not found (404). The backend route /api/v1/management/vendors/all/ may not be registered. Please restart Django server.`
          console.error('[AllVendors] 🚨 404 Error - Backend route not found!')
          console.error('[AllVendors] 💡 Solution: Restart Django server to load the new routes')
        } else if (err.response?.status === 401) {
          error.value = 'Authentication failed. Please log in again.'
          console.error('[AllVendors] 🚨 401 Error - Authentication failed')
        } else if (err.code === 'ECONNABORTED' || err.message.includes('timeout')) {
          error.value = 'Request timed out. The server may be slow or unresponsive.'
          console.error('[AllVendors] 🚨 Timeout Error - Request took too long')
        } else {
          error.value = err.response?.data?.error || err.message || 'Failed to load vendors'
        }
      } finally {
        loading.value = false
        console.log('[AllVendors] ✅ fetchVendors completed. Loading:', loading.value)
      }
    }

    const filteredVendors = computed(() => {
      let result = vendors.value

      // Filter by vendor type
      if (filters.value.vendorType) {
        result = result.filter(v => v.vendor_type === filters.value.vendorType)
      }

      // Filter by risk level
      if (filters.value.riskLevel) {
        result = result.filter(v => v.risk_level === filters.value.riskLevel)
      }

      // Filter by status
      if (filters.value.status) {
        result = result.filter(v => v.status === filters.value.status)
      }

      // Filter by search
      if (filters.value.search) {
        const search = filters.value.search.toLowerCase()
        result = result.filter(v => 
          v.company_name?.toLowerCase().includes(search) ||
          v.vendor_code?.toLowerCase().includes(search) ||
          v.legal_name?.toLowerCase().includes(search)
        )
      }

      return result
    })

    const viewVendorDetails = (vendorCode) => {
      selectedVendorCode.value = vendorCode
      showDetailModal.value = true
    }

    const closeDetailModal = () => {
      showDetailModal.value = false
      selectedVendorCode.value = null
      if (route.query.vendorCode || route.query.tab) {
        router.replace({ path: '/all-vendors' })
      }
    }

    const openDetailFromRoute = () => {
      const code = route.query.vendorCode
      if (code) {
        selectedVendorCode.value = code
        showDetailModal.value = true
      }
    }

    const getVendorCardClass = (vendorType) => {
      const classMap = {
        'ONBOARDED_WITH_RFP': 'card-onboarded-rfp',
        'ONBOARDED_WITHOUT_RFP': 'card-onboarded-no-rfp',
        'TEMPORARY_WITH_RFP': 'card-temp-rfp',
        'TEMPORARY_WITHOUT_RFP': 'card-temp-no-rfp'
      }
      return classMap[vendorType] || ''
    }

    const getVendorTypeBadgeClass = (vendorType) => {
      const classMap = {
        'ONBOARDED_WITH_RFP': 'badge-onboarded-rfp',
        'ONBOARDED_WITHOUT_RFP': 'badge-onboarded-no-rfp',
        'TEMPORARY_WITH_RFP': 'badge-temp-rfp',
        'TEMPORARY_WITHOUT_RFP': 'badge-temp-no-rfp'
      }
      return classMap[vendorType] || ''
    }

    const getRiskLevelClass = (riskLevel) => {
      const classMap = {
        'LOW': 'badge-success',
        'MEDIUM': 'badge-warning',
        'HIGH': 'badge-danger',
        'CRITICAL': 'badge-critical'
      }
      return classMap[riskLevel] || ''
    }

    const getStatusClass = (status) => {
      const classMap = {
        'DRAFT': 'badge-secondary',
        'SUBMITTED': 'badge-info',
        'IN_REVIEW': 'badge-warning',
        'APPROVED': 'badge-success',
        'REJECTED': 'badge-danger',
        'SUSPENDED': 'badge-warning',
        'TERMINATED': 'badge-dark'
      }
      return classMap[status] || ''
    }

    const formatDate = (dateString) => {
      if (!dateString) return 'N/A'
      const date = new Date(dateString)
      return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric' 
      })
    }

    onMounted(async () => {
      await fetchVendors()
      openDetailFromRoute()
    })

    watch(() => route.query, (query) => {
      if (query.vendorCode) openDetailFromRoute()
    }, { deep: true })

    return {
      vendors,
      loading,
      error,
      viewMode,
      filters,
      stats,
      filteredVendors,
      showDetailModal,
      selectedVendorCode,
      initialTabFromRoute,
      fetchVendors,
      viewVendorDetails,
      closeDetailModal,
      getVendorCardClass,
      getVendorTypeBadgeClass,
      getRiskLevelClass,
      getStatusClass,
      formatDate
    }
  }
}
</script>

<style scoped>
.all-vendors-container {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.vendors-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.vendors-title {
  font-size: 2rem;
  font-weight: 700;
  color: #1a202c;
  margin: 0;
}

.vendors-subtitle {
  color: #718096;
  margin: 0.5rem 0 0 0;
}

.header-actions {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.view-toggle {
  display: flex;
  gap: 0.5rem;
  background: #f7fafc;
  padding: 0.25rem;
  border-radius: 0.5rem;
}

.view-btn {
  padding: 0.5rem 1rem;
  border: none;
  background: transparent;
  color: #4a5568;
  cursor: pointer;
  border-radius: 0.375rem;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 500;
}

.view-btn:hover {
  background: #e2e8f0;
}

.view-btn.active {
  background: #fff;
  color: #2563eb;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* Stats Grid */
.stats-grid {
  display: grid;
  /* Desktop: force exactly 4 cards per row */
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}

.stat-card {
  background: #f9fafb;
  padding: 0.875rem 1rem;
  border-radius: 0.75rem;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
  display: flex;
  gap: 0.75rem;
  align-items: center;
  border: 1px solid #e5e7eb;
  transition: none;
}

.stat-card:hover {
  background: #f9fafb;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
  border-color: #e5e7eb;
}

/* Ensure no global gradient/top border effect is applied from shared .stat-card styles */
.stat-card::before,
.stat-card:hover::before {
  content: none !important;
}

.stat-icon {
  width: 2.25rem;
  height: 2.25rem;
  border-radius: 0.375rem;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.125rem;
  flex-shrink: 0;
}

.stat-onboarded-rfp .stat-icon {
  background: #d1fae5;
  color: #10b981;
}

.stat-onboarded-no-rfp .stat-icon {
  background: #dbeafe;
  color: #3b82f6;
}

.stat-temp-rfp .stat-icon {
  background: #fef3c7;
  color: #f59e0b;
}

.stat-temp-no-rfp .stat-icon {
  background: #ede9fe;
  color: #8b5cf6;
}

.stat-value {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1a202c;
}

.stat-label {
  font-size: 0.8125rem;
  color: #718096;
}

/* Filters */
.filters-section {
  background: #fff;
  padding: 1.5rem;
  border-radius: 0.75rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  margin-bottom: 2rem;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.filter-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #4a5568;
}

.filter-select {
  padding: 0.5rem 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  color: #1a202c;
  background: #fff;
}

.search-input-wrapper {
  position: relative;
}

.search-icon {
  position: absolute;
  left: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  color: #a0aec0;
}

.search-input {
  width: 100%;
  padding: 0.5rem 0.75rem 0.5rem 2.5rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.375rem;
  font-size: 0.875rem;
}

/* Loading, Error, Empty States */
.loading-container,
.error-container,
.empty-container {
  text-align: center;
  padding: 4rem 2rem;
  background: #fff;
  border-radius: 0.75rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.spinner {
  width: 3rem;
  height: 3rem;
  border: 4px solid #e2e8f0;
  border-top-color: #2563eb;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-container i,
.empty-container i {
  font-size: 3rem;
  color: #a0aec0;
  margin-bottom: 1rem;
}

/* Card View */
.vendors-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
}

.vendor-card {
  background: #fff;
  border-radius: 0.75rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  transition: all 0.2s;
  border-left: 4px solid;
}

.vendor-card:hover {
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.card-onboarded-rfp {
  border-color: #10b981;
}

.card-onboarded-no-rfp {
  border-color: #3b82f6;
}

.card-temp-rfp {
  border-color: #f59e0b;
}

.card-temp-no-rfp {
  border-color: #8b5cf6;
}

.vendor-card-header {
  padding: 1rem;
  background: #f7fafc;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #e2e8f0;
}

.vendor-type-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.badge-onboarded-rfp {
  background: #d1fae5;
  color: #065f46;
}

.badge-onboarded-no-rfp {
  background: #dbeafe;
  color: #1e40af;
}

.badge-temp-rfp {
  background: #fef3c7;
  color: #92400e;
}

.badge-temp-no-rfp {
  background: #ede9fe;
  color: #5b21b6;
}

.vendor-actions {
  display: flex;
  gap: 0.5rem;
}

.action-btn {
  padding: 0.5rem;
  border: none;
  background: transparent;
  color: #4a5568;
  cursor: pointer;
  border-radius: 0.375rem;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.action-btn:hover {
  background: #e2e8f0;
  color: #2563eb;
}

.view-btn-card {
  padding: 0.5rem 1rem;
  background: #2563eb;
  color: #fff;
  font-weight: 500;
  font-size: 0.875rem;
}

.view-btn-card:hover {
  background: #1d4ed8;
  color: #fff;
}

.view-btn-table {
  padding: 0.375rem 0.75rem;
  background: #2563eb;
  color: #fff;
  font-weight: 500;
  font-size: 0.75rem;
}

.view-btn-table:hover {
  background: #1d4ed8;
  color: #fff;
}

.table-actions {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  flex-wrap: wrap;
}

.screening-btn-table {
  padding: 0.375rem 0.75rem;
  background: #10b981;
  color: #fff;
  font-weight: 500;
  font-size: 0.75rem;
}

.screening-btn-table:hover {
  background: #059669;
  color: #fff;
}

.vendor-card-body {
  padding: 1.5rem;
}

.vendor-name {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1a202c;
  margin: 0 0 0.25rem 0;
}

.vendor-code {
  font-size: 0.875rem;
  color: #718096;
  font-family: monospace;
  margin: 0 0 1rem 0;
}

.vendor-details {
  margin-bottom: 1rem;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  padding: 0.5rem 0;
  border-bottom: 1px solid #f7fafc;
}

.detail-label {
  font-size: 0.875rem;
  color: #718096;
  font-weight: 500;
}

.detail-value {
  font-size: 0.875rem;
  color: #1a202c;
  text-align: right;
}

.vendor-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.badge {
  padding: 0.25rem 0.75rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.badge-success {
  background: #d1fae5;
  color: #065f46;
}

.badge-warning {
  background: #fef3c7;
  color: #92400e;
}

.badge-danger {
  background: #fee2e2;
  color: #991b1b;
}

.badge-critical {
  background: #fecaca;
  color: #7f1d1d;
}

.badge-info {
  background: #dbeafe;
  color: #1e40af;
}

.badge-secondary {
  background: #f3f4f6;
  color: #374151;
}

.badge-dark {
  background: #e5e7eb;
  color: #1f2937;
}

.vendor-card-footer {
  padding: 1rem 1.5rem;
  background: #f7fafc;
  border-top: 1px solid #e2e8f0;
}

.footer-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: #718096;
}

/* Table View */
.table-container {
  background: #fff;
  border-radius: 0.75rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow-x: auto;
}

.vendors-table {
  width: 100%;
  border-collapse: collapse;
}

.vendors-table thead {
  background: #f7fafc;
  border-bottom: 2px solid #e2e8f0;
}

.vendors-table th {
  padding: 1rem;
  text-align: left;
  font-size: 0.875rem;
  font-weight: 600;
  color: #4a5568;
  text-transform: uppercase;
}

.vendors-table tbody tr {
  border-bottom: 1px solid #e2e8f0;
  transition: background 0.2s;
}

.vendors-table tbody tr:hover {
  background: #f7fafc;
}

.vendors-table td {
  padding: 1rem;
  font-size: 0.875rem;
  color: #1a202c;
}

.vendor-code-cell {
  font-family: monospace;
  font-weight: 500;
  color: #2563eb;
}

.vendor-name-cell {
  font-weight: 600;
}

.table-badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  font-size: 0.7rem;
}

.flags-cell {
  display: flex;
  gap: 0.5rem;
}

.flag-icon {
  font-size: 1rem;
}

.text-red {
  color: #dc2626;
}

.text-blue {
  color: #2563eb;
}

.btn-sm {
  padding: 0.375rem 0.75rem;
  font-size: 0.875rem;
}

/* Responsive */
@media (max-width: 768px) {
  .vendors-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }

  .vendors-grid {
    grid-template-columns: 1fr;
  }

  .filters-section {
    grid-template-columns: 1fr;
  }

  .table-container {
    overflow-x: scroll;
  }

  /* On small screens, let the stats wrap nicely */
  .stats-grid {
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  }
}
</style>
