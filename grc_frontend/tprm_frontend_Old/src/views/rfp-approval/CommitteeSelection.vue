<template>
  <div class="h-screen flex flex-col bg-gray-50">
    <!-- Header -->
    <div class="bg-white border-b border-gray-200 px-6 py-4">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-xl font-semibold text-gray-900">Committee Member Selection</h2>
          <p class="text-sm text-gray-600 mt-1">{{ rfpData?.rfp_title || 'Loading...' }}</p>
          <p class="text-xs text-gray-500">RFP #{{ rfpData?.rfp_number }}</p>
          <div class="mt-2 flex items-center space-x-2">
            <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
              📝 Local Storage Mode
            </span>
            <span class="text-xs text-gray-500">Committee data saved locally</span>
          </div>
        </div>
        <div class="flex items-center space-x-3">
          <button 
            @click="saveCommittee" 
            :disabled="saving || selectedMembers.length === 0"
            class="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-lg hover:bg-blue-700 transition-all duration-200 shadow-sm disabled:opacity-50"
          >
            <span class="mr-2">💾</span>
            {{ saving ? 'Saving...' : 'Save Committee' }}
          </button>
          <button 
            @click="navigateBack" 
            class="inline-flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-all duration-200 shadow-sm"
          >
            <span class="mr-2">←</span>
            Back
          </button>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="flex-1 flex overflow-hidden">
      <!-- Left Panel - Available Members -->
      <div class="flex-1 overflow-y-auto bg-white border-r border-gray-200">
        <div class="p-6">
          <!-- Search and Filters -->
          <div class="mb-6">
            <div class="flex items-center space-x-4">
              <div class="flex-1">
                <input
                  v-model="searchQuery"
                  type="text"
                  placeholder="Search members by name, email, or department..."
                  class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div class="flex items-center space-x-2">
                <label class="text-sm font-medium text-gray-700">Department:</label>
                <select 
                  v-model="departmentFilter" 
                  @change="applyFilters"
                  class="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">All Departments</option>
                  <option v-for="dept in departments" :key="dept" :value="dept">{{ dept }}</option>
                </select>
              </div>
            </div>
          </div>

          <!-- Available Members List -->
          <div class="space-y-3">
            <div class="flex items-center justify-between">
              <h3 class="text-lg font-semibold text-gray-900">Available Members</h3>
              <span class="text-sm text-gray-600">{{ filteredMembers.length }} member(s) available</span>
            </div>

            <div v-if="filteredMembers.length > 0" class="space-y-2">
              <div 
                v-for="member in filteredMembers" 
                :key="member.user_id"
                class="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-all duration-200"
                :class="{
                  'border-blue-300 bg-blue-50': selectedMembers.some(m => m.user_id === member.user_id),
                  'border-gray-200': !selectedMembers.some(m => m.user_id === member.user_id)
                }"
              >
                <div class="flex items-center justify-between">
                  <div class="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      :checked="selectedMembers.some(m => m.user_id === member.user_id)"
                      @change="toggleMemberSelection(member)"
                      class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <div class="flex-1">
                      <div class="flex items-center space-x-2">
                        <h4 class="text-sm font-semibold text-gray-900">
                          {{ member.first_name }} {{ member.last_name }}
                        </h4>
                        <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                          {{ member.username }}
                        </span>
                      </div>
                      <p class="text-sm text-gray-600">{{ member.email }}</p>
                      <div class="flex items-center space-x-4 mt-1">
                        <span class="text-xs text-gray-500">
                          Department: {{ member.department_id || 'Not specified' }}
                        </span>
                        <span class="text-xs text-gray-500">
                          Status: {{ member.is_active === 'Y' ? 'Active' : 'Inactive' }}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  <div v-if="selectedMembers.some(m => m.user_id === member.user_id)" class="flex items-center space-x-2">
                    <button 
                      @click="setAsChair(member)"
                      :class="[
                        'px-3 py-1 text-xs font-medium rounded-md transition-colors',
                        selectedMembers.find(m => m.user_id === member.user_id)?.is_chair 
                          ? 'bg-yellow-100 text-yellow-800 hover:bg-yellow-200' 
                          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                      ]"
                    >
                      {{ selectedMembers.find(m => m.user_id === member.user_id)?.is_chair ? '👑 Chair' : 'Set as Chair' }}
                    </button>
                    <button 
                      @click="removeMember(member)"
                      class="px-3 py-1 text-xs font-medium text-red-600 bg-red-50 rounded-md hover:bg-red-100 transition-colors"
                    >
                      Remove
                    </button>
                  </div>
                </div>
              </div>
            </div>
            
            <div v-else class="text-center py-8 text-gray-500">
              <span class="text-4xl mb-4 text-gray-400">👥</span>
              <p>No members found matching your criteria</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Right Panel - Selected Committee -->
      <div class="w-96 overflow-y-auto bg-gray-50">
        <div class="p-6">
          <h3 class="text-lg font-medium text-gray-900 mb-6">Selected Committee</h3>
          
          <!-- Committee Summary -->
          <div class="bg-white rounded-lg border border-gray-200 p-4 mb-6">
            <h4 class="text-sm font-semibold text-gray-900 mb-3">Committee Summary</h4>
            <div class="space-y-2">
              <div class="flex justify-between text-sm">
                <span class="text-gray-600">Total Members:</span>
                <span class="font-medium">{{ selectedMembers.length }}</span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-gray-600">Chair Selected:</span>
                <span class="font-medium" :class="hasChair ? 'text-green-600' : 'text-red-600'">
                  {{ hasChair ? 'Yes' : 'No' }}
                </span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-gray-600">Departments:</span>
                <span class="font-medium">{{ uniqueDepartments.length }}</span>
              </div>
            </div>
          </div>

          <!-- Selected Members -->
          <div class="space-y-4">
            <h4 class="text-sm font-semibold text-gray-900">Selected Members</h4>
            
            <div v-if="selectedMembers.length > 0" class="space-y-3">
              <div 
                v-for="member in selectedMembers" 
                :key="member.user_id"
                class="bg-white rounded-lg border border-gray-200 p-3"
                :class="{
                  'border-yellow-300 bg-yellow-50': member.is_chair
                }"
              >
                <div class="flex items-center justify-between">
                  <div class="flex items-center space-x-2">
                    <span v-if="member.is_chair" class="text-yellow-600">👑</span>
                    <div>
                      <h5 class="text-sm font-semibold text-gray-900">
                        {{ member.first_name }} {{ member.last_name }}
                      </h5>
                      <p class="text-xs text-gray-600">{{ member.email }}</p>
                      <p class="text-xs text-gray-500">{{ member.department_id || 'No department' }}</p>
                    </div>
                  </div>
                  <div class="flex items-center space-x-1">
                    <button 
                      v-if="!member.is_chair"
                      @click="setAsChair(member)"
                      class="px-2 py-1 text-xs font-medium text-yellow-600 bg-yellow-50 rounded hover:bg-yellow-100"
                      title="Set as Chair"
                    >
                      👑
                    </button>
                    <button 
                      @click="removeMember(member)"
                      class="px-2 py-1 text-xs font-medium text-red-600 bg-red-50 rounded hover:bg-red-100"
                      title="Remove"
                    >
                      ✕
                    </button>
                  </div>
                </div>
              </div>
            </div>
            
            <div v-else class="text-center py-8 text-gray-500">
              <span class="text-4xl mb-4 text-gray-400">👥</span>
              <p>No committee members selected</p>
              <p class="text-sm">Select members from the left panel to build your committee</p>
            </div>
          </div>

          <!-- Committee Guidelines -->
          <div class="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 class="text-sm font-semibold text-blue-900 mb-2">Committee Guidelines</h4>
            <ul class="text-xs text-blue-800 space-y-1">
              <li>• Select 3-7 members for optimal decision-making</li>
              <li>• Include members from different departments</li>
              <li>• Ensure at least one member has technical expertise</li>
              <li>• Designate one member as committee chair</li>
              <li>• All members should be available for evaluation period</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Popup Modal -->
  <PopupModal />
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useRfpApi } from '@/composables/useRfpApi'
import { getTprmApiUrl, getApiOrigin } from '@/utils/backendEnv'
import PopupModal from '@/popup/PopupModal.vue'
import { PopupService } from '@/popup/popupService'
import { useNotifications } from '@/composables/useNotifications'
import loggingService from '@/services/loggingService'

const router = useRouter()

// API base URL
const API_BASE_URL = 'https://grc-tprm.vardaands.com/api/tprm/rfp'

// Get auth headers once at the top level
const { getAuthHeaders } = useRfpApi()

// State
const { showSuccess, showError, showWarning, showInfo } = useNotifications()

const rfpData = ref(null)
const availableMembers = ref([])
const selectedMembers = ref([])
const searchQuery = ref('')
const departmentFilter = ref('')
const saving = ref(false)

// Computed properties
const filteredMembers = computed(() => {
  let filtered = availableMembers.value

  // Filter by search query
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(member => 
      member.first_name.toLowerCase().includes(query) ||
      member.last_name.toLowerCase().includes(query) ||
      member.email.toLowerCase().includes(query) ||
      member.username.toLowerCase().includes(query)
    )
  }

  // Filter by department
  if (departmentFilter.value) {
    filtered = filtered.filter(member => 
      member.department_id === departmentFilter.value
    )
  }

  // Exclude already selected members
  const selectedIds = selectedMembers.value.map(m => m.user_id)
  filtered = filtered.filter(member => !selectedIds.includes(member.user_id))

  return filtered
})

const departments = computed(() => {
  const depts = [...new Set(availableMembers.value.map(m => m.department_id).filter(Boolean))]
  return depts.sort()
})

const hasChair = computed(() => {
  return selectedMembers.value.some(member => member.is_chair)
})

const uniqueDepartments = computed(() => {
  const depts = selectedMembers.value.map(m => m.department_id).filter(Boolean)
  return [...new Set(depts)]
})

// Methods
const loadRFPData = async () => {
  try {
    const urlParams = new URLSearchParams(window.location.search)
    const rfpId = urlParams.get('rfp_id')
    
    console.log('Loading RFP data for ID:', rfpId)
    
    if (!rfpId) {
      console.error('No RFP ID provided')
      PopupService.error('No RFP ID provided', 'No RFP ID')
      PopupService.onAction('ok', () => {
        router.push('/my-approvals')
      })
      return
    }
    
    const response = await fetch(`${API_BASE_URL}/rfps/${rfpId}/`, {
      method: 'GET',
      headers: getAuthHeaders()
    })
    console.log('RFP API response status:', response.status)
    
    if (response.ok) {
      rfpData.value = await response.json()
      console.log('RFP data loaded:', rfpData.value)
    } else {
      console.error('Failed to load RFP data:', response.status, response.statusText)
    }
  } catch (error) {
    console.error('Error loading RFP data:', error)
  }
}

const loadAvailableMembers = async () => {
  try {
    console.log('Loading available members from database...')
    const response = await fetch(`${API_BASE_URL}/users/?t=` + Date.now(), {
      method: 'GET',
      headers: getAuthHeaders()
    })
    console.log('Users API response status:', response.status)
    
    if (response.ok) {
      const data = await response.json()
      console.log('Users API response data:', data)
      
      // Handle different response formats
      let users = []
      if (data.results) {
        // Paginated response
        users = data.results
      } else if (Array.isArray(data)) {
        // Direct array response
        users = data
      } else {
        console.error('Unexpected API response format:', data)
        PopupService.error('Unexpected response format from users API', 'Unexpected Format')
        return
      }
      
      // Filter active users
      availableMembers.value = users.filter(user => 
        user.is_active === 'Y' || user.is_active === true || user.is_active === 1
      )
      
      console.log('Loaded available members:', availableMembers.value.length)
      
      if (availableMembers.value.length === 0) {
        PopupService.warning('No active users found in the database. Please add users first.', 'No Users')
      }
    } else {
      console.error('Failed to load users:', response.status, response.statusText)
      PopupService.error('Failed to load users from database. Please check your connection.', 'Load Failed')
    }
  } catch (error) {
    console.error('Error loading available members:', error)
    PopupService.error('Error loading users from database. Please try again.', 'Loading Error')
  }
}

const loadExistingCommittee = async () => {
  try {
    const urlParams = new URLSearchParams(window.location.search)
    const rfpId = urlParams.get('rfp_id')
    
    if (!rfpId) return
    
    console.log('🔄 Loading existing committee for RFP:', rfpId)
    
    // Try to load from backend first
    try {
      const response = await fetch(`${API_BASE_URL}/rfp/${rfpId}/committee/get/`, {
        method: 'GET',
        headers: getAuthHeaders()
      })
      if (response.ok) {
        const data = await response.json()
        console.log('📋 Committee data from backend:', data)
        
        if (data.success && data.committee_members && Array.isArray(data.committee_members)) {
          // Map backend committee data to frontend format
          selectedMembers.value = data.committee_members.map(committee => ({
            user_id: committee.member_id,
            first_name: 'Committee', // We'll need to fetch user details separately
            last_name: 'Member',
            email: 'committee@company.com',
            username: `member_${committee.member_id}`,
            department_id: 'Committee',
            is_active: 'Y',
            member_role: committee.member_role,
            is_chair: committee.is_chair
          }))
          console.log('✅ Loaded committee from backend:', selectedMembers.value.length, 'members')
          return
        }
      }
    } catch (backendError) {
      console.log('⚠️ Backend load failed:', backendError)
    }
    
    // No fallback - rely only on database
    console.log('📝 No committee found in database for RFP:', rfpId)
    
    // If no data found, start with empty committee
    console.log('📝 Starting with empty committee - no existing data found')
    selectedMembers.value = []
    
  } catch (error) {
    console.error('Error loading existing committee:', error)
    selectedMembers.value = []
  }
}

const toggleMemberSelection = (member) => {
  const isSelected = selectedMembers.value.some(m => m.user_id === member.user_id)
  
  if (isSelected) {
    removeMember(member)
  } else {
    addMember(member)
  }
}

const addMember = (member) => {
  const newMember = {
    ...member,
    member_role: 'Committee Member',
    is_chair: false
  }
  selectedMembers.value.push(newMember)
}

const removeMember = (member) => {
  selectedMembers.value = selectedMembers.value.filter(m => m.user_id !== member.user_id)
}

const setAsChair = (member) => {
  // Remove chair status from all other members
  selectedMembers.value.forEach(m => {
    m.is_chair = false
  })
  
  // Set this member as chair
  const memberIndex = selectedMembers.value.findIndex(m => m.user_id === member.user_id)
  if (memberIndex !== -1) {
    selectedMembers.value[memberIndex].is_chair = true
  }
}

const applyFilters = () => {
  // Filters are applied automatically through computed property
}

const saveCommittee = async () => {
  if (selectedMembers.value.length === 0) {
    PopupService.warning('Please select at least one committee member', 'No Members Selected')
    return
  }
  
  if (!hasChair.value) {
    PopupService.warning('Please designate a committee chair', 'No Chair Designated')
    return
  }
  
  saving.value = true
  try {
    const urlParams = new URLSearchParams(window.location.search)
    const rfpId = urlParams.get('rfp_id')
    const addedBy = urlParams.get('added_by') || '1'
    
    if (!rfpId) {
      throw new Error('No RFP ID provided')
    }
    
    console.log('💾 Saving committee for RFP:', rfpId)
    console.log('👥 Selected members:', selectedMembers.value.length)
    
    // Get all submitted vendor response IDs for this RFP (committee will evaluate all submitted responses)
    let shortlistedResponseIds = []
    try {
      const shortlistResponse = await fetch(`${API_BASE_URL}/rfp-responses-list/?rfp_id=${rfpId}&t=` + Date.now(), {
        method: 'GET',
        headers: getAuthHeaders()
      })
      if (shortlistResponse.ok) {
        const shortlistData = await shortlistResponse.json()
        console.log('📋 Vendor responses data:', shortlistData)
        
        if (shortlistData.success && shortlistData.responses) {
          // Get all submitted responses (not just shortlisted ones)
          // Handle cases where submission_status might be empty or null
          const submittedResponses = shortlistData.responses.filter(response => 
            response.submission_status === 'SUBMITTED' || 
            response.evaluation_status === 'SUBMITTED' ||
            response.evaluation_status === 'UNDER_EVALUATION' ||
            response.evaluation_status === 'SHORTLISTED' ||
            !response.submission_status || // Include responses with empty/null status
            response.response_id // Include any response that has an ID (assume it's submitted)
          )
          shortlistedResponseIds = submittedResponses.map(vendor => vendor.response_id)
          console.log('📋 Found submitted responses:', shortlistedResponseIds.length)
        } else if (Array.isArray(shortlistData)) {
          shortlistedResponseIds = shortlistData.map(vendor => vendor.response_id)
          console.log('📋 Found responses (array format):', shortlistedResponseIds.length)
        }
      }
    } catch (error) {
      console.log('⚠️ Could not fetch vendor responses:', error)
    }
    
    // If no responses found, provide a fallback or show error
    if (shortlistedResponseIds.length === 0) {
      console.log('⚠️ No submitted responses found for RFP', rfpId)
      PopupService.warning('No submitted vendor responses found for this RFP. Please ensure vendors have submitted their proposals before creating a committee.', 'No Responses')
      return
    }
    
    // Prepare committee data for backend (rfp_id is passed as URL parameter)
    const committeeData = {
      committee_members: selectedMembers.value.map(member => ({
        member_id: member.user_id,
        member_role: member.member_role || 'Committee Member',
        is_chair: member.is_chair || false
      })),
      response_ids: shortlistedResponseIds,
      added_by: parseInt(addedBy)
    }
    
    console.log('📝 Saving committee data to backend:', committeeData)
    
    // Check if committee already exists
    const existingCommitteeResponse = await fetch(`${API_BASE_URL}/rfp/${rfpId}/committee/get/`, {
      method: 'GET',
      headers: getAuthHeaders()
    })
    if (existingCommitteeResponse.ok) {
      const existingCommitteeData = await existingCommitteeResponse.json()
      if (existingCommitteeData.success && existingCommitteeData.committee_members && existingCommitteeData.committee_members.length > 0) {
        console.log('⚠️ Committee already exists, updating instead of creating new one')
        // The backend will clear existing committee and create new one, so this is fine
      }
    }
    
    // Save committee data to backend
    const response = await fetch(`${API_BASE_URL}/rfp/${rfpId}/committee/`, {
      method: 'POST',
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify(committeeData)
    })
    
    if (response.ok) {
      const result = await response.json()
      console.log('✅ Committee data saved to database:', result)
      
      // Create workflow for committee evaluation (with duplicate prevention)
      try {
        await createCommitteeEvaluationWorkflow(rfpId, selectedMembers.value, shortlistedResponseIds)
      } catch (workflowError) {
        console.log('⚠️ Workflow creation failed, but committee is saved')
        PopupService.warning('Committee saved successfully, but workflow creation failed. You may need to create the workflow manually.', 'Partial Success')
      }
      
      PopupService.success(`Committee selection completed! ${selectedMembers.value.length} members selected and saved to database.`, 'Committee Saved')
      
      // Navigate back to the comparison page
      try {
        await router.push({
          path: '/rfp-comparison',
          query: { rfp_id: rfpId }
        })
      } catch (navigationError) {
        console.warn('CommitteeSelection: navigation to comparison failed, falling back to direct path', navigationError)
        window.location.href = `/rfp-comparison?rfp_id=${encodeURIComponent(rfpId)}`
      }
    } else {
      const errorText = await response.text()
      console.error('❌ Backend save failed:', errorText)
      throw new Error(`Failed to save committee to backend: ${errorText}`)
    }
    
  } catch (error) {
    console.error('❌ Error saving committee:', error)
    PopupService.error('Failed to save committee. Please try again.', 'Save Failed')
  } finally {
    saving.value = false
  }
}

const createCommitteeEvaluationWorkflow = async (rfpId, committeeMembers, responseIds) => {
  try {
    console.log('Creating committee evaluation workflow for RFP:', rfpId)
    console.log('Committee members:', committeeMembers)
    console.log('Response IDs:', responseIds)
    
    // Check if workflow already exists for this RFP
    const apiOrigin = getApiOrigin() || 'https://grc-tprm.vardaands.com'
    const existingWorkflowsResponse = await fetch(`${apiOrigin}/api/tprm/rfp-approval/workflows/`, {
      method: 'GET',
      headers: getAuthHeaders()
    })
    if (existingWorkflowsResponse.ok) {
      const existingWorkflows = await existingWorkflowsResponse.json()
      const committeeWorkflowExists = existingWorkflows.some(workflow => 
        workflow.workflow_name && workflow.workflow_name.includes(`Committee Evaluation - RFP ${rfpId}`)
      )
      
      if (committeeWorkflowExists) {
        console.log('⚠️ Committee evaluation workflow already exists for this RFP')
        return { success: true, message: 'Workflow already exists' }
      }
    }
    
    // Prepare workflow data
    const workflowData = {
      workflow_name: `Committee Evaluation - RFP ${rfpId}`,
      workflow_type: 'MULTI_PERSON', // Parallel workflow
      description: `Parallel committee evaluation workflow for RFP ${rfpId} with ${committeeMembers.length} committee members`,
      business_object_type: 'RFP', // Must be 'RFP' for integration.approval_workflows table
      is_active: true,
      created_by: 1, // Default user ID
      stages_config: [],
      rfp_data: {
        rfp_id: rfpId,
        response_ids: responseIds,
        committee_members: committeeMembers
      }
    }
    
    // Create stages for each committee member (parallel execution)
    committeeMembers.forEach((member, index) => {
      const stage = {
        stage_order: 0, // All stages run in parallel (order = 0)
        stage_name: `Committee Evaluation - ${member.first_name} ${member.last_name}`,
        stage_description: `Final committee evaluation by ${member.first_name} ${member.last_name} (${member.member_role})`,
        assigned_user_id: parseInt(member.user_id),
        assigned_user_name: `${member.first_name} ${member.last_name}`,
        assigned_user_role: member.member_role,
        department: member.department_id || 'Committee',
        stage_type: 'PARALLEL',
        deadline_date: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString(), // 14 days from now
        is_mandatory: true
      }
      workflowData.stages_config.push(stage)
    })
    
    console.log('Workflow data to be submitted:', workflowData)
    
    // Submit workflow to backend (reuse apiOrigin from above)
    const response = await fetch(`${apiOrigin}/api/tprm/rfp-approval/workflows/`, {
      method: 'POST',
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify(workflowData)
    })
    
    if (response.ok) {
      const result = await response.json()
      console.log('Committee evaluation workflow created successfully:', result)
      PopupService.success(`Committee evaluation workflow created! Workflow ID: ${result.workflow_id}`, 'Workflow Created')
      return result
    } else {
      const errorText = await response.text()
      console.error('Failed to create committee evaluation workflow:', errorText)
      throw new Error(`Failed to create workflow: ${errorText}`)
    }
  } catch (error) {
    console.error('Error creating committee evaluation workflow:', error)
    throw error
  }
}

const navigateBack = () => {
  router.push('/my-approvals')
}

onMounted(async () => {
  await loggingService.logPageView('RFP', 'Committee Selection')
  console.log('🔄 CommitteeSelection component mounted - Version 2.0')
  console.log('📍 URL params:', window.location.search)
  console.log('🕐 Timestamp:', new Date().toISOString())
  
  await loadRFPData()
  await loadAvailableMembers()
  await loadExistingCommittee()
})
</script>

<style scoped>
/* Custom checkbox styling */
input[type="checkbox"] {
  accent-color: #3b82f6;
}

/* Hover effects */
.hover\:shadow-md:hover {
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

/* Transition effects */
.transition-all {
  transition: all 0.2s ease-in-out;
}
</style>
