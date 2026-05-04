<template>
  <div class="incident-view-container">
    <!-- Breadcrumb Section for Selected Filters - Positioned at top -->
    <div v-if="selectedFramework && selectedFramework !== '' && getSelectedFrameworkName !== ''" class="filter-breadcrumbs">
      <div class="filter-breadcrumbs__item">
        <span class="filter-breadcrumbs__label">Framework:</span>
        <span class="filter-breadcrumbs__value">{{ getSelectedFrameworkName }}</span>
        <button class="filter-breadcrumbs__close" @click="clearFrameworkSelection" title="Clear Framework">
          <i class="fas fa-times"></i>
        </button>
      </div>
    </div>

    <div class="incident-view-header">
      <div>
        <h2 class="incident-view-title">Incident Management</h2>
        <p v-if="dataSourceMessage" class="data-source-message">{{ dataSourceMessage }}</p>
      </div>
      <div class="incident-header-actions">
        <!-- Export controls - use global styles from main.css (custom dropdown + button) -->
        <div class="export-controls">
          <div class="export-controls-inner">
            <div
              class="export-select-wrapper"
              @click.stop="isExportDropdownOpen = !isExportDropdownOpen"
            >
              <button
                type="button"
                class="export-select-trigger"
              >
                <span class="export-select-text">{{ exportFormatLabel }}</span>
                <i class="fas fa-chevron-down export-select-icon"></i>
              </button>
              <div
                v-if="isExportDropdownOpen"
                class="export-select-menu"
              >
                <div
                  v-for="opt in exportFormatOptions"
                  :key="opt.value || 'placeholder'"
                  class="export-select-option"
                  :class="{
                    'is-placeholder': opt.value === '',
                    'is-selected': opt.value === exportFormat
                  }"
                  @click.stop="selectExportFormatOption(opt)"
                >
                  <span
                    v-if="opt.value === exportFormat"
                    class="export-select-check"
                  >
                    <i class="fas fa-check"></i>
                  </span>
                  <span class="export-select-option-label">
                    {{ opt.label }}
                  </span>
                </div>
              </div>
            </div>
            <button
              class="export-btn"
              @click="exportIncidents"
              :disabled="isExporting || !exportFormat"
            >
              <i v-if="!isExporting" class="fas fa-download"></i>
              <i v-else class="fas fa-spinner fa-spin"></i>
              {{ isExporting ? 'Exporting...' : 'Export' }}
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <div class="incident-list-wrapper">
      <!-- Skeleton: first paint with no cached rows (cache-first / Pinia list store) -->
      <div
        v-if="showIncidentListSkeleton"
        class="grc-skeleton-dashboard incident-list-skeleton"
        aria-busy="true"
        aria-label="Loading incidents"
      >
        <div class="grc-skeleton-table-wrap">
          <div
            v-for="n in 10"
            :key="'sk-row-' + n"
            class="grc-skeleton-row grc-skeleton-pulse"
          />
        </div>
      </div>

      <!-- Search Section (no filter-controls container) -->
      <div v-else class="incident-search-section">
        <!-- <DynamicSearchBar
          v-model="searchQuery"
          placeholder="Search by ID, title, origin, priority, incident category, status, or date..."
          @input="filterIncidents"
          @search="performSearch"
        /> -->
        <!-- Filter Dropdowns -->
        <div class="incident-filter-container">
          <div class="incident-filter-row">
            <div class="incident-filter-item">
              <label class="dropdown-external-label">Framework</label>
              <CustomDropdown
                v-model="selectedFramework"
                :options="frameworkOptions"
                @change="onFrameworkChange"
                :config="{ label: 'All Frameworks' }"
                :showLabel="false"
              />
            </div>
            <!-- <div class="incident-filter-item">
              <label class="incident-filter-label">FILTER BY STATUS:</label>
              <select v-model="selectedStatus" @change="onStatusChange" class="incident-filter-select">
                <option value="">All Statuses</option>
                <option value="Open">Open</option>
                <option value="Assigned">Assigned</option>
                <option value="Approved">Approved</option>
                <option value="Rejected">Rejected</option>
                <option value="Scheduled">Scheduled</option>
                <option value="Under Review">Under Review</option>
                <option value="Pending Review">Pending Review</option>
                <option value="Closed">Closed</option>
                <option value="In Progress">In Progress</option>
              </select>
            </div> -->
            <!-- <div class="incident-filter-item">
              <label class="incident-filter-label">FILTER BY CATEGORY:</label>
              <select v-model="selectedBusinessCategory" @change="onBusinessCategoryChange" class="incident-filter-select">
                <option value="">All Categories</option>
                <option v-for="category in businessCategories" :key="category" :value="category">{{ category }}</option>
              </select>
            </div> -->
            <!-- <div class="incident-filter-item">
              <label class="incident-filter-label">FILTER BY BUSINESS UNIT:</label>
              <select v-model="selectedBusinessUnit" @change="onBusinessUnitChange" class="incident-filter-select">
                <option value="">All Business Units</option>
                <option v-for="businessUnit in businessUnits" :key="businessUnit" :value="businessUnit">{{ businessUnit }}</option>
              </select>
            </div> -->
          </div>
          
          <!-- Debug Filter Info (remove in production) -->
          <div v-if="false" class="incident-debug-info" style="background: #f0f0f0; padding: 10px; margin: 10px 0; border-radius: 4px; font-size: 12px;">
            <strong>Debug Info:</strong><br>
            Framework: {{ selectedFramework || 'None' }}<br>
            Policy: {{ selectedPolicy || 'None' }}<br>
            SubPolicy: {{ selectedSubPolicy || 'None' }}<br>
            Priority: {{ selectedPriority || 'None' }}<br>
            Frameworks loaded: {{ frameworks.length }}<br>
            Policies loaded: {{ policies.length }}<br>
            Subpolicies loaded: {{ subpolicies.length }}<br>
            Incidents loaded: {{ incidents.length }}
          </div>
        </div>
      </div>

      <!-- Dynamic Table (keep mounted; hide visually while loading to preserve pagination state) -->
      <DynamicTable
        v-show="!showIncidentListSkeleton"
        :data="filteredIncidents"
        :columns="visibleTableColumns"
        :unique-key="'IncidentId'"
        :show-pagination="true"
        :default-page-size="pageSize"
        :page-size-options="[10, 20, 50, 100]"
        :server-side-pagination="true"
        :sync-current-page="currentPage"
        :sync-page-size="pageSize"
        :total-count="totalIncidentsCount"
        @row-click="handleRowClick"
        @open-column-chooser="toggleColumnEditor"
        @page-change="handlePageChange"
        @page-size-change="handlePageSizeChange"
      >
        <!-- Custom Title Cell with Router Link -->
        <template #cell-IncidentTitle="{ row }">
          <router-link :to="`/incident/${row.IncidentId}`" class="incident-title-link">
            {{ row.IncidentTitle }}
          </router-link>
        </template>

        <!-- Custom Status Cell with Status Badge -->
        <template #cell-Status="{ row }">
          <span :class="getIncidentStatusClass(row.Status)">
            {{ getStatusDisplayText(row.Status) }}
          </span>
        </template>

        <!-- Custom Actions Cell -->
        <template #cell-Actions="{ row }">
          <div v-if="row.Status === 'Scheduled'" class="incident-action-text">
            Mitigated to Risk
          </div>
          <div v-else-if="row.Status === 'Rejected'" class="incident-action-text">
            {{ row.RejectionSource === 'RISK' ? 'Rejected from Risk' : 'Rejected as Incident' }}
          </div>
          <div v-else-if="row.Status === 'Assigned'" class="incident-action-text">
            Assigned
          </div>
          <div v-else-if="row.Status === 'Approved'" class="incident-action-text">
            Approved
          </div>
          <div v-else-if="row.Status === 'Active'" class="incident-action-text">
            Active
          </div>
          <div v-else-if="row.Status === 'Under Review' || row.Status === 'PENDING REVIEW'" class="incident-action-text">
            Pending Review
          </div>
          <div v-else-if="row.Status === 'Completed'" class="incident-action-text">
            Completed
          </div>
          <div v-else-if="row.Status === 'Closed'" class="incident-action-text">
            Closed
          </div>
          <div v-else-if="row.Status === 'Open' || !row.Status || row.Status.trim() === ''">
            <div class="incident-actions-container">
              <i class="fas fa-user-plus action-icon assign-icon" @click.stop="handleDropdownAction('assign', row)" title="Assign as Incident"></i>
              <i class="fas fa-arrow-up action-icon escalate-icon" @click.stop="handleDropdownAction('escalate', row)" title="Escalate to Risk"></i>
              <i class="fas fa-times action-icon close-icon" @click.stop="handleDropdownAction('close', row)" title="Close Incident"></i>
            </div>
          </div>
          <div v-else-if="row.Status && row.Status.trim() !== ''" class="incident-action-text">
            {{ row.Status }}
          </div>
        </template>
      </DynamicTable>

      <!-- Column Chooser Modal -->
      <transition name="modal-fade">
        <div v-if="showColumnEditor" class="incident-column-editor-overlay" @click.self="toggleColumnEditor">
          <div class="incident-column-editor-modal">
            <div class="incident-column-editor-header">
              <h3 class="incident-column-editor-title">Choose Columns</h3>
              <button type="button" class="incident-column-editor-close" @click="toggleColumnEditor">
                <i class="fas fa-times"></i>
              </button>
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
              <button type="button" class="incident-column-action-btn" @click="selectAllColumns">
                <i class="fas fa-check-double"></i> Select All
              </button>
              <button type="button" class="incident-column-action-btn" @click="deselectAllColumns">
                <i class="fas fa-times-circle"></i> Deselect All
              </button>
              <button type="button" class="incident-column-action-btn" @click="resetColumnSelection">
                <i class="fas fa-undo"></i> Reset to Default
              </button>
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
                  class="incident-column-checkbox"
                  @click.stop="toggleColumnVisibility(column.key)"
                />
                <label class="incident-column-label">{{ column.label }}</label>
              </div>
            </div>
            
            <div v-if="filteredColumnDefinitions.length === 0" class="incident-column-editor-empty">
              <i class="fas fa-search"></i>
              <p>No columns found matching "{{ columnSearchQuery }}"</p>
            </div>
            
            <div class="incident-column-editor-footer">
              <button type="button" class="incident-column-apply-btn" @click="toggleColumnEditor">
                <i class="fas fa-check"></i> Apply
              </button>
            </div>
          </div>
        </div>
      </transition>

      <!-- No Incidents Message -->
      <div v-if="!isLoadingIncidents && incidents.length === 0" class="incident-no-incidents-message">
        <div class="incident-no-data-container">
          <i class="fas fa-exclamation-triangle incident-no-data-icon"></i>
          <h3>No Incidents Found</h3>
          <p v-if="hasActiveFilters">
            No incidents match your current filters. Try adjusting your search criteria.
          </p>
          <p v-else>
            No incidents are available at the moment.
          </p>
        </div>
      </div>
    </div>
    
    <!-- Modal for Solve/Reject -->
    <div v-if="showModal && modalAction !== 'assign'" class="incident-modal-overlay" @click="closeModal">
      <div class="incident-modal-container" @click.stop>
        <button class="incident-modal-close-btn" @click="closeModal">✕</button>
        <div class="incident-modal-content">
          <div v-if="modalAction === 'solve'" class="incident-solve-container">
            <div class="incident-solve-icon">🔄</div>
            <h3 class="incident-modal-title incident-solve">Forwarded to Risk</h3>
            <p class="incident-modal-subtitle">You will be directed to the Risk module</p>
            <div class="incident-modal-footer">
              <button @click="confirmSolve" class="incident-modal-btn incident-confirm-btn">Confirm Forward</button>
              <button @click="closeModal" class="incident-modal-btn incident-cancel-btn">Cancel</button>
            </div>
          </div>
          
          <div v-else-if="modalAction === 'reject'" class="incident-rejected-container">
            <div class="incident-rejected-icon">✕</div>
            <h3 class="incident-modal-title incident-rejected">REJECTED</h3>
            <div class="incident-modal-footer">
              <button @click="confirmReject" class="incident-modal-btn incident-reject-btn btn-reject">Confirm Reject</button>
              <button @click="closeModal" class="incident-modal-btn incident-cancel-btn">Cancel</button>
            </div>
          </div>

          <div v-else-if="modalAction === 'close'" class="incident-rejected-container">
            <div class="incident-rejected-icon">✕</div>
            <h3 class="incident-modal-title incident-rejected">CLOSED</h3>
            <div class="incident-modal-footer">
              <button @click="confirmClose" class="incident-modal-btn incident-reject-btn btn-reject">Confirm Close</button>
              <button @click="closeModal" class="incident-modal-btn incident-cancel-btn">Cancel</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Assignment Workflow Section -->
    <div v-if="showAssignmentWorkflow" class="incident-assignment-workflow-section">
      <div class="incident-assignment-header">
        <button class="back-icon-btn" @click="closeAssignmentWorkflow" aria-label="Back to Incidents">
          <i class="fas fa-arrow-left"></i>
        </button>
        <span class="incident-back-label">Back to Incidents</span>
      </div>
      <div class="assignment-body">
        <div class="incident-summary">
          <h3>{{ selectedIncident.IncidentTitle || 'Incident #' + selectedIncident.IncidentId }}</h3>
          <div class="incident-details">
            <p><strong>ID:</strong> {{ selectedIncident.IncidentId }}</p>
            <p><strong>Category:</strong> {{ selectedIncident.RiskCategory }}</p>
            <p><strong>Priority:</strong> {{ selectedIncident.RiskPriority }}</p>
            <p><strong>Origin:</strong> {{ selectedIncident.Origin }}</p>
          </div>
        </div>

        <!-- User Selection -->
        <div class="incident-user-selection">
          <h3>Assignment Details</h3>
          <div class="incident-user-form">
              <div class="incident-form-group">
                <label for="assigner">Assigner:</label>
                <div class="incident-current-user-display">
                  <span class="current-user-name">{{ currentUserName || 'Loading...' }}</span>
                  
                </div>
              </div>
              
              <div class="incident-form-group">
                <label for="reviewer" class="dropdown-external-label">Reviewer:</label>
                <CustomDropdown
                  v-model="selectedReviewer"
                  :options="reviewerOptions"
                  placeholder="Select Reviewer"
                  :showLabel="false"
                  :showSearchBar="true"
                  :showClearButton="true"
                />
            </div>
          </div>
        </div>
        
        <!-- Mitigation Workflow -->
        <div class="incident-mitigation-workflow">
          <h3>Mitigation Steps</h3>
          <!-- Existing Mitigation Steps -->
          <div v-if="mitigationSteps.length" class="incident-workflow-timeline">
            <div v-for="(step, index) in mitigationSteps" :key="index" class="incident-workflow-step">
              <div class="incident-step-number">{{ index + 1 }}</div>
              <div class="incident-step-content">
                <textarea 
                  v-model="step.description" 
                  class="incident-mitigation-textarea"
                  placeholder="Enter mitigation step description"
                ></textarea>
                <div class="incident-step-actions">
                  <button @click="removeMitigationStep(index)" class="incident-remove-step-btn">
                    <i class="fas fa-trash"></i> Remove
                  </button>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="incident-no-mitigations">
            <p>No mitigation steps found for this incident. Add steps below.</p>
          </div>
          
          <!-- Add New Mitigation Step -->
          <div class="incident-add-mitigation">
            <textarea 
              v-model="newMitigationStep" 
              class="incident-mitigation-textarea"
              placeholder="Enter mitigation step(s). Use commas to separate multiple steps (e.g., 'Step 1, Step 2, Step 3')"
            ></textarea>
            <button @click="addMitigationStep" class="btn btn-add" :disabled="!canAddMitigationStep">
              <i class="fas fa-plus"></i> Add Mitigation Step
            </button>
          </div>
          
          <!-- Due Date Input -->
          <div class="incident-due-date-section">
            <h4>Due Date for Mitigation Completion</h4>
            <input 
              type="date" 
              v-model="mitigationDueDate" 
              class="incident-due-date-input" 
              :min="getTodayDate()"
            />
          </div>

          <!-- Assignment Notes -->
          <div class="incident-assignment-notes-section">
            <h4>Assignment Notes (Optional)</h4>
                <textarea 
                  v-model="assignmentNotes" 
              class="incident-assignment-notes-textarea"
                  placeholder="Add any specific instructions or notes for the assignees..."
                  rows="3"
                ></textarea>
            </div>
            
          <!-- Submit Section -->
          <div class="incident-assignment-actions">
              <button 
              @click="confirmAssignmentWorkflow" 
              class="btn btn-submit"
              :disabled="!selectedReviewer || mitigationSteps.length === 0 || !mitigationDueDate"
              >
              <i class="fas fa-user-plus"></i> Assign Incident with Mitigations
              </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { axiosCompat as axiosInstance } from '@/services/apiServiceCompat.js';
import apiService from '@/services/apiService.js';
import { API_ENDPOINTS } from '../../config/api.js';
import './Incident.css';
import { PopupService } from '@/modules/popup';
import { AccessUtils, SessionUtils } from '@/utils/accessUtils';
import { openDownloadInNewTabWithAnchorFallback } from '@/utils/safeExternalNavigation';
import { getExplicitFrameworkId } from '@/utils/frameworkContextStorage.js';
import { mapStores } from 'pinia'
import { useFrameworkStore } from '@/stores/framework'
import { useFrameworkGlobalCacheStore } from '@/stores/frameworkGlobalCache'
import { useIncidentStore } from '@/stores/incident'
// import DynamicSearchBar from '@/components/Dynamicalsearch.vue';
import DynamicTable from '@/components/DynamicTable.vue';
import CustomDropdown from '@/components/CustomDropdown.vue';

export default {
  name: 'IncidentManagement',
  components: {
    // DynamicSearchBar,
    DynamicTable,
    CustomDropdown
  },
  data() {
    return {
      incidents: [], // Always initialize as empty array
      allIncidents: [], // Full dataset for client-side pagination when cache is available
      searchQuery: '',
      sortField: '',
      sortOrder: 'asc',
      searchTimeout: null,
      isLoadingIncidents: false,
      lastFetchTime: null, // Cache timestamp
      cacheTimeout: 300000, // 5 minutes cache (increased to prevent timeouts)
      currentPage: 1,
      incidentsPerPage: 20,
      totalIncidents: 0,
      hasMoreData: false,
      showModal: false,
      modalAction: '', // 'solve', 'reject', or 'assign'
      selectedIncident: null,
      // Export controls (shared styles from main.css)
      exportFormat: '',
      exportFormatOptions: [
        { value: '', label: 'Select format' },
        { value: 'xlsx', label: 'Excel (.xlsx)' },
        { value: 'csv', label: 'CSV (.csv)' },
        { value: 'pdf', label: 'PDF (.pdf)' },
        { value: 'json', label: 'JSON (.json)' },
        { value: 'xml', label: 'XML (.xml)' },
        { value: 'txt', label: 'Text (.txt)' }
      ],
      isExportDropdownOpen: false,
      isExporting: false,
      // Assignment related data
      selectedAssigner: '',
      selectedReviewer: '',
      assignmentNotes: '',
      availableUsers: [],
      // Current user data
      currentUser: null,
      currentUserName: '',
      // Assignment workflow data
      showAssignmentWorkflow: false,
      mitigationSteps: [],
      newMitigationStep: '',
      mitigationDueDate: '',
      // Dropdown state
      dropdownOpenFor: null,
      frameworks: [],
      policies: [],
      subpolicies: [],
      priorities: ['Critical', 'High', 'Medium', 'Low'],
      businessUnits: [],
      businessCategories: [],
      selectedFramework: '',
      selectedPolicy: '',
      selectedSubPolicy: '',
      selectedPriority: '',
      selectedBusinessUnit: '',
      selectedBusinessCategory: '',
      selectedStatus: '',
      // Pagination state for server-side pagination
      pageSize: 20,
      totalIncidentsCount: 0,
      // Data source indicator (cache vs API), similar to Risk pages
      dataSourceMessage: '',
      // Measured duration of last incident list API fetch
      lastIncidentFetchMs: null,
      /** True while first-page list is loading in background (non-blocking bootstrap). */
      incidentsListFetchPending: false,
      // Keep Incident List independent from global framework auto-sync.
      // Users can still filter using this page's framework dropdown.
      syncFrameworkFromGlobal: false,
      // Column menu and filter data
      activeFilterColumn: null,
      activeFilterColumnLabel: '',
      columnFilterSearch: '',
      columnFilterTempSelection: [],
      columnFilterPosition: { top: '0px', left: '0px' },
      columnFilters: {},
      lastFilterTrigger: null,
      activeMenuColumn: null,
      activeMenuColumnLabel: '',
      columnMenuPosition: { top: '0px', left: '0px' },
      showPinSubmenu: false,
      columnPins: {},
      columnWidths: {},
      lastMenuTrigger: null,
      // Column chooser data
      showColumnEditor: false,
      columnSearchQuery: '',
      columnDefinitions: [
        { key: 'IncidentId', label: 'ID', defaultVisible: true },
        { key: 'IncidentTitle', label: 'Title', defaultVisible: true },
        { key: 'Description', label: 'Description', defaultVisible: false },
        { key: 'Origin', label: 'Origin', defaultVisible: true },
        { key: 'RiskPriority', label: 'Priority', defaultVisible: true },
        { key: 'IncidentCategory', label: 'Incident Category', defaultVisible: true },
        { key: 'RiskCategory', label: 'Risk Category', defaultVisible: false },
        { key: 'Criticality', label: 'Criticality', defaultVisible: false },
        { key: 'Date', label: 'Date', defaultVisible: true },
        { key: 'Time', label: 'Time', defaultVisible: false },
        { key: 'Status', label: 'Status', defaultVisible: true },
        { key: 'AffectedBusinessUnit', label: 'Business Unit', defaultVisible: true },
        { key: 'SystemsAssetsInvolved', label: 'Systems/Assets', defaultVisible: false },
        { key: 'GeographicLocation', label: 'Location', defaultVisible: false },
        { key: 'InitialImpactAssessment', label: 'Impact Assessment', defaultVisible: false },
        { key: 'InternalContacts', label: 'Internal Contacts', defaultVisible: false },
        { key: 'ExternalPartiesInvolved', label: 'External Parties', defaultVisible: false },
        { key: 'RegulatoryBodies', label: 'Regulatory Bodies', defaultVisible: false },
        { key: 'RelevantPoliciesProceduresViolated', label: 'Policies Violated', defaultVisible: false },
        { key: 'ControlFailures', label: 'Control Failures', defaultVisible: false },
        { key: 'LessonsLearned', label: 'Lessons Learned', defaultVisible: false },
        { key: 'IncidentClassification', label: 'Classification', defaultVisible: false },
        { key: 'PossibleDamage', label: 'Possible Damage', defaultVisible: false },
        { key: 'CostOfIncident', label: 'Cost', defaultVisible: false },
        { key: 'RepeatedNot', label: 'Repeated', defaultVisible: false },
        { key: 'ReopenedNot', label: 'Reopened', defaultVisible: false },
        { key: 'RejectionSource', label: 'Rejection Source', defaultVisible: false },
        { key: 'CreatedAt', label: 'Created At', defaultVisible: false },
        { key: 'IdentifiedAt', label: 'Identified At', defaultVisible: false },
        { key: 'AssignedDate', label: 'Assigned Date', defaultVisible: false },
        { key: 'MitigationDueDate', label: 'Mitigation Due', defaultVisible: false },
        { key: 'MitigationCompletedDate', label: 'Mitigation Completed', defaultVisible: false },
        { key: 'Comments', label: 'Comments', defaultVisible: false },
        { key: 'AssignmentNotes', label: 'Assignment Notes', defaultVisible: false },
        { key: 'Mitigation', label: 'Mitigation', defaultVisible: false },
        { key: 'Actions', label: 'Actions', defaultVisible: true }
      ],
      visibleColumnKeys: [],
      // DynamicTable columns configuration
      tableColumns: [],
      // Prevent duplicate network calls during initial page bootstrap
      isBootstrapping: false
    }
  },
  computed: {
    ...mapStores(useIncidentStore),
    /** Table-shaped skeleton only when loading and no rows yet (prefetched full list counts as data). */
    showIncidentListSkeleton() {
      const hasRows =
        (Array.isArray(this.filteredIncidents) && this.filteredIncidents.length > 0) ||
        (Array.isArray(this.allIncidents) && this.allIncidents.length > 0)
      const listLoading =
        this.isLoadingIncidents ||
        (this.incidentsListFetchPending === true && !hasRows)
      return listLoading && !hasRows
    },
    frameworkOptions() {
      return [
        { value: '', label: 'All Frameworks' },
        ...this.frameworks.map(fw => ({ value: fw.id, label: fw.name }))
      ];
    },
    reviewerOptions() {
      return (this.availableUsers || []).map(user => ({
        value: user.id,
        label: `${user.name || ''} (${user.role || ''})`.trim() || String(user.id)
      }));
    },
    // Get selected framework name for breadcrumb
    getSelectedFrameworkName() {
      if (!this.selectedFramework || this.selectedFramework === '') return '';
      const framework = this.frameworks.find(fw => fw.id && fw.id.toString() === this.selectedFramework.toString());
      return framework ? framework.name : '';
    },
    hasActiveFilters() {
      return this.selectedFramework || this.selectedPolicy || this.selectedSubPolicy || this.selectedPriority || this.selectedBusinessUnit || this.selectedBusinessCategory || this.searchQuery.trim();
    },
    canAddMitigationStep() {
      return String(this.newMitigationStep || '').trim().length > 0;
    },
    exportFormatLabel() {
      const match = this.exportFormatOptions.find(
        opt => opt.value === this.exportFormat
      );
      return match ? match.label : 'Select format';
    },
    filteredIncidents() {
      // With server-side pagination, filtering is done on the server
      // Just return the incidents as-is (they're already filtered by the API)
      return this.incidents || [];
    },
    visibleTableColumns() {
      // Filter columns based on visibility set in column chooser
      if (this.visibleColumnKeys.length === 0) {
        // If no selection made yet, show default visible columns
        const defaultKeys = this.columnDefinitions
          .filter(col => col.defaultVisible)
          .map(col => col.key);
        return this.tableColumns.filter(col => defaultKeys.includes(col.key));
      }
      return this.tableColumns.filter(col => this.visibleColumnKeys.includes(col.key));
    },
    filteredColumnDefinitions() {
      const search = this.columnSearchQuery.toLowerCase().trim();
      if (!search) {
        return this.columnDefinitions;
      }
      return this.columnDefinitions.filter(col =>
        col.label.toLowerCase().includes(search)
      );
    }
  },
  watch: {
    // Watch for framework changes from homepage/localStorage
    '$store.state.framework.selectedFrameworkId': {
      handler(newFrameworkId) {
        if (!this.syncFrameworkFromGlobal) return;
        console.log('🔄 Framework changed in Vuex store:', newFrameworkId);
        if (newFrameworkId && newFrameworkId !== 'all') {
          const frameworkId = parseInt(newFrameworkId);
          if (frameworkId !== this.selectedFramework) {
            console.log(`🔄 Framework changed from ${this.selectedFramework} to ${frameworkId} - refreshing incidents`);
            this.selectedFramework = frameworkId;
            this.currentPage = 1;
            if (Array.isArray(this.allIncidents) && this.allIncidents.length > 0) {
              this.applyClientSideFiltersAndPaging();
            } else {
              this.fetchIncidents(1, this.pageSize);
            }
          }
        } else if (!newFrameworkId || newFrameworkId === 'all') {
          if (this.selectedFramework !== '') {
            console.log('🔄 Framework cleared - showing all frameworks');
            this.selectedFramework = '';
            this.currentPage = 1;
            if (Array.isArray(this.allIncidents) && this.allIncidents.length > 0) {
              this.applyClientSideFiltersAndPaging();
            } else {
              this.fetchIncidents(1, this.pageSize);
            }
          }
        }
      },
      immediate: false
    },
    searchQuery: {
      handler() {
        // Debounce search - wait 500ms after user stops typing
        clearTimeout(this.searchTimeout);
        this.searchTimeout = setTimeout(() => {
          this.currentPage = 1;
          if (Array.isArray(this.allIncidents) && this.allIncidents.length > 0) {
            this.applyClientSideFiltersAndPaging();
          } else {
            this.fetchIncidents(1, this.pageSize);
          }
        }, 500);
      }
    },
    selectedStatus() {
      if (this.selectedStatus !== undefined) {
        this.currentPage = 1;
        if (Array.isArray(this.allIncidents) && this.allIncidents.length > 0) {
          this.applyClientSideFiltersAndPaging();
        } else {
          this.fetchIncidents(1, this.pageSize);
        }
      }
    },
    selectedBusinessUnit() {
      if (this.selectedBusinessUnit !== undefined) {
        this.currentPage = 1;
        if (Array.isArray(this.allIncidents) && this.allIncidents.length > 0) {
          this.applyClientSideFiltersAndPaging();
        } else {
          this.fetchIncidents(1, this.pageSize);
        }
      }
    },
    selectedBusinessCategory() {
      if (this.selectedBusinessCategory !== undefined) {
        this.currentPage = 1;
        if (Array.isArray(this.allIncidents) && this.allIncidents.length > 0) {
          this.applyClientSideFiltersAndPaging();
        } else {
          this.fetchIncidents(1, this.pageSize);
        }
      }
    }
  },
  async mounted() {
    console.log('🚀 [Incident.vue] Component mounted - fetching data IMMEDIATELY...');
    this.isBootstrapping = true;
    
    // Initialize table columns (non-blocking)
    this.initializeTableColumns();
    this.loadCurrentUser();
    
    // Fetch metadata in background so incident list isn't blocked.
    // Do NOT auto-apply global selected framework here; default to all incidents.
    this.fetchFrameworks().catch(() => {});
    // Start first-page list fetch early (dedupes with loadFromStoredData / peek + session restore).
    void this.incidentStore.primeIncidentListFirstPage({ pageSize: 20, background: true }).catch(() => {});
    
    // Prefer cached incidents from IncidentService (loaded on login/home)
    // This mirrors the risk pages behavior: use cache first, then fallback.
    try {
      const usedCache = await this.loadFromStoredData();
      const elapsed = usedCache
        ? '0.0'
        : ((Number(this.lastIncidentFetchMs) || 0) / 1000).toFixed(1);
      const count = this.totalIncidentsCount || (Array.isArray(this.incidents) ? this.incidents.length : 0);
      if (usedCache) {
        this.dataSourceMessage = `Loaded ${count} incidents from cache (Pinia) in ${elapsed}s`;
      } else if (count > 0) {
        this.dataSourceMessage = `Loaded ${count} incidents directly from API in ${elapsed}s`;
      } else {
        this.dataSourceMessage = '';
      }
    } catch (e) {
      console.warn('⚠️ [Incident.vue] loadFromStoredData failed completely:', e);
      this.dataSourceMessage = 'Failed to load incidents. Please try again.';
    } finally {
      this.isBootstrapping = false;
    }
    
    // Listen for storage events to detect framework changes from other tabs/pages
    window.addEventListener('storage', this.handleStorageChange);
    
    // Ensure the main document scrolls to see all checklist data
    document.documentElement.style.overflow = 'auto';
    document.body.style.overflow = 'auto';
    
    // Add resize event listener to handle responsive behavior
    window.addEventListener('resize', this.handleResize);
    
    // Add click event listener to close dropdowns when clicking outside
    document.addEventListener('click', this.closeAllDropdowns);
    
    // Initialize visible columns
    this.visibleColumnKeys = this.columnDefinitions
      .filter(col => col.defaultVisible)
      .map(col => col.key);
  },
  beforeUnmount() {
    // Clean up event listeners
    window.removeEventListener('resize', this.handleResize);
    document.removeEventListener('click', this.closeAllDropdowns);
    
    // Clean up column filter and menu event listeners
    document.removeEventListener('click', this.handleFilterDocumentClick, true);
    document.removeEventListener('keydown', this.handleFilterEscapePress);
    document.removeEventListener('click', this.handleMenuDocumentClick, true);
    document.removeEventListener('keydown', this.handleMenuEscapePress);
  },
  methods: {
      initializeTableColumns() {
        this.tableColumns = [
          {
            key: 'IncidentId',
            label: 'ID',
            sortable: true,
            width: '70px',
            resizable: true,
            defaultVisible: true
          },
          {
            key: 'IncidentTitle',
            label: 'Title',
            sortable: true,
            slot: true,
            width: '250px',
            resizable: true,
            defaultVisible: true
          },
          {
            key: 'Description',
            label: 'Description',
            sortable: true,
            width: '200px',
            resizable: true,
            defaultVisible: false
          },
          {
            key: 'Origin',
            label: 'Origin',
            sortable: true,
            width: '120px',
            resizable: true,
            defaultVisible: true
          },
          {
            key: 'RiskPriority',
            label: 'Priority',
            sortable: true,
            width: '120px',
            resizable: true,
            defaultVisible: true
          },
          {
            key: 'IncidentCategory',
            label: 'Incident Category',
            sortable: true,
            width: '180px',
            resizable: true,
            defaultVisible: true
          },
          {
            key: 'RiskCategory',
            label: 'Risk Category',
            sortable: true,
            width: '150px',
            resizable: true,
            defaultVisible: false
          },
          {
            key: 'Criticality',
            label: 'Criticality',
            sortable: true,
            width: '120px',
            resizable: true,
            defaultVisible: false
          },
          {
            key: 'Date',
            label: 'Date',
            sortable: true,
            width: '120px',
            resizable: true,
            defaultVisible: true
          },
          {
            key: 'Time',
            label: 'Time',
            sortable: true,
            width: '100px',
            resizable: true,
            defaultVisible: false
          },
          {
            key: 'Status',
            label: 'Status',
            sortable: true,
            slot: true,
            width: '150px',
            resizable: true,
            defaultVisible: true
          },
          {
            key: 'AffectedBusinessUnit',
            label: 'Business Unit',
            sortable: true,
            width: '180px',
            resizable: true,
            defaultVisible: true
          },
          {
            key: 'SystemsAssetsInvolved',
            label: 'Systems/Assets',
            sortable: true,
            width: '180px',
            resizable: true,
            defaultVisible: false
          },
          {
            key: 'GeographicLocation',
            label: 'Location',
            sortable: true,
            width: '150px',
            resizable: true,
            defaultVisible: false
          },
          {
            key: 'InitialImpactAssessment',
            label: 'Impact Assessment',
            sortable: true,
            width: '200px',
            resizable: true,
            defaultVisible: false
          },
          {
            key: 'InternalContacts',
            label: 'Internal Contacts',
            sortable: true,
            width: '180px',
            resizable: true,
            defaultVisible: false
          },
          {
            key: 'ExternalPartiesInvolved',
            label: 'External Parties',
            sortable: true,
            width: '180px',
            resizable: true,
            defaultVisible: false
          },
          {
            key: 'RegulatoryBodies',
            label: 'Regulatory Bodies',
            sortable: true,
            width: '180px',
            resizable: true,
            defaultVisible: false
          },
          {
            key: 'RelevantPoliciesProceduresViolated',
            label: 'Policies Violated',
            sortable: true,
            width: '200px',
            resizable: true,
            defaultVisible: false
          },
          {
            key: 'ControlFailures',
            label: 'Control Failures',
            sortable: true,
            width: '180px',
            resizable: true,
            defaultVisible: false
          },
          {
            key: 'LessonsLearned',
            label: 'Lessons Learned',
            sortable: true,
            width: '180px',
            resizable: true,
            defaultVisible: false
          },
          {
            key: 'IncidentClassification',
            label: 'Classification',
            sortable: true,
            width: '150px',
            resizable: true,
            defaultVisible: false
          },
          {
            key: 'PossibleDamage',
            label: 'Possible Damage',
            sortable: true,
            width: '180px',
            resizable: true,
            defaultVisible: false
          },
          {
            key: 'CostOfIncident',
            label: 'Cost',
            sortable: true,
            width: '120px',
            resizable: true,
            defaultVisible: false
          },
          {
            key: 'RepeatedNot',
            label: 'Repeated',
            sortable: true,
            width: '100px',
            resizable: true,
            defaultVisible: false
          },
          {
            key: 'ReopenedNot',
            label: 'Reopened',
            sortable: true,
            width: '100px',
            resizable: true,
            defaultVisible: false
          },
          {
            key: 'RejectionSource',
            label: 'Rejection Source',
            sortable: true,
            width: '150px',
            resizable: true,
            defaultVisible: false
          },
          {
            key: 'CreatedAt',
            label: 'Created At',
            sortable: true,
            width: '150px',
            resizable: true,
            defaultVisible: false
          },
          {
            key: 'IdentifiedAt',
            label: 'Identified At',
            sortable: true,
            width: '150px',
            resizable: true,
            defaultVisible: false
          },
          {
            key: 'AssignedDate',
            label: 'Assigned Date',
            sortable: true,
            width: '150px',
            resizable: true,
            defaultVisible: false
          },
          {
            key: 'MitigationDueDate',
            label: 'Mitigation Due',
            sortable: true,
            width: '150px',
            resizable: true,
            defaultVisible: false
          },
          {
            key: 'MitigationCompletedDate',
            label: 'Mitigation Completed',
            sortable: true,
            width: '180px',
            resizable: true,
            defaultVisible: false
          },
          {
            key: 'Comments',
            label: 'Comments',
            sortable: true,
            width: '200px',
            resizable: true,
            defaultVisible: false
          },
          {
            key: 'AssignmentNotes',
            label: 'Assignment Notes',
            sortable: true,
            width: '200px',
            resizable: true,
            defaultVisible: false
          },
          {
            key: 'Actions',
            label: 'Actions',
            sortable: true,
            slot: true,
            width: '180px',
            resizable: true,
            defaultVisible: true,
            filterOptions: [
              { value: 'Mitigated to Risk', label: 'Mitigated to Risk' },
              { value: 'Rejected from Risk', label: 'Rejected from Risk' },
              { value: 'Rejected as Incident', label: 'Rejected as Incident' },
              { value: 'Assigned', label: 'Assigned' },
              { value: 'Approved', label: 'Approved' },
              { value: 'Active', label: 'Active' },
              { value: 'Pending Review', label: 'Pending Review' },
              { value: 'Completed', label: 'Completed' },
              { value: 'Closed', label: 'Closed' },
              { value: 'Open', label: 'Open (with action icons)' }
            ]
          }
        ];
      },
      toggleColumnEditor() {
        this.showColumnEditor = !this.showColumnEditor;
        if (this.showColumnEditor) {
          // Initialize visible column keys if empty
          if (this.visibleColumnKeys.length === 0) {
            this.visibleColumnKeys = this.columnDefinitions
              .filter(col => col.defaultVisible)
              .map(col => col.key);
          }
        }
      },
      toggleColumnVisibility(columnKey) {
        const index = this.visibleColumnKeys.indexOf(columnKey);
        if (index > -1) {
          this.visibleColumnKeys.splice(index, 1);
        } else {
          this.visibleColumnKeys.push(columnKey);
        }
      },
      isColumnVisible(columnKey) {
        if (this.visibleColumnKeys.length === 0) {
          const col = this.columnDefinitions.find(c => c.key === columnKey);
          return col ? col.defaultVisible : false;
        }
        return this.visibleColumnKeys.includes(columnKey);
      },
      selectAllColumns() {
        this.visibleColumnKeys = this.columnDefinitions.map(col => col.key);
      },
      deselectAllColumns() {
        this.visibleColumnKeys = [];
      },
      resetColumnSelection() {
        this.visibleColumnKeys = this.columnDefinitions
          .filter(col => col.defaultVisible)
          .map(col => col.key);
        this.columnSearchQuery = '';
      },
      getActionText(row) {
        // Return the text that would be displayed in the Actions column
        if (row.Status === 'Scheduled') {
          return 'Mitigated to Risk';
        } else if (row.Status === 'Rejected') {
          return row.RejectionSource === 'RISK' ? 'Rejected from Risk' : 'Rejected as Incident';
        } else if (row.Status === 'Assigned') {
          return 'Assigned';
        } else if (row.Status === 'Approved') {
          return 'Approved';
        } else if (row.Status === 'Active') {
          return 'Active';
        } else if (row.Status === 'Under Review' || row.Status === 'PENDING REVIEW') {
          return 'Pending Review';
        } else if (row.Status === 'Completed') {
          return 'Completed';
        } else if (row.Status === 'Closed') {
          return 'Closed';
        } else if (row.Status === 'Open' || !row.Status || row.Status.trim() === '') {
          return 'Open';
        } else if (row.Status && row.Status.trim() !== '') {
          return row.Status;
        }
        return '';
      },
      handleRowClick(row) {
        // Optional: Handle row click if needed
        console.log('Row clicked:', row);
      },
      // Dropdown methods
      toggleActionDropdown(incidentId) {
        console.log('Toggle dropdown for incident:', incidentId);
        console.log('Current dropdownOpenFor:', this.dropdownOpenFor);
        
        if (this.dropdownOpenFor === incidentId) {
          this.dropdownOpenFor = null;
        } else {
          this.dropdownOpenFor = incidentId;
        }
        
        console.log('New dropdownOpenFor:', this.dropdownOpenFor);
      },
      closeAllDropdowns(event) {
        // Only close if clicking outside the dropdown
        if (event && event.target) {
          const isDropdownClick = event.target.closest('.action-dropdown-container');
          const isExportDropdownClick = event.target.closest('.export-select-wrapper');
          if (isDropdownClick) {
            return; // Don't close if clicking inside dropdown
          }
          if (isExportDropdownClick) {
            return; // Don't close if clicking inside export dropdown
          }
        }
        
        console.log('Closing all dropdowns');
        this.dropdownOpenFor = null;
        this.isExportDropdownOpen = false;
      },
      selectExportFormatOption(opt) {
        if (!opt || !opt.value) return;
        this.exportFormat = opt.value;
        this.isExportDropdownOpen = false;
      },
      handleDropdownAction(action, incident) {
        console.log('Dropdown action:', action, 'for incident:', incident.IncidentId);
        
        switch(action) {
          case 'assign':
            this.openAssignModal(incident);
            break;
          case 'escalate':
            PopupService.confirm(
              `Are you sure you want to escalate Incident #${incident.IncidentId} to Risk? This will forward the incident to the Risk module for further evaluation and mitigation.`,
              'Escalate to Risk',
              () => this.confirmSolve(incident)
            );
            break;
          case 'close':
            PopupService.confirm(
              `Are you sure you want to close Incident #${incident.IncidentId}? This action cannot be undone.`,
              'Close Incident',
              () => this.confirmClose(incident)
            );
            break;
        }
      },
      openSolveModal(incident) {
      this.selectedIncident = incident;
      this.modalAction = 'solve';
      this.showModal = true;
    },
    openRejectModal(incident) {
      this.selectedIncident = incident;
      this.modalAction = 'reject';
      this.showModal = true;
    },
    openAssignModal(incident) {
      this.selectedIncident = incident;
      this.showAssignmentWorkflow = true;
      // Reset assignment form
      this.selectedReviewer = '';
      this.assignmentNotes = '';
      this.newMitigationStep = '';
      this.mitigationDueDate = '';
      
      // Load existing mitigation steps from the incident's Mitigation field
      console.log('Selected incident:', incident);
      console.log('Incident Mitigation field:', incident.Mitigation);
      this.loadExistingMitigations(incident);
      
      // Lazy load users only when needed
      if (this.availableUsers.length === 0) {
        this.fetchUsers();
      }
    },
    openCloseModal(incident) {
      this.selectedIncident = incident;
      this.modalAction = 'close';
      this.showModal = true;
    },
    closeModal() {
      this.showModal = false;
      this.selectedIncident = null;
      // Reset assignment form data
      this.selectedReviewer = '';
      this.assignmentNotes = '';
    },
    closeAssignmentWorkflow() {
      this.showAssignmentWorkflow = false;
      this.selectedIncident = null;
      // Reset assignment form data
      this.selectedReviewer = '';
      this.assignmentNotes = '';
      this.mitigationSteps = [];
      this.newMitigationStep = '';
      this.mitigationDueDate = '';
    },
    addMitigationStep() {
      const mitigationInput = String(this.newMitigationStep || '').trim();
      if (!mitigationInput) return;
      
      // Support both comma-separated and newline-separated entries.
      const steps = mitigationInput.split(/[,\n]/).filter(step => step.trim());
      
      if (steps.length > 1) {
        // Multiple comma-separated steps
        steps.forEach(step => {
          this.mitigationSteps.push({
            description: step.trim(),
            status: 'Not Started'
          });
        });
      } else {
        // Single step
        this.mitigationSteps.push({
          description: mitigationInput,
          status: 'Not Started'
        });
      }
      
      this.newMitigationStep = '';
    },
    removeMitigationStep(index) {
      this.mitigationSteps.splice(index, 1);
    },
    getTodayDate() {
      const today = new Date();
      const year = today.getFullYear();
      const month = String(today.getMonth() + 1).padStart(2, '0');
      const day = String(today.getDate()).padStart(2, '0');
      return `${year}-${month}-${day}`;
    },
    loadExistingMitigations(incident) {
      // Initialize with empty array
      this.mitigationSteps = [];
      
      // Check if incident has existing mitigation data
      if (incident.Mitigation) {
        try {
          let mitigationData = incident.Mitigation;
          
          // If it's a string, try to parse it as JSON
          if (typeof mitigationData === 'string') {
            // Check if it's JSON format
            if (mitigationData.trim().startsWith('{') || mitigationData.trim().startsWith('[')) {
              try {
                mitigationData = JSON.parse(mitigationData);
              } catch (e) {
                // If JSON parsing fails, treat as plain text
                console.log('Mitigation data is not JSON, treating as plain text');
              }
            }
          }
          
          // Handle different mitigation data formats
          if (typeof mitigationData === 'string') {
            // Plain text - split by lines, commas, or use as single step
            let steps = [];
            
            // First try splitting by newlines
            const lineSteps = mitigationData.split('\n').filter(step => step.trim());
            
            if (lineSteps.length > 1) {
              // Multiple lines found, use line separation
              steps = lineSteps;
            } else {
              // Single line or no newlines, try splitting by commas
              const commaSteps = mitigationData.split(',').filter(step => step.trim());
              if (commaSteps.length > 1) {
                // Multiple comma-separated items found
                steps = commaSteps;
              } else {
                // Single step
                steps = [mitigationData];
              }
            }
            
            this.mitigationSteps = steps.map((step) => ({
              description: step.trim(),
              status: 'Not Started'
            }));
          } else if (Array.isArray(mitigationData)) {
            // Array format
            this.mitigationSteps = mitigationData.map(item => ({
              description: typeof item === 'string' ? item : (item.description || item.title || 'Mitigation step'),
              status: item.status || 'Not Started'
            }));
          } else if (typeof mitigationData === 'object') {
            // Object format (like {"1": "Step 1", "2": "Step 2"})
            this.mitigationSteps = Object.values(mitigationData).map(step => ({
              description: typeof step === 'string' ? step : (step.description || step.title || 'Mitigation step'),
              status: step.status || 'Not Started'
            }));
          }
          
          console.log('Loaded existing mitigation steps:', this.mitigationSteps);
        } catch (error) {
          console.error('Error parsing mitigation data:', error);
          // Fallback: treat as plain text
          this.mitigationSteps = [{
            description: incident.Mitigation,
            status: 'Not Started'
          }];
        }
      }
      
      // If no mitigation steps were loaded, start with empty array
      if (this.mitigationSteps.length === 0) {
        console.log('No existing mitigation steps found');
      }
    },
    confirmAssignmentWorkflow() {
      // Validate reviewer selection
      if (!this.selectedReviewer) {
        PopupService.warning('Please select a reviewer');
        return;
      }

      // Auto-set current user as assigner
      const currentUserId = this.currentUser?.user_id;
      if (!currentUserId) {
        PopupService.error('Unable to identify current user. Please refresh and try again.');
        return;
      }

      // Check if current user is trying to assign to themselves as reviewer
      if (currentUserId === this.selectedReviewer.toString()) {
        PopupService.warning('You cannot assign yourself as both assigner and reviewer');
        return;
      }

      if (this.mitigationSteps.length === 0) {
        PopupService.warning('Please add at least one mitigation step');
        return;
      }

      if (!this.mitigationDueDate) {
        PopupService.warning('Please select a due date');
        return;
      }

      // Safety check for selectedIncident
      if (!this.selectedIncident || !this.selectedIncident.IncidentId) {
        console.error('No incident selected for assignment');
        PopupService.error('No incident selected for assignment. Please try again.');
        return;
      }

      console.log('Assigning incident:', this.selectedIncident.IncidentId);

      // Safety check for availableUsers array
      if (!this.availableUsers || !Array.isArray(this.availableUsers)) {
        console.error('Available users not loaded');
        PopupService.error('User data not loaded. Please refresh the page and try again.');
        return;
      }

      // Find reviewer details - assigner is automatically the current user
      const reviewer = this.availableUsers.find(user => user.id === this.selectedReviewer);
      
      // Safety check for reviewer
      if (!reviewer) {
        console.error('Selected reviewer not found in available users');
        PopupService.error('Selected reviewer not found. Please try again.');
        return;
      }

      // Convert mitigations to the expected JSON format
      const mitigationsJson = {};
      this.mitigationSteps.forEach((step, index) => {
        mitigationsJson[index + 1] = step.description;
      });

      const assignIncidentId = this.selectedIncident.IncidentId
      const optimisticPatch = {
        Status: 'Assigned',
        AssignerId: currentUserId,
        ReviewerId: this.selectedReviewer,
        assigner_name: this.currentUserName,
        reviewer_name: reviewer.name,
      }
      const snapshot = this.applyOptimisticIncidentPatch(this.selectedIncident, optimisticPatch)

      // Optimistic UX: success + close workflow immediately; persist assignment in the background.
      PopupService.success('Incident assigned successfully with mitigation steps!');
      this.closeAssignmentWorkflow();

      const payload = {
        status: 'Assigned',
        assigner_id: currentUserId,
        assigner_name: this.currentUserName,
        reviewer_id: this.selectedReviewer,
        reviewer_name: reviewer.name,
        assignment_notes: this.assignmentNotes,
        assigned_date: new Date().toISOString(),
        mitigations: mitigationsJson,
        due_date: this.mitigationDueDate,
      }

      axiosInstance
        .put(API_ENDPOINTS.INCIDENT_ASSIGN(assignIncidentId), payload)
        .then((response) => {
          console.log('Incident assigned — API confirmed:', response.data);
          const ok = response.data == null || response.data.success !== false;
          if (!ok) {
            this.rollbackOptimisticIncident(assignIncidentId, snapshot);
            PopupService.error(
              response.data?.message || 'Assignment could not be saved. The list was reverted.'
            );
            return;
          }
          this.afterIncidentListMutationSoftRevalidate();
        })
        .catch((error) => {
          console.error('Error assigning incident (background):', error);
          this.rollbackOptimisticIncident(assignIncidentId, snapshot);
        if (!AccessUtils.handleApiError(error, 'assign incidents')) {
            PopupService.error(
              'Assignment could not be saved on the server. The incident row was reverted — please try again.'
            );
        }
      });
    },
    confirmSolve(incidentOrEvent) {
      const incident =
        incidentOrEvent && incidentOrEvent.IncidentId != null ? incidentOrEvent : this.selectedIncident
      if (!incident || incident.IncidentId == null) {
        console.warn('confirmSolve: missing incident')
        return
      }
      console.log('Escalating incident to risk:', incident.IncidentId);
      const snapshot = this.applyOptimisticIncidentPatch(incident, { Status: 'Scheduled' })
      
      axiosInstance.put(API_ENDPOINTS.INCIDENT_STATUS(incident.IncidentId), {
        status: 'Scheduled'
      })
      .then(response => {
        console.log('Incident escalated to risk - API response:', response.data);
        
        if (response.data.success) {
          PopupService.success(`Incident #${incident.IncidentId} has been successfully escalated to Risk Management for further evaluation and mitigation.`, 'Escalated to Risk');
          this.closeModal();
          this.afterIncidentListMutationSoftRevalidate();
        } else {
          this.rollbackOptimisticIncident(incident.IncidentId, snapshot);
          console.error('API returned unsuccessful response:', response.data);
          PopupService.error(response.data.message || 'Failed to escalate incident. Please try again.');
        }
      })
      .catch(error => {
        this.rollbackOptimisticIncident(incident.IncidentId, snapshot);
        console.error('Error updating incident status:', error);
        if (!AccessUtils.handleApiError(error, 'escalate incidents')) {
          PopupService.error('Failed to escalate incident. Please try again.');
        }
      });
    },
    confirmReject() {
      console.log('Rejecting incident:', this.selectedIncident.IncidentId);
      
      // Update incident status to "Rejected"
      axiosInstance.put(API_ENDPOINTS.INCIDENT_STATUS(this.selectedIncident.IncidentId), {
        status: 'Rejected',
        rejection_source: 'INCIDENT'
      })
      .then(response => {
        console.log('Incident rejected - API response:', response.data);
        
        // Check if the response indicates success
        if (response.data.success) {
          // Show success message
          PopupService.success(`Incident #${this.selectedIncident.IncidentId} rejected successfully!`, 'Incident Rejected');
          
          // Immediately update the local incident object for instant UI feedback
          if (this.incidents && Array.isArray(this.incidents)) {
            const localIncident = this.incidents.find(inc => inc.IncidentId === this.selectedIncident.IncidentId);
            if (localIncident) {
              localIncident.Status = 'Rejected';
              localIncident.RejectionSource = 'INCIDENT';
              console.log('Updated local incident status to Rejected');
            }
          }
          
          // Update filtered incidents as well
          if (this.filteredIncidents && Array.isArray(this.filteredIncidents)) {
            const filteredIncident = this.filteredIncidents.find(inc => inc.IncidentId === this.selectedIncident.IncidentId);
            if (filteredIncident) {
              filteredIncident.Status = 'Rejected';
              filteredIncident.RejectionSource = 'INCIDENT';
            }
          }
          
          // Close the modal immediately
          this.closeModal();
          
          this.afterIncidentListMutationSoftRevalidate();
        } else {
          // Handle unsuccessful response
          console.error('API returned unsuccessful response:', response.data);
          PopupService.error(response.data.message || 'Failed to reject incident. Please try again.');
        }
      })
      .catch(error => {
        console.error('Error updating incident status:', error);
        console.error('Error details:', error.response);
        console.error('Error message:', error.message);
        
        // Check if this is an access denied error first
        if (!AccessUtils.handleApiError(error, 'reject incidents')) {
          // Only show generic error if it's not an access denied error
          PopupService.error('Failed to reject incident. Please try again.');
        }
      });
    },
    confirmClose(incidentOrEvent) {
      const incident =
        incidentOrEvent && incidentOrEvent.IncidentId != null ? incidentOrEvent : this.selectedIncident
      if (!incident || incident.IncidentId == null) {
        console.warn('confirmClose: missing incident')
        return
      }
      console.log('Closing incident:', incident.IncidentId);
      const snapshot = this.applyOptimisticIncidentPatch(incident, { Status: 'Closed' })
      this.closeModal();

      axiosInstance.put(API_ENDPOINTS.INCIDENT_STATUS(incident.IncidentId), {
        status: 'Closed'
      })
      .then(response => {
        console.log('Incident closed - API response:', response.data);
        
        if (response.data.success) {
          PopupService.success(`Incident #${incident.IncidentId} closed successfully!`, 'Incident Closed');
          this.afterIncidentListMutationSoftRevalidate();
        } else {
          this.rollbackOptimisticIncident(incident.IncidentId, snapshot);
          console.error('API returned unsuccessful response:', response.data);
          PopupService.error(response.data.message || 'Failed to close incident. Please try again.');
        }
      })
      .catch(error => {
        this.rollbackOptimisticIncident(incident.IncidentId, snapshot);
        console.error('Error updating incident status:', error);
        if (!AccessUtils.handleApiError(error, 'close incidents')) {
          PopupService.error('Failed to close incident. Please try again.');
        }
      });
    },
    confirmAssign() {
      // Validate reviewer selection
      if (!this.selectedReviewer) {
        PopupService.warning('Please select a reviewer');
        return;
      }

      // Auto-set current user as assigner
      const currentUserId = this.currentUser?.user_id;
      if (!currentUserId) {
        PopupService.error('Unable to identify current user. Please refresh and try again.');
        return;
      }

      // Check if current user is trying to assign to themselves as reviewer
      if (currentUserId === this.selectedReviewer.toString()) {
        PopupService.warning('You cannot assign yourself as both assigner and reviewer');
        return;
      }

      // Find reviewer details - assigner is automatically the current user
      const reviewer = this.availableUsers.find(user => user.id === this.selectedReviewer);
      if (!reviewer) {
        PopupService.error('Selected reviewer not found. Please try again.');
        return;
      }

      if (!this.selectedIncident || !this.selectedIncident.IncidentId) {
        PopupService.error('No incident selected for assignment. Please try again.');
        return;
      }

      const assignId = this.selectedIncident.IncidentId
      const snapshot = this.applyOptimisticIncidentPatch(this.selectedIncident, {
        Status: 'Assigned',
        AssignerId: currentUserId,
        ReviewerId: this.selectedReviewer,
        assigner_name: this.currentUserName,
        reviewer_name: reviewer.name,
      })

      PopupService.success('Incident assigned successfully.');
      this.closeModal();

      const payload = {
        status: 'Assigned',
        assigner_id: currentUserId,
        assigner_name: this.currentUserName,
        reviewer_id: this.selectedReviewer,
        reviewer_name: reviewer.name,
        assignment_notes: this.assignmentNotes,
        assigned_date: new Date().toISOString(),
      }

      axiosInstance
        .put(API_ENDPOINTS.INCIDENT_ASSIGN(assignId), payload)
        .then((response) => {
          const ok = response.data == null || response.data.success !== false;
          if (!ok) {
            this.rollbackOptimisticIncident(assignId, snapshot);
            PopupService.error(
              response.data?.message || 'Assignment could not be saved. The list was reverted.'
            );
            return;
          }
          this.afterIncidentListMutationSoftRevalidate();
        })
        .catch((error) => {
          this.rollbackOptimisticIncident(assignId, snapshot);
          console.error('Error assigning incident (background):', error);
        if (!AccessUtils.handleApiError(error, 'assign incidents')) {
            PopupService.error(
              'Assignment could not be saved on the server. The incident row was reverted — please try again.'
            );
        }
      });
    },
    getRiskCategoryClass(category) {
      if (!category) return '';
      const categoryLower = category.toLowerCase();
      if (categoryLower.includes('security')) return 'category-security';
      if (categoryLower.includes('compliance')) return 'category-compliance';
      if (categoryLower.includes('operational')) return 'category-operational';
      if (categoryLower.includes('financial')) return 'category-financial';
      if (categoryLower.includes('strategic')) return 'category-strategic';
      return 'category-other';
    },
    getIncidentCategoryClass(category) {
      if (!category) return '';
      const categoryLower = category.toLowerCase();
      if (categoryLower.includes('security')) return 'incident-category-security';
      if (categoryLower.includes('compliance')) return 'incident-category-compliance';
      if (categoryLower.includes('operational')) return 'incident-category-operational';
      if (categoryLower.includes('financial')) return 'incident-category-financial';
      if (categoryLower.includes('strategic')) return 'incident-category-strategic';
      if (categoryLower.includes('data breach')) return 'incident-category-data-breach';
      if (categoryLower.includes('system failure')) return 'incident-category-system-failure';
      if (categoryLower.includes('human error')) return 'incident-category-human-error';
      if (categoryLower.includes('malware')) return 'incident-category-malware';
      if (categoryLower.includes('phishing')) return 'incident-category-phishing';
      return 'incident-category-other';
    },
    getIncidentStatusClass(status) {
      if (!status) return 'status-open';
      const statusLower = status.toLowerCase();
      if (statusLower === 'new') return 'status-new';
      if (statusLower === 'open' || statusLower === '') return 'status-open';
      if (statusLower === 'assigned') return 'status-assigned';
      if (statusLower === 'approved') return 'status-approved';
      if (statusLower === 'active') return 'status-active';
      if (statusLower === 'under review' || statusLower === 'pending review') return 'status-pending';
      if (statusLower === 'completed') return 'status-completed';
      if (statusLower === 'closed') return 'status-closed';
      if (statusLower === 'scheduled') return 'status-scheduled';
      if (statusLower === 'rejected') return 'status-rejected';
      return 'status-default';
    },
    getStatusDisplayText(status) {
      if (!status || status.trim() === '') return 'Open';
      const statusLower = status.toLowerCase();
      if (statusLower === 'under review' || statusLower === 'pending review') return 'Pending Review';
      return status.charAt(0).toUpperCase() + status.slice(1).toLowerCase();
    },
    getStatusClass(priority) {
      const priorityLower = priority?.toLowerCase() || '';
      if (priorityLower === 'high') return 'status-active';
      if (priorityLower === 'medium') return 'status-medium';
      if (priorityLower === 'low') return 'status-inactive';
      return 'status-default';
    },
    getOriginClass(origin) {
      const originType = origin?.toLowerCase() || '';
      if (originType.includes('manual')) return 'incident-origin-manual';
      if (originType.includes('audit')) return 'incident-origin-audit';
      if (originType.includes('siem')) return 'incident-origin-siem';
      return 'incident-origin-other';
    },
    
    // Load data from stored service (from login)
    // Returns true if cache was used, false if we had to call the API
    async loadFromStoredData() {
      console.log('📦 Loading all data from Pinia incident store + API...');
      let usedCache = false;
      
      try {
        this.incidentStore.hydrateFullIncidentsFromService();
        const storedIncidents = this.incidentStore.prefetchedFullIncidents;
        console.log('🔍 [loadFromStoredData] Checking stored incidents cache:', {
          exists: !!storedIncidents,
          isArray: Array.isArray(storedIncidents),
          length: storedIncidents ? storedIncidents.length : 0,
          sampleId: storedIncidents && storedIncidents.length > 0 ? storedIncidents[0]?.IncidentId : null
        });
        
        if (storedIncidents && Array.isArray(storedIncidents) && storedIncidents.length > 0) {
          console.log(`✅ [loadFromStoredData] Loading ${storedIncidents.length} incidents from storage`);
          
          // Store full dataset for client-side pagination
          this.allIncidents = [...storedIncidents];
          this.totalIncidentsCount = this.allIncidents.length;
          // Initialize pagination state
          this.currentPage = 1;
          if (!this.pageSize || this.pageSize <= 0) {
            this.pageSize = 20;
          }
          // Apply filters and pagination on the full dataset
          this.applyClientSideFiltersAndPaging();
          console.log(
            `📊 [loadFromStoredData] allIncidents=${this.allIncidents.length}, ` +
            `visible incidents=${this.incidents.length}, pageSize=${this.pageSize}`
          );
          
          this.isLoadingIncidents = false;
          console.log(`✅ [loadFromStoredData] isLoadingIncidents set to false`);
          usedCache = true; // used cache
        } else {
          // Empty cache is an expected state on fresh session/reload.
          // Treat this as normal flow and fetch first page from API.
          console.info('ℹ️ [loadFromStoredData] Incident cache is empty. Loading first page from API...');

          // FAST FALLBACK: just fetch the first page from API using server-side pagination.
          // Do NOT prefetch ALL incidents here to avoid huge DB load.
          if (!this.pageSize || this.pageSize <= 0) {
            this.pageSize = 20;
          }
          // Pinia/session first: peek is sync; slow API runs in background so shell is not blocked ~30s.
          const listFromPinia = await this.fetchIncidents(1, this.pageSize, { deferNetwork: true });
          usedCache = listFromPinia === true;
        }
        
        // Keep startup minimal: load only incident list at first paint.
        // Reviewer/users are lazy-loaded only when assignment modal opens.
        
        console.log('✅ Critical data loaded from storage/API! Page should be visible now.');
        return usedCache;
      } catch (error) {
        console.error('❌ Error loading from stored data:', error);
        // Fallback to incident list API only.
        await this.fetchIncidents(1, this.pageSize);
        return false; // error path, used API
      } finally {
        this.isLoadingIncidents = false;
        this.$nextTick(() => {
          this.handleResize();
        });
      }
    },
    
    /**
     * Apply client-side filters, sorting, and pagination on allIncidents.
     * Used when we have a prefetched cache so we don't hit the API for each page.
     */
    applyClientSideFiltersAndPaging() {
      if (!Array.isArray(this.allIncidents) || this.allIncidents.length === 0) {
        return;
      }

      let data = [...this.allIncidents];

      // Simple text search across key fields
      if (this.searchQuery && this.searchQuery.trim()) {
        const q = this.searchQuery.trim().toLowerCase();
        data = data.filter(item => {
          const fields = [
            item.IncidentTitle,
            item.Origin,
            item.RiskPriority,
            item.RiskCategory,
            item.Status,
            item.AffectedBusinessUnit,
            item.IncidentCategory,
            item.IncidentId
          ];
          return fields.some(v => v && String(v).toLowerCase().includes(q));
        });
      }

      // Basic filters
      if (this.selectedStatus) {
        const statusFilter = this.selectedStatus.toLowerCase();
        data = data.filter(
          item => (item.Status || '').toLowerCase() === statusFilter
        );
      }
      if (this.selectedPriority) {
        const priorityFilter = this.selectedPriority.toLowerCase();
        data = data.filter(
          item => (item.RiskPriority || '').toLowerCase() === priorityFilter
        );
      }
      if (this.selectedBusinessUnit) {
        data = data.filter(
          item => (item.AffectedBusinessUnit || '') === this.selectedBusinessUnit
        );
      }
      if (this.selectedBusinessCategory) {
        data = data.filter(
          item => (item.IncidentCategory || '') === this.selectedBusinessCategory
        );
      }
      if (this.selectedFramework) {
        const fwId = String(this.selectedFramework);
        data = data.filter(item => {
          const val = item.framework_id || item.FrameworkId;
          return val != null && String(val) === fwId;
        });
      }

      // Sorting (matches backend sort_field/sort_order basics)
      if (this.sortField) {
        const field = this.sortField;
        const order = this.sortOrder === 'desc' ? -1 : 1;
        data.sort((a, b) => {
          const av = a[field];
          const bv = b[field];
          if (av == null && bv == null) return 0;
          if (av == null) return -1 * order;
          if (bv == null) return 1 * order;
          if (av < bv) return -1 * order;
          if (av > bv) return 1 * order;
          return 0;
        });
      } else {
        // Default sort by IncidentId DESC, like backend
        data.sort((a, b) => (b.IncidentId || 0) - (a.IncidentId || 0));
      }

      this.totalIncidentsCount = data.length;

      const pageSize = this.pageSize || 20;
      const currentPage = this.currentPage || 1;
      const start = (currentPage - 1) * pageSize;
      const end = start + pageSize;

      this.incidents = data.slice(start, end);
    },
    
    /**
     * Build query params for /api/incident-incidents/ (shared by Pinia store cache key + request).
     */
    buildIncidentListRequestParams({ limit, offset, minimalParamsOnly }) {
      const params = { limit, offset }
      if (minimalParamsOnly) return params
          if (this.searchQuery && this.searchQuery.trim()) {
        params.search = this.searchQuery.trim()
          }
          if (this.sortField) {
        params.sort_field = this.sortField
        params.sort_order = this.sortOrder
      }
      if (
        this.selectedFramework !== undefined &&
        this.selectedFramework !== null &&
        this.selectedFramework !== ''
      ) {
        const frameworkId = Number.parseInt(String(this.selectedFramework), 10)
            if (Number.isInteger(frameworkId) && frameworkId > 0) {
          params.framework_id = frameworkId
        }
      }
      if (this.selectedPolicy) params.policy_id = this.selectedPolicy
      if (this.selectedSubPolicy) params.subpolicy_id = this.selectedSubPolicy
      if (this.selectedPriority) params.priority = this.selectedPriority
      if (this.selectedBusinessUnit) params.business_unit = this.selectedBusinessUnit
      if (this.selectedBusinessCategory) {
        params.business_category = this.selectedBusinessCategory
      }
      if (this.selectedStatus) params.status = this.selectedStatus
      return params
    },

    _snapshotIncidentRow(incident) {
      if (!incident) return null
      try {
        if (typeof structuredClone === 'function') return structuredClone(incident)
      } catch {
        /* ignore */
      }
      try {
        return JSON.parse(JSON.stringify(incident))
      } catch {
        return { ...incident }
      }
    },

    /**
     * Update visible rows + Pinia list caches immediately; return snapshot for rollback.
     */
    applyOptimisticIncidentPatch(incident, partial) {
      if (!incident || incident.IncidentId == null || !partial) return null
      const snapshot = this._snapshotIncidentRow(incident)
      const id = incident.IncidentId
      const idStr = String(id)
      const list = this.incidents
      if (Array.isArray(list)) {
        const idx = list.findIndex((r) => String(r.IncidentId) === idStr)
        if (idx >= 0) Object.assign(list[idx], partial)
      }
      if (Array.isArray(this.allIncidents) && this.allIncidents.length) {
        const j = this.allIncidents.findIndex((r) => String(r.IncidentId) === idStr)
        if (j >= 0) Object.assign(this.allIncidents[j], partial)
      }
      this.incidentStore.patchIncidentInListCaches(id, partial)
      return snapshot
    },

    rollbackOptimisticIncident(incidentId, snapshot) {
      if (!snapshot) return
      this.incidentStore.restoreIncidentRowInListCaches(incidentId, snapshot)
      const idStr = String(incidentId)
      const restored = this._snapshotIncidentRow(snapshot)
      if (!restored) return
      const restoredCopy = this._snapshotIncidentRow(snapshot)
      if (Array.isArray(this.incidents)) {
        const idx = this.incidents.findIndex((r) => String(r.IncidentId) === idStr)
        if (idx >= 0) this.incidents.splice(idx, 1, restored)
      }
      if (Array.isArray(this.allIncidents) && this.allIncidents.length) {
        const j = this.allIncidents.findIndex((r) => String(r.IncidentId) === idStr)
        if (j >= 0) this.allIncidents.splice(j, 1, restoredCopy || restored)
      }
    },

    /** Reconcile with server without blocking UI (no invalidate / forced refetch). */
    afterIncidentListMutationSoftRevalidate() {
      const limit = this.pageSize
      const offset = (this.currentPage - 1) * limit
      this.scheduleIncidentsListBackgroundRevalidate({
        page: this.currentPage,
        pageSize: this.pageSize,
        requestParams: this.buildIncidentListRequestParams({
          limit,
          offset,
          minimalParamsOnly: false,
        }),
        minimalParamsOnly: false,
      })
    },

    refetchIncidentsListForced() {
      this.incidentStore.invalidateServerIncidentList();
      return this.fetchIncidents(null, null, { force: true });
    },

    applyIncidentsListResult(result) {
      if (!result || result.backgroundError) return
      this.incidents = result.items || []
      this.totalIncidentsCount = result.total ?? 0
      if (result.page != null) this.currentPage = result.page
      if (result.pageSize != null) this.pageSize = result.pageSize
      this.allIncidents = []
    },

    /**
     * After painting from Pinia (peek), refresh the same list query in the background and merge when still relevant.
     */
    scheduleIncidentsListBackgroundRevalidate({ page, pageSize, requestParams, minimalParamsOnly }) {
      const identityKey = this.incidentStore.getIncidentsListQueryKey(page, pageSize, requestParams)
      this.incidentStore
        .fetchIncidentsPage({
          page,
          pageSize,
          requestParams,
          force: true,
          background: true,
        })
        .then((r) => {
          if (!r || r.backgroundError) return
          const limit = this.pageSize
          const offset = (this.currentPage - 1) * this.pageSize
          const nowParams = this.buildIncidentListRequestParams({
            limit,
            offset,
            minimalParamsOnly: minimalParamsOnly === true,
          })
          const nowKey = this.incidentStore.getIncidentsListQueryKey(this.currentPage, this.pageSize, nowParams)
          if (nowKey !== identityKey) return
          this.applyIncidentsListResult(r)
          this.$nextTick(() => {
            this.handleResize()
          })
        })
        .catch(() => {})
    },

    /**
     * @param {Object} [options]
     * @param {boolean} [options.deferNetwork] When true with default page-1 + no filters: paint from Pinia/session if
     *   available, then run the slow list GET in the background so `await fetchIncidents` returns immediately.
     * @returns {Promise<boolean|void>} true when the list was painted immediately from Pinia (peek); false when a network path was started or completed.
     */
    async fetchIncidents(page = null, pageSize = null, options = {}) {
      const startedAt = performance.now()
      const minimalParamsOnly = options?.minimalParamsOnly === true
      const force = options?.force === true
      const skipBackgroundRevalidate = options?.skipBackgroundRevalidate === true
      const deferNetwork = options.deferNetwork === true

      const currentPage = page !== null ? page : this.currentPage
      const currentPageSize = pageSize !== null ? pageSize : this.pageSize
      const offset = (currentPage - 1) * currentPageSize
      const limit = currentPageSize

      this.incidentStore.restoreIncidentListPageFromSession()

      console.log(
        `🔄 [fetchIncidents] page ${currentPage} size ${limit} offset ${offset} (Pinia cache-first)`
      )

      const requestParams = this.buildIncidentListRequestParams({
        limit,
        offset,
        minimalParamsOnly,
      })
      console.log('📤 [fetchIncidents] API call params:', requestParams)

      if (!force) {
        const quick = this.incidentStore.peekIncidentsListCache(currentPage, currentPageSize, requestParams)
        if (quick) {
          this.applyIncidentsListResult(quick)
          this.isLoadingIncidents = false
          // Only hit the network when this slice is stale — always scheduling SWR stacked many
          // concurrent ~30s background GETs (one per cache hit / page) and looked like Pinia was ignored.
          if (!skipBackgroundRevalidate && quick.stale === true) {
            this.scheduleIncidentsListBackgroundRevalidate({
              page: currentPage,
              pageSize: currentPageSize,
              requestParams,
              minimalParamsOnly,
            })
          }
          this.lastIncidentFetchMs = performance.now() - startedAt
          this.$nextTick(() => {
            this.handleResize()
          })
          console.log(
            `✅ [fetchIncidents] page ${currentPage}: ${quick.items.length} incidents from Pinia (stale=${!!quick.stale}), background revalidate scheduled`
          )
          return true
        }
      }

      const isDefaultFirstPage =
        currentPage === 1 &&
        !minimalParamsOnly &&
        !this.hasActiveFilters

      if (deferNetwork && !force && isDefaultFirstPage) {
        const expectKey = this.incidentStore.getIncidentsListQueryKey(1, currentPageSize, requestParams)
        this.isLoadingIncidents = false
        this.incidentsListFetchPending = true
        this.incidentStore
          .fetchIncidentsPage({
            page: currentPage,
            pageSize: currentPageSize,
            requestParams,
            force: false,
            background: true,
          })
          .then((r) => {
            if (!r || r.backgroundError) return
            const nowParams = this.buildIncidentListRequestParams({
              limit: this.pageSize,
              offset: 0,
              minimalParamsOnly: false,
            })
            const nowKey = this.incidentStore.getIncidentsListQueryKey(1, this.pageSize, nowParams)
            if (nowKey !== expectKey) return
            this.applyIncidentsListResult(r)
            this.$nextTick(() => {
              this.handleResize()
            })
          })
          .catch((err) => {
            console.error('Deferred incident list fetch failed:', err)
            PopupService.error('Failed to load incidents. Please try again.')
          })
          .finally(() => {
            this.incidentsListFetchPending = false
            this.lastIncidentFetchMs = performance.now() - startedAt
          })
        console.log('✅ [fetchIncidents] Background list fetch started (shell not blocked on slow API)')
        return false
      }

      this.isLoadingIncidents = true
      try {
        const result = await this.incidentStore.fetchIncidentsPage({
          page: currentPage,
          pageSize: currentPageSize,
          requestParams,
          force,
          background: false,
        })

        this.applyIncidentsListResult(result)

        console.log(
          `✅ [fetchIncidents] page ${currentPage}: ${(result.items || []).length} incidents (total ${result.total}, fromCache=${result.fromCache})`
        )

        if (result.fromCache && !force && !skipBackgroundRevalidate && result.stale === true) {
          this.scheduleIncidentsListBackgroundRevalidate({
            page: currentPage,
            pageSize: currentPageSize,
            requestParams,
            minimalParamsOnly,
          })
        }

        this.$nextTick(() => {
          this.handleResize()
        })
        return false
      } catch (error) {
        console.error('Failed to fetch incidents:', error)
        console.error('Error details:', error.response)
        console.error('Error message:', error.message)
        console.error('Error code:', error.code)
        console.error('Error config:', error.config)

        if (error?.response?.status === 400 && !minimalParamsOnly) {
          console.warn(
            '⚠️ [fetchIncidents] 400 from list API, retrying with minimal pagination params only'
          )
          return await this.fetchIncidents(page, pageSize, {
            minimalParamsOnly: true,
            force: options.force,
            skipBackgroundRevalidate: options.skipBackgroundRevalidate,
          })
        }

        if (!AccessUtils.handleApiError(error, 'view incidents')) {
          let errorMessage = 'Failed to load incidents. '
          
          if (error.code === 'ECONNABORTED') {
            errorMessage +=
              'Request timed out. The database may be slow or contain many records. Please try applying filters to narrow down the results, or contact your administrator if the issue persists.'
          } else if (error.code === 'ERR_NETWORK') {
            errorMessage += 'Network error. Please check your connection.'
          } else if (error.response && error.response.status === 500) {
            errorMessage +=
              'Server error. The backend may be experiencing issues. Please try again later or contact your administrator.'
          } else if (error.response && error.response.status) {
            errorMessage += `Server error (${error.response.status}). Please try again.`
          } else {
            errorMessage += 'Please try again.'
          }
          
          PopupService.error(errorMessage)
        }
        return false
      } finally {
        this.lastIncidentFetchMs = performance.now() - startedAt
        this.isLoadingIncidents = false
      }
    },
    handlePageChange(page) {
      console.log(`📄 [Incident.vue] Page changed to: ${page}`);
      // If we have cached allIncidents, paginate on client; otherwise fall back to API
      if (Array.isArray(this.allIncidents) && this.allIncidents.length > 0) {
        this.currentPage = page;
        this.applyClientSideFiltersAndPaging();
      } else {
        // Server-side list: do not set currentPage until rows match (avoids "page 6" footer with page 1 rows
        // while sync-current-page updates DynamicTable before fetch completes).
        this.fetchIncidents(page, this.pageSize);
      }
    },
    handlePageSizeChange(newSize) {
      console.log(`📏 [Incident.vue] Page size changed to: ${newSize}`);
      if (newSize === 'all') {
        console.warn('⚠️ "All" selected - this may cause high memory usage with large datasets');
        this.pageSize = 1000; // Large number instead of "all"
      } else {
        this.pageSize = parseInt(newSize, 10);
      }
      if (Array.isArray(this.allIncidents) && this.allIncidents.length > 0) {
        this.currentPage = 1; // Reset to first page when slicing client-side cache
        this.applyClientSideFiltersAndPaging();
      } else {
        // Server-side: currentPage updates when applyIncidentsListResult runs (page 1).
        this.fetchIncidents(1, this.pageSize);
      }
    },
    async fetchUsers() {
      try {
        // Try to get from stored data first
        const storedUsers = this.incidentStore.getDomainBulkData('incidentUsers');
        if (storedUsers && Array.isArray(storedUsers) && storedUsers.length > 0) {
          console.log('📦 Using stored users data from Pinia:', storedUsers.length, 'users');
          this.availableUsers = storedUsers.map(user => ({
            id: user.UserId || user.id,
            name: user.UserName || user.name,
            role: user.role || user.Role || ''
          }));
          console.log('✅ Mapped availableUsers:', this.availableUsers.length);
          return;
        }
        
        // Fallback to API call
        console.log('🔄 Fetching users from API (cache empty or invalid)');
        // Get current user ID to exclude from reviewer list
        const currentUserId = sessionStorage.getItem('user_id') || localStorage.getItem('user_id') || ''
        // Fetch reviewers filtered by RBAC permissions (EvaluateAssignedIncident) for incident module
        const response = await axiosInstance.get(API_ENDPOINTS.USERS_FOR_REVIEWER_SELECTION, {
          params: {
            module: 'incident',
            current_user_id: currentUserId
          },
          withCredentials: true,
          headers: {
            'Content-Type': 'application/json'
          }
        });
        
        console.log('✅ Users API response:', response.data);
        console.log('✅ Response status:', response.status);
        
        // Handle response format: should be an array
        let users = [];
        if (Array.isArray(response.data)) {
          users = response.data;
          console.log('✅ Parsed users from direct array format:', users.length);
        } else {
          console.warn('⚠️ Unexpected response format:', response.data);
        }
        
        // Map the API response to match the expected frontend structure
        this.availableUsers = users.map(user => ({
          id: user.UserId || user.id || user.userId,
          name: user.UserName || user.name || user.username || 'Unknown',
          role: user.Role || user.role || ''
        })).filter(user => user.id); // Filter out invalid users
        
        console.log('✅ Mapped availableUsers:', this.availableUsers.length, 'users');
        console.log('🔍 Sample users:', this.availableUsers.slice(0, 3));
        
        // Update cache for future use
        if (this.availableUsers.length > 0) {
          this.incidentStore.setDomainBulkData('incidentUsers', users);
        }
      } catch (error) {
        console.error('❌ Failed to fetch users:', error);
        console.error('❌ Error details:', error.response?.data);
        console.error('❌ Error status:', error.response?.status);
        
        // Try fallback endpoint
        try {
          console.log('🔄 Trying fallback endpoint: /api/users/');
          const fallbackResponse = await axiosInstance.get('/api/users/', {
            withCredentials: true
          });
          
          let users = [];
          if (fallbackResponse.data && fallbackResponse.data.success && fallbackResponse.data.users) {
            users = fallbackResponse.data.users;
          } else if (Array.isArray(fallbackResponse.data)) {
            users = fallbackResponse.data;
          }
          
          this.availableUsers = users.map(user => ({
            id: user.UserId || user.id,
            name: user.UserName || user.name,
            role: user.role || user.Role || ''
          })).filter(user => user.id);
          
          console.log('✅ Fallback endpoint succeeded:', this.availableUsers.length, 'users');
          
          // Update cache
          if (this.availableUsers.length > 0) {
            this.incidentStore.setDomainBulkData('incidentUsers', users);
          }
        } catch (fallbackError) {
          console.error('❌ Fallback endpoint also failed:', fallbackError);
          
          // Check if this is an access denied error first
          if (!AccessUtils.handleApiError(error, 'view users')) {
            // Only show generic error if it's not an access denied error
            PopupService.error('Failed to load reviewers. Please refresh the page and try again.');
          }
          
          // Keep empty array if fetch fails
          this.availableUsers = [];
        }
      }
    },
    /**
     * Normalize framework rows for the incident filter dropdown (`id` / `name`).
     */
    mapRowsToIncidentFrameworkOptions(rows) {
      const out = []
      const seen = new Set()
      for (const fw of rows || []) {
        const rawId =
          fw.id ?? fw.FrameworkId ?? fw.framework_id ?? fw.FrameworkID ?? fw.value
        if (rawId == null || rawId === '') continue
        const sid = String(rawId)
        if (seen.has(sid)) continue
        seen.add(sid)
        const name =
          fw.name ??
          fw.FrameworkName ??
          fw.framework_name ??
          fw.FrameworkName_plain ??
          `Framework ${sid}`
        out.push({ ...fw, id: rawId, name })
      }
      return out
    },

    /** Drop known inactive rows; keep rows with no status (public / approved lists). */
    filterNonInactiveFrameworkRows(rows) {
      return (rows || []).filter((fw) => {
        const activeStatus = fw.status || fw.Status || fw.ActiveInactive || fw.activeInactive || ''
        if (!activeStatus) return true
        const inactive =
          activeStatus === 'Inactive' ||
          activeStatus === 'inactive' ||
          activeStatus === 'INACTIVE'
        return !inactive
      })
    },

    /**
     * Framework dropdown: reuse session/global/Pinia lists first so we do not stack another
     * slow `all-policies/frameworks` or `/api/frameworks/` call on top of Home / navbar loads.
     */
    async fetchFrameworks() {
      try {
        const frameworkStore = useFrameworkStore()
        frameworkStore.ensureUserScopedState()
        const globalCache = useFrameworkGlobalCacheStore()
        globalCache.hydrate(frameworkStore.getCurrentUserContextId())

        const fromGlobal = this.mapRowsToIncidentFrameworkOptions(
          this.filterNonInactiveFrameworkRows(globalCache.frameworks || [])
        )
        if (fromGlobal.length) {
          this.frameworks = fromGlobal
          this.incidentStore.setDomainBulkData('incidentFrameworks', fromGlobal)
          return
        }

        const cachedPinia = this.incidentStore.getDomainBulkData('incidentFrameworks')
        if (Array.isArray(cachedPinia) && cachedPinia.length) {
          this.frameworks = this.mapRowsToIncidentFrameworkOptions(cachedPinia)
          return
        }

        const storeFw = frameworkStore.frameworks || []
        if (storeFw.length) {
          const mapped = this.mapRowsToIncidentFrameworkOptions(
            this.filterNonInactiveFrameworkRows(storeFw)
          )
          if (mapped.length) {
            this.frameworks = mapped
            this.incidentStore.setDomainBulkData('incidentFrameworks', mapped)
            return
          }
        }

        let responseData
        try {
          responseData = await apiService.get('/api/frameworks/approved-active/', {}, { timeout: 60000 })
        } catch (primaryErr) {
          console.warn('[Incident] approved-active frameworks failed, falling back:', primaryErr?.message || primaryErr)
          const response = await axiosInstance.get(API_ENDPOINTS.COMPLIANCE_ALL_POLICIES_FRAMEWORKS, {
            timeout: 120000,
          })
          responseData = response.data
        }

        let allFrameworks = []
        if (Array.isArray(responseData)) {
          allFrameworks = responseData
        } else if (responseData?.frameworks && Array.isArray(responseData.frameworks)) {
          allFrameworks = responseData.frameworks
        } else if (Array.isArray(responseData?.data)) {
          allFrameworks = responseData.data
        }

        this.frameworks = this.mapRowsToIncidentFrameworkOptions(
          this.filterNonInactiveFrameworkRows(allFrameworks)
        )
        if (this.frameworks.length) {
          this.incidentStore.setDomainBulkData('incidentFrameworks', this.frameworks)
        }
      } catch (error) {
        if (!AccessUtils.handleApiError(error, 'view frameworks')) {
          console.error('Error fetching frameworks:', error)
        }
        this.frameworks = []
      }
    },
    async fetchSelectedFramework() {
      try {
        console.log('🔍 Fetching selected framework for incident list...');
        const frameworkStore = useFrameworkStore();
        await frameworkStore.loadFrameworkFromSession();
        const frameworkResponse = {
          data: {
            frameworkId: frameworkStore.selectedFrameworkId,
          },
        };
        console.log('Framework response:', frameworkResponse.data);
        
        if (frameworkResponse.data && frameworkResponse.data.frameworkId) {
          const frameworkId = parseInt(frameworkResponse.data.frameworkId);
          // If frameworkId is empty, null, undefined, or 0, set it to empty string (All Frameworks)
          this.selectedFramework = frameworkId || '';
          console.log('✅ Set selectedFramework for incident list:', this.selectedFramework);
        } else {
          console.log('⚠️ No framework selected or frameworkId not found in response');
          // Try to get from localStorage as fallback
          const storedFrameworkId = getExplicitFrameworkId();
          if (storedFrameworkId) {
            this.selectedFramework = parseInt(storedFrameworkId);
            console.log('✅ Using framework ID from localStorage:', this.selectedFramework);
          } else {
            // No framework selected means "All Frameworks" - set to empty string
            this.selectedFramework = '';
            console.log('✅ No specific framework selected - showing all frameworks');
          }
        }
      } catch (frameworkError) {
        if (!AccessUtils.handleApiError(frameworkError, 'view selected framework')) {
          console.warn('⚠️ Could not fetch selected framework:', frameworkError);
        }
        // Try to get from localStorage as fallback
        const storedFrameworkId = getExplicitFrameworkId();
        if (storedFrameworkId) {
          this.selectedFramework = parseInt(storedFrameworkId);
          console.log('✅ Using framework ID from localStorage as fallback:', this.selectedFramework);
        } else {
          // No framework found anywhere means "All Frameworks" - set to empty string
          this.selectedFramework = '';
          console.log('✅ No framework ID found - showing all frameworks');
        }
      }
    },
    async fetchBusinessUnits() {
      try {
        // Try to get from stored data first
        const storedBusinessUnits = this.incidentStore.getDomainBulkData('incidentBusinessUnits');
        if (storedBusinessUnits && Array.isArray(storedBusinessUnits)) {
          console.log('📦 Using stored business units data from Pinia');
          this.businessUnits = storedBusinessUnits;
          return;
        }
        
        // Fallback to API call
        console.log('🔄 Fetching business units from API');
        const response = await axiosInstance.get(API_ENDPOINTS.BUSINESS_UNITS);
        if (response.data && Array.isArray(response.data)) {
          this.businessUnits = response.data;
        } else {
          this.businessUnits = [];
        }
        if (this.businessUnits.length > 0) {
          this.incidentStore.setDomainBulkData('incidentBusinessUnits', this.businessUnits);
        }
        console.log('Fetched business units:', this.businessUnits);
      } catch (error) {
        console.error('Error fetching business units:', error);
        this.businessUnits = [];
      }
    },
    async fetchBusinessCategories() {
      try {
        // Try to get from stored data first
        const storedCategories = this.incidentStore.getDomainBulkData('incidentCategories');
        if (storedCategories && Array.isArray(storedCategories)) {
          console.log('📦 Using stored categories data from Pinia');
          this.businessCategories = storedCategories;
          return;
        }
        
        // Fallback to API call
        console.log('🔄 Fetching categories from API');
        const response = await axiosInstance.get(API_ENDPOINTS.CATEGORIES);
        if (response.data && Array.isArray(response.data)) {
          this.businessCategories = response.data;
        } else {
          this.businessCategories = [];
        }
        if (this.businessCategories.length > 0) {
          this.incidentStore.setDomainBulkData('incidentCategories', this.businessCategories);
        }
        console.log('Fetched business categories:', this.businessCategories);
      } catch (error) {
        console.error('Error fetching business categories:', error);
        this.businessCategories = [];
      }
    },
    async fetchPolicies() {
      try {
        if (!this.selectedFramework) {
          this.policies = [];
          return;
        }
        
        const response = await axiosInstance.get(API_ENDPOINTS.COMPLIANCE_ALL_POLICIES_POLICIES, {
          params: { 
            framework_id: this.selectedFramework
          }
        });
        
        if (response.data && Array.isArray(response.data)) {
          this.policies = response.data;
        } else {
          this.policies = [];
        }
        console.log('Fetched policies for framework:', this.selectedFramework, this.policies);
      } catch (error) {
        if (!AccessUtils.handleApiError(error, 'view policies')) {
          console.error('Error fetching policies:', error);
        }
        this.policies = [];
      }
    },
    async fetchSubPolicies() {
      try {
        if (!this.selectedPolicy) {
          this.subpolicies = [];
          return;
        }
        
        const response = await axiosInstance.get(API_ENDPOINTS.COMPLIANCE_ALL_POLICIES_SUBPOLICIES, {
          params: { 
            policy_id: this.selectedPolicy
          }
        });
        
        if (response.data && Array.isArray(response.data)) {
          this.subpolicies = response.data;
        } else {
          this.subpolicies = [];
        }
        console.log('Fetched subpolicies for policy:', this.selectedPolicy, this.subpolicies);
      } catch (error) {
        if (!AccessUtils.handleApiError(error, 'view subpolicies')) {
          console.error('Error fetching subpolicies:', error);
        }
        this.subpolicies = [];
      }
    },
    filterIncidents() {
      console.log('filterIncidents called with searchQuery:', this.searchQuery);
      
      // Clear existing timeout
      if (this.searchTimeout) {
        clearTimeout(this.searchTimeout);
      }
      
      // Set new timeout for debounced search
      this.searchTimeout = setTimeout(() => {
        console.log('Debounce timeout reached, calling performSearch');
        this.performSearch();
      }, 500); // Increased to 500ms for better performance
    },
    
    performSearch() {
      console.log('performSearch called');
      // Reset to first page when searching
      this.currentPage = 1;
      // Perform backend search by refetching data
      this.fetchIncidents();
    },
    
    clearSearch() {
      console.log('Clear search clicked');
      this.searchQuery = '';
      // Clear any pending search timeout
      if (this.searchTimeout) {
        clearTimeout(this.searchTimeout);
        this.searchTimeout = null;
      }
      this.fetchIncidents();
    },
    setSortField(field) {
      // Toggle sort order if clicking the same field
      if (this.sortField === field) {
        this.toggleSortOrder();
      } else {
        this.sortField = field;
        // Default to ascending order when changing fields
        this.sortOrder = 'asc';
      }
      // Reset to first page when sorting
      this.currentPage = 1;
      // Refetch data with new sorting from backend
      this.fetchIncidents();
    },
    sortIncidents() {
      // Refetch data with sorting from backend
      this.fetchIncidents();
    },
    toggleSortOrder() {
      this.sortOrder = this.sortOrder === 'asc' ? 'desc' : 'asc';
      // Refetch data with new sort order from backend
      this.fetchIncidents();
    },
    handleResize() {
      // Update layout when window is resized
      const wrapper = document.querySelector('.incident-list-wrapper');
      if (wrapper) {
        wrapper.style.maxWidth = '100%';
      }
    },
    getPriorityClass(priority) {
      switch(priority?.toLowerCase()) {
        case 'high':
          return 'incident-priority-high';
        case 'medium':
          return 'incident-priority-medium';
        case 'low':
          return 'incident-priority-low';
        default:
          return '';
      }
    },
    formatDate(dateString) {
      if (!dateString) return '';
      
      const [year, month, day] = dateString.split('-');
      return `${month}/${day}/${year}`;
    },
    closeIncidentDetails() {
      this.selectedIncident = null;
      this.showIncidentDetails = false;
    },
    exportIncidents() {
      console.log('Exporting incidents...');
      this.isExporting = true;
      this.isExportDropdownOpen = false;

      // Request full export from backend (S3) using active filters. User identity must come from server session/JWT, not client-supplied user_id.
      const exportOptions = {
        filters: {
          search: this.searchQuery || '',
          sort_field: this.sortField || 'Date',
          sort_order: this.sortOrder || 'desc',
          framework_id: this.selectedFramework || '',
          policy_id: this.selectedPolicy || '',
          subpolicy_id: this.selectedSubPolicy || '',
          priority: this.selectedPriority || '',
          business_unit: this.selectedBusinessUnit || '',
          business_category: this.selectedBusinessCategory || '',
          status: this.selectedStatus || ''
        },
        include_all_records: true
      };

      axiosInstance.post(API_ENDPOINTS.INCIDENTS_EXPORT, {
        file_format: this.exportFormat,
        options: JSON.stringify(exportOptions)
      })
      .then(async (response) => {
        console.log('Export successful:', response.data);
        
        // Check if we have a file URL
        if (response.data && response.data.file_url) {
          const ok = await openDownloadInNewTabWithAnchorFallback(
            response.data.file_url,
            response.data.file_name || `incidents.${this.exportFormat}`
          );
          if (ok) {
            PopupService.success('Export completed successfully! File opened or downloaded.');
          } else {
            PopupService.warning('Export link is not from an allowed host.');
          }
        }
        
        this.isExporting = false;
      })
      .catch(error => {
        console.error('Export failed:', error);
        
        // Check if this is an access denied error first
        if (!AccessUtils.handleApiError(error, 'export incidents')) {
          // Only show generic error if it's not an access denied error
          PopupService.error('Export failed. Please try again.');
        }
        
        this.isExporting = false;
      });
    },
    loadCurrentUser() {
      console.log('Loading current user for incident assignment...');
      try {
        // Get current user from session
        this.currentUser = SessionUtils.getUserSession();
        console.log('Current user session data:', this.currentUser);
        
        if (this.currentUser && this.currentUser.name) {
          this.currentUserName = this.currentUser.name;
          console.log('Set current user name to:', this.currentUserName);
        } else {
          console.warn('No current user name found in session, using fallback');
          this.currentUserName = 'Current User';
        }
      } catch (error) {
        console.error('Error loading current user:', error);
        this.currentUserName = 'Current User';
      }
    },
    async onFrameworkChange() {
      console.log('Framework changed to:', this.selectedFramework);
      // Normalize framework ID from dropdown and ignore invalid values.
      if (this.selectedFramework !== undefined && this.selectedFramework !== null && this.selectedFramework !== '') {
        const frameworkId = Number.parseInt(String(this.selectedFramework), 10);
        this.selectedFramework = Number.isInteger(frameworkId) && frameworkId > 0 ? frameworkId : '';
      }
      console.log('Framework after type conversion:', this.selectedFramework, typeof this.selectedFramework);
      this.selectedPolicy = '';
      this.selectedSubPolicy = '';
      this.policies = [];
      this.subpolicies = [];
      this.currentPage = 1; // Reset to first page

      // Policy/subpolicy filters are currently not rendered in UI for this page.
      // Skip policy tree calls to avoid unnecessary network usage and 401 noise.
      this.fetchIncidents();
    },
    async onPolicyChange() {
      console.log('Policy changed to:', this.selectedPolicy);
      this.selectedSubPolicy = '';
      this.subpolicies = [];
      this.currentPage = 1; // Reset to first page
      
      if (this.selectedPolicy) {
        await this.fetchSubPolicies();
      }
      this.fetchIncidents();
    },
    onSubPolicyChange() {
      console.log('SubPolicy changed to:', this.selectedSubPolicy);
      this.currentPage = 1; // Reset to first page
      this.fetchIncidents();
    },
    onPriorityChange() {
      console.log('Priority changed to:', this.selectedPriority);
      this.currentPage = 1; // Reset to first page
      this.fetchIncidents();
    },
    onBusinessUnitChange() {
      console.log('Business Unit changed to:', this.selectedBusinessUnit);
      this.currentPage = 1; // Reset to first page
      this.fetchIncidents();
    },
    onBusinessCategoryChange() {
      console.log('Business Category changed to:', this.selectedBusinessCategory);
      this.currentPage = 1; // Reset to first page
      this.fetchIncidents();
    },
    clearAllFilters() {
      console.log('Clearing all filters');
      this.selectedFramework = '';
      this.selectedPolicy = '';
      this.selectedSubPolicy = '';
      this.selectedPriority = '';
      this.selectedBusinessUnit = '';
      this.selectedBusinessCategory = '';
      this.searchQuery = '';
      this.policies = [];
      this.subpolicies = [];
      this.currentPage = 1; // Reset to first page
      
      // Clear any pending search timeout
      if (this.searchTimeout) {
        clearTimeout(this.searchTimeout);
        this.searchTimeout = null;
      }
      
      this.fetchIncidents();
    },
    handleStorageChange(event) {
      if (!this.syncFrameworkFromGlobal) return;
      // Listen for framework changes in localStorage (from homepage)
      if (event.key === 'selectedFrameworkId' || event.key === 'frameworkId') {
        // Prevent refresh if:
        // 1. Page is not visible (tab is hidden)
        // 2. User is on a create/edit form page (to prevent losing prefilled data)
        const isPageVisible = document.visibilityState === 'visible';
        const currentPath = this.$route?.path || window.location.pathname;
        const isOnFormPage = currentPath.includes('/create') || 
                            currentPath.includes('/edit') || 
                            currentPath.includes('/compliance/create') ||
                            currentPath.includes('/risk/create') ||
                            currentPath.includes('/create-policy');
        
        if (!isPageVisible) {
          console.log('⏸️ Storage change detected but page is hidden - skipping refresh');
          return;
        }
        
        if (isOnFormPage) {
          console.log('⏸️ Storage change detected but user is on form page - skipping refresh to preserve form data');
          return;
        }
        
        console.log('🔄 Framework changed in localStorage:', event.newValue);
        if (event.newValue && event.newValue !== 'null' && event.newValue !== 'all') {
          const frameworkId = parseInt(event.newValue);
          if (frameworkId && frameworkId !== this.selectedFramework) {
            console.log(`🔄 Framework changed from ${this.selectedFramework} to ${frameworkId} - refreshing incidents`);
            this.selectedFramework = frameworkId;
            this.fetchIncidents();
          }
        } else if (!event.newValue || event.newValue === 'null' || event.newValue === 'all') {
          if (this.selectedFramework !== '') {
            console.log('🔄 Framework cleared in localStorage - showing all frameworks');
            this.selectedFramework = '';
            this.fetchIncidents();
          }
        }
      }
    },
  }
}
</script>

<style>
@import '@/assets/css/main.css';
@import '@/assets/css/dropdown.css';

/* Position breadcrumb at the top of the page - scoped to Incident page only */
.incident-view-container .filter-breadcrumbs {
  margin-top: 0;
  margin-bottom: 24px;
}

.data-source-message {
  margin-top: 4px;
  font-size: 0.85rem;
  color: #2563eb;
  font-weight: 500;
}
</style>
<style>
/* Add these styles to your existing CSS file or inline here */
.sort-indicator {
  margin-left: 5px;
  display: inline-block;
}

.checklist-header-row div {
  cursor: pointer;
  user-select: none;
  position: relative;
}

.checklist-header-row div:not(.incident-actions-header):hover {
  background-color: rgba(0, 0, 0, 0.05);
}

.checklist-header-row div.sorted {
  font-weight: bold;
  color: #3366cc;
}

.active-sort {
  background-color: #e0e7ff;
  color: #3366cc;
}

/* Header layout with export controls */
.incident-view-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 15px;
}

.export-btn:disabled {
  background-color: #f3f4f6 !important;
  color: #ffffff !important;
  box-shadow: none !important;
}

.export-btn:disabled i {
  color: #ffffff !important;
}

/* .export-controls {
  display: flex;
  align-items: center;
  gap: 10px;
}

.export-format-select {
  padding: 8px 12px;
  border: 1px solid #ccc;
  border-radius: 4px;
  background-color: white;
  font-size: 14px;
} */

/* .export-btn {
  padding: 8px 15px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: background-color 0.2s;
}

.export-btn:hover {
  background-color: #45a049;
}

.export-btn:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
} */

/* Current user display styles */
.incident-current-user-display {
  padding: 12px 15px;
  background-color: #f8f9fa;
  border: 2px solid #e3f2fd;
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.current-user-name {
  font-weight: 600;
  color: #1976d2;
  font-size: 14px;
}

.current-user-note {
  font-size: 12px;
  color: #666;
  font-style: italic;
}

.incident-filter-controls {
  display: flex;
  gap: 10px;
  margin: 10px 0 20px 0;
}

.incident-clear-filters {
  margin: 10px 0;
}


/* Risk Category styling */
.category-security {
  background-color: #ffebee;
  color: #c62828;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.category-compliance {
  background-color: #e3f2fd;
  color: #1565c0;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.category-operational {
  background-color: #fff3e0;
  color: #ef6c00;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.category-financial {
  background-color: #e8f5e8;
  color: #2e7d32;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.category-strategic {
  background-color: #f3e5f5;
  color: #7b1fa2;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.category-other {
  background-color: #f5f5f5;
  color: #616161;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

/* Incident Category styling */
/* Incident category - plain text, no badges */
.incident-category-security,
.incident-category-compliance,
.incident-category-operational,
.incident-category-financial,
.incident-category-strategic,
.incident-category-data-breach,
.incident-category-system-failure,
.incident-category-human-error,
.incident-category-malware,
.incident-category-phishing,
.incident-category-other {
  color: inherit;
  font-size: 14px;
  font-weight: normal;
}

/* Status styling - plain text with colored dots */
.status-open,
.status-assigned,
.status-approved,
.status-active,
.status-pending,
.status-completed,
.status-closed,
.status-scheduled,
.status-rejected,
.status-default {
  color: inherit !important;
  background-color: transparent !important;
  padding: 0 !important;
  border: none !important;
  border-radius: 0 !important;
  font-size: 13px !important;
  font-weight: 500 !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: flex-start !important;
  gap: 8px !important;
  width: 100% !important;
  text-align: left !important;
}

/* Colored dots for each status */
.status-open::before {
  content: '';
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background-color: #ffc107;
  display: inline-block;
}

.status-assigned::before {
  content: '';
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background-color: #2196f3;
  display: inline-block;
}

.status-scheduled::before {
  content: '';
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background-color: #9c27b0;
  display: inline-block;
}

/* For "new" status - green dot */
.status-active::before,
.status-approved::before,
.status-default::before,
.status-new::before {
  content: '';
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background-color: #4caf50;
  display: inline-block;
}

/* Text colors to match the dots */
.status-new,
.incident-status-cell .status-new {
  color: #4caf50 !important; /* Green */
  background-color: transparent !important;
  display: inline-flex !important;
  align-items: center !important;
  gap: 8px !important;
}

.status-open,
.incident-status-cell .status-open {
  color: #ffc107 !important; /* Yellow */
}

.status-assigned,
.incident-status-cell .status-assigned {
  color: #2196f3 !important; /* Blue */
}

.status-scheduled,
.incident-status-cell .status-scheduled {
  color: #9c27b0 !important; /* Violet */
}

/* Additional status dots for other statuses */
.status-pending::before,
.status-completed::before {
  content: '';
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background-color: #9e9e9e;
  display: inline-block;
}

.status-rejected::before,
.status-closed::before {
  content: '';
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background-color: #f44336;
  display: inline-block;
}
</style>
