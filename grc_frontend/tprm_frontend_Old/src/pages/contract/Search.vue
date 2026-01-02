<template>
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <h1 class="text-3xl font-bold text-foreground">Advanced Contract Search</h1>
      <p class="text-muted-foreground">
        Search and filter contracts across your entire portfolio
      </p>
    </div>

    <!-- Search Bar -->
    <Card>
      <CardContent class="pt-6">
        <div class="flex gap-4">
          <div class="relative flex-1">
            <SearchIcon class="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
            <Input
              placeholder="Search contracts, vendors, numbers, terms..."
              v-model="searchQuery"
              class="pl-10"
            />
          </div>
          <Button 
            variant="outline" 
            @click="showAdvancedFilters = !showAdvancedFilters"
            class="gap-2"
          >
            <Filter class="w-4 h-4" />
            Filters {{ activeFiltersCount > 0 ? `(${activeFiltersCount})` : '' }}
          </Button>
          <Button variant="outline" class="gap-2">
            <BookmarkPlus class="w-4 h-4" />
            Save Search
          </Button>
        </div>
      </CardContent>
    </Card>

    <!-- Advanced Filters -->
    <Card v-if="showAdvancedFilters">
      <CardHeader>
        <CardTitle class="flex items-center justify-between">
          <span>Advanced Filters</span>
          <Button variant="ghost" size="sm" @click="clearAllFilters">
            Clear All
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <!-- Status Filter -->
          <div class="space-y-3">
            <h4 class="font-medium">Status</h4>
            <div class="space-y-2">
              <div v-for="status in ['Active', 'Draft', 'Review', 'Expired', 'Terminated']" :key="status" class="flex items-center space-x-2">
                <Checkbox
                  :id="`status-${status}`"
                  :checked="selectedFilters.status.includes(status)"
                  @update:checked="(checked) => handleFilterChange('status', status, checked)"
                />
                <Label :for="`status-${status}`" class="text-sm">
                  {{ status }}
                </Label>
              </div>
            </div>
          </div>

          <!-- Type Filter -->
          <div class="space-y-3">
            <h4 class="font-medium">Contract Type</h4>
            <div class="space-y-2">
              <div v-for="type in ['MSA', 'NDA', 'SOW', 'Service Agreement', 'Other']" :key="type" class="flex items-center space-x-2">
                <Checkbox
                  :id="`type-${type}`"
                  :checked="selectedFilters.type.includes(type)"
                  @update:checked="(checked) => handleFilterChange('type', type, checked)"
                />
                <Label :for="`type-${type}`" class="text-sm">
                  {{ type }}
                </Label>
              </div>
            </div>
          </div>

          <!-- Risk Level Filter -->
          <div class="space-y-3">
            <h4 class="font-medium">Risk Level</h4>
            <div class="space-y-2">
              <div v-for="risk in ['Low', 'Medium', 'High']" :key="risk" class="flex items-center space-x-2">
                <Checkbox
                  :id="`risk-${risk}`"
                  :checked="selectedFilters.riskLevel.includes(risk)"
                  @update:checked="(checked) => handleFilterChange('riskLevel', risk, checked)"
                />
                <Label :for="`risk-${risk}`" class="text-sm">
                  {{ risk }}
                </Label>
              </div>
            </div>
          </div>

          <!-- Date Range -->
          <div class="space-y-3">
            <h4 class="font-medium">Date Range</h4>
            <Select v-model="selectedFilters.dateRange">
              <SelectTrigger>
                <SelectValue placeholder="Select range" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="last-30">Last 30 days</SelectItem>
                <SelectItem value="last-90">Last 90 days</SelectItem>
                <SelectItem value="last-year">Last year</SelectItem>
                <SelectItem value="expiring-30">Expiring in 30 days</SelectItem>
                <SelectItem value="expiring-90">Expiring in 90 days</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- Results -->
    <div class="flex justify-between items-center">
      <p class="text-sm text-muted-foreground">
        Found {{ searchResults.length }} contracts
        <span v-if="searchQuery"> for "{{ searchQuery }}"</span>
      </p>
      <Button variant="outline" size="sm" class="gap-2">
        <Download class="w-4 h-4" />
        Export Results
      </Button>
    </div>

    <div class="grid gap-4">
      <Card 
        v-for="contract in searchResults" 
        :key="contract.id" 
        class="hover:shadow-md transition-shadow cursor-pointer"
        @click="navigateToContractByNumber(contract.contract_number)"
      >
        <CardContent class="pt-6">
          <div class="flex items-center justify-between">
            <div class="flex items-center space-x-4">
              <div class="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                <FileText class="w-5 h-5 text-primary" />
              </div>
              <div>
                <h3 class="font-semibold text-lg">{{ contract.title }}</h3>
                <p class="text-sm text-muted-foreground">
                  {{ contract.contract_number }} • {{ contract.vendor_name }}
                </p>
              </div>
            </div>
            
            <div class="flex items-center space-x-4">
              <div class="text-right">
                <div class="flex items-center gap-2">
                  <DollarSign class="w-4 h-4 text-muted-foreground" />
                  <span class="font-medium">${{ contract.value.toLocaleString() }}</span>
                </div>
                <div class="flex items-center gap-2 text-sm text-muted-foreground">
                  <Calendar class="w-3 h-3" />
                  <span>Expires {{ new Date(contract.end_date).toLocaleDateString() }}</span>
                </div>
              </div>
              
              <div class="flex flex-col items-end gap-2">
                <Badge :class="getStatusBadgeClass(contract.status)">{{ contract.status }}</Badge>
                <Badge variant="outline">{{ contract.type }}</Badge>
              </div>
              
              <Button
                variant="ghost"
                size="icon"
                @click.stop="() => {
                  console.log('Eye icon clicked for contract:', contract)
                  console.log('Contract Number:', contract.contract_number)
                  navigateToContractByNumber(contract.contract_number)
                }"
              >
                <Eye class="w-4 h-4" />
              </Button>
            </div>
          </div>

          <div class="mt-4 flex items-center justify-between">
            <div class="flex items-center gap-4 text-sm text-muted-foreground">
              <div class="flex items-center gap-1">
                <Building class="w-3 h-3" />
                <span>Owner: {{ contract.owner }}</span>
              </div>
              <Badge 
                variant="outline" 
                :class="getRiskLevelClass(contract.risk_level)"
              >
                {{ contract.risk_level }} Risk
              </Badge>
            </div>
            
            <div v-if="contract.compliance_frameworks.length > 0" class="flex gap-1">
              <Badge 
                v-for="framework in contract.compliance_frameworks.slice(0, 2)" 
                :key="framework" 
                variant="secondary" 
                class="text-xs"
              >
                {{ framework }}
              </Badge>
              <Badge 
                v-if="contract.compliance_frameworks.length > 2" 
                variant="secondary" 
                class="text-xs"
              >
                +{{ contract.compliance_frameworks.length - 2 }}
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card v-if="searchResults.length === 0">
        <CardContent class="text-center py-12">
          <SearchIcon class="mx-auto h-12 w-12 text-muted-foreground" />
          <h3 class="mt-2 text-lg font-semibold">No contracts found</h3>
          <p class="mt-1 text-sm text-muted-foreground">
            Try adjusting your search query or filters.
          </p>
          <Button @click="clearAllFilters" class="mt-4">
            Clear all filters
          </Button>
        </CardContent>
      </Card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import loggingService from '@/services/loggingService'
import { 
  Card, CardContent, CardDescription, CardHeader, CardTitle,
  Badge, Button, Input, Label, Checkbox, Select, SelectContent, SelectItem, SelectTrigger, SelectValue
} from '@/components/ui_contract'
import { 
  Search as SearchIcon, Filter, BookmarkPlus, Download, Eye, FileText, Calendar, DollarSign, Building 
} from 'lucide-vue-next'

const router = useRouter()

// State
const searchQuery = ref('')
const showAdvancedFilters = ref(false)
const selectedFilters = ref({
  status: [],
  type: [],
  riskLevel: [],
  vendor: [],
  dateRange: '',
  valueRange: ''
})

// Mock data - you can replace this with actual data from your API
const mockContracts = ref([
  {
    id: 1,
    title: "Cloud Infrastructure Services Agreement",
    contract_number: "CNT-2024-001",
    vendor_name: "TechCloud Solutions Inc.",
    owner: "John Smith",
    status: "Active",
    type: "Service Agreement",
    value: 150000,
    end_date: "2025-01-14",
    risk_level: "Medium",
    compliance_frameworks: ["SOC2", "ISO27001"]
  },
  {
    id: 2,
    title: "Software Development Project Agreement",
    contract_number: "CNT-2024-002",
    vendor_name: "CodeCraft Solutions Ltd.",
    owner: "Jane Doe",
    status: "Draft",
    type: "Project Agreement",
    value: 200000,
    end_date: "2024-12-31",
    risk_level: "High",
    compliance_frameworks: ["ISO27001", "HIPAA"]
  },
  {
    id: 3,
    title: "Data Analytics Services Agreement",
    contract_number: "CNT-2024-003",
    vendor_name: "DataMind Inc.",
    owner: "Michael Brown",
    status: "Expired",
    type: "Service Agreement",
    value: 100000,
    end_date: "2023-12-31",
    risk_level: "Low",
    compliance_frameworks: ["SOC2"]
  },
  {
    id: 4,
    title: "IT Infrastructure Maintenance Contract",
    contract_number: "CNT-2024-004",
    vendor_name: "TechGuard Solutions",
    owner: "Sarah Wilson",
    status: "Active",
    type: "Maintenance Agreement",
    value: 80000,
    end_date: "2025-02-28",
    risk_level: "Medium",
    compliance_frameworks: ["ISO27001", "PCI DSS"]
  },
  {
    id: 5,
    title: "Consulting Services Agreement",
    contract_number: "CNT-2024-005",
    vendor_name: "Expert Advisors LLC",
    owner: "Michael Chen",
    status: "Review",
    type: "Service Agreement",
    value: 120000,
    end_date: "2025-04-09",
    risk_level: "Low",
    compliance_frameworks: ["ISO27001"]
  }
])

// Computed
const searchResults = computed(() => {
  return mockContracts.value.filter(contract => {
    if (searchQuery.value) {
      const query = searchQuery.value.toLowerCase()
      const matchesQuery = 
        contract.title.toLowerCase().includes(query) ||
        contract.vendor_name.toLowerCase().includes(query) ||
        contract.contract_number.toLowerCase().includes(query) ||
        contract.owner.toLowerCase().includes(query)
      
      if (!matchesQuery) return false
    }

    // Apply filters
    if (selectedFilters.value.status.length > 0 && !selectedFilters.value.status.includes(contract.status)) {
      return false
    }
    if (selectedFilters.value.type.length > 0 && !selectedFilters.value.type.includes(contract.type)) {
      return false
    }
    if (selectedFilters.value.riskLevel.length > 0 && !selectedFilters.value.riskLevel.includes(contract.risk_level)) {
      return false
    }

    return true
  })
})

const activeFiltersCount = computed(() => {
  return Object.values(selectedFilters.value).flat().filter(Boolean).length
})

// Methods
const handleFilterChange = (filterType, value, checked) => {
  if (checked) {
    selectedFilters.value[filterType] = [...selectedFilters.value[filterType], value]
  } else {
    selectedFilters.value[filterType] = selectedFilters.value[filterType].filter(item => item !== value)
  }
}

const clearAllFilters = () => {
  selectedFilters.value = {
    status: [],
    type: [],
    riskLevel: [],
    vendor: [],
    dateRange: '',
    valueRange: ''
  }
  searchQuery.value = ''
}

const getStatusBadgeClass = (status) => {
  const variants = {
    'Active': 'bg-success text-success-foreground',
    'Draft': 'bg-muted text-muted-foreground',
    'Review': 'bg-warning text-warning-foreground',
    'Expired': 'bg-destructive text-destructive-foreground',
    'Terminated': 'bg-destructive text-destructive-foreground',
    'Renewed': 'bg-success text-success-foreground'
  }
  
  return variants[status] || 'bg-muted text-muted-foreground'
}

const getRiskLevelClass = (riskLevel) => {
  if (riskLevel === 'High') return 'border-destructive text-destructive'
  if (riskLevel === 'Medium') return 'border-warning text-warning'
  return 'border-success text-success'
}

const navigateToContract = (contractId) => {
  router.push(`/contracts/${contractId}`)
}

const navigateToContractByNumber = (contractNumber) => {
  router.push(`/contracts/${contractNumber}`)
}

// Log page view on mount
onMounted(async () => {
  await loggingService.logPageView('Contract', 'Contract Search')
})
</script>
