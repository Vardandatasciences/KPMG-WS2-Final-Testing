<template>
  <div class="baseline-config-container">
    <div class="baseline-header">
      <h2>Baseline Configuration</h2>
      <div class="baseline-framework-selector">
        <label>Framework:</label>
        <select v-model="selectedFrameworkId" @change="loadBaselineConfigurations">
          <option value="">Select Framework</option>
          <option v-for="fw in frameworks" :key="fw.id" :value="fw.id">
            {{ fw.name }}
          </option>
        </select>
      </div>
    </div>

    <div v-if="selectedFrameworkId" class="baseline-content">
      <!-- Filters -->
      <div v-if="!loading && compliances.length > 0" class="filters-section">
        <div class="filter-group">
          <label>Filter by Baseline Level:</label>
          <select v-model="selectedBaselineLevelFilter" class="filter-select">
            <option value="">All Levels</option>
            <option value="Low">Low</option>
            <option value="Moderate">Moderate</option>
            <option value="High">High</option>
          </select>
        </div>
        <div class="filter-group">
          <label>Filter by Importance:</label>
          <select v-model="selectedImportanceFilter" class="filter-select">
            <option value="">All Importance</option>
            <option value="Mandatory">Mandatory</option>
            <option value="Optional">Optional</option>
            <option value="Ignored">Ignored</option>
          </select>
        </div>
        <div class="filter-group">
          <label>Filter by Active Status:</label>
          <select v-model="selectedActiveFilter" class="filter-select">
            <option value="">All Status</option>
            <option value="true">Active</option>
            <option value="false">Inactive</option>
          </select>
        </div>
        <div class="filter-results-count">
          <span class="results-text">
            Showing <strong>{{ filteredCompliances.length }}</strong> of <strong>{{ compliances.length }}</strong> results
          </span>
        </div>
        <button @click="clearFilters" class="clear-filters-btn">Clear Filters</button>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="loading-state">
        <i class="fas fa-circle-notch fa-spin"></i>
        <span>Loading baseline configuration...</span>
      </div>

      <!-- Compliance Settings Table -->
      <div v-else-if="filteredCompliances.length > 0" class="compliance-settings-section">
        <div class="compliance-settings-table-wrapper">
          <table class="compliance-settings-table">
            <thead>
              <tr>
                <th>Compliance ID</th>
                <th>Title</th>
                <th>Baseline Level</th>
                <th>Version</th>
                <th>Importance</th>
                <th>Active</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="compliance in filteredCompliances" :key="compliance.baselineId">
                <td>{{ compliance.id }}</td>
                <td>{{ compliance.title }}</td>
                <td>{{ compliance.baselineLevel }}</td>
                <td>{{ compliance.version }}</td>
                <td>
                  <span :class="['status-badge', {
                    'status-mandatory': compliance.isMandatory,
                    'status-optional': compliance.isOptional,
                    'status-ignored': compliance.isIgnored
                  }]">
                    {{ compliance.complianceStatus }}
                  </span>
                </td>
                <td>
                  <span v-if="compliance.isActive" class="active-badge">Active</span>
                  <span v-else class="inactive-badge">Inactive</span>
                </td>
                <td>
                  <button @click="editBaseline(compliance)" class="edit-btn">
                    <i class="fas fa-edit"></i> Edit
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- No Data State -->
      <div v-else-if="compliances.length === 0" class="no-data-state">
        <i class="fas fa-inbox"></i>
        <p>No baseline configurations found for this framework.</p>
      </div>

      <!-- No Filtered Results State -->
      <div v-else-if="filteredCompliances.length === 0 && compliances.length > 0" class="no-data-state">
        <i class="fas fa-filter"></i>
        <p>No baseline configurations match the selected filters.</p>
        <button @click="clearFilters" class="clear-filters-btn" style="margin-top: 16px;">Clear Filters</button>
      </div>
    </div>

    <!-- Edit Modal -->
    <div v-if="showEditModal" class="modal-overlay" @click.self="closeEditModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>Edit Baseline Configuration</h3>
          <button class="modal-close-btn" @click="closeEditModal">
            <i class="fas fa-times"></i>
          </button>
        </div>
        
        <div class="modal-body">
          <div class="form-group">
            <label>Compliance ID:</label>
            <input type="text" v-model="editingBaseline.identifier" disabled class="form-input disabled" />
          </div>
          
          <div class="form-group">
            <label>Title:</label>
            <input type="text" v-model="editingBaseline.title" disabled class="form-input disabled" />
          </div>
          
          <div class="form-group">
            <label>Baseline Level:</label>
            <select v-model="editingBaseline.baselineLevel" class="form-input">
              <option value="Low">Low</option>
              <option value="Moderate">Moderate</option>
              <option value="High">High</option>
            </select>
          </div>
          
          <div class="form-group">
            <label>Version:</label>
            <input type="text" v-model="editingBaseline.version" disabled class="form-input disabled" />
            <small class="form-help-text">New version will be automatically created</small>
          </div>
          
          <div class="form-group">
            <label>Importance:</label>
            <select v-model="editingBaseline.complianceStatus" class="form-input">
              <option value="Mandatory">Mandatory</option>
              <option value="Optional">Optional</option>
              <option value="Ignored">Ignored</option>
            </select>
          </div>
          
          <div class="form-group">
            <label>Active Status:</label>
            <select v-model="editingBaseline.isActive" class="form-input">
              <option :value="true">Active</option>
              <option :value="false">Inactive</option>
            </select>
          </div>
        </div>
        
        <div class="modal-footer">
          <button class="btn-cancel" @click="closeEditModal">Cancel</button>
          <button class="btn-save-version" @click="saveAsNewVersion" :disabled="saving">
            <i class="fas fa-save"></i> {{ saving ? 'Saving...' : 'Save as New Version' }}
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { API_ENDPOINTS } from '../../config/api.js'
import { ElMessage } from 'element-plus'

export default {
  name: 'BaselineConfiguration',
  setup() {
    const frameworks = ref([])
    const selectedFrameworkId = ref(null)
    const compliances = ref([])
    const loading = ref(false)
    const selectedBaselineLevelFilter = ref('')
    const selectedImportanceFilter = ref('')
    const selectedActiveFilter = ref('')
    const showEditModal = ref(false)
    const editingBaseline = ref({
      baselineId: null,
      id: null,
      identifier: '',
      title: '',
      baselineLevel: '',
      version: '',
      complianceStatus: '',
      isActive: false
    })
    const saving = ref(false)

    onMounted(async () => {
      await loadFrameworks()
    })

    async function loadFrameworks() {
      try {
        const response = await axios.get(API_ENDPOINTS.COMPLIANCE_ALL_POLICIES_FRAMEWORKS)
        frameworks.value = response.data.map(fw => ({
          id: fw.FrameworkId || fw.id,
          name: fw.FrameworkName || fw.name
        }))
      } catch (error) {
        console.error('Error loading frameworks:', error)
        ElMessage.error('Failed to load frameworks')
      }
    }

    async function loadBaselineConfigurations() {
      if (!selectedFrameworkId.value) {
        compliances.value = []
        return
      }
      
      loading.value = true
      try {
        // Fetch flat list of all baseline rows for the selected framework
        const response = await axios.get(API_ENDPOINTS.BASELINE_CONFIGURATIONS(selectedFrameworkId.value) + '?flat=true')
        if (response.data.success) {
          const baselineData = response.data.data || []
          // Transform the data for display
          compliances.value = baselineData.map(setting => {
            // Support both new format (ComplianceStatus) and old format (IsMandatory/IsOptional/IsIgnored)
            let complianceStatus = setting.ComplianceStatus
            if (!complianceStatus) {
              if (setting.IsMandatory) complianceStatus = 'Mandatory'
              else if (setting.IsIgnored) complianceStatus = 'Ignored'
              else complianceStatus = 'Optional'
            }
            return {
              id: setting.ComplianceId,
              baselineId: setting.BaselineId,
              identifier: setting.ComplianceIdentifier || 'N/A',
              title: setting.ComplianceTitle || setting.ComplianceIdentifier || 'N/A',
              baselineLevel: setting.BaselineLevel,
              version: setting.Version,
              isActive: setting.IsActive,
              complianceStatus: complianceStatus,
              isMandatory: complianceStatus === 'Mandatory',
              isOptional: complianceStatus === 'Optional',
              isIgnored: complianceStatus === 'Ignored',
              createdDate: setting.CreatedDate,
              modifiedDate: setting.ModifiedDate
            }
          })
          // Also keep the grouped structure for backward compatibility
        } else {
            compliances.value = []
        }
      } catch (error) {
        console.error('Error loading baseline configurations:', error)
        ElMessage.error('Failed to load baseline configurations')
        compliances.value = []
      } finally {
        loading.value = false
      }
    }

    // Computed property for filtered compliances
    const filteredCompliances = computed(() => {
      let filtered = compliances.value

      // Filter by Baseline Level
      if (selectedBaselineLevelFilter.value) {
        filtered = filtered.filter(c => c.baselineLevel === selectedBaselineLevelFilter.value)
      }

      // Filter by Importance
      if (selectedImportanceFilter.value) {
        filtered = filtered.filter(c => c.complianceStatus === selectedImportanceFilter.value)
      }

      // Filter by Active Status
      if (selectedActiveFilter.value !== '') {
        const isActive = selectedActiveFilter.value === 'true'
        filtered = filtered.filter(c => c.isActive === isActive)
      }

      return filtered
    })

    function clearFilters() {
      selectedBaselineLevelFilter.value = ''
      selectedImportanceFilter.value = ''
      selectedActiveFilter.value = ''
    }

    function editBaseline(compliance) {
      // Copy the compliance data for editing
      editingBaseline.value = {
        baselineId: compliance.baselineId,
        id: compliance.id,
        identifier: compliance.identifier,
        title: compliance.title,
        baselineLevel: compliance.baselineLevel,
        version: compliance.version,
        complianceStatus: compliance.complianceStatus,
        isActive: compliance.isActive
      }
      showEditModal.value = true
    }

    function closeEditModal() {
      showEditModal.value = false
      editingBaseline.value = {
        baselineId: null,
        id: null,
        identifier: '',
        title: '',
        baselineLevel: '',
        version: '',
        complianceStatus: '',
        isActive: false
      }
    }

    async function saveAsNewVersion() {
      if (!editingBaseline.value.baselineId || !selectedFrameworkId.value) {
        ElMessage.error('Missing required information')
        return
      }
      
      saving.value = true
      try {
        // Call the API to create new version for only this single row
        const response = await axios.post(API_ENDPOINTS.CREATE_SINGLE_BASELINE_VERSION, {
          BaselineId: editingBaseline.value.baselineId,
          FrameworkId: selectedFrameworkId.value,
          BaselineLevel: editingBaseline.value.baselineLevel,
          ComplianceId: editingBaseline.value.id,
          ComplianceStatus: editingBaseline.value.complianceStatus,
          CurrentVersion: editingBaseline.value.version
        })

        if (response.data.success) {
          ElMessage.success(`Baseline version ${response.data.data?.Version || 'V2'} created successfully`)
          closeEditModal()
          // Reload the baseline configurations
          await loadBaselineConfigurations()
        } else {
          ElMessage.error(response.data.error || 'Failed to save as new version')
        }
      } catch (error) {
        console.error('Error saving as new version:', error)
        ElMessage.error(error.response?.data?.error || 'Failed to save as new version')
      } finally {
        saving.value = false
      }
    }

    return {
      frameworks,
      selectedFrameworkId,
      compliances,
      loading,
      selectedBaselineLevelFilter,
      selectedImportanceFilter,
      selectedActiveFilter,
      filteredCompliances,
      loadBaselineConfigurations,
      clearFilters,
      editBaseline,
      showEditModal,
      editingBaseline,
      saving,
      closeEditModal,
      saveAsNewVersion
    }
  }
}
</script>

<style scoped>
.baseline-config-container {
  padding: 24px;
  margin-left: 280px;
  width: calc(100% - 280px);
  max-width: calc(100vw - 280px);
  height: calc(100vh - 80px);
  max-height: calc(100vh - 80px);
  box-sizing: border-box;
  overflow-y: auto;
  overflow-x: hidden;
  background-color: #f8f9fa;
  position: relative;
  /* Custom scrollbar styling */
  scrollbar-width: thin;
  scrollbar-color: #cbd5e0 #f7fafc;
}

.baseline-config-container::-webkit-scrollbar {
  width: 8px;
}

.baseline-config-container::-webkit-scrollbar-track {
  background: #f7fafc;
  border-radius: 4px;
}

.baseline-config-container::-webkit-scrollbar-thumb {
  background: #cbd5e0;
  border-radius: 4px;
}

.baseline-config-container::-webkit-scrollbar-thumb:hover {
  background: #a0aec0;
}

.baseline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding-bottom: 15px;
  border-bottom: 2px solid #4f8cff;
  flex-wrap: wrap;
  gap: 15px;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
}

.baseline-header h2 {
  margin: 0;
  color: #344054;
  font-size: 1.8rem;
  font-weight: 700;
  word-wrap: break-word;
  overflow-wrap: break-word;
  flex: 1;
  min-width: 0;
}

.baseline-framework-selector {
  display: flex;
  align-items: center;
  gap: 10px;
}

.baseline-framework-selector label {
  font-weight: 500;
  color: #495057;
}

.baseline-framework-selector select {
  padding: 8px 12px;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  background-color: white;
  font-size: 14px;
  min-width: 0;
  max-width: 300px;
  width: 100%;
  color: #495057;
  box-sizing: border-box;
}

.baseline-content {
  background-color: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  overflow: hidden;
}

.compliance-settings-section {
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  overflow: hidden;
  position: relative;
}

.filters-section {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 24px;
  padding: 16px;
  background-color: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
  flex-wrap: wrap;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-group label {
  font-weight: 500;
  color: #495057;
  font-size: 14px;
  white-space: normal;
  word-wrap: break-word;
  min-width: 0;
  flex-shrink: 1;
}

.filter-select {
  padding: 8px 12px;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  background-color: white;
  font-size: 14px;
  min-width: 0;
  max-width: 180px;
  width: 100%;
  color: #495057;
  cursor: pointer;
  box-sizing: border-box;
}

.filter-select:focus {
  outline: none;
  border-color: #4f8cff;
  box-shadow: 0 0 0 3px rgba(79, 140, 255, 0.1);
}

.clear-filters-btn {
  padding: 8px 16px;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  background-color: white;
  color: #6c757d;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-left: auto;
}

.clear-filters-btn:hover {
  background-color: #f8f9fa;
  border-color: #adb5bd;
  color: #495057;
}

.filter-results-count {
  display: flex;
  align-items: center;
  margin-left: auto;
  margin-right: 12px;
  padding: 8px 16px;
  background-color: white;
  border-radius: 6px;
  border: 1px solid #dee2e6;
}

.results-text {
  font-size: 14px;
  color: #495057;
  white-space: normal;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.results-text strong {
  color: #4f8cff;
  font-weight: 600;
}


.compliance-settings-table-wrapper {
  margin-bottom: 24px;
  overflow-x: hidden !important;
  overflow-y: auto;
  max-height: calc(100vh - 450px);
  position: relative;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  /* Force no horizontal scroll */
  -webkit-overflow-scrolling: touch;
  /* Custom scrollbar styling */
  scrollbar-width: thin;
  scrollbar-color: #cbd5e0 #f7fafc;
}

.compliance-settings-table-wrapper::-webkit-scrollbar {
  width: 8px;
}

.compliance-settings-table-wrapper::-webkit-scrollbar-track {
  background: #f7fafc;
  border-radius: 4px;
}

.compliance-settings-table-wrapper::-webkit-scrollbar-thumb {
  background: #cbd5e0;
  border-radius: 4px;
}

.compliance-settings-table-wrapper::-webkit-scrollbar-thumb:hover {
  background: #a0aec0;
}

.compliance-settings-table {
  width: 100% !important;
  max-width: 100% !important;
  border-collapse: collapse;
  background-color: white;
  position: relative;
  table-layout: fixed;
  box-sizing: border-box;
  /* Force table to respect container width */
  min-width: 0;
}

.compliance-settings-table th {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  padding: 12px 8px;
  text-align: left;
  font-weight: 600;
  color: #495057;
  border-bottom: 2px solid #dee2e6;
  font-size: 0.9rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  position: sticky;
  top: 0;
  z-index: 10;
  word-wrap: break-word;
  overflow-wrap: break-word;
  word-break: break-word;
  white-space: normal;
  min-width: 0;
  max-width: 100%;
  overflow: hidden;
}

/* Set flexible column widths to prevent overflow */
.compliance-settings-table th:nth-child(1),
.compliance-settings-table td:nth-child(1) {
  width: 8%;
  min-width: 0;
  max-width: 10%;
}

.compliance-settings-table th:nth-child(2),
.compliance-settings-table td:nth-child(2) {
  width: auto;
  min-width: 0;
  max-width: 40%;
}

.compliance-settings-table th:nth-child(3),
.compliance-settings-table td:nth-child(3) {
  width: 12%;
  min-width: 0;
  max-width: 15%;
}

.compliance-settings-table th:nth-child(4),
.compliance-settings-table td:nth-child(4) {
  width: 8%;
  min-width: 0;
  max-width: 10%;
}

.compliance-settings-table th:nth-child(5),
.compliance-settings-table td:nth-child(5) {
  width: 12%;
  min-width: 0;
  max-width: 15%;
}

.compliance-settings-table th:nth-child(6),
.compliance-settings-table td:nth-child(6) {
  width: 10%;
  min-width: 0;
  max-width: 12%;
}

.compliance-settings-table th:nth-child(7),
.compliance-settings-table td:nth-child(7) {
  width: 10%;
  min-width: 0;
  max-width: 12%;
}

.compliance-settings-table td {
  padding: 12px 8px;
  border-bottom: 1px solid #f1f3f4;
  color: #495057;
  position: relative;
  vertical-align: middle;
  word-wrap: break-word;
  overflow-wrap: break-word;
  word-break: break-word;
  white-space: normal;
  min-width: 0;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
}

.compliance-settings-table tbody tr:hover {
  background-color: #f8f9ff;
}


.status-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 500;
  text-transform: capitalize;
  display: inline-block;
  max-width: 100%;
  word-wrap: break-word;
  overflow-wrap: break-word;
  white-space: normal;
  box-sizing: border-box;
}

.status-mandatory {
  background-color: #fee2e2;
  color: #dc2626;
}

.status-optional {
  background-color: #fef3c7;
  color: #d97706;
}

.status-ignored {
  background-color: #e5e7eb;
  color: #6b7280;
}

.active-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 500;
  background-color: #d1fae5;
  color: #065f46;
  display: inline-block;
  max-width: 100%;
  word-wrap: break-word;
  overflow-wrap: break-word;
  white-space: normal;
  box-sizing: border-box;
}

.inactive-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 500;
  background-color: #f3f4f6;
  color: #6b7280;
  display: inline-block;
  max-width: 100%;
  word-wrap: break-word;
  overflow-wrap: break-word;
  white-space: normal;
  box-sizing: border-box;
}

.edit-btn {
  padding: 6px 12px;
  border: 1px solid #4f8cff;
  border-radius: 6px;
  background-color: #4f8cff;
  color: white;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  position: static;
  z-index: auto;
  white-space: normal;
  word-wrap: break-word;
  max-width: 100%;
  box-sizing: border-box;
}

.edit-btn:hover {
  background-color: #3d7aff;
  border-color: #3d7aff;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(79, 140, 255, 0.2);
}

.edit-btn:active {
  transform: translateY(0);
  box-shadow: 0 1px 2px rgba(79, 140, 255, 0.2);
}

.edit-btn i {
  font-size: 0.8rem;
}

/* Ensure Action column stays properly contained */
.compliance-settings-table td:last-child {
  position: relative;
  overflow: visible;
  z-index: 1;
}

/* Override any global styles that might affect edit button positioning */
.compliance-settings-table .edit-btn {
  position: static !important;
  z-index: auto !important;
}


.loading-state, .no-data-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #6c757d;
  text-align: center;
}

.loading-state i {
  font-size: 2rem;
  color: #4f8cff;
  margin-bottom: 16px;
}

.no-data-state i {
  font-size: 3rem;
  color: #dee2e6;
  margin-bottom: 16px;
}

/* Edit Modal Styles */
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
}

.modal-content {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 25px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e9ecef;
}

.modal-header h3 {
  margin: 0;
  color: #344054;
  font-size: 1.5rem;
  font-weight: 600;
}

.modal-close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: #6c757d;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.modal-close-btn:hover {
  background-color: #f8f9fa;
  color: #495057;
}

.modal-body {
  padding: 24px;
  flex: 1;
  overflow-y: auto;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #495057;
  font-size: 14px;
}

.form-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  font-size: 14px;
  color: #495057;
  background-color: white;
  box-sizing: border-box;
}

.form-input:focus {
  outline: none;
  border-color: #4f8cff;
  box-shadow: 0 0 0 3px rgba(79, 140, 255, 0.1);
}

.form-input.disabled {
  background-color: #f8f9fa;
  color: #6c757d;
  cursor: not-allowed;
}

.form-input select {
  cursor: pointer;
}

.form-help-text {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: #6c757d;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px 24px;
  border-top: 1px solid #e9ecef;
}

.btn-cancel {
  padding: 10px 20px;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  background-color: white;
  color: #495057;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-cancel:hover {
  background-color: #f8f9fa;
  border-color: #adb5bd;
}

.btn-save-version {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  background-color: #4f8cff;
  color: white;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.btn-save-version:hover:not(:disabled) {
  background-color: #3d7aff;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(79, 140, 255, 0.2);
}

.btn-save-version:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-save-version:active:not(:disabled) {
  transform: translateY(0);
}

/* Responsive Design */
@media (max-width: 1024px) {
  .baseline-config-container {
    margin-left: 200px;
    width: calc(100% - 200px);
    max-width: calc(100vw - 200px);
  }
}

@media (max-width: 768px) {
  .baseline-config-container {
    margin-left: 0;
    width: 100%;
    max-width: 100vw;
    padding: 16px;
    height: calc(100vh - 60px);
    max-height: calc(100vh - 60px);
  }
  
  .baseline-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .filters-section {
    flex-direction: column;
    align-items: stretch;
  }
  
  .filter-group {
    width: 100%;
  }
  
  .filter-results-count {
    margin-left: 0;
    margin-right: 0;
    width: 100%;
  }
  
  .clear-filters-btn {
    margin-left: 0;
    width: 100%;
  }
  
  .compliance-settings-table-wrapper {
    max-height: calc(100vh - 500px);
  }
  
  .compliance-settings-table {
    table-layout: auto;
  }
  
  .compliance-settings-table th,
  .compliance-settings-table td {
    font-size: 0.85rem;
    padding: 8px;
  }
}

</style>

