<template>
  <div class="space-y-4 lg:space-y-6 p-4 lg:p-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="text-2xl lg:text-3xl font-bold tracking-tight text-foreground">Audit Reports</h1>
        <p class="text-sm lg:text-base text-muted-foreground">Comprehensive audit analytics and reporting dashboard (Admin View)</p>
      </div>
      <div class="flex flex-col sm:flex-row gap-2">
        <Button variant="outline" @click="exportReport" class="w-full sm:w-auto">
          <Download class="mr-2 h-4 w-4" />
          Export Report
        </Button>
        <Button @click="navigateToCreate" class="bg-gradient-to-r from-primary to-primary-glow hover:shadow-hover transition-all w-full sm:w-auto">
          <Plus class="mr-2 h-4 w-4" />
          Create New Audit
        </Button>
      </div>
    </div>

    <!-- Filter Controls -->
    <Card class="shadow-card">
      <CardContent class="p-4">
        <div class="grid grid-cols-1 lg:grid-cols-4 gap-4">
          <div>
            <Label for="date-range">Date Range</Label>
            <select 
              id="date-range"
              v-model="selectedDateRange" 
              @change="handleDateRangeChange"
              class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <option value="all">All Time</option>
              <option value="30">Last 30 Days</option>
              <option value="90">Last 90 Days</option>
              <option value="year">This Year</option>
            </select>
          </div>
          <div>
            <Label for="status-filter">Status</Label>
            <select 
              id="status-filter"
              v-model="selectedStatus" 
              @change="handleStatusFilter"
              class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <option value="all">All Statuses</option>
              <option value="completed">Completed</option>
              <option value="in_progress">In Progress</option>
              <option value="under_review">Under Review</option>
              <option value="created">Created</option>
            </select>
          </div>
          <div>
            <Label for="sla-filter">SLA</Label>
            <select 
              id="sla-filter"
              v-model="selectedSLA" 
              @change="handleSLAFilter"
              class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <option value="all">All SLAs</option>
              <option v-for="sla in availableSLAs" :key="sla.sla_id" :value="sla.sla_id">
                {{ sla.sla_name }}
              </option>
            </select>
          </div>
          <div>
            <Label for="auditor-filter">Auditor</Label>
            <select 
              id="auditor-filter"
              v-model="selectedAuditor" 
              @change="handleAuditorFilter"
              class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <option value="all">All Auditors</option>
              <option v-for="auditor in auditors" :key="auditor.user_id" :value="auditor.user_id">
                {{ auditor.name }}
              </option>
            </select>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- Key Metrics -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 lg:gap-6">
      <Card v-for="(metric, index) in keyMetrics" :key="index" class="shadow-card">
        <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle class="text-sm font-medium text-muted-foreground">
            {{ metric.title }}
          </CardTitle>
          <component :is="metric.icon" class="h-4 w-4 text-primary" />
        </CardHeader>
        <CardContent class="p-3 lg:p-6">
          <div class="text-lg lg:text-2xl font-bold text-foreground">{{ metric.value }}</div>
          <p class="text-xs text-muted-foreground mt-1 hidden lg:block">{{ metric.description }}</p>
          <div class="flex items-center text-xs text-primary font-medium mt-2">
            <TrendingUp class="h-3 w-3 mr-1" />
            <span class="hidden sm:inline">{{ metric.change }}</span>
          </div>
        </CardContent>
      </Card>
    </div>


    <!-- Completed Audits - Report Generation -->
    <Card class="shadow-card">
      <CardHeader>
        <div class="flex items-center justify-between">
          <div class="flex items-center">
            <FileText class="mr-2 h-5 w-5 text-primary" />
            <div>
              <CardTitle>Completed Audits - Generate Reports</CardTitle>
              <CardDescription>Download detailed PDF reports for completed audits</CardDescription>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <!-- View Toggle -->
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
      </CardHeader>
      <CardContent>
        <div v-if="completedAudits.length === 0" class="text-center py-8">
          <FileText class="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
          <h3 class="text-lg font-medium mb-2">No Completed Audits</h3>
          <p class="text-muted-foreground">No completed audits available for report generation.</p>
        </div>
        
        <!-- Grid View -->
        <div v-else-if="viewMode === 'grid'" class="space-y-4">
          <div v-for="audit in completedAudits" :key="audit.audit_id" class="border border-border rounded-lg p-4 hover:bg-muted/30 transition-colors">
            <div class="flex items-center justify-between">
              <div class="flex-1 min-w-0">
                <h4 class="font-medium text-foreground truncate">{{ audit.title }}</h4>
                <div class="flex flex-wrap items-center gap-4 mt-2 text-sm text-muted-foreground">
                  <span>ID: {{ audit.audit_id }}</span>
                  <span>SLA: {{ audit.sla_name || 'N/A' }}</span>
                  <span>Auditor: {{ audit.auditor_name || 'N/A' }}</span>
                  <span>Completed: {{ audit.completion_date ? new Date(audit.completion_date).toLocaleDateString() : 'N/A' }}</span>
                </div>
              </div>
              <div class="flex items-center gap-2 ml-4">
                <Badge variant="default" class="bg-green-600 text-white">
                  Completed
                </Badge>
                <Button
                  @click="generateAuditReport(audit)"
                  :disabled="loading"
                  variant="outline"
                  size="sm"
                  class="flex items-center gap-2"
                >
                  <Download class="h-4 w-4" />
                  {{ loading ? 'Generating...' : 'Download Report' }}
                </Button>
              </div>
            </div>
          </div>
        </div>
        
        <!-- List View -->
        <div v-else-if="viewMode === 'list'" class="space-y-2">
          <!-- List Header -->
          <div class="grid grid-cols-12 gap-4 px-4 py-3 bg-muted/50 rounded-lg text-sm font-medium text-muted-foreground">
            <div class="col-span-3">Audit Details</div>
            <div class="col-span-2">SLA</div>
            <div class="col-span-2">Auditor</div>
            <div class="col-span-2">Completion Date</div>
            <div class="col-span-1">Status</div>
            <div class="col-span-2">Actions</div>
          </div>
          
          <!-- List Items -->
          <div v-for="audit in completedAudits" :key="audit.audit_id" 
               class="grid grid-cols-12 gap-4 px-4 py-4 border border-border rounded-lg hover:bg-muted/30 transition-colors">
            <!-- Audit Details -->
            <div class="col-span-3">
              <div class="font-medium text-foreground">{{ audit.title }}</div>
              <div class="text-sm text-muted-foreground">ID: {{ audit.audit_id }}</div>
            </div>
            
            <!-- SLA -->
            <div class="col-span-2">
              <div class="text-sm text-foreground">{{ audit.sla_name || 'N/A' }}</div>
            </div>
            
            <!-- Auditor -->
            <div class="col-span-2">
              <div class="text-sm text-foreground">{{ audit.auditor_name || 'N/A' }}</div>
            </div>
            
            <!-- Completion Date -->
            <div class="col-span-2">
              <div class="text-sm text-foreground">
                {{ audit.completion_date ? new Date(audit.completion_date).toLocaleDateString() : 'N/A' }}
              </div>
            </div>
            
            <!-- Status -->
            <div class="col-span-1">
              <Badge variant="default" class="bg-green-600 text-white text-xs">
                Completed
              </Badge>
            </div>
            
            <!-- Actions -->
            <div class="col-span-2">
              <div class="flex items-center gap-2">
                <Button
                  @click="generateAuditReport(audit)"
                  :disabled="loading"
                  variant="outline"
                  size="sm"
                  class="flex items-center gap-1"
                >
                  <Download class="h-3 w-3" />
                  {{ loading ? 'Generating...' : 'Report' }}
                </Button>
                <Button
                  @click="viewAuditDetails(audit.audit_id)"
                  variant="ghost"
                  size="sm"
                  class="flex items-center gap-1"
                >
                  <Eye class="h-3 w-3" />
                  View
                </Button>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  </div>

  <!-- Popup Modal -->
  <PopupModal />
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { 
  Download,
  Plus,
  TrendingUp,
  CheckCircle,
  Clock,
  AlertTriangle,
  FileText,
  Grid3X3,
  List,
  Eye,
  Edit,
  Trash2
} from 'lucide-vue-next'
import apiService from '@/services/api.js'
import jsPDF from 'jspdf'
import Card from '@/components/ui/card.vue'
import CardHeader from '@/components/ui/card-header.vue'
import CardTitle from '@/components/ui/card-title.vue'
import CardDescription from '@/components/ui/card-description.vue'
import CardContent from '@/components/ui/card-content.vue'
import Button from '@/components/ui/button.vue'
import Badge from '@/components/ui/badge.vue'
import Label from '@/components/ui/label.vue'
import PopupModal from '@/popup/PopupModal.vue'
import { PopupService } from '@/popup/popupService'
import { useNotifications } from '@/composables/useNotifications'
import loggingService from '@/services/loggingService'

const router = useRouter()
const { showSuccess, showError, showWarning, showInfo } = useNotifications()

// API data
const allAudits = ref([])
const availableSLAs = ref([])
const availableUsers = ref([])
const auditFindings = ref([])
const staticQuestionnaires = ref([])
const loading = ref(true)

// Filter state
const selectedDateRange = ref('all')
const selectedStatus = ref('all')
const selectedSLA = ref('all')
const selectedAuditor = ref('all')

// View state
const viewMode = ref('grid') // 'grid' or 'list'

// Load data from API
const loadReportsData = async () => {
  try {
    loading.value = true
    
    // Load audits
    const auditsData = await apiService.getAudits()
    allAudits.value = auditsData.results || auditsData || []
    
    // Load SLAs
    const slasData = await apiService.getAvailableSLAs()
    availableSLAs.value = slasData || []
    
    // Load users
    const usersData = await apiService.getAvailableUsers()
    availableUsers.value = usersData || []
    
    // Load static questionnaires
    const questionnairesData = await apiService.getStaticQuestionnaires()
    staticQuestionnaires.value = questionnairesData.results || questionnairesData || []
    
  } catch (error) {
    console.error('Error loading reports data:', error)
    
    // Show error notification
    await showError('Reports Loading Failed', 'Failed to load audit reports data. Some features may not be available.', {
      action: 'reports_loading_failed',
      error_message: error.message
    })
    
    allAudits.value = []
    availableSLAs.value = []
    availableUsers.value = []
    staticQuestionnaires.value = []
  } finally {
    loading.value = false
  }
}

// Computed properties
const auditors = computed(() => availableUsers.value.filter(user => user.role === 'auditor'))

const completedAudits = computed(() => {
  return filteredAudits.value.filter(audit => audit.status === 'completed')
})

const filteredAudits = computed(() => {
  let audits = allAudits.value

  // Filter by status
  if (selectedStatus.value !== 'all') {
    audits = audits.filter(audit => audit.status === selectedStatus.value)
  }

  // Filter by SLA
  if (selectedSLA.value !== 'all') {
    audits = audits.filter(audit => audit.sla_id === parseInt(selectedSLA.value))
  }

  // Filter by auditor
  if (selectedAuditor.value !== 'all') {
    audits = audits.filter(audit => audit.auditor_id === parseInt(selectedAuditor.value))
  }

  return audits
})

const keyMetrics = computed(() => {
  const total = filteredAudits.value.length
  const completed = filteredAudits.value.filter(a => a.status === 'completed').length
  const inProgress = filteredAudits.value.filter(a => a.status === 'in_progress').length
  const overdue = filteredAudits.value.filter(a => 
    new Date(a.due_date) < new Date() && a.status !== 'completed'
  ).length

  return [
    {
      title: "Total Audits",
      value: total,
      icon: CheckCircle,
      description: "All audit records",
      change: "+12% from last period"
    },
    {
      title: "Completed",
      value: completed,
      icon: CheckCircle,
      description: "Successfully completed",
      change: `${Math.round((completed / total) * 100)}% completion rate`
    },
    {
      title: "In Progress",
      value: inProgress,
      icon: Clock,
      description: "Currently active",
      change: "Active audits"
    },
    {
      title: "Overdue",
      value: overdue,
      icon: AlertTriangle,
      description: "Past due date",
      change: overdue > 0 ? "Requires attention" : "All on track"
    }
  ]
})


// Event handlers
const handleDateRangeChange = () => {
  // Implement date filtering logic
  console.log('Date range changed:', selectedDateRange.value)
}

const handleStatusFilter = () => {
  console.log('Status filter changed:', selectedStatus.value)
}

const handleSLAFilter = () => {
  console.log('SLA filter changed:', selectedSLA.value)
}

const handleAuditorFilter = () => {
  console.log('Auditor filter changed:', selectedAuditor.value)
}

// Load data on component mount
onMounted(async () => {
  await loggingService.logPageView('Audit', 'Audit Reports')
  await loadReportsData()
})

// PDF Generation Functions
const generateAuditReport = async (audit) => {
  try {
    loading.value = true
    
    // Load audit findings for this specific audit
    const findingsData = await apiService.getAuditFindings(audit.audit_id)
    const findings = findingsData.results || findingsData || []
    
    // Load SLA details if available
    let slaDetails = null
    let slaMetrics = []
    let performanceData = null
    
    if (audit.sla_id) {
      try {
        // Fetch SLA details
        const slaResponse = await apiService.getSLA(audit.sla_id)
        slaDetails = slaResponse
        
        // Fetch SLA metrics for this SLA
        const metricsResponse = await apiService.getSLAMetrics(audit.sla_id)
        slaMetrics = metricsResponse.results || metricsResponse || []
        
        // Fetch performance data for this SLA
        const perfResponse = await apiService.getPerformanceDashboard({ 
          sla_id: audit.sla_id,
          period: 'monthly'
        })
        performanceData = perfResponse
      } catch (error) {
        console.error('Error loading SLA data:', error)
      }
    }
    
    // Create PDF
    const pdf = new jsPDF()
    let yPosition = 20
    
    // ============================================
    // COVER PAGE / HEADER WITH STYLING
    // ============================================
    // Header box with gradient effect (simulated with overlapping rectangles)
    pdf.setFillColor(37, 99, 235) // blue-600
    pdf.rect(0, 0, 210, 50, 'F')
    pdf.setFillColor(59, 130, 246) // blue-500
    pdf.rect(0, 0, 210, 45, 'F')
    
    pdf.setTextColor(255, 255, 255) // white text
    pdf.setFontSize(28)
    pdf.setFont('helvetica', 'bold')
    pdf.text('AUDIT REPORT', 105, 25, { align: 'center' })
    
    pdf.setFontSize(11)
    pdf.setFont('helvetica', 'normal')
    pdf.text(audit.title || 'Audit Report', 105, 35, { align: 'center' })
    
    // Info bar
    pdf.setFillColor(243, 244, 246) // gray-100
    pdf.rect(0, 50, 210, 15, 'F')
    pdf.setTextColor(75, 85, 99) // gray-600
    pdf.setFontSize(9)
    pdf.text(`Report Generated: ${new Date().toLocaleDateString()} ${new Date().toLocaleTimeString()}`, 105, 59, { align: 'center' })
    
    // Reset colors
    pdf.setTextColor(0, 0, 0)
    yPosition = 75
    
    // ============================================
    // AUDIT INFORMATION SECTION WITH STYLED BOX
    // ============================================
    // Section header with background
    pdf.setFillColor(239, 246, 255) // blue-50
    pdf.rect(15, yPosition - 5, 180, 10, 'F')
    pdf.setFontSize(14)
    pdf.setFont('helvetica', 'bold')
    pdf.setTextColor(29, 78, 216) // blue-700
    pdf.text('1. AUDIT INFORMATION', 20, yPosition + 2)
    pdf.setTextColor(0, 0, 0)
    yPosition += 12
    
    // Information box with border
    pdf.setDrawColor(219, 234, 254) // blue-200
    pdf.setLineWidth(0.5)
    const auditInfoHeight = 85
    pdf.rect(15, yPosition, 180, auditInfoHeight)
    yPosition += 8
    
    pdf.setFontSize(9)
    pdf.setFont('helvetica', 'normal')
    
    // Two-column layout for audit info
    const col1X = 20
    const col2X = 110
    let tempY = yPosition
    
    // Column 1
    pdf.setFont('helvetica', 'bold')
    pdf.text('Audit ID:', col1X, tempY)
    pdf.setFont('helvetica', 'normal')
    pdf.text(String(audit.audit_id), col1X + 30, tempY)
    tempY += 6
    
    pdf.setFont('helvetica', 'bold')
    pdf.text('Audit Title:', col1X, tempY)
    pdf.setFont('helvetica', 'normal')
    const titleText = pdf.splitTextToSize(audit.title || 'N/A', 60)
    pdf.text(titleText, col1X, tempY + 4)
    tempY += 4 + (titleText.length * 4)
    
    pdf.setFont('helvetica', 'bold')
    pdf.text('Audit Type:', col1X, tempY)
    pdf.setFont('helvetica', 'normal')
    pdf.text(audit.audit_type || 'N/A', col1X + 30, tempY)
    tempY += 6
    
    pdf.setFont('helvetica', 'bold')
    pdf.text('Frequency:', col1X, tempY)
    pdf.setFont('helvetica', 'normal')
    pdf.text(audit.frequency || 'N/A', col1X + 30, tempY)
    tempY += 6
    
    // Status badge
    pdf.setFont('helvetica', 'bold')
    pdf.text('Status:', col1X, tempY)
    const statusColors = {
      'completed': { bg: [220, 252, 231], text: [22, 101, 52] }, // green
      'in_progress': { bg: [254, 249, 195], text: [133, 77, 14] }, // yellow
      'under_review': { bg: [219, 234, 254], text: [30, 64, 175] }, // blue
      'created': { bg: [243, 244, 246], text: [55, 65, 81] }, // gray
      'rejected': { bg: [254, 226, 226], text: [153, 27, 27] } // red
    }
    const statusColor = statusColors[audit.status] || statusColors['created']
    pdf.setFillColor(...statusColor.bg)
    pdf.roundedRect(col1X + 20, tempY - 3, 35, 6, 1, 1, 'F')
    pdf.setTextColor(...statusColor.text)
    pdf.setFontSize(8)
    pdf.text(audit.status.toUpperCase(), col1X + 22, tempY + 1)
    pdf.setTextColor(0, 0, 0)
    pdf.setFontSize(9)
    
    // Column 2
    tempY = yPosition
    
    pdf.setFont('helvetica', 'bold')
    pdf.text('Auditor:', col2X, tempY)
    pdf.setFont('helvetica', 'normal')
    pdf.text(audit.auditor_name || 'N/A', col2X + 25, tempY)
    tempY += 6
    
    pdf.setFont('helvetica', 'bold')
    pdf.text('Reviewer:', col2X, tempY)
    pdf.setFont('helvetica', 'normal')
    pdf.text(audit.reviewer_name || 'N/A', col2X + 25, tempY)
    tempY += 6
    
    pdf.setFont('helvetica', 'bold')
    pdf.text('Due Date:', col2X, tempY)
    pdf.setFont('helvetica', 'normal')
    pdf.text(new Date(audit.due_date).toLocaleDateString(), col2X + 25, tempY)
    tempY += 6
    
    yPosition += auditInfoHeight + 10
    
    // ============================================
    // SLA DETAILS SECTION - TABULAR FORMAT
    // ============================================
    if (slaDetails) {
      // Check if we need a new page
      if (yPosition > 220) {
        pdf.addPage()
        yPosition = 20
      }
      
      // Section header with background
      pdf.setFillColor(239, 246, 255) // blue-50
      pdf.rect(15, yPosition - 5, 180, 10, 'F')
      pdf.setFontSize(14)
      pdf.setFont('helvetica', 'bold')
      pdf.setTextColor(29, 78, 216) // blue-700
      pdf.text('2. SLA DETAILS', 20, yPosition + 2)
      pdf.setTextColor(0, 0, 0)
      yPosition += 15
      
      // Tabular format for SLA details
      const tableX = 15
      const labelWidth = 50
      const valueWidth = 130
      let rowY = yPosition
      
      // Helper function to add table row (skip N/A values)
      const addSLARow = (label, value, isDate = false) => {
        // Skip if value is N/A, empty, null, or undefined
        if (!value || value === 'N/A') {
          return
        }
        
        // Check if we need a new page
        if (rowY > 260) {
          pdf.addPage()
          rowY = 20
        }
        
        const displayValue = isDate ? new Date(value).toLocaleDateString() : value
        
        // Label cell background
        pdf.setFillColor(249, 250, 251) // gray-50
        pdf.rect(tableX, rowY, labelWidth, 8, 'F')
        
        // Label text
        pdf.setFontSize(8)
        pdf.setFont('helvetica', 'bold')
        pdf.setTextColor(75, 85, 99) // gray-600
        pdf.text(label, tableX + 2, rowY + 5)
        
        // Value cell and text
        pdf.setFont('helvetica', 'normal')
        pdf.setTextColor(0, 0, 0)
        
        const valueLines = pdf.splitTextToSize(String(displayValue), valueWidth - 4)
        const cellHeight = Math.max(8, valueLines.length * 4.5 + 3)
        
        // Draw cell borders
        pdf.setDrawColor(229, 231, 235)
        pdf.rect(tableX, rowY, labelWidth, cellHeight)
        pdf.rect(tableX + labelWidth, rowY, valueWidth, cellHeight)
        
        // Value text
        pdf.text(valueLines, tableX + labelWidth + 2, rowY + 5)
        rowY += cellHeight
        
        pdf.setTextColor(0, 0, 0)
      }
      
      // Add SLA information rows (only non-N/A values)
      addSLARow('SLA ID', slaDetails.sla_id)
      addSLARow('SLA Name', slaDetails.sla_name)
      addSLARow('SLA Type', slaDetails.sla_type)
      addSLARow('Status', slaDetails.status)
      addSLARow('Priority', slaDetails.priority)
      addSLARow('Effective Date', slaDetails.effective_date, true)
      addSLARow('Expiry Date', slaDetails.expiry_date, true)
      
      if (slaDetails.compliance_score) {
        addSLARow('Compliance Score', `${slaDetails.compliance_score}%`)
      }
      
      addSLARow('Business Service', slaDetails.business_service_impacted)
      addSLARow('Reporting Frequency', slaDetails.reporting_frequency)
      addSLARow('Baseline Period', slaDetails.baseline_period)
      
      if (slaDetails.penalty_threshold) {
        addSLARow('Penalty Threshold', `${slaDetails.penalty_threshold}%`)
      }
      
      if (slaDetails.credit_threshold) {
        addSLARow('Credit Threshold', `${slaDetails.credit_threshold}%`)
      }
      
      addSLARow('Compliance Framework', slaDetails.compliance_framework)
      addSLARow('Measurement Methodology', slaDetails.measurement_methodology)
      addSLARow('Audit Requirements', slaDetails.audit_requirements)
      
      yPosition = rowY + 10
    }
    
    // ============================================
    // SLA METRICS & PERFORMANCE ANALYSIS - TABULAR
    // ============================================
    if (slaMetrics.length > 0) {
      // Check if we need a new page
      if (yPosition > 200) {
        pdf.addPage()
        yPosition = 20
      }
      
      // Section header with background
      pdf.setFillColor(239, 246, 255) // blue-50
      pdf.rect(15, yPosition - 5, 180, 10, 'F')
      pdf.setFontSize(14)
      pdf.setFont('helvetica', 'bold')
      pdf.setTextColor(29, 78, 216) // blue-700
      pdf.text('3. SLA METRICS & TARGETS', 20, yPosition + 2)
      pdf.setTextColor(0, 0, 0)
      yPosition += 15
      
      slaMetrics.forEach((metric, index) => {
        // Check if we need a new page
        if (yPosition > 230) {
          pdf.addPage()
          yPosition = 20
        }
        
        // Metric header
        pdf.setFillColor(249, 250, 251) // gray-50
        pdf.rect(15, yPosition, 180, 10, 'F')
    pdf.setFontSize(10)
        pdf.setFont('helvetica', 'bold')
        pdf.text(`Metric ${index + 1}: ${metric.metric_name}`, 20, yPosition + 6)
        yPosition += 10
        
        // Metric table
        const tableX = 15
        const labelWidth = 45
        const valueWidth = 135
        let rowY = yPosition
        
        const addMetricRow = (label, value) => {
          if (!value || value === 'N/A') return
          
          if (rowY > 260) {
            pdf.addPage()
            rowY = 20
          }
          
          // Label cell
          pdf.setFillColor(249, 250, 251)
          pdf.rect(tableX, rowY, labelWidth, 8, 'F')
          pdf.setFontSize(8)
          pdf.setFont('helvetica', 'bold')
          pdf.setTextColor(75, 85, 99)
          pdf.text(label, tableX + 2, rowY + 5)
          
          // Value cell
    pdf.setFont('helvetica', 'normal')
          pdf.setTextColor(0, 0, 0)
          const valueLines = pdf.splitTextToSize(String(value), valueWidth - 4)
          const cellHeight = Math.max(8, valueLines.length * 4.5 + 3)
          
          pdf.setDrawColor(229, 231, 235)
          pdf.rect(tableX, rowY, labelWidth, cellHeight)
          pdf.rect(tableX + labelWidth, rowY, valueWidth, cellHeight)
          pdf.text(valueLines, tableX + labelWidth + 2, rowY + 5)
          rowY += cellHeight
          pdf.setTextColor(0, 0, 0)
        }
        
        // Add metric details
        if (metric.threshold) {
          const thresholdValue = metric.measurement_unit 
            ? `${metric.threshold} ${metric.measurement_unit}`
            : metric.threshold
          addMetricRow('Target Threshold', thresholdValue)
        }
        
        addMetricRow('Frequency', metric.frequency)
        addMetricRow('Methodology', metric.measurement_methodology)
        addMetricRow('Penalty', metric.penalty)
        
        yPosition = rowY + 6
      })
      
      yPosition += 10
    }
    
    // ============================================
    // PERFORMANCE DASHBOARD SUMMARY
    // ============================================
    if (performanceData) {
      // Check if we need a new page
      if (yPosition > 200) {
        pdf.addPage()
        yPosition = 20
      }
      
      // Section header with background
      pdf.setFillColor(239, 246, 255) // blue-50
      pdf.rect(15, yPosition - 5, 180, 10, 'F')
      pdf.setFontSize(14)
      pdf.setFont('helvetica', 'bold')
      pdf.setTextColor(29, 78, 216) // blue-700
      pdf.text('4. PERFORMANCE SUMMARY', 20, yPosition + 2)
      pdf.setTextColor(0, 0, 0)
    yPosition += 15
    
      // Overall compliance metrics with styled KPI cards
      if (performanceData.overview) {
        const overview = performanceData.overview
        
        // KPI Cards in grid layout (2x3)
        const cardWidth = 57
        const cardHeight = 22
        const cardSpacing = 5
        const cardStartX = 20
        
        const kpiCards = [
          {
            label: 'Overall Compliance',
            value: `${overview.overall_compliance || 0}%`,
            color: overview.overall_compliance >= 95 ? [34, 197, 94] : 
                   overview.overall_compliance >= 90 ? [245, 158, 11] : [239, 68, 68]
          },
          {
            label: 'Compliance Trend',
            value: `${overview.compliance_trend >= 0 ? '+' : ''}${overview.compliance_trend || 0}%`,
            color: overview.compliance_trend >= 0 ? [34, 197, 94] : [239, 68, 68]
          },
          {
            label: 'Total Metrics',
            value: String(overview.total_metrics || 0),
            color: [59, 130, 246] // blue
          },
          {
            label: 'Metrics in Breach',
            value: String(overview.metrics_in_breach || 0),
            color: overview.metrics_in_breach > 0 ? [239, 68, 68] : [34, 197, 94]
          },
          {
            label: 'Performance Gap',
            value: `${overview.avg_performance_gap || 0}%`,
            color: [245, 158, 11] // amber
          },
          {
            label: 'Vendors at Risk',
            value: String(overview.vendors_at_risk || 0),
            color: overview.vendors_at_risk > 0 ? [245, 158, 11] : [34, 197, 94]
          }
        ]
        
        kpiCards.forEach((card, index) => {
          const col = index % 3
          const row = Math.floor(index / 3)
          const x = cardStartX + (col * (cardWidth + cardSpacing))
          const y = yPosition + (row * (cardHeight + cardSpacing))
          
          // Card border
          pdf.setDrawColor(229, 231, 235) // gray-200
          pdf.setLineWidth(0.3)
          pdf.rect(x, y, cardWidth, cardHeight)
          
          // Left accent bar
          pdf.setFillColor(...card.color)
          pdf.rect(x, y, 2, cardHeight, 'F')
          
          // Label
          pdf.setFontSize(7)
          pdf.setFont('helvetica', 'normal')
          pdf.setTextColor(107, 114, 128) // gray-500
          pdf.text(card.label, x + 5, y + 7)
          
          // Value
      pdf.setFontSize(14)
      pdf.setFont('helvetica', 'bold')
          pdf.setTextColor(17, 24, 39) // gray-900
          pdf.text(card.value, x + 5, y + 16)
          
          pdf.setTextColor(0, 0, 0)
        })
        
        yPosition += (cardHeight * 2) + cardSpacing + 15
        
        // Last audit date info
        pdf.setFontSize(8)
        pdf.setTextColor(107, 114, 128)
        pdf.text(`Last Audit: ${overview.last_audit_date || 'N/A'}`, 20, yPosition)
        pdf.setTextColor(0, 0, 0)
      yPosition += 10
      }
      
      // Metrics distribution with visual donut chart
      if (performanceData.metrics_distribution) {
        const dist = performanceData.metrics_distribution
        const total = (dist.compliant || 0) + (dist.at_risk || 0) + (dist.breach || 0)
        
        if (total > 0) {
          pdf.setFontSize(11)
          pdf.setFont('helvetica', 'bold')
          pdf.text('Metrics Distribution:', 20, yPosition)
          yPosition += 10
          
          // Donut chart visualization
          const centerX = 45
          const centerY = yPosition + 20
          const outerRadius = 18
          const innerRadius = 11
          
          const compliantPct = (dist.compliant / total) * 100
          const atRiskPct = (dist.at_risk / total) * 100
          const breachPct = (dist.breach / total) * 100
          
          // Calculate angles (starting from top, going clockwise)
          let currentAngle = -90 // Start from top
          
          // Helper function to draw donut segment
          const drawSegment = (percentage, color) => {
            if (percentage === 0) return
            
            const angleSize = (percentage / 100) * 360
            const startAngle = currentAngle
            const endAngle = currentAngle + angleSize
            
            // Outer arc
            pdf.setFillColor(...color)
            
            // Draw segment using triangular slices
            const slices = Math.max(Math.ceil(angleSize / 10), 1)
            for (let i = 0; i < slices; i++) {
              const a1 = startAngle + (angleSize / slices) * i
              const a2 = startAngle + (angleSize / slices) * (i + 1)
              
              const a1Rad = (a1 * Math.PI) / 180
              const a2Rad = (a2 * Math.PI) / 180
              
              // Outer points
              const x1Outer = centerX + outerRadius * Math.cos(a1Rad)
              const y1Outer = centerY + outerRadius * Math.sin(a1Rad)
              const x2Outer = centerX + outerRadius * Math.cos(a2Rad)
              const y2Outer = centerY + outerRadius * Math.sin(a2Rad)
              
              // Inner points
              const x1Inner = centerX + innerRadius * Math.cos(a1Rad)
              const y1Inner = centerY + innerRadius * Math.sin(a1Rad)
              const x2Inner = centerX + innerRadius * Math.cos(a2Rad)
              const y2Inner = centerY + innerRadius * Math.sin(a2Rad)
              
              // Draw quadrilateral
              pdf.setFillColor(...color)
              pdf.triangle(x1Outer, y1Outer, x2Outer, y2Outer, x1Inner, y1Inner, 'F')
              pdf.triangle(x2Outer, y2Outer, x2Inner, y2Inner, x1Inner, y1Inner, 'F')
            }
            
            currentAngle += angleSize
          }
          
          // Draw segments
          drawSegment(compliantPct, [34, 197, 94]) // green
          drawSegment(atRiskPct, [245, 158, 11]) // amber
          drawSegment(breachPct, [239, 68, 68]) // red
          
          // Center white circle (creates donut effect)
          pdf.setFillColor(255, 255, 255)
          pdf.circle(centerX, centerY, innerRadius, 'F')
          
          // Total in center
          pdf.setFontSize(14)
          pdf.setFont('helvetica', 'bold')
          pdf.setTextColor(17, 24, 39)
          const totalText = String(total)
          const totalWidth = pdf.getTextWidth(totalText)
          pdf.text(totalText, centerX - totalWidth / 2, centerY + 2)
          pdf.setFontSize(7)
          pdf.setFont('helvetica', 'normal')
          pdf.setTextColor(107, 114, 128)
          const labelText = 'metrics'
          const labelWidth = pdf.getTextWidth(labelText)
          pdf.text(labelText, centerX - labelWidth / 2, centerY + 7)
          pdf.setTextColor(0, 0, 0)
          
          // Legend with values
          const legendX = centerX + outerRadius + 10
          let legendY = centerY - 15
          
          const legendItems = [
            { label: 'Compliant', value: dist.compliant || 0, color: [34, 197, 94], pct: compliantPct },
            { label: 'At Risk', value: dist.at_risk || 0, color: [245, 158, 11], pct: atRiskPct },
            { label: 'Breach', value: dist.breach || 0, color: [239, 68, 68], pct: breachPct }
          ]
          
          legendItems.forEach((item, idx) => {
            const yPos = legendY + (idx * 10)
            
            // Color box
            pdf.setFillColor(...item.color)
            pdf.roundedRect(legendX, yPos - 2, 3, 3, 0.5, 0.5, 'F')
            
            // Label and value
            pdf.setFontSize(8)
            pdf.setFont('helvetica', 'normal')
            pdf.setTextColor(55, 65, 81)
            pdf.text(`${item.label}:`, legendX + 5, yPos + 1)
            
            pdf.setFont('helvetica', 'bold')
            pdf.text(`${item.value} (${Math.round(item.pct)}%)`, legendX + 28, yPos + 1)
            
            // Progress bar
            const barWidth = 35
            const barHeight = 2
            const barY = yPos + 3
            pdf.setFillColor(229, 231, 235) // gray-200
            pdf.rect(legendX + 5, barY, barWidth, barHeight, 'F')
            pdf.setFillColor(...item.color)
            pdf.rect(legendX + 5, barY, (item.pct / 100) * barWidth, barHeight, 'F')
          })
          
          pdf.setTextColor(0, 0, 0)
          yPosition += 50
        }
      }
      
      // Detailed metrics analysis with visual bar graphs
      if (performanceData.metrics_analysis && performanceData.metrics_analysis.length > 0) {
        // Check if we need a new page
        if (yPosition > 200) {
          pdf.addPage()
          yPosition = 20
        }
        
        pdf.setFillColor(239, 246, 255) // blue-50
        pdf.rect(15, yPosition - 5, 180, 10, 'F')
        pdf.setFontSize(12)
        pdf.setFont('helvetica', 'bold')
        pdf.setTextColor(29, 78, 216) // blue-700
        pdf.text('Target vs Actual Performance Comparison', 20, yPosition + 2)
        pdf.setTextColor(0, 0, 0)
        yPosition += 12
        
        performanceData.metrics_analysis.slice(0, 8).forEach((metric, index) => {
          // Check if we need a new page
          if (yPosition > 245) {
            pdf.addPage()
            yPosition = 20
          }
          
          // Metric card with border
          const cardHeight = 28
          pdf.setDrawColor(229, 231, 235) // gray-200
          pdf.setLineWidth(0.3)
          pdf.rect(15, yPosition, 180, cardHeight)
          
          // Status indicator bar (left side)
          const statusColors = {
            'Compliant': [34, 197, 94], // green
            'At Risk': [245, 158, 11], // yellow
            'Breach': [239, 68, 68] // red
          }
          const indicatorColor = statusColors[metric.status] || [156, 163, 175]
          pdf.setFillColor(...indicatorColor)
          pdf.rect(15, yPosition, 3, cardHeight, 'F')
          
          // Metric name and details
          pdf.setFontSize(9)
          pdf.setFont('helvetica', 'bold')
          pdf.text(metric.name, 22, yPosition + 6)
          
        pdf.setFont('helvetica', 'normal')
          pdf.setFontSize(7)
          pdf.setTextColor(107, 114, 128) // gray-500
          pdf.text(`${metric.vendor} • ${metric.check_date}`, 22, yPosition + 11)
          pdf.setTextColor(0, 0, 0)
          
          // Visual bar graph - Target vs Actual
          const barY = yPosition + 16
          const barWidth = 155
          const barHeight = 4
          const barStartX = 22
          
          // Target bar (background - light blue)
          pdf.setFillColor(219, 234, 254) // blue-200
          pdf.rect(barStartX, barY, barWidth, barHeight, 'F')
          pdf.setFontSize(7)
          pdf.setFont('helvetica', 'bold')
          pdf.text('Target', barStartX, barY - 1)
          pdf.setFont('helvetica', 'normal')
          pdf.text(metric.sla_target, barStartX + barWidth + 2, barY + 3)
          
          // Actual bar (foreground - color based on status)
          const actualBarY = barY + 6
          const actualPercentage = Math.min(metric.performance_percentage, 100)
          const actualBarWidth = (actualPercentage / 100) * barWidth
          
          pdf.setFillColor(...indicatorColor)
          pdf.rect(barStartX, actualBarY, actualBarWidth, barHeight, 'F')
          pdf.setFont('helvetica', 'bold')
          pdf.text('Actual', barStartX, actualBarY - 1)
          pdf.setFont('helvetica', 'normal')
          pdf.text(metric.actual_value, barStartX + barWidth + 2, actualBarY + 3)
          
          // Performance percentage badge
          pdf.setFontSize(8)
          pdf.setFont('helvetica', 'bold')
          const perfText = `${Math.round(metric.performance_percentage)}%`
          const perfBadgeX = barStartX + barWidth - 20
          const perfBadgeY = yPosition + 4
          
          // Badge background
          const badgeBg = metric.performance_percentage >= 95 ? [220, 252, 231] : 
                         metric.performance_percentage >= 90 ? [254, 249, 195] : [254, 226, 226]
          const badgeText = metric.performance_percentage >= 95 ? [22, 101, 52] :
                           metric.performance_percentage >= 90 ? [133, 77, 14] : [153, 27, 27]
          
          pdf.setFillColor(...badgeBg)
          pdf.roundedRect(perfBadgeX, perfBadgeY, 16, 6, 1, 1, 'F')
          pdf.setTextColor(...badgeText)
          pdf.text(perfText, perfBadgeX + 2, perfBadgeY + 4)
          pdf.setTextColor(0, 0, 0)
          
          yPosition += cardHeight + 3
        })
        
        if (performanceData.metrics_analysis.length > 8) {
          pdf.setFontSize(8)
          pdf.setTextColor(107, 114, 128)
          pdf.text(`+ ${performanceData.metrics_analysis.length - 8} more metrics not shown`, 20, yPosition + 5)
          pdf.setTextColor(0, 0, 0)
        }
        
        yPosition += 10
      }
    }
    
    // ============================================
    // AUDIT FINDINGS SECTION - TABULAR FORMAT
    // ============================================
    if (findings.length > 0) {
      // Check if we need a new page
      if (yPosition > 220) {
        pdf.addPage()
        yPosition = 20
      }
      
      // Section header with background
      pdf.setFillColor(239, 246, 255) // blue-50
      pdf.rect(15, yPosition - 5, 180, 10, 'F')
      pdf.setFontSize(14)
          pdf.setFont('helvetica', 'bold')
      pdf.setTextColor(29, 78, 216) // blue-700
      pdf.text('5. AUDIT FINDINGS & OBSERVATIONS', 20, yPosition + 2)
      pdf.setTextColor(0, 0, 0)
      yPosition += 15
      
      findings.forEach((finding, index) => {
        // Check if we need a new page
        if (yPosition > 230) {
          pdf.addPage()
          yPosition = 20
        }
        
        // Finding container with border
        const findingStartY = yPosition
        
        // Finding header with number and date
        pdf.setFillColor(249, 250, 251) // gray-50
        pdf.rect(15, yPosition, 180, 12, 'F')
        
        pdf.setFontSize(11)
          pdf.setFont('helvetica', 'bold')
        pdf.text(`Finding #${index + 1}`, 20, yPosition + 8)
        
        if (finding.check_date) {
          pdf.setFontSize(8)
          pdf.setFont('helvetica', 'normal')
          pdf.setTextColor(107, 114, 128) // gray-500
          pdf.text(`Checked: ${new Date(finding.check_date).toLocaleDateString()}`, 150, yPosition + 8)
          pdf.setTextColor(0, 0, 0)
        }
        
        yPosition += 12
        
        // Draw outer border
        pdf.setDrawColor(229, 231, 235) // gray-200
        pdf.setLineWidth(0.3)
        
        // Tabular format for finding details
        const tableX = 15
        const labelWidth = 45
        const valueWidth = 135
        let rowY = yPosition
        
        // Helper function to add table row (only if value is not N/A or empty)
        const addTableRow = (label, value, isMultiline = true) => {
          // Skip if value is N/A, empty, null, or undefined
          if (!value || value === 'N/A' || value.trim() === '') {
            return
          }
          
          // Check if we need a new page
          if (rowY > 260) {
            pdf.addPage()
            rowY = 20
          }
          
          // Label cell background
          pdf.setFillColor(249, 250, 251) // gray-50
          pdf.rect(tableX, rowY, labelWidth, 8, 'F')
          
          // Label text
          pdf.setFontSize(8)
            pdf.setFont('helvetica', 'bold')
          pdf.setTextColor(75, 85, 99) // gray-600
          pdf.text(label, tableX + 2, rowY + 5)
            
          // Value cell
            pdf.setFont('helvetica', 'normal')
          pdf.setTextColor(0, 0, 0)
          
          if (isMultiline) {
            const valueLines = pdf.splitTextToSize(value, valueWidth - 4)
            const cellHeight = Math.max(8, valueLines.length * 4.5 + 3)
            
            // Draw cell border
            pdf.setDrawColor(229, 231, 235)
            pdf.rect(tableX, rowY, labelWidth, cellHeight)
            pdf.rect(tableX + labelWidth, rowY, valueWidth, cellHeight)
            
            // Value text
            pdf.text(valueLines, tableX + labelWidth + 2, rowY + 5)
            rowY += cellHeight
          } else {
            // Single line
            pdf.setDrawColor(229, 231, 235)
            pdf.rect(tableX, rowY, labelWidth, 8)
            pdf.rect(tableX + labelWidth, rowY, valueWidth, 8)
            pdf.text(value, tableX + labelWidth + 2, rowY + 5)
            rowY += 8
          }
          
          pdf.setTextColor(0, 0, 0)
        }
        
        // Add rows only if they have values
        if (finding.details_of_finding && finding.details_of_finding !== 'N/A') {
          addTableRow('Finding Details', finding.details_of_finding, true)
        }
        
        if (finding.evidence && finding.evidence !== 'N/A') {
          addTableRow('Evidence', finding.evidence, true)
        }
        
        if (finding.how_to_verify && finding.how_to_verify !== 'N/A') {
          addTableRow('Verification Method', finding.how_to_verify, true)
        }
        
        if (finding.impact_recommendations && finding.impact_recommendations !== 'N/A') {
          addTableRow('Impact & Recommendations', finding.impact_recommendations, true)
        }
        
        if (finding.comment && finding.comment !== 'N/A') {
          addTableRow('Comments', finding.comment, true)
        }
        
        yPosition = rowY + 8
      })
    }
    
    // ============================================
    // COMPLIANCE VISUALIZATION & CHARTS - ENHANCED
    // ============================================
    if (performanceData && performanceData.audit_history && performanceData.audit_history.length > 0) {
      // Check if we need a new page
      if (yPosition > 150) {
                pdf.addPage()
                yPosition = 20
              }
              
      // Section header with background
      pdf.setFillColor(239, 246, 255) // blue-50
      pdf.rect(15, yPosition - 5, 180, 10, 'F')
      pdf.setFontSize(14)
      pdf.setFont('helvetica', 'bold')
      pdf.setTextColor(29, 78, 216) // blue-700
      pdf.text('6. COMPLIANCE TREND ANALYSIS', 20, yPosition + 2)
      pdf.setTextColor(0, 0, 0)
      yPosition += 15
      
      // Chart container with border
      const chartContainerHeight = 95
      pdf.setDrawColor(219, 234, 254) // blue-200
      pdf.setLineWidth(0.5)
      pdf.rect(15, yPosition, 180, chartContainerHeight)
      
      // Chart background (light gray)
      const chartX = 25
      const chartY = yPosition + 15
      const chartWidth = 160
      const chartHeight = 65
      
      pdf.setFillColor(249, 250, 251) // gray-50
      pdf.rect(chartX, chartY, chartWidth, chartHeight, 'F')
      
      // Grid lines (horizontal)
      pdf.setDrawColor(229, 231, 235) // gray-200
      pdf.setLineWidth(0.2)
      for (let i = 0; i <= 4; i++) {
        const gridY = chartY + (chartHeight / 4) * i
        pdf.line(chartX, gridY, chartX + chartWidth, gridY)
        
        // Y-axis labels
        const percentage = 100 - (i * 25)
        pdf.setFontSize(7)
        pdf.setTextColor(107, 114, 128) // gray-500
        pdf.text(`${percentage}%`, chartX - 10, gridY + 2)
      }
      pdf.setTextColor(0, 0, 0)
      
      // Draw target line at 95% with better styling
      const targetY = chartY + chartHeight - (chartHeight * 0.95)
      pdf.setDrawColor(59, 130, 246) // blue-500
      pdf.setLineWidth(0.8)
      pdf.setLineDash([3, 2])
      pdf.line(chartX, targetY, chartX + chartWidth, targetY)
      pdf.setLineDash([])
      
      // Target label with background
      pdf.setFillColor(219, 234, 254) // blue-200
      pdf.roundedRect(chartX + chartWidth - 30, targetY - 4, 28, 6, 1, 1, 'F')
      pdf.setFontSize(7)
              pdf.setFont('helvetica', 'bold')
      pdf.setTextColor(29, 78, 216) // blue-700
      pdf.text('95% Target', chartX + chartWidth - 28, targetY + 1)
      pdf.setTextColor(0, 0, 0)
      
      // Draw enhanced bars
      const history = performanceData.audit_history.slice(0, 8)
      const barWidth = (chartWidth / history.length) - 6
      const barSpacing = 4
      
      history.forEach((auditItem, index) => {
        const compliance = auditItem.compliance_rate || 0
        const barHeight = (compliance / 100) * chartHeight
        const x = chartX + (index * (barWidth + barSpacing)) + 3
        const y = chartY + chartHeight - barHeight
        
        // Bar shadow (subtle)
        pdf.setFillColor(0, 0, 0)
        pdf.setGState(pdf.GState({ opacity: 0.1 }))
        pdf.rect(x + 1, y + 1, barWidth, barHeight, 'F')
        pdf.setGState(pdf.GState({ opacity: 1 }))
        
        // Bar color based on compliance with gradient effect
        let mainColor, lightColor
        if (compliance >= 95) {
          mainColor = [34, 197, 94] // green-500
          lightColor = [134, 239, 172] // green-300
        } else if (compliance >= 90) {
          mainColor = [245, 158, 11] // amber-500
          lightColor = [253, 230, 138] // amber-200
        } else {
          mainColor = [239, 68, 68] // red-500
          lightColor = [252, 165, 165] // red-300
        }
        
        // Main bar
        pdf.setFillColor(...mainColor)
        pdf.rect(x, y, barWidth, barHeight, 'F')
        
        // Highlight on left side (gradient effect simulation)
        pdf.setFillColor(...lightColor)
        pdf.setGState(pdf.GState({ opacity: 0.5 }))
        pdf.rect(x, y, 1, barHeight, 'F')
        pdf.setGState(pdf.GState({ opacity: 1 }))
        
        // Value on top of bar
        pdf.setFontSize(7)
        pdf.setFont('helvetica', 'bold')
        pdf.setTextColor(...mainColor)
        const valueText = `${Math.round(compliance)}%`
        const textWidth = pdf.getTextWidth(valueText)
        pdf.text(valueText, x + (barWidth - textWidth) / 2, y - 2)
        
        // Period label below
        pdf.setFontSize(6)
        pdf.setTextColor(75, 85, 99) // gray-600
              pdf.setFont('helvetica', 'normal')
        const periodText = auditItem.period || `P${index + 1}`
        const periodWidth = pdf.getTextWidth(periodText)
        pdf.text(periodText, x + (barWidth - periodWidth) / 2, chartY + chartHeight + 7)
      })
      
      pdf.setTextColor(0, 0, 0)
      
      // Enhanced Legend with boxes
      yPosition += chartContainerHeight - 12
      const legendY = yPosition
      const legendX = chartX + 10
      
      pdf.setFontSize(7)
      pdf.setFont('helvetica', 'normal')
      
      // Compliant
      pdf.setFillColor(34, 197, 94)
      pdf.roundedRect(legendX, legendY, 3, 3, 0.5, 0.5, 'F')
      pdf.text('Compliant (≥95%)', legendX + 5, legendY + 2.5)
      
      // At Risk
      pdf.setFillColor(245, 158, 11)
      pdf.roundedRect(legendX + 45, legendY, 3, 3, 0.5, 0.5, 'F')
      pdf.text('At Risk (90-94%)', legendX + 50, legendY + 2.5)
      
      // Breach
      pdf.setFillColor(239, 68, 68)
      pdf.roundedRect(legendX + 95, legendY, 3, 3, 0.5, 0.5, 'F')
      pdf.text('Breach (<90%)', legendX + 100, legendY + 2.5)
      
      yPosition += 15
    }
    
    // ============================================
    // EXECUTIVE SUMMARY / CONCLUSION
    // ============================================
    if (yPosition > 220) {
      pdf.addPage()
      yPosition = 20
    }
    
    pdf.setFontSize(14)
    pdf.setFont('helvetica', 'bold')
    pdf.setTextColor(29, 78, 216)
    pdf.text('7. EXECUTIVE SUMMARY', 20, yPosition)
    pdf.setTextColor(0, 0, 0)
        yPosition += 10
    
    pdf.setFontSize(10)
    pdf.setFont('helvetica', 'normal')
    
    // Summary based on data
    const summaryText = `This audit report for "${audit.title}" was completed on ${audit.completion_date ? new Date(audit.completion_date).toLocaleDateString() : 'N/A'}. `
    let summaryContent = summaryText
    
    if (performanceData && performanceData.overview) {
      summaryContent += `The overall SLA compliance rate is ${performanceData.overview.overall_compliance || 0}% with ${performanceData.overview.metrics_in_breach || 0} metrics currently in breach. `
      
      if (performanceData.overview.overall_compliance >= 95) {
        summaryContent += 'The SLA is meeting performance targets and is in good standing. '
      } else if (performanceData.overview.overall_compliance >= 90) {
        summaryContent += 'The SLA requires attention as it is approaching breach thresholds. '
      } else {
        summaryContent += 'The SLA is in breach and requires immediate corrective action. '
      }
    }
    
    if (findings.length > 0) {
      summaryContent += `A total of ${findings.length} finding${findings.length > 1 ? 's were' : ' was'} documented during this audit. `
    }
    
    summaryContent += `This report provides a comprehensive analysis of the SLA performance, metrics comparison, and detailed audit findings for management review and action.`
    
    const summaryLines = pdf.splitTextToSize(summaryContent, 170)
    pdf.text(summaryLines, 25, yPosition)
    yPosition += (summaryLines.length * 5) + 10
    
    // Recommendations section
    pdf.setFont('helvetica', 'bold')
    pdf.text('Recommended Actions:', 25, yPosition)
    yPosition += 6
    
    pdf.setFont('helvetica', 'normal')
    const recommendations = []
    
    if (performanceData && performanceData.overview) {
      if (performanceData.overview.metrics_in_breach > 0) {
        recommendations.push('Address the metrics in breach with immediate corrective action plans')
      }
      if (performanceData.overview.vendors_at_risk > 0) {
        recommendations.push('Review vendor performance for those identified as at-risk')
      }
    }
    
    if (findings.length > 0) {
      recommendations.push('Review and implement recommendations from audit findings')
      recommendations.push('Schedule follow-up audit to verify corrective actions')
    }
    
    if (recommendations.length === 0) {
      recommendations.push('Continue monitoring SLA performance')
      recommendations.push('Maintain current performance standards')
    }
    
    recommendations.forEach((rec, index) => {
      const recText = `${index + 1}. ${rec}`
      const recLines = pdf.splitTextToSize(recText, 165)
      pdf.text(recLines, 30, yPosition)
      yPosition += (recLines.length * 5) + 3
    })
    
    // ============================================
    // FOOTER ON ALL PAGES
    // ============================================
    pdf.setTextColor(0, 0, 0)
    const pageCount = pdf.internal.getNumberOfPages()
    for (let i = 1; i <= pageCount; i++) {
      pdf.setPage(i)
      pdf.setFontSize(8)
      pdf.setFont('helvetica', 'normal')
      pdf.setDrawColor(200, 200, 200)
      pdf.line(20, 282, 190, 282)
      pdf.text(`Generated on: ${new Date().toLocaleDateString()} ${new Date().toLocaleTimeString()}`, 20, 287)
      pdf.text(`Audit ID: ${audit.audit_id}`, 105, 287, { align: 'center' })
      pdf.text(`Page ${i} of ${pageCount}`, 190, 287, { align: 'right' })
    }
    
    // Download the PDF
    const fileName = `Audit_Report_${audit.audit_id}_${audit.title.replace(/[^a-zA-Z0-9]/g, '_')}.pdf`
    pdf.save(fileName)
    
    // Show success notification
    await showSuccess('Report Downloaded', `Audit report for "${audit.title}" has been downloaded successfully!`, {
      audit_id: audit.audit_id,
      audit_title: audit.title,
      action: 'report_downloaded'
    })
    
    PopupService.success(`Audit report for "${audit.title}" has been downloaded successfully!`, 'Report Downloaded')
    
  } catch (error) {
    console.error('Error generating audit report:', error)
    
    // Show error notification
    await showError('Report Generation Failed', 'Error generating audit report. Please try again.', {
      audit_id: audit.audit_id,
      audit_title: audit.title,
      action: 'report_generation_failed',
      error_message: error.message
    })
    
    PopupService.error('Error generating audit report. Please try again.', 'Generation Failed')
  } finally {
    loading.value = false
  }
}

const exportReport = async () => {
  await showWarning('Feature Not Implemented', 'Report export functionality would be implemented here', {
    action: 'feature_not_implemented',
    feature: 'report_export'
  })
  PopupService.warning('Report export functionality would be implemented here', 'Feature Not Implemented')
}

const navigateToCreate = () => {
  router.push('/audit/create')
}

const viewAuditDetails = (auditId) => {
  router.push(`/audit/${auditId}`)
}
</script>
