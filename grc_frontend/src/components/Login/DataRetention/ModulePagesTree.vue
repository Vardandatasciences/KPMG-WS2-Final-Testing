<template>
  <div class="module-pages-tree-container">
    <div class="tree-header">
      <h3 class="tree-title">
        <i class="fas fa-sitemap"></i>
        Data Retention - Module & Pages Configuration
      </h3>
      <p class="tree-description">
        Configure data retention policies for each module and their associated pages where data is saved to the database.
      </p>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Loading modules and pages...</p>
    </div>

    <div v-else class="modules-tree">
      <div 
        v-for="module in modules" 
        :key="module.key"
        class="module-tree-item"
        :class="{ 'expanded': expandedModules.includes(module.key) }"
      >
        <!-- Module Header -->
        <div 
          class="module-tree-header"
          @click="toggleModule(module.key)"
        >
          <div class="module-tree-info">
            <i 
              :class="expandedModules.includes(module.key) ? 'fas fa-chevron-down' : 'fas fa-chevron-right'"
              class="expand-icon"
            ></i>
            <i :class="module.icon" class="module-tree-icon"></i>
            <div class="module-tree-details">
              <h4 class="module-tree-name">{{ module.name }}</h4>
              <p class="module-tree-description">{{ module.description }}</p>
            </div>
          </div>
          <div class="module-tree-controls">
            <label class="module-tree-toggle">
              <input 
                type="checkbox" 
                :checked="getModuleConfig(module.key, 'enabled')"
                @click.stop
                @change="toggleModuleEnabled(module.key, $event)"
                :disabled="loading"
              />
              <span class="toggle-slider"></span>
            </label>
          </div>
        </div>


        <!-- Pages List (when expanded) -->
        <transition name="slide-down">
          <div v-if="expandedModules.includes(module.key)" class="pages-list-container">
            <div class="pages-list-header">
              <h5>
                <i class="fas fa-file-code"></i>
                Pages/Endpoints Where Data is Saved
              </h5>
              <span class="pages-count">{{ getPagesForModule(module.key).length }} pages</span>
            </div>
            
            <div class="pages-list">
              <div 
                v-for="page in getPagesForModule(module.key)" 
                :key="page.key"
                class="page-item-row"
                :class="{ 'page-enabled': getPageConfig(page.key, 'enabled') }"
              >
                <!-- Page Name -->
                <div class="page-item-name">
                  <i :class="page.icon || 'fas fa-code'" class="page-icon-small"></i>
                  <span class="page-name-text">{{ page.name }}</span>
                </div>

                <!-- Page Toggle -->
                <label class="page-toggle-compact">
                  <input 
                    type="checkbox" 
                    :checked="getPageConfig(page.key, 'enabled')"
                    @change="togglePageEnabled(page.key, $event)"
                    :disabled="loading || !getModuleConfig(module.key, 'enabled') || isPageMandatory(page.key)"
                  />
                  <span class="toggle-slider-compact"></span>
                </label>

                <!-- Days Input Box -->
                <div class="page-days-box">
                  <input 
                    type="number" 
                    :value="getPageConfig(page.key, 'retentionDays')"
                    @input="updatePageConfig(page.key, 'retentionDays', $event.target.value)"
                    min="0"
                    max="36500"
                    placeholder="210"
                    class="days-input"
                    :disabled="loading || !getPageConfig(page.key, 'enabled') || !getModuleConfig(module.key, 'enabled')"
                  />
                  <span class="days-suffix">days</span>
                </div>
              </div>

              <div v-if="getPagesForModule(module.key).length === 0" class="no-pages">
                <i class="fas fa-info-circle"></i>
                <p>No pages found for this module</p>
              </div>
            </div>
          </div>
        </transition>
      </div>
    </div>

    <div class="tree-actions">
      <button 
        class="btn-save-all" 
        @click="saveAllConfigs"
        :disabled="loading || !hasChanges"
      >
        <i v-if="loading" class="fas fa-spinner fa-spin"></i>
        <i v-else class="fas fa-save"></i>
        {{ loading ? 'Saving...' : 'Save All Configurations' }}
      </button>
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
  name: 'ModulePagesTree',
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
      expandedModules: [],
      moduleConfigs: {},
      pageConfigs: {},
      optionalPages: ['risk_update', 'risk_instance_update'],
      modules: [
        {
          key: 'policy',
          name: 'Policy',
          description: 'Policy documents, frameworks, and approvals',
          icon: 'fas fa-file-contract'
        },
        {
          key: 'compliance',
          name: 'Compliance',
          description: 'Compliance records and assessments',
          icon: 'fas fa-clipboard-check'
        },
        {
          key: 'audit',
          name: 'Audit',
          description: 'Audit reports and findings',
          icon: 'fas fa-search'
        },
        {
          key: 'incident',
          name: 'Incident',
          description: 'Incident reports and investigations',
          icon: 'fas fa-exclamation-triangle'
        },
        {
          key: 'risk',
          name: 'Risk',
          description: 'Risk assessments and mitigation plans',
          icon: 'fas fa-shield-alt'
        },
        {
          key: 'document_handling',
          name: 'Document Handling',
          description: 'Document management and storage',
          icon: 'fas fa-file-alt'
        },
        {
          key: 'change_management',
          name: 'Change Management',
          description: 'Change requests and approvals',
          icon: 'fas fa-exchange-alt'
        },
        {
          key: 'event_handling',
          name: 'Event Handling',
          description: 'Event logs and tracking',
          icon: 'fas fa-calendar-alt'
        },
        {
          key: 'vendor',
          name: 'Vendor',
          description: 'Vendor management and onboarding',
          icon: 'fas fa-building'
        },
        {
          key: 'vendor_contract',
          name: 'Vendor Contract',
          description: 'Vendor contracts and agreements',
          icon: 'fas fa-file-contract'
        },
        {
          key: 'contract_term',
          name: 'Contract Terms',
          description: 'Contract terms and conditions',
          icon: 'fas fa-list-alt'
        },
        {
          key: 'contract_clause',
          name: 'Contract Clauses',
          description: 'Contract clauses and provisions',
          icon: 'fas fa-gavel'
        },
        {
          key: 'vendor_sla',
          name: 'Vendor SLA',
          description: 'Vendor service level agreements',
          icon: 'fas fa-handshake'
        },
        {
          key: 'sla_metric',
          name: 'SLA Metrics',
          description: 'SLA performance metrics',
          icon: 'fas fa-chart-line'
        },
        {
          key: 'rfp',
          name: 'RFP',
          description: 'Request for Proposal management',
          icon: 'fas fa-file-alt'
        },
        {
          key: 'rfp_evaluation_criteria',
          name: 'RFP Evaluation Criteria',
          description: 'RFP evaluation criteria and scoring',
          icon: 'fas fa-clipboard-list'
        },
        {
          key: 'rfp_type_custom_fields',
          name: 'RFP Type Custom Fields',
          description: 'RFP type custom field configurations',
          icon: 'fas fa-cog'
        },
        {
          key: 'bcp_drp_plan',
          name: 'BCP/DRP Plan',
          description: 'Business Continuity and Disaster Recovery plans',
          icon: 'fas fa-shield-alt'
        },
        {
          key: 'bcp_drp_evaluation',
          name: 'BCP/DRP Evaluation',
          description: 'BCP/DRP plan evaluations',
          icon: 'fas fa-check-circle'
        }
      ],
      // Pages/Endpoints where data is saved for each module
      modulePages: {
        policy: [
          { 
            key: 'policy_create', 
            name: 'Create Policy', 
            endpoint: '/api/frameworks/{id}/policies/',
            description: 'Create new policy in framework',
            icon: 'fas fa-plus-circle'
          },
          { 
            key: 'policy_update', 
            name: 'Update Policy', 
            endpoint: '/api/policies/{id}/',
            description: 'Update existing policy',
            icon: 'fas fa-edit'
          },
          { 
            key: 'policy_version_create', 
            name: 'Create Policy Version', 
            endpoint: '/api/policies/{id}/create-version/',
            description: 'Create new version of policy',
            icon: 'fas fa-code-branch'
          },
          { 
            key: 'policy_approval', 
            name: 'Policy Approval', 
            endpoint: '/api/policy-approvals/{id}/',
            description: 'Update policy approval status',
            icon: 'fas fa-check-circle'
          },
          { 
            key: 'policy_acknowledgement', 
            name: 'Policy Acknowledgement', 
            endpoint: '/api/policy-acknowledgements/create/',
            description: 'Create policy acknowledgement request',
            icon: 'fas fa-signature'
          },
          { 
            key: 'policy_templating', 
            name: 'Policy Templating', 
            endpoint: '/api/tailoring/create-policy/',
            description: 'Create tailored policy',
            icon: 'fas fa-file-alt'
          },
          { 
            key: 'policy_subpolicy_add', 
            name: 'Add SubPolicy', 
            endpoint: '/api/policies/{id}/subpolicies/add/',
            description: 'Add subpolicy to policy',
            icon: 'fas fa-list'
          },
          { 
            key: 'framework_create', 
            name: 'Create Framework', 
            endpoint: '/api/frameworks/',
            description: 'Create new framework',
            icon: 'fas fa-layer-group'
          },
          { 
            key: 'framework_update', 
            name: 'Update Framework', 
            endpoint: '/api/frameworks/{id}/',
            description: 'Update existing framework',
            icon: 'fas fa-edit'
          },
          { 
            key: 'framework_version_create', 
            name: 'Create Framework Version', 
            endpoint: '/api/frameworks/{id}/create-version/',
            description: 'Create new framework version',
            icon: 'fas fa-code-branch'
          },
          { 
            key: 'framework_approval', 
            name: 'Framework Approval', 
            endpoint: '/api/framework-approvals/{id}/',
            description: 'Update framework approval',
            icon: 'fas fa-check-circle'
          },
          { 
            key: 'save_policy_details', 
            name: 'Save Policy Details', 
            endpoint: '/api/save-policy-details/',
            description: 'Save policy details from upload',
            icon: 'fas fa-save'
          },
          { 
            key: 'save_framework_to_db', 
            name: 'Save Framework to Database', 
            endpoint: '/api/save-framework-to-database/',
            description: 'Save framework to database',
            icon: 'fas fa-database'
          },
          { 
            key: 'save_policies', 
            name: 'Save Policies', 
            endpoint: '/api/save-policies/',
            description: 'Save multiple policies',
            icon: 'fas fa-save'
          },
          { 
            key: 'save_single_policy', 
            name: 'Save Single Policy', 
            endpoint: '/api/save-single-policy/',
            description: 'Save single policy',
            icon: 'fas fa-save'
          },
          { 
            key: 'save_policy_category', 
            name: 'Save Policy Category', 
            endpoint: '/api/policy-categories/save/',
            description: 'Save policy category',
            icon: 'fas fa-tag'
          },
          { 
            key: 'create_framework_approval', 
            name: 'Create Framework Approval', 
            endpoint: '/api/frameworks/{id}/create-approval/',
            description: 'Create framework approval request',
            icon: 'fas fa-file-check'
          }
        ],
        compliance: [
          { 
            key: 'compliance_create', 
            name: 'Create Compliance', 
            endpoint: '/api/compliance-create/',
            description: 'Create new compliance record',
            icon: 'fas fa-plus-circle'
          },
          { 
            key: 'compliance_edit', 
            name: 'Edit Compliance', 
            endpoint: '/api/compliance_edit/{id}/edit/',
            description: 'Edit existing compliance',
            icon: 'fas fa-edit'
          },
          { 
            key: 'compliance_category_add', 
            name: 'Add Compliance Category', 
            endpoint: '/api/categories/add/',
            description: 'Add new compliance category',
            icon: 'fas fa-tag'
          },
          { 
            key: 'compliance_category_bu_add', 
            name: 'Add Category Business Unit', 
            endpoint: '/api/category-business-units/add/',
            description: 'Add category business unit',
            icon: 'fas fa-building'
          }
        ],
        audit: [
          { 
            key: 'audit_create', 
            name: 'Create Audit', 
            endpoint: '/api/create-audit/',
            description: 'Create new audit',
            icon: 'fas fa-plus-circle'
          },
          { 
            key: 'audit_status_update', 
            name: 'Update Audit Status', 
            endpoint: '/api/audits/{id}/status/',
            description: 'Update audit status',
            icon: 'fas fa-edit'
          },
          { 
            key: 'audit_version_save', 
            name: 'Save Audit Version', 
            endpoint: '/api/audits/{id}/save-version/',
            description: 'Save audit version',
            icon: 'fas fa-code-branch'
          },
          { 
            key: 'audit_finding_update', 
            name: 'Update Audit Finding', 
            endpoint: '/api/audit-findings/{id}/',
            description: 'Update audit finding',
            icon: 'fas fa-edit'
          },
          { 
            key: 'audit_add_compliance', 
            name: 'Add Compliance to Audit', 
            endpoint: '/api/audits/{id}/add-compliance/',
            description: 'Add compliance to audit',
            icon: 'fas fa-link'
          },
          { 
            key: 'audit_review_progress', 
            name: 'Save Review Progress', 
            endpoint: '/api/audits/{id}/save-review-progress/',
            description: 'Save audit review progress',
            icon: 'fas fa-save'
          }
        ],
        incident: [
          { 
            key: 'incident_create', 
            name: 'Create Incident', 
            endpoint: '/api/incidents/create/',
            description: 'Create new incident',
            icon: 'fas fa-plus-circle'
          },
          { 
            key: 'incident_update', 
            name: 'Update Incident', 
            endpoint: '/api/incidents/{id}/update/',
            description: 'Update existing incident',
            icon: 'fas fa-edit'
          },
          { 
            key: 'incident_status_update', 
            name: 'Update Incident Status', 
            endpoint: '/api/incidents/{id}/status/',
            description: 'Update incident status',
            icon: 'fas fa-sync'
          },
          { 
            key: 'incident_workflow_create', 
            name: 'Create Workflow', 
            endpoint: '/api/workflow/create/',
            description: 'Create incident workflow',
            icon: 'fas fa-project-diagram'
          },
          { 
            key: 'incident_from_audit', 
            name: 'Create Incident from Audit', 
            endpoint: '/api/incident/from-audit-finding/',
            description: 'Create incident from audit finding',
            icon: 'fas fa-arrow-right'
          },
          { 
            key: 'incident_category_add', 
            name: 'Add Incident Category', 
            endpoint: '/api/incident-categories/add/',
            description: 'Add incident category',
            icon: 'fas fa-tag'
          }
        ],
        risk: [
          { 
            key: 'risk_create', 
            name: 'Create Risk', 
            endpoint: '/api/risks/',
            description: 'Create new risk',
            icon: 'fas fa-plus-circle'
          },
          { 
            key: 'risk_update', 
            name: 'Update Risk', 
            endpoint: '/api/risks/{id}/',
            description: 'Update existing risk',
            icon: 'fas fa-edit'
          },
          { 
            key: 'risk_instance_create', 
            name: 'Create Risk Instance', 
            endpoint: '/api/create-risk-instance/',
            description: 'Create new risk instance',
            icon: 'fas fa-plus-square'
          },
          { 
            key: 'risk_instance_update', 
            name: 'Update Risk Instance', 
            endpoint: '/api/risk-instances/{id}/',
            description: 'Update risk instance',
            icon: 'fas fa-edit'
          },
          { 
            key: 'risk_status_update', 
            name: 'Update Risk Status', 
            endpoint: '/api/risk-update-status/',
            description: 'Update risk status',
            icon: 'fas fa-sync'
          },
          { 
            key: 'risk_mitigation_update', 
            name: 'Update Risk Mitigation', 
            endpoint: '/api/risk-update-mitigation/{id}/',
            description: 'Update risk mitigation',
            icon: 'fas fa-shield-alt'
          },
          { 
            key: 'risk_category_add', 
            name: 'Add Risk Category', 
            endpoint: '/api/risk-categories/add/',
            description: 'Add risk category',
            icon: 'fas fa-tag'
          }
        ],
        document_handling: [
          { 
            key: 'document_upload', 
            name: 'Upload Document', 
            endpoint: '/api/documents/upload/',
            description: 'Upload document',
            icon: 'fas fa-upload'
          },
          { 
            key: 'document_save', 
            name: 'Save Document', 
            endpoint: '/api/documents/save/',
            description: 'Save document metadata',
            icon: 'fas fa-save'
          }
        ],
        change_management: [
          { 
            key: 'change_create', 
            name: 'Create Change Request', 
            endpoint: '/api/change-requests/create/',
            description: 'Create change request',
            icon: 'fas fa-plus-circle'
          },
          { 
            key: 'change_update', 
            name: 'Update Change Request', 
            endpoint: '/api/change-requests/{id}/',
            description: 'Update change request',
            icon: 'fas fa-edit'
          }
        ],
        event_handling: [
          { 
            key: 'event_create', 
            name: 'Create Event', 
            endpoint: '/api/events/create/',
            description: 'Create event log',
            icon: 'fas fa-plus-circle'
          },
          { 
            key: 'event_log', 
            name: 'Log Event', 
            endpoint: '/api/events/log/',
            description: 'Log system event',
            icon: 'fas fa-list'
          }
        ],
        vendor: [
          { 
            key: 'vendor_create', 
            name: 'Create Vendor', 
            endpoint: '/api/tprm/vendor-core/vendors/',
            description: 'Create new vendor',
            icon: 'fas fa-plus-circle'
          },
          { 
            key: 'vendor_update', 
            name: 'Update Vendor', 
            endpoint: '/api/tprm/vendor-core/vendors/{id}/',
            description: 'Update existing vendor',
            icon: 'fas fa-edit'
          },
          { 
            key: 'vendor_category_create', 
            name: 'Create Vendor Category', 
            endpoint: '/api/tprm/vendor-core/vendor-categories/',
            description: 'Create vendor category',
            icon: 'fas fa-tag'
          },
          { 
            key: 'vendor_contact_create', 
            name: 'Create Vendor Contact', 
            endpoint: '/api/tprm/vendor-core/vendor-contacts/',
            description: 'Create vendor contact',
            icon: 'fas fa-user-plus'
          },
          { 
            key: 'vendor_document_upload', 
            name: 'Upload Vendor Document', 
            endpoint: '/api/tprm/vendor-core/vendor-documents/',
            description: 'Upload vendor document',
            icon: 'fas fa-upload'
          },
          { 
            key: 'vendor_submit_registration', 
            name: 'Submit Vendor Registration', 
            endpoint: '/api/tprm/vendor-core/temp-vendors/vendor_submit_registration/',
            description: 'Submit vendor registration',
            icon: 'fas fa-paper-plane'
          }
        ],
        vendor_contract: [
          { 
            key: 'contract_create', 
            name: 'Create Contract', 
            endpoint: '/api/tprm/contracts/contracts/create/',
            description: 'Create new vendor contract',
            icon: 'fas fa-plus-circle'
          },
          { 
            key: 'contract_update', 
            name: 'Update Contract', 
            endpoint: '/api/tprm/contracts/contracts/{id}/update/',
            description: 'Update existing contract',
            icon: 'fas fa-edit'
          },
          { 
            key: 'contract_archive', 
            name: 'Archive Contract', 
            endpoint: '/api/tprm/contracts/contracts/{id}/archive/',
            description: 'Archive contract',
            icon: 'fas fa-archive'
          },
          { 
            key: 'contract_restore', 
            name: 'Restore Contract', 
            endpoint: '/api/tprm/contracts/contracts/{id}/restore/',
            description: 'Restore archived contract',
            icon: 'fas fa-undo'
          },
          { 
            key: 'contract_version_create', 
            name: 'Create Contract Version', 
            endpoint: '/api/tprm/contracts/contracts/{id}/create-version/',
            description: 'Create contract version',
            icon: 'fas fa-code-branch'
          },
          { 
            key: 'contract_amendment_create', 
            name: 'Create Amendment', 
            endpoint: '/api/tprm/contracts/contracts/{id}/amendments/create/',
            description: 'Create contract amendment',
            icon: 'fas fa-file-signature'
          },
          { 
            key: 'contract_subcontract_create', 
            name: 'Create Subcontract', 
            endpoint: '/api/tprm/contracts/contracts/{id}/subcontracts/create/',
            description: 'Create subcontract',
            icon: 'fas fa-sitemap'
          }
        ],
        contract_term: [
          { 
            key: 'contract_term_create', 
            name: 'Create Contract Term', 
            endpoint: '/api/tprm/contracts/contracts/{id}/terms/create/',
            description: 'Create contract term',
            icon: 'fas fa-plus-circle'
          },
          { 
            key: 'contract_term_update', 
            name: 'Update Contract Term', 
            endpoint: '/api/tprm/contracts/contracts/{id}/terms/{term_id}/update/',
            description: 'Update contract term',
            icon: 'fas fa-edit'
          },
          { 
            key: 'contract_term_delete', 
            name: 'Delete Contract Term', 
            endpoint: '/api/tprm/contracts/contracts/{id}/terms/{term_id}/delete/',
            description: 'Delete contract term',
            icon: 'fas fa-trash'
          }
        ],
        contract_clause: [
          { 
            key: 'contract_clause_create', 
            name: 'Create Contract Clause', 
            endpoint: '/api/tprm/contracts/contracts/{id}/clauses/create/',
            description: 'Create contract clause',
            icon: 'fas fa-plus-circle'
          },
          { 
            key: 'contract_clause_update', 
            name: 'Update Contract Clause', 
            endpoint: '/api/tprm/contracts/contracts/{id}/clauses/{clause_id}/update/',
            description: 'Update contract clause',
            icon: 'fas fa-edit'
          },
          { 
            key: 'contract_clause_delete', 
            name: 'Delete Contract Clause', 
            endpoint: '/api/tprm/contracts/contracts/{id}/clauses/{clause_id}/delete/',
            description: 'Delete contract clause',
            icon: 'fas fa-trash'
          }
        ],
        vendor_sla: [
          { 
            key: 'sla_create', 
            name: 'Create SLA', 
            endpoint: '/api/tprm/slas/',
            description: 'Create new vendor SLA',
            icon: 'fas fa-plus-circle'
          },
          { 
            key: 'sla_update', 
            name: 'Update SLA', 
            endpoint: '/api/tprm/slas/{id}/',
            description: 'Update existing SLA',
            icon: 'fas fa-edit'
          },
          { 
            key: 'sla_submit', 
            name: 'Submit SLA', 
            endpoint: '/api/tprm/slas/{id}/submit/',
            description: 'Submit SLA for approval',
            icon: 'fas fa-paper-plane'
          },
          { 
            key: 'sla_approve', 
            name: 'Approve SLA', 
            endpoint: '/api/tprm/slas/{id}/approve/',
            description: 'Approve SLA',
            icon: 'fas fa-check-circle'
          }
        ],
        sla_metric: [
          { 
            key: 'sla_metric_create', 
            name: 'Create SLA Metric', 
            endpoint: '/api/tprm/slas/metrics/',
            description: 'Create new SLA metric',
            icon: 'fas fa-plus-circle'
          },
          { 
            key: 'sla_metric_update', 
            name: 'Update SLA Metric', 
            endpoint: '/api/tprm/slas/metrics/{id}/',
            description: 'Update existing SLA metric',
            icon: 'fas fa-edit'
          },
          { 
            key: 'sla_metric_delete', 
            name: 'Delete SLA Metric', 
            endpoint: '/api/tprm/slas/metrics/{id}/',
            description: 'Delete SLA metric',
            icon: 'fas fa-trash'
          }
        ],
        rfp: [
          { 
            key: 'rfp_create', 
            name: 'Create RFP', 
            endpoint: '/api/tprm/rfp/',
            description: 'Create new RFP',
            icon: 'fas fa-plus-circle'
          },
          { 
            key: 'rfp_update', 
            name: 'Update RFP', 
            endpoint: '/api/tprm/rfp/{id}/',
            description: 'Update existing RFP',
            icon: 'fas fa-edit'
          },
          { 
            key: 'rfp_submit_for_review', 
            name: 'Submit RFP for Review', 
            endpoint: '/api/tprm/rfp/{id}/submit_for_review/',
            description: 'Submit RFP for review',
            icon: 'fas fa-paper-plane'
          },
          { 
            key: 'rfp_publish', 
            name: 'Publish RFP', 
            endpoint: '/api/tprm/rfp/{id}/publish/',
            description: 'Publish RFP',
            icon: 'fas fa-bullhorn'
          },
          { 
            key: 'rfp_award', 
            name: 'Award RFP', 
            endpoint: '/api/tprm/rfp/{id}/award/',
            description: 'Award RFP to vendor',
            icon: 'fas fa-trophy'
          },
          { 
            key: 'rfp_document_upload', 
            name: 'Upload RFP Document', 
            endpoint: '/api/tprm/rfp/upload-document/',
            description: 'Upload RFP document',
            icon: 'fas fa-upload'
          },
          { 
            key: 'rfp_version_create', 
            name: 'Create RFP Version', 
            endpoint: '/api/tprm/rfp/rfps/{id}/edit_with_versioning/',
            description: 'Create RFP version',
            icon: 'fas fa-code-branch'
          }
        ],
        rfp_evaluation_criteria: [
          { 
            key: 'rfp_evaluation_criteria_create', 
            name: 'Create Evaluation Criteria', 
            endpoint: '/api/tprm/rfp/evaluation-criteria/',
            description: 'Create RFP evaluation criteria',
            icon: 'fas fa-plus-circle'
          },
          { 
            key: 'rfp_evaluation_criteria_update', 
            name: 'Update Evaluation Criteria', 
            endpoint: '/api/tprm/rfp/evaluation-criteria/{id}/',
            description: 'Update RFP evaluation criteria',
            icon: 'fas fa-edit'
          },
          { 
            key: 'rfp_evaluation_criteria_delete', 
            name: 'Delete Evaluation Criteria', 
            endpoint: '/api/tprm/rfp/evaluation-criteria/{id}/',
            description: 'Delete RFP evaluation criteria',
            icon: 'fas fa-trash'
          }
        ],
        rfp_type_custom_fields: [
          { 
            key: 'rfp_type_custom_fields_create', 
            name: 'Create RFP Type Custom Fields', 
            endpoint: '/api/tprm/rfp/rfp-types/',
            description: 'Create RFP type custom fields',
            icon: 'fas fa-plus-circle'
          },
          { 
            key: 'rfp_type_custom_fields_update', 
            name: 'Update RFP Type Custom Fields', 
            endpoint: '/api/tprm/rfp/rfp-types/{id}/',
            description: 'Update RFP type custom fields',
            icon: 'fas fa-edit'
          }
        ],
        bcp_drp_plan: [
          { 
            key: 'bcp_drp_plan_create', 
            name: 'Create BCP/DRP Plan', 
            endpoint: '/api/tprm/bcpdrp/plans/',
            description: 'Create new BCP/DRP plan',
            icon: 'fas fa-plus-circle'
          },
          { 
            key: 'bcp_drp_plan_update', 
            name: 'Update BCP/DRP Plan', 
            endpoint: '/api/tprm/bcpdrp/plans/{id}/',
            description: 'Update existing BCP/DRP plan',
            icon: 'fas fa-edit'
          },
          { 
            key: 'bcp_drp_plan_upload', 
            name: 'Upload BCP/DRP Plan', 
            endpoint: '/api/tprm/bcpdrp/vendor-upload/',
            description: 'Upload BCP/DRP plan document',
            icon: 'fas fa-upload'
          },
          { 
            key: 'bcp_drp_plan_ocr_extract', 
            name: 'Extract OCR Data', 
            endpoint: '/api/tprm/bcpdrp/ocr/plans/{id}/extract/',
            description: 'Extract data from plan via OCR',
            icon: 'fas fa-scanner'
          },
          { 
            key: 'bcp_drp_plan_approve', 
            name: 'Approve BCP/DRP Plan', 
            endpoint: '/api/tprm/bcpdrp/plans/{id}/approve/',
            description: 'Approve BCP/DRP plan',
            icon: 'fas fa-check-circle'
          },
          { 
            key: 'bcp_drp_plan_reject', 
            name: 'Reject BCP/DRP Plan', 
            endpoint: '/api/tprm/bcpdrp/plans/{id}/reject/',
            description: 'Reject BCP/DRP plan',
            icon: 'fas fa-times-circle'
          }
        ],
        bcp_drp_evaluation: [
          { 
            key: 'bcp_drp_evaluation_create', 
            name: 'Create Evaluation', 
            endpoint: '/api/tprm/bcpdrp/evaluations/{plan_id}/save/',
            description: 'Create BCP/DRP evaluation',
            icon: 'fas fa-plus-circle'
          },
          { 
            key: 'bcp_drp_evaluation_update', 
            name: 'Update Evaluation', 
            endpoint: '/api/tprm/bcpdrp/evaluations/{plan_id}/save/',
            description: 'Update BCP/DRP evaluation',
            icon: 'fas fa-edit'
          },
          { 
            key: 'bcp_drp_evaluation_save', 
            name: 'Save Evaluation', 
            endpoint: '/api/tprm/bcpdrp/evaluations/{plan_id}/save/',
            description: 'Save BCP/DRP evaluation',
            icon: 'fas fa-save'
          }
        ]
      }
    }
  },
  computed: {
    hasChanges() {
      // Check if any config has been modified
      return Object.keys(this.moduleConfigs).length > 0 || Object.keys(this.pageConfigs).length > 0;
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
      if (this.frameworkId) {
        this.loadConfigs();
      }
    }
  },
  mounted() {
    this.initializeConfigs(this.initialConfigs);
    if (this.frameworkId) {
      this.loadConfigs();
    }
  },
  methods: {
    getPagesForModule(moduleKey) {
      return this.modulePages[moduleKey] || [];
    },
    toggleModule(moduleKey) {
      const index = this.expandedModules.indexOf(moduleKey);
      if (index > -1) {
        this.expandedModules.splice(index, 1);
      } else {
        this.expandedModules.push(moduleKey);
      }
    },
     initializeConfigs(configs = {}) {
       // Initialize module configs with defaults: enabled=true
       const newModuleConfigs = {};
       this.modules.forEach(module => {
         if (configs.modules && configs.modules[module.key]) {
           newModuleConfigs[module.key] = { ...configs.modules[module.key] };
           // Ensure enabled defaults to true if not set
           if (newModuleConfigs[module.key].enabled === undefined) {
             newModuleConfigs[module.key].enabled = true;
           }
         } else {
           newModuleConfigs[module.key] = {
             enabled: true,
             retentionYears: 0,
             retentionMonths: 0,
             retentionDays: 0,
             autoDelete: false,
             disposalMethod: 'secure_delete'
           };
         }
       });
       this.moduleConfigs = newModuleConfigs;

       // Initialize page configs with defaults: enabled=true, retentionDays=210
       const newPageConfigs = {};
       Object.keys(this.modulePages).forEach(moduleKey => {
         this.modulePages[moduleKey].forEach(page => {
           if (configs.pages && configs.pages[page.key]) {
             newPageConfigs[page.key] = { ...configs.pages[page.key] };
             // Ensure retentionDays defaults to 210 if not set
             if (newPageConfigs[page.key].retentionDays === undefined || newPageConfigs[page.key].retentionDays === 0) {
               newPageConfigs[page.key].retentionDays = 210;
             }
           } else {
             newPageConfigs[page.key] = {
               enabled: true,
               retentionYears: 0,
               retentionMonths: 0,
               retentionDays: 210,
               overrideModule: false
             };
           }
         });
       });
       this.pageConfigs = newPageConfigs;
     },
    async loadConfigs() {
      if (!this.frameworkId) return;
      
      this.loading = true;
      try {
        const { API_BASE_URL } = await import('../../../config/api.js');
        const axios = (await import('axios')).default;
        const token = localStorage.getItem('access_token');
        
        // Load module configs
        const moduleResponse = await axios.get(
          `${API_BASE_URL}/api/retention/module-configs/`,
          {
            params: { framework_id: this.frameworkId },
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          }
        );
        
        // Load page configs
        const pageResponse = await axios.get(
          `${API_BASE_URL}/api/retention/page-configs/`,
          {
            params: { framework_id: this.frameworkId },
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          }
        );
        
        this.initializeConfigs({
          modules: moduleResponse.data.status === 'success' ? moduleResponse.data.data : {},
          pages: pageResponse.data.status === 'success' ? pageResponse.data.data : {}
        });
      } catch (error) {
        console.error('Error loading configs:', error);
        this.initializeConfigs({});
      } finally {
        this.loading = false;
      }
    },
    getModuleConfig(moduleKey, property) {
      if (!this.moduleConfigs || !this.moduleConfigs[moduleKey]) {
        return property === 'enabled' ? true : 
               property === 'disposalMethod' ? 'secure_delete' : 0;
      }
      return this.moduleConfigs[moduleKey][property] !== undefined ? 
             this.moduleConfigs[moduleKey][property] : 
             (property === 'enabled' ? true : 
              property === 'disposalMethod' ? 'secure_delete' : 0);
    },
    ensureModuleConfig(moduleKey) {
      if (!this.moduleConfigs[moduleKey]) {
        this.moduleConfigs = {
          ...this.moduleConfigs,
          [moduleKey]: {
            enabled: true,
            retentionYears: 0,
            retentionMonths: 0,
            retentionDays: 0,
            autoDelete: false,
            disposalMethod: 'secure_delete'
          }
        };
      }
    },
    toggleModuleEnabled(moduleKey, event) {
      this.ensureModuleConfig(moduleKey);
      const isEnabled = event.target.checked;
      this.moduleConfigs[moduleKey].enabled = isEnabled;
      
      // If module is disabled, uncheck all pages in this module
      if (!isEnabled && this.modulePages[moduleKey]) {
        this.modulePages[moduleKey].forEach(page => {
          this.ensurePageConfig(page.key);
          this.pageConfigs[page.key].enabled = false;
        });
      }
    },
    updateModuleConfig(moduleKey, property, value) {
      this.ensureModuleConfig(moduleKey);
      if (property.includes('retention')) {
        this.moduleConfigs[moduleKey][property] = parseInt(value) || 0;
      } else {
        this.moduleConfigs[moduleKey][property] = value;
      }
    },
     getPageConfig(pageKey, property) {
       if (!this.pageConfigs || !this.pageConfigs[pageKey]) {
         return property === 'enabled' ? true : 
                property === 'overrideModule' ? false : 
                property === 'retentionDays' ? 210 : 0;
       }
       return this.pageConfigs[pageKey][property] !== undefined ? 
              this.pageConfigs[pageKey][property] : 
              (property === 'enabled' ? true : 
               property === 'overrideModule' ? false :
               property === 'retentionDays' ? 210 : 0);
     },
     ensurePageConfig(pageKey) {
       if (!this.pageConfigs[pageKey]) {
         this.pageConfigs = {
           ...this.pageConfigs,
           [pageKey]: {
             enabled: true,
             retentionYears: 0,
             retentionMonths: 0,
             retentionDays: 210,
             overrideModule: false
           }
         };
       }
     },
    togglePageEnabled(pageKey, event) {
      if (this.isPageMandatory(pageKey)) {
        // Keep mandatory pages always enabled
        this.ensurePageConfig(pageKey);
        this.pageConfigs[pageKey].enabled = true;
        event.target.checked = true;
        return;
      }
      this.ensurePageConfig(pageKey);
      this.pageConfigs[pageKey].enabled = event.target.checked;
    },
    isPageMandatory(pageKey) {
      return !this.optionalPages.includes(pageKey);
    },
     updatePageConfig(pageKey, property, value) {
       this.ensurePageConfig(pageKey);
       if (property === 'retentionDays') {
         this.pageConfigs[pageKey][property] = parseInt(value) || 210;
       } else if (property.includes('retention')) {
         this.pageConfigs[pageKey][property] = parseInt(value) || 0;
       } else {
         this.pageConfigs[pageKey][property] = value;
       }
     },
    async saveAllConfigs() {
      if (!this.frameworkId) {
        this.showMessage('Please select a framework first', 'error');
        return;
      }
      
      this.loading = true;
      this.message = '';
      
      try {
        const { API_BASE_URL } = await import('../../../config/api.js');
        const axios = (await import('axios')).default;
        const token = localStorage.getItem('access_token');
        const userId = localStorage.getItem('user_id') || sessionStorage.getItem('userId');
        
        // Save module configs
        const moduleConfigsToSave = Object.keys(this.moduleConfigs).map(key => ({
          module_key: key,
          framework_id: this.frameworkId,
          enabled: this.moduleConfigs[key].enabled,
          retention_years: this.moduleConfigs[key].retentionYears,
          retention_months: this.moduleConfigs[key].retentionMonths,
          retention_days: this.moduleConfigs[key].retentionDays,
          auto_delete: this.moduleConfigs[key].autoDelete,
          disposal_method: this.moduleConfigs[key].disposalMethod,
          updated_by: userId
        }));
        
        await axios.put(
          `${API_BASE_URL}/api/retention/module-configs/bulk-update/`,
          {
            configs: moduleConfigsToSave,
            framework_id: this.frameworkId,
            updated_by: userId
          },
          {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          }
        );
        
        // Save page configs
        const pageConfigsToSave = Object.keys(this.pageConfigs).map(key => {
          // Find which module this page belongs to
          let moduleKey = '';
          Object.keys(this.modulePages).forEach(modKey => {
            if (this.modulePages[modKey].some(p => p.key === key)) {
              moduleKey = modKey;
            }
          });
          
          return {
            page_key: key,
            module_key: moduleKey,
            framework_id: this.frameworkId,
            enabled: this.pageConfigs[key].enabled,
            retention_years: this.pageConfigs[key].retentionYears,
            retention_months: this.pageConfigs[key].retentionMonths,
            retention_days: this.pageConfigs[key].retentionDays,
            override_module: this.pageConfigs[key].overrideModule,
            updated_by: userId
          };
        });
        
        await axios.put(
          `${API_BASE_URL}/api/retention/page-configs/bulk-update/`,
          {
            configs: pageConfigsToSave,
            framework_id: this.frameworkId,
            updated_by: userId
          },
          {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          }
        );
        
        this.showMessage('All configurations saved successfully', 'success');
        this.$emit('configs-saved', {
          modules: this.moduleConfigs,
          pages: this.pageConfigs
        });
      } catch (error) {
        console.error('Error saving configs:', error);
        const errorMsg = error.response?.data?.message || error.message || 'Failed to save configurations';
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
.module-pages-tree-container {
  padding: 20px;
  background: transparent;
}

.tree-header {
  margin-bottom: 24px;
}

.tree-title {
  font-size: 20px;
  font-weight: 600;
  color: #2c3e50;
  margin: 0 0 8px 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.tree-description {
  color: #6c757d;
  font-size: 14px;
  margin: 0;
  line-height: 1.5;
}

.loading-state {
  text-align: center;
  padding: 60px 20px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e5e7eb;
  border-top: 4px solid #007bff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.modules-tree {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.module-tree-item {
  background: transparent;
  border: none;
  border-bottom: 1px solid #e5e7eb;
  overflow: visible;
  padding-bottom: 12px;
  margin-bottom: 12px;
}

.module-tree-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  cursor: pointer;
  background: transparent;
}

.module-tree-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.expand-icon {
  font-size: 14px;
  color: #6c757d;
  transition: transform 0.3s;
  width: 16px;
}

.module-tree-icon {
  font-size: 24px;
  color: #3b82f6;
}

.module-tree-details {
  flex: 1;
}

.module-tree-name {
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
  margin: 0 0 4px 0;
}

.module-tree-description {
  font-size: 13px;
  color: #6c757d;
  margin: 0;
}

.module-tree-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.module-tree-toggle {
  position: relative;
  display: inline-block;
  width: 50px;
  height: 26px;
}

.module-tree-toggle input {
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

.module-tree-toggle input:checked + .toggle-slider {
  background-color: #3b82f6;
}

.module-tree-toggle input:checked + .toggle-slider:before {
  transform: translateX(24px);
}

.module-retention-config {
  padding: 12px 0 12px 32px;
  background: transparent;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.retention-config-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.retention-config-row label {
  font-size: 14px;
  font-weight: 500;
  color: #495057;
  min-width: 120px;
}

.retention-inputs {
  display: flex;
  gap: 8px;
}

.retention-input-small {
  width: 80px;
  padding: 6px 10px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 13px;
}

.disposal-select-small {
  width: 180px;
  padding: 6px 10px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 13px;
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

.pages-list-container {
  border: none;
  background: transparent;
  margin-left: 32px;
  padding: 0;
}

.pages-list-header {
  padding: 12px 0;
  background: transparent;
  border: none;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pages-list-header h5 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #495057;
  display: flex;
  align-items: center;
  gap: 8px;
}

.pages-count {
  font-size: 12px;
  color: #6c757d;
  background: #e9ecef;
  padding: 4px 10px;
  border-radius: 12px;
}

.pages-list {
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.page-item-row {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 10px 0;
  background: transparent;
  border: none;
  transition: none;
}

.page-item-name {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 0;
}

.page-icon-small {
  font-size: 16px;
  color: #6c757d;
  flex-shrink: 0;
}

.page-name-text {
  font-size: 14px;
  font-weight: 500;
  color: #2c3e50;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.page-toggle-compact {
  position: relative;
  display: inline-block;
  width: 44px;
  height: 24px;
  flex-shrink: 0;
}

.page-toggle-compact input {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-slider-compact {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #ccc;
  transition: 0.3s;
  border-radius: 24px;
}

.toggle-slider-compact:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: 0.3s ease;
  border-radius: 50%;
}

.page-toggle-compact input:checked + .toggle-slider-compact {
  background-color: #3b82f6;
}

.page-toggle-compact input:checked + .toggle-slider-compact:before {
  transform: translateX(20px);
}

.page-toggle-compact input:disabled + .toggle-slider-compact {
  opacity: 0.6;
  cursor: not-allowed;
}

.page-days-box {
  display: flex;
  align-items: center;
  gap: 6px;
  background: transparent;
  border: none;
  padding: 0;
  min-width: 100px;
}

.days-input {
  width: 70px;
  border: none;
  outline: none;
  font-size: 14px;
  font-weight: 500;
  color: #2c3e50;
  text-align: center;
  background: transparent;
  padding: 4px 8px;
  -moz-appearance: textfield;
}

.days-input::-webkit-outer-spin-button,
.days-input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.days-input:disabled {
  color: #94a3b8;
  cursor: not-allowed;
  opacity: 0.6;
}

.days-input::placeholder {
  color: #9ca3af;
  font-weight: 400;
}

.days-suffix {
  font-size: 13px;
  color: #6c757d;
  font-weight: 500;
  white-space: nowrap;
  flex-shrink: 0;
}

.no-pages {
  text-align: center;
  padding: 40px 20px;
  color: #6c757d;
}

.no-pages i {
  font-size: 32px;
  margin-bottom: 12px;
  display: block;
  color: #ced4da;
}

.tree-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 24px;
}

.btn-save-all {
  padding: 12px 24px;
  background: #007bff;
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
  background: #0056b3;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 123, 255, 0.3);
}

.btn-save-all:disabled {
  opacity: 0.6;
  cursor: not-allowed;
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

.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.3s ease;
  max-height: 1000px;
  overflow: hidden;
}

.slide-down-enter-from,
.slide-down-leave-to {
  max-height: 0;
  opacity: 0;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
