<template>
  <div class="FC_framework-comparison-container">
    <!-- Header -->
    <div class="FC_framework-comparison-header">
      <div class="FC_header-content">
        <h1 class="FC_framework-comparison-title">Framework Comparison</h1>
        <p class="FC_framework-comparison-subtitle">Analyze framework amendments and find matches</p>
      </div>
      <div class="FC_header-actions">
        <div class="FC_header-actions-left">
          <div class="FC_notification-wrapper">
            <button
              class="FC_notification-button"
              :disabled="loadingUpdateNotifications"
              @click="toggleUpdateNotifications"
              title="Framework amendment notifications"
            >
              <i class="fas fa-bell"></i>
              <span v-if="updateNotificationsCount" class="FC_notification-badge">
                {{ updateNotificationsCount }}
              </span>
            </button>

            <div v-if="showUpdateNotifications" class="FC_notification-popover">
              <div class="FC_notification-popover__header">
                <div class="FC_notification-popover__title">Framework updates</div>
                <span class="FC_notification-popover__count">{{ updateNotificationsCount }}</span>
              </div>

              <div v-if="loadingUpdateNotifications" class="FC_notification-popover__loading">
                <i class="fas fa-spinner fa-spin"></i>
                <span>Loading updates...</span>
              </div>

              <div v-else-if="updateNotifications.length === 0" class="FC_notification-popover__empty">
                No frameworks found.
              </div>

              <div v-else class="FC_notification-popover__list">
                <div
                  v-for="framework in updateNotifications"
                  :key="framework.framework_id"
                  class="FC_notification-row"
                  @click="selectFrameworkFromNotification(framework)"
                >
                  <div class="FC_notification-row__content">
                    <div class="FC_notification-row__name">
                      {{ framework.framework_name }}
                    </div>
                    <div
                      class="FC_notification-row__status"
                      :class="(framework.has_document || framework.document_available) ? 'has-update' : 'no-update'"
                    >
                      <i :class="(framework.has_document || framework.document_available) ? 'fas fa-check-circle' : 'fas fa-minus-circle'"></i>
                      <span>
                        {{ (framework.has_document || framework.document_available) ? 'Amendment available' : 'No amendment yet' }}
                      </span>
                    </div>
                  </div>
                  <div v-if="framework.last_comparison_date" class="FC_notification-row__date">
                    Last checked: {{ formatDate(framework.last_comparison_date) }}
                  </div>
                </div>
              </div>
            </div>
          </div>

          <button
            class="FC_check-updates-button"
            @click="checkWithUpdates"
            :disabled="checkingUpdates || !selectedFrameworkId"
          >
            <i v-if="!checkingUpdates" class="fas fa-clipboard-check"></i>
            <i v-else class="fas fa-spinner fa-spin"></i>
            {{ checkingUpdates ? 'Checking...' : 'Check the updates' }}
          </button>
        </div>
        <button class="FC_export-button" @click="exportComparison">
          <i class="fas fa-download"></i>
          Export Comparison
        </button>
      </div>
    </div>

    <!-- Framework Selection -->
    <div class="FC_framework-selection-card">
      <div class="FC_framework-selection-content">
        <div class="FC_framework-selector">
          <label class="FC_framework-label">Framework:</label>
          <select v-model="selectedFrameworkId" @change="onFrameworkChange" class="FC_framework-select">
            <option value="">Select Framework</option>
            <option v-for="framework in frameworkOptions" :key="framework.FrameworkId" :value="framework.FrameworkId">
              {{ framework.FrameworkName }} ({{ framework.amendment_count }} amendments)
            </option>
          </select>
        </div>
      </div>
    </div>

    <!-- Document Viewer Section -->
    <div v-if="selectedFrameworkId && documentInfo && documentInfo.has_document" class="FC_document-viewer-card">
      <div class="FC_document-viewer-content">
        <div class="FC_document-info">
          <div class="FC_document-icon">
            <i class="fas fa-file-pdf"></i>
          </div>
          <div class="FC_document-details">
            <h3 class="FC_document-name">{{ documentInfo.document.name }}</h3>
            <p class="FC_document-meta">
              Amendment Date: {{ documentInfo.document.amendment_date }} | 
              Downloaded: {{ formatDate(documentInfo.document.downloaded_date) }}
            </p>
            <div v-if="documentInfo.document.processed" class="FC_document-status FC_document-processed">
              <i class="fas fa-check-circle"></i>
              Processed on {{ formatDate(documentInfo.document.processed_date) }}
            </div>
            <div v-else class="FC_document-status FC_document-pending">
              <i class="fas fa-clock"></i>
              Awaiting Analysis
            </div>
          </div>
        </div>
        <div class="FC_document-actions">
          <button 
            @click="viewDocument" 
            class="FC_view-document-button"
            title="View document in new tab"
          >
            <i class="fas fa-eye"></i>
            View Document
          </button>
          <button 
            v-if="!documentInfo.document.processed"
            @click="startAnalysis" 
            :disabled="analyzingDocument"
            class="FC_start-analysis-button"
            title="Start AI processing of the document"
          >
            <i v-if="!analyzingDocument" class="fas fa-brain"></i>
            <i v-else class="fas fa-spinner fa-spin"></i>
            {{ analyzingDocument ? 'Analyzing...' : 'Start Analysis' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="FC_loading-state">
      <i class="fas fa-spinner fa-spin"></i>
      <p>Loading framework data...</p>
    </div>

    <!-- Error State -->
    <div v-if="error" class="FC_error-state">
      <i class="fas fa-exclamation-circle"></i>
      <p>{{ error }}</p>
    </div>

    <!-- No Amendment Data Message -->
    <div v-if="selectedFrameworkId && !loading && !targetData && !error" class="FC_no-amendment-message">
      <i class="fas fa-info-circle"></i>
      <h3>No Amendment Data Available</h3>
      <p>This framework does not have any amendment data in the Amendment column.</p>
      <p>Please check for updates or process an amendment document to view comparison data.</p>
    </div>

    <!-- Summary Statistics -->
    <div v-if="selectedFrameworkId && !loading && summaryStats" class="FC_summary-stats-grid">
      <div class="FC_summary-stat-card FC_clickable-card" @click="filterByType('new')" :class="{ 'FC_card-active': activeFilter === 'new' }">
        <div class="FC_summary-stat-content">
          <p class="FC_summary-stat-number FC_summary-stat-new">{{ complianceMatchingStats.newControls }}</p>
          <p class="FC_summary-stat-label">New Controls</p>
        </div>
      </div>
      <div class="FC_summary-stat-card FC_clickable-card" @click="filterByType('modified')" :class="{ 'FC_card-active': activeFilter === 'modified' }">
        <div class="FC_summary-stat-content">
          <p class="FC_summary-stat-number FC_summary-stat-modified">{{ complianceMatchingStats.modifiedControls }}</p>
          <p class="FC_summary-stat-label">Modified</p>
        </div>
      </div>
      <div class="FC_summary-stat-card FC_clickable-card" @click="filterByType('deprecated')" :class="{ 'FC_card-active': activeFilter === 'deprecated' }">
        <div class="FC_summary-stat-content">
          <p class="FC_summary-stat-number FC_summary-stat-removed">{{ complianceMatchingStats.deprecatedControls }}</p>
          <p class="FC_summary-stat-label">Deprecated</p>
        </div>
      </div>
    </div>
    <div 
      v-if="selectedFrameworkId && !loading && extractionSummary" 
      class="FC_summary-stats-grid FC_structured-summary-grid"
    >
      <div class="FC_summary-stat-card">
        <div class="FC_summary-stat-content">
          <p class="FC_summary-stat-number FC_summary-stat-structured">
            {{ extractionSummary.total_policies || 0 }}
          </p>
          <p class="FC_summary-stat-label">Extracted Policies</p>
        </div>
      </div>
      <div class="FC_summary-stat-card">
        <div class="FC_summary-stat-content">
          <p class="FC_summary-stat-number FC_summary-stat-structured">
            {{ extractionSummary.total_subpolicies || 0 }}
          </p>
          <p class="FC_summary-stat-label">Extracted Sub-Policies</p>
        </div>
      </div>
      <div class="FC_summary-stat-card">
        <div class="FC_summary-stat-content">
          <p class="FC_summary-stat-number FC_summary-stat-structured">
            {{ extractionSummary.total_compliance_records || 0 }}
          </p>
          <p class="FC_summary-stat-label">Extracted Compliances</p>
        </div>
      </div>
    </div>

    <!-- Filters -->
    <div v-if="selectedFrameworkId && !loading" class="FC_filters-card">
      <div class="FC_filters-content">
        <div class="FC_search-input-wrapper">
          <input
            v-model="searchTerm"
            placeholder="Search policies, controls..."
            class="FC_search-input"
          />
        </div>
        <select v-model="filter" class="FC_filter-select">
          <option value="all">Show All</option>
          <option value="changes">Show Only Changes</option>
        </select>
        <button 
          v-if="selectedControl"
          @click="clearMatches" 
          class="FC_clear-matches-button"
        >
          <i class="fas fa-times"></i>
          Clear Matches
        </button>
        <button 
          v-if="selectedFrameworkId && targetData"
          @click="matchCompliances" 
          :disabled="complianceMatchingInProgress"
          class="FC_match-compliances-button"
          title="Match all compliances from amendments"
        >
          <i v-if="!complianceMatchingInProgress" class="fas fa-check-circle"></i>
          <i v-else class="fas fa-spinner fa-spin"></i>
          {{ complianceMatchingInProgress ? 'Matching Compliances...' : 'Match Compliances' }}
        </button>
      </div>
    </div>
    
    <!-- Comparison View -->
    <div v-if="selectedFrameworkId && !loading && targetData && targetData.framework && targetData.framework.FrameworkId === selectedFrameworkId" class="FC_comparison-view">
      <!-- Left Side - Target (Amendments) -->
      <div class="FC_framework-side">
        <div class="FC_framework-side-header">
          <h3 class="FC_framework-side-title">
            <span class="FC_framework-badge FC_framework-badge-target">TARGET</span>
            {{ targetData.amendment && targetData.amendment.amendment_name ? targetData.amendment.amendment_name : 'No amendment data' }}
          </h3>
        </div>
        <div class="FC_framework-side-content">
          <!-- Structured sections (policies / sub-policies / compliances) -->
          <div v-if="hasStructuredSections" class="FC_structured-sections">
            <div 
              v-for="(section, sectionIndex) in structuredSections" 
              :key="sectionIndex" 
              class="FC_structured-section"
            >
              <div class="FC_section-header-row">
                <h4 class="FC_structured-section-title">
                  {{ section.section_info?.title || section.section_info?.name || `Section ${sectionIndex + 1}` }}
                </h4>
                <span v-if="section.section_info?.start_page" class="FC_section-page-info">
                  Pages {{ section.section_info.start_page }}<span v-if="section.section_info.end_page"> - {{ section.section_info.end_page }}</span>
                </span>
              </div>
              <p 
                v-if="section.section_info?.summary" 
                class="FC_structured-section-summary"
              >
                {{ section.section_info.summary }}
              </p>
              
              <div 
                v-for="(policy, policyIndex) in section.policies || []"
                :key="`${sectionIndex}-policy-${policyIndex}`"
                class="FC_policy-card"
              >
                <div class="FC_policy-card-header">
                  <div>
                    <h5>{{ policy.policy_title || policy.policy_name || `Policy ${policyIndex + 1}` }}</h5>
                    <p v-if="policy.scope" class="FC_policy-scope">{{ policy.scope }}</p>
                  </div>
                  <span v-if="policy.policy_type" class="FC_policy-type-pill">{{ policy.policy_type }}</span>
                </div>
                <p class="FC_policy-card-description" v-if="policy.policy_description">{{ policy.policy_description }}</p>
                
                <div class="FC_subpolicy-list">
                  <div 
                    v-for="(subpolicy, subIndex) in policy.subpolicies || []"
                    :key="`${sectionIndex}-policy-${policyIndex}-sub-${subIndex}`"
                    class="FC_subpolicy-card"
                  >
                    <div class="FC_subpolicy-card-header">
                      <div>
                        <h6>{{ subpolicy.subpolicy_title || subpolicy.SubPolicyName || `Sub-Policy ${subIndex + 1}` }}</h6>
                        <p v-if="subpolicy.control" class="FC_subpolicy-control">{{ subpolicy.control }}</p>
                      </div>
                      <span v-if="subpolicy.subpolicy_id" class="FC_subpolicy-pill">{{ subpolicy.subpolicy_id }}</span>
                    </div>
                    <p class="FC_subpolicy-card-description" v-if="subpolicy.subpolicy_description">
                      {{ subpolicy.subpolicy_description }}
                    </p>
                    
                    <div 
                      v-if="subpolicy.compliance_records && subpolicy.compliance_records.length"
                      class="FC_compliance-chip-list"
                    >
                      <div 
                        v-for="(compliance, compIndex) in subpolicy.compliance_records"
                        :key="compIndex"
                        class="FC_compliance-chip"
                      >
                        <strong class="FC_compliance-chip-title">
                          {{
                            compliance.ComplianceTitle ||
                            compliance.compliance_title ||
                            compliance.title ||
                            `Compliance ${compIndex + 1}`
                          }}
                        </strong>
                        <p class="FC_compliance-chip-desc">
                          {{
                            compliance.ComplianceItemDescription ||
                            compliance.compliance_description ||
                            compliance.description ||
                            compliance.requirement ||
                            ''
                          }}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <template v-else>
            <!-- Modified Controls -->
            <div v-if="filteredTargetModifiedControls.length > 0 && (activeFilter === null || activeFilter === 'modified' || activeFilter === 'deprecated')">
            <h4 class="FC_section-header">Modified Controls</h4>
            <div 
              v-for="control in filteredTargetModifiedControls" 
              :key="'modified-' + control.control_id" 
              :class="['FC_policy-item', 'FC_clickable-control', { 'FC_selected-control': selectedControl && selectedControl.control_id === control.control_id }]"
            >
              <div 
                class="FC_policy-header"
                @click.stop="togglePolicy(control.control_id, 'target')"
              >
                <button 
                  @click.stop="findMatches(control)" 
                  class="FC_find-match-button"
                  :disabled="matchingInProgress"
                  title="Find matching items"
                >
                  <i v-if="!matchingInProgress" class="fas fa-search-plus"></i>
                  <i v-else class="fas fa-spinner fa-spin"></i>
                </button>
                <i v-if="isPolicyExpanded(control.control_id, 'target')" class="fas fa-chevron-down FC_toggle-icon"></i>
                <i v-else class="fas fa-chevron-right FC_toggle-icon"></i>
                <div class="FC_policy-info">
                  <div class="FC_policy-title">
                    <span class="FC_policy-name">{{ control.control_id }} - {{ control.control_name }}</span>
                    <span :class="`FC_change-badge FC_change-badge-${control.change_type}`">
                      {{ control.change_type }}
                    </span>
                  </div>
                  <p class="FC_policy-description">{{ control.change_description }}</p>
                </div>
              </div>
              
              <div v-if="isPolicyExpanded(control.control_id, 'target')" class="FC_policy-content">
                <!-- Enhancements -->
                <div v-if="control.enhancements && control.enhancements.length > 0" class="FC_enhancement-section">
                  <h5>Enhancements:</h5>
                  <ul>
                    <li v-for="(enhancement, idx) in control.enhancements" :key="idx">{{ enhancement }}</li>
                  </ul>
                </div>
                
                <!-- Related Controls -->
                <div v-if="control.related_controls && control.related_controls.length > 0" class="FC_related-section">
                  <h5>Related Controls:</h5>
                  <p>{{ control.related_controls.join(', ') }}</p>
                </div>
                
                <!-- Sub-policies -->
                <div v-if="control.sub_policies && control.sub_policies.length > 0">
                  <div 
                    v-for="subPolicy in control.sub_policies" 
                    :key="subPolicy.sub_policy_name" 
                    class="FC_sub-policy-item"
                  >
                    <div class="FC_sub-policy-header">
                      <span class="FC_sub-policy-name">{{ subPolicy.sub_policy_name }}</span>
                      <span :class="`FC_change-badge FC_change-badge-${subPolicy.change_type}`">
                        {{ subPolicy.change_type }}
                      </span>
                    </div>
                    <div class="FC_sub-policy-content">
                      <p class="FC_sub-policy-description">{{ subPolicy.change_description }}</p>
                      <div v-if="subPolicy.requirements && subPolicy.requirements.length > 0" class="FC_requirements-section">
                        <h6>Requirements:</h6>
                        <ul>
                          <li v-for="(req, idx) in subPolicy.requirements" :key="idx">{{ req }}</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            </div>
            
            <!-- New Additions -->
            <div v-if="filteredTargetNewAdditions.length > 0 && (activeFilter === null || activeFilter === 'new')" class="FC_new-additions-section">
              <h4 class="FC_section-header">New Additions</h4>
              <div 
                v-for="addition in filteredTargetNewAdditions" 
                :key="'new-' + addition.control_id" 
                class="FC_policy-item FC_new-item"
              >
                <div class="FC_policy-header">
                  <div class="FC_policy-info">
                    <div class="FC_policy-title">
                      <span class="FC_policy-name">{{ addition.control_id }} - {{ addition.control_name }}</span>
                      <span class="FC_change-badge FC_change-badge-new">NEW</span>
                    </div>
                    <p class="FC_policy-description"><strong>Scope:</strong> {{ addition.scope }}</p>
                    <p class="FC_policy-description"><strong>Purpose:</strong> {{ addition.purpose }}</p>
                  </div>
                </div>
              </div>
            </div>
          </template>
        </div>
      </div>

      <!-- Right Side - Analysis (Matches Panel) -->
      <div class="FC_framework-side">
        <div class="FC_framework-side-header">
          <h3 class="FC_framework-side-title">
            <span class="FC_framework-badge FC_framework-badge-current">ANALYSIS</span>
            Control Matching
            <button 
              v-if="complianceMatches && complianceMatches.unmatched && complianceMatches.unmatched.length > 0"
              @click="openAddAllModal"
              class="FC_add-all-button"
              title="Add all unmatched compliances"
            >
              <i class="fas fa-plus-circle"></i>
              Add All
            </button>
          </h3>
        </div>
        <div class="FC_framework-side-content">
          <div v-if="complianceMatches" class="FC_compliance-matches-panel">
            <div class="FC_matches-header">
              <h4>
                <i class="fas fa-check-circle"></i>
                Compliance Matching Results
              </h4>
              <span class="FC_match-badge">
                <i class="fas fa-brain"></i>
                AI-Powered
              </span>
            </div>
            
            <!-- Summary -->
            <div class="FC_compliance-summary">
              <div class="FC_summary-stat">
                <span class="FC_summary-label">Total Compliances:</span>
                <span class="FC_summary-value">{{ complianceMatches.total_target || 0 }}</span>
              </div>
              <div class="FC_summary-stat FC_summary-matched">
                <span class="FC_summary-label">Matched:</span>
                <span class="FC_summary-value">{{ complianceMatches.matched_count || 0 }}</span>
              </div>
              <div class="FC_summary-stat FC_summary-unmatched">
                <span class="FC_summary-label">Not Following:</span>
                <span class="FC_summary-value">{{ complianceMatches.unmatched_count || 0 }}</span>
              </div>
            </div>
            
            <!-- Matched Compliances - Show only ONE match per target compliance -->
            <div v-if="complianceMatches.matched && complianceMatches.matched.length > 0" class="FC_compliance-section">
              <h5 class="FC_section-title FC_matched-title">
                <i class="fas fa-check-circle"></i>
                Matched Compliances
              </h5>
              <div class="FC_compliance-list">
                <div 
                  v-for="(match, index) in complianceMatches.matched" 
                  :key="'matched-' + index" 
                  :class="['FC_compliance-match-item', 'FC_matched-item', 'FC_expandable-item', { 'FC_expanded': expandedComplianceIndex === index }]"
                  @click="toggleComplianceDetails(index)"
                >
                  <div class="FC_compliance-match-header">
                    <div class="FC_match-status-icon FC_match-success">
                      <i class="fas fa-check"></i>
                    </div>
                    <div class="FC_compliance-match-info">
                      <h6 class="FC_target-compliance-title">
                        {{ match.target_compliance.compliance_title || 'Compliance' }}
                      </h6>
                      <p class="FC_target-compliance-desc">
                        {{ match.target_compliance.compliance_description || '' }}
                      </p>
                    </div>
                    <div class="FC_expand-icon">
                      <i :class="expandedComplianceIndex === index ? 'fas fa-chevron-up' : 'fas fa-chevron-down'"></i>
                    </div>
                  </div>
                  
                  <!-- Matched Compliance Details - Expandable -->
                  <div v-if="expandedComplianceIndex === index" class="FC_matched-compliance-details">
                    <div class="FC_detail-section">
                      <label>Policy:</label>
                      <span>{{ match.matched_compliance.policy_identifier || '' }} - {{ match.matched_compliance.policy_name || '' }}</span>
                    </div>
                    <div class="FC_detail-section">
                      <label>Policy Description:</label>
                      <span>{{ match.matched_compliance.policy_description || '' }}</span>
                    </div>
                    <div class="FC_detail-section">
                      <label>Sub-Policy:</label>
                      <span>{{ match.matched_compliance.subpolicy_identifier || '' }} - {{ match.matched_compliance.subpolicy_name || '' }}</span>
                    </div>
                    <div class="FC_detail-section">
                      <label>Sub-Policy Description:</label>
                      <span>{{ match.matched_compliance.subpolicy_description || '' }}</span>
                    </div>
                    <div class="FC_detail-section">
                      <label>Compliance Title:</label>
                      <span>{{ match.matched_compliance.compliance_title || '' }}</span>
                    </div>
                    <div class="FC_detail-section">
                      <label>Compliance Description:</label>
                      <span>{{ match.matched_compliance.compliance_description || '' }}</span>
                    </div>
                    <div v-if="match.matched_compliance.compliance_type" class="FC_detail-section">
                      <label>Compliance Type:</label>
                      <span>{{ match.matched_compliance.compliance_type }}</span>
                    </div>
                    <div v-if="match.matched_compliance.status" class="FC_detail-section">
                      <label>Status:</label>
                      <span>{{ match.matched_compliance.status }}</span>
                    </div>
                    <div v-if="match.matched_compliance.criticality" class="FC_detail-section">
                      <label>Criticality:</label>
                      <span>{{ match.matched_compliance.criticality }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Unmatched Compliances -->
            <div v-if="complianceMatches.unmatched && complianceMatches.unmatched.length > 0" class="FC_compliance-section">
              <h5 class="FC_section-title FC_unmatched-title">
                <i class="fas fa-exclamation-triangle"></i>
                Not Following These Compliances
              </h5>
              <div class="FC_compliance-list">
                <div 
                  v-for="(unmatch, index) in complianceMatches.unmatched" 
                  :key="'unmatched-' + index" 
                  class="FC_compliance-match-item FC_unmatched-item"
                >
                  <div class="FC_compliance-match-header">
                    <div class="FC_match-status-icon FC_match-warning">
                      <i class="fas fa-exclamation-triangle"></i>
                    </div>
                    <div class="FC_compliance-match-info">
                      <h6 class="FC_target-compliance-title">
                        {{ unmatch.target_compliance.compliance_title || 'Compliance' }}
                      </h6>
                      <p class="FC_target-compliance-desc">
                        {{ unmatch.target_compliance.compliance_description || '' }}
                      </p>
                    </div>
                    <button 
                      class="FC_add-compliance-button" 
                      @click.stop="openComplianceModal(unmatch)"
                      title="Add this compliance to framework"
                    >
                      <i class="fas fa-plus"></i>
                    </button>
                  </div>
                  <div class="FC_unmatched-message">
                    <i class="fas fa-times-circle"></i>
                    <span>{{ unmatch.message || 'We are not following this compliance' }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div v-else-if="!selectedControl" class="FC_analysis-placeholder">
            <i class="fas fa-search"></i>
            <p>Select a control from the left panel and click the search button to find matches.</p>
          </div>
          <div v-else-if="selectedControl && !controlMatches" class="FC_analysis-placeholder">
            <i class="fas fa-spinner fa-spin"></i>
            <p>Finding matches for: {{ selectedControl.control_id }}</p>
          </div>
          <div v-else class="FC_matches-panel">
            <div class="FC_matches-header">
              <h4>
                <i class="fas fa-link"></i>
                Best Matches for: {{ selectedControl.control_id }} - {{ selectedControl.control_name }}
              </h4>
              <span class="FC_match-badge">
                <i class="fas fa-brain"></i>
                AI-Powered
              </span>
            </div>
            <div class="FC_matches-list">
              <div 
                v-for="(match, index) in controlMatches" 
                :key="index" 
                class="FC_match-item"
              >
                <div class="FC_match-rank">{{ index + 1 }}</div>
                <div class="FC_match-info">
                  <div class="FC_match-type-badge">
                    <i :class="match.type === 'policy' ? 'fas fa-folder' : match.type === 'subpolicy' ? 'fas fa-file' : 'fas fa-check-circle'"></i>
                    {{ match.type.toUpperCase() }}
                  </div>
                  <p class="FC_match-path">{{ match.path }}</p>
                </div>
                <div class="FC_match-score">
                  <div class="FC_score-bar">
                    <div class="FC_score-fill" :style="{ width: (match.score * 100) + '%' }"></div>
                  </div>
                  <span class="FC_score-text">{{ (match.score * 100).toFixed(1) }}%</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Legend -->
    <div v-if="selectedFrameworkId && !loading" class="FC_legend-card">
      <div class="FC_legend-header">
        <h3 class="FC_legend-title">Legend</h3>
      </div>
      <div class="FC_legend-content">
        <div class="FC_legend-grid">
          <div class="FC_legend-section">
            <h4 class="FC_legend-section-title">Change Types</h4>
            <div class="FC_legend-items">
              <div class="FC_legend-item">
                <div class="FC_change-badge FC_change-badge-new">
                  <i class="fas fa-plus"></i>
                  <span>New</span>
                </div>
                <span class="FC_legend-description">New control added</span>
              </div>
              <div class="FC_legend-item">
                <div class="FC_change-badge FC_change-badge-modified">
                  <i class="fas fa-edit"></i>
                  <span>Modified</span>
                </div>
                <span class="FC_legend-description">Modified control</span>
              </div>
              <div class="FC_legend-item">
                <div class="FC_change-badge FC_change-badge-enhanced">
                  <i class="fas fa-arrow-up"></i>
                  <span>Enhanced</span>
                </div>
                <span class="FC_legend-description">Enhanced control</span>
              </div>
              <div class="FC_legend-item">
                <div class="FC_change-badge FC_change-badge-deprecated">
                  <i class="fas fa-minus"></i>
                  <span>Deprecated</span>
                </div>
                <span class="FC_legend-description">Deprecated control</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div v-if="showComplianceModal" class="FC_modal-backdrop">
      <div class="FC_modal">
        <div class="FC_modal-header">
          <h3>Add Compliance to Framework</h3>
          <button class="FC_modal-close" @click="closeComplianceModal">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="FC_modal-body">
          <div class="FC_modal-section">
            <h4>Policy Details</h4>
            <div class="FC_modal-field">
              <label>Policy Name</label>
              <input type="text" v-model="complianceForm.policy_name" />
            </div>
            <div class="FC_modal-field">
              <label>Policy Identifier</label>
              <input type="text" v-model="complianceForm.policy_identifier" />
            </div>
            <div class="FC_modal-field">
              <label>Policy Description</label>
              <textarea v-model="complianceForm.policy_description"></textarea>
            </div>
            <div class="FC_modal-grid">
              <div class="FC_modal-field">
                <label>Scope</label>
                <input type="text" v-model="complianceForm.policy_scope" />
              </div>
              <div class="FC_modal-field">
                <label>Objective</label>
                <input type="text" v-model="complianceForm.policy_objective" />
              </div>
            </div>
          </div>

          <div class="FC_modal-section">
            <h4>Sub-Policy Details</h4>
            <div class="FC_modal-field">
              <label>Sub-Policy Name</label>
              <input type="text" v-model="complianceForm.subpolicy_name" />
            </div>
            <div class="FC_modal-field">
              <label>Sub-Policy Identifier</label>
              <input type="text" v-model="complianceForm.subpolicy_identifier" />
            </div>
            <div class="FC_modal-field">
              <label>Description</label>
              <textarea v-model="complianceForm.subpolicy_description"></textarea>
            </div>
            <div class="FC_modal-field">
              <label>Control</label>
              <input type="text" v-model="complianceForm.subpolicy_control" />
            </div>
          </div>

          <div class="FC_modal-section">
            <h4>Compliance Details</h4>
            <div class="FC_modal-field">
              <label>Compliance Title</label>
              <input type="text" v-model="complianceForm.compliance_title" />
            </div>
            <div class="FC_modal-field">
              <label>Compliance Description</label>
              <textarea v-model="complianceForm.compliance_description"></textarea>
            </div>
            <div class="FC_modal-grid">
              <div class="FC_modal-field">
                <label>Compliance Type</label>
                <input type="text" v-model="complianceForm.compliance_type" />
              </div>
              <div class="FC_modal-field">
                <label>Criticality</label>
                <select v-model="complianceForm.criticality">
                  <option>Low</option>
                  <option>Medium</option>
                  <option>High</option>
                  <option>Critical</option>
                </select>
              </div>
            </div>
            <div class="FC_modal-grid">
              <div class="FC_modal-field">
                <label>Mandatory / Optional</label>
                <select v-model="complianceForm.mandatory">
                  <option>Mandatory</option>
                  <option>Optional</option>
                </select>
              </div>
              <div class="FC_modal-field">
                <label>Manual / Automatic</label>
                <select v-model="complianceForm.manual_automatic">
                  <option>Manual</option>
                  <option>Automatic</option>
                </select>
              </div>
            </div>
          </div>
          <p v-if="complianceSaveError" class="FC_modal-error">{{ complianceSaveError }}</p>
        </div>
        <div class="FC_modal-footer">
          <button class="FC_modal-secondary" @click="closeComplianceModal">Cancel</button>
          <button 
            class="FC_modal-primary"
            :disabled="submittingCompliance"
            @click="submitComplianceForm"
          >
            <span v-if="!submittingCompliance">Save Compliance</span>
            <span v-else><i class="fas fa-spinner fa-spin"></i> Saving...</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Progress Popup Modal -->
    <div v-if="showProgressModal" class="FC_progress-modal-backdrop">
      <div class="FC_progress-modal">
        <div class="FC_progress-modal-header">
          <h3><i class="fas fa-brain"></i> Analyzing Amendment Document</h3>
          <button class="FC_progress-cancel-btn" @click="cancelAnalysis" title="Cancel Analysis">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="FC_progress-modal-body">
          <div class="FC_progress-spinner-container">
            <div class="FC_progress-spinner"></div>
          </div>
          <p class="FC_progress-status-text">{{ analysisStatus }}</p>
          <div class="FC_progress-bar-container">
            <div class="FC_progress-bar">
              <div class="FC_progress-bar-fill" :style="{ width: analysisProgress + '%' }"></div>
            </div>
            <span class="FC_progress-percentage">{{ analysisProgress }}%</span>
          </div>
          <div class="FC_progress-steps">
            <div class="FC_progress-step" :class="{ active: currentAnalysisStep >= 1, completed: currentAnalysisStep > 1 }">
              <i class="fas fa-file-upload"></i>
              <span>Initializing</span>
            </div>
            <div class="FC_progress-step" :class="{ active: currentAnalysisStep >= 2, completed: currentAnalysisStep > 2 }">
              <i class="fas fa-search"></i>
              <span>Extracting</span>
            </div>
            <div class="FC_progress-step" :class="{ active: currentAnalysisStep >= 3, completed: currentAnalysisStep > 3 }">
              <i class="fas fa-brain"></i>
              <span>AI Processing</span>
            </div>
            <div class="FC_progress-step" :class="{ active: currentAnalysisStep >= 4, completed: currentAnalysisStep > 4 }">
              <i class="fas fa-check-circle"></i>
              <span>Complete</span>
            </div>
          </div>
        </div>
        <div class="FC_progress-modal-footer">
          <p class="FC_progress-note">You can navigate away - processing will continue in the background</p>
        </div>
      </div>
    </div>

    <!-- Add All Compliances Checklist Modal -->
    <div v-if="showAddAllModal" class="FC_modal-overlay-checklist" @click.self="closeAddAllModal">
      <div class="FC_modal-content FC_add-all-modal">
        <div class="FC_modal-header">
          <h3>Select Compliances to Add</h3>
          <button @click="closeAddAllModal" class="FC_modal-close">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="FC_modal-body">
          <div class="FC_checklist-container">
            <div 
              v-for="(unmatch, index) in complianceMatches.unmatched" 
              :key="'checklist-' + index"
              class="FC_checklist-item"
            >
              <label class="FC_checklist-label">
                <input 
                  type="checkbox" 
                  :value="index"
                  v-model="selectedCompliancesForAdd"
                  class="FC_checkbox"
                />
                <div class="FC_checklist-content">
                  <h6 class="FC_checklist-title">
                    {{ unmatch.target_compliance.compliance_title || 'Compliance' }}
                  </h6>
                  <p class="FC_checklist-description">
                    {{ unmatch.target_compliance.compliance_description || '' }}
                  </p>
                </div>
              </label>
            </div>
          </div>
          <div class="FC_checklist-summary">
            <p>
              <strong>{{ selectedCompliancesForAdd.length }}</strong> of 
              <strong>{{ complianceMatches.unmatched.length }}</strong> compliances selected
            </p>
          </div>
        </div>
        <div class="FC_modal-footer">
          <button class="FC_modal-secondary" @click="closeAddAllModal">Cancel</button>
          <button 
            class="FC_modal-primary"
            :disabled="selectedCompliancesForAdd.length === 0"
            @click="processSelectedCompliances"
          >
            <i class="fas fa-check"></i>
            Process ({{ selectedCompliancesForAdd.length }})
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import frameworkComparisonService from '@/services/frameworkComparisonService'
import { PopupService } from '@/modules/popup'

export default {
  name: 'FrameworkComparison',
  data() {
    return {
      frameworkOptions: [],
      selectedFrameworkId: '',
      loading: false,
      error: null,
      
      // Data
      targetData: null,
      summaryStats: null,
      
      // UI State
      expandedPoliciesTarget: new Set(),
      expandedSubPoliciesTarget: new Set(),
      searchTerm: '',
      filter: 'all',
      activeFilter: null,  // 'new', 'modified', 'deprecated', or null
      
      // Similarity Matching
      selectedControl: null,
      controlMatches: null,
      matchingInProgress: false,
      // AI matching is always enabled (OpenAI)
      
      // Compliance Matching
      complianceMatches: null,
      complianceMatchingInProgress: false,
      expandedComplianceIndex: null,  // Track which compliance is expanded
      checkingUpdates: false,
      updateNotifications: [],
      updateNotificationsCount: 0,
      loadingUpdateNotifications: false,
      showUpdateNotifications: false,
      showComplianceModal: false,
      complianceModalData: null,
      showAddAllModal: false,
      selectedCompliancesForAdd: [],  // Array of indices or IDs
      
      // Document Viewer
      documentInfo: null,
      analyzingDocument: false,
      
      // Analysis Progress
      showProgressModal: false,
      analysisProgress: 0,
      analysisStatus: 'Initializing analysis...',
      currentAnalysisStep: 0,
      analysisPollingInterval: null,
      backgroundAnalysisActive: false,
      stateSaveInterval: null,
      
      complianceForm: {
        policy_name: '',
        policy_identifier: '',
        policy_description: '',
        policy_scope: '',
        policy_objective: '',
        subpolicy_name: '',
        subpolicy_identifier: '',
        subpolicy_description: '',
        subpolicy_control: '',
        compliance_title: '',
        compliance_description: '',
        compliance_type: '',
        criticality: 'Medium',
        mandatory: 'Mandatory',
        manual_automatic: 'Manual'
      },
      complianceSaveError: '',
      submittingCompliance: false
    }
  },
  
  computed:{
    filteredTargetModifiedControls() {
      if (!this.targetData || !this.targetData.modified_controls) return []
      
      let controls = this.targetData.modified_controls
      
      // Apply search filter
      if (this.searchTerm) {
        const search = this.searchTerm.toLowerCase()
        controls = controls.filter(control => 
          (control.control_name && control.control_name.toLowerCase().includes(search)) ||
          (control.control_id && control.control_id.toLowerCase().includes(search)) ||
          (control.change_description && control.change_description.toLowerCase().includes(search))
        )
      }
      
      // Apply change filter
      if (this.filter === 'changes') {
        controls = controls.filter(control => control.change_type !== 'unchanged')
      }
      
      // Apply active filter from card click
      if (this.activeFilter === 'modified') {
        controls = controls.filter(control => control.change_type === 'modified')
      } else if (this.activeFilter === 'deprecated') {
        controls = controls.filter(control => control.change_type === 'deprecated' || control.change_type === 'removed')
      }
      
      return controls
    },
    
    filteredTargetNewAdditions() {
      if (!this.targetData || !this.targetData.new_additions) return []
      
      let additions = this.targetData.new_additions
      
      // Apply search filter
      if (this.searchTerm) {
        const search = this.searchTerm.toLowerCase()
        additions = additions.filter(addition => 
          (addition.control_name && addition.control_name.toLowerCase().includes(search)) ||
          (addition.control_id && addition.control_id.toLowerCase().includes(search)) ||
          (addition.scope && addition.scope.toLowerCase().includes(search))
        )
      }
      
      // Apply active filter from card click - only show if 'new' is selected
      if (this.activeFilter && this.activeFilter !== 'new') {
        return []
      }
      
      return additions
    },
    
    structuredSections() {
      if (!this.targetData || !Array.isArray(this.targetData.sections)) return []
      return this.targetData.sections
    },
    
    hasStructuredSections() {
      return this.structuredSections.length > 0
    },
    
    extractionSummary() {
      if (!this.targetData || !this.targetData.extraction_summary) return null
      return this.targetData.extraction_summary
    },
    
    complianceMatchingStats() {
      // If compliance matching has been done, use those results
      if (this.complianceMatches) {
        return {
          newControls: this.complianceMatches.unmatched_count || 0,  // Unmatched = new controls we're not following
          modifiedControls: this.complianceMatches.matched_count || 0,  // Matched = modified/existing controls
          deprecatedControls: 0  // Deprecated not available in compliance matching results
        }
      }
      
      // Otherwise fall back to summaryStats from framework comparison
      if (this.summaryStats) {
        return {
          newControls: this.summaryStats.new_controls || 0,
          modifiedControls: this.summaryStats.modified_controls || 0,
          deprecatedControls: this.summaryStats.deprecated_controls || 0
        }
      }
      
      // Default values
      return {
        newControls: 0,
        modifiedControls: 0,
        deprecatedControls: 0
      }
    }
  },
  
  async mounted() {
    await this.loadFrameworksWithAmendments()
    await this.applyFrameworkFromSession()
    await this.refreshUpdateNotifications()
    
    // Load and resume any background analysis (after framework is selected)
    // We'll check again in onFrameworkChange to ensure framework is set
    this.loadAnalysisState()
    
    // Listen for page visibility changes to pause/resume polling
    document.addEventListener('visibilitychange', this.handleVisibilityChange)
    
    // Save state periodically while analysis is running
    if (this.backgroundAnalysisActive) {
      this.stateSaveInterval = setInterval(() => {
        if (this.backgroundAnalysisActive) {
          this.saveAnalysisState()
        }
      }, 5000) // Save every 5 seconds
    }
  },
  
  beforeUnmount() {
    // Save state before unmounting so we can resume later
    if (this.backgroundAnalysisActive) {
      this.saveAnalysisState()
      console.log('💾 Saved analysis state before unmounting')
    }
    
    // Clean up intervals
    this.stopAnalysisPolling()
    if (this.stateSaveInterval) {
      clearInterval(this.stateSaveInterval)
      this.stateSaveInterval = null
    }
    
    // Remove event listener
    document.removeEventListener('visibilitychange', this.handleVisibilityChange)
  },
  
  activated() {
    // Vue keep-alive hook - when component is activated again
    if (this.selectedFrameworkId) {
      this.checkAndResumeAnalysis()
    }
  },
  
  handleVisibilityChange() {
    // When page becomes visible again, check and resume analysis
    if (!document.hidden && this.selectedFrameworkId) {
      this.checkAndResumeAnalysis()
    }
  },
  
  methods: {
    async loadFrameworksWithAmendments() {
      try {
        this.loading = true
        this.error = null
        
        const response = await frameworkComparisonService.getFrameworksWithAmendments()
        
        if (response.success) {
          this.frameworkOptions = response.data
        } else {
          this.error = response.error || 'Failed to load frameworks'
        }
      } catch (error) {
        this.error = 'Error loading frameworks: ' + error.message
        console.error('Error loading frameworks:', error)
      } finally {
        this.loading = false
      }
    },

    async refreshUpdateNotifications() {
      try {
        this.loadingUpdateNotifications = true
        const response = await frameworkComparisonService.getFrameworkUpdateNotifications()

        if (response && response.success) {
          this.updateNotifications = response.frameworks || []
          this.updateNotificationsCount = response.updated_count || 0
        } else {
          this.updateNotifications = []
          this.updateNotificationsCount = 0
        }
      } catch (error) {
        console.error('Error fetching update notifications:', error)
        this.updateNotifications = []
        this.updateNotificationsCount = 0
      } finally {
        this.loadingUpdateNotifications = false
      }
    },

    async toggleUpdateNotifications() {
      if (!this.showUpdateNotifications) {
        await this.refreshUpdateNotifications()
      }
      this.showUpdateNotifications = !this.showUpdateNotifications
    },

    async selectFrameworkFromNotification(framework) {
      if (!framework || !framework.framework_id) return
      this.selectedFrameworkId = framework.framework_id
      this.showUpdateNotifications = false
      await this.onFrameworkChange()
    },
    
    async applyFrameworkFromSession() {
      try {
        const response = await frameworkComparisonService.getSelectedFramework()
        
        if (response && response.success) {
          const selectedId = response.frameworkId
          
          if (selectedId) {
            const frameworkExists = this.frameworkOptions.find(
              framework => String(framework.FrameworkId) === String(selectedId)
            )
            
            if (frameworkExists) {
              this.selectedFrameworkId = frameworkExists.FrameworkId
              await this.onFrameworkChange()
              return
            } else {
              console.warn('Selected framework not found in options:', selectedId)
            }
          }
        }
        
        // No framework selected or not found - default to showing all frameworks
        this.selectedFrameworkId = ''
        await this.onFrameworkChange()
      } catch (error) {
        console.error('Error applying framework from session:', error)
      }
    },
    
    async onFrameworkChange() {
      // Clear all data immediately when framework changes
      this.targetData = null
      this.summaryStats = null
      this.selectedControl = null
      this.controlMatches = null
      this.complianceMatches = null
      this.expandedComplianceIndex = null
      this.documentInfo = null
      
      if (!this.selectedFrameworkId) {
        return
      }
      
      try {
        this.loading = true
        this.error = null
        
        // Store the selected framework ID to verify response matches
        const currentFrameworkId = this.selectedFrameworkId
        
        // Check and resume any background analysis for this framework
        this.checkAndResumeAnalysis()
        
        // Load target data, summary, and document info in parallel
        const [targetResponse, summaryResponse] = await Promise.all([
          frameworkComparisonService.getFrameworkTargetData(currentFrameworkId),
          frameworkComparisonService.getFrameworkComparisonSummary(currentFrameworkId)
        ])
        
        // Verify that the response is for the currently selected framework
        // If user switched frameworks while request was in flight, ignore the response
        if (this.selectedFrameworkId !== currentFrameworkId) {
          console.log('Framework changed during request, ignoring response')
          return
        }
        
        // Fetch document info separately (it sets this.documentInfo internally)
        await this.fetchDocumentInfo()
        
        // Only set data if it matches the selected framework
        if (targetResponse.success) {
          // Double-check that the response is for the correct framework
          if (targetResponse.framework && targetResponse.framework.FrameworkId === currentFrameworkId) {
            // Also verify that amendment data exists
            if (targetResponse.amendment && (targetResponse.sections || targetResponse.modified_controls || targetResponse.new_additions)) {
              this.targetData = targetResponse
            } else {
              // No amendment data available
              this.targetData = null
            }
          } else {
            console.warn('Response framework ID does not match selected framework', {
              responseFrameworkId: targetResponse.framework?.FrameworkId,
              selectedFrameworkId: currentFrameworkId
            })
            this.targetData = null
          }
        } else {
          // If no amendments found or error, clear targetData
          this.targetData = null
        }
        
        if (summaryResponse.success) {
          // Verify summary is for the correct framework
          if (summaryResponse.framework_id === currentFrameworkId) {
            this.summaryStats = summaryResponse.summary
          } else {
            this.summaryStats = null
          }
        } else {
          this.summaryStats = null
        }
        
      } catch (error) {
        this.error = 'Error loading framework data: ' + error.message
        console.error('Error loading framework data:', error)
        // Clear data on error
        this.targetData = null
        this.summaryStats = null
      } finally {
        this.loading = false
      }
    },
    
    togglePolicy(policyId, side) {
      if (side === 'target') {
        if (this.expandedPoliciesTarget.has(policyId)) {
          this.expandedPoliciesTarget.delete(policyId)
        } else {
          this.expandedPoliciesTarget.add(policyId)
        }
      }
    },
    
    toggleSubPolicy(subPolicyId, side) {
      if (side === 'target') {
        if (this.expandedSubPoliciesTarget.has(subPolicyId)) {
          this.expandedSubPoliciesTarget.delete(subPolicyId)
        } else {
          this.expandedSubPoliciesTarget.add(subPolicyId)
        }
      }
    },
    
    isPolicyExpanded(policyId, side) {
      return side === 'target' && this.expandedPoliciesTarget.has(policyId)
    },
    
    isSubPolicyExpanded(subPolicyId, side) {
      return side === 'target' && this.expandedSubPoliciesTarget.has(subPolicyId)
    },
    
    exportComparison() {
      // TODO: Implement export functionality
      PopupService.info('Export functionality coming soon!', 'Export')
    },
    
    async checkWithUpdates() {
      if (!this.selectedFrameworkId) {
        PopupService.warning('Please select a framework first.', 'Framework Selection')
        return
      }

      try {
        this.checkingUpdates = true
        const response = await frameworkComparisonService.checkFrameworkUpdates(this.selectedFrameworkId)

          if (response && response.warning) {
            PopupService.warning(response.warning, 'Warning')
            return
          }

          if (response && response.success) {
          const updateResult = response.result || {}
          const hasUpdate = !!updateResult.has_update

          // Always refresh document info to show the latest downloaded document
          await this.fetchDocumentInfo()
          await this.refreshUpdateNotifications()
          
          if (hasUpdate) {
            await this.onFrameworkChange()
            PopupService.success('New amendment available and downloaded, please go through the amendment', 'Update Available')
          } else {
            PopupService.success('No new amendments found.', 'No Updates')
          }
        } else {
          PopupService.error(response && response.error ? response.error : 'Unable to check updates.', 'Error')
        }
      } catch (error) {
        console.error('Error checking updates:', error)
        PopupService.error(`Error checking updates: ${error.message}`, 'Error')
      } finally {
        this.checkingUpdates = false
      }
    },
    
    async fetchDocumentInfo() {
      if (!this.selectedFrameworkId) {
        this.documentInfo = null
        return
      }
      
      try {
        const response = await frameworkComparisonService.getAmendmentDocumentInfo(this.selectedFrameworkId)
        
        if (response && response.success) {
          this.documentInfo = response
          // Debug logging for completion detection
          if (this.backgroundAnalysisActive) {
            const processed = response.document?.processed
            console.log('📊 Polling check - Document processed status:', processed, 'Full response:', response)
          }
        } else {
          this.documentInfo = null
        }
      } catch (error) {
        console.error('Error fetching document info:', error)
        this.documentInfo = null
      }
    },
    
    viewDocument() {
      if (!this.documentInfo || !this.documentInfo.document || !this.documentInfo.document.url) {
        PopupService.error('Document URL not available', 'Error')
        return
      }
      
      // Open document in new tab
      const documentUrl = this.documentInfo.document.url
      window.open(documentUrl, '_blank')
    },
    
    async startAnalysis() {
      if (!this.selectedFrameworkId) {
        PopupService.warning('Please select a framework first.', 'Framework Selection')
        return
      }
      
      if (!this.documentInfo || !this.documentInfo.has_document) {
        PopupService.warning('No document available to analyze.', 'No Document')
        return
      }
      
      try {
        this.analyzingDocument = true
        this.showProgressModal = true
        this.analysisProgress = 5
        this.currentAnalysisStep = 1
        this.analysisStatus = 'Initializing analysis...'
        this.backgroundAnalysisActive = true
        
        // Save analysis state to sessionStorage
        this.saveAnalysisState()
        
        // Start periodic state saving
        if (this.stateSaveInterval) {
          clearInterval(this.stateSaveInterval)
        }
        this.stateSaveInterval = setInterval(() => {
          if (this.backgroundAnalysisActive) {
            this.saveAnalysisState()
          }
        }, 5000) // Save every 5 seconds
        
        // Start polling immediately (don't wait for backend)
        this.startAnalysisPolling()
        
        // Start the analysis in the background (this is async and may take time)
        // Don't await it - let it run in background while we poll
        frameworkComparisonService.startAmendmentAnalysis(this.selectedFrameworkId)
          .then(async (response) => {
            if (response && response.success) {
              console.log('✅ Backend analysis completed successfully')
              
              // Backend is done! Immediately check for completion and finish
              // Give it a moment for database to update, then check
              setTimeout(async () => {
                await this.checkAndCompleteAnalysis()
              }, 2000) // Wait 2 seconds for database to update
            } else {
              console.error('❌ Backend analysis failed:', response?.error)
              // Stop polling and show error
              this.stopAnalysisPolling()
              this.showProgressModal = false
              this.backgroundAnalysisActive = false
              
              if (this.stateSaveInterval) {
                clearInterval(this.stateSaveInterval)
                this.stateSaveInterval = null
              }
              
              this.clearAnalysisState()
              PopupService.error(response?.error || 'Analysis failed. Please try again.', 'Analysis Error')
            }
          })
          .catch((error) => {
            console.error('❌ Error in backend analysis:', error)
            // Stop polling and show error
            this.stopAnalysisPolling()
            this.showProgressModal = false
            this.backgroundAnalysisActive = false
            
            if (this.stateSaveInterval) {
              clearInterval(this.stateSaveInterval)
              this.stateSaveInterval = null
            }
            
            this.clearAnalysisState()
            PopupService.error(`Error during analysis: ${error.message}`, 'Error')
          })
        
      } catch (error) {
        console.error('Error starting analysis:', error)
        this.stopAnalysisPolling()
        this.showProgressModal = false
        this.backgroundAnalysisActive = false
        
        // Clear state save interval
        if (this.stateSaveInterval) {
          clearInterval(this.stateSaveInterval)
          this.stateSaveInterval = null
        }
        
        this.clearAnalysisState()
        PopupService.error(`Error starting analysis: ${error.message}`, 'Error')
        this.analyzingDocument = false
      }
    },
    
    startAnalysisPolling() {
      // Clear any existing polling
      this.stopAnalysisPolling()
      
      let pollCount = 0
      const maxPolls = 300 // Maximum 15 minutes (300 * 3 seconds)
      
      // Poll every 3 seconds
      this.analysisPollingInterval = setInterval(async () => {
        try {
          pollCount++
          
          // Update progress gradually (but don't go above 95% until confirmed complete)
          if (this.analysisProgress < 95) {
            // Start faster, then slow down
            if (this.analysisProgress < 20) {
              this.analysisProgress += 3 // Fast initial progress
            } else if (this.analysisProgress < 50) {
              this.analysisProgress += 2 // Medium progress
            } else if (this.analysisProgress < 80) {
              this.analysisProgress += 1.5 // Slower progress
            } else {
              this.analysisProgress += 0.5 // Very slow near completion
            }
            
            // Cap at 95% until we confirm completion
            if (this.analysisProgress > 95) {
              this.analysisProgress = 95
            }
          }
          
          // Update status based on progress
          if (this.analysisProgress < 20) {
            this.currentAnalysisStep = 1
            this.analysisStatus = 'Initializing analysis...'
          } else if (this.analysisProgress < 40) {
            this.currentAnalysisStep = 2
            this.analysisStatus = 'Extracting document content...'
          } else if (this.analysisProgress < 80) {
            this.currentAnalysisStep = 3
            this.analysisStatus = 'AI is processing and analyzing data...'
          } else {
            this.currentAnalysisStep = 3
            this.analysisStatus = 'Finalizing analysis...'
          }
          
          // Check if analysis is complete by fetching document info
          const completed = await this.checkAndCompleteAnalysis()
          
          if (completed) {
            // Analysis is complete, stop polling
            return
          }
          
          // Check for timeout - but also check one more time if document is processed
          if (pollCount >= maxPolls) {
            // Final check before timing out
            const completed = await this.checkAndCompleteAnalysis()
            
            if (completed) {
              // Actually completed, just took longer
              console.log('✅ Analysis completed (detected on timeout check)')
              return
            }
            
            console.warn('⚠️ Analysis polling timeout reached after', pollCount, 'polls')
            this.stopAnalysisPolling()
            this.showProgressModal = false
            this.backgroundAnalysisActive = false
            
            if (this.stateSaveInterval) {
              clearInterval(this.stateSaveInterval)
              this.stateSaveInterval = null
            }
            
            PopupService.warning('Analysis is taking longer than expected. The backend may still be processing. Please check the status manually or refresh the page.', 'Analysis Timeout')
            this.clearAnalysisState()
            return
          }
          
          // Save state for background processing
          this.saveAnalysisState()
        } catch (error) {
          console.error('Error polling analysis status:', error)
          // Don't stop polling on error, just log it
          // But if we've been polling for a while and still getting errors, might be an issue
          if (pollCount > 20) {
            console.error('Multiple polling errors detected, but continuing...')
          }
        }
      }, 3000) // Poll every 3 seconds
    },
    
    stopAnalysisPolling() {
      if (this.analysisPollingInterval) {
        clearInterval(this.analysisPollingInterval)
        this.analysisPollingInterval = null
      }
    },
    
    async checkAndCompleteAnalysis() {
      // Force refresh document info
      await this.fetchDocumentInfo()
      
      // Check if document is processed - check multiple possible response structures
      const isProcessed = (
        (this.documentInfo && 
         this.documentInfo.document && 
         (this.documentInfo.document.processed === true || 
          this.documentInfo.document.processed === 'true' ||
          String(this.documentInfo.document.processed).toLowerCase() === 'true')) ||
        // Also check if response has processed flag directly
        (this.documentInfo && this.documentInfo.processed === true) ||
        // Check if document exists and has extraction_summary (indicates processing completed)
        (this.documentInfo && 
         this.documentInfo.document && 
         this.documentInfo.document.extraction_summary &&
         Object.keys(this.documentInfo.document.extraction_summary).length > 0)
      )
      
      if (isProcessed) {
        console.log('✅ Analysis completion confirmed! Completing progress bar...', {
          documentInfo: this.documentInfo,
          processed: this.documentInfo?.document?.processed,
          hasExtractionSummary: !!this.documentInfo?.document?.extraction_summary
        })
        
        // Complete the progress bar
        this.currentAnalysisStep = 4
        this.analysisProgress = 100
        this.analysisStatus = 'Analysis completed successfully!'
        
        // Stop polling
        this.stopAnalysisPolling()
        
        // Wait a moment to show completion, then close
        setTimeout(() => {
          this.showProgressModal = false
          this.backgroundAnalysisActive = false
          
          // Clear state save interval
          if (this.stateSaveInterval) {
            clearInterval(this.stateSaveInterval)
            this.stateSaveInterval = null
          }
          
          this.clearAnalysisState()
          
          // Refresh data
          this.onFrameworkChange()
          
          // Show success notification
          PopupService.success('Analysis completed successfully! The amendment has been processed and saved.', 'Analysis Complete')
          
          // Show browser notification if available
          this.showBrowserNotification('Analysis Complete', 'Amendment document has been processed successfully!')
        }, 1500)
        
        return true
      } else {
        console.log('⏳ Analysis not yet detected as complete, will continue polling...', {
          documentInfo: this.documentInfo,
          processed: this.documentInfo?.document?.processed
        })
        return false
      }
    },
    
    cancelAnalysis() {
      // Confirm cancellation
      PopupService.confirm(
        'Are you sure you want to cancel the analysis? The process will stop and you will need to start again.',
        'Cancel Analysis',
        () => {
          // User confirmed cancellation
          try {
            // Stop polling
            this.stopAnalysisPolling()
            
            // Clear state save interval
            if (this.stateSaveInterval) {
              clearInterval(this.stateSaveInterval)
              this.stateSaveInterval = null
            }
            
            // Clear analysis state
            this.clearAnalysisState()
            
            // Reset UI
            this.showProgressModal = false
            this.backgroundAnalysisActive = false
            this.analysisProgress = 0
            this.analysisStatus = 'Initializing analysis...'
            this.currentAnalysisStep = 0
            
            // Show cancellation message
            PopupService.info('Analysis has been cancelled. You can start a new analysis when ready.', 'Analysis Cancelled')
            
            console.log('❌ Analysis cancelled by user')
          } catch (error) {
            console.error('Error cancelling analysis:', error)
            PopupService.error('Error cancelling analysis. Please try again.', 'Error')
          }
        },
        () => {
          // User chose not to cancel - do nothing
        }
      )
    },
    
    saveAnalysisState() {
      if (!this.selectedFrameworkId) {
        return // Don't save if no framework is selected
      }
      
      const state = {
        frameworkId: this.selectedFrameworkId,
        isAnalyzing: this.backgroundAnalysisActive,
        progress: this.analysisProgress,
        status: this.analysisStatus,
        currentStep: this.currentAnalysisStep,
        timestamp: Date.now()
      }
      try {
        sessionStorage.setItem('framework_analysis_state', JSON.stringify(state))
        console.log('💾 Saved analysis state:', {
          frameworkId: state.frameworkId,
          progress: state.progress,
          isAnalyzing: state.isAnalyzing
        })
      } catch (error) {
        console.error('Failed to save analysis state:', error)
      }
    },
    
    loadAnalysisState() {
      try {
        const savedState = sessionStorage.getItem('framework_analysis_state')
        if (!savedState) return false
        
        const state = JSON.parse(savedState)
        
        // Check if state is not too old (1 hour max)
        const maxAge = 60 * 60 * 1000 // 1 hour
        if (Date.now() - state.timestamp > maxAge) {
          this.clearAnalysisState()
          return false
        }
        
        // Resume if it's for the current framework (or if framework is not selected yet, we'll check later)
        if (state.isAnalyzing) {
          // If framework matches or framework is not selected yet, restore state
          if (!this.selectedFrameworkId || state.frameworkId === this.selectedFrameworkId) {
            this.backgroundAnalysisActive = state.isAnalyzing
            this.analysisProgress = state.progress || 0
            this.analysisStatus = state.status || 'Resuming analysis...'
            this.currentAnalysisStep = state.currentStep || 1
            
            if (this.backgroundAnalysisActive) {
              this.showProgressModal = true
              this.startAnalysisPolling()
              
              // Show info notification
              PopupService.info('Resuming background analysis...', 'Analysis in Progress')
            }
            
            return true
          }
        }
        
        return false
      } catch (error) {
        console.error('Failed to load analysis state:', error)
        this.clearAnalysisState()
        return false
      }
    },
    
    checkAndResumeAnalysis() {
      // Check if there's a background analysis running for the current framework
      if (this.selectedFrameworkId) {
        try {
          const savedState = sessionStorage.getItem('framework_analysis_state')
          if (savedState) {
            const state = JSON.parse(savedState)
            
            // Check if state is not too old (1 hour max)
            const maxAge = 60 * 60 * 1000 // 1 hour
            if (Date.now() - state.timestamp <= maxAge) {
              // If it's for this framework and still analyzing
              if (state.frameworkId === this.selectedFrameworkId && state.isAnalyzing) {
                // Restore state
                this.backgroundAnalysisActive = state.isAnalyzing
                this.analysisProgress = state.progress || 0
                this.analysisStatus = state.status || 'Resuming analysis...'
                this.currentAnalysisStep = state.currentStep || 1
                
                if (this.backgroundAnalysisActive && !this.analysisPollingInterval) {
                  this.showProgressModal = true
                  this.startAnalysisPolling()
                  
                  // Start periodic state saving
                  if (this.stateSaveInterval) {
                    clearInterval(this.stateSaveInterval)
                  }
                  this.stateSaveInterval = setInterval(() => {
                    if (this.backgroundAnalysisActive) {
                      this.saveAnalysisState()
                    }
                  }, 5000) // Save every 5 seconds
                  
                  // Show info notification
                  PopupService.info('Resuming background analysis...', 'Analysis in Progress')
                  console.log('🔄 Resumed background analysis from saved state')
                }
              }
            } else {
              // State is too old, clear it
              this.clearAnalysisState()
            }
          }
        } catch (error) {
          console.error('Failed to check analysis state:', error)
        }
      }
    },
    
    clearAnalysisState() {
      try {
        sessionStorage.removeItem('framework_analysis_state')
      } catch (error) {
        console.error('Failed to clear analysis state:', error)
      }
    },
    
    showBrowserNotification(title, message) {
      // Check if browser supports notifications
      if ('Notification' in window && Notification.permission === 'granted') {
        new Notification(title, {
          body: message,
          icon: '/favicon.ico',
          tag: 'framework-analysis'
        })
      } else if ('Notification' in window && Notification.permission !== 'denied') {
        // Request permission
        Notification.requestPermission().then(permission => {
          if (permission === 'granted') {
            new Notification(title, {
              body: message,
              icon: '/favicon.ico',
              tag: 'framework-analysis'
            })
          }
        })
      }
    },
    
    formatDate(dateString) {
      if (!dateString) return 'N/A'
      
      try {
        const date = new Date(dateString)
        return date.toLocaleString('en-US', {
          year: 'numeric',
          month: 'short',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit'
        })
      } catch (error) {
        return dateString
      }
    },
    
    async findMatches(control) {
      if (!control || !this.selectedFrameworkId) return
      
      try {
        this.matchingInProgress = true
        this.selectedControl = control
        this.controlMatches = null
        
        console.log('Finding matches for control:', control)
        
        const response = await frameworkComparisonService.findControlMatches(
          this.selectedFrameworkId,
          control,
          true,  // Always use AI matching (OpenAI)
          5
        )
        
        if (response.success) {
          this.controlMatches = response.matches
          this.$forceUpdate()
        } else {
          console.error('Error finding matches:', response.error)
          PopupService.error(`Error finding matches: ${response.error}`, 'Error')
        }
      } catch (error) {
        console.error('Error finding matches:', error)
        PopupService.error(`Error: ${error.message}`, 'Error')
      } finally {
        this.matchingInProgress = false
      }
    },
    
    clearMatches() {
      this.selectedControl = null
      this.controlMatches = null
      this.complianceMatches = null
      this.expandedComplianceIndex = null
      this.$forceUpdate()
    },
    
    toggleComplianceDetails(index) {
      // Toggle: if already expanded, collapse; otherwise expand this one
      if (this.expandedComplianceIndex === index) {
        this.expandedComplianceIndex = null
      } else {
        this.expandedComplianceIndex = index
      }
      this.$forceUpdate()
    },
    
    
    async matchCompliances() {
      if (!this.selectedFrameworkId || !this.targetData) return
      
      try {
        this.complianceMatchingInProgress = true
        this.complianceMatches = null
        this.expandedComplianceIndex = null
        
        console.log('Matching compliances for framework:', this.selectedFrameworkId)
        
        const response = await frameworkComparisonService.matchAmendmentsCompliances(
          this.selectedFrameworkId,
          true,  // Always use AI matching (OpenAI)
          0.65  // Threshold for matching
        )
        
        if (response.success) {
          this.complianceMatches = response.results
          if (response.reused_cached) {
            PopupService.info('Using saved compliance matching results for this amendment. Upload a new amendment to re-run matching.', 'Using Saved Results')
          }
          this.$forceUpdate()
          return response
        } else {
          console.error('Error matching compliances:', response.error)
          PopupService.error(`Error matching compliances: ${response.error}`, 'Error')
        }
      } catch (error) {
        console.error('Error matching compliances:', error)
        PopupService.error(`Error: ${error.message}`, 'Error')
      } finally {
        this.complianceMatchingInProgress = false
      }
    },

    openComplianceModal(unmatch) {
      const target = unmatch?.target_compliance || {}
      const policyInfo = target.policy_info || {}
      const subpolicyInfo = target.subpolicy_info || {}

      this.complianceForm = {
        policy_name: policyInfo.policy_name || '',
        policy_identifier: policyInfo.policy_identifier || '',
        policy_description: policyInfo.policy_description || '',
        policy_scope: policyInfo.scope || '',
        policy_objective: policyInfo.objective || '',
        subpolicy_name: subpolicyInfo.subpolicy_name || '',
        subpolicy_identifier: subpolicyInfo.subpolicy_identifier || '',
        subpolicy_description: subpolicyInfo.subpolicy_description || '',
        subpolicy_control: subpolicyInfo.control || '',
        compliance_title: target.compliance_title || '',
        compliance_description: target.compliance_description || '',
        compliance_type: target.compliance_type || '',
        criticality: target.criticality || 'Medium',
        mandatory: target.mandatory || 'Mandatory',
        manual_automatic: target.manual_automatic || 'Manual'
      }
      this.complianceModalData = unmatch
      this.complianceSaveError = ''
      this.showComplianceModal = true
    },

    closeComplianceModal() {
      if (this.submittingCompliance) return
      this.showComplianceModal = false
      this.complianceModalData = null
    },

    async submitComplianceForm() {
      if (!this.selectedFrameworkId) return
      try {
        this.submittingCompliance = true
        this.complianceSaveError = ''
        const payload = {
          policy: {
            name: this.complianceForm.policy_name,
            identifier: this.complianceForm.policy_identifier,
            description: this.complianceForm.policy_description,
            scope: this.complianceForm.policy_scope,
            objective: this.complianceForm.policy_objective
          },
          subpolicy: {
            name: this.complianceForm.subpolicy_name,
            identifier: this.complianceForm.subpolicy_identifier,
            description: this.complianceForm.subpolicy_description,
            control: this.complianceForm.subpolicy_control
          },
          compliance: {
            title: this.complianceForm.compliance_title,
            description: this.complianceForm.compliance_description,
            type: this.complianceForm.compliance_type,
            criticality: this.complianceForm.criticality,
            mandatory: this.complianceForm.mandatory,
            manual_automatic: this.complianceForm.manual_automatic
          }
        }
        await frameworkComparisonService.createComplianceFromAmendment(
          this.selectedFrameworkId,
          payload
        )
        this.showComplianceModal = false
        this.complianceModalData = null
        await this.matchCompliances()
      } catch (error) {
        this.complianceSaveError = error?.response?.data?.error || error.message || 'Failed to save compliance'
      } finally {
        this.submittingCompliance = false
      }
    },
    
    openAddAllModal() {
      if (!this.complianceMatches || !this.complianceMatches.unmatched || this.complianceMatches.unmatched.length === 0) {
        PopupService.warning('No unmatched compliances to add.', 'No Compliances')
        return
      }
      this.selectedCompliancesForAdd = []
      this.showAddAllModal = true
    },
    
    closeAddAllModal() {
      this.showAddAllModal = false
      this.selectedCompliancesForAdd = []
    },
    
    processSelectedCompliances() {
      if (this.selectedCompliancesForAdd.length === 0) {
        PopupService.warning('Please select at least one compliance to add.', 'No Selection')
        return
      }
      
      // Get selected compliances data
      const selectedCompliances = this.selectedCompliancesForAdd.map(index => {
        const unmatch = this.complianceMatches.unmatched[index]
        const target = unmatch?.target_compliance || {}
        const policyInfo = target.policy_info || {}
        const subpolicyInfo = target.subpolicy_info || {}
        
        return {
          policy: {
            name: policyInfo.policy_name || '',
            identifier: policyInfo.policy_identifier || '',
            description: policyInfo.policy_description || '',
            scope: policyInfo.scope || '',
            objective: policyInfo.objective || ''
          },
          subpolicy: {
            name: subpolicyInfo.subpolicy_name || '',
            identifier: subpolicyInfo.subpolicy_identifier || '',
            description: subpolicyInfo.subpolicy_description || '',
            control: subpolicyInfo.control || ''
          },
          compliance: {
            title: target.compliance_title || '',
            description: target.compliance_description || '',
            type: target.compliance_type || '',
            criticality: target.criticality || 'Medium',
            mandatory: target.mandatory || 'Mandatory',
            manual_automatic: target.manual_automatic || 'Manual'
          },
          originalData: unmatch
        }
      })
      
      // Store in localStorage and navigate to new page
      localStorage.setItem('selected_compliances_for_add', JSON.stringify(selectedCompliances))
      localStorage.setItem('framework_id_for_compliances', this.selectedFrameworkId.toString())
      
      // Navigate to checklist page
      this.$router.push('/framework-migration/checklisted-compliances')
    }
  }
}
</script>

<style scoped>
.FC_framework-comparison-container {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
  margin-left: 280px;
  max-width: 100%;
}

.FC_framework-comparison-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.FC_header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.FC_header-actions-left {
  display: flex;
  align-items: center;
  gap: 10px;
  position: relative;
}

.FC_notification-wrapper {
  position: relative;
}

.FC_notification-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 1px solid var(--border-color);
  background: white;
  color: var(--text-primary);
  cursor: pointer;
  position: relative;
  transition: all 0.2s ease;
}

.FC_notification-button:hover {
  background: #f3f4f6;
}

.FC_notification-badge {
  position: absolute;
  top: 4px;
  right: 4px;
  background: #ef4444;
  color: white;
  border-radius: 999px;
  font-size: 11px;
  padding: 2px 6px;
  line-height: 1;
}

.FC_notification-popover {
  position: absolute;
  top: 44px;
  left: 0;
  width: 320px;
  background: white;
  border: 1px solid var(--border-color);
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.12);
  border-radius: 12px;
  z-index: 10;
  padding: 12px;
}

.FC_notification-popover__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.FC_notification-popover__title {
  font-weight: 600;
  color: var(--text-primary);
}

.FC_notification-popover__count {
  background: var(--primary-color);
  color: white;
  border-radius: 999px;
  padding: 2px 8px;
  font-size: 12px;
}

.FC_notification-popover__loading,
.FC_notification-popover__empty {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px;
  color: var(--text-secondary);
  font-size: 14px;
}

.FC_notification-popover__list {
  max-height: 240px;
  overflow: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.FC_notification-row {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  cursor: pointer;
  transition: border-color 0.2s ease, background 0.2s ease;
}

.FC_notification-row:hover {
  border-color: var(--primary-color);
  background: #f8fafc;
}

.FC_notification-row__content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.FC_notification-row__name {
  font-weight: 600;
  color: var(--text-primary);
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.FC_notification-row__status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  padding: 4px 8px;
  border-radius: 6px;
  flex-shrink: 0;
}

.FC_notification-row__status.has-update {
  color: #166534;
  background: #ecfdf3;
}

.FC_notification-row__status.no-update {
  color: #6b7280;
  background: #f3f4f6;
}

.FC_notification-row__date {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 4px;
  padding-left: 2px;
}

.FC_header-content h1 {
  font-size: 2rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.FC_framework-comparison-subtitle {
  color: var(--text-secondary);
  font-size: 1rem;
}

.FC_export-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: transparent;
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.FC_check-updates-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: var(--primary-color);
  border: 1px solid var(--primary-color);
  color: white;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.FC_check-updates-button:hover {
  background: #1d4ed8;
  border-color: #1d4ed8;
}

.FC_export-button:hover {
  background: var(--secondary-color);
}

.FC_framework-selection-card,
.FC_filters-card,
.FC_legend-card,
.FC_document-viewer-card {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.FC_document-viewer-card {
  background: transparent;
  border: 1px solid #e5e7eb;
  border-radius: 0;
  box-shadow: none;
  color: #1f2937;
}

.FC_document-viewer-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
}

.FC_document-info {
  display: flex;
  gap: 16px;
  align-items: center;
  flex: 1;
}

.FC_document-icon {
  font-size: 48px;
  color: #4f8cff;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border-radius: 0;
  padding: 16px;
  min-width: 80px;
  height: 80px;
}

.FC_document-details {
  flex: 1;
}

.FC_document-name {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0 0 8px 0;
  color: #1f2937;
}

.FC_document-meta {
  font-size: 0.875rem;
  color: #6b7280;
  margin: 0 0 8px 0;
}

.FC_document-status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.875rem;
  padding: 4px 12px;
  border-radius: 0;
  font-weight: 500;
  border: 1px solid transparent;
}

.FC_document-processed {
  background: transparent;
  color: #22c55e;
  border: 1px solid #22c55e;
}

.FC_document-pending {
  background: transparent;
  color: #f59e0b;
  border: 1px solid #f59e0b;
}

.FC_document-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.FC_view-document-button,
.FC_start-analysis-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border-radius: 0;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid #d1d5db;
  font-size: 0.9375rem;
  background: transparent;
  color: #1f2937;
}

.FC_view-document-button {
  background: transparent;
  color: #1f2937;
  border: 1px solid #d1d5db;
}

.FC_view-document-button:hover {
  background: transparent;
  border-color: #4f8cff;
  color: #4f8cff;
  opacity: 0.8;
}

.FC_start-analysis-button {
  background: transparent;
  color: #1f2937;
  font-weight: 600;
  border: 1px solid #4f8cff;
  color: #4f8cff;
}

.FC_start-analysis-button:hover:not(:disabled) {
  background: transparent;
  border-color: #1d4ed8;
  color: #1d4ed8;
  opacity: 0.8;
  transform: none;
  box-shadow: none;
}

.FC_start-analysis-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  border-color: #d1d5db;
  color: #6b7280;
}

.FC_framework-selection-content,
.FC_filters-content {
  display: flex;
  gap: 20px;
  align-items: center;
  justify-content: space-between;
}

.FC_framework-selector {
  display: flex;
  align-items: center;
  gap: 8px;
}

.FC_framework-label {
  font-weight: 500;
  color: var(--text-primary);
}

.FC_framework-select,
.FC_version-select,
.FC_filter-select {
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--input-bg);
  color: var(--text-primary);
  font-size: 14px;
  transition: all 0.2s ease;
  cursor: pointer;
  min-width: 120px;
}

.FC_framework-select:focus,
.FC_version-select:focus,
.FC_filter-select:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.FC_search-container {
  flex: 1;
  max-width: 400px;
}

.FC_search-input-wrapper {
  position: relative;
  width: 50%;
}

.FC_search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-secondary);
  font-size: 14px;
  z-index: 1;
}

.FC_search-input {
  width: 100%;
  padding: 10px 12px 10px 36px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--input-bg);
  color: var(--text-primary);
  font-size: 14px;
  transition: all 0.2s ease;
  box-sizing: border-box;
}

.FC_search-input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.FC_search-input::placeholder {
  color: var(--text-secondary);
  font-size: 14px;
}

.FC_summary-stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.FC_summary-stat-card {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 16px;
  text-align: center;
  transition: all 0.2s ease;
}

.FC_clickable-card {
  cursor: pointer;
  user-select: none;
}

.FC_clickable-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: var(--primary-color);
}

.FC_card-active {
  background: rgba(59, 130, 246, 0.1);
  border-color: var(--primary-color);
  border-width: 2px;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
}

.FC_summary-stat-number {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 4px;
}

.FC_summary-stat-new { color: #22c55e; }
.FC_summary-stat-modified { color: var(--primary-color); }
.FC_summary-stat-removed { color: #ef4444; }
.FC_summary-stat-unchanged { color: #6b7280; }
.FC_summary-stat-structured { color: #0ea5e9; }
.FC_structured-summary-grid {
  margin-top: 8px;
}

.FC_summary-stat-label {
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.FC_comparison-view {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 24px;
}

.FC_framework-side {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  overflow: hidden;
}

.FC_framework-side-header {
  padding: 16px;
  border-bottom: 1px solid var(--border-color);
  background: var(--secondary-color);
}

.FC_framework-side-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--text-primary);
  flex-wrap: wrap;
}

.FC_add-all-button {
  margin-left: auto;
  padding: 6px 16px;
  background: var(--primary-color, #3b82f6);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s;
}

.FC_add-all-button:hover {
  background: var(--primary-color-dark, #2563eb);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
}

.FC_add-all-button i {
  font-size: 16px;
}

.FC_framework-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
}

.FC_framework-badge-current {
  background: var(--secondary-color);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

.FC_framework-badge-target {
  background: var(--primary-color);
  color: white;
}

.FC_framework-side-content {
  max-height: 600px;
  overflow-y: auto;
  padding: 16px;
}

.FC_structured-sections {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.FC_structured-section {
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 16px;
  background: var(--card-bg);
}

.FC_section-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 8px;
}

.FC_structured-section-title {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
}

.FC_section-page-info {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.FC_structured-section-summary {
  margin: 0 0 12px 0;
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.FC_policy-card {
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 16px;
  margin-top: 12px;
  background: var(--secondary-color);
}

.FC_policy-card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.FC_policy-card-header h5 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
}

.FC_policy-scope {
  margin: 4px 0 0 0;
  color: var(--text-secondary);
  font-size: 0.85rem;
}

.FC_policy-type-pill {
  background: rgba(59, 130, 246, 0.15);
  color: var(--primary-color);
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
}

.FC_policy-card-description {
  margin: 12px 0;
  color: var(--text-secondary);
  line-height: 1.5;
}

.FC_subpolicy-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.FC_subpolicy-card {
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 12px;
  background: var(--card-bg);
}

.FC_subpolicy-card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.FC_subpolicy-card-header h6 {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 600;
}

.FC_subpolicy-control {
  margin: 4px 0 0 0;
  font-size: 0.8rem;
  color: var(--text-secondary);
  font-style: italic;
}

.FC_subpolicy-pill {
  background: rgba(14, 165, 233, 0.15);
  color: #0ea5e9;
  border-radius: 999px;
  padding: 3px 8px;
  font-size: 0.7rem;
  font-weight: 600;
  white-space: nowrap;
}

.FC_subpolicy-card-description {
  margin: 8px 0 0 0;
  color: var(--text-secondary);
  font-size: 0.875rem;
  line-height: 1.5;
}

.FC_compliance-chip-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 12px;
}

.FC_compliance-chip {
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 10px;
  background: rgba(34, 197, 94, 0.08);
}

.FC_compliance-chip-title {
  display: block;
  margin-bottom: 4px;
  color: var(--text-primary);
}

.FC_compliance-chip-desc {
  margin: 0;
  color: var(--text-secondary);
  font-size: 0.85rem;
  line-height: 1.4;
}

.FC_framework-side-content .FC_matches-panel {
  padding: 0;
}

.FC_framework-side-content .FC_matches-header {
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-color);
}

.FC_framework-side-content .FC_matches-list {
  gap: 12px;
}

.FC_policy-item {
  border: 1px solid var(--border-color);
  border-radius: 6px;
  margin-bottom: 16px;
}

.FC_policy-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.FC_policy-header:hover {
  background: var(--secondary-color);
}

.FC_toggle-icon {
  color: var(--text-secondary);
  font-size: 0.875rem;
  transition: transform 0.2s ease;
  flex-shrink: 0;
  margin-top: 2px;
  width: 16px;
  text-align: center;
}

.FC_policy-header:hover .FC_toggle-icon,
.FC_sub-policy-header:hover .FC_toggle-icon {
  color: var(--primary-color);
}

.FC_policy-info {
  flex: 1;
  min-width: 0;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.FC_policy-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
  flex-wrap: wrap;
}

.FC_policy-name {
  font-weight: 600;
  color: var(--text-primary);
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.FC_policy-description {
  color: var(--text-secondary);
  font-size: 0.875rem;
  word-wrap: break-word;
  overflow-wrap: break-word;
  line-height: 1.4;
}

.FC_policy-content {
  padding: 0 16px 16px 16px;
  border-top: 1px solid var(--border-color);
  margin-top: 8px;
}

.FC_sub-policy-item {
  margin-bottom: 8px;
}

.FC_sub-policy-header {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 12px;
  cursor: pointer;
  border-radius: 6px;
  transition: background-color 0.2s ease;
  border: 1px solid var(--border-color);
  background: var(--card-bg);
  margin-bottom: 8px;
}

.FC_sub-policy-header:hover {
  background: var(--secondary-color);
}

.FC_sub-policy-name {
  font-weight: 500;
  color: var(--text-primary);
  flex: 1;
  min-width: 0;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.FC_sub-policy-content {
  margin-top: 8px;
  padding: 12px;
  background: var(--secondary-color);
  border-radius: 6px;
  border: 1px solid var(--border-color);
}

.FC_sub-policy-description {
  color: var(--text-secondary);
  font-size: 0.75rem;
  margin-bottom: 12px;
  word-wrap: break-word;
  overflow-wrap: break-word;
  line-height: 1.4;
}

.FC_compliance-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 12px;
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  margin-bottom: 8px;
}

.FC_compliance-info {
  flex: 1;
  min-width: 0;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.FC_compliance-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
  flex-wrap: wrap;
}

.FC_compliance-name {
  font-weight: 500;
  color: var(--text-primary);
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.FC_compliance-description {
  color: var(--text-secondary);
  font-size: 0.75rem;
  word-wrap: break-word;
  overflow-wrap: break-word;
  line-height: 1.4;
}

.FC_change-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 0.625rem;
  font-weight: 600;
  border: 1px solid;
  transition: all 0.2s ease;
}

.FC_change-badge-new {
  background: rgba(34, 197, 94, 0.1);
  color: #22c55e;
  border-color: rgba(34, 197, 94, 0.3);
}

.FC_change-badge-modified {
  background: rgba(59, 130, 246, 0.1);
  color: var(--primary-color);
  border-color: rgba(59, 130, 246, 0.3);
}

.FC_change-badge-removed {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
  border-color: rgba(239, 68, 68, 0.3);
}

.FC_change-badge-unchanged {
  background: rgba(107, 114, 128, 0.1);
  color: #6b7280;
  border-color: rgba(107, 114, 128, 0.3);
}

.FC_change-badge-enhanced {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
  border-color: rgba(245, 158, 11, 0.3);
}

.FC_change-badge-deprecated {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
  border-color: rgba(239, 68, 68, 0.3);
}

.FC_status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  transition: all 0.2s ease;
  flex-shrink: 0;
  white-space: nowrap;
}

.FC_status-badge-compliant {
  background: rgba(34, 197, 94, 0.1);
  color: #22c55e;
}

.FC_status-badge-non-compliant {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.FC_status-badge-partial {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
}

.FC_status-badge-gap {
  background: rgba(107, 114, 128, 0.1);
  color: #6b7280;
}

.FC_status-badge-audit {
  background: rgba(59, 130, 246, 0.1);
  color: var(--primary-color);
}

.FC_legend-card {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.FC_legend-header {
  margin-bottom: 24px;
}

.FC_legend-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.FC_legend-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 32px;
}

.FC_legend-section-title {
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 16px;
  font-size: 1rem;
}

.FC_legend-items {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.FC_legend-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 8px 0;
}

.FC_legend-description {
  color: var(--text-secondary);
  font-size: 0.875rem;
  font-weight: 500;
  flex: 1;
}

@media (max-width: 1024px) {
  .FC_comparison-view {
    grid-template-columns: 1fr;
  }
  
  .FC_legend-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .FC_framework-comparison-container {
    padding: 16px;
  }
  
  .FC_framework-comparison-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  
  .FC_summary-stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .FC_framework-selection-content,
  .FC_filters-content {
    flex-direction: column;
    align-items: stretch;
  }
  
  .FC_policy-header,
  .FC_sub-policy-header {
    padding: 12px;
  }
  
  .FC_compliance-item {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }
  
  .FC_status-badge {
    align-self: flex-start;
  }
}

.FC_loading-state, .FC_error-state, .FC_no-amendment-message {
  text-align: center;
  padding: 40px;
  background: var(--card-bg);
  border-radius: 12px;
  margin: 20px 0;
}

.FC_no-amendment-message {
  border: 1px solid var(--border-color);
}

.FC_loading-state i, .FC_error-state i, .FC_no-amendment-message i {
  font-size: 3rem;
  margin-bottom: 1rem;
  color: var(--primary-color);
}

.FC_error-state i {
  color: #ef4444;
}

.FC_no-amendment-message i {
  opacity: 0.7;
}

.FC_no-amendment-message h3 {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 12px 0;
}

.FC_no-amendment-message p {
  color: var(--text-secondary);
  font-size: 1rem;
  line-height: 1.6;
  margin: 8px 0;
}

.FC_section-header {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 20px 0 10px 0;
  padding: 10px;
  background: var(--secondary-color);
  border-radius: 6px;
}

.FC_enhancement-section, .FC_related-section, .FC_requirements-section {
  margin-top: 12px;
  padding: 12px;
  background: var(--secondary-color);
  border-radius: 6px;
}

.FC_enhancement-section h5, .FC_related-section h5, .FC_requirements-section h6 {
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.FC_enhancement-section ul, .FC_requirements-section ul {
  margin-left: 20px;
  color: var(--text-secondary);
}

.FC_new-item {
  border-left: 4px solid #22c55e;
}

/* AI Matching Styles */
.FC_clear-matches-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--card-bg);
  color: var(--text-primary);
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 14px;
  font-weight: 500;
}

.FC_clear-matches-button:hover {
  background: var(--secondary-color);
  border-color: var(--primary-color);
}

.FC_clear-matches-button {
  background: rgba(239, 68, 68, 0.1);
  border-color: rgba(239, 68, 68, 0.3);
  color: #ef4444;
}

.FC_clear-matches-button:hover {
  background: rgba(239, 68, 68, 0.2);
}

/* Analysis Placeholder */
.FC_analysis-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
  color: var(--text-secondary);
  min-height: 400px;
}

.FC_analysis-placeholder i {
  font-size: 3rem;
  margin-bottom: 16px;
  color: var(--primary-color);
  opacity: 0.5;
}

.FC_analysis-placeholder p {
  font-size: 0.95rem;
  line-height: 1.6;
  max-width: 400px;
}

/* Matches Panel */
.FC_matches-panel {
  background: transparent;
  border: none;
  border-radius: 0;
  padding: 0;
  margin-bottom: 0;
  box-shadow: none;
}

.FC_matches-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-color);
}

.FC_matches-header h4 {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.FC_match-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: var(--primary-color);
  color: white;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
}

.FC_matches-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.FC_match-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: var(--secondary-color);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  transition: all 0.2s ease;
}

.FC_match-item:hover {
  border-color: var(--primary-color);
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.1);
}

.FC_match-rank {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: var(--primary-color);
  color: white;
  border-radius: 50%;
  font-weight: 700;
  font-size: 0.875rem;
  flex-shrink: 0;
}

.FC_match-info {
  flex: 1;
  min-width: 0;
}

.FC_match-type-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  background: rgba(59, 130, 246, 0.1);
  color: var(--primary-color);
  border-radius: 4px;
  font-size: 0.625rem;
  font-weight: 600;
  margin-bottom: 4px;
}

.FC_match-path {
  color: var(--text-secondary);
  font-size: 0.875rem;
  margin: 0;
  word-wrap: break-word;
}

.FC_match-score {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 120px;
}

.FC_score-bar {
  flex: 1;
  height: 8px;
  background: rgba(0, 0, 0, 0.1);
  border-radius: 4px;
  overflow: hidden;
}

.FC_score-fill {
  height: 100%;
  background: linear-gradient(90deg, #22c55e 0%, var(--primary-color) 50%, #f59e0b 100%);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.FC_score-text {
  font-weight: 600;
  color: var(--primary-color);
  font-size: 0.875rem;
  min-width: 45px;
  text-align: right;
}

/* Highlighting Styles */
.FC_highlighted {
  border: 2px solid var(--primary-color) !important;
  background: rgba(59, 130, 246, 0.05);
  box-shadow: 0 0 12px rgba(59, 130, 246, 0.2);
}

.FC_match-indicator {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: var(--primary-color);
  color: white;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  margin-right: 8px;
  flex-shrink: 0;
}

.FC_match-indicator-small {
  font-size: 0.625rem;
  padding: 2px 6px;
  position: absolute;
  top: 8px;
  right: 8px;
}

/* Target Control Styles */
.FC_clickable-control {
  cursor: pointer;
  position: relative;
  transition: all 0.2s ease;
}

.FC_clickable-control:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.FC_selected-control {
  border: 2px solid #22c55e !important;
  background: rgba(34, 197, 94, 0.05);
}

.FC_find-match-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  padding: 0;
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
  margin-right: 8px;
}

.FC_find-match-button:hover:not(:disabled) {
  background: var(--primary-color);
  transform: scale(1.1);
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
}

.FC_find-match-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .FC_matches-panel {
    padding: 16px;
  }
  
  .FC_matches-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .FC_match-item {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .FC_match-score {
    width: 100%;
  }
  
  .FC_compliance-summary {
    flex-direction: column;
    gap: 12px;
  }
}

/* Compliance Matching Styles */
.FC_match-compliances-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: #22c55e;
  color: white;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 14px;
  font-weight: 500;
}

.FC_match-compliances-button:hover:not(:disabled) {
  background: #16a34a;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(34, 197, 94, 0.3);
}

.FC_match-compliances-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.FC_compliance-matches-panel {
  background: transparent;
  border: none;
  border-radius: 0;
  padding: 0;
  margin-bottom: 0;
}

.FC_compliance-summary {
  display: flex;
  gap: 16px;
  padding: 16px;
  background: var(--secondary-color);
  border-radius: 8px;
  margin-bottom: 20px;
  border: 1px solid var(--border-color);
}

.FC_summary-stat {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.FC_summary-label {
  font-size: 0.75rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.FC_summary-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary);
}

.FC_summary-matched .FC_summary-value {
  color: #22c55e;
}

.FC_summary-unmatched .FC_summary-value {
  color: #ef4444;
}

.FC_compliance-section {
  margin-bottom: 24px;
}

.FC_section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 2px solid var(--border-color);
}

.FC_matched-title {
  color: #22c55e;
  border-bottom-color: #22c55e;
}

.FC_unmatched-title {
  color: #ef4444;
  border-bottom-color: #ef4444;
}

.FC_compliance-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.FC_compliance-match-item {
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 16px;
  background: var(--card-bg);
  transition: all 0.2s ease;
}

.FC_expandable-item {
  cursor: pointer;
}

.FC_expandable-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border-color: var(--primary-color);
}

.FC_expanded {
  border-color: var(--primary-color);
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.2);
}

.FC_matched-item {
  border-left: 4px solid #22c55e;
}

.FC_unmatched-item {
  border-left: 4px solid #ef4444;
}

.FC_compliance-match-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 12px;
}

.FC_match-status-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  flex-shrink: 0;
}

.FC_match-success {
  background: rgba(34, 197, 94, 0.1);
  color: #22c55e;
}

.FC_match-warning {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.FC_compliance-match-info {
  flex: 1;
  min-width: 0;
}

.FC_add-compliance-button {
  border: none;
  background: rgba(34, 197, 94, 0.15);
  color: #16a34a;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.FC_add-compliance-button:hover {
  background: rgba(34, 197, 94, 0.25);
}

.FC_expand-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  color: var(--text-secondary);
  transition: transform 0.2s ease;
  flex-shrink: 0;
}

.FC_expandable-item:hover .FC_expand-icon {
  color: var(--primary-color);
}

.FC_expanded .FC_expand-icon {
  color: var(--primary-color);
}

.FC_target-compliance-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
  word-wrap: break-word;
}

.FC_target-compliance-desc {
  font-size: 0.875rem;
  color: var(--text-secondary);
  word-wrap: break-word;
  line-height: 1.5;
}

.FC_matched-compliance-details {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.FC_detail-section {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.FC_detail-section label {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.FC_detail-section span {
  font-size: 0.875rem;
  color: var(--text-primary);
  word-wrap: break-word;
  line-height: 1.5;
}

.FC_unmatched-message {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background: rgba(239, 68, 68, 0.1);
  border-radius: 6px;
  color: #ef4444;
  font-weight: 500;
  margin-top: 12px;
}

.FC_modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.FC_modal {
  width: 90%;
  max-width: 800px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
  max-height: 90vh;
}

.FC_modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e5e7eb;
}

.FC_modal-header h3 {
  margin: 0;
  font-size: 1.25rem;
}

.FC_modal-close {
  border: none;
  background: transparent;
  font-size: 1.1rem;
  cursor: pointer;
  color: #6b7280;
}

.FC_modal-body {
  padding: 20px;
  overflow-y: auto;
}

.FC_modal-section {
  margin-bottom: 20px;
  padding: 15px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #f9fafb;
}

.FC_modal-section h4 {
  margin-top: 0;
  margin-bottom: 12px;
  font-size: 1rem;
  color: #111827;
}

.FC_modal-field {
  display: flex;
  flex-direction: column;
  margin-bottom: 12px;
}

.FC_modal-field label {
  font-size: 0.85rem;
  margin-bottom: 6px;
  color: #4b5563;
}

.FC_modal-field input,
.FC_modal-field textarea,
.FC_modal-field select {
  padding: 8px 10px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.95rem;
  background: #fff;
}

.FC_modal-field textarea {
  min-height: 70px;
  resize: vertical;
}

.FC_modal-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.FC_modal-footer {
  padding: 16px 20px;
  border-top: 1px solid #e5e7eb;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.FC_modal-primary,
.FC_modal-secondary {
  padding: 10px 20px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  font-weight: 600;
}

.FC_modal-secondary {
  background: #f3f4f6;
  color: #374151;
}

.FC_modal-primary {
  background: var(--primary-color);
  color: white;
}

.FC_modal-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.FC_modal-error {
  color: #dc2626;
  font-weight: 500;
  margin-top: 8px;
}

@media (max-width: 640px) {
  .FC_modal {
    width: 95%;
    max-height: 95vh;
  }
}

/* Add All Modal Styles */
.FC_modal-overlay-checklist {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10001;
  overflow-y: auto;
  padding: 20px;
}

.FC_add-all-modal {
  max-width: 700px;
  max-height: 85vh;
  width: 90%;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
  display: flex;
  flex-direction: column;
  margin: auto;
}

.FC_checklist-container {
  max-height: 400px;
  overflow-y: auto;
  margin-bottom: 16px;
}

.FC_checklist-item {
  margin-bottom: 12px;
  padding: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: #f9fafb;
  transition: all 0.2s;
}

.FC_checklist-item:hover {
  background: #f3f4f6;
  border-color: #d1d5db;
}

.FC_checklist-label {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  cursor: pointer;
  margin: 0;
}

.FC_checkbox {
  width: 20px;
  height: 20px;
  margin-top: 2px;
  cursor: pointer;
  flex-shrink: 0;
}

.FC_checklist-content {
  flex: 1;
}

.FC_checklist-title {
  margin: 0 0 6px 0;
  font-size: 15px;
  font-weight: 600;
  color: #111827;
}

.FC_checklist-description {
  margin: 0;
  font-size: 13px;
  color: #6b7280;
  line-height: 1.5;
}

.FC_checklist-summary {
  padding: 12px;
  background: #eff6ff;
  border-radius: 6px;
  text-align: center;
  margin-top: 16px;
}

.FC_checklist-summary p {
  margin: 0;
  font-size: 14px;
  color: #1e40af;
}

.FC_checklist-summary strong {
  font-weight: 600;
}

/* Progress Modal Styles */
.FC_progress-modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: transparent; /* No background overlay - allows interaction with sidebar */
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  pointer-events: none; /* Allow clicks to pass through backdrop */
}

.FC_progress-modal {
  width: 90%;
  max-width: 500px;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  overflow: hidden;
  animation: slideIn 0.3s ease-out;
  pointer-events: auto; /* Allow interaction with modal itself */
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.FC_progress-modal-header {
  padding: 24px;
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.FC_progress-modal-header h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
}

.FC_progress-modal-header h3 i {
  font-size: 1.5rem;
}

.FC_progress-cancel-btn {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: white;
  transition: all 0.2s ease;
  padding: 0;
  font-size: 14px;
  flex-shrink: 0;
}

.FC_progress-cancel-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  border-color: rgba(255, 255, 255, 0.5);
  transform: scale(1.1);
}

.FC_progress-cancel-btn:active {
  transform: scale(0.95);
}

.FC_progress-cancel-btn i {
  margin: 0;
}

.FC_progress-modal-body {
  padding: 32px 24px;
  text-align: center;
}

.FC_progress-spinner-container {
  margin-bottom: 24px;
  display: flex;
  justify-content: center;
}

.FC_progress-spinner {
  width: 60px;
  height: 60px;
  border: 4px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.FC_progress-status-text {
  font-size: 1rem;
  color: #374151;
  margin-bottom: 24px;
  font-weight: 500;
  min-height: 24px;
}

.FC_progress-bar-container {
  margin-bottom: 32px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.FC_progress-bar {
  flex: 1;
  height: 12px;
  background: #e5e7eb;
  border-radius: 6px;
  overflow: hidden;
  position: relative;
}

.FC_progress-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6 0%, #1d4ed8 100%);
  border-radius: 6px;
  transition: width 0.3s ease;
  position: relative;
  overflow: hidden;
}

.FC_progress-bar-fill::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.3),
    transparent
  );
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(100%);
  }
}

.FC_progress-percentage {
  font-size: 1rem;
  font-weight: 700;
  color: #3b82f6;
  min-width: 50px;
  text-align: right;
}

.FC_progress-steps {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  margin-top: 24px;
}

.FC_progress-step {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 12px 8px;
  border-radius: 8px;
  transition: all 0.3s ease;
  opacity: 0.4;
}

.FC_progress-step i {
  font-size: 1.5rem;
  color: #9ca3af;
  transition: all 0.3s ease;
}

.FC_progress-step span {
  font-size: 0.75rem;
  color: #6b7280;
  font-weight: 500;
  text-align: center;
}

.FC_progress-step.active {
  opacity: 1;
  background: rgba(59, 130, 246, 0.1);
}

.FC_progress-step.active i {
  color: #3b82f6;
  animation: pulse 2s infinite;
}

.FC_progress-step.completed {
  opacity: 1;
}

.FC_progress-step.completed i {
  color: #22c55e;
}

.FC_progress-step.completed span {
  color: #22c55e;
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.1);
  }
}

.FC_progress-modal-footer {
  padding: 16px 24px;
  background: #f9fafb;
  border-top: 1px solid #e5e7eb;
  text-align: center;
}

.FC_progress-note {
  margin: 0;
  font-size: 0.875rem;
  color: #6b7280;
  font-style: italic;
}

@media (max-width: 640px) {
  .FC_progress-modal {
    width: 95%;
    margin: 20px;
  }
  
  .FC_progress-steps {
    flex-wrap: wrap;
  }
  
  .FC_progress-step {
    min-width: calc(50% - 4px);
  }
}
</style>

