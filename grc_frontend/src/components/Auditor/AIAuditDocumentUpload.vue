<template>
  <div class="ai-audit-document-upload-page">
    <div class="audit-content">
      <h1 class="audit-title">Audit Document Upload</h1>
      <p class="audit-subtitle">Upload documents for Automated audit processing</p>

    <!-- Audit Selection Only -->
    <div class="audit-selection-section">
      <h3>Select Assigned Audit</h3>
      <div class="audit-switcher">
        <div class="custom-dropdown-container" :class="{ 'is-open': isDropdownOpen, 'has-selection': selectedExistingAuditId }">
          <div class="dropdown-trigger" @click="toggleDropdown" @blur="closeDropdown">
            <div class="dropdown-selected">
              <div class="selected-content">
                <i class="fas fa-clipboard-list dropdown-icon"></i>
                <div class="selected-text">
                  <span v-if="selectedExistingAuditId" class="selected-title">
                    {{ getSelectedAuditTitle() }}
                  </span>
                  <span v-else class="placeholder-text">Select Assigned AI Audit...</span>
                </div>
              </div>
              <i class="fas fa-chevron-down dropdown-arrow" :class="{ 'is-open': isDropdownOpen }"></i>
            </div>
          </div>
          
          <div class="dropdown-options" v-show="isDropdownOpen">
            <div class="dropdown-search" v-if="availableAIAudits.length > 5">
              <input 
                type="text" 
                v-model="searchQuery" 
                placeholder="Search audits..." 
                class="search-input"
                @click.stop
              >
              <i class="fas fa-search search-icon"></i>
            </div>
            
            <div class="options-list">
              <div 
                v-for="audit in filteredAudits" 
                :key="audit.audit_id" 
                class="dropdown-option"
                :class="{ 'is-selected': selectedExistingAuditId === audit.audit_id }"
                @click="selectAudit(audit)"
              >
                <div class="option-content">
                  <div class="option-header">
                    <span class="option-title">{{ audit.title || 'Audit' }}</span>
                    <span class="option-id">ID: {{ audit.audit_id }}</span>
                  </div>
                  <div class="option-meta">
                    <span class="option-due-date">
                      <i class="fas fa-calendar-alt"></i>
                      Due: {{ audit.duedate || audit.due_date || 'N/A' }}
                    </span>
                    <span class="option-type" :class="audit.audit_type?.toLowerCase()">
                      {{ audit.audit_type || 'AI' }}
                    </span>
                  </div>
                </div>
                <i v-if="selectedExistingAuditId === audit.audit_id" class="fas fa-check option-check"></i>
              </div>
              
              <div v-if="filteredAudits.length === 0" class="no-options">
                <i class="fas fa-search"></i>
                <span>No audits found matching "{{ searchQuery }}"</span>
              </div>
              
              <div v-if="!isLoadingAudits && availableAIAudits.length === 0" class="no-options">
                <i class="fas fa-exclamation-triangle"></i>
                <span>No assigned AI audits found</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      <p v-if="!hasSelectedAudit" class="hint-text">Choose an assigned AI audit to start uploading documents.</p>
      <p v-if="auditLoadError" class="error-text">{{ auditLoadError }}</p>
    </div>

    <!-- Audit Information (Only shown after selection) -->
    <div v-if="hasSelectedAudit" class="audit-info-section">
      <h3>{{ auditInfo.title || 'Audit Information' }}</h3>
      <div class="audit-meta">
        <span class="audit-id">Audit ID: {{ currentAuditId }}</span>
        <span class="audit-type">{{ auditInfo.type || 'AI Audit' }}</span>
        <span class="framework">{{ auditInfo.framework || 'Framework' }}</span>
      </div>
      
      <!-- SEBI AI Auditor Insights -->
      <div v-if="sebiEnabled" class="sebi-insights-section">
        <div class="sebi-insights-header">
          <h4><i class="fas fa-chart-line"></i> SEBI Compliance Insights</h4>
          <span v-if="isLoadingSEBI" class="loading-text">Loading...</span>
        </div>
        
        <div v-if="!isLoadingSEBI" class="sebi-insights-grid">
          <!-- Filing Accuracy -->
          <div v-if="sebiInsights.filingAccuracy" class="sebi-insight-card">
            <div class="insight-header">
              <i class="fas fa-file-check"></i>
              <span>Filing Accuracy</span>
            </div>
            <div class="insight-value">
              <span class="score">{{ (sebiInsights.filingAccuracy.overall_score * 100).toFixed(1) }}%</span>
            </div>
            <div v-if="sebiInsights.filingAccuracy.arithmetic_errors?.length > 0" class="insight-warning">
              <i class="fas fa-exclamation-triangle"></i>
              {{ sebiInsights.filingAccuracy.arithmetic_errors.length }} arithmetic error(s)
            </div>
          </div>
          
          <!-- Timeliness SLA -->
          <div v-if="sebiInsights.timelinessSLA" class="sebi-insight-card" 
               :class="{ 'sla-breach': sebiInsights.timelinessSLA.sla_breach }">
            <div class="insight-header">
              <i class="fas fa-clock"></i>
              <span>Timeliness SLA</span>
            </div>
            <div v-if="sebiInsights.timelinessSLA.sla_breach" class="insight-value">
              <span class="breach">
                <i class="fas fa-exclamation-circle"></i>
                {{ sebiInsights.timelinessSLA.days_delayed || sebiInsights.timelinessSLA.hours_delayed }} 
                {{ sebiInsights.timelinessSLA.days_delayed ? 'days' : 'hours' }} delayed
              </span>
            </div>
            <div v-else class="insight-value">
              <span class="on-time"><i class="fas fa-check-circle"></i> On Time</span>
            </div>
            <div v-if="sebiInsights.timelinessSLA.severity" class="insight-severity" 
                 :class="'severity-' + sebiInsights.timelinessSLA.severity">
              Severity: {{ sebiInsights.timelinessSLA.severity }}
            </div>
          </div>
          
          <!-- Risk Score -->
          <div v-if="sebiInsights.riskScore" class="sebi-insight-card"
               :class="{ 'risk-high': sebiInsights.riskScore.risk_level === 'High' }">
            <div class="insight-header">
              <i class="fas fa-exclamation-triangle"></i>
              <span>Risk Score</span>
            </div>
            <div class="insight-value">
              <span class="risk-level" :class="'risk-' + sebiInsights.riskScore.risk_level.toLowerCase()">
                {{ sebiInsights.riskScore.risk_score }} ({{ sebiInsights.riskScore.risk_level }})
              </span>
            </div>
            <div v-if="sebiInsights.riskScore.factors" class="insight-factors">
              <div v-for="(factor, key) in sebiInsights.riskScore.factors" :key="key" class="factor-item">
                <span class="factor-name">{{ key.replace('_', ' ') }}:</span>
                <span class="factor-count">{{ factor.count || 0 }}</span>
              </div>
            </div>
          </div>
          
          <!-- Patterns -->
          <div v-if="sebiInsights.patterns" class="sebi-insight-card">
            <div class="insight-header">
              <i class="fas fa-search"></i>
              <span>Behavioral Patterns</span>
            </div>
            <div v-if="sebiInsights.patterns.frequent_last_day_filings?.length > 0" class="insight-pattern">
              <i class="fas fa-calendar-times"></i>
              {{ sebiInsights.patterns.frequent_last_day_filings.length }} last-day filing(s) detected
            </div>
            <div v-if="sebiInsights.patterns.recurring_disclosure_edits?.length > 0" class="insight-pattern">
              <i class="fas fa-edit"></i>
              {{ sebiInsights.patterns.recurring_disclosure_edits.length }} recurring edit(s) detected
            </div>
            <div v-if="(!sebiInsights.patterns.frequent_last_day_filings?.length && 
                       !sebiInsights.patterns.recurring_disclosure_edits?.length)" 
                 class="insight-pattern">
              <i class="fas fa-check"></i> No significant patterns detected
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Suggested Documents Section - Hidden since we now do automatic processing -->
    <div v-if="false && hasSelectedAudit" class="suggested-documents-container">
      <div class="suggested-documents-header" @click="toggleSuggestedDocuments">
        <div class="header-left">
          <div>
            <h3>Suggested Documents</h3>
            <p class="header-subtitle">
              {{ relevantDocuments.length }} document{{ relevantDocuments.length !== 1 ? 's' : '' }} found based on AI analysis
            </p>
          </div>
        </div>
        <div class="header-right">
          <span v-if="selectedRelevantDocuments.length > 0" class="selection-count">
            {{ selectedRelevantDocuments.length }} selected
          </span>
          <i class="fas fa-chevron-down expand-icon" :class="{ 'expanded': showSuggestedDocuments }"></i>
        </div>
      </div>
      
      <div v-show="showSuggestedDocuments" class="suggested-documents-content">
        <div v-if="isLoadingRelevantDocuments" class="loading-state">
          <i class="fas fa-spinner fa-spin"></i>
          <span>Loading relevant documents...</span>
        </div>
        
        <div v-else-if="relevantDocuments.length > 0" class="documents-grid">
          <div class="documents-actions-bar">
            <div class="action-buttons-left">
              <button 
                @click="uploadSelectedRelevantDocuments" 
                class="btn btn-primary"
                :disabled="selectedRelevantDocuments.length === 0 || isUploadingRelevantDocuments"
                :title="selectedRelevantDocuments.length === 0 ? 'Please select at least one document' : 'Click to upload selected documents'"
              >
                <i class="fas" :class="isUploadingRelevantDocuments ? 'fa-spinner fa-spin' : 'fa-upload'"></i>
                {{ isUploadingRelevantDocuments ? 'Uploading...' : `Upload Selected (${selectedRelevantDocuments.length})` }}
              </button>
              <button 
                @click="selectAllRelevantDocuments" 
                class="btn btn-outline"
                v-if="selectedRelevantDocuments.length < relevantDocuments.length"
              >
                <i class="fas fa-check-square"></i>
                Select All
              </button>
              <button 
                @click="deselectAllRelevantDocuments" 
                class="btn btn-outline"
                v-if="selectedRelevantDocuments.length > 0"
              >
                <i class="fas fa-square"></i>
                Deselect All
              </button>
            </div>
            <div class="action-instructions">
              <p><strong>How it works:</strong> 
                <span v-if="selectedRelevantDocuments.length === 0">
                  Select documents using checkboxes, then click "Upload Selected" to add them to this audit. Each document shows which policies, sub-policies, and compliances it's relevant for based on AI analysis.
                </span>
                <span v-else>
                  Ready to upload! Click "Upload Selected" to add {{ selectedRelevantDocuments.length }} document(s) to this audit. The documents will appear in your uploaded documents list below. Each document's relevance to specific policies, sub-policies, and compliances is shown in the document details.
                </span>
              </p>
            </div>
          </div>
          
          <div class="document-cards-grid">
            <div 
              class="document-card" 
              v-for="doc in relevantDocuments" 
              :key="doc.file_operation_id"
              :class="{ 'selected': selectedRelevantDocuments.includes(doc.file_operation_id) }"
            >
              <div class="card-checkbox-wrapper">
                <input 
                  type="checkbox" 
                  :id="'doc-checkbox-' + doc.file_operation_id"
                  :value="doc.file_operation_id"
                  :checked="selectedRelevantDocuments.includes(doc.file_operation_id)"
                  @change="toggleRelevantDocumentSelection(doc.file_operation_id)"
                  @click.stop
                />
                <label :for="'doc-checkbox-' + doc.file_operation_id" class="checkbox-label"></label>
              </div>
              
              <div class="card-content" @click="toggleDocumentDetails(doc.file_operation_id)">
                <div class="card-header">
              <div class="file-icon-wrapper">
                <i class="fas file-icon" :class="getFileIcon(doc.file_type)"></i>
              </div>
                  <div class="file-info">
                    <h4 class="file-name" :title="doc.file_name || doc.original_name">
                      {{ (doc.file_name || doc.original_name).substring(0, 50) }}{{ (doc.file_name || doc.original_name).length > 50 ? '...' : '' }}
                    </h4>
                    <div class="file-meta">
                      <span class="file-type">{{ doc.file_type }}</span>
                      <span class="file-size">{{ formatFileSize(doc.file_size) }}</span>
                      <span class="file-date">{{ formatDate(doc.created_at) }}</span>
                    </div>
                  </div>
                  <div class="relevance-score">
                    <span class="relevance-badge" :class="getRelevanceClass(doc.relevance_score)">
                      {{ Math.round(doc.relevance_score * 100) }}%
                    </span>
                  </div>
                </div>
                
                <div v-if="expandedDocumentId === doc.file_operation_id" class="card-details">
                  <div class="detail-section" v-if="doc.summary">
                    <h5><i class="fas fa-align-left"></i> Document Overview</h5>
                    <p>{{ doc.summary }}</p>
                  </div>
                  
                  <div class="detail-section relevance-reason" v-if="doc.relevance_reason">
                    <h5><i class="fas fa-info-circle"></i> Why relevant</h5>
                    <p>{{ doc.relevance_reason }}</p>
                  </div>
                  
                  <div class="detail-section matched-items" v-if="(doc.matched_policies_with_names && doc.matched_policies_with_names.length > 0) || 
                                                                 (doc.matched_subpolicies_with_names && doc.matched_subpolicies_with_names.length > 0) || 
                                                                 (doc.matched_compliances_with_names && doc.matched_compliances_with_names.length > 0)">
                    <h5><i class="fas fa-link"></i> Matched Framework Elements</h5>
                    <div v-if="doc.matched_policies_with_names && doc.matched_policies_with_names.length > 0" class="matched-group">
                      <strong><i class="fas fa-shield-alt"></i> Policies:</strong>
                      <div class="tags-container">
                        <span class="matched-tag" v-for="policy in doc.matched_policies_with_names" :key="'policy-' + policy.id">
                          {{ policy.name }} <span class="tag-id">(ID: {{ policy.id }})</span>
                        </span>
                      </div>
                    </div>
                    <div v-if="doc.matched_subpolicies_with_names && doc.matched_subpolicies_with_names.length > 0" class="matched-group">
                      <strong><i class="fas fa-list"></i> Subpolicies:</strong>
                      <div class="tags-container">
                        <span class="matched-tag" v-for="subpolicy in doc.matched_subpolicies_with_names" :key="'subpolicy-' + subpolicy.id">
                          {{ subpolicy.name }} <span class="tag-id">(ID: {{ subpolicy.id }})</span>
                        </span>
                      </div>
                    </div>
                    <div v-if="doc.matched_compliances_with_names && doc.matched_compliances_with_names.length > 0" class="matched-group">
                      <strong><i class="fas fa-check-circle"></i> Compliances:</strong>
                      <div class="tags-container">
                        <span class="matched-tag" v-for="compliance in doc.matched_compliances_with_names" :key="'compliance-' + compliance.id">
                          {{ compliance.name }} <span class="tag-id">(ID: {{ compliance.id }})</span>
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div class="card-footer">
                  <button class="btn btn-outline btn-sm" @click.stop="toggleDocumentDetails(doc.file_operation_id)">
                    <i class="fas" :class="expandedDocumentId === doc.file_operation_id ? 'fa-chevron-up' : 'fa-chevron-down'"></i>
                    {{ expandedDocumentId === doc.file_operation_id ? 'Hide Details' : 'View Details' }}
                  </button>
                  <a :href="doc.s3_url" target="_blank" class="btn btn-outline btn-sm" @click.stop>
                    <i class="fas fa-download"></i>
                    Download
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div v-else class="no-documents-message">
          <i class="fas fa-inbox"></i>
          <p>No relevant documents found</p>
          <span>{{ relevantDocumentsMessage || 'Upload documents in Document Handling to see AI-suggested documents here.' }}</span>
          <div v-if="relevantDocumentsStats" class="stats-info" style="margin-top: 10px; font-size: 0.85em; color: #666; padding: 8px; background: #f5f5f5; border-radius: 4px;">
            <div v-if="relevantDocumentsStats.total_files_in_framework > 0" style="margin: 4px 0;">
              📊 {{ relevantDocumentsStats.total_files_in_framework }} document(s) in Document Handling for this framework
            </div>
            <div v-if="relevantDocumentsStats.completed_files_in_framework > 0" style="margin: 4px 0;">
              ✅ {{ relevantDocumentsStats.completed_files_in_framework }} completed
            </div>
            <div v-if="relevantDocumentsStats.documents_analyzed_for_audit > 0" style="margin: 4px 0;">
              🔍 {{ relevantDocumentsStats.documents_analyzed_for_audit }} analyzed for this audit
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Document Upload Section -->
    <div v-if="hasSelectedAudit" class="upload-section">
      <h3>Documents Used for Audit</h3>
      <p class="upload-description">
        Documents automatically processed for this audit. Documents uploaded via Document Handling are automatically analyzed and linked to this audit when relevant.
      </p>

      <!-- Multi-select for Policies / Sub-policies / Compliances -->
      <!-- Show whenever an audit is selected; inner lists handle empty states -->
      <div class="multi-mapping-container" v-if="hasSelectedAudit">
          <h4 class="multi-mapping-title">Select scope for this AI audit upload (Optional)</h4>
          <p class="multi-mapping-help">
            <strong>Optional:</strong> Choose one or more <strong>policies</strong>, their <strong>sub‑policies</strong> and specific
            <strong>compliances</strong> to explicitly map uploaded documents. If not selected, AI will automatically analyze 
            document relevance to all framework elements. Documents will show which policies, sub-policies, and compliances 
            they're relevant for based on AI analysis.
          </p>

          <div class="multi-mapping-columns">
            <!-- Policies column -->
            <div class="multi-column">
              <div class="multi-column-header">
                <span>Policies in this framework</span>
                <label class="select-all-label">
                  <input
                    type="checkbox"
                    :checked="allPoliciesSelected"
                    @change="toggleSelectAllPolicies"
                  />
                  <span>Select all</span>
                </label>
              </div>
              <div class="multi-column-list">
                <label
                  v-for="policy in auditHierarchyPolicies"
                  :key="policy.policy_id"
                  class="multi-checkbox-row"
                >
                  <input
                    type="checkbox"
                    :value="policy.policy_id"
                    v-model="selectedPolicyIdsMulti"
                    @change="onPolicyMultiChange(policy.policy_id)"
                  />
                  <span class="multi-checkbox-label">{{ policy.policy_name }}</span>
                </label>
                <div v-if="!auditHierarchyPolicies.length" class="empty-text">
                  No policies found for this audit.
                </div>
              </div>
            </div>

            <!-- Sub‑policies column -->
            <div class="multi-column">
              <div class="multi-column-header">
                <span>Sub‑policies</span>
                <label class="select-all-label">
                  <input
                    type="checkbox"
                    :checked="allSubpoliciesSelected"
                    @change="toggleSelectAllSubpolicies"
                    :disabled="!availableSubpolicies.length"
                  />
                  <span>Select all</span>
                </label>
              </div>
              <div class="multi-column-list">
                <label
                  v-for="sub in availableSubpolicies"
                  :key="sub.subpolicy_id"
                  class="multi-checkbox-row"
                >
                  <input
                    type="checkbox"
                    :value="sub.subpolicy_id"
                    v-model="selectedSubpolicyIdsMulti"
                    @change="onSubpolicyMultiChange(sub.subpolicy_id, sub.policy_id)"
                  />
                  <span class="multi-checkbox-label">
                    {{ sub.subpolicy_name }}
                    <span class="multi-subpolicy-policy">({{ sub.policy_name }})</span>
                  </span>
                </label>
                <div v-if="!availableSubpolicies.length" class="empty-text">
                  Select at least one policy to see its sub‑policies.
                </div>
              </div>
            </div>

            <!-- Compliances column -->
            <div class="multi-column">
              <div class="multi-column-header">
                <span>Compliances</span>
                <label class="select-all-label">
                  <input
                    type="checkbox"
                    :checked="allCompliancesSelected"
                    @change="toggleSelectAllCompliances"
                    :disabled="!availableCompliances.length"
                  />
                  <span>Select all</span>
                </label>
              </div>
              <div class="multi-column-list">
                <label
                  v-for="comp in availableCompliances"
                  :key="comp.compliance_id"
                  class="multi-checkbox-row"
                >
                  <input
                    type="checkbox"
                    :value="comp.compliance_id"
                    v-model="selectedComplianceIds"
                  />
                  <span class="multi-checkbox-label">
                    {{ comp.description || comp.compliance_title || ('Compliance ' + comp.compliance_id) }}
                    <span class="multi-subpolicy-policy">
                      ({{ comp.policy_name }} › {{ comp.subpolicy_name }})
                    </span>
                  </span>
                </label>
                <div v-if="!availableCompliances.length" class="empty-text">
                  Select at least one policy or sub‑policy to see compliances.
                </div>
              </div>
            </div>
          </div>

          <p class="multi-mapping-summary">
            <strong>Current selection:</strong>
            {{ selectedPolicyIdsMulti.length }} policies,
            {{ selectedSubpolicyIdsMulti.length }} sub‑policies,
            {{ selectedComplianceIds.length }} compliances.
          </p>
        </div>

        <!-- Compliance Requirements Display (disabled) -->
        <div class="compliance-requirements" v-if="false">
          <h4>Compliance Requirements</h4>
          <div v-if="complianceRequirements.length > 0" class="requirements-list">
            <div v-for="req in complianceRequirements" :key="req.compliance_id" class="requirement-item">
              <div class="requirement-header">
                <span class="requirement-title">{{ req.compliance_title }}</span>
                <span class="requirement-type" :class="req.compliance_type.toLowerCase()">
                  {{ req.compliance_type }}
                </span>
              </div>
              <p class="requirement-description">{{ req.compliance_description }}</p>
              <div class="requirement-meta">
                <span class="risk-level" :class="req.risk_level.toLowerCase()">
                  {{ req.risk_level }} Risk
                </span>
                <span v-if="req.mandatory" class="mandatory">Mandatory</span>
              </div>
            </div>
          </div>
          <div v-else class="no-requirements">
            <p v-if="complianceRequirements.length === 0">
              No compliance requirements configured for this policy yet.
            </p>
          </div>
        </div>

      <!-- File Upload Area -->
      <div class="file-upload-area" @click="triggerFileUpload" @dragover.prevent @drop.prevent="handleDrop">
        <input 
          ref="fileInput" 
          type="file" 
          multiple 
          @change="handleFileSelect" 
          accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.csv,.json"
          style="display: none;"
        >
        <div class="upload-content" :class="{ 'dragover': isDragOver }">
          <i class="fas fa-cloud-upload-alt upload-icon"></i>
          <h4>Drop files here or click to browse</h4>
          <p>Supported formats: PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX, TXT, CSV, JSON</p>
          <p class="file-limit">Maximum file size: 100MB per file</p>
        </div>
      </div>

      <!-- Selected Files Preview -->
      <div v-if="selectedFiles.length > 0" class="selected-files">
        <h4>Selected Files ({{ selectedFiles.length }})</h4>
        <div class="file-list">
          <div v-for="(file, index) in selectedFiles" :key="index" class="file-item">
            <div class="file-info">
              <i class="fas fa-file file-icon"></i>
              <div class="file-details">
                <span class="file-name">{{ file.name }}</span>
                <span class="file-size">{{ formatFileSize(file.size) }}</span>
              </div>
            </div>
            <button @click="removeFile(index)" class="remove-btn">
              <i class="fas fa-times"></i>
            </button>
          </div>
        </div>
      </div>

      <!-- Upload Progress -->
      <div v-if="uploading" class="upload-progress">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: uploadProgress + '%' }"></div>
        </div>
        <p class="progress-text">Uploading... {{ uploadProgress }}%</p>
      </div>

      <!-- Upload Actions -->
      <div class="upload-actions">
        <button 
          @click="uploadFiles" 
          :disabled="selectedFiles.length === 0 || uploading"
          class="btn btn-primary upload-btn"
          @mousedown="console.log('🔍 Upload button mousedown')"
        >
          <i class="fas fa-upload"></i>
          Upload {{ selectedFiles.length }} File(s)
        </button>
        <button @click="clearFiles" class="btn btn-secondary" :disabled="selectedFiles.length === 0">
          Clear All
        </button>
      </div>
    </div>

    <!-- Smart Compliance Selection Interface (disabled) -->
    <div v-if="false && showComplianceSelection" class="compliance-selection-section">
      <h3>📋 Smart Compliance Analysis</h3>
      <p class="selection-description">
        AI has analyzed your uploaded documents and suggests the most relevant compliance requirements to check. 
        Select which compliance requirements you want to process for AI audit:
      </p>
      
      <div v-for="mapping in documentComplianceMapping" :key="mapping.document_id" class="document-mapping">
        <h4>📄 {{ mapping.document_name }}</h4>
        
        <!-- High Relevance Suggestions -->
        <div v-if="mapping.suggested_compliances.filter(s => s.relevance_score >= 0.6).length > 0" class="suggestions high-relevance">
          <h5>🎯 Highly Relevant (Recommended)</h5>
          <div class="compliance-suggestions">
            <div v-for="suggestion in mapping.suggested_compliances.filter(s => s.relevance_score >= 0.6)" 
                 :key="suggestion.compliance_id" 
                 class="suggestion-item high">
              <label class="suggestion-checkbox">
                <input type="checkbox" 
                       :value="suggestion.compliance_id" 
                       v-model="selectedComplianceIds"
                       :id="`compliance-${suggestion.compliance_id}`">
                <span class="checkmark"></span>
                <div class="suggestion-content">
                  <span class="compliance-title">{{ suggestion.compliance_title }}</span>
                  <span class="relevance-score">{{ Math.round(suggestion.relevance_score * 100) }}% match</span>
                  <span class="relevance-reason">{{ suggestion.relevance_reason }}</span>
                </div>
              </label>
            </div>
          </div>
        </div>
        
        <!-- Medium Relevance Suggestions -->
        <div v-if="mapping.suggested_compliances.filter(s => s.relevance_score >= 0.4 && s.relevance_score < 0.6).length > 0" class="suggestions medium-relevance">
          <h5>⚠️ Possibly Relevant</h5>
          <div class="compliance-suggestions">
            <div v-for="suggestion in mapping.suggested_compliances.filter(s => s.relevance_score >= 0.4 && s.relevance_score < 0.6)" 
                 :key="suggestion.compliance_id" 
                 class="suggestion-item medium">
              <label class="suggestion-checkbox">
                <input type="checkbox" 
                       :value="suggestion.compliance_id" 
                       v-model="selectedComplianceIds"
                       :id="`compliance-${suggestion.compliance_id}`">
                <span class="checkmark"></span>
                <div class="suggestion-content">
                  <span class="compliance-title">{{ suggestion.compliance_title }}</span>
                  <span class="relevance-score">{{ Math.round(suggestion.relevance_score * 100) }}% match</span>
                  <span class="relevance-reason">{{ suggestion.relevance_reason }}</span>
                </div>
              </label>
            </div>
          </div>
        </div>
        
        <!-- No Suggestions -->
        <div v-if="mapping.suggested_compliances.length === 0" class="no-suggestions">
          <p>🤔 No highly relevant compliance requirements found for this document. You may need to upload a different document or manually select compliance requirements.</p>
        </div>
      </div>
      
      <!-- Action Buttons -->
      <div class="selection-actions">
        <button @click="proceedWithSelectedCompliances" 
                :disabled="selectedComplianceIds.length === 0"
                class="btn btn-primary">
          📊 Start AI Processing ({{ selectedComplianceIds.length }} selected)
        </button>
        <button @click="selectAllCompliances" class="btn btn-outline">
          ✅ Select All Compliance Requirements
        </button>
        <button @click="cancelSelection" class="btn btn-outline">
          ❌ Cancel Selection
        </button>
      </div>
      
      <!-- Selected Count Summary -->
      <div v-if="selectedComplianceIds.length > 0" class="selection-summary">
        <p><strong>Selected:</strong> {{ selectedComplianceIds.length }} compliance requirement(s) for AI processing</p>
      </div>
    </div>

    <!-- Uploaded Documents List: Physical Documents -->
    <div v-if="fileDocuments.length > 0" class="uploaded-documents">
      <div class="uploaded-documents-header">
        <h3>Documents Used for Audit</h3>
        <div style="display: flex; gap: 8px;">
          <button
            class="btn btn-sm btn-danger"
            @click="deleteAllDocuments"
            :disabled="bulkDeleting || fileDocuments.length === 0"
          >
            <i class="fas fa-trash"></i>
            {{ bulkDeleting ? 'Deleting...' : 'Delete All' }}
          </button>
          <button
            class="btn btn-sm btn-primary"
            @click="checkAllDocumentsCompliance"
            :disabled="bulkChecking || fileDocuments.length === 0"
          >
            <i class="fas fa-robot"></i>
            {{ bulkChecking ? 'Checking all...' : 'Check All' }}
          </button>
        </div>
      </div>
      <div class="documents-grid">
        <div v-for="(fileGroup, fileIndex) in fileDocuments" :key="fileIndex" class="document-card">
          <div class="document-content">
            <div class="document-main">
              <i class="fas fa-file document-icon"></i>
              <div class="document-info">
                <h4 :title="fileGroup.document_name">{{ fileGroup.document_name }}</h4>
                <p class="document-meta">
                  {{ formatFileSize(fileGroup.file_size) }} • {{ fileGroup.uploaded_date }}
                </p>
              </div>
            </div>
            
            <div class="document-type">
              <span><strong>Type:</strong> {{ fileGroup.document_type }}</span>
            </div>
            
            <!-- Mappings Display (Always show all) -->
            <div class="mappings-list">
              <label style="display: block; margin-bottom: 6px; font-weight: 600; font-size: 13px; color: #495057;">
                Mappings ({{ fileGroup.mappings.length }}):
              </label>
              <div class="mappings-badges">
                <span 
                  v-for="(mapping, mapIndex) in fileGroup.mappings" 
                  :key="mapIndex" 
                  class="mapping-badge"
                  :title="mapping.mapping_display"
                >
                  {{ mapping.mapping_display }}
                </span>
              </div>
            </div>
            
            <!-- Show aggregated status for all mappings -->
            <div class="document-status">
              <span v-if="areAllMappingsCompleted(fileGroup)" class="status-badge completed">
                COMPLETED
              </span>
              <span v-else-if="fileGroup.mappings.some(m => m.processing_status === 'processing')" class="status-badge processing">
                PROCESSING
              </span>
              <span v-else class="status-badge pending">
                PENDING
              </span>
              <span 
                v-if="areAllMappingsCompleted(fileGroup) && getAggregatedComplianceStatus(fileGroup)" 
                :class="['status-badge', 'compliance', getAggregatedComplianceStatus(fileGroup).toLowerCase()]" 
                style="margin-left:6px;"
              >
                {{ getAggregatedComplianceStatus(fileGroup).toUpperCase() }}
                <span v-if="getAggregatedConfidenceScore(fileGroup)">
                  ({{ Math.round(getAggregatedConfidenceScore(fileGroup) * 100) }}%)
                </span>
              </span>
            </div>
            
            <div class="document-actions">
              <button 
                v-if="fileGroup.document_id" 
                @click="deleteDocument(fileGroup.document_id)" 
                class="btn btn-sm btn-danger"
              >
                <i class="fas fa-trash"></i> Delete
              </button>
             <!-- Show Check button only if no completed mappings yet AND not showing Details button -->
              <button 
                v-if="!areAllMappingsCompleted(fileGroup) && !shouldShowDetailsButton(fileGroup)"
                @click="checkDocumentCompliance(null, fileGroup)" 
                class="btn btn-sm btn-primary" 
                :disabled="isCheckingAnyMapping(fileGroup)"
              >
                <i v-if="isCheckingAnyMapping(fileGroup)" class="fas fa-spinner fa-spin"></i>
                <i v-else class="fas fa-robot"></i>
                {{ isCheckingAnyMapping(fileGroup) ? 'Checking...' : 'Check' }}
              </button>
              <!-- Show Details button as soon as at least one mapping is completed (replaces Check button) -->
              <!-- For combined checks, only show button on the primary fileGroup -->
              <button 
                v-if="shouldShowDetailsButton(fileGroup)" 
                @click="showAllMappingsDetails(fileGroup)" 
                class="btn btn-sm btn-primary"
                :title="isPartOfCombinedCheckGroup(fileGroup) ? `Combined check with ${getCombinedCheckGroup(fileGroup).length} document(s)` : getMappingsTooltip(fileGroup)"
              >
                <i class="fas fa-list"></i> Details
                <span v-if="isPartOfCombinedCheckGroup(fileGroup)" class="combined-badge">
                  ({{ getCombinedCheckGroup(fileGroup).length }} docs)
                </span>
              </button>
            </div>
            
          </div>
        </div>
      </div>
      </div>
    </div>

    <!-- Additional Evidence List - REMOVED per user request -->

    <!-- AI Processing Status (disabled) -->
    <div v-if="false && hasSelectedAudit && processingStatus" class="ai-processing-status">
      <h3>🤖 AI Processing Status</h3>
      <div class="processing-card">
        <div class="processing-progress">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: processingStatus.progress_percentage + '%' }"></div>
          </div>
          <p class="progress-text">
            {{ processingStatus.completed }} of {{ processingStatus.total_documents }} documents processed
            ({{ processingStatus.progress_percentage }}%)
          </p>
        </div>
        
        <div class="processing-details">
          <div class="status-item">
            <span class="status-label">Pending:</span>
            <span class="status-value">{{ processingStatus.pending }}</span>
          </div>
          <div class="status-item">
            <span class="status-label">Processing:</span>
            <span class="status-value">{{ processingStatus.processing }}</span>
          </div>
          <div class="status-item">
            <span class="status-label">Completed:</span>
            <span class="status-value">{{ processingStatus.completed }}</span>
          </div>
          <div class="status-item">
            <span class="status-label">Failed:</span>
            <span class="status-value">{{ processingStatus.failed }}</span>
          </div>
        </div>
        
        <div class="ai-info">
          <p class="ai-note">
            <i class="fas fa-robot"></i>
            Using Ollama (local AI) for intelligent document analysis and compliance assessment
            <span class="ai-benefits">• Private • Free • No API limits • Offline capable</span>
          </p>
        </div>
      </div>
    </div>

    <!-- AI Processing Results (disabled) -->
    <div v-if="false && hasSelectedAudit && aiProcessingResults.length > 0" class="ai-processing-results">
      <h3>🤖 AI Processing Results</h3>
      <div class="results-grid">
        <div v-for="result in aiProcessingResults" :key="result.document_id" class="result-card">
          <div class="result-header">
            <h4>{{ result.document_name || 'Unknown Document' }}</h4>
            <span :class="['compliance-status', result.compliance_status || 'unknown']">
              {{ (result.compliance_status || 'unknown').replace('_', ' ').toUpperCase() }}
            </span>
          </div>
          
          <div class="result-details">
            <div class="ai-metrics">
              <div class="metric-item">
                <span class="metric-label">AI Confidence:</span>
                <span class="metric-value">{{ Math.round((result.confidence_score || 0) * 100) }}%</span>
              </div>
              <div class="metric-item">
                <span class="metric-label">Risk Level:</span>
                <span :class="['risk-level', result.risk_level || 'medium']">{{ (result.risk_level || 'medium').toUpperCase() }}</span>
              </div>
              <div class="metric-item">
                <span class="metric-label">Text Length:</span>
                <span class="metric-value">{{ result.processing_results?.text_length || 0 }} chars</span>
              </div>
            </div>
            
            <div class="ai-analysis">
              <h5>📊 AI Analysis</h5>
              <p><strong>Document Type:</strong> {{ result.compliance_mapping?.document_type_detected || 'Unknown' }}</p>
              <p><strong>Found Keywords:</strong> {{ result.compliance_mapping?.found_keywords ? result.compliance_mapping.found_keywords.join(', ') : 'None detected' }}</p>
              <p><strong>Analysis Time:</strong> {{ result.compliance_mapping?.analysis_timestamp ? new Date(result.compliance_mapping.analysis_timestamp).toLocaleString() : 'Unknown' }}</p>
            </div>
            
            <div class="ai-recommendations">
              <h5>💡 AI Recommendations</h5>
              <p>{{ result.ai_recommendations || 'No recommendations available' }}</p>
            </div>
            
            <div class="extracted-text" v-if="result.extracted_text">
              <h5>📄 Extracted Text Preview</h5>
              <div class="text-preview">
                {{ result.extracted_text }}
              </div>
            </div>
          </div>
          
          <div class="result-actions">
            <button @click="reviewAIResult(result)" class="btn btn-sm btn-primary">
              <i class="fas fa-eye"></i> Review Details
            </button>
            <button @click="downloadAIReport(result)" class="btn btn-sm btn-secondary">
              <i class="fas fa-download"></i> Download Report
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Enhanced Details Section - At Bottom of Page -->
    <div v-if="selectedDocumentForDetails" class="compliance-details-expanded">
      <!-- Close Button -->
      <div class="details-header">
        <h3><i class="fas fa-list-alt"></i> Compliance Analysis Details</h3>
        <div class="details-actions">
          <button @click="downloadAuditReport()" class="btn btn-sm btn-secondary">
            <i class="fas fa-download"></i> Download Report
          </button>
          <button @click="selectedDocumentForDetails = null" class="btn btn-sm btn-outline">
            <i class="fas fa-times"></i> Close
          </button>
        </div>
      </div>
      
      <!-- Overall Status Card -->
      <div class="overall-status-card">
        <div class="status-header">
          <h4><i class="fas fa-shield-alt"></i> Overall Compliance Status</h4>
          <div class="status-badges">
            <span :class="['compliance-status-badge', selectedDocumentForDetails.compliance_status || 'unknown']">
              {{ (selectedDocumentForDetails.compliance_status || 'unknown').replace('_',' ').toUpperCase() }}
            </span>
            <span v-if="selectedDocumentForDetails.confidence_score" class="confidence-badge">
              <i class="fas fa-chart-line"></i> {{ Math.round((selectedDocumentForDetails.confidence_score||0)*100) }}% Confidence
            </span>
          </div>
        </div>
        
        <div class="status-summary">
          <div class="summary-item">
            <i class="fas fa-file-alt"></i>
            <span>Document: {{ selectedDocumentForDetails.document_name }}</span>
          </div>
          <div v-if="selectedDocumentForDetails.isCombinedCheck && selectedDocumentForDetails.combinedDocuments" class="summary-item" style="background-color: #e3f2fd; padding: 8px; border-radius: 4px; margin-top: 8px;">
            <i class="fas fa-link"></i>
            <strong>Combined Check:</strong> This analysis includes evidence from {{ selectedDocumentForDetails.combinedDocuments.length }} document(s):
            <ul style="margin: 4px 0 0 20px; padding: 0;">
              <li v-for="(doc, idx) in selectedDocumentForDetails.combinedDocuments" :key="idx" style="margin: 2px 0;">
                {{ doc.document_name }}
              </li>
            </ul>
          </div>
          <div v-if="selectedDocumentForDetails.isAllMappings" class="summary-item">
            <i class="fas fa-layer-group"></i>
            <span>{{ selectedDocumentForDetails.mappings?.length || 0 }} Mapping(s) Analyzed</span>
          </div>
          <div v-else>
            <div class="summary-item" v-if="selectedDocumentForDetails.mapped_policy">
              <i class="fas fa-gavel"></i>
              <span>Policy: {{ selectedDocumentForDetails.mapped_policy }}</span>
            </div>
            <div class="summary-item" v-if="selectedDocumentForDetails.mapped_subpolicy">
              <i class="fas fa-list"></i>
              <span>Sub-policy: {{ selectedDocumentForDetails.mapped_subpolicy }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Detailed Analysis Section -->
      <div v-if="selectedDocumentForDetails.compliance_analyses && selectedDocumentForDetails.compliance_analyses.length" class="detailed-analysis">
        <div class="analysis-header">
          <h4><i class="fas fa-search"></i> Detailed Compliance Analysis</h4>
          <span class="analysis-count">{{ selectedDocumentForDetails.compliance_analyses.length }} Requirements Analyzed</span>
        </div>
        
        <div class="requirements-grid">
          <div v-for="(analysis, idx) in selectedDocumentForDetails.compliance_analyses" :key="idx" class="requirement-card">
            <div class="requirement-header">
              <div class="requirement-number">
                <!-- Main title: ALWAYS prioritize compliance_title (unique per compliance), show compliance_id badge -->
                <!-- Removed mapping_display (policy → subpolicy) to avoid confusion - all cards were showing the same mapping -->
                <span class="req-idx" style="font-weight: 600; font-size: 1.05em; display: block; margin-bottom: 4px; color: #333;" :title="analysis.requirement_title || ''">
                  {{ analysis.compliance_title || analysis.requirement_title || `Requirement ${analysis.index}` }}
                  <span v-if="analysis.compliance_id" class="compliance-id-badge" style="font-size: 0.7em; color: #666; margin-left: 8px; font-weight: normal;">
                    (ID: {{ analysis.compliance_id }})
                  </span>
                </span>
                <!-- Show full requirement_title as description if it's different from compliance_title -->
                <div v-if="analysis.requirement_title && analysis.compliance_title && analysis.requirement_title !== analysis.compliance_title && analysis.requirement_title.length > analysis.compliance_title.length" class="requirement-description" style="font-size: 0.85em; color: #666; margin-top: 4px; line-height: 1.4; padding-left: 8px; border-left: 2px solid #e0e0e0;">
                  {{ analysis.requirement_title }}
                </div>
                <div class="compliance-status">
                  <div class="meter-label">Compliance</div>
                  <div class="status-line">
                    <span class="status-pill" :class="(analysis.status || complianceStatusFromScore(analysis.compliance_score ?? analysis.relevance ?? 0))">
                      {{ (analysis.status || complianceStatusFromScore(analysis.compliance_score ?? analysis.relevance ?? 0)).replace('_',' ') }}
                    </span>
                    <span class="percent">{{ Math.round(((analysis.compliance_score ?? analysis.relevance ?? 0) * 100)) }}%</span>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Evidence Section -->
            <div v-if="analysis.evidence && analysis.evidence.length" class="evidence-section">
              <div class="evidence-list">
                <div v-for="(evidence, eIdx) in analysis.evidence" :key="eIdx" class="evidence-item">
                  <span>{{ typeof evidence === 'string' ? evidence : ((evidence && (evidence.text || evidence.reason)) || JSON.stringify(evidence)) }}</span>
                </div>
              </div>
            </div>
            
            <!-- Missing Elements Section -->
            <div v-if="analysis.missing && analysis.missing.length" class="missing-section">
              <div class="section-header">
                <i class="fas fa-exclamation-triangle text-warning"></i>
                <span>Missing Elements</span>
              </div>
              <div class="missing-list">
                <div v-for="(missing, mIdx) in analysis.missing" :key="mIdx" class="missing-item">
                  <span>{{ typeof missing === 'string' ? missing : ((missing && (missing.text || missing.reason)) || JSON.stringify(missing)) }}</span>
                </div>
              </div>
            </div>
            
            <!-- No Evidence/Missing -->
            <div v-if="(!analysis.evidence || !analysis.evidence.length) && (!analysis.missing || !analysis.missing.length)" class="no-analysis">
              <i class="fas fa-info-circle"></i>
              <span>No specific evidence or missing elements identified</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- No Analysis Available -->
      <div v-else class="no-analysis-available">
        <i class="fas fa-info-circle"></i>
        <span>No detailed analysis available for this document</span>
      </div>
    </div>

    <!-- Action Buttons (AI disabled) -->
    <div v-if="hasSelectedAudit" class="action-buttons">
      <button v-if="false" @click="startAIProcessing" class="btn btn-success" :disabled="uploadedDocuments.length === 0 || isProcessingAI" :class="{ 'processing': isProcessingAI }">
        <i v-if="!isProcessingAI" class="fas fa-robot"></i>
        <i v-else class="fas fa-spinner fa-spin"></i>
        {{ isProcessingAI ? 'AI Analyzing Documents...' : 'Start AI Analysis' }}
      </button>
      <button @click="goToReviews" class="btn btn-primary">
        <i class="fas fa-list-check"></i> Go to Reviews
      </button>
    </div>
    
    <!-- Bottom spacing for scrolling -->
    <div style="height: 50px;"></div>
  </div>
</template>

<script>
import api from '@/services/api.js'
import auditorDataService from '@/services/auditorService' // NEW: Use cached auditor data
import { compressFile, shouldCompressFile } from '@/utils/fileCompression.js'

export default {
  name: 'AIAuditDocumentUpload',
  props: {
    auditId: {
      type: [String, Number],
      required: true
    }
  },
  data() {
    return {
      auditInfo: {
        title: 'Audit Information',
        type: 'AI Audit',
        framework: 'Selected Framework',
        policy: 'Not Specified',
        subpolicy: 'Not Specified'
      },
      selectedPolicyName: 'Not Specified',
      selectedSubPolicyName: 'Not Specified',
      // Legacy single-select fields (kept for backward compatibility)
      policies: [],
      subpolicies: [],
      selectedPolicyId: '',
      selectedSubPolicyId: '',
      complianceRequirements: [],
      // New multi-select hierarchy based on audit scope
      auditHierarchyPolicies: [],        // [{ policy_id, policy_name, subpolicies: [...] }]
      selectedPolicyIdsMulti: [],        // [policy_id, ...]
      selectedSubpolicyIdsMulti: [],     // [subpolicy_id, ...]
      selectedFiles: [],
      uploadedDocuments: [],
      uploading: false,
      uploadProgress: 0,
      isDragOver: false,
      documentComplianceMapping: [], // Store document-to-compliance relevance mapping
      showComplianceSelection: false, // Show compliance selection modal
      selectedComplianceIds: [], // User-selected compliance requirements for processing
      processingStatus: null,
      complianceResults: [],
      aiProcessingResults: [],
      pollingInterval: null,
      isProcessingAI: false,
      availableAudits: [],
      availableAIAudits: [],
      selectedExistingAuditId: '',
      hasUserConfirmedSelection: false,
      isLoadingAudits: false,
      auditLoadError: '',
      selectedDocumentForDetails: null,
      isDropdownOpen: false,
      searchQuery: '',
      bulkChecking: false,
      relevantDocuments: [], // Documents from file_operations relevant to this audit
      selectedRelevantDocuments: [], // Checked relevant documents to upload
      isLoadingRelevantDocuments: false,
      isUploadingRelevantDocuments: false, // Loading state for upload
      showSuggestedDocuments: true, // Whether to show suggested documents section
      relevantDocumentsMessage: null, // Message explaining why no documents found
      relevantDocumentsStats: null, // Statistics about documents in framework
      expandedDocumentId: null, // Which document details are expanded
      bulkDeletingDatabase: false,
      bulkDeleting: false,  // For deleting all documents
      // SEBI AI Auditor data
      sebiEnabled: false,
      sebiInsights: {
        filingAccuracy: null,
        timelinessSLA: null,
        riskScore: null,
        patterns: null
      },
      isLoadingSEBI: false
    }
  },
  computed: {
    // Physical files (S3 documents)
    fileDocuments() {
      return this.uploadedDocuments.filter(
        d => d.external_source !== 'database_record' && d.document_type !== 'db_record'
      )
    },
    // Additional evidence items
    databaseEvidence() {
      return this.uploadedDocuments
        .filter(d => {
          // Only include database evidence items
          if (d.external_source !== 'database_record' && d.document_type !== 'db_record') {
            return false
          }
          
          // Exclude items that are part of a combined check (they're shown with the document instead)
          // Check the part_of_combined_check flag that we preserved during document loading
          if (d.part_of_combined_check === true) {
            console.log('🚫 Filtering out database evidence that is part of combined check:', d.document_id, d.document_name)
            return false
          }
          
          // Fallback: Also check compliance_analyses in case the flag wasn't preserved
          if (d.compliance_analyses) {
            try {
              let analyses = d.compliance_analyses
              if (typeof analyses === 'string') {
                analyses = JSON.parse(analyses)
              }
              // Check for part_of_combined_check flag in the analyses object
              if (analyses && typeof analyses === 'object' && analyses.part_of_combined_check === true) {
                console.log('🚫 Filtering out database evidence (fallback check):', d.document_id, d.document_name)
                return false
              }
            } catch (e) {
              // If parsing fails, include the item (safer to show than hide)
            }
          }
          
          return true
        })
        .map(d => {
          // Determine if this DB record has at least one real mapping
          // (policy/subpolicy/compliance). If not, we hide it completely.
          let hasRealMapping = false

          if (Array.isArray(d.mappings) && d.mappings.length > 0) {
            hasRealMapping = d.mappings.some(m => {
              const hasIds = (m.policy_id && m.subpolicy_id) || m.compliance_count > 0
              const label = (m.mapping_display || '').toLowerCase()
              const notUnmapped = label && !label.startsWith('unmapped')
              return hasIds || notUnmapped
            })
          } else if (d.mapped_policy || d.mapped_subpolicy) {
            hasRealMapping = true
          }

          if (!hasRealMapping) {
            // Skip completely: do not show unmapped DB records
            return null
          }

          // Preserve all mappings with their processing_status and other fields
          const preservedMappings = Array.isArray(d.mappings) && d.mappings.length > 0
            ? d.mappings.map(m => ({
                display: m.mapping_display || m.display || 'Unknown mapping',
                mapping_display: m.mapping_display || m.display,
                processing_status: m.processing_status || d.processing_status || 'pending',
                compliance_status: m.compliance_status || d.compliance_status || null,
                confidence_score: m.confidence_score || d.confidence_score || null,
                compliance_analyses: m.compliance_analyses || d.compliance_analyses || null,
                policy_id: m.policy_id || d.policy_id,
                subpolicy_id: m.subpolicy_id || d.subpolicy_id,
                mapped_policy: m.mapped_policy || d.mapped_policy,
                mapped_subpolicy: m.mapped_subpolicy || d.mapped_subpolicy
              }))
            : [{
                display: d.mapped_policy && d.mapped_subpolicy 
                  ? `${d.mapped_policy} → ${d.mapped_subpolicy}`
                  : d.mapped_policy || d.mapped_subpolicy || 'Database mapping',
                mapping_display: d.mapped_policy && d.mapped_subpolicy 
                  ? `${d.mapped_policy} → ${d.mapped_subpolicy}`
                  : d.mapped_policy || d.mapped_subpolicy || 'Database mapping',
                processing_status: d.processing_status || 'pending',
                compliance_status: d.compliance_status || null,
                confidence_score: d.confidence_score || null,
                compliance_analyses: d.compliance_analyses || null,
                policy_id: d.policy_id,
                subpolicy_id: d.subpolicy_id,
                mapped_policy: d.mapped_policy,
                mapped_subpolicy: d.mapped_subpolicy
              }]

          return {
            document_id: d.document_id,
            document_name: d.document_name || 'Evidence',
            uploaded_date: d.uploaded_date,
            record_source: d.external_source || 'database_record',
            processing_status: d.processing_status || 'pending',
            mappings: preservedMappings
          }
        })
        .filter(Boolean)
    },
    currentAuditId() {
      // Priority: selected dropdown audit > route params > props > fallback
      return this.selectedExistingAuditId || this.auditId || this.$route.params.auditId || this.$route.query.auditId || '1092'
    },
    hasSelectedAudit() {
      // Show details only after explicit user confirmation
      return this.hasUserConfirmedSelection === true
    },
    hasRequiredMapping() {
      // Require at least one policy, subpolicy or compliance for upload
      return (
        this.selectedPolicyIdsMulti.length > 0 ||
        this.selectedSubpolicyIdsMulti.length > 0 ||
        (this.selectedComplianceIds && this.selectedComplianceIds.length > 0)
      )
    },
    // Flattened helpers for the hierarchy
    availableSubpolicies() {
      // All subpolicies under the selected policies
      const map = []
      this.auditHierarchyPolicies.forEach(policy => {
        if (this.selectedPolicyIdsMulti.includes(policy.policy_id)) {
          (policy.subpolicies || []).forEach(sp => {
            map.push({
              policy_id: policy.policy_id,
              policy_name: policy.policy_name,
              subpolicy_id: sp.subpolicy_id,
              subpolicy_name: sp.subpolicy_name
            })
          })
        }
      })
      return map
    },
    availableCompliances() {
      // All compliances under the selected subpolicies (or, if none, under selected policies)
      const selectedSubSet = new Set(this.selectedSubpolicyIdsMulti)
      const selectedPolicySet = new Set(this.selectedPolicyIdsMulti)
      const result = []

      this.auditHierarchyPolicies.forEach(policy => {
        const policySelected = selectedPolicySet.has(policy.policy_id)
        ;(policy.subpolicies || []).forEach(sp => {
          const subSelected =
            selectedSubSet.size > 0
              ? selectedSubSet.has(sp.subpolicy_id)
              : policySelected
          if (!subSelected) return
          ;(sp.compliances || []).forEach(c => {
            result.push({
              ...c,
              policy_id: policy.policy_id,
              policy_name: policy.policy_name,
              subpolicy_id: sp.subpolicy_id,
              subpolicy_name: sp.subpolicy_name,
              compliance_id: c.compliance_id || c.ComplianceId
            })
          })
        })
      })
      return result
    },
    allPoliciesSelected() {
      return (
        this.auditHierarchyPolicies.length > 0 &&
        this.selectedPolicyIdsMulti.length === this.auditHierarchyPolicies.length
      )
    },
    allSubpoliciesSelected() {
      const subs = this.availableSubpolicies
      return subs.length > 0 && this.selectedSubpolicyIdsMulti.length === subs.length
    },
    allCompliancesSelected() {
      const comps = this.availableCompliances
      return comps.length > 0 && this.selectedComplianceIds.length === comps.length
    },
    filteredAudits() {
      if (!this.searchQuery) {
        return this.availableAIAudits
      }
      return this.availableAIAudits.filter(audit => {
        const searchLower = this.searchQuery.toLowerCase()
        const title = (audit.title || audit.policy || 'Audit').toLowerCase()
        const auditId = audit.audit_id.toString().toLowerCase()
        const dueDate = (audit.duedate || audit.due_date || '').toLowerCase()
        
        return title.includes(searchLower) || 
               auditId.includes(searchLower) || 
               dueDate.includes(searchLower)
      })
    }
  },
  watch: {
    selectedPolicyIdsMulti: {
      handler() {
        if (this.hasSelectedAudit) {
          this.loadRelevantDocuments()
        }
      },
      deep: true
    },
    selectedSubpolicyIdsMulti: {
      handler() {
        if (this.hasSelectedAudit) {
          this.loadRelevantDocuments()
        }
      },
      deep: true
    },
    selectedComplianceIds: {
      handler() {
        if (this.hasSelectedAudit) {
          this.loadRelevantDocuments()
        }
      },
      deep: true
    }
  },
  mounted() {
    console.log('🔍 Component mounted')
    console.log('🔍 Props auditId:', this.auditId)
    console.log('🔍 Route params:', this.$route.params)
    console.log('🔍 Current audit ID (route):', this.currentAuditId)
    
    // Pre-select dropdown with route auditId if present, but do not load details yet
    const routeAuditId = this.$route.params.auditId || this.$route.query.auditId || this.auditId
    if (routeAuditId) {
      this.selectedExistingAuditId = String(routeAuditId)
    }

    this.loadAvailableAudits()
    
    // Add click outside listener for dropdown
    document.addEventListener('click', this.handleClickOutside)
  },
  beforeUnmount() {
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval)
    }
    // Remove click outside listener
    document.removeEventListener('click', this.handleClickOutside)
  },
  methods: {
    // Dropdown methods
    toggleDropdown() {
      this.isDropdownOpen = !this.isDropdownOpen
      if (this.isDropdownOpen) {
        this.searchQuery = ''
      }
    },
    
    closeDropdown() {
      // Delay closing to allow click events to register
      setTimeout(() => {
        this.isDropdownOpen = false
        this.searchQuery = ''
      }, 150)
    },
    
    selectAudit(audit) {
      this.selectedExistingAuditId = audit.audit_id
      this.isDropdownOpen = false
      this.searchQuery = ''
      this.onSelectExistingAudit()
    },
    
    getSelectedAuditTitle() {
      const selectedAudit = this.availableAIAudits.find(a => a.audit_id === this.selectedExistingAuditId)
      if (selectedAudit) {
        return selectedAudit.title || 'Audit'
      }
      return 'Select Assigned AI Audit...'
    },
    
    handleClickOutside(event) {
      const dropdown = this.$el.querySelector('.custom-dropdown-container')
      if (dropdown && !dropdown.contains(event.target)) {
        this.isDropdownOpen = false
        this.searchQuery = ''
      }
    },
    
    complianceStatusFromScore(score) {
      const s = Number(score || 0)
      if (s >= 0.7) return 'compliant'
      if (s >= 0.4) return 'partially_compliant'
      return 'non_compliant'
    },
    async downloadAuditReport() {
      try {
        const auditId = this.currentAuditId
        if (!auditId) return
        
        // Build list of document_ids to include in the report based on current UI selection
        const selectedIds = new Set()
        
        // If a specific mapping was opened in the Details view, prioritise that
        if (this.selectedDocumentForDetails) {
          // If showing all mappings details, include all their document_ids
          if (this.selectedDocumentForDetails.isAllMappings && this.selectedDocumentForDetails.mappings) {
            this.selectedDocumentForDetails.mappings.forEach(m => {
              if (m.document_id) {
                selectedIds.add(m.document_id)
              }
            })
          } else if (this.selectedDocumentForDetails.document_id) {
            // Single mapping details
            selectedIds.add(this.selectedDocumentForDetails.document_id)
          }
        }
        
        if (selectedIds.size === 0 && this.uploadedDocuments && this.uploadedDocuments.length > 0) {
          // Otherwise, include all completed mappings currently visible in the UI
          this.uploadedDocuments.forEach(fileGroup => {
            if (!fileGroup || !fileGroup.mappings) return
            
            // If "All Mappings" is selected for this file, include all its completed mappings
            if (this.isAllMappingsSelected(fileGroup)) {
              fileGroup.mappings.forEach(m => {
                if (m.processing_status === 'completed' && m.document_id) {
                  selectedIds.add(m.document_id)
                }
              })
            } else {
              // Only include the currently selected mapping if it is completed
              const mapping = this.getSelectedMapping(fileGroup)
              if (mapping && mapping.processing_status === 'completed' && mapping.document_id) {
                selectedIds.add(mapping.document_id)
              }
            }
          })
        }
        
        const params = {}
        if (selectedIds.size > 0) {
          params.document_ids = Array.from(selectedIds).join(',')
        }
        
        const url = `/api/ai-audit/${auditId}/download-report/`
        const response = await api.get(url, { responseType: 'blob', params })
        const blob = new Blob([response.data], { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })
        const link = document.createElement('a')
        const fileURL = window.URL.createObjectURL(blob)
        link.href = fileURL
        link.download = `Audit_Report_${auditId}.docx`
        document.body.appendChild(link)
        link.click()
        link.remove()
        window.URL.revokeObjectURL(fileURL)
      } catch (e) {
        console.error('Error downloading report:', e)
        this.$popup?.error('Failed to generate report')
      }
    },
    showDocumentDetails(doc) {
      this.selectedDocumentForDetails = doc
      console.log('Selected document for details:', doc)
      console.log('Compliance analyses:', doc.compliance_analyses)
      if (doc.compliance_analyses && doc.compliance_analyses.length > 0) {
        console.log('First analysis:', doc.compliance_analyses[0])
        console.log('Requirement title:', doc.compliance_analyses[0].requirement_title)
      }
      // Scroll to the details section with better positioning
      this.$nextTick(() => {
        const detailsElement = document.querySelector('.compliance-details-expanded')
        if (detailsElement) {
          // Scroll to show the details section with some offset from top
          const offset = 100
          const elementPosition = detailsElement.offsetTop - offset
          window.scrollTo({
            top: elementPosition,
            behavior: 'smooth'
          })
        }
      })
    },
    // Show combined details for ALL mappings of a file group
    showAllMappingsDetails(fileGroup) {
      if (!fileGroup || !fileGroup.mappings || fileGroup.mappings.length === 0) {
        this.$popup?.warning('No mappings available for this document.')
        return
      }
      // Only consider completed mappings
      const completedMappings = fileGroup.mappings.filter(
        m => m.processing_status === 'completed'
      )
      if (completedMappings.length === 0) {
        this.$popup?.warning('Please run compliance check for all mappings before viewing details.')
        return
      }
      
      // Check if this is part of a combined check with other documents
      const combinedGroup = this.isPartOfCombinedCheckGroup(fileGroup) 
        ? this.getCombinedCheckGroup(fileGroup) 
        : [fileGroup]
      const isCombinedCheck = combinedGroup.length > 1
      
      // Combine analyses from all completed mappings
      const allAnalyses = []
      console.log('🔍 Extracting analyses from completed mappings:', completedMappings.length)
      
      completedMappings.forEach((m, idx) => {
        console.log(`🔍 Processing mapping ${idx + 1}/${completedMappings.length}:`, {
          mapping_display: m.mapping_display,
          has_compliance_analyses: !!m.compliance_analyses,
          compliance_analyses_type: typeof m.compliance_analyses,
          compliance_analyses_is_array: Array.isArray(m.compliance_analyses),
          compliance_analyses_keys: m.compliance_analyses && typeof m.compliance_analyses === 'object' ? Object.keys(m.compliance_analyses) : null,
          FULL_COMPLIANCE_ANALYSES: JSON.stringify(m.compliance_analyses, null, 2) // Dump full structure
        })
        
        let analyses = m.compliance_analyses
        if (!analyses) {
          console.warn(`⚠️ Mapping ${m.mapping_display} has no compliance_analyses`)
          return
        }
        
        // Handle JSON string
        if (typeof analyses === 'string') {
          try {
            analyses = JSON.parse(analyses)
            console.log(`✅ Parsed JSON string for mapping ${m.mapping_display}`, {
              type: typeof analyses,
              is_array: Array.isArray(analyses),
              keys: typeof analyses === 'object' && !Array.isArray(analyses) ? Object.keys(analyses) : null
            })
          } catch (err) {
            console.warn('Failed to parse compliance_analyses string for mapping', m.mapping_display, err)
            analyses = null
            return
          }
        }
        
        // Handle object with compliance_analyses or analyses key
        // Backend stores: {compliance_status, confidence_score, compliance_analyses: [...], processed_at}
        // Frontend wraps it: {analyses: [...], ...metadata} or {compliance_analyses: [...]}
        if (analyses && typeof analyses === 'object' && !Array.isArray(analyses)) {
          console.log(`🔍 analyses is object, checking for nested arrays:`, {
            has_analyses_key: !!analyses.analyses,
            has_compliance_analyses_key: !!analyses.compliance_analyses,
            keys: Object.keys(analyses),
            analyses_type: analyses.analyses ? typeof analyses.analyses : null,
            analyses_is_array: analyses.analyses ? Array.isArray(analyses.analyses) : null,
            compliance_analyses_type: analyses.compliance_analyses ? typeof analyses.compliance_analyses : null,
            compliance_analyses_is_array: analyses.compliance_analyses ? Array.isArray(analyses.compliance_analyses) : null
          })
          
          // Priority order for extraction - try ALL possible paths:
          // 1. analyses.analyses (frontend wrapped structure)
          // 2. analyses.compliance_analyses (backend structure)
          // 3. Check if any key contains an array
          let extracted = false
          
          if (analyses.analyses && Array.isArray(analyses.analyses)) {
            analyses = analyses.analyses
            console.log(`✅ Extracted from analyses.analyses (${analyses.length} items)`)
            extracted = true
          } else if (analyses.compliance_analyses && Array.isArray(analyses.compliance_analyses)) {
            analyses = analyses.compliance_analyses
            console.log(`✅ Extracted from analyses.compliance_analyses (${analyses.length} items)`)
            extracted = true
          } else {
            // Try one more level deep in case of double nesting
            if (analyses.analyses && typeof analyses.analyses === 'object' && !Array.isArray(analyses.analyses)) {
              if (analyses.analyses.analyses && Array.isArray(analyses.analyses.analyses)) {
                analyses = analyses.analyses.analyses
                console.log(`✅ Extracted from nested analyses.analyses.analyses (${analyses.length} items)`)
                extracted = true
              } else if (analyses.analyses.compliance_analyses && Array.isArray(analyses.analyses.compliance_analyses)) {
                analyses = analyses.analyses.compliance_analyses
                console.log(`✅ Extracted from nested analyses.analyses.compliance_analyses (${analyses.length} items)`)
                extracted = true
              }
            }
            
            if (!extracted && analyses.compliance_analyses && typeof analyses.compliance_analyses === 'object' && !Array.isArray(analyses.compliance_analyses)) {
              if (analyses.compliance_analyses.analyses && Array.isArray(analyses.compliance_analyses.analyses)) {
                analyses = analyses.compliance_analyses.analyses
                console.log(`✅ Extracted from nested analyses.compliance_analyses.analyses (${analyses.length} items)`)
                extracted = true
              } else if (analyses.compliance_analyses.compliance_analyses && Array.isArray(analyses.compliance_analyses.compliance_analyses)) {
                analyses = analyses.compliance_analyses.compliance_analyses
                console.log(`✅ Extracted from nested analyses.compliance_analyses.compliance_analyses (${analyses.length} items)`)
                extracted = true
              }
            }
            
            // Last resort: search ALL keys for arrays
            if (!extracted) {
              console.log(`🔍 Searching all keys for array values...`)
              for (const key of Object.keys(analyses)) {
                const value = analyses[key]
                if (Array.isArray(value) && value.length > 0) {
                  console.log(`✅ Found array in key "${key}" with ${value.length} items`)
                  analyses = value
                  extracted = true
                  break
                } else if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
                  // Check nested object for arrays
                  for (const nestedKey of Object.keys(value)) {
                    if (Array.isArray(value[nestedKey]) && value[nestedKey].length > 0) {
                      console.log(`✅ Found array in nested key "${key}.${nestedKey}" with ${value[nestedKey].length} items`)
                      analyses = value[nestedKey]
                      extracted = true
                      break
                    }
                  }
                  if (extracted) break
                }
              }
            }
            
            if (!extracted) {
              console.warn(`⚠️ Could not extract array from object structure for mapping ${m.mapping_display}`, {
                structure: JSON.stringify(analyses, null, 2)
              })
              analyses = null
            }
          }
        }
        
        if (!analyses) {
          console.warn(`⚠️ No analyses extracted for mapping ${m.mapping_display}`)
          return
        }
        
        if (!Array.isArray(analyses)) {
          console.warn(`⚠️ Analyses is not an array for mapping ${m.mapping_display}:`, typeof analyses, analyses)
          // Try to convert single object to array
          if (typeof analyses === 'object' && analyses !== null) {
            analyses = [analyses]
            console.log(`✅ Converted single object to array for mapping ${m.mapping_display}`)
          } else {
            console.warn(`⚠️ Cannot convert to array, skipping mapping ${m.mapping_display}`)
            return
          }
        }
        
        console.log(`✅ Found ${analyses.length} analyses for mapping ${m.mapping_display}`, {
          first_analysis_keys: analyses.length > 0 && typeof analyses[0] === 'object' ? Object.keys(analyses[0]) : null
        })
        
        analyses.forEach((a) => {
          // Ensure compliance_title is preserved from the analysis object
          const analysisWithMapping = {
            ...a,
            // Add mapping context so UI can show which mapping this belongs to
            mapping_display: m.mapping_display,
            mapping_policy: m.mapped_policy,
            mapping_subpolicy: m.mapped_subpolicy
          }
          
          // Log to verify compliance_title is present
          if (a.compliance_id) {
            console.log(`📋 Analysis for compliance_id ${a.compliance_id}:`, {
              has_compliance_title: !!a.compliance_title,
              compliance_title: a.compliance_title,
              requirement_title: a.requirement_title,
              mapping_display: m.mapping_display
            })
          }
          
          allAnalyses.push(analysisWithMapping)
        })
      })
      
      console.log(`✅ Total analyses extracted: ${allAnalyses.length} from ${completedMappings.length} mapping(s)`)
      
      // Deduplicate by compliance_id - keep only one entry per compliance
      const seenComplianceIds = new Map()
      const deduplicatedAnalyses = []
      
      allAnalyses.forEach((analysis) => {
        const complianceId = analysis.compliance_id
        if (!complianceId) {
          // If no compliance_id, keep it (might be a special case)
          deduplicatedAnalyses.push(analysis)
          return
        }
        
        if (!seenComplianceIds.has(complianceId)) {
          // First time seeing this compliance_id - keep it
          seenComplianceIds.set(complianceId, analysis)
          deduplicatedAnalyses.push(analysis)
        } else {
          // Duplicate found - keep the one with higher compliance_score or relevance
          const existing = seenComplianceIds.get(complianceId)
          const existingScore = existing.compliance_score ?? existing.relevance ?? 0
          const currentScore = analysis.compliance_score ?? analysis.relevance ?? 0
          
          if (currentScore > existingScore) {
            // Replace with better score
            const index = deduplicatedAnalyses.findIndex(a => a.compliance_id === complianceId)
            if (index !== -1) {
              deduplicatedAnalyses[index] = analysis
              seenComplianceIds.set(complianceId, analysis)
            }
          }
          // Otherwise keep the existing one (higher score)
        }
      })
      
      console.log(`✅ Deduplicated: ${allAnalyses.length} → ${deduplicatedAnalyses.length} unique compliances`)
      
      // Ensure each analysis has a unique compliance_title
      // The backend should have set compliance_title in each analysis object
      deduplicatedAnalyses.forEach((analysis) => {
        // Log current state before processing
        console.log(`🔍 Processing analysis for compliance_id ${analysis.compliance_id}:`, {
          compliance_title: analysis.compliance_title,
          requirement_title: analysis.requirement_title ? analysis.requirement_title.substring(0, 50) + '...' : null,
          has_compliance_title: !!analysis.compliance_title,
          compliance_title_length: analysis.compliance_title ? analysis.compliance_title.length : 0
        })
        
        // If compliance_title is missing or same as requirement_title, extract unique title
        if (!analysis.compliance_title || 
            analysis.compliance_title === analysis.requirement_title ||
            analysis.compliance_title.trim() === '') {
          console.warn(`⚠️ compliance_title missing or invalid for compliance_id ${analysis.compliance_id}, extracting from requirement_title`)
          
          if (analysis.requirement_title) {
            // Use first sentence or first 100 chars as compliance_title
            const firstSentence = analysis.requirement_title.split('.')[0].trim()
            if (firstSentence.length > 10 && firstSentence.length < 150) {
              analysis.compliance_title = firstSentence
            } else {
              analysis.compliance_title = analysis.requirement_title.substring(0, 100).trim()
            }
          } else {
            analysis.compliance_title = `Compliance ${analysis.compliance_id || analysis.index || 'Unknown'}`
          }
          
          console.log(`✅ Extracted compliance_title: "${analysis.compliance_title}"`)
        } else {
          console.log(`✅ Using existing compliance_title: "${analysis.compliance_title}"`)
        }
      })
      
      // Final verification: log all unique compliance titles
      console.log(`📊 Final compliance titles:`, deduplicatedAnalyses.map(a => ({
        compliance_id: a.compliance_id,
        compliance_title: a.compliance_title,
        mapping_display: a.mapping_display
      })))
      
      // Build document name that indicates combined check if applicable
      let displayName = fileGroup.document_name
      if (isCombinedCheck) {
        const otherDocNames = combinedGroup
          .filter(fg => fg !== fileGroup)
          .map(fg => fg.document_name)
          .filter(name => name)
        if (otherDocNames.length > 0) {
          displayName = `${fileGroup.document_name} + ${otherDocNames.length} other document(s)`
        }
      }
      
      // Show details even if no analyses - the UI will display a message
      const combinedDetails = {
        document_name: displayName,
        document_type: fileGroup.document_type,
        file_size: fileGroup.file_size,
        uploaded_date: fileGroup.uploaded_date,
        isAllMappings: true,
        isCombinedCheck: isCombinedCheck, // Flag to indicate this is a combined check
        combinedDocuments: isCombinedCheck ? combinedGroup.map(fg => ({
          document_name: fg.document_name,
          document_id: fg.document_id
        })) : null, // List of all documents in the combined check
        mappings: completedMappings,
        compliance_status: this.aggregateComplianceStatus(completedMappings),
        confidence_score: this.aggregateConfidenceScore(completedMappings),
        compliance_analyses: deduplicatedAnalyses.length > 0 ? deduplicatedAnalyses : [] // Always provide array, even if empty (deduplicated)
      }
      
      console.log('🔍 Showing details for fileGroup:', {
        document_name: displayName,
        mappings_count: completedMappings.length,
        analyses_count: allAnalyses.length,
        has_analyses: allAnalyses.length > 0
      })
      
      this.showDocumentDetails(combinedDetails)
      
      // Show a warning if no analyses, but still display the details view
      if (allAnalyses.length === 0) {
        this.$popup?.warning('No analysis results available for completed mappings. Showing document details anyway.')
      }
    },
    // Show details popup for additional evidence
    showDatabaseRecordDetails(recordGroup) {
      if (!recordGroup || !Array.isArray(recordGroup.mappings) || recordGroup.mappings.length === 0) {
        this.$popup?.warning('No mappings available for this item.')
        return
      }
      
      // Only consider completed mappings (same as documents)
      const completedMappings = recordGroup.mappings.filter(
        m => m.processing_status === 'completed'
      )
      
      if (completedMappings.length === 0) {
        this.$popup?.warning('Please run compliance check before viewing details.')
        return
      }

      const allAnalyses = []
      completedMappings.forEach(m => {
        let analyses = m.compliance_analyses
        if (!analyses) return
        if (typeof analyses === 'string') {
          try {
            analyses = JSON.parse(analyses)
          } catch (err) {
            console.warn('Failed to parse compliance_analyses string for mapping', m.display || m.mapping_display, err)
            analyses = null
          }
        }
        // Handle object with compliance_analyses or analyses key
        // (compliance_analyses can be stored as {analyses: [...], ...metadata} or {compliance_analyses: [...]})
        if (analyses && typeof analyses === 'object' && !Array.isArray(analyses)) {
          // Try both 'analyses' (new structure) and 'compliance_analyses' (old structure)
          analyses = analyses.analyses || analyses.compliance_analyses || analyses
        }
        if (!Array.isArray(analyses)) return
        analyses.forEach(a => {
          allAnalyses.push({
            ...a,
            mapping_display: m.mapping_display || m.display,
          })
        })
      })

      if (allAnalyses.length === 0) {
        this.$popup?.warning('No analysis details are available for this item yet.')
        return
      }

      // Deduplicate by compliance_id - keep only one entry per compliance
      const seenComplianceIds = new Map()
      const deduplicatedAnalyses = []
      
      allAnalyses.forEach((analysis) => {
        const complianceId = analysis.compliance_id
        if (!complianceId) {
          // If no compliance_id, keep it (might be a special case)
          deduplicatedAnalyses.push(analysis)
          return
        }
        
        if (!seenComplianceIds.has(complianceId)) {
          // First time seeing this compliance_id - keep it
          seenComplianceIds.set(complianceId, analysis)
          deduplicatedAnalyses.push(analysis)
        } else {
          // Duplicate found - keep the one with higher compliance_score or relevance
          const existing = seenComplianceIds.get(complianceId)
          const existingScore = existing.compliance_score ?? existing.relevance ?? 0
          const currentScore = analysis.compliance_score ?? analysis.relevance ?? 0
          
          if (currentScore > existingScore) {
            // Replace with better score
            const index = deduplicatedAnalyses.findIndex(a => a.compliance_id === complianceId)
            if (index !== -1) {
              deduplicatedAnalyses[index] = analysis
              seenComplianceIds.set(complianceId, analysis)
            }
          }
          // Otherwise keep the existing one (higher score)
        }
      })
      
      console.log(`✅ Deduplicated database records: ${allAnalyses.length} → ${deduplicatedAnalyses.length} unique compliances`)

      const combinedDetails = {
        document_name: recordGroup.document_name,
        document_type: recordGroup.record_source || 'database_record',
        file_size: null,
        uploaded_date: recordGroup.uploaded_date,
        isAllMappings: true,
        mappings: completedMappings,
        compliance_status: this.aggregateComplianceStatus(completedMappings),
        confidence_score: this.aggregateConfidenceScore(completedMappings),
        compliance_analyses: deduplicatedAnalyses
      }
      this.showDocumentDetails(combinedDetails)
    },
    async loadAuditHierarchy() {
      try {
        const auditId = this.currentAuditId
        if (!auditId || auditId === 'Unknown') {
          return
        }
        console.log('📚 Loading compliance hierarchy (framework-wide) for audit:', auditId)

        // Always build from framework using framework_id (show all policies in framework,
        // not just those already used in this audit)
        let hierarchyPolicies = []

        // Get framework_id from auditInfo (already loaded in loadAuditInfo)
        const frameworkId = this.auditInfo.framework_id
        console.log('📚 auditInfo object:', this.auditInfo)
        console.log('📚 Using framework_id from auditInfo:', frameworkId)
        console.log('📚 Framework name:', this.auditInfo.framework)

        // Validate frameworkId early - handle null, undefined, 0, empty string, etc.
        if (frameworkId === null || frameworkId === undefined || frameworkId === '' || frameworkId === 0 || frameworkId === '0') {
          console.warn('⚠️ No valid framework_id available on auditInfo; cannot build policy list. FrameworkId:', frameworkId)
          this.auditHierarchyPolicies = []
          return
        }

        const fwId = parseInt(frameworkId)
        if (isNaN(fwId) || fwId <= 0) {
          console.warn('⚠️ Parsed framework_id is invalid:', frameworkId, '->', fwId)
          this.auditHierarchyPolicies = []
          return
        }

        // Use tree / framework endpoints to build full hierarchy for this framework
        try {
            console.log('📚 Building hierarchy from framework_id:', fwId, '(type:', typeof fwId, ')')
          // Try tree endpoint first
          let policiesResp
          let policies = []
          try {
            policiesResp = await api.get(`/api/tree/frameworks/${fwId}/policies/`, { timeout: 20000 })
            policies = policiesResp.data?.data || policiesResp.data || []
            console.log('📚 Found', policies.length, 'policies from tree endpoint for framework', fwId)
          } catch (treeError) {
            console.warn('⚠️ Tree endpoint failed, trying fallback endpoint:', treeError.message)
            // Fallback to simpler endpoint
            try {
              policiesResp = await api.get(`/api/frameworks/${fwId}/get-policies/`, { timeout: 20000 })
              policies = Array.isArray(policiesResp.data) ? policiesResp.data : []
              console.log('📚 Found', policies.length, 'policies from fallback endpoint for framework', fwId)
            } catch (fallbackError) {
              console.error('❌ Both endpoints failed:', fallbackError.message)
              throw fallbackError
            }
          }

          // Build hierarchy: for each policy, get subpolicies, then compliances
          hierarchyPolicies = await Promise.all(
            policies.map(async (policy) => {
                  const policyId = policy.PolicyId || policy.policy_id || policy.id
                  if (!policyId) return null

                  try {
                    // Get subpolicies for this policy
                    const subpoliciesResp = await api.get(`/api/tree/policies/${policyId}/subpolicies/`, { timeout: 15000 })
                    const subpoliciesData = subpoliciesResp.data?.data || subpoliciesResp.data || []
                    
                    // For each subpolicy, get compliances
                    const subpolicies = await Promise.all(
                      subpoliciesData.map(async (subpolicy) => {
                        const subpolicyId = subpolicy.SubPolicyId || subpolicy.subpolicy_id || subpolicy.id
                        if (!subpolicyId) return null

                        try {
                          const compliancesResp = await api.get(`/api/tree/subpolicies/${subpolicyId}/compliances/`, { timeout: 15000 })
                          const compliancesData = compliancesResp.data?.data || compliancesResp.data || []
                          
                          return {
                            subpolicy_id: subpolicyId,
                            subpolicy_name: subpolicy.SubPolicyName || subpolicy.subpolicy_name || subpolicy.name,
                            compliances: compliancesData.map(c => ({
                              compliance_id: c.ComplianceId || c.compliance_id || c.id,
                              compliance_title: c.ComplianceTitle || c.compliance_title || c.title || c.ComplianceItemDescription,
                              compliance_description: c.ComplianceItemDescription || c.compliance_description || c.description,
                              Criticality: c.Criticality || c.criticality
                            }))
                          }
                        } catch (e) {
                          console.warn(`⚠️ Could not load compliances for subpolicy ${subpolicyId}:`, e)
                          return {
                            subpolicy_id: subpolicyId,
                            subpolicy_name: subpolicy.SubPolicyName || subpolicy.subpolicy_name || subpolicy.name,
                            compliances: []
                          }
                        }
                      })
                    )

                    return {
                      policy_id: policyId,
                      policy_name: policy.PolicyName || policy.policy_name || policy.name,
                      subpolicies: subpolicies.filter(sp => sp !== null)
                    }
                  } catch (e) {
                    console.warn(`⚠️ Could not load subpolicies for policy ${policyId}:`, e)
                    return {
                      policy_id: policyId,
                      policy_name: policy.PolicyName || policy.policy_name || policy.name,
                      subpolicies: []
                    }
                  }
                })
              )

              hierarchyPolicies = hierarchyPolicies.filter(p => p !== null)
              console.log('📚 Built hierarchy from framework tree. Policies:', hierarchyPolicies.length)
          console.log('📚 Built hierarchy from framework tree. Policies:', hierarchyPolicies.length)
        } catch (e) {
          console.error('❌ Error building hierarchy from framework tree/framework endpoints:', e)
        }

        this.auditHierarchyPolicies = hierarchyPolicies
        console.log('📚 Final hierarchy policies count:', this.auditHierarchyPolicies.length)

        // Restore any saved selections for this audit
        if (this.auditHierarchyPolicies.length) {
          this.restoreSelectionsForAudit()
        }
      } catch (error) {
        console.error('❌ Error loading audit/framework compliance hierarchy:', error)
        console.error('Error details:', error.response?.data || error.message)
        this.auditHierarchyPolicies = []
      }
    },
    async loadAvailableAudits() {
      try {
        this.isLoadingAudits = true
        this.auditLoadError = ''
        
        console.log('🔍 [AIAuditUpload] Checking for cached audits data...')
        
        // Check if prefetch was never started (user came directly to this page)
        if (!window.auditorDataFetchPromise && !auditorDataService.hasAuditsCache()) {
          console.log('🚀 [AIAuditUpload] Starting prefetch now (user came directly to this page)...')
          window.auditorDataFetchPromise = auditorDataService.fetchAllAuditorData()
        }
        
        // Wait for prefetch if it's running
        if (window.auditorDataFetchPromise) {
          console.log('⏳ [AIAuditUpload] Waiting for prefetch to complete...')
          try {
            await window.auditorDataFetchPromise
            console.log('✅ [AIAuditUpload] Prefetch completed')
          } catch (error) {
            console.warn('⚠️ [AIAuditUpload] Prefetch failed, will fetch directly')
          }
        }
        
        let merged = []
        
        // Try to get data from cache first
        if (auditorDataService.hasAuditsCache()) {
          console.log('✅ [AIAuditUpload] Using cached audits data')
          const cachedAudits = auditorDataService.getData('audits') || []
          console.log(`[AIAuditUpload] Loaded ${cachedAudits.length} audits from cache`)
          merged = cachedAudits
        } else {
          // Fallback: Fetch auditor, reviewer and public audits in parallel and merge
          console.log('⚠️ [AIAuditUpload] No cached data found, fetching from API...')
          const results = await Promise.allSettled([
            api.get('/api/my-audits/'),
            api.get('/api/my-reviews/'),
            api.get('/api/audits/public/')
          ])

          const pushNormalized = (arr) => {
            if (!Array.isArray(arr)) return
            arr.forEach(item => merged.push(item))
          }

          results.forEach((res, idx) => {
            if (res.status === 'fulfilled') {
              const data = res.value?.data
              const list = Array.isArray(data?.audits) ? data.audits : (Array.isArray(data) ? data : [])
              console.log('🔎 Source', idx, 'count:', Array.isArray(list) ? list.length : 0)
              pushNormalized(list)
            } else {
              console.warn('Audit source failed:', idx, res.reason?.response?.status)
            }
          })
          
          // Update cache with fetched data
          if (merged.length > 0) {
            auditorDataService.setData('audits', merged)
            console.log('ℹ️ [AIAuditUpload] Cache updated after direct API fetch')
          }
        }

        // Deduplicate by AuditId/audit_id
        const seen = new Set()
        const deduped = merged.filter(a => {
          const id = a.audit_id || a.AuditId || a.id
          if (!id) return false
          if (seen.has(id)) return false
          seen.add(id)
          return true
        })

        this.availableAudits = deduped
        // Do not filter by audit type because some AI audits may be stored as 'I'.
        // Show all assigned audits and indicate type in the label.
        this.availableAIAudits = this.availableAudits.map(a => {
          const title = (a.title || a.Title || '').toString().trim()
          return {
            audit_id: a.audit_id || a.AuditId || a.id,
            title: title || 'Audit',
            policy: a.policy || a.Policy || title || 'Audit',
            duedate: a.duedate || a.due_date || a.DueDate || null,
            framework: a.framework || a.FrameworkName || null,
            audit_type: (a.audit_type || a.AuditType || '').toString().toUpperCase() || 'UNKNOWN'
          }
        }).sort((a) => (a.audit_type === 'A' ? -1 : 1))
        console.log('🔍 Loaded AI audits:', this.availableAIAudits)
      } catch (e) {
        console.error('Error loading assigned audits:', e)
        this.auditLoadError = 'Unable to load assigned AI audits.'
        this.availableAIAudits = []
      } finally {
        this.isLoadingAudits = false
      }
    },
    onSelectExistingAudit() {
      if (!this.selectedExistingAuditId) return
      console.log('🔄 Switching to audit ID:', this.selectedExistingAuditId)
      console.log('🔄 Current computed audit ID:', this.currentAuditId)
      console.log('🔄 All audit ID sources:', {
        selectedExistingAuditId: this.selectedExistingAuditId,
        auditId: this.auditId,
        routeParams: this.$route.params.auditId,
        routeQuery: this.$route.query.auditId
      })
      
      // Clear existing data before loading new audit
      this.auditInfo = {}
      this.selectedPolicyName = ''
      this.selectedSubPolicyName = ''
      this.auditHierarchyPolicies = []
      this.selectedPolicyIdsMulti = []
      this.selectedSubpolicyIdsMulti = []
      this.selectedComplianceIds = []
      this.uploadedDocuments = []
      this.processingStatus = 'idle'
      this.processingResults = []
      // Clear SEBI data
      this.sebiEnabled = false
      this.sebiInsights = {
        filingAccuracy: null,
        timelinessSLA: null,
        riskScore: null,
        patterns: null
      }
      this.isLoadingSEBI = false
      
      // Now that user selected, mark confirmed and load data for the chosen audit inline
      this.hasUserConfirmedSelection = true
      this.$nextTick(async () => {
        console.log('🔄 Starting to load audit data...')
        
        // Load audit info first (this gives us framework_id)
        try {
          await this.loadAuditInfo()
          console.log('✅ loadAuditInfo completed, framework_id:', this.auditInfo.framework_id)
          
          // Check if SEBI AI Auditor is enabled and run checks
          if (this.auditInfo.framework_id) {
            try {
              await this.checkAndRunSEBIChecks()
            } catch (e) {
              console.warn('⚠️ SEBI checks failed (non-critical):', e.message)
            }
          }
        } catch (e) {
          console.error('❌ Error in loadAuditInfo:', e)
        }
        
        // Load hierarchy immediately after audit info (don't wait for policies)
        // This uses framework_id directly, so it doesn't need the slow /api/policies/ call
        try {
          console.log('🔄 About to call loadAuditHierarchy...')
          await this.loadAuditHierarchy()
          console.log('✅ loadAuditHierarchy completed, policies count:', this.auditHierarchyPolicies.length)
        } catch (e) {
          console.error('❌ Error in loadAuditHierarchy:', e)
          console.error('Error details:', e.response?.data || e.message)
        }
        
        // Load policies in background (for other features, but don't block on it)
        try {
          await Promise.race([
            this.loadPolicies(),
            new Promise((_, reject) => setTimeout(() => reject(new Error('Timeout')), 5000))
          ])
          console.log('✅ loadPolicies completed')
        } catch (e) {
          console.warn('⚠️ loadPolicies timed out or failed (non-critical):', e.message)
        }
        
        // Load uploaded documents
        try {
          await this.loadUploadedDocuments()
          console.log('✅ loadUploadedDocuments completed')
        } catch (e) {
          console.error('❌ Error in loadUploadedDocuments:', e)
        }
        
        // Load relevant documents from file_operations
        // DISABLED: No longer needed since we do automatic processing
        // Documents are automatically linked when uploaded via Document Handling
        // try {
        //   await this.loadRelevantDocuments()
        //   console.log('✅ loadRelevantDocuments completed')
        // } catch (e) {
        //   console.error('❌ Error in loadRelevantDocuments:', e)
        // }
        
        this.startStatusPolling()
      })
    },
    async loadAuditInfo() {
      try {
        const auditId = this.currentAuditId
        console.log('🔄 Loading audit info for ID:', auditId)
        
        if (!auditId || auditId === 'Unknown') {
          console.warn('No audit ID available, using default audit')
          this.auditInfo = {
            title: 'AI Audit Document Upload',
            type: 'AI Audit',
            framework: 'Default Framework'
          }
          return
        }
        
        // Load audit details
        const response = await api.get(`/api/audits/${auditId}/task-details/`)
        console.log('🔍 API Response for audit', auditId, ':', response.data)
        console.log('🔍 Policy from API:', response.data?.policy_name)
        console.log('🔍 Sub-policy from API:', response.data?.subpolicy_name)
        console.log('🔍 Framework from API:', response.data?.framework_name)
        console.log('🔍 Framework ID from API:', response.data?.framework_id)
        
        if (response.data && !response.data.error) {
          // Extract actual audit data from the API response
          // Handle framework_id - it might be 0, null, undefined, or empty string
          const frameworkId = response.data.framework_id
          const validFrameworkId = (frameworkId && frameworkId !== 0 && frameworkId !== '0' && frameworkId !== '') ? frameworkId : null
          
          this.auditInfo = {
            title: response.data.title || `Audit ${auditId}`,
            type: 'AI Audit', // Since this is the AI audit upload page
            framework: response.data.framework_name || 'Framework Not Set',
            framework_id: validFrameworkId,
            policy: response.data.policy_name || 'Not Specified',
            subpolicy: response.data.subpolicy_name || 'Not Specified'
          }
          console.log('✅ Stored auditInfo with framework_id:', this.auditInfo.framework_id, '(raw:', frameworkId, ')')
          
          // Pre-populate the selected policy and sub-policy
          this.selectedPolicyName = response.data.policy_name || 'Not Specified'
          this.selectedSubPolicyName = response.data.subpolicy_name || 'Not Specified'
          
          console.log('✅ Updated selectedPolicyName to:', this.selectedPolicyName)
          console.log('✅ Updated selectedSubPolicyName to:', this.selectedSubPolicyName)
          
          // Load compliance requirements in background (non-blocking, don't await)
          // This is for the old single-policy display, not needed for multi-select hierarchy
          console.log('🔍 Loading compliance by policy and sub-policy names (non-blocking)')
          this.loadComplianceByPolicyNames(response.data.policy_name, response.data.subpolicy_name).catch(e => {
            console.warn('⚠️ loadComplianceByPolicyNames failed (non-critical):', e.message)
          })

          // Also resolve and store IDs for mapping enforcement (non-blocking)
          this.findPolicyIdByName(this.selectedPolicyName).then(policyId => {
            if (policyId) {
              this.selectedPolicyId = policyId
              // Attempt to resolve subpolicy under this policy
              api.get(`/api/compliance/policies/${policyId}/subpolicies/`).then(spRes => {
                const sp = spRes.data?.subpolicies?.find(sp => sp.SubPolicyName?.toLowerCase() === this.selectedSubPolicyName?.toLowerCase())
                if (sp) this.selectedSubPolicyId = sp.SubPolicyId || sp.id
              }).catch(() => { /* ignore */ })
            }
          }).catch(e => {
            console.log('ℹ️ Could not auto-resolve policy/subpolicy IDs (non-critical)', e)
          })
        } else {
          // Fallback data if API returns error
          console.warn('❌ API returned error or no data for audit', auditId)
          this.auditInfo = {
            title: `Audit ${auditId}`,
            type: 'AI Audit',
            framework: 'Framework Not Set',
            policy: 'Not Specified',
            subpolicy: 'Not Specified'
          }
          this.selectedPolicyName = 'Not Specified'
          this.selectedSubPolicyName = 'Not Specified'
        }
        console.log('🎯 Final audit info for', auditId, ':', this.auditInfo)
      } catch (error) {
        console.error('Error loading audit info:', error)
        // Set fallback data on error
        this.auditInfo = {
          title: `Audit ${this.currentAuditId}`,
          type: 'AI Audit',
          framework: 'Framework Not Set',
          policy: 'Not Specified',
          subpolicy: 'Not Specified'
        }
        this.selectedPolicyName = 'Not Specified'
        this.selectedSubPolicyName = 'Not Specified'
      }
    },
    async checkAndRunSEBIChecks() {
      /**
       * Check if SEBI AI Auditor is enabled for this framework
       * If enabled, automatically run SEBI compliance checks
       */
      const auditId = this.currentAuditId
      const frameworkId = this.auditInfo.framework_id
      
      if (!auditId || !frameworkId) {
        console.log('ℹ️ SEBI check skipped: missing auditId or frameworkId')
        return
      }
      
      try {
        this.isLoadingSEBI = true
        console.log('🔍 Checking SEBI AI Auditor status for framework:', frameworkId)
        
        // Check if SEBI is enabled via dashboard endpoint
        const dashboardResponse = await api.get(`/api/sebi-auditor/dashboard/`, {
          params: { framework_id: frameworkId }
        })
        
        if (dashboardResponse.data && dashboardResponse.data.sebi_enabled) {
          this.sebiEnabled = true
          console.log('✅ SEBI AI Auditor enabled - running checks for audit:', auditId)
          
          // Run SEBI checks in parallel (non-blocking)
          Promise.all([
            // 1. Filing Accuracy Verification
            api.get(`/api/sebi-auditor/audit/${auditId}/filing-accuracy/`).then(res => {
              this.sebiInsights.filingAccuracy = res.data
              console.log('✅ SEBI Filing Accuracy:', res.data)
            }).catch(e => {
              console.warn('⚠️ SEBI Filing Accuracy check failed:', e.message)
            }),
            
            // 2. Timeliness & SLA Monitoring
            api.get(`/api/sebi-auditor/audit/${auditId}/timeliness-sla/`).then(res => {
              this.sebiInsights.timelinessSLA = res.data
              console.log('✅ SEBI Timeliness SLA:', res.data)
              
              // Show alert if SLA breach detected
              if (res.data.sla_breach && res.data.severity === 'high') {
                this.$popup?.warning(`SEBI SLA Breach: ${res.data.days_delayed} days delayed (${res.data.severity} severity)`)
              }
            }).catch(e => {
              console.warn('⚠️ SEBI Timeliness SLA check failed:', e.message)
            }),
            
            // 3. Risk Score Calculation
            api.get(`/api/sebi-auditor/audit/${auditId}/risk-score/`).then(res => {
              this.sebiInsights.riskScore = res.data
              console.log('✅ SEBI Risk Score:', res.data)
              
              // Show alert if high risk
              if (res.data.risk_level === 'High') {
                this.$popup?.warning(`SEBI High Risk Detected: Risk Score ${res.data.risk_score} (${res.data.risk_level})`)
              }
            }).catch(e => {
              console.warn('⚠️ SEBI Risk Score check failed:', e.message)
            }),
            
            // 4. Pattern Detection
            api.get(`/api/sebi-auditor/patterns/`, {
              params: { audit_id: auditId }
            }).then(res => {
              this.sebiInsights.patterns = res.data
              console.log('✅ SEBI Patterns:', res.data)
            }).catch(e => {
              console.warn('⚠️ SEBI Pattern detection failed:', e.message)
            })
          ]).then(() => {
            console.log('✅ All SEBI checks completed')
          }).catch(e => {
            console.warn('⚠️ Some SEBI checks failed:', e.message)
          })
          
        } else {
          this.sebiEnabled = false
          console.log('ℹ️ SEBI AI Auditor not enabled for this framework')
        }
      } catch (e) {
        console.warn('⚠️ SEBI check failed (non-critical):', e.message)
        this.sebiEnabled = false
      } finally {
        this.isLoadingSEBI = false
      }
    },
    // ----- Multi-select helpers -----
    toggleSelectAllPolicies() {
      if (this.allPoliciesSelected) {
        this.selectedPolicyIdsMulti = []
        this.selectedSubpolicyIdsMulti = []
        this.selectedComplianceIds = []
      } else {
        this.selectedPolicyIdsMulti = this.auditHierarchyPolicies.map(
          p => p.policy_id
        )
        // When selecting all policies, also select all subpolicies and compliances
        const allSubIds = []
        const allCompIds = []
        this.auditHierarchyPolicies.forEach(p => {
          (p.subpolicies || []).forEach(sp => {
            allSubIds.push(sp.subpolicy_id)
            const compliances = sp.compliances || []
            compliances.forEach(c => {
              allCompIds.push(c.compliance_id || c.ComplianceId)
            })
          })
        })
        this.selectedSubpolicyIdsMulti = Array.from(new Set(allSubIds))
        this.selectedComplianceIds = Array.from(new Set(allCompIds))
      }
      this.saveSelectionsForAudit()
    },
    toggleSelectAllSubpolicies() {
      const subs = this.availableSubpolicies
      if (!subs.length) return
      if (this.allSubpoliciesSelected) {
        this.selectedSubpolicyIdsMulti = []
        // Do not clear policies; user might still want them
      } else {
        this.selectedSubpolicyIdsMulti = subs.map(s => s.subpolicy_id)
      }
      this.saveSelectionsForAudit()
    },
    toggleSelectAllCompliances() {
      const comps = this.availableCompliances
      if (!comps.length) return
      if (this.allCompliancesSelected) {
        this.selectedComplianceIds = []
      } else {
        this.selectedComplianceIds = comps.map(c => c.compliance_id)
      }
      this.saveSelectionsForAudit()
    },
    onPolicyMultiChange(changedPolicyId) {
      const isSelected = this.selectedPolicyIdsMulti.includes(changedPolicyId)
      if (!isSelected) {
        // If policy deselected, also remove its subpolicies and compliances
        const subIdsToRemove = []
        const compIdsToRemove = []
        const policy = this.auditHierarchyPolicies.find(
          p => p.policy_id === changedPolicyId
        )
        if (policy) {
          (policy.subpolicies || []).forEach(sp => {
            subIdsToRemove.push(sp.subpolicy_id)
            const compliances = sp.compliances || []
            compliances.forEach(c => {
              compIdsToRemove.push(c.compliance_id || c.ComplianceId)
            })
          })
        }
        this.selectedSubpolicyIdsMulti = this.selectedSubpolicyIdsMulti.filter(
          id => !subIdsToRemove.includes(id)
        )
        this.selectedComplianceIds = this.selectedComplianceIds.filter(
          id => !compIdsToRemove.includes(id)
        )
      }
      this.saveSelectionsForAudit()
    },
    onSubpolicyMultiChange(subpolicyId, policyId) {
      const isSelected = this.selectedSubpolicyIdsMulti.includes(subpolicyId)
      if (!isSelected) {
        // If subpolicy deselected, also remove its compliances
        const policy = this.auditHierarchyPolicies.find(
          p => p.policy_id === policyId
        )
        if (policy) {
          const sub = (policy.subpolicies || []).find(
            sp => sp.subpolicy_id === subpolicyId
          )
          if (sub && sub.compliances) {
            const compIds = sub.compliances.map(
              c => c.compliance_id || c.ComplianceId
            )
            this.selectedComplianceIds = this.selectedComplianceIds.filter(
              id => !compIds.includes(id)
            )
          }
        }
      }
      this.saveSelectionsForAudit()
    },
    saveSelectionsForAudit() {
      try {
        const auditId = this.currentAuditId
        if (!auditId || auditId === 'Unknown') return
        const key = `aiAuditSelections:${auditId}`
        const payload = {
          policies: this.selectedPolicyIdsMulti,
          subpolicies: this.selectedSubpolicyIdsMulti,
          compliances: this.selectedComplianceIds
        }
        window.localStorage.setItem(key, JSON.stringify(payload))
      } catch (e) {
        console.warn('Could not persist AI audit selections:', e)
      }
    },
    restoreSelectionsForAudit() {
      try {
        const auditId = this.currentAuditId
        if (!auditId || auditId === 'Unknown') return
        const key = `aiAuditSelections:${auditId}`
        const raw = window.localStorage.getItem(key)
        if (!raw) return
        const parsed = JSON.parse(raw)
        this.selectedPolicyIdsMulti = parsed.policies || []
        this.selectedSubpolicyIdsMulti = parsed.subpolicies || []
        this.selectedComplianceIds = parsed.compliances || []
      } catch (e) {
        console.warn('Could not restore AI audit selections:', e)
      }
    },
    
    async loadPolicies() {
      try {
        // Try to load policies, but don't fail if permission denied
        const response = await api.get('/api/policies/')
        this.policies = response.data || []
      } catch (error) {
        console.error('Error loading policies:', error)
        // Set empty array if policies can't be loaded
        this.policies = []
      }
    },
    
    async onPolicyChange() {
      this.selectedSubPolicyId = ''
      this.subpolicies = []
      this.complianceRequirements = []
      
      if (this.selectedPolicyId) {
        console.log('🔍 Policy changed to:', this.selectedPolicyId, 'Type:', typeof this.selectedPolicyId)
        try {
          // Get JWT token for authentication
          const token = localStorage.getItem('access_token')
          const headers = { 'Content-Type': 'application/json' }
          if (token) {
            headers['Authorization'] = `Bearer ${token}`
          }
          
          // Load subpolicies - using the correct API endpoint
          const response = await api.get(`/api/compliance/policies/${this.selectedPolicyId}/subpolicies/`, { headers })
          console.log('🔍 Subpolicies response:', response.data)
          if (response.data && response.data.success) {
            this.subpolicies = response.data.subpolicies || []
            console.log('🔍 Loaded subpolicies:', this.subpolicies.length)
          } else {
            this.subpolicies = []
            console.log('🔍 No subpolicies in response')
          }
          
          // Load compliance requirements
          await this.loadComplianceRequirements(this.selectedPolicyId);
        } catch (error) {
          console.error('Error loading subpolicies:', error)
          // If it's a 404, it means no subpolicies exist for this policy
          if (error.response && error.response.status === 404) {
            console.log('ℹ️ No subpolicies found for this policy')
            this.subpolicies = []
          }
        }
      }
    },
    
    async findPolicyIdByName(policyName) {
      try {
        if (!policyName || policyName === 'Not Specified') {
          return null;
        }
        
        // First check if policies are already loaded
        if (this.policies.length === 0) {
          console.log('🔍 Loading policies to find ID for:', policyName)
          await this.loadPolicies();
        }
        
        // Search for policy by name (case-insensitive)
        const policy = this.policies.find(p => 
          p.PolicyName?.toLowerCase() === policyName.toLowerCase() ||
          p.policy_name?.toLowerCase() === policyName.toLowerCase() ||
          p.name?.toLowerCase() === policyName.toLowerCase()
        );
        
        if (policy) {
          return policy.PolicyId || policy.policy_id || policy.id;
        }
        
        // If not found in loaded policies, try API search
        console.log('🔍 Policy not found in cache, searching via API')
        const response = await api.get('/api/policies/', {
          params: { search: policyName }
        });
        
        if (response.data && response.data.length > 0) {
          const foundPolicy = response.data.find(p => 
            p.PolicyName?.toLowerCase() === policyName.toLowerCase() ||
            p.policy_name?.toLowerCase() === policyName.toLowerCase()
          );
          return foundPolicy ? (foundPolicy.PolicyId || foundPolicy.policy_id || foundPolicy.id) : null;
        }
        
        return null;
      } catch (error) {
        console.error('❌ Error finding policy ID by name:', error);
        return null;
      }
    },

    async loadComplianceByPolicyNames(policyName, subPolicyName) {
      try {
        console.log('🔍 Loading compliance by names - Policy:', policyName, 'Sub-policy:', subPolicyName)
        
        // First, find the policy and sub-policy IDs, then get compliance requirements
        console.log('🔍 Step 1: Finding policy and sub-policy IDs')
        
        // Find policy ID by name
        let policyId = null;
        let subPolicyId = null;
        
        try {
          if (this.policies.length === 0) {
            await this.loadPolicies();
          }
          
          const policy = this.policies.find(p => 
            p.PolicyName?.toLowerCase() === policyName?.toLowerCase() ||
            p.policy_name?.toLowerCase() === policyName?.toLowerCase()
          );
          
          if (policy) {
            policyId = policy.PolicyId || policy.policy_id;
            console.log('✅ Found policy ID:', policyId, 'for policy:', policyName);
            
            // Now find sub-policy ID
            try {
              const subPolicyResponse = await api.get(`/api/compliance/policies/${policyId}/subpolicies/`);
              if (subPolicyResponse.data.success && subPolicyResponse.data.subpolicies) {
                const subPolicy = subPolicyResponse.data.subpolicies.find(sp => 
                  sp.SubPolicyName?.toLowerCase() === subPolicyName?.toLowerCase() ||
                  sp.name?.toLowerCase() === subPolicyName?.toLowerCase()
                );
                
                if (subPolicy) {
                  subPolicyId = subPolicy.SubPolicyId || subPolicy.id;
                  console.log('✅ Found sub-policy ID:', subPolicyId, 'for sub-policy:', subPolicyName);
                }
              }
            } catch (error) {
              console.log('❌ Error finding sub-policy ID:', error.response?.status);
            }
          }
        } catch (error) {
          console.log('❌ Error finding policy ID:', error.response?.status);
        }
        
        // Try different API endpoints using the IDs we found
        const endpoints = [];
        
        if (policyId) {
          endpoints.push(`/api/compliance/view/policy/${policyId}`);
          endpoints.push(`/compliances/policy/${policyId}/`);
        }
        
        if (subPolicyId) {
          endpoints.push(`/api/compliance/view/subpolicy/${subPolicyId}`);
          endpoints.push(`/api/subpolicies/${subPolicyId}/compliances/`);
          endpoints.push(`/compliances/subpolicy/${subPolicyId}/`);
        }
        
        // Also try the type-based endpoints
        if (policyId) {
          endpoints.push(`/compliance/view/policy/${policyId}`);
        }
        if (subPolicyId) {
          endpoints.push(`/compliance/view/subpolicy/${subPolicyId}`);
        }
        
        let foundCompliances = [];
        
        for (const endpoint of endpoints) {
          try {
            console.log('🔍 Trying endpoint:', endpoint)
            const response = await api.get(endpoint);
            console.log('🔍 Response from', endpoint, ':', response.data)
            
            if (response.data && Array.isArray(response.data)) {
              foundCompliances = response.data;
              console.log('✅ Found compliances via', endpoint, ':', foundCompliances.length, 'items')
              break;
            } else if (response.data && response.data.compliances && Array.isArray(response.data.compliances)) {
              foundCompliances = response.data.compliances;
              console.log('✅ Found compliances via', endpoint, ':', foundCompliances.length, 'items')
              break;
            }
          } catch (error) {
            console.log('❌ Endpoint', endpoint, 'failed:', error.response?.status)
            continue;
          }
        }
        
        // Format compliance data for display
        if (foundCompliances.length > 0) {
          this.complianceRequirements = foundCompliances.map(comp => ({
            compliance_id: comp.ComplianceId || comp.compliance_id || comp.id,
            compliance_title: comp.ComplianceTitle || comp.compliance_title || comp.title || comp.ComplianceItemDescription,
            compliance_description: comp.ComplianceItemDescription || comp.compliance_description || comp.description,
            compliance_type: comp.ComplianceType || comp.compliance_type || 'Mandatory',
            risk_level: comp.Criticality || comp.risk_level || 'Medium',
            mandatory: (comp.MandatoryOptional || comp.mandatory) === 'Mandatory' || comp.mandatory === true
          }));
          console.log('✅ Formatted compliance requirements:', this.complianceRequirements.length, 'items')
        } else {
          console.log('ℹ️ No compliance requirements found for this policy/sub-policy combination')
          this.complianceRequirements = [];
        }
        
      } catch (error) {
        console.error('❌ Error loading compliance by policy names:', error);
        this.complianceRequirements = [];
      }
    },

    async loadComplianceRequirements(policyId) {
      try {
        console.log('🔍 Loading compliance requirements for policy:', policyId)
        const response = await api.get(`/api/compliance-mapping/requirements/${policyId}/`);
        console.log('🔍 Compliance API response:', response.data)
        if (response.data.success) {
          this.complianceRequirements = response.data.requirements;
          console.log('✅ Loaded compliance requirements:', this.complianceRequirements.length, 'items')
        } else {
          console.warn('❌ Compliance API returned no success flag')
          this.complianceRequirements = [];
        }
      } catch (error) {
        console.error('❌ Error loading compliance requirements:', error);
        if (error.response?.status === 404) {
          console.log('ℹ️ No compliance requirements found for this policy (404)');
        } else {
          console.error('❌ Server error loading compliance requirements:', error.response?.status);
        }
        this.complianceRequirements = [];
      }
    },
    
    async analyzeDocumentRelevance() {
      try {
        console.log('🤖 Starting document relevance analysis...')
        console.log('📄 Uploaded documents:', this.uploadedDocuments.length)
        console.log('📋 Compliance requirements:', this.complianceRequirements.length)
        
        if (this.uploadedDocuments.length === 0 || this.complianceRequirements.length === 0) {
          console.log('❌ No documents or compliance requirements to analyze')
          return
        }
        
        // Analyze each uploaded document against compliance requirements
        const mappingResults = []
        
        for (const document of this.uploadedDocuments) {
          console.log(`🔍 Analyzing document: ${document.document_name}`)
          
          // Call AI endpoint to analyze document relevance
          try {
            console.log('🤖 AI Analysis - Using audit ID:', this.currentAuditId)
            console.log('🤖 AI Analysis - Document ID:', document.document_id)
            console.log('🤖 AI Analysis - Document name:', document.document_name)
            const response = await api.post(`/api/ai-audit/${this.currentAuditId}/analyze-document-relevance/`, {
              document_id: document.document_id,
              document_name: document.document_name,
              compliance_requirements: this.complianceRequirements
            })
            
            if (response.data.success) {
              mappingResults.push({
                document_id: document.document_id,
                document_name: document.document_name,
                relevance_scores: response.data.relevance_scores,
                suggested_compliances: response.data.suggested_compliances
              })
              
              console.log(`✅ Relevance analysis complete for: ${document.document_name}`)
              console.log('🎯 Suggested compliances:', response.data.suggested_compliances)
            }
          } catch (error) {
            console.error(`❌ Error analyzing ${document.document_name}:`, error)
            console.error('❌ AI endpoint not available - skipping document analysis')
            
            // Show error message instead of fallback
            this.$popup?.warning(`AI analysis failed for "${document.document_name}". Please ensure AI services are running.`)
          }
        }
        
        // Store mapping results and show selection interface
        this.documentComplianceMapping = mappingResults
        
        // Show compliance selection modal/interface
        this.showComplianceSelectionInterface()
        
      } catch (error) {
        console.error('❌ Error in document relevance analysis:', error)
      }
    },
    
    
    showComplianceSelectionInterface() {
      console.log('📋 Showing compliance selection interface')
      console.log('🗂️ Document compliance mapping:', this.documentComplianceMapping)
      
      // Set flag to show the compliance selection modal/section
      this.showComplianceSelection = true
      
      // Auto-select suggested compliance requirements with high relevance
      this.selectedComplianceIds = []
      for (const mapping of this.documentComplianceMapping) {
        for (const suggestion of mapping.suggested_compliances) {
          if (suggestion.relevance_score >= 0.6 && !this.selectedComplianceIds.includes(suggestion.compliance_id)) {
            this.selectedComplianceIds.push(suggestion.compliance_id)
          }
        }
      }
      
      console.log('✅ Auto-selected compliance IDs:', this.selectedComplianceIds)
    },
    
    proceedWithSelectedCompliances() {
      console.log('🚀 Proceeding with AI processing for selected compliance requirements')
      console.log('📋 Selected compliance IDs:', this.selectedComplianceIds)
      
      if (this.selectedComplianceIds.length === 0) {
        this.$popup?.warning('Please select at least one compliance requirement to process.')
        return
      }
      
      // Hide the selection interface
      this.showComplianceSelection = false
      
      // Start AI processing with selected compliance requirements
      this.startSelectiveAIProcessing()
    },
    
    selectAllCompliances() {
      console.log('✅ Selecting all compliance requirements')
      this.selectedComplianceIds = this.complianceRequirements.map(c => c.compliance_id)
      console.log('📋 All compliance IDs selected:', this.selectedComplianceIds)
    },
    
    cancelSelection() {
      console.log('❌ Cancelling compliance selection')
      this.showComplianceSelection = false
      this.selectedComplianceIds = []
      this.documentComplianceMapping = []
    },
    
    async startSelectiveAIProcessing() {
      console.log('🤖 Starting selective AI processing...')
      console.log('📋 Processing compliance IDs:', this.selectedComplianceIds)
      console.log('📄 Processing documents:', this.uploadedDocuments.length)
      
      try {
        // Call AI processing endpoint with selected compliance requirements
        const response = await api.post(`/api/ai-audit/${this.currentAuditId}/start-selective-processing/`, {
          selected_compliance_ids: this.selectedComplianceIds,
          document_compliance_mapping: this.documentComplianceMapping
        })
        
        if (response.data.success) {
          this.$popup?.success('AI processing started! Check the status below for progress.')
          
          // Start polling for results
          this.startStatusPolling()
        } else {
          this.$popup?.error('Failed to start AI processing: ' + response.data.error)
        }
        
      } catch (error) {
        console.error('❌ Error starting selective AI processing:', error)
        
        // Fallback: Use existing AI processing method
        console.log('🔄 Falling back to standard AI processing...')
        this.$popup?.info('Using standard AI processing method...')
        this.startAIProcessing()
      }
    },

    triggerFileUpload() {
      this.$refs.fileInput.click()
    },
    
    handleFileSelect(event) {
      console.log('🔍 File select event triggered')
      const files = Array.from(event.target.files)
      console.log('🔍 Selected files from input:', files)
      this.addFiles(files)
    },
    
    handleDrop(event) {
      this.isDragOver = false
      const files = Array.from(event.dataTransfer.files)
      this.addFiles(files)
    },
    
    addFiles(files) {
      console.log('🔍 addFiles called with:', files)
      const validFiles = files.filter(file => {
        const extension = '.' + file.name.split('.').pop().toLowerCase()
        const allowedExtensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.csv', '.json']
        return allowedExtensions.includes(extension) && file.size <= 100 * 1024 * 1024 // 100MB
      })
      
      console.log('🔍 Valid files after filtering:', validFiles)
      console.log('🔍 Current selectedFiles before adding:', this.selectedFiles)
      
      this.selectedFiles = [...this.selectedFiles, ...validFiles]
      
      console.log('🔍 selectedFiles after adding:', this.selectedFiles)
    },
    
    removeFile(index) {
      this.selectedFiles.splice(index, 1)
    },
    
    clearFiles() {
      this.selectedFiles = []
    },
    
    formatFileSize(bytes) {
      if (bytes === 0) return '0 Bytes'
      const k = 1024
      const sizes = ['Bytes', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    },
    
    formatDate(dateString) {
      if (!dateString) return 'N/A'
      try {
        const date = new Date(dateString)
        return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
      } catch (e) {
        return dateString
      }
    },
    
    getFileIcon(fileType) {
      if (!fileType) return 'fa-file'
      const type = fileType.toLowerCase()
      if (type === 'pdf') return 'fa-file-pdf'
      if (type === 'xlsx' || type === 'xls') return 'fa-file-excel'
      if (type === 'doc' || type === 'docx') return 'fa-file-word'
      if (type === 'txt') return 'fa-file-alt'
      if (type === 'csv') return 'fa-file-csv'
      return 'fa-file'
    },
    
    getRelevanceClass(score) {
      if (score >= 0.8) return 'relevance-high'
      if (score >= 0.6) return 'relevance-medium'
      return 'relevance-low'
    },
    
    async uploadFiles() {
      // Check consent before proceeding with audit document upload
      try {
        const consentService = (await import('@/services/consentService.js')).default;
        const { CONSENT_ACTIONS } = await import('@/utils/consentManager.js');
        
        const canProceed = await consentService.checkAndRequestConsent(
          CONSENT_ACTIONS.UPLOAD_AUDIT
        );
        
        // If user declined consent, stop here
        if (!canProceed) {
          console.log('Audit document upload cancelled by user (consent declined)');
          return;
        }
      } catch (consentError) {
        console.error('Error checking consent:', consentError);
        // Continue with upload if consent check fails
      }
      console.log('🔍 Upload button clicked!')
      console.log('🔍 Selected files:', this.selectedFiles)
      console.log('🔍 Selected files length:', this.selectedFiles.length)
      
      if (this.selectedFiles.length === 0) {
        console.warn('No files selected')
        return
      }

      // Note: Uploading without explicit policy/subpolicy selection is allowed.
      // The AI will analyze the document and determine relevance to all framework elements.

      // Build mapping combinations that actually have selected compliances
      const mappingPairs = []

      // If user selected compliances, derive mappings from those (primary driver)
      if (this.selectedComplianceIds && this.selectedComplianceIds.length > 0) {
        const selectedSet = new Set(this.selectedComplianceIds)
        const seen = new Map() // Use Map to track compliances per mapping

        this.availableCompliances.forEach(c => {
          if (!selectedSet.has(c.compliance_id)) return
          const key = `${c.policy_id || ''}-${c.subpolicy_id || ''}`
          
          if (!seen.has(key)) {
            seen.set(key, {
              policy_id: c.policy_id || '',
              subpolicy_id: c.subpolicy_id || '',
              compliance_ids: [],
              compliance_names: []
            })
          }
          // Track all compliances for this mapping
          const mapping = seen.get(key)
          mapping.compliance_ids.push(c.compliance_id)
          // Get compliance name if available
          const complianceName = c.compliance_name || c.ComplianceName || `Compliance ${c.compliance_id}`
          mapping.compliance_names.push(complianceName)
        })
        
        // Convert to array - NO DEDUPLICATION, show all mappings
        mappingPairs.push(...Array.from(seen.values()).map(m => ({
          policy_id: m.policy_id,
          subpolicy_id: m.subpolicy_id,
          compliance_ids: m.compliance_ids,
          compliance_names: m.compliance_names,
          compliance_count: m.compliance_ids.length
        })))
        
        console.log(`📊 Created ${mappingPairs.length} unique mappings from ${this.selectedComplianceIds.length} selected compliances`)
        mappingPairs.forEach((mp, idx) => {
          console.log(`  Mapping ${idx + 1}: policy_id=${mp.policy_id}, subpolicy_id=${mp.subpolicy_id}, compliances=${mp.compliance_count}:`, mp.compliance_names)
        })
      } else {
        // Fallback: derive mappings from selected policies/sub‑policies only
        const selectedPolicySet = new Set(this.selectedPolicyIdsMulti)
        const selectedSubSet = new Set(this.selectedSubpolicyIdsMulti)

        this.auditHierarchyPolicies.forEach(policy => {
          if (!selectedPolicySet.has(policy.policy_id)) return
          const subpolicies = policy.subpolicies || []
          const selectedSubsForPolicy = subpolicies.filter(sp =>
            selectedSubSet.size > 0
              ? selectedSubSet.has(sp.subpolicy_id)
              : true
          )

          if (selectedSubsForPolicy.length === 0) {
            // Policy selected without any specific sub‑policy
            mappingPairs.push({
              policy_id: policy.policy_id,
              subpolicy_id: ''
            })
          } else {
            selectedSubsForPolicy.forEach(sp => {
              mappingPairs.push({
                policy_id: policy.policy_id,
                subpolicy_id: sp.subpolicy_id
              })
            })
          }
        })
      }

      // Allow upload even without explicit mappings - AI will analyze document relevance
      // If no mappings selected, send empty array - backend will handle it
      if (!mappingPairs.length) {
        console.log('⚠️ No explicit mappings selected - uploading without mappings. AI will analyze document relevance.')
      }
      
      const auditId = this.currentAuditId
      console.log('🔍 Current audit ID for upload:', auditId)
      console.log('🔍 Audit ID type:', typeof auditId)
      console.log('🔍 Selected existing audit ID:', this.selectedExistingAuditId)
      console.log('🔍 Props auditId:', this.auditId)
      console.log('🔍 Route params auditId:', this.$route.params.auditId)
      console.log('🔍 Route query auditId:', this.$route.query.auditId)
      
      if (!auditId || auditId === 'Unknown') {
        console.warn('No valid audit ID, cannot upload files')
        this.$popup?.error('No valid audit ID. Please refresh the page.')
        return
      }
      
      this.uploading = true
      this.uploadProgress = 0
      
      try {
        const totalFiles = this.selectedFiles.length
        let completedFiles = 0

        // Upload each file ONCE with all mappings
        for (let i = 0; i < this.selectedFiles.length; i++) {
          let file = this.selectedFiles[i]
          let compressionMetadata = null

          // Compress file if beneficial
          if (shouldCompressFile(file)) {
            try {
              this.uploadProgress = Math.round((completedFiles / totalFiles) * 100)
              const result = await compressFile(file)
              file = result.compressedFile
              compressionMetadata = {
                original_size: result.originalSize,
                compressed_size: result.compressedSize,
                ratio: result.compressionRatio
              }
              console.log(`✅ Compression complete for ${this.selectedFiles[i].name}: ${result.compressionRatio}% reduction`)
            } catch (error) {
              console.warn('⚠️ Compression failed, uploading original file:', error)
              // Continue with original file if compression fails
            }
          }

          const formData = new FormData()

          // Append file (possibly compressed)
          formData.append('file', file)
          formData.append('document_type', 'evidence')
          formData.append('external_source', 'manual')
          
          // Include compression metadata if available
          if (compressionMetadata) {
            formData.append('compression_metadata', JSON.stringify(compressionMetadata))
          }
          
          // Append all mappings as JSON array
          formData.append('mappings', JSON.stringify(mappingPairs))

          const response = await api.post(
            `/api/ai-audit/${auditId}/upload-document/`,
            formData,
            {
              // Don't set Content-Type manually - let axios/browser set it with boundary automatically
              onUploadProgress: progressEvent => {
                const singleFileProgress =
                  (progressEvent.loaded / progressEvent.total) || 0
                const overallProgress =
                  ((completedFiles + singleFileProgress) / totalFiles) * 100
                this.uploadProgress = Math.round(overallProgress)
              }
            }
          )

          if (response.data.success) {
            const mappingsCount = response.data.mappings_count || mappingPairs.length
            this.$popup?.success(
              `File "${file.name}" uploaded successfully with ${mappingsCount} mapping(s)`
            )
          }

          completedFiles += 1
          this.uploadProgress = Math.round(
            (completedFiles / totalFiles) * 100
          )
        }

        this.selectedFiles = []
        this.uploadProgress = 100
        await this.loadUploadedDocuments()
        
        // Show success popup for all files uploaded
        this.$popup?.success(`Successfully uploaded ${totalFiles} file(s). Documents are now available in the Uploaded Documents section.`)
        // AI relevance analysis is disabled per request
        
      } catch (error) {
        console.error('❌ Upload error details:', error)
        console.error('❌ Error response:', error.response?.data)
        console.error('❌ Error status:', error.response?.status)
        console.error('❌ Error message:', error.message)
        
        let errorMessage = 'Error uploading files. Please try again.'
        if (error.response?.data?.error) {
          errorMessage = `Upload failed: ${error.response.data.error}`
        } else if (error.message) {
          errorMessage = `Upload failed: ${error.message}`
        }
        
        this.$popup?.error(errorMessage)
      } finally {
        this.uploading = false
        this.uploadProgress = 0
      }
    },
    
    async loadUploadedDocuments() {
      try {
        const auditId = this.currentAuditId
        if (!auditId || auditId === 'Unknown') {
          console.warn('No valid audit ID, skipping document load')
          return
        }
        console.log('📋 Loading documents for audit:', auditId)
        console.log('📋 Current uploadedDocuments count before load:', this.uploadedDocuments.length)

        // Preserve currently selected mapping per file (by file + mapping key)
        const previousSelections = new Map()
        if (Array.isArray(this.uploadedDocuments) && this.uploadedDocuments.length > 0) {
          this.uploadedDocuments.forEach(fileGroup => {
            if (!fileGroup || !fileGroup.mappings || fileGroup.mappings.length === 0) return
            const fileKey = `${fileGroup.document_name || ''}|${fileGroup.file_size || 0}`
            const selectedIdx = parseInt(fileGroup.selectedMappingIndex ?? 0) || 0
            const selectedMapping = fileGroup.mappings[selectedIdx] || fileGroup.mappings[0]
            if (!selectedMapping) return
            const mappingKey = selectedMapping.mapping_key || `${selectedMapping.policy_id || 'none'}-${selectedMapping.subpolicy_id || 'none'}`
            previousSelections.set(`${fileKey}::${mappingKey}`, true)
          })
        }

        const response = await api.get(`/api/ai-audit/${auditId}/documents/`, {
          timeout: 120000 // 2 minute timeout for large document lists
        })
        console.log('📋 Documents response:', response.data)
        console.log('📋 Response success:', response.data.success)
        console.log('📋 Response documents array length:', response.data.documents?.length || 0)
        console.log('📋 Raw response status:', response.status)
        if (response.data.success) {
          // Map API response fields to component expected fields
          const mappedDocs = response.data.documents.map(doc => {
            // Preserve root-level metadata from compliance_analyses BEFORE transforming it
            // (e.g., part_of_combined_check flag that gets lost when converting to array)
            let compliance_analyses_metadata = {}
            let compliance_analyses = doc.compliance_analyses || null
            
            if (compliance_analyses) {
              // Handle both string (JSON) and object formats
              if (typeof compliance_analyses === 'string') {
                try {
                  compliance_analyses = JSON.parse(compliance_analyses)
                } catch (e) {
                  console.warn('Failed to parse compliance_analyses:', e)
                  compliance_analyses = null
                }
              }
              
              // If it's an object (not an array), preserve metadata flags before transformation
              if (compliance_analyses && typeof compliance_analyses === 'object' && !Array.isArray(compliance_analyses)) {
                // Extract metadata flags like part_of_combined_check, combined_with_document_id, etc.
                compliance_analyses_metadata = {
                  part_of_combined_check: compliance_analyses.part_of_combined_check,
                  combined_with_document_id: compliance_analyses.combined_with_document_id,
                  combined_compliance_id: compliance_analyses.combined_compliance_id
                }
                
                // If it's an object with a 'compliance_analyses' key, extract it
                compliance_analyses = compliance_analyses.compliance_analyses || compliance_analyses
              }
              
              // Ensure it's an array for compatibility with existing code
              if (compliance_analyses && !Array.isArray(compliance_analyses)) {
                compliance_analyses = [compliance_analyses]
              }
            }
            
            // Preserve the original compliance_analyses object (with metadata) for filtering purposes
            // Store metadata in the root-level object for the filter to access
            const compliance_analyses_with_metadata = compliance_analyses ? {
              ...compliance_analyses_metadata,
              analyses: compliance_analyses
            } : (Object.keys(compliance_analyses_metadata).length > 0 ? compliance_analyses_metadata : null)
            
            return {
              document_id: doc.document_id,
              // For DB evidence, backend only has document_name; for files it has file_name
              document_name: doc.file_name || doc.document_name,
              file_size: doc.file_size,
              uploaded_date: doc.uploaded_date,
              document_type: doc.file_type,
              external_source: doc.external_source || null,
              external_id: doc.external_id || null,  // Add external_id for grouping by s3_key/stored_name
              processing_status: doc.ai_processing_status || doc.processing_status || 'pending',
              upload_status: doc.upload_status || 'uploaded',
              mapped_policy: doc.policy_name || doc.mapped_policy || null,
              mapped_subpolicy: doc.subpolicy_name || doc.mapped_subpolicy || null,
              compliance_status: doc.compliance_status || null,
              confidence_score: doc.confidence_score || null,
              compliance_analyses: compliance_analyses_with_metadata || compliance_analyses,
              // Store the combined check flag separately so it's not lost during transformation
              part_of_combined_check: compliance_analyses_metadata.part_of_combined_check === true,
              // Keep raw ids for potential future use
              policy_id: doc.policy_id || null,
              subpolicy_id: doc.subpolicy_id || null
            }
          })

          // Group documents by external_id (s3_key/stored_name) + file_size to handle cases where
          // the same physical file is uploaded with different module selections (which changes document_name).
          // Fallback to document_name + file_size if external_id is not available.
          // IMPORTANT: We deduplicate mappings by (policy_id, subpolicy_id) so that
          // the dropdown structure stays the same before and after checks, even if
          // multiple DB rows exist for the same mapping (e.g. old runs or 'Document' rows).
          const fileGroups = new Map()
          
          mappedDocs.forEach(d => {
            // CRITICAL: Group same files uploaded with different modules
            // PROBLEM: When same file is uploaded multiple times, each upload gets a NEW external_id (file_operation_id)
            // So external_id="1947", external_id="2006", external_id="1976" are all the SAME file but different uploads
            // SOLUTION: Normalize document_name to remove module-specific parts and use that for grouping
            
            let groupingKey = ''
            
            // Step 1: ALWAYS normalize document_name to remove module-specific parts
            // CRITICAL: external_id changes with each upload (1947, 2006, 1976 for same file)
            // So we MUST use normalized document_name, NOT external_id, for grouping
            if (d.document_name) {
              let normalizedName = d.document_name
              
              // Remove module-specific parts: _policy_, _audit_, _incident_, etc.
              // Pattern: ..._framework_MODULE_... → ..._framework_...
              normalizedName = normalizedName.replace(/_(policy|audit|incident|compliance|risk)_/gi, '_')
              
              // Extract stable part: everything after "basel_iii_framework" or "framework"
              // Example: "document_handling_20251224_basel_iii_framework_policy_baseliii_leverageratio_rawdata_1.xlsx"
              // After removing _policy_: "document_handling_20251224_basel_iii_framework_baseliii_leverageratio_rawdata_1.xlsx"
              // Match extracts: "basel_iii_framework_baseliii_leverageratio_rawdata_1.xlsx"
              const frameworkMatch = normalizedName.match(/(?:basel_iii_framework|framework)[^/]*$/i)
              if (frameworkMatch && frameworkMatch[0]) {
                groupingKey = frameworkMatch[0]
              } else {
                // Fallback: use normalized name (with module parts removed)
                // This still groups files better than using external_id
                groupingKey = normalizedName
              }
              
              // IMPORTANT: groupingKey is now set from normalized document_name
              // Do NOT overwrite it with external_id below!
            }
            
            // DO NOT use external_id for grouping - it changes with each upload!
            // Only use external_id if document_name is completely missing AND groupingKey is still empty
            
            // Step 2: Only use external_id if document_name is completely missing
            // DO NOT use external_id if document_name exists - it changes with each upload!
            if (!groupingKey && !d.document_name && d.external_id && d.external_id.trim()) {
              groupingKey = d.external_id.trim()
            }
            
            // Step 3: Final fallback
            if (!groupingKey) {
              groupingKey = d.document_name || `doc_${d.document_id || 'unknown'}`
            }
            
            // Group by normalized key + file size (same file = same size)
            // This ensures same files with different external_ids are grouped together
            const fileKey = `${groupingKey}|${d.file_size || 0}`
            
            // Debug logging for grouping
            if (mappedDocs.length > 1) {
              const normalizedFromName = d.document_name ? (() => {
                let n = d.document_name.replace(/_(policy|audit|incident|compliance|risk)_/gi, '_')
                const m = n.match(/(?:basel_iii_framework|framework)[^/]*$/i)
                return m ? m[0] : n
              })() : 'N/A'
              console.log(`📋 Grouping: name="${d.document_name}", external_id="${d.external_id || 'NULL'}", normalized_from_name="${normalizedFromName}", final_key="${groupingKey}", size=${d.file_size}, fileKey="${fileKey}"`)
            }
            
            if (!fileGroups.has(fileKey)) {
              fileGroups.set(fileKey, {
                document_name: d.document_name,
                file_size: d.file_size,
                uploaded_date: d.uploaded_date,
                document_type: d.document_type,
                external_source: d.external_source || null,
                // mappingsMap: Map<policy-subpolicy key, bestDoc>
                mappingsMap: new Map()
              })
              console.log(`📦 Created new fileGroup for fileKey: "${fileKey}"`)
            }
            
            const group = fileGroups.get(fileKey)
            // Include compliance_id in mapping key to handle multiple compliances under same policy/subpolicy
            // This ensures each compliance gets its own mapping entry
            const mappingKey = `${d.policy_id || 'none'}-${d.subpolicy_id || 'none'}-${d.compliance_id || 'none'}`
            const existing = group.mappingsMap.get(mappingKey)
            
            // Prefer the "best" record for this mapping:
            // 1) completed over pending/processing
            // 2) record with analyses over one without
            // 3) If same status and analyses, prefer the newer record (higher document_id) to avoid mixing old mappings
            // 4) otherwise keep the first one we saw
            let bestDoc = d
            if (existing) {
              const weight = status => {
                if (status === 'completed') return 2
                if (status === 'processing') return 1
                return 0 // pending / unknown
              }
              const existingStatus = existing.processing_status || 'pending'
              const newStatus = d.processing_status || 'pending'
              const existingWeight = weight(existingStatus)
              const newWeight = weight(newStatus)
              
              if (existingWeight > newWeight) {
                bestDoc = existing
              } else if (existingWeight === newWeight) {
                // Check if analyses exist (handle both array and object formats)
                const getAnalysesCount = (analyses) => {
                  if (!analyses) return 0
                  if (Array.isArray(analyses)) return analyses.length
                  if (typeof analyses === 'object') {
                    // Handle both 'analyses' (new structure) and 'compliance_analyses' (old structure)
                    const analysesArray = analyses.analyses || analyses.compliance_analyses
                    return Array.isArray(analysesArray) ? analysesArray.length : 0
                  }
                  return 0
                }
                const existingHasAnalyses = getAnalysesCount(existing.compliance_analyses) > 0
                const newHasAnalyses = getAnalysesCount(d.compliance_analyses) > 0
                
                if (existingHasAnalyses && !newHasAnalyses) {
                  bestDoc = existing
                } else if (!existingHasAnalyses && newHasAnalyses) {
                  bestDoc = d
                } else {
                  // If both have same status and analyses, prefer the newer record (higher document_id)
                  // This ensures we use the most recently checked/updated mapping
                  bestDoc = (d.document_id > (existing.document_id || 0)) ? d : existing
                }
              }
            }
            
            group.mappingsMap.set(mappingKey, bestDoc)
          })
          
          // Convert to array format for display
          const previousCount = this.uploadedDocuments.length
          console.log(`📊 Grouping complete: ${fileGroups.size} unique file(s) from ${mappedDocs.length} document record(s)`)
          fileGroups.forEach((group, fileKey) => {
            console.log(`  - fileKey: "${fileKey}" has ${group.mappingsMap.size} mapping(s)`)
          })
          this.uploadedDocuments = Array.from(fileGroups.entries()).map(([fileKey, group]) => {
            // Get document_id from first mapping (or first doc that created this group)
            let document_id = null
            if (group.mappingsMap.size > 0) {
              const firstMapping = Array.from(group.mappingsMap.values())[0]
              document_id = firstMapping.document_id
            }
            
            const mappings = []
            group.mappingsMap.forEach(d => {
              // Store document_id if not already set
              if (!document_id && d.document_id) {
                document_id = d.document_id
              }
              
              // Build mapping display string
              const mappingParts = []
              if (d.mapped_policy) {
                mappingParts.push(d.mapped_policy)
              }
              if (d.mapped_subpolicy) {
                mappingParts.push(d.mapped_subpolicy)
              }
              
              // Determine if this mapping already has stored analyses/results
              let hasExistingAnalyses = false
              if (d.compliance_analyses) {
                if (Array.isArray(d.compliance_analyses)) {
                  hasExistingAnalyses = d.compliance_analyses.length > 0
                } else if (typeof d.compliance_analyses === 'object') {
                  // Handle both 'analyses' (new structure) and 'compliance_analyses' (old structure)
                  const analysesArray = d.compliance_analyses.analyses || d.compliance_analyses.compliance_analyses
                  hasExistingAnalyses = Array.isArray(analysesArray) && analysesArray.length > 0
                }
              }

              // Find all compliances that belong to this policy/sub-policy mapping
              // CRITICAL: If compliance_id is stored in database (from manual upload), use it directly
              let compliancesForMapping = []
              let complianceIdsForMapping = []
              
              // First priority: Use compliance_id from database if it exists (manually uploaded documents)
              if (d.compliance_id) {
                const directCompliance = this.availableCompliances.find(c => c.compliance_id === d.compliance_id)
                if (directCompliance) {
                  compliancesForMapping = [directCompliance]
                  complianceIdsForMapping = [d.compliance_id]
                  console.log(`✅ Using direct compliance_id ${d.compliance_id} from database for mapping ${d.policy_id}-${d.subpolicy_id}`)
                } else {
                  // Compliance not found in availableCompliances, but still use the ID
                  complianceIdsForMapping = [d.compliance_id]
                  console.log(`⚠️ compliance_id ${d.compliance_id} from database not found in availableCompliances, but will use it anyway`)
                }
              }
              
              // Second priority: If no direct compliance_id, match by policy/subpolicy
              if (compliancesForMapping.length === 0) {
                compliancesForMapping = this.availableCompliances.filter(c => {
                  // Match by policy/subpolicy
                  const matchesPolicy = !d.policy_id || c.policy_id === d.policy_id
                  const matchesSubpolicy = !d.subpolicy_id || c.subpolicy_id === d.subpolicy_id
                  const isSelected =
                    !this.selectedComplianceIds || this.selectedComplianceIds.length === 0
                      ? true
                      : this.selectedComplianceIds.includes(c.compliance_id)
                  return matchesPolicy && matchesSubpolicy && isSelected
                })
                complianceIdsForMapping = compliancesForMapping.map(c => c.compliance_id)
              }

              // If no currently selected compliances match but we have historical
              // analyses, fall back to the compliance IDs present in the analyses
              if ((!compliancesForMapping || compliancesForMapping.length === 0) && hasExistingAnalyses) {
                let analysisList = []
                if (Array.isArray(d.compliance_analyses)) {
                  analysisList = d.compliance_analyses
                } else if (typeof d.compliance_analyses === 'object') {
                  // Handle both 'analyses' (new structure) and 'compliance_analyses' (old structure)
                  analysisList = d.compliance_analyses.analyses || d.compliance_analyses.compliance_analyses || []
                }
                const analysisIds = Array.from(
                  new Set(
                    (analysisList || [])
                      .map(a => a && a.compliance_id)
                      .filter(id => id != null)
                  )
                )
                if (analysisIds.length > 0) {
                  compliancesForMapping = this.availableCompliances.filter(c =>
                    analysisIds.includes(c.compliance_id)
                  )
                }
              }

              // Final guard: if there are still no compliances AND no analyses,
              // this is a brand‑new unmapped combination for file uploads.
              // BUT we want to show it if:
              // 1. It's database evidence (always show)
              // 2. It's pending/processing (auto-processing might still be running)
              // 3. It has a policy/subpolicy mapping (even without compliances)
              // 4. It has policy_id or subpolicy_id set (mapping exists in database)
              if ((!compliancesForMapping || compliancesForMapping.length === 0) && !hasExistingAnalyses) {
                if (d.external_source !== 'database_record' && d.document_type !== 'db_record') {
                  // For documents: only hide if it's completed with no mappings
                  // Show if pending/processing (auto-processing might still be running)
                  const status = d.processing_status || 'pending'
                  const hasPolicyMapping = d.policy_id || d.subpolicy_id || d.mapped_policy || d.mapped_subpolicy
                  
                  // IMPORTANT: Always show if policy_id or subpolicy_id exists (mapping was created)
                  // This ensures documents with mappings from auto-processing are visible
                  if (hasPolicyMapping) {
                    // Has mapping - always show it, even if compliances aren't loaded yet
                    // Don't return, continue to create the mapping entry
                  } else if (status === 'completed') {
                    // Only hide completed documents with no policy/subpolicy mapping
                    return
                  }
                  // Otherwise show it (pending/processing)
                }
              }
              
              const complianceNames = compliancesForMapping.map(c => 
                c.compliance_name || c.ComplianceName || `Compliance ${c.compliance_id}`
              )
              
              let mappingDisplay = mappingParts.length > 0 
                ? `${mappingParts.join(' → ')}`
                : 'Unmapped'
              
              // Add compliance count/names to display
              if (complianceNames.length > 0) {
                if (complianceNames.length <= 3) {
                  // Show all compliance names if 3 or fewer
                  mappingDisplay += ` (${complianceNames.join(', ')})`
                } else {
                  // Show count if more than 3
                  mappingDisplay += ` (${complianceNames.length} compliances: ${complianceNames.slice(0, 2).join(', ')}, ...)`
                }
              }
              // Removed "compliances loading..." message - just show the mapping without compliance names if not loaded yet
              
              // Use complianceIdsForMapping if we have it (from direct compliance_id), otherwise use from compliancesForMapping
              const finalComplianceIds = complianceIdsForMapping.length > 0 
                ? complianceIdsForMapping 
                : compliancesForMapping.map(c => c.compliance_id)
              
              mappings.push({
                ...d,
                mapping_display: mappingDisplay,
                mapping_key: `${d.policy_id || 'none'}-${d.subpolicy_id || 'none'}-${d.compliance_id || 'none'}`, // Include compliance_id to keep separate mappings
                compliance_names: complianceNames,
                compliance_ids: finalComplianceIds, // Use the compliance IDs we determined
                compliance_count: complianceNames.length > 0 ? complianceNames.length : finalComplianceIds.length
              })
            })
            
            // Work out which mapping should be selected for this file
            let selectedMappingIndex = 0
            mappings.forEach((m, idx) => {
              const key = `${fileKey}::${m.mapping_key || `${m.policy_id || 'none'}-${m.subpolicy_id || 'none'}`}`
              if (previousSelections.has(key) && selectedMappingIndex === 0) {
                selectedMappingIndex = idx
              }
            })

            // Extract combined_check_group_id from mappings if they're part of a combined check
            // The combined_check_group_id is stored at the top level of compliance_analyses JSON object
            let combinedCheckGroupId = null
            let combinedWithDocumentIds = null
            for (const mapping of mappings) {
              if (mapping.compliance_analyses) {
                try {
                  let analyses = mapping.compliance_analyses
                  if (typeof analyses === 'string') {
                    analyses = JSON.parse(analyses)
                  }
                  // The combined_check_group_id is stored at the top level of the compliance_analyses object
                  // Structure: { combined_check_group_id: "...", combined_with_document_ids: [...], compliance_analyses: [...] }
                  if (typeof analyses === 'object' && !Array.isArray(analyses)) {
                    if (analyses.combined_check_group_id) {
                      combinedCheckGroupId = analyses.combined_check_group_id
                      combinedWithDocumentIds = analyses.combined_with_document_ids || []
                      break // Found it, no need to check other mappings
                    }
                  }
                } catch (e) {
                  // Ignore parsing errors
                  console.warn('Failed to parse compliance_analyses for combined check group ID:', e)
                }
              }
            }
            
            return {
              document_id: document_id, // Store document_id at fileGroup level for delete button
              document_name: group.document_name,
              file_size: group.file_size,
              uploaded_date: group.uploaded_date,
              document_type: group.document_type,
              mappings,
              // Keep previously selected mapping if possible, otherwise default to first
              selectedMappingIndex,
              _expanded: false, // For expandable view
              combinedCheckGroupId, // ID for grouping documents that were combined in the same check
              combinedWithDocumentIds // List of document IDs that were combined together
            }
          })
          console.log('📋 Loaded files (grouped):', this.uploadedDocuments.length)
          console.log('📋 Previous count:', previousCount, '→ New count:', this.uploadedDocuments.length)
          if (this.uploadedDocuments.length > previousCount) {
            console.log('⚠️ NEW FILES DETECTED! Files appeared after reload:', this.uploadedDocuments.length - previousCount)
          }
          console.log('📋 File groups:', this.uploadedDocuments)
          // Debug mappings for each file
          this.uploadedDocuments.forEach((fileGroup, idx) => {
            console.log(`📋 File ${idx + 1} (${fileGroup.document_name}):`, {
              mappings_count: fileGroup.mappings.length,
              mappings: fileGroup.mappings.map(m => ({
                mapping: m.mapping_display,
                status: m.processing_status || m.ai_processing_status,
                has_analyses: !!m.compliance_analyses,
                shouldShowDetails: this.shouldShowDetailsButton(fileGroup)
              }))
            })
          })
          
          // Force Vue reactivity update to ensure UI reflects status changes
          this.$nextTick(() => {
            this.$forceUpdate()
          })
        } else {
          console.warn('📋 Failed to load documents:', response.data.error)
          this.uploadedDocuments = []
        }
        
        // Start polling for status updates if there are documents that might be processing
        // This ensures Details button appears as soon as documents are completed
        this.startStatusPolling()
      } catch (error) {
        console.error('Error loading uploaded documents:', error)
        if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
          console.error('⏱️ Request timed out - API may be slow or unresponsive')
          this.$popup?.error('Request timed out while loading documents. Please try refreshing the page.')
        } else if (error.response) {
          console.error('API Error:', error.response.status, error.response.data)
          this.$popup?.error(`Failed to load documents: ${error.response.data?.error || error.response.statusText || 'Unknown error'}`)
        } else {
          console.error('Network or other error:', error.message)
          this.$popup?.error(`Failed to load documents: ${error.message || 'Network error'}`)
        }
        this.uploadedDocuments = []
        
        // Start polling even on error, in case documents are being processed
        this.startStatusPolling()
      }
    },
    
    async loadRelevantDocuments() {
      try {
        const auditId = this.currentAuditId
        if (!auditId || auditId === 'Unknown') {
          console.warn('No valid audit ID, skipping relevant documents load')
          this.relevantDocuments = []
          return
        }
        
        this.isLoadingRelevantDocuments = true
        console.log('📋 Loading relevant documents for audit:', auditId)
        
        // Build query parameters based on selected policies/subpolicies/compliances
        const params = {}
        if (this.selectedPolicyIdsMulti.length > 0) {
          params.policy_ids = this.selectedPolicyIdsMulti.join(',')
        }
        if (this.selectedSubpolicyIdsMulti.length > 0) {
          params.subpolicy_ids = this.selectedSubpolicyIdsMulti.join(',')
        }
        if (this.selectedComplianceIds.length > 0) {
          params.compliance_ids = this.selectedComplianceIds.join(',')
        }
        
        const response = await api.get(`/api/ai-audit/${auditId}/relevant-documents/`, { params })
        console.log('📋 Relevant documents response:', response.data)
        
        if (response.data.success) {
          this.relevantDocuments = response.data.documents || []
          this.relevantDocumentsMessage = response.data.message || null
          this.relevantDocumentsStats = response.data.stats || null
          console.log('✅ Loaded', this.relevantDocuments.length, 'relevant documents')
          if (response.data.message) {
            console.log('📋 Message:', response.data.message)
          }
          if (response.data.stats) {
            console.log('📊 Stats:', response.data.stats)
          }
        } else {
          console.warn('📋 Failed to load relevant documents:', response.data.error)
          this.relevantDocuments = []
          this.relevantDocumentsMessage = response.data.error || null
          this.relevantDocumentsStats = null
        }
      } catch (error) {
        console.error('Error loading relevant documents:', error)
        this.relevantDocuments = []
      } finally {
        this.isLoadingRelevantDocuments = false
      }
    },
    
    toggleRelevantDocumentSelection(fileOperationId) {
      console.log('🔘 Toggling document selection:', fileOperationId)
      console.log('🔘 Current selectedRelevantDocuments:', this.selectedRelevantDocuments)
      const index = this.selectedRelevantDocuments.indexOf(fileOperationId)
      const isSelecting = index === -1
      
      if (isSelecting) {
        // Adding document to selection - auto-select its relevant policies/subpolicies/compliances
        this.selectedRelevantDocuments.push(fileOperationId)
        console.log('   ✅ Added to selection') 
        
        // Find the document and auto-select its matched policies/subpolicies/compliances
        const doc = this.relevantDocuments.find(d => d.file_operation_id === fileOperationId)
        if (!doc) {
          console.warn('   ⚠️ Document not found in relevantDocuments array')
          console.warn('   ⚠️ Available documents:', this.relevantDocuments.map(d => d.file_operation_id))
          return
        }
        
        console.log('   📄 Document found:', doc.file_name || doc.original_name)
        console.log('   📄 Full document data:', doc)
        console.log('   📄 Matched policies (raw):', doc.matched_policies)
        console.log('   📄 Matched policies (with names):', doc.matched_policies_with_names)
        console.log('   📄 Matched subpolicies (raw):', doc.matched_subpolicies)
        console.log('   📄 Matched subpolicies (with names):', doc.matched_subpolicies_with_names)
        console.log('   📄 Matched compliances (raw):', doc.matched_compliances)
        console.log('   📄 Matched compliances (with names):', doc.matched_compliances_with_names)
        console.log('   📄 Current selectedPolicyIdsMulti before:', this.selectedPolicyIdsMulti)
        console.log('   📄 Current selectedSubpolicyIdsMulti before:', this.selectedSubpolicyIdsMulti)
        console.log('   📄 Current selectedComplianceIds before:', this.selectedComplianceIds)
          
          // Auto-select matched policies
          const matchedPolicies = doc.matched_policies_with_names || doc.matched_policies || []
          let addedPolicies = 0
          
          // Get available policy IDs from hierarchy to ensure we only select valid ones
          const availablePolicyIds = this.auditHierarchyPolicies.map(p => {
            const pid = p.policy_id
            return typeof pid === 'string' ? parseInt(pid, 10) : pid
          })
          console.log('   📋 Available policy IDs in hierarchy:', availablePolicyIds)
          
          matchedPolicies.forEach(p => {
            // Handle both object format {id: X, name: Y} and direct ID format
            let policyId = typeof p === 'object' ? (p.id || p.policy_id) : p
            // Convert to number for consistent comparison
            policyId = typeof policyId === 'string' ? parseInt(policyId, 10) : policyId
            
            if (policyId && !isNaN(policyId)) {
              // Check if this policy ID exists in the hierarchy
              if (!availablePolicyIds.includes(policyId)) {
                console.warn(`   ⚠️ Policy ID ${policyId} not found in hierarchy, skipping`)
                return
              }
              
              // Check if already selected - compare both as numbers and strings
              const isAlreadySelected = this.selectedPolicyIdsMulti.some(id => {
                const idNum = typeof id === 'string' ? parseInt(id, 10) : id
                return idNum === policyId
              })
              
              if (!isAlreadySelected) {
                // Match the type used in the hierarchy (check first policy in hierarchy)
                const hierarchyPolicyId = this.auditHierarchyPolicies[0]?.policy_id
                const targetType = typeof hierarchyPolicyId
                const valueToAdd = targetType === 'string' ? String(policyId) : policyId
                
                this.selectedPolicyIdsMulti.push(valueToAdd)
                addedPolicies++
                console.log(`   ➕ Added policy ID: ${valueToAdd} (type: ${typeof valueToAdd})`)
              } else {
                console.log(`   ✓ Policy ID ${policyId} already selected`)
              }
            }
          })
          console.log(`   ✅ Added ${addedPolicies} policies (total: ${this.selectedPolicyIdsMulti.length})`)
          
          // Auto-select matched subpolicies
          const matchedSubpolicies = doc.matched_subpolicies_with_names || doc.matched_subpolicies || []
          let addedSubpolicies = 0
          
          // Get available subpolicy IDs from hierarchy
          const availableSubpolicyIds = []
          this.auditHierarchyPolicies.forEach(policy => {
            (policy.subpolicies || []).forEach(sp => {
              const spid = sp.subpolicy_id
              const spidNum = typeof spid === 'string' ? parseInt(spid, 10) : spid
              if (spidNum && !availableSubpolicyIds.includes(spidNum)) {
                availableSubpolicyIds.push(spidNum)
              }
            })
          })
          console.log('   📋 Available subpolicy IDs in hierarchy:', availableSubpolicyIds)
          
          matchedSubpolicies.forEach(sp => {
            let subpolicyId = typeof sp === 'object' ? (sp.id || sp.subpolicy_id) : sp
            subpolicyId = typeof subpolicyId === 'string' ? parseInt(subpolicyId, 10) : subpolicyId
            
            if (subpolicyId && !isNaN(subpolicyId)) {
              // Check if this subpolicy ID exists in the hierarchy
              if (!availableSubpolicyIds.includes(subpolicyId)) {
                console.warn(`   ⚠️ Subpolicy ID ${subpolicyId} not found in hierarchy, skipping`)
                return
              }
              
              const isAlreadySelected = this.selectedSubpolicyIdsMulti.some(id => {
                const idNum = typeof id === 'string' ? parseInt(id, 10) : id
                return idNum === subpolicyId
              })
              
              if (!isAlreadySelected) {
                // Match the type used in the hierarchy
                const hierarchySubpolicyId = this.auditHierarchyPolicies[0]?.subpolicies?.[0]?.subpolicy_id
                const targetType = hierarchySubpolicyId ? typeof hierarchySubpolicyId : 'number'
                const valueToAdd = targetType === 'string' ? String(subpolicyId) : subpolicyId
                
                this.selectedSubpolicyIdsMulti.push(valueToAdd)
                addedSubpolicies++
                console.log(`   ➕ Added subpolicy ID: ${valueToAdd} (type: ${typeof valueToAdd})`)
              } else {
                console.log(`   ✓ Subpolicy ID ${subpolicyId} already selected`)
              }
            }
          })
          console.log(`   ✅ Added ${addedSubpolicies} subpolicies (total: ${this.selectedSubpolicyIdsMulti.length})`)
          
          // Auto-select matched compliances
          // Also auto-select their parent subpolicies and policies
          const matchedCompliances = doc.matched_compliances_with_names || doc.matched_compliances || []
          let addedCompliances = 0
          const subpolicyIdsToAdd = new Set() // Track subpolicy IDs to add
          const policyIdsToAdd = new Set() // Track policy IDs to add
          
          // Get all available compliances with their parent relationships
          // Note: availableCompliances requires selected policies/subpolicies, so we'll search the hierarchy directly
          matchedCompliances.forEach(c => {
            let complianceId = typeof c === 'object' ? (c.id || c.compliance_id) : c
            complianceId = typeof complianceId === 'string' ? parseInt(complianceId, 10) : complianceId
            
            if (complianceId && !isNaN(complianceId)) {
              const isAlreadySelected = this.selectedComplianceIds.some(id => {
                const idNum = typeof id === 'string' ? parseInt(id, 10) : id
                return idNum === complianceId
              })
              
              if (!isAlreadySelected) {
                const existingType = this.selectedComplianceIds.length > 0 ? typeof this.selectedComplianceIds[0] : 'number'
                const valueToAdd = existingType === 'string' ? String(complianceId) : complianceId
                this.selectedComplianceIds.push(valueToAdd)
                addedCompliances++
                console.log(`   ➕ Added compliance ID: ${valueToAdd}`)
                
                // Get parent subpolicy and policy IDs directly from compliance data
                // Backend now includes subpolicy_id and policy_id in matched_compliances_with_names
                const subpolicyId = typeof c === 'object' ? (c.subpolicy_id || c.SubPolicyId) : null
                const policyId = typeof c === 'object' ? (c.policy_id || c.PolicyId) : null
                
                if (subpolicyId) {
                  const spIdNum = typeof subpolicyId === 'string' ? parseInt(subpolicyId, 10) : subpolicyId
                  if (spIdNum && !isNaN(spIdNum)) {
                    subpolicyIdsToAdd.add(spIdNum)
                    console.log(`   📍 Found parent subpolicy ${spIdNum} for compliance ${complianceId} (from compliance data)`)
                  }
                }
                
                if (policyId) {
                  const pIdNum = typeof policyId === 'string' ? parseInt(policyId, 10) : policyId
                  if (pIdNum && !isNaN(pIdNum)) {
                    policyIdsToAdd.add(pIdNum)
                    console.log(`   📍 Found parent policy ${pIdNum} for compliance ${complianceId} (from compliance data)`)
                  }
                }
                
                // Fallback: if not in compliance data, search hierarchy
                if (!subpolicyId || !policyId) {
                  console.warn(`   ⚠️ Compliance ${complianceId} missing parent IDs, searching hierarchy...`)
                  let found = false
                  for (const policy of this.auditHierarchyPolicies) {
                    for (const sp of (policy.subpolicies || [])) {
                      for (const comp of (sp.compliances || [])) {
                        const compId = comp.compliance_id || comp.ComplianceId
                        const compIdNum = typeof compId === 'string' ? parseInt(compId, 10) : compId
                        if (compIdNum === complianceId) {
                          const spId = sp.subpolicy_id
                          const spIdNum = typeof spId === 'string' ? parseInt(spId, 10) : spId
                          const pId = policy.policy_id
                          const pIdNum = typeof pId === 'string' ? parseInt(pId, 10) : pId
                          
                          if (spIdNum && !isNaN(spIdNum) && !subpolicyIdsToAdd.has(spIdNum)) {
                            subpolicyIdsToAdd.add(spIdNum)
                            console.log(`   📍 Found parent subpolicy ${spIdNum} for compliance ${complianceId} (from hierarchy)`)
                          }
                          if (pIdNum && !isNaN(pIdNum) && !policyIdsToAdd.has(pIdNum)) {
                            policyIdsToAdd.add(pIdNum)
                            console.log(`   📍 Found parent policy ${pIdNum} for compliance ${complianceId} (from hierarchy)`)
                          }
                          found = true
                          break
                        }
                      }
                      if (found) break
                    }
                    if (found) break
                  }
                  
                  if (!found) {
                    console.warn(`   ⚠️ Could not find compliance ${complianceId} in hierarchy`)
                  }
                }
              }
            }
          })
          console.log(`   ✅ Added ${addedCompliances} compliances (total: ${this.selectedComplianceIds.length})`)
          
          // Auto-select parent subpolicies for selected compliances
          let addedSubpoliciesFromCompliances = 0
          subpolicyIdsToAdd.forEach(subpolicyIdNum => {
            const isAlreadySelected = this.selectedSubpolicyIdsMulti.some(id => {
              const idNum = typeof id === 'string' ? parseInt(id, 10) : id
              return idNum === subpolicyIdNum
            })
            
            if (!isAlreadySelected) {
              // Find the subpolicy in hierarchy to get its type
              let hierarchySubpolicy = null
              for (const policy of this.auditHierarchyPolicies) {
                for (const sp of (policy.subpolicies || [])) {
                  const spId = sp.subpolicy_id
                  const spIdNum = typeof spId === 'string' ? parseInt(spId, 10) : spId
                  if (spIdNum === subpolicyIdNum) {
                    hierarchySubpolicy = sp
                    break
                  }
                }
                if (hierarchySubpolicy) break
              }
              
              const targetType = hierarchySubpolicy?.subpolicy_id ? typeof hierarchySubpolicy.subpolicy_id : 'number'
              const valueToAdd = targetType === 'string' ? String(subpolicyIdNum) : subpolicyIdNum
              this.selectedSubpolicyIdsMulti.push(valueToAdd)
              addedSubpoliciesFromCompliances++
              console.log(`   ➕ Added subpolicy ID ${valueToAdd} (parent of selected compliance)`)
            }
          })
          if (addedSubpoliciesFromCompliances > 0) {
            console.log(`   ✅ Added ${addedSubpoliciesFromCompliances} subpolicies from compliances`)
          }
          
          // Auto-select parent policies for selected subpolicies
          let addedPoliciesFromSubpolicies = 0
          policyIdsToAdd.forEach(policyIdNum => {
            const isAlreadySelected = this.selectedPolicyIdsMulti.some(id => {
              const idNum = typeof id === 'string' ? parseInt(id, 10) : id
              return idNum === policyIdNum
            })
            
            if (!isAlreadySelected) {
              // Find the policy in hierarchy to get its type
              const hierarchyPolicy = this.auditHierarchyPolicies.find(p => {
                const pId = p.policy_id
                const pIdNum = typeof pId === 'string' ? parseInt(pId, 10) : pId
                return pIdNum === policyIdNum
              })
              
              const targetType = hierarchyPolicy?.policy_id ? typeof hierarchyPolicy.policy_id : 'number'
              const valueToAdd = targetType === 'string' ? String(policyIdNum) : policyIdNum
              this.selectedPolicyIdsMulti.push(valueToAdd)
              addedPoliciesFromSubpolicies++
              console.log(`   ➕ Added policy ID ${valueToAdd} (parent of selected compliance)`)
            }
          })
          if (addedPoliciesFromSubpolicies > 0) {
            console.log(`   ✅ Added ${addedPoliciesFromSubpolicies} policies from compliances`)
          }
          
          console.log('   📋 Final selected policies:', this.selectedPolicyIdsMulti)
          console.log('   📋 Final selected subpolicies:', this.selectedSubpolicyIdsMulti)
          console.log('   📋 Final selected compliances:', this.selectedComplianceIds)
          
          // Force Vue to detect the array changes by reassigning
          // In Vue 3, reactivity is automatic, so we just reassign the arrays
          this.selectedPolicyIdsMulti = [...this.selectedPolicyIdsMulti]
          this.selectedSubpolicyIdsMulti = [...this.selectedSubpolicyIdsMulti]
          this.selectedComplianceIds = [...this.selectedComplianceIds]
          
          // Use nextTick to ensure Vue has processed the changes
          this.$nextTick(() => {
            console.log('   📋 After nextTick - selected policies:', this.selectedPolicyIdsMulti)
            console.log('   📋 After nextTick - selected subpolicies:', this.selectedSubpolicyIdsMulti)
            console.log('   📋 After nextTick - selected compliances:', this.selectedComplianceIds)
            
            // Verify the policy IDs exist in the hierarchy
            const availablePolicyIds = this.auditHierarchyPolicies.map(p => {
              const pid = p.policy_id
              return typeof pid === 'string' ? parseInt(pid, 10) : pid
            })
            console.log('   📋 Available policy IDs in hierarchy:', availablePolicyIds)
            const selectedPolicyIdsNums = this.selectedPolicyIdsMulti.map(id => typeof id === 'string' ? parseInt(id, 10) : id)
            const matchedPolicyIds = selectedPolicyIdsNums.filter(id => availablePolicyIds.includes(id))
            console.log('   📋 Matched policy IDs:', matchedPolicyIds)
            
            if (matchedPolicyIds.length !== this.selectedPolicyIdsMulti.length) {
              console.warn('   ⚠️ Some policy IDs are not in the hierarchy!')
              console.warn('   ⚠️ Selected:', this.selectedPolicyIdsMulti)
              console.warn('   ⚠️ Available:', availablePolicyIds)
            }
          })
          
          // Force Vue reactivity update
          this.$forceUpdate()
          
          // Save selections
          this.saveSelectionsForAudit()
          
          // Log to verify the checkboxes should reflect changes now
          console.log('   ✅ Arrays updated, checkboxes should reflect changes now')
      } else {
        // Removing document from selection
        this.selectedRelevantDocuments.splice(index, 1)
        console.log('   ✅ Removed from selection')
        
        // Optionally: unselect policies/subpolicies/compliances if no other selected documents use them
        // For now, we'll keep them selected (user can manually deselect if needed)
      }
      console.log('   📋 Selected documents:', this.selectedRelevantDocuments)
    },
    
    toggleSuggestedDocuments() {
      this.showSuggestedDocuments = !this.showSuggestedDocuments
    },
    
    toggleDocumentDetails(fileOperationId) {
      if (this.expandedDocumentId === fileOperationId) {
        this.expandedDocumentId = null
      } else {
        this.expandedDocumentId = fileOperationId
      }
    },
    
    selectAllRelevantDocuments() {
      this.selectedRelevantDocuments = this.relevantDocuments.map(doc => doc.file_operation_id)
      
      // Auto-select all policies/subpolicies/compliances from all selected documents
      const allPolicyIds = new Set()
      const allSubpolicyIds = new Set()
      const allComplianceIds = new Set()
      
      this.relevantDocuments.forEach(doc => {
        // Collect policies
        const matchedPolicies = doc.matched_policies_with_names || doc.matched_policies || []
        matchedPolicies.forEach(p => {
          const policyId = typeof p === 'object' ? (p.id || p.policy_id) : p
          const policyIdNum = typeof policyId === 'string' ? parseInt(policyId, 10) : policyId
          if (policyIdNum && !isNaN(policyIdNum)) {
            allPolicyIds.add(policyIdNum)
          }
        })
        
        // Collect subpolicies
        const matchedSubpolicies = doc.matched_subpolicies_with_names || doc.matched_subpolicies || []
        matchedSubpolicies.forEach(sp => {
          const subpolicyId = typeof sp === 'object' ? (sp.id || sp.subpolicy_id) : sp
          const subpolicyIdNum = typeof subpolicyId === 'string' ? parseInt(subpolicyId, 10) : subpolicyId
          if (subpolicyIdNum && !isNaN(subpolicyIdNum)) {
            allSubpolicyIds.add(subpolicyIdNum)
          }
        })
        
        // Collect compliances and their parent subpolicies/policies
        const matchedCompliances = doc.matched_compliances_with_names || doc.matched_compliances || []
        matchedCompliances.forEach(c => {
          const complianceId = typeof c === 'object' ? (c.id || c.compliance_id) : c
          const complianceIdNum = typeof complianceId === 'string' ? parseInt(complianceId, 10) : complianceId
          if (complianceIdNum && !isNaN(complianceIdNum)) {
            allComplianceIds.add(complianceIdNum)
            
            // Get parent subpolicy and policy IDs directly from compliance data
            const subpolicyId = typeof c === 'object' ? (c.subpolicy_id || c.SubPolicyId) : null
            const policyId = typeof c === 'object' ? (c.policy_id || c.PolicyId) : null
            
            if (subpolicyId) {
              const spIdNum = typeof subpolicyId === 'string' ? parseInt(subpolicyId, 10) : subpolicyId
              if (spIdNum && !isNaN(spIdNum)) {
                allSubpolicyIds.add(spIdNum)
              }
            }
            
            if (policyId) {
              const pIdNum = typeof policyId === 'string' ? parseInt(policyId, 10) : policyId
              if (pIdNum && !isNaN(pIdNum)) {
                allPolicyIds.add(pIdNum)
              }
            }
          }
        })
      })
      
      // Convert Sets to Arrays, matching the type used in the hierarchy
      const hierarchyPolicyId = this.auditHierarchyPolicies[0]?.policy_id
      const targetPolicyType = hierarchyPolicyId ? typeof hierarchyPolicyId : 'number'
      
      const hierarchySubpolicyId = this.auditHierarchyPolicies[0]?.subpolicies?.[0]?.subpolicy_id
      const targetSubpolicyType = hierarchySubpolicyId ? typeof hierarchySubpolicyId : 'number'
      
      const hierarchyComplianceId = this.auditHierarchyPolicies[0]?.subpolicies?.[0]?.compliances?.[0]?.compliance_id
      const targetComplianceType = hierarchyComplianceId ? typeof hierarchyComplianceId : 'number'
      
      this.selectedPolicyIdsMulti = Array.from(allPolicyIds).map(id => 
        targetPolicyType === 'string' ? String(id) : id
      )
      this.selectedSubpolicyIdsMulti = Array.from(allSubpolicyIds).map(id => 
        targetSubpolicyType === 'string' ? String(id) : id
      )
      this.selectedComplianceIds = Array.from(allComplianceIds).map(id => 
        targetComplianceType === 'string' ? String(id) : id
      )
      
      // Force Vue reactivity update
      this.$forceUpdate()
      
      console.log('📋 Auto-selected all policies:', this.selectedPolicyIdsMulti)
      console.log('📋 Auto-selected all subpolicies:', this.selectedSubpolicyIdsMulti)
      console.log('📋 Auto-selected all compliances:', this.selectedComplianceIds)
      
      this.saveSelectionsForAudit()
    },
    
    deselectAllRelevantDocuments() {
      this.selectedRelevantDocuments = []
      // Note: We don't auto-deselect policies/subpolicies/compliances here
      // User may want to keep them selected for other purposes
    },
    
    async uploadSelectedRelevantDocuments() {
      console.log('🔘 uploadSelectedRelevantDocuments called')
      console.log('🔘 Selected documents:', this.selectedRelevantDocuments)
      console.log('🔘 Has required mapping:', this.hasRequiredMapping)
      console.log('🔘 Selected policies:', this.selectedPolicyIdsMulti)
      console.log('🔘 Selected subpolicies:', this.selectedSubpolicyIdsMulti)
      console.log('🔘 Selected compliances:', this.selectedComplianceIds)
      
      if (this.selectedRelevantDocuments.length === 0) {
        console.log('❌ No documents selected')
        this.$popup?.warning('Please select at least one document to upload')
        return
      }
      
      // Note: Uploading without explicit policy/subpolicy selection is allowed.
      // The documents already have AI-analyzed relevance to policies/subpolicies/compliances.
      
      console.log('✅ Starting upload process...')
      this.isUploadingRelevantDocuments = true
      
      try {
        const auditId = this.currentAuditId
        if (!auditId || auditId === 'Unknown') {
          throw new Error('No audit selected. Please select an audit first.')
        }
        
        const selectedDocs = this.relevantDocuments.filter(doc => 
          this.selectedRelevantDocuments.includes(doc.file_operation_id)
        )
        
        console.log('📤 Uploading', selectedDocs.length, 'relevant documents to audit', auditId)
        console.log('📤 Selected documents:', selectedDocs.map(d => ({ id: d.file_operation_id, name: d.file_name })))
        
        // Build mapping pairs (same logic as regular upload)
        const mappingPairs = []
        
        if (this.selectedComplianceIds && this.selectedComplianceIds.length > 0) {
          const selectedSet = new Set(this.selectedComplianceIds)
          const seen = new Map()
          
          this.availableCompliances.forEach(c => {
            if (!selectedSet.has(c.compliance_id)) return
            const key = `${c.policy_id || ''}-${c.subpolicy_id || ''}`
            
            if (!seen.has(key)) {
              seen.set(key, {
                policy_id: c.policy_id || '',
                subpolicy_id: c.subpolicy_id || '',
                compliance_ids: [],
                compliance_names: []
              })
            }
            const mapping = seen.get(key)
            mapping.compliance_ids.push(c.compliance_id)
            const complianceName = c.compliance_name || c.ComplianceName || `Compliance ${c.compliance_id}`
            mapping.compliance_names.push(complianceName)
          })
          
          mappingPairs.push(...Array.from(seen.values()).map(m => ({
            policy_id: m.policy_id,
            subpolicy_id: m.subpolicy_id,
            compliance_ids: m.compliance_ids
          })))
        } else {
          const selectedPolicySet = new Set(this.selectedPolicyIdsMulti)
          const selectedSubSet = new Set(this.selectedSubpolicyIdsMulti)
          
          this.auditHierarchyPolicies.forEach(policy => {
            if (!selectedPolicySet.has(policy.policy_id)) return
            const subpolicies = policy.subpolicies || []
            const selectedSubsForPolicy = subpolicies.filter(sp =>
              selectedSubSet.size > 0 ? selectedSubSet.has(sp.subpolicy_id) : true
            )
            
            if (selectedSubsForPolicy.length === 0) {
              mappingPairs.push({
                policy_id: policy.policy_id,
                subpolicy_id: ''
              })
            } else {
              selectedSubsForPolicy.forEach(sp => {
                mappingPairs.push({
                  policy_id: policy.policy_id,
                  subpolicy_id: sp.subpolicy_id
                })
              })
            }
          })
        }
        
        console.log('📤 Mapping pairs:', mappingPairs)
        
        // Allow upload even without explicit mappings - documents already have AI-analyzed relevance
        // If no mappings selected, use empty array - the document's AI-analyzed relevance will be used
        if (mappingPairs.length === 0) {
          console.log('⚠️ No explicit mappings selected - using document\'s AI-analyzed relevance instead.')
        }
        
        // For each selected document, upload it to the audit
        // If no explicit mappings, send empty array - backend will use document's AI-analyzed relevance
        const uploadPromises = selectedDocs.map(async (doc) => {
          const formData = new FormData()
          formData.append('file_operation_id', doc.file_operation_id)
          
          // Use explicit mappings if provided, otherwise send empty array
          // Backend will use the document's existing AI-analyzed relevance from document_audit_relevance table
          formData.append('mappings', JSON.stringify(mappingPairs))
          
          console.log(`📤 Uploading document ${doc.file_operation_id} with mappings:`, mappingPairs.length > 0 ? mappingPairs : 'empty (using AI-analyzed relevance)')
          
          const response = await api.post(`/api/ai-audit/${auditId}/upload-document/`, formData, {
            // Don't set Content-Type manually - let axios/browser set it with boundary automatically
          })
          
          console.log(`✅ Document ${doc.file_operation_id} uploaded successfully:`, response.data)
          return response
        })
        
        const results = await Promise.all(uploadPromises)
        console.log('✅ All documents uploaded successfully:', results.length)
        
        this.$popup?.success(`Successfully uploaded ${selectedDocs.length} document(s) to audit`)
        
        // Clear selections and reload
        this.selectedRelevantDocuments = []
        await this.loadUploadedDocuments()
        await this.loadRelevantDocuments()
        
      } catch (error) {
        console.error('❌ Error uploading relevant documents:', error)
        console.error('❌ Error details:', {
          message: error.message,
          response: error.response?.data,
          status: error.response?.status
        })
        
        let errorMessage = 'Failed to upload documents. '
        if (error.response?.data?.error) {
          errorMessage += error.response.data.error
        } else if (error.response?.data?.message) {
          errorMessage += error.response.data.message
        } else if (error.message) {
          errorMessage += error.message
        } else {
          errorMessage += 'Please try again.'
        }
        
        this.$popup?.error(errorMessage)
      } finally {
        this.isUploadingRelevantDocuments = false
      }
    },
    
    getSelectedMapping(fileGroup) {
      if (!fileGroup || !fileGroup.mappings || fileGroup.mappings.length === 0) {
        return null
      }
      const index = fileGroup.selectedMappingIndex
      // -1 means "All" selected
      if (index === -1 || index === '-1') {
        return null // Return null to indicate "All"
      }
      const numIndex = parseInt(index) || 0
      return fileGroup.mappings[numIndex] || fileGroup.mappings[0]
    },
    
    isAllMappingsSelected(fileGroup) {
      const index = fileGroup.selectedMappingIndex
      return index === -1 || index === '-1'
    },
    
    isCheckingAnyMapping(fileGroup) {
      if (!fileGroup || !fileGroup.mappings) return false
      return fileGroup.mappings.some(m => m._checking === true)
    },
    
    // Helper: check if all mappings for a file are completed
    areAllMappingsCompleted(fileGroup) {
      if (!fileGroup || !fileGroup.mappings || fileGroup.mappings.length === 0) {
        return false
      }
      // Check both processing_status and ai_processing_status for compatibility
      return fileGroup.mappings.every(m => {
        const status = m.processing_status || m.ai_processing_status || 'pending'
        return status === 'completed'
      })
    },
    
    // Check if database evidence is part of a combined check (should not show Details button)
    isPartOfCombinedCheck(recordGroup) {
      if (!recordGroup || !recordGroup.mappings || !recordGroup.mappings.length) {
        return false
      }
      // Check if any mapping has the combined check flag
      return recordGroup.mappings.some(m => {
        if (m.compliance_analyses) {
          try {
            const analyses = typeof m.compliance_analyses === 'string' 
              ? JSON.parse(m.compliance_analyses) 
              : m.compliance_analyses
            return analyses?.part_of_combined_check === true
          } catch (e) {
            return false
          }
        }
        return false
      })
    },
    
    // Check if a fileGroup is part of a combined check (has combinedCheckGroupId)
    isPartOfCombinedCheckGroup(fileGroup) {
      return !!(fileGroup && fileGroup.combinedCheckGroupId)
    },
    
    // Get all fileGroups that share the same combined check group ID
    getCombinedCheckGroup(fileGroup) {
      if (!fileGroup || !fileGroup.combinedCheckGroupId) {
        return [fileGroup] // Return single fileGroup if not part of combined check
      }
      // Find all fileGroups with the same combinedCheckGroupId
      return this.uploadedDocuments.filter(fg => 
        fg.combinedCheckGroupId === fileGroup.combinedCheckGroupId
      )
    },
    
    // Check if this fileGroup should show the Details button
    // Show Details button as soon as at least one mapping is completed (don't wait for all)
    // Only show Details button for the FIRST fileGroup in a combined check group
    shouldShowDetailsButton(fileGroup) {
      if (!fileGroup || !fileGroup.mappings || fileGroup.mappings.length === 0) {
        console.log('🔍 shouldShowDetailsButton: No mappings', fileGroup)
        return false // No mappings, don't show
      }
      
      // Check if at least one mapping is completed (changed from "all mappings")
      // Check both processing_status and ai_processing_status fields
      const completedMappings = fileGroup.mappings.filter(m => {
        const status = m.processing_status || m.ai_processing_status || 'pending'
        const isCompleted = status === 'completed'
        if (isCompleted) {
          console.log('✅ Found completed mapping:', {
            mapping: m.mapping_display,
            status: status,
            hasAnalyses: !!m.compliance_analyses
          })
        }
        return isCompleted
      })
      
      if (completedMappings.length === 0) {
        console.log('🔍 shouldShowDetailsButton: No completed mappings yet', {
          mappings: fileGroup.mappings.map(m => ({
            display: m.mapping_display,
            status: m.processing_status || m.ai_processing_status
          }))
        })
        return false // Don't show if no mappings are completed
      }
      
      console.log('🔍 shouldShowDetailsButton: Found completed mappings, checking analyses...', {
        completedCount: completedMappings.length,
        totalCount: fileGroup.mappings.length
      })
      
      // If at least one mapping is completed, ALWAYS show the button
      // Don't wait for analyses to be loaded - if status is 'completed', show the button
      // The showAllMappingsDetails function will handle the case where analyses are missing
      // This ensures the button appears immediately when processing completes
      console.log('✅ shouldShowDetailsButton: Showing Details button for completed mappings', {
        completedCount: completedMappings.length,
        totalMappingsCount: fileGroup.mappings.length,
        completedMappings: completedMappings.map(m => ({
          display: m.mapping_display,
          status: m.processing_status || m.ai_processing_status,
          hasAnalyses: !!m.compliance_analyses
        }))
      })
      
      // If not part of a combined check, show the button
      if (!this.isPartOfCombinedCheckGroup(fileGroup)) {
        console.log('✅ shouldShowDetailsButton: Showing Details button (not part of combined check)')
        return true
      }
      
      // If part of a combined check, only show button for the first fileGroup in the group
      const combinedGroup = this.getCombinedCheckGroup(fileGroup)
      if (combinedGroup.length <= 1) {
        console.log('✅ shouldShowDetailsButton: Showing Details button (only one in group)')
        return true // Only one fileGroup in group, show button
      }
      
      // Find the index of this fileGroup in the combined group
      // Use document_id or document_name to determine "first" (lowest document_id or alphabetically first name)
      const sortedGroup = [...combinedGroup].sort((a, b) => {
        // Sort by document_id if available, otherwise by document_name
        if (a.document_id && b.document_id) {
          return a.document_id - b.document_id
        }
        if (a.document_name && b.document_name) {
          return a.document_name.localeCompare(b.document_name)
        }
        return 0
      })
      
      // Show button only for the first (lowest document_id) fileGroup
      const shouldShow = sortedGroup[0] === fileGroup || sortedGroup[0].document_id === fileGroup.document_id
      console.log('🔍 shouldShowDetailsButton: Combined check group', {
        shouldShow,
        isFirst: sortedGroup[0] === fileGroup,
        groupSize: combinedGroup.length
      })
      return shouldShow
    },
    
    // Helper: get tooltip text showing all mappings
    getMappingsTooltip(fileGroup) {
      if (!fileGroup || !fileGroup.mappings || fileGroup.mappings.length === 0) {
        return 'No mappings available'
      }
      const mappingTexts = fileGroup.mappings.map((m, idx) => {
        return `${idx + 1}. ${m.mapping_display || 'Unknown mapping'}`
      })
      return `Mappings:\n${mappingTexts.join('\n')}`
    },
    
    // Get aggregated compliance status for all mappings
    getAggregatedComplianceStatus(fileGroup) {
      if (!fileGroup || !fileGroup.mappings) return null
      return this.aggregateComplianceStatus(fileGroup.mappings)
    },
    
    // Get aggregated confidence score for all mappings
    getAggregatedConfidenceScore(fileGroup) {
      if (!fileGroup || !fileGroup.mappings) return 0
      return this.aggregateConfidenceScore(fileGroup.mappings)
    },
    
    // Aggregate overall compliance status across multiple mappings
    aggregateComplianceStatus(mappings) {
      const completed = (mappings || []).filter(m => m.processing_status === 'completed')
      if (completed.length === 0) return null
      const statuses = completed.map(m => m.compliance_status || 'unknown')
      if (statuses.some(s => s === 'non_compliant')) return 'non_compliant'
      if (statuses.some(s => s === 'partially_compliant')) return 'partially_compliant'
      if (statuses.every(s => s === 'compliant')) return 'compliant'
      return 'partially_compliant'
    },
    
    // Average confidence score across multiple mappings
    aggregateConfidenceScore(mappings) {
      const completed = (mappings || []).filter(
        m => m.processing_status === 'completed' && m.confidence_score != null
      )
      if (completed.length === 0) return 0
      const sum = completed.reduce((acc, m) => acc + (Number(m.confidence_score) || 0), 0)
      return sum / completed.length
    },
    
    async startAIProcessing() {
      try {
        console.log('🚀 startAIProcessing called!')
        console.log('🚀 uploadedDocuments.length:', this.uploadedDocuments.length)
        console.log('🚀 uploadedDocuments:', this.uploadedDocuments)
        
        const auditId = this.currentAuditId
        if (!auditId || auditId === 'Unknown') {
          console.warn('No valid audit ID, cannot start AI processing')
          this.$popup?.error('No valid audit ID. Please refresh the page.')
          return
        }
        
        if (this.uploadedDocuments.length === 0) {
          console.warn('No uploaded documents to process')
          this.$popup?.error('Please upload documents before starting AI processing.')
          return
        }
        
        // Check authentication status
        const token = localStorage.getItem('access_token')
        if (!token) {
          console.warn('No JWT token found, cannot start AI processing')
          this.$popup?.error('Authentication required. Please log in again.')
          return
        }
        
        // Set loading state
        this.isProcessingAI = true
        
        console.log('🚀 Starting AI processing request...')
        console.log('🚀 Audit ID:', auditId)
        console.log('🚀 Token available:', !!token)
        
        const response = await api.post(`/api/ai-audit/${auditId}/start-processing/`, {
          processing_options: {
            enable_compliance_mapping: true,
            enable_risk_assessment: true,
            enable_recommendations: true
          }
        }, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        })
        
        console.log('🚀 AI processing response:', response.data)
        
        if (response.data && response.data.success) {
          this.$popup?.success('AI processing started successfully')
          
          // Wait a moment then refresh status manually
          setTimeout(() => {
            console.log('🔄 Manually refreshing status after AI processing start')
            this.loadAIStatus()
          }, 2000)
          
          this.startStatusPolling()
        } else {
          const errorMessage = response.data?.error || response.data?.message || 'Unknown error occurred'
          console.error('🚀 AI processing failed:', errorMessage)
          this.$popup?.error(`AI processing failed: ${errorMessage}`)
        }
      } catch (error) {
        console.error('Error starting AI processing:', error)
        
        // Provide more specific error messages
        let errorMessage = 'Error starting AI processing. Please try again.'
        
        if (error.response) {
          // Server responded with error status
          const status = error.response.status
          const data = error.response.data
          
          console.error('🚀 Server error response:', { status, data })
          
          if (status === 401) {
            errorMessage = 'Authentication failed. Please log in again.'
          } else if (status === 403) {
            errorMessage = 'You do not have permission to start AI processing.'
          } else if (status === 404) {
            errorMessage = 'Audit not found. Please refresh the page.'
          } else if (status === 400) {
            errorMessage = data?.error || data?.message || 'Invalid request. Please check your data.'
          } else if (status >= 500) {
            errorMessage = 'Server error. Please try again later.'
          } else {
            errorMessage = data?.error || data?.message || `Server error (${status}). Please try again.`
          }
        } else if (error.request) {
          // Network error
          console.error('🚀 Network error:', error.request)
          errorMessage = 'Network error. Please check your connection and try again.'
        } else {
          // Other error
          console.error('🚀 Other error:', error.message)
          errorMessage = error.message || 'An unexpected error occurred.'
        }
        
        this.$popup?.error(errorMessage)
      } finally {
        // Always reset loading state
        this.isProcessingAI = false
      }
    },
    
    async loadAIStatus() {
      try {
        const auditId = this.currentAuditId
        if (!auditId || auditId === 'Unknown') {
          console.warn('No valid audit ID, skipping AI status load')
          return
        }
        console.log('📊 Loading AI status for audit:', auditId)
        const response = await api.get(`/api/ai-audit/${auditId}/status/`)
        console.log('📊 AI status response:', response.data)
        if (response.data.success) {
          this.processingStatus = response.data.processing_status
          this.complianceResults = response.data.compliance_results || []
          console.log('📊 Updated processing status:', this.processingStatus)
        }
        
        // Load AI processing results from completed documents
        await this.loadAIProcessingResults()
      } catch (error) {
        console.error('Error loading AI status:', error)
      }
    },
    
    async loadAIProcessingResults() {
      try {
        const auditId = this.currentAuditId
        if (!auditId || auditId === 'Unknown') {
          return
        }
        
        console.log('🤖 Loading AI processing results for audit:', auditId)
        const response = await api.get(`/api/ai-audit/${auditId}/documents/`)
        
        if (response.data.success) {
          // Filter documents that have been processed by AI
          const processedDocs = response.data.documents.filter(doc => 
            doc.processing_status === 'completed' && doc.processing_results
          )
          
          this.aiProcessingResults = processedDocs.map(doc => {
            try {
              const processingResults = JSON.parse(doc.processing_results || '{}')
              const complianceMapping = JSON.parse(doc.compliance_mapping || '{}')
              
              return {
                document_id: doc.document_id,
                document_name: doc.file_name,
                compliance_status: doc.compliance_status || 'unknown',
                risk_level: doc.risk_level || 'medium',
                confidence_score: parseFloat(doc.confidence_score) || 0.0,
                ai_recommendations: doc.ai_recommendations || '',
                extracted_text: doc.extracted_text || '',
                processing_results: processingResults,
                compliance_mapping: complianceMapping
              }
            } catch (e) {
              console.error('Error parsing AI results for document:', doc.document_id, e)
              return null
            }
          }).filter(result => result !== null)
          
          console.log('🤖 Loaded AI processing results:', this.aiProcessingResults.length)
        }
      } catch (error) {
        console.error('Error loading AI processing results:', error)
      }
    },
    
    startStatusPolling() {
      // Clear any existing polling interval
      if (this.pollingInterval) {
        clearInterval(this.pollingInterval)
      }
      
      // Track if we've seen any processing documents to continue polling for a bit after completion
      let hasSeenProcessingDocs = false
      let consecutiveCompletedCount = 0
      const MAX_CONSECUTIVE_COMPLETED = 3 // Stop after 3 consecutive checks showing all completed
      
      // Poll for document status updates every 5 seconds
      // This ensures Details button appears as soon as documents are completed
      this.pollingInterval = setInterval(() => {
        // If no documents at all, stop polling immediately
        if (!this.uploadedDocuments || this.uploadedDocuments.length === 0) {
          console.log('✅ No documents found, stopping status polling')
          if (this.pollingInterval) {
            clearInterval(this.pollingInterval)
            this.pollingInterval = null
          }
          return
        }
        
        // Check if we have documents that might be processing
        const hasProcessingDocs = this.uploadedDocuments.some(fg => 
          fg.mappings && fg.mappings.some(m => {
            const status = m.processing_status || m.ai_processing_status || 'pending'
            return status === 'processing' || status === 'pending'
          })
        )
        
        // Check if all documents are completed
        const allCompleted = this.uploadedDocuments.every(fg => 
          this.areAllMappingsCompleted(fg)
        )
        
        if (hasProcessingDocs) {
          // Still have processing documents, continue polling
          hasSeenProcessingDocs = true
          consecutiveCompletedCount = 0
          console.log('🔄 Polling for document status updates (processing documents found)...')
          this.loadUploadedDocuments().catch(err => {
            console.warn('⚠️ Error during status polling:', err)
          })
        } else if (allCompleted) {
          // All documents are completed
          consecutiveCompletedCount++
          console.log(`✅ All documents completed (check ${consecutiveCompletedCount}/${MAX_CONSECUTIVE_COMPLETED})...`)
          
          if (consecutiveCompletedCount >= MAX_CONSECUTIVE_COMPLETED) {
            // Stop polling after confirming all are completed for 3 cycles
            console.log('✅ All documents confirmed completed, stopping status polling')
            if (this.pollingInterval) {
              clearInterval(this.pollingInterval)
              this.pollingInterval = null
            }
          } else {
            // Do one final refresh to ensure UI is up to date
            this.loadUploadedDocuments().catch(err => {
              console.warn('⚠️ Error during final status polling:', err)
            })
          }
        } else if (hasSeenProcessingDocs) {
          // Had processing docs before, but now none are processing and not all are completed
          // This shouldn't happen normally, but continue polling just in case
          console.log('🔄 Polling for document status updates (transition state)...')
          this.loadUploadedDocuments().catch(err => {
            console.warn('⚠️ Error during status polling:', err)
          })
        } else {
          // No processing docs and never had any - stop immediately
          console.log('✅ No processing documents found, stopping status polling')
          if (this.pollingInterval) {
            clearInterval(this.pollingInterval)
            this.pollingInterval = null
          }
        }
      }, 5000) // Poll every 5 seconds
      
      console.log('✅ Status polling enabled (5 second interval)')
    },
    
    
    // eslint-disable-next-line no-unused-vars
    // viewDocument(doc) {
    //   // TODO: Implement document viewer
    //   this.$popup?.info('Document viewer coming soon!')
    // },
    
    // eslint-disable-next-line no-unused-vars
    async deleteDocument(documentId) {
      if (confirm('Are you sure you want to delete this document?')) {
        try {
          console.log('🗑️ Deleting document:', documentId)
          
          const auditId = this.currentAuditId
          if (!auditId || auditId === 'Unknown') {
            this.$popup?.error('No valid audit ID. Please refresh the page.')
            return
          }
          
          const response = await api.delete(`/api/ai-audit/${auditId}/documents/${documentId}/`, {
            timeout: 60000 // 60 seconds timeout for delete operations (may need to delete multiple records)
          })
          
          if (response.data.success) {
            console.log('✅ Document deleted successfully')
            this.$popup?.success('Document deleted successfully!')
            
            // Reload the documents list
            await this.loadUploadedDocuments()
          } else {
            console.error('❌ Delete failed:', response.data.error)
            this.$popup?.error(`Delete failed: ${response.data.error}`)
          }
        } catch (error) {
          console.error('❌ Error deleting document:', error)
          
          // Handle timeout specifically
          if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
            this.$popup?.error('Delete operation timed out. The document may still be deleted. Please refresh the page.')
            // Try to reload anyway in case the delete succeeded
            setTimeout(() => {
              this.loadUploadedDocuments()
            }, 1000)
          } else if (error.response?.status === 404) {
            this.$popup?.error('Document not found or already deleted.')
            // Reload to refresh the list
            await this.loadUploadedDocuments()
          } else if (error.response?.status === 401) {
            this.$popup?.error('Authentication required. Please log in again.')
          } else {
            this.$popup?.error(`Delete failed: ${error.response?.data?.error || error.message}`)
          }
        }
      }
    },

    async deleteAllDatabaseEvidence() {
      if (!confirm('Are you sure you want to delete all additional evidence for this audit?')) {
        return
      }

      try {
        this.bulkDeletingDatabase = true

        const auditId = this.currentAuditId
        if (!auditId || auditId === 'Unknown') {
          this.$popup?.error('No valid audit ID. Please refresh the page.')
          this.bulkDeletingDatabase = false
          return
        }

        console.log('🗑️ Bulk deleting all additional evidence for audit:', auditId)
        const response = await api.delete(`/api/ai-audit/${auditId}/documents/delete-all/`, {
          params: { type: 'database' }
        })

        if (response.data.success) {
          console.log('✅ Bulk delete successful', response.data)
          this.$popup?.success('All additional evidence deleted for this audit.')
          await this.loadUploadedDocuments()
        } else {
          console.error('❌ Bulk delete failed:', response.data.error)
          this.$popup?.error(`Delete failed: ${response.data.error}`)
        }
      } catch (error) {
        console.error('❌ Error bulk deleting additional evidence:', error)
        this.$popup?.error(`Delete failed: ${error.response?.data?.error || error.message}`)
      } finally {
        this.bulkDeletingDatabase = false
      }
    },

    async deleteAllDocuments() {
      if (!confirm('Are you sure you want to delete ALL documents for this audit? This action cannot be undone.')) {
        return
      }

      try {
        this.bulkDeleting = true

        const auditId = this.currentAuditId
        if (!auditId || auditId === 'Unknown') {
          this.$popup?.error('No valid audit ID. Please refresh the page.')
          this.bulkDeleting = false
          return
        }

        console.log('🗑️ Bulk deleting all documents for audit:', auditId)
        
        // Delete all document records (not database records) for this audit
        // Get all document IDs first
        const documentIds = []
        this.fileDocuments.forEach(fileGroup => {
          if (fileGroup.mappings && fileGroup.mappings.length > 0) {
            fileGroup.mappings.forEach(mapping => {
              if (mapping.document_id && !documentIds.includes(mapping.document_id)) {
                documentIds.push(mapping.document_id)
              }
            })
          }
        })

        if (documentIds.length === 0) {
          this.$popup?.info('No documents to delete.')
          this.bulkDeleting = false
          return
        }

        // Delete each document
        let deletedCount = 0
        let failedCount = 0
        for (const docId of documentIds) {
          try {
            const response = await api.delete(`/api/ai-audit/${auditId}/documents/${docId}/`)
            if (response.data.success) {
              deletedCount++
            } else {
              failedCount++
            }
          } catch (error) {
            console.error(`❌ Error deleting document ${docId}:`, error)
            failedCount++
          }
        }

        if (deletedCount > 0) {
          this.$popup?.success(`Successfully deleted ${deletedCount} document(s).${failedCount > 0 ? ` ${failedCount} failed.` : ''}`)
          await this.loadRelevantDocuments()  // Reload documents list
        } else {
          this.$popup?.error(`Failed to delete documents. ${failedCount} error(s).`)
        }
      } catch (error) {
        console.error('❌ Error bulk deleting documents:', error)
        this.$popup?.error(`Delete failed: ${error.response?.data?.error || error.message}`)
      } finally {
        this.bulkDeleting = false
      }
    },
    
    // eslint-disable-next-line no-unused-vars
    reviewFinding(result) {
      // TODO: Implement finding review modal
      this.$popup?.info('Finding review coming soon!')
    },
    
    getPolicyName(policyId) {
      const policy = this.policies.find(p => p.PolicyId === policyId)
      return policy ? policy.PolicyName : 'Unknown Policy'
    },
    
    getSubPolicyName(subPolicyId) {
      const subpolicy = this.subpolicies.find(sp => sp.SubPolicyId === subPolicyId)
      return subpolicy ? subpolicy.SubPolicyName : 'Unknown Sub-policy'
    },
    
    goToReviews() {
      this.$router.push('/auditor/reviews')
    },
    
    reviewAIResult(result) {
      // Show detailed AI analysis in a modal or new page
      console.log('Reviewing AI result:', result)
      this.$popup?.info(`Reviewing AI analysis for: ${result.document_name}`)
    },
    
    async downloadAIReport(result) {
      // Generate and download comprehensive AI analysis report
      console.log('📊 Downloading comprehensive AI report for:', result)
      
      try {
        const auditId = this.currentAuditId
        console.log('📊 Generating comprehensive report for audit:', auditId)
        
        // Call the new comprehensive report endpoint
        const response = await api.get(`/api/ai-audit/${auditId}/download-report/`, {
          responseType: 'blob',
          timeout: 30000 // 30 second timeout
        })
        
        // Create blob from response
        const blob = new Blob([response.data], {
          type: 'application/json'
        })
        
        // Create download link
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = `AI_Audit_Comprehensive_Report_${auditId}_${new Date().toISOString().slice(0,10)}.json`
        link.target = '_blank'
        
        // Trigger download
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        
        // Clean up
        window.URL.revokeObjectURL(url)
        
        console.log(`📊 Comprehensive AI audit report downloaded successfully for audit ${auditId}`)
        
        // Show success message
        this.$popup?.success(`Comprehensive AI audit report for Audit ID ${auditId} downloaded successfully!`)
        
        // Send push notification about successful download
        if (window.sendPushNotification) {
          window.sendPushNotification({
            title: 'AI Audit Report Downloaded',
            message: `Comprehensive AI audit report for Audit ID ${auditId} has been downloaded successfully.`,
            category: 'audit',
            priority: 'medium',
            user_id: 'default_user'
          })
        }
        
      } catch (error) {
        console.error('❌ Error downloading comprehensive AI report:', error)
        
        // Fallback to simple JSON report if comprehensive report fails
        console.log('📊 Falling back to simple report generation')
        
        const reportData = {
          document_name: result.document_name || 'Unknown Document',
          compliance_status: result.compliance_status || 'unknown',
          risk_level: result.risk_level || 'medium',
          confidence_score: result.confidence_score || 0,
          ai_recommendations: result.ai_recommendations || 'No recommendations available',
          analysis_timestamp: result.compliance_mapping?.analysis_timestamp || new Date().toISOString(),
          found_keywords: result.compliance_mapping?.found_keywords || [],
          extracted_text_preview: result.extracted_text || 'No text extracted',
          audit_id: this.currentAuditId,
          processing_details: {
            ai_model_used: 'llama3.2:3b',
            processing_method: 'Ollama AI/ML Analysis',
            compliance_checking: 'Structured Compliance Analysis'
          }
        }
        
        const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' })
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `AI_Analysis_Report_${(result.document_name || 'Unknown_Document').replace(/\.[^/.]+$/, '')}.json`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        window.URL.revokeObjectURL(url)
        
        this.$popup?.success('AI analysis report downloaded successfully! (Fallback mode)')
      }
    }
    ,
    async checkDocumentCompliance(doc, fileGroup) {
      try {
        const auditId = this.currentAuditId
        
        if (!fileGroup || !fileGroup.mappings || fileGroup.mappings.length === 0) {
          this.$popup?.error(`No mappings found for "${fileGroup?.document_name || 'document'}". Please ensure the document has been uploaded and mapped to policies/sub-policies.`)
          return
        }
        
        // If "All" is selected (doc is null), check all mappings
        if (!doc || this.isAllMappingsSelected(fileGroup)) {
          console.log('🧪 Checking compliance for ALL mappings of file:', fileGroup.document_name)
          
          // Mark all mappings as checking
          fileGroup.mappings.forEach(m => { m._checking = true })
          
          // Collect ALL compliance IDs from ALL mappings
          const allComplianceIds = new Set()
          const mappingComplianceMap = new Map() // Map compliance_id -> mapping for later assignment
          let primaryDocumentId = null
          
          console.log(`🔍 Collecting compliance IDs from ${fileGroup.mappings.length} mapping(s)`)
          
          for (const mapping of fileGroup.mappings) {
            console.log(`🔍 Mapping: ${mapping.mapping_display}`, {
              has_compliance_ids: !!mapping.compliance_ids,
              compliance_ids: mapping.compliance_ids,
              compliance_id_from_db: mapping.compliance_id, // Direct from database
              document_id: mapping.document_id
            })
            
            // First, check if mapping has direct compliance_id from database (manually uploaded)
            if (mapping.compliance_id && !allComplianceIds.has(mapping.compliance_id)) {
              allComplianceIds.add(mapping.compliance_id)
              if (!mappingComplianceMap.has(mapping.compliance_id)) {
                mappingComplianceMap.set(mapping.compliance_id, [])
              }
              mappingComplianceMap.get(mapping.compliance_id).push(mapping)
              console.log(`✅ Added compliance_id ${mapping.compliance_id} from database record`)
            }
            
            // Also check compliance_ids array (for multiple compliances or Document Handling uploads)
            if (mapping.compliance_ids && Array.isArray(mapping.compliance_ids)) {
              mapping.compliance_ids.forEach(compId => {
                if (!allComplianceIds.has(compId)) {
                  allComplianceIds.add(compId)
                  if (!mappingComplianceMap.has(compId)) {
                    mappingComplianceMap.set(compId, [])
                  }
                  mappingComplianceMap.get(compId).push(mapping)
                  console.log(`✅ Added compliance_id ${compId} from compliance_ids array`)
                }
              })
            }
            
            // Use the first mapping's document_id as the primary one
            if (!primaryDocumentId && mapping.document_id) {
              primaryDocumentId = mapping.document_id
            }
          }
          
          console.log(`🧪 Found ${allComplianceIds.size} unique compliance IDs across ${fileGroup.mappings.length} mapping(s):`, Array.from(allComplianceIds))
          
          if (allComplianceIds.size === 0) {
            this.$popup?.error(`No compliance IDs found in any mapping for "${fileGroup.document_name}". Please ensure mappings have compliance requirements.`)
            fileGroup.mappings.forEach(m => { m._checking = false })
            return
          }
          
          // Use the first mapping's document_id (they should all be the same for the same file)
          const documentIdToUse = primaryDocumentId || fileGroup.mappings[0]?.document_id
          if (!documentIdToUse) {
            this.$popup?.error(`No document ID found for "${fileGroup.document_name}".`)
            fileGroup.mappings.forEach(m => { m._checking = false })
            return
          }
          
          try {
            // Make ONE API call with ALL compliance IDs
            const payload = {
              selected_compliance_ids: Array.from(allComplianceIds)
            }
            console.log(`🧪 Checking ALL mappings with ${allComplianceIds.size} compliance IDs:`, payload.selected_compliance_ids)
            
            const res = await api.post(
              `/api/ai-audit/${auditId}/documents/${documentIdToUse}/check/`,
              payload,
              { timeout: 600000 } // 10 minutes timeout for compliance checks (can take longer for multiple compliances)
            )
            console.log('🧪 Check response for all mappings:', res.status, res.data)
            
            if (res.data && res.data.success) {
              // Update all mappings with the results
              const analyses = res.data.analyses || []
              
              // Group analyses by compliance_id and update corresponding mappings
              for (const mapping of fileGroup.mappings) {
                mapping.processing_status = 'completed'
                mapping.compliance_status = res.data.status || mapping.compliance_status
                mapping.confidence_score = res.data.confidence ?? mapping.confidence_score
                
                // Filter analyses for this mapping's compliance IDs
                const mappingAnalyses = analyses.filter(a => 
                  mapping.compliance_ids && mapping.compliance_ids.includes(a.compliance_id)
                )
                if (mappingAnalyses.length > 0) {
                  mapping.compliance_analyses = mappingAnalyses
                } else {
                  mapping.compliance_analyses = analyses // Fallback: use all analyses
                }
              }
              
              // Clear checking flags
              fileGroup.mappings.forEach(m => { m._checking = false })
              
              // Force Vue reactivity update immediately
              this.$forceUpdate()
              
              this.$popup?.success(`Compliance checked successfully for "${fileGroup.document_name}" - ${allComplianceIds.size} compliance requirement(s) analyzed across ${fileGroup.mappings.length} mapping(s)`)
              
              // Reload documents to get updated status from backend (with delay to ensure backend has updated)
              // Use multiple reload attempts to ensure status is correctly reflected
              const reloadWithRetry = async (attempt = 1, maxAttempts = 3) => {
                try {
                  await this.loadUploadedDocuments()
                  // After reload, verify that mappings are marked as completed
                  const reloadedFileGroup = this.uploadedDocuments.find(fg => 
                    fg.document_name === fileGroup.document_name && 
                    fg.file_size === fileGroup.file_size
                  )
                  if (reloadedFileGroup) {
                    console.log(`🔍 After reload (attempt ${attempt}) - mappings status:`, reloadedFileGroup.mappings.map(m => ({
                      mapping: m.mapping_display,
                      status: m.processing_status,
                      has_analyses: !!m.compliance_analyses
                    })))
                    const allCompleted = reloadedFileGroup.mappings.every(m => m.processing_status === 'completed')
                    console.log(`🔍 All mappings completed? ${allCompleted}`)
                    
                    // If not all completed and we have retries left, try again
                    if (!allCompleted && attempt < maxAttempts) {
                      console.log(`⚠️ Not all mappings completed, retrying reload in ${attempt * 500}ms...`)
                      setTimeout(() => reloadWithRetry(attempt + 1, maxAttempts), attempt * 500)
                    } else if (!allCompleted) {
                      console.warn('⚠️ Some mappings are not marked as completed after all reload attempts. This may prevent Details button from showing.')
                      // Force update status locally as fallback
                      reloadedFileGroup.mappings.forEach(m => {
                        if (m.processing_status !== 'completed') {
                          m.processing_status = 'completed'
                        }
                      })
                      this.$forceUpdate()
                    }
                  }
                } catch (err) {
                  console.error('Error reloading documents:', err)
                  // Don't retry on timeout errors - they indicate a bigger problem
                  if (err.code === 'ECONNABORTED' || err.message?.includes('timeout')) {
                    console.error('⏱️ Timeout error during reload - stopping retries')
                    return
                  }
                  if (attempt < maxAttempts) {
                    setTimeout(() => reloadWithRetry(attempt + 1, maxAttempts), attempt * 500)
                  }
                }
              }
              
              // Start reload after a short delay
              setTimeout(() => reloadWithRetry(), 1500) // Start with 1.5 second delay
            } else {
              const errorMsg = res.data?.error || 'Unknown error'
              this.$popup?.error(`Failed to check compliance for "${fileGroup.document_name}". ${errorMsg}`)
            }
          } catch (err) {
            const errorMsg = err.response?.data?.error || err.message || 'Network error'
            console.error('🧪 Error checking all mappings:', err)
            this.$popup?.error(`Failed to check compliance for "${fileGroup.document_name}". ${errorMsg}`)
          } finally {
            fileGroup.mappings.forEach(m => { m._checking = false })
          }
          return
        }
        
        // Single mapping selected - check only this mapping with its compliances
        doc._checking = true
        console.log('🧪 Checking compliance for mapping:', doc.mapping_display)

        const payload = {}
        // Only send compliances for THIS specific mapping
        if (doc.compliance_ids && doc.compliance_ids.length > 0) {
          payload.selected_compliance_ids = doc.compliance_ids
          console.log(`🧪 Selected compliance IDs for this mapping: ${doc.compliance_ids.length} compliance(s)`, doc.compliance_ids)
        }

        // Check this single document record (allow long-running AI job)
        const res = await api.post(
          `/api/ai-audit/${auditId}/documents/${doc.document_id}/check/`,
          payload,
          { timeout: 600000 } // 10 minutes
        )
        console.log('🧪 Check response:', res.status, res.data)
        
        // Check if this is a background job (202 Accepted with job_id)
        if (res.status === 202 && res.data?.job_id) {
          const jobId = res.data.job_id
          console.log(`🚀 Background job started: ${jobId}. Polling for status...`)
          
          // Show initial progress message
          this.$popup?.info(`Processing ${res.data.total_requirements || 'multiple'} requirements in background. Progress will be shown...`)
          
          // Start polling for job status
          this.pollJobStatus(jobId, doc, fileGroup)
          return
        }
        
        if (res.data && res.data.success) {
          doc.processing_status = 'completed'
          doc.compliance_status = res.data.status || doc.compliance_status
          doc.confidence_score = res.data.confidence ?? doc.confidence_score
          doc.compliance_analyses = res.data.analyses || doc.compliance_analyses
          
          // Force Vue reactivity update immediately
          this.$forceUpdate()
          
          this.$popup?.success(`Compliance checked for "${fileGroup.document_name}" - ${doc.mapping_display}`)
          
          // Reload documents to get updated status from backend (with retry logic)
          const reloadWithRetry = async (attempt = 1, maxAttempts = 3) => {
            try {
              await this.loadUploadedDocuments()
              // Verify the mapping is marked as completed
              const reloadedFileGroup = this.uploadedDocuments.find(fg => 
                fg.document_name === fileGroup.document_name && 
                fg.file_size === fileGroup.file_size
              )
              if (reloadedFileGroup) {
                const reloadedMapping = reloadedFileGroup.mappings.find(m => 
                  m.policy_id === doc.policy_id && m.subpolicy_id === doc.subpolicy_id
                )
                if (reloadedMapping && reloadedMapping.processing_status !== 'completed' && attempt < maxAttempts) {
                  console.log(`⚠️ Mapping not completed after reload, retrying in ${attempt * 500}ms...`)
                  setTimeout(() => reloadWithRetry(attempt + 1, maxAttempts), attempt * 500)
                } else if (reloadedMapping && reloadedMapping.processing_status !== 'completed') {
                  // Force update as fallback
                  reloadedMapping.processing_status = 'completed'
                  this.$forceUpdate()
                }
              }
            } catch (err) {
              console.error('Error reloading documents:', err)
              if (attempt < maxAttempts) {
                setTimeout(() => reloadWithRetry(attempt + 1, maxAttempts), attempt * 500)
              }
            }
          }
          
          setTimeout(() => reloadWithRetry(), 1500)
        } else {
          const msg = res.data?.error || 'Compliance check failed'
          console.warn('🧪 Check failed:', msg)
          this.$popup?.error(msg)
        }
      } catch (e) {
        const status = e?.response?.status
        const data = e?.response?.data
        console.error('🧪 Compliance check error:', { status, data, message: e?.message })
        this.$popup?.error(data?.error || e?.message || 'Compliance check error')
      } finally {
        // Clear checking flags
        if (doc) {
          doc._checking = false
        } else if (fileGroup && fileGroup.mappings) {
          fileGroup.mappings.forEach(m => { m._checking = false })
        }
      }
    },
    async pollJobStatus(jobId, doc, fileGroup, pollInterval = 3000, maxPolls = 600) {
      /**
       * Poll for background job status
       * @param {string} jobId - Job ID to poll
       * @param {object} doc - Document/mapping object to update
       * @param {object} fileGroup - File group object
       * @param {number} pollInterval - Polling interval in ms (default: 3 seconds)
       * @param {number} maxPolls - Maximum number of polls (default: 600 = 30 minutes)
       */
      let pollCount = 0
      const poll = async () => {
        try {
          pollCount++
          if (pollCount > maxPolls) {
            console.warn(`⏱️ Max polls reached for job ${jobId}. Stopping polling.`)
            this.$popup?.warning(`Job ${jobId} is taking longer than expected. Please check status manually.`)
            return
          }
          
          const res = await api.get(`/api/ai-audit/compliance-job/${jobId}/status/`)
          const job = res.data
          
          console.log(`📊 Job ${jobId} status: ${job.status}, progress: ${job.progress_percent}% (${job.processed_requirements}/${job.total_requirements})`)
          
          // Update UI with progress
          if (doc) {
            doc._job_progress = job.progress_percent
            doc._job_status = job.status
            this.$forceUpdate()
          }
          
          if (job.status === 'completed') {
            console.log(`✅ Job ${jobId} completed!`)
            // Update document status
            if (doc) {
              doc.processing_status = 'completed'
              doc.compliance_status = job.results?.status || doc.compliance_status
              doc.confidence_score = job.results?.confidence ?? doc.confidence_score
              doc.compliance_analyses = job.results?.analyses || doc.compliance_analyses
              doc._job_progress = 100
              this.$forceUpdate()
            }
            
            this.$popup?.success(`Compliance check completed for "${fileGroup.document_name}" - ${job.completed_requirements} requirements analyzed`)
            
            // Reload documents to get final status
            setTimeout(async () => {
              try {
                await this.loadUploadedDocuments()
              } catch (err) {
                console.error('Error reloading documents after job completion:', err)
              }
            }, 1000)
            
            return // Stop polling
          } else if (job.status === 'failed') {
            console.error(`❌ Job ${jobId} failed: ${job.error}`)
            if (doc) {
              doc.processing_status = 'failed'
              doc._job_error = job.error
              this.$forceUpdate()
            }
            this.$popup?.error(`Compliance check failed: ${job.error}`)
            return // Stop polling
          } else {
            // Still processing - poll again
            setTimeout(poll, pollInterval)
          }
        } catch (err) {
          console.error(`❌ Error polling job ${jobId} status:`, err)
          // Continue polling even on error (might be temporary network issue)
          if (pollCount < maxPolls) {
            setTimeout(poll, pollInterval)
          } else {
            this.$popup?.error(`Failed to get job status after ${maxPolls} attempts. Please refresh the page.`)
          }
        }
      }
      
      // Start polling
      poll()
    },
    async checkAllDocumentsCompliance() {
      try {
        const auditId = this.currentAuditId
        if (!auditId || auditId === 'Unknown') {
          this.$popup?.error('No valid audit ID. Please refresh the page.')
          return
        }
        if (this.uploadedDocuments.length === 0) {
          this.$popup?.error('No uploaded documents to check.')
          return
        }

        this.bulkChecking = true
        console.log('🧪 Checking compliance for ALL mappings in ALL files:', auditId)

        let successCount = 0
        let totalMappings = 0

        // Run checks sequentially for each file and each mapping
        for (const fileGroup of this.uploadedDocuments) {
          for (const mapping of fileGroup.mappings) {
            try {
              // Skip mappings that are already completed and have analyses
              if (
                mapping.processing_status === 'completed' &&
                (mapping.compliance_analyses && mapping.compliance_analyses.length)
              ) {
                console.log(
                  '🧪 Skipping already completed mapping:',
                  mapping.mapping_display
                )
                continue
              }

              totalMappings += 1
              
              // Build payload with ONLY compliances for THIS specific mapping
              const payload = {}
              if (mapping.compliance_ids && mapping.compliance_ids.length > 0) {
                payload.selected_compliance_ids = mapping.compliance_ids
                console.log(`🧪 Checking mapping "${mapping.mapping_display}" with ${mapping.compliance_ids.length} compliance(s)`)
              }
              
              const res = await api.post(
                `/api/ai-audit/${auditId}/documents/${mapping.document_id}/check/`,
                payload,
                { timeout: 600000 } // 10 minutes per mapping
              )
              console.log('🧪 Bulk check response:', mapping.document_id, res.status, res.data)

              if (res.data && res.data.success) {
                successCount += 1
                // Update the mapping object with the result
                mapping.processing_status = 'completed'
                mapping.compliance_status = res.data.status || mapping.compliance_status
                mapping.confidence_score = res.data.confidence ?? mapping.confidence_score
                mapping.compliance_analyses = res.data.analyses || mapping.compliance_analyses
              } else {
                mapping.processing_status = mapping.processing_status || 'pending'
              }
            } catch (err) {
              const status = err?.response?.status
              const data = err?.response?.data
              console.error('🧪 Bulk compliance check error:', {
                document_id: mapping.document_id,
                status,
                data,
                message: err?.message
              })
              // Continue with other mappings even if one fails
              mapping.processing_status = mapping.processing_status || 'pending'
            }
          }
        }

        this.$popup?.success(`Compliance checked for ${successCount}/${totalMappings} mapping(s).`)
        
        // Reload documents to get the latest status from backend
        await this.loadUploadedDocuments()
      } finally {
        this.bulkChecking = false
      }
    }
  }
}
</script>

<style scoped>
.multi-mapping-container {
  margin-top: 24px;
  padding: 20px 24px;
  border-radius: 12px;
  border: 1px solid #e0e0e0;
  background: #f9fafb;
}

.multi-mapping-title {
  margin: 0 0 4px 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2933;
}

.multi-mapping-help {
  margin: 0 0 16px 0;
  font-size: 13px;
  color: #6b7280;
}

.multi-mapping-columns {
  display: grid;
  grid-template-columns: 1.1fr 1.2fr 1.2fr;
  gap: 16px;
}

.multi-column {
  background: #ffffff;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  padding: 12px 14px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
  max-height: 220px;
  display: flex;
  flex-direction: column;
}

.multi-column-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #111827;
}

.multi-column-header span {
  white-space: nowrap;
}

.select-all-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 500;
  color: #2563eb;
  cursor: pointer;
}

.select-all-label input {
  margin: 0;
}

.multi-column-list {
  flex: 1;
  overflow-y: auto;
  padding-right: 4px;
}

.multi-checkbox-row {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  font-size: 12px;
  color: #374151;
  padding: 4px 2px;
  border-radius: 4px;
  cursor: pointer;
}

.multi-checkbox-row:hover {
  background: #f3f4f6;
}

.multi-checkbox-row input {
  margin-top: 2px;
}

.multi-checkbox-label {
  line-height: 1.35;
}

.multi-subpolicy-policy {
  display: inline-block;
  margin-left: 4px;
  font-size: 11px;
  color: #9ca3af;
}

.empty-text {
  font-size: 12px;
  color: #9ca3af;
  padding: 4px 0;
}

.multi-mapping-summary {
  margin-top: 12px;
  font-size: 12px;
  color: #4b5563;
}

@media (max-width: 1200px) {
  .multi-mapping-columns {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 900px) {
  .multi-mapping-columns {
    grid-template-columns: 1fr;
  }
}
</style>

<style scoped>
@import './AssignAudit.css';

.ai-audit-document-upload-page {
  max-width: calc(100vw - 180px);
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: flex-start;
  box-sizing: border-box;
  margin-left: 280px;
  font-family: var(--font-family, inherit);
  color: var(--text-primary);
  overflow-y: auto;
}

.audit-content {
  width: 100%;
  max-width: var(--form-container-max-width, 1400px);
  min-width: 0;
  margin-top: 20px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.audit-title {
  font-size: 1.7rem;
  font-weight: 700;
  color: black;
  margin-bottom: 8px;
  margin-top: 22px;
  letter-spacing: 0.01em;
  position: relative;
  display: inline-block;
  padding-bottom: 6px;
  background: transparent;
  font-family: var(--font-family, inherit);
}

.audit-title::after {
  display: none;
}

.audit-subtitle {
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin-bottom: 48px;
  margin-top: -10px;
  line-height: 1.5;
}

.audit-selection-section {
  margin-bottom: 2rem !important;
  margin-top: 0 !important;
}

.audit-selection-section h3 {
  color: #2c3e50;
  margin-bottom: 15px;
  font-size: 1rem;
  font-weight: 600;
}

/* Custom Dropdown Styles */
.custom-dropdown-container {
  position: relative;
  width: 100%;
  max-width: 600px;
}

.dropdown-trigger {
  width: 100%;
  cursor: pointer;
}

.dropdown-selected {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #ffffff;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  transition: all 0.3s ease;
}

.selected-content {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.dropdown-icon {
  color: #4f7cff;
  font-size: 16px;
  width: 18px;
  text-align: center;
}

.selected-text {
  flex: 1;
  min-width: 0;
}

.selected-title {
  color: #2c3e50;
  font-weight: 600;
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.placeholder-text {
  color: #9ca3af;
  font-size: 14px;
  font-style: italic;
}

.dropdown-arrow {
  color: #6b7280;
  font-size: 12px;
  transition: transform 0.3s ease;
  width: 18px;
  text-align: center;
}

.dropdown-arrow.is-open {
  transform: rotate(180deg);
  color: #4f7cff;
}

.dropdown-options {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: #ffffff;
  border-top: none;
  border-radius: 0 0 12px 12px;
  z-index: 1000;
  max-height: 400px;
  overflow: hidden;
  animation: dropdownSlideDown 0.3s ease;
}

@keyframes dropdownSlideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.dropdown-search {
  position: relative;
  padding: 8px 12px;
  border-bottom: 1px solid #e5e7eb;
  background: #f8f9fa;
}

.search-input {
  width: 100%;
  padding: 6px 20px 6px 10px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 11px;
  background: #ffffff;
  transition: border-color 0.3s ease;
}

.search-input:focus {
  outline: none;
  box-shadow: 0 0 0 3px rgba(79, 124, 255, 0.1);
}

.search-icon {
  position: absolute;
  right: 18px;
  top: 50%;
  transform: translateY(-50%);
  color: #6b7280;
  font-size: 11px;
}

.options-list {
  max-height: 300px;
  overflow-y: auto;
}

.dropdown-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  border-bottom: 1px solid #f3f4f6;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
}

.dropdown-option:hover {
  background: #f8f9ff;
}

.dropdown-option.is-selected {
  background: linear-gradient(135deg, #e3f2fd 0%, #f8f9ff 100%);
  border-left: 4px solid #4f7cff;
}

.dropdown-option:last-child {
  border-bottom: none;
}

.option-content {
  flex: 1;
  min-width: 0;
}

.option-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
  gap: 12px;
}

.option-title {
  color: #2c3e50;
  font-weight: 600;
  font-size: 13px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
}

.option-id {
  color: #6b7280;
  font-size: 10px;
  font-weight: 500;
  background: #f3f4f6;
  padding: 2px 8px;
  border-radius: 12px;
  white-space: nowrap;
}

.option-meta {
  display: flex;
  align-items: center;
  gap: 14px;
  font-size: 11px;
}

.option-due-date {
  color: #6b7280;
  display: flex;
  align-items: center;
  gap: 6px;
}

.option-due-date i {
  color: #9ca3af;
  font-size: 10px;
}

.option-type {
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 9px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.option-type.ai {
  background: #e3f2fd;
  color: #1976d2;
}

.option-type.i {
  background: #f3e5f5;
  color: #7b1fa2;
}

.option-type.a {
  background: #e8f5e8;
  color: #2e7d32;
}

.option-check {
  color: #4f7cff;
  font-size: 14px;
  margin-left: 12px;
}

.no-options {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 24px 12px;
  color: #6b7280;
  font-style: italic;
  text-align: center;
  font-size: 12px;
}

.no-options i {
  font-size: 18px;
  color: #9ca3af;
}

.hint-text {
  color: #6b7280;
  font-size: 13px;
  margin-top: 8px;
  font-style: italic;
}

.error-text {
  color: #dc2626;
  font-size: 13px;
  margin-top: 8px;
  font-weight: 500;
}

.audit-info-section {
  margin-bottom: 2rem;
  margin-top: 0 !important;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid #e5e7eb;
}

.audit-info-section h3 {
  color: #2c3e50;
  margin-bottom: 15px;
}

.audit-meta {
  display: flex;
  gap: 20px;
  margin-bottom: 15px;
}

.audit-meta span {
  background: white;
  border: 1px solid #e5e7eb;
  padding: 5px 10px;
  border-radius: 4px;
  font-size: 14px;
}

.sebi-badge {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.sebi-badge i {
  font-size: 11px;
}

/* SEBI Insights Section */
.sebi-insights-section {
  margin-top: 20px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.sebi-insights-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.sebi-insights-header h4 {
  margin: 0;
  color: #2c3e50;
  font-size: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.sebi-insights-header h4 i {
  color: #667eea;
}

.loading-text {
  color: #6c757d;
  font-size: 14px;
  font-style: italic;
}

.sebi-insights-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 15px;
}

.sebi-insight-card {
  background: white;
  padding: 15px;
  border-radius: 8px;
  border: 1px solid #dee2e6;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
  transition: all 0.3s ease;
}

.sebi-insight-card:hover {
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
  transform: translateY(-2px);
}

.sebi-insight-card.sla-breach {
  border-left: 4px solid #dc3545;
  background: #fff5f5;
}

.sebi-insight-card.risk-high {
  border-left: 4px solid #dc3545;
  background: #fff5f5;
}

.insight-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  font-weight: 600;
  color: #495057;
  font-size: 14px;
}

.insight-header i {
  color: #667eea;
  font-size: 14px;
}

.insight-value {
  margin: 10px 0;
}

.insight-value .score {
  font-size: 24px;
  font-weight: 700;
  color: #28a745;
}

.insight-value .breach {
  font-size: 18px;
  font-weight: 600;
  color: #dc3545;
  display: flex;
  align-items: center;
  gap: 8px;
}

.insight-value .on-time {
  font-size: 16px;
  font-weight: 600;
  color: #28a745;
  display: flex;
  align-items: center;
  gap: 8px;
}

.insight-warning {
  margin-top: 8px;
  padding: 8px;
  background: #fff3cd;
  border-radius: 4px;
  color: #856404;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.insight-severity {
  margin-top: 8px;
  padding: 6px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}

.insight-severity.severity-high {
  background: #f8d7da;
  color: #721c24;
}

.insight-severity.severity-medium {
  background: #fff3cd;
  color: #856404;
}

.insight-severity.severity-low {
  background: #d1ecf1;
  color: #0c5460;
}

.risk-level {
  font-size: 18px;
  font-weight: 700;
  padding: 8px 12px;
  border-radius: 6px;
  display: inline-block;
}

.risk-level.risk-high {
  background: #f8d7da;
  color: #721c24;
}

.risk-level.risk-medium {
  background: #fff3cd;
  color: #856404;
}

.risk-level.risk-low {
  background: #d1ecf1;
  color: #0c5460;
}

.insight-factors {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #e9ecef;
}

.factor-item {
  display: flex;
  justify-content: space-between;
  padding: 4px 0;
  font-size: 12px;
}

.factor-name {
  color: #6c757d;
  text-transform: capitalize;
}

.factor-count {
  font-weight: 600;
  color: #495057;
}

.insight-pattern {
  margin-top: 8px;
  padding: 8px;
  background: #e7f3ff;
  border-radius: 4px;
  font-size: 12px;
  color: #004085;
  display: flex;
  align-items: center;
  gap: 6px;
}

/* Suggested Documents Container - System Style */
.suggested-documents-container {
  margin-top: 30px;
  margin-bottom: 2rem;
  width: 100%;
  background: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  border: 1px solid #e5e7eb;
  overflow: hidden;
}

.suggested-documents-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: #f8f9fa;
  border-bottom: 1px solid #e5e7eb;
  cursor: pointer;
  transition: background 0.2s ease;
  user-select: none;
}

.suggested-documents-header:hover {
  background: #e9ecef;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.suggested-documents-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
}

.header-subtitle {
  margin: 4px 0 0 0;
  font-size: 13px;
  color: #6b7280;
  font-weight: 400;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.selection-count {
  background: #4f7cff;
  color: white;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.expand-icon {
  font-size: 16px;
  color: #6b7280;
  transition: transform 0.3s ease;
}

.expand-icon.expanded {
  transform: rotate(180deg);
}

.suggested-documents-content {
  padding: 20px;
  background: #ffffff;
}

/* Legacy class for backward compatibility */
.relevant-documents-section {
  margin-top: 30px;
  margin-bottom: 2rem;
  width: 100%;
  padding: 25px;
  background: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.relevant-documents-section h3 {
  margin-top: 0;
  margin-bottom: 10px;
  color: #2c3e50;
  font-size: 20px;
  font-weight: 600;
}

.section-description {
  color: #6c757d;
  margin-bottom: 20px;
  font-size: 14px;
}

.loading-state {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 20px;
  color: #6c757d;
}

.relevant-documents-list {
  margin-top: 20px;
}

.relevant-documents-header {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 15px;
}

.relevant-document-item {
  display: flex;
  gap: 15px;
  padding: 15px;
  margin-bottom: 15px;
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.relevant-document-item:hover {
  background: #e9ecef;
  border-color: #dee2e6;
}

.document-checkbox {
  display: flex;
  align-items: flex-start;
  padding-top: 5px;
}

.document-checkbox input[type="checkbox"] {
  width: 20px;
  height: 20px;
  cursor: pointer;
  accent-color: #007bff;
  flex-shrink: 0;
}

.document-info {
  flex: 1;
}

.document-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.document-header h4 {
  margin: 0;
  color: #2c3e50;
  font-size: 16px;
  font-weight: 600;
}

.relevance-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.relevance-badge.relevance-high {
  background: #d4edda;
  color: #155724;
}

.relevance-badge.relevance-medium {
  background: #fff3cd;
  color: #856404;
}

.relevance-badge.relevance-low {
  background: #f8d7da;
  color: #721c24;
}

.document-meta {
  display: flex;
  gap: 15px;
  margin-bottom: 10px;
  font-size: 13px;
  color: #6c757d;
}

.document-meta span {
  display: flex;
  align-items: center;
  gap: 5px;
}

.document-summary {
  margin-bottom: 10px;
  color: #495057;
  font-size: 14px;
  line-height: 1.5;
}

.document-reason {
  margin-bottom: 10px;
  padding: 10px;
  background: #e7f3ff;
  border-left: 3px solid #007bff;
  border-radius: 4px;
  font-size: 13px;
  color: #004085;
}

.document-reason strong {
  display: block;
  margin-bottom: 5px;
}

.matched-items {
  margin-top: 10px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #dee2e6;
}

.matched-section {
  margin-bottom: 10px;
}

.matched-section:last-child {
  margin-bottom: 0;
}

.matched-section strong {
  display: block;
  margin-bottom: 6px;
  color: #495057;
  font-size: 13px;
}

.matched-section strong i {
  margin-right: 6px;
  color: #007bff;
}

.matched-tag {
  display: inline-block;
  padding: 5px 12px;
  margin: 4px 4px 4px 0;
  background: #ffffff;
  border: 1px solid #dee2e6;
  border-radius: 16px;
  font-size: 12px;
  color: #495057;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}

.no-relevant-documents {
  padding: 40px;
  text-align: center;
  color: #6c757d;
  font-size: 14px;
}

.no-relevant-documents i {
  font-size: 24px;
  margin-bottom: 10px;
  display: block;
  color: #adb5bd;
}

/* Document Actions Bar */
.documents-actions-bar {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 20px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.action-buttons-left {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  align-items: center;
}

.action-buttons-left .btn {
  min-width: 150px;
}

.action-instructions {
  background: #f8f9fa;
  padding: 12px;
  border-radius: 6px;
  border-left: 3px solid #4f7cff;
}

.action-instructions p {
  margin: 0;
  font-size: 13px;
  color: #374151;
  line-height: 1.5;
}

.action-instructions strong {
  color: #2c3e50;
}

.documents-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.document-cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 20px;
}

.document-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
  transition: all 0.2s ease;
  position: relative;
  cursor: pointer;
}

.document-card:hover {
  border-color: #4f7cff;
  box-shadow: 0 2px 4px rgba(79, 124, 255, 0.1);
}

.document-card.selected {
  border-color: #4f7cff;
  background: #f8f9ff;
  box-shadow: 0 2px 4px rgba(79, 124, 255, 0.15);
}

.card-checkbox-wrapper {
  position: absolute;
  top: 20px;
  right: 20px;
  z-index: 10;
}

.card-checkbox-wrapper input[type="checkbox"] {
  width: 20px;
  height: 20px;
  cursor: pointer;
  accent-color: #4f7cff;
}

.card-content {
  padding-right: 40px;
}

.card-header {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}

.file-icon-wrapper {
  width: 40px;
  height: 40px;
  background: #f3f4f6;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border: 1px solid #e5e7eb;
}

.file-icon {
  font-size: 20px;
  color: #4f7cff;
}

.file-info {
  flex: 1;
  min-width: 0;
}

.file-name {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #6b7280;
}

.file-meta span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.relevance-score {
  display: flex;
  align-items: flex-start;
}

.card-details {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #e5e7eb;
}

.detail-section {
  margin-bottom: 16px;
}

.detail-section:last-child {
  margin-bottom: 0;
}

.detail-section h5 {
  margin: 0 0 8px 0;
  font-size: 14px;
  font-weight: 600;
  color: #374151;
  display: flex;
  align-items: center;
  gap: 8px;
}

.detail-section h5 i {
  color: #4f7cff;
  font-size: 14px;
}

.detail-section p {
  margin: 0;
  font-size: 13px;
  color: #6b7280;
  line-height: 1.6;
}

.relevance-reason {
  background: #f8f9fa;
  padding: 12px;
  border-radius: 6px;
  border-left: 3px solid #4f7cff;
}

.matched-group {
  margin-bottom: 12px;
}

.matched-group:last-child {
  margin-bottom: 0;
}

.matched-group strong {
  display: block;
  margin-bottom: 8px;
  font-size: 13px;
  color: #374151;
  display: flex;
  align-items: center;
  gap: 6px;
}

.matched-group strong i {
  color: #4f7cff;
  font-size: 12px;
}

.tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.matched-tag .tag-id {
  color: #9ca3af;
  font-size: 11px;
}

.card-footer {
  display: flex;
  gap: 12px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #e5e7eb;
}

.card-footer .btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.no-documents-message {
  text-align: center;
  padding: 60px 20px;
  color: #6b7280;
}

.no-documents-message i {
  font-size: 48px;
  color: #d1d5db;
  margin-bottom: 16px;
  display: block;
}

.no-documents-message p {
  margin: 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: #374151;
}

.no-documents-message span {
  font-size: 14px;
  color: #6b7280;
}

.upload-section {
  margin-bottom: 2rem;
  width: 100%;
  padding-bottom: 1.5rem;
}

.upload-section h3 {
  color: #2c3e50;
  margin-bottom: 15px;
}

.upload-description {
  color: #6c757d;
  margin-bottom: 20px;
}

.policy-selection {
  margin-bottom: 25px;
}

.policy-display {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 15px;
}

.policy-info {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.policy-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.policy-label {
  font-weight: 600;
  color: #495057;
  font-size: 14px;
}

.policy-value {
  color: #212529;
  font-size: 16px;
  padding: 8px 12px;
  background: white;
  border: 1px solid #dee2e6;
  border-radius: 4px;
}

.policy-dropdowns {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
}

.form-control {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.file-upload-area {
  border: 2px dashed #ddd;
  border-radius: 8px;
  padding: 40px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-bottom: 20px;
}

.file-upload-area:hover,
.file-upload-area.dragover {
  border-color: #6b7280;
  background-color: white;
}

.upload-content {
  color: #6c757d;
}

.upload-icon {
  font-size: 48px;
  color: #6b7280;
  margin-bottom: 15px;
}

.upload-content h4 {
  color: #2c3e50;
  margin-bottom: 10px;
}

.file-limit {
  font-size: 12px;
  color: #95a5a6;
  margin-top: 10px;
}

.selected-files {
  margin-bottom: 20px;
}

.file-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.file-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.file-icon {
  color: #6b7280;
}

.file-details {
  display: flex;
  flex-direction: column;
}

.file-name {
  font-weight: 500;
  color: #2c3e50;
}

.file-size {
  font-size: 12px;
  color: #6c757d;
}

.remove-btn {
  background: var(--btn-primary-bg, #4f7cff);
  color: var(--btn-primary-text, #fff);
  border: 1px solid var(--btn-primary-bg, #4f7cff);
  border-radius: 4px;
  padding: 5px 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.remove-btn:hover {
  background: var(--btn-primary-hover-bg, #3b5bcc);
  border-color: var(--btn-primary-hover-bg, #3b5bcc);
}

.upload-progress {
  margin-bottom: 20px;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #f1f5f9;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 10px;
}

.progress-fill {
  height: 100%;
  background: #6b7280;
  transition: width 0.3s ease;
}

.progress-text {
  text-align: center;
  color: #6c757d;
  font-size: 14px;
}

.upload-actions {
  display: flex;
  gap: 15px;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--btn-primary-bg, #4f7cff);
  color: var(--btn-primary-text, #fff);
  border: 1px solid var(--btn-primary-bg, #4f7cff);
}

.btn-primary:hover:not(:disabled) {
  background: var(--btn-primary-hover-bg, #3b5bcc);
  border-color: var(--btn-primary-hover-bg, #3b5bcc);
}

.btn-secondary {
  background: var(--btn-primary-bg, #4f7cff);
  color: var(--btn-primary-text, #fff);
  border: 1px solid var(--btn-primary-bg, #4f7cff);
}

.btn-secondary:hover:not(:disabled) {
  background: var(--btn-primary-hover-bg, #3b5bcc);
  border-color: var(--btn-primary-hover-bg, #3b5bcc);
}

.btn-success {
  background: var(--btn-primary-bg, #4f7cff);
  color: var(--btn-primary-text, #fff);
  border: 1px solid var(--btn-primary-bg, #4f7cff);
}

.btn-success:hover:not(:disabled) {
  background: var(--btn-primary-hover-bg, #3b5bcc);
  border-color: var(--btn-primary-hover-bg, #3b5bcc);
}

.btn.processing {
  opacity: 0.8;
  cursor: not-allowed;
}

.btn.processing i.fa-spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.btn-danger {
  background: var(--btn-primary-bg, #4f7cff);
  color: var(--btn-primary-text, #fff);
  border: 1px solid var(--btn-primary-bg, #4f7cff);
}

.btn-danger:hover:not(:disabled) {
  background: var(--btn-primary-hover-bg, #3b5bcc);
  border-color: var(--btn-primary-hover-bg, #3b5bcc);
}

.btn-outline {
  background: var(--btn-primary-bg, #4f7cff);
  color: var(--btn-primary-text, #fff);
  border: 1px solid var(--btn-primary-bg, #4f7cff);
}

.btn-outline:hover:not(:disabled) {
  background: var(--btn-primary-hover-bg, #3b5bcc);
  border-color: var(--btn-primary-hover-bg, #3b5bcc);
}


.compliance-requirements {
  margin-top: 2rem;
  padding: 1.5rem;
  background: #f8fafc;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
}

.compliance-requirements h4 {
  margin: 0 0 1rem 0;
  font-size: 16px;
  font-weight: 600;
  color: #374151;
}

.requirements-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.requirement-item {
  background: white;
  padding: 16px;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
}

.requirement-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.requirement-title {
  font-weight: 600;
  color: #374151;
  font-size: 14px;
}

.requirement-type {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  text-transform: uppercase;
}

.requirement-type.mandatory {
  background: #fee2e2;
  color: #dc2626;
}

.requirement-type.optional {
  background: #f3f4f6;
  color: #6b7280;
}

.requirement-description {
  margin: 8px 0;
  color: #6b7280;
  font-size: 14px;
  line-height: 1.5;
}

.requirement-meta {
  display: flex;
  gap: 12px;
  align-items: center;
}

.risk-level {
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 11px;
  font-weight: 500;
  text-transform: uppercase;
}

.risk-level.high {
  background: #fee2e2;
  color: #dc2626;
}

.risk-level.medium {
  background: #fef3c7;
  color: #d97706;
}

.risk-level.low {
  background: #dcfce7;
  color: #16a34a;
}

.mandatory {
  padding: 2px 6px;
  background: #dbeafe;
  color: #2563eb;
  border-radius: 3px;
  font-size: 11px;
  font-weight: 500;
  text-transform: uppercase;
}

.no-requirements {
  text-align: center;
  padding: 2rem;
  color: #6b7280;
  font-style: italic;
}

.uploaded-documents {
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  width: 100%;
  box-sizing: border-box;
  overflow-x: hidden;
}

.uploaded-documents-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.documents-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 20px;
  width: 100%;
  box-sizing: border-box;
}

.document-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 16px;
  transition: all 0.3s ease;
  width: 100%;
  box-sizing: border-box;
  overflow: visible;
}

.document-card:hover {
  background: #f8fafc;
  border-color: #d1d5db;
}

.document-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
}

.document-main {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  width: 100%;
  box-sizing: border-box;
  min-width: 0;
}

.document-icon {
  font-size: 20px;
  color: #6b7280;
  flex-shrink: 0;
  margin-top: 2px;
}

.document-info {
  flex: 1;
  min-width: 0;
  overflow: visible;
  word-wrap: break-word;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
}

.document-info h4 {
  color: #2c3e50;
  margin: 0 0 4px 0;
  font-size: 14px;
  font-weight: 600;
  word-break: break-word;
  overflow-wrap: break-word;
  line-height: 1.4;
  max-width: 100%;
}

.document-meta {
  color: #6c757d;
  font-size: 11px;
  margin: 0;
  word-break: break-word;
  overflow-wrap: break-word;
  white-space: normal;
  line-height: 1.4;
}

.document-type {
  width: 100%;
  margin-top: 4px;
}

.document-type span {
  font-size: 12px;
  color: #6c757d;
  word-break: break-word;
}

.document-status {
  width: 100%;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 4px;
}

.status-badge {
  padding: 3px 8px;
  border-radius: 12px;
  font-size: 10px;
  font-weight: 500;
  text-transform: uppercase;
  white-space: nowrap;
}

.status-badge.pending {
  background: #fff3cd;
  color: #856404;
}

.status-badge.processing {
  background: #d1ecf1;
  color: #0c5460;
}

.status-badge.completed {
  background: #d4edda;
  color: #155724;
}

.status-badge.failed {
  background: #f8d7da;
  color: #721c24;
}

.document-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  align-items: center;
  gap: 8px;
  width: 100%;
  margin-top: 8px;
  box-sizing: border-box;
}

.document-actions .btn {
  flex-shrink: 0;
  margin: 0;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 12px;
  white-space: nowrap;
  min-width: fit-content;
}

.mapping-selector {
  width: 100%;
  margin-top: 8px;
}

.mapping-dropdown {
  width: 100%;
  padding: 6px 10px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 13px;
  background-color: white;
  word-break: break-word;
  overflow-wrap: break-word;
  box-sizing: border-box;
  max-width: 100%;
}

.mapping-dropdown option {
  white-space: normal;
  word-break: break-word;
  padding: 4px;
  overflow: visible;
}

.mappings-list {
  width: 100%;
  margin-top: 8px;
}

.mappings-badges {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex-wrap: wrap;
}

.mapping-badge {
  display: inline-block;
  padding: 6px 10px;
  background-color: #e9ecef;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 12px;
  color: #495057;
  word-break: break-word;
  overflow-wrap: break-word;
  line-height: 1.4;
}

.ai-processing-status {
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid #e5e7eb;
}

.processing-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 16px;
  margin-top: 16px;
}

.processing-details {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 15px;
  margin-top: 15px;
}

.status-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.status-label {
  color: #6c757d;
  font-weight: 500;
}

.status-value {
  color: #2c3e50;
  font-weight: 600;
}

.ai-info {
  margin-top: 15px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
}

.ai-note {
  margin: 0;
  color: #495057;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.ai-note i {
  color: #4f7cff;
}

.ai-benefits {
  font-size: 12px;
  color: #6c757d;
  font-style: italic;
  margin-left: 8px;
}

.compliance-results {
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  
}

.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.result-card {
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 20px;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 15px;
}

.result-header h4 {
  color: #2c3e50;
  margin: 0;
  flex: 1;
}

.compliance-status {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  text-transform: uppercase;
}

.compliance-status.compliant {
  background: #d4edda;
  color: #155724;
}

.compliance-status.non_compliant {
  background: #f8d7da;
  color: #721c24;
}

.compliance-status.partially_compliant {
  background: #fff3cd;
  color: #856404;
}

.compliance-status.requires_review {
  background: #d1ecf1;
  color: #0c5460;
}

.result-details p {
  margin-bottom: 8px;
  font-size: 14px;
  color: #6c757d;
}

.result-actions {
  margin-top: 15px;
}

.action-buttons {
  display: flex;
  gap: 15px;
  justify-content: center;
  margin-top: -120px;
  border-top: none !important;
}

@media (max-width: 768px) {
  .custom-dropdown-container {
    max-width: 100%;
  }
  
  .dropdown-selected {
    padding: 14px 16px;
  }
  
  .selected-content {
    gap: 10px;
  }
  
  .dropdown-icon {
    font-size: 16px;
  }
  
  .selected-title,
  .placeholder-text {
    font-size: 15px;
  }
  
  .dropdown-options {
    max-height: 300px;
  }
  
  .dropdown-option {
    padding: 14px 16px;
  }
  
  .option-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .option-title {
    font-size: 14px;
  }
  
  .option-meta {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .policy-dropdowns {
    grid-template-columns: 1fr;
  }
  
  .integration-options {
    flex-direction: column;
    gap: 0;
  }
  
  .integration-item {
    border-right: none;
    border-bottom: 1px solid #e5e7eb;
  }
  
  .integration-item:last-child {
    border-bottom: none;
  }
  
  .document-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .document-main {
    width: 100%;
  }
  
  .document-type {
    min-width: auto;
  }
  
  .document-actions {
    width: 100%;
    justify-content: flex-end;
  }
  
  .results-grid {
    grid-template-columns: 1fr;
  }
  
  .action-buttons {
    flex-direction: column;
  }
}

/* Compliance Requirements Styles */
.compliance-requirements {
  margin-top: 20px;
  padding: 20px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.compliance-requirements h4 {
  margin: 0 0 15px 0;
  color: #333;
  font-size: 16px;
}

.requirements-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.requirement-item {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 15px;
}

.requirement-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.requirement-title {
  font-weight: 600;
  color: #333;
  font-size: 14px;
}

.requirement-type {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.requirement-type.security {
  background: #fef2f2;
  color: #dc2626;
}

.requirement-type.compliance {
  background: #f0f9ff;
  color: #0369a1;
}

.requirement-type.operational {
  background: #f0fdf4;
  color: #16a34a;
}

.requirement-description {
  margin: 0 0 10px 0;
  color: #666;
  font-size: 13px;
  line-height: 1.4;
}

.requirement-meta {
  display: flex;
  gap: 10px;
  align-items: center;
}

.risk-level {
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 11px;
  font-weight: 500;
}

.risk-level.high {
  background: #fef2f2;
  color: #dc2626;
}

.risk-level.medium {
  background: #fef3c7;
  color: #d97706;
}

.risk-level.low {
  background: #f0fdf4;
  color: #16a34a;
}

.mandatory {
  background: #fef2f2;
  color: #dc2626;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 11px;
  font-weight: 500;
}

/* AI Processing Results Styles */
.ai-processing-results {
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid #e5e7eb;
}

.ai-processing-results h3 {
  color: #2c3e50;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.result-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.result-card:hover {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid #f0f0f0;
}

.result-header h4 {
  color: #2c3e50;
  margin: 0;
  flex: 1;
  font-size: 16px;
}

.compliance-status {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.compliance-status.compliant {
  background: #d4edda;
  color: #155724;
}

.compliance-status.partially_compliant {
  background: #fff3cd;
  color: #856404;
}

.compliance-status.non_compliant {
  background: #f8d7da;
  color: #721c24;
}

.compliance-status.unknown {
  background: #e2e3e5;
  color: #6c757d;
}

.ai-metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 15px;
  margin-bottom: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 6px;
}

.metric-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.metric-label {
  font-size: 12px;
  color: #6c757d;
  font-weight: 500;
}

.metric-value {
  font-size: 14px;
  color: #2c3e50;
  font-weight: 600;
}

.risk-level {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
}

.risk-level.low {
  background: #d4edda;
  color: #155724;
}

.risk-level.medium {
  background: #fff3cd;
  color: #856404;
}

.risk-level.high {
  background: #f8d7da;
  color: #721c24;
}

.ai-analysis, .ai-recommendations, .extracted-text {
  margin-bottom: 15px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 6px;
}

.ai-analysis h5, .ai-recommendations h5, .extracted-text h5 {
  margin: 0 0 10px 0;
  color: #2c3e50;
  font-size: 14px;
  font-weight: 600;
}

.ai-analysis p, .ai-recommendations p {
  margin: 5px 0;
  font-size: 13px;
  color: #495057;
  line-height: 1.4;
}

.text-preview {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  padding: 10px;
  max-height: 150px;
  overflow-y: auto;
  font-size: 12px;
  color: #495057;
  line-height: 1.4;
}

.result-actions {
  display: flex;
  gap: 10px;
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #f0f0f0;
}

.result-actions .btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
}

@media (max-width: 768px) {
  .results-grid {
    grid-template-columns: 1fr;
  }
  
  .ai-metrics {
    grid-template-columns: 1fr;
  }
  
  .result-actions {
    flex-direction: column;
  }
}
/* Force compact layout for compliance details */
.ai-audit-document-upload-page .compliance-details-expanded {
  max-height: 60vh !important;
  overflow-y: auto !important;
  padding: 15px !important;
  margin: 20px 0 !important;
}

.ai-audit-document-upload-page .compliance-details-expanded * {
  box-sizing: border-box !important;
}

/* Enhanced Compliance Details Styles */
.compliance-details-expanded {
  margin-top: 20px !important;
  margin-bottom: 20px !important;
  padding: 15px !important;
  background: #ffffff !important;
  border: 1px solid #e9ecef !important;
  border-radius: 8px !important;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1) !important;
  max-width: 100% !important;
  width: 100% !important;
  box-sizing: border-box !important;
  overflow-x: hidden !important;
  position: relative !important;
  z-index: 1 !important;
  max-height: 60vh !important;
  overflow-y: auto !important;
}

.details-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 2px solid #e9ecef;
}

.details-header h3 {
  margin: 0;
  color: #2c3e50;
  font-size: 1.4rem;
  font-weight: 600;
}

.details-header h3 i {
  color: #007bff;
  margin-right: 8px;
}

.overall-status-card {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%) !important;
  border-radius: 8px !important;
  padding: 12px !important;
  margin-bottom: 12px !important;
  border: 1px solid #dee2e6 !important;
}

.status-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  flex-wrap: wrap;
  gap: 10px;
}

.status-header h4 {
  margin: 0;
  color: #2c3e50;
  font-size: 18px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-header h4 i {
  color: #007bff;
}

.status-badges {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.compliance-status-badge {
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.compliance-status-badge.compliant {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.compliance-status-badge.non_compliant {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.compliance-status-badge.partially_compliant {
  background: #fff3cd;
  color: #856404;
  border: 1px solid #ffeaa7;
}

.compliance-status-badge.unknown {
  background: #e2e3e5;
  color: #6c757d;
  border: 1px solid #d6d8db;
}

.confidence-badge {
  background: #e3f2fd;
  color: #1976d2;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  border: 1px solid #bbdefb;
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 15px;
}

.summary-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 8px;
  font-size: 14px;
  color: #495057;
}

.summary-item i {
  color: #007bff;
  width: 16px;
  text-align: center;
}

.detailed-analysis {
  margin-top: 20px;
}

.analysis-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 2px solid #e9ecef;
}

.analysis-header h4 {
  margin: 0;
  color: #2c3e50;
  font-size: 18px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.analysis-header h4 i {
  color: #28a745;
}

.analysis-count {
  background: #007bff;
  color: white;
  padding: 6px 12px;
  border-radius: 15px;
  font-size: 12px;
  font-weight: 600;
}

.requirements-grid {
  display: grid !important;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)) !important;
  gap: 12px !important;
  margin-top: 12px !important;
}

.requirement-card {
  background: #ffffff !important;
  border: 1px solid #e9ecef !important;
  border-radius: 6px !important;
  padding: 10px !important;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
  transition: all 0.3s ease !important;
  max-width: 100% !important;
  box-sizing: border-box !important;
  margin-bottom: 8px !important;
}

.requirement-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.requirement-header {
  margin-bottom: 20px;
}

.requirement-number {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  flex-wrap: wrap;
  gap: 15px;
}

.req-idx {
  font-size: 14px;
  font-weight: 600;
  color: #2c3e50;
  background: #f8f9fa;
  padding: 6px 12px;
  border-radius: 15px;
  border: 1px solid #dee2e6;
  line-height: 1.3;
  word-wrap: break-word;
  hyphens: auto;
  display: block;
  max-width: 100%;
}

.relevance-meter {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 200px;
}

.meter-label {
  font-size: 12px;
  color: #6c757d;
  font-weight: 600;
  min-width: 60px;
}

.meter-bar {
  flex: 1;
  height: 8px;
  background: #e9ecef;
  border-radius: 4px;
  position: relative;
  overflow: hidden;
}

.meter-fill {
  height: 100%;
  background: linear-gradient(90deg, #dc3545 0%, #ffc107 50%, #28a745 100%);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.meter-value {
  font-size: 12px;
  font-weight: 700;
  color: #2c3e50;
  min-width: 35px;
  text-align: right;
}

.evidence-section, .missing-section {
  margin-bottom: 8px !important;
  padding: 8px !important;
  border-radius: 4px !important;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-weight: 600;
  font-size: 14px;
  color: #2c3e50;
}

.section-header i {
  font-size: 16px;
}

.text-success {
  color: #28a745 !important;
}

.text-warning {
  color: #ffc107 !important;
}

.evidence-list, .missing-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.evidence-item, .missing-item {
  display: flex;
  align-items: flex-start;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
  font-size: 13px;
  line-height: 1.5;
}

.missing-item {
  background: #fffbf0;
}

.evidence-item i, .missing-item i {
  color: #6c757d;
  margin-top: 2px;
  font-size: 12px;
}

.no-analysis {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
  color: #6c757d;
  font-style: italic;
  text-align: center;
  justify-content: center;
}

.no-analysis i {
  color: #6c757d;
}

.no-analysis-available {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 30px;
  background: #f8f9fa;
  border-radius: 10px;
  color: #6c757d;
  font-style: italic;
  margin-top: 20px;
}

.no-analysis-available i {
  font-size: 24px;
  color: #adb5bd;
}


/* Responsive Design */
@media (min-width: 1200px) {
  .requirements-grid {
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
    max-width: 1200px;
    margin: 20px auto 0;
  }
}

@media (max-width: 768px) {
  .compliance-details-expanded {
    padding: 10px !important;
    max-height: 50vh !important;
    margin-top: 15px !important;
    margin-bottom: 15px !important;
  }
  
  .details-header {
    flex-direction: column !important;
    align-items: flex-start !important;
    gap: 6px !important;
    margin-bottom: 12px !important;
  }
  
  .details-header h3 {
    font-size: 1rem !important;
  }
  
  .requirements-grid {
    grid-template-columns: 1fr !important;
    gap: 8px !important;
  }
  
  .requirement-card {
    padding: 8px !important;
    margin-bottom: 6px !important;
  }
  
  .overall-status-card {
    padding: 10px !important;
    margin-bottom: 10px !important;
  }
  
  .status-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .status-badges {
    width: 100%;
    justify-content: flex-start;
  }
  
  .status-summary {
    grid-template-columns: 1fr;
  }
  
  .requirement-number {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .relevance-meter {
    width: 100%;
    min-width: auto;
  }
  
  .analysis-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
}
</style>
