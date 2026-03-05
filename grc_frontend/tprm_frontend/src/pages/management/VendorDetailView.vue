<template>
  <div class="vendor-detail-container">
    <!-- Header with Back Button -->
    <div class="detail-header">
      <button @click="goBack" class="back-btn">
        <i class="fas fa-arrow-left"></i>
        <span>Back to Vendors</span>
      </button>
      <h1 class="detail-title">Vendor Details</h1>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-container">
      <div class="spinner"></div>
      <p>Loading vendor details...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-container">
      <i class="fas fa-exclamation-triangle"></i>
      <p>{{ error }}</p>
      <button @click="fetchVendorDetails" class="btn btn-primary">Retry</button>
    </div>

    <!-- Vendor Details -->
    <div v-else-if="vendor" class="detail-content">
      <!-- Vendor Type Banner -->
      <div class="vendor-type-banner" :class="getBannerClass(vendor.vendor_type)">
        <i class="fas fa-info-circle"></i>
        <span>{{ vendor.vendor_type_label }}</span>
      </div>

      <!-- Tabs - Horizontal Layout -->
      <div class="tabs-container">
        <div class="tabs-wrapper">
          <button 
            v-for="tab in tabs" 
            :key="tab.id"
            class="tab"
            :class="{ active: activeTab === tab.id }"
            @click="activeTab = tab.id"
          >
            <i :class="tab.icon"></i>
            <span class="tab-label">{{ tab.label }}</span>
          </button>
        </div>

        <!-- Tab Content -->
        <div class="tab-content-wrapper">
          <div class="tab-content">
          <!-- Company Information Tab -->
          <div v-if="activeTab === 'company'" class="info-section">
            <h3 class="section-title">Company Information</h3>
            <div class="info-grid">
              <div class="info-item">
                <label>Vendor Code</label>
                <p>{{ vendor.vendor_code || 'N/A' }}</p>
              </div>
              <div class="info-item">
                <label>Company Name</label>
                <p>{{ vendor.company_name || 'N/A' }}</p>
              </div>
              <div class="info-item">
                <label>Legal Name</label>
                <p>{{ vendor.legal_name || 'N/A' }}</p>
              </div>
              <div class="info-item">
                <label>Business Type</label>
                <p>{{ vendor.business_type || 'N/A' }}</p>
              </div>
              <div class="info-item">
                <label>Industry Sector</label>
                <p>{{ vendor.industry_sector || 'N/A' }}</p>
              </div>
              <div class="info-item" v-if="!vendor.is_temporary">
                <label>Incorporation Date</label>
                <p>{{ formatDate(vendor.incorporation_date) }}</p>
              </div>
              <div class="info-item" v-if="!vendor.is_temporary">
                <label>Tax ID</label>
                <p>{{ vendor.tax_id || 'N/A' }}</p>
              </div>
              <div class="info-item" v-if="!vendor.is_temporary">
                <label>DUNS Number</label>
                <p>{{ vendor.duns_number || 'N/A' }}</p>
              </div>
              <div class="info-item">
                <label>Website</label>
                <p>
                  <a v-if="vendor.website" :href="vendor.website" target="_blank" class="link">
                    {{ vendor.website }}
                  </a>
                  <span v-else>N/A</span>
                </p>
              </div>
              <div class="info-item" v-if="!vendor.is_temporary">
                <label>Annual Revenue</label>
                <p>{{ formatCurrency(vendor.annual_revenue) }}</p>
              </div>
              <div class="info-item">
                <label>Employee Count</label>
                <p>{{ vendor.employee_count || 'N/A' }}</p>
              </div>
              <div class="info-item" v-if="!vendor.is_temporary">
                <label>Headquarters Country</label>
                <p>{{ vendor.headquarters_country || 'N/A' }}</p>
              </div>
              <div class="info-item full-width" v-if="!vendor.is_temporary">
                <label>Headquarters Address</label>
                <p>{{ vendor.headquarters_address || 'N/A' }}</p>
              </div>
              <div class="info-item full-width">
                <label>Description</label>
                <p>{{ vendor.description || 'N/A' }}</p>
              </div>
              <div class="info-item" v-if="!vendor.is_temporary && vendor.vendor_category_id">
                <label>Vendor Category ID</label>
                <p>{{ vendor.vendor_category_id }}</p>
              </div>
              <div class="info-item" v-if="!vendor.is_temporary && vendor.vendor_tier_id">
                <label>Vendor Tier ID</label>
                <p>{{ vendor.vendor_tier_id }}</p>
              </div>
              <div class="info-item" v-if="!vendor.is_temporary && vendor.parent_vendor_id">
                <label>Parent Vendor ID</label>
                <p>{{ vendor.parent_vendor_id }}</p>
              </div>
              <div class="info-item" v-if="!vendor.is_temporary && vendor.geographic_presence">
                <label>Geographic Presence</label>
                <p>{{ formatJSON(vendor.geographic_presence) }}</p>
              </div>
              <div class="info-item" v-if="!vendor.is_temporary && vendor.data_classification_handled">
                <label>Data Classification Handled</label>
                <p>{{ vendor.data_classification_handled }}</p>
              </div>
              <div class="info-item" v-if="!vendor.is_temporary && vendor.business_criticality">
                <label>Business Criticality</label>
                <p>{{ vendor.business_criticality }}</p>
              </div>
              <div class="info-item" v-if="!vendor.is_temporary && vendor.vendor_size_category">
                <label>Vendor Size Category</label>
                <p>{{ vendor.vendor_size_category }}</p>
              </div>
              <div class="info-item" v-if="!vendor.is_temporary">
                <label>Preferred Vendor</label>
                <p>{{ vendor.preferred_vendor_flag ? 'Yes' : 'No' }}</p>
              </div>
              <div class="info-item" v-if="!vendor.is_temporary && vendor.diversity_certification">
                <label>Diversity Certification</label>
                <p>{{ formatJSON(vendor.diversity_certification) }}</p>
              </div>
              <div class="info-item" v-if="!vendor.is_temporary && vendor.sustainability_rating">
                <label>Sustainability Rating</label>
                <p>{{ vendor.sustainability_rating }}</p>
              </div>
              <div class="info-item" v-if="!vendor.is_temporary && vendor.match_score">
                <label>Match Score</label>
                <p>{{ vendor.match_score }}</p>
              </div>
              <div class="info-item" v-if="!vendor.is_temporary && vendor.data_inventory">
                <label>Data Inventory</label>
                <p>{{ formatJSON(vendor.data_inventory) }}</p>
              </div>
              <div class="info-item" v-if="!vendor.is_temporary && vendor.retentionExpiry">
                <label>Retention Expiry</label>
                <p>{{ formatDate(vendor.retentionExpiry) }}</p>
              </div>
            </div>
          </div>

          <!-- External Screening Tab -->
          <div v-if="activeTab === 'screening'" class="info-section">
            <h3 class="section-title">External Screening Results</h3>
            
            <!-- Date Filters -->
            <div class="screening-filters">
              <div class="filter-group">
                <label>Start Date</label>
                <input 
                  type="date" 
                  v-model="screeningFilters.startDate" 
                  @change="fetchScreeningResults"
                  class="filter-input"
                />
              </div>
              <div class="filter-group">
                <label>End Date</label>
                <input 
                  type="date" 
                  v-model="screeningFilters.endDate" 
                  @change="fetchScreeningResults"
                  class="filter-input"
                />
              </div>
              <div class="filter-group">
                <button @click="clearScreeningFilters" class="btn btn-secondary btn-sm">
                  <i class="fas fa-times"></i> Clear Filters
                </button>
              </div>
            </div>

            <!-- Loading State -->
            <div v-if="screeningLoading" class="loading-state-small">
              <div class="spinner-small"></div>
              <p>Loading screening results...</p>
            </div>

            <!-- Error State -->
            <div v-else-if="screeningError" class="error-state-small">
              <i class="fas fa-exclamation-triangle"></i>
              <p>{{ screeningError }}</p>
              <button @click="fetchScreeningResults" class="btn btn-primary btn-sm">Retry</button>
            </div>

            <!-- Empty State -->
            <div v-else-if="!screeningData || screeningData.versions.length === 0" class="empty-state">
              <i class="fas fa-search"></i>
              <p>No screening results found</p>
              <p class="empty-state-subtitle">External screening results will appear here once screening is performed.</p>
            </div>

            <!-- Screening Results by Version -->
            <div v-else class="screening-versions">
              <div 
                v-for="version in screeningData.versions" 
                :key="version.version"
                class="screening-version"
              >
                <div class="version-header">
                  <h4 class="version-title">
                    <i class="fas fa-calendar-alt"></i>
                    Version: {{ formatDate(version.screening_date) }}
                  </h4>
                  <span class="version-badge">{{ version.results.length }} Screening{{ version.results.length !== 1 ? 's' : '' }}</span>
                </div>

                <!-- Screening Results for this Version -->
                <div class="screening-results-list">
                  <div 
                    v-for="result in version.results" 
                    :key="result.screening_id"
                    class="screening-result-card"
                  >
                    <div class="result-header">
                      <div class="result-title">
                        <i :class="getScreeningTypeIcon(result.screening_type)"></i>
                        <span class="result-type">{{ result.screening_type }}</span>
                        <span class="badge" :class="getScreeningStatusClass(result.status)">
                          {{ result.status }}
                        </span>
                      </div>
                      <div class="result-meta">
                        <span class="result-date">{{ formatDateTime(result.screening_date) }}</span>
                      </div>
                    </div>

                    <div class="result-stats">
                      <div class="stat-item">
                        <label>Total Matches</label>
                        <span class="stat-value">{{ result.total_matches }}</span>
                      </div>
                      <div class="stat-item">
                        <label>High Risk</label>
                        <span class="stat-value stat-high-risk">{{ result.high_risk_matches }}</span>
                      </div>
                      <div class="stat-item" v-if="result.search_terms">
                        <label>Search Terms</label>
                        <span class="stat-value">{{ formatSearchTerms(result.search_terms) }}</span>
                      </div>
                    </div>

                    <!-- Review Information -->
                    <div v-if="result.review_date || result.review_comments" class="result-review">
                      <div v-if="result.review_date" class="review-item">
                        <label>Reviewed On:</label>
                        <span>{{ formatDateTime(result.review_date) }}</span>
                      </div>
                      <div v-if="result.review_comments" class="review-item">
                        <label>Comments:</label>
                        <p>{{ result.review_comments }}</p>
                      </div>
                    </div>

                    <!-- Matches for this Screening Result -->
                    <div v-if="result.matches && result.matches.length > 0" class="matches-section">
                      <h5 class="matches-title">
                        <i class="fas fa-list"></i>
                        Matches ({{ result.matches.length }})
                      </h5>
                      <div class="matches-list">
                        <div 
                          v-for="match in result.matches" 
                          :key="match.match_id"
                          class="match-card"
                          :class="getMatchRiskClass(match.match_score)"
                        >
                          <div class="match-header">
                            <div class="match-type">
                              <i class="fas fa-flag"></i>
                              {{ match.match_type }}
                            </div>
                            <div class="match-score">
                              <span class="score-badge" :class="getScoreClass(match.match_score)">
                                Score: {{ match.match_score }}%
                              </span>
                            </div>
                          </div>
                          <div class="match-details" v-if="match.match_details">
                            <div v-for="(value, key) in match.match_details" :key="key" class="match-detail-item">
                              <label>{{ formatKey(key) }}:</label>
                              <span>{{ formatMatchValue(value) }}</span>
                            </div>
                          </div>
                          <div class="match-resolution" v-if="match.resolution_status || match.resolution_notes">
                            <div class="resolution-status">
                              <label>Resolution:</label>
                              <span class="badge" :class="getResolutionStatusClass(match.resolution_status)">
                                {{ match.resolution_status || 'PENDING' }}
                              </span>
                            </div>
                            <div v-if="match.resolution_notes" class="resolution-notes">
                              <label>Notes:</label>
                              <p>{{ match.resolution_notes }}</p>
                            </div>
                            <div v-if="match.resolved_date" class="resolution-date">
                              <label>Resolved:</label>
                              <span>{{ formatDateTime(match.resolved_date) }}</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                    <div v-else class="no-matches">
                      <i class="fas fa-check-circle"></i>
                      <span>No matches found</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- RFP Tab -->
          <div v-if="activeTab === 'rfp'" class="info-section">
            <h3 class="section-title">RFP Information</h3>
            
            <!-- Loading State -->
            <div v-if="rfpLoading" class="loading-state-small">
              <div class="spinner-small"></div>
              <p>Loading RFP data...</p>
            </div>

            <!-- Error State -->
            <div v-else-if="rfpError" class="error-state-small">
              <i class="fas fa-exclamation-triangle"></i>
              <p>{{ rfpError }}</p>
              <button @click="fetchRFPData" class="btn btn-primary btn-sm">Retry</button>
            </div>

            <!-- Empty State -->
            <div v-else-if="!rfpData" class="empty-state">
              <i class="fas fa-file-alt"></i>
              <p>No RFP data available</p>
            </div>

            <!-- RFP Data -->
            <div v-else class="rfp-content">
              <!-- RFP Response Information Section -->
              <div class="rfp-subsection">
                <h4 class="subsection-title">
                  <i class="fas fa-file-signature"></i>
                  RFP Response Information
                </h4>
                <div class="info-grid">
                  <div class="info-item">
                    <label>Response ID</label>
                    <p class="response-id">{{ rfpData.response?.response_id || 'N/A' }}</p>
                  </div>
                  <div class="info-item">
                    <label>RFP ID</label>
                    <p>{{ rfpData.response?.rfp_id || 'N/A' }}</p>
                  </div>
                  <div class="info-item">
                    <label>Vendor Name</label>
                    <p>{{ rfpData.response?.vendor_name || 'N/A' }}</p>
                  </div>
                  <div class="info-item">
                    <label>Organization</label>
                    <p>{{ rfpData.response?.org || 'N/A' }}</p>
                  </div>
                  <div class="info-item">
                    <label>Contact Email</label>
                    <p>
                      <a v-if="rfpData.response?.contact_email" :href="`mailto:${rfpData.response.contact_email}`" class="link">
                        {{ rfpData.response.contact_email }}
                      </a>
                      <span v-else>N/A</span>
                    </p>
                  </div>
                  <div class="info-item">
                    <label>Contact Phone</label>
                    <p>{{ rfpData.response?.contact_phone || 'N/A' }}</p>
                  </div>
                  <div class="info-item">
                    <label>Proposed Value</label>
                    <p>{{ formatCurrency(rfpData.response?.proposed_value) }}</p>
                  </div>
                  <div class="info-item">
                    <label>Evaluation Status</label>
                    <p>
                      <span 
                        v-if="rfpData.response?.evaluation_status"
                        class="badge"
                        :class="getStatusClass(rfpData.response.evaluation_status)"
                      >
                        {{ rfpData.response.evaluation_status }}
                      </span>
                      <span v-else>N/A</span>
                    </p>
                  </div>
                  <div class="info-item">
                    <label>Submission Date</label>
                    <p>{{ formatDateTime(rfpData.response?.submission_date || rfpData.response?.submitted_at) }}</p>
                  </div>
                  <div class="info-item" v-if="rfpData.response?.submitted_at && rfpData.response?.submission_date && rfpData.response.submitted_at !== rfpData.response.submission_date">
                    <label>Submitted At</label>
                    <p>{{ formatDateTime(rfpData.response.submitted_at) }}</p>
                  </div>
                  <div class="info-item">
                    <label>Technical Score</label>
                    <p>{{ rfpData.response?.technical_score !== null && rfpData.response?.technical_score !== undefined ? rfpData.response.technical_score : 'N/A' }}</p>
                  </div>
                  <div class="info-item">
                    <label>Commercial Score</label>
                    <p>{{ rfpData.response?.commercial_score !== null && rfpData.response?.commercial_score !== undefined ? rfpData.response.commercial_score : 'N/A' }}</p>
                  </div>
                  <div class="info-item">
                    <label>Overall Score</label>
                    <p>{{ rfpData.response?.overall_score !== null && rfpData.response?.overall_score !== undefined ? rfpData.response.overall_score : 'N/A' }}</p>
                  </div>
                  <div class="info-item" v-if="rfpData.response?.weighted_final_score">
                    <label>Weighted Final Score</label>
                    <p>{{ rfpData.response.weighted_final_score }}</p>
                  </div>
                  <div class="info-item" v-if="rfpData.response?.evaluation_date">
                    <label>Evaluation Date</label>
                    <p>{{ formatDateTime(rfpData.response.evaluation_date) }}</p>
                  </div>
                  <div class="info-item" v-if="rfpData.response?.completion_percentage">
                    <label>Completion Percentage</label>
                    <p>{{ rfpData.response.completion_percentage }}%</p>
                  </div>
                  <div class="info-item" v-if="rfpData.response?.submission_source">
                    <label>Submission Source</label>
                    <p>{{ rfpData.response.submission_source }}</p>
                  </div>
                  <div class="info-item full-width" v-if="rfpData.response?.evaluation_comments">
                    <label>Evaluation Comments</label>
                    <p>{{ rfpData.response.evaluation_comments }}</p>
                  </div>
                  <div class="info-item full-width" v-if="rfpData.response?.rejection_reason">
                    <label>Rejection Reason</label>
                    <p>{{ rfpData.response.rejection_reason }}</p>
                  </div>
                </div>

                <!-- Proposal Data Section -->
                <div v-if="rfpData.response?.proposal_data" class="rfp-subsection">
                  <h5 class="subsection-title">
                    <i class="fas fa-file-alt"></i>
                    Proposal Data
                  </h5>
                  <div class="json-data-container">
                    <JsonRenderer :data="rfpData.response.proposal_data" />
                  </div>
                </div>

                <!-- Response Documents Section -->
                <div v-if="rfpData.response?.response_documents" class="rfp-subsection">
                  <h5 class="subsection-title">
                    <i class="fas fa-file-alt"></i>
                    Response Documents
                  </h5>
                  <div class="json-data-container">
                    <JsonRenderer :data="rfpData.response.response_documents" />
                  </div>
                </div>

                <!-- Document URLs Section -->
                <div v-if="rfpData.response?.document_urls && Object.keys(rfpData.response.document_urls).length > 0" class="rfp-subsection">
                  <h5 class="subsection-title">
                    <i class="fas fa-paperclip"></i>
                    Response Documents
                  </h5>
                  <div class="documents-list">
                    <div 
                      v-for="(url, docName) in rfpData.response.document_urls" 
                      :key="docName"
                      class="document-card"
                    >
                      <i class="fas fa-file-alt document-icon"></i>
                      <div class="document-info">
                        <h4 class="document-name">{{ docName }}</h4>
                        <a :href="url" target="_blank" class="link">View Document</a>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- RFP Details Section -->
              <div v-if="rfpData.rfp" class="rfp-subsection">
                <h4 class="subsection-title">
                  <i class="fas fa-file-contract"></i>
                  RFP Details
                </h4>
                <div class="info-grid">
                  <div class="info-item">
                    <label>RFP Number</label>
                    <p>{{ rfpData.rfp.rfp_number || 'N/A' }}</p>
                  </div>
                  <div class="info-item">
                    <label>RFP Title</label>
                    <p>{{ rfpData.rfp.rfp_title || 'N/A' }}</p>
                  </div>
                  <div class="info-item">
                    <label>RFP Type</label>
                    <p>{{ rfpData.rfp.rfp_type || 'N/A' }}</p>
                  </div>
                  <div class="info-item">
                    <label>Category</label>
                    <p>{{ rfpData.rfp.category || 'N/A' }}</p>
                  </div>
                  <div class="info-item">
                    <label>Status</label>
                    <p>
                      <span 
                        v-if="rfpData.rfp.status"
                        class="badge"
                        :class="getStatusClass(rfpData.rfp.status)"
                      >
                        {{ rfpData.rfp.status }}
                      </span>
                      <span v-else>N/A</span>
                    </p>
                  </div>
                  <div class="info-item">
                    <label>Estimated Value</label>
                    <p>{{ formatCurrency(rfpData.rfp.estimated_value) }}</p>
                  </div>
                  <div class="info-item">
                    <label>Currency</label>
                    <p>{{ rfpData.rfp.currency || 'N/A' }}</p>
                  </div>
                  <div class="info-item">
                    <label>Budget Range</label>
                    <p v-if="rfpData.rfp.budget_range_min || rfpData.rfp.budget_range_max">
                      {{ formatCurrency(rfpData.rfp.budget_range_min) }} - {{ formatCurrency(rfpData.rfp.budget_range_max) }}
                    </p>
                    <p v-else>N/A</p>
                  </div>
                  <div class="info-item">
                    <label>Issue Date</label>
                    <p>{{ formatDate(rfpData.rfp.issue_date) }}</p>
                  </div>
                  <div class="info-item">
                    <label>Submission Deadline</label>
                    <p>{{ formatDateTime(rfpData.rfp.submission_deadline) }}</p>
                  </div>
                  <div class="info-item">
                    <label>Evaluation Period End</label>
                    <p>{{ formatDate(rfpData.rfp.evaluation_period_end) }}</p>
                  </div>
                  <div class="info-item">
                    <label>Award Date</label>
                    <p>{{ formatDate(rfpData.rfp.award_date) }}</p>
                  </div>
                  <div class="info-item">
                    <label>Criticality Level</label>
                    <p>
                      <span 
                        v-if="rfpData.rfp.criticality_level"
                        class="badge"
                        :class="getRiskLevelClass(rfpData.rfp.criticality_level.toUpperCase())"
                      >
                        {{ rfpData.rfp.criticality_level }}
                      </span>
                      <span v-else>N/A</span>
                    </p>
                  </div>
                  <div class="info-item">
                    <label>Evaluation Method</label>
                    <p>{{ rfpData.rfp.evaluation_method || 'N/A' }}</p>
                  </div>
                  <div class="info-item">
                    <label>Geographical Scope</label>
                    <p>{{ rfpData.rfp.geographical_scope || 'N/A' }}</p>
                  </div>
                  <div class="info-item" v-if="rfpData.rfp.final_evaluation_score">
                    <label>Final Evaluation Score</label>
                    <p>{{ rfpData.rfp.final_evaluation_score }}</p>
                  </div>
                  <div class="info-item full-width" v-if="rfpData.rfp.description">
                    <label>Description</label>
                    <p>{{ rfpData.rfp.description }}</p>
                  </div>
                  <div class="info-item full-width" v-if="rfpData.rfp.award_justification">
                    <label>Award Justification</label>
                    <p>{{ rfpData.rfp.award_justification }}</p>
                  </div>
                </div>

                <!-- RFP Documents Section -->
                <div v-if="rfpData.rfp.documents" class="rfp-subsection">
                  <h5 class="subsection-title">
                    <i class="fas fa-paperclip"></i>
                    RFP Documents
                  </h5>
                  <div class="json-data-container">
                    <JsonRenderer :data="rfpData.rfp.documents" />
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Risk & Status Tab -->
          <div v-if="activeTab === 'risk'" class="info-section">
            <h3 class="section-title">Risk & Status Information</h3>
            <div class="info-grid">
              <div class="info-item">
                <label>Risk Level</label>
                <p>
                  <span 
                    v-if="vendor.risk_level" 
                    class="badge"
                    :class="getRiskLevelClass(vendor.risk_level)"
                  >
                    {{ vendor.risk_level }}
                  </span>
                  <span v-else>N/A</span>
                </p>
              </div>
              <div class="info-item">
                <label>Status</label>
                <p>
                  <span 
                    v-if="vendor.status" 
                    class="badge"
                    :class="getStatusClass(vendor.status)"
                  >
                    {{ vendor.status }}
                  </span>
                  <span v-else>N/A</span>
                </p>
              </div>
              <div class="info-item">
                <label>Lifecycle Stage</label>
                <p>{{ vendor.lifecycle_stage || 'N/A' }}</p>
              </div>
              <div class="info-item">
                <label>Critical Vendor</label>
                <p>
                  <span :class="vendor.is_critical_vendor ? 'text-danger' : 'text-muted'">
                    {{ vendor.is_critical_vendor ? 'Yes' : 'No' }}
                  </span>
                </p>
              </div>
              <div class="info-item">
                <label>Has Data Access</label>
                <p>
                  <span :class="vendor.has_data_access ? 'text-info' : 'text-muted'">
                    {{ vendor.has_data_access ? 'Yes' : 'No' }}
                  </span>
                </p>
              </div>
              <div class="info-item">
                <label>Has System Access</label>
                <p>
                  <span :class="vendor.has_system_access ? 'text-info' : 'text-muted'">
                    {{ vendor.has_system_access ? 'Yes' : 'No' }}
                  </span>
                </p>
              </div>
              <div class="info-item" v-if="!vendor.is_temporary">
                <label>Onboarding Date</label>
                <p>{{ formatDate(vendor.onboarding_date) }}</p>
              </div>
              <div class="info-item" v-if="!vendor.is_temporary">
                <label>Last Assessment Date</label>
                <p>{{ formatDate(vendor.last_assessment_date) }}</p>
              </div>
              <div class="info-item" v-if="!vendor.is_temporary">
                <label>Next Assessment Date</label>
                <p>{{ formatDate(vendor.next_assessment_date) }}</p>
              </div>
              <div class="info-item" v-if="vendor.response_id">
                <label>RFP Response ID</label>
                <p class="response-id">{{ vendor.response_id }}</p>
              </div>
            </div>
          </div>

          <!-- Contacts Tab (for temporary vendors with JSON contacts) -->
          <div v-if="activeTab === 'contacts'" class="info-section">
            <h3 class="section-title">Contact Information</h3>
            <div v-if="vendor.contacts && vendor.contacts.length > 0" class="contacts-list">
              <div 
                v-for="(contact, index) in vendor.contacts" 
                :key="index"
                class="contact-card"
              >
                <h4 class="contact-name">{{ contact.name || 'N/A' }}</h4>
                <div class="contact-details">
                  <div v-if="contact.email" class="contact-detail">
                    <i class="fas fa-envelope"></i>
                    <a :href="`mailto:${contact.email}`">{{ contact.email }}</a>
                  </div>
                  <div v-if="contact.phone" class="contact-detail">
                    <i class="fas fa-phone"></i>
                    <span>{{ contact.phone }}</span>
                  </div>
                  <div v-if="contact.designation" class="contact-detail">
                    <i class="fas fa-briefcase"></i>
                    <span>{{ contact.designation }}</span>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="empty-state">
              <i class="fas fa-address-book"></i>
              <p>No contact information available</p>
            </div>
          </div>

          <!-- Documents Tab (for temporary vendors with JSON documents) -->
          <div v-if="activeTab === 'documents'" class="info-section">
            <h3 class="section-title">Documents</h3>
            <div v-if="vendor.documents && vendor.documents.length > 0" class="documents-list">
              <div 
                v-for="(document, index) in vendor.documents" 
                :key="index"
                class="document-card"
              >
                <i class="fas fa-file-alt document-icon"></i>
                <div class="document-info">
                  <h4 class="document-name">{{ document.name || 'Document' }}</h4>
                  <p class="document-type">{{ document.type || 'Unknown Type' }}</p>
                </div>
              </div>
            </div>
            <div v-else class="empty-state">
              <i class="fas fa-folder-open"></i>
              <p>No documents available</p>
            </div>
          </div>

          <!-- Contracts Tab -->
          <div v-if="activeTab === 'contracts'" class="info-section">
            <h3 class="section-title">Vendor Contracts</h3>
            <div v-if="vendor.related_data && vendor.related_data.contracts && vendor.related_data.contracts.length > 0" class="contracts-list">
              <div
                v-for="contract in vendor.related_data.contracts"
                :key="contract.contract_id"
                class="contract-card"
                style="display: flex; align-items: center; justify-content: space-between; padding: 14px 18px;"
              >
                <div style="display: flex; align-items: center; gap: 12px;">
                  <i class="fas fa-file-contract" style="color: var(--primary, #4f46e5); font-size: 16px;"></i>
                  <div>
                    <h4 class="contract-title" style="margin: 0 0 2px 0; font-size: 15px;">{{ contract.contract_title || 'Untitled Contract' }}</h4>
                    <span class="contract-number" style="font-size: 12px; color: #6b7280;">{{ contract.contract_number }}</span>
                  </div>
                </div>
                <button
                  class="btn-view-contract"
                  @click="viewContract(contract.contract_id)"
                  style="display: flex; align-items: center; gap: 6px; padding: 7px 16px; background: #4f46e5; color: #fff; border: none; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 500; transition: background 0.2s;"
                  onmouseover="this.style.background='#4338ca'"
                  onmouseout="this.style.background='#4f46e5'"
                >
                  <i class="fas fa-eye"></i>
                  View
                </button>
              </div>
            </div>
            <div v-else class="empty-state">
              <i class="fas fa-file-contract"></i>
              <p>No contracts found for this vendor</p>
            </div>
          </div>

          <!-- SLAs Tab -->
          <div v-if="activeTab === 'slas'" class="info-section">
            <h3 class="section-title">Service Level Agreements (SLAs)</h3>
            <div v-if="vendor.related_data && vendor.related_data.slas && vendor.related_data.slas.length > 0" class="slas-list">
              <div
                v-for="sla in vendor.related_data.slas"
                :key="sla.sla_id"
                class="sla-card"
                style="display: flex; align-items: center; justify-content: space-between; padding: 14px 18px;"
              >
                <div style="display: flex; align-items: center; gap: 12px;">
                  <i class="fas fa-chart-line" style="color: var(--primary, #4f46e5); font-size: 16px;"></i>
                  <div>
                    <h4 class="sla-name" style="margin: 0 0 4px 0; font-size: 15px;">{{ sla.sla_name || 'Untitled SLA' }}</h4>
                    <span class="badge" :class="getStatusClass(sla.status)" style="font-size: 11px;">{{ sla.status || 'N/A' }}</span>
                  </div>
                </div>
                <button
                  @click="viewSla(sla.sla_id)"
                  style="display: flex; align-items: center; gap: 6px; padding: 7px 16px; background: #4f46e5; color: #fff; border: none; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 500; transition: background 0.2s;"
                  onmouseover="this.style.background='#4338ca'"
                  onmouseout="this.style.background='#4f46e5'"
                >
                  <i class="fas fa-eye"></i>
                  View
                </button>
              </div>
            </div>
            <div v-else class="empty-state">
              <i class="fas fa-chart-line"></i>
              <p>No SLAs found for this vendor</p>
            </div>
          </div>

          <!-- BCP/DRP Plans Tab -->
          <div v-if="activeTab === 'bcp_plans'" class="info-section">
            <h3 class="section-title">BCP/DRP Plans</h3>
            <div v-if="vendor.related_data && vendor.related_data.bcp_drp_plans && vendor.related_data.bcp_drp_plans.length > 0" class="plans-list">
              <div
                v-for="plan in vendor.related_data.bcp_drp_plans"
                :key="plan.plan_id"
                class="plan-card"
                style="display: flex; align-items: center; justify-content: space-between; padding: 14px 18px;"
              >
                <div style="display: flex; align-items: center; gap: 12px;">
                  <i class="fas fa-clipboard-list" style="color: var(--primary, #4f46e5); font-size: 16px;"></i>
                  <div>
                    <h4 class="plan-name" style="margin: 0 0 4px 0; font-size: 15px;">{{ plan.plan_name || 'Untitled Plan' }}</h4>
                    <div style="display: flex; align-items: center; gap: 6px;">
                      <span style="font-size: 11px; color: #6b7280;">{{ plan.plan_type || '' }}</span>
                      <span v-if="plan.plan_type && plan.criticality" style="font-size: 11px; color: #6b7280;">•</span>
                      <span class="badge" :class="getRiskLevelClass(plan.criticality)" style="font-size: 11px;">{{ plan.criticality || '' }}</span>
                    </div>
                  </div>
                </div>
                <button
                  @click="viewBcpPlan(plan.plan_id)"
                  style="display: flex; align-items: center; gap: 6px; padding: 7px 16px; background: #4f46e5; color: #fff; border: none; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 500; transition: background 0.2s;"
                  onmouseover="this.style.background='#4338ca'"
                  onmouseout="this.style.background='#4f46e5'"
                >
                  <i class="fas fa-eye"></i>
                  View
                </button>
              </div>
            </div>
            <div v-else class="empty-state">
              <i class="fas fa-clipboard-list"></i>
              <p>No BCP/DRP plans found for this vendor</p>
            </div>
          </div>

          <!-- Audit Trail Tab -->
          <div v-if="activeTab === 'audit'" class="info-section">
            <h3 class="section-title">Audit Trail & Performance</h3>
            
            <!-- Vendor Record Audit -->
            <div class="audit-subsection">
              <h4 class="subsection-title">
                <i class="fas fa-history"></i>
                Vendor Record History
              </h4>
              <div class="info-grid">
                <div class="info-item" v-if="!vendor.is_temporary && vendor.created_by">
                  <label>Created By</label>
                  <p>{{ vendor.created_by }}</p>
                </div>
                <div class="info-item">
                  <label>Created At</label>
                  <p>{{ formatDateTime(vendor.created_at) }}</p>
                </div>
                <div class="info-item" v-if="!vendor.is_temporary && vendor.updated_by">
                  <label>Updated By</label>
                  <p>{{ vendor.updated_by }}</p>
                </div>
                <div class="info-item">
                  <label>Updated At</label>
                  <p>{{ formatDateTime(vendor.updated_at) }}</p>
                </div>
                <div class="info-item" v-if="vendor.is_temporary && vendor.UserId">
                  <label>User ID</label>
                  <p>{{ vendor.UserId }}</p>
                </div>
              </div>
            </div>

            <!-- Contract Audits -->
            <div class="audit-subsection" v-if="vendor.related_data && (vendor.related_data.contract_audits?.length > 0 || vendor.related_data.sla_audits?.length > 0)">
              <h4 class="subsection-title">
                <i class="fas fa-file-contract"></i>
                Contract Audits
              </h4>
              <div v-if="vendor.related_data.contract_audits && vendor.related_data.contract_audits.length > 0" class="audits-list">
                <div 
                  v-for="audit in vendor.related_data.contract_audits" 
                  :key="audit.audit_id"
                  class="audit-card"
                >
                  <div class="audit-header">
                    <h5 class="audit-title">{{ audit.title || 'Contract Audit' }}</h5>
                    <div class="audit-badges">
                      <span class="badge" :class="getAuditStatusClass(audit.status)">{{ audit.status || 'N/A' }}</span>
                      <span class="badge" :class="getReviewStatusClass(audit.review_status)">{{ audit.review_status || 'N/A' }}</span>
                      <button
                        class="btn-download-report"
                        @click="generateAuditReport(audit)"
                        :disabled="downloadingReportId === audit.audit_id"
                        title="Download Audit Report PDF"
                      >
                        <i v-if="downloadingReportId === audit.audit_id" class="fas fa-spinner fa-spin"></i>
                        <i v-else class="fas fa-file-download"></i>
                        {{ downloadingReportId === audit.audit_id ? 'Generating...' : 'Download Report' }}
                      </button>
                    </div>
                  </div>
                  <div class="audit-body">
                    <div class="audit-info-grid">
                      <div class="audit-info-item">
                        <i class="fas fa-user-tie"></i>
                        <div>
                          <label>Audit Type</label>
                          <p>{{ audit.audit_type || 'N/A' }}</p>
                        </div>
                      </div>
                      <div class="audit-info-item">
                        <i class="fas fa-calendar-alt"></i>
                        <div>
                          <label>Assigned</label>
                          <p>{{ formatDate(audit.assign_date) }}</p>
                        </div>
                      </div>
                      <div class="audit-info-item">
                        <i class="fas fa-calendar-check"></i>
                        <div>
                          <label>Due Date</label>
                          <p>{{ formatDate(audit.due_date) }}</p>
                        </div>
                      </div>
                      <div class="audit-info-item">
                        <i class="fas fa-sync-alt"></i>
                        <div>
                          <label>Frequency</label>
                          <p>{{ audit.frequency || 'N/A' }}</p>
                        </div>
                      </div>
                    </div>
                    <div v-if="audit.scope" class="audit-scope">
                      <label>Scope:</label>
                      <p>{{ audit.scope }}</p>
                    </div>
                    <div v-if="audit.review_comments" class="audit-comments">
                      <label>Review Comments:</label>
                      <p>{{ audit.review_comments }}</p>
                    </div>
                    <!-- Contract Audit Findings -->
                    <div v-if="getContractAuditFindings(audit.audit_id).length > 0" class="audit-findings">
                      <label><i class="fas fa-exclamation-triangle"></i> Findings ({{ getContractAuditFindings(audit.audit_id).length }})</label>
                      <div class="findings-list">
                        <div 
                          v-for="finding in getContractAuditFindings(audit.audit_id)" 
                          :key="finding.audit_finding_id"
                          class="finding-item"
                        >
                          <div class="finding-header">
                            <span class="finding-date">{{ formatDate(finding.check_date) }}</span>
                          </div>
                          <p v-if="finding.details_of_finding" class="finding-details">{{ finding.details_of_finding }}</p>
                          <p v-if="finding.impact_recommendations" class="finding-impact"><strong>Impact:</strong> {{ finding.impact_recommendations }}</p>
                          <p v-if="finding.comment" class="finding-comment"><strong>Comment:</strong> {{ finding.comment }}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div v-else class="empty-state-small">
                <i class="fas fa-clipboard-check"></i>
                <p>No contract audits performed yet</p>
              </div>
            </div>

            <!-- SLA Audits -->
            <div class="audit-subsection" v-if="vendor.related_data && vendor.related_data.sla_audits?.length > 0">
              <h4 class="subsection-title">
                <i class="fas fa-chart-line"></i>
                SLA Performance Audits
              </h4>
              <div class="audits-list">
                <div 
                  v-for="audit in vendor.related_data.sla_audits" 
                  :key="audit.audit_id"
                  class="audit-card"
                >
                  <div class="audit-header">
                    <h5 class="audit-title">{{ audit.title || 'SLA Audit' }}</h5>
                    <div class="audit-badges">
                      <span class="badge" :class="getAuditStatusClass(audit.status)">{{ audit.status || 'N/A' }}</span>
                      <span class="badge" :class="getReviewStatusClass(audit.review_status)">{{ audit.review_status || 'N/A' }}</span>
                      <button
                        class="btn-download-report"
                        @click="generateSLAAuditReport(audit)"
                        :disabled="downloadingSLAReportId === audit.audit_id"
                        title="Download SLA Audit Report PDF"
                      >
                        <i v-if="downloadingSLAReportId === audit.audit_id" class="fas fa-spinner fa-spin"></i>
                        <i v-else class="fas fa-file-download"></i>
                        {{ downloadingSLAReportId === audit.audit_id ? 'Generating...' : 'Download Report' }}
                      </button>
                    </div>
                  </div>
                  <div class="audit-body">
                    <div class="audit-info-grid">
                      <div class="audit-info-item">
                        <i class="fas fa-user-tie"></i>
                        <div>
                          <label>Audit Type</label>
                          <p>{{ audit.audit_type || 'N/A' }}</p>
                        </div>
                      </div>
                      <div class="audit-info-item">
                        <i class="fas fa-calendar-alt"></i>
                        <div>
                          <label>Assigned</label>
                          <p>{{ formatDate(audit.assign_date) }}</p>
                        </div>
                      </div>
                      <div class="audit-info-item">
                        <i class="fas fa-calendar-check"></i>
                        <div>
                          <label>Due Date</label>
                          <p>{{ formatDate(audit.due_date) }}</p>
                        </div>
                      </div>
                      <div class="audit-info-item">
                        <i class="fas fa-sync-alt"></i>
                        <div>
                          <label>Frequency</label>
                          <p>{{ audit.frequency || 'N/A' }}</p>
                        </div>
                      </div>
                    </div>
                    <div v-if="audit.scope" class="audit-scope">
                      <label>Scope:</label>
                      <p>{{ audit.scope }}</p>
                    </div>
                    <div v-if="audit.review_comments" class="audit-comments">
                      <label>Review Comments:</label>
                      <p>{{ audit.review_comments }}</p>
                    </div>
                    <!-- SLA Audit Findings -->
                    <div v-if="getSLAAuditFindings(audit.audit_id).length > 0" class="audit-findings">
                      <label><i class="fas fa-exclamation-triangle"></i> Findings ({{ getSLAAuditFindings(audit.audit_id).length }})</label>
                      <div class="findings-list">
                        <div 
                          v-for="finding in getSLAAuditFindings(audit.audit_id)" 
                          :key="finding.audit_finding_id"
                          class="finding-item"
                        >
                          <div class="finding-header">
                            <span class="finding-date">{{ formatDate(finding.check_date) }}</span>
                          </div>
                          <p v-if="finding.details_of_finding" class="finding-details">{{ finding.details_of_finding }}</p>
                          <p v-if="finding.impact_recommendations" class="finding-impact"><strong>Impact:</strong> {{ finding.impact_recommendations }}</p>
                          <p v-if="finding.comment" class="finding-comment"><strong>Comment:</strong> {{ finding.comment }}</p>
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
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import axios from '@/config/axios'
import jsPDF from 'jspdf'
import contractAuditApi from '@/services/contractAuditApi.js'
import apiService from '@/services/api.js'
import { PopupService } from '@/popup/popupService'

// JsonRenderer Component - Recursively renders JSON data in a clean, structured format
const JsonRenderer = {
  name: 'JsonRenderer',
  props: {
    data: {
      type: [Object, Array, String, Number, Boolean],
      required: true
    },
    level: {
      type: Number,
      default: 0
    },
    keyName: {
      type: String,
      default: ''
    }
  },
  setup(props) {
    const isExpanded = ref(props.level < 2) // Auto-expand first 2 levels
    
    const toggleExpand = () => {
      isExpanded.value = !isExpanded.value
    }
    
    const formatValue = (value) => {
      if (value === null || value === undefined || value === '') {
        return { type: 'empty', display: 'N/A' }
      }
      
      if (typeof value === 'string') {
        // Check if it's a URL
        if (value.startsWith('http://') || value.startsWith('https://')) {
          return { type: 'url', display: value, url: value }
        }
        // Check if it's an email
        if (value.includes('@') && value.includes('.') && !value.includes(' ')) {
          return { type: 'email', display: value, email: value }
        }
        // Check if it's a date string
        if (/^\d{4}-\d{2}-\d{2}/.test(value) && value.includes('T')) {
          try {
            const date = new Date(value)
            return { 
              type: 'date', 
              display: date.toLocaleString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
              })
            }
          } catch (e) {
            return { type: 'string', display: value }
          }
        }
        return { type: 'string', display: value }
      }
      
      if (typeof value === 'number') {
        return { type: 'number', display: value.toLocaleString('en-US') }
      }
      
      if (typeof value === 'boolean') {
        return { type: 'boolean', display: value ? 'Yes' : 'No', value: value }
      }
      
      return { type: 'string', display: String(value) }
    }
    
    const formatKey = (key) => {
      // Convert camelCase or snake_case to Title Case
      return key
        .replace(/([A-Z])/g, ' $1')
        .replace(/_/g, ' ')
        .replace(/^./, str => str.toUpperCase())
        .trim()
    }
    
    const isSpecialSection = (key) => {
      const specialKeys = ['companyInfo', 'keyPersonnel', 'metadata', 'teamInfo', 'documents', 'document_urls', 'response_documents']
      return specialKeys.includes(key)
    }
    
    const isPersonnelItem = (item) => {
      return item && typeof item === 'object' && (item.name || item.email || item.role)
    }
    
    const isDocumentItem = (item) => {
      return item && typeof item === 'object' && (item.url || item.filename || item.key || (typeof item === 'object' && !Array.isArray(item) && Object.keys(item).some(k => k.toLowerCase().includes('url') || k.toLowerCase().includes('file'))))
    }
    
    const renderDocumentObject = (docObj) => {
      // Handle nested document objects like { technical_proposal: { url: ..., filename: ... } }
      const docs = []
      for (const [key, value] of Object.entries(docObj)) {
        if (value && typeof value === 'object' && (value.url || value.filename || value.key)) {
          docs.push({ name: key, ...value })
        } else if (typeof value === 'string' && (value.startsWith('http://') || value.startsWith('https://'))) {
          docs.push({ name: key, url: value })
        }
      }
      return docs
    }
    
    return {
      isExpanded,
      toggleExpand,
      formatValue,
      formatKey,
      isSpecialSection,
      isPersonnelItem,
      isDocumentItem,
      renderDocumentObject
    }
  },
  template: `
    <div class="json-renderer" :class="'json-level-' + level">
      <!-- Array with special handling for personnel and documents -->
      <div v-if="Array.isArray(data)" class="json-array">
        <div v-if="isPersonnelItem(data[0])" class="personnel-grid">
          <div v-for="(person, index) in data" :key="index" class="personnel-card">
            <div class="personnel-header">
              <i class="fas fa-user-tie"></i>
              <h4>{{ person.name || 'Unknown' }}</h4>
            </div>
            <div class="personnel-details">
              <div v-if="person.role" class="detail-item">
                <label>Role:</label>
                <span>{{ person.role }}</span>
              </div>
              <div v-if="person.email" class="detail-item">
                <label>Email:</label>
                <a :href="'mailto:' + person.email" class="json-link">
                  <i class="fas fa-envelope"></i> {{ person.email }}
                </a>
              </div>
              <div v-if="person.phone" class="detail-item">
                <label>Phone:</label>
                <span>{{ person.phone }}</span>
              </div>
              <div v-if="person.education" class="detail-item">
                <label>Education:</label>
                <span>{{ person.education }}</span>
              </div>
              <div v-if="person.experience" class="detail-item">
                <label>Experience:</label>
                <span>{{ person.experience }} year{{ person.experience !== 1 ? 's' : '' }}</span>
              </div>
              <div v-if="person.certifications && person.certifications.length > 0" class="detail-item">
                <label>Certifications:</label>
                <div class="certifications-list">
                  <span v-for="(cert, idx) in person.certifications" :key="idx" class="cert-badge">
                    {{ cert }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div v-else-if="isDocumentItem(data[0])" class="documents-grid">
          <div v-for="(doc, index) in data" :key="index" class="document-item-card">
            <i class="fas fa-file-alt"></i>
            <div class="document-details">
              <div v-if="doc.filename || doc.key" class="doc-name">{{ doc.filename || doc.key }}</div>
              <div v-if="doc.url" class="doc-url">
                <a :href="doc.url" target="_blank" class="json-link">
                  <i class="fas fa-external-link-alt"></i> View Document
                </a>
              </div>
              <div v-if="doc.size" class="doc-size">Size: {{ (doc.size / 1024).toFixed(2) }} KB</div>
              <div v-if="doc.content_type" class="doc-type">{{ doc.content_type }}</div>
            </div>
          </div>
        </div>
        <div v-else-if="data.length > 0" class="clean-array-container">
          <div v-for="(item, index) in data" :key="index" class="clean-array-item">
            <JsonRenderer :data="item" :level="level + 1" />
          </div>
        </div>
        <div v-else class="json-empty">
          <i class="fas fa-inbox"></i>
          <span>No items</span>
        </div>
      </div>
      
      <!-- Object with clean section-based layout -->
      <div v-else-if="data !== null && typeof data === 'object'" class="clean-object-container">
        <!-- Top-level proposal data -->
        <template v-if="level === 0">
          <div v-for="(value, key) in data" :key="key" class="clean-section">
            <!-- Organization -->
            <div v-if="key === 'org'" class="clean-field-row">
              <label>Organization:</label>
              <span class="clean-value">{{ value || 'N/A' }}</span>
            </div>
            
            <!-- Metadata Section -->
            <div v-else-if="key === 'metadata'" class="clean-section-card">
              <h5 class="section-header">
                <i class="fas fa-info-circle"></i>
                Metadata
              </h5>
              <div class="metadata-grid">
                <div v-for="(metaValue, metaKey) in value" :key="metaKey" class="metadata-field">
                  <label>{{ formatKey(metaKey) }}</label>
                  <JsonRenderer :data="metaValue" :level="level + 1" :key-name="metaKey" />
                </div>
              </div>
            </div>
            
            <!-- Team Info Section -->
            <div v-else-if="key === 'teamInfo' || key === 'team_info'" class="clean-section-card">
              <h5 class="section-header">
                <i class="fas fa-users"></i>
                Team Information
              </h5>
              <JsonRenderer :data="value" :level="level + 1" :key-name="key" />
            </div>
            
            <!-- Company Info Section -->
            <div v-else-if="key === 'companyInfo' || key === 'company_info'" class="clean-section-card">
              <h5 class="section-header">
                <i class="fas fa-building"></i>
                Company Information
              </h5>
              <div class="info-grid-clean">
                <div v-for="(infoValue, infoKey) in value" :key="infoKey" class="info-item-clean">
                  <label>{{ formatKey(infoKey) }}</label>
                  <div class="info-value">
                    <template v-if="formatValue(infoValue).type === 'url'">
                      <a :href="formatValue(infoValue).url" target="_blank" class="json-link" rel="noopener noreferrer">
                        <i class="fas fa-external-link-alt"></i> {{ formatValue(infoValue).display }}
                      </a>
                    </template>
                    <template v-else-if="formatValue(infoValue).type === 'email'">
                      <a :href="'mailto:' + formatValue(infoValue).email" class="json-link">
                        <i class="fas fa-envelope"></i> {{ formatValue(infoValue).display }}
                      </a>
                    </template>
                    <template v-else-if="formatValue(infoValue).type === 'boolean'">
                      <span :class="'badge badge-' + (infoValue ? 'success' : 'secondary')">
                        {{ formatValue(infoValue).display }}
                      </span>
                    </template>
                    <template v-else>
                      <span :class="'json-value json-' + formatValue(infoValue).type">
                        {{ formatValue(infoValue).display }}
                      </span>
                    </template>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Default field -->
            <div v-else class="clean-field-row">
              <label>{{ formatKey(key) }}:</label>
              <JsonRenderer :data="value" :level="level + 1" :key-name="key" />
            </div>
          </div>
        </template>
        
        <!-- Nested objects -->
        <template v-else>
          <!-- Key Personnel -->
          <div v-if="keyName === 'keyPersonnel' || keyName === 'key_personnel'" class="key-personnel-section">
            <h6 class="subsection-header">
              <i class="fas fa-user-tie"></i>
              Key Personnel
            </h6>
            <JsonRenderer :data="data" :level="level + 1" :key-name="keyName" />
          </div>
          
          <!-- Document Objects -->
          <div v-else-if="isDocumentItem(Object.values(data)[0])" class="documents-grid">
            <div v-for="(value, key) in data" :key="key" class="document-item-card">
              <i class="fas fa-file-alt"></i>
              <div class="document-details">
                <div class="doc-name">{{ formatKey(key) }}</div>
                <template v-if="typeof value === 'object' && value !== null">
                  <div v-if="value.url" class="doc-url">
                    <a :href="value.url" target="_blank" class="json-link">
                      <i class="fas fa-external-link-alt"></i> View Document
                    </a>
                  </div>
                  <div v-if="value.filename || value.key" class="doc-name">{{ value.filename || value.key }}</div>
                  <div v-if="value.size" class="doc-size">Size: {{ (value.size / 1024).toFixed(2) }} KB</div>
                  <div v-if="value.content_type" class="doc-type">{{ value.content_type }}</div>
                  <div v-if="value.upload_date" class="doc-date">Uploaded: {{ formatValue(value.upload_date).display }}</div>
                </template>
                <template v-else-if="typeof value === 'string' && (value.startsWith('http://') || value.startsWith('https://'))">
                  <div class="doc-url">
                    <a :href="value" target="_blank" class="json-link">
                      <i class="fas fa-external-link-alt"></i> View Document
                    </a>
                  </div>
                </template>
              </div>
            </div>
          </div>
          
          <!-- Metadata nested -->
          <div v-else-if="keyName === 'metadata' || keyName === 'utmParameters' || keyName === 'utm_parameters'" class="metadata-nested">
            <div v-for="(value, key) in data" :key="key" class="metadata-field">
              <label>{{ formatKey(key) }}</label>
              <JsonRenderer :data="value" :level="level + 1" :key-name="key" />
            </div>
          </div>
          
          <!-- Team Info nested -->
          <div v-else-if="keyName === 'teamInfo' || keyName === 'team_info'" class="team-info-nested">
            <div v-for="(value, key) in data" :key="key" class="team-field">
              <label>{{ formatKey(key) }}</label>
              <JsonRenderer :data="value" :level="level + 1" :key-name="key" />
            </div>
          </div>
          
          <!-- Regular nested object -->
          <div v-else class="clean-nested-object">
            <div v-for="(value, key) in data" :key="key" class="clean-field-row">
              <label>{{ formatKey(key) }}:</label>
              <JsonRenderer :data="value" :level="level + 1" :key-name="key" />
            </div>
          </div>
        </template>
      </div>
      
      <!-- Primitive Value -->
      <div v-else class="clean-primitive">
        <template v-if="formatValue(data).type === 'url'">
          <a :href="formatValue(data).url" target="_blank" class="json-link" rel="noopener noreferrer">
            <i class="fas fa-external-link-alt"></i> {{ formatValue(data).display }}
          </a>
        </template>
        <template v-else-if="formatValue(data).type === 'email'">
          <a :href="'mailto:' + formatValue(data).email" class="json-link">
            <i class="fas fa-envelope"></i> {{ formatValue(data).display }}
          </a>
        </template>
        <template v-else-if="formatValue(data).type === 'boolean'">
          <span :class="'badge badge-' + (data ? 'success' : 'secondary')">
            {{ formatValue(data).display }}
          </span>
        </template>
        <template v-else>
          <span :class="'clean-value clean-' + formatValue(data).type">{{ formatValue(data).display }}</span>
        </template>
      </div>
    </div>
  `
}

export default {
  name: 'VendorDetailView',
  components: {
    JsonRenderer
  },
  props: {
    vendorCode: {
      type: String,
      required: true
    },
    initialTab: {
      type: String,
      default: null
    }
  },
  emits: ['back'],
  setup(props, { emit }) {
    const router = useRouter()
    const vendor = ref(null)
    const loading = ref(false)
    const error = ref(null)
    const activeTab = ref(props.initialTab || 'company')
    const screeningData = ref(null)
    const screeningLoading = ref(false)
    const screeningError = ref(null)
    const screeningFilters = ref({
      startDate: '',
      endDate: ''
    })
    const rfpData = ref(null)
    const rfpLoading = ref(false)
    const rfpError = ref(null)

    const tabs = computed(() => {
      const baseTabs = [
        { id: 'company', label: 'Company Info', icon: 'fas fa-building' },
        { id: 'risk', label: 'Risk & Status', icon: 'fas fa-shield-alt' },
        { id: 'screening', label: 'External Screening', icon: 'fas fa-search' },
        { id: 'contracts', label: 'Contracts', icon: 'fas fa-file-contract' },
        { id: 'slas', label: 'SLAs', icon: 'fas fa-chart-line' },
        { id: 'bcp_plans', label: 'BCP/DRP Plans', icon: 'fas fa-clipboard-list' },
        { id: 'audit', label: 'Audit Trail', icon: 'fas fa-history' }
      ]

      // Add RFP tab for vendors with RFP (ONBOARDED_WITH_RFP or TEMPORARY_WITH_RFP)
      if (vendor.value && (vendor.value.vendor_type === 'ONBOARDED_WITH_RFP' || vendor.value.vendor_type === 'TEMPORARY_WITH_RFP')) {
        baseTabs.splice(3, 0, { id: 'rfp', label: 'RFP', icon: 'fas fa-file-alt' })
      }

      // Add contacts and documents tabs for temporary vendors
      if (vendor.value?.is_temporary) {
        baseTabs.splice(2, 0, 
          { id: 'contacts', label: 'Contacts', icon: 'fas fa-address-book' },
          { id: 'documents', label: 'Documents', icon: 'fas fa-file-alt' }
        )
      }

      return baseTabs
    })

    const fetchVendorDetails = async () => {
      loading.value = true
      error.value = null

      try {
        const response = await axios.get(`/api/v1/management/vendors/${props.vendorCode}/`)

        if (response.data.success) {
          vendor.value = response.data.data
          
          // Log related data for debugging
          console.log('[VendorDetailView] Vendor data loaded:', {
            vendor_code: vendor.value.vendor_code,
            response_id: vendor.value.response_id,
            vendor_type: vendor.value.vendor_type,
            has_related_data: !!vendor.value.related_data,
            contracts_count: vendor.value.related_data?.contracts?.length || 0,
            slas_count: vendor.value.related_data?.slas?.length || 0,
            plans_count: vendor.value.related_data?.bcp_drp_plans?.length || 0
          })
          
          // Parse JSON fields if they are strings
          if (vendor.value.contacts && typeof vendor.value.contacts === 'string') {
            try {
              vendor.value.contacts = JSON.parse(vendor.value.contacts)
            } catch (e) {
              console.warn('Failed to parse contacts JSON:', e)
              vendor.value.contacts = []
            }
          }
          
          if (vendor.value.documents && typeof vendor.value.documents === 'string') {
            try {
              vendor.value.documents = JSON.parse(vendor.value.documents)
            } catch (e) {
              console.warn('Failed to parse documents JSON:', e)
              vendor.value.documents = []
            }
          }
          
          // Ensure related_data exists even if empty
          if (!vendor.value.related_data) {
            vendor.value.related_data = {
              contracts: [],
              contract_terms: [],
              contract_clauses: [],
              slas: [],
              sla_metrics: [],
              bcp_drp_plans: []
            }
          }
        } else {
          error.value = 'Failed to load vendor details'
        }
      } catch (err) {
        console.error('Error fetching vendor details:', err)
        error.value = err.response?.data?.error || 'Failed to load vendor details'
      } finally {
        loading.value = false
      }
    }

    const goBack = () => {
      emit('back')
    }

    const getBannerClass = (vendorType) => {
      const classMap = {
        'ONBOARDED_WITH_RFP': 'banner-onboarded-rfp',
        'ONBOARDED_WITHOUT_RFP': 'banner-onboarded-no-rfp',
        'TEMPORARY_WITH_RFP': 'banner-temp-rfp',
        'TEMPORARY_WITHOUT_RFP': 'banner-temp-no-rfp'
      }
      return classMap[vendorType] || ''
    }

    const getRiskLevelClass = (riskLevel) => {
      const classMap = {
        'LOW': 'badge-success',
        'MEDIUM': 'badge-warning',
        'HIGH': 'badge-danger',
        'CRITICAL': 'badge-critical'
      }
      return classMap[riskLevel] || ''
    }

    const getStatusClass = (status) => {
      const classMap = {
        'DRAFT': 'badge-secondary',
        'SUBMITTED': 'badge-info',
        'IN_REVIEW': 'badge-warning',
        'APPROVED': 'badge-success',
        'REJECTED': 'badge-danger',
        'SUSPENDED': 'badge-warning',
        'TERMINATED': 'badge-dark'
      }
      return classMap[status] || ''
    }

    const formatDate = (dateString) => {
      if (!dateString) return 'N/A'
      const date = new Date(dateString)
      return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
      })
    }

    const formatDateTime = (dateString) => {
      if (!dateString) return 'N/A'
      const date = new Date(dateString)
      return date.toLocaleString('en-US', { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    }

    const formatCurrency = (amount) => {
      if (!amount) return 'N/A'
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
      }).format(amount)
    }

    const formatJSON = (jsonData) => {
      if (!jsonData) return 'N/A'
      if (typeof jsonData === 'string') {
        try {
          jsonData = JSON.parse(jsonData)
        } catch (e) {
          return jsonData
        }
      }
      return JSON.stringify(jsonData, null, 2)
    }

    // Helper to get contract audit findings for a specific audit
    const getContractAuditFindings = (auditId) => {
      if (!vendor.value?.related_data?.contract_audit_findings) return []
      return vendor.value.related_data.contract_audit_findings.filter(f => f.audit_id === auditId)
    }

    // Helper to get SLA audit findings for a specific audit
    const getSLAAuditFindings = (auditId) => {
      if (!vendor.value?.related_data?.sla_audit_findings) return []
      return vendor.value.related_data.sla_audit_findings.filter(f => f.audit_id === auditId)
    }

    // Helper for audit status badge class
    const getAuditStatusClass = (status) => {
      const classMap = {
        'created': 'badge-secondary',
        'in_progress': 'badge-info',
        'under_review': 'badge-warning',
        'completed': 'badge-success',
        'rejected': 'badge-danger'
      }
      return classMap[status] || 'badge-secondary'
    }

    // Helper for review status badge class
    const getReviewStatusClass = (reviewStatus) => {
      const classMap = {
        'pending': 'badge-warning',
        'approved': 'badge-success',
        'rejected': 'badge-danger'
      }
      return classMap[reviewStatus] || 'badge-secondary'
    }

    const getContractTerms = (contractId) => {
      if (!vendor.value?.related_data?.contract_terms) return []
      return vendor.value.related_data.contract_terms.filter(term => term.contract_id === contractId)
    }

    const getContractClauses = (contractId) => {
      if (!vendor.value?.related_data?.contract_clauses) return []
      return vendor.value.related_data.contract_clauses.filter(clause => clause.contract_id === contractId)
    }

    const getSLAMetrics = (slaId) => {
      if (!vendor.value?.related_data?.sla_metrics) return []
      return vendor.value.related_data.sla_metrics.filter(metric => metric.sla_id === slaId)
    }

    const fetchScreeningResults = async () => {
      if (!props.vendorCode) return
      
      screeningLoading.value = true
      screeningError.value = null
      
      try {
        let url = `/api/v1/management/vendors/${props.vendorCode}/screening-results/`
        const params = new URLSearchParams()
        
        if (screeningFilters.value.startDate) {
          params.append('start_date', screeningFilters.value.startDate)
        }
        if (screeningFilters.value.endDate) {
          params.append('end_date', screeningFilters.value.endDate)
        }
        
        if (params.toString()) {
          url += `?${params.toString()}`
        }
        
        const response = await axios.get(url)
        
        if (response.data.success) {
          screeningData.value = response.data
        } else {
          screeningError.value = response.data.error || 'Failed to load screening results'
        }
      } catch (err) {
        console.error('Error fetching screening results:', err)
        screeningError.value = err.response?.data?.error || 'Failed to load screening results'
      } finally {
        screeningLoading.value = false
      }
    }

    const clearScreeningFilters = () => {
      screeningFilters.value.startDate = ''
      screeningFilters.value.endDate = ''
      fetchScreeningResults()
    }

    const fetchRFPData = async () => {
      rfpLoading.value = true
      rfpError.value = null
      
      try {
        // Get response_id from vendor data or fetch from temp_vendor if not available
        let responseId = vendor.value?.response_id
        
        // If response_id is not in vendor data, try to fetch it from temp_vendor using vendor_code
        if (!responseId && vendor.value?.vendor_code) {
          try {
            console.log('[VendorDetailView] Response ID not found in vendor data, fetching from temp_vendor...')
            // Try to get temp_vendor data to extract response_id
            // The vendor detail endpoint should already include this, but as a fallback:
            const tempVendorResponse = await axios.get(`/api/v1/management/vendors/${vendor.value.vendor_code}/`)
            if (tempVendorResponse.data?.success && tempVendorResponse.data?.data?.response_id) {
              responseId = tempVendorResponse.data.data.response_id
              console.log('[VendorDetailView] Found response_id from vendor detail:', responseId)
            }
          } catch (tempErr) {
            console.warn('[VendorDetailView] Could not fetch response_id from vendor detail:', tempErr)
          }
        }
        
        if (!responseId) {
          rfpError.value = 'No RFP response ID available for this vendor. This vendor may not have submitted an RFP response.'
          rfpLoading.value = false
          return
        }
        
        console.log('[VendorDetailView] Fetching RFP response data for response_id:', responseId)
        
        // First, fetch the RFP response data
        const responseData = await axios.get(`/api/v1/rfp-responses-detail/${responseId}/`)
        
        if (!responseData.data.success) {
          rfpError.value = responseData.data.error || 'Failed to load RFP response data'
          rfpLoading.value = false
          return
        }
        
        const rfpResponse = responseData.data.data
        
        // Map the response data to include all fields from the database
        const mappedResponse = {
          ...rfpResponse,
          submission_date: rfpResponse.submission_date || rfpResponse.submitted_at,
          submitted_at: rfpResponse.submitted_at || rfpResponse.submission_date
        }
        
        // Then, fetch the RFP data using the rfp_id from the response
        let rfpDetails = null
        if (rfpResponse.rfp_id) {
          try {
            const rfpResponseData = await axios.get(`/api/v1/rfps/${rfpResponse.rfp_id}/`)
            if (rfpResponseData.data && (rfpResponseData.data.rfp_id || rfpResponseData.data.id)) {
              rfpDetails = rfpResponseData.data
            }
          } catch (rfpErr) {
            console.warn('Could not fetch RFP details:', rfpErr)
            // Continue without RFP details if it fails - this is not critical
          }
        }
        
        // Combine both datasets
        rfpData.value = {
          response: mappedResponse,
          rfp: rfpDetails
        }
      } catch (err) {
        console.error('[VendorDetailView] Error fetching RFP data:', err)
        const responseId = vendor.value?.response_id || 'unknown'
        if (err.response?.status === 404) {
          rfpError.value = `RFP response not found: ${responseId}. The response may have been deleted, the ID is incorrect, or it belongs to a different tenant. Please verify the response_id in the temp_vendor table.`
        } else if (err.response?.status === 403) {
          rfpError.value = 'Access denied. You may not have permission to view this RFP response, or tenant context is missing.'
        } else if (err.response?.status === 401) {
          rfpError.value = 'Authentication required. Please log in again.'
        } else {
          rfpError.value = err.response?.data?.error || err.response?.data?.message || err.message || 'Failed to load RFP data'
        }
      } finally {
        rfpLoading.value = false
      }
    }

    const getScreeningTypeIcon = (type) => {
      const iconMap = {
        'OFAC': 'fas fa-shield-alt',
        'PEP': 'fas fa-user-tie',
        'SANCTIONS': 'fas fa-ban',
        'ADVERSE_MEDIA': 'fas fa-newspaper',
        'WORLDCHECK': 'fas fa-globe'
      }
      return iconMap[type] || 'fas fa-search'
    }

    const getScreeningStatusClass = (status) => {
      const classMap = {
        'CLEAR': 'badge-success',
        'POTENTIAL_MATCH': 'badge-warning',
        'CONFIRMED_MATCH': 'badge-danger',
        'UNDER_REVIEW': 'badge-info'
      }
      return classMap[status] || 'badge-secondary'
    }

    const getMatchRiskClass = (score) => {
      if (score >= 85) return 'match-high-risk'
      if (score >= 70) return 'match-medium-risk'
      return 'match-low-risk'
    }

    const getScoreClass = (score) => {
      if (score >= 85) return 'score-high'
      if (score >= 70) return 'score-medium'
      return 'score-low'
    }

    const getResolutionStatusClass = (status) => {
      const classMap = {
        'PENDING': 'badge-warning',
        'CLEARED': 'badge-success',
        'ESCALATED': 'badge-info',
        'BLOCKED': 'badge-danger'
      }
      return classMap[status] || 'badge-secondary'
    }

    const formatSearchTerms = (searchTerms) => {
      if (!searchTerms) return 'N/A'
      if (typeof searchTerms === 'string') {
        try {
          searchTerms = JSON.parse(searchTerms)
        } catch (e) {
          return searchTerms
        }
      }
      if (typeof searchTerms === 'object') {
        return Object.entries(searchTerms)
          .filter(([key, value]) => value && key !== 'threshold')
          .map(([key, value]) => `${key}: ${value}`)
          .join(', ') || 'N/A'
      }
      return 'N/A'
    }

    const formatKey = (key) => {
      return key.split('_').map(word => 
        word.charAt(0).toUpperCase() + word.slice(1)
      ).join(' ')
    }

    const formatMatchValue = (value) => {
      if (Array.isArray(value)) {
        return value.join(', ')
      }
      if (typeof value === 'object') {
        return JSON.stringify(value, null, 2)
      }
      return value || 'N/A'
    }

    // Watch for tab changes to fetch screening data when tab is activated
    watch(activeTab, (newTab) => {
      if (newTab === 'screening' && !screeningData.value && !screeningLoading.value) {
        fetchScreeningResults()
      }
      if (newTab === 'rfp' && !rfpData.value && !rfpLoading.value && vendor.value) {
        console.log('[VendorDetailView] RFP tab activated, fetching RFP data...', {
          vendor_code: vendor.value.vendor_code,
          response_id: vendor.value.response_id
        })
        fetchRFPData()
      }
    })

    // When returning from contract/SLA/BCP detail, open the correct tab
    watch(() => props.initialTab, (tab) => {
      if (tab) activeTab.value = tab
    }, { immediate: true })

    onMounted(() => {
      fetchVendorDetails()
    })

    // ── Contract Audit Report Download ──────────────────────────────────────
    const downloadingReportId = ref(null)

    const generateAuditReport = async (audit) => {
      try {
        downloadingReportId.value = audit.audit_id

        const findingsResponse = await contractAuditApi.getContractAuditFindings({ audit_id: audit.audit_id })
        let findings = []
        if (findingsResponse.success) {
          if (Array.isArray(findingsResponse.data)) {
            findings = findingsResponse.data
          } else if (findingsResponse.data && Array.isArray(findingsResponse.data.results)) {
            findings = findingsResponse.data.results
          } else if (findingsResponse.data && Array.isArray(findingsResponse.data.data)) {
            findings = findingsResponse.data.data
          }
        }

        const pdf = new jsPDF('p', 'mm', 'a4')
        const pageWidth = pdf.internal.pageSize.getWidth()
        const pageHeight = pdf.internal.pageSize.getHeight()
        const margin = 20
        const contentWidth = pageWidth - margin * 2
        let yPosition = 20

        const primaryColor = [37, 99, 235]
        const secondaryColor = [107, 114, 128]
        const headerBgColor = [249, 250, 251]
        const borderColor = [229, 231, 235]

        const addFooter = (pageNum, totalPages) => {
          const footerY = pageHeight - 15
          pdf.setDrawColor(...borderColor)
          pdf.setLineWidth(0.5)
          pdf.line(margin, footerY, pageWidth - margin, footerY)
          pdf.setFontSize(8)
          pdf.setTextColor(...secondaryColor)
          pdf.setFont('helvetica', 'normal')
          pdf.text(`Generated on ${new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}`, margin, footerY + 5)
          pdf.text(`Page ${pageNum} of ${totalPages}`, pageWidth - margin, footerY + 5, { align: 'right' })
        }

        const checkNewPage = (requiredSpace = 20) => {
          if (yPosition + requiredSpace > pageHeight - 30) {
            addFooter(pdf.getNumberOfPages(), pdf.getNumberOfPages())
            pdf.addPage()
            yPosition = 20
            return true
          }
          return false
        }

        const addSectionHeader = (title, y) => {
          pdf.setFillColor(...headerBgColor)
          pdf.rect(margin, y - 5, contentWidth, 8, 'F')
          pdf.setFillColor(...primaryColor)
          pdf.rect(margin, y - 5, 3, 8, 'F')
          pdf.setFontSize(14)
          pdf.setTextColor(...primaryColor)
          pdf.setFont('helvetica', 'bold')
          pdf.text(title, margin + 8, y + 1)
          pdf.setTextColor(0, 0, 0)
          return y + 10
        }

        const addInfoRow = (label, value, y, isMultiline = false) => {
          const labelWidth = contentWidth * 0.35
          const valueWidth = contentWidth * 0.65
          const rowHeight = isMultiline ? 12 : 8
          checkNewPage(rowHeight + 5)
          pdf.setFillColor(...headerBgColor)
          pdf.rect(margin, y - 4, labelWidth, rowHeight, 'F')
          pdf.setDrawColor(...borderColor)
          pdf.setLineWidth(0.3)
          pdf.rect(margin, y - 4, labelWidth, rowHeight)
          pdf.rect(margin + labelWidth, y - 4, valueWidth, rowHeight)
          pdf.setFontSize(9)
          pdf.setTextColor(75, 85, 99)
          pdf.setFont('helvetica', 'bold')
          pdf.text(label, margin + 3, y + 2)
          pdf.setFontSize(9)
          pdf.setTextColor(0, 0, 0)
          pdf.setFont('helvetica', 'normal')
          if (isMultiline && value) {
            const valueLines = pdf.splitTextToSize(value || 'N/A', valueWidth - 6)
            const actualHeight = Math.max(rowHeight, valueLines.length * 4 + 4)
            pdf.rect(margin + labelWidth, y - 4, valueWidth, actualHeight)
            pdf.text(valueLines, margin + labelWidth + 3, y + 2)
            return y + actualHeight + 3
          } else {
            pdf.text(value || 'N/A', margin + labelWidth + 3, y + 2)
            return y + rowHeight + 3
          }
        }

        // Cover page
        pdf.setFillColor(...primaryColor)
        pdf.rect(0, 0, pageWidth, 50, 'F')
        pdf.setFontSize(24)
        pdf.setTextColor(255, 255, 255)
        pdf.setFont('helvetica', 'bold')
        pdf.text('AUDIT REPORT', pageWidth / 2, 25, { align: 'center' })
        pdf.setFontSize(12)
        pdf.setFont('helvetica', 'normal')
        pdf.text('Contract Compliance Audit', pageWidth / 2, 35, { align: 'center' })
        yPosition = 70

        pdf.setFontSize(18)
        pdf.setTextColor(0, 0, 0)
        pdf.setFont('helvetica', 'bold')
        pdf.text(audit.title || 'Contract Audit', pageWidth / 2, yPosition, { align: 'center' })
        yPosition += 20

        const boxY = yPosition
        pdf.setFillColor(255, 255, 255)
        pdf.setDrawColor(...borderColor)
        pdf.setLineWidth(0.5)
        pdf.roundedRect(margin, boxY, contentWidth, 60, 3, 3, 'FD')
        yPosition += 10
        yPosition = addInfoRow('Audit ID', `#${audit.audit_id}`, yPosition)
        yPosition = addInfoRow('Contract', audit.contract_title || 'N/A', yPosition)
        yPosition = addInfoRow('Auditor', audit.auditor_name || 'N/A', yPosition)
        yPosition = addInfoRow('Status', audit.status?.toUpperCase() || 'N/A', yPosition)

        const completionDateText = audit.completion_date
          ? new Date(audit.completion_date).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
          : 'N/A'
        yPosition = addInfoRow('Completion Date', completionDateText, yPosition)

        const dueDateText = audit.due_date
          ? new Date(audit.due_date).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
          : 'N/A'
        yPosition = addInfoRow('Due Date', dueDateText, yPosition)
        yPosition += 20

        yPosition = addSectionHeader('Executive Summary', yPosition)
        pdf.setFontSize(10)
        pdf.setTextColor(0, 0, 0)
        pdf.setFont('helvetica', 'normal')
        const summaryText = `This audit report presents a comprehensive review of the contract compliance audit conducted for ${audit.contract_title || 'the specified contract'}. The audit was completed on ${completionDateText} and includes ${findings.length} finding(s) across various contract terms and compliance requirements.`
        const summaryLines = pdf.splitTextToSize(summaryText, contentWidth)
        pdf.text(summaryLines, margin, yPosition)
        yPosition += summaryLines.length * 5 + 10

        pdf.setFillColor(...headerBgColor)
        pdf.setDrawColor(...borderColor)
        pdf.roundedRect(margin, yPosition, contentWidth, 25, 3, 3, 'FD')
        yPosition += 8
        pdf.setFontSize(10)
        pdf.setFont('helvetica', 'bold')
        pdf.text('Summary Statistics', margin + 5, yPosition)
        yPosition += 8
        pdf.setFontSize(9)
        pdf.setFont('helvetica', 'normal')
        pdf.text(`Total Findings: ${findings.length}`, margin + 5, yPosition)
        pdf.text(`Contract: ${audit.contract_title || 'N/A'}`, margin + contentWidth / 2, yPosition)
        yPosition += 15
        addFooter(1, 1)

        // Findings section
        if (findings.length > 0) {
          pdf.addPage()
          yPosition = 20
          yPosition = addSectionHeader('Detailed Audit Findings', yPosition)
          yPosition += 5

          findings.forEach((finding, index) => {
            checkNewPage(80)
            pdf.setFillColor(...primaryColor)
            pdf.roundedRect(margin, yPosition - 5, contentWidth, 8, 2, 2, 'F')
            pdf.setFontSize(12)
            pdf.setTextColor(255, 255, 255)
            pdf.setFont('helvetica', 'bold')
            pdf.text(`Finding ${index + 1}`, margin + 5, yPosition + 1)
            yPosition += 12

            if (finding.term_id) yPosition = addInfoRow('Term ID', String(finding.term_id), yPosition)
            if (finding.term_title) yPosition = addInfoRow('Term Title', finding.term_title, yPosition, true)
            if (finding.term_category) yPosition = addInfoRow('Term Category', finding.term_category, yPosition)
            if (finding.term_text) yPosition = addInfoRow('Term Text', finding.term_text, yPosition, true)
            if (finding.evidence) yPosition = addInfoRow('Evidence', finding.evidence, yPosition, true)
            if (finding.how_to_verify) yPosition = addInfoRow('Verification Method', finding.how_to_verify, yPosition, true)
            if (finding.impact_recommendations) yPosition = addInfoRow('Recommendations', finding.impact_recommendations, yPosition, true)
            if (finding.details_of_finding) yPosition = addInfoRow('Details', finding.details_of_finding, yPosition, true)

            if (finding.questionnaire_responses || finding.questionnaire_responses_with_questions) {
              checkNewPage(30)
              pdf.setFontSize(10)
              pdf.setFont('helvetica', 'bold')
              pdf.setTextColor(...primaryColor)
              pdf.text('Questionnaire Responses', margin, yPosition)
              yPosition += 8
              try {
                let responses = finding.questionnaire_responses_with_questions
                if (!responses && finding.questionnaire_responses) {
                  responses = typeof finding.questionnaire_responses === 'string'
                    ? JSON.parse(finding.questionnaire_responses)
                    : finding.questionnaire_responses
                }
                if (responses && Object.keys(responses).length > 0) {
                  Object.entries(responses).forEach(([questionId, responseData]) => {
                    pdf.setFontSize(9)
                    pdf.setFont('helvetica', 'normal')
                    let questionText = ''
                    let answerText = ''
                    let questionLines = []
                    let questionHeight = 0
                    let answerHeight = 0
                    const indent = 5
                    if (responseData && typeof responseData === 'object' && responseData.question_text) {
                      questionText = `Q${questionId}: ${responseData.question_text}`
                      answerText = responseData.answer || ''
                      questionLines = pdf.splitTextToSize(questionText, contentWidth)
                      questionHeight = questionLines.length * 3.5
                      if (answerText) {
                        const answerLines = pdf.splitTextToSize(`Answer: ${answerText}`, contentWidth - indent)
                        answerHeight = answerLines.length * 3.5
                      }
                    } else {
                      questionText = `Q${questionId}: ${responseData}`
                      questionLines = pdf.splitTextToSize(questionText, contentWidth)
                      questionHeight = questionLines.length * 3.5
                    }
                    const totalHeight = questionHeight + answerHeight + (answerText ? 2 : 0)
                    checkNewPage(totalHeight + 2)
                    pdf.setTextColor(0, 0, 0)
                    pdf.setFont('helvetica', 'normal')
                    pdf.text(questionLines, margin, yPosition)
                    if (answerText) {
                      const answerY = yPosition + questionHeight + 2
                      pdf.setFont('helvetica', 'bold')
                      pdf.setTextColor(...primaryColor)
                      const answerLines = pdf.splitTextToSize(`Answer: ${answerText}`, contentWidth - indent)
                      pdf.text(answerLines, margin + indent, answerY)
                      answerHeight = answerLines.length * 3.5
                    }
                    yPosition += totalHeight + 5
                  })
                }
              } catch (e) {
                pdf.setFontSize(9)
                pdf.setFont('helvetica', 'normal')
                pdf.setTextColor(239, 68, 68)
                pdf.text('Error parsing questionnaire responses', margin, yPosition)
                yPosition += 6
              }
            }

            if (finding.comment) yPosition = addInfoRow('Comments', finding.comment, yPosition, true)
            yPosition += 10

            if (index < findings.length - 1) {
              pdf.setDrawColor(...borderColor)
              pdf.setLineWidth(0.5)
              pdf.line(margin, yPosition, pageWidth - margin, yPosition)
              yPosition += 5
            }
          })
        } else {
          pdf.addPage()
          yPosition = 20
          yPosition = addSectionHeader('Detailed Audit Findings', yPosition)
          yPosition += 10
          pdf.setFontSize(11)
          pdf.setTextColor(...secondaryColor)
          pdf.setFont('helvetica', 'italic')
          pdf.text('No audit findings available for this audit.', margin, yPosition)
        }

        const totalPages = pdf.getNumberOfPages()
        addFooter(totalPages, totalPages)

        const fileName = `Audit_Report_${audit.audit_id}_${audit.title.replace(/[^a-zA-Z0-9]/g, '_')}.pdf`

        // Persist in S3
        try {
          const uploadPayload = {
            audit_id: audit.audit_id,
            contract_id: audit.contract_id || null,
            term_id: audit.term_id || null,
            file_name: fileName,
            file_data: pdf.output('datauristring')
          }
          const uploadResponse = await contractAuditApi.uploadAuditReport(uploadPayload)
          if (!uploadResponse.success) {
            PopupService.warning('Report downloaded locally but could not be stored. Please retry later.', 'Report Storage Warning')
          }
        } catch (uploadError) {
          console.error('Error uploading audit report:', uploadError)
          PopupService.warning('Could not persist the audit report. Local download will continue.', 'Report Storage Error')
        }

        pdf.save(fileName)
        PopupService.success(`Audit report for "${audit.title}" downloaded successfully!`, 'Report Downloaded')
      } catch (error) {
        console.error('Error generating audit report:', error)
        PopupService.error('Error generating audit report. Please try again.', 'Generation Error')
      } finally {
        downloadingReportId.value = null
      }
    }

    // ── SLA Audit Report Download ────────────────────────────────────────────
    const downloadingSLAReportId = ref(null)

    const generateSLAAuditReport = async (audit) => {
      try {
        downloadingSLAReportId.value = audit.audit_id

        // Fetch findings, SLA details, metrics, and performance data in parallel
        const findingsData = await apiService.getAuditFindings(audit.audit_id)
        const findings = findingsData.results || findingsData || []

        let slaDetails = null
        let slaMetrics = []
        let performanceData = null

        if (audit.sla_id) {
          try {
            slaDetails = await apiService.getSLA(audit.sla_id)
            const metricsResponse = await apiService.getSLAMetrics(audit.sla_id)
            slaMetrics = metricsResponse.results || metricsResponse || []
            performanceData = await apiService.getPerformanceDashboard({ sla_id: audit.sla_id, period: 'monthly' })
          } catch (e) {
            console.error('Error loading SLA data for report:', e)
          }
        }

        const pdf = new jsPDF()
        let yPosition = 20

        // ── Cover / Header ────────────────────────────────────────────────────
        pdf.setFillColor(37, 99, 235)
        pdf.rect(0, 0, 210, 50, 'F')
        pdf.setFillColor(59, 130, 246)
        pdf.rect(0, 0, 210, 45, 'F')
        pdf.setTextColor(255, 255, 255)
        pdf.setFontSize(28)
        pdf.setFont('helvetica', 'bold')
        pdf.text('AUDIT REPORT', 105, 25, { align: 'center' })
        pdf.setFontSize(11)
        pdf.setFont('helvetica', 'normal')
        pdf.text(audit.title || 'SLA Audit Report', 105, 35, { align: 'center' })
        pdf.setFillColor(243, 244, 246)
        pdf.rect(0, 50, 210, 15, 'F')
        pdf.setTextColor(75, 85, 99)
        pdf.setFontSize(9)
        pdf.text(`Report Generated: ${new Date().toLocaleDateString()} ${new Date().toLocaleTimeString()}`, 105, 59, { align: 'center' })
        pdf.setTextColor(0, 0, 0)
        yPosition = 75

        // ── Section 1: Audit Information ──────────────────────────────────────
        pdf.setFillColor(239, 246, 255)
        pdf.rect(15, yPosition - 5, 180, 10, 'F')
        pdf.setFontSize(14)
        pdf.setFont('helvetica', 'bold')
        pdf.setTextColor(29, 78, 216)
        pdf.text('1. AUDIT INFORMATION', 20, yPosition + 2)
        pdf.setTextColor(0, 0, 0)
        yPosition += 12

        pdf.setDrawColor(219, 234, 254)
        pdf.setLineWidth(0.5)
        const auditInfoHeight = 85
        pdf.rect(15, yPosition, 180, auditInfoHeight)
        yPosition += 8

        pdf.setFontSize(9)
        pdf.setFont('helvetica', 'normal')
        const col1X = 20
        const col2X = 110
        let tempY = yPosition

        pdf.setFont('helvetica', 'bold')
        pdf.text('Audit ID:', col1X, tempY)
        pdf.setFont('helvetica', 'normal')
        pdf.text(String(audit.audit_id), col1X + 30, tempY)
        tempY += 6

        pdf.setFont('helvetica', 'bold')
        pdf.text('Audit Title:', col1X, tempY)
        pdf.setFont('helvetica', 'normal')
        const titleText = pdf.splitTextToSize(audit.title || 'N/A', 60)
        pdf.text(titleText, col1X, tempY + 4)
        tempY += 4 + (titleText.length * 4)

        pdf.setFont('helvetica', 'bold')
        pdf.text('Audit Type:', col1X, tempY)
        pdf.setFont('helvetica', 'normal')
        pdf.text(audit.audit_type || 'N/A', col1X + 30, tempY)
        tempY += 6

        pdf.setFont('helvetica', 'bold')
        pdf.text('Frequency:', col1X, tempY)
        pdf.setFont('helvetica', 'normal')
        pdf.text(audit.frequency || 'N/A', col1X + 30, tempY)
        tempY += 6

        pdf.setFont('helvetica', 'bold')
        pdf.text('Status:', col1X, tempY)
        const statusColors = {
          completed: { bg: [220, 252, 231], text: [22, 101, 52] },
          in_progress: { bg: [254, 249, 195], text: [133, 77, 14] },
          under_review: { bg: [219, 234, 254], text: [30, 64, 175] },
          created: { bg: [243, 244, 246], text: [55, 65, 81] },
          rejected: { bg: [254, 226, 226], text: [153, 27, 27] }
        }
        const statusColor = statusColors[audit.status] || statusColors['created']
        pdf.setFillColor(...statusColor.bg)
        pdf.roundedRect(col1X + 20, tempY - 3, 35, 6, 1, 1, 'F')
        pdf.setTextColor(...statusColor.text)
        pdf.setFontSize(8)
        pdf.text((audit.status || 'N/A').toUpperCase(), col1X + 22, tempY + 1)
        pdf.setTextColor(0, 0, 0)
        pdf.setFontSize(9)

        tempY = yPosition
        pdf.setFont('helvetica', 'bold')
        pdf.text('Auditor:', col2X, tempY)
        pdf.setFont('helvetica', 'normal')
        pdf.text(audit.auditor_name || 'N/A', col2X + 25, tempY)
        tempY += 6

        pdf.setFont('helvetica', 'bold')
        pdf.text('Reviewer:', col2X, tempY)
        pdf.setFont('helvetica', 'normal')
        pdf.text(audit.reviewer_name || 'N/A', col2X + 25, tempY)
        tempY += 6

        if (audit.due_date) {
          pdf.setFont('helvetica', 'bold')
          pdf.text('Due Date:', col2X, tempY)
          pdf.setFont('helvetica', 'normal')
          pdf.text(new Date(audit.due_date).toLocaleDateString(), col2X + 25, tempY)
        }

        yPosition += auditInfoHeight + 10

        // ── Section 2: SLA Details ─────────────────────────────────────────────
        if (slaDetails) {
          if (yPosition > 220) { pdf.addPage(); yPosition = 20 }

          pdf.setFillColor(239, 246, 255)
          pdf.rect(15, yPosition - 5, 180, 10, 'F')
          pdf.setFontSize(14)
          pdf.setFont('helvetica', 'bold')
          pdf.setTextColor(29, 78, 216)
          pdf.text('2. SLA DETAILS', 20, yPosition + 2)
          pdf.setTextColor(0, 0, 0)
          yPosition += 15

          const tableX = 15
          const labelW = 50
          const valueW = 130
          let rowY = yPosition

          const addSLARow = (label, value, isDate = false) => {
            if (!value || value === 'N/A') return
            if (rowY > 260) { pdf.addPage(); rowY = 20 }
            const displayValue = isDate ? new Date(value).toLocaleDateString() : String(value)
            pdf.setFillColor(249, 250, 251)
            pdf.rect(tableX, rowY, labelW, 8, 'F')
            pdf.setFontSize(8)
            pdf.setFont('helvetica', 'bold')
            pdf.setTextColor(75, 85, 99)
            pdf.text(label, tableX + 2, rowY + 5)
            pdf.setFont('helvetica', 'normal')
            pdf.setTextColor(0, 0, 0)
            const valueLines = pdf.splitTextToSize(displayValue, valueW - 4)
            const cellHeight = Math.max(8, valueLines.length * 4.5 + 3)
            pdf.setDrawColor(229, 231, 235)
            pdf.rect(tableX, rowY, labelW, cellHeight)
            pdf.rect(tableX + labelW, rowY, valueW, cellHeight)
            pdf.text(valueLines, tableX + labelW + 2, rowY + 5)
            rowY += cellHeight
          }

          addSLARow('SLA ID', slaDetails.sla_id)
          addSLARow('SLA Name', slaDetails.sla_name)
          addSLARow('SLA Type', slaDetails.sla_type)
          addSLARow('Status', slaDetails.status)
          addSLARow('Priority', slaDetails.priority)
          addSLARow('Effective Date', slaDetails.effective_date, true)
          addSLARow('Expiry Date', slaDetails.expiry_date, true)
          if (slaDetails.compliance_score) addSLARow('Compliance Score', `${slaDetails.compliance_score}%`)
          addSLARow('Business Service', slaDetails.business_service_impacted)
          addSLARow('Reporting Frequency', slaDetails.reporting_frequency)
          addSLARow('Baseline Period', slaDetails.baseline_period)
          if (slaDetails.penalty_threshold) addSLARow('Penalty Threshold', `${slaDetails.penalty_threshold}%`)
          if (slaDetails.credit_threshold) addSLARow('Credit Threshold', `${slaDetails.credit_threshold}%`)
          addSLARow('Compliance Framework', slaDetails.compliance_framework)
          addSLARow('Measurement Methodology', slaDetails.measurement_methodology)
          addSLARow('Audit Requirements', slaDetails.audit_requirements)

          yPosition = rowY + 10
        }

        // ── Section 3: SLA Metrics ─────────────────────────────────────────────
        if (slaMetrics.length > 0) {
          if (yPosition > 200) { pdf.addPage(); yPosition = 20 }

          pdf.setFillColor(239, 246, 255)
          pdf.rect(15, yPosition - 5, 180, 10, 'F')
          pdf.setFontSize(14)
          pdf.setFont('helvetica', 'bold')
          pdf.setTextColor(29, 78, 216)
          pdf.text('3. SLA METRICS & TARGETS', 20, yPosition + 2)
          pdf.setTextColor(0, 0, 0)
          yPosition += 15

          slaMetrics.forEach((metric, index) => {
            if (yPosition > 230) { pdf.addPage(); yPosition = 20 }
            pdf.setFillColor(249, 250, 251)
            pdf.rect(15, yPosition, 180, 10, 'F')
            pdf.setFontSize(10)
            pdf.setFont('helvetica', 'bold')
            pdf.text(`Metric ${index + 1}: ${metric.metric_name}`, 20, yPosition + 6)
            yPosition += 10

            const tX = 15
            const lW = 45
            const vW = 135
            let rY = yPosition

            const addMetricRow = (label, value) => {
              if (!value || value === 'N/A') return
              if (rY > 260) { pdf.addPage(); rY = 20 }
              pdf.setFillColor(249, 250, 251)
              pdf.rect(tX, rY, lW, 8, 'F')
              pdf.setFontSize(8)
              pdf.setFont('helvetica', 'bold')
              pdf.setTextColor(75, 85, 99)
              pdf.text(label, tX + 2, rY + 5)
              pdf.setFont('helvetica', 'normal')
              pdf.setTextColor(0, 0, 0)
              const vLines = pdf.splitTextToSize(String(value), vW - 4)
              const cellH = Math.max(8, vLines.length * 4.5 + 3)
              pdf.setDrawColor(229, 231, 235)
              pdf.rect(tX, rY, lW, cellH)
              pdf.rect(tX + lW, rY, vW, cellH)
              pdf.text(vLines, tX + lW + 2, rY + 5)
              rY += cellH
            }

            if (metric.threshold) {
              addMetricRow('Target Threshold', metric.measurement_unit ? `${metric.threshold} ${metric.measurement_unit}` : metric.threshold)
            }
            addMetricRow('Frequency', metric.frequency)
            addMetricRow('Methodology', metric.measurement_methodology)
            addMetricRow('Penalty', metric.penalty)

            yPosition = rY + 6
          })

          yPosition += 10
        }

        // ── Section 4: Performance Summary ────────────────────────────────────
        if (performanceData) {
          if (yPosition > 200) { pdf.addPage(); yPosition = 20 }

          pdf.setFillColor(239, 246, 255)
          pdf.rect(15, yPosition - 5, 180, 10, 'F')
          pdf.setFontSize(14)
          pdf.setFont('helvetica', 'bold')
          pdf.setTextColor(29, 78, 216)
          pdf.text('4. PERFORMANCE SUMMARY', 20, yPosition + 2)
          pdf.setTextColor(0, 0, 0)
          yPosition += 15

          if (performanceData.overview) {
            const ov = performanceData.overview
            const cardW = 57
            const cardH = 22
            const cardS = 5
            const startX = 20
            const kpiCards = [
              { label: 'Overall Compliance', value: `${ov.overall_compliance || 0}%`, color: ov.overall_compliance >= 95 ? [34, 197, 94] : ov.overall_compliance >= 90 ? [245, 158, 11] : [239, 68, 68] },
              { label: 'Compliance Trend', value: `${(ov.compliance_trend || 0) >= 0 ? '+' : ''}${ov.compliance_trend || 0}%`, color: (ov.compliance_trend || 0) >= 0 ? [34, 197, 94] : [239, 68, 68] },
              { label: 'Total Metrics', value: String(ov.total_metrics || 0), color: [59, 130, 246] },
              { label: 'Metrics in Breach', value: String(ov.metrics_in_breach || 0), color: (ov.metrics_in_breach || 0) > 0 ? [239, 68, 68] : [34, 197, 94] },
              { label: 'Performance Gap', value: `${ov.avg_performance_gap || 0}%`, color: [245, 158, 11] },
              { label: 'Vendors at Risk', value: String(ov.vendors_at_risk || 0), color: (ov.vendors_at_risk || 0) > 0 ? [245, 158, 11] : [34, 197, 94] }
            ]
            kpiCards.forEach((card, i) => {
              const col = i % 3
              const row = Math.floor(i / 3)
              const x = startX + col * (cardW + cardS)
              const y = yPosition + row * (cardH + cardS)
              pdf.setDrawColor(229, 231, 235)
              pdf.setLineWidth(0.3)
              pdf.rect(x, y, cardW, cardH)
              pdf.setFillColor(...card.color)
              pdf.rect(x, y, 2, cardH, 'F')
              pdf.setFontSize(7)
              pdf.setFont('helvetica', 'normal')
              pdf.setTextColor(107, 114, 128)
              pdf.text(card.label, x + 5, y + 7)
              pdf.setFontSize(14)
              pdf.setFont('helvetica', 'bold')
              pdf.setTextColor(17, 24, 39)
              pdf.text(card.value, x + 5, y + 16)
            })
            yPosition += (cardH * 2) + cardS + 15
            if (ov.last_audit_date) {
              pdf.setFontSize(8)
              pdf.setTextColor(107, 114, 128)
              pdf.text(`Last Audit: ${ov.last_audit_date}`, 20, yPosition)
              yPosition += 10
            }
            pdf.setTextColor(0, 0, 0)
          }
        }

        // ── Section 5: Audit Findings ──────────────────────────────────────────
        if (findings.length > 0) {
          if (yPosition > 220) { pdf.addPage(); yPosition = 20 }

          pdf.setFillColor(239, 246, 255)
          pdf.rect(15, yPosition - 5, 180, 10, 'F')
          pdf.setFontSize(14)
          pdf.setFont('helvetica', 'bold')
          pdf.setTextColor(29, 78, 216)
          pdf.text('5. AUDIT FINDINGS & OBSERVATIONS', 20, yPosition + 2)
          pdf.setTextColor(0, 0, 0)
          yPosition += 15

          findings.forEach((finding, index) => {
            if (yPosition > 230) { pdf.addPage(); yPosition = 20 }

            pdf.setFillColor(249, 250, 251)
            pdf.rect(15, yPosition, 180, 12, 'F')
            pdf.setFontSize(11)
            pdf.setFont('helvetica', 'bold')
            pdf.text(`Finding #${index + 1}`, 20, yPosition + 8)
            if (finding.check_date) {
              pdf.setFontSize(8)
              pdf.setFont('helvetica', 'normal')
              pdf.setTextColor(107, 114, 128)
              pdf.text(`Checked: ${new Date(finding.check_date).toLocaleDateString()}`, 150, yPosition + 8)
              pdf.setTextColor(0, 0, 0)
            }
            yPosition += 12

            const ftX = 15
            const flW = 45
            const fvW = 135
            let frY = yPosition

            const addFindingRow = (label, value) => {
              if (!value || value === 'N/A' || (typeof value === 'string' && value.trim() === '')) return
              if (frY > 260) { pdf.addPage(); frY = 20 }
              pdf.setFillColor(249, 250, 251)
              pdf.rect(ftX, frY, flW, 8, 'F')
              pdf.setFontSize(8)
              pdf.setFont('helvetica', 'bold')
              pdf.setTextColor(75, 85, 99)
              pdf.text(label, ftX + 2, frY + 5)
              pdf.setFont('helvetica', 'normal')
              pdf.setTextColor(0, 0, 0)
              const fLines = pdf.splitTextToSize(String(value), fvW - 4)
              const fCellH = Math.max(8, fLines.length * 4.5 + 3)
              pdf.setDrawColor(229, 231, 235)
              pdf.rect(ftX, frY, flW, fCellH)
              pdf.rect(ftX + flW, frY, fvW, fCellH)
              pdf.text(fLines, ftX + flW + 2, frY + 5)
              frY += fCellH
            }

            addFindingRow('Finding Details', finding.details_of_finding)
            addFindingRow('Evidence', finding.evidence)
            addFindingRow('Verification Method', finding.how_to_verify)
            addFindingRow('Impact & Recommendations', finding.impact_recommendations)
            addFindingRow('Comments', finding.comment)

            yPosition = frY + 8
          })
        }

        // ── Section 6: Executive Summary ──────────────────────────────────────
        if (yPosition > 220) { pdf.addPage(); yPosition = 20 }

        pdf.setFontSize(14)
        pdf.setFont('helvetica', 'bold')
        pdf.setTextColor(29, 78, 216)
        pdf.text('6. EXECUTIVE SUMMARY', 20, yPosition)
        pdf.setTextColor(0, 0, 0)
        yPosition += 10

        pdf.setFontSize(10)
        pdf.setFont('helvetica', 'normal')

        let summaryContent = `This audit report for "${audit.title}" was completed on ${audit.completion_date ? new Date(audit.completion_date).toLocaleDateString() : 'N/A'}. `
        if (performanceData?.overview) {
          summaryContent += `The overall SLA compliance rate is ${performanceData.overview.overall_compliance || 0}% with ${performanceData.overview.metrics_in_breach || 0} metrics currently in breach. `
          if ((performanceData.overview.overall_compliance || 0) >= 95) {
            summaryContent += 'The SLA is meeting performance targets and is in good standing. '
          } else if ((performanceData.overview.overall_compliance || 0) >= 90) {
            summaryContent += 'The SLA requires attention as it is approaching breach thresholds. '
          } else {
            summaryContent += 'The SLA is in breach and requires immediate corrective action. '
          }
        }
        if (findings.length > 0) summaryContent += `A total of ${findings.length} finding${findings.length > 1 ? 's were' : ' was'} documented during this audit. `
        summaryContent += 'This report provides a comprehensive analysis of SLA performance and detailed audit findings for management review.'

        const sumLines = pdf.splitTextToSize(summaryContent, 170)
        pdf.text(sumLines, 25, yPosition)
        yPosition += (sumLines.length * 5) + 10

        pdf.setFont('helvetica', 'bold')
        pdf.text('Recommended Actions:', 25, yPosition)
        yPosition += 6

        pdf.setFont('helvetica', 'normal')
        const recommendations = []
        if (performanceData?.overview?.metrics_in_breach > 0) recommendations.push('Address metrics in breach with immediate corrective action plans')
        if (performanceData?.overview?.vendors_at_risk > 0) recommendations.push('Review vendor performance for those identified as at-risk')
        if (findings.length > 0) {
          recommendations.push('Review and implement recommendations from audit findings')
          recommendations.push('Schedule follow-up audit to verify corrective actions')
        }
        if (recommendations.length === 0) {
          recommendations.push('Continue monitoring SLA performance')
          recommendations.push('Maintain current performance standards')
        }
        recommendations.forEach((rec, i) => {
          const recLines = pdf.splitTextToSize(`${i + 1}. ${rec}`, 165)
          pdf.text(recLines, 30, yPosition)
          yPosition += (recLines.length * 5) + 3
        })

        // ── Footer on all pages ────────────────────────────────────────────────
        pdf.setTextColor(0, 0, 0)
        const pageCount = pdf.internal.getNumberOfPages()
        for (let i = 1; i <= pageCount; i++) {
          pdf.setPage(i)
          pdf.setFontSize(8)
          pdf.setFont('helvetica', 'normal')
          pdf.setDrawColor(200, 200, 200)
          pdf.line(20, 282, 190, 282)
          pdf.text(`Generated on: ${new Date().toLocaleDateString()} ${new Date().toLocaleTimeString()}`, 20, 287)
          pdf.text(`Audit ID: ${audit.audit_id}`, 105, 287, { align: 'center' })
          pdf.text(`Page ${i} of ${pageCount}`, 190, 287, { align: 'right' })
        }

        const fileName = `SLA_Audit_Report_${audit.audit_id}_${(audit.title || 'report').replace(/[^a-zA-Z0-9]/g, '_')}.pdf`
        pdf.save(fileName)
        PopupService.success(`SLA audit report for "${audit.title}" downloaded successfully!`, 'Report Downloaded')
      } catch (error) {
        console.error('Error generating SLA audit report:', error)
        PopupService.error('Error generating SLA audit report. Please try again.', 'Generation Error')
      } finally {
        downloadingSLAReportId.value = null
      }
    }

    const viewContract = (contractId) => {
      router.push(`/contracts/${contractId}?returnTo=vendor-detail&vendorCode=${encodeURIComponent(props.vendorCode)}&tab=contracts`)
    }

    const viewSla = (slaId) => {
      router.push(`/slas/${slaId}?returnTo=vendor-detail&vendorCode=${encodeURIComponent(props.vendorCode)}&tab=slas`)
    }

    const viewBcpPlan = (planId) => {
      router.push(`/bcp/library?planId=${planId}&returnTo=vendor-detail&vendorCode=${encodeURIComponent(props.vendorCode)}&tab=bcp_plans`)
    }

    return {
      vendor,
      loading,
      error,
      activeTab,
      tabs,
      screeningData,
      screeningLoading,
      screeningError,
      screeningFilters,
      rfpData,
      rfpLoading,
      rfpError,
      fetchVendorDetails,
      fetchScreeningResults,
      clearScreeningFilters,
      fetchRFPData,
      goBack,
      getBannerClass,
      getRiskLevelClass,
      getStatusClass,
      formatDate,
      formatDateTime,
      formatCurrency,
      formatJSON,
      getContractTerms,
      getContractClauses,
      getSLAMetrics,
      viewContract,
      viewSla,
      viewBcpPlan,
      getContractAuditFindings,
      getSLAAuditFindings,
      getAuditStatusClass,
      getReviewStatusClass,
      getScreeningTypeIcon,
      getScreeningStatusClass,
      getMatchRiskClass,
      getScoreClass,
      getResolutionStatusClass,
      formatSearchTerms,
      formatKey,
      formatMatchValue,
      downloadingReportId,
      generateAuditReport,
      downloadingSLAReportId,
      generateSLAAuditReport
    }
  }
}
</script>

<style scoped>
.vendor-detail-container {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
  min-height: 100vh;
  background: #f7fafc;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 2rem;
  background: #fff;
  padding: 1.5rem;
  border-radius: 0.75rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: #f3f4f6;
  border: none;
  border-radius: 0.375rem;
  color: #374151;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.back-btn:hover {
  background: #e5e7eb;
  color: #1f2937;
}

.detail-title {
  font-size: 2rem;
  font-weight: 700;
  color: #1a202c;
  margin: 0;
}

.loading-container,
.error-container {
  text-align: center;
  padding: 4rem 2rem;
  background: #fff;
  border-radius: 0.75rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.spinner {
  width: 3rem;
  height: 3rem;
  border: 4px solid #e2e8f0;
  border-top-color: #2563eb;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-container i {
  font-size: 3rem;
  color: #dc2626;
  margin-bottom: 1rem;
}

.detail-content {
  background: #fff;
  border-radius: 0.75rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.vendor-type-banner {
  padding: 1rem 1.5rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-weight: 600;
  margin: 0;
}

.banner-onboarded-rfp {
  background: #d1fae5;
  color: #065f46;
}

.banner-onboarded-no-rfp {
  background: #dbeafe;
  color: #1e40af;
}

.banner-temp-rfp {
  background: #fef3c7;
  color: #92400e;
}

.banner-temp-no-rfp {
  background: #ede9fe;
  color: #5b21b6;
}

.tabs-container {
  padding: 0;
  background: #fff;
  border-bottom: 1px solid #e2e8f0;
}

.tabs-wrapper {
  padding: 0 1.5rem;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  display: flex !important;
  flex-direction: row !important;
  flex-wrap: nowrap !important;
  gap: 0;
  scrollbar-width: thin;
}

.tab {
  padding: 1rem 1.5rem;
  border: none;
  background: transparent;
  color: #718096;
  cursor: pointer;
  border-bottom: 3px solid transparent;
  margin-bottom: -1px;
  transition: all 0.2s;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  white-space: nowrap;
  position: relative;
  font-size: 0.875rem;
  flex-shrink: 0;
  flex-grow: 0;
}

.tab:hover {
  color: #2563eb;
  background: #f7fafc;
}

.tab.active {
  color: #2563eb;
  border-bottom-color: #2563eb;
  background: #f7fafc;
  font-weight: 600;
}

.tab.active::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  right: 0;
  height: 1px;
  background: #fff;
}

.tab-label {
  display: inline-block;
}

.tab i {
  font-size: 0.875rem;
}

.tab-content-wrapper {
  padding: 1.5rem;
}

.tab-content {
  /* Tab content styles */
}

.section-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1a202c;
  margin: 0 0 1.5rem 0;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid #e2e8f0;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.info-item.full-width {
  grid-column: 1 / -1;
}

.info-item label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #718096;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.info-item p {
  font-size: 1rem;
  color: #1a202c;
  margin: 0;
  word-break: break-word;
}

.link {
  color: #2563eb;
  text-decoration: none;
}

.link:hover {
  text-decoration: underline;
}

.badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.badge-success {
  background: #d1fae5;
  color: #065f46;
}

.badge-warning {
  background: #fef3c7;
  color: #92400e;
}

.badge-danger {
  background: #fee2e2;
  color: #991b1b;
}

.badge-critical {
  background: #fecaca;
  color: #7f1d1d;
}

.badge-info {
  background: #dbeafe;
  color: #1e40af;
}

.badge-secondary {
  background: #f3f4f6;
  color: #374151;
}

.badge-dark {
  background: #e5e7eb;
  color: #1f2937;
}

.text-danger {
  color: #dc2626;
  font-weight: 600;
}

.text-info {
  color: #2563eb;
  font-weight: 600;
}

.text-muted {
  color: #9ca3af;
}

.response-id {
  font-family: monospace;
  color: #2563eb;
  font-weight: 600;
}

/* Contacts */
.contacts-list {
  display: grid;
  gap: 1rem;
}

.contact-card {
  padding: 1rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  background: #f7fafc;
}

.contact-name {
  font-size: 1rem;
  font-weight: 600;
  color: #1a202c;
  margin: 0 0 0.75rem 0;
}

.contact-details {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.contact-detail {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: #4a5568;
}

.contact-detail i {
  width: 1.25rem;
  color: #718096;
}

.contact-detail a {
  color: #2563eb;
  text-decoration: none;
}

.contact-detail a:hover {
  text-decoration: underline;
}

/* Documents */
.documents-list {
  display: grid;
  gap: 1rem;
}

.document-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  background: #f7fafc;
}

.document-icon {
  font-size: 2rem;
  color: #2563eb;
}

.document-info {
  flex: 1;
}

.document-name {
  font-size: 1rem;
  font-weight: 600;
  color: #1a202c;
  margin: 0 0 0.25rem 0;
}

.document-type {
  font-size: 0.875rem;
  color: #718096;
  margin: 0;
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 3rem 1.5rem;
  color: #9ca3af;
}

.empty-state i {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 0.375rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: #2563eb;
  color: #fff;
}

.btn-primary:hover {
  background: #1d4ed8;
}

/* Contracts */
.contracts-list {
  display: grid;
  gap: 1.5rem;
}

.contract-card {
  padding: 1.5rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  background: #f7fafc;
}

.contract-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #e2e8f0;
}

.contract-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1a202c;
  margin: 0;
}

.contract-number {
  font-size: 0.875rem;
  color: #718096;
  font-family: monospace;
}

.contract-details-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1rem;
}

.contract-detail-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.contract-detail-item label {
  font-size: 0.75rem;
  font-weight: 600;
  color: #718096;
  text-transform: uppercase;
}

.contract-detail-item p {
  font-size: 0.875rem;
  color: #1a202c;
  margin: 0;
}

.contract-subsection {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e2e8f0;
}

.contract-subsection h5 {
  font-size: 0.875rem;
  font-weight: 600;
  color: #4a5568;
  margin: 0 0 0.75rem 0;
}

.terms-list,
.clauses-list {
  display: grid;
  gap: 0.75rem;
}

.term-item,
.clause-item {
  padding: 0.75rem;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 0.375rem;
}

.term-item strong,
.clause-item strong {
  display: block;
  font-size: 0.875rem;
  font-weight: 600;
  color: #1a202c;
  margin-bottom: 0.5rem;
}

.term-item p,
.clause-item p {
  font-size: 0.875rem;
  color: #4a5568;
  margin: 0.5rem 0 0 0;
  line-height: 1.5;
}

.badge-small {
  font-size: 0.625rem;
  padding: 0.125rem 0.5rem;
}

/* SLAs */
.slas-list {
  display: grid;
  gap: 1.5rem;
}

.sla-card {
  padding: 1.5rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  background: #f7fafc;
}

.sla-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #e2e8f0;
}

.sla-name {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1a202c;
  margin: 0;
}

.sla-details-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1rem;
}

.sla-detail-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.sla-detail-item label {
  font-size: 0.75rem;
  font-weight: 600;
  color: #718096;
  text-transform: uppercase;
}

.sla-detail-item p {
  font-size: 0.875rem;
  color: #1a202c;
  margin: 0;
}

.sla-subsection {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e2e8f0;
}

.sla-subsection h5 {
  font-size: 0.875rem;
  font-weight: 600;
  color: #4a5568;
  margin: 0 0 0.75rem 0;
}

.metrics-list {
  display: grid;
  gap: 0.75rem;
}

.metric-item {
  padding: 0.75rem;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 0.375rem;
}

.metric-item strong {
  display: block;
  font-size: 0.875rem;
  font-weight: 600;
  color: #1a202c;
  margin-bottom: 0.5rem;
}

.metric-item p {
  font-size: 0.875rem;
  color: #4a5568;
  margin: 0.25rem 0;
}

/* BCP/DRP Plans */
.plans-list {
  display: grid;
  gap: 1.5rem;
}

.plan-card {
  padding: 1.5rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  background: #f7fafc;
}

.plan-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #e2e8f0;
}

.plan-name {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1a202c;
  margin: 0;
}

.plan-details-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1rem;
}

.plan-detail-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.plan-detail-item label {
  font-size: 0.75rem;
  font-weight: 600;
  color: #718096;
  text-transform: uppercase;
}

.plan-detail-item p {
  font-size: 0.875rem;
  color: #1a202c;
  margin: 0;
}

.plan-scope {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e2e8f0;
}

.plan-scope label {
  font-size: 0.75rem;
  font-weight: 600;
  color: #718096;
  text-transform: uppercase;
  display: block;
  margin-bottom: 0.5rem;
}

.plan-scope p {
  font-size: 0.875rem;
  color: #4a5568;
  line-height: 1.5;
  margin: 0;
}

/* Responsive */
@media (max-width: 768px) {
  .vendor-detail-container {
    padding: 1rem;
  }

  .detail-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .info-grid {
    grid-template-columns: 1fr;
  }

  .tabs-wrapper {
    padding: 0 1rem;
  }

  .tab {
    padding: 0.75rem 1rem;
    font-size: 0.8125rem;
  }

  .tab-label {
    display: none;
  }

  .tab i {
    font-size: 1rem;
  }

  .tab-content-wrapper {
    padding: 1rem;
  }

  .contract-details-grid,
  .sla-details-grid,
  .plan-details-grid,
  .audit-info-grid {
    grid-template-columns: 1fr;
  }

  .audit-header {
    flex-direction: column;
    align-items: flex-start;
  }
}

/* Audit Subsections */
.audit-subsection {
  margin-top: 2rem;
  padding-top: 2rem;
  border-top: 2px solid #e2e8f0;
}

.audit-subsection:first-child {
  margin-top: 0;
  padding-top: 0;
  border-top: none;
}

.subsection-title {
  font-size: 1rem;
  font-weight: 600;
  color: #1a202c;
  margin: 0 0 1rem 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.subsection-title i {
  color: #2563eb;
}

.audits-list {
  display: grid;
  gap: 1.5rem;
}

.audit-card {
  background: #f7fafc;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  overflow: hidden;
}

.audit-header {
  padding: 1rem 1.5rem;
  background: #fff;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.audit-title {
  font-size: 1rem;
  font-weight: 600;
  color: #1a202c;
  margin: 0;
}

.audit-badges {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  align-items: center;
}

.btn-download-report {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.3rem 0.75rem;
  font-size: 0.8rem;
  font-weight: 500;
  color: #2563eb;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  border-radius: 0.375rem;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s, color 0.15s;
  white-space: nowrap;
}

.btn-download-report:hover:not(:disabled) {
  background: #dbeafe;
  border-color: #93c5fd;
  color: #1d4ed8;
}

.btn-download-report:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.audit-body {
  padding: 1.5rem;
}

.audit-info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1rem;
}

.audit-info-item {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
}

.audit-info-item i {
  color: #2563eb;
  font-size: 1.25rem;
  margin-top: 0.25rem;
}

.audit-info-item label {
  font-size: 0.75rem;
  font-weight: 600;
  color: #718096;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  display: block;
  margin-bottom: 0.25rem;
}

.audit-info-item p {
  font-size: 0.875rem;
  color: #1a202c;
  margin: 0;
}

.audit-scope,
.audit-comments {
  margin-top: 1rem;
  padding: 1rem;
  background: #fff;
  border-radius: 0.375rem;
  border-left: 3px solid #2563eb;
}

.audit-scope label,
.audit-comments label {
  font-size: 0.75rem;
  font-weight: 600;
  color: #718096;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  display: block;
  margin-bottom: 0.5rem;
}

.audit-scope p,
.audit-comments p {
  font-size: 0.875rem;
  color: #4a5568;
  margin: 0;
  line-height: 1.6;
}

.audit-findings {
  margin-top: 1rem;
  padding: 1rem;
  background: #fef3c7;
  border-radius: 0.375rem;
  border-left: 3px solid #f59e0b;
}

.audit-findings label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #92400e;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.audit-findings label i {
  color: #f59e0b;
}

.findings-list {
  display: grid;
  gap: 0.75rem;
}

.finding-item {
  background: #fff;
  padding: 0.75rem;
  border-radius: 0.375rem;
  border: 1px solid #fbbf24;
}

.finding-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.finding-date {
  font-size: 0.75rem;
  color: #718096;
  font-weight: 600;
}

.finding-details {
  font-size: 0.875rem;
  color: #1a202c;
  margin: 0 0 0.5rem 0;
  line-height: 1.5;
}

.finding-impact,
.finding-comment {
  font-size: 0.8125rem;
  color: #4a5568;
  margin: 0.25rem 0;
  line-height: 1.5;
}

.empty-state-small {
  text-align: center;
  padding: 2rem 1rem;
  color: #9ca3af;
}

.empty-state-small i {
  font-size: 2rem;
  margin-bottom: 0.5rem;
  display: block;
}

.empty-state-small p {
  margin: 0;
  font-size: 0.875rem;
}

/* External Screening Tab Styles */
.screening-filters {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
  padding: 1rem;
  background: #f7fafc;
  border-radius: 0.5rem;
  flex-wrap: wrap;
  align-items: flex-end;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.filter-group label {
  font-size: 0.75rem;
  font-weight: 600;
  color: #718096;
  text-transform: uppercase;
}

.filter-input {
  padding: 0.5rem 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  min-width: 150px;
}

.btn-sm {
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
}

.btn-secondary {
  background: #6b7280;
  color: #fff;
}

.btn-secondary:hover {
  background: #4b5563;
}

.loading-state-small,
.error-state-small {
  text-align: center;
  padding: 2rem;
  color: #9ca3af;
}

.spinner-small {
  width: 2rem;
  height: 2rem;
  border: 3px solid #e2e8f0;
  border-top-color: #2563eb;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

.error-state-small i {
  font-size: 2rem;
  color: #dc2626;
  margin-bottom: 1rem;
}

.empty-state-subtitle {
  font-size: 0.875rem;
  color: #9ca3af;
  margin-top: 0.5rem;
}

.screening-versions {
  display: grid;
  gap: 2rem;
}

.screening-version {
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  overflow: hidden;
  background: #fff;
}

.version-header {
  padding: 1rem 1.5rem;
  background: #f7fafc;
  border-bottom: 2px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.version-title {
  font-size: 1rem;
  font-weight: 600;
  color: #1a202c;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.version-title i {
  color: #2563eb;
}

.version-badge {
  padding: 0.25rem 0.75rem;
  background: #dbeafe;
  color: #1e40af;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
}

.screening-results-list {
  padding: 1.5rem;
  display: grid;
  gap: 1.5rem;
}

.screening-result-card {
  padding: 1.5rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  background: #f7fafc;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #e2e8f0;
  flex-wrap: wrap;
  gap: 1rem;
}

.result-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.result-type {
  font-size: 1rem;
  font-weight: 600;
  color: #1a202c;
}

.result-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.25rem;
}

.result-date {
  font-size: 0.875rem;
  color: #718096;
}

.result-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
  margin-bottom: 1rem;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.stat-item label {
  font-size: 0.75rem;
  font-weight: 600;
  color: #718096;
  text-transform: uppercase;
}

.stat-value {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1a202c;
}

.stat-high-risk {
  color: #dc2626;
}

.result-review {
  padding: 1rem;
  background: #fff;
  border-radius: 0.375rem;
  border-left: 3px solid #2563eb;
  margin-bottom: 1rem;
}

.review-item {
  margin-bottom: 0.5rem;
}

.review-item:last-child {
  margin-bottom: 0;
}

.review-item label {
  font-size: 0.75rem;
  font-weight: 600;
  color: #718096;
  text-transform: uppercase;
  display: block;
  margin-bottom: 0.25rem;
}

.review-item p {
  margin: 0.25rem 0 0 0;
  font-size: 0.875rem;
  color: #4a5568;
  line-height: 1.5;
}

.matches-section {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e2e8f0;
}

.matches-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: #4a5568;
  margin: 0 0 1rem 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.matches-list {
  display: grid;
  gap: 1rem;
}

.match-card {
  padding: 1rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.375rem;
  background: #fff;
  border-left: 4px solid;
}

.match-low-risk {
  border-left-color: #10b981;
}

.match-medium-risk {
  border-left-color: #f59e0b;
}

.match-high-risk {
  border-left-color: #dc2626;
}

.match-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.match-type {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  color: #1a202c;
}

.match-score {
  display: flex;
  align-items: center;
}

.score-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
}

.score-low {
  background: #d1fae5;
  color: #065f46;
}

.score-medium {
  background: #fef3c7;
  color: #92400e;
}

.score-high {
  background: #fee2e2;
  color: #991b1b;
}

.match-details {
  margin-bottom: 0.75rem;
  padding: 0.75rem;
  background: #f7fafc;
  border-radius: 0.375rem;
}

.match-detail-item {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
}

.match-detail-item:last-child {
  margin-bottom: 0;
}

.match-detail-item label {
  font-weight: 600;
  color: #4a5568;
  min-width: 120px;
}

.match-detail-item span {
  color: #1a202c;
  word-break: break-word;
}

.match-resolution {
  padding: 0.75rem;
  background: #f7fafc;
  border-radius: 0.375rem;
  border-top: 1px solid #e2e8f0;
}

.resolution-status {
  margin-bottom: 0.5rem;
}

.resolution-status label {
  font-size: 0.75rem;
  font-weight: 600;
  color: #718096;
  text-transform: uppercase;
  margin-right: 0.5rem;
}

.resolution-notes {
  margin-top: 0.5rem;
}

.resolution-notes label {
  font-size: 0.75rem;
  font-weight: 600;
  color: #718096;
  text-transform: uppercase;
  display: block;
  margin-bottom: 0.25rem;
}

.resolution-notes p {
  margin: 0;
  font-size: 0.875rem;
  color: #4a5568;
  line-height: 1.5;
}

.resolution-date {
  margin-top: 0.5rem;
  font-size: 0.75rem;
  color: #718096;
}

.resolution-date label {
  font-weight: 600;
  margin-right: 0.5rem;
}

.no-matches {
  padding: 1rem;
  text-align: center;
  color: #10b981;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  font-weight: 500;
}

.no-matches i {
  font-size: 1.25rem;
}

@media (max-width: 768px) {
  .screening-filters {
    flex-direction: column;
  }

  .filter-group {
    width: 100%;
  }

  .result-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .result-meta {
    align-items: flex-start;
  }

  .result-stats {
    grid-template-columns: 1fr;
  }

  .match-header {
    flex-direction: column;
    align-items: flex-start;
  }
}

/* RFP Tab Styles */
.rfp-content {
  margin-top: 1rem;
}

.rfp-subsection {
  margin-top: 2rem;
  padding-top: 2rem;
  border-top: 2px solid #e2e8f0;
}

.rfp-subsection:first-child {
  margin-top: 0;
  padding-top: 0;
  border-top: none;
}

.proposal-data-container {
  background: #f7fafc;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  padding: 1rem;
  overflow-x: auto;
}

.proposal-data {
  margin: 0;
  font-family: 'Courier New', monospace;
  font-size: 0.875rem;
  color: #1a202c;
  white-space: pre-wrap;
  word-wrap: break-word;
  line-height: 1.6;
}

/* Clean JSON Renderer Styles */
.json-data-container {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 0.75rem;
  padding: 1.5rem;
  overflow-x: auto;
  max-height: 800px;
  overflow-y: auto;
}

.json-renderer {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  font-size: 0.875rem;
  line-height: 1.6;
  color: #1a202c;
}

/* Clean Section Cards */
.clean-section {
  margin-bottom: 1.5rem;
}

.clean-section-card {
  background: #f7fafc;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  padding: 1.25rem;
  margin-bottom: 1rem;
}

.section-header {
  font-size: 1rem;
  font-weight: 600;
  color: #1a202c;
  margin: 0 0 1rem 0;
  padding-bottom: 0.75rem;
  border-bottom: 2px solid #e2e8f0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.section-header i {
  color: #2563eb;
  font-size: 1.125rem;
}

.subsection-header {
  font-size: 0.875rem;
  font-weight: 600;
  color: #4a5568;
  margin: 0 0 0.75rem 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.subsection-header i {
  color: #2563eb;
}

/* Clean Field Rows */
.clean-field-row {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 0.75rem 0;
  border-bottom: 1px solid #f7fafc;
}

.clean-field-row:last-child {
  border-bottom: none;
}

.clean-field-row label {
  font-weight: 600;
  color: #4a5568;
  min-width: 180px;
  flex-shrink: 0;
  font-size: 0.875rem;
}

.clean-value {
  color: #1a202c;
  word-break: break-word;
  flex: 1;
}

.clean-value.clean-string {
  color: #1a202c;
}

.clean-value.clean-number {
  color: #2563eb;
  font-weight: 500;
}

.clean-value.clean-date {
  color: #7c3aed;
  font-weight: 500;
}

/* Clean Arrays */
.clean-array-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 0.5rem 0;
}

.clean-array-item {
  padding: 0.75rem;
  background: #f7fafc;
  border-radius: 0.375rem;
  border: 1px solid #e2e8f0;
}

/* Clean Nested Objects */
.clean-nested-object {
  padding: 0.5rem 0;
}

.clean-primitive {
  display: inline-block;
}

/* Metadata Section */
.metadata-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 1rem;
}

.metadata-field {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.metadata-field label {
  font-size: 0.75rem;
  font-weight: 600;
  color: #718096;
  text-transform: uppercase;
}

.metadata-nested {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
  padding: 0.5rem 0;
}

/* Team Info Nested */
.team-info-nested {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 0.5rem 0;
}

.team-field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.team-field label {
  font-weight: 600;
  color: #4a5568;
  font-size: 0.875rem;
}

.key-personnel-section {
  margin-top: 1rem;
}

.json-empty {
  color: #9ca3af;
  font-style: italic;
  font-size: 0.875rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem;
  text-align: center;
  justify-content: center;
}

.json-empty i {
  font-size: 1rem;
}

/* Link Styles */
.json-link {
  color: #2563eb;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  border-radius: 0.375rem;
  background: #dbeafe;
  transition: all 0.2s;
  word-break: break-word;
  font-weight: 500;
  font-size: 0.875rem;
}

.json-link:hover {
  background: #bfdbfe;
  text-decoration: underline;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(37, 99, 235, 0.2);
}

.json-link i {
  font-size: 0.875rem;
}

/* Clean UI Components */
.info-grid-clean {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1rem;
  padding: 0.5rem 0;
}

.info-item-clean {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 1rem;
  background: #fff;
  border-radius: 0.5rem;
  border: 1px solid #e2e8f0;
  transition: all 0.2s;
}

.info-item-clean:hover {
  border-color: #2563eb;
  box-shadow: 0 2px 4px rgba(37, 99, 235, 0.1);
}

.info-item-clean label {
  font-size: 0.75rem;
  font-weight: 600;
  color: #718096;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.info-item-clean .info-value {
  font-size: 0.875rem;
  color: #1a202c;
  word-break: break-word;
  line-height: 1.5;
}

.personnel-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
  padding: 1rem 0;
}

.personnel-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  padding: 1rem;
  transition: all 0.2s;
}

.personnel-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border-color: #2563eb;
}

.personnel-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
  padding-bottom: 0.75rem;
  border-bottom: 2px solid #e2e8f0;
}

.personnel-header i {
  font-size: 1.5rem;
  color: #2563eb;
}

.personnel-header h4 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: #1a202c;
}

.personnel-details {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.personnel-details .detail-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.personnel-details .detail-item label {
  font-size: 0.75rem;
  font-weight: 600;
  color: #718096;
  text-transform: uppercase;
}

.personnel-details .detail-item span {
  font-size: 0.875rem;
  color: #1a202c;
}

.certifications-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.25rem;
}

.cert-badge {
  padding: 0.25rem 0.75rem;
  background: #dbeafe;
  color: #1e40af;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 500;
}

.documents-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
  padding: 1rem 0;
}

.document-item-card {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1rem;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  transition: all 0.2s;
}

.document-item-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border-color: #2563eb;
}

.document-item-card i {
  font-size: 2rem;
  color: #2563eb;
  flex-shrink: 0;
}

.document-details {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.doc-name {
  font-weight: 600;
  color: #1a202c;
  font-size: 0.875rem;
  word-break: break-word;
}

.doc-url {
  margin-top: 0.25rem;
}

.doc-size,
.doc-type {
  font-size: 0.75rem;
  color: #718096;
}

.metadata-section {
  padding: 1rem;
  background: #f7fafc;
  border-radius: 0.5rem;
  border: 1px solid #e2e8f0;
}

.metadata-item {
  margin-bottom: 1rem;
}

.metadata-item:last-child {
  margin-bottom: 0;
}

.metadata-item label {
  display: block;
  font-size: 0.75rem;
  font-weight: 600;
  color: #718096;
  text-transform: uppercase;
  margin-bottom: 0.5rem;
}

.json-object-fields-default {
  padding: 0.5rem 0;
}

.json-array-items-default {
  padding: 0.5rem 0;
}

/* Badge styles for boolean values */
.badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.badge-success {
  background: #d1fae5;
  color: #065f46;
}

.badge-secondary {
  background: #f3f4f6;
  color: #374151;
}

/* Responsive */
@media (max-width: 768px) {
  .json-key {
    min-width: 100px;
    font-size: 0.8125rem;
  }
  
  .json-object-fields,
  .json-array-items {
    margin-left: 0.5rem;
    padding-left: 0.5rem;
  }
  
  .json-level-1 {
    padding-left: 0.5rem;
  }
  
  .json-level-2 {
    padding-left: 1rem;
  }
  
  .json-level-3 {
    padding-left: 1.5rem;
  }
  
  .info-grid-clean {
    grid-template-columns: 1fr;
  }
  
  .personnel-grid,
  .documents-grid {
    grid-template-columns: 1fr;
  }
}
</style>
