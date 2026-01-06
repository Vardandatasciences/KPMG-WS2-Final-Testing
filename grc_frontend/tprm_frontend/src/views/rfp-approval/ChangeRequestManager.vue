<template>
  <div class="change-request-manager max-w-7xl mx-auto p-6">
    <!-- Header -->
    <div class="bg-white rounded-lg border border-gray-200 shadow-sm mb-6">
      <div class="px-6 py-4 border-b border-gray-200">
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-2xl font-bold text-gray-900">Change Request Manager</h1>
            <p class="text-gray-600 mt-1">
              Review and respond to change requests for your RFPs
            </p>
          </div>
          <div class="flex items-center space-x-3">
            <button 
              @click="goBack"
              class="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors flex items-center space-x-2"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path>
              </svg>
              <span>Back</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Change Requests List -->
    <div class="bg-white rounded-lg border border-gray-200 shadow-sm">
      <div class="px-6 py-4 border-b border-gray-200">
        <h2 class="text-lg font-semibold text-gray-900">Pending Change Requests</h2>
        <p class="text-sm text-gray-600 mt-1">Review and respond to change requests from reviewers</p>
      </div>

      <div v-if="loading" class="p-8 text-center">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
        <p class="text-sm text-gray-600 mt-2">Loading change requests...</p>
      </div>

      <div v-else-if="changeRequests.length === 0" class="p-8 text-center">
        <div class="text-gray-400 mb-4">
          <svg class="mx-auto h-12 w-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
          </svg>
        </div>
        <h3 class="text-lg font-medium text-gray-900 mb-2">No Change Requests</h3>
        <p class="text-gray-600">You don't have any pending change requests at this time.</p>
      </div>

      <div v-else class="divide-y divide-gray-200">
        <div 
          v-for="request in changeRequests" 
          :key="request.change_request_id"
          class="p-6 hover:bg-gray-50 transition-colors"
        >
          <div class="flex items-start justify-between">
            <div class="flex-1">
              <div class="flex items-center space-x-3 mb-4">
                <div class="flex items-center space-x-2">
                  <div class="px-3 py-1 text-sm font-medium bg-amber-100 text-amber-800 rounded-full">
                    Change Request
                  </div>
                  <div class="text-sm text-gray-500">
                    Requested by {{ request.requested_by_name }} ({{ request.requested_by_role }})
                  </div>
                </div>
                <div class="text-sm text-gray-500">
                  {{ formatDate(request.requested_at) }}
                </div>
              </div>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div>
                  <h4 class="text-sm font-medium text-gray-700 mb-1">RFP Information</h4>
                  <p class="text-sm text-gray-900">{{ request.rfp_title }}</p>
                  <p class="text-xs text-gray-500">RFP ID: {{ request.rfp_id }}</p>
                </div>
                <div>
                  <h4 class="text-sm font-medium text-gray-700 mb-1">Approval Information</h4>
                  <p class="text-sm text-gray-900">Approval ID: {{ request.approval_id }}</p>
                  <p class="text-xs text-gray-500">Stage: {{ request.stage_name }}</p>
                </div>
              </div>

              <div class="mb-4">
                <h4 class="text-sm font-medium text-gray-700 mb-2">Change Request Details</h4>
                <div class="bg-amber-50 p-4 rounded-lg border border-amber-200">
                  <p class="text-sm text-gray-900">{{ request.change_request_description }}</p>
                </div>
              </div>

              <div v-if="request.specific_fields && request.specific_fields.length > 0" class="mb-4">
                <h4 class="text-sm font-medium text-gray-700 mb-2">Specific Fields to Change</h4>
                <div class="bg-blue-50 p-4 rounded-lg border border-blue-200">
                  <ul class="text-sm text-gray-900 space-y-1">
                    <li v-for="field in request.specific_fields" :key="field" class="flex items-center space-x-2">
                      <svg class="w-4 h-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
                      </svg>
                      <span>{{ field }}</span>
                    </li>
                  </ul>
                </div>
              </div>

              <!-- Actions -->
              <div class="flex items-center space-x-3">
                <button 
                  @click="editRFP(request)"
                  class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm font-medium flex items-center space-x-2"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
                  </svg>
                  <span>Edit RFP</span>
                </button>
                <button 
                  @click="viewRFPDetails(request)"
                  class="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors text-sm font-medium flex items-center space-x-2"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
                  </svg>
                  <span>View RFP</span>
                </button>
                <button 
                  @click="respondToRequest(request, 'decline')"
                  class="px-4 py-2 bg-red-100 text-red-700 rounded-md hover:bg-red-200 transition-colors text-sm font-medium flex items-center space-x-2"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                  </svg>
                  <span>Decline</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- RFP Edit Modal -->
    <div v-if="showEditModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg shadow-xl max-w-6xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div class="px-6 py-4 border-b border-gray-200">
          <div class="flex items-center justify-between">
            <h3 class="text-lg font-semibold text-gray-900">Edit RFP - {{ selectedRequest?.rfp_title }}</h3>
            <button 
              @click="showEditModal = false"
              class="text-gray-400 hover:text-gray-600"
            >
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
          </div>
        </div>

        <div class="p-6">
          <div class="mb-6 p-4 bg-amber-50 rounded-lg border border-amber-200">
            <h4 class="text-sm font-semibold text-amber-900 mb-2">Change Request Details</h4>
            <p class="text-sm text-amber-800">{{ selectedRequest?.change_request_description }}</p>
          </div>

          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">Changes Made</label>
              <textarea 
                v-model="changesMade"
                rows="4"
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Describe the changes you made to address the reviewer's request..."
              ></textarea>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">Additional Notes</label>
              <textarea 
                v-model="additionalNotes"
                rows="3"
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Any additional notes or comments..."
              ></textarea>
            </div>
          </div>

          <div class="flex items-center justify-end space-x-3 pt-6">
            <button 
              @click="showEditModal = false"
              class="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
            >
              Cancel
            </button>
            <button 
              @click="submitChanges"
              :disabled="submitting"
              class="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              <svg v-if="submitting" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span>{{ submitting ? 'Submitting...' : 'Submit Changes' }}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { API_CONFIG, API_ENDPOINTS, buildApiUrl, apiCall } from '@/config/api.js'
import { useRfpApi } from '@/composables/useRfpApi'
import { useNotifications } from '@/composables/useNotifications'
import loggingService from '@/services/loggingService'

// Router
const route = useRoute()
const router = useRouter()

// Notifications
const { showSuccess, showError, showWarning, showInfo } = useNotifications()

// Get authenticated headers for axios requests
const { getAuthHeaders } = useRfpApi()

// Reactive data
const changeRequests = ref([])
const loading = ref(false)
const submitting = ref(false)
const showEditModal = ref(false)
const selectedRequest = ref(null)

// Edit form data
const changesMade = ref('')
const additionalNotes = ref('')

// Methods
const loadChangeRequests = async () => {
  try {
    loading.value = true
    console.log('🔄 Loading change requests...')
    
    const url = buildApiUrl('/change-requests/')
    const response = await apiCall(url)
    
    if (response.success && response.change_requests) {
      changeRequests.value = response.change_requests
      console.log('✅ Change requests loaded:', changeRequests.value.length)
    } else {
      console.log('⚠️ No change requests found or API error')
      changeRequests.value = []
    }
  } catch (error) {
    console.error('❌ Error loading change requests:', error)
    // Don't show error notifications to avoid additional API calls
    console.log('⚠️ Showing empty state due to error')
    changeRequests.value = []
  } finally {
    loading.value = false
  }
}

const editRFP = async (request) => {
  try {
    selectedRequest.value = request
    changesMade.value = ''
    additionalNotes.value = ''
    
    // Load the original RFP data
    console.log('🔄 Loading RFP data for editing:', request.rfp_id)
    const rfpData = await loadRFPData(request.rfp_id)
    
    if (rfpData) {
      // Store the original RFP data for versioning
      localStorage.setItem('original_rfp_data', JSON.stringify(rfpData))
      localStorage.setItem('current_change_request_id', request.change_request_id)
      localStorage.setItem('current_rfp_id', request.rfp_id)
      localStorage.setItem('current_approval_id', request.approval_id)
      localStorage.setItem('current_stage_id', request.stage_id)
      
      // Navigate to RFP creation page with edit mode
      router.push({
        name: 'RFPCreation',
        query: {
          rfpId: request.rfp_id,
          edit: true,
          changeRequest: request.change_request_id,
          approvalId: request.approval_id,
          stageId: request.stage_id,
          mode: 'change_request'
        }
      })
    } else {
      showError('Failed to load RFP data for editing')
    }
  } catch (error) {
    console.error('❌ Error loading RFP for editing:', error)
    showError('Failed to load RFP data')
  }
}

const loadRFPData = async (rfpId) => {
  try {
    // Use the stable RFP details endpoint
    const url = buildApiUrl(`/rfp-details/${rfpId}/`)
    const response = await apiCall(url)
    
    // The backend returns the RFP data directly (not wrapped in success/rfp)
    // Handle both response formats for compatibility
    if (response.rfp_id || response.rfp_title) {
      console.log('✅ RFP data loaded successfully:', response.rfp_title)
      
      // Transform backend response to frontend-compatible format
      const rfpData = {
        // Use both formats for compatibility
        id: response.rfp_id,
        rfp_id: response.rfp_id,
        rfp_number: response.rfp_number,
        title: response.rfp_title,
        rfp_title: response.rfp_title,
        description: response.description,
        type: response.rfp_type,
        rfp_type: response.rfp_type,
        category: response.category,
        estimatedValue: response.estimated_value,
        estimated_value: response.estimated_value,
        currency: response.currency,
        budgetMin: response.budget_range_min,
        budget_range_min: response.budget_range_min,
        budgetMax: response.budget_range_max,
        budget_range_max: response.budget_range_max,
        issueDate: response.issue_date,
        issue_date: response.issue_date,
        deadline: response.submission_deadline,
        submission_deadline: response.submission_deadline,
        evaluationPeriodEnd: response.evaluation_period_end,
        evaluation_period_end: response.evaluation_period_end,
        evaluationMethod: response.evaluation_method,
        evaluation_method: response.evaluation_method,
        criticalityLevel: response.criticality_level,
        criticality_level: response.criticality_level,
        geographicalScope: response.geographical_scope,
        geographical_scope: response.geographical_scope,
        complianceRequirements: response.compliance_requirements,
        compliance_requirements: response.compliance_requirements,
        allowLateSubmissions: response.allow_late_submissions,
        allow_late_submissions: response.allow_late_submissions,
        autoApprove: response.auto_approve,
        auto_approve: response.auto_approve,
        documents: response.documents || [],
        evaluation_criteria: response.evaluation_criteria || [],
        custom_fields: response.custom_fields,
        status: response.status,
        version_number: response.version_number
      }
      
      return rfpData
    } else if (response.success && response.rfp) {
      // Handle legacy wrapped format
      console.log('✅ RFP data loaded successfully (legacy format)')
      return response.rfp
    } else if (response.error) {
      console.error('❌ Failed to load RFP data:', response.error)
      showError(response.error || 'Failed to load RFP data')
      return null
    } else {
      console.error('❌ Unexpected response format:', response)
      showError('Unexpected response format from server')
      return null
    }
  } catch (error) {
    console.error('❌ Error loading RFP data:', error)
    showError(`Failed to load RFP data: ${error.message || 'Unknown error'}`)
    return null
  }
}

const viewRFPDetails = (request) => {
  // Navigate to RFP details page
  router.push({
    name: 'RFPCreation',
    query: {
      rfpId: request.rfp_id,
      edit: true,
      changeRequest: request.change_request_id
    }
  })
}

const submitChanges = async () => {
  try {
    submitting.value = true
    
    const changeData = {
      change_request_id: selectedRequest.value.change_request_id,
      approval_id: selectedRequest.value.approval_id,
      stage_id: selectedRequest.value.stage_id,
      changes_made: changesMade.value,
      additional_notes: additionalNotes.value,
      status: 'completed'
    }
    
    const url = buildApiUrl('/change-requests/respond/')
    const response = await apiCall(url, {
      method: 'POST',
      body: JSON.stringify(changeData)
    })
    
    if (response.success) {
      showSuccess('Changes submitted successfully')
      showEditModal.value = false
      await loadChangeRequests()
    } else {
      showError(response.message || 'Failed to submit changes')
    }
  } catch (error) {
    console.error('❌ Error submitting changes:', error)
    showError('Failed to submit changes')
  } finally {
    submitting.value = false
  }
}

const respondToRequest = async (request, action) => {
  try {
    const responseData = {
      change_request_id: request.change_request_id,
      approval_id: request.approval_id,
      stage_id: request.stage_id,
      status: action === 'decline' ? 'declined' : 'accepted',
      response_notes: action === 'decline' ? 'Change request declined by creator' : 'Change request accepted'
    }
    
    const url = buildApiUrl('/change-requests/respond/')
    const response = await apiCall(url, {
      method: 'POST',
      body: JSON.stringify(responseData)
    })
    
    if (response.success) {
      showSuccess(`Change request ${action}d successfully`)
      await loadChangeRequests()
    } else {
      showError(response.message || `Failed to ${action} change request`)
    }
  } catch (error) {
    console.error(`❌ Error ${action}ing change request:`, error)
    showError(`Failed to ${action} change request`)
  }
}

const formatDate = (dateString) => {
  if (!dateString) return 'Not set'
  try {
    return new Date(dateString).toLocaleString()
  } catch {
    return dateString
  }
}

const goBack = () => {
  try {
    router.go(-1)
  } catch (error) {
    console.error('Navigation error:', error)
    window.history.back()
  }
}

// Lifecycle
onMounted(async () => {
  try {
    await loggingService.logPageView('RFP', 'Change Request Manager')
    await loadChangeRequests()
  } catch (error) {
    console.warn('Permission or logging error, continuing anyway:', error)
    // Still try to load change requests even if logging fails
    await loadChangeRequests()
  }
})
</script>

<style scoped>
.change-request-manager {
  min-height: 100vh;
  background-color: #f9fafb;
}
</style>
