<template>
  <!-- Show Access Denied if user doesn't have SubmitVendorForApproval permission -->
  <AccessDenied 
    v-if="!hasAccess"
    :message="accessDeniedInfo.message"
    :errorCode="accessDeniedInfo.code"
    :permission="accessDeniedInfo.permission"
  />
  
  <!-- Show content only if user has permission -->
  <div v-else class="comprehensive-workflow-creator">
    <!-- Page Header -->
    <div class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">Create Workflow & Request</h1>
        <p class="page-subtitle">Design and configure approval workflows with modern, intuitive controls</p>
      </div>
      <div class="page-header-right">
        <div class="status-indicator">
          <div class="status-dot"></div>
          <span>Ready to create</span>
        </div>
      </div>
    </div>

    <div class="workflow-card card">
      <!-- Tab Navigation -->
      <div class="tab-navigation">
        <button 
          type="button"
          :class="['tab-button', { active: activeTab === 'workflow' }]"
          @click="activeTab = 'workflow'"
        >
          WORKFLOW INFORMATION
        </button>
        <button 
          type="button"
          :class="['tab-button', { active: activeTab === 'request' }]"
          @click="activeTab = 'request'"
        >
          REQUEST INFORMATION
        </button>
        <button 
          type="button"
          :class="['tab-button', { active: activeTab === 'data' }]"
          @click="activeTab = 'data'"
        >
          REQUEST DATA
        </button>
        <button 
          type="button"
          :class="['tab-button', { active: activeTab === 'stages' }]"
          @click="activeTab = 'stages'"
        >
          STAGES CONFIGURATION
        </button>
      </div>

      <form 
        ref="workflowFormRef" 
        class="workflow-form"
        @submit.prevent="submitWorkflow"
      >
        <!-- Auto-populate notification -->
        <div v-if="isAutoPopulated" class="alert alert-info" style="margin: 20px 24px; border: 2px solid #93c5fd; background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);">
          <div class="alert-icon" style="font-size: 1.5rem;">🚀</div>
          <div class="alert-content">
            <div class="alert-title" style="font-size: 1.1rem; font-weight: 700; color: #60a5fa;">Auto-populated from Questionnaire Builder</div>
            <div class="alert-description" style="font-size: 1rem; color: #60a5fa;">{{ autoPopulateMessage }}</div>
          </div>
        </div>
        
        <!-- Workflow Information Tab -->
        <div v-show="activeTab === 'workflow'" class="tab-content">
        
        <div class="row">
          <div class="col-12">
            <div class="form-item">
              <label class="form-label">Workflow Name</label>
              <input 
                v-model.lazy="workflowForm.workflow_name" 
                type="text"
                class="form-input"
                placeholder="e.g., Standard Policy Approval"
              />
            </div>
          </div>
          <div class="col-12">
            <div class="form-item">
              <label class="form-label">Workflow Type</label>
              <select v-model="workflowForm.workflow_type" class="form-select">
                <option value="">Select workflow type</option>
                <option value="MULTI_LEVEL">Tiered Approval</option>
                <option value="MULTI_PERSON">Team Approval</option>
              </select>
            </div>
          </div>
        </div>

        <div class="row">
          <div class="col-12">
            <div class="form-item">
              <label class="form-label">Created By</label>
              <input 
                v-model.lazy="workflowForm.created_by" 
                type="text"
                class="form-input"
                placeholder="Username" 
                readonly 
              />
            </div>
          </div>
        </div>
        
        <!-- Hidden Created By field - auto-populated from current user -->
        <div class="form-item" style="display: none;">
          <input v-model="workflowForm.created_by" type="hidden" />
        </div>
        <!-- Hidden Business Object Type field -->
        <div class="form-item" style="display: none;">
          <input v-model="workflowForm.business_object_type" type="hidden" />
        </div>

        <div class="form-item">
          <label class="form-label">Description</label>
          <textarea 
            v-model.lazy="workflowForm.description" 
            class="form-textarea"
            rows="3"
            placeholder="Describe the workflow purpose and rules..."
          ></textarea>
        </div>

        <!-- Tab Navigation Buttons -->
        <div class="tab-actions">
          <button type="button" class="btn btn-primary btn-tab-nav" @click="activeTab = 'request'">
            REQUEST INFORMATION
          </button>
        </div>
        </div>

        <!-- Request Information Tab -->
        <div v-show="activeTab === 'request'" class="tab-content">
        
        <div class="row">
          <div class="col-12">
            <div class="form-item">
              <label class="form-label">Request Title</label>
              <input 
                v-model.lazy="requestForm.request_title" 
                type="text"
                class="form-input"
                placeholder="e.g., Employee Remote Work Policy"
              />
            </div>
          </div>
          <div class="col-12">
            <div class="form-item">
              <label class="form-label">Priority</label>
              <select v-model="requestForm.priority" class="form-select">
                <option value="">Select priority</option>
                <option value="LOW">Low</option>
                <option value="MEDIUM">Medium</option>
                <option value="HIGH">High</option>
                <option value="URGENT">Urgent</option>
              </select>
            </div>
          </div>
        </div>
        <!-- Hidden Requester fields - auto-populated from current user -->
        <div class="form-item" style="display: none;">
          <input v-model="requestForm.requester_id" type="hidden" />
          <input v-model="requestForm.requester_name" type="hidden" />
          <input v-model="requestForm.requester_department" type="hidden" />
        </div>

        <div class="row">
          <div class="col-12">
            <div class="form-item">
              <label class="form-label">Department</label>
              <input 
                v-model.lazy="requestForm.requester_department" 
                type="text"
                class="form-input"
                placeholder="Your department" 
              />
            </div>
          </div>
        </div>

        <div class="form-item">
          <label class="form-label">Request Description</label>
          <textarea 
            v-model.lazy="requestForm.request_description" 
            class="form-textarea"
            rows="3"
            placeholder="Describe what you're requesting approval for..."
          ></textarea>
        </div>

        <!-- Tab Navigation Buttons -->
        <div class="tab-actions">
          <button type="button" class="btn btn-secondary btn-tab-nav" @click="activeTab = 'workflow'">
            BACK TO WORKFLOW
          </button>
          <button type="button" class="btn btn-primary btn-tab-nav" @click="activeTab = 'data'">
            REQUEST DATA
          </button>
        </div>
        </div>

        <!-- Request Data Tab -->
        <div v-show="activeTab === 'data'" class="tab-content">
        
        <div class="payload-section">
          <div class="payload-header">
            <h3>Request Payload</h3>
            <button type="button" class="help-button" @click="showPayloadHelp">
              <span class="icon">?</span>
              Help
            </button>
          </div>
          
          <div class="row" style="margin-bottom: 20px;">
            <div class="col-12">
              <div class="form-item">
                <label class="form-label">Approval Type</label>
                <select 
                  v-model="approvalType" 
                  class="form-select" 
                  @change="handleApprovalTypeChange"
                >
                  <option value="">Select approval type</option>
                  <option 
                    v-for="option in availableApprovalTypes" 
                    :key="option.value" 
                    :value="option.value"
                  >
                    {{ option.label }}
                  </option>
                </select>
              </div>
            </div>
            <div class="col-12" v-if="approvalType === 'questionnaire_approval'">
              <div class="form-item">
                <label class="form-label">Select Questionnaire</label>
                <select 
                  v-model="selectedQuestionnaire" 
                  class="form-select"
                  :disabled="loadingQuestionnaires"
                  @change="handleQuestionnaireChange"
                  :style="isAutoPopulated ? 'border: 2px solid #10b981; background: #f0fdf4;' : ''"
                >
                  <option value="" disabled>{{ loadingQuestionnaires ? 'Loading questionnaires...' : 'Select questionnaire' }}</option>
                  <option
                    v-for="questionnaire in (questionnaires || [])"
                    :key="questionnaire.questionnaire_id"
                    :value="questionnaire.questionnaire_id"
                  >
                    {{ getQuestionnaireDisplayName(questionnaire) }}
                  </option>
                </select>
                <div v-if="loadingQuestionnaires" class="form-help-text" style="color: #60a5fa; font-weight: 500;">
                  ⏳ Loading questionnaires...
                </div>
                <div v-if="!loadingQuestionnaires && questionnaires && questionnaires.length === 0" class="form-help-text" style="color: #f59e0b; font-weight: 500;">
                  ⚠️ No questionnaires available. Please check database or permissions.
                </div>
                <div v-if="isAutoPopulated && selectedQuestionnaire" class="form-help-text" style="color: #10b981; font-weight: 600;">
                  ✓ Auto-selected from Questionnaire Builder
                </div>
              </div>
            </div>
            <div class="col-12" v-if="approvalType === 'final_vendor_approval'">
              <div class="form-item">
                <label class="form-label">Select Vendor</label>
                <select 
                  v-model="selectedVendor" 
                  class="form-select"
                  :disabled="loadingVendors"
                  @change="handleVendorChange"
                >
                  <option value="">Select vendor</option>
                  <option
                    v-for="vendor in (vendors || [])"
                    :key="vendor.id"
                    :value="vendor.id"
                  >
                    {{ getVendorDisplayName(vendor) }}
                  </option>
                </select>
              </div>
            </div>
          </div>
          
          <!-- Questionnaire Approval Form -->
          <div v-if="approvalType === 'questionnaire_approval' && selectedQuestionnaire && Object.keys(selectedQuestionnaireData).length > 0">
            <div class="alert alert-info">
              <div class="alert-icon">ℹ</div>
              <div class="alert-content">
                <div class="alert-title">Questionnaire Approval Details</div>
                <div class="alert-description">Review the selected questionnaire details for approval.</div>
              </div>
            </div>
            
            <div class="questionnaire-card card">
              <div class="card-header">
                <div class="questionnaire-header">
                  <h3>{{ selectedQuestionnaireData.questionnaire_name || 'Activated Test Questionnaire' }}</h3>
                  <span :class="getQuestionnaireTypeColor(selectedQuestionnaireData.questionnaire_type)" class="tag">
                    {{ selectedQuestionnaireData.questionnaire_type || 'ONBOARDING' }}
                  </span>
                </div>
              </div>
              
              <div class="card-body">
                <div class="row">
                  <div class="col-12">
                    <div class="form-item">
                      <label class="form-label">Questionnaire ID</label>
                      <input :value="selectedQuestionnaireData.questionnaire_id || '13'" class="form-input" readonly />
                    </div>
                  </div>
                  <div class="col-12">
                    <div class="form-item">
                      <label class="form-label">Version</label>
                      <input :value="selectedQuestionnaireData.version || '1.0'" class="form-input" readonly />
                    </div>
                  </div>
                </div>
                
                <div class="row">
                  <div class="col-12">
                    <div class="form-item">
                      <label class="form-label">Type</label>
                      <input :value="selectedQuestionnaireData.questionnaire_type || 'ONBOARDING'" class="form-input" readonly />
                    </div>
                  </div>
                  <div class="col-12">
                    <div class="form-item">
                      <label class="form-label">Created Date</label>
                      <input :value="selectedQuestionnaireData.created_at ? formatDate(selectedQuestionnaireData.created_at) : '9/9/2025 5:19:21 AM'" class="form-input" readonly />
                    </div>
                  </div>
                </div>
                
                <div class="form-item">
                  <label class="form-label">Description</label>
                  <textarea
                    :value="selectedQuestionnaireData.description || 'Final Description'"
                    class="form-textarea"
                    rows="3"
                    readonly
                  ></textarea>
                </div>
                
                <div class="form-item">
                  <label class="form-label">Approval Type</label>
                  <input value="Questionnaire Approval" class="form-input" readonly />
                </div>
              </div>
            </div>
          </div>
          
          <!-- Response Approval Form -->
          <div v-if="approvalType === 'response_approval'">
            <!-- Response Approval Workflow Card -->
            <div class="response-approval-card">
              <div class="response-approval-icon">📋</div>
              <h2 class="response-approval-title">Response Approval Workflow</h2>
              <p class="response-approval-description">Review and approve submitted questionnaire responses with comprehensive evaluation tools</p>
              <div class="response-approval-tag">TEAM REVIEW</div>
            </div>
            
            <!-- Submitted Questionnaire Section -->
            <div class="submitted-questionnaire-section">
              <div class="form-item">
                <label class="form-label">
                  <span class="label-icon-small">📄</span>
                  SUBMITTED QUESTIONNAIRE
                </label>
                <div class="questionnaire-select-wrapper">
                  <input 
                    :value="selectedQuestionnaireAssignment && Object.keys(selectedAssignmentData).length > 0 ? getAssignmentDisplayName(selectedAssignmentData) : ''"
                    class="form-input questionnaire-select-input"
                    placeholder="Select a questionnaire assignment"
                    readonly
                  />
                  <select 
                    v-model="selectedQuestionnaireAssignment" 
                    class="questionnaire-select-dropdown"
                    :disabled="loadingQuestionnaireAssignments"
                    @change="handleQuestionnaireAssignmentChange"
                  >
                    <option value="">Choose a responded questionnaire to review and approve</option>
                    <option
                      v-for="assignment in (questionnaireAssignments || [])"
                      :key="assignment.assignment_id"
                      :value="assignment.assignment_id"
                    >
                      {{ getAssignmentDisplayName(assignment) }}
                    </option>
                  </select>
                </div>
              </div>
              
              <div v-if="selectedQuestionnaireAssignment && Object.keys(selectedAssignmentData).length > 0" class="questionnaire-details-row">
                <div class="detail-item">
                  <label class="detail-label">ASSIGNMENT ID</label>
                  <div class="detail-value">#{{ selectedAssignmentData.assignment_id || '29' }}</div>
                </div>
                <div class="detail-item">
                  <label class="detail-label">QUESTIONNAIRE VERSION</label>
                  <div class="detail-value">v{{ selectedAssignmentData.questionnaire_version || '1.0' }}</div>
                </div>
                <div class="detail-item">
                  <label class="detail-label">SUBMISSION DATE</label>
                  <div class="detail-value">{{ selectedAssignmentData.submission_date ? formatDate(selectedAssignmentData.submission_date) : '10/21/2025 11:08:40 AM' }}</div>
                </div>
              </div>
            </div>
            
            
            <!-- Assignment Details Display (Hidden for MULTI_PERSON) -->
            <div v-if="selectedQuestionnaireAssignment && Object.keys(selectedAssignmentData).length > 0" style="display: none;">
              <div class="assignment-details-card card" style="margin-bottom: 24px">
                <div class="card-header">
                  <div class="assignment-header">
                    <div class="header-content">
                      <span class="header-icon" style="color: #67c23a;">✅</span>
                      <div>
                        <h3>{{ selectedAssignmentData.questionnaire_name || 'APPROVAL QUESTIONS' }}</h3>
                        <p class="header-subtitle">Assignment Details & Vendor Information</p>
                      </div>
                    </div>
                    <div class="assignment-tags">
                      <span :class="getQuestionnaireTypeColor(selectedAssignmentData.questionnaire_type)" class="tag tag-large">
                        {{ selectedAssignmentData.questionnaire_type || 'ONBOARDING' }}
                      </span>
                      <span class="tag tag-success tag-large">
                        {{ selectedAssignmentData.status || 'SUBMITTED' }}
                      </span>
                      <span class="tag tag-warning tag-large">
                        Score: {{ selectedAssignmentData.overall_score || '70' }}%
                      </span>
                    </div>
                  </div>
                </div>
                
                <div class="card-body">
                  <!-- Assignment Summary -->
                  <div class="assignment-summary">
                    <div class="row">
                      <div class="col-8">
                        <div class="summary-item">
                          <div class="summary-label">ASSIGNMENT ID</div>
                          <div class="summary-value">#{{ selectedAssignmentData.assignment_id || '15' }}</div>
                        </div>
                      </div>
                      <div class="col-8">
                        <div class="summary-item">
                          <div class="summary-label">QUESTIONNAIRE VERSION</div>
                          <div class="summary-value">v{{ selectedAssignmentData.questionnaire_version || '1.0' }}</div>
                        </div>
                      </div>
                      <div class="col-8">
                        <div class="summary-item">
                          <div class="summary-label">SUBMISSION DATE</div>
                          <div class="summary-value">{{ selectedAssignmentData.submission_date ? formatDate(selectedAssignmentData.submission_date) : '9/23/2025 2:17:45 AM' }}</div>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div class="vendor-info-section">
                    <div class="section-header">
                      <span class="icon">👤</span>
                      <span class="section-title">Vendor Information</span>
                    </div>
                    
                    <div class="row" style="margin-bottom: 20px">
                      <div class="col-12">
                        <div class="form-item">
                          <label class="form-label">Company Name</label>
                          <input :value="selectedAssignmentData.vendor_company_name || 'GlobalMed Supplies'" class="form-input" readonly />
                        </div>
                      </div>
                      <div class="col-12">
                        <div class="form-item">
                          <label class="form-label">Vendor Code</label>
                          <input :value="selectedAssignmentData.vendor_code || 'V002'" class="form-input" readonly />
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div class="questionnaire-details-section">
                    <div class="section-header">
                      <span class="icon">📄</span>
                      <span class="section-title">Questionnaire Details</span>
                    </div>
                    
                    <div class="form-item" style="margin-bottom: 16px">
                      <label class="form-label">Description</label>
                      <textarea
                        :value="selectedAssignmentData.questionnaire_description || 'APPROVAL QUESTIONS'"
                        class="form-textarea readonly-textarea"
                        rows="3"
                        readonly
                      ></textarea>
                    </div>
                    
                    <div class="form-item" style="margin-bottom: 0">
                      <label class="form-label">Additional Notes</label>
                      <textarea
                        :value="selectedAssignmentData.notes || 'Final Decision: DRAFT\nAssignee Comments: Individual score saved'"
                        class="form-textarea readonly-textarea"
                        rows="2"
                        readonly
                      ></textarea>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- Response Statistics Card -->
              <div class="statistics-card card" style="margin-bottom: 24px">
                <div class="card-header">
                  <div class="card-header-with-icon">
                    <span class="header-icon" style="color: #e6a23c;">📊</span>
                    <h3>Response Statistics</h3>
                  </div>
                </div>
                
                <div class="card-body">
                  <div class="row">
                    <div class="col-6">
                      <div class="stat-card">
                        <div class="stat-number">{{ selectedAssignmentData.response_statistics?.total_questions || 2 }}</div>
                        <div class="stat-label">TOTAL QUESTIONS</div>
                      </div>
                    </div>
                    <div class="col-6">
                      <div class="stat-card">
                        <div class="stat-number">{{ selectedAssignmentData.response_statistics?.completed_questions || 2 }}</div>
                        <div class="stat-label">COMPLETED</div>
                      </div>
                    </div>
                    <div class="col-6">
                      <div class="stat-card">
                        <div class="stat-number">{{ selectedAssignmentData.response_statistics?.required_questions || 0 }}</div>
                        <div class="stat-label">REQUIRED</div>
                      </div>
                    </div>
                    <div class="col-6">
                      <div class="stat-card">
                        <div class="stat-number">{{ selectedAssignmentData.response_statistics?.completion_percentage || 100 }}%</div>
                        <div class="stat-label">COMPLETION RATE</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- Enhanced Questions and Responses Card -->
              <div class="questions-responses-card-enhanced card" style="margin-bottom: 24px">
                <div class="card-header">
                  <div class="questions-header">
                    <div class="header-content">
                      <span class="header-icon-enhanced">❓</span>
                      <div>
                        <h3>Questions & Vendor Responses</h3>
                        <p class="header-subtitle">Comprehensive review of questionnaire questions and vendor-provided responses</p>
                      </div>
                    </div>
                    <div class="questions-summary">
                      <div class="summary-item">
                        <span class="summary-label">Total Questions</span>
                        <span class="summary-value">{{ selectedAssignmentData.questions_and_responses?.length || 0 }}</span>
                      </div>
                      <div class="summary-item">
                        <span class="summary-label">Completed</span>
                        <span class="summary-value">{{ selectedAssignmentData.questions_and_responses?.filter(q => q.is_completed).length || 0 }}</span>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div class="card-body">
                  <!-- Enhanced Questions List -->
                  <div v-if="selectedAssignmentData.questions_and_responses && selectedAssignmentData.questions_and_responses.length > 0" class="questions-container-enhanced">
                    <div 
                      v-for="(question, index) in selectedAssignmentData.questions_and_responses" 
                      :key="question.question_id || `question_${index}`"
                      class="question-item-enhanced"
                >
                      <div class="question-header-enhanced" @click="toggleQuestion(question.question_id || `question_${index}`)">
                        <div class="question-main-info">
                          <div class="question-number-enhanced">
                            <span class="q-number">Q{{ index + 1 }}</span>
                          </div>
                          <div class="question-content-main">
                            <h4 class="question-title">{{ question.question_text || 'No question text' }}</h4>
                            <div class="question-meta">
                              <span class="question-type-badge">{{ formatQuestionType(question.question_type) }}</span>
                              <span v-if="question.is_required" class="required-badge">Required</span>
                              <span v-if="question.scoring_weight" class="weight-badge">Weight: {{ question.scoring_weight }}</span>
                            </div>
                          </div>
                        </div>
                        <div class="question-status-section">
                          <div class="status-badges">
                            <span :class="question.is_completed ? 'status-completed' : 'status-incomplete'" class="status-badge">
                              {{ question.is_completed ? 'Completed' : 'Incomplete' }}
                            </span>
                            <span v-if="question.score !== undefined && question.score !== null" class="score-badge">
                              {{ question.score }}%
                            </span>
                          </div>
                          <div class="expand-icon">
                            <span class="expand-arrow" :class="{ 'expanded': activeQuestionCollapse.includes(question.question_id || `question_${index}`) }">▼</span>
                          </div>
                        </div>
                      </div>
                      
                      <div v-show="activeQuestionCollapse.includes(question.question_id || `question_${index}`)" class="question-details-enhanced">
                        <div class="details-grid">
                          <div class="question-details-panel">
                            <div class="panel-header">
                              <span class="panel-icon">📝</span>
                              <h5>Question Details</h5>
                            </div>
                            <div class="details-content">
                              <div class="detail-row">
                                <span class="detail-label">Type:</span>
                                <span class="detail-value">{{ formatQuestionType(question.question_type) }}</span>
                              </div>
                              <div v-if="question.category" class="detail-row">
                                <span class="detail-label">Category:</span>
                                <span class="detail-value">{{ question.category }}</span>
                              </div>
                              <div v-if="question.scoring_weight !== undefined" class="detail-row">
                                <span class="detail-label">Scoring Weight:</span>
                                <span class="detail-value">{{ question.scoring_weight }}</span>
                              </div>
                              <div v-if="question.is_required !== undefined" class="detail-row">
                                <span class="detail-label">Required:</span>
                                <span class="detail-value">{{ question.is_required ? 'Yes' : 'No' }}</span>
                              </div>
                              
                              <!-- Enhanced options display -->
                              <div v-if="question.options && question.options.length > 0" class="options-section">
                                <span class="detail-label">Available Options:</span>
                                <div class="options-grid">
                                  <span v-for="(option, optIdx) in question.options" :key="optIdx" class="option-item">
                                    {{ option }}
                                  </span>
                                </div>
                              </div>
                            </div>
                          </div>
                          
                          <div class="response-details-panel">
                            <div class="panel-header">
                              <span class="panel-icon">💬</span>
                              <h5>Vendor Response</h5>
                            </div>
                            <div class="response-content-enhanced">
                              <div v-if="question.vendor_response" class="response-section">
                                <div class="response-header">
                                  <span class="response-label">Response:</span>
                                </div>
                                <div class="response-value-enhanced">{{ question.vendor_response }}</div>
                              </div>
                              <div v-else class="no-response-enhanced">
                                <span class="no-response-icon">⚠️</span>
                                <span>No response provided</span>
                              </div>
                              
                              <!-- Enhanced vendor comment -->
                              <div v-if="question.vendor_comment" class="comment-section">
                                <div class="comment-header">
                                  <span class="comment-label">Additional Comment:</span>
                                </div>
                                <div class="comment-value-enhanced">{{ question.vendor_comment }}</div>
                              </div>
                              
                              <!-- Enhanced file uploads -->
                              <div v-if="question.file_uploads && question.file_uploads.length > 0" class="attachments-section">
                                <div class="attachments-header">
                                  <span class="attachments-label">Attachments:</span>
                                </div>
                                <div class="attachments-list">
                                  <div v-for="(file, fileIdx) in question.file_uploads" :key="fileIdx" class="attachment-item">
                                    <span class="attachment-icon">📎</span>
                                    <span class="attachment-name">{{ file.name || file }}</span>
                                  </div>
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <!-- Enhanced no questions message -->
                  <div v-else class="no-questions-enhanced">
                    <div class="empty-state-enhanced">
                      <div class="empty-icon-enhanced">❓</div>
                      <h4>No Questions Available</h4>
                      <p>No questions found for this questionnaire response. Please select a questionnaire assignment to view questions and responses.</p>
                    </div>
                  </div>
                </div>
              </div>
            
            <!-- Enhanced Response Approval Configuration -->
            <div class="response-configuration-card card">
              <div class="card-header">
                <div class="config-header">
                  <div class="header-content">
                    <span class="header-icon-enhanced">⚙️</span>
                    <div>
                      <h3>Response Approval Configuration</h3>
                      <p class="header-subtitle">Configure approval parameters and review criteria for the selected response</p>
                    </div>
                  </div>
                  <div class="config-status">
                    <div class="status-indicator">
                      <span class="status-dot active"></span>
                      <span>Ready to Configure</span>
                    </div>
                  </div>
                </div>
              </div>
              
              <div class="card-body">
                <div class="configuration-grid">
                  <div class="config-section">
                    <div class="section-header">
                      <span class="section-icon">🎯</span>
                      <h4>Review Type & Priority</h4>
                    </div>
                    
                    <div class="form-row-enhanced">
                      <div class="form-item-enhanced">
                        <label class="form-label-enhanced">
                          <span class="label-icon">📋</span>
                          Response Type
                        </label>
                        <div class="select-wrapper-enhanced">
                          <select v-model="responseType" class="form-select-enhanced">
                            <option value="">Select response type</option>
                            <option value="questionnaire_review">Questionnaire Review</option>
                            <option value="vendor_response_review">Vendor Response Review</option>
                            <option value="compliance_assessment">Compliance Assessment</option>
                            <option value="risk_assessment">Risk Assessment</option>
                          </select>
                          <div class="select-arrow">▼</div>
                        </div>
                      </div>
                      
                      <div class="form-item-enhanced">
                        <label class="form-label-enhanced">
                          <span class="label-icon">⚡</span>
                          Priority Level
                        </label>
                        <div class="select-wrapper-enhanced">
                          <select v-model="responsePriority" class="form-select-enhanced">
                            <option value="">Select priority</option>
                            <option value="LOW">Low - Standard review timeline</option>
                            <option value="MEDIUM">Medium - Normal business priority</option>
                            <option value="HIGH">High - Expedited review required</option>
                            <option value="CRITICAL">Critical - Immediate attention needed</option>
                          </select>
                          <div class="select-arrow">▼</div>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div class="config-section">
                    <div class="section-header">
                      <span class="section-icon">📝</span>
                      <h4>Review Comments & Assessment Notes</h4>
                    </div>
                    
                    <div class="form-item-enhanced">
                      <label class="form-label-enhanced">
                        <span class="label-icon">💭</span>
                        Detailed Review Comments
                      </label>
                      <div class="textarea-wrapper">
                        <textarea
                          v-model="responseData"
                          class="form-textarea-enhanced"
                          rows="6"
                          placeholder="Enter detailed review comments, assessment notes, approval criteria, or any specific concerns that need to be addressed during the approval process..."
                          maxlength="1000"
                        ></textarea>
                        <div class="textarea-footer">
                          <div class="character-count">
                            <span class="count" :class="{ 'warning': responseData.length > 800, 'error': responseData.length >= 1000 }">
                              {{ responseData.length }}/1000
                            </span>
                          </div>
                          <div class="textarea-actions">
                            <button type="button" class="btn-text" @click="responseData = ''">Clear</button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Final Vendor Approval Form -->
          <div v-if="approvalType === 'final_vendor_approval'">
            <div class="alert alert-success">
              <div class="alert-icon">✅</div>
              <div class="alert-content">
                <div class="alert-title">Final Vendor Approval</div>
                <div class="alert-description">This approval type is used for final vendor decisions and approvals.</div>
              </div>
            </div>
            
            <!-- Vendor Details Display -->
            <div v-if="selectedVendor || true">
              <div class="vendor-details-card card" style="margin-bottom: 20px">
                <div class="card-header">
                  <div class="vendor-header">
                    <h3>Acme Corporation Vardaan</h3>
                    <div class="vendor-tags">
                      <span class="tag tag-success">low</span>
                      <span class="tag tag-default">cleared</span>
                    </div>
                  </div>
                </div>
                
                <div class="card-body">
                  <div class="row">
                    <div class="col-12">
                      <div class="form-item">
                        <label class="form-label">Vendor Code</label>
                        <input value="VEND00968" class="form-input" readonly />
                      </div>
                    </div>
                    <div class="col-12">
                      <div class="form-item">
                        <label class="form-label">Legal Name</label>
                        <input value="Acme Corporation Inc. Ltd. vardaan" class="form-input" readonly />
                      </div>
                    </div>
                  </div>
                  
                  <div class="row">
                    <div class="col-12">
                      <div class="form-item">
                        <label class="form-label">Business Type</label>
                        <input value="partnership" class="form-input" readonly />
                      </div>
                    </div>
                    <div class="col-12">
                      <div class="form-item">
                        <label class="form-label">Industry Sector</label>
                        <input value="technology" class="form-input" readonly />
                      </div>
                    </div>
                  </div>
                  
                  <div class="row">
                    <div class="col-12">
                      <div class="form-item">
                        <label class="form-label">Vendor Category</label>
                        <input value="services" class="form-input" readonly />
                      </div>
                    </div>
                    <div class="col-12">
                      <div class="form-item">
                        <label class="form-label">Website</label>
                        <input value="https://acme.com" class="form-input" readonly />
                      </div>
                    </div>
                  </div>
                  
                  <div class="form-item">
                    <label class="form-label">Description</label>
                    <textarea
                      value=""
                      class="form-textarea"
                      rows="2"
                      readonly
                    ></textarea>
                  </div>
                  
                  <div class="vendor-access-info">
                    <div class="row">
                      <div class="col-8">
                        <div class="form-item">
                          <label class="form-label">Data Access</label>
                          <span class="tag tag-info">No</span>
                        </div>
                      </div>
                      <div class="col-8">
                        <div class="form-item">
                          <label class="form-label">System Access</label>
                          <span class="tag tag-info">No</span>
                        </div>
                      </div>
                      <div class="col-8">
                        <div class="form-item">
                          <label class="form-label">Employee Count</label>
                          <input value="500" class="form-input" readonly />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Vendor Risks Display -->
            <div v-if="selectedVendor && (internalRisks.length > 0 || externalRisks.length > 0)">
              <div class="vendor-risks-card card" style="margin-bottom: 20px">
                <div class="card-header">
                  <div class="risks-header">
                    <h3>Vendor Risk Assessment</h3>
                    <div class="risk-summary-tags">
                      <span class="tag tag-info">Total: {{ riskSummary.total_risks || (internalRisks.length + externalRisks.length) }}</span>
                      <span class="tag tag-primary">Internal: {{ internalRisks.length }}</span>
                      <span class="tag tag-warning">External: {{ externalRisks.length }}</span>
                      <span v-if="riskSummary.high_priority > 0" class="tag tag-danger">High: {{ riskSummary.high_priority }}</span>
                      <span v-if="riskSummary.medium_priority > 0" class="tag tag-warning">Medium: {{ riskSummary.medium_priority }}</span>
                      <span v-if="riskSummary.low_priority > 0" class="tag tag-success">Low: {{ riskSummary.low_priority }}</span>
                    </div>
                  </div>
                </div>
                
                <div class="card-body">
                  <div class="risk-overview">
                    <div class="row" style="margin-bottom: 20px">
                      <div class="col-8">
                        <div class="risk-stat">
                          <span class="stat-label">Internal Risks:</span>
                          <span :class="internalRisks.length > 0 ? 'tag-primary' : 'tag-success'" class="tag">
                            {{ internalRisks.length }}
                          </span>
                        </div>
                      </div>
                      <div class="col-8">
                        <div class="risk-stat">
                          <span class="stat-label">External Risks:</span>
                          <span :class="externalRisks.length > 0 ? 'tag-warning' : 'tag-success'" class="tag">
                            {{ externalRisks.length }}
                          </span>
                        </div>
                      </div>
                      <div class="col-8">
                        <div class="risk-stat">
                          <span class="stat-label">Escalated:</span>
                          <span :class="externalRisks.filter(r => r.resolution_status === 'ESCALATED').length > 0 ? 'tag-danger' : 'tag-success'" class="tag">
                            {{ externalRisks.filter(r => r.resolution_status === 'ESCALATED').length }}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <!-- Risk sections would continue here with similar conversions -->
                  
                  <!-- No Risks Message -->
                  <div v-if="internalRisks.length === 0 && externalRisks.length === 0" class="no-risks-section">
                    <div class="empty">
                      <div class="empty-image">✅</div>
                      <h6 class="empty-title">No Escalated Risks Found</h6>
                      <p class="empty-description">No internal risks or external screening escalations identified for this vendor.</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Tab Navigation Buttons -->
        <div class="tab-actions">
          <button type="button" class="btn btn-secondary btn-tab-nav" @click="activeTab = 'request'">
            BACK TO REQUEST
          </button>
          <button type="button" class="btn btn-primary btn-tab-nav" @click="activeTab = 'stages'">
            STAGES CONFIGURATION
          </button>
        </div>
        </div>
        </div>
        
        <!-- Stages Configuration Tab -->
        <div v-show="activeTab === 'stages'" class="tab-content">
        
        <div class="stages-section">
          <div class="stages-header">
            <h3>Workflow Stages</h3>
            <button type="button" class="btn btn-primary" @click="addStage">
              <span class="icon">+</span>
              Add Stage
            </button>
          </div>

          <div v-if="stages.length === 0" class="no-stages">
            <div class="empty">
              <div class="empty-image">📋</div>
              <div class="empty-description">No stages configured yet</div>
              <button type="button" class="btn btn-primary empty-action" @click="addStage">Add First Stage</button>
            </div>
          </div>

          <div v-else class="stages-list">
            <div 
              v-for="(stage, index) in (stages || [])" 
              :key="index" 
              class="stage-card card"
            >
              <div class="card-header">
                <div class="stage-header">
                  <span class="stage-title">{{ getStageTitle(index + 1) }}</span>
                  <div class="stage-actions">
                    <button 
                      v-if="workflowForm.workflow_type === 'MULTI_LEVEL' && index > 0" 
                      type="button"
                      class="btn-icon" 
                      @click="moveStage(index, 'up')"
                    >
                      ↑
                    </button>
                    <button 
                      v-if="workflowForm.workflow_type === 'MULTI_LEVEL' && index < stages.length - 1" 
                      type="button"
                      class="btn-icon" 
                      @click="moveStage(index, 'down')"
                    >
                      ↓
                    </button>
                    <button 
                      type="button"
                      class="btn-icon btn-danger" 
                      @click="removeStage(index)"
                      title="Delete Stage"
                      aria-label="Delete Stage"
                    >
                      🗑️
                    </button>
                  </div>
                </div>
              </div>

              <div class="card-body">
                <div class="row">
                  <div class="col-12">
                    <div class="form-item">
                      <label class="form-label">{{ workflowForm.workflow_type === 'MULTI_PERSON' ? 'Approval Name' : `${getStageTitle(index + 1)} Name` }}</label>
                      <input 
                        v-model.lazy="stage.stage_name" 
                        type="text"
                        class="form-input"
                        :placeholder="workflowForm.workflow_type === 'MULTI_PERSON' ? requestForm.request_title || 'Enter approval name' : getStagePlaceholder(index + 1)"
                        :readonly="workflowForm.workflow_type === 'MULTI_PERSON'"
                      />
                    </div>
                  </div>
                  <!-- Weightage field for MULTI_PERSON / response approval workflows -->
                  <div 
                    class="col-12" 
                    v-if="workflowForm.workflow_type === 'MULTI_PERSON' && approvalType === 'response_approval'"
                  >
                    <div class="form-item">
                      <label class="form-label">Weightage</label>
                      <input
                        v-model.number="stage.weightage"
                        type="number"
                        class="form-input"
                        min="0"
                        max="100"
                        placeholder="Enter weightage for this approver (e.g., 25)"
                      />
                    </div>
                  </div>
                  <div class="col-12" v-if="workflowForm.workflow_type === 'MULTI_LEVEL'">
                    <div class="form-item">
                      <label class="form-label">{{ getStageTitle(index + 1) }} Order</label>
                      <input 
                        v-model.number="stage.stage_order" 
                        type="number"
                        class="form-input"
                        :min="1" 
                        :max="stages.length"
                      />
                    </div>
                  </div>
                </div>

                <div class="row">
                  <div class="col-12">
                    <div class="form-item">
                      <label class="form-label">Assigned User</label>
                      <select 
                        v-model="stage.assigned_user_id" 
                        class="form-select"
                        @change="(value) => handleUserSelection(stage, value)"
                        :disabled="loadingUsers"
                      >
                        <option value="">Select user</option>
                        <option
                          v-for="user in (users || [])"
                          :key="user.id"
                          :value="user.id"
                        >
                          {{ getUserDisplayName(user) }}
                        </option>
                      </select>
                    </div>
                  </div>
                </div>
                <!-- Hidden auto-populated fields -->
                <div class="form-item" style="display: none;">
                  <input v-model="stage.assigned_user_name" type="hidden" />
                  <input v-model="stage.assigned_user_role" type="hidden" />
                  <input v-model="stage.department" type="hidden" />
                </div>
                <div class="row">
                  <div class="col-12">
                    <div class="form-item">
                      <label class="form-label">Department</label>
                      <input 
                        v-model="stage.department" 
                        type="text"
                        class="form-input"
                        placeholder="Auto-populated from user"
                        readonly
                      />
                    </div>
                  </div>
                </div>

                <div class="row">
                  <div class="col-12">
                    <div class="form-item">
                      <label class="form-label">Deadline Date</label>
                      <input
                        v-model="stage.deadline_date"
                        type="date"
                        class="form-input"
                        :min="new Date().toISOString().split('T')[0]"
                      />
                    </div>
                  </div>
                </div>

                <div class="form-item">
                  <label class="form-label">{{ getStageTitle(index + 1) }} Description</label>
                  <textarea 
                    v-model.lazy="stage.stage_description" 
                    class="form-textarea"
                    rows="2"
                    placeholder="Describe what this stage involves..."
                  ></textarea>
                </div>

                <div class="form-item">
                  <label class="checkbox-label">
                    <input type="checkbox" v-model="stage.is_mandatory" />
                    This stage is mandatory
                  </label>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Tab Navigation Buttons -->
        <div class="tab-actions">
          <button type="button" class="btn btn-secondary btn-tab-nav" @click="activeTab = 'data'">
            BACK TO DATA
          </button>
        </div>
        </div>

        <!-- Form Actions -->
        
        <div class="form-actions">
          <button type="button" class="btn btn-secondary" @click="resetForm">Reset</button>
          <button type="submit" class="btn btn-primary" :disabled="submitting">
            {{ submitting ? 'Creating...' : 'Create Workflow & Request' }}
          </button>
        </div>
      </form>
    </div>

    <!-- Success Dialog -->
    <div v-if="successDialogVisible" class="dialog-overlay" @click="successDialogVisible = false">
      <div class="dialog" @click.stop>
        <div class="dialog-header">
          <h3>Workflow & Request Created Successfully</h3>
          <button class="dialog-close" @click="successDialogVisible = false">×</button>
        </div>
        <div class="dialog-body">
          <div class="success-content">
            <div class="success-icon">✅</div>
            <h3>Success!</h3>
            <p>Your workflow and approval request have been created successfully.</p>
            <div class="workflow-info">
              <p><strong>Workflow ID:</strong> {{ createdWorkflowId }}</p>
              <p><strong>Request ID:</strong> {{ createdRequestId }}</p>
              <p><strong>Workflow Type:</strong> {{ getWorkflowTypeLabel(workflowForm.workflow_type) }}</p>
              <p><strong>Stages:</strong> {{ stages.length }}</p>
              <p><strong>Status:</strong> <span class="tag tag-warning">PENDING</span></p>
            </div>
          </div>
        </div>
        <div class="dialog-footer">
          <button class="btn btn-secondary" @click="successDialogVisible = false">Close</button>
          <button class="btn btn-primary" @click="createAnother">Create Another</button>
        </div>
      </div>
    </div>

    <!-- Help Dialog -->
    <div v-if="helpDialogVisible" class="dialog-overlay" @click="helpDialogVisible = false">
      <div class="dialog" @click.stop>
        <div class="dialog-header">
          <h3>JSON Payload Help</h3>
          <button class="dialog-close" @click="helpDialogVisible = false">×</button>
        </div>
        <div class="dialog-body">
          <div class="help-content">
            <h4>Understanding JSON Payloads</h4>
            <p>The JSON payload is the core data that needs approval. It can contain any structure your business module requires.</p>
            
            <h5>Examples:</h5>
            <ul>
              <li><strong>Policy:</strong> policy content, effective dates, scope</li>
              <li><strong>Contract:</strong> terms, amounts, vendor details</li>
              <li><strong>Purchase:</strong> items, quantities, prices, suppliers</li>
            </ul>
            
            <h5>Tips:</h5>
            <ul>
              <li>Use the "Format JSON" button to make your JSON readable</li>
              <li>Use the "Validate JSON" button to check syntax</li>
              <li>Load sample payloads for reference</li>
              <li>Ensure all required fields are included</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Popup Modal -->
  <PopupModal />
</template>

<script>
import { ref, reactive, computed, onMounted, shallowRef, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/utils/api'
import { getMockUsers } from '@/services/users'
import PopupModal from '@/popup/PopupModal.vue'
import { PopupService } from '@/popup/popupService'
import { useNotifications } from '@/composables/useNotifications'
import notificationService from '@/services/notificationService'
import { useVendorPermissions } from '@/composables/useVendorPermissions'
import AccessDenied from '@/components/AccessDenied.vue'
import permissionsService from '@/services/permissionsService'

export default {
  name: 'ComprehensiveWorkflowCreator',
  components: {
    PopupModal,
    AccessDenied
  },
  setup() {
    const route = useRoute()
    const { showSuccess, showError, showWarning, showInfo } = useNotifications()
    
    // Initialize RBAC permissions
    const { permissions, showDeniedAlert } = useVendorPermissions()
    
    // Check if user has permission to access this page
    const hasAccess = ref(false)
    const accessDeniedInfo = ref({
      message: 'You do not have permission to create workflows',
      code: '403',
      permission: 'SubmitVendorForApproval',
      permissionRequired: 'vendor_create'
    })
    const workflowForm = reactive({
      workflow_name: '',
      workflow_type: 'MULTI_LEVEL',
      description: '',
      business_object_type: 'Vendor',
      created_by: '', // Will be set from authenticated user API
    })
    
    const requestForm = reactive({
      request_title: '',
      request_description: '',
      requester_id: null,
      requester_name: '',
      requester_department: '',
      business_object_type: 'Vendor',
      business_object_id: '',
      priority: 'MEDIUM',
      request_data: {}
    })
    
    // Use shallowRef for large objects to improve performance
    const stages = ref([])
    const users = shallowRef([])
    const loadingUsers = ref(false)

    // Fetch authenticated user from backend API
    const fetchAuthenticatedUser = async () => {
      try {
        console.log('Fetching authenticated user from /api/v1/vendor-approval/users/me/')
        const response = await api.get('/api/v1/vendor-approval/users/me/')
        const user = response.data
        
        console.log('Authenticated user from API:', user)
        
        // Extract user information from API response
        const userId = user.id
        const userName = user.first_name && user.last_name 
          ? `${user.first_name} ${user.last_name}`.trim()
          : user.username || user.email || ''
        const userDept = user.department || ''
        
        const currentUser = {
          id: userId,
          name: userName,
          username: user.username,
          email: user.email,
          department: userDept
        }
        
        console.log('Parsed authenticated user:', currentUser)
        return currentUser
      } catch (error) {
        console.error('Error fetching authenticated user from API:', error)
        throw error // Re-throw to let caller handle
      }
    }

    
    // Update created_by when component mounts and fetch users
    onMounted(async () => {
      console.log('ApprovalWorkflowCreator component mounted')
      
      // Check permission before loading any data
      // User must have SubmitVendorForApproval permission to create workflows
      // First check localStorage, then check backend API if needed
      let hasPermission = permissions.value.canSubmitForApproval
      console.log('Initial permission check from localStorage:', hasPermission)
      
      // Always check backend API to ensure we have the latest permissions
      // This is important because permissions might have changed or localStorage might be stale
      try {
        console.log('Checking backend API for submit_vendor_for_approval permission...')
        const backendPermission = await permissionsService.checkVendorPermission('submit_vendor_for_approval')
        console.log('Backend permission check result:', backendPermission)
        
        // Use backend result as the source of truth
        hasPermission = backendPermission
        
        // If we got permission from backend, update localStorage for future checks
        if (hasPermission) {
          // Update user object in localStorage with permission
          let userStr = localStorage.getItem('user')
          if (!userStr) {
            userStr = localStorage.getItem('current_user')
          }
          
          if (userStr) {
            try {
              const user = JSON.parse(userStr)
              if (!user.permissions) {
                user.permissions = {}
              }
              user.permissions.SubmitVendorForApproval = true
              // Save to both keys for compatibility
              localStorage.setItem('user', JSON.stringify(user))
              if (localStorage.getItem('current_user')) {
                localStorage.setItem('current_user', JSON.stringify(user))
              }
              console.log('Updated localStorage with permission')
            } catch (e) {
              console.error('Error updating localStorage:', e)
            }
          }
        }
      } catch (error) {
        console.error('Error checking permission from backend:', error)
        // If backend check fails, fall back to localStorage check
        // This allows the page to work if there's a temporary network issue
        console.log('Falling back to localStorage permission check due to backend error')
        hasPermission = permissions.value.canSubmitForApproval
      }
      
      if (!hasPermission) {
        console.warn('Access denied: User does not have SubmitVendorForApproval permission')
        hasAccess.value = false
        
        // Store error info in sessionStorage for AccessDenied component
        sessionStorage.setItem('access_denied_error', JSON.stringify({
          message: 'You do not have permission to create workflows. This page requires the permission to submit vendors for approval.',
          code: '403',
          path: route.path,
          permission: 'SubmitVendorForApproval',
          permissionRequired: 'vendor_create'
        }))
        
        return // Exit early without loading data
      }
      
      hasAccess.value = true
      await fetchUsers()

      // Fetch authenticated user from backend API (no fallbacks)
      try {
        const currentUser = await fetchAuthenticatedUser()
        if (currentUser && currentUser.name) {
          workflowForm.created_by = currentUser.name
          requestForm.requester_id = currentUser.id
          requestForm.requester_name = currentUser.name
          requestForm.requester_department = currentUser.department || ''
          console.log('Authenticated user loaded and set:', currentUser)
          console.log('workflowForm.created_by set to:', workflowForm.created_by)
        } else {
          console.error('Authenticated user data is incomplete:', currentUser)
          showError('Failed to load user information. Please refresh the page.')
        }
      } catch (error) {
        console.error('Failed to fetch authenticated user:', error)
        showError('Failed to load user information. Please refresh the page.')
        // Don't set any fallback values - leave fields empty
      }
      
      // Auto-expand the first question by default
      activeQuestionCollapse.value = ['q1']
      console.log('Initial activeQuestionCollapse:', activeQuestionCollapse.value)
      
      // Add watchers for debugging
      watch(() => selectedQuestionnaireData.value, (newVal) => {
        console.log('selectedQuestionnaireData changed:', newVal)
      }, { deep: true })
      
      watch(() => selectedAssignmentData.value, (newVal) => {
        console.log('selectedAssignmentData changed:', newVal)
      }, { deep: true })
      
      // Watch for changes to created_by to debug and prevent reset to 'GRC Administrator'
      watch(() => workflowForm.created_by, async (newVal, oldVal) => {
        console.log('workflowForm.created_by changed from', oldVal, 'to:', newVal)
        // If someone tries to set it back to 'GRC Administrator' or other invalid values, restore from API
        if (newVal === 'GRC Administrator' || newVal === 'Current User' || newVal.startsWith('User ')) {
          try {
            const currentUser = await fetchAuthenticatedUser()
            if (currentUser && currentUser.name) {
              console.warn('Prevented reset to invalid value, restoring authenticated user name:', currentUser.name)
              workflowForm.created_by = currentUser.name
            }
          } catch (error) {
            console.error('Failed to restore user name from API:', error)
          }
        }
      })
      
      // Check if we need to auto-populate from query parameters
      console.log('Component mounted, checking route query:', route.query)
      if (route.query.auto_populate === 'true') {
        console.log('Auto-populate flag detected, starting auto-population...')
        await handleAutoPopulateFromQuery()
      } else {
        console.log('No auto-populate flag, normal page load')
      }
    })
    
    // Function to handle auto-population from query parameters
    const handleAutoPopulateFromQuery = async () => {
      try {
        console.log('Auto-populating from query parameters:', route.query)
        
        // Set workflow type
        if (route.query.workflow_type) {
          workflowForm.workflow_type = route.query.workflow_type
          console.log('Set workflow type to:', route.query.workflow_type)
        }
        
        // Set approval type
        if (route.query.approval_type) {
          approvalType.value = route.query.approval_type
          console.log('Set approval type to:', route.query.approval_type)
          
          // If it's questionnaire approval, fetch questionnaires
          if (route.query.approval_type === 'questionnaire_approval') {
            console.log('Fetching questionnaires...')
            await fetchQuestionnaires()
            
            // Wait a bit for questionnaires to load
            await new Promise(resolve => setTimeout(resolve, 1000))
            console.log('Questionnaires loaded:', questionnaires.value.length)
            
            // Select the questionnaire if ID is provided
            if (route.query.questionnaire_id) {
              console.log('Looking for questionnaire ID:', route.query.questionnaire_id)
              
              // If no questionnaires loaded from API, create mock data
              if (questionnaires.value.length === 0) {
                console.log('No questionnaires from API, creating mock data')
                questionnaires.value = [{
                  questionnaire_id: route.query.questionnaire_id,
                  questionnaire_name: route.query.questionnaire_name || 'Test Questionnaire',
                  questionnaire_type: route.query.questionnaire_type || 'ONBOARDING',
                  description: 'Auto-generated questionnaire for approval',
                  version: '1.0',
                  created_at: new Date().toISOString(),
                  vendor_id: route.query.vendor_id // Include vendor_id from query parameters
                }]
              }
              
              selectedQuestionnaire.value = route.query.questionnaire_id
              
              // Find and populate questionnaire data
              const questionnaire = questionnaires.value.find(q => 
                String(q.questionnaire_id) === String(route.query.questionnaire_id)
              )
              
              console.log('Found questionnaire:', questionnaire)
              
              if (questionnaire) {
                // Capture vendor_id from URL query parameters
                const vendorIdFromUrl = route.query.vendor_id
                console.log('Vendor ID from URL query:', vendorIdFromUrl)
                
                // Set vendor_id in business_object_id for backend
                if (vendorIdFromUrl) {
                  requestForm.business_object_id = vendorIdFromUrl
                  console.log('Set requestForm.business_object_id to:', vendorIdFromUrl)
                }
                
                selectedQuestionnaireData.value = {
                  questionnaire_id: questionnaire.questionnaire_id,
                  questionnaire_name: questionnaire.questionnaire_name,
                  questionnaire_type: questionnaire.questionnaire_type,
                  description: questionnaire.description,
                  version: questionnaire.version,
                  created_at: questionnaire.created_at,
                  approval_type: 'questionnaire_approval',
                  vendor_id: vendorIdFromUrl // Include vendor_id from query parameters
                }
                
                // Auto-populate request title and workflow name
                const defaultTitle = `${questionnaire.questionnaire_name} Approval`
                requestForm.request_title = defaultTitle
                workflowForm.workflow_name = `${questionnaire.questionnaire_name} Approval Workflow`
                requestForm.request_description = `Approval request for ${questionnaire.questionnaire_name} (${questionnaire.questionnaire_type})`
                
                console.log('Auto-populated questionnaire data:', selectedQuestionnaireData.value)
                console.log('Vendor ID from query:', route.query.vendor_id)
                
                // Set auto-population indicators
                isAutoPopulated.value = true
                autoPopulateMessage.value = `Questionnaire "${questionnaire.questionnaire_name}" has been automatically loaded. Please add approval stages and submit the workflow.`
                
                showMessage('Questionnaire data loaded successfully! Please configure approval stages and submit.', 'success')
                
                // Scroll to the request data section smoothly
                setTimeout(() => {
                  const requestDataSection = document.querySelector('.payload-section')
                  if (requestDataSection) {
                    requestDataSection.scrollIntoView({ behavior: 'smooth', block: 'center' })
                  }
                }, 1000)
              } else {
                console.error('Questionnaire not found with ID:', route.query.questionnaire_id)
                showMessage('Questionnaire not found. Please select manually.', 'warning')
              }
            }
          }
        }
      } catch (error) {
        console.error('Error auto-populating from query:', error)
        isAutoPopulated.value = false
        autoPopulateMessage.value = ''
        showMessage('Failed to auto-populate some data. Please fill in manually.', 'warning')
      }
    }

    // Watch for request title changes and update stage names for Team Approval workflows
    watch(() => requestForm.request_title, (newTitle) => {
      if (workflowForm.workflow_type === 'MULTI_PERSON' && newTitle) {
        stages.value.forEach(stage => {
          stage.stage_name = newTitle
        })
      }
    })

    // Watch for workflow type changes and update stage names accordingly
    watch(() => workflowForm.workflow_type, (newType) => {
      if (newType === 'MULTI_PERSON' && requestForm.request_title) {
        stages.value.forEach(stage => {
          stage.stage_name = requestForm.request_title
        })
      } else if (newType === 'MULTI_LEVEL') {
        stages.value.forEach((stage, index) => {
          stage.stage_name = ''
        })
      }
      
      // Reset approval type when workflow type changes
      approvalType.value = ''
      selectedQuestionnaire.value = ''
      questionnaires.value = []
      selectedQuestionnaireData.value = {}
      responseType.value = ''
      responseData.value = ''
      responsePriority.value = 'MEDIUM'
      selectedQuestionnaireAssignment.value = ''
      questionnaireAssignments.value = []
      selectedAssignmentData.value = {}
      finalApprovalType.value = ''
      vendorInfo.value = ''
      decisionCriteria.value = ''
      businessImpact.value = 'MEDIUM'
      selectedVendor.value = ''
      vendors.value = []
      selectedVendorData.value = {}
      vendorRisks.value = []
      riskSummary.value = {}
      activeRiskCollapse.value = []
      activeQuestionCollapse.value = []
    })
    
    const fetchUsers = async () => {
      try {
        loadingUsers.value = true
        const response = await api.get('/api/v1/vendor-approval/users/')
        users.value = response.data
      } catch (error) {
        console.error('Error fetching users:', error)
        users.value = getMockUsers()
        showMessage('Using mock user data - API endpoint not available', 'warning')
      } finally {
        loadingUsers.value = false
      }
    }

    const submitting = ref(false)
    const successDialogVisible = ref(false)
    const createdWorkflowId = ref('')
    const createdRequestId = ref('')
    const helpDialogVisible = ref(false)
    const jsonPayloadString = ref('')
    const approvalType = ref('')
    const selectedQuestionnaire = ref('')
    const questionnaires = ref([])
    const loadingQuestionnaires = ref(false)
    const selectedQuestionnaireData = ref({})
    const responseType = ref('')
    const responseData = ref('')
    const responsePriority = ref('MEDIUM')
    const workflowFormRef = ref()
    
    // Questionnaire assignment variables for response approval
    const selectedQuestionnaireAssignment = ref('')
    const questionnaireAssignments = ref([])
    const loadingQuestionnaireAssignments = ref(false)
    const selectedAssignmentData = ref({})
    
    // Final Vendor Approval variables
    const finalApprovalType = ref('')
    const vendorInfo = ref('')
    const decisionCriteria = ref('')
    const businessImpact = ref('MEDIUM')
    
    // Vendor selection variables
    const selectedVendor = ref('')
    const vendors = ref([])
    const loadingVendors = ref(false)
    const selectedVendorData = ref({})
    
    // Vendor risks variables
    const vendorRisks = ref([]) // Keep for backward compatibility
    const internalRisks = ref([])
    const externalRisks = ref([])
    const riskSummary = ref({})
    const activeRiskCollapse = ref([]) // Keep for backward compatibility
    const activeInternalRiskCollapse = ref([])
    const activeExternalRiskCollapse = ref([])
    
    // Questions and responses variables
    const activeQuestionCollapse = ref([])
    
    // Auto-population indicator
    const isAutoPopulated = ref(false)
    const autoPopulateMessage = ref('')
    
    // Active tab for navigation
    const activeTab = ref('workflow')
    
    // Computed property for available approval types based on workflow type
    const availableApprovalTypes = computed(() => {
      if (workflowForm.workflow_type === 'MULTI_PERSON') {
        return [
          { label: 'Questionnaire Approval', value: 'questionnaire_approval' },
          { label: 'Response Approval', value: 'response_approval' }
        ]
      } else if (workflowForm.workflow_type === 'MULTI_LEVEL') {
        return [
          { label: 'Final Vendor Approval', value: 'final_vendor_approval' }
        ]
      }
      return []
    })

    // Simple message function to replace ElMessage
    const showMessage = (message, type = 'info') => {
      console.log(`${type.toUpperCase()}: ${message}`)
      // Use PopupService for consistent alerts
      if (type === 'error') {
        PopupService.error(message, 'Error')
      } else if (type === 'success') {
        PopupService.success(message, 'Success')
      } else if (type === 'warning') {
        PopupService.warning(message, 'Warning')
      } else {
        PopupService.success(message, 'Info')
      }
    }

    // Simple confirm function to replace ElMessageBox
    const showConfirm = (message, title = 'Confirm') => {
      return new Promise((resolve) => {
        PopupService.confirm(
          message,
          title,
          () => resolve(true),
          () => resolve(false)
        )
      })
    }

    const addStage = () => {
      const newStage = {
        stage_order: getDefaultStageOrder(),
        stage_name: workflowForm.workflow_type === 'MULTI_PERSON' ? requestForm.request_title : '',
        stage_description: '',
        // New field used for MULTI_PERSON / response approval workflows
        weightage: workflowForm.workflow_type === 'MULTI_PERSON' && approvalType.value === 'response_approval' ? 0 : null,
        assigned_user_id: null,
        assigned_user_name: '',
        assigned_user_role: '',
        department: '2',
        stage_type: workflowForm.workflow_type === 'MULTI_PERSON' ? 'PARALLEL' : 'SEQUENTIAL',
        deadline_date: null,
        is_mandatory: true
      }
      stages.value.push(newStage)
    }

    const removeStage = async (index) => {
      const confirmed = await showConfirm('Are you sure you want to remove this stage?', 'Warning')
      if (confirmed) {
        stages.value.splice(index, 1)
        // Reorder remaining stages based on workflow type
        if (workflowForm.workflow_type === 'MULTI_LEVEL') {
          stages.value.forEach((stage, idx) => {
            stage.stage_order = idx + 1
          })
        } else {
          // For MULTI_PERSON, keep stage_order as 0
          stages.value.forEach((stage, idx) => {
            stage.stage_order = 0
          })
        }
        showMessage('Stage removed successfully', 'success')
      }
    }

    const moveStage = (index, direction) => {
      // Only allow reordering for MULTI_LEVEL workflows
      if (workflowForm.workflow_type !== 'MULTI_LEVEL') {
        return
      }
      
      if (direction === 'up' && index > 0) {
        const temp = stages.value[index]
        stages.value[index] = stages.value[index - 1]
        stages.value[index - 1] = temp
        // Update stage orders
        stages.value.forEach((stage, idx) => {
          stage.stage_order = idx + 1
        })
      } else if (direction === 'down' && index < stages.value.length - 1) {
        const temp = stages.value[index]
        stages.value[index] = stages.value[index + 1]
        stages.value[index + 1] = temp
        // Update stage orders
        stages.value.forEach((stage, idx) => {
          stage.stage_order = idx + 1
        })
      }
    }

    const validateStages = () => {
      if (stages.value.length === 0) {
        showMessage('At least one stage is required', 'error')
        return false
      }

      for (let i = 0; i < stages.value.length; i++) {
        const stage = stages.value[i]
        if (!stage.stage_name || !stage.assigned_user_id || !stage.deadline_date) {
          showMessage(`Stage ${i + 1} is missing required information (name, user, or deadline)`, 'error')
          return false
        }
      }

      return true
    }

    const submitWorkflow = async () => {
      try {
        // Validate workflow form
        if (!workflowForm.workflow_name || !workflowForm.workflow_name.trim()) {
          showMessage('Workflow name is required', 'error')
          activeTab.value = 'workflow'
          return
        }

        // Validate request form
        if (!requestForm.request_title || !requestForm.request_title.trim()) {
          showMessage('Request title is required', 'error')
          activeTab.value = 'request'
          return
        }

        // Validate stages
        if (!validateStages()) {
          activeTab.value = 'stages'
          return
        }

        // Validate approval type and related data
        if (approvalType.value === 'questionnaire_approval' && !selectedQuestionnaire.value) {
          showMessage('Please select a questionnaire', 'error')
          activeTab.value = 'data'
          return
        }

        if (approvalType.value === 'response_approval' && !selectedQuestionnaireAssignment.value) {
          showMessage('Please select a questionnaire assignment', 'error')
          activeTab.value = 'data'
          return
        }

        if (approvalType.value === 'final_vendor_approval' && !selectedVendor.value) {
          showMessage('Please select a vendor', 'error')
          activeTab.value = 'data'
          return
        }

        submitting.value = true

        // Prepare the submission data
        const requestData = getRequestData()
        
        // Get vendor_id from multiple sources, but allow it to be undefined for questionnaire-only approvals
        const vendorId = requestData.vendor_id || 
                        requestData.business_object_id ||
                        requestForm.business_object_id || 
                        route.query.vendor_id ||
                        (selectedQuestionnaireData.value && selectedQuestionnaireData.value.vendor_id) ||
                        (selectedAssignmentData.value && selectedAssignmentData.value.vendor_id) ||
                        selectedVendor.value ||
                        null
        
        console.log('ApprovalWorkflowCreator - Final vendor_id being sent:', vendorId)
        console.log('ApprovalWorkflowCreator - requestData structure:', requestData)
        console.log('ApprovalWorkflowCreator - Approval type:', approvalType.value)
        
        // Remove undefined values from requestData to prevent serialization issues
        const cleanRequestData = Object.fromEntries(
          Object.entries(requestData).filter(([_, v]) => v !== undefined && v !== null)
        )
        
        const submitData = {
          workflow: {
            ...workflowForm,
            business_object_type: workflowForm.business_object_type || requestForm.business_object_type || 'Vendor'
          },
          request: {
            ...requestForm,
            business_object_type: workflowForm.business_object_type || requestForm.business_object_type || 'Vendor',
            request_data: cleanRequestData
          },
          stages: stages.value.map(stage => {
            const stageData = {
              ...stage,
              deadline_date: stage.deadline_date ? new Date(stage.deadline_date).toISOString() : null
            }
            
            // Remove weightage if it's null or not applicable
            // Only include weightage for MULTI_PERSON response_approval workflows
            if (stageData.weightage === null || stageData.weightage === undefined || 
                !(workflowForm.workflow_type === 'MULTI_PERSON' && approvalType.value === 'response_approval')) {
              delete stageData.weightage
            }
            
            return stageData
          })
        }
        
        // Only add vendor_id and business_object_id if they exist
        // Some approval types (like questionnaire-only) might not require vendor_id
        if (vendorId) {
          submitData.vendor_id = vendorId
          submitData.business_object_id = vendorId
        }
        
        console.log('Submitting comprehensive workflow:', JSON.stringify(submitData, null, 2))
        
        const response = await api.post('/api/v1/vendor-approval/create-workflow-request/', submitData)
        
        createdWorkflowId.value = response.data.workflow_id
        createdRequestId.value = response.data.approval_id
        successDialogVisible.value = true
        
        showMessage('Workflow and request created successfully!', 'success')
        
        // Create notification
        await notificationService.createVendorSuccessNotification('workflow_created', {
          title: 'Workflow Created',
          message: 'Approval workflow and request created successfully!',
          workflow_id: response.data.workflow_id,
          approval_id: response.data.approval_id,
          workflow_name: workflowForm.workflow_name
        })
        
      } catch (error) {
        console.error('Error creating workflow and request:', error)
        console.error('Error response:', error.response)
        console.error('Error response data:', error.response?.data)
        console.error('Error response status:', error.response?.status)
        
        // Extract error message
        let errorMessage = 'Failed to create workflow and request'
        if (error.response?.data) {
          if (typeof error.response.data === 'string') {
            errorMessage = error.response.data
          } else if (error.response.data.error) {
            errorMessage = error.response.data.error
          } else if (error.response.data.details) {
            errorMessage = error.response.data.details
          } else if (error.response.data.message) {
            errorMessage = error.response.data.message
          }
        } else if (error.message) {
          errorMessage = error.message
        }
        
        showMessage(errorMessage, 'error')
        
        // Create error notification
        await notificationService.createVendorErrorNotification('create_workflow', errorMessage, {
          title: 'Workflow Creation Failed',
          workflow_name: workflowForm.workflow_name
        })
      } finally {
        submitting.value = false
      }
    }

    const resetForm = async () => {
      try {
        // Fetch authenticated user from API
        let currentUser = null
        try {
          currentUser = await fetchAuthenticatedUser()
        } catch (error) {
          console.error('Error fetching authenticated user in resetForm:', error)
        }

        // Reset all form data manually
        Object.assign(workflowForm, {
          workflow_name: '',
          workflow_type: 'MULTI_LEVEL',
          description: '',
          business_object_type: 'Vendor',
          created_by: currentUser ? currentUser.name : ''
        })

        Object.assign(requestForm, {
          request_title: '',
          request_description: '',
          requester_id: currentUser ? currentUser.id : null,
          requester_name: currentUser ? currentUser.name : '',
          requester_department: currentUser ? currentUser.department : '',
          business_object_type: 'Vendor',
          business_object_id: '',
          priority: 'MEDIUM',
          request_data: {}
        })
        
        stages.value = []
        jsonPayloadString.value = ''
        approvalType.value = ''
        selectedQuestionnaire.value = ''
        questionnaires.value = []
        selectedQuestionnaireData.value = {}
        responseType.value = ''
        responseData.value = ''
        responsePriority.value = 'MEDIUM'
        selectedQuestionnaireAssignment.value = ''
        questionnaireAssignments.value = []
        selectedAssignmentData.value = {}
        finalApprovalType.value = ''
        vendorInfo.value = ''
        decisionCriteria.value = ''
        businessImpact.value = 'MEDIUM'
        selectedVendor.value = ''
        vendors.value = []
        selectedVendorData.value = {}
        vendorRisks.value = []
        internalRisks.value = []
        externalRisks.value = []
        riskSummary.value = {}
        activeRiskCollapse.value = []
        activeInternalRiskCollapse.value = []
        activeExternalRiskCollapse.value = []
        activeQuestionCollapse.value = []
        
        showMessage('Form reset successfully', 'info')
      } catch (error) {
        console.error('Error resetting form:', error)
        showMessage('Failed to reset form', 'error')
      }
    }

    const createAnother = () => {
      successDialogVisible.value = false
      resetForm()
    }

    const getWorkflowTypeLabel = (type) => {
      return type === 'MULTI_LEVEL' ? 'Tiered Approval' : 'Team Approval'
    }
    
    const handleUserSelection = (stage, userId) => {
      const selectedUser = users.value.find(user => user.id === parseInt(userId))
      if (selectedUser) {
        stage.assigned_user_id = selectedUser.id
        stage.assigned_user_name = `${selectedUser.first_name} ${selectedUser.last_name}`
        stage.assigned_user_role = selectedUser.role
        stage.department = selectedUser.department
      }
    }
    
    const getUserDisplayName = (user) => {
      return `${user.first_name} ${user.last_name} (${user.role} - ${user.department})`
    }

    const showPayloadHelp = () => {
      helpDialogVisible.value = true
    }

    // Questionnaire handling functions
    const fetchQuestionnaires = async () => {
      try {
        loadingQuestionnaires.value = true
        console.log('Fetching questionnaires from API...')
        const response = await api.get('/api/v1/vendor-approval/questionnaires/active/')
        
        console.log('Questionnaires API response:', response)
        console.log('Response data:', response.data)
        console.log('Response data type:', typeof response.data)
        console.log('Is array:', Array.isArray(response.data))
        
        // Ensure we have proper data structure
        if (response.data && Array.isArray(response.data)) {
          questionnaires.value = response.data.map(q => ({
            questionnaire_id: q.questionnaire_id,
            questionnaire_name: q.questionnaire_name || 'Unnamed Questionnaire',
            questionnaire_type: q.questionnaire_type || 'CUSTOM',
            description: q.description || '',
            version: q.version || '1.0',
            created_at: q.created_at || new Date().toISOString()
          }))
        } else if (response.data && typeof response.data === 'object') {
          // Handle case where API returns object with questionnaires array
          const questionnairesArray = response.data.questionnaires || [];
          questionnaires.value = questionnairesArray.map(q => ({
            questionnaire_id: q.questionnaire_id,
            questionnaire_name: q.questionnaire_name || 'Unnamed Questionnaire',
            questionnaire_type: q.questionnaire_type || 'CUSTOM',
            description: q.description || '',
            version: q.version || '1.0',
            created_at: q.created_at || new Date().toISOString()
          }))
        } else {
          questionnaires.value = []
        }
        
        console.log('Fetched questionnaires:', questionnaires.value)
        console.log('Number of questionnaires:', questionnaires.value.length)
        
        if (questionnaires.value.length === 0) {
          showMessage('No questionnaires found in the database.', 'warning')
        } else {
          console.log('Successfully loaded', questionnaires.value.length, 'questionnaires')
        }
      } catch (error) {
        console.error('Error fetching questionnaires:', error)
        console.error('Error details:', {
          message: error.message,
          response: error.response,
          status: error.response?.status,
          statusText: error.response?.statusText,
          data: error.response?.data
        })
        
        // Check error type to provide better feedback
        const errorStatus = error.response?.status
        const errorMessage = error.response?.data?.error || error.response?.data?.details || error.message
        
        // For permission errors (403), show different message
        if (errorStatus === 403) {
          console.warn('Permission denied when fetching questionnaires. User may not have view_vendors permission.')
          showMessage('You do not have permission to view questionnaires. Please contact your administrator.', 'warning')
        } else if (errorStatus === 404) {
          console.warn('Questionnaires endpoint not found (404)')
          showMessage('Questionnaires endpoint not available. Using fallback data.', 'warning')
        } else {
          // For 500 or other server errors, show error but still use mock data
          console.warn('Server error when fetching questionnaires. Using fallback data.')
          showMessage('Unable to load questionnaires from server. Using fallback data for testing.', 'warning')
        }
        
        // Add mock data for testing if API fails
        // Only add if we don't already have questionnaires
        if (questionnaires.value.length === 0) {
          console.log('Adding mock questionnaires for testing...')
          questionnaires.value = [
            {
              questionnaire_id: '1',
              questionnaire_name: 'Vendor Onboarding Assessment',
              questionnaire_type: 'ONBOARDING',
              description: 'Standard questionnaire for new vendor onboarding process',
              version: '1.2',
              created_at: new Date().toISOString()
            },
            {
              questionnaire_id: '2',
              questionnaire_name: 'Annual Security Review',
              questionnaire_type: 'ANNUAL',
              description: 'Annual security assessment for existing vendors',
              version: '2.0',
              created_at: new Date().toISOString()
            }
          ]
          console.log('Mock questionnaires added:', questionnaires.value.length)
        }
      } finally {
        loadingQuestionnaires.value = false
      }
    }

    const handleApprovalTypeChange = (event) => {
      const value = event.target.value
      approvalType.value = value
      
      if (value === 'questionnaire_approval') {
        fetchQuestionnaires()
        // Reset other data
        selectedVendor.value = ''
        vendors.value = []
        selectedVendorData.value = {}
        selectedQuestionnaireAssignment.value = ''
        questionnaireAssignments.value = []
        selectedAssignmentData.value = {}
      } else if (value === 'response_approval') {
        fetchQuestionnaireAssignments()
        // Reset other data
        selectedQuestionnaire.value = ''
        questionnaires.value = []
        selectedVendor.value = ''
        vendors.value = []
        selectedVendorData.value = {}
      } else if (value === 'final_vendor_approval') {
        fetchVendors()
        // Reset other data
        selectedQuestionnaire.value = ''
        questionnaires.value = []
        selectedQuestionnaireAssignment.value = ''
        questionnaireAssignments.value = []
        selectedAssignmentData.value = {}
      } else {
        // Reset all data
        selectedQuestionnaire.value = ''
        questionnaires.value = []
        selectedQuestionnaireAssignment.value = ''
        questionnaireAssignments.value = []
        selectedAssignmentData.value = {}
        selectedVendor.value = ''
        vendors.value = []
        selectedVendorData.value = {}
      }
    }

    const handleQuestionnaireChange = (event) => {
      const questionnaireId = event.target.value
      selectedQuestionnaire.value = questionnaireId
      
      // Log for debugging
      console.log('Selected questionnaire ID:', questionnaireId)
      console.log('Available questionnaires:', questionnaires.value)
      
      // Convert to string for comparison if needed
      const questionnaire = questionnaires.value.find(q => String(q.questionnaire_id) === String(questionnaireId))
      console.log('Found questionnaire:', questionnaire)
      
      if (questionnaire) {
        // Get vendor_id from URL query if available
        const vendorIdFromUrl = route.query.vendor_id
        if (vendorIdFromUrl) {
          requestForm.business_object_id = vendorIdFromUrl
          console.log('handleQuestionnaireChange - Set business_object_id to:', vendorIdFromUrl)
        }
        
        // Store the questionnaire data for display - create a new object to ensure reactivity
        selectedQuestionnaireData.value = {
          questionnaire_id: questionnaire.questionnaire_id,
          questionnaire_name: questionnaire.questionnaire_name,
          questionnaire_type: questionnaire.questionnaire_type,
          description: questionnaire.description,
          version: questionnaire.version,
          created_at: questionnaire.created_at,
          approval_type: 'questionnaire_approval',
          vendor_id: vendorIdFromUrl || questionnaire.vendor_id // Include vendor_id from URL or questionnaire
        }
        
        console.log('Updated selectedQuestionnaireData:', selectedQuestionnaireData.value)
        
        // Also populate JSON payload for backend submission
        const questionnairePayload = {
          questionnaire_id: questionnaire.questionnaire_id,
          questionnaire_name: questionnaire.questionnaire_name,
          questionnaire_type: questionnaire.questionnaire_type,
          description: questionnaire.description,
          version: questionnaire.version,
          approval_type: 'questionnaire_approval'
        }
        jsonPayloadString.value = JSON.stringify(questionnairePayload, null, 2)
      }
    }

    const getQuestionnaireDisplayName = (questionnaire) => {
      return `${questionnaire.questionnaire_name} (${questionnaire.questionnaire_type} - v${questionnaire.version})`
    }

    const getQuestionnaireTypeColor = (type) => {
      const colorMap = {
        'ONBOARDING': 'tag-primary',
        'ANNUAL': 'tag-success',
        'INCIDENT': 'tag-warning',
        'CUSTOM': 'tag-info'
      }
      return colorMap[type] || 'tag-default'
    }

    const formatDate = (dateString) => {
      if (!dateString) return 'N/A'
      try {
        const date = new Date(dateString)
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString()
      } catch (e) {
        return dateString
      }
    }

    // Vendor handling functions
    const fetchVendors = async () => {
      try {
        loadingVendors.value = true
        const response = await api.get('/api/v1/vendor-approval/vendors/')
        vendors.value = response.data.vendors || []
        
        if (vendors.value.length === 0) {
          showMessage('No vendors found in the database.', 'warning')
        }
      } catch (error) {
        console.error('Error fetching vendors:', error)
        showMessage('Failed to load vendors from database.', 'error')
        vendors.value = []
      } finally {
        loadingVendors.value = false
      }
    }

    const handleVendorChange = async (event) => {
      const vendorId = event.target.value
      selectedVendor.value = vendorId
      
      try {
        if (!vendorId) {
          selectedVendorData.value = {}
          vendorRisks.value = []
          internalRisks.value = []
          externalRisks.value = []
          riskSummary.value = {}
          return
        }
        
        // Fetch detailed vendor information and risks in parallel
        const [vendorResponse, risksResponse] = await Promise.all([
          api.get(`/api/v1/vendor-approval/vendors/${vendorId}/`),
          api.get(`/api/v1/vendor-approval/vendors/${vendorId}/risks/`)
        ])
        
        selectedVendorData.value = vendorResponse.data
        
        // Process risks response to separate internal and external
        const risksData = risksResponse.data
        vendorRisks.value = risksData.risks || [] // Keep for backward compatibility
        
        // Separate internal and external risks
        // Backend already filters external risks for ESCALATED status
        internalRisks.value = risksData.internal_risks || risksData.risks || []
        externalRisks.value = risksData.external_risks || risksData.screening_risks || []
        
        riskSummary.value = risksData.risk_summary || {}
        
        // Update vendor info in the form
        const totalRisks = internalRisks.value.length + externalRisks.value.length
        vendorInfo.value = `Vendor: ${vendorResponse.data.company_name} (${vendorResponse.data.vendor_code}) - ${totalRisks} risks identified (${internalRisks.value.length} internal, ${externalRisks.value.length} external)`
        
      } catch (error) {
        console.error('Error fetching vendor details:', error)
        showMessage('Failed to load vendor details.', 'error')
        selectedVendorData.value = {}
        vendorRisks.value = []
        internalRisks.value = []
        externalRisks.value = []
        riskSummary.value = {}
      }
    }

    const getVendorDisplayName = (vendor) => {
      return `${vendor.company_name} (${vendor.vendor_code}) - ${vendor.business_type}`
    }

    const getVendorRiskColor = (riskLevel) => {
      const colorMap = {
        'LOW': 'tag-success',
        'MEDIUM': 'tag-warning',
        'HIGH': 'tag-danger',
        'CRITICAL': 'tag-danger'
      }
      return colorMap[riskLevel?.toUpperCase()] || 'tag-info'
    }

    const getVendorStatusColor = (status) => {
      const colorMap = {
        'ACTIVE': 'tag-success',
        'INACTIVE': 'tag-info',
        'PENDING': 'tag-warning',
        'SUSPENDED': 'tag-danger',
        'TERMINATED': 'tag-danger'
      }
      return colorMap[status?.toUpperCase()] || 'tag-info'
    }

    // Questionnaire assignment handling functions
    const fetchQuestionnaireAssignments = async () => {
      try {
        loadingQuestionnaireAssignments.value = true
        // This endpoint now returns questionnaires with status='RESPONDED'
        const response = await api.get('/api/v1/vendor-approval/questionnaire-assignments/submitted/')
        
        // Process the response data
        if (response.data && response.data.assignments) {
          questionnaireAssignments.value = response.data.assignments.map(a => ({
            assignment_id: a.assignment_id,
            questionnaire_id: a.questionnaire_id,
            questionnaire_name: a.questionnaire_name || 'Unnamed Questionnaire',
            questionnaire_type: a.questionnaire_type || 'CUSTOM',
            questionnaire_description: a.questionnaire_description || '',
            questionnaire_version: a.questionnaire_version || '1.0',
            submission_date: a.submission_date || new Date().toISOString(),
            overall_score: a.overall_score || 0,
            status: a.status || 'SUBMITTED',
            vendor_id: a.vendor_id,
            vendor_company_name: a.vendor_company_name || 'Unknown Vendor',
            vendor_code: a.vendor_code || 'N/A',
            vendor_legal_name: a.vendor_legal_name,
            vendor_business_type: a.vendor_business_type,
            response_statistics: a.response_statistics || {
              total_questions: 0,
              completed_questions: 0,
              required_questions: 0,
              completion_percentage: 0
            },
            questions_and_responses: a.questions_and_responses || [],
            notes: a.notes || ''
          }))
        } else {
          questionnaireAssignments.value = []
        }
        
        console.log('Fetched questionnaire assignments:', questionnaireAssignments.value)
        
        if (questionnaireAssignments.value.length === 0) {
          showMessage('No responded questionnaire assignments found.', 'warning')
          
          // Add mock data for testing if no assignments found
          questionnaireAssignments.value = [
            {
              assignment_id: '1001',
              questionnaire_id: '101',
              questionnaire_name: 'Annual Security Assessment',
              questionnaire_type: 'ANNUAL',
              questionnaire_description: 'Annual security review for existing vendors',
              questionnaire_version: '2.0',
              submission_date: new Date().toISOString(),
              overall_score: 85,
              status: 'RESPONDED',
              vendor_id: 'V001',
              vendor_company_name: 'Acme Technology Solutions',
              vendor_code: 'ATS-001',
              vendor_legal_name: 'Acme Technology Solutions Inc.',
              vendor_business_type: 'Technology Provider',
              response_statistics: {
                total_questions: 50,
                completed_questions: 48,
                required_questions: 45,
                completion_percentage: 96
              },
              questions_and_responses: [
                {
                  question_id: 'q1',
                  display_order: 1,
                  question_text: 'Does your organization have a formal information security policy?',
                  question_type: 'RADIO',
                  is_required: true,
                  is_completed: true,
                  scoring_weight: 2.0,
                  score: 100,
                  options: ['Yes', 'No', 'In Progress'],
                  vendor_response: 'Yes',
                  vendor_comment: 'Our security policy is reviewed annually and was last updated in January 2025.'
                },
                {
                  question_id: 'q2',
                  display_order: 2,
                  question_text: 'Describe your data breach notification process.',
                  question_type: 'TEXTAREA',
                  is_required: true,
                  is_completed: true,
                  scoring_weight: 1.5,
                  score: 80,
                  vendor_response: 'Our data breach notification process includes immediate internal escalation, investigation within 24 hours, and customer notification within 48 hours of confirmation. We maintain a dedicated incident response team available 24/7.'
                },
                {
                  question_id: 'q3',
                  display_order: 3,
                  question_text: 'Which security certifications does your organization currently maintain?',
                  question_type: 'MULTI_SELECT',
                  is_required: true,
                  is_completed: true,
                  scoring_weight: 1.0,
                  score: 90,
                  options: ['ISO 27001', 'SOC 2 Type II', 'PCI DSS', 'HIPAA', 'GDPR Compliance', 'NIST'],
                  vendor_response: 'ISO 27001, SOC 2 Type II, GDPR Compliance',
                  file_uploads: [
                    { name: 'ISO27001_Certificate_2025.pdf' },
                    { name: 'SOC2_Report_2024.pdf' }
                  ]
                },
                {
                  question_id: 'q4',
                  display_order: 4,
                  question_text: 'How often do you conduct penetration testing?',
                  question_type: 'SELECT',
                  is_required: true,
                  is_completed: true,
                  scoring_weight: 1.0,
                  score: 100,
                  options: ['Monthly', 'Quarterly', 'Bi-annually', 'Annually', 'Never'],
                  vendor_response: 'Quarterly'
                },
                {
                  question_id: 'q5',
                  display_order: 5,
                  question_text: 'Do you have a business continuity plan?',
                  question_type: 'BOOLEAN',
                  is_required: true,
                  is_completed: false,
                  scoring_weight: 2.0,
                  vendor_response: null
                }
              ],
              notes: 'Vendor has completed all required sections.'
            }
          ]
        }
      } catch (error) {
        console.error('Error fetching questionnaire assignments:', error)
        showMessage('Failed to load questionnaire assignments.', 'error')
        questionnaireAssignments.value = []
      } finally {
        loadingQuestionnaireAssignments.value = false
      }
    }

    const handleQuestionnaireAssignmentChange = (event) => {
      const assignmentId = event.target.value
      selectedQuestionnaireAssignment.value = assignmentId
      
      console.log('Selected questionnaire assignment ID:', assignmentId)
      console.log('Available questionnaire assignments:', questionnaireAssignments.value)
      
      // Convert to string for comparison if needed
      const assignment = questionnaireAssignments.value.find(a => String(a.assignment_id) === String(assignmentId))
      console.log('Found assignment:', assignment)
      
      if (assignment) {
        // Create a new object to ensure reactivity
        selectedAssignmentData.value = { ...assignment }
        console.log('Updated selectedAssignmentData:', selectedAssignmentData.value)
        
        // Set default response type for questionnaire reviews
        responseType.value = 'questionnaire_review'
        
        // Update response data with assignment context
        responseData.value = `Review of questionnaire assignment ${assignment.assignment_id} for ${assignment.vendor_company_name}`
        
        // Reset active question collapses
        activeQuestionCollapse.value = []
        
        // Auto-expand the first question if available
        if (assignment.questions_and_responses && assignment.questions_and_responses.length > 0) {
          const firstQuestion = assignment.questions_and_responses[0]
          const firstQuestionId = firstQuestion.question_id || 'q0'
          activeQuestionCollapse.value.push(firstQuestionId)
          console.log(`Auto-expanded first question: ${firstQuestionId}`)
        }
      } else {
        console.warn('No assignment found for ID:', assignmentId)
      }
    }

    const getAssignmentDisplayName = (assignment) => {
      return `${assignment.questionnaire_name} - ${assignment.vendor_company_name} (${assignment.vendor_code}) - Score: ${assignment.overall_score || 'N/A'}%`
    }

    const formatQuestionType = (type) => {
      const typeMap = {
        'TEXT': 'Text Input',
        'TEXTAREA': 'Long Text',
        'SELECT': 'Single Choice',
        'MULTI_SELECT': 'Multiple Choice',
        'RADIO': 'Radio Button',
        'CHECKBOX': 'Checkbox',
        'FILE': 'File Upload',
        'DATE': 'Date Picker',
        'NUMBER': 'Number Input',
        'EMAIL': 'Email Input',
        'URL': 'URL Input',
        'BOOLEAN': 'Yes/No',
        'RATING': 'Rating Scale'
      }
      return typeMap[type] || type
    }

    const getStageTitle = (stageNumber) => {
      if (workflowForm.workflow_type === 'MULTI_PERSON') {
        return `Approver ${stageNumber}`
      } else {
        return `Stage ${stageNumber}`
      }
    }

    const getStagePlaceholder = (stageNumber) => {
      if (workflowForm.workflow_type === 'MULTI_PERSON') {
        return `e.g., Approver ${stageNumber} Review`
      } else {
        return `e.g., Manager Review`
      }
    }

    const getDefaultStageOrder = () => {
      if (workflowForm.workflow_type === 'MULTI_PERSON') {
        return 0  // Team Approval stages start from 0
      } else {
        return stages.value.length + 1  // Tiered Approval stages are sequential
      }
    }

    const getRequestData = () => {
      if (approvalType.value === 'questionnaire_approval' && selectedQuestionnaireData.value && selectedQuestionnaireData.value.questionnaire_id) {
        // Get vendor_id from multiple sources with priority
        const vendor_id = selectedQuestionnaireData.value.vendor_id || 
                         requestForm.business_object_id || 
                         selectedAssignmentData.value?.vendor_id || 
                         selectedVendor.value || 
                         route.query.vendor_id ||
                         null
        
        console.log('getRequestData - Preparing questionnaire approval data with vendor_id:', vendor_id)
        console.log('getRequestData - Sources:', {
          selectedQuestionnaireData_vendor_id: selectedQuestionnaireData.value?.vendor_id,
          business_object_id: requestForm.business_object_id,
          route_query_vendor_id: route.query.vendor_id,
          selectedVendor: selectedVendor.value
        })
        
        const requestPayload = {
          questionnaire_id: selectedQuestionnaireData.value.questionnaire_id,
          questionnaire_name: selectedQuestionnaireData.value.questionnaire_name || '',
          questionnaire_type: selectedQuestionnaireData.value.questionnaire_type || 'CUSTOM',
          description: selectedQuestionnaireData.value.description || '',
          version: selectedQuestionnaireData.value.version || '1.0',
          approval_type: 'questionnaire_approval'
        }
        
        // Only add vendor_id if it exists
        if (vendor_id) {
          requestPayload.vendor_id = vendor_id
          requestPayload.business_object_id = vendor_id
        }
        
        return requestPayload
      } else if (approvalType.value === 'response_approval' && selectedAssignmentData.value && selectedAssignmentData.value.assignment_id) {
        const assignment = selectedAssignmentData.value
        
        const requestPayload = {
          response_type: responseType.value || 'questionnaire_review',
          response_data: responseData.value || '',
          response_priority: responsePriority.value || 'MEDIUM',
          questionnaire_assignment_id: selectedQuestionnaireAssignment.value,
          approval_type: 'response_approval',
          
          // Comprehensive assignment data for approvers
          assignment_summary: {
            assignment_id: assignment.assignment_id,
            questionnaire_id: assignment.questionnaire_id || null,
            questionnaire_name: assignment.questionnaire_name || '',
            questionnaire_type: assignment.questionnaire_type || 'CUSTOM',
            questionnaire_description: assignment.questionnaire_description || '',
            questionnaire_version: assignment.questionnaire_version || '1.0',
            submission_date: assignment.submission_date || null,
            overall_score: assignment.overall_score || 0,
            status: assignment.status || 'SUBMITTED'
          },
          
          // Vendor information
          vendor_information: {
            vendor_id: assignment.vendor_id || null,
            company_name: assignment.vendor_company_name || '',
            vendor_code: assignment.vendor_code || '',
            legal_name: assignment.vendor_legal_name || '',
            business_type: assignment.vendor_business_type || ''
          },
          
          // Response statistics for quick overview
          response_statistics: assignment.response_statistics || {},
          
          // Complete questions and responses for detailed review
          questions_and_responses: assignment.questions_and_responses || [],
          
          // Assignment metadata
          assignment_metadata: {
            assigned_date: assignment.assigned_date || null,
            due_date: assignment.due_date || null,
            assigned_by: assignment.assigned_by || null,
            notes: assignment.notes || ''
          },
          
          // Review context
          review_context: {
            approval_workflow_type: 'Response Approval',
            review_focus: 'Questionnaire Response Evaluation',
            key_areas: [
              'Response Completeness',
              'Response Quality',
              'Compliance Requirements',
              'Risk Assessment',
              'Vendor Capability Evaluation'
            ],
            review_instructions: `Please review all ${assignment.response_statistics?.total_questions || 0} questions and their corresponding vendor responses. Pay special attention to required questions and ensure all responses meet organizational standards and compliance requirements.`
          }
        }
        
        // Only add vendor_id if it exists
        if (assignment.vendor_id) {
          requestPayload.vendor_id = assignment.vendor_id
          requestPayload.business_object_id = assignment.vendor_id
        }
        
        return requestPayload
      } else if (approvalType.value === 'final_vendor_approval' && selectedVendor.value) {
        const requestPayload = {
          final_approval_type: finalApprovalType.value || '',
          vendor_id: selectedVendor.value,
          vendor_data: selectedVendorData.value || {},
          vendor_risks: vendorRisks.value || [], // For backward compatibility
          internal_risks: internalRisks.value || [],
          external_risks: externalRisks.value || [],
          screening_risks: externalRisks.value || [], // Alternative name for frontend compatibility
          risk_summary: riskSummary.value || {},
          vendor_info: vendorInfo.value || '',
          decision_criteria: decisionCriteria.value || '',
          business_impact: businessImpact.value || 'MEDIUM',
          approval_type: 'final_vendor_approval',
          business_object_id: selectedVendor.value
        }
        
        return requestPayload
      } else {
        // Default empty object when no approval type is selected
        return {}
      }
    }

    // Question toggle functionality
    const toggleQuestion = (questionId) => {
      // If questionId is null or undefined, don't do anything
      if (!questionId) {
        console.warn('Attempted to toggle question with null/undefined ID')
        return
      }
      
      const index = activeQuestionCollapse.value.indexOf(questionId)
      if (index > -1) {
        activeQuestionCollapse.value.splice(index, 1)
      } else {
        activeQuestionCollapse.value.push(questionId)
        
        // Auto-expand the first question if none are expanded
        if (activeQuestionCollapse.value.length === 1) {
          console.log(`Expanded question: ${questionId}`)
        }
      }
      
      console.log('Active question collapses:', activeQuestionCollapse.value)
    }

    return {
      // RBAC permission check
      hasAccess,
      accessDeniedInfo,
      
      workflowForm,
      requestForm,
      stages,
      users,
      loadingUsers,
      submitting,
      successDialogVisible,
      createdWorkflowId,
      createdRequestId,
      helpDialogVisible,
      jsonPayloadString,
      approvalType,
      selectedQuestionnaire,
      questionnaires,
      loadingQuestionnaires,
      selectedQuestionnaireData,
      responseType,
      responseData,
      responsePriority,
      selectedQuestionnaireAssignment,
      questionnaireAssignments,
      loadingQuestionnaireAssignments,
      selectedAssignmentData,
      workflowFormRef,
      availableApprovalTypes,
      finalApprovalType,
      vendorInfo,
      decisionCriteria,
      businessImpact,
      selectedVendor,
      vendors,
      loadingVendors,
      selectedVendorData,
      vendorRisks,
      internalRisks,
      externalRisks,
      riskSummary,
      activeRiskCollapse,
      activeInternalRiskCollapse,
      activeExternalRiskCollapse,
      activeQuestionCollapse,
      addStage,
      removeStage,
      moveStage,
      submitWorkflow,
      resetForm,
      createAnother,
      getWorkflowTypeLabel,
      handleUserSelection,
      getUserDisplayName,
      showPayloadHelp,
      fetchQuestionnaires,
      handleApprovalTypeChange,
      handleQuestionnaireChange,
      getQuestionnaireDisplayName,
      getQuestionnaireTypeColor,
      formatDate,
      getRequestData,
      getStageTitle,
      getStagePlaceholder,
      getDefaultStageOrder,
      fetchVendors,
      handleVendorChange,
      getVendorDisplayName,
      getVendorRiskColor,
      getVendorStatusColor,
      fetchQuestionnaireAssignments,
      handleQuestionnaireAssignmentChange,
      getAssignmentDisplayName,
      formatQuestionType,
      toggleQuestion,
      handleAutoPopulateFromQuery,
      isAutoPopulated,
      autoPopulateMessage,
      activeTab
    }
  }
}
</script>

<!-- Main styles from external file -->
<style src="./ApprovalWorkflowCreator.css"></style>

<!-- Critical fallback styles -->
<style>
/* Ensure minimum functionality if external CSS fails to load */
.comprehensive-workflow-creator {
  min-height: 100vh;
  padding: 32px;
  background: #f3f4f6;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.modern-header {
  background: white;
  border-radius: 8px;
  padding: 24px 32px;
  margin-bottom: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border: 1px solid #e5e7eb;
}

.card, .workflow-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  margin-bottom: 24px;
  overflow: hidden;
}

.card-header {
  padding: 24px;
  border-bottom: 1px solid #e5e7eb;
  background: white;
}

.card-body {
  padding: 24px;
}

.form-item {
  margin-bottom: 20px;
  padding: 0;
  background: transparent;
  border: none;
  border-radius: 0;
  box-shadow: none;
}

.form-label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #374151;
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.form-input,
.form-select,
.form-textarea {
  display: block;
  width: 100%;
  padding: 10px 14px;
  font-size: 14px;
  color: #111827;
  background: white;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  box-sizing: border-box;
  outline: none;
  font-family: inherit;
  font-weight: 400;
}

.form-input:focus,
.form-select:focus,
.form-textarea:focus {
  border-color: #93c5fd;
  box-shadow: 0 0 0 3px rgba(147, 197, 253, 0.35);
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 20px;
  font-size: 14px;
  font-weight: 500;
  border: 1px solid transparent;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: #93c5fd;
  color: white;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  border: 1px solid #93c5fd;
}

.btn-primary:hover {
  background: #60a5fa;
  box-shadow: 0 2px 4px rgba(96, 165, 250, 0.35);
}

.btn-secondary {
  background: white;
  border: 1px solid #d1d5db;
  color: #374151;
}

.row {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  margin: 0;
}

.col-12 {
  flex: 0 0 calc(50% - 10px);
  max-width: calc(50% - 10px);
}

/* Remove all decorative borders and dividers */
.divider {
  display: none;
}

.divider-text {
  display: none;
}

/* Simplify stage cards */
.stage-card {
  border: 1px solid #e5e7eb !important;
  border-left: 3px solid #93c5fd !important;
  border-radius: 0 !important;
  background: white !important;
  padding: 20px !important;
  box-shadow: none !important;
}

.stage-header {
  padding: 0 0 16px 0 !important;
  background: transparent !important;
  border-bottom: 1px solid #e5e7eb !important;
  margin-bottom: 20px !important;
}

.stage-title {
  font-size: 14px !important;
  font-weight: 600 !important;
  color: #111827 !important;
}

/* Simplify payload section */
.payload-section {
  padding: 0 !important;
  background: transparent !important;
  border: none !important;
  border-radius: 0 !important;
  box-shadow: none !important;
}

.payload-header h3 {
  font-size: 15px !important;
  font-weight: 600 !important;
  color: #111827 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.05em !important;
}

/* Simplify stages header */
.stages-header {
  padding: 0 !important;
  background: transparent !important;
  border: none !important;
  border-radius: 0 !important;
  margin-bottom: 24px !important;
}

.stages-header h3 {
  font-size: 16px !important;
  font-weight: 600 !important;
  color: #111827 !important;
}

/* Simplify cards */
.questionnaire-card,
.vendor-details-card,
.vendor-risks-card,
.assignment-details-card,
.statistics-card,
.questions-responses-card,
.response-selection-card,
.response-configuration-card {
  border: 1px solid #e5e7eb !important;
  border-radius: 6px !important;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
  margin-bottom: 20px !important;
}

/* Simplify help button */
.help-button {
  padding: 6px 12px !important;
  background: transparent !important;
  border: 1px solid #d1d5db !important;
  color: #6b7280 !important;
  font-size: 13px !important;
  border-radius: 6px !important;
}

.help-button:hover {
  background: #f9fafb !important;
  border-color: #9ca3af !important;
  color: #374151 !important;
}

.help-button .icon {
  width: 16px !important;
  height: 16px !important;
  background: transparent !important;
  color: #6b7280 !important;
  font-size: 12px !important;
}

/* Simplify icon buttons */
.btn-icon {
  padding: 6px 10px !important;
  background: white !important;
  border: 1px solid #d1d5db !important;
  color: #374151 !important;
  font-size: 14px !important;
}

.btn-icon:hover:not(:disabled) {
  background: #f9fafb !important;
  border-color: #9ca3af !important;
  transform: none !important;
}

.btn-icon.btn-danger {
  background: white !important;
  color: #dc2626 !important;
  border: 1px solid #d1d5db !important;
}

.btn-icon.btn-danger:hover {
  background: #fef2f2 !important;
  border-color: #9ca3af !important;
}

/* Simplify tags */
.tag {
  padding: 4px 10px !important;
  font-size: 12px !important;
  font-weight: 500 !important;
  border-radius: 4px !important;
  transition: all 0.2s ease !important;
}

.tag:hover {
  transform: none !important;
}

/* Card headers */
.card-header-with-icon {
  background: white !important;
  border-bottom: 1px solid #e5e7eb !important;
  padding: 20px !important;
}

.card-header-with-icon h3,
.card-header-content h2 {
  font-size: 16px !important;
  font-weight: 600 !important;
  color: #111827 !important;
}

/* Remove all gradient backgrounds */
.questionnaire-header,
.vendor-header,
.assignment-header,
.risks-header,
.questions-header,
.config-header {
  background: white !important;
  border-bottom: 1px solid #e5e7eb !important;
  padding: 20px !important;
}

/* Section headers */
.section-header {
  background: transparent !important;
  border: none !important;
  padding: 0 0 12px 0 !important;
  margin-bottom: 16px !important;
}

.section-header::before,
.section-header::after {
  display: none !important;
}

.section-title {
  font-size: 14px !important;
  font-weight: 600 !important;
  color: #374151 !important;
}

/* Remove all backdrop filters and blur effects */
* {
  backdrop-filter: none !important;
  -webkit-backdrop-filter: none !important;
}

.form-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 24px;
  padding: 20px 24px;
  background: white;
  border-top: 1px solid #e5e7eb;
  border-radius: 0;
}

/* Response Approval Card - Purple Gradient */
.response-approval-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 40px 32px;
  margin-bottom: 24px;
  color: white;
  position: relative;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
  text-align: center;
}

.response-approval-icon {
  font-size: 48px;
  margin-bottom: 16px;
  display: block;
}

.response-approval-title {
  font-size: 24px;
  font-weight: 700;
  margin: 0 0 12px 0;
  color: white;
}

.response-approval-description {
  font-size: 14px;
  margin: 0 0 20px 0;
  color: rgba(255, 255, 255, 0.9);
  line-height: 1.5;
}

.response-approval-tag {
  position: absolute;
  top: 20px;
  right: 20px;
  background: #22c55e;
  color: white;
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* Submitted Questionnaire Section */
.submitted-questionnaire-section {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 24px;
  margin-bottom: 24px;
}

.submitted-questionnaire-section .form-item {
  margin-bottom: 20px;
}

.submitted-questionnaire-section .form-label {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.label-icon-small {
  font-size: 16px;
}

.submitted-questionnaire-section .form-input {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 12px 16px;
  font-size: 14px;
  color: #111827;
  cursor: pointer;
}

.submitted-questionnaire-section .form-input:hover {
  border-color: #93c5fd;
  background: white;
}

.questionnaire-select-wrapper {
  position: relative;
}

.questionnaire-select-input {
  width: 100%;
  cursor: pointer;
}

.questionnaire-select-dropdown {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  opacity: 0;
  cursor: pointer;
  z-index: 10;
}

.questionnaire-details-row {
  display: flex;
  gap: 32px;
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #e5e7eb;
}

.detail-item {
  flex: 1;
}

.detail-label {
  display: block;
  font-size: 11px;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 6px;
}

.detail-value {
  font-size: 14px;
  font-weight: 500;
  color: #111827;
}

/* Responsive styles for response approval */
@media (max-width: 768px) {
  .response-approval-card {
    padding: 32px 24px;
  }
  
  .response-approval-icon {
    font-size: 40px;
  }
  
  .response-approval-title {
    font-size: 20px;
  }
  
  .response-approval-tag {
    position: static;
    display: inline-block;
    margin-top: 12px;
  }
  
  .questionnaire-details-row {
    flex-direction: column;
    gap: 20px;
  }
}

/* Enhanced Selection Card */
.response-selection-card {
  border: 2px solid #e5e7eb;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.response-selection-card .selection-header {
  display: flex;
  align-items: center;
  gap: 16px;
}

.response-selection-card .selection-icon {
  font-size: 24px;
  color: #6366f1;
}

.response-selection-card .enhanced-form-item {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 0;
}

.response-selection-card .enhanced-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 16px;
}

.response-selection-card .label-icon {
  font-size: 18px;
}

.response-selection-card .select-wrapper {
  position: relative;
}

.response-selection-card .enhanced-select {
  width: 100%;
  padding: 16px 20px;
  border: 2px solid #d1d5db;
  border-radius: 8px;
  font-size: 16px;
  background: white;
  transition: all 0.3s ease;
}

.response-selection-card .enhanced-select:focus {
  border-color: #6366f1;
  box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.1);
  outline: none;
}

.response-selection-card .loading-indicator {
  position: absolute;
  right: 16px;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  gap: 8px;
  color: #6b7280;
}

.response-selection-card .spinner {
  width: 16px;
  height: 16px;
  border: 2px solid #e5e7eb;
  border-top: 2px solid #6366f1;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.response-selection-card .no-assignments-enhanced {
  text-align: center;
  padding: 40px 20px;
}

.response-selection-card .empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.response-selection-card .empty-icon {
  font-size: 48px;
  opacity: 0.6;
}

.response-selection-card .empty-state h4 {
  margin: 0;
  color: #374151;
  font-size: 20px;
}

.response-selection-card .empty-state p {
  margin: 0;
  color: #6b7280;
  font-size: 16px;
}

.response-selection-card .enhanced-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.response-selection-card .enhanced-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(99, 102, 241, 0.3);
}

/* Enhanced Questions and Responses */
.questions-responses-card-enhanced {
  border: 2px solid #e5e7eb;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.questions-responses-card-enhanced .questions-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.questions-responses-card-enhanced .header-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.questions-responses-card-enhanced .header-icon-enhanced {
  font-size: 24px;
  color: #f59e0b;
}

.questions-responses-card-enhanced .questions-summary {
  display: flex;
  gap: 24px;
}

.questions-responses-card-enhanced .summary-item {
  text-align: center;
}

.questions-responses-card-enhanced .summary-label {
  display: block;
  font-size: 12px;
  color: #6b7280;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.questions-responses-card-enhanced .summary-value {
  display: block;
  font-size: 24px;
  font-weight: 700;
  color: #1f2937;
  margin-top: 4px;
}

.questions-container-enhanced {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.question-item-enhanced {
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  overflow: hidden;
  background: white;
  transition: all 0.3s ease;
}

.question-item-enhanced:hover {
  border-color: #d1d5db;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.question-header-enhanced {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  cursor: pointer;
  transition: all 0.3s ease;
}

.question-header-enhanced:hover {
  background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
}

.question-main-info {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
}

.question-number-enhanced {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 700;
  font-size: 14px;
}

.question-content-main {
  flex: 1;
}

.question-title {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  line-height: 1.4;
}

.question-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.question-type-badge {
  background: #dbeafe;
  color: #3b82f6;
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
}

.required-badge {
  background: #fef3c7;
  color: #92400e;
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
}

.weight-badge {
  background: #e0e7ff;
  color: #3730a3;
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
}

.question-status-section {
  display: flex;
  align-items: center;
  gap: 16px;
}

.status-badges {
  display: flex;
  gap: 8px;
}

.status-badge {
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}

.status-completed {
  background: #d1fae5;
  color: #065f46;
}

.status-incomplete {
  background: #fef3c7;
  color: #92400e;
}

.score-badge {
  background: #dbeafe;
  color: #3b82f6;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}

.expand-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.expand-arrow {
  font-size: 16px;
  color: #6b7280;
  transition: transform 0.3s ease;
}

.expand-arrow.expanded {
  transform: rotate(180deg);
}

.question-details-enhanced {
  padding: 24px;
  background: #fafafa;
  border-top: 1px solid #e5e7eb;
}

.details-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.question-details-panel,
.response-details-panel {
  background: white;
  border-radius: 8px;
  padding: 20px;
  border: 1px solid #e5e7eb;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f3f4f6;
}

.panel-icon {
  font-size: 18px;
}

.panel-header h5 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.details-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
}

.detail-label {
  font-weight: 500;
  color: #6b7280;
  font-size: 14px;
}

.detail-value {
  font-weight: 600;
  color: #1f2937;
  font-size: 14px;
}

.options-section {
  margin-top: 12px;
}

.options-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.option-item {
  background: #f3f4f6;
  color: #374151;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
}

.response-content-enhanced {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.response-section {
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: 8px;
  padding: 16px;
}

.response-header {
  margin-bottom: 8px;
}

.response-label {
  font-weight: 600;
  color: #0369a1;
  font-size: 14px;
}

.response-value-enhanced {
  color: #0c4a6e;
  font-size: 14px;
  line-height: 1.5;
  white-space: pre-wrap;
}

.no-response-enhanced {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #dc2626;
  font-style: italic;
  padding: 16px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
}

.no-response-icon {
  font-size: 16px;
}

.comment-section {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 8px;
  padding: 16px;
}

.comment-header {
  margin-bottom: 8px;
}

.comment-label {
  font-weight: 600;
  color: #166534;
  font-size: 14px;
}

.comment-value-enhanced {
  color: #14532d;
  font-size: 14px;
  line-height: 1.5;
  white-space: pre-wrap;
}

.attachments-section {
  background: #fefce8;
  border: 1px solid #fde047;
  border-radius: 8px;
  padding: 16px;
}

.attachments-header {
  margin-bottom: 8px;
}

.attachments-label {
  font-weight: 600;
  color: #a16207;
  font-size: 14px;
}

.attachments-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.attachment-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: white;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
}

.attachment-icon {
  font-size: 14px;
  color: #6b7280;
}

.attachment-name {
  font-size: 14px;
  color: #374151;
  font-weight: 500;
}

.no-questions-enhanced {
  text-align: center;
  padding: 40px 20px;
}

.empty-state-enhanced {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.empty-icon-enhanced {
  font-size: 48px;
  opacity: 0.6;
}

.empty-state-enhanced h4 {
  margin: 0;
  color: #374151;
  font-size: 20px;
}

.empty-state-enhanced p {
  margin: 0;
  color: #6b7280;
  font-size: 16px;
  max-width: 400px;
}

/* Enhanced Response Configuration */
.response-configuration-card {
  border: 2px solid #e5e7eb;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.response-configuration-card .config-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.response-configuration-card .header-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.response-configuration-card .header-icon-enhanced {
  font-size: 24px;
  color: #10b981;
}

.response-configuration-card .config-status {
  display: flex;
  align-items: center;
}

.response-configuration-card .status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #f0fdf4;
  color: #166534;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
}

.response-configuration-card .status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #dcfce7;
}

.response-configuration-card .status-dot.active {
  background: #22c55e;
  animation: pulse 2s infinite;
}

.configuration-grid {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.config-section {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  padding: 24px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid #d1d5db;
}

.section-icon {
  font-size: 20px;
}

.section-header h4 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.form-row-enhanced {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.form-item-enhanced {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.form-label-enhanced {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #374151;
  font-size: 14px;
}

.form-label-enhanced .label-icon {
  font-size: 16px;
}

.select-wrapper-enhanced {
  position: relative;
}

.form-select-enhanced {
  width: 100%;
  padding: 16px 20px;
  border: 2px solid #d1d5db;
  border-radius: 8px;
  font-size: 16px;
  background: white;
  transition: all 0.3s ease;
  appearance: none;
}

.form-select-enhanced:focus {
  border-color: #10b981;
  box-shadow: 0 0 0 4px rgba(16, 185, 129, 0.1);
  outline: none;
}

.select-arrow {
  position: absolute;
  right: 16px;
  top: 50%;
  transform: translateY(-50%);
  color: #6b7280;
  pointer-events: none;
}

.textarea-wrapper {
  position: relative;
}

.form-textarea-enhanced {
  width: 100%;
  padding: 16px 20px;
  border: 2px solid #d1d5db;
  border-radius: 8px;
  font-size: 16px;
  background: white;
  transition: all 0.3s ease;
  resize: vertical;
  min-height: 120px;
  font-family: inherit;
}

.form-textarea-enhanced:focus {
  border-color: #10b981;
  box-shadow: 0 0 0 4px rgba(16, 185, 129, 0.1);
  outline: none;
}

.textarea-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}

.character-count {
  font-size: 14px;
}

.character-count .count {
  color: #6b7280;
  font-weight: 500;
}

.character-count .count.warning {
  color: #f59e0b;
}

.character-count .count.error {
  color: #dc2626;
}

.textarea-actions {
  display: flex;
  gap: 8px;
}

.btn-text {
  background: none;
  border: none;
  color: #6b7280;
  font-size: 14px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.btn-text:hover {
  background: #f3f4f6;
  color: #374151;
}

@media (max-width: 768px) {
  .col-12 {
    flex: 0 0 100%;
    max-width: 100%;
  }
  
  .comprehensive-workflow-creator {
    padding: 16px;
  }
  
  .response-approval-header {
    flex-direction: column;
    gap: 20px;
    text-align: center;
  }
  
  .details-grid {
    grid-template-columns: 1fr;
  }
  
  .form-row-enhanced {
    grid-template-columns: 1fr;
  }
  
  .questions-responses-card-enhanced .questions-header {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }
  
  .questions-responses-card-enhanced .questions-summary {
    flex-direction: column;
    gap: 12px;
  }
}

/* ========================================
   COMPREHENSIVE UI REDESIGN TO MATCH REFERENCE IMAGE
   ======================================== */

/* Clean Background */
.comprehensive-workflow-creator {
  min-height: 100vh;
  padding: 20px !important;
  background: #f9fafb !important;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

/* Page Header */
.page-header {
  display: flex !important;
  justify-content: space-between !important;
  align-items: center !important;
  background: white !important;
  border: 1px solid #e5e7eb !important;
  border-radius: 12px !important;
  padding: 24px 32px !important;
  margin-bottom: 24px !important;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
}

.page-header-left {
  flex: 1 !important;
  text-align: left !important;
}

.page-title {
  font-size: 24px !important;
  font-weight: 700 !important;
  color: #111827 !important;
  margin: 0 0 8px 0 !important;
  text-align: left !important;
}

.page-subtitle {
  font-size: 14px !important;
  color: #6b7280 !important;
  margin: 0 !important;
  text-align: left !important;
}

.page-header-right {
  display: flex !important;
  align-items: center !important;
  gap: 16px !important;
}

.status-indicator {
  display: flex !important;
  align-items: center !important;
  gap: 8px !important;
  padding: 8px 16px !important;
  background: #f0fdf4 !important;
  border: 1px solid #86efac !important;
  border-radius: 8px !important;
}

.status-dot {
  width: 8px !important;
  height: 8px !important;
  background: #22c55e !important;
  border-radius: 50% !important;
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite !important;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.status-indicator span {
  font-size: 13px !important;
  font-weight: 600 !important;
  color: #16a34a !important;
}

/* Main Card */
.workflow-card {
  background: white !important;
  border: 1px solid #e5e7eb !important;
  border-radius: 12px !important;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
  margin: 0 !important;
  padding: 0 !important;
  overflow: hidden !important;
}

/* Tab Navigation - Blue Active State */
.tab-navigation {
  display: flex !important;
  border-bottom: 1px solid #e5e7eb !important;
  background: white !important;
  padding: 0 !important;
  margin: 0 !important;
  position: relative !important;
  border-radius: 12px 12px 0 0 !important;
  overflow: hidden !important;
}

.tab-button {
  flex: 1 !important;
  padding: 18px 24px !important;
  background: #f9fafb !important;
  border: none !important;
  border-bottom: none !important;
  border-right: 1px solid #e5e7eb !important;
  color: #6b7280 !important;
  font-size: 12px !important;
  font-weight: 600 !important;
  letter-spacing: 0.05em !important;
  cursor: pointer !important;
  transition: all 0.2s ease !important;
  position: relative !important;
  text-transform: uppercase !important;
}

.tab-button:last-child {
  border-right: none !important;
}

.tab-button:hover {
  color: #60a5fa !important;
  background: #eff6ff !important;
}

.tab-button.active {
  color: white !important;
  background: #93c5fd !important;
  font-weight: 700 !important;
  border-right: 1px solid #60a5fa !important;
}

.tab-button.active::before,
.tab-button.active::after,
.tab-button::before,
.tab-button::after {
  display: none !important;
}

/* Tab Content */
.tab-content {
  padding: 32px 40px !important;
  animation: none !important;
  min-height: auto !important;
  background: white !important;
}

/* Form Items */
.form-item {
  margin-bottom: 24px !important;
  padding: 0 !important;
  background: transparent !important;
  border: none !important;
  border-radius: 0 !important;
  box-shadow: none !important;
}

/* Form Labels */
.form-label {
  display: block !important;
  margin-bottom: 8px !important;
  font-weight: 600 !important;
  color: #374151 !important;
  font-size: 12px !important;
  text-transform: uppercase !important;
  letter-spacing: 0.05em !important;
}

/* Form Inputs */
.form-input,
.form-select,
.form-textarea {
  display: block !important;
  width: 100% !important;
  padding: 12px 16px !important;
  font-size: 14px !important;
  color: #111827 !important;
  background: #f9fafb !important;
  border: 1px solid #e5e7eb !important;
  border-radius: 8px !important;
  box-sizing: border-box !important;
  outline: none !important;
  font-family: inherit !important;
  font-weight: 400 !important;
  transition: all 0.2s ease !important;
}

.form-input:focus,
.form-select:focus,
.form-textarea:focus {
  border-color: #93c5fd !important;
  background: white !important;
  box-shadow: 0 0 0 3px rgba(147, 197, 253, 0.35) !important;
}

/* Tab Action Buttons */
.tab-actions {
  display: flex !important;
  justify-content: flex-end !important;
  gap: 12px !important;
  margin-top: 32px !important;
  padding-top: 24px !important;
  border-top: 1px solid #e5e7eb !important;
}

.btn-tab-nav {
  padding: 12px 32px !important;
  font-size: 13px !important;
  font-weight: 600 !important;
  letter-spacing: 0.05em !important;
  text-transform: uppercase !important;
  border-radius: 8px !important;
}

.btn-tab-nav.btn-primary {
  background: #93c5fd !important;
  color: white !important;
  border: 1px solid #93c5fd !important;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05) !important;
}

.btn-tab-nav.btn-primary:hover {
  background: #60a5fa !important;
  border-color: #60a5fa !important;
  box-shadow: 0 4px 6px rgba(96, 165, 250, 0.35) !important;
}

.btn-tab-nav.btn-secondary {
  background: white !important;
  color: #6b7280 !important;
  border: 1px solid #d1d5db !important;
}

.btn-tab-nav.btn-secondary:hover {
  background: #f9fafb !important;
  color: #374151 !important;
  border-color: #9ca3af !important;
}

/* Row Layout */
.row {
  display: flex !important;
  flex-wrap: wrap !important;
  gap: 24px !important;
  margin: 0 0 8px 0 !important;
}

.col-12 {
  flex: 0 0 calc(50% - 12px) !important;
  max-width: calc(50% - 12px) !important;
}

/* Remove Card Headers Inside Tabs */
.tab-content .card-header {
  display: none !important;
}

/* Show card-header for stage cards (needed for delete button) */
.tab-content .stage-card .card-header {
  display: block !important;
  padding: 0 !important;
  border-bottom: none !important;
  background: transparent !important;
}

/* Alert Styles */
.alert {
  padding: 16px 20px !important;
  border-radius: 8px !important;
  margin: 0 0 24px 0 !important;
  border: 1px solid !important;
}

.alert-info {
  background: #eff6ff !important;
  border-color: #93c5fd !important;
}

.alert-icon {
  font-size: 20px !important;
}

.alert-title {
  font-size: 14px !important;
  font-weight: 600 !important;
  color: #60a5fa !important;
  margin-bottom: 4px !important;
}

.alert-description {
  font-size: 13px !important;
  color: #60a5fa !important;
}

/* Payload Section */
.payload-section {
  padding: 0 !important;
  background: transparent !important;
  border: none !important;
  border-radius: 0 !important;
  box-shadow: none !important;
}

.payload-header {
  display: flex !important;
  justify-content: space-between !important;
  align-items: center !important;
  margin-bottom: 0 !important;
  padding-bottom: 16px !important;
  border-bottom: none !important;
}

.payload-header h3 {
  font-size: 14px !important;
  font-weight: 600 !important;
  color: #111827 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.05em !important;
  margin: 0 !important;
}

/* Help Button */
.help-button {
  padding: 8px 16px !important;
  background: white !important;
  border: 1px solid #d1d5db !important;
  color: #6b7280 !important;
  font-size: 12px !important;
  border-radius: 6px !important;
  font-weight: 500 !important;
}

.help-button:hover {
  background: #f9fafb !important;
  border-color: #9ca3af !important;
  color: #374151 !important;
}

.help-button .icon {
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  width: 18px !important;
  height: 18px !important;
  background: #e5e7eb !important;
  border-radius: 50% !important;
  color: #6b7280 !important;
  font-size: 12px !important;
  margin-right: 6px !important;
}

/* Questionnaire Card */
.questionnaire-card {
  border: 1px solid #e5e7eb !important;
  border-radius: 8px !important;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
  margin-bottom: 24px !important;
  background: white !important;
}

.questionnaire-card .card-header {
  display: block !important;
  background: white !important;
  border-bottom: 1px solid #e5e7eb !important;
  padding: 20px 24px !important;
}

.questionnaire-header {
  display: flex !important;
  justify-content: space-between !important;
  align-items: center !important;
}

.questionnaire-header h3 {
  font-size: 16px !important;
  font-weight: 600 !important;
  color: #111827 !important;
  margin: 0 !important;
}

.questionnaire-card .card-body {
  padding: 24px !important;
}

/* Tags */
.tag {
  padding: 4px 12px !important;
  font-size: 11px !important;
  font-weight: 600 !important;
  border-radius: 6px !important;
  text-transform: uppercase !important;
  letter-spacing: 0.05em !important;
}

/* Stages Section */
.stages-section {
  padding: 0 !important;
}

.stages-header {
  display: flex !important;
  justify-content: space-between !important;
  align-items: center !important;
  margin-bottom: 24px !important;
  padding-bottom: 16px !important;
  border-bottom: 1px solid #e5e7eb !important;
  background: transparent !important;
}

.stages-header h3 {
  font-size: 14px !important;
  font-weight: 600 !important;
  color: #111827 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.05em !important;
  margin: 0 !important;
}

/* Stage Cards */
.stage-card {
  border: 1px solid #e5e7eb !important;
  border-radius: 8px !important;
  background: white !important;
  padding: 24px !important;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
  margin-bottom: 20px !important;
}

.stage-header {
  display: flex !important;
  justify-content: space-between !important;
  align-items: center !important;
  padding: 0 0 16px 0 !important;
  background: transparent !important;
  border-bottom: 1px solid #e5e7eb !important;
  margin-bottom: 20px !important;
}

.stage-title {
  font-size: 15px !important;
  font-weight: 600 !important;
  color: #111827 !important;
}

.stage-actions {
  display: flex !important;
  align-items: center !important;
  gap: 8px !important;
}

/* Buttons */
.btn {
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  gap: 8px !important;
  padding: 10px 20px !important;
  font-size: 13px !important;
  font-weight: 600 !important;
  border: 1px solid transparent !important;
  border-radius: 8px !important;
  cursor: pointer !important;
  transition: all 0.2s ease !important;
}

.btn-primary {
  background: #93c5fd !important;
  color: white !important;
  border-color: #93c5fd !important;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05) !important;
}

.btn-primary:hover {
  background: #60a5fa !important;
  border-color: #60a5fa !important;
  box-shadow: 0 4px 6px rgba(96, 165, 250, 0.35) !important;
}

.btn-secondary {
  background: white !important;
  color: #374151 !important;
  border: 1px solid #d1d5db !important;
}

.btn-secondary:hover {
  background: #f9fafb !important;
  border-color: #9ca3af !important;
}

/* Remove all decorative elements */
.divider,
.divider-text {
  display: none !important;
}

/* Remove all backdrop filters */
* {
  backdrop-filter: none !important;
  -webkit-backdrop-filter: none !important;
}

/* Clean up all pseudo-elements that add decorative borders */
.card::before,
.card::after,
.card-header::before,
.card-header::after,
.form-item::before,
.form-item::after,
.stage-card::before,
.stage-card::after {
  display: none !important;
}

/* Form Actions at Bottom */
.form-actions {
  display: flex !important;
  justify-content: flex-end !important;
  gap: 12px !important;
  margin-top: 0 !important;
  padding: 24px 40px !important;
  border-top: 1px solid #e5e7eb !important;
  background: white !important;
}

.form-actions .btn {
  padding: 12px 32px !important;
  font-size: 14px !important;
  font-weight: 600 !important;
}

/* Responsive */
@media (max-width: 768px) {
  .comprehensive-workflow-creator {
    padding: 16px !important;
  }
  
  .tab-content {
    padding: 24px 20px !important;
  }
  
  .col-12 {
    flex: 0 0 100% !important;
    max-width: 100% !important;
  }
  
  .tab-button {
    font-size: 10px !important;
    padding: 14px 12px !important;
  }
  
  .tab-actions {
    flex-direction: column !important;
  }
  
  .btn-tab-nav {
    width: 100% !important;
  }
}
</style>

