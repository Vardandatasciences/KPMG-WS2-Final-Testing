<template>
  <div class="vendor-risks-container">
    <!-- Filters -->
    <div class="filters-section">
      <div class="filter-group">
        <label class="filter-label">Status</label>
        <select v-model="filters.status" class="filter-select" @change="applyFilters">
          <option value="">All Statuses</option>
          <option value="OPEN">Open</option>
          <option value="CLOSED">Closed</option>
          <option value="MITIGATED">Mitigated</option>
          <option value="ACKNOWLEDGED">Acknowledged</option>
        </select>
      </div>
      <div class="filter-group">
        <label class="filter-label">Priority</label>
        <select v-model="filters.priority" class="filter-select" @change="applyFilters">
          <option value="">All Priorities</option>
          <option value="LOW">Low</option>
          <option value="MEDIUM">Medium</option>
          <option value="HIGH">High</option>
          <option value="CRITICAL">Critical</option>
        </select>
      </div>
      <div class="filter-group">
        <label class="filter-label">Risk Type</label>
        <select v-model="filters.risk_type" class="filter-select" @change="applyFilters">
          <option value="">All Types</option>
          <option value="OPERATIONAL">Operational</option>
          <option value="FINANCIAL">Financial</option>
          <option value="COMPLIANCE">Compliance</option>
          <option value="SECURITY">Security</option>
          <option value="REPUTATIONAL">Reputational</option>
        </select>
      </div>
      <div class="filter-group">
        <label class="filter-label">Entity</label>
        <select v-model="filters.entity" class="filter-select" @change="applyFilters">
          <option value="">All Entities</option>
          <option v-for="entity in uniqueEntities" :key="entity" :value="entity">
            {{ entity || 'N/A' }}
          </option>
        </select>
      </div>
      <div class="filter-group">
        <label class="filter-label">Vendor</label>
        <select 
          v-model="filters.vendor_id" 
          class="filter-select" 
          @change="applyFilters"
          :disabled="loadingVendors"
        >
          <option value="">All Vendors</option>
          <option 
            v-if="loadingVendors"
            value=""
            disabled
          >
            Loading vendors...
          </option>
          <option 
            v-for="vendor in vendors" 
            :key="vendor.vendor_id || vendor.id || `vendor-${vendors.indexOf(vendor)}`" 
            :value="vendor.vendor_id || vendor.id"
          >
            {{ vendor.company_name || 'Unknown Vendor' }} {{ vendor.vendor_code ? `(${vendor.vendor_code})` : (vendor.vendor_id ? `(${vendor.vendor_id})` : vendor.id ? `(${vendor.id})` : '') }}
          </option>
          <option 
            v-if="!loadingVendors && vendors.length === 0"
            value=""
            disabled
          >
            No vendors available
          </option>
        </select>
      </div>
      <div class="filter-group filter-search">
        <label class="filter-label">Search</label>
        <input 
          type="text" 
          v-model="filters.search" 
          @input="debouncedSearch"
          placeholder="Search by title or description..."
          class="filter-input"
        />
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading && risks.length === 0" class="loading-container">
      <div class="spinner"></div>
      <p>Loading vendor risks...</p>
    </div>

    <!-- Error State -->
    <div v-if="error && !loading" class="error-container">
      <div class="error-message">
        <i class="fas fa-exclamation-circle"></i>
        <p>{{ error }}</p>
        <button @click="fetchRisks" class="btn btn-primary">Retry</button>
      </div>
    </div>

    <!-- Risks Table -->
    <div v-if="!loading || risks.length > 0" class="table-container">
      <div class="table-header">
        <div class="table-info">
          <span>Showing {{ risks.length }} of {{ total }} risks</span>
        </div>
        <div class="header-actions">
          <button 
            @click="exportToExcel" 
            class="btn btn-sm btn-success"
            :disabled="loading || exporting"
            title="Export Risks to Excel"
          >
            <i class="fas fa-file-excel" :class="{ 'fa-spin': exporting }"></i>
            {{ exporting ? 'Exporting...' : 'Export to Excel' }}
          </button>
          <button 
            @click="refreshRisks" 
            class="btn btn-sm btn-primary"
            :disabled="loading"
            title="Refresh Risks"
          >
            <i class="fas fa-sync-alt" :class="{ 'fa-spin': loading }"></i>
            Refresh
          </button>
        </div>
      </div>

      <table class="risks-table">
        <thead>
          <tr>
            <th class="col-id">ID</th>
            <th class="col-title">TITLE</th>
            <th class="col-description">DESCRIPTION</th>
            <th class="col-likelihood">LIKELIHOOD</th>
            <th class="col-impact">IMPACT</th>
            <th class="col-score">SCORE</th>
            <th class="col-priority">PRIORITY</th>
            <th class="col-status">STATUS</th>
            <th class="col-risk-type">RISK TYPE</th>
            <th class="col-entity">ENTITY</th>
            <th class="col-exposure">EXPOSURE RATING</th>
            <th class="col-created">CREATED AT</th>
            <th class="col-updated">UPDATED AT</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="risks.length === 0 && !loading">
            <td colspan="13" class="no-data">
              <div class="no-data-message">
                <i class="fas fa-inbox"></i>
                <p>No vendor risks found</p>
              </div>
            </td>
          </tr>
          <tr v-for="risk in risks" :key="risk.id" class="risk-row">
            <td class="risk-id col-id">{{ risk.id }}</td>
            <td class="risk-title col-title">
              <span :title="risk.title || 'No title'">
                {{ truncateText(risk.title, 100) || 'N/A' }}
              </span>
            </td>
            <td class="risk-description col-description">
              <span :title="risk.description || 'No description'">
                {{ truncateText(risk.description, 100) || 'N/A' }}
              </span>
            </td>
            <td class="col-likelihood">
              <span class="badge badge-likelihood" :class="getLikelihoodClass(risk.likelihood)">
                {{ risk.likelihood }}
              </span>
            </td>
            <td class="col-impact">
              <span class="badge badge-impact" :class="getImpactClass(risk.impact)">
                {{ risk.impact }}
              </span>
            </td>
            <td class="col-score">
              <span class="badge badge-score" :class="getScoreClass(risk.score)">
                {{ risk.score.toFixed(2) }}
              </span>
            </td>
            <td class="col-priority">
              <span class="badge" :class="getPriorityClass(risk.priority)">
                {{ risk.priority || 'N/A' }}
              </span>
            </td>
            <td class="col-status">
              <span class="badge" :class="getStatusClass(risk.status)">
                {{ risk.status || 'N/A' }}
              </span>
            </td>
            <td class="col-risk-type">{{ risk.risk_type || 'N/A' }}</td>
            <td class="col-entity">{{ risk.entity || 'N/A' }}</td>
            <td class="col-exposure">
              <span class="badge badge-exposure" :class="getExposureClass(risk.exposure_rating)">
                {{ risk.exposure_rating }}
              </span>
            </td>
            <td class="col-created">{{ formatDate(risk.created_at) }}</td>
            <td class="col-updated">{{ formatDate(risk.updated_at) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination Controls - Outside table container -->
    <div v-if="!loading || risks.length > 0" class="pagination-footer">
      <div class="pagination-controls">
        <div class="page-size-selector">
          <label>Items per page:</label>
          <select v-model="pageSize" @change="onPageSizeChange" class="page-size-select">
            <option :value="10">10</option>
            <option :value="25">25</option>
            <option :value="50">50</option>
            <option :value="100">100</option>
            <option :value="200">200</option>
            <option :value="500">500</option>
          </select>
        </div>
        <button 
          @click="goToPage(currentPage - 1)" 
          :disabled="currentPage === 1 || loading"
          class="btn btn-sm"
        >
          <i class="fas fa-chevron-left"></i> Previous
        </button>
        <span class="page-info">Page {{ currentPage }} of {{ totalPages }}</span>
        <button 
          @click="goToPage(currentPage + 1)" 
          :disabled="currentPage >= totalPages || loading"
          class="btn btn-sm"
        >
          Next <i class="fas fa-chevron-right"></i>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import axios from '@/config/axios'

export default {
  name: 'VendorRisks',
  setup() {
    const risks = ref([])
    const loading = ref(false)
    const error = ref(null)
    const total = ref(0)
    const currentPage = ref(1)
    const pageSize = ref(10)
    const totalPages = ref(1)
    const uniqueEntities = ref([])
    const vendors = ref([])
    const loadingVendors = ref(false)
    const exporting = ref(false)
    
    const filters = ref({
      status: '',
      priority: '',
      risk_type: '',
      entity: '',
      vendor_id: '',
      search: ''
    })

    let searchTimeout = null

    const fetchRisks = async () => {
      loading.value = true
      error.value = null
      
      try {
        const params = {
          page: currentPage.value,
          page_size: pageSize.value
        }
        
        if (filters.value.status) {
          params.status = filters.value.status
        }
        if (filters.value.priority) {
          params.priority = filters.value.priority
        }
        if (filters.value.risk_type) {
          params.risk_type = filters.value.risk_type
        }
        if (filters.value.entity) {
          params.entity = filters.value.entity
        }
        if (filters.value.vendor_id) {
          params.vendor_id = filters.value.vendor_id
        }
        if (filters.value.search) {
          params.search = filters.value.search
        }
        
        console.log('[VendorRisks] Fetching risks with params:', params)
        
        // Remove timeout constraint for this request - let it take as long as needed
        // Using a very large timeout (1 hour) instead of 0 for better compatibility
        const response = await axios.get('/api/v1/management/vendor-risks/', { 
          params,
          timeout: 3600000 // 1 hour timeout (3600000ms) - effectively no timeout for practical purposes
        })
        
        if (response.data.success) {
          risks.value = response.data.data || []
          total.value = response.data.total || 0
          totalPages.value = response.data.total_pages || 1
          
          // Use unique entities from API response (includes all entities from database)
          if (response.data.unique_entities && Array.isArray(response.data.unique_entities)) {
            uniqueEntities.value = response.data.unique_entities.filter(e => e && e.trim()).sort()
            console.log('[VendorRisks] Updated unique entities from API:', uniqueEntities.value.length, 'entities')
          }
          
          console.log('[VendorRisks] Fetched risks:', risks.value.length, 'of', total.value)
        } else {
          throw new Error(response.data.error || 'Failed to fetch vendor risks')
        }
      } catch (err) {
        console.error('[VendorRisks] Error fetching risks:', err)
        error.value = err.response?.data?.error || err.message || 'Failed to load vendor risks'
      } finally {
        loading.value = false
      }
    }

    const updateUniqueEntities = () => {
      // Extract unique entity values from currently loaded risks
      const entities = new Set(uniqueEntities.value) // Keep existing entities
      
      risks.value.forEach(risk => {
        if (risk.entity && risk.entity.trim()) {
          entities.add(risk.entity.trim())
        }
      })
      
      uniqueEntities.value = Array.from(entities).sort()
      console.log('[VendorRisks] Updated unique entities:', uniqueEntities.value.length, 'entities')
    }

    const refreshRisks = () => {
      currentPage.value = 1
      fetchRisks()
    }

    const applyFilters = () => {
      currentPage.value = 1
      fetchRisks()
    }

    const debouncedSearch = () => {
      if (searchTimeout) {
        clearTimeout(searchTimeout)
      }
      searchTimeout = setTimeout(() => {
        applyFilters()
      }, 500)
    }

    const goToPage = (page) => {
      if (page >= 1 && page <= totalPages.value) {
        currentPage.value = page
        fetchRisks()
      }
    }

    const onPageSizeChange = () => {
      currentPage.value = 1
      fetchRisks()
    }

    const formatDate = (dateString) => {
      if (!dateString) return 'N/A'
      try {
        const date = new Date(dateString)
        return date.toLocaleDateString('en-US', {
          year: 'numeric',
          month: 'short',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit'
        })
      } catch (e) {
        return dateString
      }
    }

    const truncateText = (text, maxLength) => {
      if (!text) return ''
      if (text.length <= maxLength) return text
      return text.substring(0, maxLength) + '...'
    }

    const getPriorityClass = (priority) => {
      if (!priority) return 'badge-default'
      const p = priority.toUpperCase()
      if (p === 'CRITICAL') return 'badge-critical'
      if (p === 'HIGH') return 'badge-high'
      if (p === 'MEDIUM') return 'badge-medium'
      if (p === 'LOW') return 'badge-low'
      return 'badge-default'
    }

    const getStatusClass = (status) => {
      if (!status) return 'badge-default'
      const s = status.toUpperCase()
      if (s === 'OPEN') return 'badge-open'
      if (s === 'CLOSED') return 'badge-closed'
      if (s === 'MITIGATED') return 'badge-mitigated'
      if (s === 'ACKNOWLEDGED') return 'badge-acknowledged'
      return 'badge-default'
    }

    const getLikelihoodClass = (likelihood) => {
      if (likelihood >= 8) return 'badge-high'
      if (likelihood >= 5) return 'badge-medium'
      return 'badge-low'
    }

    const getImpactClass = (impact) => {
      if (impact >= 8) return 'badge-high'
      if (impact >= 5) return 'badge-medium'
      return 'badge-low'
    }

    const getScoreClass = (score) => {
      if (score >= 64) return 'badge-critical'
      if (score >= 25) return 'badge-high'
      if (score >= 9) return 'badge-medium'
      return 'badge-low'
    }

    const getExposureClass = (rating) => {
      if (rating >= 8) return 'badge-high'
      if (rating >= 5) return 'badge-medium'
      return 'badge-low'
    }

    const fetchVendors = async () => {
      loadingVendors.value = true
      vendors.value = [] // Reset vendors array
      
      try {
        // Fetch only vendors from vendors table (onboarded vendors)
        console.log('[VendorRisks] Fetching vendors from dropdown endpoint: /api/v1/management/vendors/dropdown/')
        
        const response = await axios.get('/api/v1/management/vendors/dropdown/', {
          timeout: 30000 // 30 second timeout
        })
        
        console.log('[VendorRisks] Response status:', response.status)
        console.log('[VendorRisks] Response data:', JSON.stringify(response.data, null, 2))
        
        // Handle different response structures
        let vendorData = []
        
        if (response.data) {
          // Check if response has success field
          if (response.data.success !== undefined) {
            if (response.data.success) {
              vendorData = response.data.data || response.data.vendors || []
            } else {
              console.warn('[VendorRisks] API returned success=false:', response.data.error || response.data.message)
              vendorData = []
            }
          } else {
            // Response might be direct array or have different structure
            if (Array.isArray(response.data)) {
              vendorData = response.data
            } else if (response.data.data && Array.isArray(response.data.data)) {
              vendorData = response.data.data
            } else if (response.data.vendors && Array.isArray(response.data.vendors)) {
              vendorData = response.data.vendors
            } else {
              console.warn('[VendorRisks] Unexpected response structure:', response.data)
              vendorData = []
            }
          }
        }
        
        // Normalize vendor data to ensure consistent structure
        vendorData = vendorData.map(vendor => {
          return {
            vendor_id: vendor.vendor_id || vendor.id || vendor.vendorId,
            company_name: vendor.company_name || vendor.companyName || vendor.name || 'Unknown Vendor',
            vendor_code: vendor.vendor_code || vendor.vendorCode || vendor.code || null,
            ...vendor // Keep all other fields
          }
        })
        
        vendors.value = vendorData
        console.log('[VendorRisks] Processed vendors:', vendors.value.length, 'vendors')
        
        if (vendors.value.length > 0) {
          console.log('[VendorRisks] First vendor:', {
            vendor_id: vendors.value[0].vendor_id,
            company_name: vendors.value[0].company_name,
            vendor_code: vendors.value[0].vendor_code
          })
        } else {
          console.warn('[VendorRisks] No vendors returned from API. This might be normal if no vendors exist in the database.')
        }
        
      } catch (err) {
        console.error('[VendorRisks] Error fetching vendors:', err)
        console.error('[VendorRisks] Error details:', {
          message: err.message,
          response: err.response?.data,
          status: err.response?.status,
          statusText: err.response?.statusText,
          url: err.config?.url
        })
        
        // Check for specific error types
        if (err.response?.status === 401) {
          console.warn('[VendorRisks] 401 Unauthorized - Authentication required')
        } else if (err.response?.status === 403) {
          console.warn('[VendorRisks] 403 Forbidden - Insufficient permissions')
        } else if (err.response?.status === 404) {
          console.error('[VendorRisks] 404 Not Found - Endpoint does not exist. URL:', err.config?.url)
        } else if (err.response?.status === 500) {
          console.error('[VendorRisks] 500 Server Error - Backend error:', err.response?.data)
        } else if (err.code === 'ECONNABORTED') {
          console.error('[VendorRisks] Request timeout - Server took too long to respond')
        }
        
        vendors.value = []
        // Don't show error to user, just log it - vendor filter is optional
      } finally {
        loadingVendors.value = false
        console.log('[VendorRisks] fetchVendors completed. Vendors count:', vendors.value.length)
      }
    }

    const exportToExcel = async () => {
      exporting.value = true
      try {
        // Build query parameters with current filters
        const params = {}
        
        if (filters.value.status) {
          params.status = filters.value.status
        }
        if (filters.value.priority) {
          params.priority = filters.value.priority
        }
        if (filters.value.risk_type) {
          params.risk_type = filters.value.risk_type
        }
        if (filters.value.entity) {
          params.entity = filters.value.entity
        }
        if (filters.value.vendor_id) {
          params.vendor_id = filters.value.vendor_id
        }
        if (filters.value.search) {
          params.search = filters.value.search
        }
        
        console.log('[VendorRisks] Exporting risks with params:', params)
        
        // Make request to export endpoint
        const response = await axios.get('/api/v1/management/vendor-risks/export/', {
          params,
          responseType: 'blob', // Important for file download
          timeout: 3600000 // 1 hour timeout for large exports
        })
        
        // Create download link
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        
        // Get filename from Content-Disposition header or use default
        const contentDisposition = response.headers['content-disposition']
        let filename = 'vendor-risks-export.xlsx'
        if (contentDisposition) {
          const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/)
          if (filenameMatch && filenameMatch[1]) {
            filename = filenameMatch[1].replace(/['"]/g, '')
          }
        }
        
        link.setAttribute('download', filename)
        document.body.appendChild(link)
        link.click()
        link.remove()
        window.URL.revokeObjectURL(url)
        
        console.log('[VendorRisks] Excel export completed successfully')
      } catch (err) {
        console.error('[VendorRisks] Error exporting to Excel:', err)
        error.value = err.response?.data?.error || err.message || 'Failed to export risks to Excel'
        alert('Failed to export risks to Excel. Please try again.')
      } finally {
        exporting.value = false
      }
    }

    onMounted(() => {
      fetchRisks()
      fetchVendors()
    })

    return {
      risks,
      loading,
      error,
      total,
      currentPage,
      pageSize,
      totalPages,
      filters,
      uniqueEntities,
      vendors,
      loadingVendors,
      exporting,
      fetchRisks,
      refreshRisks,
      applyFilters,
      debouncedSearch,
      goToPage,
      onPageSizeChange,
      formatDate,
      truncateText,
      getPriorityClass,
      getStatusClass,
      getLikelihoodClass,
      getImpactClass,
      getScoreClass,
      getExposureClass,
      exportToExcel
    }
  }
}
</script>

<style scoped>
.vendor-risks-container {
  padding: 0;
  max-width: 100%;
  margin: 0;
  background: transparent;
  display: flex;
  flex-direction: column;
}

.risks-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  padding: 20px;
  background: transparent;
  flex-shrink: 0;
}

.risks-title {
  font-size: 28px;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 8px 0;
}

.risks-subtitle {
  font-size: 14px;
  color: #6b7280;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.filters-section {
  display: flex;
  gap: 10px;
  margin-bottom: 8px;
  padding: 8px 20px;
  background: transparent;
  flex-wrap: wrap;
  flex-shrink: 0;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 130px;
}

.filter-group.filter-search {
  flex: 1;
  min-width: 250px;
}

.filter-label {
  font-size: 11px;
  font-weight: 600;
  color: #374151;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.filter-select,
.filter-input {
  padding: 5px 8px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 12px;
  color: #1f2937;
  background: white;
  transition: border-color 0.2s;
}

.filter-select:focus,
.filter-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.loading-container,
.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-message {
  text-align: center;
  color: #dc2626;
}

.error-message i {
  font-size: 48px;
  margin-bottom: 16px;
}

.table-container {
  background: transparent;
  display: flex;
  flex-direction: column;
  padding: 0 20px 8px 20px;
  overflow-x: auto;
  max-width: 100%;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 20px;
  border-bottom: 1px solid #e5e7eb;
  background: transparent;
  flex-shrink: 0;
}

.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.pagination-footer {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  padding: 16px 20px;
  margin-top: 16px;
  border-top: 1px solid #e5e7eb;
  background: transparent;
  width: 100%;
}

.page-size-selector {
  display: flex;
  align-items: center;
  gap: 6px;
}

.page-size-selector label {
  font-size: 12px;
  color: #374151;
}

.page-size-select {
  padding: 5px 10px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 12px;
  color: #1f2937;
  background: white;
  cursor: pointer;
}

.page-size-select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.table-info {
  font-size: 12px;
  color: #6b7280;
}

.pagination-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.page-info {
  font-size: 12px;
  color: #374151;
  font-weight: 500;
}

.risks-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  table-layout: fixed;
  border: 1px solid #e5e7eb;
}

.risks-table thead {
  background: #f9fafb;
}

.risks-table th {
  padding: 10px 12px;
  text-align: left;
  font-size: 11px;
  font-weight: 600;
  color: #374151;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 2px solid #e5e7eb;
  white-space: nowrap;
  position: sticky;
  top: 0;
  background: #f9fafb;
  z-index: 10;
}

.risks-table th.col-id {
  width: 80px;
  min-width: 80px;
}

.risks-table th.col-title {
  width: 200px;
  min-width: 150px;
}

.risks-table th.col-description {
  width: 250px;
  min-width: 200px;
}

.risks-table th.col-likelihood,
.risks-table th.col-impact,
.risks-table th.col-exposure {
  width: 90px;
  min-width: 90px;
  text-align: center;
}

.risks-table th.col-score {
  width: 100px;
  min-width: 100px;
  text-align: center;
}

.risks-table th.col-priority,
.risks-table th.col-status {
  width: 110px;
  min-width: 100px;
  text-align: center;
}

.risks-table th.col-risk-type {
  width: 120px;
  min-width: 100px;
}

.risks-table th.col-entity {
  width: 150px;
  min-width: 120px;
}

.risks-table th.col-created,
.risks-table th.col-updated {
  width: 160px;
  min-width: 140px;
}

.risks-table td {
  padding: 10px 12px;
  border-bottom: 1px solid #e5e7eb;
  font-size: 12px;
  color: #1f2937;
  vertical-align: middle;
}

.risks-table td.col-likelihood,
.risks-table td.col-impact,
.risks-table td.col-exposure {
  text-align: center;
}

.risks-table td.col-score,
.risks-table td.col-priority,
.risks-table td.col-status {
  text-align: center;
}

.risks-table tbody tr:hover {
  background: #f9fafb;
}

.risk-id {
  font-weight: 600;
  color: #3b82f6;
}

.risk-title {
  font-weight: 600;
  color: #1f2937;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.risk-title span {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.risk-description {
  max-width: 300px;
  color: #6b7280;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.risk-description span {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.no-data {
  text-align: center;
  padding: 60px 20px;
}

.no-data-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: #9ca3af;
}

.no-data-message i {
  font-size: 48px;
}

.badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.badge-critical {
  background: #fee2e2;
  color: #991b1b;
}

.badge-high {
  background: #fed7aa;
  color: #92400e;
}

.badge-medium {
  background: #fef3c7;
  color: #78350f;
}

.badge-low {
  background: #d1fae5;
  color: #065f46;
}

.badge-default {
  background: #e5e7eb;
  color: #374151;
}

.badge-open {
  background: #dbeafe;
  color: #1e40af;
}

.badge-closed {
  background: #e5e7eb;
  color: #374151;
}

.badge-mitigated {
  background: #d1fae5;
  color: #065f46;
}

.badge-acknowledged {
  background: #fef3c7;
  color: #78350f;
}

.btn {
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.btn-primary {
  background: #3b82f6;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #2563eb;
}

.btn-primary:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

.btn-success {
  background: #10b981;
  color: white;
}

.btn-success:hover:not(:disabled) {
  background: #059669;
}

.btn-success:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

.btn-sm {
  padding: 5px 10px;
  font-size: 11px;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 1200px) {
  .risks-table {
    font-size: 12px;
  }
  
  .risks-table th,
  .risks-table td {
    padding: 8px 12px;
  }
}

@media (max-width: 768px) {
  .vendor-risks-container {
    padding: 16px;
  }
  
  .risks-header {
    flex-direction: column;
    gap: 16px;
  }
  
  .filters-section {
    flex-direction: column;
  }
  
  .filter-group {
    width: 100%;
  }
  
  .table-header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
  
  .pagination-footer {
    justify-content: center;
  }
  
  .pagination-controls {
    flex-wrap: wrap;
    justify-content: center;
    gap: 8px;
  }
  
  .risks-table {
    display: block;
  }
}
</style>

