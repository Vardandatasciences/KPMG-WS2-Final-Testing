<template>
  <div class="vendor_vendor-registration-container">
    <!-- Header -->
    <div class="vendor_registration-header">
      <div>
        <h1 class="vendor_registration-title">Vendor Registration</h1>
        <p class="vendor_registration-subtitle">Register and manage vendor profiles</p>
      </div>
      <div class="vendor_action-buttons">
        <!-- RFP Details Button -->
        <button 
          class="vendor_btn vendor_btn-outline" 
          :class="{ 'vendor_rfp-details-active': vendor_isToggleActive }"
          @click="vendor_toggleView"
          :title="vendor_isToggleActive ? 'Switch to Form View' : 'Switch to Data View'"
        >
          <svg class="vendor_h-4 vendor_w-4 vendor_mr-2" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          RFP Details
        </button>

        <button class="vendor_btn vendor_btn-outline" @click="vendor_refreshUserData" :disabled="vendor_isLoadingUserData" title="Refresh User Data">
          <svg class="vendor_h-4 vendor_w-4 vendor_mr-2" :class="{ 'animate-spin': vendor_isLoadingUserData }" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          {{ vendor_isLoadingUserData ? 'Loading...' : 'Refresh Data' }}
        </button>
        
        <!-- Form Actions - Always visible, disabled only when submitting or in data view -->
        <button 
          class="vendor_btn vendor_btn-outline" 
          @click="vendor_saveDraft" 
          :disabled="vendor_isSubmitting || vendor_isToggleActive"
          title="Save draft registration"
        >
          <svg class="vendor_h-4 vendor_w-4 vendor_mr-2" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
          </svg>
          {{ vendor_isSubmitting ? 'Saving...' : 'Save Draft' }}
        </button>
        <button 
          class="vendor_btn vendor_btn-primary" 
          @click="vendor_submitRegistration" 
          :disabled="vendor_isSubmitting || vendor_isToggleActive"
          title="Submit vendor registration for approval"
        >
          <svg class="vendor_h-4 vendor_w-4 vendor_mr-2" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
          </svg>
          {{ vendor_isSubmitting ? 'Submitting...' : 'Submit' }}
        </button>
        
        <!-- Screening Status Notification -->
        <div v-if="vendor_screeningStatus" class="vendor_screening-notification" :class="vendor_screeningStatus.type">
          <div class="vendor_notification-content">
            <svg class="vendor_h-4 vendor_w-4 vendor_mr-2" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path v-if="vendor_screeningStatus.type === 'success'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
              <path v-else-if="vendor_screeningStatus.type === 'warning'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"/>
              <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
            <span>{{ vendor_screeningStatus.message }}</span>
          </div>
          <button @click="vendor_screeningStatus = null" class="vendor_notification-close">
            <svg class="vendor_h-4 vendor_w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
      </div>
    </div>


    <!-- No Vendor Information Message -->
    <div v-if="vendor_noVendorInfo" class="vendor_already-registered">
      <div class="vendor_already-registered-content">
        <div class="vendor_already-registered-icon">
          <svg class="vendor_w-16 vendor_h-16" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <div class="vendor_already-registered-text">
          <h2 class="vendor_already-registered-title">No Vendor Information</h2>
          <p class="vendor_already-registered-message">
            No vendor information found for your account. If you believe this is an error, please contact support.
          </p>
        </div>
      </div>
    </div>

    <!-- Already Registered Message -->
    <div v-if="vendor_hasAlreadyRegistered" class="vendor_already-registered">
      <div class="vendor_already-registered-content">
        <div class="vendor_already-registered-icon">
          <svg class="vendor_w-16 vendor_h-16" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <div class="vendor_already-registered-text">
          <h2 class="vendor_already-registered-title">You Have Already Registered</h2>
          <p class="vendor_already-registered-message">
            Your vendor registration is already in progress or completed. 
            You are currently at stage {{ vendor_formData.lifecycle_data?.current_stage?.stage_id || 'Unknown' }}: 
            {{ vendor_formData.lifecycle_data?.current_stage?.stage_name || 'Unknown Stage' }}.
          </p>
          <div class="vendor_already-registered-actions">
            <button class="vendor_btn vendor_btn-primary" @click="vendor_viewProgress">
              <svg class="vendor_w-4 vendor_h-4 vendor_mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              View Progress
            </button>
            <button class="vendor_btn vendor_btn-outline" @click="vendor_refreshUserData">
              <svg class="vendor_w-4 vendor_h-4 vendor_mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Refresh Status
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Data View (shown when toggle is active) -->
    <div v-if="vendor_isToggleActive" class="vendor_data-view">
      <div class="vendor_card">
        <div class="vendor_card-header">
          <div class="vendor_card-header-content">
            <div>
              <h3 class="vendor_card-title">Registration Data Overview</h3>
              <p class="vendor_card-subtitle">Current registration data and statistics</p>
            </div>
            <button class="vendor_btn vendor_btn-outline vendor_back-btn" @click="vendor_toggleView" title="Back to Registration Form">
              <svg class="vendor_h-4 vendor_w-4 vendor_mr-2" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              Back to Form
            </button>
          </div>
        </div>
        <div class="vendor_card-content">
          <!-- Loading indicator -->
          <div v-if="vendor_isLoadingUserData" style="display: flex; justify-content: center; align-items: center; padding: 3rem; color: #6b7280;">
            <svg class="vendor_h-4 vendor_w-4" style="width: 2rem; height: 2rem; animation: spin 1s linear infinite;" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            <span style="margin-left: 0.75rem; font-size: 1rem;">Loading user data...</span>
          </div>
          
            <!-- Data content -->
    <div v-if="!vendor_isLoadingUserData && vendor_formData.rfp_response_data" class="vendor_toggle-tabs-container">
      <!-- Tab Navigation -->
      <div class="vendor_toggle-tabs">
        <button 
          class="vendor_toggle-tab" 
          :class="{ 'vendor_toggle-tab-active': vendor_toggleActiveTab === 'overview' }"
          @click="vendor_toggleActiveTab = 'overview'"
        >
          <svg class="vendor_w-4 vendor_h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          Overview
        </button>
        <button 
          class="vendor_toggle-tab" 
          :class="{ 'vendor_toggle-tab-active': vendor_toggleActiveTab === 'documents' }"
          @click="vendor_toggleActiveTab = 'documents'"
        >
          <svg class="vendor_w-4 vendor_h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          Documents
        </button>
      </div>

      <!-- Tab Content -->
      <div class="vendor_toggle-tab-content">
        <!-- Overview Tab -->
        <div v-if="vendor_toggleActiveTab === 'overview'" class="vendor_data-grid">
          <!-- RFP Response Summary - Company/Vendor Details -->
          <div class="vendor_data-section">
            <h4 class="vendor_data-section-title">Vendor Details</h4>
            <div class="vendor_data-item">
              <span class="vendor_data-label">Company Name:</span>
              <span class="vendor_data-value">{{ (vendor_formData.rfp_response_data.response_documents && vendor_formData.rfp_response_data.response_documents.companyInfo && vendor_formData.rfp_response_data.response_documents.companyInfo.companyName) || 'Not provided' }}</span>
            </div>
            <div class="vendor_data-item">
              <span class="vendor_data-label">Contact Name:</span>
              <span class="vendor_data-value">{{ (vendor_formData.rfp_response_data.response_documents && vendor_formData.rfp_response_data.response_documents.companyInfo && vendor_formData.rfp_response_data.response_documents.companyInfo.contactName) || 'Not provided' }}</span>
            </div>
            <div class="vendor_data-item">
              <span class="vendor_data-label">Contact Email:</span>
              <span class="vendor_data-value">{{ (vendor_formData.rfp_response_data.response_documents && vendor_formData.rfp_response_data.response_documents.companyInfo && vendor_formData.rfp_response_data.response_documents.companyInfo.email) || 'Not provided' }}</span>
            </div>
            <div class="vendor_data-item">
              <span class="vendor_data-label">Contact Phone:</span>
              <span class="vendor_data-value">{{ (vendor_formData.rfp_response_data.response_documents && vendor_formData.rfp_response_data.response_documents.companyInfo && vendor_formData.rfp_response_data.response_documents.companyInfo.phone) || 'Not provided' }}</span>
            </div>
            <div class="vendor_data-item">
              <span class="vendor_data-label">Submission Date:</span>
              <span class="vendor_data-value">{{ vendor_formatDate(vendor_formData.rfp_response_data.submission_date) }}</span>
            </div>
          </div>

          <!-- Financial/Scoring Summary from RFP Response -->
          <div class="vendor_data-section">
            <h4 class="vendor_data-section-title">Proposal & Financial Details</h4>
            <div class="vendor_data-item">
              <span class="vendor_data-label">Proposed Value:</span>
              <span class="vendor_data-value">{{ vendor_formData.rfp_response_data.proposed_value ? `$${Number(vendor_formData.rfp_response_data.proposed_value).toLocaleString()}` : 'Not provided' }}</span>
            </div>
            <div class="vendor_data-item">
              <span class="vendor_data-label">Business Type:</span>
              <span class="vendor_data-value">{{ (vendor_formData.rfp_response_data.response_documents && vendor_formData.rfp_response_data.response_documents.companyInfo && vendor_formData.rfp_response_data.response_documents.companyInfo.businessType) || 'Not provided' }}</span>
            </div>
            <div class="vendor_data-item">
              <span class="vendor_data-label">Annual Revenue:</span>
              <span class="vendor_data-value">{{ (vendor_formData.rfp_response_data.response_documents && vendor_formData.rfp_response_data.response_documents.companyInfo && vendor_formData.rfp_response_data.response_documents.companyInfo.annualRevenue) || 'Not provided' }}</span>
            </div>
            <div class="vendor_data-item">
              <span class="vendor_data-label">Employee Count:</span>
              <span class="vendor_data-value">{{ (vendor_formData.rfp_response_data.response_documents && vendor_formData.rfp_response_data.response_documents.companyInfo && vendor_formData.rfp_response_data.response_documents.companyInfo.employeeCount) || 'Not provided' }}</span>
            </div>
          </div>

          <!-- Status Summary from RFP Response -->
          <div class="vendor_data-section">
            <h4 class="vendor_data-section-title">Status & Evaluation</h4>
            <div class="vendor_data-item">
              <span class="vendor_data-label">Evaluation Status:</span>
              <span class="vendor_data-value vendor_data-badge" :class="`vendor_data-badge-${(vendor_formData.rfp_response_data.evaluation_status || 'default').toLowerCase()}`">
                {{ vendor_formData.rfp_response_data.evaluation_status || 'Not evaluated' }}
              </span>
            </div>
            <div class="vendor_data-item">
              <span class="vendor_data-label">Submission Status:</span>
              <span class="vendor_data-value vendor_data-badge" :class="`vendor_data-badge-${(vendor_formData.rfp_response_data.submission_status || 'default').toLowerCase()}`">
                {{ vendor_formData.rfp_response_data.submission_status || 'Not submitted' }}
              </span>
            </div>
            <div class="vendor_data-item">
              <span class="vendor_data-label">Completion %:</span>
              <span class="vendor_data-value">{{ vendor_formData.rfp_response_data.completion_percentage ? `${vendor_formData.rfp_response_data.completion_percentage}%` : '0%' }}</span>
            </div>
          </div>

          <!-- Company Information from RFP Response -->
          <div class="vendor_data-section">
            <h4 class="vendor_data-section-title">Company Information</h4>
            <div class="vendor_data-item">
              <span class="vendor_data-label">Legal Name:</span>
              <span class="vendor_data-value">{{ (vendor_formData.rfp_response_data.response_documents && vendor_formData.rfp_response_data.response_documents.companyInfo && vendor_formData.rfp_response_data.response_documents.companyInfo.legalName) || 'Not provided' }}</span>
            </div>
            <div class="vendor_data-item">
              <span class="vendor_data-label">Tax ID:</span>
              <span class="vendor_data-value">{{ (vendor_formData.rfp_response_data.response_documents && vendor_formData.rfp_response_data.response_documents.companyInfo && vendor_formData.rfp_response_data.response_documents.companyInfo.taxId) || 'Not provided' }}</span>
            </div>
            <div class="vendor_data-item">
              <span class="vendor_data-label">DUNS Number:</span>
              <span class="vendor_data-value">{{ (vendor_formData.rfp_response_data.response_documents && vendor_formData.rfp_response_data.response_documents.companyInfo && vendor_formData.rfp_response_data.response_documents.companyInfo.dunsNumber) || 'Not provided' }}</span>
            </div>
            <div class="vendor_data-item">
              <span class="vendor_data-label">Industry Sector:</span>
              <span class="vendor_data-value">{{ (vendor_formData.rfp_response_data.response_documents && vendor_formData.rfp_response_data.response_documents.companyInfo && vendor_formData.rfp_response_data.response_documents.companyInfo.industrySector) || 'Not provided' }}</span>
            </div>
          </div>

          <!-- Documents Summary -->
          <div class="vendor_data-section">
            <h4 class="vendor_data-section-title">Documents Summary</h4>
            <div class="vendor_data-item">
              <span class="vendor_data-label">Available Documents:</span>
              <span class="vendor_data-value">{{ vendor_formData.rfp_response_data.document_urls ? Object.keys(vendor_formData.rfp_response_data.document_urls).length : 0 }}</span>
            </div>
          </div>
        </div>

        <!-- Documents Tab -->
        <div v-if="vendor_toggleActiveTab === 'documents'" class="vendor_documents-tab-content">
          <div v-if="vendor_formData.rfp_response_data && vendor_formData.rfp_response_data.document_urls" class="vendor_documents-grid">
            <div v-for="(url, key) in vendor_formData.rfp_response_data.document_urls" :key="key" class="vendor_document-card">
              <div class="vendor_document-card-header">
                <div class="vendor_document-icon">
                  <svg class="vendor_w-8 vendor_h-8" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <div class="vendor_document-info">
                  <h5 class="vendor_document-title">{{ key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) }}</h5>
                  <p class="vendor_document-type">PDF Document</p>
                </div>
              </div>
              <div class="vendor_document-card-content">
                <div class="vendor_document-actions">
                  <button class="vendor_btn vendor_btn-primary" @click="vendor_openDocumentInModal(typeof url === 'object' && url.url ? url.url : url, key)" title="View Document">
                    <svg class="vendor_w-4 vendor_h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                    View Document
                  </button>
                  <button class="vendor_btn vendor_btn-outline" @click="vendor_copyUrl(typeof url === 'object' && url.url ? url.url : url)" title="Copy URL">
                    <svg class="vendor_w-4 vendor_h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                    Copy URL
                  </button>
                  <button class="vendor_btn vendor_btn-outline" @click="vendor_downloadDocumentUrl(typeof url === 'object' && url.url ? url.url : url, key)" title="Download Document">
                    <svg class="vendor_w-4 vendor_h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    Download
                  </button>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="vendor_no-documents">
            <div class="vendor_no-documents-icon">
              <svg class="vendor_w-16 vendor_h-16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h3 class="vendor_no-documents-title">No Documents Available</h3>
            <p class="vendor_no-documents-text">There are no documents associated with this RFP response.</p>
          </div>
        </div>
      </div>



          </div>
        </div>
      </div>
    </div>

    <!-- Tabs (shown when toggle is inactive and vendor hasn't already registered and vendor information exists) -->
    <div v-if="!vendor_isToggleActive && !vendor_hasAlreadyRegistered && !vendor_noVendorInfo" class="vendor_tabs">
      <div class="vendor_tabs-list">
        <button 
          v-for="vendor_tab in vendor_tabs" 
          :key="vendor_tab.id"
          class="vendor_tabs-trigger"
          :class="{ 'vendor_tabs-trigger-active': vendor_activeTab === vendor_tab.id }"
          @click="vendor_activeTab = vendor_tab.id"
        >
          {{ vendor_tab.label }}
        </button>
      </div>

      <!-- Company Info Tab -->
      <div v-if="vendor_activeTab === 'company-info'" class="vendor_tabs-content">
        <div class="vendor_card">
          <div class="vendor_card-header">
            <h3 class="vendor_card-title">Company Information</h3>
          </div>
          <div class="vendor_card-content">
            <div class="vendor_form-grid">
              <div class="vendor_form-item">
                <label class="vendor_form-label" for="vendor-code">Vendor Code</label>
                <input id="vendor-code" class="vendor_input" v-model="vendor_formData.vendor_code" />
              </div>
              <div class="vendor_form-item">
                <label class="vendor_form-label" for="company-name">Company Name</label>
                <input id="company-name" class="vendor_input" v-model="vendor_formData.company_name" required />
              </div>
              <div class="vendor_form-item">
                <label class="vendor_form-label" for="legal-name">Legal Name</label>
                <input id="legal-name" class="vendor_input" v-model="vendor_formData.legal_name" />
              </div>
              <div class="vendor_form-item">
                <label class="vendor_form-label" for="business-type">Business Type</label>
                <select id="business-type" class="vendor_select" v-model="vendor_formData.business_type">
                  <option value="">Select business type</option>
                  <option value="corporation">Corporation</option>
                  <option value="llc">LLC</option>
                  <option value="partnership">Partnership</option>
                  <option value="sole-proprietorship">Sole Proprietorship</option>
                </select>
              </div>
              <div class="vendor_form-item">
                <label class="vendor_form-label" for="tax-id">Tax ID</label>
                <input id="tax-id" class="vendor_input" v-model="vendor_formData.tax_id" />
              </div>
              <div class="vendor_form-item">
                <label class="vendor_form-label" for="duns-number">DUNS Number</label>
                <input id="duns-number" class="vendor_input" v-model="vendor_formData.duns_number" />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Legal & Financial Tab -->
      <div v-if="vendor_activeTab === 'legal-financial'" class="vendor_tabs-content">
        <div class="vendor_card">
          <div class="vendor_card-header">
            <h3 class="vendor_card-title">Legal & Financial Details</h3>
          </div>
          <div class="vendor_card-content">
            <div class="vendor_form-grid">
              <div class="vendor_form-item">
                <label class="vendor_form-label" for="incorporation-date">Incorporation Date</label>
                <div class="vendor_relative">
                  <input id="incorporation-date" class="vendor_input vendor_pl-10" type="date" v-model="vendor_formData.incorporation_date" />
                  <svg class="vendor_absolute vendor_left-3 vendor_top-half vendor_transform vendor_-translate-y-half vendor_h-4 vendor_w-4 vendor_text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
              </div>
              <div class="vendor_form-item">
                <label class="vendor_form-label" for="industry-sector">Industry Sector</label>
                <select id="industry-sector" class="vendor_select" v-model="vendor_formData.industry_sector">
                  <option value="">Select industry</option>
                  <option value="technology">Technology</option>
                  <option value="finance">Finance</option>
                  <option value="healthcare">Healthcare</option>
                  <option value="manufacturing">Manufacturing</option>
                  <option value="retail">Retail</option>
                </select>
              </div>
              <div class="vendor_form-item">
                <label class="vendor_form-label" for="website">Website</label>
                <input id="website" class="vendor_input" v-model="vendor_formData.website" placeholder="https://example.com" />
              </div>
              <div class="vendor_form-item">
                <label class="vendor_form-label" for="annual-revenue">Annual Revenue</label>
                <input id="annual-revenue" class="vendor_input" type="number" step="0.01" v-model.number="vendor_formData.annual_revenue" placeholder="1000000" />
              </div>
              <div class="vendor_form-item">
                <label class="vendor_form-label" for="employee-count">Employee Count</label>
                <input id="employee-count" class="vendor_input" type="number" v-model.number="vendor_formData.employee_count" placeholder="100" />
              </div>
              <div class="vendor_form-item">
                <label class="vendor_form-label" for="headquarters">Headquarters Address</label>
                <textarea id="headquarters" class="vendor_textarea" v-model="vendor_formData.headquarters_address" placeholder="123 Main St, City, State, ZIP"></textarea>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Category & Risk Tab -->
      <div v-if="vendor_activeTab === 'category-risk'" class="vendor_tabs-content">
        <div class="vendor_card">
          <div class="vendor_card-header">
            <h3 class="vendor_card-title">Category & Risk Assessment</h3>
          </div>
          <div class="vendor_card-content">
            <div class="vendor_form-grid">
              <div class="vendor_form-item">
                <label class="vendor_form-label" for="vendor-category">Vendor Category</label>
                <select id="vendor-category" class="vendor_select" v-model="vendor_formData.vendor_category">
                  <option value="">Select category</option>
                  <option value="software">Software</option>
                  <option value="services">Services</option>
                  <option value="consulting">Consulting</option>
                  <option value="hardware">Hardware</option>
                  <option value="maintenance">Maintenance</option>
                </select>
              </div>
              <div class="vendor_form-item">
                <label class="vendor_form-label" for="risk-level">Risk Level</label>
                <select id="risk-level" class="vendor_select" v-model="vendor_formData.risk_level">
                  <option value="">Select risk level</option>
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                </select>
              </div>
              <div class="vendor_form-item">
                <label class="vendor_form-label" for="status">Status</label>
                <select id="status" class="vendor_select" v-model="vendor_formData.status">
                  <option value="">Select status</option>
                  <option value="active">Active</option>
                  <option value="pending">Pending</option>
                  <option value="suspended">Suspended</option>
                  <option value="inactive">Inactive</option>
                </select>
              </div>
              <div class="vendor_form-item">
                <label class="vendor_form-label" for="has-system-access">Has System Access</label>
                <div class="vendor_checkbox-container">
                  <input type="checkbox" id="has-system-access" class="vendor_checkbox" v-model="vendor_formData.has_system_access" />
                  <label class="vendor_form-label" for="has-system-access">Has System Access</label>
                </div>
              </div>
            </div>
            
            <div class="vendor_space-y-4">
              <div class="vendor_checkbox-container">
                <input type="checkbox" id="critical-vendor" class="vendor_checkbox" v-model="vendor_formData.is_critical_vendor" />
                <label class="vendor_form-label" for="critical-vendor">Is Critical Vendor</label>
              </div>
              <div class="vendor_checkbox-container">
                <input type="checkbox" id="data-access" class="vendor_checkbox" v-model="vendor_formData.has_data_access" />
                <label class="vendor_form-label" for="data-access">Has Data Access</label>
              </div>
            </div>

            <div class="vendor_form-item">
              <label class="vendor_form-label" for="description">Description</label>
              <textarea 
                id="description" 
                class="vendor_textarea"
                v-model="vendor_formData.description"
                placeholder="Vendor description and notes..."
                style="min-height: 100px;"
              ></textarea>
            </div>
          </div>
        </div>
      </div>

      <!-- Contacts Tab -->
      <div v-if="vendor_activeTab === 'contacts'" class="vendor_tabs-content">
        <div class="vendor_card">
          <div class="vendor_card-header">
            <div class="vendor_flex vendor_items-center vendor_justify-between">
              <h3 class="vendor_card-title">Vendor Contacts</h3>
              <button 
                class="vendor_btn vendor_btn-primary" 
                @click="vendor_addContact"
                title="Add new contact"
              >
                <svg class="vendor_h-4 vendor_w-4 vendor_mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
                Add Contact
              </button>
            </div>
          </div>
          <div class="vendor_card-content vendor_space-y-4">
            <div v-if="vendor_contacts.length === 0" class="vendor_no-contacts">
              <div class="vendor_no-contacts-icon">
                <svg class="vendor_w-16 vendor_h-16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
              </div>
              <h3 class="vendor_no-contacts-title">No Contacts Added</h3>
              <p class="vendor_no-contacts-text">Click "Add Contact" to add your first vendor contact.</p>
            </div>
            <div v-for="contact in vendor_contacts" :key="contact.id" class="vendor_contact-card">
              <!-- Editing Mode -->
              <div v-if="contact.isEditing" class="vendor_form-grid" style="grid-template-columns: 1fr;">
                <div class="vendor_form-item">
                  <label class="vendor_form-label">Name</label>
                  <input v-model="contact.name" class="vendor_input" placeholder="Contact Name" />
                </div>
                <div class="vendor_form-item">
                  <label class="vendor_form-label">Email</label>
                  <input v-model="contact.email" class="vendor_input" type="email" placeholder="contact@example.com" />
                </div>
                <div class="vendor_form-item">
                  <label class="vendor_form-label">Phone</label>
                  <input v-model="contact.phone" class="vendor_input" placeholder="+1-555-0000" />
                </div>
                <div class="vendor_form-item">
                  <label class="vendor_form-label">Role</label>
                  <input v-model="contact.role" class="vendor_input" placeholder="Contact Role" />
                </div>
                <div class="vendor_checkbox-container">
                  <input type="checkbox" v-model="contact.isPrimary" class="vendor_checkbox" />
                  <label class="vendor_form-label">Primary Contact</label>
                </div>
                <div class="vendor_contact-actions">
                  <button class="vendor_btn vendor_btn-primary vendor_btn-sm" @click="vendor_saveContact(contact.id)">Save</button>
                  <button class="vendor_btn vendor_btn-outline vendor_btn-sm" @click="vendor_cancelEditContact(contact.id)">Cancel</button>
                </div>
              </div>

              <!-- View Mode -->
              <div v-else class="vendor_contact-info">
                <div class="vendor_flex vendor_items-center vendor_gap-2 vendor_mb-1">
                  <h4 class="vendor_contact-name">{{ contact.name }}</h4>
                  <span v-if="contact.isPrimary" class="vendor_badge vendor_badge-secondary">Primary</span>
                </div>
                <p class="vendor_contact-details">
                  {{ contact.email }} • {{ contact.phone }}
                </p>
                <p class="vendor_contact-role">
                  {{ contact.role }}
                </p>
                <div class="vendor_contact-actions">
                  <button 
                    class="vendor_btn vendor_btn-ghost vendor_btn-sm" 
                    @click="vendor_editContact(contact.id)" 
                    aria-label="Edit contact"
                    title="Edit contact"
                  >
                    <svg class="vendor_h-4 vendor_w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </button>
                  <button 
                    class="vendor_btn vendor_btn-ghost vendor_btn-sm" 
                    @click="vendor_removeContact(contact.id)" 
                    aria-label="Delete contact"
                    title="Delete contact"
                  >
                    <svg class="vendor_h-4 vendor_w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Documents Tab -->
      <div v-if="vendor_activeTab === 'documents'" class="vendor_tabs-content">
        <div class="vendor_card">
          <div class="vendor_card-header">
            <div class="vendor_flex vendor_items-center vendor_justify-between">
              <h3 class="vendor_card-title">Vendor Documents</h3>
              <button 
                class="vendor_btn vendor_btn-primary" 
                @click="vendor_addDocument"
                title="Upload new document"
              >
                <svg class="vendor_h-4 vendor_w-4 vendor_mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/>
                </svg>
                Upload Document
              </button>
            </div>
          </div>
          <div class="vendor_card-content vendor_space-y-4">
            <div v-if="vendor_documents.length === 0" class="vendor_no-documents">
              <div class="vendor_no-documents-icon">
                <svg class="vendor_w-16 vendor_h-16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h3 class="vendor_no-documents-title">No Documents Added</h3>
              <p class="vendor_no-documents-text">Click "Upload Document" to add your first vendor document.</p>
            </div>
            <div v-for="doc in vendor_documents" :key="doc.id" class="vendor_document-card">
              <!-- Editing Mode -->
              <div v-if="doc.isEditing" class="vendor_form-grid" style="grid-template-columns: 1fr;">
                <div class="vendor_form-item">
                  <label class="vendor_form-label">Document Name</label>
                  <input v-model="doc.name" class="vendor_input" placeholder="Document Name" />
                </div>
                <div class="vendor_form-item">
                  <label class="vendor_form-label">Document Type</label>
                  <select v-model="doc.type" class="vendor_select">
                    <option value="">Select type</option>
                    <option value="License">License</option>
                    <option value="Certificate">Certificate</option>
                    <option value="Contract">Contract</option>
                    <option value="Insurance">Insurance</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
                <div class="vendor_form-item">
                  <label class="vendor_form-label">Version</label>
                  <input v-model="doc.version" class="vendor_input" placeholder="1.0" />
                </div>
                <div class="vendor_form-item">
                  <label class="vendor_form-label">Status</label>
                  <select v-model="doc.status" class="vendor_select">
                    <option value="Pending">Pending</option>
                    <option value="Approved">Approved</option>
                    <option value="Rejected">Rejected</option>
                    <option value="Expired">Expired</option>
                  </select>
                </div>
                <div class="vendor_form-item">
                  <label class="vendor_form-label">Expiry Date</label>
                  <input v-model="doc.expiryDate" class="vendor_input" type="date" />
                </div>
                <div class="vendor_form-item">
                  <label class="vendor_form-label">File Upload</label>
                  <input 
                    type="file" 
                    class="vendor_input" 
                    @change="vendor_handleFileUpload($event, doc.id)"
                    accept=".pdf,.doc,.docx,.txt,.jpg,.jpeg,.png,.xlsx,.xls"
                  />
                  <div v-if="doc.fileName" class="vendor_file-info">
                    <small>Selected: {{ doc.fileName }}</small>
                  </div>
                </div>
                <div class="vendor_document-actions">
                  <button class="vendor_btn vendor_btn-primary vendor_btn-sm" @click="vendor_saveDocument(doc.id)">Save</button>
                  <button class="vendor_btn vendor_btn-outline vendor_btn-sm" @click="vendor_cancelEditDocument(doc.id)">Cancel</button>
                </div>
              </div>

              <!-- View Mode -->
              <div v-else class="vendor_document-info">
                <div class="vendor_flex vendor_items-center vendor_gap-2 vendor_mb-1">
                  <h4 class="vendor_document-name">{{ doc.name || doc.document_name }}</h4>
                  <span class="vendor_badge" :class="vendor_getDocumentStatusClass(doc.status)">
                    {{ doc.status }}
                  </span>
                  <span v-if="doc.s3_url || doc.s3_file_id" class="vendor_badge vendor_badge-success">Uploaded</span>
                  <span v-else class="vendor_badge vendor_badge-warning">Not Uploaded</span>
                </div>
                <p class="vendor_document-details">
                  {{ doc.type || doc.document_type }} • Version {{ doc.version || 'N/A' }}
                </p>
                <p class="vendor_document-meta">
                  Expires: {{ doc.expiryDate || doc.expiry_date || 'No expiry date' }}
                </p>
                <p v-if="doc.fileSize" class="vendor_document-meta">
                  File Size: {{ (doc.fileSize / 1024 / 1024).toFixed(2) }} MB
                </p>
                <p v-if="doc.s3_file_id" class="vendor_document-meta">
                  S3 File ID: {{ doc.s3_file_id }}
                </p>
                <div class="vendor_document-actions">
                  <button 
                    v-if="doc.s3_url" 
                    class="vendor_btn vendor_btn-ghost vendor_btn-sm" 
                    @click="vendor_viewDocument(doc.id)" 
                    aria-label="View document"
                    title="View document"
                  >
                    <svg class="vendor_h-4 vendor_w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  </button>
                  <button 
                    v-if="doc.s3_url" 
                    class="vendor_btn vendor_btn-ghost vendor_btn-sm" 
                    @click="vendor_downloadDocument(doc.id)" 
                    aria-label="Download document"
                    title="Download document"
                  >
                    <svg class="vendor_h-4 vendor_w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </button>
                  <button 
                    class="vendor_btn vendor_btn-ghost vendor_btn-sm" 
                    @click="vendor_editDocument(doc.id)" 
                    aria-label="Edit document"
                    title="Edit document"
                  >
                    <svg class="vendor_h-4 vendor_w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </button>
                  <button 
                    class="vendor_btn vendor_btn-ghost vendor_btn-sm" 
                    @click="vendor_removeDocument(doc.id)" 
                    aria-label="Delete document"
                    title="Delete document"
                  >
                    <svg class="vendor_h-4 vendor_w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <!-- Lifecycle Tab -->
      <div v-if="vendor_activeTab === 'lifecycle'" class="vendor_tabs-content">
        <div class="vendor_card">
          <div class="vendor_card-header">
            <h3 class="vendor_card-title">Vendor Lifecycle Timeline</h3>
            <p class="vendor_card-subtitle">Track your vendor onboarding progress through different stages</p>
          </div>
          <div class="vendor_card-content">
            <div v-if="vendor_formData.lifecycle_data" class="vendor_lifecycle-container">
              <!-- Current Stage -->
              <div class="vendor_current-stage">
                <h4 class="vendor_current-stage-title">Current Stage</h4>
                <div class="vendor_stage-card vendor_stage-current">
                  <div class="vendor_stage-header">
                    <div class="vendor_stage-icon">
                      <svg class="vendor_w-6 vendor_h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                    <div class="vendor_stage-info">
                      <h5 class="vendor_stage-name">{{ vendor_formData.lifecycle_data.current_stage.stage_name }}</h5>
                      <p class="vendor_stage-code">{{ vendor_formData.lifecycle_data.current_stage.stage_code }}</p>
                      <p v-if="vendor_formData.lifecycle_data.current_stage.description" class="vendor_stage-description">
                        {{ vendor_formData.lifecycle_data.current_stage.description }}
                      </p>
                    </div>
                    <div class="vendor_stage-status">
                      <span class="vendor_badge vendor_badge-primary">IN PROGRESS</span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Timeline -->
              <div class="vendor_timeline">
                <h4 class="vendor_timeline-title">Stage-wise progression through vendor onboarding process</h4>
                <div class="vendor_timeline-container">
                  <div v-for="(entry, index) in vendor_formData.lifecycle_data.tracker_entries" :key="entry.stage_id" class="vendor_timeline-item">
                    <div class="vendor_timeline-marker" :class="{ 'vendor_timeline-marker-current': entry.is_current, 'vendor_timeline-marker-completed': entry.ended_at }">
                      <svg v-if="entry.ended_at" class="vendor_w-4 vendor_h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                      </svg>
                      <svg v-else class="vendor_w-4 vendor_h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                    <div class="vendor_timeline-content">
                      <div class="vendor_timeline-stage">
                        <h6 class="vendor_timeline-stage-name">{{ entry.stage_name }}</h6>
                        <span class="vendor_timeline-stage-code">{{ entry.stage_code }}</span>
                      </div>
                      <div class="vendor_timeline-dates">
                        <p class="vendor_timeline-date">
                          <strong>Started:</strong> {{ vendor_formatDate(entry.started_at) }}
                        </p>
                        <p v-if="entry.ended_at" class="vendor_timeline-date">
                          <strong>Completed:</strong> {{ vendor_formatDate(entry.ended_at) }}
                        </p>
                        <p v-else class="vendor_timeline-date vendor_timeline-date-current">
                          <strong>Status:</strong> In Progress
                        </p>
                      </div>
                      <div v-if="entry.is_current" class="vendor_timeline-actions">
                        <button class="vendor_btn vendor_btn-primary vendor_btn-sm">
                          <svg class="vendor_w-4 vendor_h-4 vendor_mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          Approval Required
                        </button>
                        <button class="vendor_btn vendor_btn-outline vendor_btn-sm">
                          <svg class="vendor_w-4 vendor_h-4 vendor_mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          Max: 7 days
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="vendor_no-lifecycle-data">
              <div class="vendor_no-lifecycle-icon">
                <svg class="vendor_w-16 vendor_h-16" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 class="vendor_no-lifecycle-title">No Lifecycle Data Available</h3>
              <p class="vendor_no-lifecycle-text">Lifecycle tracking information will appear here once your vendor registration is processed.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Document View Modal -->
  <div v-if="vendor_showDocumentModal" class="vendor_document-modal-overlay" @click="vendor_closeDocumentModal">
    <div class="vendor_document-modal-content" @click.stop>
      <div class="vendor_document-modal-header">
        <h3 class="vendor_document-modal-title">{{ vendor_currentDocumentName }}</h3>
        <button class="vendor_document-modal-close" @click="vendor_closeDocumentModal">
          <svg class="vendor_w-6 vendor_h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      <div class="vendor_document-modal-body">
        <iframe 
          :src="vendor_currentDocumentUrl" 
          class="vendor_document-iframe"
          frameborder="0"
          allowfullscreen>
        </iframe>
      </div>
    </div>
  </div>

  <!-- Popup Modal -->
  <PopupModal />
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import PopupModal from '@/popup/PopupModal.vue'
import { PopupService } from '@/popup/popupService'

import { useNotifications } from '@/composables/useNotifications'
import notificationService from '@/services/notificationService'
import loggingService from '@/services/loggingService'
import { useAuthStore } from '@/stores/auth_vendor'
import { useVendorPermissions } from '@/composables/useVendorPermissions'
import { getTprmApiUrl } from '@/utils/backendEnv'

const { showSuccess, showError, showWarning, showInfo } = useNotifications()
// Initialize router and auth store
const router = useRouter()
const authStore = useAuthStore()

// API base URL for vendor-core endpoints
const VENDOR_CORE_API_BASE_URL = getTprmApiUrl('vendor-core')

// Initialize RBAC permissions
const { permissions, canPerformAction, showDeniedAlert } = useVendorPermissions()

const vendor_activeTab = ref('company-info')
const vendor_isToggleActive = ref(false)

// Form data structure matching the backend model - all fields clear by default
const vendor_formData = reactive({
  vendor_code: '',
  company_name: '',
  legal_name: '',
  business_type: '',
  tax_id: '',
  duns_number: '',
  incorporation_date: '',
  industry_sector: '',
  website: '',
  annual_revenue: null,
  employee_count: null,
  headquarters_address: '',
  vendor_category: '',
  risk_level: '',
  status: 'pending',
  is_critical_vendor: false,
  has_data_access: false,
  has_system_access: false,
  description: '',
  temp_vendor_id: null,  // Store temp vendor ID for document uploads
  user_id: null,  // Store user ID
  lifecycle_data: null,
  user_role: null,  // Store user role from RBAC
  user_rbac_permissions: null  // Store user RBAC permissions
})

// Loading states
const vendor_isSubmitting = ref(false)
const vendor_submitSuccess = ref(false)
const vendor_submitError = ref('')
const vendor_screeningStatus = ref(null)
const vendor_isLoadingUserData = ref(false)
const vendor_noVendorInfo = ref(false)

const vendor_tabs = [
  { id: 'company-info', label: 'Company Info' },
  { id: 'legal-financial', label: 'Legal & Financial' },
  { id: 'category-risk', label: 'Category & Risk' },
  { id: 'contacts', label: 'Contacts' },
  { id: 'documents', label: 'Documents' },
  { id: 'lifecycle', label: 'Lifecycle' }
]

const vendor_contacts = ref([])

const vendor_documents = ref([])

// Document modal state
const vendor_showDocumentModal = ref(false)
const vendor_currentDocumentUrl = ref('')
const vendor_currentDocumentName = ref('')

// Toggle tab state
const vendor_toggleActiveTab = ref('overview')

// Check if vendor has already registered (lifecycle stage not equal to 1 AND user role is "vendor")
const vendor_hasAlreadyRegistered = computed(() => {
  if (!vendor_formData.lifecycle_data) return false
  
  const currentStage = vendor_formData.lifecycle_data.current_stage?.stage_id
  const userRole = vendor_formData.user_role
  
  // Check if user has "vendor" role (case-insensitive) AND lifecycle_stage is not 1
  const isVendorRole = userRole && userRole.toLowerCase() === 'vendor'
  const hasCompletedRegistration = currentStage && currentStage !== 1
  
  console.log('Checking registration status:', {
    currentStage,
    userRole,
    isVendorRole,
    hasCompletedRegistration,
    shouldShowAlreadyRegistered: isVendorRole && hasCompletedRegistration
  })
  
  return isVendorRole && hasCompletedRegistration
})

// Computed property to check if form has been submitted
const vendor_isFormSubmitted = computed(() => {
  // Only consider form submitted if lifecycle stage is beyond initial registration (stage 1)
  // AND user has vendor role (meaning they've completed registration)
  if (vendor_hasAlreadyRegistered.value) return true
  
  // Check RFP response submission status - only consider submitted if explicitly submitted/approved/rejected
  if (vendor_formData.rfp_response_data?.submission_status) {
    const submissionStatus = vendor_formData.rfp_response_data.submission_status.toLowerCase()
    // Only consider submitted if status is explicitly submitted, approved, rejected, etc.
    // Allow draft and pending statuses
    const submittedStatuses = ['submitted', 'approved', 'rejected', 'awarded', 'shortlisted', 'under_evaluation', 'accepted']
    if (submittedStatuses.includes(submissionStatus)) {
      return true
    }
  }
  
  // Check temp_vendor status - only consider submitted if explicitly submitted/approved/rejected
  if (vendor_formData.status) {
    const status = vendor_formData.status.toLowerCase()
    // Only consider submitted if status is explicitly submitted, approved, rejected, etc.
    // Allow draft and pending statuses
    const submittedStatuses = ['submitted', 'approved', 'rejected', 'active', 'inactive', 'suspended']
    if (submittedStatuses.includes(status)) {
      return true
    }
  }
  
  return false
})

// Computed property for data count (prioritize RFP response data)
const vendor_dataCount = computed(() => {
  let count = 0
  const r = vendor_formData.rfp_response_data || {}
  
  // Count company info fields from response_documents.companyInfo
  if (r.response_documents && r.response_documents.companyInfo) {
    const companyInfo = r.response_documents.companyInfo
    const companyFields = ['companyName', 'contactName', 'email', 'phone', 'businessType', 'annualRevenue', 'employeeCount', 'legalName', 'taxId', 'dunsNumber', 'industrySector']
    companyFields.forEach(field => {
      if (companyInfo[field] && companyInfo[field] !== '') count++
    })
  }
  
  // Count main RFP response fields
  const mainFields = ['submission_date', 'proposed_value', 'evaluation_status', 'submission_status', 'completion_percentage']
  mainFields.forEach(field => {
    if (r[field] !== undefined && r[field] !== null && r[field] !== '') count++
  })
  
  // Count document_urls entries
  if (r.document_urls && typeof r.document_urls === 'object') {
    count += Object.keys(r.document_urls).length
  }
  
  return count
})

// Toggle function
const vendor_toggleView = async () => {
  vendor_isToggleActive.value = !vendor_isToggleActive.value
  
  // If toggling to data view, fetch user data
  if (vendor_isToggleActive.value) {
    await vendor_fetchUserData()
  }
}

// Refresh user data function
const vendor_refreshUserData = async () => {
  console.log('Refreshing user data...')
  await vendor_fetchUserData()
}

// Fetch user data based on UserId
const vendor_fetchUserData = async () => {
  vendor_isLoadingUserData.value = true
  
  try {
    // Get UserId from localStorage with fallbacks
    const userId = vendor_getUserIdFromStorage()
    
    if (!userId) {
      console.warn('No user ID found in localStorage or auth store')
      console.log('Available localStorage keys:', Object.keys(localStorage))
      console.log('current_user:', localStorage.getItem('current_user'))
  console.log('user:', localStorage.getItem('current_user') || localStorage.getItem('user'))
      PopupService.warning('No user session found. Please log in again.', 'Session Error')
      return
    }
    
    console.log('Fetching user data for userId:', userId)
    
    // Get auth headers for API requests
    const token = localStorage.getItem('session_token')
    const headers = {}
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
    
    // Use correct API endpoint: /api/tprm/vendor-core/ (not /api/v1/vendor-core/)
    const response = await fetch(`${VENDOR_CORE_API_BASE_URL}/temp-vendors/get_user_data/?user_id=${userId}`, {
      headers
    })
    
    // Check if response is OK or if it's a 404 (no data found - this is normal for new users)
    if (!response.ok && response.status === 404) {
      // 404 means no existing data - set flag to show "no vendor information" message
      console.log('No existing registration data found (HTTP 404). Setting no vendor info flag.')
      vendor_noVendorInfo.value = true
      vendor_isLoadingUserData.value = false
      return
    }
    
    // Check if response is OK
    if (!response.ok) {
      const errorResult = await response.json()
      console.error('Failed to fetch user data:', errorResult)
      
      // Check if this is a "no data found" scenario
      const isNoDataError = errorResult.message && (
        errorResult.message.includes('No vendor') || 
        errorResult.message.includes('No RFP response') ||
        errorResult.message.includes('not found')
      )
      
      if (isNoDataError) {
        // User hasn't started registration yet - set flag to show "no vendor information" message
        console.log('No existing registration data found. Setting no vendor info flag.')
        vendor_noVendorInfo.value = true
      } else {
        // Actual error occurred
        PopupService.error('Error: ' + (errorResult.message || 'Failed to load data'), 'User Data Error')
        await showError('Data Load Error', 'Failed to load your vendor registration data. Please try again.', {
          action: 'vendor_data_load_error',
          user_id: userId,
          error_message: errorResult.message
        })
      }
      vendor_isLoadingUserData.value = false
      return
    }
    
    const result = await response.json()
    
    if (result.status === 'success' || result.status === 'partial_success') {
      // Data found - reset the no vendor info flag
      vendor_noVendorInfo.value = false
      
      // Store temp_vendor ID if available
      if (result.data.temp_vendor && result.data.temp_vendor.id) {
        vendor_formData.temp_vendor_id = result.data.temp_vendor.id
        console.log('Stored temp vendor ID:', vendor_formData.temp_vendor_id)
        
        // Populate form data with temp_vendor data
        const tempVendor = result.data.temp_vendor
        vendor_populateFormFromTempVendor(tempVendor)
      }
      
      // Also populate RFP response data if available
      if (result.data.rfp_response) {
        const rfpResponse = result.data.rfp_response
        
        // Log detailed RFP response data for debugging
        console.log('RFP Response Data:', rfpResponse)
        console.log('Response Documents:', rfpResponse.response_documents)
        console.log('Document URLs:', rfpResponse.document_urls)
        
        // Update form data with RFP response data if vendor data is missing
        if (rfpResponse.vendor_name && !vendor_formData.company_name) {
          vendor_formData.company_name = rfpResponse.vendor_name
          console.log('Updated company name from RFP response:', rfpResponse.vendor_name)
        }
        
        if (rfpResponse.contact_email && !vendor_formData.website) {
          console.log('RFP Contact Email available:', rfpResponse.contact_email)
        }
        
        // Parse JSON fields if they're strings
        if (typeof rfpResponse.response_documents === 'string') {
          try {
            rfpResponse.response_documents = JSON.parse(rfpResponse.response_documents)
          } catch (e) {
            console.error('Error parsing response_documents:', e)
          }
        }
        
        if (typeof rfpResponse.document_urls === 'string') {
          try {
            rfpResponse.document_urls = JSON.parse(rfpResponse.document_urls)
          } catch (e) {
            console.error('Error parsing document_urls:', e)
          }
        }
        
        // Store RFP response for reference
        vendor_formData.rfp_response_data = rfpResponse
        console.log('RFP response data stored in form data')
      } else {
        console.log('No RFP response data found')
      }
      
      // Store lifecycle data if available
      if (result.data.lifecycle) {
        vendor_formData.lifecycle_data = result.data.lifecycle
        console.log('Lifecycle data stored:', result.data.lifecycle)
      } else {
        console.log('No lifecycle data found')
      }
      
      // Store user role and RBAC permissions
      if (result.data.user_role) {
        vendor_formData.user_role = result.data.user_role
        console.log('User role stored:', result.data.user_role)
      }
      
      if (result.data.user_rbac_permissions) {
        vendor_formData.user_rbac_permissions = result.data.user_rbac_permissions
        console.log('User RBAC permissions stored:', result.data.user_rbac_permissions)
      }
      
      console.log('User data loaded successfully:', result.data)
      
      // Show success notification only if data was found
      if (result.data.temp_vendor || result.data.rfp_response || result.data.lifecycle) {
        await showInfo('Data Loaded', 'Your vendor registration data has been loaded successfully.', {
          action: 'vendor_data_loaded',
          user_id: userId,
          has_temp_vendor: !!result.data.temp_vendor,
          has_rfp_response: !!result.data.rfp_response
        })
      }
    }
  } catch (error) {
    console.error('Error fetching user data:', error)
    PopupService.error('Error fetching user data: ' + error.message, 'Loading Error')
    
    // Show error notification
    await showError('Network Error', 'Failed to connect to the server. Please check your connection and try again.', {
      action: 'vendor_data_network_error',
      error_message: error.message
    })
  } finally {
    vendor_isLoadingUserData.value = false
  }
}

// Populate form data from temp_vendor record
const vendor_populateFormFromTempVendor = (tempVendor) => {
  console.log('Populating form data from temp_vendor:', tempVendor)
  
  // Map temp_vendor fields to form data
  if (tempVendor.vendor_code) vendor_formData.vendor_code = tempVendor.vendor_code
  if (tempVendor.company_name) vendor_formData.company_name = tempVendor.company_name
  if (tempVendor.legal_name) vendor_formData.legal_name = tempVendor.legal_name
  if (tempVendor.business_type) vendor_formData.business_type = tempVendor.business_type
  if (tempVendor.tax_id) vendor_formData.tax_id = tempVendor.tax_id
  if (tempVendor.duns_number) vendor_formData.duns_number = tempVendor.duns_number
  if (tempVendor.incorporation_date) vendor_formData.incorporation_date = tempVendor.incorporation_date
  if (tempVendor.industry_sector) vendor_formData.industry_sector = tempVendor.industry_sector
  if (tempVendor.website) vendor_formData.website = tempVendor.website
  if (tempVendor.annual_revenue) vendor_formData.annual_revenue = tempVendor.annual_revenue
  if (tempVendor.employee_count) vendor_formData.employee_count = tempVendor.employee_count
  if (tempVendor.headquarters_address) vendor_formData.headquarters_address = tempVendor.headquarters_address
  if (tempVendor.vendor_category) vendor_formData.vendor_category = tempVendor.vendor_category
  if (tempVendor.risk_level) vendor_formData.risk_level = tempVendor.risk_level
  if (tempVendor.status) vendor_formData.status = tempVendor.status
  if (tempVendor.is_critical_vendor !== undefined) vendor_formData.is_critical_vendor = tempVendor.is_critical_vendor
  if (tempVendor.has_data_access !== undefined) vendor_formData.has_data_access = tempVendor.has_data_access
  if (tempVendor.has_system_access !== undefined) vendor_formData.has_system_access = tempVendor.has_system_access
  if (tempVendor.description) vendor_formData.description = tempVendor.description
  
  // Populate contacts if available
  if (tempVendor.contacts && Array.isArray(tempVendor.contacts)) {
    vendor_contacts.value = tempVendor.contacts.map(contact => ({
      ...contact,
      isEditing: false // Ensure contacts are in view mode
    }))
  }
  
  // Populate documents if available
  if (tempVendor.documents && Array.isArray(tempVendor.documents)) {
    vendor_documents.value = tempVendor.documents.map(doc => ({
      ...doc,
      isEditing: false // Ensure documents are in view mode
    }))
  }
  
  console.log('Form data populated successfully from temp_vendor')
}

const vendor_addContact = () => {
  // Always allow adding contacts during registration
  // This is part of filling out the registration form - no permission check needed
  const vendor_newContact = {
    id: Date.now().toString(),
    name: "New Contact",
    email: "contact@example.com",
    phone: "+1-555-0000",
    role: "Contact",
    isPrimary: false,
    isEditing: true
  }
  vendor_contacts.value.push(vendor_newContact)
}

const vendor_removeContact = (id) => {
  // Always allow removing contacts during registration
  vendor_contacts.value = vendor_contacts.value.filter(vendor_contact => vendor_contact.id !== id)
}

const vendor_editContact = (id) => {
  // Always allow editing contacts during registration
  const contact = vendor_contacts.value.find(c => c.id === id)
  if (contact) {
    contact.isEditing = true
  }
}

const vendor_saveContact = (id) => {
  const contact = vendor_contacts.value.find(c => c.id === id)
  if (contact) {
    contact.isEditing = false
  }
}

const vendor_cancelEditContact = (id) => {
  const contact = vendor_contacts.value.find(c => c.id === id)
  if (contact) {
    contact.isEditing = false
    // If it's a new contact that was never saved, remove it
    if (contact.name === "New Contact" && contact.email === "contact@example.com") {
      vendor_removeContact(id)
    }
  }
}

const vendor_addDocument = () => {
  // Always allow adding documents during registration
  // This is part of filling out the registration form - no permission check needed
  const vendor_newDocument = {
    id: Date.now().toString(),
    name: "New Document.pdf",
    type: "Document",
    version: "1.0",
    status: "Pending",
    expiryDate: "",
    isEditing: true,
    file: null
  }
  vendor_documents.value.push(vendor_newDocument)
}

const vendor_removeDocument = (id) => {
  // Always allow removing documents during registration
  vendor_documents.value = vendor_documents.value.filter(vendor_doc => vendor_doc.id !== id)
}

const vendor_editDocument = (id) => {
  // Always allow editing documents during registration
  const document = vendor_documents.value.find(d => d.id === id)
  if (document) {
    document.isEditing = true
  }
}

const vendor_saveDocument = async (id) => {
  const document = vendor_documents.value.find(d => d.id === id)
  if (!document) return
  
  // If it's a new document with a file, upload it
  if (document.file && !document.s3_url) {
    try {
      const formData = new FormData()
      formData.append('file', document.file)
      formData.append('document_name', document.name)
      formData.append('document_type', document.type)
      formData.append('version', document.version)
      formData.append('status', document.status)
      formData.append('expiry_date', document.expiryDate || '')
      
      // Send temp_vendor_id if available, otherwise send user_id
      if (vendor_formData.temp_vendor_id) {
        formData.append('vendor_id', vendor_formData.temp_vendor_id.toString())
      }
      formData.append('user_id', vendor_formData.user_id.toString())
      
      const token = localStorage.getItem('session_token')
      const response = await fetch(`${VENDOR_CORE_API_BASE_URL}/temp-vendors/upload_document/`, {
        method: 'POST',
        body: formData,
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      })
      
      const result = await response.json()
      
      if (result.status === 'success') {
        // Update document with S3 info
        document.s3_url = result.data.s3_url
        document.file_size = result.data.upload_info.file_size
        document.s3_file_id = result.data.s3_file_id
        document.id = result.data.s3_file_id // Update with real ID from database
        
        document.isEditing = false
        
        // Show success message
        console.log('Document uploaded successfully:', result.data)
      } else {
        PopupService.error('Error uploading document: ' + result.message, 'Upload Failed')
        return
      }
    } catch (error) {
      console.error('Upload error:', error)
      PopupService.error('Error uploading document: ' + error.message, 'Upload Error')
      return
    }
  } else {
    // Just save the document info without uploading
    document.isEditing = false
  }
}

const vendor_cancelEditDocument = (id) => {
  const document = vendor_documents.value.find(d => d.id === id)
  if (document) {
    document.isEditing = false
    // If it's a new document that was never saved, remove it
    if (document.name === "New Document.pdf" && document.type === "Document") {
      vendor_removeDocument(id)
    }
  }
}

const vendor_handleFileUpload = async (event, documentId) => {
  // Always allow uploading files during registration
  // No permission check needed - this is part of filling out the form
  
  const file = event.target.files[0]
  const document = vendor_documents.value.find(d => d.id === documentId)
  
  if (file && document) {
    // Validate file size (max 100MB)
    const maxSize = 100 * 1024 * 1024 // 100MB
    if (file.size > maxSize) {
      PopupService.warning('File size cannot exceed 100MB', 'File Too Large')
      // Create warning notification
      await notificationService.createVendorWarningNotification('file_too_large', {
        title: 'File Too Large',
        message: 'File size cannot exceed 100MB'
      })
      event.target.value = ''
      return
    }
    
    // Validate file type
    const allowedTypes = ['pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png', 'xlsx', 'xls']
    const fileExtension = file.name.split('.').pop().toLowerCase()
    
    if (!allowedTypes.includes(fileExtension)) {
      PopupService.warning(`File type not allowed. Allowed types: ${allowedTypes.join(', ')}`, 'Invalid File Type')
      event.target.value = ''
      return
    }
    
    // Update document with file info
    document.file = file
    document.fileName = file.name
    document.fileSize = file.size
    
    // Auto-update document name if it's still the default
    if (document.name === "New Document.pdf") {
      document.name = file.name
    }
  }
}

const vendor_viewDocument = (id) => {
  const document = vendor_documents.value.find(d => d.id === id)
  if (document) {
    if (document.s3_url) {
      // Open S3 URL in new tab for viewing
      window.open(document.s3_url, '_blank')
    } else {
      const docName = document.name || document.document_name
      const docType = document.type || document.document_type
      PopupService.warning(`Document not uploaded yet: ${docName}\nType: ${docType}\nVersion: ${document.version}\nStatus: ${document.status}`, 'Document Not Available')
    }
  }
}

const vendor_downloadDocument = (id) => {
  const document = vendor_documents.value.find(d => d.id === id)
  if (document) {
    if (document.s3_url) {
      // Create a temporary link to download the file
      const link = document.createElement('a')
      link.href = document.s3_url
      link.download = document.name || document.document_name
      link.target = '_blank'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    } else {
      const docName = document.name || document.document_name
      PopupService.warning(`Document not uploaded yet: ${docName}`, 'Document Not Available')
    }
  }
}

const vendor_getDocumentStatusClass = (status) => {
  switch (status) {
    case "Approved": return "vendor_badge-success"
    case "Pending": return "vendor_badge-warning"
    case "Rejected": return "vendor_badge-destructive"
    default: return "vendor_badge-default"
  }
}

// API submission functions
const vendor_submitRegistration = async () => {
  // Allow vendors to submit their own registration - no permission check needed
  // Permission checks are handled by the backend API
  
  vendor_isSubmitting.value = true
  vendor_submitError.value = ''
  vendor_submitSuccess.value = false
  
  try {
    // Prepare the complete registration data with proper data types
    const vendor_registrationData = {
      ...vendor_formData,
      // Ensure numeric fields are properly formatted or null if empty
      annual_revenue: vendor_formData.annual_revenue === '' || vendor_formData.annual_revenue === null ? null : Number(vendor_formData.annual_revenue),
      employee_count: vendor_formData.employee_count === '' || vendor_formData.employee_count === null ? null : Number(vendor_formData.employee_count),
      contacts: vendor_contacts.value,
      documents: vendor_documents.value
    }

    // Submit to backend API - include temp_vendor_id if available for update
    const submissionData = {
      ...vendor_registrationData
    }
    
    // Include temp_vendor_id if we have an existing record
    if (vendor_formData.temp_vendor_id) {
      submissionData.temp_vendor_id = vendor_formData.temp_vendor_id
      console.log('Submitting registration for existing temp vendor:', vendor_formData.temp_vendor_id)
    } else {
      console.log('Creating new vendor registration')
    }
    
    const token = localStorage.getItem('session_token')
    const headers = {
      'Content-Type': 'application/json'
    }
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
    
    const response = await fetch(`${VENDOR_CORE_API_BASE_URL}/temp-vendors/vendor_submit_registration/`, {
      method: 'POST',
      headers,
      body: JSON.stringify(submissionData)
    })
    
    const result = await response.json()
    
    if (response.ok && result.status === 'success') {
      vendor_submitSuccess.value = true
      vendor_submitError.value = ''
      
      // Store temp_vendor_id if this was a new record
      if (!vendor_formData.temp_vendor_id && result.data && result.data.id) {
        vendor_formData.temp_vendor_id = result.data.id
        console.log('Stored new temp vendor ID after submission:', vendor_formData.temp_vendor_id)
      }
      
      // Check if screening was completed and show notification
      if (result.data.screening_status === 'completed') {
        vendor_screeningStatus.value = {
          type: 'success',
          message: 'Vendor registration submitted successfully! External verification completed. You can view the results in the External Screening page.'
        }
        
        // Show success notification
        await showSuccess('Registration Submitted', 'Vendor registration submitted successfully! External verification completed.', {
          action: 'vendor_registration_submitted',
          vendor_code: vendor_formData.vendor_code,
          company_name: vendor_formData.company_name,
          screening_status: 'completed'
        })
        
        // Create notification service notifications
        await notificationService.createVendorRegistrationNotification('registration_submitted', {
          vendor_id: result.data.vendor_id,
          company_name: vendor_formData.company_name
        })
        
        await notificationService.createVendorScreeningNotification('screening_passed', {
          vendor_id: result.data.vendor_id,
          vendor_name: vendor_formData.company_name
        })
        
        console.log('Registration successful with screening:', result.data.screening_results)
      } else if (result.data.screening_status === 'failed') {
        vendor_screeningStatus.value = {
          type: 'warning',
          message: 'Vendor registration submitted successfully! However, external verification failed. Please check the External Screening page for manual review.'
        }
        
        // Show warning notification
        await showWarning('Registration Submitted with Issues', 'Vendor registration submitted successfully! However, external verification failed. Please check the External Screening page for manual review.', {
          action: 'vendor_registration_submitted_with_issues',
          vendor_code: vendor_formData.vendor_code,
          company_name: vendor_formData.company_name,
          screening_status: 'failed'
        })
        
        // Create notification service notifications
        await notificationService.createVendorRegistrationNotification('registration_submitted', {
          vendor_id: result.data.vendor_id,
          company_name: vendor_formData.company_name
        })
        
        await notificationService.createVendorScreeningNotification('screening_failed', {
          vendor_id: result.data.vendor_id,
          vendor_name: vendor_formData.company_name,
          reason: 'External verification checks failed'
        })
        
        console.log('Registration successful but screening failed:', result)
      } else {
        vendor_screeningStatus.value = {
          type: 'success',
          message: 'Vendor registration submitted successfully!'
        }
        
        // Show success notification
        await showSuccess('Registration Submitted', 'Vendor registration submitted successfully!', {
          action: 'vendor_registration_submitted',
          vendor_code: vendor_formData.vendor_code,
          company_name: vendor_formData.company_name,
          screening_status: 'pending'
        })
        
        // Create notification service notification
        await notificationService.createVendorRegistrationNotification('registration_submitted', {
          vendor_id: result.data.vendor_id,
          company_name: vendor_formData.company_name
        })
        
        console.log('Registration successful:', result)
      }
      
      // Auto-hide notification after 10 seconds
      setTimeout(() => {
        vendor_screeningStatus.value = null
      }, 10000)
      
      // Optionally redirect or reset form
      // vendor_resetForm()
    } else {
      vendor_submitError.value = result.message || result.error_details || 'Failed to submit registration'
      console.error('Registration failed:', result)
      
      // Show error notification
      await showError('Registration Failed', 'Failed to submit vendor registration. Please try again.', {
        action: 'vendor_registration_failed',
        vendor_code: vendor_formData.vendor_code,
        company_name: vendor_formData.company_name,
        error_message: vendor_submitError.value
      })
      
      // Create error notification
      await notificationService.createVendorErrorNotification('submit_registration', vendor_submitError.value, {
        title: 'Registration Failed',
        company_name: vendor_formData.company_name
      })
      
      PopupService.error('Error: ' + vendor_submitError.value, 'Registration Failed')
    }
    
  } catch (error) {
    vendor_submitError.value = `Network error: Could not submit registration - ${error.message}`
    console.error('Network/Submission error:', error)
    console.error('Error details:', {
      message: error.message,
      stack: error.stack,
      name: error.name
    })
    
    // Show error notification
    await showError('Submission Error', 'Network error: Could not submit registration. Please check your connection and try again.', {
      action: 'vendor_registration_network_error',
      vendor_code: vendor_formData.vendor_code,
      company_name: vendor_formData.company_name,
      error_message: error.message
    })
    
    // Create error notification
    await notificationService.createVendorErrorNotification('submit_registration', error.message, {
      title: 'Network Error',
      message: 'Could not submit registration. Please check your connection and try again.',
      company_name: vendor_formData.company_name
    })
    
    PopupService.error('Error: ' + vendor_submitError.value, 'Submission Error')
  } finally {
    vendor_isSubmitting.value = false
  }
}

const vendor_saveDraft = async () => {
  // Allow vendors to save their draft registration - no permission check needed
  // Permission checks are handled by the backend API
  
  vendor_isSubmitting.value = true
  vendor_submitError.value = ''
  
  try {
    // Prepare draft data (mark as draft status) with proper data types
    const vendor_draftData = {
      ...vendor_formData,
      // Ensure numeric fields are properly formatted or null if empty
      annual_revenue: vendor_formData.annual_revenue === '' || vendor_formData.annual_revenue === null ? null : Number(vendor_formData.annual_revenue),
      employee_count: vendor_formData.employee_count === '' || vendor_formData.employee_count === null ? null : Number(vendor_formData.employee_count),
      contacts: vendor_contacts.value,
      documents: vendor_documents.value,
      status: 'draft'
    }
    
    let response
    let result
    
    // Check if we have an existing temp_vendor_id to update
    if (vendor_formData.temp_vendor_id) {
      console.log('Updating existing temp vendor record:', vendor_formData.temp_vendor_id)
      
      // Use PUT to update existing record
      const token = localStorage.getItem('session_token')
      const headers = {
        'Content-Type': 'application/json'
      }
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }
      
      response = await fetch(`${VENDOR_CORE_API_BASE_URL}/temp-vendors/${vendor_formData.temp_vendor_id}/`, {
        method: 'PUT',
        headers,
        body: JSON.stringify(vendor_draftData)
      })
      
      result = await response.json()
      
      if (response.ok && result.status === 'success') {
        PopupService.success('Draft updated successfully!', 'Draft Updated')
        // Create notification
        await notificationService.createVendorRegistrationNotification('draft_updated', {
          vendor_id: vendor_formData.temp_vendor_id,
          company_name: vendor_formData.company_name
        })
      } else {
        PopupService.error('Error updating draft: ' + (result.message || 'Unknown error'), 'Update Failed')
        // Create error notification
        await notificationService.createVendorErrorNotification('update_draft', result.message || 'Unknown error', {
          title: 'Failed to Update Draft',
          company_name: vendor_formData.company_name
        })
      }
    } else {
      console.log('Creating new temp vendor record')
      
      // Use POST to create new record
      const token = localStorage.getItem('session_token')
      const headers = {
        'Content-Type': 'application/json'
      }
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }
      
      response = await fetch(`${VENDOR_CORE_API_BASE_URL}/temp-vendors/`, {
        method: 'POST',
        headers,
        body: JSON.stringify(vendor_draftData)
      })
      
      result = await response.json()
      
      if (response.ok && result.status === 'success') {
        // Store the new temp_vendor_id for future updates
        if (result.data && result.data.id) {
          vendor_formData.temp_vendor_id = result.data.id
          console.log('Stored new temp vendor ID:', vendor_formData.temp_vendor_id)
        }
        
        PopupService.success('Draft saved successfully!', 'Draft Saved')
        // Create notification
        await notificationService.createVendorRegistrationNotification('draft_saved', {
          vendor_id: result.data?.id || result.data?.vendor_id,
          company_name: vendor_formData.company_name
        })
      } else {
        PopupService.error('Error saving draft: ' + (result.message || 'Unknown error'), 'Save Failed')
        // Create error notification
        await notificationService.createVendorErrorNotification('save_draft', result.message || 'Unknown error', {
          title: 'Failed to Save Draft',
          company_name: vendor_formData.company_name
        })
      }
    }
    
  } catch (error) {
    PopupService.error('Network error: Could not save draft', 'Network Error')
    console.error('Draft save error:', error)
    // Create error notification
    await notificationService.createVendorErrorNotification('save_draft', error.message, {
      title: 'Network Error',
      message: 'Could not save draft. Please check your connection.',
      company_name: vendor_formData.company_name
    })
  } finally {
    vendor_isSubmitting.value = false
  }
}

const vendor_getCSRFToken = () => {
  // Get CSRF token from cookie or meta tag
  const name = 'csrftoken'
  let cookieValue = null
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';')
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim()
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1))
        break
      }
    }
  }
  return cookieValue || ''
}

// Utility functions
const vendor_formatDate = (dateString) => {
  if (!dateString) return 'Not provided'
  try {
    const date = new Date(dateString)
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString()
  } catch (error) {
    return 'Invalid date'
  }
}

const vendor_openDocument = (url) => {
  if (url) {
    window.open(url, '_blank')
  } else {
    PopupService.warning('No document URL available', 'Document Not Available')
  }
}

const vendor_openDocumentInModal = (url, name) => {
  if (url) {
    vendor_currentDocumentUrl.value = url
    vendor_currentDocumentName.value = name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
    vendor_showDocumentModal.value = true
  } else {
    PopupService.warning('No document URL available', 'Document Not Available')
  }
}

const vendor_closeDocumentModal = () => {
  vendor_showDocumentModal.value = false
  vendor_currentDocumentUrl.value = ''
  vendor_currentDocumentName.value = ''
}

const vendor_copyUrl = async (url) => {
  if (!url) {
    PopupService.warning('No URL to copy', 'No URL')
    return
  }
  
  try {
    await navigator.clipboard.writeText(url)
    PopupService.success('URL copied to clipboard', 'Copied')
  } catch (error) {
    // Fallback for browsers that don't support clipboard API
    const textArea = document.createElement('textarea')
    textArea.value = url
    document.body.appendChild(textArea)
    textArea.select()
    document.execCommand('copy')
    document.body.removeChild(textArea)
    PopupService.success('URL copied to clipboard', 'Copied')
  }
}

const vendor_downloadDocumentUrl = (url, filename) => {
  if (!url) {
    PopupService.warning('No document URL available', 'Document Not Available')
    return
  }
  
  try {
    // Create a temporary link to download the file
    const link = document.createElement('a')
    link.href = url
    link.download = filename || 'document'
    link.target = '_blank'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  } catch (error) {
    console.error('Error downloading document:', error)
    PopupService.error('Error downloading document: ' + error.message, 'Download Failed')
  }
}

const vendor_resetForm = () => {
  // Reset form to initial state
  Object.keys(vendor_formData).forEach(key => {
    if (typeof vendor_formData[key] === 'boolean') {
      vendor_formData[key] = false
    } else if (key === 'annual_revenue' || key === 'employee_count') {
      vendor_formData[key] = null
    } else if (key === 'status') {
      vendor_formData[key] = 'pending'
    } else {
      vendor_formData[key] = ''
    }
  })
  vendor_contacts.value = []
  vendor_documents.value = []
  vendor_activeTab.value = 'company-info'
}

// Clear old cached user data and force refresh
const vendor_clearCachedUserData = () => {
  // Clear localStorage to remove old cached user data
  localStorage.removeItem('current_user')
  localStorage.removeItem('isAuthenticated')
  
  // Force reinitialize the auth store with new user data
  authStore.initializeCurrentUser()
  
  console.log('Cleared cached user data')
}

// Helper function to ensure user data is available in localStorage
const vendor_ensureUserDataInStorage = () => {
  // Check if current_user exists in localStorage
  const currentUser = localStorage.getItem('current_user')
  if (!currentUser) {
    // If not, try to get from auth store and store it
    if (authStore.user) {
      localStorage.setItem('current_user', JSON.stringify(authStore.user))
      console.log('Stored user data from auth store to localStorage')
      return true
    }
    
    // If auth store doesn't have user, initialize it
    authStore.initializeCurrentUser()
    if (authStore.user) {
      localStorage.setItem('current_user', JSON.stringify(authStore.user))
      console.log('Initialized and stored user data to localStorage')
      return true
    }
  }
  return !!currentUser
}

// Simple function to get user ID from localStorage with fallbacks
const vendor_getUserIdFromStorage = () => {
  // Try different localStorage keys that might contain user data
  const userKeys = ['current_user', 'user']
  
  for (const key of userKeys) {
    const userData = localStorage.getItem(key)
    if (userData) {
      try {
        const parsedUser = JSON.parse(userData)
        // Check multiple possible user ID field names (case variations)
        const userId = parsedUser.id || parsedUser.userid || parsedUser.UserId || parsedUser.user_id || parsedUser.userId
        if (userId) {
          console.log(`Found user ID ${userId} in localStorage key: ${key}`)
          return userId
        }
      } catch (e) {
        console.warn(`Failed to parse user data from ${key}:`, e)
      }
    }
  }
  
  // Fallback to auth store
  if (authStore.user) {
    const userId = authStore.user.id || authStore.user.UserId || authStore.user.userId
    if (userId) {
      console.log('Using userId from auth store as fallback:', userId)
      return userId
    }
  }
  
  return null
}

// Navigate to lifecycle tracker for the current vendor
const vendor_viewProgress = () => {
  try {
    // Get the current vendor ID
    const vendorId = vendor_formData.temp_vendor_id
    
    if (!vendorId) {
      PopupService.warning('No vendor ID found. Please refresh your data and try again.', 'Navigation Error')
      return
    }
    
    console.log('Navigating to lifecycle tracker for vendor:', vendorId)
    
    // Navigate to the lifecycle tracker with vendor ID as query parameter
    router.push({
      name: 'VendorLifecycleTracker',
      query: {
        vendorId: vendorId,
        fromRegistration: 'true'
      }
    })
    
  } catch (error) {
    console.error('Error navigating to lifecycle tracker:', error)
    PopupService.error('Failed to navigate to lifecycle tracker. Please try again.', 'Navigation Error')
  }
}

// Test method to simulate different lifecycle stages (for development/testing)
const vendor_testLifecycleStage = (stage) => {
  if (!vendor_formData.lifecycle_data) {
    vendor_formData.lifecycle_data = {
      current_stage: {
        stage_id: stage,
        stage_name: `Stage ${stage}`,
        stage_code: `S${stage}`,
        description: `Test stage ${stage}`
      },
      tracker_entries: []
    }
  } else {
    vendor_formData.lifecycle_data.current_stage.stage_id = stage
    vendor_formData.lifecycle_data.current_stage.stage_name = `Stage ${stage}`
    vendor_formData.lifecycle_data.current_stage.stage_code = `S${stage}`
  }
  
  console.log(`Simulated lifecycle stage ${stage}. Has already registered:`, vendor_hasAlreadyRegistered.value)
}

// Initialize user session and load data on mount
onMounted(async () => {
  try {
    // Log page view
    await loggingService.logPageView('Vendor', 'Vendor Registration')
    
    // Ensure user data is available in localStorage
    const hasUserData = vendor_ensureUserDataInStorage()
    
    if (!hasUserData) {
      console.warn('Could not initialize user data')
      PopupService.warning('No user session found. Please log in to access your vendor registration data.', 'Session Required')
      return
    }
    
    // Get user ID from localStorage with fallbacks
    const userId = vendor_getUserIdFromStorage()
    
    if (userId) {
      vendor_formData.user_id = userId
      console.log('User ID set from localStorage/auth store:', userId)
      
      // Automatically load user data if available
      await vendor_fetchUserData()
    } else {
      console.warn('No user ID found in localStorage or auth store on mount')
      console.log('Available localStorage keys:', Object.keys(localStorage))
      console.log('current_user:', localStorage.getItem('current_user'))
      console.log('user:', localStorage.getItem('current_user') || localStorage.getItem('user'))
      PopupService.warning('No user session found. Please log in to access your vendor registration data.', 'Session Required')
    }
    
    // Expose test method to global scope for development/testing
    if (process.env.NODE_ENV === 'development') {
      window.testLifecycleStage = vendor_testLifecycleStage
      console.log('Test method exposed: window.testLifecycleStage(stage) - Use stages 1, 2, 3, etc.')
    }
  } catch (error) {
    console.error('Error during component initialization:', error)
  }
})
</script>

<style>
@import './VendorRegistration.css';

/* Fallback CSS variables in case they're not defined */
:root {
  --vendor_background: #ffffff;
  --vendor_foreground: #111827;
  --vendor_card: #ffffff;
  --vendor_border: #e5e7eb;
  --vendor_muted: #f9fafb;
  --vendor_muted-foreground: #6b7280;
  --vendor_primary: #3b82f6;
  --vendor_primary-foreground: #ffffff;
  --vendor_secondary: #6b7280;
  --vendor_secondary-foreground: #ffffff;
  --vendor_accent: #f3f4f6;
  --vendor_accent-foreground: #111827;
  --vendor_success: #22c55e;
  --vendor_success-foreground: #ffffff;
  --vendor_warning: #f59e0b;
  --vendor_warning-foreground: #ffffff;
  --vendor_destructive: #ef4444;
  --vendor_destructive-foreground: #ffffff;
  --vendor_radius: 0.5rem;
  --vendor_shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --vendor_shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
  --vendor_shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
}

/* Ensure basic visibility and styling */
.vendor_vendor-registration-container {
  max-width: 1200px !important;
  margin: 0 auto !important;
  padding: 2rem 1rem !important;
  min-height: 100vh !important;
  background-color: #ffffff !important;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
}

.vendor_registration-header {
  display: flex !important;
  align-items: center !important;
  justify-content: space-between !important;
  margin-bottom: 2rem !important;
  padding-bottom: 1rem !important;
  border-bottom: 1px solid #e5e7eb !important;
}

.vendor_registration-title {
  font-size: 2.5rem !important;
  font-weight: 700 !important;
  color: #111827 !important;
  margin: 0 !important;
}

.vendor_registration-subtitle {
  font-size: 1rem !important;
  color: #6b7280 !important;
  margin: 0.5rem 0 0 0 !important;
}

.vendor_action-buttons {
  display: flex !important;
  gap: 0.75rem !important;
  align-items: center !important;
}

.vendor_btn {
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  border-radius: 0.5rem !important;
  font-size: 0.875rem !important;
  font-weight: 500 !important;
  transition: all 0.2s ease !important;
  cursor: pointer !important;
  border: 1px solid transparent !important;
  padding: 0.5rem 1rem !important;
  height: 2.5rem !important;
  text-decoration: none !important;
}

.vendor_btn-primary {
  background-color: #3b82f6 !important;
  color: #ffffff !important;
  border-color: #3b82f6 !important;
}

.vendor_btn-primary:hover {
  background-color: #2563eb !important;
}

.vendor_btn-outline {
  background-color: transparent !important;
  color: #111827 !important;
  border-color: #e5e7eb !important;
}

.vendor_btn-outline:hover {
  background-color: #f3f4f6 !important;
}

.vendor_btn:disabled {
  opacity: 0.5 !important;
  cursor: not-allowed !important;
  pointer-events: none !important;
}

.vendor_btn-primary:disabled {
  background-color: #9ca3af !important;
  border-color: #9ca3af !important;
}

.vendor_btn-sm {
  padding: 0.375rem 0.75rem !important;
  font-size: 0.75rem !important;
  height: auto !important;
}

.vendor_btn-ghost {
  background-color: transparent !important;
  border: none !important;
  color: #6b7280 !important;
  padding: 0.5rem !important;
}

.vendor_btn-ghost:hover {
  background-color: #f3f4f6 !important;
  color: #111827 !important;
}

.vendor_tabs {
  margin-bottom: 2rem !important;
}

.vendor_tabs-list {
  display: inline-flex !important;
  height: 2.5rem !important;
  align-items: center !important;
  justify-content: center !important;
  border-radius: 0.375rem !important;
  background-color: #f9fafb !important;
  padding: 0.25rem !important;
  color: #6b7280 !important;
  width: 100% !important;
}

.vendor_tabs-trigger {
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  white-space: nowrap !important;
  border-radius: 0.25rem !important;
  padding: 0.5rem 1rem !important;
  font-size: 0.875rem !important;
  font-weight: 500 !important;
  transition: all 0.15s !important;
  cursor: pointer !important;
  border: none !important;
  background: transparent !important;
  color: #6b7280 !important;
  flex: 1 !important;
}

.vendor_tabs-trigger:hover {
  background-color: #f3f4f6 !important;
  color: #111827 !important;
}

.vendor_tabs-trigger-active {
  background-color: #ffffff !important;
  color: #111827 !important;
  box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05) !important;
  font-weight: 600 !important;
}

.vendor_tabs-content {
  margin-top: 1.5rem !important;
}

.vendor_card {
  background-color: #ffffff !important;
  border: 1px solid #e5e7eb !important;
  border-radius: 0.5rem !important;
  box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05) !important;
  overflow: hidden !important;
  transition: box-shadow 0.2s ease !important;
}

.vendor_card:hover {
  box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1) !important;
}

.vendor_card-header {
  padding: 1.5rem !important;
  border-bottom: 1px solid #e5e7eb !important;
  background-color: #ffffff !important;
}

.vendor_card-header-content {
  display: flex !important;
  align-items: center !important;
  justify-content: space-between !important;
  gap: 1rem !important;
  flex-wrap: wrap !important;
}

.vendor_back-btn {
  flex-shrink: 0 !important;
}

.vendor_card-title {
  font-size: 1.25rem !important;
  font-weight: 600 !important;
  color: #111827 !important;
  margin: 0 !important;
}

.vendor_card-content {
  padding: 2rem !important;
}

.vendor_form-grid {
  display: grid !important;
  grid-template-columns: repeat(1, minmax(0, 1fr)) !important;
  gap: 1.5rem !important;
}

@media (min-width: 768px) {
  .vendor_form-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
  }
}

.vendor_form-item {
  display: flex !important;
  flex-direction: column !important;
  gap: 0.5rem !important;
}

.vendor_form-label {
  font-size: 0.875rem !important;
  font-weight: 600 !important;
  color: #111827 !important;
  margin-bottom: 0.25rem !important;
}

.vendor_input,
.vendor_select,
.vendor_textarea {
  display: flex !important;
  height: 2.75rem !important;
  width: 100% !important;
  border-radius: 0.5rem !important;
  border: 1px solid #e5e7eb !important;
  background-color: #ffffff !important;
  padding: 0.75rem 1rem !important;
  font-size: 0.875rem !important;
  transition: all 0.2s ease !important;
  color: #111827 !important;
  box-sizing: border-box !important;
}

.vendor_input:focus,
.vendor_select:focus,
.vendor_textarea:focus {
  outline: none !important;
  border-color: #3b82f6 !important;
  box-shadow: 0 0 0 3px rgb(59 130 246 / 0.1) !important;
}

.vendor_input:hover,
.vendor_select:hover,
.vendor_textarea:hover {
  border-color: #d1d5db !important;
}

.vendor_textarea {
  min-height: 6rem !important;
  resize: vertical !important;
  height: auto !important;
}

.vendor_select {
  cursor: pointer !important;
}

.vendor_checkbox-container {
  display: flex !important;
  align-items: center !important;
  gap: 0.75rem !important;
  margin-top: 0.5rem !important;
}

.vendor_checkbox {
  width: 1rem !important;
  height: 1rem !important;
  border: 1px solid #e5e7eb !important;
  border-radius: 0.25rem !important;
  background-color: #ffffff !important;
  cursor: pointer !important;
}

.vendor_checkbox:checked {
  background-color: #3b82f6 !important;
  border-color: #3b82f6 !important;
}

/* Utility classes */
.vendor_flex {
  display: flex !important;
}

.vendor_items-center {
  align-items: center !important;
}

.vendor_justify-between {
  justify-content: space-between !important;
}

.vendor_gap-2 {
  gap: 0.5rem !important;
}

.vendor_mr-2 {
  margin-right: 0.5rem !important;
}

.vendor_h-4 {
  height: 1rem !important;
}

.vendor_w-4 {
  width: 1rem !important;
}

/* Responsive design */
@media (max-width: 768px) {
  .vendor_vendor-registration-container {
    padding: 1rem 0.5rem !important;
  }
  
  .vendor_registration-header {
    flex-direction: column !important;
    align-items: flex-start !important;
    gap: 1rem !important;
  }
  
  .vendor_action-buttons {
    width: 100% !important;
    justify-content: flex-end !important;
  }
  
  .vendor_tabs-list {
    flex-direction: column !important;
    height: auto !important;
  }
  
  .vendor_tabs-trigger {
    width: 100% !important;
    justify-content: flex-start !important;
    padding: 0.75rem 1rem !important;
  }
  
  .vendor_form-grid {
    grid-template-columns: 1fr !important;
  }
  
  .vendor_card-content {
    padding: 1rem !important;
  }
  
  .vendor_card-header-content {
    flex-direction: column !important;
    align-items: flex-start !important;
  }
  
  .vendor_back-btn {
    width: 100% !important;
    justify-content: center !important;
  }
  
  .vendor_document-card {
    flex-direction: column !important;
  }
  
  .vendor_document-card-header {
    border-right: none !important;
    border-bottom: 1px solid #e2e8f0 !important;
  }
  
  .vendor_document-card-content {
    justify-content: flex-start !important;
  }
  
  .vendor_document-actions {
    width: 100% !important;
  }
  
  .vendor_document-actions .vendor_btn {
    flex: 1 !important;
    min-width: 120px !important;
  }
}

/* File upload styling */
.vendor_file-info {
  margin-top: 0.5rem !important;
  padding: 0.5rem !important;
  background-color: #f3f4f6 !important;
  border-radius: 0.25rem !important;
  border: 1px solid #e5e7eb !important;
}

.vendor_file-info small {
  color: #6b7280 !important;
  font-size: 0.75rem !important;
}

/* Loading animation */
@keyframes spin {
  from {
    transform: rotate(0deg) !important;
  }
  to {
    transform: rotate(360deg) !important;
  }
}

.animate-spin {
  animation: spin 1s linear infinite !important;
}

/* Document Modal Styling */
.vendor_document-modal-overlay {
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  right: 0 !important;
  bottom: 0 !important;
  background-color: rgba(0, 0, 0, 0.8) !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  z-index: 9999 !important;
  padding: 1rem !important;
}

.vendor_document-modal-content {
  background: white !important;
  border-radius: 0.5rem !important;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25) !important;
  width: 90% !important;
  max-width: 1200px !important;
  height: 90% !important;
  max-height: 800px !important;
  display: flex !important;
  flex-direction: column !important;
  overflow: hidden !important;
}

.vendor_document-modal-header {
  display: flex !important;
  justify-content: space-between !important;
  align-items: center !important;
  padding: 1rem 1.5rem !important;
  border-bottom: 1px solid #e5e7eb !important;
  background-color: #f9fafb !important;
}

.vendor_document-modal-title {
  font-size: 1.25rem !important;
  font-weight: 600 !important;
  color: #111827 !important;
  margin: 0 !important;
}

.vendor_document-modal-close {
  background: none !important;
  border: none !important;
  cursor: pointer !important;
  padding: 0.5rem !important;
  border-radius: 0.25rem !important;
  color: #6b7280 !important;
  transition: all 0.2s !important;
}

.vendor_document-modal-close:hover {
  background-color: #e5e7eb !important;
  color: #374151 !important;
}

.vendor_document-modal-body {
  flex: 1 !important;
  padding: 0 !important;
  overflow: hidden !important;
}

.vendor_document-iframe {
  width: 100% !important;
  height: 100% !important;
  border: none !important;
  border-radius: 0 0 0.5rem 0.5rem !important;
}

/* Document URL styling */
.vendor_document-url {
  color: #6b7280 !important;
  font-size: 0.875rem !important;
  word-break: break-all !important;
}

/* Toggle Tabs Styling */
.vendor_toggle-tabs-container {
  background: white !important;
  border-radius: 0.5rem !important;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06) !important;
  overflow: hidden !important;
}

.vendor_toggle-tabs {
  display: flex !important;
  background-color: #f8fafc !important;
  border-bottom: 1px solid #e2e8f0 !important;
}

.vendor_toggle-tab {
  flex: 1 !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  gap: 0.5rem !important;
  padding: 0.75rem 1rem !important;
  background: none !important;
  border: none !important;
  color: #64748b !important;
  font-weight: 500 !important;
  font-size: 0.875rem !important;
  cursor: pointer !important;
  transition: all 0.2s !important;
  border-bottom: 2px solid transparent !important;
}

.vendor_toggle-tab:hover {
  background-color: #f1f5f9 !important;
  color: #334155 !important;
}

.vendor_toggle-tab-active {
  color: #3b82f6 !important;
  background-color: white !important;
  border-bottom-color: #3b82f6 !important;
}

.vendor_toggle-tab-content {
  padding: 1.5rem !important;
}

/* Documents Tab Content */
.vendor_documents-tab-content {
  min-height: 400px !important;
}

.vendor_documents-grid {
  display: flex !important;
  flex-direction: column !important;
  gap: 1rem !important;
}

.vendor_document-card {
  background: white !important;
  border: 1px solid #e2e8f0 !important;
  border-radius: 0.5rem !important;
  overflow: hidden !important;
  transition: all 0.2s !important;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1) !important;
  width: 100% !important;
  display: flex !important;
  flex-direction: column !important;
  padding: 1.5rem !important;
  margin-bottom: 1rem !important;
}

.vendor_document-card:hover {
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06) !important;
  transform: translateY(-1px) !important;
}

.vendor_document-card-header {
  display: flex !important;
  align-items: center !important;
  gap: 1rem !important;
  padding: 1rem !important;
  background-color: #f8fafc !important;
  border-bottom: 1px solid #e2e8f0 !important;
  border-right: none !important;
  flex: 1 !important;
  min-width: 0 !important;
  margin-bottom: 1rem !important;
}

.vendor_document-icon {
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  width: 3rem !important;
  height: 3rem !important;
  background-color: #3b82f6 !important;
  color: white !important;
  border-radius: 0.5rem !important;
}

.vendor_document-info {
  flex: 1 !important;
  width: 100% !important;
}

.vendor_document-name {
  font-size: 1rem !important;
  font-weight: 600 !important;
  color: #1e293b !important;
  margin: 0 0 0.25rem 0 !important;
}

.vendor_document-title {
  font-size: 1rem !important;
  font-weight: 600 !important;
  color: #1e293b !important;
  margin: 0 0 0.25rem 0 !important;
}

.vendor_document-details {
  font-size: 0.875rem !important;
  color: #64748b !important;
  margin: 0.25rem 0 !important;
}

.vendor_document-meta {
  font-size: 0.75rem !important;
  color: #94a3b8 !important;
  margin: 0.25rem 0 !important;
}

.vendor_document-type {
  font-size: 0.875rem !important;
  color: #64748b !important;
  margin: 0 !important;
}

.vendor_document-card-content {
  padding: 0 !important;
  display: flex !important;
  align-items: center !important;
  justify-content: flex-start !important;
  flex-shrink: 0 !important;
  margin-top: 1rem !important;
}

.vendor_document-url-preview {
  margin-bottom: 1rem !important;
  padding: 0.75rem !important;
  background-color: #f8fafc !important;
  border-radius: 0.375rem !important;
  border: 1px solid #e2e8f0 !important;
}

.vendor_document-url-text {
  font-size: 0.75rem !important;
  color: #64748b !important;
  font-family: monospace !important;
  word-break: break-all !important;
}

.vendor_document-actions {
  display: flex !important;
  gap: 0.5rem !important;
  flex-wrap: wrap !important;
  align-items: center !important;
  margin-top: 1rem !important;
  padding-top: 1rem !important;
  border-top: 1px solid #e5e7eb !important;
}

.vendor_document-actions .vendor_btn {
  flex: 0 0 auto !important;
  min-width: auto !important;
  white-space: nowrap !important;
}

/* Badge Styles */
.vendor_badge {
  display: inline-flex !important;
  align-items: center !important;
  padding: 0.25rem 0.75rem !important;
  font-size: 0.75rem !important;
  font-weight: 500 !important;
  border-radius: 9999px !important;
  margin-left: 0.5rem !important;
}

.vendor_badge-secondary {
  background-color: #e5e7eb !important;
  color: #374151 !important;
}

.vendor_badge-success {
  background-color: #dcfce7 !important;
  color: #166534 !important;
}

.vendor_badge-warning {
  background-color: #fef3c7 !important;
  color: #92400e !important;
}

.vendor_badge-destructive {
  background-color: #fee2e2 !important;
  color: #991b1b !important;
}

.vendor_badge-default {
  background-color: #f3f4f6 !important;
  color: #374151 !important;
}

.vendor_badge-primary {
  background-color: #dbeafe !important;
  color: #1e40af !important;
}

/* Contacts Section Styling */
.vendor_contact-card {
  background: white !important;
  border: 1px solid #e2e8f0 !important;
  border-radius: 0.5rem !important;
  padding: 1.5rem !important;
  margin-bottom: 1rem !important;
  transition: all 0.2s !important;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1) !important;
}

.vendor_contact-card:hover {
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06) !important;
  transform: translateY(-1px) !important;
}

.vendor_contact-info {
  position: relative !important;
}

.vendor_contact-name {
  font-size: 1.125rem !important;
  font-weight: 600 !important;
  color: #1e293b !important;
  margin: 0 !important;
}

.vendor_contact-details {
  font-size: 0.875rem !important;
  color: #64748b !important;
  margin: 0.5rem 0 !important;
}

.vendor_contact-role {
  font-size: 0.875rem !important;
  color: #94a3b8 !important;
  margin: 0.25rem 0 0 0 !important;
  font-style: italic !important;
}

.vendor_contact-actions {
  display: flex !important;
  gap: 0.5rem !important;
  margin-top: 1rem !important;
  padding-top: 1rem !important;
  border-top: 1px solid #e5e7eb !important;
}

.vendor_mb-1 {
  margin-bottom: 0.25rem !important;
}

.vendor_space-y-4 > * + * {
  margin-top: 1rem !important;
}

/* No Contacts State */
.vendor_no-contacts {
  display: flex !important;
  flex-direction: column !important;
  align-items: center !important;
  justify-content: center !important;
  padding: 3rem 2rem !important;
  text-align: center !important;
  color: #64748b !important;
}

.vendor_no-contacts-icon {
  margin-bottom: 1rem !important;
  color: #cbd5e1 !important;
}

.vendor_no-contacts-title {
  font-size: 1.25rem !important;
  font-weight: 600 !important;
  color: #475569 !important;
  margin: 0 0 0.5rem 0 !important;
}

.vendor_no-contacts-text {
  font-size: 0.875rem !important;
  color: #64748b !important;
  margin: 0 !important;
}

/* No Documents State */
.vendor_no-documents {
  display: flex !important;
  flex-direction: column !important;
  align-items: center !important;
  justify-content: center !important;
  padding: 3rem 2rem !important;
  text-align: center !important;
  color: #64748b !important;
}

.vendor_no-documents-icon {
  margin-bottom: 1rem !important;
  color: #cbd5e1 !important;
}

.vendor_no-documents-title {
  font-size: 1.25rem !important;
  font-weight: 600 !important;
  color: #475569 !important;
  margin: 0 0 0.5rem 0 !important;
}

.vendor_no-documents-text {
  font-size: 0.875rem !important;
  color: #64748b !important;
  margin: 0 !important;
}

/* RFP Response Documents Styling */
.vendor_data-document-content {
  margin-top: 0.5rem !important;
  padding: 0.75rem !important;
  background-color: #ffffff !important;
  border: 1px solid #e5e7eb !important;
  border-radius: 0.375rem !important;
  font-size: 0.75rem !important;
}

.vendor_data-document-meta {
  margin-bottom: 0.25rem !important;
  color: #6b7280 !important;
}

.vendor_document-link {
  color: #3b82f6 !important;
  text-decoration: none !important;
  font-weight: 500 !important;
  transition: color 0.2s ease !important;
  word-break: break-all !important;
}

.vendor_document-link:hover {
  color: #2563eb !important;
  text-decoration: underline !important;
}

.vendor_document-actions {
  display: flex !important;
  gap: 0.5rem !important;
  align-items: center !important;
  margin-top: 0.5rem !important;
  padding-top: 0.5rem !important;
  border-top: 1px solid #e5e7eb !important;
}

/* RFP Response Status Badges */
.vendor_data-badge-submitted {
  background-color: #dbeafe !important;
  color: #1e40af !important;
}

.vendor_data-badge-under_evaluation {
  background-color: #fef3c7 !important;
  color: #92400e !important;
}

.vendor_data-badge-shortlisted {
  background-color: #dcfce7 !important;
  color: #166534 !important;
}

.vendor_data-badge-rejected {
  background-color: #fee2e2 !important;
  color: #991b1b !important;
}

.vendor_data-badge-awarded {
  background-color: #dcfce7 !important;
  color: #166534 !important;
}

.vendor_data-badge-draft {
  background-color: #f3f4f6 !important;
  color: #374151 !important;
}

.vendor_data-badge-under_review {
  background-color: #fef3c7 !important;
  color: #92400e !important;
}

.vendor_data-badge-accepted {
  background-color: #dcfce7 !important;
  color: #166534 !important;
}

/* Enhanced document display */
.vendor_data-document {
  transition: all 0.2s ease !important;
}

.vendor_data-document:hover {
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1) !important;
}

/* Document URL display */
.vendor_data-document-content a {
  display: block !important;
  margin-bottom: 0.5rem !important;
  padding: 0.5rem !important;
  background-color: #f8fafc !important;
  border: 1px solid #e2e8f0 !important;
  border-radius: 0.375rem !important;
  word-break: break-all !important;
}

/* Lifecycle Timeline Styling */
.vendor_lifecycle-container {
  max-width: 800px !important;
  margin: 0 auto !important;
}

.vendor_current-stage {
  margin-bottom: 2rem !important;
}

.vendor_current-stage-title {
  font-size: 1.125rem !important;
  font-weight: 600 !important;
  color: #1e293b !important;
  margin-bottom: 1rem !important;
}

.vendor_stage-card {
  background: white !important;
  border: 1px solid #e2e8f0 !important;
  border-radius: 0.5rem !important;
  padding: 1.5rem !important;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1) !important;
}

.vendor_stage-current {
  border-color: #3b82f6 !important;
  box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.1) !important;
}

.vendor_stage-header {
  display: flex !important;
  align-items: flex-start !important;
  gap: 1rem !important;
}

.vendor_stage-icon {
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  width: 3rem !important;
  height: 3rem !important;
  background-color: #3b82f6 !important;
  color: white !important;
  border-radius: 50% !important;
  flex-shrink: 0 !important;
}

.vendor_stage-info {
  flex: 1 !important;
}

.vendor_stage-name {
  font-size: 1.25rem !important;
  font-weight: 600 !important;
  color: #1e293b !important;
  margin: 0 0 0.25rem 0 !important;
}

.vendor_stage-code {
  font-size: 0.875rem !important;
  color: #64748b !important;
  font-family: monospace !important;
  margin: 0 0 0.5rem 0 !important;
}

.vendor_stage-description {
  font-size: 0.875rem !important;
  color: #64748b !important;
  margin: 0 !important;
  line-height: 1.5 !important;
}

.vendor_stage-status {
  flex-shrink: 0 !important;
}

.vendor_timeline {
  margin-top: 2rem !important;
}

.vendor_timeline-title {
  font-size: 1.125rem !important;
  font-weight: 600 !important;
  color: #1e293b !important;
  margin-bottom: 1.5rem !important;
}

.vendor_timeline-container {
  position: relative !important;
  padding-left: 2rem !important;
}

.vendor_timeline-container::before {
  content: '' !important;
  position: absolute !important;
  left: 1rem !important;
  top: 0 !important;
  bottom: 0 !important;
  width: 2px !important;
  background-color: #e2e8f0 !important;
}

.vendor_timeline-item {
  position: relative !important;
  margin-bottom: 2rem !important;
  padding-left: 2rem !important;
}

.vendor_timeline-marker {
  position: absolute !important;
  left: -1.5rem !important;
  top: 0.5rem !important;
  width: 2rem !important;
  height: 2rem !important;
  border-radius: 50% !important;
  background-color: #e2e8f0 !important;
  border: 3px solid white !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  color: #64748b !important;
  z-index: 1 !important;
}

.vendor_timeline-marker-completed {
  background-color: #22c55e !important;
  color: white !important;
}

.vendor_timeline-marker-current {
  background-color: #3b82f6 !important;
  color: white !important;
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1) !important;
}

.vendor_timeline-content {
  background: white !important;
  border: 1px solid #e2e8f0 !important;
  border-radius: 0.5rem !important;
  padding: 1.5rem !important;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1) !important;
}

.vendor_timeline-stage {
  margin-bottom: 1rem !important;
}

.vendor_timeline-stage-name {
  font-size: 1rem !important;
  font-weight: 600 !important;
  color: #1e293b !important;
  margin: 0 0 0.25rem 0 !important;
}

.vendor_timeline-stage-code {
  font-size: 0.75rem !important;
  color: #64748b !important;
  font-family: monospace !important;
  background-color: #f1f5f9 !important;
  padding: 0.25rem 0.5rem !important;
  border-radius: 0.25rem !important;
}

.vendor_timeline-dates {
  margin-bottom: 1rem !important;
}

.vendor_timeline-date {
  font-size: 0.875rem !important;
  color: #64748b !important;
  margin: 0.25rem 0 !important;
}

.vendor_timeline-date-current {
  color: #3b82f6 !important;
  font-weight: 500 !important;
}

.vendor_timeline-actions {
  display: flex !important;
  gap: 0.5rem !important;
  flex-wrap: wrap !important;
}

.vendor_timeline-actions .vendor_btn {
  font-size: 0.75rem !important;
  padding: 0.375rem 0.75rem !important;
}

/* No Lifecycle Data State */
.vendor_no-lifecycle-data {
  display: flex !important;
  flex-direction: column !important;
  align-items: center !important;
  justify-content: center !important;
  padding: 3rem 2rem !important;
  text-align: center !important;
  color: #64748b !important;
}

.vendor_no-lifecycle-icon {
  margin-bottom: 1rem !important;
  color: #cbd5e1 !important;
}

.vendor_no-lifecycle-title {
  font-size: 1.25rem !important;
  font-weight: 600 !important;
  color: #475569 !important;
  margin: 0 0 0.5rem 0 !important;
}

.vendor_no-lifecycle-text {
  font-size: 0.875rem !important;
  color: #64748b !important;
  margin: 0 !important;
  max-width: 400px !important;
}

/* Already Registered Message Styles */
.vendor_already-registered {
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%) !important;
  border: 1px solid #0ea5e9 !important;
  border-radius: 0.75rem !important;
  margin: 2rem 0 !important;
  padding: 2rem !important;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06) !important;
}

.vendor_already-registered-content {
  display: flex !important;
  align-items: center !important;
  gap: 2rem !important;
  max-width: 800px !important;
  margin: 0 auto !important;
}

.vendor_already-registered-icon {
  flex-shrink: 0 !important;
  color: #0ea5e9 !important;
}

.vendor_already-registered-text {
  flex: 1 !important;
}

.vendor_already-registered-title {
  font-size: 1.5rem !important;
  font-weight: 700 !important;
  color: #0c4a6e !important;
  margin: 0 0 0.75rem 0 !important;
}

.vendor_already-registered-message {
  font-size: 1rem !important;
  color: #0369a1 !important;
  margin: 0 0 1.5rem 0 !important;
  line-height: 1.6 !important;
}

.vendor_already-registered-actions {
  display: flex !important;
  gap: 1rem !important;
  flex-wrap: wrap !important;
}

.vendor_already-registered-actions .vendor_btn {
  display: inline-flex !important;
  align-items: center !important;
  gap: 0.5rem !important;
  padding: 0.75rem 1.5rem !important;
  font-weight: 500 !important;
  border-radius: 0.5rem !important;
  transition: all 0.2s ease !important;
}

.vendor_already-registered-actions .vendor_btn-primary {
  background-color: #0ea5e9 !important;
  color: #ffffff !important;
  border: 1px solid #0ea5e9 !important;
}

.vendor_already-registered-actions .vendor_btn-primary:hover {
  background-color: #0284c7 !important;
  border-color: #0284c7 !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 8px rgba(14, 165, 233, 0.3) !important;
}

.vendor_already-registered-actions .vendor_btn-outline {
  background-color: transparent !important;
  color: #0ea5e9 !important;
  border: 1px solid #0ea5e9 !important;
}

.vendor_already-registered-actions .vendor_btn-outline:hover {
  background-color: #0ea5e9 !important;
  color: #ffffff !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 8px rgba(14, 165, 233, 0.2) !important;
}

/* Responsive design for already registered message */
@media (max-width: 768px) {
  .vendor_already-registered-content {
    flex-direction: column !important;
    text-align: center !important;
    gap: 1.5rem !important;
  }
  
  .vendor_already-registered-actions {
    justify-content: center !important;
  }
  
  .vendor_already-registered-actions .vendor_btn {
    flex: 1 !important;
    min-width: 140px !important;
  }
}
</style>
