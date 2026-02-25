<template>
  <div class="vendor_vendor-registration-container">
    <!-- Header -->
    <div class="vendor_registration-header">
      <div>
        <h1 class="vendor_registration-title">
          Vendor Management
        </h1>
        <p class="vendor_registration-subtitle">Add and manage vendor information</p>
      </div>
      <div class="vendor_summary-stats">
        <div class="vendor_stat-item">
          <span class="vendor_stat-label">Total:</span>
          <span class="vendor_stat-value">{{ totalVendors }}</span>
        </div>
        <div class="vendor_stat-item">
          <span class="vendor_stat-label">Unsaved:</span>
          <span class="vendor_stat-value vendor_stat-value-warning">{{ unsavedVendorsCount }}</span>
        </div>
      </div>
    </div>

    <!-- Action Buttons -->
    <div class="vendor_action-buttons-bar">
      <button 
        class="vendor_btn vendor_btn-outline" 
        @click="downloadExcelTemplate"
        title="Download Excel template with column headers"
      >
        <svg class="vendor_h-4 vendor_w-4 vendor_mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        Download Template
      </button>
      <label 
        for="bulk-upload-input"
        class="vendor_btn vendor_btn-outline vendor_btn-upload"
        :class="{ 'vendor_btn-upload-disabled': isSubmitting }"
        title="Upload Excel/CSV file to add multiple vendors"
      >
        <svg class="vendor_h-4 vendor_w-4 vendor_mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
        </svg>
        Bulk Upload
        <input 
          id="bulk-upload-input"
          type="file" 
          accept=".xlsx,.xls,.csv"
          @change="handleBulkUpload"
          style="display: none"
          :disabled="isSubmitting"
        />
      </label>
      <button 
        class="vendor_btn vendor_btn-outline" 
        @click="addNewVendorForm"
        :disabled="isSubmitting"
        title="Add another vendor"
      >
        <svg class="vendor_h-4 vendor_w-4 vendor_mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
        </svg>
        Add Another Vendor
      </button>
      <button 
        class="vendor_btn vendor_btn-primary vendor_btn-submit-all" 
        @click="submitAllVendors" 
        :disabled="isSubmitting || unsavedVendorsCount === 0"
        title="Submit all unsaved vendors"
      >
        <svg class="vendor_h-4 vendor_w-4 vendor_mr-2" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
        </svg>
        <span>Submit All Vendors</span>
        <span v-if="unsavedVendorsCount > 0" class="vendor_badge-count">{{ unsavedVendorsCount }}</span>
      </button>
    </div>

    <!-- List View -->
    <template v-if="showListView">
    <!-- Vendors Table -->
    <div v-if="vendorForms.length > 0" class="vendor_table-container">
      <table class="vendor_table">
        <thead>
          <tr>
            <th>Vendor Code</th>
            <th>Company Name</th>
            <th>Industry</th>
            <th>Risk Level</th>
            <th>Status</th>
            <th>Saved</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(vendorForm, index) in vendorForms" :key="vendorForm.id" class="vendor_table-row">
            <td>{{ vendorForm.data.vendor_code || '-' }}</td>
            <td>{{ vendorForm.data.company_name || 'Unnamed' }}</td>
            <td>{{ vendorForm.data.industry_sector || '-' }}</td>
            <td>
              <span 
                class="vendor_risk-badge" 
                :class="{
                  'vendor_risk-low': vendorForm.data.risk_level?.toLowerCase() === 'low',
                  'vendor_risk-medium': vendorForm.data.risk_level?.toLowerCase() === 'medium',
                  'vendor_risk-high': vendorForm.data.risk_level?.toLowerCase() === 'high',
                  'vendor_risk-critical': vendorForm.data.risk_level?.toLowerCase() === 'critical'
                }"
              >
                {{ vendorForm.data.risk_level || 'Low' }}
              </span>
            </td>
            <td>
              <span 
                class="vendor_status-badge" 
                :class="{
                  'vendor_status-pending': vendorForm.data.status === 'pending',
                  'vendor_status-approved': vendorForm.data.status === 'approved',
                  'vendor_status-rejected': vendorForm.data.status === 'rejected'
                }"
              >
                {{ vendorForm.data.status || 'Pending' }}
              </span>
            </td>
            <td>{{ vendorForm.submitted ? 'Yes' : '-' }}</td>
            <td class="vendor_actions-cell">
              <button 
                class="vendor_action-btn vendor_action-edit" 
                @click="editVendor(vendorForm.id)"
                title="Edit vendor"
              >
                <svg class="vendor_h-4 vendor_w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
              </button>
              <button 
                class="vendor_action-btn vendor_action-delete" 
                @click="deleteVendor(vendorForm.id)"
                title="Delete vendor"
              >
                <svg class="vendor_h-4 vendor_w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
              <button 
                class="vendor_action-btn vendor_action-view" 
                @click="viewVendorDetails(vendorForm.id)"
                title="View details"
              >
                <svg class="vendor_h-4 vendor_w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

      <!-- Empty State -->
      <div v-if="vendorForms.length === 0" class="vendor_no-vendors-state">
        <div class="vendor_no-vendors-icon">
          <svg class="vendor_w-16 vendor_h-16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
          </svg>
        </div>
        <h3 class="vendor_no-vendors-title">No Vendors Added</h3>
        <p class="vendor_no-vendors-text">Click "Add Another Vendor" to start adding vendors to the system.</p>
        <button class="vendor_btn vendor_btn-primary" @click="addNewVendorForm">
          <svg class="vendor_h-4 vendor_w-4 vendor_mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          Add First Vendor
        </button>
      </div>
    </template>

    <!-- Edit/View Form View -->
    <div v-if="!showListView && activeVendorForm" class="vendor_form-view">
      <!-- Form Header -->
      <div class="vendor_form-header">
        <div class="vendor_form-header-left">
          <button class="vendor_back-button" @click="goBackToList" title="Back to list">
            <svg class="vendor_h-5 vendor_w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
            </svg>
            <span>Back</span>
          </button>
          <div class="vendor_form-title-section">
            <h1 class="vendor_form-title">Vendor #{{ getVendorIndex(activeVendorForm.id) + 1 }}</h1>
            <p class="vendor_form-code">{{ activeVendorForm.data.vendor_code || '-' }}</p>
          </div>
        </div>
        <div class="vendor_form-header-right">
          <button 
            v-if="!activeVendorForm.submitted && viewMode === 'edit'"
            class="vendor_btn vendor_btn-primary vendor_submit-button" 
            @click="submitSingleVendor(activeVendorForm.id)"
            :disabled="isSubmitting || activeVendorForm.isSubmitting"
            title="Submit this vendor"
          >
            <svg class="vendor_h-4 vendor_w-4 vendor_mr-2" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
            </svg>
            <span v-if="activeVendorForm.isSubmitting">Submitting...</span>
            <span v-else>Submit Vendor</span>
          </button>
        </div>
      </div>

      <!-- Vendor Form Content -->
      <div class="vendor_form-container">
        <!-- Error Messages -->
        <div v-if="activeVendorForm.errors && Object.keys(activeVendorForm.errors).length > 0" class="vendor_error-messages">
          <div v-for="(error, field) in activeVendorForm.errors" :key="field" class="vendor_error-message">
            <svg class="vendor_h-4 vendor_w-4 vendor_mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <strong>{{ formatFieldName(field) }}:</strong> {{ Array.isArray(error) ? error.join(', ') : error }}
          </div>
        </div>

        <!-- Vendor Form Content -->
        <div class="vendor_form-content">
          <div class="vendor_card">
            <div class="vendor_card-content">
              <!-- Form Tabs -->
              <div class="vendor_tabs">
                <div class="vendor_tabs-list">
                  <button 
                    v-for="tab in tabs" 
                    :key="tab.id"
                    class="vendor_tabs-trigger"
                    :class="{ 'vendor_tabs-trigger-active': activeVendorForm.activeTab === tab.id }"
                    @click="activeVendorForm.activeTab = tab.id"
                  >
                    {{ tab.label }}
                  </button>
                </div>
              </div>

              <!-- Company Info Tab -->
              <div v-if="activeVendorForm && activeVendorForm.activeTab === 'company-info'" class="vendor_tabs-content">
                <div class="vendor_form-grid">
                  <div class="vendor_form-item">
                    <label for="vendor-code" class="vendor_form-label">Vendor Code</label>
                    <input 
                      id="vendor-code" 
                      class="vendor_input" 
                      v-model="activeVendorForm.data.vendor_code"
                      placeholder="Auto-generated"
                      readonly
                      title="Vendor code is auto-generated"
                    />
                  </div>
                  <div class="vendor_form-item">
                    <label for="company-name" class="vendor_form-label">Company Name *</label>
                    <input 
                      id="company-name" 
                      class="vendor_input" 
                      v-model="activeVendorForm.data.company_name" 
                      :readonly="viewMode === 'view'"
                      required
                      placeholder="Enter company name"
                    />
                  </div>
                  <div class="vendor_form-item">
                    <label for="legal-name" class="vendor_form-label">Legal Name</label>
                    <input 
                      id="legal-name" 
                      class="vendor_input" 
                      v-model="activeVendorForm.data.legal_name"
                      :readonly="viewMode === 'view'"
                      placeholder="Enter legal name"
                    />
                  </div>
                  <div class="vendor_form-item">
                    <label for="business-type" class="vendor_form-label">Business Type</label>
                    <div class="vendor_searchable-select">
                      <input 
                        id="business-type"
                        type="text"
                        class="vendor_input"
                        v-model="activeVendorForm.data.business_type"
                        :readonly="viewMode === 'view'"
                        :list="'business-type-list-' + activeVendorForm.id"
                        placeholder="Type or select business type"
                        @input="handleBusinessTypeInput"
                      />
                      <datalist :id="'business-type-list-' + activeVendorForm.id">
                        <option v-for="type in businessTypes" :key="type" :value="type"></option>
                      </datalist>
                    </div>
                  </div>
                  <div class="vendor_form-item">
                    <label for="tax-id" class="vendor_form-label">Tax ID</label>
                    <input 
                      id="tax-id" 
                      class="vendor_input" 
                      v-model="activeVendorForm.data.tax_id"
                      :readonly="viewMode === 'view'"
                      placeholder="Enter tax ID"
                    />
                  </div>
                  <div class="vendor_form-item">
                    <label for="duns-number" class="vendor_form-label">DUNS Number</label>
                    <input 
                      id="duns-number" 
                      class="vendor_input" 
                      v-model="activeVendorForm.data.duns_number"
                      :readonly="viewMode === 'view'"
                      placeholder="Enter DUNS number"
                    />
                  </div>
                </div>
              </div>

              <!-- Legal & Financial Tab -->
              <div v-if="activeVendorForm && activeVendorForm.activeTab === 'legal-financial'" class="vendor_tabs-content">
                <div class="vendor_form-grid">
                  <div class="vendor_form-item">
                    <label for="incorporation-date" class="vendor_form-label">Incorporation Date</label>
                    <input 
                      id="incorporation-date" 
                      class="vendor_input" 
                      type="date" 
                      v-model="activeVendorForm.data.incorporation_date"
                      :readonly="viewMode === 'view'"
                    />
                  </div>
                  <div class="vendor_form-item">
                    <label for="industry-sector" class="vendor_form-label">Industry Sector</label>
                    <div class="vendor_searchable-select">
                      <input 
                        id="industry-sector"
                        type="text"
                        class="vendor_input"
                        v-model="activeVendorForm.data.industry_sector"
                        :readonly="viewMode === 'view'"
                        :list="'industry-sector-list-' + activeVendorForm.id"
                        placeholder="Type or select industry sector"
                        @input="handleIndustrySectorInput"
                      />
                      <datalist :id="'industry-sector-list-' + activeVendorForm.id">
                        <option v-for="sector in industrySectors" :key="sector" :value="sector"></option>
                      </datalist>
                    </div>
                  </div>
                  <div class="vendor_form-item">
                    <label for="website" class="vendor_form-label">Website</label>
                    <input 
                      id="website" 
                      class="vendor_input" 
                      v-model="activeVendorForm.data.website"
                      :readonly="viewMode === 'view'"
                      placeholder="https://example.com"
                    />
                  </div>
                  <div class="vendor_form-item">
                    <label for="annual-revenue" class="vendor_form-label">Annual Revenue</label>
                    <input 
                      id="annual-revenue" 
                      class="vendor_input" 
                      type="number" 
                      step="0.01"
                      v-model.number="activeVendorForm.data.annual_revenue"
                      :readonly="viewMode === 'view'"
                      placeholder="1000000"
                    />
                  </div>
                  <div class="vendor_form-item">
                    <label for="employee-count" class="vendor_form-label">Employee Count</label>
                    <input 
                      id="employee-count" 
                      class="vendor_input" 
                      type="number"
                      v-model.number="activeVendorForm.data.employee_count"
                      :readonly="viewMode === 'view'"
                      placeholder="100"
                    />
                  </div>
                  <div class="vendor_form-item" style="grid-column: 1 / -1;">
                    <label for="headquarters-address" class="vendor_form-label">Headquarters Address</label>
                    <textarea 
                      id="headquarters-address" 
                      class="vendor_textarea" 
                      v-model="activeVendorForm.data.headquarters_address"
                      :readonly="viewMode === 'view'"
                      placeholder="123 Main St, City, State, ZIP"
                      rows="3"
                    ></textarea>
                  </div>
                </div>
              </div>

              <!-- Category & Risk Tab -->
              <div v-if="activeVendorForm && activeVendorForm.activeTab === 'category-risk'" class="vendor_tabs-content">
                <div class="vendor_form-grid">
                  <div class="vendor_form-item">
                    <label for="vendor-category" class="vendor_form-label">Vendor Category</label>
                    <div class="vendor_searchable-select">
                      <input 
                        id="vendor-category"
                        type="text"
                        class="vendor_input"
                        v-model="activeVendorForm.data.vendor_category"
                        :readonly="viewMode === 'view'"
                        :list="'vendor-category-list-' + activeVendorForm.id"
                        placeholder="Type or select vendor category"
                        @input="handleVendorCategoryInput"
                      />
                      <datalist :id="'vendor-category-list-' + activeVendorForm.id">
                        <option v-for="category in vendorCategories" :key="category" :value="category"></option>
                      </datalist>
                    </div>
                  </div>
                  <div class="vendor_form-item">
                    <label for="risk-level" class="vendor_form-label">Risk Level</label>
                    <select id="risk-level" class="vendor_select" v-model="activeVendorForm.data.risk_level" :disabled="viewMode === 'view'">
                      <option value="">Select risk level</option>
                      <option value="low">Low</option>
                      <option value="medium">Medium</option>
                      <option value="high">High</option>
                      <option value="critical">Critical</option>
                    </select>
                  </div>
                  <div class="vendor_form-item">
                    <label for="status" class="vendor_form-label">Status</label>
                    <select id="status" class="vendor_select" v-model="activeVendorForm.data.status" :disabled="viewMode === 'view'">
                      <option value="pending">Pending</option>
                      <option value="active">Active</option>
                      <option value="inactive">Inactive</option>
                      <option value="suspended">Suspended</option>
                    </select>
                  </div>
                  <div class="vendor_form-item" style="grid-column: 1 / -1;">
                    <div class="vendor_space-y-4">
                      <div class="vendor_checkbox-container vendor_flex vendor_items-center vendor_gap-2">
                        <input 
                          type="checkbox" 
                          id="critical-vendor" 
                          class="vendor_checkbox" 
                          v-model="activeVendorForm.data.is_critical_vendor"
                          :disabled="viewMode === 'view'"
                        />
                        <label class="vendor_form-label" for="critical-vendor">Is Critical Vendor</label>
                      </div>
                      <div class="vendor_checkbox-container vendor_flex vendor_items-center vendor_gap-2">
                        <input 
                          type="checkbox" 
                          id="data-access" 
                          class="vendor_checkbox" 
                          v-model="activeVendorForm.data.has_data_access"
                          :disabled="viewMode === 'view'"
                        />
                        <label class="vendor_form-label" for="data-access">Has Data Access</label>
                      </div>
                      <div class="vendor_checkbox-container vendor_flex vendor_items-center vendor_gap-2">
                        <input 
                          type="checkbox" 
                          id="system-access" 
                          class="vendor_checkbox" 
                          v-model="activeVendorForm.data.has_system_access"
                          :disabled="viewMode === 'view'"
                        />
                        <label class="vendor_form-label" for="system-access">Has System Access</label>
                      </div>
                    </div>
                  </div>
                  <div class="vendor_form-item" style="grid-column: 1 / -1;">
                    <label for="description" class="vendor_form-label">Description</label>
                    <textarea 
                      id="description" 
                      class="vendor_textarea"
                      v-model="activeVendorForm.data.description"
                      :readonly="viewMode === 'view'"
                      placeholder="Vendor description and notes..."
                      rows="4"
                    ></textarea>
                  </div>
                </div>
              </div>

              <!-- Contacts Tab -->
              <div v-if="activeVendorForm && activeVendorForm.activeTab === 'contacts'" class="vendor_tabs-content">
                <div class="vendor_card">
                  <div class="vendor_card-header">
                    <div class="vendor_flex vendor_items-center vendor_justify-between">
                      <h3 class="vendor_card-title">Vendor Contacts</h3>
                      <button 
                        v-if="viewMode === 'edit'"
                        class="vendor_btn vendor_btn-primary" 
                        @click="addContact(activeVendorForm.id)"
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
                    <div v-if="activeVendorForm.contacts.length === 0" class="vendor_no-contacts">
                      <div class="vendor_no-contacts-icon">
                        <svg class="vendor_w-8 vendor_h-8" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                        </svg>
                      </div>
                      <h3 class="vendor_no-contacts-title">No Contacts Added</h3>
                      <p class="vendor_no-contacts-text">Click "Add Contact" to add your first vendor contact.</p>
                    </div>
                    <div v-for="contact in activeVendorForm.contacts" :key="contact.id" class="vendor_contact-card">
                      <div v-if="contact.isEditing && viewMode === 'edit'" class="vendor_form-grid" style="grid-template-columns: 1fr;">
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
                          <button class="vendor_btn vendor_btn-primary vendor_btn-sm" @click="saveContact(activeVendorForm.id, contact.id)">Save</button>
                          <button class="vendor_btn vendor_btn-outline vendor_btn-sm" @click="cancelEditContact(activeVendorForm.id, contact.id)">Cancel</button>
                        </div>
                      </div>
                      <div v-else class="vendor_contact-info">
                        <div class="vendor_flex vendor_items-center vendor_gap-2 vendor_mb-1">
                          <h4 class="vendor_contact-name">{{ contact.name }}</h4>
                          <span v-if="contact.isPrimary" class="vendor_badge vendor_badge-secondary">Primary</span>
                        </div>
                        <p class="vendor_contact-details">{{ contact.email }} • {{ contact.phone }}</p>
                        <p class="vendor_contact-role">{{ contact.role }}</p>
                        <div v-if="viewMode === 'edit'" class="vendor_contact-actions">
                          <button 
                            class="vendor_btn vendor_btn-ghost vendor_btn-sm" 
                            @click="editContact(activeVendorForm.id, contact.id)"
                            title="Edit contact"
                          >
                            <svg class="vendor_h-4 vendor_w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                            </svg>
                          </button>
                          <button 
                            class="vendor_btn vendor_btn-ghost vendor_btn-sm" 
                            @click="removeContact(activeVendorForm.id, contact.id)"
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
              <div v-if="activeVendorForm && activeVendorForm.activeTab === 'documents'" class="vendor_tabs-content">
                <div class="vendor_card">
                  <div class="vendor_card-header">
                    <div class="vendor_flex vendor_items-center vendor_justify-between">
                      <h3 class="vendor_card-title">Vendor Documents</h3>
                      <button 
                        v-if="viewMode === 'edit'"
                        class="vendor_btn vendor_btn-primary" 
                        @click="addDocument(activeVendorForm.id)"
                        title="Upload new document"
                      >
                        <svg class="vendor_h-4 vendor_w-4 vendor_mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                        </svg>
                        Upload Document
                      </button>
                    </div>
                  </div>
                  <div class="vendor_card-content vendor_space-y-4">
                    <div v-if="activeVendorForm.documents.length === 0" class="vendor_no-documents">
                      <div class="vendor_no-documents-icon">
                        <svg class="vendor_w-8 vendor_h-8" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                      </div>
                      <h3 class="vendor_no-documents-title">No Documents Added</h3>
                      <p class="vendor_no-documents-text">Click "Upload Document" to add your first vendor document.</p>
                    </div>
                    <div v-for="doc in activeVendorForm.documents" :key="doc.id" class="vendor_document-card">
                      <div v-if="doc.isEditing && viewMode === 'edit'" class="vendor_form-grid" style="grid-template-columns: 1fr;">
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
                            @change="handleFileUpload($event, activeVendorForm.id, doc.id)"
                            accept=".pdf,.doc,.docx,.txt,.jpg,.jpeg,.png,.xlsx,.xls"
                          />
                          <div v-if="doc.fileName" class="vendor_file-info">
                            <small>Selected: {{ doc.fileName }}</small>
                          </div>
                        </div>
                        <div class="vendor_document-actions">
                          <button class="vendor_btn vendor_btn-primary vendor_btn-sm" @click="saveDocument(activeVendorForm.id, doc.id)">Save</button>
                          <button class="vendor_btn vendor_btn-outline vendor_btn-sm" @click="cancelEditDocument(activeVendorForm.id, doc.id)">Cancel</button>
                        </div>
                      </div>
                      <div v-else class="vendor_document-info">
                        <div class="vendor_flex vendor_items-center vendor_gap-2 vendor_mb-1">
                          <h4 class="vendor_document-name">{{ doc.name || 'Untitled Document' }}</h4>
                          <span class="vendor_badge" :class="getDocumentStatusClass(doc.status)">
                            {{ doc.status }}
                          </span>
                        </div>
                        <p class="vendor_document-details">{{ doc.type }} • Version {{ doc.version || 'N/A' }}</p>
                        <p v-if="doc.expiryDate" class="vendor_document-meta">Expires: {{ doc.expiryDate }}</p>
                        <div v-if="viewMode === 'edit'" class="vendor_document-actions">
                          <button 
                            class="vendor_btn vendor_btn-ghost vendor_btn-sm" 
                            @click="editDocument(activeVendorForm.id, doc.id)"
                            title="Edit document"
                          >
                            <svg class="vendor_h-4 vendor_w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                            </svg>
                          </button>
                          <button 
                            class="vendor_btn vendor_btn-ghost vendor_btn-sm" 
                            @click="removeDocument(activeVendorForm.id, doc.id)"
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
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Popup Modal -->
  <PopupModal />
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/utils/api'
import { getTprmApiUrl } from '@/utils/backendEnv'
import PopupModal from '@/popup/PopupModal.vue'
import { PopupService } from '@/popup/popupService'
import { useNotifications } from '@/composables/useNotifications'
import notificationService from '@/services/notificationService'
import loggingService from '@/services/loggingService'
import { useAuthStore } from '@/stores/auth_vendor'

const { showSuccess, showError, showWarning, showInfo } = useNotifications()
const authStore = useAuthStore()

const vendorForms = ref([])
const activeVendorId = ref(null)
const isSubmitting = ref(false)
const submitMessage = ref(null)
const isProcessingUpload = ref(false)
const showListView = ref(true) // Toggle between list view and edit/view form

// Dynamic options for dropdowns
const businessTypes = ref(['Corporation', 'LLC', 'Partnership', 'Sole Proprietorship', 'Non-Profit', 'Public Company', 'Private Company'])
const industrySectors = ref(['Technology', 'Finance', 'Healthcare', 'Manufacturing', 'Retail', 'Energy', 'Telecommunications', 'Transportation', 'Construction', 'Education', 'Government'])
const vendorCategories = ref(['Software', 'Services', 'Consulting', 'Hardware', 'Maintenance', 'Support', 'Professional Services', 'Managed Services', 'Cloud Services', 'Security'])

// Computed property to get the active vendor form
const activeVendorForm = computed(() => {
  return vendorForms.value.find(f => f.id === activeVendorId.value) || null
})

// Computed properties for summary statistics
const totalVendors = computed(() => {
  return vendorForms.value.length
})

const unsavedVendorsCount = computed(() => {
  return vendorForms.value.filter(form => !form.submitted).length
})

// Modal state
const editingVendorId = ref(null)
const viewMode = ref('edit') // 'edit' or 'view'

// Get vendor index by ID
const getVendorIndex = (formId) => {
  return vendorForms.value.findIndex(f => f.id === formId)
}

// Page navigation management
const editVendor = (vendorId) => {
  activeVendorId.value = vendorId
  viewMode.value = 'edit'
  showListView.value = false
}

const viewVendorDetails = (vendorId) => {
  activeVendorId.value = vendorId
  viewMode.value = 'view'
  showListView.value = false
}

const goBackToList = () => {
  showListView.value = true
  activeVendorId.value = null
  viewMode.value = 'edit'
}

const deleteVendor = (vendorId) => {
  if (confirm('Are you sure you want to delete this vendor?')) {
    removeVendorForm(vendorId)
  }
}

const saveVendor = async (vendorId) => {
  await submitSingleVendor(vendorId)
  // Optionally go back to list view after successful submission
  // goBackToList()
}

    const tabs = [
      { id: 'company-info', label: 'Company Info' },
      { id: 'legal-financial', label: 'Legal & Financial' },
      { id: 'category-risk', label: 'Category & Risk' },
      { id: 'contacts', label: 'Contacts' },
      { id: 'documents', label: 'Documents' }
    ]

    // Generate unique alphanumeric vendor code
    const generateVendorCode = () => {
      // Generate a unique code: VEND + timestamp + random alphanumeric
      const timestamp = Date.now().toString(36).toUpperCase()
      const randomPart = Math.random().toString(36).substring(2, 8).toUpperCase()
      const code = `VEND-${timestamp}-${randomPart}`
      
      // Check if code already exists in current vendor forms
      const existingCodes = vendorForms.value.map(f => f.data.vendor_code)
      if (existingCodes.includes(code)) {
        // If duplicate, generate again with additional randomness
        return generateVendorCode()
      }
      
      return code
    }

    // Create default vendor form data structure
    const createDefaultVendorForm = () => {
      const formId = Date.now().toString() + Math.random().toString(36).substr(2, 9)
      return {
        id: formId,
        activeTab: 'company-info',
        submitted: false,
        isSubmitting: false,
        errors: {},
        data: {
          vendor_code: generateVendorCode(),
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
          contacts: [],
          documents: []
        },
        contacts: [],
        documents: []
      }
    }

    // Add new vendor form
    const addNewVendorForm = () => {
      const newForm = createDefaultVendorForm()
      vendorForms.value.push(newForm)
      activeVendorId.value = newForm.id // Set as active vendor
    }

    // Remove vendor form
    const removeVendorForm = (formId) => {
      const index = vendorForms.value.findIndex(f => f.id === formId)
      if (index === -1) return
      
      const wasActive = activeVendorId.value === formId
      
      // Remove the vendor
      vendorForms.value = vendorForms.value.filter(form => form.id !== formId)
      
      // If we removed the active vendor, switch to another one
      if (wasActive) {
        if (vendorForms.value.length > 0) {
          // Switch to the previous vendor if possible, otherwise the first one
          const newIndex = index > 0 ? Math.min(index - 1, vendorForms.value.length - 1) : 0
          activeVendorId.value = vendorForms.value[newIndex].id
        } else {
          activeVendorId.value = null
        }
      }
    }

    // Download Excel template
    const downloadExcelTemplate = () => {
      try {
        // Create CSV template with headers based on the vendor form fields
        const headers = [
          'Company Name*',
          'Legal Company Name',
          'Business Type',
          'Tax ID',
          'Registration Number',
          'Industry',
          'Website',
          'Primary Email*',
          'Primary Phone',
          'Country*',
          'State',
          'City',
          'Postal Code',
          'Street Address',
          'Contact Person Name',
          'Contact Person Email',
          'Contact Person Phone',
          'Contact Person Position',
          'Annual Revenue',
          'Number of Employees',
          'Year Established',
          'Description'
        ]
        
        // Create sample row with instructions
        const sampleRow = [
          'Example Corp',
          'Example Corporation LLC',
          'Corporation',
          '12-3456789',
          'REG123456',
          'Technology',
          'https://example.com',
          'contact@example.com',
          '+1-555-0100',
          'United States',
          'California',
          'San Francisco',
          '94105',
          '123 Market St',
          'John Doe',
          'john.doe@example.com',
          '+1-555-0101',
          'Procurement Manager',
          '5000000',
          '50',
          '2010',
          'Leading technology solutions provider'
        ]
        
        // Create CSV content
        const csvContent = [
          headers.join(','),
          sampleRow.join(','),
          // Add empty rows for data entry
          Array(headers.length).fill('').join(',')
        ].join('\n')
        
        // Create blob and download
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = 'Vendor_Upload_Template.csv'
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)

        showMessage('success', 'CSV template downloaded successfully')
      } catch (error) {
        console.error('Error downloading template:', error)
        showMessage('error', `Failed to download template: ${error.message}`)
      }
    }

    // Handle bulk upload from Excel/CSV
    const handleBulkUpload = async (event) => {
      const file = event.target.files?.[0]
      if (!file) return

      // Reset file input
      event.target.value = ''

      isProcessingUpload.value = true

      try {
        const fileExtension = file.name.split('.').pop().toLowerCase()
        
        if (fileExtension === 'csv') {
          await parseCSVFile(file)
        } else if (fileExtension === 'xlsx' || fileExtension === 'xls') {
          await parseExcelFile(file)
        } else {
          showMessage('error', 'Unsupported file format. Please upload CSV or Excel (.xlsx, .xls) file.')
          return
        }
      } catch (error) {
        console.error('Error processing bulk upload:', error)
        showMessage('error', `Failed to process file: ${error.message}`)
      } finally {
        isProcessingUpload.value = false
      }
    }

    // Parse CSV file
    const parseCSVFile = (file) => {
      return new Promise((resolve, reject) => {
        const reader = new FileReader()
        
        reader.onload = (e) => {
          try {
            const text = e.target.result
            const lines = text.split('\n').filter(line => line.trim())
            
            if (lines.length < 2) {
              reject(new Error('CSV file must have at least a header row and one data row'))
              return
            }

            // Parse header row
            const headers = parseCSVLine(lines[0])
            const headerMap = createHeaderMap(headers)

            // Parse data rows
            const vendors = []
            for (let i = 1; i < lines.length; i++) {
              const values = parseCSVLine(lines[i])
              if (values.length === 0 || values.every(v => !v.trim())) continue // Skip empty rows
              
              const vendorData = mapRowToVendorData(values, headerMap)
              if (vendorData.company_name) { // Only add if company name exists
                vendors.push(vendorData)
              }
            }

            if (vendors.length === 0) {
              reject(new Error('No valid vendor data found in CSV file'))
              return
            }

            // Create vendor forms from parsed data
            vendors.forEach(vendorData => {
              const newForm = createDefaultVendorForm()
              // Extract contacts before spreading vendorData
              const contacts = vendorData.contacts || []
              delete vendorData.contacts // Remove contacts from vendorData
              newForm.data = { ...newForm.data, ...vendorData }
              // Add parsed contacts to the form
              newForm.contacts = contacts
              vendorForms.value.push(newForm)
            })

            // Set the first new vendor as active
            if (vendorForms.value.length > 0) {
              activeVendorId.value = vendorForms.value[vendorForms.value.length - vendors.length].id
            }

            showMessage('success', `Successfully imported ${vendors.length} vendor(s) from CSV file`)
            resolve()
          } catch (error) {
            reject(error)
          }
        }

        reader.onerror = () => reject(new Error('Failed to read file'))
        reader.readAsText(file)
      })
    }

    // Load XLSX library helper
    const loadXLSXLibrary = () => {
      return new Promise((resolve, reject) => {
        // Check if XLSX is already loaded
        if (window.XLSX && typeof window.XLSX.read === 'function') {
          resolve(window.XLSX)
          return
        }

        // Check if script is already being loaded
        const existingScript = document.querySelector('script[src*="xlsx"]')
        if (existingScript) {
          // Wait for existing script to load
          existingScript.onload = () => {
            if (window.XLSX) {
              resolve(window.XLSX)
            } else {
              reject(new Error('XLSX library failed to load'))
            }
          }
          existingScript.onerror = () => reject(new Error('XLSX library failed to load'))
          return
        }

        // Load xlsx library from CDN
        const script = document.createElement('script')
        script.src = 'https://cdn.sheetjs.com/xlsx-0.20.1/package/dist/xlsx.full.min.js'
        script.async = true
        
        script.onload = () => {
          if (window.XLSX && typeof window.XLSX.read === 'function') {
            resolve(window.XLSX)
          } else {
            reject(new Error('XLSX library failed to initialize'))
          }
        }
        
        script.onerror = () => {
          reject(new Error('Failed to load XLSX library. Please ensure you have an internet connection or save the file as CSV format.'))
        }
        
        document.head.appendChild(script)
      })
    }

    // Parse Excel file
    const parseExcelFile = async (file) => {
      try {
        // Load XLSX library
        const XLSX = await loadXLSXLibrary()

        // Read file as ArrayBuffer
        const arrayBuffer = await new Promise((resolve, reject) => {
          const reader = new FileReader()
          reader.onload = (e) => resolve(e.target.result)
          reader.onerror = () => reject(new Error('Failed to read Excel file'))
          reader.readAsArrayBuffer(file)
        })

        // Parse Excel file
        const data = new Uint8Array(arrayBuffer)
        const workbook = XLSX.read(data, { type: 'array' })
        
        // Get first sheet
        if (!workbook.SheetNames || workbook.SheetNames.length === 0) {
          throw new Error('Excel file has no sheets')
        }

        const firstSheetName = workbook.SheetNames[0]
        const worksheet = workbook.Sheets[firstSheetName]
        
        // Convert to JSON with header row
        const jsonData = XLSX.utils.sheet_to_json(worksheet, { 
          defval: '', // Default value for empty cells
          raw: false // Convert dates and numbers to strings
        })
        
        if (jsonData.length === 0) {
          throw new Error('Excel file is empty or has no data rows')
        }

        // Map Excel columns to vendor data
        const vendors = jsonData.map(row => mapExcelRowToVendorData(row))
          .filter(v => v.company_name && v.company_name.trim() !== '') // Only include rows with company name

        if (vendors.length === 0) {
          throw new Error('No valid vendor data found in Excel file. Please ensure at least one row has a Company Name column.')
        }

        // Create vendor forms
        const startIndex = vendorForms.value.length
        vendors.forEach(vendorData => {
          const newForm = createDefaultVendorForm()
          // Extract contacts before spreading vendorData
          const contacts = vendorData.contacts || []
          delete vendorData.contacts // Remove contacts from vendorData
          newForm.data = { ...newForm.data, ...vendorData }
          // Add parsed contacts to the form
          newForm.contacts = contacts
          vendorForms.value.push(newForm)
        })

        // Set the first new vendor as active
        if (vendorForms.value.length > 0) {
          activeVendorId.value = vendorForms.value[startIndex].id
        }

        showMessage('success', `Successfully imported ${vendors.length} vendor(s) from Excel file`)
      } catch (error) {
        console.error('Error parsing Excel:', error)
        throw new Error(error.message || 'Failed to parse Excel file')
      }
    }

    // Helper function to parse CSV line (handles quoted values)
    const parseCSVLine = (line) => {
      const result = []
      let current = ''
      let inQuotes = false

      for (let i = 0; i < line.length; i++) {
        const char = line[i]
        const nextChar = line[i + 1]

        if (char === '"') {
          if (inQuotes && nextChar === '"') {
            current += '"'
            i++ // Skip next quote
          } else {
            inQuotes = !inQuotes
          }
        } else if (char === ',' && !inQuotes) {
          result.push(current.trim())
          current = ''
        } else {
          current += char
        }
      }
      result.push(current.trim())
      return result
    }

    // Create header map for flexible column mapping
    const createHeaderMap = (headers) => {
      const map = {}
      headers.forEach((header, index) => {
        const normalized = header.toLowerCase().replace(/\s+/g, '_').replace(/[^a-z0-9_]/g, '')
        map[normalized] = index
        // Also map common variations
        const variations = {
          'company_name': ['company', 'companyname', 'vendor_name', 'name'],
          'legal_name': ['legal', 'legalname', 'legal_entity_name'],
          'vendor_code': ['code', 'vendorcode', 'vendor_code'],
          'business_type': ['businesstype', 'type', 'business'],
          'tax_id': ['taxid', 'tax', 'ein', 'tin'],
          'duns_number': ['duns', 'dunsnumber', 'duns_no'],
          'incorporation_date': ['incorporation', 'inc_date', 'date_incorporated'],
          'industry_sector': ['industry', 'sector'],
          'website': ['url', 'web', 'website_url'],
          'annual_revenue': ['revenue', 'annualrevenue'],
          'employee_count': ['employees', 'employee_count', 'headcount'],
          'headquarters_address': ['address', 'hq_address', 'location'],
          'vendor_category': ['category', 'vendorcategory'],
          'risk_level': ['risk', 'risklevel'],
          'status': ['status'],
          'description': ['desc', 'notes', 'description'],
        }
        if (variations[normalized]) {
          variations[normalized].forEach(variation => {
            map[variation] = index
          })
        }
      })
      return map
    }

    // Valid risk level options (matching dropdown values)
    const validRiskLevels = ['low', 'medium', 'high', 'critical']

    // Normalize risk level value to match dropdown options (case-insensitive)
    const normalizeRiskLevel = (value) => {
      if (!value) return ''
      
      const normalizedValue = value.trim()
      const lowerValue = normalizedValue.toLowerCase()
      
      // Case-insensitive matching to dropdown options
      if (lowerValue === 'low') return 'low'
      if (lowerValue === 'medium') return 'medium'
      if (lowerValue === 'high') return 'high'
      if (lowerValue === 'critical') return 'critical'
      
      // Return empty string if no match
      return ''
    }

    // Helper function to add value to dropdown options if not exists
    const addToBusinessTypes = (value) => {
      if (value && !businessTypes.value.includes(value)) {
        businessTypes.value.push(value)
        businessTypes.value.sort()
      }
    }

    const addToIndustrySectors = (value) => {
      if (value && !industrySectors.value.includes(value)) {
        industrySectors.value.push(value)
        industrySectors.value.sort()
      }
    }

    const addToVendorCategories = (value) => {
      if (value && !vendorCategories.value.includes(value)) {
        vendorCategories.value.push(value)
        vendorCategories.value.sort()
      }
    }

    // Handle input events to add new values
    const handleBusinessTypeInput = (event) => {
      const value = event.target.value.trim()
      if (value && !businessTypes.value.includes(value)) {
        addToBusinessTypes(value)
      }
    }

    const handleIndustrySectorInput = (event) => {
      const value = event.target.value.trim()
      if (value && !industrySectors.value.includes(value)) {
        addToIndustrySectors(value)
      }
    }

    const handleVendorCategoryInput = (event) => {
      const value = event.target.value.trim()
      if (value && !vendorCategories.value.includes(value)) {
        addToVendorCategories(value)
      }
    }

    // Parse JSON contacts data
    const parseContactsFromJSON = (contactsJson) => {
      if (!contactsJson) return []
      
      try {
        // Handle string JSON
        let contactsData = contactsJson
        if (typeof contactsJson === 'string') {
          contactsData = JSON.parse(contactsJson)
        }
        
        // Ensure it's an array
        if (!Array.isArray(contactsData)) {
          contactsData = [contactsData]
        }
        
        // Map JSON contact structure to form contact structure
        return contactsData.map((contact, index) => {
          const contactId = Date.now().toString() + Math.random().toString(36).substr(2, 9) + index
          return {
            id: contactId,
            name: contact.name || '',
            email: contact.email || '',
            phone: contact.phone || '',
            role: contact.role || '',
            isPrimary: contact.primary_contact === true || contact.isPrimary === true || false,
            isEditing: false // Don't show in edit mode, show as saved
          }
        })
      } catch (error) {
        console.error('Error parsing contacts JSON:', error)
        return []
      }
    }

    // Map CSV row to vendor data
    const mapRowToVendorData = (values, headerMap) => {
      const getValue = (key) => {
        const index = headerMap[key]
        return index !== undefined && values[index] ? values[index].trim() : ''
      }

      const businessType = getValue('business_type') || getValue('type')
      const industrySector = getValue('industry_sector') || getValue('industry')
      const vendorCategory = getValue('vendor_category') || getValue('category')
      const contactsJson = getValue('contacts') || getValue('vendor_contacts')

      // Add new values to dropdowns if they don't exist
      if (businessType) addToBusinessTypes(businessType)
      if (industrySector) addToIndustrySectors(industrySector)
      if (vendorCategory) addToVendorCategories(vendorCategory)

      // Parse contacts from JSON
      const contacts = parseContactsFromJSON(contactsJson)

      return {
        company_name: getValue('company_name') || getValue('company') || getValue('vendor_name'),
        legal_name: getValue('legal_name') || getValue('legal'),
        vendor_code: getValue('vendor_code') || getValue('code') || generateVendorCode(),
        business_type: businessType,
        tax_id: getValue('tax_id') || getValue('taxid'),
        duns_number: getValue('duns_number') || getValue('duns'),
        incorporation_date: getValue('incorporation_date') || getValue('incorporation'),
        industry_sector: industrySector,
        website: getValue('website') || getValue('url'),
        annual_revenue: getValue('annual_revenue') ? parseFloat(getValue('annual_revenue')) : null,
        employee_count: getValue('employee_count') ? parseInt(getValue('employee_count')) : null,
        headquarters_address: getValue('headquarters_address') || getValue('address'),
        vendor_category: vendorCategory,
        risk_level: normalizeRiskLevel(getValue('risk_level') || getValue('risk')),
        status: 'pending', // Always set to pending for bulk uploaded vendors
        description: getValue('description') || getValue('desc'),
        is_critical_vendor: ['true', '1', 'yes'].includes((getValue('is_critical_vendor') || '').toLowerCase()),
        has_data_access: ['true', '1', 'yes'].includes((getValue('has_data_access') || '').toLowerCase()),
        has_system_access: ['true', '1', 'yes'].includes((getValue('has_system_access') || '').toLowerCase()),
        contacts: contacts // Include parsed contacts
      }
    }

    // Map Excel row to vendor data (similar to CSV but uses object keys)
    const mapExcelRowToVendorData = (row) => {
      const getValue = (keys) => {
        for (const key of keys) {
          if (row[key]) return String(row[key]).trim()
          // Try case-insensitive match
          const found = Object.keys(row).find(k => k.toLowerCase().replace(/\s+/g, '_') === key.toLowerCase())
          if (found) return String(row[found]).trim()
        }
        return ''
      }

      const businessType = getValue(['Business Type', 'business_type', 'Type']) || ''
      const industrySector = getValue(['Industry Sector', 'industry_sector', 'Industry']) || ''
      const vendorCategory = getValue(['Vendor Category', 'vendor_category', 'Category']) || ''
      const contactsJson = getValue(['Contacts', 'contacts', 'Vendor Contacts', 'vendor_contacts']) || ''

      // Add new values to dropdowns if they don't exist
      if (businessType) addToBusinessTypes(businessType)
      if (industrySector) addToIndustrySectors(industrySector)
      if (vendorCategory) addToVendorCategories(vendorCategory)

      // Parse contacts from JSON
      const contacts = parseContactsFromJSON(contactsJson)

      return {
        company_name: getValue(['Company Name', 'company_name', 'Company', 'Vendor Name']) || '',
        legal_name: getValue(['Legal Name', 'legal_name', 'Legal Name']) || '',
        vendor_code: getValue(['Vendor Code', 'vendor_code', 'Code']) || generateVendorCode(),
        business_type: businessType,
        tax_id: getValue(['Tax ID', 'tax_id', 'Tax ID', 'EIN']) || '',
        duns_number: getValue(['DUNS Number', 'duns_number', 'DUNS']) || '',
        incorporation_date: getValue(['Incorporation Date', 'incorporation_date']) || '',
        industry_sector: industrySector,
        website: getValue(['Website', 'website', 'URL']) || '',
        annual_revenue: getValue(['Annual Revenue', 'annual_revenue']) ? parseFloat(getValue(['Annual Revenue', 'annual_revenue'])) : null,
        employee_count: getValue(['Employee Count', 'employee_count', 'Employees']) ? parseInt(getValue(['Employee Count', 'employee_count', 'Employees'])) : null,
        headquarters_address: getValue(['Headquarters Address', 'headquarters_address', 'Address']) || '',
        vendor_category: vendorCategory,
        risk_level: normalizeRiskLevel(getValue(['Risk Level', 'risk_level', 'Risk']) || ''),
        status: 'pending', // Always set to pending for bulk uploaded vendors
        description: getValue(['Description', 'description', 'Notes']) || '',
        is_critical_vendor: ['true', '1', 'yes'].includes((getValue(['Is Critical Vendor', 'is_critical_vendor']) || '').toLowerCase()),
        has_data_access: ['true', '1', 'yes'].includes((getValue(['Has Data Access', 'has_data_access']) || '').toLowerCase()),
        has_system_access: ['true', '1', 'yes'].includes((getValue(['Has System Access', 'has_system_access']) || '').toLowerCase()),
        contacts: contacts // Include parsed contacts
      }
    }

    // Add contact to vendor form
    const addContact = (formId) => {
      const form = vendorForms.value.find(f => f.id === formId)
      if (form) {
        const contactId = Date.now().toString() + Math.random().toString(36).substr(2, 9)
        form.contacts.push({
          id: contactId,
          name: '',
          email: '',
          phone: '',
          role: '',
          isPrimary: false,
          isEditing: true
        })
      }
    }

    // Save contact
    const saveContact = (formId, contactId) => {
      const form = vendorForms.value.find(f => f.id === formId)
      if (form) {
        const contact = form.contacts.find(c => c.id === contactId)
        if (contact) {
          contact.isEditing = false
        }
      }
    }

    // Cancel edit contact
    const cancelEditContact = (formId, contactId) => {
      const form = vendorForms.value.find(f => f.id === formId)
      if (form) {
        const contact = form.contacts.find(c => c.id === contactId)
        if (contact) {
          if (!contact.name && !contact.email) {
            // New contact with no data - remove it
            removeContact(formId, contactId)
          } else {
            contact.isEditing = false
          }
        }
      }
    }

    // Edit contact
    const editContact = (formId, contactId) => {
      const form = vendorForms.value.find(f => f.id === formId)
      if (form) {
        const contact = form.contacts.find(c => c.id === contactId)
        if (contact) {
          contact.isEditing = true
        }
      }
    }

    // Remove contact
    const removeContact = (formId, contactId) => {
      const form = vendorForms.value.find(f => f.id === formId)
      if (form) {
        form.contacts = form.contacts.filter(c => c.id !== contactId)
      }
    }

    // Add document to vendor form
    const addDocument = (formId) => {
      const form = vendorForms.value.find(f => f.id === formId)
      if (form) {
        const docId = Date.now().toString() + Math.random().toString(36).substr(2, 9)
        form.documents.push({
          id: docId,
          name: '',
          type: '',
          version: '',
          status: 'Pending',
          expiryDate: '',
          fileName: '',
          file: null,
          isEditing: true
        })
      }
    }

    // Handle file upload
    const handleFileUpload = (event, formId, docId) => {
      const form = vendorForms.value.find(f => f.id === formId)
      if (form) {
        const doc = form.documents.find(d => d.id === docId)
        if (doc) {
          const file = event.target.files[0]
          if (file) {
            // Validate file size (max 100MB)
            const maxSize = 100 * 1024 * 1024
            if (file.size > maxSize) {
              showMessage('error', 'File size cannot exceed 100MB')
              event.target.value = ''
              return
            }
            
            doc.file = file
            doc.fileName = file.name
            if (!doc.name) {
              doc.name = file.name
            }
          }
        }
      }
    }

    // Save document
    const saveDocument = (formId, docId) => {
      const form = vendorForms.value.find(f => f.id === formId)
      if (form) {
        const doc = form.documents.find(d => d.id === docId)
        if (doc) {
          doc.isEditing = false
        }
      }
    }

    // Cancel edit document
    const cancelEditDocument = (formId, docId) => {
      const form = vendorForms.value.find(f => f.id === formId)
      if (form) {
        const doc = form.documents.find(d => d.id === docId)
        if (doc) {
          if (!doc.name && !doc.file) {
            // New document with no data - remove it
            removeDocument(formId, docId)
          } else {
            doc.isEditing = false
          }
        }
      }
    }

    // Edit document
    const editDocument = (formId, docId) => {
      const form = vendorForms.value.find(f => f.id === formId)
      if (form) {
        const doc = form.documents.find(d => d.id === docId)
        if (doc) {
          doc.isEditing = true
        }
      }
    }

    // Remove document
    const removeDocument = (formId, docId) => {
      const form = vendorForms.value.find(f => f.id === formId)
      if (form) {
        form.documents = form.documents.filter(d => d.id !== docId)
      }
    }

    // Get document status class
    const getDocumentStatusClass = (status) => {
      switch (status) {
        case 'Approved': return 'vendor_badge-success'
        case 'Pending': return 'vendor_badge-warning'
        case 'Rejected': return 'vendor_badge-destructive'
        default: return 'vendor_badge-default'
      }
    }

    // Format field name for error messages
    const formatFieldName = (fieldName) => {
      return fieldName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
    }

    // Show message
    const showMessage = async (type, text) => {
      switch (type) {
        case 'success':
          await showSuccess('Success', text)
          PopupService.success(text, 'Success')
          break
        case 'error':
          await showError('Error', text)
          PopupService.error(text, 'Error')
          break
        case 'warning':
          await showWarning('Warning', text)
          PopupService.warning(text, 'Warning')
          break
        default:
          await showInfo('Info', text)
          PopupService.info(text, 'Info')
      }
    }

    // Validate vendor form
    const validateVendorForm = (form) => {
      const errors = {}
      
      if (!form.data.company_name || form.data.company_name.trim() === '') {
        errors.company_name = 'Company name is required'
      }

      return errors
    }

    // Submit single vendor
    const submitSingleVendor = async (formId) => {
      const form = vendorForms.value.find(f => f.id === formId)
      if (!form) {
        showMessage('error', 'Vendor form not found.')
        return
      }

      // Check if already submitted
      if (form.submitted) {
        showMessage('warning', 'This vendor has already been submitted.')
        return
      }

      // Set submitting state for this specific form
      form.isSubmitting = true
      form.errors = {}

      try {
        // Validate the form
        form.errors = validateVendorForm(form)
        if (Object.keys(form.errors).length > 0) {
          showMessage('error', 'Please fix errors in the form before submitting.')
          form.isSubmitting = false
          return
        }

        // Get user ID from localStorage
        const userId = localStorage.getItem('user_id') || localStorage.getItem('userId')
        if (!userId) {
          showMessage('error', 'User ID not found. Please log in again.')
          form.isSubmitting = false
          return
        }

        // Prepare vendor data
        const vendorData = {
          ...form.data,
          UserId: parseInt(userId),
          annual_revenue: form.data.annual_revenue === '' || form.data.annual_revenue === null ? null : Number(form.data.annual_revenue),
          employee_count: form.data.employee_count === '' || form.data.employee_count === null ? null : Number(form.data.employee_count),
          contacts: form.contacts.map(c => ({
            name: c.name,
            email: c.email,
            phone: c.phone,
            role: c.role,
            isPrimary: c.isPrimary
          })),
          documents: form.documents.map(d => ({
            name: d.name,
            type: d.type,
            version: d.version,
            status: d.status,
            expiry_date: d.expiryDate || null,
            document_name: d.name,
            document_type: d.type
          })),
          status: form.data.status || 'pending'
        }

        // Submit to API
        const response = await api.post(
          getTprmApiUrl('v1/management/temp-vendors/'),
          vendorData
        )

        if (response.data && (response.data.status === 'success' || response.status === 201)) {
          form.submitted = true
          showMessage('success', 'Vendor submitted successfully!')
          
          // Optionally remove the form after a delay or keep it marked as submitted
          setTimeout(() => {
            // Keep the form but mark it as submitted
            // User can still view it but cannot edit
          }, 1000)
        } else {
          form.errors = { general: response.data?.message || 'Failed to submit vendor' }
          showMessage('error', response.data?.message || 'Failed to submit vendor')
        }
      } catch (error) {
        console.error('Error submitting vendor:', error)
        const errorMessage = error.response?.data?.message || error.response?.data?.error || error.message || 'Failed to submit vendor'
        form.errors = { general: errorMessage }
        showMessage('error', errorMessage)
      } finally {
        form.isSubmitting = false
      }
    }

    // Submit all vendors
    const submitAllVendors = async () => {
      if (vendorForms.value.length === 0) {
        showMessage('error', 'Please add at least one vendor before submitting.')
        return
      }

      // Filter out already submitted vendors
      const unsubmittedVendors = vendorForms.value.filter(form => !form.submitted)
      
      if (unsubmittedVendors.length === 0) {
        showMessage('info', 'All vendors have already been submitted.')
        return
      }

      isSubmitting.value = true
      let successCount = 0
      let errorCount = 0
      const errors = []

      try {
        // Validate only unsubmitted forms
        for (const form of unsubmittedVendors) {
          form.errors = validateVendorForm(form)
          if (Object.keys(form.errors).length > 0) {
            errorCount++
          }
        }

        if (errorCount > 0) {
          showMessage('error', `Please fix errors in ${errorCount} vendor form${errorCount !== 1 ? 's' : ''} before submitting.`)
          isSubmitting.value = false
          return
        }

        // Get user ID from localStorage
        const userId = localStorage.getItem('user_id') || localStorage.getItem('userId')
        if (!userId) {
          showMessage('error', 'User ID not found. Please log in again.')
          isSubmitting.value = false
          return
        }

        // Submit each unsubmitted vendor form
        for (const form of unsubmittedVendors) {
          try {
            // Prepare vendor data
            const vendorData = {
              ...form.data,
              UserId: parseInt(userId),
              annual_revenue: form.data.annual_revenue === '' || form.data.annual_revenue === null ? null : Number(form.data.annual_revenue),
              employee_count: form.data.employee_count === '' || form.data.employee_count === null ? null : Number(form.data.employee_count),
              contacts: form.contacts.map(c => ({
                name: c.name,
                email: c.email,
                phone: c.phone,
                role: c.role,
                isPrimary: c.isPrimary
              })),
              documents: form.documents.map(d => ({
                name: d.name,
                type: d.type,
                version: d.version,
                status: d.status,
                expiry_date: d.expiryDate || null,
                document_name: d.name,
                document_type: d.type
              })),
              status: form.data.status || 'pending'
            }

            // Submit to API using tprm_frontend's api instance which handles JWT authentication
            const response = await api.post(
              getTprmApiUrl('v1/management/temp-vendors/'),
              vendorData
            )

            if (response.data && (response.data.status === 'success' || response.status === 201)) {
              form.submitted = true
              successCount++
            } else {
              form.errors = { general: response.data?.message || 'Failed to submit vendor' }
              errorCount++
            }
          } catch (error) {
            console.error('Error submitting vendor:', error)
            const errorMessage = error.response?.data?.message || error.response?.data?.error || error.message || 'Failed to submit vendor'
            form.errors = { general: errorMessage }
            errors.push(errorMessage)
            errorCount++
          }
        }

        // Show result message
        const submittedCount = vendorForms.value.filter(f => f.submitted).length
        const totalCount = vendorForms.value.length
        
        if (successCount > 0 && errorCount === 0) {
          if (submittedCount === totalCount) {
            showMessage('success', `Successfully submitted ${successCount} vendor${successCount !== 1 ? 's' : ''}! All vendors have been submitted.`)
            // Optionally clear forms after successful submission
            setTimeout(() => {
              vendorForms.value = vendorForms.value.filter(f => !f.submitted)
              if (vendorForms.value.length === 0) {
                addNewVendorForm()
              }
            }, 2000)
          } else {
            showMessage('success', `Successfully submitted ${successCount} vendor${successCount !== 1 ? 's' : ''}! ${submittedCount} of ${totalCount} vendors are now submitted.`)
          }
        } else if (successCount > 0 && errorCount > 0) {
          showMessage('warning', `Submitted ${successCount} vendor${successCount !== 1 ? 's' : ''} successfully, but ${errorCount} failed. ${submittedCount} of ${totalCount} vendors are now submitted.`)
        } else {
          showMessage('error', `Failed to submit ${errorCount} vendor${errorCount !== 1 ? 's' : ''}. Please check the errors and try again.`)
        }
      } catch (error) {
        console.error('Error in submitAllVendors:', error)
        showMessage('error', 'An error occurred while submitting vendors. Please try again.')
      } finally {
        isSubmitting.value = false
      }
    }

// Initialize with one empty form
onMounted(async () => {
  try {
    // Log page view
    await loggingService.logPageView('Vendor', 'Add Vendors')
    
    // Don't auto-add form on mount, let user click "Add Another Vendor" first
    // addNewVendorForm()
  } catch (error) {
    console.error('Error during component initialization:', error)
  }
})
</script>

<style>
@import '../vendor/VendorRegistration.css';

/* Header with Summary Stats */
.vendor_registration-header {
  display: flex !important;
  justify-content: space-between !important;
  align-items: flex-start !important;
  margin-bottom: 1.5rem !important;
  padding-bottom: 1rem !important;
  border-bottom: 2px solid #e5e7eb !important;
}

.vendor_summary-stats {
  display: flex !important;
  gap: 1.5rem !important;
  align-items: center !important;
}

.vendor_stat-item {
  display: flex !important;
  align-items: center !important;
  gap: 0.5rem !important;
}

.vendor_stat-label {
  font-size: 0.875rem !important;
  color: #6b7280 !important;
  font-weight: 500 !important;
}

.vendor_stat-value {
  font-size: 1.125rem !important;
  font-weight: 600 !important;
  color: #111827 !important;
}

.vendor_stat-value-warning {
  color: #f59e0b !important;
}

/* Action Buttons Bar */
.vendor_action-buttons-bar {
  display: flex !important;
  gap: 0.75rem !important;
  margin-bottom: 1.5rem !important;
  flex-wrap: wrap !important;
}

.vendor_btn-submit-all {
  position: relative !important;
  margin-left: auto !important;
}

.vendor_badge-count {
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  min-width: 1.5rem !important;
  height: 1.5rem !important;
  padding: 0 0.5rem !important;
  margin-left: 0.5rem !important;
  background-color: #ffffff !important;
  color: #3b82f6 !important;
  border-radius: 9999px !important;
  font-size: 0.75rem !important;
  font-weight: 600 !important;
}

/* Table Styles */
.vendor_table-container {
  background: white !important;
  border-radius: 0.5rem !important;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1) !important;
  overflow: hidden !important;
  margin-bottom: 2rem !important;
}

.vendor_table {
  width: 100% !important;
  border-collapse: collapse !important;
}

.vendor_table thead {
  background-color: #f9fafb !important;
  border-bottom: 2px solid #e5e7eb !important;
}

.vendor_table th {
  padding: 0.75rem 1rem !important;
  text-align: left !important;
  font-size: 0.875rem !important;
  font-weight: 600 !important;
  color: #374151 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.05em !important;
}

.vendor_table tbody tr {
  border-bottom: 1px solid #e5e7eb !important;
  transition: background-color 0.15s ease !important;
}

.vendor_table tbody tr:hover {
  background-color: #f9fafb !important;
}

.vendor_table td {
  padding: 1rem !important;
  font-size: 0.875rem !important;
  color: #111827 !important;
}

/* Risk Level Badges */
.vendor_risk-badge {
  display: inline-block !important;
  padding: 0.25rem 0.75rem !important;
  border-radius: 9999px !important;
  font-size: 0.75rem !important;
  font-weight: 500 !important;
  text-transform: capitalize !important;
}

.vendor_risk-low {
  background-color: #d1fae5 !important;
  color: #065f46 !important;
}

.vendor_risk-medium {
  background-color: #fef3c7 !important;
  color: #92400e !important;
}

.vendor_risk-high {
  background-color: #fee2e2 !important;
  color: #991b1b !important;
}

.vendor_risk-critical {
  background-color: #fecaca !important;
  color: #7f1d1d !important;
  font-weight: 600 !important;
}

/* Status Badges */
.vendor_status-badge {
  display: inline-block !important;
  padding: 0.25rem 0.75rem !important;
  border-radius: 9999px !important;
  font-size: 0.75rem !important;
  font-weight: 500 !important;
  text-transform: capitalize !important;
}

.vendor_status-pending {
  background-color: #fed7aa !important;
  color: #9a3412 !important;
}

.vendor_status-approved {
  background-color: #d1fae5 !important;
  color: #065f46 !important;
}

.vendor_status-rejected {
  background-color: #fee2e2 !important;
  color: #991b1b !important;
}

/* Actions Cell */
.vendor_actions-cell {
  display: flex !important;
  gap: 0.5rem !important;
  align-items: center !important;
}

.vendor_action-btn {
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  width: 2rem !important;
  height: 2rem !important;
  padding: 0 !important;
  border: 1px solid #e5e7eb !important;
  border-radius: 0.375rem !important;
  background-color: white !important;
  color: #6b7280 !important;
  cursor: pointer !important;
  transition: all 0.15s ease !important;
}

.vendor_action-btn:hover {
  background-color: #f3f4f6 !important;
  border-color: #d1d5db !important;
}

.vendor_action-edit:hover {
  background-color: #eff6ff !important;
  border-color: #3b82f6 !important;
  color: #3b82f6 !important;
}

.vendor_action-delete:hover {
  background-color: #fef2f2 !important;
  border-color: #ef4444 !important;
  color: #ef4444 !important;
}

.vendor_action-view:hover {
  background-color: #f0fdf4 !important;
  border-color: #10b981 !important;
  color: #10b981 !important;
}

/* Modal Styles */
.vendor_modal-overlay {
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  right: 0 !important;
  bottom: 0 !important;
  background-color: rgba(0, 0, 0, 0.5) !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  z-index: 1000 !important;
  padding: 1rem !important;
}

.vendor_modal-content {
  background: white !important;
  border-radius: 0.5rem !important;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1) !important;
  max-width: 90vw !important;
  max-height: 90vh !important;
  width: 100% !important;
  display: flex !important;
  flex-direction: column !important;
  overflow: hidden !important;
}

.vendor_modal-header {
  display: flex !important;
  justify-content: space-between !important;
  align-items: center !important;
  padding: 1.5rem !important;
  border-bottom: 1px solid #e5e7eb !important;
}

.vendor_modal-title {
  font-size: 1.25rem !important;
  font-weight: 600 !important;
  color: #111827 !important;
}

.vendor_modal-close {
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  width: 2rem !important;
  height: 2rem !important;
  border: none !important;
  background: transparent !important;
  color: #6b7280 !important;
  cursor: pointer !important;
  border-radius: 0.375rem !important;
  transition: all 0.15s ease !important;
}

.vendor_modal-close:hover {
  background-color: #f3f4f6 !important;
  color: #111827 !important;
}

.vendor_modal-body {
  flex: 1 !important;
  overflow-y: auto !important;
  padding: 1.5rem !important;
}

.vendor_modal-footer {
  display: flex !important;
  justify-content: flex-end !important;
  gap: 0.75rem !important;
  padding: 1.5rem !important;
  border-top: 1px solid #e5e7eb !important;
}

/* Vendor Tabs Wrapper */
.vendor_vendor-tabs-wrapper {
  margin-bottom: 1.5rem !important;
  border-bottom: 2px solid #e5e7eb !important;
}

.vendor_vendor-tabs {
  display: flex !important;
  gap: 0.5rem !important;
  overflow-x: auto !important;
  padding: 0 0.5rem !important;
  scrollbar-width: thin !important;
}

.vendor_vendor-tab {
  display: flex !important;
  align-items: center !important;
  gap: 0.5rem !important;
  padding: 0.75rem 1.25rem !important;
  background-color: #f3f4f6 !important;
  border: 1px solid #e5e7eb !important;
  border-bottom: none !important;
  border-radius: 0.5rem 0.5rem 0 0 !important;
  cursor: pointer !important;
  transition: all 0.2s ease !important;
  white-space: nowrap !important;
  position: relative !important;
  font-weight: 500 !important;
  color: #6b7280 !important;
}

.vendor_vendor-tab:hover {
  background-color: #e5e7eb !important;
  color: #374151 !important;
}

.vendor_vendor-tab-active {
  background-color: #ffffff !important;
  border-color: #3b82f6 !important;
  border-bottom-color: #ffffff !important;
  color: #3b82f6 !important;
  margin-bottom: -2px !important;
  z-index: 1 !important;
}

.vendor_vendor-tab-active:hover {
  background-color: #ffffff !important;
  color: #2563eb !important;
}

.vendor_vendor-tab-badge {
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  width: 1.25rem !important;
  height: 1.25rem !important;
  border-radius: 50% !important;
  font-size: 0.75rem !important;
  font-weight: bold !important;
}

.vendor_vendor-tab-close {
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  width: 1.25rem !important;
  height: 1.25rem !important;
  border-radius: 50% !important;
  background-color: transparent !important;
  border: none !important;
  cursor: pointer !important;
  padding: 0 !important;
  color: #6b7280 !important;
  transition: all 0.2s ease !important;
  margin-left: 0.25rem !important;
}

.vendor_vendor-tab-close:hover {
  background-color: #ef4444 !important;
  color: #ffffff !important;
}

.vendor_vendor-tab-active .vendor_vendor-tab-close {
  color: #3b82f6 !important;
}

.vendor_vendor-tab-active .vendor_vendor-tab-close:hover {
  background-color: #ef4444 !important;
  color: #ffffff !important;
}

/* Vendor Forms Container */
.vendor_forms-container {
  display: flex !important;
  flex-direction: column !important;
  gap: 2rem !important;
}

/* Error Messages */
.vendor_error-messages {
  margin: 1rem 1.5rem !important;
  padding: 1rem !important;
  background-color: #fef2f2 !important;
  border: 1px solid #fecaca !important;
  border-radius: 0.375rem !important;
}

.vendor_error-message {
  display: flex !important;
  align-items: center !important;
  color: #991b1b !important;
  margin-bottom: 0.5rem !important;
  font-size: 0.875rem !important;
}

.vendor_error-message:last-child {
  margin-bottom: 0 !important;
}

/* No Vendors State */
.vendor_no-vendors-state {
  display: flex !important;
  flex-direction: column !important;
  align-items: center !important;
  justify-content: center !important;
  padding: 3rem 2rem !important;
  text-align: center !important;
  color: #64748b !important;
  background: white !important;
  border: 2px dashed #e5e7eb !important;
  border-radius: 0.5rem !important;
  margin: 2rem 0 !important;
}

.vendor_no-vendors-icon {
  margin-bottom: 1rem !important;
  color: #cbd5e1 !important;
}

.vendor_no-contacts-icon {
  margin-bottom: 1rem !important;
  color: #cbd5e1 !important;
  display: flex !important;
  justify-content: center !important;
  align-items: center !important;
}

.vendor_no-contacts-icon svg {
  width: 2rem !important;
  height: 2rem !important;
}

.vendor_no-documents-icon {
  margin-bottom: 1rem !important;
  color: #cbd5e1 !important;
  display: flex !important;
  justify-content: center !important;
  align-items: center !important;
}

.vendor_no-documents-icon svg {
  width: 2rem !important;
  height: 2rem !important;
}

.vendor_no-vendors-title {
  font-size: 1.25rem !important;
  font-weight: 600 !important;
  color: #475569 !important;
  margin: 0 0 0.5rem 0 !important;
}

.vendor_no-vendors-text {
  font-size: 0.875rem !important;
  color: #64748b !important;
  margin: 0 0 1rem 0 !important;
}

/* Bulk Upload Button */
.vendor_btn-upload {
  cursor: pointer !important;
  position: relative !important;
  overflow: hidden !important;
}

.vendor_btn-upload-disabled {
  opacity: 0.6 !important;
  cursor: not-allowed !important;
}

.vendor_btn-upload input[type="file"] {
  position: absolute !important;
  opacity: 0 !important;
  width: 100% !important;
  height: 100% !important;
  cursor: pointer !important;
}

/* Searchable Select Styles */
.vendor_searchable-select {
  position: relative !important;
}

.vendor_searchable-select input[list] {
  width: 100% !important;
  padding: 0.75rem 1rem !important;
  font-size: 1rem !important;
  line-height: 1.5 !important;
  color: #495057 !important;
  background-color: #fff !important;
  background-clip: padding-box !important;
  border: 1px solid #ced4da !important;
  border-radius: 0.25rem !important;
  transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out !important;
}

.vendor_searchable-select input[list]:focus {
  border-color: #80bdff !important;
  outline: 0 !important;
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25) !important;
}

.vendor_searchable-select input[list]:hover {
  border-color: #adb5bd !important;
}

/* Readonly input styling */
.vendor_input[readonly] {
  background-color: #f8f9fa !important;
  cursor: not-allowed !important;
  color: #6c757d !important;
}

.vendor_input[readonly]:focus {
  border-color: #ced4da !important;
  box-shadow: none !important;
}

/* Form View Styles */
.vendor_form-view {
  width: 100% !important;
  display: flex !important;
  flex-direction: column !important;
}

.vendor_form-header {
  display: flex !important;
  justify-content: space-between !important;
  align-items: center !important;
  margin-bottom: 1.5rem !important;
  padding-bottom: 1rem !important;
  border-bottom: 2px solid #e5e7eb !important;
}

.vendor_form-header-left {
  display: flex !important;
  align-items: center !important;
  gap: 1rem !important;
}

.vendor_form-header-right {
  display: flex !important;
  align-items: center !important;
  gap: 0.75rem !important;
}

.vendor_back-button {
  display: flex !important;
  align-items: center !important;
  gap: 0.5rem !important;
  padding: 0.5rem 1rem !important;
  background-color: #f3f4f6 !important;
  border: 1px solid #e5e7eb !important;
  border-radius: 0.375rem !important;
  color: #374151 !important;
  cursor: pointer !important;
  transition: all 0.15s ease !important;
  font-size: 0.875rem !important;
  font-weight: 500 !important;
}

.vendor_back-button:hover {
  background-color: #e5e7eb !important;
  border-color: #d1d5db !important;
  color: #111827 !important;
}

.vendor_form-title-section {
  display: flex !important;
  flex-direction: column !important;
  gap: 0.25rem !important;
}

.vendor_form-title {
  font-size: 1.5rem !important;
  font-weight: 600 !important;
  color: #111827 !important;
  margin: 0 !important;
}

.vendor_form-code {
  font-size: 0.875rem !important;
  color: #6b7280 !important;
  margin: 0 !important;
}

.vendor_form-container {
  width: 100% !important;
  display: flex !important;
  flex-direction: column !important;
}

.vendor_form-content {
  width: 100% !important;
  display: flex !important;
  flex-direction: column !important;
}

.vendor_submit-button {
  display: flex !important;
  align-items: center !important;
  gap: 0.5rem !important;
  background-color: #3b82f6 !important;
  color: #ffffff !important;
  border-color: #3b82f6 !important;
}

.vendor_submit-button:hover {
  background-color: #2563eb !important;
  border-color: #2563eb !important;
  color: #ffffff !important;
}

.vendor_submit-button:disabled {
  background-color: #9ca3af !important;
  border-color: #9ca3af !important;
  color: #ffffff !important;
  opacity: 0.6 !important;
  cursor: not-allowed !important;
}

</style>

