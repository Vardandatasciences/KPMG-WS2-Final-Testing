<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex justify-between items-center">
      <div>
        <h1 class="text-2xl font-bold text-foreground">🧪 Testing Library</h1>
        <p class="text-muted-foreground">Manage and organize testing questionnaires</p>
      </div>
      <div class="flex gap-2">
        <button class="btn btn--primary" @click="showCreateModal = true">
          <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
          </svg>
          Create New Questionnaire
        </button>
        <button class="btn btn--outline">
          <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
          </svg>
          Import Template
        </button>
        <div class="relative">
          <button class="btn btn--outline" @click="showExportMenu = !showExportMenu">
            Export All
            <svg class="h-4 w-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
            </svg>
          </button>
          <div v-if="showExportMenu" class="absolute right-0 top-full mt-1 bg-panel border border-border rounded-md shadow-lg z-10 min-w-[120px]">
            <button class="block w-full text-left px-3 py-2 hover:bg-muted">CSV</button>
            <button class="block w-full text-left px-3 py-2 hover:bg-muted">JSON</button>
            <button class="block w-full text-left px-3 py-2 hover:bg-muted">PDF</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Search and Filters -->
    <div class="card">
      <div class="card-content p-4">
        <div class="flex gap-4 mb-4">
          <div class="flex-1">
            <div class="relative">
              <svg class="absolute left-3 top-3 h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
              </svg>
              <input
                class="input pl-9"
                placeholder="Search assignments..."
                v-model="searchTerm"
                @input="fetchAssignments"
              />
            </div>
          </div>
        </div>
        
        <div class="filters-container">
          <div class="filter-item">
            <label class="label">Status</label>
            <select class="input" v-model="filters.status" @change="fetchAssignments">
              <option value="all">Any</option>
              <option value="IN_PROGRESS">In Progress</option>
              <option value="SUBMITTED">Submitted</option>
              <option value="COMPLETED">Completed</option>
            </select>
          </div>
          <div class="filter-item">
            <label class="label">Plan ID</label>
            <input 
              class="input" 
              v-model="filters.planType" 
              placeholder="Filter by Plan ID"
              @input="fetchAssignments"
            />
          </div>
          <div class="filter-item">
            <label class="label">Assigned To</label>
            <input 
              class="input" 
              v-model="filters.owner" 
              placeholder="Filter by User ID"
              @input="fetchAssignments"
            />
          </div>
          <div class="filter-item">
            <label class="label">Min Questions</label>
            <select class="input" v-model="filters.minQuestions">
              <option value="all">Any</option>
              <option value="1">1+</option>
              <option value="5">5+</option>
              <option value="10">10+</option>
              <option value="15">15+</option>
            </select>
          </div>
          <div class="filter-item">
            <label class="label">Questionnaire ID</label>
            <input 
              class="input" 
              v-model="filters.vendor" 
              placeholder="Filter by Questionnaire ID"
              @input="fetchAssignments"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- Summary Stats -->
    <div class="summary-stats-container">
      <div class="stat-card">
        <div class="stat-value">{{ summaryStats.totalAssignments }}</div>
        <div class="stat-label">Total Assignments</div>
      </div>
      <div class="stat-card">
        <div class="stat-value orange-stat">{{ summaryStats.inProgress }}</div>
        <div class="stat-label">In Progress</div>
      </div>
      <div class="stat-card">
        <div class="stat-value blue-stat">{{ summaryStats.submitted }}</div>
        <div class="stat-label">Submitted</div>
      </div>
      <div class="stat-card">
        <div class="stat-value green-stat">{{ summaryStats.completed }}</div>
        <div class="stat-label">Completed</div>
      </div>
    </div>

    <!-- Main Table -->
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">Assignment Responses</h3>
      </div>
      <div class="card-content">
        <div v-if="isLoading" class="loading-state">
          <div class="loading-spinner"></div>
          <p>Loading assignments...</p>
        </div>
        <div v-else-if="assignments.length === 0" class="empty-state">
          <div class="empty-icon">📋</div>
          <p>No assignments found</p>
          <p class="empty-subtitle">Create your first questionnaire assignment to get started</p>
        </div>
        <table v-else class="table">
          <thead>
            <tr>
              <th>Assignment ID</th>
              <th>Plan ID</th>
              <th>Questionnaire ID</th>
              <th>Assigned To</th>
              <th>Status</th>
              <th>Questions</th>
              <th>Due Date</th>
              <th>Assigned Date</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="assignment in filteredAssignments" :key="assignment.assignment_response_id">
              <td class="font-medium">{{ assignment.assignment_response_id }}</td>
              <td>{{ assignment.plan_id }}</td>
              <td>{{ assignment.questionnaire_id }}</td>
              <td>{{ assignment.assigned_to_user_id }}</td>
              <td>
                <span :class="['badge', getStatusColor(assignment.status)]">
                  {{ assignment.status }}
                </span>
              </td>
              <td>{{ assignment.total_questions || 0 }}</td>
              <td>{{ assignment.due_date ? new Date(assignment.due_date).toLocaleDateString() : 'N/A' }}</td>
              <td>{{ assignment.assigned_at ? new Date(assignment.assigned_at).toLocaleDateString() : 'N/A' }}</td>
              <td>
                <div class="flex gap-2">
                  <button 
                    class="action-icon-btn" 
                    @click="handleViewDetails(assignment)"
                    title="View Details"
                  >
                    <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                    </svg>
                  </button>
                  <button 
                    class="action-icon-btn" 
                    @click="viewAnswers(assignment)"
                    title="View Answers"
                  >
                    <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                    </svg>
                  </button>
                  <button 
                    class="action-icon-btn" 
                    @click="exportAssignment(assignment)"
                    title="Export"
                  >
                    <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                    </svg>
                  </button>
                  <button 
                    class="action-icon-btn" 
                    @click="createApprovalAssignment(assignment)"
                    title="Create Approval Assignment"
                  >
                    <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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

    <!-- Questionnaire Detail Modal -->
    <div v-if="showDetailModal" class="modal-overlay" @click.self="showDetailModal = false">
      <div class="modal-content detail-modal">
        <div class="modal-header">
          <h3 class="modal-title">🧾 Questionnaire Detail — {{ mockQuestionnaireDetail.title }}</h3>
        </div>
        <button @click="showDetailModal = false" class="modal-close-btn">✕</button>
        <div class="p-6">
          <div class="space-y-6">
            <!-- Basic Info -->
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="label">Plan Type</label>
                <span :class="['badge', getPlanTypeColor(mockQuestionnaireDetail.planType)]">
                  {{ mockQuestionnaireDetail.planType }}
                </span>
              </div>
              <div>
                <label class="label">Status</label>
                <span :class="['badge', getStatusColor(mockQuestionnaireDetail.status)]">
                  {{ mockQuestionnaireDetail.status }}
                </span>
              </div>
              <div>
                <label class="label">Owner</label>
                <p>{{ mockQuestionnaireDetail.owner }}</p>
              </div>
              <div>
                <label class="label">Last Updated</label>
                <p>{{ mockQuestionnaireDetail.lastUpdated }}</p>
              </div>
            </div>

            <!-- Tags -->
            <div>
              <label class="label">Tags</label>
              <div class="flex gap-2 mt-1">
                <span v-for="(tag, index) in mockQuestionnaireDetail.tags" :key="index" class="badge badge--outline">{{ tag }}</span>
              </div>
            </div>

            <!-- Associated Plans -->
            <div>
              <label class="label">Associated Plans</label>
              <table class="table">
                <thead>
                  <tr>
                    <th>Plan ID</th>
                    <th>Plan Name</th>
                    <th>Type</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="plan in mockQuestionnaireDetail.associatedPlans" :key="plan.id">
                    <td>{{ plan.id }}</td>
                    <td>{{ plan.name }}</td>
                    <td>
                      <span :class="['badge', getPlanTypeColor(plan.type)]">{{ plan.type }}</span>
                    </td>
                    <td>
                      <span :class="['badge', getStatusColor(plan.status)]">{{ plan.status }}</span>
                    </td>
                    <td>
                      <button class="btn btn--ghost btn--sm">
                        View ▶
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Associated Tests -->
            <div>
              <label class="label">Associated Tests (Assignments)</label>
              <table class="table">
                <thead>
                  <tr>
                    <th>Test ID</th>
                    <th>Plan Name</th>
                    <th>Status</th>
                    <th>Assigned To</th>
                    <th>Due Date</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="test in mockQuestionnaireDetail.associatedTests" :key="test.id">
                    <td>{{ test.id }}</td>
                    <td>{{ test.planName }}</td>
                    <td>
                      <span :class="['badge', getStatusColor(test.status)]">{{ test.status }}</span>
                    </td>
                    <td>{{ test.assignedTo }}</td>
                    <td>{{ test.dueDate }}</td>
                    <td>
                      <button class="btn btn--ghost btn--sm">
                        View ▶
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Version History -->
            <div>
              <label class="label">Version History</label>
              <table class="table">
                <thead>
                  <tr>
                    <th>Version</th>
                    <th>Status</th>
                    <th>Approved By</th>
                    <th>Date</th>
                    <th>Changes Summary</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="version in mockQuestionnaireDetail.versions" :key="version.version">
                    <td class="font-medium">{{ version.version }}</td>
                    <td>
                      <span :class="['badge', getStatusColor(version.status)]">{{ version.status }}</span>
                    </td>
                    <td>{{ version.approvedBy }}</td>
                    <td>{{ version.date }}</td>
                    <td>{{ version.changes }}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Reviewer Comments -->
            <div>
              <label class="label">Reviewer Comments</label>
              <div class="space-y-2">
                <div v-for="(comment, index) in mockQuestionnaireDetail.reviewerComments" :key="index" class="p-3 bg-muted rounded-lg">
                  <div class="font-medium">Version {{ comment.version }}</div>
                  <div class="text-sm text-muted-foreground">{{ comment.comment }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Create New Questionnaire Modal -->
    <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false">
      <div class="modal-content create-modal">
        <div class="modal-header">
          <h3 class="modal-title">✏️ Create New Questionnaire</h3>
        </div>
        <button @click="showCreateModal = false" class="modal-close-btn">✕</button>
        <div class="p-6">
          <div class="space-y-6">
            <!-- Basic Info -->
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="label" for="title">Title</label>
                <input
                  id="title"
                  class="input"
                  v-model="newQuestionnaire.title"
                  placeholder="Enter questionnaire title"
                />
              </div>
              <div>
                <label class="label" for="category">Category/Tag</label>
                <input
                  id="category"
                  class="input"
                  v-model="newQuestionnaire.category"
                  placeholder="e.g., Failover, RTO, DRP"
                />
              </div>
            </div>

            <div>
              <label class="label" for="description">Description</label>
              <textarea
                id="description"
                class="textarea"
                v-model="newQuestionnaire.description"
                placeholder="Enter questionnaire description"
              ></textarea>
            </div>

            <!-- Plan Type -->
            <div>
              <label class="label">Plan Type</label>
              <div class="flex gap-6 mt-2">
                <label class="flex items-center space-x-2">
                  <input type="radio" v-model="newQuestionnaire.planType" value="BCP" class="radio-input" />
                  <span>BCP</span>
                </label>
                <label class="flex items-center space-x-2">
                  <input type="radio" v-model="newQuestionnaire.planType" value="DRP" class="radio-input" />
                  <span>DRP</span>
                </label>
                <label class="flex items-center space-x-2">
                  <input type="radio" v-model="newQuestionnaire.planType" value="Other" class="radio-input" />
                  <span>Other</span>
                </label>
              </div>
            </div>

            <!-- Questions Setup -->
            <div>
              <div class="flex justify-between items-center mb-4">
                <label class="text-lg font-medium">Questions Setup</label>
                <button class="btn btn--primary btn--sm" @click="addNewQuestion">
                  <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
                  </svg>
                  Add New Question
                </button>
              </div>

              <div class="space-y-4">
                <div v-for="(question, index) in newQuestionnaire.questions" :key="question.id" class="p-4 border rounded-lg">
                  <div class="flex justify-between items-start mb-4">
                    <label class="font-medium">Question #{{ index + 1 }}</label>
                    <button
                      class="btn btn--ghost btn--sm"
                      @click="removeQuestion(question.id)"
                    >
                      <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                      </svg>
                    </button>
                  </div>
                  
                  <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div class="md:col-span-2">
                      <label class="label">Question Text</label>
                      <textarea
                        class="textarea"
                        v-model="question.text"
                        placeholder="Enter question text"
                      ></textarea>
                    </div>
                    
                    <div class="space-y-4">
                      <div>
                        <label class="label">Type</label>
                        <select class="input" v-model="question.type">
                          <option value="YES_NO">Yes/No</option>
                          <option value="TEXT">Text</option>
                          <option value="NUMBER">Number</option>
                          <option value="DATE">Date</option>
                        </select>
                      </div>
                      
                      <div class="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          :id="`required-${question.id}`"
                          v-model="question.required"
                          class="checkbox-input"
                        />
                        <label :for="`required-${question.id}`">Required</label>
                      </div>
                      
                      <div>
                        <label class="label">Weight</label>
                        <input
                          type="number"
                          class="input"
                          v-model="question.weight"
                          step="0.1"
                          min="0"
                          max="2"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Action Buttons -->
            <div class="flex justify-end gap-4">
              <button class="btn btn--outline" @click="showCreateModal = false">
                Cancel
              </button>
              <button class="btn btn--outline">
                Save as Draft
              </button>
              <button class="btn btn--primary">
                Submit & Create
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import './TestingLibrary.css'
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../../services/api_bcp.js'
import { useNotifications } from '@/composables/useNotifications'
import { PopupService } from '@/popup/popupService'
import loggingService from '@/services/loggingService'

const router = useRouter()

const { showSuccess, showError, showWarning, showInfo } = useNotifications()

const searchTerm = ref("")
const filters = ref({
  planType: "all",
  status: "all",
  owner: "all",
  vendor: "all",
  minQuestions: "all"
})
const selectedQuestionnaire = ref<any>(null)
const showCreateModal = ref(false)
const showDetailModal = ref(false)
const showExportMenu = ref(false)

// Real data from API
const assignments = ref<any[]>([])
const isLoading = ref(false)
const summaryStats = ref({
  totalAssignments: 0,
  inProgress: 0,
  submitted: 0,
  completed: 0
})

// Fetch assignments from API
const fetchAssignments = async () => {
  isLoading.value = true
  try {
    console.log('Fetching assignments with params:', {
      search: searchTerm.value,
      status: filters.value.status !== 'all' ? filters.value.status : undefined
    })
    
    const response = await api.questionnaires.assignments({
      search: searchTerm.value,
      status: filters.value.status !== 'all' ? filters.value.status : undefined
    })
    
    console.log('API Response:', response)
    
    if (response && response.data && response.data.assignments) {
      console.log('Assignments found:', response.data.assignments.length)
      assignments.value = response.data.assignments
      updateSummaryStats()
    } else {
      console.log('No assignments in response or invalid response format')
      console.log('Response structure:', Object.keys(response || {}))
      if (response && response.data) {
        console.log('Data structure:', Object.keys(response.data || {}))
      }
    }
  } catch (error) {
    console.error('Error fetching assignments:', error)
    console.error('Error details:', error.response?.data || error.message)
    PopupService.error(`Failed to fetch assignments: ${error.message}`, 'Loading Failed')
  } finally {
    isLoading.value = false
  }
}

// Update summary statistics
const updateSummaryStats = () => {
  const total = assignments.value.length
  const inProgress = assignments.value.filter(a => a.status === 'IN_PROGRESS').length
  const submitted = assignments.value.filter(a => a.status === 'SUBMITTED').length
  const completed = assignments.value.filter(a => a.status === 'COMPLETED').length
  
  summaryStats.value = {
    totalAssignments: total,
    inProgress: inProgress,
    submitted: submitted,
    completed: completed
  }
}

// Mock data for testing questionnaires (keeping for reference)
const mockTestingData = [
  {
    id: "QF-1001",
    title: "Payments DC Failover",
    latestVersion: "1.3",
    status: "APPROVED",
    planType: "BCP",
    owner: "Owner A",
    questionCount: 14,
    usedBy: 27,
    lastUpdated: "2025-08-16",
    tags: ["Failover", "Payments", "BCP"]
  },
  {
    id: "QF-1007",
    title: "Network Recovery & Failback",
    latestVersion: "1.2",
    status: "APPROVED",
    planType: "DRP",
    owner: "Owner B",
    questionCount: 18,
    usedBy: 19,
    lastUpdated: "2025-08-14",
    tags: ["Recovery", "Network", "Failback"]
  },
  {
    id: "QF-1010",
    title: "Backup Verification Compliance",
    latestVersion: "1.0",
    status: "APPROVED",
    planType: "DRP",
    owner: "Owner A",
    questionCount: 10,
    usedBy: 11,
    lastUpdated: "2025-08-10",
    tags: ["Backup", "Compliance", "Verification"]
  },
  {
    id: "QF-1016",
    title: "BCP Roles & Responsibilities",
    latestVersion: "0.9",
    status: "IN_REVIEW",
    planType: "BCP",
    owner: "Owner C",
    questionCount: 12,
    usedBy: 3,
    lastUpdated: "2025-08-17",
    tags: ["BCP", "Roles", "Responsibilities"]
  },
  {
    id: "QF-1022",
    title: "Application Recovery Orchestration",
    latestVersion: "1.1",
    status: "APPROVED",
    planType: "DRP",
    owner: "Owner B",
    questionCount: 16,
    usedBy: 7,
    lastUpdated: "2025-08-13",
    tags: ["Application", "Recovery", "Orchestration"]
  },
  {
    id: "QF-1031",
    title: "Cloud Region Failover Readiness",
    latestVersion: "1.1",
    status: "APPROVED",
    planType: "BCP",
    owner: "Owner D",
    questionCount: 15,
    usedBy: 7,
    lastUpdated: "2025-08-13",
    tags: ["Cloud", "Failover", "Region"]
  },
  {
    id: "QF-1033",
    title: "Data Integrity & RPO Validation",
    latestVersion: "1.0",
    status: "APPROVED",
    planType: "DRP",
    owner: "Owner A",
    questionCount: 13,
    usedBy: 8,
    lastUpdated: "2025-08-09",
    tags: ["Data", "Integrity", "RPO"]
  },
  {
    id: "QF-1040",
    title: "Branch Ops Recovery Checklist",
    latestVersion: "0.8",
    status: "IN_REVIEW",
    planType: "DRP",
    owner: "Owner E",
    questionCount: 11,
    usedBy: 2,
    lastUpdated: "2025-08-15",
    tags: ["Branch", "Operations", "Recovery"]
  }
]

// Mock data for questionnaire details
const mockQuestionnaireDetail = {
  id: "QF-1001",
  title: "Payments DC Failover",
  planType: "BCP",
  owner: "Owner A",
  status: "APPROVED",
  lastUpdated: "2025-08-16",
  version: "1.3",
  tags: ["Failover", "Payments", "BCP"],
  associatedPlans: [
    { id: "1042", name: "Cloud BCP", type: "BCP", status: "APPROVED" },
    { id: "1043", name: "Network DRP", type: "DRP", status: "UNDER_EVAL" },
    { id: "1044", name: "Branch DRP", type: "DRP", status: "OCR_DONE" }
  ],
  associatedTests: [
    { id: "501", planName: "Cloud BCP", status: "IN_PROGRESS", assignedTo: "User A", dueDate: "2025-09-05" },
    { id: "502", planName: "Network DRP", status: "SUBMITTED", assignedTo: "User B", dueDate: "2025-08-30" },
    { id: "503", planName: "Branch DRP", status: "COMPLETED", assignedTo: "User C", dueDate: "2025-08-15" }
  ],
  versions: [
    { version: "1.3", status: "APPROVED", approvedBy: "Owner A", date: "2025-08-16", changes: "Added Q4, Adjusted Q5 weight" },
    { version: "1.2", status: "APPROVED", approvedBy: "Owner A", date: "2025-08-12", changes: "Updated Q1 wording" },
    { version: "1.1", status: "APPROVED", approvedBy: "Owner A", date: "2025-08-10", changes: "Added new validation for failback" },
    { version: "1.0", status: "ARCHIVED", approvedBy: "—", date: "2025-08-08", changes: "Initial version" }
  ],
  reviewerComments: [
    { version: "1.3", comment: "Add question on failback test evidence." },
    { version: "1.2", comment: "Clarify DR site wording for critical systems." }
  ]
}

// Mock questions for creation modal
const defaultQuestions = [
  { id: 1, text: "Is a DR site available for all critical payment systems?", type: "YES_NO", required: true, weight: 1.0 },
  { id: 2, text: "Provide the current RTO for Core Banking API.", type: "TEXT", required: true, weight: 1.0 },
  { id: 3, text: "Provide the current RPO for Core Banking API.", type: "TEXT", required: true, weight: 1.0 },
  { id: 4, text: "Was DR failback executed successfully in the last 12 months?", type: "YES_NO", required: true, weight: 1.0 },
  { id: 5, text: "Attach evidence of latest DR failover/failback test.", type: "TEXT", required: false, weight: 0.5 },
  { id: 6, text: "Are backup verification reports up-to-date?", type: "YES_NO", required: true, weight: 1.0 }
]

const newQuestionnaire = ref({
  title: "",
  description: "",
  planType: "BCP",
  category: "",
  questions: defaultQuestions
})

const getStatusColor = (status: string) => {
  switch (status) {
    case "APPROVED":
      return "bg-green-100 text-green-800 border-green-200";
    case "IN_REVIEW":
      return "bg-yellow-100 text-yellow-800 border-yellow-200";
    case "DRAFT":
      return "bg-gray-100 text-gray-800 border-gray-200";
    case "ARCHIVED":
      return "bg-slate-100 text-slate-800 border-slate-200";
    case "UNDER_EVAL":
      return "bg-blue-100 text-blue-800 border-blue-200";
    case "OCR_DONE":
      return "bg-purple-100 text-purple-800 border-purple-200";
    case "IN_PROGRESS":
      return "bg-orange-100 text-orange-800 border-orange-200";
    case "SUBMITTED":
      return "bg-indigo-100 text-indigo-800 border-indigo-200";
    case "COMPLETED":
      return "bg-green-100 text-green-800 border-green-200";
    default:
      return "bg-gray-100 text-gray-800 border-gray-200";
  }
}

const getPlanTypeColor = (type: string) => {
  switch (type) {
    case "BCP":
      return "bg-blue-100 text-blue-800 border-blue-200";
    case "DRP":
      return "bg-purple-100 text-purple-800 border-purple-200";
    default:
      return "bg-gray-100 text-gray-800 border-gray-200";
  }
}

const handleViewDetails = (assignment: any) => {
  selectedQuestionnaire.value = assignment
  showDetailModal.value = true
}

const viewAnswers = (assignment: any) => {
  // Navigate to questionnaire assignment page or show answers in modal
  console.log('View answers for assignment:', assignment.assignment_response_id)
  // You can implement navigation or modal display here
}

const exportAssignment = (assignment: any) => {
  // Export assignment data
  console.log('Export assignment:', assignment.assignment_response_id)
  // You can implement export functionality here
  PopupService.success(`Export functionality for assignment ${assignment.assignment_response_id} - to be implemented`, 'Export')
}

const createApprovalAssignment = (assignment: any) => {
  // Navigate to approval assignment screen with prefilled data
  console.log('Creating approval assignment for:', assignment.assignment_response_id)
  
  // Store the assignment data in sessionStorage for the approval form
  const approvalData = {
    object_type: 'assignment_response',
    object_id: assignment.assignment_response_id,
    assignment_response_id: assignment.assignment_response_id,
    plan_id: assignment.plan_id,
    questionnaire_id: assignment.questionnaire_id,
    assigned_to_user_id: assignment.assigned_to_user_id,
    status: assignment.status,
    autoOpenForm: true // Flag to indicate form should open automatically
  }
  
  sessionStorage.setItem('prefilledApprovalData', JSON.stringify(approvalData))
  
  // Navigate to approval assignment screen with query parameter to trigger form opening
  router.push({
    path: '/bcp/approval-assignment',
    query: {
      createNew: 'true',
      objectType: 'assignment_response',
      objectId: assignment.assignment_response_id
    }
  })
}

const addNewQuestion = () => {
  const newId = Math.max(...newQuestionnaire.value.questions.map(q => q.id)) + 1
  newQuestionnaire.value.questions.push({
    id: newId,
    text: "",
    type: "TEXT",
    required: true,
    weight: 1.0
  })
}

const removeQuestion = (id: number) => {
  newQuestionnaire.value.questions = newQuestionnaire.value.questions.filter(q => q.id !== id)
}

// Filter assignments based on local filters
const filteredAssignments = computed(() => {
  let filtered = assignments.value

  // Apply minimum questions filter
  if (filters.value.minQuestions !== 'all') {
    const minQuestions = parseInt(filters.value.minQuestions)
    filtered = filtered.filter(assignment => 
      (assignment.total_questions || 0) >= minQuestions
    )
  }

  return filtered
})

// Initialize data on component mount
onMounted(async () => {
  await loggingService.logPageView('BCP', 'Testing Library')
  await fetchAssignments()
})
</script>
