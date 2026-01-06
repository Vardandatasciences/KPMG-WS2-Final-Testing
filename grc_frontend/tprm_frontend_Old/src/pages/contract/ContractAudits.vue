<template>
  <div class="space-y-4 lg:space-y-6 p-4 lg:p-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="text-2xl lg:text-3xl font-bold tracking-tight text-foreground">My Audits</h1>
        <p class="text-sm lg:text-base text-muted-foreground">Manage your assigned audits and review queue</p>
      </div>
      <Button 
        @click="navigateToCreate"
        class="bg-gradient-to-r from-primary to-primary-glow hover:shadow-hover transition-all w-full sm:w-auto"
      >
        <FileText class="mr-2 h-4 w-4" />
        Create New Audit
      </Button>
    </div>

    <!-- Search -->
    <Card class="shadow-card">
      <CardContent class="p-4">
        <div class="relative">
          <Search class="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
          <Input
            placeholder="Search audits by title or contract..."
            v-model="searchTerm"
            class="pl-10"
          />
        </div>
      </CardContent>
    </Card>

    <!-- Statistics -->
    <div class="grid grid-cols-2 lg:grid-cols-5 gap-3 lg:gap-4">
      <Card 
        v-for="stat in statistics" 
        :key="stat.label" 
        class="shadow-card"
      >
        <CardContent class="p-3 lg:p-4 text-center">
          <component :is="stat.icon" :class="`w-5 h-5 lg:w-6 lg:h-6 mx-auto mb-2 ${stat.color}`" />
          <div class="text-lg lg:text-2xl font-bold">{{ stat.count }}</div>
          <div class="text-xs text-muted-foreground">{{ stat.label }}</div>
        </CardContent>
      </Card>
    </div>

    <!-- View Toggle - Top Right -->
    <div class="flex justify-end">
      <div class="flex items-center gap-2">
        <span class="text-sm text-muted-foreground">View:</span>
        <div class="flex bg-muted rounded-lg p-1">
          <button
            @click="viewMode = 'grid'"
            :class="[
              'px-3 py-1.5 text-sm font-medium rounded-md transition-colors flex items-center gap-2',
              viewMode === 'grid' 
                ? 'bg-background text-foreground shadow-sm' 
                : 'text-muted-foreground hover:text-foreground'
            ]"
          >
            <Grid3X3 class="h-4 w-4" />
            Grid
          </button>
          <button
            @click="viewMode = 'list'"
            :class="[
              'px-3 py-1.5 text-sm font-medium rounded-md transition-colors flex items-center gap-2',
              viewMode === 'list' 
                ? 'bg-background text-foreground shadow-sm' 
                : 'text-muted-foreground hover:text-foreground'
            ]"
          >
            <List class="h-4 w-4" />
            List
          </button>
        </div>
      </div>
    </div>

    <!-- Audit Tabs -->
    <div class="space-y-4 lg:space-y-6">
      <div class="grid grid-cols-2 lg:grid-cols-6 w-full bg-muted rounded-lg p-1 gap-1">
        <button
          v-for="tab in tabs"
          :key="tab.value"
          :class="[
            'px-2 lg:px-3 py-2 text-xs lg:text-sm font-medium rounded-md transition-colors',
            activeTab === tab.value 
              ? 'bg-background text-foreground shadow-sm' 
              : 'text-muted-foreground hover:text-foreground'
          ]"
          @click="activeTab = tab.value"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- Tab Content -->
      <div class="space-y-4">
        <div v-if="currentAudits.length === 0" class="text-center py-8">
          <FileText class="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
          <h3 class="text-lg font-medium mb-2">No audits found</h3>
          <p class="text-muted-foreground mb-4">
            {{ searchTerm ? "Try adjusting your search criteria" : "No audits found in the system" }}
          </p>
          <Button @click="navigateToCreate">
            Create Your First Audit
          </Button>
        </div>
        
        <!-- Grid View -->
        <div v-else-if="viewMode === 'grid'" class="grid gap-4">
          <ContractAuditCard 
            v-for="audit in currentAudits" 
            :key="audit.audit_id" 
            :audit="audit"
            :currentUserId="currentUser?.userid || currentUser?.user_id"
            @click="navigateToAudit(audit.audit_id)"
          />
        </div>
        
        <!-- List View -->
        <div v-else-if="viewMode === 'list'" class="space-y-2">
          <!-- List Header -->
          <div class="grid grid-cols-12 gap-4 px-4 py-3 bg-muted/50 rounded-lg text-sm font-medium text-muted-foreground">
            <div class="col-span-3">Audit Details</div>
            <div class="col-span-2">Contract</div>
            <div class="col-span-2">Auditor</div>
            <div class="col-span-2">Due Date</div>
            <div class="col-span-1">Status</div>
            <div class="col-span-2">Actions</div>
          </div>
          
          <!-- List Items -->
          <div v-for="audit in currentAudits" :key="audit.audit_id" 
               class="grid grid-cols-12 gap-4 px-4 py-4 border border-border rounded-lg hover:bg-muted/30 transition-colors">
            <!-- Audit Details -->
            <div class="col-span-3">
              <div class="font-medium text-foreground cursor-pointer hover:text-primary" @click="navigateToAudit(audit.audit_id)">
                {{ audit.title }}
              </div>
              <div class="text-sm text-muted-foreground">ID: {{ audit.audit_id }}</div>
            </div>
            
            <!-- Contract -->
            <div class="col-span-2">
              <div class="text-sm text-foreground">{{ audit.contract_title || 'N/A' }}</div>
            </div>
            
            <!-- Auditor -->
            <div class="col-span-2">
              <div class="text-sm text-foreground">{{ audit.auditor_name || 'N/A' }}</div>
            </div>
            
            <!-- Due Date -->
            <div class="col-span-2">
              <div class="text-sm text-foreground">
                {{ audit.due_date ? new Date(audit.due_date).toLocaleDateString() : 'N/A' }}
              </div>
            </div>
            
            <!-- Status -->
            <div class="col-span-1">
              <Badge 
                :variant="getStatusVariant(audit.status)" 
                :class="getStatusClass(audit.status)"
                class="text-xs"
              >
                {{ getStatusLabel(audit.status) }}
              </Badge>
            </div>
            
            <!-- Actions -->
            <div class="col-span-2">
              <div class="flex items-center gap-2">
                <Button
                  @click="navigateToAudit(audit.audit_id)"
                  variant="ghost"
                  size="sm"
                  class="flex items-center gap-1"
                >
                  <Eye class="h-3 w-3" />
                  View
                </Button>
                
                <!-- Status-specific actions -->
                <template v-if="audit.status === 'created' && isCurrentUserAuditor(audit)">
                  <Button
                    @click="startAudit(audit)"
                    variant="default"
                    size="sm"
                    class="flex items-center gap-1 bg-green-600 hover:bg-green-700"
                  >
                    <Play class="h-3 w-3" />
                    Start Audit
                  </Button>
                </template>
                
                <template v-else-if="audit.status === 'completed'">
                  <Button
                    @click="generateReport(audit)"
                    variant="outline"
                    size="sm"
                    class="flex items-center gap-1"
                  >
                    <Download class="h-3 w-3" />
                    Report
                  </Button>
                </template>
                
                <template v-else-if="audit.status === 'in_progress' || audit.status === 'rejected'">
                  <Button
                    @click="editAudit(audit.audit_id)"
                    variant="ghost"
                    size="sm"
                    class="flex items-center gap-1"
                  >
                    <Edit class="h-3 w-3" />
                    Edit
                  </Button>
                </template>
                
                <template v-else-if="audit.status === 'under_review'">
                  <Button
                    @click="reviewAudit(audit.audit_id)"
                    variant="ghost"
                    size="sm"
                    class="flex items-center gap-1"
                  >
                    <Eye class="h-3 w-3" />
                    Review
                  </Button>
                </template>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Popup Modal -->
  <PopupModal />
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'
import PopupModal from '@/popup/PopupModal.vue'
import { PopupService } from '@/popup/popupService'
import { 
  FileText, 
  Search, 
  Clock,
  CheckCircle,
  AlertTriangle,
  Eye,
  Grid3X3,
  List,
  Edit,
  Trash2,
  Download,
  Play
} from 'lucide-vue-next'
import contractAuditApi from '@/services/contractAuditApi.js'
import loggingService from '@/services/loggingService'
import { 
  Card, CardContent, Button, Input, Badge
} from '@/components/ui_contract'
import ContractAuditCard from '@/components/ContractAuditCard.vue'

const router = useRouter()
const store = useStore()
const searchTerm = ref('')
const activeTab = ref('all')
const loading = ref(true)
const allAudits = ref([])
const viewMode = ref('grid') // 'grid' or 'list'

// Get current user from store
const currentUser = computed(() => store.getters['auth/currentUser'])

// Load audits from API
const loadAudits = async () => {
  try {
    loading.value = true
    console.log('🔄 [ContractAudits] Loading audits...')
    const response = await contractAuditApi.getContractAudits()
    console.log('📦 [ContractAudits] API Response:', response)
    
    if (response.success) {
      // Handle different response structures
      let audits = []
      if (Array.isArray(response.data)) {
        audits = response.data
      } else if (response.data?.results && Array.isArray(response.data.results)) {
        audits = response.data.results
      } else if (response.data?.data && Array.isArray(response.data.data)) {
        audits = response.data.data
      } else if (response.data?.audits && Array.isArray(response.data.audits)) {
        audits = response.data.audits
      }
      
      console.log(`✅ [ContractAudits] Loaded ${audits.length} audits`)
      allAudits.value = audits
    } else {
      console.error('❌ [ContractAudits] Error loading contract audits:', response.error || response.message)
      allAudits.value = []
    }
  } catch (error) {
    console.error('❌ [ContractAudits] Exception loading contract audits:', error)
    console.error('❌ [ContractAudits] Error details:', error.response?.data || error.message)
    allAudits.value = []
  } finally {
    loading.value = false
  }
}

// Filter audits to show only those assigned to current user or where user is auditor
// TEMPORARY: Show all audits for debugging - will filter by user once we confirm data is loading
const myAudits = computed(() => {
  // For now, return all audits to debug if data is loading
  // TODO: Re-enable filtering once we confirm data is loading correctly
  if (allAudits.value.length > 0) {
    console.log('📋 [ContractAudits] Showing all audits for debugging:', allAudits.value.length)
    if (currentUser.value) {
      const currentUserId = currentUser.value.userid || currentUser.value.user_id || currentUser.value.UserId || currentUser.value.id
      console.log('👤 [ContractAudits] Current user ID:', currentUserId)
      
      // Log sample audit data
      if (allAudits.value[0]) {
        console.log('📄 [ContractAudits] Sample audit:', {
          audit_id: allAudits.value[0].audit_id,
          title: allAudits.value[0].title,
          assignee_id: allAudits.value[0].assignee_id,
          auditor_id: allAudits.value[0].auditor_id,
          status: allAudits.value[0].status
        })
      }
    }
  }
  
  // Return all audits for now (remove filtering temporarily)
  return allAudits.value
  
  // Original filtering logic (commented out for debugging):
  // if (!currentUser.value) {
  //   console.warn('⚠️ [ContractAudits] No current user found')
  //   return []
  // }
  // 
  // const currentUserId = currentUser.value.userid || currentUser.value.user_id || currentUser.value.UserId || currentUser.value.id
  // return allAudits.value.filter(audit => 
  //   audit.assignee_id == currentUserId || audit.auditor_id == currentUserId
  // )
})

// Filter by search term
const filteredAudits = computed(() => myAudits.value.filter(audit =>
  audit.title.toLowerCase().includes(searchTerm.value.toLowerCase()) ||
  (audit.contract_title && audit.contract_title.toLowerCase().includes(searchTerm.value.toLowerCase()))
))

// Group audits by status
const groupedAudits = computed(() => ({
  created: filteredAudits.value.filter(audit => audit.status === 'created'),
  in_progress: filteredAudits.value.filter(audit => audit.status === 'in_progress'),
  under_review: filteredAudits.value.filter(audit => audit.status === 'under_review'),
  completed: filteredAudits.value.filter(audit => audit.status === 'completed'),
  rejected: filteredAudits.value.filter(audit => audit.status === 'rejected')
}))

const statistics = computed(() => [
  { label: "Created", count: groupedAudits.value.created.length, icon: FileText, color: "text-blue-600" },
  { label: "In Progress", count: groupedAudits.value.in_progress.length, icon: Clock, color: "text-yellow-600" },
  { label: "Under Review", count: groupedAudits.value.under_review.length, icon: Eye, color: "text-purple-600" },
  { label: "Completed", count: groupedAudits.value.completed.length, icon: CheckCircle, color: "text-green-600" },
  { label: "Rejected", count: groupedAudits.value.rejected.length, icon: AlertTriangle, color: "text-red-600" }
])

const tabs = computed(() => [
  { value: 'all', label: `All (${filteredAudits.value.length})` },
  { value: 'created', label: `Created (${groupedAudits.value.created.length})` },
  { value: 'in_progress', label: `In Progress (${groupedAudits.value.in_progress.length})` },
  { value: 'under_review', label: `Review (${groupedAudits.value.under_review.length})` },
  { value: 'completed', label: `Completed (${groupedAudits.value.completed.length})` },
  { value: 'rejected', label: `Rejected (${groupedAudits.value.rejected.length})` }
])

const currentAudits = computed(() => {
  if (activeTab.value === 'all') {
    return filteredAudits.value
  }
  return groupedAudits.value[activeTab.value] || []
})

// Load data on component mount
onMounted(async () => {
  await loggingService.logPageView('Contract', 'Contract Audits')
  await loadAudits()
})

// Helper functions for status display
const getStatusLabel = (status) => {
  const labels = {
    created: 'Created',
    in_progress: 'In Progress',
    under_review: 'Under Review',
    completed: 'Completed',
    rejected: 'Rejected'
  }
  return labels[status] || status
}

const getStatusVariant = (status) => {
  const variants = {
    created: 'secondary',
    in_progress: 'secondary',
    under_review: 'secondary',
    completed: 'default',
    rejected: 'destructive'
  }
  return variants[status] || 'secondary'
}

const getStatusClass = (status) => {
  const classes = {
    created: 'bg-blue-100 text-blue-800',
    in_progress: 'bg-yellow-100 text-yellow-800',
    under_review: 'bg-purple-100 text-purple-800',
    completed: 'bg-green-100 text-green-800',
    rejected: 'bg-red-100 text-red-800'
  }
  return classes[status] || 'bg-gray-100 text-gray-800'
}

// Navigation functions
const navigateToCreate = () => router.push('/contract-audit/create')
const navigateToAudit = (auditId) => router.push(`/contract-audit/${auditId}`)
const navigateToAllAudits = () => router.push('/contract-audit/all')

// Action functions
const editAudit = (auditId) => {
  router.push(`/contract-audit/${auditId}`)
}

const reviewAudit = (auditId) => {
  router.push(`/contract-audit/${auditId}/review`)
}

const generateReport = (audit) => {
  // This would integrate with the report generation from AuditReports.vue
  PopupService.success(`Generating report for audit: ${audit.title}`, 'Report Generation')
  // You could import and call the generateAuditReport function here
}

// Check if current user is the auditor for an audit
const isCurrentUserAuditor = (audit) => {
  if (!currentUser.value || !audit.auditor_id) return false
  const currentUserId = currentUser.value.userid || currentUser.value.user_id
  return currentUserId == audit.auditor_id
}

// Start audit function
const startAudit = async (audit) => {
  PopupService.confirm(
    `Are you sure you want to start the audit "${audit.title}"?`,
    'Start Audit',
    async () => {
      await performStartAudit(audit)
    }
  )
}

const performStartAudit = async (audit) => {
  try {
    loading.value = true
    const response = await contractAuditApi.startContractAudit(audit.audit_id)
    
    if (response.success) {
      PopupService.success(response.message, 'Audit Started')
      // Reload audits to show updated status
      await loadAudits()
    } else {
      PopupService.error(response.error || 'Failed to start audit. Please try again.', 'Start Failed')
    }
  } catch (error) {
    console.error('Error starting audit:', error)
    PopupService.error(error.response?.data?.error || 'Failed to start audit. Please try again.', 'Start Error')
  } finally {
    loading.value = false
  }
}
</script>
