<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-foreground">OCR & Extraction Console</h1>
        <p class="text-muted-foreground">Process and extract data from submitted plans</p>
      </div>
    </div>

    <div class="card">
      <div class="card-header">
        <h3 class="card-title flex items-center gap-2">
          <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
          </svg>
          Filter Plans
        </h3>
      </div>
      <div class="card-content">
        <div class="grid grid-cols-4 gap-4">
          <div>
            <label class="label">Strategy Name/ID</label>
            <input 
              class="input"
              placeholder="Search strategies..."
              v-model="filters.strategy"
            />
          </div>
          <div>
            <label class="label">Vendor</label>
            <input 
              class="input"
              placeholder="Filter by vendor..."
              v-model="filters.vendor"
            />
          </div>
          <div>
            <label class="label">Plan Type</label>
            <select class="select" v-model="filters.planType">
              <option value="">All types</option>
              <option value="BCP">BCP</option>
              <option value="DRP">DRP</option>
            </select>
          </div>
          <div>
            <label class="label">Status</label>
            <select class="select" v-model="filters.status">
              <option value="">All statuses</option>
              <option value="SUBMITTED">Submitted</option>
              <option value="OCR_IN_PROGRESS">OCR In Progress</option>
              <option value="OCR_COMPLETED">OCR Completed</option>
            </select>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Content Area -->
    <div class="ocr-main-layout">
      <!-- Plans Table Section -->
      <div class="ocr-table-section" :class="{ 'ocr-table-section--with-panel': selectedPlan }">
        <div class="card">
          <div class="card-header">
            <h3 class="card-title flex items-center justify-between">
              <span>Plans Awaiting OCR</span>
              <div class="flex items-center gap-2">
                <span class="text-sm text-muted-foreground">{{ plans.length }} plans</span>
                <button 
                  v-if="selectedPlan"
                  class="btn btn--ghost btn--sm"
                  @click="closePlanDetails"
                  title="Close Details Panel"
                >
                  <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                  </svg>
                </button>
              </div>
            </h3>
          </div>
          <div class="card-content">
            <!-- Loading State -->
            <div v-if="loading" class="flex items-center justify-center py-8">
              <div class="text-muted-foreground">Loading plans...</div>
            </div>
            
            <!-- Error State -->
            <div v-else-if="error" class="flex items-center justify-center py-8">
              <div class="text-red-600">Error: {{ error }}</div>
            </div>
            
            <!-- Empty State -->
            <div v-else-if="plans.length === 0" class="flex items-center justify-center py-8">
              <div class="text-muted-foreground">No plans found matching your criteria.</div>
            </div>
            
            <!-- Plans Table -->
            <div v-else class="table-container">
              <table class="table">
                <thead>
                  <tr>
                    <th>Plan ID</th>
                    <th>Strategy</th>
                    <th>Plan Name</th>
                    <th>Type</th>
                    <th>Version</th>
                    <th>Vendor</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr 
                    v-for="plan in plans" 
                    :key="plan.plan_id"
                    :class="{ 'table-row--selected': selectedPlan === plan.plan_id }"
                  >
                    <td class="font-medium">{{ plan.plan_id }}</td>
                    <td>
                      <div>
                        <div class="font-medium">{{ plan.strategy_name }}</div>
                        <div class="text-sm text-muted-foreground">ID: {{ plan.strategy_id }}</div>
                      </div>
                    </td>
                    <td>{{ plan.plan_name }}</td>
                    <td>
                      <span :class="['badge', plan.plan_type === 'BCP' ? 'badge--default' : 'badge--secondary']">
                        {{ plan.plan_type }}
                      </span>
                    </td>
                    <td>{{ plan.version }}</td>
                    <td>{{ plan.vendor_name }}</td>
                    <td>
                      <span :class="['badge', getStatusColor(plan.status)]">
                        {{ plan.status.replace('_', ' ') }}
                      </span>
                    </td>
                    <td>
                      <div class="flex gap-1">
                        <button 
                          class="btn btn--ghost btn--sm"
                          :class="{ 'btn--primary': selectedPlan === plan.plan_id }"
                          @click="selectedPlan = plan.plan_id"
                          title="View Plan Details"
                        >
                          <svg class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                          </svg>
                        </button>
                        <button 
                          v-if="plan.status === 'SUBMITTED'"
                          class="btn btn--ghost btn--sm"
                          @click="runOCR(plan.plan_id)"
                          title="Start OCR Processing"
                        >
                          <svg class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.828 14.828a4 4 0 01-5.656 0M9 10h1m4 0h1m-6 4h.01M19 10a9 9 0 11-18 0 9 9 0 0118 0z"/>
                          </svg>
                        </button>
                        <button 
                          v-if="plan.status === 'OCR_COMPLETED'"
                          class="btn btn--ghost btn--sm"
                          @click="assignForEvaluation(plan.plan_id)"
                          title="Assign for Evaluation"
                        >
                          <svg class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z"/>
                          </svg>
                        </button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      <!-- Plan Details Side Panel -->
      <div v-if="selectedPlan && selectedPlanData" class="ocr-details-panel">
        <div class="panel-header">
          <div class="panel-title">
            <h3 class="text-lg font-semibold">Plan Details</h3>
            <div class="panel-subtitle">
              <span class="font-medium">{{ selectedPlanData.plan_name }}</span>
              <span class="text-sm text-muted-foreground">ID: {{ selectedPlan }}</span>
            </div>
          </div>
          <div class="panel-actions">
            <div class="flex items-center gap-2">
              <span :class="['badge', selectedPlanData.plan_type === 'BCP' ? 'badge--default' : 'badge--secondary']">
                {{ selectedPlanData.plan_type }}
              </span>
              <span :class="['badge', getStatusColor(selectedPlanData.status)]">
                {{ selectedPlanData.status.replace('_', ' ') }}
              </span>
            </div>
            <button 
              class="btn btn--ghost btn--sm"
              @click="closePlanDetails"
              title="Close Panel"
            >
              <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </div>
        </div>

        <div class="panel-content">
          <div class="panel-section">
            <h4 class="panel-section-title">Source Document</h4>
            <div class="document-preview">
              <div class="document-preview-placeholder">
                <div class="text-4xl mb-2">📄</div>
                <p class="text-sm text-muted-foreground">PDF Preview</p>
                <p class="text-xs text-muted-foreground">{{ selectedPlanData.plan_name }}.pdf</p>
                <p class="text-xs text-muted-foreground mt-1">{{ selectedPlanData.file_uri }}</p>
              </div>
            </div>
          </div>

          <div class="panel-section">
            <h4 class="panel-section-title">Extracted Fields</h4>
            
            <div class="tabs">
              <div class="tabs-list">
                <button
                  :class="['tabs-trigger', { 'data-state-active': activeTab === 'bcp' }]"
                  :data-state="activeTab === 'bcp' ? 'active' : 'inactive'"
                  :disabled="selectedPlanData.plan_type !== 'BCP'"
                  @click="activeTab = 'bcp'"
                >
                  BCP Extract
                </button>
                <button
                  :class="['tabs-trigger', { 'data-state-active': activeTab === 'drp' }]"
                  :data-state="activeTab === 'drp' ? 'active' : 'inactive'"
                  :disabled="selectedPlanData.plan_type !== 'DRP'"
                  @click="activeTab = 'drp'"
                >
                  DRP Extract
                </button>
              </div>
              
              <div v-show="activeTab === 'bcp'" class="tabs-content">
                <div class="form-grid">
                  <div class="form-field">
                    <label class="label">Purpose & Scope</label>
                    <textarea 
                      class="textarea h-20" 
                      placeholder="Enter purpose and scope..." 
                      v-model="extractedData.purpose_scope"
                    />
                  </div>
                  <div class="form-field">
                    <label class="label">Regulatory References</label>
                    <input 
                      class="input" 
                      placeholder='["SOX", "Basel III", "PCI DSS"]' 
                      v-model="extractedData.regulatory_references"
                    />
                  </div>
                  <div class="form-field">
                    <label class="label">Critical Services</label>
                    <input 
                      class="input" 
                      placeholder='["Payments","Collections"]' 
                      v-model="extractedData.critical_services"
                    />
                  </div>
                  <div class="form-field">
                    <label class="label">Internal Dependencies</label>
                    <input 
                      class="input" 
                      placeholder='["IT Systems", "HR Department"]' 
                      v-model="extractedData.dependencies_internal"
                    />
                  </div>
                  <div class="form-field">
                    <label class="label">External Dependencies</label>
                    <input 
                      class="input" 
                      placeholder='["Cloud Provider", "Payment Gateway"]' 
                      v-model="extractedData.dependencies_external"
                    />
                  </div>
                  <div class="form-field form-field--full">
                    <label class="label">Risk Assessment Summary</label>
                    <textarea 
                      class="textarea h-20" 
                      placeholder="Enter risk assessment..." 
                      v-model="extractedData.risk_assessment_summary"
                    />
                  </div>
                  <div class="form-field form-field--full">
                    <label class="label">Business Impact Analysis Summary</label>
                    <textarea 
                      class="textarea h-20" 
                      placeholder="Enter business impact analysis..." 
                      v-model="extractedData.bia_summary"
                    />
                  </div>
                  <div class="form-field">
                    <label class="label">RTO Targets</label>
                    <input 
                      class="input" 
                      placeholder='{"Payments":"4h","Collections":"2h"}' 
                      v-model="extractedData.rto_targets"
                    />
                  </div>
                  <div class="form-field">
                    <label class="label">RPO Targets</label>
                    <input 
                      class="input" 
                      placeholder='{"Payments":"15m","Collections":"30m"}' 
                      v-model="extractedData.rpo_targets"
                    />
                  </div>
                  <div class="form-field">
                    <label class="label">Incident Types</label>
                    <input 
                      class="input" 
                      placeholder='["System Failure", "Cyber Attack"]' 
                      v-model="extractedData.incident_types"
                    />
                  </div>
                  <div class="form-field">
                    <label class="label">Alternate Work Locations</label>
                    <input 
                      class="input" 
                      placeholder='["Remote Office", "Backup Site"]' 
                      v-model="extractedData.alternate_work_locations"
                    />
                  </div>
                  <div class="form-field form-field--full">
                    <label class="label">Internal Communication Plan</label>
                    <textarea 
                      class="textarea h-20" 
                      placeholder="Enter internal communication plan..." 
                      v-model="extractedData.communication_plan_internal"
                    />
                  </div>
                  <div class="form-field form-field--full">
                    <label class="label">Bank Communication Plan</label>
                    <textarea 
                      class="textarea h-20" 
                      placeholder="Enter bank communication plan..." 
                      v-model="extractedData.communication_plan_bank"
                    />
                  </div>
                  <div class="form-field">
                    <label class="label">Roles & Responsibilities</label>
                    <input 
                      class="input" 
                      placeholder='["Incident Commander", "Communication Lead"]' 
                      v-model="extractedData.roles_responsibilities"
                    />
                  </div>
                  <div class="form-field form-field--full">
                    <label class="label">Training & Testing Schedule</label>
                    <textarea 
                      class="textarea h-20" 
                      placeholder="Enter training and testing schedule..." 
                      v-model="extractedData.training_testing_schedule"
                    />
                  </div>
                  <div class="form-field form-field--full">
                    <label class="label">Maintenance & Review Cycle</label>
                    <textarea 
                      class="textarea h-20" 
                      placeholder="Enter maintenance and review cycle..." 
                      v-model="extractedData.maintenance_review_cycle"
                    />
                  </div>
                </div>
              </div>

              <div v-show="activeTab === 'drp'" class="tabs-content">
                <div class="form-grid">
                  <div class="form-field form-field--full">
                    <label class="label">Purpose & Scope</label>
                    <textarea 
                      class="textarea h-20" 
                      placeholder="Enter purpose and scope..." 
                      v-model="extractedData.purpose_scope"
                    />
                  </div>
                  <div class="form-field">
                    <label class="label">Regulatory References</label>
                    <input 
                      class="input" 
                      placeholder='["SOX", "Basel III", "PCI DSS"]' 
                      v-model="extractedData.regulatory_references"
                    />
                  </div>
                  <div class="form-field">
                    <label class="label">Critical Systems</label>
                    <input 
                      class="input" 
                      placeholder='["Core Banking","Payment Gateway"]' 
                      v-model="extractedData.critical_systems"
                    />
                  </div>
                  <div class="form-field">
                    <label class="label">Critical Applications</label>
                    <input 
                      class="input" 
                      placeholder='["Loan System","Trading Platform"]' 
                      v-model="extractedData.critical_applications"
                    />
                  </div>
                  <div class="form-field">
                    <label class="label">Databases</label>
                    <input 
                      class="input" 
                      placeholder='["Customer DB","Transaction DB"]' 
                      v-model="extractedData.databases_list"
                    />
                  </div>
                  <div class="form-field">
                    <label class="label">Supporting Infrastructure</label>
                    <input 
                      class="input" 
                      placeholder='["Network","Storage","Servers"]' 
                      v-model="extractedData.supporting_infrastructure"
                    />
                  </div>
                  <div class="form-field">
                    <label class="label">Third Party Services</label>
                    <input 
                      class="input" 
                      placeholder='["Cloud Provider","SMS Gateway"]' 
                      v-model="extractedData.third_party_services"
                    />
                  </div>
                  <div class="form-field">
                    <label class="label">Disaster Scenarios</label>
                    <input 
                      class="input" 
                      placeholder='["Fire","Flood","Cyber Attack"]' 
                      v-model="extractedData.disaster_scenarios"
                    />
                  </div>
                  <div class="form-field form-field--full">
                    <label class="label">Disaster Declaration Process</label>
                    <textarea 
                      class="textarea h-20" 
                      placeholder="Enter disaster declaration process..." 
                      v-model="extractedData.disaster_declaration_process"
                    />
                  </div>
                  <div class="form-field form-field--full">
                    <label class="label">Data Backup Strategy</label>
                    <textarea 
                      class="textarea h-20" 
                      placeholder="Enter backup strategy..." 
                      v-model="extractedData.data_backup_strategy"
                    />
                  </div>
                  <div class="form-field">
                    <label class="label">Recovery Site Details</label>
                    <input 
                      class="input" 
                      placeholder="Primary DR site location and details" 
                      v-model="extractedData.recovery_site_details"
                    />
                  </div>
                  <div class="form-field form-field--full">
                    <label class="label">Failover Procedures</label>
                    <textarea 
                      class="textarea h-20" 
                      placeholder="Enter failover procedures..." 
                      v-model="extractedData.failover_procedures"
                    />
                  </div>
                  <div class="form-field form-field--full">
                    <label class="label">Failback Procedures</label>
                    <textarea 
                      class="textarea h-20" 
                      placeholder="Enter failback procedures..." 
                      v-model="extractedData.failback_procedures"
                    />
                  </div>
                  <div class="form-field form-field--full">
                    <label class="label">Network Recovery Steps</label>
                    <textarea 
                      class="textarea h-20" 
                      placeholder="Enter network recovery steps..." 
                      v-model="extractedData.network_recovery_steps"
                    />
                  </div>
                  <div class="form-field">
                    <label class="label">Application Restoration Order</label>
                    <input 
                      class="input" 
                      placeholder='["Critical Apps First", "Supporting Apps Second"]' 
                      v-model="extractedData.application_restoration_order"
                    />
                  </div>
                  <div class="form-field">
                    <label class="label">RTO Targets</label>
                    <input 
                      class="input" 
                      placeholder='{"Critical Systems":"2h"}' 
                      v-model="extractedData.rto_targets"
                    />
                  </div>
                  <div class="form-field">
                    <label class="label">RPO Targets</label>
                    <input 
                      class="input" 
                      placeholder='{"Critical Systems":"30m"}' 
                      v-model="extractedData.rpo_targets"
                    />
                  </div>
                  <div class="form-field form-field--full">
                    <label class="label">Testing & Validation Schedule</label>
                    <textarea 
                      class="textarea h-20" 
                      placeholder="Enter testing and validation schedule..." 
                      v-model="extractedData.testing_validation_schedule"
                    />
                  </div>
                  <div class="form-field form-field--full">
                    <label class="label">Maintenance & Review Cycle</label>
                    <textarea 
                      class="textarea h-20" 
                      placeholder="Enter maintenance and review cycle..." 
                      v-model="extractedData.maintenance_review_cycle"
                    />
                  </div>
                </div>
              </div>
            </div>

            <div class="panel-actions">
              <button 
                class="btn btn--primary" 
                @click="saveExtractedData"
                :disabled="saving"
              >
                <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3-3m0 0l-3 3m3-3v12"/>
                </svg>
                {{ saving ? 'Saving...' : 'Save Extracted Data' }}
              </button>
              <button 
                class="btn btn--outline" 
                @click="markOCRCompleted"
                :disabled="saving"
              >
                <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
                Mark OCR Completed
              </button>
              <button 
                class="btn btn--outline" 
                @click="assignForEvaluation(selectedPlanData.plan_id)"
                :disabled="saving"
              >
                <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z"/>
                </svg>
                Assign for Evaluation
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import './OcrExtraction.css'
import { ref, computed, onMounted, watch } from 'vue'
import http from '../../api/http.js'
import { useNotifications } from '@/composables/useNotifications'
import { PopupService } from '@/popup/popupService'
import notificationService from '@/services/notificationService'
import loggingService from '@/services/loggingService'

// Data state
const { showSuccess, showError, showWarning, showInfo } = useNotifications()

const plans = ref([])
const selectedPlanData = ref(null)
const loading = ref(false)
const error = ref(null)
const saving = ref(false)

// UI state
const selectedPlan = ref<number | null>(null)
const activeTab = ref("bcp")
const filters = ref({
  strategy: "",
  vendor: "",
  planType: "",
  status: ""
})

// Extracted data state
const extractedData = ref({
  // BCP fields
  purpose_scope: '',
  regulatory_references: '',
  critical_services: '',
  dependencies_internal: '',
  dependencies_external: '',
  risk_assessment_summary: '',
  bia_summary: '',
  rto_targets: '',
  rpo_targets: '',
  incident_types: '',
  alternate_work_locations: '',
  communication_plan_internal: '',
  communication_plan_bank: '',
  roles_responsibilities: '',
  training_testing_schedule: '',
  maintenance_review_cycle: '',
  
  // DRP fields
  critical_systems: '',
  critical_applications: '',
  databases_list: '',
  supporting_infrastructure: '',
  third_party_services: '',
  disaster_scenarios: '',
  disaster_declaration_process: '',
  data_backup_strategy: '',
  recovery_site_details: '',
  failover_procedures: '',
  failback_procedures: '',
  network_recovery_steps: '',
  application_restoration_order: '',
  testing_validation_schedule: ''
})

// Fetch plans from API
const fetchPlans = async () => {
  loading.value = true
  error.value = null
  
  try {
    // Build query parameters
    const params = new URLSearchParams()
    
    if (filters.value.strategy) params.append('strategy', filters.value.strategy)
    if (filters.value.vendor) params.append('vendor', filters.value.vendor)
    if (filters.value.planType) params.append('plan_type', filters.value.planType)
    if (filters.value.status) params.append('status', filters.value.status)
    
    const queryString = params.toString()
    const url = queryString ? `/bcpdrp/ocr/plans/?${queryString}` : '/bcpdrp/ocr/plans/'
    
    const response = await http.get(url)
    plans.value = response.data.plans || []
  } catch (err) {
    error.value = err.message || 'Failed to fetch plans'
    console.error('Error fetching plans:', err)
  } finally {
    loading.value = false
  }
}

// Fetch plan details
const fetchPlanDetails = async (planId: number) => {
  try {
    const response = await http.get(`/bcpdrp/ocr/plans/${planId}/`)
    selectedPlanData.value = response.data
    
    // Load existing extracted data if available
    if (response.data.extracted_data) {
      const data = response.data.extracted_data
      
      // BCP fields
      extractedData.value.purpose_scope = data.purpose_scope || ''
      extractedData.value.regulatory_references = Array.isArray(data.regulatory_references) ? JSON.stringify(data.regulatory_references) : (data.regulatory_references || '')
      extractedData.value.critical_services = Array.isArray(data.critical_services) ? JSON.stringify(data.critical_services) : (data.critical_services || '')
      extractedData.value.dependencies_internal = Array.isArray(data.dependencies_internal) ? JSON.stringify(data.dependencies_internal) : (data.dependencies_internal || '')
      extractedData.value.dependencies_external = Array.isArray(data.dependencies_external) ? JSON.stringify(data.dependencies_external) : (data.dependencies_external || '')
      extractedData.value.risk_assessment_summary = data.risk_assessment_summary || ''
      extractedData.value.bia_summary = data.bia_summary || ''
      extractedData.value.rto_targets = typeof data.rto_targets === 'object' ? JSON.stringify(data.rto_targets) : (data.rto_targets || '')
      extractedData.value.rpo_targets = typeof data.rpo_targets === 'object' ? JSON.stringify(data.rpo_targets) : (data.rpo_targets || '')
      extractedData.value.incident_types = Array.isArray(data.incident_types) ? JSON.stringify(data.incident_types) : (data.incident_types || '')
      extractedData.value.alternate_work_locations = Array.isArray(data.alternate_work_locations) ? JSON.stringify(data.alternate_work_locations) : (data.alternate_work_locations || '')
      extractedData.value.communication_plan_internal = data.communication_plan_internal || ''
      extractedData.value.communication_plan_bank = data.communication_plan_bank || ''
      extractedData.value.roles_responsibilities = Array.isArray(data.roles_responsibilities) ? JSON.stringify(data.roles_responsibilities) : (data.roles_responsibilities || '')
      extractedData.value.training_testing_schedule = data.training_testing_schedule || ''
      extractedData.value.maintenance_review_cycle = data.maintenance_review_cycle || ''
      
      // DRP fields
      extractedData.value.critical_systems = Array.isArray(data.critical_systems) ? JSON.stringify(data.critical_systems) : (data.critical_systems || '')
      extractedData.value.critical_applications = Array.isArray(data.critical_applications) ? JSON.stringify(data.critical_applications) : (data.critical_applications || '')
      extractedData.value.databases_list = Array.isArray(data.databases_list) ? JSON.stringify(data.databases_list) : (data.databases_list || '')
      extractedData.value.supporting_infrastructure = Array.isArray(data.supporting_infrastructure) ? JSON.stringify(data.supporting_infrastructure) : (data.supporting_infrastructure || '')
      extractedData.value.third_party_services = Array.isArray(data.third_party_services) ? JSON.stringify(data.third_party_services) : (data.third_party_services || '')
      extractedData.value.disaster_scenarios = Array.isArray(data.disaster_scenarios) ? JSON.stringify(data.disaster_scenarios) : (data.disaster_scenarios || '')
      extractedData.value.disaster_declaration_process = data.disaster_declaration_process || ''
      extractedData.value.data_backup_strategy = data.data_backup_strategy || ''
      extractedData.value.recovery_site_details = data.recovery_site_details || ''
      extractedData.value.failover_procedures = data.failover_procedures || ''
      extractedData.value.failback_procedures = data.failback_procedures || ''
      extractedData.value.network_recovery_steps = data.network_recovery_steps || ''
      extractedData.value.application_restoration_order = Array.isArray(data.application_restoration_order) ? JSON.stringify(data.application_restoration_order) : (data.application_restoration_order || '')
      extractedData.value.testing_validation_schedule = data.testing_validation_schedule || ''
    } else {
      // Reset extracted data if no existing data
      Object.keys(extractedData.value).forEach(key => {
        extractedData.value[key] = ''
      })
    }
    
  } catch (err) {
    error.value = err.message || 'Failed to fetch plan details'
    console.error('Error fetching plan details:', err)
  }
}

// Load plans on component mount
onMounted(async () => {
  await loggingService.logPageView('BCP', 'OCR Extraction')
  await fetchPlans()
})

// Watch for filter changes and refetch data
watch(filters, () => {
  fetchPlans()
}, { deep: true })

// Watch for selected plan changes
watch(selectedPlan, (newPlanId) => {
  if (newPlanId) {
    fetchPlanDetails(newPlanId)
  } else {
    selectedPlanData.value = null
  }
})

// Close plan details panel
const closePlanDetails = () => {
  selectedPlan.value = null
  selectedPlanData.value = null
}

const getStatusColor = (status: string) => {
  switch (status) {
    case "SUBMITTED": return "bg-blue-100 text-blue-800"
    case "OCR_IN_PROGRESS": return "bg-yellow-100 text-yellow-800"
    case "OCR_COMPLETED": return "bg-green-100 text-green-800"
    default: return "bg-gray-100 text-gray-800"
  }
}

const runOCR = async (planId: number) => {
  try {
    await http.patch(`/bcpdrp/ocr/plans/${planId}/status/`, {
      status: 'OCR_IN_PROGRESS'
    })
    PopupService.success('Document processing has been initiated', 'OCR Started')
    // Create notification
    await notificationService.createOCRNotification('ocr_started', { plan_id: planId })
    fetchPlans() // Refresh the plans list
  } catch (err) {
    PopupService.error(`Error starting OCR: ${err.message}`, 'OCR Failed')
    // Create error notification
    await notificationService.createBCPErrorNotification('ocr_start', err.message, {
      title: 'OCR Start Failed',
      plan_id: planId
    })
    console.error('Error starting OCR:', err)
  }
}

const saveExtractedData = async () => {
  if (!selectedPlan.value) return
  
  saving.value = true
  try {
    // Prepare data for saving - convert JSON strings to objects where needed
    const dataToSave = { ...extractedData.value }
    
    // Convert JSON strings to objects for fields that expect arrays/objects
    const jsonFields = [
      'regulatory_references', 'critical_services', 'dependencies_internal', 'dependencies_external',
      'rto_targets', 'rpo_targets', 'incident_types', 'alternate_work_locations',
      'roles_responsibilities', 'critical_systems', 'critical_applications', 
      'databases_list', 'supporting_infrastructure', 'third_party_services',
      'disaster_scenarios', 'application_restoration_order'
    ]
    
    jsonFields.forEach(field => {
      if (dataToSave[field] && typeof dataToSave[field] === 'string') {
        try {
          dataToSave[field] = JSON.parse(dataToSave[field])
        } catch (e) {
          // If parsing fails, keep as string
          console.warn(`Failed to parse JSON for field ${field}:`, e)
        }
      }
    })
    
    await http.post(`/bcpdrp/ocr/plans/${selectedPlan.value}/extract/`, {
      extracted_data: dataToSave
    })
    
    PopupService.success('Extracted information has been saved successfully', 'Data Saved')
    // Create notification
    await notificationService.createOCRNotification('data_saved', { plan_id: selectedPlan.value })
    // Refresh plan details to show saved data
    fetchPlanDetails(selectedPlan.value)
  } catch (err) {
    PopupService.error(`Error saving data: ${err.message}`, 'Save Failed')
    // Create error notification
    await notificationService.createBCPErrorNotification('save_extracted_data', err.message, {
      title: 'Data Save Failed',
      plan_id: selectedPlan.value
    })
    console.error('Error saving extracted data:', err)
  } finally {
    saving.value = false
  }
}

const markOCRCompleted = async () => {
  if (!selectedPlan.value) return
  
  try {
    await http.patch(`/bcpdrp/ocr/plans/${selectedPlan.value}/status/`, {
      status: 'OCR_COMPLETED'
    })
    PopupService.success('Plan marked as ready for evaluation', 'OCR Completed')
    // Create notification
    await notificationService.createOCRNotification('ocr_completed', { plan_id: selectedPlan.value })
    fetchPlans() // Refresh the plans list
    fetchPlanDetails(selectedPlan.value) // Refresh plan details
  } catch (err) {
    PopupService.error(`Error updating status: ${err.message}`, 'Update Failed')
    // Create error notification
    await notificationService.createBCPErrorNotification('mark_ocr_completed', err.message, {
      title: 'OCR Completion Failed',
      plan_id: selectedPlan.value
    })
    console.error('Error updating OCR status:', err)
  }
}

const assignForEvaluation = async (planId: number) => {
  try {
    await http.patch(`/bcpdrp/ocr/plans/${planId}/status/`, {
      status: 'ASSIGNED_FOR_EVALUATION'
    })
    PopupService.success('Plan has been assigned to an evaluator', 'Assigned for Evaluation')
    // Create notification
    await notificationService.createOCRNotification('assigned_for_evaluation', { plan_id: planId })
    fetchPlans() // Refresh the plans list
  } catch (err) {
    PopupService.error(`Error assigning for evaluation: ${err.message}`, 'Assignment Failed')
    // Create error notification
    await notificationService.createBCPErrorNotification('assign_for_evaluation', err.message, {
      title: 'Assignment Failed',
      plan_id: planId
    })
    console.error('Error assigning for evaluation:', err)
  }
}
</script>
