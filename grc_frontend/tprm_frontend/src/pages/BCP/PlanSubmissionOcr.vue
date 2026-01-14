<template>
  <div class="plan-submission-ocr">
    <!-- Breadcrumb Navigation -->
    <div class="breadcrumb-container">
      <nav class="breadcrumb">
        <div 
          class="breadcrumb-item" 
          :class="{ 'breadcrumb-item--active': currentStep === 1 }"
          @click="goToStep(1)"
        >
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
        
        <div 
          class="breadcrumb-item" 
          :class="{ 
            'breadcrumb-item--active': currentStep === 2,
            'breadcrumb-item--disabled': !isStep2Enabled && currentStep !== 2
          }"
          @click="handleStep2Click"
          :title="!isStep2Enabled ? 'Please complete OCR extraction and save data in Step 1 first' : ''"
        >
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

                <!-- Unified Extraction Fields for All Plan Types - Dynamic -->
                <div class="extraction-fields">
                  <!-- Field Management Header -->
                  <div class="field-management-header">
                    <button 
                      class="btn btn--outline btn--sm"
                      @click="showAddFieldModal = true"
                    >
                      <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
                      </svg>
                      Add Custom Field
                    </button>
                    <button 
                      class="btn btn--outline btn--sm"
                      @click="showRemoveButtons = !showRemoveButtons"
                      :class="{ 'btn--active': showRemoveButtons }"
                    >
                      <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                      </svg>
                      Remove Fields
                    </button>
                  </div>

                  <!-- Dynamic Field Sections -->
                  <template v-for="sectionGroup in getSectionGroups()" :key="sectionGroup.section">
                    <div class="field-section">
                      <div class="section-header">
                        <h4 class="section-title">{{ sectionGroup.title }}</h4>
                        <button 
                          v-if="showRemoveButtons"
                          class="btn-remove-section"
                          @click="removeSection(sectionGroup.section)"
                          :title="'Remove entire section: ' + sectionGroup.title"
                        >
                          <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                          </svg>
                        </button>
                      </div>
                      <div 
                        class="field-grid"
                        :class="{
                          'field-grid--2cols': sectionGroup.section === 'purpose' || sectionGroup.section === 'risk' || sectionGroup.section === 'recovery' || sectionGroup.section === 'incident',
                          'field-grid--3cols': sectionGroup.section === 'dependencies' || sectionGroup.section === 'communication' || sectionGroup.section === 'procedures' || sectionGroup.section === 'training',
                          'field-grid--4cols': sectionGroup.section === 'infrastructure'
                        }"
                      >
                        <div 
                          v-for="field in sectionGroup.fields" 
                          :key="field.id"
                          class="field-group"
                          :style="{
                            gridColumn: field.gridCols === 2 ? 'span 2' : 'span 1'
                          }"
                        >
                          <div class="field-header">
                            <label class="field-label">{{ field.label }}</label>
                            <button 
                              v-if="showRemoveButtons"
                              class="btn-remove-field"
                              @click="removeField(field.id)"
                              :title="field.isCustom ? 'Remove custom field' : 'Remove field'"
                            >
                              <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                              </svg>
                            </button>
                          </div>
                          <textarea 
                            class="textarea" 
                            :placeholder="field.placeholder"
                            :style="{ minHeight: `${field.rows * 1.5}rem` }"
                            v-model="extractedData[field.key]"
                          />
                        </div>
                      </div>
                    </div>
                  </template>
                  
                  <!-- Removed Fields Section -->
                  <div v-if="removedFields.length > 0" class="removed-fields-section">
                    <div class="section-header">
                      <h4 class="section-title removed-section-title">Removed Fields</h4>
                    </div>
                    <div class="removed-fields-grid">
                      <div 
                        v-for="field in removedFields" 
                        :key="field.id"
                        class="removed-field-group"
                      >
                        <div class="field-header">
                          <label class="field-label removed-field-label">{{ field.label }}</label>
                          <span class="removed-badge">Removed</span>
                        </div>
                        <textarea 
                          class="textarea removed-field-textarea" 
                          :placeholder="field.placeholder"
                          :style="{ minHeight: `${field.rows * 1.5}rem` }"
                          :value="extractedData[field.key] || ''"
                          readonly
                          disabled
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
                  <div class="save-action-group">
                    <button 
                      class="btn btn--primary"
                      @click="saveExtractedData"
                      :disabled="saving"
                    >
                      <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3-3m0 0l-3 3m3-3v12"/>
                      </svg>
                      {{ saving ? 'Saving...' : 'Save and Assign' }}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Step 2: Assignment for Evaluation -->
      <div v-if="currentStep === 2" class="space-y-6">
        <div class="card">
          <div class="card-header">
            <h3 class="card-title flex items-center gap-2">
              <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
              </svg>
              Assign for Evaluation
            </h3>
          </div>
          <div class="card-content space-y-6">
            <!-- Empty State -->
            <div v-if="!selectedPlanId" class="empty-state">
              <div class="empty-icon">📄</div>
              <p>No plan selected for assignment</p>
              <button @click="goToStep(1)" class="btn btn--primary">Go to Step 1</button>
            </div>
            
            <!-- Assignment Form for Selected Plan -->
            <form v-else-if="selectedPlan && selectedPlan.plan_id" @submit.prevent="createAssignment" class="space-y-6">
              <!-- Row 1: Plan Type, Object ID, Object Type -->
              <div class="form-grid-3">
                <div class="space-y-2">
                  <label for="planType" class="block text-sm font-medium">Plan Type <span class="text-destructive">*</span></label>
                  <select v-model="assignmentForm.plan_type" id="planType" class="input" required>
                    <option value="">Select plan type</option>
                    <option v-for="pt in planTypes" :key="pt" :value="pt">
                      {{ pt }}
                    </option>
                  </select>
                </div>
                <div class="space-y-2">
                  <label for="objectId" class="block text-sm font-medium">Object ID <span class="text-destructive">*</span></label>
                  <input 
                    v-model="assignmentForm.object_id" 
                    type="number" 
                    id="objectId" 
                    class="input" 
                    required 
                    placeholder="Enter object ID"
                    readonly
                  />
                </div>
                <div class="space-y-2">
                  <label for="objectType" class="block text-sm font-medium">Object Type <span class="text-destructive">*</span></label>
                  <select v-model="assignmentForm.object_type" id="objectType" class="input" required>
                    <option value="">Select object type</option>
                    <option value="PLAN EVALUATION">Plan Evaluation</option>
                    <option value="NEW QUESTIONNAIRE">New Questionnaire</option>
                    <option value="QUESTIONNAIRE RESPONSE">Questionnaire Response</option>
                  </select>
                </div>
              </div>

              <!-- Row 2: Workflow Name, Assigner, Assigner Name -->
              <div class="form-grid-3">
                <div class="space-y-2">
                  <label for="workflowName" class="block text-sm font-medium">Workflow Name <span class="text-destructive">*</span></label>
                  <input 
                    v-model="assignmentForm.workflow_name" 
                    type="text" 
                    id="workflowName" 
                    class="input" 
                    required 
                    placeholder="Enter workflow name"
                  />
                </div>
                <div class="space-y-2">
                  <label for="assignerId" class="block text-sm font-medium">Assigner <span class="text-destructive">*</span></label>
                  <select v-model="assignmentForm.assigner_id" id="assignerId" class="input" required @change="onAssignerChange" :disabled="isLoadingUsers">
                    <option value="">{{ isLoadingUsers ? 'Loading users...' : 'Select assigner' }}</option>
                    <option v-for="user in users" :key="user.user_id" :value="user.user_id">
                      {{ user.display_name }}
                    </option>
                  </select>
                </div>
                <div class="space-y-2">
                  <label for="assignerName" class="block text-sm font-medium">Assigner Name</label>
                  <input 
                    v-model="assignmentForm.assigner_name" 
                    type="text" 
                    id="assignerName" 
                    class="input" 
                    readonly
                    placeholder="Auto-filled from selection"
                  />
                </div>
              </div>

              <!-- Row 3: Assignee Name, Assignee ID, Due Date -->
              <div class="form-grid-3">
                <div class="space-y-2">
                  <label for="assigneeName" class="block text-sm font-medium">Assignee Name</label>
                  <input 
                    v-model="assignmentForm.assignee_name" 
                    type="text" 
                    id="assigneeName" 
                    class="input" 
                    readonly
                    placeholder="Auto-filled from selection"
                  />
                </div>
                <div class="space-y-2">
                  <label for="assigneeId" class="block text-sm font-medium">Assignee <span class="text-destructive">*</span></label>
                  <select v-model="assignmentForm.assignee_id" id="assigneeId" class="input" :required="!noApprovalNeeded" @change="onAssigneeChange" :disabled="noApprovalNeeded || isLoadingUsers">
                    <option value="">{{ isLoadingUsers ? 'Loading users...' : 'Select assignee' }}</option>
                    <option v-for="user in users" :key="user.user_id" :value="user.user_id">
                      {{ user.display_name }}
                    </option>
                  </select>
                </div>
                <div class="space-y-2">
                  <label for="dueDate" class="block text-sm font-medium">Due Date <span class="text-destructive">*</span></label>
                  <input 
                    v-model="assignmentForm.due_date" 
                    type="datetime-local" 
                    id="dueDate" 
                    class="input" 
                    required
                  />
                </div>
              </div>

              <!-- Row 4: No Approval Needed Checkbox -->
              <div class="space-y-2">
                <label class="flex items-center gap-2 cursor-pointer">
                  <input 
                    type="checkbox" 
                    v-model="noApprovalNeeded"
                    class="rounded border-gray-300 cursor-pointer"
                    @change="handleNoApprovalChange"
                  />
                  <span class="text-sm font-medium">No Approval Needed</span>
                </label>
                <p class="text-xs text-gray-500 ml-6">
                  If checked, the assigner and assignee will be the same (current user), and approval will be automatic
                </p>
              </div>

              <!-- Action Buttons -->
              <div class="flex gap-4 pt-4">
                <button type="button" @click="goToStep(1)" class="btn btn--outline">
                  <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"/>
                  </svg>
                  Back to OCR Extraction
                </button>
                <button type="button" @click="resetAssignmentForm" class="btn btn--outline">
                  <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
                  </svg>
                  Reset Form
                </button>
                <button type="submit" class="btn btn--primary" :disabled="isSubmittingAssignment">
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

    <!-- Add Field Modal -->
    <div v-if="showAddFieldModal" class="modal-overlay" @click.self="showAddFieldModal = false">
      <div class="modal-content add-field-modal">
        <div class="modal-header">
          <h3 class="modal-title">Add Custom Field</h3>
          <button class="btn btn--ghost btn--sm" @click="showAddFieldModal = false">
            <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <div class="form-section">
            <label class="field-label">Field Key <span class="text-destructive">*</span></label>
            <input 
              v-model="newFieldForm.key" 
              type="text" 
              class="input" 
              placeholder="e.g., custom_field_name"
              required
            />
            <p class="field-hint">Must be unique and contain only letters, numbers, and underscores</p>
          </div>
          <div class="form-section">
            <label class="field-label">Field Label <span class="text-destructive">*</span></label>
            <input 
              v-model="newFieldForm.label" 
              type="text" 
              class="input" 
              placeholder="e.g., Custom Field Name"
              required
            />
          </div>
          <div class="form-section">
            <label class="field-label">Section</label>
            <select v-model="newFieldForm.section" class="select">
              <option value="custom">Custom Fields</option>
              <option value="purpose">Purpose & Scope</option>
              <option value="dependencies">Dependencies</option>
              <option value="infrastructure">Infrastructure</option>
              <option value="risk">Risk & Impact</option>
              <option value="recovery">Recovery Objectives</option>
              <option value="incident">Incident Management</option>
              <option value="communication">Communication & Roles</option>
              <option value="procedures">Recovery Procedures</option>
              <option value="training">Training & Maintenance</option>
            </select>
          </div>
          <div class="form-section">
            <label class="field-label">Section Title</label>
            <input 
              v-model="newFieldForm.sectionTitle" 
              type="text" 
              class="input" 
              placeholder="Section Title"
            />
          </div>
          <div class="form-section">
            <label class="field-label">Placeholder Text</label>
            <input 
              v-model="newFieldForm.placeholder" 
              type="text" 
              class="input" 
              placeholder="Enter placeholder text..."
            />
          </div>
          <div class="form-row">
            <div class="form-section">
              <label class="field-label">Grid Columns</label>
              <select v-model.number="newFieldForm.gridCols" class="select">
                <option :value="1">1 Column</option>
                <option :value="2">2 Columns</option>
              </select>
            </div>
            <div class="form-section">
              <label class="field-label">Textarea Rows</label>
              <input 
                v-model.number="newFieldForm.rows" 
                type="number" 
                class="input" 
                min="1"
                max="10"
              />
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn--outline" @click="showAddFieldModal = false">Cancel</button>
          <button class="btn btn--primary" @click="addCustomField">Add Field</button>
        </div>
      </div>
    </div>

    <!-- TPRM Consent Modal -->
    <TPRMConsentModal
      ref="consentModalRef"
    />
  </div>
</template>

<script setup lang="ts">
import './PlanSubmissionOcr.css'
import { ref, computed, onMounted, watch, reactive } from 'vue'
import http from '../../api/http.js'
import api from '../../services/api_bcp.js'
import { useNotifications } from '@/composables/useNotifications'
import { PopupService } from '@/popup/popupService'
import notificationService from '@/services/notificationService'
import loggingService from '@/services/loggingService'
import { useStore } from 'vuex'
import TPRMConsentModal from '@/components/Consent/TPRMConsentModal.vue'
import { executeWithTPRMConsent, TPRM_CONSENT_ACTIONS } from '@/utils/tprmConsentManager.js'
import { nextTick } from 'vue'

// Define interfaces for type safety
interface ExtractedData {
  plan_id?: number | null
  purpose_scope?: string | null
  regulatory_references?: string | null
  critical_services?: string | null
  dependencies_internal?: string | null
  dependencies_external?: string | null
  risk_assessment_summary?: string | null
  bia_summary?: string | null
  rto_targets?: string | null
  rpo_targets?: string | null
  critical_systems?: string | null
  critical_applications?: string | null
  databases_list?: string | null
  supporting_infrastructure?: string | null
  third_party_services?: string | null
  incident_types?: string | null
  alternate_work_locations?: string | null
  communication_plan_internal?: string | null
  communication_plan_bank?: string | null
  roles_responsibilities?: string | null
  training_testing_schedule?: string | null
  maintenance_review_cycle?: string | null
  disaster_scenarios?: string | null
  disaster_declaration_process?: string | null
  data_backup_strategy?: string | null
  recovery_site_details?: string | null
  failover_procedures?: string | null
  failback_procedures?: string | null
  network_recovery_steps?: string | null
  application_restoration_order?: string | null
  testing_validation_schedule?: string | null
  [key: string]: any // Allow custom fields
}

interface FieldDefinition {
  id: string
  key: string
  label: string
  section: string
  sectionTitle: string
  placeholder: string
  isCustom: boolean
  gridCols?: number
  rows?: number
}

// Data state
const { showSuccess, showError, showWarning, showInfo } = useNotifications()

// Vuex store
const store = useStore()

const saving = ref(false)
const submitting = ref(false)
const isRunningOCR = ref(false)
const isOCRSaved = ref(false) // Track if OCR data has been saved for current plan

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
  object_type: 'PLAN EVALUATION',
  object_id: '',
  due_date: ''
})
const isSubmittingAssignment = ref(false)
const noApprovalNeeded = ref(false)
const planTypes = ref<string[]>([])

// TPRM Consent Modal ref
const consentModalRef = ref(null)

// UI state
const currentStep = ref(1)

// Extracted data state for selected plan
const extractedData = ref<ExtractedData>({})

// Dynamic field management
const fieldDefinitions = ref<FieldDefinition[]>([])
const removedFields = ref<FieldDefinition[]>([])
const showAddFieldModal = ref(false)
const showRemoveButtons = ref(false)
const newFieldForm = ref({
  key: '',
  label: '',
  section: 'custom',
  sectionTitle: 'Custom Fields',
  placeholder: 'Enter value...',
  gridCols: 1,
  rows: 3
})

// Computed properties

const isAllSelected = computed(() => {
  return availablePlans.value.length > 0 && availablePlans.value.every(plan => 
    selectedPlanId.value === plan.plan_id.toString()
  )
})

const isStep2Enabled = computed(() => {
  // Step 2 is enabled only if a plan is selected and OCR data has been saved
  return selectedPlanId.value !== "" && isOCRSaved.value
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
      
      // Extract unique plan types from plans
      const uniquePlanTypes = [...new Set(plans.map((plan: any) => plan.plan_type).filter(Boolean))]
      planTypes.value = uniquePlanTypes.sort()
      console.log('Extracted plan types from plans:', planTypes.value)
    } else {
      console.error('API returned no plans data or plans is not an array')
      availablePlans.value = []
      planTypes.value = []
    }
  } catch (error) {
    console.error('Error fetching plans from API:', error)
    availablePlans.value = []
    planTypes.value = []
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

const selectPlan = async (plan) => {
  if (!plan || !plan.plan_id) {
    console.error('Invalid plan selected:', plan)
    return
  }
  
  selectedPlanId.value = plan.plan_id.toString()
  selectedPlan.value = plan
  isDropdownOpen.value = false
  
  console.log('Plan selected:', plan)
  
  // Reset OCR saved status when selecting a new plan
  isOCRSaved.value = false
  
  // Clear removed fields when selecting a new plan
  removedFields.value = []
  
  // Initialize field definitions
  fieldDefinitions.value = initializeFieldDefinitions()
  
  // Initialize extracted data for the selected plan
  extractedData.value = initializeExtractedData(plan.plan_type)
  
  // Load any existing extracted data and custom fields
  await loadExistingExtractedData(plan.plan_id)
  
  // Check if plan already has OCR data saved (status is OCR_COMPLETED)
  if (plan.status === 'OCR_COMPLETED') {
    isOCRSaved.value = true
  }
  
  // If user is on Step 2 and selects a new plan, go back to Step 1
  if (currentStep.value === 2) {
    currentStep.value = 1
  }
  
  // Initialize assignment form
  assignmentForm.value = initializeAssignmentForm(plan.plan_type)
  assignmentForm.value.object_id = plan.plan_id
}

const loadExistingExtractedData = async (planId: number) => {
  try {
    // Try to fetch existing extracted data
    const response = await api.plans.get(planId)
    const plan = (response as any).plan || (response as any).data?.plan
    
    if (plan?.ocr_extracted_data) {
      const existingData = plan.ocr_extracted_data
      
      // List of all predefined field keys (hardcoded fields)
      const predefinedFieldKeys = [
        'purpose_scope', 'regulatory_references', 'critical_services', 
        'dependencies_internal', 'dependencies_external', 'risk_assessment_summary',
        'bia_summary', 'rto_targets', 'rpo_targets', 'critical_systems',
        'critical_applications', 'databases_list', 'supporting_infrastructure',
        'third_party_services', 'incident_types', 'alternate_work_locations',
        'communication_plan_internal', 'communication_plan_bank', 'roles_responsibilities',
        'training_testing_schedule', 'maintenance_review_cycle', 'disaster_scenarios',
        'disaster_declaration_process', 'data_backup_strategy', 'recovery_site_details',
        'failover_procedures', 'failback_procedures', 'network_recovery_steps',
        'application_restoration_order', 'testing_validation_schedule'
      ]
      
      // JSON fields that need stringification
      const jsonFields = [
        'regulatory_references', 'critical_services', 'dependencies_internal', 
        'dependencies_external', 'rto_targets', 'rpo_targets', 'incident_types',
        'alternate_work_locations', 'roles_responsibilities', 'critical_systems',
        'critical_applications', 'databases_list', 'supporting_infrastructure',
        'third_party_services', 'disaster_scenarios', 'application_restoration_order'
      ]
      
      // Load fields from existing data
      Object.keys(existingData).forEach(key => {
        if (key === 'plan_id') return
        
        const value = existingData[key]
        if (value === null || value === undefined) return
        
        // Check if this field is currently in fieldDefinitions
        const fieldExists = fieldDefinitions.value.some(f => f.key === key)
        
        if (fieldExists) {
          // Field is in current fieldDefinitions, so load it
          if (jsonFields.includes(key) && typeof value === 'object') {
            extractedData.value[key] = JSON.stringify(value, null, 2)
          } else {
            extractedData.value[key] = value
          }
        } else {
          // Field is not in current fieldDefinitions
          // Only restore it if it's a custom field (not in predefined list)
          // This means it was a custom field that was previously added
          if (!predefinedFieldKeys.includes(key)) {
            // It's a custom field, add it to fieldDefinitions and load it
            const customField: FieldDefinition = {
              id: `custom_${key}_${Date.now()}`,
              key: key,
              label: key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
              section: 'custom',
              sectionTitle: 'Custom Fields',
              placeholder: 'Enter value...',
              isCustom: true,
              gridCols: 1,
              rows: 3
            }
            fieldDefinitions.value.push(customField)
            
            // Load the value
            if (typeof value === 'object' && (Array.isArray(value) || (typeof value === 'object' && value !== null))) {
              extractedData.value[key] = JSON.stringify(value, null, 2)
            } else {
              extractedData.value[key] = value
            }
          }
          // If it's a predefined field that's not in fieldDefinitions, it was removed
          // Don't restore it - it will be excluded from the save
        }
      })
      
      console.log(`Loaded existing data: ${Object.keys(extractedData.value).length} fields restored`)
    }
  } catch (error) {
    console.log('No existing extracted data found or error loading:', error)
  }
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

const initializeFieldDefinitions = (): FieldDefinition[] => {
  return [
    // Purpose & Scope
    { id: 'purpose_scope', key: 'purpose_scope', label: 'Purpose & Scope', section: 'purpose', sectionTitle: 'Purpose & Scope', placeholder: 'Enter the purpose and scope of the plan...', isCustom: false, gridCols: 1, rows: 6 },
    { id: 'regulatory_references', key: 'regulatory_references', label: 'Regulatory References', section: 'purpose', sectionTitle: 'Purpose & Scope', placeholder: '["SOX", "Basel III", "PCI DSS"]', isCustom: false, gridCols: 1, rows: 6 },
    
    // Critical Services & Dependencies
    { id: 'critical_services', key: 'critical_services', label: 'Critical Services', section: 'dependencies', sectionTitle: 'Critical Services & Dependencies', placeholder: '["Payments", "Collections", "Customer Service"]', isCustom: false, gridCols: 1, rows: 4 },
    { id: 'dependencies_internal', key: 'dependencies_internal', label: 'Internal Dependencies', section: 'dependencies', sectionTitle: 'Critical Services & Dependencies', placeholder: '["IT Systems", "HR Department", "Finance"]', isCustom: false, gridCols: 1, rows: 4 },
    { id: 'dependencies_external', key: 'dependencies_external', label: 'External Dependencies', section: 'dependencies', sectionTitle: 'Critical Services & Dependencies', placeholder: '["Cloud Provider", "Payment Gateway", "Banking Partners"]', isCustom: false, gridCols: 1, rows: 4 },
    
    // Critical Systems & Infrastructure
    { id: 'critical_systems', key: 'critical_systems', label: 'Critical Systems', section: 'infrastructure', sectionTitle: 'Critical Systems & Infrastructure', placeholder: '["Core Banking", "Payment Gateway", "Database Servers"]', isCustom: false, gridCols: 1, rows: 4 },
    { id: 'critical_applications', key: 'critical_applications', label: 'Critical Applications', section: 'infrastructure', sectionTitle: 'Critical Systems & Infrastructure', placeholder: '["Loan System", "Trading Platform", "Customer Portal"]', isCustom: false, gridCols: 1, rows: 4 },
    { id: 'databases_list', key: 'databases_list', label: 'Databases', section: 'infrastructure', sectionTitle: 'Critical Systems & Infrastructure', placeholder: '["Customer DB", "Transaction DB", "Archive DB"]', isCustom: false, gridCols: 1, rows: 4 },
    { id: 'supporting_infrastructure', key: 'supporting_infrastructure', label: 'Supporting Infrastructure', section: 'infrastructure', sectionTitle: 'Critical Systems & Infrastructure', placeholder: '["Network", "Storage", "Servers", "Security"]', isCustom: false, gridCols: 1, rows: 4 },
    { id: 'third_party_services', key: 'third_party_services', label: 'Third Party Services', section: 'infrastructure', sectionTitle: 'Critical Systems & Infrastructure', placeholder: '["Cloud Provider", "SMS Gateway", "Email Service"]', isCustom: false, gridCols: 1, rows: 4 },
    
    // Risk & Business Impact
    { id: 'risk_assessment_summary', key: 'risk_assessment_summary', label: 'Risk Assessment Summary', section: 'risk', sectionTitle: 'Risk & Business Impact', placeholder: 'Enter risk assessment summary...', isCustom: false, gridCols: 1, rows: 5 },
    { id: 'bia_summary', key: 'bia_summary', label: 'Business Impact Analysis Summary', section: 'risk', sectionTitle: 'Risk & Business Impact', placeholder: 'Enter business impact analysis...', isCustom: false, gridCols: 1, rows: 5 },
    
    // Recovery Objectives
    { id: 'rto_targets', key: 'rto_targets', label: 'RTO Targets', section: 'recovery', sectionTitle: 'Recovery Objectives', placeholder: '{"Payments":"4h","Collections":"2h","Customer Service":"8h"}', isCustom: false, gridCols: 1, rows: 4 },
    { id: 'rpo_targets', key: 'rpo_targets', label: 'RPO Targets', section: 'recovery', sectionTitle: 'Recovery Objectives', placeholder: '{"Payments":"15m","Collections":"30m","Customer Data":"1h"}', isCustom: false, gridCols: 1, rows: 4 },
    
    // Incident Management
    { id: 'incident_types', key: 'incident_types', label: 'Incident Types', section: 'incident', sectionTitle: 'Incident Management', placeholder: '["Cyber Attack", "Natural Disaster", "System Failure"]', isCustom: false, gridCols: 1, rows: 4 },
    { id: 'alternate_work_locations', key: 'alternate_work_locations', label: 'Alternate Work Locations', section: 'incident', sectionTitle: 'Incident Management', placeholder: '["Remote Work", "Backup Office", "Partner Locations"]', isCustom: false, gridCols: 1, rows: 4 },
    { id: 'disaster_scenarios', key: 'disaster_scenarios', label: 'Disaster Scenarios', section: 'incident', sectionTitle: 'Incident Management', placeholder: '["Data Center Failure", "Network Outage", "Cyber Attack"]', isCustom: false, gridCols: 1, rows: 4 },
    { id: 'disaster_declaration_process', key: 'disaster_declaration_process', label: 'Disaster Declaration Process', section: 'incident', sectionTitle: 'Incident Management', placeholder: 'Enter disaster declaration process...', isCustom: false, gridCols: 1, rows: 4 },
    
    // Communication & Roles
    { id: 'communication_plan_internal', key: 'communication_plan_internal', label: 'Internal Communication Plan', section: 'communication', sectionTitle: 'Communication & Roles', placeholder: 'Enter internal communication plan...', isCustom: false, gridCols: 1, rows: 4 },
    { id: 'communication_plan_bank', key: 'communication_plan_bank', label: 'Bank Communication Plan', section: 'communication', sectionTitle: 'Communication & Roles', placeholder: 'Enter bank communication plan...', isCustom: false, gridCols: 1, rows: 4 },
    { id: 'roles_responsibilities', key: 'roles_responsibilities', label: 'Roles & Responsibilities', section: 'communication', sectionTitle: 'Communication & Roles', placeholder: '["Incident Commander", "Communication Lead", "Technical Lead"]', isCustom: false, gridCols: 1, rows: 4 },
    
    // Recovery Procedures
    { id: 'recovery_site_details', key: 'recovery_site_details', label: 'Recovery Site Details', section: 'procedures', sectionTitle: 'Recovery Procedures', placeholder: 'Primary DR site location and details', isCustom: false, gridCols: 1, rows: 4 },
    { id: 'data_backup_strategy', key: 'data_backup_strategy', label: 'Data Backup Strategy', section: 'procedures', sectionTitle: 'Recovery Procedures', placeholder: 'Enter data backup strategy...', isCustom: false, gridCols: 1, rows: 4 },
    { id: 'failover_procedures', key: 'failover_procedures', label: 'Failover Procedures', section: 'procedures', sectionTitle: 'Recovery Procedures', placeholder: 'Enter failover procedures...', isCustom: false, gridCols: 1, rows: 4 },
    { id: 'failback_procedures', key: 'failback_procedures', label: 'Failback Procedures', section: 'procedures', sectionTitle: 'Recovery Procedures', placeholder: 'Enter failback procedures...', isCustom: false, gridCols: 1, rows: 4 },
    { id: 'network_recovery_steps', key: 'network_recovery_steps', label: 'Network Recovery Steps', section: 'procedures', sectionTitle: 'Recovery Procedures', placeholder: 'Enter network recovery steps...', isCustom: false, gridCols: 1, rows: 4 },
    { id: 'application_restoration_order', key: 'application_restoration_order', label: 'Application Restoration Order', section: 'procedures', sectionTitle: 'Recovery Procedures', placeholder: '["Core Banking", "Payment Gateway", "Customer Portal"]', isCustom: false, gridCols: 1, rows: 4 },
    
    // Training, Testing & Maintenance
    { id: 'training_testing_schedule', key: 'training_testing_schedule', label: 'Training & Testing Schedule', section: 'training', sectionTitle: 'Training, Testing & Maintenance', placeholder: 'Enter training and testing schedule...', isCustom: false, gridCols: 1, rows: 4 },
    { id: 'testing_validation_schedule', key: 'testing_validation_schedule', label: 'Testing & Validation Schedule', section: 'training', sectionTitle: 'Training, Testing & Maintenance', placeholder: 'Enter testing and validation schedule...', isCustom: false, gridCols: 1, rows: 4 },
    { id: 'maintenance_review_cycle', key: 'maintenance_review_cycle', label: 'Maintenance & Review Cycle', section: 'training', sectionTitle: 'Training, Testing & Maintenance', placeholder: 'Enter maintenance and review cycle...', isCustom: false, gridCols: 1, rows: 4 }
  ]
}

const initializeExtractedData = (planType: string): ExtractedData => {
  // Unified fields for all plan types
  return {
    plan_id: null,
    purpose_scope: null,
    regulatory_references: null,
    critical_services: null,
    dependencies_internal: null,
    dependencies_external: null,
    risk_assessment_summary: null,
    bia_summary: null,
    rto_targets: null,
    rpo_targets: null,
    critical_systems: null,
    critical_applications: null,
    databases_list: null,
    supporting_infrastructure: null,
    third_party_services: null,
    incident_types: null,
    alternate_work_locations: null,
    communication_plan_internal: null,
    communication_plan_bank: null,
    roles_responsibilities: null,
    training_testing_schedule: null,
    maintenance_review_cycle: null,
    disaster_scenarios: null,
    disaster_declaration_process: null,
    data_backup_strategy: null,
    recovery_site_details: null,
    failover_procedures: null,
    failback_procedures: null,
    network_recovery_steps: null,
    application_restoration_order: null,
    testing_validation_schedule: null
  }
}

// Field management functions
const addCustomField = () => {
  if (!newFieldForm.value.key || !newFieldForm.value.label) {
    PopupService.warning('Please provide both field key and label', 'Validation Error')
    return
  }
  
  // Validate key format (must be valid JavaScript identifier)
  const keyRegex = /^[a-zA-Z_][a-zA-Z0-9_]*$/
  if (!keyRegex.test(newFieldForm.value.key)) {
    PopupService.warning('Field key must start with a letter or underscore and contain only letters, numbers, and underscores', 'Invalid Key Format')
    return
  }
  
  // Check if key already exists
  if (fieldDefinitions.value.some(f => f.key === newFieldForm.value.key)) {
    PopupService.warning('A field with this key already exists', 'Duplicate Key')
    return
  }
  
  // Get existing section title if section already exists
  let sectionTitle = newFieldForm.value.sectionTitle
  const existingSection = fieldDefinitions.value.find(f => f.section === newFieldForm.value.section)
  if (existingSection && existingSection.sectionTitle) {
    sectionTitle = existingSection.sectionTitle
  }
  
  const newField: FieldDefinition = {
    id: `custom_${Date.now()}`,
    key: newFieldForm.value.key,
    label: newFieldForm.value.label,
    section: newFieldForm.value.section,
    sectionTitle: sectionTitle,
    placeholder: newFieldForm.value.placeholder,
    isCustom: true,
    gridCols: newFieldForm.value.gridCols || 1,
    rows: newFieldForm.value.rows || 3
  }
  
  fieldDefinitions.value.push(newField)
  
  // Initialize the field value in extractedData
  extractedData.value[newField.key] = null
  
  // Reset form
  newFieldForm.value = {
    key: '',
    label: '',
    section: 'custom',
    sectionTitle: 'Custom Fields',
    placeholder: 'Enter value...',
    gridCols: 1,
    rows: 3
  }
  
  showAddFieldModal.value = false
  PopupService.success('Custom field added successfully', 'Field Added')
}

const removeField = (fieldId: string) => {
  const field = fieldDefinitions.value.find(f => f.id === fieldId)
  if (!field) return
  
  // Don't allow removing predefined fields (optional - you can change this)
  if (!field.isCustom) {
    const confirmed = confirm(`Are you sure you want to remove the field "${field.label}"? This is a predefined field.`)
    if (!confirmed) return
  }
  
  // Move field to removedFields instead of deleting
  const index = fieldDefinitions.value.findIndex(f => f.id === fieldId)
  if (index > -1) {
    const removedField = { ...fieldDefinitions.value[index] }
    fieldDefinitions.value.splice(index, 1)
    
    // Add to removed fields if not already there
    if (!removedFields.value.find(f => f.id === fieldId)) {
      removedFields.value.push(removedField)
    }
  }
  
  // Note: We keep the data in extractedData for display, but it won't be saved to backend
  
  PopupService.success('Field removed successfully', 'Field Removed')
}

const removeSection = (section: string) => {
  const sectionFields = fieldDefinitions.value.filter(f => f.section === section)
  if (sectionFields.length === 0) return
  
  const sectionTitle = sectionFields[0]?.sectionTitle || section
  const confirmed = confirm(`Are you sure you want to remove the entire section "${sectionTitle}"? This will remove ${sectionFields.length} field(s).`)
  if (!confirmed) return
  
  // Move all fields in this section to removedFields
  sectionFields.forEach(field => {
    const index = fieldDefinitions.value.findIndex(f => f.id === field.id)
    if (index > -1) {
      const removedField = { ...fieldDefinitions.value[index] }
      fieldDefinitions.value.splice(index, 1)
      
      // Add to removed fields if not already there
      if (!removedFields.value.find(f => f.id === field.id)) {
        removedFields.value.push(removedField)
      }
    }
  })
  
  PopupService.success(`Section "${sectionTitle}" removed successfully`, 'Section Removed')
}

const getFieldsBySection = (section: string) => {
  return fieldDefinitions.value.filter(f => f.section === section)
}

const getSectionGroups = () => {
  const sections = new Map<string, { title: string, fields: FieldDefinition[] }>()
  
  fieldDefinitions.value.forEach(field => {
    if (!sections.has(field.section)) {
      sections.set(field.section, { title: field.sectionTitle, fields: [] })
    }
    sections.get(field.section)!.fields.push(field)
  })
  
  return Array.from(sections.entries()).map(([section, data]) => ({
    section,
    title: data.title,
    fields: data.fields
  }))
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
    object_type: 'PLAN EVALUATION',
    object_id: '',
    due_date: tomorrow.toISOString().slice(0, 16)
  }
  
  console.log('Initialized assignment form:', form)
  return form
}

const handleStep2Click = () => {
  if (!isStep2Enabled.value) {
    PopupService.warning(
      'Please complete OCR extraction and save data in Step 1 before accessing Step 2.',
      'Step 2 Disabled'
    )
    return
  }
  goToStep(2)
}

const goToStep = (step: number) => {
  // Prevent navigation to Step 2 if conditions aren't met
  if (step === 2 && !isStep2Enabled.value) {
    PopupService.warning(
      'Please complete OCR extraction and save data in Step 1 before accessing Step 2.',
      'Step 2 Disabled'
    )
    return
  }
  
  currentStep.value = step
  if (step === 2 && selectedPlan.value && selectedPlan.value.plan_id) {
    // Initialize assignment form for selected plan when going to step 2
    assignmentForm.value = initializeAssignmentForm(selectedPlan.value.plan_type)
    assignmentForm.value.object_id = selectedPlan.value.plan_id.toString()
    assignmentForm.value.object_type = 'PLAN EVALUATION'
    console.log('Initialized assignment form for plan:', selectedPlan.value.plan_id)
  } else if (step === 2) {
    // Reset assignment form if no plan is selected
    assignmentForm.value = {
      workflow_name: '',
      plan_type: '',
      assigner_id: '',
      assigner_name: '',
      assignee_id: '',
      assignee_name: '',
      object_type: 'PLAN EVALUATION',
      object_id: '',
      due_date: ''
    }
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
    let userId = null
    let userName = null
    
    // Method 1: Try to get from JWT token FIRST (most reliable source of current logged-in user)
    // This should be checked first to avoid using stale localStorage values
    try {
      const token = localStorage.getItem('access_token') || localStorage.getItem('session_token')
      if (token) {
        // Decode JWT token to get user_id
        const base64Url = token.split('.')[1]
        if (base64Url) {
          const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
          const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
            return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)
          }).join(''))
          const payload = JSON.parse(jsonPayload)
          userId = payload.user_id || payload.userId || payload.UserId || payload.sub || payload.userid
          if (userId) {
            console.log('✅ Extracted user_id from JWT token (most reliable source):', userId)
          }
        }
      }
    } catch (e) {
      console.warn('⚠️ Error extracting user_id from token:', e)
    }
    
    // Method 2: Try to get from Vuex store (second most reliable)
    if (!userId) {
      const currentUser = store.getters['auth/currentUser']
      if (currentUser) {
        userId = currentUser.UserId || currentUser.user_id || currentUser.userId || currentUser.userid || currentUser.id
        userName = currentUser.UserName || currentUser.username || `${currentUser.first_name || ''} ${currentUser.last_name || ''}`.trim() || currentUser.email
        if (userId) {
          console.log('✅ Extracted user_id from Vuex store:', userId)
        }
      }
    }
    
    // Method 3: Try to parse current_user from localStorage (check UserId with capital letters)
    if (!userId) {
      try {
        const userStr = localStorage.getItem('current_user')
        if (userStr) {
          const parsedUser = JSON.parse(userStr)
          // Check for UserId (capital U, capital I) first, then lowercase variants
          userId = parsedUser.UserId || parsedUser.user_id || parsedUser.userId || parsedUser.userid || parsedUser.id
          if (userId) {
            console.log('✅ Extracted user_id from localStorage current_user:', userId)
          }
          // Try to get username, but it might be encrypted
          if (!userName) {
            userName = parsedUser.UserName || parsedUser.username || `${parsedUser.first_name || ''} ${parsedUser.last_name || ''}`.trim() || parsedUser.email
          }
        }
      } catch (error) {
        console.warn('⚠️ Error parsing user from localStorage (may be encrypted):', error)
      }
    }
    
    // Method 4: Fallback to localStorage user_id (least reliable - may be stale)
    // Only use this if JWT token and Vuex store don't have the user
    if (!userId) {
      userId = localStorage.getItem('user_id') || 
               localStorage.getItem('userId') || 
               localStorage.getItem('UserId')
      if (userId) {
        console.log('⚠️ Using user_id from localStorage (fallback - may be stale):', userId)
      }
    }
    
    // Method 5: Try to get username from users list (if already loaded and userId found)
    if (userId && !userName && users.value && users.value.length > 0) {
      const user = users.value.find(u => u.user_id == userId || u.userid == userId)
      if (user) {
        userName = user.username || user.display_name || `${user.first_name || ''} ${user.last_name || ''}`.trim() || user.email
        if (userName) {
          console.log('✅ Found username from users list:', userName)
        }
      }
    }
    
    // Method 6: If username looks encrypted (starts with gAAAAA), try to get from users list
    if (userName && userName.startsWith('gAAAAA') && users.value && users.value.length > 0 && userId) {
      const user = users.value.find(u => u.user_id == userId || u.userid == userId)
      if (user) {
        userName = user.username || user.display_name || `${user.first_name || ''} ${user.last_name || ''}`.trim() || user.email
        console.log('✅ Decrypted username from users list:', userName)
      }
    }
    
    if (userId) {
      // Auto-fill assigner
      assignmentForm.value.assigner_id = userId.toString()
      assignmentForm.value.assigner_name = userName || `User ${userId}`
      
      // Set assignee to same as assigner
      assignmentForm.value.assignee_id = userId.toString()
      assignmentForm.value.assignee_name = userName || `User ${userId}`
      
      console.log('✅ Auto-filled assigner/assignee:', { userId, userName })
    } else {
      console.error('❌ No current user found in any storage location')
      console.log('Store state:', store.getters['auth/currentUser'])
      console.log('localStorage user_id:', localStorage.getItem('user_id'))
      console.log('localStorage current_user:', localStorage.getItem('current_user'))
      PopupService.warning('Unable to get current user information. Please log in again or select assignee manually.', 'User Not Found')
      noApprovalNeeded.value = false
    }
  } else {
    // Reset assignee when unchecked
    assignmentForm.value.assignee_id = ''
    assignmentForm.value.assignee_name = ''
  }
}

const resetAssignmentForm = () => {
  noApprovalNeeded.value = false
  if (selectedPlan.value && selectedPlan.value.plan_id) {
    assignmentForm.value = initializeAssignmentForm(selectedPlan.value.plan_type)
    assignmentForm.value.object_id = selectedPlan.value.plan_id
    assignmentForm.value.object_type = 'PLAN EVALUATION'
  } else {
    assignmentForm.value = {
      workflow_name: '',
      plan_type: '',
      assigner_id: '',
      assigner_name: '',
      assignee_id: '',
      assignee_name: '',
      object_type: 'PLAN EVALUATION',
      object_id: '',
      due_date: ''
    }
  }
}

// Show TPRM Consent Modal
async function showTPRMConsentModal(actionType, config) {
  console.log('[TPRM Consent] Showing consent modal for action:', actionType, 'config:', config)
  
  if (!consentModalRef.value) {
    console.error('[TPRM Consent] Consent modal ref not available - waiting for component to mount')
    // Wait a bit for component to mount
    await nextTick()
    if (!consentModalRef.value) {
      console.error('[TPRM Consent] Consent modal ref still not available after nextTick')
      return false
    }
  }
  
  try {
    // Show the modal and wait for user response
    const accepted = await consentModalRef.value.show(actionType, config)
    
    console.log('[TPRM Consent] Consent modal result:', accepted)
    
    // Ensure boolean return value
    return accepted === true || accepted === 'true'
  } catch (error) {
    console.error('[TPRM Consent] Error showing consent modal:', error)
    // If modal was cancelled/rejected, return false
    if (error.message && error.message.includes('cancelled')) {
      return false
    }
    return false
  }
}

// Helper function to actually create the assignment (called after consent is obtained)
const createAssignmentAction = async (consentConfig) => {
  console.log('[TPRM Consent] Creating assignment action, consentConfig:', consentConfig)
  
  // Prepare the assignment data with proper structure
  // If no approval needed, set assignee to same as assigner
  const assignerId = parseInt(assignmentForm.value.assigner_id)
  const assigneeId = noApprovalNeeded.value 
    ? assignerId  // Use assigner_id when no approval needed
    : parseInt(assignmentForm.value.assignee_id || assignmentForm.value.assigner_id)
  
  const assigneeName = noApprovalNeeded.value
    ? assignmentForm.value.assigner_name  // Use assigner_name when no approval needed
    : assignmentForm.value.assignee_name || assignmentForm.value.assigner_name
  
  // Ensure assignee_name is set when no approval needed
  const finalAssigneeName = noApprovalNeeded.value && !assigneeName
    ? assignmentForm.value.assigner_name || 'Auto-assigned'
    : assigneeName
  
  // Ensure assignee_id is set when no approval needed
  const finalAssigneeId = noApprovalNeeded.value && !assigneeId
    ? assignerId
    : assigneeId
  
  const assignmentData = {
    workflow_name: assignmentForm.value.workflow_name,
    plan_type: selectedPlan.value.plan_type,
    assigner_id: assignerId,
    assigner_name: assignmentForm.value.assigner_name || '',
    assignee_id: finalAssigneeId,
    assignee_name: finalAssigneeName || '',
    object_type: 'PLAN EVALUATION',
    object_id: parseInt(selectedPlan.value.plan_id), // Ensure it's an integer
    due_date: assignmentForm.value.due_date,
    no_approval_needed: noApprovalNeeded.value
  }
  
  // Add consent data to assignment data if consent was provided
  if (consentConfig) {
    assignmentData.consent_accepted = true
    assignmentData.consent_config_id = consentConfig.config_id
    assignmentData.framework_id = 1 // Default TPRM framework
  }
  
  console.log('Sending assignment data:', assignmentData)
  
  // Call the API to create the approval assignment
  const response = await api.approvals.createAssignment(assignmentData)
  
  console.log('Assignment created successfully:', response)
  
  return response
}

const createAssignment = async () => {
  if (!selectedPlan.value) {
    PopupService.warning('No plan selected. Please select a plan first.', 'No Plan Selected')
    return
  }

  isSubmittingAssignment.value = true
  
  try {
    console.log('[TPRM Consent] ========== Starting consent flow for: tprm_create_plans')
    console.log('Creating assignment for plan:', selectedPlan.value.plan_id, assignmentForm.value)
    
    // Ensure all required fields are filled
    if (!assignmentForm.value.workflow_name || !assignmentForm.value.assigner_id || !assignmentForm.value.due_date) {
      PopupService.warning('Please fill in all required fields (Workflow Name, Assigner, Due Date)', 'Required Fields Missing')
      isSubmittingAssignment.value = false
      return
    }
    
    // Validate assigner_name is set
    if (!assignmentForm.value.assigner_name || assignmentForm.value.assigner_name.trim() === '') {
      PopupService.warning('Assigner name is required. Please select an assigner from the dropdown.', 'Assigner Name Required')
      isSubmittingAssignment.value = false
      return
    }
    
    if (!noApprovalNeeded.value && !assignmentForm.value.assignee_id) {
      PopupService.warning('Please select an assignee or check "No Approval Needed"', 'Assignee Required')
      isSubmittingAssignment.value = false
      return
    }
    
    // If no approval needed, ensure assignee is set to assigner
    if (noApprovalNeeded.value) {
      if (!assignmentForm.value.assigner_id) {
        PopupService.warning('Please select an assigner first', 'Assigner Required')
        isSubmittingAssignment.value = false
        return
      }
    }
    
    // Wrap assignment creation with consent check
    // The consent modal will be shown by executeWithTPRMConsent if consent is required
    const response = await executeWithTPRMConsent(
      TPRM_CONSENT_ACTIONS.CREATE_PLANS,
      createAssignmentAction,
      showTPRMConsentModal
    )
    
    // Check if assignment creation was cancelled due to consent rejection
    if (response === null) {
      // Consent was rejected - user cancelled the action
      console.log('[Plan Assignment] Assignment creation cancelled - consent not accepted')
      PopupService.info('Assignment creation cancelled. You must accept the consent to create the assignment.', 'Consent Required')
      isSubmittingAssignment.value = false
      return
    }
    
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
      object_type: 'PLAN EVALUATION',
      object_id: '',
      due_date: ''
    }
    
    // Go back to step 1 to select another plan
    goToStep(1)
    
  } catch (error) {
    console.error('Error creating assignment:', error)
    
    // Check if error is due to consent rejection
    if (error.message && (error.message.includes('consent') || error.message.includes('Consent') || error.message.includes('cancelled'))) {
      PopupService.warning('Assignment creation cancelled. You must accept the consent to create the assignment.', 'Consent Required')
      isSubmittingAssignment.value = false
      return
    }
    
    let errorMessage = 'Error creating assignment. Please try again.'
    
    // Try to extract detailed error message from response
    if (error.response?.data) {
      const errorData = error.response.data
      
      // Check for validation errors
      if (errorData.errors && Array.isArray(errorData.errors)) {
        errorMessage = errorData.errors.join(', ')
      } else if (errorData.errors && typeof errorData.errors === 'object') {
        errorMessage = Object.values(errorData.errors).flat().join(', ')
      } else if (errorData.message) {
        errorMessage = errorData.message
      } else if (errorData.error) {
        errorMessage = errorData.error
      } else if (errorData.detail) {
        errorMessage = errorData.detail
      } else if (typeof errorData === 'string') {
        errorMessage = errorData
      }
    } else if (error.message) {
      errorMessage = error.message
    }
    
    // Log the full error response for debugging
    console.error('Full error response:', error.response?.data)
    console.error('Error status:', error.response?.status)
    
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
    const dataToSave: any = {}
    dataToSave.plan_id = selectedPlan.value.plan_id
    
    // Helper function to check if a value is empty/null
    const isEmpty = (val: any): boolean => {
      if (val === null || val === undefined) return true
      if (typeof val === 'string' && val.trim() === '') return true
      if (Array.isArray(val) && val.length === 0) return true
      if (typeof val === 'object' && Object.keys(val).length === 0) return true
      return false
    }
    
    // Only save fields that are in fieldDefinitions (including custom fields) and have non-empty values
    fieldDefinitions.value.forEach(fieldDef => {
      const value = extractedData.value[fieldDef.key]
      
      // Skip null, undefined, empty strings, empty arrays, and empty objects
      if (isEmpty(value)) {
        return
      }
      
      // Parse JSON fields - convert string representations back to objects
      const jsonFields = [
        'regulatory_references', 'critical_services', 'dependencies_internal', 
        'dependencies_external', 'rto_targets', 'rpo_targets', 'incident_types',
        'alternate_work_locations', 'roles_responsibilities', 'critical_systems',
        'critical_applications', 'databases_list', 'supporting_infrastructure',
        'third_party_services', 'disaster_scenarios', 'application_restoration_order'
      ]
      
      // Check if field should be parsed as JSON (either predefined JSON field or custom field that looks like JSON)
      if (jsonFields.includes(fieldDef.key) || (fieldDef.isCustom && typeof value === 'string' && (value.trim().startsWith('[') || value.trim().startsWith('{')))) {
        try {
          const parsed = JSON.parse(value as string)
          // Only save if parsed value is not empty
          if (!isEmpty(parsed)) {
            dataToSave[fieldDef.key] = parsed
          }
        } catch (e) {
          console.warn(`Failed to parse JSON for field ${fieldDef.key}:`, e)
          // If parsing fails, try to create a simple array from comma-separated values
          if (typeof value === 'string' && value.includes(',')) {
            const arrayValue = value.split(',').map(item => item.trim()).filter(item => item)
            if (arrayValue.length > 0) {
              dataToSave[fieldDef.key] = arrayValue
            }
          } else if (!isEmpty(value)) {
            // Save as string if not empty
            dataToSave[fieldDef.key] = typeof value === 'string' ? value.trim() : value
          }
        }
      } else {
        // For non-JSON fields, trim strings and save if not empty
        if (typeof value === 'string') {
          const trimmed = value.trim()
          if (trimmed !== '') {
            dataToSave[fieldDef.key] = trimmed
          }
        } else if (!isEmpty(value)) {
          dataToSave[fieldDef.key] = value
        }
      }
    })
    
    console.log('Fields in fieldDefinitions:', fieldDefinitions.value.map(f => f.key))
    console.log('Data to save (filtered, only fields in fieldDefinitions):', dataToSave)
    console.log(`Saving ${Object.keys(dataToSave).length - 1} fields (excluding plan_id)`)
    
    // Use the OCR microservice extraction endpoint - OCR endpoints are at /api/tprm/ocr/
    // Use the http instance since it already has the correct baseURL (/api/tprm)
    const endpoint = `ocr/plans/${selectedPlan.value.plan_id}/extract/`
    
    // Send unified payload with all fields (including custom fields)
    const response = await http.post(endpoint, {
      extracted_data: dataToSave
    }, {
      timeout: 30000 // 30 seconds timeout for saving data
    })
    
    // Check for risk generation info in response
    let successMessage = 'Extracted information has been saved successfully'
    const responseData = (response as any)?.data || (response as any)
    if (responseData?.risk_generation) {
      const riskInfo = responseData.risk_generation
      if (riskInfo.status === 'started') {
        successMessage += '. Risk generation has started in the background - risks will appear in Risk Analytics shortly.'
      } else if (riskInfo.status === 'deferred') {
        successMessage += '. Risk generation will start shortly - check Risk Analytics in a few minutes.'
      }
    } else if (responseData?.risk_message) {
      successMessage += '. ' + responseData.risk_message
    }
    
    PopupService.success(successMessage, 'Data Saved')
    
    // Mark OCR as saved - this enables Step 2
    isOCRSaved.value = true
    
    // Create notification with risk generation info
    await notificationService.createOCRNotification('data_saved', {
      plan_id: selectedPlan.value.plan_id,
      risk_generation: responseData?.risk_generation
    })
    
    // Update plan status to OCR_COMPLETED and navigate to Step 2
    try {
      await http.patch(`/bcpdrp/ocr/plans/${selectedPlan.value.plan_id}/status/`, {
        status: 'OCR_COMPLETED'
      })
      
      // Update the plan status in our local state
      const plan = availablePlans.value.find(p => p.plan_id === selectedPlan.value.plan_id)
      if (plan) {
        plan.status = 'OCR_COMPLETED'
      }
      
      // Advance to Step 2 after a short delay
      setTimeout(() => {
        goToStep(2)
      }, 1000)
    } catch (statusErr) {
      console.error('Error updating plan status:', statusErr)
      // Don't show error to user if status update fails, data was saved successfully
      // Still navigate to Step 2
      setTimeout(() => {
        goToStep(2)
      }, 1000)
    }
  } catch (err) {
    PopupService.error(`Error saving data: ${err.message}`, 'Save Failed')
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
    await http.patch(`/api/bcpdrp/ocr/plans/${selectedPlan.value.plan_id}/status/`, {
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
    
    // Use OCR microservice endpoint - OCR endpoints are at /api/tprm/ocr/
    // Use the http instance since it already has the correct baseURL (/api/tprm)
    const endpoint = `ocr/plans/${selectedPlan.value.plan_id}/run/`
    
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
    console.log('Extracted data:', response.data?.extracted_data)
    
    // Update the extracted data with the OCR results
    // The HTTP interceptor unwraps the response, so data is directly accessible
    if (response.data?.extracted_data) {
      console.log('Setting extracted data:', response.data.extracted_data)
      
      // Process the extracted data to handle JSON fields properly
      const processedData = { ...response.data.extracted_data }
      
      // Convert JSON objects/arrays to strings for form display
      const jsonFields = [
        'regulatory_references', 'critical_services', 'dependencies_internal', 
        'dependencies_external', 'rto_targets', 'rpo_targets', 'incident_types',
        'alternate_work_locations', 'roles_responsibilities', 'critical_systems',
        'critical_applications', 'databases_list', 'supporting_infrastructure',
        'third_party_services', 'disaster_scenarios', 'application_restoration_order'
      ]
      
      // Process all fields from OCR response
      Object.keys(processedData).forEach(field => {
        // Handle JSON fields
        if (jsonFields.includes(field) && typeof processedData[field] === 'object') {
          processedData[field] = JSON.stringify(processedData[field], null, 2)
        }
        // Handle custom fields that might be objects/arrays
        else if (typeof processedData[field] === 'object' && !fieldDefinitions.value.some(f => f.key === field)) {
          // Check if it's a custom field that should be stringified
          if (Array.isArray(processedData[field]) || (typeof processedData[field] === 'object' && processedData[field] !== null)) {
            processedData[field] = JSON.stringify(processedData[field], null, 2)
          }
        }
        
        // Add custom fields to field definitions if they don't exist
        if (!fieldDefinitions.value.some(f => f.key === field)) {
          const customField: FieldDefinition = {
            id: `custom_${field}_${Date.now()}`,
            key: field,
            label: field.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
            section: 'custom',
            sectionTitle: 'Custom Fields',
            placeholder: 'Enter value...',
            isCustom: true,
            gridCols: 1,
            rows: 3
          }
          fieldDefinitions.value.push(customField)
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
    
  } catch (err) {
    console.error('Error running OCR:', err)
    showError(`Error running OCR: ${err.response?.data?.message || err.message || 'Unknown error'}`)
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
