<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
      <div>
        <div class="flex items-center gap-2 mb-2">
          <Badge variant="outline">Phase 2</Badge>
        </div>
        <h1 class="text-3xl font-bold tracking-tight">RFP Management</h1>
        <p class="text-muted-foreground">
          View and manage RFPs created by users.
        </p>
      </div>
    </div>


    <!-- User Info Section -->
      <Card class="phase-card">
        <CardHeader>
        <CardTitle>My RFPs</CardTitle>
        <CardDescription>View RFPs created by you</CardDescription>
        </CardHeader>
        <CardContent>
        <div class="flex items-center gap-4">
          <div class="flex-1">
            <p class="text-sm text-gray-600">
              Showing RFPs created by you
              <span class="text-muted-foreground ml-2">({{ filteredRFPs.length }} RFPs)</span>
            </p>
          </div>
            <div class="flex items-center gap-2">
            <Button @click="fetchRFPs" :disabled="loading" variant="outline">
              <RefreshCw class="h-4 w-4 mr-2" :class="{ 'animate-spin': loading }" />
              {{ loading ? 'Loading...' : 'Refresh' }}
            </Button>
            </div>
            </div>
        </CardContent>
      </Card>

    <!-- RFP Table -->
      <Card class="phase-card">
        <CardHeader>
        <CardTitle>RFPs</CardTitle>
        <CardDescription>List of all RFPs</CardDescription>
        </CardHeader>
        <CardContent>
        <!-- Loading State -->
        <div v-if="loading" class="text-center py-12">
          <RefreshCw class="h-8 w-8 text-primary animate-spin mx-auto mb-4" />
          <p class="text-muted-foreground">Loading RFPs...</p>
                </div>

        <!-- Empty State -->
        <div v-else-if="filteredRFPs.length === 0" class="text-center py-12">
          <FileText class="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h3 class="text-lg font-medium text-gray-900 mb-2">No RFPs Found</h3>
          <p class="text-muted-foreground">
            You have not created any RFPs yet.
          </p>
                  </div>

        <!-- RFP Table -->
        <div v-else class="overflow-x-auto">
          <table class="w-full border-collapse">
            <thead>
              <tr class="border-b border-gray-200">
                <th class="text-left py-3 px-4 font-medium text-gray-900">RFP Number</th>
                <th class="text-left py-3 px-4 font-medium text-gray-900">Title</th>
                <th class="text-left py-3 px-4 font-medium text-gray-900">Type</th>
                <th class="text-left py-3 px-4 font-medium text-gray-900">Budget</th>
                <th class="text-left py-3 px-4 font-medium text-gray-900">Status</th>
                <th class="text-left py-3 px-4 font-medium text-gray-900">Created</th>
                <th class="text-left py-3 px-4 font-medium text-gray-900">Deadline</th>
                <th class="text-left py-3 px-4 font-medium text-gray-900">Creator</th>
                <th class="text-left py-3 px-4 font-medium text-gray-900">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr 
                v-for="rfp in filteredRFPs" 
                :key="rfp.rfp_id"
                class="border-b border-gray-100 hover:bg-gray-50 transition-colors"
              >
                <td class="py-3 px-4">
                  <span class="font-mono text-sm text-gray-600">{{ rfp.rfp_number }}</span>
                </td>
                <td class="py-3 px-4">
                    <div>
                    <div class="font-medium text-gray-900">{{ rfp.rfp_title }}</div>
                    <div class="text-sm text-gray-500 mt-1 line-clamp-2 max-w-xs">
                      {{ rfp.description }}
                    </div>
                  </div>
                </td>
                <td class="py-3 px-4">
                  <Badge v-if="rfp.rfp_type" variant="outline" class="text-xs">{{ rfp.rfp_type }}</Badge>
                  <span v-else class="text-sm text-gray-400">N/A</span>
                </td>
                <td class="py-3 px-4">
                  <span class="font-medium">{{ formatCurrency(rfp.estimated_value) }}</span>
                </td>
                <td class="py-3 px-4">
                  <component :is="getStatusBadgeComponent(rfp.status)" />
                </td>
                <td class="py-3 px-4">
                  <span class="text-sm text-gray-600">{{ formatDate(rfp.created_at) }}</span>
                </td>
                <td class="py-3 px-4">
                  <span class="text-sm text-gray-600">{{ formatDate(rfp.submission_deadline) }}</span>
                </td>
                <td class="py-3 px-4">
                  <span class="text-sm text-gray-600">{{ getCreatorName(rfp.created_by) }}</span>
                </td>
                <td class="py-3 px-4">
                  <div class="flex items-center gap-2">
                    <Button 
                      v-if="rfp.status === 'APPROVED'"
                      @click="proceedToVendorSelection(rfp)"
                      size="sm"
                      class="bg-blue-600 hover:bg-blue-700 text-white"
                    >
                      <ArrowRight class="h-3 w-3 mr-1" />
                      Vendor Selection
                    </Button>
                    <span v-else class="text-xs text-gray-400">
                      {{ getActionText(rfp.status) }}
                    </span>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
          </div>
        </CardContent>
      </Card>
    </div>
</template>

<script setup lang="ts">
import { ref, h, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { useNotifications } from '@/composables/useNotifications'
import loggingService from '@/services/loggingService'
import { 
  FileText, 
  RefreshCw,
  ArrowRight
} from 'lucide-vue-next'
import { rfpUseToast } from '@/composables/rfpUseToast.js'
import { API_CONFIG, API_ENDPOINTS, buildApiUrl, apiCall } from '@/config/api.js'
import Card from '@/components_rfp/ui/Card.vue'
import CardContent from '@/components_rfp/ui/CardContent.vue'
import CardDescription from '@/components_rfp/ui/CardDescription.vue'
import CardHeader from '@/components_rfp/ui/CardHeader.vue'
import CardTitle from '@/components_rfp/ui/CardTitle.vue'
import Button from '@/components_rfp/ui/Button.vue'
import Badge from '@/components_rfp/ui/Badge.vue'

const { success, error } = rfpUseToast()
const router = useRouter()

// Reactive data for RFP management
const { showSuccess, showError, showWarning, showInfo } = useNotifications()

const rfps = ref([])
const loading = ref(false)

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
      
      // Try multiple possible user ID field names
      const userId = user.id || user.user_id || user.userId || user.userid
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


// Computed properties
const filteredRFPs = computed(() => {
  const currentUserId = getCurrentUserId()
  if (!currentUserId) {
    return []
  }
  return rfps.value.filter(rfp => rfp.created_by === parseInt(currentUserId))
})

// Methods for RFP management

const fetchRFPs = async () => {
  loading.value = true
  try {
    // Use the correct API endpoint for RFPs
    const url = `${API_CONFIG.BASE_URL}/v1/rfps/`
    const data = await apiCall(url)
    rfps.value = data.results || data // Handle pagination if present
  } catch (err) {
    console.error('Error fetching RFPs:', err)
    error('Error', 'Failed to fetch RFPs from database')
    rfps.value = []
  } finally {
    loading.value = false
  }
}

const getCreatorName = (userId: number) => {
  // Try to get creator name from Vuex store or localStorage
  try {
    const store = useStore()
    const vuexUser = store.getters['auth/currentUser']
    if (vuexUser && vuexUser.id === userId) {
      return `${vuexUser.first_name || ''} ${vuexUser.last_name || ''}`.trim() || vuexUser.username || `User ${userId}`
    }
  } catch (e) {
    // Ignore Vuex errors
  }
  
  // Fallback to localStorage
  try {
    const currentUserFromStorage = localStorage.getItem('current_user')
    if (currentUserFromStorage) {
      const user = JSON.parse(currentUserFromStorage)
      if (user.id === userId || user.user_id === userId) {
        return `${user.first_name || ''} ${user.last_name || ''}`.trim() || user.username || `User ${userId}`
      }
    }
  } catch (e) {
    // Ignore localStorage errors
  }
  
  return `User ${userId}`
}

const formatCurrency = (amount: number) => {
  if (!amount) return 'N/A'
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(amount)
}

const formatDate = (dateString: string) => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

const getStatusBadgeComponent = (status: string) => {
  const statusConfig = {
    'DRAFT': { class: 'bg-gray-100 text-gray-800 border-gray-200', text: 'Draft' },
    'IN_REVIEW': { class: 'bg-yellow-100 text-yellow-800 border-yellow-200', text: 'In Review' },
    'APPROVED': { class: 'bg-green-100 text-green-800 border-green-200', text: 'Approved' },
    'PUBLISHED': { class: 'bg-blue-100 text-blue-800 border-blue-200', text: 'Published' },
    'SUBMISSION_OPEN': { class: 'bg-purple-100 text-purple-800 border-purple-200', text: 'Submission Open' },
    'EVALUATION': { class: 'bg-indigo-100 text-indigo-800 border-indigo-200', text: 'Evaluation' },
    'AWARDED': { class: 'bg-emerald-100 text-emerald-800 border-emerald-200', text: 'Awarded' },
    'CANCELLED': { class: 'bg-red-100 text-red-800 border-red-200', text: 'Cancelled' },
    'ARCHIVED': { class: 'bg-slate-100 text-slate-800 border-slate-200', text: 'Archived' }
  }
  
  const config = statusConfig[status] || statusConfig['DRAFT']
  return h(Badge, { class: config.class }, () => config.text)
}

const proceedToVendorSelection = (rfp: any) => {
  // Store the selected RFP data for the vendor selection page
  localStorage.setItem('selectedRFP', JSON.stringify(rfp))
  
    // Navigate to Phase 3 Vendor Selection
    window.location.href = '/rfp-vendor-selection'
  
  success('Proceeding to Vendor Selection', `RFP ${rfp.rfp_number} is ready for vendor selection.`)
}

const getActionText = (status: string) => {
  const actionTexts = {
    'DRAFT': 'Awaiting submission',
    'IN_REVIEW': 'Under review',
    'PUBLISHED': 'Published',
    'SUBMISSION_OPEN': 'Accepting submissions',
    'EVALUATION': 'Under evaluation',
    'AWARDED': 'Awarded',
    'CANCELLED': 'Cancelled',
    'ARCHIVED': 'Archived'
  }
  return actionTexts[status] || 'No action available'
}

// Initialize data on component mount
onMounted(async () => {
  await loggingService.logPageView('RFP', 'Phase 2 - RFP Approval')
  const currentUserId = getCurrentUserId()
  if (!currentUserId) {
    console.error('No current user found. User may not be properly logged in.')
    error('Error', 'Unable to identify current user. Please log in again.')
    return
  }
  console.log('✅ Current user ID:', currentUserId)
  fetchRFPs()
})
</script>

<style scoped>
.phase-card {
  @apply bg-white border border-border rounded-lg shadow-sm;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
