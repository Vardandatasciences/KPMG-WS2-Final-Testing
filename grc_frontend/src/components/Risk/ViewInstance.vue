<template>
  <div class="instance-view-container">
    <PopupModal />
    
    <div class="instance-view-header">
      <h2 class="instance-view-title">Risk Instance Details</h2>
      <div class="instance-view-header-actions">
        <button v-if="!isEditMode" class="instance-view-edit-button" @click="toggleEditMode">
          <i class="fas fa-edit"></i> Edit Instance
        </button>
        <button v-if="isEditMode" class="instance-view-request-button" @click="openInstanceRectificationModal" :disabled="!hasInstanceChanges()">
          <i class="fas fa-paper-plane"></i> Request
        </button>
        <button v-if="isEditMode" class="instance-view-cancel-button" @click="cancelEdit">
          <i class="fas fa-times"></i> Cancel
        </button>
        <button class="instance-view-back-button" @click="goBack">
          <i class="fas fa-arrow-left"></i> Back to Risk Instances
        </button>
      </div>
    </div>

    <div class="instance-view-details-card" v-if="instance">
      <div class="instance-view-details-header">
        <div class="instance-view-id-section">
          <span class="instance-view-id-label">Risk ID:</span>
          <span class="instance-view-id-value">{{ instance.RiskId }}</span>
          <span class="instance-view-id-label">Instance ID:</span>
          <span class="instance-view-id-value">{{ instance.RiskInstanceId }}</span>
        </div>
        <div class="instance-view-meta">
          <div class="instance-view-meta-item">
            <span class="instance-view-origin-badge">MANUAL</span>
          </div>
          <div class="instance-view-meta-item">
            <span v-if="!isEditMode" class="instance-view-category-badge">{{ instance.Category }}</span>
            <select v-if="isEditMode" v-model="editInstance.Category" class="instance-view-select">
              <option value="">Select Category</option>
              <option value="Operational">Operational</option>
              <option value="Financial">Financial</option>
              <option value="Technical">Technical</option>
              <option value="Strategic">Strategic</option>
              <option value="Compliance">Compliance</option>
              <option value="Reputational">Reputational</option>
            </select>
          </div>
          <div class="instance-view-meta-item">
            <span v-if="!isEditMode" :class="'instance-view-priority-' + instance.Criticality.toLowerCase()">
              {{ instance.Criticality }}
            </span>
            <select v-if="isEditMode" v-model="editInstance.Criticality" class="instance-view-select">
              <option value="">Select Criticality</option>
              <option value="Low">Low</option>
              <option value="Medium">Medium</option>
              <option value="High">High</option>
              <option value="Critical">Critical</option>
            </select>
          </div>
          <div class="instance-view-meta-item">
            <span v-if="!isEditMode" :class="'instance-view-status-' + (instance.RiskStatus ? instance.RiskStatus.toLowerCase().replace(/\s+/g, '-') : 'open')">
              {{ instance.RiskStatus || 'Open' }}
            </span>
            <select v-if="isEditMode" v-model="editInstance.RiskStatus" class="instance-view-select">
              <option value="">Select Status</option>
              <option value="Open">Open</option>
              <option value="In Progress">In Progress</option>
              <option value="Mitigated">Mitigated</option>
              <option value="Closed">Closed</option>
              <option value="Transferred">Transferred</option>
            </select>
          </div>
        </div>
      </div>

      <div class="instance-view-content">
        <div class="instance-view-content-row">
          <div class="instance-view-content-column">
            <h4 class="instance-view-section-title">Description:</h4>
            <div v-if="!isEditMode" class="instance-view-section-content">{{ instance.RiskDescription || 'Not specified' }}</div>
            <textarea v-if="isEditMode" v-model="editInstance.RiskDescription" class="instance-view-textarea" placeholder="Enter risk description" rows="4"></textarea>
          </div>
          <div class="instance-view-content-column">
            <h4 class="instance-view-section-title">Category:</h4>
            <div v-if="!isEditMode" class="instance-view-section-content">{{ instance.Category || 'Not specified' }}</div>
            <input v-if="isEditMode" v-model="editInstance.Category" class="instance-view-input" placeholder="Enter category" readonly />
          </div>
        </div>

        <div class="instance-view-content-row">
          <div class="instance-view-content-column">
            <h4 class="instance-view-section-title">Criticality:</h4>
            <div v-if="!isEditMode" class="instance-view-section-content">{{ instance.Criticality || 'Not specified' }}</div>
            <input v-if="isEditMode" v-model="editInstance.Criticality" class="instance-view-input" placeholder="Enter criticality" readonly />
          </div>
          <div class="instance-view-content-column">
            <h4 class="instance-view-section-title">Status:</h4>
            <div v-if="!isEditMode" class="instance-view-section-content">{{ instance.RiskStatus || 'Open' }}</div>
            <input v-if="isEditMode" v-model="editInstance.RiskStatus" class="instance-view-input" placeholder="Enter status" readonly />
          </div>
        </div>

        <div class="instance-view-content-row">
          <div class="instance-view-content-column">
            <h4 class="instance-view-section-title">Possible Damage:</h4>
            <div v-if="!isEditMode" class="instance-view-section-content">{{ instance.PossibleDamage || 'Not specified' }}</div>
            <textarea v-if="isEditMode" v-model="editInstance.PossibleDamage" class="instance-view-textarea" placeholder="Enter possible damage" rows="3"></textarea>
          </div>
          <div class="instance-view-content-column">
            <h4 class="instance-view-section-title">Risk Appetite:</h4>
            <div v-if="!isEditMode" class="instance-view-section-content">{{ instance.Appetite || 'Not specified' }}</div>
            <input v-if="isEditMode" v-model="editInstance.Appetite" class="instance-view-input" placeholder="Enter risk appetite" />
          </div>
        </div>

        <div class="instance-view-content-row">
          <div class="instance-view-content-column">
            <h4 class="instance-view-section-title">Likelihood:</h4>
            <div v-if="!isEditMode" class="instance-view-section-content">{{ instance.RiskLikelihood || 'Not specified' }}</div>
            <select v-if="isEditMode" v-model="editInstance.RiskLikelihood" class="instance-view-select">
              <option value="">Select Likelihood</option>
              <option value="Very Low">Very Low</option>
              <option value="Low">Low</option>
              <option value="Medium">Medium</option>
              <option value="High">High</option>
              <option value="Very High">Very High</option>
            </select>
          </div>
          <div class="instance-view-content-column">
            <h4 class="instance-view-section-title">Impact:</h4>
            <div v-if="!isEditMode" class="instance-view-section-content">{{ instance.RiskImpact || 'Not specified' }}</div>
            <select v-if="isEditMode" v-model="editInstance.RiskImpact" class="instance-view-select">
              <option value="">Select Impact</option>
              <option value="Very Low">Very Low</option>
              <option value="Low">Low</option>
              <option value="Medium">Medium</option>
              <option value="High">High</option>
              <option value="Very High">Very High</option>
            </select>
          </div>
        </div>

        <div class="instance-view-content-row">
          <div class="instance-view-content-column">
            <h4 class="instance-view-section-title">Exposure Rating:</h4>
            <div v-if="!isEditMode" class="instance-view-section-content">{{ instance.RiskExposureRating || 'Not specified' }}</div>
            <input v-if="isEditMode" v-model="editInstance.RiskExposureRating" class="instance-view-input" placeholder="Enter exposure rating" />
          </div>
          <div class="instance-view-content-column">
            <h4 class="instance-view-section-title">Priority:</h4>
            <div v-if="!isEditMode" class="instance-view-section-content">{{ instance.RiskPriority || 'Not specified' }}</div>
            <select v-if="isEditMode" v-model="editInstance.RiskPriority" class="instance-view-select">
              <option value="">Select Priority</option>
              <option value="Low">Low</option>
              <option value="Medium">Medium</option>
              <option value="High">High</option>
              <option value="Critical">Critical</option>
            </select>
          </div>
        </div>

        <div class="instance-view-content-row">
          <div class="instance-view-content-column">
            <h4 class="instance-view-section-title">Response Type:</h4>
            <div v-if="!isEditMode" class="instance-view-section-content">{{ instance.RiskResponseType || 'Not specified' }}</div>
            <select v-if="isEditMode" v-model="editInstance.RiskResponseType" class="instance-view-select">
              <option value="">Select Response Type</option>
              <option value="Accept">Accept</option>
              <option value="Avoid">Avoid</option>
              <option value="Mitigate">Mitigate</option>
              <option value="Transfer">Transfer</option>
            </select>
          </div>
          <div class="instance-view-content-column">
            <h4 class="instance-view-section-title">Response Description:</h4>
            <div v-if="!isEditMode" class="instance-view-section-content">{{ instance.RiskResponseDescription || 'Not specified' }}</div>
            <textarea v-if="isEditMode" v-model="editInstance.RiskResponseDescription" class="instance-view-textarea" placeholder="Enter response description" rows="3"></textarea>
          </div>
        </div>

        <div class="instance-view-content-row">
          <div class="instance-view-content-column">
            <h4 class="instance-view-section-title">Mitigation:</h4>
            <div v-if="!isEditMode" class="instance-view-section-content">{{ instance.RiskMitigation || 'Not specified' }}</div>
            <textarea v-if="isEditMode" v-model="editInstance.RiskMitigation" class="instance-view-textarea" placeholder="Enter risk mitigation" rows="3"></textarea>
          </div>
          <div class="instance-view-content-column">
            <h4 class="instance-view-section-title">Risk Owner:</h4>
            <div v-if="!isEditMode" class="instance-view-section-content">{{ instance.RiskOwner || 'Not assigned' }}</div>
            <input v-if="isEditMode" v-model="editInstance.RiskOwner" class="instance-view-input" placeholder="Enter risk owner" />
          </div>
        </div>
      </div>
    </div>

    <div v-else class="instance-view-no-data">
      Loading instance details or no instance found...
    </div>

    <!-- Success/Error Messages -->
    <div v-if="successMessage" class="instance-view-success-message">
      <i class="fas fa-check-circle"></i> {{ successMessage }}
    </div>
    <div v-if="errorMessage" class="instance-view-error-message">
      <i class="fas fa-exclamation-circle"></i> {{ errorMessage }}
    </div>

    <!-- Risk Instance Rectification Request Modal -->
    <div v-if="showRectificationModal" class="instance-rectification-modal-overlay" @click="closeInstanceRectificationModal">
      <div class="instance-rectification-modal-content" @click.stop>
        <div class="instance-rectification-modal-header">
          <h3>
            <i class="fas fa-file-alt"></i>
            Request Rectification of Risk Instance Information
          </h3>
          <button class="instance-rectification-modal-close-btn" @click="closeInstanceRectificationModal">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="instance-rectification-modal-body">
          <p class="instance-rectification-modal-message">
            You are requesting to update risk instance information. The changes will be reviewed and approved by an administrator.
          </p>
          <div class="instance-rectification-changes-summary" v-if="Object.keys(getInstanceChanges()).length > 0">
            <h4>Changes Summary:</h4>
            <ul class="instance-rectification-changes-list">
              <li v-for="(change, field) in getInstanceChanges()" :key="field">
                <strong>{{ formatInstanceFieldName(field) }}:</strong>
                <span class="instance-rectification-old-value">{{ change.old || 'N/A' }}</span> →
                <span class="instance-rectification-new-value">{{ change.new || 'N/A' }}</span>
              </li>
            </ul>
          </div>

          <!-- Impact Analysis Section -->
          <div class="instance-impact-analysis-panel" v-if="Object.keys(getInstanceChanges()).length > 0">
            <div class="instance-impact-analysis-header" @click="toggleImpactAnalysis">
              <h4>
                <i class="fas fa-chart-line"></i>
                Impact Analysis
              </h4>
              <button class="instance-impact-toggle-btn" type="button">
                <i :class="showImpactAnalysis ? 'fas fa-chevron-up' : 'fas fa-chevron-down'"></i>
              </button>
            </div>
            <div v-if="showImpactAnalysis" class="instance-impact-analysis-content">
              <div class="instance-impact-loading" v-if="analyzingImpact">
                <i class="fas fa-spinner fa-spin"></i> Analyzing impact...
              </div>
              <div v-else>
                <!-- Risk Level Indicator -->
                <div class="instance-impact-risk-level">
                  <div class="instance-impact-risk-badge" :class="'risk-level-' + impactAnalysis.riskLevel.toLowerCase()">
                    <i class="fas fa-exclamation-triangle"></i>
                    Risk Level: {{ impactAnalysis.riskLevel }}
                  </div>
                </div>

                <!-- Affected Modules -->
                <div class="instance-impact-section">
                  <h5><i class="fas fa-cubes"></i> Affected Modules</h5>
                  <ul class="instance-impact-list">
                    <li v-for="module in impactAnalysis.affectedModules" :key="module">
                      <strong>{{ module }}</strong>
                    </li>
                  </ul>
                </div>

                <!-- Affected Users -->
                <div class="instance-impact-section">
                  <h5><i class="fas fa-users"></i> Affected Users</h5>
                  <ul class="instance-impact-list">
                    <li v-for="user in impactAnalysis.affectedUsers" :key="user">
                      <strong>{{ user }}</strong>
                    </li>
                  </ul>
                </div>

                <!-- Dependencies -->
                <div class="instance-impact-section">
                  <h5><i class="fas fa-project-diagram"></i> Dependencies</h5>
                  <ul class="instance-impact-list">
                    <li v-for="dependency in impactAnalysis.dependencies" :key="dependency">
                      <strong>{{ dependency }}</strong>
                    </li>
                  </ul>
                </div>

                <!-- Impact Report -->
                <div class="instance-impact-section">
                  <h5><i class="fas fa-file-alt"></i> Impact Report</h5>
                  <div class="instance-impact-report">
                    <div class="instance-impact-report-item">
                      <span class="instance-impact-report-label">Affected Components:</span>
                      <span class="instance-impact-report-value">{{ impactAnalysis.affectedComponents.length }}</span>
                    </div>
                    <div class="instance-impact-report-item">
                      <span class="instance-impact-report-label">Estimated Impact:</span>
                      <span class="instance-impact-report-value">{{ impactAnalysis.estimatedImpact }}</span>
                    </div>
                    <div class="instance-impact-report-item">
                      <span class="instance-impact-report-label">Risk Assessment:</span>
                      <span class="instance-impact-report-value" :class="'risk-assessment-' + impactAnalysis.riskLevel.toLowerCase()">
                        {{ impactAnalysis.riskAssessment }}
                      </span>
                    </div>
                  </div>
                </div>

                <!-- Recommendations -->
                <div class="instance-impact-section">
                  <h5><i class="fas fa-lightbulb"></i> Recommendations</h5>
                  <ul class="instance-impact-list">
                    <li v-for="(recommendation, index) in impactAnalysis.recommendations" :key="index">
                      {{ recommendation }}
                    </li>
                  </ul>
                </div>

                <!-- High-Risk Areas -->
                <div class="instance-impact-warning" v-if="impactAnalysis.highRiskAreas.length > 0">
                  <i class="fas fa-exclamation-triangle"></i>
                  <div>
                    <strong>High-Risk Areas Detected:</strong>
                    <ul class="instance-impact-list">
                      <li v-for="area in impactAnalysis.highRiskAreas" :key="area">{{ area }}</li>
                    </ul>
                  </div>
                </div>

                <!-- Mitigation Steps -->
                <div class="instance-impact-section">
                  <h5><i class="fas fa-shield-alt"></i> Suggested Mitigation Steps</h5>
                  <ul class="instance-impact-list">
                    <li v-for="(step, index) in impactAnalysis.mitigationSteps" :key="index">
                      <strong>Step {{ index + 1 }}:</strong> {{ step }}
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="instance-rectification-modal-footer">
          <button class="instance-rectification-modal-cancel-btn" @click="closeInstanceRectificationModal">
            Cancel
          </button>
          <button class="instance-rectification-modal-request-btn" @click="submitInstanceRectificationRequest" :disabled="submittingRectification">
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
import './ViewInstance.css'
import axios from 'axios'
import { PopupModal } from '@/modules/popup'
import { API_ENDPOINTS } from '../../config/api.js'

export default {
  name: 'ViewInstance',
  components: {
    PopupModal
  },
  data() {
    return {
      instance: null,
      editInstance: {},
      isEditMode: false,
      isSaving: false,
      originalInstance: {},
      successMessage: '',
      errorMessage: '',
      showRectificationModal: false,
      submittingRectification: false,
      showImpactAnalysis: true,
      analyzingImpact: false,
      impactAnalysis: {
        riskLevel: 'Medium',
        affectedModules: [],
        affectedUsers: [],
        dependencies: [],
        affectedComponents: [],
        estimatedImpact: 'Moderate',
        riskAssessment: 'Medium risk - Review recommended',
        recommendations: [],
        highRiskAreas: [],
        mitigationSteps: []
      }
    }
  },
  created() {
    this.fetchInstanceDetails()
  },
  methods: {
    async sendPushNotification(notificationData) {
      try {
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
    fetchInstanceDetails() {
      const instanceId = this.$route.params.id
      if (!instanceId) {
        this.$router.push('/risk/riskinstances-list')
        return
      }

      axios.get(API_ENDPOINTS.RISK_INSTANCE(instanceId))
        .then(response => {
          this.instance = response.data
          this.originalInstance = { ...response.data }
          this.editInstance = { ...response.data }
          // Send push notification for successful instance view
          this.sendPushNotification({
            title: 'Risk Instance Viewed',
            message: `Risk instance "${response.data.RiskId || 'Unknown Risk'}" has been viewed in the Risk module.`,
            category: 'risk',
            priority: 'medium',
            user_id: 'default_user'
          });
        })
        .catch(error => {
          console.error('Error fetching risk instance details:', error)
          this.showError('Failed to load risk instance details')
          // Send push notification for error
          this.sendPushNotification({
            title: 'Risk Instance View Failed',
            message: `Failed to load risk instance details: ${error.response?.data?.error || error.message}`,
            category: 'risk',
            priority: 'high',
            user_id: 'default_user'
          });
          // Try alternative endpoint if the first one fails
          this.tryAlternativeEndpoint(instanceId)
        })
    },
    
    toggleEditMode() {
      this.isEditMode = true
      this.editInstance = { ...this.instance }
      this.clearMessages()
    },

    cancelEdit() {
      this.isEditMode = false
      this.editInstance = { ...this.originalInstance }
      this.clearMessages()
    },

    async saveInstance() {
      if (!this.validateInstance()) {
        return
      }

      this.isSaving = true
      this.clearMessages()

      try {
        const response = await axios.put(API_ENDPOINTS.RISK_INSTANCE(this.instance.RiskInstanceId), this.editInstance)
        
        this.instance = response.data
        this.originalInstance = { ...response.data }
        this.isEditMode = false
        
        this.showSuccess('Risk instance updated successfully!')
        
        // Send push notification for successful update
        this.sendPushNotification({
          title: 'Risk Instance Updated',
          message: `Risk instance "${this.instance.RiskId}" has been successfully updated.`,
          category: 'risk',
          priority: 'medium',
          user_id: 'default_user'
        })
        
      } catch (error) {
        console.error('Error updating risk instance:', error)
        this.showError('Failed to update risk instance. Please try again.')
        
        // Send push notification for error
        this.sendPushNotification({
          title: 'Risk Instance Update Failed',
          message: `Failed to update risk instance: ${error.response?.data?.error || error.message}`,
          category: 'risk',
          priority: 'high',
          user_id: 'default_user'
        })
      } finally {
        this.isSaving = false
      }
    },

    validateInstance() {
      if (!this.editInstance.RiskId) {
        this.showError('Risk ID is required')
        return false
      }
      if (!this.editInstance.Category) {
        this.showError('Risk category is required')
        return false
      }
      if (!this.editInstance.Criticality) {
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
    
    tryAlternativeEndpoint(instanceId) {
      axios.get(API_ENDPOINTS.RISK_INSTANCE(instanceId))
        .then(response => {
          this.instance = response.data
          this.originalInstance = { ...response.data }
          this.editInstance = { ...response.data }
          // Send push notification for successful instance view via alternative endpoint
          this.sendPushNotification({
            title: 'Risk Instance Viewed',
            message: `Risk instance "${response.data.RiskId || 'Unknown Risk'}" has been viewed via alternative endpoint.`,
            category: 'risk',
            priority: 'medium',
            user_id: 'default_user'
          });
        })
        .catch(error => {
          console.error('Error with alternative endpoint:', error)
          this.showError('Failed to load risk instance details from both endpoints')
          // Send push notification for alternative endpoint error
          this.sendPushNotification({
            title: 'Risk Instance View Failed',
            message: `Failed to load risk instance details via alternative endpoint: ${error.response?.data?.error || error.message}`,
            category: 'risk',
            priority: 'high',
            user_id: 'default_user'
          });
        })
    },
    goBack() {
      this.$router.push('/risk/riskinstances-list')
    },
    
    hasInstanceChanges() {
      if (!this.isEditMode || !this.instance || !this.editInstance) return false
      const changes = this.getInstanceChanges()
      return Object.keys(changes).length > 0
    },
    
    getInstanceChanges() {
      const changes = {}
      if (!this.isEditMode || !this.instance || !this.editInstance) return changes
      
      // Compare each field
      const fieldsToCompare = [
        'RiskDescription',
        'Category',
        'Criticality',
        'RiskStatus',
        'PossibleDamage',
        'Appetite',
        'RiskLikelihood',
        'RiskImpact',
        'RiskExposureRating',
        'RiskPriority',
        'RiskResponseType',
        'RiskResponseDescription',
        'RiskMitigation',
        'RiskOwner'
      ]
      
      fieldsToCompare.forEach(field => {
        const oldValue = this.originalInstance[field] || null
        const newValue = this.editInstance[field] || null
        
        // Normalize values for comparison
        const normalizeValue = (val) => {
          if (val === null || val === undefined || val === '') return null
          if (typeof val === 'string') return val.trim()
          return val
        }
        
        const normalizedOld = normalizeValue(oldValue)
        const normalizedNew = normalizeValue(newValue)
        
        if (normalizedOld !== normalizedNew) {
          changes[field] = {
            old: normalizedOld || 'N/A',
            new: normalizedNew || 'N/A'
          }
        }
      })
      
      return changes
    },
    
    formatInstanceFieldName(field) {
      const fieldNames = {
        RiskDescription: 'Description',
        Category: 'Category',
        Criticality: 'Criticality',
        RiskStatus: 'Status',
        PossibleDamage: 'Possible Damage',
        Appetite: 'Risk Appetite',
        RiskLikelihood: 'Likelihood',
        RiskImpact: 'Impact',
        RiskExposureRating: 'Exposure Rating',
        RiskPriority: 'Priority',
        RiskResponseType: 'Response Type',
        RiskResponseDescription: 'Response Description',
        RiskMitigation: 'Mitigation',
        RiskOwner: 'Risk Owner'
      }
      return fieldNames[field] || field
    },
    
    openInstanceRectificationModal() {
      const changes = this.getInstanceChanges()
      if (Object.keys(changes).length === 0) {
        this.showError('No changes detected. Please make changes before requesting.')
        return
      }
      this.showRectificationModal = true
      this.analyzeImpact()
    },
    
    toggleImpactAnalysis() {
      this.showImpactAnalysis = !this.showImpactAnalysis
    },
    
    analyzeImpact() {
      this.analyzingImpact = true
      
      // Simulate analysis delay for better UX
      setTimeout(() => {
        const changes = this.getInstanceChanges()
        this.impactAnalysis = this.calculateInstanceImpact(changes)
        this.analyzingImpact = false
      }, 800)
    },
    
    calculateInstanceImpact(changes) {
      // Analyze changes and determine impact
      const affectedFields = Object.keys(changes)
      const criticalFields = ['RiskPriority', 'Criticality', 'RiskLikelihood', 'RiskImpact', 'RiskStatus', 'RiskExposureRating']
      const hasCriticalChanges = affectedFields.some(field => criticalFields.includes(field))
      
      // Determine risk level
      let riskLevel = 'Low'
      let riskScore = 0
      
      affectedFields.forEach(field => {
        if (criticalFields.includes(field)) {
          riskScore += 3
        } else if (['Category', 'RiskResponseType', 'RiskMitigation'].includes(field)) {
          riskScore += 2
        } else {
          riskScore += 1
        }
      })
      
      if (riskScore >= 10 || hasCriticalChanges) {
        riskLevel = 'High'
      } else if (riskScore >= 5) {
        riskLevel = 'Medium'
      }
      
      // Determine affected modules based on changes
      const affectedModules = []
      if (changes.Category) affectedModules.push('Risk Management', 'Compliance Module')
      if (changes.RiskStatus) {
        affectedModules.push('Workflow Engine', 'Status Tracking', 'Notification System')
      }
      if (changes.RiskMitigation) affectedModules.push('Risk Handling', 'Mitigation Workflows')
      if (changes.RiskPriority || changes.Criticality) {
        affectedModules.push('Risk Dashboard', 'Analytics Module', 'Reporting System')
      }
      if (changes.RiskLikelihood || changes.RiskImpact) {
        affectedModules.push('Risk Scoring', 'Heatmap Visualization', 'Risk Metrics')
      }
      if (changes.RiskResponseType) {
        affectedModules.push('Response Management', 'Action Tracking')
      }
      if (changes.RiskOwner) {
        affectedModules.push('User Assignment', 'Notification System')
      }
      
      // Remove duplicates
      const uniqueModules = [...new Set(affectedModules)]
      
      // Determine affected users
      const affectedUsers = []
      if (this.instance && this.instance.RiskOwner) {
        affectedUsers.push(this.instance.RiskOwner)
      }
      if (this.instance && this.instance.UserId) {
        affectedUsers.push('Assigned User (ID: ' + this.instance.UserId + ')')
      }
      if (changes.RiskPriority || changes.Criticality) {
        affectedUsers.push('Risk Managers', 'Compliance Officers', 'Executive Team')
      }
      if (changes.RiskStatus) {
        affectedUsers.push('Workflow Participants', 'Status Reviewers', 'Assigned Users')
      }
      if (changes.RiskMitigation) {
        affectedUsers.push('Risk Handlers', 'Assigned Users', 'Reviewers')
      }
      if (changes.RiskOwner) {
        affectedUsers.push('New Risk Owner', 'Previous Risk Owner')
      }
      const uniqueUsers = [...new Set(affectedUsers)]
      
      // Determine dependencies
      const dependencies = []
      if (changes.RiskMitigation) {
        dependencies.push('Mitigation Workflows', 'Approval Processes', 'Risk Handling Steps')
      }
      if (changes.Category) {
        dependencies.push('Category Filters', 'Risk Classifications', 'Reporting Queries')
      }
      if (changes.RiskPriority || changes.Criticality) {
        dependencies.push('Risk Heatmaps', 'Dashboard Widgets', 'KPI Calculations', 'Analytics Reports')
      }
      if (changes.RiskStatus) {
        dependencies.push('Status Workflows', 'State Transitions', 'Notification Rules')
      }
      if (changes.RiskResponseType) {
        dependencies.push('Response Actions', 'Mitigation Plans', 'Transfer Processes')
      }
      if (changes.RiskOwner) {
        dependencies.push('User Permissions', 'Assignment History', 'Notification Preferences')
      }
      const uniqueDependencies = [...new Set(dependencies)]
      
      // Affected components
      const affectedComponents = []
      if (changes.RiskDescription) {
        affectedComponents.push('Instance Details View', 'Instance List Display', 'Search Index')
      }
      if (changes.Category) {
        affectedComponents.push('Category Filters', 'Instance Grouping', 'Category Analytics')
      }
      if (changes.RiskPriority || changes.Criticality) {
        affectedComponents.push('Priority Badges', 'Criticality Indicators', 'Sorting Logic', 'Filter Options')
      }
      if (changes.RiskLikelihood || changes.RiskImpact) {
        affectedComponents.push('Risk Heatmap', 'Risk Matrix', 'Scoring Calculations')
      }
      if (changes.RiskStatus) {
        affectedComponents.push('Status Badges', 'Workflow UI', 'Status Filters', 'Progress Tracking')
      }
      if (changes.RiskMitigation) {
        affectedComponents.push('Mitigation Display', 'Workflow Steps', 'Approval Forms')
      }
      if (changes.RiskOwner) {
        affectedComponents.push('Owner Display', 'Assignment UI', 'User Filters')
      }
      
      // Estimated impact
      let estimatedImpact = 'Low'
      if (riskScore >= 10) {
        estimatedImpact = 'High - Significant system-wide impact expected'
      } else if (riskScore >= 5) {
        estimatedImpact = 'Moderate - Multiple components affected'
      } else {
        estimatedImpact = 'Low - Limited impact scope'
      }
      
      // Risk assessment
      let riskAssessment = 'Low risk - Changes are safe to proceed'
      if (riskLevel === 'High') {
        riskAssessment = 'High risk - Requires thorough review and approval'
      } else if (riskLevel === 'Medium') {
        riskAssessment = 'Medium risk - Review recommended before approval'
      }
      
      // Recommendations
      const recommendations = []
      if (hasCriticalChanges) {
        recommendations.push('Notify all stakeholders before applying changes')
        recommendations.push('Schedule a review meeting with risk management team')
        recommendations.push('Update related workflows and assignments')
      }
      if (changes.RiskStatus) {
        recommendations.push('Verify status transition is valid and authorized')
        recommendations.push('Check if status change triggers any automated workflows')
        recommendations.push('Notify users affected by status change')
      }
      if (changes.RiskPriority || changes.Criticality) {
        recommendations.push('Verify impact on risk heatmaps and dashboards')
        recommendations.push('Check if changes affect active workflows')
        recommendations.push('Update risk metrics and KPI calculations')
      }
      if (changes.RiskOwner) {
        recommendations.push('Verify new owner has appropriate permissions')
        recommendations.push('Transfer any pending tasks to new owner')
        recommendations.push('Notify both previous and new owners')
      }
      if (changes.RiskMitigation) {
        recommendations.push('Review mitigation steps with assigned users')
        recommendations.push('Update workflow approvals if needed')
      }
      if (recommendations.length === 0) {
        recommendations.push('Changes appear safe - standard review process applies')
      }
      
      // High-risk areas
      const highRiskAreas = []
      if (changes.RiskStatus && (this.editInstance.RiskStatus === 'Closed' || this.editInstance.RiskStatus === 'Mitigated')) {
        highRiskAreas.push('Status change may close active workflows and prevent further edits')
      }
      if (changes.RiskPriority && (this.editInstance.RiskPriority === 'Critical' || this.editInstance.RiskPriority === 'High')) {
        highRiskAreas.push('Priority escalation may trigger alerts and notifications')
      }
      if (changes.Criticality && (this.editInstance.Criticality === 'Critical' || this.editInstance.Criticality === 'High')) {
        highRiskAreas.push('Criticality change affects risk scoring and heatmap positioning')
      }
      if (changes.RiskLikelihood || changes.RiskImpact) {
        highRiskAreas.push('Score changes impact risk matrix and exposure calculations')
      }
      if (changes.RiskOwner) {
        highRiskAreas.push('Owner change may affect access permissions and notifications')
      }
      
      // Mitigation steps
      const mitigationSteps = []
      mitigationSteps.push('Review all affected modules and components listed above')
      mitigationSteps.push('Notify affected users about pending changes')
      if (hasCriticalChanges) {
        mitigationSteps.push('Create backup of current instance data before applying changes')
        mitigationSteps.push('Test changes in a staging environment if available')
      }
      if (changes.RiskStatus) {
        mitigationSteps.push('Verify status transition rules and permissions')
      }
      if (changes.RiskOwner) {
        mitigationSteps.push('Ensure new owner has required access and training')
      }
      mitigationSteps.push('Monitor system after changes are applied')
      mitigationSteps.push('Update documentation if instance structure changes significantly')
      
      return {
        riskLevel,
        affectedModules: uniqueModules,
        affectedUsers: uniqueUsers,
        dependencies: uniqueDependencies,
        affectedComponents,
        estimatedImpact,
        riskAssessment,
        recommendations,
        highRiskAreas,
        mitigationSteps
      }
    },
    
    closeInstanceRectificationModal() {
      this.showRectificationModal = false
    },
    
    async submitInstanceRectificationRequest() {
      this.submittingRectification = true
      this.clearMessages()
      
      try {
        const changes = this.getInstanceChanges()
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
        
        // Get impact analysis before submitting
        const impactAnalysis = this.calculateInstanceImpact(changes)
        
        const response = await axios.post(
          API_ENDPOINTS.CREATE_DATA_SUBJECT_REQUEST,
          {
            request_type: 'RECTIFICATION',
            info_type: 'risk_instance',
            risk_instance_id: this.instance.RiskInstanceId,
            risk_id: this.instance.RiskId,
            changes: changes,
            impact_analysis: impactAnalysis
          }
        )
        
        if (response.data.status === 'success') {
          this.showSuccess('Risk instance rectification request submitted successfully!')
          this.closeInstanceRectificationModal()
          
          // Exit edit mode
          this.isEditMode = false
          this.editInstance = { ...this.instance }
          
          setTimeout(() => {
            this.successMessage = ''
          }, 5000)
        } else {
          throw new Error(response.data.message || 'Failed to submit request')
        }
      } catch (error) {
        console.error('Error submitting risk instance rectification request:', error)
        this.showError(
          error.response?.data?.message ||
          error.response?.data?.error ||
          error.message ||
          'Failed to submit risk instance rectification request. Please try again.'
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
