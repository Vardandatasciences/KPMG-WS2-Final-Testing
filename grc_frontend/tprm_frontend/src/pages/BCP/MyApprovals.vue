<template>
  <div class="p-6 max-w-7xl mx-auto space-y-6">
    <!-- User Info Card -->
    <div class="card" v-if="userInfo">
      <div class="card-header">
        <h3 class="card-title">Welcome, {{ userInfo.full_name }}</h3>
      </div>
      <div class="card-content">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div class="stat-card stat-card--primary">
            <div class="stat-card__icon">
              <svg class="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
              </svg>
            </div>
            <div class="stat-card__content">
              <div class="stat-card__value">{{ totalApprovals }}</div>
              <div class="stat-card__label">Total Approvals</div>
            </div>
          </div>
          <div class="stat-card stat-card--warning">
            <div class="stat-card__icon">
              <svg class="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
            </div>
            <div class="stat-card__content">
              <div class="stat-card__value">{{ pendingApprovals }}</div>
              <div class="stat-card__label">Pending</div>
            </div>
          </div>
          <div class="stat-card stat-card--danger">
            <div class="stat-card__icon">
              <svg class="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"/>
              </svg>
            </div>
            <div class="stat-card__content">
              <div class="stat-card__value">{{ overdueApprovals }}</div>
              <div class="stat-card__label">Overdue</div>
            </div>
          </div>
          <div class="stat-card stat-card--success">
            <div class="stat-card__icon">
              <svg class="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
            </div>
            <div class="stat-card__content">
              <div class="stat-card__value">{{ completedApprovals }}</div>
              <div class="stat-card__label">Completed</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Filters -->
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">Filters</h3>
      </div>
      <div class="card-content">
        <div class="form-grid-5">
          <div class="space-y-2">
            <label class="block text-sm font-medium">Search</label>
            <input 
              v-model="filters.search" 
              type="text" 
              class="input" 
              placeholder="Search by workflow name or assigner"
              @input="fetchMyApprovals"
            />
          </div>
          <div class="space-y-2">
            <label class="block text-sm font-medium">User</label>
            <select v-model="filters.user_id" class="input" @change="fetchMyApprovals" :disabled="isLoadingUsers">
              <option value="">{{ isLoadingUsers ? 'Loading users...' : 'All Users' }}</option>
              <option v-for="user in users" :key="user.user_id" :value="user.user_id">
                {{ user.display_name }}
              </option>
            </select>
          </div>
          <div class="space-y-2">
            <label class="block text-sm font-medium">Status</label>
            <select v-model="filters.status" class="input" @change="fetchMyApprovals">
              <option value="">All Statuses</option>
              <option value="ASSIGNED">Assigned</option>
              <option value="IN_PROGRESS">In Progress</option>
              <option value="COMMENTED">Commented</option>
              <option value="SKIPPED">Skipped</option>
              <option value="EXPIRED">Expired</option>
              <option value="CANCELLED">Cancelled</option>
            </select>
          </div>
          <div class="space-y-2">
            <label class="block text-sm font-medium">Plan Type</label>
            <select v-model="filters.plan_type" class="input" @change="fetchMyApprovals">
              <option value="">All Plan Types</option>
              <option value="BCP">Business Continuity Plan</option>
              <option value="DRP">Disaster Recovery Plan</option>
            </select>
          </div>
          <div class="space-y-2">
            <label class="block text-sm font-medium">Object Type</label>
            <select v-model="filters.object_type" class="input" @change="fetchMyApprovals">
              <option value="">All Object Types</option>
              <option value="PLAN EVALUATION">Plan Evaluation</option>
              <option value="NEW QUESTIONNAIRE">New Questionnaire</option>
              <option value="QUESTIONNAIRE RESPONSE">Questionnaire Response</option>
            </select>
          </div>
        </div>
      </div>
    </div>

    <!-- My Approvals Cards -->
    <div class="card">
      <div class="card-header">
        <div class="flex items-center gap-2">
          <svg class="h-5 w-5 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
          <h3 class="card-title">Pending Approvals ({{ isLoadingApprovals ? '...' : filteredApprovals.length }})</h3>
        </div>
      </div>
      <!-- Object Type Toggle -->
      <div class="object-type-toggle-container">
        <div class="object-type-toggle">
          <button
            v-for="type in objectTypes"
            :key="type.value"
            @click="selectedObjectType = type.value"
            class="toggle-option"
            :class="{ 'toggle-option--active': selectedObjectType === type.value }"
          >
            {{ type.label }}
            <span class="toggle-count">({{ getApprovalCountByType(type.value) }})</span>
          </button>
        </div>
      </div>
      <div class="card-content">
        <div v-if="isLoadingApprovals" class="p-6 text-center">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
          <p class="mt-2 text-muted-foreground">Loading your approvals...</p>
        </div>
        <div v-else-if="filteredApprovals.length === 0" class="p-6 text-center">
          <div class="mb-4">
            <svg class="h-12 w-12 mx-auto text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
            </svg>
          </div>
          <p class="text-muted-foreground">
            <span v-if="selectedObjectType !== 'ALL'">No {{ objectTypes.find(t => t.value === selectedObjectType)?.label || selectedObjectType }} approvals found.</span>
            <span v-else>No approvals assigned to you at the moment.</span>
          </p>
          <p class="text-sm text-muted-foreground mt-2">
            <span v-if="selectedObjectType !== 'ALL'">Try selecting a different type or "All" to see all approvals.</span>
            <span v-else>Check back later or contact your administrator if you expect to see approvals here.</span>
          </p>
        </div>
        <div v-else class="approval-cards-grid">
          <div 
            v-for="approval in filteredApprovals" 
            :key="approval.approval_id" 
            class="approval-card"
            :class="{ 
              'approval-card--overdue': approval.is_overdue, 
              'approval-card--urgent': approval.days_until_due <= 2 && approval.days_until_due > 0 
            }"
          >
            <div class="approval-card__header">
              <div class="approval-card__title-row">
                <h4 class="approval-card__title">{{ approval.object_type }}</h4>
                <div class="approval-card__tags">
                  <span class="badge badge--plan-type" :class="approval.plan_type === 'BCP' ? 'badge--success' : 'badge--info'">
                    {{ approval.plan_type }}
                  </span>
                  <span class="badge badge--priority" :class="getPriorityBadgeClass(approval)">
                    {{ getPriorityLabel(approval) }}
                  </span>
                </div>
              </div>
              <h5 class="approval-card__subtitle">{{ approval.workflow_name }}</h5>
            </div>
            <div class="approval-card__body">
              <div class="approval-card__details">
                <span class="approval-card__detail-text">
                  {{ approval.object_type }} #{{ approval.object_id }} | Assigned by: {{ approval.assigner_name }}
                </span>
              </div>
              <div class="approval-card__due-date">
                <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
                <span class="approval-card__due-text" :class="getDueDateClass(approval)">
                  Due: {{ formatDateShort(approval.due_date) }} 
                  <span v-if="approval.is_overdue" class="approval-card__days-left">
                    ({{ Math.abs(approval.days_until_due) }} days overdue)
                  </span>
                  <span v-else-if="approval.days_until_due !== null" class="approval-card__days-left">
                    ({{ approval.days_until_due }} {{ approval.days_until_due === 1 ? 'day' : 'days' }} left)
                  </span>
                </span>
              </div>
            </div>
            <div class="approval-card__actions">
              <button 
                @click="viewApproval(approval)" 
                class="btn btn--card btn--view"
                title="View Details"
              >
                <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                </svg>
                View
              </button>
              <button 
                @click="updateStatus(approval, 'IN_PROGRESS')" 
                class="btn btn--card btn--start"
                v-if="approval.status === 'ASSIGNED'"
                title="Start Working"
              >
                Start Working
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Comment Modal -->
    <div v-if="showCommentModal" class="modal-overlay" @click="closeCommentModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3 class="modal-title">Add Comment</h3>
          <button @click="closeCommentModal" class="modal-close">
            <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium mb-2">Workflow: {{ selectedApproval?.workflow_name }}</label>
              <p class="text-sm text-muted-foreground">Assigned by: {{ selectedApproval?.assigner_name }}</p>
            </div>
            <div class="space-y-2">
              <label class="block text-sm font-medium">Your Comment</label>
              <textarea 
                v-model="commentText" 
                class="input min-h-[100px]" 
                placeholder="Enter your comment or feedback here..."
                rows="4"
              ></textarea>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="closeCommentModal" class="btn btn--outline">Cancel</button>
          <button @click="submitComment" class="btn btn--primary" :disabled="!commentText.trim()">
            Submit Comment
          </button>
        </div>
      </div>
    </div>

    <!-- View Details Modal -->
    <div v-if="showViewModal" class="modal-overlay" @click="closeViewModal">
      <div class="modal-content modal-content--large" @click.stop>
        <div class="modal-header">
          <h3 class="modal-title">Approval Details</h3>
          <button @click="closeViewModal" class="modal-close">
            <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <div v-if="selectedApproval" class="space-y-6">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div class="space-y-4">
                <div>
                  <label class="block text-sm font-medium text-muted-foreground">Workflow Name</label>
                  <p class="text-lg font-medium">{{ selectedApproval.workflow_name }}</p>
                </div>
                <div>
                  <label class="block text-sm font-medium text-muted-foreground">Plan Type</label>
                  <span class="badge" :class="selectedApproval.plan_type === 'BCP' ? 'badge--success' : 'badge--info'">
                    {{ selectedApproval.plan_type }}
                  </span>
                </div>
                <div>
                  <label class="block text-sm font-medium text-muted-foreground">Object Type</label>
                  <span class="badge badge--outline">{{ selectedApproval.object_type }}</span>
                </div>
                <div>
                  <label class="block text-sm font-medium text-muted-foreground">Object ID</label>
                  <p class="font-mono">{{ selectedApproval.object_id }}</p>
                </div>
              </div>
              <div class="space-y-4">
                <div>
                  <label class="block text-sm font-medium text-muted-foreground">Assigned By</label>
                  <p>{{ selectedApproval.assigner_name }}</p>
                </div>
                <div>
                  <label class="block text-sm font-medium text-muted-foreground">Status</label>
                  <span class="status-badge" :class="`status-badge--${selectedApproval.status.toLowerCase().replace('_', '-')}`">
                    {{ selectedApproval.status.replace('_', ' ') }}
                  </span>
                </div>
                <div>
                  <label class="block text-sm font-medium text-muted-foreground">Assigned Date</label>
                  <p>{{ formatDate(selectedApproval.assigned_date) }}</p>
                </div>
                <div>
                  <label class="block text-sm font-medium text-muted-foreground">Due Date</label>
                  <p :class="{ 'text-red-600 font-medium': selectedApproval.is_overdue }">
                    {{ formatDate(selectedApproval.due_date) }}
                    <span v-if="selectedApproval.is_overdue" class="ml-2 text-sm">(Overdue)</span>
                  </p>
                </div>
              </div>
            </div>
            <div v-if="selectedApproval.comment_text">
              <label class="block text-sm font-medium text-muted-foreground mb-2">Comments</label>
              <div class="bg-muted p-4 rounded-lg">
                <p class="whitespace-pre-wrap">{{ selectedApproval.comment_text }}</p>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="closeViewModal" class="btn btn--outline">Close</button>
          <button 
            @click="updateStatus(selectedApproval, 'IN_PROGRESS')" 
            class="btn btn--primary"
            v-if="selectedApproval.status === 'ASSIGNED'"
          >
            Start Working
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'
import api from '../../services/api_bcp.js'
import { useNotifications } from '@/composables/useNotifications'
import { PopupService } from '@/popup/popupService'
import loggingService from '@/services/loggingService'

export default {
  name: 'MyApprovals',
  setup() {
    const store = useStore()
    const router = useRouter()
    const { showSuccess, showError, showWarning, showInfo } = useNotifications()
    
    // Reactive data
    const approvals = ref([])
    const isLoadingApprovals = ref(false)
    const userInfo = ref(null)
    const users = ref([])
    const isLoadingUsers = ref(false)
    const filters = ref({
      search: '',
      status: '',
      plan_type: '',
      object_type: '',
      user_id: ''
    })
    
    // Modal states
    const showCommentModal = ref(false)
    const showViewModal = ref(false)
    const selectedApproval = ref(null)
    const commentText = ref('')
    
    // Object type toggle state
    const selectedObjectType = ref('ALL')
    const objectTypes = [
      { value: 'ALL', label: 'All' },
      { value: 'PLAN EVALUATION', label: 'Plan Evaluation' },
      { value: 'NEW QUESTIONNAIRE', label: 'New Questionnaire' },
      { value: 'QUESTIONNAIRE RESPONSE', label: 'Questionnaire Response' }
    ]

    // Computed properties for statistics
    const totalApprovals = computed(() => approvals.value.length)
    const pendingApprovals = computed(() => 
      approvals.value.filter(a => a.status === 'ASSIGNED' || a.status === 'IN_PROGRESS').length
    )
    const overdueApprovals = computed(() => 
      approvals.value.filter(a => a.is_overdue).length
    )
    const completedApprovals = computed(() => 
      approvals.value.filter(a => a.status === 'COMMENTED' || a.status === 'SKIPPED').length
    )
    
    // Filtered approvals based on selected object type
    const filteredApprovals = computed(() => {
      if (selectedObjectType.value === 'ALL') {
        return approvals.value
      }
      return approvals.value.filter(a => a.object_type === selectedObjectType.value)
    })
    
    // Get count of approvals by type
    const getApprovalCountByType = (type) => {
      if (type === 'ALL') {
        return approvals.value.length
      }
      return approvals.value.filter(a => a.object_type === type).length
    }

    // Methods
    const fetchUsers = async () => {
      isLoadingUsers.value = true
      try {
        console.log('Fetching users from API endpoint: /api/bcpdrp/users/')
        const response = await api.users.list()
        
        console.log('API response data:', response)
        
        // Check if users are in response.users (unwrapped by interceptor) or response.data?.users
        const usersData = response.users || response.data?.users
        console.log('Users found:', usersData)
        
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

    const fetchMyApprovals = async () => {
      isLoadingApprovals.value = true
      try {
        const params = new URLSearchParams()
        if (filters.value.search) params.append('search', filters.value.search)
        if (filters.value.status) params.append('status', filters.value.status)
        if (filters.value.plan_type) params.append('plan_type', filters.value.plan_type)
        if (filters.value.object_type) params.append('object_type', filters.value.object_type)
        if (filters.value.user_id) params.append('user_id', filters.value.user_id)

        const response = await api.approvals.myApprovals(Object.fromEntries(params))
        
        // The HTTP interceptor unwraps the response, so we access data directly
        if (response.data && response.data.approvals !== undefined) {
          approvals.value = response.data.approvals || []
          userInfo.value = response.data.user_info || null
        } else {
          console.error('Failed to fetch approvals:', response.data?.message || 'Unknown error')
          console.error('Full error response:', response.data)
          // Remove the notification dispatch since the action doesn't exist
          // store.dispatch('showNotification', {
          //   type: 'error',
          //   message: response.data.message || 'Failed to fetch approvals'
          // })
        }
      } catch (error) {
        console.error('Error fetching my approvals:', error)
        console.error('Error details:', error.response?.data)
        // Remove the notification dispatch since the action doesn't exist
        // store.dispatch('showNotification', {
        //   type: 'error',
        //   message: 'Failed to fetch approvals. Please try again.'
        // })
      } finally {
        isLoadingApprovals.value = false
      }
    }

    const formatDate = (dateString) => {
      if (!dateString) return 'N/A'
      try {
        const date = new Date(dateString)
        return date.toLocaleDateString('en-US', {
          year: 'numeric',
          month: 'short',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit'
        })
      } catch (error) {
        return 'Invalid Date'
      }
    }

    const formatDateShort = (dateString) => {
      if (!dateString) return 'N/A'
      try {
        const date = new Date(dateString)
        return date.toLocaleDateString('en-US', {
          year: 'numeric',
          month: '2-digit',
          day: '2-digit'
        })
      } catch (error) {
        return 'Invalid Date'
      }
    }

    const getObjectTypeLabel = (objectType) => {
      const labels = {
        'PLAN EVALUATION': 'Plan Review',
        'NEW QUESTIONNAIRE': 'Questionnaire Review',
        'QUESTIONNAIRE RESPONSE': 'Evaluation Approval'
      }
      return labels[objectType] || objectType
    }

    const getPriorityLabel = (approval) => {
      if (approval.is_overdue) return 'High'
      if (approval.days_until_due <= 2 && approval.days_until_due > 0) return 'High'
      if (approval.days_until_due <= 7 && approval.days_until_due > 2) return 'Normal'
      return 'Low'
    }

    const getPriorityBadgeClass = (approval) => {
      if (approval.is_overdue) return 'badge--priority-high'
      if (approval.days_until_due <= 2 && approval.days_until_due > 0) return 'badge--priority-high'
      if (approval.days_until_due <= 7 && approval.days_until_due > 2) return 'badge--priority-normal'
      return 'badge--priority-low'
    }

    const getDueDateClass = (approval) => {
      if (approval.is_overdue) return 'approval-card__due-text--overdue'
      if (approval.days_until_due <= 2 && approval.days_until_due > 0) return 'approval-card__due-text--urgent'
      return ''
    }

    const viewApproval = (approval) => {
      selectedApproval.value = approval
      showViewModal.value = true
    }

    const addComment = (approval) => {
      selectedApproval.value = approval
      commentText.value = approval.comment_text || ''
      showCommentModal.value = true
      if (showViewModal.value) {
        showViewModal.value = false
      }
    }

    const updateStatus = async (approval, newStatus) => {
      try {
        console.log(`Updating approval ${approval.approval_id} to status ${newStatus}`)
        
        // Call API to update approval status
        const response = await api.approvals.updateStatus(approval.approval_id, {
          status: newStatus,
          comment_text: approval.comment_text || ''
        })
        
        console.log('Approval status update response:', response)
        
        // Update local state
        const index = approvals.value.findIndex(a => a.approval_id === approval.approval_id)
        if (index !== -1) {
          approvals.value[index].status = newStatus
          if (response.data) {
            // Update any other fields from response if needed
            if (response.data.new_status) {
              approvals.value[index].status = response.data.new_status
            }
          }
        }
        
        console.log(`Approval status updated to ${newStatus.replace('_', ' ')}`)
        
        // Show success notification
        await showSuccess('Status Updated', `Approval status updated to ${newStatus.replace('_', ' ')}.`, {
          action: 'approval_status_updated',
          approval_id: approval.approval_id,
          new_status: newStatus,
          object_type: approval.object_type
        })
        
        // Show success popup
        PopupService.success(`Approval status updated to ${newStatus.replace('_', ' ')}.`, 'Status Updated')
        
        // Navigate based on object type when status is IN_PROGRESS
        if (newStatus === 'IN_PROGRESS') {
          if (approval.object_type === 'PLAN EVALUATION') {
            navigateToPlanEvaluation(approval)
          } else if (approval.object_type === 'NEW QUESTIONNAIRE') {
            navigateToQuestionnaireBuilder(approval)
          } else if (approval.object_type === 'QUESTIONNAIRE RESPONSE') {
            navigateToAssignmentAnswering(approval)
          }
        }
      } catch (error) {
        console.error('Error updating approval status:', error)
        
        // Show error notification
        await showError('Update Failed', 'Failed to update approval status. Please try again.', {
          action: 'approval_status_update_failed',
          approval_id: approval.approval_id,
          new_status: newStatus,
          error_message: error.message
        })
        
        // Show error popup
        const errorMessage = error.response?.data?.message || error.message || 'Failed to update approval status. Please try again.'
        PopupService.error(errorMessage, 'Update Failed')
      }
    }

    const submitComment = async () => {
      if (!commentText.value.trim()) return

      try {
        console.log(`Submitting comment for approval ${selectedApproval.value.approval_id}:`, commentText.value)
        
        // Call API to update approval status to COMMENTED with comment
        const response = await api.approvals.updateStatus(selectedApproval.value.approval_id, {
          status: 'COMMENTED',
          comment_text: commentText.value
        })
        
        console.log('Comment submission response:', response)
        
        // Update local state
        const index = approvals.value.findIndex(a => a.approval_id === selectedApproval.value.approval_id)
        if (index !== -1) {
          approvals.value[index].comment_text = commentText.value
          approvals.value[index].status = 'COMMENTED'
        }
        
        console.log('Comment submitted successfully')
        
        // Show success message
        PopupService.success('Review comment submitted successfully. Questionnaire has been approved.', 'Comment Submitted')
        
        // Refresh approvals list to get updated data
        await fetchMyApprovals()
        
        closeCommentModal()
      } catch (error) {
        console.error('Error submitting comment:', error)
        const errorMessage = error.response?.data?.message || error.message || 'Failed to submit comment. Please try again.'
        PopupService.error(errorMessage, 'Submission Failed')
      }
    }

    const closeCommentModal = () => {
      showCommentModal.value = false
      selectedApproval.value = null
      commentText.value = ''
    }

    const closeViewModal = () => {
      showViewModal.value = false
      selectedApproval.value = null
    }

    const navigateToPlanEvaluation = (approval) => {
      // Navigate to plan evaluation page with the plan ID as query parameter
      router.push({
        path: '/bcp/evaluation',
        query: {
          planId: approval.object_id
        }
      })
    }

    const navigateToQuestionnaireBuilder = (approval) => {
      // Navigate to questionnaire builder page with the questionnaire ID as query parameter
      router.push({
        path: '/bcp/questionnaire-builder',
        query: {
          questionnaireId: approval.object_id
        }
      })
    }

    const navigateToAssignmentAnswering = (approval) => {
      // Navigate to questionnaire assignment page with the assignment ID as query parameter
      // This will open the assignment in answering mode
      router.push({
        path: '/bcp/questionnaire-assignment',
        query: {
          assignmentId: approval.object_id
        }
      })
    }

    // Lifecycle
    onMounted(async () => {
      await loggingService.logPageView('BCP', 'My Approvals')
      await fetchUsers()
      await fetchMyApprovals()
    })

    return {
      // Data
      approvals,
      isLoadingApprovals,
      userInfo,
      users,
      isLoadingUsers,
      filters,
      showCommentModal,
      showViewModal,
      selectedApproval,
      commentText,
      
      // Computed
      totalApprovals,
      pendingApprovals,
      overdueApprovals,
      completedApprovals,
      
      // Methods
      fetchUsers,
      fetchMyApprovals,
      formatDate,
      formatDateShort,
      getObjectTypeLabel,
      getPriorityLabel,
      getPriorityBadgeClass,
      getDueDateClass,
      viewApproval,
      addComment,
      updateStatus,
      submitComment,
      closeCommentModal,
      closeViewModal,
      navigateToPlanEvaluation,
      navigateToQuestionnaireBuilder,
      navigateToAssignmentAnswering,
      selectedObjectType,
      objectTypes,
      filteredApprovals,
      getApprovalCountByType
    }
  }
}
</script>

<style src="./MyApprovals.css"></style>
