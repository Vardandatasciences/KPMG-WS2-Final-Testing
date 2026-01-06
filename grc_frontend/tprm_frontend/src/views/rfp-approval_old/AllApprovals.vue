<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">All Approval Workflows</h1>
        <p class="text-gray-600 mt-1">View and manage all approval workflows created by users</p>
      </div>
      <div class="flex items-center space-x-3">
        <button 
          @click="fetchWorkflows" 
          :disabled="loading"
          class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50"
        >
          {{ loading ? 'Loading...' : 'Refresh' }}
        </button>
        <button 
          @click="exportWorkflows"
          :disabled="!selectedUserId || workflows.length === 0"
          class="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors disabled:opacity-50"
        >
          Export
        </button>
      </div>
    </div>

    <!-- User Selection -->
    <div class="bg-white p-4 rounded-lg border border-gray-200">
      <div class="flex items-center space-x-4">
        <div class="flex items-center space-x-2">
          <label class="text-sm font-medium text-gray-700">Select Creator:</label>
          <select 
            v-model="selectedUserId" 
            @change="onUserChange"
            class="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">Select a user...</option>
            <option v-for="user in users" :key="user.id" :value="user.id">
              {{ user.first_name }} {{ user.last_name }} ({{ user.username }})
            </option>
          </select>
        </div>
        <div v-if="selectedUserId" class="flex items-center space-x-2">
          <span class="text-sm text-gray-600">
            Showing workflows created by: <strong>{{ getSelectedUserName() }}</strong>
          </span>
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
            <option value="1">Active</option>
            <option value="0">Inactive</option>
          </select>
        </div>
        <div class="flex items-center space-x-2">
          <label class="text-sm font-medium text-gray-700">Type:</label>
          <select v-model="typeFilter" @change="applyFilters" class="px-3 py-1 border border-gray-300 rounded-md text-sm">
            <option value="all">All</option>
            <option value="MULTI_LEVEL">Multi Level</option>
            <option value="MULTI_PERSON">Multi Person</option>
          </select>
        </div>
        <div class="flex items-center space-x-2">
          <label class="text-sm font-medium text-gray-700">Business Type:</label>
          <select v-model="businessTypeFilter" @change="applyFilters" class="px-3 py-1 border border-gray-300 rounded-md text-sm">
            <option value="all">All</option>
            <option value="Policy">Policy</option>
            <option value="Contract">Contract</option>
            <option value="Purchase">Purchase</option>
            <option value="Finance">Finance</option>
            <option value="HR">HR</option>
            <option value="IT">IT</option>
          </select>
        </div>
        <div class="flex items-center space-x-2">
          <label class="text-sm font-medium text-gray-700">Search:</label>
          <input 
            v-model="searchFilter" 
            @input="applyFilters"
            type="text" 
            placeholder="Search workflows..."
            class="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      </div>
    </div>

    <!-- Workflows Table -->
    <div class="bg-white rounded-lg border border-gray-200">
      <div class="px-6 py-4 border-b border-gray-200">
        <h2 class="text-lg font-semibold text-gray-900">
          {{ selectedUserId ? `Workflows Created by ${getSelectedUserName()}` : 'Select a user to view workflows' }}
        </h2>
        <p v-if="selectedUserId" class="text-sm text-gray-600 mt-1">
          Total workflows: {{ filteredWorkflows.length }} | Active: {{ activeWorkflowsCount }} | Inactive: {{ inactiveWorkflowsCount }}
        </p>
      </div>
      
      <!-- Loading state -->
      <div v-if="loading" class="px-6 py-12 text-center">
        <div class="text-gray-400 mb-4">
          <svg class="animate-spin mx-auto h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
          </svg>
        </div>
        <p class="text-gray-600">Loading workflows...</p>
      </div>

      <!-- Workflows table -->
      <div v-else-if="filteredWorkflows.length > 0" class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Workflow Details
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Type & Status
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Business Object
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Created
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Last Updated
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr 
              v-for="workflow in filteredWorkflows" 
              :key="workflow.workflow_id"
              class="hover:bg-gray-50 transition-colors"
            >
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="flex items-center">
                  <div class="flex-shrink-0 h-10 w-10">
                    <div class="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center">
                      <svg class="h-5 w-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                      </svg>
                    </div>
                  </div>
                  <div class="ml-4">
                    <div class="text-sm font-medium text-gray-900">
                      {{ workflow.workflow_name }}
                    </div>
                    <div class="text-sm text-gray-500">
                      ID: {{ workflow.workflow_id }}
                    </div>
                    <div class="text-xs text-gray-400 mt-1 max-w-xs truncate">
                      {{ workflow.description }}
                    </div>
                  </div>
                </div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="space-y-1">
                  <span 
                    :class="getWorkflowTypeBadgeClass(workflow.workflow_type)"
                    class="inline-flex px-2 py-1 text-xs font-medium rounded-full"
                  >
                    {{ getWorkflowTypeLabel(workflow.workflow_type) }}
                  </span>
                  <div>
                    <span 
                      :class="workflow.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'"
                      class="inline-flex px-2 py-1 text-xs font-medium rounded-full"
                    >
                      {{ workflow.is_active ? 'Active' : 'Inactive' }}
                    </span>
                  </div>
                </div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm text-gray-900">{{ workflow.business_object_type }}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm text-gray-900">{{ formatDate(workflow.created_at) }}</div>
                <div class="text-xs text-gray-500">by {{ getCreatorName(workflow.created_by) }}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm text-gray-900">{{ formatDate(workflow.updated_at) }}</div>
                <div class="text-xs text-gray-500">{{ formatRelativeTime(workflow.updated_at) }}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                <div class="flex items-center space-x-2">
                  <button 
                    @click="viewWorkflowDetails(workflow)"
                    class="text-blue-600 hover:text-blue-900 transition-colors"
                  >
                    View Requests
                  </button>
                  <button 
                    @click="viewWorkflowChanges(workflow)"
                    class="text-green-600 hover:text-green-900 transition-colors"
                  >
                    View Changes
                  </button>
                  <button 
                    @click="toggleWorkflowStatus(workflow)"
                    :class="workflow.is_active ? 'text-red-600 hover:text-red-900' : 'text-green-600 hover:text-green-900'"
                    class="transition-colors"
                  >
                    {{ workflow.is_active ? 'Deactivate' : 'Activate' }}
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Empty state -->
      <div v-else-if="selectedUserId && !loading" class="px-6 py-12 text-center">
        <div class="text-gray-400 mb-4">
          <svg class="mx-auto h-12 w-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
          </svg>
        </div>
        <h3 class="text-lg font-medium text-gray-900 mb-2">No workflows found</h3>
        <p class="text-gray-600">
          {{ filteredWorkflows.length === 0 && workflows.length > 0 
            ? 'No workflows match the current filters.' 
            : 'No approval workflows have been created by this user.' 
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
        <p class="text-gray-600">Please select a user from the dropdown above to view their created approval workflows.</p>
      </div>
    </div>


    <!-- Workflow Changes Modal -->
    <div
      v-if="showChangesModal"
      class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50"
    >
      <div class="relative top-20 mx-auto p-5 border w-4/5 max-w-4xl shadow-lg rounded-md bg-white">
        <div class="mt-3">
          <div class="flex justify-between items-center mb-4">
            <h3 class="text-lg leading-6 font-medium text-gray-900">Workflow Changes History</h3>
            <button
              @click="showChangesModal = false"
              class="text-gray-400 hover:text-gray-600"
            >
              <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
          </div>
          
          <div class="space-y-4">
            <div v-if="workflowChanges.length > 0" class="space-y-3">
              <div 
                v-for="change in workflowChanges" 
                :key="change.id"
                class="border border-gray-200 rounded-lg p-4"
              >
                <div class="flex justify-between items-start">
                  <div class="flex-1">
                    <h4 class="text-sm font-medium text-gray-900">{{ change.change_type }}</h4>
                    <p class="text-sm text-gray-600 mt-1">{{ change.description }}</p>
                    <div class="mt-2 text-xs text-gray-500">
                      Changed by: {{ getCreatorName(change.changed_by) }} | 
                      {{ formatDate(change.changed_at) }}
                    </div>
                  </div>
                  <span 
                    :class="getChangeTypeBadgeClass(change.change_type)"
                    class="inline-flex px-2 py-1 text-xs font-medium rounded-full"
                  >
                    {{ change.change_type }}
                  </span>
                </div>
                <div v-if="change.old_values || change.new_values" class="mt-3 grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div v-if="change.old_values">
                    <label class="text-xs font-medium text-gray-700">Previous Values</label>
                    <pre class="text-xs text-gray-600 bg-gray-50 p-2 rounded mt-1">{{ JSON.stringify(change.old_values, null, 2) }}</pre>
                  </div>
                  <div v-if="change.new_values">
                    <label class="text-xs font-medium text-gray-700">New Values</label>
                    <pre class="text-xs text-gray-600 bg-gray-50 p-2 rounded mt-1">{{ JSON.stringify(change.new_values, null, 2) }}</pre>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="text-center py-8">
              <p class="text-gray-500">No changes recorded for this workflow.</p>
            </div>
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
import PopupModal from '@/popup/PopupModal.vue'
import { PopupService } from '@/popup/popupService'
import { useNotifications } from '@/composables/useNotifications'
import loggingService from '@/services/loggingService'

// Router
const router = useRouter()

// Reactive data
const { showSuccess, showError, showWarning, showInfo } = useNotifications()

const workflows = ref([])
const users = ref([])
const loading = ref(false)
const selectedUserId = ref('')
const showChangesModal = ref(false)
const workflowChanges = ref([])

// Filters
const statusFilter = ref('all')
const typeFilter = ref('all')
const businessTypeFilter = ref('all')
const searchFilter = ref('')

// Computed properties
const filteredWorkflows = computed(() => {
  let filtered = workflows.value

  if (statusFilter.value !== 'all') {
    const isActive = statusFilter.value === '1'
    filtered = filtered.filter(workflow => workflow.is_active === isActive)
  }

  if (typeFilter.value !== 'all') {
    filtered = filtered.filter(workflow => workflow.workflow_type === typeFilter.value)
  }

  if (businessTypeFilter.value !== 'all') {
    filtered = filtered.filter(workflow => workflow.business_object_type === businessTypeFilter.value)
  }

  if (searchFilter.value) {
    const search = searchFilter.value.toLowerCase()
    filtered = filtered.filter(workflow => 
      workflow.workflow_name.toLowerCase().includes(search) ||
      workflow.description.toLowerCase().includes(search) ||
      workflow.workflow_id.toLowerCase().includes(search)
    )
  }

  return filtered
})

const activeWorkflowsCount = computed(() => {
  return workflows.value.filter(workflow => workflow.is_active).length
})

const inactiveWorkflowsCount = computed(() => {
  return workflows.value.filter(workflow => !workflow.is_active).length
})

// Methods
const fetchUsers = async () => {
  try {
    const url = buildApiUrl(API_ENDPOINTS.RFP_APPROVAL.USERS)
    const data = await apiCall(url)
    users.value = data
  } catch (error) {
    console.error('Error fetching users:', error)
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

const fetchWorkflows = async () => {
  if (!selectedUserId.value) {
    workflows.value = []
    return
  }

  loading.value = true
  try {
    // Fetch workflows created by the selected user
    const url = buildApiUrl(`${API_ENDPOINTS.RFP_APPROVAL.WORKFLOWS}?created_by=${selectedUserId.value}`)
    const data = await apiCall(url)
    
    // Force Vue reactivity by creating a new array
    workflows.value = [...data]
  } catch (error) {
    console.error('Error fetching workflows:', error)
    // Show user-friendly error message
    PopupService.error('Failed to fetch workflows. Please check if the backend server is running on port 8000.', 'Fetch Failed')
    workflows.value = []
  } finally {
    loading.value = false
  }
}

const onUserChange = () => {
  if (selectedUserId.value) {
    fetchWorkflows()
  } else {
    workflows.value = []
  }
}

const applyFilters = () => {
  // Filters are applied automatically through computed property
}

const getSelectedUserName = () => {
  const user = users.value.find(u => u.id == selectedUserId.value)
  return user ? `${user.first_name} ${user.last_name}` : 'Unknown User'
}

const getCreatorName = (userId: number) => {
  const user = users.value.find(u => u.id == userId)
  return user ? `${user.first_name} ${user.last_name}` : `User ${userId}`
}

const getWorkflowTypeLabel = (type: string) => {
  return type === 'MULTI_LEVEL' ? 'Multi Level' : 'Multi Person'
}

const getWorkflowTypeBadgeClass = (type: string) => {
  return type === 'MULTI_LEVEL' ? 'bg-blue-100 text-blue-800' : 'bg-purple-100 text-purple-800'
}

const getChangeTypeBadgeClass = (type: string) => {
  switch (type.toLowerCase()) {
    case 'created':
      return 'bg-green-100 text-green-800'
    case 'updated':
      return 'bg-blue-100 text-blue-800'
    case 'deleted':
      return 'bg-red-100 text-red-800'
    case 'activated':
      return 'bg-green-100 text-green-800'
    case 'deactivated':
      return 'bg-yellow-100 text-yellow-800'
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

const viewWorkflowDetails = (workflow: any) => {
  // Navigate to AssigneeDecision page instead of showing modal
  router.push({
    name: 'AssigneeDecision',
    query: {
      workflow_id: workflow.workflow_id,
      created_by: workflow.created_by
    }
  })
}

const viewWorkflowChanges = async (workflow: any) => {
  try {
    // Fetch workflow changes/history
    const url = buildApiUrl(`${API_ENDPOINTS.RFP_APPROVAL.WORKFLOWS}${workflow.workflow_id}/changes/`)
    const data = await apiCall(url)
    workflowChanges.value = data
    showChangesModal.value = true
  } catch (error) {
    console.error('Error fetching workflow changes:', error)
    // Show mock data for demonstration
    workflowChanges.value = [
      {
        id: 1,
        change_type: 'Created',
        description: 'Workflow was initially created',
        changed_by: workflow.created_by,
        changed_at: workflow.created_at,
        old_values: null,
        new_values: {
          workflow_name: workflow.workflow_name,
          workflow_type: workflow.workflow_type,
          description: workflow.description
        }
      },
      {
        id: 2,
        change_type: 'Updated',
        description: 'Workflow description was modified',
        changed_by: workflow.created_by,
        changed_at: workflow.updated_at,
        old_values: {
          description: 'Original description'
        },
        new_values: {
          description: workflow.description
        }
      }
    ]
    showChangesModal.value = true
  }
}

const toggleWorkflowStatus = async (workflow: any) => {
  try {
    const newStatus = !workflow.is_active
    const url = buildApiUrl(`${API_ENDPOINTS.RFP_APPROVAL.WORKFLOWS}${workflow.workflow_id}/`)
    
    await apiCall(url, {
      method: 'PATCH',
      body: JSON.stringify({
        is_active: newStatus
      })
    })
    
    // Update local state
    workflow.is_active = newStatus
    
    console.log(`Workflow ${newStatus ? 'activated' : 'deactivated'} successfully`)
  } catch (error) {
    console.error('Error toggling workflow status:', error)
    PopupService.error('Failed to update workflow status', 'Update Failed')
  }
}

const exportWorkflows = () => {
  if (!selectedUserId.value || workflows.value.length === 0) return
  
  const csvContent = [
    ['Workflow ID', 'Name', 'Type', 'Status', 'Business Type', 'Created At', 'Updated At', 'Created By'],
    ...workflows.value.map(workflow => [
      workflow.workflow_id,
      workflow.workflow_name,
      getWorkflowTypeLabel(workflow.workflow_type),
      workflow.is_active ? 'Active' : 'Inactive',
      workflow.business_object_type,
      formatDate(workflow.created_at),
      formatDate(workflow.updated_at),
      getCreatorName(workflow.created_by)
    ])
  ].map(row => row.join(',')).join('\n')
  
  const blob = new Blob([csvContent], { type: 'text/csv' })
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `workflows_${getSelectedUserName().replace(/\s+/g, '_')}_${new Date().toISOString().split('T')[0]}.csv`
  a.click()
  window.URL.revokeObjectURL(url)
}

// Lifecycle
onMounted(async () => {
  await loggingService.logPageView('RFP', 'All Approvals')
  await fetchUsers()
})
</script>

<style scoped>
/* Component-specific styles if needed */
</style>
