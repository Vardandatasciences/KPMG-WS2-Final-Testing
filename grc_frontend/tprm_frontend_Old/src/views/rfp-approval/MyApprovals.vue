<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">My RFP Approvals</h1>
        <p class="text-gray-600 mt-1">Review and manage your pending RFP approval requests</p>
      </div>
      <div class="flex items-center space-x-3">
        <button 
          @click="fetchApprovals" 
          :disabled="loading"
          class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50"
        >
          {{ loading ? 'Loading...' : 'Refresh' }}
        </button>
      </div>
    </div>

    <!-- User Selection -->
    <div class="bg-white p-4 rounded-lg border border-gray-200">
      <div class="flex items-center space-x-4">
        <div class="flex items-center space-x-2">
          <label class="text-sm font-medium text-gray-700">Select User:</label>
          <select 
            v-model="selectedUserId" 
            @change="onUserChange"
            class="px-3 py-1 border border-gray-300 rounded-md text-sm"
          >
            <option value="">Select a user...</option>
            <option v-for="user in users" :key="user.id" :value="user.id">
              {{ user.first_name }} {{ user.last_name }} ({{ user.username }})
            </option>
          </select>
        </div>
      </div>
    </div>

    <!-- Filters -->
    <div class="bg-white p-4 rounded-lg border border-gray-200">
      <div class="flex items-center space-x-4">
        <div class="flex items-center space-x-2">
          <label class="text-sm font-medium text-gray-700">Status:</label>
          <select v-model="statusFilter" @change="applyFilters" class="px-3 py-1 border border-gray-300 rounded-md text-sm">
            <option value="all">All</option>
            <option value="PENDING">Pending</option>
            <option value="IN_PROGRESS">In Progress</option>
            <option value="APPROVED">Approved</option>
            <option value="REJECTED">Rejected</option>
          </select>
        </div>
        <div class="flex items-center space-x-2">
          <label class="text-sm font-medium text-gray-700">Priority:</label>
          <select v-model="priorityFilter" @change="applyFilters" class="px-3 py-1 border border-gray-300 rounded-md text-sm">
            <option value="all">All</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
            <option value="URGENT">Urgent</option>
          </select>
        </div>
        <div class="flex items-center space-x-2">
          <label class="text-sm font-medium text-gray-700">Type:</label>
          <select v-model="typeFilter" @change="applyFilters" class="px-3 py-1 border border-gray-300 rounded-md text-sm">
            <option value="all">All</option>
            <option value="RFP">RFP</option>
            <option value="VENDOR">Vendor</option>
            <option value="CONTRACT">Contract</option>
          </select>
        </div>
      </div>
    </div>

    <!-- Approvals List -->
    <div class="bg-white rounded-lg border border-gray-200">
      <div class="px-6 py-4 border-b border-gray-200">
        <h2 class="text-lg font-semibold text-gray-900">
          {{ selectedUserId ? 'User RFP Approvals' : 'Select a user to view RFP approvals' }}
        </h2>
      </div>
      
      <!-- Loading state -->
      <div v-if="loading" class="px-6 py-12 text-center">
        <div class="text-gray-400 mb-4">
          <svg class="animate-spin mx-auto h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
          </svg>
        </div>
        <p class="text-gray-600">Loading approvals...</p>
      </div>


      <!-- Dynamic approval items -->
      <div v-else-if="filteredApprovals.length > 0" class="divide-y divide-gray-200">
        <div 
          v-for="approval in filteredApprovals" 
          :key="approval.stage_id"
          class="px-6 py-4 hover:bg-gray-50 transition-colors"
        >
          <div class="flex items-center justify-between">
            <div class="flex-1">
              <div class="flex items-center space-x-3">
                <div 
                  :class="getStatusColor(approval.stage_status)" 
                  class="w-2 h-2 rounded-full"
                ></div>
                <h3 class="text-sm font-medium text-gray-900">{{ approval.request_title }}</h3>
                <span 
                  :class="getStatusBadgeClass(approval.stage_status)"
                  class="px-2 py-1 text-xs font-medium rounded-full"
                >
                  {{ approval.stage_status }}
                </span>
              </div>
              <p class="text-sm text-gray-600 mt-1">{{ approval.request_description }}</p>
              <div class="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                <span>Stage: {{ approval.stage_name }}</span>
                <span>Priority: {{ approval.priority }}</span>
                <span>Type: {{ approval.business_object_type }}</span>
                <span v-if="approval.deadline_date">
                  Deadline: {{ formatDate(approval.deadline_date) }}
                </span>
              </div>
              <div class="flex items-center space-x-4 mt-1 text-xs text-gray-500">
                <span>Submitted: {{ formatDate(approval.submission_date) }}</span>
                <span>Department: {{ approval.requester_department }}</span>
                <span>Workflow: {{ approval.workflow_name }}</span>
              </div>
            </div>
            <div class="flex items-center space-x-2">
              <!-- Sequential Workflow Pending Indicator -->
              <div v-if="isSequentialWorkflow(approval) && isWaitingForPreviousStage(approval)" class="flex items-center space-x-1 text-xs text-gray-500">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                <span>Pending</span>
              </div>
              
              <!-- Only show Score Proposal button for proposal evaluations -->
              <button 
                v-if="isProposalEvaluation(approval)"
                @click="handleEvaluateProposal(approval)"
                class="px-3 py-1 text-sm bg-purple-100 text-purple-800 rounded-md hover:bg-purple-200 transition-colors"
              >
                Score Proposal
              </button>
              
              <!-- Show other buttons only if NOT a proposal evaluation -->
              <template v-else>
                <button 
                  v-if="(approval.stage_status?.toUpperCase() === 'PENDING' || approval.stage_status?.toUpperCase() === 'IN_PROGRESS') && !isRfpCreation(approval)"
                  @click="handleApprove(approval.stage_id)"
                  :disabled="processingStage === approval.stage_id"
                  class="px-3 py-1 text-sm bg-green-100 text-green-800 rounded-md hover:bg-green-200 transition-colors disabled:opacity-50"
                >
                  {{ processingStage === approval.stage_id ? 'Processing...' : 'Approve' }}
                </button>
                <button 
                  v-if="(approval.stage_status?.toUpperCase() === 'PENDING' || approval.stage_status?.toUpperCase() === 'IN_PROGRESS') && !isRfpCreation(approval)"
                  @click="handleReject(approval.stage_id)"
                  :disabled="processingStage === approval.stage_id"
                  class="px-3 py-1 text-sm bg-red-100 text-red-800 rounded-md hover:bg-red-200 transition-colors disabled:opacity-50"
                >
                  {{ processingStage === approval.stage_id ? 'Processing...' : 'Reject' }}
                </button>
                <button 
                  @click="handleViewDetails(approval)"
                  class="px-3 py-1 text-sm bg-blue-100 text-blue-800 rounded-md hover:bg-blue-200 transition-colors"
                >
                  Review & Decide
                </button>
              </template>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty state -->
      <div v-else-if="selectedUserId && !loading" class="px-6 py-12 text-center">
        <div class="text-gray-400 mb-4">
          <svg class="mx-auto h-12 w-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
          </svg>
        </div>
        <h3 class="text-lg font-medium text-gray-900 mb-2">No RFP approvals found</h3>
        <p class="text-gray-600">
          {{ filteredApprovals.length === 0 && approvals.length > 0 
            ? 'No RFP approvals match the current filters.' 
            : 'No RFP approval requests are assigned to this user.' 
          }}
        </p>
      </div>

      <!-- No user selected state -->
      <div v-else-if="!selectedUserId" class="px-6 py-12 text-center">
        <div class="text-gray-400 mb-4">
          <svg class="mx-auto h-12 w-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
          </svg>
        </div>
        <h3 class="text-lg font-medium text-gray-900 mb-2">Select a user</h3>
        <p class="text-gray-600">Please select a user from the dropdown above to view their RFP approval requests.</p>
      </div>
    </div>

    <!-- Recent Activity -->
    <div class="bg-white rounded-lg border border-gray-200">
      <div class="px-6 py-4 border-b border-gray-200">
        <h2 class="text-lg font-semibold text-gray-900">Recent Activity</h2>
      </div>
      <div class="px-6 py-4">
        <div v-if="recentActivity.length > 0" class="space-y-3">
          <div 
            v-for="activity in recentActivity" 
            :key="activity.stage_id"
            class="flex items-center space-x-3"
          >
            <div 
              :class="getStatusColor(activity.stage_status)" 
              class="w-2 h-2 rounded-full"
            ></div>
            <div class="flex-1">
              <p class="text-sm text-gray-900">
                {{ activity.stage_status === 'APPROVED' ? 'Approved' : 
                   activity.stage_status === 'REJECTED' ? 'Rejected' : 
                   activity.stage_status }} {{ activity.request_title }}
              </p>
              <p class="text-xs text-gray-500">
                {{ formatRelativeTime(activity.completed_at || activity.updated_at) }}
              </p>
            </div>
          </div>
        </div>
        <div v-else class="text-center py-4">
          <p class="text-sm text-gray-500">No recent activity</p>
        </div>
      </div>
    </div>

    <!-- Details Modal -->
    <div v-if="showDetailsModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-gray-900">Approval Details</h3>
          <button 
            @click="showDetailsModal = false"
            class="text-gray-400 hover:text-gray-600"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>
        
        <div v-if="selectedApproval" class="space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="text-sm font-medium text-gray-700">Title:</label>
              <p class="text-sm text-gray-900">{{ selectedApproval.request_title }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-700">Status:</label>
              <span 
                :class="getStatusBadgeClass(selectedApproval.stage_status)"
                class="px-2 py-1 text-xs font-medium rounded-full"
              >
                {{ selectedApproval.stage_status }}
              </span>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-700">Stage:</label>
              <p class="text-sm text-gray-900">{{ selectedApproval.stage_name }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-700">Priority:</label>
              <p class="text-sm text-gray-900">{{ selectedApproval.priority }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-700">Type:</label>
              <p class="text-sm text-gray-900">{{ selectedApproval.business_object_type }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-700">Department:</label>
              <p class="text-sm text-gray-900">{{ selectedApproval.requester_department }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-700">Workflow:</label>
              <p class="text-sm text-gray-900">{{ selectedApproval.workflow_name }}</p>
            </div>
            <div>
              <label class="text-sm font-medium text-gray-700">Submitted:</label>
              <p class="text-sm text-gray-900">{{ formatDate(selectedApproval.submission_date) }}</p>
            </div>
            <div v-if="selectedApproval.deadline_date">
              <label class="text-sm font-medium text-gray-700">Deadline:</label>
              <p class="text-sm text-gray-900">{{ formatDate(selectedApproval.deadline_date) }}</p>
            </div>
          </div>
          
          <div>
            <label class="text-sm font-medium text-gray-700">Description:</label>
            <p class="text-sm text-gray-900 mt-1">{{ selectedApproval.request_description }}</p>
          </div>
          
          <div class="flex justify-end space-x-3 pt-4 border-t">
            <button 
              @click="showDetailsModal = false"
              class="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors"
            >
              Close
            </button>
            
            <!-- Sequential Workflow Pending Indicator -->
            <div v-if="isSequentialWorkflow(selectedApproval) && isWaitingForPreviousStage(selectedApproval)" class="flex items-center space-x-1 text-sm text-gray-500 px-3 py-2">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
              <span>Pending</span>
            </div>
            
            <!-- Only show Score Proposal button for proposal evaluations -->
            <button 
              v-if="isProposalEvaluation(selectedApproval)"
              @click="handleEvaluateProposal(selectedApproval); showDetailsModal = false"
              class="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors"
            >
              Score Proposal
            </button>
            
            <!-- Show other buttons only if NOT a proposal evaluation -->
            <template v-else>
              <button 
                v-if="(selectedApproval.stage_status?.toUpperCase() === 'PENDING' || selectedApproval.stage_status?.toUpperCase() === 'IN_PROGRESS') && !isRfpCreation(selectedApproval)"
                @click="handleApprove(selectedApproval.stage_id); showDetailsModal = false"
                :disabled="processingStage === selectedApproval.stage_id"
                class="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors disabled:opacity-50"
              >
                {{ processingStage === selectedApproval.stage_id ? 'Processing...' : 'Approve' }}
              </button>
              <button 
                v-if="(selectedApproval.stage_status?.toUpperCase() === 'PENDING' || selectedApproval.stage_status?.toUpperCase() === 'IN_PROGRESS') && !isRfpCreation(selectedApproval)"
                @click="handleReject(selectedApproval.stage_id); showDetailsModal = false"
                :disabled="processingStage === selectedApproval.stage_id"
                class="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors disabled:opacity-50"
              >
                {{ processingStage === selectedApproval.stage_id ? 'Processing...' : 'Reject' }}
              </button>
            </template>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Popup Modal -->
  <PopupModal />
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { API_CONFIG, API_ENDPOINTS, buildApiUrl, apiCall } from '@/config/api.js'
import { useRfpApi } from '@/composables/useRfpApi'
import PopupModal from '@/popup/PopupModal.vue'
import { PopupService } from '@/popup/popupService'
import { useNotifications } from '@/composables/useNotifications'
import loggingService from '@/services/loggingService'

// Router
const router = useRouter()

// Reactive data
const { showSuccess, showError, showWarning, showInfo } = useNotifications()

// Get authenticated headers for axios requests
const { getAuthHeaders } = useRfpApi()

const approvals = ref([])
const users = ref([])
const loading = ref(false)
const processingStage = ref('')
const selectedUserId = ref('')
const statusFilter = ref('all')
const priorityFilter = ref('all')
const typeFilter = ref('all')
const showDetailsModal = ref(false)
const selectedApproval = ref(null)

// Computed properties
const filteredApprovals = computed(() => {
  let filtered = approvals.value

  // Filter to show only RFP business object type
  filtered = filtered.filter(approval => approval.business_object_type === 'RFP')

  if (statusFilter.value !== 'all') {
    filtered = filtered.filter(approval => approval.stage_status === statusFilter.value)
  }

  if (priorityFilter.value !== 'all') {
    filtered = filtered.filter(approval => approval.priority === priorityFilter.value)
  }

  if (typeFilter.value !== 'all') {
    filtered = filtered.filter(approval => approval.business_object_type === typeFilter.value)
  }

  return filtered
})

const recentActivity = computed(() => {
  // Get completed approvals (approved or rejected) and sort by completion date
  return approvals.value
    .filter(approval => approval.business_object_type === 'RFP')
    .filter(approval => approval.stage_status === 'APPROVED' || approval.stage_status === 'REJECTED')
    .sort((a, b) => {
      const dateA = new Date(a.completed_at || a.updated_at)
      const dateB = new Date(b.completed_at || b.updated_at)
      return dateB.getTime() - dateA.getTime()
    })
    .slice(0, 5) // Show only the 5 most recent activities
})

const hasSequentialWorkflows = computed(() => {
  return approvals.value
    .filter(approval => approval.business_object_type === 'RFP')
    .some(approval => 
      approval.workflow_type === 'MULTI_LEVEL' || 
      approval.workflow_type === 'SEQUENTIAL' ||
      approval.workflow_name?.toLowerCase().includes('multi level') ||
      approval.workflow_name?.toLowerCase().includes('sequential')
    )
})

const isSequentialWorkflow = (approval) => {
  return approval.workflow_type === 'MULTI_LEVEL' || 
         approval.workflow_type === 'SEQUENTIAL' ||
         approval.workflow_name?.toLowerCase().includes('multi level') ||
         approval.workflow_name?.toLowerCase().includes('sequential')
}

const isWaitingForPreviousStage = (approval) => {
  // This would need to be implemented based on your specific logic
  // For now, we'll show pending for stages that are not the first stage
  // and are in PENDING status (meaning they're waiting for previous stages)
  return approval.stage_order > 1 && approval.stage_status === 'PENDING'
}

// Methods
const fetchUsers = async () => {
  try {
    const url = buildApiUrl(API_ENDPOINTS.RFP_APPROVAL.USERS)
    console.log('🔍 Fetching users from URL:', url)
    
    // Try direct fetch first
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
      },
    })
    
    console.log('📡 Response status:', response.status)
    console.log('📡 Response headers:', Object.fromEntries(response.headers.entries()))
    
    // Handle 403 Forbidden - redirect to access denied
    if (response.status === 403) {
      const errorData = await response.json().catch(() => ({}))
      const errorMessage = errorData?.error || errorData?.message || 'You do not have permission to access this resource.'
      sessionStorage.setItem('access_denied_error', JSON.stringify({
        message: errorMessage,
        code: '403',
        timestamp: new Date().toISOString(),
        path: window.location.pathname
      }))
      console.log('🔄 Redirecting to /access-denied page...')
      window.location.href = '/access-denied'
      // Return a never-resolving promise to stop execution
      return new Promise(() => {})
    }
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    const data = await response.json()
    console.log('✅ Users fetched successfully:', data)
    users.value = data
  } catch (error) {
    console.error('❌ Error fetching users:', error)
    console.log('🔄 Falling back to mock data')
    // Fallback to mock data if API fails
    users.value = [
      {
        id: '1',
        username: 'admin',
        first_name: 'Admin',
        last_name: 'User',
        email: 'admin@company.com',
        role: 'Administrator',
        department: 'IT',
        is_active: true
      },
      {
        id: '2',
        username: 'manager',
        first_name: 'Manager',
        last_name: 'User',
        email: 'manager@company.com',
        role: 'Manager',
        department: 'Operations',
        is_active: true
      },
      {
        id: '3',
        username: 'reviewer',
        first_name: 'Reviewer',
        last_name: 'User',
        email: 'reviewer@company.com',
        role: 'Reviewer',
        department: 'Finance',
        is_active: true
      }
    ]
  }
}

const fetchApprovals = async () => {
  if (!selectedUserId.value) {
    approvals.value = []
    return
  }

  loading.value = true
  try {
    const url = buildApiUrl(`${API_ENDPOINTS.RFP_APPROVAL.USER_APPROVALS}?user_id=${selectedUserId.value}`)
    console.log('🔍 Fetching approvals from URL:', url)
    const data = await apiCall(url)
    console.log('✅ Approvals fetched successfully:', data)
    
    // Filter approvals based on sequential workflow rules
    const filteredData = await filterSequentialApprovals(data)
    
    // Force Vue reactivity by creating a new array
    approvals.value = [...filteredData]
  } catch (error) {
    console.error('❌ Error fetching approvals:', error)
    // Show user-friendly error message
    PopupService.error('Failed to fetch approvals. Please check if the backend server is running on port 8000.', 'Fetch Failed')
    approvals.value = []
  } finally {
    loading.value = false
  }
}

const filterSequentialApprovals = async (approvals) => {
  try {
    // Group approvals by approval_id to check sequential dependencies
    const approvalGroups = {}
    
    for (const approval of approvals) {
      if (!approvalGroups[approval.approval_id]) {
        approvalGroups[approval.approval_id] = []
      }
      approvalGroups[approval.approval_id].push(approval)
    }
    
    const filteredApprovals = []
    
    for (const [approvalId, groupApprovals] of Object.entries(approvalGroups)) {
      // Sort by stage_order
      const sortedApprovals = groupApprovals.sort((a, b) => a.stage_order - b.stage_order)
      
      // Check if this is a multi-level/sequential workflow
      const isMultiLevel = sortedApprovals.some(approval => 
        approval.workflow_type === 'MULTI_LEVEL' || 
        approval.workflow_type === 'SEQUENTIAL' ||
        approval.workflow_name?.toLowerCase().includes('multi level') ||
        approval.workflow_name?.toLowerCase().includes('sequential')
      )
      
      if (isMultiLevel) {
        console.log(`🔍 Sequential workflow detected for approval ${approvalId}`)
        
        // Find the first stage that is not approved
        let firstUnapprovedIndex = -1
        for (let i = 0; i < sortedApprovals.length; i++) {
          if (sortedApprovals[i].stage_status !== 'APPROVED') {
            firstUnapprovedIndex = i
            break
          }
        }
        
        // Only show the first unapproved stage (or all if all are approved)
        if (firstUnapprovedIndex >= 0) {
          // Show only the first unapproved stage
          const availableStage = sortedApprovals[firstUnapprovedIndex]
          filteredApprovals.push(availableStage)
          console.log(`✅ Showing stage ${availableStage.stage_name} (order: ${availableStage.stage_order}) for approval ${approvalId}`)
        } else {
          // All stages are approved, show the last one
          const lastStage = sortedApprovals[sortedApprovals.length - 1]
          filteredApprovals.push(lastStage)
          console.log(`✅ All stages approved, showing last stage ${lastStage.stage_name} for approval ${approvalId}`)
        }
      } else {
        // Non-sequential workflow, show all stages
        filteredApprovals.push(...sortedApprovals)
        console.log(`✅ Non-sequential workflow, showing all stages for approval ${approvalId}`)
      }
    }
    
    return filteredApprovals
    
  } catch (error) {
    console.error('❌ Error filtering sequential approvals:', error)
    // Return original data if filtering fails
    return approvals
  }
}

const onUserChange = () => {
  if (selectedUserId.value) {
    fetchApprovals()
  } else {
    approvals.value = []
  }
}

const applyFilters = () => {
  // Filters are applied automatically through computed property
}

const handleApprove = async (stageId: string) => {
  processingStage.value = stageId
  try {
    const url = buildApiUrl(API_ENDPOINTS.RFP_APPROVAL.UPDATE_STAGE_STATUS)
    await apiCall(url, {
      method: 'POST',
      body: JSON.stringify({
        stage_id: stageId,
        status: 'APPROVE',
        comments: 'Approved by user'
      })
    })

    // Refresh the approvals list
    await fetchApprovals()
    console.log('Approval successful')
  } catch (error) {
    console.error('Error approving:', error)
    PopupService.error('Failed to approve. Please try again.', 'Approval Failed')
  } finally {
    processingStage.value = ''
  }
}

const handleReject = async (stageId: string) => {
  PopupService.comment(
    'Please provide a reason for rejection:',
    'Rejection Reason',
    async (reason) => {
      if (!reason) return
      await performReject(stageId, reason)
    }
  )
}

const performReject = async (stageId: string, reason: string) => {

  processingStage.value = stageId
  try {
    const url = buildApiUrl(API_ENDPOINTS.RFP_APPROVAL.UPDATE_STAGE_STATUS)
    await apiCall(url, {
      method: 'POST',
      body: JSON.stringify({
        stage_id: stageId,
        status: 'REJECT',
        comments: reason
      })
    })

    // Refresh the approvals list
    await fetchApprovals()
    console.log('Rejection successful')
  } catch (error) {
    console.error('Error rejecting:', error)
    PopupService.error('Failed to reject. Please try again.', 'Rejection Failed')
  } finally {
    processingStage.value = ''
  }
}

const handleViewDetails = (approval: any) => {
  try {
    // Vue Router Navigation: Use router.push for proper SPA navigation
    const queryParams = {
      userId: selectedUserId.value,
      stageId: approval.stage_id,
      approvalId: approval.approval_id,
      workflowId: approval.approval_id
    }
    
    console.log('Navigating to StageReviewer with params:', queryParams)
    
    // Navigate to the stage-reviewer page using Vue Router
    router.push({
      name: 'StageReviewer',
      query: queryParams
    })
    
  } catch (error) {
    console.error('Error in handleViewDetails:', error)
    // Fallback to modal
    selectedApproval.value = approval
    showDetailsModal.value = true
  }
}

const handleEvaluateProposal = async (approval: any) => {
  try {
    console.log('🔍 DEBUG: Starting proposal evaluation process')
    console.log('🔍 DEBUG: Full approval object:', JSON.stringify(approval, null, 2))
    
    // Determine the type of evaluation based on business_object_type, workflow name and stage name
    const businessObjectType = approval.business_object_type?.toLowerCase() || ''
    const workflowName = approval.workflow_name?.toLowerCase() || ''
    const stageName = approval.stage_name?.toLowerCase() || ''
    const requestTitle = approval.request_title?.toLowerCase() || ''
    
    console.log('🔍 DEBUG: Business Object Type:', businessObjectType)
    console.log('🔍 DEBUG: Workflow name:', workflowName)
    console.log('🔍 DEBUG: Stage name:', stageName)
    console.log('🔍 DEBUG: Request title:', requestTitle)
    
    // Check if this is a committee evaluation
    const isCommitteeEvaluation = businessObjectType === 'committee evaluation' ||
                                 workflowName.includes('committee evaluation') ||
                                 stageName.includes('committee evaluation') ||
                                 requestTitle.includes('committee evaluation')
    
    if (isCommitteeEvaluation) {
      console.log('🎯 DEBUG: This is a committee evaluation approval')
      
      // Extract RFP ID from approval data
      let rfpId = null
      
      // First, try to get RFP ID from request_data
      if (approval.request_data) {
        try {
          const requestData = typeof approval.request_data === 'string' 
            ? JSON.parse(approval.request_data) 
            : approval.request_data
          
          console.log('🔍 DEBUG: Parsed request_data:', requestData)
          
          // Try to get RFP ID from request data
          rfpId = requestData.rfp_id || requestData.rfpId
          
          // If request_data is an array, get RFP ID from first item
          if (!rfpId && Array.isArray(requestData) && requestData.length > 0) {
            rfpId = requestData[0].rfp_id || requestData[0].rfpId
          }
          
          // Convert to string if it's a number
          if (rfpId && typeof rfpId === 'number') {
            rfpId = rfpId.toString()
          }
        } catch (e) {
          console.log('Could not parse request_data for RFP ID:', e)
        }
      }
      
      // If no RFP ID found in request_data, try to get it from the approval request directly
      if (!rfpId && approval.approval_id) {
        try {
          console.log('🔍 DEBUG: Fetching approval request data for RFP ID...')
          const approvalResponse = await fetch(`https://grc-tprm.vardaands.com/api/tprm/approval/requests/`, {
            method: 'GET',
            headers: getAuthHeaders()
          })
          if (approvalResponse.ok) {
            const approvalData = await approvalResponse.json()
            const matchingApproval = approvalData.find(a => a.approval_id === approval.approval_id)
            
            if (matchingApproval && matchingApproval.request_data) {
              const requestData = typeof matchingApproval.request_data === 'string' 
                ? JSON.parse(matchingApproval.request_data) 
                : matchingApproval.request_data
              
              rfpId = requestData.rfp_id || requestData.rfpId
              console.log('✅ DEBUG: Found RFP ID from approval request:', rfpId)
            }
          }
        } catch (e) {
          console.log('Could not fetch approval request data:', e)
        }
      }
      
      if (!rfpId) {
        console.log('❌ DEBUG: No RFP ID found for committee evaluation')
        PopupService.error('❌ No RFP data found for committee evaluation!\n\nThis approval does not contain the necessary RFP information.', 'No RFP Data')
        return
      }
      
      console.log('✅ DEBUG: Found RFP ID for committee evaluation:', rfpId)
      
      // Navigate to CommitteeEvaluation
      router.push({
        name: 'CommitteeEvaluation',
        query: {
          rfp_id: rfpId,
          evaluator_id: selectedUserId.value,
          approval_id: approval.approval_id,
          stage_id: approval.stage_id
        }
      })
      return
    }
    
    // For regular proposal evaluation, extract response_id
    let responseId = null
    
    // Try to get response_id from different possible locations
    if (approval.response_id) {
      responseId = approval.response_id
    } else if (approval.request_data) {
      try {
        const requestData = typeof approval.request_data === 'string' 
          ? JSON.parse(approval.request_data) 
          : approval.request_data
        console.log('🔍 DEBUG: Parsed request_data:', requestData)
        
        // Handle case where request_data is an array (proposal evaluation)
        if (Array.isArray(requestData) && requestData.length > 0) {
          console.log('🔍 DEBUG: Processing array format request_data')
          const firstProposal = requestData[0]
          if (firstProposal && firstProposal.response_id) {
            responseId = firstProposal.response_id
            console.log('✅ DEBUG: Found response_id in array:', responseId)
          }
        } else if (typeof requestData === 'object' && requestData !== null) {
          console.log('🔍 DEBUG: Processing object format request_data')
          // Try multiple possible field names for the proposal/response ID
          responseId = requestData.response_id || 
                      requestData.proposal_id || 
                      requestData.rfp_response_id ||
                      requestData.id ||
                      requestData.proposalId ||
                      requestData.responseId
          console.log('🔍 DEBUG: Object response_id search result:', responseId)
        }
      } catch (e) {
        console.log('Could not parse request_data:', e)
      }
    }
    
    // If still no response_id found, try to look it up from the backend
    if (!responseId) {
      console.log('❌ DEBUG: No response_id found in approval data. Trying backend lookup...')
      
       try {
         // Try to get proposal ID from backend using the correct approval_id
         const response = await fetch(`https://grc-tprm.vardaands.com/api/tprm/rfp-approval/get-proposal-id/${approval.approval_id}/`, {
           method: 'GET',
           headers: getAuthHeaders()
         })
         
         if (response.ok) {
           const data = await response.json()
           console.log('🔍 DEBUG: Backend response data:', data)
           responseId = data.proposal_id
           console.log('✅ DEBUG: Found proposal ID from backend:', responseId)
         } else {
           console.log('❌ DEBUG: Backend lookup failed - no valid response_id found')
           PopupService.error('❌ No proposal data found!\n\nThis approval does not contain vendor proposal information.\nPlease select an approval that was created for proposal evaluation.', 'No Proposal Data')
           return
         }
       } catch (error) {
         console.log('❌ DEBUG: Backend lookup error:', error)
         PopupService.error('❌ Failed to retrieve proposal data from backend.\n\nPlease try again or contact support if the issue persists.', 'Retrieval Failed')
         return
       }
    }
    
    if (!responseId) {
      console.log('❌ DEBUG: No response_id found after all attempts')
      PopupService.error('❌ No proposal data found!\n\nThis approval does not contain vendor proposal information.\nPlease select an approval that was created for proposal evaluation.', 'No Proposal Data')
      return
    }
    
    console.log('✅ DEBUG: Final response_id to use:', responseId)
    
    // Navigate to ProposalEvaluation with response_id
    router.push({
      name: 'ProposalEvaluation',
      query: {
        response_id: responseId,
        userId: selectedUserId.value,
        stageId: approval.stage_id,
        approvalId: approval.approval_id
      }
    })
    
  } catch (error) {
    console.error('Error navigating to proposal evaluation:', error)
    PopupService.error('Failed to navigate to proposal evaluation. Please try again.', 'Navigation Failed')
  }
}

const isRfpCreation = (approval: any) => {
  // Check if this approval is for RFP creation
  const businessType = approval.business_object_type?.toLowerCase()
  const workflowName = approval.workflow_name?.toLowerCase()
  const requestTitle = approval.request_title?.toLowerCase()
  
  // Check for RFP creation indicators
  const hasRfpCreationWorkflow = workflowName?.includes('rfp creation') || 
                                  workflowName?.includes('rfp approval')
  const hasRfpCreationTitle = requestTitle?.includes('rfp approval') || 
                              requestTitle?.includes('rfp creation')
  const hasPolicyBusinessType = businessType === 'policy'
  const hasRfpBusinessType = businessType === 'rfp'
  
  return hasRfpCreationWorkflow || hasRfpCreationTitle || hasPolicyBusinessType || hasRfpBusinessType
}

const isProposalEvaluation = (approval: any) => {
  // Check if this approval is for proposal evaluation (including committee evaluation)
  const businessType = approval.business_object_type?.toLowerCase()
  const stageName = approval.stage_name?.toLowerCase()
  const requestTitle = approval.request_title?.toLowerCase()
  const workflowName = approval.workflow_name?.toLowerCase()
  
  // Check for committee evaluation indicators (highest priority)
  const isCommitteeEvaluation = businessType === 'committee evaluation' ||
                               workflowName?.includes('committee evaluation') ||
                               stageName?.includes('committee evaluation') ||
                               requestTitle?.includes('committee evaluation')
  
  // Check for regular proposal evaluation indicators
  const hasProposalInTitle = requestTitle?.includes('proposal evaluation') || 
                            requestTitle?.includes('proposal -') ||
                            requestTitle?.includes('evaluation')
  const hasEvaluationWorkflow = workflowName?.includes('proposal evaluation') ||
                               workflowName?.includes('evaluation workflow')
  const hasContractBusinessType = businessType === 'contract' || businessType === 'evaluation'
  const hasCommitteeStage = stageName?.includes('evaluation') ||
                           stageName?.includes('technical') ||
                           stageName?.includes('commercial')
  
  // Check if request_data contains actual proposal data (array format)
  let hasProposalData = false
  let hasRfpData = false
  
  if (approval.request_data) {
    try {
      const requestData = typeof approval.request_data === 'string' 
        ? JSON.parse(approval.request_data) 
        : approval.request_data
      
      // Check if it's an array with proposal data
      if (Array.isArray(requestData) && requestData.length > 0) {
        const firstItem = requestData[0]
        hasProposalData = firstItem && (firstItem.response_id || firstItem.vendor_name)
      }
      
      // Check for RFP data (for committee evaluation)
      if (typeof requestData === 'object' && requestData !== null) {
        hasRfpData = requestData.rfp_id || requestData.rfpId
      }
      
      // If request_data is an array, check for RFP data in first item
      if (!hasRfpData && Array.isArray(requestData) && requestData.length > 0) {
        hasRfpData = requestData[0].rfp_id || requestData[0].rfpId
      }
    } catch (e) {
      // Ignore parsing errors
    }
  }
  
  console.log('🔍 DEBUG: isProposalEvaluation check for approval:', {
    approval_id: approval.approval_id,
    businessType,
    stageName,
    requestTitle,
    workflowName,
    isCommitteeEvaluation,
    hasProposalInTitle,
    hasEvaluationWorkflow,
    hasContractBusinessType,
    hasCommitteeStage,
    hasProposalData,
    hasRfpData,
    result: isCommitteeEvaluation || ((hasProposalInTitle || hasEvaluationWorkflow || hasContractBusinessType || hasCommitteeStage) && (hasProposalData || hasRfpData))
  })
  
  // Show evaluation button if it's committee evaluation OR regular proposal evaluation with relevant data
  return isCommitteeEvaluation || ((hasProposalInTitle || hasEvaluationWorkflow || hasContractBusinessType || hasCommitteeStage) && (hasProposalData || hasRfpData))
}

const getStatusColor = (status: string) => {
  // Convert to uppercase for case-insensitive comparison
  const statusUpper = status?.toUpperCase() || '';
  
  switch (statusUpper) {
    case 'PENDING':
      return 'bg-yellow-500'
    case 'IN_PROGRESS':
      return 'bg-blue-500'
    case 'APPROVED':
      return 'bg-green-500'
    case 'REJECTED':
      return 'bg-red-500'
    case 'EXPIRED':
      return 'bg-gray-500'
    default:
      return 'bg-gray-400'
  }
}

const getStatusBadgeClass = (status: string) => {
  // Convert to uppercase for case-insensitive comparison
  const statusUpper = status?.toUpperCase() || '';
  
  switch (statusUpper) {
    case 'PENDING':
      return 'bg-yellow-100 text-yellow-800'
    case 'IN_PROGRESS':
      return 'bg-blue-100 text-blue-800'
    case 'APPROVED':
      return 'bg-green-100 text-green-800'
    case 'REJECTED':
      return 'bg-red-100 text-red-800'
    case 'EXPIRED':
      return 'bg-gray-100 text-gray-800'
    default:
      return 'bg-gray-100 text-gray-800'
  }
}

const formatDate = (dateString: string) => {
  if (!dateString) return 'N/A'
  try {
    const date = new Date(dateString)
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString()
  } catch (error) {
    return 'Invalid Date'
  }
}

const formatRelativeTime = (dateString: string) => {
  if (!dateString) return 'N/A'
  try {
    const date = new Date(dateString)
    const now = new Date()
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000)
    
    if (diffInSeconds < 60) {
      return 'Just now'
    } else if (diffInSeconds < 3600) {
      const minutes = Math.floor(diffInSeconds / 60)
      return `${minutes} minute${minutes > 1 ? 's' : ''} ago`
    } else if (diffInSeconds < 86400) {
      const hours = Math.floor(diffInSeconds / 3600)
      return `${hours} hour${hours > 1 ? 's' : ''} ago`
    } else {
      const days = Math.floor(diffInSeconds / 86400)
      return `${days} day${days > 1 ? 's' : ''} ago`
    }
  } catch (error) {
    return 'Invalid Date'
  }
}

// Watchers - removed debug watchers

// Lifecycle
onMounted(async () => {
  await loggingService.logPageView('RFP', 'My Approvals')
  console.log('🚀 MyApprovals component mounted')
  console.log('🔧 API Config:', API_CONFIG)
  console.log('🔧 API Endpoints:', API_ENDPOINTS)
  
  // Test API connectivity first
  try {
    console.log('🧪 Testing API connectivity...')
    const testUrl = 'https://grc-tprm.vardaands.com/api/tprm/rfp-approval/users/'
    console.log('🧪 Testing URL:', testUrl)
    const testResponse = await fetch(testUrl, {
      method: 'GET',
      headers: getAuthHeaders()
    })
    console.log('🧪 Test response status:', testResponse.status)
    console.log('🧪 Test response headers:', Object.fromEntries(testResponse.headers.entries()))
    
    if (testResponse.ok) {
      const testData = await testResponse.json()
      console.log('🧪 Test data received:', testData)
      console.log('🧪 Test data length:', testData.length)
    } else {
      console.error('🧪 Test failed with status:', testResponse.status)
    }
  } catch (testError) {
    console.error('🧪 Test connectivity failed:', testError)
  }
  
  console.log('🔄 Calling fetchUsers...')
  await fetchUsers()
  console.log('✅ fetchUsers completed, users.value:', users.value)
})
</script>

<style scoped>
/* Component-specific styles if needed */
</style>
