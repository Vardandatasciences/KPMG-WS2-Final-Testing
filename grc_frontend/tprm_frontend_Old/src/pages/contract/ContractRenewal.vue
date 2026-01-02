<template>
  <div class="space-y-6">
    <!-- Main Content -->
    <div>
      <!-- Header -->
      <div class="flex justify-between items-center">
        <div>
          <h1 class="text-3xl font-bold text-foreground">{{ pageTitle }}</h1>
          <p class="text-muted-foreground">{{ pageDescription }}</p>
        </div>
        <Button @click="go('/contracts')" variant="outline" class="gap-2">
          <ArrowLeft class="w-4 h-4" />
          Back to Contracts
        </Button>
      </div>

      <!-- Loading State -->
      <Card v-if="loading && !contract">
        <CardContent class="text-center py-12">
          <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p class="mt-4 text-muted-foreground">Loading contract information...</p>
        </CardContent>
      </Card>

      <!-- Contract Information -->
      <Card v-else-if="contract">
        <CardHeader>
          <CardTitle class="flex items-center gap-2">
            <FileText class="w-5 h-5" />
            Contract Information
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div>
              <Label class="text-sm font-medium text-muted-foreground">Contract Title</Label>
              <div class="text-sm font-medium">{{ contract.contract_title || 'N/A' }}</div>
            </div>
            <div>
              <Label class="text-sm font-medium text-muted-foreground">Contract Number</Label>
              <div class="text-sm font-medium">{{ contract.contract_number || 'N/A' }}</div>
            </div>
            <div>
              <Label class="text-sm font-medium text-muted-foreground">Vendor</Label>
              <div class="text-sm font-medium">{{ contract.vendor?.company_name || 'N/A' }}</div>
            </div>
            <div>
              <Label class="text-sm font-medium text-muted-foreground">Contract Value</Label>
              <div class="text-sm font-medium">
                ${{ (contract.contract_value || 0).toLocaleString() }} {{ contract.currency || 'USD' }}
              </div>
            </div>
            <div>
              <Label class="text-sm font-medium text-muted-foreground">Start Date</Label>
              <div class="text-sm font-medium">
                {{ contract.start_date ? new Date(contract.start_date).toLocaleDateString() : 'N/A' }}
              </div>
            </div>
            <div>
              <Label class="text-sm font-medium text-muted-foreground">End Date</Label>
              <div class="text-sm font-medium">
                {{ contract.end_date ? new Date(contract.end_date).toLocaleDateString() : 'N/A' }}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <!-- Renewal Form -->
      <Card>
        <CardHeader>
          <CardTitle class="flex items-center gap-2">
            <RefreshCw class="w-5 h-5" />
            Renewal Details
          </CardTitle>
          <CardDescription>
            {{ isViewMode ? 'View renewal information and status details' : 'Fill in the renewal information according to the contract_renewals table schema' }}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <!-- View Mode Template -->
          <div v-if="isViewMode" class="space-y-8">
            <!-- Renewal Overview Card -->
            <Card class="border-l-4 border-l-primary">
              <CardHeader class="pb-4">
                <div class="flex items-center justify-between">
                  <div>
                    <CardTitle class="text-xl flex items-center gap-2">
                      <RefreshCw class="w-5 h-5 text-primary" />
                      Renewal Overview
                    </CardTitle>
                    <CardDescription>Renewal ID: {{ renewalId }}</CardDescription>
                  </div>
                  <div class="flex items-center gap-2">
                    <span class="text-sm text-muted-foreground">Status:</span>
                    <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium"
                          :class="{
                            'bg-blue-100 text-blue-800 border border-blue-200': renewalForm.status === 'initiated',
                            'bg-yellow-100 text-yellow-800 border border-yellow-200': renewalForm.status === 'under_review',
                            'bg-green-100 text-green-800 border border-green-200': renewalForm.status === 'decision_made'
                          }">
                      {{ renewalForm.status?.replace('_', ' ').toUpperCase() || 'NOT SET' }}
                    </span>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div class="text-center p-4 bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg">
                    <div class="text-2xl font-bold text-blue-900">
                      {{ renewalForm.renewal_date ? new Date(renewalForm.renewal_date).toLocaleDateString() : 'N/A' }}
                    </div>
                    <div class="text-sm text-blue-700 font-medium">Renewal Date</div>
                  </div>
                  <div class="text-center p-4 bg-gradient-to-br from-green-50 to-green-100 rounded-lg">
                    <div class="text-2xl font-bold text-green-900">
                      {{ renewalForm.decision_due_date ? new Date(renewalForm.decision_due_date).toLocaleDateString() : 'N/A' }}
                    </div>
                    <div class="text-sm text-green-700 font-medium">Decision Due</div>
                  </div>
                  <div class="text-center p-4 bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg">
                    <div class="text-2xl font-bold text-purple-900">
                      {{ renewalForm.notification_sent_date ? new Date(renewalForm.notification_sent_date).toLocaleDateString() : 'N/A' }}
                    </div>
                    <div class="text-sm text-purple-700 font-medium">Notification Sent</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <!-- Decision Information Card -->
            <Card>
              <CardHeader>
                <CardTitle class="flex items-center gap-2">
                  <FileText class="w-5 h-5 text-primary" />
                  Decision Information
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div class="space-y-4">
                    <div>
                      <div class="text-sm font-medium text-muted-foreground mb-2">Renewal Decision</div>
                      <div class="flex items-center gap-2">
                        <span class="inline-flex items-center px-3 py-2 rounded-lg text-sm font-semibold"
                              :class="{
                                'bg-yellow-100 text-yellow-800 border border-yellow-300': renewalForm.renewal_decision === 'PENDING',
                                'bg-green-100 text-green-800 border border-green-300': renewalForm.renewal_decision === 'RENEW',
                                'bg-blue-100 text-blue-800 border border-blue-300': renewalForm.renewal_decision === 'RENEGOTIATE',
                                'bg-red-100 text-red-800 border border-red-300': renewalForm.renewal_decision === 'TERMINATE'
                              }">
                          {{ renewalForm.renewal_decision || 'Not Set' }}
                        </span>
                      </div>
                    </div>
                    <div>
                      <div class="text-sm font-medium text-muted-foreground mb-2">Decision Date</div>
                      <div class="text-lg font-semibold text-foreground">
                        {{ renewalForm.decision_date ? new Date(renewalForm.decision_date).toLocaleDateString() : 'Not Set' }}
                      </div>
                    </div>
                  </div>
                  <div class="space-y-4">
                    <div>
                      <div class="text-sm font-medium text-muted-foreground mb-2">Decided By</div>
                      <div class="flex items-center gap-2">
                        <div class="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center">
                          <span class="text-sm font-semibold text-primary">
                            {{ (getDisplayName(renewalForm.decided_by) || renewalForm.decided_by || 'N/A').charAt(0) }}
                          </span>
                        </div>
                        <div class="text-lg font-semibold text-foreground">
                          {{ getDisplayName(renewalForm.decided_by) || renewalForm.decided_by || 'Not Set' }}
                        </div>
                      </div>
                    </div>
                    <div>
                      <div class="text-sm font-medium text-muted-foreground mb-2">Initiated By</div>
                      <div class="flex items-center gap-2">
                        <div class="w-8 h-8 bg-secondary/10 rounded-full flex items-center justify-center">
                          <span class="text-sm font-semibold text-secondary-foreground">
                            {{ (getDisplayName(renewalForm.initiated_by) || renewalForm.initiated_by || 'N/A').charAt(0) }}
                          </span>
                        </div>
                        <div class="text-lg font-semibold text-foreground">
                          {{ getDisplayName(renewalForm.initiated_by) || renewalForm.initiated_by || 'Not Set' }}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <!-- Contract Details Card -->
            <Card>
              <CardHeader>
                <CardTitle class="flex items-center gap-2">
                  <FileText class="w-5 h-5 text-primary" />
                  Contract Details
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div class="bg-gradient-to-r from-slate-50 to-slate-100 p-6 rounded-lg">
                  <div class="text-center">
                    <div class="text-3xl font-bold text-slate-900 mb-2">
                      Contract #{{ renewalForm.renewed_contract_id || 'N/A' }}
                    </div>
                    <div class="text-sm text-slate-600">Renewed Contract ID</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <!-- Additional Information Card -->
            <Card>
              <CardHeader>
                <CardTitle class="flex items-center gap-2">
                  <FileText class="w-5 h-5 text-primary" />
                  Additional Information
                </CardTitle>
              </CardHeader>
              <CardContent class="space-y-6">
                <div>
                  <div class="text-sm font-medium text-muted-foreground mb-3">Renewal Reason</div>
                  <div class="bg-slate-50 p-4 rounded-lg border border-slate-200">
                    <p class="text-foreground leading-relaxed">
                      {{ renewalForm.renewal_reason || 'No reason provided' }}
                    </p>
                  </div>
                </div>
                
                <div>
                  <div class="text-sm font-medium text-muted-foreground mb-3">Comments</div>
                  <div class="bg-slate-50 p-4 rounded-lg border border-slate-200">
                    <p class="text-foreground leading-relaxed">
                      {{ renewalForm.comments || 'No comments provided' }}
                    </p>
                  </div>
                </div>

                <div v-if="renewalForm.renewal_documents">
                  <div class="text-sm font-medium text-muted-foreground mb-3">Renewal Documents</div>
                  <div class="bg-slate-50 p-4 rounded-lg border border-slate-200">
                    <div class="flex items-center gap-2">
                      <FileText class="w-4 h-4 text-muted-foreground" />
                      <span class="text-foreground font-mono text-sm">{{ renewalForm.renewal_documents }}</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <!-- Create Mode Form -->
          <form v-else @submit.prevent="handleSubmit" class="space-y-6">
            <!-- Basic Information -->
            <div class="space-y-4">
              <h3 class="text-lg font-semibold">Primary Information</h3>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label for="renewal_date">Renewal Date *</Label>
                  <Input
                    id="renewal_date"
                    v-model="renewalForm.renewal_date"
                    type="date"
                    :disabled="isViewMode"
                    :required="!isViewMode"
                    @input="onRenewalDateChange"
                  />
                  <p v-if="renewalForm.renewal_date" class="text-xs text-muted-foreground mt-1">
                    Selected date: {{ renewalForm.renewal_date }}
                  </p>
                </div>
                <div>
                  <Label for="notification_sent_date">Notification Sent Date</Label>
                  <Input
                    id="notification_sent_date"
                    v-model="renewalForm.notification_sent_date"
                    type="date"
                    :disabled="isViewMode"
                    @input="onNotificationDateChange"
                  />
                  <p v-if="renewalForm.notification_sent_date" class="text-xs text-muted-foreground mt-1">
                    Selected: {{ renewalForm.notification_sent_date }}
                  </p>
                </div>
                <div>
                  <Label for="decision_due_date">Decision Due Date</Label>
                  <Input
                    id="decision_due_date"
                    v-model="renewalForm.decision_due_date"
                    type="date"
                    :disabled="isViewMode"
                    @input="onDecisionDueDateChange"
                  />
                  <p v-if="renewalForm.decision_due_date" class="text-xs text-muted-foreground mt-1">
                    Selected: {{ renewalForm.decision_due_date }}
                  </p>
                </div>
                <div>
                  <Label for="renewal_decision">Renewal Decision</Label>
                  <Select v-model="renewalForm.renewal_decision" :disabled="isViewMode">
                    <SelectTrigger>
                      <SelectValue placeholder="Select decision" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="PENDING">Pending</SelectItem>
                      <SelectItem value="RENEW">Renew</SelectItem>
                      <SelectItem value="RENEGOTIATE">Renegotiate</SelectItem>
                      <SelectItem value="TERMINATE">Terminate</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>

            <!-- Contract Information -->
            <div class="space-y-4">
              <h3 class="text-lg font-semibold">Contract Information</h3>
              <div class="grid grid-cols-1 gap-4">
                <div>
                  <Label for="renewed_contract_id">Renewed Contract ID</Label>
                  <div class="text-sm font-medium text-muted-foreground bg-muted p-2 rounded-md">
                    {{ renewalForm.renewed_contract_id || contractId }} 
                    {{ isViewMode ? '(From renewal data)' : '(Auto-filled from selected contract)' }}
                  </div>
                </div>
              </div>
            </div>

            <!-- Decision Information -->
            <div class="space-y-4">
              <h3 class="text-lg font-semibold">Decision Information</h3>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label for="decided_by">Decided By</Label>
                  <Select v-model="renewalForm.decided_by" :disabled="isViewMode">
                    <SelectTrigger>
                      <SelectValue placeholder="Select user" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem 
                        v-for="user in users" 
                        :key="user.user_id" 
                        :value="user.user_id"
                      >
                        {{ user.display_name }} (ID: {{ user.user_id }})
                      </SelectItem>
                      <SelectItem v-if="users.length === 0" value="" disabled>
                        No users available
                      </SelectItem>
                    </SelectContent>
                  </Select>
                  <p v-if="users.length === 0" class="text-xs text-muted-foreground mt-1">
                    Unable to load users. You can enter the user ID manually in the form data.
                  </p>
                </div>
                <div>
                  <Label for="decision_date">Decision Date</Label>
                  <Input
                    id="decision_date"
                    v-model="renewalForm.decision_date"
                    type="date"
                    :disabled="isViewMode"
                    @input="onDecisionDateChange"
                  />
                  <p v-if="renewalForm.decision_date" class="text-xs text-muted-foreground mt-1">
                    Selected: {{ renewalForm.decision_date }}
                  </p>
                </div>
              </div>
            </div>

            <!-- Status and Reason -->
            <div class="space-y-4">
              <h3 class="text-lg font-semibold">Status and Reason</h3>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label for="status">Status</Label>
                  <Select v-model="renewalForm.status" :disabled="isViewMode">
                    <SelectTrigger>
                      <SelectValue placeholder="Select status" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="initiated">Initiated</SelectItem>
                      <SelectItem value="under_review">Under Review</SelectItem>
                      <SelectItem value="decision_made">Decision Made</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label for="initiated_by">Initiated By</Label>
                  <Select v-model="renewalForm.initiated_by" :disabled="isViewMode">
                    <SelectTrigger>
                      <SelectValue placeholder="Select user" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem 
                        v-for="user in users" 
                        :key="user.user_id" 
                        :value="user.user_id"
                      >
                        {{ user.display_name }} (ID: {{ user.user_id }})
                      </SelectItem>
                      <SelectItem v-if="users.length === 0" value="" disabled>
                        No users available
                      </SelectItem>
                    </SelectContent>
                  </Select>
                  <p v-if="users.length === 0" class="text-xs text-muted-foreground mt-1">
                    Unable to load users. You can enter the user ID manually in the form data.
                  </p>
                </div>
              </div>
              <div>
                <Label for="renewal_reason">Renewal Reason</Label>
                <Textarea
                  id="renewal_reason"
                  v-model="renewalForm.renewal_reason"
                  placeholder="Enter reason for renewal"
                  rows="3"
                  :disabled="isViewMode"
                  @input="onRenewalReasonChange"
                />
                <p v-if="renewalForm.renewal_reason" class="text-xs text-muted-foreground mt-1">
                  Entered: {{ renewalForm.renewal_reason }}
                </p>
              </div>
            </div>

            <!-- Comments and Documents -->
            <div class="space-y-4">
              <h3 class="text-lg font-semibold">Additional Information</h3>
              <div>
                <Label for="comments">Comments</Label>
                <Textarea
                  id="comments"
                  v-model="renewalForm.comments"
                  placeholder="Any comments regarding the renewal"
                  rows="3"
                  :disabled="isViewMode"
                  @input="onCommentsChange"
                />
                <p v-if="renewalForm.comments" class="text-xs text-muted-foreground mt-1">
                  Entered: {{ renewalForm.comments }}
                </p>
              </div>
              <div>
                <Label for="renewal_documents">Renewal Documents</Label>
                <Input
                  id="renewal_documents"
                  v-model="renewalForm.renewal_documents"
                  placeholder="Path or reference to renewal-related documents (JSON format)"
                  :disabled="isViewMode"
                />
                <p class="text-xs text-muted-foreground mt-1">
                  Enter as JSON array: ["document1.pdf", "document2.pdf"]
                </p>
              </div>
            </div>

            <!-- Form Actions -->
            <div v-if="!isViewMode" class="flex justify-end gap-4">
              <Button type="button" variant="outline" @click="go('/contracts')">
                Cancel
              </Button>
              <Button type="submit" :disabled="loading">
                <RefreshCw v-if="loading" class="w-4 h-4 mr-2 animate-spin" />
                {{ loading ? 'Creating Renewal...' : 'Create Renewal' }}
              </Button>
            </div>
            
            <!-- View Mode Actions -->
            <div v-else class="flex justify-end gap-4">
              <Button type="button" variant="outline" @click="go('/contracts')">
                Back to Contracts
              </Button>
              <Button type="button" @click="editRenewal" v-if="!isViewMode">
                Edit Renewal
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <!-- Error Display -->
      <div v-if="error" class="bg-destructive/10 border border-destructive/20 rounded-lg p-4">
        <div class="flex items-center gap-2">
          <AlertCircle class="w-4 h-4 text-destructive" />
          <span class="text-sm font-medium text-destructive">Error</span>
        </div>
        <p class="text-sm text-destructive mt-1">{{ error }}</p>
        <div class="mt-3">
          <Button 
            variant="outline" 
            size="sm" 
            @click="loadContract"
            :disabled="loading"
          >
            <RefreshCw v-if="loading" class="w-4 h-4 mr-2 animate-spin" />
            Retry
          </Button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { 
  Card, CardContent, CardDescription, CardHeader, CardTitle,
  Button, Input, Label, Textarea, Select, SelectContent, SelectItem, SelectTrigger, SelectValue
} from '@/components/ui_contract'
import { 
  FileText, RefreshCw, ArrowLeft, AlertCircle
} from 'lucide-vue-next'
import contractsApi from '../../services/contractsApi'
import loggingService from '@/services/loggingService'

const router = useRouter()
const route = useRoute()
const go = (path) => router.push(path)

// State
const loading = ref(false)
const error = ref(null)
const contract = ref(null)
const users = ref([])


// Renewal form data based on contract_renewals table schema
const renewalForm = ref({
  contract_id: null,
  renewal_date: '',
  notification_sent_date: '',
  decision_due_date: '',
  renewal_decision: 'PENDING',
  decided_by: '',
  decision_date: '',
  comments: '',
  initiated_by: '',
  initiated_date: '',
  renewal_reason: '',
  renewal_documents: '',
  status: 'initiated',
  renewed_contract_id: null // Will be set automatically to the current contract ID
})

// Computed
const contractId = computed(() => {
  const id = route.params.id || route.query.contractId || route.query.id
  console.log('🔍 ContractRenewal - Computed contractId:', id)
  return id
})

const renewalId = computed(() => {
  const id = route.params.renewalId
  console.log('🔍 ContractRenewal - Computed renewalId:', id)
  return id
})

const isViewMode = computed(() => {
  return !!renewalId.value
})

const pageTitle = computed(() => {
  return isViewMode.value ? 'View Contract Renewal' : 'Contract Renewal'
})

const pageDescription = computed(() => {
  return isViewMode.value ? 'View renewal details and status' : 'Initiate renewal process for contract'
})

// Watchers
watch(() => renewalForm.value.renewal_date, (newValue, oldValue) => {
  console.log('🔍 ContractRenewal - renewal_date changed:', { oldValue, newValue, type: typeof newValue })
})

watch(() => renewalForm.value.notification_sent_date, (newValue, oldValue) => {
  console.log('🔍 ContractRenewal - notification_sent_date changed:', { oldValue, newValue, type: typeof newValue })
})

watch(() => renewalForm.value.decision_due_date, (newValue, oldValue) => {
  console.log('🔍 ContractRenewal - decision_due_date changed:', { oldValue, newValue, type: typeof newValue })
})

watch(() => renewalForm.value.decision_date, (newValue, oldValue) => {
  console.log('🔍 ContractRenewal - decision_date changed:', { oldValue, newValue, type: typeof newValue })
})

watch(() => renewalForm.value.comments, (newValue, oldValue) => {
  console.log('🔍 ContractRenewal - comments changed:', { oldValue, newValue, type: typeof newValue })
})

watch(() => renewalForm.value.renewal_reason, (newValue, oldValue) => {
  console.log('🔍 ContractRenewal - renewal_reason changed:', { oldValue, newValue, type: typeof newValue })
})

// Methods
const loadContract = async () => {
  console.log('🔍 ContractRenewal - Route params:', route.params)
  console.log('🔍 ContractRenewal - Route query:', route.query)
  console.log('🔍 ContractRenewal - Contract ID:', contractId.value)
  console.log('🔍 ContractRenewal - Is view mode:', isViewMode.value)
  
  if (!contractId.value && !isViewMode.value) {
    error.value = `Contract ID is required. Current route: ${route.path}, Params: ${JSON.stringify(route.params)}, Query: ${JSON.stringify(route.query)}`
    return
  }
  
  // In view mode, contract loading is handled by loadRenewalDetails
  if (isViewMode.value) {
    console.log('🔍 ContractRenewal - Skipping loadContract in view mode')
    return
  }

  try {
    loading.value = true
    error.value = null
    const response = await contractsApi.getContract(contractId.value)
    
    if (response.success) {
      contract.value = response.data
      renewalForm.value.contract_id = parseInt(contractId.value)
      renewalForm.value.renewed_contract_id = parseInt(contractId.value)
    } else {
      throw new Error(response.message || 'Failed to load contract')
    }
  } catch (err) {
    console.error('Error loading contract:', err)
    error.value = err.message || 'Failed to load contract. Please check your connection and try again.'
  } finally {
    loading.value = false
  }
}

const loadRenewalDetails = async () => {
  console.log('🔍 ContractRenewal - Loading renewal details for ID:', renewalId.value)
  
  if (!renewalId.value) {
    error.value = 'Renewal ID is required'
    return
  }

  try {
    loading.value = true
    error.value = null
    const response = await contractsApi.getContractRenewal(renewalId.value)
    
    if (response.success) {
      const renewalData = response.data
      console.log('🔍 ContractRenewal - Loaded renewal data:', renewalData)
      
      // Helper function to format date for input[type="date"]
      const formatDateForInput = (dateString) => {
        if (!dateString) return ''
        try {
          const date = new Date(dateString)
          if (isNaN(date.getTime())) return ''
          return date.toISOString().split('T')[0] // Returns YYYY-MM-DD format
        } catch (e) {
          console.warn('Error formatting date:', dateString, e)
          return ''
        }
      }
      
      // Populate the form with renewal data
      renewalForm.value = {
        contract_id: renewalData.contract_id,
        renewal_date: formatDateForInput(renewalData.renewal_date),
        notification_sent_date: formatDateForInput(renewalData.notification_sent_date),
        decision_due_date: formatDateForInput(renewalData.decision_due_date),
        renewal_decision: renewalData.renewal_decision || 'PENDING',
        decided_by: renewalData.decided_by || '',
        decision_date: formatDateForInput(renewalData.decision_date),
        comments: renewalData.comments || '',
        initiated_by: renewalData.initiated_by || '',
        initiated_date: renewalData.initiated_date || '',
        renewal_reason: renewalData.renewal_reason || '',
        renewal_documents: renewalData.renewal_documents || '',
        status: renewalData.status || 'initiated',
        renewed_contract_id: renewalData.renewed_contract_id
      }
      
      console.log('🔍 ContractRenewal - Formatted renewal form data:', renewalForm.value)
      
      // Debug user data
      console.log('🔍 ContractRenewal - Users loaded:', users.value.length)
      console.log('🔍 ContractRenewal - Decided by ID:', renewalData.decided_by)
      console.log('🔍 ContractRenewal - Initiated by ID:', renewalData.initiated_by)
      
      // Find user names for display
      if (users.value.length > 0) {
        const decidedByUser = users.value.find(u => u.user_id === renewalData.decided_by)
        const initiatedByUser = users.value.find(u => u.user_id === renewalData.initiated_by)
        console.log('🔍 ContractRenewal - Decided by user:', decidedByUser)
        console.log('🔍 ContractRenewal - Initiated by user:', initiatedByUser)
      }
      
      // Load the associated contract
      if (renewalData.contract_id) {
        console.log('🔍 ContractRenewal - Loading associated contract:', renewalData.contract_id)
        // Set the contract ID for loading
        contract.value = null // Reset contract first
        try {
          const response = await contractsApi.getContract(renewalData.contract_id)
          console.log('🔍 ContractRenewal - Contract API response:', response)
          if (response.success) {
            contract.value = response.data
            console.log('🔍 ContractRenewal - Loaded associated contract:', contract.value)
            console.log('🔍 ContractRenewal - Contract title:', contract.value?.contract_title)
            console.log('🔍 ContractRenewal - Contract value:', contract.value?.contract_value)
          } else {
            console.warn('🔍 ContractRenewal - Failed to load associated contract:', response.message)
            // Set a fallback contract object
            contract.value = {
              contract_title: 'Contract not found',
              contract_number: 'N/A',
              contract_value: 0,
              currency: 'USD',
              vendor: { company_name: 'N/A' },
              start_date: null,
              end_date: null
            }
          }
        } catch (err) {
          console.error('Error loading associated contract:', err)
          // Set a fallback contract object
          contract.value = {
            contract_title: 'Error loading contract',
            contract_number: 'N/A',
            contract_value: 0,
            currency: 'USD',
            vendor: { company_name: 'N/A' },
            start_date: null,
            end_date: null
          }
        }
      } else {
        console.warn('🔍 ContractRenewal - No contract_id in renewal data')
      }
    } else {
      throw new Error(response.message || 'Failed to load renewal details')
    }
  } catch (err) {
    console.error('Error loading renewal details:', err)
    error.value = err.message || 'Failed to load renewal details. Please check your connection and try again.'
  } finally {
    loading.value = false
  }
}

const loadUsers = async () => {
  try {
    console.log('🔍 ContractRenewal - Loading users...')
    console.log('🔍 ContractRenewal - Token in localStorage:', localStorage.getItem('session_token'))
    
    const response = await contractsApi.getUsers()
    
    console.log('🔍 ContractRenewal - Users API response:', response)
    
    if (response.success) {
      users.value = response.data || []
      console.log('🔍 ContractRenewal - Loaded users:', users.value.length, users.value)
    } else {
      console.warn('Failed to load users:', response.message)
      users.value = []
    }
  } catch (err) {
    console.error('Error loading users:', err)
    console.error('Error details:', {
      message: err.message,
      status: err.response?.status,
      statusText: err.response?.statusText,
      data: err.response?.data
    })
    // Don't show error for users, just use empty array
    users.value = []
  }
}


const onRenewalDateChange = (event) => {
  console.log('🔍 ContractRenewal - Date input changed:', event.target.value)
  renewalForm.value.renewal_date = event.target.value
}

const onNotificationDateChange = (event) => {
  console.log('🔍 ContractRenewal - Notification date input changed:', event.target.value)
  renewalForm.value.notification_sent_date = event.target.value
}

const onDecisionDueDateChange = (event) => {
  console.log('🔍 ContractRenewal - Decision due date input changed:', event.target.value)
  renewalForm.value.decision_due_date = event.target.value
}

const onDecisionDateChange = (event) => {
  console.log('🔍 ContractRenewal - Decision date input changed:', event.target.value)
  renewalForm.value.decision_date = event.target.value
}

const onCommentsChange = (event) => {
  console.log('🔍 ContractRenewal - Comments input changed:', event.target.value)
  renewalForm.value.comments = event.target.value
}

const onRenewalReasonChange = (event) => {
  console.log('🔍 ContractRenewal - Renewal reason input changed:', event.target.value)
  renewalForm.value.renewal_reason = event.target.value
}

const editRenewal = () => {
  // Switch to edit mode by removing the renewalId from the route
  router.push(`/contracts/${contractId.value}/renewal`)
}

const getDisplayName = (userId) => {
  if (!userId || !users.value.length) return null
  const user = users.value.find(u => u.user_id === userId)
  return user ? (user.display_name || user.username) : null
}

const handleSubmit = async () => {
  try {
    loading.value = true
    error.value = null

    // Prepare form data
    const formData = { ...renewalForm.value }
    
    // Debug: Log renewal_date value with more details
    console.log('🔍 ContractRenewal - renewal_date value:', formData.renewal_date, 'type:', typeof formData.renewal_date, 'length:', formData.renewal_date?.length, 'truthy:', !!formData.renewal_date)
    
    // Debug: Log the problematic fields before conversion
    console.log('🔍 ContractRenewal - Before conversion:')
    console.log('  notification_sent_date:', formData.notification_sent_date, 'type:', typeof formData.notification_sent_date, 'length:', formData.notification_sent_date?.length)
    console.log('  decision_due_date:', formData.decision_due_date, 'type:', typeof formData.decision_due_date, 'length:', formData.decision_due_date?.length)
    console.log('  decision_date:', formData.decision_date, 'type:', typeof formData.decision_date, 'length:', formData.decision_date?.length)
    console.log('  comments:', formData.comments, 'type:', typeof formData.comments, 'length:', formData.comments?.length)
    console.log('  renewal_reason:', formData.renewal_reason, 'type:', typeof formData.renewal_reason, 'length:', formData.renewal_reason?.length)
    
    // Debug: Log the current form state
    console.log('🔍 ContractRenewal - Current form state:', renewalForm.value)
    
    // Ensure renewal_date is set (required field) - check before converting empty strings
    if (!formData.renewal_date || formData.renewal_date.trim() === '') {
      throw new Error(`Renewal date is required. Current value: "${formData.renewal_date}" (type: ${typeof formData.renewal_date})`)
    }
    
    // Ensure contract_id is set
    formData.contract_id = parseInt(contractId.value)
    
    // renewed_contract_id is automatically set to the current contract ID
    formData.renewed_contract_id = parseInt(contractId.value)
    
    // Convert empty strings to null for optional fields (excluding required fields)
    const requiredFields = ['renewal_date', 'contract_id', 'renewed_contract_id']
    Object.keys(formData).forEach(key => {
      // Only convert to null if the field is truly empty (empty string or whitespace)
      if (formData[key] === '' || (typeof formData[key] === 'string' && formData[key].trim() === '')) {
        if (!requiredFields.includes(key)) {
          formData[key] = null
        }
      }
    })
    
    // Debug: Log the problematic fields after conversion
    console.log('🔍 ContractRenewal - After conversion:')
    console.log('  notification_sent_date:', formData.notification_sent_date, 'type:', typeof formData.notification_sent_date)
    console.log('  decision_due_date:', formData.decision_due_date, 'type:', typeof formData.decision_due_date)
    console.log('  decision_date:', formData.decision_date, 'type:', typeof formData.decision_date)
    console.log('  comments:', formData.comments, 'type:', typeof formData.comments)
    console.log('  renewal_reason:', formData.renewal_reason, 'type:', typeof formData.renewal_reason)
    
    // Convert user IDs to integers
    if (formData.decided_by) {
      formData.decided_by = parseInt(formData.decided_by)
    }
    if (formData.initiated_by) {
      formData.initiated_by = parseInt(formData.initiated_by)
    }

    // Parse renewal_documents if it's a string
    if (formData.renewal_documents && typeof formData.renewal_documents === 'string') {
      try {
        formData.renewal_documents = JSON.parse(formData.renewal_documents)
      } catch (e) {
        // If it's not valid JSON, treat it as a single document
        formData.renewal_documents = [formData.renewal_documents]
      }
    }

    // Debug: Log the data being sent
    console.log('🔍 ContractRenewal - Sending data:', formData)

    const response = await contractsApi.createContractRenewal(formData)
    
    if (response.success) {
      // Redirect to contracts page with success message
      router.push({
        path: '/contracts',
        query: { 
          message: 'Contract renewal created successfully',
          type: 'success'
        }
      })
    } else {
      throw new Error(response.message || 'Failed to create renewal')
    }
  } catch (err) {
    console.error('Error creating renewal:', err)
    error.value = err.message || 'Failed to create renewal'
  } finally {
    loading.value = false
  }
}

// Lifecycle
onMounted(async () => {
  await loggingService.logPageView('Contract', 'Contract Renewal')
  console.log('🔍 ContractRenewal - onMounted - Mode:', isViewMode.value ? 'VIEW' : 'CREATE')
  console.log('🔍 ContractRenewal - onMounted - Route:', route.path)
  console.log('🔍 ContractRenewal - onMounted - Params:', route.params)
  
  // Authentication check removed - no login required for renewal page
  
  await loadUsers()
  
  // Load data based on mode
  if (isViewMode.value) {
    console.log('🔍 ContractRenewal - Loading renewal details for ID:', renewalId.value)
    await loadRenewalDetails()
  } else {
    console.log('🔍 ContractRenewal - Loading contract for ID:', contractId.value)
    await loadContract()
  }
  
  // Debug: Log initial form data
  console.log('🔍 ContractRenewal - Initial form data:', renewalForm.value)
  console.log('🔍 ContractRenewal - Mode:', isViewMode.value ? 'VIEW' : 'CREATE')
})
</script>
