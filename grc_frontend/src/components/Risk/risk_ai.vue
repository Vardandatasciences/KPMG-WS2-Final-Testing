<template>
  <div class="risk-ai-container" :class="{ 'sidebar-collapsed': isSidebarCollapsed }">
    <!-- Header -->
    <div class="page-header">
      <div class="header-content">
        <h1><i class="fas fa-robot"></i> AI-Powered Risk Register Document Import</h1>
        <p class="subtitle">Upload risk register documents and let AI extract and predict risk information automatically</p>
      </div>
    </div>

    <!-- Upload Section -->
    <div v-if="currentStep === 'upload'" class="upload-section">
      <div class="upload-card">
        <div class="upload-card-header">
          <h2>Upload Risk Register Document</h2>
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
        <h2>AI Processing Risk Document...</h2>
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
              <span class="stat-label">Estimated Fields:</span>
              <span class="stat-value">{{ progressDetails.estimatedFields }}</span>
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
        <h2><i class="fas fa-edit"></i> Review Extracted Risks</h2>
        <p>{{ extractedRisks.length }} risk(s) found. Review and edit before saving.</p>
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
        <div v-for="(risk, index) in extractedRisks" :key="index" class="risk-card">
          <div class="risk-card-header">
            <h3>Risk #{{ index + 1 }}</h3>
            <div class="risk-card-actions">
              <button 
                @click="generateAIAnalysis(risk, index)" 
                :disabled="isGeneratingAnalysis"
                class="btn-ai-analysis"
                title="Generate enhanced AI analysis and justifications"
              >
                <i class="fas fa-brain"></i>
                {{ isGeneratingAnalysis ? 'Analyzing...' : 'Generate Analysis' }}
              </button>
              <button @click="removeRisk(index)" class="btn-remove">
                <i class="fas fa-trash"></i>
              </button>
            </div>
          </div>

          <div class="risk-form">
            <div class="form-row">
              <div class="form-group">
                <label>
                  Risk Title <span class="required">*</span>
                  <span v-if="isAIGenerated(risk, 'RiskTitle')" class="ai-indicator" :title="getEnhancedAITooltip(risk, 'RiskTitle', index)">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(risk, 'RiskTitle') }}%
                  </span>
                </label>
                <input 
                  v-model="risk.RiskTitle" 
                  type="text" 
                  placeholder="Enter risk title"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(risk, 'RiskTitle') }]"
                />
              </div>
              <div class="form-group">
                <label>
                  Category
                  <span v-if="isAIGenerated(risk, 'Category')" class="ai-indicator" :title="getEnhancedAITooltip(risk, 'Category', index)">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(risk, 'Category') }}%
                  </span>
                </label>
                <input 
                  v-model="risk.Category" 
                  type="text" 
                  placeholder="e.g., Operational, Financial"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(risk, 'Category') }]"
                />
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label>
                  Criticality
                  <span v-if="isAIGenerated(risk, 'Criticality')" class="ai-indicator" :title="getEnhancedAITooltip(risk, 'Criticality', index)">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(risk, 'Criticality') }}%
                  </span>
                </label>
                <select v-model="risk.Criticality" :class="['form-control', { 'ai-generated-field': isAIGenerated(risk, 'Criticality') }]">
                  <option value="">Select Criticality</option>
                  <option value="Low">Low</option>
                  <option value="Medium">Medium</option>
                  <option value="High">High</option>
                  <option value="Critical">Critical</option>
                </select>
              </div>
              <div class="form-group">
                <label>
                  Risk Type
                  <span v-if="isAIGenerated(risk, 'RiskType')" class="ai-indicator" :title="getEnhancedAITooltip(risk, 'RiskType', index)">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(risk, 'RiskType') }}%
                  </span>
                </label>
                <select v-model="risk.RiskType" :class="['form-control', { 'ai-generated-field': isAIGenerated(risk, 'RiskType') }]">
                  <option value="">Select Risk Type</option>
                  <option value="Operational">Operational</option>
                  <option value="Financial">Financial</option>
                  <option value="Strategic">Strategic</option>
                  <option value="Compliance">Compliance</option>
                  <option value="Reputational">Reputational</option>
                </select>
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label>
                  Business Impact
                  <span v-if="isAIGenerated(risk, 'BusinessImpact')" class="ai-indicator" :title="getEnhancedAITooltip(risk, 'BusinessImpact', index)">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(risk, 'BusinessImpact') }}%
                  </span>
                </label>
                <textarea 
                  v-model="risk.BusinessImpact" 
                  type="text" 
                  placeholder="Describe potential business impact"
                  rows="2"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(risk, 'BusinessImpact') }]"
                ></textarea>
              </div>
              <div class="form-group">
                <label>
                  Possible Damage
                  <span v-if="isAIGenerated(risk, 'PossibleDamage')" class="ai-indicator" :title="getEnhancedAITooltip(risk, 'PossibleDamage', index)">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(risk, 'PossibleDamage') }}%
                  </span>
                </label>
                <textarea 
                  v-model="risk.PossibleDamage" 
                  type="text" 
                  placeholder="Describe possible damage"
                  rows="2"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(risk, 'PossibleDamage') }]"
                ></textarea>
              </div>
            </div>

            <div class="form-row">
              <div class="form-group full-width">
                <label>
                  Risk Description
                  <span v-if="isAIGenerated(risk, 'RiskDescription')" class="ai-indicator" :title="getEnhancedAITooltip(risk, 'RiskDescription', index)">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(risk, 'RiskDescription') }}%
                  </span>
                </label>
                <textarea 
                  v-model="risk.RiskDescription" 
                  placeholder="Detailed description of the risk"
                  rows="3"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(risk, 'RiskDescription') }]"
                ></textarea>
              </div>
            </div>

            <div class="form-row">
              <div class="form-group full-width">
                <label>
                  Risk Mitigation
                  <span v-if="isAIGenerated(risk, 'RiskMitigation')" class="ai-indicator" :title="getEnhancedAITooltip(risk, 'RiskMitigation', index)">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(risk, 'RiskMitigation') }}%
                  </span>
                </label>
                <textarea 
                  v-model="risk.RiskMitigation" 
                  placeholder="Describe mitigation strategies"
                  rows="2"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(risk, 'RiskMitigation') }]"
                ></textarea>
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label>
                  Risk Likelihood (1-10)
                  <span v-if="isAIGenerated(risk, 'RiskLikelihood')" class="ai-indicator" :title="getEnhancedAITooltip(risk, 'RiskLikelihood', index)">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(risk, 'RiskLikelihood') }}%
                  </span>
                </label>
                <input 
                  v-model.number="risk.RiskLikelihood" 
                  type="number" 
                  min="1" 
                  max="10"
                  placeholder="1-10"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(risk, 'RiskLikelihood') }]"
                />
              </div>
              <div class="form-group">
                <label>
                  Risk Impact (1-10)
                  <span v-if="isAIGenerated(risk, 'RiskImpact')" class="ai-indicator" :title="getEnhancedAITooltip(risk, 'RiskImpact', index)">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(risk, 'RiskImpact') }}%
                  </span>
                </label>
                <input 
                  v-model.number="risk.RiskImpact" 
                  type="number" 
                  min="1" 
                  max="10"
                  placeholder="1-10"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(risk, 'RiskImpact') }]"
                />
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label>
                  Risk Exposure Rating (0-100)
                  <span v-if="isAIGenerated(risk, 'RiskExposureRating')" class="ai-indicator" :title="getEnhancedAITooltip(risk, 'RiskExposureRating', index)">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(risk, 'RiskExposureRating') }}%
                  </span>
                </label>
                <input 
                  v-model.number="risk.RiskExposureRating" 
                  type="number" 
                  step="0.01"
                  min="0" 
                  max="100"
                  placeholder="0-100"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(risk, 'RiskExposureRating') }]"
                  readonly
                />
              </div>
              <div class="form-group">
                <label>
                  Risk Priority
                  <span v-if="isAIGenerated(risk, 'RiskPriority')" class="ai-indicator" :title="getEnhancedAITooltip(risk, 'RiskPriority', index)">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(risk, 'RiskPriority') }}%
                  </span>
                </label>
                <select v-model="risk.RiskPriority" :class="['form-control', { 'ai-generated-field': isAIGenerated(risk, 'RiskPriority') }]">
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
                  Risk Multiplier X
                  <span v-if="isAIGenerated(risk, 'RiskMultiplierX')" class="ai-indicator" :title="getEnhancedAITooltip(risk, 'RiskMultiplierX', index)">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(risk, 'RiskMultiplierX') }}%
                  </span>
                </label>
                <input 
                  v-model.number="risk.RiskMultiplierX" 
                  type="number" 
                  step="0.1"
                  min="0.1" 
                  max="2.0"
                  placeholder="0.1-2.0"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(risk, 'RiskMultiplierX') }]"
                />
              </div>
              <div class="form-group">
                <label>
                  Risk Multiplier Y
                  <span v-if="isAIGenerated(risk, 'RiskMultiplierY')" class="ai-indicator" :title="getEnhancedAITooltip(risk, 'RiskMultiplierY', index)">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(risk, 'RiskMultiplierY') }}%
                  </span>
                </label>
                <input 
                  v-model.number="risk.RiskMultiplierY" 
                  type="number" 
                  step="0.1"
                  min="0.1" 
                  max="2.0"
                  placeholder="0.1-2.0"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(risk, 'RiskMultiplierY') }]"
                />
              </div>
            </div>

            <div class="form-row">
              <div class="form-group full-width">
                <label>
                  Created Date
                  <span v-if="isAIGenerated(risk, 'CreatedAt')" class="ai-indicator" :title="getEnhancedAITooltip(risk, 'CreatedAt', index)">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(risk, 'CreatedAt') }}%
                  </span>
                </label>
                <input 
                  v-model="risk.CreatedAt" 
                  type="date"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(risk, 'CreatedAt') }]"
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
        <button @click="saveAllRisks" :disabled="isSaving" class="btn btn-submit">
          {{ isSaving ? 'Saving...' : 'Save All Risks' }}
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
        <p>{{ savedCount }} risk(s) have been successfully saved to the database.</p>
        <div class="action-buttons">
          <button @click="resetForm" class="btn-cancel">
            Upload Another
          </button>
          <button @click="viewRisks" class="btn btn-submit btn-primary">
            View All Risks
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { API_ENDPOINTS } from '../../config/api.js';
import apiService from '@/services/apiService.js';

const axios = {
  post: (url, data = {}, config = {}) =>
    apiService.post(url, data, config).then((res) => ({ data: res, status: 200 }))
};

export default {
  name: 'RiskRegisterAIDocumentUpload',
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
      extractedRisks: [],
      savedCount: 0,
      isSidebarCollapsed: false,
      uploadController: null,
      aiProgressTimer: null,
      progressDetails: {
        estimatedFields: 0,
        estimatedTime: 0,
        processedItems: 0
      },
      // AI Justifications for enhanced tooltips (similar to incident_ai_import.vue)
      aiJustifications: {},
      isGeneratingAnalysis: false
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
        extractedRisks: this.extractedRisks,
        progressDetails: this.progressDetails,
        selectedFile: this.selectedFile ? { name: this.selectedFile.name, size: this.selectedFile.size } : null,
        timestamp: Date.now()
      };
      try {
        sessionStorage.setItem('risk_register_ai_processing_state', JSON.stringify(state));
        console.log('💾 Risk Register AI processing state saved:', state);
      } catch (error) {
        console.error('❌ Failed to save risk register AI processing state:', error);
      }
    },

    loadProcessingState() {
      try {
        const savedState = sessionStorage.getItem('risk_register_ai_processing_state');
        if (!savedState) {
          console.log('❌ No saved risk register AI state found');
          return false;
        }

        const state = JSON.parse(savedState);

        // Check if state is not too old (24 hours max)
        const maxAge = 24 * 60 * 60 * 1000; // 24 hours in milliseconds
        if (Date.now() - state.timestamp > maxAge) {
          console.log('❌ Saved risk register AI state is too old, clearing');
          sessionStorage.removeItem('risk_register_ai_processing_state');
          return false;
        }

        // Restore state
        this.currentStep = state.currentStep || 'upload';
        this.isProcessing = state.isProcessing || false;
        this.processingStatus = state.processingStatus || 'Initializing...';
        this.processingProgress = state.processingProgress || 0;
        this.currentProcessingStep = state.currentProcessingStep || 0;
        this.currentProcessingPhase = state.currentProcessingPhase || 'upload';
        this.extractedRisks = state.extractedRisks || [];
        this.progressDetails = state.progressDetails || { estimatedFields: 0, estimatedTime: 0, processedItems: 0 };
        this.selectedFile = null; // Don't restore file object, just clear it

        console.log('✅ Risk Register AI processing state restored:', state);
        return true;
      } catch (error) {
        console.error('❌ Failed to load risk register AI processing state:', error);
        sessionStorage.removeItem('risk_register_ai_processing_state');
        return false;
      }
    },

    clearProcessingState() {
      try {
        sessionStorage.removeItem('risk_register_ai_processing_state');
        this.aiJustifications = {};
        console.log('🗑️ Risk Register AI processing state cleared');
      } catch (error) {
        console.error('❌ Failed to clear risk register AI processing state:', error);
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
        console.log('🔄 Resuming risk register AI processing from step:', this.currentProcessingStep);
        // Continue from where it left off - progress will update naturally
        this.$notify({
          type: 'info',
          title: 'Resuming',
          text: `Resuming risk register processing from ${this.processingProgress}%`
        });
      } else if (this.currentStep === 'review' && this.extractedRisks.length > 0) {
        console.log('🔄 Risk Register AI review data restored');
        this.$notify({
          type: 'info',
          title: 'Data Restored',
          text: `Restored ${this.extractedRisks.length} risk(s) for review`
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
      
      // Estimate fields and time based on file size
      this.estimateProcessingDetails();
      this.saveProcessingState();

      const formData = new FormData();
      formData.append('file', this.selectedFile);

      try {
        // Update progress for upload start
        this.updateProgressWithPhase(10, 'upload', 'Uploading document...');
        this.currentProcessingStep = 1;
        this.saveProcessingState();

        // Create AbortController for this upload so we can cancel it
        const controller = new AbortController();
        this.uploadController = controller;

        // Track upload progress in real-time
        const response = await axios.post(
          API_ENDPOINTS.RISK_AI_UPLOAD,
          formData,
          {
            headers: {
              'Content-Type': 'multipart/form-data'
            },
            timeout: 300000, // 5 minutes
            signal: controller.signal,
            onUploadProgress: (progressEvent) => {
              if (progressEvent.total) {
                const uploadPercent = Math.round((progressEvent.loaded * 30) / progressEvent.total); // 0-30% for upload
                this.updateProgressWithPhase(10 + uploadPercent, 'upload', 'Uploading document...');
                // When upload is essentially done, start a smooth AI phase progress
                if (uploadPercent >= 30 && !this.aiProgressTimer) {
                  this.startAIPhaseProgress();
                }
                this.saveProcessingState();
              }
            }
          }
        );

        // Ensure AI phase is active while backend is processing
        this.updateProgressWithPhase(Math.max(this.processingProgress, 40), 'ai', 'AI analyzing and generating risk fields...');

        // Backend processing is complete at this point
        this.stopAIPhaseProgress();
        this.updateProgressWithPhase(100, 'finalize', 'Processing complete!');
        this.currentProcessingStep = 4;
        this.saveProcessingState();
        this.uploadController = null;

        if (response.data.status === 'success') {
          const risks = response.data.risks || [];
          
          console.log('🔍 DEBUG: Raw risks from backend:', JSON.stringify(risks[0]?._meta, null, 2));
          
          this.extractedRisks = risks.map((risk, idx) => {
            const meta = risk._meta || {};
            const perField = meta.per_field || {};
            
            const aiFieldsList = Object.keys(perField).filter(k => perField[k]?.source === 'AI_GENERATED');
            const extractedFieldsList = Object.keys(perField).filter(k => perField[k]?.source === 'EXTRACTED');
            
            console.log(`📋 Risk ${idx + 1} Metadata Summary:`);
            console.log(`   ✓ Total fields with metadata: ${Object.keys(perField).length}`);
            console.log(`   🤖 AI Generated: ${aiFieldsList.length} fields`);
            console.log(`   📄 Extracted: ${extractedFieldsList.length} fields`);
            console.log(`   🎯 Sample AI fields:`, aiFieldsList.slice(0, 5));
            
            if (aiFieldsList.length === 0) {
              console.error('❌ CRITICAL: No AI-generated fields found! Check backend metadata generation.');
            }
            
            // Create mapped risk with proper structure
            const mappedRisk = {
              ...risk,
              _meta: meta,
              _perField: perField
            };
            
            // Log sample field to verify structure
            if (perField['RiskTitle']) {
              console.log(`   📝 Sample: RiskTitle metadata:`, perField['RiskTitle']);
            }
            
            return mappedRisk;
          });

          // Enable debug mode for first render
          window.aiDebugMode = true;
          setTimeout(() => { window.aiDebugMode = false; }, 5000);

          console.log('✅ Extracted risks ready for display');
          
          // Comprehensive metadata summary
          const summary = {
            totalRisks: this.extractedRisks.length,
            aiGenerated: 0,
            extracted: 0,
            default: 0,
            computed: 0,
            totalFields: 0
          };
          
          this.extractedRisks.forEach((risk) => {
            const perField = risk._perField || {};
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
          console.log(`   📋 Total Risks: ${summary.totalRisks}`);
          console.log(`   🤖 AI Generated Fields: ${summary.aiGenerated}`);
          console.log(`   📄 Extracted Fields: ${summary.extracted}`);
          console.log(`   🔧 Default Fields: ${summary.default}`);
          console.log(`   🧮 Computed Fields: ${summary.computed}`);
          console.log(`   📊 Total Fields Tracked: ${summary.totalFields}`);

          // Update progress details with final statistics
          this.progressDetails.processedItems = summary.totalRisks;
          
          // Display data immediately - no artificial delays
          this.currentStep = 'review';
          this.isProcessing = false;
          this.saveProcessingState();

          // Count AI-generated fields for notification
          const aiFieldsCount = summary.aiGenerated;

          this.$notify({
            type: 'success',
            title: 'AI Processing Complete',
            text: `Extracted ${this.extractedRisks.length} risk(s) with ${aiFieldsCount} AI-generated fields. Look for 🤖 icons showing AI predictions with confidence scores!`
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
            text: 'AI risk register processing was cancelled.'
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
        text: 'AI risk register processing was cancelled.'
      });
    },

    isAIGenerated(risk, fieldName) {
      // Robust check for AI-generated fields
      // Backend uses _meta.per_field structure
      const perField = (risk._meta && risk._meta.per_field) || risk._perField || {};
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
          hasValue: !!risk[fieldName]
        });
      }
      
      return isAI;
    },

    getAITooltip(risk, fieldName) {
      // Backend uses _meta.per_field structure
      const perField = (risk._meta && risk._meta.per_field) || risk._perField || {};
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

    getConfidencePercent(risk, fieldName) {
      // Backend uses _meta.per_field structure
      const perField = (risk._meta && risk._meta.per_field) || risk._perField || {};
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

    startAIPhaseProgress() {
      // Smoothly increase progress during AI processing, up to 90%
      if (this.aiProgressTimer) return;
      this.aiProgressTimer = setInterval(() => {
        if (!this.isProcessing) {
          this.stopAIPhaseProgress();
          return;
        }
        if (this.processingProgress < 90) {
          this.processingProgress += 1;
        } else {
          this.stopAIPhaseProgress();
        }
      }, 1000);
    },

    stopAIPhaseProgress() {
      if (this.aiProgressTimer) {
        clearInterval(this.aiProgressTimer);
        this.aiProgressTimer = null;
      }
    },

    estimateProcessingDetails() {
      if (!this.selectedFile) return;
      
      const fileSizeKB = this.selectedFile.size / 1024;
      
      // Estimate fields based on file size (rough calculation)
      if (fileSizeKB < 50) {
        this.progressDetails.estimatedFields = 8;
        this.progressDetails.estimatedTime = 15000; // 15 seconds
      } else if (fileSizeKB < 200) {
        this.progressDetails.estimatedFields = 12;
        this.progressDetails.estimatedTime = 25000; // 25 seconds
      } else if (fileSizeKB < 500) {
        this.progressDetails.estimatedFields = 18;
        this.progressDetails.estimatedTime = 40000; // 40 seconds
      } else {
        this.progressDetails.estimatedFields = 25;
        this.progressDetails.estimatedTime = 60000; // 60 seconds
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

    removeRisk(index) {
      if (confirm('Are you sure you want to remove this risk?')) {
        this.extractedRisks.splice(index, 1);
      }
    },

    async saveAllRisks() {
      const invalidRisks = this.extractedRisks.filter(risk => !risk.RiskTitle);
      if (invalidRisks.length > 0) {
        this.$notify({
          type: 'error',
          title: 'Validation Error',
          text: 'All risks must have a title.'
        });
        return;
      }

      this.isSaving = true;
      this.saveProcessingState();

      try {
        const cleanRisks = this.extractedRisks.map(risk => {
          // eslint-disable-next-line no-unused-vars
          const { _meta, _perField, ...cleanRisk } = risk;
          return cleanRisk;
        });

        const response = await axios.post(
          API_ENDPOINTS.RISK_AI_SAVE || `${API_ENDPOINTS.RISK_AI_UPLOAD.replace('upload', 'save')}`,
          {
            risks: cleanRisks,
            
          }
        );

        if (response.data.status === 'success') {
          this.savedCount = response.data.saved?.length || this.extractedRisks.length;
          this.currentStep = 'success';
          this.clearProcessingState();
          
          this.$notify({
            type: 'success',
            title: 'Success',
            text: `Successfully saved ${this.savedCount} risk(s) to the database.`
          });
        } else {
          throw new Error(response.data.message || 'Failed to save risks');
        }
      } catch (error) {
        console.error('Error saving risks:', error);
        this.$notify({
          type: 'error',
          title: 'Save Failed',
          text: error.response?.data?.message || error.message || 'Failed to save risks. Please try again.'
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
      this.extractedRisks = [];
      this.processingProgress = 0;
      this.currentProcessingStep = 0;
      this.currentProcessingPhase = 'upload';
      this.progressDetails = { estimatedFields: 0, estimatedTime: 0, processedItems: 0 };
      this.savedCount = 0;
      this.stopAIPhaseProgress();
      this.clearProcessingState();
      this.aiJustifications = {};
      if (this.$refs.fileInput) {
        this.$refs.fileInput.value = '';
      }
    },

    viewRisks() {
      this.$router.push('/risk/risk-list');
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
      this.extractedRisks.forEach(risk => {
        const perField = risk._perField || {};
        const aiFields = Object.keys(perField).filter(k => perField[k]?.source === 'AI_GENERATED');
        total += aiFields.length;
      });
      return total;
    },

    getAverageConfidence() {
      let sum = 0;
      let count = 0;
      this.extractedRisks.forEach(risk => {
        const perField = risk._perField || {};
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
      if (this.extractedRisks.length === 0) return 0;
      
      const totalPossibleFields = ['RiskTitle', 'Category', 'Criticality', 'RiskType', 'BusinessImpact', 
        'PossibleDamage', 'RiskDescription', 'RiskMitigation', 'RiskLikelihood', 'RiskImpact', 
        'RiskExposureRating', 'RiskPriority', 'RiskMultiplierX', 'RiskMultiplierY', 'CreatedAt'];
      
      let totalFields = 0;
      let filledFields = 0;
      
      this.extractedRisks.forEach(risk => {
        totalPossibleFields.forEach(fieldName => {
          totalFields++;
          if (risk[fieldName] && risk[fieldName] !== '' && risk[fieldName] !== null) {
            filledFields++;
          }
        });
      });
      
      return totalFields > 0 ? Math.round((filledFields / totalFields) * 100) : 0;
    },

    // Generate AI analysis for enhanced tooltips
    async generateAIAnalysis(risk, riskIndex) {
      if (!risk.RiskTitle || !risk.RiskDescription) {
        this.$notify({
          type: 'error',
          title: 'Missing Information',
          text: 'Please ensure risk has both title and description before generating analysis.'
        });
        return;
      }

      if (risk.RiskTitle.trim().length < 3) {
        this.$notify({
          type: 'error',
          title: 'Invalid Title',
          text: 'Risk title must be at least 3 characters long.'
        });
        return;
      }

      this.isGeneratingAnalysis = true;

      try {
        const response = await axios.post(
          API_ENDPOINTS.RISK_GENERATE_ANALYSIS || `${API_ENDPOINTS.RISK_AI_UPLOAD.replace('upload', 'analyze')}`,
          {
            title: risk.RiskTitle,
            description: risk.RiskDescription
          },
          {
            headers: {
              'Content-Type': 'application/json'
            }
          }
        );

        if (response.data && response.data.success) {
          const analysis = response.data.analysis;
          
          console.log('🧠 AI Risk Analysis received:', analysis);

          // Create unique key for this risk
          const riskKey = `risk_${riskIndex}`;
          
          // Initialize justifications for this risk
          if (!this.aiJustifications[riskKey]) {
            this.$set(this.aiJustifications, riskKey, {});
          }

          // Map analysis to form fields and set justifications
          if (analysis.criticality) {
            risk.Criticality = analysis.criticality;
          }

          this.$set(this.aiJustifications[riskKey], 'criticality', 
            analysis.criticalityJustification ||
            'Criticality determined by potential business impact, system dependencies, customer exposure, and regulatory implications. Follows enterprise risk assessment guidelines.');

          if (analysis.riskLikelihood) {
            risk.RiskLikelihood = parseInt(analysis.riskLikelihood);
          }

          this.$set(this.aiJustifications[riskKey], 'riskLikelihood',
            analysis.riskLikelihoodJustification ||
            'Likelihood assessment based on historical data, current threat landscape, control effectiveness, and environmental factors. Rating follows industry risk assessment standards.');

          if (analysis.riskImpact) {
            risk.RiskImpact = parseInt(analysis.riskImpact);
          }

          this.$set(this.aiJustifications[riskKey], 'riskImpact',
            analysis.riskImpactJustification ||
            'Impact assessment considers financial, operational, reputational, and regulatory consequences. Score reflects potential severity based on business criticality.');

          if (analysis.possibleDamage) {
            risk.PossibleDamage = Array.isArray(analysis.possibleDamage) 
              ? analysis.possibleDamage.join(', ') 
              : analysis.possibleDamage;
          }

          this.$set(this.aiJustifications[riskKey], 'possibleDamage',
            analysis.possibleDamageJustification ||
            'Damage assessment considers operational disruption, financial impact, customer effect, regulatory exposure, and reputational risks. Severity based on risk characteristics.');

          if (analysis.riskMitigation) {
            risk.RiskMitigation = Array.isArray(analysis.riskMitigation) 
              ? analysis.riskMitigation.join('. ') 
              : analysis.riskMitigation;
          }

          this.$set(this.aiJustifications[riskKey], 'riskMitigation',
            analysis.riskMitigationJustification ||
            'Mitigation strategies based on risk type, affected systems, and best practices for prevention, detection, and response. Implementation prioritized by effectiveness.');

          if (analysis.category) {
            risk.Category = analysis.category;
          }

          this.$set(this.aiJustifications[riskKey], 'category',
            analysis.categoryJustification ||
            'Category classification based on primary risk domain, business impact area, and regulatory requirements. Aligns with enterprise risk taxonomy.');

          if (analysis.businessImpact) {
            risk.BusinessImpact = analysis.businessImpact;
          }

          this.$set(this.aiJustifications[riskKey], 'businessImpact',
            analysis.businessImpactJustification ||
            'Business impact assessment covering revenue effects, operational disruption, compliance requirements, and strategic implications. Based on business continuity analysis.');

          // Update exposure rating if likelihood and impact changed
          if (risk.RiskLikelihood && risk.RiskImpact) {
            risk.RiskExposureRating = parseFloat((risk.RiskLikelihood * risk.RiskImpact).toFixed(2));
          }

          this.$notify({
            type: 'success',
            title: 'AI Analysis Complete',
            text: 'Enhanced AI analysis generated for this risk. Look for detailed AI insights in the field tooltips!'
          });

        } else {
          throw new Error(response.data?.message || 'AI analysis failed');
        }

      } catch (error) {
        console.error('Error generating AI analysis:', error);
        this.$notify({
          type: 'error',
          title: 'Analysis Failed',
          text: error.response?.data?.message || 'Failed to generate AI analysis. Please try again.'
        });
      } finally {
        this.isGeneratingAnalysis = false;
      }
    },

    // Enhanced AI tooltip that combines existing metadata with generated justifications
    getEnhancedAITooltip(risk, fieldName, riskIndex) {
      const riskKey = `risk_${riskIndex}`;
      const perField = risk._perField || {};
      const fieldInfo = perField[fieldName];
      
      // Start with basic AI info if field is AI-generated
      let tooltip = '';
      
      if (fieldInfo && fieldInfo.source === 'AI_GENERATED') {
        const confidence = Math.round((fieldInfo.confidence || 0.75) * 100);
        const rationale = fieldInfo.rationale || 'AI analyzed the document and predicted this value';
        
        tooltip = `🤖 AI GENERATED FIELD\n`;
        tooltip += `━━━━━━━━━━━━━━━━━━━━\n\n`;
        tooltip += `✓ Confidence Score: ${confidence}%\n\n`;
        tooltip += `📝 Document Analysis:\n${rationale}\n\n`;
      }
      
      // Add enhanced justification if available
      const fieldMapping = {
        'Criticality': 'criticality',
        'RiskLikelihood': 'riskLikelihood', 
        'RiskImpact': 'riskImpact',
        'PossibleDamage': 'possibleDamage',
        'RiskMitigation': 'riskMitigation',
        'Category': 'category',
        'BusinessImpact': 'businessImpact'
      };
      
      const justificationKey = fieldMapping[fieldName];
      if (justificationKey && this.aiJustifications[riskKey] && this.aiJustifications[riskKey][justificationKey]) {
        if (tooltip) tooltip += `━━━━━━━━━━━━━━━━━━━━\n`;
        tooltip += `🧠 ENHANCED AI ANALYSIS\n`;
        tooltip += `━━━━━━━━━━━━━━━━━━━━\n\n`;
        tooltip += `${this.aiJustifications[riskKey][justificationKey]}\n\n`;
      }
      
      if (tooltip) {
        tooltip += `━━━━━━━━━━━━━━━━━━━━\n`;
        tooltip += `💡 Tip: You can edit this value before saving. Click "Generate Analysis" for more AI insights.`;
      }
      
      return tooltip || this.getAITooltip(risk, fieldName);
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
<style src="./risk_ai.css" scoped></style>

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

/* Risk card actions styling */
.risk-card-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.btn-ai-analysis {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-ai-analysis:hover:not(:disabled) {
  background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-ai-analysis:disabled {
  background: linear-gradient(135deg, #a0aec0 0%, #718096 100%);
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.btn-ai-analysis i {
  font-size: 0.875rem;
}

/* Enhanced AI indicator styling */
.ai-indicator {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
  margin-left: 8px;
  cursor: help;
  transition: all 0.2s ease;
}

.ai-indicator:hover {
  background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%);
  transform: scale(1.05);
}

.ai-indicator i {
  font-size: 0.7rem;
}

/* AI generated field styling */
.ai-generated-field {
  background: linear-gradient(to right, #f8f9ff 0%, #ffffff 100%);
  border-left: 3px solid #667eea !important;
  position: relative;
}

.ai-generated-field::before {
  content: '🤖';
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  opacity: 0.6;
  font-size: 0.875rem;
  pointer-events: none;
}

/* Upload card header */
.upload-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.upload-card-header h2 {
  margin: 0;
  color: #2d3748;
  font-weight: 600;
}

.btn-clear-cache {
  background: #e2e8f0;
  color: #4a5568;
  border: none;
  padding: 8px 10px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.875rem;
}

.btn-clear-cache:hover {
  background: #cbd5e0;
  color: #2d3748;
  transform: translateY(-1px);
}

.btn-clear-cache i {
  font-size: 0.875rem;
}
</style>

