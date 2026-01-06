<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h3 class="text-lg font-semibold">Search Filters</h3>
      <Button 
        variant="outline" 
        size="sm" 
        @click="clearAllFilters"
        :disabled="!hasActiveFilters"
      >
        Clear All
      </Button>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
      <!-- Module Filter -->
      <div class="space-y-2">
        <label class="text-sm font-medium text-muted-foreground">Modules</label>
        <MultiSelectDropdown
          v-model="localFilters.module"
          :options="availableModules"
          placeholder="Select modules..."
          :selected-count="localFilters.module.length"
        />
      </div>

      <!-- Status Filter -->
      <div class="space-y-2">
        <label class="text-sm font-medium text-muted-foreground">Status</label>
        <MultiSelectDropdown
          v-model="localFilters.status"
          :options="availableStatuses"
          placeholder="Select status..."
          :selected-count="localFilters.status.length"
        />
      </div>

      <!-- Category Filter -->
      <div class="space-y-2">
        <label class="text-sm font-medium text-muted-foreground">Category</label>
        <MultiSelectDropdown
          v-model="localFilters.category"
          :options="availableCategories"
          placeholder="Select categories..."
          :selected-count="localFilters.category.length"
        />
      </div>

      <!-- Risk Level Filter -->
      <div class="space-y-2">
        <label class="text-sm font-medium text-muted-foreground">Risk Level</label>
        <MultiSelectDropdown
          v-model="localFilters.risk_level"
          :options="availableRiskLevels"
          placeholder="Select risk levels..."
          :selected-count="localFilters.risk_level.length"
        />
      </div>
    </div>

    <!-- Active Filters Summary -->
    <div v-if="hasActiveFilters" class="pt-4 border-t border-border">
      <div class="flex items-center gap-2 flex-wrap">
        <span class="text-sm font-medium text-muted-foreground">Active filters:</span>
        
        <!-- Module filters -->
        <Badge 
          v-for="module in localFilters.module" 
          :key="`module-${module}`"
          variant="secondary"
          class="text-xs"
        >
          {{ getModuleLabel(module) }}
        </Badge>
        
        <!-- Status filters -->
        <Badge 
          v-for="status in localFilters.status" 
          :key="`status-${status}`"
          variant="outline"
          class="text-xs"
        >
          {{ status }}
        </Badge>
        
        <!-- Category filters -->
        <Badge 
          v-for="category in localFilters.category" 
          :key="`category-${category}`"
          variant="secondary"
          class="text-xs"
        >
          {{ category }}
        </Badge>
        
        <!-- Risk level filters -->
        <Badge 
          v-for="risk in localFilters.risk_level" 
          :key="`risk-${risk}`"
          :variant="getRiskVariant(risk)"
          class="text-xs"
        >
          {{ risk.toUpperCase() }}
        </Badge>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { searchAPI } from '@/services/globalsearch_api'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import MultiSelectDropdown from './MultiSelectDropdown.vue'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({
      module: [],
      status: [],
      category: [],
      risk_level: []
    })
  }
})

const emit = defineEmits(['update:modelValue'])

// Local reactive filters
const createFilterState = (source = {}) => ({
  module: Array.isArray(source.module) ? [...source.module] : [],
  status: Array.isArray(source.status) ? [...source.status] : [],
  category: Array.isArray(source.category) ? [...source.category] : [],
  risk_level: Array.isArray(source.risk_level) ? [...source.risk_level] : []
})

const localFilters = ref(createFilterState(props.modelValue))
let syncingFromParent = false

// Available filter options
const availableModules = ref([
  { value: 'contract', label: 'Contracts' },
  { value: 'vendor', label: 'Vendors' },
  { value: 'rfp', label: 'RFPs' },
  { value: 'sla', label: 'SLAs' },
  { value: 'bcp', label: 'BCP/DRP' }
])

const availableStatuses = ref([
  { value: 'active', label: 'Active' },
  { value: 'draft', label: 'Draft' },
  { value: 'pending', label: 'Pending' },
  { value: 'completed', label: 'Completed' },
  { value: 'expired', label: 'Expired' }
])

const availableCategories = ref([
  { value: 'technology', label: 'Technology' },
  { value: 'finance', label: 'Finance' },
  { value: 'operations', label: 'Operations' },
  { value: 'legal', label: 'Legal' },
  { value: 'hr', label: 'Human Resources' }
])

const availableRiskLevels = ref([
  { value: 'low', label: 'Low' },
  { value: 'medium', label: 'Medium' },
  { value: 'high', label: 'High' },
  { value: 'critical', label: 'Critical' }
])

// Computed properties
const hasActiveFilters = computed(() => {
  return localFilters.value.module.length > 0 ||
         localFilters.value.status.length > 0 ||
         localFilters.value.category.length > 0 ||
         localFilters.value.risk_level.length > 0
})

// Methods
const clearAllFilters = () => {
  localFilters.value = createFilterState()
}

const getModuleLabel = (module) => {
  const moduleObj = availableModules.value.find(m => m.value === module)
  return moduleObj ? moduleObj.label : module
}

const getRiskVariant = (risk) => {
  const variants = {
    low: 'default',
    medium: 'secondary',
    high: 'destructive',
    critical: 'destructive'
  }
  return variants[risk] || 'outline'
}

const loadFilterOptions = async () => {
  try {
    const response = await searchAPI.getFilterOptions()
    
    if (response.modules) {
      availableModules.value = Object.entries(response.modules).map(([value, label]) => ({
        value,
        label: typeof label === 'string' ? label : value
      }))
    }
    
    if (response.statuses) {
      availableStatuses.value = Object.entries(response.statuses).map(([value, label]) => ({
        value,
        label: typeof label === 'string' ? label : value
      }))
    }
    
    if (response.categories) {
      availableCategories.value = Object.entries(response.categories).map(([value, label]) => ({
        value,
        label: typeof label === 'string' ? label : value
      }))
    }
    
    if (response.risk_levels) {
      availableRiskLevels.value = Object.entries(response.risk_levels).map(([value, label]) => ({
        value,
        label: typeof label === 'string' ? label : value
      }))
    }
  } catch (error) {
    console.error('Failed to load filter options:', error)
    // Use default options if API fails
  }
}

// Watch for changes and emit updates
watch(localFilters, (newFilters) => {
  if (syncingFromParent) return
  emit('update:modelValue', createFilterState(newFilters))
}, { deep: true })

// Watch for prop changes
watch(() => props.modelValue, (newValue) => {
  if (!newValue) return
  syncingFromParent = true
  localFilters.value = createFilterState(newValue)
  nextTick(() => {
    syncingFromParent = false
  })
}, { immediate: true, deep: true })

// Initialize
onMounted(() => {
  loadFilterOptions()
})
</script>

