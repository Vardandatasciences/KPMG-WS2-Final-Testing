<template>
  <div class="space-y-6">
    <!-- Results Summary -->
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-4">
        <h2 class="text-xl font-semibold">Search Results</h2>
        <Badge variant="secondary">
          {{ searchResults.length }} results
        </Badge>
      </div>
      
      <!-- Pagination Controls -->
      <div class="flex items-center gap-2">
        <span class="text-sm text-muted-foreground">Results per page:</span>
        <select 
          v-model="localPageSize" 
          @change="handlePageSizeChange"
          class="px-2 py-1 border rounded text-sm"
        >
          <option value="10">10</option>
          <option value="20">20</option>
          <option value="50">50</option>
          <option value="100">100</option>
        </select>
      </div>
    </div>

    <!-- Module Tabs -->
    <div v-if="groupedResults.length > 0" class="space-y-6">
      <!-- Horizontal Module Tab Bar -->
      <div class="flex flex-wrap justify-center gap-2 p-4 bg-muted/20 rounded-lg">
        <button
          v-for="group in groupedResults"
          :key="group.entityType"
          @click="selectModule(group.entityType)"
          :class="`flex items-center gap-2 px-4 py-2 rounded-md font-medium transition-all duration-200 ${
            selectedModule === group.entityType 
              ? 'text-white shadow-md' 
              : 'bg-background hover:bg-muted text-foreground hover:shadow-sm'
          }`"
          :style="selectedModule === group.entityType ? { backgroundColor: getModuleColor(group.entityType) } : {}"
        >
          <div 
            :class="`w-5 h-5 rounded flex items-center justify-center ${
              selectedModule === group.entityType ? 'text-white' : 'text-white'
            }`"
            :style="selectedModule !== group.entityType ? { backgroundColor: getModuleColor(group.entityType) } : {}"
          >
            <component :is="getModuleIcon(group.entityType)" class="h-3 w-3" />
          </div>
          <span>{{ getModuleLabel(group.entityType) }}</span>
          <Badge 
            :variant="selectedModule === group.entityType ? 'secondary' : 'outline'"
            :class="selectedModule === group.entityType ? 'bg-white/20 text-white border-white/30' : ''"
          >
            {{ group.results.length }}
          </Badge>
        </button>
      </div>

      <!-- Selected Module Results -->
      <div v-if="selectedModuleResults" class="space-y-4">
        <div class="flex items-center justify-between">
          <h3 class="text-xl font-semibold flex items-center gap-2">
            <div 
              :class="`w-6 h-6 rounded flex items-center justify-center text-white`"
              :style="{ backgroundColor: getModuleColor(selectedModule) }"
            >
              <component :is="getModuleIcon(selectedModule)" class="h-3 w-3" />
            </div>
            {{ getModuleLabel(selectedModule) }}
            <Badge variant="secondary">{{ selectedModuleResults.length }} results</Badge>
          </h3>
        </div>

        <!-- Results Grid -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <SearchResultCard_TPRM
            v-for="result in selectedModuleResults"
            :key="result.id"
            :result="result"
            :search-terms="searchTerms"
            :show-details="false"
            @click="handleResultClick"
            @view-details="handleViewDetails"
            @edit="handleEdit"
          />
        </div>
      </div>
    </div>

    <!-- No Results -->
    <div v-else-if="!isLoading" class="text-center py-12">
      <Search class="h-16 w-16 mx-auto text-muted-foreground mb-4" />
      <div class="text-xl font-semibold mb-2">No results found</div>
      <div class="text-muted-foreground">Try adjusting your search terms or filters</div>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="text-center py-12">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
      <div class="mt-4 text-muted-foreground">Loading results...</div>
    </div>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="flex items-center justify-between">
      <div class="text-sm text-muted-foreground">
        Showing {{ startItem }} to {{ endItem }} of {{ totalResults }} results
      </div>
      
      <div class="flex items-center gap-2">
        <Button 
          variant="outline" 
          size="sm"
          @click="handlePageChange(currentPage - 1)"
          :disabled="currentPage <= 1"
        >
          <ChevronLeft class="h-4 w-4" />
          Previous
        </Button>
        
        <div class="flex items-center gap-1">
          <Button
            v-for="page in visiblePages"
            :key="page"
            :variant="page === currentPage ? 'default' : 'outline'"
            size="sm"
            @click="handlePageChange(page)"
            class="w-8 h-8 p-0"
          >
            {{ page }}
          </Button>
        </div>
        
        <Button 
          variant="outline" 
          size="sm"
          @click="handlePageChange(currentPage + 1)"
          :disabled="currentPage >= totalPages"
        >
          Next
          <ChevronRight class="h-4 w-4" />
        </Button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import SearchResultCard_TPRM from './SearchResultCard_TPRM.vue'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

// Icons
import { 
  Search, 
  ChevronLeft, 
  ChevronRight,
  FileText, 
  Building2, 
  Users, 
  Shield, 
  FileCheck
} from 'lucide-vue-next'

const props = defineProps({
  searchResults: {
    type: Array,
    required: true
  },
  searchQuery: {
    type: String,
    default: ''
  },
  searchTerms: {
    type: Array,
    default: () => []
  },
  isLoading: {
    type: Boolean,
    default: false
  },
  pageSize: {
    type: Number,
    default: 20
  },
  currentPage: {
    type: Number,
    default: 1
  },
  selectedModules: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['page-change', 'page-size-change'])

// Local state
const localPageSize = ref(props.pageSize)
const selectedModule = ref('')

// Computed properties
const groupedResults = computed(() => {
  const groups = {}
  
  props.searchResults.forEach(result => {
    const entityType = result.module || 'unknown'
    
    if (!groups[entityType]) {
      groups[entityType] = {
        entityType,
        results: []
      }
    }
    
    groups[entityType].results.push(result)
  })
  
  // Filter out groups with no results and sort by entity type order
  const entityOrder = ['contract', 'vendor', 'rfp', 'sla', 'bcp_drp']
  return Object.values(groups)
    .filter(group => group.results.length > 0) // Only show modules with actual results
    .sort((a, b) => {
      const aIndex = entityOrder.indexOf(a.entityType)
      const bIndex = entityOrder.indexOf(b.entityType)
      return aIndex - bIndex
    })
})

const selectedModuleResults = computed(() => {
  if (!selectedModule.value) return []
  const group = groupedResults.value.find(g => g.entityType === selectedModule.value)
  return group ? group.results : []
})

const totalResults = computed(() => props.searchResults.length)
const totalPages = computed(() => Math.ceil(totalResults.value / localPageSize.value))
const startItem = computed(() => (props.currentPage - 1) * localPageSize.value + 1)
const endItem = computed(() => Math.min(props.currentPage * localPageSize.value, totalResults.value))

const visiblePages = computed(() => {
  const pages = []
  const maxVisible = 5
  const halfVisible = Math.floor(maxVisible / 2)
  
  let start = Math.max(1, props.currentPage - halfVisible)
  let end = Math.min(totalPages.value, start + maxVisible - 1)
  
  if (end - start + 1 < maxVisible) {
    start = Math.max(1, end - maxVisible + 1)
  }
  
  for (let i = start; i <= end; i++) {
    pages.push(i)
  }
  
  return pages
})

// Methods
const selectModule = (entityType) => {
  selectedModule.value = entityType
}

const initializeSelectedModule = () => {
  // Select the first module with results, not just the first module
  if (groupedResults.value.length > 0 && !selectedModule.value) {
    // Find the first module that actually has results
    const moduleWithResults = groupedResults.value.find(group => group.results.length > 0)
    
    if (moduleWithResults) {
      selectedModule.value = moduleWithResults.entityType
      console.log('Auto-selected module with results:', moduleWithResults.entityType, 'with', moduleWithResults.results.length, 'results')
    } else {
      // Fallback: select first module even if it has no results (shouldn't happen)
      selectedModule.value = groupedResults.value[0].entityType
      console.log('Fallback: selected first module:', selectedModule.value)
    }
  }
}

const handlePageChange = (page) => {
  if (page >= 1 && page <= totalPages.value) {
    emit('page-change', page)
  }
}

const handlePageSizeChange = () => {
  emit('page-size-change', localPageSize.value)
}

const handleResultClick = (result) => {
  console.log('Result clicked:', result)
}

const handleViewDetails = (result) => {
  console.log('View details:', result)
}

const handleEdit = (result) => {
  console.log('Edit result:', result)
}

const getModuleColor = (module) => {
  const colors = {
    contract: '#3b82f6',
    vendor: '#10b981',
    rfp: '#f59e0b',
    sla: '#8b5cf6',
    bcp_drp: '#ef4444'
  }
  return colors[module] || '#6b7280'
}

const getModuleIcon = (module) => {
  const icons = {
    contract: FileText,
    vendor: Building2,
    rfp: Users,
    sla: Shield,
    bcp_drp: FileCheck
  }
  return icons[module] || FileText
}

const getModuleLabel = (module) => {
  const labels = {
    contract: 'Contracts',
    vendor: 'Vendors',
    rfp: 'RFPs',
    sla: 'SLAs',
    bcp_drp: 'BCP/DRP Plans'
  }
  return labels[module] || module
}

// Watch for prop changes
watch(() => props.pageSize, (newSize) => {
  localPageSize.value = newSize
})

// Watch for search results changes to initialize selected module
watch(() => props.searchResults, () => {
  // Reset selected module when search results change
  selectedModule.value = ''
  initializeSelectedModule()
}, { immediate: true })

// Also watch for grouped results changes
watch(groupedResults, () => {
  initializeSelectedModule()
}, { immediate: true })
</script>

<style scoped>
/* Custom select styling */
select {
  background-color: hsl(var(--background));
  border-color: hsl(var(--border));
  color: hsl(var(--foreground));
}

select:focus {
  outline: 2px solid hsl(var(--ring));
  outline-offset: 2px;
}
</style>
