<template>
  <div class="incident-ai-container" :class="{ 'sidebar-collapsed': isSidebarCollapsed }">
    <!-- Header -->
    <div class="page-header">
      <div class="header-content">
        <h1><i class="fas fa-robot icon-md icon-primary"></i> AI-Powered Incident Document Ingestion</h1>
        <p class="subtitle">Upload documents and let AI extract and predict incident information automatically</p>
      </div>
    </div>

    <!-- Upload Section -->
    <div v-if="currentStep === 'upload'" class="upload-section">
      <div class="upload-card">
        <div class="upload-card-header">
          <h2>Upload Incident Document</h2>
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
            <i class="fas fa-shield-alt icon-sm icon-primary"></i>
            <span>Secure & private</span>
          </div>
          <div class="guide-item">
            <i class="fas fa-file-medical icon-sm icon-primary"></i>
            <span>Clean text extraction</span>
          </div>
          <div class="guide-item">
            <i class="fas fa-magic icon-sm icon-primary"></i>
            <span>AI-assisted fields</span>
          </div>
        </div>
        
        <div class="file-input-wrapper">
          <input 
            type="file" 
            ref="fileInput" 
            @change="handleFileSelect" 
            accept=".pdf,.docx,.xlsx,.xls,.txt"
            id="fileUpload"
          />
          <label for="fileUpload" class="btn-upload-document" title="Click to select a file">
            <i class="fas fa-file-upload icon-md"></i>
            <span class="file-label-text">{{ selectedFile ? selectedFile.name : 'Upload Document' }}</span>
          </label>
        </div>

        <button 
          @click="uploadAndProcess" 
          :disabled="!selectedFile || isProcessing"
          class="btn btn-submit"
        >
          <i class="fas fa-magic icon-md"></i>
          Process with AI
        </button>
      </div>
    </div>

    <!-- Processing Section -->
    <div v-if="currentStep === 'processing'" class="processing-section">
      <div class="processing-card">
        <div class="spinner-container">
          <div class="spinner"></div>
        </div>
        <h2>AI Processing Incident Document...</h2>
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
            class="btn-secondary"
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
        <h2><i class="fas fa-edit icon-md icon-primary"></i> Review Extracted Incidents</h2>
        <p>{{ extractedIncidents.length }} incident(s) found. Review and edit before saving.</p>
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

      <div class="incidents-container">
        <div v-for="(incident, index) in extractedIncidents" :key="index" class="incident-card">
          <div class="incident-card-header">
            <h3>Incident #{{ index + 1 }}</h3>
            <div class="incident-card-actions">
              <button 
                @click="generateAIAnalysis(incident, index)" 
                :disabled="isGeneratingAnalysis"
                class="btn-ai-analysis"
                title="Generate enhanced AI analysis and justifications"
              >
                <i class="fas fa-brain"></i>
                {{ isGeneratingAnalysis ? 'Analyzing...' : 'Generate Analysis' }}
              </button>
              <button @click="removeIncident(index)" class="btn-remove">
                <i class="fas fa-trash icon-md icon-white"></i>
              </button>
            </div>
          </div>

          <div class="incident-form">
            <!-- Row 1: Title -->
            <div class="form-row">
              <div class="form-group full-width">
                <label>
                  Incident Title <span class="required">*</span>
                  <span v-if="isAIGenerated(incident, 'IncidentTitle')" class="ai-indicator" :title="getEnhancedAITooltip(incident, 'IncidentTitle', index)">
                    <i class="fas fa-robot icon-sm"></i> AI {{ getConfidencePercent(incident, 'IncidentTitle') }}%
                  </span>
                </label>
                <input 
                  v-model="incident.IncidentTitle" 
                  type="text" 
                  placeholder="Brief incident title" 
                  maxlength="255"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(incident, 'IncidentTitle') }]"
                  required
                />
              </div>
            </div>

            <!-- Row 2: Description -->
            <div class="form-row">
              <div class="form-group full-width">
                <label>
                  Description
                  <span v-if="isAIGenerated(incident, 'Description')" class="ai-indicator" :title="getAITooltip(incident, 'Description')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(incident, 'Description') }}%
                  </span>
                </label>
                <textarea 
                  v-model="incident.Description" 
                  placeholder="Detailed incident description"
                  rows="4"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(incident, 'Description') }]"
                ></textarea>
              </div>
            </div>

            <!-- Row 3: Category and Status -->
            <div class="form-row">
              <div class="form-group">
                <label>
                  Incident Category
                  <span v-if="isAIGenerated(incident, 'IncidentCategory')" class="ai-indicator" :title="getAITooltip(incident, 'IncidentCategory')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(incident, 'IncidentCategory') }}%
                  </span>
                </label>
                <select v-model="incident.IncidentCategory" :class="['form-control', { 'ai-generated-field': isAIGenerated(incident, 'IncidentCategory') }]">
                  <option value="">Select Category</option>
                  <option value="Security Breach">Security Breach</option>
                  <option value="Data Loss">Data Loss</option>
                  <option value="System Outage">System Outage</option>
                  <option value="Compliance Violation">Compliance Violation</option>
                  <option value="Operational Failure">Operational Failure</option>
                  <option value="Third-Party Issue">Third-Party Issue</option>
                  <option value="Human Error">Human Error</option>
                  <option value="Natural Disaster">Natural Disaster</option>
                  <option value="Cyber Attack">Cyber Attack</option>
                  <option value="Privacy Incident">Privacy Incident</option>
                  <option value="Safety Incident">Safety Incident</option>
                  <option value="Financial Loss">Financial Loss</option>
                </select>
              </div>

              <div class="form-group">
                <label>
                  Status
                  <span v-if="isAIGenerated(incident, 'Status')" class="ai-indicator" :title="getAITooltip(incident, 'Status')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(incident, 'Status') }}%
                  </span>
                </label>
                <select v-model="incident.Status" :class="['form-control', { 'ai-generated-field': isAIGenerated(incident, 'Status') }]">
                  <option value="New">New</option>
                  <option value="In Progress">In Progress</option>
                  <option value="Under Investigation">Under Investigation</option>
                  <option value="Resolved">Resolved</option>
                  <option value="Closed">Closed</option>
                  <option value="Escalated">Escalated</option>
                  <option value="Risk Mitigated">Risk Mitigated</option>
                </select>
              </div>
            </div>

            <!-- Row 4: Criticality and Priority -->
            <div class="form-row">
              <div class="form-group">
                <label>
                  Criticality
                  <span v-if="isAIGenerated(incident, 'Criticality')" class="ai-indicator" :title="getEnhancedAITooltip(incident, 'Criticality', index)">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(incident, 'Criticality') }}%
                  </span>
                </label>
                <select v-model="incident.Criticality" :class="['form-control', { 'ai-generated-field': isAIGenerated(incident, 'Criticality') }]">
                  <option value="Low">Low</option>
                  <option value="Medium">Medium</option>
                  <option value="High">High</option>
                  <option value="Critical">Critical</option>
                </select>
              </div>

              <div class="form-group">
                <label>
                  Risk Priority
                  <span v-if="isAIGenerated(incident, 'RiskPriority')" class="ai-indicator" :title="getEnhancedAITooltip(incident, 'RiskPriority', index)">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(incident, 'RiskPriority') }}%
                  </span>
                </label>
                <select v-model="incident.RiskPriority" :class="['form-control', { 'ai-generated-field': isAIGenerated(incident, 'RiskPriority') }]">
                  <option value="Low">Low</option>
                  <option value="Medium">Medium</option>
                  <option value="High">High</option>
                  <option value="Critical">Critical</option>
                </select>
              </div>
            </div>

            <!-- Row 5: Origin and Risk Category -->
            <div class="form-row">
              <div class="form-group">
                <label>
                  Origin
                  <span v-if="isAIGenerated(incident, 'Origin')" class="ai-indicator" :title="getAITooltip(incident, 'Origin')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(incident, 'Origin') }}%
                  </span>
                </label>
                <select v-model="incident.Origin" :class="['form-control', { 'ai-generated-field': isAIGenerated(incident, 'Origin') }]">
                  <option value="MANUAL">Manual</option>
                  <option value="AUDIT_FINDING">Audit Finding</option>
                  <option value="AUTOMATED">Automated</option>
                  <option value="EXTERNAL_REPORT">External Report</option>
                  <option value="INTERNAL_DETECTION">Internal Detection</option>
                </select>
              </div>

              <div class="form-group">
                <label>
                  Risk Category
                  <span v-if="isAIGenerated(incident, 'RiskCategory')" class="ai-indicator" :title="getAITooltip(incident, 'RiskCategory')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(incident, 'RiskCategory') }}%
                  </span>
                </label>
                <select v-model="incident.RiskCategory" :class="['form-control', { 'ai-generated-field': isAIGenerated(incident, 'RiskCategory') }]">
                  <option value="">Select Category</option>
                  <option value="Operational">Operational</option>
                  <option value="Financial">Financial</option>
                  <option value="Strategic">Strategic</option>
                  <option value="Compliance">Compliance</option>
                  <option value="Technical">Technical</option>
                  <option value="Reputational">Reputational</option>
                  <option value="Information Security">Information Security</option>
                  <option value="Process Risk">Process Risk</option>
                  <option value="Third-Party">Third-Party</option>
                  <option value="Regulatory">Regulatory</option>
                  <option value="Governance">Governance</option>
                </select>
              </div>
            </div>

            <!-- Row 6: Affected Business Unit and Geographic Location -->
            <div class="form-row">
              <div class="form-group">
                <label>
                  Affected Business Unit
                  <span v-if="isAIGenerated(incident, 'AffectedBusinessUnit')" class="ai-indicator" :title="getAITooltip(incident, 'AffectedBusinessUnit')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(incident, 'AffectedBusinessUnit') }}%
                  </span>
                </label>
                <input 
                  v-model="incident.AffectedBusinessUnit" 
                  type="text" 
                  placeholder="Business unit impacted"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(incident, 'AffectedBusinessUnit') }]"
                />
              </div>

              <div class="form-group">
                <label>
                  Geographic Location
                  <span v-if="isAIGenerated(incident, 'GeographicLocation')" class="ai-indicator" :title="getAITooltip(incident, 'GeographicLocation')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(incident, 'GeographicLocation') }}%
                  </span>
                </label>
                <input 
                  v-model="incident.GeographicLocation" 
                  type="text" 
                  placeholder="Location where incident occurred"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(incident, 'GeographicLocation') }]"
                />
              </div>
            </div>

            <!-- Row 7: Systems and Cost -->
            <div class="form-row">
              <div class="form-group">
                <label>
                  Systems/Assets Involved
                  <span v-if="isAIGenerated(incident, 'SystemsAssetsInvolved')" class="ai-indicator" :title="getEnhancedAITooltip(incident, 'SystemsAssetsInvolved', index)">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(incident, 'SystemsAssetsInvolved') }}%
                  </span>
                </label>
                <textarea 
                  v-model="incident.SystemsAssetsInvolved" 
                  placeholder="Systems and assets affected"
                  rows="2"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(incident, 'SystemsAssetsInvolved') }]"
                ></textarea>
              </div>

              <div class="form-group">
                <label>
                  Cost of Incident
                  <span v-if="isAIGenerated(incident, 'CostOfIncident')" class="ai-indicator" :title="getEnhancedAITooltip(incident, 'CostOfIncident', index)">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(incident, 'CostOfIncident') }}%
                  </span>
                </label>
                <input 
                  v-model="incident.CostOfIncident" 
                  type="text" 
                  placeholder="$0 or Not assessed"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(incident, 'CostOfIncident') }]"
                />
              </div>
            </div>

            <!-- Row 8: Initial Impact Assessment -->
            <div class="form-row">
              <div class="form-group full-width">
                <label>
                  Initial Impact Assessment
                  <span v-if="isAIGenerated(incident, 'InitialImpactAssessment')" class="ai-indicator" :title="getAITooltip(incident, 'InitialImpactAssessment')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(incident, 'InitialImpactAssessment') }}%
                  </span>
                </label>
                <textarea 
                  v-model="incident.InitialImpactAssessment" 
                  placeholder="Initial assessment of impact"
                  rows="3"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(incident, 'InitialImpactAssessment') }]"
                ></textarea>
              </div>
            </div>

            <!-- Row 9: Possible Damage -->
            <div class="form-row">
              <div class="form-group full-width">
                <label>
                  Possible Damage
                  <span v-if="isAIGenerated(incident, 'PossibleDamage')" class="ai-indicator" :title="getAITooltip(incident, 'PossibleDamage')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(incident, 'PossibleDamage') }}%
                  </span>
                </label>
                <textarea 
                  v-model="incident.PossibleDamage" 
                  placeholder="Potential damages and consequences"
                  rows="3"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(incident, 'PossibleDamage') }]"
                ></textarea>
              </div>
            </div>

            <!-- Row 10: Contacts -->
            <div class="form-row">
              <div class="form-group">
                <label>
                  Internal Contacts
                  <span v-if="isAIGenerated(incident, 'InternalContacts')" class="ai-indicator" :title="getAITooltip(incident, 'InternalContacts')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(incident, 'InternalContacts') }}%
                  </span>
                </label>
                <textarea 
                  v-model="incident.InternalContacts" 
                  placeholder="Internal personnel involved"
                  rows="2"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(incident, 'InternalContacts') }]"
                ></textarea>
              </div>

              <div class="form-group">
                <label>
                  External Parties Involved
                  <span v-if="isAIGenerated(incident, 'ExternalPartiesInvolved')" class="ai-indicator" :title="getAITooltip(incident, 'ExternalPartiesInvolved')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(incident, 'ExternalPartiesInvolved') }}%
                  </span>
                </label>
                <textarea 
                  v-model="incident.ExternalPartiesInvolved" 
                  placeholder="External organizations involved"
                  rows="2"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(incident, 'ExternalPartiesInvolved') }]"
                ></textarea>
              </div>
            </div>

            <!-- Row 11: Policies Violated -->
            <div class="form-row">
              <div class="form-group full-width">
                <label>
                  Policies/Procedures Violated
                  <span v-if="isAIGenerated(incident, 'RelevantPoliciesProceduresViolated')" class="ai-indicator" :title="getAITooltip(incident, 'RelevantPoliciesProceduresViolated')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(incident, 'RelevantPoliciesProceduresViolated') }}%
                  </span>
                </label>
                <textarea 
                  v-model="incident.RelevantPoliciesProceduresViolated" 
                  placeholder="Policies or procedures violated"
                  rows="2"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(incident, 'RelevantPoliciesProceduresViolated') }]"
                ></textarea>
              </div>
            </div>

            <!-- Row 12: Control Failures -->
            <div class="form-row">
              <div class="form-group full-width">
                <label>
                  Control Failures
                  <span v-if="isAIGenerated(incident, 'ControlFailures')" class="ai-indicator" :title="getEnhancedAITooltip(incident, 'ControlFailures', index)">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(incident, 'ControlFailures') }}%
                  </span>
                </label>
                <textarea 
                  v-model="incident.ControlFailures" 
                  placeholder="Controls that failed or were bypassed"
                  rows="2"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(incident, 'ControlFailures') }]"
                ></textarea>
              </div>
            </div>

            <!-- Row 13: Lessons Learned and Classification -->
            <div class="form-row">
              <div class="form-group">
                <label>
                  Lessons Learned
                  <span v-if="isAIGenerated(incident, 'LessonsLearned')" class="ai-indicator" :title="getEnhancedAITooltip(incident, 'LessonsLearned', index)">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(incident, 'LessonsLearned') }}%
                  </span>
                </label>
                <textarea 
                  v-model="incident.LessonsLearned" 
                  placeholder="Key insights and learnings"
                  rows="3"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(incident, 'LessonsLearned') }]"
                ></textarea>
              </div>

              <div class="form-group">
                <label>
                  Incident Classification
                  <span v-if="isAIGenerated(incident, 'IncidentClassification')" class="ai-indicator" :title="getAITooltip(incident, 'IncidentClassification')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(incident, 'IncidentClassification') }}%
                  </span>
                </label>
                <input 
                  v-model="incident.IncidentClassification" 
                  type="text" 
                  placeholder="Classification code or category"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(incident, 'IncidentClassification') }]"
                />
              </div>
            </div>

            <!-- Row 14: Comments -->
            <div class="form-row">
              <div class="form-group full-width">
                <label>
                  Comments
                  <span v-if="isAIGenerated(incident, 'Comments')" class="ai-indicator" :title="getAITooltip(incident, 'Comments')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(incident, 'Comments') }}%
                  </span>
                </label>
                <textarea 
                  v-model="incident.Comments" 
                  placeholder="Additional notes or observations"
                  rows="2"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(incident, 'Comments') }]"
                ></textarea>
              </div>
            </div>

            <!-- Row 15: Boolean Flags -->
            <div class="form-row">
              <div class="form-group checkbox-group">
                <label>
                  <input type="checkbox" v-model="incident.RepeatedNot" />
                  <span>Repeated Incident</span>
                  <span v-if="isAIGenerated(incident, 'RepeatedNot')" class="ai-indicator" :title="getAITooltip(incident, 'RepeatedNot')">
                    <i class="fas fa-robot icon-sm"></i> AI
                  </span>
                </label>
              </div>

              <div class="form-group checkbox-group">
                <label>
                  <input type="checkbox" v-model="incident.ReopenedNot" />
                  <span>Reopened Incident</span>
                  <span v-if="isAIGenerated(incident, 'ReopenedNot')" class="ai-indicator" :title="getAITooltip(incident, 'ReopenedNot')">
                    <i class="fas fa-robot icon-sm"></i> AI
                  </span>
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="review-actions">
        <button @click="currentStep = 'upload'" class="btn-secondary">
          <i class="fas fa-arrow-left icon-md"></i>
          Back to Upload
        </button>
        <button @click="saveAllIncidents" :disabled="isSaving" class="btn btn-submit">
          <i class="fas fa-save icon-md"></i>
          {{ isSaving ? 'Saving...' : 'Save All Incidents' }}
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
        <p>{{ savedCount }} incident(s) have been successfully saved to the database.</p>
        
        <div class="success-actions">
          <button @click="resetToUpload" class="btn-secondary">
            <i class="fas fa-plus icon-md"></i>
            Upload Another
          </button>
          <button @click="navigateToIncidents" class="btn-primary">
            <i class="fas fa-list icon-md"></i>
            View Incidents
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import { API_ENDPOINTS } from '@/config/api';

export default {
  name: 'IncidentAIImport',
  
  data() {
    return {
      selectedFile: null,
      isProcessing: false,
      isSaving: false,
      currentStep: 'upload', // 'upload', 'processing', 'review', 'success'
      extractedIncidents: [],
      savedCount: 0,
      processingStatus: 'Initializing...',
      processingProgress: 0,
      currentProcessingStep: 0,
      currentProcessingPhase: 'upload', // 'upload', 'extract', 'ai', 'finalize'
      
      // Progress details
      progressDetails: {
        estimatedFields: 0,
        estimatedTime: 0,
        processedItems: 0
      },
      
      // AI Justifications for enhanced tooltips (similar to CreateIncident.vue)
      aiJustifications: {},
      isGeneratingAnalysis: false,
      
      isSidebarCollapsed: false,
      uploadController: null,
      aiProgressTimer: null
    };
  },

  mounted() {
    this.checkSidebarState();
    
    document.addEventListener('click', (event) => {
      if (event.target.closest('.toggle') || event.target.closest('.expand-button')) {
        setTimeout(() => {
          this.checkSidebarState();
        }, 300);
      }
    });

    // Load processing state on component mount
    this.loadProcessingState();
    this.resumeProcessingIfNeeded();
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
        progressDetails: this.progressDetails,
        extractedIncidents: this.extractedIncidents,
        selectedFile: this.selectedFile ? { name: this.selectedFile.name, size: this.selectedFile.size } : null,
        timestamp: Date.now()
      };
      try {
        sessionStorage.setItem('incident_ai_processing_state', JSON.stringify(state));
        console.log('💾 Incident AI processing state saved:', state);
      } catch (error) {
        console.error('❌ Failed to save incident AI processing state:', error);
      }
    },

    loadProcessingState() {
      try {
        const savedState = sessionStorage.getItem('incident_ai_processing_state');
        if (!savedState) {
          console.log('❌ No saved incident AI state found');
          return false;
        }

        const state = JSON.parse(savedState);

        // Check if state is not too old (24 hours max)
        const maxAge = 24 * 60 * 60 * 1000; // 24 hours in milliseconds
        if (Date.now() - state.timestamp > maxAge) {
          console.log('❌ Saved incident AI state is too old, clearing');
          sessionStorage.removeItem('incident_ai_processing_state');
          return false;
        }

        // Restore state
        this.currentStep = state.currentStep || 'upload';
        this.isProcessing = state.isProcessing || false;
        this.processingStatus = state.processingStatus || 'Initializing...';
        this.processingProgress = state.processingProgress || 0;
        this.currentProcessingStep = state.currentProcessingStep || 0;
        this.currentProcessingPhase = state.currentProcessingPhase || 'upload';
        this.progressDetails = state.progressDetails || { estimatedFields: 0, estimatedTime: 0, processedItems: 0 };
        this.extractedIncidents = state.extractedIncidents || [];
        this.selectedFile = null; // Don't restore file object, just clear it

        console.log('✅ Incident AI processing state restored:', state);
        return true;
      } catch (error) {
        console.error('❌ Failed to load incident AI processing state:', error);
        sessionStorage.removeItem('incident_ai_processing_state');
        return false;
      }
    },

    clearProcessingState() {
      try {
        sessionStorage.removeItem('incident_ai_processing_state');
        this.aiJustifications = {};
        console.log('🗑️ Incident AI processing state cleared');
      } catch (error) {
        console.error('❌ Failed to clear incident AI processing state:', error);
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
        console.log('🔄 Resuming incident AI processing from step:', this.currentProcessingStep);
        // Continue from where it left off - progress will update naturally
        this.$notify({
          type: 'info',
          title: 'Resuming',
          text: `Resuming incident AI processing from ${this.processingProgress}% (${this.currentProcessingPhase})`
        });
      } else if (this.currentStep === 'review' && this.extractedIncidents.length > 0) {
        console.log('🔄 Incident AI review data restored');
        this.$notify({
          type: 'info',
          title: 'Data Restored',
          text: `Restored ${this.extractedIncidents.length} incident(s) for review`
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
          'application/vnd.ms-excel',
          'text/plain'
        ];
        
        if (validTypes.includes(file.type) || 
            file.name.match(/\.(pdf|docx|doc|xlsx|xls|txt)$/i)) {
          this.selectedFile = file;
        } else {
          this.$notify({
            type: 'error',
            title: 'Invalid File Type',
            text: 'Please upload a PDF, DOCX, Excel, or TXT file.'
          });
          event.target.value = '';
        }
      }
    },

    async uploadAndProcess() {
      if (!this.selectedFile) {
        this.$notify({
          type: 'error',
          title: 'No File Selected',
          text: 'Please select a file to upload.'
        });
        return;
      }

      this.isProcessing = true;
      this.currentStep = 'processing';
      this.processingProgress = 0;
      this.currentProcessingStep = 1;
      this.currentProcessingPhase = 'upload';
      this.processingStatus = 'Initializing AI processing...';
      
      // Estimate processing details based on file size
      this.estimateProcessingDetails();
      this.saveProcessingState();

      const formData = new FormData();
      formData.append('file', this.selectedFile);
      formData.append('user_id', localStorage.getItem('user_id') || '1');

      try {
        // Update progress for upload start
        this.updateProgressWithPhase(10, 'upload', 'Uploading document...');
        this.currentProcessingStep = 1;

        // Create AbortController for this upload so we can cancel it
        const controller = new AbortController();
        this.uploadController = controller;

        const response = await axios.post(
          API_ENDPOINTS.INCIDENT_AI_UPLOAD,
          formData,
          {
            headers: {
              'Content-Type': 'multipart/form-data',
              'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            },
            timeout: 300000,
            signal: controller.signal,
            onUploadProgress: (progressEvent) => {
              if (progressEvent.total) {
                const uploadPercent = Math.round((progressEvent.loaded * 30) / progressEvent.total); // 0-30% for upload
                this.updateProgressWithPhase(10 + uploadPercent, 'upload', 'Uploading document...');
                // When upload is essentially done, start a smooth AI phase progress
                if (uploadPercent >= 30 && !this.aiProgressTimer) {
                  this.startAIPhaseProgress();
                }
              }
            }
          }
        );

        // Ensure AI phase is active while backend is processing
        this.updateProgressWithPhase(Math.max(this.processingProgress, 40), 'ai', 'AI analyzing and generating incident fields...');

        // Backend processing is complete at this point
        this.stopAIPhaseProgress();
        this.updateProgressWithPhase(100, 'finalize', 'Processing complete!');
        this.currentProcessingStep = 4;
        this.uploadController = null;

        if (response.data.status === 'success') {
          const incidents = response.data.incidents || [];
          
          console.log('🔍 DEBUG: Raw incidents from backend:', JSON.stringify(incidents[0]?._meta, null, 2));
          
          this.extractedIncidents = incidents.map((incident, idx) => {
            const meta = incident._meta || {};
            const perField = meta.per_field || {};
            
            const aiFieldsList = Object.keys(perField).filter(k => perField[k]?.source === 'AI_GENERATED');
            const extractedFieldsList = Object.keys(perField).filter(k => perField[k]?.source === 'EXTRACTED');
            
            console.log(`📋 Incident ${idx + 1} Metadata Summary:`);
            console.log(`   ✓ Total fields with metadata: ${Object.keys(perField).length}`);
            console.log(`   🤖 AI Generated: ${aiFieldsList.length} fields`);
            console.log(`   📄 Extracted: ${extractedFieldsList.length} fields`);
            console.log(`   🎯 Sample AI fields:`, aiFieldsList.slice(0, 5));
            
            if (aiFieldsList.length === 0) {
              console.error('❌ CRITICAL: No AI-generated fields found! Check backend metadata generation.');
            }
            
            // Create mapped incident with proper structure
            const mappedIncident = {
              ...incident,
              _meta: meta,
              _perField: perField
            };
            
            // Log sample field to verify structure
            if (perField['IncidentTitle']) {
              console.log(`   📝 Sample: IncidentTitle metadata:`, perField['IncidentTitle']);
            }
            
            return mappedIncident;
          });

          console.log('✅ Extracted incidents ready for display');
          
          // Comprehensive metadata summary
          const summary = {
            totalIncidents: this.extractedIncidents.length,
            aiGenerated: 0,
            extracted: 0,
            default: 0,
            computed: 0,
            totalFields: 0
          };
          
          this.extractedIncidents.forEach((inc) => {
            const perField = inc._perField || {};
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
          console.log(`   📋 Total Incidents: ${summary.totalIncidents}`);
          console.log(`   🤖 AI Generated Fields: ${summary.aiGenerated}`);
          console.log(`   📄 Extracted Fields: ${summary.extracted}`);
          console.log(`   🔧 Default Fields: ${summary.default}`);
          console.log(`   🧮 Computed Fields: ${summary.computed}`);
          console.log(`   📊 Total Fields Tracked: ${summary.totalFields}`);

          // Display data immediately - no artificial delays
          this.currentStep = 'review';
          this.isProcessing = false;
          this.saveProcessingState();

          // Count AI-generated fields for notification
          const aiFieldsCount = summary.aiGenerated;

          this.$notify({
            type: 'success',
            title: 'AI Processing Complete',
            text: `Extracted ${this.extractedIncidents.length} incident(s) with ${aiFieldsCount} AI-generated fields. Look for 🤖 icons showing AI predictions with confidence scores!`
          });
        } else {
          throw new Error(response.data.message || 'Processing failed');
        }
      } catch (error) {
        console.error('Error processing document:', error);
        this.stopAIPhaseProgress();
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
            text: 'AI incident processing was cancelled.'
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

      this.stopAIPhaseProgress();
      this.isProcessing = false;
      this.currentStep = 'upload';
      this.processingStatus = 'Processing cancelled by user';
      this.processingProgress = 0;
      this.currentProcessingStep = 0;
      this.currentProcessingPhase = 'upload';
      this.progressDetails = { estimatedFields: 0, estimatedTime: 0, processedItems: 0 };
      this.clearProcessingState();

      this.$notify({
        type: 'info',
        title: 'Cancelled',
        text: 'AI incident processing was cancelled.'
      });
    },

    isAIGenerated(incident, fieldName) {
      const perField = incident._perField || incident._meta?.per_field || {};
      const fieldInfo = perField[fieldName];
      if (!fieldInfo) return false;
      return fieldInfo.source === 'AI_GENERATED';
    },

    getAITooltip(incident, fieldName) {
      const perField = incident._perField || {};
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

    getConfidencePercent(incident, fieldName) {
      const perField = incident._perField || {};
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

    delay(ms) {
      return new Promise(resolve => setTimeout(resolve, ms));
    },

    removeIncident(index) {
      if (confirm('Are you sure you want to remove this incident?')) {
        this.extractedIncidents.splice(index, 1);
      }
    },

    async saveAllIncidents() {
      const invalidIncidents = this.extractedIncidents.filter(inc => !inc.IncidentTitle);
      if (invalidIncidents.length > 0) {
        this.$notify({
          type: 'error',
          title: 'Validation Error',
          text: 'All incidents must have a title.'
        });
        return;
      }

      this.isSaving = true;
      this.saveProcessingState();

      try {
        const cleanIncidents = this.extractedIncidents.map(inc => {
          // eslint-disable-next-line no-unused-vars
          const { _meta, _perField, ...cleanInc } = inc;
          return cleanInc;
        });

        const response = await axios.post(
          API_ENDPOINTS.INCIDENT_AI_SAVE,
          {
            incidents: cleanIncidents,
            user_id: localStorage.getItem('user_id') || '1'
          },
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
              'Content-Type': 'application/json'
            }
          }
        );

        if (response.data.status === 'success') {
          this.savedCount = response.data.saved?.length || this.extractedIncidents.length;
          this.currentStep = 'success';
          this.clearProcessingState();
          
          this.$notify({
            type: 'success',
            title: 'Success',
            text: `Successfully saved ${this.savedCount} incident(s) to the database.`
          });
        } else {
          throw new Error(response.data.message || 'Save failed');
        }
      } catch (error) {
        console.error('Error saving incidents:', error);
        this.$notify({
          type: 'error',
          title: 'Save Failed',
          text: error.response?.data?.message || error.message || 'Failed to save incidents. Please try again.'
        });
      } finally {
        this.isSaving = false;
      }
    },

    resetToUpload() {
      this.selectedFile = null;
      this.extractedIncidents = [];
      this.savedCount = 0;
      this.processingProgress = 0;
      this.currentProcessingStep = 0;
      this.currentStep = 'upload';
      this.clearProcessingState();
      if (this.$refs.fileInput) {
        this.$refs.fileInput.value = '';
      }
    },

    navigateToIncidents() {
      this.$router.push('/incident/incident');
    },

    checkSidebarState() {
      const sidebar = document.querySelector('.sidebar');
      if (sidebar) {
        this.isSidebarCollapsed = sidebar.classList.contains('collapsed');
      }
    },

    getTotalAIFields() {
      let total = 0;
      this.extractedIncidents.forEach(incident => {
        const perField = incident._perField || {};
        const aiFields = Object.keys(perField).filter(k => perField[k]?.source === 'AI_GENERATED');
        total += aiFields.length;
      });
      return total;
    },

    getAverageConfidence() {
      let sum = 0;
      let count = 0;
      this.extractedIncidents.forEach(incident => {
        const perField = incident._perField || {};
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

    // ===== NEW PROGRESS TRACKING METHODS =====
    
    updateProgressWithPhase(percentage, phase, status) {
      this.processingProgress = percentage;
      this.currentProcessingPhase = phase;
      this.processingStatus = status;
      this.saveProcessingState();
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
      // Estimate processing details based on file size (tuned for incidents)
      const fileSizeKB = this.selectedFile ? Math.round(this.selectedFile.size / 1024) : 0;
      
      // Incident fields that are typically generated
      const baseFields = 24; // Approximate number of incident fields
      
      // Estimate fields based on file size
      if (fileSizeKB < 50) {
        this.progressDetails.estimatedFields = Math.min(baseFields, 18);
        this.progressDetails.estimatedTime = 15; // seconds
      } else if (fileSizeKB < 200) {
        this.progressDetails.estimatedFields = Math.min(baseFields, 22);
        this.progressDetails.estimatedTime = 25;
      } else {
        this.progressDetails.estimatedFields = baseFields;
        this.progressDetails.estimatedTime = 35;
      }
      
      this.progressDetails.processedItems = 0;
    },
    
    formatFileSize(bytes) {
      if (bytes === 0) return '0 B';
      const k = 1024;
      const sizes = ['B', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    },
    
    formatTime(seconds) {
      if (seconds < 60) return `${seconds}s`;
      const minutes = Math.floor(seconds / 60);
      const remainingSeconds = seconds % 60;
      return `${minutes}m ${remainingSeconds}s`;
    },
    
    getFieldCoverage() {
      if (this.extractedIncidents.length === 0) return 0;
      
      const incidentFieldsCount = 24; // Total expected incident fields
      let totalFilledFields = 0;
      
      this.extractedIncidents.forEach(incident => {
        const filledFields = Object.keys(incident).filter(key => {
          if (key.startsWith('_')) return false; // Skip metadata
          const value = incident[key];
          return value !== null && value !== undefined && value !== '' && 
                 !(Array.isArray(value) && value.length === 0) && 
                 !(typeof value === 'object' && Object.keys(value).length === 0);
        });
        totalFilledFields += filledFields.length;
      });
      
      const averageFilledFields = totalFilledFields / this.extractedIncidents.length;
      return Math.round((averageFilledFields / incidentFieldsCount) * 100);
    },
        
    resetForm() {
      this.selectedFile = null;
      this.stopAIPhaseProgress();
      this.isProcessing = false;
      this.isSaving = false;
      this.currentStep = 'upload';
      this.extractedIncidents = [];
      this.savedCount = 0;
      this.processingStatus = 'Initializing...';
      this.processingProgress = 0;
      this.currentProcessingStep = 0;
      this.currentProcessingPhase = 'upload';
      this.progressDetails = { estimatedFields: 0, estimatedTime: 0, processedItems: 0 };
      this.uploadController = null;
      this.aiJustifications = {};
      this.clearProcessingState();
    },

    // Generate AI analysis for enhanced tooltips
    async generateAIAnalysis(incident, incidentIndex) {
      if (!incident.IncidentTitle || !incident.Description) {
        this.$notify({
          type: 'error',
          title: 'Missing Information',
          text: 'Please ensure incident has both title and description before generating analysis.'
        });
        return;
      }

      if (incident.IncidentTitle.trim().length < 3) {
        this.$notify({
          type: 'error',
          title: 'Invalid Title',
          text: 'Incident title must be at least 3 characters long.'
        });
        return;
      }

      this.isGeneratingAnalysis = true;

      try {
        const response = await axios.post(
          API_ENDPOINTS.INCIDENT_GENERATE_ANALYSIS,
          {
            title: incident.IncidentTitle,
            description: incident.Description
          },
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
              'Content-Type': 'application/json'
            }
          }
        );

        if (response.data && response.data.success) {
          const analysis = response.data.analysis;
          
          console.log('🧠 AI Analysis received:', analysis);

          // Create unique key for this incident
          const incidentKey = `incident_${incidentIndex}`;
          
          // Initialize justifications for this incident
          if (!this.aiJustifications[incidentKey]) {
            this.$set(this.aiJustifications, incidentKey, {});
          }

          // Map analysis to form fields and set justifications
          if (analysis.riskPriority) {
            const priorityMap = {
              'P0': 'Critical',
              'P1': 'High',
              'P2': 'Medium',
              'P3': 'Low'
            };
            incident.RiskPriority = priorityMap[analysis.riskPriority] || analysis.riskPriority;
          }

          this.$set(this.aiJustifications[incidentKey], 'riskPriority', 
            analysis.riskPriorityJustification ||
            analysis.riskPriorityReason ||
            analysis.priorityJustification ||
            'Priority assessment based on incident scope, customer impact, and regulatory requirements. Classification follows banking incident response protocols.');

          if (analysis.criticality) {
            incident.Criticality = analysis.criticality;
          }

          this.$set(this.aiJustifications[incidentKey], 'criticality',
            analysis.criticalityJustification ||
            analysis.criticalityReason ||
            'Criticality determined by potential business impact, system dependencies, customer exposure, and regulatory implications. Follows enterprise risk assessment guidelines.');

          if (analysis.costOfIncident) {
            incident.CostOfIncident = typeof analysis.costOfIncident === 'number' 
              ? `$${analysis.costOfIncident.toLocaleString()}` 
              : analysis.costOfIncident;
          }

          this.$set(this.aiJustifications[incidentKey], 'costOfIncident',
            analysis.costJustification ||
            'Cost estimation includes direct incident response, recovery, investigation, regulatory compliance, and potential business impact. Based on industry benchmarks and historical data.');

          if (analysis.possibleDamage) {
            incident.PossibleDamage = Array.isArray(analysis.possibleDamage) 
              ? analysis.possibleDamage.join(', ') 
              : analysis.possibleDamage;
          }

          this.$set(this.aiJustifications[incidentKey], 'possibleDamage',
            analysis.possibleDamageJustification ||
            'Damage assessment considers operational disruption, data integrity, customer impact, regulatory exposure, and reputational risks. Severity based on incident characteristics.');

          if (analysis.systemsInvolved) {
            incident.SystemsAssetsInvolved = Array.isArray(analysis.systemsInvolved) 
              ? analysis.systemsInvolved.join(', ') 
              : analysis.systemsInvolved;
          }

          this.$set(this.aiJustifications[incidentKey], 'systemsInvolved',
            analysis.systemsJustification ||
            'System identification based on incident description, affected processes, and typical infrastructure dependencies. Includes primary and secondary impact systems.');

          if (analysis.initialImpactAssessment) {
            incident.InitialImpactAssessment = analysis.initialImpactAssessment;
          }

          this.$set(this.aiJustifications[incidentKey], 'initialImpactAssessment',
            analysis.impactJustification ||
            'Impact assessment considers immediate operational effects, customer experience, data integrity, compliance status, and potential escalation scenarios.');

          if (analysis.mitigationSteps) {
            // Note: mitigationSteps might map to Comments or a similar field
            const mitigationText = Array.isArray(analysis.mitigationSteps) 
              ? analysis.mitigationSteps.join('. ') 
              : analysis.mitigationSteps;
            
            if (incident.Comments) {
              incident.Comments += `\n\nSuggested Mitigation: ${mitigationText}`;
            } else {
              incident.Comments = `Suggested Mitigation: ${mitigationText}`;
            }
          }

          this.$set(this.aiJustifications[incidentKey], 'comments',
            analysis.mitigationJustification ||
            'Mitigation strategies based on incident type, affected systems, and best practices for containment, recovery, and prevention of recurrence.');

          if (analysis.violatedPolicies) {
            incident.RelevantPoliciesProceduresViolated = Array.isArray(analysis.violatedPolicies) 
              ? analysis.violatedPolicies.join(', ') 
              : analysis.violatedPolicies;
          }

          this.$set(this.aiJustifications[incidentKey], 'violatedPolicies',
            analysis.violatedPoliciesJustification ||
            'Policy violations identified through analysis of incident characteristics, affected processes, and regulatory requirements. Based on enterprise policy framework.');

          if (analysis.procedureControlFailures) {
            incident.ControlFailures = Array.isArray(analysis.procedureControlFailures) 
              ? analysis.procedureControlFailures.join(', ') 
              : analysis.procedureControlFailures;
          }

          this.$set(this.aiJustifications[incidentKey], 'procedureControlFailures',
            analysis.controlFailuresJustification ||
            'Control failures identified through root cause analysis, comparing incident characteristics with expected control effectiveness and security frameworks.');

          if (analysis.lessonsLearned) {
            incident.LessonsLearned = Array.isArray(analysis.lessonsLearned) 
              ? analysis.lessonsLearned.join('. ') 
              : analysis.lessonsLearned;
          }

          this.$set(this.aiJustifications[incidentKey], 'lessonsLearned',
            analysis.lessonsLearnedJustification ||
            'Lessons learned derived from incident analysis, control failure assessment, and industry best practices for prevention and response improvement.');

          this.$notify({
            type: 'success',
            title: 'AI Analysis Complete',
            text: 'Enhanced AI analysis generated for this incident. Look for detailed AI insights in the field tooltips!'
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
    getEnhancedAITooltip(incident, fieldName, incidentIndex) {
      const incidentKey = `incident_${incidentIndex}`;
      const perField = incident._perField || {};
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
        'RiskPriority': 'riskPriority',
        'Criticality': 'criticality', 
        'CostOfIncident': 'costOfIncident',
        'PossibleDamage': 'possibleDamage',
        'SystemsAssetsInvolved': 'systemsInvolved',
        'InitialImpactAssessment': 'initialImpactAssessment',
        'Comments': 'comments',
        'RelevantPoliciesProceduresViolated': 'violatedPolicies',
        'ControlFailures': 'procedureControlFailures',
        'LessonsLearned': 'lessonsLearned'
      };
      
      const justificationKey = fieldMapping[fieldName];
      if (justificationKey && this.aiJustifications[incidentKey] && this.aiJustifications[incidentKey][justificationKey]) {
        if (tooltip) tooltip += `━━━━━━━━━━━━━━━━━━━━\n`;
        tooltip += `🧠 ENHANCED AI ANALYSIS\n`;
        tooltip += `━━━━━━━━━━━━━━━━━━━━\n\n`;
        tooltip += `${this.aiJustifications[incidentKey][justificationKey]}\n\n`;
      }
      
      if (tooltip) {
        tooltip += `━━━━━━━━━━━━━━━━━━━━\n`;
        tooltip += `💡 Tip: You can edit this value before saving. Click "Generate Analysis" for more AI insights.`;
      }
      
      return tooltip;
    }
  }
};
</script>

<style scoped src="./incident_ai_import.css"></style>
