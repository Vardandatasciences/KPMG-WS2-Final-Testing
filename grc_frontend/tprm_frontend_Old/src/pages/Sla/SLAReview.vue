<template>
  <div class="sla-review-container">
    <!-- Header Section -->
    <div class="review-header">
      <div class="header-content">
        <div class="header-left">
          <button @click="goBack" class="back-btn">
            <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"/>
            </svg>
            Back to Approvals
          </button>
          <div class="header-text">
            <h1 class="review-title">SLA Review & Approval</h1>
            <p class="review-subtitle">Review SLA details and make approval decision</p>
          </div>
        </div>
        <div class="header-actions">
          <div class="approval-info">
            <span class="approval-id">Approval #{{ approvalId }}</span>
            <span class="approval-status" :class="`status-${currentApproval?.status?.toLowerCase()}`">
              {{ currentApproval?.status?.replace('_', ' ') || 'Loading...' }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="loading-state">
      <div class="loading-spinner"></div>
      <h4>Loading SLA details...</h4>
      <p>Please wait while we fetch the SLA information</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-state">
      <div class="error-icon">
        <svg class="h-16 w-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"/>
        </svg>
      </div>
      <h4>Error Loading SLA</h4>
      <p>{{ error }}</p>
      <button @click="fetchApprovalDetails" class="retry-btn">
        <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
        </svg>
        Try Again
      </button>
    </div>

    <!-- SLA Review Content -->
    <div v-else-if="currentApproval" class="review-content">
      <div class="review-grid">
        <!-- SLA Information Section -->
        <div class="review-section">
          <div class="section-header">
            <h3 class="section-title">SLA Information</h3>
            <div class="section-badges">
              <span class="badge" :class="`badge--${currentApproval.sla_details?.priority?.toLowerCase() || 'medium'}`">
                {{ currentApproval.sla_details?.priority || 'MEDIUM' }}
              </span>
              <span class="badge" :class="`badge--${currentApproval.sla_details?.status?.toLowerCase() || 'pending'}`">
                {{ currentApproval.sla_details?.status || 'PENDING' }}
              </span>
            </div>
          </div>
          <div class="section-content">
            <div class="info-grid">
              <div class="info-item">
                <label>SLA Name</label>
                <p class="info-value">{{ currentApproval.sla_details?.sla_name || 'N/A' }}</p>
              </div>
              <div class="info-item">
                <label>SLA Type</label>
                <p class="info-value">{{ currentApproval.sla_details?.sla_type || 'N/A' }}</p>
              </div>
              <div class="info-item">
                <label>Business Service Impacted</label>
                <p class="info-value">{{ currentApproval.sla_details?.business_service_impacted || 'N/A' }}</p>
              </div>
              <div class="info-item">
                <label>Compliance Score</label>
                <p class="info-value score-value">{{ currentApproval.sla_details?.compliance_score || 'N/A' }}%</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Dates & Thresholds Section -->
        <div class="review-section">
          <div class="section-header">
            <h3 class="section-title">Dates & Thresholds</h3>
          </div>
          <div class="section-content">
            <div class="info-grid">
              <div class="info-item">
                <label>Effective Date</label>
                <p class="info-value">{{ formatDate(currentApproval.sla_details?.effective_date) }}</p>
              </div>
              <div class="info-item">
                <label>Expiry Date</label>
                <p class="info-value">{{ formatDate(currentApproval.sla_details?.expiry_date) }}</p>
              </div>
              <div class="info-item">
                <label>Penalty Threshold</label>
                <p class="info-value penalty-value">{{ currentApproval.sla_details?.penalty_threshold || 'N/A' }}%</p>
              </div>
              <div class="info-item">
                <label>Credit Threshold</label>
                <p class="info-value credit-value">{{ currentApproval.sla_details?.credit_threshold || 'N/A' }}%</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Technical Details Section -->
        <div class="review-section">
          <div class="section-header">
            <h3 class="section-title">Technical Details</h3>
          </div>
          <div class="section-content">
            <div class="info-item full-width">
              <label>Measurement Methodology</label>
              <div class="text-content">{{ currentApproval.sla_details?.measurement_methodology || 'N/A' }}</div>
            </div>
            <div class="info-item full-width">
              <label>Exclusions</label>
              <div class="text-content">{{ currentApproval.sla_details?.exclusions || 'N/A' }}</div>
            </div>
            <div class="info-item full-width">
              <label>Audit Requirements</label>
              <div class="text-content">{{ currentApproval.sla_details?.audit_requirements || 'N/A' }}</div>
            </div>
            <div class="info-grid">
              <div class="info-item">
                <label>Compliance Framework</label>
                <p class="info-value">{{ currentApproval.sla_details?.compliance_framework || 'N/A' }}</p>
              </div>
              <div class="info-item">
                <label>Document Versioning</label>
                <p class="info-value">{{ currentApproval.sla_details?.document_versioning || 'N/A' }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Approval Information Section -->
        <div class="review-section">
          <div class="section-header">
            <h3 class="section-title">Approval Information</h3>
          </div>
          <div class="section-content">
            <div class="info-grid">
              <div class="info-item">
                <label>Workflow</label>
                <p class="info-value">{{ currentApproval.workflow_name }}</p>
              </div>
              <div class="info-item">
                <label>Assigned By</label>
                <p class="info-value">{{ currentApproval.assigner_name }}</p>
              </div>
              <div class="info-item">
                <label>Assigned To</label>
                <p class="info-value">{{ currentApproval.assignee_name }}</p>
              </div>
              <div class="info-item">
                <label>Due Date</label>
                <p class="info-value" :class="{ 'overdue': currentApproval.is_overdue }">
                  {{ formatDate(currentApproval.due_date) }}
                  <span v-if="currentApproval.is_overdue" class="overdue-text">(Overdue)</span>
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- Existing Comments Section -->
        <div v-if="currentApproval.comment_text" class="review-section">
          <div class="section-header">
            <h3 class="section-title">Existing Comments</h3>
          </div>
          <div class="section-content">
            <div class="comment-display">
              {{ currentApproval.comment_text }}
            </div>
          </div>
        </div>

        <!-- Review Actions Section -->
        <div class="review-section review-actions">
          <div class="section-header">
            <h3 class="section-title">Review Actions</h3>
          </div>
          <div class="section-content">
            <div class="review-form">
              <div class="comment-input-section">
                <label class="input-label">Add Your Comment</label>
                <textarea 
                  v-model="reviewComment" 
                  class="comment-input" 
                  placeholder="Enter your review comments, feedback, or recommendations..."
                  rows="4"
                ></textarea>
              </div>
              
              <div class="action-buttons">
                <button 
                  @click="addComment" 
                  class="btn btn--secondary"
                  :disabled="!reviewComment.trim() || isSubmitting"
                >
                  <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
                  </svg>
                  {{ isSubmitting ? 'Adding Comment...' : 'Add Comment' }}
                </button>
                
                <button 
                  @click="approveSLA" 
                  class="btn btn--success"
                  :disabled="isSubmitting"
                  v-if="currentApproval.status === 'COMMENTED' || currentApproval.status === 'IN_PROGRESS'"
                >
                  <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                  </svg>
                  {{ isSubmitting ? 'Approving...' : 'Approve SLA' }}
                </button>
                
                <button 
                  @click="rejectSLA" 
                  class="btn btn--danger"
                  :disabled="isSubmitting"
                  v-if="currentApproval.status === 'COMMENTED' || currentApproval.status === 'IN_PROGRESS'"
                >
                  <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                  </svg>
                  {{ isSubmitting ? 'Rejecting...' : 'Reject SLA' }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Popup Modal -->
  <PopupModal />
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import slaApprovalApi from '../../services/slaApprovalApi.js'
import PopupModal from '@/popup/PopupModal.vue'
import { PopupService } from '@/popup/popupService'
import loggingService from '@/services/loggingService'

export default {
  name: 'SLAReview',
  components: {
    PopupModal
  },
  setup() {
    const route = useRoute()
    const router = useRouter()
    
    // Reactive data
    const currentApproval = ref(null)
    const isLoading = ref(true)
    const error = ref(null)
    const reviewComment = ref('')
    const isSubmitting = ref(false)
    
    // Get approval ID from route params
    const approvalId = ref(route.params.id)
    
    // Methods
    const fetchApprovalDetails = async () => {
      isLoading.value = true
      error.value = null
      
      try {
        console.log('🔍 Fetching approval details for ID:', approvalId.value)
        const response = await slaApprovalApi.getApproval(approvalId.value)
        
        console.log('📡 Full API response:', response)
        console.log('📋 Response success:', response?.success)
        console.log('📋 Response data:', response?.data)
        
        if (response.success && response.data) {
          currentApproval.value = response.data
          console.log('✅ Approval details loaded:', currentApproval.value)
          console.log('🔍 SLA details:', currentApproval.value.sla_details)
          
          // Check if sla_details is null or empty
          if (!currentApproval.value.sla_details) {
            console.error('❌ sla_details is null or missing!')
            console.error('🔍 Full approval object:', JSON.stringify(currentApproval.value, null, 2))
            error.value = 'SLA details not found. The SLA may have been deleted or the approval data is incomplete.'
          } else {
            console.log('✅ SLA details found:', currentApproval.value.sla_details)
            console.log('🔍 SLA name:', currentApproval.value.sla_details.sla_name)
            console.log('🔍 SLA type:', currentApproval.value.sla_details.sla_type)
            console.log('🔍 Business service:', currentApproval.value.sla_details.business_service_impacted)
            console.log('🔍 Compliance score:', currentApproval.value.sla_details.compliance_score)
          }
        } else {
          console.error('❌ API response failed:', response)
          error.value = response.message || 'Failed to load approval details'
        }
      } catch (err) {
        console.error('❌ Error fetching approval details:', err)
        console.error('❌ Error details:', err.message, err.stack)
        error.value = err.message || 'Failed to load approval details'
      } finally {
        isLoading.value = false
      }
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
    
    const addComment = async () => {
      if (!reviewComment.value.trim()) return
      
      isSubmitting.value = true
      try {
        console.log(`Adding comment for approval ${approvalId.value}:`, reviewComment.value)
        
        const response = await slaApprovalApi.updateApproval(approvalId.value, { 
          comment_text: reviewComment.value,
          status: 'COMMENTED'
        })
        
        if (response.success) {
          // Update local state
          currentApproval.value.comment_text = reviewComment.value
          currentApproval.value.status = 'COMMENTED'
          
          console.log('Comment added successfully')
          reviewComment.value = ''
          PopupService.success('Comment added successfully!', 'Comment Added')
        } else {
          console.error('Failed to add comment:', response.message)
          PopupService.error('Failed to add comment: ' + response.message, 'Comment Failed')
        }
      } catch (error) {
        console.error('Error adding comment:', error)
        PopupService.error('Error adding comment: ' + error.message, 'Comment Error')
      } finally {
        isSubmitting.value = false
      }
    }
    
    const approveSLA = async () => {
      isSubmitting.value = true
      try {
        console.log(`Approving SLA for approval ${approvalId.value}`)
        
        const response = await slaApprovalApi.approveSLA(approvalId.value)
        
        if (response.success) {
          // Update local state
          currentApproval.value.status = 'APPROVED'
          currentApproval.value.approval_status = 'APPROVED'
          
          console.log('SLA approved successfully')
          PopupService.success('SLA approved successfully!', 'Approval Successful')
        } else {
          console.error('Failed to approve SLA:', response.message)
          PopupService.error('Failed to approve SLA: ' + response.message, 'Approval Failed')
        }
      } catch (error) {
        console.error('Error approving SLA:', error)
        PopupService.error('Error approving SLA: ' + error.message, 'Approval Error')
      } finally {
        isSubmitting.value = false
      }
    }
    
    const rejectSLA = async () => {
      PopupService.comment(
        'Please provide a reason for rejection:',
        'Reject SLA',
        async (rejectionReason) => {
          if (!rejectionReason || !rejectionReason.trim()) return
          
          isSubmitting.value = true
          try {
            console.log(`Rejecting SLA for approval ${approvalId.value}`)
            
            const response = await slaApprovalApi.rejectSLA(approvalId.value, rejectionReason)
            
            if (response.success) {
              // Update local state
              currentApproval.value.status = 'REJECTED'
              currentApproval.value.approval_status = 'REJECTED'
              currentApproval.value.comment_text = `REJECTED: ${rejectionReason}`
              
              console.log('SLA rejected successfully')
              PopupService.success('SLA rejected successfully!', 'Rejection Successful')
            } else {
              console.error('Failed to reject SLA:', response.message)
              PopupService.error('Failed to reject SLA: ' + response.message, 'Rejection Failed')
            }
          } catch (error) {
            console.error('Error rejecting SLA:', error)
            PopupService.error('Error rejecting SLA: ' + error.message, 'Rejection Error')
          } finally {
            isSubmitting.value = false
          }
        }
      )
    }
    
    const goBack = () => {
      router.push('/slas/approvals')
    }
    
    // Lifecycle
    onMounted(async () => {
      await loggingService.logPageView('SLA', 'SLA Review')
      await fetchApprovalDetails()
    })
    
    return {
      // Data
      currentApproval,
      isLoading,
      error,
      reviewComment,
      isSubmitting,
      approvalId,
      
      // Methods
      fetchApprovalDetails,
      formatDate,
      addComment,
      approveSLA,
      rejectSLA,
      goBack
    }
  }
}
</script>

<style scoped>
.sla-review-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  padding: 2rem;
}

.review-header {
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  border-radius: 16px;
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  border: 1px solid #e2e8f0;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.back-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(59, 130, 246, 0.3);
}

.review-title {
  font-size: 2rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
}

.review-subtitle {
  color: #64748b;
  margin: 0.5rem 0 0 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.approval-info {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.5rem;
}

.approval-id {
  font-weight: 600;
  color: #64748b;
}

.approval-status {
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-weight: 600;
  font-size: 0.875rem;
}

.status-assigned {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: white;
}

.status-commented {
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  color: white;
}

.status-approved {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
}

.status-rejected {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
}

.review-content {
  max-width: 1200px;
  margin: 0 auto;
}

.review-grid {
  display: grid;
  gap: 2rem;
}

.review-section {
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  border-radius: 16px;
  padding: 2rem;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  border: 1px solid #e2e8f0;
}

.review-actions {
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  border: 2px solid #f59e0b;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #e2e8f0;
}

.section-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
}

.section-badges {
  display: flex;
  gap: 0.5rem;
}

.badge {
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-weight: 600;
  font-size: 0.875rem;
}

.badge--high {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
}

.badge--medium {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: white;
}

.badge--low {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
}

.badge--active {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
}

.badge--pending {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: white;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.info-item.full-width {
  grid-column: 1 / -1;
}

.info-item label {
  font-weight: 600;
  color: #64748b;
  font-size: 0.875rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.info-value {
  font-size: 1.125rem;
  font-weight: 500;
  color: #1e293b;
  margin: 0;
}

.score-value {
  color: #059669;
  font-weight: 700;
}

.penalty-value {
  color: #dc2626;
  font-weight: 700;
}

.credit-value {
  color: #059669;
  font-weight: 700;
}

.overdue {
  color: #dc2626;
  font-weight: 700;
}

.overdue-text {
  font-size: 0.875rem;
  margin-left: 0.5rem;
}

.text-content {
  background: #f8fafc;
  padding: 1rem;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  white-space: pre-wrap;
  line-height: 1.6;
}

.comment-display {
  background: #f8fafc;
  padding: 1.5rem;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  white-space: pre-wrap;
  line-height: 1.6;
  font-style: italic;
}

.review-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.comment-input-section {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.input-label {
  font-weight: 600;
  color: #1e293b;
  font-size: 1rem;
}

.comment-input {
  width: 100%;
  min-height: 120px;
  padding: 1rem;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  font-size: 1rem;
  line-height: 1.6;
  resize: vertical;
  transition: all 0.3s ease;
}

.comment-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.action-buttons {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.btn {
  display: flex;
  align-items: center;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  border: none;
  font-size: 1rem;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn--secondary {
  background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
  color: white;
}

.btn--secondary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(107, 114, 128, 0.3);
}

.btn--success {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
}

.btn--success:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(16, 185, 129, 0.3);
}

.btn--danger {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
}

.btn--danger:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(239, 68, 68, 0.3);
}

.loading-state, .error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  text-align: center;
  background: white;
  border-radius: 16px;
  padding: 3rem;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e2e8f0;
  border-top: 4px solid #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-icon {
  color: #ef4444;
  margin-bottom: 1rem;
}

.retry-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-top: 1rem;
}

.retry-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(59, 130, 246, 0.3);
}

@media (max-width: 768px) {
  .sla-review-container {
    padding: 1rem;
  }
  
  .header-content {
    flex-direction: column;
    gap: 1rem;
    align-items: flex-start;
  }
  
  .action-buttons {
    flex-direction: column;
  }
  
  .btn {
    width: 100%;
    justify-content: center;
  }
}
</style>
