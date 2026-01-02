<template>
  <!-- Show Access Denied if user doesn't have SubmitVendorForApproval permission -->
  <AccessDenied 
    v-if="!hasAccess"
    :message="accessDeniedInfo.message"
    :errorCode="accessDeniedInfo.code"
    :permission="accessDeniedInfo.permission"
  />
  
  <!-- Show content only if user has permission -->
  <div v-else class="vendor_space-y-6">
    <div class="vendor_flex vendor_items-end vendor_gap-4">
      <div class="vendor_w-64">
        <label class="vendor_block vendor_text-sm vendor_text-muted-foreground vendor_mb-1">Stage Type</label>
        <select v-model="stageType" class="vendor_input" @change="loadData">
          <option value="All">All</option>
          <option value="Parallel">Team Approval</option>
          <option value="Sequential">Tiered Approval</option>
        </select>
      </div>
      <button class="vendor_btn vendor_btn-primary" @click="loadData" :disabled="loading">
        {{ loading ? 'Loading...' : 'Load' }}
      </button>
    </div>

    <div class="vendor_card">
      <div class="vendor_card-header">
        <h2 class="vendor_card-title">All Approvals</h2>
        <p class="vendor_card-description">Requests created by the current user</p>
      </div>
      <div class="vendor_card-content">
        <div v-if="approvals.length === 0" class="vendor_text-sm vendor_text-muted-foreground">No records</div>
        <div v-else class="vendor_overflow-x-auto">
          <table class="vendor_table">
            <thead>
              <tr>
                <th>Approval ID</th>
                <th>Title</th>
                <th>Priority</th>
                <th>Status</th>
                <th>Submission</th>
                <th>Stage Count</th>
                <th>Workflow Type</th>
                <th>View</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in approvals" :key="r.approval_id">
                <td>{{ r.approval_id }}</td>
                <td>{{ r.request_title }}</td>
                <td>{{ r.priority }}</td>
                <td>{{ r.overall_status }}</td>
                <td>{{ formatDate(r.submission_date) }}</td>
                <td>{{ r.stage_count }}</td>
                <td>{{ formatFlowType(r.flow_type) }}</td>
                <td>
                  <button class="vendor_btn vendor_btn-outline vendor_btn-sm" @click="viewRequest(r)">
                    View
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'
import api from '@/utils/api'
import loggingService from '@/services/loggingService'
import { useVendorPermissions } from '@/composables/useVendorPermissions'
import AccessDenied from '@/components/AccessDenied.vue'
import permissionsService from '@/services/permissionsService'
import { getTprmApiUrl } from '@/utils/backendEnv'

// API base URL for vendor-approval endpoints
const VENDOR_APPROVAL_API_BASE_URL = getTprmApiUrl('vendor-approval')

// Initialize RBAC permissions
const { permissions, showDeniedAlert } = useVendorPermissions()

// Check if user has permission to access this page
const hasAccess = ref(false)
const accessDeniedInfo = ref({
  message: 'You do not have permission to access this page',
  code: '403',
  permission: 'SubmitVendorForApproval',
  permissionRequired: 'vendor_create'
})

const stageType = ref('All')
const approvals = ref([])
const loading = ref(false)
const router = useRouter()
const users = ref([])
const selectedRequesterId = ref('')

// Get current user from localStorage with Vuex fallback
const getCurrentUserId = () => {
  try {
    console.log('=== USER ID RESOLUTION DEBUG ===')
    
    // First, try to get user from Vuex store (most reliable source)
    try {
      const store = useStore()
      const vuexUser = store.getters['auth/currentUser']
      console.log('Vuex store user:', vuexUser)
      console.log('Vuex store user ID:', vuexUser?.id)
      
      if (vuexUser && vuexUser.id) {
        console.log('✅ Using Vuex store user ID:', vuexUser.id)
        return vuexUser.id
      }
    } catch (vuexError) {
      console.log('Could not access Vuex store:', vuexError.message)
    }
    
    // Fallback to localStorage if Vuex store is not available
    console.log('Vuex store not available, trying localStorage...')
    const currentUserFromStorage = localStorage.getItem('current_user')
    console.log('localStorage.getItem("current_user"):', currentUserFromStorage)
    
    if (currentUserFromStorage) {
      const user = JSON.parse(currentUserFromStorage)
      console.log('Parsed currentUser object:', user)
      
      // Try multiple possible user ID field names (including UserId with capital U)
      const userId = user.UserId || user.id || user.user_id || user.userId || user.userid
      console.log('Available userId from localStorage:', userId)
      
      if (userId) {
        console.log('✅ Using localStorage userId:', userId)
        return userId
      }
    }
    
    console.log('❌ No user ID found in localStorage or Vuex store')
    return null
  } catch (error) {
    console.error('Error getting current user:', error)
    return null
  }
}

const loadUsers = async () => {
  try {
    const res = await api.get(`${VENDOR_APPROVAL_API_BASE_URL}/users/`)
    users.value = Array.isArray(res.data) ? res.data : []
  } catch (e) {
    console.warn('Failed to load users endpoint, will fallback to reviewers:', e?.message)
    users.value = []
  }

  // Fallback to reviewers list if users empty
  if (!users.value.length) {
    try {
      const r = await api.get(`${VENDOR_APPROVAL_API_BASE_URL}/stages/reviewers/`)
      users.value = (r.data || []).map(x => ({ id: x.id, UserName: x.name }))
    } catch (e) {
      console.error('Failed to load reviewers fallback:', e?.message)
      users.value = []
    }
  }

  if (users.value.length && !selectedRequesterId.value) {
    selectedRequesterId.value = users.value[0].id || users.value[0].UserId
  }
}

const loadData = async () => {
  const currentUserId = getCurrentUserId()
  if (!currentUserId) {
    console.error('No current user found in localStorage or Vuex store')
    console.error('User may not be properly logged in. Please refresh the page or log in again.')
    return
  }
  
  loading.value = true
  try {
    console.log('Loading approvals for user ID:', currentUserId)
    const res = await api.get(`${VENDOR_APPROVAL_API_BASE_URL}/requests/by-requester/`, {
      params: { requester_id: Number(currentUserId), stage_type: stageType.value }
    })
    console.log('Approvals API response:', res.data)
    approvals.value = res.data || []
    console.log('Loaded approvals:', approvals.value.length)
  } catch (e) {
    console.error('Error loading approvals:', e)
    approvals.value = []
  } finally {
    loading.value = false
  }
}

const formatDate = (d) => {
  if (!d) return ''
  try { return new Date(d).toLocaleString() } catch { return d }
}

const formatFlowType = (flowType) => {
  if (!flowType) return 'Unknown'
  const type = String(flowType).toLowerCase()
  if (type === 'parallel') return 'Team Approval'
  if (type === 'sequential') return 'Tiered Approval'
  return flowType
}

const viewRequest = (row) => {
  const currentUserId = getCurrentUserId()
  router.push({
    name: 'Vendor Assignee Decision',
    query: {
      requester_id: currentUserId,
      approval_id: row.approval_id,
      flow_type: row.flow_type
    }
  })
}

onMounted(async () => {
  console.log('AllApprovals component mounted')
  
  // Check permission before loading data
  // User must have SubmitVendorForApproval permission to view their approval requests
  // First check localStorage, then check backend API if needed
  let hasPermission = permissions.value.canSubmitForApproval
  
  // If permission check from localStorage returns false, try fetching from backend
  if (!hasPermission) {
    console.log('Permission not found in localStorage, checking backend API...')
    try {
      // Check backend API for the permission
      hasPermission = await permissionsService.checkVendorPermission('submit_vendor_for_approval')
      console.log('Backend permission check result:', hasPermission)
      
      // If we got permission from backend, update localStorage
      if (hasPermission) {
        // Update user object in localStorage with permission
        const userStr = localStorage.getItem('current_user') || localStorage.getItem('user')
        if (userStr) {
          try {
            const user = JSON.parse(userStr)
            if (!user.permissions) {
              user.permissions = {}
            }
            user.permissions.SubmitVendorForApproval = true
            localStorage.setItem('current_user', JSON.stringify(user))
            console.log('Updated localStorage with permission')
          } catch (e) {
            console.error('Error updating localStorage:', e)
          }
        }
      }
    } catch (error) {
      console.error('Error checking permission from backend:', error)
      hasPermission = false
    }
  }
  
  if (!hasPermission) {
    console.warn('Access denied: User does not have SubmitVendorForApproval permission')
    hasAccess.value = false
    
    // Store error info in sessionStorage for AccessDenied component
    sessionStorage.setItem('access_denied_error', JSON.stringify({
      message: 'You do not have permission to access the All Approvals page. This page requires the permission to create workflows.',
      code: '403',
      path: router.currentRoute.value.path,
      permission: 'SubmitVendorForApproval',
      permissionRequired: 'vendor_create'
    }))
    
    return
  }
  
  hasAccess.value = true
  await loggingService.logPageView('Vendor', 'All Approvals')
  await loadData()
})
</script>

<style scoped>
/* Base styles for vendor components */
.vendor_input { 
  padding: 0.5rem 0.75rem; 
  border: 1px solid #e5e7eb; 
  border-radius: 0.375rem; 
  background: #ffffff; 
  color: #374151; 
  width: 100%;
  box-sizing: border-box;
}

.vendor_btn {
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  border: 1px solid transparent;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.vendor_btn-primary {
  background: #3b82f6;
  color: #ffffff;
  border-color: #3b82f6;
}

.vendor_btn-primary:hover:not(:disabled) {
  background: #2563eb;
  border-color: #2563eb;
}

.vendor_btn-primary:disabled {
  background: #9ca3af;
  border-color: #9ca3af;
  cursor: not-allowed;
}

.vendor_btn-outline {
  background: #ffffff;
  color: #374151;
  border-color: #d1d5db;
}

.vendor_btn-outline:hover {
  background: #f9fafb;
  border-color: #9ca3af;
}

.vendor_btn-sm {
  padding: 0.25rem 0.75rem;
  font-size: 0.875rem;
}

.vendor_card { 
  border: 1px solid #e5e7eb; 
  border-radius: 0.5rem; 
  background: #ffffff; 
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.vendor_card-header { 
  padding: 0.75rem 1rem; 
  border-bottom: 1px solid #e5e7eb; 
  background: #f9fafb;
}

.vendor_card-title { 
  font-weight: 600; 
  font-size: 1.125rem;
  color: #111827;
  margin: 0;
}

.vendor_card-description { 
  font-size: 0.875rem; 
  color: #6b7280; 
  margin: 0.25rem 0 0 0;
}

.vendor_card-content { 
  padding: 0.75rem 1rem; 
}

/* Table styles */
.vendor_table { 
  width: 100%; 
  border-collapse: collapse; 
  font-size: 0.875rem;
}

.vendor_table th, 
.vendor_table td { 
  text-align: left; 
  border-bottom: 1px solid #e5e7eb; 
  padding: 0.75rem 0.5rem; 
}

.vendor_table th {
  background: #f9fafb;
  font-weight: 600;
  color: #374151;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.vendor_table td {
  color: #6b7280;
}

.vendor_table tbody tr:hover {
  background: #f9fafb;
}

/* Utility classes */
.vendor_space-y-6 > * + * { margin-top: 1.5rem; }
.vendor_flex { display: flex; }
.vendor_items-end { align-items: flex-end; }
.vendor_gap-4 { gap: 1rem; }
.vendor_w-64 { width: 16rem; }
.vendor_block { display: block; }
.vendor_text-sm { font-size: 0.875rem; }
.vendor_text-muted-foreground { color: #6b7280; }
.vendor_mb-1 { margin-bottom: 0.25rem; }
.vendor_overflow-x-auto { overflow-x: auto; }

/* Responsive design */
@media (max-width: 768px) {
  .vendor_flex.vendor_items-end {
    flex-direction: column;
    align-items: stretch;
    gap: 0.75rem;
  }
  
  .vendor_w-64 {
    width: 100%;
  }
  
  .vendor_table {
    font-size: 0.75rem;
  }
  
  .vendor_table th,
  .vendor_table td {
    padding: 0.5rem 0.25rem;
  }
}
</style>


