<template>
  <div class="space-y-4 lg:space-y-6 p-4 lg:p-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="text-2xl lg:text-3xl font-bold tracking-tight text-foreground">My Audits</h1>
        <p class="text-sm lg:text-base text-muted-foreground">Manage audits assigned to you as auditor or reviewer</p>
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
            placeholder="Search audits by title or SLA..."
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
          <AuditCard 
            v-for="audit in currentAudits" 
            :key="audit.audit_id" 
            :audit="audit"
            :currentUserId="currentUserId"
            @click="navigateToAudit(audit.audit_id)"
          />
        </div>
        
        <!-- List View -->
        <div v-else-if="viewMode === 'list'" class="space-y-2">
          <!-- List Header -->
          <div class="grid grid-cols-12 gap-4 px-4 py-3 bg-muted/50 rounded-lg text-sm font-medium text-muted-foreground">
            <div class="col-span-3">Audit Details</div>
            <div class="col-span-2">SLA</div>
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
              <div class="text-xs text-muted-foreground flex items-center gap-1 mt-1">
                <Paperclip class="w-3 h-3" />
                Evidence docs: {{ getEvidenceDocCount(audit.audit_id) }}
                <span v-if="getEvidenceUpdatedLabel(audit.audit_id)" class="text-[11px] text-muted-foreground/80">
                  • Updated {{ getEvidenceUpdatedLabel(audit.audit_id) }}
                </span>
              </div>
            </div>
            
            <!-- SLA -->
            <div class="col-span-2">
              <div class="text-sm text-foreground">{{ audit.sla_name || 'N/A' }}</div>
              <div v-if="audit.metrics_count > 0" class="text-xs text-muted-foreground">
                {{ audit.metrics_count }} metrics: {{ audit.metrics_names }}
              </div>
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
                <template v-if="audit.status === 'created'">
                  <Button
                    @click="startAudit(audit.audit_id)"
                    variant="default"
                    size="sm"
                    class="flex items-center gap-1 bg-gradient-to-r from-primary to-primary-glow hover:shadow-hover"
                  >
                    <Activity class="h-3 w-3" />
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
                    Continue
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
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'
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
  Activity,
  Paperclip
} from 'lucide-vue-next'
import apiService from '@/services/api.js'
import Card from '@/components/ui/card.vue'
import CardContent from '@/components/ui/card-content.vue'
import Button from '@/components/ui/button.vue'
import Input from '@/components/ui/input.vue'
import Badge from '@/components/ui/badge.vue'
import AuditCard from '@/components/AuditCard.vue'
import PopupModal from '@/popup/PopupModal.vue'
import { PopupService } from '@/popup/popupService'
import { useNotifications } from '@/composables/useNotifications'
import loggingService from '@/services/loggingService'

const router = useRouter()
const store = useStore()
const { showSuccess, showError, showWarning, showInfo } = useNotifications()

// Get current user from store
const currentUser = computed(() => store.state.auth.currentUser)

// Get current user ID
const currentUserId = computed(() => {
  if (!currentUser.value) return null
  return currentUser.value.id || currentUser.value.user_id || currentUser.value.userid
})

const searchTerm = ref('')
const activeTab = ref('all')
const loading = ref(true)
const allAudits = ref([])
const viewMode = ref('grid') // 'grid' or 'list'
const evidenceStorageKey = 'auditEvidenceDocuments'
const auditEvidenceMap = ref({})
let storageListener = null
let evidenceBroadcastListener = null

const loadEvidenceFromStorage = () => {
  if (typeof window === 'undefined') return
  try {
    const stored = JSON.parse(localStorage.getItem(evidenceStorageKey)) || {}
    auditEvidenceMap.value = stored
  } catch (error) {
    console.error('Failed to parse evidence storage payload:', error)
    auditEvidenceMap.value = {}
  }
}

const attachEvidenceMetadata = (audits = []) => {
  if (!Array.isArray(audits)) return []
  return audits.map(audit => {
    const evidenceInfo = auditEvidenceMap.value?.[audit.audit_id] || {}
    return {
      ...audit,
      evidence_docs_count: evidenceInfo.count || 0,
      evidence_docs_last_updated: evidenceInfo.updatedAt || null
    }
  })
}

const getEvidenceDocCount = (auditId) => auditEvidenceMap.value?.[auditId]?.count || 0

const getEvidenceUpdatedLabel = (auditId) => {
  const updatedAt = auditEvidenceMap.value?.[auditId]?.updatedAt
  if (!updatedAt) return null
  return new Date(updatedAt).toLocaleDateString()
}

// Load audits from API
const loadAudits = async () => {
  try {
    loading.value = true
    // Pass show_all=true to get all audits for the tenant (not just assigned ones)
    const auditsData = await apiService.getAudits({ show_all: true })
    let audits = auditsData.results || auditsData || []
    
    // Load SLA data to populate SLA names
    let slasData = []
    try {
      slasData = await apiService.getAvailableSLAs()
      console.log('Loaded SLAs:', slasData)
    } catch (slaError) {
      console.error('Error loading SLAs:', slaError)
      // Continue without SLA data - will show "Unknown SLA" for all audits
    }
    
    // Create a map of SLA ID to SLA name for quick lookup
    const slaMap = {}
    if (Array.isArray(slasData)) {
      slasData.forEach(sla => {
        if (sla.sla_id && sla.sla_name) {
          slaMap[sla.sla_id] = sla.sla_name
        }
      })
    } else if (slasData && slasData.results && Array.isArray(slasData.results)) {
      slasData.results.forEach(sla => {
        if (sla.sla_id && sla.sla_name) {
          slaMap[sla.sla_id] = sla.sla_name
        }
      })
    }
    
    // Populate SLA names and metrics in audits
    audits = await Promise.all(audits.map(async (audit) => {
      const auditWithSLA = {
        ...audit,
        sla_name: audit.sla_id ? (slaMap[audit.sla_id] || 'Unknown SLA') : 'No SLA Assigned'
      }
      
      // Fetch metrics for this audit's SLA
      const slaExists = audit.sla_id && slaMap[audit.sla_id]
      if (slaExists) {
        try {
          const metricsData = await apiService.getSLAMetrics(audit.sla_id)
          console.log(`Metrics for SLA ${audit.sla_id}:`, metricsData)
          
          // Handle different response formats
          let metrics = []
          if (Array.isArray(metricsData)) {
            metrics = metricsData
          } else if (metricsData && metricsData.metrics && Array.isArray(metricsData.metrics)) {
            metrics = metricsData.metrics
          } else if (metricsData && metricsData.results && Array.isArray(metricsData.results)) {
            metrics = metricsData.results
          }
          
          auditWithSLA.metrics = metrics
          auditWithSLA.metrics_count = metrics.length
          auditWithSLA.metrics_names = metrics.map(m => m.metric_name).join(', ')
        } catch (error) {
          console.error(`Error loading metrics for SLA ${audit.sla_id}:`, error)
          auditWithSLA.metrics = []
          auditWithSLA.metrics_count = 0
          auditWithSLA.metrics_names = 'Metrics unavailable'
        }
      } else {
        auditWithSLA.metrics = []
        auditWithSLA.metrics_count = 0
        auditWithSLA.metrics_names = audit.sla_id ? 'SLA not accessible' : 'No SLA assigned'
      }
      
      return auditWithSLA
    }))
    
    console.log('Audits with SLA names and metrics:', audits)
    allAudits.value = attachEvidenceMetadata(audits)
    
  } catch (error) {
    console.error('Error loading audits:', error)
    
    // Show error notification
    await showError('Audits Loading Failed', 'Failed to load audits. Please try refreshing the page.', {
      action: 'audits_loading_failed',
      error_message: error.message
    })
    
    allAudits.value = []
  } finally {
    loading.value = false
  }
}

// Filter audits - backend already filters by tenant and user assignment
// Frontend just returns all audits from backend (they're already filtered appropriately)
const myAudits = computed(() => {
  // Backend already handles filtering by tenant and user assignment
  // So we just return all audits returned by the backend
  return allAudits.value
})

// Filter by search term
const filteredAudits = computed(() => myAudits.value.filter(audit =>
  audit.title.toLowerCase().includes(searchTerm.value.toLowerCase()) ||
  (audit.sla_name && audit.sla_name.toLowerCase().includes(searchTerm.value.toLowerCase()))
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

watch(auditEvidenceMap, () => {
  allAudits.value = attachEvidenceMetadata(allAudits.value)
})

// Load data on component mount
onMounted(async () => {
  loadEvidenceFromStorage()
  if (typeof window !== 'undefined') {
    storageListener = (event) => {
      if (event.key === evidenceStorageKey) {
        loadEvidenceFromStorage()
      }
    }
    evidenceBroadcastListener = () => loadEvidenceFromStorage()
    window.addEventListener('storage', storageListener)
    window.addEventListener('audit-evidence-updated', evidenceBroadcastListener)
  }
  await loggingService.logPageView('Audit', 'My Audits')
  await loadAudits()
})

onBeforeUnmount(() => {
  if (typeof window === 'undefined') return
  if (storageListener) {
    window.removeEventListener('storage', storageListener)
    storageListener = null
  }
  if (evidenceBroadcastListener) {
    window.removeEventListener('audit-evidence-updated', evidenceBroadcastListener)
    evidenceBroadcastListener = null
  }
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
const navigateToCreate = () => router.push('/audit/create')
const navigateToAudit = (auditId) => router.push(`/audit/${auditId}`)

// Action functions
const startAudit = async (auditId) => {
  try {
    // Update audit status to in_progress
    await apiService.updateAudit(auditId, { status: 'in_progress' })
    
    // Show success notification
    await showSuccess('Audit Started', 'Audit has been started successfully. You can now begin the audit process.', {
      audit_id: auditId,
      action: 'audit_started'
    })
    
    router.push(`/audit/${auditId}`)
  } catch (error) {
    console.error('Error starting audit:', error)
    
    // Show error notification
    await showError('Start Failed', 'Error starting audit. Please try again.', {
      audit_id: auditId,
      action: 'audit_start_failed',
      error_message: error.message
    })
    
    PopupService.error('Error starting audit. Please try again.', 'Start Failed')
  }
}

const editAudit = (auditId) => {
  router.push(`/audit/${auditId}`)
}

const reviewAudit = (auditId) => {
  router.push(`/audit/${auditId}/review`)
}

const generateReport = async (audit) => {
  try {
    // Show info notification
    await showInfo('Report Generation', `Generating report for audit: ${audit.title}`, {
      audit_id: audit.audit_id,
      audit_title: audit.title,
      action: 'report_generation_initiated'
    })
    
    // This would integrate with the report generation from AuditReports.vue
    PopupService.warning(`Generating report for audit: ${audit.title}`, 'Report Generation')
    // You could import and call the generateAuditReport function here
  } catch (error) {
    console.error('Error generating report:', error)
    
    // Show error notification
    await showError('Report Generation Failed', 'Error generating report. Please try again.', {
      audit_id: audit.audit_id,
      audit_title: audit.title,
      action: 'report_generation_failed',
      error_message: error.message
    })
  }
}
</script>
