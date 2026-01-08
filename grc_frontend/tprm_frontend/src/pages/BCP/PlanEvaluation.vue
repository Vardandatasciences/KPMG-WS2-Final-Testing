<template>
  <div class="space-y-6">
    <div class="plans-dropdown-section">
      <div class="plans-dropdown">
        <label class="modern-label">
          <div class="label-content">
            <div class="label-icon">
              <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
              </svg>
            </div>
            <span class="label-text">Select Plan</span>
          </div>
        </label>
        <div class="modern-dropdown" :class="{ 'is-open': isDropdownOpen }">
          <button 
            class="modern-trigger"
            @click="toggleDropdown"
            @blur="closeDropdown"
          >
            <div class="trigger-content">
              <div v-if="selectedPlanId" class="selected-plan">
                <div class="selected-plan-info">
                  <span class="selected-plan-name">{{ getSelectedPlanDisplay() }}</span>
                  <div class="selected-plan-badges">
                    <span :class="['mini-badge', getSelectedPlanType() === 'BCP' ? 'badge--default' : 'badge--secondary']">
                      {{ getSelectedPlanType() }}
                    </span>
                  </div>
                </div>
              </div>
              <div v-else class="placeholder-content">
                <span class="placeholder-text">Choose a plan...</span>
                <span class="placeholder-subtitle">Select from available BCP/DRP plans</span>
              </div>
            </div>
            <div class="trigger-icon">
              <svg class="dropdown-arrow" :class="{ 'rotated': isDropdownOpen }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
              </svg>
            </div>
          </button>
          <Transition name="dropdown">
            <div v-if="isDropdownOpen" class="table-dropdown-menu">
              <div class="table-header">
                <span class="table-title">Available Plans</span>
                <span class="table-count">{{ availablePlans.length }} plans</span>
              </div>
              <div class="table-container">
                <div v-if="isLoadingPlans" class="loading-state">
                  <div class="loading-spinner"></div>
                  <p>Loading plans...</p>
                </div>
                <div v-else-if="availablePlans.length === 0" class="empty-state">
                  <div class="empty-icon">📄</div>
                  <p>No plans available</p>
                  <p class="empty-subtitle">No BCP/DRP plans found in the system</p>
                </div>
                <table v-else class="plans-table">
                  <thead>
                    <tr>
                      <th class="checkbox-column">
                        <input 
                          type="checkbox" 
                          class="select-all-checkbox"
                          :checked="isAllSelected"
                          @change="toggleSelectAll"
                        />
                      </th>
                      <th>Plan ID</th>
                      <th>Plan Name</th>
                      <th>Type</th>
                      <th>Strategy</th>
                      <th>Vendor</th>
                      <th>Criticality</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr 
                      v-for="plan in availablePlans" 
                      :key="plan.plan_id"
                      class="plan-row"
                      :class="{ 'selected': selectedPlanId === plan.plan_id.toString() }"
                    >
                      <td class="checkbox-column">
                        <input 
                          type="checkbox" 
                          class="plan-checkbox"
                          :checked="selectedPlanId === plan.plan_id.toString()"
                          @change="openPlanForEvaluation(plan)"
                        />
                      </td>
                      <td class="plan-id-cell">{{ plan.plan_id }}</td>
                      <td class="plan-name-cell">{{ plan.plan_name }}</td>
                      <td>
                        <span :class="['badge', plan.plan_type === 'BCP' ? 'badge--default' : 'badge--secondary']">
                          {{ plan.plan_type }}
                        </span>
                      </td>
                      <td class="strategy-cell">{{ plan.strategy_name }}</td>
                      <td class="vendor-cell">{{ plan.vendor_id }}</td>
                      <td>
                        {{ plan.criticality }}
                      </td>
                      <td>
                        {{ typeof plan.status === 'string' ? plan.status.replace(/_/g, ' ') : 'N/A' }}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </Transition>
        </div>
      </div>
    </div>


    <div v-if="selectedEvaluation" class="card">
      <div class="card-header">
        <div class="card-title flex items-center justify-between">
          <span>Evaluation - {{ selectedEvaluationData?.plan_name || 'Loading...' }} (Plan ID: {{ selectedEvaluation }})</span>
          <div class="flex items-center gap-2">
            <span :class="['badge', selectedEvaluationData?.plan_type === 'BCP' ? 'badge--default' : 'badge--secondary']">
              {{ selectedEvaluationData?.plan_type || 'N/A' }}
            </span>
            <span :class="['badge', getStatusColor(selectedEvaluationData?.status)]">
              {{ typeof selectedEvaluationData?.status === 'string' ? selectedEvaluationData.status.replace(/_/g, ' ') : 'N/A' }}
            </span>
            <div class="flex items-center gap-1 text-sm text-muted-foreground">
              <svg class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.464 0L4.351 16.5c-.77.833.192 2.5 1.732 2.5z"/>
              </svg>
              Submitted: {{ formatDate(selectedEvaluationData?.submitted_at) }}
            </div>
          </div>
        </div>
        
      </div>
      <div class="card-content">
        <!-- Loading State -->
        <div v-if="isLoadingPlanDetails" class="loading-state">
          <div class="loading-spinner"></div>
          <p>Loading plan details and evaluation data...</p>
        </div>
        
        <!-- Evaluation Section -->
        <div v-else class="evaluation-section">
          <!-- Two-Column Layout: Extracted Data (Left) + Evaluation Form (Right) -->
          <div class="evaluation-workspace-two-column">
          <!-- Left Column: Extracted Data and Risks -->
          <div class="extracted-data-column">
            <!-- Toggle Buttons -->
            <div class="data-toggle-buttons">
              <button
                :class="['toggle-button', { 'active': activeDataTab === 'extracted' }]"
                @click="activeDataTab = 'extracted'"
              >
                Extracted Plan Data
              </button>
              <button
                :class="['toggle-button', { 'active': activeDataTab === 'risks' }]"
                @click="activeDataTab = 'risks'; fetchPlanRisks()"
              >
                Risks
                <span v-if="planRisks.length > 0" class="risk-count-badge">{{ planRisks.length }}</span>
              </button>
            </div>

            <!-- Extracted Plan Data Tab -->
            <div v-show="activeDataTab === 'extracted'">
              <h3 class="column-title">Extracted Plan Data</h3>
              <div v-if="isLoadingPlanDetails" class="loading-state">
                <div class="loading-spinner"></div>
                <span>Loading extracted data...</span>
              </div>
            <div v-else-if="selectedEvaluationData && selectedEvaluationData.extracted_data" class="extracted-data-list">
              <!-- Dynamic display of all extracted fields (including custom fields) -->
              <template v-for="(value, key) in selectedEvaluationData.extracted_data" :key="key">
                <div v-if="key !== 'plan_id' && value !== null && value !== undefined && !isEmptyValue(value)" class="data-item">
                  <span class="data-label">{{ formatFieldLabel(key) }}:</span>
                  <span class="data-value">{{ formatFieldValue(value) }}</span>
                </div>
              </template>
              
              <!-- Fallback message if no data fields are populated -->
              <div v-if="!hasAnyExtractedData" class="no-data">
                <div class="no-data-icon">📄</div>
                <p>No extracted data fields are populated for this plan.</p>
                <p class="no-data-subtitle">The plan may not have been processed through OCR extraction yet.</p>
              </div>
            </div>
            <div v-else class="no-data">
              <div class="no-data-icon">📄</div>
              <p>No extracted data available for this plan.</p>
              <p class="no-data-subtitle">The plan may not have been processed through OCR extraction yet.</p>
            </div>
            </div>

            <!-- Risks Tab -->
            <div v-show="activeDataTab === 'risks'">
              <h3 class="column-title">Risks</h3>
              <div v-if="isLoadingRisks" class="loading-state">
                <div class="loading-spinner"></div>
                <span>Loading risks...</span>
              </div>
              <div v-else-if="planRisks.length > 0" class="risks-list">
                <div v-for="(risk, index) in planRisks" :key="risk.id" class="risk-item">
                  <div class="risk-number">{{ index + 1 }}</div>
                  <div class="risk-header">
                    <div class="risk-title-row">
                      <h4 class="risk-title">{{ risk.title }}</h4>
                      <span :class="['risk-priority-badge', `priority-${risk.priority?.toLowerCase()}`]">
                        {{ risk.priority }}
                      </span>
                    </div>
                    <div class="risk-meta">
                      <span class="risk-score">Score: {{ risk.score }}</span>
                      <span class="risk-likelihood">Likelihood: {{ risk.likelihood }}</span>
                      <span class="risk-impact">Impact: {{ risk.impact }}</span>
                    </div>
                  </div>
                  <div v-if="risk.description" class="risk-description">
                    <span class="risk-label">Description:</span>
                    <span class="risk-value">{{ risk.description }}</span>
                  </div>
                  <div v-if="risk.ai_explanation" class="risk-explanation">
                    <span class="risk-label">AI Explanation:</span>
                    <span class="risk-value">{{ risk.ai_explanation }}</span>
                  </div>
                  <div v-if="risk.suggested_mitigations && risk.suggested_mitigations.length > 0" class="risk-mitigations">
                    <span class="risk-label">Suggested Mitigations:</span>
                    <ul class="mitigation-list">
                      <li v-for="(mitigation, index) in risk.suggested_mitigations" :key="index" class="mitigation-item">
                        {{ mitigation }}
                      </li>
                    </ul>
                  </div>
                  <div class="risk-footer">
                    <span class="risk-status">Status: {{ risk.status }}</span>
                    <span class="risk-type">Type: {{ risk.risk_type }}</span>
                  </div>
                </div>
              </div>
              <div v-else class="no-data">
                <div class="no-data-icon">⚠️</div>
                <p>No risks found for this plan.</p>
                <p class="no-data-subtitle">Risks will appear here once they are generated for this plan.</p>
              </div>
            </div>
          </div>

          <!-- Right Column: Evaluation Form -->
          <div class="evaluation-form-column">
            <h3 class="column-title">Evaluation Form</h3>
            <div class="evaluation-form-content">

              <!-- Quick Score Inputs -->
              <div class="quick-score-section">
                <h4 class="section-subtitle">Quick Score Input</h4>
                <div class="score-inputs-grid">
                  <div class="score-input-group">
                    <label class="label flex items-center gap-2">
                      <span>Coverage Score</span>
                      <div class="bcp-data-type-circle-toggle-wrapper">
                        <div class="bcp-data-type-circle-toggle">
                          <div 
                            class="bcp-circle-option bcp-personal-circle" 
                            :class="{ active: getEvaluationDataType('coverage_score') === 'personal' }"
                            @click="setEvaluationDataType('coverage_score', 'personal')"
                            title="Personal Data"
                          >
                            <div class="bcp-circle-inner"></div>
                          </div>
                          <div 
                            class="bcp-circle-option bcp-confidential-circle" 
                            :class="{ active: getEvaluationDataType('coverage_score') === 'confidential' }"
                            @click="setEvaluationDataType('coverage_score', 'confidential')"
                            title="Confidential Data"
                          >
                            <div class="bcp-circle-inner"></div>
                          </div>
                          <div 
                            class="bcp-circle-option bcp-regular-circle" 
                            :class="{ active: getEvaluationDataType('coverage_score') === 'regular' }"
                            @click="setEvaluationDataType('coverage_score', 'regular')"
                            title="Regular Data"
                          >
                            <div class="bcp-circle-inner"></div>
                          </div>
                        </div>
                      </div>
                    </label>
                    <input 
                      type="number" 
                      min="0" 
                      max="100" 
                      step="1"
                      class="input score-input"
                      v-model.number="evaluationData.coverage_score"
                      @input="onMainScoreChange('coverage')"
                      placeholder="0-100"
                    />
                  </div>
                  <div class="score-input-group">
                    <label class="label flex items-center gap-2">
                      <span>Quality Score</span>
                      <div class="bcp-data-type-circle-toggle-wrapper">
                        <div class="bcp-data-type-circle-toggle">
                          <div 
                            class="bcp-circle-option bcp-personal-circle" 
                            :class="{ active: getEvaluationDataType('quality_score') === 'personal' }"
                            @click="setEvaluationDataType('quality_score', 'personal')"
                            title="Personal Data"
                          >
                            <div class="bcp-circle-inner"></div>
                          </div>
                          <div 
                            class="bcp-circle-option bcp-confidential-circle" 
                            :class="{ active: getEvaluationDataType('quality_score') === 'confidential' }"
                            @click="setEvaluationDataType('quality_score', 'confidential')"
                            title="Confidential Data"
                          >
                            <div class="bcp-circle-inner"></div>
                          </div>
                          <div 
                            class="bcp-circle-option bcp-regular-circle" 
                            :class="{ active: getEvaluationDataType('quality_score') === 'regular' }"
                            @click="setEvaluationDataType('quality_score', 'regular')"
                            title="Regular Data"
                          >
                            <div class="bcp-circle-inner"></div>
                          </div>
                        </div>
                      </div>
                    </label>
                    <input 
                      type="number" 
                      min="0" 
                      max="100" 
                      step="1"
                      class="input score-input"
                      v-model.number="evaluationData.quality_score"
                      @input="onMainScoreChange('quality')"
                      placeholder="0-100"
                    />
                  </div>
                  <div class="score-input-group">
                    <label class="label flex items-center gap-2">
                      <span>Compliance Score</span>
                      <div class="bcp-data-type-circle-toggle-wrapper">
                        <div class="bcp-data-type-circle-toggle">
                          <div 
                            class="bcp-circle-option bcp-personal-circle" 
                            :class="{ active: getEvaluationDataType('compliance_score') === 'personal' }"
                            @click="setEvaluationDataType('compliance_score', 'personal')"
                            title="Personal Data"
                          >
                            <div class="bcp-circle-inner"></div>
                          </div>
                          <div 
                            class="bcp-circle-option bcp-confidential-circle" 
                            :class="{ active: getEvaluationDataType('compliance_score') === 'confidential' }"
                            @click="setEvaluationDataType('compliance_score', 'confidential')"
                            title="Confidential Data"
                          >
                            <div class="bcp-circle-inner"></div>
                          </div>
                          <div 
                            class="bcp-circle-option bcp-regular-circle" 
                            :class="{ active: getEvaluationDataType('compliance_score') === 'regular' }"
                            @click="setEvaluationDataType('compliance_score', 'regular')"
                            title="Regular Data"
                          >
                            <div class="bcp-circle-inner"></div>
                          </div>
                        </div>
                      </div>
                    </label>
                    <input 
                      type="number" 
                      min="0" 
                      max="100" 
                      step="1"
                      class="input score-input"
                      v-model.number="evaluationData.compliance_score"
                      @input="onMainScoreChange('compliance')"
                      placeholder="0-100"
                    />
                  </div>
                  <div v-if="selectedEvaluationData?.plan_type === 'DRP'" class="score-input-group">
                    <label class="label flex items-center gap-2">
                      <span>Recovery Score</span>
                      <div class="bcp-data-type-circle-toggle-wrapper">
                        <div class="bcp-data-type-circle-toggle">
                          <div 
                            class="bcp-circle-option bcp-personal-circle" 
                            :class="{ active: getEvaluationDataType('recovery_capability_score') === 'personal' }"
                            @click="setEvaluationDataType('recovery_capability_score', 'personal')"
                            title="Personal Data"
                          >
                            <div class="bcp-circle-inner"></div>
                          </div>
                          <div 
                            class="bcp-circle-option bcp-confidential-circle" 
                            :class="{ active: getEvaluationDataType('recovery_capability_score') === 'confidential' }"
                            @click="setEvaluationDataType('recovery_capability_score', 'confidential')"
                            title="Confidential Data"
                          >
                            <div class="bcp-circle-inner"></div>
                          </div>
                          <div 
                            class="bcp-circle-option bcp-regular-circle" 
                            :class="{ active: getEvaluationDataType('recovery_capability_score') === 'regular' }"
                            @click="setEvaluationDataType('recovery_capability_score', 'regular')"
                            title="Regular Data"
                          >
                            <div class="bcp-circle-inner"></div>
                          </div>
                        </div>
                      </div>
                    </label>
                    <input 
                      type="number" 
                      min="0" 
                      max="100" 
                      step="1"
                      class="input score-input"
                      v-model.number="evaluationData.recovery_capability_score"
                      @input="onMainScoreChange('recovery')"
                      placeholder="0-100"
                    />
                  </div>
                  <div class="score-input-group overall-score">
                    <label class="label flex items-center gap-2">
                      <span>Overall Score</span>
                      <div class="bcp-data-type-circle-toggle-wrapper">
                        <div class="bcp-data-type-circle-toggle">
                          <div 
                            class="bcp-circle-option bcp-personal-circle" 
                            :class="{ active: getEvaluationDataType('overall_score') === 'personal' }"
                            @click="setEvaluationDataType('overall_score', 'personal')"
                            title="Personal Data"
                          >
                            <div class="bcp-circle-inner"></div>
                          </div>
                          <div 
                            class="bcp-circle-option bcp-confidential-circle" 
                            :class="{ active: getEvaluationDataType('overall_score') === 'confidential' }"
                            @click="setEvaluationDataType('overall_score', 'confidential')"
                            title="Confidential Data"
                          >
                            <div class="bcp-circle-inner"></div>
                          </div>
                          <div 
                            class="bcp-circle-option bcp-regular-circle" 
                            :class="{ active: getEvaluationDataType('overall_score') === 'regular' }"
                            @click="setEvaluationDataType('overall_score', 'regular')"
                            title="Regular Data"
                          >
                            <div class="bcp-circle-inner"></div>
                          </div>
                        </div>
                      </div>
                    </label>
                    <input 
                      type="number" 
                      min="0" 
                      max="100" 
                      step="1"
                      class="input score-input overall-score-input"
                      v-model.number="evaluationData.overall_score"
                      readonly
                      placeholder="Auto-calculated"
                    />
                  </div>
                  <div class="score-input-group">
                    <label class="label flex items-center gap-2">
                      <span>Weighted Score</span>
                      <div class="bcp-data-type-circle-toggle-wrapper">
                        <div class="bcp-data-type-circle-toggle">
                          <div 
                            class="bcp-circle-option bcp-personal-circle" 
                            :class="{ active: getEvaluationDataType('weighted_score') === 'personal' }"
                            @click="setEvaluationDataType('weighted_score', 'personal')"
                            title="Personal Data"
                          >
                            <div class="bcp-circle-inner"></div>
                          </div>
                          <div 
                            class="bcp-circle-option bcp-confidential-circle" 
                            :class="{ active: getEvaluationDataType('weighted_score') === 'confidential' }"
                            @click="setEvaluationDataType('weighted_score', 'confidential')"
                            title="Confidential Data"
                          >
                            <div class="bcp-circle-inner"></div>
                          </div>
                          <div 
                            class="bcp-circle-option bcp-regular-circle" 
                            :class="{ active: getEvaluationDataType('weighted_score') === 'regular' }"
                            @click="setEvaluationDataType('weighted_score', 'regular')"
                            title="Regular Data"
                          >
                            <div class="bcp-circle-inner"></div>
                          </div>
                        </div>
                      </div>
                    </label>
                    <input 
                      type="number" 
                      min="0" 
                      max="100" 
                      step="1"
                      class="input score-input"
                      v-model.number="evaluationData.weighted_score"
                      placeholder="0-100"
                    />
                  </div>
                </div>
              </div>

              <!-- Detailed Evaluation Questions -->
              <div class="detailed-questions-section">
                <h4 class="section-subtitle">Detailed Evaluation Questions</h4>
                <div class="questions-tabs">
                  <div class="questions-tab-list">
                    <button
                      v-for="tab in tabOptions"
                      :key="tab.value"
                      :class="['questions-tab-trigger', { 'active': activeTab === tab.value }]"
                      :disabled="tab.disabled"
                      @click="activeTab = tab.value"
                    >
                      {{ tab.label }}
                    </button>
                  </div>

                  <div v-show="activeTab === 'coverage'" class="questions-tab-content">
                    <div class="questions-list">
                      <!-- Coverage Question 1 -->
                      <div class="question-item">
                        <div class="question-header">
                          <label class="question-label flex items-center gap-2">
                            <span>Is scope comprehensive and well-defined?</span>
                            <div class="bcp-data-type-circle-toggle-wrapper">
                              <div class="bcp-data-type-circle-toggle">
                                <div 
                                  class="bcp-circle-option bcp-personal-circle" 
                                  :class="{ active: getEvaluationDataType('scope_comprehensive') === 'personal' }"
                                  @click="setEvaluationDataType('scope_comprehensive', 'personal')"
                                  title="Personal Data"
                                >
                                  <div class="bcp-circle-inner"></div>
                                </div>
                                <div 
                                  class="bcp-circle-option bcp-confidential-circle" 
                                  :class="{ active: getEvaluationDataType('scope_comprehensive') === 'confidential' }"
                                  @click="setEvaluationDataType('scope_comprehensive', 'confidential')"
                                  title="Confidential Data"
                                >
                                  <div class="bcp-circle-inner"></div>
                                </div>
                                <div 
                                  class="bcp-circle-option bcp-regular-circle" 
                                  :class="{ active: getEvaluationDataType('scope_comprehensive') === 'regular' }"
                                  @click="setEvaluationDataType('scope_comprehensive', 'regular')"
                                  title="Regular Data"
                                >
                                  <div class="bcp-circle-inner"></div>
                                </div>
                              </div>
                            </div>
                          </label>
                          <div class="yes-no-options">
                            <label class="radio-option">
                              <input type="radio" name="coverage_scope_comprehensive" value="yes" class="radio-item" v-model="evaluationData.yes_no_responses.coverage_scope_comprehensive" />
                              <span>Yes</span>
                            </label>
                            <label class="radio-option">
                              <input type="radio" name="coverage_scope_comprehensive" value="no" class="radio-item" v-model="evaluationData.yes_no_responses.coverage_scope_comprehensive" />
                              <span>No</span>
                            </label>
                          </div>
                        </div>
                        <div class="question-inputs">
                          <div class="score-input-group">
                            <label class="label">Score (0-100)</label>
                            <input
                              type="number"
                              min="0"
                              max="100"
                              step="1"
                              v-model="evaluationData.criteria_json.coverage.scope_comprehensive"
                              placeholder="75"
                              class="input"
                              @input="updateScore('coverage', 'scope_comprehensive', parseFloat(($event.target as HTMLInputElement).value))"
                            />
                          </div>
                          <div class="comment-input-group">
                            <label class="label">Comment</label>
                            <textarea
                              v-model="evaluationData.criteria_json.coverage.comments.scope_comprehensive"
                              placeholder="Why?"
                              class="textarea"
                              @input="updateComment('coverage', 'scope_comprehensive', ($event.target as HTMLTextAreaElement).value)"
                            />
                          </div>
                        </div>
                      </div>

                      <!-- Coverage Question 2 -->
                      <div class="question-item">
                        <div class="question-header">
                          <label class="question-label flex items-center gap-2">
                            <span>Are RTO/RPO targets adequate and realistic?</span>
                            <div class="bcp-data-type-circle-toggle-wrapper">
                              <div class="bcp-data-type-circle-toggle">
                                <div 
                                  class="bcp-circle-option bcp-personal-circle" 
                                  :class="{ active: getEvaluationDataType('rto_rpo_adequate') === 'personal' }"
                                  @click="setEvaluationDataType('rto_rpo_adequate', 'personal')"
                                  title="Personal Data"
                                >
                                  <div class="bcp-circle-inner"></div>
                                </div>
                                <div 
                                  class="bcp-circle-option bcp-confidential-circle" 
                                  :class="{ active: getEvaluationDataType('rto_rpo_adequate') === 'confidential' }"
                                  @click="setEvaluationDataType('rto_rpo_adequate', 'confidential')"
                                  title="Confidential Data"
                                >
                                  <div class="bcp-circle-inner"></div>
                                </div>
                                <div 
                                  class="bcp-circle-option bcp-regular-circle" 
                                  :class="{ active: getEvaluationDataType('rto_rpo_adequate') === 'regular' }"
                                  @click="setEvaluationDataType('rto_rpo_adequate', 'regular')"
                                  title="Regular Data"
                                >
                                  <div class="bcp-circle-inner"></div>
                                </div>
                              </div>
                            </div>
                          </label>
                          <div class="yes-no-options">
                            <label class="radio-option">
                              <input type="radio" name="coverage_rto_rpo_adequate" value="yes" class="radio-item" v-model="evaluationData.yes_no_responses.coverage_rto_rpo_adequate" />
                              <span>Yes</span>
                            </label>
                            <label class="radio-option">
                              <input type="radio" name="coverage_rto_rpo_adequate" value="no" class="radio-item" v-model="evaluationData.yes_no_responses.coverage_rto_rpo_adequate" />
                              <span>No</span>
                            </label>
                          </div>
                        </div>
                        <div class="question-inputs">
                          <div class="score-input-group">
                            <label class="label">Score (0-100)</label>
                            <input
                              type="number"
                              min="0"
                              max="100"
                              step="1"
                              v-model="evaluationData.criteria_json.coverage.rto_rpo_adequate"
                              placeholder="75"
                              class="input"
                              @input="updateScore('coverage', 'rto_rpo_adequate', parseFloat(($event.target as HTMLInputElement).value))"
                            />
                          </div>
                          <div class="comment-input-group">
                            <label class="label">Comment</label>
                            <textarea
                              v-model="evaluationData.criteria_json.coverage.comments.rto_rpo_adequate"
                              placeholder="Why?"
                              class="textarea"
                              @input="updateComment('coverage', 'rto_rpo_adequate', ($event.target as HTMLTextAreaElement).value)"
                            />
                          </div>
                        </div>
                      </div>

                      <!-- Coverage Question 3 -->
                      <div class="question-item">
                        <div class="question-header">
                          <label class="question-label flex items-center gap-2">
                            <span>Are all critical services identified and prioritized?</span>
                            <div class="bcp-data-type-circle-toggle-wrapper">
                              <div class="bcp-data-type-circle-toggle">
                                <div 
                                  class="bcp-circle-option bcp-personal-circle" 
                                  :class="{ active: getEvaluationDataType('critical_services_listed') === 'personal' }"
                                  @click="setEvaluationDataType('critical_services_listed', 'personal')"
                                  title="Personal Data"
                                >
                                  <div class="bcp-circle-inner"></div>
                                </div>
                                <div 
                                  class="bcp-circle-option bcp-confidential-circle" 
                                  :class="{ active: getEvaluationDataType('critical_services_listed') === 'confidential' }"
                                  @click="setEvaluationDataType('critical_services_listed', 'confidential')"
                                  title="Confidential Data"
                                >
                                  <div class="bcp-circle-inner"></div>
                                </div>
                                <div 
                                  class="bcp-circle-option bcp-regular-circle" 
                                  :class="{ active: getEvaluationDataType('critical_services_listed') === 'regular' }"
                                  @click="setEvaluationDataType('critical_services_listed', 'regular')"
                                  title="Regular Data"
                                >
                                  <div class="bcp-circle-inner"></div>
                                </div>
                              </div>
                            </div>
                          </label>
                          <div class="yes-no-options">
                            <label class="radio-option">
                              <input type="radio" name="coverage_critical_services_listed" value="yes" class="radio-item" v-model="evaluationData.yes_no_responses.coverage_critical_services_listed" />
                              <span>Yes</span>
                            </label>
                            <label class="radio-option">
                              <input type="radio" name="coverage_critical_services_listed" value="no" class="radio-item" v-model="evaluationData.yes_no_responses.coverage_critical_services_listed" />
                              <span>No</span>
                            </label>
                          </div>
                        </div>
                        <div class="question-inputs">
                          <div class="score-input-group">
                            <label class="label">Score (0-100)</label>
                            <input
                              type="number"
                              min="0"
                              max="100"
                              step="1"
                              v-model="evaluationData.criteria_json.coverage.critical_services_listed"
                              placeholder="75"
                              class="input"
                              @input="updateScore('coverage', 'critical_services_listed', parseFloat(($event.target as HTMLInputElement).value))"
                            />
                          </div>
                          <div class="comment-input-group">
                            <label class="label">Comment</label>
                            <textarea
                              v-model="evaluationData.criteria_json.coverage.comments.critical_services_listed"
                              placeholder="Why?"
                              class="textarea"
                              @input="updateComment('coverage', 'critical_services_listed', ($event.target as HTMLTextAreaElement).value)"
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div v-show="activeTab === 'quality'" class="questions-tab-content">
                    <div class="questions-list">
                      <!-- Quality Question 1 -->
                      <div class="question-item">
                        <div class="question-header">
                          <label class="question-label flex items-center gap-2">
                            <span>Are roles and responsibilities clearly defined?</span>
                            <div class="bcp-data-type-circle-toggle-wrapper">
                              <div class="bcp-data-type-circle-toggle">
                                <div 
                                  class="bcp-circle-option bcp-personal-circle" 
                                  :class="{ active: getEvaluationDataType('roles_responsibilities_clear') === 'personal' }"
                                  @click="setEvaluationDataType('roles_responsibilities_clear', 'personal')"
                                  title="Personal Data"
                                >
                                  <div class="bcp-circle-inner"></div>
                                </div>
                                <div 
                                  class="bcp-circle-option bcp-confidential-circle" 
                                  :class="{ active: getEvaluationDataType('roles_responsibilities_clear') === 'confidential' }"
                                  @click="setEvaluationDataType('roles_responsibilities_clear', 'confidential')"
                                  title="Confidential Data"
                                >
                                  <div class="bcp-circle-inner"></div>
                                </div>
                                <div 
                                  class="bcp-circle-option bcp-regular-circle" 
                                  :class="{ active: getEvaluationDataType('roles_responsibilities_clear') === 'regular' }"
                                  @click="setEvaluationDataType('roles_responsibilities_clear', 'regular')"
                                  title="Regular Data"
                                >
                                  <div class="bcp-circle-inner"></div>
                                </div>
                              </div>
                            </div>
                          </label>
                          <div class="yes-no-options">
                            <label class="radio-option">
                              <input type="radio" name="quality_roles_responsibilities_clear" value="yes" class="radio-item" v-model="evaluationData.yes_no_responses.quality_roles_responsibilities_clear" />
                              <span>Yes</span>
                            </label>
                            <label class="radio-option">
                              <input type="radio" name="quality_roles_responsibilities_clear" value="no" class="radio-item" v-model="evaluationData.yes_no_responses.quality_roles_responsibilities_clear" />
                              <span>No</span>
                            </label>
                          </div>
                        </div>
                        <div class="question-inputs">
                          <div class="score-input-group">
                            <label class="label">Score (0-100)</label>
                            <input
                              type="number"
                              min="0"
                              max="100"
                              step="1"
                              v-model="evaluationData.criteria_json.quality.roles_responsibilities_clear"
                              placeholder="75"
                              class="input"
                              @input="updateScore('quality', 'roles_responsibilities_clear', parseFloat(($event.target as HTMLInputElement).value))"
                            />
                          </div>
                          <div class="comment-input-group">
                            <label class="label">Comment</label>
                            <textarea
                              v-model="evaluationData.criteria_json.quality.comments.roles_responsibilities_clear"
                              placeholder="Why?"
                              class="textarea"
                              @input="updateComment('quality', 'roles_responsibilities_clear', ($event.target as HTMLTextAreaElement).value)"
                            />
                          </div>
                        </div>
                      </div>

                      <!-- Quality Question 2 -->
                      <div class="question-item">
                        <div class="question-header">
                          <label class="question-label flex items-center gap-2">
                            <span>Are communication plans comprehensive and tested?</span>
                            <div class="bcp-data-type-circle-toggle-wrapper">
                              <div class="bcp-data-type-circle-toggle">
                                <div 
                                  class="bcp-circle-option bcp-personal-circle" 
                                  :class="{ active: getEvaluationDataType('communication_plans_solid') === 'personal' }"
                                  @click="setEvaluationDataType('communication_plans_solid', 'personal')"
                                  title="Personal Data"
                                >
                                  <div class="bcp-circle-inner"></div>
                                </div>
                                <div 
                                  class="bcp-circle-option bcp-confidential-circle" 
                                  :class="{ active: getEvaluationDataType('communication_plans_solid') === 'confidential' }"
                                  @click="setEvaluationDataType('communication_plans_solid', 'confidential')"
                                  title="Confidential Data"
                                >
                                  <div class="bcp-circle-inner"></div>
                                </div>
                                <div 
                                  class="bcp-circle-option bcp-regular-circle" 
                                  :class="{ active: getEvaluationDataType('communication_plans_solid') === 'regular' }"
                                  @click="setEvaluationDataType('communication_plans_solid', 'regular')"
                                  title="Regular Data"
                                >
                                  <div class="bcp-circle-inner"></div>
                                </div>
                              </div>
                            </div>
                          </label>
                          <div class="yes-no-options">
                            <label class="radio-option">
                              <input type="radio" name="quality_communication_plans_solid" value="yes" class="radio-item" v-model="evaluationData.yes_no_responses.quality_communication_plans_solid" />
                              <span>Yes</span>
                            </label>
                            <label class="radio-option">
                              <input type="radio" name="quality_communication_plans_solid" value="no" class="radio-item" v-model="evaluationData.yes_no_responses.quality_communication_plans_solid" />
                              <span>No</span>
                            </label>
                          </div>
                        </div>
                        <div class="question-inputs">
                          <div class="score-input-group">
                            <label class="label">Score (0-100)</label>
                            <input
                              type="number"
                              min="0"
                              max="100"
                              step="1"
                              v-model="evaluationData.criteria_json.quality.communication_plans_solid"
                              placeholder="75"
                              class="input"
                              @input="updateScore('quality', 'communication_plans_solid', parseFloat(($event.target as HTMLInputElement).value))"
                            />
                          </div>
                          <div class="comment-input-group">
                            <label class="label">Comment</label>
                            <textarea
                              v-model="evaluationData.criteria_json.quality.comments.communication_plans_solid"
                              placeholder="Why?"
                              class="textarea"
                              @input="updateComment('quality', 'communication_plans_solid', ($event.target as HTMLTextAreaElement).value)"
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div v-show="activeTab === 'compliance'" class="questions-tab-content">
                    <div class="questions-list">
                      <!-- Compliance Question 1 -->
                      <div class="question-item">
                        <div class="question-header">
                          <label class="question-label flex items-center gap-2">
                            <span>Do regulatory references align with current requirements?</span>
                            <div class="bcp-data-type-circle-toggle-wrapper">
                              <div class="bcp-data-type-circle-toggle">
                                <div 
                                  class="bcp-circle-option bcp-personal-circle" 
                                  :class="{ active: getEvaluationDataType('regulatory_references_align') === 'personal' }"
                                  @click="setEvaluationDataType('regulatory_references_align', 'personal')"
                                  title="Personal Data"
                                >
                                  <div class="bcp-circle-inner"></div>
                                </div>
                                <div 
                                  class="bcp-circle-option bcp-confidential-circle" 
                                  :class="{ active: getEvaluationDataType('regulatory_references_align') === 'confidential' }"
                                  @click="setEvaluationDataType('regulatory_references_align', 'confidential')"
                                  title="Confidential Data"
                                >
                                  <div class="bcp-circle-inner"></div>
                                </div>
                                <div 
                                  class="bcp-circle-option bcp-regular-circle" 
                                  :class="{ active: getEvaluationDataType('regulatory_references_align') === 'regular' }"
                                  @click="setEvaluationDataType('regulatory_references_align', 'regular')"
                                  title="Regular Data"
                                >
                                  <div class="bcp-circle-inner"></div>
                                </div>
                              </div>
                            </div>
                          </label>
                          <div class="yes-no-options">
                            <label class="radio-option">
                              <input type="radio" name="compliance_regulatory" value="yes" class="radio-item" v-model="evaluationData.yes_no_responses.compliance_regulatory" />
                              <span>Yes</span>
                            </label>
                            <label class="radio-option">
                              <input type="radio" name="compliance_regulatory" value="no" class="radio-item" v-model="evaluationData.yes_no_responses.compliance_regulatory" />
                              <span>No</span>
                            </label>
                          </div>
                        </div>
                        <div class="question-inputs">
                          <div class="score-input-group">
                            <label class="label">Score (0-100)</label>
                            <input 
                              type="number" 
                              min="0" 
                              max="100" 
                              step="1" 
                              v-model="evaluationData.criteria_json.compliance.regulatory_references_align"
                              placeholder="75" 
                              class="input"
                              @input="updateScore('compliance', 'regulatory_references_align', parseFloat(($event.target as HTMLInputElement).value))"
                            />
                          </div>
                          <div class="comment-input-group">
                            <label class="label">Comment</label>
                            <textarea 
                              v-model="evaluationData.criteria_json.compliance.comments.regulatory_references_align"
                              placeholder="Why?" 
                              class="textarea"
                              @input="updateComment('compliance', 'regulatory_references_align', ($event.target as HTMLTextAreaElement).value)"
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div v-show="activeTab === 'recovery'" class="questions-tab-content">
                    <div class="questions-list">
                      <!-- Recovery Question 1 -->
                      <div class="question-item">
                        <div class="question-header">
                          <label class="question-label flex items-center gap-2">
                            <span>Is recovery capability adequate for business needs?</span>
                            <div class="bcp-data-type-circle-toggle-wrapper">
                              <div class="bcp-data-type-circle-toggle">
                                <div 
                                  class="bcp-circle-option bcp-personal-circle" 
                                  :class="{ active: getEvaluationDataType('recovery_capability_adequate') === 'personal' }"
                                  @click="setEvaluationDataType('recovery_capability_adequate', 'personal')"
                                  title="Personal Data"
                                >
                                  <div class="bcp-circle-inner"></div>
                                </div>
                                <div 
                                  class="bcp-circle-option bcp-confidential-circle" 
                                  :class="{ active: getEvaluationDataType('recovery_capability_adequate') === 'confidential' }"
                                  @click="setEvaluationDataType('recovery_capability_adequate', 'confidential')"
                                  title="Confidential Data"
                                >
                                  <div class="bcp-circle-inner"></div>
                                </div>
                                <div 
                                  class="bcp-circle-option bcp-regular-circle" 
                                  :class="{ active: getEvaluationDataType('recovery_capability_adequate') === 'regular' }"
                                  @click="setEvaluationDataType('recovery_capability_adequate', 'regular')"
                                  title="Regular Data"
                                >
                                  <div class="bcp-circle-inner"></div>
                                </div>
                              </div>
                            </div>
                          </label>
                          <div class="yes-no-options">
                            <label class="radio-option">
                              <input type="radio" name="recovery_capability" value="yes" class="radio-item" v-model="evaluationData.yes_no_responses.recovery_capability" />
                              <span>Yes</span>
                            </label>
                            <label class="radio-option">
                              <input type="radio" name="recovery_capability" value="no" class="radio-item" v-model="evaluationData.yes_no_responses.recovery_capability" />
                              <span>No</span>
                            </label>
                          </div>
                        </div>
                        <div class="question-inputs">
                          <div class="score-input-group">
                            <label class="label">Score (0-100)</label>
                            <input 
                              type="number" 
                              min="0" 
                              max="100" 
                              step="1" 
                              v-model="evaluationData.criteria_json.recovery.recovery_capability_adequate"
                              placeholder="75" 
                              class="input"
                              @input="updateScore('recovery', 'recovery_capability_adequate', parseFloat(($event.target as HTMLInputElement).value))"
                            />
                          </div>
                          <div class="comment-input-group">
                            <label class="label">Comment</label>
                            <textarea 
                              v-model="evaluationData.criteria_json.recovery.comments.recovery_capability_adequate"
                              placeholder="Why?" 
                              class="textarea"
                              @input="updateComment('recovery', 'recovery_capability_adequate', ($event.target as HTMLTextAreaElement).value)"
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          </div>
        </div>


        <!-- No Data State -->
        <div v-if="!selectedEvaluationData" class="no-data">
          <div class="no-data-icon">⚠️</div>
          <p>Failed to load plan details</p>
          <p class="no-data-subtitle">Please try selecting the plan again</p>
        </div>

        <!-- Bottom Section: Comments and Actions -->
        <div v-if="selectedEvaluationData" class="evaluation-bottom-section">
          <!-- Comments Section -->
          <div class="comments-section">
            <h3 class="section-title flex items-center gap-2">
              <span>Evaluator Comments</span>
              <div class="bcp-data-type-circle-toggle-wrapper">
                <div class="bcp-data-type-circle-toggle">
                  <div 
                    class="bcp-circle-option bcp-personal-circle" 
                    :class="{ active: getEvaluationDataType('evaluator_comments') === 'personal' }"
                    @click="setEvaluationDataType('evaluator_comments', 'personal')"
                    title="Personal Data"
                  >
                    <div class="bcp-circle-inner"></div>
                  </div>
                  <div 
                    class="bcp-circle-option bcp-confidential-circle" 
                    :class="{ active: getEvaluationDataType('evaluator_comments') === 'confidential' }"
                    @click="setEvaluationDataType('evaluator_comments', 'confidential')"
                    title="Confidential Data"
                  >
                    <div class="bcp-circle-inner"></div>
                  </div>
                  <div 
                    class="bcp-circle-option bcp-regular-circle" 
                    :class="{ active: getEvaluationDataType('evaluator_comments') === 'regular' }"
                    @click="setEvaluationDataType('evaluator_comments', 'regular')"
                    title="Regular Data"
                  >
                    <div class="bcp-circle-inner"></div>
                  </div>
                </div>
              </div>
            </h3>
            <textarea 
              class="textarea"
              placeholder="Enter your overall assessment and recommendations..."
              v-model="evaluationData.evaluator_comments"
              rows="4"
            />
          </div>

          <!-- Action Buttons -->
          <div class="action-buttons">
            <button class="btn btn--outline btn--sm" @click="loadMockData">
              <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/>
              </svg>
              Load Data
            </button>
            <button class="btn btn--primary btn--sm" @click="submitEvaluation" :disabled="isSubmitting">
              <svg v-if="!isSubmitting" class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/>
              </svg>
              <svg v-else class="h-4 w-4 mr-2 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
              </svg>
              {{ isSubmitting ? 'Submitting Evaluation...' : 'Submit' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import './PlanEvaluation.css'
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../../services/api_bcp.js'
import { useNotifications } from '@/composables/useNotifications'
import { PopupService } from '@/popup/popupService'
import notificationService from '@/services/notificationService'
import loggingService from '@/services/loggingService'

// Type definitions for API responses
interface ApiResponse {
  plans?: any[]
  data?: {
    plans?: any[]
  }
}

// Force TypeScript recompilation
const _forceRecompile = true

const route = useRoute()
const router = useRouter()
const { showSuccess, showError, showWarning, showInfo } = useNotifications()

// Reactive data
const selectedEvaluation = ref<string | null>(null)
const selectedPlanId = ref<string>("")
const availablePlans = ref<any[]>([])
const isDropdownOpen = ref(false)
const isLoadingPlans = ref(false)
const activeTab = ref("coverage")
const activeDataTab = ref("extracted") // Toggle between 'extracted' and 'risks'
const planRisks = ref<any[]>([])
const isLoadingRisks = ref(false)
const evaluationData = ref<any>({
  // Main scores (0-100) - Initialize with 0 instead of null
  overall_score: 0,
  quality_score: 0,
  coverage_score: 0,
  recovery_capability_score: 0,
  compliance_score: 0,
  weighted_score: 0,
  
  // Yes/No radio button responses
  yes_no_responses: {
    coverage_scope_comprehensive: '',
    coverage_rto_rpo_adequate: '',
    coverage_critical_services_listed: '',
    quality_roles_responsibilities_clear: '',
    quality_communication_plans_solid: '',
    compliance_regulatory: '',
    recovery_capability: ''
  },
  
  // Detailed criteria scores (JSON structure)
  criteria_json: {
    coverage: {
      scope_comprehensive: null,
      rto_rpo_adequate: null,
      critical_services_listed: null,
      dependencies_identified: null,
      risk_assessment_complete: null,
      comments: {}
    },
    quality: {
      roles_responsibilities_clear: null,
      communication_plans_solid: null,
      testing_procedures_adequate: null,
      training_schedule_defined: null,
      maintenance_review_cycle: null,
      comments: {}
    },
    compliance: {
      regulatory_references_align: null,
      industry_standards_met: null,
      bank_requirements_covered: null,
      audit_trail_complete: null,
      comments: {}
    },
    recovery: {
      recovery_capability_adequate: null,
      backup_strategies_comprehensive: null,
      failover_procedures_defined: null,
      recovery_site_details: null,
      testing_validation_schedule: null,
      comments: {}
    }
  },
  
  // Comments
  evaluator_comments: ""
})

const selectedEvaluationData = ref<any>(null)
const isLoadingPlanDetails = ref(false)

// Data type classification for evaluation fields
const evaluationFieldDataTypes = reactive({
  overall_score: 'regular',
  quality_score: 'regular',
  coverage_score: 'regular',
  recovery_capability_score: 'regular',
  compliance_score: 'regular',
  weighted_score: 'regular',
  evaluator_comments: 'regular',
  // Yes/No responses
  coverage_scope_comprehensive: 'regular',
  coverage_rto_rpo_adequate: 'regular',
  coverage_critical_services_listed: 'regular',
  quality_roles_responsibilities_clear: 'regular',
  quality_communication_plans_solid: 'regular',
  compliance_regulatory: 'regular',
  recovery_capability: 'regular',
  // Coverage criteria
  scope_comprehensive: 'regular',
  rto_rpo_adequate: 'regular',
  critical_services_listed: 'regular',
  // Quality criteria
  roles_responsibilities_clear: 'regular',
  communication_plans_solid: 'regular',
  // Compliance criteria
  regulatory_references_align: 'regular',
  // Recovery criteria
  recovery_capability_adequate: 'regular'
})

// Method to set data type for an evaluation field
const setEvaluationDataType = (fieldName: string, type: string) => {
  if (evaluationFieldDataTypes.hasOwnProperty(fieldName)) {
    evaluationFieldDataTypes[fieldName] = type
    console.log(`Data type selected for evaluation field ${fieldName}:`, type)
  }
}

// Get data type for an evaluation field
const getEvaluationDataType = (fieldName: string) => {
  return evaluationFieldDataTypes[fieldName] || 'regular'
}

// Helper function to build data_inventory JSON for evaluation
const buildEvaluationDataInventory = () => {
  const fieldLabelMap = {
    overall_score: 'Overall Score',
    quality_score: 'Quality Score',
    coverage_score: 'Coverage Score',
    recovery_capability_score: 'Recovery Capability Score',
    compliance_score: 'Compliance Score',
    weighted_score: 'Weighted Score',
    evaluator_comments: 'Evaluator Comments',
    coverage_scope_comprehensive: 'Coverage - Scope Comprehensive',
    coverage_rto_rpo_adequate: 'Coverage - RTO/RPO Adequate',
    coverage_critical_services_listed: 'Coverage - Critical Services Listed',
    quality_roles_responsibilities_clear: 'Quality - Roles Responsibilities Clear',
    quality_communication_plans_solid: 'Quality - Communication Plans Solid',
    compliance_regulatory: 'Compliance - Regulatory',
    recovery_capability: 'Recovery - Capability',
    scope_comprehensive: 'Scope Comprehensive',
    rto_rpo_adequate: 'RTO/RPO Adequate',
    critical_services_listed: 'Critical Services Listed',
    roles_responsibilities_clear: 'Roles Responsibilities Clear',
    communication_plans_solid: 'Communication Plans Solid',
    regulatory_references_align: 'Regulatory References Align',
    recovery_capability_adequate: 'Recovery Capability Adequate'
  }

  const dataInventory = {}
  
  // Build flat structure: {"Field Label": "data_type"}
  for (const [fieldName, dataType] of Object.entries(evaluationFieldDataTypes)) {
    if (fieldLabelMap[fieldName]) {
      const fieldLabel = fieldLabelMap[fieldName]
      dataInventory[fieldLabel] = dataType
    }
  }
  
  console.log('📋 Evaluation Data Inventory JSON:', JSON.stringify(dataInventory, null, 2))
  return dataInventory
}

// Computed properties
const isAllSelected = computed(() => {
  return availablePlans.value.length > 0 && availablePlans.value.every(plan => 
    selectedPlanId.value === plan.plan_id.toString()
  )
})

const tabOptions = computed(() => [
  { value: "coverage", label: "Coverage", disabled: false },
  { value: "quality", label: "Quality", disabled: false },
  { value: "compliance", label: "Compliance", disabled: false },
  { value: "recovery", label: "DR", disabled: selectedEvaluationData.value?.plan_type !== "DRP" }
])


const hasAnyExtractedData = computed(() => {
  if (!selectedEvaluationData.value?.extracted_data) return false
  
  const data = selectedEvaluationData.value.extracted_data
  
  // Check all fields dynamically (including custom fields)
  return Object.keys(data).some(key => {
    if (key === 'plan_id') return false
    
    const value = data[key]
    return !isEmptyValue(value)
  })
})

// Note: RTO/RPO targets are now formatted dynamically using formatFieldValue function

// Utility functions
const getStatusColor = (status: string) => {
  if (!status) return "bg-gray-100 text-gray-800"
  switch (status) {
    case "ASSIGNED": return "bg-blue-100 text-blue-800"
    case "IN_PROGRESS": return "bg-yellow-100 text-yellow-800"
    case "SUBMITTED": return "bg-green-100 text-green-800"
    default: return "bg-gray-100 text-gray-800"
  }
}

const getCriticalityBadgeClass = (criticality: string) => {
  if (!criticality) return "badge--secondary"
  switch (criticality) {
    case "CRITICAL": return "badge--destructive"
    case "HIGH": return "badge--warning"
    case "MEDIUM": return "badge--secondary"
    case "LOW": return "badge--outline"
    default: return "badge--secondary"
  }
}

const getStatusBadgeClass = (status: string) => {
  if (!status) return "badge--secondary"
  switch (status) {
    case "SUBMITTED": return "badge--default"
    case "OCR_COMPLETED": return "badge--success"
    case "ASSIGNED_FOR_EVALUATION": return "badge--warning"
    case "APPROVED": return "badge--success"
    case "REJECTED": return "badge--destructive"
    case "REVISION_REQUESTED": return "badge--warning"
    default: return "badge--secondary"
  }
}

const formatDate = (dateString: string) => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

// Helper function to format field labels (convert snake_case to Title Case)
const formatFieldLabel = (key: string): string => {
  // Handle special cases with custom labels
  const labelMap: { [key: string]: string } = {
    'purpose_scope': 'Purpose & Scope',
    'regulatory_references': 'Regulatory References',
    'critical_services': 'Critical Services',
    'critical_systems': 'Critical Systems',
    'dependencies_internal': 'Internal Dependencies',
    'dependencies_external': 'External Dependencies',
    'risk_assessment_summary': 'Risk Assessment Summary',
    'bia_summary': 'Business Impact Analysis Summary',
    'rto_targets': 'RTO Targets',
    'rpo_targets': 'RPO Targets',
    'communication_plan_internal': 'Internal Communication Plan',
    'communication_plan_bank': 'Bank Communication Plan',
    'roles_responsibilities': 'Roles & Responsibilities',
    'training_testing_schedule': 'Training & Testing Schedule',
    'testing_validation_schedule': 'Testing & Validation Schedule',
    'maintenance_review_cycle': 'Maintenance & Review Cycle',
    'critical_applications': 'Critical Applications',
    'databases_list': 'Databases',
    'supporting_infrastructure': 'Supporting Infrastructure',
    'third_party_services': 'Third Party Services',
    'disaster_scenarios': 'Disaster Scenarios',
    'disaster_declaration_process': 'Disaster Declaration Process',
    'data_backup_strategy': 'Data Backup Strategy',
    'recovery_site_details': 'Recovery Site Details',
    'failover_procedures': 'Failover Procedures',
    'failback_procedures': 'Failback Procedures',
    'network_recovery_steps': 'Network Recovery Steps',
    'application_restoration_order': 'Application Restoration Order',
    'incident_types': 'Incident Types',
    'alternate_work_locations': 'Alternate Work Locations'
  }
  
  // Return mapped label if exists, otherwise format the key
  if (labelMap[key]) {
    return labelMap[key]
  }
  
  // Convert snake_case to Title Case
  return key
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ')
}

// Helper function to format field values (handle arrays, objects, strings)
const formatFieldValue = (value: any): string => {
  if (value === null || value === undefined) return ''
  
  // Handle arrays
  if (Array.isArray(value)) {
    return value.length > 0 ? value.join(', ') : ''
  }
  
  // Handle objects (like RTO/RPO targets)
  if (typeof value === 'object' && value !== null) {
    // Check if it's an empty object
    if (Object.keys(value).length === 0) return ''
    
    // Format as key-value pairs
    return Object.entries(value)
      .map(([key, val]) => `${key}: ${val}`)
      .join(', ')
  }
  
  // Handle strings and other primitives
  return String(value)
}

// Helper function to check if a value is empty
const isEmptyValue = (value: any): boolean => {
  if (value === null || value === undefined) return true
  if (typeof value === 'string' && value.trim() === '') return true
  if (Array.isArray(value) && value.length === 0) return true
  if (typeof value === 'object' && Object.keys(value).length === 0) return true
  return false
}



// Load plans on component mount
onMounted(async () => {
  await loggingService.logPageView('BCP', 'Plan Evaluation')
  await fetchPlans()
  
  // Check for planId URL parameter and preselect the plan
  const planIdFromUrl = route.query.planId
  if (planIdFromUrl) {
    console.log('Plan ID from URL parameter:', planIdFromUrl)
    
    // Find the plan in the available plans
    const targetPlan = availablePlans.value.find(plan => 
      plan.plan_id.toString() === planIdFromUrl.toString()
    )
    
    if (targetPlan) {
      console.log('Found target plan:', targetPlan)
      // Preselect the plan and open it for evaluation
      await openPlanForEvaluation(targetPlan)
    } else {
      console.warn('Plan with ID', planIdFromUrl, 'not found in available plans')
    }
  }
})


// API functions
const fetchPlans = async () => {
  isLoadingPlans.value = true
  try {
    console.log('Fetching plans from API endpoint: http://localhost:8000/api/bcpdrp/plans/')
    const response = await api.plans.list()
    
    console.log('API response data:', response)
    console.log('Response type:', typeof response)
    console.log('Response keys:', Object.keys(response))
    
    // Check if plans are in response.data.plans (unwrapped by interceptor) or response.plans
    const apiResponse = response as ApiResponse
    const plans = apiResponse.plans || apiResponse.data?.plans
    console.log('Plans found:', plans)
    console.log('Plans type:', typeof plans)
    console.log('Plans length:', plans ? plans.length : 'undefined')
    
    if (plans && Array.isArray(plans)) {
      availablePlans.value = plans
      console.log('Successfully fetched plans:', plans.length, 'plans')
    } else {
      console.error('API returned no plans data or plans is not an array')
      console.error('Response structure:', JSON.stringify(response, null, 2))
      availablePlans.value = []
    }
  } catch (error) {
    console.error('Error fetching plans from API:', error)
    availablePlans.value = []
    PopupService.error(`Failed to load plans: ${error.message}. Please check your connection and try again.`, 'Loading Failed')
  } finally {
    isLoadingPlans.value = false
  }
}

// Score calculation functions
const updateScore = (section: string, question: string, score: number) => {
  // Update criteria_json with detailed scores
  evaluationData.value.criteria_json[section] = {
    ...evaluationData.value.criteria_json[section],
    [question]: score
  }
  
  // Calculate section average and update main score
  // Only include actual score values, not comments or other non-score properties
  const sectionData = evaluationData.value.criteria_json[section]
  const scoreFields = Object.keys(sectionData).filter(key => 
    key !== 'comments' && 
    sectionData[key] !== null && 
    sectionData[key] !== undefined &&
    typeof sectionData[key] === 'number'
  )
  
  if (scoreFields.length > 0) {
    const sectionAverage = scoreFields.reduce((sum, key) => sum + sectionData[key], 0) / scoreFields.length
    evaluationData.value[`${section}_score`] = Math.round(sectionAverage * 100) / 100
  }
  
  // Calculate overall score
  calculateOverallScore()
}

const updateComment = (section: string, question: string, comment: string) => {
  // Store comments in criteria_json for detailed tracking
  if (!evaluationData.value.criteria_json[section].comments) {
    evaluationData.value.criteria_json[section].comments = {}
  }
  evaluationData.value.criteria_json[section].comments[question] = comment
}

const onMainScoreChange = (section: string) => {
  // When main score inputs change, update the corresponding section scores in criteria_json
  // This ensures the detailed evaluation questions reflect the main scores
  const scoreValue = evaluationData.value[`${section}_score`]
  console.log(`Main score changed for ${section}:`, scoreValue)
  
  if (scoreValue !== null && scoreValue !== undefined) {
    // Update the criteria_json section to reflect the main score
    // This helps maintain consistency between quick scores and detailed evaluation
    if (!evaluationData.value.criteria_json[section]) {
      evaluationData.value.criteria_json[section] = { comments: {} }
    }
    
    // Set a default score for the first question in each section if not already set
    const sectionQuestions = {
      coverage: ['scope_comprehensive', 'rto_rpo_adequate', 'critical_services_listed'],
      quality: ['roles_responsibilities_clear', 'communication_plans_solid'],
      compliance: ['regulatory_references_align'],
      recovery: ['recovery_capability_adequate']
    }
    
    const questions = sectionQuestions[section] || []
    if (questions.length > 0) {
      // Set the first question's score to match the main score if it's not already set
      const firstQuestion = questions[0]
      if (evaluationData.value.criteria_json[section][firstQuestion] === null || 
          evaluationData.value.criteria_json[section][firstQuestion] === undefined) {
        evaluationData.value.criteria_json[section][firstQuestion] = scoreValue
        console.log(`Set ${section}.${firstQuestion} to ${scoreValue}`)
      }
    }
  }
  
  // Always recalculate overall score when any main score changes
  calculateOverallScore()
  console.log('Updated evaluation data:', evaluationData.value)
}

const calculateOverallScore = () => {
  const scores = []
  
  // Always include these scores for both BCP and DRP
  if (evaluationData.value.coverage_score !== null && evaluationData.value.coverage_score !== undefined) {
    scores.push(evaluationData.value.coverage_score)
  }
  if (evaluationData.value.quality_score !== null && evaluationData.value.quality_score !== undefined) {
    scores.push(evaluationData.value.quality_score)
  }
  if (evaluationData.value.compliance_score !== null && evaluationData.value.compliance_score !== undefined) {
    scores.push(evaluationData.value.compliance_score)
  }
  
  // Only include recovery score for DRP plans
  if (selectedEvaluationData.value?.plan_type === 'DRP' && 
      evaluationData.value.recovery_capability_score !== null && 
      evaluationData.value.recovery_capability_score !== undefined) {
    scores.push(evaluationData.value.recovery_capability_score)
  }
  
  if (scores.length > 0) {
    const overall = scores.reduce((sum, score) => sum + score, 0) / scores.length
    evaluationData.value.overall_score = Math.round(overall * 100) / 100
  } else {
    evaluationData.value.overall_score = 0
  }
}

// Save and submit functions
const saveDraft = async () => {
  if (!selectedEvaluation.value) {
    await showWarning('No Plan Selected', 'Please select a plan first.', {
      action: 'no_plan_selected'
    })
    PopupService.warning('Please select a plan first.', 'No Plan Selected')
    return
  }

  try {
    const saveData = {
      ...evaluationData.value,
      is_final_submission: false,
      data_inventory: buildEvaluationDataInventory()
    }
    console.log('Saving draft with data:', saveData)
    
    const response = await api.evaluations.save(selectedEvaluation.value, saveData)

    if (response) {
      PopupService.success('Your evaluation progress has been saved', 'Draft Saved')
      // Create notification
      await notificationService.createEvaluationNotification('evaluation_saved', {
        plan_id: selectedEvaluation.value,
        evaluation_id: (response as any).evaluation_id || (response as any).data?.evaluation_id || selectedEvaluation.value
      })
    }
  } catch (error) {
    console.error('Error saving draft:', error)
    PopupService.error(`Failed to save draft: ${error.message || 'Unknown error'}`, 'Save Failed')
    // Create error notification
    await notificationService.createEvaluationNotification('evaluation_failed', {
      plan_id: selectedEvaluation.value,
      error: error.message || 'Unknown error'
    })
  }
}

const isSubmitting = ref(false)

const submitEvaluation = async () => {
  if (!selectedEvaluation.value) {
    await showWarning('No Plan Selected', 'Please select a plan first.', {
      action: 'no_plan_selected'
    })
    PopupService.warning('Please select a plan first.', 'No Plan Selected')
    return
  }


  isSubmitting.value = true
  
  try {
    const submitData = {
      ...evaluationData.value,
      is_final_submission: true,
      data_inventory: buildEvaluationDataInventory()
    }
    console.log('Submitting evaluation with data:', submitData)
    
    const response = await api.evaluations.save(selectedEvaluation.value, submitData)

    if (response) {
      // Show success notification
      await showSuccess('Evaluation Submitted', 'Evaluation submitted successfully!', {
        action: 'evaluation_submitted',
        evaluation_id: selectedEvaluation.value
      })
      
      // Show success popup
      PopupService.success('Evaluation submitted successfully!', 'Evaluation Submitted')
      
      // Create additional notification service notification
      await notificationService.createEvaluationNotification('evaluation_submitted', {
        plan_id: selectedEvaluation.value,
        evaluation_id: selectedEvaluation.value
      })
      
      // Refresh the evaluation data to show the updated status
      await fetchPlanDetails(parseInt(selectedEvaluation.value))
      
      // Redirect to Approval Assignment screen
      setTimeout(() => {
        router.push('/bcp/approval-assignment')
      }, 2000)
    }
  } catch (error) {
    console.error('Error submitting evaluation:', error)
    
    // Show error notification
    await showError('Submission Failed', 'Failed to submit evaluation. Please try again.', {
      action: 'evaluation_submission_failed',
      evaluation_id: selectedEvaluation.value,
      error_message: error.message || 'Unknown error',
      is_timeout: error.message && error.message.includes('timeout')
    })
    
    // Show error popup
    PopupService.error('Failed to submit evaluation. Please try again.', 'Submission Failed')
    
    // Create additional notification service notification
    await notificationService.createEvaluationNotification('evaluation_failed', {
      plan_id: selectedEvaluation.value,
      error: error.message || 'Unknown error'
    })
  } finally {
    isSubmitting.value = false
  }
}

const toggleDropdown = () => {
  isDropdownOpen.value = !isDropdownOpen.value
}

const closeDropdown = () => {
  setTimeout(() => {
    isDropdownOpen.value = false
  }, 150)
}

const selectPlan = async (plan: any) => {
  selectedPlanId.value = plan.plan_id.toString()
  isDropdownOpen.value = false
  // Also open the plan for evaluation when selecting
  await openPlanForEvaluation(plan)
}

const toggleSelectAll = async () => {
  if (isAllSelected.value) {
    selectedPlanId.value = ""
    selectedEvaluation.value = null
  } else {
    if (availablePlans.value.length > 0) {
      await selectPlan(availablePlans.value[0])
    }
  }
}

const getSelectedPlanDisplay = () => {
  const plan = availablePlans.value.find(p => p.plan_id.toString() === selectedPlanId.value)
  if (plan) {
    return `[${plan.plan_id}] ${plan.plan_name} (${plan.plan_type})`
  }
  return ""
}

const getSelectedPlanType = () => {
  const plan = availablePlans.value.find(p => p.plan_id.toString() === selectedPlanId.value)
  return plan ? plan.plan_type : ""
}

const openPlanForEvaluation = async (plan: any) => {
  console.log('Opening plan for evaluation:', plan)
  selectedEvaluation.value = plan.plan_id.toString()
  selectedPlanId.value = plan.plan_id.toString()
  await fetchPlanDetails(plan.plan_id)
}

const fetchPlanRisks = async () => {
  if (!selectedEvaluation.value) return
  
  isLoadingRisks.value = true
  try {
    console.log('Fetching risks for plan ID:', selectedEvaluation.value)
    const response = await api.risks.getPlanRisks(parseInt(selectedEvaluation.value))
    
    if (response && response.data) {
      planRisks.value = response.data.risks || []
      console.log(`Loaded ${planRisks.value.length} risks for plan ${selectedEvaluation.value}`)
    } else {
      planRisks.value = []
    }
  } catch (error) {
    console.error('Error fetching plan risks:', error)
    planRisks.value = []
    PopupService.error(`Failed to load risks: ${error.message || 'Unknown error'}`, 'Loading Failed')
  } finally {
    isLoadingRisks.value = false
  }
}

const fetchPlanDetails = async (planId: number) => {
  isLoadingPlanDetails.value = true
  try {
    console.log('Fetching plan details for plan ID:', planId)
    
    // Fetch both plan details and evaluations in parallel
    const [planData, evaluationResponseData] = await Promise.all([
      api.ocr.planDetail(planId),
      api.evaluations.list(planId).catch(() => null) // Don't fail if no evaluations exist
    ])
    
    console.log('Plan details loaded successfully for plan ID:', planId)
    
    if (evaluationResponseData) {
      console.log('Evaluation data response:', evaluationResponseData)
    } else {
      console.log('No evaluation data available for this plan')
    }
    
    // Both responses are unwrapped by the HTTP interceptor, so we access the data directly
    if (planData && planData.data) {
      selectedEvaluationData.value = {
        ...planData.data,
        evaluations: evaluationResponseData?.data?.evaluations || [],
        latest_evaluation: evaluationResponseData?.data?.evaluations && evaluationResponseData.data.evaluations.length > 0 
          ? evaluationResponseData.data.evaluations[0] 
          : null
      }
      
      console.log('Plan data loaded successfully')
      
      // Load existing evaluation data if available
      if (evaluationResponseData?.data?.evaluations && evaluationResponseData.data.evaluations.length > 0) {
        const latestEval = evaluationResponseData.data.evaluations[0]
        console.log('Loading existing evaluation data')
        
        // Deep merge the existing evaluation data
        evaluationData.value = {
          overall_score: latestEval.overall_score || 0,
          quality_score: latestEval.quality_score || 0,
          coverage_score: latestEval.coverage_score || 0,
          recovery_capability_score: latestEval.recovery_capability_score || 0,
          compliance_score: latestEval.compliance_score || 0,
          weighted_score: latestEval.weighted_score || 0,
          yes_no_responses: latestEval.yes_no_responses || {
            coverage_scope_comprehensive: '',
            coverage_rto_rpo_adequate: '',
            coverage_critical_services_listed: '',
            quality_roles_responsibilities_clear: '',
            quality_communication_plans_solid: '',
            compliance_regulatory: '',
            recovery_capability: ''
          },
          criteria_json: {
            coverage: {
              ...latestEval.criteria_json?.coverage,
              comments: latestEval.criteria_json?.coverage?.comments || {}
            },
            quality: {
              ...latestEval.criteria_json?.quality,
              comments: latestEval.criteria_json?.quality?.comments || {}
            },
            compliance: {
              ...latestEval.criteria_json?.compliance,
              comments: latestEval.criteria_json?.compliance?.comments || {}
            },
            recovery: {
              ...latestEval.criteria_json?.recovery,
              comments: latestEval.criteria_json?.recovery?.comments || {}
            }
          },
          evaluator_comments: latestEval.evaluator_comments || ""
        }
        
        console.log('Loaded existing evaluation data')
      } else {
        // Reset to default values for new evaluation
        console.log('No existing evaluation found, resetting to defaults')
        evaluationData.value = {
          overall_score: 0,
          quality_score: 0,
          coverage_score: 0,
          recovery_capability_score: 0,
          compliance_score: 0,
          weighted_score: 0,
          yes_no_responses: {
            coverage_scope_comprehensive: '',
            coverage_rto_rpo_adequate: '',
            coverage_critical_services_listed: '',
            quality_roles_responsibilities_clear: '',
            quality_communication_plans_solid: '',
            compliance_regulatory: '',
            recovery_capability: ''
          },
          criteria_json: {
            coverage: { comments: {} },
            quality: { comments: {} },
            compliance: { comments: {} },
            recovery: { comments: {} }
          },
          evaluator_comments: ""
        }
      }
      
      console.log('Successfully loaded plan details')
      
      // Reset active data tab to extracted when loading new plan
      activeDataTab.value = 'extracted'
      planRisks.value = []
    } else {
      console.error('API returned no plan data')
      PopupService.error('Failed to load plan details', 'Loading Failed')
    }
  } catch (error) {
    console.error('Error fetching plan details:', error)
    PopupService.error(`Failed to load plan details: ${error.message}`, 'Loading Failed')
  } finally {
    isLoadingPlanDetails.value = false
  }
}

// Mock data functions
const getBCPMockData = () => {
  return {
    overall_score: 85,
    quality_score: 88,
    coverage_score: 82,
    recovery_capability_score: 0, // Not applicable for BCP
    compliance_score: 90,
    weighted_score: 87,
    criteria_json: {
      coverage: {
        scope_comprehensive: 85,
        rto_rpo_adequate: 80,
        critical_services_listed: 90,
        dependencies_identified: 85,
        risk_assessment_complete: 88,
        comments: {
          scope_comprehensive: "Comprehensive scope covering all critical business functions with clear boundaries and exclusions.",
          rto_rpo_adequate: "RTO/RPO targets are realistic and aligned with business requirements. Some targets could be more aggressive.",
          critical_services_listed: "All critical services are well-identified with proper prioritization and dependencies mapped.",
          dependencies_identified: "Internal and external dependencies are clearly documented with contact information.",
          risk_assessment_complete: "Thorough risk assessment covering cyber threats, natural disasters, and operational risks."
        }
      },
      quality: {
        roles_responsibilities_clear: 90,
        communication_plans_solid: 85,
        testing_procedures_adequate: 88,
        training_schedule_defined: 82,
        maintenance_review_cycle: 87,
        comments: {
          roles_responsibilities_clear: "Clear role definitions with escalation procedures and backup personnel identified.",
          communication_plans_solid: "Comprehensive communication plans for internal and external stakeholders with multiple channels.",
          testing_procedures_adequate: "Regular testing schedule with documented procedures and lessons learned tracking.",
          training_schedule_defined: "Annual training program with role-specific modules and competency assessments.",
          maintenance_review_cycle: "Quarterly reviews with annual comprehensive updates and change management process."
        }
      },
      compliance: {
        regulatory_references_align: 92,
        industry_standards_met: 88,
        bank_requirements_covered: 90,
        audit_trail_complete: 85,
        comments: {
          regulatory_references_align: "Strong alignment with SOX, Basel III, and PCI DSS requirements with regular updates.",
          industry_standards_met: "Follows ISO 22301 and FFIEC guidelines with documented compliance mapping.",
          bank_requirements_covered: "Comprehensive coverage of bank-specific regulatory requirements and internal policies.",
          audit_trail_complete: "Complete audit trail with version control and approval workflows documented."
        }
      },
      recovery: {
        recovery_capability_adequate: 0,
        backup_strategies_comprehensive: 0,
        failover_procedures_defined: 0,
        recovery_site_details: 0,
        testing_validation_schedule: 0,
        comments: {}
      }
    },
    evaluator_comments: "Overall strong BCP with comprehensive coverage of business continuity requirements. The plan demonstrates good understanding of critical business functions and has realistic recovery objectives. Areas for improvement include more aggressive RTO targets for certain services and enhanced testing frequency. The communication plans are well-structured and the regulatory compliance is excellent. Recommend approval with minor revisions to RTO targets.",
    // Yes/No radio button responses
    yes_no_responses: {
      coverage_scope_comprehensive: "yes",
      coverage_rto_rpo_adequate: "yes", 
      coverage_critical_services_listed: "yes",
      quality_roles_responsibilities_clear: "yes",
      quality_communication_plans_solid: "yes",
      compliance_regulatory: "yes",
      recovery_capability: "no" // Not applicable for BCP
    }
  }
}

const getDRPMockData = () => {
  return {
    overall_score: 88,
    quality_score: 85,
    coverage_score: 90,
    recovery_capability_score: 92,
    compliance_score: 87,
    weighted_score: 89,
    criteria_json: {
      coverage: {
        scope_comprehensive: 90,
        rto_rpo_adequate: 88,
        critical_services_listed: 92,
        dependencies_identified: 85,
        risk_assessment_complete: 87,
        comments: {
          scope_comprehensive: "Excellent scope covering all critical IT systems, applications, and infrastructure components.",
          rto_rpo_adequate: "Realistic RTO/RPO targets with clear escalation procedures and automated failover capabilities.",
          critical_services_listed: "Comprehensive identification of critical systems with proper tier classification and priority levels.",
          dependencies_identified: "Well-documented system dependencies with network diagrams and data flow mappings.",
          risk_assessment_complete: "Thorough assessment of IT risks including cyber threats, hardware failures, and data corruption scenarios."
        }
      },
      quality: {
        roles_responsibilities_clear: 88,
        communication_plans_solid: 85,
        testing_procedures_adequate: 90,
        training_schedule_defined: 87,
        maintenance_review_cycle: 89,
        comments: {
          roles_responsibilities_clear: "Clear IT team roles with defined escalation paths and backup personnel for key positions.",
          communication_plans_solid: "Effective communication protocols for IT incidents with stakeholder notification procedures.",
          testing_procedures_adequate: "Comprehensive testing program including DR drills, failover tests, and recovery validation.",
          training_schedule_defined: "Regular training for IT staff on DR procedures with hands-on exercises and simulations.",
          maintenance_review_cycle: "Monthly DR plan reviews with quarterly updates and annual comprehensive assessments."
        }
      },
      compliance: {
        regulatory_references_align: 85,
        industry_standards_met: 90,
        bank_requirements_covered: 88,
        audit_trail_complete: 87,
        comments: {
          regulatory_references_align: "Good alignment with FFIEC guidelines and SOX requirements for IT controls and data protection.",
          industry_standards_met: "Follows ISO 27001 and NIST frameworks with documented compliance mapping.",
          bank_requirements_covered: "Comprehensive coverage of banking IT requirements including data residency and security controls.",
          audit_trail_complete: "Complete audit trail with change management and approval workflows for DR procedures."
        }
      },
      recovery: {
        recovery_capability_adequate: 95,
        backup_strategies_comprehensive: 90,
        failover_procedures_defined: 88,
        recovery_site_details: 92,
        testing_validation_schedule: 87,
        comments: {
          recovery_capability_adequate: "Excellent recovery capabilities with automated failover, redundant systems, and comprehensive backup strategies.",
          backup_strategies_comprehensive: "Multi-tier backup strategy with real-time replication, daily backups, and off-site storage.",
          failover_procedures_defined: "Well-defined failover procedures with automated triggers and manual override capabilities.",
          recovery_site_details: "Detailed recovery site specifications with full infrastructure replication and connectivity options.",
          testing_validation_schedule: "Regular testing schedule with monthly DR drills and annual comprehensive recovery exercises."
        }
      }
    },
    evaluator_comments: "Outstanding DRP with excellent technical depth and comprehensive recovery capabilities. The plan demonstrates strong understanding of IT infrastructure and has realistic recovery objectives. The automated failover capabilities and backup strategies are particularly impressive. Areas for improvement include enhanced testing frequency and more detailed communication procedures. The regulatory compliance is good and the overall technical approach is sound. Recommend approval with minor enhancements to testing procedures.",
    // Yes/No radio button responses
    yes_no_responses: {
      coverage_scope_comprehensive: "yes",
      coverage_rto_rpo_adequate: "yes", 
      coverage_critical_services_listed: "yes",
      quality_roles_responsibilities_clear: "yes",
      quality_communication_plans_solid: "yes",
      compliance_regulatory: "yes",
      recovery_capability: "yes" // Applicable for DRP
    }
  }
}

const loadMockData = async () => {
  if (!selectedEvaluationData.value) {
    PopupService.warning('Please select a plan first before loading mock data.', 'No Plan Selected')
    return
  }

  const planType = selectedEvaluationData.value.plan_type
  let mockData

  if (planType === 'BCP') {
    mockData = getBCPMockData()
    console.log('Loading BCP mock data')
  } else if (planType === 'DRP') {
    mockData = getDRPMockData()
    console.log('Loading DRP mock data')
  } else {
    PopupService.warning('Unknown plan type. Please select a BCP or DRP plan.', 'Invalid Plan Type')
    return
  }

  // Load the mock data into the evaluation form
  evaluationData.value = { ...mockData }
  
  // Recalculate overall score
  calculateOverallScore()
  
  PopupService.success(`Mock data loaded for ${planType} plan. You can now review and modify the evaluation scores before saving.`, 'Mock Data Loaded')
  
  // Create notification
  await notificationService.createEvaluationNotification('mock_data_loaded', {
    plan_type: planType
  })
}
</script>

<style scoped>
/* Data Type Classification Toggle Styles */
.bcp-data-type-circle-toggle-wrapper {
  display: inline-flex !important;
  align-items: center !important;
  margin-left: 12px !important;
  padding: 4px 8px !important;
  background-color: white !important;
  border: 1px solid #e5e7eb !important;
  border-radius: 16px !important;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
  visibility: visible !important;
  opacity: 1 !important;
  position: relative !important;
  z-index: 1 !important;
  flex-shrink: 0 !important;
}

.bcp-data-type-circle-toggle {
  display: flex !important;
  align-items: center !important;
  gap: 4px !important;
  visibility: visible !important;
  opacity: 1 !important;
}

.bcp-circle-option {
  width: 14px !important;
  height: 14px !important;
  border-radius: 50% !important;
  border: 1.5px solid #d1d5db !important;
  background-color: white !important;
  cursor: pointer !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  transition: all 0.3s ease !important;
  position: relative !important;
  visibility: visible !important;
  opacity: 1 !important;
  flex-shrink: 0 !important;
}

.bcp-circle-option:hover {
  transform: scale(1.2) !important;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.12) !important;
}

.bcp-circle-inner {
  width: 0 !important;
  height: 0 !important;
  border-radius: 50% !important;
  transition: all 0.3s ease !important;
  background-color: transparent !important;
}

.bcp-circle-option.active .bcp-circle-inner {
  width: 9px !important;
  height: 9px !important;
  box-shadow: 0 0 4px rgba(0, 0, 0, 0.2) !important;
}

/* Personal Circle - Blue */
.bcp-circle-option.bcp-personal-circle {
  border: 1.5px solid #4f7cff !important;
}

.bcp-circle-option.bcp-personal-circle.active {
  border: 1.5px solid #4f7cff !important;
  background-color: rgba(79, 124, 255, 0.1) !important;
  box-shadow: 0 0 6px rgba(79, 124, 255, 0.2) !important;
}

.bcp-circle-option.bcp-personal-circle.active .bcp-circle-inner {
  background-color: #4f7cff !important;
  box-shadow: 0 0 4px rgba(79, 124, 255, 0.35) !important;
}

/* Confidential Circle - Red */
.bcp-circle-option.bcp-confidential-circle {
  border: 1.5px solid #e63946 !important;
}

.bcp-circle-option.bcp-confidential-circle.active {
  border: 1.5px solid #e63946 !important;
  background-color: rgba(230, 57, 70, 0.1) !important;
  box-shadow: 0 0 6px rgba(230, 57, 70, 0.2) !important;
}

.bcp-circle-option.bcp-confidential-circle.active .bcp-circle-inner {
  background-color: #e63946 !important;
  box-shadow: 0 0 4px rgba(230, 57, 70, 0.35) !important;
}

/* Regular Circle - Grey */
.bcp-circle-option.bcp-regular-circle {
  border: 1.5px solid #6c757d !important;
}

.bcp-circle-option.bcp-regular-circle.active {
  border: 1.5px solid #6c757d !important;
  background-color: rgba(108, 117, 125, 0.1) !important;
  box-shadow: 0 0 6px rgba(108, 117, 125, 0.2) !important;
}

.bcp-circle-option.bcp-regular-circle.active .bcp-circle-inner {
  background-color: #6c757d !important;
  box-shadow: 0 0 4px rgba(108, 117, 125, 0.35) !important;
}
</style>




