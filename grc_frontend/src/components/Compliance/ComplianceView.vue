<!--
  Control Detail View
  This component displays detailed information about controls (compliances)
  when navigated to from the Control Management page.
-->

<template>
  <div class="compliance-view-container">
    <div class="compliance-header">
      <div class="compliance-header-left">
        <!-- Use global back-icon-btn styles from main.css -->
        <button @click="goBack" class="back-icon-btn" aria-label="Back">
          <i class="fas fa-arrow-left"></i>
        </button>
        <h2>{{ title }}</h2>
      </div>
      <div class="compliance-actions">
        <button class="compliance-export-btn" @click="exportData">
          <i class="fas fa-download"></i> Export
        </button>
      </div>
    </div>

    <div v-if="error" class="compliance-error">
      <p>{{ error }}</p>
      <button @click="retryLoading" class="compliance-retry-btn">Retry</button>
    </div>

    <div>
      <!-- Filter Section -->
      <div class="controls-filter-section">
        <div class="compliance-view-dropdowns-row">
          <div>
            <label class="dropdown-external-label">Status</label>
            <CustomDropdown
              :config="statusDropdownConfig"
              v-model="statusFilter"
              :showClearButton="true"
              @change="filterControls"
            />
          </div>
          <div>
            <label class="dropdown-external-label">Criticality</label>
            <CustomDropdown
              :config="criticalityDropdownConfig"
              v-model="criticalityFilter"
              :showClearButton="true"
              @change="filterControls"
            />
          </div>
          <div>
            <label class="dropdown-external-label">Maturity Level</label>
            <CustomDropdown
              :config="maturityDropdownConfig"
              v-model="maturityFilter"
              :showClearButton="true"
              @change="filterControls"
            />
          </div>
        </div>
      </div>

      <!-- Table View -->
      <DynamicTable
        :data="filteredControls"
        :columns="visibleColumns"
        uniqueKey="ComplianceId"
        :showPagination="true"
        :showActions="true"
        @open-column-chooser="handleOpenColumnChooser"
      >
        <template #actions="{ row }">
          <button class="action-btn view" @click="showControlDetails(row)">
            <i class="fas fa-eye"></i>
          </button>
        </template>
      </DynamicTable>

      <!-- Control Details Modal -->
      <div v-if="selectedControl" class="modal-overlay" @click="closeControlDetails">
        <div class="modal-content" @click.stop>
          <div class="modal-header">
            <h3>Control Details</h3>
            <button class="modal-close" @click="closeControlDetails">&times;</button>
          </div>
          <div class="modal-description">
            <label>Description:</label>
            <p>{{ selectedControl.ComplianceItemDescription }}</p>
          </div>
          <div class="modal-body">
            <div class="detail-section">
              <h4>Basic Information</h4>
              <div class="detail-grid">
                <div class="detail-item">
                  <label>Title:</label>
                  <span>{{ selectedControl.ComplianceTitle }}</span>
                </div>
                <div class="detail-item">
                  <label>ID:</label>
                  <span>{{ selectedControl.Identifier }}</span>
                </div>
                 <div class="detail-item">
                   <label>Status:</label>
                   <span>{{ selectedControl.Status }}</span>
                 </div>
                 <div class="detail-item">
                   <label>Criticality:</label>
                   <span>{{ selectedControl.Criticality }}</span>
                 </div>
              </div>
            </div>

            <div class="detail-section">
              <h4>Implementation Details</h4>
              <div class="detail-grid">
                <div class="detail-item">
                  <label>Type:</label>
                  <span>{{ selectedControl.MandatoryOptional }}</span>
                </div>
                <div class="detail-item">
                  <label>Implementation:</label>
                  <span>{{ selectedControl.ManualAutomatic }}</span>
                </div>
                <div class="detail-item">
                  <label>Maturity Level:</label>
                  <span>{{ selectedControl.MaturityLevel }}</span>
                </div>
              </div>
            </div>

            <div v-if="selectedControl.IsRisk" class="detail-section risk-section">
              <h4>Risk Information</h4>
              <div class="detail-grid">
                <div class="detail-item">
                  <label>Possible Damage:</label>
                  <p>{{ selectedControl.PossibleDamage }}</p>
                </div>
                <div class="detail-item">
                  <label>Mitigation:</label>
                  <p>{{ selectedControl.mitigation }}</p>
                </div>
              </div>
            </div>

            <div class="detail-section">
              <h4>Hierarchy</h4>
              <div class="detail-grid">
                <div class="detail-item">
                  <label>Framework:</label>
                  <span>{{ selectedControl.FrameworkName }}</span>
                </div>
                <div class="detail-item">
                  <label>Policy:</label>
                  <span>{{ selectedControl.PolicyName }}</span>
                </div>
                <div class="detail-item">
                  <label>SubPolicy:</label>
                  <span>{{ selectedControl.SubPolicyName }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Column Chooser Modal -->
    <div v-if="showColumnEditor" class="incident-column-editor-overlay" @click.self="toggleColumnEditor">
      <div class="incident-column-editor-modal">
        <div class="incident-column-editor-header">
          <h3>Choose Columns</h3>
          <button class="incident-column-editor-close" @click="toggleColumnEditor">&times;</button>
        </div>

        <div class="search-bar">
          <i class="fas fa-search search-bar__icon"></i>
          <input
            type="text"
            v-model="columnSearchQuery"
            placeholder="Search columns..."
            class="search-bar__input"
          />
        </div>

        <div class="incident-column-editor-actions">
          <button class="incident-column-select-btn" @click="selectAllColumns">Select All</button>
          <button class="incident-column-select-btn" @click="deselectAllColumns">Deselect All</button>
          <button class="incident-column-select-btn" @click="resetColumnSelection">Reset to Default</button>
        </div>

        <div class="incident-column-editor-list">
          <div
            v-for="column in filteredColumnDefinitions"
            :key="column.key"
            class="incident-column-editor-item"
            @click="toggleColumnVisibility(column.key)"
          >
            <input
              type="checkbox"
              :checked="isColumnVisible(column.key)"
              class="incident-column-editor-checkbox"
              @click.stop="toggleColumnVisibility(column.key)"
            />
            <label class="incident-column-editor-label">
              <span class="incident-column-editor-text">{{ column.label }}</span>
            </label>
          </div>
          <div v-if="filteredColumnDefinitions.length === 0" class="incident-column-editor-empty">
            <i class="fas fa-search"></i>
            <p>No columns found matching "{{ columnSearchQuery }}"</p>
          </div>
        </div>

        <div class="incident-column-editor-footer">
          <button class="incident-column-done-btn" @click="toggleColumnEditor">Done</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { complianceService } from '../../services/api';
// import Dynamicalsearch from '../Dynamicalsearch.vue'; // Unused import
import CustomDropdown from '../CustomDropdown.vue';
import DynamicTable from '../DynamicTable.vue';

const route = useRoute();
const router = useRouter();
const loading = ref(false);
const error = ref(null);
const compliances = ref([]);
const selectedControl = ref(null);

// Filter and Sort state
const searchQuery = ref('');
const statusFilter = ref('');
const criticalityFilter = ref('');
const maturityFilter = ref('');
const sortKey = ref('Identifier');
const sortOrder = ref('asc');

const title = computed(() => {
  const name = decodeURIComponent(route.params.name || '');
  const type = route.params.type.charAt(0).toUpperCase() + route.params.type.slice(1);
  return `Controls for ${type}: ${name}`;
});

// Dropdown configs
const statusDropdownConfig = {
  name: 'Status',
  label: 'Status',
  values: [
    { value: '', label: 'All Statuses' },
    { value: 'Under Review', label: 'Under Review' },
    { value: 'Approved', label: 'Approved' },
    { value: 'Rejected', label: 'Rejected' }
  ]
};
const criticalityDropdownConfig = {
  name: 'Criticality',
  label: 'Criticality',
  values: [
    { value: '', label: 'All Criticality' },
    { value: 'High', label: 'High' },
    { value: 'Medium', label: 'Medium' },
    { value: 'Low', label: 'Low' }
  ]
};
const maturityDropdownConfig = {
  name: 'MaturityLevel',
  label: 'Maturity Level',
  values: [
    { value: '', label: 'All Maturity Levels' },
    { value: 'Initial', label: 'Initial' },
    { value: 'Developing', label: 'Developing' },
    { value: 'Defined', label: 'Defined' },
    { value: 'Managed', label: 'Managed' },
    { value: 'Optimizing', label: 'Optimizing' }
  ]
};

// All available column definitions (includes all columns from backend)
const columnDefinitions = [
  { key: 'Identifier', label: 'ID', defaultVisible: true, sortable: true },
  { key: 'ComplianceTitle', label: 'Title', defaultVisible: true, sortable: true },
  { key: 'Annex', label: 'Annex', defaultVisible: true, sortable: true },
  { key: 'Status', label: 'Status', defaultVisible: true, sortable: true },
  { key: 'Criticality', label: 'Criticality', defaultVisible: true, sortable: true },
  { key: 'MaturityLevel', label: 'Maturity Level', defaultVisible: true, sortable: true },
  { key: 'MandatoryOptional', label: 'Type', defaultVisible: true, sortable: true },
  { key: 'ManualAutomatic', label: 'Implementation', defaultVisible: true, sortable: true },
  { key: 'CreatedByDate', label: 'Created Date', defaultVisible: true, sortable: true },
  { key: 'ComplianceId', label: 'Compliance ID', defaultVisible: false, sortable: true },
  { key: 'ComplianceItemDescription', label: 'Description', defaultVisible: false, sortable: false },
  { key: 'ComplianceType', label: 'Compliance Type', defaultVisible: false, sortable: true },
  { key: 'Scope', label: 'Scope', defaultVisible: false, sortable: false },
  { key: 'Objective', label: 'Objective', defaultVisible: false, sortable: false },
  { key: 'IsRisk', label: 'Is Risk', defaultVisible: false, sortable: true },
  { key: 'PossibleDamage', label: 'Possible Damage', defaultVisible: false, sortable: false },
  { key: 'Impact', label: 'Impact', defaultVisible: false, sortable: true },
  { key: 'Probability', label: 'Probability', defaultVisible: false, sortable: true },
  { key: 'ComplianceVersion', label: 'Version', defaultVisible: false, sortable: true },
  { key: 'CreatedByName', label: 'Created By', defaultVisible: false, sortable: true },
  { key: 'RiskType', label: 'Risk Type', defaultVisible: false, sortable: true },
  { key: 'RiskCategory', label: 'Risk Category', defaultVisible: false, sortable: true },
  { key: 'RiskBusinessImpact', label: 'Risk Business Impact', defaultVisible: false, sortable: true },
  { key: 'SubPolicyName', label: 'SubPolicy', defaultVisible: false, sortable: true },
  { key: 'PolicyName', label: 'Policy', defaultVisible: false, sortable: true },
  { key: 'FrameworkName', label: 'Framework', defaultVisible: false, sortable: true }
];

// Column chooser state
const showColumnEditor = ref(false);
const columnSearchQuery = ref('');
// Default visible columns - only those marked as defaultVisible: true
const defaultVisibleColumns = columnDefinitions.filter(col => col.defaultVisible).map(col => col.key);
const visibleColumnKeys = ref([...defaultVisibleColumns]);

// Filtered columns based on search query
const filteredColumnDefinitions = computed(() => {
  if (!columnSearchQuery.value) {
    return columnDefinitions;
  }
  const query = columnSearchQuery.value.toLowerCase();
  return columnDefinitions.filter(col =>
    col.label.toLowerCase().includes(query) ||
    col.key.toLowerCase().includes(query)
  );
});

// Visible columns based on selection - build tableColumns from columnDefinitions
const visibleColumns = computed(() => {
  return columnDefinitions
    .filter(col => visibleColumnKeys.value.includes(col.key))
    .map(col => ({
      key: col.key,
      label: col.label,
      sortable: col.sortable || false
    }));
});

// Sorting and Filtering
const filteredControls = computed(() => {
  let result = [...compliances.value];

  // Apply search filter
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase();
    result = result.filter(control => 
    (control.ComplianceTitle?.toLowerCase().includes(query) ||
      control.ComplianceItemDescription?.toLowerCase().includes(query) ||
      control.Identifier?.toLowerCase().includes(query) ||
      control.Annex?.toLowerCase().includes(query))
 
    );
  }

  // Apply status filter
  if (statusFilter.value) {
    result = result.filter(control => control.Status === statusFilter.value);
  }

  // Apply criticality filter
  if (criticalityFilter.value) {
    result = result.filter(control => control.Criticality === criticalityFilter.value);
  }

  // Apply maturity filter
  if (maturityFilter.value) {
    result = result.filter(control => control.MaturityLevel === maturityFilter.value);
  }

  // Apply sorting
  result.sort((a, b) => {
    let aVal = a[sortKey.value] || '';
    let bVal = b[sortKey.value] || '';
    if (sortKey.value === 'CreatedByDate') {
      aVal = new Date(aVal);
      bVal = new Date(bVal);
    } else {
      aVal = typeof aVal === 'string' ? aVal.toLowerCase() : aVal;
      bVal = typeof bVal === 'string' ? bVal.toLowerCase() : bVal;
    }
    if (aVal < bVal) return sortOrder.value === 'asc' ? -1 : 1;
    if (aVal > bVal) return sortOrder.value === 'asc' ? 1 : -1;
    return 0;
  });
  return result;
});

const filterControls = () => {
  // The filtering is handled by the computed property
};

const showControlDetails = (control) => {
  selectedControl.value = control;
};

const closeControlDetails = () => {
  selectedControl.value = null;
};

const retryLoading = () => {
  fetchCompliances();
};

const goBack = () => {
  router.back();
};

const exportData = () => {
  // TODO: Implement export functionality
  console.log('Export functionality to be implemented');
};

const fetchCompliances = async () => {
  try {
    loading.value = true;
    error.value = null;
    const response = await complianceService.getCompliancesByType(
      route.params.type,
      route.params.id
    );
    if (response.data.success) {
      compliances.value = response.data.compliances.map(compliance => ({
        ...compliance,
        CreatedByDate: compliance.CreatedByDate ? new Date(compliance.CreatedByDate).toLocaleDateString() : 'N/A',
        category: compliance.Criticality || 'Not Specified',
        name: compliance.ComplianceTitle || compliance.ComplianceItemDescription,
        description: compliance.ComplianceItemDescription,
        title: compliance.ComplianceTitle,
        maturityLevel: compliance.MaturityLevel || 'Not Specified',
        version: compliance.ComplianceVersion,
        mandatoryOptional: compliance.MandatoryOptional || 'Not Specified',
        manualAutomatic: compliance.ManualAutomatic || 'Not Specified'
      }));
    } else {
      error.value = response.data.message || 'Failed to load controls';
    }
  } catch (err) {
    error.value = err.response?.data?.message || 'Failed to load controls. Please try again.';
  } finally {
    loading.value = false;
  }
};

// Column chooser functions
const handleOpenColumnChooser = () => {
  console.log('🔍 handleOpenColumnChooser called - event received from DynamicTable');
  toggleColumnEditor();
};

const toggleColumnEditor = () => {
  console.log('🔍 toggleColumnEditor called, current state:', showColumnEditor.value);
  showColumnEditor.value = !showColumnEditor.value;
  console.log('✅ showColumnEditor set to:', showColumnEditor.value);
  if (!showColumnEditor.value) {
    columnSearchQuery.value = '';
  }
};

const toggleColumnVisibility = (columnKey) => {
  const index = visibleColumnKeys.value.indexOf(columnKey);
  if (index > -1) {
    visibleColumnKeys.value.splice(index, 1);
  } else {
    visibleColumnKeys.value.push(columnKey);
  }
};

const isColumnVisible = (columnKey) => {
  return visibleColumnKeys.value.includes(columnKey);
};

const selectAllColumns = () => {
  visibleColumnKeys.value = columnDefinitions.map(col => col.key);
};

const deselectAllColumns = () => {
  visibleColumnKeys.value = [];
};

const resetColumnSelection = () => {
  visibleColumnKeys.value = [...defaultVisibleColumns];
};

onMounted(() => {
  fetchCompliances();
});
</script>

<style>
@import '@/assets/css/main.css';
@import '@/assets/css/dropdown.css';
</style>

<style scoped>
/* Main Container */
.compliance-view-container {
  padding: 24px;
  margin-left: 250px;
  width: calc(100% - 280px);
  min-height: calc(100vh - 60px);
  box-sizing: border-box;
  background: transparent;
}

/* Header Section */
.compliance-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
  padding: 0 4px;
  background: none !important;
  background-color: transparent !important;
}

.compliance-header h2 {
  color: #1f2937;
  font-size: 1.45rem;
  font-weight: 700;
  margin: 0;
  background: none !important;
  background-color: transparent !important;
}

.compliance-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.compliance-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-left: -20px;
}

.compliance-export-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.compliance-export-btn {
  background-color: #3b82f6;
  color: white;
}

.compliance-export-btn:hover {
  background-color: #2563eb;
  transform: translateY(-1px);
}

.compliance-back-btn {
  background-color: #6b7280;
  color: white;
}

.compliance-back-btn:hover {
  background-color: #4b5563;
  transform: translateY(-1px);
}

/* Loading and Error States */
.compliance-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
}

.compliance-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #e5e7eb;
  border-top: 3px solid #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.compliance-error {
  text-align: center;
  padding: 40px 20px;
}

.compliance-retry-btn {
  background-color: #dc2626;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  margin-top: 16px;
}

/* Filter Section */
.controls-filter-section {
  margin-bottom: 16px;
}

/* Dropdowns Row - Scoped to ComplianceView page */
.compliance-view-dropdowns-row {
  display: flex;
  gap: 94px;
  flex-wrap: wrap;
}

.compliance-view-dropdowns-row > div {
  display: flex;
  flex-direction: column;
  flex: 1 1 auto;
  min-width: 200px;
  max-width: 250px;
}

.compliance-view-dropdowns-row .dropdown {
  max-width: 100%;
  width: 100%;
}



/* Ensure table and its elements stay below dropdown */
.controls-table,
.dynamic-table,
.dynamic-table td,
.dynamic-table th,
.dynamic-table tr,
.action-btn,
.action-btn i {
  position: relative;
  z-index: 1 !important;
}

:deep(.dynamic-table tbody tr td) {
  background: #ffffff !important;
}

/* Table Container */
.controls-table {
  width: 100%;
  border-collapse: collapse;
}

.controls-table th,
.controls-table td {
  padding: 16px 20px;
  text-align: left;
  border-bottom: 1px solid #f3f4f6;
}

.controls-table th {
  font-weight: 600;
  color: #374151;
  cursor: pointer;
  user-select: none;
  font-size: 14px;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.controls-table th.active {
  color: #3b82f6;
}

.controls-table th:hover {
  background: transparent;
}

.controls-table th i {
  margin-left: 6px;
  font-size: 12px;
}

.controls-table tbody tr {
  transition: background-color 0.2s ease;
}

.controls-table tbody tr:hover {
  background: transparent;
}

.control-title {
  color: #3b82f6;
  cursor: pointer;
  font-weight: 500;
}

.control-title:hover {
  text-decoration: underline;
  color: #2563eb;
}

/* Badge Styles */
.status-badge,
.criticality-badge {
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
  display: inline-block;
}

/* Status badges */
.status-review { 
  background-color: #fef3c7; 
  color: #92400e; 
  border: 1px solid #f59e0b;
}
.status-approved { 
  background-color: #dcfce7; 
  color: #166534; 
  border: 1px solid #22c55e;
}
.status-rejected { 
  background-color: #fee2e2; 
  color: #991b1b; 
  border: 1px solid #ef4444;
}
.status-default { 
  background-color: #f3f4f6; 
  color: #4b5563; 
  border: 1px solid #9ca3af;
}

/* Criticality badges */
.criticality-high { 
  background-color: #fee2e2; 
  color: #991b1b; 
  border: 1px solid #ef4444;
}
.criticality-medium { 
  background-color: #fef3c7; 
  color: #92400e; 
  border: 1px solid #f59e0b;
}
.criticality-low { 
  background-color: #dcfce7; 
  color: #166534; 
  border: 1px solid #22c55e;
}

/* Action Buttons */
.action-column {
  white-space: nowrap;
}

.compliance-view-container .action-btn,
.dynamic-table .action-btn {
  padding: 0 !important;
  border: none !important;
  background: none !important;
  background-color: transparent !important;
  border-radius: 0 !important;
  cursor: pointer;
  margin-right: 8px;
  margin-left: -10px;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-shadow: none !important;
}

.compliance-view-container .action-btn.view,
.dynamic-table .action-btn.view {
  color: #000000 !important;
  background: transparent !important;
  background-color: transparent !important;
  box-shadow: none !important;
}

.compliance-view-container .action-btn.view:hover,
.dynamic-table .action-btn.view:hover {
  color: #3b82f6 !important;
  background: transparent !important;
  background-color: transparent !important;
  transform: scale(1.2);
  box-shadow: none !important;
}

.compliance-view-container .action-btn.view:active,
.dynamic-table .action-btn.view:active {
  background: transparent !important;
  background-color: transparent !important;
  transform: scale(1.1);
  box-shadow: none !important;
}

.compliance-view-container .action-btn.view i,
.dynamic-table .action-btn.view i {
  font-size: 18px !important;
  color: inherit !important;
  transition: all 0.2s ease;
}

.compliance-view-container .action-btn.view:hover i,
.dynamic-table .action-btn.view:hover i {
  transform: none !important;
  color: inherit !important;
}

.action-btn.risk {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(239, 68, 68, 0.3);
}

.action-btn.risk:hover {
  background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.4);
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  padding: 40px;
  backdrop-filter: blur(2px);
  animation: fadeIn 0.3s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.modal-content {
  background: white;
  border-radius: 12px;
  width: 70% !important;
  max-width: 1000px !important;
  min-width: 700px !important;
  max-height: 85vh;
  min-height: 400px;
  overflow: hidden;
  box-shadow: 0 20px 40px -8px rgba(0, 0, 0, 0.2), 0 0 0 1px rgba(255, 255, 255, 0.1);
  animation: slideIn 0.3s ease-out;
  border: 1px solid rgba(255, 255, 255, 0.2);
  margin: 30px !important;
  position: relative;
  z-index: 1001;
  box-sizing: border-box;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: none;
  background: transparent;
  background-color: transparent;
  border-radius: 12px 12px 0 0;
  position: sticky;
  top: 0;
  z-index: 10;
}

.modal-header h3 {
  margin: 0;
  color: #1f2937;
  font-size: 1.25rem;
  font-weight: 700;
  background: linear-gradient(135deg, #1f2937 0%, #374151 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.modal-close {
  background: rgba(107, 114, 128, 0.1);
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #6b7280;
  padding: 8px;
  border-radius: 8px;
  transition: all 0.2s ease;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 300;
}

.modal-close:hover {
  color: #374151;
  background: rgba(107, 114, 128, 0.2);
  transform: scale(1.1);
}

.modal-description {
  padding: 16px 20px;
  margin: 0 20px 20px 20px;
  background: #f8f9fa;
  background-color: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  gap: 12px;
}

.modal-description label {
  font-weight: 700;
  color: #4b5563;
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin: 0;
  width: 140px;
  flex-shrink: 0;
  text-align: left;
}

.modal-description p {
  font-size: 0.9rem;
  line-height: 1.5;
  color: #4b5563;
  margin: 0;
  padding: 0;
  background: none;
  border-radius: 0;
  flex: 1;
}

.modal-body {
  padding: 20px;
  flex: 1;
  overflow-y: auto;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  align-items: start;
}

:deep(.dynamic-table-container) {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 0 !important;
  margin: 0 !important;
}

:deep(.dynamic-table-container .table-wrapper) {
  margin-top: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
  border: none !important;
}

:deep(.dynamic-table-container .dynamic-table) {
  background: transparent !important;
  box-shadow: none !important;
  border: none !important;
}

.detail-section {
  margin-bottom: 0;
  padding: 20px;
  border-radius: 12px;
  background: white;
  border: 1px solid #e5e7eb;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  transition: all 0.2s ease;
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 300px;
  height: 300px;
}

.detail-section:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.detail-section h4 {
  margin: 0 0 16px 0;
  color: #1f2937;
  font-size: 1.25rem;
  font-weight: 700;
  padding-bottom: 12px;
  border-bottom: 2px solid #e5e7eb;
  flex-shrink: 0;
}

.detail-item {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 6px;
  padding: 12px;
  border-radius: 8px;
  transition: all 0.2s ease;
  min-height: 40px;
  justify-content: flex-start;
}

.detail-item label {
  font-weight: 700;
  color: #4b5563;
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0;
  width: 140px;
  flex-shrink: 0;
  text-align: left;
}

.detail-item span,
.detail-item p {
  color: #4b5563;
  font-weight: normal;
  line-height: 1.5;
  font-size: 0.8rem;
  flex: 1;
  margin: 0;
}

.detail-item span {
  font-weight: 600;
}

.risk-section {
  background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
  padding: 16px;
  border-radius: 10px;
  border-left: 4px solid #ef4444;
  box-shadow: 0 2px 8px rgba(239, 68, 68, 0.1);
}

.risk-section h4 {
  color: #991b1b;
  border-bottom-color: #fecaca;
}

.risk-section h4::after {
  background: linear-gradient(90deg, #ef4444 0%, #dc2626 100%);
}

.risk-section .detail-item {
  background: rgba(254, 242, 242, 0.8);
  border-left-color: #f87171;
}

.risk-section .detail-item:hover {
  background: rgba(254, 226, 226, 0.9);
}

/* Enhanced badge styles for modal */
.modal-content .status-badge,
.modal-content .criticality-badge {
  padding: 8px 14px;
  border-radius: 8px;
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  display: inline-block;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: all 0.2s ease;
}

.modal-content .status-badge:hover,
.modal-content .criticality-badge:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.18);
}

/* Scrollbar styling for modal */
.modal-content::-webkit-scrollbar {
  width: 8px;
}

.modal-content::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 4px;
}

.modal-content::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}

.modal-content::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

/* Responsive Design */
@media (max-width: 1024px) {
  .compliance-view-container {
    margin-left: 200px;
    width: calc(100% - 200px);
    padding: 16px;
  }
  
  
  .modal-content {
    max-width: 85vw !important;
    width: 80% !important;
    min-width: 700px !important;
    margin: 15px !important;
  }
  
  .modal-body {
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
  }
  
  .detail-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
  }
  
  .detail-item {
    padding: 16px;
    min-height: 80px;
  }
}

@media (max-width: 768px) {
  .compliance-view-container {
    margin-left: 0;
    width: 100%;
    padding: 12px;
  }
  
  .compliance-header {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }
  
  .compliance-header h2 {
    font-size: 1.5rem;
  }
  
  .dropdowns-row {
    flex-direction: column;
    gap: 16px;
  }
  
  .filter-dropdown {
    min-width: 100%;
    max-width: 100%;
  }
  
  .modal-content {
    margin: 15px !important;
    max-height: calc(100vh - 30px) !important;
    max-width: 85vw !important;
    width: 80% !important;
    min-width: 600px !important;
  }
  
  .modal-header,
  .modal-body {
    padding: 16px;
  }
  
  .modal-body {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .detail-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .detail-item {
    padding: 16px;
    min-height: 80px;
  }
  
  .controls-table th,
  .controls-table td {
    padding: 12px 16px;
  }
}

@media (max-width: 480px) {
  .compliance-view-container {
    padding: 8px;
  }
  
  .compliance-actions {
    flex-direction: column;
    width: 100%;
  }
  
  .compliance-export-btn,
  .compliance-back-btn {
    width: 100%;
    justify-content: center;
  }
  
  .modal-content {
    max-width: 80vw !important;
    width: 75% !important;
    min-width: 300px !important;
    margin: 15px !important;
    border-radius: 12px;
  }
  
  .modal-header {
    padding: 20px 24px;
  }
  
  .modal-header h3 {
    font-size: 1.5rem;
  }
  
  .modal-body {
    padding: 24px;
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .detail-section {
    padding: 20px;
    margin-bottom: 0;
  }
  
  .detail-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .detail-item {
    padding: 16px;
    min-height: auto;
  }
  
  .detail-item label {
    font-size: 0.8rem;
  }
  
  .detail-item span,
  .detail-item p {
    font-size: 0.95rem;
  }
}

/* Column Chooser Styles */
.incident-column-editor-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 10000;
  backdrop-filter: blur(4px);
}

.incident-column-editor-modal {
  background: var(--card-bg, white);
  border-radius: 12px;
  width: 90%;
  max-width: 550px;
  max-height: 85vh;
  min-height: 400px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  overflow: hidden;
}

.incident-column-editor-header {
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-color, #e5e7eb);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--header-bg, #f9fafb);
}

.incident-column-editor-header h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary, #1f2937);
  letter-spacing: 0.3px;
}

.incident-column-editor-close {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: var(--text-secondary, #6b7280);
  padding: 4px 8px;
  border-radius: 4px;
  transition: all 0.2s ease;
  line-height: 1;
}

.incident-column-editor-close:hover {
  background: var(--hover-bg, #f3f4f6);
  color: var(--text-primary, #1f2937);
}

.incident-column-editor-modal .search-bar {
  padding: 16px 24px;
  border-bottom: 1px solid var(--border-color, #e5e7eb);
  width: 100%;
  box-sizing: border-box;
}

.incident-column-editor-modal .search-bar__icon {
  left: calc(24px + 0.875rem) !important;
}

.incident-column-editor-modal .search-bar__input {
  width: 100%;
  box-sizing: border-box;
}

.incident-column-editor-actions {
  padding: 12px 24px;
  display: flex;
  gap: 12px;
  border-bottom: 1px solid var(--border-color, #e5e7eb);
  background: var(--secondary-bg, #f9fafb);
}

.incident-column-select-btn {
  padding: 6px 12px;
  border: 1px solid var(--border-color, #d1d5db);
  background: var(--btn-bg, white);
  color: var(--text-primary, #1f2937);
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.2s ease;
}

.incident-column-select-btn:hover {
  background: var(--hover-bg, #f3f4f6);
  border-color: var(--primary-color, #4f7cff);
}

.incident-column-editor-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px 24px;
  max-height: 450px;
  min-height: 200px;
}

.incident-column-editor-list::-webkit-scrollbar {
  width: 8px;
}

.incident-column-editor-list::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 4px;
}

.incident-column-editor-list::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}

.incident-column-editor-list::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

.incident-column-editor-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 8px;
  border-bottom: 1px solid var(--border-color, #f3f4f6);
  cursor: pointer;
  transition: background 0.2s ease;
}

.incident-column-editor-item:hover {
  background: var(--hover-bg, #f9fafb);
}

.incident-column-editor-item:last-child {
  border-bottom: none;
}

.incident-column-editor-label {
  display: flex;
  align-items: center;
  flex: 1;
  cursor: pointer;
  user-select: none;
}

.incident-column-editor-checkbox {
  width: 20px;
  height: 20px;
  cursor: pointer;
  accent-color: var(--primary-color, #4f7cff);
  flex-shrink: 0;
  margin-right: 0;
}

.incident-column-editor-text {
  font-size: 15px;
  color: var(--text-primary, #1f2937);
  font-weight: 500;
  line-height: 1.5;
  margin-left: 0;
}

.incident-column-editor-footer {
  padding: 16px 24px;
  border-top: 1px solid var(--border-color, #e5e7eb);
  display: flex;
  justify-content: flex-end;
  background: var(--footer-bg, #f9fafb);
}

.incident-column-done-btn {
  padding: 10px 24px;
  background: var(--primary-color, #4f7cff);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.2s ease;
  box-shadow: 0 2px 4px rgba(79, 124, 255, 0.2);
}

.incident-column-done-btn:hover {
  background: var(--primary-hover, #3b5bdb);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(79, 124, 255, 0.3);
}

.incident-column-editor-empty {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-secondary, #6b7280);
  font-size: 14px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.incident-column-editor-empty i {
  font-size: 32px;
  color: #cbd5e1;
  margin-bottom: 8px;
}

.incident-column-editor-empty p {
  margin: 0;
  font-size: 15px;
}
</style>