<template>
  <div class="contract-detail-container">
    <!-- Header -->
    <div class="contract-header">
      <div class="header-content">
        <div class="header-left">
          <button @click="goBack" class="back-button">
            <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
            </svg>
            Back to Approvals
          </button>
          <div class="contract-title-section">
            <h1 class="contract-title">{{ contract?.contract_title || 'Loading...' }}</h1>
            <div class="contract-meta">
              <span class="contract-number">{{ contract?.contract_number }}</span>
              <span class="contract-type">{{ contract?.contract_type }}</span>
              <span class="contract-status" :class="`status--${contract?.status?.toLowerCase()}`">
                {{ contract?.status }}
              </span>
            </div>
          </div>
        </div>
        <div class="header-actions">
          <button @click="refreshData" class="action-button" :disabled="isLoading">
            <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
            </svg>
            Refresh
          </button>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>Loading contract details...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-container">
      <div class="error-icon">
        <svg class="h-12 w-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"/>
        </svg>
      </div>
      <h3>Error Loading Contract</h3>
      <p>{{ error }}</p>
      <button @click="refreshData" class="retry-button">Try Again</button>
    </div>

    <!-- Main Content -->
    <div v-else-if="contract" class="contract-content">
      <!-- Summary Cards -->
      <div class="summary-cards">
        <div class="summary-card">
          <div class="summary-icon">
            <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
            </svg>
          </div>
          <div class="summary-content">
            <div class="summary-value">{{ summary.total_terms }}</div>
            <div class="summary-label">Contract Terms</div>
          </div>
        </div>
        <div class="summary-card">
          <div class="summary-icon">
            <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
            </svg>
          </div>
          <div class="summary-content">
            <div class="summary-value">{{ summary.total_clauses }}</div>
            <div class="summary-label">Contract Clauses</div>
          </div>
        </div>
        <div class="summary-card">
          <div class="summary-icon">
            <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/>
            </svg>
          </div>
          <div class="summary-content">
            <div class="summary-value">{{ summary.total_sub_contracts }}</div>
            <div class="summary-label">Sub Contracts</div>
          </div>
        </div>
      </div>

      <!-- Contract Information -->
      <div class="contract-info-section">
        <h2 class="section-title">Contract Information</h2>
        <div class="info-grid">
          <div class="info-item">
            <label>Vendor</label>
            <div class="info-value">{{ contract.vendor?.company_name || 'N/A' }}</div>
          </div>
          <div class="info-item">
            <label>Contract Value</label>
            <div class="info-value">{{ formatCurrency(contract.contract_value) }}</div>
          </div>
          <div class="info-item">
            <label>Start Date</label>
            <div class="info-value">{{ formatDate(contract.start_date) }}</div>
          </div>
          <div class="info-item">
            <label>End Date</label>
            <div class="info-value">{{ formatDate(contract.end_date) }}</div>
          </div>
          <div class="info-item">
            <label>Priority</label>
            <div class="info-value priority-badge" :class="`priority--${contract.priority?.toLowerCase()}`">
              {{ contract.priority }}
            </div>
          </div>
          <div class="info-item">
            <label>Compliance Status</label>
            <div class="info-value compliance-badge" :class="`compliance--${contract.compliance_status?.toLowerCase()}`">
              {{ contract.compliance_status }}
            </div>
          </div>
        </div>
      </div>

      <!-- Contract Terms -->
      <div class="terms-section">
        <h2 class="section-title">Contract Terms</h2>
        <div v-if="terms.length === 0" class="empty-state">
          <p>No contract terms found.</p>
        </div>
        <div v-else class="terms-list">
          <div v-for="term in terms" :key="term.id" class="term-card">
            <div class="term-header">
              <h3 class="term-title">{{ term.term_title || `Term ${term.term_id}` }}</h3>
              <div class="term-meta">
                <span class="term-category">{{ term.term_category }}</span>
                <span class="risk-level" :class="`risk--${term.risk_level?.toLowerCase()}`">
                  {{ term.risk_level }}
                </span>
              </div>
            </div>
            <div class="term-content">
              <p>{{ term.term_text }}</p>
            </div>
            <div class="term-footer">
              <span class="compliance-status" :class="`compliance--${term.compliance_status?.toLowerCase()}`">
                {{ term.compliance_status }}
              </span>
              <span class="approval-status" :class="`approval--${term.approval_status?.toLowerCase()}`">
                {{ term.approval_status }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Contract Clauses -->
      <div class="clauses-section">
        <h2 class="section-title">Contract Clauses</h2>
        <div v-if="clauses.length === 0" class="empty-state">
          <p>No contract clauses found.</p>
        </div>
        <div v-else class="clauses-list">
          <div v-for="clause in clauses" :key="clause.id" class="clause-card">
            <div class="clause-header">
              <h3 class="clause-title">{{ clause.clause_name }}</h3>
              <div class="clause-meta">
                <span class="clause-type">{{ clause.clause_type }}</span>
                <span class="risk-level" :class="`risk--${clause.risk_level?.toLowerCase()}`">
                  {{ clause.risk_level }}
                </span>
              </div>
            </div>
            <div class="clause-content">
              <p>{{ clause.clause_text }}</p>
            </div>
            <div v-if="clause.renewal_terms || clause.termination_conditions" class="clause-details">
              <div v-if="clause.renewal_terms" class="detail-item">
                <strong>Renewal Terms:</strong> {{ clause.renewal_terms }}
              </div>
              <div v-if="clause.termination_conditions" class="detail-item">
                <strong>Termination Conditions:</strong> {{ clause.termination_conditions }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Sub Contracts -->
      <div class="sub-contracts-section">
        <h2 class="section-title">Sub Contracts</h2>
        <div v-if="subContracts.length === 0" class="empty-state">
          <p>No sub contracts found.</p>
        </div>
        <div v-else class="sub-contracts-list">
          <div v-for="subContract in subContracts" :key="subContract.contract_id" class="sub-contract-card">
            <div class="sub-contract-header" @click="toggleSubContract(subContract.contract_id)">
              <div class="sub-contract-title-section">
                <h3 class="sub-contract-title">{{ subContract.contract_title }}</h3>
                <span class="sub-contract-number">{{ subContract.contract_number }}</span>
              </div>
              <div class="sub-contract-actions">
                <div class="sub-contract-stats">
                  <span class="stat-badge">{{ subContract.terms_count || 0 }} Terms</span>
                  <span class="stat-badge">{{ subContract.clauses_count || 0 }} Clauses</span>
                </div>
                <button class="expand-button" :class="{ 'expanded': expandedSubContracts.includes(subContract.contract_id) }">
                  <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
                  </svg>
                </button>
              </div>
            </div>
            
            <div class="sub-contract-info">
              <div class="info-row">
                <span class="label">Vendor:</span>
                <span class="value">{{ subContract.vendor?.company_name || 'N/A' }}</span>
              </div>
              <div class="info-row">
                <span class="label">Value:</span>
                <span class="value">{{ formatCurrency(subContract.contract_value) }}</span>
              </div>
              <div class="info-row">
                <span class="label">Status:</span>
                <span class="value status-badge" :class="`status--${subContract.status?.toLowerCase()}`">
                  {{ subContract.status }}
                </span>
              </div>
              <div class="info-row">
                <span class="label">Start Date:</span>
                <span class="value">{{ formatDate(subContract.start_date) }}</span>
              </div>
              <div class="info-row">
                <span class="label">End Date:</span>
                <span class="value">{{ formatDate(subContract.end_date) }}</span>
              </div>
            </div>

            <!-- Expandable Terms and Clauses Section -->
            <div v-if="expandedSubContracts.includes(subContract.contract_id)" class="sub-contract-details">
              <!-- Sub-contract Terms -->
              <div class="sub-contract-terms">
                <h4 class="subsection-title">Contract Terms</h4>
                <div v-if="!subContract.terms || subContract.terms.length === 0" class="empty-subsection">
                  <p>No contract terms found for this sub-contract.</p>
                </div>
                <div v-else class="terms-list">
                  <div v-for="term in subContract.terms" :key="term.id" class="term-card">
                    <div class="term-header">
                      <h5 class="term-title">{{ term.term_title || `Term ${term.term_id}` }}</h5>
                      <div class="term-meta">
                        <span class="term-category">{{ term.term_category }}</span>
                        <span class="risk-level" :class="`risk--${term.risk_level?.toLowerCase()}`">
                          {{ term.risk_level }}
                        </span>
                      </div>
                    </div>
                    <div class="term-content">
                      <p>{{ term.term_text }}</p>
                    </div>
                    <div class="term-footer">
                      <span class="compliance-status" :class="`compliance--${term.compliance_status?.toLowerCase()}`">
                        {{ term.compliance_status }}
                      </span>
                      <span class="approval-status" :class="`approval--${term.approval_status?.toLowerCase()}`">
                        {{ term.approval_status }}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Sub-contract Clauses -->
              <div class="sub-contract-clauses">
                <h4 class="subsection-title">Contract Clauses</h4>
                <div v-if="!subContract.clauses || subContract.clauses.length === 0" class="empty-subsection">
                  <p>No contract clauses found for this sub-contract.</p>
                </div>
                <div v-else class="clauses-list">
                  <div v-for="clause in subContract.clauses" :key="clause.id" class="clause-card">
                    <div class="clause-header">
                      <h5 class="clause-title">{{ clause.clause_name }}</h5>
                      <div class="clause-meta">
                        <span class="clause-type">{{ clause.clause_type }}</span>
                        <span class="risk-level" :class="`risk--${clause.risk_level?.toLowerCase()}`">
                          {{ clause.risk_level }}
                        </span>
                      </div>
                    </div>
                    <div class="clause-content">
                      <p>{{ clause.clause_text }}</p>
                    </div>
                    <div v-if="clause.renewal_terms || clause.termination_conditions" class="clause-details">
                      <div v-if="clause.renewal_terms" class="detail-item">
                        <strong>Renewal Terms:</strong> {{ clause.renewal_terms }}
                      </div>
                      <div v-if="clause.termination_conditions" class="detail-item">
                        <strong>Termination Conditions:</strong> {{ clause.termination_conditions }}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Comments Section -->
      <div class="comments-section">
        <h2 class="section-title">Review Comments</h2>
        <div class="comments-container">
          <!-- Existing Comments -->
          <div v-if="existingComments.length > 0" class="existing-comments">
            <h3 class="comments-subtitle">Previous Comments</h3>
            <div class="comments-list">
              <div v-for="comment in existingComments" :key="comment.approval_id" class="comment-item">
                <div class="comment-header">
                  <div class="comment-author">
                    <span class="author-name">{{ 
                      comment.assignee_name || 
                      comment.assigner_name || 
                      comment.assignee_details?.full_name || 
                      comment.assigner_details?.full_name || 
                      'Unknown User' 
                    }}</span>
                    <span class="comment-date">{{ formatDate(comment.created_at) }}</span>
                    <!-- Debug info - remove in production -->
                    <div class="debug-info" style="font-size: 10px; color: #999; margin-top: 4px;">
                      Debug: assignee_name="{{ comment.assignee_name }}", assigner_name="{{ comment.assigner_name }}"
                    </div>
                  </div>
                  <span class="comment-status" :class="`status--${comment.status?.toLowerCase()}`">
                    {{ comment.status }}
                  </span>
                </div>
                <div class="comment-content">
                  <p>{{ comment.comment_text }}</p>
                </div>
              </div>
            </div>
          </div>

          <!-- Comment Form (Only for Assignees) -->
          <div v-if="!isAssigner" class="comment-form">
            <h3 class="comments-subtitle">Add Your Comment</h3>
            
            <!-- No Approval Warning -->
            <div v-if="!currentApprovalId" class="no-approval-warning">
              <div class="warning-icon">
                <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"/>
                </svg>
              </div>
              <div class="warning-content">
                <h4>No Approval Assignment Found</h4>
                <p>You don't have an approval assignment for this contract. The system will attempt to create one automatically, or you may need to contact your administrator.</p>
              </div>
            </div>
            
            <div class="form-group">
              <label for="comment-text" class="form-label">Your Review Comment</label>
              <textarea
                id="comment-text"
                v-model="commentText"
                class="comment-textarea"
                placeholder="Enter your review comments, feedback, or recommendations here..."
                rows="6"
                :disabled="isSubmittingComment || !currentApprovalId"
              ></textarea>
              <div class="character-count">
                {{ commentText.length }}/2000 characters
              </div>
            </div>
            
            <div class="form-actions">
              <button
                @click="saveAsDraft"
                class="action-btn draft-btn"
                :disabled="!commentText.trim() || isSubmittingComment || !currentApprovalId"
              >
                <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4"/>
                </svg>
                {{ isSubmittingComment ? 'Saving...' : 'Save as Draft' }}
              </button>
              
              <button
                @click="submitComment"
                class="action-btn submit-btn"
                :disabled="!commentText.trim() || isSubmittingComment || !currentApprovalId"
              >
                <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/>
                </svg>
                {{ isSubmittingComment ? 'Submitting...' : 'Submit Comment' }}
              </button>
            </div>
          </div>
          
          <!-- Info for Assigners -->
          <div v-if="isAssigner" class="assigner-info-card">
            <div class="info-icon">
              <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
            </div>
            <div class="info-content">
              <h4>Viewing as Assigner</h4>
              <p>You assigned this contract for review. To approve or reject this contract, please go to the <strong>My Contract Approvals</strong> page under the <strong>"My Reviews"</strong> tab.</p>
              <button @click="goToMyApprovals" class="go-to-approvals-btn">
                <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"/>
                </svg>
                Go to My Approvals
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStore } from 'vuex'
import contractApi from '../../services/vendorcontractsApi'
import loggingService from '@/services/loggingService'
import { PopupService } from '@/popup/popupService'

export default {
  name: 'ContractDetailView',
  setup() {
    const route = useRoute()
    const router = useRouter()
    const store = useStore()
    
    // Reactive data
    const contract = ref(null)
    const terms = ref([])
    const clauses = ref([])
    const subContracts = ref([])
    const summary = ref({
      total_terms: 0,
      total_clauses: 0,
      total_sub_contracts: 0
    })
    const isLoading = ref(false)
    const error = ref(null)
    const expandedSubContracts = ref([])
    const commentText = ref('')
    const isSubmittingComment = ref(false)
    const existingComments = ref([])
    const currentApprovalId = ref(null)
    const isAssigner = ref(false)

    // Methods
    const fetchContractDetails = async () => {
      isLoading.value = true
      error.value = null
      
      try {
        const contractId = route.params.contractId
        const response = await contractApi.getContractComprehensiveDetail(contractId)
        
        if (response.success) {
          contract.value = response.data.contract
          terms.value = response.data.terms
          clauses.value = response.data.clauses
          subContracts.value = response.data.sub_contracts
          summary.value = response.data.summary
          
          console.log('Contract details loaded:', {
            contract: contract.value,
            terms: terms.value,
            clauses: clauses.value,
            subContracts: subContracts.value,
            summary: summary.value
          })
        } else {
          error.value = response.message || 'Failed to load contract details'
        }
      } catch (err) {
        error.value = err.message || 'An error occurred while loading contract details'
      } finally {
        isLoading.value = false
      }
    }

    const refreshData = () => {
      fetchContractDetails()
    }

    const goBack = () => {
      router.go(-1)
    }

    const formatDate = (dateString) => {
      if (!dateString) return 'N/A'
      try {
        const date = new Date(dateString)
        return date.toLocaleDateString('en-US', {
          year: 'numeric',
          month: 'short',
          day: 'numeric'
        })
      } catch (error) {
        return 'Invalid Date'
      }
    }

    const formatCurrency = (amount) => {
      if (!amount) return 'N/A'
      try {
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD'
        }).format(amount)
      } catch (error) {
        return `$${amount}`
      }
    }

    const toggleSubContract = (contractId) => {
      const index = expandedSubContracts.value.indexOf(contractId)
      if (index > -1) {
        expandedSubContracts.value.splice(index, 1)
      } else {
        expandedSubContracts.value.push(contractId)
      }
    }

    const fetchExistingComments = async () => {
      try {
        const contractId = route.params.contractId
        const response = await contractApi.getContractApprovals(contractId)
        
        if (response.success && response.data) {
          // Show all approvals as comments, not just those with comment text
          existingComments.value = response.data.filter(approval => 
            approval.comment_text && approval.comment_text.trim()
          )
          
          console.log('Filtered comments for display:', existingComments.value.map(c => ({
            approval_id: c.approval_id,
            assigner_name: c.assigner_name,
            assignee_name: c.assignee_name,
            comment_text: c.comment_text,
            status: c.status
          })))
          
          console.log('All approvals for contract:', response.data.map(a => ({
            approval_id: a.approval_id,
            assigner_name: a.assigner_name,
            assignee_name: a.assignee_name,
            assigner_id: a.assigner_id,
            assignee_id: a.assignee_id,
            object_id: a.object_id,
            comment_text: a.comment_text,
            status: a.status
          })))
          
          // Find the current user's approval for this contract
          const currentUserId = getCurrentUserId()
          console.log('🔍 Looking for approval for user:', currentUserId, 'contract:', contractId)
          console.log('🔍 Available approvals:', response.data.map(a => ({
            approval_id: a.approval_id,
            assigner_id: a.assigner_id,
            assignee_id: a.assignee_id,
            assigner_id_type: typeof a.assigner_id,
            assignee_id_type: typeof a.assignee_id,
            object_id: a.object_id
          })))
          
          // Normalize approval IDs for comparison (handle both string and number)
          const normalizeId = (id) => {
            if (id === null || id === undefined) return null
            const num = typeof id === 'string' ? parseInt(id, 10) : id
            return isNaN(num) ? null : num
          }
          
          // First, check if user is an assignee (they need to comment)
          // This is the priority - assignees should be able to comment
          const currentApproval = response.data.find(approval => {
            const assigneeId = normalizeId(approval.assignee_id)
            const objId = normalizeId(approval.object_id)
            const contractIdNum = normalizeId(contractId)
            const match = assigneeId === currentUserId && objId === contractIdNum
            if (match) {
              console.log('✅ Found approval where user is ASSIGNEE:', {
                approval_id: approval.approval_id,
                assignee_id: approval.assignee_id,
                normalized_assignee_id: assigneeId,
                current_user_id: currentUserId,
                match
              })
            }
            return match
          })
          
          // Also check if user is an assigner (they can approve/reject)
          const userIsAssigner = response.data.some(approval => {
            const assignerId = normalizeId(approval.assigner_id)
            const objId = normalizeId(approval.object_id)
            const contractIdNum = normalizeId(contractId)
            const match = assignerId === currentUserId && objId === contractIdNum
            if (match) {
              console.log('✅ Found approval where user is ASSIGNER:', {
                approval_id: approval.approval_id,
                assigner_id: approval.assigner_id,
                normalized_assigner_id: assignerId,
                current_user_id: currentUserId,
                match
              })
            }
            return match
          })
          
          if (currentApproval) {
            // User is an ASSIGNEE - they should be able to comment
            currentApprovalId.value = currentApproval.approval_id
            isAssigner.value = false
            console.log('✅ User is ASSIGNEE - can comment. Approval ID:', currentApprovalId.value)
          } else if (userIsAssigner) {
            // User is an ASSIGNER - they should see the info message
            console.log('ℹ️ User is ASSIGNER (not assignee) - showing info message')
            currentApprovalId.value = null
            isAssigner.value = true
          } else {
            // No approval found - try to create one
            console.warn('⚠️ No approval found for current user and contract')
            isAssigner.value = false
            // Try to create a new approval for the current user
            await createApprovalForCurrentUser(contractId)
          }
        }
      } catch (error) {
        console.error('Error fetching existing comments:', error)
      }
    }

    const getCurrentUserId = () => {
      // Try to get user ID from various sources
      try {
        // First try to get from Vuex store
        const currentUser = store.getters?.['auth/currentUser']
        if (currentUser) {
          // Check all possible user ID fields
          const userId = currentUser.userid || currentUser.user_id || currentUser.UserId || currentUser.id
          if (userId) {
            // Normalize to number for consistent comparison
            const userIdNum = typeof userId === 'string' ? parseInt(userId, 10) : userId
            if (!isNaN(userIdNum)) {
              console.log('✅ Found user ID from store:', userIdNum, '(original:', userId, ')')
              return userIdNum
            }
          }
        }
        
        // Fallback to localStorage
        const localUserId = localStorage.getItem('user_id') || localStorage.getItem('userid') || localStorage.getItem('UserId')
        if (localUserId) {
          const userIdNum = typeof localUserId === 'string' ? parseInt(localUserId, 10) : localUserId
          if (!isNaN(userIdNum)) {
            console.log('✅ Found user ID from localStorage:', userIdNum)
            return userIdNum
          }
        }
        
        // Try to get from session storage
        const sessionUserId = sessionStorage.getItem('user_id') || sessionStorage.getItem('userid') || sessionStorage.getItem('UserId')
        if (sessionUserId) {
          const userIdNum = typeof sessionUserId === 'string' ? parseInt(sessionUserId, 10) : sessionUserId
          if (!isNaN(userIdNum)) {
            console.log('✅ Found user ID from sessionStorage:', userIdNum)
            return userIdNum
          }
        }
        
        console.warn('⚠️ No user ID found in any source')
        return null
      } catch (error) {
        console.error('❌ Error getting current user ID:', error)
        return null
      }
    }

    const createApprovalForCurrentUser = async (contractId) => {
      try {
        const currentUserId = getCurrentUserId()
        if (!currentUserId) {
          console.error('Cannot create approval: No user ID found')
          return
        }

        const currentUser = store.getters?.['auth/currentUser']
        const userName = currentUser ? 
          `${currentUser.first_name || ''} ${currentUser.last_name || ''}`.trim() || currentUser.username :
          'Current User'

        console.log('Creating approval for user:', currentUserId, 'contract:', contractId)
        
        const approvalData = {
          workflow_id: 1,
          workflow_name: 'Contract Review Workflow',
          assigner_id: currentUserId,
          assigner_name: userName,
          assignee_id: currentUserId,
          assignee_name: userName,
          object_type: 'CONTRACT_CREATION',
          object_id: contractId,
          assigned_date: new Date().toISOString(),
          due_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(), // 7 days from now
          status: 'IN_PROGRESS',
          comment_text: ''
        }

        const response = await contractApi.createContractApproval(approvalData)
        
        if (response.success) {
          currentApprovalId.value = response.data.approval_id
          console.log('Created new approval with ID:', currentApprovalId.value)
        } else {
          console.error('Failed to create approval:', response.message)
          PopupService.error('Failed to create approval assignment. Please contact your administrator.', 'Approval Creation Failed')
        }
      } catch (error) {
        console.error('Error creating approval:', error)
        PopupService.error('Error creating approval assignment. Please contact your administrator.', 'Approval Error')
      }
    }

    const saveAsDraft = async () => {
      if (!commentText.value.trim()) return
      
      if (!currentApprovalId.value) {
        PopupService.warning('No approval assignment found for this contract. Please contact your administrator.', 'No Approval Found')
        return
      }
      
      isSubmittingComment.value = true
      try {
        console.log('Saving draft with approval ID:', currentApprovalId.value)
        const response = await contractApi.updateContractApproval(currentApprovalId.value, {
          comment_text: commentText.value,
          status: 'IN_PROGRESS' // Keep as in progress for draft
        })
        
        if (response.success) {
          PopupService.success('Comment saved as draft successfully!', 'Draft Saved')
          commentText.value = ''
          await fetchExistingComments() // Refresh comments
        } else {
          PopupService.error('Failed to save comment as draft: ' + (response.message || 'Unknown error'), 'Save Failed')
        }
      } catch (error) {
        console.error('Error saving comment as draft:', error)
        PopupService.error('Error saving comment as draft: ' + error.message, 'Save Error')
      } finally {
        isSubmittingComment.value = false
      }
    }

    const submitComment = async () => {
      if (!commentText.value.trim()) return
      
      if (!currentApprovalId.value) {
        PopupService.warning('No approval assignment found for this contract. Please contact your administrator.', 'No Approval Found')
        return
      }
      
      isSubmittingComment.value = true
      try {
        console.log('Submitting comment with approval ID:', currentApprovalId.value)
        const response = await contractApi.updateContractApproval(currentApprovalId.value, {
          comment_text: commentText.value,
          status: 'COMMENTED' // Change status to COMMENTED
        })
        
        if (response.success) {
          PopupService.success('Comment submitted successfully! The approval status has been updated to COMMENTED.', 'Comment Submitted')
          commentText.value = ''
          await fetchExistingComments() // Refresh comments
          
          // Redirect to My Contract Approvals page
          setTimeout(() => {
            router.push('/my-contract-approvals')
          }, 1500)
        } else {
          PopupService.error('Failed to submit comment: ' + (response.message || 'Unknown error'), 'Submission Failed')
        }
      } catch (error) {
        console.error('Error submitting comment:', error)
        PopupService.error('Error submitting comment: ' + error.message, 'Submission Error')
      } finally {
        isSubmittingComment.value = false
      }
    }

    const goToMyApprovals = () => {
      router.push('/my-contract-approvals')
    }

    // Lifecycle
    onMounted(async () => {
      await loggingService.logPageView('Contract', 'Contract Detail View')
      await fetchContractDetails()
      await fetchExistingComments()
    })

    return {
      contract,
      terms,
      clauses,
      subContracts,
      summary,
      isLoading,
      error,
      expandedSubContracts,
      commentText,
      isSubmittingComment,
      existingComments,
      currentApprovalId,
      isAssigner,
      fetchContractDetails,
      refreshData,
      goBack,
      formatDate,
      formatCurrency,
      toggleSubContract,
      saveAsDraft,
      submitComment,
      goToMyApprovals
    }
  }
}
</script>

<style src="./ContractDetailView.css"></style>
