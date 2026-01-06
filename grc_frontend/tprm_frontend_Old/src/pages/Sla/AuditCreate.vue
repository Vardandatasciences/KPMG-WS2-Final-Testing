<template>
  <div class="max-w-7xl mx-auto space-y-4 lg:space-y-6 p-4 lg:p-6">
    <!-- Header -->
    <div>
      <h1 class="text-2xl lg:text-3xl font-bold tracking-tight text-foreground">Create New Audit</h1>
      <p class="text-sm lg:text-base text-muted-foreground">Set up a new audit with SLA selection, assignee configuration, and custom questionnaires</p>
    </div>

    <!-- SLA Selection -->
    <Card class="shadow-card">
      <CardHeader>
        <CardTitle class="flex items-center">
          <FileText class="mr-2 h-5 w-5 text-primary" />
          SLA Selection
        </CardTitle>
        <CardDescription>Choose the Service Level Agreement to audit</CardDescription>
      </CardHeader>
      <CardContent class="p-4 lg:p-6">
        <div class="space-y-4">
          <div>
            <Label for="sla-select">Select SLA</Label>
            <select 
              id="sla-select"
              v-model="selectedSLAId" 
              @change="handleSLASelection"
              class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <option value="">Choose an SLA to audit</option>
              <option 
                v-for="sla in approvedSLAs" 
                :key="sla.sla_id" 
                :value="sla.sla_id"
              >
                {{ sla.sla_name }} - {{ sla.company_name }}
              </option>
            </select>
          </div>

          <div v-if="selectedSLA" class="p-3 lg:p-4 bg-muted/30 rounded-lg border">
            <h4 class="font-medium text-foreground mb-2 text-sm lg:text-base">Selected SLA Details</h4>
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-3 lg:gap-4 text-xs lg:text-sm">
              <div>
                <span class="text-muted-foreground">Title:</span>
                <span class="ml-2 font-medium">{{ selectedSLA.sla_name }}</span>
              </div>
              <div>
                <span class="text-muted-foreground">Type:</span>
                <Badge variant="outline" class="ml-2">{{ selectedSLA.sla_type }}</Badge>
              </div>
              <div>
                <span class="text-muted-foreground">Duration:</span>
                <span class="ml-2">{{ selectedSLA.effective_date }} to {{ selectedSLA.expiry_date }}</span>
              </div>
              <div>
                <span class="text-muted-foreground">Metrics:</span>
                <span class="ml-2 font-medium">{{ metrics.length }} metrics available</span>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- Audit Configuration -->
    <Card class="shadow-card">
      <CardHeader>
        <CardTitle class="flex items-center">
          <Target class="mr-2 h-5 w-5 text-primary" />
          Audit Configuration
        </CardTitle>
        <CardDescription>Configure basic audit parameters</CardDescription>
      </CardHeader>
      <CardContent class="p-4 lg:p-6">
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div>
            <Label for="audit-title">Audit Title *</Label>
            <Input
              id="audit-title"
              v-model="auditTitle"
              placeholder="Enter audit title"
            />
          </div>
          <div>
            <Label for="due-date">Due Date *</Label>
            <Input
              id="due-date"
              type="date"
              v-model="dueDate"
            />
          </div>
          <div>
            <Label for="frequency">Frequency</Label>
            <select 
              id="frequency"
              v-model="frequency"
              class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <option value="">Select frequency</option>
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
              <option value="quarterly">Quarterly</option>
              <option value="yearly">Yearly</option>
            </select>
          </div>
          <div>
            <Label for="audit-type">Audit Type</Label>
            <select 
              id="audit-type"
              v-model="auditType"
              class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <option value="">Select type</option>
              <option value="internal">Internal</option>
              <option value="external">External</option>
              <option value="self">Self Assessment</option>
            </select>
          </div>
          <div class="lg:col-span-2">
            <Label for="audit-scope">Audit Scope</Label>
            <Textarea
              id="audit-scope"
              v-model="auditScope"
              placeholder="Describe the scope and objectives of this audit"
              :rows="3"
            />
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- Assignee Selection -->
    <Card class="shadow-card">
      <CardHeader>
        <CardTitle class="flex items-center">
          <Users class="mr-2 h-5 w-5 text-primary" />
          Assignee Selection
        </CardTitle>
        <CardDescription>Assign auditor and reviewer for this audit (Admin can assign to any user)</CardDescription>
      </CardHeader>
      <CardContent class="p-4 lg:p-6">
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div>
            <Label for="auditor-select">Auditor *</Label>
            <select 
              id="auditor-select"
              v-model="selectedAuditorId" 
              @change="handleAuditorSelection"
              class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <option value="">Select auditor</option>
              <option 
                v-for="auditor in auditors" 
                :key="auditor.user_id" 
                :value="auditor.user_id"
              >
                {{ auditor.name }} ({{ auditor.email }})
              </option>
            </select>
          </div>
          <div>
            <Label for="reviewer-select">Reviewer *</Label>
            <select 
              id="reviewer-select"
              v-model="selectedReviewerId" 
              @change="handleReviewerSelection"
              class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <option value="">Select reviewer</option>
              <option 
                v-for="reviewer in reviewers" 
                :key="reviewer.user_id" 
                :value="reviewer.user_id"
              >
                {{ reviewer.name }} ({{ reviewer.email }})
              </option>
            </select>
          </div>
        </div>

        <div v-if="selectedAuditor || selectedReviewer" class="mt-4 p-3 lg:p-4 bg-muted/30 rounded-lg border">
          <h4 class="font-medium text-foreground mb-2 text-sm lg:text-base">Assignment Summary</h4>
          <div class="space-y-2 text-xs lg:text-sm">
            <div v-if="selectedAuditor" class="flex items-center">
              <span class="text-muted-foreground w-20">Auditor:</span>
              <span class="font-medium">{{ selectedAuditor.name }}</span>
              <span class="text-muted-foreground ml-2">({{ selectedAuditor.email }})</span>
            </div>
            <div v-if="selectedReviewer" class="flex items-center">
              <span class="text-muted-foreground w-20">Reviewer:</span>
              <span class="font-medium">{{ selectedReviewer.name }}</span>
              <span class="text-muted-foreground ml-2">({{ selectedReviewer.email }})</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- SLA Metrics Overview -->
    <Card v-if="selectedSLA && metrics.length > 0" class="shadow-card">
      <CardHeader>
        <CardTitle class="flex items-center">
          <Target class="mr-2 h-5 w-5 text-primary" />
          SLA Metrics Overview
        </CardTitle>
        <CardDescription>Review the metrics that will be audited for this SLA</CardDescription>
      </CardHeader>
      <CardContent class="p-4 lg:p-6">
        <div class="space-y-4">
          <div v-for="metric in metrics" :key="metric.metric_id" class="border border-border rounded-lg p-4">
            <div class="flex items-center justify-between mb-2">
              <h4 class="font-medium text-foreground">{{ metric.metric_name }}</h4>
              <Badge variant="outline" class="text-xs">{{ metric.frequency }}</Badge>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-muted-foreground">
              <div>
                <span class="font-medium">Target:</span> {{ metric.threshold }} {{ metric.measurement_unit }}
              </div>
              <div>
                <span class="font-medium">Measurement:</span> {{ metric.measurement_methodology || 'Standard measurement' }}
              </div>
            </div>
            <div v-if="metric.penalty" class="mt-2 text-sm">
              <span class="font-medium text-muted-foreground">Penalty Clause:</span>
              <p class="text-muted-foreground mt-1">{{ metric.penalty }}</p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- Submit -->
    <div class="flex flex-col sm:flex-row justify-end gap-3 sm:gap-4">
      <Button variant="outline" @click="navigateBack" class="w-full sm:w-auto">
        Cancel
      </Button>
      <Button 
        @click="handleSubmit"
        :disabled="loading"
        class="bg-gradient-to-r from-primary to-primary-glow hover:shadow-hover transition-all w-full sm:w-auto"
      >
        <Calendar class="mr-2 h-4 w-4" />
        {{ loading ? 'Creating...' : 'Create Audit' }}
      </Button>
    </div>
  </div>

  <!-- Popup Modal -->
  <PopupModal />
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { 
  FileText, 
  Target, 
  Users, 
  Calendar 
} from 'lucide-vue-next'
import apiService from '@/services/api.js'
import Card from '@/components/ui/card.vue'
import CardHeader from '@/components/ui/card-header.vue'
import CardTitle from '@/components/ui/card-title.vue'
import CardDescription from '@/components/ui/card-description.vue'
import CardContent from '@/components/ui/card-content.vue'
import Button from '@/components/ui/button.vue'
import Badge from '@/components/ui/badge.vue'
import Input from '@/components/ui/input.vue'
import Label from '@/components/ui/label.vue'
import Textarea from '@/components/ui/textarea.vue'
import Select from '@/components/ui/select.vue'
import PopupModal from '@/popup/PopupModal.vue'
import { PopupService } from '@/popup/popupService'
import { useNotifications } from '@/composables/useNotifications'
import loggingService from '@/services/loggingService'

// CustomQuestion interface removed for JavaScript compatibility

const router = useRouter()
const { showSuccess, showError, showWarning, showInfo } = useNotifications()

// Form state
const selectedSLAId = ref(null)
const selectedAuditorId = ref(null)
const selectedReviewerId = ref(null)
const auditTitle = ref('')
const auditScope = ref('')
const dueDate = ref('')
const frequency = ref('')
const auditType = ref('')

// SLA metrics state
const metrics = ref([])

// API data
const approvedSLAs = ref([])
const auditors = ref([])
const reviewers = ref([])
const loading = ref(false)

const selectedSLA = computed(() => 
  selectedSLAId.value ? approvedSLAs.value.find(sla => sla.sla_id === selectedSLAId.value) : null
)

const selectedAuditor = computed(() => 
  selectedAuditorId.value ? auditors.value.find(auditor => auditor.user_id === selectedAuditorId.value) : null
)

const selectedReviewer = computed(() => 
  selectedReviewerId.value ? reviewers.value.find(reviewer => reviewer.user_id === selectedReviewerId.value) : null
)

// Load data on component mount
const loadData = async () => {
  loading.value = true
  try {
    // Load available SLAs
    const slasData = await apiService.getAvailableSLAs()
    approvedSLAs.value = slasData

    // Load available users
    const usersData = await apiService.getAvailableUsers()
    auditors.value = usersData.filter(user => user.role === 'auditor')
    reviewers.value = usersData.filter(user => user.role === 'reviewer')
  } catch (error) {
    console.error('Error loading data:', error)
    
    // Show error notification
    await showError('Data Loading Failed', 'Failed to load audit creation data. Please refresh the page.', {
      action: 'data_loading_failed',
      error_message: error.message
    })
    
    PopupService.error('Error loading data. Please refresh the page.', 'Loading Error')
  } finally {
    loading.value = false
  }
}

// Load data when component mounts
loadData()

// Watch for SLA selection changes
watch(selectedSLA, async (newSLA) => {
  if (newSLA) {
    try {
      // Load SLA metrics from API
      const metricsData = await apiService.getSLAMetrics(newSLA.sla_id)
      console.log('SLA Metrics loaded:', metricsData)
      
      // Handle different response formats
      if (Array.isArray(metricsData)) {
        metrics.value = metricsData
      } else if (metricsData && metricsData.metrics && Array.isArray(metricsData.metrics)) {
        metrics.value = metricsData.metrics
      } else if (metricsData && metricsData.results && Array.isArray(metricsData.results)) {
        metrics.value = metricsData.results
      } else {
        metrics.value = []
      }
      
      console.log('Processed metrics:', metrics.value)
      
      // Set default audit title
      auditTitle.value = `${new Date().getFullYear()} ${newSLA.sla_name} Audit`
    } catch (error) {
      console.error('Error loading SLA metrics:', error)
      
      // Show error notification
      await showError('SLA Metrics Loading Failed', 'Failed to load SLA metrics. Please try again.', {
        sla_id: newSLA.sla_id,
        sla_name: newSLA.sla_name,
        action: 'metrics_loading_failed',
        error_message: error.message
      })
      
      PopupService.error('Error loading SLA metrics. Please try again.', 'Loading Error')
      metrics.value = []
    }
  } else {
    metrics.value = []
  }
})

// Event handlers
const handleSLASelection = (event) => {
  const target = event.target
  selectedSLAId.value = target.value ? parseInt(target.value) : null
}

const handleAuditorSelection = (event) => {
  const target = event.target
  selectedAuditorId.value = target.value ? parseInt(target.value) : null
}

const handleReviewerSelection = (event) => {
  const target = event.target
  selectedReviewerId.value = target.value ? parseInt(target.value) : null
}


const handleSubmit = async () => {
  // Validation
  if (!selectedSLA.value || !selectedAuditor.value || !selectedReviewer.value || !auditTitle.value || !dueDate.value) {
    await showWarning('Missing Required Fields', 'Please fill in all required fields before creating the audit.', {
      action: 'validation_failed',
      missing_fields: 'required fields'
    })
    PopupService.warning('Please fill in all required fields.', 'Missing Required Fields')
    return
  }

  if (selectedAuditor.value.user_id === selectedReviewer.value.user_id) {
    await showWarning('Invalid Selection', 'Auditor and Reviewer cannot be the same person.', {
      action: 'invalid_assignment',
      auditor_id: selectedAuditor.value.user_id,
      reviewer_id: selectedReviewer.value.user_id
    })
    PopupService.warning('Auditor and Reviewer cannot be the same person.', 'Invalid Selection')
    return
  }

  // Additional validation for SLA ID
  if (!selectedSLA.value.sla_id) {
    await showWarning('Invalid SLA', 'Invalid SLA selected. Please select a valid SLA.', {
      action: 'invalid_sla',
      sla_id: selectedSLA.value.sla_id
    })
    PopupService.warning('Invalid SLA selected. Please select a valid SLA.', 'Invalid SLA')
    return
  }

  console.log('Validation passed. SLA ID:', selectedSLA.value.sla_id, 'Auditor ID:', selectedAuditor.value.user_id)

  loading.value = true
  try {
    // Prepare audit data for API - ensure all required fields are included
    const auditData = {
      title: auditTitle.value,
      scope: auditScope.value,
      sla_id: parseInt(selectedSLA.value.sla_id), // Ensure it's an integer
      assignee_id: parseInt(selectedAuditor.value.user_id), // Set assignee_id to auditor_id
      auditor_id: parseInt(selectedAuditor.value.user_id),
      reviewer_id: parseInt(selectedReviewer.value.user_id),
      assign_date: new Date().toISOString().split('T')[0], // Set assign_date to today
      due_date: dueDate.value,
      frequency: frequency.value,
      audit_type: auditType.value,
      status: 'created', // Explicitly set status
      review_status: 'pending', // Explicitly set review_status
      // Include metrics information for reference
      metrics_count: metrics.value.length,
      metrics_info: metrics.value.map(metric => ({
        metric_id: metric.metric_id,
        metric_name: metric.metric_name,
        threshold: metric.threshold,
        measurement_unit: metric.measurement_unit
      }))
    }

    console.log('Creating audit with metrics:', auditData)
    console.log('SLA ID being sent:', selectedSLA.value.sla_id)
    console.log('Assignee ID being sent:', selectedAuditor.value.user_id)

    // Create audit via API
    const response = await apiService.createAudit(auditData)
    console.log('Audit creation response:', response)
    console.log('Response type:', typeof response)
    console.log('Response keys:', Object.keys(response || {}))
    
    // Check if the response contains the expected fields (handle different response formats)
    if (response && (response.audit_id || response.id || response.pk)) {
      const auditId = response.audit_id || response.id || response.pk
      console.log('Audit created successfully with ID:', auditId)
      console.log('Response SLA ID:', response.sla_id)
      console.log('Response Assignee ID:', response.assignee_id)
      
      // Check if sla_id was properly saved
      if (response.sla_id) {
        console.log('✅ SLA ID was saved successfully:', response.sla_id)
      } else {
        console.warn('⚠️ SLA ID was not returned in response - may not be saved')
      }
      
      // Show success notification
      await showSuccess('Audit Created Successfully', `Audit "${auditTitle.value}" has been created and assigned to ${selectedAuditor.value.name}.`, {
        audit_id: auditId,
        audit_title: auditTitle.value,
        sla_id: selectedSLA.value.sla_id,
        sla_name: selectedSLA.value.sla_name,
        auditor_id: selectedAuditor.value.user_id,
        auditor_name: selectedAuditor.value.name,
        action: 'audit_created'
      })
      
      PopupService.success(`Audit "${auditTitle.value}" has been created successfully and assigned to ${selectedAuditor.value.name}.`, 'Audit Created')
      PopupService.onAction('ok', () => {
        // Navigate to audit list or dashboard
        router.push('/audit/my-audits')
      })
    } else {
      console.error('Unexpected response format:', response)
      console.log('Response structure:', JSON.stringify(response, null, 2))
      
      // Show warning notification
      await showWarning('Unexpected Response', 'Audit created but with unexpected response format. Please check the audit list.', {
        audit_title: auditTitle.value,
        action: 'unexpected_response',
        response_data: response
      })
      
      PopupService.warning('Audit created but with unexpected response format. Please check the audit list.', 'Unexpected Response')
      PopupService.onAction('ok', () => {
        router.push('/audit/my-audits')
      })
    }
  } catch (error) {
    console.error('Error creating audit:', error)
    console.error('Error details:', error.response || error.message)
    
    // Show error notification
    await showError('Audit Creation Failed', 'Error creating audit. Please try again.', {
      audit_title: auditTitle.value,
      sla_id: selectedSLA.value.sla_id,
      action: 'audit_creation_failed',
      error_message: error.message
    })
    
    PopupService.error('Error creating audit. Please try again.', 'Creation Failed')
  } finally {
    loading.value = false
  }
}

const navigateBack = () => {
  router.go(-1)
}
</script>
