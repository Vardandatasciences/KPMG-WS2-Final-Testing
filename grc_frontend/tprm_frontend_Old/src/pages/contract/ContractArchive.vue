<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <div>
        <h1 class="text-3xl font-bold text-foreground">Archive</h1>
        <p class="text-muted-foreground">Archived and completed contracts</p>
      </div>
      <div class="flex gap-2">
        <Button variant="outline" class="gap-2">
          <Download class="w-4 h-4" />
          Export Archive
        </Button>
      </div>
    </div>

    <!-- Stats Cards -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
      <Card>
        <CardHeader class="pb-2">
          <CardTitle class="text-sm font-medium text-muted-foreground">Archived Contracts</CardTitle>
        </CardHeader>
        <CardContent>
          <div class="text-2xl font-bold text-foreground">{{ pagination.total_count || archivedContracts.length }}</div>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader class="pb-2">
          <CardTitle class="text-sm font-medium text-muted-foreground">Completed</CardTitle>
        </CardHeader>
        <CardContent>
          <div class="text-2xl font-bold text-foreground">
            {{ completedCount }}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader class="pb-2">
          <CardTitle class="text-sm font-medium text-muted-foreground">Terminated</CardTitle>
        </CardHeader>
        <CardContent>
          <div class="text-2xl font-bold text-foreground">
            {{ terminatedCount }}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader class="pb-2">
          <CardTitle class="text-sm font-medium text-muted-foreground">Total Archived Value</CardTitle>
        </CardHeader>
        <CardContent>
          <div class="text-2xl font-bold text-foreground">
            ${{ totalValue.toLocaleString() }}
          </div>
          <p class="text-xs text-muted-foreground mt-1">
            From {{ archivedContracts.length }} archived contracts
          </p>
        </CardContent>
      </Card>
    </div>

    <!-- Filters -->
    <Card>
      <CardHeader>
        <CardTitle>Filters</CardTitle>
        <CardDescription>Filter archived contracts by reason</CardDescription>
      </CardHeader>
      <CardContent>
        <div class="flex justify-start">
          <Select v-model="reasonFilter">
            <SelectTrigger class="w-[300px]">
              <SelectValue>
                {{ getReasonFilterLabel(reasonFilter) }}
              </SelectValue>
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Archive Reasons</SelectItem>
              <SelectItem value="CONTRACT_EXPIRED">Contract Expired</SelectItem>
              <SelectItem value="EARLY_TERMINATION">Early Termination</SelectItem>
              <SelectItem value="PROJECT_COMPLETED">Project Completed</SelectItem>
              <SelectItem value="MUTUAL_AGREEMENT">Mutual Agreement</SelectItem>
              <SelectItem value="BREACH">Breach of Contract</SelectItem>
              <SelectItem value="OTHER">Other</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </CardContent>
    </Card>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-12">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
      <p class="mt-4 text-muted-foreground">Loading archived contracts...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="text-center py-12">
      <div class="text-destructive mb-4">
        <ArchiveIcon class="mx-auto h-12 w-12" />
      </div>
      <h3 class="text-lg font-semibold text-foreground mb-2">Error Loading Archived Contracts</h3>
      <p class="text-muted-foreground mb-4">{{ error }}</p>
      <Button @click="loadArchivedContracts" variant="outline">
        <RotateCcw class="w-4 h-4 mr-2" />
        Try Again
      </Button>
    </div>

    <!-- Archive Table -->
    <Card v-else>
      <CardHeader>
        <CardTitle>Archived Contracts</CardTitle>
        <CardDescription>Historical contract records</CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Contract</TableHead>
              <TableHead>Vendor</TableHead>
              <TableHead>Value</TableHead>
              <TableHead>Duration</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Archive Reason</TableHead>
              <TableHead>Archived By</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow v-for="contract in filteredContracts" :key="contract.contract_id">
              <TableCell>
                <div class="flex items-center gap-3">
                  <div class="w-10 h-10 bg-muted rounded-lg flex items-center justify-center">
                    <ArchiveIcon class="w-5 h-5 text-muted-foreground" />
                  </div>
                  <div>
                    <div class="font-medium text-foreground">{{ contract.contract_title || 'N/A' }}</div>
                    <div class="text-sm text-muted-foreground">{{ contract.contract_number || 'N/A' }}</div>
                  </div>
                </div>
              </TableCell>
              <TableCell class="text-foreground">{{ contract.vendor?.company_name || 'N/A' }}</TableCell>
              <TableCell class="font-medium">
                ${{ (parseFloat(contract.contract_value) || 0).toLocaleString() }} {{ contract.currency || 'USD' }}
              </TableCell>
              <TableCell>
                <div class="flex items-center gap-2 text-sm">
                  <Calendar class="w-3 h-3 text-muted-foreground" />
                  {{ contract.start_date ? new Date(contract.start_date).toLocaleDateString() : 'N/A' }} - 
                  {{ contract.end_date ? new Date(contract.end_date).toLocaleDateString() : 'N/A' }}
                </div>
                <div class="text-xs text-muted-foreground">
                  Archived: {{ contract.archived_date ? new Date(contract.archived_date).toLocaleDateString() : 'N/A' }}
                </div>
              </TableCell>
              <TableCell>
                <Badge :variant="getStatusBadgeVariant(contract.status)">
                  {{ contract.status || 'N/A' }}
                </Badge>
              </TableCell>
              <TableCell>
                <Badge :variant="getReasonBadgeVariant(contract.archive_reason)">
                  {{ getArchiveReasonText(contract.archive_reason) }}
                </Badge>
              </TableCell>
              <TableCell class="text-sm text-muted-foreground">{{ contract.archived_by || 'N/A' }}</TableCell>
              <TableCell>
                <div class="flex gap-2">
                  <Button variant="outline" size="sm" class="gap-1">
                    <Download class="w-3 h-3" />
                    Download
                  </Button>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    class="gap-1"
                    @click="restoreContract(contract)"
                    :disabled="!contract.can_be_restored"
                  >
                    <RotateCcw class="w-3 h-3" />
                    Restore
                  </Button>
                </div>
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>

        <div v-if="filteredContracts.length === 0 && !loading" class="text-center py-12">
          <ArchiveIcon class="mx-auto h-12 w-12 text-muted-foreground" />
          <h3 class="mt-2 text-sm font-semibold text-foreground">No archived contracts found</h3>
          <p class="mt-1 text-sm text-muted-foreground">
            Try adjusting your search or filter criteria.
          </p>
        </div>
      </CardContent>
    </Card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { 
  Card, CardContent, CardDescription, CardHeader, CardTitle,
  Badge, Button, Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow
} from '@/components/ui_contract'
import { 
  RotateCcw, Download, Archive as ArchiveIcon, Calendar 
} from 'lucide-vue-next'
import contractsApi from '../../services/contractsApi'
import loggingService from '@/services/loggingService'
import { PopupService } from '@/popup/popupService'

const router = useRouter()

// State
const reasonFilter = ref('all')
const loading = ref(false)
const error = ref(null)

// Data
const archivedContracts = ref([])
const pagination = ref({
  page: 1,
  page_size: 20,
  total_pages: 1,
  total_count: 0,
  has_next: false,
  has_previous: false
})

// Computed
const totalValue = computed(() => {
  return archivedContracts.value.reduce((sum, contract) => {
    const value = parseFloat(contract.contract_value) || 0
    return sum + value
  }, 0)
})

const completedCount = computed(() => {
  return archivedContracts.value.filter(c => {
    return c.status === "COMPLETED" || 
           c.archive_reason === "PROJECT_COMPLETED" || 
           c.archive_reason === "CONTRACT_EXPIRED"
  }).length
})

const terminatedCount = computed(() => {
  return archivedContracts.value.filter(c => {
    return c.status === "TERMINATED" || 
           c.archive_reason === "EARLY_TERMINATION" || 
           c.archive_reason === "BREACH"
  }).length
})

const filteredContracts = computed(() => {
  return archivedContracts.value.filter(contract => {
    // Reason filter
    if (reasonFilter.value !== 'all' && contract.archive_reason !== reasonFilter.value) {
      return false
    }

    return true
  })
})

// Methods
const loadArchivedContracts = async () => {
  try {
    loading.value = true
    error.value = null
    
    const params = {
      page: pagination.value.page,
      page_size: pagination.value.page_size,
      ordering: '-archived_date'
    }
    
    const response = await contractsApi.getArchivedContracts(params)
    
    if (response.success) {
      archivedContracts.value = response.data || []
      pagination.value = response.pagination || pagination.value
    } else {
      throw new Error(response.message || 'Failed to load archived contracts')
    }
  } catch (err) {
    console.error('Error loading archived contracts:', err)
    error.value = err.message || 'Failed to load archived contracts'
    archivedContracts.value = []
  } finally {
    loading.value = false
  }
}

const restoreContract = async (contract) => {
  if (!confirm(`Are you sure you want to restore contract "${contract.contract_title}"?`)) {
    return
  }

  try {
    const response = await contractsApi.restoreContract(contract.contract_id, {
      restore_reason: 'Restored from archive'
    })
    
    if (response.success) {
      // Remove from archived list
      archivedContracts.value = archivedContracts.value.filter(c => c.contract_id !== contract.contract_id)
      pagination.value.total_count = Math.max(0, pagination.value.total_count - 1)
      console.log('Contract restored successfully')
    } else {
      throw new Error(response.message || 'Failed to restore contract')
    }
  } catch (err) {
    console.error('Error restoring contract:', err)
    PopupService.error('Failed to restore contract: ' + err.message, 'Restore Failed')
  }
}

// Lifecycle
onMounted(async () => {
  await loggingService.logPageView('Contract', 'Contract Archive')
  await loadArchivedContracts()
})

// Helper functions for badge variants
const getStatusBadgeVariant = (status) => {
  const variants = {
    "ACTIVE": "default",
    "COMPLETED": "default",
    "TERMINATED": "destructive", 
    "CANCELLED": "secondary",
    "EXPIRED": "secondary"
  }
  return variants[status] || "secondary"
}

const getReasonBadgeVariant = (reason) => {
  const variants = {
    "CONTRACT_EXPIRED": "outline",
    "EARLY_TERMINATION": "destructive",
    "PROJECT_COMPLETED": "default",
    "MUTUAL_AGREEMENT": "default",
    "BREACH": "destructive",
    "OTHER": "secondary"
  }
  return variants[reason] || "outline"
}

const getArchiveReasonText = (reason) => {
  const reasonTexts = {
    "CONTRACT_EXPIRED": "Contract Expired",
    "EARLY_TERMINATION": "Early Termination",
    "PROJECT_COMPLETED": "Project Completed",
    "MUTUAL_AGREEMENT": "Mutual Agreement",
    "BREACH": "Breach of Contract",
    "OTHER": "Other"
  }
  return reasonTexts[reason] || reason || 'N/A'
}

// Helper function for dropdown label
const getReasonFilterLabel = (reason) => {
  const labels = {
    'all': 'All Archive Reasons',
    'CONTRACT_EXPIRED': 'Contract Expired',
    'EARLY_TERMINATION': 'Early Termination',
    'PROJECT_COMPLETED': 'Project Completed',
    'MUTUAL_AGREEMENT': 'Mutual Agreement',
    'BREACH': 'Breach of Contract',
    'OTHER': 'Other'
  }
  return labels[reason] || reason
}
</script>
