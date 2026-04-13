<template>
  <div class="auditor-dashboard-container">
    <!-- Header Title -->
    <div class="dashboard-header-title">
      Audit Dashboard
    </div>
    
    <div v-if="loading" class="loading-indicator">Loading audits...</div>
    <div v-if="error" class="error-message">
      {{ error }}
      <button @click="retryLoading" class="retry-btn">Retry</button>
    </div>
    
    <DynamicTable
      v-if="!loading && audits.length > 0"
      :title="'Audits'"
      :data="audits"
      :columns="tableColumns"
      :filters="tableFilters"
      :actionButtons="tableActionButtons"
      :showActions="true"
      :showPagination="true"
      :defaultPageSize="10"
      @button-click="handleButtonClick"
      @filter-change="handleFilterChange"
      @open-column-chooser="toggleColumnEditor"
    >
      <template #cell-status="{ row }">
        <div 
          class="status-indicator" 
          :class="getStatusClass(row.status)"
          @click="onStatusButtonClick(row)"
        >
          <span class="status-dot"></span>
          <span class="status-text">{{ getStatusDisplayText(row) }}</span>
        </div>
      </template>
      <template #cell-business_unit="{ row }">
        <div class="cell-content-wrapper">{{ row.business_unit || 'Not Specified' }}</div>
      </template>
      <template #actions="{ row }">
        <div class="action-buttons">
          <CustomButton
            :config="{
              name: '',
              icon: 'PhFileText',
              className: 'report-btn icon-only',
              iconOnly: true
            }"
            @click="showReports(row)"
            :title="'Reports'"
          />
          <CustomButton
            v-if="row.status === 'Completed'"
            :config="{
              name: '',
              icon: 'PhClock',
              className: 'view-versions-btn icon-only',
              iconOnly: true
            }"
            @click="viewAuditVersions(row)"
            :title="'Versions'  "
          />
          </div>
      </template>
    </DynamicTable>

    <div v-else-if="!loading && audits.length === 0" class="no-data-message">
      No audits found. You don't have any audits assigned to you.
    </div>


    <!-- Popup Modal -->
    <div v-if="showPopup" class="audit-popup-overlay">
      <div class="audit-popup-modal">
        <button class="popup-close" @click="closePopup">&times;</button>
        <div class="popup-header">
          <h2 class="popup-title">{{ popupData.framework }}</h2>
        </div>
        <div class="popup-content">
          <div class="popup-policy">
            <h3 class="popup-policy-name">{{ popupData.policy }}</h3>
            <div v-if="popupData.subpolicy" class="popup-subpolicy">
              <h4>Subpolicy: {{ popupData.subpolicy }}</h4>
            </div>

            <!-- Loading State -->
            <div v-if="popupData.loadingCompliances" class="popup-loading">
              <i class="fas fa-spinner fa-spin"></i> Loading compliance data...
            </div>

            <!-- Error State -->
            <div v-else-if="popupData.complianceError" class="popup-error">
              <i class="fas fa-exclamation-circle"></i> {{ popupData.complianceError }}
              <button @click="retryLoadingCompliances" class="retry-btn">Retry</button>
            </div>

            <!-- Compliance List -->
            <div v-else class="popup-compliance-list">
              <div v-for="compliance in popupData.compliances" 
                   :key="compliance.finding_id" 
                   class="popup-compliance-item">
                <div class="compliance-header">
                  <h4>{{ compliance.compliance_name }}</h4>
                  <span class="compliance-id">ID: {{ compliance.compliance_id }}</span>
                </div>
                
                <div class="compliance-description">
                  {{ compliance.compliance_description }}
                </div>

                <div class="compliance-controls">
                  <div class="compliance-check">
                    <input 
                      type="checkbox" 
                      :checked="compliance.check === '1'"
                      @change="updateComplianceCheck(compliance.finding_id, $event)"
                    >
                    <label>Compliant</label>
                  </div>

                  <div class="compliance-evidence">
                    <label>Evidence:</label>
                    <textarea 
                      v-model="compliance.evidence"
                      @input="updateComplianceEvidence(compliance.finding_id, $event)"
                      placeholder="Enter evidence here..."
                    ></textarea>
                  </div>

                  <div class="compliance-comments">
                    <label>Comments:</label>
                    <textarea 
                      v-model="compliance.comments"
                      @input="updateComplianceComments(compliance.finding_id, $event)"
                      placeholder="Enter comments here..."
                    ></textarea>
                  </div>

                  <div class="compliance-major-minor" v-if="!compliance.check">
                    <label>Finding Type:</label>
                    <select 
                      v-model="compliance.major_minor"
                      @change="updateComplianceMajorMinor(compliance.finding_id, $event)"
                    >
                      <option value="">Select Type</option>
                      <option value="Major">Major</option>
                      <option value="Minor">Minor</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="popup-actions">
          <button class="btn btn-submit" @click="saveCompliances">Save Changes</button>
          <button class="btn-cancel" @click="closePopup">Cancel</button>
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
        </div>

        <div class="incident-column-editor-list">
          <div
            v-for="column in filteredColumnDefinitions"
            :key="column.key"
            class="incident-column-editor-item"
          >
            <label class="incident-column-editor-label">
              <input
                type="checkbox"
                :checked="isColumnVisible(column.key)"
                @change="toggleColumnVisibility(column.key)"
                class="incident-column-editor-checkbox"
              />
              <span class="incident-column-editor-text">{{ column.label }}</span>
            </label>
          </div>
        </div>

        <div class="incident-column-editor-footer">
          <button class="incident-column-done-btn" @click="toggleColumnEditor">Done</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script>
import './AuditorDashboard.css';
import auditorDataService from '@/services/auditorService';
import DynamicTable from '../DynamicTable.vue';
import CustomButton from '../CustomButton.vue';
import apiService from '@/services/apiService';
import { AccessUtils } from '@/utils/accessUtils';
import { API_ENDPOINTS } from '@/config/api.js';

export default {
  name: 'AuditorDashboard',
  components: {
    DynamicTable,
    CustomButton
  },
  data() {
    return {
      auditStatuses: [],
      loading: true,
      error: '',
      audits: [],
      showPopup: false,
      popupData: {
        framework: '',
        policy: '',
        subpolicy: '',
        audit_id: null,
        compliances: [],
        loadingCompliances: false,
        complianceError: null
      },
      frameworks: [],
      policies: [],
      businessUnits: [],
      statusUpdating: false,
      // Column chooser properties
      showColumnEditor: false,
      columnSearchQuery: '',
      visibleColumnKeys: ['audit_id', 'framework', 'policy', 'subpolicy', 'date', 'business_unit', 'auditType', 'status'],
      columnDefinitions: [
        { key: 'audit_id', label: 'Audit ID', defaultVisible: true },
        { key: 'title', label: 'Title', defaultVisible: false },
        { key: 'framework', label: 'Framework', defaultVisible: true },
        { key: 'policy', label: 'Policy', defaultVisible: true },
        { key: 'subpolicy', label: 'Subpolicy', defaultVisible: true },
        { key: 'date', label: 'Due Date', defaultVisible: true },
        { key: 'business_unit', label: 'Business Unit', defaultVisible: true },
        { key: 'auditType', label: 'Audit Type', defaultVisible: true },
        { key: 'status', label: 'Status', defaultVisible: true },
        { key: 'scope', label: 'Scope', defaultVisible: false },
        { key: 'objective', label: 'Objective', defaultVisible: false },
        { key: 'role', label: 'Role', defaultVisible: false },
        { key: 'responsibility', label: 'Responsibility', defaultVisible: false },
        { key: 'assignee', label: 'Assignee', defaultVisible: false },
        { key: 'frequency', label: 'Frequency', defaultVisible: false },
        { key: 'completion_date', label: 'Completion Date', defaultVisible: false },
        { key: 'review_status', label: 'Review Status', defaultVisible: false },
        { key: 'reviewer_comments', label: 'Reviewer Comments', defaultVisible: false },
        { key: 'evidence', label: 'Evidence', defaultVisible: false },
        { key: 'comments', label: 'Comments', defaultVisible: false },
        { key: 'assigned_date', label: 'Assigned Date', defaultVisible: false },
        { key: 'review_start_date', label: 'Review Start Date', defaultVisible: false },
        { key: 'review_date', label: 'Review Date', defaultVisible: false }
      ]
    }
  },
  computed: {
    tableColumns() {
      const allColumns = [
        { key: 'audit_id', label: 'Audit ID', sortable: true, width: '100px', resizable: true },
        { key: 'title', label: 'Title', sortable: true, width: '200px', resizable: true },
        { key: 'framework', label: 'Framework', sortable: true, width: '150px', resizable: true },
        { key: 'policy', label: 'Policy', sortable: true, width: '180px', resizable: true },
        { key: 'subpolicy', label: 'Subpolicy', sortable: true, width: '180px', resizable: true },
        { key: 'date', label: 'Due Date', sortable: true, width: '120px', resizable: true },
        { key: 'business_unit', label: 'Business Unit', sortable: true, width: '150px', resizable: true, slot: true },
        { key: 'auditType', label: 'Audit Type', sortable: true, width: '120px', resizable: true },
        { key: 'status', label: 'Status', sortable: true, width: '140px', resizable: true, slot: 'cell-status' },
        { key: 'scope', label: 'Scope', sortable: true, width: '200px', resizable: true },
        { key: 'objective', label: 'Objective', sortable: true, width: '200px', resizable: true },
        { key: 'role', label: 'Role', sortable: true, width: '120px', resizable: true },
        { key: 'responsibility', label: 'Responsibility', sortable: true, width: '180px', resizable: true },
        { key: 'assignee', label: 'Assignee', sortable: true, width: '140px', resizable: true },
        { key: 'frequency', label: 'Frequency', sortable: true, width: '100px', resizable: true },
        { key: 'completion_date', label: 'Completion Date', sortable: true, width: '140px', resizable: true },
        { key: 'review_status', label: 'Review Status', sortable: true, width: '130px', resizable: true },
        { key: 'reviewer_comments', label: 'Reviewer Comments', sortable: true, width: '200px', resizable: true },
        { key: 'evidence', label: 'Evidence', sortable: true, width: '150px', resizable: true },
        { key: 'comments', label: 'Comments', sortable: true, width: '200px', resizable: true },
        { key: 'assigned_date', label: 'Assigned Date', sortable: true, width: '140px', resizable: true },
        { key: 'review_start_date', label: 'Review Start Date', sortable: true, width: '150px', resizable: true },
        { key: 'review_date', label: 'Review Date', sortable: true, width: '130px', resizable: true }
      ];

      // Filter to only show visible columns
      return allColumns.filter(col => this.visibleColumnKeys.includes(col.key));
    },
    filteredColumnDefinitions() {
      if (!this.columnSearchQuery) {
        return this.columnDefinitions;
      }
      const query = this.columnSearchQuery.toLowerCase();
      return this.columnDefinitions.filter(col =>
        col.label.toLowerCase().includes(query) ||
        col.key.toLowerCase().includes(query)
      );
    },
    tableFilters() {
      return [];
    },
    tableActionButtons() {
      return [];
    }
  },
  created() {
    this.fetchAudits()
    this.fetchBusinessUnits()
  },
  methods: {
    retryLoading() {
      this.fetchAudits()
    },
    
    async fetchBusinessUnits() {
      try {
        console.log('🔍 [AuditorDashboard] Checking for cached business units data...');
        
        // Try to get data from cache first
        if (auditorDataService.hasBusinessUnitsCache()) {
          console.log('✅ [AuditorDashboard] Using cached business units data');
          this.businessUnits = auditorDataService.getData('businessUnits') || [];
          console.log(`[AuditorDashboard] Loaded ${this.businessUnits.length} business units from cache`);
        } else {
          // Fallback: Fetch from API if cache is empty
          console.log('⚠️ [AuditorDashboard] No cached business units found, fetching from API...');
          const data = await apiService.get(API_ENDPOINTS.BUSINESS_UNITS);
          if (data) {
            this.businessUnits = Array.isArray(data) ? data : (data.business_units || []);
            
            // Update cache
            auditorDataService.setData('businessUnits', this.businessUnits);
            console.log('ℹ️ [AuditorDashboard] Business units cache updated after direct API fetch');
          }
        }
      } catch (error) {
        console.error('Error fetching business units:', error);
        // If API call fails, we'll use the business units from the audit data
      }
    },
    async fetchAudits() {
      this.loading = true;
      this.error = '';
      
      console.log('🔍 [AuditorDashboard] Checking for cached audits data...');
      
      // Check if prefetch was never started (user came directly to this page)
      if (!window.auditorDataFetchPromise && !auditorDataService.hasAuditsCache()) {
        console.log('🚀 [AuditorDashboard] Starting prefetch now (user came directly to this page)...');
        window.auditorDataFetchPromise = auditorDataService.fetchAllAuditorData();
      }
      
      // Wait for prefetch if it's running
      if (window.auditorDataFetchPromise) {
        console.log('⏳ [AuditorDashboard] Waiting for prefetch to complete...');
        try {
          await window.auditorDataFetchPromise;
          console.log('✅ [AuditorDashboard] Prefetch completed');
        } catch (error) {
          console.warn('⚠️ [AuditorDashboard] Prefetch failed, will fetch directly');
        }
      }
      
      // Try to get data from cache first
      if (auditorDataService.hasAuditsCache()) {
        console.log('✅ [AuditorDashboard] Using cached audits data');
        const cachedAudits = auditorDataService.getData('audits') || [];
        console.log(`[AuditorDashboard] Loaded ${cachedAudits.length} audits from cache (prefetched on Home page)`);
        
        // Process cached data
        const response = { data: { audits: cachedAudits } };
        this.processAuditsData(response);
      } else {
        // Fallback: Fetch from API if cache is empty
        console.log('⚠️ [AuditorDashboard] No cached data found, fetching from API...');
        apiService.get(API_ENDPOINTS.AUDIT_MY_AUDITS)
          .then(data => {
            console.log('[AuditorDashboard] Audit data received from API:', data);
            
            // Update cache for subsequent loads
            if (data && data.audits) {
              auditorDataService.setData('audits', data.audits);
              console.log('ℹ️ [AuditorDashboard] Cache updated after direct API fetch');
            }
            
            this.processAuditsData({ data });
          })
          .catch(error => {
            console.error('[AuditorDashboard] Error fetching audits:', error);
            this.error = 'Failed to load audits';
            this.loading = false;
          });
      }
    },
    
    processAuditsData(response) {
      console.log('Processing audit data:', response.data);
          
          // Transform the data for our component
          if (response.data && response.data.audits) {
            this.audits = response.data.audits.map(audit => {
              // Get reports field (try both cases and log for debugging)
              const reportsField = audit.Reports || audit.reports;
              console.log(`Audit ${audit.audit_id} raw reports field:`, audit.Reports);
              console.log(`Audit ${audit.audit_id} processed reports field:`, reportsField);
              
              // Check if reports are available
              const hasReports = Boolean(reportsField && reportsField !== 'null' && reportsField !== '[]' && reportsField !== '{}');
              console.log(`Audit ${audit.audit_id} has reports:`, hasReports);
              
              // Normalize the status value (case sensitivity, etc.)
              let normalizedStatus = audit.status || 'Yet to Start';
              if (normalizedStatus.toLowerCase() === 'completed') {
                normalizedStatus = 'Completed';
              } else if (normalizedStatus.toLowerCase() === 'work in progress') {
                normalizedStatus = 'Work In Progress';
              } else if (normalizedStatus.toLowerCase() === 'under review') {
                normalizedStatus = 'Under review';
              } else if (normalizedStatus.toLowerCase() === 'yet to start') {
                normalizedStatus = 'Yet to Start';
              }
              
              console.log(`Audit ${audit.audit_id} original status: "${audit.status}", normalized: "${normalizedStatus}"`);
              
              return {
                audit_id: audit.audit_id,
                title: audit.title || audit.Title || 'N/A',
                framework: audit.framework || 'N/A',
                policy: audit.policy || 'N/A',
                subpolicy: audit.subpolicy || audit.SubPolicy || 'N/A',
                date: audit.duedate || audit.DueDate || 'N/A',
                business_unit: audit.business_unit || audit.BusinessUnit || 'Not Specified',
                auditType: audit.audit_type_text || audit.audit_type || audit.AuditType || 'N/A',
                status: normalizedStatus,
                scope: audit.scope || audit.Scope || '',
                objective: audit.objective || audit.Objective || '',
                role: audit.role || audit.Role || '',
                responsibility: audit.responsibility || audit.Responsibility || '',
                assignee: audit.assignee || audit.Assignee || 'N/A',
                frequency: audit.frequency || audit.Frequency || '',
                completion_date: audit.completion_date || audit.CompletionDate || '',
                review_status: audit.review_status || audit.ReviewStatus || '',
                reviewer_comments: audit.reviewer_comments || audit.ReviewerComments || '',
                evidence: audit.evidence || audit.Evidence || '',
                comments: audit.comments || audit.Comments || '',
                assigned_date: audit.assigned_date || audit.AssignedDate || '',
                review_start_date: audit.review_start_date || audit.ReviewStartDate || '',
                review_date: audit.review_date || audit.ReviewDate || '',
                user: audit.assignee || 'N/A',
                reviewer: audit.reviewer || 'N/A',
                Reports: reportsField, // Store reports field
                report_available: hasReports // Set report availability
              };
            });

            // Initialize auditStatuses with the initial statuses from audits
            this.auditStatuses = this.audits.map(a => a.status);
            
            // Extract unique frameworks, policies, and business units for dropdown
            this.frameworks = [...new Set(this.audits.map(a => a.framework).filter(Boolean))];
            this.policies = [...new Set(this.audits.map(a => a.policy).filter(Boolean))];
            this.businessUnits = [...new Set(this.audits.map(a => a.business_unit).filter(bu => bu && bu !== 'Not Specified'))];
          } else {
            this.audits = [];
            this.auditStatuses = [];
          }
          
          this.loading = false;
    },
    
    handleButtonClick(button) {
      // Handle button clicks from the table
      console.log('Button clicked:', button);
    },
    
    handleFilterChange(filterData) {
      // Handle filter changes from the table
      console.log('Filter changed:', filterData);
    },
    
    async openPopup(idx) {
      const audit = this.audits[idx];
      
      // Don't proceed if the audit is in "Under review" or "Completed" status
      if (audit.status === 'Under review' || audit.status === 'Completed') {
        return;
      }

      // For AI audits, don't allow editing - they are done by AI
      const isAIAudit = (audit.auditType || '').toString().toUpperCase() === 'A' || 
                        (audit.auditType || '').toString().toUpperCase() === 'AI';
      
      if (isAIAudit) {
        // AI audits cannot be edited - redirect to AI audit document upload page instead
        this.$router.push(`/ai-audit/${audit.audit_id}/upload`);
        return;
      }
      
      // Navigate to TaskView for Edit Audit
      if (audit.status === 'Work In Progress') {
        this.$router.push(`/audit/${audit.audit_id}/tasks`);
        return;
      }

      // For other statuses, show the popup
      this.popupData = {
        framework: audit.framework,
        policy: audit.policy,
        subpolicy: audit.subpolicy,
        audit_id: audit.audit_id,
        compliances: [],
        loadingCompliances: true,
        complianceError: null
      };
      
      this.showPopup = true;

      try {
        // Fetch compliance data
        const data = await apiService.get(API_ENDPOINTS.AUDIT_COMPLIANCES(audit.audit_id));
        this.popupData = {
          ...audit,
          compliances: data.compliances || data || []
        };
      } catch (error) {
        console.error('Error fetching compliance data:', error);
        // Handle access denied errors
        if (AccessUtils.handleApiError(error, 'audit compliance access')) {
          this.popupData.complianceError = 'Access denied';
        } else {
          this.popupData.complianceError = 'Failed to load compliance data. Please try again.';
        }
      } finally {
        this.popupData.loadingCompliances = false;
      }
    },
    
    startAudit(idx) {
      const audit = this.audits[idx];
      
      // Update status from "Yet to Start" to "Work In Progress"
      this.updateAuditStatus(idx, 'Work In Progress');
      
      // Navigate to the TaskView component with the audit ID
      this.$router.push(`/audit/${audit.audit_id}/tasks`);
    },
    
    updateAuditStatus(idx, newStatus) {
      if (this.statusUpdating) return;
      this.statusUpdating = true;
      
      const auditId = this.audits[idx].audit_id;
      const oldStatus = this.audits[idx].status;
      
      // Optimistically update UI
      this.audits[idx].status = newStatus;
      
      // Update the server - fix by passing status in correct format
      (async () => {
        try {
          // Use apiService.post for status updates
          const data = await apiService.post(API_ENDPOINTS.AUDIT_STATUS(auditId), { status: newStatus })
          
          if (data && data.success) {
            this.$popup.success(`Audit status updated to ${newStatus}`);
            await this.fetchAudits();
          } else {
            // If post failed, try put as fallback (legacy behavior)
            const putData = await apiService.put(API_ENDPOINTS.AUDIT_STATUS(auditId), { status: newStatus })
            if (putData && putData.success) {
              this.$popup.success(`Audit status updated to ${newStatus}`);
              await this.fetchAudits();
            } else {
              this.$popup.error('Failed to update audit status');
            }
          }
        } catch (error) {
          console.error('Error updating audit status:', error);
          this.$popup.error('Error updating audit status');
          // Revert to old status on error
          this.audits[idx].status = oldStatus;
        } finally {
          this.statusUpdating = false;
        }
      })();
    },
    
    closePopup() {
      this.showPopup = false
    },
    
    addCompliance(subIdx) {
      this.popupData.subpolicies[subIdx].compliances.push({ checked: false, comment: '', commentChecked: false })
    },
    
    submitPopup() {
      // Here you would send the compliance updates to the backend
      // For example:
      // api.updateComplianceItems(this.popupData.audit_id, transformedComplianceData)
      //   .then(() => {
      //     // Refresh data after update
      //     this.fetchAudits();
      //   })
      
      console.log('Submitting compliance updates:', this.popupData)
      this.closePopup()
      
      // For now, let's just update the local progress to show something changed
      const auditIndex = this.audits.findIndex(a => a.audit_id === this.popupData.audit_id)
      if (auditIndex >= 0) {
        // Simulate progress increase
        this.audits[auditIndex].progress = Math.min(100, this.audits[auditIndex].progress + 20)
        
        // If progress is 100%, change status to Completed
        if (this.audits[auditIndex].progress === 100) {
          this.updateAuditStatus(auditIndex, 'Completed');
        }
      }
    },
    
    
    formatDate(dateString) {
      if (!dateString) return 'N/A';
      const date = new Date(dateString);
      return date.toLocaleDateString();
    },
    

    async showReports(audit) {
      // Prefer opening the latest available report version (S3 link)
      const auditId = audit.audit_id;
      console.log(`🔍 Attempting to show reports for audit ${auditId}`);
      
      this.latestAuditVersionS3Link = '';
      
      try {
        const data = await apiService.get(API_ENDPOINTS.AUDIT_REPORT_VERSIONS(auditId))
        const versions = data.versions || data || [];
        
        if (versions.length > 0) {
          // Get the most recent version
          const latestVersion = versions[0].version || versions[0];
          const s3Data = await apiService.get(API_ENDPOINTS.AUDIT_REPORT_VERSION_S3_LINK(auditId, latestVersion));
          
          if (s3Data && s3Data.s3_link) {
            this.latestAuditVersionS3Link = s3Data.s3_link;
          }
        }
      } catch (error) {
        console.error('Error fetching audit versions:', error);
      }
      
      if (this.latestAuditVersionS3Link) {
        window.open(this.latestAuditVersionS3Link, '_blank', 'noopener,noreferrer');
      } else {
        // Fallback: navigate to reports page which will render current report state
        console.log(`🔄 Falling back to reports view for audit ${auditId}`);
        localStorage.setItem(`audit_${auditId}_data`, JSON.stringify(audit));
        this.$router.push(`/audit-reports/${auditId}`);
      }
    },


    // Add sendPushNotification method
    async sendPushNotification(notificationData) {
      try {
        await apiService.post(API_ENDPOINTS.PUSH_NOTIFICATION, notificationData);
        console.log('Push notification sent successfully');
      } catch (error) {
        console.error('Error sending push notification:', error);
      }
    },

    // Add a helper method to show success messages
    showSuccessMessage(message) {
      // If you have a toast/notification system, use it here
      // Otherwise use a simple alert
      this.$popup.success(message);
      // Send push notification
      this.sendPushNotification({
        title: 'Audit Notification',
        message: message,
        category: 'audit',
        priority: 'high',
        user_id: 'default_user'
      });
    },
    
    // Method to view all versions of an audit
    viewAuditVersions(audit) {
      // Store audit data in localStorage for the versions view to access
      localStorage.setItem(`audit_${audit.audit_id}_data`, JSON.stringify(audit));
      
      // Navigate to the versions view
      this.$router.push(`/audit-versions/${audit.audit_id}`);
    },
    
    

    
    


    async retryLoadingCompliances() {
      this.popupData.loadingCompliances = true;
      this.popupData.complianceError = null;
      
      try {
        const data = await apiService.get(API_ENDPOINTS.AUDIT_COMPLIANCES(this.popupData.audit_id));
        this.popupData.compliances = data.compliances || data || [];
      } catch (error) {
        console.error('Error fetching compliance data:', error);
        this.popupData.complianceError = 'Failed to load compliance data. Please try again.';
      } finally {
        this.popupData.loadingCompliances = false;
      }
    },

    updateComplianceCheck(findingId, event) {
      const compliance = this.popupData.compliances.find(c => c.finding_id === findingId);
      if (compliance) {
        compliance.check = event.target.checked ? '1' : '0';
        compliance.is_modified = true;
        // Clear major/minor if compliant
        if (event.target.checked) {
          compliance.major_minor = null;
        }
      }
    },

    updateComplianceEvidence(findingId, event) {
      const compliance = this.popupData.compliances.find(c => c.finding_id === findingId);
      if (compliance) {
        compliance.evidence = event.target.value;
        compliance.is_modified = true;
      }
    },

    updateComplianceComments(findingId, event) {
      const compliance = this.popupData.compliances.find(c => c.finding_id === findingId);
      if (compliance) {
        compliance.comments = event.target.value;
        compliance.is_modified = true;
      }
    },

    updateComplianceMajorMinor(findingId, event) {
      const compliance = this.popupData.compliances.find(c => c.finding_id === findingId);
      if (compliance) {
        compliance.major_minor = event.target.value;
        compliance.is_modified = true;
      }
    },

    async saveCompliances() {
      try {
        const modifiedCompliances = (this.popupData.compliances || []).filter(c => c.is_modified);
        
        if (modifiedCompliances.length > 0) {
          await apiService.post(API_ENDPOINTS.AUDIT_FINDINGS_BULK_UPDATE, {
            audit_id: this.popupData.audit_id,
            findings: modifiedCompliances.map(c => ({
              finding_id: c.finding_id,
              check: c.check,
              evidence: c.evidence,
              comments: c.comments,
              major_minor: c.major_minor
            }))
          });
          this.$popup.success('Compliance updates saved successfully');
        }
        
        // Close the popup
        this.closePopup();
        
        // Refresh the audit list to get updated status
        this.fetchAudits();
      } catch (error) {
        console.error('Error saving compliance updates:', error);
        const msg = 'Failed to save compliance updates. Please try again.';
        this.$popup.error(msg);
        this.sendPushNotification({
          title: 'Audit Notification',
          message: msg,
          category: 'audit',
          priority: 'high',
          user_id: 'default_user'
        });
      }
    },

    getStatusButtonConfig(row) {
      if (row.status === 'Yet to Start') {
        return { 
          name: 'Start', 
          className: 'auditor-card-status status-yet' 
        };
      }
      if (row.status === 'Work In Progress') {
        return { 
          name: 'Edit Audit', 
          className: 'auditor-card-status status-progress' 
        };
      }
      return {
        name: row.status,
        className: `auditor-card-status ${row.status === 'Under review' ? 'status-review' : 'status-completed'}`,
        disabled: row.status === 'Completed' || row.status === 'Under review'
      };
    },
    
    getStatusDisplayText(row) {
      if (row.status === 'Yet to Start') {
        return 'Start';
      }
      if (row.status === 'Work In Progress') {
        return 'Edit Audit';
      }
      return row.status;
    },
    
    getStatusClass(status) {
      if (status === 'Yet to Start') return 'status-yet';
      if (status === 'Work In Progress') return 'status-progress';
      if (status === 'Under review') return 'status-review';
      if (status === 'Completed') return 'status-completed';
      return '';
    },
    
    onStatusButtonClick(row) {
      // For AI audits, don't allow editing - they are done by AI
      const isAIAudit = (row.auditType || '').toString().toUpperCase() === 'A' || 
                        (row.auditType || '').toString().toUpperCase() === 'AI';
      
      if (isAIAudit) {
        // AI audits cannot be edited - just show message or navigate to view
        this.$popup?.info('AI audits are processed automatically. Please use the AI Audit Document Upload page to manage documents.');
        return;
      }
      
      const idx = this.audits.findIndex(a => a.audit_id === row.audit_id);
      if (row.status === 'Yet to Start') {
        this.startAudit(idx);
      } else if (row.status === 'Work In Progress') {
        this.openPopup(idx);
      }
      // Disabled for 'Under review' and 'Completed' - no action
    },
    
    // Column chooser methods
    toggleColumnEditor() {
      this.showColumnEditor = !this.showColumnEditor;
      if (!this.showColumnEditor) {
        this.columnSearchQuery = '';
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
      return this.visibleColumnKeys.includes(columnKey);
    },
    
    selectAllColumns() {
      this.visibleColumnKeys = this.columnDefinitions.map(col => col.key);
    },
    
    deselectAllColumns() {
      this.visibleColumnKeys = [];
    }

  }
}
</script>

<style>
@import '@/assets/css/main.css';
</style>
<style scoped>
@import './AuditorDashboard.css';

.dashboard-header-title {
  font-size: 1.8rem;
  font-weight: 650;
  color: var(--form-header-text, var(--card-view-title-color, var(--text-primary)));
  margin-bottom: 32px;
  margin-top: 12px;
  letter-spacing: 0.01em;
  position: relative;
  display: inline-block;
  padding-bottom: 8px;
  background: transparent;
  font-family: var(--font-family, inherit);
}
.dashboard-header-title::after {
  display: none;
}

.auditor-dashboard-container {
  margin-left: 280px;
  min-height: 100vh;
  max-width: calc(100vw - 180px);
  color: var(--text-primary);
  /* background: var(--main-bg); */
  box-sizing: border-box;
  overflow-x: hidden;
  font-family: var(--font-family, inherit);
}


/* Add new styles for the versions button */
.view-versions-btn {
  margin-left: 8px;
  background-color: #7048e8;
  color: white;
}

.view-versions-btn:hover {
  background-color: #5f3dc4;
}

/* Add style for table view actions */
.audits-table td .report-btn {
  margin-bottom: 5px;
  display: inline-block;
  min-width: 120px;
  text-align: center;
}

.audits-table td .view-versions-btn {
  display: block; /* Display as block to ensure it's visible */
  margin-top: 8px;
  margin-left: 0;
  background-color: #7048e8;
  color: white;
  font-weight: 500;
}

/* Make sure the Actions column is wide enough */
.audits-table th:nth-child(10), 
.audits-table td:nth-child(10) { 
  width: 150px; 
  min-width: 150px;
  max-width: 200px; 
}

/* Add responsive handling for mobile */
@media screen and (max-width: 768px) {
  .audits-table td .report-btn {
    display: block;
    margin-bottom: 5px;
    width: 100%;
    font-size: 12px;
    padding: 6px 8px;
  }
  
  .audits-table td .view-versions-btn {
    margin-left: 0;
  }
}

/* Add these new styles */
.popup-compliance-item {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  background: #f8fafc;
}

.compliance-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.compliance-header h4 {
  margin: 0;
  color: #2d3748;
  font-size: 1.1em;
}

.compliance-id {
  color: #718096;
  font-size: 0.9em;
}

.compliance-description {
  color: #4a5568;
  margin-bottom: 16px;
  line-height: 1.5;
}

.compliance-controls {
  display: grid;
  gap: 16px;
}

.compliance-check {
  display: flex;
  align-items: center;
  gap: 8px;
}

.compliance-evidence,
.compliance-comments {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.compliance-evidence textarea,
.compliance-comments textarea {
  width: 100%;
  min-height: 80px;
  padding: 8px;
  border: 1px solid #e2e8f0;
  border-radius: 4px;
  resize: vertical;
}

.compliance-major-minor {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.compliance-major-minor select {
  padding: 8px;
  border: 1px solid #e2e8f0;
  border-radius: 4px;
  background: white;
}

.popup-loading {
  text-align: center;
  padding: 24px;
  color: #4299e1;
}

.popup-error {
  text-align: center;
  padding: 24px;
  color: #e53e3e;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.retry-btn {
  background: #e53e3e;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.retry-btn:hover {
  background: #c53030;
}

.popup-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #e2e8f0;
}

.popup-save-btn,
.popup-cancel-btn {
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
}

.popup-save-btn {
  background: #4299e1;
  color: white;
  border: none;
}

.popup-save-btn:hover {
  background: #3182ce;
}

.popup-cancel-btn {
  background: white;
  color: #4a5568;
  border: 1px solid #e2e8f0;
}

.popup-cancel-btn:hover {
  background: #f7fafc;
}

/* Audit Popup Modal Styles */
.audit-popup-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 99999 !important;
  backdrop-filter: blur(4px);
}

.audit-popup-modal {
  background: #f8f8f8 !important;
  border-radius: 16px;
  padding: 32px;
  width: 90%;
  max-width: 1000px;
  max-height: 85vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  position: relative;
  z-index: 100000 !important;
  border: 1px solid #d1d5db;
}

.popup-close {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #4a5568;
  padding: 8px;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s;
  position: absolute;
  top: 16px;
  right: 16px;
}

.popup-close:hover {
  background-color: #f3f4f6;
}
</style> 