<template>
  <!-- Success Popup Modal -->
  <div v-if="showSuccessModal" class="modal-backdrop success-popup" @click.self="showSuccessModal = false">
    <div class="success-modal-content">
      <div class="success-icon">
        <i class="fas fa-check-circle"></i>
      </div>
      <h3>{{ successModalTitle }}</h3>
      <p>{{ successModalMessage }}</p>
      <button class="btn primary" @click="showSuccessModal = false">OK</button>
    </div>
  </div>

  <div class="system-risk-container" :class="{ 'sidebar-collapsed': isSidebarCollapsed }">
    <div class="system-risk-header">
      <div class="system-risk-header-left">
        <h2>System Identified Risks</h2>
        <p>AI-detected risks pending your review. Accept and complete details to add to the Risk Register.</p>
      </div>

      <div class="system-risk-header-actions">
        <div class="premium-scan-container">
          <!-- Main Configuration Toggle -->
          <div class="scan-config-trigger" @click="isDocHandlingExpanded = !isDocHandlingExpanded">
            <div class="trigger-content">
              <i class="fas fa-sliders-h"></i>
              <span>Configure AI Scan</span>
              <div class="active-count-badges">
                <span v-if="selectedSources.length" class="count-badge modules">{{ selectedSources.length }}</span>
                <span v-if="selectedSubFolderIds.length" class="count-badge docs">{{ selectedSubFolderIds.length }}</span>
                <span v-if="runChecklist" class="count-badge checklist"><i class="fas fa-check"></i></span>
              </div>
            </div>
            <i class="fas fa-chevron-down toggle-icon" :class="{ rotated: isDocHandlingExpanded }"></i>
          </div>

          <!-- Unified Scan Button -->
          <button
            type="button"
            class="btn btn-ai-scan-main"
            @click="runManualScan"
            :disabled="loading"
          >
            <i class="fas fa-robot" :class="{ 'fa-spin': loading }"></i>
            {{ loading ? 'Analyzing...' : 'Run AI Risk Scan' }}
          </button>

          <!-- Dropdown Panel -->
          <div v-if="isDocHandlingExpanded" class="scan-config-backdrop" @click="isDocHandlingExpanded = false"></div>
          <div v-if="isDocHandlingExpanded" class="scan-config-panel glass-panel shadow-2xl">
            <div class="panel-header">
              <h3><i class="fas fa-robot"></i> AI Scan Configuration</h3>
              <button type="button" class="panel-close-x" @click="isDocHandlingExpanded = false">
                <i class="fas fa-times"></i>
              </button>
            </div>

            <div class="panel-body-layout">
              <div class="panel-left-col">
                <div class="panel-section">
                  <label><i class="fas fa-cubes"></i> Source Modules</label>
                  <p class="section-desc">Select which modules the AI should analyze for risks.</p>
                  <div class="module-grid">
                    <div 
                      v-for="source in ['COMPLIANCE', 'AUDIT', 'INCIDENT', 'EVENT', 'EXTERNAL_SOURCES']" 
                      :key="source"
                      class="module-option"
                      :class="{ active: selectedSources.includes(source) }"
                      @click="toggleSourceSelection(source)"
                    >
                      <i :class="getSourceIcon(source)"></i>
                      <span>{{ source === 'EXTERNAL_SOURCES' ? 'External Sources' : source.charAt(0) + source.slice(1).toLowerCase() }}</span>
                      <div class="check-indicator"><i class="fas fa-check"></i></div>
                    </div>
                  </div>
                </div>

                <div class="panel-section no-border">
                  <label class="flex-label" @click="runChecklist = !runChecklist">
                    <span><i class="fas fa-clipboard-check"></i> Analysis Checklist</span>
                    <div class="toggle-switch" :class="{ active: runChecklist }">
                      <div class="switch-knob"></div>
                    </div>
                  </label>
                  <p class="section-hint">Perform analysis on all items currently checklisted for review in the system.</p>
                </div>
              </div>

              <div class="panel-right-col">
                <!-- External Sources Selection (Visible when EXTERNAL_SOURCES module is selected) -->
                <div v-if="selectedSources.includes('EXTERNAL_SOURCES')" class="panel-section external-sources-section">
                  <label><i class="fas fa-globe"></i> News Portals & Feeds</label>
                  <p class="section-desc">Select specific news sources the AI should crawl for relevant risks.</p>
                  
                  <div v-if="loadingExternalSources" class="external-loading">
                    <i class="fas fa-spinner fa-spin"></i> Loading sources...
                  </div>
                  <div v-else class="external-source-list custom-scrollbar">
                    <div v-for="source in availableExternalSources" :key="source.url" class="external-source-item">
                      <label class="premium-checkbox">
                        <input type="checkbox" :value="source.url" v-model="selectedExternalUrls" />
                        <span class="box"><i class="fas fa-check"></i></span>
                        <div class="source-info">
                          <span class="label">{{ source.name }}</span>
                          <span class="url-hint">{{ source.url }}</span>
                        </div>
                      </label>
                    </div>
                  </div>
                </div>

                <div class="panel-section" :class="{ 'with-top-margin': selectedSources.includes('EXTERNAL_SOURCES') }">
                  <label><i class="fas fa-folder-tree"></i> Document Repository</label>
                  <p class="section-desc">Choose specific documents or folders to include in the scan.</p>
                  <div class="repo-controls">
                    <select v-model="selectedFolderId" class="premium-select" @change="onFolderChange">
                      <option value="">Select Company Folder...</option>
                      <option v-for="folder in companyFolders" :key="folder.id" :value="folder.id">{{ folder.name }}</option>
                    </select>
                    
                    <div v-if="subFolders.length > 0" class="subfolder-selection">
                      <p class="repo-hint">Select subfolders, then choose specific documents if needed.</p>
                      <div class="subfolder-list custom-scrollbar">
                        <div v-for="sub in subFolders" :key="sub.id" class="subfolder-item-wrapper">
                          <label class="premium-checkbox">
                            <input type="checkbox" :value="sub.id" v-model="selectedSubFolderIds" @change="onSubfolderToggle(sub)" />
                            <span class="box"><i class="fas fa-check"></i></span>
                            <span class="label">{{ sub.name }}</span>
                          </label>
                          
                          <!-- Nested Documents -->
                          <div v-if="selectedSubFolderIds.includes(sub.id)" class="nested-document-list">
                            <div v-if="loadingDocuments[sub.id]" class="docs-loading">
                              <i class="fas fa-spinner fa-spin"></i> Loading...
                            </div>
                            <div v-else-if="!subfolderDocuments[sub.id] || subfolderDocuments[sub.id].length === 0" class="docs-empty">
                              No documents found.
                            </div>
                            <template v-else>
                              <div class="docs-meta">
                                <span>{{ subfolderDocuments[sub.id].length }} document(s) available</span>
                              </div>
                              <label v-for="doc in subfolderDocuments[sub.id]" :key="doc.id" class="premium-checkbox doc-checkbox">
                                <input type="checkbox" :value="doc.id" v-model="selectedDocumentIds" />
                                <span class="box"><i class="fas fa-check"></i></span>
                                <span class="label doc-label" :title="doc.name">
                                  <i class="far fa-file-alt"></i> {{ displayDocumentName(doc) }}
                                </span>
                              </label>
                            </template>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div class="panel-footer">
              <div class="footer-summary">
                <span v-if="selectedSources.length">{{ selectedSources.length }} modules selected</span>
                <span v-if="selectedSubFolderIds.length">{{ selectedSubFolderIds.length }} folders selected</span>
              </div>
              <button type="button" class="config-save-btn" @click="isDocHandlingExpanded = false">
                Apply & Save Configuration
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="testAnalysis.active" class="test-progress-wrap">
      <div class="test-progress-meta">
        <span>Risk Test Analysis In Progress</span>
        <span class="test-progress-meta-right">
          {{ testAnalysis.processed }}/{{ testAnalysis.total || '?' }} records ({{ testAnalysis.progressPct }}%)
          <button
            type="button"
            class="test-cancel-btn"
            title="Cancel analysis"
            @click="cancelRiskTestAnalysis"
            :disabled="testAnalysis.cancelling"
          >
            <i class="fas fa-times"></i>
          </button>
        </span>
      </div>
      <div class="test-progress-bar">
        <div class="test-progress-fill" :style="{ width: `${testAnalysis.progressPct}%` }"></div>
      </div>
      <p v-if="testAnalysis.lastRecord" class="test-progress-last">Last processed: {{ testAnalysis.lastRecord }}</p>
    </div>

    <div class="system-risk-stats">
      <div class="stat-card clickable" :class="{ active: filters.status === 'PENDING_REVIEW' }" @click="setStatusFilter('PENDING_REVIEW')">
        <p class="stat-value">{{ pendingCount }}</p>
        <p class="stat-label">Live Risks</p>
      </div>
      <div class="stat-card clickable" :class="{ active: filters.status === 'ACCEPTED_PENDING_APPROVAL' }" @click="setStatusFilter('ACCEPTED_PENDING_APPROVAL')">
        <p class="stat-value pending">{{ pendingApprovalCount }}</p>
        <p class="stat-label">Pending Approval</p>
      </div>
      <div class="stat-card clickable" :class="{ active: filters.status === 'APPROVED_ADDED' }" @click="setStatusFilter('APPROVED_ADDED')">
        <p class="stat-value accepted">{{ acceptedCount }}</p>
        <p class="stat-label">Approved</p>
      </div>
      <div class="stat-card clickable" :class="{ active: filters.status === 'REJECTED' }" @click="setStatusFilter('REJECTED')">
        <p class="stat-value rejected">{{ rejectedCount }}</p>
        <p class="stat-label">Rejected</p>
      </div>
    </div>

    <div class="ai-monitoring-meta">
      <h4 class="resources-heading">AI Resources</h4>
      <span class="meta-item">
        <span class="meta-label">Last AI run:</span>
        <span class="meta-value">{{ lastAiRunText }}</span>
      </span>
    </div>

    <div class="source-chips">
      <button
          v-for="sf in fetchedSourceFilters"
          :key="sf.value"
        type="button"
        class="chip"
          :class="{ active: filters.source === sf.value }"
          @click="toggleSourceFilter(sf.value)"
      >
          <span class="chip-dot"></span>
          {{ sf.label }}
      </button>
      <span v-if="!fetchedSourceFilters.length" class="no-resources-chip">No fetched resources yet</span>
    </div>

    <div class="monitoring-filter-bar">
      <input
        v-model.trim="uiFilters.search"
        class="monitoring-search-input"
        type="text"
        placeholder="Search by title, source, category..."
      />
      <select v-model="uiFilters.type" class="monitoring-select">
        <option value="">Type: All</option>
        <option value="Current">Current</option>
        <option value="Emerging">Emerging</option>
      </select>
      <select v-model="uiFilters.category" class="monitoring-select">
        <option value="">Category: All</option>
        <option v-for="category in categoryOptions" :key="`filter-category-${category}`" :value="category">{{ category }}</option>
      </select>
      <select v-model="uiFilters.confidence" class="monitoring-select">
        <option value="">Confidence: All</option>
        <option value="high">High (80%+)</option>
        <option value="medium">Medium (60-79%)</option>
        <option value="low">Low (&lt;60%)</option>
      </select>
      <select v-model="filters.status" class="monitoring-select" @change="loadRisks">
        <option value="PENDING_REVIEW">Status: Pending Review</option>
        <option value="ACCEPTED_PENDING_APPROVAL">Status: Sent for Approval</option>
        <option value="APPROVED_ADDED">Status: Accepted to Register</option>
        <option value="REJECTED">Status: Rejected</option>
      </select>
      <select v-model="uiFilters.sourceRef" class="monitoring-select">
        <option value="">Source: All</option>
        <option v-for="source in sourceReferenceOptions" :key="`filter-source-${source}`" :value="source">{{ source }}</option>
      </select>
      <select v-model="uiFilters.functionalArea" class="monitoring-select">
        <option value="">Area: All</option>
        <option v-for="area in functionalAreaOptions" :key="`filter-area-${area}`" :value="area">{{ area }}</option>
      </select>
      
      <button
        v-if="hasActiveUiFilters"
        type="button"
        class="clear-filters-btn"
        @click="clearUiFilters"
      >
        Clear
      </button>
    </div>

    <div class="risk-list">
      <article v-for="risk in filteredRisks" :key="risk.id" class="risk-card">
        <!-- Top row: Category and Confidence -->
        <div class="risk-card-header">
          <div class="risk-type-group">
            <span class="risk-category-tag" :class="risk.category.toLowerCase().replace(' ', '-')">{{ risk.category }}</span>
            <span class="risk-type-label">{{ risk.type }}</span>
          </div>
          <div class="ai-confidence-indicator">
            <template v-if="risk.status !== 'PENDING_REVIEW'">
              <span class="card-status-badge" :class="statusClass(risk.status)">
                <i class="fas fa-circle"></i> {{ statusLabel(risk.status) }}
              </span>
            </template>
            <div class="confidence-tag">
              <i class="fas fa-robot"></i>
              <span>{{ risk.confidence }}% AI</span>
              
              <!-- AI Justification Tooltip -->
              <div class="justification-tooltip">
                <div class="tooltip-header">
                  <i class="fas fa-brain"></i> AI Confidence Basis
                </div>
                <div class="tooltip-body">
                  {{ risk.confidenceJustification || 'AI calculated this confidence score based on the depth of evidence and impact factors.' }}
                </div>
                <div v-if="risk.confidenceFactors && risk.confidenceFactors.length" class="factor-list">
                  <div v-for="factor in risk.confidenceFactors" :key="factor.name" class="factor-item">
                    <span class="factor-name">{{ factor.name }}</span>
                    <span class="factor-score">{{ factor.score }}%</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <h3 class="risk-title">{{ risk.title }}</h3>
        
        <!-- Integrated Metadata: Criticality, Area, Source -->
        <div class="risk-metadata">
          <span class="meta-criticality" :class="risk.criticality.toLowerCase()">{{ risk.criticality }}</span>
          <span class="meta-divider">•</span>
          <span class="meta-item">Multiplier: ME 4</span>
          <span class="meta-divider">•</span>
          <span class="meta-item">{{ risk.functionalArea }}</span>
          <span class="meta-divider">•</span>
          <span class="meta-item">Source: {{ risk.source }}</span>
        </div>

        <p class="risk-summary-text">{{ risk.description }}</p>

        <!-- AI Reasoning section -->
        <div class="ai-reasoning-section">
          <div class="reasoning-toggle" @click="toggleReasoning(risk.id)">
            <i class="fas" :class="isExpandedReasoning(risk.id) ? 'fa-chevron-up' : 'fa-chevron-down'"></i>
            AI Reasoning & Evidence
          </div>
          <div v-show="isExpandedReasoning(risk.id)" class="reasoning-content">
            {{ risk.aiReasoning || risk.description }}
          </div>
        </div>

        <!-- Integrated Scores Grid -->
        <div class="risk-scores-grid">
          <div class="score-stat">
            <span class="stat-label">Likelihood</span>
            <span class="stat-value">{{ risk.likelihood }}</span>
            <div v-if="hasRationale(risk, 'likelihood')" class="justification-tooltip">
              <div class="tooltip-header"><i class="fas fa-info-circle"></i> Basis</div>
              <div class="tooltip-body">{{ getRationale(risk, 'likelihood') }}</div>
            </div>
          </div>
          <div class="score-stat">
            <span class="stat-label">Impact</span>
            <span class="stat-value">{{ risk.impact }}</span>
            <div v-if="hasRationale(risk, 'impact')" class="justification-tooltip">
              <div class="tooltip-header"><i class="fas fa-info-circle"></i> Basis</div>
              <div class="tooltip-body">{{ getRationale(risk, 'impact') }}</div>
            </div>
          </div>
          <div class="score-stat">
            <span class="stat-label">Velocity</span>
            <span class="stat-value">{{ risk.velocity }}</span>
            <div v-if="hasRationale(risk, 'velocity')" class="justification-tooltip">
              <div class="tooltip-header"><i class="fas fa-info-circle"></i> Basis</div>
              <div class="tooltip-body">{{ getRationale(risk, 'velocity') }}</div>
            </div>
          </div>
          <div class="score-stat exposure">
            <span class="stat-label">Exposure Score</span>
            <span class="stat-value"><strong>{{ risk.exposure }}</strong></span>
            <div v-if="hasRationale(risk, 'exposure')" class="justification-tooltip">
              <div class="tooltip-header"><i class="fas fa-info-circle"></i> Basis</div>
              <div class="tooltip-body">{{ getRationale(risk, 'exposure') }}</div>
            </div>
          </div>
        </div>

        <div class="risk-mitigation-preview">
          <strong>Proposed Mitigation:</strong> 
          <span v-if="Array.isArray(risk.mitigationSteps) && risk.mitigationSteps.length > 0">
            {{ risk.mitigationSteps.join('; ') }}
          </span>
          <span v-else-if="risk.mitigationSteps">{{ risk.mitigationSteps }}</span>
          <span v-else>{{ risk.mitigation }}</span>
        </div>


        <!-- Actions row: Buttons on left, View Source on right -->
        <div class="risk-actions-row">
          <div class="risk-actions">
            <template v-if="risk.status === 'PENDING_REVIEW'">
              <button type="button" class="btn-review" @click="openReview(risk)">Review &amp; Accept</button>
              <button type="button" class="btn-reject-ghost" @click="rejectFromList(risk.id)">Reject</button>
            </template>
            <template v-else-if="risk.status === 'ACCEPTED_PENDING_APPROVAL'">
              <button v-if="!canApprove(risk)" type="button" class="btn-review pending" disabled>
                <i class="fas fa-spinner fa-spin"></i> Approval In Progress
              </button>
              <button v-else type="button" class="btn-review approve" @click="openReview(risk)">
                Review & Approve
              </button>
              <button type="button" class="btn-review-ghost" @click="goToWorkflow(risk)">
                View Workflow <i class="fas fa-arrow-right"></i>
              </button>
            </template>
            <template v-else-if="risk.status === 'APPROVED_ADDED'">
              <span class="status-badge-outline approved">
                <i class="fas fa-check-circle"></i> Added to Register
              </span>
            </template>
            <template v-else-if="risk.status === 'REJECTED'">
              <span class="status-badge-outline rejected">
                <i class="fas fa-times-circle"></i> Rejected
              </span>
              <button type="button" class="btn-review-ghost" @click="openReview(risk)">Re-Review</button>
            </template>
            <template v-else>
              <span class="status-badge">{{ statusLabel(risk.status) }}</span>
            </template>
          </div>
          <button type="button" class="btn-view-source" @click="openSourceDrawer(risk)">
            View Source <i class="fas fa-external-link-alt"></i>
          </button>
        </div>
      </article>
      <div v-if="!loading && filteredRisks.length === 0" class="empty-risk-state">
        No risks match the selected filters.
      </div>
    </div>

    <div v-if="sourceDrawerOpen" class="source-drawer-overlay" @click.self="closeSourceDrawer">
      <aside class="source-drawer">
        <div class="source-drawer-header">
          <h3>Source Record</h3>
          <button type="button" class="close-btn" @click="closeSourceDrawer">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div v-if="sourceDrawerLoading" class="source-drawer-body">
          <div class="drawer-loading-state">
            <i class="fas fa-spinner fa-spin"></i>
            <p>Fetching original source details...</p>
          </div>
        </div>
        <div v-else-if="sourceDrawerRisk" class="source-drawer-body">
          <div class="source-header-main">
            <div class="source-icon">
              <i :class="getSourceIcon(sourceDrawerRisk.sourceModule)"></i>
            </div>
            <div class="source-title-group">
              <h3 class="source-drawer-title">{{ sourceDrawerDetail?.title || sourceDrawerRisk.source }}</h3>
              <span class="source-drawer-type">{{ (sourceDrawerRisk.sourceModule || 'GENERAL').replace('_', ' ') }}</span>
            </div>
          </div>

          <div v-if="sourceDrawerDetail?.link" class="source-field">
            <div class="source-label">Original Source Link</div>
            <div class="source-link-box">
              <a :href="sourceDrawerDetail.link" target="_blank" class="source-url">
                <i class="fas fa-external-link-alt"></i> {{ sourceDrawerDetail.link }}
              </a>
            </div>
          </div>

          <div class="source-field">
            <div class="source-label">Source Content / Evidence Snippet</div>
            <div class="source-summary-box">
              {{ sourceDrawerDetail?.description || sourceDrawerRisk.description }}
            </div>
          </div>

          <div class="source-metadata-grid">
            <div class="source-field">
              <div class="source-label">Reference ID</div>
              <div class="source-value">{{ sourceDrawerRisk.sourceRefId || '-' }}</div>
            </div>
            <div class="source-field">
              <div class="source-label">Detected On</div>
              <div class="source-value">{{ sourceDrawerRisk.detected }}</div>
            </div>
            <div v-if="sourceDrawerDetail?.extra_info?.category" class="source-field">
              <div class="source-label">Source Category</div>
              <div class="source-value">{{ sourceDrawerDetail.extra_info.category }}</div>
            </div>
          </div>

          <div class="source-field">
            <div class="source-label">AI Identification Reasoning</div>
            <div class="source-reasoning-box">
              <p>{{ sourceDrawerRisk.aiReasoning }}</p>
            </div>
          </div>
          
          <div class="source-field">
            <div class="source-label">Associated Risk Candidate</div>
            <div class="source-value">{{ sourceDrawerRisk.title }}</div>
          </div>
        </div>
      </aside>
    </div>

    <div v-if="selectedRisk" class="review-drawer-overlay" @click.self="closeReview">
      <div class="review-drawer">
        <header class="review-header">
          <div class="header-left">
            <h3>Review AI-Identified Risk</h3>
            <p class="review-subtitle">Compare AI suggestion with your review. Edit fields as needed.</p>
          </div>
          <button type="button" class="close-btn" @click="closeReview">
            <i class="fas fa-times"></i>
          </button>
        </header>

        <div class="review-body">
          <section class="draft-side">
            <h4 class="side-title"><i class="fas fa-sparkles"></i> AI Draft (Read-only)</h4>
            
            <div class="ai-field has-tooltip">
              <label>Risk Title <span class="ai-badge">AI</span></label>
              <div class="ai-value">{{ selectedRisk.title }}</div>
              <div class="justification-tooltip">
                <div class="tooltip-header"><i class="fas fa-brain"></i> AI Reasoning</div>
                <div class="tooltip-body">{{ selectedRisk.aiReasoning || 'AI inferred this title from the source document context.' }}</div>
              </div>
            </div>
            <div class="ai-field has-tooltip">
              <label>Risk Type <span class="ai-badge">AI</span></label>
              <div class="ai-value">{{ selectedRisk.type }}</div>
              <div class="justification-tooltip">
                <div class="tooltip-header"><i class="fas fa-info-circle"></i> Basis</div>
                <div class="tooltip-body">{{ getRationale(selectedRisk, 'risk_type') }}</div>
              </div>
            </div>
            <div class="ai-field has-tooltip">
              <label>Category <span class="ai-badge">AI</span></label>
              <div class="ai-value">{{ selectedRisk.category }}</div>
              <div class="justification-tooltip">
                <div class="tooltip-header"><i class="fas fa-info-circle"></i> Basis</div>
                <div class="tooltip-body">{{ getRationale(selectedRisk, 'category') }}</div>
              </div>
            </div>
            <div class="ai-field has-tooltip">
              <label>Criticality <span class="ai-badge">AI</span></label>
              <div class="ai-value">{{ selectedRisk.criticality }}</div>
              <div class="justification-tooltip">
                <div class="tooltip-header"><i class="fas fa-info-circle"></i> Basis</div>
                <div class="tooltip-body">{{ getRationale(selectedRisk, 'criticality') }}</div>
              </div>
            </div>
            <div class="ai-field has-tooltip">
              <label>Risk Description <span class="ai-badge">AI</span></label>
              <div class="ai-value">{{ selectedRisk.description }}</div>
              <div class="justification-tooltip">
                <div class="tooltip-header"><i class="fas fa-info-circle"></i> Basis</div>
                <div class="tooltip-body">{{ getRationale(selectedRisk, 'risk_description') }}</div>
              </div>
            </div>
            <div class="ai-field has-tooltip">
              <label>Possible Damage <span class="ai-badge">AI</span></label>
              <div class="ai-value">{{ selectedRisk.possibleDamage }}</div>
              <div class="justification-tooltip">
                <div class="tooltip-header"><i class="fas fa-info-circle"></i> Basis</div>
                <div class="tooltip-body">{{ getRationale(selectedRisk, 'possible_damage') }}</div>
              </div>
            </div>
            <div class="ai-field has-tooltip">
              <label>Business Impact <span class="ai-badge">AI</span></label>
              <div class="ai-value">{{ Array.isArray(selectedRisk.businessImpact) ? selectedRisk.businessImpact.join(', ') : (selectedRisk.businessImpact || 'N/A') }}</div>
              <div class="justification-tooltip">
                <div class="tooltip-header"><i class="fas fa-info-circle"></i> Basis</div>
                <div class="tooltip-body">{{ getRationale(selectedRisk, 'business_impact') }}</div>
              </div>
            </div>

            <div class="ai-grid-2">
              <div class="ai-field has-tooltip">
                <label>Likelihood <span class="ai-badge">AI</span></label>
                <div class="ai-value">{{ selectedRisk.likelihood }}/10</div>
                <div class="justification-tooltip">
                  <div class="tooltip-header"><i class="fas fa-info-circle"></i> Basis</div>
                  <div class="tooltip-body">{{ getRationale(selectedRisk, 'likelihood') }}</div>
                </div>
              </div>
              <div class="ai-field has-tooltip">
                <label>Impact <span class="ai-badge">AI</span></label>
                <div class="ai-value">{{ selectedRisk.impact }}/10</div>
                <div class="justification-tooltip">
                  <div class="tooltip-header"><i class="fas fa-info-circle"></i> Basis</div>
                  <div class="tooltip-body">{{ getRationale(selectedRisk, 'impact') }}</div>
                </div>
              </div>
            </div>

            <div class="ai-field has-tooltip">
              <label>Exposure Rating <span class="ai-badge">AI</span></label>
              <div class="ai-value">{{ selectedRisk.exposure }}</div>
              <div class="justification-tooltip">
                <div class="tooltip-header"><i class="fas fa-info-circle"></i> Basis</div>
                <div class="tooltip-body">Calculated based on Likelihood ({{selectedRisk.likelihood}}) and Impact ({{selectedRisk.impact}}).</div>
              </div>
            </div>
            
            <div class="ai-field has-tooltip">
              <label>Velocity <span class="ai-badge">AI</span></label>
              <div class="ai-value">{{ selectedRisk.velocity || 5 }}/10</div>
              <div class="justification-tooltip">
                <div class="tooltip-header"><i class="fas fa-info-circle"></i> Basis</div>
                <div class="tooltip-body">{{ getRationale(selectedRisk, 'velocity') }}</div>
              </div>
            </div>

            <div class="ai-field has-tooltip">
              <label>Control Effectiveness <span class="ai-badge">AI</span></label>
              <div class="ai-value">{{ selectedRisk.controlEffectiveness || 'Low' }}</div>
              <div class="justification-tooltip">
                <div class="tooltip-header"><i class="fas fa-info-circle"></i> Basis</div>
                <div class="tooltip-body">{{ getRationale(selectedRisk, 'control_effectiveness') }}</div>
              </div>
            </div>

            <div class="ai-field has-tooltip">
              <label>Framework Reference <span class="ai-badge">AI</span></label>
              <div class="ai-value">{{ selectedRisk.frameworkReference || 'N/A' }}</div>
              <div class="justification-tooltip">
                <div class="tooltip-header"><i class="fas fa-info-circle"></i> Basis</div>
                <div class="tooltip-body">{{ getRationale(selectedRisk, 'framework_reference') }}</div>
              </div>
            </div>

            <div class="ai-field has-tooltip">
              <label>Functional Area <span class="ai-badge">AI</span></label>
              <div class="ai-value">{{ selectedRisk.functionalArea || 'IT' }}</div>
              <div class="justification-tooltip">
                <div class="tooltip-header"><i class="fas fa-info-circle"></i> Basis</div>
                <div class="tooltip-body">{{ getRationale(selectedRisk, 'functional_area') }}</div>
              </div>
            </div>

            <div class="ai-field">
              <label>Mitigation Steps <span class="ai-badge">AI</span></label>
              <ul class="ai-steps" v-if="Array.isArray(selectedRisk.mitigationSteps)">
                <li v-for="(step, idx) in selectedRisk.mitigationSteps" :key="idx">{{ step }}</li>
              </ul>
              <div v-else class="ai-value">{{ selectedRisk.mitigationSteps || 'None identified' }}</div>
            </div>

            <div class="ai-field">
              <label>AI Reasoning <span class="ai-badge">AI</span></label>
              <div class="ai-reasoning-quote">{{ selectedRisk.aiReasoning || selectedRisk.description }}</div>
            </div>

            <div class="ai-field rationale-block">
              <label>Per-Field Rationale</label>
              <div class="rationale-item">
                <strong>Likelihood:</strong> {{ selectedRisk.ai_metadata?.per_field_rationale?.likelihood || 'Based on historical trends.' }}
              </div>
              <div class="rationale-item">
                <strong>Impact:</strong> {{ selectedRisk.ai_metadata?.per_field_rationale?.impact || 'Calculated from business criticality.' }}
              </div>
              <div class="rationale-item">
                <strong>Velocity:</strong> {{ selectedRisk.ai_metadata?.per_field_rationale?.velocity || 'Estimated arrival time.' }}
              </div>
              <div class="rationale-item">
                <strong>Control effectiveness:</strong> {{ selectedRisk.ai_metadata?.per_field_rationale?.control_effectiveness || 'Current mitigation coverage.' }}
              </div>
              <div class="rationale-item">
                <strong>Functional area:</strong> {{ selectedRisk.ai_metadata?.per_field_rationale?.functional_area || 'Identified primary department.' }}
              </div>
              <div class="rationale-item">
                <strong>Framework reference:</strong> {{ selectedRisk.ai_metadata?.per_field_rationale?.framework_reference || 'Regulatory/Standard alignment.' }}
              </div>
            </div>

            <div class="ai-field">
              <label>Linked Source</label>
              <a href="#" @click.prevent="openSourceDrawer(selectedRisk)" class="source-link">
                {{ selectedRisk.sourceRef || 'Source Record' }} — View →
              </a>
            </div>
          </section>

          <section class="edit-side">
            <h4 class="side-title">Your Review (Editable)</h4>

            <div class="risk-score-widget">
              <div class="score-row">
                <div class="score-info">
                  <span class="score-label">Inherent Risk: {{ inherentRiskScore }}</span>
                  <span class="score-tag high">{{ inherentRiskScore > 70 ? 'CRITICAL' : (inherentRiskScore > 40 ? 'HIGH' : 'MEDIUM') }}</span>
                </div>
                <div class="progress-container">
                  <div class="progress-bar inherent" :style="{ width: inherentRiskScore + '%' }"></div>
                </div>
              </div>
              <div class="score-row">
                <div class="score-info">
                  <span class="score-label">Residual Risk: {{ residualRiskScore }}</span>
                  <span class="score-tag med-h">{{ residualRiskScore > 60 ? 'HIGH' : (residualRiskScore > 30 ? 'MED-H' : 'MEDIUM') }}</span>
                </div>
                <div class="progress-container">
                  <div class="progress-bar residual" :style="{ width: residualRiskScore + '%' }"></div>
                </div>
              </div>
              <p class="control-effect-note">{{ controlEffectText }}</p>
            </div>

            <div class="form-group">
              <label>Risk Title</label>
              <input v-model="reviewForm.title" type="text" class="review-input" :disabled="isReviewerApprovalMode" />
              <!-- Change Alert for Title -->
              <div v-if="isReviewerApprovalMode && isFieldChanged('title')" class="field-change-alert">
                <i class="fas fa-exclamation-triangle"></i> Modified from AI: <span>"{{ getOriginalValueDisplay('title') }}"</span>
              </div>
            </div>

            <div class="form-group">
              <label>Risk Type</label>
              <select v-model="reviewForm.type" class="review-select" :disabled="isReviewerApprovalMode">
                <option v-for="opt in typeOptions" :key="opt" :value="opt">{{ opt }}</option>
              </select>
              <!-- Change Alert for Type -->
              <div v-if="isReviewerApprovalMode && isFieldChanged('type')" class="field-change-alert">
                <i class="fas fa-exclamation-triangle"></i> Modified from AI: <span>{{ getOriginalValueDisplay('type') }}</span>
              </div>
            </div>

            <div class="form-group">
              <label>Category</label>
              <select v-model="reviewForm.category" class="review-select" :disabled="isReviewerApprovalMode">
                <option v-for="cat in categoryOptions" :key="cat" :value="cat">{{ cat }}</option>
              </select>
              <!-- Change Alert for Category -->
              <div v-if="isReviewerApprovalMode && isFieldChanged('category')" class="field-change-alert">
                <i class="fas fa-exclamation-triangle"></i> Modified from AI: <span>{{ getOriginalValueDisplay('category') }}</span>
              </div>
            </div>

            <div class="form-group">
              <label>Criticality</label>
              <select v-model="reviewForm.criticality" class="review-select" :disabled="isReviewerApprovalMode">
                <option>Low</option>
                <option>Medium</option>
                <option>High</option>
                <option>Critical</option>
              </select>
              <!-- Change Alert for Criticality -->
              <div v-if="isReviewerApprovalMode && isFieldChanged('criticality')" class="field-change-alert">
                <i class="fas fa-exclamation-triangle"></i> Modified from AI: <span>{{ getOriginalValueDisplay('criticality') }}</span>
              </div>
            </div>

            <div class="form-group">
              <label>Description</label>
              <textarea v-model="reviewForm.description" rows="3" class="review-textarea" :disabled="isReviewerApprovalMode"></textarea>
            </div>

            <div class="form-group">
              <label>Possible Damage</label>
              <textarea v-model="reviewForm.possibleDamage" rows="2" class="review-textarea" :disabled="isReviewerApprovalMode"></textarea>
            </div>

            <div class="form-group">
              <label>Business Impact</label>
              <div class="impact-buttons" :class="{ disabled: isReviewerApprovalMode }">
                <button 
                  v-for="impact in impactOptions" 
                  :key="impact" 
                  @click="!isReviewerApprovalMode && toggleImpact(impact)"
                  :class="{ active: reviewForm.businessImpact.includes(impact) }"
                  class="impact-btn"
                  :disabled="isReviewerApprovalMode"
                >
                  {{ impact }}
                </button>
              </div>
            </div>

            <div class="sliders-grid">
              <div class="slider-item">
                <label>Likelihood: {{ reviewForm.likelihood }}/10</label>
                <input type="range" v-model.number="reviewForm.likelihood" min="1" max="10" :disabled="isReviewerApprovalMode" />
              </div>
              <div class="slider-item">
                <label>Impact: {{ reviewForm.impact }}/10</label>
                <input type="range" v-model.number="reviewForm.impact" min="1" max="10" :disabled="isReviewerApprovalMode" />
              </div>
            </div>

            <!-- Justification for Likelihood/Impact -->
            <div v-if="isReviewerApprovalMode && (isFieldChanged('likelihood') || isFieldChanged('impact'))" class="justification-box">
              <div class="justification-warning">
                <span class="change-label">Changed Risk Metrics</span>
                <span class="change-values">
                  AI: <strong>L:{{ getOriginalValueDisplay('likelihood') }}, I:{{ getOriginalValueDisplay('impact') }}</strong> 
                  → User: <strong>L:{{ reviewForm.likelihood }}, I:{{ reviewForm.impact }}</strong>
                </span>
              </div>
              <textarea 
                v-model="reviewForm.justifications.likelihood" 
                class="justification-textarea" 
                placeholder="Justification required for changing risk metrics..."
              ></textarea>
            </div>

            <div class="form-group">
              <label>Exposure Rating (auto-calculated)</label>
              <div class="exposure-value">{{ inherentRiskScore }}</div>
            </div>

            <div class="form-group">
              <label>Velocity: {{ reviewForm.velocity }}/10</label>
              <input type="range" v-model.number="reviewForm.velocity" min="1" max="10" class="velocity-slider" :disabled="isReviewerApprovalMode" />
              <p class="hint">How quickly this risk can impact the organisation</p>
            </div>

            <div class="form-group">
              <label>Control Effectiveness</label>
              <select v-model="reviewForm.controlEffectiveness" class="review-select" :disabled="isReviewerApprovalMode">
                <option v-for="opt in controlEffectivenessOptions" :key="opt" :value="opt">{{ opt }}</option>
              </select>
              <p class="hint">Effectiveness of existing controls for this risk</p>

              <!-- Justification for Control Effectiveness -->
              <div v-if="isReviewerApprovalMode && isFieldChanged('controlEffectiveness')" class="justification-box">
                <div class="justification-warning">
                  <span class="change-label">Changed Control Effectiveness</span>
                  <span class="change-values">
                    AI: <strong>{{ getOriginalValueDisplay('controlEffectiveness') }}</strong> 
                    → User: <strong>{{ reviewForm.controlEffectiveness }}</strong>
                  </span>
                </div>
                <textarea 
                  v-model="reviewForm.justifications.controlEffectiveness" 
                  class="justification-textarea" 
                  placeholder="Justification required for changing control effectiveness..."
                ></textarea>
              </div>
            </div>

            <div class="scores-preview-grid">
              <div class="preview-box">
                <span class="p-label">Inherent Risk Score</span>
                <span class="p-value inherent">{{ inherentRiskScore }}</span>
              </div>
              <div class="preview-box">
                <span class="p-label">Residual Risk Score</span>
                <span class="p-value residual">{{ residualRiskScore }}</span>
              </div>
            </div>

            <div class="form-group">
              <label>Framework Reference</label>
              <select v-model="reviewForm.frameworkReference" class="review-select" :disabled="isReviewerApprovalMode">
                <option v-for="ref in frameworkReferenceOptions" :key="ref" :value="ref">{{ ref }}</option>
              </select>

              <!-- Justification for Framework -->
              <div v-if="isReviewerApprovalMode && isFieldChanged('frameworkReference')" class="justification-box">
                <div class="justification-warning">
                  <span class="change-label">Changed Framework Reference</span>
                  <span class="change-values">
                    AI: <strong>{{ getOriginalValueDisplay('frameworkReference') || 'None' }}</strong> 
                    → User: <strong>{{ reviewForm.frameworkReference }}</strong>
                  </span>
                </div>
                <textarea 
                  v-model="reviewForm.justifications.frameworkReference" 
                  class="justification-textarea" 
                  placeholder="Justification required for changing framework reference..."
                ></textarea>
              </div>
            </div>

            <div class="form-group">
              <label>Functional Area</label>
              <select v-model="reviewForm.functionalArea" class="review-select" :disabled="isReviewerApprovalMode">
                <option v-for="area in functionalAreaOptions" :key="area" :value="area">{{ area }}</option>
              </select>

              <!-- AI Rationale for Functional Area -->
              <div v-if="hasRationale(selectedRisk, 'functionalArea')" class="field-rationale">
                <i class="fas fa-robot"></i>
                <span>{{ getRationale(selectedRisk, 'functionalArea') }}</span>
              </div>

              <!-- Justification for Functional Area -->
              <div v-if="isReviewerApprovalMode && isFieldChanged('functionalArea')" class="justification-box">
                <div class="justification-warning">
                  <span class="change-label">Changed Functional Area</span>
                  <span class="change-values">
                    AI: <strong>{{ getOriginalValueDisplay('functionalArea') }}</strong> 
                    → User: <strong>{{ reviewForm.functionalArea }}</strong>
                  </span>
                </div>
                <textarea 
                  v-model="reviewForm.justifications.functionalArea" 
                  class="justification-textarea" 
                  placeholder="Justification required for changing functional area..."
                ></textarea>
              </div>
            </div>

            <div class="form-group">
              <label>Mitigation Steps</label>
              <div class="mitigation-edit">
                <div v-for="(step, i) in reviewForm.mitigationSteps" :key="i" class="step-input-row">
                  <input v-model="reviewForm.mitigationSteps[i]" type="text" class="step-input" :disabled="isReviewerApprovalMode" />
                  <button @click="removeMitigationStep(i)" class="remove-step" :disabled="isReviewerApprovalMode">×</button>
                </div>
                <button @click="addMitigationStep" class="add-step-link" :disabled="isReviewerApprovalMode">+ Add Step</button>
              </div>
            </div>

            <div class="form-group">
              <label>Assign Risk Owner</label>
              <select v-model="reviewForm.riskOwner" class="review-select" :disabled="isReviewerApprovalMode">
                <option value="">Select...</option>
                <option v-for="u in userOptions" :key="u.id" :value="u.id">{{ u.name }}</option>
              </select>
            </div>

            <div class="form-group">
              <label>Assign Reviewer</label>
              <select v-model="reviewForm.reviewer" class="review-select" :disabled="isReviewerApprovalMode">
                <option value="">Select...</option>
                <option v-for="u in userOptions" :key="u.id" :value="u.id">{{ u.name }}</option>
              </select>
            </div>

            <div class="form-group">
              <label>{{ isReviewerApprovalMode ? 'Reviewer Feedback / Comments' : 'Notes / Comments' }}</label>
              <textarea 
                v-model="reviewForm.notes" 
                rows="3" 
                class="review-textarea" 
                :placeholder="isReviewerApprovalMode ? 'Enter your approval/rejection feedback here...' : ''"
              ></textarea>
            </div>

            <p class="workflow-note">Accepted risks will be routed through the standard approval workflow before being added to the Risk Register.</p>

            <div class="drawer-actions">
              <template v-if="selectedRisk && selectedRisk.status === 'ACCEPTED_PENDING_APPROVAL'">
                <button @click="approveRisk(selectedRisk)" class="btn-accept">Review & Accept</button>
                <button @click="rejectRisk(selectedRisk)" class="btn-reject">Reject</button>
              </template>
              <template v-else>
                <button @click="directSendForApproval" class="btn-accept">Accept & Send for Approval</button>
                <button @click="saveDraft" class="btn-draft">Save as Draft</button>
                <button @click="rejectCurrent" class="btn-reject">Reject</button>
              </template>
              <button @click="closeReview" class="btn-cancel">Cancel</button>
            </div>
          </section>
        </div>
      </div>
    </div>




    <!-- Scheduling Modal -->
    <div v-if="showScheduleModal" class="modal-backdrop" @click.self="closeScheduleModal">
      <div class="schedule-modal">
        <div class="modal-header">
          <h3>Schedule Smart Risk Scan</h3>
          <button type="button" class="close-btn" @click="closeScheduleModal">×</button>
        </div>
        <div class="modal-body">
          <div class="schedule-config">
            <div class="form-group">
              <label>Frequency</label>
              <select v-model="scheduleForm.schedule_type" class="form-control">
                <option value="daily">Every Day</option>
                <option value="recurring">Every Week</option>
                <option value="monthly">Every Month</option>
                <option value="quarterly">Every Quarter</option>
                <option value="yearly">Every Year</option>
                <option value="one_minute">Test (Every Minute)</option>
              </select>
            </div>
            <div class="form-group">
              <label>Start Date & Time</label>
              <input type="datetime-local" v-model="scheduleForm.start_date" class="form-control" />
            </div>
            <div class="form-group" v-if="scheduleForm.schedule_type === 'recurring'">
              <label>Day of Week</label>
              <select v-model="scheduleForm.day_of_week" class="form-control">
                <option :value="0">Monday</option>
                <option :value="1">Tuesday</option>
                <option :value="2">Wednesday</option>
                <option :value="3">Thursday</option>
                <option :value="4">Friday</option>
                <option :value="5">Saturday</option>
                <option :value="6">Sunday</option>
              </select>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>Hour (0-23)</label>
                <input type="number" v-model="scheduleForm.hour" min="0" max="23" class="form-control" />
              </div>
              <div class="form-group">
                <label>Minute (0-59)</label>
                <input type="number" v-model="scheduleForm.minute" min="0" max="59" class="form-control" />
              </div>
            </div>
          </div>

          <div class="active-schedules" v-if="activeSchedules.length">
            <h4 class="section-title">Active Schedules</h4>
            <div v-for="s in activeSchedules" :key="s.id" class="schedule-item">
              <div class="schedule-info">
                <strong>{{ formatFrequency(s.schedule_type) }}</strong>
                <span>Next run: {{ formatDate(s.next_run_at) }}</span>
              </div>
              <div class="schedule-actions">
                <button type="button" class="btn-icon danger" @click="deleteSchedule(s.id)" title="Delete schedule">
                  <i class="fas fa-trash"></i>
                </button>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn primary" @click="saveSchedule" :disabled="scheduling">
            {{ scheduling ? 'Saving...' : 'Set Schedule' }}
          </button>
          <button type="button" class="btn ghost" @click="closeScheduleModal">Cancel</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import apiService from '../../services/apiService.js';
import { API_ENDPOINTS } from '../../config/api.js';
import { useRiskStore } from '@/stores/risk';

export default {
  name: 'SystemIdentifiedRisks',
  components: {},
  data() {
    return {
      isSidebarCollapsed: false,
      loading: false,
      sourceFilters: [
        { label: 'Audit Findings', value: 'AUDIT' },
        { label: 'Incidents', value: 'INCIDENT' },
        { label: 'Compliance Controls', value: 'COMPLIANCE' },
        { label: 'TPRM / Vendor Data', value: 'TPRM' },
        { label: 'External Integrations', value: 'INTEGRATION' },
        { label: 'External Sources', value: 'EXTERNAL_SOURCES' },
        { label: 'Events', value: 'EVENT' }
      ],
      typeOptions: ['Current', 'Residual', 'Inherent', 'Emerging', 'Accepted'],
      categoryOptions: ['IT Security', 'Operational', 'Compliance', 'Financial', 'Strategic', 'Third-Party'],
      functionalAreaOptions: [],
      impactOptions: ['Revenue Loss', 'Reputation', 'Regulatory', 'Operational', 'Strategic'],
      stats: {
        pendingCount: 0,
        pendingApprovalCount: 0,
        acceptedToday: 0, // Keeping for backward compatibility if needed elsewhere
        acceptedCount: 0,
        rejectedCount: 0,
        sourcesActive: 0
      },
      selectedScanSource: 'COMPLIANCE', // Legacy single source
      selectedSources: ['INCIDENT'],     // New multi-source
      companyFolders: [],
      selectedFolderId: '',
      selectedFolderCode: '',
      subFolders: [],
      selectedSubFolderIds: [],
      subfolderDocuments: {},
      selectedDocumentIds: [],
      loadingDocuments: {},
      loadingExternalSources: false,
      availableExternalSources: [],
      selectedExternalUrls: [],
      isDocHandlingExpanded: false,
      runChecklist: false,
      pagination: {
        page: 1,
        pageSize: 10,
        totalCount: 0,
        totalPages: 0
      },
      filters: {
        source: '',
        status: 'PENDING_REVIEW',
        category: '',
        reviewer_status: ''
      },
      uiFilters: {
        search: '',
        type: '',
        category: '',
        confidence: '',
        sourceRef: '',
        functionalArea: '',
        velocityMin: 0
      },
      testAnalysis: {
        active: false,
        jobId: null,
        processed: 0,
        total: 0,
        progressPct: 0,
        lastRecord: null,
        cancelling: false,
        pollTimer: null
      },
      sourceDrawerOpen: false,
      sourceDrawerLoading: false,
      sourceDrawerRisk: null,
      sourceDrawerDetail: null,
      selectedRisk: null,
      showWorkflowModal: false,
      workflowRiskData: null,
      controlEffectivenessOptions: ['Low', 'Medium', 'High'],
      frameworkReferenceOptions: ['ME 4 (Infection Control)', 'NIST PR.AC-1', 'ISO 27001 A.5.1', 'GDPR Art. 32'],
      userOptions: [],
      currentUser: null,
      reviewForm: {
        title: '',
        type: 'Current',
        category: '',
        criticality: 'Medium',
        description: '',
        possibleDamage: '',
        businessImpact: [],
        likelihood: 5,
        impact: 5,
        velocity: 5,
        controlEffectiveness: 'Low',
        frameworkReference: '',
        functionalArea: 'IT',
        riskOwner: '',
        reviewer: '',
        notes: '',
        priority: 'Medium',
        mitigationSteps: [],
        complianceId: null,
        justifications: {
          likelihood: '',
          impact: '',
          velocity: '',
          controlEffectiveness: '',
          frameworkReference: '',
          functionalArea: '',
          businessImpact: ''
        }
      },
      showScheduleModal: false,
      scheduling: false,
      activeSchedules: [],
      scheduleForm: {
        schedule_type: 'daily',
        start_date: new Date().toISOString().slice(0, 16),
        hour: 9,
        minute: 0,
        day_of_week: 1,
        day_of_month: 1
      },
      risks: [],
      expandedReasoning: [],
      originalAiValues: {},
      showSuccessModal: false,
      successModalTitle: '',
      successModalMessage: ''
    };
  },
  computed: {
    pendingCount() {
      return this.stats.pendingCount || 0;
    },
    pendingApprovalCount() {
      return this.stats.pendingApprovalCount || 0;
    },
    acceptedCount() {
      return this.stats.acceptedCount || 0;
    },
    rejectedCount() {
      return this.stats.rejectedCount || 0;
    },
    sourceCounts() {
      const counts = {};
      for (const r of this.risks || []) {
        const key = r.sourceModule;
        if (!key) continue;
        counts[key] = (counts[key] || 0) + 1;
      }
      return counts;
    },
    fetchedSourceFilters() {
      return this.sourceFilters.filter((sf) => (this.sourceCounts[sf.value] || 0) > 0);
    },
    sourceReferenceOptions() {
      return [...new Set((this.risks || []).map((r) => r.source).filter(Boolean))].sort();
    },
    hasActiveUiFilters() {
      return Object.values(this.uiFilters).some((value) => Boolean(value));
    },
    filteredRisks() {
      const searchTerm = (this.uiFilters.search || '').toLowerCase();
      return (this.risks || []).filter((risk) => {
        if (this.uiFilters.type && risk.type !== this.uiFilters.type) return false;
        if (this.uiFilters.category && risk.category !== this.uiFilters.category) return false;
        if (this.uiFilters.sourceRef && risk.source !== this.uiFilters.sourceRef) return false;
        if (this.uiFilters.functionalArea && risk.functionalArea !== this.uiFilters.functionalArea) return false;
        if (this.uiFilters.velocityMin > 0 && Number(risk.velocity) < this.uiFilters.velocityMin) return false;

        if (this.uiFilters.confidence === 'high' && Number(risk.confidence) < 80) return false;
        if (
          this.uiFilters.confidence === 'medium'
          && (Number(risk.confidence) < 60 || Number(risk.confidence) >= 80)
        ) return false;
        if (this.uiFilters.confidence === 'low' && Number(risk.confidence) >= 60) return false;

        if (!searchTerm) return true;
        const searchCorpus = [
          risk.title,
          risk.description,
          risk.source,
          risk.category,
          risk.type
        ]
          .filter(Boolean)
          .join(' ')
          .toLowerCase();
        return searchCorpus.includes(searchTerm);
      });
    },
    lastAiRunText() {
      if (!this.risks || this.risks.length === 0) {
        return 'No AI run history yet';
      }
      const latest = this.risks
        .map((r) => r.createdAtRaw)
        .filter(Boolean)
        .map((d) => new Date(d))
        .filter((d) => !Number.isNaN(d.getTime()))
        .sort((a, b) => b - a)[0];
      if (!latest) {
        return 'No AI run history yet';
      }
      return latest.toLocaleString();
    },
    inherentRiskScore() {
      return this.reviewForm.likelihood * this.reviewForm.impact;
    },
    residualRiskScore() {
      const inherent = this.inherentRiskScore;
      const reductionMap = { 'Low': 0.15, 'Medium': 0.45, 'High': 0.85 };
      const reduction = reductionMap[this.reviewForm.controlEffectiveness] || 0;
      return Math.round(inherent * (1 - reduction));
    },
    controlEffectText() {
      const reductionMap = { 'Low': '15% reduction', 'Medium': '45% reduction', 'High': '85% reduction' };
      return `Control Effect: ${this.reviewForm.controlEffectiveness} (${reductionMap[this.reviewForm.controlEffectiveness] || '0%'})`;
    },
    isReviewerApprovalMode() {
      return this.selectedRisk && 
             this.selectedRisk.status === 'ACCEPTED_PENDING_APPROVAL' && 
             this.canApprove(this.selectedRisk);
    }
  },
  methods: {
    setStatusFilter(status) {
      this.filters.status = status;
      this.pagination.page = 1;
      this.loadRisks();
    },

    goToWorkflow(risk) {
      // Navigate to the Workflow page
      if (this.$router) {
        this.$router.push({ 
          path: '/risk/workflow',
          query: { riskInstanceId: risk.created_risk_instance_id || risk.id }
        });
      } else {
        window.location.href = `/risk/workflow?riskInstanceId=${risk.created_risk_instance_id || risk.id}`;
      }
    },

    clearUiFilters() {
      this.uiFilters = {
        search: '',
        type: '',
        category: '',
        confidence: '',
        sourceRef: '',
        functionalArea: '',
        velocityMin: 0
      };
    },
    toggleSourceFilter(sourceValue) {
      // Clicking the active chip removes the filter (shows all sources)
      this.filters.source = this.filters.source === sourceValue ? '' : sourceValue;
      this.pagination.page = 1;
      this.loadRisks();
    },

    openScheduleModal() {
      this.showScheduleModal = true;
      this.loadSchedules();
    },
    closeScheduleModal() {
      this.showScheduleModal = false;
    },
    async loadSchedules() {
      try {
        const response = await apiService.get(API_ENDPOINTS.SYSTEM_RISKS_SCHEDULES);
        if (response && (response.status === 'success' || response.data)) {
          this.activeSchedules = response.data.schedules || [];
        }
      } catch (error) {
        console.error('Error loading schedules:', error);
      }
    },
    async saveSchedule() {
      this.scheduling = true;
      try {
        const response = await apiService.post(API_ENDPOINTS.SYSTEM_RISKS_SCHEDULE_CREATE, this.scheduleForm);
        if (response && (response.status === 'success' || response.data)) {
          this.$notify?.({ type: 'success', title: 'Scheduled', text: 'AI Risk analysis schedule created successfully.' });
          this.loadSchedules();
          this.closeScheduleModal();
        }
      } catch (error) {
        console.error('Error saving schedule:', error);
        this.$notify?.({ type: 'error', title: 'Error', text: error.response?.data?.error || 'Failed to create schedule.' });
      } finally {
        this.scheduling = false;
      }
    },
    async deleteSchedule(id) {
      if (!confirm('Are you sure you want to delete this schedule?')) return;
      try {
        await apiService.delete(API_ENDPOINTS.SYSTEM_RISKS_SCHEDULE_DETAIL(id));
        this.loadSchedules();
      } catch (error) {
        console.error('Error deleting schedule:', error);
      }
    },
    formatFrequency(type) {
      const map = {
        daily: 'Daily',
        recurring: 'Weekly',
        monthly: 'Monthly',
        quarterly: 'Quarterly',
        yearly: 'Yearly',
        one_minute: 'Every Minute (Test)'
      };
      return map[type] || type;
    },

    statusLabel(status) {
      const labels = {
        'PENDING_REVIEW': 'Pending Review',
        'ACCEPTED_PENDING_APPROVAL': 'Approval Pending',
        'APPROVED_ADDED': 'Added to Register',
        'REJECTED': 'Rejected'
      };
      return labels[status] || status;
    },
    statusClass(statusValue) {
      const normalized = String(statusValue || '').trim().toUpperCase();
      if (normalized === 'ACCEPTED_PENDING_APPROVAL') return 'pending-approval';
      if (normalized === 'APPROVED_ADDED') return 'approved';
      if (normalized === 'REJECTED') return 'rejected';
      return '';
    },

    async loadStats() {
      try {
        const data = await apiService.get(API_ENDPOINTS.SYSTEM_RISKS_STATS, {}, { background: true });
        if (data) {
          const s = data.stats || {};
          this.stats = {
            pendingCount: s.pending_count ?? 0,
            pendingApprovalCount: s.pending_approval_count ?? 0,
            acceptedCount: s.accepted_count ?? 0,
            rejectedCount: s.rejected_count ?? 0
          };
        }
      } catch (error) {
        console.error('Error loading stats:', error);
      }
    },

    async loadRisks() {
      this.loading = true;
      try {
        const params = new URLSearchParams({
          page: this.pagination.page,
          page_size: this.pagination.pageSize ?? 10,
          ...this.filters
        });
        
        const response = await apiService.get(`${API_ENDPOINTS.SYSTEM_RISKS_LIST}?${params}`);
        if (response && response.data) {
          // Transform API data to match component expectations
          this.risks = response.data.map(item => ({
            id: item.id,
            category: item.category || 'Unknown',
            confidence: item.confidence_score || 0,
            title: item.risk_title || '',
            description: item.risk_description || '',
            type: item.risk_type || 'Current',
            criticality: item.criticality || 'Medium',
            source: item.source_title || item.source_ref || '',
            sourceRefId: this.extractSourceRefId(item.source_ref || ''),
            sourceModule: (item.source_module === 'INTEGRATION' && (item.source_ref || '').startsWith('External:')) ? 'EXTERNAL_SOURCES' : item.source_module,
            createdAtRaw: item.created_at || null,
            detected: this.formatDate(item.created_at),
            likelihood: item.likelihood || 5,
            impact: item.impact || 5,
            exposure: item.exposure_rating || 0,
            priority: item.priority || 'Medium',
            velocity: item.velocity_score || 0,
            functionalArea: item.functional_area || 'General',
            businessImpact: Array.isArray(item.business_impact) ? item.business_impact : (item.business_impact ? [item.business_impact] : []),
            possibleDamage: item.possible_damage || '',
            mitigation: (Array.isArray(item.mitigation_steps) && item.mitigation_steps.length > 0) 
              ? item.mitigation_steps[0] 
              : (item.mitigation_steps || 'No mitigation defined'),
            mitigationSteps: Array.isArray(item.mitigation_steps) ? item.mitigation_steps : (item.mitigation_steps ? [item.mitigation_steps] : []),
            status: String(item.status || '').trim().toUpperCase(),
            riskInstanceId: item.risk_instance_id || null, // Add risk instance ID for workflow
            reviewerId: item.reviewer_id || null,
            aiReasoning: item.ai_reasoning || '',
            aiMetadata: item.ai_metadata || {},
            confidenceJustification: item.confidence_justification || (item.ai_metadata?.confidence_justification || ''),
            confidenceFactors: Array.isArray(item.confidence_factors)
              ? item.confidence_factors
              : (Array.isArray(item.ai_metadata?.confidence_factors) ? item.ai_metadata.confidence_factors : [])
          }));
          // Backend returns snake_case pagination keys; normalize to component camelCase.
          this.pagination = {
            page: response.pagination.page,
            pageSize: response.pagination.page_size ?? response.pagination.pageSize ?? 10,
            totalCount: response.pagination.total_count ?? response.pagination.totalCount ?? 0,
            totalPages: response.pagination.total_pages ?? response.pagination.totalPages ?? 0
          };
        }
      } catch (error) {
        console.error('Error loading risks:', error);
        this.$notify?.({
          type: 'error',
          title: 'Error',
          text: 'Failed to load system identified risks.'
        });
      } finally {
        this.loading = false;
      }
    },
    async openSourceDrawer(risk) {
      this.sourceDrawerOpen = true;
      this.sourceDrawerLoading = true;
      this.sourceDrawerRisk = { ...risk };
      this.sourceDrawerDetail = null;
      try {
        const response = await apiService.get(API_ENDPOINTS.SYSTEM_RISKS_DETAIL(risk.id));
        if (response && response.data) {
          const d = response.data || {};
          this.sourceDrawerDetail = d.source_details || null;
          this.sourceDrawerRisk = {
            ...risk,
            sourceRefId: this.extractSourceRefId(d.source_ref || risk.source || ''),
            detected: this.formatDate(d.created_at || risk.createdAtRaw),
            aiReasoning: d.ai_reasoning || risk.aiReasoning || risk.description,
            status: d.status || risk.status
          };
        }
      } catch (error) {
        console.error('Error loading source details:', error);
      } finally {
        this.sourceDrawerLoading = false;
      }
    },
    closeSourceDrawer() {
      this.sourceDrawerOpen = false;
      this.sourceDrawerLoading = false;
      this.sourceDrawerRisk = null;
    },
    extractSourceRefId(sourceRef) {
      if (!sourceRef) return '';
      const match = sourceRef.match(/#(\d+)/);
      return match ? `#${match[1]}` : sourceRef;
    },
    hasRationale(risk, field) {
      if (!risk) return false;
      const rationale = risk.aiMetadata?.per_field_rationale || risk.ai_metadata?.per_field_rationale;
      if (!rationale) return false;
      return !!rationale[field];
    },
    getRationale(risk, field) {
      if (!risk) return '';
      const rationale = risk.aiMetadata?.per_field_rationale || risk.ai_metadata?.per_field_rationale;
      return rationale?.[field] || `The AI selected this ${field.replace('_', ' ')} by analyzing the relationship between the source incident's description and established risk patterns in the GRC database.`;
    },
    toggleReasoning(riskId) {
      const idx = this.expandedReasoning.indexOf(riskId);
      if (idx > -1) {
        this.expandedReasoning.splice(idx, 1);
      } else {
        this.expandedReasoning.push(riskId);
      }
    },
    isExpandedReasoning(riskId) {
      return this.expandedReasoning.includes(riskId);
    },
    isFieldChanged(field) {
      if (!this.originalAiValues || this.originalAiValues[field] === undefined || this.originalAiValues[field] === '' || this.originalAiValues[field] === null) return false;
      const current = this.reviewForm[field];
      const original = this.originalAiValues[field];
      
      if (Array.isArray(current)) {
        return JSON.stringify([...current].sort()) !== JSON.stringify([...original].sort());
      }
      return current !== original;
    },
    getOriginalValueDisplay(field) {
      const val = this.originalAiValues[field];
      if (val === undefined || val === '' || val === null) return 'Not suggested by AI';
      return val;
    },

    async runManualScan() {
      if (this.selectedSources.length === 0 && this.selectedSubFolderIds.length === 0 && !this.runChecklist) {
        this.$notify?.({ type: 'warn', title: 'No Source Selected', text: 'Please select at least one module, folder, or the checklist to scan.' });
        return;
      }

      this.loading = true;
      try {
        const payload = {
          limit: 10,
          source_types: this.selectedSources,
          subfolder_ids: this.selectedSubFolderIds,
          document_ids: this.selectedDocumentIds,
          external_urls: this.selectedExternalUrls,
          run_checklist: this.runChecklist
        };
        const response = await apiService.post(API_ENDPOINTS.SYSTEM_RISKS_RUN_SCAN_MANUAL, payload, { timeout: 600000 }); // 10 minute timeout for AI analysis
        
        if (response) {
          this.$notify?.({
            type: 'success',
            title: 'Scan Complete',
            text: response.message || 'Multi-source scan initiated successfully.'
          });
          
          // Reload data
          await this.loadStats();
          await this.loadRisks();
        }
      } catch (error) {
        console.error('Error running multi-source scan:', error);
        this.$notify?.({
          type: 'error',
          title: 'Scan Failed',
          text: error.response?.data?.message || error.message || 'Failed to run multi-source risk scan.'
        });
      } finally {
        this.loading = false;
      }
    },
    async loadExternalSources() {
      this.loadingExternalSources = true;
      try {
        const response = await apiService.get(API_ENDPOINTS.SYSTEM_RISKS_EXTERNAL_SOURCES);
        if (response && response.data) {
          this.availableExternalSources = response.data;
        }
      } catch (error) {
        console.error('Error loading external sources:', error);
      } finally {
        this.loadingExternalSources = false;
      }
    },

    async loadCompanyFolders() {
      try {
        const response = await apiService.get(API_ENDPOINTS.COMPANY_FOLDERS);
        if (response) {
          this.companyFolders = response.folders || (Array.isArray(response) ? response : (response.data || []));
        }
      } catch (error) {
        console.error('Error loading company folders:', error);
      }
    },

    async onFolderChange() {
      this.subFolders = [];
      this.selectedSubFolderIds = [];
      this.subfolderDocuments = {};
      this.selectedDocumentIds = [];
      this.selectedFolderCode = '';
      if (!this.selectedFolderId) return;
      const selectedFolder = (this.companyFolders || []).find(
        (folder) => String(folder.id) === String(this.selectedFolderId)
      );
      this.selectedFolderCode = selectedFolder?.code || '';

      try {
        const response = await apiService.get(API_ENDPOINTS.COMPANY_SUBFOLDERS(this.selectedFolderId));
        if (response) {
          this.subFolders = response.subfolders || (Array.isArray(response) ? response : (response.data || []));
        }
      } catch (error) {
        console.error('Error loading subfolders:', error);
      }
    },

    async onSubfolderToggle(sub) {
      if (this.selectedSubFolderIds.includes(sub.id) && !this.subfolderDocuments[sub.id]) {
        this.loadingDocuments[sub.id] = true;
        try {
          const queryParams = new URLSearchParams({
            subfolder_code: sub.code || '',
            page_size: '100'
          });
          if (this.selectedFolderCode) {
            queryParams.set('company_code', this.selectedFolderCode);
          }
          const response = await apiService.get(`${API_ENDPOINTS.DOCUMENTS_LIST}?${queryParams.toString()}`);
          if (response && response.documents) {
            this.subfolderDocuments[sub.id] = response.documents;
          } else {
            this.subfolderDocuments[sub.id] = [];
          }
        } catch (error) {
          console.error(`Error loading documents for subfolder ${sub.id}:`, error);
          this.subfolderDocuments[sub.id] = [];
        } finally {
          this.loadingDocuments[sub.id] = false;
        }
      }
    },

    toggleSourceSelection(source) {
      const idx = this.selectedSources.indexOf(source);
      if (idx > -1) {
        this.selectedSources.splice(idx, 1);
      } else {
        this.selectedSources.push(source);
      }
    },

    getSourceIcon(source) {
      const icons = {
        'COMPLIANCE': 'fas fa-shield-alt',
        'AUDIT': 'fas fa-search-dollar',
        'INCIDENT': 'fas fa-exclamation-triangle',
        'EVENT': 'fas fa-calendar-check',
        'EXTERNAL_SOURCES': 'fas fa-globe',
        'INTEGRATION': 'fas fa-file-alt'
      };
      return icons[source] || 'fas fa-cube';
    },

    startTestAnalysisPolling() {
      this.stopTestAnalysisPolling();
      this.testAnalysis.pollTimer = setInterval(async () => {
        if (!this.testAnalysis.jobId) return;
        try {
          const response = await apiService.get(API_ENDPOINTS.SYSTEM_RISKS_RUN_TEST_ANALYSIS_STATUS(this.testAnalysis.jobId));
          const job = response?.job || {};
          this.testAnalysis.processed = job.processed || 0;
          this.testAnalysis.total = job.total || 0;
          this.testAnalysis.progressPct = job.progress_pct || 0;
          this.testAnalysis.lastRecord = job.last_record || null;

          if (job.state === 'completed') {
            this.stopTestAnalysisPolling();
            this.testAnalysis.active = false;
            this.testAnalysis.cancelling = false;
            this.$notify?.({
              type: 'success',
              title: 'Risk Test Analysis Complete',
              text: `Processed ${job.processed || 0} records, created ${(job.results && job.results.created) || 0} risk candidates.`
            });
            await this.loadStats();
            await this.loadRisks();
          } else if (job.state === 'cancelled') {
            this.stopTestAnalysisPolling();
            this.testAnalysis.active = false;
            this.testAnalysis.cancelling = false;
            this.$notify?.({
              type: 'info',
              title: 'Risk Test Analysis Cancelled',
              text: `Stopped at ${job.processed || 0} processed records.`
            });
            await this.loadStats();
            await this.loadRisks();
          } else if (job.state === 'failed') {
            this.stopTestAnalysisPolling();
            this.testAnalysis.active = false;
            this.testAnalysis.cancelling = false;
            this.$notify?.({
              type: 'error',
              title: 'Risk Test Analysis Failed',
              text: job.error || 'An unexpected error occurred during analysis.'
            });
          }
        } catch (error) {
          console.error('Error polling analysis status:', error);
          this.stopTestAnalysisPolling();
        }
      }, 3000);
    },

    stopTestAnalysisPolling() {
      if (this.testAnalysis.pollTimer) {
        clearInterval(this.testAnalysis.pollTimer);
        this.testAnalysis.pollTimer = null;
      }
    },

    async cancelRiskTestAnalysis() {
      if (!this.testAnalysis.jobId) return;
      this.testAnalysis.cancelling = true;
      try {
        await apiService.post(API_ENDPOINTS.SYSTEM_RISKS_RUN_TEST_ANALYSIS_CANCEL(this.testAnalysis.jobId), {});
        this.$notify?.({
          type: 'info',
          title: 'Cancelling',
          text: 'Cancellation requested. Waiting for current record to finish.'
        });
      } catch (error) {
        this.testAnalysis.cancelling = false;
        console.error('Error cancelling risk test analysis:', error);
        this.$notify?.({
          type: 'error',
          title: 'Cancel Failed',
          text: 'Unable to cancel analysis.'
        });
      }
    },

    async openReview(risk) {
      this.selectedRisk = risk;
      const meta = risk.aiMetadata || {};
      
      this.originalAiValues = {
        title: meta.risk_title || '',
        type: meta.risk_type || '',
        category: meta.category || '',
        criticality: meta.criticality || '',
        description: meta.risk_description || '',
        possibleDamage: meta.possible_damage || '',
        businessImpact: Array.isArray(meta.business_impact) ? [...meta.business_impact] : [],
        likelihood: meta.likelihood || 5,
        impact: meta.impact || 5,
        velocity: meta.velocity_score || 5,
        controlEffectiveness: meta.control_effectiveness || 'Low',
        frameworkReference: meta.framework_reference || '',
        functionalArea: meta.functional_area || 'IT',
        mitigationSteps: Array.isArray(meta.mitigation_steps) ? [...meta.mitigation_steps] : []
      };

      try {
        const response = await apiService.get(API_ENDPOINTS.SYSTEM_RISKS_DETAIL(risk.id));
        if (response && response.data) {
          const data = response.data;
          const currentMeta = data.ai_metadata || {};
          
          this.selectedRisk = {
            ...risk,
            description: data.risk_description || risk.description,
            possibleDamage: data.possible_damage || risk.possibleDamage,
            aiReasoning: data.ai_reasoning || risk.aiReasoning
          };

          this.reviewForm = {
            title: data.risk_title || '',
            type: this.getValidOption(data.risk_type || risk.type, this.typeOptions, true),
            category: this.getValidOption(data.category || risk.category, this.categoryOptions, true),
            criticality: this.getValidOption(data.criticality || risk.criticality, ['Low', 'Medium', 'High', 'Critical']),
            description: data.risk_description || '',
            possibleDamage: data.possible_damage || '',
            businessImpact: Array.isArray(data.business_impact) ? [...data.business_impact] : (data.business_impact ? [data.business_impact] : []),
            likelihood: data.likelihood || 5,
            impact: data.impact || 5,
            velocity: data.velocity_score || currentMeta.velocity_score || 5,
            controlEffectiveness: this.getValidOption(currentMeta.control_effectiveness || 'Low', this.controlEffectivenessOptions),
            frameworkReference: currentMeta.framework_reference || '',
            functionalArea: this.getValidOption(data.functional_area || 'IT', this.functionalAreaOptions, true),
            riskOwner: data.user_id || this.currentUser?.id || this.currentUser?.UserId || '',
            reviewer: data.reviewer_id || '',
            notes: '',
            priority: data.priority || 'Medium',
            mitigationSteps: Array.isArray(data.mitigation_steps) ? [...data.mitigation_steps] : (data.mitigation_steps ? [data.mitigation_steps] : [...(risk.mitigationSteps || [])]),
            complianceId: currentMeta.review_overrides?.compliance_id ?? null,
            justifications: currentMeta.review_overrides?.justifications || {
              likelihood: '',
              impact: '',
              velocity: '',
              controlEffectiveness: '',
              frameworkReference: '',
              functionalArea: '',
              businessImpact: ''
            }
          };
        }
      } catch (error) {
        console.error('Error loading risk details:', error);
      }
    },

    async acceptRisk() {
      if (!this.selectedRisk) return;
      
      try {
        const response = await apiService.post(API_ENDPOINTS.SYSTEM_RISKS_ACCEPT(this.selectedRisk.id), {
          risk_title: this.reviewForm.title,
          risk_type: this.reviewForm.type,
          category: this.reviewForm.category,
          criticality: this.reviewForm.criticality,
          risk_description: this.reviewForm.description,
          possible_damage: this.reviewForm.possibleDamage,
          business_impact: this.reviewForm.businessImpact,
          likelihood: this.reviewForm.likelihood,
          impact: this.reviewForm.impact,
          exposure_rating: this.inherentRiskScore,
          residual_risk_score: this.residualRiskScore,
          velocity_score: this.reviewForm.velocity,
          control_effectiveness: this.reviewForm.controlEffectiveness,
          framework_reference: this.reviewForm.frameworkReference,
          risk_owner: this.reviewForm.riskOwner,
          reviewer: this.reviewForm.reviewer,
          assigner_id: this.currentUser?.UserId || this.currentUser?.id,
          notes: this.reviewForm.notes,
          functional_area: this.reviewForm.functionalArea,
          priority: this.reviewForm.priority,
          mitigation_steps: (this.reviewForm.mitigationSteps || []).filter(Boolean),
          compliance_id: this.reviewForm.complianceId,
          justifications: this.reviewForm.justifications
        });
        
        if (response) {
          this.$notify?.({
            type: 'success',
            title: 'Accepted',
            text: response.message || 'Risk accepted successfully'
          });
          
          this.closeReview();
          await this.loadStats();
          await this.loadRisks();
        }
      } catch (error) {
        console.error('Error accepting risk:', error);
        this.$notify?.({
          type: 'error',
          title: 'Error',
          text: 'Failed to accept risk.'
        });
      }
    },

    async saveDraft() {
      if (!this.selectedRisk) return;
      
      try {
        const response = await apiService.put(API_ENDPOINTS.SYSTEM_RISKS_REVIEW(this.selectedRisk.id), {
          risk_title: this.reviewForm.title,
          risk_type: this.reviewForm.type,
          category: this.reviewForm.category,
          criticality: this.reviewForm.criticality,
          risk_description: this.reviewForm.description,
          possible_damage: this.reviewForm.possibleDamage,
          business_impact: this.reviewForm.businessImpact,
          likelihood: this.reviewForm.likelihood,
          impact: this.reviewForm.impact,
          velocity_score: this.reviewForm.velocity,
          control_effectiveness: this.reviewForm.controlEffectiveness,
          framework_reference: this.reviewForm.frameworkReference,
          risk_owner: this.reviewForm.riskOwner,
          reviewer: this.reviewForm.reviewer,
          assigner_id: this.currentUser?.UserId || this.currentUser?.id,
          notes: this.reviewForm.notes,
          functional_area: this.reviewForm.functionalArea,
          priority: this.reviewForm.priority,
          mitigation_steps: (this.reviewForm.mitigationSteps || []).filter(Boolean),
          compliance_id: this.reviewForm.complianceId,
          justifications: this.reviewForm.justifications
        });
        
        if (response) {
          this.$notify?.({
            type: 'info',
            title: 'Draft Saved',
            text: response.message || 'Draft saved successfully'
          });
          this.closeReview();
          await this.loadRisks(); // Reload to show updated status
        }
      } catch (error) {
        console.error('Error saving draft:', error);
        this.$notify?.({
          type: 'error',
          title: 'Error',
          text: 'Failed to save draft.'
        });
      }
    },

    async rejectCurrent() {
      const reason = prompt('Please provide a reason for rejection:');
      if (!reason || !this.selectedRisk) return;
      
      try {
        const response = await apiService.post(API_ENDPOINTS.SYSTEM_RISKS_REJECT(this.selectedRisk.id), {
          reason: reason
        });
        
        if (response) {
          this.$notify?.({
            type: 'info',
            title: 'Rejected',
            text: response.message || 'Risk rejected'
          });
          
          this.closeReview();
          await this.loadStats();
          await this.loadRisks();
        }
      } catch (error) {
        console.error('Error rejecting risk:', error);
        this.$notify?.({
          type: 'error',
          title: 'Error',
          text: 'Failed to reject risk.'
        });
      }
    },

    async rejectFromList(id) {
      const reason = prompt('Please provide a reason for rejection:');
      if (!reason) return;
      
      try {
        const response = await apiService.post(API_ENDPOINTS.SYSTEM_RISKS_REJECT(id), {
          reason: reason
        });
        
        if (response) {
          this.$notify?.({
            type: 'info',
            title: 'Rejected',
            text: 'Risk rejected successfully.'
          });
          
          await this.loadStats();
          await this.loadRisks();
        }
      } catch (error) {
        console.error('Error rejecting risk:', error);
        this.$notify?.({
          type: 'error',
          title: 'Error',
          text: 'Failed to reject risk.'
        });
      }
    },

    checkSidebarState() {
      const sidebar = document.querySelector('.sidebar');
      this.isSidebarCollapsed = !!sidebar && sidebar.classList.contains('collapsed');
    },

    closeReview() {
      this.selectedRisk = null;
    },

    openWorkflowModal() {
      if (!this.selectedRisk) return;
      
      // Prepare risk data for workflow
      this.workflowRiskData = {
        id: this.selectedRisk.id,
        title: this.reviewForm.title,
        type: this.reviewForm.type,
        category: this.reviewForm.category,
        criticality: this.reviewForm.criticality,
        description: this.reviewForm.description,
        possibleDamage: this.reviewForm.possibleDamage,
        businessImpact: this.reviewForm.businessImpact,
        likelihood: this.reviewForm.likelihood,
        impact: this.reviewForm.impact,
        exposure: this.reviewForm.likelihood * this.reviewForm.impact,
        priority: this.reviewForm.priority,
        mitigationSteps: this.reviewForm.mitigationSteps,
        complianceId: this.reviewForm.complianceId,
        multiplierX: this.reviewForm.multiplierX,
        multiplierY: this.reviewForm.multiplierY,
        riskOwner: this.reviewForm.riskOwner,
        reviewer: this.reviewForm.reviewer,
        justifications: this.reviewForm.justifications
      };
      
      this.showWorkflowModal = true;
    },

    async directSendForApproval() {
      if (!this.reviewForm.riskOwner || !this.reviewForm.reviewer) {
        this.$notify?.({
          type: 'warning',
          title: 'Missing Selection',
          text: 'Please select both a Risk Owner and a Reviewer before sending for approval.'
        });
        return;
      }

      this.loading = true;
      try {
        const payload = {
          user_id: this.reviewForm.riskOwner,
          reviewer_id: this.reviewForm.reviewer,
          risk_data: {
            risk_title: this.reviewForm.title,
            risk_type: this.reviewForm.type,
            category: this.reviewForm.category,
            criticality: this.reviewForm.criticality,
            risk_description: this.reviewForm.description,
            possible_damage: this.reviewForm.possibleDamage,
            business_impact: this.reviewForm.businessImpact,
            likelihood: this.reviewForm.likelihood,
            impact: this.reviewForm.impact,
            exposure_rating: this.selectedRisk.exposure,
            priority: this.reviewForm.priority,
            mitigation_steps: this.reviewForm.mitigationSteps,
            compliance_id: this.reviewForm.complianceId,
            multiplier_x: this.reviewForm.multiplierX,
            multiplier_y: this.reviewForm.multiplierY,
            justifications: this.reviewForm.justifications
          }
        };

        const response = await apiService.post(API_ENDPOINTS.SYSTEM_RISKS_SEND_FOR_APPROVAL(this.selectedRisk.id), payload);

        if (response && (response.status === 'success' || response.data?.status === 'success')) {
          this.$notify?.({
            type: 'success',
            title: 'Success',
            text: 'Risk sent for approval successfully!'
          });
          
          this.closeReview();
          await this.loadStats();
          await this.loadRisks();
        }
      } catch (error) {
        console.error('Error creating workflow:', error);
        this.$notify?.({
          type: 'error',
          title: 'Error',
          text: error.response?.data?.message || 'Failed to create workflow.'
        });
      } finally {
        this.loading = false;
      }
    },

    closeWorkflowModal() {
      this.showWorkflowModal = false;
      this.workflowRiskData = null;
    },

    async onWorkflowCreated() {
      // Close the review modal and refresh data
      this.closeReview();
      this.closeWorkflowModal();
      await this.loadStats();
      await this.loadRisks();
      
      this.$notify?.({
        type: 'success',
        title: 'Workflow Created',
        text: `Risk sent for approval. User and reviewer have been notified.`
      });
    },

    canApprove(risk) {
      if (risk.status !== 'ACCEPTED_PENDING_APPROVAL') return false;
      const currentUserId = Number(
        localStorage.getItem('user_id')
        || sessionStorage.getItem('user_id')
        || 0
      );
      const assignedReviewerId = Number(risk.reviewerId || 0);
      return currentUserId > 0 && assignedReviewerId > 0 && currentUserId === assignedReviewerId;
    },

    async approveRisk(risk) {
      if (!risk.riskInstanceId) {
        this.$notify?.({
          type: 'error',
          title: 'Error',
          text: 'Risk instance ID not found.'
        });
        return;
      }

      const feedback = prompt('Please provide approval feedback (optional):');
      
      try {
        const response = await apiService.post(API_ENDPOINTS.SYSTEM_RISKS_WORKFLOW_APPROVE(risk.riskInstanceId), {
          feedback: feedback || ''
        });
        
        if (response) {
          // Immediate local UI update so user sees the change instantly
          const idx = (this.risks || []).findIndex((r) => r.id === risk.id);
          if (idx !== -1) {
            this.risks[idx].status = 'APPROVED_ADDED';
          }
          this.successModalTitle = 'Risk Approved';
          this.successModalMessage = response?.message || response?.data?.message || 'Action completed successfully.';
          this.showSuccessModal = true;

          // Close review modal and refresh server state
          this.closeReview();
          await this.loadStats();
          await this.loadRisks();
        }
      } catch (error) {
        console.error('Error approving risk:', error);
        this.$notify?.({
          type: 'error',
          title: 'Error',
          text: error.response?.data?.message || error.message || 'Failed to approve risk.'
        });
      }
    },

    async rejectRisk(risk) {
      if (!risk.riskInstanceId) {
        this.$notify?.({
          type: 'error',
          title: 'Error',
          text: 'Risk instance ID not found.'
        });
        return;
      }

      const feedback = prompt('Please provide rejection reason:');
      if (!feedback) return;
      
      try {
        const response = await apiService.post(API_ENDPOINTS.SYSTEM_RISKS_WORKFLOW_REJECT(risk.riskInstanceId), {
          feedback: feedback
        });

        if (response) {
          // Immediate local UI update so user sees the change instantly
          const idx = (this.risks || []).findIndex((r) => r.id === risk.id);
          if (idx !== -1) {
            this.risks[idx].status = 'REJECTED';
          }

          this.$notify?.({
            type: 'info',
            title: 'Rejected',
            text: response.message || 'Risk rejected'
          });

          // Close review modal and refresh server state
          this.closeReview();
          await this.loadStats();
          await this.loadRisks();
        }
      } catch (error) {
        console.error('Error rejecting risk:', error);
        this.$notify?.({
          type: 'error',
          title: 'Error',
          text: error.response?.data?.message || error.message || 'Failed to reject risk.'
        });
      }
    },

    toggleImpact(impact) {
      if (!Array.isArray(this.reviewForm.businessImpact)) {
        this.reviewForm.businessImpact = [];
      }
      if (this.reviewForm.businessImpact.includes(impact)) {
        this.reviewForm.businessImpact = this.reviewForm.businessImpact.filter((item) => item !== impact);
      } else {
        this.reviewForm.businessImpact.push(impact);
      }
    },
    addMitigationStep() {
      if (!Array.isArray(this.reviewForm.mitigationSteps)) this.reviewForm.mitigationSteps = [];
      this.reviewForm.mitigationSteps.push('');
    },
    removeMitigationStep(index) {
      this.reviewForm.mitigationSteps.splice(index, 1);
    },
    getConfidenceColor(score) {
      if (score >= 80) return '#2ed573';
      if (score >= 60) return '#ffa502';
      return '#ff4757';
    },
    getVelocityClass(velocity) {
      if (velocity >= 70) return 'velocity-high';
      if (velocity >= 40) return 'velocity-medium';
      return 'velocity-low';
    },
    getValidOption(val, options, allowCustom = false) {
      if (!val) return options[0];
      const match = options.find(opt => String(opt).toLowerCase() === String(val).toLowerCase());
      if (match) return match;
      
      if (allowCustom) {
        // Add to options if it's a custom value the user/AI wants
        options.push(val);
        return val;
      }
      return options[0];
    },

    formatDate(dateString) {
      if (!dateString) return 'Unknown';
      
      const date = new Date(dateString);
      const now = new Date();
      const diffMs = now - date;
      const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
      const diffDays = Math.floor(diffHours / 24);
      
      if (diffHours < 1) {
        return 'Just now';
      } else if (diffHours < 24) {
        return `${diffHours}h ago`;
      } else if (diffDays < 7) {
        return `${diffDays}d ago`;
      } else {
        return date.toLocaleDateString();
      }
    },
    async fetchUsers() {
      try {
        const response = await apiService.get(API_ENDPOINTS.USERS_FOR_DROPDOWN);
        const userData = response.users || response.data || (Array.isArray(response) ? response : []);
        if (Array.isArray(userData)) {
          this.userOptions = userData.map(u => ({
            id: u.UserId || u.id || u.user_id,
            name: u.UserName || u.name || u.username || 'Unknown User'
          })).filter(u => u.id);
          console.log(`Successfully loaded ${this.userOptions.length} users for dropdowns`);
        }
      } catch (error) {
        console.error('Error fetching users for dropdown:', error);
      }
    },
    async fetchCurrentUser() {
      try {
        const response = await apiService.get(API_ENDPOINTS.CURRENT_USER || `${window.location.origin}/api/current-user/`);
        if (response) {
          this.currentUser = response.user || response.data || response;
        }
      } catch (error) {
        console.error('Error fetching current user:', error);
      }
    },
    maskValue(val) {
      if (!val) return '***';
      if (val.length <= 4) return '****';
      const visible = val.substring(0, 3);
      const ext = val.includes('.') ? val.split('.').pop() : '';
      return `${visible}***${ext ? '.' + ext : ''}`;
    },
    displayDocumentName(doc) {
      const rawName = doc?.name || doc?.file_name || doc?.original_name || 'Untitled document';
      return String(rawName);
    },
    async fetchDepartments() {
      try {
        const response = await apiService.get(API_ENDPOINTS.DEPARTMENTS);
        const data = response.data || response;
        if (Array.isArray(data)) {
          this.functionalAreaOptions = [...new Set(data.map(d => d.DepartmentName).filter(Boolean))].sort();
          // Ensure 'IT' and 'Operations' are available as defaults
          if (!this.functionalAreaOptions.includes('IT')) this.functionalAreaOptions.push('IT');
          if (!this.functionalAreaOptions.includes('Operations')) this.functionalAreaOptions.push('Operations');
        }
      } catch (error) {
        console.error('Error fetching departments:', error);
      }
    }
  },
  async mounted() {
    this.checkSidebarState();
    document.addEventListener('click', this.checkSidebarState);

    try {
      void useRiskStore().prefetchRiskRegisterAndInstances({ force: false });
    } catch {
      /* non-fatal */
    }

    // Load initial data
    await this.loadStats();
    await this.loadRisks();
    await this.fetchUsers();
    await this.fetchCurrentUser();
    await this.loadCompanyFolders();
    await this.fetchDepartments();
    await this.loadExternalSources();
  },
  beforeUnmount() {
    this.stopTestAnalysisPolling();
    document.removeEventListener('click', this.checkSidebarState);
  }
};
</script>

<style src="./SystemIdentifiedRisks.css" scoped></style>

<style scoped>
/* Status badges */
.status-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.status-badge.pending-approval {
  background-color: #fff3cd;
  color: #856404;
  border: 1px solid #ffeaa7;
}

.status-badge.approved {
  background-color: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.status-badge.rejected {
  background-color: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

/* Clickable Stats */
.stat-card.clickable {
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.stat-card.clickable:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  border-color: #e2e8f0;
}

.stat-card.clickable.active {
  background-color: #f0f4ff;
  border-color: #6c5ce7;
  box-shadow: 0 4px 12px rgba(108, 92, 231, 0.1);
}

.stat-card.clickable.active .stat-label {
  color: #6c5ce7;
  font-weight: 600;
}

/* Ghost Buttons */
.btn-review-ghost {
  background: transparent;
  color: #6c5ce7;
  border: 1px solid #6c5ce7;
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.btn-review-ghost:hover {
  background: #f0f4ff;
  transform: translateY(-1px);
}

.status-badge-outline {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 600;
}

.status-badge-outline.in-workflow {
  color: #d97706;
  background: #fffbeb;
  border: 1px solid #fef3c7;
}

.status-badge-outline.approved {
  color: #059669;
  background: #ecfdf5;
  border: 1px solid #d1fae5;
}

.status-badge-outline.rejected {
  color: #dc2626;
  background: #fef2f2;
  border: 1px solid #fee2e2;
}

.status-badge-outline.pending {
  color: #4b5563;
  background: #f3f4f6;
  border: 1px solid #e5e7eb;
}

.risk-status-row {
  margin: 8px 0 4px;
}

/* Button styles for approval actions */
.btn.success {
  background-color: #28a745;
  color: white;
  border: 1px solid #28a745;
}

.btn.success:hover {
  background-color: #218838;
  border-color: #1e7e34;
}

.btn.danger {
  background-color: #dc3545;
  color: white;
  border: 1px solid #dc3545;
}

.btn.danger:hover {
  background-color: #c82333;
  border-color: #bd2130;
}

/* Scheduling Styles */
.btn-schedule {
  margin-left: 10px;
}

.scheduling-modal .modal-content {
  max-width: 500px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #4a5568;
}

.form-control {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.9rem;
  transition: all 0.2s;
}

.form-control:focus {
  outline: none;
  border-color: #6c5ce7;
  box-shadow: 0 0 0 3px rgba(108, 92, 231, 0.1);
}

.section-title {
  font-size: 1rem;
  font-weight: 700;
  color: #2d3748;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
}

.active-schedules {
  padding: 0 4px;
}

.schedule-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #f8fafc;
  border-radius: 8px;
  margin-bottom: 8px;
}

.schedule-info {
  display: flex;
  flex-direction: column;
}

.schedule-info strong {
  color: #2d3748;
  font-size: 0.9rem;
}

.schedule-info span {
  color: #718096;
  font-size: 0.8rem;
}

.card-status-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.card-status-badge.pending-review {
  background: #eff6ff;
  color: #2563eb;
  border: 1px solid #dbeafe;
  font-size: 0.5rem;
}

.card-status-badge.pending-approval {
  background: #fffbeb;
  color: #d97706;
  border: 1px solid #fef3c7;
}

.card-status-badge.approved {
  background: #ecfdf5;
  color: #059669;
  border: 1px solid #d1fae5;
}

.card-status-badge.rejected {
  background: #fef2f2;
  color: #dc2626;
  border: 1px solid #fee2e2;
}

/* Stat Value Colors */
.stat-value.pending {
  color: #d97706;
}

/* Pending Button */
.btn-review.pending {
  background: #f3f4f6 !important;
  color: #6b7280 !important;
  border: 1px solid #e5e7eb !important;
  cursor: not-allowed;
}

.field-change-alert {
  margin-top: 4px;
  padding: 6px 10px;
  background: #fffbeb;
  border-left: 3px solid #d97706;
  border-radius: 4px;
  font-size: 0.75rem;
  color: #92400e;
  display: flex;
  align-items: center;
  gap: 6px;
  animation: slideIn 0.3s ease-out;
}

.field-change-alert i {
  color: #d97706;
}

.field-change-alert span {
  font-weight: 600;
  text-decoration: line-through;
  opacity: 0.8;
  margin-left: 4px;
}

@keyframes slideIn {
  from { opacity: 0; transform: translateY(-5px); }
  to { opacity: 1; transform: translateY(0); }
}

.impact-buttons.disabled {
  opacity: 0.8;
  pointer-events: none;
}

.btn-review.pending i {
  margin-right: 6px;
}

/* Success Modal Styles */
.success-popup .success-modal-content {
  background: white;
  border-radius: 20px;
  padding: 40px;
  width: 100%;
  max-width: 400px;
  text-align: center;
  box-shadow: 0 20px 40px rgba(0,0,0,0.15);
  animation: modalScale 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  z-index: 10001;
  position: relative;
}

@keyframes modalScale {
  from { transform: scale(0.8); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}

.success-icon {
  width: 80px;
  height: 80px;
  background: #f0fdf4;
  color: #22c55e;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40px;
  margin: 0 auto 24px;
}

.success-popup h3 {
  margin: 0 0 12px;
  font-size: 24px;
  color: #1a202c;
}

.success-popup p {
  margin: 0 0 30px;
  color: #4a5568;
  line-height: 1.5;
}

.success-popup.modal-backdrop {
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Source Drawer Enhancements */
.source-header-main {
  display: flex;
  gap: 16px;
  align-items: center;
  padding: 16px;
  background: #f8fafc;
  border-radius: 12px;
  margin-bottom: 24px;
}

.source-icon {
  width: 48px;
  height: 48px;
  background: white;
  color: #6366f1;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.source-title-group {
  flex: 1;
}

.source-drawer-title {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 700;
  color: #1e293b;
  line-height: 1.4;
}

.source-drawer-type {
  font-size: 0.75rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.source-link-box {
  background: #f1f5f9;
  padding: 12px;
  border-radius: 8px;
  border: 1px dashed #cbd5e1;
}

.source-url {
  color: #3b82f6;
  text-decoration: none;
  font-size: 0.85rem;
  word-break: break-all;
  display: flex;
  align-items: center;
  gap: 8px;
}

.source-url:hover {
  text-decoration: underline;
}

.source-metadata-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin: 20px 0;
}

.source-reasoning-box {
  background: #fdf2f8;
  padding: 16px;
  border-radius: 8px;
  border-left: 4px solid #db2777;
  font-size: 0.9rem;
  color: #831843;
  line-height: 1.6;
}

.drawer-loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #64748b;
}

.drawer-loading-state i {
  font-size: 2rem;
  margin-bottom: 16px;
  color: #6366f1;
}

.repo-hint {
  margin: 0 0 10px;
  font-size: 12px;
  color: #6b7280;
}

.docs-meta {
  margin: 4px 0 8px;
  font-size: 12px;
  color: #4b5563;
}

.doc-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
