<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
      <div>
        <h1 class="text-3xl font-bold tracking-tight">RFI Management</h1>
        <p class="text-muted-foreground">
          View, manage, and share all your RFIs
        </p>
      </div>
      <div class="flex gap-2">
        <Button variant="outline" as-child>
          <a href="/rfi-responses">
            <FileText class="h-4 w-4 mr-2" />
            View Responses
          </a>
        </Button>
        <Button variant="outline" @click="refreshRFIs">
          <RefreshCw class="h-4 w-4 mr-2" :class="{ 'animate-spin': loading }" />
          Refresh
        </Button>
        <Button as-child class="gradient-primary">
          <a href="/rfi-creation">
            <Plus class="h-4 w-4 mr-2" />
            Create New RFI
          </a>
        </Button>
      </div>
    </div>

    <!-- Filters -->
    <Card class="phase-card">
      <div class="p-6">
        <div class="flex flex-col sm:flex-row gap-4 items-start sm:items-center">
          <div class="flex-1">
            <Input
              v-model="searchQuery"
              placeholder="Search RFIs by title, number, or description..."
              class="w-full"
            />
          </div>
          <div class="flex gap-2">
            <Select v-model="statusFilter">
              <SelectTrigger class="w-40">
                <SelectValue placeholder="All Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">All Status</SelectItem>
                <SelectItem value="DRAFT">Draft</SelectItem>
                <SelectItem value="IN_REVIEW">In Review</SelectItem>
                <SelectItem value="PUBLISHED">Published</SelectItem>
                <SelectItem value="SUBMISSION_OPEN">Submission Open</SelectItem>
                <SelectItem value="EVALUATION">Evaluation</SelectItem>
                <SelectItem value="AWARDED">Awarded</SelectItem>
              </SelectContent>
            </Select>
            <Select v-model="typeFilter">
              <SelectTrigger class="w-40">
                <SelectValue placeholder="All Types" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">All Types</SelectItem>
                <SelectItem v-for="type in rfiTypes" :key="type" :value="type">
                  {{ type }}
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>
    </Card>

    <!-- RFI List -->
    <div class="grid gap-6">
      <Card v-for="rfi in filteredRFIs" :key="rfi.rfi_id" class="phase-card">
        <div class="p-6">
          <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
            <!-- RFI Info -->
            <div class="flex-1 space-y-3">
              <div class="flex items-center gap-3 flex-wrap">
                <h3 class="text-lg font-semibold">{{ rfi.rfi_title }}</h3>
                <Badge :class="getStatusColor(rfi.status)">
                  {{ formatStatus(rfi.status) }}
                </Badge>
                <Badge variant="outline">{{ rfi.rfi_type }}</Badge>
              </div>
              
              <div class="flex items-center gap-4 text-sm text-muted-foreground flex-wrap">
                <span class="font-medium">{{ rfi.rfi_number }}</span>
                <span class="flex items-center gap-1">
                  <Calendar class="h-3 w-3" />
                  {{ formatDate(rfi.created_at) }}
                </span>
                <span class="flex items-center gap-1">
                  <Clock class="h-3 w-3" />
                  {{ formatDate(rfi.submission_deadline) }}
                </span>
                <span v-if="rfi.budget_range_min || rfi.budget_range_max" class="flex items-center gap-1">
                  <DollarSign class="h-3 w-3" />
                  {{ formatBudget(rfi.budget_range_min, rfi.budget_range_max) }}
                </span>
              </div>
              
              <p class="text-sm text-muted-foreground line-clamp-2">
                {{ rfi.description }}
              </p>
            </div>

            <!-- Actions -->
            <div class="flex flex-col sm:flex-row gap-2">
              <Button variant="outline" size="sm" @click="viewRFI(rfi)">
                <Eye class="h-4 w-4 mr-2" />
                View
              </Button>
              <Button variant="default" size="sm" @click="selectVendors(rfi)" class="gradient-primary">
                <Users class="h-4 w-4 mr-2" />
                Select Vendors
              </Button>
            </div>
          </div>
        </div>
      </Card>

      <!-- Empty State -->
      <Card v-if="filteredRFIs.length === 0 && !loading" class="phase-card">
        <div class="p-12 text-center">
          <FileText class="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <h3 class="text-lg font-semibold mb-2">No RFIs Found</h3>
          <p class="text-muted-foreground mb-4">
            {{ searchQuery || statusFilter || typeFilter ? 'No RFIs match your current filters.' : 'You haven\'t created any RFIs yet.' }}
          </p>
          <Button as-child>
            <a href="/rfi-creation">
              <Plus class="h-4 w-4 mr-2" />
              Create Your First RFI
            </a>
          </Button>
        </div>
      </Card>

      <!-- Loading State -->
      <Card v-if="loading" class="phase-card">
        <div class="p-12 text-center">
          <RefreshCw class="h-8 w-8 mx-auto text-muted-foreground mb-4 animate-spin" />
          <p class="text-muted-foreground">Loading RFIs...</p>
        </div>
      </Card>
    </div>

    <!-- RFI Preview Modal -->
    <Dialog v-model:open="showRFIPreviewModal">
      <DialogContent class="max-w-7xl max-h-[95vh] p-0">
        <div class="flex flex-col h-full">
          <!-- Header -->
          <div class="flex-shrink-0 border-b border-gray-200 bg-gray-50 px-6 py-4">
            <div class="flex items-center justify-between">
              <div>
                <h2 class="text-2xl font-bold text-gray-900">{{ selectedRFI?.rfi_title }}</h2>
                <p class="text-sm text-gray-600 mt-1">{{ selectedRFI?.rfi_number || 'RFI Details' }}</p>
              </div>
              <div class="flex items-center gap-3">
                <Badge :class="getStatusColor(selectedRFI?.status)" class="text-sm px-3 py-1">
                  {{ formatStatus(selectedRFI?.status) }}
                </Badge>
                <Button variant="outline" size="sm" @click="showRFIPreviewModal = false">
                  <X class="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>

          <!-- Content -->
          <div class="flex-1 overflow-y-auto">
            <div v-if="rfiPreviewLoading" class="flex items-center justify-center h-64">
              <div class="text-center">
                <RefreshCw class="h-8 w-8 mx-auto text-gray-400 mb-4 animate-spin" />
                <p class="text-gray-600">Loading RFI details...</p>
              </div>
            </div>
            
            <div v-else-if="rfiFullDetails" class="p-6 space-y-8">
              <!-- Overview Section -->
              <div class="bg-white rounded-xl border border-gray-200 p-8">
                <div class="flex items-center gap-3 mb-6">
                  <div class="p-2 bg-blue-100 rounded-lg">
                    <FileText class="h-6 w-6 text-blue-600" />
                  </div>
                  <h3 class="text-xl font-semibold text-gray-900">Overview</h3>
                </div>
                
                <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
                  <!-- Basic Info -->
                  <div class="space-y-4">
                    <h4 class="font-medium text-gray-900 border-b border-gray-100 pb-2">Basic Information</h4>
                    <div class="space-y-3">
                      <div>
                        <Label class="text-xs font-medium text-gray-500 uppercase tracking-wide">RFI Number</Label>
                        <p class="text-sm font-medium text-gray-900 mt-1">{{ rfiFullDetails.rfi_number || 'Not assigned' }}</p>
                      </div>
                      <div>
                        <Label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Type</Label>
                        <p class="text-sm text-gray-700 mt-1">{{ rfiFullDetails.rfi_type }}</p>
                      </div>
                      <div>
                        <Label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Category</Label>
                        <p class="text-sm text-gray-700 mt-1">{{ rfiFullDetails.category || 'Not specified' }}</p>
                      </div>
                      <div>
                        <Label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Version</Label>
                        <p class="text-sm text-gray-700 mt-1">{{ rfiFullDetails.version_number }}</p>
                      </div>
                    </div>
                  </div>

                  <!-- Budget Info -->
                  <div class="space-y-4">
                    <h4 class="font-medium text-gray-900 border-b border-gray-100 pb-2">Budget Information</h4>
                    <div class="space-y-3">
                      <div>
                        <Label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Estimated Value</Label>
                        <p class="text-sm font-medium text-gray-900 mt-1">
                          {{ rfiFullDetails.estimated_value ? `$${Number(rfiFullDetails.estimated_value).toLocaleString()}` : 'Not specified' }}
                        </p>
                      </div>
                      <div>
                        <Label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Budget Range</Label>
                        <p class="text-sm text-gray-700 mt-1">{{ formatBudget(rfiFullDetails.budget_range_min, rfiFullDetails.budget_range_max) }}</p>
                      </div>
                      <div>
                        <Label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Currency</Label>
                        <p class="text-sm text-gray-700 mt-1">{{ rfiFullDetails.currency }}</p>
                      </div>
                    </div>
                  </div>

                  <!-- Timeline Info -->
                  <div class="space-y-4">
                    <h4 class="font-medium text-gray-900 border-b border-gray-100 pb-2">Timeline</h4>
                    <div class="space-y-3">
                      <div>
                        <Label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Issue Date</Label>
                        <p class="text-sm text-gray-700 mt-1">{{ formatDate(rfiFullDetails.issue_date) }}</p>
                      </div>
                      <div>
                        <Label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Submission Deadline</Label>
                        <p class="text-sm text-gray-700 mt-1">{{ formatDate(rfiFullDetails.submission_deadline) }}</p>
                      </div>
                      <div>
                        <Label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Evaluation End</Label>
                        <p class="text-sm text-gray-700 mt-1">{{ formatDate(rfiFullDetails.evaluation_period_end) }}</p>
                      </div>
                      <div>
                        <Label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Award Date</Label>
                        <p class="text-sm text-gray-700 mt-1">{{ formatDate(rfiFullDetails.award_date) }}</p>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Description -->
                <div class="mt-8 pt-6 border-t border-gray-100">
                  <Label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Description</Label>
                  <p class="text-sm text-gray-700 mt-2 leading-relaxed">{{ rfiFullDetails.description }}</p>
                </div>
              </div>
            </div>
            
            <div v-else class="flex items-center justify-center h-64">
              <div class="text-center">
                <AlertCircle class="h-8 w-8 mx-auto text-red-400 mb-4" />
                <p class="text-red-600 font-medium">Failed to load RFI details</p>
                <p class="text-sm text-gray-500 mt-1">Please try again or contact support</p>
              </div>
            </div>
          </div>

          <!-- Footer -->
          <div class="flex-shrink-0 border-t border-gray-200 bg-gray-50 px-6 py-4">
            <div class="flex items-center justify-between">
              <div class="text-sm text-gray-500">
                RFI ID: {{ rfiFullDetails?.rfi_id || 'N/A' }}
              </div>
              <div class="flex items-center gap-3">
                <Button variant="outline" @click="showRFIPreviewModal = false">
                  Close
                </Button>
              </div>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { rfpUseToast } from '@/composables/rfpUseToast'
import { useRfpApi } from '@/composables/useRfpApi'
import { getTprmApiV1BaseUrl } from '@/utils/backendEnv'

// Components
import Card from '@/components_rfp/Card.vue'
import Button from '@/components_rfp/Button.vue'
import Badge from '@/components_rfp/rfpBadge.vue'
import Input from '@/components_rfp/ui/Input.vue'
import Select from '@/components_rfp/ui/Select.vue'
import SelectContent from '@/components_rfp/ui/SelectContent.vue'
import SelectItem from '@/components_rfp/ui/SelectItem.vue'
import SelectTrigger from '@/components_rfp/ui/SelectTrigger.vue'
import SelectValue from '@/components_rfp/ui/SelectValue.vue'
import Dialog from '@/components_rfp/ui/Dialog.vue'
import DialogContent from '@/components_rfp/ui/DialogContent.vue'
import Label from '@/components_rfp/ui/Label.vue'

// Icons
import {
  FileText,
  Eye,
  RefreshCw,
  Plus,
  Calendar,
  Clock,
  DollarSign,
  AlertCircle,
  X,
  Users
} from 'lucide-vue-next'

// Store and composables
const { success, error: toastError } = rfpUseToast()
const { getAuthHeaders } = useRfpApi()
const API_BASE_URL = getTprmApiV1BaseUrl()

// Reactive data
const loading = ref(false)
const searchQuery = ref('')
const statusFilter = ref('')
const typeFilter = ref('')
const rfis = ref([])
const rfiTypes = ref([])

// Selected RFI for preview
const selectedRFI = ref(null)
const showRFIPreviewModal = ref(false)
const rfiFullDetails = ref(null)
const rfiPreviewLoading = ref(false)

// Computed properties
const filteredRFIs = computed(() => {
  let filtered = rfis.value

  // Filter by search query
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(rfi => 
      rfi.rfi_title?.toLowerCase().includes(query) ||
      rfi.rfi_number?.toLowerCase().includes(query) ||
      rfi.description?.toLowerCase().includes(query)
    )
  }

  // Filter by status
  if (statusFilter.value) {
    filtered = filtered.filter(rfi => rfi.status === statusFilter.value)
  }

  // Filter by type
  if (typeFilter.value) {
    filtered = filtered.filter(rfi => rfi.rfi_type === typeFilter.value)
  }

  return filtered
})

// Methods
const fetchRFIs = async () => {
  loading.value = true
  try {
    console.log('[RFIList] Fetching RFIs from:', `${API_BASE_URL}/rfis/`)
    
    let allRFIs = []
    let nextUrl = `${API_BASE_URL}/rfis/`
    
    // Fetch all pages if pagination is enabled
    while (nextUrl) {
      const response = await axios.get(nextUrl, {
        headers: getAuthHeaders()
      })
      
      console.log('[RFIList] Response received:', {
        status: response.status,
        hasData: !!response.data,
        isArray: Array.isArray(response.data),
        hasResults: !!(response.data && response.data.results),
        hasNext: !!(response.data && response.data.next)
      })
      
      if (response.data && Array.isArray(response.data)) {
        // Direct array response (no pagination)
        allRFIs = response.data
        nextUrl = null
        console.log('[RFIList] Loaded', response.data.length, 'RFIs (direct array)')
      } else if (response.data && response.data.results) {
        // Paginated response
        allRFIs = allRFIs.concat(response.data.results)
        console.log('[RFIList] Loaded page:', response.data.results.length, 'RFIs (total so far:', allRFIs.length, ')')
        
        // Check if there's a next page
        if (response.data.next) {
          // Handle both absolute and relative URLs
          if (response.data.next.startsWith('http')) {
            nextUrl = response.data.next
          } else {
            // Relative URL - prepend base URL if needed
            nextUrl = response.data.next.startsWith('/') 
              ? `${API_BASE_URL}${response.data.next}`
              : `${API_BASE_URL}/rfis/${response.data.next}`
          }
          console.log('[RFIList] Fetching next page:', nextUrl)
        } else {
          nextUrl = null
          console.log('[RFIList] All pages loaded. Total RFIs:', allRFIs.length)
        }
      } else {
        console.warn('[RFIList] Unexpected response format:', response.data)
        break
      }
    }
    
    rfis.value = allRFIs
    console.log('[RFIList] Final count:', allRFIs.length, 'RFIs loaded')
    
  } catch (error) {
    console.error('[RFIList] Error fetching RFIs:', {
      message: error.message,
      response: error.response?.data,
      status: error.response?.status,
      url: error.config?.url
    })
    toastError('Failed to load RFIs. Please check your connection and try again.')
    rfis.value = []
  } finally {
    loading.value = false
  }
}

const fetchRFITypes = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/rfi-types/types/`, {
      headers: getAuthHeaders()
    })
    
    if (response.data && response.data.success && Array.isArray(response.data.rfi_types)) {
      rfiTypes.value = response.data.rfi_types
    } else {
      rfiTypes.value = []
    }
  } catch (error) {
    console.error('Error fetching RFI types:', error)
    rfiTypes.value = []
  }
}

const refreshRFIs = async () => {
  await fetchRFIs()
  success('RFIs refreshed successfully')
}

const router = useRouter()
const selectVendors = (rfi) => {
  localStorage.setItem('selectedRFI', JSON.stringify(rfi))
  router.push('/rfi-vendor-selection')
}

const viewRFI = async (rfi) => {
  selectedRFI.value = rfi
  showRFIPreviewModal.value = true
  rfiPreviewLoading.value = true
  rfiFullDetails.value = null
  
  try {
    const response = await axios.get(`${API_BASE_URL}/rfis/${rfi.rfi_id}/`, {
      headers: getAuthHeaders()
    })
    
    if (response.data) {
      rfiFullDetails.value = response.data
    } else {
      toastError('Failed to load RFI details')
    }
  } catch (error) {
    console.error('Error loading RFI details:', error)
    toastError('Failed to load RFI details')
  } finally {
    rfiPreviewLoading.value = false
  }
}

// Helper functions
const formatStatus = (status) => {
  const statusMap = {
    'DRAFT': 'Draft',
    'IN_REVIEW': 'In Review',
    'PUBLISHED': 'Published',
    'SUBMISSION_OPEN': 'Submission Open',
    'EVALUATION': 'Evaluation',
    'AWARDED': 'Awarded',
    'CANCELLED': 'Cancelled',
    'ARCHIVED': 'Archived'
  }
  return statusMap[status] || status
}

const getStatusColor = (status) => {
  switch (status) {
    case 'DRAFT': return 'bg-gray-100 text-gray-800'
    case 'IN_REVIEW': return 'bg-blue-100 text-blue-800'
    case 'PUBLISHED': return 'bg-green-100 text-green-800'
    case 'SUBMISSION_OPEN': return 'bg-purple-100 text-purple-800'
    case 'EVALUATION': return 'bg-yellow-100 text-yellow-800'
    case 'AWARDED': return 'bg-emerald-100 text-emerald-800'
    case 'CANCELLED': return 'bg-red-100 text-red-800'
    case 'ARCHIVED': return 'bg-gray-100 text-gray-600'
    default: return 'bg-gray-100 text-gray-800'
  }
}

const formatDate = (dateString) => {
  if (!dateString) return 'Not set'
  return new Date(dateString).toLocaleDateString()
}

const formatBudget = (min, max) => {
  if (!min && !max) return 'Not specified'
  if (min && max) return `$${Number(min).toLocaleString()} - $${Number(max).toLocaleString()}`
  if (min) return `$${Number(min).toLocaleString()}+`
  if (max) return `Up to $${Number(max).toLocaleString()}`
  return 'Not specified'
}

// Lifecycle
onMounted(async () => {
  await fetchRFITypes()
  await fetchRFIs()
})
</script>

<style scoped>
.phase-card {
  @apply bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition-shadow;
}

.text-muted-foreground {
  @apply text-gray-500;
}

.gradient-primary {
  @apply bg-gradient-to-r from-blue-600 to-blue-700 text-white hover:from-blue-700 hover:to-blue-800;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>


