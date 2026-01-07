<template>
  <div v-if="!audit" class="flex items-center justify-center min-h-[400px] p-4">
    <Card class="w-full max-w-md text-center">
      <CardContent class="p-6">
        <AlertCircle class="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
        <h3 class="text-lg font-medium mb-2">Audit Not Found</h3>
        <p class="text-muted-foreground mb-4">The requested audit could not be found.</p>
        <Button @click="navigateToMyAudits">
          Back to My Audits
        </Button>
      </CardContent>
    </Card>
  </div>

  <div v-else class="max-w-7xl mx-auto space-y-4 lg:space-y-6 p-4 lg:p-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="text-2xl lg:text-3xl font-bold tracking-tight text-foreground">Review Audit</h1>
        <p class="text-sm lg:text-base text-muted-foreground">{{ audit.title }} 
          <span v-if="isAssignedReviewer">(Reviewer Access)</span>
          <span v-else>(View Only)</span>
        </p>
      </div>
      <div class="flex items-center space-x-2">
        <!-- Reviewer Badge -->
        <Badge v-if="isAssignedReviewer" variant="default" class="bg-blue-600 text-white">
          Reviewer Access
        </Badge>
        <Badge v-else variant="outline" class="bg-yellow-100 text-yellow-800">
          View Only
        </Badge>
        <Badge variant="outline" class="text-sm">
          Version {{ currentVersion?.version_number || 'N/A' }}
        </Badge>
        <StatusBadge :status="audit.status" />
      </div>
    </div>

    <!-- Audit Information -->
    <Card class="shadow-card">
      <CardHeader>
        <CardTitle class="flex items-center">
          <FileText class="mr-2 h-5 w-5 text-primary" />
          Audit Information
        </CardTitle>
      </CardHeader>
      <CardContent class="p-4 lg:p-6">
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-4 text-sm">
          <div>
            <span class="text-muted-foreground">Auditor:</span>
            <span class="ml-2 font-medium">{{ auditor?.name || 'Unknown' }}</span>
          </div>
          <div>
            <span class="text-muted-foreground">SLA:</span>
            <span class="ml-2 font-medium">{{ sla?.sla_name || 'Unknown SLA' }}</span>
          </div>
          <div>
            <span class="text-muted-foreground">Due Date:</span>
            <span class="ml-2 font-medium">{{ formatDate(audit.due_date) }}</span>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- Version History -->
    <Card v-if="versions.length > 0" class="shadow-card">
      <CardHeader>
        <CardTitle class="flex items-center">
          <History class="mr-2 h-5 w-5 text-primary" />
          Version History
        </CardTitle>
        <CardDescription>Review all versions of this audit</CardDescription>
      </CardHeader>
      <CardContent class="p-4 lg:p-6">
        <div class="space-y-4">
          <div v-for="version in versions" :key="version.version_id" 
               class="border border-border rounded-lg p-4"
               :class="{ 'bg-primary/5 border-primary/30': version.version_id === currentVersion?.version_id }">
            <div class="flex items-center justify-between mb-3">
              <div class="flex items-center space-x-3">
                <Badge variant="outline">
                  {{ version.version_type === 'A' ? `v${version.version_number}` : `r${version.version_number}` }}
                </Badge>
                <Badge :variant="version.approval_status === 'approved' ? 'default' : version.approval_status === 'rejected' ? 'destructive' : 'secondary'">
                  {{ version.approval_status }}
                </Badge>
                <span class="text-sm text-muted-foreground">
                  {{ formatDate(version.date_created) }}
                </span>
              </div>
              <Button 
                v-if="version.version_id === currentVersion?.version_id && audit.status === 'under_review'"
                variant="outline" 
                size="sm"
                @click="selectVersion(version)"
              >
                Review This Version
              </Button>
            </div>
            
            <div v-if="version.extended_information" class="text-sm text-muted-foreground">
              <p><strong>Type:</strong> {{ version.version_type === 'A' ? 'Audit Submission' : 'Review Response' }}</p>
              <p><strong>Submitted by:</strong> User {{ version.user_id }}</p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>


    <!-- Current Version Review -->
    <Card v-if="currentVersion && selectedVersion" class="shadow-card">
      <CardHeader>
        <CardTitle class="flex items-center">
          <Eye class="mr-2 h-5 w-5 text-primary" />
          Review Version {{ selectedVersion.version_number }}
        </CardTitle>
        <CardDescription>Review the audit findings and provide feedback</CardDescription>
      </CardHeader>
      <CardContent class="p-4 lg:p-6">
        <!-- Audit Data Review -->
        <div v-if="parsedExtendedInfo" class="space-y-6">
          <!-- Display data for each metric -->
          <div v-for="(metricData, metricName) in parsedExtendedInfo.responses" :key="metricName" 
               class="border border-border rounded-lg p-4 bg-muted/20">
            <h4 class="font-medium text-foreground mb-4 flex items-center">
              <Target class="mr-2 h-4 w-4" />
              {{ metricName }} - Audit Review
            </h4>
            
            <!-- Questionnaire Responses -->
            <div class="mb-4">
              <h5 class="font-medium text-muted-foreground mb-2">Questionnaire Responses:</h5>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div v-for="(response, questionId) in metricData" :key="questionId" 
                     class="bg-background p-3 rounded border">
                  <div class="text-sm font-medium text-primary mb-1">Question {{ questionId }}:</div>
                  <div class="text-sm text-foreground bg-green-50 p-2 rounded">
                    {{ response }}
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Evidence -->
            <div class="mb-4" v-if="parsedExtendedInfo.evidence?.[metricName]">
              <h5 class="font-medium text-muted-foreground mb-2">Evidence:</h5>
              <div class="bg-background p-3 rounded border">
                <div class="text-sm text-foreground bg-blue-50 p-2 rounded">
                  {{ parsedExtendedInfo.evidence[metricName] }}
                </div>
              </div>
            </div>

            <!-- Evidence Documents -->
            <div class="mb-4" v-if="parsedExtendedInfo.evidence_documents?.[metricName]?.length">
              <h5 class="font-medium text-muted-foreground mb-2">Evidence Documents:</h5>
              <div class="space-y-2">
                <div
                  v-for="doc in parsedExtendedInfo.evidence_documents[metricName]"
                  :key="doc.document_id || doc.name"
                  class="flex items-center justify-between p-3 bg-muted/20 border border-border rounded-lg"
                >
                  <div>
                    <p class="text-sm font-medium text-foreground flex items-center gap-2">
                      <Paperclip class="w-4 h-4 text-primary" />
                      {{ doc.name || doc.file_name || 'Evidence Document' }}
                    </p>
                    <p class="text-xs text-muted-foreground">
                      {{ formatFileSize(doc.size || doc.file_size) }}
                      <span v-if="doc.uploaded_at">
                        • {{ formatDate(doc.uploaded_at) }}
                      </span>
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    class="text-primary"
                    @click.stop="openEvidenceDocument(doc)"
                  >
                    <Download class="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </div>
            
            <!-- Verification Method -->
            <div class="mb-4" v-if="parsedExtendedInfo.verification_methods?.[metricName]">
              <h5 class="font-medium text-muted-foreground mb-2">Verification Method:</h5>
              <div class="bg-background p-3 rounded border">
                <div class="text-sm text-foreground bg-yellow-50 p-2 rounded">
                  {{ parsedExtendedInfo.verification_methods[metricName] }}
                </div>
              </div>
            </div>
            
            <!-- Recommendations -->
            <div class="mb-4" v-if="parsedExtendedInfo.recommendations?.[metricName]">
              <h5 class="font-medium text-muted-foreground mb-2">Recommendations:</h5>
              <div class="bg-background p-3 rounded border">
                <div class="text-sm text-foreground bg-purple-50 p-2 rounded">
                  {{ parsedExtendedInfo.recommendations[metricName] }}
                </div>
              </div>
            </div>
            
            <!-- Comments -->
            <div class="mb-4" v-if="parsedExtendedInfo.comments?.[metricName]">
              <h5 class="font-medium text-muted-foreground mb-2">Auditor Comments:</h5>
              <div class="bg-background p-3 rounded border">
                <div class="text-sm text-foreground bg-gray-50 p-2 rounded">
                  {{ parsedExtendedInfo.comments[metricName] }}
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- No Data Available -->
        <div v-else class="text-center py-8">
          <AlertCircle class="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
          <h3 class="text-lg font-medium mb-2">No Audit Data Available</h3>
          <p class="text-muted-foreground">No audit data found for this version.</p>
        </div>

        <!-- Access Denied Message -->
        <div v-if="!isAssignedReviewer" class="mt-6 pt-6 border-t border-border">
          <div class="text-center py-4">
            <AlertCircle class="w-8 h-8 mx-auto mb-2 text-red-500" />
            <p class="text-red-600 font-medium">Access Denied</p>
            <p class="text-muted-foreground">
              You are not the assigned reviewer for this audit. Only the assigned reviewer can approve or reject this audit.
            </p>
            <Button @click="navigateToMyAudits" variant="outline" class="mt-4">
              Back to My Audits
            </Button>
          </div>
        </div>

        <!-- Review Actions -->
        <div v-else-if="canReview" class="mt-6 pt-6 border-t border-border">
          <div class="space-y-4">
            <div>
              <Label for="review-comments">Review Comments</Label>
              <Textarea
                id="review-comments"
                v-model="reviewComments"
                placeholder="Provide your review comments and feedback..."
                :rows="4"
                class="mt-2"
              />
            </div>
            
            <div class="flex flex-col sm:flex-row gap-3">
              <Button 
                @click="handleApprove"
                :disabled="loading || !reviewComments.trim()"
                class="bg-gradient-to-r from-green-600 to-green-700 hover:shadow-hover transition-all"
              >
                <CheckCircle class="mr-2 h-4 w-4" />
                Approve Audit
              </Button>
              <Button 
                variant="destructive"
                @click="handleReject"
                :disabled="loading || !reviewComments.trim()"
              >
                <X class="mr-2 h-4 w-4" />
                Reject & Request Changes
              </Button>
              <Button 
                variant="outline"
                @click="navigateToMyAudits"
                class="w-full sm:w-auto"
              >
                Cancel
              </Button>
            </div>
            
            <!-- Additional rejection guidance -->
            <div v-if="reviewComments && reviewComments.toLowerCase().includes('reject')" class="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <div class="flex items-start space-x-2">
                <AlertTriangle class="w-5 h-5 text-yellow-600 mt-0.5" />
                <div>
                  <h4 class="font-medium text-yellow-800">Rejection Guidelines</h4>
                  <p class="text-sm text-yellow-700 mt-1">
                    When rejecting an audit, please provide specific feedback on what needs to be changed. 
                    The auditor will see your comments and can address the issues before resubmitting.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Not Available for Review Message -->
        <div v-else-if="audit.status !== 'under_review'" class="mt-6 pt-6 border-t border-border">
          <div class="text-center py-4">
            <AlertCircle class="w-8 h-8 mx-auto mb-2 text-muted-foreground" />
            <p class="text-muted-foreground">
              This audit is not currently under review. 
              <span v-if="audit.status === 'completed'">It has already been completed.</span>
              <span v-else-if="audit.status === 'rejected'">It has been rejected and is awaiting resubmission.</span>
              <span v-else>Status: {{ audit.status }}</span>
            </p>
            <Button @click="navigateToMyAudits" variant="outline" class="mt-4">
              Back to My Audits
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- No Version Selected -->
    <Card v-else-if="currentVersion && !selectedVersion" class="shadow-card">
      <CardContent class="p-6 text-center">
        <Eye class="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
        <h3 class="text-lg font-medium mb-2">Select a Version to Review</h3>
        <p class="text-muted-foreground">Please select a version from the history above to review.</p>
      </CardContent>
    </Card>
  </div>

  <!-- Popup Modal -->
  <PopupModal />
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { 
  FileText, 
  Eye, 
  History,
  CheckCircle,
  X,
  AlertCircle,
  Target,
  AlertTriangle,
  Paperclip,
  Download
} from 'lucide-vue-next'
import apiService from '@/services/api.js'
import Card from '@/components/ui/card.vue'
import CardHeader from '@/components/ui/card-header.vue'
import CardTitle from '@/components/ui/card-title.vue'
import CardDescription from '@/components/ui/card-description.vue'
import CardContent from '@/components/ui/card-content.vue'
import Button from '@/components/ui/button.vue'
import Badge from '@/components/ui/badge.vue'
import Label from '@/components/ui/label.vue'
import Textarea from '@/components/ui/textarea.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import PopupModal from '@/popup/PopupModal.vue'
import { PopupService } from '@/popup/popupService'
import { useNotifications } from '@/composables/useNotifications'
import loggingService from '@/services/loggingService'

const route = useRoute()
const router = useRouter()
const store = useStore()
const { showSuccess, showError, showWarning, showInfo } = useNotifications()

// Get current user from store
const currentUser = computed(() => store.state.auth.currentUser)

// Check if current user is the assigned reviewer
// User can review if they are:
// 1. The assigned reviewer (reviewer_id)
// 2. The assignee (assignee_id)
// 3. The auditor (auditor_id)
// 4. OR have PerformContractAudit permission
const isAssignedReviewer = computed(() => {
  if (!currentUser.value || !audit.value) {
    console.log('[Review Access Check] No currentUser or audit:', { hasUser: !!currentUser.value, hasAudit: !!audit.value })
    return false
  }
  
  // Check multiple possible user ID field names (handle different formats)
  const userId = currentUser.value.id || 
                 currentUser.value.user_id || 
                 currentUser.value.userid || 
                 currentUser.value.UserId ||  // Capital U, capital I
                 currentUser.value.userId ||  // camelCase
                 currentUser.value.USER_ID
  
  if (!userId) {
    console.log('[Review Access Check] No userId found in currentUser:', currentUser.value)
    console.log('[Review Access Check] Available keys:', Object.keys(currentUser.value || {}))
    return false
  }
  
  // Convert to numbers for comparison to handle string/int mismatches
  const currentUserId = Number(userId)
  const auditReviewerId = audit.value.reviewer_id ? Number(audit.value.reviewer_id) : null
  const auditAssigneeId = audit.value.assignee_id ? Number(audit.value.assignee_id) : null
  const auditAuditorId = audit.value.auditor_id ? Number(audit.value.auditor_id) : null
  
  // Check if user is assigned as reviewer, assignee, or auditor
  const isReviewer = auditReviewerId !== null && currentUserId === auditReviewerId
  const isAssignee = auditAssigneeId !== null && currentUserId === auditAssigneeId
  const isAuditor = auditAuditorId !== null && currentUserId === auditAuditorId
  
  console.log('[Review Access Check]', {
    currentUserId,
    auditReviewerId,
    auditAssigneeId,
    auditAuditorId,
    isReviewer,
    isAssignee,
    isAuditor,
    result: isReviewer || isAssignee || isAuditor
  })
  
  // Allow review access if user is reviewer, assignee, or auditor
  return isReviewer || isAssignee || isAuditor
})

// Check if user has access to review this audit
// User can review if they have reviewer access AND audit is under review
const canReview = computed(() => {
  const canReviewResult = isAssignedReviewer.value && audit.value?.status === 'under_review'
  console.log('[Review Can Review Check]', {
    isAssignedReviewer: isAssignedReviewer.value,
    auditStatus: audit.value?.status,
    canReview: canReviewResult
  })
  return canReviewResult
})

const loading = ref(true)
const audit = ref(null)
const sla = ref(null)
const auditor = ref(null)
const reviewer = ref(null)
const versions = ref([])
const currentVersion = ref(null)
const selectedVersion = ref(null)
const reviewComments = ref('')

const formatFileSize = (size) => {
  if (!size && size !== 0) return 'N/A'
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / (1024 * 1024)).toFixed(1)} MB`
}

const openEvidenceDocument = async (file) => {
  if (typeof window === 'undefined') return
  try {
    if (file.url) {
      window.open(file.url, '_blank', 'noopener')
      return
    }

    const documentId = file.document_id || file.id || file.s3_file_id
    if (documentId) {
      const response = await apiService.getS3File(documentId)
      const downloadUrl = response?.s3_file?.url || response?.file_operation?.s3_url || response?.url
      if (downloadUrl) {
        window.open(downloadUrl, '_blank', 'noopener')
        return
      }
    }

    throw new Error('No download URL available')
  } catch (error) {
    console.error('Unable to open evidence document:', error)
    await showError('Download Failed', 'Unable to download the evidence document. Please try again later.', {
      action: 'review_evidence_download_failed',
      error_message: error.message
    })
  }
}

// Parse extended information JSON
const parsedExtendedInfo = computed(() => {
  if (!selectedVersion.value?.extended_information) {
    return null
  }
  
  try {
    // Handle both string and object formats
    const info = typeof selectedVersion.value.extended_information === 'string' 
      ? JSON.parse(selectedVersion.value.extended_information)
      : selectedVersion.value.extended_information
    
    return info
  } catch (error) {
    console.error('Error parsing extended_information:', error)
    return null
  }
})

// Load audit data
const loadAuditData = async () => {
  try {
    loading.value = true
    const auditId = route.params.auditId
    
    // Load audit details
    const auditData = await apiService.getAudit(auditId)
    audit.value = auditData
    
    // Load SLA details
    if (auditData.sla_id) {
      const slaData = await apiService.getAvailableSLAs()
      sla.value = slaData.find(s => s.sla_id === auditData.sla_id) || null
    }
    
    // Load auditor and reviewer - these are users with PerformContractAudit permission
    const usersResponse = await apiService.getAvailableUsers()
    
    // Handle different response formats
    let usersData = []
    if (usersResponse && usersResponse.success && Array.isArray(usersResponse.data)) {
      usersData = usersResponse.data
    } else if (usersResponse && Array.isArray(usersResponse)) {
      usersData = usersResponse
    } else if (usersResponse && usersResponse.data && Array.isArray(usersResponse.data)) {
      usersData = usersResponse.data
    } else {
      console.error('Error loading users:', usersResponse?.error || usersResponse?.message || 'Unknown error')
      usersData = []
    }
    
    // Find auditor and reviewer by matching user IDs (handle different field names)
    auditor.value = usersData.find(u => {
      const uId = u.user_id || u.userid || u.id || u.UserId || u.userId
      return uId && (Number(uId) === Number(auditData.auditor_id))
    }) || null
    reviewer.value = usersData.find(u => {
      const uId = u.user_id || u.userid || u.id || u.UserId || u.userId
      return uId && (Number(uId) === Number(auditData.reviewer_id))
    }) || null
    console.log('[Review] Users loaded:', { auditor: auditor.value, reviewer: reviewer.value, auditData })
    
    // Load versions
    const versionsData = await apiService.getAuditVersions(auditId)
    
    // Handle both array and paginated response formats
    if (Array.isArray(versionsData)) {
      versions.value = versionsData
    } else if (versionsData && versionsData.results && Array.isArray(versionsData.results)) {
      versions.value = versionsData.results
    } else {
      versions.value = []
    }
    
    // Find current version (latest audit version)
    const auditVersions = versions.value.filter(v => v.version_type === 'A')
    currentVersion.value = auditVersions.length > 0 ? 
      auditVersions.reduce((latest, current) => 
        current.version_number > latest.version_number ? current : latest
      ) : null
    
    // Auto-select current version for review
    if (currentVersion.value && audit.value.status === 'under_review') {
      selectedVersion.value = currentVersion.value
    }
    
  } catch (error) {
    console.error('Error loading audit data:', error)
    
    // Show error notification
    await showError('Audit Loading Failed', 'Failed to load audit data for review. Please try refreshing the page.', {
      audit_id: route.params.auditId,
      action: 'audit_loading_failed',
      error_message: error.message
    })
    
    audit.value = null
  } finally {
    loading.value = false
  }
}

const selectVersion = (version) => {
  selectedVersion.value = version
}

const handleApprove = async () => {
  if (!reviewComments.value.trim()) {
    await showWarning('Missing Comments', 'Please provide review comments before approving.', {
      audit_id: route.params.auditId,
      audit_title: audit.value?.title,
      action: 'missing_review_comments'
    })
    PopupService.warning('Please provide review comments before approving.', 'Missing Comments')
    return
  }

  loading.value = true
  try {
    const auditId = route.params.auditId
    
    console.log('Approving audit:', {
      auditId,
      selectedVersion: selectedVersion.value,
      extendedInformation: selectedVersion.value.extended_information
    })
    
    // STEP 1: Create audit findings for each metric (after approval)
    const extendedInfo = parsedExtendedInfo.value
    const findings = []
    
    if (extendedInfo && extendedInfo.responses) {
      // Get metrics for this audit - handle null SLA ID
      if (audit.value.sla_id && audit.value.sla_id !== null) {
        try {
          const slaMetrics = await apiService.getSLAMetrics(audit.value.sla_id)
          console.log('SLA metrics for audit findings:', slaMetrics)
          
          // Create audit findings for each metric
          for (const metric of slaMetrics.metrics || []) {
            const findingData = {
              audit_id: parseInt(auditId),
              metrics_id: metric.metric_id,
              evidence: extendedInfo.evidence?.[metric.metric_name] || '',
              user_id: 1, // Admin user ID
              how_to_verify: extendedInfo.verification_methods?.[metric.metric_name] || '',
              impact_recommendations: extendedInfo.recommendations?.[metric.metric_name] || '',
              details_of_finding: extendedInfo.comments?.[metric.metric_name] || '',
              comment: reviewComments.value, // Admin's approval comment
              check_date: new Date().toISOString().split('T')[0],
              questionnaire_responses: JSON.stringify(extendedInfo.responses?.[metric.metric_name] || {})
            }
            
            console.log('Creating audit finding:', findingData)
            const finding = await apiService.createAuditFinding(findingData)
            findings.push(finding)
          }
        } catch (error) {
          console.error('Error loading SLA metrics for audit findings:', error)
          // Continue without creating findings if SLA metrics can't be loaded
        }
      } else {
        console.warn('No valid SLA ID for creating audit findings')
        // Create findings using the extended info data directly
        for (const [metricName, responses] of Object.entries(extendedInfo.responses)) {
          const findingData = {
            audit_id: parseInt(auditId),
            metrics_id: 1, // Default metric ID when SLA ID is null
            evidence: extendedInfo.evidence?.[metricName] || '',
            user_id: 1, // Admin user ID
            how_to_verify: extendedInfo.verification_methods?.[metricName] || '',
            impact_recommendations: extendedInfo.recommendations?.[metricName] || '',
            details_of_finding: extendedInfo.comments?.[metricName] || '',
            comment: reviewComments.value,
            check_date: new Date().toISOString().split('T')[0],
            questionnaire_responses: JSON.stringify(responses || {})
          }
          
          try {
            console.log('Creating audit finding for metric:', metricName, findingData)
            const finding = await apiService.createAuditFinding(findingData)
            findings.push(finding)
          } catch (error) {
            console.error('Error creating audit finding:', error)
          }
        }
      }
    }
    
    // STEP 2: Update the audit version to approved
    const approvedVersionData = {
      approval_status: 'approved'
    }
    
    await apiService.updateAuditVersion(selectedVersion.value.version_id, approvedVersionData)
    console.log('Updated audit version to approved')
    
    // STEP 3: Create review version (r1, r2, etc.)
    const reviewVersions = versions.value.filter(v => v.version_type === 'R')
    const nextReviewVersion = reviewVersions.length + 1
    
    const reviewVersionData = {
      audit_id: parseInt(auditId),
      version_type: 'R', // Review version
      version_number: nextReviewVersion,
      extended_information: JSON.stringify({
        approved_version: selectedVersion.value.version_number,
        review_comments: reviewComments.value,
        approved_findings: findings,
        approval_date: new Date().toISOString()
      }),
      user_id: 1, // Admin user ID
      approval_status: 'approved',
      date_created: new Date().toISOString().split('T')[0],
      is_active: 1
    }
    
    console.log('Creating review version:', reviewVersionData)
    await apiService.createAuditVersion(reviewVersionData)
    
    // STEP 4: Update audit status to completed
    await apiService.updateAudit(auditId, { 
      status: 'completed',
      review_status: 'approved',
      review_comments: reviewComments.value,
      completion_date: new Date().toISOString().split('T')[0]
    })
    
    console.log('Audit approval completed successfully')
    
    // Show success notification
    await showSuccess('Audit Approved', 'Audit has been approved by admin! Audit findings have been created.', {
      audit_id: route.params.auditId,
      audit_title: audit.value?.title,
      action: 'audit_approved'
    })
    
    PopupService.success('Audit has been approved by admin! Audit findings have been created.', 'Audit Approved')
    PopupService.onAction('ok', () => {
      router.push('/audit/my-audits')
    })
    
  } catch (error) {
    console.error('Error approving audit:', error)
    
    // Show error notification
    await showError('Approval Failed', 'Failed to approve audit. Please try again.', {
      audit_id: route.params.auditId,
      audit_title: audit.value?.title,
      action: 'audit_approval_failed',
      error_message: error.message
    })
    
    PopupService.error('Failed to approve audit. Please try again.', 'Approval Failed')
  } finally {
    loading.value = false
  }
}

const handleReject = async () => {
  if (!reviewComments.value.trim()) {
    await showWarning('Missing Comments', 'Please provide review comments before rejecting.', {
      audit_id: route.params.auditId,
      audit_title: audit.value?.title,
      action: 'missing_review_comments'
    })
    PopupService.warning('Please provide review comments before rejecting.', 'Missing Comments')
    return
  }

  // Confirm rejection
  PopupService.confirm(
    'Are you sure you want to reject this audit? The auditor will be notified and can resubmit after addressing your feedback.',
    'Confirm Rejection',
    async () => {
      await performReject()
    }
  )
}

const performReject = async () => {

  loading.value = true
  try {
    const auditId = route.params.auditId
    
    console.log('Rejecting audit:', {
      auditId,
      selectedVersion: selectedVersion.value,
      reviewComments: reviewComments.value
    })
    
    // STEP 1: Update the audit version to rejected
    const rejectedVersionData = {
      approval_status: 'rejected'
    }
    
    await apiService.updateAuditVersion(selectedVersion.value.version_id, rejectedVersionData)
    console.log('Updated audit version to rejected')
    
    // STEP 2: Create review version (r1, r2, etc.)
    const reviewVersions = versions.value.filter(v => v.version_type === 'R')
    const nextReviewVersion = reviewVersions.length + 1
    
    const reviewVersionData = {
      audit_id: parseInt(auditId),
      version_type: 'R', // Review version
      version_number: nextReviewVersion,
      extended_information: JSON.stringify({
        rejected_version: selectedVersion.value.version_number,
        review_comments: reviewComments.value,
        required_changes: reviewComments.value,
        rejection_date: new Date().toISOString(),
        rejection_reason: 'Audit requires revisions based on reviewer feedback',
        next_steps: 'Please address the feedback and resubmit for review'
      }),
      user_id: 1, // Admin user ID
      approval_status: 'rejected',
      date_created: new Date().toISOString().split('T')[0],
      is_active: 1
    }
    
    console.log('Creating review version:', reviewVersionData)
    await apiService.createAuditVersion(reviewVersionData)
    
    // STEP 3: Update audit status to rejected (auditor can resubmit)
    await apiService.updateAudit(auditId, { 
      status: 'rejected',
      review_status: 'rejected',
      review_comments: reviewComments.value
    })
    
    console.log('Audit rejection completed successfully')
    
    // Show warning notification
    await showWarning('Audit Rejected', 'Audit has been rejected by admin. The auditor will see your feedback and can resubmit after making changes.', {
      audit_id: route.params.auditId,
      audit_title: audit.value?.title,
      action: 'audit_rejected'
    })
    
    PopupService.success('Audit has been rejected by admin. The auditor will see your feedback and can resubmit after making changes.', 'Audit Rejected')
    PopupService.onAction('ok', () => {
      router.push('/audit/my-audits')
    })
    
  } catch (error) {
    console.error('Error rejecting audit:', error)
    
    // Show error notification
    await showError('Rejection Failed', 'Failed to reject audit. Please try again.', {
      audit_id: route.params.auditId,
      audit_title: audit.value?.title,
      action: 'audit_rejection_failed',
      error_message: error.message
    })
    
    PopupService.error('Failed to reject audit. Please try again.', 'Rejection Failed')
  } finally {
    loading.value = false
  }
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString()
}

const navigateToMyAudits = () => router.push('/audit/my-audits')

onMounted(async () => {
  await loggingService.logPageView('Audit', 'Audit Review')
  await loadAuditData()
})
</script>
