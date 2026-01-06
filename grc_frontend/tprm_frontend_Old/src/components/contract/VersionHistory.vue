<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h3 class="text-lg font-semibold">Version History</h3>
      <button @click="$emit('close')" class="text-muted-foreground hover:text-foreground">
        <X class="w-4 h-4" />
      </button>
    </div>
    
    <div v-if="loading" class="text-center py-8">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
      <p class="mt-2 text-sm text-muted-foreground">Loading version history...</p>
    </div>
    
    <div v-else-if="versions.length === 0" class="text-center py-8">
      <FileText class="mx-auto h-12 w-12 text-muted-foreground" />
      <h3 class="mt-2 text-sm font-semibold">No versions found</h3>
      <p class="mt-1 text-sm text-muted-foreground">
        This contract doesn't have any version history yet.
      </p>
    </div>
    
    <div v-else class="space-y-3">
      <div 
        v-for="version in versions" 
        :key="version.contract_id" 
        class="border rounded-lg p-4 hover:bg-muted/50 transition-colors"
      >
        <div class="flex items-center justify-between">
          <div class="flex-1">
            <div class="flex items-center gap-2">
              <h4 class="font-medium">{{ version.contract_title }}</h4>
              <span class="px-2 py-1 bg-primary/10 text-primary rounded-full text-xs font-medium">
                v{{ version.version_number }}
              </span>
              <span v-if="version.contract_id === currentContractId" class="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs font-medium">
                Current
              </span>
            </div>
            <p class="text-sm text-muted-foreground mt-1">{{ version.contract_number }}</p>
          </div>
          
          <div class="flex items-center gap-2">
            <span :class="getStatusBadgeClass(version.status)" class="px-2 py-1 rounded-full text-xs font-medium">
              {{ version.status }}
            </span>
            <button 
              v-if="version.contract_id !== currentContractId"
              @click="$emit('switch-version', version)"
              class="px-3 py-1 text-xs border rounded-md hover:bg-muted"
            >
              Switch to this version
            </button>
          </div>
        </div>
        
        <div class="mt-3 grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-muted-foreground">
          <div>
            <span class="font-medium">Created:</span>
            <p>{{ formatDate(version.created_at) }}</p>
          </div>
          <div v-if="version.previous_version_id">
            <span class="font-medium">Previous Version:</span>
            <p>{{ version.previous_version_id }}</p>
          </div>
          <div v-if="version.contract_value">
            <span class="font-medium">Value:</span>
            <p>${{ version.contract_value.toLocaleString() }} {{ version.currency }}</p>
          </div>
        </div>
        
        <div v-if="version.description" class="mt-3">
          <span class="font-medium text-sm">Description:</span>
          <p class="text-sm text-muted-foreground mt-1">{{ version.description }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { FileText, X } from 'lucide-vue-next'
import contractsApi from '@/services/contractsApi'

// Props
const props = defineProps({
  contractId: {
    type: Number,
    required: true
  },
  currentContractId: {
    type: Number,
    required: true
  }
})

// Emits
const emit = defineEmits(['close', 'switch-version'])

// Reactive state
const versions = ref([])
const loading = ref(false)

// Methods
const loadVersions = async () => {
  try {
    loading.value = true
    const response = await contractsApi.getContractVersions(props.contractId)
    
    if (response.success !== false) {
      versions.value = response.success ? response.data : response
    } else {
      console.error('Failed to load versions:', response.message)
    }
  } catch (error) {
    console.error('Error loading contract versions:', error)
  } finally {
    loading.value = false
  }
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

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleDateString()
}

// Initialize
onMounted(() => {
  loadVersions()
})
</script>