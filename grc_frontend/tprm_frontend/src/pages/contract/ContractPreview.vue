<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-4">
        <Button variant="ghost" size="icon" @click="goBack">
          <ArrowLeft class="w-4 h-4" />
        </Button>
        <div>
          <h1 class="text-3xl font-bold text-foreground">
            {{ isSubcontract ? 'Subcontract Preview' : 'Contract Preview' }}
          </h1>
          <p class="text-muted-foreground">
            {{ isSubcontract ? 'Review subcontract details and parent contract information before submitting for approval' : 'Review all contract details before submitting for approval' }}
          </p>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <Button variant="outline" @click="goBack" class="gap-2">
          <Edit class="w-4 h-4" />
          Edit Contract
        </Button>
        <Button @click="handleSubmit" :disabled="isLoading || isSubmitting" class="gap-2">
          <Send class="w-4 h-4" />
          {{ isLoading || isSubmitting ? 'Submitting...' : 'Submit for Review' }}
        </Button>
      </div>
    </div>

    <!-- Success Message -->
    <div v-if="successMessage" class="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg">
      <div class="flex items-center gap-2 text-green-800">
        <CheckCircle class="w-5 h-5" />
        <span>{{ successMessage }}</span>
      </div>
    </div>

    <!-- Error Messages -->
    <div v-if="errors.general" class="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
      <div class="flex items-center gap-2 text-red-800">
        <AlertTriangle class="w-5 h-5" />
        <span>{{ errors.general }}</span>
      </div>
    </div>

    <!-- Risk Analysis Notification -->
    <div v-if="showRiskAnalysisNotification" class="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
      <div class="flex items-center gap-2 text-blue-800">
        <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
        <span class="text-sm">Risk analysis is running in the background. You can continue working while it completes.</span>
        <Button variant="ghost" size="sm" @click="showRiskAnalysisNotification = false" class="ml-auto">
          <X class="w-4 h-4" />
        </Button>
      </div>
    </div>

    <!-- Risk Analysis Triggered Notification -->
    <div v-if="showRiskAnalysisTriggered" class="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg">
      <div class="flex items-center gap-2 text-green-800">
        <CheckCircle class="w-4 h-4" />
        <span class="text-sm">Risk analysis has been triggered and will run in the background.</span>
        <Button variant="ghost" size="sm" @click="showRiskAnalysisTriggered = false" class="ml-auto">
          <X class="w-4 h-4" />
        </Button>
      </div>
    </div>

    <!-- Parent Contract Information (for subcontracts) -->
    <div v-if="isSubcontract && parentContract.contract_id" class="mb-6">
      <Card class="border-blue-200 bg-blue-50">
        <CardHeader>
          <CardTitle class="flex items-center gap-2 text-blue-800">
            <FileText class="w-5 h-5" />
            Parent Contract Information
          </CardTitle>
          <CardDescription class="text-blue-600">
            This subcontract is created under the following parent contract
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <span class="text-sm font-medium text-blue-800">Parent Contract ID:</span>
              <p class="text-blue-700 font-semibold">#{{ parentContract.contract_id }}</p>
            </div>
            <div>
              <span class="text-sm font-medium text-blue-800">Parent Contract Title:</span>
              <p class="text-blue-700">{{ parentContract.contract_title || 'Not specified' }}</p>
            </div>
            <div>
              <span class="text-sm font-medium text-blue-800">Parent Contract Value:</span>
              <p class="text-blue-700">{{ formatCurrency(parentContract.contract_value) }}</p>
            </div>
            <div>
              <span class="text-sm font-medium text-blue-800">Parent Contract Type:</span>
              <p class="text-blue-700">{{ parentContract.contract_type || 'Not specified' }}</p>
            </div>
            <div>
              <span class="text-sm font-medium text-blue-800">Parent Contract Status:</span>
              <Badge :variant="getStatusVariant(parentContract.status)">
                {{ parentContract.status || 'Not specified' }}
              </Badge>
            </div>
            <div>
              <span class="text-sm font-medium text-blue-800">Parent Contract Vendor:</span>
              <p class="text-blue-700">{{ parentContract.vendor?.company_name || 'Not specified' }}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>

    <!-- Contract Details -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Basic Information -->
      <Card>
        <CardHeader>
          <CardTitle class="flex items-center gap-2">
            <FileText class="w-5 h-5" />
            Primary Information
          </CardTitle>
        </CardHeader>
        <CardContent class="space-y-4">
          <div class="grid grid-cols-1 gap-4">
            <div>
              <span class="font-medium text-sm text-muted-foreground">Title:</span>
              <p class="text-lg">{{ contractData.contract_title || "Not specified" }}</p>
            </div>
            <div>
              <span class="font-medium text-sm text-muted-foreground">Contract Number:</span>
              <p class="text-lg">{{ contractData.contract_number || "Not specified" }}</p>
            </div>
            <div>
              <span class="font-medium text-sm text-muted-foreground">Type:</span>
              <p class="text-lg">{{ contractData.contract_type || "Not specified" }}</p>
            </div>
            <div>
              <span class="font-medium text-sm text-muted-foreground">Category:</span>
              <p class="text-lg">{{ contractData.contract_category || "Not specified" }}</p>
            </div>
            <div>
              <span class="font-medium text-sm text-muted-foreground">Priority:</span>
              <p class="text-lg">{{ contractData.priority || "Not specified" }}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <!-- Vendor Information -->
      <Card>
        <CardHeader>
          <CardTitle class="flex items-center gap-2">
            <Building class="w-5 h-5" />
            Vendor Information
          </CardTitle>
        </CardHeader>
        <CardContent class="space-y-4">
          <div class="grid grid-cols-1 gap-4">
            <div>
              <span class="font-medium text-sm text-muted-foreground">Vendor Name:</span>
              <p class="text-lg">{{ contractData.vendor_name || "Not specified" }}</p>
            </div>
            <div>
              <span class="font-medium text-sm text-muted-foreground">Vendor ID:</span>
              <p class="text-lg">{{ contractData.vendor_id || "Not specified" }}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <!-- Financial Details -->
      <Card>
        <CardHeader>
          <CardTitle class="flex items-center gap-2">
            <DollarSign class="w-5 h-5" />
            Financial Details
          </CardTitle>
        </CardHeader>
        <CardContent class="space-y-4">
          <div class="grid grid-cols-1 gap-4">
            <div>
              <span class="font-medium text-sm text-muted-foreground">Value:</span>
              <p class="text-lg">
                {{ contractData.contract_value ? `${contractData.currency} ${Number(contractData.contract_value).toLocaleString()}` : "Not specified" }}
              </p>
            </div>
            <div>
              <span class="font-medium text-sm text-muted-foreground">Currency:</span>
              <p class="text-lg">{{ contractData.currency || "Not specified" }}</p>
            </div>
            <div>
              <span class="font-medium text-sm text-muted-foreground">Liability Cap:</span>
              <p class="text-lg">
                {{ contractData.liability_cap ? `${contractData.currency} ${Number(contractData.liability_cap).toLocaleString()}` : "Not specified" }}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <!-- Dates & Terms -->
      <Card>
        <CardHeader>
          <CardTitle class="flex items-center gap-2">
            <Calendar class="w-5 h-5" />
            Dates & Terms
          </CardTitle>
        </CardHeader>
        <CardContent class="space-y-4">
          <div class="grid grid-cols-1 gap-4">
            <div>
              <span class="font-medium text-sm text-muted-foreground">Start Date:</span>
              <p class="text-lg">{{ contractData.start_date || "Not specified" }}</p>
            </div>
            <div>
              <span class="font-medium text-sm text-muted-foreground">End Date:</span>
              <p class="text-lg">{{ contractData.end_date || "Not specified" }}</p>
            </div>
            <div>
              <span class="font-medium text-sm text-muted-foreground">Notice Period:</span>
              <p class="text-lg">{{ contractData.notice_period_days }} days</p>
            </div>
            <div>
              <span class="font-medium text-sm text-muted-foreground">Auto Renewal:</span>
              <p class="text-lg">{{ contractData.auto_renewal ? "Enabled" : "Disabled" }}</p>
            </div>
            <div v-if="contractData.renewal_terms">
              <span class="font-medium text-sm text-muted-foreground">Renewal Terms:</span>
              <p class="text-sm text-muted-foreground mt-1">{{ contractData.renewal_terms }}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <!-- Stakeholders -->
      <Card>
        <CardHeader>
          <CardTitle class="flex items-center gap-2">
            <Users class="w-5 h-5" />
            Stakeholders
          </CardTitle>
        </CardHeader>
        <CardContent class="space-y-4">
          <div class="grid grid-cols-1 gap-4">
            <div>
              <span class="font-medium text-sm text-muted-foreground">Contract Owner:</span>
              <p class="text-lg">{{ getContractOwnerName() || "Not specified" }}</p>
            </div>
            <div>
              <span class="font-medium text-sm text-muted-foreground">Legal Reviewer:</span>
              <p class="text-lg">{{ getLegalReviewerName() || "Not specified" }}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <!-- Legal & Risk -->
      <Card>
        <CardHeader>
          <CardTitle class="flex items-center gap-2">
            <Shield class="w-5 h-5" />
            Legal & Risk Management
          </CardTitle>
        </CardHeader>
        <CardContent class="space-y-4">
          <div class="grid grid-cols-1 gap-4">
            <div>
              <span class="font-medium text-sm text-muted-foreground">Risk Score:</span>
              <p class="text-lg">{{ contractData.contract_risk_score || "Not specified" }}</p>
            </div>
            <div>
              <span class="font-medium text-sm text-muted-foreground">Dispute Resolution:</span>
              <p class="text-lg">{{ contractData.dispute_resolution_method || "Not specified" }}</p>
            </div>
            <div>
              <span class="font-medium text-sm text-muted-foreground">Governing Law:</span>
              <p class="text-lg">{{ contractData.governing_law || "Not specified" }}</p>
            </div>
            <div>
              <span class="font-medium text-sm text-muted-foreground">Termination Clause:</span>
              <p class="text-lg">{{ contractData.termination_clause_type || "Not specified" }}</p>
            </div>
            <div v-if="contractData.compliance_framework">
              <span class="font-medium text-sm text-muted-foreground">Compliance Framework:</span>
              <p class="text-lg">{{ contractData.compliance_framework }}</p>
            </div>
            <div v-if="contractData.insurance_requirements">
              <span class="font-medium text-sm text-muted-foreground">Insurance Requirements:</span>
              <p class="text-sm text-muted-foreground mt-1">{{ contractData.insurance_requirements }}</p>
            </div>
            <div v-if="contractData.data_protection_clauses">
              <span class="font-medium text-sm text-muted-foreground">Data Protection Clauses:</span>
              <p class="text-sm text-muted-foreground mt-1">{{ contractData.data_protection_clauses }}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>

    <!-- Contract Terms -->
    <Card v-if="contractTerms && contractTerms.length > 0">
      <CardHeader>
        <CardTitle class="flex items-center gap-2">
          <FileCheck class="w-5 h-5" />
          Contract Terms ({{ contractTerms.length }})
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div class="space-y-4">
          <div v-for="(term, index) in contractTerms" :key="term?.term_id || `term-${index}`" class="border rounded p-4">
            <div class="space-y-2">
              <div class="flex items-center justify-between">
                <h4 class="font-medium">{{ term.term_title || `Term #${index + 1}` }}</h4>
                <Badge :variant="getTermStatusVariant(term.compliance_status)">
                  {{ term.compliance_status }}
                </Badge>
              </div>
              <div class="text-sm text-muted-foreground">
                <span class="font-medium">Category:</span> {{ term.term_category }} | 
                <span class="font-medium">Risk Level:</span> {{ term.risk_level }}
              </div>
              <div v-if="term.term_text" class="text-sm text-muted-foreground">
                {{ term.term_text }}
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- Contract Clauses -->
    <Card v-if="contractClauses && contractClauses.length > 0">
      <CardHeader>
        <CardTitle class="flex items-center gap-2">
          <FileText class="w-5 h-5" />
          Contract Clauses ({{ contractClauses.length }})
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div class="space-y-4">
          <div v-for="(clause, index) in contractClauses" :key="clause?.clause_id || `clause-${index}`" class="border rounded p-4">
            <div class="space-y-2">
              <div class="flex items-center justify-between">
                <h4 class="font-medium">{{ clause.clause_name || `Clause #${index + 1}` }}</h4>
                <div class="flex gap-2">
                  <Badge :variant="getClauseTypeVariant(clause.clause_type)">
                    {{ clause.clause_type }}
                  </Badge>
                  <Badge :variant="getRiskVariant(clause.risk_level)">
                    {{ clause.risk_level }}
                  </Badge>
                </div>
              </div>
              <div v-if="clause.legal_category" class="text-sm text-muted-foreground">
                <span class="font-medium">Legal Category:</span> {{ clause.legal_category }}
              </div>
              <div v-if="clause.clause_text" class="text-sm text-muted-foreground">
                {{ clause.clause_text }}
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
import { useRouter, useRoute } from 'vue-router'
import { 
  Card, CardContent, CardDescription, CardHeader, CardTitle,
  Badge, Button
} from '@/components/ui'
import { 
  ArrowLeft, Send, FileText, Building, DollarSign, Calendar, 
  Shield, FileCheck, Edit, Users, AlertTriangle, CheckCircle, X
} from 'lucide-vue-next'
import contractsApi from '@/services/contractsApi'
import apiService from '@/services/api'

// Utility functions
const formatCurrency = (value, currency = 'USD') => {
  if (!value || value === '') return 'Not specified'
  return `${currency} ${Number(value).toLocaleString()}`
}

const getStatusVariant = (status) => {
  switch (status) {
    case 'ACTIVE': return 'default'
    case 'DRAFT': return 'secondary'
    case 'UNDER_REVIEW': return 'warning'
    case 'APPROVED': return 'success'
    case 'REJECTED': return 'destructive'
    case 'EXPIRED': return 'secondary'
    default: return 'secondary'
  }
}

const router = useRouter()
const route = useRoute()

// State
const isLoading = ref(false)
const isSubmitting = ref(false) // Prevent double submission
const errors = ref({})
const successMessage = ref('')
const showRiskAnalysisNotification = ref(false)
const showRiskAnalysisTriggered = ref(false)

// Get contract data from route params or session storage
const contractData = ref({})
const contractTerms = ref([])
const contractClauses = ref([])
const users = ref([])
const legalReviewers = ref([])
const parentContract = ref({})
const isSubcontract = ref(false)
const allTermQuestionnaires = ref([]) // Store questionnaires loaded from sessionStorage
const selectedTemplates = ref({}) // Store selected template_id by term_id: { term_id: template_id }

// Methods
const goBack = () => {
  // Ensure data is stored in sessionStorage before navigating
  // This ensures the CreateContract page can restore the data
  const previewData = {
    contractData: contractData.value,
    contractTerms: contractTerms.value,
    contractClauses: contractClauses.value,
    isSubcontract: isSubcontract.value,
    parentContract: parentContract.value
  }
  sessionStorage.setItem('contractPreviewData', JSON.stringify(previewData))
  console.log('💾 Stored contract data in sessionStorage before navigating back:', previewData)
  
  // Navigate back to the appropriate page based on contract type
  if (isSubcontract.value && contractData.value.parent_contract_id) {
    router.push(`/contracts/${contractData.value.parent_contract_id}/subcontract`)
  } else {
    // For regular contracts, navigate back to create contract page
    // Use /contracts/create instead of /contracts/new for consistency
    // Add query parameter to indicate we're coming from preview
    router.push({
      path: '/contracts/create',
      query: { from: 'preview' }
    })
  }
}

const getContractOwnerName = () => {
  if (!contractData.value.contract_owner) return null
  const user = users.value.find(u => u.user_id === contractData.value.contract_owner)
  return user ? user.display_name : `User ${contractData.value.contract_owner}`
}

const getLegalReviewerName = () => {
  if (!contractData.value.legal_reviewer) return null
  const reviewer = legalReviewers.value.find(r => r.user_id === contractData.value.legal_reviewer)
  return reviewer ? reviewer.display_name : `User ${contractData.value.legal_reviewer}`
}

const getTermStatusVariant = (status) => {
  switch (status) {
    case 'Compliant': return 'default'
    case 'Non-Compliant': return 'destructive'
    case 'Under Review': return 'secondary'
    default: return 'outline'
  }
}

const getClauseTypeVariant = (type) => {
  switch (type) {
    case 'standard': return 'default'
    case 'risk': return 'destructive'
    case 'compliance': return 'secondary'
    case 'financial': return 'outline'
    default: return 'outline'
  }
}

const getRiskVariant = (risk) => {
  switch (risk) {
    case 'low': return 'default'
    case 'medium': return 'secondary'
    case 'high': return 'destructive'
    case 'critical': return 'destructive'
    default: return 'outline'
  }
}

// Trigger risk analysis in the background (non-blocking)
const triggerRiskAnalysis = async (contractId) => {
  try {
    console.log(`🔄 Triggering risk analysis for contract ${contractId} in background...`)
    
    // Show notification that risk analysis is being triggered
    showRiskAnalysisTriggered.value = true
    
    // Call the trigger endpoint using the contractsApi service (which includes auth headers)
    contractsApi.triggerContractRiskAnalysis(contractId)
      .then(data => {
        if (data.success) {
          console.log(`✅ Risk analysis triggered successfully for contract ${contractId}:`, data.message)
          // Hide the triggered notification and show the running notification
          showRiskAnalysisTriggered.value = false
          showRiskAnalysisNotification.value = true
        } else {
          console.warn(`⚠️ Failed to trigger risk analysis for contract ${contractId}:`, data.message)
          showRiskAnalysisTriggered.value = false
        }
      })
      .catch(error => {
        console.error(`❌ Error triggering risk analysis for contract ${contractId}:`, error)
        console.error(`❌ Error details:`, error.message)
        showRiskAnalysisTriggered.value = false
      })
    
    // Don't wait for the response - this is fire-and-forget
  } catch (error) {
    console.error(`❌ Error in triggerRiskAnalysis for contract ${contractId}:`, error)
    showRiskAnalysisTriggered.value = false
  }
}

const handleSubmit = async () => {
  // Prevent double submission
  if (isSubmitting.value) {
    console.log('⚠️ Submission already in progress, ignoring duplicate click')
    return
  }
  
  isSubmitting.value = true
  isLoading.value = true
  errors.value = {}
  
  try {
    if (isSubcontract.value) {
      // Handle subcontract submission
      const parentContractId = contractData.value.parent_contract_id
      if (!parentContractId) {
        errors.value.general = 'Parent contract ID is required for subcontract submission'
        return
      }
      
      // Check if parent contract needs to be updated to UNDER_REVIEW status
      if (parentContract.value && parentContract.value.status === 'DRAFT') {
        // Both contracts need to be submitted together
        console.log('Submitting both main contract and subcontract together')
        
        const mainContractDataToSubmit = {
          ...parentContract.value,
          status: 'PENDING_ASSIGNMENT',
          workflow_stage: 'under_review',
          contract_kind: 'MAIN' // Ensure contract_kind is set to a valid value
        }
        
        const subcontractDataToSubmit = {
          ...contractData.value,
          status: 'PENDING_ASSIGNMENT',
          workflow_stage: 'under_review',
          contract_kind: 'SUBCONTRACT' // Ensure contract_kind is set to a valid value
        }
        
        // Handle integer fields - convert empty strings to null
        if (!subcontractDataToSubmit.assigned_to || subcontractDataToSubmit.assigned_to === '') {
          subcontractDataToSubmit.assigned_to = null
        }
        if (!subcontractDataToSubmit.contract_owner || subcontractDataToSubmit.contract_owner === '') {
          subcontractDataToSubmit.contract_owner = null
        }
        if (!subcontractDataToSubmit.legal_reviewer || subcontractDataToSubmit.legal_reviewer === '') {
          subcontractDataToSubmit.legal_reviewer = null
        }
        
        // Convert JSON fields to proper format before sending
        if (subcontractDataToSubmit.insurance_requirements && typeof subcontractDataToSubmit.insurance_requirements === 'string') {
          if (subcontractDataToSubmit.insurance_requirements.trim()) {
            subcontractDataToSubmit.insurance_requirements = {
              requirements: subcontractDataToSubmit.insurance_requirements.trim(),
              type: 'text'
            }
          } else {
            subcontractDataToSubmit.insurance_requirements = {}
          }
        }
        
        if (subcontractDataToSubmit.data_protection_clauses && typeof subcontractDataToSubmit.data_protection_clauses === 'string') {
          if (subcontractDataToSubmit.data_protection_clauses.trim()) {
            subcontractDataToSubmit.data_protection_clauses = {
              clauses: subcontractDataToSubmit.data_protection_clauses.trim(),
              type: 'text'
            }
          } else {
            subcontractDataToSubmit.data_protection_clauses = {}
          }
        }
        
        // Remove fields that shouldn't be sent in update
        delete mainContractDataToSubmit.contract_id
        delete mainContractDataToSubmit.created_at
        delete mainContractDataToSubmit.updated_at
        
        console.log('🔍 Dual submission - subcontract data:', subcontractDataToSubmit)
        console.log('🔍 Dual submission - main contract data:', mainContractDataToSubmit)
        console.log('🔍 Dual submission - subcontract file_path (S3 URL):', subcontractDataToSubmit.file_path)
        console.log('🔍 Dual submission - main contract file_path (S3 URL):', mainContractDataToSubmit.file_path)
        
        const response = await contractsApi.createContractWithSubcontract(
          mainContractDataToSubmit, 
          subcontractDataToSubmit
        )
        
        if (response.success) {
          console.log('Both contracts submitted successfully:', response.data)
          
          // Save terms and clauses for both contracts
          // Note: The response should contain both contract IDs
          const mainContractId = response.data.main_contract?.contract_id
          const subcontractId = response.data.subcontract?.contract_id
          
          // Save terms and clauses for main contract if it has any
          if (mainContractId && contractTerms.value.length > 0) {
            await saveContractTerms(mainContractId)
          }
          
          if (mainContractId && contractClauses.value.length > 0) {
            await saveContractClauses(mainContractId)
          }
          
          // Save terms and clauses for subcontract if it has any
          if (subcontractId && contractTerms.value.length > 0) {
            await saveContractTerms(subcontractId)
          }
          
          if (subcontractId && contractClauses.value.length > 0) {
            await saveContractClauses(subcontractId)
          }
          
          // Show success message and risk analysis notification
          successMessage.value = 'Both contracts submitted for review successfully!'
          showRiskAnalysisNotification.value = true
          
          // Trigger risk analysis for both contracts in the background (non-blocking)
          if (mainContractId) {
            triggerRiskAnalysis(mainContractId)
          }
          if (subcontractId) {
            triggerRiskAnalysis(subcontractId)
          }
          
          // Clear session storage
          sessionStorage.removeItem('contractPreviewData')
          
          // Navigate to contract approval assignment page after a short delay
          setTimeout(() => {
            router.push({
              path: '/contract-approval-assignment',
              query: { 
                contractId: mainContractId,
                objectType: 'CONTRACT_CREATION'
              }
            })
          }, 2000)
        } else {
          errors.value.general = response.message || 'Failed to submit both contracts'
        }
      } else {
        // Only subcontract needs to be submitted
        const subcontractDataToSubmit = {
          ...contractData.value,
          status: 'PENDING_ASSIGNMENT',
          workflow_stage: 'under_review',
          contract_kind: 'SUBCONTRACT' // Ensure contract_kind is set to a valid value
        }
        
        // Handle integer fields - convert empty strings to null
        if (!subcontractDataToSubmit.assigned_to || subcontractDataToSubmit.assigned_to === '') {
          subcontractDataToSubmit.assigned_to = null
        }
        if (!subcontractDataToSubmit.contract_owner || subcontractDataToSubmit.contract_owner === '') {
          subcontractDataToSubmit.contract_owner = null
        }
        if (!subcontractDataToSubmit.legal_reviewer || subcontractDataToSubmit.legal_reviewer === '') {
          subcontractDataToSubmit.legal_reviewer = null
        }
        
        // Convert JSON fields to proper format before sending
        if (subcontractDataToSubmit.insurance_requirements && typeof subcontractDataToSubmit.insurance_requirements === 'string') {
          if (subcontractDataToSubmit.insurance_requirements.trim()) {
            subcontractDataToSubmit.insurance_requirements = {
              requirements: subcontractDataToSubmit.insurance_requirements.trim(),
              type: 'text'
            }
          } else {
            subcontractDataToSubmit.insurance_requirements = {}
          }
        }
        
        if (subcontractDataToSubmit.data_protection_clauses && typeof subcontractDataToSubmit.data_protection_clauses === 'string') {
          if (subcontractDataToSubmit.data_protection_clauses.trim()) {
            subcontractDataToSubmit.data_protection_clauses = {
              clauses: subcontractDataToSubmit.data_protection_clauses.trim(),
              type: 'text'
            }
          } else {
            subcontractDataToSubmit.data_protection_clauses = {}
          }
        }
        
        console.log('🔍 Final subcontract data being sent:', subcontractDataToSubmit)
        console.log('🔍 Final insurance_requirements:', subcontractDataToSubmit.insurance_requirements)
        console.log('🔍 Final data_protection_clauses:', subcontractDataToSubmit.data_protection_clauses)
        console.log('🔍 Final file_path (S3 URL):', subcontractDataToSubmit.file_path)
        
        const response = await contractsApi.createSubcontract(parentContractId, subcontractDataToSubmit)
        
        if (response.success) {
          // Save terms and clauses for subcontract
          if (contractTerms.value.length > 0) {
            await saveContractTerms(response.data.contract_id)
          }
          
          if (contractClauses.value.length > 0) {
            await saveContractClauses(response.data.contract_id)
          }
          
          // Show success message and risk analysis notification
          successMessage.value = 'Subcontract submitted for review successfully!'
          showRiskAnalysisNotification.value = true
          
          // Trigger risk analysis in the background (non-blocking)
          triggerRiskAnalysis(response.data.contract_id)
          
          // Clear session storage
          sessionStorage.removeItem('contractPreviewData')
          
          // Navigate to contract approval assignment page after a short delay
          setTimeout(() => {
            router.push({
              path: '/contract-approval-assignment',
              query: { 
                contractId: response.data.contract_id,
                objectType: 'SUBCONTRACT_CREATION'
              }
            })
          }, 2000)
        } else {
          errors.value.general = response.message || 'Failed to create subcontract'
        }
      }
    } else {
      // Handle regular contract submission
      const contractDataToSubmit = {
        ...contractData.value,
        status: 'PENDING_ASSIGNMENT',
        workflow_stage: 'under_review',
        contract_kind: 'MAIN' // Ensure contract_kind is set to a valid value
      }
      
      // Handle integer fields - convert empty strings to null
      if (!contractDataToSubmit.assigned_to || contractDataToSubmit.assigned_to === '') {
        contractDataToSubmit.assigned_to = null
      }
      if (!contractDataToSubmit.contract_owner || contractDataToSubmit.contract_owner === '') {
        contractDataToSubmit.contract_owner = null
      }
      if (!contractDataToSubmit.legal_reviewer || contractDataToSubmit.legal_reviewer === '') {
        contractDataToSubmit.legal_reviewer = null
      }
      
      console.log('🔍 Final contract data being sent:', contractDataToSubmit)
      console.log('🔍 Final file_path (S3 URL):', contractDataToSubmit.file_path)
      
      const response = await contractsApi.createContract(contractDataToSubmit)
      
        if (response.success) {
          // Save terms and clauses
          if (contractTerms.value.length > 0) {
            await saveContractTerms(response.data.contract_id)
          }
          
          if (contractClauses.value.length > 0) {
            await saveContractClauses(response.data.contract_id)
          }
          
          // Show success message and risk analysis notification
          successMessage.value = 'Contract submitted for review successfully!'
          showRiskAnalysisNotification.value = true
          
          // Trigger risk analysis in the background (non-blocking)
          triggerRiskAnalysis(response.data.contract_id)
          
          // Clear session storage
          sessionStorage.removeItem('contractPreviewData')
          
          // Redirect to contract approval assignment page after a short delay
          setTimeout(() => {
            router.push({
              path: '/contract-approval-assignment',
              query: { 
                contractId: response.data.contract_id,
                objectType: 'CONTRACT_CREATION'
              }
            })
          }, 2000)
        } else {
          errors.value.general = response.message || 'Failed to create contract'
        }
    }
  } catch (error) {
    console.error('Error submitting contract:', error)
    errors.value.general = error.message || 'Failed to submit contract for review'
  } finally {
    isLoading.value = false
    isSubmitting.value = false
  }
}

// Load questionnaires in background if missing from sessionStorage
async function loadQuestionnairesInBackground(terms) {
  try {
    const uniqueTermCategories = [...new Set(terms.map(t => t.term_category).filter(Boolean))]
    const loadPromises = uniqueTermCategories.map(termCategory =>
      apiService.getQuestionnairesByTermTitle(null, null, termCategory)
        .then(response => {
          const questionnaires = response.questionnaires || response.results || response || []
          return questionnaires.map(q => ({ 
            ...q, 
            term_category: termCategory,
            _matched_term_category: termCategory
          }))
        })
        .catch(error => {
          console.error(`Error loading questionnaires for category "${termCategory}":`, error)
          return []
        })
    )
    
    const results = await Promise.all(loadPromises)
    const allQuestionnaires = results.flat()
    
    // Remove duplicates
    const seenIds = new Set()
    const uniqueQuestionnaires = allQuestionnaires.filter(q => {
      if (seenIds.has(q.question_id)) return false
      seenIds.add(q.question_id)
      return true
    })
    
    allTermQuestionnaires.value = uniqueQuestionnaires
    console.log(`📋 Loaded ${uniqueQuestionnaires.length} questionnaires in background`)
  } catch (error) {
    console.error('Error loading questionnaires in background:', error)
  }
}

// Get questionnaires for a specific term (used when saving)
// Now uses selected template if available, otherwise falls back to direct questionnaires
const getQuestionnairesForTerm = async (termId, termCategory, termTitle) => {
  const termIdStr = String(termId || '')
  
  // First, check if a template is selected for this term
  const selectedTemplateId = selectedTemplates.value[termIdStr]
  if (selectedTemplateId) {
    try {
      console.log(`📋 Using selected template ${selectedTemplateId} for term ${termIdStr} in preview`)
      // When a template is selected, fetch ALL questions from that template
      // Don't pass term_id or term_category to get ALL questions (not filtered)
      const response = await apiService.getTemplateQuestions(selectedTemplateId, null, null)
      const questions = response.questions || []
      
      console.log(`✅ Retrieved ${questions.length} questions from template ${selectedTemplateId} in preview`)
      
      // Convert template questions to the format expected by backend
      const formattedQuestions = questions.map(q => {
        const questionType = mapAnswerTypeToQuestionType(q.answer_type || 'TEXT')
        return {
          question_id: q.question_id,
          question_text: q.question_text || '',
          question_type: questionType,
          is_required: q.is_required || false,
          scoring_weightings: q.weightage || 10.0,
          question_category: q.question_category || 'Contract',
          options: q.options || [],
          help_text: q.help_text || '',
          metric_name: q.metric_name || null,
          allow_document_upload: q.allow_document_upload || false,
          document_upload: q.allow_document_upload || false, // Map allow_document_upload to document_upload
          multiple_choice: questionType === 'multiple_choice' ? (q.options || []) : null, // Only set when question_type is multiple_choice
          template_id: selectedTemplateId // Include template_id for reference
        }
      })
      
      console.log(`📋 Returning ${formattedQuestions.length} formatted questions from selected template in preview`)
      return formattedQuestions
    } catch (error) {
      console.error(`❌ Error loading questions from template ${selectedTemplateId} in preview:`, error)
      // Don't fall back - if template is selected but fails to load, return empty
      // This prevents accidentally using wrong questionnaires
      return []
    }
  }
  
  // Fallback to direct questionnaires (legacy behavior)
  if (!allTermQuestionnaires.value.length) return []
  
  const searchTermId = String(termId || '')
  const searchTermCategory = termCategory || ''
  
  // Filter questionnaires that match this term
  const matchingQuestionnaires = allTermQuestionnaires.value.filter(q => {
    const qTermCategory = q.term_category || q._matched_term_category || ''
    const qTermId = String(q.term_id || '')
    
    // Match by term_category (case-insensitive) - PRIMARY METHOD
    if (searchTermCategory && qTermCategory.toLowerCase() === searchTermCategory.toLowerCase()) {
      return true
    }
    
    // Match by term_id (exact or partial match) - FALLBACK
    if (termId && (qTermId === searchTermId || 
                   qTermId.includes(searchTermId) || 
                   searchTermId.includes(qTermId))) {
      return true
    }
    
    return false
  })
  
  // Return questionnaires in the format expected by backend
  return matchingQuestionnaires.map(q => {
    const questionType = q.question_type || 'text'
    return {
      question_id: q.question_id,
      question_text: q.question_text || '',
      question_type: questionType,
      is_required: q.is_required || false,
      scoring_weightings: q.scoring_weightings || 10.0,
      question_category: q.question_category || 'Contract',
      options: q.options || [],
      help_text: q.help_text || '',
      metric_name: q.metric_name || null,
      allow_document_upload: q.allow_document_upload || false,
      document_upload: q.allow_document_upload || false, // Map allow_document_upload to document_upload
      multiple_choice: questionType === 'multiple_choice' ? (q.options || []) : null // Only set when question_type is multiple_choice
    }
  })
}

// Helper function to map answer_type to question_type (same as in CreateContract.vue)
function mapAnswerTypeToQuestionType(answerType) {
  const typeMap = {
    'TEXT': 'text',
    'TEXTAREA': 'textarea',
    'NUMBER': 'number',
    'BOOLEAN': 'boolean',
    'YES_NO': 'yes/no',
    'MULTIPLE_CHOICE': 'multiple_choice',
    'CHECKBOX': 'checkbox',
    'RATING': 'rating',
    'SCALE': 'scale',
    'DATE': 'date'
  }
  return typeMap[answerType?.toUpperCase()] || 'text'
}

const saveContractTerms = async (contractId) => {
  try {
    if (!contractTerms.value || !Array.isArray(contractTerms.value)) {
      return
    }
    
    console.log('🔍 Saving contract terms for contract ID:', contractId)
    console.log(`📋 Available questionnaires: ${allTermQuestionnaires.value.length}`)
    
    for (const [index, term] of contractTerms.value.entries()) {
      if (!term) continue
      
      // Get questionnaires for this term (from selected template or direct questionnaires)
      // Now supports template selection from CreateContract.vue
      const termQuestionnaires = await getQuestionnairesForTerm(term.term_id, term.term_category, term.term_title)
      console.log(`📋 Found ${termQuestionnaires.length} questionnaires for term ${index + 1} (${term.term_id || term.term_title})`)
      
      const termData = {
        term_id: term.term_id || `term_${Date.now()}_${index}`,
        term_category: term.term_category || '',
        term_title: term.term_title || '',
        term_text: term.term_text || '',
        risk_level: term.risk_level || 'Low',
        compliance_status: term.compliance_status || 'Pending',
        is_standard: Boolean(term.is_standard),
        approval_status: term.approval_status || 'Pending',
        version_number: term.version_number || '1.0',
        parent_term_id: term.parent_term_id || '',
        questionnaires: termQuestionnaires // Include questionnaires for this term
      }
      
      if (!termData.term_text || termData.term_text.trim() === '') {
        continue // Skip terms without text
      }
      
      console.log(`📤 Sending term ${index + 1} with ${termQuestionnaires.length} questionnaires`)
      await contractsApi.createContractTerms(contractId, termData)
    }
  } catch (error) {
    console.error('Error saving contract terms:', error)
    throw error
  }
}

const saveContractClauses = async (contractId) => {
  try {
    if (!contractClauses.value || !Array.isArray(contractClauses.value)) {
      return
    }
    
    for (const [index, clause] of contractClauses.value.entries()) {
      if (!clause) continue
      
      const clauseData = {
        clause_id: clause.clause_id || `clause_${Date.now()}`,
        clause_name: clause.clause_name || '',
        clause_type: clause.clause_type || 'standard',
        clause_text: clause.clause_text || '',
        risk_level: clause.risk_level || 'low',
        legal_category: clause.legal_category || '',
        version_number: clause.version_number || '1.0',
        is_standard: Boolean(clause.is_standard),
        notice_period_days: clause.notice_period_days || null,
        auto_renew: Boolean(clause.auto_renew),
        renewal_terms: clause.renewal_terms || '',
        termination_notice_period: clause.termination_notice_period || null,
        early_termination_fee: clause.early_termination_fee || null,
        termination_conditions: clause.termination_conditions || ''
      }
      
      if (!clauseData.clause_name || clauseData.clause_name.trim() === '') {
        continue // Skip clauses without name
      }
      
      if (!clauseData.clause_text || clauseData.clause_text.trim() === '') {
        continue // Skip clauses without text
      }
      
      await contractsApi.createContractClauses(contractId, clauseData)
    }
  } catch (error) {
    console.error('Error saving contract clauses:', error)
    throw error
  }
}

// Load data on mount
onMounted(async () => {
  try {
    // Load contract data from session storage or route params
    const storedData = sessionStorage.getItem('contractPreviewData')
    console.log('🔍 Raw stored data from sessionStorage:', storedData)
    
    if (storedData) {
      const data = JSON.parse(storedData)
      console.log('🔍 Parsed preview data:', data)
      console.log('🔍 Contract data keys:', Object.keys(data.contractData || {}))
      console.log('🔍 Contract title:', data.contractData?.contract_title)
      console.log('🔍 Contract type:', data.contractData?.contract_type)
      console.log('🔍 Contract value:', data.contractData?.contract_value)
      
      // Check if this is subcontract data
      if (data.isSubcontract) {
        isSubcontract.value = true
        contractData.value = data.subcontractData || {}
        parentContract.value = data.parentContract || {}
        console.log('🔍 Subcontract data:', contractData.value)
        console.log('🔍 Parent contract data:', parentContract.value)
        console.log('🔍 Contract title:', contractData.value.contract_title)
        console.log('🔍 Contract number:', contractData.value.contract_number)
        console.log('🔍 Vendor name:', contractData.value.vendor_name)
      } else {
        // Regular contract data
        contractData.value = data.contractData || {}
        parentContract.value = {}
        console.log('🔍 Regular contract data:', contractData.value)
      }
      
      contractTerms.value = data.contractTerms || []
      contractClauses.value = data.contractClauses || []
      allTermQuestionnaires.value = data.allTermQuestionnaires || []
      selectedTemplates.value = data.selectedTemplates || {} // Load selected templates
      console.log('🔍 Contract terms:', contractTerms.value)
      console.log('🔍 Contract clauses:', contractClauses.value)
      console.log(`📋 Loaded ${allTermQuestionnaires.value.length} questionnaires from sessionStorage`)
      console.log(`📋 Loaded selected templates:`, selectedTemplates.value)
      
      // If questionnaires are missing and we have terms, load them in background
      if (allTermQuestionnaires.value.length === 0 && contractTerms.value.length > 0) {
        console.log('📋 Questionnaires missing from sessionStorage, loading in background...')
        loadQuestionnairesInBackground(contractTerms.value)
      }
    } else {
      console.log('❌ No preview data found in sessionStorage')
    }
    
    // Load users and legal reviewers for display names
    const [usersResponse, legalReviewersResponse] = await Promise.all([
      contractsApi.getUsers(),
      contractsApi.getLegalReviewers()
    ])
    
    if (usersResponse.success) {
      users.value = usersResponse.data
    }
    
    if (legalReviewersResponse.success) {
      legalReviewers.value = legalReviewersResponse.data
    }
  } catch (error) {
    console.error('Error loading preview data:', error)
    errors.value.general = 'Failed to load contract preview data'
  }
})
</script>
