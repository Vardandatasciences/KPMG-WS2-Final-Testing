<template>
  <div class="assignee-decision">
    <div class="decision-card">
      <div class="card-header">
        <h2>Assignee Dashboard</h2>
        <p>Review assigned stages and make final decisions on approval requests</p>
      </div>

      <!-- Requester Requests and Stages Section -->
      <div v-if="selectedRequesterId && requesterRequests.length > 0" class="requests-section">
        <div class="divider">
          <h3>Requests and Decisions</h3>
        </div>
        
        <div class="requests-list">
          <div 
            v-for="request in (requesterRequests || [])" 
            :key="request.approval_id" 
            class="request-card"
          >
            <div class="request-header">
              <span class="request-title">{{ request.request_title }}</span>
              <span class="tag" :class="getStatusType(request.overall_status)">
                {{ request.overall_status }}
              </span>
            </div>

            <div class="request-content">
              <div class="request-summary">
                <dl class="summary-list">
                  <div class="summary-pair">
                    <dt>Request ID</dt>
                    <dd>{{ request.approval_id }}</dd>
                  </div>
                  <div class="summary-pair">
                    <dt>Workflow</dt>
                    <dd>{{ request.workflow_name || '—' }}</dd>
                  </div>
                  <div class="summary-pair">
                    <dt>Type</dt>
                    <dd>{{ request.workflow_type }}</dd>
                  </div>
                  <div class="summary-pair">
                    <dt>Priority</dt>
                    <dd>{{ request.priority || '—' }}</dd>
                  </div>
                  <div class="summary-pair">
                    <dt>Requester</dt>
                    <dd>{{ request.requester_id || '—' }}</dd>
                  </div>
                  <div class="summary-pair">
                    <dt>Department</dt>
                    <dd>{{ request.requester_department || '—' }}</dd>
                  </div>
                  <div class="summary-pair">
                    <dt>Created</dt>
                    <dd>{{ formatDate(request.created_at) }}</dd>
                  </div>
                  <div class="summary-pair summary-description">
                    <dt>Description</dt>
                    <dd>{{ request.request_description || 'No description provided' }}</dd>
                  </div>
                </dl>
              </div>

              <!-- Questionnaire Questions for Questionnaire Approval -->
              <div v-if="request.is_questionnaire_approval && request.questionnaire_questions" class="questionnaire-section">
                <h4>Questionnaire Questions</h4>
                <table class="table" style="width: 100%">
                  <thead>
                    <tr>
                      <th>Question</th>
                      <th style="width: 120px">Type</th>
                      <th style="width: 150px">Category</th>
                      <th style="width: 100px">Required</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="question in (request.questionnaire_questions || [])" :key="question.id">
                      <td>{{ question.question_text }}</td>
                      <td>{{ question.question_type }}</td>
                      <td>{{ question.question_category }}</td>
                      <td>
                        <span class="tag" :class="question.is_required ? 'tag-danger' : 'tag-info'">
                          {{ question.is_required ? 'Required' : 'Optional' }}
                        </span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>


              <!-- Vendor Risk Assessment for Final Vendor Approval -->
              <div v-if="isFinalVendorApproval(request)" class="vendor-risk-assessment-section">
                <h4>Vendor Risk Assessment</h4>
                
                <!-- Vendor Information -->
                <div v-if="getVendorData(request)" class="vendor-info-card">
                  <div class="vendor-header">
                    <h5>{{ getVendorData(request).company_name }}</h5>
                    <div class="vendor-tags">
                      <span class="badge badge-vendor-code">{{ getVendorData(request).vendor_code }}</span>
                      <span :class="getVendorRiskBadgeClass(getVendorData(request).risk_level)">
                        {{ getVendorData(request).risk_level }}
                      </span>
                      <span v-if="getVendorData(request).is_critical_vendor" class="badge badge-critical">Critical Vendor</span>
                    </div>
                  </div>
                  
                  <div class="vendor-details">
                    <div class="detail-row">
                      <span class="detail-label">Business Type:</span>
                      <span class="detail-value">{{ getVendorData(request).business_type }}</span>
                    </div>
                    <div class="detail-row">
                      <span class="detail-label">Industry Sector:</span>
                      <span class="detail-value">{{ getVendorData(request).industry_sector }}</span>
                    </div>
                    <div class="detail-row">
                      <span class="detail-label">Status:</span>
                      <span :class="getVendorStatusBadgeClass(getVendorData(request).status)">
                        {{ getVendorData(request).status }}
                      </span>
                    </div>
                  </div>
                </div>

                <!-- Risk Summary -->
                <div v-if="getRiskSummary(request)" class="risk-summary-card">
                  <h6>Risk Summary</h6>
                  <div class="risk-stats">
                    <div class="stat-item">
                      <span class="stat-label">Total Internal:</span>
                      <span class="stat-value">{{ (getInternalRisks(request) || []).length }}</span>
                    </div>
                    <div class="stat-item">
                      <span class="stat-label">Total External:</span>
                      <span class="stat-value">{{ (getExternalRisks(request) || []).length }}</span>
                    </div>
                    <div class="stat-item">
                      <span class="stat-label">High Priority:</span>
                      <span class="stat-value danger">{{ getRiskSummary(request).high_priority || 0 }}</span>
                    </div>
                    <div class="stat-item">
                      <span class="stat-label">Escalated:</span>
                      <span class="stat-value warning">{{ (getExternalRisks(request) || []).filter(r => r.resolution_status === 'ESCALATED').length }}</span>
                    </div>
                  </div>
                </div>

                <!-- Internal Risks -->
                <div v-if="getInternalRisks(request) && getInternalRisks(request).length > 0" class="risks-section internal-risks">
                  <div class="risk-section-header">
                    <h6><i class="el-icon-warning-outline"></i> Internal Risks ({{ getInternalRisks(request).length }})</h6>
                    <span class="risk-type-badge internal-badge">Internal Assessment</span>
                  </div>
                  <div class="risks-grid">
                    <div v-for="risk in getInternalRisks(request).slice(0, 4)" :key="risk.id" class="risk-card internal-risk-card">
                      <div class="risk-header">
                        <span class="risk-title">{{ risk.title }}</span>
                        <div class="risk-badges">
                          <span class="badge badge-internal">Internal</span>
                          <span :class="getRiskPriorityBadgeClass(risk.priority)">{{ risk.priority || 'N/A' }}</span>
                          <span :class="getRiskStatusBadgeClass(risk.status)">{{ risk.status || 'N/A' }}</span>
                        </div>
                      </div>
                      <div class="risk-content">
                        <p class="risk-description">{{ risk.description || 'No description available' }}</p>
                        <div v-if="risk.likelihood || risk.impact" class="risk-metrics">
                          <span class="metric">Likelihood: {{ risk.likelihood || 'N/A' }}</span>
                          <span class="metric">Impact: {{ risk.impact || 'N/A' }}</span>
                          <span v-if="risk.score" class="metric">Score: {{ risk.score }}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div v-if="getInternalRisks(request).length > 4" class="more-risks">
                    <p>{{ getInternalRisks(request).length - 4 }} more internal risks available...</p>
                  </div>
                </div>

                <!-- External Risks -->
                <div v-if="getExternalRisks(request) && getExternalRisks(request).length > 0" class="risks-section external-risks">
                  <div class="risk-section-header">
                    <h6><i class="el-icon-search"></i> External Screening Risks ({{ getExternalRisks(request).length }})</h6>
                    <span class="risk-type-badge external-badge">External Screening</span>
                  </div>
                  <div class="risks-grid">
                    <div v-for="risk in getExternalRisks(request).slice(0, 4)" :key="risk.match_id" class="risk-card external-risk-card">
                      <div class="risk-header">
                        <span class="risk-title">{{ risk.match_type || 'Screening Match' }}</span>
                        <div class="risk-badges">
                          <span class="badge badge-external">External</span>
                          <span :class="getScreeningTypeBadgeClass(risk.screening_type)">{{ risk.screening_type || 'N/A' }}</span>
                          <span :class="getResolutionStatusBadgeClass(risk.resolution_status)">{{ risk.resolution_status || 'N/A' }}</span>
                        </div>
                      </div>
                      <div class="risk-content">
                        <p class="risk-description">{{ getMatchDescription(risk) }}</p>
                        <div class="screening-metadata">
                          <span class="metadata-item">Matches: {{ risk.total_matches || 0 }}</span>
                          <span v-if="risk.high_risk_matches" class="metadata-item high-risk">High Risk: {{ risk.high_risk_matches }}</span>
                          <span v-if="risk.match_score" class="metadata-item">Score: {{ risk.match_score }}%</span>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div v-if="getExternalRisks(request).length > 4" class="more-risks">
                    <p>{{ getExternalRisks(request).length - 4 }} more external screening risks available...</p>
                  </div>
                </div>

                <!-- No Risks Message -->
                <div v-if="(!getInternalRisks(request) || getInternalRisks(request).length === 0) && 
                           (!getExternalRisks(request) || getExternalRisks(request).length === 0)" class="no-risks">
                  <div class="no-risks-content">
                    <i class="el-icon-success"></i>
                    <h6>No Escalated Risks Found</h6>
                    <p>No internal risks or external screening escalations identified for this vendor.</p>
                  </div>
                </div>
              </div>

              <!-- Team Approval Response Scoring Section (shown once per request) -->
              <div v-if="isParallelResponseApproval(request)" class="parallel-scoring-section">
                <div v-if="parallelScoringData && parallelScoringData.assignment" class="scoring-overview">
                  <h5>Team Approval Response Scoring - Comprehensive Review</h5>
                  
                  <!-- Assignment Summary -->
                  <div class="assignment-summary">
                    <el-row :gutter="20">
                      <el-col :span="12">
                        <p><strong>Vendor:</strong> {{ parallelScoringData.assignment.vendor_company_name }} ({{ parallelScoringData.assignment.vendor_code }})</p>
                        <p><strong>Questionnaire:</strong> {{ parallelScoringData.assignment.questionnaire_name }}</p>
                      </el-col>
                      <el-col :span="12">
                        <p><strong>Type:</strong> {{ parallelScoringData.assignment.questionnaire_type }}</p>
                        <p><strong>Current Overall Score:</strong> {{ parallelScoringData.assignment.overall_score || 'Not set' }}</p>
                      </el-col>
                    </el-row>
                  </div>

                  <!-- Review Statistics -->
                  <div v-if="parallelScoringData && parallelScoringData.statistics" class="review-statistics">
                    <div class="row">
                      <div class="col-6">
                        <div class="stat-card">
                          <div class="stat-number">{{ parallelScoringData.statistics.total_reviewers || 0 }}</div>
                          <div class="stat-label">Total Reviewers</div>
                        </div>
                      </div>
                      <div class="col-6">
                        <div class="stat-card">
                          <div class="stat-number">{{ parallelScoringData.statistics.completed_reviews || 0 }}</div>
                          <div class="stat-label">Completed Reviews</div>
                        </div>
                      </div>
                      <div class="col-6">
                        <div class="stat-card">
                          <div class="stat-number">{{ parallelScoringData.statistics.total_questions || 0 }}</div>
                          <div class="stat-label">Total Questions</div>
                        </div>
                      </div>
                      <div class="col-6">
                        <div class="stat-card">
                          <div class="stat-number">{{ parallelScoringData.statistics.questions_with_scores || 0 }}</div>
                          <div class="stat-label">Questions Scored</div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- Overall Score Display -->
                  <div v-if="parallelScoringData && parallelScoringData.assignment" class="overall-score-section">
                    <h6>Overall Score Summary</h6>
                    <div class="overall-score-card">
                      <div class="score-display">
                        <div class="current-score">
                          <span class="score-label">Current Overall Score:</span>
                          <span class="score-value" :class="getScoreClass(parallelScoringData.assignment.overall_score || 0)">
                            {{ (parallelScoringData.assignment.overall_score || 0).toFixed(1) }}
                          </span>
                        </div>
                        <div class="score-breakdown">
                          <span class="breakdown-text">
                            Based on {{ Object.keys(finalScores).filter(id => finalScores[id] !== null && finalScores[id] !== undefined).length }} 
                            of {{ parallelScoringData.questions_and_responses ? parallelScoringData.questions_and_responses.length : 0 }} questions scored
                          </span>
                        </div>
                      </div>
                      <div class="score-actions">
                        <button @click="refreshOverallScoreFromBackend" class="btn btn-info btn-small">
                          Refresh Score
                        </button>
                      </div>
                    </div>
                  </div>

                  <!-- Questions and Consolidated Scores -->
                  <div v-if="parallelScoringData && parallelScoringData.questions_and_responses" class="questions-scoring-section">
                    <h6>Question-by-Question Review & Final Scoring</h6>
                    <div v-for="qr in parallelScoringData.questions_and_responses" :key="qr.question_id" class="question-scoring-card">
                      <div class="question-header">
                        <div class="question-info">
                          <div class="question-number-badge">
                            <span class="q-number">Q{{ qr.display_order }}</span>
                          </div>
                          <div class="question-content">
                            <div class="q-text">{{ qr.question_text }}</div>
                            <div class="question-meta">
                              <span class="q-weight">Weight: {{ qr.scoring_weight }}</span>
                              <span class="q-max-score">Max Score: {{ getMaxScore(qr.scoring_weight) }}</span>
                            </div>
                          </div>
                        </div>
                        <div class="question-badges">
                          <span class="badge badge-type">{{ qr.question_type }}</span>
                          <span v-if="qr.is_required" class="badge badge-required">Required</span>
                        </div>
                      </div>

                      <!-- Vendor Response -->
                      <div class="vendor-response">
                        <h6>Vendor Response</h6>
                        <div class="response-content">{{ qr.vendor_response || 'No response provided' }}</div>
                        <div v-if="qr.vendor_comment" class="vendor-comment">
                          <strong>Vendor Comment:</strong> {{ qr.vendor_comment }}
                        </div>
                      </div>

                      <!-- All Reviewer Scores -->
                      <div class="reviewer-scores">
                        <div class="reviewer-scores-header">
                          <h6>Reviewer Scores & Decisions</h6>
                          <span class="reviewer-count">
                            {{ qr.reviewer_scores.filter(r => r.score !== null && r.score !== undefined).length }} of {{ qr.reviewer_scores.length }} completed
                          </span>
                        </div>
                        
                        <div v-if="qr.reviewer_scores && qr.reviewer_scores.length > 0" class="reviewer-scores-container">
                          <!-- Individual Reviewer Scores -->
                          <div class="individual-reviewers">
                            <div v-for="(reviewScore, index) in qr.reviewer_scores" :key="`${qr.question_id}-${index}-${reviewScore.stage_id || 'no-stage'}`" 
                                 class="reviewer-card" :class="{ 'pending-reviewer': reviewScore.score === null || reviewScore.score === undefined }">
                              <div class="reviewer-card-header">
                                <div class="reviewer-info">
                                  <div class="reviewer-avatar" :class="{ 'pending-avatar': reviewScore.score === null || reviewScore.score === undefined }">
                                    <span>{{ index + 1 }}</span>
                                  </div>
                                  <div class="reviewer-details">
                                    <div class="reviewer-name">{{ reviewScore.reviewer || 'Unknown Reviewer' }}</div>
                                    <div class="reviewer-role">Reviewer</div>
                                  </div>
                                </div>
                                <div class="reviewer-score-display" v-if="reviewScore.score !== null && reviewScore.score !== undefined">
                                  <span class="score-number">{{ reviewScore.score }}</span>
                                  <span class="score-divider">/</span>
                                  <span class="score-max">{{ getMaxScore(qr.scoring_weight) }}</span>
                                </div>
                                <div class="pending-score-display" v-else>
                                  <span class="pending-text">Pending</span>
                                </div>
                              </div>
                              
                              <div class="reviewer-card-body">
                                <div v-if="reviewScore.score !== null && reviewScore.score !== undefined" class="score-breakdown">
                                  <div class="score-bar">
                                    <div 
                                      class="score-fill" 
                                      :style="{ width: ((reviewScore.score / getMaxScore(qr.scoring_weight)) * 100) + '%' }"
                                      :class="getScoreBarClass(reviewScore.score / getMaxScore(qr.scoring_weight))"
                                    ></div>
                                  </div>
                                </div>
                                
                                <div v-else class="pending-breakdown">
                                  <div class="pending-indicator">
                                    <div class="pending-icon">⏳</div>
                                    <div class="pending-message">Waiting for review</div>
                                  </div>
                                </div>
                                
                                <div v-if="reviewScore.comment" class="reviewer-comment">
                                  <div class="comment-label">Reviewer Comment:</div>
                                  <div class="comment-text">{{ reviewScore.comment }}</div>
                                </div>
                                
                                <div class="reviewer-decision">
                                  <span class="decision-badge" :class="getDecisionClass(reviewScore.decision)">
                                    {{ getDisplayDecision(reviewScore.decision) }}
                                  </span>
                                  <span class="review-date">
                                    {{ reviewScore.completed_at ? formatDate(reviewScore.completed_at) : 'Not started' }}
                                  </span>
                                </div>
                              </div>
                            </div>
                          </div>
                          
                          <!-- Weighted Score Summary -->
                          <div class="average-score-summary">
                            <div class="average-header">
                              <h6>Overall Assessment</h6>
                            </div>
                            <div class="average-content">
                              <div class="average-score-display">
                                <div class="average-number">{{ (qr.average_score || 0).toFixed(1) }}%</div>
                                <div class="average-details">
                                  <div class="average-label">Weighted Score</div>
                                  <div class="average-max">calculated using weightage</div>
                                </div>
                              </div>
                            </div>
                            <div class="consensus-indicator">
                              <span class="consensus-text">
                                {{ getConsensusText(qr.reviewer_scores, qr.average_score) }}
                              </span>
                            </div>
                          </div>
                        </div>
                        
                        <div v-else class="no-scores">
                          <div class="no-scores-icon">📝</div>
                          <div class="no-scores-text">No scores provided by reviewers yet</div>
                        </div>
                      </div>

                      <!-- Final Assignee Scoring -->
                      <div class="final-scoring">
                        <h6>Your Final Score & Decision</h6>
                        <div class="row">
                          <div class="col-8">
                            <div class="form-item">
                              <label>Final Score</label>
                              <div class="final-score-input-container">
                                <input
                                  v-model="finalScores[qr.question_id]"
                                  type="number"
                                  :min="0"
                                  :max="getMaxScore(qr.scoring_weight)"
                                  step="0.1"
                                  placeholder="Enter final score"
                                  class="form-input"
                                  @change="saveIndividualScore(qr.question_id)"
                                />
                                <span class="max-score-label">/ {{ getMaxScore(qr.scoring_weight) }}</span>
                              </div>
                              <div class="score-reference">
                                <span class="reference-label">Weighted Assessment:</span>
                                <span class="reference-score">{{ (qr.average_score || 0).toFixed(1) }}%</span>
                              </div>
                            </div>
                          </div>
                          <div class="col-16">
                            <div class="form-item">
                              <label>Final Comment</label>
                              <textarea
                                v-model="finalComments[qr.question_id]"
                                :rows="2"
                                placeholder="Your final assessment comment..."
                                class="form-textarea"
                                @blur="saveIndividualScore(qr.question_id)"
                              />
                            </div>
                          </div>
                        </div>
                        <div class="score-actions">
                          <button 
                            class="btn btn-primary btn-small"
                            @click="saveIndividualScore(qr.question_id)"
                            :disabled="savingScores[qr.question_id]"
                          >
                            {{ savingScores[qr.question_id] ? 'Saving...' : 'Save Score' }}
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>

                </div>
                <div v-else class="loading-scoring">
                  <div class="skeleton">
                    <div class="skeleton-line"></div>
                    <div class="skeleton-line"></div>
                    <div class="skeleton-line"></div>
                    <div class="skeleton-line"></div>
                    <div class="skeleton-line"></div>
                  </div>
                  <p>Loading parallel scoring data...</p>
                </div>
              </div>

              <!-- Stage Decisions (Collapsible) -->
              <div v-if="request.stages && request.stages.length > 0" class="stages-summary">
                <div class="stages-header-bar">
                  <h4>Stage Decisions ({{ request.stages.length }} stages)</h4>
                  <span class="expand-hint">Click on a stage to view details</span>
                </div>
                <div class="collapse">
                  <div 
                    v-for="stage in (request.stages || [])" 
                    :key="stage.stage_id"
                    class="collapse-item"
                  >
                    <div class="collapse-header" @click="toggleCollapse(stage.stage_id)">
                      <div class="stage-header-content">
                        <span class="stage-title">Stage {{ stage.stage_order }}: {{ stage.stage_name }}</span>
                        <span class="tag tag-small" :class="getStatusType(stage.stage_status)">
                          {{ stage.stage_status }}
                        </span>
                      </div>
                      <span class="collapse-icon">{{ isCollapsed[stage.stage_id] !== false ? '▼' : '▲' }}</span>
                    </div>
                    <div v-if="isCollapsed[stage.stage_id] === false" class="collapse-content">
                    <div class="stage-decision-detail">
                      <div class="row">
                        <div class="col-12">
                          <div class="stage-info">
                            <h5>Stage Information</h5>
                            <p><strong>Order:</strong> {{ stage.stage_order }}</p>
                            <p><strong>Name:</strong> {{ stage.stage_name }}</p>
                            <p><strong>Type:</strong> {{ stage.stage_type }}</p>
                            <p><strong>Status:</strong> 
                              <span class="tag" :class="getStatusType(stage.stage_status)">
                                {{ stage.stage_status }}
                              </span>
                            </p>
                            <p><strong>Mandatory:</strong> {{ stage.is_mandatory ? 'Yes' : 'No' }}</p>
                          </div>
                        </div>
                        <div class="col-12">
                          <div class="assignee-info">
                            <h5>Assigned To</h5>
                            <p><strong>Name:</strong> {{ stage.assigned_user_name }}</p>
                            <p><strong>Role:</strong> {{ stage.assigned_user_role }}</p>
                            <p><strong>Department:</strong> {{ stage.department }}</p>
                            <p><strong>Deadline:</strong> {{ formatDate(stage.deadline_date) }}</p>
                            <p><strong>Started:</strong> {{ formatDate(stage.started_at) }}</p>
                            <p><strong>Completed:</strong> {{ formatDate(stage.completed_at) }}</p>
                          </div>
                        </div>
                      </div>

                      <!-- Stage Description -->
                      <div v-if="stage.stage_description" class="stage-description">
                        <h5>Description</h5>
                        <p>{{ stage.stage_description }}</p>
                      </div>

                      <!-- Regular Decision/Response Data -->
                      <div v-if="stage.response_data && Object.keys(stage.response_data).length > 0" class="decision-data">
                        <h5>Decision Data</h5>
                        <textarea
                          v-model="stage.response_data_display"
                          :rows="3"
                          readonly
                          class="form-textarea"
                        />
                      </div>

                      <!-- Rejection Reason -->
                      <div v-if="stage.rejection_reason" class="rejection-reason">
                        <h5>Rejection Reason</h5>
                        <div class="alert alert-error">
                          <span class="alert-icon">⚠️</span>
                          <span class="alert-message">{{ stage.rejection_reason }}</span>
                        </div>
                      </div>

                      <!-- Decision Summary -->
                      <div class="decision-summary">
                        <h5>Decision Summary</h5>
                        <div v-if="stage.stage_status === 'APPROVED'" class="approved-decision">
                          <span class="icon">✅</span>
                          <span style="color: green; margin-left: 8px;">
                            <strong>{{ stage.assigned_user_name }}</strong> approved this stage
                            {{ stage.completed_at ? `on ${formatDate(stage.completed_at)}` : '' }}
                          </span>
                        </div>
                        <div v-else-if="stage.stage_status === 'REJECTED'" class="rejected-decision">
                          <span class="icon">❌</span>
                          <span style="color: red; margin-left: 8px;">
                            <strong>{{ stage.assigned_user_name }}</strong> rejected this stage
                            {{ stage.completed_at ? `on ${formatDate(stage.completed_at)}` : '' }}
                          </span>
                        </div>
                        <div v-else-if="stage.stage_status === 'IN_PROGRESS'" class="in-progress-decision">
                          <span class="icon">⏳</span>
                          <span style="color: orange; margin-left: 8px;">
                            <strong>{{ stage.assigned_user_name }}</strong> is reviewing this stage
                          </span>
                        </div>
                        <div v-else class="pending-decision">
                          <span class="icon">⏰</span>
                          <span style="color: gray; margin-left: 8px;">
                            Waiting for <strong>{{ stage.assigned_user_name }}</strong> to review
                          </span>
                        </div>
                      </div>
                    </div>
                    </div>
                  </div>
                </div>
              </div>


              <!-- Admin Rejection Handling Options (Only for MULTI_LEVEL workflows) -->
              <div v-if="hasRejectedStages(request) && request.workflow_type === 'MULTI_LEVEL'" class="rejection-handling">
                <div class="divider">
                  <h3>Admin Rejection Handling</h3>
                </div>
                <div class="alert alert-warning">
                  <span class="alert-icon">⚠️</span>
                  <div class="alert-content">
                    <div class="alert-title">This request has rejected stages - Admin Controls</div>
                    <div class="alert-description">As an admin, you can restart the workflow from the rejected stage, restart from a specific stage, or finally reject the request.</div>
                  </div>
                </div>
                
                <form class="form" style="margin-top: 20px;">
                  <div class="form-item">
                    <label>Admin Action</label>
                    <div class="radio-group">
                      <label class="radio-item">
                        <input type="radio" v-model="adminRejectionForm.action" value="RESTART_FROM_REJECTED" />
                        <span>Restart from Rejected Stage</span>
                      </label>
                      <label class="radio-item">
                        <input type="radio" v-model="adminRejectionForm.action" value="RESTART_FROM_STAGE" />
                        <span>Restart from Specific Stage</span>
                      </label>
                      <label class="radio-item">
                        <input type="radio" v-model="adminRejectionForm.action" value="FINAL_REJECT" />
                        <span>Final Rejection</span>
                      </label>
                    </div>
                  </div>

                  <!-- Stage Selection for RESTART_FROM_STAGE -->
                  <div v-if="adminRejectionForm.action === 'RESTART_FROM_STAGE'">
                    <div class="form-item">
                      <label>Select Stage</label>
                      <select v-model="adminRejectionForm.stage_order" class="form-select">
                        <option value="">Select stage to restart from</option>
                        <option
                          v-for="stage in (request.stages || [])"
                          :key="stage.stage_order"
                          :value="stage.stage_order"
                        >
                          Stage {{ stage.stage_order }}: {{ stage.stage_name }}
                        </option>
                      </select>
                    </div>
                  </div>

                  <!-- Admin Comments -->
                  <div class="form-item">
                    <label>Admin Comments</label>
                    <textarea
                      v-model="adminRejectionForm.admin_comments"
                      :rows="3"
                      placeholder="Provide comments for this admin action..."
                      class="form-textarea"
                    />
                  </div>

                  <!-- Version History Display -->
                  <div v-if="versionHistory && versionHistory[request.approval_id] && versionHistory[request.approval_id].length > 0" class="version-history-section-enhanced admin-version-history">
                    <div class="form-item">
                      <label>📋 Version History ({{ versionHistory[request.approval_id].length }} versions)</label>
                      <div class="version-info-banner">
                        <span class="info-icon">ℹ️</span>
                        <span>Review all versions before making admin decision</span>
                      </div>
                      <div class="version-history-content">
                        <div class="versions-list-enhanced">
                          <div v-for="version in (versionHistory[request.approval_id] || [])" :key="version.version_id" class="version-item-enhanced">
                            <div class="version-header-enhanced">
                              <div class="version-title-group">
                                <span class="version-title">v{{ version.version_number }} - {{ version.version_label }}</span>
                                <span class="version-id">ID: {{ version.version_id }}</span>
                              </div>
                              <div class="version-badges">
                                <span class="tag" :class="getVersionTypeColor(version.version_type)">
                                  {{ version.version_type }}
                                </span>
                                <span v-if="version.is_current" class="tag tag-success">Current</span>
                                <span v-if="version.is_approved" class="tag tag-success">Approved</span>
                                <span v-else-if="version.is_approved === false" class="tag tag-warning">Pending</span>
                              </div>
                            </div>
                            <div class="version-details-enhanced">
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
                                <pre class="json-pre">{{ JSON.stringify(version.json_payload, null, 2) }}</pre>
                              </details>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div class="form-item">
                    <button 
                      class="btn btn-primary"
                      @click="handleAdminRejection(request)"
                      :disabled="submitting"
                    >
                      {{ submitting ? 'Processing...' : getAdminActionLabel(adminRejectionForm.action) }}
                    </button>
                  </div>
                </form>
              </div>

              <!-- Final Decision for MULTI_PERSON Workflows -->
              <div v-if="request.workflow_type === 'MULTI_PERSON' && allStagesCompleted(request)" class="final-decision">
                <!-- Show different content based on whether request is already completed -->
                <div v-if="request.overall_status === 'APPROVED' || request.overall_status === 'REJECTED'">
                  <!-- Request already completed - show frozen details -->
                  <div class="divider">
                    <h3>Final Decision Completed</h3>
                  </div>
                  <div class="alert" :class="request.overall_status === 'APPROVED' ? 'alert-success' : 'alert-error'">
                    <span class="alert-icon">{{ request.overall_status === 'APPROVED' ? '✅' : '❌' }}</span>
                    <div class="alert-content">
                      <div class="alert-title">Request has been {{ request.overall_status.toLowerCase() }}</div>
                      <div class="alert-description">Final decision was made and the workflow is now closed.</div>
                    </div>
                  </div>
                  
                  <div class="stages-summary-final">
                    <h4>Final Stage Decisions Summary:</h4>
                    <table class="table" style="width: 100%">
                      <thead>
                        <tr>
                          <th>Stage</th>
                          <th>Reviewer</th>
                          <th>Decision</th>
                          <th>Completed</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr v-for="stage in (request.stages || [])" :key="stage.stage_id">
                          <td>{{ stage.stage_name }}</td>
                          <td>{{ stage.assigned_user_name }}</td>
                          <td>
                            <span class="tag" :class="getStatusType(stage.stage_status)">
                              {{ stage.stage_status }}
                            </span>
                          </td>
                          <td>{{ formatDate(stage.completed_at) }}</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>

                  <div class="final-decision-summary">
                    <h4>Final Decision Details:</h4>
                    <div class="row">
                      <div class="col-12">
                        <p><strong>Final Status:</strong> 
                          <span class="tag" :class="getStatusType(request.overall_status)">
                            {{ request.overall_status }}
                          </span>
                        </p>
                        <p><strong>Completed:</strong> {{ formatDate(request.completion_date) }}</p>
                      </div>
                      <div class="col-12">
                        <p><strong>Workflow Type:</strong> {{ request.workflow_type }}</p>
                        <p><strong>Total Stages:</strong> {{ request.stages.length }}</p>
                      </div>
                    </div>
                    
                    <!-- Vendor Migration Status for Final Vendor Approvals -->
                    <div v-if="isFinalVendorApproval(request) && request.overall_status === 'APPROVED'" class="vendor-migration-status">
                      <div class="divider">
                        <h3>Vendor Migration Status</h3>
                      </div>
                      <div class="migration-success">
                        <span class="icon" style="color: green; font-size: 20px;">✅</span>
                        <div class="migration-details">
                          <h5>Vendor Successfully Migrated to Main System</h5>
                          <p>The vendor data has been automatically migrated from the temporary registration to the main vendor management system.</p>
                          <div class="migration-info">
                            <p><strong>Vendor:</strong> {{ getVendorData(request)?.company_name || 'Unknown' }}</p>
                            <p><strong>Status:</strong> <span class="tag tag-success">ONBOARDED</span></p>
                            <p><strong>Migration Date:</strong> {{ formatDate(request.completion_date) }}</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div v-else>
                  <!-- Request pending final decision - show active form -->
                  <div class="divider">
                    <h3>Final Decision Required</h3>
                  </div>
                  <div class="alert alert-info">
                    <span class="alert-icon">ℹ️</span>
                    <div class="alert-content">
                      <div class="alert-title">All stages completed - Final decision required</div>
                      <div class="alert-description">All reviewers have completed their stages. You can now make the final decision to approve or reject this request.</div>
                    </div>
                  </div>
                  
                  <div class="stages-summary-final">
                    <h4>Stage Decisions Summary:</h4>
                    <table class="table" style="width: 100%">
                      <thead>
                        <tr>
                          <th>Stage</th>
                          <th>Reviewer</th>
                          <th>Decision</th>
                          <th>Completed</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr v-for="stage in (request.stages || [])" :key="stage.stage_id">
                          <td>{{ stage.stage_name }}</td>
                          <td>{{ stage.assigned_user_name }}</td>
                          <td>
                            <span class="tag" :class="getStatusType(stage.stage_status)">
                              {{ stage.stage_status }}
                            </span>
                          </td>
                          <td>{{ formatDate(stage.completed_at) }}</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>

                  <form class="form" style="margin-top: 20px;">
                     <div class="form-item">
                      <label>Final Decision</label>
                      <div class="radio-group">
                         <label class="radio-item">
                           <input type="radio" v-model="finalDecisionForm.decision_type" value="FINAL_APPROVE" />
                           <span>Approve Request</span>
                         </label>
                         <label class="radio-item">
                           <input type="radio" v-model="finalDecisionForm.decision_type" value="FINAL_REJECT" />
                           <span>Reject Request</span>
                         </label>
                       </div>
                     </div>

                    <!-- Overall Score Override Section -->
                    <div v-if="parallelScoringData && parallelScoringData.assignment" class="form-item">
                      <label>Overall Score</label>
                      <div class="overall-score-input-section">
                        <div class="current-score-info">
                          <span class="score-label">Calculated Score:</span>
                          <span class="current-score" :class="getScoreClass(parallelScoringData.assignment.overall_score || 0)">
                            {{ (parallelScoringData.assignment.overall_score || 0).toFixed(1) }}
                          </span>
                        </div>
                        <div class="score-override-section">
                          <label class="checkbox-item">
                            <input type="checkbox" v-model="finalDecisionForm.override_score" @change="handleScoreOverrideChange" />
                            <span>Override calculated score</span>
                          </label>
                          <div v-if="finalDecisionForm.override_score" class="override-input">
                            <input
                              v-model="finalDecisionForm.custom_overall_score"
                              type="number"
                              :min="0"
                              :max="100"
                              step="0.1"
                              placeholder="Enter custom score"
                              class="form-input"
                              style="width: 140px; margin-left: 10px;"
                            />
                            <span class="score-unit">%</span>
                            <button 
                              class="btn btn-info btn-small"
                              @click="resetToCalculatedScore"
                              style="margin-left: 10px;"
                            >
                              Reset to Calculated
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div class="form-item">
                      <label>Decision Reason</label>
                       <textarea
                        v-model="finalDecisionForm.decision_reason"
                         :rows="3"
                        placeholder="Provide reason for your final decision..."
                        class="form-textarea"
                     />
                   </div>

                   <div class="form-item">
                     <button 
                       class="btn btn-primary"
                        @click="handleRequesterFinalDecision(request)"
                       :disabled="submitting"
                     >
                       {{ submitting ? 'Submitting...' : 'Submit Final Decision' }}
                     </button>
                   </div>
                 </form>
                 </div>
               </div>
            </div>
          </div>
        </div>
      </div>

      <!-- No Data Messages -->
      <div v-else-if="selectedRequesterId && requesterRequests.length === 0" class="no-data">
        <div class="empty-state">
          <div class="empty-icon">📋</div>
          <h3>No requests found for this requester</h3>
          <p>This requester doesn't have any approval requests at this time.</p>
        </div>
      </div>

      <!-- Select Requester Message -->
      <div v-else class="select-requester">
        <div class="empty-state">
          <div class="empty-icon">👤</div>
          <h3>Please select a requester ID to view their requests and stages</h3>
          <p>Choose a requester ID from the dropdown above to see their approval requests and associated stages.</p>
        </div>
      </div>
    </div>
    
    <!-- Risk Generation Progress Popup -->
    <div v-if="showRiskGenerationPopup" class="risk-generation-overlay">
      <div class="risk-generation-modal">
        <div class="risk-modal-header">
          <h3>{{ riskGenerationStatus.status === 'completed' ? '✅ Risk Analysis Complete' : '⚙️ Generating Risk Analysis' }}</h3>
        </div>
        <div class="risk-modal-body">
          <div v-if="riskGenerationStatus.status === 'in_progress'" class="progress-container">
            <div class="spinner-large"></div>
            <p class="progress-message">{{ riskGenerationStatus.message }}</p>
            <p class="progress-detail">This may take 30-60 seconds. Please wait...</p>
          </div>
          <div v-else-if="riskGenerationStatus.status === 'completed'" class="completion-container">
            <div class="success-icon">✓</div>
            <p class="success-message">{{ riskGenerationStatus.message }}</p>
            <p class="success-detail">
              <strong>{{ riskGenerationStatus.risk_count }}</strong> risks have been identified and documented.
            </p>
          </div>
          <div v-else class="error-container">
            <p class="error-message">{{ riskGenerationStatus.message }}</p>
          </div>
        </div>
        <div class="risk-modal-footer">
          <button 
            v-if="riskGenerationStatus.status === 'completed'" 
            class="btn btn-primary"
            @click="closeRiskGenerationPopup"
          >
            Continue
          </button>
          <button 
            v-else 
            class="btn btn-info"
            @click="closeRiskGenerationPopup"
          >
            Run in Background
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- Popup Modal -->
  <PopupModal />
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import api from '@/utils/api'
import { getCurrentUserId } from '@/utils/session'
import PopupModal from '@/popup/PopupModal.vue'
import { PopupService } from '@/popup/popupService'
import { useNotifications } from '@/composables/useNotifications'
import notificationService from '@/services/notificationService'
import loggingService from '@/services/loggingService'
import { ElMessage } from 'element-plus'

export default {
  components: {
    PopupModal
  },
  name: 'AssigneeDecision',
  setup() {
    const { showSuccess, showError, showWarning, showInfo } = useNotifications()
    
    const selectedRequesterId = ref('')
    const selectedApprovalId = ref('')
    const requesters = ref([])
    const requesterRequests = ref([])
    const versionHistory = ref({}) // approval_id -> versions[]
    const submitting = ref(false)
    const statusChanging = ref(false)
    const parallelScoringData = ref(null)
    const finalScores = ref({})
    const finalComments = ref({})
    const submittingFinalDecision = ref(false)
    const previewOverallScore = ref(null)
    const savingScores = ref({})
    const calculatedOverallScore = ref(0)
    const isCollapsed = ref({})
    const showVersionHistory = ref(false)
    const showRiskGenerationPopup = ref(false)
    const riskGenerationStatus = ref({
      status: 'pending',
      message: '',
      risk_count: 0
    })
    const riskGenerationInterval = ref(null)
    const decisionForm = reactive({
      decision_type: '',
      decision_reason: '',
      revised_payload: '',
      additional_notes: ''
    })
    const rejectionForm = reactive({
      action_type: '',
      new_status: '',
      revision_reason: '',
      revised_data: ''
    })
    const adminRejectionForm = reactive({
      action: '',
      stage_order: null,
      admin_comments: ''
      // admin_id and admin_name removed - obtained from authenticated user in backend
    })
    const finalDecisionForm = reactive({
      decision_type: '',
      decision_reason: '',
      override_score: false,
      custom_overall_score: 0
    })
    const assigneeDecisionForm = reactive({
      decision: '',
      comments: ''
    })

    onMounted(async () => {
      await loggingService.logPageView('Vendor', 'Assignee Decision')
      await fetchRequesters()
      try {
        const url = new URL(window.location.href)
        const rq = url.searchParams.get('requester_id')
        const aid = url.searchParams.get('approval_id')
        if (aid) {
          // If approval_id is provided, set it and fetch that specific request
          selectedApprovalId.value = aid
          await fetchSingleRequest(aid)
        } else if (rq) {
          selectedRequesterId.value = rq
          await fetchRequesterData()
        }
      } catch {}
    })

    const fetchRequesters = async () => {
      try {
        const response = await api.get('/vendor-approval/users/')
        requesters.value = (response.data || []).map(user => ({
          id: user.id || user.UserId,
          requester_id: user.UserName || user.user_name || user.first_name
        }))

        if (!selectedRequesterId.value && requesters.value.length > 0 && !selectedApprovalId.value) {
          selectedRequesterId.value = requesters.value[0].id
          await fetchRequesterData()
        }
      } catch (error) {
        console.error('Error fetching requesters:', error)
        ElMessage.error('Failed to fetch requesters')
      }
    }

    const fetchSingleRequest = async (approvalId) => {
      try {
        const response = await api.get(`/vendor-approval/requests/${approvalId}/`)
        const request = {
          ...response.data,
          request_data_display: response.data.request_data ? JSON.stringify(response.data.request_data, null, 2) : 'No data',
          stages: response.data.stages.map(stage => ({
            ...stage,
            response_data_display: stage.response_data ? JSON.stringify(stage.response_data, null, 2) : 'No data'
          }))
        }
        requesterRequests.value = [request]
        selectedRequesterId.value = request.requester_id
        
        // Fetch version history for this request if applicable
        const shouldFetchVersionHistory = 
          request.workflow_type === 'MULTI_LEVEL' || 
          isFinalVendorApproval(request) ||
          isParallelResponseApproval(request) ||
          request.workflow_type === 'MULTI_PERSON'
        
        if (shouldFetchVersionHistory) {
          try {
            const vRes = await api.get(`/vendor-approval/requests/${approvalId}/versions/`)
            versionHistory.value[approvalId] = vRes.data || []
            console.log(`✓ Version history loaded for single request ${approvalId}: ${versionHistory.value[approvalId].length} versions`)
          } catch (vError) {
            console.error(`Failed to load version history for approval ${approvalId}:`, vError)
            versionHistory.value[approvalId] = []
          }
        }
        
        // Check if this should load parallel scoring data
        if (isParallelResponseApproval(request)) {
          await loadParallelScoringData(approvalId)
        }
      } catch (error) {
        console.error('Error fetching single request:', error)
        ElMessage.error('Failed to fetch request data')
      }
    }

    const fetchRequesterData = async () => {
      if (!selectedRequesterId.value) return
      
      try {
        // Fetch requests for the selected requester
        const response = await api.get(`/vendor-approval/requests/by-requester/`, {
          params: { requester_id: selectedRequesterId.value }
        })
        
        // The by-requester endpoint returns a simpler structure
        const requests = (response.data || []).map(request => ({
          ...request,
          request_data: request.request_data || {},
          request_data_display: request.request_data ? JSON.stringify(request.request_data, null, 2) : 'No data',
          stages: [] // This endpoint doesn't include stages, so we'll need to fetch them separately
        }))

        // For detailed view, we should use the single request endpoint for each request
        // But for the list view, this simplified data is sufficient
        requesterRequests.value = requests
        
        // Fetch version history for multi-level workflows and final vendor approval
        for (const request of requests) {
          // Fetch version history for MULTI_LEVEL workflows or Final Vendor Approval
          const shouldFetchVersionHistory = 
            request.workflow_type === 'MULTI_LEVEL' || 
            isFinalVendorApproval(request) ||
            request.workflow_type === 'MULTI_PERSON' // Also support multi-person workflows
          
          if (shouldFetchVersionHistory) {
            try {
              const vRes = await api.get(`/api/v1/vendor-approval/requests/${request.approval_id}/versions/`)
              versionHistory.value[request.approval_id] = vRes.data || []
              console.log(`✓ Version history loaded for approval ${request.approval_id}: ${versionHistory.value[request.approval_id].length} versions`)
            } catch (e) {
              console.error(`Failed to load version history for approval ${request.approval_id}:`, e)
              versionHistory.value[request.approval_id] = []
            }
          }
        }
      } catch (error) {
        console.error('Error fetching requester data:', error)
        ElMessage.error('Failed to fetch requester data')
      }
    }

    const hasRejectedStages = (request) => {
      return request.stages.some(stage => stage.stage_status === 'REJECTED')
    }

    const allStagesCompleted = (request) => {
      return request.stages.every(stage => 
        stage.stage_status === 'APPROVED' || stage.stage_status === 'REJECTED'
      )
    }

    const formatRevisedPayload = () => {
      try {
        const parsed = JSON.parse(decisionForm.revised_payload)
        decisionForm.revised_payload = JSON.stringify(parsed, null, 2)
        ElMessage.success('JSON formatted successfully')
      } catch (e) {
        ElMessage.error('Invalid JSON format')
      }
    }

    const validateRevisedPayload = () => {
      try {
        JSON.parse(decisionForm.revised_payload)
        ElMessage.success('JSON is valid')
      } catch (e) {
        ElMessage.error('Invalid JSON format')
      }
    }

    const formatRevisedData = () => {
      try {
        const parsed = JSON.parse(rejectionForm.revised_data)
        rejectionForm.revised_data = JSON.stringify(parsed, null, 2)
        ElMessage.success('JSON formatted successfully')
      } catch (e) {
        ElMessage.error('Invalid JSON format')
      }
    }

    const validateRevisedData = () => {
      try {
        JSON.parse(rejectionForm.revised_data)
        ElMessage.success('JSON is valid')
      } catch (e) {
        ElMessage.error('Invalid JSON format')
      }
    }

    const handleRejectionRevision = async (request) => {
      if (!rejectionForm.action_type) {
        ElMessage.warning('Please select an action type')
        return
      }

      if (rejectionForm.action_type === 'CHANGE_STATUS' && !rejectionForm.new_status) {
        ElMessage.warning('Please select a new status')
        return
      }

      if (rejectionForm.action_type === 'SEND_REVISION') {
        if (!rejectionForm.revision_reason) {
          ElMessage.warning('Please provide a revision reason')
          return
        }
        if (!rejectionForm.revised_data) {
          ElMessage.warning('Please provide revised data')
          return
        }
        try {
          JSON.parse(rejectionForm.revised_data)
        } catch (e) {
          ElMessage.error('Invalid JSON format in revised data')
          return
        }
      }

      try {
        submitting.value = true
        
        const requestData = {
          action_type: rejectionForm.action_type,
          new_status: rejectionForm.new_status,
          revised_data: rejectionForm.action_type === 'SEND_REVISION' ? JSON.parse(rejectionForm.revised_data) : {},
          revision_reason: rejectionForm.revision_reason,
          assignee_id: selectedRequesterId.value,
          assignee_name: requesters.value.find(r => r.id === selectedRequesterId.value)?.requester_id || 'Unknown'
        }

        await api.post(`/api/approval/handle-rejection-revision/${request.approval_id}/`, requestData)
        
        ElMessage.success('Action completed successfully')
        
        // Reset form and refresh requests
        Object.assign(rejectionForm, {
          action_type: '',
          new_status: '',
          revision_reason: '',
          revised_data: ''
        })
        
        await fetchRequesterData()
        
      } catch (error) {
        console.error('Error handling rejection revision:', error)
        ElMessage.error(error.response?.data?.error || 'Failed to handle rejection revision')
      } finally {
        submitting.value = false
      }
    }

    const handleScoreOverrideChange = (override) => {
      if (override && parallelScoringData.value && parallelScoringData.value.assignment) {
        // Initialize custom score with current calculated score
        finalDecisionForm.custom_overall_score = parallelScoringData.value.assignment.overall_score || 0
      }
    }

    const resetToCalculatedScore = () => {
      if (parallelScoringData.value && parallelScoringData.value.assignment) {
        finalDecisionForm.custom_overall_score = parallelScoringData.value.assignment.overall_score || 0
        console.log('Score reset to calculated value')
      }
    }

    const checkRiskGenerationStatus = async (approvalId) => {
      try {
        const response = await api.get(`/vendor-approval/risk-generation-status/${approvalId}/`)
        
        riskGenerationStatus.value = {
          status: response.data.status,
          message: response.data.message,
          risk_count: response.data.risk_count || 0
        }
        
        // If completed, stop polling and update lifecycle
        if (response.data.status === 'completed') {
          if (riskGenerationInterval.value) {
            clearInterval(riskGenerationInterval.value)
            riskGenerationInterval.value = null
          }
          
          console.log('✅ Risk generation completed, lifecycle should be updated by backend')
        }
        
        return response.data.status
      } catch (error) {
        console.error('Error checking risk generation status:', error)
        return 'error'
      }
    }

    const startRiskGenerationTracking = (approvalId) => {
      console.log('Starting risk generation tracking for approval:', approvalId)
      
      // Show the popup
      showRiskGenerationPopup.value = true
      riskGenerationStatus.value = {
        status: 'in_progress',
        message: 'Analyzing vendor responses and generating risk assessment...',
        risk_count: 0
      }
      
      // Start polling for status updates every 3 seconds
      riskGenerationInterval.value = setInterval(async () => {
        const status = await checkRiskGenerationStatus(approvalId)
        if (status === 'completed') {
          // Keep popup open to show completion message
          console.log('Risk generation completed')
        }
      }, 3000)
    }

    const closeRiskGenerationPopup = () => {
      showRiskGenerationPopup.value = false
      if (riskGenerationInterval.value) {
        clearInterval(riskGenerationInterval.value)
        riskGenerationInterval.value = null
      }
    }

    const handleRequesterFinalDecision = async (request) => {
      console.log('=== SUBMIT BUTTON CLICKED ===')
      console.log('Request:', request)
      console.log('Form data:', finalDecisionForm)
      
      if (!finalDecisionForm.decision_type) {
        console.error('Validation failed: No decision type selected')
        PopupService.warning('Please select a decision type (Approve or Reject)', 'Missing Decision Type')
        return
      }

      if (!finalDecisionForm.decision_reason) {
        console.error('Validation failed: No decision reason provided')
        PopupService.warning('Please provide a decision reason', 'Missing Reason')
        return
      }

      // Validate custom score if override is enabled
      if (finalDecisionForm.override_score) {
        if (finalDecisionForm.custom_overall_score === null || finalDecisionForm.custom_overall_score === undefined) {
          console.error('Validation failed: Invalid custom score')
          PopupService.warning('Please enter a valid custom overall score', 'Invalid Score')
          return
        }
        if (finalDecisionForm.custom_overall_score < 0 || finalDecisionForm.custom_overall_score > 100) {
          console.error('Validation failed: Score out of range')
          PopupService.warning('Overall score must be between 0 and 100', 'Score Out of Range')
          return
        }
      }

      try {
        submitting.value = true
        console.log('Starting submission process...')
        
        const decision = finalDecisionForm.decision_type === 'FINAL_APPROVE' ? 'APPROVE' : 'REJECT'
        const requestData = {
          decision: decision,
          reason: finalDecisionForm.decision_reason
        }

        console.log('Prepared request data:', requestData)

        // Include overall score override if enabled
        if (finalDecisionForm.override_score && parallelScoringData.value && parallelScoringData.value.assignment) {
          requestData.overall_score_override = {
            enabled: true,
            custom_score: finalDecisionForm.custom_overall_score,
            original_score: parallelScoringData.value.assignment.overall_score || 0,
            override_reason: finalDecisionForm.decision_reason
          }
          console.log('Added score override:', requestData.overall_score_override)
        }

        const apiUrl = `/vendor-approval/requests/${request.approval_id}/requester-final-decision/`
        console.log('Making API call to:', apiUrl)
        console.log('Request data:', requestData)
        
        const response = await api.post(apiUrl, requestData)
        
        console.log('API response received:', response)
        console.log('Response status:', response.status)
        console.log('Response data:', response.data)
        
        // Check if this is a response approval and if risk generation was started
        if (isParallelResponseApproval(request) && decision === 'APPROVE') {
          console.log('Response approval approved - starting risk generation tracking')
          startRiskGenerationTracking(request.approval_id)
        }
        
        // Check if this was a final vendor approval and handle migration feedback
        if (isFinalVendorApproval(request) && finalDecisionForm.decision_type === 'FINAL_APPROVE') {
          const migrationInfo = response.data.vendor_migration
          if (migrationInfo) {
            if (migrationInfo.success) {
              console.log('SUCCESS: Vendor migration completed')
              PopupService.success(`Final decision submitted successfully! Vendor migrated to main system: ${migrationInfo.company_name} (ID: ${migrationInfo.vendor_id})`, 'Success')
              console.log('Vendor migration details:', {
                vendor_id: migrationInfo.vendor_id,
                vendor_code: migrationInfo.vendor_code,
                company_name: migrationInfo.company_name,
                contacts_migrated: migrationInfo.contacts_migrated,
                documents_migrated: migrationInfo.documents_migrated
              })
            } else {
              console.error('Vendor migration failed:', migrationInfo.error)
              PopupService.warning(`Final decision submitted, but vendor migration failed: ${migrationInfo.error}`, 'Migration Failed')
            }
          } else {
            console.log('SUCCESS: Final decision submitted (no migration)')
            PopupService.success('Final decision submitted successfully', 'Success')
          }
        } else {
          console.log('SUCCESS: Final decision submitted')
          PopupService.success('Final decision submitted successfully', 'Success')
        }
        
        // Reset form and refresh requests
        console.log('Resetting form and refreshing data...')
        Object.assign(finalDecisionForm, {
          decision_type: '',
          decision_reason: '',
          override_score: false,
          custom_overall_score: 0
        })
        
        // Refresh the data to show updated status
        await fetchRequesterData()
        
        // If we're viewing a single request, refresh it to show updated status
        if (selectedApprovalId.value) {
          console.log('Refreshing single request data...')
          await fetchSingleRequest(selectedApprovalId.value)
        }
        
        console.log('Form reset and data refreshed successfully')
        
      } catch (error) {
        console.error('=== SUBMISSION ERROR ===')
        console.error('Error details:', error)
        console.error('Error message:', error.message)
        console.error('Error response:', error.response)
        console.error('Error status:', error.response?.status)
        console.error('Error data:', error.response?.data)
        
        let errorMessage = 'Failed to submit final decision'
        
        if (error.response?.data?.error) {
          errorMessage = error.response.data.error
        } else if (error.response?.status === 400) {
          errorMessage = 'Invalid request data. Please check your input.'
        } else if (error.response?.status === 404) {
          errorMessage = 'Approval request not found.'
        } else if (error.response?.status === 500) {
          errorMessage = 'Server error. Please try again later.'
        } else if (error.message) {
          errorMessage = `Error: ${error.message}`
        }
        
        PopupService.error(`SUBMISSION FAILED: ${errorMessage}`, 'Submission Failed')
        console.error('Final error message:', errorMessage)
        
      } finally {
        submitting.value = false
        console.log('Submission process completed')
      }
    }

    const handleAdminRejection = async (request) => {
      if (!adminRejectionForm.action) {
        PopupService.warning('Please select an admin action', 'Missing Action')
        return
      }

      if (adminRejectionForm.action === 'RESTART_FROM_STAGE' && !adminRejectionForm.stage_order) {
        PopupService.warning('Please select a stage to restart from', 'Missing Stage')
        return
      }

      try {
        submitting.value = true
        
        const requestData = {
          action: adminRejectionForm.action,
          stage_order: adminRejectionForm.stage_order,
          admin_comments: adminRejectionForm.admin_comments
          // admin_id and admin_name are now obtained from request.user in backend
        }

        const response = await api.post(`/vendor-approval/requests/${request.approval_id}/admin-handle-rejection/`, requestData)
        
        console.log('✅ Admin action completed successfully:', response.data)
        PopupService.success('Admin action completed successfully', 'Success')
        
        // Refresh version history immediately to show the new version
        try {
          const vRes = await api.get(`/api/v1/vendor-approval/requests/${request.approval_id}/versions/`)
          versionHistory.value[request.approval_id] = vRes.data || []
          console.log(`✓ Version history refreshed for approval ${request.approval_id}: ${versionHistory.value[request.approval_id].length} versions`)
        } catch (vError) {
          console.error('Failed to refresh version history:', vError)
        }
        
        // Reset form and refresh requests
        Object.assign(adminRejectionForm, {
          action: '',
          stage_order: null,
          admin_comments: ''
        })
        
        await fetchRequesterData()
        
      } catch (error) {
        console.error('Error handling admin rejection:', error)
        PopupService.error(error.response?.data?.error || 'Failed to handle admin rejection', 'Admin Action Failed')
      } finally {
        submitting.value = false
      }
    }

    const getAdminActionLabel = (action) => {
      const labelMap = {
        'RESTART_FROM_REJECTED': 'Restart from Rejected Stage',
        'RESTART_FROM_STAGE': 'Restart from Selected Stage',
        'FINAL_REJECT': 'Final Rejection'
      }
      return labelMap[action] || 'Execute Action'
    }

    const getVersionTypeColor = (versionType) => {
      const colorMap = {
        'INITIAL': 'info',
        'REVISION': 'warning',
        'CONSOLIDATION': 'primary',
        'FINAL': 'success'
      }
      return colorMap[versionType] || 'default'
    }

    const getStatusType = (status) => {
      const statusMap = {
        'DRAFT': 'info',
        'PENDING': 'warning',
        'IN_PROGRESS': 'warning',
        'APPROVED': 'success',
        'REJECTED': 'danger',
        'CANCELLED': 'info',
        'EXPIRED': 'danger'
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

    // Final Vendor Approval Functions
    const isFinalVendorApproval = (request) => {
      if (!request) return false
      const requestData = request.request_data || {}
      const rd = requestData.request_data || requestData
      return String(rd.approval_type || '').toLowerCase() === 'final_vendor_approval'
    }

    const getVendorData = (request) => {
      const requestData = request.request_data || {}
      const rd = requestData.request_data || requestData
      return rd.vendor_data || null
    }

    const getRiskSummary = (request) => {
      const requestData = request.request_data || {}
      const rd = requestData.request_data || requestData
      return rd.risk_summary || null
    }

    const getInternalRisks = (request) => {
      const requestData = request.request_data || {}
      const rd = requestData.request_data || requestData
      return rd.internal_risks || rd.tprm_risks || []
    }

    const getExternalRisks = (request) => {
      const requestData = request.request_data || {}
      const rd = requestData.request_data || requestData
      return rd.external_risks || rd.screening_risks || []
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

    // Team Approval Response Scoring Functions
    const isParallelResponseApproval = (request) => {
      if (!request) return false
      try {
        // Check if this is a team approval workflow and response approval
        const url = new URL(window.location.href)
        const flowType = url.searchParams.get('flow_type')
        
        if (flowType !== 'Parallel') return false
        
        // Check if request data indicates response approval
        const requestData = request.request_data || {}
        const rd = requestData.request_data || requestData
        return String(rd.approval_type || '').toLowerCase() === 'response_approval'
      } catch {
        return false
      }
    }

    const loadParallelScoringData = async (approvalId) => {
      try {
        const response = await api.get(`/vendor-approval/parallel-scoring/${approvalId}/`)
        if (response.data.success) {
          parallelScoringData.value = response.data
          
          // Debug: Log the data structure to understand what we're getting
          console.log('Parallel scoring data loaded:', response.data)
          console.log('Questions and responses:', response.data.questions_and_responses)
          console.log('Stages data:', response.data.stages)
          
          // Initialize final scores with average scores (overall assessment)
          response.data.questions_and_responses.forEach(qr => {
            // Convert average score percentage (0-100) back to actual score range (0 to max_score)
            if (qr.average_score !== null && qr.average_score !== undefined) {
              const maxScore = getMaxScore(qr.scoring_weight)
              // Convert percentage back to actual score: (percentage / 100) * max_score
              const actualScore = (parseFloat(qr.average_score) / 100) * maxScore
              finalScores.value[qr.question_id] = actualScore
            } else {
              finalScores.value[qr.question_id] = 0
            }
            
            if (qr.final_reviewer_comment) {
              finalComments.value[qr.question_id] = qr.final_reviewer_comment
            }
            
            // Debug: Log reviewer scores for each question
            console.log(`Question ${qr.question_id} reviewer scores:`, qr.reviewer_scores)
            console.log(`Question ${qr.question_id} average score:`, qr.average_score)
            console.log(`Question ${qr.question_id} final score initialized:`, finalScores.value[qr.question_id])
          })
          
          // Calculate initial overall score
          calculateOverallScore()
          
          // Debug: Log the initialized final scores
          console.log('Initialized final scores:', finalScores.value)
          console.log('Initialized final comments:', finalComments.value)
        }
      } catch (error) {
        console.error('Error loading parallel scoring data:', error)
        ElMessage.error('Failed to load scoring data')
      }
    }

    const getMaxScore = (scoringWeight) => {
      return parseFloat(scoringWeight) * 10 || 10
    }

    const calculatePreviewScore = () => {
      if (!parallelScoringData.value) return
      
      let totalWeightedScore = 0
      let totalWeightedMax = 0
      
      parallelScoringData.value.questions_and_responses.forEach(qr => {
        const finalScore = finalScores.value[qr.question_id] || 0
        const weight = qr.scoring_weight || 1
        const maxScore = getMaxScore(weight)
        
        totalWeightedScore += finalScore * weight
        totalWeightedMax += maxScore * weight
      })
      
      if (totalWeightedMax > 0) {
        previewOverallScore.value = (totalWeightedScore / totalWeightedMax) * 100
      } else {
        previewOverallScore.value = 0
      }
      
      ElMessage.success(`Predicted overall score: ${previewOverallScore.value.toFixed(1)}%`)
    }

    const saveIndividualScore = async (questionId) => {
      if (!parallelScoringData.value) return
      
      const score = finalScores.value[questionId]
      const comment = finalComments.value[questionId] || ''
      
      if (score === null || score === undefined) {
        ElMessage.warning('Please enter a score before saving')
        return
      }
      
      try {
        savingScores.value[questionId] = true
        
        // Prepare score data for this specific question
        const scoreData = {
          assignment_id: parallelScoringData.value.assignment.assignment_id,
          final_scores: [{
            question_id: questionId,
            final_score: score,
            final_comment: comment
          }],
          assignee_decision: 'DRAFT', // Mark as draft while individual scores are being saved
          assignee_comments: 'Individual score saved',
          assignee_id: getCurrentUserId()
        }
        
        const response = await api.post('/vendor-approval/final-assignee-scores/save/', scoreData)
        
        if (response.data.success) {
          ElMessage.success(`Score saved for question ${questionId}`)
          
          // Refresh overall score from backend to get the accurate calculation
          await refreshOverallScoreFromBackend()
        }
        
      } catch (error) {
        console.error('Error saving individual score:', error)
        ElMessage.error('Failed to save score')
      } finally {
        savingScores.value[questionId] = false
      }
    }

    const calculateOverallScore = () => {
      if (!parallelScoringData.value) return
      
      let totalWeightedScore = 0
      let totalWeightedMax = 0
      
      parallelScoringData.value.questions_and_responses.forEach(qr => {
        const finalScore = finalScores.value[qr.question_id]
        if (finalScore !== null && finalScore !== undefined) {
          const weight = qr.scoring_weight || 1
          const maxScore = getMaxScore(weight)
          
          totalWeightedScore += finalScore * weight
          totalWeightedMax += maxScore * weight
        }
      })
      
      if (totalWeightedMax > 0) {
        calculatedOverallScore.value = (totalWeightedScore / totalWeightedMax) * 100
      } else {
        calculatedOverallScore.value = 0
      }
    }

    const refreshOverallScoreFromBackend = async () => {
      if (!parallelScoringData.value) return
      
      try {
        const response = await api.get(`/api/v1/vendor-approval/parallel-scoring/${parallelScoringData.value.approval_id}/`)
        if (response.data.success) {
          // Update the assignment overall score from backend
          parallelScoringData.value.assignment.overall_score = response.data.assignment.overall_score
          calculatedOverallScore.value = response.data.assignment.overall_score || 0
        }
      } catch (error) {
        console.error('Error refreshing overall score from backend:', error)
      }
    }

    const toggleCollapse = (stageId) => {
      isCollapsed.value[stageId] = !isCollapsed.value[stageId]
    }

    const toggleVersionHistory = () => {
      showVersionHistory.value = !showVersionHistory.value
    }

    const getScoreClass = (score) => {
      if (score >= 80) return 'score-excellent'
      if (score >= 60) return 'score-good'
      if (score >= 40) return 'score-fair'
      return 'score-poor'
    }

    const getScoreBarClass = (scoreRatio) => {
      if (scoreRatio >= 0.8) return 'score-fill-excellent'
      if (scoreRatio >= 0.6) return 'score-fill-good'
      if (scoreRatio >= 0.4) return 'score-fill-fair'
      return 'score-fill-poor'
    }

    const getDecisionClass = (decision) => {
      const decisionMap = {
        'APPROVED': 'decision-approved',
        'REJECTED': 'decision-rejected',
        'REVIEWED': 'decision-reviewed',
        'PENDING': 'decision-pending'
      }
      return decisionMap[decision] || 'decision-reviewed'
    }

    const getDisplayDecision = (decision) => {
      // Map the decision values to proper display text
      const decisionMap = {
        'APPROVED': 'APPROVED',
        'REJECTED': 'REJECTED',
        'REVIEWED': 'REVIEWED',
        'PENDING': 'PENDING',
        'APPROVE': 'APPROVED',
        'REJECT': 'REJECTED',
        'REVIEW': 'REVIEWED'
      }
      return decisionMap[decision] || 'PENDING'
    }

    const getConsensusText = (reviewerScores, averageScore) => {
      if (!reviewerScores || reviewerScores.length === 0) return 'No reviews yet'
      
      const completedScores = reviewerScores.filter(r => r.score !== null && r.score !== undefined)
      const pendingScores = reviewerScores.filter(r => r.score === null || r.score === undefined)
      
      if (completedScores.length === 0) return `${pendingScores.length} reviewer(s) pending`
      if (completedScores.length === 1) {
        return pendingScores.length > 0 
          ? `Single review completed, ${pendingScores.length} pending`
          : 'Single reviewer assessment'
      }
      
      if (pendingScores.length > 0) {
        return `${completedScores.length} completed, ${pendingScores.length} pending`
      }
      
      // All reviewers have completed - show consensus
      // averageScore is now normalized to 0-100 scale, so use it directly
      const scorePercentage = averageScore || 0
      
      if (scorePercentage >= 80) return 'Strong consensus - High scores'
      if (scorePercentage >= 60) return 'Good consensus - Above average'
      if (scorePercentage >= 40) return 'Mixed consensus - Average scores'
      return 'Low consensus - Below average scores'
    }

    const saveFinalAssigneeDecision = async () => {
      if (!parallelScoringData.value) {
        ElMessage.error('No scoring data available')
        return
      }
      
      if (!assigneeDecisionForm.decision) {
        ElMessage.warning('Please select a decision (Approve/Reject)')
        return
      }
      
      // Validate that scores are provided
      const missingScores = parallelScoringData.value.questions_and_responses.filter(qr => 
        finalScores.value[qr.question_id] === undefined || finalScores.value[qr.question_id] === null
      )
      
      if (missingScores.length > 0) {
        ElMessage.warning(`Please provide final scores for all ${missingScores.length} remaining questions`)
        return
      }
      
      try {
        submittingFinalDecision.value = true
        
        // Prepare final scores data
        const finalScoresData = parallelScoringData.value.questions_and_responses.map(qr => ({
          question_id: qr.question_id,
          final_score: finalScores.value[qr.question_id],
          final_comment: finalComments.value[qr.question_id] || ''
        }))
        
        const payload = {
          assignment_id: parallelScoringData.value.assignment.assignment_id,
          final_scores: finalScoresData,
          assignee_decision: assigneeDecisionForm.decision,
          assignee_comments: assigneeDecisionForm.comments,
          assignee_id: getCurrentUserId()
        }
        
        const response = await api.post('/api/v1/vendor-approval/final-assignee-scores/save/', payload)
        
        if (response.data.success) {
          ElMessage.success('Final decision and scores saved successfully!')
          
          // Refresh the data to show updated status
          await loadParallelScoringData(parallelScoringData.value.approval_id)
          
          // Refresh version history to show the new version created by assignee decision
          try {
            const approvalId = parallelScoringData.value.approval_id
            const vRes = await api.get(`/vendor-approval/requests/${approvalId}/versions/`)
            versionHistory.value[approvalId] = vRes.data || []
            console.log(`✓ Version history refreshed for approval ${approvalId}`)
          } catch (vError) {
            console.error('Failed to refresh version history:', vError)
          }
          
          // Refresh the requester data to reflect the new status
          if (selectedRequesterId.value) {
            await fetchRequesterData()
          }
          
          // Reset form
          Object.assign(assigneeDecisionForm, { decision: '', comments: '' })
          previewOverallScore.value = null
        }
        
      } catch (error) {
        console.error('Error saving final decision:', error)
        ElMessage.error('Failed to save final decision')
      } finally {
        submittingFinalDecision.value = false
      }
    }

    return {
      selectedRequesterId,
      selectedApprovalId,
      requesters,
      requesterRequests,
      versionHistory,
      submitting,
      statusChanging,
      decisionForm,
      rejectionForm,
      adminRejectionForm,
      finalDecisionForm,
      fetchSingleRequest,
      fetchRequesterData,
      hasRejectedStages,
      allStagesCompleted,
      formatRevisedPayload,
      validateRevisedPayload,
      formatRevisedData,
      validateRevisedData,
      handleRejectionRevision,
      handleAdminRejection,
      handleRequesterFinalDecision,
      handleScoreOverrideChange,
      resetToCalculatedScore,
      getAdminActionLabel,
      getVersionTypeColor,
      getStatusType,
      formatDate,
      isFinalVendorApproval,
      getVendorData,
      getRiskSummary,
      getInternalRisks,
      getExternalRisks,
      getVendorRiskBadgeClass,
      getVendorStatusBadgeClass,
      getRiskPriorityBadgeClass,
      getRiskStatusBadgeClass,
      getScreeningTypeBadgeClass,
      getResolutionStatusBadgeClass,
      getMatchDescription,
      isParallelResponseApproval,
      parallelScoringData,
      finalScores,
      finalComments,
      assigneeDecisionForm,
      submittingFinalDecision,
      previewOverallScore,
      loadParallelScoringData,
      getMaxScore,
      calculatePreviewScore,
      saveFinalAssigneeDecision,
      saveIndividualScore,
      calculateOverallScore,
      getScoreClass,
      getScoreBarClass,
      getDecisionClass,
      getDisplayDecision,
      getConsensusText,
      savingScores,
      calculatedOverallScore,
      refreshOverallScoreFromBackend,
      isCollapsed,
      showVersionHistory,
      toggleCollapse,
      toggleVersionHistory,
      showRiskGenerationPopup,
      riskGenerationStatus,
      checkRiskGenerationStatus,
      startRiskGenerationTracking,
      closeRiskGenerationPopup
    }
  }
}
</script>

<!-- Import Enhanced Styles -->
<style src="./AssigneeDecision.css"></style>

<!-- Fallback Critical Styles -->
<style>
/* Fallback styles to ensure basic functionality if CSS import fails */
.assignee-decision {
  max-width: 1400px;
  margin: 0 auto;
  padding: 32px 24px;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  min-height: 100vh;
}

.decision-card {
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  margin-bottom: 32px;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 12px 24px;
  border: 2px solid transparent;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-primary {
  background: #93c5fd;
  color: #1f2937;
  border-color: #c7d2fe;
}

.btn-info {
  background: #bfdbfe;
  color: #1f2937;
  border-color: #c7d2fe;
}

.form-select, .form-input, .form-textarea {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  font-size: 15px;
  transition: all 0.3s ease;
}

.form-select:focus, .form-input:focus, .form-textarea:focus {
  outline: none;
  border-color: #93c5fd;
  box-shadow: 0 0 0 4px rgba(147, 197, 253, 0.3);
}

/* Radio button fixes */
.radio-item {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  min-height: 48px;
  width: 100%;
}

.radio-item input[type="radio"] {
  width: 20px;
  height: 20px;
  min-width: 20px;
  max-width: 20px;
  flex-shrink: 0;
  margin: 0;
}

.radio-item span {
  flex: 1;
  line-height: 1.6;
  word-wrap: break-word;
  white-space: normal;
  display: inline-block;
  overflow-wrap: break-word;
}

/* Stage summary compact styles */
.stages-summary {
  margin: 20px 0;
}

.collapse-header {
  padding: 12px 16px;
  min-height: 48px;
  cursor: pointer;
}

.stage-header-content {
  display: flex;
  align-items: center;
  gap: 12px;
}
</style>