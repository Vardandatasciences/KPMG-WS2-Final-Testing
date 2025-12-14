<template>
  <div class="subpages-checklist-container">
    <div class="checklist-header">
      <h3 class="checklist-title">
        <i class="fas fa-sitemap"></i>
        Sub-Pages Checklist
      </h3>
      <p class="checklist-description">
        Configure data retention policies for specific pages within each module. Fine-tune retention settings for individual pages.
      </p>
    </div>

    <div class="module-selector">
      <label>Select Module:</label>
      <select 
        v-model="selectedModule" 
        @change="onModuleChange"
        class="module-select"
        :disabled="loading"
      >
        <option value="">-- Select Module --</option>
        <option v-for="module in modules" :key="module.key" :value="module.key">
          {{ module.name }}
        </option>
      </select>
    </div>

    <div v-if="selectedModule" class="subpages-section">
      <div class="subpages-list">
        <div 
          v-for="page in getSubPagesForModule(selectedModule)" 
          :key="page.key"
          class="subpage-card"
          :class="{ 'active': pageConfigs && pageConfigs[page.key] && pageConfigs[page.key].enabled }"
        >
          <div class="subpage-header">
            <div class="subpage-info">
              <i :class="page.icon || 'fas fa-file'" class="subpage-icon"></i>
              <div class="subpage-details">
                <h4 class="subpage-name">{{ page.name }}</h4>
                <p class="subpage-description">{{ page.description }}</p>
              </div>
            </div>
            <label class="subpage-toggle">
              <input 
                type="checkbox" 
                :checked="getPageConfig(page.key, 'enabled')"
                @change="togglePageEnabled(page.key, $event)"
                :disabled="loading"
              />
              <span class="toggle-slider"></span>
            </label>
          </div>

          <transition name="fade">
            <div v-if="getPageConfig(page.key, 'enabled')" class="subpage-config">
              <div class="config-row">
                <label>Retention Period (Years):</label>
                <input 
                  type="number" 
                  :value="getPageConfig(page.key, 'retentionYears')"
                  @input="updatePageConfig(page.key, 'retentionYears', $event.target.value)"
                  min="0"
                  max="100"
                  :disabled="loading"
                  class="retention-input"
                />
              </div>
              <div class="config-row">
                <label>Retention Period (Months):</label>
                <input 
                  type="number" 
                  :value="getPageConfig(page.key, 'retentionMonths')"
                  @input="updatePageConfig(page.key, 'retentionMonths', $event.target.value)"
                  min="0"
                  max="11"
                  :disabled="loading"
                  class="retention-input"
                />
              </div>
              <div class="config-row">
                <label>Retention Period (Days):</label>
                <input 
                  type="number" 
                  :value="getPageConfig(page.key, 'retentionDays')"
                  @input="updatePageConfig(page.key, 'retentionDays', $event.target.value)"
                  min="0"
                  max="30"
                  :disabled="loading"
                  class="retention-input"
                />
              </div>
              <div class="config-row">
                <label>Override Module Settings:</label>
                <label class="switch-small">
                  <input 
                    type="checkbox" 
                    :checked="getPageConfig(page.key, 'overrideModule')"
                    @change="updatePageConfig(page.key, 'overrideModule', $event.target.checked)"
                    :disabled="loading"
                  />
                  <span class="slider-small"></span>
                </label>
              </div>
            </div>
          </transition>
        </div>
      </div>

      <div class="checklist-actions">
        <button 
          class="btn-save-all" 
          @click="saveAllPageConfigs"
          :disabled="loading || !hasChanges"
        >
          <i v-if="loading" class="fas fa-spinner fa-spin"></i>
          <i v-else class="fas fa-save"></i>
          {{ loading ? 'Saving...' : 'Save All Page Configurations' }}
        </button>
      </div>
    </div>

    <div v-else class="no-selection">
      <i class="fas fa-info-circle"></i>
      <p>Please select a module to configure sub-pages</p>
    </div>

    <!-- Messages -->
    <transition name="fade">
      <div v-if="message" class="message" :class="messageType">
        <i :class="messageType === 'success' ? 'fas fa-check-circle' : 'fas fa-exclamation-circle'"></i>
        {{ message }}
      </div>
    </transition>
  </div>
</template>

<script>
export default {
  name: 'SubPagesChecklist',
  props: {
    frameworkId: {
      type: [Number, String],
      default: null
    },
    initialConfigs: {
      type: Object,
      default: () => ({})
    }
  },
  data() {
    return {
      loading: false,
      message: '',
      messageType: 'success',
      selectedModule: '',
      pageConfigs: {},
      modules: [
        { key: 'policy', name: 'Policy' },
        { key: 'compliance', name: 'Compliance' },
        { key: 'audit', name: 'Audit' },
        { key: 'incident', name: 'Incident' },
        { key: 'risk', name: 'Risk' },
        { key: 'document_handling', name: 'Document Handling' },
        { key: 'change_management', name: 'Change Management' },
        { key: 'event_handling', name: 'Event Handling' }
      ],
      subPages: {
        policy: [
          { key: 'policy_create', name: 'Create Policy', description: 'Policy creation page', icon: 'fas fa-plus-circle' },
          { key: 'policy_edit', name: 'Edit Policy', description: 'Policy editing page', icon: 'fas fa-edit' },
          { key: 'policy_view', name: 'View Policy', description: 'Policy viewing page', icon: 'fas fa-eye' },
          { key: 'policy_upload', name: 'Upload Policy', description: 'Policy upload page', icon: 'fas fa-upload' },
          { key: 'policy_approval', name: 'Policy Approval', description: 'Policy approval workflow', icon: 'fas fa-check-circle' }
        ],
        compliance: [
          { key: 'compliance_create', name: 'Create Compliance', description: 'Compliance record creation', icon: 'fas fa-plus-circle' },
          { key: 'compliance_assessment', name: 'Compliance Assessment', description: 'Compliance assessment page', icon: 'fas fa-clipboard-list' },
          { key: 'compliance_report', name: 'Compliance Report', description: 'Compliance reporting', icon: 'fas fa-file-chart-line' },
          { key: 'compliance_review', name: 'Compliance Review', description: 'Compliance review page', icon: 'fas fa-search' }
        ],
        audit: [
          { key: 'audit_create', name: 'Create Audit', description: 'Audit creation page', icon: 'fas fa-plus-circle' },
          { key: 'audit_plan', name: 'Audit Plan', description: 'Audit planning page', icon: 'fas fa-calendar-alt' },
          { key: 'audit_execution', name: 'Audit Execution', description: 'Audit execution page', icon: 'fas fa-play-circle' },
          { key: 'audit_report', name: 'Audit Report', description: 'Audit reporting', icon: 'fas fa-file-alt' },
          { key: 'audit_findings', name: 'Audit Findings', description: 'Audit findings page', icon: 'fas fa-exclamation-triangle' }
        ],
        incident: [
          { key: 'incident_create', name: 'Create Incident', description: 'Incident creation page', icon: 'fas fa-plus-circle' },
          { key: 'incident_investigation', name: 'Incident Investigation', description: 'Incident investigation page', icon: 'fas fa-search' },
          { key: 'incident_response', name: 'Incident Response', description: 'Incident response page', icon: 'fas fa-first-aid' },
          { key: 'incident_report', name: 'Incident Report', description: 'Incident reporting', icon: 'fas fa-file-medical' }
        ],
        risk: [
          { key: 'risk_create', name: 'Create Risk', description: 'Risk creation page', icon: 'fas fa-plus-circle' },
          { key: 'risk_assessment', name: 'Risk Assessment', description: 'Risk assessment page', icon: 'fas fa-balance-scale' },
          { key: 'risk_mitigation', name: 'Risk Mitigation', description: 'Risk mitigation planning', icon: 'fas fa-shield-alt' },
          { key: 'risk_monitoring', name: 'Risk Monitoring', description: 'Risk monitoring dashboard', icon: 'fas fa-chart-line' }
        ],
        document_handling: [
          { key: 'document_upload', name: 'Upload Document', description: 'Document upload page', icon: 'fas fa-upload' },
          { key: 'document_view', name: 'View Document', description: 'Document viewing page', icon: 'fas fa-eye' },
          { key: 'document_edit', name: 'Edit Document', description: 'Document editing page', icon: 'fas fa-edit' },
          { key: 'document_version', name: 'Document Versioning', description: 'Document version control', icon: 'fas fa-code-branch' }
        ],
        change_management: [
          { key: 'change_create', name: 'Create Change Request', description: 'Change request creation', icon: 'fas fa-plus-circle' },
          { key: 'change_approval', name: 'Change Approval', description: 'Change approval workflow', icon: 'fas fa-check-circle' },
          { key: 'change_implementation', name: 'Change Implementation', description: 'Change implementation tracking', icon: 'fas fa-cogs' },
          { key: 'change_review', name: 'Change Review', description: 'Change review page', icon: 'fas fa-search' }
        ],
        event_handling: [
          { key: 'event_create', name: 'Create Event', description: 'Event creation page', icon: 'fas fa-plus-circle' },
          { key: 'event_log', name: 'Event Log', description: 'Event logging page', icon: 'fas fa-list' },
          { key: 'event_monitoring', name: 'Event Monitoring', description: 'Event monitoring dashboard', icon: 'fas fa-chart-bar' },
          { key: 'event_response', name: 'Event Response', description: 'Event response page', icon: 'fas fa-bolt' }
        ]
      }
    }
  },
  computed: {
    hasChanges() {
      if (!this.pageConfigs || Object.keys(this.pageConfigs).length === 0) {
        return false;
      }
      return Object.keys(this.pageConfigs).some(key => {
        const config = this.pageConfigs[key];
        if (!config) return false;
        return config.enabled || config.retentionYears > 0 || config.retentionMonths > 0 || config.retentionDays > 0;
      });
    }
  },
  watch: {
    initialConfigs: {
      immediate: true,
      handler(newConfigs) {
        this.initializeConfigs(newConfigs);
      }
    },
    frameworkId() {
      if (this.selectedModule) {
        this.loadPageConfigs();
      }
    }
  },
  mounted() {
    this.initializeConfigs(this.initialConfigs);
  },
  methods: {
    getSubPagesForModule(moduleKey) {
      return this.subPages[moduleKey] || [];
    },
    initializeConfigs(configs = {}) {
      // Initialize all page configs
      const newConfigs = {};
      Object.keys(this.subPages).forEach(moduleKey => {
        this.subPages[moduleKey].forEach(page => {
          if (configs[page.key]) {
            newConfigs[page.key] = {
              enabled: configs[page.key].enabled || false,
              retentionYears: configs[page.key].retentionYears || 0,
              retentionMonths: configs[page.key].retentionMonths || 0,
              retentionDays: configs[page.key].retentionDays || 0,
              overrideModule: configs[page.key].overrideModule || false
            };
          } else {
            newConfigs[page.key] = {
              enabled: false,
              retentionYears: 0,
              retentionMonths: 0,
              retentionDays: 0,
              overrideModule: false
            };
          }
        });
      });
      this.pageConfigs = newConfigs;
    },
    onModuleChange() {
      if (this.selectedModule && this.frameworkId) {
        this.loadPageConfigs();
      }
    },
    async loadPageConfigs() {
      if (!this.frameworkId || !this.selectedModule) return;
      
      this.loading = true;
      try {
        const { API_BASE_URL } = await import('../../../config/api.js');
        const axios = (await import('axios')).default;
        const token = localStorage.getItem('access_token');
        
        const response = await axios.get(
          `${API_BASE_URL}/api/retention/page-configs/`,
          {
            params: { 
              framework_id: this.frameworkId,
              module_key: this.selectedModule
            },
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          }
        );
        
        if (response.data.status === 'success') {
          this.initializeConfigs(response.data.data);
        }
      } catch (error) {
        console.error('Error loading page configs:', error);
        this.initializeConfigs({});
      } finally {
        this.loading = false;
      }
    },
    getPageConfig(pageKey, property) {
      if (!this.pageConfigs || !this.pageConfigs[pageKey]) {
        return property === 'enabled' ? false : 
               property === 'overrideModule' ? false : 0;
      }
      return this.pageConfigs[pageKey][property] !== undefined ? this.pageConfigs[pageKey][property] : 
             (property === 'enabled' ? false : 
              property === 'overrideModule' ? false : 0);
    },
    
    ensurePageConfig(pageKey) {
      if (!this.pageConfigs[pageKey]) {
        this.pageConfigs = {
          ...this.pageConfigs,
          [pageKey]: {
            enabled: false,
            retentionYears: 0,
            retentionMonths: 0,
            retentionDays: 0,
            overrideModule: false
          }
        };
      }
    },
    
    togglePageEnabled(pageKey, event) {
      this.ensurePageConfig(pageKey);
      this.pageConfigs[pageKey].enabled = event.target.checked;
      this.$emit('page-toggled', {
        page: pageKey,
        enabled: this.pageConfigs[pageKey].enabled
      });
    },
    
    updatePageConfig(pageKey, property, value) {
      this.ensurePageConfig(pageKey);
      if (property === 'retentionYears' || property === 'retentionMonths' || property === 'retentionDays') {
        this.pageConfigs[pageKey][property] = parseInt(value) || 0;
      } else {
        this.pageConfigs[pageKey][property] = value;
      }
    },
    async saveAllPageConfigs() {
      if (!this.frameworkId) {
        this.showMessage('Please select a framework first', 'error');
        return;
      }
      
      if (!this.selectedModule) {
        this.showMessage('Please select a module first', 'error');
        return;
      }
      
      this.loading = true;
      this.message = '';
      
      try {
        const { API_BASE_URL } = await import('../../../config/api.js');
        const axios = (await import('axios')).default;
        const token = localStorage.getItem('access_token');
        const userId = localStorage.getItem('user_id') || sessionStorage.getItem('userId');
        
        const pagesForModule = this.getSubPagesForModule(this.selectedModule);
        const configsToSave = pagesForModule
          .filter(page => this.pageConfigs[page.key])
          .map(page => ({
            page_key: page.key,
            module_key: this.selectedModule,
            framework_id: this.frameworkId,
            enabled: this.pageConfigs[page.key].enabled,
            retention_years: this.pageConfigs[page.key].retentionYears,
            retention_months: this.pageConfigs[page.key].retentionMonths,
            retention_days: this.pageConfigs[page.key].retentionDays,
            override_module: this.pageConfigs[page.key].overrideModule,
            updated_by: userId
          }));
        
        const response = await axios.put(
          `${API_BASE_URL}/api/retention/page-configs/bulk-update/`,
          {
            configs: configsToSave,
            framework_id: this.frameworkId,
            module_key: this.selectedModule,
            updated_by: userId
          },
          {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          }
        );
        
        if (response.data.status === 'success') {
          this.showMessage('Page configurations saved successfully', 'success');
          this.$emit('configs-saved', this.pageConfigs);
        } else {
          throw new Error(response.data.message || 'Failed to save configurations');
        }
      } catch (error) {
        console.error('Error saving page configs:', error);
        const errorMsg = error.response?.data?.message || error.message || 'Failed to save page configurations';
        this.showMessage(errorMsg, 'error');
      } finally {
        this.loading = false;
      }
    },
    showMessage(msg, type = 'success') {
      this.message = msg;
      this.messageType = type;
      setTimeout(() => {
        this.message = '';
      }, 5000);
    }
  }
}
</script>

<style scoped>
.subpages-checklist-container {
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.checklist-header {
  margin-bottom: 24px;
}

.checklist-title {
  font-size: 20px;
  font-weight: 600;
  color: #2c3e50;
  margin: 0 0 8px 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.checklist-description {
  color: #6c757d;
  font-size: 14px;
  margin: 0;
  line-height: 1.5;
}

.module-selector {
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.module-selector label {
  font-size: 15px;
  font-weight: 600;
  color: #495057;
}

.module-select {
  flex: 1;
  max-width: 300px;
  padding: 10px 14px;
  border: 1px solid #ced4da;
  border-radius: 6px;
  font-size: 15px;
  background: white;
}

.subpages-section {
  margin-top: 24px;
}

.subpages-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.subpage-card {
  background: white;
  border: 2px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  transition: all 0.3s ease;
}

.subpage-card.active {
  border-color: #28a745;
  box-shadow: 0 2px 8px rgba(40, 167, 69, 0.15);
}

.subpage-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.subpage-info {
  display: flex;
  gap: 12px;
  flex: 1;
}

.subpage-icon {
  font-size: 20px;
  color: #28a745;
  margin-top: 4px;
}

.subpage-details {
  flex: 1;
}

.subpage-name {
  font-size: 15px;
  font-weight: 600;
  color: #2c3e50;
  margin: 0 0 4px 0;
}

.subpage-description {
  font-size: 12px;
  color: #6c757d;
  margin: 0;
  line-height: 1.4;
}

.subpage-toggle {
  position: relative;
  display: inline-block;
  width: 50px;
  height: 26px;
  flex-shrink: 0;
}

.subpage-toggle input {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #ccc;
  transition: 0.3s;
  border-radius: 26px;
}

.toggle-slider:before {
  position: absolute;
  content: "";
  height: 20px;
  width: 20px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: 0.3s;
  border-radius: 50%;
}

.subpage-toggle input:checked + .toggle-slider {
  background-color: #28a745;
}

.subpage-toggle input:checked + .toggle-slider:before {
  transform: translateX(24px);
}

.subpage-config {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #e9ecef;
}

.config-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.config-row label {
  font-size: 14px;
  color: #495057;
  font-weight: 500;
}

.retention-input {
  width: 80px;
  padding: 6px 10px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 14px;
}

.switch-small {
  position: relative;
  display: inline-block;
  width: 40px;
  height: 20px;
}

.switch-small input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider-small {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #ccc;
  transition: 0.3s;
  border-radius: 20px;
}

.slider-small:before {
  position: absolute;
  content: "";
  height: 14px;
  width: 14px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: 0.3s;
  border-radius: 50%;
}

.switch-small input:checked + .slider-small {
  background-color: #28a745;
}

.switch-small input:checked + .slider-small:before {
  transform: translateX(20px);
}

.checklist-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 24px;
}

.btn-save-all {
  padding: 12px 24px;
  background: #28a745;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s;
}

.btn-save-all:hover:not(:disabled) {
  background: #218838;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(40, 167, 69, 0.3);
}

.btn-save-all:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.no-selection {
  text-align: center;
  padding: 60px 20px;
  color: #6c757d;
}

.no-selection i {
  font-size: 48px;
  margin-bottom: 16px;
  color: #ced4da;
}

.no-selection p {
  font-size: 16px;
  margin: 0;
}

.message {
  margin-top: 16px;
  padding: 12px 16px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
}

.message.success {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.message.error {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>

