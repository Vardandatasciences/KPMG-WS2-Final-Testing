<template>
  <div class="contract-review-container">
    <!-- Header Section -->
    <div class="review-header">
      <div class="header-content">
        <div class="header-left">
          <button @click="goBack" class="back-button">
            <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
            </svg>
            Back
          </button>
          <div class="header-text">
            <h1 class="review-title">Contract Review & Edit</h1>
            <p class="review-subtitle">Review and make changes to the contract before approval</p>
          </div>
        </div>
        <div class="header-actions">
          <div class="approval-info">
            <span class="approval-status" :class="`status-${approval?.status?.toLowerCase()}`">
              {{ approval?.status?.replace('_', ' ') || 'Loading...' }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="loading-state">
      <div class="loading-spinner"></div>
      <h4>Loading contract details...</h4>
      <p>Please wait while we fetch the contract information</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-state">
      <div class="error-icon">
        <svg class="h-16 w-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"/>
        </svg>
      </div>
      <h4>Error Loading Contract</h4>
      <p>{{ error }}</p>
      <button @click="fetchContractDetails" class="retry-btn">
        <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
        </svg>
        Try Again
      </button>
    </div>

    <!-- Main Content -->
    <div v-else-if="contract" class="review-content">
      <!-- Contract Information -->
      <div class="contract-info-section">
        <div class="section-header">
          <h2 class="section-title">Contract Information</h2>
        </div>
        <div class="contract-details">
          <div class="detail-grid">
            <div class="detail-item">
              <label class="detail-label">Contract Title</label>
              <input 
                v-model="contractData.contract_title" 
                class="detail-input"
                type="text"
              />
            </div>
            <div class="detail-item">
              <label class="detail-label">Contract Number</label>
              <input 
                v-model="contractData.contract_number" 
                class="detail-input"
                type="text"
              />
            </div>
            <div class="detail-item">
              <label class="detail-label">Contract Type</label>
              <select v-model="contractData.contract_type" class="detail-select">
                <option value="SERVICE">Service</option>
                <option value="SUPPLY">Supply</option>
                <option value="CONSULTING">Consulting</option>
                <option value="MAINTENANCE">Maintenance</option>
                <option value="OTHER">Other</option>
              </select>
            </div>
            <div class="detail-item">
              <label class="detail-label">Status</label>
              <select v-model="contractData.status" class="detail-select">
                <option value="DRAFT">Draft</option>
                <option value="PENDING_ASSIGNMENT">Pending Assignment</option>
                <option value="UNDER_REVIEW">Under Review</option>
                <option value="APPROVED">Approved</option>
                <option value="REJECTED">Rejected</option>
              </select>
            </div>
            <div class="detail-item">
              <label class="detail-label">Start Date</label>
              <input 
                v-model="contractData.start_date" 
                class="detail-input"
                type="date"
              />
            </div>
            <div class="detail-item">
              <label class="detail-label">End Date</label>
              <input 
                v-model="contractData.end_date" 
                class="detail-input"
                type="date"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Contract Terms -->
      <div class="contract-terms-section">
        <div class="section-header">
          <h2 class="section-title">Contract Terms</h2>
          <button @click="addTerm" class="add-button">
            <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
            </svg>
            Add Term
          </button>
        </div>
        <div class="terms-list">
          <div v-for="(term, index) in contractTerms" :key="term.term_id || index" class="term-item">
            <div class="term-header">
              <h3 class="term-title">Term {{ index + 1 }}</h3>
              <button @click="removeTerm(index)" class="remove-button">
                <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                </svg>
              </button>
            </div>
            <div class="term-fields">
              <div class="term-field">
                <label class="term-label">Category</label>
                <select v-model="term.term_category" class="term-input">
                  <option value="Payment">Payment</option>
                  <option value="Delivery">Delivery</option>
                  <option value="Performance">Performance</option>
                  <option value="Liability">Liability</option>
                  <option value="Termination">Termination</option>
                  <option value="Intellectual Property">Intellectual Property</option>
                  <option value="Confidentiality">Confidentiality</option>
                  <option value="Other">Other</option>
                </select>
              </div>
              <div class="term-field">
                <label class="term-label">Title</label>
                <input v-model="term.term_title" class="term-input" type="text" />
              </div>
              <div class="term-field">
                <label class="term-label">Risk Level</label>
                <select v-model="term.risk_level" class="term-input">
                  <option value="Low">Low</option>
                  <option value="Medium">Medium</option>
                  <option value="High">High</option>
                  <option value="Urgent">Urgent</option>
                </select>
              </div>
              <div class="term-field">
                <label class="term-label">Compliance Status</label>
                <select v-model="term.compliance_status" class="term-input">
                  <option value="Pending">Pending</option>
                  <option value="Compliant">Compliant</option>
                  <option value="Non-Compliant">Non-Compliant</option>
                  <option value="Under Review">Under Review</option>
                  <option value="pending_review">Pending Review</option>
                </select>
              </div>
              <div class="term-field">
                <label class="term-label">Approval Status</label>
                <select v-model="term.approval_status" class="term-input">
                  <option value="Pending">Pending</option>
                  <option value="Approved">Approved</option>
                  <option value="Rejected">Rejected</option>
                  <option value="Under Review">Under Review</option>
                </select>
              </div>
              <div class="term-field">
                <label class="term-label">Version</label>
                <input v-model="term.version_number" class="term-input" type="text" />
              </div>
              <div class="term-field">
                <label class="term-label">Standard Term</label>
                <input v-model="term.is_standard" class="term-checkbox" type="checkbox" />
              </div>
              <div class="term-field term-field--full">
                <label class="term-label">Term Text</label>
                <textarea v-model="term.term_text" class="term-textarea" rows="4"></textarea>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Contract Clauses -->
      <div class="contract-clauses-section">
        <div class="section-header">
          <h2 class="section-title">Contract Clauses</h2>
          <button @click="addClause" class="add-button">
            <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
            </svg>
            Add Clause
          </button>
        </div>
        <div class="clauses-list">
          <div v-for="(clause, index) in contractClauses" :key="clause.clause_id || index" class="clause-item">
            <div class="clause-header">
              <h3 class="clause-title">Clause {{ index + 1 }}</h3>
              <button @click="removeClause(index)" class="remove-button">
                <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                </svg>
              </button>
            </div>
            <div class="clause-fields">
              <div class="clause-field">
                <label class="clause-label">Type</label>
                <select v-model="clause.clause_type" class="clause-input">
                  <option value="standard">Standard</option>
                  <option value="risk">Risk</option>
                  <option value="compliance">Compliance</option>
                  <option value="financial">Financial</option>
                  <option value="operational">Operational</option>
                  <option value="renewal">Renewal</option>
                  <option value="termination">Termination</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div class="clause-field">
                <label class="clause-label">Name</label>
                <input v-model="clause.clause_name" class="clause-input" type="text" />
              </div>
              <div class="clause-field">
                <label class="clause-label">Risk Level</label>
                <select v-model="clause.risk_level" class="clause-input">
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                  <option value="urgent">Urgent</option>
                </select>
              </div>
              <div class="clause-field">
                <label class="clause-label">Legal Category</label>
                <input v-model="clause.legal_category" class="clause-input" type="text" />
              </div>
              <div class="clause-field">
                <label class="clause-label">Version</label>
                <input v-model="clause.version_number" class="clause-input" type="text" />
              </div>
              <div class="clause-field">
                <label class="clause-label">Status</label>
                <select v-model="clause.status" class="clause-input">
                  <option value="Pending">Pending</option>
                  <option value="Approved">Approved</option>
                  <option value="Rejected">Rejected</option>
                  <option value="Under Review">Under Review</option>
                </select>
              </div>
              <div class="clause-field">
                <label class="clause-label">Standard Clause</label>
                <input v-model="clause.is_standard" class="clause-checkbox" type="checkbox" />
              </div>
              <div class="clause-field">
                <label class="clause-label">Notice Period (Days)</label>
                <input v-model="clause.notice_period_days" class="clause-input" type="number" />
              </div>
              <div class="clause-field">
                <label class="clause-label">Auto Renew</label>
                <input v-model="clause.auto_renew" class="clause-checkbox" type="checkbox" />
              </div>
              <div class="clause-field">
                <label class="clause-label">Termination Notice (Days)</label>
                <input v-model="clause.termination_notice_period" class="clause-input" type="number" />
              </div>
              <div class="clause-field">
                <label class="clause-label">Early Termination Fee</label>
                <input v-model="clause.early_termination_fee" class="clause-input" type="number" step="0.01" />
              </div>
              <div class="clause-field clause-field--full">
                <label class="clause-label">Clause Text</label>
                <textarea v-model="clause.clause_text" class="clause-textarea" rows="4"></textarea>
              </div>
              <div class="clause-field clause-field--full">
                <label class="clause-label">Renewal Terms</label>
                <textarea v-model="clause.renewal_terms" class="clause-textarea" rows="2"></textarea>
              </div>
              <div class="clause-field clause-field--full">
                <label class="clause-label">Termination Conditions</label>
                <textarea v-model="clause.termination_conditions" class="clause-textarea" rows="2"></textarea>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Subcontracts Section -->
      <div v-if="subContracts.length > 0" class="subcontracts-section">
        <div class="section-header">
          <h2 class="section-title">Subcontracts</h2>
          <div class="subcontract-count">{{ subContracts.length }} subcontract(s)</div>
        </div>
        <div class="subcontracts-list">
          <div v-for="(subcontract, index) in subContracts" :key="subcontract.contract_id" class="subcontract-item">
            <div class="subcontract-header">
              <h3 class="subcontract-title">{{ subcontract.contract_title || `Subcontract ${index + 1}` }}</h3>
              <div class="subcontract-status" :class="`status-${subcontract.status?.toLowerCase()}`">
                {{ subcontract.status?.replace('_', ' ') }}
              </div>
            </div>
            <div class="subcontract-details">
              <div class="subcontract-info">
                <div class="info-item">
                  <span class="info-label">Contract Number:</span>
                  <span class="info-value">{{ subcontract.contract_number }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">Type:</span>
                  <span class="info-value">{{ subcontract.contract_type }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">Start Date:</span>
                  <span class="info-value">{{ subcontract.start_date }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">End Date:</span>
                  <span class="info-value">{{ subcontract.end_date }}</span>
                </div>
              </div>
              <div class="subcontract-summary">
                <div class="summary-item">
                  <span class="summary-label">Terms:</span>
                  <span class="summary-value">{{ subcontract.terms_count || 0 }}</span>
                </div>
                <div class="summary-item">
                  <span class="summary-label">Clauses:</span>
                  <span class="summary-value">{{ subcontract.clauses_count || 0 }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Comments Section -->
      <div class="comments-section">
        <div class="section-header">
          <h2 class="section-title">Review Comments</h2>
        </div>
        <div class="comments-list">
          <div v-for="comment in existingComments" :key="comment.approval_id" class="comment-item">
            <div class="comment-header">
              <div class="comment-author">{{ comment.assignee_name || comment.assigner_name || 'Unknown User' }}</div>
              <div class="comment-date">{{ formatDate(comment.created_at) }}</div>
            </div>
            <div class="comment-content">{{ comment.comment_text }}</div>
          </div>
        </div>
        <div class="comment-form">
          <label class="comment-label">Add Review Comment</label>
          <textarea 
            v-model="reviewComment" 
            class="comment-textarea"
            placeholder="Enter your review comments here..."
            rows="4"
          ></textarea>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="action-buttons">
        <button @click="approveContract" class="action-btn action-btn--approve" :disabled="isSubmitting">
          <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
          Approve Contract
        </button>
      </div>
    </div>
  </div>

  <!-- Popup Modal -->
  <PopupModal />
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStore } from 'vuex'
import contractsApi from '../../services/contractsApi'
import contractApprovalApi from '../../services/contractApprovalApi'
import PopupModal from '@/popup/PopupModal.vue'
import { PopupService } from '@/popup/popupService'
import loggingService from '@/services/loggingService'

export default {
  name: 'ContractReviewEdit',
  components: {
    PopupModal
  },
  setup() {
    const route = useRoute()
    const router = useRouter()
    const store = useStore()
    
    // Reactive data
    const contract = ref(null)
    const contractData = ref({})
    const contractTerms = ref([])
    const contractClauses = ref([])
    const subContracts = ref([])
    const existingComments = ref([])
    const reviewComment = ref('')
    const approval = ref(null)
    const isLoading = ref(false)
    const isSubmitting = ref(false)
    const error = ref(null)
    
    // Methods
    const fetchContractDetails = async () => {
      isLoading.value = true
      error.value = null
      
      try {
        const contractId = route.params.contractId
        
        // Fetch comprehensive contract details (contract, terms, clauses, sub-contracts)
        console.log(`[FRONTEND] Fetching comprehensive contract details for ID: ${contractId}`)
        
        // Check authentication token
        const token = localStorage.getItem('session_token')
        console.log(`[FRONTEND] Auth token present: ${!!token}`)
        console.log(`[FRONTEND] Token preview: ${token ? token.substring(0, 20) + '...' : 'None'}`)
        
        const comprehensiveResponse = await contractsApi.getContractComprehensive(contractId)
        console.log('[FRONTEND] Comprehensive API response:', comprehensiveResponse)
        
        if (comprehensiveResponse.success) {
          const data = comprehensiveResponse.data
          contract.value = data.contract
          contractData.value = { ...data.contract }
          contractTerms.value = data.terms || []
          contractClauses.value = data.clauses || []
          subContracts.value = data.sub_contracts || []
          
          console.log('[FRONTEND] Comprehensive contract data loaded:', {
            contract: data.contract,
            terms: data.terms?.length || 0,
            clauses: data.clauses?.length || 0,
            subContracts: data.sub_contracts?.length || 0,
            summary: data.summary,
            termsData: data.terms,
            clausesData: data.clauses
          })
          
          // Debug: Log first term and clause to see field structure
          if (data.terms && data.terms.length > 0) {
            console.log('[FRONTEND] First term structure:', data.terms[0])
          }
          if (data.clauses && data.clauses.length > 0) {
            console.log('[FRONTEND] First clause structure:', data.clauses[0])
          }
        } else {
          console.error('[FRONTEND] Comprehensive API failed:', comprehensiveResponse)
          throw new Error(comprehensiveResponse.message || 'Failed to load contract details')
        }
        
        // Fetch existing comments
        const commentsResponse = await contractApprovalApi.getContractApprovals(contractId)
        if (commentsResponse.success) {
          existingComments.value = commentsResponse.data.filter(c => c.comment_text && c.comment_text.trim())
        }
        
      } catch (err) {
        console.error('Error fetching contract details:', err)
        
        // Provide more specific error messages
        if (err.code === 'ERR_NETWORK' || err.message?.includes('Network Error')) {
          error.value = 'Backend server is not running. Please start the Django server on port 8000.'
        } else if (err.response?.status === 404) {
          error.value = 'Contract not found. Please check the contract ID.'
        } else if (err.response?.status === 500) {
          error.value = 'Server error occurred. Please check the backend logs.'
        } else {
          error.value = err.message || 'Failed to load contract details'
        }
      } finally {
        isLoading.value = false
      }
    }
    
    const addTerm = () => {
      contractTerms.value.push({
        term_category: 'Other',
        term_title: '',
        term_text: '',
        risk_level: 'Low',
        compliance_status: 'Pending',
        is_standard: false,
        approval_status: 'Pending',
        version_number: '1.0'
      })
    }
    
    const removeTerm = (index) => {
      contractTerms.value.splice(index, 1)
    }
    
    const addClause = () => {
      contractClauses.value.push({
        clause_type: 'standard',
        clause_name: '',
        clause_text: '',
        risk_level: 'low',
        legal_category: '',
        version_number: '1.0',
        status: 'Pending',
        is_standard: false,
        notice_period_days: null,
        auto_renew: false,
        renewal_terms: '',
        termination_notice_period: null,
        early_termination_fee: null,
        termination_conditions: ''
      })
    }
    
    const removeClause = (index) => {
      contractClauses.value.splice(index, 1)
    }
    
    
    const approveContract = async () => {
      PopupService.confirm(
        'Are you sure you want to approve this contract?',
        'Confirm Approval',
        async () => {
          await performApproval()
        }
      )
    }
    
    const performApproval = async () => {
      isSubmitting.value = true
      try {
        // Save changes first (without showing success message)
        try {
          // Update contract
          await contractsApi.updateContract(contract.value.contract_id, contractData.value)
          
          // Update terms
          await contractsApi.updateContractTerms(contract.value.contract_id, contractTerms.value)
          
          // Update clauses
          await contractsApi.updateContractClauses(contract.value.contract_id, contractClauses.value)
          
          // Don't show "draft saved" message here
        } catch (saveErr) {
          console.error('Error saving before approval:', saveErr)
          // Continue with approval even if save fails
        }
        
        // Find the approval for this contract where user is the ASSIGNER (to approve/reject)
        const currentUser = store.getters['auth/currentUser']
        // Check multiple possible field names for user ID
        const userId = currentUser?.userid || currentUser?.user_id || currentUser?.UserId || currentUser?.id || 
                      (currentUser?.user && (currentUser.user.userid || currentUser.user.user_id || currentUser.user.UserId || currentUser.user.id))
        
        console.log('Current user for approval:', {
          currentUser,
          userId,
          contractId: contract.value?.contract_id
        })
        
        if (userId) {
          // Get approvals where user is the ASSIGNER (they can approve/reject)
          console.log('Fetching assigner approvals for userId:', userId)
          const reviewsResponse = await contractApprovalApi.getAssignerApprovals({ assigner_id: userId })
          
          console.log('Assigner approvals response:', {
            success: reviewsResponse.success,
            dataLength: reviewsResponse.data?.length,
            data: reviewsResponse.data,
            pagination: reviewsResponse.pagination
          })
          
          // Handle both array and paginated response formats
          const approvalsList = Array.isArray(reviewsResponse.data) 
            ? reviewsResponse.data 
            : (reviewsResponse.data?.results || reviewsResponse.data || [])
          
          const contractApproval = approvalsList.find(a => 
            a.object_id == contract.value.contract_id || 
            a.object_id === contract.value.contract_id ||
            String(a.object_id) === String(contract.value.contract_id)
          )
          
          console.log('Looking for approval as ASSIGNER:', {
            userId,
            contractId: contract.value.contract_id,
            approvalsCount: approvalsList.length,
            approvals: approvalsList,
            foundApproval: contractApproval
          })
          
          if (contractApproval) {
            console.log('Found approval, attempting to approve:', contractApproval.approval_id)
            const approveResponse = await contractApprovalApi.approveContract(contractApproval.approval_id)
            console.log('Approve response:', approveResponse)
            
            if (approveResponse.success) {
              PopupService.success('Contract approved successfully!', 'Approval Successful')
              PopupService.onAction('ok', () => {
                router.push('/my-contract-approvals')
              })
            } else {
              const errorMsg = approveResponse.error || approveResponse.message || 'Unknown error'
              PopupService.error(`Failed to approve contract: ${errorMsg}`, 'Approval Failed')
            }
          } else {
            console.warn('No approval found for contract:', {
              contractId: contract.value.contract_id,
              userId,
              availableApprovals: approvalsList.map(a => ({ 
                approval_id: a.approval_id, 
                object_id: a.object_id, 
                assigner_id: a.assigner_id 
              }))
            })
            PopupService.warning('No approval found for this contract. You must be the assigner to approve/reject contracts.', 'Approval Not Found')
          }
        } else {
          console.error('User ID not found in current user:', currentUser)
          PopupService.error('User ID not found. Please log in again.', 'Authentication Required')
        }
      } catch (err) {
        console.error('Error approving contract:', err)
        PopupService.error('Failed to approve contract: ' + err.message, 'Approval Failed')
      } finally {
        isSubmitting.value = false
      }
    }
    
    
    const goBack = () => {
      router.push('/contracts/approvals')
    }
    
    const formatDate = (dateString) => {
      if (!dateString) return 'N/A'
      try {
        const date = new Date(dateString)
        return date.toLocaleDateString('en-US', {
          year: 'numeric',
          month: 'short',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit'
        })
      } catch (error) {
        return 'Invalid Date'
      }
    }
    
    // Lifecycle
    onMounted(async () => {
      await loggingService.logPageView('Contract', 'Contract Review Edit')
      await fetchContractDetails()
    })
    
    return {
      contract,
      contractData,
      contractTerms,
      contractClauses,
      subContracts,
      existingComments,
      reviewComment,
      approval,
      isLoading,
      isSubmitting,
      error,
      addTerm,
      removeTerm,
      addClause,
      removeClause,
      approveContract,
      goBack,
      formatDate,
      fetchContractDetails
    }
  }
}
</script>

<style src="./ContractReviewEdit.css"></style>
