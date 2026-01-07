<template>
  <div class="organizational-controls">
    <!-- Page Header -->
    <div class="page-header">
      <h1>Organizational Controls Mapping</h1>
      <p class="subtitle">Map your organizational controls to framework compliance requirements</p>
    </div>

    <!-- Three Section Split Screen -->
    <div class="split-screen-container">
      
      <!-- ═══════════════════════════════════════════════════════════════════════════ -->
      <!-- SECTION 1: FRAMEWORK HIERARCHY (Left Panel) -->
      <!-- ═══════════════════════════════════════════════════════════════════════════ -->
      <div class="panel panel-left">
        <div class="panel-header">
          <div class="panel-title">
            <i class="fas fa-sitemap"></i>
            <span>Framework Structure</span>
          </div>
        </div>

        <!-- Framework Dropdown -->
        <div class="framework-selector">
          <label>Select Framework</label>
          <select v-model="selectedFrameworkId" @change="loadFrameworkControls">
            <option value="">-- Select Framework --</option>
            <option v-for="fw in frameworks" :key="fw.id || fw.FrameworkId" :value="fw.id || fw.FrameworkId">
              {{ fw.name || fw.FrameworkName }}
            </option>
          </select>
        </div>

        <!-- Search Box -->
        <div v-if="selectedFrameworkId && !isLoading" class="search-box">
          <div class="search-input-wrapper">
            <i class="fas fa-search search-icon"></i>
            <input 
              type="text" 
              v-model="searchQuery" 
              placeholder="Search policies, sub-policies, compliances..."
              @input="handleSearch"
              class="search-input"
            />
            <button v-if="searchQuery" @click="clearSearch" class="search-clear-btn">
              <i class="fas fa-times"></i>
            </button>
          </div>
          <div v-if="searchQuery" class="search-results-info">
            <span v-if="searchResultsCount > 0" class="results-count">
              <i class="fas fa-check-circle"></i> {{ searchResultsCount }} result{{ searchResultsCount !== 1 ? 's' : '' }} found
            </span>
            <span v-else class="no-results">
              <i class="fas fa-info-circle"></i> No results found
            </span>
          </div>
        </div>

        <!-- Loading State -->
        <div v-if="isLoading" class="panel-loading">
          <div class="spinner"></div>
          <p>Loading...</p>
        </div>

        <!-- Hierarchy Tree -->
        <div v-if="selectedFrameworkId && !isLoading" class="hierarchy-tree">
          <div class="tree-stats">
            <span class="tree-stat">
              <i class="fas fa-folder"></i> {{ frameworkControls.length }} Policies
            </span>
            <span class="tree-stat">
              <i class="fas fa-folder-open"></i> {{ getTotalSubPoliciesCount() }} Sub-Policies
            </span>
            <span class="tree-stat">
              <i class="fas fa-clipboard-list"></i> {{ getTotalControlsCount() }} Controls
            </span>
          </div>

          <!-- Tree Content -->
          <div class="tree-content" v-if="selectedFrameworkId">
            <!-- Framework Root Node -->
            <div class="tree-framework">
              <div class="tree-item framework-item" 
                   :class="{ 
                     expanded: expandedFramework,
                     'search-match': searchQuery && isFrameworkMatch()
                   }"
                   @click="toggleFramework()">
                <i :class="expandedFramework ? 'fas fa-chevron-down' : 'fas fa-chevron-right'" class="expand-icon"></i>
                <i class="fas fa-layer-group item-icon framework-icon"></i>
                <div class="item-content">
                  <span class="item-id">{{ getSelectedFrameworkId() }}</span>
                  <span class="item-name" v-html="highlightText(getSelectedFrameworkName())"></span>
                </div>
                <button class="tree-upload-btn" @click.stop="openFrameworkUpload()" title="Upload documents for entire framework">
                  <i class="fas fa-cloud-upload-alt"></i>
                </button>
                <span class="item-badge">{{ getTotalControlsCount() }}</span>
              </div>

              <!-- Policies (nested under framework) -->
              <div v-show="expandedFramework && filteredFrameworkControls.length" class="tree-children">
                <div v-for="policy in filteredFrameworkControls" :key="policy.PolicyId" class="tree-policy">
              
              <!-- Policy Item -->
              <div class="tree-item policy-item" 
                   :class="{ 
                     expanded: expandedPolicies.includes(policy.PolicyId),
                     'search-match': searchQuery && isPolicyMatch(policy)
                   }"
                   @click="togglePolicy(policy.PolicyId)">
                <i :class="expandedPolicies.includes(policy.PolicyId) ? 'fas fa-chevron-down' : 'fas fa-chevron-right'" class="expand-icon"></i>
                <i class="fas fa-folder item-icon policy-icon"></i>
                <div class="item-content">
                  <span class="item-id" v-html="highlightText(policy.Identifier || 'N/A')"></span>
                  <span class="item-name" v-html="highlightText(policy.PolicyName)"></span>
                </div>
                <button class="tree-upload-btn" @click.stop="openUploadModal('policy', policy)" title="Upload documents for this policy">
                  <i class="fas fa-cloud-upload-alt"></i>
                </button>
                <span class="item-badge">{{ getFilteredComplianceCount(policy) }}</span>
              </div>

              <!-- SubPolicies -->
              <div v-show="expandedPolicies.includes(policy.PolicyId)" class="tree-children">
                <div v-for="subpolicy in getFilteredSubPolicies(policy)" :key="subpolicy.SubPolicyId" class="tree-subpolicy">
                  
                  <!-- SubPolicy Item -->
                  <div class="tree-item subpolicy-item"
                       :class="{ 
                         expanded: expandedSubPolicies.includes(subpolicy.SubPolicyId),
                         'search-match': searchQuery && isSubPolicyMatch(subpolicy)
                       }"
                       @click="toggleSubPolicy(subpolicy.SubPolicyId)">
                    <i :class="expandedSubPolicies.includes(subpolicy.SubPolicyId) ? 'fas fa-chevron-down' : 'fas fa-chevron-right'" class="expand-icon"></i>
                    <i class="fas fa-folder-open item-icon subpolicy-icon"></i>
                    <div class="item-content">
                      <span class="item-id" v-html="highlightText(subpolicy.Identifier || 'N/A')"></span>
                      <span class="item-name" v-html="highlightText(subpolicy.SubPolicyName)"></span>
                    </div>
                    <button class="tree-upload-btn" @click.stop="openUploadModal('subpolicy', subpolicy, policy)" title="Upload documents for this sub-policy">
                      <i class="fas fa-cloud-upload-alt"></i>
                    </button>
                    <span class="item-badge">{{ getFilteredCompliances(subpolicy).length }}</span>
                  </div>

                  <!-- Controls -->
                  <div v-show="expandedSubPolicies.includes(subpolicy.SubPolicyId)" class="tree-children">
                    <div v-for="compliance in getFilteredCompliances(subpolicy)" 
                         :key="compliance.ComplianceId" 
                         class="tree-item control-item"
                         :class="{ 
                           'has-control': compliance.OrgControlId,
                           'fully-mapped': compliance.MappingStatus === 'fully_mapped',
                           'partially-mapped': compliance.MappingStatus === 'partially_mapped',
                           'not-mapped': compliance.MappingStatus === 'not_mapped',
                           'search-match': searchQuery && isComplianceMatch(compliance)
                         }">
                      <i class="fas fa-file-alt item-icon control-icon"></i>
                      <div class="item-content">
                        <span class="item-id" v-html="highlightText(compliance.Identifier || 'N/A')"></span>
                        <span class="item-name" v-html="highlightText(compliance.ComplianceTitle)"></span>
                      </div>
                      <button class="tree-upload-btn small" @click.stop="openUploadModal('compliance', compliance, policy, subpolicy)" title="Upload document">
                        <i class="fas fa-cloud-upload-alt"></i>
                      </button>
                      <div class="control-status-dot" :class="compliance.MappingStatus"></div>
                    </div>
                  </div>
                </div>
              </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Empty State -->
          <div v-if="selectedFrameworkId && !expandedFramework && !filteredFrameworkControls.length" class="tree-empty">
            <i class="fas fa-folder-open"></i>
            <p v-if="searchQuery">No results found for "{{ searchQuery }}"</p>
            <p v-else>No controls found</p>
            <button v-if="searchQuery" @click="clearSearch" class="btn-clear-search">
              <i class="fas fa-times"></i> Clear Search
            </button>
          </div>
        </div>

        <!-- No Framework Selected -->
        <div v-if="!selectedFrameworkId && !isLoading" class="panel-empty">
          <i class="fas fa-hand-pointer"></i>
          <p>Select a framework to view its structure</p>
        </div>
      </div>

      <!-- ═══════════════════════════════════════════════════════════════════════════ -->
      <!-- SECTION 2: ORGANIZATIONAL CONTROL INPUT (Middle Panel) -->
      <!-- ═══════════════════════════════════════════════════════════════════════════ -->
      <div class="panel panel-middle">
        <div class="panel-header">
          <div class="panel-title">
            <i class="fas fa-building"></i>
            <span>{{ showUploadInterface ? 'Upload Documents' : 'Organizational Control' }}</span>
          </div>
          <button v-if="showUploadInterface" @click="closeUploadInterface" class="btn-close-upload" title="Close Upload">
            <i class="fas fa-times"></i>
          </button>
          <button v-else-if="selectedCompliance" @click="showBulkUploadModal = true" class="btn-bulk-upload" title="Bulk Upload">
            <i class="fas fa-file-upload"></i>
          </button>
        </div>

        <!-- Upload Interface -->
        <div v-if="showUploadInterface" class="upload-interface">
          <!-- Upload Target Info -->
          <div class="upload-target-header">
            <div class="target-badge" :class="uploadTarget.type">
              <i :class="getTargetIcon(uploadTarget.type)"></i>
              <span>{{ uploadTarget.type === 'policy' ? 'Policy' : uploadTarget.type === 'subpolicy' ? 'Sub-Policy' : uploadTarget.type === 'compliance' ? 'Compliance' : 'Framework' }}</span>
            </div>
            <div class="target-details">
              <span class="target-id">{{ uploadTarget.identifier }}</span>
              <span class="target-name">{{ uploadTarget.name }}</span>
            </div>
          </div>

          <!-- Upload Type Selection -->
          <div class="upload-section">
            <h3 class="section-title"><i class="fas fa-list-ul"></i> Upload Type</h3>
            <div class="upload-type-options">
              <label class="upload-type-option" :class="{ active: uploadMode === 'single' }">
                <input type="radio" v-model="uploadMode" value="single" />
                <div class="option-icon"><i class="fas fa-file"></i></div>
                <div class="option-content">
                  <span class="option-title">Single Document</span>
                  <span class="option-desc">Upload one document</span>
                </div>
              </label>
              <label class="upload-type-option" :class="{ active: uploadMode === 'multiple' }">
                <input type="radio" v-model="uploadMode" value="multiple" />
                <div class="option-icon"><i class="fas fa-copy"></i></div>
                <div class="option-content">
                  <span class="option-title">Multiple Documents</span>
                  <span class="option-desc">Upload multiple files for the same compliance(s)</span>
                </div>
              </label>
              <label class="upload-type-option" :class="{ active: uploadMode === 'bulk' }" v-if="uploadTarget.type !== 'compliance'">
                <input type="radio" v-model="uploadMode" value="bulk" />
                <div class="option-icon"><i class="fas fa-layer-group"></i></div>
                <div class="option-content">
                  <span class="option-title">Bulk Upload</span>
                  <span class="option-desc">Apply same file(s) to all controls in {{ uploadTarget.type === 'policy' ? 'this policy' : uploadTarget.type === 'subpolicy' ? 'this sub-policy' : 'framework' }}</span>
                </div>
              </label>
            </div>
          </div>

          <!-- File Upload Area -->
          <div class="upload-section">
            <h3 class="section-title"><i class="fas fa-file-upload"></i> Select Files</h3>
            <div class="file-upload-area large" 
                 @click="triggerUploadInput" 
                 @dragover.prevent="dragOver = true" 
                 @dragleave="dragOver = false"
                 @drop.prevent="handleFileDrop"
                 :class="{ 'drag-over': dragOver }">
              <input 
                type="file" 
                ref="uploadInput" 
                @change="handleUploadFileSelect" 
                accept=".pdf,.docx,.doc,.txt,.xlsx,.xls,.pptx,.ppt"
                :multiple="uploadMode !== 'single'"
                style="display: none" 
              />
              <div v-if="uploadFiles.length === 0" class="upload-placeholder">
                <div class="upload-icon-wrapper">
                  <i class="fas fa-cloud-upload-alt"></i>
                </div>
                <p>Drag & drop files here or click to browse</p>
                <small>Supported: PDF, DOCX, DOC, TXT, XLSX, XLS, PPTX, PPT</small>
                <small v-if="uploadMode === 'single'" class="upload-limit">Max 1 file</small>
                <small v-else-if="uploadMode === 'multiple'" class="upload-limit">Max 10 files</small>
                <small v-else-if="uploadMode === 'bulk'" class="upload-limit">No limit</small>
              </div>
              <div v-else class="selected-files-list">
                <div v-for="(fileObj, index) in uploadFiles" :key="index" class="selected-file-item" :class="fileObj.status">
                  <i :class="getDocumentIcon(fileObj.name || (fileObj.file && fileObj.file.name))"></i>
                  <div class="file-details">
                    <span class="file-name">{{ fileObj.name || (fileObj.file && fileObj.file.name) }}</span>
                    <span class="file-size">{{ formatFileSize(fileObj.size || (fileObj.file && fileObj.file.size)) }}</span>
                    <!-- Progress Bar -->
                    <div v-if="fileObj.status === 'uploading' || fileObj.status === 'completed'" class="file-progress-container">
                      <div class="file-progress-bar">
                        <div class="file-progress-fill" :style="{ width: fileObj.progress + '%' }"></div>
                      </div>
                      <span class="file-progress-text">{{ fileObj.progress }}%</span>
                    </div>
                    <!-- Status Icons -->
                    <div v-if="fileObj.status === 'completed'" class="file-status-icon completed">
                      <i class="fas fa-check-circle"></i>
                    </div>
                    <div v-if="fileObj.status === 'error'" class="file-status-icon error">
                      <i class="fas fa-exclamation-circle"></i>
                    </div>
                  </div>
                  <button v-if="fileObj.status !== 'uploading'" @click.stop="removeUploadFile(index)" class="btn-remove-file">&times;</button>
                  <div v-else class="uploading-spinner">
                    <i class="fas fa-spinner fa-spin"></i>
                  </div>
                </div>
                <button v-if="uploadMode !== 'single' && (uploadMode === 'bulk' || uploadFiles.length < 10)" @click.stop="triggerUploadInput" class="btn-add-more">
                  <i class="fas fa-plus"></i> Add More Files
                </button>
              </div>
            </div>
          </div>

          <!-- Scope Selection for Non-Compliance Targets -->
          <div class="upload-section" v-if="uploadTarget.type !== 'compliance' && uploadMode === 'bulk'">
            <h3 class="section-title"><i class="fas fa-sitemap"></i> Apply To</h3>
            <div class="scope-info">
              <i class="fas fa-info-circle"></i>
              <span>Documents will be applied to all {{ uploadTarget.type === 'policy' ? 'controls in this policy' : uploadTarget.type === 'subpolicy' ? 'controls in this sub-policy' : 'controls in the framework' }}</span>
            </div>
          </div>

          <!-- Upload Actions -->
          <div class="upload-actions">
            <button @click="closeUploadInterface" class="btn-cancel">Cancel</button>
            <button @click="processUpload" class="btn-upload" :disabled="isUploading || uploadFiles.length === 0">
              <i :class="isUploading ? 'fas fa-spinner fa-spin' : 'fas fa-upload'"></i>
              {{ isUploading ? 'Uploading...' : `Upload ${uploadFiles.length} File${uploadFiles.length !== 1 ? 's' : ''}` }}
            </button>
            <button @click="runAIAuditAfterUpload" class="btn-run-ai-audit" :disabled="isAuditing || !filesUploadedSuccessfully">
              <i :class="isAuditing ? 'fas fa-spinner fa-spin' : 'fas fa-robot'"></i>
              {{ isAuditing ? 'Running AI...' : 'Run AI Audit' }}
            </button>
          </div>
          
          <!-- AI Audit Progress Bar -->
          <div v-if="isAuditing" class="audit-progress-container">
            <div class="audit-progress-header">
              <span class="audit-progress-label">
                <i class="fas fa-brain"></i>
                AI Audit in Progress
              </span>
              <span class="audit-progress-percentage">{{ auditProgress }}%</span>
            </div>
            <div class="audit-progress-bar">
              <div class="audit-progress-fill" :style="{ width: auditProgress + '%' }"></div>
            </div>
          </div>
        </div>

        <!-- No Control Selected State -->
        <div v-if="!showUploadInterface" class="panel-empty">
          <i class="fas fa-mouse-pointer"></i>
          <h3>Select a Control</h3>
          <p>Click on a control from the framework structure to view details and upload documents. You can also click the upload icon on any policy, sub-policy, or control to upload documents directly.</p>
        </div>
      </div>

      <!-- ═══════════════════════════════════════════════════════════════════════════ -->
      <!-- SECTION 3: AI MAPPING RESULTS (Right Panel) -->
      <!-- ═══════════════════════════════════════════════════════════════════════════ -->
      <div class="panel panel-right">
        <div class="panel-header">
          <div class="panel-title">
            <i class="fas fa-brain"></i>
            <span>AI Analysis Results</span>
          </div>
          <button v-if="selectedCompliance && selectedCompliance.OrgControlId && selectedCompliance.MappingStatus === 'not_audited'" 
                  @click="runSingleAudit(selectedCompliance)" 
                  class="btn-run-audit"
                  :disabled="auditingComplianceId === selectedCompliance.ComplianceId">
            <i class="fas fa-play"></i>
            {{ auditingComplianceId === selectedCompliance.ComplianceId ? 'Running...' : 'Run Audit' }}
          </button>
        </div>

        <!-- Audit Results (Show when audit was just run) -->
        <div v-if="auditResults && auditResults.length > 0" class="bulk-audit-results">
          <div class="bulk-results-header">
            <h3>
              <i class="fas fa-list-check"></i>
              Audit Results
              <span class="results-count">({{ auditResults.length }} compliance{{ auditResults.length !== 1 ? 's' : '' }})</span>
            </h3>
          </div>
          
          <div class="bulk-results-list">
            <div v-for="result in auditResults" :key="result.compliance_id || result.org_control_id" 
                 class="bulk-result-item"
                 :class="result.mapping_status || 'not_audited'">
              <div class="result-item-header">
                <div class="result-status-badge" :class="result.mapping_status || 'not_audited'">
                  <i :class="getMappingStatusIcon(result.mapping_status || 'not_audited')"></i>
                  <span>{{ formatMappingStatus(result.mapping_status || 'not_audited') }}</span>
                </div>
                <div v-if="result.confidence_score" class="result-confidence">
                  <span class="confidence-label">Confidence:</span>
                  <span class="confidence-value" :class="getConfidenceClass(result.confidence_score)">
                    {{ result.confidence_score }}%
                  </span>
                </div>
              </div>
              <div class="result-item-content">
                <div class="result-compliance-title">
                  <i class="fas fa-file-alt"></i>
                  <span>{{ result.compliance_title || 'Compliance ' + (result.compliance_id || 'N/A') }}</span>
                </div>
                <div v-if="result.status === 'error'" class="result-error">
                  <i class="fas fa-exclamation-circle"></i>
                  <span>{{ result.message || 'Error during audit' }}</span>
                </div>
                <div v-else-if="result.status === 'skipped'" class="result-skipped">
                  <i class="fas fa-info-circle"></i>
                  <span>{{ result.message || 'Skipped' }}</span>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Save Results Button -->
          <div class="bulk-results-actions">
            <button @click="saveAndRefreshResults" class="btn-save-results" :disabled="isSaving">
              <i :class="isSaving ? 'fas fa-spinner fa-spin' : 'fas fa-save'"></i>
              {{ isSaving ? 'Saving...' : 'Save Results' }}
            </button>
          </div>
        </div>

        <!-- Control Selected with Results (Show when no audit results but compliance is selected) -->
        <div v-else-if="selectedCompliance" class="ai-results-container">
          
          <!-- Mapping Status -->
          <div class="mapping-status-card" :class="selectedCompliance.MappingStatus">
            <div class="status-icon">
              <i :class="getMappingStatusIcon(selectedCompliance.MappingStatus)"></i>
            </div>
            <div class="status-content">
              <span class="status-label">Mapping Status</span>
              <span class="status-value">{{ formatMappingStatus(selectedCompliance.MappingStatus) }}</span>
            </div>
          </div>

          <!-- AI Results -->
          <div v-if="selectedCompliance.MappingStatus !== 'not_audited'" class="ai-results-details">
            
            <!-- Confidence Score -->
            <div class="result-card confidence-card" v-if="selectedCompliance.ConfidenceScore">
              <div class="result-header">
                <i class="fas fa-chart-line"></i>
                <span>AI Confidence</span>
              </div>
              <div class="confidence-display">
                <div class="confidence-bar">
                  <div class="confidence-fill" 
                       :style="{ width: selectedCompliance.ConfidenceScore + '%' }" 
                       :class="getConfidenceClass(selectedCompliance.ConfidenceScore)"></div>
                </div>
                <span class="confidence-value" :class="getConfidenceClass(selectedCompliance.ConfidenceScore)">
                  {{ selectedCompliance.ConfidenceScore }}%
                </span>
              </div>
            </div>

            <!-- What is Satisfying -->
            <div v-if="getAIAnalysisField('what_is_satisfying')" class="result-card satisfying-card">
              <div class="result-header">
                <i class="fas fa-check-circle"></i>
                <span>What is Satisfying</span>
              </div>
              <p class="result-text">{{ getAIAnalysisField('what_is_satisfying') }}</p>
            </div>

            <!-- What is Left -->
            <div v-if="getAIAnalysisField('what_is_left')" class="result-card missing-card">
              <div class="result-header">
                <i class="fas fa-exclamation-triangle"></i>
                <span>What is Left</span>
              </div>
              <p class="result-text">{{ getAIAnalysisField('what_is_left') }}</p>
            </div>

            <!-- Why Not Mapped -->
            <div v-if="getAIAnalysisField('why_not_mapped')" class="result-card not-mapped-card">
              <div class="result-header">
                <i class="fas fa-times-circle"></i>
                <span>Why Not Mapped</span>
              </div>
              <p class="result-text">{{ getAIAnalysisField('why_not_mapped') }}</p>
            </div>
          </div>

          <!-- Not Audited State -->
          <div v-else class="not-audited-state">
            <div class="not-audited-icon">
              <i class="fas fa-robot"></i>
            </div>
            <h4>Not Yet Audited</h4>
            <p v-if="selectedCompliance.OrgControlId">Click "Run Audit" to analyze this control with AI</p>
            <p v-else>Add an organizational control first, then run AI audit</p>
          </div>
        </div>

        <!-- No Control Selected -->
        <div v-else class="panel-empty">
          <i class="fas fa-chart-bar"></i>
          <p>Select a control to view AI analysis results</p>
        </div>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════════════════════ -->
    <!-- MODALS -->
    <!-- ═══════════════════════════════════════════════════════════════════════════ -->

    <!-- Legacy Bulk Upload Modal (keeping for compatibility) -->
    <div v-if="showBulkUploadModal" class="modal-overlay" @click.self="showBulkUploadModal = false">
      <div class="modal-content modal-large">
        <div class="modal-header">
          <h2><i class="fas fa-file-upload"></i> Bulk Upload Organizational Controls</h2>
          <button @click="showBulkUploadModal = false" class="btn-close">&times;</button>
        </div>
        
        <p class="modal-subtitle">Upload documents containing organizational controls for multiple framework requirements</p>

        <div class="modal-body">
          <!-- Upload Scope Selection -->
          <div class="modal-input-section">
            <h3>Select Upload Scope</h3>
            <div class="scope-options">
              <label class="scope-option" :class="{ active: bulkUploadType === 'bulk' }">
                <input type="radio" v-model="bulkUploadType" value="bulk" />
                <i class="fas fa-layer-group"></i>
                <span>Entire Framework</span>
              </label>
              <label class="scope-option" :class="{ active: bulkUploadType === 'policy' }">
                <input type="radio" v-model="bulkUploadType" value="policy" />
                <i class="fas fa-folder"></i>
                <span>Specific Policy</span>
              </label>
              <label class="scope-option" :class="{ active: bulkUploadType === 'subpolicy' }">
                <input type="radio" v-model="bulkUploadType" value="subpolicy" />
                <i class="fas fa-folder-open"></i>
                <span>Specific Sub-Policy</span>
              </label>
            </div>
          </div>

          <!-- Policy Selection -->
          <div class="modal-input-section" v-if="bulkUploadType === 'policy' || bulkUploadType === 'subpolicy'">
            <h3>Select Policy</h3>
            <select v-model="selectedBulkPolicyId" @change="selectedBulkSubPolicyId = ''">
              <option value="">-- Select Policy --</option>
              <option v-for="policy in frameworkControls" :key="policy.PolicyId" :value="policy.PolicyId">
                {{ policy.Identifier }} - {{ policy.PolicyName }}
              </option>
            </select>
          </div>

          <!-- Sub-Policy Selection -->
          <div class="modal-input-section" v-if="bulkUploadType === 'subpolicy' && selectedBulkPolicyId">
            <h3>Select Sub-Policy</h3>
            <select v-model="selectedBulkSubPolicyId">
              <option value="">-- Select Sub-Policy --</option>
              <option v-for="sp in getSubPoliciesForPolicy(selectedBulkPolicyId)" :key="sp.SubPolicyId" :value="sp.SubPolicyId">
                {{ sp.Identifier }} - {{ sp.SubPolicyName }}
              </option>
            </select>
          </div>

          <!-- File Upload -->
          <div class="modal-input-section">
            <h3>Upload Document</h3>
            <div class="file-upload-area large" @click="triggerBulkFileInput" @dragover.prevent @drop.prevent="handleBulkFileDrop">
              <input type="file" ref="bulkFileInput" @change="handleBulkFileSelect" accept=".pdf,.docx,.doc,.txt,.xlsx" style="display: none" />
              <div v-if="!bulkFile" class="upload-placeholder">
                <i class="fas fa-cloud-upload-alt"></i>
                <p>Drag & drop or click to upload</p>
                <small>Supported: PDF, DOCX, DOC, TXT, XLSX</small>
              </div>
              <div v-else class="selected-file-display">
                <i class="fas fa-file-check"></i>
                <span>{{ bulkFile.name }}</span>
                <button @click.stop="clearBulkFile" class="btn-remove-file">&times;</button>
              </div>
            </div>
          </div>
        </div>

        <div class="modal-actions">
          <button @click="showBulkUploadModal = false" class="btn-cancel">Cancel</button>
          <button @click="uploadBulkDocument" class="btn-save" :disabled="isUploading || !bulkFile || !isValidBulkUpload">
            <i class="fas fa-upload"></i> {{ isUploading ? 'Uploading...' : 'Upload Document' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Toast Notification -->
    <div v-if="toast.show" :class="['toast', toast.type]">
      <i :class="toast.type === 'success' ? 'fas fa-check-circle' : 'fas fa-exclamation-circle'"></i>
      {{ toast.message }}
    </div>
  </div>
</template>

<script>
import { axiosInstance } from '@/config/api.js';

export default {
  name: 'OrganizationalControls',
  data() {
    return {
      frameworks: [],
      selectedFrameworkId: null,
      frameworkControls: [],
      statistics: null,
      
      // Selected items for middle and right panels
      selectedCompliance: null,
      selectedSubPolicy: null,
      selectedPolicy: null,
      
      // Expanded states
      expandedFramework: true, // Framework is expanded by default
      expandedPolicies: [],
      expandedSubPolicies: [],
      
      // Modal states
      showBulkUploadModal: false,
      showUploadInterface: false,
      controlText: '',
      selectedFile: null,
      bulkFile: null,
      
      // Upload interface
      uploadMode: 'single', // single, multiple, bulk
      uploadFiles: [],
      uploadTarget: {
        type: '', // policy, subpolicy, compliance, framework
        id: null,
        identifier: '',
        name: '',
        policyId: null,
        subPolicyId: null
      },
      dragOver: false,
      uploadedDocuments: [], // Documents for current compliance
      filesUploadedSuccessfully: false, // Track if files were just uploaded
      
      // Bulk upload options
      bulkUploadType: 'bulk',
      selectedBulkPolicyId: '',
      selectedBulkSubPolicyId: '',
      
      // Loading states
      isLoading: false,
      isSaving: false,
      isAuditing: false,
      isUploading: false,
      auditingComplianceId: null,
      auditProgress: 0, // AI audit progress (0-100)
      
      // Toast notification
      toast: {
        show: false,
        message: '',
        type: 'success'
      },
      
      // Search
      searchQuery: '',
      searchResultsCount: 0,
      
      // Audit results for bulk operations
      auditResults: null, // Stores audit results after completion
      auditTargetType: null // Type of target that was audited (policy, subpolicy, compliance)
    };
  },
  computed: {
    isValidBulkUpload() {
      if (this.bulkUploadType === 'bulk') return true;
      if (this.bulkUploadType === 'policy') return !!this.selectedBulkPolicyId;
      if (this.bulkUploadType === 'subpolicy') return !!this.selectedBulkSubPolicyId;
      return false;
    },
    
    filteredFrameworkControls() {
      if (!this.searchQuery.trim()) {
        return this.frameworkControls;
      }
      
      const filtered = [];
      
      for (const policy of this.frameworkControls) {
        const policyMatches = this.isPolicyMatch(policy);
        const matchingSubPolicies = [];
        
        for (const subpolicy of (policy.SubPolicies || [])) {
          const subPolicyMatches = this.isSubPolicyMatch(subpolicy);
          const matchingCompliances = (subpolicy.Compliances || []).filter(c => this.isComplianceMatch(c));
          
          // Include subpolicy if it matches or has matching compliances
          if (subPolicyMatches || matchingCompliances.length > 0) {
            matchingSubPolicies.push({
              ...subpolicy,
              _filteredCompliances: matchingCompliances.length > 0 ? matchingCompliances : subpolicy.Compliances
            });
          }
        }
        
        // Include policy if it matches or has matching subpolicies
        if (policyMatches || matchingSubPolicies.length > 0) {
          filtered.push({
            ...policy,
            _filteredSubPolicies: matchingSubPolicies.length > 0 ? matchingSubPolicies : policy.SubPolicies
          });
        }
      }
      
      return filtered;
    }
  },
  async mounted() {
    await this.loadFrameworks();
  },
  methods: {
    async loadFrameworks() {
      try {
        const response = await axiosInstance.get('/api/all-policies/frameworks/', {
          params: { active_only: 'true' }
        });
        console.log('Frameworks API response:', response.data);
        
        if (response.data.success && response.data.frameworks) {
          this.frameworks = response.data.frameworks;
        } else if (Array.isArray(response.data)) {
          this.frameworks = response.data;
        } else if (response.data && typeof response.data === 'object') {
          this.frameworks = response.data.frameworks || Object.values(response.data);
        }
        
        console.log('Loaded frameworks:', this.frameworks);
      } catch (error) {
        console.error('Error loading frameworks:', error);
        this.showToast('Error loading frameworks', 'error');
      }
    },
    
    getSelectedFrameworkName() {
      if (!this.selectedFrameworkId) return '';
      const framework = this.frameworks.find(f => (f.id || f.FrameworkId) === this.selectedFrameworkId);
      return framework?.name || framework?.FrameworkName || 'Framework';
    },
    
    async loadFrameworkControls() {
      if (!this.selectedFrameworkId) {
        this.frameworkControls = [];
        this.statistics = null;
        this.selectedCompliance = null;
        this.selectedSubPolicy = null;
        this.selectedPolicy = null;
        return;
      }
      
      this.isLoading = true;
      this.expandedPolicies = [];
      this.expandedSubPolicies = [];
      this.selectedCompliance = null;
      this.selectedSubPolicy = null;
      this.selectedPolicy = null;
      this.controlText = '';
      this.selectedFile = null;
      this.searchQuery = '';
      this.searchResultsCount = 0;
      
      try {
        const [controlsRes, statsRes] = await Promise.all([
          axiosInstance.get(`/api/organizational-controls/framework/${this.selectedFrameworkId}/`),
          axiosInstance.get(`/api/organizational-controls/statistics/${this.selectedFrameworkId}/`)
        ]);
        
        if (controlsRes.data.success) {
          this.frameworkControls = controlsRes.data.controls;
          // Auto-expand first policy
          if (this.frameworkControls.length > 0) {
            this.expandedPolicies.push(this.frameworkControls[0].PolicyId);
            // Also expand first subpolicy
            if (this.frameworkControls[0].SubPolicies?.length > 0) {
              this.expandedSubPolicies.push(this.frameworkControls[0].SubPolicies[0].SubPolicyId);
            }
          }
        }
        
        if (statsRes.data.success) {
          this.statistics = statsRes.data.statistics;
        }
      } catch (error) {
        console.error('Error loading framework controls:', error);
        this.showToast('Error loading framework controls', 'error');
      } finally {
        this.isLoading = false;
      }
    },
    
    selectControl(compliance, subpolicy, policy) {
      this.selectedCompliance = compliance;
      this.selectedSubPolicy = subpolicy;
      this.selectedPolicy = policy;
      this.controlText = compliance.ControlText || '';
      this.selectedFile = null;
      // Clear bulk audit results when selecting a specific compliance
      if (this.auditTargetType === 'compliance') {
        this.auditResults = null;
        this.auditTargetType = null;
      }
      // Load documents for this compliance
      this.loadComplianceDocuments(compliance.ComplianceId);
    },
    
    async loadComplianceDocuments(complianceId) {
      // For now, use existing document if available
      // TODO: In future, fetch documents from API using complianceId
      console.log('Loading documents for compliance:', complianceId);
      this.uploadedDocuments = [];
      // Load documents from API response (Documents array from backend)
      if (this.selectedCompliance?.Documents && Array.isArray(this.selectedCompliance.Documents)) {
        this.uploadedDocuments = this.selectedCompliance.Documents.map(doc => ({
          name: doc.DocumentName,
          DocumentName: doc.DocumentName,
          DocumentId: doc.DocumentId,
          DocumentPath: doc.DocumentPath,
          DocumentType: doc.DocumentType,
          FileSize: doc.FileSize,
          IsPrimary: doc.IsPrimary,
          uploadedAt: doc.UploadedAt ? new Date(doc.UploadedAt) : new Date()
        }));
      } else if (this.selectedCompliance?.DocumentName) {
        // Fallback for backward compatibility
        this.uploadedDocuments.push({
          name: this.selectedCompliance.DocumentName,
          DocumentName: this.selectedCompliance.DocumentName,
          uploadedAt: new Date()
        });
      }
    },
    
    formatMappingStatus(status) {
      const statusMap = {
        'fully_mapped': 'Fully Mapped',
        'partially_mapped': 'Partially Mapped',
        'not_mapped': 'Not Mapped',
        'not_audited': 'Not Audited'
      };
      return statusMap[status] || status;
    },
    
    getMappingStatusIcon(status) {
      const iconMap = {
        'fully_mapped': 'fas fa-check-circle',
        'partially_mapped': 'fas fa-exclamation-circle',
        'not_mapped': 'fas fa-times-circle',
        'not_audited': 'fas fa-clock'
      };
      return iconMap[status] || 'fas fa-question-circle';
    },
    
    getConfidenceClass(score) {
      if (score >= 80) return 'high';
      if (score >= 50) return 'medium';
      return 'low';
    },
    
    getComplianceCount(policy) {
      let count = 0;
      if (policy.SubPolicies) {
        policy.SubPolicies.forEach(sp => {
          count += sp.Compliances?.length || 0;
        });
      }
      return count;
    },
    
    getTotalSubPoliciesCount() {
      let total = 0;
      this.frameworkControls.forEach(policy => {
        total += (policy.SubPolicies?.length || 0);
      });
      return total;
    },
    
    getTotalControlsCount() {
      let total = 0;
      this.frameworkControls.forEach(policy => {
        total += this.getComplianceCount(policy);
      });
      return total;
    },
    
    getSubPoliciesForPolicy(policyId) {
      const policy = this.frameworkControls.find(p => p.PolicyId === policyId);
      return policy?.SubPolicies || [];
    },
    
    togglePolicy(policyId) {
      const index = this.expandedPolicies.indexOf(policyId);
      if (index > -1) {
        this.expandedPolicies.splice(index, 1);
      } else {
        this.expandedPolicies.push(policyId);
      }
    },
    
    toggleSubPolicy(subPolicyId) {
      const index = this.expandedSubPolicies.indexOf(subPolicyId);
      if (index > -1) {
        this.expandedSubPolicies.splice(index, 1);
      } else {
        this.expandedSubPolicies.push(subPolicyId);
      }
    },
    
    toggleFramework() {
      this.expandedFramework = !this.expandedFramework;
    },
    
    getSelectedFrameworkId() {
      if (!this.selectedFrameworkId) return '';
      // Try to get identifier from framework data, or use a shortened version of the ID
      const framework = this.frameworks.find(f => (f.id || f.FrameworkId) === this.selectedFrameworkId);
      return framework?.identifier || framework?.code || this.selectedFrameworkId.toString().substring(0, 8).toUpperCase();
    },
    
    isFrameworkMatch() {
      const query = this.searchQuery.toLowerCase().trim();
      if (!query) return false;
      const name = this.getSelectedFrameworkName().toLowerCase();
      const id = this.getSelectedFrameworkId().toLowerCase();
      return name.includes(query) || id.includes(query);
    },
    
    triggerFileInput() {
      this.$refs.fileInput.click();
    },
    
    handleFileSelect(event) {
      this.selectedFile = event.target.files[0];
    },
    
    clearFile() {
      this.selectedFile = null;
      if (this.$refs.fileInput) {
        this.$refs.fileInput.value = '';
      }
    },
    
    triggerBulkFileInput() {
      this.$refs.bulkFileInput.click();
    },
    
    handleBulkFileSelect(event) {
      this.bulkFile = event.target.files[0];
    },
    
    handleBulkFileDrop(event) {
      const files = event.dataTransfer.files;
      if (files.length > 0) {
        this.bulkFile = files[0];
      }
    },
    
    clearBulkFile() {
      this.bulkFile = null;
      if (this.$refs.bulkFileInput) {
        this.$refs.bulkFileInput.value = '';
      }
    },
    
    async saveControl() {
      if (!this.controlText && !this.selectedFile) {
        this.showToast('Please enter control text or upload a document', 'error');
        return;
      }
      
      this.isSaving = true;
      try {
        if (this.selectedFile) {
          const formData = new FormData();
          formData.append('file', this.selectedFile);
          formData.append('framework_id', this.selectedFrameworkId);
          formData.append('compliance_ids', this.selectedCompliance.ComplianceId);
          formData.append('upload_type', 'single');
          
          await axiosInstance.post('/api/organizational-controls/upload/', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
            timeout: 0 // No timeout - uploads can take time
          });
        } else {
          await axiosInstance.post('/api/organizational-controls/save/', {
            compliance_id: this.selectedCompliance.ComplianceId,
            control_text: this.controlText,
            framework_id: this.selectedFrameworkId
          });
        }
        
        this.showToast('Organizational control saved successfully', 'success');
        await this.loadFrameworkControls();
        // Re-select the control to refresh its data
        this.reselectCurrentControl();
      } catch (error) {
        console.error('Error saving control:', error);
        this.showToast('Error saving control: ' + (error.response?.data?.error || error.message), 'error');
      } finally {
        this.isSaving = false;
      }
    },
    
    async saveAndAudit() {
      if (!this.controlText && !this.selectedFile) {
        this.showToast('Please enter control text or upload a document', 'error');
        return;
      }
      
      this.isSaving = true;
      const complianceId = this.selectedCompliance?.ComplianceId;
      
      try {
        if (this.selectedFile) {
          const formData = new FormData();
          formData.append('file', this.selectedFile);
          formData.append('framework_id', this.selectedFrameworkId);
          formData.append('compliance_ids', complianceId);
          formData.append('upload_type', 'single');
          
          await axiosInstance.post('/api/organizational-controls/upload/', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
            timeout: 0 // No timeout - uploads can take time
          });
        } else {
          await axiosInstance.post('/api/organizational-controls/save/', {
            compliance_id: complianceId,
            control_text: this.controlText,
            framework_id: this.selectedFrameworkId
          });
        }
        
        const auditResponse = await axiosInstance.post('/api/organizational-controls/run-audit/', {
          compliance_id: complianceId
        }, {
          timeout: 0 // No timeout - AI audit can take as long as needed
        });
        
        if (auditResponse.data.success) {
          const result = auditResponse.data.results[0];
          if (result?.status === 'success') {
            this.showToast(`AI Audit complete: ${this.formatMappingStatus(result.mapping_status)}`, 'success');
          } else {
            this.showToast('Control saved. AI Audit completed.', 'success');
          }
        }
        
        await this.loadFrameworkControls();
        this.reselectCurrentControl();
      } catch (error) {
        console.error('Error:', error);
        this.showToast('Error: ' + (error.response?.data?.error || error.message), 'error');
      } finally {
        this.isSaving = false;
      }
    },
    
    async runSingleAudit(compliance) {
      this.auditingComplianceId = compliance.ComplianceId;
      
      try {
        const response = await axiosInstance.post('/api/organizational-controls/run-audit/', {
          compliance_id: compliance.ComplianceId
        }, {
          timeout: 0 // No timeout - AI audit can take as long as needed
        });
        
        if (response.data.success) {
          const result = response.data.results[0];
          if (result?.status === 'success') {
            // Update selectedCompliance with new results without refreshing
            if (this.selectedCompliance && this.selectedCompliance.ComplianceId === compliance.ComplianceId) {
              this.selectedCompliance.MappingStatus = result.mapping_status;
              this.selectedCompliance.ConfidenceScore = result.confidence_score;
            }
            this.showToast(`AI Audit complete: ${this.formatMappingStatus(result.mapping_status)}`, 'success');
          } else {
            this.showToast(result?.message || 'Audit completed', 'success');
          }
        }
        
        // Don't auto-refresh - user will click Save Results if needed
        // await this.loadFrameworkControls();
        // this.reselectCurrentControl();
      } catch (error) {
        console.error('Error running audit:', error);
        this.showToast('Error running audit', 'error');
      } finally {
        this.auditingComplianceId = null;
      }
    },
    
    async uploadBulkDocument() {
      if (!this.bulkFile) return;
      
      this.isUploading = true;
      try {
        const formData = new FormData();
        formData.append('file', this.bulkFile);
        formData.append('framework_id', this.selectedFrameworkId);
        formData.append('upload_type', this.bulkUploadType);
        
        if (this.bulkUploadType === 'policy') {
          formData.append('policy_id', this.selectedBulkPolicyId);
        } else if (this.bulkUploadType === 'subpolicy') {
          formData.append('subpolicy_id', this.selectedBulkSubPolicyId);
        }
        
        const response = await axiosInstance.post('/api/organizational-controls/upload/', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
          timeout: 0 // No timeout - uploads can take time
        });
        
        if (response.data.success) {
          this.showToast(response.data.message || 'Document uploaded successfully', 'success');
        }
        
        this.showBulkUploadModal = false;
        this.bulkFile = null;
        this.bulkUploadType = 'bulk';
        this.selectedBulkPolicyId = '';
        this.selectedBulkSubPolicyId = '';
        await this.loadFrameworkControls();
      } catch (error) {
        console.error('Error uploading bulk document:', error);
        this.showToast('Error uploading document: ' + (error.response?.data?.error || error.message), 'error');
      } finally {
        this.isUploading = false;
      }
    },
    
    // ═══════════════════════════════════════════════════════════════════════════
    // NEW UPLOAD MODAL METHODS
    // ═══════════════════════════════════════════════════════════════════════════
    
    openUploadModal(type, item, policy = null, subpolicy = null) {
      // Set selected compliance only for right panel display (not for middle panel)
      if (type === 'compliance') {
        this.selectedCompliance = item;
        this.selectedSubPolicy = subpolicy;
        this.selectedPolicy = policy;
      }
      
      this.uploadTarget = {
        type: type,
        id: type === 'policy' ? item.PolicyId : type === 'subpolicy' ? item.SubPolicyId : item.ComplianceId,
        identifier: item.Identifier || '',
        name: type === 'policy' ? item.PolicyName : type === 'subpolicy' ? item.SubPolicyName : item.ComplianceTitle,
        policyId: policy?.PolicyId || null,
        subPolicyId: subpolicy?.SubPolicyId || null
      };
      this.uploadMode = type === 'compliance' ? 'single' : 'single';
      this.uploadFiles = [];
      this.dragOver = false;
      this.showUploadInterface = true;
    },
    
    openFrameworkUpload() {
      const selectedFramework = this.frameworks.find(f => (f.id || f.FrameworkId) === this.selectedFrameworkId);
      this.uploadTarget = {
        type: 'framework',
        id: this.selectedFrameworkId,
        identifier: '',
        name: selectedFramework?.name || selectedFramework?.FrameworkName || 'Framework',
        policyId: null,
        subPolicyId: null
      };
      this.uploadMode = 'bulk';
      this.uploadFiles = [];
      this.dragOver = false;
      this.showUploadInterface = true;
    },
    
    closeUploadInterface() {
      this.showUploadInterface = false;
      this.uploadFiles = [];
      this.uploadTarget = { type: '', id: null, identifier: '', name: '', policyId: null, subPolicyId: null };
      this.uploadMode = 'single';
      this.dragOver = false;
      this.filesUploadedSuccessfully = false;
    },
    
    getTargetIcon(type) {
      const icons = {
        'policy': 'fas fa-folder',
        'subpolicy': 'fas fa-folder-open',
        'compliance': 'fas fa-file-alt',
        'framework': 'fas fa-layer-group'
      };
      return icons[type] || 'fas fa-file';
    },
    
    triggerUploadInput() {
      this.$refs.uploadInput?.click();
    },
    
    handleUploadFileSelect(event) {
      const files = Array.from(event.target.files);
      this.addFilesToUpload(files);
      event.target.value = '';
    },
    
    handleFileDrop(event) {
      this.dragOver = false;
      const files = Array.from(event.dataTransfer.files);
      this.addFilesToUpload(files);
    },
    
    addFilesToUpload(files) {
      const allowedTypes = ['.pdf', '.docx', '.doc', '.txt', '.xlsx', '.xls', '.pptx', '.ppt'];
      // No limit for bulk upload, 10 for multiple, 1 for single
      const maxFiles = this.uploadMode === 'single' ? 1 : this.uploadMode === 'bulk' ? null : 10;
      
      for (const file of files) {
        // Only check limit if maxFiles is not null (bulk has no limit)
        if (maxFiles !== null && this.uploadFiles.length >= maxFiles) {
          this.showToast(`Maximum ${maxFiles} file(s) allowed`, 'error');
          break;
        }
        
        const ext = '.' + file.name.split('.').pop().toLowerCase();
        if (!allowedTypes.includes(ext)) {
          this.showToast(`File type ${ext} not supported`, 'error');
          continue;
        }
        
        // Check for duplicates
        if (this.uploadFiles.some(f => (f.file || f).name === file.name)) {
          continue;
        }
        
        // Store file with progress tracking
        const fileWithProgress = {
          file: file,
          name: file.name,
          size: file.size,
          progress: 0,
          status: 'pending' // pending, uploading, completed, error
        };
        
        if (this.uploadMode === 'single') {
          this.uploadFiles = [fileWithProgress];
        } else {
          this.uploadFiles.push(fileWithProgress);
        }
      }
    },
    
    removeUploadFile(index) {
      this.uploadFiles.splice(index, 1);
    },
    
    async processUpload() {
      if (this.uploadFiles.length === 0) return;
      
      this.isUploading = true;
      
      // Reset all files to pending status
      this.uploadFiles.forEach(fileObj => {
        fileObj.status = 'pending';
        fileObj.progress = 0;
      });
      
      try {
        // Upload files one by one sequentially
        for (let i = 0; i < this.uploadFiles.length; i++) {
          const fileObj = this.uploadFiles[i];
          
          // Set current file to uploading
          fileObj.status = 'uploading';
          fileObj.progress = 0;
          
          const formData = new FormData();
          
          // Add single file
          formData.append('files', fileObj.file);
          
          // Add target info
          formData.append('framework_id', this.selectedFrameworkId);
          formData.append('upload_type', this.uploadTarget.type);
          formData.append('upload_mode', this.uploadMode);
          
          if (this.uploadTarget.type === 'policy') {
            formData.append('policy_id', this.uploadTarget.id);
          } else if (this.uploadTarget.type === 'subpolicy') {
            formData.append('subpolicy_id', this.uploadTarget.id);
            formData.append('policy_id', this.uploadTarget.policyId);
          } else if (this.uploadTarget.type === 'compliance') {
            formData.append('compliance_id', this.uploadTarget.id);
          }
          
          try {
            const response = await axiosInstance.post('/api/organizational-controls/upload/', formData, {
              headers: { 'Content-Type': 'multipart/form-data' },
              timeout: 0, // No timeout - uploads can take time
              onUploadProgress: (progressEvent) => {
                if (progressEvent.total) {
                  // Update progress for current file only
                  fileObj.progress = Math.round((progressEvent.loaded / progressEvent.total) * 100);
                }
              }
            });
            
            if (response.data.success) {
              // Mark current file as completed
              fileObj.status = 'completed';
              fileObj.progress = 100;
            } else {
              fileObj.status = 'error';
            }
          } catch (fileError) {
            // Mark current file as error
            fileObj.status = 'error';
            console.error(`Error uploading file ${fileObj.name}:`, fileError);
          }
        }
        
        // Check if all files completed successfully
        const allCompleted = this.uploadFiles.every(fileObj => fileObj.status === 'completed');
        const errorCount = this.uploadFiles.filter(fileObj => fileObj.status === 'error').length;
        
        if (allCompleted) {
          this.showToast(`${this.uploadFiles.length} document(s) uploaded successfully`, 'success');
          
          // Add to local documents list
          for (const fileObj of this.uploadFiles) {
            this.uploadedDocuments.push({
              name: fileObj.name,
              size: fileObj.size,
              uploadedAt: new Date()
            });
          }
          
          // Set flag to show Run AI Audit button
          this.filesUploadedSuccessfully = true;
        } else if (errorCount > 0) {
          this.showToast(`${errorCount} file(s) failed to upload`, 'error');
        }
        
        // Don't close interface immediately - let user run AI audit
        await this.loadFrameworkControls();
        if (this.uploadTarget.type === 'compliance') {
          this.reselectCurrentControl();
        }
      } catch (error) {
        console.error('Error uploading documents:', error);
        // Mark all files as error
        this.uploadFiles.forEach(fileObj => {
          fileObj.status = 'error';
        });
        this.showToast('Error uploading: ' + (error.response?.data?.error || error.message), 'error');
      } finally {
        this.isUploading = false;
      }
    },
    
    getDocumentIcon(filename) {
      if (!filename) return 'fas fa-file';
      const ext = filename.split('.').pop().toLowerCase();
      const icons = {
        'pdf': 'fas fa-file-pdf',
        'doc': 'fas fa-file-word',
        'docx': 'fas fa-file-word',
        'xls': 'fas fa-file-excel',
        'xlsx': 'fas fa-file-excel',
        'ppt': 'fas fa-file-powerpoint',
        'pptx': 'fas fa-file-powerpoint',
        'txt': 'fas fa-file-alt'
      };
      return icons[ext] || 'fas fa-file';
    },
    
    formatFileSize(bytes) {
      if (!bytes) return '';
      if (bytes < 1024) return bytes + ' B';
      if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
      return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    },
    
    formatDate(date) {
      if (!date) return '';
      return new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    },
    
    viewDocument(doc) {
      // Placeholder for document viewing
      this.showToast('Opening document: ' + (doc.name || doc.DocumentName), 'success');
    },
    
    removeDocument(index) {
      this.uploadedDocuments.splice(index, 1);
      this.showToast('Document removed', 'success');
    },
    
    async runAIAudit() {
      if (!this.selectedCompliance) return;
      
      this.isAuditing = true;
      try {
        // First save if there's text
        if (this.controlText) {
          await axiosInstance.post('/api/organizational-controls/save/', {
            compliance_id: this.selectedCompliance.ComplianceId,
            control_text: this.controlText,
            framework_id: this.selectedFrameworkId
          });
        }
        
        // Run audit
        const response = await axiosInstance.post('/api/organizational-controls/run-audit/', {
          compliance_id: this.selectedCompliance.ComplianceId
        }, {
          timeout: 0 // No timeout - AI audit can take as long as needed
        });
        
        if (response.data.success) {
          const result = response.data.results[0];
          if (result?.status === 'success') {
            this.showToast(`AI Audit complete: ${this.formatMappingStatus(result.mapping_status)}`, 'success');
          } else {
            this.showToast('AI Audit completed', 'success');
          }
        }
        
        await this.loadFrameworkControls();
        this.reselectCurrentControl();
      } catch (error) {
        console.error('Error running AI audit:', error);
        this.showToast('Error running audit: ' + (error.response?.data?.error || error.message), 'error');
      } finally {
        this.isAuditing = false;
      }
    },
    
    async runAIAuditAfterUpload() {
      this.isAuditing = true;
      this.auditProgress = 0;
      
      // Simulate progress (gradually increase to 90%, then jump to 100% on completion)
      const progressInterval = setInterval(() => {
        if (this.auditProgress < 90) {
          this.auditProgress += 2; // Increase by 2% every interval
        }
      }, 500); // Update every 500ms
      
      try {
        let response;
        const auditParams = {
          framework_id: this.selectedFrameworkId
        };
        
        // Handle different upload types
        if (this.uploadTarget.type === 'compliance') {
          // Run audit for specific compliance
          auditParams.compliance_id = this.uploadTarget.id;
        } else if (this.uploadTarget.type === 'policy') {
          // Run audit for all compliances under this policy
          auditParams.policy_id = this.uploadTarget.id;
        } else if (this.uploadTarget.type === 'subpolicy') {
          // Run audit for all compliances under this subpolicy
          auditParams.subpolicy_id = this.uploadTarget.id;
        } else if (this.uploadTarget.type === 'framework') {
          // Run audit for all compliances in framework
          auditParams.audit_all = true;
        }
        
        response = await axiosInstance.post('/api/organizational-controls/run-audit/', auditParams, {
          timeout: 0 // No timeout - AI audit can take as long as needed
        });
        
        // Clear progress interval and set to 100%
        clearInterval(progressInterval);
        this.auditProgress = 100;
        
        if (response.data.success) {
          // Store audit results for display
          this.auditResults = response.data.results || [];
          this.auditTargetType = this.uploadTarget.type;
          
          const summary = response.data.summary;
          if (this.uploadTarget.type === 'compliance' && response.data.results.length > 0) {
            // Single compliance result - update selectedCompliance if it matches
            const result = response.data.results[0];
            if (result?.status === 'success') {
              if (this.selectedCompliance && this.selectedCompliance.ComplianceId === this.uploadTarget.id) {
                this.selectedCompliance.MappingStatus = result.mapping_status;
                this.selectedCompliance.ConfidenceScore = result.confidence_score;
              }
              this.showToast(`AI Audit complete: ${this.formatMappingStatus(result.mapping_status)}`, 'success');
            } else {
              this.showToast('AI Audit completed', 'success');
            }
          } else {
            // Bulk audit results
            this.showToast(
              `AI Audit completed! Total: ${summary.total}, Fully Mapped: ${summary.fully_mapped}, Partially: ${summary.partially_mapped}, Not Mapped: ${summary.not_mapped}`,
              'success'
            );
          }
          
          // Close upload interface but don't refresh yet - show results first
          this.closeUploadInterface();
        }
      } catch (error) {
        clearInterval(progressInterval);
        this.auditProgress = 0;
        console.error('Error running AI audit:', error);
        this.showToast('Error running audit: ' + (error.response?.data?.error || error.message), 'error');
      } finally {
        this.isAuditing = false;
        // Reset progress after a short delay to show completion
        setTimeout(() => {
          if (this.auditProgress === 100) {
            this.auditProgress = 0;
          }
        }, 2000);
      }
    },
    
    async saveAndRefreshResults() {
      this.isSaving = true;
      try {
        // Refresh framework controls to get latest saved data
        await this.loadFrameworkControls();
        
        // If we have a selected compliance, re-select it to show updated data
        if (this.selectedCompliance) {
          this.reselectCurrentControl();
        }
        
        // Clear audit results after refresh
        this.auditResults = null;
        this.auditTargetType = null;
        
        this.showToast('Results saved and refreshed successfully', 'success');
      } catch (error) {
        console.error('Error saving results:', error);
        this.showToast('Error saving results: ' + (error.response?.data?.error || error.message), 'error');
      } finally {
        this.isSaving = false;
      }
    },
    
    async runBulkAudit() {
      this.isAuditing = true;
      try {
        const response = await axiosInstance.post('/api/organizational-controls/run-audit/', {
          framework_id: this.selectedFrameworkId,
          audit_all: true
        }, {
          timeout: 0 // No timeout - AI audit can take as long as needed
        });
        
        if (response.data.success) {
          const summary = response.data.summary;
          this.showToast(
            `AI Audit completed! Fully Mapped: ${summary.fully_mapped}, Partially: ${summary.partially_mapped}, Not Mapped: ${summary.not_mapped}`,
            'success'
          );
        }
        
        await this.loadFrameworkControls();
        this.reselectCurrentControl();
      } catch (error) {
        console.error('Error running bulk audit:', error);
        this.showToast('Error running audit: ' + (error.response?.data?.error || error.message), 'error');
      } finally {
        this.isAuditing = false;
      }
    },
    
    reselectCurrentControl() {
      if (!this.selectedCompliance) return;
      
      const complianceId = this.selectedCompliance.ComplianceId;
      
      // Find the control in the updated data
      for (const policy of this.frameworkControls) {
        for (const subpolicy of policy.SubPolicies || []) {
          for (const compliance of subpolicy.Compliances || []) {
            if (compliance.ComplianceId === complianceId) {
              this.selectedCompliance = compliance;
              this.selectedSubPolicy = subpolicy;
              this.selectedPolicy = policy;
              this.controlText = compliance.ControlText || '';
              return;
            }
          }
        }
      }
    },
    
    showToast(message, type = 'success') {
      this.toast = { show: true, message, type };
      setTimeout(() => {
        this.toast.show = false;
      }, 4000);
    },
    
    // Search Methods
    handleSearch() {
      if (this.searchQuery.trim()) {
        // Auto-expand matching items
        this.expandMatchingItems();
        // Count results
        this.countSearchResults();
      } else {
        this.searchResultsCount = 0;
      }
    },
    
    clearSearch() {
      this.searchQuery = '';
      this.searchResultsCount = 0;
    },
    
    countSearchResults() {
      let count = 0;
      const query = this.searchQuery.toLowerCase().trim();
      
      if (!query) {
        this.searchResultsCount = 0;
        return;
      }
      
      for (const policy of this.frameworkControls) {
        if (this.isPolicyMatch(policy)) count++;
        
        for (const subpolicy of (policy.SubPolicies || [])) {
          if (this.isSubPolicyMatch(subpolicy)) count++;
          
          for (const compliance of (subpolicy.Compliances || [])) {
            if (this.isComplianceMatch(compliance)) count++;
          }
        }
      }
      
      this.searchResultsCount = count;
    },
    
    expandMatchingItems() {
      const query = this.searchQuery.toLowerCase().trim();
      if (!query) return;
      
      const policiesToExpand = [];
      const subPoliciesToExpand = [];
      
      for (const policy of this.frameworkControls) {
        let shouldExpandPolicy = false;
        
        for (const subpolicy of (policy.SubPolicies || [])) {
          let shouldExpandSubPolicy = false;
          
          for (const compliance of (subpolicy.Compliances || [])) {
            if (this.isComplianceMatch(compliance)) {
              shouldExpandSubPolicy = true;
              shouldExpandPolicy = true;
              break;
            }
          }
          
          if (this.isSubPolicyMatch(subpolicy)) {
            shouldExpandPolicy = true;
            shouldExpandSubPolicy = true;
          }
          
          if (shouldExpandSubPolicy && !subPoliciesToExpand.includes(subpolicy.SubPolicyId)) {
            subPoliciesToExpand.push(subpolicy.SubPolicyId);
          }
        }
        
        if (this.isPolicyMatch(policy) || shouldExpandPolicy) {
          if (!policiesToExpand.includes(policy.PolicyId)) {
            policiesToExpand.push(policy.PolicyId);
          }
        }
      }
      
      // Add new expansions without removing existing ones
      for (const id of policiesToExpand) {
        if (!this.expandedPolicies.includes(id)) {
          this.expandedPolicies.push(id);
        }
      }
      
      for (const id of subPoliciesToExpand) {
        if (!this.expandedSubPolicies.includes(id)) {
          this.expandedSubPolicies.push(id);
        }
      }
    },
    
    isPolicyMatch(policy) {
      const query = this.searchQuery.toLowerCase().trim();
      if (!query) return false;
      
      const identifier = (policy.Identifier || '').toLowerCase();
      const name = (policy.PolicyName || '').toLowerCase();
      
      return identifier.includes(query) || name.includes(query);
    },
    
    isSubPolicyMatch(subpolicy) {
      const query = this.searchQuery.toLowerCase().trim();
      if (!query) return false;
      
      const identifier = (subpolicy.Identifier || '').toLowerCase();
      const name = (subpolicy.SubPolicyName || '').toLowerCase();
      
      return identifier.includes(query) || name.includes(query);
    },
    
    isComplianceMatch(compliance) {
      const query = this.searchQuery.toLowerCase().trim();
      if (!query) return false;
      
      const identifier = (compliance.Identifier || '').toLowerCase();
      const title = (compliance.ComplianceTitle || '').toLowerCase();
      const description = (compliance.ComplianceItemDescription || '').toLowerCase();
      
      return identifier.includes(query) || title.includes(query) || description.includes(query);
    },
    
    highlightText(text) {
      if (!text || !this.searchQuery.trim()) return text;
      
      const query = this.searchQuery.trim();
      const regex = new RegExp(`(${this.escapeRegExp(query)})`, 'gi');
      
      return text.replace(regex, '<mark class="search-highlight">$1</mark>');
    },
    
    escapeRegExp(string) {
      return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    },
    
    getFilteredSubPolicies(policy) {
      if (!this.searchQuery.trim()) {
        return policy.SubPolicies || [];
      }
      return policy._filteredSubPolicies || policy.SubPolicies || [];
    },
    
    getFilteredCompliances(subpolicy) {
      if (!this.searchQuery.trim()) {
        return subpolicy.Compliances || [];
      }
      return subpolicy._filteredCompliances || subpolicy.Compliances || [];
    },
    
    getFilteredComplianceCount(policy) {
      if (!this.searchQuery.trim()) {
        return this.getComplianceCount(policy);
      }
      
      let count = 0;
      const subPolicies = this.getFilteredSubPolicies(policy);
      for (const sp of subPolicies) {
        count += this.getFilteredCompliances(sp).length;
      }
      return count;
    },
    
    getAIAnalysisField(fieldName) {
      if (!this.selectedCompliance) return null;
      
      // Support both direct field access (backward compatibility) and AIAnalysis JSON
      if (this.selectedCompliance[fieldName]) {
        return this.selectedCompliance[fieldName];
      }
      
      if (this.selectedCompliance.AIAnalysis && typeof this.selectedCompliance.AIAnalysis === 'object') {
        return this.selectedCompliance.AIAnalysis[fieldName] || null;
      }
      
      return null;
    }
  }
};
</script>

<style scoped>
/* ═══════════════════════════════════════════════════════════════════════════ */
/* BASE STYLES - LIGHT THEME */
/* ═══════════════════════════════════════════════════════════════════════════ */
.organizational-controls {
  padding: 16px 20px;
  margin-left: 250px;
  width: calc(100% - 250px);
  height: calc(100vh - 60px);
  max-height: calc(100vh - 60px);
  box-sizing: border-box;
  background: #f1f5f9;
  color: #475569;
  font-family: 'Segoe UI', system-ui, sans-serif;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Page Header */
.page-header {
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}

.page-header h1 {
  font-size: 1.5rem;
  color: #1e293b;
  margin: 0;
  font-weight: 600;
}

.subtitle {
  color: #64748b;
  font-size: 0.85rem;
  margin: 0;
}


/* ═══════════════════════════════════════════════════════════════════════════ */
/* THREE PANEL SPLIT SCREEN */
/* ═══════════════════════════════════════════════════════════════════════════ */
.split-screen-container {
  display: grid;
  grid-template-columns: 520px 1fr 340px;
  gap: 16px;
  flex: 1;
  min-height: 0;
  height: calc(100vh - 140px);
  max-height: calc(100vh - 140px);
}

.panel {
  background: #ffffff;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  display: flex !important;
  flex-direction: column !important;
  overflow: hidden !important;
  gap: 0 !important;
  position: relative !important;
  justify-content: flex-start !important;
  align-items: stretch !important;
  height: 100% !important;
  max-height: 100% !important;
}

.panel-header {
  display: flex !important;
  align-items: center !important;
  justify-content: space-between !important;
  padding: 14px 16px !important;
  margin: 0 !important;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-bottom: 1px solid #e2e8f0;
  position: static !important;
  flex: 0 0 auto !important;
  flex-grow: 0 !important;
  flex-shrink: 0 !important;
  order: 0 !important;
  height: auto !important;
  min-height: auto !important;
  max-height: fit-content !important;
  top: auto !important;
  left: auto !important;
  right: auto !important;
  bottom: auto !important;
  transform: none !important;
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 600;
  color: #1e293b;
  font-size: 0.95rem;
}

.panel-title i {
  color: #3b82f6;
  font-size: 1rem;
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/* PANEL LEFT - FRAMEWORK HIERARCHY */
/* ═══════════════════════════════════════════════════════════════════════════ */
.panel-left {
  min-width: 480px;
  display: flex !important;
  flex-direction: column !important;
  position: relative !important;
}

/* Reset all direct children of panel-left - prevent unwanted growth */
.panel-left > * {
  position: static !important;
  flex-grow: 0 !important;
  flex-shrink: 0 !important;
  width: 100% !important;
  box-sizing: border-box !important;
}

/* Only hierarchy-tree should grow to fill remaining space */
.panel-left > .hierarchy-tree {
  flex-grow: 1 !important;
  flex-shrink: 1 !important;
}

.framework-selector {
  padding: 12px 16px !important;
  margin: 0 !important;
  border-bottom: 1px solid #e2e8f0;
  position: static !important;
  flex: 0 0 auto !important;
  flex-grow: 0 !important;
  flex-shrink: 0 !important;
  order: 1 !important;
  height: auto !important;
  min-height: auto !important;
  max-height: fit-content !important;
}

.framework-selector label {
  display: block;
  margin-bottom: 6px !important;
  margin-top: 0 !important;
  padding: 0 !important;
  color: #64748b;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  position: static !important;
}

.framework-selector select {
  width: 100%;
  padding: 10px 12px !important;
  margin: 0 !important;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  color: #334155;
  font-size: 0.9rem;
  cursor: pointer;
  position: static !important;
}

.framework-selector select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

/* Search Box */
.search-box {
  padding: 14px 16px !important;
  margin: 0 !important;
  border-bottom: 1px solid #e2e8f0;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  position: static !important;
  flex: 0 0 auto !important;
  flex-grow: 0 !important;
  flex-shrink: 0 !important;
  order: 2 !important;
  height: auto !important;
  min-height: auto !important;
  max-height: fit-content !important;
  top: auto !important;
  left: auto !important;
  right: auto !important;
  bottom: auto !important;
  transform: none !important;
}

.search-input-wrapper {
  position: relative !important;
  display: flex !important;
  align-items: center !important;
  margin: 0 !important;
  top: auto !important;
  left: auto !important;
  right: auto !important;
  bottom: auto !important;
  transform: none !important;
}

.search-icon {
  position: absolute !important;
  left: 14px !important;
  top: 50% !important;
  transform: translateY(-50%) !important;
  right: auto !important;
  bottom: auto !important;
  color: #64748b;
  font-size: 0.9rem;
  pointer-events: none;
  z-index: 1;
}

.search-input {
  width: 100% !important;
  padding: 12px 40px 12px 42px !important;
  margin: 0 !important;
  background: #ffffff;
  border: 2px solid #e2e8f0;
  border-radius: 10px;
  color: #1e293b;
  font-size: 0.9rem;
  font-weight: 500;
  transition: all 0.25s ease;
  position: static !important;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.search-input:hover {
  border-color: #cbd5e1;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
}

.search-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.12), 0 2px 8px rgba(59, 130, 246, 0.1);
  background: #fff;
}

.search-input::placeholder {
  color: #94a3b8;
  font-weight: 400;
}

.search-clear-btn {
  position: absolute !important;
  right: 10px !important;
  top: 50% !important;
  transform: translateY(-50%) !important;
  background: #ef4444;
  border: none;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #fff;
  font-size: 0.65rem;
  font-weight: 600;
  transition: all 0.2s;
  z-index: 1;
}

.search-clear-btn:hover {
  background: #dc2626;
  transform: translateY(-50%) scale(1.1);
}

.search-results-info {
  margin-top: 10px !important;
  margin-bottom: 0 !important;
  padding: 0 !important;
  font-size: 0.8rem;
  display: flex !important;
  align-items: center !important;
  gap: 8px;
  position: static !important;
}

.results-count {
  color: #059669;
  background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
  padding: 6px 12px;
  border-radius: 20px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  font-size: 0.8rem;
  border: 1px solid #a7f3d0;
  box-shadow: 0 1px 2px rgba(16, 185, 129, 0.1);
}

.results-count i {
  font-size: 0.75rem;
  color: #10b981;
}

.no-results {
  color: #d97706;
  background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
  padding: 6px 12px;
  border-radius: 20px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  font-size: 0.8rem;
  border: 1px solid #fde68a;
  box-shadow: 0 1px 2px rgba(245, 158, 11, 0.1);
}

.no-results i {
  font-size: 0.75rem;
  color: #f59e0b;
}

/* Search Highlight */
.search-highlight {
  background: linear-gradient(135deg, #fef08a 0%, #fde047 100%);
  color: #854d0e;
  padding: 0 2px;
  border-radius: 2px;
  font-weight: 600;
}

/* Search Match Styling */
.tree-item.search-match {
  background: #fffbeb;
  border-left-color: #f59e0b;
}

.tree-item.search-match:hover {
  background: #fef3c7;
}

/* Clear search button in empty state */
.btn-clear-search {
  margin-top: 12px;
  padding: 8px 16px;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  color: #64748b;
  font-size: 0.8rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
}

.btn-clear-search:hover {
  background: #e2e8f0;
  color: #334155;
}

.panel-loading {
  display: flex !important;
  flex-direction: column !important;
  align-items: center !important;
  justify-content: center !important;
  padding: 40px !important;
  margin: 0 !important;
  color: #64748b;
  position: static !important;
  flex: 1 1 auto !important;
  order: 3 !important;
  top: auto !important;
  left: auto !important;
  right: auto !important;
  bottom: auto !important;
  transform: none !important;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e2e8f0;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 12px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.hierarchy-tree {
  flex: 1 1 0 !important;
  overflow-y: auto !important;
  overflow-x: hidden !important;
  display: flex !important;
  flex-direction: column !important;
  margin: 0 !important;
  padding: 0 !important;
  position: static !important;
  order: 3 !important;
  min-height: 0 !important;
  top: auto !important;
  left: auto !important;
  right: auto !important;
  bottom: auto !important;
  transform: none !important;
}

.tree-stats {
  display: flex !important;
  gap: 12px;
  padding: 10px 16px !important;
  margin: 0 !important;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  position: static !important;
  flex: 0 0 auto !important;
  flex-grow: 0 !important;
  flex-shrink: 0 !important;
  height: auto !important;
  min-height: auto !important;
  max-height: fit-content !important;
  top: auto !important;
  left: auto !important;
  right: auto !important;
  bottom: auto !important;
  transform: none !important;
}

.tree-stat {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.75rem;
  color: #64748b;
  margin: 0 !important;
  position: static !important;
}

.tree-stat i {
  color: #94a3b8;
}

.tree-content {
  flex: 1 1 0 !important;
  overflow-y: auto !important;
  overflow-x: hidden !important;
  padding: 8px 0 !important;
  margin: 0 !important;
  position: static !important;
  min-height: 0 !important;
  top: auto !important;
  left: auto !important;
  right: auto !important;
  bottom: auto !important;
  transform: none !important;
}

/* Tree Items */
.tree-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px !important;
  margin: 0 !important;
  cursor: pointer;
  transition: all 0.15s;
  border-left: 3px solid transparent;
}

.tree-framework,
.tree-policy,
.tree-subpolicy {
  margin: 0 !important;
  padding: 0 !important;
}

.framework-item {
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border-left: 3px solid #3b82f6;
  font-weight: 500;
  padding: 8px 12px !important;
}

.framework-item:hover {
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
}

.framework-item .item-name {
  font-weight: 500;
  color: #1e40af;
  font-size: 0.8rem;
}

.tree-item:hover {
  background: #f8fafc;
}

.tree-item.selected {
  background: #eff6ff;
  border-left-color: #3b82f6;
}

.expand-icon {
  width: 16px;
  font-size: 0.7rem;
  color: #94a3b8;
  transition: transform 0.2s;
}

.item-icon {
  font-size: 0.85rem;
}

.framework-icon { 
  color: #3b82f6; 
  font-size: 0.75rem !important;
}
.policy-icon { color: #f59e0b; }
.subpolicy-icon { color: #8b5cf6; }
.control-icon { color: #64748b; }

.item-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.item-id {
  font-size: 0.7rem;
  color: #94a3b8;
  font-family: 'Consolas', monospace;
}

.item-name {
  font-size: 0.8rem;
  color: #334155;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.item-badge {
  background: #e2e8f0;
  color: #64748b;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 0.7rem;
  font-weight: 600;
}

/* Tree Children */
.tree-children {
  margin-left: 20px !important;
  margin-top: 0 !important;
  margin-bottom: 0 !important;
  margin-right: 0 !important;
  padding: 0 !important;
}

.tree-subpolicy .tree-children {
  margin-left: 16px !important;
}

/* Control Item States */
.control-item {
  padding-left: 24px;
}

.control-item .expand-icon {
  display: none;
}

.control-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #cbd5e1;
}

.control-status-dot.fully_mapped { background: #10b981; }
.control-status-dot.partially_mapped { background: #f59e0b; }
.control-status-dot.not_mapped { background: #ef4444; }
.control-status-dot.not_audited { background: #cbd5e1; }

.control-item.has-control .control-icon {
  color: #3b82f6;
}

.tree-empty, .panel-empty {
  display: flex !important;
  flex-direction: column !important;
  align-items: center !important;
  justify-content: center !important;
  padding: 40px 20px !important;
  margin: 0 !important;
  color: #94a3b8;
  text-align: center;
  flex: 1 1 0 !important;
  position: static !important;
  order: 3 !important;
  min-height: 0 !important;
  overflow-y: auto !important;
  top: auto !important;
  left: auto !important;
  right: auto !important;
  bottom: auto !important;
  transform: none !important;
}

/* Ensure panel-empty inside panel-left fills space */
.panel-left > .panel-empty {
  flex-grow: 1 !important;
  width: 100% !important;
  box-sizing: border-box !important;
}

.tree-empty i, .panel-empty i {
  font-size: 2.5rem;
  margin-bottom: 12px;
  color: #cbd5e1;
}

.panel-empty h3 {
  color: #475569;
  margin-bottom: 8px;
  font-size: 1rem;
}

.panel-empty p {
  font-size: 0.85rem;
  margin: 0;
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/* PANEL MIDDLE - ORGANIZATIONAL CONTROL */
/* ═══════════════════════════════════════════════════════════════════════════ */
.btn-bulk-upload {
  padding: 6px 12px;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  color: #64748b;
  cursor: pointer;
  font-size: 0.8rem;
  transition: all 0.2s;
}

.btn-bulk-upload:hover {
  background: #3b82f6;
  border-color: #3b82f6;
  color: #fff;
}

.btn-close-upload {
  padding: 6px 12px;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  color: #64748b;
  cursor: pointer;
  font-size: 0.8rem;
  transition: all 0.2s;
}

.btn-close-upload:hover {
  background: #ef4444;
  border-color: #ef4444;
  color: #fff;
}

/* Upload Interface */
.upload-interface {
  flex: 1 1 0 !important;
  overflow-y: auto !important;
  overflow-x: hidden !important;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-height: 0 !important;
}

.upload-target-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  flex-shrink: 0;
}

.upload-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex-shrink: 0;
  background: transparent;
  border: none;
  padding: 0;
  margin: 0;
  box-shadow: none;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.8rem;
  font-weight: 600;
  color: #334155;
  margin: 0;
}

.section-title i {
  color: #3b82f6;
  font-size: 0.75rem;
}

.upload-actions {
  display: flex;
  gap: 8px;
  margin-top: auto;
  padding-top: 10px;
  flex-shrink: 0;
}

.control-editor {
  flex: 1 1 0 !important;
  overflow-y: auto !important;
  overflow-x: hidden !important;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 0 !important;
}

.control-info-header {
  margin-bottom: 8px;
}

.control-breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.75rem;
  color: #94a3b8;
  margin-bottom: 8px;
}

.breadcrumb-item {
  padding: 2px 8px;
  background: #f1f5f9;
  border-radius: 4px;
}

.breadcrumb-item.active {
  background: #3b82f6;
  color: #fff;
}

.control-breadcrumb i {
  font-size: 0.6rem;
}

.control-info-header .control-title {
  font-size: 1.1rem;
  color: #1e293b;
  font-weight: 600;
  margin: 0;
}

/* Requirement Box */
.requirement-box {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 14px;
}

.requirement-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.75rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 10px;
}

.requirement-label i {
  color: #3b82f6;
}

.requirement-text {
  color: #334155;
  font-size: 0.9rem;
  line-height: 1.6;
  margin: 0;
}

.requirement-meta {
  display: flex;
  gap: 12px;
  margin-top: 12px;
  flex-wrap: wrap;
}

.meta-tag {
  font-size: 0.75rem;
  padding: 4px 10px;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  color: #475569;
}

/* Org Control Input */
.org-control-input {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.input-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.75rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.input-label i {
  color: #10b981;
}

.org-control-input textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  font-size: 0.9rem;
  font-family: inherit;
  resize: vertical;
  transition: all 0.2s;
  background: #fff;
}

.org-control-input textarea:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.input-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.char-count {
  font-size: 0.75rem;
  color: #94a3b8;
}

.btn-attach {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  color: #64748b;
  cursor: pointer;
  font-size: 0.8rem;
  transition: all 0.2s;
}

.btn-attach:hover {
  background: #e2e8f0;
  color: #334155;
}

.attached-file {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
  border-radius: 8px;
  color: #059669;
  font-size: 0.85rem;
}

.btn-remove-file {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #dc2626;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  cursor: pointer;
  font-size: 0.9rem;
  line-height: 1;
  margin-left: auto;
}

/* Existing Control */
.existing-control {
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  border-radius: 10px;
  padding: 14px;
}

.existing-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.75rem;
  font-weight: 600;
  color: #3b82f6;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 10px;
}

.existing-text {
  color: #334155;
  font-size: 0.85rem;
  line-height: 1.5;
  margin: 0;
}

.existing-document {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #fff;
  border-radius: 6px;
  color: #3b82f6;
  font-size: 0.85rem;
  margin-top: 8px;
}

/* Control Actions */
.control-actions {
  display: flex;
  gap: 10px;
  margin-top: auto;
  padding-top: 16px;
}

.btn-save, .btn-save-audit {
  flex: 1;
  padding: 12px 16px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.2s;
}

.btn-save {
  background: linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%);
  color: #fff;
}

.btn-save:hover:not(:disabled) {
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.btn-save-audit {
  background: linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%);
  color: #fff;
}

.btn-save-audit:hover:not(:disabled) {
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);
}

.btn-save:disabled, .btn-save-audit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Quick Actions */
.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 20px;
  width: 100%;
  max-width: 280px;
}

.btn-quick-action {
  padding: 12px 20px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  color: #475569;
  cursor: pointer;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  transition: all 0.2s;
}

.btn-quick-action:hover:not(:disabled) {
  background: #3b82f6;
  border-color: #3b82f6;
  color: #fff;
}

.btn-quick-action:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/* PANEL RIGHT - AI RESULTS */
/* ═══════════════════════════════════════════════════════════════════════════ */

/* Mapping Stats Grid */
.mapping-stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  padding: 14px;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
}

.mini-stat {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  background: #fff;
  border: 1px solid #e2e8f0;
}

.mini-stat i {
  font-size: 1.1rem;
}

.mini-stat-content {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.mini-stat-value {
  font-size: 1.1rem;
  font-weight: 700;
  line-height: 1.2;
}

.mini-stat-label {
  font-size: 0.7rem;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.mini-stat.fully-mapped {
  border-color: #a7f3d0;
  background: #ecfdf5;
}
.mini-stat.fully-mapped i { color: #10b981; }
.mini-stat.fully-mapped .mini-stat-value { color: #059669; }

.mini-stat.partially-mapped {
  border-color: #fde68a;
  background: #fffbeb;
}
.mini-stat.partially-mapped i { color: #f59e0b; }
.mini-stat.partially-mapped .mini-stat-value { color: #d97706; }

.mini-stat.not-mapped {
  border-color: #fecaca;
  background: #fef2f2;
}
.mini-stat.not-mapped i { color: #ef4444; }
.mini-stat.not-mapped .mini-stat-value { color: #dc2626; }

.mini-stat.coverage {
  border-color: #bfdbfe;
  background: #eff6ff;
}
.mini-stat.coverage i { color: #3b82f6; }
.mini-stat.coverage .mini-stat-value { color: #2563eb; }

.btn-run-audit {
  padding: 6px 12px;
  background: linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%);
  border: none;
  border-radius: 6px;
  color: #fff;
  cursor: pointer;
  font-size: 0.8rem;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
}

.btn-run-audit:hover:not(:disabled) {
  box-shadow: 0 2px 8px rgba(139, 92, 246, 0.3);
}

.btn-run-audit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.ai-results-container {
  flex: 1 1 0 !important;
  overflow-y: auto !important;
  overflow-x: hidden !important;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-height: 0 !important;
}

/* Mapping Status Card */
.mapping-status-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px;
  border-radius: 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}

.mapping-status-card.fully_mapped {
  background: #ecfdf5;
  border-color: #a7f3d0;
}

.mapping-status-card.partially_mapped {
  background: #fffbeb;
  border-color: #fde68a;
}

.mapping-status-card.not_mapped {
  background: #fef2f2;
  border-color: #fecaca;
}

.status-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
}

.mapping-status-card.fully_mapped .status-icon { background: #d1fae5; color: #059669; }
.mapping-status-card.partially_mapped .status-icon { background: #fef3c7; color: #d97706; }
.mapping-status-card.not_mapped .status-icon { background: #fee2e2; color: #dc2626; }
.mapping-status-card.not_audited .status-icon { background: #e2e8f0; color: #64748b; }

.status-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.status-label {
  font-size: 0.7rem;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.status-value {
  font-size: 0.95rem;
  font-weight: 600;
  color: #1e293b;
}

/* AI Results Details */
.ai-results-details {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.result-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 14px;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.8rem;
  font-weight: 600;
  color: #475569;
  margin-bottom: 10px;
}

.result-text {
  color: #334155;
  font-size: 0.85rem;
  line-height: 1.6;
  margin: 0;
}

/* Confidence Card */
.confidence-card .result-header i { color: #3b82f6; }

.confidence-display {
  display: flex;
  align-items: center;
  gap: 12px;
}

.confidence-bar {
  flex: 1;
  height: 8px;
  background: #e2e8f0;
  border-radius: 4px;
  overflow: hidden;
}

.confidence-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.5s ease;
}

.confidence-fill.high { background: linear-gradient(90deg, #10b981, #34d399); }
.confidence-fill.medium { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
.confidence-fill.low { background: linear-gradient(90deg, #ef4444, #f87171); }

.confidence-value {
  font-weight: 700;
  font-size: 1rem;
  min-width: 45px;
  text-align: right;
}

.confidence-value.high { color: #059669; }
.confidence-value.medium { color: #d97706; }
.confidence-value.low { color: #dc2626; }

/* Result Cards */
.satisfying-card { border-left: 4px solid #10b981; }
.satisfying-card .result-header i { color: #10b981; }

.missing-card { border-left: 4px solid #f59e0b; }
.missing-card .result-header i { color: #f59e0b; }

.not-mapped-card { border-left: 4px solid #ef4444; }
.not-mapped-card .result-header i { color: #ef4444; }

/* Not Audited State */
.not-audited-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  text-align: center;
  padding: 40px 20px;
}

.not-audited-icon {
  width: 60px;
  height: 60px;
  background: #f1f5f9;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.8rem;
  color: #94a3b8;
  margin-bottom: 16px;
}

.not-audited-state h4 {
  color: #475569;
  margin: 0 0 8px 0;
  font-size: 1rem;
}

.not-audited-state p {
  color: #94a3b8;
  margin: 0;
  font-size: 0.85rem;
}

/* Bulk Audit Results */
.bulk-audit-results {
  flex: 1 1 0 !important;
  overflow-y: auto !important;
  overflow-x: hidden !important;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-height: 0 !important;
}

.bulk-results-header {
  margin-bottom: 8px;
}

.bulk-results-header h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 1rem;
  color: #1e293b;
  margin: 0;
  font-weight: 600;
}

.bulk-results-header h3 i {
  color: #3b82f6;
}

.results-count {
  font-size: 0.85rem;
  color: #64748b;
  font-weight: 400;
}

.bulk-results-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.bulk-result-item {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 14px;
  transition: all 0.2s;
}

.bulk-result-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  border-color: #cbd5e1;
}

.bulk-result-item.fully_mapped {
  border-left: 4px solid #10b981;
  background: #f0fdf4;
}

.bulk-result-item.partially_mapped {
  border-left: 4px solid #f59e0b;
  background: #fffbeb;
}

.bulk-result-item.not_mapped {
  border-left: 4px solid #ef4444;
  background: #fef2f2;
}

.bulk-result-item.not_audited {
  border-left: 4px solid #cbd5e1;
  background: #f8fafc;
}

.result-item-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
  flex-wrap: wrap;
  gap: 8px;
}

.result-status-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 600;
}

.result-status-badge.fully_mapped {
  background: #d1fae5;
  color: #059669;
}

.result-status-badge.partially_mapped {
  background: #fef3c7;
  color: #d97706;
}

.result-status-badge.not_mapped {
  background: #fee2e2;
  color: #dc2626;
}

.result-status-badge.not_audited {
  background: #e2e8f0;
  color: #64748b;
}

.result-confidence {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.75rem;
}

.confidence-label {
  color: #64748b;
}

.result-item-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.result-compliance-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9rem;
  color: #334155;
  font-weight: 500;
}

.result-compliance-title i {
  color: #3b82f6;
  font-size: 0.85rem;
}

.result-error {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #dc2626;
  font-size: 0.8rem;
  padding: 6px 10px;
  background: #fef2f2;
  border-radius: 6px;
}

.result-skipped {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #64748b;
  font-size: 0.8rem;
  padding: 6px 10px;
  background: #f1f5f9;
  border-radius: 6px;
}

.bulk-results-actions {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: center;
}

.btn-save-results {
  padding: 12px 24px;
  background: linear-gradient(135deg, #10b981 0%, #34d399 100%);
  border: none;
  border-radius: 8px;
  color: #fff;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s;
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.2);
}

.btn-save-results:hover:not(:disabled) {
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
  transform: translateY(-1px);
}

.btn-save-results:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.btn-save-results i {
  font-size: 0.85rem;
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/* MODALS */
/* ═══════════════════════════════════════════════════════════════════════════ */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(15, 23, 42, 0.4);
  backdrop-filter: blur(4px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  padding: 20px;
}

.modal-content {
  background: #ffffff;
  border-radius: 16px;
  width: 100%;
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.15);
  border: 1px solid #e2e8f0;
}

.modal-content.modal-large {
  max-width: 650px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 20px;
  border-bottom: 1px solid #e2e8f0;
}

.modal-header h2 {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 1.1rem;
  color: #1e293b;
  margin: 0;
}

.modal-header h2 i {
  color: #3b82f6;
}

.btn-close {
  background: #f1f5f9;
  border: none;
  font-size: 1.2rem;
  color: #64748b;
  cursor: pointer;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-close:hover {
  background: #e2e8f0;
  color: #334155;
}

.modal-subtitle {
  color: #64748b;
  padding: 12px 20px;
  font-size: 0.85rem;
  background: #f8fafc;
  margin: 0;
}

.modal-body {
  padding: 20px;
}

.modal-input-section {
  margin-bottom: 16px;
}

.modal-input-section:last-child {
  margin-bottom: 0;
}

.modal-input-section h3 {
  font-size: 0.9rem;
  color: #334155;
  margin: 0 0 10px 0;
}

.modal-input-section select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.9rem;
  background: #f8fafc;
}

.modal-input-section select:focus {
  outline: none;
  border-color: #3b82f6;
}

/* Scope Options */
.scope-options {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.scope-option {
  flex: 1;
  min-width: 120px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 14px;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  background: #f8fafc;
}

.scope-option input { display: none; }

.scope-option i {
  font-size: 1.3rem;
  color: #94a3b8;
}

.scope-option span {
  font-size: 0.8rem;
  color: #64748b;
  text-align: center;
}

.scope-option.active,
.scope-option:hover {
  border-color: #3b82f6;
  background: #eff6ff;
}

.scope-option.active i { color: #3b82f6; }

/* File Upload Area */
.file-upload-area {
  border: 2px dashed #cbd5e1;
  border-radius: 12px;
  padding: 32px 16px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  background: #f8fafc;
}

.file-upload-area:hover {
  border-color: #3b82f6;
  background: #eff6ff;
}

.file-upload-area.large {
  padding: 24px 12px;
  min-height: 120px;
}

.upload-placeholder i {
  font-size: 1.5rem;
  color: #3b82f6;
  margin-bottom: 8px;
}

.upload-placeholder p {
  color: #475569;
  margin: 0 0 4px 0;
  font-size: 0.85rem;
}

.upload-placeholder small {
  color: #94a3b8;
  font-size: 0.7rem;
}

.selected-file-display {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: #059669;
}

.selected-file-display i { font-size: 1.2rem; }

/* Modal Actions */
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 16px 20px;
  border-top: 1px solid #e2e8f0;
  background: #f8fafc;
}

.btn-cancel {
  padding: 8px 16px;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  color: #64748b;
  cursor: pointer;
  font-size: 0.85rem;
  transition: all 0.2s;
}

.btn-cancel:hover {
  background: #e2e8f0;
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/* TREE UPLOAD BUTTON */
/* ═══════════════════════════════════════════════════════════════════════════ */
.tree-upload-btn {
  padding: 4px 8px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 6px;
  color: #94a3b8;
  cursor: pointer;
  font-size: 0.75rem;
  transition: all 0.2s;
  opacity: 0;
  margin-left: auto;
  margin-right: 8px;
}

.tree-item:hover .tree-upload-btn {
  opacity: 1;
}

.tree-upload-btn:hover {
  background: #3b82f6;
  border-color: #3b82f6;
  color: #fff;
}

.tree-upload-btn.small {
  padding: 3px 6px;
  font-size: 0.65rem;
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/* DOCUMENTS SECTION */
/* ═══════════════════════════════════════════════════════════════════════════ */
.documents-section {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  overflow: hidden;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
  border-bottom: 1px solid #e2e8f0;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #334155;
  font-size: 0.9rem;
}

.section-title i {
  color: #3b82f6;
}

.btn-add-doc {
  padding: 6px 12px;
  background: #3b82f6;
  border: none;
  border-radius: 6px;
  color: #fff;
  font-size: 0.8rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
}

.btn-add-doc:hover {
  background: #2563eb;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
}

.documents-list {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 200px;
  overflow-y: auto;
}

.document-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  transition: all 0.2s;
}

.document-card:hover {
  border-color: #3b82f6;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.1);
}

.doc-icon {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  color: #3b82f6;
}

.doc-info {
  flex: 1;
  min-width: 0;
}

.doc-name {
  display: block;
  font-size: 0.85rem;
  font-weight: 500;
  color: #1e293b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.doc-meta {
  font-size: 0.7rem;
  color: #94a3b8;
}

.doc-actions {
  display: flex;
  gap: 4px;
}

.doc-action-btn {
  padding: 6px;
  background: #f1f5f9;
  border: none;
  border-radius: 6px;
  color: #64748b;
  cursor: pointer;
  font-size: 0.75rem;
  transition: all 0.2s;
}

.doc-action-btn:hover {
  background: #3b82f6;
  color: #fff;
}

.doc-action-btn.delete:hover {
  background: #ef4444;
}

.no-documents {
  padding: 30px 20px;
  text-align: center;
  color: #94a3b8;
}

.no-documents i {
  font-size: 2rem;
  color: #cbd5e1;
  margin-bottom: 10px;
  display: block;
}

.no-documents p {
  margin: 0 0 12px 0;
  font-size: 0.85rem;
}

.btn-upload-first {
  padding: 10px 16px;
  background: linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%);
  border: none;
  border-radius: 8px;
  color: #fff;
  font-size: 0.85rem;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s;
}

.btn-upload-first:hover {
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
  transform: translateY(-1px);
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/* NEW UPLOAD MODAL STYLES */
/* ═══════════════════════════════════════════════════════════════════════════ */
.upload-target-info {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 20px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-bottom: 1px solid #e2e8f0;
}

.target-badge {
  padding: 5px 10px;
  border-radius: 16px;
  font-size: 0.7rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 5px;
  flex-shrink: 0;
}

.target-badge.policy {
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  color: #92400e;
}

.target-badge.subpolicy {
  background: linear-gradient(135deg, #ede9fe 0%, #ddd6fe 100%);
  color: #5b21b6;
}

.target-badge.compliance {
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
  color: #1e40af;
}

.target-badge.framework {
  background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
  color: #166534;
}

.target-details {
  flex: 1;
  min-width: 0;
}

.target-id {
  font-size: 0.65rem;
  color: #64748b;
  display: block;
  font-family: 'Consolas', monospace;
  line-height: 1.2;
}

.target-name {
  font-size: 0.8rem;
  color: #1e293b;
  font-weight: 500;
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.upload-type-options {
  display: flex;
  gap: 8px;
}

.upload-type-option {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  border: none;
  border-radius: 0;
  cursor: pointer;
  transition: all 0.2s;
  background: transparent;
}

.upload-type-option input { display: none; }

.upload-type-option .option-icon {
  width: 32px;
  height: 32px;
  background: transparent;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.9rem;
  color: #64748b;
  transition: all 0.2s;
  flex-shrink: 0;
}

.upload-type-option .option-content {
  flex: 1;
  min-width: 0;
}

.upload-type-option .option-title {
  display: block;
  font-size: 0.8rem;
  font-weight: 600;
  color: #334155;
  line-height: 1.2;
}

.upload-type-option .option-desc {
  display: block;
  font-size: 0.7rem;
  color: #94a3b8;
  line-height: 1.2;
}

.upload-type-option:hover {
  opacity: 0.8;
}

.upload-type-option:hover .option-icon {
  color: #3b82f6;
}

.upload-type-option.active {
  background: transparent;
}

.upload-type-option.active .option-icon {
  background: #3b82f6;
  color: #fff;
}

.upload-type-option.active .option-title {
  color: #3b82f6;
  font-weight: 700;
}

.file-upload-area.drag-over {
  border-color: #3b82f6;
  background: #eff6ff;
}

.upload-icon-wrapper {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 8px;
}

.upload-icon-wrapper i {
  font-size: 1.2rem;
  color: #3b82f6;
}

.upload-limit {
  display: block;
  margin-top: 4px;
  color: #64748b !important;
}

.selected-files-list {
  text-align: left;
}

.selected-file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  margin-bottom: 6px;
}

.selected-file-item i {
  font-size: 1rem;
  color: #3b82f6;
  flex-shrink: 0;
}

.selected-file-item .file-details {
  flex: 1;
  min-width: 0;
}

.selected-file-item .file-name {
  display: block;
  font-size: 0.8rem;
  color: #1e293b;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.selected-file-item .file-size {
  font-size: 0.65rem;
  color: #94a3b8;
}

/* File Progress Bar */
.file-progress-container {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 6px;
  width: 100%;
}

.file-progress-bar {
  flex: 1;
  height: 4px;
  background: #e2e8f0;
  border-radius: 2px;
  overflow: hidden;
}

.file-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #10b981, #34d399);
  border-radius: 2px;
  transition: width 0.3s ease;
}

.file-progress-text {
  font-size: 0.7rem;
  color: #64748b;
  font-weight: 600;
  min-width: 35px;
  text-align: right;
}

.file-status-icon {
  margin-top: 4px;
  font-size: 0.9rem;
}

.file-status-icon.completed {
  color: #10b981;
}

.file-status-icon.error {
  color: #ef4444;
}

.selected-file-item.uploading {
  border-color: #3b82f6;
  background: #f0f9ff;
}

.selected-file-item.completed {
  border-color: #10b981;
  background: #f0fdf4;
}

.selected-file-item.error {
  border-color: #ef4444;
  background: #fef2f2;
}

.uploading-spinner {
  color: #3b82f6;
  font-size: 0.9rem;
  padding: 4px;
}

.btn-add-more {
  width: 100%;
  padding: 8px;
  background: #f1f5f9;
  border: 1px dashed #cbd5e1;
  border-radius: 6px;
  color: #64748b;
  font-size: 0.75rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  transition: all 0.2s;
}

.btn-add-more:hover {
  background: #e2e8f0;
  border-color: #94a3b8;
}

.scope-info {
  padding: 8px 12px;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  border-radius: 6px;
  font-size: 0.75rem;
  color: #1e40af;
  display: flex;
  align-items: center;
  gap: 8px;
  line-height: 1.4;
}

.scope-info i {
  font-size: 0.85rem;
  flex-shrink: 0;
}

.btn-upload {
  padding: 8px 16px;
  background: linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%);
  border: none;
  border-radius: 6px;
  color: #fff;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
  flex: 1;
}

.btn-upload:hover:not(:disabled) {
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.btn-upload:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-run-ai-audit {
  padding: 8px 16px;
  background: linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%);
  border: none;
  border-radius: 6px;
  color: #fff;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
  flex: 1;
}

.btn-run-ai-audit:hover:not(:disabled) {
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);
}

.btn-run-ai-audit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* AI Audit Progress Bar */
.audit-progress-container {
  margin-top: 12px;
  padding: 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
}

.audit-progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.audit-progress-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.8rem;
  font-weight: 600;
  color: #475569;
}

.audit-progress-label i {
  color: #8b5cf6;
  font-size: 0.85rem;
}

.audit-progress-percentage {
  font-size: 0.8rem;
  font-weight: 700;
  color: #8b5cf6;
}

.audit-progress-bar {
  width: 100%;
  height: 8px;
  background: #e2e8f0;
  border-radius: 4px;
  overflow: hidden;
}

.audit-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #8b5cf6, #a78bfa);
  border-radius: 4px;
  transition: width 0.5s ease;
  box-shadow: 0 2px 4px rgba(139, 92, 246, 0.3);
}

.modal-input-section h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9rem;
  color: #334155;
  margin: 0 0 12px 0;
}

.modal-input-section h3 i {
  color: #3b82f6;
  font-size: 0.85rem;
}

/* Run AI Button */
.btn-run-ai {
  flex: 1;
  padding: 12px 16px;
  background: linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%);
  border: none;
  border-radius: 8px;
  color: #fff;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.2s;
}

.btn-run-ai:hover:not(:disabled) {
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);
}

.btn-run-ai:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/* TOAST */
/* ═══════════════════════════════════════════════════════════════════════════ */
.toast {
  position: fixed;
  bottom: 24px;
  right: 24px;
  padding: 14px 20px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 0.9rem;
  z-index: 2000;
  animation: slideIn 0.3s ease;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

.toast.success {
  background: #ecfdf5;
  color: #059669;
  border: 1px solid #a7f3d0;
}

.toast.error {
  background: #fef2f2;
  color: #dc2626;
  border: 1px solid #fecaca;
}

@keyframes slideIn {
  from { transform: translateX(100%); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/* RESPONSIVE */
/* ═══════════════════════════════════════════════════════════════════════════ */
@media (max-width: 1600px) {
  .split-screen-container {
    grid-template-columns: 480px 1fr 320px;
  }
}

@media (max-width: 1400px) {
  .split-screen-container {
    grid-template-columns: 420px 1fr 300px;
  }
}

@media (max-width: 1200px) {
  .split-screen-container {
    grid-template-columns: 380px 1fr 280px;
    gap: 12px;
  }
}

@media (max-width: 992px) {
  .organizational-controls {
    margin-left: 60px;
    width: calc(100% - 60px);
    padding: 12px;
  }
  
  .split-screen-container {
    grid-template-columns: 1fr;
    grid-template-rows: auto 1fr auto;
  }
  
  .panel-left {
    max-height: 400px;
    min-width: 100%;
  }
  
  .panel-right {
    max-height: 350px;
  }
}

@media (max-width: 768px) {
  .organizational-controls {
    margin-left: 0;
    width: 100%;
  }
  
  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .stats-summary {
    width: 100%;
  }
  
  .control-actions {
    flex-direction: column;
  }
}
</style>
