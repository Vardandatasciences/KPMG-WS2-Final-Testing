<template>
  <div class="modal-overlay" @click.self="closeModal">
    <div class="modal-container">
      <!-- Modal Header -->
      <div class="modal-header">
        <h2 class="modal-title">Vendor Details</h2>
        <button @click="closeModal" class="close-btn">
          <i class="fas fa-times"></i>
        </button>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="modal-body loading-state">
        <div class="spinner"></div>
        <p>Loading vendor details...</p>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="modal-body error-state">
        <i class="fas fa-exclamation-triangle"></i>
        <p>{{ error }}</p>
        <button @click="fetchVendorDetails" class="btn btn-primary">Retry</button>
      </div>

      <!-- Vendor Details -->
      <div v-else-if="vendor" class="modal-body">
        <!-- Vendor Type Badge -->
        <div class="vendor-type-banner" :class="getBannerClass(vendor.vendor_type)">
          <i class="fas fa-info-circle"></i>
          <span>{{ vendor.vendor_type_label }}</span>
        </div>

        <!-- Tabs - Horizontal Layout -->
        <div class="tabs-container">
          <div class="tabs-wrapper">
            <button 
              v-for="tab in tabs" 
              :key="tab.id"
              class="tab"
              :class="{ active: activeTab === tab.id }"
              @click="activeTab = tab.id"
            >
              <i :class="tab.icon"></i>
              <span class="tab-label">{{ tab.label }}</span>
            </button>
          </div>

          <!-- Tab Content -->
          <div class="tab-content-wrapper">
            <div class="tab-content">
            <!-- Company Information Tab -->
            <div v-if="activeTab === 'company'" class="info-section">
              <h3 class="section-title">Company Information</h3>
              <div class="info-grid">
                <div class="info-item">
                  <label>Vendor Code</label>
                  <p>{{ vendor.vendor_code || 'N/A' }}</p>
                </div>
                <div class="info-item">
                  <label>Company Name</label>
                  <p>{{ vendor.company_name || 'N/A' }}</p>
                </div>
                <div class="info-item">
                  <label>Legal Name</label>
                  <p>{{ vendor.legal_name || 'N/A' }}</p>
                </div>
                <div class="info-item">
                  <label>Business Type</label>
                  <p>{{ vendor.business_type || 'N/A' }}</p>
                </div>
                <div class="info-item">
                  <label>Industry Sector</label>
                  <p>{{ vendor.industry_sector || 'N/A' }}</p>
                </div>
                <div class="info-item" v-if="!vendor.is_temporary">
                  <label>Incorporation Date</label>
                  <p>{{ formatDate(vendor.incorporation_date) }}</p>
                </div>
                <div class="info-item" v-if="!vendor.is_temporary">
                  <label>Tax ID</label>
                  <p>{{ vendor.tax_id || 'N/A' }}</p>
                </div>
                <div class="info-item" v-if="!vendor.is_temporary">
                  <label>DUNS Number</label>
                  <p>{{ vendor.duns_number || 'N/A' }}</p>
                </div>
                <div class="info-item">
                  <label>Website</label>
                  <p>
                    <a v-if="vendor.website" :href="vendor.website" target="_blank" class="link">
                      {{ vendor.website }}
                    </a>
                    <span v-else>N/A</span>
                  </p>
                </div>
                <div class="info-item" v-if="!vendor.is_temporary">
                  <label>Annual Revenue</label>
                  <p>{{ formatCurrency(vendor.annual_revenue) }}</p>
                </div>
                <div class="info-item">
                  <label>Employee Count</label>
                  <p>{{ vendor.employee_count || 'N/A' }}</p>
                </div>
                <div class="info-item" v-if="!vendor.is_temporary">
                  <label>Headquarters Country</label>
                  <p>{{ vendor.headquarters_country || 'N/A' }}</p>
                </div>
                <div class="info-item full-width" v-if="!vendor.is_temporary">
                  <label>Headquarters Address</label>
                  <p>{{ vendor.headquarters_address || 'N/A' }}</p>
                </div>
                <div class="info-item full-width">
                  <label>Description</label>
                  <p>{{ vendor.description || 'N/A' }}</p>
                </div>
              </div>
            </div>

            <!-- Risk & Status Tab -->
            <div v-if="activeTab === 'risk'" class="info-section">
              <h3 class="section-title">Risk & Status Information</h3>
              <div class="info-grid">
                <div class="info-item">
                  <label>Risk Level</label>
                  <p>
                    <span 
                      v-if="vendor.risk_level" 
                      class="badge"
                      :class="getRiskLevelClass(vendor.risk_level)"
                    >
                      {{ vendor.risk_level }}
                    </span>
                    <span v-else>N/A</span>
                  </p>
                </div>
                <div class="info-item">
                  <label>Status</label>
                  <p>
                    <span 
                      v-if="vendor.status" 
                      class="badge"
                      :class="getStatusClass(vendor.status)"
                    >
                      {{ vendor.status }}
                    </span>
                    <span v-else>N/A</span>
                  </p>
                </div>
                <div class="info-item">
                  <label>Lifecycle Stage</label>
                  <p>{{ vendor.lifecycle_stage || 'N/A' }}</p>
                </div>
                <div class="info-item">
                  <label>Critical Vendor</label>
                  <p>
                    <span :class="vendor.is_critical_vendor ? 'text-danger' : 'text-muted'">
                      {{ vendor.is_critical_vendor ? 'Yes' : 'No' }}
                    </span>
                  </p>
                </div>
                <div class="info-item">
                  <label>Has Data Access</label>
                  <p>
                    <span :class="vendor.has_data_access ? 'text-info' : 'text-muted'">
                      {{ vendor.has_data_access ? 'Yes' : 'No' }}
                    </span>
                  </p>
                </div>
                <div class="info-item">
                  <label>Has System Access</label>
                  <p>
                    <span :class="vendor.has_system_access ? 'text-info' : 'text-muted'">
                      {{ vendor.has_system_access ? 'Yes' : 'No' }}
                    </span>
                  </p>
                </div>
                <div class="info-item" v-if="!vendor.is_temporary">
                  <label>Onboarding Date</label>
                  <p>{{ formatDate(vendor.onboarding_date) }}</p>
                </div>
                <div class="info-item" v-if="!vendor.is_temporary">
                  <label>Last Assessment Date</label>
                  <p>{{ formatDate(vendor.last_assessment_date) }}</p>
                </div>
                <div class="info-item" v-if="!vendor.is_temporary">
                  <label>Next Assessment Date</label>
                  <p>{{ formatDate(vendor.next_assessment_date) }}</p>
                </div>
                <div class="info-item" v-if="vendor.response_id">
                  <label>RFP Response ID</label>
                  <p class="response-id">{{ vendor.response_id }}</p>
                </div>
              </div>
            </div>

            <!-- Contacts Tab (for temporary vendors with JSON contacts) -->
            <div v-if="activeTab === 'contacts'" class="info-section">
              <h3 class="section-title">Contact Information</h3>
              <div v-if="vendor.contacts && vendor.contacts.length > 0" class="contacts-list">
                <div 
                  v-for="(contact, index) in vendor.contacts" 
                  :key="index"
                  class="contact-card"
                >
                  <h4 class="contact-name">{{ contact.name || 'N/A' }}</h4>
                  <div class="contact-details">
                    <div v-if="contact.email" class="contact-detail">
                      <i class="fas fa-envelope"></i>
                      <a :href="`mailto:${contact.email}`">{{ contact.email }}</a>
                    </div>
                    <div v-if="contact.phone" class="contact-detail">
                      <i class="fas fa-phone"></i>
                      <span>{{ contact.phone }}</span>
                    </div>
                    <div v-if="contact.designation" class="contact-detail">
                      <i class="fas fa-briefcase"></i>
                      <span>{{ contact.designation }}</span>
                    </div>
                  </div>
                </div>
              </div>
              <div v-else class="empty-state">
                <i class="fas fa-address-book"></i>
                <p>No contact information available</p>
              </div>
            </div>

            <!-- Documents Tab (for temporary vendors with JSON documents) -->
            <div v-if="activeTab === 'documents'" class="info-section">
              <h3 class="section-title">Documents</h3>
              <div v-if="vendor.documents && vendor.documents.length > 0" class="documents-list">
                <div 
                  v-for="(document, index) in vendor.documents" 
                  :key="index"
                  class="document-card"
                >
                  <i class="fas fa-file-alt document-icon"></i>
                  <div class="document-info">
                    <h4 class="document-name">{{ document.name || 'Document' }}</h4>
                    <p class="document-type">{{ document.type || 'Unknown Type' }}</p>
                  </div>
                </div>
              </div>
              <div v-else class="empty-state">
                <i class="fas fa-folder-open"></i>
                <p>No documents available</p>
              </div>
            </div>

            <!-- Audit Trail Tab -->
            <div v-if="activeTab === 'audit'" class="info-section">
              <h3 class="section-title">Audit Trail</h3>
              <div class="info-grid">
                <div class="info-item" v-if="!vendor.is_temporary && vendor.created_by">
                  <label>Created By</label>
                  <p>{{ vendor.created_by }}</p>
                </div>
                <div class="info-item">
                  <label>Created At</label>
                  <p>{{ formatDateTime(vendor.created_at) }}</p>
                </div>
                <div class="info-item" v-if="!vendor.is_temporary && vendor.updated_by">
                  <label>Updated By</label>
                  <p>{{ vendor.updated_by }}</p>
                </div>
                <div class="info-item">
                  <label>Updated At</label>
                  <p>{{ formatDateTime(vendor.updated_at) }}</p>
                </div>
              </div>
            </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Modal Footer -->
      <div class="modal-footer">
        <button @click="closeModal" class="btn btn-secondary">Close</button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import axios from '@/config/axios'

export default {
  name: 'VendorDetailModal',
  props: {
    vendorCode: {
      type: String,
      required: true
    }
  },
  emits: ['close'],
  setup(props, { emit }) {
    const vendor = ref(null)
    const loading = ref(false)
    const error = ref(null)
    const activeTab = ref('company')

    const tabs = computed(() => {
      const baseTabs = [
        { id: 'company', label: 'Company Info', icon: 'fas fa-building' },
        { id: 'risk', label: 'Risk & Status', icon: 'fas fa-shield-alt' },
        { id: 'audit', label: 'Audit Trail', icon: 'fas fa-history' }
      ]

      // Add contacts and documents tabs for temporary vendors
      if (vendor.value?.is_temporary) {
        baseTabs.splice(2, 0, 
          { id: 'contacts', label: 'Contacts', icon: 'fas fa-address-book' },
          { id: 'documents', label: 'Documents', icon: 'fas fa-file-alt' }
        )
      }

      return baseTabs
    })

    const fetchVendorDetails = async () => {
      loading.value = true
      error.value = null

      try {
        const response = await axios.get(`/api/v1/management/vendors/${props.vendorCode}/`)

        if (response.data.success) {
          vendor.value = response.data.data
          
          // Parse JSON fields if they are strings
          if (vendor.value.contacts && typeof vendor.value.contacts === 'string') {
            try {
              vendor.value.contacts = JSON.parse(vendor.value.contacts)
            } catch (e) {
              console.warn('Failed to parse contacts JSON:', e)
              vendor.value.contacts = []
            }
          }
          
          if (vendor.value.documents && typeof vendor.value.documents === 'string') {
            try {
              vendor.value.documents = JSON.parse(vendor.value.documents)
            } catch (e) {
              console.warn('Failed to parse documents JSON:', e)
              vendor.value.documents = []
            }
          }
        } else {
          error.value = 'Failed to load vendor details'
        }
      } catch (err) {
        console.error('Error fetching vendor details:', err)
        error.value = err.response?.data?.error || 'Failed to load vendor details'
      } finally {
        loading.value = false
      }
    }

    const closeModal = () => {
      emit('close')
    }

    const getBannerClass = (vendorType) => {
      const classMap = {
        'ONBOARDED_WITH_RFP': 'banner-onboarded-rfp',
        'ONBOARDED_WITHOUT_RFP': 'banner-onboarded-no-rfp',
        'TEMPORARY_WITH_RFP': 'banner-temp-rfp',
        'TEMPORARY_WITHOUT_RFP': 'banner-temp-no-rfp'
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
        month: 'long', 
        day: 'numeric' 
      })
    }

    const formatDateTime = (dateString) => {
      if (!dateString) return 'N/A'
      const date = new Date(dateString)
      return date.toLocaleString('en-US', { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    }

    const formatCurrency = (amount) => {
      if (!amount) return 'N/A'
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
      }).format(amount)
    }

    onMounted(() => {
      fetchVendorDetails()
    })

    return {
      vendor,
      loading,
      error,
      activeTab,
      tabs,
      fetchVendorDetails,
      closeModal,
      getBannerClass,
      getRiskLevelClass,
      getStatusClass,
      formatDate,
      formatDateTime,
      formatCurrency
    }
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal-container {
  background: #fff;
  border-radius: 0.75rem;
  width: 100%;
  max-width: 900px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
}

.modal-header {
  padding: 1.5rem;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1a202c;
  margin: 0;
}

.close-btn {
  padding: 0.5rem;
  border: none;
  background: transparent;
  color: #718096;
  cursor: pointer;
  border-radius: 0.375rem;
  transition: all 0.2s;
  font-size: 1.25rem;
}

.close-btn:hover {
  background: #f7fafc;
  color: #1a202c;
}

.modal-body {
  padding: 0 !important;
  overflow-y: auto;
  flex: 1;
  display: flex;
  flex-direction: column;
  width: 100%;
}

.loading-state,
.error-state {
  text-align: center;
  padding: 3rem 1.5rem;
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

.vendor-type-banner {
  padding: 1rem;
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
  font-weight: 600;
}

.banner-onboarded-rfp {
  background: #d1fae5;
  color: #065f46;
}

.banner-onboarded-no-rfp {
  background: #dbeafe;
  color: #1e40af;
}

.banner-temp-rfp {
  background: #fef3c7;
  color: #92400e;
}

.banner-temp-no-rfp {
  background: #ede9fe;
  color: #5b21b6;
}

.tabs-container {
  margin-top: 0;
  background: #fff;
  border-bottom: 1px solid #e2e8f0;
  width: 100%;
}

.tabs-wrapper {
  padding: 0 1.5rem;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  width: 100%;
  display: flex !important;
  flex-direction: row !important;
  flex-wrap: nowrap !important;
  gap: 0;
  scrollbar-width: thin;
}

.tab {
  padding: 1rem 1.5rem;
  border: none;
  background: transparent;
  color: #718096;
  cursor: pointer;
  border-bottom: 3px solid transparent;
  margin-bottom: -1px;
  transition: all 0.2s;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  white-space: nowrap;
  position: relative;
  font-size: 0.875rem;
  flex-shrink: 0;
  flex-grow: 0;
}

.tab:hover {
  color: #2563eb;
  background: #f7fafc;
}

.tab.active {
  color: #2563eb;
  border-bottom-color: #2563eb;
  background: #f7fafc;
  font-weight: 600;
}

.tab.active::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  right: 0;
  height: 1px;
  background: #fff;
}

.tab-label {
  display: inline-block;
}

.tab i {
  font-size: 0.875rem;
}

.tab-content-wrapper {
  padding: 1.5rem;
  width: 100%;
  overflow-y: auto;
}

.tab-content {
  width: 100%;
}

.section-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1a202c;
  margin: 0 0 1.5rem 0;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid #e2e8f0;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.info-item.full-width {
  grid-column: 1 / -1;
}

.info-item label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #718096;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.info-item p {
  font-size: 1rem;
  color: #1a202c;
  margin: 0;
  word-break: break-word;
}

.link {
  color: #2563eb;
  text-decoration: none;
}

.link:hover {
  text-decoration: underline;
}

.badge {
  display: inline-block;
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

.text-danger {
  color: #dc2626;
  font-weight: 600;
}

.text-info {
  color: #2563eb;
  font-weight: 600;
}

.text-muted {
  color: #9ca3af;
}

.response-id {
  font-family: monospace;
  color: #2563eb;
  font-weight: 600;
}

/* Contacts */
.contacts-list {
  display: grid;
  gap: 1rem;
}

.contact-card {
  padding: 1rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  background: #f7fafc;
}

.contact-name {
  font-size: 1rem;
  font-weight: 600;
  color: #1a202c;
  margin: 0 0 0.75rem 0;
}

.contact-details {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.contact-detail {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: #4a5568;
}

.contact-detail i {
  width: 1.25rem;
  color: #718096;
}

.contact-detail a {
  color: #2563eb;
  text-decoration: none;
}

.contact-detail a:hover {
  text-decoration: underline;
}

/* Documents */
.documents-list {
  display: grid;
  gap: 1rem;
}

.document-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  background: #f7fafc;
}

.document-icon {
  font-size: 2rem;
  color: #2563eb;
}

.document-info {
  flex: 1;
}

.document-name {
  font-size: 1rem;
  font-weight: 600;
  color: #1a202c;
  margin: 0 0 0.25rem 0;
}

.document-type {
  font-size: 0.875rem;
  color: #718096;
  margin: 0;
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 3rem 1.5rem;
  color: #9ca3af;
}

.empty-state i {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.modal-footer {
  padding: 1.5rem;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: flex-end;
}

.btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 0.375rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: #2563eb;
  color: #fff;
}

.btn-primary:hover {
  background: #1d4ed8;
}

.btn-secondary {
  background: #f3f4f6;
  color: #374151;
}

.btn-secondary:hover {
  background: #e5e7eb;
}

/* Responsive - Mobile */
@media (max-width: 768px) {
  .tabs-wrapper {
    padding: 0 1rem;
  }

  .tab {
    padding: 0.75rem 1rem;
    font-size: 0.8125rem;
  }

  .tab-label {
    display: none;
  }

  .tab i {
    font-size: 1rem;
  }

  .tab-content-wrapper {
    padding: 1rem;
  }

  .info-grid {
    grid-template-columns: 1fr;
  }
}
</style>
