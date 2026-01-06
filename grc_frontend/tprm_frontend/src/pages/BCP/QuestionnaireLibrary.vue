<template>
  <div class="min-h-screen bg-background">
    <div class="container mx-auto p-6 space-y-6">
      <!-- Action Buttons -->
      <div class="flex items-center justify-end">
        <div class="flex gap-2">
          <button class="btn btn--primary" @click="navigateToQuestionnaireWorkflow">
            <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
            </svg>
            Create New Questionnaire
          </button>
          <button class="btn btn--outline" @click="navigateToWorkflow">
            <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
            </svg>
            Assignment Workflow
          </button>
        </div>
      </div>

      <!-- Search and Filters -->
        <div class="card">
          <div class="card-header">
            <h3 class="card-title text-lg">Search & Filters</h3>
          </div>
          <div class="card-content space-y-4">
            <div class="flex flex-wrap gap-4">
              <div class="flex-1 min-w-80">
                <label class="label">Search</label>
                <div class="relative">
                  <svg class="absolute left-3 top-3 h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                  </svg>
                  <input
                    id="search"
                    class="input pl-10"
                    placeholder="Search questionnaires..."
                    v-model="searchTerm"
                  />
                </div>
              </div>
              <div class="flex gap-2">
                <div>
                  <label class="label">Plan Type</label>
                  <select class="select w-32" v-model="filters.planType">
                    <option value="ALL">Any</option>
                    <option value="BCP">BCP</option>
                    <option value="DRP">DRP</option>
                  </select>
                </div>
                <div>
                  <label class="label">Status</label>
                  <select class="select w-32" v-model="filters.status">
                    <option value="ALL">Any</option>
                    <option value="DRAFT">Draft</option>
                    <option value="IN_REVIEW">In Review</option>
                    <option value="APPROVED">Approved</option>
                    <option value="ARCHIVED">Archived</option>
                  </select>
                </div>
                <div>
                  <label class="label">Owner</label>
                  <select class="select w-32" v-model="filters.owner">
                    <option value="ALL">Any</option>
                    <option value="ME">Me</option>
                    <option value="Owner A">Owner A</option>
                    <option value="Owner B">Owner B</option>
                    <option value="Owner C">Owner C</option>
                    <option value="Owner D">Owner D</option>
                    <option value="Owner E">Owner E</option>
                  </select>
                </div>
                <div>
                  <label class="label">Vendor</label>
                  <select class="select w-32" v-model="filters.vendor">
                    <option value="ALL">Any</option>
                    <option value="Mau">Mau</option>
                    <option value="CoreNet">CoreNet</option>
                    <option value="FinEdge">FinEdge</option>
                  </select>
                </div>
              </div>
            </div>
          </div>
        </div>

      <!-- Assignment Form (replaces table when shown) -->
      <div v-if="showAssignment && selectedQuestionnaire" class="card">
        <div class="card-header">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="card-title flex items-center gap-2">
                <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z"/>
                </svg>
                Assign Questionnaire to Plan
              </h3>
              <p class="card-description">
                {{ selectedQuestionnaire.title }} (v{{ selectedQuestionnaire.version || selectedQuestionnaire.latestVersion }})
              </p>
            </div>
            <button 
              @click="showAssignment = false"
              class="btn btn--outline btn--sm"
              title="Back to Table"
            >
              <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"/>
              </svg>
              Back to Table
            </button>
          </div>
        </div>
        
        <div class="card-content space-y-6">
          <!-- Error Display -->
          <div v-if="assignmentError" class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            {{ assignmentError }}
          </div>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="space-y-2">
              <label for="selectPlan">Select Plan</label>
              <select class="input" v-model="assignmentForm.plan_id" id="selectPlan">
                <option value="">Choose a plan</option>
                <option v-for="plan in plans" :key="plan.plan_id" :value="plan.plan_id">
                  {{ plan.plan_name }} | Plan ID: {{ plan.plan_id }}
                </option>
              </select>
            </div>
            <div class="space-y-2">
              <label for="selectQuestionnaire">Selected Questionnaire</label>
              <input class="input" :value="selectedQuestionnaire.title + ' (v' + (selectedQuestionnaire.version || selectedQuestionnaire.latestVersion) + ')'" readonly />
            </div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
             <div class="space-y-2">
               <label for="assignTo">Assign To</label>
               <select class="input" v-model="assignmentForm.assigned_to_user_id" id="assignTo">
                 <option value="">Select user</option>
                 <option v-for="user in users" :key="user.user_id" :value="user.user_id">
                   {{ user.username }} ({{ user.role }})
                 </option>
               </select>
             </div>
            <div class="space-y-2">
              <label for="dueDate">Due Date</label>
              <input class="input" type="date" id="dueDate" v-model="assignmentForm.due_date" />
            </div>
          </div>

          <div class="flex gap-4">
            <button 
              class="btn btn--primary" 
              @click="submitAssignment"
              :disabled="assignmentLoading"
            >
              <div v-if="assignmentLoading" class="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              <svg v-else class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/>
              </svg>
              {{ assignmentLoading ? 'Assigning...' : 'Assign Questionnaire' }}
            </button>
            <button class="btn btn--outline" @click="showAssignment = false" :disabled="assignmentLoading">
              Cancel
            </button>
          </div>
        </div>
      </div>

      <!-- Main Table (hidden when assignment form is shown) -->
      <div v-else class="card">
        <div class="card-header">
          <h3 class="card-title">Questionnaire Catalog</h3>
          <p class="card-description">All questionnaires in the system</p>
        </div>
        <div class="card-content">
          <table class="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Title</th>
                <th>Version</th>
                <th>Status</th>
                <th>Plan Type</th>
                <th>Owner</th>
                <th>#Qs</th>
                <th>Tags</th>
                <th>Used By</th>
                <th>Updated</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="loading">
                <td colspan="11" class="text-center py-8">
                  <div class="flex items-center justify-center">
                    <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                    <span class="ml-2">Loading questionnaires...</span>
                  </div>
                </td>
              </tr>
              <tr v-else-if="error">
                <td colspan="11" class="text-center py-8 text-red-600">
                  {{ error }}
                </td>
              </tr>
              <tr v-else-if="filteredQuestionnaires.length === 0">
                <td colspan="11" class="text-center py-8 text-muted-foreground">
                  No questionnaires found
                </td>
              </tr>
              <tr v-else v-for="questionnaire in filteredQuestionnaires" :key="questionnaire.questionnaire_id">
                <td class="font-medium">{{ questionnaire.questionnaire_id }}</td>
                <td>{{ questionnaire.title }}</td>
                <td>{{ questionnaire.version }}</td>
                <td>
                  <span :class="['badge', getStatusColor(questionnaire.status)]">
                    {{ questionnaire.status }}
                  </span>
                </td>
                <td>
                  <span :class="['badge', getPlanTypeColor(questionnaire.planType)]">
                    {{ questionnaire.planType }}
                  </span>
                </td>
                <td>{{ questionnaire.owner }}</td>
                <td>{{ questionnaire.questionCount }}</td>
                <td>
                  <div class="flex flex-wrap gap-1">
                    <span v-for="tag in questionnaire.tags" :key="tag" class="badge badge--outline text-xs">
                      {{ tag }}
                    </span>
                  </div>
                </td>
                <td>{{ questionnaire.assignments }}</td>
                <td>{{ questionnaire.updated }}</td>
                <td>
                  <div class="flex gap-1">
                    <button class="btn btn--ghost btn--sm" @click="handleViewDetails(questionnaire)" title="View Details">
                      <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                      </svg>
                    </button>
                    <button class="btn btn--ghost btn--sm" @click="handleAssign(questionnaire)" title="Assign Questionnaire">
                      <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z"/>
                      </svg>
                    </button>
                    <button class="btn btn--ghost btn--sm" @click="handleApprovalAssignment(questionnaire)" title="Assign for Approval">
                      <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                      </svg>
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- View Details Modal -->
      <div v-if="showDetails && selectedQuestionnaire" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="showDetails = false">
        <div class="bg-card rounded-lg max-w-4xl max-h-[90vh] overflow-y-auto m-4">
          <div class="card-header">
            <h3 class="card-title">📋 Questionnaire Details</h3>
            <p class="card-description">
              {{ selectedQuestionnaire.title }} (Family {{ selectedQuestionnaire.family }}, v{{ selectedQuestionnaire.latestVersion }} {{ selectedQuestionnaire.status }})
            </p>
          </div>
          
          <div class="card-content space-y-6 p-4">
            <!-- Header Info -->
            <div class="grid grid-cols-2 gap-6">
              <div class="space-y-3">
                <div>
                  <label class="label text-sm font-semibold">Title</label>
                  <p class="text-sm">{{ selectedQuestionnaire.title }}</p>
                </div>
                <div>
                  <label class="label text-sm font-semibold">Plan Type</label>
                  <span :class="['badge', getPlanTypeColor(selectedQuestionnaire.planType)]">
                    {{ selectedQuestionnaire.planType }}
                  </span>
                </div>
                <div>
                  <label class="label text-sm font-semibold">Status</label>
                  <span :class="['badge', getStatusColor(selectedQuestionnaire.status)]">
                    {{ selectedQuestionnaire.status }}
                  </span>
                </div>
              </div>
              <div class="space-y-3">
                <div>
                  <label class="label text-sm font-semibold">Family</label>
                  <p class="text-sm">{{ selectedQuestionnaire.family }}</p>
                </div>
                <div>
                  <label class="label text-sm font-semibold">Owner</label>
                  <p class="text-sm">{{ selectedQuestionnaire.owner }}</p>
                </div>
                <div>
                  <label class="label text-sm font-semibold">Latest Version</label>
                  <p class="text-sm">{{ selectedQuestionnaire.latestVersion }} ({{ selectedQuestionnaire.updated }})</p>
                </div>
              </div>
            </div>

            <!-- Tags -->
            <div>
              <label class="label text-sm font-semibold">Tags</label>
              <div class="flex flex-wrap gap-2 mt-2">
                <span v-for="tag in selectedQuestionnaire.tags" :key="tag" class="badge badge--outline">
                  {{ tag }}
                </span>
              </div>
            </div>

            <!-- Usage & Associations -->
            <div class="card">
              <div class="card-header">
                <h4 class="card-title text-lg">Usage & Associations (last 90 days)</h4>
              </div>
              <div class="card-content space-y-3">
                <div class="grid grid-cols-2 gap-4">
                  <div>
                    <label class="label text-sm font-semibold">Assignments</label>
                    <p class="text-sm">9 (Mau: 5, CoreNet: 3, FinEdge: 1)</p>
                  </div>
                  <div>
                    <label class="label text-sm font-semibold">Approval Rate</label>
                    <p class="text-sm">67% | Avg Submission Time: 4.1 days</p>
                  </div>
                </div>
                <div>
                  <label class="label text-sm font-semibold">Related Plans (top)</label>
                  <p class="text-sm">Cloud BCP (Plan 1042), Payments BCP (Plan 1108), Branch Ops BCP (Plan 1203)</p>
                </div>
              </div>
            </div>

            <!-- Questions Section -->
            <div class="space-y-4">
              <div class="flex items-center justify-between">
                <h3 class="text-lg font-semibold">Questions</h3>
                <button 
                  class="btn btn--outline btn--sm"
                  @click="showQuestions = !showQuestions"
                >
                  {{ showQuestions ? 'Hide Questions' : 'View Questions' }}
                </button>
              </div>
              
              <div v-if="showQuestions" class="card">
                <div class="card-header">
                  <h4 class="card-title">Question Set — v{{ selectedQuestionnaire.latestVersion }}</h4>
                </div>
                <div class="card-content">
                  <table class="table">
                    <thead>
                      <tr>
                        <th class="w-12">#</th>
                        <th>Question Text</th>
                        <th class="w-20">Type</th>
                        <th class="w-20">Required</th>
                        <th class="w-20">Weight</th>
                        <th>Tags</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="question in questions" :key="question.id">
                        <td>{{ question.id }}</td>
                        <td>{{ question.text }}</td>
                        <td>
                          <span class="badge badge--outline">{{ question.type }}</span>
                        </td>
                        <td>
                          {{ question.required ? '☑' : '☐' }}
                        </td>
                        <td>{{ question.weight }}</td>
                        <td>
                          <div class="flex flex-wrap gap-1">
                            <span v-for="tag in question.tags" :key="tag" class="badge badge--outline text-xs">
                              {{ tag }}
                            </span>
                          </div>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            <!-- Actions -->
            <div class="flex gap-2 pt-4 border-t">
              <button class="btn btn--outline" @click="handleAssign(selectedQuestionnaire)">
                <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z"/>
                </svg>
                Assign
              </button>
              <button class="btn btn--outline">
                <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 002 2z"/>
                </svg>
                Copy
              </button>
              <button class="btn btn--outline" @click="showDetails = false">Close</button>
            </div>
          </div>
        </div>
      </div>



      <!-- Footer -->
      <div class="flex items-center justify-between border-t pt-4">
        <div class="text-sm text-muted-foreground">
          1–{{ filteredQuestionnaires.length }} of {{ (summary as any).total_families || summary.total_questionnaires }} families
        </div>
        <div class="flex items-center gap-2">
          <span class="text-sm text-muted-foreground">Rows per page:</span>
          <select class="select w-20">
            <option value="10">10</option>
            <option value="25" selected>25</option>
            <option value="50">50</option>
            <option value="100">100</option>
          </select>
          <div class="flex gap-1">
            <button class="btn btn--outline btn--sm">‹ Prev</button>
            <button class="btn btn--outline btn--sm">1</button>
            <button class="btn btn--outline btn--sm">2</button>
            <button class="btn btn--outline btn--sm">3</button>
            <span class="px-2">…</span>
            <button class="btn btn--outline btn--sm">Next ›</button>
          </div>
        </div>
        <div class="text-sm text-muted-foreground">
          Last refreshed: 2025-08-18 10:12 IST
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import './QuestionnaireLibrary.css'
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { questionnaireApi } from '../../api/questionnaire.js'
import http from '../../api/http.js'
import { useNotifications } from '@/composables/useNotifications'
import { PopupService } from '@/popup/popupService'
import loggingService from '@/services/loggingService'

const router = useRouter()
const { showSuccess, showError, showWarning, showInfo } = useNotifications()

const searchTerm = ref("")
const filters = ref({
  planType: "ALL",
  status: "ALL",
  owner: "ALL",
  vendor: "ALL"
})
const showDetails = ref(false)
const showQuestions = ref(false)
const showAssignment = ref(false)
const selectedQuestionnaire = ref<any>(null)

// Assignment form data
const assignmentForm = ref({
  plan_id: '',
  questionnaire_id: '',
  assigned_to_user_id: '',
  due_date: ''
})
const assignmentLoading = ref(false)
const assignmentError = ref(null)

// Data from API
const questionnaires = ref([])
const plans = ref([])
const users = ref([])
const summary = ref({
  total_questionnaires: 0,
  approved: 0,
  used_in_assignments: 0,
  drafts: 0,
  in_review: 0,
  archived: 0,
  reuse_rate: "0%"
})
const loading = ref(false)
const error = ref(null)

// Questions data (will be loaded from API)
const questions = ref([])

// Computed property for filtered questionnaires
const filteredQuestionnaires = computed(() => {
  return questionnaires.value
})

// API Functions
const fetchQuestionnaires = async () => {
  try {
    loading.value = true
    error.value = null
    
    const params = {
      search: searchTerm.value,
      planType: filters.value.planType,
      status: filters.value.status,
      owner: filters.value.owner
    }
    
    console.log('Fetching questionnaires with params:', params)
    const response = await questionnaireApi.getQuestionnaires(params)
    console.log('API Response:', response)
    console.log('Response data:', response.data)
    console.log('Response data type:', typeof response.data)
    
    // Try both possible structures
    const questionnairesData = (response as any).data?.questionnaires || (response as any).questionnaires || []
    const summaryData = (response as any).data?.summary || (response as any).summary || summary.value
    
    questionnaires.value = questionnairesData
    summary.value = summaryData
    
    console.log('Processed questionnaires:', questionnaires.value)
    console.log('Processed summary:', summary.value)
    
    // Show success notification
    await showSuccess('Questionnaires Loaded', `Successfully loaded ${questionnaires.value.length} questionnaires.`, {
      action: 'questionnaires_loaded',
      count: questionnaires.value.length,
      search_term: searchTerm.value,
      filters: filters.value
    })
    
    // Show success popup
    PopupService.success(`Successfully loaded ${questionnaires.value.length} questionnaires.`, 'Questionnaires Loaded')
  } catch (err) {
    error.value = err.message || 'Failed to fetch questionnaires'
    console.error('Error fetching questionnaires:', err)
    
    // Show error notification
    await showError('Loading Failed', 'Failed to fetch questionnaires. Please try again.', {
      action: 'questionnaires_loading_failed',
      error_message: err.message,
      search_term: searchTerm.value
    })
    
    // Show error popup
    PopupService.error('Failed to fetch questionnaires. Please try again.', 'Loading Failed')
  } finally {
    loading.value = false
  }
}

const fetchQuestionnaireDetails = async (questionnaireId) => {
  try {
    const response = await questionnaireApi.getQuestionnaireDetail(questionnaireId)
    console.log('Questionnaire details response:', response)
    console.log('Response data:', response.data)
    
    // Try both possible structures
    const questionsData = (response as any).data?.questions || (response as any).questions || []
    questions.value = questionsData
    
    console.log('Processed questions:', questions.value)
    return response
  } catch (err) {
    console.error('Error fetching questionnaire details:', err)
    throw err
  }
}

// Fetch plans from API (similar to Plan Library)
const fetchPlans = async () => {
  try {
    console.log('Fetching plans for assignment dropdown...')
    const response = await http.get('/bcpdrp/plans/')
    console.log('Plans API Response:', response)
    
    // Extract plans from response
    const plansData = (response as any).data?.plans || (response as any).data || []
    plans.value = plansData
    
    console.log('Processed plans:', plans.value)
  } catch (err) {
    console.error('Error fetching plans:', err)
    // Set empty array on error to prevent dropdown issues
    plans.value = []
  }
}

// Fetch users from rbac_tprm table
const fetchUsers = async () => {
  try {
    console.log('Fetching users from rbac_tprm table...')
    const response = await http.get('/bcpdrp/users/')
    console.log('Users API Response:', response)
    
    // Extract users from response
    const usersData = (response as any).data?.users || (response as any).data || []
    users.value = usersData
    
    console.log('Processed users:', users.value)
  } catch (err) {
    console.error('Error fetching users:', err)
    // Set empty array on error to prevent dropdown issues
    users.value = []
  }
}


// Lifecycle
onMounted(async () => {
  await loggingService.logPageView('BCP', 'Questionnaire Library')
  await fetchQuestionnaires()
})

// Watch for filter changes
watch([searchTerm, filters], () => {
  fetchQuestionnaires()
}, { deep: true })

const getStatusColor = (status: string) => {
  switch (status) {
    case "APPROVED":
      return "bg-green-100 text-green-800 border-green-200"
    case "IN_REVIEW":
      return "bg-yellow-100 text-yellow-800 border-yellow-200"
    case "DRAFT":
      return "bg-blue-100 text-blue-800 border-blue-200"
    case "ARCHIVED":
      return "bg-gray-100 text-gray-800 border-gray-200"
    default:
      return "bg-gray-100 text-gray-800 border-gray-200"
  }
}

const getPlanTypeColor = (type: string) => {
  return type === "BCP" 
    ? "bg-blue-100 text-blue-800 border-blue-200" 
    : "bg-purple-100 text-purple-800 border-purple-200"
}

const handleViewDetails = async (questionnaire: any) => {
  try {
    selectedQuestionnaire.value = questionnaire
    await fetchQuestionnaireDetails(questionnaire.questionnaire_id)
    showDetails.value = true
    
    // Show success notification
    await showSuccess('Questionnaire Details', `Viewing details for questionnaire: ${questionnaire.title}`, {
      action: 'questionnaire_view_details',
      questionnaire_id: questionnaire.questionnaire_id,
      questionnaire_title: questionnaire.title
    })
    
    // Show success popup
    PopupService.success(`Viewing details for questionnaire: ${questionnaire.title}`, 'Questionnaire Details')
  } catch (err) {
    console.error('Error loading questionnaire details:', err)
    
    // Show error notification
    await showError('View Failed', 'Failed to load questionnaire details. Please try again.', {
      action: 'questionnaire_view_failed',
      questionnaire_id: questionnaire.questionnaire_id,
      error_message: err.message
    })
    
    // Show error popup
    PopupService.error('Failed to load questionnaire details. Please try again.', 'View Failed')
  }
}


const handleAssign = async (questionnaire: any) => {
  selectedQuestionnaire.value = questionnaire
  
  // Reset assignment form and set questionnaire_id
  assignmentForm.value = {
    plan_id: '',
    questionnaire_id: questionnaire.questionnaire_id,
    assigned_to_user_id: '',
    due_date: ''
  }
  assignmentError.value = null
  
  showAssignment.value = true
  // Fetch plans and users when assignment form is shown
  await Promise.all([fetchPlans(), fetchUsers()])
}

const submitAssignment = async () => {
  try {
    assignmentLoading.value = true
    assignmentError.value = null
    
    // Validate form
    if (!assignmentForm.value.plan_id) {
      assignmentError.value = 'Please select a plan'
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
    
    console.log('Submitting assignment:', assignmentForm.value)
    
    // Make API call to create assignment
    const response = await http.post('/bcpdrp/questionnaires/assign/', {
      plan_id: parseInt(assignmentForm.value.plan_id),
      questionnaire_id: parseInt(assignmentForm.value.questionnaire_id),
      assigned_to_user_id: parseInt(assignmentForm.value.assigned_to_user_id),
      due_date: assignmentForm.value.due_date
    })
    
    console.log('Assignment response:', response)
    
    if (response.data && response.data.status === 'success') {
      PopupService.success(`Questionnaire assigned successfully! Created 1 assignment record with ${response.data.data.question_count} questions.`, 'Assignment Created')
      showAssignment.value = false
      
      // Refresh questionnaires list to show updated assignment counts
      await fetchQuestionnaires()
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

const handleApprovalAssignment = (questionnaire: any) => {
  // Navigate to approval assignment screen with pre-filled data
  router.push({
    path: '/bcp/approval-assignment',
    query: {
      planId: questionnaire.questionnaire_id,
      objectType: 'NEW QUESTIONNAIRE',
      planType: questionnaire.planType
    }
  })
}

const navigateToWorkflow = () => {
  router.push('/bcp/questionnaire-assignment-workflow')
}

const navigateToQuestionnaireWorkflow = () => {
  router.push('/bcp/questionnaire-workflow')
}
</script>
