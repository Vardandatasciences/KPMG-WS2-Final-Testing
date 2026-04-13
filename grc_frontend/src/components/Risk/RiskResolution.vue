<template>
  <div class="risk-resolution-container" style="background: white !important;">
    <!-- Toggle first so position matches Risk Workflow (constant when switching) -->
    <div class="risk-creation-mode-toggle risk-resolution-toggle-wrapper">
      <div class="toggle-group risk-resolution-toggle-group">
        <button
          type="button"
          class="toggle-button"
          :class="{ active: activeView === 'resolution' }"
          @click="navigateTo('resolution')"
        >
          Risk Resolution
        </button>
        <button
          type="button"
          class="toggle-button"
          :class="{ active: activeView === 'workflow' }"
          @click="navigateTo('workflow')"
        >
          Risk Workflow
        </button>
      </div>
    </div>

    <PopupModal />

    <!-- Search and Filter Bar (hidden when in mitigation workflow view) -->
    <div v-if="!showMitigationModal" class="risk-resolution-filters-wrapper">
      <p
        v-if="dataSourceMessage"
        class="risk-resolution-data-source"
      >
        {{ dataSourceMessage }}
      </p>
      <div class="search-bar" style="margin-bottom: 10px;">
        <i class="fas fa-search search-bar__icon"></i>
        <input
          type="text"
          v-model="searchQuery"
          placeholder="Search risks..."
          @input="filterRisks"
          class="search-bar__input"
        />
      </div>
      <div class="risk-resolution-filter-dropdowns">
        <CustomDropdown 
          :config="criticalityDropdownConfig"
          v-model="criticalityFilter"
          @change="filterRisks"
        />
        <CustomDropdown 
          :config="statusDropdownConfig"
          v-model="statusFilter"
          @change="filterRisks"
        />
        <CustomDropdown 
          :config="assignedToDropdownConfig"
          v-model="assignedToFilter"
          @change="filterRisks"
        />
        <CustomDropdown 
          :config="reviewerDropdownConfig"
          v-model="reviewerFilter"
          @change="filterRisks"
        />
      </div>
    </div>
    
    <div v-if="error" class="risk-resolution-error-message">
      {{ error }}
    </div>
    
    
    <!-- Show collapsible table if not in mitigation workflow -->
    <div v-if="!error && !showMitigationModal" class="risk-resolution-collapsible-container">
      <CollapsibleTable
        v-for="(section, index) in riskSections"
        :key="section.name"
        :section-config="section"
        :table-headers="tableHeaders"
        :is-expanded="expandedSections[index]"
        @toggle="toggleSection(index)"
        @task-click="openMitigationModal"
        @add-task="addTaskToSection"
      />
    </div>

    <!-- Mitigation Workflow Section -->
    <div v-if="showMitigationModal" class="risk-resolution-mitigation-workflow-section">
      <div class="risk-resolution-mitigation-header">
        <div class="risk-resolution-mitigation-header-left">
          <button
            class="back-icon-btn"
            @click="closeMitigationModal"
            aria-label="Back to Risks"
          >
            <i class="fas fa-arrow-left"></i>
          </button>
          <h2 v-if="viewOnlyMitigationModal">Viewing Mitigation Steps</h2>
          <h2 v-else>Assign Risk with Mitigation Steps</h2>
        </div>
      </div>
      <div class="risk-resolution-mitigation-body">
        <div v-if="loadingMitigations" class="risk-resolution-loading">
          <div class="risk-resolution-spinner"></div>
          <span>Loading mitigation steps...</span>
        </div>
        <div v-else>
          <div class="risk-resolution-risk-summary">
            <h3>{{ selectedRisk.RiskTitle || 'Risk #' + selectedRisk.RiskInstanceId }}</h3>
            <div class="risk-resolution-risk-details">
              <p><strong>ID:</strong> {{ selectedRisk.RiskInstanceId }}</p>
              <p><strong>Category:</strong> {{ selectedRisk.Category }}</p>
              <p><strong>Criticality:</strong> {{ selectedRisk.Criticality }}</p>
              <p><strong>Reviewer:</strong> <span class="risk-resolution-reviewer-info">{{ selectedRisk.Reviewer || selectedRisk.ReviewerName || 'Yet to Start' }}</span></p>
            </div>
          </div>
          
          <!-- Add User and Reviewer Assignment Section -->
          <div v-if="!viewOnlyMitigationModal" class="risk-resolution-assignment-section">
            <h3>Assign Risk</h3>
            <div class="risk-resolution-assignment-fields">
              <div class="risk-resolution-assignment-field">
                <label class="risk-resolution-assignment-label">Assign To:</label>
                <CustomDropdown
                  :options="assignToOptions"
                  :model-value="selectedUsers[selectedRisk.RiskInstanceId] || ''"
                  @update:model-value="onAssignToSelect"
                  placeholder="Select User"
                  :show-label="false"
                  class="risk-resolution-assignment-custom-dropdown"
                />
                <div v-if="selectedUsers[selectedRisk.RiskInstanceId]" class="risk-resolution-selected-user-info">
                  Selected User ID: {{ selectedUsers[selectedRisk.RiskInstanceId] }}
                </div>
              </div>
              <div class="risk-resolution-assignment-field">
                <label class="risk-resolution-assignment-label">Reviewer:</label>
                <CustomDropdown
                  :options="reviewerOptions"
                  :model-value="selectedReviewers[selectedRisk.RiskInstanceId] || ''"
                  @update:model-value="onReviewerSelect"
                  placeholder="Select Reviewer"
                  :show-label="false"
                  class="risk-resolution-assignment-custom-dropdown"
                />
                <div v-if="selectedReviewers[selectedRisk.RiskInstanceId]" class="risk-resolution-selected-user-info">
                  Selected Reviewer ID: {{ selectedReviewers[selectedRisk.RiskInstanceId] }}
                </div>
              </div>
              <div class="risk-resolution-assignment-field">
                <label class="risk-resolution-assignment-label" for="due-date-input">Due Date for Mitigation:</label>
                <input
                  id="due-date-input"
                  type="date"
                  v-model="mitigationDueDate"
                  class="risk-resolution-assignment-dropdown"
                  :readonly="viewOnlyMitigationModal"
                  :min="getTodayDate()"
                />
              </div>
            </div>
          </div>
          
          <div class="risk-resolution-mitigation-workflow">
            <h3>Mitigation Steps</h3>
            <!-- Existing Mitigation Steps -->
            <div v-if="mitigationSteps.length" class="risk-resolution-workflow-timeline">
              <div v-for="(step, index) in mitigationSteps" :key="index" class="risk-resolution-workflow-step">
                <div class="risk-resolution-step-number">Step {{ index + 1 }}</div>
                <div class="risk-resolution-step-content">
                  <textarea 
                    v-model="step.description" 
                    class="risk-resolution-mitigation-textarea"
                    :readonly="viewOnlyMitigationModal"
                    placeholder="Enter mitigation step description"
                  ></textarea>
                  <div class="risk-resolution-step-actions">
                    <button @click="removeMitigationStep(index)" class="risk-resolution-remove-step-btn" :disabled="viewOnlyMitigationModal">
                      <i class="fas fa-trash"></i> Remove
                    </button>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="risk-resolution-no-mitigations">
              <p>No mitigation steps defined for this risk. Add steps below.</p>
            </div>
            <!-- Add New Mitigation Step -->
            <div class="risk-resolution-add-mitigation">
              <textarea 
                v-model="newMitigationStep" 
                class="global-form-textarea"
                :readonly="viewOnlyMitigationModal"
                placeholder="Enter a new mitigation step description"
              ></textarea>
              <button @click="addMitigationStep" class="btn-add" :disabled="viewOnlyMitigationModal || !newMitigationStep.trim()">
                <i class="fas fa-plus"></i> Add Mitigation Step
              </button>
            </div>
            <!-- Submit Section -->
            <div class="risk-resolution-mitigation-actions">
              <button 
                @click="assignRiskWithMitigations" 
                class="btn btn-submit"
                :disabled="loading || viewOnlyMitigationModal || mitigationSteps.length === 0 || !mitigationDueDate || !selectedUsers[selectedRisk.RiskInstanceId] || !selectedReviewers[selectedRisk.RiskInstanceId]"
              >
                <i class="fas fa-user-plus"></i> Assign with Mitigations
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import CustomDropdown from '../CustomDropdown.vue';
import CollapsibleTable from '../CollapsibleTable.vue';
import { PopupModal } from '@/modules/popup';
import { API_ENDPOINTS } from '../../config/api.js';
import apiService from '@/services/apiService.js';
import riskDataService from '@/services/riskService';

const axios = {
  get: (url, config = {}) =>
    apiService.get(url, config?.params || {}, config).then((data) => ({ data, status: 200 })),
  post: (url, data = {}, config = {}) =>
    apiService.post(url, data, config).then((res) => ({ data: res, status: 200 })),
  delete: (url, config = {}) =>
    apiService.delete(url, config).then((res) => ({ data: res, status: 200 }))
};

export default {
  name: 'RiskResolution',
  components: {
    CustomDropdown,
    CollapsibleTable,
    PopupModal
  },
  data() {
    return {
      activeView: 'resolution', // Track active toggle view
      risks: [],
      filteredRisks: [],
      users: [],
      selectedUsers: {},
      selectedReviewers: {},
      loading: true,
      error: null,
      dataSourceMessage: '',
      // New properties for mitigation modal
      showMitigationModal: false,
      selectedRisk: {},
      mitigationSteps: [],
      newMitigationStep: '',
      loadingMitigations: false,
      mitigationDueDate: '',
      viewOnlyMitigationModal: false,
      // New properties for search and filtering
      searchQuery: '',
      criticalityFilter: '',
      statusFilter: '',
      assignedToFilter: '',
      reviewerFilter: '',
      expandedSections: [],
      // Dropdown open states
      openDropdowns: {
        criticality: false,
        status: false,
        assignedTo: false,
        reviewer: false,
        assignTo: false,
        reviewerAssign: false
      },
      // Search queries for dropdowns
      searchQueries: {
        criticality: '',
        status: '',
        assignedTo: '',
        reviewer: '',
        assignTo: '',
        reviewerAssign: ''
      }
    }
  },
  computed: {
    uniqueCriticalities() {
      return [...new Set(this.risks.map(risk => risk.Criticality).filter(Boolean))];
    },
    uniqueStatuses() {
      return [...new Set(this.risks.map(risk => risk.RiskStatus).filter(Boolean))];
    },
    uniqueAssignedUsers() {
      return [...new Set(this.risks.map(risk => 
        risk.RiskOwner && risk.RiskOwner !== 'System Owner' && risk.RiskOwner !== 'System User' ? 
        risk.RiskOwner : 'Yet to Start'
      ))];
    },
    uniqueReviewers() {
      return [...new Set(this.risks.map(risk => risk.ReviewerName || 'Yet to Start'))];
    },
    // Options for Assign To / Reviewer custom dropdowns (uses dropdown.css)
    assignToOptions() {
      const placeholders = [{ value: '', label: 'Select User' }];
      const userOptions = (this.users || []).map(user => ({
        value: this.getUserId(user),
        label: `${this.getUserName(user)} (ID: ${this.getUserId(user)})`
      }));
      return [...placeholders, ...userOptions];
    },
    reviewerOptions() {
      const placeholders = [{ value: '', label: 'Select Reviewer' }];
      const userOptions = (this.users || []).map(user => ({
        value: this.getUserId(user),
        label: `${this.getUserName(user)} (ID: ${this.getUserId(user)})`
      }));
      return [...placeholders, ...userOptions];
    },
    // Table headers for CollapsibleTable
    tableHeaders() {
      return [
        { key: 'riskId', label: 'RISK ID', width: '80px' },
        { key: 'riskTitle', label: 'RISK TITLE', width: '300px' },
        { key: 'category', label: 'CATEGORY', width: '120px' },
        { key: 'criticality', label: 'CRITICALITY', width: '100px' },
        { key: 'assignedTo', label: 'ASSIGNED TO', width: '150px' },
        { key: 'reviewer', label: 'REVIEWER', width: '150px' },
        { key: 'reviewCount', label: 'REVIEW COUNT', width: '100px' },
        { key: 'actions', label: 'ACTION', width: '120px' }
      ];
    },
    // Group risks by status for CollapsibleTable
    riskSections() {
      const sections = {};
      
      this.filteredRisks.forEach(risk => {
        let status = risk.RiskStatus || 'Unknown';
        
        // Map status names
        if (status === 'Not Assigned') {
          status = 'Yet to Start';
        } else if (status === 'Approved') {
          status = 'Completed';
        }
        
        if (!sections[status]) {
          sections[status] = {
            name: status,
            statusClass: this.getStatusClass(status),
            tasks: []
          };
        }
        
        // Format risk data for table display
        const formattedRisk = {
          incidentId: risk.RiskInstanceId,
          riskId: risk.RiskInstanceId,
          riskTitle: risk.RiskTitle || 'No title',
          category: risk.Category || 'N/A',
          criticality: risk.Criticality || 'N/A',
          assignedTo: risk.RiskOwner && risk.RiskOwner !== 'System Owner' && risk.RiskOwner !== 'System User' ? 
            risk.RiskOwner : 'Yet to Start',
          reviewer: risk.Reviewer || risk.ReviewerName || 'Yet to Start',
          reviewCount: risk.ReviewerCount || 0,
          actions: 'assign',
          originalRisk: risk // Keep reference to original risk data
        };
        
        sections[status].tasks.push(formattedRisk);
      });
      
      // Convert to array and sort by status priority - "Yet to Start" first
      return Object.values(sections).sort((a, b) => {
        const statusPriority = {
          'Yet to Start': 1,
          'Assigned': 2,
          'In Progress': 3,
          'Pending': 4,
          'Open': 5,
          'Completed': 6,
          'Closed': 7,
          'Rejected': 8
        };
        return (statusPriority[a.name] || 999) - (statusPriority[b.name] || 999);
      });
    },
    // Dropdown configurations
    criticalityDropdownConfig() {
      return {
        label: 'Criticality',
        defaultValue: 'All Criticality',
        values: [
          { value: '', label: 'All Criticality' },
          ...this.uniqueCriticalities.map(criticality => ({
            value: criticality,
            label: criticality
          }))
        ]
      };
    },
    statusDropdownConfig() {
      return {
        label: 'Status',
        defaultValue: 'All Status',
        values: [
          { value: '', label: 'All Status' },
          ...this.uniqueStatuses.map(status => ({
            value: status,
            label: status
          }))
        ]
      };
    },
    assignedToDropdownConfig() {
      return {
        label: 'Assigned To',
        defaultValue: 'All Assigned To',
        values: [
          { value: '', label: 'All Assigned To' },
          ...this.uniqueAssignedUsers.map(user => ({
            value: user,
            label: user
          }))
        ]
      };
    },
    reviewerDropdownConfig() {
      return {
        label: 'Reviewer',
        defaultValue: 'All Reviewers',
        values: [
          { value: '', label: 'All Reviewers' },
          ...this.uniqueReviewers.map(reviewer => ({
            value: reviewer,
            label: reviewer
          }))
        ]
      };
    }
  },
  mounted() {
    // Reset all filters to default "All" values
    this.searchQuery = '';
    this.criticalityFilter = '';
    this.statusFilter = '';
    this.assignedToFilter = '';
    this.reviewerFilter = '';
    
    this.fetchRisks();
    this.fetchUsers();
    
    // Close dropdowns when clicking outside
    document.addEventListener('click', this.handleClickOutside);
  },
  created() {
    // Initialize filteredRisks with all risks that have completed scoring
    this.filteredRisks = this.risks;
  },
  methods: {
    async sendPushNotification(notificationData) {
      try {
        await apiService.post(API_ENDPOINTS.PUSH_NOTIFICATION, notificationData);
        console.log('Push notification sent successfully');
      } catch (error) {
        console.error('Error sending push notification:', error);
      }
    },
    fetchRisks() {
      this.loading = true;
      this.dataSourceMessage = 'Loading risks...';
      
      const useCachedRisks = async () => {
        const cachedRisks = riskDataService.getData('riskInstances') || [];
        const clonedRisks = JSON.parse(JSON.stringify(cachedRisks));
        this.handleRiskResponse(clonedRisks);
        this.dataSourceMessage = `Loaded ${clonedRisks.length} risks from cache (prefetched on Home page)`;
      };
      
      const fetchFromApi = () => {
        return axios.get(API_ENDPOINTS.RISK_INSTANCES)
        .then(response => {
          let apiRisks;
            if (Array.isArray(response.data)) {
              apiRisks = response.data;
            } else if (response.data?.success && response.data?.risks) {
              apiRisks = response.data.risks;
            } else {
              apiRisks = response.data || [];
            }
            
            this.handleRiskResponse(apiRisks);
            this.dataSourceMessage = `Loaded ${apiRisks.length} risks directly from API (cache unavailable)`;
            riskDataService.setData('riskInstances', apiRisks);
          });
      };
      (async () => {
        try {
          if (typeof window !== 'undefined' && window.riskDataFetchPromise) {
            try {
              await window.riskDataFetchPromise;
            } catch (prefetchError) {
              console.warn('RiskResolution: Prefetch promise rejected:', prefetchError);
            }
          }
          
          if (riskDataService.hasRiskInstancesCache()) {
            await useCachedRisks();
          } else {
            await fetchFromApi();
          }
        } catch (error) {
          console.error('Error fetching risks:', error);
          this.error = `Failed to fetch risks: ${error.message}`;
          this.dataSourceMessage = 'Failed to load risks';
        } finally {
          const needsApiFetch = !this.error && (!this.risks || this.risks.length === 0);
          if (needsApiFetch) {
            this.dataSourceMessage = riskDataService.hasRiskInstancesCache()
              ? 'No risks found in cache; fetching from API...'
              : 'Fetching risks from API...';
            this.loading = true;
            fetchFromApi()
              .catch(apiError => {
                console.error('Error fetching risks from API:', apiError);
                this.error = `Failed to fetch risks: ${apiError.message}`;
                this.dataSourceMessage = 'Failed to load risks';
              })
              .finally(() => {
                this.loading = false;
              });
          } else {
            this.loading = false;
          }
        }
      })();
    },
    handleRiskResponse(responseData) {
      console.log('Risk data received:', responseData);
      
      if (responseData && responseData.length > 0) {
        responseData.forEach(risk => {
          console.log(`Risk ID: ${risk.RiskInstanceId}, Reviewer: ${risk.Reviewer || risk.ReviewerName || 'None'}, ReviewerId: ${risk.ReviewerId || 'None'}`);
        });
      }
      
      // First filter: Only include risks with completed scoring (Risk Impact, Risk Likelihood, Risk Exposure Rating)
      // and not rejected (Appetite is not 'No' and Status is not 'Rejected')
      // This is the base requirement for risks to appear in Risk Resolution
      const filteredRisks = responseData.filter(risk => {
        // Use helper methods to check if risk has completed scoring and is not rejected
        const hasScoring = this.hasCompletedScoring(risk);
        const isNotRejected = !this.isRiskRejected(risk);
        
        // Only include risks with complete scoring and not rejected
        return hasScoring && isNotRejected;
      });
      
      console.log(`Filtered ${responseData.length - filteredRisks.length} risks without complete scoring or rejected status`);
      
      this.risks = filteredRisks;
      this.filteredRisks = [...filteredRisks]; // Initialize filtered risks with all risks that have completed scoring
      this.loading = false;
      
      // Initialize expanded sections
      this.initializeExpandedSections();
    },
    fetchUsers() {
      // Fetch reviewers filtered by RBAC permissions (ApproveRisk) for risk module
      axios.get(API_ENDPOINTS.USERS_FOR_REVIEWER_SELECTION, {
        params: {
          module: 'risk'
        }
      })
        .then(response => {
          console.log('User data received:', response.data);
          // Handle response format: should be an array
          if (Array.isArray(response.data)) {
            this.users = response.data;
          } else {
            this.users = [];
          }
          
          // Check if users were loaded correctly
          if (this.users && this.users.length > 0) {
            console.log(`Loaded ${this.users.length} users successfully`);
            console.log('Sample user data:', this.users[0]);
            
            // Debug each user's ID to ensure we're getting the right data
            this.users.forEach(user => {
              const userId = this.getUserId(user);
              console.log(`User: ${this.getUserName(user)}, ID: ${userId}, Type: ${typeof userId}`);
            });
          } else {
            console.warn('No users found or empty users array returned');
          }
        })
        .catch(error => {
          console.error('Error fetching users:', error);
          this.error = 'Failed to load user data. Please refresh the page or contact support.';
          this.users = [];
        });
    },
    filterRisks() {
      // Apply filters to all risks that already have complete scoring
      this.filteredRisks = this.risks.filter(risk => {
        // Search query filter
        const searchLower = this.searchQuery.toLowerCase();
        const matchesSearch = !this.searchQuery || 
          (risk.RiskInstanceId && risk.RiskInstanceId.toString().toLowerCase().includes(searchLower)) ||
          (risk.RiskTitle && risk.RiskTitle.toLowerCase().includes(searchLower)) ||
          (risk.Category && risk.Category.toLowerCase().includes(searchLower)) ||
          (risk.Criticality && risk.Criticality.toLowerCase().includes(searchLower)) ||
          (risk.RiskStatus && risk.RiskStatus.toLowerCase().includes(searchLower)) ||
          (risk.RiskDescription && risk.RiskDescription.toLowerCase().includes(searchLower));
        
        // Dropdown filters
        const matchesCriticality = !this.criticalityFilter || risk.Criticality === this.criticalityFilter;
        const matchesStatus = !this.statusFilter || risk.RiskStatus === this.statusFilter;
        
        // Assigned to filter
        const assignedTo = risk.RiskOwner && risk.RiskOwner !== 'System Owner' && risk.RiskOwner !== 'System User' ? 
          risk.RiskOwner : 'Yet to Start';
        const matchesAssignedTo = !this.assignedToFilter || assignedTo === this.assignedToFilter;
        
        // Reviewer filter
        const reviewer = risk.ReviewerName || 'Yet to Start';
        const matchesReviewer = !this.reviewerFilter || reviewer === this.reviewerFilter;
        
        return matchesSearch && matchesCriticality && matchesStatus && matchesAssignedTo && matchesReviewer;
      });
      
      console.log(`Applied filters: ${this.filteredRisks.length} risks displayed out of ${this.risks.length} total risks with completed scoring`);
    },
    initializeExpandedSections() {
      // Initialize all sections as expanded by default
      this.expandedSections = this.riskSections.map(() => true);
    },
    toggleSection(status) {
      this.expandedSections[status] = !this.expandedSections[status];
    },
    addTaskToSection(section) {
      // Implementation of adding a task to a section
      console.log('Adding task to section:', section);
    },
    openMitigationModal(taskOrId) {
      // Accept either a task object or an incidentId
      let incidentId = taskOrId;
      if (typeof taskOrId === 'object' && taskOrId !== null) {
        incidentId = taskOrId.incidentId;
      }
      let risk = null;
      for (const section of this.riskSections) {
        const task = section.tasks.find(task => task.incidentId === incidentId);
        if (task) {
          risk = task.originalRisk;
          break;
        }
      }
      
      if (!risk) {
        console.error('Risk not found for incidentId:', incidentId);
        return;
      }
      
      this.selectedRisk = risk;
      this.showMitigationModal = true;
      this.loadingMitigations = true;
      
      // Initialize user and reviewer so placeholder "Select User" / "Select Reviewer" shows when empty
      this.selectedUsers[risk.RiskInstanceId] = risk.UserId || '';
      this.selectedReviewers[risk.RiskInstanceId] = risk.ReviewerId || '';
      
      // First get the risk instance details to get mitigations
      axios.get(API_ENDPOINTS.RISK_INSTANCE(risk.RiskInstanceId))
        .then(response => {
          console.log('Risk instance data:', response.data);
          this.selectedRisk = response.data;
          
          // Check if there are mitigations in the risk instance data
          if (response.data.RiskMitigation) {
            let mitigations = [];
            const mitData = response.data.RiskMitigation;
            
            // Handle different mitigation data formats
            if (typeof mitData === 'string') {
              try {
                const parsed = JSON.parse(mitData);
                if (typeof parsed === 'object') {
                  // Convert object format to array format
                  Object.keys(parsed).forEach(key => {
                    mitigations.push({
                      description: parsed[key],
                      status: 'Not Started'
                    });
                  });
                }
              } catch (e) {
                // If not valid JSON, create a single step
                mitigations = [{
                  description: mitData,
                  status: 'Not Started'
                }];
              }
            } else if (typeof mitData === 'object' && !Array.isArray(mitData)) {
              // Convert object format to array format
              Object.keys(mitData).forEach(key => {
                mitigations.push({
                  description: mitData[key],
                  status: 'Not Started'
                });
              });
            } else if (Array.isArray(mitData)) {
              mitigations = mitData.map(step => ({
                description: typeof step === 'string' ? step : step.description,
                status: step.status || 'Not Started'
              }));
            }
            
            this.mitigationSteps = mitigations;
          } else {
            this.mitigationSteps = [];
          }
          
          this.loadingMitigations = false;
          
          // Set due date if it exists
          if (response.data.MitigationDueDate) {
            this.mitigationDueDate = response.data.MitigationDueDate;
          } else {
            // Set default due date to 7 days from today
            const date = new Date();
            date.setDate(date.getDate() + 7);
            const year = date.getFullYear();
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const day = String(date.getDate()).padStart(2, '0');
            this.mitigationDueDate = `${year}-${month}-${day}`;
          }
        })
        .catch(error => {
          console.error('Error fetching risk instance:', error);
          this.mitigationSteps = [];
          this.loadingMitigations = false;
          
          // Set default due date to 7 days from today
          const date = new Date();
          date.setDate(date.getDate() + 7);
          const year = date.getFullYear();
          const month = String(date.getMonth() + 1).padStart(2, '0');
          const day = String(date.getDate()).padStart(2, '0');
          this.mitigationDueDate = `${year}-${month}-${day}`;
        });
    },
    closeMitigationModal() {
      this.showMitigationModal = false;
      this.selectedRisk = {};
      this.mitigationSteps = [];
      this.newMitigationStep = '';
      this.mitigationDueDate = '';
      this.viewOnlyMitigationModal = false;
    },
    parseMitigations(data) {
      // Convert different mitigation formats to our standard format
      if (!data || data.length === 0) {
        return [];
      }
      
      // If it's already an array of objects with descriptions
      if (Array.isArray(data) && data[0] && data[0].description) {
        return data.map(item => ({
          description: item.description || item.title || '',
          status: item.status || 'Not Started'
        }));
      }
      
      // If it's an array of strings or simple objects
      if (Array.isArray(data)) {
        return data.map((item, index) => ({
          description: typeof item === 'string' ? item : (item.description || item.title || `Step ${index + 1}`),
          status: item.status || 'Not Started'
        }));
      }
      
      // If it's an object with numbered keys (e.g., {"1": "Step 1", "2": "Step 2"})
      if (typeof data === 'object' && !Array.isArray(data)) {
        const steps = [];
        Object.keys(data).forEach(key => {
          const value = data[key];
          steps.push({
            description: typeof value === 'string' ? value : (value.description || value.title || `Step ${key}`),
            status: value.status || 'Not Started'
          });
        });
        return steps;
      }
      
      // Fallback: if it's a string, create a single step
      if (typeof data === 'string') {
        return [{
          description: data,
          status: 'Not Started'
        }];
      }
      
      return [];
    },
    addMitigationStep() {
      if (!this.newMitigationStep.trim()) return;
      
      this.mitigationSteps.push({
        description: this.newMitigationStep,
        status: 'Not Started'
      });
      
      this.newMitigationStep = '';
    },
    removeMitigationStep(index) {
      this.mitigationSteps.splice(index, 1);
    },
    assignRiskWithMitigations() {
      const riskId = this.selectedRisk.RiskInstanceId;
      const userId = this.selectedUsers[riskId];
      const reviewerId = this.selectedReviewers[riskId];
      const dueDateValidationError = this.validateMitigationDueDate(this.mitigationDueDate, this.selectedRisk?.CreatedAt);
      if (dueDateValidationError) {
        this.$popup.warning(dueDateValidationError);
        return;
      }
      
      // Convert IDs to numbers to ensure proper format
      // Handle null or undefined values
      if (!userId) {
        this.$popup.warning('No user selected. Please select a user to assign this risk to.');
        this.sendPushNotification({
          title: 'Risk Assignment Warning',
          message: 'No user selected for risk assignment. Please select a user to assign this risk to.',
          category: 'risk',
          priority: 'medium'
        });
        this.loading = false;
        return;
      }
      
      const userIdNum = parseInt(userId, 10);
      const reviewerIdNum = parseInt(reviewerId, 10);
      
      console.log('Assigning risk with following IDs:', { 
        riskId, 
        userId: userIdNum, 
        reviewerId: reviewerIdNum 
      });
      
      if (!userIdNum || !reviewerIdNum || this.mitigationSteps.length === 0 || !this.mitigationDueDate) {
        // Show validation error
        if (!userIdNum) {
          this.$popup.warning('Please select a valid user to assign this risk to.');
          this.sendPushNotification({
            title: 'Risk Assignment Validation Error',
            message: 'Please select a valid user to assign this risk to.',
            category: 'risk',
            priority: 'medium'
          });
          return;
        }
        if (!reviewerIdNum) {
          this.$popup.warning('Please select a valid reviewer for this risk.');
          this.sendPushNotification({
            title: 'Risk Assignment Validation Error',
            message: 'Please select a valid reviewer for this risk.',
            category: 'risk',
            priority: 'medium'
          });
          return;
        }
        if (this.mitigationSteps.length === 0) {
          this.$popup.warning('Please add at least one mitigation step.');
          this.sendPushNotification({
            title: 'Risk Assignment Validation Error',
            message: 'Please add at least one mitigation step for risk assignment.',
            category: 'risk',
            priority: 'medium'
          });
          return;
        }
        if (!this.mitigationDueDate) {
          this.$popup.warning('Please select a due date for mitigation completion.');
          this.sendPushNotification({
            title: 'Risk Assignment Validation Error',
            message: 'Please select a due date for mitigation completion.',
            category: 'risk',
            priority: 'medium'
          });
          return;
        }
        return;
      }
      
      this.loading = true;
      
      // Convert mitigations to the expected JSON format
      // Format: {"1": "Description 1", "2": "Description 2", ...}
      const mitigationsJson = {};
      this.mitigationSteps.forEach((step, index) => {
        mitigationsJson[index + 1] = step.description;
      });
      
      console.log('Sending mitigation data:', mitigationsJson);
      console.log('User ID type:', typeof userIdNum, 'value:', userIdNum);
      console.log('Reviewer ID type:', typeof reviewerIdNum, 'value:', reviewerIdNum);
      
      // Log the exact payload we're sending to the API
      const assignPayload = {
        risk_id: parseInt(riskId, 10),
        UserId: userIdNum,
        mitigations: mitigationsJson,
        due_date: this.mitigationDueDate,
        risk_form_details: {} // Empty object instead of form details
      };
      console.log('Exact payload being sent to risk-assign API:', JSON.stringify(assignPayload));
      
      // First assign the risk to the user with mitigations
      axios.post(API_ENDPOINTS.RISK_ASSIGN, assignPayload, {
        // Add headers to ensure proper content type
        headers: {
          'Content-Type': 'application/json'
        }
      })
      .then(response => {
        console.log('Assignment response:', response.data);
        
        // Now assign the reviewer - explicitly set create_approval_record to false
        const reviewerPayload = {
          risk_id: parseInt(riskId, 10),
          ReviewerId: reviewerIdNum,
          UserId: userIdNum,
          mitigations: mitigationsJson,
          risk_form_details: {}, // Empty object instead of form details
          create_approval_record: false // Explicitly set to false to prevent creating version entry
        };
        console.log('Exact payload being sent to assign-reviewer API:', JSON.stringify(reviewerPayload));
        
        return axios.post(API_ENDPOINTS.ASSIGN_REVIEWER, reviewerPayload, {
          // Add headers to ensure proper content type
          headers: {
            'Content-Type': 'application/json'
          }
        });
      })
      .then(response => {
        console.log('Reviewer assignment response:', response.data);
        
        // Update the local risk data to show assignment
        const index = this.risks.findIndex(r => r.RiskInstanceId === riskId);
        if (index !== -1) {
          const assignedUser = this.users.find(u => this.getUserId(u) == userId);
          const assignedReviewer = this.users.find(u => this.getUserId(u) == reviewerId);
          
          // Make sure we have both user objects
          if (assignedUser && assignedReviewer) {
            this.risks[index].RiskOwner = this.getUserName(assignedUser);
            this.risks[index].UserId = userId;
            
            // Update both Reviewer and ReviewerName fields to ensure compatibility
            this.risks[index].ReviewerId = Number(reviewerId);
            this.risks[index].ReviewerName = this.getUserName(assignedReviewer);
            this.risks[index].Reviewer = this.getUserName(assignedReviewer);
            
            this.risks[index].RiskStatus = 'Assigned';
            this.risks[index].RiskMitigation = mitigationsJson;
            this.risks[index].MitigationDueDate = this.mitigationDueDate;
            this.risks[index].MitigationStatus = 'Yet to Start';
            this.risks[index].RiskFormDetails = {}; // Empty object instead of form details
          } else {
            console.error('Could not find assigned user or reviewer:', { userId, reviewerId });
          }
        }
        
        this.loading = false;
        this.closeMitigationModal();
        
        // Show success message
        this.$popup.success('Risk assigned successfully with mitigation steps and reviewer!');
        this.sendPushNotification({
          title: 'Risk Assignment Successful',
          message: `Risk "${this.selectedRisk.RiskTitle || 'Risk #' + this.selectedRisk.RiskInstanceId}" has been successfully assigned with mitigation steps and reviewer.`,
          category: 'risk',
          priority: 'high'
        });
      })
      .catch(error => {
        console.error('Error assigning risk:', error);
        this.loading = false;
        
        // Show more detailed error message
        let errorMessage = 'Failed to assign risk. ';
        
        if (error.response) {
          // The request was made and the server responded with a status code
          // that falls out of the range of 2xx
          errorMessage += `Server error: ${error.response.status} - ${error.response.data.message || error.response.data || 'Unknown error'}`;
          console.error('Error response data:', error.response.data);
        } else if (error.request) {
          // The request was made but no response was received
          errorMessage += 'No response received from server. Please check your network connection.';
        } else {
          // Something happened in setting up the request that triggered an Error
          errorMessage += error.message || 'Unknown error occurred';
        }
        
        this.$popup.error(errorMessage);
        this.sendPushNotification({
          title: 'Risk Assignment Failed',
          message: `Failed to assign risk "${this.selectedRisk.RiskTitle || 'Risk #' + this.selectedRisk.RiskInstanceId}": ${errorMessage}`,
          category: 'risk',
          priority: 'high'
        });
      });
    },
    getCriticalityClass(criticality) {
      if (!criticality) return '';
      const level = criticality.toLowerCase();
      if (level.includes('high')) return 'high';
      if (level.includes('medium')) return 'medium';
      if (level.includes('low')) return 'low';
      if (level.includes('critical')) return 'critical';
      return '';
    },
    getPriorityClass(priority) {
      if (!priority) return '';
      const level = priority.toLowerCase();
      if (level.includes('high')) return 'high';
      if (level.includes('medium')) return 'medium';
      if (level.includes('low')) return 'low';
      return '';
    },
    getStatusClass(status) {
      if (!status) return 'pending';
      const statusLower = status.toLowerCase();
      if (statusLower.includes('assigned') || statusLower.includes('in progress')) return 'in-progress';
      if (statusLower.includes('completed') || statusLower.includes('closed') || statusLower.includes('approved')) return 'completed';
      if (statusLower.includes('rejected')) return 'rejected';
      if (statusLower.includes('pending') || statusLower.includes('open') || statusLower.includes('yet to start')) return 'pending';
      return 'pending';
    },
    getRowClass(status) {
      if (!status) return '';
      const statusLower = status.toLowerCase();
      if (statusLower.includes('completed')) return 'row-approved';
      if (statusLower.includes('review')) return 'row-review';
      return '';
    },
    getTodayDate() {
      const today = new Date();
      const year = today.getFullYear();
      const month = String(today.getMonth() + 1).padStart(2, '0');
      const day = String(today.getDate()).padStart(2, '0');
      return `${year}-${month}-${day}`;
    },
    validateMitigationDueDate(rawDueDate, createdAtRaw) {
      if (!rawDueDate) return 'Please select a due date for mitigation completion.';
      const dueDate = new Date(rawDueDate);
      if (Number.isNaN(dueDate.getTime())) return 'Due date must be in YYYY-MM-DD format.';

      const createdAt = createdAtRaw ? new Date(createdAtRaw) : new Date();
      const baseline = Number.isNaN(createdAt.getTime()) ? new Date() : createdAt;
      baseline.setHours(0, 0, 0, 0);
      dueDate.setHours(0, 0, 0, 0);

      if (dueDate < baseline) return 'Due date cannot be earlier than risk creation date.';

      const maxAllowed = new Date(baseline);
      maxAllowed.setFullYear(maxAllowed.getFullYear() + 10);
      if (dueDate > maxAllowed) return 'Due date cannot be more than 10 years from creation date.';

      return null;
    },
    isRiskRejected(risk) {
      // Helper method to check if a risk is rejected
      // Used in filtering risks for the resolution screen
      if (!risk) return false;
      
      const appetite = (risk.Appetite || '').toLowerCase();
      const status = (risk.RiskStatus || '').toLowerCase();
      
      return appetite === 'no' || status === 'rejected';
    },
    hasCompletedScoring(risk) {
      // Helper method to check if a risk has completed scoring
      // Used to determine if a risk should be displayed in the resolution screen
      if (!risk) return false;
      
      return (
        risk.RiskLikelihood !== undefined && 
        risk.RiskLikelihood !== null && 
        risk.RiskImpact !== undefined && 
        risk.RiskImpact !== null && 
        risk.RiskExposureRating !== undefined && 
        risk.RiskExposureRating !== null
      );
    },
    
    // Helper methods to handle different user data structures
    getUserId(user) {
      // Handle different possible user object structures
      if (!user) return '';
      
      // Django Users model structure
      if (user.UserId !== undefined) return parseInt(user.UserId, 10);
      
      // Custom users API structure
      if (user.user_id !== undefined) return parseInt(user.user_id, 10);
      
      // Django auth User model structure
      if (user.id !== undefined) return parseInt(user.id, 10);
      
      // Fallback - try to parse any available ID field
      const id = user.id || user.UserId || user.user_id || '';
      return id ? parseInt(id, 10) : '';
    },
    
    getUserName(user) {
      // Handle different possible user object structures
      if (!user) return 'Unknown User';
      
      // Django Users model structure
      if (user.UserName) {
        return user.UserName + (user.email ? ` (${user.email})` : '');
      }
      
      // Custom users API structure
      if (user.user_name) {
        let displayName = user.user_name;
        if (user.department || user.designation) {
          displayName += ' (';
          if (user.department) displayName += user.department;
          if (user.department && user.designation) displayName += ', ';
          if (user.designation) displayName += user.designation;
          displayName += ')';
        }
        return displayName;
      }
      
      // Django auth User model structure
      if (user.username) {
        return user.first_name && user.last_name 
          ? `${user.first_name} ${user.last_name} (${user.username})` 
          : user.username;
      }
      
      // Fallback
      return user.UserName || user.user_name || user.username || user.email || 'User ' + this.getUserId(user);
    },
    navigateTo(screen) {
      this.activeView = screen;

      // Navigate to the appropriate screen
      switch(screen) {
        case 'resolution':
          // Already on resolution page
          break;
        case 'workflow':
          this.$router.push('/risk/workflow');
          break;
      }
    },
    // Custom dropdown methods
    toggleDropdown(dropdownName) {
      // Close all other dropdowns
      Object.keys(this.openDropdowns).forEach(key => {
        if (key !== dropdownName) {
          this.openDropdowns[key] = false;
        }
      });
      // Toggle the clicked dropdown
      this.openDropdowns[dropdownName] = !this.openDropdowns[dropdownName];
      // Reset search query when opening dropdown
      if (this.openDropdowns[dropdownName]) {
        this.searchQueries[dropdownName] = '';
      }
    },
    selectCriticality(value) {
      this.criticalityFilter = value;
      this.openDropdowns.criticality = false;
      this.filterRisks();
    },
    selectStatus(value) {
      this.statusFilter = value;
      this.openDropdowns.status = false;
      this.filterRisks();
    },
    selectAssignedTo(value) {
      this.assignedToFilter = value;
      this.openDropdowns.assignedTo = false;
      this.filterRisks();
    },
    selectReviewer(value) {
      this.reviewerFilter = value;
      this.openDropdowns.reviewer = false;
      this.filterRisks();
    },
    selectAssignTo(userId) {
      this.selectedUsers[this.selectedRisk.RiskInstanceId] = userId;
      this.openDropdowns.assignTo = false;
    },
    selectReviewerAssign(userId) {
      this.selectedReviewers[this.selectedRisk.RiskInstanceId] = userId;
      this.openDropdowns.reviewerAssign = false;
    },
    onAssignToSelect(val) {
      if (this.selectedRisk && this.selectedRisk.RiskInstanceId != null) {
        this.selectedUsers[this.selectedRisk.RiskInstanceId] = val;
      }
    },
    onReviewerSelect(val) {
      if (this.selectedRisk && this.selectedRisk.RiskInstanceId != null) {
        this.selectedReviewers[this.selectedRisk.RiskInstanceId] = val;
      }
    },
    getCriticalityLabel() {
      return this.criticalityFilter || 'All Criticality';
    },
    getStatusLabel() {
      return this.statusFilter || 'All Status';
    },
    getAssignedToLabel() {
      return this.assignedToFilter || 'All Assigned To';
    },
    getReviewerLabel() {
      return this.reviewerFilter || 'All Reviewers';
    },
    clearCriticality() {
      this.criticalityFilter = '';
      this.filterRisks();
    },
    clearStatus() {
      this.statusFilter = '';
      this.filterRisks();
    },
    clearAssignedTo() {
      this.assignedToFilter = '';
      this.filterRisks();
    },
    clearReviewer() {
      this.reviewerFilter = '';
      this.filterRisks();
    },
    getAssignToLabel() {
      if (!this.selectedUsers[this.selectedRisk.RiskInstanceId]) {
        return 'Select User';
      }
      const user = this.users.find(u => this.getUserId(u) === this.selectedUsers[this.selectedRisk.RiskInstanceId]);
      return user ? `${this.getUserName(user)} (ID: ${this.getUserId(user)})` : 'Select User';
    },
    getReviewerAssignLabel() {
      if (!this.selectedReviewers[this.selectedRisk.RiskInstanceId]) {
        return 'Select Reviewer';
      }
      const user = this.users.find(u => this.getUserId(u) === this.selectedReviewers[this.selectedRisk.RiskInstanceId]);
      return user ? `${this.getUserName(user)} (ID: ${this.getUserId(user)})` : 'Select Reviewer';
    },
    // Filtered options for dropdowns
    filteredCriticalities() {
      if (!this.searchQueries.criticality) return this.uniqueCriticalities;
      const query = this.searchQueries.criticality.toLowerCase();
      return this.uniqueCriticalities.filter(c => c.toLowerCase().includes(query));
    },
    filteredStatuses() {
      if (!this.searchQueries.status) return this.uniqueStatuses;
      const query = this.searchQueries.status.toLowerCase();
      return this.uniqueStatuses.filter(s => s.toLowerCase().includes(query));
    },
    filteredAssignedUsers() {
      if (!this.searchQueries.assignedTo) return this.uniqueAssignedUsers;
      const query = this.searchQueries.assignedTo.toLowerCase();
      return this.uniqueAssignedUsers.filter(u => u.toLowerCase().includes(query));
    },
    filteredReviewers() {
      if (!this.searchQueries.reviewer) return this.uniqueReviewers;
      const query = this.searchQueries.reviewer.toLowerCase();
      return this.uniqueReviewers.filter(r => r.toLowerCase().includes(query));
    },
    filteredAssignToUsers() {
      if (!this.searchQueries.assignTo) return this.users;
      const query = this.searchQueries.assignTo.toLowerCase();
      return this.users.filter(u => this.getUserName(u).toLowerCase().includes(query));
    },
    filteredReviewerAssignUsers() {
      if (!this.searchQueries.reviewerAssign) return this.users;
      const query = this.searchQueries.reviewerAssign.toLowerCase();
      return this.users.filter(u => this.getUserName(u).toLowerCase().includes(query));
    },
    handleClickOutside(event) {
      if (!event.target.closest('.dropdown')) {
        Object.keys(this.openDropdowns).forEach(key => {
          this.openDropdowns[key] = false;
        });
      }
    }
  },
  beforeUnmount() {
    document.removeEventListener('click', this.handleClickOutside);
  }
}
</script>

<style>
/* Import centralized search bar styles */
@import '@/assets/css/main.css';
@import '@/assets/css/dropdown.css';
@import '@/assets/css/form.css';
</style>

<style scoped>
/* Import the CSS file */
@import './RiskResolution.css';

/* Force white background for the container */
.risk-resolution-container {
  background:white !important;
}

/* Force table header size - highest specificity */
.risk-resolution-collapsible-container .task-table th,
.risk-resolution-collapsible-container .task-table th *,
.risk-resolution-collapsible-container .task-table th div,
.risk-resolution-collapsible-container .task-table th span {
  font-size: 12px !important;
  font-weight: 600 !important;
  color: #495057 !important;
  background: white !important;
  background-color: white !important;
  padding: 8px 12px !important;
  margin: 0px !important;
  line-height: normal !important;
  border: none !important;
  box-shadow: none !important;
}

/* Add additional styles for the section title */
.section-title {
  margin: 20px 0;
  color: #333;
  font-size: 1.8rem;
  font-weight: 600;
  text-align: center;
}

/* Layout-only wrapper tweaks; button look comes from main.css (.toggle-group/.toggle-button) */
.risk-resolution-toggle-group {
  margin: 10px auto 20px auto;
}

.risk-resolution-data-source {
  margin: 0 0 12px 0;
  font-size: 0.85rem;
  color: #2563eb;
  font-weight: 600;
}

/* Style for selected user info */
.risk-resolution-selected-user-info {
  margin-top: 5px;
  font-size: 0.85rem;
  color: #666;
  padding: 3px 8px;
  border-radius: 4px;
 
}
</style> 