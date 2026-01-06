<template>
  <div class="comprehensive-workflow-creator">
    <el-card class="workflow-card">
      <template #header>
        <div class="card-header">
          <h2>Create Workflow & Request</h2>
          <p>Create workflow template and approval request in one operation</p>
        </div>
      </template>

      <el-form 
        ref="workflowFormRef" 
        :model="workflowForm" 
        :rules="workflowRules" 
        label-width="140px"
        class="workflow-form"
        :validate-on-rule-change="false"
        :hide-required-asterisk="false"
        :validate-on-input="false"
      >
        <!-- Workflow Information -->
        <el-divider content-position="left">Workflow Information</el-divider>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="Workflow Name" prop="workflow_name">
              <el-input 
                v-model.lazy="workflowForm.workflow_name" 
                placeholder="e.g., Standard Policy Approval"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="Workflow Type" prop="workflow_type">
              <el-select v-model="workflowForm.workflow_type" placeholder="Select workflow type" style="width: 100%">
                <el-option label="Tiered Approval" value="MULTI_LEVEL" />
                <el-option label="Team Approval" value="MULTI_PERSON" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="Created By" prop="created_by">
              <el-input v-model.lazy="workflowForm.created_by" placeholder="Username" readonly />
            </el-form-item>
          </el-col>
        </el-row>
        
        <!-- Hidden Business Object Type field -->
        <el-form-item style="display: none;">
          <el-input v-model="workflowForm.business_object_type" />
        </el-form-item>

        <el-form-item label="Description" prop="description">
          <el-input 
            v-model.lazy="workflowForm.description" 
            type="textarea" 
            :rows="3"
            placeholder="Describe the workflow purpose and rules..."
          />
        </el-form-item>

        <!-- Request Information -->
        <el-divider content-position="left">Request Information</el-divider>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="Request Title" prop="request_title">
              <el-input 
                v-model.lazy="requestForm.request_title" 
                placeholder="e.g., Employee Remote Work Policy"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="Priority" prop="priority">
              <el-select v-model="requestForm.priority" placeholder="Select priority" style="width: 100%">
                <el-option label="Low" value="LOW" />
                <el-option label="Medium" value="MEDIUM" />
                <el-option label="High" value="HIGH" />
                <el-option label="Urgent" value="URGENT" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="Requester" prop="requester_name">
              <el-input v-model.lazy="requestForm.requester_name" placeholder="Requester username" readonly />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="Department" prop="requester_department">
              <el-input v-model.lazy="requestForm.requester_department" placeholder="Your department" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="Request Description" prop="request_description">
          <el-input 
            v-model.lazy="requestForm.request_description" 
            type="textarea" 
            :rows="3"
            placeholder="Describe what you're requesting approval for..."
          />
        </el-form-item>


        <!-- Request Data -->
        <el-divider content-position="left">Request Data</el-divider>
        
        <div class="payload-section">
          <div class="payload-header">
            <h3>Request Payload</h3>
            <el-button type="text" @click="showPayloadHelp" :icon="QuestionFilled">
              Help
            </el-button>
          </div>
          
          <el-row :gutter="20" style="margin-bottom: 20px;">
            <el-col :span="12">
              <el-form-item label="Approval Type" prop="approval_type">
                <el-select v-model="approvalType" placeholder="Select approval type" style="width: 100%" @change="handleApprovalTypeChange">
                  <el-option 
                    v-for="option in availableApprovalTypes" 
                    :key="option.value" 
                    :label="option.label" 
                    :value="option.value" 
                  />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12" v-if="approvalType === 'questionnaire_approval'">
              <el-form-item label="Select Questionnaire" prop="selected_questionnaire">
                <el-select 
                  v-model="selectedQuestionnaire" 
                  placeholder="Select questionnaire" 
                  style="width: 100%"
                  :loading="loadingQuestionnaires"
                  @change="handleQuestionnaireChange"
                >
                  <el-option
                    v-for="questionnaire in questionnaires"
                    :key="questionnaire.questionnaire_id"
                    :label="getQuestionnaireDisplayName(questionnaire)"
                    :value="questionnaire.questionnaire_id"
                  />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12" v-if="approvalType === 'final_vendor_approval'">
              <el-form-item label="Select Vendor" prop="selected_vendor">
                <el-select 
                  v-model="selectedVendor" 
                  placeholder="Select vendor" 
                  style="width: 100%"
                  :loading="loadingVendors"
                  @change="handleVendorChange"
                  filterable
                >
                  <el-option
                    v-for="vendor in vendors"
                    :key="vendor.id"
                    :label="getVendorDisplayName(vendor)"
                    :value="vendor.id"
                  />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          
          <!-- Questionnaire Approval Form -->
          <div v-if="approvalType === 'questionnaire_approval' && selectedQuestionnaire">
            <el-alert
              title="Questionnaire Approval Details"
              description="Review the selected questionnaire details for approval."
              type="info"
              show-icon
              :closable="false"
              style="margin-bottom: 20px"
            />
            
            <el-card class="questionnaire-card" shadow="hover">
              <template #header>
                <div class="questionnaire-header">
                  <h3>{{ selectedQuestionnaireData.questionnaire_name }}</h3>
                  <el-tag :type="getQuestionnaireTypeColor(selectedQuestionnaireData.questionnaire_type)">
                    {{ selectedQuestionnaireData.questionnaire_type }}
                  </el-tag>
                </div>
              </template>
              
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="Questionnaire ID">
                    <el-input :value="selectedQuestionnaireData.questionnaire_id" readonly />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="Version">
                    <el-input :value="selectedQuestionnaireData.version" readonly />
                  </el-form-item>
                </el-col>
              </el-row>
              
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="Type">
                    <el-input :value="selectedQuestionnaireData.questionnaire_type" readonly />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="Created Date">
                    <el-input :value="formatDate(selectedQuestionnaireData.created_at)" readonly />
                  </el-form-item>
                </el-col>
              </el-row>
              
              <el-form-item label="Description">
                <el-input
                  :value="selectedQuestionnaireData.description"
                  type="textarea"
                  :rows="3"
                  readonly
                />
              </el-form-item>
              
              <el-form-item label="Approval Type">
                <el-input value="Questionnaire Approval" readonly />
              </el-form-item>
            </el-card>
          </div>
          
          <!-- Response Approval Form -->
          <div v-if="approvalType === 'response_approval'">
            <el-alert
              title="Response Approval Details"
              description="Configure the response approval parameters for submitted questionnaire responses."
              type="info"
              show-icon
              :closable="false"
              style="margin-bottom: 24px"
            />
            
            <!-- Questionnaire Assignment Selection Card -->
            <el-card class="selection-card" shadow="hover" style="margin-bottom: 24px">
              <template #header>
                <div class="card-header-with-icon">
                  <el-icon class="header-icon" color="#409eff">
                    <Document />
                  </el-icon>
                  <h3>Select Questionnaire Response</h3>
                </div>
              </template>
              
              <el-form-item label="Submitted Questionnaire" prop="selected_questionnaire_assignment" style="margin-bottom: 0">
                <el-select 
                  v-model="selectedQuestionnaireAssignment" 
                  placeholder="Choose a submitted questionnaire to review and approve" 
                  style="width: 100%"
                  :loading="loadingQuestionnaireAssignments"
                  @change="handleQuestionnaireAssignmentChange"
                  filterable
                  size="large"
                >
                  <el-option
                    v-for="assignment in questionnaireAssignments"
                    :key="assignment.assignment_id"
                    :label="getAssignmentDisplayName(assignment)"
                    :value="assignment.assignment_id"
                  >
                    <div class="option-content">
                      <div class="option-title">{{ assignment.questionnaire_name }}</div>
                      <div class="option-subtitle">
                        {{ assignment.vendor_company_name }} ({{ assignment.vendor_code }}) 
                        <el-tag v-if="assignment.overall_score" size="small" type="info" style="margin-left: 8px">
                          Score: {{ assignment.overall_score }}%
                        </el-tag>
                      </div>
                    </div>
                  </el-option>
                </el-select>
              </el-form-item>
              
              <div v-if="questionnaireAssignments.length === 0 && !loadingQuestionnaireAssignments" class="no-assignments">
                <el-empty description="No submitted questionnaires found" :image-size="60">
                  <el-button type="primary" @click="fetchQuestionnaireAssignments">Refresh</el-button>
                </el-empty>
              </div>
            </el-card>
            
            <!-- Assignment Details Display -->
            <div v-if="selectedQuestionnaireAssignment && selectedAssignmentData.assignment_id">
              <el-card class="assignment-details-card" shadow="hover" style="margin-bottom: 24px">
                <template #header>
                  <div class="assignment-header">
                    <div class="header-content">
                      <el-icon class="header-icon" color="#67c23a">
                        <CircleCheckFilled />
                      </el-icon>
                      <div>
                        <h3>{{ selectedAssignmentData.questionnaire_name }}</h3>
                        <p class="header-subtitle">Assignment Details & Vendor Information</p>
                      </div>
                    </div>
                    <div class="assignment-tags">
                      <el-tag :type="getQuestionnaireTypeColor(selectedAssignmentData.questionnaire_type)" size="large">
                        {{ selectedAssignmentData.questionnaire_type }}
                      </el-tag>
                      <el-tag type="success" size="large">
                        {{ selectedAssignmentData.status }}
                      </el-tag>
                      <el-tag v-if="selectedAssignmentData.overall_score" type="warning" size="large">
                        Score: {{ selectedAssignmentData.overall_score }}%
                      </el-tag>
                    </div>
                  </div>
                </template>
                
                <!-- Assignment Summary -->
                <div class="assignment-summary">
                  <el-row :gutter="24">
                    <el-col :span="8">
                      <div class="summary-item">
                        <div class="summary-label">Assignment ID</div>
                        <div class="summary-value">#{{ selectedAssignmentData.assignment_id }}</div>
                      </div>
                    </el-col>
                    <el-col :span="8">
                      <div class="summary-item">
                        <div class="summary-label">Questionnaire Version</div>
                        <div class="summary-value">v{{ selectedAssignmentData.questionnaire_version }}</div>
                      </div>
                    </el-col>
                    <el-col :span="8">
                      <div class="summary-item">
                        <div class="summary-label">Submission Date</div>
                        <div class="summary-value">{{ formatDate(selectedAssignmentData.submission_date) }}</div>
                      </div>
                    </el-col>
                  </el-row>
                </div>
                
                <el-divider content-position="left">
                  <el-icon>
                    <User />
                  </el-icon>
                  Vendor Information
                </el-divider>
                
                <el-row :gutter="20" style="margin-bottom: 20px">
                  <el-col :span="12">
                    <el-form-item label="Company Name">
                      <el-input :value="selectedAssignmentData.vendor_company_name" readonly />
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="Vendor Code">
                      <el-input :value="selectedAssignmentData.vendor_code" readonly />
                    </el-form-item>
                  </el-col>
                </el-row>
                
                <el-divider content-position="left">
                  <el-icon>
                    <Document />
                  </el-icon>
                  Questionnaire Details
                </el-divider>
                
                <el-form-item label="Description" style="margin-bottom: 16px">
                  <el-input
                    :value="selectedAssignmentData.questionnaire_description"
                    type="textarea"
                    :rows="3"
                    readonly
                    class="readonly-textarea"
                  />
                </el-form-item>
                
                <el-form-item v-if="selectedAssignmentData.notes" label="Additional Notes" style="margin-bottom: 0">
                  <el-input
                    :value="selectedAssignmentData.notes"
                    type="textarea"
                    :rows="2"
                    readonly
                    class="readonly-textarea"
                  />
                </el-form-item>
              </el-card>
              
              <!-- Response Statistics Card -->
              <el-card v-if="selectedAssignmentData.response_statistics" class="statistics-card" shadow="hover" style="margin-bottom: 24px">
                <template #header>
                  <div class="card-header-with-icon">
                    <el-icon class="header-icon" color="#e6a23c">
                      <DataAnalysis />
                    </el-icon>
                    <h3>Response Statistics</h3>
                  </div>
                </template>
                
                <el-row :gutter="24">
                  <el-col :span="6">
                    <div class="stat-card">
                      <div class="stat-number">{{ selectedAssignmentData.response_statistics.total_questions }}</div>
                      <div class="stat-label">Total Questions</div>
                    </div>
                  </el-col>
                  <el-col :span="6">
                    <div class="stat-card">
                      <div class="stat-number">{{ selectedAssignmentData.response_statistics.completed_questions }}</div>
                      <div class="stat-label">Completed</div>
                    </div>
                  </el-col>
                  <el-col :span="6">
                    <div class="stat-card">
                      <div class="stat-number">{{ selectedAssignmentData.response_statistics.required_questions }}</div>
                      <div class="stat-label">Required</div>
                    </div>
                  </el-col>
                  <el-col :span="6">
                    <div class="stat-card">
                      <div class="stat-number">{{ selectedAssignmentData.response_statistics.completion_percentage }}%</div>
                      <div class="stat-label">Completion Rate</div>
                    </div>
                  </el-col>
                </el-row>
              </el-card>
              
              <!-- Questions and Responses Card -->
              <el-card v-if="selectedAssignmentData.questions_and_responses && selectedAssignmentData.questions_and_responses.length > 0" 
                       class="questions-responses-card" shadow="hover" style="margin-bottom: 24px">
                <template #header>
                  <div class="card-header-with-icon">
                    <el-icon class="header-icon" color="#909399">
                      <QuestionFilled />
                    </el-icon>
                    <div>
                      <h3>Questions & Vendor Responses</h3>
                      <p class="header-subtitle">Review all questionnaire questions and vendor-provided responses</p>
                    </div>
                  </div>
                </template>
                
                <div class="questions-container">
                  <el-collapse v-model="activeQuestionCollapse" accordion>
                    <el-collapse-item
                      v-for="(qr, index) in selectedAssignmentData.questions_and_responses"
                      :key="qr.question_id"
                      :name="qr.question_id"
                      class="question-item"
                    >
                      <template #title>
                        <div class="question-header">
                          <div class="question-title-section">
                            <span class="question-number">Q{{ qr.display_order }}</span>
                            <span class="question-text">{{ qr.question_text }}</span>
                          </div>
                          <div class="question-badges">
                            <el-tag v-if="qr.is_required" type="danger" size="small">Required</el-tag>
                            <el-tag :type="qr.is_completed ? 'success' : 'warning'" size="small">
                              {{ qr.is_completed ? 'Completed' : 'Incomplete' }}
                            </el-tag>
                            <el-tag v-if="qr.score" type="info" size="small">Score: {{ qr.score }}%</el-tag>
                          </div>
                        </div>
                      </template>
                      
                      <div class="question-content">
                        <el-row :gutter="20">
                          <el-col :span="12">
                            <div class="question-details">
                              <h4>Question Details</h4>
                              <p><strong>Type:</strong> {{ formatQuestionType(qr.question_type) }}</p>
                              <p v-if="qr.question_category"><strong>Category:</strong> {{ qr.question_category }}</p>
                              <p v-if="qr.help_text"><strong>Help Text:</strong> {{ qr.help_text }}</p>
                              <p><strong>Scoring Weight:</strong> {{ qr.scoring_weight || 1.0 }}</p>
                              <div v-if="qr.options" class="question-options">
                                <p><strong>Available Options:</strong></p>
                                <pre>{{ JSON.stringify(qr.options, null, 2) }}</pre>
                              </div>
                              <div v-if="qr.conditional_logic" class="conditional-logic">
                                <p><strong>Conditional Logic:</strong></p>
                                <pre>{{ JSON.stringify(qr.conditional_logic, null, 2) }}</pre>
                              </div>
                            </div>
                          </el-col>
                          <el-col :span="12">
                            <div class="response-details">
                              <h4>Vendor Response</h4>
                              <div class="response-content">
                                <div v-if="qr.vendor_response" class="response-text">
                                  <strong>Response:</strong>
                                  <div class="response-value">{{ qr.vendor_response }}</div>
                                </div>
                                <div v-else class="no-response">
                                  <el-alert title="No response provided" type="warning" :closable="false" />
                                </div>
                                
                                <div v-if="qr.vendor_comment" class="vendor-comment">
                                  <strong>Vendor Comment:</strong>
                                  <div class="comment-value">{{ qr.vendor_comment }}</div>
                                </div>
                                
                                <div v-if="qr.file_uploads && qr.file_uploads.length > 0" class="file-uploads">
                                  <strong>File Uploads:</strong>
                                  <ul>
                                    <li v-for="file in qr.file_uploads" :key="file.name">{{ file.name }}</li>
                                  </ul>
                                </div>
                                
                                <div v-if="qr.reviewer_comment" class="reviewer-comment">
                                  <strong>Previous Review Comment:</strong>
                                  <div class="comment-value">{{ qr.reviewer_comment }}</div>
                                </div>
                              </div>
                            </div>
                          </el-col>
                        </el-row>
                      </div>
                    </el-collapse-item>
                  </el-collapse>
                </div>
              </el-card>
            </div>
            
            <el-card class="response-card" shadow="hover">
              <template #header>
                <div class="card-header-with-icon">
                  <el-icon class="header-icon" color="#409eff">
                    <Setting />
                  </el-icon>
                  <h3>Response Approval Configuration</h3>
                </div>
              </template>
              
              <el-row :gutter="20" style="margin-bottom: 20px">
                <el-col :span="12">
                  <el-form-item label="Response Type">
                    <el-select v-model="responseType" placeholder="Select response type" style="width: 100%" size="large">
                      <el-option label="Questionnaire Review" value="questionnaire_review">
                        <div class="option-content">
                          <div class="option-title">Questionnaire Review</div>
                          <div class="option-subtitle">General review of questionnaire responses</div>
                        </div>
                      </el-option>
                      <el-option label="Vendor Response Review" value="vendor_response_review">
                        <div class="option-content">
                          <div class="option-title">Vendor Response Review</div>
                          <div class="option-subtitle">Detailed review of vendor-specific responses</div>
                        </div>
                      </el-option>
                      <el-option label="Compliance Assessment" value="compliance_assessment">
                        <div class="option-content">
                          <div class="option-title">Compliance Assessment</div>
                          <div class="option-subtitle">Compliance and regulatory review</div>
                        </div>
                      </el-option>
                      <el-option label="Risk Assessment" value="risk_assessment">
                        <div class="option-content">
                          <div class="option-title">Risk Assessment</div>
                          <div class="option-subtitle">Risk evaluation and mitigation review</div>
                        </div>
                      </el-option>
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="Priority Level">
                    <el-select v-model="responsePriority" placeholder="Select priority" style="width: 100%" size="large">
                      <el-option label="Low" value="LOW">
                        <el-tag type="success" size="small">Low</el-tag>
                        <span style="margin-left: 8px">Standard review timeline</span>
                      </el-option>
                      <el-option label="Medium" value="MEDIUM">
                        <el-tag type="warning" size="small">Medium</el-tag>
                        <span style="margin-left: 8px">Normal business priority</span>
                      </el-option>
                      <el-option label="High" value="HIGH">
                        <el-tag type="danger" size="small">High</el-tag>
                        <span style="margin-left: 8px">Expedited review required</span>
                      </el-option>
                      <el-option label="Critical" value="CRITICAL">
                        <el-tag type="danger" size="small">Critical</el-tag>
                        <span style="margin-left: 8px">Immediate attention needed</span>
                      </el-option>
                    </el-select>
                  </el-form-item>
                </el-col>
              </el-row>
              
              <el-form-item label="Review Comments & Assessment Notes">
                <el-input
                  v-model="responseData"
                  type="textarea"
                  :rows="5"
                  placeholder="Enter detailed review comments, assessment notes, approval criteria, or any specific concerns that need to be addressed during the approval process..."
                  show-word-limit
                  maxlength="1000"
                />
              </el-form-item>
            </el-card>
          </div>
          
          <!-- Final Vendor Approval Form -->
          <div v-if="approvalType === 'final_vendor_approval'">
            <el-alert
              title="Final Vendor Approval"
              description="This approval type is used for final vendor decisions and approvals."
              type="success"
              show-icon
              :closable="false"
              style="margin-bottom: 20px"
            />
            
            <!-- Vendor Details Display -->
            <div v-if="selectedVendor && selectedVendorData.id">
              <el-card class="vendor-details-card" shadow="hover" style="margin-bottom: 20px">
                <template #header>
                  <div class="vendor-header">
                    <h3>{{ selectedVendorData.company_name }}</h3>
                    <div class="vendor-tags">
                      <el-tag :type="getVendorRiskColor(selectedVendorData.risk_level)">
                        {{ selectedVendorData.risk_level }}
                      </el-tag>
                      <el-tag v-if="selectedVendorData.is_critical_vendor" type="warning">
                        Critical Vendor
                      </el-tag>
                      <el-tag :type="getVendorStatusColor(selectedVendorData.status)">
                        {{ selectedVendorData.status }}
                      </el-tag>
                    </div>
                  </div>
                </template>
                
                <el-row :gutter="20">
                  <el-col :span="12">
                    <el-form-item label="Vendor Code">
                      <el-input :value="selectedVendorData.vendor_code" readonly />
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="Legal Name">
                      <el-input :value="selectedVendorData.legal_name" readonly />
                    </el-form-item>
                  </el-col>
                </el-row>
                
                <el-row :gutter="20">
                  <el-col :span="12">
                    <el-form-item label="Business Type">
                      <el-input :value="selectedVendorData.business_type" readonly />
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="Industry Sector">
                      <el-input :value="selectedVendorData.industry_sector" readonly />
                    </el-form-item>
                  </el-col>
                </el-row>
                
                <el-row :gutter="20">
                  <el-col :span="12">
                    <el-form-item label="Vendor Category">
                      <el-input :value="selectedVendorData.vendor_category" readonly />
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="Website">
                      <el-input :value="selectedVendorData.website" readonly />
                    </el-form-item>
                  </el-col>
                </el-row>
                
                <el-form-item label="Description">
                  <el-input
                    :value="selectedVendorData.description"
                    type="textarea"
                    :rows="2"
                    readonly
                  />
                </el-form-item>
                
                <div class="vendor-access-info">
                  <el-row :gutter="20">
                    <el-col :span="8">
                      <el-form-item label="Data Access">
                        <el-tag :type="selectedVendorData.has_data_access ? 'success' : 'info'">
                          {{ selectedVendorData.has_data_access ? 'Yes' : 'No' }}
                        </el-tag>
                      </el-form-item>
                    </el-col>
                    <el-col :span="8">
                      <el-form-item label="System Access">
                        <el-tag :type="selectedVendorData.has_system_access ? 'success' : 'info'">
                          {{ selectedVendorData.has_system_access ? 'Yes' : 'No' }}
                        </el-tag>
                      </el-form-item>
                    </el-col>
                    <el-col :span="8">
                      <el-form-item label="Employee Count">
                        <el-input :value="selectedVendorData.employee_count?.toString() || 'N/A'" readonly />
                      </el-form-item>
                    </el-col>
                  </el-row>
                </div>
              </el-card>
            </div>
            
            <!-- Vendor Risks Display -->
            <div v-if="selectedVendor && (internalRisks.length > 0 || externalRisks.length > 0)">
              <el-card class="vendor-risks-card" shadow="hover" style="margin-bottom: 20px">
                <template #header>
                  <div class="risks-header">
                    <h3>Vendor Risk Assessment</h3>
                    <div class="risk-summary-tags">
                      <el-tag type="info">Total: {{ riskSummary.total_risks || (internalRisks.length + externalRisks.length) }}</el-tag>
                      <el-tag type="primary">Internal: {{ internalRisks.length }}</el-tag>
                      <el-tag type="warning">External: {{ externalRisks.length }}</el-tag>
                      <el-tag v-if="riskSummary.high_priority > 0" type="danger">High: {{ riskSummary.high_priority }}</el-tag>
                      <el-tag v-if="riskSummary.medium_priority > 0" type="warning">Medium: {{ riskSummary.medium_priority }}</el-tag>
                      <el-tag v-if="riskSummary.low_priority > 0" type="success">Low: {{ riskSummary.low_priority }}</el-tag>
                    </div>
                  </div>
                </template>
                
                <div class="risk-overview">
                  <el-row :gutter="20" style="margin-bottom: 20px">
                    <el-col :span="8">
                      <div class="risk-stat">
                        <span class="stat-label">Internal Risks:</span>
                        <el-tag :type="internalRisks.length > 0 ? 'primary' : 'success'">
                          {{ internalRisks.length }}
                        </el-tag>
                      </div>
                    </el-col>
                    <el-col :span="8">
                      <div class="risk-stat">
                        <span class="stat-label">External Risks:</span>
                        <el-tag :type="externalRisks.length > 0 ? 'warning' : 'success'">
                          {{ externalRisks.length }}
                        </el-tag>
                      </div>
                    </el-col>
                    <el-col :span="8">
                      <div class="risk-stat">
                        <span class="stat-label">Escalated:</span>
                        <el-tag :type="externalRisks.filter(r => r.resolution_status === 'ESCALATED').length > 0 ? 'danger' : 'success'">
                          {{ externalRisks.filter(r => r.resolution_status === 'ESCALATED').length }}
                        </el-tag>
                      </div>
                    </el-col>
                  </el-row>
                </div>
                
                <!-- Internal Risks Section -->
                <div v-if="internalRisks.length > 0" class="risk-section internal-risks-section">
                  <div class="section-header">
                    <h4><i class="el-icon-warning-outline"></i> Internal Risks ({{ internalRisks.length }})</h4>
                    <el-tag type="primary" size="small">Internal Assessment</el-tag>
                  </div>
                  
                  <el-collapse v-model="activeInternalRiskCollapse">
                    <el-collapse-item
                      v-for="risk in internalRisks.slice(0, 3)"
                      :key="'internal-' + risk.id"
                      :title="risk.title"
                      :name="'internal-' + risk.id"
                    >
                      <template #title>
                        <div class="risk-item-header internal-risk-header">
                          <span class="risk-title">{{ risk.title }}</span>
                          <div class="risk-badges">
                            <el-tag type="primary" size="small">Internal</el-tag>
                            <el-tag :type="getRiskPriorityColor(risk.priority)" size="small">
                              {{ risk.priority || 'N/A' }}
                            </el-tag>
                            <el-tag :type="getRiskStatusColor(risk.status)" size="small">
                              {{ risk.status || 'N/A' }}
                            </el-tag>
                            <el-tag v-if="risk.score" type="info" size="small">
                              Score: {{ risk.score }}
                            </el-tag>
                          </div>
                        </div>
                      </template>
                      
                      <div class="risk-details internal-risk-details">
                        <el-row :gutter="20">
                          <el-col :span="12">
                            <p><strong>Description:</strong></p>
                            <p>{{ risk.description || 'No description provided' }}</p>
                          </el-col>
                          <el-col :span="12">
                            <div class="risk-metrics">
                              <p><strong>Risk Metrics:</strong></p>
                              <el-tag type="info" size="small" style="margin-right: 8px">
                                Likelihood: {{ risk.likelihood || 'N/A' }}
                              </el-tag>
                              <el-tag type="info" size="small">
                                Impact: {{ risk.impact || 'N/A' }}
                              </el-tag>
                            </div>
                          </el-col>
                        </el-row>
                        
                        <div v-if="risk.ai_explanation" class="ai-explanation">
                          <p><strong>AI Analysis:</strong></p>
                          <p>{{ risk.ai_explanation }}</p>
                        </div>
                        
                        <div v-if="risk.suggested_mitigations" class="suggested-mitigations">
                          <p><strong>Suggested Mitigations:</strong></p>
                          <ul>
                            <li v-for="(mitigation, index) in risk.suggested_mitigations" :key="index">
                              {{ typeof mitigation === 'object' ? mitigation.description || JSON.stringify(mitigation) : mitigation }}
                            </li>
                          </ul>
                        </div>
                        
                        <div class="risk-metadata">
                          <span class="metadata-item">ID: {{ risk.id }}</span>
                          <span v-if="risk.module_id" class="metadata-item">Module: {{ risk.module_id }}</span>
                          <span v-if="risk.created_at" class="metadata-item">Created: {{ formatDate(risk.created_at) }}</span>
                        </div>
                      </div>
                    </el-collapse-item>
                  </el-collapse>
                  
                  <div v-if="internalRisks.length > 3" class="more-risks-info">
                    <el-alert
                      :title="`${internalRisks.length - 3} more internal risks available`"
                      type="info"
                      show-icon
                      :closable="false"
                    />
                  </div>
                </div>
                
                <!-- External Risks Section -->
                <div v-if="externalRisks.length > 0" class="risk-section external-risks-section">
                  <div class="section-header">
                    <h4><i class="el-icon-search"></i> External Screening Risks ({{ externalRisks.length }})</h4>
                    <el-tag type="warning" size="small">External Screening</el-tag>
                  </div>
                  
                  <el-collapse v-model="activeExternalRiskCollapse">
                    <el-collapse-item
                      v-for="risk in externalRisks.slice(0, 3)"
                      :key="'external-' + risk.match_id"
                      :title="risk.match_type || 'Screening Match'"
                      :name="'external-' + risk.match_id"
                    >
                      <template #title>
                        <div class="risk-item-header external-risk-header">
                          <span class="risk-title">{{ risk.match_type || 'Screening Match' }}</span>
                          <div class="risk-badges">
                            <el-tag type="warning" size="small">External</el-tag>
                            <el-tag :type="getScreeningTypeColor(risk.screening_type)" size="small">
                              {{ risk.screening_type || 'N/A' }}
                            </el-tag>
                            <el-tag :type="getResolutionStatusColor(risk.resolution_status)" size="small">
                              {{ risk.resolution_status || 'N/A' }}
                            </el-tag>
                            <el-tag v-if="risk.match_score" type="info" size="small">
                              Score: {{ risk.match_score }}%
                            </el-tag>
                          </div>
                        </div>
                      </template>
                      
                      <div class="risk-details external-risk-details">
                        <el-row :gutter="20">
                          <el-col :span="12">
                            <p><strong>Match Details:</strong></p>
                            <p>{{ getMatchDescription(risk) }}</p>
                            
                            <div v-if="risk.search_terms" class="search-terms">
                              <p><strong>Search Terms:</strong></p>
                              <div class="search-terms-list">
                                <el-tag 
                                  v-for="(term, index) in getSearchTerms(risk.search_terms)" 
                                  :key="index" 
                                  size="small" 
                                  type="info"
                                  style="margin: 2px;"
                                >
                                  {{ term }}
                                </el-tag>
                              </div>
                            </div>
                          </el-col>
                          <el-col :span="12">
                            <div class="screening-info">
                              <p><strong>Screening Info:</strong></p>
                              <el-tag type="info" size="small" style="margin-right: 8px">
                                Date: {{ formatDate(risk.screening_date) }}
                              </el-tag>
                              <el-tag type="info" size="small" style="margin-right: 8px">
                                Total Matches: {{ risk.total_matches || 0 }}
                              </el-tag>
                              <el-tag v-if="risk.high_risk_matches" type="danger" size="small">
                                High Risk: {{ risk.high_risk_matches }}
                              </el-tag>
                            </div>
                          </el-col>
                        </el-row>
                        
                        <div v-if="risk.match_details" class="match-details">
                          <p><strong>Detailed Match Information:</strong></p>
                          <div class="match-details-content">
                            {{ formatMatchDetails(risk.match_details) }}
                          </div>
                        </div>
                        
                        <div v-if="risk.resolution_notes" class="resolution-notes">
                          <p><strong>Resolution Notes:</strong></p>
                          <p>{{ risk.resolution_notes }}</p>
                        </div>
                        
                        <div class="risk-metadata">
                          <span class="metadata-item">Match ID: {{ risk.match_id }}</span>
                          <span class="metadata-item">Screening ID: {{ risk.screening_id }}</span>
                          <span v-if="risk.resolved_date" class="metadata-item">Resolved: {{ formatDate(risk.resolved_date) }}</span>
                        </div>
                      </div>
                    </el-collapse-item>
                  </el-collapse>
                  
                  <div v-if="externalRisks.length > 3" class="more-risks-info">
                    <el-alert
                      :title="`${externalRisks.length - 3} more external screening risks available`"
                      type="warning"
                      show-icon
                      :closable="false"
                    />
                  </div>
                </div>
                
                <!-- No Risks Message -->
                <div v-if="internalRisks.length === 0 && externalRisks.length === 0" class="no-risks-section">
                  <el-empty description="No risks identified for this vendor">
                    <div class="no-risks-content">
                      <i class="el-icon-success"></i>
                      <h6>No Escalated Risks Found</h6>
                      <p>No internal risks or external screening escalations identified for this vendor.</p>
                    </div>
                  </el-empty>
                </div>
              </el-card>
            </div>
            
          </div>
        </div>

        <!-- Stages Configuration -->
        <el-divider content-position="left">Stages Configuration</el-divider>
        
        <div class="stages-section">
          <div class="stages-header">
            <h3>Workflow Stages</h3>
            <el-button type="primary" @click="addStage" :icon="Plus">
              Add Stage
            </el-button>
          </div>

          <div v-if="stages.length === 0" class="no-stages">
            <el-empty description="No stages configured yet">
              <el-button type="primary" @click="addStage">Add First Stage</el-button>
            </el-empty>
          </div>

          <div v-else class="stages-list">
            <el-card 
              v-for="(stage, index) in stages" 
              :key="index" 
              class="stage-card"
              shadow="hover"
            >
              <template #header>
                <div class="stage-header">
                  <span class="stage-title">{{ getStageTitle(index + 1) }}</span>
                  <div class="stage-actions">
                    <el-button 
                      v-if="workflowForm.workflow_type === 'MULTI_LEVEL' && index > 0" 
                      type="text" 
                      @click="moveStage(index, 'up')"
                      :icon="ArrowUp"
                    />
                    <el-button 
                      v-if="workflowForm.workflow_type === 'MULTI_LEVEL' && index < stages.length - 1" 
                      type="text" 
                      @click="moveStage(index, 'down')"
                      :icon="ArrowDown"
                    />
                    <el-button 
                      type="text" 
                      @click="removeStage(index)"
                      :icon="Delete"
                      style="color: #f56c6c"
                    />
                  </div>
                </div>
              </template>

              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item :label="workflowForm.workflow_type === 'MULTI_PERSON' ? 'Approval Name' : `${getStageTitle(index + 1)} Name`">
                    <el-input 
                      v-model.lazy="stage.stage_name" 
                      :placeholder="workflowForm.workflow_type === 'MULTI_PERSON' ? requestForm.request_title || 'Enter approval name' : getStagePlaceholder(index + 1)"
                      :readonly="workflowForm.workflow_type === 'MULTI_PERSON'"
                    />
                  </el-form-item>
                </el-col>
                <el-col :span="12" v-if="workflowForm.workflow_type === 'MULTI_LEVEL'">
                  <el-form-item :label="`${getStageTitle(index + 1)} Order`">
                    <el-input-number 
                      v-model="stage.stage_order" 
                      :min="1" 
                      :max="stages.length"
                      style="width: 100%"
                    />
                  </el-form-item>
                </el-col>
              </el-row>

              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item :label="`Assigned User`">
                    <el-select 
                      v-model="stage.assigned_user_id" 
                      placeholder="Select user"
                      style="width: 100%"
                      @change="(value) => handleUserSelection(stage, value)"
                      :loading="loadingUsers"
                    >
                      <el-option
                        v-for="user in users"
                        :key="user.id"
                        :label="getUserDisplayName(user)"
                        :value="user.id"
                      />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item :label="`User Role`">
                    <el-input 
                      v-model="stage.assigned_user_role" 
                      placeholder="Auto-populated from user"
                      readonly
                    />
                  </el-form-item>
                </el-col>
              </el-row>

              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item :label="`Department`">
                    <el-input 
                      v-model="stage.department" 
                      placeholder="Auto-populated from user"
                      readonly
                    />
                  </el-form-item>
                </el-col>
              </el-row>

              <el-row :gutter="20">
                                 <el-col :span="12">
                   <el-form-item :label="`Deadline Date`">
                     <el-date-picker
                       v-model="stage.deadline_date"
                       type="date"
                       placeholder="Select deadline date"
                       style="width: 100%"
                       :disabled-date="(time) => time.getTime() < Date.now() - 8.64e7"
                     />
                   </el-form-item>
                 </el-col>
              </el-row>

              <el-form-item :label="`${getStageTitle(index + 1)} Description`">
                <el-input 
                  v-model.lazy="stage.stage_description" 
                  type="textarea" 
                  :rows="2"
                  placeholder="Describe what this stage involves..."
                />
              </el-form-item>

              <el-form-item>
                <el-checkbox v-model="stage.is_mandatory">This stage is mandatory</el-checkbox>
              </el-form-item>
            </el-card>
          </div>
        </div>

        <!-- Form Actions -->
        <el-divider />
        
        <div class="form-actions">
          <el-button @click="resetForm">Reset</el-button>
          <el-button type="primary" @click="submitWorkflow" :loading="submitting">
            Create Workflow & Request
          </el-button>
        </div>
      </el-form>
    </el-card>

    <!-- Success Dialog -->
    <el-dialog
      v-model="successDialogVisible"
      title="Workflow & Request Created Successfully"
      width="500px"
      :close-on-click-modal="false"
    >
      <div class="success-content">
        <el-icon class="success-icon" color="#67c23a" size="48">
          <CircleCheckFilled />
        </el-icon>
        <h3>Success!</h3>
        <p>Your workflow and approval request have been created successfully.</p>
        <div class="workflow-info">
          <p><strong>Workflow ID:</strong> {{ createdWorkflowId }}</p>
          <p><strong>Request ID:</strong> {{ createdRequestId }}</p>
          <p><strong>Workflow Type:</strong> {{ getWorkflowTypeLabel(workflowForm.workflow_type) }}</p>
          <p><strong>Stages:</strong> {{ stages.length }}</p>
          <p><strong>Status:</strong> <el-tag type="warning">PENDING</el-tag></p>
        </div>
      </div>
      <template #footer>
        <el-button @click="successDialogVisible = false">Close</el-button>
        <el-button type="primary" @click="createAnother">Create Another</el-button>
      </template>
    </el-dialog>

    <!-- Help Dialog -->
    <el-dialog
      v-model="helpDialogVisible"
      title="JSON Payload Help"
      width="600px"
    >
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
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, shallowRef, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Plus, 
  Delete, 
  ArrowUp, 
  ArrowDown, 
  CircleCheckFilled,
  QuestionFilled, 
  MagicStick, 
  Check, 
  Document,
  User,
  Setting,
  DataAnalysis
} from '@element-plus/icons-vue'
import api from '@/utils/api'
import { getCurrentUserId } from '@/utils/session'
import { getMockUsers } from '@/services/users'
import loggingService from '@/services/loggingService'

export default {
  name: 'ComprehensiveWorkflowCreator',
  components: {
    Plus,
    Delete,
    ArrowUp,
    ArrowDown,
    CircleCheckFilled,
    QuestionFilled,
    MagicStick,
    Check,
    Document,
    User,
    Setting,
    DataAnalysis
  },
  setup() {
    const workflowForm = reactive({
      workflow_name: '',
      workflow_type: 'MULTI_LEVEL',
      description: '',
      business_object_type: 'Vendor',
      created_by: 'GRC Administrator',
    })
    
    const requestForm = reactive({
      request_title: '',
      request_description: '',
      requester_id: 60,
      requester_name: 'GRC Administrator',
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
    
    // Update created_by when component mounts and fetch users
    onMounted(async () => {
      await loggingService.logPageView('Vendor', 'Sample Workflow')
      await fetchUsers()
    })

    // Watch for request title changes and update stage names for Multi-Person workflows
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
        ElMessage.warning('Using mock user data - API endpoint not available')
      } finally {
        loadingUsers.value = false
      }
    }

    const workflowRules = {
      workflow_name: [
        { required: true, message: 'Please enter workflow name', trigger: 'blur' }
      ],
      workflow_type: [
        { required: true, message: 'Please select workflow type', trigger: 'change' }
      ],
      description: [
        { required: true, message: 'Please enter workflow description', trigger: 'blur' }
      ]
    }

    const requestRules = {
      request_title: [
        { required: true, message: 'Please enter request title', trigger: 'blur' }
      ],
      request_description: [
        { required: true, message: 'Please enter request description', trigger: 'blur' }
      ],
      requester_id: [
        { required: true, message: 'Please enter requester ID', trigger: 'blur' }
      ]
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

    const addStage = () => {
      const newStage = {
        stage_order: getDefaultStageOrder(),
        stage_name: workflowForm.workflow_type === 'MULTI_PERSON' ? requestForm.request_title : '',
        stage_description: '',
        assigned_user_id: 60,
        assigned_user_name: 'GRC Administrator',
        assigned_user_role: 'GRC Administrator',
        department: '2',
        stage_type: workflowForm.workflow_type === 'MULTI_PERSON' ? 'PARALLEL' : 'SEQUENTIAL',
        deadline_date: null,
        is_mandatory: true
      }
      stages.value.push(newStage)
    }

    const removeStage = (index) => {
      ElMessageBox.confirm(
        'Are you sure you want to remove this stage?',
        'Warning',
        {
          confirmButtonText: 'Yes',
          cancelButtonText: 'No',
          type: 'warning'
        }
      ).then(() => {
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
        ElMessage.success('Stage removed successfully')
      })
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
        ElMessage.error('At least one stage is required')
        return false
      }

      for (let i = 0; i < stages.value.length; i++) {
        const stage = stages.value[i]
        if (!stage.stage_name || !stage.assigned_user_id || !stage.assigned_user_name || !stage.deadline_date) {
          ElMessage.error(`Stage ${i + 1} is missing required information (name, user, or deadline)`)
          return false
        }
      }

      return true
    }

    const submitWorkflow = async () => {
      try {
        await workflowFormRef.value.validate()
        
        if (!validateStages()) {
          return
        }

        submitting.value = true

        // Prepare the submission data
        const submitData = {
          workflow: {
            ...workflowForm,
            business_object_type: workflowForm.business_object_type || requestForm.business_object_type
          },
          request: {
            ...requestForm,
            business_object_type: workflowForm.business_object_type || requestForm.business_object_type,
            request_data: getRequestData()
          },
          stages: stages.value.map(stage => ({
          ...stage,
          deadline_date: stage.deadline_date ? new Date(stage.deadline_date).toISOString() : null
        }))
        }
        
        console.log('Submitting comprehensive workflow:', submitData)
        
        const response = await api.post('/api/v1/vendor-approval/create-workflow-request/', submitData)
        
        createdWorkflowId.value = response.data.workflow_id
        createdRequestId.value = response.data.approval_id
        successDialogVisible.value = true
        
        ElMessage.success('Workflow and request created successfully!')
        
      } catch (error) {
        console.error('Error creating workflow and request:', error)
        ElMessage.error(error.response?.data?.error || 'Failed to create workflow and request')
      } finally {
        submitting.value = false
      }
    }

    const resetForm = () => {
      try {
        if (workflowFormRef.value && typeof workflowFormRef.value.resetFields === 'function') {
      workflowFormRef.value.resetFields()
        }
        
        // Reset all form data manually
        Object.assign(workflowForm, {
          workflow_name: '',
          workflow_type: 'MULTI_LEVEL',
          description: '',
          business_object_type: 'Vendor',
          created_by: 'GRC Administrator'
        })
        
        Object.assign(requestForm, {
          request_title: '',
          request_description: '',
          requester_id: 60,
          requester_name: 'GRC Administrator',
          requester_department: '',
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
        
      ElMessage.info('Form reset successfully')
      } catch (error) {
        console.error('Error resetting form:', error)
        ElMessage.error('Failed to reset form')
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
      const selectedUser = users.value.find(user => user.id === userId)
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

    // JSON handling functions
    const formatJSON = () => {
      try {
        const parsed = JSON.parse(jsonPayloadString.value)
        jsonPayloadString.value = JSON.stringify(parsed, null, 2)
        ElMessage.success('JSON formatted successfully')
      } catch (e) {
        ElMessage.error('Invalid JSON format')
      }
    }

    const validateJSON = () => {
      try {
        JSON.parse(jsonPayloadString.value)
        ElMessage.success('JSON is valid')
      } catch (e) {
        ElMessage.error('Invalid JSON format')
      }
    }

    const loadSamplePayload = () => {
      const businessType = (workflowForm.business_object_type || requestForm.business_object_type || 'policy').toLowerCase()
      const samplePayloads = {
        policy: JSON.stringify({
          policy_name: "Employee Remote Work Policy",
          policy_content: "This policy outlines guidelines for remote work...",
          effective_date: "2024-02-01",
          scope: ["All Employees", "Remote Workers"],
          budget_impact: 50000,
          departments: ["HR", "IT", "Finance"]
        }, null, 2),
        contract: JSON.stringify({
          contract_title: "Vendor Service Agreement",
          vendor_name: "TechCorp Solutions",
          contract_value: 150000,
          start_date: "2024-03-01",
          end_date: "2025-02-28",
          terms: "Standard service agreement terms...",
          payment_terms: "Net 30"
        }, null, 2),
        purchase: JSON.stringify({
          item_description: "Office Equipment Package",
          items: [
            { name: "Laptop", quantity: 10, unit_price: 1200 },
            { name: "Monitor", quantity: 10, unit_price: 300 }
          ],
          total_amount: 15000,
          supplier: "Office Supplies Inc",
          urgency: "Medium",
          delivery_date: "2024-02-15"
        }, null, 2)
      }
      
      if (samplePayloads[businessType]) {
        jsonPayloadString.value = samplePayloads[businessType]
        ElMessage.success('Sample payload loaded')
      } else {
        jsonPayloadString.value = samplePayloads.policy
        ElMessage.success('Default sample payload loaded')
      }
    }

    const showPayloadHelp = () => {
      helpDialogVisible.value = true
    }

    // Questionnaire handling functions
    const fetchQuestionnaires = async () => {
      try {
        loadingQuestionnaires.value = true
        const response = await api.get('/api/v1/vendor-approval/questionnaires/active/')
        questionnaires.value = response.data
        
        if (questionnaires.value.length === 0) {
          ElMessage.warning('No questionnaires found in the database.')
        }
      } catch (error) {
        console.error('Error fetching questionnaires:', error)
        ElMessage.error('Failed to load questionnaires from database.')
        questionnaires.value = []
      } finally {
        loadingQuestionnaires.value = false
      }
    }

    const handleApprovalTypeChange = (value) => {
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

    const handleQuestionnaireChange = (questionnaireId) => {
      const questionnaire = questionnaires.value.find(q => q.questionnaire_id === questionnaireId)
      if (questionnaire) {
        // Store the questionnaire data for display
        selectedQuestionnaireData.value = questionnaire
        
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
        'ONBOARDING': 'primary',
        'ANNUAL': 'success',
        'INCIDENT': 'warning',
        'CUSTOM': 'info'
      }
      return colorMap[type] || 'default'
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
          ElMessage.warning('No vendors found in the database.')
        }
      } catch (error) {
        console.error('Error fetching vendors:', error)
        ElMessage.error('Failed to load vendors from database.')
        vendors.value = []
      } finally {
        loadingVendors.value = false
      }
    }

    const handleVendorChange = async (vendorId) => {
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
        ElMessage.error('Failed to load vendor details.')
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
        'LOW': 'success',
        'MEDIUM': 'warning',
        'HIGH': 'danger',
        'CRITICAL': 'danger'
      }
      return colorMap[riskLevel?.toUpperCase()] || 'info'
    }

    const getVendorStatusColor = (status) => {
      const colorMap = {
        'ACTIVE': 'success',
        'INACTIVE': 'info',
        'PENDING': 'warning',
        'SUSPENDED': 'danger',
        'TERMINATED': 'danger'
      }
      return colorMap[status?.toUpperCase()] || 'info'
    }

    const getRiskPriorityColor = (priority) => {
      const colorMap = {
        'LOW': 'success',
        'MEDIUM': 'warning',
        'HIGH': 'danger',
        'CRITICAL': 'danger'
      }
      return colorMap[priority?.toUpperCase()] || 'info'
    }

    const getRiskStatusColor = (status) => {
      const colorMap = {
        'OPEN': 'danger',
        'ACTIVE': 'danger',
        'IDENTIFIED': 'warning',
        'IN_PROGRESS': 'warning',
        'MITIGATED': 'success',
        'CLOSED': 'success',
        'RESOLVED': 'success'
      }
      return colorMap[status?.toUpperCase()] || 'info'
    }

    const getScreeningTypeColor = (screeningType) => {
      const colorMap = {
        'WORLDCHECK': 'danger',
        'OFAC': 'danger',
        'PEP': 'warning',
        'SANCTIONS': 'danger',
        'ADVERSE_MEDIA': 'warning'
      }
      return colorMap[screeningType?.toUpperCase()] || 'info'
    }

    const getResolutionStatusColor = (status) => {
      const colorMap = {
        'PENDING': 'warning',
        'CLEARED': 'success',
        'ESCALATED': 'danger',
        'BLOCKED': 'danger'
      }
      return colorMap[status?.toUpperCase()] || 'info'
    }

    const getMatchDescription = (risk) => {
      if (risk.match_details) {
        try {
          const details = typeof risk.match_details === 'string' ? JSON.parse(risk.match_details) : risk.match_details
          return details.description || details.summary || `${risk.match_type} screening match found`
        } catch {
          return `${risk.match_type} screening match found`
        }
      }
      return `${risk.match_type || 'Screening'} match identified during external screening`
    }

    const formatMatchDetails = (details) => {
      if (!details) return 'No details available'
      try {
        const parsed = typeof details === 'string' ? JSON.parse(details) : details
        if (typeof parsed === 'object') {
          return Object.entries(parsed).map(([key, value]) => `${key}: ${value}`).join(', ')
        }
        return String(parsed)
      } catch {
        return String(details)
      }
    }

    const getSearchTerms = (terms) => {
      if (!terms) return []
      try {
        const parsed = typeof terms === 'string' ? JSON.parse(terms) : terms
        if (Array.isArray(parsed)) return parsed
        if (typeof parsed === 'object') return Object.values(parsed)
        return [String(parsed)]
      } catch {
        return [String(terms)]
      }
    }

    
    // Questionnaire assignment handling functions
    const fetchQuestionnaireAssignments = async () => {
      try {
        loadingQuestionnaireAssignments.value = true
        const response = await api.get('/api/v1/vendor-approval/questionnaire-assignments/submitted/')
        questionnaireAssignments.value = response.data.assignments || []
        
        if (questionnaireAssignments.value.length === 0) {
          ElMessage.warning('No submitted questionnaire assignments found.')
        }
      } catch (error) {
        console.error('Error fetching questionnaire assignments:', error)
        ElMessage.error('Failed to load questionnaire assignments.')
        questionnaireAssignments.value = []
      } finally {
        loadingQuestionnaireAssignments.value = false
      }
    }

    const handleQuestionnaireAssignmentChange = (assignmentId) => {
      const assignment = questionnaireAssignments.value.find(a => a.assignment_id === assignmentId)
      if (assignment) {
        selectedAssignmentData.value = assignment
        
        // Set default response type for questionnaire reviews
        responseType.value = 'questionnaire_review'
        
        // Update response data with assignment context
        responseData.value = `Review of questionnaire assignment ${assignment.assignment_id} for ${assignment.vendor_company_name}`
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
        return 0  // Multi-person stages start from 0
      } else {
        return stages.value.length + 1  // Multi-level stages are sequential
      }
    }

    const getRequestData = () => {
      if (approvalType.value === 'questionnaire_approval' && selectedQuestionnaireData.value.questionnaire_id) {
        return {
          questionnaire_id: selectedQuestionnaireData.value.questionnaire_id,
          questionnaire_name: selectedQuestionnaireData.value.questionnaire_name,
          questionnaire_type: selectedQuestionnaireData.value.questionnaire_type,
          description: selectedQuestionnaireData.value.description,
          version: selectedQuestionnaireData.value.version,
          approval_type: 'questionnaire_approval'
        }
      } else if (approvalType.value === 'response_approval') {
        return {
          response_type: responseType.value,
          response_data: responseData.value,
          response_priority: responsePriority.value,
          questionnaire_assignment_id: selectedQuestionnaireAssignment.value,
          approval_type: 'response_approval',
          
          // Comprehensive assignment data for approvers
          assignment_summary: {
            assignment_id: selectedAssignmentData.value.assignment_id,
            questionnaire_id: selectedAssignmentData.value.questionnaire_id,
            questionnaire_name: selectedAssignmentData.value.questionnaire_name,
            questionnaire_type: selectedAssignmentData.value.questionnaire_type,
            questionnaire_description: selectedAssignmentData.value.questionnaire_description,
            questionnaire_version: selectedAssignmentData.value.questionnaire_version,
            submission_date: selectedAssignmentData.value.submission_date,
            overall_score: selectedAssignmentData.value.overall_score,
            status: selectedAssignmentData.value.status
          },
          
          // Vendor information
          vendor_information: {
            vendor_id: selectedAssignmentData.value.vendor_id,
            company_name: selectedAssignmentData.value.vendor_company_name,
            vendor_code: selectedAssignmentData.value.vendor_code,
            legal_name: selectedAssignmentData.value.vendor_legal_name,
            business_type: selectedAssignmentData.value.vendor_business_type
          },
          
          // Response statistics for quick overview
          response_statistics: selectedAssignmentData.value.response_statistics || {},
          
          // Complete questions and responses for detailed review
          questions_and_responses: selectedAssignmentData.value.questions_and_responses || [],
          
          // Assignment metadata
          assignment_metadata: {
            assigned_date: selectedAssignmentData.value.assigned_date,
            due_date: selectedAssignmentData.value.due_date,
            assigned_by: selectedAssignmentData.value.assigned_by,
            notes: selectedAssignmentData.value.notes
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
            review_instructions: `Please review all ${selectedAssignmentData.value.response_statistics?.total_questions || 0} questions and their corresponding vendor responses. Pay special attention to required questions and ensure all responses meet organizational standards and compliance requirements.`
          }
        }
      } else if (approvalType.value === 'final_vendor_approval') {
        return {
          final_approval_type: finalApprovalType.value,
          vendor_id: selectedVendor.value,
          vendor_data: selectedVendorData.value,
          vendor_risks: vendorRisks.value, // For backward compatibility
          internal_risks: internalRisks.value,
          external_risks: externalRisks.value,
          screening_risks: externalRisks.value, // Alternative name for frontend compatibility
          risk_summary: riskSummary.value,
          vendor_info: vendorInfo.value,
          decision_criteria: decisionCriteria.value,
          business_impact: businessImpact.value,
          approval_type: 'final_vendor_approval'
        }
      } else {
        // Default empty object when no approval type is selected
        return {}
      }
    }


    return {
      workflowForm,
      requestForm,
      workflowRules,
      requestRules,
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
      formatJSON,
      validateJSON,
      loadSamplePayload,
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
      getRiskPriorityColor,
      getRiskStatusColor,
      getScreeningTypeColor,
      getResolutionStatusColor,
      getMatchDescription,
      formatMatchDetails,
      getSearchTerms,
      fetchQuestionnaireAssignments,
      handleQuestionnaireAssignmentChange,
      getAssignmentDisplayName,
      formatQuestionType
    }
  }
}
</script>
