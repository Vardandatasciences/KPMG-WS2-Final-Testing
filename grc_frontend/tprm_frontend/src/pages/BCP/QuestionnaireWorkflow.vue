<template>
  <div class="questionnaire-workflow-page p-6 max-w-7xl mx-auto space-y-6">
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
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2V7a2 2 0 00-2-2H9z"/>
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 9h10m-10 4h10m-10 4h10"/>
            </svg>
            <span v-else class="breadcrumb-number">1</span>
          </div>
          <div class="breadcrumb-content">
            <span class="breadcrumb-title">Create Questionnaire</span>
            <span class="breadcrumb-description">Create and configure your questionnaire</span>
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
            'breadcrumb-item--disabled': !canProceedToStep2 && currentStep !== 2
          }"
          @click="handleStep2Click"
          :title="!canProceedToStep2 ? 'Please complete questionnaire creation in Step 1 first' : ''"
        >
          <div class="breadcrumb-icon">
            <svg v-if="currentStep === 2" class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z"/>
            </svg>
            <span v-else class="breadcrumb-number">2</span>
          </div>
          <div class="breadcrumb-content">
            <span class="breadcrumb-title">Assign for Testing</span>
            <span class="breadcrumb-description">Assign questionnaire for testing</span>
          </div>
        </div>
      </nav>
    </div>

    <!-- Step 1: Create Questionnaire -->
    <div v-if="currentStep === 1" class="space-y-6">
      <div class="card">
        <div class="card-header">
          <h3 class="card-title flex items-center gap-2">
            <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2V7a2 2 0 00-2-2H9z"/>
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 9h10m-10 4h10m-10 4h10"/>
            </svg>
            Create New Questionnaire
          </h3>
        </div>
        <div class="card-content space-y-6">
          <!-- Template Actions -->
          <div class="flex gap-3 flex-wrap justify-end">
            <button 
              type="button" 
              class="btn btn--outline" 
              @click="openTemplateSelector"
            >
              <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/>
              </svg>
              Select a Template
            </button>
            <button 
              type="button" 
              class="btn btn--outline" 
              @click="navigateToTemplateScreen"
            >
              <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
              </svg>
              Create a Template
            </button>
            <button 
              type="button" 
              class="btn btn--outline" 
              @click="saveAsTemplate"
              :disabled="!canSaveAsTemplate"
            >
              <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4"/>
              </svg>
              Save as Template
            </button>
          </div>

          <!-- Plan Selection -->
          <div class="plans-dropdown-section">
            <div class="plans-dropdown">
              <label class="modern-label">
                <div class="label-content">
                  <div class="label-icon">
                    <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                    </svg>
                  </div>
                  <span class="label-text">Select Plan <span class="text-destructive">*</span></span>
                </div>
              </label>
              <div class="modern-dropdown" :class="{ 'is-open': isPlanDropdownOpen }">
                <button 
                  class="modern-trigger"
                  @click="togglePlanDropdown"
                  @blur="closePlanDropdown"
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
                    <svg class="dropdown-arrow" :class="{ 'rotated': isPlanDropdownOpen }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
                    </svg>
                  </div>
                </button>
                <Transition name="dropdown">
                  <div v-if="isPlanDropdownOpen" class="table-dropdown-menu">
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
                            <td>
                              <span class="badge badge--neutral">
                                {{ plan.criticality }}
                              </span>
                            </td>
                            <td>
                              <span class="badge badge--neutral">
                                {{ typeof plan.status === 'string' ? plan.status.replace(/_/g, ' ') : 'N/A' }}
                              </span>
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

          <!-- Questionnaire Details -->
          <div class="grid grid-cols-3 gap-4">
            <div class="space-y-2">
              <label class="label" for="title">Questionnaire Title</label>
              <input 
                class="input" 
                id="title" 
                placeholder="e.g., Payments DC Failover Test 2025"
                v-model="questionnaire.title"
              />
            </div>
            <div class="space-y-2">
              <label class="label" for="planType">Plan Type</label>
              <div class="plan-type-dropdown-wrapper">
                <div 
                  class="plan-type-dropdown-select"
                  :class="{ 'is-open': isPlanTypeDropdownOpen, 'has-value': questionnaire.planType, 'is-disabled': !!selectedPlanId }"
                  @click="!selectedPlanId && togglePlanTypeDropdown()"
                  @blur="closePlanTypeDropdown"
                  :tabindex="selectedPlanId ? -1 : 0"
                >
                  <span v-if="questionnaire.planType" class="selected-plan-type">{{ questionnaire.planType }}</span>
                  <span v-else class="placeholder-plan-type">Select plan type</span>
                  <svg 
                    v-if="!selectedPlanId"
                    class="plan-type-arrow" 
                    :class="{ 'rotated': isPlanTypeDropdownOpen }"
                    fill="none" 
                    stroke="currentColor" 
                    viewBox="0 0 24 24"
                  >
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
                  </svg>
                </div>
                <Transition name="dropdown">
                  <div v-if="isPlanTypeDropdownOpen && !selectedPlanId" class="plan-type-dropdown-menu">
                    <div 
                      v-for="pt in planTypes" 
                      :key="pt.id" 
                      class="plan-type-dropdown-item"
                      :class="{ 'is-selected': questionnaire.planType === pt.value }"
                      @click.stop="selectPlanTypeValue(pt.value)"
                    >
                      <span>{{ pt.value }}</span>
                      <svg 
                        v-if="questionnaire.planType === pt.value"
                        class="check-icon-small"
                        fill="none" 
                        stroke="currentColor" 
                        viewBox="0 0 24 24"
                      >
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                      </svg>
                    </div>
                    <div class="plan-type-divider"></div>
                    <div 
                      class="plan-type-dropdown-item add-new-plan-type"
                      @click.stop="openAddPlanTypeModal"
                    >
                      <svg class="add-icon-small" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
                      </svg>
                      <span>Add New Plan Type</span>
                    </div>
                  </div>
                </Transition>
              </div>
            </div>
            <div class="space-y-2">
              <label class="label" for="description">Description</label>
              <textarea 
                class="textarea" 
                id="description" 
                placeholder="Questionnaire for validating disaster recovery readiness."
                v-model="questionnaire.description"
                rows="3"
              ></textarea>
            </div>
          </div>

          <!-- Questions Section -->
          <div class="questions-section">
            <h4 v-if="mockQuestions.length > 0" class="font-medium mb-4">Questions</h4>
            <div v-if="mockQuestions.length > 0" class="overflow-x-auto">
              <table class="table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Question Text</th>
                    <th>Type</th>
                    <th>Required?</th>
                    <th>Weight</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(question, index) in mockQuestions" :key="question.id" class="hover:bg-muted/50">
                    <td>{{ index + 1 }}</td>
                    <td class="max-w-md">{{ question.text }}</td>
                    <td>
                      <div class="badge badge--secondary">{{ question.type }}</div>
                      <div v-if="(question.type === 'MULTIPLE_CHOICE' || question.type === 'CHECKBOX') && question.choiceOptions?.length > 0" class="choice-options-display mt-2">
                        <div class="text-xs text-muted-foreground mb-1">
                          {{ question.choiceOptions.length }} options:
                        </div>
                        <div class="choice-options-list">
                          <div 
                            v-for="(option, optionIndex) in question.choiceOptions" 
                            :key="optionIndex" 
                            class="choice-option-item"
                          >
                            <span class="choice-option-number">{{ optionIndex + 1 }}.</span>
                            <span class="choice-option-text">{{ option }}</span>
                          </div>
                        </div>
                      </div>
                      <div v-if="question.allowDocumentUpload" class="text-xs text-muted-foreground mt-1">
                        📎 Document upload allowed
                      </div>
                    </td>
                    <td>
                      {{ question.required ? "✓" : "—" }}
                    </td>
                    <td>{{ question.weight }}</td>
                    <td>
                      <div class="flex gap-2">
                        <button 
                          class="btn btn--ghost btn--sm" 
                          @click="editQuestion(index)"
                          title="Edit question"
                        >
                          <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                          </svg>
                        </button>
                        <button 
                          class="btn btn--ghost btn--sm" 
                          @click="deleteQuestion(index)"
                          title="Delete question"
                        >
                          <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                          </svg>
                        </button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div class="mt-6 p-4 bg-muted/30 rounded-lg">
              <h4 class="font-medium mb-4">{{ editingQuestionIndex !== null ? 'Edit Question' : 'Add New Question' }}</h4>
              <div class="grid grid-cols-1 gap-4">
                <!-- Question Text and Answer Type in one row -->
                <div class="grid grid-cols-12 gap-4">
                  <div class="space-y-2 col-span-8">
                    <label class="label">Question Text</label>
                    <textarea class="textarea" placeholder="Enter your question..." rows="2" v-model="newQuestion.text"></textarea>
                  </div>
                  <div class="space-y-2 col-span-4">
                    <label class="label">Answer Type</label>
                    <select class="select" v-model="newQuestion.type">
                      <option value="">Select type</option>
                      <option value="TEXT">TEXT</option>
                      <option value="TEXTAREA">TEXTAREA</option>
                      <option value="NUMBER">NUMBER</option>
                      <option value="YES_NO">YES_NO</option>
                      <option value="BOOLEAN">BOOLEAN</option>
                      <option value="MULTIPLE_CHOICE">MULTIPLE_CHOICE</option>
                      <option value="CHECKBOX">CHECKBOX</option>
                      <option value="RATING">RATING</option>
                      <option value="SCALE">SCALE</option>
                      <option value="DATE">DATE</option>
                      <option value="FILE_UPLOAD">FILE_UPLOAD</option>
                    </select>
                  </div>
                </div>
                <div class="space-y-4">
                  <div v-if="newQuestion.type === 'MULTIPLE_CHOICE' || newQuestion.type === 'CHECKBOX'" class="space-y-2">
                    <label class="label">Choice Options</label>
                    <div class="space-y-2">
                      <div v-for="(option, index) in newQuestion.choiceOptions" :key="index" class="flex gap-2">
                        <input 
                          class="input flex-1" 
                          v-model="newQuestion.choiceOptions[index]"
                          :placeholder="`Option ${index + 1}`"
                        />
                        <button 
                          type="button" 
                          class="btn btn--ghost btn--sm"
                          @click="removeChoiceOption(index)"
                          :disabled="newQuestion.choiceOptions.length <= 2"
                        >
                          <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                          </svg>
                        </button>
                      </div>
                      <button 
                        type="button" 
                        class="btn btn--ghost btn--sm"
                        @click="addChoiceOption"
                      >
                        <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
                        </svg>
                        Add Option
                      </button>
                    </div>
                  </div>
                  <div class="flex items-center space-x-2">
                    <input type="checkbox" id="required" v-model="newQuestion.required" class="checkbox" />
                    <label class="label" for="required">Required</label>
                  </div>
                  <div class="flex items-center space-x-2">
                    <input type="checkbox" id="allowDocumentUpload" v-model="newQuestion.allowDocumentUpload" class="checkbox" />
                    <label class="label" for="allowDocumentUpload">Allow Document Upload (Evidence)</label>
                  </div>
                </div>
              </div>
              <div class="flex gap-2 mt-4">
                <button class="btn btn--primary" @click="addQuestion">
                  <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
                  </svg>
                  {{ editingQuestionIndex !== null ? 'Update Question' : 'Add Question' }}
                </button>
                <button 
                  v-if="editingQuestionIndex !== null" 
                  class="btn btn--outline" 
                  @click="cancelEditQuestion"
                >
                  Cancel
                </button>
              </div>
            </div>

            <div class="flex gap-4 mt-6">
              <button class="btn btn--outline" @click="loadMockData">
                <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/>
                </svg>
                Load Data
              </button>
              <button class="btn btn--primary" @click="proceedToStep2" :disabled="!canProceedToStep2">
                <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4"/>
                </svg>
                Save and Assign
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Step 2: Assignment Form -->
    <div v-if="currentStep === 2" class="space-y-6">
      <div class="card">
        <div class="card-header">
          <h3 class="card-title flex items-center gap-2">
            <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
            </svg>
            Assign Questionnaire for Testing
          </h3>
        </div>
        <div class="card-content space-y-6">
          <form @submit.prevent="createAssignment" class="space-y-6">
            <!-- Row 1: Plan Type, Object ID, Object Type -->
            <div class="form-grid-3">
              <div class="space-y-2">
                <label for="planType" class="block text-sm font-medium">Plan Type <span class="text-destructive">*</span></label>
                <select v-model="assignmentForm.plan_type" id="planType" class="input" required>
                  <option value="">Select plan type</option>
                  <option v-for="pt in planTypes" :key="pt.id" :value="pt.value">
                    {{ pt.value }}
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
              <button type="button" @click="goBackToStep1" class="btn btn--outline">
                <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"/>
                </svg>
                Back to Questionnaire
              </button>
              <button type="button" @click="resetAssignmentForm" class="btn btn--outline">
                <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
                </svg>
                Reset Form
              </button>
              <button type="submit" class="btn btn--primary" :disabled="isSubmitting">
                <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
                </svg>
                {{ isSubmitting ? 'Creating...' : 'Create Assignment' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Template Selection Modal -->
    <div v-if="showTemplateSelector" class="modal-overlay" @click.self="closeTemplateSelector">
      <div class="modal-content template-modal-content">
        <div class="modal-header">
          <h3 class="modal-title">Select a Template</h3>
          <button class="modal-close" @click="closeTemplateSelector">
            <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <div v-if="isLoadingTemplates" class="loading-state">
            <div class="loading-spinner"></div>
            <p>Loading templates...</p>
          </div>
          <div v-else-if="availableTemplates.length === 0" class="empty-state">
            <div class="empty-icon">📄</div>
            <p>No templates available</p>
            <p class="empty-subtitle">No templates found for {{ questionnaire.planType || 'selected plan type' }}</p>
          </div>
          <div v-else class="template-cards-grid">
            <div 
              v-for="template in availableTemplates" 
              :key="template.template_id"
              class="template-card"
              @click="selectTemplate(template)"
            >
              <div class="template-card-header">
                <div class="template-card-title-section">
                  <h4 class="template-card-name">{{ template.template_name }}</h4>
                  <div class="template-card-badges">
                    <span :class="['badge', template.module_type === 'PLANS' ? 'badge--default' : 'badge--secondary']">
                      {{ template.module_type }}
                    </span>
                    <span v-if="template.module_subtype" :class="['badge', 'badge--subtype']">
                      {{ template.module_subtype }}
                    </span>
                    <span class="badge badge--secondary">{{ template.template_type }}</span>
                  </div>
                </div>
                <span :class="['badge', getStatusBadgeClass(template.status)]">
                  {{ template.status }}
                </span>
              </div>
              
              <div class="template-card-body">
                <p v-if="template.template_description" class="template-card-description">
                  {{ template.template_description }}
                </p>
                <p v-else class="template-card-description text-muted-foreground italic">
                  No description provided
                </p>
                
                <div class="template-card-details">
                  <div class="template-detail-item">
                    <svg class="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                    </svg>
                    <span class="text-sm">{{ template.question_count || 0 }} Questions</span>
                  </div>
                  <div class="template-detail-item">
                    <svg class="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"/>
                    </svg>
                    <span class="text-sm">v{{ template.template_version || '1.0' }}</span>
                  </div>
                </div>
                
                <div v-if="template.created_at" class="template-card-footer">
                  <span class="text-xs text-muted-foreground">
                    Created: {{ formatDate(template.created_at) }}
                  </span>
                </div>
              </div>
              
              <div class="template-card-action">
                <button 
                  class="template-card-select-btn"
                  @click.stop="selectTemplate(template)"
                >
                  <span>Select Template</span>
                  <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Create Template Modal -->
    <div v-if="showCreateTemplateModal" class="modal-overlay" @click.self="closeCreateTemplateModal">
      <div class="modal-content max-w-2xl">
        <div class="modal-header">
          <h3 class="modal-title">Create New Template</h3>
          <button class="modal-close" @click="closeCreateTemplateModal">
            <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <form @submit.prevent="createTemplate" class="space-y-4">
            <div class="space-y-2">
              <label class="label">Template Name <span class="text-destructive">*</span></label>
              <input 
                class="input" 
                v-model="newTemplateForm.template_name"
                placeholder="e.g., Standard BCP Assessment Template"
                required
              />
            </div>
            <div class="space-y-2">
              <label class="label">Description</label>
              <textarea 
                class="textarea" 
                v-model="newTemplateForm.template_description"
                rows="3"
                placeholder="Describe the purpose of this template"
              ></textarea>
            </div>
            <div class="grid grid-cols-2 gap-4">
              <div class="space-y-2">
                <label class="label">Template Type</label>
                <select class="select" v-model="newTemplateForm.template_type">
                  <option value="STATIC">Static</option>
                  <option value="DYNAMIC">Dynamic</option>
                  <option value="ASSESSMENT">Assessment</option>
                  <option value="EVALUATION">Evaluation</option>
                  <option value="TEST">Test</option>
                </select>
              </div>
              <div class="space-y-2">
                <label class="label">Version</label>
                <input 
                  class="input" 
                  v-model="newTemplateForm.template_version"
                  placeholder="1.0"
                />
              </div>
            </div>
            <div class="space-y-2">
              <label class="label">Status</label>
              <select class="select" v-model="newTemplateForm.status">
                <option value="DRAFT">Draft</option>
                <option value="ACTIVE">Active</option>
                <option value="IN_REVIEW">In Review</option>
                <option value="APPROVED">Approved</option>
              </select>
            </div>
            <div class="flex gap-4 pt-4">
              <button type="button" @click="closeCreateTemplateModal" class="btn btn--outline">
                Cancel
              </button>
              <button type="submit" class="btn btn--primary" :disabled="isCreatingTemplate">
                {{ isCreatingTemplate ? 'Creating...' : 'Create Template' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Save as Template Modal -->
    <div v-if="showSaveAsTemplateModal" class="modal-overlay" @click.self="closeSaveAsTemplateModal">
      <div class="modal-content max-w-2xl">
        <div class="modal-header">
          <h3 class="modal-title">Save as Template</h3>
          <button class="modal-close" @click="closeSaveAsTemplateModal">
            <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <form @submit.prevent="confirmSaveAsTemplate" class="space-y-4">
            <div class="space-y-2">
              <label class="label">Template Name <span class="text-destructive">*</span></label>
              <input 
                class="input" 
                v-model="saveAsTemplateForm.template_name"
                placeholder="e.g., Standard BCP Assessment Template"
                required
              />
            </div>
            <div class="space-y-2">
              <label class="label">Description</label>
              <textarea 
                class="textarea" 
                v-model="saveAsTemplateForm.template_description"
                rows="3"
                placeholder="Describe the purpose of this template"
              ></textarea>
            </div>
            <div class="grid grid-cols-2 gap-4">
              <div class="space-y-2">
                <label class="label">Template Type</label>
                <select class="select" v-model="saveAsTemplateForm.template_type">
                  <option value="STATIC">Static</option>
                  <option value="DYNAMIC">Dynamic</option>
                  <option value="ASSESSMENT">Assessment</option>
                  <option value="EVALUATION">Evaluation</option>
                  <option value="TEST">Test</option>
                </select>
              </div>
              <div class="space-y-2">
                <label class="label">Version</label>
                <input 
                  class="input" 
                  v-model="saveAsTemplateForm.template_version"
                  placeholder="1.0"
                />
              </div>
            </div>
            <div class="space-y-2">
              <label class="label">Status</label>
              <select class="select" v-model="saveAsTemplateForm.status">
                <option value="DRAFT">Draft</option>
                <option value="ACTIVE">Active</option>
                <option value="IN_REVIEW">In Review</option>
                <option value="APPROVED">Approved</option>
              </select>
            </div>
            <div class="flex gap-4 pt-4">
              <button type="button" @click="closeSaveAsTemplateModal" class="btn btn--outline">
                Cancel
              </button>
              <button type="submit" class="btn btn--primary" :disabled="isSavingAsTemplate">
                {{ isSavingAsTemplate ? 'Saving...' : 'Save Template' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Add Plan Type Modal -->
    <div v-if="showAddPlanTypeModal" class="modal-overlay" @click="closeAddPlanTypeModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3 class="modal-title">Add New Plan Type</h3>
          <button class="modal-close" @click="closeAddPlanTypeModal">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label for="new-plan-type" class="form-label">
              Plan Type Name <span class="required-asterisk">*</span>
            </label>
            <input
              id="new-plan-type"
              type="text"
              class="form-input"
              v-model="newPlanTypeValue"
              placeholder="e.g., CRP, ERP, etc."
              @keyup.enter="saveNewPlanType"
              ref="newPlanTypeInput"
            />
            <p class="form-hint">Enter a unique plan type name (e.g., Crisis Recovery Plan, Emergency Response Plan)</p>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn--outline" @click="closeAddPlanTypeModal">Cancel</button>
          <button 
            class="btn btn--primary" 
            @click="saveNewPlanType"
            :disabled="!newPlanTypeValue.trim() || isSavingPlanType"
          >
            <span v-if="isSavingPlanType">Saving...</span>
            <span v-else>Save Plan Type</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import './QuestionnaireWorkflow.css'
import { ref, computed, onMounted, reactive, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import http from '../../api/http'
import api from '../../services/api_bcp.js'
import { useNotifications } from '@/composables/useNotifications'
import { PopupService } from '@/popup/popupService'
import loggingService from '@/services/loggingService'
import { useStore } from 'vuex'

const route = useRoute()
const router = useRouter()

// Step management
const { showSuccess, showError, showWarning, showInfo } = useNotifications()

// Vuex store
const store = useStore()

const currentStep = ref(1)

// Plan selection data
const availablePlans = ref<any[]>([])
const selectedPlanId = ref<string>("")
const isPlanDropdownOpen = ref(false)
const isLoadingPlans = ref(false)

// Plan types data
const planTypes = ref<any[]>([])
const isPlanTypeDropdownOpen = ref(false)
const showAddPlanTypeModal = ref(false)
const newPlanTypeValue = ref('')
const isSavingPlanType = ref(false)
const newPlanTypeInput = ref(null)

// Questionnaire data
const questionnaire = ref({
  questionnaire_id: null, // Store ID for updates
  title: '',
  planType: '',
  description: ''
})

const questionnaireData = reactive({
  questionnaire: {
    title: '',
    planType: 'BCP',
    description: '',
    plan_id: 0,
    questionnaire_id: null
  },
  questions: []
})

const newQuestion = ref({
  text: '',
  type: '',
  required: false,
  choiceOptions: ['Option 1', 'Option 2'],
  allowDocumentUpload: false,
  helpText: undefined,
  questionCategory: undefined,
  metricName: undefined,
  termId: undefined
})

const mockQuestions = ref([])
const editingQuestionIndex = ref<number | null>(null)

// Assignment form data
const assignmentForm = ref({
  workflow_name: '',
  plan_type: '',
  assigner_id: '',
  assigner_name: '',
  assignee_id: '',
  assignee_name: '',
  object_type: 'NEW QUESTIONNAIRE',
  object_id: '',
  due_date: ''
})

// Users data
const users = ref([])
const isLoadingUsers = ref(false)
const isSubmitting = ref(false)
const noApprovalNeeded = ref(false)

// Template management data
const availableTemplates = ref<any[]>([])
const isLoadingTemplates = ref(false)
const showTemplateSelector = ref(false)
const showCreateTemplateModal = ref(false)
const showSaveAsTemplateModal = ref(false)
const isCreatingTemplate = ref(false)
const isSavingAsTemplate = ref(false)

const newTemplateForm = ref({
  template_name: '',
  template_description: '',
  template_type: 'ASSESSMENT',
  template_version: '1.0',
  status: 'DRAFT'
})

const saveAsTemplateForm = ref({
  template_name: '',
  template_description: '',
  template_type: 'ASSESSMENT',
  template_version: '1.0',
  status: 'DRAFT'
})

// Computed properties
const isAllSelected = computed(() => {
  return availablePlans.value.length > 0 && availablePlans.value.every(plan => 
    selectedPlanId.value === plan.plan_id.toString()
  )
})

const canProceedToStep2 = computed(() => {
  return selectedPlanId.value && 
         questionnaire.value.title && 
         questionnaire.value.description && 
         mockQuestions.value.length > 0
})

const canSaveAsTemplate = computed(() => {
  return mockQuestions.value.length > 0 && 
         questionnaire.value.title && 
         questionnaire.value.description
})

// Plan type fetching - extract from plans table
const fetchPlanTypes = async () => {
  try {
    console.log('Fetching plan types from plans table')
    const response = await api.plans.list()
    console.log('Plans API Response:', response)
    
    const plans = (response as any).plans || (response as any).data?.plans || []
    
    // Update plan types from the fetched plans
    updatePlanTypesFromPlans(plans)
    
    // Set default to first plan type if available
    if (planTypes.value.length > 0 && !questionnaire.value.planType) {
      questionnaire.value.planType = planTypes.value[0].value
    }
  } catch (error) {
    console.error('Error fetching plan types:', error)
    console.error('Error details:', error.message)
    planTypes.value = []
  }
}

// Plan selection methods
const fetchPlans = async () => {
  isLoadingPlans.value = true
  try {
    console.log('Fetching plans from API endpoint: http://localhost:8000/api/bcpdrp/plans/')
    const response = await api.plans.list()
    
    console.log('API response data:', response)
    
    const plans = (response as any).plans || (response as any).data?.plans
    console.log('Plans found:', plans)
    
    if (plans && Array.isArray(plans)) {
      availablePlans.value = plans
      console.log('Successfully fetched plans:', plans.length, 'plans')
      
      // Update plan types from the fetched plans
      await updatePlanTypesFromPlans(plans)
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

// Helper function to update plan types from plans
const updatePlanTypesFromPlans = (plans: any[]) => {
  // Extract unique plan types from plans table
  const uniquePlanTypes = [...new Set(plans.map((plan: any) => plan.plan_type).filter(Boolean))]
  
  // If questionnaire already has a plan type, ensure it's included
  if (questionnaire.value.planType && !uniquePlanTypes.includes(questionnaire.value.planType)) {
    uniquePlanTypes.push(questionnaire.value.planType)
  }
  
  // Transform to match the expected format
  planTypes.value = uniquePlanTypes.map((pt: string) => ({
    id: pt,
    value: pt
  })).sort((a, b) => a.value.localeCompare(b.value))
  
  console.log('Plan types updated from plans:', planTypes.value)
}

const togglePlanDropdown = () => {
  isPlanDropdownOpen.value = !isPlanDropdownOpen.value
}

const closePlanDropdown = () => {
  setTimeout(() => {
    isPlanDropdownOpen.value = false
  }, 150)
}

const selectPlan = (plan: any) => {
  selectedPlanId.value = plan.plan_id.toString()
  questionnaire.value.planType = plan.plan_type
  isPlanDropdownOpen.value = false
}

const toggleSelectAll = () => {
  if (isAllSelected.value) {
    selectedPlanId.value = ""
  } else {
    if (availablePlans.value.length > 0) {
      selectPlan(availablePlans.value[0])
    }
  }
}

const getSelectedPlanDisplay = () => {
  const plan = availablePlans.value.find(p => p.plan_id.toString() === selectedPlanId.value)
  if (plan) {
    return `[${plan.plan_id}] ${plan.plan_name} (${plan.plan_type})`
  }
  return ""
}

const getSelectedPlanType = () => {
  const plan = availablePlans.value.find(p => p.plan_id.toString() === selectedPlanId.value)
  return plan ? plan.plan_type : ""
}

const togglePlanTypeDropdown = () => {
  if (!selectedPlanId.value) {
    isPlanTypeDropdownOpen.value = !isPlanTypeDropdownOpen.value
  }
}

const closePlanTypeDropdown = () => {
  setTimeout(() => {
    isPlanTypeDropdownOpen.value = false
  }, 200)
}

const selectPlanTypeValue = (value: string) => {
  questionnaire.value.planType = value
  isPlanTypeDropdownOpen.value = false
}

const openAddPlanTypeModal = () => {
  showAddPlanTypeModal.value = true
  newPlanTypeValue.value = ''
  isPlanTypeDropdownOpen.value = false
  setTimeout(() => {
    if (newPlanTypeInput.value) {
      (newPlanTypeInput.value as HTMLInputElement).focus()
    }
  }, 100)
}

const closeAddPlanTypeModal = () => {
  showAddPlanTypeModal.value = false
  newPlanTypeValue.value = ''
}

const saveNewPlanType = async () => {
  const trimmedValue = newPlanTypeValue.value.trim()
  
  if (!trimmedValue) {
    PopupService.warning('Please enter a plan type name', 'Validation Error')
    return
  }

  // Check if plan type already exists
  if (planTypes.value.some(pt => pt.value.toUpperCase() === trimmedValue.toUpperCase())) {
    PopupService.warning(`Plan type "${trimmedValue}" already exists`, 'Duplicate Plan Type')
    return
  }

  isSavingPlanType.value = true
  try {
    const response = await api.planTypes.create({ value: trimmedValue })
    console.log('Plan type created:', response)
    
    // Refresh plan types list
    await fetchPlanTypes()
    
    // Select the newly created plan type
    questionnaire.value.planType = trimmedValue
    
    // Close modal
    closeAddPlanTypeModal()
    
    PopupService.success(`Plan type "${trimmedValue}" has been added successfully`, 'Plan Type Added')
  } catch (error: any) {
    console.error('Error creating plan type:', error)
    PopupService.error(
      error.response?.data?.message || `Failed to add plan type "${trimmedValue}"`,
      'Error'
    )
  } finally {
    isSavingPlanType.value = false
  }
}

const getCriticalityBadgeClass = (criticality: string) => {
  if (!criticality) return "badge--secondary"
  switch (criticality) {
    case "CRITICAL": return "badge--destructive"
    case "HIGH": return "badge--warning"
    case "MEDIUM": return "badge--secondary"
    case "LOW": return "badge--outline"
    default: return "badge--secondary"
  }
}

const getStatusBadgeClass = (status: string) => {
  if (!status) return "badge--secondary"
  switch (status) {
    case "SUBMITTED": return "badge--default"
    case "OCR_COMPLETED": return "badge--success"
    case "ASSIGNED_FOR_EVALUATION": return "badge--warning"
    case "APPROVED": return "badge--success"
    case "REJECTED": return "badge--destructive"
    case "REVISION_REQUESTED": return "badge--warning"
    case "DRAFT": return "badge--neutral"
    case "ACTIVE": return "badge--success"
    case "IN_REVIEW": return "badge--warning"
    case "ARCHIVED": return "badge--secondary"
    case "DEPRECATED": return "badge--destructive"
    default: return "badge--secondary"
  }
}

const formatDate = (dateString: string) => {
  if (!dateString) return 'N/A'
  try {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    })
  } catch (error) {
    return dateString
  }
}

// Question management methods
const addChoiceOption = () => {
  newQuestion.value.choiceOptions.push(`Option ${newQuestion.value.choiceOptions.length + 1}`)
}

const removeChoiceOption = (index) => {
  if (newQuestion.value.choiceOptions.length > 2) {
    newQuestion.value.choiceOptions.splice(index, 1)
  }
}

const addQuestion = () => {
  if (newQuestion.value.text && newQuestion.value.type) {
    const question: any = {
      id: editingQuestionIndex.value !== null 
        ? mockQuestions.value[editingQuestionIndex.value].id 
        : Date.now(),
      text: newQuestion.value.text,
      type: newQuestion.value.type,
      required: newQuestion.value.required,
      weight: editingQuestionIndex.value !== null 
        ? mockQuestions.value[editingQuestionIndex.value].weight 
        : 1.0,
      choiceOptions: (newQuestion.value.type === 'MULTIPLE_CHOICE' || newQuestion.value.type === 'CHECKBOX') ? [...newQuestion.value.choiceOptions] : [],
      allowDocumentUpload: newQuestion.value.allowDocumentUpload
    }
    
    // Add optional fields if they exist
    if (newQuestion.value.helpText) question.helpText = newQuestion.value.helpText
    if (newQuestion.value.questionCategory) question.questionCategory = newQuestion.value.questionCategory
    if (newQuestion.value.metricName) question.metricName = newQuestion.value.metricName
    if (newQuestion.value.termId) question.termId = newQuestion.value.termId
    
    if (editingQuestionIndex.value !== null) {
      // Update existing question
      mockQuestions.value[editingQuestionIndex.value] = question
      PopupService.success('Question updated successfully!', 'Question Updated')
    } else {
      // Add new question
      mockQuestions.value.push(question)
      PopupService.success('Question added successfully!', 'Question Added')
    }
    
    // Reset form
    cancelEditQuestion()
  } else {
    PopupService.warning('Please fill in question text and select a type', 'Validation Error')
  }
}

const editQuestion = (index: number) => {
  const question = mockQuestions.value[index]
  if (!question) return
  
  // Load question data into form - handle all fields including optional ones
  newQuestion.value = {
    text: question.text || '',
    type: question.type || '',
    required: question.required !== undefined ? question.required : false,
    choiceOptions: (question.choiceOptions && question.choiceOptions.length > 0) 
      ? [...question.choiceOptions] 
      : (question.type === 'MULTIPLE_CHOICE' || question.type === 'CHECKBOX' ? ['Option 1', 'Option 2'] : []),
    allowDocumentUpload: question.allowDocumentUpload !== undefined ? question.allowDocumentUpload : false,
    helpText: question.helpText || undefined,
    questionCategory: question.questionCategory || undefined,
    metricName: question.metricName || undefined,
    termId: question.termId || undefined
  }
  
  editingQuestionIndex.value = index
  
  // Scroll to form
  const formElement = document.querySelector('.mt-6.p-4.bg-muted\\/30')
  if (formElement) {
    formElement.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

const deleteQuestion = (index: number) => {
  PopupService.confirm(
    'Are you sure you want to delete this question?',
    'Delete Question',
    () => {
      mockQuestions.value.splice(index, 1)
      PopupService.success('Question deleted successfully!', 'Question Deleted')
      
      // Cancel editing if we're editing this question
      if (editingQuestionIndex.value === index) {
        cancelEditQuestion()
      } else if (editingQuestionIndex.value !== null && editingQuestionIndex.value > index) {
        // Adjust editing index if a question before it was deleted
        editingQuestionIndex.value = editingQuestionIndex.value - 1
      }
    },
    () => {
      // User cancelled
    }
  )
}

const cancelEditQuestion = () => {
  editingQuestionIndex.value = null
  newQuestion.value = {
    text: '',
    type: '',
    required: false,
    choiceOptions: ['Option 1', 'Option 2'],
    allowDocumentUpload: false,
    helpText: undefined,
    questionCategory: undefined,
    metricName: undefined,
    termId: undefined
  }
}

const saveQuestionnaire = async () => {
  try {
    // Prepare the data to send to the API
    const questionnaireData = {
      questionnaire: {
        title: questionnaire.value.title,
        description: questionnaire.value.description,
        planType: questionnaire.value.planType,
        plan_id: parseInt(selectedPlanId.value)
      },
      questions: mockQuestions.value.map(q => ({
        text: q.text,
        type: q.type,
        required: q.required,
        weight: q.weight,
        choice_options: q.choiceOptions || [],
        allow_document_upload: q.allowDocumentUpload || false,
        help_text: q.helpText || undefined,
        question_category: q.questionCategory || undefined,
        metric_name: q.metricName || undefined,
        term_id: q.termId || undefined
      }))
    }

    // Include questionnaire_id if updating existing questionnaire
    if (questionnaire.value.questionnaire_id) {
      (questionnaireData.questionnaire as any).questionnaire_id = questionnaire.value.questionnaire_id
    }

    // Make API call to save questionnaire using the new workflow API
    const response = await api.questionnaireWorkflow.createQuestionnaire(questionnaireData)

    console.log('Questionnaire saved successfully:', response.data)
    
    // Show appropriate message based on whether it was an update or creation
    const message = response.data.is_update ? 'Questionnaire updated successfully!' : 'Questionnaire saved successfully!'
    PopupService.success(message, response.data.is_update ? 'Questionnaire Updated' : 'Questionnaire Saved')
    
    // Store the questionnaire ID for future updates and the assignment form
    if (response.data && response.data.questionnaire_id) {
      questionnaire.value.questionnaire_id = response.data.questionnaire_id
      assignmentForm.value.object_id = response.data.questionnaire_id.toString()
    }
  } catch (error) {
    console.error('Error saving questionnaire:', error)
    PopupService.error('Error saving questionnaire: ' + (error.message || 'Unknown error'), 'Save Failed')
  }
}

const proceedToStep2 = async () => {
  // Save the questionnaire first
  await saveQuestionnaire()
  
  // Ensure plan types are loaded before proceeding
  if (planTypes.value.length === 0) {
    await fetchPlanTypes()
  }
  
  // Auto-fill assignment form with questionnaire data
  assignmentForm.value.plan_type = questionnaire.value.planType || ''
  assignmentForm.value.workflow_name = `${questionnaire.value.title} - Testing Assignment`
  
  // Ensure object_id is set if questionnaire was saved
  if (questionnaire.value.questionnaire_id) {
    assignmentForm.value.object_id = questionnaire.value.questionnaire_id.toString()
  }
  
  console.log('Proceeding to Step 2 with plan type:', questionnaire.value.planType)
  console.log('Available plan types:', planTypes.value)
  console.log('Assignment form plan_type:', assignmentForm.value.plan_type)
  
  // Move to step 2
  currentStep.value = 2
}

const handleStep2Click = () => {
  if (!canProceedToStep2.value) {
    PopupService.warning(
      'Please complete questionnaire creation in Step 1 before accessing Step 2.',
      'Step 2 Disabled'
    )
    return
  }
  proceedToStep2()
}

const goToStep = (step: number) => {
  // Prevent navigation to Step 2 if conditions aren't met
  if (step === 2 && !canProceedToStep2.value) {
    PopupService.warning(
      'Please complete questionnaire creation in Step 1 before accessing Step 2.',
      'Step 2 Disabled'
    )
    return
  }
  
  if (step === 2) {
    proceedToStep2()
  } else {
    currentStep.value = step
  }
}

// Watch for plan type changes and update assignment form when on Step 2
watch(() => questionnaire.value.planType, (newPlanType) => {
  if (newPlanType && currentStep.value === 2) {
    assignmentForm.value.plan_type = newPlanType
    console.log('Plan type updated in assignment form:', newPlanType)
  }
})

// Assignment form methods
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
    // Use display_name if available (shown in dropdown), otherwise fall back to username
    assignmentForm.value.assigner_name = selectedUser.display_name || selectedUser.username || ''
  } else {
    assignmentForm.value.assigner_name = ''
  }
}

const onAssigneeChange = () => {
  const selectedUser = users.value.find(user => user.user_id == assignmentForm.value.assignee_id)
  if (selectedUser) {
    // Use display_name if available (shown in dropdown), otherwise fall back to username
    assignmentForm.value.assignee_name = selectedUser.display_name || selectedUser.username || ''
  } else {
    assignmentForm.value.assignee_name = ''
  }
}

const handleNoApprovalChange = () => {
  if (noApprovalNeeded.value) {
    let userId = null
    let userName = null
    let currentUser = null
    
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
      try {
        currentUser = store.getters['auth/currentUser']
        if (currentUser) {
          userId = currentUser.UserId || currentUser.user_id || currentUser.userId || currentUser.userid || currentUser.id
          userName = currentUser.UserName || currentUser.username || `${currentUser.first_name || ''} ${currentUser.last_name || ''}`.trim() || currentUser.email
          if (userId) {
            console.log('✅ Extracted user_id from Vuex store:', userId)
          }
        }
      } catch (vuexError) {
        console.log('Could not access Vuex store:', vuexError.message)
      }
    } else {
      // If we got userId from JWT, still try to get currentUser from store for userName
      try {
        currentUser = store.getters['auth/currentUser']
        if (currentUser) {
          userName = currentUser.UserName || currentUser.username || `${currentUser.first_name || ''} ${currentUser.last_name || ''}`.trim() || currentUser.email
        }
      } catch (vuexError) {
        // Ignore error
      }
    }
    
    // Method 3: Try to parse current_user from localStorage (check UserId with capital letters)
    if (!userId || !userName) {
      try {
        const userStr = localStorage.getItem('current_user')
        if (userStr) {
          const parsedUser = JSON.parse(userStr)
          // Check for UserId (capital U, capital I) first, then lowercase variants
          if (!userId) {
            userId = parsedUser.UserId || parsedUser.user_id || parsedUser.userId || parsedUser.userid || parsedUser.id
            if (userId) {
              console.log('✅ Extracted user_id from localStorage current_user:', userId)
            }
          }
          // Try to get username, but it might be encrypted
          if (!userName) {
            userName = parsedUser.UserName || parsedUser.username || `${parsedUser.first_name || ''} ${parsedUser.last_name || ''}`.trim() || parsedUser.email
          }
          if (!currentUser) {
            currentUser = parsedUser
          }
        }
      } catch (error) {
        console.warn('⚠️ Error parsing user from localStorage (may be encrypted):', error)
      }
    }
    
    // Method 4: Try to get username from users list (if already loaded and userId found)
    if (userId && !userName && users.value && users.value.length > 0) {
      const userFromList = users.value.find(user => user.user_id == userId || user.userid == userId)
      if (userFromList) {
        userName = userFromList.display_name || userFromList.username || ''
        if (userName) {
          console.log('✅ Found username from users list:', userName)
        }
      }
    }
    
    // Method 5: If username looks encrypted (starts with gAAAAA), try to get from users list
    if (userName && userName.startsWith('gAAAAA') && users.value && users.value.length > 0 && userId) {
      const userFromList = users.value.find(user => user.user_id == userId || user.userid == userId)
      if (userFromList) {
        userName = userFromList.display_name || userFromList.username || ''
        console.log('✅ Decrypted username from users list:', userName)
      }
    }
    
    // Method 6: If still no userName, construct from currentUser object
    if (!userName && currentUser) {
      userName = currentUser.UserName || currentUser.username || 
                 `${currentUser.first_name || ''} ${currentUser.last_name || ''}`.trim() || 
                 currentUser.email || 
                 ''
    }
    
    if (userId) {
      // Auto-fill assigner
      assignmentForm.value.assigner_id = userId.toString()
      assignmentForm.value.assigner_name = userName || `User ${userId}`
      
      // Set assignee to same as assigner
      assignmentForm.value.assignee_id = userId.toString()
      assignmentForm.value.assignee_name = userName || `User ${userId}`
      
      console.log('✅ Successfully set assigner and assignee from user:', { userId, userName })
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

const createAssignment = async () => {
  isSubmitting.value = true
  
  try {
    console.log('Creating assignment:', assignmentForm.value)
    
    // Validate all required fields (matching backend requirements)
    const missingFields = []
    
    if (!assignmentForm.value.workflow_name) missingFields.push('Workflow Name')
    if (!assignmentForm.value.plan_type) missingFields.push('Plan Type')
    if (!assignmentForm.value.assigner_id) missingFields.push('Assigner')
    if (!assignmentForm.value.assigner_name) missingFields.push('Assigner Name')
    if (!assignmentForm.value.object_type) missingFields.push('Object Type')
    if (!assignmentForm.value.object_id) missingFields.push('Object ID')
    if (!assignmentForm.value.due_date) missingFields.push('Due Date')
    
    // Only require assignee fields if no_approval_needed is false
    if (!noApprovalNeeded.value) {
      if (!assignmentForm.value.assignee_id) missingFields.push('Assignee')
      if (!assignmentForm.value.assignee_name) missingFields.push('Assignee Name')
    }
    
    if (missingFields.length > 0) {
      PopupService.warning(`Please fill in all required fields: ${missingFields.join(', ')}`, 'Required Fields Missing')
      isSubmitting.value = false
      return
    }
    
    // Add no_approval_needed flag to assignment data
    const assignmentData = {
      ...assignmentForm.value,
      no_approval_needed: noApprovalNeeded.value
    }
    
    // Ensure object_id is a string or number (not empty string)
    if (assignmentData.object_id === '' || assignmentData.object_id === null || assignmentData.object_id === undefined) {
      PopupService.warning('Object ID is required. Please ensure the questionnaire was saved successfully.', 'Object ID Missing')
      isSubmitting.value = false
      return
    }
    
    // Call the API to create the approval assignment using the new workflow API
    const response = await api.questionnaireWorkflow.assignQuestionnaire(assignmentData)
    
    console.log('Assignment created successfully:', response)
    
    PopupService.success(`Assignment created successfully! Approval ID: ${(response as any).approval_id || (response as any).data?.approval_id || 'N/A'}`, 'Assignment Created')
    
    // Reset the form and go back to step 1
    resetWorkflow()
    
  } catch (error) {
    console.error('Error creating assignment:', error)
    console.error('Error response:', error.response?.data)
    
    let errorMessage = 'Error creating assignment. Please try again.'
    
    // Try to extract detailed error message from backend
    if (error.response?.data) {
      const responseData = error.response.data
      // Check for different possible error message formats
      if (responseData.message) {
        errorMessage = responseData.message
      } else if (responseData.error) {
        errorMessage = responseData.error
      } else if (responseData.detail) {
        errorMessage = responseData.detail
      } else if (typeof responseData === 'string') {
        errorMessage = responseData
      } else if (responseData.non_field_errors && Array.isArray(responseData.non_field_errors)) {
        errorMessage = responseData.non_field_errors.join(', ')
      } else {
        // Try to extract first error message from any field
        const firstError = Object.values(responseData).find(v => typeof v === 'string' || Array.isArray(v))
        if (firstError) {
          errorMessage = Array.isArray(firstError) ? firstError[0] : firstError
        }
      }
    } else if (error.message) {
      errorMessage = error.message
    }
    
    PopupService.error(errorMessage, 'Assignment Failed')
  } finally {
    isSubmitting.value = false
  }
}

const resetAssignmentForm = () => {
  noApprovalNeeded.value = false
  assignmentForm.value = {
    workflow_name: '',
    plan_type: '',
    assigner_id: '',
    assigner_name: '',
    assignee_id: '',
    assignee_name: '',
    object_type: 'NEW QUESTIONNAIRE',
    object_id: '',
    due_date: ''
  }
}

const goBackToStep1 = () => {
  currentStep.value = 1
}

const resetWorkflow = () => {
  currentStep.value = 1
  selectedPlanId.value = ""
  questionnaire.value = {
    questionnaire_id: null, // Reset ID when starting new workflow
    title: '',
    planType: 'BCP',
    description: ''
  }
  mockQuestions.value = []
  cancelEditQuestion() // Cancel any active editing
  resetAssignmentForm()
}

// Template management functions
const fetchTemplates = async (moduleType?: string) => {
  isLoadingTemplates.value = true
  try {
    const params: any = { is_active: 'true' }
    if (moduleType) {
      params.module_type = moduleType
    } else {
      // Always fetch templates with module_type as 'PLANS'
      params.module_type = 'PLANS'
    }
    
    const response = await api.questionnaireTemplates.list(params)
    const templates = (response as any).templates || (response as any).data?.templates || []
    availableTemplates.value = templates
    console.log('Fetched templates:', templates.length)
  } catch (error) {
    console.error('Error fetching templates:', error)
    PopupService.error(`Failed to load templates: ${error.message || 'Unknown error'}`, 'Loading Failed')
    availableTemplates.value = []
  } finally {
    isLoadingTemplates.value = false
  }
}

const openTemplateSelector = async () => {
  showTemplateSelector.value = true
  await fetchTemplates()
}

const closeTemplateSelector = () => {
  showTemplateSelector.value = false
}

const selectTemplate = async (template: any) => {
  try {
    // Cancel any active editing before loading template
    cancelEditQuestion()
    
    // Fetch full template data including questions
    const response = await api.questionnaireTemplates.get(template.template_id)
    const templateData = (response as any).data || response
    
    // Load template data into questionnaire form
    // Fetch title and description from questionnaire template table
    if (templateData.template_name) {
      questionnaire.value.title = templateData.template_name
    }
    if (templateData.template_description) {
      questionnaire.value.description = templateData.template_description
    }
    
    // Plan type should come from selected plan, not from template
    // Only set plan type from template if no plan is selected
    if (!selectedPlanId.value && templateData.module_type) {
      questionnaire.value.planType = templateData.module_type
    }
    // If a plan is selected, keep the plan type from the selected plan
    else if (selectedPlanId.value) {
      const selectedPlan = availablePlans.value.find(p => p.plan_id.toString() === selectedPlanId.value)
      if (selectedPlan && selectedPlan.plan_type) {
        questionnaire.value.planType = selectedPlan.plan_type
      }
    }
    
    // Convert template questions to questionnaire format
    if (templateData.template_questions_json && Array.isArray(templateData.template_questions_json)) {
      mockQuestions.value = templateData.template_questions_json.map((q: any, index: number) => {
        // Map answer_type from template to workflow format
        // Handle all answer types from template: TEXT, TEXTAREA, NUMBER, BOOLEAN, MULTIPLE_CHOICE, CHECKBOX, RATING, SCALE, DATE, FILE_UPLOAD, YES_NO
        let questionType = q.answer_type || q.type || 'TEXT'
        
        // Ensure the type is one of the supported types (keep as-is, template types match workflow types)
        // BOOLEAN and YES_NO are both supported, but we can keep BOOLEAN as BOOLEAN or convert to YES_NO
        // For consistency, let's keep BOOLEAN as BOOLEAN since it's in the dropdown now
        
        return {
          id: q.question_id || Date.now() + index,
          text: q.question_text || q.text || '', // Map question_text -> text
          type: questionType, // answer_type -> type (already mapped)
          required: q.is_required !== undefined ? q.is_required : (q.required !== undefined ? q.required : false), // is_required -> required
          weight: q.weightage !== undefined && q.weightage !== null ? q.weightage : (q.weight !== undefined ? q.weight : 1.0), // weightage -> weight
          choiceOptions: (q.options && Array.isArray(q.options)) ? [...q.options] : (q.choiceOptions && Array.isArray(q.choiceOptions) ? [...q.choiceOptions] : []), // options -> choiceOptions
          allowDocumentUpload: q.allow_document_upload !== undefined ? q.allow_document_upload : (q.allowDocumentUpload !== undefined ? q.allowDocumentUpload : false), // allow_document_upload -> allowDocumentUpload
          helpText: q.help_text || q.helpText || undefined, // help_text -> helpText (optional field)
          questionCategory: q.question_category || q.questionCategory || undefined, // question_category -> questionCategory (optional, for VENDOR)
          metricName: q.metric_name || q.metricName || undefined, // metric_name -> metricName (optional, for SLA)
          termId: q.term_id || q.termId || undefined // term_id -> termId (optional, for CONTRACT)
        }
      })
      
      PopupService.success(`Template loaded successfully! ${mockQuestions.value.length} questions loaded.`, 'Template Loaded')
    } else {
      mockQuestions.value = []
      PopupService.warning('Template loaded but contains no questions.', 'No Questions')
    }
    
    closeTemplateSelector()
  } catch (error) {
    console.error('Error loading template:', error)
    PopupService.error(`Failed to load template: ${error.message || 'Unknown error'}`, 'Load Failed')
  }
}

const navigateToTemplateScreen = () => {
  // Navigate to questionnaire templates screen
  router.push('/questionnaire-templates')
}

const openCreateTemplateModal = () => {
  // Pre-fill form with current plan type if available
  showCreateTemplateModal.value = true
  newTemplateForm.value = {
    template_name: '',
    template_description: '',
    template_type: 'ASSESSMENT',
    template_version: '1.0',
    status: 'DRAFT'
  }
}

const closeCreateTemplateModal = () => {
  showCreateTemplateModal.value = false
  newTemplateForm.value = {
    template_name: '',
    template_description: '',
    template_type: 'ASSESSMENT',
    template_version: '1.0',
    status: 'DRAFT'
  }
}

const createTemplate = async () => {
  if (!newTemplateForm.value.template_name.trim()) {
    PopupService.warning('Template name is required', 'Validation Error')
    return
  }
  
  if (mockQuestions.value.length === 0) {
    PopupService.warning('Please add questions to the questionnaire before creating a template.', 'No Questions')
    return
  }
  
  isCreatingTemplate.value = true
  try {
    // Convert current questions to template format - map all fields correctly
    const templateQuestions = mockQuestions.value.map((q: any, index: number) => ({
      question_id: index + 1,
      questionnaire_id: null,
      display_order: index + 1,
      question_text: q.text || '', // text -> question_text
      question_category: q.questionCategory || undefined, // questionCategory -> question_category
      answer_type: q.type || 'TEXT', // type -> answer_type (keep as-is, both YES_NO and BOOLEAN are valid)
      is_required: q.required !== undefined ? q.required : false, // required -> is_required
      weightage: q.weight !== undefined && q.weight !== null ? q.weight : 1.0, // weight -> weightage
      metric_name: q.metricName || undefined, // metricName -> metric_name
      term_id: q.termId || null, // termId -> term_id
      allow_document_upload: q.allowDocumentUpload !== undefined ? q.allowDocumentUpload : false, // allowDocumentUpload -> allow_document_upload
      options: q.choiceOptions && Array.isArray(q.choiceOptions) ? [...q.choiceOptions] : [], // choiceOptions -> options
      help_text: q.helpText || undefined, // helpText -> help_text
      created_at: new Date().toISOString()
    }))
    
    const templateData = {
      template_name: newTemplateForm.value.template_name,
      template_description: newTemplateForm.value.template_description || null,
      template_version: newTemplateForm.value.template_version || '1.0',
      template_type: newTemplateForm.value.template_type,
      module_type: 'PLANS',
      template_questions_json: templateQuestions,
      status: newTemplateForm.value.status,
      is_active: true,
      is_template: true
    }
    
    const response = await api.questionnaireTemplates.save(templateData)
    const templateId = (response as any).template_id || (response as any).data?.template_id
    
    PopupService.success(`Template created successfully! Template ID: ${templateId || 'N/A'}`, 'Template Created')
    closeCreateTemplateModal()
    
    // Refresh templates list if selector is open
    if (showTemplateSelector.value) {
      await fetchTemplates()
    }
  } catch (error) {
    console.error('Error creating template:', error)
    PopupService.error(`Failed to create template: ${error.message || 'Unknown error'}`, 'Creation Failed')
  } finally {
    isCreatingTemplate.value = false
  }
}

const saveAsTemplate = () => {
  if (!canSaveAsTemplate.value) {
    PopupService.warning('Please add questions and fill in questionnaire details before saving as template.', 'Incomplete Questionnaire')
    return
  }
  
  // Pre-fill form with current questionnaire data
  saveAsTemplateForm.value = {
    template_name: questionnaire.value.title || '',
    template_description: questionnaire.value.description || '',
    template_type: 'ASSESSMENT',
    template_version: '1.0',
    status: 'DRAFT'
  }
  
  showSaveAsTemplateModal.value = true
}

const closeSaveAsTemplateModal = () => {
  showSaveAsTemplateModal.value = false
  saveAsTemplateForm.value = {
    template_name: '',
    template_description: '',
    template_type: 'ASSESSMENT',
    template_version: '1.0',
    status: 'DRAFT'
  }
}

const confirmSaveAsTemplate = async () => {
  if (!saveAsTemplateForm.value.template_name.trim()) {
    PopupService.warning('Template name is required', 'Validation Error')
    return
  }
  
  isSavingAsTemplate.value = true
  try {
    // Verify we have questions to save
    if (!mockQuestions.value || mockQuestions.value.length === 0) {
      PopupService.warning('No questions to save. Please add questions to the questionnaire first.', 'No Questions')
      isSavingAsTemplate.value = false
      return
    }
    
    console.log('Saving template with questions:', mockQuestions.value.length, 'questions')
    console.log('Questions data:', mockQuestions.value)
    
    // Convert current questions to template format - map all fields correctly
    const templateQuestions = mockQuestions.value.map((q: any, index: number) => ({
      question_id: index + 1,
      questionnaire_id: null,
      display_order: index + 1,
      question_text: q.text || '', // text -> question_text
      question_category: q.questionCategory || undefined, // questionCategory -> question_category
      answer_type: q.type || 'TEXT', // type -> answer_type (keep as-is, both YES_NO and BOOLEAN are valid)
      is_required: q.required !== undefined ? q.required : false, // required -> is_required
      weightage: q.weight !== undefined && q.weight !== null ? q.weight : 1.0, // weight -> weightage
      metric_name: q.metricName || undefined, // metricName -> metric_name
      term_id: q.termId || null, // termId -> term_id
      allow_document_upload: q.allowDocumentUpload !== undefined ? q.allowDocumentUpload : false, // allowDocumentUpload -> allow_document_upload
      options: q.choiceOptions && Array.isArray(q.choiceOptions) ? [...q.choiceOptions] : [], // choiceOptions -> options
      help_text: q.helpText || undefined, // helpText -> help_text
      created_at: new Date().toISOString()
    }))
    
    const templateData = {
      template_name: saveAsTemplateForm.value.template_name,
      template_description: saveAsTemplateForm.value.template_description || null,
      template_version: saveAsTemplateForm.value.template_version || '1.0',
      template_type: saveAsTemplateForm.value.template_type,
      module_type: 'PLANS',
      template_questions_json: templateQuestions,
      status: saveAsTemplateForm.value.status,
      is_active: true,
      is_template: true
    }
    
    console.log('Saving template to database:', {
      template_name: templateData.template_name,
      module_type: templateData.module_type,
      question_count: templateQuestions.length,
      template_questions_json: templateQuestions
    })
    
    const response = await api.questionnaireTemplates.save(templateData)
    const templateId = (response as any).template_id || (response as any).data?.template_id
    
    PopupService.success(`Template saved successfully! Template ID: ${templateId || 'N/A'}`, 'Template Saved')
    closeSaveAsTemplateModal()
    
    // Refresh templates list if selector is open
    if (showTemplateSelector.value) {
      await fetchTemplates()
    }
  } catch (error) {
    console.error('Error saving template:', error)
    PopupService.error(`Failed to save template: ${error.message || 'Unknown error'}`, 'Save Failed')
  } finally {
    isSavingAsTemplate.value = false
  }
}

// Mock data functions
const getBCPMockData = () => {
  return {
    questionnaire: {
      title: 'Business Continuity Plan Assessment 2025',
      planType: 'BCP',
      description: 'Comprehensive questionnaire to evaluate business continuity plan effectiveness, covering critical business functions, recovery procedures, and stakeholder coordination.'
    },
    questions: [
      {
        id: 1,
        text: 'Are all critical business functions identified and documented in the BCP?',
        type: 'YES_NO',
        required: true,
        weight: 1.0,
        choiceOptions: [],
        allowDocumentUpload: true
      },
      {
        id: 2,
        text: 'What is the maximum acceptable downtime for core banking operations?',
        type: 'MULTIPLE_CHOICE',
        required: true,
        weight: 1.5,
        choiceOptions: ['Less than 1 hour', '1-4 hours', '4-8 hours', '8-24 hours', 'More than 24 hours'],
        allowDocumentUpload: false
      },
      {
        id: 3,
        text: 'Describe the communication plan for notifying stakeholders during a business disruption.',
        type: 'TEXT',
        required: true,
        weight: 1.2,
        choiceOptions: [],
        allowDocumentUpload: true
      },
      {
        id: 4,
        text: 'Are backup procedures documented for all critical systems?',
        type: 'YES_NO',
        required: true,
        weight: 1.0,
        choiceOptions: [],
        allowDocumentUpload: true
      },
      {
        id: 5,
        text: 'What is the frequency of BCP testing and validation?',
        type: 'MULTIPLE_CHOICE',
        required: true,
        weight: 1.3,
        choiceOptions: ['Monthly', 'Quarterly', 'Semi-annually', 'Annually', 'As needed'],
        allowDocumentUpload: false
      },
      {
        id: 6,
        text: 'Describe the alternative work arrangements for key personnel during a disruption.',
        type: 'TEXT',
        required: false,
        weight: 1.0,
        choiceOptions: [],
        allowDocumentUpload: true
      },
      {
        id: 7,
        text: 'Are regulatory requirements addressed in the BCP?',
        type: 'YES_NO',
        required: true,
        weight: 1.4,
        choiceOptions: [],
        allowDocumentUpload: true
      },
      {
        id: 8,
        text: 'What is the escalation procedure for declaring a business continuity event?',
        type: 'TEXT',
        required: true,
        weight: 1.5,
        choiceOptions: [],
        allowDocumentUpload: true
      }
    ]
  }
}

const getDRPMockData = () => {
  return {
    questionnaire: {
      title: 'Disaster Recovery Plan Technical Assessment 2025',
      planType: 'DRP',
      description: 'Technical evaluation questionnaire for disaster recovery plans, focusing on IT infrastructure recovery, data backup procedures, and system restoration capabilities.'
    },
    questions: [
      {
        id: 1,
        text: 'Are all critical IT systems and applications identified in the DRP?',
        type: 'YES_NO',
        required: true,
        weight: 1.0,
        choiceOptions: [],
        allowDocumentUpload: true
      },
      {
        id: 2,
        text: 'What is the Recovery Time Objective (RTO) for primary data center systems?',
        type: 'MULTIPLE_CHOICE',
        required: true,
        weight: 1.5,
        choiceOptions: ['Less than 1 hour', '1-4 hours', '4-8 hours', '8-24 hours', 'More than 24 hours'],
        allowDocumentUpload: false
      },
      {
        id: 3,
        text: 'Describe the data backup and replication strategy for critical databases.',
        type: 'TEXT',
        required: true,
        weight: 1.4,
        choiceOptions: [],
        allowDocumentUpload: true
      },
      {
        id: 4,
        text: 'Are failover procedures automated for critical systems?',
        type: 'YES_NO',
        required: true,
        weight: 1.2,
        choiceOptions: [],
        allowDocumentUpload: true
      },
      {
        id: 5,
        text: 'What is the frequency of disaster recovery testing?',
        type: 'MULTIPLE_CHOICE',
        required: true,
        weight: 1.3,
        choiceOptions: ['Monthly', 'Quarterly', 'Semi-annually', 'Annually', 'As needed'],
        allowDocumentUpload: false
      },
      {
        id: 6,
        text: 'Describe the network connectivity and bandwidth requirements for the recovery site.',
        type: 'TEXT',
        required: false,
        weight: 1.1,
        choiceOptions: [],
        allowDocumentUpload: true
      },
      {
        id: 7,
        text: 'Are security controls maintained at the same level during recovery operations?',
        type: 'YES_NO',
        required: true,
        weight: 1.4,
        choiceOptions: [],
        allowDocumentUpload: true
      },
      {
        id: 8,
        text: 'What is the procedure for validating data integrity after system recovery?',
        type: 'TEXT',
        required: true,
        weight: 1.5,
        choiceOptions: [],
        allowDocumentUpload: true
      },
      {
        id: 9,
        text: 'Are cloud-based recovery options considered and documented?',
        type: 'YES_NO',
        required: false,
        weight: 1.0,
        choiceOptions: [],
        allowDocumentUpload: true
      },
      {
        id: 10,
        text: 'Describe the incident response coordination between IT and business teams.',
        type: 'TEXT',
        required: true,
        weight: 1.3,
        choiceOptions: [],
        allowDocumentUpload: true
      }
    ]
  }
}

const loadMockData = () => {
  if (mockQuestions.value.length > 0) {
    PopupService.confirm('This will replace all existing questions. Continue?', 'Confirm Replace', 
      () => {
        // Continue with loading mock data
        loadMockDataConfirmed()
      },
      () => {
        // User cancelled
        return
      }
    )
    return
  }
  
  loadMockDataConfirmed()
}

const loadMockDataConfirmed = () => {
  let mockData
  if (questionnaire.value.planType === 'BCP') {
    mockData = getBCPMockData()
    console.log('Loading BCP mock data')
  } else if (questionnaire.value.planType === 'DRP') {
    mockData = getDRPMockData()
    console.log('Loading DRP mock data')
  } else {
    PopupService.warning('Please select a plan type (BCP or DRP) first', 'Plan Type Required')
    return
  }

  // Load the mock data
  questionnaire.value.title = mockData.questionnaire.title
  questionnaire.value.description = mockData.questionnaire.description
  mockQuestions.value = [...mockData.questions]
  
  PopupService.success(`Mock data loaded for ${questionnaire.value.planType} questionnaire with ${mockData.questions.length} questions. You can now review and modify the questions before saving.`, 'Mock Data Loaded')
}

// Optional: Complete entire workflow in one step
const completeWorkflow = async () => {
  isSubmitting.value = true
  
  try {
    const workflowData = {
      questionnaire: {
        title: questionnaire.value.title,
        description: questionnaire.value.description,
        planType: questionnaire.value.planType,
        plan_id: parseInt(selectedPlanId.value)
      },
      questions: mockQuestions.value.map(q => ({
        text: q.text,
        type: q.type,
        required: q.required,
        weight: q.weight,
        choice_options: q.choiceOptions || [],
        allow_document_upload: q.allowDocumentUpload || false,
        help_text: q.helpText || undefined,
        question_category: q.questionCategory || undefined,
        metric_name: q.metricName || undefined,
        term_id: q.termId || undefined
      })),
      assignment: assignmentForm.value
    }

    const response = await api.questionnaireWorkflow.completeWorkflow(workflowData)
    
    console.log('Workflow completed successfully:', response)
    PopupService.success('Questionnaire workflow completed successfully!', 'Workflow Completed')
    
    resetWorkflow()
    
  } catch (error) {
    console.error('Error completing workflow:', error)
    PopupService.error('Error completing workflow: ' + (error.message || 'Unknown error'), 'Workflow Failed')
  } finally {
    isSubmitting.value = false
  }
}

// Initialize component
onMounted(async () => {
  await loggingService.logPageView('BCP', 'Questionnaire Workflow')
  const tomorrow = new Date()
  tomorrow.setDate(tomorrow.getDate() + 1)
  assignmentForm.value.due_date = tomorrow.toISOString().slice(0, 16)
  
  await fetchPlanTypes()
  await fetchPlans()
  await fetchUsers()
})

</script>
