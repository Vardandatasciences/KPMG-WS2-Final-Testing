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
          <span v-else>(Admin Access)</span>
        </p>
      </div>
      <div class="flex items-center space-x-2">
        <!-- Reviewer/Admin Badge -->
        <Badge variant="default" :class="isAssignedReviewer ? 'bg-blue-600 text-white' : 'bg-purple-600 text-white'">
          {{ isAssignedReviewer ? 'Reviewer' : 'Admin' }} Review
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
        <div class="grid grid-cols-1 lg:grid-cols-4 gap-4 text-sm">
          <div>
            <span class="text-muted-foreground">Auditor:</span>
            <span class="ml-2 font-medium">{{ auditor?.name || 'Unknown' }}</span>
          </div>
          <div>
            <span class="text-muted-foreground">Reviewer:</span>
            <span class="ml-2 font-medium">{{ reviewer?.name || 'Unknown' }}</span>
          </div>
          <div>
            <span class="text-muted-foreground">Contract:</span>
            <span class="ml-2 font-medium">{{ contract?.contract_title || 'Unknown Contract' }}</span>
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
        <div v-if="normalizedExtendedInfo" class="space-y-6">
          <!-- Display data for each metric -->
          <div
            v-for="termId in normalizedTermIds"
            :key="termId"
            class="border border-border rounded-lg p-4 bg-muted/20"
          >
            <h4 class="font-medium text-foreground mb-4 flex items-center">
              <Target class="mr-2 h-4 w-4" />
              {{ getTermDisplayName(termId) }} - Audit Review
            </h4>
            
            <!-- Questionnaire Responses -->
            <div class="mb-4">
              <h5 class="font-medium text-muted-foreground mb-2">Questionnaire Responses:</h5>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div
                  v-for="(response, questionId) in normalizedExtendedInfo.responses[termId]"
                  :key="questionId"
                  class="bg-background p-3 rounded border"
                >
                  <div class="text-sm font-medium text-primary mb-1">Question {{ questionId }}:</div>
                  <div class="text-sm text-foreground bg-green-50 p-2 rounded">
                    {{ response }}
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Evidence -->
            <div class="mb-4" v-if="normalizedExtendedInfo.evidence?.[termId]">
              <h5 class="font-medium text-muted-foreground mb-2">Evidence:</h5>
              <div class="bg-background p-3 rounded border">
                <div class="text-sm text-foreground bg-blue-50 p-2 rounded">
                  {{ normalizedExtendedInfo.evidence[termId] }}
                </div>
              </div>
            </div>
            
            <!-- Verification Method -->
            <div class="mb-4" v-if="normalizedExtendedInfo.verification_methods?.[termId]">
              <h5 class="font-medium text-muted-foreground mb-2">Verification Method:</h5>
              <div class="bg-background p-3 rounded border">
                <div class="text-sm text-foreground bg-yellow-50 p-2 rounded">
                  {{ normalizedExtendedInfo.verification_methods[termId] }}
                </div>
              </div>
            </div>
            
            <!-- Recommendations -->
            <div class="mb-4" v-if="normalizedExtendedInfo.recommendations?.[termId]">
              <h5 class="font-medium text-muted-foreground mb-2">Recommendations:</h5>
              <div class="bg-background p-3 rounded border">
                <div class="text-sm text-foreground bg-purple-50 p-2 rounded">
                  {{ normalizedExtendedInfo.recommendations[termId] }}
                </div>
              </div>
            </div>
            
            <!-- Comments -->
            <div class="mb-4" v-if="normalizedExtendedInfo.comments?.[termId]">
              <h5 class="font-medium text-muted-foreground mb-2">Auditor Comments:</h5>
              <div class="bg-background p-3 rounded border">
                <div class="text-sm text-foreground bg-gray-50 p-2 rounded">
                  {{ normalizedExtendedInfo.comments[termId] }}
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

        <!-- Review Actions -->
        <div v-if="canReview" class="mt-6 pt-6 border-t border-border">
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
        
        <!-- Access Denied Message -->
        <div v-else-if="audit.status !== 'under_review'" class="mt-6 pt-6 border-t border-border">
          <div class="text-center py-4">
            <AlertCircle class="w-8 h-8 mx-auto mb-2 text-muted-foreground" />
            <p class="text-muted-foreground">
              This audit is not currently under review. 
              <span v-if="audit.status === 'completed'">It has already been completed.</span>
              <span v-else-if="audit.status === 'rejected'">It has been rejected and is awaiting resubmission.</span>
              <span v-else>Status: {{ audit.status }}</span>
            </p>
          </div>
        </div>
        
        <!-- Not Authorized Message -->
        <div v-else-if="!isAssignedReviewer" class="mt-6 pt-6 border-t border-border">
          <div class="text-center py-4">
            <AlertCircle class="w-8 h-8 mx-auto mb-2 text-red-500" />
            <p class="text-red-600 font-medium">Access Denied</p>
            <p class="text-muted-foreground">
              You are not the assigned reviewer for this audit. Only the assigned reviewer can approve or reject this audit.
            </p>
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
import { useNotifications } from '@/composables/useNotifications'
import PopupModal from '@/popup/PopupModal.vue'
import { PopupService } from '@/popup/popupService'
import { 
  FileText, 
  Eye, 
  History,
  CheckCircle,
  X,
  AlertCircle,
  Target,
  AlertTriangle
} from 'lucide-vue-next'
import contractAuditApi from '@/services/contractAuditApi.js'
import loggingService from '@/services/loggingService'
import { 
  Card, CardHeader, CardTitle, CardDescription, CardContent, Button, Badge, Label, Textarea
} from '@/components/ui_contract'
import StatusBadge from '@/components/StatusBadge.vue'

const route = useRoute()
const router = useRouter()
const store = useStore()
const { showSuccess, showError, showWarning, showInfo } = useNotifications()

const loading = ref(true)
const audit = ref(null)
const contract = ref(null)
const auditor = ref(null)
const reviewer = ref(null)
const contractTerms = ref([])
const versions = ref([])
const currentVersion = ref(null)
const selectedVersion = ref(null)
const reviewComments = ref('')

// Get current user from store
const currentUser = computed(() => store.state.auth.currentUser)

// Check if current user is the assigned reviewer
const isAssignedReviewer = computed(() => {
  return currentUser.value && audit.value && 
         (currentUser.value.userid === audit.value.reviewer_id || 
          currentUser.value.user_id === audit.value.reviewer_id)
})

// Check if user has access to review this audit
const canReview = computed(() => {
  return isAssignedReviewer.value && audit.value?.status === 'under_review'
})

// Parse extended information JSON
const rawExtendedInfo = computed(() => {
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

const normalizeTermId = (value) => {
  if (value === null || value === undefined) return null
  return value.toString()
}

const termLookup = computed(() => {
  return contractTerms.value.reduce((acc, term) => {
    const termId = normalizeTermId(term.term_id)
    if (termId) {
      acc[termId] = term
    }
    return acc
  }, {})
})

const normalizedExtendedInfo = computed(() => {
  if (!rawExtendedInfo.value) return null

  const normalizeSection = (section) => {
    const result = {}
    if (!section) return result

    Object.entries(section).forEach(([key, value]) => {
      const normalizedKey = resolveTermKey(key)
      if (normalizedKey) {
        result[normalizedKey] = value
      }
    })

    return result
  }

  const resolveTermKey = (key) => {
    const candidateKey = normalizeTermId(key)
    if (!candidateKey) return null

    if (termLookup.value[candidateKey]) {
      return candidateKey
    }

    const metadataMatch = rawExtendedInfo.value?.metadata?.terms?.[candidateKey]
    if (metadataMatch?.term_id) {
      return normalizeTermId(metadataMatch.term_id)
    }

    const metadataByName = Object.entries(rawExtendedInfo.value?.metadata?.terms || {}).find(
      ([, data]) => data?.term_name === candidateKey
    )
    if (metadataByName && metadataByName[1]?.term_id) {
      return normalizeTermId(metadataByName[1].term_id)
    }

    const contractTermMatch = contractTerms.value.find(term => {
      const titles = [term.term_title, term.term_name].filter(Boolean)
      return titles.includes(candidateKey)
    })

    if (contractTermMatch?.term_id) {
      return normalizeTermId(contractTermMatch.term_id)
    }

    return candidateKey
  }

  const normalized = {
    responses: normalizeSection(rawExtendedInfo.value.responses),
    evidence: normalizeSection(rawExtendedInfo.value.evidence),
    verification_methods: normalizeSection(rawExtendedInfo.value.verification_methods),
    recommendations: normalizeSection(rawExtendedInfo.value.recommendations),
    comments: normalizeSection(rawExtendedInfo.value.comments),
    metadata: { terms: {} }
  }

  Object.entries(rawExtendedInfo.value?.metadata?.terms || {}).forEach(([key, data]) => {
    const normalizedKey = resolveTermKey(data?.term_id ?? key)
    if (!normalizedKey) return
    normalized.metadata.terms[normalizedKey] = {
      term_id: normalizeTermId(data?.term_id) || normalizedKey,
      term_name: data?.term_name || data?.metric_name || termLookup.value[normalizedKey]?.term_title || normalizedKey
    }
  })

  Object.keys(normalized.responses).forEach(termId => {
    if (!normalized.metadata.terms[termId]) {
      const lookupTerm = termLookup.value[termId]
      normalized.metadata.terms[termId] = {
        term_id: termId,
        term_name: lookupTerm?.term_title || lookupTerm?.term_name || (termId === 'general' ? 'General Audit Questions' : `Term ${termId}`)
      }
    }
  })

  return normalized
})

const normalizedTermIds = computed(() => {
  if (!normalizedExtendedInfo.value) return []
  return Object.keys(normalizedExtendedInfo.value.responses || {})
})

const getTermDisplayName = (termId) => {
  const id = normalizeTermId(termId)
  if (!id) return 'Unknown Term'
  if (id === 'general') return 'General Audit Questions'
  const term = termLookup.value[id]
  if (term) {
    return term.term_title || term.term_name || `Term ${id}`
  }
  const metadataTerm = normalizedExtendedInfo.value?.metadata?.terms?.[id] || rawExtendedInfo.value?.metadata?.terms?.[id]
  if (metadataTerm?.term_name) {
    return metadataTerm.term_name
  }
  return `Term ${id}`
}

// Load audit data
const loadAuditData = async () => {
  try {
    loading.value = true
    const auditId = route.params.auditId
    
    // Load audit details
    const auditResponse = await contractAuditApi.getContractAudit(auditId)
    const auditData = auditResponse.success ? auditResponse.data : null
    console.log('Loaded audit data:', auditData)
    
    if (!auditData) {
      audit.value = null
      PopupService.error('Unable to load audit details.', 'Load Failed')
      return
    }

    audit.value = auditData
    
    // Load Contract details
    if (auditData.contract_id) {
      const contractsResponse = await contractAuditApi.getAvailableContracts()
      const contractsData = contractsResponse.success ? contractsResponse.data : []
      contract.value = contractsData.find(c => c.contract_id === auditData.contract_id) || null
      console.log('Found contract:', contract.value)

      const termsResponse = await contractAuditApi.getContractTermsForAudit(auditData.contract_id)
      const termsData = termsResponse.success ? termsResponse.data : null
      const extractedTerms = Array.isArray(termsData?.terms)
        ? termsData.terms
        : Array.isArray(termsData)
          ? termsData
          : []
      contractTerms.value = extractedTerms
      console.log('Loaded contract terms:', contractTerms.value)
    } else {
      console.log('No contract_id found in audit data')
      contract.value = null
      contractTerms.value = []
    }
    
    // Load auditor and reviewer
    const usersResponse = await contractAuditApi.getAvailableUsers()
    const usersData = usersResponse.success ? usersResponse.data : []
    auditor.value = usersData.find(u => u.user_id === auditData.auditor_id) || null
    reviewer.value = usersData.find(u => u.user_id === auditData.reviewer_id) || null
    
    // Load versions
    const versionsResponse = await contractAuditApi.getContractAuditVersions({ audit_id: auditId })
    const versionsData = versionsResponse.success ? versionsResponse.data : []
    
    // Handle both array and paginated response formats
    if (Array.isArray(versionsData)) {
      versions.value = versionsData
    } else if (versionsData && versionsData.results && Array.isArray(versionsData.results)) {
      versions.value = versionsData.results
    } else {
      versions.value = []
    }
    
    // Find current version (latest audit version that is pending)
    const auditVersions = versions.value.filter(v => v.version_type === 'A')
    const pendingAuditVersions = auditVersions.filter(v => !v.approval_status || v.approval_status === 'pending')
    
    // If there are pending versions, use the latest one
    if (pendingAuditVersions.length > 0) {
      currentVersion.value = pendingAuditVersions.reduce((latest, current) => 
        current.version_number > latest.version_number ? current : latest
      )
    } else {
      // If no pending versions, use the latest audit version (might be already approved/rejected)
      currentVersion.value = auditVersions.length > 0 ? 
        auditVersions.reduce((latest, current) => 
          current.version_number > latest.version_number ? current : latest
        ) : null
    }
    
    // Auto-select current version for review
    if (currentVersion.value && audit.value.status === 'under_review') {
      selectedVersion.value = currentVersion.value
      console.log('Auto-selected version for review:', selectedVersion.value)
    }
    
    console.log('All versions loaded:', versions.value)
    console.log('Audit versions (type A):', auditVersions)
    console.log('Pending audit versions:', pendingAuditVersions)
    console.log('Current version:', currentVersion.value)
    console.log('Selected version:', selectedVersion.value)
    
  } catch (error) {
    console.error('Error loading audit data:', error)
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
    PopupService.warning('Please provide review comments before approving.', 'Missing Comments')
    return
  }

  // Check if we have a selected version
  if (!selectedVersion.value) {
    PopupService.warning('No version selected for approval. Please select a version to review.', 'No Version Selected')
    return
  }

  // Check if the version is in the correct status for approval
  if (selectedVersion.value.approval_status && selectedVersion.value.approval_status !== 'pending') {
    PopupService.warning(`Cannot approve this version. Current status: ${selectedVersion.value.approval_status}`, 'Invalid Status')
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
    const extendedInfo = normalizedExtendedInfo.value
    const findings = []
    const failedFindings = []
    
    if (extendedInfo && extendedInfo.responses && Object.keys(extendedInfo.responses).length > 0) {
      // Get metrics for this audit - now we should have contract_id field
      let contractIdToUse = audit.value.contract_id
      
      console.log('Audit data for contract terms:', {
        contract_id: audit.value.contract_id,
        contract: audit.value.contract,
        contractIdToUse: contractIdToUse
      })
      
      if (!contractIdToUse) {
        console.error('No contract ID found in audit data!')
        PopupService.error('Cannot create audit findings: No contract ID associated with this audit.', 'No Contract ID')
        return
      }
      
      let termsList = contractTerms.value
      if (!termsList || termsList.length === 0) {
        console.log('Contract terms cache empty, fetching terms...')
        const contractTermsResponse = await contractAuditApi.getContractTermsForAudit(contractIdToUse)
        const termsData = contractTermsResponse.success ? contractTermsResponse.data : null
        termsList = Array.isArray(termsData?.terms)
          ? termsData.terms
          : Array.isArray(termsData)
            ? termsData
            : []
        contractTerms.value = termsList
      }
      
      console.log('Extracted contract terms:', termsList)
      
      if (!termsList || termsList.length === 0) {
        console.warn('No contract terms found for this audit')
        PopupService.warning('Warning: No contract terms found. Proceeding without creating findings.', 'No Terms Found')
      } else {
        console.log(`Creating audit findings for ${Object.keys(extendedInfo.responses).length} term response(s)...`)

        const termMap = termsList.reduce((acc, term) => {
          const termId = normalizeTermId(term.term_id)
          if (termId) {
            acc[termId] = term
          }
          return acc
        }, {})

        for (const [termKey, responses] of Object.entries(extendedInfo.responses)) {
          const normalizedTermId = normalizeTermId(termKey)
          if (!normalizedTermId) continue

          const term = termMap[normalizedTermId]
          if (!term) {
            console.warn(`No matching contract term found for term key "${termKey}". Skipping finding creation.`)
            failedFindings.push({ term_id: normalizedTermId, error: 'Term not found' })
            continue
          }

          console.log(`Processing term: ${normalizedTermId} (${term.term_title || term.term_name})`)

          const evidenceValue = extendedInfo.evidence?.[normalizedTermId] ?? 'No evidence provided'
          const verificationValue = extendedInfo.verification_methods?.[normalizedTermId] ?? 'Manual verification'
          const recommendationsValue = extendedInfo.recommendations?.[normalizedTermId] ?? 'No recommendations'
          const commentsValue = extendedInfo.comments?.[normalizedTermId] ?? 'No details provided'

          const questionnaireResponses = typeof responses === 'string'
            ? responses
            : JSON.stringify(responses || {})

          const findingData = {
            audit_id: parseInt(auditId),
            term_id: normalizedTermId,
            evidence: evidenceValue,
            user_id: currentUser.value?.userid || currentUser.value?.user_id || 1, // Current reviewer user ID
            how_to_verify: verificationValue,
            impact_recommendations: recommendationsValue,
            details_of_finding: commentsValue,
            comment: reviewComments.value, // Reviewer's approval comment
            check_date: new Date().toISOString().split('T')[0],
            questionnaire_responses: questionnaireResponses
          }
          
          console.log(`Creating audit finding for term ${normalizedTermId}:`, findingData)
          
          try {
            const findingResponse = await contractAuditApi.createContractAuditFinding(findingData)
            
            console.log('Audit finding creation response:', findingResponse)
            
            if (findingResponse.success) {
              console.log(`✅ Audit finding created successfully for term ${normalizedTermId}`)
              findings.push(findingResponse.data)
            } else {
              console.error(`❌ Failed to create audit finding for term ${normalizedTermId}:`, findingResponse.error)
              failedFindings.push({ term_id: normalizedTermId, error: findingResponse.error })
            }
          } catch (error) {
            console.error(`❌ Error creating audit finding for term ${normalizedTermId}:`, error)
            failedFindings.push({ term_id: normalizedTermId, error: error.message })
          }
        }
        
        console.log(`Audit findings creation complete: ${findings.length} successful, ${failedFindings.length} failed`)
        
        if (failedFindings.length > 0) {
          console.error('Failed findings:', failedFindings)
        }
      }
    }
    
    // STEP 2: Update the audit version to approved
    const approvedVersionData = {
      approval_status: 'approved'
    }
    
    console.log('Updating audit version:', {
      versionId: selectedVersion.value.version_id,
      versionData: approvedVersionData,
      selectedVersion: selectedVersion.value
    })
    
    await contractAuditApi.updateContractAuditVersion(selectedVersion.value.version_id, approvedVersionData)
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
      user_id: currentUser.value?.userid || currentUser.value?.user_id || 1, // Current reviewer user ID
      approval_status: 'approved',
      date_created: new Date().toISOString().split('T')[0],
      is_active: 1
    }
    
    console.log('Creating review version:', reviewVersionData)
    await contractAuditApi.createContractAuditVersion(reviewVersionData)
    
    // STEP 4: Update audit status to completed
    await contractAuditApi.updateContractAudit(auditId, { 
      status: 'completed',
      review_status: 'approved',
      review_comments: reviewComments.value,
      completion_date: new Date().toISOString().split('T')[0]
    })
    
    console.log('Audit approval completed successfully')
    
    // STEP 5: Verify findings were saved to database
    try {
      const savedFindings = await contractAuditApi.getContractAuditFindings({ audit_id: auditId })
      console.log('📊 Verification - Findings saved in database:', savedFindings)
      
      const savedCount = savedFindings.data?.length || 0
      console.log(`📊 Verification - Total findings in DB for audit ${auditId}: ${savedCount}`)
      
      if (savedCount !== findings.length) {
        console.warn(`⚠️ Mismatch: Created ${findings.length} findings but found ${savedCount} in database`)
      } else {
        console.log(`✅ Verification successful: All ${savedCount} findings confirmed in database`)
      }
    } catch (verifyError) {
      console.error('❌ Error verifying saved findings:', verifyError)
    }
    
    // Build success message with findings status
    let successMessage = 'Audit has been approved!'
    if (findings.length > 0) {
      successMessage += `\n✅ ${findings.length} audit finding(s) created successfully.`
    }
    if (failedFindings.length > 0) {
      successMessage += `\n⚠️ ${failedFindings.length} audit finding(s) failed to create.`
      successMessage += '\n\nPlease check the console for error details.'
      console.error('Failed findings details:', failedFindings)
    }
    if (findings.length === 0 && failedFindings.length === 0) {
      successMessage += '\nℹ️ No audit findings were created (no contract terms found).'
    }
    
    PopupService.success(successMessage, 'Audit Approved')
    PopupService.onAction('ok', () => {
      router.push('/contract-audit/all')
    })
    
  } catch (error) {
    console.error('Error approving audit:', error)
    PopupService.error('Failed to approve audit. Please try again.', 'Approval Failed')
  } finally {
    loading.value = false
  }
}

const handleReject = async () => {
  if (!reviewComments.value.trim()) {
    PopupService.warning('Please provide review comments before rejecting.', 'Missing Comments')
    return
  }

  // Check if we have a selected version
  if (!selectedVersion.value) {
    PopupService.warning('No version selected for rejection. Please select a version to review.', 'No Version Selected')
    return
  }

  // Check if the version is in the correct status for rejection
  if (selectedVersion.value.approval_status && selectedVersion.value.approval_status !== 'pending') {
    PopupService.warning(`Cannot reject this version. Current status: ${selectedVersion.value.approval_status}`, 'Invalid Status')
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
    
    await contractAuditApi.updateContractAuditVersion(selectedVersion.value.version_id, rejectedVersionData)
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
        next_steps: 'Please address the feedback and resubmit for review',
        reviewer_id: currentUser.value?.userid || currentUser.value?.user_id || 1,
        reviewer_name: currentUser.value?.name || 'Reviewer'
      }),
      user_id: currentUser.value?.userid || currentUser.value?.user_id || 1, // Current reviewer user ID
      approval_status: 'rejected',
      date_created: new Date().toISOString().split('T')[0],
      is_active: 1
    }
    
    console.log('Creating review version:', reviewVersionData)
    await contractAuditApi.createContractAuditVersion(reviewVersionData)
    console.log('Review version created successfully')
    
    // STEP 3: Update audit status to rejected (auditor can resubmit)
    const updateData = { 
      status: 'rejected',
      review_status: 'rejected',
      review_comments: reviewComments.value
    }
    console.log('Updating audit status to rejected:', updateData)
    await contractAuditApi.updateContractAudit(auditId, updateData)
    
    console.log('✅ Audit rejection completed successfully')
    console.log('Audit status changed to: rejected')
    console.log('Auditor can now resubmit the audit from the execution page')
    
    PopupService.success('Audit has been rejected. The auditor will see your feedback and can resubmit after making changes.', 'Audit Rejected')
    PopupService.onAction('ok', () => {
      router.push('/contract-audit/all')
    })
    
  } catch (error) {
    console.error('Error rejecting audit:', error)
    PopupService.error('Failed to reject audit. Please try again.', 'Rejection Failed')
  } finally {
    loading.value = false
  }
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString()
}

const navigateToMyAudits = () => router.push('/contract-audit/all')

onMounted(async () => {
  await loggingService.logPageView('Contract', 'Contract Audit Review')
  await loadAuditData()
})
</script>
