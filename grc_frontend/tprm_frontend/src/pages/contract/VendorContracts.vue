<template>
  <div class="space-y-6">
    <!-- Loading State -->
    <div v-if="isLoading" class="flex flex-col items-center justify-center py-20">
      <div class="relative">
        <div class="animate-spin rounded-full h-16 w-16 border-4 border-primary/20 border-t-primary"></div>
        <div class="absolute inset-0 flex items-center justify-center">
          <Building2 class="h-6 w-6 text-primary animate-pulse" />
        </div>
      </div>
       <h3 class="mt-6 text-xl font-semibold text-foreground">Loading Vendor Contracts</h3>
       <p class="mt-2 text-muted-foreground text-center max-w-md">
         Please wait while we fetch vendor contract information and statistics.
       </p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="flex flex-col items-center justify-center py-20">
      <div class="w-20 h-20 bg-red-50 dark:bg-red-900/20 rounded-full flex items-center justify-center mb-6">
        <FileText class="h-10 w-10 text-red-500" />
      </div>
       <h3 class="text-xl font-semibold text-foreground mb-2">Error Loading Vendor Contracts</h3>
       <p class="text-muted-foreground text-center max-w-md mb-6">
         {{ error }}
       </p>
       <Button @click="loadVendors" class="gap-2">
         <FileText class="w-4 h-4" />
         Try Again
       </Button>
    </div>

    <!-- Vendor Details View -->
    <div v-else-if="selectedVendor" class="space-y-6">
      <div class="flex items-center gap-4">
        <Button variant="ghost" @click="handleBackToList">
          <ArrowLeft class="w-4 h-4 mr-2" />
          Back to Vendor Contracts
        </Button>
        <div>
          <h1 class="text-3xl font-bold text-foreground">{{ selectedVendor.company_name }}</h1>
          <p class="text-muted-foreground">Vendor Contract Details & Associated Contracts</p>
        </div>
      </div>

      <!-- Vendor Information -->
      <Card>
        <CardHeader>
          <CardTitle class="flex items-center gap-3">
            <div class="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center">
              <Building2 class="w-6 h-6 text-primary" />
            </div>
            <div>
              <div class="text-xl font-bold">{{ selectedVendor.company_name }}</div>
              <div class="text-sm text-muted-foreground">{{ selectedVendor.vendor_code }}</div>
            </div>
            <Badge :variant="selectedVendor.status === 'APPROVED' ? 'default' : 'secondary'">
              {{ selectedVendor.status }}
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div class="space-y-3">
              <h3 class="font-medium text-foreground">Contact Information</h3>
              <div class="space-y-2">
                <div v-if="selectedVendor.primary_contact" class="flex items-center gap-2 text-sm">
                  <Mail class="w-4 h-4 text-muted-foreground" />
                  {{ selectedVendor.primary_contact.email }}
                </div>
                <div v-if="selectedVendor.primary_contact" class="flex items-center gap-2 text-sm">
                  <Phone class="w-4 h-4 text-muted-foreground" />
                  {{ selectedVendor.primary_contact.primary_phone }}
                </div>
                <div class="flex items-center gap-2 text-sm">
                  <MapPin class="w-4 h-4 text-muted-foreground" />
                  {{ selectedVendor.full_address }}
                </div>
              </div>
            </div>
            
            <div>
              <h3 class="font-medium text-foreground mb-2">Total Contracts</h3>
              <div class="text-2xl font-bold text-primary">{{ selectedVendor.contracts_count || 0 }}</div>
            </div>
            
            <div>
              <h3 class="font-medium text-foreground mb-2">Total Value</h3>
              <div class="text-2xl font-bold text-primary">${{ (selectedVendor.total_value || 0).toLocaleString() }}</div>
            </div>
            
            <div>
              <h3 class="font-medium text-foreground mb-2">Last Activity</h3>
              <div class="text-lg text-muted-foreground">
                {{ selectedVendor.last_activity ? new Date(selectedVendor.last_activity).toLocaleDateString() : 'No activity' }}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <!-- Contracts List -->
      <Card>
        <CardHeader>
          <CardTitle class="flex items-center gap-2">
            <FileText class="w-5 h-5" />
            Contracts
          </CardTitle>
          <CardDescription>All contracts associated with this vendor</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Contract Details</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Start Date</TableHead>
                <TableHead>End Date</TableHead>
                <TableHead>Value</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow v-for="contract in selectedVendor.contracts" :key="contract.contract_id">
                <TableCell>
                  <div>
                    <div class="font-medium text-foreground">{{ contract.contract_title }}</div>
                    <div class="text-sm text-muted-foreground">{{ contract.contract_number }}</div>
                  </div>
                </TableCell>
                <TableCell>
                  <Badge variant="outline">{{ contract.contract_type }}</Badge>
                </TableCell>
                <TableCell>
                  <Badge :variant="contract.status === 'ACTIVE' ? 'default' : 'secondary'">
                    {{ contract.status }}
                  </Badge>
                </TableCell>
                <TableCell>{{ contract.start_date ? new Date(contract.start_date).toLocaleDateString() : 'N/A' }}</TableCell>
                <TableCell>{{ contract.end_date ? new Date(contract.end_date).toLocaleDateString() : 'N/A' }}</TableCell>
                <TableCell class="font-medium">${{ (contract.contract_value || 0).toLocaleString() }}</TableCell>
                <TableCell>
                  <Button 
                    variant="outline" 
                    size="sm"
                    @click="viewContract(contract.contract_id)"
                    class="gap-2"
                  >
                    <Eye class="w-4 h-4" />
                    View
                  </Button>
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>

    <!-- Main Vendors List View -->
    <div v-else class="space-y-6">
      <div>
        <h1 class="text-3xl font-bold text-foreground">Vendor Contracts</h1>
        <p class="text-muted-foreground">
          {{ isVendor ? 'View your vendor information and associated contracts' : 'Manage vendor relationships and their associated contracts' }}
        </p>
      </div>

      <!-- Stats Cards -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card v-if="!isVendor">
          <CardHeader class="pb-2">
            <CardTitle class="text-sm font-medium text-muted-foreground">Total Vendors</CardTitle>
          </CardHeader>
          <CardContent>
            <div class="text-2xl font-bold text-foreground">{{ vendorStats.total_vendors || 0 }}</div>
          </CardContent>
        </Card>
        
        <Card v-if="!isVendor">
          <CardHeader class="pb-2">
            <CardTitle class="text-sm font-medium text-muted-foreground">Active Vendors</CardTitle>
          </CardHeader>
          <CardContent>
            <div class="text-2xl font-bold text-foreground">
              {{ vendorStats.active_vendors || 0 }}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader class="pb-2">
            <CardTitle class="text-sm font-medium text-muted-foreground">
              {{ isVendor ? 'My Contracts' : 'Total Contracts' }}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div class="text-2xl font-bold text-foreground">
              {{ vendorStats.total_contracts || 0 }}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader class="pb-2">
            <CardTitle class="text-sm font-medium text-muted-foreground">
              {{ isVendor ? 'Total Contract Value' : 'Total Value' }}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div class="text-2xl font-bold text-foreground">
              ${{ (vendorStats.total_value || 0).toLocaleString() }}
            </div>
          </CardContent>
        </Card>
      </div>

      <!-- Filters -->
      <Card>
        <CardHeader>
          <CardTitle>Search & Filter</CardTitle>
           <CardDescription>Find vendor contracts quickly</CardDescription>
        </CardHeader>
        <CardContent>
          <div class="flex gap-4">
            <div class="relative flex-1">
              <Search class="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <Input 
                v-model="searchQuery" 
                @input="handleSearch"
                 placeholder="Search vendor contracts..." 
                class="pl-10" 
              />
            </div>
            <Select v-model="statusFilter" @update:model-value="handleSearch">
              <SelectTrigger class="w-[180px]">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="APPROVED">Approved</SelectItem>
                <SelectItem value="DRAFT">Draft</SelectItem>
                <SelectItem value="SUBMITTED">Submitted</SelectItem>
                <SelectItem value="IN_REVIEW">In Review</SelectItem>
                <SelectItem value="REJECTED">Rejected</SelectItem>
                <SelectItem value="SUSPENDED">Suspended</SelectItem>
                <SelectItem value="TERMINATED">Terminated</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <!-- Vendors Table -->
      <Card>
        <CardHeader>
           <CardTitle>Vendor Contracts Directory</CardTitle>
           <CardDescription>
             {{ isVendor ? 'Your vendor information and contracts' : 'Complete list of vendor contract partners' }}
           </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Vendor Details</TableHead>
                <TableHead>Contact</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Contracts</TableHead>
                <TableHead>Total Value</TableHead>
                <TableHead>Last Activity</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow v-for="vendor in filteredVendors" :key="vendor.vendor_id">
                <TableCell>
                  <div class="flex items-center gap-3">
                    <div class="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                      <Building2 class="w-5 h-5 text-primary" />
                    </div>
                    <div>
                      <div class="font-medium text-foreground">{{ vendor.company_name }}</div>
                      <div class="text-sm text-muted-foreground">{{ vendor.vendor_code }}</div>
                    </div>
                  </div>
                </TableCell>
                <TableCell>
                  <div class="space-y-1">
                    <div v-if="vendor.primary_contact" class="flex items-center gap-2 text-sm">
                      <Mail class="w-3 h-3 text-muted-foreground" />
                      {{ vendor.primary_contact.email }}
                    </div>
                    <div v-if="vendor.primary_contact" class="flex items-center gap-2 text-sm">
                      <Phone class="w-3 h-3 text-muted-foreground" />
                      {{ vendor.primary_contact.primary_phone }}
                    </div>
                    <div class="flex items-center gap-2 text-sm">
                      <MapPin class="w-3 h-3 text-muted-foreground" />
                      {{ vendor.full_address }}
                    </div>
                  </div>
                </TableCell>
                <TableCell>
                  <Badge :variant="vendor.status === 'APPROVED' ? 'default' : 'secondary'">
                    {{ vendor.status }}
                  </Badge>
                </TableCell>
                <TableCell class="text-center">{{ vendor.contracts_count || 0 }}</TableCell>
                <TableCell>${{ (vendor.total_value || 0).toLocaleString() }}</TableCell>
                <TableCell>{{ vendor.last_activity ? new Date(vendor.last_activity).toLocaleDateString() : 'No activity' }}</TableCell>
                <TableCell>
                  <div class="flex gap-2">
                    <Button 
                      variant="outline" 
                      size="sm"
                      @click="loadVendorDetails(vendor.vendor_id)"
                    >
                      View
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'
import { 
  Card, CardContent, CardDescription, CardHeader, CardTitle,
  Badge, Button, Input, Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow
} from '@/components/ui_contract'
import { 
  Search, Plus, Building2, Mail, Phone, MapPin, ArrowLeft, FileText, 
  CheckCircle, DollarSign, Eye, Edit, Trash2, Calendar, User, Shield
} from 'lucide-vue-next'
import vendorcontractsApi from '../../services/vendorcontractsApi'
import loggingService from '@/services/loggingService'

const store = useStore()
const router = useRouter()

// Get current user from store
const currentUser = computed(() => store.getters['auth/currentUser'])

// Check if user is a vendor
const isVendor = computed(() => {
  if (!currentUser.value) return false
  const role = currentUser.value.role || currentUser.value.user_role || ''
  return role.toLowerCase() === 'vendor'
})

// State
const selectedVendor = ref(null)
const searchQuery = ref('')
const statusFilter = ref('all')
const vendors = ref([])
const vendorStats = ref({
  total_vendors: 0,
  active_vendors: 0,
  total_contracts: 0,
  total_value: 0
})
const isLoading = ref(true)
const error = ref(null)

// Computed
const filteredVendors = computed(() => {
  return vendors.value.filter(vendor => {
    // Search filter
    if (searchQuery.value) {
      const query = searchQuery.value.toLowerCase()
      const matchesQuery = 
        vendor.company_name?.toLowerCase().includes(query) ||
        vendor.vendor_code?.toLowerCase().includes(query) ||
        vendor.legal_name?.toLowerCase().includes(query) ||
        vendor.description?.toLowerCase().includes(query)
      
      if (!matchesQuery) return false
    }

    // Status filter
    if (statusFilter.value !== 'all' && vendor.status !== statusFilter.value) {
      return false
    }

    return true
  })
})

// Methods
const loadVendors = async () => {
  try {
    isLoading.value = true
    error.value = null
    
    const response = await vendorcontractsApi.getVendors({
      search: searchQuery.value,
      status: statusFilter.value !== 'all' ? statusFilter.value : '',
      page_size: 100 // Load more vendors for better UX
    })
    
    if (response.success) {
      vendors.value = response.data || []
       console.log('Vendor contracts loaded:', vendors.value.length, 'vendor contracts')
      // Calculate stats from loaded vendors as fallback
      calculateStatsFromVendors()
    } else {
       error.value = response.message || 'Failed to load vendor contracts'
    }
  } catch (err) {
    console.error('Error loading vendor contracts:', err)
    error.value = 'Failed to load vendor contracts'
  } finally {
    isLoading.value = false
  }
}

const loadVendorStats = async () => {
  try {
    const response = await vendorcontractsApi.getVendorStats()
    if (response.success) {
      vendorStats.value = response.data
       console.log('Vendor contract stats loaded:', response.data)
    } else {
      console.error('Failed to load vendor contract stats:', response.message)
      // Calculate stats from vendor list as fallback
      calculateStatsFromVendors()
    }
  } catch (err) {
    console.error('Error loading vendor contract stats:', err)
    // Calculate stats from vendor list as fallback
    calculateStatsFromVendors()
  }
}

const calculateStatsFromVendors = () => {
  if (vendors.value.length > 0) {
    const totalVendors = vendors.value.length
    const activeVendors = vendors.value.filter(v => v.status === 'APPROVED').length
    const totalContracts = vendors.value.reduce((sum, v) => sum + (v.contracts_count || 0), 0)
    const totalValue = vendors.value.reduce((sum, v) => sum + (v.total_value || 0), 0)
    
    vendorStats.value = {
      total_vendors: totalVendors,
      active_vendors: activeVendors,
      total_contracts: totalContracts,
      total_value: totalValue
    }
     console.log('Calculated stats from vendor contracts:', vendorStats.value)
  }
}

const loadVendorDetails = async (vendorId) => {
  try {
    const response = await vendorcontractsApi.getVendor(vendorId)
    if (response.success) {
      selectedVendor.value = response.data
    } else {
       error.value = response.message || 'Failed to load vendor contract details'
    }
  } catch (err) {
    console.error('Error loading vendor contract details:', err)
    error.value = 'Failed to load vendor contract details'
  }
}

const handleVendorSelect = (vendor) => {
  selectedVendor.value = vendor
}

const handleBackToList = () => {
  selectedVendor.value = null
}

const viewContract = (contractId) => {
  if (contractId) {
    router.push({
      path: `/contracts/${contractId}`,
      query: { returnTo: 'vendor-contracts' }
    })
  }
}

// Watch for search changes
const handleSearch = () => {
  loadVendors()
}

// Watch for changes in vendors to recalculate stats
watch(vendors, () => {
  calculateStatsFromVendors()
}, { deep: true })

// Lifecycle
onMounted(async () => {
  await loggingService.logPageView('Contract', 'Vendor Contracts')
  await Promise.all([
    loadVendors(),
    loadVendorStats()
  ])
})
</script>
