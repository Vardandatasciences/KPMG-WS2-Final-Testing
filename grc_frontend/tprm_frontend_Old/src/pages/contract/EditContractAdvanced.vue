<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-4">
        <button @click="navigate('/contracts')" class="p-2 hover:bg-muted rounded-md">
          <ArrowLeft class="w-4 h-4" />
        </button>
        <div>
          <h1 class="text-3xl font-bold text-foreground">Edit Contract</h1>
          <p class="text-muted-foreground">Manage contract details, versions, amendments, and subcontracts</p>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <button @click="navigate('/contracts')" class="inline-flex items-center gap-2 px-4 py-2 border rounded-md hover:bg-muted">
          <ArrowLeft class="w-4 h-4" />
          Back to Contracts
        </button>
      </div>
    </div>

    <div v-if="loading" class="text-center py-12">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
      <h3 class="mt-2 text-sm font-semibold text-foreground">Loading contract...</h3>
    </div>

    <div v-else-if="error" class="text-center py-12">
      <FileText class="mx-auto h-12 w-12 text-muted-foreground" />
      <h3 class="mt-2 text-sm font-semibold text-foreground">Error loading contract</h3>
      <p class="mt-1 text-sm text-muted-foreground">{{ error }}</p>
      <div class="mt-6">
        <button @click="loadContract()" class="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90">
          Retry
        </button>
      </div>
    </div>

    <div v-else-if="!contract" class="text-center py-12">
      <FileText class="mx-auto h-12 w-12 text-muted-foreground" />
      <h3 class="mt-2 text-sm font-semibold text-foreground">Contract not found</h3>
      <p class="mt-1 text-sm text-muted-foreground">
        The contract you're looking for doesn't exist.
      </p>
    </div>

    <div v-else>
      <!-- Contract Header with Version Info -->
      <div class="border rounded-lg bg-card p-6">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-2xl font-bold text-foreground">
              {{ contract.contract_title }}
              <span class="text-lg font-normal text-muted-foreground">v{{ contract.version_number }}</span>
            </h2>
            <p class="text-muted-foreground">{{ contract.contract_number }}</p>
          </div>
          <div class="flex items-center gap-2">
            <span :class="getStatusBadgeClass(contract.status)" class="px-3 py-1 rounded-full text-sm font-medium">
              {{ contract.status }}
            </span>
            <span v-if="isLatestVersion" class="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">
              Latest Version
            </span>
          </div>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="flex items-center gap-4">
        <button 
          @click="navigate(`/contracts/${contractId}/create-amendment?from=edit-advanced`)"
          class="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          <FileText class="w-4 h-4" />
          Create Amendment
        </button>
        <button 
          @click="navigate(`/contracts/${contractId}/create-subcontract-advanced`)"
          class="inline-flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
        >
          <Plus class="w-4 h-4" />
          Add Subcontract
        </button>
        <button 
          @click="showVersionHistory = true" 
          class="inline-flex items-center gap-2 px-4 py-2 border rounded-md hover:bg-muted"
        >
          <History class="w-4 h-4" />
          Version History
        </button>
      </div>

      <!-- Contract Overview Cards -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Basic Information Card -->
        <div class="lg:col-span-2">
          <div class="border rounded-lg bg-card">
            <div class="p-6 border-b">
              <h3 class="text-lg font-semibold flex items-center gap-2">
                <FileText class="w-5 h-5" />
                Contract Information
              </h3>
            </div>
            <div class="p-6 space-y-6">
              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div class="space-y-2">
                  <label class="text-sm font-medium text-muted-foreground">Contract Title</label>
                  <div class="text-lg font-semibold text-foreground">{{ contract.contract_title }}</div>
                </div>
                <div class="space-y-2">
                  <label class="text-sm font-medium text-muted-foreground">Contract Number</label>
                  <div class="text-lg font-mono text-foreground">{{ contract.contract_number }}</div>
                </div>
                <div class="space-y-2">
                  <label class="text-sm font-medium text-muted-foreground">Contract Type</label>
                  <div class="flex items-center gap-2">
                    <span class="px-2 py-1 bg-blue-100 text-blue-800 rounded-md text-sm font-medium">
                      {{ getContractTypeLabel(contract.contract_type) }}
                    </span>
                  </div>
                </div>
                <div class="space-y-2">
                  <label class="text-sm font-medium text-muted-foreground">Contract Value</label>
                  <div class="text-lg font-semibold text-foreground flex items-center gap-1">
                    <DollarSign class="w-4 h-4" />
                    {{ formatCurrency(contract.contract_value) }}
                  </div>
                </div>
                <div class="space-y-2">
                  <label class="text-sm font-medium text-muted-foreground">Start Date</label>
                  <div class="flex items-center gap-2 text-foreground">
                    <Calendar class="w-4 h-4" />
                    {{ formatDate(contract.start_date) }}
                  </div>
                </div>
                <div class="space-y-2">
                  <label class="text-sm font-medium text-muted-foreground">End Date</label>
                  <div class="flex items-center gap-2 text-foreground">
                    <Calendar class="w-4 h-4" />
                    {{ formatDate(contract.end_date) }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Status & Actions Card -->
        <div class="space-y-6">
          <!-- Contract Status -->
          <div class="border rounded-lg bg-card">
            <div class="p-6">
              <h3 class="text-lg font-semibold flex items-center gap-2 mb-4">
                <Shield class="w-5 h-5" />
                Contract Status
              </h3>
              <div class="space-y-4">
                <div class="flex items-center justify-between">
                  <span class="text-sm font-medium text-muted-foreground">Status</span>
                  <span :class="getStatusBadgeClass(contract.status)" class="px-3 py-1 rounded-full text-sm font-medium">
                    {{ contract.status }}
                  </span>
                </div>
                <div class="flex items-center justify-between">
                  <span class="text-sm font-medium text-muted-foreground">Priority</span>
                  <span class="px-2 py-1 bg-gray-100 text-gray-800 rounded-md text-sm font-medium capitalize">
                    {{ contract.priority || 'Medium' }}
                  </span>
                </div>
                <div class="flex items-center justify-between">
                  <span class="text-sm font-medium text-muted-foreground">Risk Score</span>
                  <span class="px-2 py-1 bg-yellow-100 text-yellow-800 rounded-md text-sm font-medium">
                    {{ contract.contract_risk_score || 'N/A' }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- Vendor Information -->
          <div class="border rounded-lg bg-card">
            <div class="p-6">
              <h3 class="text-lg font-semibold flex items-center gap-2 mb-4">
                <Building class="w-5 h-5" />
                Vendor Details
              </h3>
              <div class="space-y-4">
                <!-- Company Information -->
                <div class="space-y-2">
                  <label class="text-sm font-medium text-muted-foreground">Company Name</label>
                  <div class="text-foreground font-medium">{{ contract.vendor?.company_name || 'N/A' }}</div>
                </div>
                
                <!-- Primary Contact Information -->
                <div v-if="contract.vendor?.primary_contact" class="space-y-3">
                  <label class="text-sm font-medium text-muted-foreground">Primary Contact</label>
                  <div class="bg-gray-50 rounded-lg p-4 space-y-2">
                    <div class="flex items-center gap-2">
                      <Users class="w-4 h-4 text-muted-foreground" />
                      <span class="font-medium text-foreground">
                        {{ contract.vendor.primary_contact.full_name || `${contract.vendor.primary_contact.first_name || ''} ${contract.vendor.primary_contact.last_name || ''}`.trim() || 'N/A' }}
                      </span>
                      <span v-if="contract.vendor.primary_contact.is_primary" class="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium">
                        Primary
                      </span>
                    </div>
                    
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                      <div v-if="contract.vendor.primary_contact.email" class="flex items-center gap-2">
                        <span class="text-muted-foreground">Email:</span>
                        <a :href="`mailto:${contract.vendor.primary_contact.email}`" class="text-blue-600 hover:text-blue-800">
                          {{ contract.vendor.primary_contact.email }}
                        </a>
                      </div>
                      
                      <div v-if="contract.vendor.primary_contact.primary_phone || contract.vendor.primary_contact.phone" class="flex items-center gap-2">
                        <span class="text-muted-foreground">Phone:</span>
                        <a :href="`tel:${contract.vendor.primary_contact.primary_phone || contract.vendor.primary_contact.phone}`" class="text-blue-600 hover:text-blue-800">
                          {{ contract.vendor.primary_contact.primary_phone || contract.vendor.primary_contact.phone }}
                        </a>
                      </div>
                      
                      <div v-if="contract.vendor.primary_contact.mobile" class="flex items-center gap-2">
                        <span class="text-muted-foreground">Mobile:</span>
                        <a :href="`tel:${contract.vendor.primary_contact.mobile}`" class="text-blue-600 hover:text-blue-800">
                          {{ contract.vendor.primary_contact.mobile }}
                        </a>
                      </div>
                      
                      <div v-if="contract.vendor.primary_contact.designation" class="flex items-center gap-2">
                        <span class="text-muted-foreground">Designation:</span>
                        <span class="text-foreground">{{ contract.vendor.primary_contact.designation }}</span>
                      </div>
                      
                      <div v-if="contract.vendor.primary_contact.department" class="flex items-center gap-2">
                        <span class="text-muted-foreground">Department:</span>
                        <span class="text-foreground">{{ contract.vendor.primary_contact.department }}</span>
                      </div>
                    </div>
                  </div>
                </div>
                
                <!-- Fallback for simple contact display -->
                <div v-else class="space-y-2">
                  <label class="text-sm font-medium text-muted-foreground">Contact</label>
                  <div class="text-foreground">{{ contract.vendor?.primary_contact || 'N/A' }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>




      <!-- Version History Modal -->
      <div v-if="showVersionHistory" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div class="bg-background rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
          <VersionHistory 
            :contract-id="contractId"
            :current-contract-id="contract.contract_id"
            @close="showVersionHistory = false"
            @switch-version="handleVersionSwitch"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { 
  ArrowLeft, FileText, Building, DollarSign, Calendar, 
  Shield, Users, FileCheck, Plus, History
} from 'lucide-vue-next'
import contractsApi from '@/services/contractsApi'
import VersionHistory from '@/components/VersionHistory.vue'
import loggingService from '@/services/loggingService'

// Router and route
const router = useRouter()
const route = useRoute()
const navigate = (path) => router.push(path)
const contractId = parseInt(route.params.id)

// Reactive state
const contract = ref(null)
const contractVersions = ref([])
const loading = ref(false)
const error = ref(null)


// Modal states
const showVersionHistory = ref(false)

// Computed properties
const isLatestVersion = computed(() => {
  if (!contractVersions.value.length) return true
  const latest = contractVersions.value[0]
  return latest.contract_id === contract.value?.contract_id
})

// Methods
const loadContract = async () => {
  try {
    loading.value = true
    const response = await contractsApi.getContract(contractId)
    
    if (response.success !== false) {
      const contractData = response.success ? response.data : response
      contract.value = contractData
    } else {
      throw new Error(response.message || 'Failed to load contract')
    }
  } catch (error) {
    console.error('Error loading contract:', error)
    error.value = error.message
  } finally {
    loading.value = false
  }
}

const loadContractVersions = async () => {
  try {
    const response = await contractsApi.getContractVersions(contractId)
    if (response.success !== false) {
      contractVersions.value = response.success ? response.data : response
    }
  } catch (error) {
    console.error('Error loading contract versions:', error)
  }
}

// Helper functions
const getContractTypeLabel = (type) => {
  const typeLabels = {
    'MASTER_AGREEMENT': 'Master Agreement',
    'SOW': 'Statement of Work',
    'PURCHASE_ORDER': 'Purchase Order',
    'SERVICE_AGREEMENT': 'Service Agreement',
    'LICENSE': 'License',
    'NDA': 'Non-Disclosure Agreement'
  }
  return typeLabels[type] || type
}

const formatCurrency = (value) => {
  if (!value) return 'N/A'
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD'
  }).format(value)
}

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

const getStatusBadgeClass = (status) => {
  const statusConfig = {
    'DRAFT': 'bg-gray-100 text-gray-800',
    'ACTIVE': 'bg-green-100 text-green-800',
    'EXPIRED': 'bg-red-100 text-red-800',
    'TERMINATED': 'bg-red-100 text-red-800',
    'UNDER_REVIEW': 'bg-yellow-100 text-yellow-800'
  }
  return statusConfig[status] || 'bg-gray-100 text-gray-800'
}

const handleVersionSwitch = (version) => {
  // Navigate to the selected version
  navigate(`/contracts/${version.contract_id}/edit-advanced`)
}



// Initialize component
onMounted(async () => {
  await loggingService.logPageView('Contract', 'Edit Contract Advanced', contractId)
  await loadContract()
  await loadContractVersions()
})
</script>

