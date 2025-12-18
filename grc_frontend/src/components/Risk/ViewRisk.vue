<template>
  <div class="risk-view-container">
    <PopupModal />
    
    <div class="risk-view-header">
      <h2 class="risk-view-title"><i class="fas fa-exclamation-triangle risk-view-icon"></i> Risk Details</h2>
      <div class="risk-view-header-actions">
        <button v-if="!isEditMode" class="risk-view-edit-button" @click="toggleEditMode">
          <i class="fas fa-edit"></i> Edit Risk
        </button>
        <button v-if="isEditMode" class="risk-view-request-button" @click="openRiskRectificationModal" :disabled="!hasRiskChanges()">
          <i class="fas fa-paper-plane"></i> Request
        </button>
        <button v-if="isEditMode" class="risk-view-cancel-button" @click="cancelEdit">
          <i class="fas fa-times"></i> Cancel
        </button>
        <button class="risk-view-back-button" @click="goBack">
          <i class="fas fa-arrow-left"></i> Back to Risk Register
        </button>
      </div>
    </div>

    <div class="risk-view-details-card" v-if="risk">
      <div class="risk-view-details-top">
        <div class="risk-view-id-section">
          <span class="risk-view-id-label">Risk ID:</span>
          <span class="risk-view-id-value">{{ risk.RiskId }}</span>
        </div>
        <div class="risk-view-meta">
          <div v-if="!isEditMode" class="risk-view-category">{{ risk.Category }}</div>
          <div v-if="!isEditMode" class="risk-view-criticality" :class="getCriticalityClass(risk.Criticality)">{{ risk.Criticality }}</div>
          
          <!-- Edit mode for category and criticality -->
          <div v-if="isEditMode" class="risk-view-edit-meta">
            <select v-model="editRisk.Category" class="risk-view-select">
              <option value="">Select Category</option>
              <option value="Operational">Operational</option>
              <option value="Financial">Financial</option>
              <option value="Technical">Technical</option>
              <option value="Strategic">Strategic</option>
              <option value="Compliance">Compliance</option>
              <option value="Reputational">Reputational</option>
            </select>
            <select v-model="editRisk.Criticality" class="risk-view-select">
              <option value="">Select Criticality</option>
              <option value="Low">Low</option>
              <option value="Medium">Medium</option>
              <option value="High">High</option>
              <option value="Critical">Critical</option>
            </select>
          </div>
        </div>
      </div>

      <div class="risk-view-title-section">
        <h3 v-if="!isEditMode">{{ risk.RiskTitle }}</h3>
        <input v-if="isEditMode" v-model="editRisk.RiskTitle" class="risk-view-title-input" placeholder="Enter risk title" />
        
        <div class="risk-view-compliance-section">
          <span class="risk-view-compliance-label">Compliance ID:</span>
          <span v-if="!isEditMode" class="risk-view-compliance-value">{{ risk.ComplianceId || 'N/A' }}</span>
          <input v-if="isEditMode" v-model="editRisk.ComplianceId" class="risk-view-compliance-input" placeholder="Enter compliance ID" />
        </div>
      </div>

      <div class="risk-view-content">
        <div class="risk-view-content-row">
          <div class="risk-view-content-column">
            <h4 class="risk-view-section-title">Risk Description:</h4>
            <div v-if="!isEditMode" class="risk-view-section-content">{{ risk.RiskDescription || 'N/A' }}</div>
            <textarea v-if="isEditMode" v-model="editRisk.RiskDescription" class="risk-view-textarea" placeholder="Enter risk description" rows="4"></textarea>
          </div>
          <div class="risk-view-content-column">
            <h4 class="risk-view-section-title">Business Impact:</h4>
            <div v-if="!isEditMode" class="risk-view-section-content">{{ risk.BusinessImpact || 'N/A' }}</div>
            <textarea v-if="isEditMode" v-model="editRisk.BusinessImpact" class="risk-view-textarea" placeholder="Enter business impact" rows="4"></textarea>
          </div>
        </div>

        <div class="risk-view-content-row">
          <div class="risk-view-content-column">
            <h4 class="risk-view-section-title">Possible Damage:</h4>
            <div v-if="!isEditMode" class="risk-view-section-content">{{ risk.PossibleDamage || 'N/A' }}</div>
            <textarea v-if="isEditMode" v-model="editRisk.PossibleDamage" class="risk-view-textarea" placeholder="Enter possible damage" rows="3"></textarea>
          </div>
          <div class="risk-view-content-column">
            <h4 class="risk-view-section-title">Risk Likelihood:</h4>
            <div v-if="!isEditMode" class="risk-view-section-content">{{ risk.RiskLikelihood || 'N/A' }}</div>
            <select
              v-if="isEditMode"
              v-model.number="editRisk.RiskLikelihood"
              class="risk-view-select"
            >
              <option value="">Select Likelihood</option>
              <option
                v-for="option in riskScoreOptions"
                :key="`likelihood-${option.value}`"
                :value="option.value"
              >
                {{ option.label }}
              </option>
            </select>
          </div>
        </div>

        <div class="risk-view-content-row">
          <div class="risk-view-content-column">
            <h4 class="risk-view-section-title">Risk Impact:</h4>
            <div v-if="!isEditMode" class="risk-view-section-content">{{ risk.RiskImpact || 'N/A' }}</div>
            <select
              v-if="isEditMode"
              v-model.number="editRisk.RiskImpact"
              class="risk-view-select"
            >
              <option value="">Select Impact</option>
              <option
                v-for="option in riskScoreOptions"
                :key="`impact-${option.value}`"
                :value="option.value"
              >
                {{ option.label }}
              </option>
            </select>
          </div>
          <div class="risk-view-content-column">
            <h4 class="risk-view-section-title">Risk Exposure Rating:</h4>
            <div v-if="!isEditMode" class="risk-view-section-content">{{ risk.RiskExposureRating || 'N/A' }}</div>
            <input v-if="isEditMode" v-model="editRisk.RiskExposureRating" class="risk-view-input" placeholder="Enter exposure rating" />
          </div>
        </div>

        <div class="risk-view-content-row">
          <div class="risk-view-content-column">
            <h4 class="risk-view-section-title">Risk Priority:</h4>
            <div v-if="!isEditMode" class="risk-view-section-content">{{ risk.RiskPriority || 'N/A' }}</div>
            <select v-if="isEditMode" v-model="editRisk.RiskPriority" class="risk-view-select">
              <option value="">Select Priority</option>
              <option value="Low">Low</option>
              <option value="Medium">Medium</option>
              <option value="High">High</option>
              <option value="Critical">Critical</option>
            </select>
          </div>
          <div class="risk-view-content-column">
            <h4 class="risk-view-section-title">Risk Mitigation:</h4>
            <div v-if="!isEditMode" class="risk-view-section-content">{{ risk.RiskMitigation || 'N/A' }}</div>
            <textarea v-if="isEditMode" v-model="editRisk.RiskMitigation" class="risk-view-textarea" placeholder="Enter risk mitigation" rows="3"></textarea>
          </div>
        </div>

        <div class="risk-view-content-row">
          <div class="risk-view-content-column">
            <h4 class="risk-view-section-title">Risk Type:</h4>
            <div v-if="!isEditMode" class="risk-view-section-content">{{ risk.RiskType || 'N/A' }}</div>
            <select v-if="isEditMode" v-model="editRisk.RiskType" class="risk-view-select">
              <option value="">Select Type</option>
              <option value="Internal">Internal</option>
              <option value="External">External</option>
              <option value="Emerging">Emerging</option>
              <option value="Systemic">Systemic</option>
            </select>
          </div>
          <div class="risk-view-content-column">
            <h4 class="risk-view-section-title">Created At:</h4>
            <div class="risk-view-section-content">{{ formatDate(risk.CreatedAt) }}</div>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="risk-view-no-data">
      Loading risk details or no risk found...
    </div>

    <!-- Success/Error Messages -->
    <div v-if="successMessage" class="risk-view-success-message">
      <i class="fas fa-check-circle"></i> {{ successMessage }}
    </div>
    <div v-if="errorMessage" class="risk-view-error-message">
      <i class="fas fa-exclamation-circle"></i> {{ errorMessage }}
    </div>

    <!-- Risk Rectification Request Modal -->
    <div v-if="showRectificationModal" class="risk-rectification-modal-overlay" @click="closeRiskRectificationModal">
      <div class="risk-rectification-modal-content" @click.stop>
        <div class="risk-rectification-modal-header">
          <h3>
            <i class="fas fa-file-alt"></i>
            Request Rectification of Risk Information
          </h3>
          <button class="risk-rectification-modal-close-btn" @click="closeRiskRectificationModal">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="risk-rectification-modal-body">
          <p class="risk-rectification-modal-message">
            You are requesting to update risk information. The changes will be reviewed and approved by an administrator.
          </p>
          <div class="risk-rectification-changes-summary" v-if="Object.keys(getRiskChanges()).length > 0">
            <h4>Changes Summary:</h4>
            <ul class="risk-rectification-changes-list">
              <li v-for="(change, field) in getRiskChanges()" :key="field">
                <strong>{{ formatRiskFieldName(field) }}:</strong>
                <span class="risk-rectification-old-value">{{ change.old || 'N/A' }}</span> →
                <span class="risk-rectification-new-value">{{ change.new || 'N/A' }}</span>
              </li>
            </ul>
          </div>
        </div>
        <div class="risk-rectification-modal-footer">
          <button class="risk-rectification-modal-cancel-btn" @click="closeRiskRectificationModal">
            Cancel
          </button>
          <button class="risk-rectification-modal-request-btn" @click="submitRiskRectificationRequest" :disabled="submittingRectification">
            <i v-if="submittingRectification" class="fas fa-spinner fa-spin"></i>
            <i v-else class="fas fa-paper-plane"></i>
            {{ submittingRectification ? 'Submitting...' : 'Request' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import './ViewRisk.css'
import axios from 'axios'
import { PopupModal } from '@/modules/popup'
import { API_ENDPOINTS } from '../../config/api.js'

export default {
  name: 'ViewRisk',
  components: {
    PopupModal
  },
  data() {
    return {
      risk: null,
      editRisk: {},
      isEditMode: false,
      isSaving: false,
      originalRisk: {},
      successMessage: '',
      errorMessage: '',
      showRectificationModal: false,
      submittingRectification: false,
      riskScoreOptions: [
        { value: 1, label: '1 - Very Low' },
        { value: 2, label: '2 - Low' },
        { value: 3, label: '3 - Low / Medium' },
        { value: 4, label: '4 - Medium' },
        { value: 5, label: '5 - Medium / High' },
        { value: 6, label: '6 - Medium / High+' },
        { value: 7, label: '7 - High' },
        { value: 8, label: '8 - Very High' },
        { value: 9, label: '9 - Severe' },
        { value: 10, label: '10 - Critical' }
      ]
    }
  },
  created() {
    this.fetchRiskDetails()
  },
  methods: {
    fetchRiskDetails() {
      const riskId = this.$route.params.id
      if (!riskId) {
        this.$router.push('/risk/riskregister-list')
        return
      }

      axios.get(API_ENDPOINTS.RISK(riskId))
        .then(response => {
          this.risk = response.data
          this.originalRisk = { ...response.data }
          this.editRisk = { ...response.data }
          // Send push notification when risk details are viewed
          this.sendPushNotification(this.risk)
        })
        .catch(error => {
          console.error('Error fetching risk details:', error)
          this.showError('Failed to load risk details')
          // Send push notification for error case
          this.sendPushNotification({
            RiskTitle: 'Error Loading Risk',
            message: `Failed to load risk details: ${error.message}`
          })
        })
    },

    toggleEditMode() {
      this.isEditMode = true
      this.editRisk = { ...this.risk }
      this.clearMessages()
    },

    cancelEdit() {
      this.isEditMode = false
      this.editRisk = { ...this.originalRisk }
      this.clearMessages()
    },

    async saveRisk() {
      if (!this.validateRisk()) {
        return
      }

      this.isSaving = true
      this.clearMessages()

      try {
        const payload = this.buildRiskPayload()
        const response = await axios.put(API_ENDPOINTS.RISK(this.risk.RiskId), payload)
        
        this.risk = response.data
        this.originalRisk = { ...response.data }
        this.isEditMode = false
        
        this.showSuccess('Risk updated successfully!')
        
        // Send push notification for successful update
        this.sendPushNotification({
          title: 'Risk Updated',
          message: `Risk "${this.risk.RiskTitle}" has been successfully updated.`,
          category: 'risk',
          priority: 'medium',
          user_id: 'default_user'
        })
        
      } catch (error) {
        console.error('Error updating risk:', error)
        this.showError('Failed to update risk. Please try again.')
        
        // Send push notification for error
        this.sendPushNotification({
          title: 'Risk Update Failed',
          message: `Failed to update risk: ${error.response?.data?.error || error.message}`,
          category: 'risk',
          priority: 'high',
          user_id: 'default_user'
        })
      } finally {
        this.isSaving = false
      }
    },

    buildRiskPayload() {
      const normalizeInteger = (value) => {
        if (value === '' || value === null || value === undefined) return null
        const parsed = parseInt(value, 10)
        return isNaN(parsed) ? null : parsed
      }

      const normalizeFloat = (value) => {
        if (value === '' || value === null || value === undefined) return null
        const parsed = parseFloat(value)
        return isNaN(parsed) ? null : parsed
      }

      const labelToNumberMap = {
        'Very Low': 1,
        'Low': 3,
        'Medium': 5,
        'High': 7,
        'Very High': 9
      }

      const normalizeScore = (value) => {
        if (typeof value === 'string' && labelToNumberMap[value]) {
          return labelToNumberMap[value]
        }
        return normalizeInteger(value)
      }

      return {
        ...this.editRisk,
        RiskLikelihood: normalizeScore(this.editRisk.RiskLikelihood),
        RiskImpact: normalizeScore(this.editRisk.RiskImpact),
        RiskExposureRating: normalizeFloat(this.editRisk.RiskExposureRating),
        ComplianceId: normalizeInteger(this.editRisk.ComplianceId)
      }
    },

    validateRisk() {
      if (!this.editRisk.RiskTitle || this.editRisk.RiskTitle.trim() === '') {
        this.showError('Risk title is required')
        return false
      }
      if (!this.editRisk.Category) {
        this.showError('Risk category is required')
        return false
      }
      if (!this.editRisk.Criticality) {
        this.showError('Risk criticality is required')
        return false
      }
      return true
    },

    showSuccess(message) {
      this.successMessage = message
      this.errorMessage = ''
      setTimeout(() => {
        this.successMessage = ''
      }, 5000)
    },

    showError(message) {
      this.errorMessage = message
      this.successMessage = ''
      setTimeout(() => {
        this.errorMessage = ''
      }, 5000)
    },

    clearMessages() {
      this.successMessage = ''
      this.errorMessage = ''
    },

    async sendPushNotification(riskData) {
      try {
        const notificationData = {
          title: riskData.title || 'Risk Details Viewed',
          message: riskData.message || `Risk "${riskData.RiskTitle || 'Untitled Risk'}" details have been viewed in the Risk module.`,
          category: riskData.category || 'risk',
          priority: riskData.priority || 'medium',
          user_id: riskData.user_id || 'default_user'
        };
        const response = await fetch(API_ENDPOINTS.PUSH_NOTIFICATION, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(notificationData)
        });
        if (response.ok) {
          console.log('Push notification sent successfully');
        } else {
          console.error('Failed to send push notification');
        }
      } catch (error) {
        console.error('Error sending push notification:', error);
      }
    },
    
    getCriticalityClass(criticality) {
      if (!criticality) return ''
      criticality = criticality.toLowerCase()
      if (criticality === 'critical') return 'risk-view-priority-critical'
      if (criticality === 'high') return 'risk-view-priority-high'
      if (criticality === 'medium') return 'risk-view-priority-medium'
      if (criticality === 'low') return 'risk-view-priority-low'
      return ''
    },
    formatDate(dateString) {
      if (!dateString) return 'N/A'
      const date = new Date(dateString)
      return date.toLocaleDateString()
    },
    goBack() {
      this.$router.push('/risk/riskregister-list')
    },
    
    hasRiskChanges() {
      if (!this.isEditMode || !this.risk || !this.editRisk) return false
      const changes = this.getRiskChanges()
      return Object.keys(changes).length > 0
    },
    
    getRiskChanges() {
      const changes = {}
      if (!this.isEditMode || !this.risk || !this.editRisk) return changes
      
      // Compare each field
      const fieldsToCompare = [
        'RiskTitle',
        'Category',
        'Criticality',
        'ComplianceId',
        'RiskDescription',
        'BusinessImpact',
        'PossibleDamage',
        'RiskLikelihood',
        'RiskImpact',
        'RiskExposureRating',
        'RiskPriority',
        'RiskMitigation',
        'RiskType'
      ]
      
      fieldsToCompare.forEach(field => {
        const oldValue = this.originalRisk[field] || null
        const newValue = this.editRisk[field] || null
        
        // Normalize values for comparison
        const normalizeValue = (val) => {
          if (val === null || val === undefined || val === '') return null
          if (typeof val === 'string') return val.trim()
          return val
        }
        
        const normalizedOld = normalizeValue(oldValue)
        const normalizedNew = normalizeValue(newValue)
        
        // Handle RiskLikelihood and RiskImpact - convert numbers to labels if needed
        if (field === 'RiskLikelihood' || field === 'RiskImpact') {
          const oldLabel = this.getRiskScoreLabel(normalizedOld)
          const newLabel = this.getRiskScoreLabel(normalizedNew)
          if (oldLabel !== newLabel) {
            changes[field] = {
              old: oldLabel || 'N/A',
              new: newLabel || 'N/A'
            }
          }
        } else if (normalizedOld !== normalizedNew) {
          changes[field] = {
            old: normalizedOld || 'N/A',
            new: normalizedNew || 'N/A'
          }
        }
      })
      
      return changes
    },
    
    getRiskScoreLabel(value) {
      if (!value) return null
      const option = this.riskScoreOptions.find(opt => opt.value === value || opt.value === parseInt(value))
      return option ? option.label : value
    },
    
    formatRiskFieldName(field) {
      const fieldNames = {
        RiskTitle: 'Risk Title',
        Category: 'Category',
        Criticality: 'Criticality',
        ComplianceId: 'Compliance ID',
        RiskDescription: 'Risk Description',
        BusinessImpact: 'Business Impact',
        PossibleDamage: 'Possible Damage',
        RiskLikelihood: 'Risk Likelihood',
        RiskImpact: 'Risk Impact',
        RiskExposureRating: 'Risk Exposure Rating',
        RiskPriority: 'Risk Priority',
        RiskMitigation: 'Risk Mitigation',
        RiskType: 'Risk Type'
      }
      return fieldNames[field] || field
    },
    
    openRiskRectificationModal() {
      const changes = this.getRiskChanges()
      if (Object.keys(changes).length === 0) {
        this.showError('No changes detected. Please make changes before requesting.')
        return
      }
      this.showRectificationModal = true
    },
    
    closeRiskRectificationModal() {
      this.showRectificationModal = false
    },
    
    async submitRiskRectificationRequest() {
      this.submittingRectification = true
      this.clearMessages()
      
      try {
        const changes = this.getRiskChanges()
        if (Object.keys(changes).length === 0) {
          this.showError('No changes detected.')
          this.submittingRectification = false
          return
        }
        
        // Get user ID from session or local storage
        const userId = this.getCurrentUserId()
        if (!userId) {
          this.showError('User ID not found. Please log in again.')
          this.submittingRectification = false
          return
        }
        
        const axios = (await import('axios')).default
        
        const response = await axios.post(
          API_ENDPOINTS.CREATE_DATA_SUBJECT_REQUEST,
          {
            request_type: 'RECTIFICATION',
            info_type: 'risk',
            risk_id: this.risk.RiskId,
            changes: changes
          }
        )
        
        if (response.data.status === 'success') {
          this.showSuccess('Risk rectification request submitted successfully!')
          this.closeRiskRectificationModal()
          
          // Exit edit mode
          this.isEditMode = false
          this.editRisk = { ...this.risk }
          
          setTimeout(() => {
            this.successMessage = ''
          }, 5000)
        } else {
          throw new Error(response.data.message || 'Failed to submit request')
        }
      } catch (error) {
        console.error('Error submitting risk rectification request:', error)
        this.showError(
          error.response?.data?.message ||
          error.response?.data?.error ||
          error.message ||
          'Failed to submit risk rectification request. Please try again.'
        )
      } finally {
        this.submittingRectification = false
      }
    },
    
    getCurrentUserId() {
      // Try to get user ID from various sources
      try {
        // Check localStorage
        const storedUser = localStorage.getItem('user')
        if (storedUser) {
          const user = JSON.parse(storedUser)
          return user.user_id || user.UserId || user.id
        }
        
        // Check sessionStorage
        const sessionUser = sessionStorage.getItem('user')
        if (sessionUser) {
          const user = JSON.parse(sessionUser)
          return user.user_id || user.UserId || user.id
        }
        
        // Try to get from RBAC context if available
        if (window.rbacContext && window.rbacContext.user_id) {
          return window.rbacContext.user_id
        }
        
        return null
      } catch (error) {
        console.error('Error getting user ID:', error)
        return null
      }
    }
  }
}
</script> 
