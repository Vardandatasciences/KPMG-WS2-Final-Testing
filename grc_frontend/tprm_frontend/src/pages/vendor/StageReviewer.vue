<template>
  <div class="stage-reviewer">
    <div class="page-header">
      <h1>Review & Decision</h1>
      <p class="page-subtitle">Review and make decisions on assigned approval stages</p>
    </div>

    <!-- Main Content -->
    <div v-if="currentStage" class="content-wrapper">
      
      <!-- Stage Details -->
      <section class="section">
        <h2 class="section-title">Stage Details</h2>
        
        <div class="stage-info">
          <div class="stage-title-row">
            <div class="stage-heading">
              <div class="stage-labels">
                <span class="stage-chip">Stage {{ Number(currentStage.stage_order) + 1 }}</span>
                <span class="stage-chip subtle">{{ formatWorkflowType(currentStage.workflow_type) }}</span>
              </div>
              <h3 class="stage-name">{{ currentStage.stage_name }}</h3>
              <p class="stage-request">{{ currentStage.request_title }}</p>
            </div>
            <span class="status-badge" :class="getStatusType(currentStage.stage_status)">
              {{ currentStage.stage_status }}
            </span>
          </div>

          <div v-if="currentStage.stage_description" class="stage-description-block">
            <span class="meta-label">Stage Summary</span>
            <p class="stage-description">{{ currentStage.stage_description }}</p>
          </div>

          <div class="stage-meta-grid simple-grid">
            <div class="meta-item">
              <span class="meta-label">Deadline</span>
              <span class="meta-value">{{ formatDate(currentStage.deadline_date) }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">Priority</span>
              <span class="meta-value">{{ formatValue(currentStage.priority) }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">Department</span>
              <span class="meta-value">{{ formatValue(currentStage.department) }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">Created</span>
              <span class="meta-value">{{ formatDate(currentStage.created_at) }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">Workflow Type</span>
              <span class="meta-value">{{ formatWorkflowType(currentStage.workflow_type) }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- Request Details -->
      <section class="section">
        <h2 class="section-title">Request Details</h2>
        <div class="info-grid">
          <div v-for="f in deriveFields(currentStage)" :key="f.key" class="info-item">
            <span class="info-label">{{ f.label }}</span>
            <span class="info-value">{{ f.value }}</span>
          </div>
        </div>
      </section>

      <!-- Response Approval - Questions and Responses with Scoring -->
      <section v-if="isResponseApproval(currentStage)" class="section">
        <div class="section-header-row">
          <h2 class="section-title">Questionnaire Review & Scoring</h2>
          <div v-if="totalScore !== null" class="total-score">
            <span class="score-label">Total Score:</span>
            <span class="score-value" :class="getScoreClass(totalScore)">{{ totalScore.toFixed(1) }}%</span>
          </div>
        </div>
        
        <div v-if="questionsAndResponses.length > 0" class="questions-list">
          <div v-for="(qr, index) in questionsAndResponses" :key="qr.question_id" class="question-item">
            <div class="question-response-header">
              <div class="question-info">
                <span class="q-number">Q{{ qr.display_order }}</span>
                <span class="q-text">{{ qr.question_text }}</span>
                <span class="q-weight">Weight: {{ qr.scoring_weight }}</span>
              </div>
              <div class="question-badges">
                <span class="badge badge-type">{{ qr.question_type }}</span>
                <span v-if="qr.is_required" class="badge badge-required">Required</span>
                <span v-if="qr.is_completed" class="badge badge-completed">Completed</span>
              </div>
            </div>
            
            <div class="question-response-content">
              <div class="vendor-response-section">
                <h5>Vendor Response</h5>
                <div v-if="qr.vendor_response" class="response-text">
                  {{ qr.vendor_response }}
                </div>
                <div v-else class="no-response">
                  <div class="alert alert-warning">
                    <span class="alert-icon">⚠️</span>
                    <div class="alert-content">
                      <div class="alert-title">No response provided</div>
                    </div>
                  </div>
                </div>
                
                <div v-if="qr.vendor_comment" class="vendor-comment">
                  <strong>Vendor Comment:</strong>
                  <p>{{ qr.vendor_comment }}</p>
                </div>
                
                <div v-if="qr.file_uploads && qr.file_uploads.length > 0" class="file-uploads">
                  <strong>File Uploads:</strong>
                  <div class="file-list">
                    <div v-for="file in qr.file_uploads" :key="file.s3_file_id || file.name" class="file-item">
                      <div class="file-info">
                        <svg class="file-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                        </svg>
                        <div class="file-details">
                          <div class="file-name">{{ file.original_name || file.name }}</div>
                          <div v-if="file.file_size || file.size" class="file-size">{{ formatFileSize(file.file_size || file.size) }}</div>
                        </div>
                      </div>
                      <div class="file-actions">
                        <a 
                          v-if="file.s3_url" 
                          :href="file.s3_url" 
                          target="_blank" 
                          class="file-download-btn"
                          title="Open file"
                        >
                          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/>
                          </svg>
                          Open
                        </a>
                        <span v-else class="file-unavailable">File not accessible</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              <div class="scoring-section">
                <h5>Reviewer Scoring</h5>
                <div class="score-input-group">
                  <div class="form-item">
                    <label>Score</label>
                    <div class="score-input-container">
                      <input
                        v-model="qr.reviewer_score"
                        type="number"
                        :min="0"
                        :max="getMaxScore(qr.scoring_weight)"
                        step="0.1"
                        @change="updateScore(qr.question_id, qr.reviewer_score)"
                        placeholder="0.0"
                        class="form-input score-input"
                      />
                      <span class="max-score-label">/ {{ getMaxScore(qr.scoring_weight) }}</span>
                    </div>
                  </div>
                  
                  <div class="form-item">
                    <label>Reviewer Comment</label>
                    <textarea
                      v-model="qr.reviewer_comment_draft"
                      :rows="2"
                      placeholder="Add your review comments..."
                      class="form-textarea"
                      @change="updateReviewerComment(qr.question_id, qr.reviewer_comment_draft)"
                    />
                  </div>
                </div>
                
                <div v-if="qr.reviewer_comment" class="existing-comment">
                  <strong>Previous Review:</strong>
                  <p>{{ qr.reviewer_comment }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div v-else class="empty-message">
          <p>No questionnaire responses found</p>
        </div>
        
        <!-- Save Scores Button -->
        <div class="action-buttons">
          <button class="btn btn-primary" @click="saveReviewerScores" :disabled="savingScores">
            {{ savingScores ? 'Saving...' : 'Save Scores' }}
          </button>
          <button class="btn btn-secondary" @click="calculateTotalScore">
            Recalculate Total
          </button>
        </div>
      </section>

      <!-- Regular Questionnaire Questions (for other approval types) -->
      <section v-else-if="questionsMap[currentStage.stage_id] && questionsMap[currentStage.stage_id].length" class="section">
        <h2 class="section-title">Questionnaire Questions</h2>
        <div class="questions-list">
          <div v-for="q in questionsMap[currentStage.stage_id]" :key="q.question_id" class="question-item">
            <div class="question-header-row">
              <span class="q-order">{{ q.display_order }}.</span>
              <span class="q-title">{{ q.question_text }}</span>
              <span class="spacer"></span>
              <span class="badge badge-type">{{ q.question_type }}</span>
              <span v-if="q.is_required" class="badge badge-required">Required</span>
            </div>
            <div v-if="q.options && parseOptions(q.options).length" class="question-options">
              <div class="options-label">Options</div>
              <ul>
                <li v-for="(opt, idx) in parseOptions(q.options)" :key="idx">{{ opt }}</li>
              </ul>
            </div>
            <div v-if="q.help_text" class="question-help">{{ q.help_text }}</div>
          </div>
        </div>
      </section>

      <!-- Vendor Risk Assessment for Final Vendor Approval -->
      <section v-if="isFinalVendorApproval(currentStage)" class="section">
        <h2 class="section-title">Vendor Risk Assessment</h2>
        
        <!-- Vendor Information -->
        <div v-if="getVendorData(currentStage)" class="vendor-info">
          <div class="vendor-header">
            <h5>{{ getVendorData(currentStage).company_name }}</h5>
            <div class="vendor-tags">
              <span class="badge badge-vendor-code">{{ getVendorData(currentStage).vendor_code }}</span>
              <span :class="getVendorRiskBadgeClass(getVendorData(currentStage).risk_level)">
                {{ getVendorData(currentStage).risk_level }}
              </span>
              <span v-if="getVendorData(currentStage).is_critical_vendor" class="badge badge-critical">Critical Vendor</span>
            </div>
          </div>
          
          <div class="vendor-details">
            <div class="detail-row">
              <span class="detail-label">Business Type:</span>
              <span class="detail-value">{{ getVendorData(currentStage).business_type }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">Industry Sector:</span>
              <span class="detail-value">{{ getVendorData(currentStage).industry_sector }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">Status:</span>
              <span :class="getVendorStatusBadgeClass(getVendorData(currentStage).status)">
                {{ getVendorData(currentStage).status }}
              </span>
            </div>
          </div>
        </div>

        <!-- Risk Summary -->
        <div v-if="getRiskSummary(currentStage)" class="risk-summary-card">
          <h6>Risk Summary</h6>
          <div class="risk-stats">
            <div class="stat-item">
              <span class="stat-label">Total Risks:</span>
              <span class="stat-value">{{ getRiskSummary(currentStage).total_risks || 0 }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">High Priority:</span>
              <span class="stat-value danger">{{ getRiskSummary(currentStage).high_priority || 0 }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Medium Priority:</span>
              <span class="stat-value warning">{{ getRiskSummary(currentStage).medium_priority || 0 }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Open Risks:</span>
              <span class="stat-value danger">{{ getRiskSummary(currentStage).open_risks || 0 }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Mitigated:</span>
              <span class="stat-value success">{{ getRiskSummary(currentStage).mitigated_risks || 0 }}</span>
            </div>
          </div>
        </div>

        <!-- Internal Risks -->
        <div v-if="getInternalRisks(currentStage) && getInternalRisks(currentStage).length > 0" class="risks-list internal-risks">
          <div class="risk-section-header">
            <h6><i class="el-icon-warning-outline"></i> Internal Risks ({{ getInternalRisks(currentStage).length }})</h6>
            <span class="risk-type-badge internal-badge">Internal Assessment</span>
          </div>
          <div class="risks-grid">
            <div v-for="risk in getInternalRisks(currentStage).slice(0, 6)" :key="risk.id" class="risk-card internal-risk-card">
              <div class="risk-header">
                <span class="risk-title">{{ risk.title }}</span>
                <div class="risk-badges">
                  <span class="badge badge-internal">Internal</span>
                  <span :class="getRiskPriorityBadgeClass(risk.priority)">
                    {{ risk.priority || 'N/A' }}
                  </span>
                  <span :class="getRiskStatusBadgeClass(risk.status)">
                    {{ risk.status || 'N/A' }}
                  </span>
                  <span v-if="risk.score" class="badge badge-score">
                    Score: {{ risk.score }}
                  </span>
                </div>
              </div>
              
              <div class="risk-content">
                <p class="risk-description">{{ risk.description || 'No description available' }}</p>
                
                <div v-if="risk.likelihood || risk.impact" class="risk-metrics">
                  <span class="metric">Likelihood: {{ risk.likelihood || 'N/A' }}</span>
                  <span class="metric">Impact: {{ risk.impact || 'N/A' }}</span>
                </div>
                
                <div v-if="risk.ai_explanation" class="ai-explanation">
                  <strong>AI Analysis:</strong>
                  <p>{{ risk.ai_explanation }}</p>
                </div>
                
                <div v-if="risk.suggested_mitigations && risk.suggested_mitigations.length > 0" class="mitigations">
                  <strong>Suggested Mitigations:</strong>
                  <ul>
                    <li v-for="(mitigation, index) in risk.suggested_mitigations.slice(0, 3)" :key="index">
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
            </div>
          </div>
          
          <div v-if="getInternalRisks(currentStage).length > 6" class="more-risks">
            <p>{{ getInternalRisks(currentStage).length - 6 }} more internal risks available in the full assessment...</p>
          </div>
        </div>

        <!-- External Risks -->
        <div v-if="getExternalRisks(currentStage) && getExternalRisks(currentStage).length > 0" class="risks-list external-risks">
          <div class="risk-section-header">
            <h6><i class="el-icon-search"></i> External Screening Risks ({{ getExternalRisks(currentStage).length }})</h6>
            <span class="risk-type-badge external-badge">External Screening</span>
          </div>
          <div class="risks-grid">
            <div v-for="risk in getExternalRisks(currentStage).slice(0, 6)" :key="risk.match_id" class="risk-card external-risk-card">
              <div class="risk-header">
                <span class="risk-title">{{ risk.match_type || 'Screening Match' }}</span>
                <div class="risk-badges">
                  <span class="badge badge-external">External</span>
                  <span :class="getScreeningTypeBadgeClass(risk.screening_type)">
                    {{ risk.screening_type || 'N/A' }}
                  </span>
                  <span :class="getResolutionStatusBadgeClass(risk.resolution_status)">
                    {{ risk.resolution_status || 'N/A' }}
                  </span>
                  <span v-if="risk.match_score" class="badge badge-score">
                    Score: {{ risk.match_score }}%
                  </span>
                </div>
              </div>
              
              <div class="risk-content">
                <div class="screening-details">
                  <p class="risk-description">{{ getMatchDescription(risk) }}</p>
                  
                  <div class="screening-metadata">
                    <span class="metadata-item">Date: {{ formatDate(risk.screening_date) }}</span>
                    <span class="metadata-item">Matches: {{ risk.total_matches || 0 }}</span>
                    <span v-if="risk.high_risk_matches" class="metadata-item high-risk">High Risk: {{ risk.high_risk_matches }}</span>
                  </div>
                  
                  <div v-if="risk.match_details" class="match-details">
                    <strong>Match Details:</strong>
                    <div class="match-details-content">
                      {{ formatMatchDetails(risk.match_details) }}
                    </div>
                  </div>
                  
                  <div v-if="risk.resolution_notes" class="resolution-notes">
                    <strong>Resolution Notes:</strong>
                    <p>{{ risk.resolution_notes }}</p>
                  </div>
                  
                  <div v-if="risk.search_terms" class="search-terms">
                    <strong>Search Terms:</strong>
                    <div class="search-terms-list">
                      <span v-for="(term, index) in getSearchTerms(risk.search_terms)" :key="index" class="search-term">
                        {{ term }}
                      </span>
                    </div>
                  </div>
                </div>
                
                <div class="risk-metadata">
                  <span class="metadata-item">Match ID: {{ risk.match_id }}</span>
                  <span class="metadata-item">Screening ID: {{ risk.screening_id }}</span>
                  <span v-if="risk.resolved_date" class="metadata-item">Resolved: {{ formatDate(risk.resolved_date) }}</span>
                </div>
              </div>
            </div>
          </div>
          
          <div v-if="getExternalRisks(currentStage).length > 6" class="more-risks">
            <p>{{ getExternalRisks(currentStage).length - 6 }} more external screening risks available...</p>
          </div>
        </div>

        <!-- No Risks Message -->
        <div v-if="(!getInternalRisks(currentStage) || getInternalRisks(currentStage).length === 0) && 
                   (!getExternalRisks(currentStage) || getExternalRisks(currentStage).length === 0)" class="empty-message">
          <p>No Escalated Risks Found</p>
          <p class="empty-subtext">No internal risks or external screening escalations identified for this vendor.</p>
        </div>
      </section>

      <!-- Stage Actions -->
      <section v-if="canMakeDecision(currentStage)" class="section">
        <h2 class="section-title">Stage Decision</h2>
        
        <form class="form">
          <div class="form-item">
            <label>Decision</label>
            <div class="radio-group">
              <label class="radio-item">
                <input type="radio" v-model="stageDecision.decision" value="APPROVE" />
                <span>Approve</span>
              </label>
              <label class="radio-item">
                <input type="radio" v-model="stageDecision.decision" value="REJECT" />
                <span>Reject</span>
              </label>
            </div>
          </div>

          <div v-if="stageDecision.decision === 'REJECT'" class="form-item">
            <label>Rejection Reason</label>
            <textarea
              v-model="stageDecision.rejection_reason"
              :rows="3"
              placeholder="Please provide a reason for rejection..."
              class="form-textarea"
            />
          </div>

          <div class="form-item">
            <label>Comments</label>
            <textarea
              v-model="stageDecision.comments"
              :rows="2"
              placeholder="Additional comments..."
              class="form-textarea"
            />
          </div>

          <div class="form-item">
            <button 
              class="btn btn-primary"
              type="button"
              @click="submitStageDecision(currentStage)"
              :disabled="submitting"
            >
              {{ submitting ? 'Submitting...' : 'Submit Decision' }}
            </button>
            <button 
              class="btn btn-secondary"
              type="button"
              @click="saveDraft(currentStage)"
              :disabled="savingDraft"
            >
              {{ savingDraft ? 'Saving...' : 'Save Draft' }}
            </button>
          </div>
        </form>
      </section>

      <!-- Decision Already Made - Frozen State -->
      <section v-else-if="hasUserMadeDecision(currentStage)" class="section">
        <h2 class="section-title">Decision Made</h2>
        <div class="info-message" :class="getDecisionAlertType(currentStage.stage_status)">
          <p><strong>You have already made a decision for this stage</strong></p>
          <p>Your decision has been submitted and sent to the next level. The stage is now {{ currentStage.stage_status.toLowerCase() }}.</p>
        </div>
        
        <div class="decision-summary">
          <h3 class="summary-title">Your Decision Summary:</h3>
          <div class="row">
            <div class="col-12">
              <p><strong>Decision:</strong> 
                <span class="tag" :class="getStatusType(currentStage.stage_status)">
                  {{ currentStage.stage_status }}
                </span>
              </p>
              <p><strong>Completed:</strong> {{ formatDate(currentStage.completed_at) }}</p>
            </div>
            <div class="col-12">
              <p v-if="currentStage.rejection_reason"><strong>Reason:</strong> {{ currentStage.rejection_reason }}</p>
              <p v-if="currentStage.response_data && currentStage.response_data.comments"><strong>Comments:</strong> {{ currentStage.response_data.comments }}</p>
            </div>
          </div>
        </div>
      </section>

      <!-- Version History for Tiered Approval Workflows, Final Vendor Approval, and Response Approval -->
      <section v-if="(isMultiLevel(currentStage) || isFinalVendorApproval(currentStage) || isResponseApproval(currentStage) || currentStage.workflow_type === 'MULTI_PERSON') && versionHistory[currentStage.approval_id] && versionHistory[currentStage.approval_id].length > 0" class="section">
        <h2 class="section-title">Version History ({{ versionHistory[currentStage.approval_id].length }} versions)</h2>
        <div class="version-info">
          <p>Complete version tracking for this approval request</p>
        </div>
        <div class="versions-list">
          <div v-for="version in versionHistory[currentStage.approval_id]" :key="version.version_id" class="version-item">
            <div class="version-header">
              <div class="version-title-group">
                <span class="version-title">v{{ version.version_number }} - {{ version.version_label }}</span>
                <span class="version-id">ID: {{ version.version_id }}</span>
              </div>
              <div class="version-badges">
                <span class="tag tag-small" :class="getVersionTypeColor(version.version_type)">
                  {{ version.version_type }}
                </span>
                <span v-if="version.is_current" class="tag tag-success tag-small">Current</span>
                <span v-if="version.is_approved" class="tag tag-success tag-small">Approved</span>
                <span v-else-if="version.is_approved === false" class="tag tag-warning tag-small">Pending</span>
              </div>
            </div>
            <div class="version-details">
              <div class="version-meta-grid">
                <div class="version-meta-item">
                  <span class="meta-label">Created by:</span>
                  <span class="meta-value">{{ version.created_by_name }}</span>
                </div>
                <div class="version-meta-item">
                  <span class="meta-label">Role:</span>
                  <span class="meta-value">{{ version.created_by_role }}</span>
                </div>
                <div class="version-meta-item">
                  <span class="meta-label">User ID:</span>
                  <span class="meta-value">{{ version.created_by }}</span>
                </div>
                <div class="version-meta-item">
                  <span class="meta-label">Created at:</span>
                  <span class="meta-value">{{ formatDate(version.created_at) }}</span>
                </div>
                <div v-if="version.parent_version_id" class="version-meta-item">
                  <span class="meta-label">Parent Version:</span>
                  <span class="meta-value">{{ version.parent_version_id }}</span>
                </div>
              </div>
              
              <div v-if="version.changes_summary" class="version-changes">
                <strong>Changes Summary:</strong>
                <p>{{ version.changes_summary }}</p>
              </div>
              
              <div v-if="version.change_reason" class="version-reason">
                <strong>Change Reason:</strong>
                <p>{{ version.change_reason }}</p>
              </div>
              
              <details v-if="version.json_payload" class="version-payload">
                <summary>View JSON Payload</summary>
                <pre class="json-pre">{{ pretty(version.json_payload) }}</pre>
              </details>
            </div>
          </div>
        </div>
      </section>

      <!-- Stage History -->
      <section v-if="currentStage.stage_status !== 'PENDING'" class="section">
        <h2 class="section-title">Stage History</h2>
        <div class="info-grid">
          <div class="info-item">
            <span class="info-label">Status:</span>
            <span class="info-value">{{ currentStage.stage_status }}</span>
          </div>
          <div v-if="currentStage.completed_at" class="info-item">
            <span class="info-label">Completed:</span>
            <span class="info-value">{{ formatDate(currentStage.completed_at) }}</span>
          </div>
          <div v-if="currentStage.rejection_reason" class="info-item">
            <span class="info-label">Rejection Reason:</span>
            <span class="info-value">{{ currentStage.rejection_reason }}</span>
          </div>
        </div>
      </section>

    </div>

      <!-- No Stage Message -->
      <div v-if="!currentStage" class="empty-state">
        <h2>No stage found</h2>
        <p>The requested stage was not found or you don't have access to it.</p>
      </div>
  
  </div>
  
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import api from '@/utils/api'
import { getCurrentUserId } from '@/utils/session'
import { useNotifications } from '@/composables/useNotifications'
import notificationService from '@/services/notificationService'
import loggingService from '@/services/loggingService'

export default {
  name: 'StageReviewer',
  setup() {
    const { showSuccess, showError, showWarning, showInfo } = useNotifications()
    
    const selectedUserId = ref('')
    const currentStage = ref(null)
    const questionsMap = ref({}) // stage_id -> questions[]
    const versionHistory = ref({}) // approval_id -> versions[]
    const activeVersionCollapse = ref([])
    const submitting = ref(false)
    const savingDraft = ref(false)
    const savingScores = ref(false)
    const questionsAndResponses = ref([])
    const totalScore = ref(null)
    const reviewerScores = ref({}) // question_id -> {score, comment}
    const stageDecision = reactive({
      decision: '',
      rejection_reason: '',
      comments: ''
    })
    const showVersionHistory = ref(false)

    onMounted(async () => {
      await loggingService.logPageView('Vendor', 'Stage Reviewer')
      // Get user_id and stage_id from route query or route params
      const routeUserId = typeof window !== 'undefined' ? new URLSearchParams(window.location.search).get('user_id') : ''
      const stageId = typeof window !== 'undefined' ? new URLSearchParams(window.location.search).get('stage_id') : ''
      
      // Check if we have a review ID from route params (e.g., /review/ACA5ECE8)
      const reviewId = typeof window !== 'undefined' ? window.location.pathname.split('/review/')[1] : ''
      
      selectedUserId.value = routeUserId || getCurrentUserId()
      
      // If we have a review ID, use it as the stage ID
      const targetStageId = stageId || reviewId
      
      if (selectedUserId.value && targetStageId) {
        await fetchSpecificStage(targetStageId)
      }
    })

    const autoExpandVersionHistory = (stage) => {
      // Auto-expand version history for tiered approval workflows
      if (isMultiLevel(stage) || isFinalVendorApproval(stage) || isResponseApproval(stage)) {
        showVersionHistory.value = true
      }
    }


    const fetchSpecificStage = async (stageId) => {
      if (!selectedUserId.value || !stageId) return
      
      try {
        const response = await api.get(`/api/v1/vendor-approval/stages/assigned/${selectedUserId.value}/`)
        const stages = response.data.map(stage => ({
          ...stage,
          request_data_display: stage.request_data ? JSON.stringify(stage.request_data, null, 2) : 'No data'
        }))

        // Find the specific stage (stage_id may be number in API but stageId is always a string from URL)
        const stage = stages.find(s => String(s.stage_id) === String(stageId))
        if (!stage) {
          console.warn('Stage not found or not assigned to this user')
          return
        }

        currentStage.value = stage

        // Fetch questionnaire questions and version history
        const payload = stage.request_data || tryParse(stage.request_data_display)
        const approvalType = payload?.approval_type || payload?.request_data?.approval_type
        const questionnaireId = payload?.questionnaire_id || payload?.request_data?.questionnaire_id
        
        // Normalize approval type for comparison (handle both "questionnaire approval" and "questionnaire_approval")
        const normalizedApprovalType = String(approvalType || '').toLowerCase().replace(/\s+/g, '_')
        
        console.log('🔍 Fetching questions for stage:', {
          stage_id: stage.stage_id,
          approval_type: approvalType,
          normalized_approval_type: normalizedApprovalType,
          questionnaire_id: questionnaireId,
          payload_keys: Object.keys(payload || {})
        })
        
        // Fetch questionnaire questions for regular questionnaire approval
        // Check for "questionnaire_approval" (not "response_approval") and ensure questionnaireId exists
        if (normalizedApprovalType === 'questionnaire_approval' && questionnaireId) {
          try {
            console.log(`📋 Fetching questions for questionnaire_id: ${questionnaireId}`)
            const qRes = await api.get(`/api/v1/vendor-approval/questionnaires/${questionnaireId}/questions/`)
            questionsMap.value[stage.stage_id] = qRes.data || []
            console.log(`✅ Loaded ${questionsMap.value[stage.stage_id].length} questions for stage ${stage.stage_id}`)
          } catch (e) {
            console.error('❌ Error fetching questionnaire questions:', e)
            console.error('Error details:', e.response?.data || e.message)
            questionsMap.value[stage.stage_id] = []
          }
        } else {
          console.log('⏭️ Skipping question fetch:', {
            reason: !questionnaireId ? 'No questionnaire_id' : `Approval type is "${normalizedApprovalType}", not "questionnaire_approval"`,
            normalized_approval_type: normalizedApprovalType,
            questionnaire_id: questionnaireId
          })
        }
        
        // Fetch questionnaire responses for response approval
        if (normalizedApprovalType === 'response_approval') {
          try {
            const questionsResponses = payload?.request_data?.questions_and_responses || payload?.questions_and_responses || []
            
            // Check if stage has existing reviewer scores in response_data
            let existingScores = {}
            if (stage.response_data) {
              try {
                const responseData = typeof stage.response_data === 'string' ? JSON.parse(stage.response_data) : stage.response_data
                if (responseData.reviewer_scores) {
                  existingScores = responseData.reviewer_scores
                  console.log('Found existing scores in stage response_data:', existingScores)
                }
              } catch (e) {
                console.log('No existing scores found in response_data')
              }
            }
            
            questionsAndResponses.value = questionsResponses.map(qr => {
              // Priority: existing scores in response_data > original scores > 0
              const existingScore = existingScores[qr.question_id]?.score || qr.score || 0
              const existingComment = existingScores[qr.question_id]?.comment || qr.reviewer_comment || ''
              
              return {
                ...qr,
                reviewer_score: existingScore,
                reviewer_comment_draft: existingComment
              }
            })
            
            // Initialize reviewer scores
            questionsAndResponses.value.forEach(qr => {
              reviewerScores.value[qr.question_id] = {
                score: qr.reviewer_score || 0,
                comment: qr.reviewer_comment_draft || ''
              }
            })
            
            // Calculate initial total score
            calculateTotalScore()
          } catch (e) {
            console.error('Error loading questionnaire responses:', e)
            questionsAndResponses.value = []
          }
        }
        
        // Load saved draft if available
        await loadSavedDraft(stage.stage_id)
        
        // Fetch version history for tiered approval workflows, final vendor approval, and response approval
        const shouldFetchVersionHistory = 
          isMultiLevel(stage) || 
          isFinalVendorApproval(stage) || 
          isResponseApproval(stage) ||
          stage.workflow_type === 'MULTI_PERSON'
        
        if (shouldFetchVersionHistory) {
          try {
            const vRes = await api.get(`/api/v1/vendor-approval/requests/${stage.approval_id}/versions/`)
            versionHistory.value[stage.approval_id] = vRes.data || []
            console.log(`✓ Version history loaded for stage ${stage.stage_id}: ${versionHistory.value[stage.approval_id].length} versions`)
            console.log('Version history data:', versionHistory.value[stage.approval_id])
            
            // Auto-expand version history for tiered approval workflows
            autoExpandVersionHistory(stage)
            console.log('showVersionHistory after auto-expand:', showVersionHistory.value)
          } catch (e) {
            console.error('Failed to load version history:', e)
            versionHistory.value[stage.approval_id] = []
          }
        }
      } catch (error) {
        console.error('Error fetching stage:', error)
        console.error('Failed to fetch stage details')
      }
    }

    const submitStageDecision = async (stage) => {
      if (!stageDecision.decision) {
        console.warn('Please select a decision')
        return
      }



      try {
        submitting.value = true
        
        // For response approval workflows, ensure scores are saved first
        if (isResponseApproval(stage)) {
          await saveReviewerScoresToAssignment()
        }
        
        // Prepare response_data with all necessary information
        const responseData = {
          decision: stageDecision.decision,
          comments: stageDecision.comments,
          rejection_reason: stageDecision.rejection_reason,
          is_draft: false
        }

        // Include reviewer scores for response approval workflows
        if (isResponseApproval(stage)) {
          responseData.reviewer_scores = reviewerScores.value
          responseData.total_score = totalScore.value
          responseData.scores_saved_at = new Date().toISOString()
          responseData.scores_saved_by = selectedUserId.value
        }

        const decisionData = {
          action: stageDecision.decision,
          user_id: selectedUserId.value,
          user_name: 'Current User',
          response_data: responseData
        }

        await api.post(`/api/v1/vendor-approval/stages/${stage.stage_id}/action/`, decisionData)
        
        console.log('Stage decision submitted successfully')
        
        // Create success notification based on decision
        if (stageDecision.decision === 'APPROVE') {
          await notificationService.createVendorApprovalNotification('stage_approved', {
            stage_id: stage.stage_id,
            stage_name: stage.stage_name,
            approval_id: stage.approval_id
          })
        } else if (stageDecision.decision === 'REJECT') {
          await notificationService.createVendorApprovalNotification('stage_rejected', {
            stage_id: stage.stage_id,
            stage_name: stage.stage_name,
            approval_id: stage.approval_id,
            reason: stageDecision.rejection_reason
          })
        } else {
          await notificationService.createVendorApprovalNotification('decision_submitted', {
            stage_id: stage.stage_id,
            stage_name: stage.stage_name,
            decision: stageDecision.decision
          })
        }
        
        // Reset form and refresh stages
        Object.assign(stageDecision, {
          decision: '',
          rejection_reason: '',
          comments: ''
        })
        
        await fetchSpecificStage(currentStage.value.stage_id)
        
      } catch (error) {
        console.error('Error submitting stage decision:', error)
        console.error(error.response?.data?.error || 'Failed to submit stage decision')
        
        // Create error notification
        await notificationService.createVendorErrorNotification('submit_decision', error.response?.data?.error || error.message, {
          title: 'Decision Submission Failed',
          stage_id: stage.stage_id,
          stage_name: stage.stage_name
        })
      } finally {
        submitting.value = false
      }
    }

    const toTitleCase = (str = '') => str.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())

    const formatWorkflowType = (type) => {
      if (!type) return 'Unknown'
      const typeStr = String(type).toUpperCase()
      if (typeStr === 'MULTI_LEVEL') return 'Tiered Approval'
      if (typeStr === 'MULTI_PERSON') return 'Team Approval'
      return toTitleCase(String(type))
    }

    const formatValue = (value) => {
      if (value === null || value === undefined || value === '') return '—'
      return toTitleCase(String(value))
    }

    const getStatusType = (status) => {
      const statusMap = {
        'PENDING': 'info',
        'IN_PROGRESS': 'warning',
        'APPROVED': 'success',
        'REJECTED': 'danger',
        'SKIPPED': 'info',
        'EXPIRED': 'danger',
        'CANCELLED': 'info'
      }
      return statusMap[status] || 'info'
    }

    const formatDate = (dateString) => {
      if (!dateString) return 'Not set'
      try {
        return new Date(dateString).toLocaleString()
      } catch {
        return dateString
      }
    }

    const tryParse = (maybeString) => {
      if (!maybeString || typeof maybeString !== 'string') return undefined
      try { return JSON.parse(maybeString) } catch { return undefined }
    }

    const pretty = (obj) => {
      try { return JSON.stringify(obj, null, 2) } catch { return String(obj) }
    }

    const renderOptions = (opts) => {
      if (!opts) return ''
      try {
        const o = typeof opts === 'string' ? JSON.parse(opts) : opts
        if (Array.isArray(o)) return o.join(', ')
        if (o && Array.isArray(o.options)) return o.options.join(', ')
        return JSON.stringify(o)
      } catch { return String(opts) }
    }

    const parseOptions = (opts) => {
      if (!opts) return []
      try {
        const o = typeof opts === 'string' ? JSON.parse(opts) : opts
        if (Array.isArray(o)) return o
        if (o && Array.isArray(o.options)) return o.options
        return []
      } catch { return [] }
    }

    const deriveFields = (stage) => {
      const payload = stage.request_data || tryParse(stage.request_data_display) || {}
      const rd = payload.request_data || payload
      const fields = []
      const push = (key, label, value) => {
        if (value !== undefined && value !== null && value !== '') fields.push({ key, label, value })
      }
      push('request_title', 'Title', payload.request_title || rd.request_title)
      push('priority', 'Priority', payload.priority || rd.priority)
      push('requester_name', 'Requester', payload.requester_name || rd.requester_name)
      push('requester_department', 'Department', payload.requester_department || rd.requester_department)
      push('approval_type', 'Approval Type', rd.approval_type)
      push('questionnaire_name', 'Questionnaire', rd.questionnaire_name)
      push('questionnaire_id', 'Questionnaire ID', rd.questionnaire_id)
      push('questionnaire_type', 'Questionnaire Type', rd.questionnaire_type)
      push('business_object_type', 'Business Object Type', payload.business_object_type || rd.business_object_type)
      push('business_object_id', 'Business Object ID', payload.business_object_id || rd.business_object_id)
      push('request_description', 'Description', payload.request_description || rd.description || rd.request_description)
      return fields
    }

    const canMakeDecision = (stage) => {
      // User can make decision if:
      // 1. Stage is PENDING or IN_PROGRESS
      // 2. Stage is assigned to the current user
      // 3. For MULTI_LEVEL workflows, if stage is rejected but overall status is not PENDING_DECISION
      if (stage.stage_status === 'PENDING' || stage.stage_status === 'IN_PROGRESS') {
        return true
      }
      
      // For MULTI_LEVEL workflows, if user rejected and it's sent to admin, they can't make another decision
      if (stage.workflow_type === 'MULTI_LEVEL' && 
          stage.stage_status === 'REJECTED' && 
          stage.overall_status === 'PENDING') {
        return false
      }
      
      return false
    }

    const hasUserMadeDecision = (stage) => {
      // User has made a decision if:
      // 1. Stage is APPROVED, REJECTED, or has completed_at timestamp
      // 2. For MULTI_LEVEL workflows, if stage is REJECTED and overall status is PENDING_DECISION
      if (stage.stage_status === 'APPROVED' || stage.stage_status === 'REJECTED') {
        return true
      }
      
      if (stage.completed_at) {
        return true
      }
      
      return false
    }

    const getDecisionAlertType = (status) => {
      const alertMap = {
        'APPROVED': 'success',
        'REJECTED': 'error',
        'REQUEST_CHANGES': 'warning'
      }
      return alertMap[status] || 'info'
    }

    const isMultiPerson = (stage) => String(stage.workflow_type).toUpperCase() === 'MULTI_PERSON'
    
    const isMultiLevel = (stage) => String(stage.workflow_type).toUpperCase() === 'MULTI_LEVEL'

    const getVersionTypeColor = (versionType) => {
      const colorMap = {
        'INITIAL': 'info',
        'REVISION': 'warning',
        'CONSOLIDATION': 'primary',
        'FINAL': 'success'
      }
      return colorMap[versionType] || 'default'
    }

    // Vendor risk assessment functions
    const isFinalVendorApproval = (stage) => {
      const payload = stage.request_data || tryParse(stage.request_data_display) || {}
      const rd = payload.request_data || payload
      const approvalType = String(rd.approval_type || '').toLowerCase().replace(/\s+/g, '_')
      return approvalType === 'final_vendor_approval'
    }

    const getVendorData = (stage) => {
      const payload = stage.request_data || tryParse(stage.request_data_display) || {}
      const rd = payload.request_data || payload
      return rd.vendor_data || null
    }

    const getVendorRisks = (stage) => {
      const payload = stage.request_data || tryParse(stage.request_data_display) || {}
      const rd = payload.request_data || payload
      return rd.vendor_risks || []
    }

    const getInternalRisks = (stage) => {
      const payload = stage.request_data || tryParse(stage.request_data_display) || {}
      const rd = payload.request_data || payload
      return rd.internal_risks || rd.tprm_risks || []
    }

    const getExternalRisks = (stage) => {
      const payload = stage.request_data || tryParse(stage.request_data_display) || {}
      const rd = payload.request_data || payload
      // Filter for ESCALATED status as per user requirement
      return (rd.external_risks || rd.screening_risks || []).filter(risk => risk.resolution_status === 'ESCALATED')
    }

    const getRiskSummary = (stage) => {
      const payload = stage.request_data || tryParse(stage.request_data_display) || {}
      const rd = payload.request_data || payload
      return rd.risk_summary || null
    }

    const getVendorRiskBadgeClass = (riskLevel) => {
      const level = String(riskLevel || '').toLowerCase()
      const classMap = {
        'low': 'badge badge-risk-low',
        'medium': 'badge badge-risk-medium',
        'high': 'badge badge-risk-high',
        'critical': 'badge badge-risk-critical'
      }
      return classMap[level] || 'badge badge-risk-unknown'
    }

    const getVendorStatusBadgeClass = (status) => {
      const statusStr = String(status || '').toLowerCase()
      const classMap = {
        'active': 'badge badge-status-active',
        'inactive': 'badge badge-status-inactive',
        'pending': 'badge badge-status-pending',
        'suspended': 'badge badge-status-suspended',
        'terminated': 'badge badge-status-terminated'
      }
      return classMap[statusStr] || 'badge badge-status-unknown'
    }

    const getRiskPriorityBadgeClass = (priority) => {
      const priorityStr = String(priority || '').toLowerCase()
      const classMap = {
        'low': 'badge badge-priority-low',
        'medium': 'badge badge-priority-medium',
        'high': 'badge badge-priority-high',
        'critical': 'badge badge-priority-critical'
      }
      return classMap[priorityStr] || 'badge badge-priority-unknown'
    }

    const getRiskStatusBadgeClass = (status) => {
      const statusStr = String(status || '').toLowerCase()
      const classMap = {
        'open': 'badge badge-risk-status-open',
        'active': 'badge badge-risk-status-open',
        'identified': 'badge badge-risk-status-open',
        'in_progress': 'badge badge-risk-status-progress',
        'mitigated': 'badge badge-risk-status-mitigated',
        'closed': 'badge badge-risk-status-mitigated',
        'resolved': 'badge badge-risk-status-mitigated'
      }
      return classMap[statusStr] || 'badge badge-risk-status-unknown'
    }

    const getScreeningTypeBadgeClass = (screeningType) => {
      const typeStr = String(screeningType || '').toLowerCase()
      const classMap = {
        'worldcheck': 'badge badge-screening-worldcheck',
        'ofac': 'badge badge-screening-ofac',
        'pep': 'badge badge-screening-pep',
        'sanctions': 'badge badge-screening-sanctions',
        'adverse_media': 'badge badge-screening-media'
      }
      return classMap[typeStr] || 'badge badge-screening-unknown'
    }

    const getResolutionStatusBadgeClass = (status) => {
      const statusStr = String(status || '').toLowerCase()
      const classMap = {
        'pending': 'badge badge-resolution-pending',
        'cleared': 'badge badge-resolution-cleared',
        'escalated': 'badge badge-resolution-escalated',
        'blocked': 'badge badge-resolution-blocked'
      }
      return classMap[statusStr] || 'badge badge-resolution-unknown'
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

    // Response approval specific functions
    const isResponseApproval = (stage) => {
      const payload = stage.request_data || tryParse(stage.request_data_display) || {}
      const rd = payload.request_data || payload
      const approvalType = String(rd.approval_type || '').toLowerCase().replace(/\s+/g, '_')
      return approvalType === 'response_approval'
    }

    const updateScore = (questionId, score) => {
      if (reviewerScores.value[questionId]) {
        reviewerScores.value[questionId].score = score
      } else {
        reviewerScores.value[questionId] = { score: score, comment: '' }
      }
      calculateTotalScore()
    }

    const updateReviewerComment = (questionId, comment) => {
      if (reviewerScores.value[questionId]) {
        reviewerScores.value[questionId].comment = comment
      } else {
        reviewerScores.value[questionId] = { score: 0, comment: comment }
      }
    }

    const getMaxScore = (scoringWeight) => {
      return parseFloat(scoringWeight) * 10 || 10
    }

    // Format file size for display
    const formatFileSize = (bytes) => {
      if (bytes === 0) return '0 Bytes'
      const k = 1024
      const sizes = ['Bytes', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    }

    const calculateTotalScore = () => {
      if (questionsAndResponses.value.length === 0) {
        totalScore.value = null
        return
      }

      let totalScore_weighted = 0
      let totalMaxScore_weighted = 0

      questionsAndResponses.value.forEach(qr => {
        const score = reviewerScores.value[qr.question_id]?.score || qr.reviewer_score || 0
        const weight = parseFloat(qr.scoring_weight) || 1
        const maxScoreForQuestion = getMaxScore(weight)
        
        // Calculate weighted scores
        totalScore_weighted += score * weight
        totalMaxScore_weighted += maxScoreForQuestion * weight
      })

      if (totalMaxScore_weighted > 0) {
        totalScore.value = (totalScore_weighted / totalMaxScore_weighted) * 100
      } else {
        totalScore.value = 0
      }
      
      console.log(`Total Score Calculation: ${totalScore_weighted}/${totalMaxScore_weighted} = ${totalScore.value.toFixed(1)}%`)
    }

    const getScoreClass = (score) => {
      if (score >= 80) return 'score-excellent'
      if (score >= 60) return 'score-good'
      if (score >= 40) return 'score-fair'
      return 'score-poor'
    }

    const saveReviewerScoresToAssignment = async () => {
      if (!currentStage.value) return

      try {
        const payload = currentStage.value.request_data || tryParse(currentStage.value.request_data_display) || {}
        const assignmentId = payload?.request_data?.questionnaire_assignment_id || payload?.questionnaire_assignment_id

        if (!assignmentId) {
          console.error('Assignment ID not found')
          return
        }

        const scores = Object.entries(reviewerScores.value).map(([questionId, data]) => ({
          question_id: parseInt(questionId),
          score: data.score,
          reviewer_comment: data.comment
        }))

        // Save scores to the questionnaire assignment
        await api.post('/api/v1/vendor-approval/reviewer-scores/save/', {
          assignment_id: assignmentId,
          scores: scores,
          reviewer_id: selectedUserId.value
        })

        console.log('Reviewer scores saved to assignment successfully')
        
      } catch (error) {
        console.error('Error saving reviewer scores to assignment:', error)
      }
    }

    const saveReviewerScores = async () => {
      if (!currentStage.value) return

      try {
        savingScores.value = true
        
        const payload = currentStage.value.request_data || tryParse(currentStage.value.request_data_display) || {}
        const assignmentId = payload?.request_data?.questionnaire_assignment_id || payload?.questionnaire_assignment_id

        if (!assignmentId) {
          console.error('Assignment ID not found')
          return
        }

        const scores = Object.entries(reviewerScores.value).map(([questionId, data]) => ({
          question_id: parseInt(questionId),
          score: data.score,
          reviewer_comment: data.comment
        }))

        // Save scores to the questionnaire assignment
        await api.post('/api/v1/vendor-approval/reviewer-scores/save/', {
          assignment_id: assignmentId,
          scores: scores,
          reviewer_id: selectedUserId.value
        })

        // Also save scores to stage response_data for persistence
        const stageScoreData = {
          reviewer_scores: reviewerScores.value,
          total_score: totalScore.value,
          scores_saved_at: new Date().toISOString(),
          scores_saved_by: selectedUserId.value
        }

        await api.post('/api/v1/vendor-approval/stage-draft/save/', {
          stage_id: currentStage.value.stage_id,
          draft_data: stageScoreData,
          user_id: selectedUserId.value
        })

        console.log('Reviewer scores saved successfully')
        
        // Update the questions and responses with new scores
        questionsAndResponses.value.forEach(qr => {
          const updatedScore = reviewerScores.value[qr.question_id]
          if (updatedScore) {
            qr.reviewer_score = updatedScore.score
            qr.reviewer_comment = updatedScore.comment
          }
        })

      } catch (error) {
        console.error('Error saving reviewer scores:', error)
        console.error('Failed to save reviewer scores')
      } finally {
        savingScores.value = false
      }
    }

    const loadSavedDraft = async (stageId) => {
      try {
        const response = await api.get(`/api/v1/vendor-approval/stage-draft/load/${stageId}/`, {
          params: { user_id: selectedUserId.value }
        })
        
        if (response.data.success && response.data.draft_data) {
          const draftData = response.data.draft_data
          
          // Restore stage decision if it's a draft (works for all workflow types)
          if (draftData.is_draft || draftData.status === 'DRAFT') {
            // Restore basic decision data
            stageDecision.decision = draftData.decision || ''
            stageDecision.rejection_reason = draftData.rejection_reason || ''
            stageDecision.comments = draftData.comments || ''
            
            // Restore reviewer scores for response approval workflows
            if (draftData.reviewer_scores && isResponseApproval(currentStage.value)) {
              Object.keys(draftData.reviewer_scores).forEach(questionId => {
                if (reviewerScores.value[questionId]) {
                  reviewerScores.value[questionId] = {
                    ...reviewerScores.value[questionId],
                    ...draftData.reviewer_scores[questionId]
                  }
                } else {
                  reviewerScores.value[questionId] = draftData.reviewer_scores[questionId]
                }
                
                // Update the questionnaire responses display
                const qr = questionsAndResponses.value.find(q => q.question_id == questionId)
                if (qr) {
                  qr.reviewer_score = draftData.reviewer_scores[questionId].score || 0
                  qr.reviewer_comment_draft = draftData.reviewer_scores[questionId].comment || ''
                }
              })
              
              // Recalculate total score
              calculateTotalScore()
            }
            
            // Restore total score if available
            if (draftData.total_score !== undefined && draftData.total_score !== null) {
              totalScore.value = draftData.total_score
            }
            
            // Show draft loaded message
            console.log('Draft data loaded successfully')
            
            console.log('Draft loaded successfully for workflow type:', currentStage.value?.workflow_type)
          }
        }
      } catch (error) {
        // Silently fail if no draft exists - this is normal
        console.log('No saved draft found or error loading draft:', error)
      }
    }

    const saveDraft = async (stage) => {
      try {
        savingDraft.value = true
        
        // Prepare draft data based on workflow type
        const draftData = {
          decision: stageDecision.decision,
          rejection_reason: stageDecision.rejection_reason,
          comments: stageDecision.comments,
          saved_at: new Date().toISOString(),
          status: 'DRAFT',
          workflow_type: stage.workflow_type
        }

        // Add reviewer scores for response approval workflows
        if (isResponseApproval(stage)) {
          draftData.reviewer_scores = reviewerScores.value
          draftData.total_score = totalScore.value
        }

        // Add any additional workflow-specific data
        if (isFinalVendorApproval(stage)) {
          // For final vendor approval, could save vendor-specific decision data
          draftData.approval_type = 'final_vendor_approval'
        }

        console.log('Saving draft for workflow type:', stage.workflow_type, 'with data:', Object.keys(draftData))

        await api.post('/api/v1/vendor-approval/stage-draft/save/', {
          stage_id: stage.stage_id,
          draft_data: draftData,
          user_id: selectedUserId.value
        })

        console.log('Draft saved successfully')
        
      } catch (error) {
        console.error('Error saving draft:', error)
        console.error('Failed to save draft')
      } finally {
        savingDraft.value = false
      }
    }

    const toggleVersionHistory = () => {
      showVersionHistory.value = !showVersionHistory.value
    }

    return {
      selectedUserId,
      currentStage,
      submitting,
      savingDraft,
      savingScores,
      questionsAndResponses,
      totalScore,
      reviewerScores,
      stageDecision,
      showVersionHistory,
      toggleVersionHistory,
      autoExpandVersionHistory,
      fetchSpecificStage,
      submitStageDecision,
      canMakeDecision,
      hasUserMadeDecision,
      getDecisionAlertType,
      getStatusType,
      formatWorkflowType,
      formatValue,
      formatDate,
      tryParse, pretty, questionsMap, renderOptions, deriveFields, parseOptions, isMultiPerson, isMultiLevel,
      versionHistory, activeVersionCollapse, getVersionTypeColor,
      isFinalVendorApproval, getVendorData, getVendorRisks, getRiskSummary, getInternalRisks, getExternalRisks,
      getVendorRiskBadgeClass, getVendorStatusBadgeClass, getRiskPriorityBadgeClass, getRiskStatusBadgeClass,
      getScreeningTypeBadgeClass, getResolutionStatusBadgeClass, getMatchDescription, formatMatchDetails, getSearchTerms,
      isResponseApproval, updateScore, updateReviewerComment, getMaxScore, formatFileSize, calculateTotalScore,
      getScoreClass, saveReviewerScores, saveReviewerScoresToAssignment, loadSavedDraft, saveDraft
    }
  }
}
</script>

<style scoped>
/* Base Layout */
.stage-reviewer {
  max-width: 1400px;
  margin: 0 auto;
  padding: 40px 32px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background: #fafbfc;
  color: #1e293b;
  line-height: 1.6;
  /* Professional Theme Tokens */
  --border: #e2e8f0;
  --border-strong: #cbd5e1;
  --bg-surface: #ffffff;
  --bg-subtle: #f8fafc;
  --bg-hover: #f1f5f9;
  --text: #0f172a;
  --text-secondary: #475569;
  --muted: #64748b;
  --accent: #2563eb;
  --accent-hover: #1d4ed8;
  --accent-light: #eff6ff;
  --success: #059669;
  --warning: #d97706;
  --danger: #dc2626;
  --radius: 8px;
  --radius-sm: 6px;
  --shadow-sm: 0 1px 2px 0 rgba(15, 23, 42, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(15, 23, 42, 0.1), 0 2px 4px -1px rgba(15, 23, 42, 0.06);
  --shadow-lg: 0 10px 15px -3px rgba(15, 23, 42, 0.1), 0 4px 6px -2px rgba(15, 23, 42, 0.05);
}

/* Page Header */
.page-header {
  margin-bottom: 48px;
  padding-bottom: 32px;
  border-bottom: 1px solid var(--border);
}

.page-header h1 {
  margin: 0 0 12px 0;
  font-size: 32px;
  font-weight: 700;
  letter-spacing: -0.5px;
  color: var(--text);
  line-height: 1.2;
}

.page-subtitle {
  margin: 0;
  font-size: 16px;
  color: var(--text-secondary);
  font-weight: 400;
  line-height: 1.5;
}

/* Content Wrapper */
.content-wrapper {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

/* Sections */
.section {
  padding: 0;
  margin-bottom: 40px;
}

.section-title {
  margin: 0 0 28px 0;
  font-size: 22px;
  font-weight: 700;
  color: var(--text);
  letter-spacing: -0.3px;
  padding-bottom: 16px;
  border-bottom: 2px solid var(--accent);
  display: flex;
  align-items: center;
  gap: 12px;
}

.section-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 28px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border);
}

/* Stage Info */
.stage-info {
  margin-bottom: 40px;
  background: var(--bg-surface);
  padding: 28px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow-sm);
}

.stage-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--border);
}

.stage-name {
  margin: 0;
  font-size: 26px;
  font-weight: 700;
  color: var(--text);
  letter-spacing: -0.3px;
}

.stage-heading {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.stage-labels {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.stage-chip {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  background: var(--bg-subtle);
  border: 1px solid var(--border);
  border-radius: 9999px;
  font-size: 12px;
  font-weight: 600;
  color: var(--muted);
  letter-spacing: 0.3px;
  text-transform: uppercase;
}

.stage-chip.subtle {
  background: #ecf3ff;
  border-color: #d1e4ff;
  color: #1d4ed8;
}

.stage-request {
  margin: 0;
  color: var(--text-secondary);
  font-size: 16px;
  font-weight: 500;
}

.stage-description-block {
  margin-top: 20px;
  padding: 16px 18px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg-subtle);
  box-shadow: var(--shadow-sm);
}

.stage-description {
  margin: 6px 0 0 0;
  font-size: 15px;
  color: var(--text-secondary);
  line-height: 1.6;
}

.stage-meta-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
  margin-top: 24px;
}

.stage-meta-grid.simple-grid {
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}

.meta-item,
.meta-card {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px 16px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
}

.meta-label {
  font-size: 12px;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.45px;
  font-weight: 600;
}

.meta-value {
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
  letter-spacing: -0.2px;
}

/* Status Badge */
.status-badge {
  display: inline-block;
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border: none;
  transition: all 0.2s ease;
}

.status-badge.info {
  background: #dbeafe;
  color: #1e40af;
}

.status-badge.success {
  background: #dcfce7;
  color: #166534;
}

.status-badge.warning {
  background: #fef3c7;
  color: #b45309;
}

.status-badge.danger {
  background: #fee2e2;
  color: #991b1b;
}

/* Info Grid */
.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 16px;
  background: var(--bg-subtle);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  transition: all 0.2s ease;
}

.info-item:hover {
  background: var(--bg-hover);
  border-color: var(--border-strong);
}

.info-label {
  font-size: 12px;
  color: var(--muted);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.info-value {
  font-size: 15px;
  color: var(--text);
  font-weight: 500;
}

/* JSON Details */
/* Questions List */
.questions-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.question-item {
  padding: 24px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--bg-surface);
  transition: all 0.2s ease;
  box-shadow: var(--shadow-sm);
}

.question-item:hover {
  border-color: var(--border-strong);
  box-shadow: var(--shadow-md);
}

.question-header-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border);
}

.q-order {
  color: #6b7280;
  font-weight: 600;
  font-size: 14px;
}

.q-title {
  font-weight: 500;
  color: var(--text);
  flex: 1;
  font-size: 15px;
}

.spacer {
  flex: 1;
}

.question-options {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--border);
}

.options-label {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 8px;
  font-weight: 500;
}

.question-options ul {
  margin: 0;
  padding-left: 20px;
  color: #374151;
  font-size: 14px;
}

.question-help {
  margin-top: 12px;
  font-size: 13px;
  color: #6b7280;
  font-style: italic;
}

/* Question Response Content */
.question-response-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e5e7eb;
}

.question-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.q-number {
  background: #4b5563;
  color: white;
  padding: 4px 10px;
  border-radius: 4px;
  font-weight: 600;
  font-size: 12px;
  min-width: 36px;
  text-align: center;
}

.q-text {
  font-weight: 500;
  color: #111827;
  flex: 1;
  font-size: 15px;
}

.q-weight {
  background: #f3f4f6;
  color: #374151;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}

.question-badges {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.question-response-content {
  display: grid;
  grid-template-columns: 1fr 380px;
  gap: 24px;
}

@media (max-width: 1200px) {
  .question-response-content {
    grid-template-columns: 1fr;
  }
}

.vendor-response-section,
.scoring-section {
  padding: 16px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--bg-subtle);
}

.vendor-response-section h5,
.scoring-section h5 {
  margin: 0 0 12px 0;
  color: #374151;
  font-size: 14px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.response-text {
  background: var(--bg-surface);
  padding: 12px;
  border-radius: 4px;
  border: 1px solid var(--border);
  margin-bottom: 12px;
  white-space: pre-wrap;
  line-height: 1.6;
  font-size: 14px;
  color: #374151;
}

.vendor-comment,
.existing-comment {
  margin-top: 12px;
  padding: 12px;
  background: #f0f9ff;
  border: 1px solid #dbeafe;
  border-radius: 4px;
}

.vendor-comment p,
.existing-comment p {
  margin: 8px 0 0 0;
  line-height: 1.5;
  color: #374151;
  font-size: 14px;
}

.file-uploads {
  margin-top: 16px;
  padding: 16px;
  background: #fffbeb;
  border: 1px solid var(--border);
  border-radius: 6px;
}

.file-list {
  margin-top: 12px;
}

.file-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: 4px;
  margin-bottom: 8px;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.file-icon {
  width: 20px;
  height: 20px;
  color: #6b7280;
  flex-shrink: 0;
}

.file-details {
  flex: 1;
  min-width: 0;
}

.file-name {
  font-weight: 500;
  color: #111827;
  margin-bottom: 2px;
  word-break: break-all;
  font-size: 14px;
}

.file-size {
  font-size: 12px;
  color: #6b7280;
}

.file-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.file-download-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: var(--accent);
  color: white;
  text-decoration: none;
  border-radius: 4px;
  font-size: 13px;
  font-weight: 500;
  transition: background 0.2s;
}

.file-download-btn:hover {
  background: var(--accent-strong);
  color: white;
  text-decoration: none;
}

.file-download-btn svg {
  width: 14px;
  height: 14px;
}

.file-unavailable {
  color: #dc2626;
  font-size: 13px;
  font-style: italic;
}

/* Scoring */
.total-score {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  background: var(--accent-light);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow-sm);
}

.score-label {
  font-weight: 600;
  color: var(--muted);
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.score-value {
  font-size: 20px;
  font-weight: 800;
  padding: 6px 12px;
  border-radius: 6px;
  min-width: 70px;
  text-align: center;
}

.score-excellent {
  background: #d1fae5;
  color: #065f46;
}

.score-good {
  background: #fef3c7;
  color: #92400e;
}

.score-fair {
  background: #fee2e2;
  color: #991b1b;
}

.score-poor {
  background: #fee2e2;
  color: #991b1b;
}

.score-input-group {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-item label {
  font-size: 13px;
  font-weight: 500;
  color: #374151;
}

.score-input-container {
  display: flex;
  align-items: center;
  gap: 8px;
}

.form-input {
  padding: 10px 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 14px;
  transition: all 0.2s ease;
  background: var(--bg-surface);
  color: var(--text);
}

.form-input:hover {
  border-color: var(--border-strong);
}

.form-input:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
  background: var(--bg-surface);
}

.score-input {
  width: 90px;
  text-align: center;
  font-weight: 700;
}

.max-score-label {
  color: var(--muted);
  font-weight: 600;
  font-size: 14px;
}

.form-textarea {
  padding: 12px 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 14px;
  font-family: inherit;
  resize: vertical;
  transition: all 0.2s ease;
  background: var(--bg-surface);
  color: var(--text);
  line-height: 1.5;
}

.form-textarea:hover {
  border-color: var(--border-strong);
}

.form-textarea:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
  background: var(--bg-surface);
}

/* Action Buttons */
.action-buttons {
  display: flex;
  gap: 12px;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid var(--border);
}

/* Buttons */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 12px 24px;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  font-size: 14px;
  font-weight: 600;
  text-decoration: none;
  cursor: pointer;
  transition: all 0.2s ease;
  min-height: 44px;
  letter-spacing: 0.3px;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--accent);
  color: white;
  border-color: var(--accent);
  box-shadow: 0 1px 3px rgba(37, 99, 235, 0.3);
}

.btn-primary:hover:not(:disabled) {
  background: var(--accent-hover);
  border-color: var(--accent-hover);
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4);
  transform: translateY(-1px);
}

.btn-secondary {
  background: var(--bg-surface);
  color: var(--accent);
  border-color: var(--border-strong);
}

.btn-secondary:hover:not(:disabled) {
  background: var(--bg-hover);
  border-color: var(--accent);
  color: var(--accent-hover);
}

/* Badges */
.badge {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 500;
  border: 1px solid transparent;
}

.badge-type {
  background: #f3f4f6;
  color: #374151;
  border-color: #e5e7eb;
}

.badge-required {
  background: #fee2e2;
  color: #991b1b;
  border-color: #fecaca;
}

.badge-completed {
  background: #d1fae5;
  color: #065f46;
  border-color: #a7f3d0;
}

.badge-vendor-code {
  background: #ede9fe;
  color: #5b21b6;
  border-color: #ddd6fe;
}

.badge-critical {
  background: #fee2e2;
  color: #991b1b;
  border-color: #fecaca;
}

.badge-score {
  background: #dbeafe;
  color: #1e40af;
  border-color: #bfdbfe;
}

.badge-risk-low {
  background: #d1fae5;
  color: #065f46;
  border-color: #a7f3d0;
}

.badge-risk-medium {
  background: #fef3c7;
  color: #92400e;
  border-color: #fde68a;
}

.badge-risk-high,
.badge-risk-critical {
  background: #fee2e2;
  color: #991b1b;
  border-color: #fecaca;
}

.badge-status-active {
  background: #d1fae5;
  color: #065f46;
  border-color: #a7f3d0;
}

.badge-status-inactive,
.badge-status-pending {
  background: #fef3c7;
  color: #92400e;
  border-color: #fde68a;
}

.badge-status-suspended,
.badge-status-terminated {
  background: #fee2e2;
  color: #991b1b;
  border-color: #fecaca;
}

.badge-priority-low {
  background: #d1fae5;
  color: #065f46;
  border-color: #a7f3d0;
}

.badge-priority-medium {
  background: #fef3c7;
  color: #92400e;
  border-color: #fde68a;
}

.badge-priority-high,
.badge-priority-critical {
  background: #fee2e2;
  color: #991b1b;
  border-color: #fecaca;
}

.badge-risk-status-open {
  background: #fee2e2;
  color: #991b1b;
  border-color: #fecaca;
}

.badge-risk-status-progress {
  background: #fef3c7;
  color: #92400e;
  border-color: #fde68a;
}

.badge-risk-status-mitigated {
  background: #d1fae5;
  color: #065f46;
  border-color: #a7f3d0;
}

.badge-risk-unknown,
.badge-status-unknown,
.badge-priority-unknown,
.badge-risk-status-unknown {
  background: #f3f4f6;
  color: #6b7280;
  border-color: #e5e7eb;
}

.badge-screening-worldcheck,
.badge-screening-ofac,
.badge-screening-pep,
.badge-screening-sanctions,
.badge-screening-media {
  background: #fee2e2;
  color: #991b1b;
  border-color: #fecaca;
}

.badge-screening-unknown {
  background: #f3f4f6;
  color: #6b7280;
  border-color: #e5e7eb;
}

.badge-resolution-pending {
  background: #fef3c7;
  color: #92400e;
  border-color: #fde68a;
}

.badge-resolution-cleared {
  background: #d1fae5;
  color: #065f46;
  border-color: #a7f3d0;
}

.badge-resolution-escalated {
  background: #fee2e2;
  color: #991b1b;
  border-color: #fecaca;
}

.badge-resolution-blocked {
  background: #1f2937;
  color: #ffffff;
  border-color: #111827;
}

.badge-resolution-unknown {
  background: #f3f4f6;
  color: #6b7280;
  border-color: #e5e7eb;
}

.badge-internal {
  background: #dbeafe;
  color: #1e40af;
  border-color: #bfdbfe;
}

.badge-external {
  background: #fef3c7;
  color: #92400e;
  border-color: #fde68a;
}

/* Vendor Risk Section */
.vendor-info {
  margin-bottom: 28px;
  padding: 24px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--bg-surface);
  box-shadow: var(--shadow-sm);
  transition: all 0.2s ease;
}

.vendor-info:hover {
  border-color: var(--border-strong);
  box-shadow: var(--shadow-md);
}

.vendor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border);
}

.vendor-header h5 {
  margin: 0;
  color: var(--text);
  font-size: 20px;
  font-weight: 700;
  letter-spacing: -0.3px;
}

.vendor-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.vendor-details {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.detail-label {
  font-weight: 500;
  color: #6b7280;
  font-size: 14px;
}

.detail-value {
  color: #111827;
  font-size: 14px;
}

.risk-summary-card {
  margin-bottom: 24px;
  padding: 20px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--bg-surface);
}

.risk-summary-card h6 {
  margin: 0 0 16px 0;
  color: #111827;
  font-size: 16px;
  font-weight: 600;
}

.risk-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 16px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  text-align: center;
}

.stat-label {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 6px;
}

.stat-value {
  font-size: 20px;
  font-weight: 600;
  color: #111827;
}

.stat-value.danger {
  color: #dc2626;
}

.stat-value.warning {
  color: #d97706;
}

.stat-value.success {
  color: #059669;
}

/* Risks List */
.risks-list {
  margin-bottom: 32px;
}

.risks-list h6 {
  margin: 0 0 16px 0;
  color: #111827;
  font-size: 16px;
  font-weight: 600;
}

.risks-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
}

.risk-card {
  padding: 20px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg-surface);
  transition: all 0.2s ease;
  box-shadow: var(--shadow-sm);
}

.risk-card:hover {
  border-color: var(--border-strong);
  box-shadow: var(--shadow-md);
}

.risk-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.risk-title {
  font-weight: 600;
  color: #111827;
  flex: 1;
  margin-right: 12px;
  font-size: 15px;
}

.risk-badges {
  display: flex;
  flex-direction: column;
  gap: 4px;
  align-items: flex-end;
}

.risk-content {
  color: #374151;
  font-size: 14px;
}

.risk-description {
  margin: 12px 0;
  line-height: 1.5;
}

.risk-metrics {
  display: flex;
  gap: 12px;
  margin: 12px 0;
}

.metric {
  font-size: 12px;
  color: #6b7280;
  background: #f9fafb;
  padding: 4px 8px;
  border-radius: 4px;
}

.ai-explanation {
  margin: 12px 0;
  padding: 12px;
  background: #eff6ff;
  border: 1px solid #dbeafe;
  border-radius: 4px;
}

.ai-explanation p {
  margin: 6px 0 0 0;
  font-size: 13px;
}

.mitigations {
  margin: 12px 0;
  padding: 12px;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 4px;
}

.mitigations ul {
  margin: 6px 0 0 0;
  padding-left: 20px;
}

.mitigations li {
  font-size: 13px;
  margin: 4px 0;
}

.risk-section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 12px 16px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
}

.risk-section-header h6 {
  margin: 0;
  color: #111827;
  font-size: 15px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.risk-type-badge {
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.internal-badge {
  background: #dbeafe;
  color: #1e40af;
  border: 1px solid #bfdbfe;
}

.external-badge {
  background: #fef3c7;
  color: #92400e;
  border: 1px solid #fde68a;
}

.internal-risks {
  border-left: 3px solid #3b82f6;
  padding-left: 16px;
}

.external-risks {
  border-left: 3px solid #f59e0b;
  padding-left: 16px;
  margin-top: 24px;
}

.internal-risk-card {
  border-left: 3px solid #3b82f6;
}

.external-risk-card {
  border-left: 3px solid #f59e0b;
}

.screening-details {
  padding: 0;
}

.screening-metadata {
  display: flex;
  gap: 12px;
  margin: 12px 0;
  flex-wrap: wrap;
}

.screening-metadata .metadata-item {
  background: #f3f4f6;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 11px;
  color: #374151;
}

.screening-metadata .high-risk {
  background: #fee2e2;
  color: #991b1b;
  font-weight: 600;
}

.match-details {
  margin: 12px 0;
  padding: 12px;
  background: #fffbeb;
  border: 1px solid #fef3c7;
  border-radius: 4px;
}

.match-details-content {
  margin-top: 6px;
  font-size: 13px;
  color: #374151;
  white-space: pre-wrap;
}

.resolution-notes {
  margin: 12px 0;
  padding: 12px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 4px;
}

.search-terms {
  margin: 12px 0;
}

.search-terms-list {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-top: 6px;
}

.search-term {
  background: #ede9fe;
  color: #5b21b6;
  padding: 3px 8px;
  border-radius: 12px;
  font-size: 11px;
  border: 1px solid #ddd6fe;
}

.risk-metadata {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #f3f4f6;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.metadata-item {
  background: #f9fafb;
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 11px;
  color: #6b7280;
  border: 1px solid #e5e7eb;
}

.more-risks {
  text-align: center;
  margin-top: 16px;
  padding: 12px;
  background: #fffbeb;
  border: 1px solid #fef3c7;
  border-radius: 6px;
  color: #92400e;
  font-size: 14px;
}

/* Form Elements */
.form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.radio-group {
  display: flex;
  gap: 24px;
  margin-top: 8px;
}

.radio-item {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.radio-item input[type="radio"] {
  margin: 0;
}

/* Info Messages */
.info-message {
  padding: 16px 20px;
  border-radius: var(--radius-sm);
  margin-bottom: 24px;
  border: 1px solid;
  box-shadow: var(--shadow-sm);
}

.info-message.success {
  background: #f0fdf4;
  border-color: #86efac;
  color: #166534;
}

.info-message.error {
  background: #fef2f2;
  border-color: #fca5a5;
  color: #991b1b;
}

.info-message.warning {
  background: #fffbeb;
  border-color: #fcd34d;
  color: #92400e;
}

.info-message.info {
  background: #eff6ff;
  border-color: #93c5fd;
  color: #1e40af;
}

.info-message p {
  margin: 6px 0;
  font-size: 14px;
  font-weight: 500;
  line-height: 1.5;
}

/* Decision Summary */
.decision-summary {
  margin-top: 24px;
  padding: 24px;
  background: var(--bg-subtle);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow-sm);
}

.summary-title {
  margin: 0 0 20px 0;
  color: var(--text);
  font-size: 18px;
  font-weight: 700;
  letter-spacing: -0.3px;
}

.decision-summary p {
  margin: 10px 0;
  font-size: 15px;
  color: var(--text-secondary);
  line-height: 1.6;
}

/* Version History */
.version-info {
  margin-bottom: 24px;
  padding: 16px;
  background: var(--accent-light);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow-sm);
}

.version-info p {
  margin: 0;
  font-size: 14px;
  color: var(--text-secondary);
  font-weight: 500;
}

.versions-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.version-item {
  padding: 24px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--bg-surface);
  box-shadow: var(--shadow-sm);
  transition: all 0.2s ease;
}

.version-item:hover {
  border-color: var(--border-strong);
  box-shadow: var(--shadow-md);
}

.version-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border);
}

.version-title-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.version-title {
  font-weight: 700;
  color: var(--text);
  font-size: 16px;
  letter-spacing: -0.2px;
}

.version-id {
  font-size: 11px;
  color: var(--muted);
  font-family: 'Monaco', 'Menlo', monospace;
  letter-spacing: 0.3px;
}

.version-badges {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.version-details {
  color: #374151;
  font-size: 14px;
}

.version-details p {
  margin: 4px 0;
  line-height: 1.5;
}

.version-meta-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.version-meta-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.meta-label {
  font-size: 11px;
  color: #6b7280;
  text-transform: uppercase;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.meta-value {
  color: #111827;
  font-weight: 500;
  font-size: 14px;
}

.version-changes,
.version-reason {
  margin: 12px 0;
  padding: 12px;
  background: #eff6ff;
  border: 1px solid #dbeafe;
  border-radius: 4px;
}

.version-changes strong,
.version-reason strong {
  color: #1e40af;
  display: block;
  margin-bottom: 6px;
  font-size: 13px;
}

.version-changes p,
.version-reason p {
  margin: 0;
  color: #374151;
  line-height: 1.5;
  font-size: 14px;
}

.version-payload {
  margin-top: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
}

.version-payload summary {
  cursor: pointer;
  padding: 8px 12px;
  background: #f9fafb;
  border-radius: 4px 4px 0 0;
  font-size: 12px;
  color: #6b7280;
  font-weight: 500;
  transition: background 0.2s;
}

.version-payload summary:hover {
  background: #f3f4f6;
}

.version-payload .json-pre {
  margin-top: 0;
  border-radius: 0 0 4px 4px;
  max-height: 400px;
}

.tag {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.tag.info {
  background: #eff6ff;
  color: #1e40af;
}

.tag.success {
  background: #f0fdf4;
  color: #166534;
}

.tag.warning {
  background: #fffbeb;
  color: #92400e;
}

.tag.danger {
  background: #fef2f2;
  color: #991b1b;
}

.tag-small {
  font-size: 11px;
  padding: 3px 8px;
}

/* Empty States */
.empty-state {
  text-align: center;
  padding: 80px 20px;
  background: var(--bg-subtle);
  border-radius: var(--radius);
  margin: 40px 0;
}

.empty-state h2 {
  margin-bottom: 16px;
  color: var(--text);
  font-size: 26px;
  font-weight: 700;
  letter-spacing: -0.3px;
}

.empty-state p {
  margin: 8px 0;
  font-size: 16px;
  color: var(--text-secondary);
  line-height: 1.6;
}

.empty-message {
  text-align: center;
  padding: 48px;
  background: var(--bg-subtle);
  border: 1px dashed var(--border-strong);
  border-radius: var(--radius);
  color: var(--muted);
}

.empty-message p {
  margin: 8px 0;
  font-size: 15px;
  font-weight: 500;
}

.empty-subtext {
  font-size: 14px;
  color: var(--muted);
  font-weight: 400;
}

/* Utility Classes */
.row {
  display: flex;
  flex-wrap: wrap;
  margin: 0 -8px;
}

.col-12 {
  flex: 0 0 100%;
  padding: 0 8px;
}

@media (min-width: 768px) {
  .col-12 {
    flex: 0 0 50%;
  }
}

/* Responsive Design */
@media (max-width: 768px) {
  .stage-reviewer {
    padding: 20px 16px;
  }
  
  .page-header h1 {
    font-size: 24px;
  }
  
  .section-title {
    font-size: 18px;
  }
  
  .question-response-content {
    grid-template-columns: 1fr;
  }
  
  .vendor-details {
    grid-template-columns: 1fr;
  }
  
  .risk-stats {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .risks-grid {
    grid-template-columns: 1fr;
  }
  
  .radio-group {
    flex-direction: column;
    gap: 12px;
  }
  
  .action-buttons {
    flex-direction: column;
  }
  
  .stage-title-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .section-header-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
}
</style>
