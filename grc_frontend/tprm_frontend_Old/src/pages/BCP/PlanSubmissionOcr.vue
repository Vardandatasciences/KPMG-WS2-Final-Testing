<template>
  <div class="plan-submission-ocr">
    <!-- Page Header -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">OCR Extraction & Plan Assignment</h1>
        <p class="page-subtitle">Extract data from submitted plans and assign for evaluation</p>
      </div>
    </div>

    <!-- Breadcrumb Navigation -->
    <div class="breadcrumb-container">
      <nav class="breadcrumb">
        <div class="breadcrumb-item" :class="{ 'breadcrumb-item--active': currentStep === 1 }">
          <div class="breadcrumb-icon">
            <svg v-if="currentStep === 1" class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
            </svg>
            <span v-else class="breadcrumb-number">1</span>
          </div>
          <div class="breadcrumb-content">
            <span class="breadcrumb-title">OCR Extraction</span>
            <span class="breadcrumb-description">Extract data from submitted plans</span>
          </div>
        </div>
        
        <div class="breadcrumb-separator">
          <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
          </svg>
        </div>
        
        <div class="breadcrumb-item" :class="{ 'breadcrumb-item--active': currentStep === 2 }">
          <div class="breadcrumb-icon">
            <svg v-if="currentStep === 2" class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z"/>
            </svg>
            <span v-else class="breadcrumb-number">2</span>
          </div>
          <div class="breadcrumb-content">
            <span class="breadcrumb-title">Assign for Evaluation</span>
            <span class="breadcrumb-description">Assign plans for evaluation</span>
          </div>
        </div>
      </nav>
    </div>

    <!-- Step Content -->
    <div class="step-content">
      <!-- Step 1: OCR Extraction -->
      <div v-if="currentStep === 1" class="step-panel step-1">
        <div class="step-header">
          <h2 class="step-title">
            <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
            </svg>
            Step 1: Data Extraction
          </h2>
          <p class="step-description">Select a plan and extract data through OCR processing</p>
        </div>

        <div class="step-body">
          <!-- Plan Selection Dropdown -->
          <div class="plans-dropdown-section">
            <div class="plans-dropdown">
              <label class="modern-label">
                <div class="label-content">
                  <div class="label-icon">
                    <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                    </svg>
                  </div>
                  <span class="label-text">Select Plan</span>
                </div>
              </label>
              <div class="modern-dropdown" :class="{ 'is-open': isDropdownOpen }">
                <button 
                  class="modern-trigger"
                  @click="toggleDropdown"
                  @blur="closeDropdown"
                >
                  <div class="trigger-content">
                    <div v-if="selectedPlanId" class="selected-plan">
                      <div class="selected-plan-info">
                        <span class="selected-plan-name">{{ getSelectedPlanDisplay() }}</span>
                        <div class="selected-plan-badges">
                          <span :class="['mini-badge', getSelectedPlanType() === 'BCP' ? 'badge--default' : 'badge--secondary']">
                            {{ getSelectedPlanType() }}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div v-else class="placeholder-content">
                      <span class="placeholder-text">Choose a plan...</span>
                      <span class="placeholder-subtitle">Select from available BCP/DRP plans</span>
                    </div>
                  </div>
                  <div class="trigger-icon">
                    <svg class="dropdown-arrow" :class="{ 'rotated': isDropdownOpen }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
                    </svg>
                  </div>
                </button>
                <Transition name="dropdown">
                  <div v-if="isDropdownOpen" class="table-dropdown-menu">
                    <div class="table-header">
                      <span class="table-title">Available Plans</span>
                      <span class="table-count">{{ availablePlans.length }} plans</span>
                    </div>
                    <div class="table-container">
                      <div v-if="isLoadingPlans" class="loading-state">
                        <div class="loading-spinner"></div>
                        <p>Loading plans...</p>
                      </div>
                      <div v-else-if="availablePlans.length === 0" class="empty-state">
                        <div class="empty-icon">📄</div>
                        <p>No plans available</p>
                        <p class="empty-subtitle">No BCP/DRP plans found in the system</p>
                      </div>
                      <table v-else class="plans-table">
                        <thead>
                          <tr>
                            <th class="checkbox-column">
                              <input 
                                type="checkbox" 
                                class="select-all-checkbox"
                                :checked="isAllSelected"
                                @change="toggleSelectAll"
                              />
                            </th>
                            <th>Plan ID</th>
                            <th>Plan Name</th>
                            <th>Type</th>
                            <th>Strategy</th>
                            <th>Vendor</th>
                            <th>Criticality</th>
                            <th>Status</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr 
                            v-for="plan in availablePlans" 
                            :key="plan.plan_id"
                            class="plan-row"
                            :class="{ 'selected': selectedPlanId === plan.plan_id.toString() }"
                          >
                            <td class="checkbox-column">
                              <input 
                                type="checkbox" 
                                class="plan-checkbox"
                                :checked="selectedPlanId === plan.plan_id.toString()"
                                @change="selectPlan(plan)"
                              />
                            </td>
                            <td class="plan-id-cell">{{ plan.plan_id }}</td>
                            <td class="plan-name-cell">{{ plan.plan_name }}</td>
                            <td>
                              <span :class="['badge', plan.plan_type === 'BCP' ? 'badge--default' : 'badge--secondary']">
                                {{ plan.plan_type }}
                              </span>
                            </td>
                            <td class="strategy-cell">{{ plan.strategy_name }}</td>
                            <td class="vendor-cell">{{ plan.vendor_id }}</td>
                            <td class="criticality-cell">
                              {{ plan.criticality }}
                            </td>
                            <td class="status-cell">
                              {{ typeof plan.status === 'string' ? plan.status.replace(/_/g, ' ') : 'N/A' }}
                            </td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                </Transition>
              </div>
            </div>
          </div>

          <!-- Empty State -->
          <div v-if="!selectedPlanId" class="empty-state">
            <div class="empty-icon"></div>
            <p></p>
            <p class="empty-subtitle"></p>
          </div>
          
          <!-- Extraction Forms for Selected Plan -->
          <div v-else-if="selectedPlanId && selectedPlan && selectedPlan.plan_id" class="extraction-forms">
            <div class="extraction-form-card">
              <div class="form-card-header">
                <h3 class="plan-title">{{ selectedPlan.plan_name }}</h3>
                <div class="plan-badges">
                  <span :class="['type-badge', selectedPlan.plan_type === 'BCP' ? 'type-bcp' : 'type-drp']">
                    {{ selectedPlan.plan_type }}
                  </span>
                  <span class="plan-id-badge">ID: {{ selectedPlan.plan_id }}</span>
                </div>
              </div>
              
              <div class="extraction-form-content">
                <!-- Run OCR Button -->
                <div class="ocr-action-section">
                  <button 
                    class="btn btn--primary btn--lg btn-run-ocr"
                    @click="runOCR"
                    :disabled="saving || isRunningOCR"
                  >
                    <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                    </svg>
                    {{ isRunningOCR ? 'Running OCR...' : 'Run OCR' }}
                  </button>
                </div>

                <!-- BCP Extraction Fields -->
                <div v-if="selectedPlan.plan_type === 'BCP'" class="extraction-fields">
                  <div class="field-section">
                    <h4 class="section-title">Purpose & Scope</h4>
                    <div class="field-grid">
                      <div class="field-group field-group--full">
                        <label class="field-label">Purpose & Scope</label>
                        <textarea 
                          class="textarea h-24" 
                          placeholder="Enter the purpose and scope of the business continuity plan..."
                          v-model="extractedData.purpose_scope"
                        />
                      </div>
                    </div>
                  </div>
                  
                  <div class="field-section">
                    <h4 class="section-title">Regulatory & Compliance</h4>
                    <div class="field-grid">
                      <div class="field-group">
                        <label class="field-label">Regulatory References</label>
                        <input 
                          class="input" 
                          placeholder='["SOX", "Basel III", "PCI DSS"]' 
                          v-model="extractedData.regulatory_references"
                        />
                      </div>
                    </div>
                  </div>
                  
                  <div class="field-section">
                    <h4 class="section-title">Critical Services & Dependencies</h4>
                    <div class="field-grid">
                      <div class="field-group">
                        <label class="field-label">Critical Services</label>
                        <input 
                          class="input" 
                          placeholder='["Payments", "Collections", "Customer Service"]' 
                          v-model="extractedData.critical_services"
                        />
                      </div>
                      <div class="field-group">
                        <label class="field-label">Internal Dependencies</label>
                        <input 
                          class="input" 
                          placeholder='["IT Systems", "HR Department", "Finance"]' 
                          v-model="extractedData.dependencies_internal"
                        />
                      </div>
                      <div class="field-group">
                        <label class="field-label">External Dependencies</label>
                        <input 
                          class="input" 
                          placeholder='["Cloud Provider", "Payment Gateway", "Banking Partners"]' 
                          v-model="extractedData.dependencies_external"
                        />
                      </div>
                    </div>
                  </div>
                  
                  <div class="field-section">
                    <h4 class="section-title">Risk & Business Impact</h4>
                    <div class="field-grid">
                      <div class="field-group field-group--full">
                        <label class="field-label">Risk Assessment Summary</label>
                        <textarea 
                          class="textarea h-20" 
                          placeholder="Enter risk assessment summary..." 
                          v-model="extractedData.risk_assessment_summary"
                        />
                      </div>
                      <div class="field-group field-group--full">
                        <label class="field-label">Business Impact Analysis Summary</label>
                        <textarea 
                          class="textarea h-20" 
                          placeholder="Enter business impact analysis..." 
                          v-model="extractedData.bia_summary"
                        />
                      </div>
                    </div>
                  </div>
                  
                  <div class="field-section">
                    <h4 class="section-title">Recovery Objectives</h4>
                    <div class="field-grid">
                      <div class="field-group">
                        <label class="field-label">RTO Targets</label>
                        <input 
                          class="input" 
                          placeholder='{"Payments":"4h","Collections":"2h","Customer Service":"8h"}' 
                          v-model="extractedData.rto_targets"
                          title='Enter as JSON object: {"Service":"Time"}'
                        />
                      </div>
                      <div class="field-group">
                        <label class="field-label">RPO Targets</label>
                        <input 
                          class="input" 
                          placeholder='{"Payments":"15m","Collections":"30m","Customer Data":"1h"}' 
                          v-model="extractedData.rpo_targets"
                          title='Enter as JSON object: {"Service":"Time"}'
                        />
                      </div>
                    </div>
                  </div>
                  
                  <div class="field-section">
                    <h4 class="section-title">Communication & Roles</h4>
                    <div class="field-grid">
                      <div class="field-group field-group--full">
                        <label class="field-label">Internal Communication Plan</label>
                        <textarea 
                          class="textarea h-16" 
                          placeholder="Enter internal communication plan..." 
                          v-model="extractedData.communication_plan_internal"
                        />
                      </div>
                      <div class="field-group field-group--full">
                        <label class="field-label">Bank Communication Plan</label>
                        <textarea 
                          class="textarea h-16" 
                          placeholder="Enter bank communication plan..." 
                          v-model="extractedData.communication_plan_bank"
                        />
                      </div>
                      <div class="field-group">
                        <label class="field-label">Roles & Responsibilities</label>
                        <input 
                          class="input" 
                          placeholder='["Incident Commander", "Communication Lead", "Technical Lead"]' 
                          v-model="extractedData.roles_responsibilities"
                          title='Enter as JSON array: ["Role1", "Role2"]'
                        />
                      </div>
                    </div>
                  </div>
                </div>
                
                <!-- DRP Extraction Fields -->
                <div v-else class="extraction-fields">
                  <div class="field-section">
                    <h4 class="section-title">Purpose & Scope</h4>
                    <div class="field-grid">
                      <div class="field-group field-group--full">
                        <label class="field-label">Purpose & Scope</label>
                        <textarea 
                          class="textarea h-24" 
                          placeholder="Enter the purpose and scope of the disaster recovery plan..."
                          v-model="extractedData.purpose_scope"
                        />
                      </div>
                    </div>
                  </div>
                  
                  <div class="field-section">
                    <h4 class="section-title">Critical Systems & Infrastructure</h4>
                    <div class="field-grid">
                      <div class="field-group">
                        <label class="field-label">Critical Systems</label>
                        <input 
                          class="input" 
                          placeholder='["Core Banking", "Payment Gateway", "Database Servers"]' 
                          v-model="extractedData.critical_systems"
                        />
                      </div>
                      <div class="field-group">
                        <label class="field-label">Critical Applications</label>
                        <input 
                          class="input" 
                          placeholder='["Loan System", "Trading Platform", "Customer Portal"]' 
                          v-model="extractedData.critical_applications"
                        />
                      </div>
                      <div class="field-group">
                        <label class="field-label">Databases</label>
                        <input 
                          class="input" 
                          placeholder='["Customer DB", "Transaction DB", "Archive DB"]' 
                          v-model="extractedData.databases_list"
                        />
                      </div>
                      <div class="field-group">
                        <label class="field-label">Supporting Infrastructure</label>
                        <input 
                          class="input" 
                          placeholder='["Network", "Storage", "Servers", "Security"]' 
                          v-model="extractedData.supporting_infrastructure"
                        />
                      </div>
                      <div class="field-group">
                        <label class="field-label">Third Party Services</label>
                        <input 
                          class="input" 
                          placeholder='["Cloud Provider", "SMS Gateway", "Email Service"]' 
                          v-model="extractedData.third_party_services"
                        />
                      </div>
                    </div>
                  </div>
                  
                  <div class="field-section">
                    <h4 class="section-title">Recovery Objectives</h4>
                    <div class="field-grid">
                      <div class="field-group">
                        <label class="field-label">RTO Targets</label>
                        <input 
                          class="input" 
                          placeholder='{"Critical Systems":"2h","Applications":"4h","Databases":"1h"}' 
                          v-model="extractedData.rto_targets"
                        />
                      </div>
                      <div class="field-group">
                        <label class="field-label">RPO Targets</label>
                        <input 
                          class="input" 
                          placeholder='{"Critical Systems":"30m","Applications":"1h","Databases":"15m"}' 
                          v-model="extractedData.rpo_targets"
                        />
                      </div>
                    </div>
                  </div>
                  
                  <div class="field-section">
                    <h4 class="section-title">Recovery Procedures</h4>
                    <div class="field-grid">
                      <div class="field-group">
                        <label class="field-label">Recovery Site Details</label>
                        <input 
                          class="input" 
                          placeholder="Primary DR site location and details" 
                          v-model="extractedData.recovery_site_details"
                        />
                      </div>
                      <div class="field-group field-group--full">
                        <label class="field-label">Failover Procedures</label>
                        <textarea 
                          class="textarea h-16" 
                          placeholder="Enter failover procedures..." 
                          v-model="extractedData.failover_procedures"
                        />
                      </div>
                      <div class="field-group field-group--full">
                        <label class="field-label">Failback Procedures</label>
                        <textarea 
                          class="textarea h-16" 
                          placeholder="Enter failback procedures..." 
                          v-model="extractedData.failback_procedures"
                        />
                      </div>
                    </div>
                  </div>
                </div>
                
                <!-- Form Actions -->
                <div class="form-actions">
                  <button 
                    class="btn btn--outline"
                    @click="loadMockData"
                    :disabled="saving"
                  >
                    <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/>
                    </svg>
                    Load Data
                  </button>
                  <button 
                    class="btn btn--primary"
                    @click="saveExtractedData"
                    :disabled="saving"
                  >
                    <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3-3m0 0l-3 3m3-3v12"/>
                    </svg>
                    {{ saving ? 'Saving...' : 'Save Data' }}
                  </button>
                  <button 
                    class="btn btn--success"
                    @click="markPlanComplete"
                    :disabled="saving"
                  >
                    <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                    </svg>
                    Mark Complete & Continue
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Step 2: Assignment for Evaluation -->
      <div v-if="currentStep === 2" class="step-panel step-2">
        <div class="step-header">
          <h2 class="step-title">
            <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z"/>
            </svg>
            Step 2: Assign for Evaluation
          </h2>
          <p class="step-description">Assign your completed plans for evaluation</p>
        </div>

        <div class="step-body">
          <!-- Empty State -->
          <div v-if="!selectedPlanId" class="empty-state">
            <div class="empty-icon">📄</div>
            <p>No plan selected for assignment</p>
            <button @click="goToStep(1)" class="btn btn--primary">Go to Step 1</button>
          </div>
          
          <!-- Assignment Forms for Selected Plan -->
          <div v-else-if="selectedPlan && selectedPlan.plan_id" class="assignment-forms">
            <div class="assignment-form-card">
              <div class="form-card-header">
                <h3 class="plan-title">{{ selectedPlan.plan_name }}</h3>
                <div class="plan-badges">
                  <span :class="['type-badge', selectedPlan.plan_type === 'BCP' ? 'type-bcp' : 'type-drp']">
                    {{ selectedPlan.plan_type }}
                  </span>
                  <span class="plan-id-badge">ID: {{ selectedPlan.plan_id }}</span>
                </div>
              </div>
              
              <div class="assignment-form-content">
                <form @submit.prevent="createAssignment" class="assignment-form">
                  <!-- Row 1: Workflow Name, Assigner, Assigner Name -->
                  <div class="form-grid-3">
                    <div class="form-section">
                      <label class="field-label">Workflow Name <span class="text-destructive">*</span></label>
                      <input 
                        v-model="assignmentForm.workflow_name" 
                        type="text" 
                        class="input" 
                        required 
                        placeholder="Enter workflow name"
                      />
                    </div>
                    <div class="form-section">
                      <label class="field-label">Assigner <span class="text-destructive">*</span></label>
                      <select 
                        v-model="assignmentForm.assigner_id" 
                        class="select" 
                        required 
                        @change="onAssignerChange"
                        :disabled="isLoadingUsers"
                      >
                        <option value="">{{ isLoadingUsers ? 'Loading users...' : 'Select assigner' }}</option>
                        <option v-for="user in users" :key="user.user_id" :value="user.user_id">
                          {{ user.display_name }}
                        </option>
                      </select>
                    </div>
                    <div class="form-section">
                      <label class="field-label">Assigner Name</label>
                      <input 
                        v-model="assignmentForm.assigner_name" 
                        type="text" 
                        class="input" 
                        readonly
                        placeholder="Auto-filled from selection"
                      />
                    </div>
                  </div>

                  <!-- Row 2: Assignee Name, Assignee ID, Due Date -->
                  <div class="form-grid-3">
                    <div class="form-section">
                      <label class="field-label">Assignee Name</label>
                      <input 
                        v-model="assignmentForm.assignee_name" 
                        type="text" 
                        class="input" 
                        readonly
                        placeholder="Auto-filled from selection"
                      />
                    </div>
                    <div class="form-section">
                      <label class="field-label">Assignee <span class="text-destructive">*</span></label>
                      <select 
                        v-model="assignmentForm.assignee_id" 
                        class="select" 
                        :required="!noApprovalNeeded"
                        @change="onAssigneeChange"
                        :disabled="noApprovalNeeded || isLoadingUsers"
                      >
                        <option value="">{{ isLoadingUsers ? 'Loading users...' : 'Select assignee' }}</option>
                        <option v-for="user in users" :key="user.user_id" :value="user.user_id">
                          {{ user.display_name }}
                        </option>
                      </select>
                    </div>
                    <div class="form-section">
                      <label class="field-label">Due Date <span class="text-destructive">*</span></label>
                      <input 
                        v-model="assignmentForm.due_date" 
                        type="datetime-local" 
                        class="input" 
                        required
                      />
                    </div>
                  </div>

                  <!-- Row 3: No Approval Needed Checkbox -->
                  <div class="form-section mt-4">
                    <label class="flex items-center gap-2 cursor-pointer">
                      <input 
                        type="checkbox" 
                        v-model="noApprovalNeeded"
                        class="rounded border-gray-300 cursor-pointer"
                        @change="handleNoApprovalChange"
                      />
                      <span class="text-sm font-medium">No Approval Needed</span>
                    </label>
                    <p class="text-xs text-gray-500 ml-6 mt-1">
                      If checked, the assigner and assignee will be the same (current user), and approval will be automatic
                    </p>
                  </div>

                  <!-- Hidden fields for plan-specific data -->
                  <input type="hidden" :value="selectedPlan.plan_type" />
                  <input type="hidden" :value="selectedPlan.plan_id" />

                  <!-- Form Actions -->
                  <div class="form-actions">
                    <button 
                      type="submit" 
                      class="btn btn--primary"
                      :disabled="isSubmittingAssignment"
                    >
                      <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
                      </svg>
                      {{ isSubmittingAssignment ? 'Creating...' : 'Create Assignment' }}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import './PlanSubmissionOcr.css'
import { ref, computed, onMounted, watch, reactive } from 'vue'
import http from '../../api/http.js'
import api from '../../services/api_bcp.js'
import { useNotifications } from '@/composables/useNotifications'
import { PopupService } from '@/popup/popupService'
import loggingService from '@/services/loggingService'
import { useStore } from 'vuex'

// Define interfaces for type safety
interface ExtractedData {
  purpose_scope?: string
  regulatory_references?: string
  critical_services?: string
  dependencies_internal?: string
  dependencies_external?: string
  risk_assessment_summary?: string
  bia_summary?: string
  rto_targets?: string
  rpo_targets?: string
  incident_types?: string
  alternate_work_locations?: string
  communication_plan_internal?: string
  communication_plan_bank?: string
  roles_responsibilities?: string
  training_testing_schedule?: string
  maintenance_review_cycle?: string
  critical_systems?: string
  critical_applications?: string
  databases_list?: string
  supporting_infrastructure?: string
  third_party_services?: string
  disaster_scenarios?: string
  disaster_declaration_process?: string
  data_backup_strategy?: string
  recovery_site_details?: string
  failover_procedures?: string
  failback_procedures?: string
  network_recovery_steps?: string
  application_restoration_order?: string
  testing_validation_schedule?: string
}

// Data state
const { showSuccess, showError, showWarning, showInfo } = useNotifications()

// Vuex store
const store = useStore()

const saving = ref(false)
const submitting = ref(false)
const isRunningOCR = ref(false)

// Plan selection data
const availablePlans = ref([])
const selectedPlanId = ref("")
const selectedPlan = ref(null)
const isDropdownOpen = ref(false)
const isLoadingPlans = ref(false)

// Assignment data
const users = ref([])
const isLoadingUsers = ref(false)
const assignmentForm = ref({
  workflow_name: '',
  plan_type: '',
  assigner_id: '',
  assigner_name: '',
  assignee_id: '',
  assignee_name: '',
  object_type: 'PLAN',
  object_id: '',
  due_date: ''
})
const isSubmittingAssignment = ref(false)
const noApprovalNeeded = ref(false)

// UI state
const currentStep = ref(1)

// Extracted data state for selected plan
const extractedData = ref<ExtractedData>({})

// Computed properties

const isAllSelected = computed(() => {
  return availablePlans.value.length > 0 && availablePlans.value.every(plan => 
    selectedPlanId.value === plan.plan_id.toString()
  )
})

// Methods
const fetchPlans = async () => {
  isLoadingPlans.value = true
  try {
    console.log('Fetching plans from API endpoint: /api/bcpdrp/plans/')
    const response = await api.plans.list()
    
    const plans = (response as any).plans || (response as any).data?.plans
    
    if (plans && Array.isArray(plans)) {
      availablePlans.value = plans
      console.log('Successfully fetched plans:', plans.length, 'plans')
    } else {
      console.error('API returned no plans data or plans is not an array')
      availablePlans.value = []
    }
  } catch (error) {
    console.error('Error fetching plans from API:', error)
    availablePlans.value = []
    PopupService.error(`Failed to load plans: ${error.message}. Please check your connection and try again.`, 'Loading Failed')
  } finally {
    isLoadingPlans.value = false
  }
}

const toggleDropdown = () => {
  isDropdownOpen.value = !isDropdownOpen.value
}

const closeDropdown = () => {
  setTimeout(() => {
    isDropdownOpen.value = false
  }, 150)
}

const selectPlan = (plan) => {
  if (!plan || !plan.plan_id) {
    console.error('Invalid plan selected:', plan)
    return
  }
  
  selectedPlanId.value = plan.plan_id.toString()
  selectedPlan.value = plan
  isDropdownOpen.value = false
  
  console.log('Plan selected:', plan)
  
  // Initialize extracted data for the selected plan
  extractedData.value = initializeExtractedData(plan.plan_type)
  
  // Initialize assignment form
  assignmentForm.value = initializeAssignmentForm(plan.plan_type)
  assignmentForm.value.object_id = plan.plan_id
}

const toggleSelectAll = () => {
  if (isAllSelected.value) {
    selectedPlanId.value = ""
    selectedPlan.value = null
  } else {
    if (availablePlans.value.length > 0) {
      selectPlan(availablePlans.value[0])
    }
  }
}

const getSelectedPlanDisplay = () => {
  if (selectedPlan.value) {
    return `[${selectedPlan.value.plan_id}] ${selectedPlan.value.plan_name} (${selectedPlan.value.plan_type})`
  }
  return ""
}

const getSelectedPlanType = () => {
  return selectedPlan.value ? selectedPlan.value.plan_type : ""
}

const openPlanForExtraction = async (plan) => {
  console.log('Opening plan for extraction:', plan)
  selectPlan(plan)
}

const getCriticalityBadgeClass = (criticality) => {
  if (!criticality) return "badge--secondary"
  switch (criticality) {
    case "CRITICAL": return "badge--destructive"
    case "HIGH": return "badge--warning"
    case "MEDIUM": return "badge--secondary"
    case "LOW": return "badge--outline"
    default: return "badge--secondary"
  }
}

const getStatusBadgeClass = (status) => {
  if (!status) return "badge--secondary"
  switch (status) {
    case "SUBMITTED": return "badge--default"
    case "OCR_COMPLETED": return "badge--success"
    case "ASSIGNED_FOR_EVALUATION": return "badge--warning"
    case "APPROVED": return "badge--success"
    case "REJECTED": return "badge--destructive"
    case "REVISION_REQUESTED": return "badge--warning"
    default: return "badge--secondary"
  }
}


// Updated methods for new workflow

const initializeExtractedData = (planType: string): ExtractedData => {
  if (planType === 'BCP') {
    return {
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
      maintenance_review_cycle: ''
    }
  } else {
    return {
      purpose_scope: '',
      regulatory_references: '',
      critical_systems: '',
      critical_applications: '',
      databases_list: '',
      supporting_infrastructure: '',
      third_party_services: '',
      rto_targets: '',
      rpo_targets: '',
      disaster_scenarios: '',
      disaster_declaration_process: '',
      data_backup_strategy: '',
      recovery_site_details: '',
      failover_procedures: '',
      failback_procedures: '',
      network_recovery_steps: '',
      application_restoration_order: '',
      testing_validation_schedule: '',
      maintenance_review_cycle: ''
    }
  }
}

const initializeAssignmentForm = (planType: string) => {
  const tomorrow = new Date()
  tomorrow.setDate(tomorrow.getDate() + 1)
  
  const form = {
    workflow_name: `${planType} Evaluation Workflow`,
    plan_type: planType,
    assigner_id: '',
    assigner_name: '',
    assignee_id: '',
    assignee_name: '',
    object_type: 'PLAN',
    object_id: '',
    due_date: tomorrow.toISOString().slice(0, 16)
  }
  
  console.log('Initialized assignment form:', form)
  return form
}

const goToStep = (step: number) => {
  currentStep.value = step
  if (step === 2 && selectedPlan.value && selectedPlan.value.plan_id) {
    // Initialize assignment form for selected plan when going to step 2
    assignmentForm.value = initializeAssignmentForm(selectedPlan.value.plan_type)
    assignmentForm.value.object_id = selectedPlan.value.plan_id
    console.log('Initialized assignment form for plan:', selectedPlan.value.plan_id)
  }
}

// Step 3 - Assignment functions
const fetchUsers = async () => {
  isLoadingUsers.value = true
  try {
    console.log('Fetching users from API endpoint: /api/bcpdrp/users/')
    const response = await api.users.list()
    
    const usersData = (response as any).users || (response as any).data?.users
    
    if (usersData && Array.isArray(usersData)) {
      users.value = usersData
      console.log('Successfully fetched users:', usersData.length, 'users')
    } else {
      console.error('API returned no users data or users is not an array')
      users.value = []
    }
  } catch (error) {
    console.error('Error fetching users from API:', error)
    users.value = []
    PopupService.error(`Failed to load users: ${error.message}. Please check your connection and try again.`, 'Loading Failed')
  } finally {
    isLoadingUsers.value = false
  }
}

const onAssignerChange = () => {
  const selectedUser = users.value.find(user => user.user_id == assignmentForm.value.assigner_id)
  if (selectedUser) {
    assignmentForm.value.assigner_name = selectedUser.username
  } else {
    assignmentForm.value.assigner_name = ''
  }
}

const onAssigneeChange = () => {
  const selectedUser = users.value.find(user => user.user_id == assignmentForm.value.assignee_id)
  if (selectedUser) {
    assignmentForm.value.assignee_name = selectedUser.username
  } else {
    assignmentForm.value.assignee_name = ''
  }
}

const handleNoApprovalChange = () => {
  if (noApprovalNeeded.value) {
    // Try to get current logged in user from Vuex store first
    let currentUser = store.getters['auth/currentUser']
    
    // If not in store, try to get from localStorage as fallback
    if (!currentUser) {
      try {
        const userStr = localStorage.getItem('current_user')
        if (userStr) {
          currentUser = JSON.parse(userStr)
          console.log('Retrieved user from localStorage:', currentUser)
        }
      } catch (error) {
        console.error('Error parsing user from localStorage:', error)
      }
    }
    
    // Handle multiple property name formats (PascalCase from store, snake_case from localStorage, etc.)
    const userId = currentUser?.UserId || 
                   currentUser?.userId || 
                   currentUser?.user_id || 
                   currentUser?.userid || 
                   currentUser?.id
    
    const userName = currentUser?.UserName || 
                     currentUser?.username || 
                     `${currentUser?.FirstName || currentUser?.first_name || ''} ${currentUser?.LastName || currentUser?.last_name || ''}`.trim() || 
                     currentUser?.Email || 
                     currentUser?.email ||
                     currentUser?.name
    
    if (currentUser && userId) {
      // Auto-fill assigner
      assignmentForm.value.assigner_id = userId.toString()
      assignmentForm.value.assigner_name = userName || 'Current User'
      
      // Set assignee to same as assigner
      assignmentForm.value.assignee_id = userId.toString()
      assignmentForm.value.assignee_name = userName || 'Current User'
    } else {
      console.error('No current user found in store or localStorage')
      console.log('Store state:', store.getters['auth/currentUser'])
      console.log('localStorage current_user:', localStorage.getItem('current_user'))
      console.log('Current user object:', currentUser)
      console.log('Resolved userId:', userId)
      PopupService.warning('Unable to get current user information. Please log in again or select assignee manually.', 'User Not Found')
      noApprovalNeeded.value = false
    }
  } else {
    // Reset assignee when unchecked
    assignmentForm.value.assignee_id = ''
    assignmentForm.value.assignee_name = ''
  }
}

const createAssignment = async () => {
  if (!selectedPlan.value) {
    PopupService.warning('No plan selected. Please select a plan first.', 'No Plan Selected')
    return
  }

  isSubmittingAssignment.value = true
  
  try {
    console.log('Creating assignment for plan:', selectedPlan.value.plan_id, assignmentForm.value)
    
    // Ensure all required fields are filled
    if (!assignmentForm.value.workflow_name || !assignmentForm.value.assigner_id || !assignmentForm.value.due_date) {
      PopupService.warning('Please fill in all required fields (Workflow Name, Assigner, Due Date)', 'Required Fields Missing')
      return
    }
    
    if (!noApprovalNeeded.value && !assignmentForm.value.assignee_id) {
      PopupService.warning('Please select an assignee or check "No Approval Needed"', 'Assignee Required')
      return
    }
    
    // Prepare the assignment data with proper structure
    // Ensure assignee_id is set to assigner_id if no approval needed
    const assignerId = parseInt(assignmentForm.value.assigner_id) || 0
    const assigneeId = noApprovalNeeded.value 
      ? assignerId 
      : (parseInt(assignmentForm.value.assignee_id) || 0)
    const assigneeName = noApprovalNeeded.value
      ? assignmentForm.value.assigner_name
      : assignmentForm.value.assignee_name
    
    const assignmentData = {
      workflow_name: assignmentForm.value.workflow_name,
      plan_type: selectedPlan.value.plan_type,
      assigner_id: assignerId,
      assigner_name: assignmentForm.value.assigner_name,
      assignee_id: assigneeId,
      assignee_name: assigneeName,
      object_type: 'PLAN',
      object_id: selectedPlan.value.plan_id,
      due_date: assignmentForm.value.due_date,
      no_approval_needed: noApprovalNeeded.value
    }
    
    console.log('Sending assignment data:', assignmentData)
    
    // Call the API to create the approval assignment
    const response = await api.approvals.createAssignment(assignmentData)
    
    console.log('Assignment created successfully:', response)
    
    PopupService.success(`Assignment created successfully for ${assignmentForm.value.workflow_name}! Approval ID: ${(response as any).approval_id}`, 'Assignment Created')
    
    // Reset the form and go back to step 1 for next assignment
    selectedPlanId.value = ""
    selectedPlan.value = null
    noApprovalNeeded.value = false
    assignmentForm.value = {
      workflow_name: '',
      plan_type: '',
      assigner_id: '',
      assigner_name: '',
      assignee_id: '',
      assignee_name: '',
      object_type: 'PLAN',
      object_id: '',
      due_date: ''
    }
    
    // Go back to step 1 to select another plan
    goToStep(1)
    
  } catch (error) {
    console.error('Error creating assignment:', error)
    
    let errorMessage = 'Error creating assignment. Please try again.'
    if (error.response?.data?.message) {
      errorMessage = error.response.data.message
    } else if (error.response?.data?.error) {
      errorMessage = error.response.data.error
    } else if (error.response?.data?.detail) {
      errorMessage = error.response.data.detail
    } else if (error.message) {
      errorMessage = error.message
    }
    
    // Log the full error response for debugging
    console.error('Full error response:', error.response?.data)
    
    PopupService.error(errorMessage, 'Assignment Failed')
  } finally {
    isSubmittingAssignment.value = false
  }
}


const saveExtractedData = async () => {
  if (!selectedPlan.value || !selectedPlan.value.plan_id) {
    PopupService.warning('No plan selected. Please select a plan first.', 'No Plan Selected')
    return
  }

  saving.value = true
  try {
    const dataToSave = { ...extractedData.value }
    
    // Parse JSON fields - convert string representations back to objects
    const jsonFields = [
      'regulatory_references', 'critical_services', 'dependencies_internal', 
      'dependencies_external', 'rto_targets', 'rpo_targets', 'incident_types',
      'alternate_work_locations', 'roles_responsibilities', 'critical_systems',
      'critical_applications', 'databases_list', 'supporting_infrastructure',
      'third_party_services', 'disaster_scenarios', 'application_restoration_order'
    ]
    
    jsonFields.forEach(field => {
      if (dataToSave[field] && typeof dataToSave[field] === 'string') {
        try {
          dataToSave[field] = JSON.parse(dataToSave[field])
        } catch (e) {
          console.warn(`Failed to parse JSON for field ${field}:`, e)
          // If parsing fails, try to create a simple array from comma-separated values
          if (dataToSave[field].includes(',')) {
            dataToSave[field] = dataToSave[field].split(',').map(item => item.trim()).filter(item => item)
          }
        }
      }
    })
    
    // Use the OCR microservice extraction endpoint
    const endpoint = `/ocr/plans/${selectedPlan.value.plan_id}/extract/`
    
    // Wrap data in extracted_data object as expected by the backend
    await http.post(endpoint, {
      extracted_data: dataToSave
    }, {
      timeout: 30000 // 30 seconds timeout for saving data
    })
    
    PopupService.success('Extracted information has been saved successfully', 'Data Saved')
  } catch (err: any) {
    const errorMessage = err.response?.data?.message || err.response?.data?.error || err.message || 'Unknown error occurred'
    PopupService.error(`Error saving data: ${errorMessage}`, 'Save Failed')
    console.error('Error saving extracted data:', err)
  } finally {
    saving.value = false
  }
}

const markPlanComplete = async () => {
  if (!selectedPlan.value || !selectedPlan.value.plan_id) {
    PopupService.warning('No plan selected. Please select a plan first.', 'No Plan Selected')
    return
  }

  saving.value = true
  try {
    await http.patch(`/bcpdrp/ocr/plans/${selectedPlan.value.plan_id}/status/`, {
      status: 'OCR_COMPLETED'
    })
    
    // Update the plan status in our local state
    const plan = availablePlans.value.find(p => p.plan_id === selectedPlan.value.plan_id)
    if (plan) {
      plan.status = 'OCR_COMPLETED'
    }
    
    PopupService.success('Plan has been marked as ready for evaluation', 'Plan Marked Complete')
    
    // Advance to Step 2
    setTimeout(() => {
      goToStep(2)
    }, 1000)
  } catch (err) {
    PopupService.error(`Error updating status: ${err.message}`, 'Update Failed')
    console.error('Error updating plan status:', err)
  } finally {
    saving.value = false
  }
}

const runOCR = async () => {
  if (!selectedPlan.value || !selectedPlan.value.plan_id) {
    PopupService.warning('No plan selected. Please select a plan first.', 'No Plan Selected')
    return
  }

  isRunningOCR.value = true
  try {
    console.log('Running OCR for plan:', selectedPlan.value.plan_id)
    
    // Use OCR microservice endpoint
    const endpoint = `/ocr/plans/${selectedPlan.value.plan_id}/run/`
    
    showInfo('OCR processing started. This may take 1-2 minutes for AI extraction...')
    PopupService.success('OCR processing started. This may take 1-2 minutes for AI extraction...', 'Processing')
    
    const response = await http.post(endpoint, {
      plan_id: selectedPlan.value.plan_id,
      plan_type: selectedPlan.value.plan_type
    }, {
      timeout: 120000 // 2 minutes timeout for OCR processing
    })
    
    console.log('OCR processing completed:', response)
    console.log('Response data:', response.data)
    
    // The HTTP interceptor unwraps the response, so data is directly accessible
    // Check both response.data.extracted_data and response.data.data.extracted_data
    // to handle different response structures
    const extractedDataFromResponse = response.data?.extracted_data || response.data?.data?.extracted_data
    
    console.log('Extracted data:', extractedDataFromResponse)
    
    if (extractedDataFromResponse) {
      console.log('Setting extracted data:', extractedDataFromResponse)
      
      // Process the extracted data to handle JSON fields properly
      const processedData = { ...extractedDataFromResponse }
      
      // Convert JSON objects/arrays to strings for form display
      const jsonFields = [
        'regulatory_references', 'critical_services', 'dependencies_internal', 
        'dependencies_external', 'rto_targets', 'rpo_targets', 'incident_types',
        'alternate_work_locations', 'roles_responsibilities', 'critical_systems',
        'critical_applications', 'databases_list', 'supporting_infrastructure',
        'third_party_services', 'disaster_scenarios', 'application_restoration_order'
      ]
      
      jsonFields.forEach(field => {
        if (processedData[field] && typeof processedData[field] === 'object') {
          processedData[field] = JSON.stringify(processedData[field], null, 2)
        }
      })
      
      extractedData.value = processedData
      showSuccess('OCR completed successfully! Extracted data has been populated in the form.')
      PopupService.success('OCR completed successfully! Extracted data has been populated in the form.', 'Success')
    } else {
      console.log('No extracted_data found in response')
      console.log('Available response keys:', Object.keys(response.data || {}))
      console.log('Full response data:', response.data)
      showSuccess('OCR processing completed.')
      PopupService.success('OCR processing completed.', 'Success')
    }
    
  } catch (err: any) {
    console.error('Error running OCR:', err)
    const errorMessage = err.response?.data?.message || err.response?.data?.error || err.message || 'Unknown error occurred'
    showError(`Error running OCR: ${errorMessage}`)
    PopupService.error(`Failed to run OCR: ${errorMessage}`, 'OCR Error')
  } finally {
    isRunningOCR.value = false
  }
}

// Mock data for BCP plans
const getBCPMockData = (): ExtractedData => {
  return {
    purpose_scope: 'This Business Continuity Plan (BCP) ensures the continued operation of critical banking services during disruptive events. The plan covers all business units, systems, and processes essential for maintaining customer service and regulatory compliance.',
    regulatory_references: '["SOX", "Basel III", "PCI DSS", "GDPR", "CCAR"]',
    critical_services: '["Payment Processing", "Customer Service", "Loan Origination", "Risk Management", "Compliance Monitoring"]',
    dependencies_internal: '["IT Systems", "HR Department", "Finance", "Legal", "Operations"]',
    dependencies_external: '["Cloud Provider", "Payment Gateway", "Banking Partners", "Regulatory Bodies", "Credit Bureaus"]',
    risk_assessment_summary: 'Comprehensive risk assessment identified cyber threats, natural disasters, and operational failures as primary risks. Risk mitigation strategies include redundant systems, backup procedures, and incident response protocols.',
    bia_summary: 'Business Impact Analysis shows that payment processing downtime exceeding 4 hours would result in significant financial losses and regulatory penalties. Customer service interruptions beyond 2 hours impact customer satisfaction and retention.',
    rto_targets: '{"Payment Processing":"4h","Customer Service":"2h","Loan Origination":"8h","Risk Management":"6h","Compliance":"12h"}',
    rpo_targets: '{"Payment Processing":"15m","Customer Data":"30m","Transaction Records":"1h","Customer Service":"2h","Risk Data":"4h"}',
    incident_types: '["Cyber Attack", "Natural Disaster", "System Failure", "Pandemic", "Regulatory Action"]',
    alternate_work_locations: '["Remote Work", "Backup Office", "Partner Locations", "Mobile Units", "Cloud Infrastructure"]',
    communication_plan_internal: 'Internal communication follows a hierarchical structure: Executive Team → Department Heads → Team Leads → Staff. Communication channels include email, phone, SMS, and internal messaging systems.',
    communication_plan_bank: 'Bank communication plan includes customer notifications via website, mobile app, email, and SMS. Regulatory notifications are sent to relevant authorities within 24 hours of incident declaration.',
    roles_responsibilities: '["Incident Commander", "Communication Lead", "Technical Lead", "Business Continuity Manager", "Risk Officer"]',
    training_testing_schedule: 'Annual BCP training for all staff, quarterly tabletop exercises, and semi-annual full-scale testing. Testing includes scenario-based drills and recovery procedure validation.',
    maintenance_review_cycle: 'BCP is reviewed quarterly with annual comprehensive updates. Changes in business processes, technology, or regulations trigger immediate review and updates.'
  }
}

// Mock data for DRP plans
const getDRPMockData = (): ExtractedData => {
  return {
    purpose_scope: 'This Disaster Recovery Plan (DRP) ensures rapid recovery of critical IT systems and infrastructure following disruptive events. The plan covers data centers, networks, applications, and supporting infrastructure essential for business operations.',
    regulatory_references: '["SOX", "Basel III", "PCI DSS", "GDPR", "FFIEC"]',
    critical_systems: '["Core Banking System", "Payment Gateway", "Database Servers", "Network Infrastructure", "Security Systems"]',
    critical_applications: '["Loan Management System", "Trading Platform", "Customer Portal", "Risk Management System", "Compliance System"]',
    databases_list: '["Customer Database", "Transaction Database", "Risk Database", "Archive Database", "Audit Database"]',
    supporting_infrastructure: '["Network", "Storage", "Servers", "Security", "Monitoring", "Backup Systems"]',
    third_party_services: '["Cloud Provider", "SMS Gateway", "Email Service", "Credit Bureau", "Regulatory Reporting"]',
    rto_targets: '{"Critical Systems":"2h","Applications":"4h","Databases":"1h","Network":"30m","Security":"6h"}',
    rpo_targets: '{"Critical Systems":"30m","Applications":"1h","Databases":"15m","Network":"5m","Security":"2h"}',
    disaster_scenarios: '["Data Center Failure", "Network Outage", "Cyber Attack", "Natural Disaster", "Hardware Failure", "Software Corruption"]',
    disaster_declaration_process: 'Disaster declaration follows a three-tier process: Level 1 (Minor) - Local IT team response, Level 2 (Major) - Department-wide response, Level 3 (Critical) - Enterprise-wide response with executive involvement.',
    data_backup_strategy: 'Multi-tier backup strategy includes real-time replication to secondary data center, daily incremental backups, weekly full backups, and monthly archival to off-site storage. Backup testing performed monthly.',
    recovery_site_details: 'Primary DR site located 50 miles from main data center with full infrastructure replication. Secondary DR site located 200 miles away with critical systems only. Both sites have redundant power, cooling, and network connectivity.',
    failover_procedures: 'Automated failover for critical systems with manual verification. Process includes: 1) Incident detection and assessment, 2) DR team activation, 3) System failover execution, 4) Service validation, 5) Stakeholder notification.',
    failback_procedures: 'Failback procedures include: 1) Primary system validation, 2) Data synchronization, 3) Service migration, 4) Performance testing, 5) Full service restoration, 6) Post-incident review and documentation.',
    network_recovery_steps: 'Network recovery follows: 1) Assess network damage, 2) Activate backup circuits, 3) Configure routing, 4) Test connectivity, 5) Restore services, 6) Monitor performance.',
    application_restoration_order: '["Core Banking", "Payment Gateway", "Customer Portal", "Risk Management", "Compliance", "Reporting", "Analytics"]',
    testing_validation_schedule: 'Monthly DR testing includes: Week 1 - Network failover, Week 2 - Application recovery, Week 3 - Database restoration, Week 4 - Full system testing. Annual comprehensive DR exercise.',
    maintenance_review_cycle: 'DRP reviewed monthly with quarterly updates. Technology changes, infrastructure modifications, or regulatory requirements trigger immediate review and plan updates.'
  }
}

const loadMockData = () => {
  if (!selectedPlan.value || !selectedPlan.value.plan_type) {
    PopupService.warning('No plan selected. Please select a plan first.', 'No Plan Selected')
    return
  }

  // Load appropriate mock data based on plan type
  if (selectedPlan.value.plan_type === 'BCP') {
    extractedData.value = getBCPMockData()
    console.log('Loaded BCP mock data')
  } else {
    extractedData.value = getDRPMockData()
    console.log('Loaded DRP mock data')
  }

  PopupService.success(`Mock data loaded for ${selectedPlan.value.plan_type} plan. You can now review and modify the extracted information before saving.`, 'Mock Data Loaded')
}


// Lifecycle
onMounted(async () => {
  await loggingService.logPageView('BCP', 'Plan Submission OCR')
  await fetchPlans()
  await fetchUsers()
})
</script>
