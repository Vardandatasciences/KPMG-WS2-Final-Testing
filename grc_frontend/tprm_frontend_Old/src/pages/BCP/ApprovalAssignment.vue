<template>
  <div class="approval-assignment-page p-6 max-w-7xl mx-auto space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-3xl font-bold text-foreground">Approval Assignment</h1>
        <p class="text-muted-foreground">Manage BCP/DRP approval workflows and assignments</p>
      </div>
      <div class="flex gap-3">
        <span class="badge badge--outline text-sm">Workflow Management</span>
        <button 
          @click="toggleFormView" 
          class="btn btn--primary"
          v-if="!showCreateForm"
        >
          <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
          </svg>
          Assign Approval
        </button>
      </div>
    </div>

    <!-- APPROVAL ASSIGNMENTS TABLE -->
    <div v-if="!showCreateForm" class="space-y-6">
      <!-- Filters -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Filters</h3>
        </div>
        <div class="card-content">
          <div class="form-grid-3">
            <div class="space-y-2">
              <label class="block text-sm font-medium">Search</label>
              <input 
                v-model="filters.search" 
                type="text" 
                class="input" 
                placeholder="Search by workflow name, assigner, or assignee"
                @input="fetchApprovals"
              />
            </div>
            <div class="space-y-2">
              <label class="block text-sm font-medium">Status</label>
              <select v-model="filters.status" class="input" @change="fetchApprovals">
                <option value="">All Statuses</option>
                <option value="ASSIGNED">Assigned</option>
                <option value="IN_PROGRESS">In Progress</option>
                <option value="COMMENTED">Commented</option>
                <option value="SKIPPED">Skipped</option>
                <option value="EXPIRED">Expired</option>
                <option value="CANCELLED">Cancelled</option>
              </select>
            </div>
            <div class="space-y-2">
              <label class="block text-sm font-medium">Plan Type</label>
              <select v-model="filters.plan_type" class="input" @change="fetchApprovals">
                <option value="">All Plan Types</option>
                <option value="BCP">Business Continuity Plan</option>
                <option value="DRP">Disaster Recovery Plan</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      <!-- Approvals Table -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Approval Assignments</h3>
          <div class="text-sm text-muted-foreground">
            {{ isLoadingApprovals ? 'Loading...' : `${approvals.length} assignments found` }}
          </div>
        </div>
        <div class="card-content p-0">
          <div v-if="isLoadingApprovals" class="p-6 text-center">
            <div class="loading-spinner animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
            <p class="mt-2 text-muted-foreground">Loading approvals...</p>
          </div>
          <div v-else-if="approvals.length === 0" class="p-6 text-center">
            <p class="text-muted-foreground">No approval assignments found.</p>
            <button @click="toggleFormView" class="btn btn--primary mt-4">
              Create First Assignment
            </button>
          </div>
          <div v-else class="overflow-x-auto">
            <table class="approval-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Workflow Name</th>
                  <th>Plan Type</th>
                  <th>Object Type</th>
                  <th>Object ID</th>
                  <th>Assigner</th>
                  <th>Assignee</th>
                  <th>Status</th>
                  <th>Assigned Date</th>
                  <th>Due Date</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="approval in approvals" :key="approval.approval_id">
                  <td>{{ approval.approval_id }}</td>
                  <td class="font-medium">{{ approval.workflow_name }}</td>
                  <td>{{ approval.plan_type }}</td>
                  <td>{{ approval.object_type }}</td>
                  <td>{{ approval.object_id }}</td>
                  <td>{{ approval.assigner_name }}</td>
                  <td>{{ approval.assignee_name }}</td>
                  <td>{{ formatStatus(approval.status) }}</td>
                  <td>{{ formatDate(approval.assigned_date) }}</td>
                  <td>{{ formatDate(approval.due_date) }}</td>
                  <td>
                    <div class="flex gap-2">
                      <button 
                        @click="viewApprovalDetails(approval)" 
                        class="btn btn--outline btn--sm" 
                        title="View Details"
                      >
                        <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                        </svg>
                      </button>
                      <button class="btn btn--outline btn--sm" title="Edit">
                        <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                        </svg>
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- CREATE ASSIGNMENT FORM -->
    <div v-if="showCreateForm" class="space-y-6">
        <div class="card">
          <div class="card-header">
            <div class="flex items-center justify-between">
              <h3 class="card-title flex items-center gap-2">
                <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
                </svg>
                Create New Approval Assignment
              </h3>
              <button @click="toggleFormView" class="btn btn--outline">
                <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"/>
                </svg>
                Back to List
              </button>
            </div>
          </div>
          <div class="card-content space-y-6">
            <form @submit.prevent="createAssignment" class="space-y-6">
              <!-- Row 1: Plan Type, Object ID, Object Type -->
              <div class="form-grid-3">
                <div class="space-y-2">
                  <label for="planType" class="block text-sm font-medium">Plan Type <span class="text-destructive">*</span></label>
                  <select v-model="form.plan_type" id="planType" class="input" required>
                    <option value="">Select plan type</option>
                    <option value="BCP">Business Continuity Plan</option>
                    <option value="DRP">Disaster Recovery Plan</option>
                  </select>
                </div>
                <div class="space-y-2">
                  <label for="objectId" class="block text-sm font-medium">Object ID <span class="text-destructive">*</span></label>
                  <input 
                    v-model="form.object_id" 
                    type="number" 
                    id="objectId" 
                    class="input" 
                    required 
                    placeholder="Enter object ID"
                  />
                </div>
                <div class="space-y-2">
                  <label for="objectType" class="block text-sm font-medium">Object Type <span class="text-destructive">*</span></label>
                  <select v-model="form.object_type" id="objectType" class="input" required>
                    <option value="">Select object type</option>
                    <option value="PLAN">Plan</option>
                    <option value="QUESTIONNAIRE">Questionnaire</option>
                    <option value="ASSIGNMENT_RESPONSE">Assignment Response</option>
                  </select>
                </div>
              </div>

              <!-- Row 2: Workflow Name, Assigner, Assigner Name -->
              <div class="form-grid-3">
                <div class="space-y-2">
                  <label for="workflowName" class="block text-sm font-medium">Workflow Name <span class="text-destructive">*</span></label>
                  <input 
                    v-model="form.workflow_name" 
                    type="text" 
                    id="workflowName" 
                    class="input" 
                    required 
                    placeholder="Enter workflow name"
                  />
                </div>
                <div class="space-y-2">
                  <label for="assignerId" class="block text-sm font-medium">Assigner <span class="text-destructive">*</span></label>
                  <select v-model="form.assigner_id" id="assignerId" class="input" required @change="onAssignerChange" :disabled="isLoadingUsers">
                    <option value="">{{ isLoadingUsers ? 'Loading users...' : 'Select assigner' }}</option>
                    <option v-for="user in users" :key="user.user_id" :value="user.user_id">
                      {{ user.display_name }}
                    </option>
                  </select>
                </div>
                <div class="space-y-2">
                  <label for="assignerName" class="block text-sm font-medium">Assigner Name</label>
                  <input 
                    v-model="form.assigner_name" 
                    type="text" 
                    id="assignerName" 
                    class="input" 
                    readonly
                    placeholder="Auto-filled from selection"
                  />
                </div>
              </div>

              <!-- Row 3: Assignee Name, Assignee ID, Due Date -->
              <div class="form-grid-3">
                <div class="space-y-2">
                  <label for="assigneeName" class="block text-sm font-medium">Assignee Name</label>
                  <input 
                    v-model="form.assignee_name" 
                    type="text" 
                    id="assigneeName" 
                    class="input" 
                    readonly
                    placeholder="Auto-filled from selection"
                  />
                </div>
                <div class="space-y-2">
                  <label for="assigneeId" class="block text-sm font-medium">Assignee <span class="text-destructive">*</span></label>
                  <select v-model="form.assignee_id" id="assigneeId" class="input" required @change="onAssigneeChange" :disabled="isLoadingUsers">
                    <option value="">{{ isLoadingUsers ? 'Loading users...' : 'Select assignee' }}</option>
                    <option v-for="user in users" :key="user.user_id" :value="user.user_id">
                      {{ user.display_name }}
                    </option>
                  </select>
                </div>
                <div class="space-y-2">
                  <label for="dueDate" class="block text-sm font-medium">Due Date <span class="text-destructive">*</span></label>
                  <input 
                    v-model="form.due_date" 
                    type="datetime-local" 
                    id="dueDate" 
                    class="input" 
                    required
                  />
                </div>
              </div>

              <!-- Action Buttons -->
              <div class="flex gap-4 pt-4">
                <button type="button" @click="resetForm" class="btn btn--outline">
                  <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
                  </svg>
                  Reset Form
                </button>
                <button type="submit" class="btn btn--primary" :disabled="isSubmitting">
                  <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
                  </svg>
                  {{ isSubmitting ? 'Creating...' : 'Create Assignment' }}
                </button>
              </div>
            </form>
          </div>
        </div>
    </div>

    <!-- APPROVAL DETAILS MODAL -->
    <div v-if="showDetailsModal" class="modal-overlay" @click="closeDetailsModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3 class="modal-title">Approval Details</h3>
          <button @click="closeDetailsModal" class="modal-close-btn">
            <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
        
        <div class="modal-body">
          <div v-if="isLoadingDetails" class="loading-container">
            <div class="loading-spinner animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
            <p class="mt-2 text-muted-foreground">Loading approval details...</p>
          </div>
          
          <div v-else-if="approvalDetails">
            <!-- Basic Information -->
            <div class="details-section">
              <h4 class="section-title">Basic Information</h4>
              <div class="details-grid">
                <div class="detail-item">
                  <label>Workflow Name:</label>
                  <span>{{ approvalDetails.workflow_name }}</span>
                </div>
                <div class="detail-item">
                  <label>Plan Type:</label>
                  <span>{{ approvalDetails.plan_type }}</span>
                </div>
                <div class="detail-item">
                  <label>Object Type:</label>
                  <span>{{ approvalDetails.object_type }}</span>
                </div>
                <div class="detail-item">
                  <label>Object ID:</label>
                  <span>{{ approvalDetails.object_id }}</span>
                </div>
                <div class="detail-item">
                  <label>Status:</label>
                  <span>{{ formatStatus(approvalDetails.status) }}</span>
                </div>
                <div class="detail-item">
                  <label>Assigned Date:</label>
                  <span>{{ formatDate(approvalDetails.assigned_date) }}</span>
                </div>
                <div class="detail-item">
                  <label>Due Date:</label>
                  <span>{{ formatDate(approvalDetails.due_date) }}</span>
                </div>
              </div>
            </div>

            <!-- Plan Evaluations (for PLAN object type) -->
            <div v-if="approvalDetails.object_type === 'PLAN'" class="details-section">
              <h4 class="section-title">Plan Information</h4>
              
              <!-- Show plan basic info if available -->
              <div v-if="planInfo" class="plan-info">
                <div class="detail-item">
                  <label>Plan Name:</label>
                  <span>{{ planInfo.plan_name }}</span>
                </div>
                <div class="detail-item">
                  <label>Plan Type:</label>
                  <span>{{ planInfo.plan_type }}</span>
                </div>
                <div class="detail-item">
                  <label>Strategy:</label>
                  <span>{{ planInfo.strategy_name }}</span>
                </div>
                <div class="detail-item">
                  <label>Vendor ID:</label>
                  <span>{{ planInfo.vendor_id }}</span>
                </div>
                <div class="detail-item">
                  <label>Status:</label>
                  <span>{{ formatStatus(planInfo.status) }}</span>
                </div>
                <div class="detail-item">
                  <label>Criticality:</label>
                  <span>{{ planInfo.criticality || 'N/A' }}</span>
                </div>
                <div class="detail-item">
                  <label>Submitted Date:</label>
                  <span>{{ formatDate(planInfo.submitted_at) }}</span>
                </div>
              </div>
              
              <!-- Show evaluations if available -->
              <div v-if="planEvaluations.length > 0" class="evaluations-section">
                <h5>Plan Evaluations ({{ planEvaluations.length }})</h5>
                <div v-for="evaluation in planEvaluations" :key="evaluation.evaluation_id" class="evaluation-card">
                  <div class="evaluation-header">
                    <h6>Evaluation #{{ evaluation.evaluation_id }}</h6>
                    <span>{{ formatStatus(evaluation.status) }}</span>
                  </div>
                  <div class="evaluation-scores">
                    <div class="score-item">
                      <label>Overall Score:</label>
                      <span class="score-value">{{ evaluation.overall_score || 'N/A' }}</span>
                    </div>
                    <div class="score-item">
                      <label>Quality Score:</label>
                      <span class="score-value">{{ evaluation.quality_score || 'N/A' }}</span>
                    </div>
                    <div class="score-item">
                      <label>Coverage Score:</label>
                      <span class="score-value">{{ evaluation.coverage_score || 'N/A' }}</span>
                    </div>
                    <div class="score-item">
                      <label>Recovery Capability Score:</label>
                      <span class="score-value">{{ evaluation.recovery_capability_score || (planInfo?.plan_type === 'BCP' ? 'Not Applicable' : 'N/A') }}</span>
                    </div>
                    <div class="score-item">
                      <label>Compliance Score:</label>
                      <span class="score-value">{{ evaluation.compliance_score || 'N/A' }}</span>
                    </div>
                  </div>
                  <div v-if="evaluation.evaluator_comments" class="evaluation-comments">
                    <label>Evaluator Comments:</label>
                    <p class="comments-text">{{ evaluation.evaluator_comments }}</p>
                  </div>
                </div>
              </div>
              
              <!-- Show message if no evaluations -->
              <div v-else class="no-evaluations">
                <p class="text-muted-foreground">No evaluations found for this plan.</p>
              </div>
            </div>

            <!-- Questionnaire Details (for QUESTIONNAIRE object type) -->
            <div v-if="approvalDetails.object_type === 'QUESTIONNAIRE' && questionnaireDetails" class="details-section">
              <h4 class="section-title">Questionnaire Details</h4>
              
              <div class="questionnaire-info">
                <div class="detail-item">
                  <label>Questionnaire ID:</label>
                  <span>{{ questionnaireDetails.questionnaire_id || 'N/A' }}</span>
                </div>
                <div class="detail-item">
                  <label>Title:</label>
                  <span>{{ questionnaireDetails.title || questionnaireDetails.name || 'N/A' }}</span>
                </div>
                <div class="detail-item">
                  <label>Description:</label>
                  <span>{{ questionnaireDetails.description || 'N/A' }}</span>
                </div>
                <div class="detail-item">
                  <label>Status:</label>
                  <span>{{ formatStatus(questionnaireDetails.status) }}</span>
                </div>
                <div class="detail-item">
                  <label>Total Questions:</label>
                  <span>{{ questionnaireDetails.questions ? questionnaireDetails.questions.length : 0 }} questions</span>
                </div>
                <div v-if="questionnaireDetails.reviewer_comment" class="detail-item">
                  <label>Reviewer Comment:</label>
                  <div class="comment-content">
                    {{ questionnaireDetails.reviewer_comment }}
                  </div>
                </div>
              </div>
              
              <div v-if="questionnaireDetails.questions && questionnaireDetails.questions.length > 0" class="questions-section">
                <h5>Questions ({{ questionnaireDetails.questions.length }})</h5>
                <div class="questions-list">
                  <div v-for="(question, index) in questionnaireDetails.questions" :key="question.id || index" class="question-card">
                    <div class="question-header">
                      <h6>Question {{ question.id || (index + 1) }}</h6>
                      <div class="question-badges">
                        <span v-if="question.required">Required</span>
                        <span v-if="question.allow_document_upload">Document Upload</span>
                      </div>
                    </div>
                    <div class="question-content">
                      <div class="question-text">
                        <label>Question:</label>
                        <p>{{ question.text || question.question_text || 'No question text available' }}</p>
                      </div>
                      <div v-if="question.choice_options && question.choice_options.length > 0" class="choice-options">
                        <label>Answer Options:</label>
                        <div class="options-grid">
                          <div v-for="(option, optIndex) in question.choice_options" :key="optIndex" class="option-item">
                            <span class="option-number">{{ optIndex + 1 }}.</span>
                            <span class="option-text">{{ option }}</span>
                          </div>
                        </div>
                      </div>
                      <div v-if="question.type" class="question-type">
                        <label>Type:</label>
                        <span>{{ question.type }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              <div v-if="questionnaireResponses.length > 0" class="responses-section">
                <h5>Responses & Comments</h5>
                <div v-for="response in questionnaireResponses" :key="response.response_id" class="response-card">
                  <div class="response-header">
                    <h6>Response #{{ response.response_id }}</h6>
                    <span>{{ formatStatus(response.status) }}</span>
                  </div>
                  <div v-if="response.comments" class="response-comments">
                    <label>Comments:</label>
                    <p class="comments-text">{{ response.comments }}</p>
                  </div>
                  <div v-if="response.review_answers" class="review-answers">
                    <label>Review Answers:</label>
                    <div class="answers-list">
                      <div v-for="(answer, questionId) in response.review_answers" :key="questionId" class="answer-item">
                        <strong>Q{{ questionId }}:</strong> {{ answer }}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
            </div>

            <!-- Assignment Response Details (for ASSIGNMENT_RESPONSE object type) -->
            <div v-if="approvalDetails.object_type === 'ASSIGNMENT_RESPONSE' && assignmentResponseDetails" class="details-section">
              <h4 class="section-title">Assignment Response Details</h4>
              <div class="assignment-info">
                <div class="detail-item">
                  <label>Assignment Response ID:</label>
                  <span>{{ assignmentResponseDetails.assignment_response_id }}</span>
                </div>
                <div class="detail-item">
                  <label>Plan ID:</label>
                  <span>{{ assignmentResponseDetails.plan_id }}</span>
                </div>
                <div class="detail-item">
                  <label>Questionnaire ID:</label>
                  <span>{{ assignmentResponseDetails.questionnaire_id }}</span>
                </div>
                <div class="detail-item">
                  <label>Status:</label>
                  <span>{{ formatStatus(assignmentResponseDetails.status) }}</span>
                </div>
                <div class="detail-item">
                  <label>Assigned Date:</label>
                  <span>{{ formatDate(assignmentResponseDetails.assigned_at) }}</span>
                </div>
                <div class="detail-item">
                  <label>Due Date:</label>
                  <span>{{ formatDate(assignmentResponseDetails.due_date) }}</span>
                </div>
                <div class="detail-item">
                  <label>Total Questions:</label>
                  <span>{{ assignmentResponseDetails.total_questions || 'N/A' }}</span>
                </div>
              </div>
              
              <!-- Question Responses Section -->
              <div v-if="assignmentResponseDetails.questions_data && Object.keys(assignmentResponseDetails.questions_data).length > 0" class="responses-section">
                <h5>Question Responses ({{ Object.keys(assignmentResponseDetails.questions_data).length }})</h5>
                <div class="responses-list">
                  <div v-for="(response, questionId) in assignmentResponseDetails.questions_data" :key="questionId" class="response-card">
                    <div class="response-header">
                      <h6>Question {{ questionId }}</h6>
                      <span>{{ getResponseStatus(response) }}</span>
                    </div>
                    <div class="response-content">
                      <!-- Handle structured response data -->
                      <div v-if="isStructuredResponse(response)" class="structured-response">
                        <div class="response-field">
                          <label>Question Text:</label>
                          <div class="field-value">{{ response.question_text || response.question || 'N/A' }}</div>
                        </div>
                        <div class="response-field">
                          <label>Answer:</label>
                          <div class="field-value">{{ response.answer || response.vendor_response || 'No answer provided' }}</div>
                        </div>
                        <div v-if="response.options && response.options.length > 0" class="response-field">
                          <label>Available Options:</label>
                          <div class="options-list">
                            <div v-for="(option, index) in response.options" :key="index" class="option-item">
                              {{ index + 1 }}. {{ option }}
                            </div>
                          </div>
                        </div>
                        <div v-if="response.vendor_comment" class="response-field">
                          <label>Vendor Comment:</label>
                          <div class="field-value">{{ response.vendor_comment }}</div>
                        </div>
                        <div v-if="response.reviewer_comment" class="response-field">
                          <label>Reviewer Comment:</label>
                          <div class="field-value">{{ response.reviewer_comment }}</div>
                        </div>
                        <div v-if="response.is_completed !== undefined" class="response-field">
                          <label>Completed:</label>
                          <div class="field-value">
                            <span>{{ response.is_completed ? 'Yes' : 'No' }}</span>
                          </div>
                        </div>
                        <div v-if="response.score !== undefined" class="response-field">
                          <label>Score:</label>
                          <div class="field-value">{{ response.score }}</div>
                        </div>
                        <div v-if="response.file_uploads && response.file_uploads.length > 0" class="response-field">
                          <label>File Uploads:</label>
                          <div class="documents-list">
                            <div v-for="(file, index) in response.file_uploads" :key="index" class="document-item">
                              {{ file }}
                            </div>
                          </div>
                        </div>
                        <div v-if="response.evidence_documents && response.evidence_documents.length > 0" class="response-field">
                          <label>Evidence Documents:</label>
                          <div class="documents-list">
                            <div v-for="(doc, index) in response.evidence_documents" :key="index" class="document-item">
                              {{ doc }}
                            </div>
                          </div>
                        </div>
                        <div v-if="response.answered_at" class="response-field">
                          <label>Answered At:</label>
                          <div class="field-value">{{ formatDate(response.answered_at) }}</div>
                        </div>
                      </div>
                      <!-- Handle simple string responses -->
                      <div v-else-if="typeof response === 'string'" class="simple-response">
                        <label>Response:</label>
                        <div class="response-text">
                          {{ response || 'No response provided' }}
                        </div>
                      </div>
                      <!-- Handle other object structures -->
                      <div v-else class="raw-response">
                        <label>Raw Response Data:</label>
                        <div class="response-text">
                          <pre>{{ JSON.stringify(response, null, 2) }}</pre>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- Comments Section -->
              <div v-if="assignmentResponseDetails.owner_comment || assignmentResponseDetails.reason_comment" class="comments-section">
                <h5>Comments</h5>
                <div class="comments-list">
                  <div v-if="assignmentResponseDetails.owner_comment" class="comment-card">
                    <div class="comment-header">
                      <h6>Owner Comments</h6>
                      <span>Owner</span>
                    </div>
                    <div class="comment-content">
                      {{ assignmentResponseDetails.owner_comment }}
                    </div>
                  </div>
                  
                  <div v-if="assignmentResponseDetails.reason_comment" class="comment-card">
                    <div class="comment-header">
                      <h6>Reason Comments</h6>
                      <span>Reason</span>
                    </div>
                    <div class="comment-content">
                      {{ assignmentResponseDetails.reason_comment }}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- No details available message -->
            <div v-if="!hasDetailsData" class="no-details">
              <p class="text-muted-foreground">No detailed information available for this approval.</p>
            </div>
          </div>
        </div>
        
        <div class="modal-footer">
          <div class="footer-actions">
            <button @click="closeDetailsModal" class="btn btn--outline">
              Close
            </button>
            <div class="action-buttons">
              <button 
                @click="rejectApproval" 
                class="btn btn--danger"
                :disabled="isProcessingAction"
                :class="{ 'btn--loading': isProcessingAction && actionType === 'reject' }"
              >
                <span v-if="isProcessingAction && actionType === 'reject'" class="btn__spinner"></span>
                <span v-else>Reject</span>
              </button>
              <button 
                @click="approveApproval" 
                class="btn btn--success"
                :disabled="isProcessingAction"
                :class="{ 'btn--loading': isProcessingAction && actionType === 'approve' }"
              >
                <span v-if="isProcessingAction && actionType === 'approve'" class="btn__spinner"></span>
                <span v-else>Approve</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import './ApprovalAssignment.css'
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import api from '../../services/api_bcp.js'
import { useNotifications } from '@/composables/useNotifications'
import { PopupService } from '@/popup/popupService'
import notificationService from '@/services/notificationService'
import loggingService from '@/services/loggingService'

const route = useRoute()

// Reactive data
const { showSuccess, showError, showWarning, showInfo } = useNotifications()

const isSubmitting = ref(false)
const users = ref([])
const isLoadingUsers = ref(false)
const approvals = ref([])
const isLoadingApprovals = ref(false)
const showCreateForm = ref(false)

// Modal data
const showDetailsModal = ref(false)
const isLoadingDetails = ref(false)
const approvalDetails = ref(null)
const planEvaluations = ref([])
const planInfo = ref(null)
const questionnaireDetails = ref(null)
const questionnaireResponses = ref([])
const assignmentResponseDetails = ref(null)
const isProcessingAction = ref(false)
const actionType = ref('')

// Filters
const filters = ref({
  search: '',
  status: '',
  plan_type: '',
  object_type: '',
  assignee: ''
})

// Form data
const form = ref({
  workflow_name: '',
  plan_type: '',
  assigner_id: '',
  assigner_name: '', // This will contain the username
  assignee_id: '',
  assignee_name: '', // This will contain the username
  object_type: '',
  object_id: '',
  due_date: ''
})


// Methods
const fetchUsers = async () => {
  isLoadingUsers.value = true
  try {
    console.log('Fetching users from API endpoint: /api/bcpdrp/users/')
    const response = await api.users.list()
    
    console.log('API response data:', response)
    console.log('Response type:', typeof response)
    console.log('Response keys:', Object.keys(response))
    
    // Check if users are in response.users (unwrapped by interceptor) or response.data?.users
    const usersData = (response as any).users || (response as any).data?.users
    console.log('Users found:', usersData)
    console.log('Users type:', typeof usersData)
    console.log('Users length:', usersData ? usersData.length : 'undefined')
    
    if (usersData && Array.isArray(usersData)) {
      users.value = usersData
      console.log('Successfully fetched users:', usersData.length, 'users')
    } else {
      console.error('API returned no users data or users is not an array')
      console.error('Response structure:', JSON.stringify(response, null, 2))
      users.value = []
    }
  } catch (error) {
    console.error('Error fetching users from API:', error)
    console.error('Error details:', {
      message: error.message,
      status: error.response?.status,
      statusText: error.response?.statusText,
      data: error.response?.data
    })
    users.value = []
    PopupService.error(`Failed to load users: ${error.message}. Please check your connection and try again.`, 'Loading Failed')
  } finally {
    isLoadingUsers.value = false
  }
}

const onAssignerChange = () => {
  const selectedUser = users.value.find(user => user.user_id == form.value.assigner_id)
  if (selectedUser) {
    form.value.assigner_name = selectedUser.username
  } else {
    form.value.assigner_name = ''
  }
}

const onAssigneeChange = () => {
  const selectedUser = users.value.find(user => user.user_id == form.value.assignee_id)
  if (selectedUser) {
    form.value.assignee_name = selectedUser.username
  } else {
    form.value.assignee_name = ''
  }
}

const createAssignment = async () => {
  isSubmitting.value = true
  
  try {
    console.log('Creating assignment:', form.value)
    
    // Call the API to create the approval assignment
    const response = await api.approvals.createAssignment(form.value)
    
    console.log('Assignment created successfully:', response)
    
    // Reset form and go back to list view
    resetForm()
    showCreateForm.value = false
    
    // Refresh the approvals list
    await fetchApprovals()
    
    PopupService.success(`Assignment created successfully! Approval ID: ${(response as any).approval_id}`, 'Assignment Created')
    // Create notification
    await notificationService.createBCPSuccessNotification('approval_assignment_created', {
      title: 'Approval Assignment Created',
      message: `Assignment created successfully! Approval ID: ${(response as any).approval_id}`,
      approval_id: (response as any).approval_id
    })
  } catch (error) {
    console.error('Error creating assignment:', error)
    
    // Handle different types of errors
    let errorMessage = 'Error creating assignment. Please try again.'
    if (error.response?.data?.message) {
      errorMessage = error.response.data.message
    } else if (error.response?.data?.error) {
      errorMessage = error.response.data.error
    } else if (error.message) {
      errorMessage = error.message
    }
    
    PopupService.error(errorMessage, 'Assignment Creation Failed')
    // Create error notification
    await notificationService.createBCPErrorNotification('approval_assignment_create', errorMessage, {
      title: 'Assignment Creation Failed'
    })
  } finally {
    isSubmitting.value = false
  }
}

const resetForm = () => {
  form.value = {
    workflow_name: '',
    plan_type: '',
    assigner_id: '',
    assigner_name: '', // This will contain the username
    assignee_id: '',
    assignee_name: '', // This will contain the username
    object_type: '',
    object_id: '',
    due_date: ''
  }
}

const fetchApprovals = async () => {
  isLoadingApprovals.value = true
  try {
    console.log('Fetching approvals with filters:', filters.value)
    const response = await api.approvals.list(filters.value)
    
    console.log('API response:', response)
    
    // Check if approvals are in response.approvals (unwrapped by interceptor) or response.data?.approvals
    const approvalsData = (response as any).approvals || (response as any).data?.approvals
    console.log('Approvals found:', approvalsData)
    
    if (approvalsData && Array.isArray(approvalsData)) {
      approvals.value = approvalsData
      console.log('Successfully fetched approvals:', approvalsData.length, 'records')
    } else {
      console.error('API returned no approvals data or approvals is not an array')
      console.error('Response structure:', JSON.stringify(response, null, 2))
      approvals.value = []
    }
  } catch (error) {
    console.error('Error fetching approvals:', error)
    console.error('Error details:', {
      message: error.message,
      status: error.response?.status,
      statusText: error.response?.statusText,
      data: error.response?.data
    })
    approvals.value = []
    PopupService.error(`Failed to load approvals: ${error.message}. Please check your connection and try again.`, 'Loading Failed')
  } finally {
    isLoadingApprovals.value = false
  }
}

const toggleFormView = () => {
  showCreateForm.value = !showCreateForm.value
  if (!showCreateForm.value) {
    resetForm()
  }
}

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  try {
    const date = new Date(dateString)
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  } catch (error) {
    return 'Invalid Date'
  }
}

const formatStatus = (status) => {
  const statusMap = {
    'ASSIGNED': 'Assigned',
    'IN_PROGRESS': 'In Progress',
    'COMMENTED': 'Commented',
    'SKIPPED': 'Skipped',
    'EXPIRED': 'Expired',
    'CANCELLED': 'Cancelled'
  }
  return statusMap[status] || status
}

const getStatusClass = (status) => {
  const statusClasses = {
    'ASSIGNED': 'status-assigned',
    'IN_PROGRESS': 'status-in-progress',
    'COMMENTED': 'status-commented',
    'SKIPPED': 'status-skipped',
    'EXPIRED': 'status-expired',
    'CANCELLED': 'status-cancelled'
  }
  return statusClasses[status] || 'status-default'
}

// Modal methods
const viewApprovalDetails = async (approval) => {
  console.log('Viewing approval details:', approval)
  showDetailsModal.value = true
  approvalDetails.value = approval
  isLoadingDetails.value = true
  
  try {
    // Reset all detail data
    planEvaluations.value = []
    questionnaireDetails.value = null
    questionnaireResponses.value = []
    assignmentResponseDetails.value = null
    
    // Fetch details based on object type
    if (approval.object_type === 'PLAN') {
      await fetchPlanEvaluations(approval.object_id)
    } else if (approval.object_type === 'QUESTIONNAIRE') {
      await fetchQuestionnaireDetails(approval.object_id)
    } else if (approval.object_type === 'ASSIGNMENT_RESPONSE') {
      await fetchAssignmentResponseDetails(approval.object_id)
    }
  } catch (error) {
    console.error('Error fetching approval details:', error)
    PopupService.error('Failed to load approval details. Please try again.', 'Loading Failed')
  } finally {
    isLoadingDetails.value = false
  }
}

const fetchPlanEvaluations = async (planId) => {
  try {
    console.log('Fetching plan evaluations for plan ID:', planId)
    const response = await api.plans.getEvaluations(planId)
    console.log('Plan evaluations response:', response)
    console.log('Response type:', typeof response)
    console.log('Response keys:', Object.keys(response || {}))
    
    // Check multiple possible response structures
    let evaluations = []
    
    if (response && (response as any).evaluations) {
      evaluations = (response as any).evaluations
      console.log('Found evaluations in response.evaluations:', evaluations.length)
    } else if (response && (response as any).data && (response as any).data.evaluations) {
      evaluations = (response as any).data.evaluations
      console.log('Found evaluations in response.data.evaluations:', evaluations.length)
    } else if (response && Array.isArray(response)) {
      evaluations = response
      console.log('Found evaluations as array:', evaluations.length)
    } else if (response && (response as any).data && Array.isArray((response as any).data)) {
      evaluations = (response as any).data
      console.log('Found evaluations in response.data array:', evaluations.length)
    } else {
      console.log('No evaluations found in response structure')
      console.log('Full response structure:', JSON.stringify(response, null, 2))
    }
    
    planEvaluations.value = evaluations
    
    // Also extract plan information if available
    if (response && (response as any).plan) {
      planInfo.value = (response as any).plan
      console.log('Found plan info:', planInfo.value)
    } else if (response && (response as any).data && (response as any).data.plan) {
      planInfo.value = (response as any).data.plan
      console.log('Found plan info in data:', planInfo.value)
    } else {
      planInfo.value = null
      console.log('No plan info found in response')
    }
    
    console.log('Final planEvaluations set to:', planEvaluations.value.length, 'items')
    console.log('Final planInfo set to:', planInfo.value ? 'available' : 'null')
  } catch (error) {
    console.error('Error fetching plan evaluations:', error)
    planEvaluations.value = []
  }
}

const fetchQuestionnaireDetails = async (questionnaireId) => {
  try {
    const response = await api.questionnaires.getDetails(questionnaireId)
    
    // Extract questionnaire data from the response
    let questionnaireData = null
    
    // The HTTP interceptor unwraps the response, so we get: { questionnaire: {...}, questions: [...] }
    if (response && (response as any).data) {
      const responseData = (response as any).data
      
      // Extract questionnaire and questions from the data
      if (responseData.questionnaire) {
        questionnaireData = {
          ...responseData.questionnaire,
          questions: responseData.questions || []
        }
      } else {
        questionnaireData = responseData
      }
    } else if (response && (response as any).questionnaire_id) {
      questionnaireData = response
    }
    
    questionnaireDetails.value = questionnaireData
    
    // For questionnaire responses, we need to fetch from assignments
    // This will be handled separately if needed
    questionnaireResponses.value = []
  } catch (error) {
    console.error('Error fetching questionnaire details:', error)
    questionnaireDetails.value = null
    questionnaireResponses.value = []
  }
}

const fetchAssignmentResponseDetails = async (assignmentId) => {
  try {
    console.log('Fetching assignment response details for ID:', assignmentId)
    const response = await api.assignments.getResponseDetails(assignmentId)
    console.log('Assignment response details:', response)
    
    // The response will be a list, so we need to find the specific assignment
    const assignments = (response as any).assignments || (response as any).data?.assignments || []
    const assignment = assignments.find((a: any) => a.assignment_response_id == assignmentId)
    
    if (assignment) {
      // Parse the questions_data if it's a JSON string
      if (assignment.questions_data && typeof assignment.questions_data === 'string') {
        try {
          assignment.questions_data = JSON.parse(assignment.questions_data)
          console.log('Parsed questions_data:', assignment.questions_data)
        } catch (error) {
          console.error('Error parsing questions_data:', error)
        }
      }
      
      // Parse the answer_text if it's a JSON string
      if (assignment.answer_text && typeof assignment.answer_text === 'string') {
        try {
          const parsedAnswerText = JSON.parse(assignment.answer_text)
          assignment.parsed_answer_text = parsedAnswerText
          console.log('Parsed answer_text:', parsedAnswerText)
          
          // If questions_data is not available, try to extract it from answer_text
          if (!assignment.questions_data && parsedAnswerText.questions_data) {
            assignment.questions_data = parsedAnswerText.questions_data
            console.log('Extracted questions_data from answer_text:', assignment.questions_data)
          }
        } catch (error) {
          console.error('Error parsing answer_text:', error)
        }
      }
      
      // Ensure questions_data is properly structured
      if (assignment.questions_data && typeof assignment.questions_data === 'object') {
        // Convert questions_data to a more usable format if needed
        const questionsData = assignment.questions_data
        if (Array.isArray(questionsData)) {
          // Convert array to object with question IDs as keys
          const questionsObj = {}
          questionsData.forEach((q, index) => {
            questionsObj[q.id || index + 1] = q
          })
          assignment.questions_data = questionsObj
        }
      }
      
      assignmentResponseDetails.value = assignment
    } else {
      console.warn('Assignment not found in response')
      assignmentResponseDetails.value = null
    }
  } catch (error) {
    console.error('Error fetching assignment response details:', error)
    assignmentResponseDetails.value = null
  }
}

const closeDetailsModal = () => {
  showDetailsModal.value = false
  approvalDetails.value = null
  planEvaluations.value = []
  planInfo.value = null
  questionnaireDetails.value = null
  questionnaireResponses.value = []
  assignmentResponseDetails.value = null
  isProcessingAction.value = false
  actionType.value = ''
}

// Approve and Reject functionality
const approveApproval = async () => {
  if (!approvalDetails.value) return
  
  isProcessingAction.value = true
  actionType.value = 'approve'
  
  try {
    console.log('Approving approval:', approvalDetails.value.approval_id)
    
    // Call the appropriate API based on object type
    let response
    if (approvalDetails.value.object_type === 'PLAN') {
      response = await api.plans.approve(approvalDetails.value.object_id)
    } else if (approvalDetails.value.object_type === 'QUESTIONNAIRE') {
      response = await api.questionnaires.approve(approvalDetails.value.object_id)
    } else if (approvalDetails.value.object_type === 'ASSIGNMENT_RESPONSE') {
      response = await api.assignments.approve(approvalDetails.value.object_id)
    }
    
    console.log('Approval successful:', response)
    
    // Show success message
    PopupService.success('Approval approved successfully!', 'Approved')
    // Create notification
    await notificationService.createApprovalNotification('approval_submitted', {
      plan_id: approvalDetails.value?.object_id,
      decision: 'APPROVED'
    })
    
    // Close modal and refresh data
    closeDetailsModal()
    await fetchApprovals()
    
  } catch (error) {
    console.error('Error approving:', error)
    PopupService.error('Failed to approve. Please try again.', 'Approval Failed')
    // Create error notification
    await notificationService.createApprovalNotification('approval_failed', {
      plan_id: approvalDetails.value?.object_id,
      error: error.message || 'Unknown error'
    })
  } finally {
    isProcessingAction.value = false
    actionType.value = ''
  }
}

const rejectApproval = async () => {
  if (!approvalDetails.value) return
  
  isProcessingAction.value = true
  actionType.value = 'reject'
  
  try {
    console.log('Rejecting approval:', approvalDetails.value.approval_id)
    
    // Call the appropriate API based on object type
    let response
    if (approvalDetails.value.object_type === 'PLAN') {
      response = await api.plans.reject(approvalDetails.value.object_id)
    } else if (approvalDetails.value.object_type === 'QUESTIONNAIRE') {
      response = await api.questionnaires.reject(approvalDetails.value.object_id)
    } else if (approvalDetails.value.object_type === 'ASSIGNMENT_RESPONSE') {
      response = await api.assignments.reject(approvalDetails.value.object_id)
    }
    
    console.log('Rejection successful:', response)
    
    // Show success message
    PopupService.success('Approval rejected successfully!', 'Rejected')
    // Create notification
    await notificationService.createApprovalNotification('approval_submitted', {
      plan_id: approvalDetails.value?.object_id,
      decision: 'REJECTED'
    })
    
    // Close modal and refresh data
    closeDetailsModal()
    await fetchApprovals()
    
  } catch (error) {
    console.error('Error rejecting:', error)
    PopupService.error('Failed to reject. Please try again.', 'Rejection Failed')
    // Create error notification
    await notificationService.createApprovalNotification('approval_failed', {
      plan_id: approvalDetails.value?.object_id,
      error: error.message || 'Unknown error'
    })
  } finally {
    isProcessingAction.value = false
    actionType.value = ''
  }
}

// Helper methods for parsing assignment response data
const isStructuredResponse = (response) => {
  if (typeof response === 'string') {
    try {
      const parsed = JSON.parse(response)
      return parsed && typeof parsed === 'object' && (
        parsed.question_text || parsed.question || 
        parsed.vendor_response || parsed.answer ||
        parsed.question_type || parsed.type
      )
    } catch {
      return false
    }
  }
  return response && typeof response === 'object' && (
    response.question_text || response.question || 
    response.vendor_response || response.answer ||
    response.question_type || response.type
  )
}

const getResponseStatus = (response) => {
  if (typeof response === 'string') {
    try {
      const parsed = JSON.parse(response)
      return parsed.status || parsed.response_status || 'Unknown'
    } catch {
      return 'Unknown'
    }
  }
  return response.status || response.response_status || 'Unknown'
}

const getResponseStatusClass = (response) => {
  const status = getResponseStatus(response)
  const statusClasses = {
    'PENDING': 'status-pending',
    'COMPLETED': 'status-completed',
    'ANSWERED': 'status-answered',
    'SUBMITTED': 'status-submitted',
    'IN_PROGRESS': 'status-in-progress',
    'ASSIGNED': 'status-assigned',
    'COMMENTED': 'status-commented',
    'SKIPPED': 'status-skipped',
    'EXPIRED': 'status-expired',
    'CANCELLED': 'status-cancelled'
  }
  return statusClasses[status] || 'status-unknown'
}

// Computed property to check if we have any details data
const hasDetailsData = computed(() => {
  const hasPlanData = planEvaluations.value.length > 0 || planInfo.value
  const hasQuestionnaireData = questionnaireDetails.value && (
    questionnaireDetails.value.questions || 
    questionnaireDetails.value.title || 
    questionnaireDetails.value.questionnaire_id ||
    questionnaireDetails.value.description
  )
  const hasAssignmentData = assignmentResponseDetails.value && assignmentResponseDetails.value.assignment_response_id
  
  console.log('hasDetailsData check:', {
    hasPlanData,
    hasQuestionnaireData,
    hasAssignmentData,
    planEvaluations: planEvaluations.value.length,
    planInfo: !!planInfo.value,
    questionnaireDetails: !!questionnaireDetails.value,
    questionnaireKeys: questionnaireDetails.value ? Object.keys(questionnaireDetails.value) : [],
    assignmentResponseDetails: !!assignmentResponseDetails.value
  })
  
  return hasPlanData || hasQuestionnaireData || hasAssignmentData
})


// Initialize form with default due date and fetch users
onMounted(async () => {
  await loggingService.logPageView('BCP', 'Approval Assignment')
  const tomorrow = new Date()
  tomorrow.setDate(tomorrow.getDate() + 1)
  
  form.value.due_date = tomorrow.toISOString().slice(0, 16)
  
  // Check for URL parameters and auto-fill form (if any parameters, show form directly)
  const createNew = Array.isArray(route.query.createNew) ? route.query.createNew[0] : route.query.createNew
  const objectType = Array.isArray(route.query.objectType) ? route.query.objectType[0] : route.query.objectType
  const objectId = Array.isArray(route.query.objectId) ? route.query.objectId[0] : route.query.objectId
  const planId = Array.isArray(route.query.planId) ? route.query.planId[0] : route.query.planId
  const planType = Array.isArray(route.query.planType) ? route.query.planType[0] : route.query.planType
  
  if (createNew === 'true' || planId || objectType || planType) {
    showCreateForm.value = true
    
    // Handle assignment_response object type from TestingLibrary
    if (objectType === 'assignment_response') {
      form.value.object_type = 'ASSIGNMENT_RESPONSE'
      console.log('Auto-filled object_type from URL parameter:', objectType)
    }
    
    // Handle object ID from TestingLibrary or other sources
    if (objectId) {
      form.value.object_id = objectId
      console.log('Auto-filled object_id from URL parameter:', objectId)
    } else if (planId) {
      form.value.object_id = planId
      console.log('Auto-filled object_id from URL parameter:', planId)
    }
    
    if (objectType && objectType !== 'assignment_response') {
      form.value.object_type = objectType
      console.log('Auto-filled object_type from URL parameter:', objectType)
    }
    
    if (planType) {
      form.value.plan_type = planType
      console.log('Auto-filled plan_type from URL parameter:', planType)
    }
    
    // Load additional prefilled data from sessionStorage if available
    const prefilledData = sessionStorage.getItem('prefilledApprovalData')
    if (prefilledData) {
      try {
        const data = JSON.parse(prefilledData)
        console.log('Loading prefilled data from sessionStorage:', data)
        
        // Prefill additional fields if available
        if (data.plan_id && !form.value.object_id) {
          form.value.object_id = data.plan_id
        }
        if (data.questionnaire_id && !form.value.object_id) {
          form.value.object_id = data.questionnaire_id
        }
        
        // Clear the sessionStorage after using it
        sessionStorage.removeItem('prefilledApprovalData')
      } catch (error) {
        console.error('Error parsing prefilled data:', error)
      }
    }
  }
  
  // Fetch users for dropdowns and approvals for table
  await fetchUsers()
  await fetchApprovals()
})
</script>

<style scoped>
/* Scoped styles to ensure proper rendering and override external CSS */
.approval-assignment-page {
  min-height: 100vh !important;
  background-color: hsl(var(--background)) !important;
  color: hsl(var(--foreground)) !important;
}

/* Ensure proper display of all elements */
.approval-assignment-page * {
  box-sizing: border-box !important;
}

/* Loading spinner specific styles */
.loading-spinner {
  border: 2px solid hsl(var(--border)) !important;
  border-top: 2px solid hsl(var(--primary)) !important;
  border-radius: 50% !important;
  width: 2rem !important;
  height: 2rem !important;
  animation: spin 1s linear infinite !important;
}

/* Ensure cards are visible */
.card {
  background-color: hsl(var(--card)) !important;
  border: 1px solid hsl(var(--border)) !important;
  border-radius: 0.5rem !important;
  box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1) !important;
}

/* Ensure table is properly styled */
.approval-table {
  background-color: hsl(var(--card)) !important;
  border-collapse: collapse !important;
  width: 100% !important;
}

.approval-table th {
  background-color: hsl(var(--muted)) !important;
  color: hsl(var(--muted-foreground)) !important;
  font-weight: 500 !important;
  text-align: left !important;
  padding: 0.75rem !important;
  border-bottom: 1px solid hsl(var(--border)) !important;
}

.approval-table td {
  padding: 0.75rem !important;
  border-bottom: 1px solid hsl(var(--border)) !important;
  color: hsl(var(--foreground)) !important;
}

.approval-table tr:hover {
  background-color: hsl(var(--muted) / 0.5) !important;
}

/* Ensure buttons are properly styled */
.btn {
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  border-radius: 0.375rem !important;
  font-size: 0.875rem !important;
  font-weight: 500 !important;
  transition: all 0.2s !important;
  border: 1px solid transparent !important;
  cursor: pointer !important;
  text-decoration: none !important;
}

.btn--primary {
  background-color: hsl(var(--primary)) !important;
  color: hsl(var(--primary-foreground)) !important;
  border-color: hsl(var(--primary)) !important;
}

.btn--primary:hover {
  background-color: hsl(var(--primary) / 0.9) !important;
}

.btn--outline {
  border-color: hsl(var(--border)) !important;
  color: hsl(var(--foreground)) !important;
  background-color: transparent !important;
}

.btn--outline:hover {
  background-color: hsl(var(--muted)) !important;
}

.btn--sm {
  padding: 0.25rem 0.5rem !important;
  font-size: 0.75rem !important;
}

/* Ensure form elements are properly styled */
.input {
  display: flex !important;
  height: 2.5rem !important;
  width: 100% !important;
  border-radius: 0.375rem !important;
  border: 1px solid hsl(var(--border)) !important;
  background-color: hsl(var(--background)) !important;
  color: hsl(var(--foreground)) !important;
  padding: 0.5rem 0.75rem !important;
  font-size: 0.875rem !important;
  transition: border-color 0.2s !important;
}

.input:focus {
  outline: 2px solid transparent !important;
  outline-offset: 2px !important;
  border-color: hsl(var(--ring)) !important;
}

.input:disabled {
  opacity: 0.6 !important;
  cursor: not-allowed !important;
  background-color: hsl(var(--muted)) !important;
}

/* Ensure badges are properly styled */
.badge {
  display: inline-flex !important;
  align-items: center !important;
  border-radius: 9999px !important;
  border: 1px solid transparent !important;
  padding: 0.25rem 0.75rem !important;
  font-size: 0.75rem !important;
  font-weight: 500 !important;
  transition: colors 0.2s !important;
}

.badge--outline {
  border-color: hsl(var(--border)) !important;
  color: hsl(var(--foreground)) !important;
}

.badge--success {
  background-color: hsl(var(--success)) !important;
  color: hsl(var(--success-foreground)) !important;
}

.badge--info {
  background-color: hsl(var(--info)) !important;
  color: hsl(var(--info-foreground)) !important;
}

/* Status badge styles */
.status-badge {
  display: inline-flex !important;
  align-items: center !important;
  padding: 0.25rem 0.5rem !important;
  border-radius: 9999px !important;
  font-size: 0.75rem !important;
  font-weight: 500 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.05em !important;
}

.status-assigned {
  background-color: hsl(var(--blue) / 0.1) !important;
  color: hsl(var(--blue)) !important;
}

.status-in-progress {
  background-color: hsl(var(--yellow) / 0.1) !important;
  color: hsl(var(--yellow)) !important;
}

.status-commented {
  background-color: hsl(var(--purple) / 0.1) !important;
  color: hsl(var(--purple)) !important;
}

.status-skipped {
  background-color: hsl(var(--gray) / 0.1) !important;
  color: hsl(var(--gray)) !important;
}

.status-expired {
  background-color: hsl(var(--red) / 0.1) !important;
  color: hsl(var(--red)) !important;
}

.status-cancelled {
  background-color: hsl(var(--red) / 0.1) !important;
  color: hsl(var(--red)) !important;
}

/* Ensure proper spacing */
.space-y-6 > * + * {
  margin-top: 1.5rem !important;
}

.gap-3 {
  gap: 0.75rem !important;
}

.gap-2 {
  gap: 0.5rem !important;
}

.mt-2 {
  margin-top: 0.5rem !important;
}

.mt-4 {
  margin-top: 1rem !important;
}

.mr-2 {
  margin-right: 0.5rem !important;
}

/* Ensure proper text colors */
.text-foreground {
  color: hsl(var(--foreground)) !important;
}

.text-muted-foreground {
  color: hsl(var(--muted-foreground)) !important;
}

.text-destructive {
  color: hsl(var(--destructive)) !important;
}

/* Ensure proper display */
.flex {
  display: flex !important;
}

.items-center {
  align-items: center !important;
}

.justify-between {
  justify-content: space-between !important;
}

.text-center {
  text-align: center !important;
}

/* Ensure proper sizing */
.text-3xl {
  font-size: 1.875rem !important;
  line-height: 2.25rem !important;
}

.text-sm {
  font-size: 0.875rem !important;
  line-height: 1.25rem !important;
}

.font-bold {
  font-weight: 700 !important;
}

.font-medium {
  font-weight: 500 !important;
}

/* Ensure proper layout */
.max-w-7xl {
  max-width: 80rem !important;
}

.mx-auto {
  margin-left: auto !important;
  margin-right: auto !important;
}

.p-6 {
  padding: 1.5rem !important;
}

.p-0 {
  padding: 0 !important;
}

/* Grid layout */
.form-grid-3 {
  display: grid !important;
  grid-template-columns: repeat(3, 1fr) !important;
  gap: 1rem !important;
}

@media (max-width: 768px) {
  .form-grid-3 {
    grid-template-columns: 1fr !important;
  }
}

/* Ensure overflow handling */
.overflow-x-auto {
  overflow-x: auto !important;
}

/* Animation keyframes */
@keyframes spin {
  from {
    transform: rotate(0deg) !important;
  }
  to {
    transform: rotate(360deg) !important;
  }
}
</style>
