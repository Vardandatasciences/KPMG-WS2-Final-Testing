<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Assignee Dashboard</h1>
        <p class="text-gray-600 mt-1">Review assigned stages and make final decisions on approval requests</p>
      </div>
      <div class="flex items-center space-x-4">
        <div class="flex items-center space-x-2">
          <label class="text-sm font-medium text-gray-700">Current User:</label>
          <select 
            v-model="currentUserId" 
            class="px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="1">User 1 (Admin)</option>
            <option value="2">User 2 (Manager)</option>
            <option value="3">User 3 (Reviewer)</option>
            <option value="4">User 4 (Sarah Wilson)</option>
            <option value="5">User 5 (David Brown)</option>
          </select>
        </div>
      </div>
    </div>

    <!-- Approval Request Info -->
    <div v-if="approvalId && approvalRequest" class="bg-white p-6 rounded-lg border border-gray-200">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-xl font-semibold text-gray-900">Approval Request Details</h2>
        <span class="text-sm font-bold text-blue-600">ID: {{ approvalId }}</span>
      </div>
      
      <!-- Request Information -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <div class="space-y-3">
          <div>
            <span class="text-sm font-medium text-gray-700">Request Title:</span>
            <p class="text-sm text-gray-900 font-medium">{{ approvalRequest.request_title || 'No title' }}</p>
          </div>
          <div>
            <span class="text-sm font-medium text-gray-700">Requester:</span>
            <p class="text-sm text-gray-900">{{ approvalRequest.requester_id || 'Unknown' }}</p>
          </div>
          <div>
            <span class="text-sm font-medium text-gray-700">Department:</span>
            <p class="text-sm text-gray-900">{{ approvalRequest.requester_department || 'Unknown' }}</p>
          </div>
          <div>
            <span class="text-sm font-medium text-gray-700">Priority:</span>
            <span 
              :class="getPriorityBadgeClass(approvalRequest.priority)"
              class="px-2 py-1 text-xs font-medium rounded-full"
            >
              {{ approvalRequest.priority || 'MEDIUM' }}
            </span>
          </div>
        </div>
        <div class="space-y-3">
          <div>
            <span class="text-sm font-medium text-gray-700">Workflow:</span>
            <p class="text-sm text-gray-900">{{ approvalRequest.workflow_name || 'Default Workflow' }}</p>
          </div>
          <div>
            <span class="text-sm font-medium text-gray-700">Workflow Type:</span>
            <p class="text-sm text-gray-900">{{ approvalRequest.workflow_type || 'SEQUENTIAL' }}</p>
          </div>
          <div>
            <span class="text-sm font-medium text-gray-700">Overall Status:</span>
            <span 
              :class="getStatusBadgeClass(approvalRequest.overall_status)"
              class="px-2 py-1 text-xs font-medium rounded-full"
            >
              {{ approvalRequest.overall_status || 'PENDING' }}
            </span>
          </div>
          <div>
            <span class="text-sm font-medium text-gray-700">Created:</span>
            <p class="text-sm text-gray-900">{{ formatDate(approvalRequest.created_at) }}</p>
          </div>
        </div>
      </div>

      <!-- Request Description -->
      <div class="mb-6">
        <span class="text-sm font-medium text-gray-700">Description:</span>
        <p class="text-sm text-gray-900 bg-gray-50 p-3 rounded-md mt-1">
          {{ approvalRequest.request_description || 'No description provided' }}
        </p>
              </div>

              <!-- Request Data -->
      <div v-if="approvalRequest.request_data" class="mb-6">
        <h4 class="text-sm font-medium text-gray-700 mb-3">Request Details</h4>
        <div class="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <div v-if="isValidJson(approvalRequest.request_data)" class="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div 
              v-for="(value, key) in parsedRequestData" 
              :key="key"
              class="bg-white border border-gray-200 rounded-lg p-3"
            >
              <div class="flex items-center mb-2">
                <span class="text-sm font-semibold text-gray-700 capitalize">
                  {{ formatKeyName(key) }}
                </span>
              </div>

              <!-- Simple values -->
              <div v-if="typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean'" 
                   class="text-sm text-gray-900">
                {{ formatValue(value) }}
              </div>

              <!-- Arrays (like criteria) -->
              <div v-else-if="Array.isArray(value)" class="text-sm text-gray-900">
                <div v-if="value.length === 0" class="text-gray-500 italic">No items</div>
                <div v-else class="space-y-2">
                  <div v-for="(item, index) in value" :key="index" 
                       class="border border-gray-200 rounded p-2 bg-gray-50">
                    <div class="flex items-center justify-between mb-1">
                      <span class="text-xs font-medium text-blue-600">Item {{ index + 1 }}</span>
                      <span class="text-xs text-gray-500">{{ Object.keys(item).length }} fields</span>
                      </div>
                    <div v-if="typeof item === 'object'" class="space-y-1">
                      <div v-for="(subValue, subKey) in item" :key="subKey" 
                           class="flex justify-between text-xs">
                        <span class="font-medium text-gray-600">{{ formatKeyName(subKey) }}:</span>
                        <span class="text-gray-900 truncate ml-2">{{ formatValue(subValue) }}</span>
                      </div>
                    </div>
                    <div v-else class="text-xs text-gray-900">{{ item }}</div>
                  </div>
                </div>
              </div>

              <!-- Objects -->
              <div v-else-if="typeof value === 'object'" class="text-sm text-gray-900">
                <div class="space-y-1">
                  <div v-for="(subValue, subKey) in value" :key="subKey" 
                       class="flex justify-between text-xs">
                    <span class="font-medium text-gray-600">{{ formatKeyName(subKey) }}:</span>
                    <span class="text-gray-900 truncate ml-2">{{ formatValue(subValue) }}</span>
                  </div>
                   </div>
              </div>

              <!-- Fallback -->
              <div v-else class="text-sm text-gray-900">{{ value }}</div>
            </div>
          </div>
          <div v-else class="text-sm text-gray-600 italic">
            <p>Raw data format:</p>
            <pre class="mt-2 p-3 bg-white border border-gray-200 rounded text-xs overflow-x-auto max-h-40">{{ approvalRequest.request_data_display }}</pre>
          </div>
        </div>
                  </div>

      <!-- Timeline Information -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
        <div class="bg-white border border-gray-200 rounded-lg p-3">
          <span class="font-medium text-gray-700">Submission Date:</span>
          <p class="text-gray-900 mt-1">{{ formatDate(approvalRequest.submission_date) }}</p>
        </div>
        <div class="bg-white border border-gray-200 rounded-lg p-3">
          <span class="font-medium text-gray-700">Expiry Date:</span>
          <p class="text-gray-900 mt-1">{{ formatDate(approvalRequest.expiry_date) }}</p>
        </div>
        <div class="bg-white border border-gray-200 rounded-lg p-3">
          <span class="font-medium text-gray-700">Completion Date:</span>
          <p class="text-gray-900 mt-1">{{ formatDate(approvalRequest.completion_date) }}</p>
        </div>
                  </div>
                </div>

    <!-- Pending Reviews Summary -->
    <div v-if="approvalId && approvalStages.length > 0" class="bg-white p-6 rounded-lg border border-gray-200">
      <h2 class="text-lg font-semibold text-gray-900 mb-4">Review Status Summary</h2>
      
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <!-- Pending Reviews -->
        <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <h3 class="text-sm font-medium text-yellow-800 mb-2">Yet to Review ({{ pendingStagesCount }})</h3>
          <div v-if="pendingStagesCount > 0" class="space-y-2">
            <div 
              v-for="stage in approvalStages.filter(s => s.stage_status === 'PENDING' || s.stage_status === 'IN_PROGRESS')" 
              :key="stage.stage_id"
              class="flex items-center justify-between text-xs"
            >
              <span class="text-yellow-700">{{ stage.assigned_user_name }} ({{ stage.assigned_user_role }})</span>
              <span class="px-2 py-1 bg-yellow-100 text-yellow-800 rounded-full text-xs">
                {{ stage.stage_status }}
              </span>
            </div>
          </div>
          <p v-else class="text-xs text-yellow-600">No pending reviews</p>
        </div>

        <!-- Completed Reviews -->
        <div class="bg-green-50 border border-green-200 rounded-lg p-4">
          <h3 class="text-sm font-medium text-green-800 mb-2">Completed Reviews ({{ completedStagesCount }})</h3>
          <div v-if="completedStagesCount > 0" class="space-y-2">
            <div 
              v-for="stage in approvalStages.filter(s => s.stage_status === 'APPROVED' || s.stage_status === 'REJECTED')" 
              :key="stage.stage_id"
              class="flex items-center justify-between text-xs"
            >
              <span class="text-green-700">{{ stage.assigned_user_name }} ({{ stage.assigned_user_role }})</span>
              <span 
                :class="stage.stage_status === 'APPROVED' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'"
                class="px-2 py-1 rounded-full text-xs"
              >
                {{ stage.stage_status }}
              </span>
            </div>
          </div>
          <p v-else class="text-xs text-green-600">No completed reviews yet</p>
        </div>
      </div>
    </div>

    <!-- Approval Stages Section -->
    <div v-if="approvalId && approvalStages.length > 0" class="space-y-6">
      <div class="bg-white p-4 rounded-lg border border-gray-200">
        <h2 class="text-lg font-semibold text-gray-900 mb-4">All Stages for Approval Request: {{ approvalId }}</h2>
        <p class="text-sm text-gray-600 mb-4">Total stages: {{ approvalStages.length }} | Pending: {{ pendingStagesCount }} | Completed: {{ completedStagesCount }}</p>
        
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div 
            v-for="stage in approvalStages" 
                    :key="stage.stage_id"
            class="bg-gray-50 rounded-lg p-4 border border-gray-200"
          >
            <!-- Stage Header -->
            <div class="flex justify-between items-center mb-4">
              <h3 class="text-lg font-medium text-gray-900">{{ stage.stage_name }}</h3>
              <span 
                :class="getStatusBadgeClass(stage.stage_status)"
                class="px-2 py-1 text-xs font-medium rounded-full"
              >
                {{ stage.stage_status }}
              </span>
            </div>

            <!-- Stage Details -->
            <div class="grid grid-cols-2 gap-3 mb-4 text-xs">
              <div><span class="font-medium text-gray-600">ID:</span> {{ stage.stage_id }}</div>
              <div><span class="font-medium text-gray-600">Order:</span> {{ stage.stage_order }}</div>
              <div><span class="font-medium text-gray-600">Type:</span> {{ stage.stage_type }}</div>
              <div><span class="font-medium text-gray-600">Department:</span> {{ stage.department }}</div>
              <div><span class="font-medium text-gray-600">Assigned To:</span> {{ stage.assigned_user_name }}</div>
              <div><span class="font-medium text-gray-600">Role:</span> {{ stage.assigned_user_role }}</div>
              <div><span class="font-medium text-gray-600">Deadline:</span> {{ formatDate(stage.deadline_date) }}</div>
              <div><span class="font-medium text-gray-600">Started:</span> {{ formatDate(stage.started_at) }}</div>
                  </div>

            <!-- Stage Description -->
            <div class="mb-3">
              <h4 class="text-xs font-medium text-gray-700 mb-1">Description:</h4>
              <p class="text-xs text-gray-900 bg-white p-2 rounded border">{{ stage.stage_description || 'No description provided' }}</p>
            </div>

            <!-- Response Data -->
            <div v-if="stage.response_data" class="mb-3">
              <h4 class="text-xs font-medium text-gray-700 mb-1">Response Data:</h4>
              <textarea
                v-model="stage.response_data_display"
                readonly
                rows="3"
                class="w-full px-2 py-1 border border-gray-300 rounded text-xs bg-white"
              />
            </div>

            <!-- Rejection Reason -->
            <div v-if="stage.rejection_reason" class="mb-3">
              <h4 class="text-xs font-medium text-gray-700 mb-1">Rejection Reason:</h4>
              <div class="bg-red-50 border border-red-200 rounded p-2">
                <p class="text-xs text-red-800">{{ stage.rejection_reason }}</p>
              </div>
            </div>

            <!-- Stage Actions - Only show to assigned users -->
            <div v-if="(stage.stage_status === 'PENDING' || stage.stage_status === 'IN_PROGRESS') && isCurrentUserAssigned(stage)" class="mt-3 p-3 bg-blue-50 border border-blue-200 rounded">
              <h4 class="text-xs font-medium text-blue-800 mb-2">Actions</h4>
              <div class="flex flex-wrap gap-2">
                <button 
                  @click="handleStageAction(stage, 'APPROVED')"
                  :disabled="submitting"
                  class="px-3 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700 disabled:opacity-50"
                >
                  Approve
                </button>
                <button 
                  @click="handleStageAction(stage, 'REJECTED')"
                  :disabled="submitting"
                  class="px-3 py-1 bg-red-600 text-white text-xs rounded hover:bg-red-700 disabled:opacity-50"
                >
                  Reject
                </button>
                <button 
                  @click="handleStageAction(stage, 'IN_PROGRESS')"
                  :disabled="submitting"
                  class="px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 disabled:opacity-50"
                >
                  In Progress
                </button>
              </div>
            </div>

            <!-- Show message for non-assigned users -->
            <div v-else-if="(stage.stage_status === 'PENDING' || stage.stage_status === 'IN_PROGRESS') && !isCurrentUserAssigned(stage)" class="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded">
              <h4 class="text-xs font-medium text-yellow-800 mb-2">Awaiting Review</h4>
              <p class="text-xs text-yellow-700">
                <span class="font-medium">{{ stage.assigned_user_name }}</span> ({{ stage.assigned_user_role }}) is yet to review this stage.
              </p>
            </div>

            <!-- Stage Comments -->
            <div v-if="stage.stage_status === 'APPROVED' || stage.stage_status === 'REJECTED'" class="mt-3 p-3 bg-gray-50 border border-gray-200 rounded">
              <h4 class="text-xs font-medium text-gray-700 mb-1">Status</h4>
              <p class="text-xs text-gray-600">
                {{ stage.stage_status.toLowerCase() }}
                <span v-if="stage.completed_at"> - {{ formatDate(stage.completed_at) }}</span>
              </p>
                 </div>
               </div>
            </div>
        </div>
      </div>

      <!-- No Data Messages -->
    <div v-else-if="approvalId && approvalStages.length === 0" class="bg-white rounded-lg border border-gray-200 p-12 text-center">
      <div class="text-gray-400 mb-4">
        <svg class="mx-auto h-12 w-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
        </svg>
      </div>
      <h3 class="text-lg font-medium text-gray-900 mb-2">No stages found</h3>
      <p class="text-gray-600">This approval request doesn't have any stages at this time.</p>
      </div>

    <!-- Loading Message -->
    <div v-else-if="!approvalId" class="bg-white rounded-lg border border-gray-200 p-12 text-center">
      <div class="text-gray-400 mb-4">
        <svg class="mx-auto h-12 w-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
        </svg>
      </div>
      <h3 class="text-lg font-medium text-gray-900 mb-2">Loading approval request...</h3>
      <p class="text-gray-600">Please wait while we fetch the approval request details.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { API_CONFIG, API_ENDPOINTS, buildApiUrl, apiCall } from '@/config/api.js'
import { useRfpApi } from '@/composables/useRfpApi'
import { useNotifications } from '@/composables/useNotifications'
import loggingService from '@/services/loggingService'

// Router
const route = useRoute()

// Reactive data
const { showSuccess, showError, showWarning, showInfo } = useNotifications()

// Get authenticated headers for axios requests
const { getAuthHeaders } = useRfpApi()

const approvalId = ref('')
const approvalRequest = ref(null)
const approvalStages = ref([])
const submitting = ref(false)
const currentUserId = ref('1') // Default user ID - in a real app, this would come from authentication

// Get current user ID from route params if available
onMounted(() => {
  if (route.params.userId) {
    currentUserId.value = route.params.userId as string
  }
})

// Computed properties
const pendingStagesCount = computed(() => {
  return approvalStages.value.filter(stage => stage.stage_status === 'PENDING' || stage.stage_status === 'IN_PROGRESS').length
})

const completedStagesCount = computed(() => {
  return approvalStages.value.filter(stage => stage.stage_status === 'APPROVED' || stage.stage_status === 'REJECTED').length
})

const parsedRequestData = computed(() => {
  if (!approvalRequest.value?.request_data) return {}
  
  try {
    // If it's already an object, return it
    if (typeof approvalRequest.value.request_data === 'object') {
      return approvalRequest.value.request_data
    }
    // If it's a string, try to parse it
    if (typeof approvalRequest.value.request_data === 'string') {
      return JSON.parse(approvalRequest.value.request_data)
    }
    return {}
  } catch (error) {
    console.error('Error parsing request data:', error)
    return {}
  }
})

// Helper function to check if current user is assigned to a stage
const isCurrentUserAssigned = (stage) => {
  return stage.assigned_user_id == currentUserId.value
}

// Methods
const fetchApprovalRequest = async () => {
  if (!approvalId.value) return
  
  try {
    // Use the requests endpoint to get the approval request details
    const url = buildApiUrl(`${API_ENDPOINTS.RFP_APPROVAL.REQUESTS}?workflow_id=${approvalId.value}`)
    const data = await apiCall(url)
    
    if (data && data.length > 0) {
      const request = data[0] // Get the first (and should be only) request
      approvalRequest.value = {
        ...request,
        request_data_display: request.request_data ? JSON.stringify(request.request_data, null, 2) : 'No data'
      }
    }
  } catch (error) {
    console.error('Error fetching approval request:', error)
  }
}

const fetchApprovalStages = async () => {
  if (!approvalId.value) return
  
  try {
    // Use the stages endpoint to get all stages for the specific approval request
    const url = buildApiUrl(`${API_ENDPOINTS.RFP_APPROVAL.STAGES}?approval_id=${approvalId.value}`)
    const data = await apiCall(url)
    
    approvalStages.value = data.map(stage => ({
      ...stage,
      response_data_display: stage.response_data ? JSON.stringify(stage.response_data, null, 2) : 'No data'
    }))
  } catch (error) {
    console.error('Error fetching approval stages:', error)
  }
}

const handleStageAction = async (stage: any, newStatus: string) => {
      try {
        submitting.value = true
        
        const requestData = {
      stage_id: stage.stage_id,
      status: newStatus,
      comments: `Stage ${newStatus.toLowerCase()} by user`
    }

    const url = buildApiUrl(API_ENDPOINTS.RFP_APPROVAL.UPDATE_STAGE_STATUS)
    await apiCall(url, {
      method: 'POST',
      body: JSON.stringify(requestData)
    })
    
    console.log(`Stage ${newStatus.toLowerCase()} successfully`)
    
    // Refresh the stages data
    await fetchApprovalStages()
        
      } catch (error) {
    console.error('Error updating stage status:', error)
      } finally {
        submitting.value = false
      }
    }


const getStatusBadgeClass = (status: string) => {
  const statusMap: { [key: string]: string } = {
    'DRAFT': 'bg-gray-100 text-gray-800',
    'PENDING': 'bg-yellow-100 text-yellow-800',
    'IN_PROGRESS': 'bg-blue-100 text-blue-800',
    'APPROVED': 'bg-green-100 text-green-800',
    'REJECTED': 'bg-red-100 text-red-800',
    'CANCELLED': 'bg-gray-100 text-gray-800',
    'EXPIRED': 'bg-red-100 text-red-800'
  }
  return statusMap[status] || 'bg-gray-100 text-gray-800'
}

const getPriorityBadgeClass = (priority: string) => {
  const priorityMap: { [key: string]: string } = {
    'LOW': 'bg-green-100 text-green-800',
    'MEDIUM': 'bg-yellow-100 text-yellow-800',
    'HIGH': 'bg-orange-100 text-orange-800',
    'URGENT': 'bg-red-100 text-red-800',
    'CRITICAL': 'bg-red-200 text-red-900'
  }
  return priorityMap[priority] || 'bg-gray-100 text-gray-800'
}

const isValidJson = (data: any) => {
  if (!data) return false
  
  try {
    if (typeof data === 'object') return true
    if (typeof data === 'string') {
      JSON.parse(data)
      return true
    }
    return false
  } catch {
    return false
  }
}

const formatKeyName = (key: string) => {
  // Convert camelCase, snake_case, or kebab-case to readable format
  return key
    .replace(/([A-Z])/g, ' $1') // Add space before capital letters
    .replace(/_/g, ' ') // Replace underscores with spaces
    .replace(/-/g, ' ') // Replace hyphens with spaces
    .replace(/\b\w/g, l => l.toUpperCase()) // Capitalize first letter of each word
    .trim()
}

const formatValue = (value: any) => {
  if (value === null || value === undefined) return 'Not specified'
  if (typeof value === 'boolean') return value ? 'Yes' : 'No'
  if (typeof value === 'number') {
    // Format currency if it looks like a price
    if (value > 1000 && value % 1 === 0) {
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
      }).format(value)
    }
    return value.toLocaleString()
  }
  if (typeof value === 'string') {
    // Format dates if they look like ISO dates
    if (value.match(/^\d{4}-\d{2}-\d{2}/)) {
      try {
        return new Date(value).toLocaleDateString('en-US', {
          year: 'numeric',
          month: 'long',
          day: 'numeric'
        })
      } catch {
        return value
      }
    }
    return value
  }
  return String(value)
}

const formatDate = (dateString: string) => {
      if (!dateString) return 'Not set'
      try {
        return new Date(dateString).toLocaleString()
      } catch {
        return dateString
      }
    }

// Lifecycle
onMounted(async () => {
  await loggingService.logPageView('RFP', 'Assignee Decision')
  // Check if we have query parameters from AllApprovals page
  if (route.query.workflow_id) {
    // The workflow_id parameter contains the approval request ID
    // We'll use this to fetch both the approval request and all stages
    approvalId.value = route.query.workflow_id as string
    await Promise.all([
      fetchApprovalRequest(),
      fetchApprovalStages()
    ])
  }
})
</script>

<style scoped>
/* Component-specific styles if needed */
</style>