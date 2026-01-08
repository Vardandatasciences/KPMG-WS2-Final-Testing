<template>
  <div class="max-w-7xl mx-auto space-y-4 lg:space-y-6 p-4 lg:p-6">
    <!-- Header -->
    <div>
      <h1 class="text-2xl lg:text-3xl font-bold tracking-tight text-foreground">Create New Audit</h1>
      <p class="text-sm lg:text-base text-muted-foreground">Set up a new audit with contract selection, assignee configuration, and term evaluation</p>
    </div>

    <!-- Contract Selection -->
    <Card class="shadow-card">
      <CardHeader>
        <CardTitle class="flex items-center">
          <FileText class="mr-2 h-5 w-5 text-primary" />
          Contract Selection
        </CardTitle>
        <CardDescription>Choose an approved or active contract to audit</CardDescription>
      </CardHeader>
      <CardContent class="p-4 lg:p-6">
        <div class="space-y-4">
          <div>
            <Label for="contract-select">Select Contract</Label>
            <select 
              id="contract-select"
              v-model="selectedContractId" 
              @change="handleContractSelection"
              class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <option value="">Choose an approved or active contract to audit</option>
              <option 
                v-for="contract in availableContracts" 
                :key="contract.contract_id" 
                :value="contract.contract_id"
              >
                {{ contract.contract_title }} - {{ contract.vendor_name }}
              </option>
            </select>
          </div>

          <div v-if="selectedContract" class="p-3 lg:p-4 bg-muted/30 rounded-lg border">
            <h4 class="font-medium text-foreground mb-2 text-sm lg:text-base">Selected Contract Details</h4>
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-3 lg:gap-4 text-xs lg:text-sm">
              <div>
                <span class="text-muted-foreground">Title:</span>
                <span class="ml-2 font-medium">{{ selectedContract.contract_title }}</span>
              </div>
              <div>
                <span class="text-muted-foreground">Type:</span>
                <Badge variant="outline" class="ml-2">{{ selectedContract.contract_type }}</Badge>
              </div>
              <div>
                <span class="text-muted-foreground">Duration:</span>
                <span class="ml-2">{{ selectedContract.start_date }} to {{ selectedContract.end_date }}</span>
              </div>
              <div>
                <span class="text-muted-foreground">Terms:</span>
                <span class="ml-2 font-medium">{{ terms.length }} terms available</span>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- Audit Configuration -->
    <Card class="shadow-card">
      <CardHeader>
        <CardTitle class="flex items-center">
          <Target class="mr-2 h-5 w-5 text-primary" />
          Audit Configuration
        </CardTitle>
        <CardDescription>Configure basic audit parameters</CardDescription>
      </CardHeader>
      <CardContent class="p-4 lg:p-6">
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div>
            <Label for="audit-title">Audit Title *</Label>
            <Input
              id="audit-title"
              v-model="auditTitle"
              placeholder="Enter audit title"
            />
          </div>
          <div>
            <Label for="due-date">Due Date *</Label>
            <input
              id="due-date"
              type="date"
              :value="dueDate"
              @input="dueDate = $event.target.value"
              @change="handleDateChange"
              class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            />
          </div>
          <div>
            <Label for="frequency">Frequency</Label>
            <select 
              id="frequency"
              v-model="frequency"
              class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <option value="">Select frequency</option>
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
              <option value="quarterly">Quarterly</option>
              <option value="yearly">Yearly</option>
            </select>
          </div>
          <div>
            <Label for="audit-type">Audit Type</Label>
            <select 
              id="audit-type"
              v-model="auditType"
              class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <option value="">Select type</option>
              <option value="internal">Internal</option>
              <option value="external">External</option>
              <option value="self">Self Assessment</option>
            </select>
          </div>
          <div class="lg:col-span-2">
            <Label for="audit-scope">Audit Scope</Label>
            <textarea
              id="audit-scope"
              :value="auditScope"
              @input="auditScope = $event.target.value"
              @change="handleScopeChange"
              placeholder="Describe the scope and objectives of this audit"
              rows="3"
              class="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            />
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- Assignee Selection -->
    <Card class="shadow-card">
      <CardHeader>
        <CardTitle class="flex items-center">
          <Users class="mr-2 h-5 w-5 text-primary" />
          Assignee Selection
        </CardTitle>
        <CardDescription>Assign auditor and reviewer for this audit (Admin can assign to any user)</CardDescription>
      </CardHeader>
      <CardContent class="p-4 lg:p-6">
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div>
            <Label for="auditor-select">Auditor *</Label>
            <select 
              id="auditor-select"
              v-model="selectedAuditorId" 
              @change="handleAuditorSelection"
              class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <option value="">Select auditor</option>
              <option 
                v-for="auditor in auditors" 
                :key="auditor.user_id" 
                :value="auditor.user_id"
              >
                {{ auditor.name }}
              </option>
            </select>
          </div>
          <div>
            <Label for="reviewer-select">Reviewer *</Label>
            <select 
              id="reviewer-select"
              v-model="selectedReviewerId" 
              @change="handleReviewerSelection"
              class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <option value="">Select reviewer</option>
              <option 
                v-for="reviewer in reviewers" 
                :key="reviewer.user_id" 
                :value="reviewer.user_id"
              >
                {{ reviewer.name }}
              </option>
            </select>
          </div>
        </div>

        <div v-if="selectedAuditor || selectedReviewer" class="mt-4 p-3 lg:p-4 bg-muted/30 rounded-lg border">
          <h4 class="font-medium text-foreground mb-2 text-sm lg:text-base">Assignment Summary</h4>
          <div class="space-y-2 text-xs lg:text-sm">
            <div v-if="selectedAuditor" class="flex items-center">
              <span class="text-muted-foreground w-20">Auditor:</span>
              <span class="font-medium">{{ selectedAuditor.name }}</span>
              <span class="text-muted-foreground ml-2">({{ selectedAuditor.email }})</span>
              <Badge variant="outline" class="ml-2 text-xs">{{ selectedAuditor.role }}</Badge>
            </div>
            <div v-if="selectedReviewer" class="flex items-center">
              <span class="text-muted-foreground w-20">Reviewer:</span>
              <span class="font-medium">{{ selectedReviewer.name }}</span>
              <span class="text-muted-foreground ml-2">({{ selectedReviewer.email }})</span>
              <Badge variant="outline" class="ml-2 text-xs">{{ selectedReviewer.role }}</Badge>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- Contract Terms Overview -->
    <Card v-if="selectedContract && terms.length > 0" class="shadow-card">
      <CardHeader>
        <CardTitle class="flex items-center">
          <Target class="mr-2 h-5 w-5 text-primary" />
          Contract Terms Overview
        </CardTitle>
        <CardDescription>Review the terms that will be audited for this contract</CardDescription>
      </CardHeader>
      <CardContent class="p-4 lg:p-6">
        <div class="space-y-4">
          <div v-for="term in terms" :key="term.term_id" class="border border-border rounded-lg p-4">
            <div class="flex items-center justify-between mb-2">
              <h4 class="font-medium text-foreground">{{ term.term_name }}</h4>
              <Badge variant="outline" class="text-xs">{{ term.monitoring_frequency }}</Badge>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-muted-foreground">
              <div>
                <span class="font-medium">Type:</span> {{ term.term_type }}
              </div>
              <div>
                <span class="font-medium">Compliance:</span> {{ term.compliance_requirement || 'Standard compliance' }}
              </div>
            </div>
            <div v-if="term.description" class="mt-2 text-sm">
              <span class="font-medium text-muted-foreground">Description:</span>
              <p class="text-muted-foreground mt-1">{{ term.description }}</p>
            </div>
            <div v-if="term.penalty_clause" class="mt-2 text-sm">
              <span class="font-medium text-muted-foreground">Penalty Clause:</span>
              <p class="text-muted-foreground mt-1">{{ term.penalty_clause }}</p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- Submit -->
    <div class="flex flex-col sm:flex-row justify-end gap-3 sm:gap-4">
      <Button variant="outline" @click="navigateBack" class="w-full sm:w-auto">
        Cancel
      </Button>
      <Button 
        @click="handleSubmit"
        :disabled="loading"
        class="bg-gradient-to-r from-primary to-primary-glow hover:shadow-hover transition-all w-full sm:w-auto"
      >
        <Calendar class="mr-2 h-4 w-4" />
        {{ loading ? 'Creating...' : 'Create Audit' }}
      </Button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { useNotifications } from '@/composables/useNotifications'
import { 
  FileText, 
  Target, 
  Users, 
  Calendar 
} from 'lucide-vue-next'
import contractAuditApi from '@/services/contractAuditApi.js'
import loggingService from '@/services/loggingService'
import { PopupService } from '@/popup/popupService'
import { 
  Card, CardHeader, CardTitle, CardDescription, CardContent, Button, Badge, Input, Label, Textarea, Select
} from '@/components/ui_contract'

// CustomQuestion interface removed for JavaScript compatibility

const router = useRouter()
const store = useStore()
const { showSuccess, showError, showWarning, showInfo } = useNotifications()

// Form state
const selectedContractId = ref(null)
const selectedAuditorId = ref(null)
const selectedReviewerId = ref(null)
const auditTitle = ref('')
const auditScope = ref('')
const dueDate = ref('')
const frequency = ref('')
const auditType = ref('')

// Initialize date to today's date
const today = new Date().toISOString().split('T')[0]
dueDate.value = today

// Contract terms state
const terms = ref([])

// API data
const availableContracts = ref([])
const auditors = ref([])
const reviewers = ref([])
const loading = ref(false)

const selectedContract = computed(() => 
  selectedContractId.value ? availableContracts.value.find(contract => contract.contract_id == selectedContractId.value) : null
)

const selectedAuditor = computed(() => 
  selectedAuditorId.value ? auditors.value.find(auditor => auditor.user_id == selectedAuditorId.value) : null
)

const selectedReviewer = computed(() => 
  selectedReviewerId.value ? reviewers.value.find(reviewer => reviewer.user_id == selectedReviewerId.value) : null
)

// Get current user from store
const currentUser = computed(() => store.getters['auth/currentUser'])

// Load data on component mount
const loadData = async () => {
  loading.value = true
  try {
    // Load available contracts from contract audit API
    const contractsResponse = await contractAuditApi.getAvailableContracts()
    if (contractsResponse.success) {
      // Filter to show only APPROVED and Active contracts (case-insensitive)
      availableContracts.value = contractsResponse.data.filter(contract => {
        const status = contract.status?.toUpperCase()
        return status === 'APPROVED' || status === 'ACTIVE'
      })
      
      console.log('📋 Total contracts loaded:', contractsResponse.data.length)
      console.log('✅ Filtered contracts (APPROVED or ACTIVE):', availableContracts.value.length)
      console.log('📊 Contract statuses:', contractsResponse.data.map(c => c.status))
    } else {
      console.error('Error loading contracts:', contractsResponse.error)
      availableContracts.value = []
    }

    // Load available users from contract audit API
    console.log('Fetching available users for auditor and reviewer selection...')
    const usersResponse = await contractAuditApi.getAvailableUsers()
    console.log('Users response:', {
      success: usersResponse.success,
      hasData: !!usersResponse.data,
      dataType: Array.isArray(usersResponse.data) ? 'array' : typeof usersResponse.data,
      dataLength: Array.isArray(usersResponse.data) ? usersResponse.data.length : 'N/A',
      error: usersResponse.error
    })
    
    if (usersResponse.success && usersResponse.data) {
      // Ensure data is an array
      const usersList = Array.isArray(usersResponse.data) 
        ? usersResponse.data 
        : (usersResponse.data.results || [])
      
      // Show all users for both auditor and reviewer selection
      auditors.value = usersList
      reviewers.value = usersList
      
      console.log('Loaded users for dropdowns:', {
        auditorsCount: auditors.value.length,
        reviewersCount: reviewers.value.length,
        sampleUser: usersList[0]
      })
      
      // Automatically select current user as auditor if available
      if (currentUser.value && !selectedAuditorId.value) {
        // Check multiple possible field names for user ID
        const currentUserId = currentUser.value?.userid || currentUser.value?.user_id || 
                             currentUser.value?.UserId || currentUser.value?.id ||
                             (currentUser.value?.user && (currentUser.value.user.userid || currentUser.value.user.user_id || currentUser.value.user.UserId || currentUser.value.user.id))
        
        if (currentUserId) {
          // Check if current user exists in the auditors list
          const currentUserInAuditors = auditors.value.find(
            auditor => auditor.user_id == currentUserId || 
                      auditor.userid == currentUserId ||
                      String(auditor.user_id) === String(currentUserId) ||
                      String(auditor.userid) === String(currentUserId)
          )
          if (currentUserInAuditors) {
            selectedAuditorId.value = currentUserInAuditors.user_id || currentUserInAuditors.userid
            console.log('Auto-selected current user as auditor:', selectedAuditorId.value)
          } else {
            console.log('Current user not found in auditors list:', {
              currentUserId,
              availableUserIds: auditors.value.map(a => a.user_id || a.userid)
            })
          }
        } else {
          console.warn('Could not extract user ID from current user:', currentUser.value)
        }
      }
    } else {
      const errorMsg = usersResponse.error || usersResponse.message || 'Unknown error'
      console.error('Error loading users:', errorMsg)
      PopupService.warning(`Failed to load users: ${errorMsg}. Please refresh the page.`, 'Loading Error')
      auditors.value = []
      reviewers.value = []
    }
  } catch (error) {
    console.error('Error loading data:', error)
    PopupService.error('Error loading data. Please refresh the page.', 'Loading Error')
  } finally {
    loading.value = false
  }
}

// Load data when component mounts
loadData()

// Watch for current user and auditors to auto-select auditor
watch([currentUser, auditors], ([newUser, newAuditors]) => {
  // Only auto-select if no auditor is currently selected and both user and auditors are available
  if (newUser && newAuditors && newAuditors.length > 0 && !selectedAuditorId.value) {
    // Check multiple possible field names for user ID
    const currentUserId = newUser?.userid || newUser?.user_id || 
                         newUser?.UserId || newUser?.id ||
                         (newUser?.user && (newUser.user.userid || newUser.user.user_id || newUser.user.UserId || newUser.user.id))
    
    if (currentUserId) {
      // Check if current user exists in the auditors list
      const currentUserInAuditors = newAuditors.find(
        auditor => auditor.user_id == currentUserId || 
                  auditor.userid == currentUserId ||
                  String(auditor.user_id) === String(currentUserId) ||
                  String(auditor.userid) === String(currentUserId)
      )
      if (currentUserInAuditors) {
        selectedAuditorId.value = currentUserInAuditors.user_id || currentUserInAuditors.userid
        console.log('Auto-selected current user as auditor (via watcher):', selectedAuditorId.value)
      }
    }
  }
}, { immediate: true })

// Debug: Watch form values
watch([auditTitle, dueDate, frequency, auditType, auditScope], (newValues, oldValues) => {
  console.log('Form values changed:', {
    auditTitle: newValues[0],
    dueDate: newValues[1],
    frequency: newValues[2],
    auditType: newValues[3],
    auditScope: newValues[4]
  })
})

// Debug: Watch auditScope specifically
watch(auditScope, (newScope, oldScope) => {
  console.log('Audit scope changed:', {
    newScope: newScope,
    oldScope: oldScope,
    length: newScope ? newScope.length : 0
  })
})

// Watch for Contract selection changes
watch(selectedContract, async (newContract) => {
  if (newContract) {
    try {
      // Load contract terms from contract audit API
      const termsResponse = await contractAuditApi.getContractTermsForAudit(newContract.contract_id)
      if (termsResponse.success) {
        terms.value = termsResponse.data.terms || []
      } else {
        console.error('Error loading contract terms:', termsResponse.error)
        terms.value = []
      }
      
      // Set default audit title
      auditTitle.value = `${new Date().getFullYear()} ${newContract.contract_title} Audit`
    } catch (error) {
      console.error('Error loading contract terms:', error)
      PopupService.error('Error loading contract terms. Please try again.', 'Loading Error')
    }
  }
})

// Event handlers
const handleContractSelection = (event) => {
  const target = event.target
  selectedContractId.value = target.value ? parseInt(target.value) : null
  console.log('Contract selected:', selectedContractId.value, selectedContract.value)
}

const handleAuditorSelection = (event) => {
  const target = event.target
  selectedAuditorId.value = target.value ? parseInt(target.value) : null
  console.log('Auditor selected:', selectedAuditorId.value, selectedAuditor.value)
}

const handleReviewerSelection = (event) => {
  const target = event.target
  selectedReviewerId.value = target.value ? parseInt(target.value) : null
  console.log('Reviewer selected:', selectedReviewerId.value, selectedReviewer.value)
}

const handleDateChange = (event) => {
  dueDate.value = event.target.value
  console.log('Date changed:', dueDate.value)
}

const handleScopeChange = (event) => {
  auditScope.value = event.target.value
  console.log('Scope changed:', auditScope.value)
}

// Watch dueDate for debugging
watch(dueDate, (newDate) => {
  console.log('Due date reactive value changed:', newDate)
})


const handleSubmit = async () => {
  // Debug: Log all values to see what's missing
  console.log('Validation Debug:', {
    selectedContract: selectedContract.value,
    selectedAuditor: selectedAuditor.value,
    selectedReviewer: selectedReviewer.value,
    auditTitle: auditTitle.value,
    dueDate: dueDate.value,
    auditScope: auditScope.value,
    frequency: frequency.value,
    auditType: auditType.value
  })
  
  // Validation
  if (!selectedContract.value || !selectedAuditor.value || !selectedReviewer.value || !auditTitle.value || !dueDate.value) {
    console.log('Validation failed:', {
      hasContract: !!selectedContract.value,
      hasAuditor: !!selectedAuditor.value,
      hasReviewer: !!selectedReviewer.value,
      hasTitle: !!auditTitle.value,
      hasDueDate: !!dueDate.value
    })
    PopupService.warning('Please fill in all required fields.', 'Required Fields Missing')
    return
  }

  // Check if auditor and reviewer are the same - handle multiple field names
  const auditorId = selectedAuditor.value.user_id || selectedAuditor.value.userid || 
                   selectedAuditor.value.UserId || selectedAuditor.value.id
  const reviewerId = selectedReviewer.value.user_id || selectedReviewer.value.userid || 
                    selectedReviewer.value.UserId || selectedReviewer.value.id
  
  if (auditorId && reviewerId && (String(auditorId) === String(reviewerId))) {
    PopupService.warning('Auditor and Reviewer cannot be the same person.', 'Invalid Selection')
    return
  }

  loading.value = true
  try {
    // Get current user ID for assignee_id - check multiple possible field names
    const currentUserId = currentUser.value?.userid || currentUser.value?.user_id || 
                         currentUser.value?.UserId || currentUser.value?.id ||
                         (currentUser.value?.user && (currentUser.value.user.userid || currentUser.value.user.user_id || currentUser.value.user.UserId || currentUser.value.user.id))
    
    // Get tenant_id from multiple sources: current user object, localStorage, or JWT token
    let tenantId = null
    if (currentUser.value?.tenant_id) {
      tenantId = currentUser.value.tenant_id
    } else if (localStorage.getItem('tenant_id')) {
      tenantId = parseInt(localStorage.getItem('tenant_id')) || localStorage.getItem('tenant_id')
    } else {
      // Try to extract from JWT token if available
      const token = localStorage.getItem('session_token')
      if (token) {
        try {
          const base64Url = token.split('.')[1]
          if (base64Url) {
            const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
            const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
              return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)
            }).join(''))
            const payload = JSON.parse(jsonPayload)
            if (payload.tenant_id) {
              tenantId = payload.tenant_id
            }
          }
        } catch (e) {
          console.warn('Could not extract tenant_id from JWT token:', e)
        }
      }
    }
    
    console.log('Current user for submit:', {
      currentUser: currentUser.value,
      currentUserId,
      tenantId,
      availableFields: currentUser.value ? Object.keys(currentUser.value) : []
    })
    
    if (!currentUserId) {
      console.error('Could not extract user ID from current user:', currentUser.value)
      PopupService.error('Unable to determine current user. Please refresh the page and try again.', 'User Error')
      loading.value = false
      return
    }
    
    if (!tenantId) {
      console.warn('⚠️ No tenant_id found. Audit will be created without tenant_id (backend will try to get it from contract)')
    }

    // Extract auditor and reviewer IDs - handle multiple possible field names
    const auditorId = selectedAuditor.value.user_id || selectedAuditor.value.userid || 
                     selectedAuditor.value.UserId || selectedAuditor.value.id
    const reviewerId = selectedReviewer.value.user_id || selectedReviewer.value.userid || 
                      selectedReviewer.value.UserId || selectedReviewer.value.id
    
    if (!auditorId || !reviewerId) {
      console.error('Could not extract auditor or reviewer ID:', {
        auditor: selectedAuditor.value,
        reviewer: selectedReviewer.value
      })
      PopupService.error('Unable to determine auditor or reviewer. Please select them again.', 'Selection Error')
      loading.value = false
      return
    }

    // Prepare audit data for API
    const auditData = {
      title: auditTitle.value,
      scope: auditScope.value || '',
      contract: selectedContract.value.contract_id,
      assignee_id: currentUserId,
      auditor_id: auditorId,
      reviewer_id: reviewerId,
      due_date: dueDate.value,
      frequency: frequency.value || 'monthly',
      audit_type: auditType.value || 'internal',
      business_unit: 'Default Business Unit',
      role: 'Auditor',
      responsibility: 'Conduct contract audit'
    }
    
    // Add tenant_id if available
    if (tenantId) {
      auditData.tenant_id = tenantId
      console.log('✅ Adding tenant_id to audit data:', tenantId)
    } else {
      console.warn('⚠️ No tenant_id available - backend will try to get it from contract')
    }

    console.log('Creating contract audit:', auditData)
    console.log('Current user:', currentUser.value)
    console.log('Current user ID:', currentUserId)
    console.log('Scope value being sent:', `"${auditData.scope}"`, 'Length:', auditData.scope.length)

    // Create audit via contract audit API
    const response = await contractAuditApi.createContractAudit(auditData)
    
    if (response.success) {
      PopupService.success(`Audit "${auditTitle.value}" has been created successfully and assigned to ${selectedAuditor.value.name}.`, 'Audit Created')
      // Navigate to audit list or dashboard
      router.push('/contract-audit/all')
    } else {
      PopupService.error(`Error creating audit: ${response.error || 'Unknown error'}`, 'Creation Error')
    }
  } catch (error) {
    console.error('Error creating contract audit:', error)
    PopupService.error('Error creating contract audit. Please try again.', 'Creation Error')
  } finally {
    loading.value = false
  }
}

const navigateBack = () => {
  router.go(-1)
}

// Log page view on mount
onMounted(async () => {
  await loggingService.logPageView('Contract', 'Contract Audit Create')
})
</script>

