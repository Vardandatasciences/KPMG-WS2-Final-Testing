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
    
    // Create PDF document
    const pdf = new jsPDF()
    let yPosition = 20
    
    // Header
    pdf.setFontSize(20)
    pdf.setFont('helvetica', 'bold')
    pdf.text('AUDIT REPORT', 105, yPosition, { align: 'center' })
    yPosition += 20
    
    // Audit Information
    pdf.setFontSize(14)
    pdf.setFont('helvetica', 'bold')
    pdf.text('Audit Information', 20, yPosition)
    yPosition += 15
    
    pdf.setFontSize(10)
    pdf.setFont('helvetica', 'normal')
    pdf.text(`Audit ID: ${audit.audit_id}`, 20, yPosition)
    yPosition += 8
    pdf.text(`Title: ${audit.title}`, 20, yPosition)
    yPosition += 8
    pdf.text(`Contract: ${audit.contract_title || 'N/A'}`, 20, yPosition)
    yPosition += 8
    pdf.text(`Auditor: ${audit.auditor_name || 'N/A'}`, 20, yPosition)
    yPosition += 8
    pdf.text(`Status: ${audit.status}`, 20, yPosition)
    yPosition += 8
    
    // Format completion date properly
    const completionDateText = audit.completion_date 
      ? new Date(audit.completion_date).toLocaleDateString() 
      : 'N/A'
    pdf.text(`Completion Date: ${completionDateText}`, 20, yPosition)
    yPosition += 8
    
    // Add due date as well
    const dueDateText = audit.due_date 
      ? new Date(audit.due_date).toLocaleDateString() 
      : 'N/A'
    pdf.text(`Due Date: ${dueDateText}`, 20, yPosition)
    yPosition += 15
    
    // Audit Findings
    console.log('📄 Generating PDF findings section with', findings.length, 'findings')
    if (findings.length > 0) {
      console.log('✅ Found findings, adding to PDF:', findings)
      pdf.setFontSize(14)
      pdf.setFont('helvetica', 'bold')
      pdf.text('Audit Findings', 20, yPosition)
      yPosition += 15
      
      findings.forEach((finding, index) => {
        if (yPosition > 250) {
          pdf.addPage()
          yPosition = 20
        }
        
        pdf.setFontSize(12)
        pdf.setFont('helvetica', 'bold')
        pdf.text(`Finding ${index + 1}:`, 20, yPosition)
        yPosition += 10
        
        pdf.setFontSize(10)
        pdf.setFont('helvetica', 'normal')
        
        // Evidence
        if (finding.evidence) {
          pdf.text('Evidence:', 25, yPosition)
          yPosition += 8
          const evidenceLines = pdf.splitTextToSize(finding.evidence, 160)
          pdf.text(evidenceLines, 30, yPosition)
          yPosition += evidenceLines.length * 4 + 5
        }
        
        // Verification Method
        if (finding.how_to_verify) {
          pdf.text('Verification Method:', 25, yPosition)
          yPosition += 8
          const verificationLines = pdf.splitTextToSize(finding.how_to_verify, 160)
          pdf.text(verificationLines, 30, yPosition)
          yPosition += verificationLines.length * 4 + 5
        }
        
        // Recommendations
        if (finding.impact_recommendations) {
          pdf.text('Recommendations:', 25, yPosition)
          yPosition += 8
          const recommendationLines = pdf.splitTextToSize(finding.impact_recommendations, 160)
          pdf.text(recommendationLines, 30, yPosition)
          yPosition += recommendationLines.length * 4 + 5
        }
        
        // Questionnaire Responses
        if (finding.questionnaire_responses || finding.questionnaire_responses_with_questions) {
          pdf.text('Questionnaire Responses:', 25, yPosition)
          yPosition += 8
          
          try {
            // Use enhanced responses if available, otherwise parse the raw responses
            let responses = finding.questionnaire_responses_with_questions
            
            if (!responses && finding.questionnaire_responses) {
              responses = typeof finding.questionnaire_responses === 'string' 
                ? JSON.parse(finding.questionnaire_responses) 
                : finding.questionnaire_responses
            }
            
            console.log('📋 Parsed questionnaire responses:', responses)
            
            // Display each response
            Object.entries(responses).forEach(([questionId, responseData]) => {
              if (yPosition > 250) {
                pdf.addPage()
                yPosition = 20
              }
              
              pdf.setFontSize(9)
              pdf.setFont('helvetica', 'normal')
              
              // Check if we have enhanced response data with question text
              if (responseData && typeof responseData === 'object' && responseData.question_text) {
                // Enhanced format with question text
                const questionText = responseData.question_text
                const answer = responseData.answer
                
                // Split long question text into multiple lines
                const questionLines = pdf.splitTextToSize(`Q${questionId}: ${questionText}`, 150)
                pdf.text(questionLines, 30, yPosition)
                yPosition += questionLines.length * 4 + 2
                
                // Add the answer
                pdf.setFont('helvetica', 'bold')
                pdf.text(`Answer: ${answer}`, 35, yPosition)
                yPosition += 6
              } else {
                // Simple format (question ID and answer)
                pdf.text(`Q${questionId}: ${responseData}`, 30, yPosition)
                yPosition += 6
              }
            })
          } catch (error) {
            console.error('Error parsing questionnaire responses:', error)
            pdf.setFontSize(9)
            pdf.setFont('helvetica', 'normal')
            pdf.text('Error parsing questionnaire responses', 30, yPosition)
            yPosition += 6
          }
          
          yPosition += 5
        }
        
        yPosition += 10
      })
    } else {
      console.log('❌ No findings found, adding "No findings" message to PDF')
      pdf.setFontSize(12)
      pdf.setFont('helvetica', 'normal')
      pdf.text('No audit findings available for this audit.', 20, yPosition)
    }
    
    // Footer
    pdf.setFontSize(8)
    pdf.setFont('helvetica', 'normal')
    pdf.text(`Generated on: ${new Date().toLocaleDateString()}`, 20, 280)
    pdf.text(`Page 1 of ${pdf.getNumberOfPages()}`, 170, 280)
    
    // Download the PDF
    const fileName = `Audit_Report_${audit.audit_id}_${audit.title.replace(/[^a-zA-Z0-9]/g, '_')}.pdf`
    pdf.save(fileName)
    
    PopupService.success(`Audit report for "${audit.title}" has been downloaded successfully!`, 'Report Downloaded')
    
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
        let summary = `- ${f.term_id}: ${f.evidence?.substring(0, 50)}...`
        
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
