<template>
  <div class="questionnaire-builder">
    <!-- Header Section -->
    <div class="builder-header">
      <div class="header-content">
        <div class="header-info">
          <h1 class="page-title">Questionnaire Builder</h1>
          <p class="page-subtitle">Create and manage vendor questionnaires</p>
          <div v-if="saveMessage" class="alert alert-success">{{ saveMessage }}</div>
          <div v-if="isLoading" class="alert alert-info">Loading...</div>
        </div>
        <div class="header-actions">
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="builder-content">
      <!-- Left Panel: Vendor Information -->
      <div class="left-panel">
        <div class="panel-card">
          <div class="card-header">
            <h2 class="card-title">Vendor Information</h2>
          </div>
          
          <div class="card-body">
            <!-- Vendor Selection -->
            <div class="form-group">
              <label class="form-label">Select Vendor</label>
              <select 
                :value="questionnaire.vendor_id" 
                @change="updateVendorId($event.target.value)"
                class="form-select"
              >
                <option value="">Select a vendor</option>
                <option 
                  v-for="vendor in vendors" 
                  :key="vendor.id" 
                  :value="vendor.id"
                >
                  {{ vendor.company_name }} ({{ vendor.vendor_code || 'No Code' }})
                </option>
              </select>
            </div>

            <!-- Data Source Selection -->
            <div class="form-group">
              <label class="form-label">View Data From</label>
              <select 
                v-model="selectedDataSource" 
                @change="handleDataSourceChange"
                class="form-select"
              >
                <option value="vendor-data">Vendor Data</option>
                <option value="rfp-data">RFP Data</option>
                <option value="screening-data">Screening Data</option>
              </select>
            </div>

            <div class="section-divider"></div>

            <!-- Key Attributes -->
            <div class="info-section scrollable-content">
              <h3 class="section-title">Key Attributes</h3>
              <div class="attribute-list">
                <!-- Vendor Data Display -->
                <template v-if="selectedDataSource === 'vendor-data'">
                  <div class="attribute-item">
                    <span class="attribute-label">Company:</span>
                    <span class="attribute-value">{{ selectedVendor?.company_name || 'No vendor selected' }}</span>
                  </div>
                  <div class="attribute-item">
                    <span class="attribute-label">Category:</span>
                    <span class="badge badge-secondary">{{ selectedVendor?.vendor_category || 'N/A' }}</span>
                  </div>
                  <div class="attribute-item">
                    <span class="attribute-label">Risk Level:</span>
                    <span class="badge" :class="getRiskLevelClass(selectedVendor?.risk_level)">
                      {{ selectedVendor?.risk_level || 'N/A' }}
                    </span>
                  </div>
                  <div class="attribute-item">
                    <span class="attribute-label">Status:</span>
                    <span class="badge" :class="getStatusClass(selectedVendor?.status)">
                      {{ selectedVendor?.status || 'N/A' }}
                    </span>
                  </div>
                  <div class="attribute-item" v-if="selectedVendor?.business_type">
                    <span class="attribute-label">Business Type:</span>
                    <span class="attribute-value">{{ selectedVendor.business_type }}</span>
                  </div>
                  <div class="attribute-item" v-if="selectedVendor?.industry_sector">
                    <span class="attribute-label">Industry:</span>
                    <span class="attribute-value">{{ selectedVendor.industry_sector }}</span>
                  </div>
                </template>

                <!-- RFP Data Display -->
                <template v-else-if="selectedDataSource === 'rfp-data'">
                  <div v-if="rfpData.length === 0" class="attribute-item">
                    <span class="attribute-value">No RFP responses found for this vendor</span>
                  </div>
                  <template v-else>
                    <div class="attribute-item">
                      <span class="attribute-label">Total RFP Responses:</span>
                      <span class="attribute-value">{{ rfpData.length }}</span>
                    </div>
                    <div class="attribute-item">
                      <span class="attribute-label">Latest Response:</span>
                      <span class="attribute-value">{{ formatDate(rfpData[0]?.submission_date) }}</span>
                    </div>
                    <div class="attribute-item">
                      <span class="attribute-label">Latest Status:</span>
                      <span class="badge" :class="getRFPStatusClass(rfpData[0]?.evaluation_status)">
                        {{ rfpData[0]?.evaluation_status || 'N/A' }}
                      </span>
                    </div>
                    <div class="attribute-item" v-if="rfpData[0]?.overall_score">
                      <span class="attribute-label">Latest Score:</span>
                      <span class="attribute-value">{{ rfpData[0].overall_score }}/100</span>
                    </div>
                    <div class="attribute-item" v-if="rfpData[0]?.proposed_value">
                      <span class="attribute-label">Latest Proposal:</span>
                      <span class="attribute-value">${{ formatCurrency(rfpData[0].proposed_value) }}</span>
                    </div>
                    
                    <!-- RFP Response Documents Section -->
                    <div class="attribute-item full-width">
                      <span class="attribute-label">Response Documents:</span>
                      <div class="documents-container">
                        <div v-if="rfpData.length === 0" class="no-documents">
                          <span class="attribute-value">No RFP responses found</span>
                        </div>
                        <div v-else class="documents-list">
                          <div v-for="(response, index) in rfpData" :key="response.response_id" class="response-documents">
                            <div class="response-group">
                              <div class="response-header">
                                <span class="response-title">Response #{{ response.response_id }} ({{ formatDate(response.submission_date) }})</span>
                                <span class="document-count" v-if="getResponseDocumentCount(response) > 0">
                                  {{ getResponseDocumentCount(response) }} item(s)
                                </span>
                              </div>
                              
                              <!-- All Data from response_documents (simplified structure) -->
                              <div class="response-data-container" v-if="getRequiredResponseData(response)">
                                <div v-for="(groupData, groupName) in getRequiredResponseData(response)" :key="groupName" class="data-group">
                                  <h4 class="group-title">{{ groupName }}</h4>
                                  <div v-for="(value, key) in groupData" :key="key" class="data-field">
                                    <span class="field-label">{{ formatJsonKey(key) }}:</span>
                                    <!-- Array of Objects -->
                                    <div v-if="Array.isArray(value) && value.length > 0 && typeof value[0] === 'object'" class="array-items">
                                      <div v-for="(item, index) in value" :key="index" class="array-item">
                                        <div v-for="(itemValue, itemKey) in item" :key="itemKey" class="field-row">
                                          <span class="field-label-small">{{ formatJsonKey(itemKey) }}:</span>
                                          <!-- URL Button -->
                                          <button 
                                            v-if="isUrl(itemValue)" 
                                            @click="openDocumentViewer(getUrlFromValue(itemValue), getFileNameFromUrl(itemValue))"
                                            class="url-button"
                                            type="button"
                                          >
                                            <svg class="icon-small" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                                            </svg>
                                            {{ getFileNameFromUrl(itemValue) }}
                                          </button>
                                          <!-- Regular Value -->
                                          <span v-else :class="'field-value field-value-' + getJsonValueType(itemValue)">{{ formatJsonValue(itemValue) }}</span>
                                        </div>
                                      </div>
                                    </div>
                                    <!-- Simple Array -->
                                    <div v-else-if="Array.isArray(value)" class="array-items">
                                      <div v-for="(item, index) in value" :key="index" class="array-item-simple">
                                        <!-- URL Button -->
                                        <button 
                                          v-if="isUrl(item)" 
                                          @click="openDocumentViewer(getUrlFromValue(item), getFileNameFromUrl(item))"
                                          class="url-button"
                                          type="button"
                                        >
                                          <svg class="icon-small" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                                          </svg>
                                          {{ getFileNameFromUrl(item) }}
                                        </button>
                                        <!-- Regular Value -->
                                        <span v-else :class="'field-value field-value-' + getJsonValueType(item)">{{ formatJsonValue(item) }}</span>
                                      </div>
                                    </div>
                                    <!-- Object -->
                                    <div v-else-if="typeof value === 'object' && value !== null" class="object-items">
                                      <div v-for="(objValue, objKey) in value" :key="objKey" class="field-row">
                                        <span class="field-label-small">{{ formatJsonKey(objKey) }}:</span>
                                        <!-- URL Button -->
                                        <button 
                                          v-if="isUrl(objValue)" 
                                          @click="openDocumentViewer(getUrlFromValue(objValue), getFileNameFromUrl(objValue))"
                                          class="url-button"
                                          type="button"
                                        >
                                          <svg class="icon-small" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                                          </svg>
                                          {{ getFileNameFromUrl(objValue) }}
                                        </button>
                                        <!-- Regular Value -->
                                        <span v-else :class="'field-value field-value-' + getJsonValueType(objValue)">{{ formatJsonValue(objValue) }}</span>
                                      </div>
                                    </div>
                                    <!-- Simple Value -->
                                    <div v-else class="simple-value-wrapper">
                                      <!-- URL Button -->
                                      <button 
                                        v-if="isUrl(value)" 
                                        @click="openDocumentViewer(getUrlFromValue(value), getFileNameFromUrl(value))"
                                        class="url-button"
                                        type="button"
                                      >
                                        <svg class="icon-small" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                                        </svg>
                                        {{ getFileNameFromUrl(value) }}
                                      </button>
                                      <!-- Regular Value -->
                                      <span v-else :class="'field-value field-value-' + getJsonValueType(value)">{{ formatJsonValue(value) }}</span>
                                    </div>
                                  </div>
                                </div>
                              </div>
                              
                              <!-- Documents from document_urls - Inline Viewer -->
                              <div v-if="getDocumentsFromUrls(response).length > 0" class="documents-section">
                                <div class="documents-header">
                                  <span class="documents-title">Attached Documents</span>
                                  <span class="documents-count">{{ getDocumentsFromUrls(response).length }} file(s)</span>
                                </div>
                                <div class="documents-list">
                                  <button 
                                    v-for="(document, docIndex) in getDocumentsFromUrls(response)" 
                                    :key="docIndex"
                                    @click="openDocumentViewer(getDocumentUrlFromData(document), getDocumentName(document))"
                                    class="document-link"
                                  >
                                    <svg class="icon-small" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                                    </svg>
                                    {{ getDocumentName(document) }}
                                  </button>
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </template>
                </template>

                <!-- Screening Data Display -->
                <template v-else-if="selectedDataSource === 'screening-data'">
                  <div v-if="screeningData.length === 0" class="attribute-item">
                    <span class="attribute-value">No screening results found for this vendor</span>
                  </div>
                  <template v-else>
                    <div class="attribute-item">
                      <span class="attribute-label">Total Screenings:</span>
                      <span class="attribute-value">{{ screeningData.length }}</span>
                    </div>
                    <div class="attribute-item">
                      <span class="attribute-label">Latest Screening:</span>
                      <span class="attribute-value">{{ formatDate(screeningData[0]?.screening_date) }}</span>
                    </div>
                    <div class="attribute-item">
                      <span class="attribute-label">Latest Type:</span>
                      <span class="badge badge-info">{{ screeningData[0]?.screening_type || 'N/A' }}</span>
                    </div>
                    <div class="attribute-item">
                      <span class="attribute-label">Latest Status:</span>
                      <span class="badge" :class="getScreeningStatusClass(screeningData[0]?.status)">
                        {{ screeningData[0]?.status || 'N/A' }}
                      </span>
                    </div>
                    <div class="attribute-item" v-if="screeningData[0]?.total_matches > 0">
                      <span class="attribute-label">Total Matches:</span>
                      <span class="attribute-value">{{ screeningData[0].total_matches }}</span>
                    </div>
                    <div class="attribute-item" v-if="screeningData[0]?.high_risk_matches > 0">
                      <span class="attribute-label">High Risk Matches:</span>
                      <span class="badge badge-danger">{{ screeningData[0].high_risk_matches }}</span>
                    </div>
                  </template>
                </template>
              </div>
            </div>

          </div>
        </div>
      </div>

      <!-- Right Panel: Questionnaire Details -->
      <div class="right-panel">
        <div class="panel-card">
          <div class="card-header">
            <h2 class="card-title">Questionnaire Details</h2>
          </div>
          
          <div class="card-body scrollable-content">
            <!-- Template Selection -->
            <div class="form-section">
              <div class="form-group full-width">
                <label class="form-label">Load from Template (Optional)</label>
                <select 
                  v-model="selectedTemplateId" 
                  @change="handleTemplateChange"
                  class="form-select"
                  :disabled="isLoadingTemplates"
                >
                  <option value="">Select a template...</option>
                  <option 
                    v-for="template in templates" 
                    :key="template.template_id" 
                    :value="template.template_id"
                  >
                    {{ template.template_name }} ({{ template.question_count || 0 }} questions)
                  </option>
                </select>
                <p v-if="isLoadingTemplates" class="form-help-text">Loading templates...</p>
                <p v-else-if="templates.length === 0" class="form-help-text">No templates available</p>
              </div>
            </div>

            <div class="section-divider"></div>

            <!-- Basic Information Form -->
            <div class="form-section">
              <div class="form-grid">
                <div class="form-group">
                  <label class="form-label">Questionnaire Name</label>
                  <input 
                    :value="questionnaire.questionnaire_name" 
                    @input="updateQuestionnaireName($event.target.value)"
                    class="form-input" 
                    placeholder="Enter questionnaire name"
                  />
                </div>
                
                <div class="form-group">
                  <label class="form-label">Type</label>
                  <select 
                    :value="questionnaire.questionnaire_type" 
                    @change="updateQuestionnaireType($event.target.value)"
                    class="form-select"
                  >
                    <option value="">Select type</option>
                    <option value="ONBOARDING">Onboarding</option>
                    <option value="ANNUAL">Annual Review</option>
                    <option value="INCIDENT">Incident Response</option>
                    <option value="CUSTOM">Custom</option>
                  </select>
                </div>
                
                <div class="form-group full-width">
                  <label class="form-label">Description</label>
                  <textarea 
                    :value="questionnaire.description" 
                    @input="updateDescription($event.target.value)"
                    class="form-textarea" 
                    placeholder="Enter questionnaire description"
                    rows="3"
                  ></textarea>
                </div>
                
                <div class="form-group">
                  <label class="form-label">Vendor Category</label>
                  <select 
                    :value="questionnaire.vendor_category_id" 
                    @change="updateVendorCategory($event.target.value)"
                    class="form-select"
                  >
                    <option value="">Select category</option>
                    <option 
                      v-for="category in vendorCategories" 
                      :key="category.value" 
                      :value="category.value"
                    >
                      {{ category.label }}
                    </option>
                  </select>
                </div>
                
                <div class="form-group">
                  <label class="form-label">Status</label>
                  <select 
                    :value="questionnaire.status" 
                    @change="updateStatus($event.target.value)"
                    class="form-select"
                  >
                    <option value="DRAFT">Draft</option>
                    <option value="ACTIVE">Active</option>
                    <option value="ARCHIVED">Archived</option>
                  </select>
                </div>
              </div>
            </div>

            <div class="section-divider"></div>

            <!-- Questions Section -->
            <div class="questions-section">
              <div class="section-header">
                <h3 class="section-title">Questions</h3>
                <button class="btn-add-question" @click="addQuestion">
                  <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v12m6-6H6"/>
                  </svg>
                  Add Question
                </button>
              </div>

              <!-- Questions List -->
              <div class="questions-list">
                <div v-for="(question, index) in questions" :key="question.id" class="question-item">
                  <div class="question-header">
                    <span class="question-number">Question {{ index + 1 }}</span>
                    <button class="btn-remove" @click="removeQuestion(question.id)">
                      <svg class="icon-small" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                      </svg>
                    </button>
                  </div>
                  
                  <div class="question-form">
                    <div class="form-group full-width">
                      <label class="form-label">Question Text</label>
                      <textarea 
                        :value="question.question_text" 
                        @input="updateQuestion(question.id, 'question_text', $event.target.value)"
                        class="form-textarea" 
                        placeholder="Enter your question"
                        rows="2"
                      ></textarea>
                    </div>
                    
                    <div class="question-grid">
                      <div class="form-group">
                        <label class="form-label">Question Type</label>
                        <select 
                          :value="question.question_type" 
                          @change="updateQuestion(question.id, 'question_type', $event.target.value)"
                          class="form-select"
                        >
                          <option value="TEXT">Text</option>
                          <option value="MULTIPLE_CHOICE">Multiple Choice</option>
                          <option value="CHECKBOX">Checkbox</option>
                          <option value="RATING">Rating</option>
                          <option value="FILE_UPLOAD">File Upload</option>
                          <option value="DATE">Date</option>
                          <option value="NUMBER">Number</option>
                        </select>
                      </div>
                      
                      <div class="form-group">
                        <label class="form-label">Category</label>
                        <input 
                          :value="question.question_category" 
                          @input="updateQuestion(question.id, 'question_category', $event.target.value)"
                          class="form-input" 
                          placeholder="e.g., Security, Compliance"
                        />
                      </div>
                      
                      <div class="form-group">
                        <label class="form-label">Scoring Weight</label>
                        <input 
                          :value="question.scoring_weight" 
                          @input="updateQuestion(question.id, 'scoring_weight', Math.min(parseFloat($event.target.value) || 1.0, 9.99))"
                          type="number" 
                          min="0" 
                          max="9.99" 
                          step="0.1" 
                          class="form-input"
                        />
                      </div>
                      
                      <div class="form-group">
                        <label class="form-label">Required</label>
                        <div class="checkbox-wrapper">
                          <input 
                            type="checkbox" 
                            :checked="question.is_required" 
                            @change="updateQuestion(question.id, 'is_required', $event.target.checked)"
                            class="form-checkbox"
                          />
                          <span class="checkbox-label">Required field</span>
                        </div>
                      </div>
                    </div>
                    
                    <!-- Dynamic Options Section -->
                    <div v-if="shouldShowOptions(question.question_type)" class="form-group full-width">
                      <label class="form-label">Options</label>
                      <div class="options-container">
                        <div 
                          v-for="(option, optionIndex) in getQuestionOptions(question)" 
                          :key="optionIndex" 
                          class="option-item"
                        >
                          <input 
                            :value="option" 
                            @input="updateQuestionOption(question.id, optionIndex, $event.target.value)"
                            class="form-input option-input" 
                            :placeholder="getOptionPlaceholder(question.question_type)"
                          />
                          <button 
                            type="button"
                            class="btn-remove-option" 
                            @click="removeQuestionOption(question.id, optionIndex)"
                            :disabled="getQuestionOptions(question).length <= 2"
                          >
                            <svg class="icon-small" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                            </svg>
                          </button>
                        </div>
                        <button 
                          type="button"
                          class="btn-add-option" 
                          @click="addQuestionOption(question.id)"
                        >
                          <svg class="icon-small" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v12m6-6H6"/>
                          </svg>
                          Add Option
                        </button>
                      </div>
                    </div>

                    <!-- Rating Scale Configuration -->
                    <div v-if="question.question_type === 'RATING'" class="form-group full-width">
                      <label class="form-label">Rating Scale</label>
                      <div class="rating-config">
                        <div class="rating-input-group">
                          <label class="rating-label">Min Value:</label>
                          <input 
                            :value="getRatingConfig(question).min || 1" 
                            @input="updateRatingConfig(question.id, 'min', parseInt($event.target.value) || 1)"
                            type="number" 
                            min="0" 
                            max="10" 
                            class="form-input rating-input"
                          />
                        </div>
                        <div class="rating-input-group">
                          <label class="rating-label">Max Value:</label>
                          <input 
                            :value="getRatingConfig(question).max || 5" 
                            @input="updateRatingConfig(question.id, 'max', parseInt($event.target.value) || 5)"
                            type="number" 
                            min="1" 
                            max="10" 
                            class="form-input rating-input"
                          />
                        </div>
                        <div class="rating-input-group">
                          <label class="rating-label">Step:</label>
                          <input 
                            :value="getRatingConfig(question).step || 1" 
                            @input="updateRatingConfig(question.id, 'step', parseFloat($event.target.value) || 1)"
                            type="number" 
                            min="0.1" 
                            max="1" 
                            step="0.1" 
                            class="form-input rating-input"
                          />
                        </div>
                        <div class="rating-input-group">
                          <label class="rating-label">Labels:</label>
                          <input 
                            :value="getRatingConfig(question).labels || ''" 
                            @input="updateRatingConfig(question.id, 'labels', $event.target.value)"
                            class="form-input rating-input" 
                            placeholder="e.g., Poor, Fair, Good, Very Good, Excellent"
                          />
                        </div>
                      </div>
                    </div>

                    <!-- File Upload Configuration -->
                    <div v-if="question.question_type === 'FILE_UPLOAD'" class="form-group full-width">
                      <label class="form-label">File Upload Settings</label>
                      <div class="file-config" style="border: 2px solid red; background: #fff5f5; padding: 10px;">
                        <p style="color: red; margin-bottom: 10px;">DEBUG: File Upload section is rendering</p>
                        <div class="file-input-group">
                          <label class="file-label">Allowed File Types:</label>
                          <input 
                            :value="question.options?.file?.allowedTypes || 'pdf,doc,docx,jpg,jpeg,png'"
                            @input="updateFileConfig(question.id, 'allowedTypes', $event.target.value)"
                            class="form-input file-input" 
                            placeholder="pdf,doc,docx,jpg,jpeg,png"
                          />
                        </div>
                        <div class="file-input-group">
                          <label class="file-label">Max File Size (MB):</label>
                          <input 
                            :value="question.options?.file?.maxSize || 10"
                            @input="updateFileConfig(question.id, 'maxSize', parseInt($event.target.value) || 10)"
                            type="number" 
                            min="1" 
                            max="100" 
                            class="form-input file-input"
                          />
                        </div>
                        <div class="file-input-group">
                          <label class="file-label">Max Files:</label>
                          <input 
                            :value="question.options?.file?.maxFiles || 1"
                            @input="updateFileConfig(question.id, 'maxFiles', parseInt($event.target.value) || 1)"
                            type="number" 
                            min="1" 
                            max="10" 
                            class="form-input file-input"
                          />
                        </div>
                      </div>
                    </div>

                    <!-- Number Input Configuration -->
                    <div v-if="question.question_type === 'NUMBER'" class="form-group full-width">
                      <label class="form-label">Number Input Settings</label>
                      <div class="number-config">
                        <div class="number-input-group">
                          <label class="number-label">Min Value:</label>
                          <input 
                            :value="getNumberConfig(question).min || ''" 
                            @input="updateNumberConfig(question.id, 'min', $event.target.value ? parseFloat($event.target.value) : null)"
                            type="number" 
                            class="form-input number-input"
                          />
                        </div>
                        <div class="number-input-group">
                          <label class="number-label">Max Value:</label>
                          <input 
                            :value="getNumberConfig(question).max || ''" 
                            @input="updateNumberConfig(question.id, 'max', $event.target.value ? parseFloat($event.target.value) : null)"
                            type="number" 
                            class="form-input number-input"
                          />
                        </div>
                        <div class="number-input-group">
                          <label class="number-label">Step:</label>
                          <input 
                            :value="getNumberConfig(question).step || ''" 
                            @input="updateNumberConfig(question.id, 'step', $event.target.value ? parseFloat($event.target.value) : null)"
                            type="number" 
                            step="0.01" 
                            class="form-input number-input"
                          />
                        </div>
                        <div class="number-input-group">
                          <label class="number-label">Unit:</label>
                          <input 
                            :value="getNumberConfig(question).unit || ''" 
                            @input="updateNumberConfig(question.id, 'unit', $event.target.value)"
                            class="form-input number-input" 
                            placeholder="e.g., $, %, kg, etc."
                          />
                        </div>
                      </div>
                    </div>

                    <div class="form-group full-width">
                      <label class="form-label">Help Text</label>
                      <input 
                        :value="question.help_text" 
                        @input="updateQuestion(question.id, 'help_text', $event.target.value)"
                        class="form-input" 
                        placeholder="Optional guidance for this question"
                      />
                    </div>
                  </div>
                </div>

                <!-- Empty State -->
                <div v-if="questions.length === 0" class="empty-state">
                  <div class="empty-icon">📝</div>
                  <h4 class="empty-title">No questions added yet</h4>
                  <p class="empty-text">Click "Add Question" to get started building your questionnaire</p>
                </div>
              </div>
            </div>

            <!-- Save and Activate Buttons at Bottom -->
            <div class="form-actions-bottom">
              <button class="btn-secondary" @click="saveDraft" :disabled="isSaving || isLoading">
                <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4"/>
                </svg>
                {{ isSaving ? 'Saving...' : 'Save Draft' }}
              </button>
              <button class="btn-primary" @click="activateQuestionnaire" :disabled="isSaving || isLoading">
                <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                </svg>
                {{ isSaving ? 'Activating...' : 'Activate Questionnaire' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Popup Modal -->
  <PopupModal />
  
  <!-- Document Viewer Modal -->
  <div v-if="documentViewer.show" class="document-viewer-overlay" @click.self="closeDocumentViewer">
    <div class="document-viewer-modal">
      <div class="document-viewer-header">
        <h3 class="document-viewer-title">{{ documentViewer.title }}</h3>
        <button @click="closeDocumentViewer" class="document-viewer-close">
          <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
          </svg>
        </button>
      </div>
      <div class="document-viewer-content">
        <iframe 
          :src="documentViewer.url" 
          class="document-viewer-iframe"
          frameborder="0"
        ></iframe>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useQuestionnaireStore } from '../../stores/questionnaires'
import { useRoute, useRouter } from 'vue-router'
import PopupModal from '@/popup/PopupModal.vue'
import { PopupService } from '@/popup/popupService'
import { useNotifications } from '@/composables/useNotifications'
import notificationService from '@/services/notificationService'

const route = useRoute()
const router = useRouter()
const questionnaireStore = useQuestionnaireStore()
const { showSuccess, showError, showWarning, showInfo } = useNotifications()

const selectedDataSource = ref('vendor-data')
const isSaving = ref(false)
const saveMessage = ref('')
const vendorCategories = ref([])
const vendors = ref([])
const templates = ref([])
const selectedTemplateId = ref('')
const isLoadingTemplates = ref(false)

// Document viewer state
const documentViewer = ref({
  show: false,
  url: '',
  title: ''
})

const openDocumentViewer = (url, title) => {
  documentViewer.value = {
    show: true,
    url: url,
    title: title || 'Document Viewer'
  }
}

const closeDocumentViewer = () => {
  documentViewer.value = {
    show: false,
    url: '',
    title: ''
  }
}

// Check if a value is a URL or contains a URL
const isUrl = (value) => {
  if (typeof value === 'string') {
    // Check for http/https URLs
    if (/^https?:\/\//.test(value)) return true
    // Check for S3 URLs
    if (/^https?:\/\/.*\.s3\..*\.amazonaws\.com/.test(value)) return true
    // Check for file paths that might be URLs
    if (/^https?:\/\/.*\.(pdf|doc|docx|jpg|jpeg|png|gif|zip|rar|txt|csv|xlsx|xls)/i.test(value)) return true
  }
  // Check if it's an object with a url property
  if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
    if (value.url && typeof value.url === 'string' && /^https?:\/\//.test(value.url)) {
      return true
    }
  }
  return false
}

// Get URL from value (handles both string URLs and objects with url property)
const getUrlFromValue = (value) => {
  if (typeof value === 'string' && isUrl(value)) {
    return value
  }
  if (typeof value === 'object' && value !== null && value.url) {
    return value.url
  }
  return null
}

// Extract filename from URL or value
const getFileNameFromUrl = (value) => {
  const url = getUrlFromValue(value)
  if (!url || typeof url !== 'string') {
    // If it's an object with a key property, use that
    if (typeof value === 'object' && value !== null && value.key) {
      const keyParts = value.key.split('/')
      return keyParts[keyParts.length - 1] || 'Document'
    }
    return 'Document'
  }
  try {
    const urlObj = new URL(url)
    const pathname = urlObj.pathname
    const filename = pathname.split('/').pop() || 'Document'
    return decodeURIComponent(filename)
  } catch {
    // If URL parsing fails, try to extract from string
    const parts = url.split('/')
    const lastPart = parts[parts.length - 1]
    if (lastPart && lastPart.includes('.')) {
      return lastPart.split('?')[0] // Remove query params
    }
    // Try to get from key if available
    if (typeof value === 'object' && value !== null && value.key) {
      const keyParts = value.key.split('/')
      return keyParts[keyParts.length - 1] || 'Document'
    }
    return 'Document'
  }
}

// Use store data
const questionnaire = computed(() => questionnaireStore.getCurrentQuestionnaire)
const questions = computed(() => questionnaireStore.getQuestions)
const isLoading = computed(() => questionnaireStore.isLoading)
const rfpData = computed(() => questionnaireStore.getRFPData)
const screeningData = computed(() => questionnaireStore.getScreeningData)

// Computed property for selected vendor
const selectedVendor = computed(() => {
  if (!questionnaire.value.vendor_id) return null
  return vendors.value.find(vendor => vendor.id == questionnaire.value.vendor_id)
})

// Computed property for all RFP documents
const allRFPDocuments = computed(() => {
  const allDocs = []
  rfpData.value.forEach(response => {
    if (response.response_documents && response.response_documents.documents) {
      response.response_documents.documents.forEach(doc => {
        allDocs.push({
          document: doc,
          responseId: response.response_id,
          submissionDate: response.submission_date
        })
      })
    }
  })
  return allDocs
})

// Get questionnaire ID from route if editing existing
const questionnaireId = ref(route.params.id || null)

// Watch for changes in data source or vendor selection
watch([selectedDataSource, () => questionnaire.value.vendor_id], async ([newDataSource, newVendorId]) => {
  console.log('VendorQuestionnaireBuilder - Data source or vendor changed:', {
    dataSource: newDataSource,
    vendorId: newVendorId,
    vendorIdType: typeof newVendorId
  })
  
  if (newVendorId) {
    if (newDataSource === 'rfp-data') {
      console.log('VendorQuestionnaireBuilder - Fetching RFP data for vendor:', newVendorId)
      await questionnaireStore.fetchVendorRFPData(newVendorId)
      console.log('VendorQuestionnaireBuilder - RFP data fetched:', questionnaireStore.getRFPData)
    } else if (newDataSource === 'screening-data') {
      console.log('VendorQuestionnaireBuilder - Fetching screening data for vendor:', newVendorId)
      await questionnaireStore.fetchVendorScreeningData(newVendorId)
    }
  } else {
    console.log('VendorQuestionnaireBuilder - No vendor selected, clearing data')
    // Data will be cleared automatically when fetchVendorRFPData is called with null/empty
  }
}, { immediate: true })

// Watch for question type changes to initialize options
watch(() => questions.value, (newQuestions) => {
  newQuestions.forEach(question => {
    if (!question.options) {
      question.options = {}
    }
    
    // Initialize options based on question type
    if (question.question_type === 'MULTIPLE_CHOICE' || question.question_type === 'CHECKBOX') {
      if (!question.options.choices) {
        question.options.choices = ['Option 1', 'Option 2']
      }
    } else if (question.question_type === 'RATING') {
      if (!question.options.rating) {
        question.options.rating = {
          min: 1,
          max: 5,
          step: 1,
          labels: ''
        }
      }
    } else if (question.question_type === 'FILE_UPLOAD') {
      if (!question.options.file) {
        question.options.file = {
          allowedTypes: 'pdf,doc,docx,jpg,jpeg,png',
          maxSize: 10,
          maxFiles: 1
        }
      }
    } else if (question.question_type === 'NUMBER') {
      if (!question.options.number) {
        question.options.number = {
          min: null,
          max: null,
          step: null,
          unit: ''
        }
      }
    }
  })
}, { deep: true, immediate: true })

onMounted(async () => {
  try {
    // Load vendor categories and vendors
    vendorCategories.value = await questionnaireStore.getVendorCategories()
    vendors.value = await questionnaireStore.fetchVendors()
    
    // Load templates
    await loadTemplates()
    
    if (questionnaireId.value) {
      // Load existing questionnaire
      try {
        await questionnaireStore.fetchQuestionnaire(questionnaireId.value)
      } catch (error) {
        console.error('Failed to load questionnaire:', error)
        // If questionnaire doesn't exist, show a user-friendly message
        if (error.message.includes('does not exist')) {
          PopupService.warning(`Questionnaire with ID ${questionnaireId.value} does not exist. Starting with a new questionnaire.`, 'Questionnaire Not Found')
          questionnaireStore.resetCurrentQuestionnaire()
          // Clear the questionnaire ID from the route
          router.replace({ name: 'VendorQuestionnaireBuilder' })
        } else {
          throw error
        }
      }
    } else {
      // Reset for new questionnaire
      questionnaireStore.resetCurrentQuestionnaire()
    }
  } catch (error) {
    console.error('Failed to load data:', error)
    PopupService.error('Failed to load questionnaire data. Please refresh the page.', 'Loading Error')
  }
})

const loadTemplates = async () => {
  isLoadingTemplates.value = true
  try {
    templates.value = await questionnaireStore.fetchTemplates({ is_active: 'true' })
    console.log('Loaded templates:', templates.value.length)
  } catch (error) {
    console.error('Failed to load templates:', error)
    PopupService.error('Failed to load questionnaire templates.', 'Loading Error')
    templates.value = []
  } finally {
    isLoadingTemplates.value = false
  }
}

const handleTemplateChange = async () => {
  if (!selectedTemplateId.value) {
    return
  }
  
  const loadTemplate = async () => {
    try {
      console.log('Loading template:', selectedTemplateId.value)
      
      // Load template data
      await questionnaireStore.loadTemplateData(selectedTemplateId.value)
      
      PopupService.success('Template loaded successfully!', 'Template Loaded')
    } catch (error) {
      console.error('Failed to load template:', error)
      PopupService.error('Failed to load template. Please try again.', 'Loading Error')
      selectedTemplateId.value = ''
    }
  }
  
  // Confirm before loading template (will overwrite current data)
  if (questions.value.length > 0 || questionnaire.value.questionnaire_name) {
    PopupService.confirm(
      'Loading a template will replace your current questionnaire data. Do you want to continue?',
      'Confirm Template Load',
      async () => {
        await loadTemplate()
      },
      () => {
        // Reset selection if user cancels
        selectedTemplateId.value = ''
      }
    )
  } else {
    // No existing data, load template directly
    await loadTemplate()
  }
}

const addQuestion = () => {
  questionnaireStore.addQuestion()
}

const removeQuestion = (id) => {
  questionnaireStore.removeQuestion(id)
}

const updateQuestionnaireField = (field, value) => {
  questionnaireStore.updateQuestionnaireField(field, value)
}

const updateQuestion = (id, field, value) => {
  questionnaireStore.updateQuestion(id, { [field]: value })
}

const saveDraft = async () => {
  if (!questionnaire.value.questionnaire_name.trim()) {
    PopupService.warning('Please enter a questionnaire name', 'Missing Name')
    return
  }

  // Questionnaire type is optional for drafts, but show a warning if missing
  if (!questionnaire.value.questionnaire_type && questions.value.length > 0) {
    PopupService.warning('Consider selecting a questionnaire type to categorize your questionnaire', 'Type Not Selected')
    // Don't return, let them continue saving the draft
  }

  isSaving.value = true
  saveMessage.value = ''
  
  try {
    console.log('=== SAVE DRAFT DEBUG ===')
    console.log('Questionnaire ID:', questionnaireId.value)
    console.log('Questionnaire data:', questionnaire.value)
    console.log('Questions count:', questions.value.length)
    console.log('Questions data:', questions.value)
    
    if (questionnaireId.value) {
      // Update existing questionnaire
      try {
        console.log('Updating existing questionnaire:', questionnaireId.value)
        const result = await questionnaireStore.saveDraft(
          questionnaireId.value,
          questionnaire.value,
          questions.value
        )
        console.log('Save draft result:', result)
        saveMessage.value = 'Draft saved successfully!'
        PopupService.success('Draft saved successfully!', 'Saved')
        
        // Create notification
        await notificationService.createVendorQuestionnaireNotification('questionnaire_draft_saved', {
          questionnaire_id: questionnaireId.value,
          questionnaire_title: questionnaire.value.questionnaire_name
        })
      } catch (error) {
        console.error('Error saving draft:', error)
        console.error('Error details:', {
          message: error.message,
          response: error.response,
          data: error.response?.data
        })
        
        if (error.message.includes('does not exist') || error.message.includes('404')) {
          // Questionnaire doesn't exist, create a new one
          console.log('Questionnaire does not exist, creating new one...')
          PopupService.warning(`Questionnaire with ID ${questionnaireId.value} does not exist. Creating a new questionnaire.`, 'Creating New Questionnaire')
          
          const newQuestionnaire = await questionnaireStore.createQuestionnaire(questionnaire.value)
          console.log('New questionnaire created:', newQuestionnaire)
          questionnaireId.value = newQuestionnaire.questionnaire_id || newQuestionnaire.id
          
          // Then save questions if any
          if (questions.value.length > 0) {
            console.log('Saving questions for new questionnaire...')
            await questionnaireStore.saveQuestionnaireWithQuestions(
              questionnaireId.value,
              questionnaire.value,
              questions.value
            )
            console.log('Questions saved successfully')
          }
          
          saveMessage.value = 'New questionnaire created and saved as draft!'
          PopupService.success('New questionnaire created and saved as draft!', 'Created')
          
          // Update route to include ID
          router.replace({ 
            name: 'VendorQuestionnaireBuilder', 
            params: { id: questionnaireId.value } 
          })
        } else {
          throw error
        }
      }
    } else {
      // Create new questionnaire first
      console.log('Creating new questionnaire...')
      console.log('Questionnaire data:', questionnaire.value)
      console.log('Vendor ID:', questionnaire.value.vendor_id, 'Type:', typeof questionnaire.value.vendor_id)
      
      const newQuestionnaire = await questionnaireStore.createQuestionnaire(questionnaire.value)
      console.log('New questionnaire created:', newQuestionnaire)
      questionnaireId.value = newQuestionnaire.questionnaire_id || newQuestionnaire.id
      
      // Then save questions if any
      if (questions.value.length > 0) {
        console.log('Saving questions for new questionnaire...')
        await questionnaireStore.saveQuestionnaireWithQuestions(
          questionnaireId.value,
          questionnaire.value,
          questions.value
        )
        console.log('Questions saved successfully')
      } else {
        // Even if no questions, update the questionnaire to ensure it's saved
        console.log('No questions to save, updating questionnaire...')
        await questionnaireStore.updateQuestionnaire(questionnaireId.value, questionnaire.value)
      }
      
      saveMessage.value = 'Questionnaire created and saved as draft!'
      PopupService.success('Questionnaire created and saved as draft!', 'Saved')
      
      // Create notification
      await notificationService.createVendorQuestionnaireNotification('questionnaire_draft_saved', {
        questionnaire_id: questionnaireId.value,
        questionnaire_title: questionnaire.value.questionnaire_name
      })
      
      // Update route to include ID
      router.replace({ 
        name: 'VendorQuestionnaireBuilder', 
        params: { id: questionnaireId.value } 
      })
    }
    
    console.log('=== END SAVE DRAFT DEBUG ===')
    
    setTimeout(() => {
      saveMessage.value = ''
    }, 3000)
    
  } catch (error) {
    console.error('Failed to save draft:', error)
    console.error('Error details:', {
      message: error.message,
      stack: error.stack,
      response: error.response,
      data: error.response?.data
    })
    
    const errorMessage = error.response?.data?.error || error.response?.data?.message || error.message || 'Failed to save draft. Please try again.'
    PopupService.error(errorMessage, 'Save Failed')
    
    // Create error notification
    await notificationService.createVendorErrorNotification('save_questionnaire_draft', errorMessage, {
      title: 'Failed to Save Draft',
      questionnaire_name: questionnaire.value.questionnaire_name
    })
  } finally {
    isSaving.value = false
  }
}

const activateQuestionnaire = async () => {
  if (!questionnaire.value.questionnaire_name.trim()) {
    PopupService.warning('Please enter a questionnaire name', 'Missing Name')
    return
  }

  if (!questionnaire.value.questionnaire_type) {
    PopupService.warning('Please select a questionnaire type before activating', 'Missing Type')
    return
  }

  if (questions.value.length === 0) {
    PopupService.warning('Please add at least one question before activating', 'No Questions')
    return
  }

  if (!questionnaire.value.vendor_id) {
    PopupService.warning('Please select a vendor before activating the questionnaire', 'No Vendor Selected')
    return
  }

  isSaving.value = true
  
  try {
    if (!questionnaireId.value) {
      // Create new questionnaire first
      const newQuestionnaire = await questionnaireStore.createQuestionnaire(questionnaire.value)
      questionnaireId.value = newQuestionnaire.questionnaire_id
    }
    
    try {
      // Save questions
      await questionnaireStore.saveQuestionnaireWithQuestions(
        questionnaireId.value,
        questionnaire.value,
        questions.value
      )
      
      // Activate
      await questionnaireStore.activateQuestionnaire(questionnaireId.value, questionnaire.value, questions.value)
      
      // Show success message and redirect to approval workflow
      PopupService.confirm(
        'Questionnaire activated successfully! Would you like to send it for approval now?',
        'Questionnaire Activated',
        () => {
          // Redirect to ApprovalWorkflowCreator with questionnaire data
          console.log('VendorQuestionnaireBuilder - Full questionnaire object:', questionnaire.value)
          console.log('VendorQuestionnaireBuilder - vendor_id being passed:', questionnaire.value.vendor_id)
          const vendorId = questionnaire.value.vendor_id ? `&vendor_id=${questionnaire.value.vendor_id}` : ''
          console.log('VendorQuestionnaireBuilder - Full URL parameter:', vendorId)
          // Use current window origin (works for both dev and production)
          const baseUrl = typeof window !== 'undefined' ? window.location.origin : 'https://grc-tprm.vardaands.com'
          const fullUrl = `${baseUrl}/vendor-approval-workflow-creator?workflow_type=MULTI_PERSON&approval_type=questionnaire_approval&questionnaire_id=${questionnaireId.value}&questionnaire_name=${encodeURIComponent(questionnaire.value.questionnaire_name)}&questionnaire_type=${questionnaire.value.questionnaire_type}&auto_populate=true${vendorId}`
          console.log('VendorQuestionnaireBuilder - Redirecting to:', fullUrl)
          window.location.href = fullUrl
        }
      )
    } catch (error) {
      if (error.message.includes('does not exist')) {
        // Questionnaire doesn't exist, create a new one
        PopupService.warning(`Questionnaire with ID ${questionnaireId.value} does not exist. Creating a new questionnaire.`, 'Creating New Questionnaire')
        const newQuestionnaire = await questionnaireStore.createQuestionnaire(questionnaire.value)
        questionnaireId.value = newQuestionnaire.questionnaire_id
        
        // Save questions
        await questionnaireStore.saveQuestionnaireWithQuestions(
          questionnaireId.value,
          questionnaire.value,
          questions.value
        )
        
        // Activate
        await questionnaireStore.activateQuestionnaire(questionnaireId.value, questionnaire.value, questions.value)
        
        // Show success message and redirect to approval workflow
        PopupService.confirm(
          'Questionnaire created and activated successfully! Would you like to send it for approval now?',
          'Questionnaire Activated',
          () => {
            // Redirect to ApprovalWorkflowCreator with questionnaire data
            console.log('VendorQuestionnaireBuilder - Full questionnaire object:', questionnaire.value)
            console.log('VendorQuestionnaireBuilder - vendor_id being passed:', questionnaire.value.vendor_id)
            const vendorId = questionnaire.value.vendor_id ? `&vendor_id=${questionnaire.value.vendor_id}` : ''
            console.log('VendorQuestionnaireBuilder - Full URL parameter:', vendorId)
            // Use current window origin (works for both dev and production)
            const baseUrl = typeof window !== 'undefined' ? window.location.origin : 'https://grc-tprm.vardaands.com'
            const fullUrl = `${baseUrl}/vendor-approval-workflow-creator?workflow_type=MULTI_PERSON&approval_type=questionnaire_approval&questionnaire_id=${questionnaireId.value}&questionnaire_name=${encodeURIComponent(questionnaire.value.questionnaire_name)}&questionnaire_type=${questionnaire.value.questionnaire_type}&auto_populate=true${vendorId}`
            console.log('VendorQuestionnaireBuilder - Redirecting to:', fullUrl)
            window.location.href = fullUrl
          },
          () => {
            // Update route to include ID
            router.replace({ 
              name: 'VendorQuestionnaireBuilder', 
              params: { id: questionnaireId.value } 
            })
          }
        )
      } else {
        throw error
      }
    }
    
  } catch (error) {
    console.error('Failed to activate questionnaire:', error)
    PopupService.error('Failed to activate questionnaire. Please try again.', 'Activation Failed')
  } finally {
    isSaving.value = false
  }
}

// Helper methods for badge classes
const getRiskLevelClass = (riskLevel) => {
  if (!riskLevel) return 'badge-secondary'
  const level = riskLevel.toLowerCase()
  if (level.includes('high') || level.includes('critical')) return 'badge-danger'
  if (level.includes('medium')) return 'badge-warning'
  if (level.includes('low')) return 'badge-success'
  return 'badge-secondary'
}

const getStatusClass = (status) => {
  if (!status) return 'badge-secondary'
  const statusLower = status.toLowerCase()
  if (statusLower.includes('active') || statusLower.includes('approved')) return 'badge-success'
  if (statusLower.includes('pending') || statusLower.includes('review')) return 'badge-warning'
  if (statusLower.includes('rejected') || statusLower.includes('inactive')) return 'badge-danger'
  return 'badge-secondary'
}

const getRFPStatusClass = (status) => {
  if (!status) return 'badge-secondary'
  const statusLower = status.toLowerCase()
  if (statusLower.includes('awarded') || statusLower.includes('shortlisted')) return 'badge-success'
  if (statusLower.includes('under_evaluation') || statusLower.includes('submitted')) return 'badge-warning'
  if (statusLower.includes('rejected')) return 'badge-danger'
  return 'badge-secondary'
}

const getScreeningStatusClass = (status) => {
  if (!status) return 'badge-secondary'
  const statusLower = status.toLowerCase()
  if (statusLower.includes('clear')) return 'badge-success'
  if (statusLower.includes('potential_match') || statusLower.includes('under_review')) return 'badge-warning'
  if (statusLower.includes('confirmed_match')) return 'badge-danger'
  return 'badge-secondary'
}

// Helper methods for formatting
const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  try {
    const date = new Date(dateString)
    return date.toLocaleDateString()
  } catch (error) {
    return 'Invalid Date'
  }
}

const formatCurrency = (amount) => {
  if (!amount) return '0'
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(amount)
}

const getDocumentUrl = (documentName) => {
  // You can customize this URL based on your document storage system
  // For now, assuming documents are stored in a documents folder
  return `/documents/rfp/${documentName}`
}

// Helper to check if a field should be excluded (file references, etc.)
const shouldExcludeField = (key, value) => {
  // Exclude file-related keys
  const excludeKeys = ['documents', 'document_urls', 'urls', 'documentUrls']
  const keyLower = key.toLowerCase()
  if (excludeKeys.some(excludeKey => keyLower === excludeKey.toLowerCase())) {
    return true
  }
  
  // Exclude if value is a file reference
  if (typeof value === 'string') {
    return /^(https?:\/\/|\.\/|\/|.*\.(pdf|doc|docx|jpg|jpeg|png|zip|rar))/.test(value) ||
           value.length > 200 // Long strings are likely file content, not data
  }
  
  return false
}

// Helper to recursively extract all nested JSON data
const extractAllNestedData = (obj, excludeKeys = ['documents', 'document_urls', 'urls'], path = '') => {
  const result = {}
  
  if (!obj || typeof obj !== 'object' || Array.isArray(obj)) {
    return result
  }
  
  Object.keys(obj).forEach(key => {
    // Skip file-related keys
    if (excludeKeys.includes(key.toLowerCase())) {
      return
    }
    
    const value = obj[key]
    const currentPath = path ? `${path}.${key}` : key
    
    // Skip file references
    if (shouldExcludeField(key, value)) {
      return
    }
    
    // If value is an object/array, recursively extract
    if (value && typeof value === 'object') {
      if (Array.isArray(value)) {
        // For arrays, check if items are objects
        if (value.length > 0 && typeof value[0] === 'object') {
          // Store array as-is, but also extract nested data
          result[key] = value
        } else {
          // Simple array, store as-is
          result[key] = value
        }
      } else {
        // Nested object - extract its properties
        const nested = extractAllNestedData(value, excludeKeys, currentPath)
        if (Object.keys(nested).length > 0) {
          // If nested has data, merge it
          Object.assign(result, nested)
          // Also keep the original key if it has meaningful data
          if (Object.keys(value).length > 0) {
            result[key] = value
          }
        } else {
          result[key] = value
        }
      }
    } else {
      // Primitive value
      result[key] = value
    }
  })
  
  return result
}

// Helper to organize data into logical groups
const organizeDataByGroups = (data) => {
  const groups = {
    'Profile & Personnel': {},
    'Team & Structure': {},
    'Project Details': {},
    'Compliance': {},
    'References': {},
    'Timestamps': {},
    'Other': {}
  }
  
  // Define field mappings to groups
  const fieldMappings = {
    'Profile & Personnel': ['keyPersonnel', 'key_personnel', 'personnel', 'profile', 'name', 'email', 'phone', 'role', 'education', 'experience', 'relevantExperience', 'relevant_experience'],
    'Team & Structure': ['teamStructure', 'team_structure', 'teamSize', 'team_size', 'totalTeamSize', 'total_team_size', 'communicationPlan', 'communication_plan'],
    'Project Details': ['projectMethodology', 'project_methodology', 'methodology', 'proposedValue', 'proposed_value', 'technicalScore', 'technical_score', 'commercialScore', 'commercial_score'],
    'Compliance': ['compliance', 'soc2', 'hippa', 'hipaa', 'pci', 'iso', 'iso9001', 'iso14001', 'iso27001'],
    'References': ['references', 'reference'],
    'Timestamps': ['lastSaved', 'last_saved', 'submissionDate', 'submission_date', 'savedAt', 'saved_at', 'createdAt', 'created_at', 'updatedAt', 'updated_at'],
    'Other': []
  }
  
  Object.keys(data).forEach(key => {
    const keyLower = key.toLowerCase()
    let assigned = false
    
    // Try to match to a group
    for (const [groupName, fields] of Object.entries(fieldMappings)) {
      if (groupName === 'Other') continue
      
      if (fields.some(field => {
        const fieldLower = field.toLowerCase()
        return keyLower.includes(fieldLower) || keyLower === fieldLower
      })) {
        groups[groupName][key] = data[key]
        assigned = true
        break
      }
    }
    
    // If not assigned, put in Other
    if (!assigned) {
      groups['Other'][key] = data[key]
    }
  })
  
  // Remove empty groups
  Object.keys(groups).forEach(group => {
    if (Object.keys(groups[group]).length === 0) {
      delete groups[group]
    }
  })
  
  return groups
}

// Helper to get data from response_documents column
const getRequiredResponseData = (response) => {
  if (!response) return null
  
  let allData = {}
  
  // Primary source: response_documents column
  // The backend returns response_documents as: { documents: [], response_documents: {...actual data...}, document_urls: {...} }
  if (response.response_documents) {
    const responseDocs = response.response_documents
    
    // Check if response_documents.response_documents exists (the actual JSON data from the column)
    if (responseDocs.response_documents && typeof responseDocs.response_documents === 'object' && !Array.isArray(responseDocs.response_documents)) {
      // Recursively extract ALL nested data from response_documents
      const extracted = extractAllNestedData(responseDocs.response_documents)
      allData = { ...allData, ...extracted }
    }
    
    // Also check top-level response_documents for any additional data
    if (typeof responseDocs === 'object' && !Array.isArray(responseDocs)) {
      Object.keys(responseDocs).forEach(key => {
        // Skip the nested response_documents, documents, and document_urls
        if (key !== 'response_documents' && key !== 'documents' && key !== 'document_urls') {
          const value = responseDocs[key]
          if (!shouldExcludeField(key, value) && !allData[key]) {
            if (value && typeof value === 'object' && !Array.isArray(value)) {
              const extracted = extractAllNestedData(value)
              allData = { ...allData, ...extracted }
            } else {
              allData[key] = value
            }
          }
        }
      })
    }
  }
  
  // Add completion_percentage if available (from response level, but only if not already in response_documents)
  if (response.completion_percentage !== null && 
      response.completion_percentage !== undefined && 
      !allData.completion_percentage && 
      !allData.completionPercentage) {
    allData.completion_percentage = response.completion_percentage
  }
  
  // Organize data into logical groups
  const organized = organizeDataByGroups(allData)
  
  // Return organized data if it has meaningful content
  return Object.keys(organized).length > 0 ? organized : null
}

// Helper to get documents from document_urls field
const getDocumentsFromUrls = (response) => {
  if (!response) return []
  
  const documents = []
  const seenUrls = new Set() // To avoid duplicates
  
  // Helper to add URL if not already seen
  const addDocument = (url) => {
    if (url && typeof url === 'string' && !seenUrls.has(url)) {
      seenUrls.add(url)
      documents.push(url)
    }
  }
  
  // Check top-level document_urls (from backend response)
  if (response.document_urls) {
    const docUrls = response.document_urls
    
    if (Array.isArray(docUrls)) {
      docUrls.forEach(url => addDocument(url))
    } else if (typeof docUrls === 'object') {
      if (docUrls.documents && Array.isArray(docUrls.documents)) {
        docUrls.documents.forEach(url => addDocument(url))
      }
      if (docUrls.urls && Array.isArray(docUrls.urls)) {
        docUrls.urls.forEach(url => addDocument(url))
      }
      // Check all values in the object
      Object.values(docUrls).forEach(value => {
        if (typeof value === 'string' && /^(https?:\/\/|\.\/|\/|.*\.(pdf|doc|docx|jpg|jpeg|png|zip|rar))/.test(value)) {
          addDocument(value)
        } else if (Array.isArray(value)) {
          value.forEach(url => addDocument(url))
        }
      })
    } else if (typeof docUrls === 'string') {
      addDocument(docUrls)
    }
  }
  
  // Check response_documents.document_urls
  if (response.response_documents?.document_urls) {
    const docUrls = response.response_documents.document_urls
    
    if (Array.isArray(docUrls)) {
      docUrls.forEach(url => addDocument(url))
    } else if (typeof docUrls === 'object') {
      if (docUrls.documents && Array.isArray(docUrls.documents)) {
        docUrls.documents.forEach(url => addDocument(url))
      }
      if (docUrls.urls && Array.isArray(docUrls.urls)) {
        docUrls.urls.forEach(url => addDocument(url))
      }
      // Check all values in the object
      Object.values(docUrls).forEach(value => {
        if (typeof value === 'string' && /^(https?:\/\/|\.\/|\/|.*\.(pdf|doc|docx|jpg|jpeg|png|zip|rar))/.test(value)) {
          addDocument(value)
        } else if (Array.isArray(value)) {
          value.forEach(url => addDocument(url))
        }
      })
    } else if (typeof docUrls === 'string') {
      addDocument(docUrls)
    }
  }
  
  // Also check response_documents.documents (legacy support - only if they look like URLs)
  if (response.response_documents?.documents && Array.isArray(response.response_documents.documents)) {
    response.response_documents.documents.forEach(doc => {
      if (typeof doc === 'string' && /^(https?:\/\/|\.\/|\/|.*\.(pdf|doc|docx|jpg|jpeg|png|zip|rar))/.test(doc)) {
        addDocument(doc)
      }
    })
  }
  
  return documents
}

// Helper to get document URL from data (handles both string URLs and objects)
const getDocumentUrlFromData = (document) => {
  if (typeof document === 'string') {
    // If it's already a full URL, return it
    if (/^https?:\/\//.test(document)) {
      return document
    }
    // Otherwise, treat it as a relative path
    return document.startsWith('/') ? document : `/documents/rfp/${document}`
  }
  
  // If it's an object with url property
  if (typeof document === 'object' && document !== null) {
    return document.url || document.path || document.href || '#'
  }
  
  return '#'
}

// Helper to get document name for display
const getDocumentName = (document) => {
  if (typeof document === 'string') {
    // Extract filename from URL
    try {
      const url = new URL(document)
      const pathname = url.pathname
      return pathname.split('/').pop() || document
    } catch {
      // If not a valid URL, try to extract filename from path
      return document.split('/').pop() || document.split('\\').pop() || 'Document'
    }
  }
  
  // If it's an object
  if (typeof document === 'object' && document !== null) {
    return document.name || document.filename || document.title || 'Document'
  }
  
  return 'Document'
}

// Helper to count total items in response
const getResponseDocumentCount = (response) => {
  const jsonData = getRequiredResponseData(response)
  const files = getDocumentsFromUrls(response)
  
  let count = files.length
  if (jsonData) {
    // Count all fields across all groups
    Object.values(jsonData).forEach(groupData => {
      if (typeof groupData === 'object' && groupData !== null) {
        count += Object.keys(groupData).length
      }
    })
  }
  
  return count
}

// Helper methods for question options
const shouldShowOptions = (questionType) => {
  return ['MULTIPLE_CHOICE', 'CHECKBOX'].includes(questionType)
}

const getQuestionOptions = (question) => {
  if (!question.options || !question.options.choices) {
    return ['Option 1', 'Option 2']
  }
  return question.options.choices
}

const getOptionPlaceholder = (questionType) => {
  if (questionType === 'MULTIPLE_CHOICE') {
    return 'Enter choice option'
  } else if (questionType === 'CHECKBOX') {
    return 'Enter checkbox option'
  }
  return 'Enter option'
}

const updateQuestionOption = (questionId, optionIndex, value) => {
  const question = questions.value.find(q => q.id === questionId)
  if (question) {
    const options = { ...question.options } || {}
    if (!options.choices) {
      options.choices = ['Option 1', 'Option 2']
    }
    options.choices[optionIndex] = value
    updateQuestion(questionId, 'options', options)
  }
}

const addQuestionOption = (questionId) => {
  const question = questions.value.find(q => q.id === questionId)
  if (question) {
    const options = { ...question.options } || {}
    if (!options.choices) {
      options.choices = ['Option 1', 'Option 2']
    }
    options.choices.push(`Option ${options.choices.length + 1}`)
    updateQuestion(questionId, 'options', options)
  }
}

const removeQuestionOption = (questionId, optionIndex) => {
  const question = questions.value.find(q => q.id === questionId)
  if (question && question.options && question.options.choices && question.options.choices.length > 2) {
    const options = { ...question.options }
    options.choices.splice(optionIndex, 1)
    updateQuestion(questionId, 'options', options)
  }
}

// Rating configuration helpers
const getRatingConfig = (question) => {
  // Initialize default rating config if not exists
  if (!question.options) {
    question.options = {}
  }
  if (!question.options.rating) {
    question.options.rating = {
      min: 1,
      max: 5,
      step: 1,
      labels: ''
    }
  }
  return question.options.rating
}

const updateRatingConfig = (questionId, field, value) => {
  const question = questions.value.find(q => q.id === questionId)
  if (question) {
    const options = { ...question.options } || {}
    if (!options.rating) {
      options.rating = {}
    }
    options.rating[field] = value
    updateQuestion(questionId, 'options', options)
  }
}

// File upload configuration helpers
const getFileConfig = (question) => {
  // Initialize default file config if not exists
  if (!question.options) {
    question.options = {}
  }
  if (!question.options.file) {
    question.options.file = {
      allowedTypes: 'pdf,doc,docx,jpg,jpeg,png',
      maxSize: 10,
      maxFiles: 1
    }
  }
  return question.options.file
}

const updateFileConfig = (questionId, field, value) => {
  const question = questions.value.find(q => q.id === questionId)
  if (question) {
    const options = { ...question.options } || {}
    if (!options.file) {
      options.file = {}
    }
    options.file[field] = value
    updateQuestion(questionId, 'options', options)
  }
}

// Number input configuration helpers
const getNumberConfig = (question) => {
  // Initialize default number config if not exists
  if (!question.options) {
    question.options = {}
  }
  if (!question.options.number) {
    question.options.number = {
      min: null,
      max: null,
      step: null,
      unit: ''
    }
  }
  return question.options.number
}

const updateNumberConfig = (questionId, field, value) => {
  const question = questions.value.find(q => q.id === questionId)
  if (question) {
    const options = { ...question.options } || {}
    if (!options.number) {
      options.number = {}
    }
    options.number[field] = value
    updateQuestion(questionId, 'options', options)
  }
}

// Reactive updates for form fields
const updateQuestionnaireName = (value) => updateQuestionnaireField('questionnaire_name', value)
const updateQuestionnaireType = (value) => updateQuestionnaireField('questionnaire_type', value)
const updateDescription = (value) => updateQuestionnaireField('description', value)
const updateVendorCategory = (value) => updateQuestionnaireField('vendor_category_id', value)
const updateVendorId = (value) => {
  console.log('VendorQuestionnaireBuilder - Vendor selected, ID:', value, 'Type:', typeof value)
  console.log('VendorQuestionnaireBuilder - Vendor object:', vendors.value.find(v => v.id == value))
  
  // Convert to integer if not empty, otherwise set to null
  const vendorId = value && value !== '' ? parseInt(value, 10) : null
  console.log('VendorQuestionnaireBuilder - Converted vendor_id:', vendorId, 'Type:', typeof vendorId)
  
  updateQuestionnaireField('vendor_id', vendorId)
  console.log('VendorQuestionnaireBuilder - Updated questionnaire.vendor_id:', questionnaire.value.vendor_id)
}
const updateStatus = (value) => updateQuestionnaireField('status', value)

// JSON formatting helpers
const formatJsonKey = (key) => {
  // Convert camelCase to Title Case
  return key
    .replace(/([A-Z])/g, ' $1')
    .replace(/^./, str => str.toUpperCase())
    .trim()
}

const getJsonValueType = (value) => {
  if (value === null || value === undefined) return 'null'
  if (Array.isArray(value)) return 'array'
  if (typeof value === 'object') return 'object'
  if (typeof value === 'string' && /^\d{4}-\d{2}-\d{2}/.test(value)) return 'date'
  return typeof value
}

const formatJsonValue = (value) => {
  const type = getJsonValueType(value)
  
  if (type === 'null') return 'N/A'
  if (type === 'date') {
    try {
      const date = new Date(value)
      return date.toLocaleString()
    } catch {
      return value
    }
  }
  if (type === 'boolean') return value ? 'Yes' : 'No'
  if (type === 'number') {
    // Format percentages
    if (typeof value === 'number' && value <= 1 && value >= 0) {
      return `${(value * 100).toFixed(0)}%`
    }
    // Format decimals
    return value % 1 !== 0 ? value.toFixed(2) : value.toString()
  }
  return value
}

// Handle data source change manually to ensure data is fetched
const handleDataSourceChange = async () => {
  const vendorId = questionnaire.value.vendor_id
  console.log('VendorQuestionnaireBuilder - Data source changed to:', selectedDataSource.value, 'Vendor ID:', vendorId)
  
  if (vendorId) {
    if (selectedDataSource.value === 'rfp-data') {
      console.log('VendorQuestionnaireBuilder - Manually fetching RFP data for vendor:', vendorId)
      await questionnaireStore.fetchVendorRFPData(vendorId)
      console.log('VendorQuestionnaireBuilder - RFP data after manual fetch:', questionnaireStore.getRFPData)
    } else if (selectedDataSource.value === 'screening-data') {
      console.log('VendorQuestionnaireBuilder - Manually fetching screening data for vendor:', vendorId)
      await questionnaireStore.fetchVendorScreeningData(vendorId)
    }
  }
}
</script>

<style scoped src="./VendorQuestionnaireBuilder.css"></style>

<style scoped>
/* Simplified styles - minimal nesting */
.documents-container {
  width: 100%;
  margin-top: 0.5rem;
}

.documents-list {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.response-documents {
  width: 100%;
}

.response-group {
  width: 100%;
  background-color: white;
  border: 1px solid #e5e7eb;
  border-radius: 0.75rem;
  padding: 1.5rem;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.response-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 1rem;
  border-bottom: 2px solid #e2e8f0;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.response-title {
  font-weight: 600;
  color: #1e293b;
  font-size: 1rem;
  font-family: inherit;
}

.document-count {
  font-size: 0.75rem;
  color: #6b7280;
  background-color: #f3f4f6;
  padding: 0.25rem 0.75rem;
  border-radius: 1rem;
  font-family: inherit;
}

.no-documents {
  text-align: center;
  padding: 20px;
  color: #6b7280;
  font-style: italic;
  width: 100%;
}

.full-width {
  width: 100%;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .response-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .response-group {
    padding: 1rem;
  }
  
  .data-group {
    padding: 1rem;
  }
  
  .data-field {
    padding: 0.625rem;
  }
  
  .field-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.25rem;
  }
  
  .field-label-small {
    min-width: auto;
  }
}
</style>
