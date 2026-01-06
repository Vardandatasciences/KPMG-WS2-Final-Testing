<template>
  <div class="min-h-screen bg-background">
    <div class="container mx-auto p-6 space-y-6">
      <!-- Header -->
      <div class="flex flex-col space-y-4">
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-3xl font-bold text-foreground">📋 Questionnaire Assignment Workflow</h1>
            <p class="text-muted-foreground">Step {{ currentStep }} of 2: {{ currentStepTitle }}</p>
          </div>
          <div class="flex gap-2">
            <span class="badge badge--outline text-sm">Assignment Workflow</span>
          </div>
        </div>

        <!-- Progress Indicator -->
        <div class="card">
          <div class="card-content">
            <div class="flex items-center justify-between">
              <div class="flex items-center space-x-4">
                <div class="flex items-center">
                  <div :class="['step-indicator', currentStep >= 1 ? 'step-completed' : 'step-pending']">
                    <span class="step-number">1</span>
                  </div>
                  <span class="step-label">Assign Questionnaire</span>
                </div>
                <div class="step-connector"></div>
                <div class="flex items-center">
                  <div :class="['step-indicator', currentStep >= 2 ? 'step-completed' : 'step-pending']">
                    <span class="step-number">2</span>
                  </div>
                  <span class="step-label">Create Approval Assignment</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- STEP 1: Questionnaire Assignment Form -->
      <div v-if="currentStep === 1" class="card">
        <div class="card-header">
          <h3 class="card-title flex items-center gap-2">
            <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z"/>
            </svg>
            Step 1: Assign Questionnaire to Plan
          </h3>
          <p class="card-description">Select a questionnaire and assign it to a plan with a due date</p>
        </div>
        
        <div class="card-content space-y-6">
          <!-- Error Display -->
          <div v-if="assignmentError" class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            {{ assignmentError }}
          </div>
          
          <form @submit.prevent="submitQuestionnaireAssignment" class="space-y-6">
            <!-- Select Plan - Full Width -->
            <div class="space-y-2">
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
                >
                  <div class="trigger-content">
                    <div v-if="assignmentForm.plan_id" class="selected-plan">
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
                      <span class="table-count">{{ plans.length }} plans</span>
                    </div>
                    <div class="table-container">
                      <div v-if="isLoadingPlans" class="loading-state">
                        <div class="loading-spinner"></div>
                        <p>Loading plans...</p>
                      </div>
                      <div v-else-if="plans.length === 0" class="empty-state">
                        <div class="empty-icon">📄</div>
                        <p>No plans available</p>
                        <p class="empty-subtitle">No BCP/DRP plans found in the system</p>
                      </div>
                      <table v-else class="plans-table">
                        <thead>
                          <tr>
                            <th>Plan ID</th>
                            <th>Plan Name</th>
                            <th>Type</th>
                            <th>Strategy</th>
                            <th>Vendor</th>
                            <th>Criticality</th>
                            <th>Status</th>
                            <th>Action</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr 
                            v-for="plan in plans" 
                            :key="plan.plan_id"
                            class="plan-row"
                            :class="{ 'selected': assignmentForm.plan_id == plan.plan_id }"
                          >
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
                            <td class="action-cell">
                              <button 
                                class="select-plan-btn"
                                @click="selectPlan(plan)"
                                @mousedown.prevent
                              >
                                Select
                              </button>
                            </td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                </Transition>
              </div>
            </div>

            <!-- Other fields in one row -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div class="space-y-2">
                <label for="selectQuestionnaire">Select Questionnaire <span class="text-destructive">*</span></label>
                <select class="input" v-model="assignmentForm.questionnaire_id" id="selectQuestionnaire" required>
                  <option value="">Choose a questionnaire</option>
                  <option v-for="questionnaire in questionnaires" :key="questionnaire.questionnaire_id" :value="questionnaire.questionnaire_id">
                    {{ questionnaire.title }} (v{{ questionnaire.version || questionnaire.latestVersion }})
                  </option>
                </select>
              </div>
              <div class="space-y-2">
                <label for="assignTo">Assign To <span class="text-destructive">*</span></label>
                <select class="input" v-model="assignmentForm.assigned_to_user_id" id="assignTo" required>
                  <option value="">Select user</option>
                  <option v-for="user in users" :key="user.user_id" :value="user.user_id">
                    {{ user.username }} ({{ user.role }})
                  </option>
                </select>
              </div>
              <div class="space-y-2">
                <label for="dueDate">Due Date <span class="text-destructive">*</span></label>
                <input class="input" type="date" id="dueDate" v-model="assignmentForm.due_date" required />
              </div>
            </div>

            <div class="flex gap-4">
              <button 
                type="submit" 
                class="btn btn--primary" 
                :disabled="assignmentLoading"
              >
                <div v-if="assignmentLoading" class="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                <svg v-else class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/>
                </svg>
                {{ assignmentLoading ? 'Creating Assignment...' : 'Create Assignment' }}
              </button>
            </div>
          </form>
        </div>
      </div>

      <!-- STEP 2: Approval Assignment Form -->
      <div v-if="currentStep === 2" class="card">
        <div class="card-header">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="card-title flex items-center gap-2">
                <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
                Step 2: Create Approval Assignment
              </h3>
              <p class="card-description">
                Assignment Response ID: {{ assignmentResponseId }} - Create approval workflow for the questionnaire assignment
              </p>
            </div>
            <button 
              @click="goToStep(1)"
              class="btn btn--outline btn--sm"
              title="Back to Step 1"
            >
              <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"/>
              </svg>
              Back to Step 1
            </button>
          </div>
        </div>
        
        <div class="card-content space-y-6">
          <!-- Assignment Response Summary -->
          <div class="card bg-blue-50 border border-blue-200">
            <div class="card-header">
              <h4 class="card-title text-blue-800">Assignment Response Summary</h4>
            </div>
            <div class="card-content">
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="text-sm font-semibold text-blue-700">Assignment Response ID:</label>
                  <p class="text-sm">{{ assignmentResponseId }}</p>
                </div>
                <div>
                  <label class="text-sm font-semibold text-blue-700">Plan ID:</label>
                  <p class="text-sm">{{ assignmentForm.plan_id }}</p>
                </div>
                <div>
                  <label class="text-sm font-semibold text-blue-700">Questionnaire ID:</label>
                  <p class="text-sm">{{ assignmentForm.questionnaire_id }}</p>
                </div>
                <div>
                  <label class="text-sm font-semibold text-blue-700">Assigned To:</label>
                  <p class="text-sm">{{ getSelectedUser(assignmentForm.assigned_to_user_id) }}</p>
                </div>
                <div>
                  <label class="text-sm font-semibold text-blue-700">Due Date:</label>
                  <p class="text-sm">{{ assignmentForm.due_date }}</p>
                </div>
                <div>
                  <label class="text-sm font-semibold text-blue-700">Status:</label>
                  <span class="badge badge--success">Assignment Created</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Error Display -->
          <div v-if="approvalError" class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            {{ approvalError }}
          </div>
          
          <form @submit.prevent="submitApprovalAssignment" class="space-y-6">
            <!-- Row 1: Plan Type, Object ID, Object Type -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div class="space-y-2">
                <label for="planType" class="block text-sm font-medium">Plan Type <span class="text-destructive">*</span></label>
                <select v-model="approvalForm.plan_type" id="planType" class="input" required>
                  <option value="">Select plan type</option>
                  <option value="BCP">Business Continuity Plan</option>
                  <option value="DRP">Disaster Recovery Plan</option>
                </select>
              </div>
              <div class="space-y-2">
                <label for="objectId" class="block text-sm font-medium">Object ID <span class="text-destructive">*</span></label>
                <input 
                  v-model="approvalForm.object_id" 
                  type="number" 
                  id="objectId" 
                  class="input" 
                  required 
                  readonly
                  placeholder="Assignment Response ID"
                />
              </div>
              <div class="space-y-2">
                <label for="objectType" class="block text-sm font-medium">Object Type <span class="text-destructive">*</span></label>
                <input 
                  v-model="approvalForm.object_type" 
                  type="text" 
                  id="objectType" 
                  class="input" 
                  readonly
                />
              </div>
            </div>

            <!-- Row 2: Workflow Name, Assigner, Assigner Name -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div class="space-y-2">
                <label for="workflowName" class="block text-sm font-medium">Workflow Name <span class="text-destructive">*</span></label>
                <input 
                  v-model="approvalForm.workflow_name" 
                  type="text" 
                  id="workflowName" 
                  class="input" 
                  required 
                  placeholder="Enter workflow name"
                />
              </div>
              <div class="space-y-2">
                <label for="assignerId" class="block text-sm font-medium">Assigner <span class="text-destructive">*</span></label>
                <select v-model="approvalForm.assigner_id" id="assignerId" class="input" required @change="onAssignerChange" :disabled="isLoadingUsers">
                  <option value="">{{ isLoadingUsers ? 'Loading users...' : 'Select assigner' }}</option>
                  <option v-for="user in users" :key="user.user_id" :value="user.user_id">
                    {{ user.display_name || user.username }}
                  </option>
                </select>
              </div>
              <div class="space-y-2">
                <label for="assignerName" class="block text-sm font-medium">Assigner Name</label>
                <input 
                  v-model="approvalForm.assigner_name" 
                  type="text" 
                  id="assignerName" 
                  class="input" 
                  readonly
                  placeholder="Auto-filled from selection"
                />
              </div>
            </div>

            <!-- Row 3: Assignee Name, Assignee ID, Due Date -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div class="space-y-2">
                <label for="assigneeName" class="block text-sm font-medium">Assignee Name</label>
                <input 
                  v-model="approvalForm.assignee_name" 
                  type="text" 
                  id="assigneeName" 
                  class="input" 
                  readonly
                  placeholder="Auto-filled from selection"
                />
              </div>
              <div class="space-y-2">
                <label for="assigneeId" class="block text-sm font-medium">Assignee <span class="text-destructive">*</span></label>
                <select v-model="approvalForm.assignee_id" id="assigneeId" class="input" :required="!noApprovalNeeded" @change="onAssigneeChange" :disabled="noApprovalNeeded || isLoadingUsers">
                  <option value="">{{ isLoadingUsers ? 'Loading users...' : 'Select assignee' }}</option>
                  <option v-for="user in users" :key="user.user_id" :value="user.user_id">
                    {{ user.display_name || user.username }}
                  </option>
                </select>
              </div>
              <div class="space-y-2">
                <label for="approvalDueDate" class="block text-sm font-medium">Due Date <span class="text-destructive">*</span></label>
                <input 
                  v-model="approvalForm.due_date" 
                  type="datetime-local" 
                  id="approvalDueDate" 
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
              <button type="button" @click="resetApprovalForm" class="btn btn--outline">
                <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
                </svg>
                Reset Form
              </button>
              <button type="submit" class="btn btn--primary" :disabled="isSubmitting">
                <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
                {{ isSubmitting ? 'Creating Approval...' : 'Create Approval Assignment' }}
              </button>
            </div>
          </form>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import './QuestionnaireAssignmentWorkflow.css'
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { questionnaireApi } from '../../api/questionnaire.js'
import http from '../../api/http.js'
import { useNotifications } from '@/composables/useNotifications'
import { PopupService } from '@/popup/popupService'
import api from '../../services/api_bcp.js'
import loggingService from '@/services/loggingService'
import { useStore } from 'vuex'

const router = useRouter()

// Step management
const { showSuccess, showError, showWarning, showInfo } = useNotifications()

// Vuex store
const store = useStore()

const currentStep = ref(1)

// Assignment form data
const assignmentForm = ref({
  plan_id: '',
  questionnaire_id: '',
  assigned_to_user_id: '',
  due_date: ''
})
const assignmentLoading = ref(false)
const assignmentError = ref(null)
const assignmentResponseId = ref(null)

// Approval form data
const approvalForm = ref({
  workflow_name: '',
  plan_type: '',
  assigner_id: '',
  assigner_name: '',
  assignee_id: '',
  assignee_name: '',
  object_type: 'ASSIGNMENT_RESPONSE',
  object_id: '',
  due_date: ''
})
const isSubmitting = ref(false)
const approvalError = ref(null)
const noApprovalNeeded = ref(false)

// Data from API
const questionnaires = ref([])
const plans = ref([])
const users = ref([])
const isLoadingUsers = ref(false)
const isLoadingPlans = ref(false)
const isPlanDropdownOpen = ref(false)

// Computed properties
const currentStepTitle = computed(() => {
  return currentStep.value === 1 ? 'Assign Questionnaire' : 'Create Approval Assignment'
})

// API Functions
const fetchQuestionnaires = async () => {
  try {
    const response = await questionnaireApi.getQuestionnaires({})
    const questionnairesData = (response as any).data?.questionnaires || (response as any).questionnaires || []
    questionnaires.value = questionnairesData
  } catch (err) {
    console.error('Error fetching questionnaires:', err)
  }
}

const fetchPlans = async () => {
  isLoadingPlans.value = true
  try {
    console.log('Fetching plans from API endpoint: /api/bcpdrp/plans/')
    const response = await http.get('/bcpdrp/plans/')
    console.log('API response data:', response)
    
    const plansData = response.data?.plans || response.data || []
    plans.value = plansData
    console.log('Successfully fetched plans:', plansData.length, 'plans')
  } catch (err) {
    console.error('Error fetching plans:', err)
    plans.value = []
    PopupService.error(`Failed to load plans: ${err.message}. Please check your connection and try again.`, 'Loading Failed')
  } finally {
    isLoadingPlans.value = false
  }
}

const fetchUsers = async () => {
  isLoadingUsers.value = true
  try {
    const response = await api.users.list()
    const usersData = (response as any).users || (response as any).data?.users || []
    users.value = usersData
  } catch (err) {
    console.error('Error fetching users:', err)
    users.value = []
  } finally {
    isLoadingUsers.value = false
  }
}

// Assignment submission
const submitQuestionnaireAssignment = async () => {
  try {
    assignmentLoading.value = true
    assignmentError.value = null
    
    // Validate form
    if (!assignmentForm.value.plan_id) {
      assignmentError.value = 'Please select a plan'
      return
    }
    if (!assignmentForm.value.questionnaire_id) {
      assignmentError.value = 'Please select a questionnaire'
      return
    }
    if (!assignmentForm.value.assigned_to_user_id) {
      assignmentError.value = 'Please select a user to assign to'
      return
    }
    if (!assignmentForm.value.due_date) {
      assignmentError.value = 'Please select a due date'
      return
    }
    
    console.log('Submitting questionnaire assignment:', assignmentForm.value)
    
    // Make API call to create assignment
    const response = await http.post('/bcpdrp/questionnaires/assign/', {
      plan_id: parseInt(assignmentForm.value.plan_id),
      questionnaire_id: parseInt(assignmentForm.value.questionnaire_id),
      assigned_to_user_id: parseInt(assignmentForm.value.assigned_to_user_id),
      due_date: assignmentForm.value.due_date
    })
    
    console.log('Assignment response:', response)
    
    if (response.data && response.data.status === 'success') {
      assignmentResponseId.value = response.data.data.assignment_id
      approvalForm.value.object_id = response.data.data.assignment_id
      
      // Auto-fill approval form with assignment data
      const selectedPlan = plans.value.find(p => p.plan_id == assignmentForm.value.plan_id)
      if (selectedPlan) {
        approvalForm.value.plan_type = selectedPlan.plan_type || 'BCP'
      }
      approvalForm.value.workflow_name = `Questionnaire Assignment Approval - ${assignmentForm.value.questionnaire_id}`
      
      // Set default due date for approval (7 days from now)
      const approvalDueDate = new Date()
      approvalDueDate.setDate(approvalDueDate.getDate() + 7)
      approvalForm.value.due_date = approvalDueDate.toISOString().slice(0, 16)
      
      // Move to step 2
      goToStep(2)
    } else {
      throw new Error(response.data?.message || 'Failed to create assignment')
    }
    
  } catch (err: any) {
    console.error('Error submitting assignment:', err)
    assignmentError.value = err.response?.data?.message || err.message || 'Failed to create assignment'
  } finally {
    assignmentLoading.value = false
  }
}

// Approval submission
const submitApprovalAssignment = async () => {
  isSubmitting.value = true
  approvalError.value = null
  
  try {
    console.log('Creating approval assignment:', approvalForm.value)
    
    // Ensure all required fields are filled
    if (!approvalForm.value.workflow_name || !approvalForm.value.assigner_id || !approvalForm.value.due_date) {
      PopupService.warning('Please fill in all required fields (Workflow Name, Assigner, Due Date)', 'Required Fields Missing')
      return
    }
    
    if (!noApprovalNeeded.value && !approvalForm.value.assignee_id) {
      PopupService.warning('Please select an assignee or check "No Approval Needed"', 'Assignee Required')
      return
    }
    
    // Add no_approval_needed flag to approval data
    const approvalData = {
      ...approvalForm.value,
      no_approval_needed: noApprovalNeeded.value
    }
    
    // Call the API to create the approval assignment
    const response = await api.approvals.createAssignment(approvalData)
    
    console.log('Approval assignment created successfully:', response)
    
    // Show success popup
    PopupService.success('Questionnaire assignment and approval workflow have been created successfully!', 'Workflow Completed')
    
    // Redirect to My Approvals screen
    router.push('/bcp/my-approvals')
    
  } catch (error) {
    console.error('Error creating approval assignment:', error)
    
    // Handle different types of errors
    let errorMessage = 'Error creating approval assignment. Please try again.'
    if (error.response?.data?.message) {
      errorMessage = error.response.data.message
    } else if (error.response?.data?.error) {
      errorMessage = error.response.data.error
    } else if (error.message) {
      errorMessage = error.message
    }
    
    approvalError.value = errorMessage
  } finally {
    isSubmitting.value = false
  }
}

// Helper functions
const getSelectedUser = (userId) => {
  const user = users.value.find(u => u.user_id == userId)
  return user ? (user.display_name || user.username) : 'Unknown User'
}

const onAssignerChange = () => {
  const selectedUser = users.value.find(user => user.user_id == approvalForm.value.assigner_id)
  if (selectedUser) {
    approvalForm.value.assigner_name = selectedUser.display_name || selectedUser.username
  } else {
    approvalForm.value.assigner_name = ''
  }
}

const onAssigneeChange = () => {
  const selectedUser = users.value.find(user => user.user_id == approvalForm.value.assignee_id)
  if (selectedUser) {
    approvalForm.value.assignee_name = selectedUser.display_name || selectedUser.username
  } else {
    approvalForm.value.assignee_name = ''
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
      approvalForm.value.assigner_id = userId.toString()
      approvalForm.value.assigner_name = userName || 'Current User'
      
      // Set assignee to same as assigner
      approvalForm.value.assignee_id = userId.toString()
      approvalForm.value.assignee_name = userName || 'Current User'
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
    approvalForm.value.assignee_id = ''
    approvalForm.value.assignee_name = ''
  }
}

const resetApprovalForm = () => {
  noApprovalNeeded.value = false
  approvalForm.value = {
    workflow_name: '',
    plan_type: '',
    assigner_id: '',
    assigner_name: '',
    assignee_id: '',
    assignee_name: '',
    object_type: 'ASSIGNMENT_RESPONSE',
    object_id: assignmentResponseId.value || '',
    due_date: ''
  }
}

const goToStep = (step) => {
  currentStep.value = step
}

// Plan selection methods
const togglePlanDropdown = () => {
  isPlanDropdownOpen.value = !isPlanDropdownOpen.value
}

const closePlanDropdown = () => {
  isPlanDropdownOpen.value = false
}

// Handle click outside to close dropdown
const handleClickOutside = (event) => {
  const dropdown = event.target.closest('.modern-dropdown')
  if (!dropdown && isPlanDropdownOpen.value) {
    closePlanDropdown()
  }
}

const selectPlan = (plan) => {
  assignmentForm.value.plan_id = plan.plan_id.toString()
  // Small delay to ensure click registers
  setTimeout(() => {
    isPlanDropdownOpen.value = false
  }, 100)
}

const getSelectedPlanDisplay = () => {
  const plan = plans.value.find(p => p.plan_id.toString() === assignmentForm.value.plan_id)
  if (plan) {
    return `[${plan.plan_id}] ${plan.plan_name} (${plan.plan_type})`
  }
  return ""
}

const getSelectedPlanType = () => {
  const plan = plans.value.find(p => p.plan_id.toString() === assignmentForm.value.plan_id)
  return plan ? plan.plan_type : ""
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

// Lifecycle
onMounted(async () => {
  await loggingService.logPageView('BCP', 'Questionnaire Assignment Workflow')
  // Set default due date for assignment (tomorrow)
  const tomorrow = new Date()
  tomorrow.setDate(tomorrow.getDate() + 1)
  assignmentForm.value.due_date = tomorrow.toISOString().slice(0, 10)
  
  // Add click outside listener
  document.addEventListener('click', handleClickOutside)
  
  // Fetch all required data
  await Promise.all([
    fetchQuestionnaires(),
    fetchPlans(),
    fetchUsers()
  ])
})

// Cleanup
onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>
