<template>
  <div class="space-y-4 lg:space-y-6 p-4 lg:p-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="text-2xl lg:text-3xl font-bold tracking-tight text-foreground">Audit Reports</h1>
        <p class="text-sm lg:text-base text-muted-foreground">Comprehensive audit analytics and reporting dashboard (Admin View)</p>
      </div>
      <div class="flex flex-col sm:flex-row gap-2">
        <Button variant="outline" @click="navigateToAllAudits" class="w-full sm:w-auto">
          <FileText class="mr-2 h-4 w-4" />
          Back to My Audits
        </Button>
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
            <Label for="contract-filter">Contract</Label>
            <select 
              id="contract-filter"
              v-model="selectedContract" 
              @change="handleContractFilter"
              class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <option value="all">All Contracts</option>
              <option v-for="contract in availableContracts" :key="contract.contract_id" :value="contract.contract_id">
                {{ contract.contract_title }}
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
                  <span>Contract: {{ audit.contract_title || 'N/A' }}</span>
                  <span>Auditor: {{ audit.auditor_name || 'N/A' }}</span>
                  <span>Completed: {{ audit.completion_date ? new Date(audit.completion_date).toLocaleDateString() : 'N/A' }}</span>
                </div>
              </div>
              <div class="flex items-center gap-2 ml-4">
                <Badge variant="default" class="bg-green-600 text-white">
                  Completed
                </Badge>
                <Button
                  @click="testFindingsAPI(audit.audit_id)"
                  :disabled="loading"
                  variant="outline"
                  size="sm"
                  class="flex items-center gap-2"
                >
                  <Eye class="h-4 w-4" />
                  Test Findings
                </Button>
                <Button
                  v-if="getStoredReport(audit.audit_id)"
                  @click="viewStoredReport(audit.audit_id)"
                  :disabled="loading"
                  variant="outline"
                  size="sm"
                  class="flex items-center gap-2"
                >
                  <ExternalLink class="h-4 w-4" />
                  View Report
                </Button>
                <Button
                  v-else
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
            <div class="col-span-2">Contract</div>
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
            
            <!-- Contract -->
            <div class="col-span-2">
              <div class="text-sm text-foreground">{{ audit.contract_title || 'N/A' }}</div>
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
                  @click="testFindingsAPI(audit.audit_id)"
                  :disabled="loading"
                  variant="outline"
                  size="sm"
                  class="flex items-center gap-1"
                >
                  <Eye class="h-3 w-3" />
                  Test
                </Button>
                <Button
                  v-if="getStoredReport(audit.audit_id)"
                  @click="viewStoredReport(audit.audit_id)"
                  :disabled="loading"
                  variant="outline"
                  size="sm"
                  class="flex items-center gap-1"
                >
                  <ExternalLink class="h-3 w-3" />
                  View
                </Button>
                <Button
                  v-else
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
  ExternalLink,
  Grid3X3,
  List,
  Eye,
  Edit,
  Trash2
} from 'lucide-vue-next'
import jsPDF from 'jspdf'
import contractAuditApi from '@/services/contractAuditApi.js'
import loggingService from '@/services/loggingService'
import { PopupService } from '@/popup/popupService'
import { 
  Card, CardHeader, CardTitle, CardDescription, CardContent, Button, Badge, Label
} from '@/components/ui_contract'

const router = useRouter()

// API data
const allAudits = ref([])
const availableContracts = ref([])
const availableUsers = ref([])
const auditFindings = ref([])
const staticQuestionnaires = ref([])
const auditReports = ref([])
const loading = ref(true)

// Filter state
const selectedDateRange = ref('all')
const selectedStatus = ref('all')
const selectedContract = ref('all')
const selectedAuditor = ref('all')

// View state
const viewMode = ref('grid') // 'grid' or 'list'

// Load data from API
const loadReportsData = async () => {
  try {
    loading.value = true
    
    // Load audits
    const auditsResponse = await contractAuditApi.getContractAudits()
    if (auditsResponse.success) {
      allAudits.value = auditsResponse.data.results || auditsResponse.data || []
      console.log('✅ Loaded audits from API:', allAudits.value.length, 'audits')
      
      // Debug: Check if completion_date is present in completed audits
      const completedWithDate = allAudits.value.filter(a => a.status === 'completed' && a.completion_date)
      const completedWithoutDate = allAudits.value.filter(a => a.status === 'completed' && !a.completion_date)
      console.log(`📊 Completed audits: ${completedWithDate.length} with completion_date, ${completedWithoutDate.length} without`)
      
      if (allAudits.value.length > 0) {
        console.log('📋 Sample audit data:', {
          audit_id: allAudits.value[0].audit_id,
          title: allAudits.value[0].title,
          completion_date: allAudits.value[0].completion_date,
          contract_title: allAudits.value[0].contract_title,
          auditor_name: allAudits.value[0].auditor_name,
          status: allAudits.value[0].status
        })
      }
    } else {
      console.error('Error loading audits:', auditsResponse.error)
      allAudits.value = []
    }
    
    // Load Contracts
    const contractsResponse = await contractAuditApi.getAvailableContracts()
    if (contractsResponse.success) {
      availableContracts.value = contractsResponse.data || []
    } else {
      console.error('Error loading contracts:', contractsResponse.error)
      availableContracts.value = []
    }
    
    // Load users
    const usersResponse = await contractAuditApi.getAvailableUsers()
    if (usersResponse.success) {
      availableUsers.value = usersResponse.data || []
    } else {
      console.error('Error loading users:', usersResponse.error)
      availableUsers.value = []
    }
    
    // Load static questionnaires
    const questionnairesResponse = await contractAuditApi.getContractAuditQuestionnaires()
    if (questionnairesResponse.success) {
      staticQuestionnaires.value = questionnairesResponse.data.results || questionnairesResponse.data || []
    } else {
      console.error('Error loading questionnaires:', questionnairesResponse.error)
      staticQuestionnaires.value = []
    }
    
    // Load stored audit reports
    const reportsResponse = await contractAuditApi.getContractAuditReports()
    if (reportsResponse.success) {
      const reportData = reportsResponse.data?.data || reportsResponse.data?.results || reportsResponse.data || []
      auditReports.value = Array.isArray(reportData) ? reportData : []
    } else {
      console.error('Error loading stored audit reports:', reportsResponse.error)
      auditReports.value = []
    }

  } catch (error) {
    console.error('Error loading reports data:', error)
    allAudits.value = []
    availableContracts.value = []
    availableUsers.value = []
    staticQuestionnaires.value = []
  } finally {
    loading.value = false
  }
}

// Computed properties
const auditors = computed(() => {
  if (!Array.isArray(availableUsers.value)) return []
  return availableUsers.value.filter(user => user.role === 'auditor')
})

const completedAudits = computed(() => {
  if (!Array.isArray(filteredAudits.value)) return []
  return filteredAudits.value.filter(audit => audit.status === 'completed')
})

const filteredAudits = computed(() => {
  if (!Array.isArray(allAudits.value)) return []
  
  let audits = allAudits.value

  // Filter by status
  if (selectedStatus.value !== 'all') {
    audits = audits.filter(audit => audit.status === selectedStatus.value)
  }

  // Filter by Contract
  if (selectedContract.value !== 'all') {
    audits = audits.filter(audit => audit.contract_id === parseInt(selectedContract.value))
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

const reportsByAuditId = computed(() => {
  const map = {}
  if (Array.isArray(auditReports.value)) {
    auditReports.value.forEach(report => {
      if (report && report.audit_id != null) {
        map[report.audit_id] = report
      }
    })
  }
  return map
})


// Event handlers
const handleDateRangeChange = () => {
  // Implement date filtering logic
  console.log('Date range changed:', selectedDateRange.value)
}

const handleStatusFilter = () => {
  console.log('Status filter changed:', selectedStatus.value)
}

const handleContractFilter = () => {
  console.log('Contract filter changed:', selectedContract.value)
}

const handleAuditorFilter = () => {
  console.log('Auditor filter changed:', selectedAuditor.value)
}

const getStoredReport = (auditId) => {
  if (!auditId) return null
  return reportsByAuditId.value[auditId] || null
}

const viewStoredReport = (auditId) => {
  const storedReport = getStoredReport(auditId)
  if (storedReport?.report_link) {
    window.open(storedReport.report_link, '_blank')
  } else {
    PopupService.warning('No stored report link available for this audit yet.', 'Report Not Available')
  }
}

// Load data on component mount
onMounted(async () => {
  await loggingService.logPageView('Contract', 'Contract Audit Reports')
  await loadReportsData()
})

// PDF Generation Functions
const generateAuditReport = async (audit) => {
  try {
    loading.value = true
    
    console.log('📄 Generating PDF report for audit:', {
      audit_id: audit.audit_id,
      title: audit.title,
      completion_date: audit.completion_date,
      contract_title: audit.contract_title,
      auditor_name: audit.auditor_name,
      status: audit.status
    })
    
    // Load audit findings for this specific audit
    console.log('🔍 Loading audit findings for audit ID:', audit.audit_id)
    const findingsResponse = await contractAuditApi.getContractAuditFindings({ audit_id: audit.audit_id })
    console.log('📊 Findings API response:', findingsResponse)
    
    let findings = []
    if (findingsResponse.success) {
      // Handle different response structures
      if (Array.isArray(findingsResponse.data)) {
        findings = findingsResponse.data
      } else if (findingsResponse.data && Array.isArray(findingsResponse.data.results)) {
        findings = findingsResponse.data.results
      } else if (findingsResponse.data && Array.isArray(findingsResponse.data.data)) {
        findings = findingsResponse.data.data
      }
    } else {
      console.error('❌ Error loading audit findings:', findingsResponse.error)
    }
    
    console.log('📋 Final findings array:', findings)
    console.log('📋 Findings count:', findings.length)
    
    // Create PDF document with professional settings
    const pdf = new jsPDF('p', 'mm', 'a4')
    const pageWidth = pdf.internal.pageSize.getWidth()
    const pageHeight = pdf.internal.pageSize.getHeight()
    const margin = 20
    const contentWidth = pageWidth - (margin * 2)
    let yPosition = 20
    
    // Color scheme
    const primaryColor = [37, 99, 235] // Blue
    const secondaryColor = [107, 114, 128] // Gray
    const successColor = [34, 197, 94] // Green
    const headerBgColor = [249, 250, 251] // Light gray
    const borderColor = [229, 231, 235] // Border gray
    
    // Helper function to add page footer
    const addFooter = (pageNum, totalPages) => {
      const footerY = pageHeight - 15
      pdf.setDrawColor(...borderColor)
      pdf.setLineWidth(0.5)
      pdf.line(margin, footerY, pageWidth - margin, footerY)
      
      pdf.setFontSize(8)
      pdf.setTextColor(...secondaryColor)
      pdf.setFont('helvetica', 'normal')
      pdf.text(`Generated on ${new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}`, margin, footerY + 5)
      pdf.text(`Page ${pageNum} of ${totalPages}`, pageWidth - margin, footerY + 5, { align: 'right' })
    }
    
    // Helper function to check and add new page
    const checkNewPage = (requiredSpace = 20) => {
      if (yPosition + requiredSpace > pageHeight - 30) {
        const currentPage = pdf.getNumberOfPages()
        addFooter(currentPage, currentPage)
        pdf.addPage()
        yPosition = 20
        return true
      }
      return false
    }
    
    // Helper function to add section header
    const addSectionHeader = (title, y) => {
      // Background bar
      pdf.setFillColor(...headerBgColor)
      pdf.rect(margin, y - 5, contentWidth, 8, 'F')
      
      // Colored accent line
      pdf.setFillColor(...primaryColor)
      pdf.rect(margin, y - 5, 3, 8, 'F')
      
      // Title
      pdf.setFontSize(14)
      pdf.setTextColor(...primaryColor)
      pdf.setFont('helvetica', 'bold')
      pdf.text(title, margin + 8, y + 1)
      
      // Reset text color
      pdf.setTextColor(0, 0, 0)
      
      return y + 10
    }
    
    // Helper function to add info table row
    const addInfoRow = (label, value, y, isMultiline = false) => {
      const labelWidth = contentWidth * 0.35
      const valueWidth = contentWidth * 0.65
      const rowHeight = isMultiline ? 12 : 8
      
      checkNewPage(rowHeight + 5)
      
      // Label background
      pdf.setFillColor(...headerBgColor)
      pdf.rect(margin, y - 4, labelWidth, rowHeight, 'F')
      
      // Borders
      pdf.setDrawColor(...borderColor)
      pdf.setLineWidth(0.3)
      pdf.rect(margin, y - 4, labelWidth, rowHeight)
      pdf.rect(margin + labelWidth, y - 4, valueWidth, rowHeight)
      
      // Label text
      pdf.setFontSize(9)
      pdf.setTextColor(75, 85, 99) // gray-600
      pdf.setFont('helvetica', 'bold')
      pdf.text(label, margin + 3, y + 2)
      
      // Value text
      pdf.setFontSize(9)
      pdf.setTextColor(0, 0, 0)
      pdf.setFont('helvetica', 'normal')
      
      if (isMultiline && value) {
        const valueLines = pdf.splitTextToSize(value || 'N/A', valueWidth - 6)
        const actualHeight = Math.max(rowHeight, valueLines.length * 4 + 4)
        pdf.rect(margin + labelWidth, y - 4, valueWidth, actualHeight)
        pdf.text(valueLines, margin + labelWidth + 3, y + 2)
        return y + actualHeight + 3
      } else {
        pdf.text(value || 'N/A', margin + labelWidth + 3, y + 2)
        return y + rowHeight + 3
      }
    }
    
    // ========== COVER PAGE ==========
    // Header with colored bar
    pdf.setFillColor(...primaryColor)
    pdf.rect(0, 0, pageWidth, 50, 'F')
    
    // Company/System name
    pdf.setFontSize(24)
    pdf.setTextColor(255, 255, 255)
    pdf.setFont('helvetica', 'bold')
    pdf.text('AUDIT REPORT', pageWidth / 2, 25, { align: 'center' })
    
    pdf.setFontSize(12)
    pdf.setFont('helvetica', 'normal')
    pdf.text('Contract Compliance Audit', pageWidth / 2, 35, { align: 'center' })
    
    yPosition = 70
    
    // Report title
    pdf.setFontSize(18)
    pdf.setTextColor(0, 0, 0)
    pdf.setFont('helvetica', 'bold')
    pdf.text(audit.title || 'Contract Audit', pageWidth / 2, yPosition, { align: 'center' })
    yPosition += 20
    
    // Report metadata box
    const boxY = yPosition
    pdf.setFillColor(255, 255, 255)
    pdf.setDrawColor(...borderColor)
    pdf.setLineWidth(0.5)
    pdf.roundedRect(margin, boxY, contentWidth, 60, 3, 3, 'FD')
    
    yPosition += 10
    yPosition = addInfoRow('Audit ID', `#${audit.audit_id}`, yPosition)
    yPosition = addInfoRow('Contract', audit.contract_title || 'N/A', yPosition)
    yPosition = addInfoRow('Auditor', audit.auditor_name || 'N/A', yPosition)
    yPosition = addInfoRow('Status', audit.status?.toUpperCase() || 'N/A', yPosition)
    
    const completionDateText = audit.completion_date 
      ? new Date(audit.completion_date).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
      : 'N/A'
    yPosition = addInfoRow('Completion Date', completionDateText, yPosition)
    
    const dueDateText = audit.due_date 
      ? new Date(audit.due_date).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
      : 'N/A'
    yPosition = addInfoRow('Due Date', dueDateText, yPosition)
    
    yPosition += 20
    
    // Executive Summary
    yPosition = addSectionHeader('Executive Summary', yPosition)
    
    pdf.setFontSize(10)
    pdf.setTextColor(0, 0, 0)
    pdf.setFont('helvetica', 'normal')
    
    const summaryText = `This audit report presents a comprehensive review of the contract compliance audit conducted for ${audit.contract_title || 'the specified contract'}. The audit was completed on ${completionDateText} and includes ${findings.length} finding(s) across various contract terms and compliance requirements.`
    
    const summaryLines = pdf.splitTextToSize(summaryText, contentWidth)
    pdf.text(summaryLines, margin, yPosition)
    yPosition += summaryLines.length * 5 + 10
    
    // Summary statistics box
    pdf.setFillColor(...headerBgColor)
    pdf.setDrawColor(...borderColor)
    pdf.roundedRect(margin, yPosition, contentWidth, 25, 3, 3, 'FD')
    
    yPosition += 8
    pdf.setFontSize(10)
    pdf.setFont('helvetica', 'bold')
    pdf.text('Summary Statistics', margin + 5, yPosition)
    yPosition += 8
    
    pdf.setFontSize(9)
    pdf.setFont('helvetica', 'normal')
    pdf.text(`Total Findings: ${findings.length}`, margin + 5, yPosition)
    pdf.text(`Contract: ${audit.contract_title || 'N/A'}`, margin + contentWidth / 2, yPosition)
    yPosition += 15
    
    // Add footer to first page
    addFooter(1, 1)
    
    // ========== AUDIT FINDINGS SECTION ==========
    if (findings.length > 0) {
      pdf.addPage()
      yPosition = 20
      
      yPosition = addSectionHeader('Detailed Audit Findings', yPosition)
      yPosition += 5
      
      findings.forEach((finding, index) => {
        checkNewPage(80)
        
        // Finding header box
        pdf.setFillColor(...primaryColor)
        pdf.roundedRect(margin, yPosition - 5, contentWidth, 8, 2, 2, 'F')
        
        pdf.setFontSize(12)
        pdf.setTextColor(255, 255, 255)
        pdf.setFont('helvetica', 'bold')
        pdf.text(`Finding ${index + 1}`, margin + 5, yPosition + 1)
        
        yPosition += 12
        
        // Finding details in table format
        if (finding.term_id) {
          yPosition = addInfoRow('Term ID', finding.term_id, yPosition)
        }
        
        if (finding.term_title) {
          yPosition = addInfoRow('Term Title', finding.term_title, yPosition, true)
        }
        
        if (finding.term_category) {
          yPosition = addInfoRow('Term Category', finding.term_category, yPosition)
        }
        
        if (finding.term_text) {
          yPosition = addInfoRow('Term Text', finding.term_text, yPosition, true)
        }
        
        if (finding.evidence) {
          yPosition = addInfoRow('Evidence', finding.evidence, yPosition, true)
        }
        
        if (finding.how_to_verify) {
          yPosition = addInfoRow('Verification Method', finding.how_to_verify, yPosition, true)
        }
        
        if (finding.impact_recommendations) {
          yPosition = addInfoRow('Recommendations', finding.impact_recommendations, yPosition, true)
        }
        
        if (finding.details_of_finding) {
          yPosition = addInfoRow('Details', finding.details_of_finding, yPosition, true)
        }
        
        // Questionnaire Responses Section
        if (finding.questionnaire_responses || finding.questionnaire_responses_with_questions) {
          checkNewPage(30)
          
          pdf.setFontSize(10)
          pdf.setFont('helvetica', 'bold')
          pdf.setTextColor(...primaryColor)
          pdf.text('Questionnaire Responses', margin, yPosition)
          yPosition += 8
          
          try {
            let responses = finding.questionnaire_responses_with_questions
            
            if (!responses && finding.questionnaire_responses) {
              responses = typeof finding.questionnaire_responses === 'string' 
                ? JSON.parse(finding.questionnaire_responses) 
                : finding.questionnaire_responses
            }
            
            if (responses && Object.keys(responses).length > 0) {
              // Create a table for responses
              const responseEntries = Object.entries(responses)
              
              responseEntries.forEach(([questionId, responseData], qIndex) => {
                // Calculate content height first
                let questionText = ''
                let answerText = ''
                let questionLines = []
                let questionHeight = 0
                let answerHeight = 0
                const indent = 5 // Indentation for answer alignment
                
                pdf.setFontSize(9)
                pdf.setFont('helvetica', 'normal')
                
                if (responseData && typeof responseData === 'object' && responseData.question_text) {
                  questionText = `Q${questionId}: ${responseData.question_text}`
                  answerText = responseData.answer || ''
                  questionLines = pdf.splitTextToSize(questionText, contentWidth)
                  questionHeight = questionLines.length * 3.5
                  if (answerText) {
                    // Calculate answer height for multiline answers
                    const answerLines = pdf.splitTextToSize(`Answer: ${answerText}`, contentWidth - indent)
                    answerHeight = answerLines.length * 3.5
                  }
                } else {
                  questionText = `Q${questionId}: ${responseData}`
                  questionLines = pdf.splitTextToSize(questionText, contentWidth)
                  questionHeight = questionLines.length * 3.5
                }
                
                const totalHeight = questionHeight + answerHeight + (answerText ? 2 : 0)
                
                checkNewPage(totalHeight + 2)
                
                // Draw question
                pdf.setTextColor(0, 0, 0)
                pdf.setFont('helvetica', 'normal')
                pdf.text(questionLines, margin, yPosition)
                
                // Draw answer with proper indentation and alignment
                if (answerText) {
                  const answerY = yPosition + questionHeight + 2
                  pdf.setFont('helvetica', 'bold')
                  pdf.setTextColor(...primaryColor)
                  
                  // Handle multiline answers
                  const answerLines = pdf.splitTextToSize(`Answer: ${answerText}`, contentWidth - indent)
                  pdf.text(answerLines, margin + indent, answerY)
                  answerHeight = answerLines.length * 3.5
                }
                
                // Move to next response with spacing
                yPosition += totalHeight + 5
              })
            }
          } catch (error) {
            console.error('Error parsing questionnaire responses:', error)
            pdf.setFontSize(9)
            pdf.setFont('helvetica', 'normal')
            pdf.setTextColor(239, 68, 68) // Red for error
            pdf.text('Error parsing questionnaire responses', margin, yPosition)
            yPosition += 6
          }
        }
        
        // Add spacing before comments section
        if (finding.comment && (finding.questionnaire_responses || finding.questionnaire_responses_with_questions)) {
          yPosition += 8
        }
        
        // Comments section (after questionnaire responses)
        if (finding.comment) {
          yPosition = addInfoRow('Comments', finding.comment, yPosition, true)
        }
        
        yPosition += 10
        
        // Divider line between findings
        if (index < findings.length - 1) {
          pdf.setDrawColor(...borderColor)
          pdf.setLineWidth(0.5)
          pdf.line(margin, yPosition, pageWidth - margin, yPosition)
          yPosition += 5
        }
      })
    } else {
      pdf.addPage()
      yPosition = 20
      yPosition = addSectionHeader('Detailed Audit Findings', yPosition)
      yPosition += 10
      
      pdf.setFontSize(11)
      pdf.setTextColor(...secondaryColor)
      pdf.setFont('helvetica', 'italic')
      pdf.text('No audit findings available for this audit.', margin, yPosition)
    }
    
    // Add footer to last page
    const totalPages = pdf.getNumberOfPages()
    addFooter(totalPages, totalPages)
    
    // Download the PDF
    const fileName = `Audit_Report_${audit.audit_id}_${audit.title.replace(/[^a-zA-Z0-9]/g, '_')}.pdf`
    
    // Persist report in backend/S3 before saving locally
    try {
      const contractIdForReport = audit.contract_id || audit.contract?.contract_id || audit.contract || null
      const termIdForReport = audit.term_id || null
      const dataUriString = pdf.output('datauristring')
      
      const uploadPayload = {
        audit_id: audit.audit_id,
        contract_id: contractIdForReport,
        term_id: termIdForReport,
        file_name: fileName,
        file_data: dataUriString
      }
      
      const uploadResponse = await contractAuditApi.uploadAuditReport(uploadPayload)
      if (uploadResponse.success) {
        console.log('✅ Audit report stored in S3 and recorded:', uploadResponse.data)
        const storedReport = uploadResponse.data?.report
        if (storedReport) {
          auditReports.value = [
            ...auditReports.value.filter(r => r.report_id !== storedReport.report_id),
            storedReport
          ]
        }
      } else {
        console.error('❌ Failed to upload audit report:', uploadResponse.error)
        PopupService.warning(
          'Report downloaded locally but storing the report link failed. Please retry later.',
          'Report Storage Warning'
        )
      }
    } catch (uploadError) {
      console.error('❌ Error uploading audit report:', uploadError)
      PopupService.warning(
        'Could not persist the audit report in S3. Local download will continue.',
        'Report Storage Error'
      )
    }
    
    pdf.save(fileName)
    
    PopupService.success(`Professional audit report for "${audit.title}" has been downloaded successfully!`, 'Report Downloaded')
    
  } catch (error) {
    console.error('Error generating audit report:', error)
    PopupService.error('Error generating audit report. Please try again.', 'Generation Error')
  } finally {
    loading.value = false
  }
}

const exportReport = () => {
  PopupService.success('Report export functionality would be implemented here', 'Export')
}

const navigateToCreate = () => {
  router.push('/contract-audit/create')
}

const navigateToAllAudits = () => {
  router.push('/contract-audit/all')
}

const viewAuditDetails = (auditId) => {
  router.push(`/contract-audit/${auditId}`)
}

// Test function to debug findings API
const testFindingsAPI = async (auditId) => {
  try {
    console.log('🧪 Testing findings API for audit ID:', auditId)
    
    const findingsResponse = await contractAuditApi.getContractAuditFindings({ audit_id: auditId })
    console.log('🧪 Raw API response:', findingsResponse)
    
    let findings = []
    if (findingsResponse.success) {
      if (Array.isArray(findingsResponse.data)) {
        findings = findingsResponse.data
      } else if (findingsResponse.data && Array.isArray(findingsResponse.data.results)) {
        findings = findingsResponse.data.results
      } else if (findingsResponse.data && Array.isArray(findingsResponse.data.data)) {
        findings = findingsResponse.data.data
      }
    }
    
    console.log('🧪 Processed findings:', findings)
    console.log('🧪 Findings count:', findings.length)
    
    if (findings.length > 0) {
      const findingsSummary = findings.map(f => {
        const termLabel = f.term_title || f.term_id || 'Unknown Term'
        let summary = `- ${termLabel}: ${f.evidence?.substring(0, 50) || ''}...`
        
        if (f.term_category) {
          summary += `\n  Category: ${f.term_category}`
        }
        
        // Add questionnaire responses info
        if (f.questionnaire_responses || f.questionnaire_responses_with_questions) {
          try {
            let responses = f.questionnaire_responses_with_questions || f.questionnaire_responses
            if (typeof responses === 'string') {
              responses = JSON.parse(responses)
            }
            summary += `\n  Responses: ${Object.keys(responses).length} questions answered`
            
            // Show a sample response
            const firstResponse = Object.entries(responses)[0]
            if (firstResponse) {
              const [questionId, responseData] = firstResponse
              if (responseData && typeof responseData === 'object' && responseData.question_text) {
                summary += `\n  Sample: ${responseData.question_text.substring(0, 30)}... = ${responseData.answer}`
              } else {
                summary += `\n  Sample: Q${questionId} = ${responseData}`
              }
            }
          } catch (error) {
            summary += `\n  Responses: Error parsing`
          }
        }
        
        return summary
      }).join('\n')
      
      PopupService.success(`Found ${findings.length} audit findings for audit ${auditId}:\n\n${findingsSummary}`, 'Findings Found')
    } else {
      PopupService.warning(`No audit findings found for audit ${auditId}. Check console for details.`, 'No Findings')
    }
    
  } catch (error) {
    console.error('🧪 Error testing findings API:', error)
    PopupService.error(`Error testing findings API: ${error.message}`, 'API Error')
  }
}
</script>
