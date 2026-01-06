<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-3xl font-bold text-foreground">Contract Comparison</h1>
        <p class="text-muted-foreground">Compare contracts and amendments to see the differences</p>
      </div>
    </div>

    <!-- Contract Selection -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <!-- Original Contract Selection -->
      <div class="border rounded-lg p-6">
        <h3 class="text-lg font-semibold mb-4 flex items-center gap-2">
          <FileText class="w-5 h-5" />
          Original Contract
        </h3>
        <div class="space-y-4">
          <div>
            <label class="text-sm font-medium">Select Original Contract</label>
            <select v-model="selectedOriginalContract" class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground">
              <option :value="null">Choose original contract...</option>
              <option v-for="contract in contracts" :key="contract.contract_id" :value="contract.contract_id">
                {{ contract.contract_title }} ({{ contract.contract_number || 'No Number' }})
              </option>
            </select>
          </div>
          <div v-if="originalContractDetails" class="p-4 bg-muted rounded-lg">
            <h4 class="font-medium">{{ originalContractDetails.contract_title }}</h4>
            <p class="text-sm text-muted-foreground">Contract #{{ originalContractDetails.contract_number || 'N/A' }}</p>
            <p class="text-sm text-muted-foreground">Version: {{ originalContractDetails.version_number || '1.0' }}</p>
          </div>
        </div>
      </div>

      <!-- Amendment Contract Selection -->
      <div class="border rounded-lg p-6">
        <h3 class="text-lg font-semibold mb-4 flex items-center gap-2">
          <GitCompare class="w-5 h-5" />
          Amendment Contract
        </h3>
        <div class="space-y-4">
          <div>
            <label class="text-sm font-medium">Select Amendment Contract</label>
            <select v-model="selectedAmendmentContract" class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground" :disabled="!selectedOriginalContract">
              <option :value="null">
                {{ selectedOriginalContract ? 'Choose amendment contract...' : 'Select original contract first' }}
              </option>
              <option v-for="contract in filteredAmendmentContracts" :key="contract.contract_id" :value="contract.contract_id">
                {{ contract.contract_title }} ({{ contract.contract_number || 'No Number' }})
              </option>
            </select>
            
            <!-- Help text for amendment selection -->
            <div v-if="selectedOriginalContract" class="text-xs text-muted-foreground">
              <div v-if="filteredAmendmentContracts.length > 0">
                Showing {{ filteredAmendmentContracts.length }} amendment(s) for the selected contract
              </div>
              <div v-else class="text-orange-600">
                No amendments found for this contract
              </div>
            </div>
          </div>
          <div v-if="amendmentContractDetails" class="p-4 bg-muted rounded-lg">
            <h4 class="font-medium">{{ amendmentContractDetails.contract_title }}</h4>
            <p class="text-sm text-muted-foreground">Contract #{{ amendmentContractDetails.contract_number || 'N/A' }}</p>
            <p class="text-sm text-muted-foreground">Version: {{ amendmentContractDetails.version_number || '1.0' }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Compare Button -->
    <div class="flex justify-center">
      <button 
        @click="compareContracts" 
        :disabled="!selectedOriginalContract || !selectedAmendmentContract || loading"
        class="inline-flex items-center gap-2 px-6 py-3 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <GitCompare class="w-4 h-4" />
        {{ loading ? 'Comparing...' : 'Compare Contracts' }}
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-12">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
      <h3 class="mt-2 text-sm font-semibold text-foreground">Comparing contracts...</h3>
      <p class="mt-1 text-sm text-muted-foreground">Please wait while we analyze the differences</p>
    </div>

    <!-- Comparison Results -->
    <div v-if="comparisonData && !loading" class="space-y-6">
      <!-- Summary Cards -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div class="border rounded-lg p-4">
          <div class="flex items-center gap-2">
            <FileText class="w-4 h-4 text-blue-600" />
            <span class="text-sm font-medium">Contract Fields</span>
          </div>
          <div class="text-2xl font-bold mt-1">{{ comparisonData.summary.contract_fields_changed }}</div>
          <div class="text-xs text-muted-foreground">Fields changed</div>
        </div>
        <div class="border rounded-lg p-4">
          <div class="flex items-center gap-2">
            <Plus class="w-4 h-4 text-green-600" />
            <span class="text-sm font-medium">Terms Added</span>
          </div>
          <div class="text-2xl font-bold mt-1">{{ comparisonData.summary.terms_added }}</div>
          <div class="text-xs text-muted-foreground">New terms</div>
        </div>
        <div class="border rounded-lg p-4">
          <div class="flex items-center gap-2">
            <AlertTriangle class="w-4 h-4 text-orange-600" />
            <span class="text-sm font-medium">Terms Modified</span>
          </div>
          <div class="text-2xl font-bold mt-1">{{ comparisonData.summary.terms_modified }}</div>
          <div class="text-xs text-muted-foreground">Modified terms</div>
        </div>
        <div class="border rounded-lg p-4">
          <div class="flex items-center gap-2">
            <Trash2 class="w-4 h-4 text-red-600" />
            <span class="text-sm font-medium">Terms Removed</span>
          </div>
          <div class="text-2xl font-bold mt-1">{{ comparisonData.summary.terms_removed }}</div>
          <div class="text-xs text-muted-foreground">Removed terms</div>
        </div>
      </div>

      <!-- Contract Basic Information Comparison -->
      <div v-if="comparisonData.contract_changes.length > 0" class="border rounded-lg p-6">
        <h4 class="text-lg font-semibold mb-4 flex items-center gap-2">
          <FileText class="w-5 h-5" />
          Contract Basic Information Changes
        </h4>
        <div class="space-y-4">
          <div v-for="change in comparisonData.contract_changes" :key="change.field" class="grid grid-cols-3 gap-4 items-center p-4 bg-muted rounded-lg">
            <div class="text-sm font-medium text-muted-foreground">
              {{ formatFieldName(change.field) }}
            </div>
            <div class="text-sm p-2 bg-red-50 border border-red-200 rounded">
              <span class="font-medium text-red-800">Original:</span>
              <div class="text-red-700">{{ formatValue(change.original) }}</div>
            </div>
            <div class="text-sm p-2 bg-green-50 border border-green-200 rounded">
              <span class="font-medium text-green-800">Amendment:</span>
              <div class="text-green-700">{{ formatValue(change.amendment) }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Contract Terms Comparison -->
      <div class="border rounded-lg p-6">
        <h4 class="text-lg font-semibold mb-4 flex items-center gap-2">
          <FileCheck class="w-5 h-5" />
          Contract Terms Changes
        </h4>
        
        <!-- Terms Added -->
        <div v-if="comparisonData.terms_changes.added.length > 0" class="mb-6">
          <h5 class="text-md font-medium text-green-800 mb-3">➕ Terms Added ({{ comparisonData.terms_changes.added.length }})</h5>
          <div class="space-y-3">
            <div v-for="term in comparisonData.terms_changes.added" :key="term.term_id" class="p-4 bg-green-50 border border-green-200 rounded-lg">
              <div class="text-sm font-medium text-green-800">{{ term.term_title || 'Untitled Term' }}</div>
              <div class="text-xs text-green-700 mt-1">{{ term.term_text }}</div>
              <div class="flex gap-2 mt-2">
                <span class="text-xs px-2 py-1 bg-green-200 text-green-800 rounded">{{ term.term_category }}</span>
                <span class="text-xs px-2 py-1 bg-green-200 text-green-800 rounded">{{ term.risk_level }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Terms Modified -->
        <div v-if="comparisonData.terms_changes.modified.length > 0" class="mb-6">
          <h5 class="text-md font-medium text-orange-800 mb-3">🔄 Terms Modified ({{ comparisonData.terms_changes.modified.length }})</h5>
          <div class="space-y-3">
            <div v-for="change in comparisonData.terms_changes.modified" :key="change.original.term_id" class="p-4 bg-orange-50 border border-orange-200 rounded-lg">
              <div class="text-sm font-medium text-orange-800">{{ change.original.term_title || 'Untitled Term' }}</div>
              <div class="grid grid-cols-2 gap-4 mt-2">
                <div>
                  <div class="text-xs font-medium text-red-800">Original:</div>
                  <div class="text-xs text-red-700">{{ change.original.term_text }}</div>
                </div>
                <div>
                  <div class="text-xs font-medium text-green-800">Modified:</div>
                  <div class="text-xs text-green-700">{{ change.amendment.term_text }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Terms Removed -->
        <div v-if="comparisonData.terms_changes.removed.length > 0" class="mb-6">
          <h5 class="text-md font-medium text-red-800 mb-3">➖ Terms Removed ({{ comparisonData.terms_changes.removed.length }})</h5>
          <div class="space-y-3">
            <div v-for="term in comparisonData.terms_changes.removed" :key="term.term_id" class="p-4 bg-red-50 border border-red-200 rounded-lg">
              <div class="text-sm font-medium text-red-800">{{ term.term_title || 'Untitled Term' }}</div>
              <div class="text-xs text-red-700 mt-1">{{ term.term_text }}</div>
              <div class="flex gap-2 mt-2">
                <span class="text-xs px-2 py-1 bg-red-200 text-red-800 rounded">{{ term.term_category }}</span>
                <span class="text-xs px-2 py-1 bg-red-200 text-red-800 rounded">{{ term.risk_level }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- No Changes -->
        <div v-if="comparisonData.terms_changes.added.length === 0 && comparisonData.terms_changes.modified.length === 0 && comparisonData.terms_changes.removed.length === 0" class="text-center py-8 text-muted-foreground">
          No changes to contract terms
        </div>
      </div>

      <!-- Contract Clauses Comparison -->
      <div class="border rounded-lg p-6">
        <h4 class="text-lg font-semibold mb-4 flex items-center gap-2">
          <FileText class="w-5 h-5" />
          Contract Clauses Changes
        </h4>
        
        <!-- Clauses Added -->
        <div v-if="comparisonData.clauses_changes.added.length > 0" class="mb-6">
          <h5 class="text-md font-medium text-green-800 mb-3">➕ Clauses Added ({{ comparisonData.clauses_changes.added.length }})</h5>
          <div class="space-y-3">
            <div v-for="clause in comparisonData.clauses_changes.added" :key="clause.clause_id" class="p-4 bg-green-50 border border-green-200 rounded-lg">
              <div class="text-sm font-medium text-green-800">{{ clause.clause_name || 'Untitled Clause' }}</div>
              <div class="text-xs text-green-700 mt-1">{{ clause.clause_text }}</div>
              <div class="flex gap-2 mt-2">
                <span class="text-xs px-2 py-1 bg-green-200 text-green-800 rounded">{{ clause.clause_type }}</span>
                <span class="text-xs px-2 py-1 bg-green-200 text-green-800 rounded">{{ clause.risk_level }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Clauses Modified -->
        <div v-if="comparisonData.clauses_changes.modified.length > 0" class="mb-6">
          <h5 class="text-md font-medium text-orange-800 mb-3">🔄 Clauses Modified ({{ comparisonData.clauses_changes.modified.length }})</h5>
          <div class="space-y-3">
            <div v-for="change in comparisonData.clauses_changes.modified" :key="change.original.clause_id" class="p-4 bg-orange-50 border border-orange-200 rounded-lg">
              <div class="text-sm font-medium text-orange-800">{{ change.original.clause_name || 'Untitled Clause' }}</div>
              <div class="grid grid-cols-2 gap-4 mt-2">
                <div>
                  <div class="text-xs font-medium text-red-800">Original:</div>
                  <div class="text-xs text-red-700">{{ change.original.clause_text }}</div>
                </div>
                <div>
                  <div class="text-xs font-medium text-green-800">Modified:</div>
                  <div class="text-xs text-green-700">{{ change.amendment.clause_text }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Clauses Removed -->
        <div v-if="comparisonData.clauses_changes.removed.length > 0" class="mb-6">
          <h5 class="text-md font-medium text-red-800 mb-3">➖ Clauses Removed ({{ comparisonData.clauses_changes.removed.length }})</h5>
          <div class="space-y-3">
            <div v-for="clause in comparisonData.clauses_changes.removed" :key="clause.clause_id" class="p-4 bg-red-50 border border-red-200 rounded-lg">
              <div class="text-sm font-medium text-red-800">{{ clause.clause_name || 'Untitled Clause' }}</div>
              <div class="text-xs text-red-700 mt-1">{{ clause.clause_text }}</div>
              <div class="flex gap-2 mt-2">
                <span class="text-xs px-2 py-1 bg-red-200 text-red-800 rounded">{{ clause.clause_type }}</span>
                <span class="text-xs px-2 py-1 bg-red-200 text-red-800 rounded">{{ clause.risk_level }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- No Changes -->
        <div v-if="comparisonData.clauses_changes.added.length === 0 && comparisonData.clauses_changes.modified.length === 0 && comparisonData.clauses_changes.removed.length === 0" class="text-center py-8 text-muted-foreground">
          No changes to contract clauses
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="flex justify-end gap-3 pt-6 border-t">
        <button 
          @click="downloadComparisonReport" 
          class="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          <Download class="w-4 h-4" />
          Download Report
        </button>
        <button 
          @click="resetComparison" 
          class="inline-flex items-center gap-2 px-4 py-2 border border-input rounded-md hover:bg-muted"
        >
          <RotateCcw class="w-4 h-4" />
          Reset
        </button>
      </div>
    </div>

    <!-- Error Message -->
    <div v-if="errorMessage" class="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
      <div class="flex items-center gap-2 text-red-800">
        <AlertTriangle class="w-5 h-5" />
        <span>{{ errorMessage }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { 
  FileText, 
  GitCompare, 
  FileCheck, 
  Plus, 
  AlertTriangle, 
  Trash2,
  Download,
  RotateCcw
} from 'lucide-vue-next'
import contractsApi from '@/services/contractsApi'
import loggingService from '@/services/loggingService'

const route = useRoute()

// Reactive state
const loading = ref(false)
const errorMessage = ref('')
const contracts = ref([])
const amendmentContracts = ref([])
const selectedOriginalContract = ref(null)
const selectedAmendmentContract = ref(null)
const comparisonData = ref(null)

// Contract details
const originalContractDetails = ref(null)
const amendmentContractDetails = ref(null)

// Computed property for filtered amendment contracts
const filteredAmendmentContracts = computed(() => {
  if (!selectedOriginalContract.value) {
    console.log('🔍 No original contract selected, returning empty amendments list')
    return []
  }
  
  const filtered = amendmentContracts.value.filter(contract => 
    contract.parent_contract_id === selectedOriginalContract.value && 
    contract.contract_kind === 'AMENDMENT'
  )
  
  console.log('🔍 Filtering amendments for contract ID:', selectedOriginalContract.value)
  console.log('🔍 Total amendments available:', amendmentContracts.value.length)
  console.log('🔍 Filtered amendments:', filtered.length)
  console.log('🔍 Amendment contracts data:', amendmentContracts.value.map(c => ({
    id: c.contract_id,
    title: c.contract_title,
    parent_id: c.parent_contract_id,
    kind: c.contract_kind
  })))
  
  return filtered
})

// Load contracts on mount
onMounted(async () => {
  await loggingService.logPageView('Contract', 'Contract Comparison')
  await loadContracts()
  
  // Check if we have contract IDs from route params (when navigating from amendment creation)
  const originalId = route.query.originalId
  const amendmentId = route.query.amendmentId
  
  if (originalId && amendmentId) {
    console.log('🔍 Loading comparison from URL params:', { originalId, amendmentId })
    
    // First, set the original contract - this is needed for the filteredAmendmentContracts computed property
    selectedOriginalContract.value = parseInt(originalId)
    
    // Ensure the amendment contract is in our list (it might be newly created)
    const amendmentExists = amendmentContracts.value.some(c => c.contract_id === parseInt(amendmentId))
    
    if (!amendmentExists) {
      console.log('🔄 Amendment not in list, fetching it directly...')
      try {
        const response = await contractsApi.getContract(parseInt(amendmentId))
        if (response.success !== false) {
          const amendmentContract = response.success ? response.data : response
          
          console.log('📋 Fetched amendment contract:', amendmentContract)
          
          // Add to contracts list
          contracts.value.push(amendmentContract)
          
          // Add to amendment contracts list if it's an amendment
          if (amendmentContract.contract_kind === 'AMENDMENT' && amendmentContract.parent_contract_id === parseInt(originalId)) {
            amendmentContracts.value.push(amendmentContract)
            console.log('✅ Amendment contract added to list:', amendmentContract.contract_title)
          }
        }
      } catch (error) {
        console.error('❌ Error fetching amendment contract:', error)
      }
    }
    
    // Wait for Vue to update the DOM and computed properties
    await nextTick()
    
    // Now set the amendment contract selection
    selectedAmendmentContract.value = parseInt(amendmentId)
    console.log('✅ Amendment contract selected:', selectedAmendmentContract.value)
    console.log('📊 Filtered amendment contracts:', filteredAmendmentContracts.value.map(c => ({ id: c.contract_id, title: c.contract_title })))
    
    // Load contract details for both
    await Promise.all([
      updateContractDetails(parseInt(originalId), true),
      updateContractDetails(parseInt(amendmentId), false)
    ])
    
    // Wait for another tick before comparing
    await nextTick()
    
    // Trigger comparison
    await compareContracts()
  }
})

// Load contracts from API
const loadContracts = async () => {
  try {
    loading.value = true
    console.log('🔄 Loading contracts...')
    const response = await contractsApi.getContracts()
    console.log('📋 API Response:', response)
    
    // Handle the API response structure
    let contractsData = []
    
    if (response && response.success === true && response.data) {
      contractsData = response.data
      console.log('📊 Contracts data from API:', contractsData)
      
      // Ensure we have an array
      if (Array.isArray(contractsData)) {
        contracts.value = contractsData
        
        // Filter amendment contracts (contracts with parent_contract_id)
        amendmentContracts.value = contractsData.filter(contract => 
          contract.parent_contract_id && contract.contract_kind === 'AMENDMENT'
        )
        
        console.log('✅ Loaded contracts:', contracts.value.length)
        console.log('✅ Loaded amendment contracts:', amendmentContracts.value.length)
        
        // Show success message if we have contracts
        if (contracts.value.length > 0) {
          console.log('📋 Available contracts:', contracts.value.map(c => ({ 
            id: c.contract_id, 
            title: c.contract_title, 
            number: c.contract_number,
            kind: c.contract_kind,
            parent_id: c.parent_contract_id 
          })))
        }
      } else {
        console.warn('⚠️ Contracts data is not an array:', contractsData)
        contracts.value = []
        amendmentContracts.value = []
      }
    } else {
      console.error('❌ API returned error or unexpected format:', response)
      errorMessage.value = response?.message || 'Failed to load contracts - unexpected response format'
    }
  } catch (error) {
    console.error('❌ Error loading contracts:', error)
    errorMessage.value = 'Failed to load contracts: ' + error.message
  } finally {
    loading.value = false
  }
}

// Get contract details when selection changes
const updateContractDetails = async (contractId, isOriginal) => {
  if (!contractId) return
  
  try {
    const response = await contractsApi.getContract(contractId)
    if (response.success !== false) {
      const contractData = response.success ? response.data : response
      if (isOriginal) {
        originalContractDetails.value = contractData
      } else {
        amendmentContractDetails.value = contractData
      }
    }
  } catch (error) {
    console.error('Error loading contract details:', error)
  }
}

// Watch for contract selection changes
watch(() => selectedOriginalContract.value, (newId, oldId) => {
  updateContractDetails(newId, true)
  
  // Clear amendment selection when original contract changes
  if (newId !== oldId) {
    selectedAmendmentContract.value = null
    amendmentContractDetails.value = null
  }
})

watch(() => selectedAmendmentContract.value, (newId) => {
  updateContractDetails(newId, false)
})

// Compare contracts
const compareContracts = async () => {
  if (!selectedOriginalContract.value || !selectedAmendmentContract.value) {
    errorMessage.value = 'Please select both original and amendment contracts'
    return
  }

  try {
    loading.value = true
    errorMessage.value = ''
    
    const response = await contractsApi.compareContracts(
      selectedOriginalContract.value, 
      selectedAmendmentContract.value
    )
    
    if (response.success !== false) {
      comparisonData.value = response.success ? response.data : response
    } else {
      throw new Error(response.message || 'Failed to compare contracts')
    }
  } catch (error) {
    console.error('Error comparing contracts:', error)
    errorMessage.value = error.message || 'Failed to compare contracts'
  } finally {
    loading.value = false
  }
}

// Format field names for display
const formatFieldName = (field) => {
  const fieldMap = {
    'contract_title': 'Contract Title',
    'contract_number': 'Contract Number',
    'contract_type': 'Contract Type',
    'contract_value': 'Contract Value',
    'currency': 'Currency',
    'start_date': 'Start Date',
    'end_date': 'End Date',
    'priority': 'Priority',
    'status': 'Status',
    'contract_category': 'Category',
    'notice_period_days': 'Notice Period (Days)',
    'auto_renewal': 'Auto Renewal',
    'dispute_resolution_method': 'Dispute Resolution',
    'governing_law': 'Governing Law',
    'contract_risk_score': 'Risk Score',
    'compliance_framework': 'Compliance Framework'
  }
  return fieldMap[field] || field.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

// Format values for display
const formatValue = (value) => {
  if (value === null || value === undefined) return 'N/A'
  if (typeof value === 'boolean') return value ? 'Yes' : 'No'
  if (typeof value === 'object') return JSON.stringify(value)
  return value.toString()
}

// Helper function to add header with logo and company info
const addHeader = (doc, pageNumber = 1) => {
  const pageWidth = doc.internal.pageSize.width
  const margin = 20
  
  // Header background
  doc.setFillColor(41, 128, 185) // Professional blue
  doc.rect(0, 0, pageWidth, 35, 'F')
  
  // Company/System name
  doc.setTextColor(255, 255, 255)
  doc.setFontSize(16)
  doc.setFont(undefined, 'bold')
  doc.text('Vendor Guard Hub', margin, 15)
  
  // Report title
  doc.setFontSize(12)
  doc.setFont(undefined, 'normal')
  doc.text('Contract Comparison Report', margin, 25)
  
  // Date and page number
  doc.setFontSize(10)
  doc.text(`Generated: ${new Date().toLocaleDateString('en-US', { 
    year: 'numeric', 
    month: 'long', 
    day: 'numeric' 
  })}`, pageWidth - margin - 60, 15)
  
  if (pageNumber > 1) {
    doc.text(`Page ${pageNumber}`, pageWidth - margin - 20, 25)
  }
  
  // Reset text color
  doc.setTextColor(0, 0, 0)
}

// Helper function to add section header with background
const addSectionHeader = (doc, title, yPosition, margin) => {
  // Simple section title without background
  doc.setFontSize(14)
  doc.setFont(undefined, 'bold')
  doc.setTextColor(52, 73, 94) // Dark gray
  doc.text(title, margin, yPosition)
  
  // Reset colors
  doc.setTextColor(0, 0, 0)
  doc.setFont(undefined, 'normal')
  
  return yPosition + 15
}

// Helper function to add info box
const addInfoBox = (doc, title, details, yPosition, margin) => {
  const pageWidth = doc.internal.pageSize.width
  const boxWidth = pageWidth - (2 * margin)
  
  // Box border
  doc.setDrawColor(189, 195, 199)
  doc.setLineWidth(0.5)
  doc.rect(margin, yPosition, boxWidth, 25)
  
  // Title background
  doc.setFillColor(52, 73, 94)
  doc.rect(margin, yPosition, boxWidth, 8, 'F')
  
  // Title text
  doc.setTextColor(255, 255, 255)
  doc.setFontSize(10)
  doc.setFont(undefined, 'bold')
  doc.text(title, margin + 3, yPosition + 5.5)
  
  // Details
  doc.setTextColor(0, 0, 0)
  doc.setFont(undefined, 'normal')
  doc.setFontSize(9)
  
  let detailY = yPosition + 12
  details.forEach(detail => {
    doc.text(detail, margin + 3, detailY)
    detailY += 4
  })
  
  return yPosition + 30
}

// Helper function to add summary in simple table format
const addSummaryTable = (doc, summary, yPosition, margin) => {
  const pageWidth = doc.internal.pageSize.width
  const tableWidth = pageWidth - (2 * margin)
  const rowHeight = 12
  const lineHeight = 8
  
  // Table header
  doc.setFillColor(52, 73, 94)
  doc.rect(margin, yPosition, tableWidth, rowHeight, 'F')
  
  doc.setTextColor(255, 255, 255)
  doc.setFontSize(11)
  doc.setFont(undefined, 'bold')
  doc.text('Metric', margin + 5, yPosition + 8)
  doc.text('Count', margin + tableWidth - 30, yPosition + 8)
  
  // Reset colors
  doc.setTextColor(0, 0, 0)
  doc.setFont(undefined, 'normal')
  doc.setFontSize(10)
  
  yPosition += rowHeight
  
  // Summary data
  const summaryData = [
    { label: 'Contract Fields Changed', value: summary.contract_fields_changed },
    { label: 'Terms Added', value: summary.terms_added },
    { label: 'Terms Modified', value: summary.terms_modified },
    { label: 'Terms Removed', value: summary.terms_removed },
    { label: 'Clauses Added', value: summary.clauses_added },
    { label: 'Clauses Modified', value: summary.clauses_modified },
    { label: 'Clauses Removed', value: summary.clauses_removed }
  ]
  
  summaryData.forEach((item, index) => {
    // Alternate row background
    if (index % 2 === 0) {
      doc.setFillColor(248, 249, 250)
      doc.rect(margin, yPosition, tableWidth, rowHeight, 'F')
    }
    
    // Row border
    doc.setDrawColor(189, 195, 199)
    doc.setLineWidth(0.3)
    doc.line(margin, yPosition, margin + tableWidth, yPosition)
    
    // Label
    doc.setTextColor(0, 0, 0)
    doc.setFontSize(10)
    doc.setFont(undefined, 'normal')
    doc.text(item.label, margin + 5, yPosition + 8)
    
    // Value
    doc.setFont(undefined, 'bold')
    doc.text(item.value.toString(), margin + tableWidth - 30, yPosition + 8)
    
    yPosition += rowHeight
  })
  
  // Bottom border
  doc.setDrawColor(189, 195, 199)
  doc.setLineWidth(0.5)
  doc.line(margin, yPosition, margin + tableWidth, yPosition)
  
  return yPosition + 15
}

// Helper function to add change item with proper formatting
const addChangeItem = (doc, title, original, amended, yPosition, margin) => {
  // Check if we need a new page
  if (yPosition > 250) {
    doc.addPage()
    addHeader(doc, doc.internal.getCurrentPageInfo().pageNumber)
    yPosition = 45
  }
  
  // Item background
  doc.setFillColor(248, 249, 250)
  doc.rect(margin, yPosition, doc.internal.pageSize.width - (2 * margin), 25, 'F')
  
  // Item border
  doc.setDrawColor(189, 195, 199)
  doc.setLineWidth(0.3)
  doc.rect(margin, yPosition, doc.internal.pageSize.width - (2 * margin), 25)
  
  // Title
  doc.setTextColor(52, 73, 94)
  doc.setFontSize(10)
  doc.setFont(undefined, 'bold')
  doc.text(title, margin + 5, yPosition + 8)
  
  // Original value
  doc.setTextColor(231, 76, 60) // Red for original
  doc.setFontSize(8)
  doc.setFont(undefined, 'normal')
  doc.text(`Original: ${original}`, margin + 5, yPosition + 15)
  
  // Amendment value
  doc.setTextColor(46, 204, 113) // Green for amendment
  doc.text(`Amendment: ${amended}`, margin + 5, yPosition + 22)
  
  // Reset colors
  doc.setTextColor(0, 0, 0)
  
  return yPosition + 30
}

// Download comparison report as PDF
const downloadComparisonReport = () => {
  if (!comparisonData.value) return
  
  try {
    // Import jsPDF dynamically
    import('jspdf').then(({ default: jsPDF }) => {
      const doc = new jsPDF()
      
      // Set up PDF content
      let yPosition = 45 // Start after header
      const pageWidth = doc.internal.pageSize.width
      const margin = 20
      
      // Add header
      addHeader(doc, 1)
      
      // Title Section
      doc.setFontSize(18)
      doc.setFont(undefined, 'bold')
      doc.setTextColor(52, 73, 94)
      doc.text('Contract Comparison Analysis', margin, yPosition)
      yPosition += 20
      
      // Contract Information Section
      yPosition = addSectionHeader(doc, 'Contract Information', yPosition, margin)
      
      // Original Contract Info Box
      if (originalContractDetails.value) {
        const originalDetails = [
          `Contract Number: ${originalContractDetails.value.contract_number || 'N/A'}`,
          `Version: ${originalContractDetails.value.version_number || 'N/A'}`,
          `Status: ${originalContractDetails.value.status || 'N/A'}`
        ]
        yPosition = addInfoBox(doc, 'Original Contract', [
          originalContractDetails.value.contract_title || 'N/A',
          ...originalDetails
        ], yPosition, margin)
      }
      
      yPosition += 5
      
      // Amendment Contract Info Box
      if (amendmentContractDetails.value) {
        const amendmentDetails = [
          `Contract Number: ${amendmentContractDetails.value.contract_number || 'N/A'}`,
          `Version: ${amendmentContractDetails.value.version_number || 'N/A'}`,
          `Status: ${amendmentContractDetails.value.status || 'N/A'}`
        ]
        yPosition = addInfoBox(doc, 'Amendment Contract', [
          amendmentContractDetails.value.contract_title || 'N/A',
          ...amendmentDetails
        ], yPosition, margin)
      }
      
      yPosition += 15
      
      // Summary Section
      if (comparisonData.value.summary) {
        yPosition = addSectionHeader(doc, 'Comparison Summary', yPosition, margin)
        yPosition = addSummaryTable(doc, comparisonData.value.summary, yPosition, margin)
      }
      
      // Contract Changes Section - Force new page
      if (comparisonData.value.contract_changes && comparisonData.value.contract_changes.length > 0) {
        doc.addPage()
        addHeader(doc, doc.internal.getCurrentPageInfo().pageNumber)
        yPosition = 45
        
        yPosition = addSectionHeader(doc, 'Contract Field Changes', yPosition, margin)
        
        comparisonData.value.contract_changes.forEach(change => {
          yPosition = addChangeItem(
            doc,
            formatFieldName(change.field),
            formatValue(change.original),
            formatValue(change.amendment),
            yPosition,
            margin
          )
        })
      }
      
      // Terms Changes Section
      if (comparisonData.value.terms_changes) {
        const termsChanges = comparisonData.value.terms_changes
        
        // Terms Added
        if (termsChanges.added && termsChanges.added.length > 0) {
          yPosition = addSectionHeader(doc, `Terms Added (${termsChanges.added.length})`, yPosition, margin)
          
          termsChanges.added.forEach(term => {
            if (yPosition > 250) {
              doc.addPage()
              addHeader(doc, doc.internal.getCurrentPageInfo().pageNumber)
              yPosition = 45
            }
            
            // Green background for added items
            doc.setFillColor(236, 250, 241)
            doc.rect(margin, yPosition, pageWidth - (2 * margin), 20, 'F')
            
            doc.setDrawColor(46, 204, 113)
            doc.setLineWidth(0.5)
            doc.rect(margin, yPosition, pageWidth - (2 * margin), 20)
            
            doc.setTextColor(52, 73, 94)
            doc.setFontSize(10)
            doc.setFont(undefined, 'bold')
            doc.text(`+ ${term.term_title || 'Untitled Term'}`, margin + 5, yPosition + 8)
            
            doc.setTextColor(0, 0, 0)
            doc.setFontSize(8)
            doc.setFont(undefined, 'normal')
            const text = term.term_text.substring(0, 100) + (term.term_text.length > 100 ? '...' : '')
            doc.text(text, margin + 5, yPosition + 15)
            
            yPosition += 25
          })
        }
        
        // Terms Modified
        if (termsChanges.modified && termsChanges.modified.length > 0) {
          yPosition = addSectionHeader(doc, `Terms Modified (${termsChanges.modified.length})`, yPosition, margin)
          
          termsChanges.modified.forEach(change => {
            if (yPosition > 220) {
              doc.addPage()
              addHeader(doc, doc.internal.getCurrentPageInfo().pageNumber)
              yPosition = 45
            }
            
            // Orange background for modified items
            doc.setFillColor(254, 249, 231)
            doc.rect(margin, yPosition, pageWidth - (2 * margin), 30, 'F')
            
            doc.setDrawColor(241, 196, 15)
            doc.setLineWidth(0.5)
            doc.rect(margin, yPosition, pageWidth - (2 * margin), 30)
            
            doc.setTextColor(52, 73, 94)
            doc.setFontSize(10)
            doc.setFont(undefined, 'bold')
            doc.text(`~ ${change.original.term_title || 'Untitled Term'}`, margin + 5, yPosition + 8)
            
            doc.setTextColor(231, 76, 60)
            doc.setFontSize(8)
            doc.setFont(undefined, 'normal')
            doc.text(`Original: ${change.original.term_text.substring(0, 60)}...`, margin + 5, yPosition + 15)
            
            doc.setTextColor(46, 204, 113)
            doc.text(`Modified: ${change.amendment.term_text.substring(0, 60)}...`, margin + 5, yPosition + 22)
            
            yPosition += 35
          })
        }
        
        // Terms Removed
        if (termsChanges.removed && termsChanges.removed.length > 0) {
          yPosition = addSectionHeader(doc, `Terms Removed (${termsChanges.removed.length})`, yPosition, margin)
          
          termsChanges.removed.forEach(term => {
            if (yPosition > 250) {
              doc.addPage()
              addHeader(doc, doc.internal.getCurrentPageInfo().pageNumber)
              yPosition = 45
            }
            
            // Red background for removed items
            doc.setFillColor(254, 235, 238)
            doc.rect(margin, yPosition, pageWidth - (2 * margin), 20, 'F')
            
            doc.setDrawColor(231, 76, 60)
            doc.setLineWidth(0.5)
            doc.rect(margin, yPosition, pageWidth - (2 * margin), 20)
            
            doc.setTextColor(52, 73, 94)
            doc.setFontSize(10)
            doc.setFont(undefined, 'bold')
            doc.text(`- ${term.term_title || 'Untitled Term'}`, margin + 5, yPosition + 8)
            
            doc.setTextColor(0, 0, 0)
            doc.setFontSize(8)
            doc.setFont(undefined, 'normal')
            const text = term.term_text.substring(0, 100) + (term.term_text.length > 100 ? '...' : '')
            doc.text(text, margin + 5, yPosition + 15)
            
            yPosition += 25
          })
        }
      }
      
      // Clauses Changes Section
      if (comparisonData.value.clauses_changes) {
        const clausesChanges = comparisonData.value.clauses_changes
        
        // Clauses Added
        if (clausesChanges.added && clausesChanges.added.length > 0) {
          yPosition = addSectionHeader(doc, `Clauses Added (${clausesChanges.added.length})`, yPosition, margin)
          
          clausesChanges.added.forEach(clause => {
            if (yPosition > 250) {
              doc.addPage()
              addHeader(doc, doc.internal.getCurrentPageInfo().pageNumber)
              yPosition = 45
            }
            
            // Green background for added items
            doc.setFillColor(236, 250, 241)
            doc.rect(margin, yPosition, pageWidth - (2 * margin), 20, 'F')
            
            doc.setDrawColor(46, 204, 113)
            doc.setLineWidth(0.5)
            doc.rect(margin, yPosition, pageWidth - (2 * margin), 20)
            
            doc.setTextColor(52, 73, 94)
            doc.setFontSize(10)
            doc.setFont(undefined, 'bold')
            doc.text(`+ ${clause.clause_name || 'Untitled Clause'}`, margin + 5, yPosition + 8)
            
            doc.setTextColor(0, 0, 0)
            doc.setFontSize(8)
            doc.setFont(undefined, 'normal')
            const text = clause.clause_text.substring(0, 100) + (clause.clause_text.length > 100 ? '...' : '')
            doc.text(text, margin + 5, yPosition + 15)
            
            yPosition += 25
          })
        }
        
        // Clauses Modified
        if (clausesChanges.modified && clausesChanges.modified.length > 0) {
          yPosition = addSectionHeader(doc, `Clauses Modified (${clausesChanges.modified.length})`, yPosition, margin)
          
          clausesChanges.modified.forEach(change => {
            if (yPosition > 220) {
              doc.addPage()
              addHeader(doc, doc.internal.getCurrentPageInfo().pageNumber)
              yPosition = 45
            }
            
            // Orange background for modified items
            doc.setFillColor(254, 249, 231)
            doc.rect(margin, yPosition, pageWidth - (2 * margin), 30, 'F')
            
            doc.setDrawColor(241, 196, 15)
            doc.setLineWidth(0.5)
            doc.rect(margin, yPosition, pageWidth - (2 * margin), 30)
            
            doc.setTextColor(52, 73, 94)
            doc.setFontSize(10)
            doc.setFont(undefined, 'bold')
            doc.text(`~ ${change.original.clause_name || 'Untitled Clause'}`, margin + 5, yPosition + 8)
            
            doc.setTextColor(231, 76, 60)
            doc.setFontSize(8)
            doc.setFont(undefined, 'normal')
            doc.text(`Original: ${change.original.clause_text.substring(0, 60)}...`, margin + 5, yPosition + 15)
            
            doc.setTextColor(46, 204, 113)
            doc.text(`Modified: ${change.amendment.clause_text.substring(0, 60)}...`, margin + 5, yPosition + 22)
            
            yPosition += 35
          })
        }
        
        // Clauses Removed
        if (clausesChanges.removed && clausesChanges.removed.length > 0) {
          yPosition = addSectionHeader(doc, `Clauses Removed (${clausesChanges.removed.length})`, yPosition, margin)
          
          clausesChanges.removed.forEach(clause => {
            if (yPosition > 250) {
              doc.addPage()
              addHeader(doc, doc.internal.getCurrentPageInfo().pageNumber)
              yPosition = 45
            }
            
            // Red background for removed items
            doc.setFillColor(254, 235, 238)
            doc.rect(margin, yPosition, pageWidth - (2 * margin), 20, 'F')
            
            doc.setDrawColor(231, 76, 60)
            doc.setLineWidth(0.5)
            doc.rect(margin, yPosition, pageWidth - (2 * margin), 20)
            
            doc.setTextColor(52, 73, 94)
            doc.setFontSize(10)
            doc.setFont(undefined, 'bold')
            doc.text(`- ${clause.clause_name || 'Untitled Clause'}`, margin + 5, yPosition + 8)
            
            doc.setTextColor(0, 0, 0)
            doc.setFontSize(8)
            doc.setFont(undefined, 'normal')
            const text = clause.clause_text.substring(0, 100) + (clause.clause_text.length > 100 ? '...' : '')
            doc.text(text, margin + 5, yPosition + 15)
            
            yPosition += 25
          })
        }
      }
      
      // Footer on last page
      const pageCount = doc.internal.getNumberOfPages()
      for (let i = 1; i <= pageCount; i++) {
        doc.setPage(i)
        
        // Footer line
        doc.setDrawColor(189, 195, 199)
        doc.setLineWidth(0.5)
        doc.line(margin, doc.internal.pageSize.height - 20, pageWidth - margin, doc.internal.pageSize.height - 20)
        
        // Footer text
        doc.setTextColor(127, 140, 141)
        doc.setFontSize(8)
        doc.setFont(undefined, 'normal')
        doc.text('Confidential Document - Vendor Guard Hub', margin, doc.internal.pageSize.height - 10)
        doc.text(`Page ${i} of ${pageCount}`, pageWidth - margin - 20, doc.internal.pageSize.height - 10)
      }
      
      // Save the PDF
      const fileName = `Contract-Comparison-${selectedOriginalContract.value}-${selectedAmendmentContract.value}-${new Date().toISOString().split('T')[0]}.pdf`
      doc.save(fileName)
      
      console.log('✅ Professional PDF comparison report downloaded successfully')
    }).catch(error => {
      console.error('❌ Error loading jsPDF:', error)
      errorMessage.value = 'Error generating PDF: jsPDF library not available'
    })
    
  } catch (error) {
    console.error('❌ Error downloading comparison report:', error)
    errorMessage.value = 'Error downloading comparison report: ' + error.message
  }
}

// Reset comparison
const resetComparison = () => {
  selectedOriginalContract.value = null
  selectedAmendmentContract.value = null
  originalContractDetails.value = null
  amendmentContractDetails.value = null
  comparisonData.value = null
  errorMessage.value = ''
}
</script>
