<template>
  <div class="risk-instance-ai-container" :class="{ 'sidebar-collapsed': isSidebarCollapsed }">
    <!-- Header -->
    <div class="page-header">
      <div class="header-content">
        <h1><i class="fas fa-robot"></i> AI-Powered Risk Instance Document Ingestion</h1>
        <p class="subtitle">Upload documents and let AI extract and predict risk instance information automatically</p>
      </div>
    </div>

    <!-- Upload Section -->
    <div v-if="currentStep === 'upload'" class="upload-section">
      <div class="upload-card">
        <div class="upload-card-header">
          <h2>Upload Risk Instance Document</h2>
          <button
            type="button"
            class="btn-clear-cache"
            @click="clearCache"
            title="Clear saved processing state"
            aria-label="Clear cache"
          >
            <i class="fas fa-broom"></i>
          </button>
        </div>
        <p class="upload-subtext">Supported formats: PDF, DOCX, Excel (XLSX, XLS), TXT</p>

        <div class="upload-guidelines" aria-hidden="true">
          <div class="guide-item">
            <i class="fas fa-shield-alt"></i>
            <span>Secure & private</span>
          </div>
          <div class="guide-item">
            <i class="fas fa-file-medical"></i>
            <span>Clean text extraction</span>
          </div>
          <div class="guide-item">
            <i class="fas fa-magic"></i>
            <span>AI-assisted fields</span>
          </div>
        </div>
        
        <div class="file-input-wrapper">
          <label for="fileUpload" class="file-label btn-upload-document" title="Click to select a file">
            <input 
              type="file" 
              ref="fileInput" 
              @change="handleFileSelect" 
              accept=".pdf,.docx,.xlsx,.xls,.txt"
              id="fileUpload"
            />
            <i class="fas fa-file-upload"></i>
            <span class="file-label-text">{{ selectedFile ? selectedFile.name : 'Choose File' }}</span>
          </label>
          
          <button 
            @click="uploadAndProcess" 
            :disabled="!selectedFile || isProcessing"
            class="btn-primary"
          >
            <i class="fas fa-magic"></i>
            Process with AI
          </button>
        </div>
      </div>
    </div>

    <!-- Processing Section -->
    <div v-if="currentStep === 'processing'" class="processing-section">
      <div class="processing-card">
        <div class="spinner-container">
          <div class="spinner"></div>
        </div>
        <h2>AI Processing Risk Instance Document...</h2>
        <p class="processing-text">{{ processingStatus }}</p>
        
        <div class="progress-container">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: processingProgress + '%' }"></div>
          </div>
          <span class="progress-text">{{ processingProgress }}%</span>
        </div>

        <!-- Enhanced Progress Info -->
        <div v-if="progressDetails.estimatedFields > 0" class="ai-progress-details">
          <div class="progress-stats">
            <div class="stat-item">
              <i class="fas fa-file-alt"></i>
              <span class="stat-label">Document Size:</span>
              <span class="stat-value">{{ formatFileSize(selectedFile?.size || 0) }}</span>
            </div>
            <div class="stat-item">
              <i class="fas fa-robot"></i>
              <span class="stat-label">AI Fields:</span>
              <span class="stat-value">{{ currentProcessingPhase === 'ai' ? getFieldProgressText() : progressDetails.estimatedFields }}</span>
            </div>
            <div v-if="progressDetails.estimatedTime > 0" class="stat-item">
              <i class="fas fa-clock"></i>
              <span class="stat-label">Est. Time:</span>
              <span class="stat-value">{{ formatTime(progressDetails.estimatedTime) }}</span>
            </div>
          </div>
          <div class="processing-phases">
            <div class="phase" :class="{ 'active': currentProcessingPhase === 'upload', 'completed': currentProcessingPhase !== 'upload' && processingProgress > 10 }">
              <i class="fas fa-upload"></i> Upload & Parse
            </div>
            <div class="phase" :class="{ 'active': currentProcessingPhase === 'extract', 'completed': currentProcessingPhase !== 'extract' && processingProgress > 40 }">
              <i class="fas fa-search"></i> Text Extraction
            </div>
            <div class="phase" :class="{ 'active': currentProcessingPhase === 'ai', 'completed': currentProcessingPhase !== 'ai' && processingProgress > 70 }">
              <i class="fas fa-brain"></i> AI Field Generation
            </div>
            <div class="phase" :class="{ 'active': currentProcessingPhase === 'finalize', 'completed': processingProgress === 100 }">
              <i class="fas fa-check"></i> Finalization
            </div>
          </div>
        </div>

        <div class="processing-actions">
          <button
            type="button"
            class="btn btn-cancel"
            @click="cancelProcessing"
          >
            <i class="fas fa-stop-circle"></i>
            Cancel Processing
          </button>
        </div>
      </div>
    </div>

    <!-- Review Section -->
    <div v-if="currentStep === 'review'" class="review-section">
      <div class="review-header">
        <h2><i class="fas fa-edit"></i> Review Extracted Risk Instances</h2>
        <p>{{ extractedRiskInstances.length }} risk instance(s) found. Review and edit before saving.</p>
        <div class="ai-stats-panel kpi-grid">
          <div class="kpi-card">
            <div class="kpi-card-icon">
              <i class="fas fa-robot"></i>
            </div>
            <div class="kpi-card-body">
              <p class="kpi-card-title">AI-Generated Fields</p>
              <p class="kpi-card-value">{{ getTotalAIFields() }}</p>
            </div>
          </div>
          <div class="kpi-card">
            <div class="kpi-card-icon">
              <i class="fas fa-percentage"></i>
            </div>
            <div class="kpi-card-body">
              <p class="kpi-card-title">Avg Confidence</p>
              <p class="kpi-card-value">{{ getAverageConfidence() }}%</p>
            </div>
          </div>
          <div class="kpi-card">
            <div class="kpi-card-icon">
              <i class="fas fa-chart-line"></i>
            </div>
            <div class="kpi-card-body">
              <p class="kpi-card-title">Field Coverage</p>
              <p class="kpi-card-value">{{ getFieldCoverage() }}%</p>
            </div>
          </div>
          <div class="kpi-card kpi-card-legend">
            <div class="kpi-card-icon">
              <i class="fas fa-robot"></i>
            </div>
            <div class="kpi-card-body">
              <p class="kpi-card-title">= AI Predicted with Confidence %</p>
            </div>
          </div>
        </div>
      </div>

      <div class="risks-container">
        <div v-for="(riskInstance, index) in extractedRiskInstances" :key="index" class="risk-card" :data-streaming-status="riskInstance._streamingStatus">
          <div class="risk-card-header">
            <h3>Risk Instance #{{ index + 1 }}</h3>
            <button @click="removeRiskInstance(index)" class="btn-remove">
              <i class="fas fa-trash"></i>
            </button>
          </div>

          <div class="risk-form">
            <div class="form-row">
              <div class="form-group">
                <label>
                  Risk Title <span class="required">*</span>
                  <span v-if="isAIGenerated(riskInstance, 'RiskTitle')" class="ai-indicator" :title="getAITooltip(riskInstance, 'RiskTitle')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(riskInstance, 'RiskTitle') }}%
                  </span>
                </label>
                <input 
                  v-model="riskInstance.RiskTitle" 
                  type="text" 
                  placeholder="Enter risk instance title"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(riskInstance, 'RiskTitle') }]"
                  :data-risk="index"
                  data-field="RiskTitle"
                />
              </div>
              <div class="form-group">
                <label>
                  Category
                  <span v-if="isAIGenerated(riskInstance, 'Category')" class="ai-indicator" :title="getAITooltip(riskInstance, 'Category')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(riskInstance, 'Category') }}%
                  </span>
                </label>
                <input 
                  v-model="riskInstance.Category" 
                  type="text" 
                  placeholder="e.g., Operational, Financial"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(riskInstance, 'Category') }]"
                  :data-risk="index"
                  data-field="Category"
                />
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label>
                  Criticality
                  <span v-if="isAIGenerated(riskInstance, 'Criticality')" class="ai-indicator" :title="getAITooltip(riskInstance, 'Criticality')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(riskInstance, 'Criticality') }}%
                  </span>
                </label>
                <select v-model="riskInstance.Criticality" :class="['form-control', { 'ai-generated-field': isAIGenerated(riskInstance, 'Criticality') }]" :data-risk="index" data-field="Criticality">
                  <option value="">Select Criticality</option>
                  <option value="Low">Low</option>
                  <option value="Medium">Medium</option>
                  <option value="High">High</option>
                  <option value="Critical">Critical</option>
                </select>
              </div>
              <div class="form-group">
                <label>
                  Risk Priority
                  <span v-if="isAIGenerated(riskInstance, 'RiskPriority')" class="ai-indicator" :title="getAITooltip(riskInstance, 'RiskPriority')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(riskInstance, 'RiskPriority') }}%
                  </span>
                </label>
                <select v-model="riskInstance.RiskPriority" :class="['form-control', { 'ai-generated-field': isAIGenerated(riskInstance, 'RiskPriority') }]">
                  <option value="">Select Priority</option>
                  <option value="Low">Low</option>
                  <option value="Medium">Medium</option>
                  <option value="High">High</option>
                  <option value="Critical">Critical</option>
                </select>
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label>
                  Origin
                  <span v-if="isAIGenerated(riskInstance, 'Origin')" class="ai-indicator" :title="getAITooltip(riskInstance, 'Origin')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(riskInstance, 'Origin') }}%
                  </span>
                </label>
                <select v-model="riskInstance.Origin" :class="['form-control', { 'ai-generated-field': isAIGenerated(riskInstance, 'Origin') }]">
                  <option value="">Select Origin</option>
                  <option value="Internal">Internal</option>
                  <option value="External">External</option>
                  <option value="Third-Party">Third-Party</option>
                  <option value="Regulatory">Regulatory</option>
                  <option value="Market">Market</option>
                  <option value="Operational">Operational</option>
                </select>
              </div>
              <div class="form-group">
                <label>
                  Risk Owner
                  <span v-if="isAIGenerated(riskInstance, 'RiskOwner')" class="ai-indicator" :title="getAITooltip(riskInstance, 'RiskOwner')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(riskInstance, 'RiskOwner') }}%
                  </span>
                </label>
                <input 
                  v-model="riskInstance.RiskOwner" 
                  type="text" 
                  placeholder="e.g., Risk Manager, IT Department"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(riskInstance, 'RiskOwner') }]"
                />
              </div>
            </div>

            <div class="form-row">
              <div class="form-group full-width">
                <label>
                  Risk Description
                  <span v-if="isAIGenerated(riskInstance, 'RiskDescription')" class="ai-indicator" :title="getAITooltip(riskInstance, 'RiskDescription')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(riskInstance, 'RiskDescription') }}%
                  </span>
                </label>
                <textarea 
                  v-model="riskInstance.RiskDescription" 
                  placeholder="Detailed description of the risk instance"
                  rows="3"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(riskInstance, 'RiskDescription') }]"
                ></textarea>
              </div>
            </div>

            <div class="form-row">
              <div class="form-group full-width">
                <label>
                  Possible Damage
                  <span v-if="isAIGenerated(riskInstance, 'PossibleDamage')" class="ai-indicator" :title="getAITooltip(riskInstance, 'PossibleDamage')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(riskInstance, 'PossibleDamage') }}%
                  </span>
                </label>
                <textarea 
                  v-model="riskInstance.PossibleDamage" 
                  placeholder="What damage could this risk instance cause?"
                  rows="2"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(riskInstance, 'PossibleDamage') }]"
                ></textarea>
              </div>
            </div>

            <div class="form-row">
              <div class="form-group full-width">
                <label>
                  Business Impact
                  <span v-if="isAIGenerated(riskInstance, 'BusinessImpact')" class="ai-indicator" :title="getAITooltip(riskInstance, 'BusinessImpact')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(riskInstance, 'BusinessImpact') }}%
                  </span>
                </label>
                <textarea 
                  v-model="riskInstance.BusinessImpact" 
                  placeholder="Business impact description"
                  rows="2"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(riskInstance, 'BusinessImpact') }]"
                ></textarea>
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label>
                  Risk Likelihood (1-10)
                  <span v-if="isAIGenerated(riskInstance, 'RiskLikelihood')" class="ai-indicator" :title="getAITooltip(riskInstance, 'RiskLikelihood')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(riskInstance, 'RiskLikelihood') }}%
                  </span>
                </label>
                <input 
                  v-model.number="riskInstance.RiskLikelihood" 
                  type="number" 
                  min="1" 
                  max="10"
                  placeholder="1-10"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(riskInstance, 'RiskLikelihood') }]"
                />
              </div>
              <div class="form-group">
                <label>
                  Risk Impact (1-10)
                  <span v-if="isAIGenerated(riskInstance, 'RiskImpact')" class="ai-indicator" :title="getAITooltip(riskInstance, 'RiskImpact')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(riskInstance, 'RiskImpact') }}%
                  </span>
                </label>
                <input 
                  v-model.number="riskInstance.RiskImpact" 
                  type="number" 
                  min="1" 
                  max="10"
                  placeholder="1-10"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(riskInstance, 'RiskImpact') }]"
                />
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label>
                  Risk Exposure Rating (0-100)
                  <span v-if="isAIGenerated(riskInstance, 'RiskExposureRating')" class="ai-indicator" :title="getAITooltip(riskInstance, 'RiskExposureRating')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(riskInstance, 'RiskExposureRating') }}%
                  </span>
                </label>
                <input 
                  v-model.number="riskInstance.RiskExposureRating" 
                  type="number" 
                  step="0.01"
                  min="0" 
                  max="100"
                  placeholder="0-100"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(riskInstance, 'RiskExposureRating') }]"
                  readonly
                />
              </div>
              <div class="form-group">
                <label>
                  Appetite
                  <span v-if="isAIGenerated(riskInstance, 'Appetite')" class="ai-indicator" :title="getAITooltip(riskInstance, 'Appetite')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(riskInstance, 'Appetite') }}%
                  </span>
                </label>
                <select v-model="riskInstance.Appetite" :class="['form-control', { 'ai-generated-field': isAIGenerated(riskInstance, 'Appetite') }]">
                  <option value="">Select Appetite</option>
                  <option value="Low">Low</option>
                  <option value="Medium">Medium</option>
                  <option value="High">High</option>
                </select>
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label>
                  Risk Multiplier X
                  <span v-if="isAIGenerated(riskInstance, 'RiskMultiplierX')" class="ai-indicator" :title="getAITooltip(riskInstance, 'RiskMultiplierX')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(riskInstance, 'RiskMultiplierX') }}%
                  </span>
                </label>
                <input 
                  v-model.number="riskInstance.RiskMultiplierX" 
                  type="number" 
                  step="0.1"
                  min="0.1" 
                  max="2.0"
                  placeholder="0.1-2.0"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(riskInstance, 'RiskMultiplierX') }]"
                />
              </div>
              <div class="form-group">
                <label>
                  Risk Multiplier Y
                  <span v-if="isAIGenerated(riskInstance, 'RiskMultiplierY')" class="ai-indicator" :title="getAITooltip(riskInstance, 'RiskMultiplierY')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(riskInstance, 'RiskMultiplierY') }}%
                  </span>
                </label>
                <input 
                  v-model.number="riskInstance.RiskMultiplierY" 
                  type="number" 
                  step="0.1"
                  min="0.1" 
                  max="2.0"
                  placeholder="0.1-2.0"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(riskInstance, 'RiskMultiplierY') }]"
                />
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label>
                  Risk Type
                  <span v-if="isAIGenerated(riskInstance, 'RiskType')" class="ai-indicator" :title="getAITooltip(riskInstance, 'RiskType')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(riskInstance, 'RiskType') }}%
                  </span>
                </label>
                <select v-model="riskInstance.RiskType" :class="['form-control', { 'ai-generated-field': isAIGenerated(riskInstance, 'RiskType') }]">
                  <option value="">Select Risk Type</option>
                  <option value="Current">Current</option>
                  <option value="Residual">Residual</option>
                  <option value="Inherent">Inherent</option>
                  <option value="Emerging">Emerging</option>
                  <option value="Accepted">Accepted</option>
                </select>
              </div>
              <div class="form-group">
                <label>
                  Risk Response Type
                  <span v-if="isAIGenerated(riskInstance, 'RiskResponseType')" class="ai-indicator" :title="getAITooltip(riskInstance, 'RiskResponseType')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(riskInstance, 'RiskResponseType') }}%
                  </span>
                </label>
                <select v-model="riskInstance.RiskResponseType" :class="['form-control', { 'ai-generated-field': isAIGenerated(riskInstance, 'RiskResponseType') }]">
                  <option value="">Select Response Type</option>
                  <option value="Avoid">Avoid</option>
                  <option value="Mitigate">Mitigate</option>
                  <option value="Transfer">Transfer</option>
                  <option value="Accept">Accept</option>
                </select>
              </div>
            </div>

            <div class="form-row">
              <div class="form-group full-width">
                <label>
                  Risk Response Description
                  <span v-if="isAIGenerated(riskInstance, 'RiskResponseDescription')" class="ai-indicator" :title="getAITooltip(riskInstance, 'RiskResponseDescription')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(riskInstance, 'RiskResponseDescription') }}%
                  </span>
                </label>
                <textarea 
                  v-model="riskInstance.RiskResponseDescription" 
                  placeholder="Detailed description of risk response strategy"
                  rows="2"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(riskInstance, 'RiskResponseDescription') }]"
                ></textarea>
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label>
                  Risk Status
                  <span v-if="isAIGenerated(riskInstance, 'RiskStatus')" class="ai-indicator" :title="getAITooltip(riskInstance, 'RiskStatus')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(riskInstance, 'RiskStatus') }}%
                  </span>
                </label>
                <select v-model="riskInstance.RiskStatus" :class="['form-control', { 'ai-generated-field': isAIGenerated(riskInstance, 'RiskStatus') }]">
                  <option value="">Select Status</option>
                  <option value="Not Assigned">Not Assigned</option>
                  <option value="Assigned">Assigned</option>
                  <option value="Approved">Approved</option>
                  <option value="Rejected">Rejected</option>
                </select>
              </div>
              <div class="form-group">
                <label>
                  Mitigation Status
                  <span v-if="isAIGenerated(riskInstance, 'MitigationStatus')" class="ai-indicator" :title="getAITooltip(riskInstance, 'MitigationStatus')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(riskInstance, 'MitigationStatus') }}%
                  </span>
                </label>
                <select v-model="riskInstance.MitigationStatus" :class="['form-control', { 'ai-generated-field': isAIGenerated(riskInstance, 'MitigationStatus') }]">
                  <option value="">Select Status</option>
                  <option value="Pending">Pending</option>
                  <option value="Yet to Start">Yet to Start</option>
                  <option value="Work In Progress">Work In Progress</option>
                  <option value="Revision Required by Reviewer">Revision Required by Reviewer</option>
                  <option value="Revision Required by User">Revision Required by User</option>
                  <option value="Completed">Completed</option>
                </select>
              </div>
            </div>

            <div class="form-row">
              <div class="form-group full-width">
                <label>
                  Reviewer
                  <span v-if="isAIGenerated(riskInstance, 'Reviewer')" class="ai-indicator" :title="getAITooltip(riskInstance, 'Reviewer')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(riskInstance, 'Reviewer') }}%
                  </span>
                </label>
                <input 
                  v-model="riskInstance.Reviewer" 
                  type="text" 
                  placeholder="Name or role of reviewer"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(riskInstance, 'Reviewer') }]"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="action-buttons">
        <button @click="cancelReview" class="btn-cancel">
          Cancel
        </button>
        <button @click="saveAllRiskInstances" :disabled="isSaving" class="btn btn-submit">
          {{ isSaving ? 'Saving...' : 'Save All Risk Instances' }}
        </button>
      </div>
    </div>

    <!-- Success Section -->
    <div v-if="currentStep === 'success'" class="success-section">
      <div class="success-card">
        <div class="success-icon">
          <i class="fas fa-check-circle"></i>
        </div>
        <h2>Success!</h2>
        <p>{{ savedCount }} risk instance(s) have been successfully saved to the database.</p>
        <div class="action-buttons">
          <button @click="resetForm" class="btn-cancel">
            Upload Another
          </button>
          <button @click="viewRiskInstances" class="btn btn-submit btn-primary">
            View All Risk Instances
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import { API_ENDPOINTS } from '../../config/api.js';

export default {
  name: 'RiskInstanceAIDocumentUpload',
  data() {
    return {
      currentStep: 'upload', // upload, processing, review, success
      selectedFile: null,
      isProcessing: false,
      isSaving: false,
      processingStatus: 'Initializing...',
      processingProgress: 0,
      currentProcessingStep: 0,
      currentProcessingPhase: 'upload',
      extractedRiskInstances: [],
      savedCount: 0,
      isSidebarCollapsed: false,
      uploadController: null,
      progressDetails: {
        estimatedFields: 0,
        estimatedTime: 0,
        processedItems: 0
      }
    };
  },
  methods: {
    // Persistent state management
    saveProcessingState() {
      const state = {
        currentStep: this.currentStep,
        isProcessing: this.isProcessing,
        processingStatus: this.processingStatus,
        processingProgress: this.processingProgress,
        currentProcessingStep: this.currentProcessingStep,
        currentProcessingPhase: this.currentProcessingPhase,
        extractedRiskInstances: this.extractedRiskInstances,
        progressDetails: this.progressDetails,
        selectedFile: this.selectedFile ? { name: this.selectedFile.name, size: this.selectedFile.size } : null,
        timestamp: Date.now()
      };
      try {
        sessionStorage.setItem('risk_instance_ai_processing_state', JSON.stringify(state));
        console.log('💾 Risk Instance AI processing state saved:', state);
      } catch (error) {
        console.error('❌ Failed to save risk instance AI processing state:', error);
      }
    },

    loadProcessingState() {
      try {
        const savedState = sessionStorage.getItem('risk_instance_ai_processing_state');
        if (!savedState) {
          console.log('❌ No saved risk instance AI state found');
          return false;
        }

        const state = JSON.parse(savedState);

        // Check if state is not too old (24 hours max)
        const maxAge = 24 * 60 * 60 * 1000; // 24 hours in milliseconds
        if (Date.now() - state.timestamp > maxAge) {
          console.log('❌ Saved risk instance AI state is too old, clearing');
          sessionStorage.removeItem('risk_instance_ai_processing_state');
          return false;
        }

        // Restore state
        this.currentStep = state.currentStep || 'upload';
        this.isProcessing = state.isProcessing || false;
        this.processingStatus = state.processingStatus || 'Initializing...';
        this.processingProgress = state.processingProgress || 0;
        this.currentProcessingStep = state.currentProcessingStep || 0;
        this.currentProcessingPhase = state.currentProcessingPhase || 'upload';
        this.extractedRiskInstances = state.extractedRiskInstances || [];
        this.progressDetails = state.progressDetails || { estimatedFields: 0, estimatedTime: 0, processedItems: 0 };
        this.selectedFile = null; // Don't restore file object, just clear it

        console.log('✅ Risk Instance AI processing state restored:', state);
        return true;
      } catch (error) {
        console.error('❌ Failed to load risk instance AI processing state:', error);
        sessionStorage.removeItem('risk_instance_ai_processing_state');
        return false;
      }
    },

    clearProcessingState() {
      try {
        sessionStorage.removeItem('risk_instance_ai_processing_state');
        console.log('🗑️ Risk Instance AI processing state cleared');
      } catch (error) {
        console.error('❌ Failed to clear risk instance AI processing state:', error);
      }
    },

    clearCache() {
      this.clearProcessingState();
      this.selectedFile = null;
      if (this.$refs.fileInput) {
        this.$refs.fileInput.value = '';
      }
      this.$notify({
        type: 'success',
        title: 'Cache cleared',
        text: 'Processing state cleared. You can start a fresh upload.'
      });
    },

    resumeProcessingIfNeeded() {
      if (this.currentStep === 'processing' && this.isProcessing) {
        console.log('🔄 Resuming risk instance AI processing from step:', this.currentProcessingStep);
        // Continue from where it left off - progress will update naturally
        this.$notify({
          type: 'info',
          title: 'Resuming',
          text: `Resuming risk instance processing from ${this.processingProgress}%`
        });
      } else if (this.currentStep === 'review' && this.extractedRiskInstances.length > 0) {
        console.log('🔄 Risk Instance AI review data restored');
        this.$notify({
          type: 'info',
          title: 'Data Restored',
          text: `Restored ${this.extractedRiskInstances.length} risk instance(s) for review`
        });
      }
    },

    handleFileSelect(event) {
      const file = event.target.files[0];
      if (file) {
        const validTypes = [
          'application/pdf',
          'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
          'application/msword',
          'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
          'application/vnd.ms-excel'
        ];
        
        if (validTypes.includes(file.type) || 
            file.name.match(/\.(pdf|docx|doc|xlsx|xls)$/i)) {
          this.selectedFile = file;
        } else {
          this.$notify({
            type: 'error',
            title: 'Invalid File Type',
            text: 'Please upload a PDF, DOCX, or Excel file.'
          });
          event.target.value = '';
        }
      }
    },

    async uploadAndProcess() {
      if (!this.selectedFile) return;

      this.isProcessing = true;
      this.currentStep = 'processing';
      this.processingProgress = 0;
      this.currentProcessingStep = 1;
      this.currentProcessingPhase = 'upload';
      this.processingStatus = 'Uploading document...';
      this.extractedRiskInstances = [];
      this.streamingFieldUpdates = new Map(); // Track real-time field updates
      
      // Estimate fields and time based on file size
      this.estimateProcessingDetails();
      this.saveProcessingState();

      // Use non-streaming flow: upload then extract (same as original)
      await this.uploadAndProcessFallback();
    },

    async uploadAndProcessStreaming() {
      this.updateProgressWithPhase(5, 'upload', 'Connecting to streaming service...');

      const formData = new FormData();
      formData.append('file', this.selectedFile);
      formData.append('user_id', localStorage.getItem('user_id') || '1');

      try {
        // Use fetch for better SSE support
        // Note: Do NOT send Accept: text/event-stream - DRF content negotiation rejects it (406).
        // Server returns text/event-stream anyway; omit Accept so DRF allows the request.
        const headers = {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        };
        const response = await fetch(API_ENDPOINTS.RISK_INSTANCE_AI_UPLOAD_STREAM, {
          method: 'POST',
          body: formData,
          headers
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let riskInstances = [];

        return new Promise((resolve, reject) => {
          const processStream = async () => {
            try {
              // eslint-disable-next-line no-constant-condition
              while (true) {
                const { done, value } = await reader.read();
                
                if (done) {
                  resolve(riskInstances);
                  break;
                }

                buffer += decoder.decode(value, { stream: true });
                
                // Process complete lines
                const lines = buffer.split('\n');
                buffer = lines.pop(); // Keep incomplete line in buffer
                
                for (const line of lines) {
                  if (line.startsWith('data: ')) {
                    try {
                      const data = JSON.parse(line.substring(6));
                      this.handleStreamEvent(data);
                      
                      if (data.type === 'done') {
                        riskInstances = data.risk_instances;
                      } else if (data.type === 'error') {
                        reject(new Error(data.message));
                        return;
                      }
                    } catch (e) {
                      console.error('Error parsing SSE data:', e);
                    }
                  }
                }
              }
            } catch (error) {
              reject(error);
            }
          };

          processStream();
        });

      } catch (error) {
        console.error('Error setting up streaming:', error);
        throw error;
      }
    },

    async uploadAndProcessFallback() {
      // Original non-streaming method as fallback
      const formData = new FormData();
      formData.append('file', this.selectedFile);
      formData.append('user_id', localStorage.getItem('user_id') || '1');

      // Create AbortController for this upload so we can cancel it
      const controller = new AbortController();
      this.uploadController = controller;

      try {
        // Track upload progress in real-time
        const response = await axios.post(
        API_ENDPOINTS.RISK_INSTANCE_AI_UPLOAD,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          },
          timeout: 300000, // 5 minutes
          withCredentials: false,
          signal: controller.signal,
          onUploadProgress: (progressEvent) => {
            if (progressEvent.total) {
              const uploadPercent = Math.round((progressEvent.loaded * 30) / progressEvent.total); // 0-30% for upload
              this.updateProgressWithPhase(10 + uploadPercent, 'upload', 'Uploading document...');
              this.saveProcessingState();
            }
          }
        }
      );

        // Simulate processing phases after upload with field-by-field progress
        this.updateProgressWithPhase(40, 'extract', 'Extracting text from document...');
        await this.delay(800);
        
        // Simulate AI field generation with individual field updates
        const aiFields = [
          'Risk Title', 'Risk Description', 'Possible Damage', 'Risk Priority', 'Criticality',
          'Category', 'Origin', 'Risk Likelihood', 'Risk Impact', 'Risk Exposure Rating',
          'Risk Multipliers', 'Appetite', 'Risk Response Type', 'Risk Response Description',
          'Risk Mitigation', 'Risk Type', 'Risk Owner', 'Business Impact', 'Risk Status'
        ];
        
        const baseProgress = 45;
        const aiProgressRange = 40; // 45% to 85%
        
        for (let i = 0; i < aiFields.length; i++) {
          const fieldProgress = baseProgress + ((i + 1) / aiFields.length) * aiProgressRange;
          const fieldName = aiFields[i];
          this.updateProgressWithPhase(fieldProgress, 'ai', `Generating ${fieldName}...`);
          
          // Variable delay based on field complexity
          const delay = fieldName.includes('Description') || fieldName.includes('Mitigation') ? 
                       Math.random() * 800 + 600 :  // 600-1400ms for complex fields
                       Math.random() * 400 + 300;   // 300-700ms for simple fields
          await this.delay(delay);
        }
        
        this.updateProgressWithPhase(90, 'finalize', 'Finalizing results...');
        await this.delay(300);

        // Update progress immediately after response (backend processing is complete)
        this.updateProgressWithPhase(100, 'finalize', 'Processing complete!');
        this.currentProcessingStep = 4;
        this.saveProcessingState();
        this.uploadController = null;

        if (response.data.status === 'success') {
          const riskInstances = response.data.risk_instances || [];
          
          console.log('🔍 DEBUG: Raw risk instances from backend:', JSON.stringify(riskInstances[0]?._meta, null, 2));
          
          this.extractedRiskInstances = riskInstances.map((ri, idx) => {
            const meta = ri._meta || {};
            const perField = meta.per_field || {};
            
            const aiFieldsList = Object.keys(perField).filter(k => perField[k]?.source === 'AI_GENERATED');
            const extractedFieldsList = Object.keys(perField).filter(k => perField[k]?.source === 'EXTRACTED');
            
            console.log(`📋 Risk Instance ${idx + 1} Metadata Summary:`);
            console.log(`   ✓ Total fields with metadata: ${Object.keys(perField).length}`);
            console.log(`   🤖 AI Generated: ${aiFieldsList.length} fields`);
            console.log(`   📄 Extracted: ${extractedFieldsList.length} fields`);
            console.log(`   🎯 Sample AI fields:`, aiFieldsList.slice(0, 5));
            
            if (aiFieldsList.length === 0) {
              console.error('❌ CRITICAL: No AI-generated fields found! Check backend metadata generation.');
            }
            
            // Create mapped risk instance with proper structure
            const mappedRI = {
              ...ri,
              _meta: meta,
              _perField: perField
            };
            
            // Log sample field to verify structure
            if (perField['RiskTitle']) {
              console.log(`   📝 Sample: RiskTitle metadata:`, perField['RiskTitle']);
            }
            
            return mappedRI;
          });

          // Enable debug mode for first render
          window.aiDebugMode = true;
          setTimeout(() => { window.aiDebugMode = false; }, 5000);

          console.log('✅ Extracted risk instances ready for display');
          
          // Comprehensive metadata summary
          const summary = {
            totalRiskInstances: this.extractedRiskInstances.length,
            aiGenerated: 0,
            extracted: 0,
            default: 0,
            computed: 0,
            totalFields: 0
          };
          
          this.extractedRiskInstances.forEach((ri) => {
            const perField = ri._perField || {};
            Object.keys(perField).forEach(fieldName => {
              const fieldInfo = perField[fieldName];
              summary.totalFields++;
              if (fieldInfo?.source === 'AI_GENERATED') summary.aiGenerated++;
              else if (fieldInfo?.source === 'EXTRACTED') summary.extracted++;
              else if (fieldInfo?.source === 'DEFAULT') summary.default++;
              else if (fieldInfo?.source === 'COMPUTED') summary.computed++;
            });
          });
          
          console.log('📊 FINAL METADATA SUMMARY:');
          console.log(`   📋 Total Risk Instances: ${summary.totalRiskInstances}`);
          console.log(`   🤖 AI Generated Fields: ${summary.aiGenerated}`);
          console.log(`   📄 Extracted Fields: ${summary.extracted}`);
          console.log(`   🔧 Default Fields: ${summary.default}`);
          console.log(`   🧮 Computed Fields: ${summary.computed}`);
          console.log(`   📊 Total Fields Tracked: ${summary.totalFields}`);

          // Update progress details with final statistics
          this.progressDetails.processedItems = summary.totalRiskInstances;
          
          // Display data immediately - no artificial delays
          this.currentStep = 'review';
          this.isProcessing = false;
          this.saveProcessingState();

          // Count AI-generated fields for notification
          const aiFieldsCount = summary.aiGenerated;

          this.$notify({
            type: 'success',
            title: 'AI Processing Complete',
            text: `Extracted ${this.extractedRiskInstances.length} risk instance(s) with ${aiFieldsCount} AI-generated fields. Look for 🤖 icons showing AI predictions with confidence scores!`
          });
        } else {
          throw new Error(response.data.message || 'Processing failed');
        }
      } catch (error) {
        console.error('Error processing document:', error);
        this.uploadController = null;

        if (error.name === 'CanceledError' || error.code === 'ERR_CANCELED' || error.message === 'canceled') {
          this.isProcessing = false;
          this.currentStep = 'upload';
          this.processingStatus = 'Processing cancelled by user';
          this.processingProgress = 0;
          this.currentProcessingStep = 0;
          this.clearProcessingState();

          this.$notify({
            type: 'info',
            title: 'Cancelled',
            text: 'AI risk instance processing was cancelled.'
          });
        } else {
          this.isProcessing = false;
          this.currentStep = 'upload';
          this.clearProcessingState();
          
          this.$notify({
            type: 'error',
            title: 'Processing Failed',
            text: error.response?.data?.message || error.message || 'Failed to process document. Please try again.'
          });
        }
      }
    },

    handleStreamEvent(data) {
      console.log('📡 Stream event:', data.type, data);

      switch (data.type) {
        case 'status':
          this.processingStatus = data.message;
          this.processingProgress = data.progress;
          break;

        case 'structure':
          this.processingStatus = `Found ${data.risk_count} risk instance(s) to analyze...`;
          this.processingProgress = data.progress;
          this.initializeRiskInstances(data.risk_count, data.risk_titles);
          break;

        case 'risk_start':
          this.processingStatus = `Analyzing ${data.title}...`;
          this.processingProgress = data.progress;
          this.highlightActiveRisk(data.index);
          break;

        case 'field_generated':
          this.updateRiskInstanceField(
            data.risk_index,
            data.field_name,
            data.value,
            data.confidence,
            data.rationale
          );
          this.processingStatus = `Generated ${data.field_name} for Risk #${data.risk_index + 1}`;
          this.processingProgress = data.progress;
          break;

        case 'risk_complete':
          this.processingStatus = `Completed Risk Instance #${data.index + 1}`;
          this.processingProgress = data.progress;
          this.markRiskComplete(data.index);
          break;

        case 'complete':
          this.processingStatus = 'AI analysis complete!';
          this.processingProgress = 100;
          this.finalizeStreamingProcessing(data.risk_instances);
          break;

        default:
          console.log('Unknown stream event type:', data.type);
      }
    },

    initializeRiskInstances(count, titles) {
      this.extractedRiskInstances = [];
      for (let i = 0; i < count; i++) {
        this.extractedRiskInstances.push({
          RiskTitle: titles[i] || `Risk Instance ${i + 1}`,
          _meta: { per_field: {} },
          _perField: {},
          _streamingStatus: 'pending', // pending, active, completed
          _fieldsGenerated: 0,
          _totalFields: 24 // Based on schema_fields count
        });
      }
      this.currentStep = 'streaming'; // New step for progressive generation
    },

    updateRiskInstanceField(riskIndex, fieldName, value, confidence, rationale) {
      if (riskIndex < this.extractedRiskInstances.length) {
        const riskInstance = this.extractedRiskInstances[riskIndex];
        
        // Update the field value
        this.$set(riskInstance, fieldName, value);
        
        // Update metadata
        const fieldMeta = {
          source: 'AI_GENERATED',
          confidence: confidence,
          rationale: rationale
        };
        
        this.$set(riskInstance._perField, fieldName, fieldMeta);
        this.$set(riskInstance._meta.per_field, fieldName, fieldMeta);
        
        // Update field count
        riskInstance._fieldsGenerated++;
        
        // Animate the field
        this.$nextTick(() => {
          this.animateNewField(riskIndex, fieldName);
        });
      }
    },

    animateNewField(riskIndex, fieldName) {
      // Find the field input/select element
      const fieldSelector = `[data-risk="${riskIndex}"][data-field="${fieldName}"]`;
      const fieldElement = document.querySelector(fieldSelector);
      
      if (fieldElement) {
        // Add animation class
        fieldElement.classList.add('field-just-generated');
        
        // Remove animation class after animation completes
        setTimeout(() => {
          fieldElement.classList.remove('field-just-generated');
        }, 2000);
        
        // Scroll field into view if not visible
        fieldElement.scrollIntoView({
          behavior: 'smooth',
          block: 'nearest'
        });
      }
    },

    highlightActiveRisk(riskIndex) {
      if (riskIndex < this.extractedRiskInstances.length) {
        this.extractedRiskInstances[riskIndex]._streamingStatus = 'active';
      }
    },

    markRiskComplete(riskIndex) {
      if (riskIndex < this.extractedRiskInstances.length) {
        this.extractedRiskInstances[riskIndex]._streamingStatus = 'completed';
      }
    },

    finalizeStreamingProcessing(riskInstances) {
      // Ensure all instances are marked as completed
      this.extractedRiskInstances.forEach(instance => {
        instance._streamingStatus = 'completed';
      });
      
      setTimeout(() => {
        this.currentStep = 'review';
        this.isProcessing = false;
        this.saveProcessingState();
        
        this.$notify({
          type: 'success',
          title: 'AI Analysis Complete',
          text: `Successfully analyzed ${riskInstances.length} risk instance(s) with progressive field generation!`
        });
      }, 1000);
    },

    cancelProcessing() {
      if (this.uploadController) {
        try {
          this.uploadController.abort();
        } catch (e) {
          console.warn('Error aborting upload controller:', e);
        }
        this.uploadController = null;
      }

      this.isProcessing = false;
      this.currentStep = 'upload';
      this.processingStatus = 'Processing cancelled by user';
      this.processingProgress = 0;
      this.currentProcessingStep = 0;
      this.currentProcessingPhase = 'upload';
      this.clearProcessingState();

      this.$notify({
        type: 'info',
        title: 'Cancelled',
        text: 'AI risk instance processing was cancelled.'
      });
    },

    isAIGenerated(riskInstance, fieldName) {
      // Robust check for AI-generated fields
      // Backend uses _meta.per_field structure
      const perField = (riskInstance._meta && riskInstance._meta.per_field) || riskInstance._perField || {};
      const fieldInfo = perField[fieldName];
      
      if (!fieldInfo) {
        if (window.aiDebugMode) {
          console.warn(`⚠️  No metadata for field '${fieldName}' - check backend response`);
        }
        return false;
      }
      
      const isAI = fieldInfo.source === 'AI_GENERATED';
      
      // Debug log for every field to ensure we catch issues
      if (window.aiDebugMode || !window.aiFieldsLogged) {
        console.log(`🔍 AI Check '${fieldName}':`, {
          source: fieldInfo.source,
          isAI: isAI,
          confidence: fieldInfo.confidence,
          hasValue: !!riskInstance[fieldName]
        });
      }
      
      return isAI;
    },

    getAITooltip(riskInstance, fieldName) {
      // Backend uses _meta.per_field structure
      const perField = (riskInstance._meta && riskInstance._meta.per_field) || riskInstance._perField || {};
      const fieldInfo = perField[fieldName];
      if (fieldInfo && fieldInfo.source === 'AI_GENERATED') {
        const confidence = Math.round((fieldInfo.confidence || 0.75) * 100);
        const rationale = fieldInfo.rationale || 'AI analyzed the document and predicted this value';
        
        // Create rich tooltip
        let tooltip = `🤖 AI GENERATED FIELD\n`;
        tooltip += `━━━━━━━━━━━━━━━━━━━━\n\n`;
        tooltip += `✓ Confidence Score: ${confidence}%\n\n`;
        tooltip += `📝 Reasoning:\n${rationale}\n\n`;
        tooltip += `━━━━━━━━━━━━━━━━━━━━\n`;
        tooltip += `💡 Tip: You can edit this value if needed before saving.`;
        
        return tooltip;
      }
      return '';
    },

    getConfidencePercent(riskInstance, fieldName) {
      // Backend uses _meta.per_field structure
      const perField = (riskInstance._meta && riskInstance._meta.per_field) || riskInstance._perField || {};
      const fieldInfo = perField[fieldName];
      if (fieldInfo && fieldInfo.source === 'AI_GENERATED') {
        const confidence = fieldInfo.confidence || 0.75;
        return Math.round(confidence * 100);
      }
      return 75; // Default if metadata missing but field is AI-generated
    },

    updateProgress(percent, status) {
      this.processingProgress = percent;
      this.processingStatus = status;
    },

    updateProgressWithPhase(percent, phase, status) {
      this.processingProgress = percent;
      this.currentProcessingPhase = phase;
      this.processingStatus = status;
    },

    estimateProcessingDetails() {
      if (!this.selectedFile) return;
      
      const fileSizeKB = this.selectedFile.size / 1024;
      
      // Estimate fields based on file size (rough calculation for risk instances)
      if (fileSizeKB < 50) {
        this.progressDetails.estimatedFields = 12;
        this.progressDetails.estimatedTime = 20000; // 20 seconds
      } else if (fileSizeKB < 200) {
        this.progressDetails.estimatedFields = 18;
        this.progressDetails.estimatedTime = 35000; // 35 seconds
      } else if (fileSizeKB < 500) {
        this.progressDetails.estimatedFields = 25;
        this.progressDetails.estimatedTime = 50000; // 50 seconds
      } else {
        this.progressDetails.estimatedFields = 35;
        this.progressDetails.estimatedTime = 75000; // 75 seconds
      }
    },

    formatFileSize(bytes) {
      if (bytes === 0) return '0 Bytes';
      const k = 1024;
      const sizes = ['Bytes', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },

    formatTime(milliseconds) {
      const seconds = Math.ceil(milliseconds / 1000);
      if (seconds < 60) return `${seconds}s`;
      const minutes = Math.floor(seconds / 60);
      const remainingSeconds = seconds % 60;
      return `${minutes}m ${remainingSeconds}s`;
    },

    delay(ms) {
      return new Promise(resolve => setTimeout(resolve, ms));
    },

    removeRiskInstance(index) {
      if (confirm('Are you sure you want to remove this risk instance?')) {
        this.extractedRiskInstances.splice(index, 1);
      }
    },

    async saveAllRiskInstances() {
      const invalidRiskInstances = this.extractedRiskInstances.filter(ri => !ri.RiskTitle);
      if (invalidRiskInstances.length > 0) {
        this.$notify({
          type: 'error',
          title: 'Validation Error',
          text: 'All risk instances must have a title.'
        });
        return;
      }

      this.isSaving = true;
      this.saveProcessingState();

      try {
        const cleanRiskInstances = this.extractedRiskInstances.map(ri => {
          // eslint-disable-next-line no-unused-vars
          const { _meta, _perField, ...cleanRI } = ri;
          return cleanRI;
        });

        const response = await axios.post(
          API_ENDPOINTS.RISK_INSTANCE_AI_SAVE,
          {
            risk_instances: cleanRiskInstances,
            user_id: localStorage.getItem('user_id') || '1'
          },
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
          }
        );

        if (response.data.status === 'success') {
          this.savedCount = response.data.saved?.length || this.extractedRiskInstances.length;
          this.currentStep = 'success';
          this.clearProcessingState();
          
          this.$notify({
            type: 'success',
            title: 'Success',
            text: `Successfully saved ${this.savedCount} risk instance(s) to the database.`
          });
        } else {
          throw new Error(response.data.message || 'Failed to save risk instances');
        }
      } catch (error) {
        console.error('Error saving risk instances:', error);
        this.$notify({
          type: 'error',
          title: 'Save Failed',
          text: error.response?.data?.message || error.message || 'Failed to save risk instances. Please try again.'
        });
      } finally {
        this.isSaving = false;
      }
    },

    cancelReview() {
      if (confirm('Are you sure? All extracted data will be lost.')) {
        this.resetForm();
      }
    },

    resetForm() {
      this.currentStep = 'upload';
      this.selectedFile = null;
      this.extractedRiskInstances = [];
      this.processingProgress = 0;
      this.currentProcessingStep = 0;
      this.currentProcessingPhase = 'upload';
      this.progressDetails = { estimatedFields: 0, estimatedTime: 0, processedItems: 0 };
      this.savedCount = 0;
      this.clearProcessingState();
      if (this.$refs.fileInput) {
        this.$refs.fileInput.value = '';
      }
    },

    viewRiskInstances() {
      this.$router.push('/risk/riskinstances-list');
    },

    checkSidebarState() {
      // Check if sidebar exists and is collapsed
      const sidebar = document.querySelector('.sidebar');
      if (sidebar) {
        this.isSidebarCollapsed = sidebar.classList.contains('collapsed');
        console.log('Sidebar state:', this.isSidebarCollapsed ? 'collapsed' : 'expanded');
      } else {
        console.log('Sidebar not found');
      }
    },

    getTotalAIFields() {
      let total = 0;
      this.extractedRiskInstances.forEach(riskInstance => {
        const perField = riskInstance._perField || {};
        const aiFields = Object.keys(perField).filter(k => perField[k]?.source === 'AI_GENERATED');
        total += aiFields.length;
      });
      return total;
    },

    getAverageConfidence() {
      let sum = 0;
      let count = 0;
      this.extractedRiskInstances.forEach(riskInstance => {
        const perField = riskInstance._perField || {};
        Object.keys(perField).forEach(fieldName => {
          const fieldInfo = perField[fieldName];
          if (fieldInfo?.source === 'AI_GENERATED' && fieldInfo.confidence) {
            sum += fieldInfo.confidence;
            count++;
          }
        });
      });
      return count > 0 ? Math.round((sum / count) * 100) : 0;
    },

    getFieldCoverage() {
      if (this.extractedRiskInstances.length === 0) return 0;
      
      const totalPossibleFields = ['RiskTitle', 'Category', 'Criticality', 'RiskPriority', 'Origin', 
        'RiskOwner', 'RiskDescription', 'PossibleDamage', 'BusinessImpact', 'RiskLikelihood', 
        'RiskImpact', 'RiskExposureRating', 'Appetite', 'RiskMultiplierX', 'RiskMultiplierY', 
        'RiskType', 'RiskResponseType', 'RiskResponseDescription', 'RiskStatus', 'MitigationStatus', 'Reviewer'];
      
      let totalFields = 0;
      let filledFields = 0;
      
      this.extractedRiskInstances.forEach(riskInstance => {
        totalPossibleFields.forEach(fieldName => {
          totalFields++;
          if (riskInstance[fieldName] && riskInstance[fieldName] !== '' && riskInstance[fieldName] !== null) {
            filledFields++;
          }
        });
      });
      
      return totalFields > 0 ? Math.round((filledFields / totalFields) * 100) : 0;
    },

    getFieldProgressText() {
      // Extract current field name from processing status if it contains "Generating"
      if (this.processingStatus && this.processingStatus.includes('Generating')) {
        const match = this.processingStatus.match(/Generating (.+?)\.{3}$/);
        if (match) {
          const currentField = match[1];
          // Calculate approximate progress (19 total fields in the AI generation phase)
          const baseProgress = 45;
          const currentProgress = this.processingProgress;
          const aiProgressRange = 40; // 45% to 85%
          const fieldIndex = Math.floor(((currentProgress - baseProgress) / aiProgressRange) * 19);
          
          return `${Math.min(fieldIndex + 1, 19)}/19 - ${currentField}`;
        }
      }
      
      return this.progressDetails.estimatedFields || '19';
    }
  },
  mounted() {
    // Check sidebar state on mount
    this.checkSidebarState();
    
    // Listen for sidebar toggle events
    document.addEventListener('click', (event) => {
      if (event.target.closest('.toggle') || event.target.closest('.expand-button')) {
        // Wait for the sidebar animation to complete
        setTimeout(() => {
          this.checkSidebarState();
        }, 300);
      }
    });

    // Load processing state on component mount
    this.loadProcessingState();
    this.resumeProcessingIfNeeded();
  }
};
</script>

<style src="@/assets/css/main.css"></style>
<style src="./risk_ai_instance.css" scoped></style>
<style src="./streaming-animations.css" scoped></style>

<style scoped>
.ai-progress-details {
  margin: 20px 0;
  background: #f8f9fa;
  border-radius: 8px;
  padding: 15px;
}

.progress-stats {
  display: flex;
  gap: 20px;
  margin-bottom: 15px;
  flex-wrap: wrap;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stat-label {
  font-weight: 500;
  color: #6c757d;
}

.stat-value {
  font-weight: 600;
  color: #495057;
}

.processing-phases {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.phase {
  padding: 8px 12px;
  border-radius: 20px;
  background: #e9ecef;
  color: #6c757d;
  font-size: 0.875rem;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.3s ease;
}

.phase.active {
  background: #007bff;
  color: white;
  transform: scale(1.05);
}

.phase.completed {
  background: #28a745;
  color: white;
}

.phase i {
  font-size: 0.8rem;
}
</style>

