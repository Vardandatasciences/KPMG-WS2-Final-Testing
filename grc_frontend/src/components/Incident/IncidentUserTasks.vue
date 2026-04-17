<template>
  <div class="incident-tasks-page">
    <div class="incident-content">
      <h1 class="incident-title">Incident Task Management</h1>

      <!-- User Filter -->
      <div class="user-filter-section">
        <CustomDropdown 
          v-model="selectedUserId"
          :config="userFilterConfig"
          @change="fetchData"
        />
      </div>

      <!-- Task Type Tabs -->
      <div class="task-type-tabs">
        <button 
          :class="['task-type-button', { active: activeTab === 'user' }]" 
          @click="activeTab = 'user'"
        >                           
          My Tasks
          <span class="task-count">{{ userIncidents.length }}</span>
        </button>
        <button 
          :class="['task-type-button', { active: activeTab === 'reviewer' }]" 
          @click="switchToReviewerTab"
        >
          Reviewer Tasks
          <span class="task-count">{{ reviewerTasks.length }}</span>
        </button>
      </div>

      <!-- Loading and Error States -->
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <span>Loading data...</span>
      </div>
      
      <div v-else-if="error" class="error-state">
        {{ error }}
      </div>

      <!-- User Tasks View -->
      <div v-else-if="activeTab === 'user' && !showMitigationWorkflow && !showReviewerWorkflow">
        <div v-if="!selectedUserId" class="no-data-state">
          <p>Please select a user to view their assigned tasks.</p>
        </div>
        <div v-else-if="userIncidents.length === 0" class="no-data-state">
          <p>No tasks assigned to this user.</p>
        </div>
        <div v-else>
          <CollapsibleTable
            v-for="section in userTaskSections"
            :key="section.name"
            :section-config="section"
            :table-headers="userTaskTableHeaders"
            :is-expanded="expandedSections[section.statusKey]"
            @toggle="toggleSection(section.statusKey)"
            @taskClick="handleUserTaskClick"
          />
        </div>
      </div>

      <!-- Reviewer Tasks View -->
      <div v-else-if="activeTab === 'reviewer' && !showMitigationWorkflow && !showReviewerWorkflow">
        <div v-if="!selectedUserId" class="no-data-state">
          <p>Please select a user to view their reviewer tasks.</p>
        </div>
        <div v-else-if="reviewerTasks.length === 0" class="no-data-state">
          <p>No review tasks assigned to this user.</p>
        </div>
        <div v-else>
          <CollapsibleTable
            v-for="section in reviewerTaskSections"
            :key="section.name"
            :section-config="section"
            :table-headers="reviewerTaskTableHeaders"
            :is-expanded="expandedSections[section.statusKey]"
            @toggle="toggleSection(section.statusKey)"
            @taskClick="handleReviewerTaskClick"
          />
        </div>
      </div>
    </div>

    <!-- Incident Mitigation Workflow -->
    <div v-if="showMitigationWorkflow" class="workflow-overlay">
      <div class="workflow-container">
        <!-- Back Button -->
        <div class="workflow-header">
          <button @click="closeMitigationModal" class="back-button">
            <i class="fas fa-arrow-left"></i>
            Back to Tasks
          </button>
          <h2>{{ isAuditFinding ? 'Audit Finding' : 'Incident' }} Mitigation Workflow</h2>
        </div>

        <!-- Rejection Banner -->
        <div v-if="isIncidentRejected" class="rejection-banner">
          <div class="rejection-content">
            <div class="rejection-icon">⚠️</div>
            <div class="rejection-text">
              <h3>This incident has been rejected and requires resubmission</h3>
              <p>The reviewer has rejected your submission. Please review the feedback below, update the required information, and resubmit for review.</p>
            </div>
          </div>
        </div>

        <!-- Loading State -->
        <div v-if="loadingMitigations" class="loading-state">
          <div class="spinner"></div>
          <span>Loading mitigation steps...</span>
        </div>

        <!-- No Data State -->
        <div v-else-if="!mitigationSteps.length" class="no-data-state">
          No mitigation steps found for this incident.
        </div>

        <!-- Workflow Steps -->
        <div v-else class="workflow-steps">
          <!-- Steps List Navigation -->
          <div class="steps-list-navigation">
            <div 
              v-for="(step, index) in mitigationSteps" 
              :key="index"
              :class="['step-list-item', { 
                active: currentStep === index,
                completed: step.status === 'Completed',
                approved: step.approved === true,
                rejected: step.approved === false
              }]"
              @click="currentStep = index"
            >
              <span class="step-list-number">{{ index + 1 }}.</span>
              <span class="step-list-title">{{ step.description }}</span>
              <span v-if="step.status === 'Completed' || step.approved === true" class="step-complete-mark">
                <i class="fas fa-check-circle"></i>
              </span>
            </div>
            
            <!-- Questionnaire Step -->
            <div 
              v-if="allStepsCompleted"
              :class="['step-list-item', { active: currentStep === mitigationSteps.length }]"
              @click="currentStep = mitigationSteps.length"
            >
              <span class="step-list-number">{{ mitigationSteps.length + 1 }}.</span>
              <span class="step-list-title">Assessment Questionnaire</span>
            </div>
          </div>

          <!-- Step Content -->
          <div class="step-content">
            <!-- Mitigation Step Content -->
            <div v-if="currentStep < mitigationSteps.length" class="mitigation-step-content">
              <div class="step-header">
                <h3>Step {{ currentStep + 1 }}: {{ mitigationSteps[currentStep].description }}</h3>
                <div class="step-status-indicator">
                  <span v-if="mitigationSteps[currentStep].approved === true" class="status-approved">
                    <i class="fas fa-check-circle"></i> Approved
                  </span>
                  <span v-else-if="mitigationSteps[currentStep].approved === false" class="status-rejected">
                    <i class="fas fa-times-circle"></i> Rejected
                  </span>
                  <span v-else-if="mitigationSteps[currentStep].status === 'Completed'" class="status-pending">
                    <i class="fas fa-clock"></i> Pending Review
                  </span>
                  <span v-else class="status-not-started">
                    <i class="fas fa-circle"></i> Not Started
                  </span>
                </div>
              </div>

              <!-- Approval Status Display -->
              <div v-if="mitigationSteps[currentStep].approved === true" class="approval-status">
                <div class="approval-message">
                  <i class="fas fa-lock"></i>
                  This step has been approved by the reviewer and is locked for editing
                </div>
                <div v-if="mitigationSteps[currentStep].comments" class="comments-display">
                  <h4>Comments</h4>
                  <p>{{ mitigationSteps[currentStep].comments }}</p>
                </div>
                <div v-if="mitigationSteps[currentStep].fileName || (mitigationSteps[currentStep].files && mitigationSteps[currentStep].files.length > 0)" class="file-display">
                  <h4>Evidence</h4>
                  <!-- Multiple files display (preferred) -->
                  <div v-if="mitigationSteps[currentStep].files && mitigationSteps[currentStep].files.length > 0" class="evidence-files-list">
                    <div v-for="(file, fileIndex) in mitigationSteps[currentStep].files" :key="fileIndex" class="evidence-file">
                      <!-- Linked Evidence (with documents support) -->
                      <div v-if="file.type === 'linked_evidence'" class="linked-evidence-item">
                        <i class="fas fa-link"></i>
                        <div class="linked-evidence-details">
                          <div class="evidence-title">{{ file.fileName }}</div>
                          <div class="evidence-source">Source: {{ file.linkedEvent?.source || 'Unknown' }}</div>
                          <div class="evidence-meta">
                            <span v-if="file.linkedEvent?.framework">{{ file.linkedEvent.framework }}</span>
                            <span v-if="file.linkedEvent?.status" class="evidence-status">Status: {{ file.linkedEvent.status }}</span>
                            <span v-if="file.linkedEvent?.document_count > 0" class="document-count">{{ file.linkedEvent.document_count }} Document(s)</span>
                          </div>
                          <div v-if="file.linkedEvent?.description" class="evidence-description">
                            {{ file.linkedEvent.description.length > 100 ? file.linkedEvent.description.substring(0, 100) + '...' : file.linkedEvent.description }}
                          </div>
                          
                          <!-- Documents Section -->
                          <div v-if="file.linkedEvent?.documents && file.linkedEvent.documents.length > 0" class="linked-documents">
                            <h4>Attached Documents:</h4>
                            <div class="document-list">
                              <div v-for="(document, docIndex) in file.linkedEvent.documents" :key="docIndex" class="document-item">
                                <div class="document-info">
                                  <i class="fas fa-file-alt document-icon"></i>
                                  <div class="document-details">
                                    <span class="document-name">{{ document.filename }}</span>
                                    <span class="document-source">{{ document.source }}</span>
                                    <span v-if="document.file_size" class="document-size">({{ formatFileSize(document.file_size) }})</span>
                                  </div>
                                </div>
                                <div class="document-actions">
                                  <button v-if="document.downloadable" @click.stop="downloadLinkedDocument(file.linkedEvent.id, docIndex, document)" class="download-btn" title="Download Document">
                                    <i class="fas fa-download"></i>
                                  </button>
                                  <span v-else class="not-downloadable" title="Document not available for download">
                                    <i class="fas fa-ban"></i>
                                  </span>
                                </div>
                              </div>
                            </div>
                          </div>
                          
                          <div class="evidence-actions">
                            <button @click="showLinkedEventDetails(file.linkedEvent)" class="view-details-btn">
                              <i class="fas fa-info-circle"></i> View Details
                            </button>
                            <button v-if="file.linkedEvent?.documents && file.linkedEvent.documents.length > 0" @click="refreshLinkedEvidence()" class="refresh-docs-btn" title="Refresh Documents">
                              <i class="fas fa-sync-alt"></i> Refresh Docs
                            </button>
                          </div>
                        </div>
                        <span class="linked-evidence-badge">Linked Event</span>
                      </div>
                      
                      <!-- Regular File (downloadable) -->
                      <a
                        v-else-if="safeEvidenceUrl(file['aws-file_link'])"
                        :href="safeEvidenceUrl(file['aws-file_link'])"
                        :download="file.fileName"
                        target="_blank"
                        rel="noopener noreferrer"
                        class="downloadable-file"
                      >
                        <i class="fas fa-download"></i> {{ file.fileName }}
                        <span v-if="file.size" class="file-size">({{ formatFileSize(file.size) }})</span>
                        <span v-if="file.upload_type === 's3'" class="s3-indicator" title="Stored in S3">
                          <i class="fas fa-cloud"></i>
                        </span>
                      </a>
                      <span v-else class="downloadable-file downloadable-file--blocked">
                        <i class="fas fa-ban"></i> Blocked untrusted evidence URL
                      </span>
                    </div>
                  </div>
                  <!-- Legacy single file display (fallback when no files array) -->
                  <div v-else-if="mitigationSteps[currentStep].fileName && mitigationSteps[currentStep]['aws-file_link']" class="evidence-file">
                    <!-- Check if it's a linked event (placeholder URL) -->
                    <div v-if="mitigationSteps[currentStep]['aws-file_link'].startsWith('#linked-event-')" class="linked-evidence-item" @click="showLinkedEventDetailsFromStep(currentStep)" role="button" tabindex="0">
                      <i class="fas fa-link"></i>
                      <div class="linked-evidence-details">
                        <div class="evidence-title">{{ mitigationSteps[currentStep].fileName }}</div>
                        <div class="evidence-source">Source: Linked Event</div>
                        <div class="evidence-meta">
                          <span>Click to view details</span>
                        </div>
                      </div>
                      <span class="linked-evidence-badge">Linked Event</span>
                    </div>
                    
                    <!-- Regular downloadable file -->
                    <a
                      v-else-if="safeEvidenceUrl(mitigationSteps[currentStep]['aws-file_link'])"
                      :href="safeEvidenceUrl(mitigationSteps[currentStep]['aws-file_link'])"
                      :download="mitigationSteps[currentStep].fileName"
                      target="_blank"
                      rel="noopener noreferrer"
                      class="downloadable-file"
                    >
                      <i class="fas fa-download"></i> {{ mitigationSteps[currentStep].fileName }}
                    </a>
                    <span v-else class="downloadable-file downloadable-file--blocked">
                      <i class="fas fa-ban"></i> Blocked untrusted evidence URL
                    </span>
                  </div>
                </div>
              </div>

              <!-- Rejection Status Display -->
              <div v-else-if="mitigationSteps[currentStep].approved === false" class="rejection-status">
                <div class="rejection-message">
                  <i class="fas fa-exclamation-triangle"></i>
                  This step was rejected by the reviewer and needs to be updated
                </div>
                <div v-if="mitigationSteps[currentStep].remarks" class="rejection-feedback">
                  <h4>Reviewer Feedback</h4>
                  <p>{{ mitigationSteps[currentStep].remarks }}</p>
                </div>
              </div>

              <!-- Step Input Form -->
              <div v-if="mitigationSteps[currentStep].approved === false || mitigationSteps[currentStep].approved === null" class="step-form">
                <!-- Previous Comments -->
                <div v-if="mitigationSteps[currentStep].previousComments && mitigationSteps[currentStep].previousComments.trim()" class="previous-comments">
                  <h4>Previous Comments</h4>
                  <div class="previous-comments-content">
                    {{ mitigationSteps[currentStep].previousComments }}
                  </div>
                </div>

                <!-- Comments Input -->
                <div class="form-group">
                  <label for="comments">
                    {{ mitigationSteps[currentStep].previousComments && mitigationSteps[currentStep].previousComments.trim() ? 'Add New Comments:' : 'Comments:' }}
                  </label>
                  <textarea 
                    id="comments" 
                    v-model="mitigationSteps[currentStep].comments" 
                    :placeholder="mitigationSteps[currentStep].previousComments && mitigationSteps[currentStep].previousComments.trim() ? 'Add additional comments about this mitigation step...' : 'Add your comments about this mitigation step...'"
                    rows="4"
                  ></textarea>
                </div>

                <!-- Evidence Attachment Section -->
                <div class="form-group evidence-section">
                  <div class="evidence-header">
                    <h4>Evidence Documents</h4>
                    <p class="evidence-instruction">Upload supporting documents for this mitigation step</p>
                  </div>
                  
                  <!-- Current Evidence Display -->
                  <div v-if="mitigationSteps[currentStep].files && mitigationSteps[currentStep].files.length > 0" class="current-evidence">
                    <h5>Current Documents ({{ mitigationSteps[currentStep].files.length }})</h5>
                    <div class="evidence-files-list">
                      <div v-for="(file, fileIndex) in mitigationSteps[currentStep].files" :key="fileIndex" class="evidence-file-item">
                        <div class="file-info">
                          <i class="fas fa-file-alt file-icon"></i>
                          <div class="file-details">
                            <div class="file-name">{{ file.fileName }}</div>
                            <div class="file-size" v-if="file.size">{{ formatFileSize(file.size) }}</div>
                          </div>
                        </div>
                        <div class="file-actions">
                          <a
                            v-if="safeEvidenceUrl(file['aws-file_link'])"
                            :href="safeEvidenceUrl(file['aws-file_link'])"
                            target="_blank"
                            class="view-file-btn"
                            rel="noopener noreferrer"
                            title="View File"
                          >
                            <i class="fas fa-eye"></i> View
                          </a>
                          <span v-else class="view-file-btn view-file-btn--blocked" title="Blocked untrusted URL">
                            <i class="fas fa-ban"></i> Blocked
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <!-- Upload New Evidence -->
                  <div class="upload-evidence">
                    <h5>Upload New Evidence</h5>
                    <EvidenceAttachment 
                      :incident-id="selectedIncidentId"
                      :user-id="selectedUserId"
                      @filesUploaded="handleFilesUploaded"
                    />
                  </div>
                </div>

                <!-- Complete Button -->
                <div class="form-actions">
                  <button 
                    @click="updateStepStatus(currentStep, 'Completed')" 
                    class="complete-button"
                    :class="{ active: mitigationSteps[currentStep].status === 'Completed' }"
                  >
                    <i class="fas fa-check"></i> Mark as Complete
                  </button>
                </div>
              </div>
            </div>

            <!-- Questionnaire Content -->
            <div v-else-if="currentStep === mitigationSteps.length && allStepsCompleted" class="questionnaire-content">
              <div class="questionnaire-header">
                <h3>Incident Assessment Questionnaire</h3>
                <p>Please complete the assessment questionnaire to finalize your submission.</p>
              </div>

              <div class="questionnaire-form">
                <!-- Question 1: Cost -->
                <div class="question-group">
                  <label class="question-label">
                    <span class="question-number">1</span>
                    What is the total cost for implementing this mitigation? (Optional)
                  </label>
                  <div class="input-with-prefix">
                    <span class="currency-prefix">$</span>
                    <input 
                      type="number" 
                      v-model="questionnaireData.cost" 
                      placeholder="Enter amount (e.g., 5000.50)"
                      class="question-input currency-input"
                      min="0"
                      step="0.01"
                      @input="validateCurrencyInput('cost', $event)"
                    />
                  </div>
                  <small class="field-hint">Include labor, materials, technology, and any third-party costs</small>
                </div>

                <!-- Question 2: Impact -->
                <div class="question-group">
                  <label class="question-label">
                    <span class="question-number">2</span>
                    What is the overall impact level of this incident? (Optional)
                  </label>
                  <select v-model="questionnaireData.impact" class="question-select">
                    <option value="">Select impact level...</option>
                    <option value="Very Low">Very Low - Minimal disruption, easily contained</option>
                    <option value="Low">Low - Minor disruption, limited scope</option>
                    <option value="Medium">Medium - Moderate disruption, manageable impact</option>
                    <option value="High">High - Significant disruption, widespread impact</option>
                    <option value="Very High">Very High - Severe disruption, critical impact</option>
                  </select>
                  <small class="field-hint">Consider operational, business, and stakeholder impact</small>
                </div>

                <!-- Question 3: Financial Impact -->
                <div class="question-group">
                  <label class="question-label">
                    <span class="question-number">3</span>
                    What is the financial impact scale of this incident? (Optional)
                  </label>
                  <select v-model="questionnaireData.financialImpact" class="question-select">
                    <option value="">Select financial impact level...</option>
                    <option value="Very Low">Very Low - Under $1,000 in losses/costs</option>
                    <option value="Low">Low - $1,000 - $10,000 in losses/costs</option>
                    <option value="Medium">Medium - $10,000 - $100,000 in losses/costs</option>
                    <option value="High">High - $100,000 - $1,000,000 in losses/costs</option>
                    <option value="Very High">Very High - Over $1,000,000 in losses/costs</option>
                  </select>
                  <small class="field-hint">Include direct losses, opportunity costs, and recovery expenses</small>
                </div>

                <!-- Question 4: Reputational Impact -->
                <div class="question-group">
                  <label class="question-label">
                    <span class="question-number">4</span>
                    What is the reputational impact scale of this incident? (Optional)
                  </label>
                  <select v-model="questionnaireData.reputationalImpact" class="question-select">
                    <option value="">Select reputational impact level...</option>
                    <option value="Very Low">Very Low - Minimal or no reputational damage</option>
                    <option value="Low">Low - Minor reputational concerns, limited visibility</option>
                    <option value="Medium">Medium - Moderate reputational impact, some stakeholder concern</option>
                    <option value="High">High - Significant reputational damage, widespread attention</option>
                    <option value="Very High">Very High - Severe reputational crisis, major media coverage</option>
                  </select>
                  <small class="field-hint">Consider impact on brand, customer trust, media coverage, and stakeholder confidence</small>
                </div>

                <!-- Question 5: Operational Impact -->
                <div class="question-group">
                  <label class="question-label">
                    <span class="question-number">5</span>
                    What is the operational impact scale of this incident? (Optional)
                  </label>
                  <select v-model="questionnaireData.operationalImpact" class="question-select">
                    <option value="">Select operational impact level...</option>
                    <option value="Very Low">Very Low - Minimal disruption, normal operations maintained</option>
                    <option value="Low">Low - Minor disruption, limited service impact</option>
                    <option value="Medium">Medium - Moderate disruption, some services affected</option>
                    <option value="High">High - Significant disruption, major service interruption</option>
                    <option value="Very High">Very High - Severe disruption, critical systems down</option>
                  </select>
                  <small class="field-hint">Consider disruptions to processes, services, productivity, and normal operations</small>
                </div>

                <!-- Question 6: Financial Loss -->
                <div class="question-group">
                  <label class="question-label">
                    <span class="question-number">6</span>
                    What is the estimated financial loss from this incident? (Optional)
                  </label>
                  <div class="input-with-prefix">
                    <span class="currency-prefix">$</span>
                    <input 
                      type="number" 
                      v-model="questionnaireData.financialLoss" 
                      placeholder="Enter total loss amount (e.g., 25000.00)"
                      class="question-input currency-input"
                      min="0"
                      step="0.01"
                      @input="validateCurrencyInput('financialLoss', $event)"
                    />
                  </div>
                  <small class="field-hint">Include revenue loss, regulatory fines, penalties, legal costs, and recovery expenses</small>
                </div>

                <!-- Question 7: System Downtime -->
                <div class="question-group">
                  <label class="question-label">
                    <span class="question-number">7</span>
                    What is the expected system downtime if this incident occurs again? (Optional)
                  </label>
                  <div class="input-with-suffix">
                    <input 
                      type="number" 
                      v-model="questionnaireData.systemDowntime" 
                      placeholder="Enter hours (e.g., 8.5)"
                      class="question-input hours-input"
                      min="0"
                      step="0.5"
                      @input="validateHoursInput('systemDowntime', $event)"
                    />
                    <span class="hours-suffix">hours</span>
                  </div>
                  <small class="field-hint">Estimate total time systems/services would be unavailable (decimals allowed, e.g., 2.5 hours)</small>
                </div>

                <!-- Question 8: Recovery Time -->
                <div class="question-group">
                  <label class="question-label">
                    <span class="question-number">8</span>
                    How long did it take to recover from this incident? (Optional)
                  </label>
                  <div class="input-with-suffix">
                    <input 
                      type="number" 
                      v-model="questionnaireData.recoveryTime" 
                      placeholder="Enter hours (e.g., 12.0)"
                      class="question-input hours-input"
                      min="0"
                      step="0.5"
                      @input="validateHoursInput('recoveryTime', $event)"
                    />
                    <span class="hours-suffix">hours</span>
                  </div>
                  <small class="field-hint">Time from incident detection to complete restoration of normal operations (decimals allowed)</small>
                </div>

                <!-- Question 9: Risk Recurrence -->
                <div class="question-group">
                  <label class="question-label">
                    <span class="question-number">9</span>
                    Is it possible that this incident will recur again? (Optional)
                  </label>
                  <select v-model="questionnaireData.riskRecurrence" class="question-select">
                    <option value="">Select likelihood...</option>
                    <option value="yes">Yes - High likelihood of recurrence</option>
                    <option value="maybe">Maybe - Possible but uncertain recurrence</option>
                    <option value="no">No - Very unlikely to recur</option>
                  </select>
                  <small class="field-hint">Consider if root causes have been addressed and preventive measures are in place</small>
                </div>

                <!-- Question 10: Improvement Initiative -->
                <div class="question-group">
                  <label class="question-label">
                    <span class="question-number">10</span>
                    Is this mitigation an improvement initiative that will prevent future recurrence? (Optional)
                  </label>
                  <select v-model="questionnaireData.improvementInitiative" class="question-select">
                    <option value="">Select prevention level...</option>
                    <option value="yes">Yes - Completely prevents recurrence</option>
                    <option value="partially">Partially - Reduces likelihood of recurrence</option>
                    <option value="no">No - Does not prevent recurrence</option>
                  </select>
                  <small class="field-hint">Assess whether this mitigation addresses root causes and prevents similar incidents</small>
                </div>
              </div>

              <div class="questionnaire-actions">
                <button @click="closeMitigationModal" class="cancel-button">
                  <i class="fas fa-times"></i> Cancel
                </button>
                <button 
                  @click="submitIncidentAssessment" 
                  class="submit-button"
                  :disabled="!isQuestionnaireValid"
                >
                  <i class="fas fa-check-circle"></i> Submit Assessment
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Reviewer Workflow -->
    <div v-if="showReviewerWorkflow" class="workflow-overlay">
      <div class="workflow-container">
        <!-- Back Button -->
        <div class="workflow-header">
          <button @click="closeReviewerModal" class="back-button">
            <i class="fas fa-arrow-left"></i>
            Back to Tasks
          </button>
          <h2>Review Incident Mitigations</h2>
        </div>

        <!-- Loading State -->
        <div v-if="loadingMitigations" class="loading-state">
          <div class="spinner"></div>
          <span>Loading mitigation data...</span>
        </div>

        <!-- Reviewer Content -->
        <div v-else class="reviewer-content">
          <div class="incident-summary">
            <h3>{{ currentReviewTask?.Title || 'Incident #' + currentReviewTask?.id }}</h3>
            <p><strong>ID:</strong> {{ currentReviewTask?.id }}</p>
            <p><strong>Submitted By:</strong> {{ getUserName(currentReviewTask?.AssignerId) }}</p>
          </div>

          <!-- Questionnaire Review -->
          <div v-if="questionnaireReviewData" class="questionnaire-review">
            <h3>Assessment Questionnaire</h3>
            <div class="questionnaire-grid">
              <div class="questionnaire-item" v-if="questionnaireReviewData.cost">
                <label>Cost for Mitigation:</label>
                <p>{{ questionnaireReviewData.cost }}</p>
              </div>
              
              <div class="questionnaire-item" v-if="questionnaireReviewData.impact">
                <label>Impact:</label>
                <p>{{ questionnaireReviewData.impact }}</p>
              </div>
              
              <div class="questionnaire-item" v-if="questionnaireReviewData.financialImpact">
                <label>Financial Impact:</label>
                <p>{{ questionnaireReviewData.financialImpact }}</p>
              </div>
              
              <div class="questionnaire-item" v-if="questionnaireReviewData.reputationalImpact">
                <label>Reputational Impact Scale:</label>
                <p>{{ questionnaireReviewData.reputationalImpact }}</p>
              </div>
              
              <div class="questionnaire-item" v-if="questionnaireReviewData.operationalImpact">
                <label>Operational Impact Scale:</label>
                <p>{{ questionnaireReviewData.operationalImpact }}</p>
              </div>
              
              <div class="questionnaire-item" v-if="questionnaireReviewData.financialLoss">
                <label>Financial Loss:</label>
                <p>{{ questionnaireReviewData.financialLoss }}</p>
              </div>
              
              <div class="questionnaire-item" v-if="questionnaireReviewData.systemDowntime">
                <label>Expected System Downtime (hrs):</label>
                <p>{{ questionnaireReviewData.systemDowntime }}</p>
              </div>
              
              <div class="questionnaire-item" v-if="questionnaireReviewData.recoveryTime">
                <label>Recovery Time (hrs):</label>
                <p>{{ questionnaireReviewData.recoveryTime }}</p>
              </div>
              
              <div class="questionnaire-item" v-if="questionnaireReviewData.riskRecurrence">
                <label>Risk Recurrence Possibility:</label>
                <p>{{ questionnaireReviewData.riskRecurrence }}</p>
              </div>
              
              <div class="questionnaire-item" v-if="questionnaireReviewData.improvementInitiative">
                <label>Improvement Initiative:</label>
                <p>{{ questionnaireReviewData.improvementInitiative }}</p>
              </div>
              
              <div class="questionnaire-item" v-if="questionnaireReviewData.submittedAt">
                <label>Submitted At:</label>
                <p>{{ formatDateTime(questionnaireReviewData.submittedAt) }}</p>
              </div>
            </div>

            <!-- Assessment Approval -->
            <div v-if="!reviewCompleted" class="assessment-approval">
              <h4>Assessment Review</h4>
              <div class="approval-controls">
                <button 
                  @click="approveAssessment(true)" 
                  class="approve-button"
                  :class="{ active: assessmentFeedback.approved === true }"
                >
                  <i class="fas fa-check-circle"></i> Approve Assessment
                </button>
                <button 
                  @click="approveAssessment(false)" 
                  class="reject-button"
                  :class="{ active: assessmentFeedback.approved === false }"
                >
                  <i class="fas fa-times-circle"></i> Reject Assessment
                </button>
              </div>
              
              <div v-if="assessmentFeedback.approved === false" class="feedback-section">
                <label for="assessment-feedback">Assessment Feedback (required for rejection):</label>
                <textarea 
                  id="assessment-feedback"
                  v-model="assessmentFeedback.remarks" 
                  placeholder="Provide detailed feedback about why the assessment was rejected..."
                  rows="4"
                ></textarea>
              </div>
            </div>
          </div>

          <!-- Mitigation Review -->
          <div class="mitigation-review">
            <h3>Mitigation Review</h3>
            <div class="mitigation-list">
              <div 
                v-for="(mitigation, id) in mitigationReviewData" 
                :key="id" 
                class="mitigation-item"
              >
                <div class="mitigation-header">
                  <h4>Mitigation #{{ id }}</h4>
                  <div class="mitigation-status" :class="{ 
                    approved: mitigation.approved === true, 
                    rejected: mitigation.approved === false,
                    pending: mitigation.approved === undefined
                  }">
                    <i class="fas" :class="{
                      'fa-check-circle': mitigation.approved === true,
                      'fa-times-circle': mitigation.approved === false,
                      'fa-clock': mitigation.approved === undefined
                    }"></i>
                    {{ mitigation.approved === true ? 'Approved' : 
                       mitigation.approved === false ? 'Rejected' : 'Pending Review' }}
                  </div>
                </div>
                
                <div class="mitigation-content">
                  <div class="mitigation-description">
                    <h5>Description</h5>
                    <p>{{ mitigation.description }}</p>
                  </div>
                  
                  <div v-if="mitigation.comments" class="mitigation-comments">
                    <h5>User Comments</h5>
                    <p>{{ mitigation.comments }}</p>
                  </div>
                  
                  <div v-if="mitigation['aws-file_link'] || (mitigation.files && mitigation.files.length > 0)" class="mitigation-evidence">
                    <h5>Evidence</h5>
                    <!-- Multiple files display (preferred) -->
                    <div v-if="mitigation.files && mitigation.files.length > 0" class="evidence-files-list">
                      <div v-for="(file, fileIndex) in mitigation.files" :key="fileIndex" class="evidence-file">
                        <!-- Linked Evidence (with documents support) -->
                        <div v-if="file.type === 'linked_evidence'" class="linked-evidence-item">
                          <i class="fas fa-link"></i>
                          <div class="linked-evidence-details">
                            <div class="evidence-title">{{ file.fileName }}</div>
                            <div class="evidence-source">Source: {{ file.linkedEvent?.source || 'Unknown' }}</div>
                            <div class="evidence-meta">
                              <span v-if="file.linkedEvent?.framework">{{ file.linkedEvent.framework }}</span>
                              <span v-if="file.linkedEvent?.status" class="evidence-status">Status: {{ file.linkedEvent.status }}</span>
                              <span v-if="file.linkedEvent?.document_count > 0" class="document-count">{{ file.linkedEvent.document_count }} Document(s)</span>
                            </div>
                            <div v-if="file.linkedEvent?.description" class="evidence-description">
                              {{ file.linkedEvent.description.length > 100 ? file.linkedEvent.description.substring(0, 100) + '...' : file.linkedEvent.description }}
                            </div>
                            
                            <!-- Documents Section -->
                            <div v-if="file.linkedEvent?.documents && file.linkedEvent.documents.length > 0" class="linked-documents">
                              <h4>Attached Documents:</h4>
                              <div class="document-list">
                                <div v-for="(document, docIndex) in file.linkedEvent.documents" :key="docIndex" class="document-item">
                                  <div class="document-info">
                                    <i class="fas fa-file-alt document-icon"></i>
                                    <div class="document-details">
                                      <span class="document-name">{{ document.filename }}</span>
                                      <span class="document-source">{{ document.source }}</span>
                                      <span v-if="document.file_size" class="document-size">({{ formatFileSize(document.file_size) }})</span>
                                    </div>
                                  </div>
                                  <div class="document-actions">
                                    <button v-if="document.downloadable" @click.stop="downloadLinkedDocument(file.linkedEvent.id, docIndex, document)" class="download-btn" title="Download Document">
                                      <i class="fas fa-download"></i>
                                    </button>
                                    <span v-else class="not-downloadable" title="Document not available for download">
                                      <i class="fas fa-ban"></i>
                                    </span>
                                  </div>
                                </div>
                              </div>
                            </div>
                            
                            <div class="evidence-actions">
                              <button @click="showLinkedEventDetails(file.linkedEvent)" class="view-details-btn">
                                <i class="fas fa-info-circle"></i> View Details
                              </button>
                              <button v-if="file.linkedEvent?.documents && file.linkedEvent.documents.length > 0" @click="refreshLinkedEvidence()" class="refresh-docs-btn" title="Refresh Documents">
                                <i class="fas fa-sync-alt"></i> Refresh Docs
                              </button>
                            </div>
                          </div>
                          <span class="linked-evidence-badge">Linked Event</span>
                        </div>
                        
                        <!-- Regular File (downloadable) -->
                        <a
                          v-else-if="safeEvidenceUrl(file['aws-file_link'])"
                          :href="safeEvidenceUrl(file['aws-file_link'])"
                          download
                          :filename="file.fileName"
                          class="evidence-link"
                        >
                          <i class="fas fa-download"></i> {{ file.fileName }}
                          <span v-if="file.size" class="file-size">({{ formatFileSize(file.size) }})</span>
                          <span v-if="file.upload_type === 's3'" class="s3-indicator" title="Stored in S3">
                            <i class="fas fa-cloud"></i>
                          </span>
                        </a>
                        <span v-else class="evidence-link evidence-link--blocked">
                          <i class="fas fa-ban"></i> Blocked untrusted evidence URL
                        </span>
                      </div>
                    </div>
                    <!-- Legacy single file display (fallback when no files array) -->
                    <div v-else-if="mitigation['aws-file_link'] && mitigation.fileName" class="evidence-file">
                      <!-- Check if it's a linked event (placeholder URL) -->
                      <div v-if="mitigation['aws-file_link'].startsWith('#linked-event-')" class="linked-evidence-item" @click="showLinkedEventDetailsFromMitigation(mitigation)" role="button" tabindex="0">
                        <i class="fas fa-link"></i>
                        <div class="linked-evidence-details">
                          <div class="evidence-title">{{ mitigation.fileName }}</div>
                          <div class="evidence-source">Source: Linked Event</div>
                          <div class="evidence-meta">
                            <span>Click to view details</span>
                          </div>
                        </div>
                        <span class="linked-evidence-badge">Linked Event</span>
                      </div>
                      
                      <!-- Regular downloadable file -->
                      <a
                        v-else-if="safeEvidenceUrl(mitigation['aws-file_link'])"
                        :href="safeEvidenceUrl(mitigation['aws-file_link'])"
                        download
                        :filename="mitigation.fileName"
                        class="evidence-link"
                      >
                        <i class="fas fa-download"></i> {{ mitigation.fileName }}
                      </a>
                      <span v-else class="evidence-link evidence-link--blocked">
                        <i class="fas fa-ban"></i> Blocked untrusted evidence URL
                      </span>
                    </div>
                  </div>
                </div>
                
                <div class="mitigation-actions">
                  <div v-if="mitigation.approved !== true && mitigation.approved !== false && !reviewCompleted" class="approval-buttons">
                    <button @click="approveMitigation(id, true)" class="approve-button">
                      <i class="fas fa-check-double"></i> Approve
                    </button>
                    <button @click="approveMitigation(id, false)" class="reject-button">
                      <i class="fas fa-ban"></i> Reject
                    </button>
                  </div>
                  
                  <div v-if="mitigation.approved === false && !reviewCompleted" class="feedback-section">
                    <label for="remarks">Feedback (required for rejection):</label>
                    <textarea 
                      id="remarks" 
                      v-model="mitigation.remarks" 
                      placeholder="Provide feedback explaining why this mitigation was rejected..."
                    ></textarea>
                    <button @click="updateRemarks(id)" class="save-button">
                      <i class="fas fa-save"></i> Save Feedback
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Review Actions -->
          <div class="review-actions">
            <button 
              class="submit-review-button" 
              :disabled="!canSubmitReview || reviewCompleted" 
              @click="submitReview(true)"
            >
              <i class="fas fa-check-double"></i> Approve Incident
            </button>
            <button 
              class="reject-review-button" 
              :disabled="!canSubmitReview || reviewCompleted" 
              @click="submitReview(false)"
            >
              <i class="fas fa-ban"></i> Reject Incident
            </button>
            
            <div v-if="reviewCompleted" class="review-complete">
              This review has been completed
            </div>
            
            <div v-else-if="!canSubmitReview" class="review-warning">
              <i class="fas fa-exclamation-circle"></i>
              You must approve or reject each mitigation and the assessment before submitting
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Popup Modal -->
    <PopupModal />
  </div>
</template>

<script>
import apiService from '@/services/apiService.js';
import { API_ENDPOINTS, API_BASE_URL } from '../../config/api.js';
import { PopupService, PopupModal } from '@/modules/popup';
import CustomDropdown from '@/components/CustomDropdown.vue';
import CollapsibleTable from '@/components/CollapsibleTable.vue';
import EvidenceAttachment from '@/components/EventHandling/EvidenceAttachment.vue';
import incidentService from '../../services/incidentService.js';
import { safeEvidenceUrl } from '@/utils/trustedEvidenceUrl';
import { getExplicitFrameworkId } from '@/utils/frameworkContextStorage.js';
import './IncidentUserTask.css'; // Import the CSS file

export default {
  name: 'IncidentUserTasks',
  components: {
    PopupModal,
    CustomDropdown,
    CollapsibleTable,
    EvidenceAttachment
  },
  data() {
    return {
      // Add incidentService to data so it's available in methods
      incidentService,
      userIncidents: [],
      reviewerTasks: [],
      users: [],
      selectedUserId: '',
      selectedFramework: '',
      userFilterConfig: {
        name: 'User',
        label: 'User',
        defaultLabel: 'All Users',
        values: []
      },
      loading: true,
      error: null,
      showMitigationWorkflow: false,
      showReviewerWorkflow: false,
      loadingMitigations: false,
      mitigationSteps: [],
      selectedIncidentId: null,
      activeTab: 'user',
      mitigationReviewData: {},
      currentReviewTask: null,
      reviewCompleted: false,
      reviewApproved: false,
      previousVersions: {},
      showQuestionnaire: false,
      questionnaireReviewData: {},
      assessmentFeedback: {},
      assessmentFeedbackForUser: null,
      questionnaireData: {
        cost: '',
        impact: '',
        financialImpact: '',
        reputationalImpact: '',
        operationalImpact: '',
        financialLoss: '',
        systemDowntime: '',
        recoveryTime: '',
        riskRecurrence: '',
        improvementInitiative: ''
      },
      expandedSections: {
        approved: true,
        rejected: true,
        pendingReview: true,
        assigned: true,
        reviewerPending: true,
        reviewerApproved: true
      },
      approvedIncidents: [],
      rejectedIncidents: [],
      pendingReviewIncidents: [],
      assignedIncidents: [],
      pendingReviewerTasks: [],
      approvedReviewerTasks: [],
      currentStep: 0
    }
  },
  computed: {
    allStepsCompleted() {
      // Only check rejected or unreviewed steps, ignore approved ones
      const stepsToCheck = this.mitigationSteps.filter(step => step.approved === false || step.approved === null);
      return stepsToCheck.length > 0 && 
             stepsToCheck.every(step => step.status === 'Completed');
    },
    canSubmitReview() {
      const mitigationsValid = Object.values(this.mitigationReviewData).every(m => 
        m.approved === true || (m.approved === false && m.remarks && m.remarks.trim() !== '')
      );
      
      const assessmentValid = this.assessmentFeedback.approved !== undefined && 
        (this.assessmentFeedback.approved === true || 
         (this.assessmentFeedback.approved === false && this.assessmentFeedback.remarks && this.assessmentFeedback.remarks.trim() !== ''));
      
      return mitigationsValid && assessmentValid;
    },
    hasRejectedOrNewSteps() {
      return this.mitigationSteps.some(step => step.approved === false || step.approved === null);
    },
    rejectedStepsCompleted() {
      const rejectedOrNewSteps = this.mitigationSteps.filter(step => step.approved === false || step.approved === null);
      return rejectedOrNewSteps.length > 0 && 
             rejectedOrNewSteps.every(step => step.status === 'Completed');
    },
    isQuestionnaireValid() {
      // All fields are optional, so always return true
      return true;
    },
    isAuditFinding() {
      if (!this.userIncidents || !Array.isArray(this.userIncidents)) return false;
      const task = this.userIncidents.find(t => t.id === this.selectedIncidentId);
      return task && task.itemType === 'audit_finding';
    },
    isIncidentRejected() {
      if (!this.userIncidents || !Array.isArray(this.userIncidents)) return false;
      const task = this.userIncidents.find(t => t.id === this.selectedIncidentId);
      return task && task.Status === 'Rejected';
    },
    currentIncidentDetails() {
      if (!this.userIncidents || !Array.isArray(this.userIncidents)) return {};
      return this.userIncidents.find(t => t.id === this.selectedIncidentId) || {};
    },
    userTaskTableHeaders() {
      return [
        { key: 'id', label: 'ID', sortable: true, width: '8%' },
        { key: 'Title', label: 'Title', sortable: true, width: '30%' },
        { key: 'Origin', label: 'Origin', sortable: true, width: '15%' },
        { key: 'Priority', label: 'Priority', sortable: true, width: '15%' },
        { key: 'MitigationDueDate', label: 'Due Date', sortable: true, width: '15%' },
        { key: 'actions', label: 'Actions', sortable: false, width: '17%' }
      ];
    },
    reviewerTaskTableHeaders() {
      return [
        { key: 'id', label: 'ID', sortable: true, width: '8%' },
        { key: 'Title', label: 'Title', sortable: true, width: '30%' },
        { key: 'Origin', label: 'Origin', sortable: true, width: '15%' },
        { key: 'Priority', label: 'Priority', sortable: true, width: '15%' },
        { key: 'AssignerId', label: 'Assigned By', sortable: true, width: '15%' },
        { key: 'actions', label: 'Actions', sortable: false, width: '17%' }
      ];
    },
    userTaskSections() {
      return [
        {
          name: 'Approved',
          statusKey: 'approved',
          statusClass: 'approved',
          tasks: this.approvedIncidents.map(i => ({ ...i, actions: 'view' }))
        },
        {
          name: 'Rejected',
          statusKey: 'rejected',
          statusClass: 'rejected',
          tasks: this.rejectedIncidents.map(i => ({ ...i, actions: 'resubmit' }))
        },
        {
          name: 'Pending Review',
          statusKey: 'pendingReview',
          statusClass: 'pending-review',
          tasks: this.pendingReviewIncidents.map(i => ({ ...i, actions: 'view' }))
        },
        {
          name: 'Assigned',
          statusKey: 'assigned',
          statusClass: 'assigned',
          tasks: this.assignedIncidents.map(i => ({ ...i, actions: 'view' }))
        }
      ];
    },
    reviewerTaskSections() {
      return [
        {
          name: 'Pending Review',
          statusKey: 'reviewerPending',
          statusClass: 'pending-review',
          tasks: this.pendingReviewerTasks.map(i => ({ ...i, actions: 'review' }))
        },
        {
          name: 'Approved',
          statusKey: 'reviewerApproved',
          statusClass: 'approved',
          tasks: this.approvedReviewerTasks.map(i => ({ ...i, actions: 'view' }))
        }
      ];
    }
  },
    watch: {
    selectedIncidentId(newId, oldId) {
      if (newId && newId !== oldId) {
        this.$nextTick(() => {
          this.fetchLinkedEvidenceDocuments();
        });
      }
    }
  },
  async mounted() {
    console.log('🚀 [IncidentUserTasks] Component mounted');
    
    // Wait for incident data fetch if still in progress
    if (window.incidentDataFetchPromise) {
      console.log('⏳ [IncidentUserTasks] Waiting for incident data fetch...');
      try {
        await window.incidentDataFetchPromise;
        console.log('✅ [IncidentUserTasks] Incident data fetch completed');
      } catch (error) {
        console.warn('⚠️ [IncidentUserTasks] Incident data fetch failed:', error);
      }
    }
    
    // Fetch selected framework from home page first
    await this.fetchSelectedFramework();
    
    // Load users with three-tier fallback pattern
    await this.loadUsers();
    
    this.initializeFromQuery();
    this.setDefaultUser();
    
    // Ensure evidence documents are fetched when component loads
    this.$nextTick(() => {
      if (this.selectedIncidentId) {
        this.fetchLinkedEvidenceDocuments();
      }
    });
  },
  methods: {
    /** Normalize status for bucket matching (cached/API may differ in casing) */
    incidentStatusNorm(s) {
      if (s == null || s === '') return '';
      return String(s).trim().toLowerCase();
    },
    isApprovedStatus(s) {
      return this.incidentStatusNorm(s) === 'approved';
    },
    isRejectedStatus(s) {
      return this.incidentStatusNorm(s) === 'rejected';
    },
    isPendingReviewStatus(s) {
      const n = this.incidentStatusNorm(s);
      return n === 'pending review' || n === 'under review';
    },
    isAssignedBucketStatus(s) {
      return !this.isApprovedStatus(s) && !this.isRejectedStatus(s) && !this.isPendingReviewStatus(s);
    },
    /**
     * When a framework is selected, keep rows that match it OR have no framework field (lenient —
     * backend user_* + framework_id often returns [] while bulk cache has assigner tasks).
     */
    taskMatchesSelectedFramework(task) {
      const fw = this.selectedFramework;
      if (fw === '' || fw == null) return true;
      const want = String(fw);
      const itemFw =
        task.framework_id ??
        task.FrameworkId ??
        (task.Framework && (task.Framework.id ?? task.Framework.Id)) ??
        (task.framework && (task.framework.id ?? task.framework.Id));
      if (itemFw === null || itemFw === undefined || itemFw === '') return true;
      return String(itemFw) === want;
    },
    isReviewerTaskExcludedStatus(s) {
      const n = this.incidentStatusNorm(s);
      return n === 'closed' || n === 'completed' || n === 'cancelled';
    },
    taskMatchesReviewerUser(task, userId) {
      const uid = parseInt(userId, 10);
      if (Number.isNaN(uid)) return false;
      const candidates = [
        task.ReviewerId,
        task.reviewer_id,
        task.Reviewer
      ];
      return candidates.some((v) => {
        if (v === null || v === undefined || v === '') return false;
        const n = parseInt(v, 10);
        return !Number.isNaN(n) && n === uid;
      });
    },
    /**
     * Same rules as backend incident_reviewer_tasks / audit_finding_reviewer_tasks over bulk prefetch cache.
     */
    deriveReviewerTasksFromBulkCache() {
      const uid = this.selectedUserId;
      if (uid == null || uid === '') return [];
      const cachedIncidents = incidentService.getData('incidents') || [];
      const cachedAuditFindings = incidentService.getData('auditFindings') || [];
      const rows = [];
      const seen = new Set();
      const pushRow = (task, itemType) => {
        if (!this.taskMatchesReviewerUser(task, uid)) return;
        if (this.isReviewerTaskExcludedStatus(task.Status)) return;
        const id = task.id || task.IncidentId;
        if (id == null || seen.has(id)) return;
        const shaped = {
          ...task,
          itemType,
          id,
          Title: task.Title || task.IncidentTitle,
          Priority: task.Priority || task.RiskPriority,
          Origin: task.Origin,
          Status: task.Status,
          MitigationDueDate: task.MitigationDueDate,
          AssignerId: task.AssignerId,
          ReviewerId: task.ReviewerId
        };
        if (!this.taskMatchesSelectedFramework(shaped)) return;
        seen.add(id);
        rows.push(shaped);
      };
      if (Array.isArray(cachedIncidents)) cachedIncidents.forEach((t) => pushRow(t, 'incident'));
      if (Array.isArray(cachedAuditFindings)) cachedAuditFindings.forEach((t) => pushRow(t, 'audit_finding'));
      return rows;
    },
    mergeReviewerTaskListsById(apiList, cacheList) {
      const map = new Map();
      const add = (t) => {
        if (!t || t.id == null) return;
        const key = String(t.id);
        if (!map.has(key)) map.set(key, t);
      };
      (apiList || []).forEach(add);
      (cacheList || []).forEach(add);
      return [...map.values()];
    },
    async loadReviewerTasksAsync(params) {
      const parseList = (body) => (Array.isArray(body) ? body : (body?.data || []));
      const toMarked = (items, itemType) =>
        (items || []).map((item) => ({
          ...item,
          itemType,
          id: item.id || item.IncidentId,
          Title: item.Title || item.IncidentTitle,
          Priority: item.Priority || item.RiskPriority
        }));

      const fetchReviewerOnce = async (p) => {
        const [incRes, audRes] = await Promise.all([
          apiService.get(API_ENDPOINTS.INCIDENT_REVIEWER_TASKS(this.selectedUserId), p),
          apiService.get(API_ENDPOINTS.AUDIT_FINDING_REVIEWER_TASKS(this.selectedUserId), p)
        ]);
        const combined = [
          ...toMarked(parseList(incRes), 'incident'),
          ...toMarked(parseList(audRes), 'audit_finding')
        ];
        return combined.filter(
          (task, index, arr) => index === arr.findIndex((t) => t.id === task.id)
        );
      };

      let apiTasks = await fetchReviewerOnce(params || {});
      if (apiTasks.length === 0 && params && params.framework_id) {
        console.warn('⚠️ [IncidentUserTasks] Reviewer API empty with framework_id; retrying without framework (client filter)');
        apiTasks = await fetchReviewerOnce({});
        if (this.selectedFramework) {
          const before = apiTasks.length;
          apiTasks = apiTasks.filter((t) => this.taskMatchesSelectedFramework(t));
          console.log(`🔍 [IncidentUserTasks] Reviewer tasks client framework filter: ${before} → ${apiTasks.length}`);
        }
      }

      const fromCache = this.deriveReviewerTasksFromBulkCache();
      this.reviewerTasks = this.mergeReviewerTaskListsById(apiTasks, fromCache);
      this.approvedReviewerTasks = this.reviewerTasks.filter((task) => this.isApprovedStatus(task.Status));
      this.pendingReviewerTasks = this.reviewerTasks.filter((task) => !this.isApprovedStatus(task.Status));
      this.expandedSections.reviewerPending = true;
      this.expandedSections.reviewerApproved = true;
      console.log(
        `✅ [IncidentUserTasks] Reviewer tasks total: ${this.reviewerTasks.length} (API base ${apiTasks.length}, merged with cache)`
      );
    },
    safeEvidenceUrl,
    async fetchSelectedFramework() {
      try {
        console.log('🔍 Fetching selected framework for incident user tasks...');
        const frameworkBody = await apiService.get(API_ENDPOINTS.FRAMEWORK_GET_SELECTED);
        console.log('Framework response:', frameworkBody);
        
        if (frameworkBody && frameworkBody.frameworkId) {
          const frameworkId = parseInt(frameworkBody.frameworkId);
          // If frameworkId is empty, null, undefined, or 0, set it to empty string (All Frameworks)
          this.selectedFramework = frameworkId || '';
          console.log('✅ Set selectedFramework for incident user tasks:', this.selectedFramework);
        } else {
          console.log('⚠️ No framework selected or frameworkId not found in response');
          // UX-only filter hint; server must enforce tenant/RBAC (do not trust for authorization).
          const storedFrameworkId = getExplicitFrameworkId();
          if (storedFrameworkId) {
            this.selectedFramework = parseInt(storedFrameworkId);
            console.log('✅ Using framework ID from localStorage:', this.selectedFramework);
          } else {
            // No framework selected means "All Frameworks" - set to empty string
            this.selectedFramework = '';
            console.log('✅ No specific framework selected - showing all frameworks');
          }
        }
      } catch (frameworkError) {
        console.warn('⚠️ Could not fetch selected framework:', frameworkError);
        // Try to get from localStorage as fallback
        const storedFrameworkId = getExplicitFrameworkId();
        if (storedFrameworkId) {
          this.selectedFramework = parseInt(storedFrameworkId);
          console.log('✅ Using framework ID from localStorage as fallback:', this.selectedFramework);
        } else {
          // No framework found anywhere means "All Frameworks" - set to empty string
          this.selectedFramework = '';
          console.log('✅ No framework ID found - showing all frameworks');
        }
      }
    },
    async loadUsers() {
      try {
        console.log('🔍 [IncidentUserTasks] Checking for cached users...');

        // Check if prefetch is in progress or cache is available
        if (!window.incidentDataFetchPromise && !incidentService.hasValidUsersCache()) {
          console.log('🚀 [IncidentUserTasks] Starting incident prefetch for users (user navigated directly)...');
          window.incidentDataFetchPromise = incidentService.fetchAllIncidentData();
        }

        // Wait for prefetch if it's in progress
        if (window.incidentDataFetchPromise) {
          console.log('⏳ [IncidentUserTasks] Waiting for incident prefetch to complete...');
          try {
            await window.incidentDataFetchPromise;
            console.log('✅ [IncidentUserTasks] Incident prefetch completed');
          } catch (prefetchError) {
            console.warn('⚠️ [IncidentUserTasks] Incident prefetch failed, will fetch users directly', prefetchError);
          }
        }

        // Use cached data if available
        if (incidentService.hasValidUsersCache()) {
          console.log('✅ [IncidentUserTasks] Using cached users');
          const cachedUsers = incidentService.getData('incidentUsers') || [];
          this.users = cachedUsers.map(user => ({ ...user }));
          this.userFilterConfig.values = [
            { value: '', label: 'All Users' },
            ...this.users.map(user => ({
              value: user.UserId,
              label: `${user.UserName} (${user.role || user.Role || 'User'})`
            }))
          ];
          this.loading = false;
          this.setDefaultUser();
          return;
        }

        // Fallback: Fetch directly from API (await so default user + tasks load after users exist)
        console.log('⚠️ [IncidentUserTasks] No cached users found, fetching from API...');
        await this.fetchUsers();
      } catch (error) {
        console.error('❌ [IncidentUserTasks] Error loading users:', error);
        await this.fetchUsers();
      }
    },
    async fetchUsers() {
      console.log('🔄 [IncidentUserTasks] Fetching users from API...');
      const applyUserList = (users) => {
        const normalized = (users || [])
          .map(user => ({
            UserId: user.UserId || user.id || user.userId,
            UserName: user.UserName || user.name || user.username || 'Unknown',
            Role: user.Role || user.role || '',
            Email: user.Email || user.email || '',
            ...user
          }))
          .filter(user => user.UserId);
        this.users = normalized;
        incidentService.setData('incidentUsers', normalized);
        this.userFilterConfig.values = [
          { value: '', label: 'All Users' },
          ...normalized.map(user => ({
            value: user.UserId,
            label: `${user.UserName} (${user.role || user.Role || 'User'})`
          }))
        ];
        if (normalized.length === 0) {
          console.warn('⚠️ [IncidentUserTasks] No users found. This might indicate an API issue or empty database.');
        }
        this.loading = false;
        this.setDefaultUser();
      };

      const parseUsersPayload = (payload) => {
        if (payload && payload.success && payload.users) return payload.users;
        if (Array.isArray(payload)) return payload;
        if (payload && Array.isArray(payload.data)) return payload.data;
        console.warn('⚠️ [IncidentUserTasks] Unexpected response format:', payload);
        return [];
      };

      try {
        const payload = await apiService.get(API_ENDPOINTS.CUSTOM_USERS, {}, { timeout: 120000 });
        console.log('✅ [IncidentUserTasks] Users API response:', payload);
        applyUserList(parseUsersPayload(payload));
        console.log('✅ [IncidentUserTasks] Users processed successfully:', this.users.length, 'users');
      } catch (error) {
        console.error('❌ [IncidentUserTasks] Error fetching users:', error);
        console.log('🔄 [IncidentUserTasks] Trying fallback endpoint: /api/users/');
        try {
          const fallbackPayload = await apiService.get('/api/users/', {}, { timeout: 120000 });
          console.log('✅ [IncidentUserTasks] Fallback endpoint response:', fallbackPayload);
          let users = [];
          if (fallbackPayload && fallbackPayload.success && fallbackPayload.users) {
            users = fallbackPayload.users;
          } else if (Array.isArray(fallbackPayload)) {
            users = fallbackPayload;
          } else if (fallbackPayload && Array.isArray(fallbackPayload.data)) {
            users = fallbackPayload.data;
          }
          applyUserList(users);
          console.log('✅ [IncidentUserTasks] Fallback endpoint succeeded:', this.users.length, 'users');
        } catch (fallbackError) {
          console.error('❌ [IncidentUserTasks] Fallback endpoint also failed:', fallbackError);
          this.error = `Failed to fetch users: ${fallbackError.message || error.message}`;
          this.loading = false;
          this.users = [];
          PopupService.error('Failed to load reviewers. Please refresh the page and try again.');
        }
      }
    },
    setDefaultUser() {
      if (!this.users.length) return;

      // 1) Prefer logged-in user id from storage (matches session; list is only for dropdown)
      const storedId =
        sessionStorage.getItem('user_id') ||
        localStorage.getItem('user_id') ||
        sessionStorage.getItem('UserId') ||
        localStorage.getItem('UserId');
      if (storedId) {
        const sid = String(storedId).trim();
        const byId = this.users.find(u => String(u.UserId) === sid);
        if (byId) {
          this.selectedUserId = byId.UserId;
          this.$nextTick(() => {
            this.fetchData();
          });
          return;
        }
      }

      // 2) Match by display name from storage
      const currentUser = localStorage.getItem('user_name') || localStorage.getItem('user');
      if (currentUser) {
        let userData;
        try {
          userData = JSON.parse(currentUser);
        } catch (e) {
          userData = { UserName: currentUser };
        }
        const userName = userData.UserName || userData.username || userData.name || currentUser;
        const foundUser = this.users.find(user =>
          user.UserName === userName ||
          user.username === userName ||
          (user.UserName && userName && user.UserName.toLowerCase() === String(userName).toLowerCase())
        );
        if (foundUser) {
          this.selectedUserId = foundUser.UserId;
          this.$nextTick(() => {
            this.fetchData();
          });
          return;
        }
      }

      // 3) Single user in list — select them (common in small deployments)
      if (this.users.length === 1) {
        this.selectedUserId = this.users[0].UserId;
        this.$nextTick(() => {
          this.fetchData();
        });
      }
    },
    switchToReviewerTab() {
      this.activeTab = 'reviewer';
      if (this.selectedUserId) {
        this.fetchData();
        
        // Ensure sections are expanded properly
        this.$nextTick(() => {
          // Expand all reviewer sections by default
          this.expandedSections.reviewerPending = true;
          this.expandedSections.reviewerApproved = true;
        });
      }
    },
    async fetchData() {
      console.log('🔄 [IncidentUserTasks] fetchData called');
      console.log('🔍 [IncidentUserTasks] selectedUserId:', this.selectedUserId);
      console.log('🔍 [IncidentUserTasks] activeTab:', this.activeTab);
      
      if (!this.selectedUserId) {
        console.error('❌ [IncidentUserTasks] No user selected, skipping data fetch');
        this.userIncidents = [];
        this.reviewerTasks = [];
        return;
      }
      
      console.log('✅ [IncidentUserTasks] User selected, fetching data for userId:', this.selectedUserId);
      
      this.loading = true;
      
      const hasFrameworkFilter = !!this.selectedFramework;

      // Warm cache / wait for prefetch (needed even when a framework is selected — API user_* + framework_id often returns [])
      if (!window.incidentDataFetchPromise && !incidentService.hasValidIncidentsCache() && !incidentService.hasValidAuditFindingsCache()) {
        console.log('🚀 [IncidentUserTasks] Starting incident prefetch (user navigated directly)...');
        window.incidentDataFetchPromise = incidentService.fetchAllIncidentData();
      }
      if (window.incidentDataFetchPromise) {
        console.log('⏳ [IncidentUserTasks] Waiting for incident prefetch to complete...');
        try {
          await window.incidentDataFetchPromise;
          console.log('✅ [IncidentUserTasks] Incident prefetch completed');
        } catch (prefetchError) {
          console.warn('⚠️ [IncidentUserTasks] Incident prefetch failed, will fetch directly from API', prefetchError);
        }
      }

      // Prefer cache + client-side user/framework filters whenever bulk lists exist
      if (incidentService.hasValidIncidentsCache() || incidentService.hasValidAuditFindingsCache()) {
        console.log('✅ [IncidentUserTasks] Using cached incident data - filtering by user (and framework when set) client-side');
          
          // Get general incidents and audit findings from cache
          const cachedIncidents = incidentService.getData('incidents') || [];
          const cachedAuditFindings = incidentService.getData('auditFindings') || [];
          
          // Mark each item with its type
          const markedIncidents = Array.isArray(cachedIncidents) 
            ? cachedIncidents.map(item => ({ ...item, itemType: 'incident' })) 
            : [];
          const markedAuditFindings = Array.isArray(cachedAuditFindings) 
            ? cachedAuditFindings.map(item => ({ ...item, itemType: 'audit_finding' })) 
            : [];
          
          // Combine and filter by selected user for user tasks (MY TASKS tab)
          // IMPORTANT: For "My Tasks" we show incidents where the user is the AssignerId
          // AssignerId = the person WHO assigned the task to someone else (for tracking)
          // ReviewerId = the person assigned TO work on the task (shown in Reviewer Tasks tab)
          const combinedTasks = [...markedIncidents, ...markedAuditFindings];
          console.log('🔍 [IncidentUserTasks] Filtering tasks for user:', this.selectedUserId);
          console.log('🔍 [IncidentUserTasks] Total tasks before filter:', combinedTasks.length);
          console.log('🔍 [IncidentUserTasks] Sample task fields:', combinedTasks[0] ? Object.keys(combinedTasks[0]) : 'No tasks');
          if (combinedTasks.length > 0) {
            console.log('🔍 [IncidentUserTasks] Sample task data:', {
              id: combinedTasks[0].id,
              AssignerId: combinedTasks[0].AssignerId,
              ReviewerId: combinedTasks[0].ReviewerId,
              assigned_to_id: combinedTasks[0].assigned_to_id,
              AssignedTo: combinedTasks[0].AssignedTo,
              assigned_to: combinedTasks[0].assigned_to
            });
          }
          
          this.userIncidents = combinedTasks.filter(task => {
            // Normalize user IDs to integers for comparison
            const userId = parseInt(this.selectedUserId);
            
            // For "My Tasks" tab, we want incidents where user is the AssignerId
            // (tasks they assigned to others for tracking)
            const taskAssignerId = task.AssignerId ? parseInt(task.AssignerId) : null;
            const taskAssignerId2 = task.assigner_id ? parseInt(task.assigner_id) : null;
            const taskAssigner = task.Assigner ? parseInt(task.Assigner) : null;
            
            // Check multiple possible field names for assigner
            const matches = (
              taskAssignerId === userId ||  // Primary field: AssignerId
              taskAssignerId2 === userId || // Alternative field: assigner_id
              taskAssigner === userId       // Alternative field: Assigner
            );
            
            if (matches) {
              console.log('✅ [IncidentUserTasks] Task matched (user is assigner):', task.id, {
                AssignerId: task.AssignerId,
                ReviewerId: task.ReviewerId,
                Status: task.Status,
                matchedField: (
                  taskAssignerId === userId ? 'AssignerId' :
                  taskAssignerId2 === userId ? 'assigner_id' :
                  taskAssigner === userId ? 'Assigner' : 'unknown'
                )
              });
            }
            return matches;
          });
          
          // IMPORTANT: Transform cached data field names to match API response format
          // Cached data has: IncidentId, IncidentTitle, RiskPriority
          // API response has: id, Title, Priority
          this.userIncidents = this.userIncidents.map(task => ({
            ...task,
            id: task.id || task.IncidentId,
            Title: task.Title || task.IncidentTitle,
            Priority: task.Priority || task.RiskPriority,
            Origin: task.Origin,
            Status: task.Status,
            MitigationDueDate: task.MitigationDueDate,
            AssignerId: task.AssignerId,
            ReviewerId: task.ReviewerId,
            itemType: task.itemType
          }));

          if (this.selectedFramework) {
            const beforeFw = this.userIncidents.length;
            this.userIncidents = this.userIncidents.filter(t => this.taskMatchesSelectedFramework(t));
            console.log(`🔍 [IncidentUserTasks] Framework filter (${this.selectedFramework}): ${beforeFw} → ${this.userIncidents.length} tasks (cache)`);
          }
          
          console.log('✅ [IncidentUserTasks] Filtered user tasks:', this.userIncidents.length);
          if (this.userIncidents.length > 0) {
            console.log('✅ [IncidentUserTasks] Sample transformed task:', {
              id: this.userIncidents[0].id,
              Title: this.userIncidents[0].Title,
              Priority: this.userIncidents[0].Priority
            });
          }

          if (this.userIncidents.length === 0) {
            console.warn('⚠️ [IncidentUserTasks] No tasks after cache + user + framework filter; will try API');
          } else {
            // Filter incidents by status (case-insensitive; cache may differ from API casing)
            this.approvedIncidents = this.userIncidents.filter(incident => this.isApprovedStatus(incident.Status));
            this.rejectedIncidents = this.userIncidents.filter(incident => this.isRejectedStatus(incident.Status));
            this.pendingReviewIncidents = this.userIncidents.filter(incident =>
              this.isPendingReviewStatus(incident.Status)
            );
            this.assignedIncidents = this.userIncidents.filter(incident =>
              this.isAssignedBucketStatus(incident.Status)
            );
            
            this.expandedSections = {
              approved: true,
              rejected: true,
              pendingReview: true,
              assigned: true,
              reviewerPending: true,
              reviewerApproved: true
            };

            this.loading = false;
            this.error = null;
            
            console.log('📋 [IncidentUserTasks] Fetching reviewer tasks (API + cache merge)...');
            const revParams = this.selectedFramework ? { framework_id: this.selectedFramework } : {};
            this.loadReviewerTasksAsync(revParams).catch((error) => {
              console.error('❌ [IncidentUserTasks] Error fetching reviewer tasks:', error);
              this.reviewerTasks = this.deriveReviewerTasksFromBulkCache();
              this.approvedReviewerTasks = this.reviewerTasks.filter((task) => this.isApprovedStatus(task.Status));
              this.pendingReviewerTasks = this.reviewerTasks.filter((task) => !this.isApprovedStatus(task.Status));
              console.log(
                `✅ [IncidentUserTasks] Loaded ${this.userIncidents.length} user tasks from cache; reviewer from cache only: ${this.reviewerTasks.length}`
              );
            });
            
            return;
          }
        }
      
      // If framework filter or no cached data, fetch everything from API
      console.log(hasFrameworkFilter ? '🔍 [IncidentUserTasks] Framework filter active, fetching from API' : '⚠️ [IncidentUserTasks] No cached data, fetching from API');
      
      // Build query parameters for framework filtering
      const params = {};
      if (this.selectedFramework) {
        params.framework_id = this.selectedFramework;
        console.log('🔍 Adding framework filter to user tasks:', this.selectedFramework);
      }
      
      // Fetch user-assigned tasks first; reviewer endpoints are optional and may 401 without failing the page
      Promise.all([
        apiService.get(API_ENDPOINTS.USER_INCIDENTS(this.selectedUserId), params),
        apiService.get(API_ENDPOINTS.USER_AUDIT_FINDINGS(this.selectedUserId), params)
      ])
      .then(async ([incidentsResponse, auditFindingsResponse]) => {
        const parseList = (body) =>
          (Array.isArray(body) ? body : (body?.data || []));

        let incidents = parseList(incidentsResponse);
        let auditFindings = parseList(auditFindingsResponse);

        if (incidents.length === 0 && auditFindings.length === 0 && params.framework_id) {
          console.warn('⚠️ [IncidentUserTasks] user_* endpoints returned empty with framework_id; retrying without framework (client filter)');
          const [ir, ar] = await Promise.all([
            apiService.get(API_ENDPOINTS.USER_INCIDENTS(this.selectedUserId), {}),
            apiService.get(API_ENDPOINTS.USER_AUDIT_FINDINGS(this.selectedUserId), {})
          ]);
          incidents = parseList(ir);
          auditFindings = parseList(ar);
        }
        
        console.log('🔍 [IncidentUserTasks] API Response - Incidents:', incidents.length);
        console.log('🔍 [IncidentUserTasks] API Response - Audit Findings:', auditFindings.length);
        if (incidents.length > 0) {
          console.log('🔍 [IncidentUserTasks] Sample incident:', {
            id: incidents[0].id,
            Title: incidents[0].Title,
            Status: incidents[0].Status,
            AssignerId: incidents[0].AssignerId,
            ReviewerId: incidents[0].ReviewerId
          });
        }
        
        // Mark each item with its type and ensure field name consistency
        const markedIncidents = incidents.map(item => ({ 
          ...item, 
          itemType: 'incident',
          id: item.id || item.IncidentId,
          Title: item.Title || item.IncidentTitle,
          Priority: item.Priority || item.RiskPriority
        }));
        const markedAuditFindings = auditFindings.map(item => ({ 
          ...item, 
          itemType: 'audit_finding',
          id: item.id || item.IncidentId,
          Title: item.Title || item.IncidentTitle,
          Priority: item.Priority || item.RiskPriority
        }));
        
        // Combine and deduplicate by ID
        const combinedUserTasks = [...markedIncidents, ...markedAuditFindings];
        let uniqueUserTasks = combinedUserTasks.filter((task, index, array) => 
          index === array.findIndex(t => t.id === task.id)
        );
        if (this.selectedFramework) {
          const beforeFw = uniqueUserTasks.length;
          uniqueUserTasks = uniqueUserTasks.filter(t => this.taskMatchesSelectedFramework(t));
          console.log(`🔍 [IncidentUserTasks] Framework filter (${this.selectedFramework}): ${beforeFw} → ${uniqueUserTasks.length} tasks (API)`);
        }
        this.userIncidents = uniqueUserTasks;
        
        console.log('✅ [IncidentUserTasks] Total user incidents after deduplication:', this.userIncidents.length);
        console.log('🔍 [IncidentUserTasks] Status breakdown:', {
          all: this.userIncidents.length,
          byStatus: this.userIncidents.reduce((acc, inc) => {
            const status = inc.Status || 'No Status';
            acc[status] = (acc[status] || 0) + 1;
            return acc;
          }, {})
        });
        
        console.log('🔍 [IncidentUserTasks] All incident statuses:', 
          this.userIncidents.map(inc => ({ id: inc.id, Status: inc.Status, Title: inc.Title }))
        );
        
        this.approvedIncidents = this.userIncidents.filter(incident => {
          const matches = this.isApprovedStatus(incident.Status);
          if (matches) console.log('✅ Approved:', incident.id, incident.Title);
          return matches;
        });
        
        this.rejectedIncidents = this.userIncidents.filter(incident => {
          const matches = this.isRejectedStatus(incident.Status);
          if (matches) console.log('✅ Rejected:', incident.id, incident.Title);
          return matches;
        });
        
        this.pendingReviewIncidents = this.userIncidents.filter(incident => {
          const matches = this.isPendingReviewStatus(incident.Status);
          if (matches) console.log('✅ Pending Review:', incident.id, incident.Title, 'Status:', incident.Status);
          return matches;
        });
        
        this.assignedIncidents = this.userIncidents.filter(incident => {
          const isAssigned = this.isAssignedBucketStatus(incident.Status);
          if (isAssigned) {
            console.log('✅ [IncidentUserTasks] Assigned incident found:', {
              id: incident.id,
              Title: incident.Title,
              Status: incident.Status,
              ReviewerId: incident.ReviewerId,
              AssignerId: incident.AssignerId
            });
          }
          return isAssigned;
        });
        
        console.log('✅ [IncidentUserTasks] Filtered counts:', {
          approved: this.approvedIncidents.length,
          rejected: this.rejectedIncidents.length,
          pendingReview: this.pendingReviewIncidents.length,
          assigned: this.assignedIncidents.length
        });
        
        this.expandedSections = {
          approved: true,
          rejected: true,
          pendingReview: true,
          assigned: true,
          reviewerPending: true,
          reviewerApproved: true
        };

        this.loading = false;
        this.error = null;

        return this.loadReviewerTasksAsync(params).catch((revErr) => {
          console.warn('⚠️ [IncidentUserTasks] Reviewer tasks fetch failed (non-fatal):', revErr?.message || revErr);
          this.reviewerTasks = this.deriveReviewerTasksFromBulkCache();
          this.approvedReviewerTasks = this.reviewerTasks.filter((task) => this.isApprovedStatus(task.Status));
          this.pendingReviewerTasks = this.reviewerTasks.filter((task) => !this.isApprovedStatus(task.Status));
        });
      })
      .catch(error => {
        this.error = `Failed to fetch data: ${error.message}`;
        this.loading = false;
      });
    },
    getUserName(userId) {
      const user = this.users.find(u => u.UserId == userId);
      return user ? user.UserName : 'Unknown';
    },
    viewMitigations(incidentId) {
      // Convert incidentId to number if it's a string
      const id = typeof incidentId === 'string' ? parseInt(incidentId, 10) : incidentId;
      
      // Safety check for userIncidents array
      if (!this.userIncidents || !Array.isArray(this.userIncidents)) {
        PopupService.error('Task data not loaded. Please refresh the page and try again.');
        return;
      }

      // Find the task to determine if it's an audit finding or incident
      const task = this.userIncidents.find(t => t.id === id);
      
      if (!task) {
        PopupService.error(`Error: Task not found for ID ${id}`);
        return;
      }
      const isAuditFinding = task && task.itemType === 'audit_finding';
      
      // Set these first to ensure UI updates
      this.selectedIncidentId = id;
      this.showMitigationWorkflow = true;
      this.loadingMitigations = true;
      this.assessmentFeedbackForUser = null;
      
      // Force a UI update
      this.$nextTick(() => {
        // Use appropriate endpoints based on task type
        const mitigationsEndpoint = isAuditFinding
          ? API_ENDPOINTS.AUDIT_FINDING_MITIGATIONS(id)
          : API_ENDPOINTS.INCIDENT_MITIGATIONS(id);
        
        const reviewEndpoint = isAuditFinding
          ? API_ENDPOINTS.AUDIT_FINDING_REVIEW_DATA(id)
          : API_ENDPOINTS.INCIDENT_REVIEW_DATA(id);
        
        // Get the mitigation steps and assessment feedback
        Promise.all([
          apiService.get(mitigationsEndpoint),
          apiService.get(reviewEndpoint)
        ])
        .then(([mitigationsBody, reviewBody]) => {
          this.mitigationSteps = this.parseMitigations(mitigationsBody);
          
          // Fetch enhanced linked evidence data with documents
          this.fetchLinkedEvidenceDocuments();
          
          // Check for assessment feedback from reviewer
          if (reviewBody && reviewBody.assessment_feedback) {
            this.assessmentFeedbackForUser = reviewBody.assessment_feedback;
          }
          
          // Pre-fill questionnaire data if previous data exists
          if (mitigationsBody && mitigationsBody.previous_assessment_data &&
              Object.keys(mitigationsBody.previous_assessment_data).length > 0) {
            this.questionnaireData = {
              ...this.questionnaireData,
              ...mitigationsBody.previous_assessment_data
            };
          }
          
          this.loadingMitigations = false;
        })
        .catch(error => {
          PopupService.error(`Error loading data: ${error.message}`);
          this.mitigationSteps = [];
          this.assessmentFeedbackForUser = null;
          this.loadingMitigations = false;
        });
      });
    },
    parseMitigations(response) {
      // Handle the new enhanced response format
      if (response && response.mitigations) {
        const mitigations = response.mitigations;
        const keys = Object.keys(mitigations);
        const steps = [];
        
        // Sort keys numerically
        keys.sort((a, b) => Number(a) - Number(b));
        
        for (const key of keys) {
          const mitigation = mitigations[key];
          
          // Handle both old and new format
          let description, approved, remarks, status;
          if (typeof mitigation === 'string') {
            // Old format - just a string description
            description = mitigation;
            approved = null;
            remarks = null;
            status = 'Not Started';
          } else {
            // New format - object with feedback
            description = mitigation.description || mitigation;
            approved = mitigation.approved;
            remarks = mitigation.remarks;
            status = mitigation.status || 'Not Started';
          }
          
          
          steps.push({
            title: `Step ${key}`,
            description: description,
            status: status,
            approved: approved,
            remarks: remarks,
            previousComments: mitigation.comments || '',
            comments: '', // Start with empty for new comments
            'aws-file_link': mitigation['aws-file_link'] || null,
            fileName: mitigation.fileName || null,
            files: mitigation.files || [] // Support multiple files
          });
        }
        return steps;
      }
      
      // Handle legacy format or direct mitigation data
      const data = response.mitigations || response;
      
      // Handle the numbered object format like {"1": "Step 1 text", "2": "Step 2 text", ...}
      if (data && typeof data === 'object' && !Array.isArray(data)) {
        // Check if it's a numbered format
        const keys = Object.keys(data);
        if (keys.length > 0 && !isNaN(Number(keys[0]))) {
          const steps = [];
          // Sort keys numerically
          keys.sort((a, b) => Number(a) - Number(b));
          
          for (const key of keys) {
            steps.push({
              title: `Step ${key}`,
              description: data[key],
              status: 'Not Started',
              approved: null,
              remarks: null,
              comments: '',
              'aws-file_link': null,
              fileName: null,
              files: [] // Support multiple files
            });
          }
          return steps;
        }
      }
      
      // If it's already an array, return it
      if (Array.isArray(data)) {
        return data;
      }
      
      // If data is a string, try to parse it as JSON
      if (typeof data === 'string') {
        try {
          const parsedData = JSON.parse(data);
          if (parsedData && typeof parsedData === 'object' && !Array.isArray(parsedData)) {
            return this.parseMitigations({ mitigations: parsedData });
          }
          return Array.isArray(parsedData) ? parsedData : [parsedData];
        } catch (e) {
          return [{ title: 'Mitigation', description: data, approved: null, remarks: null }];
        }
      }
      
      // Default fallback
      return [{ title: 'Mitigation', description: 'No detailed mitigation steps available', approved: null, remarks: null, files: [] }];
    },
    closeMitigationModal() {
      this.showMitigationWorkflow = false;
      this.mitigationSteps = [];
      this.selectedIncidentId = null;
      this.showQuestionnaire = false;
      this.currentStep = 0;
      
      // Reset questionnaire data
      this.questionnaireData = {
        cost: '',
        impact: '',
        financialImpact: '',
        reputationalImpact: '',
        operationalImpact: '',
        financialLoss: '',
        systemDowntime: '',
        recoveryTime: '',
        riskRecurrence: '',
        improvementInitiative: ''
      };
    },
    updateStepStatus(index, status) {
      // Prevent editing of approved steps
      if (this.mitigationSteps[index].approved === true) {
        PopupService.warning('This mitigation step has been approved by the reviewer and cannot be modified.');
        return;
      }
      
      // Only allow updates to rejected or unreviewed steps
      if (this.mitigationSteps[index].approved === false || this.mitigationSteps[index].approved === null) {
        this.mitigationSteps[index].status = status;
      }
    },
    submitIncidentAssessment() {
      // Safety check for userIncidents array
      if (!this.userIncidents || !Array.isArray(this.userIncidents)) {
        PopupService.error('Task data not loaded. Please refresh the page and try again.');
        return;
      }

      // Find the task to determine if it's an audit finding or incident
      const task = this.userIncidents.find(t => t.id === this.selectedIncidentId);
      const isAuditFinding = task && task.itemType === 'audit_finding';
      
      this.loading = true;
      
      // Prepare the mitigation data
      const mitigationData = {};
      this.mitigationSteps.forEach((step, index) => {
        const stepNumber = (index + 1).toString();
        
        // Combine previous comments with new comments
        let combinedComments = '';
        const hasPreviousComments = step.previousComments && step.previousComments.trim();
        const hasNewComments = step.comments && step.comments.trim();
        
        if (hasPreviousComments && hasNewComments) {
          combinedComments = `Previous: ${step.previousComments.trim()}\n\nNew: ${step.comments.trim()}`;
        } else if (hasPreviousComments) {
          combinedComments = step.previousComments.trim();
        } else if (hasNewComments) {
          combinedComments = step.comments.trim();
        }
        
        mitigationData[stepNumber] = {
          description: step.description,
          status: step.status || 'Completed',
          comments: combinedComments,
          "aws-file_link": step['aws-file_link'],
          fileName: step.fileName,
          files: step.files || [], // Include multiple files
          approved: step.approved, // Include approval status
          remarks: step.remarks    // Include reviewer remarks
        };
        
      });
      
      // Prepare questionnaire data for assessment
      const extractedInfo = {
        cost: this.questionnaireData.cost || '',
        impact: this.questionnaireData.impact || '',
        financialImpact: this.questionnaireData.financialImpact || '',
        reputationalImpact: this.questionnaireData.reputationalImpact || '',
        operationalImpact: this.questionnaireData.operationalImpact || '',
        financialLoss: this.questionnaireData.financialLoss || '',
        systemDowntime: this.questionnaireData.systemDowntime || '',
        recoveryTime: this.questionnaireData.recoveryTime || '',
        riskRecurrence: this.questionnaireData.riskRecurrence || '',
        improvementInitiative: this.questionnaireData.improvementInitiative || '',
        mitigations: mitigationData,
        submittedAt: new Date().toISOString()
      };
      
      // Use appropriate endpoint based on task type
      const submitEndpoint = isAuditFinding
        ? API_ENDPOINTS.SUBMIT_AUDIT_FINDING_ASSESSMENT
        : API_ENDPOINTS.SUBMIT_INCIDENT_ASSESSMENT;
      
      apiService.post(submitEndpoint, {
        incident_id: this.selectedIncidentId,
        user_id: this.selectedUserId,
        extracted_info: extractedInfo
      })
      .then(() => {
        this.loading = false;
        this.closeMitigationModal();
        PopupService.success(`${isAuditFinding ? 'Audit finding' : 'Incident'} assessment submitted for review successfully!`);
        
        // Refresh the tasks list
        this.fetchData();
      })
      .catch(() => {
        this.loading = false;
        PopupService.error('Failed to submit assessment. Please try again.');
      });
    },
    closeReviewerModal() {
      this.showReviewerWorkflow = false;
      this.currentReviewTask = null;
      this.mitigationReviewData = {};
      this.previousVersions = {};
      this.reviewCompleted = false;
      this.reviewApproved = false;
    },
    approveMitigation(id, approved) {
      const updatedMitigation = {
        ...this.mitigationReviewData[id],
        approved: approved,
        reviewer_submitted_date: new Date().toISOString()
      };
      
      if (approved) {
        updatedMitigation.remarks = '';
      }
      
      this.mitigationReviewData = {
        ...this.mitigationReviewData,
        [id]: updatedMitigation
      };
    },
    approveAssessment(approved) {
      this.assessmentFeedback = {
        approved: approved,
        remarks: approved ? '' : this.assessmentFeedback.remarks || ''
      };
    },
    submitReview(approved) {
      if (!this.canSubmitReview) {
        PopupService.warning('Please complete the review of all mitigations');
        return;
      }
      
      const isAuditFinding = this.currentReviewTask && this.currentReviewTask.itemType === 'audit_finding';
      this.loading = true;
      
      // Prepare mitigation feedback for backend
      const mitigationFeedback = {};
      Object.keys(this.mitigationReviewData).forEach(id => {
        const mitigation = this.mitigationReviewData[id];
        mitigationFeedback[id] = {
          approved: mitigation.approved,
          remarks: mitigation.remarks || null
        };
      });
      
      const reviewData = {
        incident_id: this.currentReviewTask.id,
        approved: approved,
        reviewer_id: this.selectedUserId, // This is the reviewer performing the review
        mitigation_feedback: mitigationFeedback,
        assessment_feedback: this.assessmentFeedback
      };
      
      // For audit findings, add overall_decision parameter
      if (isAuditFinding) {
        reviewData.overall_decision = approved ? 'approved' : 'rejected';
      }
      
      
      // Use appropriate endpoint based on task type
      const reviewEndpoint = isAuditFinding
        ? API_ENDPOINTS.COMPLETE_AUDIT_FINDING_REVIEW
        : API_ENDPOINTS.COMPLETE_INCIDENT_REVIEW;
      
      apiService.post(reviewEndpoint, reviewData)
        .then(() => {
          this.loading = false;
          
          // Remove this task from the list
          const index = this.reviewerTasks.findIndex(t => t.id === this.currentReviewTask.id);
          if (index !== -1) {
            this.reviewerTasks.splice(index, 1);
          }
          
          this.reviewCompleted = true;
          this.reviewApproved = approved;
          
          PopupService.success(`${isAuditFinding ? 'Audit finding' : 'Incident'} ${approved ? 'approved' : 'rejected'} successfully!`);
          
          setTimeout(() => {
            this.closeReviewerModal();
          }, 2500);
        })
        .catch(() => {
          this.loading = false;
          PopupService.error('Failed to submit review. Please try again.');
        });
    },
    updateRemarks(id) {
      if (!this.mitigationReviewData[id].remarks.trim()) {
        PopupService.warning('Please provide remarks for rejection');
        return;
      }
      
      this.mitigationReviewData = {
        ...this.mitigationReviewData
      };
    },
    reviewMitigations(task) {
      const isAuditFinding = task && task.itemType === 'audit_finding';
      
      this.currentReviewTask = task;
      this.selectedIncidentId = task.id;
      this.loadingMitigations = true;
      this.showReviewerWorkflow = true;
      this.previousVersions = {};
      this.assessmentFeedback = {};
      
      // Use appropriate endpoint based on task type
      const reviewEndpoint = isAuditFinding
        ? API_ENDPOINTS.AUDIT_FINDING_REVIEW_DATA(task.id)
        : API_ENDPOINTS.INCIDENT_REVIEW_DATA(task.id);
      
      // Get review data (includes questionnaire, previous versions, and assessment feedback)
      apiService.get(reviewEndpoint)
        .then((body) => {
          
          if (body) {
            this.mitigationReviewData = body.mitigations || {};
            this.questionnaireReviewData = body.questionnaire_data || {};
            this.previousVersions = body.previous_versions || {};
            
            // Load existing assessment feedback if review is completed
            if (body.assessment_feedback) {
              this.assessmentFeedback = body.assessment_feedback;
            }
            
            const isCompleted = body.approval_entry?.review_completed;
            this.reviewCompleted = isCompleted;
            this.reviewApproved = body.approval_entry?.approved_rejected === 'Approved';
            
            this.loadingMitigations = false;
          } else {
            this.mitigationReviewData = {};
            this.questionnaireReviewData = {};
            this.previousVersions = {};
            this.assessmentFeedback = {};
            this.loadingMitigations = false;
          }
        })
        .catch(() => {
          this.mitigationReviewData = {};
          this.questionnaireReviewData = {};
          this.previousVersions = {};
          this.assessmentFeedback = {};
          this.loadingMitigations = false;
        });
    },
    formatDateTime(dateString) {
      if (!dateString) return '';
      
      const date = new Date(dateString);
      return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    },
    formatDate(dateString) {
      if (!dateString) return 'Not set';
      
      const date = new Date(dateString);
      return date.toLocaleDateString();
    },
    getDueStatusClass(dateString) {
      if (!dateString) return '';
      
      const dueDate = new Date(dateString);
      const today = new Date();
      
      dueDate.setHours(0, 0, 0, 0);
      today.setHours(0, 0, 0, 0);
      
      const daysLeft = Math.floor((dueDate - today) / (1000 * 60 * 60 * 24));
      
      if (daysLeft < 0) return 'overdue';
      if (daysLeft <= 3) return 'urgent';
      if (daysLeft <= 7) return 'warning';
      return 'on-track';
    },
    getDueStatusText(dateString) {
      if (!dateString) return '';
      
      const dueDate = new Date(dateString);
      const today = new Date();
      
      dueDate.setHours(0, 0, 0, 0);
      today.setHours(0, 0, 0, 0);
      
      const daysLeft = Math.floor((dueDate - today) / (1000 * 60 * 60 * 24));
      
      if (daysLeft < 0) return `(Delayed by ${Math.abs(daysLeft)} days)`;
      if (daysLeft === 0) return '(Due today)';
      if (daysLeft === 1) return '(Due tomorrow)';
      return `(${daysLeft} days left)`;
    },
    getPreviousMitigation(id) {
      if (!this.previousVersions || typeof this.previousVersions !== 'object') {
        return null;
      }
      
      if (!this.previousVersions[id]) {
        return null;
      }
      
      return this.previousVersions[id];
    },
    isStepActive(index) {
      const step = this.mitigationSteps[index];
      return step.approved === false || step.approved === null;
    },
    
    isStepLocked(index) {
      const step = this.mitigationSteps[index];
      return step.approved === true;
    },
    isOverdue(dateString) {
      if (!dateString) return false;
      const dueDate = new Date(dateString);
      const today = new Date();
      dueDate.setHours(0, 0, 0, 0);
      today.setHours(0, 0, 0, 0);
      return dueDate < today;
    },
    initializeFromQuery() {
      // Initialize from query parameters if provided
      const query = this.$route.query;
      if (query.userId) {
        this.selectedUserId = query.userId;
      }
      if (query.taskId) {
        this.viewMitigations(query.taskId);
      }
      if (query.mode === 'reviewer' && query.taskId) {
        // Switch to reviewer tab and open reviewer workflow
        this.activeTab = 'reviewer';
        this.$nextTick(() => {
          const task = { id: query.taskId };
          this.reviewMitigations(task);
        });
      }
    },
    
    // Client-side validation methods for questionnaire
    validateCurrencyInput(fieldName, event) {
      const value = event.target.value;
      
      // Allow empty values (optional fields)
      if (!value || value === '') return;
      
      // Remove any non-numeric characters except decimal point
      const numericValue = value.replace(/[^0-9.]/g, '');
      
      // Validate format
      const currencyPattern = /^[0-9]+(\.[0-9]{0,2})?$/;
      if (!currencyPattern.test(numericValue)) {
        event.target.setCustomValidity('Please enter a valid amount (e.g., 1000.50)');
      } else {
        const amount = parseFloat(numericValue);
        if (amount < 0) {
          event.target.setCustomValidity('Amount cannot be negative');
        } else if (amount > 999999999.99) {
          event.target.setCustomValidity('Amount exceeds maximum allowed value');
        } else {
          event.target.setCustomValidity('');
        }
      }
      
      // Update the model with cleaned value
      this.questionnaireData[fieldName] = numericValue;
    },
    
    validateHoursInput(fieldName, event) {
      const value = event.target.value;
      
      // Allow empty values (optional fields)
      if (!value || value === '') return;
      
      // Validate format
      const hoursPattern = /^[0-9]+(\.[0-9]{0,2})?$/;
      if (!hoursPattern.test(value)) {
        event.target.setCustomValidity('Please enter a valid number of hours (e.g., 8.5)');
      } else {
        const hours = parseFloat(value);
        if (hours < 0) {
          event.target.setCustomValidity('Hours cannot be negative');
        } else if (hours > 8760) {
          event.target.setCustomValidity('Hours exceeds reasonable maximum (8760 = 1 year)');
        } else {
          event.target.setCustomValidity('');
        }
      }
    },
    toggleSection(section) {
      this.expandedSections[section] = !this.expandedSections[section];
    },
    testEndpoints() {
      // Safety check for userIncidents array
      if (!this.userIncidents || !Array.isArray(this.userIncidents) || this.userIncidents.length === 0) {
        PopupService.error('No incidents available for testing');
        return;
      }
      
      const testId = this.userIncidents[0].id;
      const isAuditFinding = this.userIncidents[0].itemType === 'audit_finding';
      
      
      // Test endpoints
      const mitigationsEndpoint = isAuditFinding
        ? API_ENDPOINTS.AUDIT_FINDING_MITIGATIONS(testId)
        : API_ENDPOINTS.INCIDENT_MITIGATIONS(testId);
      
      const reviewEndpoint = isAuditFinding
        ? API_ENDPOINTS.AUDIT_FINDING_REVIEW_DATA(testId)
        : API_ENDPOINTS.INCIDENT_REVIEW_DATA(testId);
      
      // Test the mitigations endpoint
      apiService.get(mitigationsEndpoint)
        .then(() => {
          PopupService.success('Mitigations endpoint test successful');
        })
        .catch(error => {
          PopupService.error(`Mitigations endpoint test failed: ${error.message}`);
        });
      
      // Test the review endpoint
      apiService.get(reviewEndpoint)
        .then(() => {
          PopupService.success('Review endpoint test successful');
        })
        .catch(error => {
          PopupService.error(`Review endpoint test failed: ${error.message}`);
        });
    },
    handleFilesUploaded(uploadedFiles) {
      // Add uploaded files to the current mitigation step
      if (this.mitigationSteps[this.currentStep]) {
        if (!this.mitigationSteps[this.currentStep].files) {
          this.mitigationSteps[this.currentStep].files = [];
        }
        
        // Add uploaded files to the current mitigation step
        this.mitigationSteps[this.currentStep].files.push(...uploadedFiles);
        
        // Also update legacy fields for backward compatibility
        if (uploadedFiles.length > 0) {
          const firstFile = uploadedFiles[0];
          this.mitigationSteps[this.currentStep]['aws-file_link'] = firstFile['aws-file_link'];
          this.mitigationSteps[this.currentStep].fileName = firstFile.fileName;
        }
        
        // Force Vue to recognize the change by creating a new array
        this.mitigationSteps = [...this.mitigationSteps];
        
        // Update the status to completed if files are uploaded
        this.updateStepStatus(this.currentStep, 'Completed');
        
        console.log('Files uploaded successfully:', uploadedFiles);
        console.log('Updated mitigation steps:', this.mitigationSteps);
        
        // Show success message
        if (uploadedFiles.length > 0) {
          const message = uploadedFiles.length === 1 
            ? `File "${uploadedFiles[0].fileName}" uploaded successfully` 
            : `${uploadedFiles.length} files uploaded successfully`;
          
          // Use PopupService if available
          if (window.PopupService) {
            window.PopupService.success(message);
          } else {
            alert(message);
          }
        }
      }
    },
    formatFileSize(bytes) {
      if (!bytes) return '';
      if (bytes === 0) return '0 Bytes';
      const k = 1024;
      const sizes = ['Bytes', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
    /** Linked-evidence GET; older backends returned 404 when no IncidentApproval row — treat as empty list. */
    async fetchIncidentLinkedEvidencePayload() {
      const id = this.selectedIncidentId;
      if (id == null) return { success: true, linked_evidence: [], count: 0 };
      try {
        return await apiService.get(`/api/incidents/${id}/linked-evidence/`, {}, { skipCache: true });
      } catch (e) {
        if (e?.response?.status === 404) {
          return { success: true, linked_evidence: [], count: 0 };
        }
        throw e;
      }
    },
    handleUserTaskClick(task) {
      if (task.actions === 'view') this.viewMitigations(task.id);
      else if (task.actions === 'resubmit') this.viewMitigations(task.id); // Could be a resubmit modal if needed
    },
    handleReviewerTaskClick(task) {
      if (task.actions === 'review') this.reviewMitigations(task);
      else if (task.actions === 'view') this.reviewMitigations(task);
    },
    async showLinkedEventDetails(linkedEvent) {
      if (linkedEvent) {
        // First, try to fetch enhanced document data for this specific linked event
        try {
          
          // Fetch enhanced linked evidence data
          const linkedPayload = await this.fetchIncidentLinkedEvidencePayload();
          
          if (linkedPayload && linkedPayload.success && Array.isArray(linkedPayload.linked_evidence)) {
            const enhancedLinkedEvidence = linkedPayload.linked_evidence;
            
            // Find the matching evidence for this linked event
            const matchingEvidence = enhancedLinkedEvidence.find(evidence => {
              return evidence.id === linkedEvent.id || 
                     evidence.title === linkedEvent.title ||
                     (evidence.linkedRecordId && linkedEvent.linkedRecordId && 
                      evidence.linkedRecordId.toString() === linkedEvent.linkedRecordId.toString());
            });
            
            if (matchingEvidence && matchingEvidence.documents && matchingEvidence.documents.length > 0) {
              // Update the linkedEvent with enhanced document data
              linkedEvent.documents = matchingEvidence.documents;
              linkedEvent.document_count = matchingEvidence.documents.length;
              
              
              // Force Vue reactivity update to show documents in UI
              this.$forceUpdate();
              
              // Show success message that documents are now loaded
              PopupService.success(`Documents loaded successfully! ${matchingEvidence.documents.length} document(s) are now available for download.`);
            } else {
              // No enhanced documents found
              PopupService.info('No additional documents found for this linked event.');
            }
          } else {
            // Fallback if API call fails
            PopupService.warning('Unable to fetch document details. Please try refreshing.');
          }
        } catch (error) {
          PopupService.error('Error loading documents. Please try again.');
        }
      }
    },
    async showLinkedEventDetailsFromStep(stepKey) {
      // Try to get linked event details from the files array first
      const step = this.mitigationSteps[stepKey];
      if (step && step.files && step.files.length > 0) {
        const linkedFile = step.files.find(file => file.type === 'linked_evidence');
        if (linkedFile && linkedFile.linkedEvent) {
          await this.showLinkedEventDetails(linkedFile.linkedEvent);
          return;
        }
      }
      
      // Fallback: show basic info from the step itself
      alert(`Linked Event: ${step.fileName}\n\nThis is a linked event from another system. Full details may not be available in legacy format.`);
    },
    async showLinkedEventDetailsFromMitigation(mitigation) {
      // Try to get linked event details from the files array first
      if (mitigation.files && mitigation.files.length > 0) {
        const linkedFile = mitigation.files.find(file => file.type === 'linked_evidence');
        if (linkedFile && linkedFile.linkedEvent) {
          await this.showLinkedEventDetails(linkedFile.linkedEvent);
          return;
        }
      }
      
      // Fallback: show basic info from the mitigation itself
      alert(`Linked Event: ${mitigation.fileName}\n\nThis is a linked event from another system. Full details may not be available in legacy format.`);
    },
    
    async fetchLinkedEvidenceDocuments() {
      if (!this.selectedIncidentId) return;
      
      try {
        
        const linkedPayload = await this.fetchIncidentLinkedEvidencePayload();
        
        if (linkedPayload && linkedPayload.success && Array.isArray(linkedPayload.linked_evidence)) {
          const enhancedLinkedEvidence = linkedPayload.linked_evidence;
          
          // Update the mitigation steps with enhanced linked evidence data
          this.mitigationSteps.forEach(step => {
            if (step.files && step.files.length > 0) {
              step.files.forEach(file => {
                if (file.type === 'linked_evidence' && file.linkedEvent) {
                  // Find the enhanced data for this linked event using multiple matching criteria
                  let enhancedData = enhancedLinkedEvidence.find(evidence => {
                    // Try multiple matching strategies
                    const idMatch = evidence.id === file.linkedEvent.id;
                    const titleMatch = evidence.title === file.linkedEvent.title;
                    const recordIdMatch = evidence.linkedRecordId && file.linkedEvent.linkedRecordId && 
                                        evidence.linkedRecordId.toString() === file.linkedEvent.linkedRecordId.toString();
                    const stringIdMatch = evidence.id && file.linkedEvent.id && 
                                        evidence.id.toString() === file.linkedEvent.id.toString();
                    
                    
                    return idMatch || titleMatch || recordIdMatch || stringIdMatch;
                  });
                  
                  
                  // Force matching for Document Handling System events by ID pattern
                  if (!enhancedData && file.linkedEvent.source === 'Document Handling System') {
                    
                    // Try exact ID match first
                    enhancedData = enhancedLinkedEvidence.find(e => e.id === file.linkedEvent.id);
                    if (!enhancedData) {
                      // Try linkedRecordId match
                      enhancedData = enhancedLinkedEvidence.find(e => 
                        e.linkedRecordId && file.linkedEvent.linkedRecordId && 
                        e.linkedRecordId.toString() === file.linkedEvent.linkedRecordId.toString()
                      );
                    }
                    if (!enhancedData) {
                      // Try title match
                      enhancedData = enhancedLinkedEvidence.find(e => 
                        e.title === file.linkedEvent.title
                      );
                    }
                    if (!enhancedData) {
                      // Try partial title match for Document Handling
                      enhancedData = enhancedLinkedEvidence.find(e => 
                        e.source === 'Document Handling System' &&
                        e.title?.toLowerCase().includes(file.linkedEvent.title?.toLowerCase().split(' ').slice(-1)[0])
                      );
                    }
                    
                  }
                  
                  if (enhancedData) {
                    
                    // Update the linkedEvent with enhanced data including documents
                    const updatedLinkedEvent = {
                      ...file.linkedEvent,
                      ...enhancedData,
                      documents: enhancedData.documents || [],
                      document_count: enhancedData.document_count || enhancedData.documents?.length || 0
                    };
                    
                    // Replace the entire linkedEvent object to trigger Vue reactivity
                    file.linkedEvent = updatedLinkedEvent;
                    
                    // Also update the file object properties to ensure UI updates
                    if (enhancedData.documents && enhancedData.documents.length > 0) {
                      file.hasDocuments = true;
                      file.documentCount = enhancedData.documents.length;
                    }
                    
                    
                    // CRITICAL: Update the mitigation step itself to trigger Vue reactivity
                    const stepIndex = this.mitigationSteps.findIndex(s => s === step);
                    if (stepIndex !== -1) {
                      // Create new step object
                      const updatedStep = {
                        ...step,
                        files: step.files.map(f => f === file ? { ...file } : f)
                      };
                      
                      // Replace the step in the array
                      this.mitigationSteps.splice(stepIndex, 1, updatedStep);
                    }
                    
                  } else {
                    // Fallback: Ensure basic document structure exists
                    if (!file.linkedEvent.documents || file.linkedEvent.documents.length === 0) {
                      
                      // Create a basic document structure based on the file name
                      const fileName = file.linkedEvent.title || file.fileName || 'Unknown File';
                      const fallbackDocument = {
                        id: `fallback_${file.linkedEvent.id}`,
                        name: fileName,
                        fileName: fileName,
                        type: 'document',
                        size: 'Unknown',
                        url: '#',
                        isFallback: true
                      };
                      
                      // Update the linked event with fallback document
                      file.linkedEvent = {
                        ...file.linkedEvent,
                        documents: [fallbackDocument],
                        document_count: 1
                      };
                      
                      // Update file properties
                      file.hasDocuments = true;
                      file.documentCount = 1;
                      
                    }
                  }
                }
              });
            }
          });
          
          
          // Aggressive Vue reactivity - create completely new objects
          this.mitigationSteps = this.mitigationSteps.map(step => ({
            ...step,
            files: step.files ? step.files.map(file => ({ ...file })) : []
          }));
          
          // Multiple force updates
          this.$forceUpdate();
          this.$nextTick(() => {
            this.$forceUpdate();
            this.$nextTick(() => {
              this.$forceUpdate();
            });
          });
        }
      } catch (error) {
        // Error fetching enhanced linked evidence
      }
    },
    
    downloadLinkedDocument(evidenceId, documentIndex, docData) {
      try {
        // If document has direct s3_url, use that
        if (docData && docData.s3_url) {
          const link = document.createElement('a');
          link.href = docData.s3_url;
          link.download = docData.filename || 'document';
          link.target = '_blank';
          link.rel = 'noopener noreferrer';
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          return;
        }
        
        // Backend download route — use API origin (relative /api/... hits the SPA dev server, not Django).
        // Do not pass client-controlled user_id; session/JWT must authorize (see event_views.download_linked_evidence_document).
        const incidentId = this.selectedIncidentId;
        const downloadUrl = `${API_BASE_URL}/api/incidents/${incidentId}/linked-evidence/${encodeURIComponent(String(evidenceId))}/documents/${Number(documentIndex)}/download/`;
        
        // Create a temporary link and click it to trigger download
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = docData.filename || 'document';
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
      } catch (error) {
        
        // Safe error handling
        try {
          if (this.$toast && this.$toast.error) {
            this.$toast.error('Failed to download document');
          } else {
            alert('Failed to download document: ' + (error.message || 'Unknown error'));
          }
        } catch (toastError) {
          alert('Failed to download document');
        }
      }
    },
    
    refreshLinkedEvidence() {
      // Clear any existing test data from linked events
      this.mitigationSteps.forEach(step => {
        if (step.files && step.files.length > 0) {
          step.files.forEach(file => {
            if (file.type === 'linked_evidence' && file.linkedEvent && file.linkedEvent.source === 'Document Handling System') {
              // Reset documents to empty to get fresh data from backend
              file.linkedEvent.documents = [];
              file.linkedEvent.document_count = 0;
            }
          });
        }
      });
      
      // Fetch fresh data from backend
      this.fetchLinkedEvidenceDocuments();
    },
    
    async forceUpdateDocuments(file) {
      
      try {
        // Use centralized HTTP layer (cookies + CSRF + same auth as rest of app). Avoid manual Bearer from storage.
        const data = await this.fetchIncidentLinkedEvidencePayload();
        if (data && data.success && Array.isArray(data.linked_evidence)) {
          const matchingEvidence = data.linked_evidence.find(evidence =>
            evidence.id === file.linkedEvent.id ||
            evidence.title === file.linkedEvent.title
          );
          if (matchingEvidence && matchingEvidence.documents) {
            const updatedLinkedEvent = {
              ...file.linkedEvent,
              documents: matchingEvidence.documents,
              document_count: matchingEvidence.documents.length
            };
            file.linkedEvent = updatedLinkedEvent;
            this.$forceUpdate();
            alert(`Force updated ${file.linkedEvent.title} with ${matchingEvidence.documents.length} documents from backend`);
          } else {
            alert('No matching evidence found for force update');
          }
        } else {
          alert('Failed to fetch evidence data from backend');
        }
      } catch (error) {
        alert('Error force updating documents: ' + error.message);
      }
    }
  }
}
</script>

<style scoped>
@import './IncidentUserTask.css';
</style> 