<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
      <div>
        <h1 class="text-3xl font-bold tracking-tight">Auction Management</h1>
        <p class="text-muted-foreground">
          View, manage, and share all your active Auctions
        </p>
      </div>
      <div class="flex gap-2">
        <Button variant="outline" @click="refreshAuctions">
          <RefreshCw class="h-4 w-4 mr-2" :class="{ 'animate-spin': loading }" />
          Refresh
        </Button>
        <Button as-child class="gradient-primary">
          <a href="/auction-creation">
            <Plus class="h-4 w-4 mr-2" />
            Create New Auction
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
              placeholder="Search Auctions by title, number, or description..."
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
                <SelectItem v-for="type in auctionTypes" :key="type" :value="type">
                  {{ type }}
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>
    </Card>

    <!-- Auction List -->
    <div class="grid gap-6">
      <Card v-for="auction in filteredAuctions" :key="auction.auction_id" class="phase-card">
        <div class="p-6">
          <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
            <!-- Auction Info -->
            <div class="flex-1 space-y-3">
              <div class="flex items-center gap-3 flex-wrap">
                <h3 class="text-lg font-semibold">{{ auction.auction_title }}</h3>
                <Badge :class="getStatusColor(auction.status)">
                  {{ formatStatus(auction.status) }}
                </Badge>
                <Badge variant="outline">{{ auction.auction_type }}</Badge>
              </div>
              
              <div class="flex items-center gap-4 text-sm text-muted-foreground flex-wrap">
                <span class="font-medium">{{ auction.auction_number }}</span>
                <span class="flex items-center gap-1">
                  <Calendar class="h-3 w-3" />
                  {{ formatDate(auction.created_at) }}
                </span>
                <span class="flex items-center gap-1">
                  <Clock class="h-3 w-3" />
                  {{ formatDate(auction.submission_deadline) }}
                </span>
                <span v-if="auction.budget_range_min || auction.budget_range_max" class="flex items-center gap-1">
                  <DollarSign class="h-3 w-3" />
                  {{ formatBudget(auction.budget_range_min, auction.budget_range_max) }}
                </span>
              </div>
              
              <p class="text-sm text-muted-foreground line-clamp-2">
                {{ auction.description }}
              </p>
            </div>

            <!-- Actions -->
            <div class="flex flex-col sm:flex-row gap-2">
              <Button variant="outline" size="sm" @click="viewAuction(auction)">
                <Eye class="h-4 w-4 mr-2" />
                View
              </Button>
            </div>
          </div>
        </div>
      </Card>

      <!-- Empty State -->
      <Card v-if="filteredAuctions.length === 0 && !loading" class="phase-card">
        <div class="p-12 text-center">
          <FileText class="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <h3 class="text-lg font-semibold mb-2">No Auctions Found</h3>
          <p class="text-muted-foreground mb-4">
            {{ searchQuery || statusFilter || typeFilter ? 'No Auctions match your current filters.' : 'You haven\'t created any Auctions yet.' }}
          </p>
          <Button as-child>
            <a href="/auction-creation">
              <Plus class="h-4 w-4 mr-2" />
              Create Your First Auction
            </a>
          </Button>
        </div>
      </Card>

      <!-- Loading State -->
      <Card v-if="loading" class="phase-card">
        <div class="p-12 text-center">
          <RefreshCw class="h-8 w-8 mx-auto text-muted-foreground mb-4 animate-spin" />
          <p class="text-muted-foreground">Loading Auctions...</p>
        </div>
      </Card>
    </div>

    <!-- Auction Preview Modal -->
    <Dialog v-model:open="showAuctionPreviewModal">
      <DialogContent class="max-w-7xl max-h-[95vh] p-0">
        <div class="flex flex-col h-full">
          <!-- Header -->
          <div class="flex-shrink-0 border-b border-gray-200 bg-gray-50 px-6 py-4">
            <div class="flex items-center justify-between">
              <div>
                <h2 class="text-2xl font-bold text-gray-900">{{ selectedAuction?.auction_title }}</h2>
                <p class="text-sm text-gray-600 mt-1">{{ selectedAuction?.auction_number || 'Auction Details' }}</p>
              </div>
              <div class="flex items-center gap-3">
                <Badge :class="getStatusColor(selectedAuction?.status)" class="text-sm px-3 py-1">
                  {{ formatStatus(selectedAuction?.status) }}
                </Badge>
                <Button variant="outline" size="sm" @click="showAuctionPreviewModal = false">
                  <X class="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>

          <!-- Content -->
          <div class="flex-1 overflow-y-auto">
            <div v-if="auctionPreviewLoading" class="flex items-center justify-center h-64">
              <div class="text-center">
                <RefreshCw class="h-8 w-8 mx-auto text-gray-400 mb-4 animate-spin" />
                <p class="text-gray-600">Loading Auction details...</p>
              </div>
            </div>
            
            <div v-else-if="auctionFullDetails" class="p-6 space-y-8">
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
                        <Label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Auction Number</Label>
                        <p class="text-sm font-medium text-gray-900 mt-1">{{ auctionFullDetails.auction_number || 'Not assigned' }}</p>
                      </div>
                      <div>
                        <Label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Type</Label>
                        <p class="text-sm text-gray-700 mt-1">{{ auctionFullDetails.auction_type }}</p>
                      </div>
                      <div>
                        <Label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Category</Label>
                        <p class="text-sm text-gray-700 mt-1">{{ auctionFullDetails.category || 'Not specified' }}</p>
                      </div>
                      <div>
                        <Label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Version</Label>
                        <p class="text-sm text-gray-700 mt-1">{{ auctionFullDetails.version_number }}</p>
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
                          {{ auctionFullDetails.estimated_value ? `$${Number(auctionFullDetails.estimated_value).toLocaleString()}` : 'Not specified' }}
                        </p>
                      </div>
                      <div>
                        <Label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Budget Range</Label>
                        <p class="text-sm text-gray-700 mt-1">{{ formatBudget(auctionFullDetails.budget_range_min, auctionFullDetails.budget_range_max) }}</p>
                      </div>
                      <div>
                        <Label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Currency</Label>
                        <p class="text-sm text-gray-700 mt-1">{{ auctionFullDetails.currency }}</p>
                      </div>
                    </div>
                  </div>

                  <!-- Timeline Info -->
                  <div class="space-y-4">
                    <h4 class="font-medium text-gray-900 border-b border-gray-100 pb-2">Timeline</h4>
                    <div class="space-y-3">
                      <div>
                        <Label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Issue Date</Label>
                        <p class="text-sm text-gray-700 mt-1">{{ formatDate(auctionFullDetails.issue_date) }}</p>
                      </div>
                      <div>
                        <Label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Submission Deadline</Label>
                        <p class="text-sm text-gray-700 mt-1">{{ formatDate(auctionFullDetails.submission_deadline) }}</p>
                      </div>
                      <div>
                        <Label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Evaluation End</Label>
                        <p class="text-sm text-gray-700 mt-1">{{ formatDate(auctionFullDetails.evaluation_period_end) }}</p>
                      </div>
                      <div>
                        <Label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Award Date</Label>
                        <p class="text-sm text-gray-700 mt-1">{{ formatDate(auctionFullDetails.award_date) }}</p>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Description -->
                <div class="mt-8 pt-6 border-t border-gray-100">
                  <Label class="text-xs font-medium text-gray-500 uppercase tracking-wide">Description</Label>
                  <p class="text-sm text-gray-700 mt-2 leading-relaxed">{{ auctionFullDetails.description }}</p>
                </div>
              </div>
            </div>
            
            <div v-else class="flex items-center justify-center h-64">
              <div class="text-center">
                <AlertCircle class="h-8 w-8 mx-auto text-red-400 mb-4" />
                <p class="text-red-600 font-medium">Failed to load Auction details</p>
                <p class="text-sm text-gray-500 mt-1">Please try again or contact support</p>
              </div>
            </div>
          </div>

          <!-- Footer -->
          <div class="flex-shrink-0 border-t border-gray-200 bg-gray-50 px-6 py-4">
            <div class="flex items-center justify-between">
              <div class="text-sm text-gray-500">
                Auction ID: {{ auctionFullDetails?.auction_id || 'N/A' }}
              </div>
              <div class="flex items-center gap-3">
                <Button variant="outline" @click="showAuctionPreviewModal = false">
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
  X
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
const auctions = ref([])
const auctionTypes = ref([])

// Selected Auction for preview
const selectedAuction = ref(null)
const showAuctionPreviewModal = ref(false)
const auctionFullDetails = ref(null)
const auctionPreviewLoading = ref(false)

// Computed properties
const filteredAuctions = computed(() => {
  let filtered = auctions.value

  // Filter by search query
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(auction => 
      auction.auction_title?.toLowerCase().includes(query) ||
      auction.auction_number?.toLowerCase().includes(query) ||
      auction.description?.toLowerCase().includes(query)
    )
  }

  // Filter by status
  if (statusFilter.value) {
    filtered = filtered.filter(auction => auction.status === statusFilter.value)
  }

  // Filter by type
  if (typeFilter.value) {
    filtered = filtered.filter(auction => auction.auction_type === typeFilter.value)
  }

  return filtered
})

// Methods
const fetchAuctions = async () => {
  loading.value = true
  try {
    console.log('[AuctionList] Fetching Auctions from:', `${API_BASE_URL}/auctions/`)
    const response = await axios.get(`${API_BASE_URL}/auctions/`, {
      headers: getAuthHeaders()
    })
    
    console.log('[AuctionList] Response received:', {
      status: response.status,
      hasData: !!response.data,
      isArray: Array.isArray(response.data),
      hasResults: !!(response.data && response.data.results),
      dataLength: response.data ? (Array.isArray(response.data) ? response.data.length : (response.data.results ? response.data.results.length : 0)) : 0
    })
    
    if (response.data && Array.isArray(response.data)) {
      auctions.value = response.data
      console.log('[AuctionList] Loaded', response.data.length, 'Auctions (direct array)')
    } else if (response.data && response.data.results) {
      auctions.value = response.data.results
      console.log('[AuctionList] Loaded', response.data.results.length, 'Auctions (paginated)')
    } else {
      auctions.value = []
      console.warn('[AuctionList] Unexpected response format:', response.data)
    }
  } catch (error) {
    console.error('[AuctionList] Error fetching Auctions:', {
      message: error.message,
      response: error.response?.data,
      status: error.response?.status,
      url: error.config?.url
    })
    toastError('Failed to load Auctions. Please check your connection and try again.')
    auctions.value = []
  } finally {
    loading.value = false
  }
}

const fetchAuctionTypes = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/auction-types/types/`, {
      headers: getAuthHeaders()
    })
    
    if (response.data && response.data.success && Array.isArray(response.data.auction_types)) {
      auctionTypes.value = response.data.auction_types
    } else {
      auctionTypes.value = []
    }
  } catch (error) {
    console.error('Error fetching Auction types:', error)
    auctionTypes.value = []
  }
}

const refreshAuctions = async () => {
  await fetchAuctions()
  success('Auctions refreshed successfully')
}

const viewAuction = async (auction) => {
  selectedAuction.value = auction
  showAuctionPreviewModal.value = true
  auctionPreviewLoading.value = true
  auctionFullDetails.value = null
  
  try {
    const response = await axios.get(`${API_BASE_URL}/auctions/${auction.auction_id}/`, {
      headers: getAuthHeaders()
    })
    
    if (response.data) {
      auctionFullDetails.value = response.data
    } else {
      toastError('Failed to load Auction details')
    }
  } catch (error) {
    console.error('Error loading Auction details:', error)
    toastError('Failed to load Auction details')
  } finally {
    auctionPreviewLoading.value = false
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
  await fetchAuctionTypes()
  await fetchAuctions()
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
